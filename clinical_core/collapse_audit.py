"""Phase 2 shadow core, P2M-1: the structural audit of collapse / arrest safety.

    python -m clinical_core.collapse_audit --digest
    python -m clinical_core.collapse_audit --design
    python -m clinical_core.collapse_audit --run --out <directory outside the repository>

Shadow only and read-only (faculty brief of 2026-11-02, recorded in FACULTY). It makes the pulse / arrest / collapse
semantics explicit from the code (writers, readers, guards, event order), probes the zero-flow physiology and the
flow / pressure, pump / rhythm and oxygen-delivery orthogonality on fixed core states, reads the persistence and the
event order of the existing P2E-3 collapse rule through the core's own functions, characterizes the carried extreme GI
subset from committed records, classifies the generalization to seven shock families and returns the minimum structure
a common collapse safety layer needs. It changes no core file, writes no channel, adds no rule, threshold or parameter
and activates nothing: collapse stays off.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from dataclasses import replace
from pathlib import Path

from . import blood_fluid_calibration as bf
from . import calibration
from . import decision_pack
from . import derived as dv
from . import gi_reference
from . import lactate_rebuild as lr
from . import lactate_slice
from . import vascular_tone as vt
from . import ventilation_surface as vs
from .integration import step
from .state import CoreInvariantError, RhythmCode, RhythmState, UnresolvedBoundary

DECIDED = "2026-11-02"
REVISION = "P2M-1"
ROOT = vs.ROOT
CORE_DIR = ROOT / "clinical_core"
C57 = "gi_bleed_57m"
P2L1_RECORD = ROOT / "docs" / "revision" / "P2L1_consciousness_audit.json"
P2L1_RECORD_SHA = "dcb1b40ae92cd785bec0723d6262948ab616d7b2513656ecd3cf81e2fadf607b"
P2K5_RECORD = ROOT / "docs" / "revision" / "P2K5_respiratory_monotonicity.json"
P2K5_RECORD_SHA = "4c567527096d11253b6ebb054436b19a1797ae4f0aeee802fe5c7e824e7de523"

FACULTY = {
    "brief": "P2M-1 collapse / arrest safety architecture audit (2026-11-02): structural; no arrest threshold chosen",
    "three_states": "consciousness impairment, hemodynamic collapse (circulation present, not viable) and cardiac arrest "
                    "(no effective circulation) stay distinct; unconscious with a pulse, profound shock with a pulse and "
                    "collapse progressing to arrest stay representable",
    "no_biomarker_arrest": "lactate, D alone, consciousness I and the systemic encephalopathy burden F are never direct "
                           "collapse or arrest triggers",
    "candidate_domains": "A flow, B MAP / perfusion pressure, C pump P, D rhythm / pulse R, E effective oxygen delivery / "
                         "deficit, F arterial oxygenation, G severe acid-base failure, H future respiratory failure; "
                         "necessity, redundancy and order to be determined",
    "acidemia": "no pH arrest threshold unless a committed common rule exists; the P2K-5 / P2L-2 subset (57m, demand "
                "1.1, 17,604 rows, pH < 7.00) carried as a diagnostic stress subset, never filtered",
    "persistence": "if an instantaneous rule would flip or arrest in one minute: PERSISTENCE_STATE_OR_TIMER_REQUIRED; D "
                   "and F are not collapse memory without strong causal justification",
    "order": "no implicit recursive pulse / collapse feedback; an explicit lag if needed",
    "rosc": "no ACLS here; no proposed state may make a future return of circulation impossible",
    "thresholds": "the GI cases cannot identify minimum viable MAP or flow, an arrest pH or DO2 or a persistence "
                  "duration; ranges only from general physiology, otherwise UNSET",
    "closed": "BloodState, V, P, T, R, pressure, DO2 / deficit, D, lactate, HR / baroreflex, acid-base, RR / W / PaCO2 "
              "and the consciousness architecture closed; P2L-2's carried debts untouched unless collapse depends on "
              "them",
    "scope": "shadow only; no collapse activation, runtime integration, GI or second-family migration, death model or "
             "parameter approval"}
STATUS = {"approved": "none FACULTY_APPROVED", "collapse": "OFF (P2E-3 rule declared, not activated)",
          "probe_values": "SYNTHETIC_PROBE_ONLY: illustrative fixed states (P2L-1's sizes) and P2E-3's committed "
                          "synthetic test values (threshold 0.4, limit 10, repayment tau 30)"}
MECHANISM_CLASSES = ("VALID_COMMON_PHYSIOLOGY", "LEGACY_ARTIFACT", "CASE_SCRIPTED_EVENT", "SAFETY_GUARD",
                     "NOT_CURRENTLY_MODELED")
STRUCTURE_CLASSES = ("EXISTING_PULSE_ARREST_STRUCTURE_SUFFICIENT", "DERIVED_COLLAPSE_SIGNAL_ONLY_REQUIRED",
                     "SHORT_PERSISTENCE_TIMER_REQUIRED", "NEW_COLLAPSE_STATE_REQUIRED",
                     "MULTI_MECHANISM_SAFETY_ARCHITECTURE_REQUIRED")
GENERALIZATION_CLASSES = ("COMMON_COLLAPSE_ARCHITECTURE_PLAUSIBLE", "STRUCTURAL_GAP", "DISEASE_SPECIFIC_OVERFIT_RISK")


def _record(path: Path, sha: str) -> dict:
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != sha:
        raise ValueError(f"{path.name} changed after it was pinned")
    return json.loads(data)


# 1. Pulse semantics (P2M-1-1), from the code -----------------------------------------------------------------------------

OWN = ("clinical_core/collapse_audit.py",)
REPORT = "clinical_core/collapse_audit_report.py"


def core_files() -> list:
    """The physiology, contract and registry files: every clinical_core source but the analysis modules and reports (the
    two exclusion tuples) and this audit."""
    excluded = set(decision_pack.PACK_DIGEST_EXCLUDED) | set(lactate_slice.DOWNSTREAM_REPORTS) | set(OWN) | {REPORT}
    return sorted(p for p in CORE_DIR.rglob("*.py") if "__pycache__" not in p.parts
                  and p.relative_to(ROOT).as_posix() not in excluded)


RHYTHM_CONSTRUCTORS = ("RhythmState", "sinus", "asystole", "vf", "pea", "from_dict")


def pulse_scan() -> dict:
    """Every writer and reader of the rhythm / pulse state across the core files, by AST (file:line)."""
    out = {"transitions": [], "r_keyword_writes": [], "terminal_since_writes": [], "pulse_reads": [],
           "terminal_since_reads": [], "rhythm_constructors": [], "unresolved_boundaries": []}
    files = core_files()
    for path in files:
        rel = path.relative_to(CORE_DIR).as_posix()
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            where = f"{rel}:{getattr(node, 'lineno', 0)}"
            if isinstance(node, ast.Call):
                name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
                base = getattr(node.func, "value", None)
                if name == "RhythmTransition":
                    out["transitions"].append(where)
                elif name == "UnresolvedBoundary":
                    out["unresolved_boundaries"].append(where)
                elif name in RHYTHM_CONSTRUCTORS and (name == "RhythmState" or getattr(base, "id", None) in (
                        "RhythmState", "cls")):
                    out["rhythm_constructors"].append(where)
            elif isinstance(node, ast.keyword):
                if node.arg == "R":
                    out["r_keyword_writes"].append(where if hasattr(node, "lineno") else f"{rel}:{node.value.lineno}")
                elif node.arg == "terminal_since":
                    out["terminal_since_writes"].append(f"{rel}:{node.value.lineno}")
            elif isinstance(node, ast.Attribute):
                if node.attr == "pulse_present":
                    out["pulse_reads"].append(where)
                elif node.attr == "terminal_since":
                    out["terminal_since_reads"].append(where)
    out = {k: sorted(set(v)) for k, v in out.items()}
    out["files_scanned"] = len(files)
    return out


PULSE_SEMANTICS = {
    "field": "CoreState.R (channel C4, 'state machine: code, rate, effective-output factor, pulse'): "
             "RhythmState.pulse_present",
    "class": "AUTHORITATIVE_STATE: pulse is a field of the rhythm state R, changed only by rhythm transitions; it is "
             "bound by invariant to the rhythm code (pulse exactly when the code perfuses: NON_PERFUSING = pulseless VT, "
             "VF, PEA, asystole), so it is ELECTRICAL / RHYTHM semantics, never read from pressure or flow",
    "default": "the case's arrival rhythm (Anchors.rhythm; bands.ARRIVAL: sinus 80, pulse); terminal_since None",
    "invariants": "a perfusing rhythm has output_factor > 0, a pulseless one exactly 0; terminal_since is set exactly "
                  "when there is no pulse, within the encounter, and never cleared",
    "when_false": "derive's pulseless branch: output, pressure and delivery 0; SBP, DBP, MAP, SpO2, CRT and pulse rate "
                  "not measurable; RR 0; the legacy level 3; the integrator keeps T and P as latent values, accrues D at "
                  "the full demand (lactate follows it a minute later), accrues the acid burden, holds the collapse "
                  "burden; nothing restores a pulse",
    "changed_by": "a RhythmTransition: a contributor's (modules/rhythm_events.ScriptedRhythmEvent) or the core's P2E-3 "
                  "collapse rule (integration.step); the arrival constructor sets the arrival rhythm"}


# 2. Current mechanisms (P2M-1-2) ----------------------------------------------------------------------------------------------

MECHANISMS = {
    "rhythm_state_invariants": ("state.RhythmState.__post_init__", "a pulse exactly when the rhythm perfuses; a "
                                "non-perfusing rhythm has no output", "SAFETY_GUARD", True),
    "scripted_rhythm_event": ("modules/rhythm_events.ScriptedRhythmEvent", "a declared natural-history change of R at "
                              "a declared minute, cause class and preventability; not applied once in arrest; no GI "
                              "case declares one", "CASE_SCRIPTED_EVENT", False),
    "scripted_pump_change": ("modules/rhythm_events.ScriptedPumpChange", "a declared change of P per minute over an "
                             "interval; reaches flow, never the pulse directly", "CASE_SCRIPTED_EVENT", False),
    "p2e3_collapse_rule": ("derived.collapse_burden_after_minute / collapse_reached / terminal_rhythm; integration.step",
                           "aux.collapse_burden accrues the share by which output_rel falls below a declared threshold "
                           "(read on the minute's start state, only with a pulse), held or repaid when declared; at the "
                           "declared limit R moves to PEA (or asystole) the same step, so the new state is pulseless "
                           "one minute after the state that met the criterion; off by default (threshold and limit None)",
                           "VALID_COMMON_PHYSIOLOGY", False),
    "zero_output_guard": ("derived.derive", "a pulse with effective output at the numerical zero stops the run "
                          "(UnresolvedBoundary), it is never shown", "SAFETY_GUARD", True),
    "bicarbonate_guard": ("derived.bicarbonate (P2K-2)", "an acid burden that takes HCO3 to or below 0 stops the run",
                          "SAFETY_GUARD", True),
    "blood_channel_guard": ("integration.step", "a blood-state move outside the V / Hb guard stops the run",
                            "SAFETY_GUARD", True),
    "no_return_of_pulse": ("integration._rhythm_after; CoreState docstring", "a transition back to a pulse after arrest "
                           "raises ('resuscitation is out of scope'); terminal_since never cleared",
                           "SAFETY_GUARD", True),
    "hemodynamic_collapse_with_pulse": ("none", "no observable or state names a collapse while a pulse is present; only "
                                        "the hidden P2E-3 burden exists, and only when the rule is declared",
                                        "NOT_CURRENTLY_MODELED", False),
    "resuscitation_rosc": ("none", "no CPR, defibrillation, epinephrine-for-arrest or return of circulation",
                           "NOT_CURRENTLY_MODELED", False),
    "legacy_engine_arrests": ("family_engine and its family modules (read as text)", "anaphylaxis untreated minutes, "
                              "apnoea minutes, a closed coronary artery's minutes to VF, a bradycardia rate at or below "
                              "20, and the older generic low-flow conjunction in clinical_physiology", "LEGACY_ARTIFACT",
                              True)}
#: The legacy mechanisms, quoted as text from the engine and its family modules (never imported, never fitted).
LEGACY = {"anaphylaxis_reaction.py": "ARREST_AFTER_MIN", "airway_pharmacology.py": "APNOEA_TO_ARREST_MIN",
          "acs_reperfusion.py": "VF_AT_MIN", "bradycardia_toxicology.py": "ARREST_RATE",
          "clinical_physiology.py": "low_flow_burden"}


def legacy_quoted() -> dict:
    return {name: token in (ROOT / name).read_text(encoding="utf-8") for name, token in LEGACY.items()}


# 3. Probes on fixed core states (P2M-1-3 to P2M-1-7) ---------------------------------------------------------------------------

PROBE_GAIN = 0.04
PROBE_RULE = ("Fixed states on P2K-2's neutral probe arrival (bands.ARRIVAL with HCO3 20, extraction reserve 2.5), read "
              "through derive, the deficit and the ventilation candidate (gain 0.04): illustrative extremes, P2L-1's "
              "sizes where they exist. Each candidate input is classified threshold-free against the neutral reference: "
              "zero under every admissible bound (the reading is on the reference's side), or positive under some. The "
              "current P2E-3 input is output_rel, whose admissible thresholds lie below arrival output (1).")
#: name -> (what, construction, the group, the inputs expected able to read positive).
PROBES = {
    "reference": ("the neutral probe arrival", {}, "all", ()),
    "flow_A_low_flow_high_tone": ("pump 0.55, tone 3.0 (the tone guard's ceiling): low flow, MAP kept",
                                  {"P": 0.55, "T": 3.0}, "flow_map", ("output", "oxygen_delivery")),
    "flow_B_flow_kept_low_tone": ("tone 0.45 (vasodilation: flow rises, MAP falls)", {"T": 0.45}, "flow_map",
                                  ("perfusion_pressure",)),
    "flow_C_both": ("pump 0.3", {"P": 0.3}, "flow_map", ("output", "perfusion_pressure", "oxygen_delivery")),
    "pump_A_pump_failure_organized_rhythm": ("pump 0.25, sinus", {"P": 0.25}, "pump_rhythm",
                                             ("output", "perfusion_pressure", "oxygen_delivery")),
    "pump_B_rhythm_low_output_with_pulse": ("complete AV block at 30 / min, output factor 0.5, pump 1",
                                            {"rhythm": "avb"}, "pump_rhythm", ("output", "perfusion_pressure")),
    "pump_B2_pulseless_rhythm": ("pump 1, VF (no pulse)", {"rhythm": "vf"}, "pump_rhythm", ()),
    "pump_C_both": ("pump 0.4 with the AV block", {"P": 0.4, "rhythm": "avb"}, "pump_rhythm",
                    ("output", "perfusion_pressure", "oxygen_delivery")),
    "oxygen_A_low_flow_delivery_kept": ("pump 0.5 (extraction reserve keeps consumption)", {"P": 0.5}, "oxygen",
                                        ("output", "perfusion_pressure")),
    "oxygen_B_content_failure": ("Hb at 25 % (flow and MAP kept)", {"hb_share": 0.25}, "oxygen", ("oxygen_delivery",)),
    "oxygen_C_both": ("pump 0.3, Hb at 60 %", {"P": 0.3, "hb_share": 0.6}, "oxygen",
                      ("output", "perfusion_pressure", "oxygen_delivery")),
    "oxygen_E_arterial_hypoxaemia": ("arrival on FiO2 1, then room air (SpO2 73)", {"arrival_fio2": 1.0, "fio2": 0.21},
                                     "oxygen", ("arterial_oxygenation",)),
    "oxygen_E2_authored_hypoxaemia": ("authored arrival SpO2 60 (delivery index 1)", {"arrival_spo2": 60.0}, "oxygen",
                                      ("arterial_oxygenation",)),
    "acid_severe_metabolic": ("metabolic acid burden 15 (pH about 7.18)", {"burden": 15.0}, "acid", ())}
#: The faculty's A / B / C / D sets (D is the reference), which must read as distinct patterns.
FACULTY_SETS = {"flow_map": ("reference", "flow_A_low_flow_high_tone", "flow_B_flow_kept_low_tone", "flow_C_both"),
                "oxygen": ("reference", "oxygen_A_low_flow_delivery_kept", "oxygen_B_content_failure",
                           "oxygen_C_both")}
#: Inputs: the reading, the side on which it fails. 'output' is the current P2E-3 input.
INPUTS = {"output": ("output_rel", "low"), "perfusion_pressure": ("map", "low"),
          "oxygen_delivery": ("deficit_fraction", "high"), "arterial_oxygenation": ("spo2", "low")}


def _probe_state(spec: dict):
    spec = dict(spec)
    anchors, profile = vs.PROBE_ANCHORS, vs.PROBE_PROFILE
    if "arrival_spo2" in spec:
        anchors = replace(anchors, spo2=spec.pop("arrival_spo2"))
    if "arrival_fio2" in spec:
        anchors = replace(anchors, fio2=spec.pop("arrival_fio2"))
    burden = spec.pop("burden", None)
    if "hb_share" in spec:
        spec["hb"] = anchors.hb * spec.pop("hb_share")
    rhythm = spec.pop("rhythm", None)
    state = vs._probe_state(burden, anchors, profile, **spec)
    if rhythm == "avb":
        state = state.evolve(R=RhythmState(RhythmCode.COMPLETE_AV_BLOCK, 30.0, 0.5, True))
    elif rhythm == "vf":
        state = state.evolve(R=RhythmState.vf(), terminal_since=state.minute)
    return state, anchors, profile


def reading(state, anchors, profile) -> dict:
    d = dv.derive(state, anchors, profile)
    out = {"pulse": d.pulse_present, "rhythm": d.rhythm.value, "P": state.P, "T": state.T, "output_rel": d.output_rel,
           "pressure_rel": d.pressure_rel, "map": d.map, "sbp": d.sbp, "delivery_rel": d.delivery_rel, "spo2": d.spo2,
           "hb": state.hb, "deficit_fraction": None, "effective_delivery": None, "ph": None, "paco2": None,
           "legacy_level": d.consciousness_level}
    if d.pulse_present:
        out["effective_delivery"] = dv.effective_delivery(d.delivery_rel, anchors)
        out["deficit_fraction"] = dv.acute_deficit_signal(state, anchors, profile)
        gas = vs._vr(state, anchors, profile, PROBE_GAIN)
        out.update({"ph": gas["ph"], "paco2": gas["paco2"]})
    return out


def support(row: dict, reference: dict) -> dict:
    out = {}
    for name, (key, side) in INPUTS.items():
        value, base = row.get(key), reference.get(key)
        if not row["pulse"]:
            out[name] = "ARREST_NOT_COLLAPSE"
        elif value is None or base is None:
            out[name] = "UNAVAILABLE"
        else:
            past = value < base if side == "low" else value > base
            out[name] = "POSITIVE_UNDER_SOME_ADMISSIBLE_BOUND" if past else "ZERO_UNDER_EVERY_ADMISSIBLE_BOUND"
    return out


def mechanism(row: dict) -> str:
    """P2M-1-6: which kind of non-viability a state could carry, read from its threshold-free support. Flow or pressure
    failing: circulatory; only oxygen content or arterial oxygenation failing: metabolic (no hemodynamic collapse)."""
    if not row["reading"]["pulse"]:
        return "ARREST"
    positive = set(row["positive"])
    if positive & {"output", "perfusion_pressure"}:
        return "CIRCULATORY_COLLAPSE_RISK"
    if positive & {"oxygen_delivery", "arterial_oxygenation"}:
        return "METABOLIC_NONVIABILITY_RISK"
    return "NONE"


def probes() -> dict:
    rows = {}
    for name, (what, spec, group, expected) in PROBES.items():
        state, anchors, profile = _probe_state(spec)
        rows[name] = {"what": what, "group": group, "reading": reading(state, anchors, profile),
                      "expected": list(expected)}
    reference = rows["reference"]["reading"]
    for row in rows.values():
        row["support"] = support(row["reading"], reference)
        row["positive"] = sorted(k for k, v in row["support"].items() if v.startswith("POSITIVE"))
        row["as_expected"] = row["positive"] == sorted(row["expected"])
        row["mechanism"] = mechanism(row)
    groups = {}
    for group, names in FACULTY_SETS.items():
        patterns = [tuple(rows[n]["positive"]) for n in names]
        groups[group] = {"probes": list(names), "distinguishable": len(set(patterns)) == len(patterns)}
    for group in ("flow_map", "pump_rhythm", "oxygen"):
        groups.setdefault(group, {})["current_rule_blind"] = sorted(
            n for n, r in rows.items() if r["group"] == group and r["reading"]["pulse"]
            and "output" not in r["positive"] and r["positive"])
    keys = ("output_rel", "map", "deficit_fraction", "delivery_rel")
    same = lambda a, b: all(rows[a]["reading"][k] == rows[b]["reading"][k] for k in keys)  # noqa: E731
    groups["pump_rhythm"].update({
        "rhythm_equals_pump_at_equal_output": same("pump_B_rhythm_low_output_with_pulse",
                                                   "oxygen_A_low_flow_delivery_kept"),
        "pump_and_rhythm_failures_share_inputs": rows["pump_A_pump_failure_organized_rhythm"]["positive"]
        == rows["pump_C_both"]["positive"],
        "pulseless_rhythm_is_arrest": not rows["pump_B2_pulseless_rhythm"]["reading"]["pulse"]})
    return {"rule": PROBE_RULE, "rows": rows, "groups": groups,
            "all_as_expected": all(r["as_expected"] for r in rows.values())}


def zero_flow() -> dict:
    """What a pulseless state shows and how one minute moves it; which pulse / flow combinations can exist."""
    state, anchors, profile = _probe_state({"rhythm": "vf"})
    after, record = step(state, (), anchors, profile)
    moved = {"D": [state.D, after.D], "lactate_excess": [state.aux.lactate_excess_mmol_l,
                                                          after.aux.lactate_excess_mmol_l],
             "acid_burden": [state.aux.metabolic_acid_burden, after.aux.metabolic_acid_burden],
             "sympathetic_drive": [state.aux.sympathetic_drive, after.aux.sympathetic_drive],
             "collapse_burden": [state.aux.collapse_burden, after.aux.collapse_burden], "T": [state.T, after.T],
             "P": [state.P, after.P], "terminal_since": [state.terminal_since, after.terminal_since]}
    impossible = {}
    for label, args in (("pulseless_with_output", (RhythmCode.VF, None, 0.5, False)),
                        ("pulseless_organized_sinus", (RhythmCode.SINUS, 80.0, 1.0, False)),
                        ("perfusing_without_output", (RhythmCode.SINUS, 80.0, 0.0, True))):
        try:
            RhythmState(*args)
            impossible[label] = "CONSTRUCTIBLE"
        except CoreInvariantError:
            impossible[label] = "RAISES"
    base, _, _ = _probe_state({})
    try:
        dv.derive(base.evolve(P=1e-12), anchors, profile)
        zero = "SHOWN"
    except UnresolvedBoundary:
        zero = "STOPS_THE_RUN"
    near = reading(*_probe_state({"P": 0.02}))
    try:
        dv.derive(vs._probe_state(30.0, anchors, profile), anchors, profile)
        acid = "SHOWN"
    except UnresolvedBoundary:
        acid = "STOPS_THE_RUN"
    return {"pulseless": reading(state, anchors, profile), "one_minute": moved, "events": len(record.events),
            "readings": 4, "steps": 1,
            "impossible_rhythms": impossible, "pulse_with_zero_output": zero, "pulse_with_near_zero_flow": near,
            "acid_burden_30": acid,
            "reading": "pulse=false can never carry flow, pressure or delivery (the rhythm invariant and derive's "
                       "pulseless branch); pulse=true with output at the numerical zero is not representable (the run "
                       "stops), but pulse=true with output 0.02 is: MAP about 2 mmHg with a pulse, because the pulse is "
                       "rhythm semantics and nothing reads pressure to end it while the collapse rule is off"}


# 4. Persistence and event order of the existing P2E-3 rule (P2M-1-8, P2M-1-9) ---------------------------------------------------

#: P2E-3's committed synthetic test values (calibration registry 'collapse_rule_test_values', SYNTHETIC_ONLY).
TEST_THRESHOLD, TEST_LIMIT, TEST_TAU = 0.4, 10.0, 30.0


def _rule(**changes):
    return replace(vs.PROBE_PROFILE, **{"collapse_output_threshold": TEST_THRESHOLD,
                                        "collapse_burden_limit": TEST_LIMIT, **changes})


def _burden_series(levels, profile) -> list:
    """The core's own one-minute burden update over a sequence of pump levels (output = pump at tone 1)."""
    burden, out = 0.0, []
    for level in levels:
        state, anchors, _ = _probe_state({"P": level})
        state = state.evolve(aux=replace(state.aux, collapse_burden=burden))
        burden = dv.collapse_burden_after_minute(state, anchors, profile)
        out.append(burden)
    return out


