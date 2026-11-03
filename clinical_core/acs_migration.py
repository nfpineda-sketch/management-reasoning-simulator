"""Phase 2 shadow core, P2N-2: acs_70f_left_main through the common physiology (cardiogenic shadow migration).

    python -m clinical_core.acs_migration --digest
    python -m clinical_core.acs_migration --design
    python -m clinical_core.acs_migration --run --out <directory outside the repository>

Shadow only. The case's arrival mapping (acs_reference) and its family writers (modules.acs_ischaemia) run through the
certified common core unchanged: arrival reconstruction, an untreated-ischaemia course over a predeclared sparse family
region, a matched fluid counterfactual, a matched reperfusion counterfactual, the collapse layer's structural reading
(never active), a legacy comparison read after the authored-truth assessment, the family / common boundary and the GI
non-regression. No common file changes, no common value is approved, no legacy output is a target, no collapse
threshold is chosen and nothing reaches runtime. Every definition below is frozen before any outcome is read.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from dataclasses import replace
from pathlib import Path

from . import acs_reference as ar
from . import blood_anchors as ba
from . import blood_fluid_calibration as bf
from . import collapse as cx
from . import derived as dv
from . import lactate_closure as lc
from . import lactate_rebuild as lr
from . import vascular_tone as vt
from . import ventilation_surface as vs
from .integration import step
from .interventions.fluids import Crystalloid
from .modules.acs_ischaemia import CoronaryReperfusion, IschaemicCongestion, IschaemicPump

DECIDED = "2026-11-03"
REVISION = "P2N-2"
ROOT = vs.ROOT
CORE_DIR = ROOT / "clinical_core"
OWN = ("clinical_core/acs_reference.py", "clinical_core/modules/acs_ischaemia.py", "clinical_core/acs_migration.py")
REPORT = "clinical_core/acs_migration_report.py"
#: The analysis and its report leave the P2G pack digest; the case mapping and the family writers stay in it.
TUPLES_ADDED = {"DOWNSTREAM_REPORTS": (REPORT,), "PACK_DIGEST_EXCLUDED": (OWN[2], REPORT)}
#: The P2M-2 tree (6601fc7): every core and closed analysis file byte-identical, and the two tuple-only files.
SOURCES_AT_P2M2 = ("96e4e100a51132cbe19271da5bb9ab32837aea9abbf73f88ccc004051af9a423", 69)
TUPLE_AT_P2M2 = {"clinical_core/decision_pack.py": "4752c81f9f247e7c9a96f5dd600e782645719983bd6ce50cf79ec4d427042af4",
                 "clinical_core/lactate_slice.py": "895f47a37055c045160d3553ac015fe32ff87b2866853cf07cea989c2c6c53be"}
P2M2_RECORD = ROOT / "docs" / "revision" / "P2M2_collapse_architecture.json"
P2M2_RECORD_SHA = "460acee4e937a028b73980a1650c3e6af3a0fe20928b3acc3c08a8dfb8fbe6cf"
C57 = "gi_bleed_57m"

FACULTY = {
    "objective": "acs_70f_left_main through the existing common physiology without retuning the GI core; shadow only",
    "p2n1": "GENERALIZES_WITH_NEW_FAMILY_WRITERS_ONLY; PROCEED_TO_CARDIOGENIC_SHADOW_MIGRATION",
    "authorized": "arrival mapping; ischaemic pump writer; reperfusion writer; congestion / L writer; observation layer; "
                  "case intrinsic sinus rate; family arrival latent mapping",
    "not_authorized": "common-core retuning; GI changes; runtime; collapse activation or thresholds; ROSC / ACLS; NIV; "
                      "common L -> G / SpO2; pressure -> tone baroreflex; P-dependent afterload; full ACS rollout; a "
                      "third family",
    "arrival_d": "a latent arrival-state variable; no lactate -> D rule",
    "pump": "the common P channel; no second pump equation; LV impairment kept through the arrival layer",
    "hr": "the common HR physiology only (intrinsic rate as a case mapping); no ACS sympathetic gain or HR residual",
    "deferred": {"baroreflex_to_tone": "BAROREFLEX_TO_TONE_COMMON_REFINEMENT_DEFERRED",
                 "p_afterload": "P_DEPENDENT_AFTERLOAD_REFINEMENT_DEFERRED",
                 "respiratory": "EXPECTED_RESPIRATORY_FAMILY_EXTENSION (L -> gas exchange, oxygenation, congestion "
                                "drive, NIV)",
                 "legacy_vf_120": "LEGACY_FAMILY_EVENT_DEFERRED",
                 "collapse_m1": "REQUIRED_BEFORE_ACTIVE_FAMILY_COLLAPSE",
                 "collapse_m2": "REQUIRED_BEFORE_RUNTIME_TRACE_INTEGRATION"}}

# Predeclared family region, counterfactuals and horizon (frozen before any run) -------------------------------------------------

HORIZON = 120
#: The ischaemic pump loss: 5 / 10 / 20 % of the arrival pump per hour (FAMILY_CANDIDATE, a sparse span, never fitted
#: to the legacy LV_LOSS_PER_MIN); the floor and the recovery are FAMILY_CANDIDATE too.
LOSS_PER_MIN = (0.05 / 60.0, 0.10 / 60.0, 0.20 / 60.0)
FLOOR = 0.5
#: The family congestion gain as a share of the common preload-congestion scale (congestion_per_excess_preload).
CONGESTION_SHARES = (0.5, 1.0, 2.0)
RECOVERY_SHARES = (0.0, 0.5, 1.0)
RECOVERY_TAU_MIN = 30.0
REFERENCE_WRITER = {"loss_per_min": LOSS_PER_MIN[1], "floor": FLOOR, "congestion_share": CONGESTION_SHARES[1],
                    "recovery_share": RECOVERY_SHARES[1], "recovery_tau_min": RECOVERY_TAU_MIN}
#: A synthetic reperfusion minute (no door-to-balloon time is authored; the legacy 90 min is LEGACY_REFERENCE_ONLY).
REPERFUSION_MINUTE = 60
#: The matched fluid counterfactual: 1000 mL crystalloid over 30 min (the GI reference crystalloid kinetics), read at
#: 60 min, in a pump-failure state (P 0.7 at a neutral arrival preload) and a pure preload deficiency (arrival low on the
#: preload curve, 0.25, normal pump and reserve), each against its own no-fluid course.
FLUID = {"volume_ml": 1000.0, "duration_min": 30.0, "read_minute": 60, "pump_failure_P": 0.7,
         "preload_deficiency_fraction": 0.25}
CRYSTALLOID = {k: ba.REFERENCE[k] for k in ("crystalloid_effective_ml_per_ml", "crystalloid_transient_share",
                                             "crystalloid_leak_tau_min")}
#: A structural collapse-test ramp (non-clinical: no-failure bound far above any MAP), never a clinical mapping.
STRUCTURAL_RAMP = (1000.0, 0.0)
COUNTERFACTUALS = {"untreated": "the reference arrival, the ischaemic pump and congestion writers, no reperfusion",
                   "reperfusion": "the same, with CoronaryReperfusion at REPERFUSION_MINUTE, recovery share 0 / 0.5 / 1",
                   "fluid": "FLUID, pump failure vs pure preload deficiency, each against its own no-fluid course"}


def writers(loss: float = LOSS_PER_MIN[1], share: float = CONGESTION_SHARES[1], recovery: float = RECOVERY_SHARES[1],
            reperfusion: int | None = None) -> tuple:
    items = (IschaemicPump("acs-pump", loss, FLOOR, recovery, RECOVERY_TAU_MIN),
             IschaemicCongestion("acs-congestion", share * dv.DEFAULT_PROFILE.congestion_per_excess_preload))
    return items + ((CoronaryReperfusion("acs-pci", reperfusion),) if reperfusion is not None else ())


def course(items: tuple, minutes: int = HORIZON, anchors=None, profile=None, start=None) -> list:
    anchors = ar.anchors() if anchors is None else anchors
    profile = ar.common_profile() if profile is None else profile
    state = dv.arrival_state(anchors, profile) if start is None else start
    states, records = [state], []
    for _ in range(minutes):
        state, record = step(state, items, anchors, profile)
        states.append(state)
        records.append(record)
    return states, records


def row(state, anchors, profile) -> dict:
    d = dv.derive(state, anchors, profile)
    gas = vs._vr(state, anchors, profile, vs.VENTILATION_GAINS[2])
    return {"minute": state.minute, "V": state.V, "T": state.T, "P": state.P, "R": state.R.code.value, "L": state.L,
            "G": state.G, "W": state.W, "D": state.D, "N": state.N, "hr": d.monitor_rate_bpm, "sbp": d.sbp,
            "dbp": d.dbp, "map": d.map, "spo2": d.spo2, "rr": d.respiratory_rate, "lactate": d.lactate,
            "ph": gas["ph"], "paco2": gas["paco2"], "consciousness_level": d.consciousness_level,
            "output_rel": d.output_rel, "delivery_rel": d.delivery_rel,
            "delivery_index": dv.effective_delivery(d.delivery_rel, anchors),
            "deficit": dv.acute_deficit_signal(state, anchors, profile), "drive": state.aux.sympathetic_drive,
            "pulse": d.pulse_present}


# P2N-2A / -K: arrival ----------------------------------------------------------------------------------------------------------

def arrival() -> dict:
    a, p = ar.anchors(), ar.common_profile()
    s = dv.arrival_state(a, p)
    r = row(s, a, p)
    t = ar.truth()
    hr = {point: row(dv.arrival_state(ar.anchors(point), p), ar.anchors(point), p)["hr"] for point in
          ("lower", "midpoint", "upper")}
    return {"truth": t, "authored_map": ar.authored_map(t), "anchors": a.to_dict(), "row": r,
            "classes": ar.ARRIVAL_CLASSES, "channel_roles": ar.CHANNEL_ROLES,
            "bands": {k: vars(v) for k, v in ar.bands().items()},
            "reconstruction": {"hr": [r["hr"], t["hr"]], "sbp": [r["sbp"], t["sbp"]], "dbp": [r["dbp"], t["dbp"]],
                               "map": [r["map"], ar.authored_map(t)], "spo2": [r["spo2"], t["spo2"]],
                               "rr": [r["rr"], t["respiratory_rate"]], "lactate": [r["lactate"], t["lactate_mmol_l"]],
                               "ph": [r["ph"], t["abg_ph"]], "paco2": [r["paco2"], t["abg_paco2"]],
                               "mental_status": [r["consciousness_level"], t["mental_status"]]},
            "hr_over_intrinsic_band": hr, "arrival_deficit": r["deficit"], "arrival_drive": r["drive"],
            "lv_impairment_kept": {"pump_reserve": a.pump_reserve, "arrival_delivery_ratio": a.arrival_delivery_ratio,
                                   "P": s.P}}


def lactate_does_not_set_d() -> dict:
    """Changing the arrival lactate alone does not recompute the arrival D (no lactate -> D rule)."""
    base = ar.anchors()
    t = ar.truth()
    other = replace(base, lactate=t["lactate_mmol_l"] * 2.0)
    p = ar.common_profile()
    return {"d_base": dv.arrival_state(base, p).D, "d_other_lactate": dv.arrival_state(other, p).D,
            "lactates": [base.lactate, other.lactate],
            "mapping_takes_no_lactate": "lactate" not in ar.arrival_oxygen_debt.__code__.co_varnames,
            "pass": dv.arrival_state(base, p).D == dv.arrival_state(other, p).D}


def pump_semantics() -> dict:
    """P2N-2B: how the arrival pump impairment is carried, read from the code (no second pump equation)."""
    source = (CORE_DIR / "derived.py").read_text(encoding="utf-8")
    return {"P_relative_to_arrival": "Channel.P: multiplier, arrival = 1",
            "output": "output_rel = P x rhythm share x preload response (on the current pump's curve, relative to "
                      "arrival filling) x afterload (derived._perfusion)",
            "preload": "the curve's scale is preload_curve_scale_ml x P^c (derived.preload_position): a falling P lowers "
                       "the plateau and the gain per mL",
            "reserve": "pump_reserve enters only the congestion shortfall 1 - reserve x P (derived.congestion_rate)",
            "absolute_impairment": "the arrival layer: arrival_delivery_ratio (DO2 index against normal, "
                                   "derived.effective_delivery) and pump_reserve; never multiplied into output again",
            "double_counting": False,
            "second_pump_equation": source.count("def _perfusion") == 1 and "acs" not in source.lower(),
            "pending_common_decision": "a depressed pump without added volume does not congest through the common "
                                       "coupling (derived.congestion_rate's own note): the family congestion writer "
                                       "carries the cardiogenic part"}


# P2N-2L: untreated ischaemia over the predeclared family region -------------------------------------------------------------------

def _summary(states, anchors, profile) -> dict:
    rows = [row(s, anchors, profile) for s in states]
    first, last = rows[0], rows[-1]
    p = [r["P"] for r in rows]
    return {"first": first, "last": last, "at": {str(m): rows[m] for m in (0, 30, 60, 90, 120) if m < len(rows)},
            "P_nonincreasing": all(b <= a + 1e-15 for a, b in zip(p, p[1:])),
            "Q_down": last["output_rel"] < first["output_rel"], "map_down": last["map"] < first["map"],
            "delivery_down": last["delivery_index"] < first["delivery_index"],
            "deficit_up": last["deficit"] >= first["deficit"], "D_up": last["D"] >= first["D"],
            "L_up": last["L"] > first["L"], "pulse_kept": all(r["pulse"] for r in rows)}


def _family_writes(records) -> dict:
    channels, others = set(), []
    for record in records:
        for delta in record.deltas:
            if delta.source.kind.value == "disease_module":
                channels.add(delta.channel.value)
        family = [x for x in (record.transitions + record.settings + record.demand + record.blood)
                  if getattr(x, "source", None) is not None and x.source.kind.value == "disease_module"]
        others.extend(family)
    return {"channels": sorted(channels), "other_writes": len(others)}


def lactate_coherence(states, records, anchors, profile) -> dict:
    """Lactate is the core's: every minute's excess is derived.lactate_after_minute of the minute before."""
    ok = all(abs(after.aux.lactate_excess_mmol_l - dv.lactate_after_minute(before, profile)) < 1e-12
             for before, after in zip(states, states[1:]))
    return {"core_lactate_every_minute": ok,
            "no_family_lactate_write": all(c.source.kind.value != "disease_module" for r in records
                                           for c in r.auxiliary)}


def untreated() -> dict:
    a, p = ar.anchors(), ar.common_profile()
    out = {"region": {}, "congestion": {}, "tone": {}, "k_ld": {}}
    for loss in LOSS_PER_MIN:
        states, records = course(writers(loss=loss))
        out["region"][f"{loss:.6g}"] = {**_summary(states, a, p), "writes": _family_writes(records),
                                         "lactate": lactate_coherence(states, records, a, p)}
    for share in CONGESTION_SHARES:
        states, _ = course(writers(share=share))
        out["congestion"][str(share)] = _summary(states, a, p)["last"]["L"]
    for gain in ar.TONE_SENSITIVITY:
        q = ar.common_profile(deficit_to_tone_gain=gain)
        states, _ = course(writers(), profile=q)
        out["tone"][str(gain)] = {k: _summary(states, a, q)["last"][k] for k in ("P", "output_rel", "map", "T", "D")}
    for k in lc.K_LD:
        q = ar.common_profile(debt_to_lactate_gain=k)
        states, _ = course(writers(), profile=q)
        rows = [row(s, a, q) for s in (states[0], states[60], states[-1])]
        out["k_ld"][f"{k:.6g}"] = [r["lactate"] for r in rows]
    out["steps"] = HORIZON * (len(LOSS_PER_MIN) + len(CONGESTION_SHARES) + len(ar.TONE_SENSITIVITY) + len(lc.K_LD))
    reference = out["region"][f"{LOSS_PER_MIN[1]:.6g}"]
    out["directions"] = {k: all(out["region"][x][k] for x in out["region"]) for k in
                         ("P_nonincreasing", "Q_down", "map_down", "delivery_down", "deficit_up", "D_up", "L_up",
                          "pulse_kept")}
    out["family_writes_only_P_and_L"] = all(r["writes"]["channels"] == ["L", "P"] and r["writes"]["other_writes"] == 0
                                            for r in out["region"].values())
    out["lactate_core_only"] = all(r["lactate"]["core_lactate_every_minute"] and r["lactate"]["no_family_lactate_write"]
                                   for r in out["region"].values())
    out["hr_up_through_drive"] = reference["last"]["hr"] > reference["first"]["hr"] and \
        reference["last"]["drive"] > reference["first"]["drive"]
    return out


# P2N-2N: reperfusion counterfactual ----------------------------------------------------------------------------------------------

def reperfusion() -> dict:
    a, p = ar.anchors(), ar.common_profile()
    base, _ = course(writers())
    ongoing = row(base[-1], a, p)
    out = {"ongoing": {k: ongoing[k] for k in ("P", "output_rel", "map", "delivery_index", "deficit", "D", "lactate",
                                               "L", "hr")}, "shares": {}}
    for share in RECOVERY_SHARES:
        states, records = course(writers(recovery=share, reperfusion=REPERFUSION_MINUTE))
        last = row(states[-1], a, p)
        p_series = [s.P for s in states]
        out["shares"][str(share)] = {
            **{k: last[k] for k in ("P", "output_rel", "map", "delivery_index", "deficit", "D", "lactate", "L", "hr")},
            "P_at_reperfusion": states[REPERFUSION_MINUTE].P,
            "P_stops_falling": all(b >= a_ - 1e-15 for a_, b in zip(p_series[REPERFUSION_MINUTE:],
                                                                   p_series[REPERFUSION_MINUTE + 1:])),
            "writes": _family_writes(records)}
    out["P_better_than_ongoing"] = all(v["P"] >= ongoing["P"] for v in out["shares"].values())
    out["downstream_follow"] = all(v["output_rel"] >= ongoing["output_rel"] and v["deficit"] <= ongoing["deficit"] + 1e-12
                                   for v in out["shares"].values())
    out["only_P_and_L_written"] = all(set(v["writes"]["channels"]) <= {"P", "L"} and v["writes"]["other_writes"] == 0
                                      for v in out["shares"].values())
    out["reperfusion_minute"] = REPERFUSION_MINUTE
    return out


# P2N-2M: matched fluid counterfactual -------------------------------------------------------------------------------------------

def _bag():
    # The untimed rate is unused for a timed bag; the core requires it positive: the bag's own rate.
    return Crystalloid("acs-fluid", 0, FLUID["volume_ml"], FLUID["duration_min"],
                       FLUID["volume_ml"] / FLUID["duration_min"],
                       CRYSTALLOID["crystalloid_effective_ml_per_ml"], CRYSTALLOID["crystalloid_transient_share"],
                       CRYSTALLOID["crystalloid_leak_tau_min"])


def fluid() -> dict:
    p = ar.common_profile()
    weak_a = ar.anchors()
    weak = dv.arrival_state(weak_a, p).evolve(P=FLUID["pump_failure_P"])
    dry_a = ar.anchors(preload_fraction=FLUID["preload_deficiency_fraction"], pump_reserve=1.0)
    dry_a = replace(dry_a, declared={**dict(dry_a.declared), "preload_fraction": "synthetic_probe"})
    dry = dv.arrival_state(dry_a, p)
    out = {}
    for name, anchors, start in (("pump_failure", weak_a, weak), ("preload_deficiency", dry_a, dry)):
        dry_run, _ = course((), FLUID["read_minute"], anchors, p, start)
        wet_run, _ = course((_bag(),), FLUID["read_minute"], anchors, p, start)
        a0, d0, w0 = (row(x, anchors, p) for x in (start, dry_run[-1], wet_run[-1]))
        out[name] = {"output_start": a0["output_rel"], "output_without": d0["output_rel"], "output_with": w0["output_rel"],
                     "output_gain": w0["output_rel"] - d0["output_rel"], "map_gain": w0["map"] - d0["map"],
                     "L_without": d0["L"], "L_with": w0["L"], "position_with": dv.preload_position(wet_run[-1], anchors, p),
                     "deficit_with": w0["deficit"]}
    out["less_benefit_in_weak_pump"] = out["pump_failure"]["output_gain"] < out["preload_deficiency"]["output_gain"]
    out["volume_improves_preload"] = out["preload_deficiency"]["output_gain"] > 0.0
    out["no_normalization_of_pump_failure"] = out["pump_failure"]["output_with"] < 1.0
    out["congestion_visible"] = out["pump_failure"]["L_with"] >= out["pump_failure"]["L_without"]
    out["design"] = FLUID
    return out


# P2N-2O: collapse, structural only (never active) ---------------------------------------------------------------------------------

def collapse_compatibility() -> dict:
    a, p = ar.anchors(), ar.common_profile()
    states, _ = course(writers())
    ramp = cx.CollapseProfile(perfusion_mapping=cx.PerfusionMapping(*STRUCTURAL_RAMP))
    rows = []
    for s in (states[0], states[60], states[-1]):
        reading = cx.readings(s, a, p)
        unset = cx.signal_at(reading, cx.CollapseProfile())
        structural = cx.signal_at(reading, ramp)
        rows.append({"minute": s.minute, "delivery": unset.delivery, "unset_perfusion": unset.perfusion,
                     "unset_complete": unset.complete, "structural_perfusion": structural.perfusion,
                     "structural_value": structural.value,
                     "max_holds": structural.value == max(structural.perfusion, structural.delivery)})
    source = (CORE_DIR / "collapse.py").read_text(encoding="utf-8").lower()
    return {"rows": rows, "max_holds": all(r["max_holds"] for r in rows),
            "unset_is_lower_bound": all(not r["unset_complete"] for r in rows),
            "no_family_rule": not any(word in source for word in ("acs", "cardiogenic", "ischaem", "coronary")),
            "active": False, "thresholds_selected": False, "terminal_transition": False,
            "m1": FACULTY["deferred"]["collapse_m1"], "m2": FACULTY["deferred"]["collapse_m2"]}


# P2N-2P: legacy comparison (after the authored-truth assessment; never a target) ------------------------------------------------

LEGACY_MINUTES = (0, 30, 60, 90, 120)


def legacy() -> dict:
    """The family engine's untreated course, read as LEGACY_REFERENCE_ONLY."""
    from . import legacy_adapter as la
    engine = la._engine()
    current = la.bank_case(ar.CASE, family=ar.FAMILY)
    engine._initialize(current)
    out = {}
    for minute in range(max(LEGACY_MINUTES) + 1):
        if minute in LEGACY_MINUTES:
            o = current.get("observable", {})
            out[str(minute)] = {k: o.get(k) for k in ("sbp", "dbp", "hr", "spo2", "respiratory_rate", "rhythm",
                                                      "mental_status", "pulse_present")}
        if minute < max(LEGACY_MINUTES):
            engine.advance_clinical_time(current, 1)
    return out