def persistence() -> dict:
    held = _rule()
    repaid = _rule(collapse_repayment_tau_min=TEST_TAU)
    sustained = _burden_series([0.1] * 20, held)
    restored = _burden_series([0.1] * 8 + [1.0] * 60, held)
    restored_tau = _burden_series([0.1] * 8 + [1.0] * 60, repaid)
    pattern = ([0.1] + [1.0] * 9) * 24
    intermittent = _burden_series(pattern, held)
    intermittent_tau = _burden_series(pattern, repaid)
    one_minute = _burden_series([1e-3], held)
    try:    # accepted by the profile: no persistence floor is enforced
        loose, accepted = _rule(collapse_burden_limit=0.5), True
    except CoreInvariantError:
        loose, accepted = held, False
    single = _burden_series([0.1], loose)
    first = lambda series, limit: next((m + 1 for m, b in enumerate(series) if b >= limit), None)  # noqa: E731
    return {"values": {"threshold": TEST_THRESHOLD, "limit": TEST_LIMIT, "repayment_tau_min": TEST_TAU},
            "one_transient_minute": {"burden": one_minute[-1], "arrest": one_minute[-1] >= TEST_LIMIT},
            "sustained_output_0_1": {"criterion_minute": first(sustained, TEST_LIMIT), "per_minute": sustained[0]},
            "restored_after_8_min": {"burden_at_8": restored[7], "held_after_60": restored[-1],
                                     "repaid_after_60": restored_tau[-1]},
            "intermittent_1_in_10_for_4h": {"held_criterion_minute": first(intermittent, TEST_LIMIT),
                                            "repaid_max": max(intermittent_tau),
                                            "repaid_criterion_minute": first(intermittent_tau, TEST_LIMIT)},
            "single_minute_limit_0_5": {"criterion_minute": first(single, 0.5), "profile_accepts_it": accepted},
            "findings": {"persistence_exists": "aux.collapse_burden: a dedicated collapse memory (neither D nor F)",
                         "single_minute_arrest_not_excluded": "the profile accepts a limit at or below one minute's "
                                                              "maximal accrual, so an instantaneous one-minute arrest "
                                                              "is constructible",
                         "repayment_optional": "without a declared repayment the burden never falls: brief dips "
                                               "separated by normal flow accumulate to the transition"},
            "committed_rules": {k: {"rule": calibration.FROZEN_RULES[k].rule, "probe": calibration.FROZEN_RULES[k].probe}
                                for k in ("CO1", "CO2")},
            "burden_updates": sum(len(s) for s in (sustained, restored, restored_tau, intermittent, intermittent_tau,
                                                   one_minute, single)),
            "classification": "PERSISTENCE_STATE_OR_TIMER_REQUIRED: already present (P2E-3 collapse burden); two "
                              "invariants missing (a persistence floor, a mandatory repayment)"}