def legacy_comparison(untreated_out: dict, legacy_rows: dict) -> dict:
    core = untreated_out["region"][f"{LOSS_PER_MIN[1]:.6g}"]["at"]
    rows = {}
    for m in ("0", "60", "90", "120"):
        lg, cr = legacy_rows.get(m, {}), core.get(m, {})
        rows[m] = {"legacy": lg, "core": {k: cr.get(k) for k in ("sbp", "hr", "spo2", "rr")}}
    classes = {
        "sbp_course": "LEGACY_DIFFERENCE_NOT_CLINICALLY_RELEVANT: both fall under untreated ischaemia; the size is the "
                      "family candidate's and the legacy drift's, neither authored",
        "spo2_course": "EXPECTED_EXTENSION_NOT_YET_MODELED: the legacy SpO2 falls with congestion; the core's L has no "
                       "gas-exchange path (EXPECTED_RESPIRATORY_FAMILY_EXTENSION)",
        "vf_120": "EXPECTED_EXTENSION_NOT_YET_MODELED: LEGACY_FAMILY_EVENT_DEFERRED (no scripted VF, no ROSC / ACLS)",
        "hr_arrival": "LEGACY_DIFFERENCE_NOT_CLINICALLY_RELEVANT: the legacy shows the authored HR; the core's is the "
                      "common HR physiology's at the midpoint intrinsic rate (reported, not absorbed)"}
    return {"rows": rows, "classes": classes, "possible_common_core_gap": [], "used_for_parameters": False}