def event_order() -> dict:
    """The integrator's order, read from the code and checked on a sparse trajectory with the committed test rule."""
    tree = ast.parse((CORE_DIR / "integration.py").read_text(encoding="utf-8"))
    step_fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "step")
    calls = [n for n in ast.walk(step_fn) if isinstance(n, ast.Call)]
    burden_call = next(c for c in calls if getattr(c.func, "id", None) == "collapse_burden_after_minute")
    reached_call = next(c for c in calls if getattr(c.func, "id", None) == "collapse_reached")
    derive_calls = [c for c in calls if getattr(c.func, "id", None) == "derive"]
    reads_start_state = getattr(burden_call.args[0], "id", None) == "state" == getattr(reached_call.args[0], "id",
                                                                                         None)
    derive_on_new = any(getattr(c.args[0], "id", None) == "new_state" for c in derive_calls)
    profile = _rule()
    state, anchors, _ = _probe_state({"P": 0.1})
    trajectory = []
    for _ in range(20):
        burden_before = state.aux.collapse_burden
        state, record = step(state, (), anchors, profile)
        trajectory.append({"minute": state.minute, "pulse": state.R.pulse_present, "rhythm": state.R.code.value,
                           "burden": state.aux.collapse_burden, "burden_before": burden_before,
                           "transition": bool(record.transitions)})
    met = next(r for r in trajectory if r["transition"])
    after = [r for r in trajectory if r["minute"] > met["minute"]]
    return {"reads_start_state": reads_start_state, "derive_on_new_state": derive_on_new,
            "pulse_lost_minute": met["minute"], "burden_when_met": met["burden"],
            "previous_state_burden": met["burden_before"],
            "frozen_after_arrest": all(r["burden"] == met["burden"] and not r["transition"] for r in after),
            "no_retrigger": sum(r["transition"] for r in trajectory) == 1, "trajectory_steps": len(trajectory),
            "classification": "EXPLICIT_LAG_REQUIRED: already implemented (the criterion is read on the minute's "
                              "start state, the pulseless rhythm is the next state's; the detector never reads its "
                              "own result in the same step, needs a pulse to fire and freezes after arrest): ACYCLIC"}


# 5. ROSC (P2M-1-10), the carried extreme subset (P2M-1-11) --------------------------------------------------------------------

def rosc() -> dict:
    source = (CORE_DIR / "integration.py").read_text(encoding="utf-8")
    return {"status": "ROSC_NOT_CURRENTLY_MODELED",
            "guards": {"return_of_pulse_raises": "return of a pulse after arrest is not modelled" in source,
                       "terminal_since_never_cleared": "terminal_since if state.terminal_since is not None" in source},
            "reading": "a future return of circulation needs those two explicit guards lifted (and a rule that clears "
                       "terminal_since); the collapse burden is an ordinary auxiliary state a future rule can reset or "
                       "repay, so nothing in the existing structure, or in the minimum proposed here, makes it "
                       "architecturally impossible"}


def extreme_subset() -> dict:
    """The carried subset from committed records and the code's structure; flow only bounded (no reconstruction)."""
    p2l1 = _record(P2L1_RECORD, P2L1_RECORD_SHA)["extreme_acidemia"]
    p2k5 = _record(P2K5_RECORD, P2K5_RECORD_SHA)["demands"]["1.1"]["observed"]["extreme_acidemia"]
    lowest = p2k5["lowest"]
    pressure = p2l1["untreated_pressure_57m_d1.1"]
    map_low = min(p["map120"]["low"] for p in pressure.values())
    map_high = max(p["map120"]["high"] for p in pressure.values())
    sbp_low = min(p["sbp120"]["low"] for p in pressure.values())
    sbp_high = max(p["sbp120"]["high"] for p in pressure.values())
    anchors = gi_reference.canonical_anchors(C57)
    reserve = vs.PROBE_PROFILE.oxygen_extraction_reserve

    def pressure_of(target: float) -> float:
        lo, hi = 0.0, 2.0
        for _ in range(80):
            mid = (lo + hi) / 2.0
            lo, hi = (mid, hi) if dv.mean_arterial_pressure(mid, anchors, dv.DEFAULT_PROFILE) < target else (lo, mid)
        return lo

    effective = (1.1 - lowest["deficit"]) / reserve
    band = gi_reference.delivery_ratio_band(C57)
    return {"flagged": p2k5["flagged"], "by_case": p2k5["by_case"], "filtered": False,
            "map120": [map_low, map_high], "sbp120": [sbp_low, sbp_high],
            "pressure_rel120": [pressure_of(map_low), pressure_of(map_high)],
            "lowest": {k: lowest[k] for k in ("ph", "paco2", "deficit", "minute", "case")},
            "deficit_fraction_lowest": lowest["deficit"] / 1.1, "effective_delivery_lowest": effective,
            "delivery_rel_lowest": [effective / band.upper, effective / band.lower],
            "output_rel_bounds": [effective / band.upper, pressure_of(map_high)],
            "P": "1 (arrival): the untreated GI scenario writes no pump change (modules/gi_haemorrhage writes the blood "
                 "state only)",
            "R": "sinus with a pulse: no rhythm transition is declared and the collapse rule is off",
            "spo2": "97 (authored arrival; untreated FiO2 unchanged, and SpO2 moves only with FiO2)",
            "pulse": True,
            "bounds_reading": "output_rel at minute 120 lies between the effective delivery over the largest arrival "
                              "delivery ratio (Hb ratio at most 1) and the pressure the MAP implies (tone at least 1 under "
                              "the tone response); not reconstructed: the structural conclusion does not depend on it",
            "stability_problem": True,
            "missing_safety_mechanism": "ACTIVE_COMMON_COLLAPSE_RULE_MISSING: the P2E-3 structure exists but is off "
                                        "and reads output only; with it off, MAP 31-46 mmHg, a deficit of 0.84 and pH "
                                        "6.96 keep a pulse until a guard stops the run (zero output, HCO3 at 0, blood "
                                        "bounds), never an arrest"}