# P2N-2Q / -R: boundary and GI non-regression ---------------------------------------------------------------------------------

#: Names a family writer must never write or read as its output.
NEVER_WRITTEN = ("sbp", "dbp", "map", "spo2", "delivery_rel", "lactate", "lactate_excess_mmol_l", "sympathetic_drive",
                 "consciousness_level", "metabolic_acid_burden", "collapse_burden", "monitor_rate_bpm")
COMMON_FILES = ("derived.py", "integration.py", "state.py", "provenance.py", "collapse.py", "encephalopathy.py",
                "ventilation.py", "signals.py", "legacy_adapter.py")


def boundary() -> dict:
    tree = ast.parse((CORE_DIR / "modules" / "acs_ischaemia.py").read_text(encoding="utf-8"))
    channels = sorted({n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)
                       and getattr(n.value, "id", None) == "Channel"})
    attrs = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    calls = {getattr(n.func, "id", None) or getattr(n.func, "attr", None) for n in ast.walk(tree)
             if isinstance(n, ast.Call)}
    leaks = {name: "acs" in (CORE_DIR / name).read_text(encoding="utf-8").lower().replace("access", "")
             for name in COMMON_FILES}
    classes = {"IschaemicPump": "FAMILY_WRITER (P)", "IschaemicCongestion": "FAMILY_WRITER (L)",
               "CoronaryReperfusion": "FAMILY_WRITER (logistic signal, no write)", "anchors": "ARRIVAL_MAPPING",
               "OBSERVATION_LAYER": "OBSERVATION_LAYER", "legacy": "LEGACY_ONLY"}
    return {"writer_channels": channels, "writer_never_names": sorted(attrs & set(NEVER_WRITTEN)),
            "writer_other_writes": sorted(calls & {"BloodFlow", "SettingChange", "DemandModifier", "RhythmTransition",
                                                   "AuxiliaryChange"}),
            "common_files_name_acs": [k for k, v in leaks.items() if v], "classes": classes,
            "pass": channels == ["L", "P"] and not attrs & set(NEVER_WRITTEN) and not any(leaks.values())
            and not calls & {"BloodFlow", "SettingChange", "DemandModifier", "RhythmTransition", "AuxiliaryChange"}}