# 6. Generalization (P2M-1-12), the consciousness-trigger audit (P2M-1-13) ------------------------------------------------------

GENERALIZATION = {
    "hemorrhagic": ("V and Hb fall: flow, MAP and delivery fall together", "yes (flow falls)", "yes", "flow_C_both"),
    "cardiogenic": ("P falls: flow, MAP and delivery fall", "yes", "yes", "pump_A_pump_failure_organized_rhythm"),
    "obstructive_pe": ("no obstruction channel: the family's writer lowers effective preload / pump; PE adds hypoxaemia",
                       "yes for the flow part, no for the hypoxaemia", "yes (with arterial oxygenation)",
                       "flow_C_both"),
    "distributive_sepsis": ("T falls: MAP falls while flow is kept or rises; demand rises", "no (flow rises)", "yes "
                            "(perfusion pressure; demand through the deficit)", "flow_B_flow_kept_low_tone"),
    "anaphylaxis": ("T and V fall, airway: MAP first, flow later, hypoxaemia", "only once flow falls",
                    "yes", "flow_B_flow_kept_low_tone"),
    "malignant_arrhythmia": ("a pulseless rhythm is arrest at once (a rhythm transition, not collapse); a perfusing "
                             "low-output rhythm lowers flow", "pulseless: not collapse; with a pulse: yes", "same",
                             "pump_B_rhythm_low_output_with_pulse"),
    "hypoxaemia_respiratory_failure": ("SpO2 falls; the systemic deficit (extraction reserve) misses it to about 39 %; "
                                       "apnoea needs the respiratory family's writer", "no", "yes with arterial "
                                       "oxygenation; apnoea is the family's writer", "oxygen_E_arterial_hypoxaemia")}