def p2m2_sources(sources: dict) -> dict:
    """A P2M-2 dependency map: P2N-2's files removed, the two tuple-only files at their P2M-2 hashes while only their
    tuples changed (the tuple content itself is pinned by the tests)."""
    out = {k: v for k, v in sources.items() if k not in OWN}
    for relative, sha in TUPLE_AT_P2M2.items():
        item = vt.TUPLE_CHANGES[relative]
        if relative in out and vt.outside_digest(vt._live(relative), item["changed"]) == item["outside_p2j1"]:
            out[relative] = sha
    return out


def upstream_unchanged() -> dict:
    mapped = p2m2_sources(bf.freeze_sources())
    digest = hashlib.sha256(json.dumps(mapped, sort_keys=True).encode("utf-8")).hexdigest()
    readers = sorted(p.relative_to(ROOT).as_posix() for p in CORE_DIR.rglob("*.py")
                     if p.relative_to(ROOT).as_posix() not in OWN and p.name != Path(REPORT).name
                     and ("acs_ischaemia" in p.read_text(encoding="utf-8")
                          or "acs_reference" in p.read_text(encoding="utf-8")))
    return {"digest": digest, "files": len(mapped), "unchanged": (digest, len(mapped)) == SOURCES_AT_P2M2,
            "core_readers_of_family": readers}