PROPOSED_INPUTS = ("perfusion_pressure", "oxygen_delivery", "arterial_oxygenation")


def generalization(probe_rows: dict) -> dict:
    """Each family's representative fixed state: what the current output rule and the proposed signal can see."""
    rows = {}
    for k, v in GENERALIZATION.items():
        positive = set(probe_rows[v[3]]["positive"])
        rows[k] = {"pathway": v[0], "current_output_rule": v[1], "proposed_signal": v[2], "probe": v[3],
                   "current_sees": "output" in positive, "proposed_sees": bool(positive & set(PROPOSED_INPUTS)),
                   "mechanism": probe_rows[v[3]]["mechanism"]}
    current_gap = sorted(k for k, r in rows.items() if not r["current_sees"])
    proposed_ok = all(r["proposed_sees"] for r in rows.values())
    return {"rows": rows, "current": GENERALIZATION_CLASSES[1] if current_gap else GENERALIZATION_CLASSES[0],
            "current_gap": current_gap,
            "proposed": GENERALIZATION_CLASSES[0] if proposed_ok else GENERALIZATION_CLASSES[1],
            "condition": "the arterial-oxygenation input (a faculty decision) and each family's own writer of its "
                         "signal; no family term in the collapse layer"}


FORBIDDEN_TRIGGERS = ("consciousness_level", "lactate", "lactate_excess_mmol_l", "D", "encephalopathy",
                      "systemic_encephalopathy_burden", "impairment", "mental_status")


def trigger_audit() -> dict:
    """The collapse rule's code (derived's three functions, the integrator's collapse block) reads none of the
    forbidden triggers."""
    tree = ast.parse((CORE_DIR / "derived.py").read_text(encoding="utf-8"))
    names = set()
    for fn in tree.body:
        if isinstance(fn, ast.FunctionDef) and fn.name in ("collapse_burden_after_minute", "collapse_reached"):
            names |= {n.attr for n in ast.walk(fn) if isinstance(n, ast.Attribute)}
            names |= {n.id for n in ast.walk(fn) if isinstance(n, ast.Name)}
    source = (CORE_DIR / "integration.py").read_text(encoding="utf-8")
    block = source[source.index("# Terminal collapse (P2E-3)"):source.index("if profile.deficit_to_tone_gain")]
    return {"collapse_rule_reads": sorted(names & set(FORBIDDEN_TRIGGERS)),
            "integration_block_reads": sorted(t for t in FORBIDDEN_TRIGGERS if t in block),
            "terminal_rhythm_reads": "derive's monitor rate only (the PEA rate)",
            "reading": "no collapse code reads consciousness, lactate, D or the encephalopathy burden; consciousness is "
                       "downstream (derive's pulseless level 3; the P2L-2 candidate's maximal hypoperfusion without a "
                       "pulse)"}


# 7. The minimum structure, readiness, decisions ---------------------------------------------------------------------------------

REDUNDANCY = {
    "A_flow": "REDUNDANT_GIVEN_B_AND_E: flow reaches viability through perfusion pressure (pressure = flow x tone) and "
              "through delivery (delivery = flow x content); a low flow that neither lowers MAP nor exhausts extraction "
              "is not by itself non-viable",
    "B_perfusion_pressure": "NECESSARY: vasoplegia keeps flow and delivery while MAP falls (flow_B); only pressure sees "
                            "it",
    "C_pump": "REDUNDANT_VIA_FLOW: P enters output multiplicatively; reading it beside its consequences counts it twice",
    "D_rhythm": "SPLIT: a pulseless rhythm is arrest itself (a transition, not collapse); a perfusing rhythm's output "
                "factor enters flow like P",
    "E_oxygen_delivery": "NECESSARY: an oxygen-content failure keeps flow and MAP (oxygen_B); only the deficit sees it",
    "F_arterial_oxygenation": "DISTINCT_CANDIDATE: the systemic deficit misses arterial hypoxaemia to about 39 % at "
                              "normal flow and Hb (oxygen_E); the myocardium extracts near its maximum at rest, so a "
                              "separate input is plausible: faculty decision",
    "G_acid_base": "MODIFIER_NOT_INPUT: no path to P or R today; the acid burden integrates the deficit (P2L-2 M4), so "
                   "an additive pH input would recount a prolonged deficit; amplifier or myocardial depression are later "
                   "decisions",
    "H_respiratory_failure": "FUTURE: no apnoea or ventilatory-failure writer; it reaches viability through SpO2",
    "lactate_D_I_F": "EXCLUDED (faculty): consequences and markers, never triggers"}
def redundancy_evidence(pr: dict) -> dict:
    """The redundancy table, checked on the probes: each claim must hold on the fixed states."""
    rows = [r for r in pr["rows"].values() if r["reading"]["pulse"]]
    pos = [set(r["positive"]) for r in rows]
    return {
        "flow_never_alone": all(p & {"perfusion_pressure", "oxygen_delivery"} for p in pos if "output" in p),
        "pressure_needed": any("perfusion_pressure" in p and not p & {"output", "oxygen_delivery"} for p in pos),
        "delivery_needed": any("oxygen_delivery" in p and "perfusion_pressure" not in p for p in pos),
        "arterial_distinct": any("arterial_oxygenation" in p and "oxygen_delivery" not in p for p in pos),
        "pump_and_rhythm_through_flow": bool(pr["groups"]["pump_rhythm"]["rhythm_equals_pump_at_equal_output"]
                                             and pr["groups"]["pump_rhythm"]["pump_and_rhythm_failures_share_inputs"]),
        "pulseless_rhythm_is_arrest": pr["groups"]["pump_rhythm"]["pulseless_rhythm_is_arrest"],
        "acid_reaches_no_input": pr["rows"]["acid_severe_metabolic"]["positive"] == []
        and pr["rows"]["acid_severe_metabolic"]["reading"]["output_rel"] == pr["rows"]["reference"]["reading"][
            "output_rel"]}


MINIMUM = {
    "classification": STRUCTURE_CLASSES[1],
    "reuse": "the P2E-3 structure: aux.collapse_burden (a dedicated persistence memory, neither D nor F), its explicit "
             "one-minute lag, the terminal transition to a pulseless rhythm and the CO1 / CO2 rules",
    "new": "one derived common non-viability signal replacing output_rel as the burden's input: the maximum (never a "
           "sum) of perfusion-pressure failure (MAP), oxygen-delivery failure (the effective deficit) and, if the "
           "faculty decides, arterial-oxygenation failure (SpO2), with the dominant mechanism recorded "
           "(CIRCULATORY_COLLAPSE / METABOLIC_NONVIABILITY_RISK)",
    "invariants": "a persistence floor (no one-minute arrest: the limit above one minute's maximal accrual) and a "
                  "mandatory repayment whenever the rule is declared",
    "not_needed": "no new collapse state, no timer beside the burden, no pump or rhythm input, no flow input, no pH, "
                  "lactate, D, I or F input",
    "not_added_here": "nothing is implemented, activated or valued in P2M-1"}
RANGES = {"existing_committed_candidates": "the P2F calibration registry (CANDIDATE, not approved): burden per minute "
                                           "0.5 / 1 / 2, limit 5 / 15 / 30 minutes at full severity, repayment 30 / 60 "
                                           "/ 240 min; the output threshold 0.2 / 0.3 / 0.4 belongs to the output input "
                                           "the minimum replaces",
          "unset": "the bounds of the perfusion-pressure, oxygen-delivery and arterial-oxygenation failure signals, the "
                   "persistence floor, the terminal-rhythm selection rule: no committed common range; never from the GI "
                   "cases"}
READY = "COLLAPSE_STRUCTURE_READY_FOR_FACULTY_DECISION"
NOT_READY = "COLLAPSE_STRUCTURE_NOT_READY"
CRITERIA = ("pulse_semantics_explicit", "collapse_vs_arrest_separated", "causal_inputs_explicit",
            "redundancy_resolved", "persistence_classified", "event_order_safe", "generalization_plausible",
            "no_gi_threshold", "upstream_unchanged")
VERDICT_RULE = ("Predeclared. READY iff every criterion holds; otherwise NOT_READY - the first failing criterion as the "
                "blocker, every failing criterion listed. A changed upstream file stops the run before any probe.")
DECISIONS = (
    "the input of the existing collapse burden: replace output_rel by the maximum of perfusion-pressure failure (MAP) "
    "and oxygen-delivery failure (the effective deficit); confirm both mechanisms",
    "whether arterial oxygenation (SpO2) is a third input (the systemic deficit misses hypoxaemia to about 39 %)",
    "the two persistence invariants: no one-minute arrest (a floor on the limit) and a mandatory repayment",
    "acidemia: a consequence only (minimum), an amplifier of the burden, or a myocardial-depression path into P later",
    "zero flow: keep the run-stopping guard, or a same-minute definitional arrest when output reaches the numerical zero",
    "pulse semantics: the state's pulse stays rhythm semantics; whether a palpable-pulse observation is derived from "
    "pressure (a pulse with MAP about 2 mmHg is representable today)",
    "the terminal-rhythm selection rule (PEA or asystole, still TBD)",
    "the values: the new signals' bounds and the persistence floor stay UNSET until decided from general physiology; "
    "the P2F registry ranges for the persistence parameters are offered for review",
    "ROSC in a later package: lift the two guards and decide how the burden resets",
    "the next package: implement the decided collapse signal in the shadow core (off by default), then a second family")
POLICY = ("Shadow only and read-only: no core file, channel, rule, threshold or parameter changed or added; fixed core "
          "states, P2E-3's committed synthetic test values and committed records read with pinned hashes; the legacy "
          "engine quoted as text, never imported or fitted; the extreme subset kept; nothing selected, approved or "
          "activated.")
MIGRATION_GATE = ("MIGRATION_GATE_CLOSED: no collapse activation, numeric collapse filtering, arrest threshold, ROSC / "
                  "ACLS, runtime integration, GI or second-family migration is authorized")


def verdict(checks: dict) -> dict:
    failing = [c for c in CRITERIA if checks.get(c) is False]
    missing = [c for c in CRITERIA if c not in checks]
    if not failing and not missing:
        return {"verdict": READY, "checks": checks, "failing": [], "not_evaluated": []}
    return {"verdict": f"{NOT_READY} - {(failing + missing)[0].upper()}", "checks": checks, "failing": failing,
            "not_evaluated": missing}


# 8. Closure, freeze, run ----------------------------------------------------------------------------------------------------

#: The two tuple-only files at P2L-2 (b9e4913): P2M-1 adds its audit and report to their tuples, nothing else.
TUPLE_AT_P2L2 = {"clinical_core/lactate_slice.py": "03411e630d78b211bd8d00b47af05a72cc8f2f6afb78eafab1d1daf01763c2f3",
                 "clinical_core/decision_pack.py": "8f9e8e8ffff8195abd2b47710e0befa2f247f823ac93b065ce5ab07a001eec5b"}
TUPLES_ADDED = {"DOWNSTREAM_REPORTS": (REPORT,), "PACK_DIGEST_EXCLUDED": (OWN[0], REPORT)}
#: The whole P2L-2 tree's source map (b9e4913): every core and closed analysis file byte-identical.
SOURCES_AT_P2L2 = ("04bbfdd8f425384ee7dc6d7467818474d306e13a3ebac1153b88931ceed690fa", 66)


def p2l2_sources(sources: dict) -> dict:
    """A P2L-2 dependency map: P2M-1's audit removed, the two tuple-only files at their P2L-2 hashes while only their
    tuples changed (the tuple content itself is pinned by the tests)."""
    out = {k: v for k, v in sources.items() if k not in OWN}
    for relative, sha in TUPLE_AT_P2L2.items():
        item = vt.TUPLE_CHANGES[relative]
        if relative in out and vt.outside_digest(vt._live(relative), item["changed"]) == item["outside_p2j1"]:
            out[relative] = sha
    return out


def upstream_unchanged() -> dict:
    mapped = p2l2_sources(bf.freeze_sources())
    digest = hashlib.sha256(json.dumps(mapped, sort_keys=True).encode("utf-8")).hexdigest()
    return {"digest": digest, "files": len(mapped), "unchanged": (digest, len(mapped)) == SOURCES_AT_P2L2}