def gi_nonregression(minutes: int = 120) -> dict:
    """The GI untreated course with the ACS writers present at zero rates equals it without them (channels and
    auxiliary state); the ACS writers never act unless declared."""
    anchors, profile, values = ba.setup(C57)
    items = ba.contributors(C57, "untreated", values)
    plain, _ = course(items, minutes, anchors, profile)
    inert = (IschaemicPump("acs-inert", 0.0, 1.0, 0.0, 1.0), IschaemicCongestion("acs-inert-l", 0.0))
    mixed, records = course(items + inert, minutes, anchors, profile)

    def physiology(s):
        return (s.V, s.T, s.P, s.R, s.L, s.G, s.W, s.D, s.N, s.hb, s.glucose, s.k, s.aux, s.blood)

    return {"minutes": minutes, "identical": [physiology(s) for s in plain] == [physiology(s) for s in mixed],
            "inert_writes": sum(1 for r in records for d in r.deltas if d.source.id.startswith("acs-inert")),
            "digest": hashlib.sha256(json.dumps([[s.V, s.T, s.P, s.L, s.D, s.hb, s.aux.lactate_excess_mmol_l,
                                                  s.aux.sympathetic_drive] for s in plain]).encode()).hexdigest()}


# Verdict and recommendation ---------------------------------------------------------------------------------------------------