def design() -> dict:
    return {"revision": REVISION, "decided": DECIDED, "faculty": FACULTY, "status": STATUS,
            "mechanism_classes": list(MECHANISM_CLASSES), "structure_classes": list(STRUCTURE_CLASSES),
            "generalization_classes": list(GENERALIZATION_CLASSES), "pulse_semantics": PULSE_SEMANTICS,
            "mechanisms": {k: list(v) for k, v in MECHANISMS.items()}, "legacy": LEGACY, "probe_rule": PROBE_RULE,
            "probe_gain": PROBE_GAIN, "probes": {k: [v[0], v[1], v[2], list(v[3])] for k, v in PROBES.items()},
            "inputs": {k: list(v) for k, v in INPUTS.items()},
            "test_rule": [TEST_THRESHOLD, TEST_LIMIT, TEST_TAU],
            "generalization": {k: list(v) for k, v in GENERALIZATION.items()},
            "forbidden_triggers": list(FORBIDDEN_TRIGGERS), "redundancy": REDUNDANCY, "minimum": MINIMUM,
            "ranges": RANGES, "criteria": list(CRITERIA), "verdict_rule": VERDICT_RULE, "decisions": list(DECISIONS),
            "policy": POLICY, "migration_gate": MIGRATION_GATE, "own": list(OWN), "report": REPORT,
            "tuple_at_p2l2": TUPLE_AT_P2L2, "tuples_added": {k: list(v) for k, v in TUPLES_ADDED.items()},
            "sources_at_p2l2": list(SOURCES_AT_P2L2),
            "records": {"p2l1": P2L1_RECORD_SHA, "p2k5": P2K5_RECORD_SHA}}


def freeze_digest() -> str:
    text = json.dumps({"revision": REVISION, "p2l1": hashlib.sha256(P2L1_RECORD.read_bytes()).hexdigest(),
                       "p2k5": hashlib.sha256(P2K5_RECORD.read_bytes()).hexdigest(), "design": design(),
                       "sources": bf.freeze_sources()}, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run() -> dict:
    with lr.P2FGuard(), lr.LegacyLock():
        out = {"freeze_digest": freeze_digest(), "decided": DECIDED, "revision": REVISION, "policy": POLICY,
               "design": design(), "approval": STATUS["approved"], "migration_gate": MIGRATION_GATE,
               "upstream": upstream_unchanged()}
        checks = {"upstream_unchanged": out["upstream"]["unchanged"]}
        if not checks["upstream_unchanged"]:
            out["stopped"] = "an upstream file changed: STOP"
            out["verdict"] = verdict(checks)
            return out
        out.update({"pulse": pulse_scan(), "legacy_quoted": legacy_quoted(), "zero_flow": zero_flow(),
                    "probes": probes(), "persistence": persistence(), "event_order": event_order(), "rosc": rosc(),
                    "extreme_subset": extreme_subset(), "trigger_audit": trigger_audit()})
        out["generalization"] = generalization(out["probes"]["rows"])
        scan, zf, pr, order = out["pulse"], out["zero_flow"], out["probes"], out["event_order"]
        checks["pulse_semantics_explicit"] = bool(scan["transitions"] and scan["pulse_reads"]
                                                  and zf["impossible_rhythms"]["pulseless_with_output"] == "RAISES"
                                                  and zf["pulse_with_zero_output"] == "STOPS_THE_RUN")
        checks["collapse_vs_arrest_separated"] = bool(order["frozen_after_arrest"] and order["no_retrigger"]
                                                      and pr["rows"]["pump_B2_pulseless_rhythm"]["support"]["output"]
                                                      == "ARREST_NOT_COLLAPSE")
        pump = pr["groups"]["pump_rhythm"]
        checks["causal_inputs_explicit"] = bool(pr["all_as_expected"] and pr["groups"]["flow_map"]["distinguishable"]
                                                and pr["groups"]["oxygen"]["distinguishable"]
                                                and pump["rhythm_equals_pump_at_equal_output"]
                                                and pump["pump_and_rhythm_failures_share_inputs"]
                                                and pump["pulseless_rhythm_is_arrest"])
        out["redundancy_evidence"] = redundancy_evidence(pr)
        checks["redundancy_resolved"] = all(out["redundancy_evidence"].values())
        per = out["persistence"]
        checks["persistence_classified"] = bool(
            per["sustained_output_0_1"]["criterion_minute"] is not None and not per["one_transient_minute"]["arrest"]
            and per["intermittent_1_in_10_for_4h"]["held_criterion_minute"] is not None
            and per["intermittent_1_in_10_for_4h"]["repaid_criterion_minute"] is None
            and per["single_minute_limit_0_5"]["criterion_minute"] == 1)
        # The burden of minute m is read on the state of minute m - 1; the state of minute m is the pulseless one.
        checks["event_order_safe"] = bool(order["reads_start_state"] and order["derive_on_new_state"]
                                          and order["no_retrigger"] and order["frozen_after_arrest"]
                                          and order["previous_state_burden"] < TEST_LIMIT <= order["burden_when_met"]
                                          and order["pulse_lost_minute"] == out["persistence"]["sustained_output_0_1"][
                                              "criterion_minute"])
        checks["generalization_plausible"] = out["generalization"]["proposed"] == GENERALIZATION_CLASSES[0]
        checks["no_gi_threshold"] = (dv.DEFAULT_PROFILE.collapse_output_threshold is None
                                     and dv.DEFAULT_PROFILE.collapse_burden_limit is None
                                     and not out["trigger_audit"]["collapse_rule_reads"]
                                     and not out["trigger_audit"]["integration_block_reads"])
        out["redundancy"] = REDUNDANCY
        out["minimum"] = MINIMUM
        out["ranges"] = RANGES
        out["efficiency"] = {"fixed_state_readings": len(pr["rows"]) + zf["readings"],
                             "integrator_steps": zf["steps"] + order["trajectory_steps"],
                             "burden_updates": out["persistence"]["burden_updates"],
                             "records_read": ["P2L1_consciousness_audit.json", "P2K5_respiratory_monotonicity.json"],
                             "trajectory_simulations": int(order["trajectory_steps"] > 0), "gi_trajectories": 0,
                             "cartesian_sweep": False, "region_rebuilt": False, "legacy_engine_fitted": False,
                             "legacy_text_quoted": len(out["legacy_quoted"])}
        out["verdict"] = verdict(checks)
        out["decisions"] = list(DECISIONS)
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--digest", action="store_true")
    parser.add_argument("--design", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    if args.digest:
        print(freeze_digest())
        return 0
    if args.design:
        print(json.dumps(design(), indent=1, sort_keys=True, default=str))
        return 0
    if args.run:
        if args.out is None or ROOT in args.out.resolve().parents or args.out.resolve() == ROOT:
            parser.error("--run needs --out, a directory outside the repository")
        args.out.mkdir(parents=True, exist_ok=True)
        result = run()
        (args.out / "P2M1_collapse_audit.json").write_text(json.dumps(result, indent=1, sort_keys=True, default=str)
                                                            + "\n", encoding="utf-8")
        print(result["verdict"]["verdict"])
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