READY = "CARDIOGENIC_SHADOW_MIGRATION_READY"
NOT_READY = "CARDIOGENIC_SHADOW_MIGRATION_NOT_READY"
CRITERIA = ("arrival_representable", "pump_through_P", "ischaemia_writer_evolves_P", "common_downstream",
            "d_lactate_coherent", "reperfusion_targets_P", "L_represents_congestion", "no_core_retuning",
            "gi_unchanged", "respiratory_deferred", "collapse_structural", "collapse_inactive", "legacy_not_target",
            "boundaries_hold")
VERDICT_RULE = "Predeclared. READY iff every criterion holds; otherwise NOT_READY - the first failing criterion."
RECOMMENDATION_RULE = (
    "Predeclared. With READY: IMPLEMENT_EXPECTED_RESPIRATORY_EXTENSION when the case's authored congestion has no "
    "downstream path in the core (L rises with no SpO2 / G change) and the legacy comparison carries a respiratory "
    "EXPECTED_EXTENSION; otherwise PROCEED_TO_CARDIOGENIC_CASE_EXPANSION; TEST_THIRD_MECHANISTIC_FAMILY only if both "
    "the respiratory extension and case expansion are found unnecessary.")
POLICY = ("Shadow only: no common file changes; the case mapping and the family writers are declared, never approved; "
          "the common profile is one predeclared point of the GI-carried uncertainty; no legacy output is a target; "
          "collapse is read structurally and never acts; nothing reaches runtime.")
MIGRATION_GATE = ("MIGRATION_GATE_CLOSED: no runtime hook, collapse activation, clinical collapse threshold, ROSC / ACLS, "
                  "NIV, common L -> G / SpO2, baroreflex -> tone, P-dependent afterload, full ACS rollout or third family.")
DECISIONS = (
    "the arrival mapping's candidates (pump reserve, arrival delivery ratio, arrival D, lactate excess, intrinsic sinus "
    "rate): FAMILY_CANDIDATE / CASE_MAPPING values to accept, narrow or replace",
    "the ischaemic family writer's kinetics (loss per minute, floor, recovery share and time) and the congestion gain",
    "whether a common P -> L coupling replaces the family congestion writer (derived.congestion_rate's pending note)",
    "the arrival HR: the common physiology at the midpoint intrinsic rate reads below the authored 112; accept the gap, "
    "narrow the intrinsic band, or revisit the common HR gains (never an ACS residual)",
    "the next package (the recommendation)")


def verdict(checks: dict) -> dict:
    failing = [name for name in CRITERIA if not checks.get(name)]
    return {"checks": {name: bool(checks.get(name)) for name in CRITERIA}, "rule": VERDICT_RULE,
            "verdict": READY if not failing else f"{NOT_READY} — {failing[0]}", "failing": failing}


def recommendation(out: dict) -> str:
    if out["verdict"]["failing"]:
        return None
    ref = out["untreated"]["region"][f"{LOSS_PER_MIN[1]:.6g}"]
    respiratory_gap = ref["L_up"] and ref["first"]["spo2"] == ref["last"]["spo2"] and \
        ref["first"]["G"] == ref["last"]["G"]
    legacy_respiratory = out["legacy_comparison"]["classes"]["spo2_course"].startswith("EXPECTED_EXTENSION")
    if respiratory_gap and legacy_respiratory:
        return "IMPLEMENT_EXPECTED_RESPIRATORY_EXTENSION"
    return "PROCEED_TO_CARDIOGENIC_CASE_EXPANSION"


def design() -> dict:
    return {"revision": REVISION, "decided": DECIDED, "faculty": FACULTY, "case": ar.CASE, "truth_paths":
            {k: list(v) for k, v in ar.TRUTH_PATHS.items()}, "arrival_classes": ar.ARRIVAL_CLASSES,
            "channel_roles": ar.CHANNEL_ROLES, "bands": {k: vars(v) for k, v in ar.bands().items()},
            "common_reference": {k: [list(v) if isinstance(v, tuple) else v, why] for k, (v, why) in
                                 ar.COMMON_REFERENCE.items()},
            "tone_sensitivity": list(ar.TONE_SENSITIVITY), "observation_layer": ar.OBSERVATION_LAYER,
            "horizon": HORIZON, "loss_per_min": list(LOSS_PER_MIN), "floor": FLOOR,
            "congestion_shares": list(CONGESTION_SHARES), "recovery_shares": list(RECOVERY_SHARES),
            "recovery_tau_min": RECOVERY_TAU_MIN, "reference_writer": REFERENCE_WRITER,
            "reperfusion_minute": REPERFUSION_MINUTE, "fluid": FLUID, "crystalloid": CRYSTALLOID,
            "structural_ramp": list(STRUCTURAL_RAMP), "counterfactuals": COUNTERFACTUALS,
            "legacy_minutes": list(LEGACY_MINUTES), "never_written": list(NEVER_WRITTEN),
            "common_files": list(COMMON_FILES), "criteria": list(CRITERIA), "verdict_rule": VERDICT_RULE,
            "recommendation_rule": RECOMMENDATION_RULE, "decisions": list(DECISIONS), "policy": POLICY,
            "migration_gate": MIGRATION_GATE, "own": list(OWN), "report": REPORT,
            "tuples_added": {k: list(v) for k, v in TUPLES_ADDED.items()}, "tuple_at_p2m2": TUPLE_AT_P2M2,
            "sources_at_p2m2": list(SOURCES_AT_P2M2), "p2m2_record": P2M2_RECORD_SHA}


def freeze_digest() -> str:
    text = json.dumps({"revision": REVISION, "p2m2": hashlib.sha256(P2M2_RECORD.read_bytes()).hexdigest(),
                       "design": design(), "sources": bf.freeze_sources()}, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run() -> dict:
    with lr.P2FGuard(), lr.LegacyLock():
        out = {"freeze_digest": freeze_digest(), "decided": DECIDED, "revision": REVISION, "policy": POLICY,
               "design": design(), "migration_gate": MIGRATION_GATE, "upstream": upstream_unchanged()}
        if not out["upstream"]["unchanged"] or out["upstream"]["core_readers_of_family"]:
            out["stopped"] = "an upstream file changed or the common core reads the family: STOP"
            out["verdict"] = verdict({})
            return out
        out.update({"arrival": arrival(), "lactate_d": lactate_does_not_set_d(), "pump": pump_semantics(),
                    "untreated": untreated(), "reperfusion": reperfusion(), "fluid": fluid(),
                    "collapse": collapse_compatibility(), "boundary": boundary(), "gi": gi_nonregression()})
    out["legacy"] = legacy()
    out["legacy_comparison"] = legacy_comparison(out["untreated"], out["legacy"])
    u, rp, arr = out["untreated"], out["reperfusion"], out["arrival"]
    checks = {
        "arrival_representable": arr["row"]["pulse"] and abs(arr["row"]["map"] - arr["authored_map"]) < 1e-9
        and arr["row"]["spo2"] == arr["truth"]["spo2"] and arr["row"]["lactate"] == arr["truth"]["lactate_mmol_l"],
        "pump_through_P": not out["pump"]["double_counting"] and out["pump"]["second_pump_equation"],
        "ischaemia_writer_evolves_P": u["directions"]["P_nonincreasing"] and u["family_writes_only_P_and_L"],
        "common_downstream": u["directions"]["Q_down"] and u["directions"]["delivery_down"] and u["hr_up_through_drive"],
        "d_lactate_coherent": u["lactate_core_only"] and out["lactate_d"]["pass"] and u["directions"]["D_up"],
        "reperfusion_targets_P": rp["P_better_than_ongoing"] and rp["downstream_follow"] and rp["only_P_and_L_written"],
        "L_represents_congestion": u["directions"]["L_up"],
        "no_core_retuning": out["upstream"]["unchanged"] and not out["upstream"]["core_readers_of_family"],
        "gi_unchanged": out["gi"]["identical"] and out["gi"]["inert_writes"] == 0,
        # The respiratory extension stays out: over the whole course L moves while G and SpO2 do not (no L -> G / SpO2).
        "respiratory_deferred": all(r["first"]["G"] == r["last"]["G"] == 0.0 and r["first"]["spo2"] == r["last"]["spo2"]
                                    for r in u["region"].values()),
        "collapse_structural": out["collapse"]["max_holds"] and out["collapse"]["unset_is_lower_bound"]
        and out["collapse"]["no_family_rule"],
        "collapse_inactive": not out["collapse"]["active"] and not out["collapse"]["thresholds_selected"],
        "legacy_not_target": not out["legacy_comparison"]["used_for_parameters"],
        "boundaries_hold": out["boundary"]["pass"]}
    out["verdict"] = verdict(checks)
    out["recommendation"] = recommendation(out)
    out["decisions"] = list(DECISIONS)
    out["efficiency"] = {"integrator_steps": u["steps"] + HORIZON * (1 + len(RECOVERY_SHARES) + 1)
                         + 4 * FLUID["read_minute"] + 2 * 120, "fixed_state_readings": 6,
                         "legacy_minutes": max(LEGACY_MINUTES), "cartesian_sweep": False, "gi_trajectories": 2,
                         "gi_trajectory_purpose": "non-regression only", "records_read": ["P2M2_collapse_architecture.json"]}
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
    if args.design:
        print(json.dumps(design(), indent=2, sort_keys=True, default=str))
    if args.run:
        result = run()
        text = json.dumps(result, indent=2, sort_keys=True, default=str)
        if args.out:
            args.out.mkdir(parents=True, exist_ok=True)
            (args.out / "P2N2_acs_migration.json").write_text(text + "\n", encoding="utf-8")
        print(result["verdict"]["verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
