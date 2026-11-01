"""Phase 2 shadow core, P2L-1: the structural audit of consciousness / neurologic response.

    python -m clinical_core.consciousness_audit --digest
    python -m clinical_core.consciousness_audit --design
    python -m clinical_core.consciousness_audit --run --out <directory outside the repository>

Shadow only and offline (faculty brief of 2026-11-01, recorded in FACULTY). The first consciousness package: it separates
the primary neurologic state N from the observable level of consciousness, audits every current causal path into that
level, classifies each candidate systemic modifier (oxygen deficit, D, pH, PaCO2, glucose, oxygenation, MAP, N), probes
the double-counting and orthogonality questions on synthetic fixed states read through the certified core, audits
whether a recovery lag can be represented, reads the authored GI neurologic observations and the carried
extreme-acidemia subset from committed records, and returns a structural readiness verdict. It changes no core file,
writes no channel, adds no rule, threshold or parameter and calibrates nothing; collapse stays off.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import inspect
import json
from dataclasses import replace
from pathlib import Path

from . import acid_base as ab
from . import blood_fluid_calibration as bf
from . import derived as dv
from . import gi_reference
from . import lactate_rebuild as lr
from . import vascular_tone as vt
from . import ventilation_surface as vs
from .bands import ARRIVAL
from .derived import DEFAULT_PROFILE
from .state import Anchors, Channel, anchored_state

DECIDED = "2026-11-01"
REVISION = "P2L-1"
ROOT = vs.ROOT
CORE = ROOT / "clinical_core"
C57, C72 = "gi_bleed_57m", "gi_bleed_72f"
CASES = (C57, C72)
P2K5_RECORD = ROOT / "docs" / "revision" / "P2K5_respiratory_monotonicity.json"
P2K5_RECORD_SHA = "4c567527096d11253b6ebb054436b19a1797ae4f0aeee802fe5c7e824e7de523"
P2J3_RECORD = ROOT / "docs" / "revision" / "P2J3_pressure_tone_filter.json"
P2J3_RECORD_SHA = "bcecbe1651df99b9351f58162e99b312b01b23a109e785722d282faeae3151de"


# 1. The faculty decisions, recorded ----------------------------------------------------------------------------------------

FACULTY = {
    "decided": DECIDED,
    "closed": "P2K-5 accepted and closed: GI_RESPIRATORY_PHYSIOLOGY_CLOSED_FOR_CURRENT_PHASE and "
              "MOVE_FORWARD_TO_CONSCIOUSNESS; no respiratory cycle reopened, the respiratory uncertainty propagated",
    "goals": "separate the primary neurologic state N from the observable consciousness; audit every causal path into "
             "mental status; decide which systemic signals should reach it; find the double counting among oxygen "
             "deficit, pressure, oxygenation, pH and PaCO2; decide whether a recovery-lag state is structurally "
             "required; prepare a minimal common-physiology decision surface; no collapse calibration",
    "priority": "a coherent common physiology with explicit plausible uncertainty and no causal contradiction, good "
                "enough to migrate other families; not a tighter fit of two GI cases",
    "n_concept": "N is the PRIMARY NEUROLOGIC STATE / neurologic injury or reserve, never a container for every systemic "
                 "cause; observable consciousness is primary N plus relevant systemic modifiers; no shock, acidemia or "
                 "glucose written into N unless a persistent neurologic consequence is explicitly modeled",
    "lactate": "no direct lactate -> consciousness path; a direct use is BIOMARKER_PROXY_REQUIRES_REFACTOR",
    "probes": "MAP against deficit, SpO2 against delivery, pH against PaCO2, glucose, recovery lag, N1-N9, the "
              "extreme-acidemia subset, a qualitative generalization test and the upstream dependency, each on "
              "representative states; no Cartesian product",
    "no_numbers": "no numeric consciousness threshold invented to make a surface; numeric support only when the signals "
                  "are explicit, no new state is required and the ranges stand without the GI outcomes",
    "early_stop": "if common consciousness physiology needs a genuinely new state: STOP and report the smallest "
                  "required structure; no arbitrary threshold, GI offset, lactate proxy or legacy matching",
    "respiratory": "closed: ventilation gain 0.03 / 0.04, intrinsic RR, acid-to-RR gain, B, tau, HCO3 and PaCO2 "
                   "references not reopened; P2K-5 M-1 is DOCUMENTED_SEMANTIC_DEBT; HCO3_reference 24 "
                   "COMMON_REFERENCE_PROVISIONAL, g <= 1 / HCO3_reference the general rule for the linear mapping",
    "reuse": "BloodState, preload / pump, pressure / tone, DO2 / deficit, D, lactate, HR / baroreflex, acid-base and "
             "RR / W / PaCO2 closed for the current GI calibration; reopened only on a direct causal contradiction",
    "scope": "shadow only; no runtime integration, migration, consciousness parameter approval, collapse activation or "
             "legacy fitting",
}
STATUS = {"approved": "none FACULTY_APPROVED", "collapse": "OFF (not calibrated)",
          "consciousness": "AUDITED, not recalibrated: the core's derivation is unchanged"}
PATH_CLASSES = ("VALID_CAUSAL_PATH", "BIOMARKER_PROXY", "SEMANTIC_LEAK", "LEGACY_ARTIFACT", "NOT_CURRENTLY_MODELED",
                "BIOMARKER_PROXY_REQUIRES_REFACTOR")
N_CLASSES = ("PRIMARY_NEUROLOGIC_STATE", "MIXED_NEUROLOGIC_CONSTRUCT", "UNUSED_PLACEHOLDER")
OBSERVATION_CLASSES = ("AUTHORED_OBSERVATION", "MODEL_DERIVED", "LEGACY_REFERENCE")
GENERALIZATION_CLASSES = ("COMMON_NEUROLOGIC_ARCHITECTURE_PLAUSIBLE", "GI_SPECIFIC_OVERFIT_RISK", "STRUCTURAL_GAP")
LADDER = {0: "alert", 1: "drowsy", 2: "obtunded", 3: "unresponsive"}


# 2. N today (P2L-1-1): its definition, writers and readers, found in the code ------------------------------------------------

def _python(paths=None) -> list:
    own = {Path(__file__).name, "consciousness_audit_report.py"}
    return sorted(p for p in (paths or CORE.glob("*.py")) if p.name not in own and not p.name.endswith("_report.py"))


def n_references() -> dict:
    """Every place in clinical_core (this module and the reports aside) that writes or reads the N channel: a keyword
    N=... in a call, an attribute .N, or Channel.N; and every generic loop over the scalar channels."""
    writes, reads, channel = [], [], []
    for path in _python():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.keyword) and node.arg == "N":
                writes.append(f"{path.name}:{node.value.lineno}")
            elif isinstance(node, ast.Attribute) and node.attr == "N":
                where = f"{path.name}:{node.lineno}"
                if isinstance(node.value, ast.Name) and node.value.id == "Channel":
                    channel.append(where)
                else:
                    reads.append(where)
    generic = [f"{p.name}:{n}" for p in _python() for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1)
               if "for channel in SCALAR_CHANNELS" in line]
    return {"keyword_writes": writes, "attribute_reads": reads, "channel_constant": channel,
            "generic_scalar_loops": generic}


def n_audit() -> dict:
    refs = n_references()
    state = anchored_state(Anchors(**ARRIVAL))
    meaning = {"enum": "C9 CNS depression level, deviation from arrival (state.Channel.N)",
               "definition": "level deviation from arrival — CNS depression / neurological state "
                             "(state.CHANNEL_DEFINITIONS)",
               "guard": "integration.CHANNEL_BOUNDS: (-10, 10), PROVISIONAL, 'guard only; no module writes N yet'",
               "carried_note": "acid_base: no RR term; a future family may scale the drive (depressants)"}
    probe_level = {n: dv.derive(state.evolve(N=n), Anchors(**ARRIVAL), _profile()).consciousness_level
                   for n in (0.0, 5.0, -5.0)}
    return {"meaning": meaning, "arrival_value": state.N, "references": refs,
            "writers": [w for w in refs["keyword_writes"] if w.startswith("state.py")],
            "writers_rule": "only the arrival constructors (anchored_state, N=0.0); no contributor, integrator step or "
                            "case writes N",
            "readers": "none in derived or integration (no attribute read of N outside the generic scalar-channel loops "
                       "that check finiteness and apply the guard)",
            "serialization": "a scalar channel of CoreState: serialized with the state and in the Contracts-v2 shadow "
                             "payload's channels (contracts_output, always 0), its per-minute delta recorded and guarded "
                             "by integration (always 0), its bound named in the golden's channel_bounds",
            "cases": "no case declares or changes N (the legacy adapter builds the state with N = 0)",
            "observable_effect": probe_level,
            "classification": "UNUSED_PLACEHOLDER",
            "declared_semantics": "MIXED_NEUROLOGIC_CONSTRUCT: 'CNS depression / neurological state' joins drug-induced "
                                  "depression with primary neurologic injury; the faculty's concept (primary neurologic "
                                  "state / injury or reserve) is narrower"}


def _profile(**changes):
    """The GI haemodynamic profile the closed packages read (extraction reserve 2.5); nothing else changed."""
    return replace(DEFAULT_PROFILE, oxygen_extraction_reserve=2.5, **changes)


# 3. The observable consciousness today (P2L-1-2): its equation and every causal path -----------------------------------------

EQUATION = ("derived.derive: without a pulse the level is 3 (unresponsive; derived.check enforces it); with a pulse "
            "level = max(anchors.consciousness_level, L(SBP), L(SpO2)), L(SBP) = 1 below 80 and 2 below 65 mmHg "
            "(profile.pressure_levels), L(SpO2) = 1 below 87 and 2 below 80 % (profile.oxygen_levels), on the raw "
            "derived values; ladder 0 alert, 1 drowsy, 2 obtunded, 3 unresponsive")
EQUATION_SOURCE = ("level = max(anchors.consciousness_level, _level(sbp, profile.pressure_levels), "
                   "_level(spo2, profile.oxygen_levels))")
#: Each candidate input of the observable level: how the core reads it today, and its class.
PATHS = {
    "pulse": ("VALID_CAUSAL_PATH", "circulatory arrest -> unresponsive (level 3), an invariant of derive / check"),
    "sbp": ("LEGACY_ARTIFACT", "thresholds 80 / 65 adopted from family_engine._PRESSURE_LEVELS without its DC1 anchoring "
                               "or recovery margin; raw SBP, not MAP, stands in for both cerebral perfusion pressure and "
                               "systemic oxygen delivery"),
    "spo2": ("LEGACY_ARTIFACT", "thresholds 87 / 80 adopted from family_engine._OXYGEN_LEVELS; SpO2 also enters delivery "
                                "(delivery_rel = output x Hb ratio x SpO2 ratio), so a direct path double counts once "
                                "the deficit reaches consciousness"),
    "arrival_level": ("SEMANTIC_LEAK", "the authored arrival level is a permanent floor, cause-agnostic and never "
                                       "recovered: it holds whatever made the arrival impaired (a primary neurologic state "
                                       "and the arrival's systemic causes alike)"),
    "N": ("NOT_CURRENTLY_MODELED", "the channel exists (an unused placeholder); derive never reads it"),
    "effective_oxygen_deficit": ("NOT_CURRENTLY_MODELED", "computed by the core (DO2 against demand with extraction "
                                                          "reserve), read by D, the acid burden and the sympathetic drive, "
                                                          "never by consciousness"),
    "D": ("NOT_CURRENTLY_MODELED", "the accumulated oxygen-delivery debt: read by lactate and the sympathetic drive"),
    "map": ("NOT_CURRENTLY_MODELED", "derived ((SBP + 2 DBP) / 3) but not read; SBP is read instead"),
    "glucose": ("NOT_CURRENTLY_MODELED", "a state value (C11, absolute, from the case, no writer); read only by the "
                                         "sympathetic drive's hypoglycaemia term (threshold PROVISIONAL)"),
    "ph": ("NOT_CURRENTLY_MODELED", "the P2K-2 / P2K-3 respiration candidate's output, read by nothing downstream"),
    "paco2": ("NOT_CURRENTLY_MODELED", "the P2K-3 ventilation candidate's output (PaCO2_reference / W), read by nothing"),
    "lactate": ("NOT_CURRENTLY_MODELED", "correctly absent: no direct lactate -> consciousness path exists (no "
                                         "BIOMARKER_PROXY to refactor)"),
    "hr": ("NOT_CURRENTLY_MODELED", "correctly absent: the rate never reaches consciousness"),
}


def reading(state, anchors: Anchors, profile) -> dict:
    """What a fixed state shows: the observable level and every candidate signal, through the certified core."""
    d = dv.derive(state, anchors, profile)
    out = {"level": d.consciousness_level, "level_name": LADDER[d.consciousness_level], "pulse": d.pulse_present,
           "sbp": d.sbp, "map": d.map, "spo2": d.spo2, "lactate": d.lactate, "hr": d.pulse_rate_bpm,
           "glucose": state.glucose, "N": state.N, "D": state.D, "hb": state.hb,
           "demand": state.aux.oxygen_demand}
    if d.pulse_present:
        delivery = dv.effective_delivery(d.delivery_rel, anchors)
        deficit = dv.effective_oxygen_deficit(state.aux.oxygen_demand, delivery, profile.oxygen_extraction_reserve)
        out.update({"do2": delivery, "deficit": deficit, "deficit_fraction": deficit / state.aux.oxygen_demand})
    return out


def _acid(burden, efficiency: float = 1.0, gain: float = 0.04, **changes) -> dict:
    """An acid-base probe on P2K-2's neutral probe arrival (HCO3 20, A0 = 4) with a retained P2K-5 gain."""
    profile = replace(vs.PROBE_PROFILE, ventilation_efficiency=efficiency)
    state = vs._probe_state(burden, vs.PROBE_ANCHORS, profile, **changes)
    gas = vs._vr(state, vs.PROBE_ANCHORS, profile, gain)
    out = reading(state, vs.PROBE_ANCHORS, profile)
    out.update({"burden": gas["burden"], "hco3": gas["hco3"], "paco2": gas["paco2"], "ph": gas["ph"],
                "rr": gas["rr"], "w": gas["w"], "efficiency": efficiency})
    return out


def neutral() -> tuple:
    anchors = Anchors(**ARRIVAL)
    return anchors, anchored_state(anchors), _profile()


#: One perturbation per input, all else fixed at the neutral synthetic arrival (bands.ARRIVAL: SBP 120, SpO2 97, Hb 13,
#: glucose 100): does the observable level move? Structural, not a calibration: the sizes are illustrative extremes.
PERTURBATIONS = {
    "sbp": "tone T 0.45 (vasodilation, delivery kept)", "spo2": "authored arrival SpO2 82 % (delivery index 1)",
    "effective_oxygen_deficit": "Hb at 30 % of arrival (SBP kept)", "D": "D = 600 index-minutes, no deficit",
    "N": "N = 5", "glucose": "glucose 30 mg/dL", "ph": "metabolic acid burden 15 mEq/L (pH about 7.18)",
    "paco2": "ventilation efficiency 0.6 (PaCO2 about 58 mmHg)", "lactate": "lactate excess 8 mmol/L",
    "hr": "sympathetic drive 40", "demand": "oxygen demand 1.6 with delivery 1 (deficit 0 at reserve 2.5)",
    "arrival_level": "authored arrival level 2 with every signal normal"}


def perturbations() -> dict:
    anchors, base, profile = neutral()
    low_spo2 = Anchors(**{**ARRIVAL, "spo2": 82.0})
    floor = Anchors(**{**ARRIVAL, "consciousness_level": 2})
    states = {"arrival_level": (anchored_state(floor), floor, profile),
              "sbp": (base.evolve(T=0.45), anchors, profile),
              "spo2": (anchored_state(low_spo2), low_spo2, profile),
              "effective_oxygen_deficit": (base.evolve(hb=anchors.hb * 0.3), anchors, profile),
              "D": (base.evolve(D=600.0), anchors, profile), "N": (base.evolve(N=5.0), anchors, profile),
              "glucose": (base.evolve(glucose=30.0), anchors, profile),
              "lactate": (base.evolve(aux=replace(base.aux, lactate_excess_mmol_l=8.0)), anchors, profile),
              "hr": (base.evolve(aux=replace(base.aux, sympathetic_drive=40.0)), anchors, profile),
              "demand": (base.evolve(aux=replace(base.aux, oxygen_demand=1.6)), anchors, profile)}
    out = {name: reading(*args) for name, args in states.items()}
    out["ph"], out["paco2"] = _acid(15.0), _acid(None, 0.6)
    reference = {"neutral": reading(base, anchors, profile), "acid_neutral": _acid(None)}
    for name, row in out.items():
        ref = reference["acid_neutral" if name in ("ph", "paco2") else "neutral"]
        row["moves_level"] = row["level"] != ref["level"]
    return {"reference": reference, "rows": out, "what": PERTURBATIONS}


def path_table() -> dict:
    moved = perturbations()["rows"]
    rows = {}
    for name, (klass, why) in PATHS.items():
        row = {"class": klass, "why": why}
        if name in moved:
            row["moves_level"] = moved[name]["moves_level"]
        rows[name] = row
    rows["demand"] = {"class": "NOT_CURRENTLY_MODELED", "why": "demand reaches the deficit and the acid burden, not SBP "
                                                               "or SpO2", "moves_level": moved["demand"]["moves_level"]}
    return rows


def equation_audit() -> dict:
    source = inspect.getsource(dv.derive)
    return {"equation": EQUATION, "source_line_present": EQUATION_SOURCE in source,
            "pulseless_level": "consciousness_level=3" in source and "unresponsive" in inspect.getsource(dv.check),
            "pressure_levels": [list(x) for x in DEFAULT_PROFILE.pressure_levels],
            "oxygen_levels": [list(x) for x in DEFAULT_PROFILE.oxygen_levels],
            "provenance": {name: list(dv.PARAMETERS[name]) for name in ("pressure_levels", "oxygen_levels")},
            "ladder": LADDER, "anchors_field": "Anchors.consciousness_level (0-3, from the case's authored mental "
                                               "status through the legacy adapter's ladder)"}


# 4. The legacy reference (read as text, never fitted) ---------------------------------------------------------------------

LEGACY = {
    "thresholds": "family_engine._PRESSURE_LEVELS ((80, 1), (65, 2)) and _OXYGEN_LEVELS ((87, 1), (80, 2)) on systolic "
                  "pressure and saturation; ladder Alert / Drowsy / Obtunded / Unresponsive",
    "dc1": "family_engine._anchored_levels (DC1, faculty 2026-09-29): an arrival already past a threshold moves that "
           "threshold below it, so the written arrival reads as written",
    "margin": "family_engine._RECOVERY_MARGIN (SBP 2, SpO2 1, glucose 1): a level is left only past its threshold plus "
              "the margin (no flicker)",
    "recovery": "family_engine.MENTAL_RECOVERY (30 min of SpO2 >= 92, SBP >= 100 and CRT < 3.5 s, a counter that "
                "discounts a minute without them): one step up from the arrival state, never more",
    "families": "family branches: hypoglycaemia (glucose_rescue.CONSCIOUSNESS_BY_GLUCOSE, post-ictal), opioid "
                "(sedation from the drug), trauma, bradycardia, anaphylaxis and asthma rules; invasive airway "
                "pharmacology overrides",
    "class": "LEGACY_REFERENCE: a hidden recovery memory (the counter), threshold anchoring and family-specific rules; "
             "the core adopted only the two threshold ladders"}


# 5. The authored GI neurologic observations (P2L-1-8) ---------------------------------------------------------------------

#: The case bank's narrative lines (clinical_cases.py), quoted as the repository holds them.
PRESENTATION = {C57: ("clinical_cases.py:885", "A 57-year-old man presents after nearly fainting when standing. He looks "
                                               "pale and says he feels profoundly weak."),
                C72: ("clinical_cases.py:914", "A 72-year-old woman presents with worsening fatigue and lightheadedness. "
                                               "She had to stop walking from the waiting room because she felt faint.")}
NEURO_ITEMS = ("mental_status", "neurological_exam", "glucose_mg_dl", "spo2", "sbp", "dbp", "map", "abg",
               "lactate_mmol_l", "hb_g_dl")


def authored(case: str) -> dict:
    out = {"presentation": {"value": PRESENTATION[case][1], "source": PRESENTATION[case][0],
                            "class": "AUTHORED_OBSERVATION", "reading": "near-syncope / presyncope on standing"
                            if case == C57 else "lightheadedness and presyncope on walking"}}
    for item in NEURO_ITEMS:
        value, source = gi_reference.authored(case, item), gi_reference._source(case, item)
        klass = "MODEL_DERIVED" if item == "map" else "AUTHORED_OBSERVATION"
        note = "(SBP + 2 DBP) / 3 of the authored values" if item == "map" else ""
        if item == "mental_status":
            note = "the bank default 'Alert' (the case passes none), consistent with the authored examination"
        out[item] = {"value": value, "source": source, "class": klass, "note": note}
    anchors_level = 0 if gi_reference.authored(case, "mental_status") == "Alert" else None
    out["core_arrival_level"] = {"value": anchors_level, "class": "MODEL_DERIVED",
                                 "note": "Anchors.consciousness_level through the legacy adapter's ladder"}
    out["legacy_arrival"] = {"value": gi_reference.authored(case, "mental_status"), "class": "LEGACY_REFERENCE",
                             "note": "family_engine reads the same authored arrival"}
    out["absent"] = {"gcs": "not authored", "orientation_detail": "only in the examination text",
                     "focal_deficits": "none stated (72f: 'moving all limbs symmetrically'; 57m: not stated)",
                     "later_neurologic_anchors": "none authored; none invented"}
    return out


# 6. Double counting and orthogonality (P2L-1-3 to -6) ----------------------------------------------------------------------

def deficit_map_probes() -> dict:
    """A very low MAP with no deficit; an adequate MAP with a high deficit (anaemia; and a vasoconstricted low output);
    both; neither."""
    anchors, base, profile = neutral()
    rows = {"A_low_map_no_deficit": reading(base.evolve(T=0.45), anchors, profile),
            "B_adequate_map_high_deficit_anaemia": reading(base.evolve(hb=anchors.hb * 0.3), anchors, profile),
            "B2_vasoconstricted_low_output": reading(base.evolve(P=0.4, T=1.8), anchors, profile),
            "C_low_map_and_high_deficit": reading(base.evolve(P=0.3), anchors, profile),
            "D_neither": reading(base, anchors, profile)}
    a, b = rows["A_low_map_no_deficit"], rows["B_adequate_map_high_deficit_anaemia"]
    return {"rows": rows,
            "signals_distinguish_a_from_b": a["deficit"] == 0.0 < b["deficit"] and a["map"] < b["map"],
            "current_level_reads": "pressure only: A impaired, B alert",
            "current_a_impaired": a["level"] > 0, "current_b_alert": b["level"] == 0,
            "overlap": "output lowers both MAP (pressure = output x tone) and delivery; tone and Hb separate them, so a "
                       "MAP term and a deficit term are not the same signal, but they coincide in low-output shock (C): "
                       "an additive rule would count that shock twice, a max rule would not"}


def oxygenation_probes() -> dict:
    """Low SpO2 with adequate delivery; normal SpO2 with a critical deficit; both."""
    anchors, base, profile = neutral()
    low = Anchors(**{**ARRIVAL, "spo2": 82.0})
    rows = {"A_low_spo2_adequate_delivery": reading(anchored_state(low), low, profile),
            "B_normal_spo2_critical_deficit": reading(base.evolve(hb=anchors.hb * 0.25), anchors, profile),
            "C_both": reading(anchored_state(low).evolve(hb=low.hb * 0.3), low, profile)}
    return {"rows": rows,
            "spo2_in_delivery": "delivery_rel = output x (Hb / Hb0) x (SpO2 / SpO2_0), arrival-relative; the arrival's "
                                "own hypoxaemia reaches DO2 only through the case's arrival_delivery_ratio",
            "direct_path_double_counts": True,
            "current_a_impaired_b_alert": rows["A_low_spo2_adequate_delivery"]["level"] > 0
            and rows["B_normal_spo2_critical_deficit"]["level"] == 0,
            "reading": "a direct SpO2 path adds no physiology once the deficit reaches consciousness: oxygenation acts on "
                       "the brain through oxygen content, which DO2 already carries; it double counts a hypoxaemia that "
                       "lowers DO2 and impairs a hypoxaemia that DO2 says is compensated"}


def acid_base_probes() -> dict:
    """Low pH with a normal PaCO2 is not reachable (compensation is always on); a metabolic acidemia, an acute
    hypercapnia, both, neither."""
    rows = {"A_metabolic_acidemia": _acid(15.0), "B_hypercapnia": _acid(None, 0.6), "C_both": _acid(15.0, 0.6),
            "D_neither": _acid(None)}
    a, b = rows["A_metabolic_acidemia"], rows["B_hypercapnia"]
    # Near-normal pH with PaCO2 >= 50 needs HCO3 above the reference (metabolic compensation): with HCO3 = 24 - A and
    # A >= 0, pH <= 6.1 + log10(24 / (0.03 x 50)).
    ceiling = dv.carbonic_ph(vs.HCO3_REFERENCE, 50.0)
    return {"rows": rows, "distinguishes": abs(a["ph"] - b["ph"]) < 0.05 and b["paco2"] - a["paco2"] > 20.0,
            "compensated_hypercapnia_ph_ceiling": ceiling,
            "compensated_hypercapnia_representable": ceiling >= 7.35,
            "reading": "metabolic acidemia (burden up, PaCO2 down) and acute hypercapnia (W down, PaCO2 up) reach the "
                       "same pH by different signals, so the architecture can keep them apart; a near-normal pH with a "
                       "high PaCO2 (chronic, compensated hypercapnia) is not representable: no metabolic compensation "
                       "raises HCO3 above the reference; neither reaches consciousness today"}


def glucose_probe() -> dict:
    anchors, base, profile = neutral()
    rows = {"normal": reading(base, anchors, profile), "severe_hypoglycaemia": reading(base.evolve(glucose=30.0),
                                                                                     anchors, profile)}
    return {"rows": rows, "state": "CoreState.glucose (C11, absolute, from the case), guarded 15-350 (ADOPTED)",
            "writers": "none in the core: no contributor, no dextrose, no consumption",
            "reader": "the sympathetic drive's hypoglycaemia term (threshold PROVISIONAL, TBD)",
            "level_unchanged": rows["normal"]["level"] == rows["severe_hypoglycaemia"]["level"],
            "reading": "an independent path is representable (the state exists and is orthogonal to shock), but the "
                       "observable does not read it, and nothing in the core moves glucose"}


# 7. Recovery lag (P2L-1-7) and the neurologic probes N1-N9 (P2L-1-10) -------------------------------------------------------

MEMORIES = {
    "D": "accumulated oxygen-delivery debt: accrues only while the effective deficit is positive, repays first-order "
         "(debt_clearance_tau_min 60, PROVISIONAL, set for lactate and the sympathetic drive); systemic, read by lactate "
         "and the sympathetic drive",
    "aux.collapse_burden": "the collapse rule's burden (P2E-3): accrues below an output threshold; off by default",
    "aux.metabolic_acid_burden": "the acid burden: produced by the deficit, cleared with tau_acid; read by RR, W, pH",
    "aux.lactate_excess_mmol_l": "a biomarker: never a neurologic controller (faculty)",
    "aux.sympathetic_drive": "the drive: decays with its own tau; read by the heart rate",
    "N": "the unused placeholder: no writer, no reader, no dynamics"}


def recovery_lag() -> dict:
    anchors, base, profile = neutral()
    insult, restored = base.evolve(P=0.3), base.evolve(D=600.0)
    no_deficit = {"low_map": reading(base.evolve(T=0.45), anchors, profile),
                  "hypoglycaemia": reading(base.evolve(glucose=30.0), anchors, profile),
                  "hypercapnia": _acid(None, 0.6)}
    return {"instantaneous": "derive reads only the current state and the anchors: the observable has no memory",
            "insult_level": reading(insult, anchors, profile)["level"],
            "restored_level": reading(restored, anchors, profile)["level"],
            "memories": MEMORIES,
            "d_accrues_without_deficit": {k: v["deficit"] > 0.0 for k, v in no_deficit.items()},
            "d_sufficient": False,
            "why_not_d": "D is systemic oxygen debt with lactate / sympathetic time constants: it does not accrue for a "
                         "MAP-only, hypoglycaemic or hypercapnic insult (no deficit), so it cannot carry their delayed "
                         "recovery, and using it as neurologic memory would tie brain recovery to debt repayment",
            "new_state_required": True,
            "verdict": "NEUROLOGIC_RECOVERY_STATE_REQUIRED"}


#: (name, what is isolated, the expected distinction (qualitative, the faculty's concept), the signal that carries it)
NEURO_PROBES = (
    ("N1", "normal systemic physiology and normal N", "alert", "none"),
    ("N2", "isolated primary neurologic injury (N = 5)", "impaired by N alone", "N"),
    ("N3", "isolated severe oxygen deficit (Hb 25 %, SBP and SpO2 kept)", "impaired by cerebral oxygen under-delivery",
     "effective_oxygen_deficit"),
    ("N4", "isolated very low MAP with adequate delivery (tone 0.45)", "vulnerable from cerebral perfusion failure",
     "map"),
    ("N5", "isolated severe metabolic acidemia (burden 15, pH about 7.18)", "impaired when severe", "ph"),
    ("N6", "isolated acute hypercapnia (efficiency 0.6, PaCO2 about 58)", "impaired (hypercapnic encephalopathy)",
     "paco2"),
    ("N7", "isolated hypoglycaemia (glucose 30)", "impaired, independently of shock", "glucose"),
    ("N8", "combined low-output shock and acidemia (pump 0.3, burden 15)", "impaired, both mechanisms, not counted twice",
     "map, effective_oxygen_deficit, ph"),
    ("N9", "physiology restored after a prolonged prior insult (D 600, no deficit)", "recovery delayed after the "
     "physiology normalizes", "a memory"))


def neuro_probes() -> dict:
    anchors, base, profile = neutral()
    states = {"N1": reading(base, anchors, profile), "N2": reading(base.evolve(N=5.0), anchors, profile),
              "N3": reading(base.evolve(hb=anchors.hb * 0.25), anchors, profile),
              "N4": reading(base.evolve(T=0.45), anchors, profile), "N5": _acid(15.0), "N6": _acid(None, 0.6),
              "N7": reading(base.evolve(glucose=30.0), anchors, profile), "N8": _acid(15.0, P=0.3),
              "N9": reading(base.evolve(D=600.0), anchors, profile)}
    expected_impaired = {"N1": False, "N2": True, "N3": True, "N4": True, "N5": True, "N6": True, "N7": True, "N8": True,
                         "N9": True}
    signal_exists = {"N1": True, "N2": True, "N3": True, "N4": True, "N5": True, "N6": True, "N7": True, "N8": True,
                     "N9": False}
    rows = {}
    for name, isolated, expected, carrier in NEURO_PROBES:
        row = states[name]
        represented = (row["level"] > 0) == expected_impaired[name]
        rows[name] = {"isolated": isolated, "expected": expected, "carrier": carrier, "level": row["level"],
                      "level_name": row["level_name"], "current_derivation_represents": represented,
                      "signal_exists_in_core": signal_exists[name],
                      "gap": "none" if represented else ("a memory state (none exists)" if not signal_exists[name]
                                                         else "the observable does not read the signal"),
                      "reading": {k: row.get(k) for k in ("sbp", "map", "spo2", "do2", "deficit_fraction", "ph",
                                                          "paco2", "glucose", "N", "D")}}
    return {"rows": rows, "represented": sorted(k for k, v in rows.items() if v["current_derivation_represents"]),
            "signal_missing": sorted(k for k, v in rows.items() if not v["signal_exists_in_core"])}


# 8. The carried extreme-acidemia subset (P2L-1-9), read from the committed records ---------------------------------------------

def _record(path: Path, sha: str) -> dict:
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != sha:
        raise AssertionError(f"{path.name} is not the committed record")
    return json.loads(data.decode("utf-8"))


def extreme_acidemia() -> dict:
    """P2K-5's 57m / demand 1.1 subset with untreated pH < 7.00, and the untreated SBP of the same trajectories from
    P2J-3's record (respiratory latents never reach SBP; P2K-5's units are P2J-3 survivors at the same tone and
    demand), read through today's consciousness rule at minute 120, where the lowest pH lies."""
    p2k5, p2j3 = _record(P2K5_RECORD, P2K5_RECORD_SHA), _record(P2J3_RECORD, P2J3_RECORD_SHA)
    x = p2k5["demands"]["1.1"]["observed"]["extreme_acidemia"]
    pressure = {}
    for key, item in sorted(p2j3["support"].items()):
        if key.endswith("x1.1"):
            u = item[C57]
            pressure[key] = {"sbp120": u["untreated"]["sbp120"], "map120": u["untreated"]["map120"],
                             "minutes_below_80": u["below"]["P1"]["80.0"], "minutes_below_65": u["below"]["P1"]["65.0"]}
    worst_sbp = max(p["sbp120"]["high"] for p in pressure.values())
    level_120 = max(level for threshold, level in DEFAULT_PROFILE.pressure_levels if worst_sbp < threshold)
    return {"flagged": x["flagged"], "survivors": x["survivors"], "by_case": x["by_case"], "lowest": x["lowest"],
            "classification": x["lowest"]["flag"], "untreated_pressure_57m_d1.1": pressure,
            "highest_untreated_sbp120": worst_sbp, "current_level_at_120": level_120,
            "current_level_name": LADDER[level_120],
            "reading": "every trajectory of the subset already reads obtunded at minute 120 today, through the SBP "
                       "proxy alone (SBP 120 below 65 at every tone gain); pH 6.96 with a deficit of 0.84 and MAP about "
                       "35 make full alertness implausible under any plausible consciousness physiology, so the "
                       "direction agrees but for a proxy reason; the rows are kept and carried, never filtered",
            "fully_alert_plausible": False, "filtered": False}


# 9. Which upstream uncertainty reaches consciousness (P2L-1-13) --------------------------------------------------------------

UPSTREAM = {
    "demand": ("no", "yes (deficit, acid burden)", "demand moves the deficit and the burden, not SBP or SpO2"),
    "tone_gain": ("yes (SBP)", "yes (deficit through output)", "pressure = output x tone; P2J-3's untreated SBP differs "
                                                                "by tone gain"),
    "map_set": ("no", "no", "P2J-4: the baroreflex acts on the heart rate only; the rate never feeds output or pressure"),
    "baroreflex_gain": ("no", "no", "the same path as MAP_set"),
    "hr_latent_region": ("no", "no", "the heart rate reaches no output, pressure or delivery in the core"),
    "respiratory_latents": ("no", "yes (pH, PaCO2)", "B, tau and the ventilation gain move the burden, pH and PaCO2; "
                                                     "RR is no consciousness input"),
}


def upstream() -> dict:
    moved = perturbations()["rows"]
    return {"table": {k: {"current": v[0], "candidate": v[1], "why": v[2]} for k, v in UPSTREAM.items()},
            "evidence": {"hr_moves_level": moved["hr"]["moves_level"], "demand_moves_level": moved["demand"]["moves_level"],
                         "sbp_moves_level": moved["sbp"]["moves_level"]},
            "design": "representative and boundary states only; no dimension without a causal path is multiplied"}


# 10. Generalization, qualitatively (P2L-1-12) ----------------------------------------------------------------------------------

GENERALIZATION = {
    "hemorrhagic_shock": ("deficit and MAP exist", "the observable reads SBP only", "recovery lag missing"),
    "hypoglycaemia": ("glucose state exists, orthogonal to shock", "not read; no glucose writer or dextrose in the core",
                      "post-hypoglycaemic recovery lag missing"),
    "hypercapnia_opioid": ("acute hypercapnia representable (efficiency, demand); N could carry a drug's primary CNS "
                           "depression", "PaCO2 not read; compensated chronic hypercapnia not representable",
                           "recovery lag missing"),
    "primary_neurologic_injury": ("N exists", "no N writer and no N reader", "N's own dynamics undefined"),
    "severe_hypoxaemia": ("oxygenation reaches DO2", "SpO2 moves only with FiO2 (gas exchange G has no writer); the "
                          "direct SpO2 path double counts", "recovery lag missing"),
    "distributive_shock": ("low tone gives a low MAP with preserved delivery: the MAP path is distinct from the deficit",
                           "the observable reads SBP, not MAP", "recovery lag missing"),
}


def generalization() -> dict:
    return {"families": {k: {"present": v[0], "missing": v[1], "lag": v[2]} for k, v in GENERALIZATION.items()},
            "result": "STRUCTURAL_GAP",
            "reading": "no GI-specific term is needed, and every systemic signal a family needs exists or is a family's "
                       "own writer; the common gap is one neurologic recovery state, which no family can supply"}


# 11. Readiness, the smallest missing structure, the decisions requested (P2L-1-11, -15) ---------------------------------------

READY = "CONSCIOUSNESS_STRUCTURE_READY_FOR_NUMERIC_FACULTY_CALIBRATION"
NOT_READY = "CONSCIOUSNESS_STRUCTURE_NOT_READY"
BLOCKER = "NEUROLOGIC_RECOVERY_STATE_REQUIRED"
CRITERIA = ("n_semantics_explicit", "observable_separated_from_n", "causal_modifiers_explicit", "lactate_not_proxy",
            "double_counting_resolved", "recovery_lag_coherent", "generalization_plausible", "upstream_unchanged",
            "nothing_approved")
VERDICT_RULE = (
    "Frozen before the run. READY when every criterion holds. Otherwise NOT_READY: with the early-stop blocker "
    "NEUROLOGIC_RECOVERY_STATE_REQUIRED when a recovery lag needs a state the core cannot represent (the faculty's "
    "early stop: report the smallest structure, never invent it), else the first failing criterion. No numeric surface "
    "is prepared while NOT_READY.")
SMALLEST_STRUCTURE = {
    "state": "one auxiliary scalar F >= 0, a NEUROLOGIC_FUNCTIONAL_IMPAIRMENT (reversible encephalopathy depth), "
             "distinct from N (the primary, persistent neurologic state: injury or reserve) and from D (systemic "
             "oxygen debt)",
    "dynamics": "first order toward an instantaneous target F*, faster while F* rises than while it falls (two time "
                "constants, for a later faculty calibration)",
    "target": "F* from the causal systemic modifiers combined by maximum, not by sum, so a shock that lowers both MAP and "
              "delivery is not counted twice: cerebral perfusion failure (MAP), cerebral oxygen under-delivery (the "
              "effective deficit), hypoglycaemia (glucose), acidemia (pH) and hypercapnia (PaCO2) as separate inputs; "
              "no direct SpO2 term (oxygenation acts through delivery) and no lactate term",
    "observable": "level = the ladder of max(primary N, F); without a pulse 3, as now",
    "arrival": "the authored arrival level is read as the arrival value of F (or of N when the case authors a primary "
               "neurologic state), not as a permanent floor",
    "not_added_here": "no state, parameter, threshold or rule is added in P2L-1",
}
DECISIONS = (
    "accept, amend or reject the recovery state F, separate from N and from D (or keep the lag in the observation "
    "layer, as the legacy counter did)",
    "the aggregation rule of the systemic modifiers: maximum (no double counting) or additive",
    "which modifiers enter: MAP as cerebral perfusion (where, relative to autoregulation), the effective deficit, "
    "glucose, pH and PaCO2 separately; confirm no direct SpO2 and no lactate path",
    "N's semantics: primary injury / reserve only, or also a drug's primary CNS depression (opioids), or a separate "
    "pharmacologic channel",
    "the authored arrival level: arrival value of F / N instead of a floor (DC1's role in the core)",
    "the carried extreme-acidemia subset once the rules exist (kept, never filtered, today)",
    "compensated chronic hypercapnia: a respiratory-family question (metabolic compensation is not modeled)")
DECISION_SURFACE = {
    "structural_only": True,
    "options": {"memory": ["new state F", "observation-layer lag"], "aggregation": ["maximum", "additive"],
                "map": ["enters as cerebral perfusion", "does not enter"], "spo2": ["through delivery only"],
                "lactate": ["never"], "n": ["primary injury / reserve", "plus drug CNS depression", "separate channel"],
                "arrival": ["arrival value of F / N", "floor (today)"]},
    "numeric": "none: P2L-1-11 forbids a numeric surface while a new state is required"}
NEXT_RULE = ("Predeclared. READY: a small observable-consciousness decision pack, no hard filter. NOT_READY: report the "
             "smallest missing structure and the faculty decisions; nothing implemented, nothing filtered.")
POLICY = ("Shadow only and read-only: no core file, channel, rule, threshold or parameter changed or added; synthetic "
          "fixed states and committed records read through the certified core; the legacy read as text, never "
          "fitted; the extreme-acidemia rows kept; nothing selected or approved; collapse off.")
MIGRATION_GATE = ("MIGRATION_GATE_CLOSED: no runtime integration, GI or second-family migration, consciousness "
                  "parameter approval or collapse activation is authorized")


def verdict(checks: dict) -> dict:
    failing = [name for name in CRITERIA if checks.get(name) is False]
    unevaluated = [name for name in CRITERIA if name not in checks]
    if not failing and not unevaluated:
        result = READY
    elif checks.get("recovery_lag_coherent") is False:
        result = f"{NOT_READY} - {BLOCKER}"
    elif failing:
        result = f"{NOT_READY} - {failing[0].upper()}"
    else:
        result = f"{NOT_READY} - NOT_EVALUATED"
    return {"verdict": result, "checks": checks, "failing": failing, "not_evaluated": unevaluated}


def recommendation(result: dict) -> dict:
    if result["verdict"] == READY:
        return {"recommendation": "PREPARE_OBSERVABLE_CONSCIOUSNESS_DECISION_PACK", "rule": NEXT_RULE}
    return {"recommendation": "STOP_FOR_FACULTY_STRUCTURAL_DECISION", "blocker": result["verdict"],
            "smallest_structure": SMALLEST_STRUCTURE, "decisions": list(DECISIONS), "rule": NEXT_RULE}


# 12. Closure: the closed files at P2K-5 (2063748) ---------------------------------------------------------------------------

CLOSED_AT_P2K5 = {
    "clinical_core/derived.py": "b9056ada72f4c651974eccd1069a67097d31814a5d691cbfc883e33d85bb77a6",
    "clinical_core/integration.py": "dad171baff07805997272310f4f33545ed38956b531585ae246c0e26e8c07b7a",
    "clinical_core/state.py": "578d32abad60fcda31a4d3344532b709c8c8f8b71ea2f4bdb2f88c37265a6d13",
    "clinical_core/acid_base.py": "9298b1f0a6defbe1a11627a0d76208c36792b01a390d80558e3cc1fda1827954",
    "clinical_core/ventilation.py": "260393add18e2275ee21411512d18531a74387f853bb76a2f33f89d5cb1bafe9",
    "clinical_core/ventilation_surface.py": "d361b500ccaf059784ea7e7662b6be5dd7d02019174c2f66cc0ca0ff24245825",
    "clinical_core/ventilation_filter.py": "9edf6c7544924f90875bdc2abd56cf6d86346411901009e641267d14d47685b9",
    "clinical_core/respiratory_monotonicity.py": "ba6bac3ea1f4f1f9b0bff5503b4ff846f1ae5a097ee88d8480dd3ee52fbba672"}
OWN = ("clinical_core/consciousness_audit.py",)
REPORT = "clinical_core/consciousness_audit_report.py"
#: The two tuple-only files at P2K-5 (2063748): P2L-1 adds its modules to their tuples, nothing else.
TUPLE_AT_P2K5 = {"clinical_core/lactate_slice.py": "af1d59f5e00b326dbb6018598bcdfc735da516dcfaaec87592330fb78fd9dce9",
                 "clinical_core/decision_pack.py": "26105802528f516e69b221251da56f7f2e2a4837ab5d96ff6eac92381e22adc8"}
TUPLES_ADDED = {"DOWNSTREAM_REPORTS": (REPORT,), "PACK_DIGEST_EXCLUDED": (OWN[0], REPORT)}


def closed_unchanged() -> dict:
    return {relative: hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == sha
            for relative, sha in CLOSED_AT_P2K5.items()}


def p2k5_sources(sources: dict) -> dict:
    """A P2K-5 dependency map: P2L-1's module removed, the two tuple-only files at their P2K-5 hashes while only their
    tuples changed (the tuple content itself is pinned by the tests)."""
    out = {k: v for k, v in sources.items() if k not in OWN}
    for relative, sha in TUPLE_AT_P2K5.items():
        item = vt.TUPLE_CHANGES[relative]
        if relative in out and vt.outside_digest(vt._live(relative), item["changed"]) == item["outside_p2j1"]:
            out[relative] = sha
    return out


# 13. Design, freeze, run -------------------------------------------------------------------------------------------------------

def design() -> dict:
    return {"revision": REVISION, "decided": DECIDED, "faculty": FACULTY, "status": STATUS,
            "path_classes": list(PATH_CLASSES), "n_classes": list(N_CLASSES),
            "observation_classes": list(OBSERVATION_CLASSES), "generalization_classes": list(GENERALIZATION_CLASSES),
            "ladder": LADDER, "equation": EQUATION, "equation_source": EQUATION_SOURCE,
            "paths": {k: list(v) for k, v in PATHS.items()}, "perturbations": PERTURBATIONS, "legacy": LEGACY,
            "presentation": {k: list(v) for k, v in PRESENTATION.items()}, "neuro_items": list(NEURO_ITEMS),
            "memories": MEMORIES, "neuro_probes": [list(p) for p in NEURO_PROBES], "upstream": UPSTREAM,
            "generalization": GENERALIZATION, "criteria": list(CRITERIA), "verdict_rule": VERDICT_RULE,
            "smallest_structure": SMALLEST_STRUCTURE, "decisions": list(DECISIONS),
            "decision_surface": DECISION_SURFACE, "next_rule": NEXT_RULE, "policy": POLICY,
            "migration_gate": MIGRATION_GATE, "closed_at_p2k5": CLOSED_AT_P2K5, "own": list(OWN), "report": REPORT,
            "tuple_at_p2k5": TUPLE_AT_P2K5, "tuples_added": {k: list(v) for k, v in TUPLES_ADDED.items()},
            "records": {"p2k5": P2K5_RECORD_SHA, "p2j3": P2J3_RECORD_SHA}}


def freeze_digest() -> str:
    text = json.dumps({"revision": REVISION, "p2k5": hashlib.sha256(P2K5_RECORD.read_bytes()).hexdigest(),
                       "p2j3": hashlib.sha256(P2J3_RECORD.read_bytes()).hexdigest(), "design": design(),
                       "sources": bf.freeze_sources()}, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run() -> dict:
    with lr.P2FGuard(), lr.LegacyLock():
        out = {"freeze_digest": freeze_digest(), "decided": DECIDED, "revision": REVISION, "policy": POLICY,
               "design": design(), "closed_unchanged": closed_unchanged(), "approval": STATUS["approved"],
               "migration_gate": MIGRATION_GATE}
        checks = {"nothing_approved": True, "upstream_unchanged": all(out["closed_unchanged"].values())}
        if not checks["upstream_unchanged"]:
            out["stopped"] = "a closed file changed: STOP"
            out["verdict"] = verdict(checks)
            out["recommendation"] = recommendation(out["verdict"])
            return out
        out.update({"n": n_audit(), "equation": equation_audit(), "paths": path_table(),
                    "perturbations": perturbations(), "authored": {case: authored(case) for case in CASES},
                    "deficit_map": deficit_map_probes(), "oxygenation": oxygenation_probes(),
                    "acid_base": acid_base_probes(), "glucose": glucose_probe(), "recovery_lag": recovery_lag(),
                    "neuro_probes": neuro_probes(), "extreme_acidemia": extreme_acidemia(), "upstream": upstream(),
                    "generalization": generalization()})
        paths = out["paths"]
        invalid = ("LEGACY_ARTIFACT", "SEMANTIC_LEAK", "BIOMARKER_PROXY", "BIOMARKER_PROXY_REQUIRES_REFACTOR")
        checks["n_semantics_explicit"] = out["n"]["classification"] in N_CLASSES
        checks["causal_modifiers_explicit"] = not any(row["class"] in invalid for row in paths.values())
        # Separated: the observable reads N as one input beside explicit systemic modifiers (today it reads neither).
        checks["observable_separated_from_n"] = bool(paths["N"]["moves_level"]) and checks["causal_modifiers_explicit"]
        checks["lactate_not_proxy"] = paths["lactate"]["class"] not in invalid and not paths["lactate"]["moves_level"]
        checks["double_counting_resolved"] = not out["oxygenation"]["direct_path_double_counts"]
        checks["recovery_lag_coherent"] = not out["recovery_lag"]["new_state_required"]
        checks["generalization_plausible"] = out["generalization"]["result"] == GENERALIZATION_CLASSES[0]
        out["efficiency"] = {"fixed_state_readings": sum(len(out[k]["rows"]) for k in (
                                 "perturbations", "deficit_map", "oxygenation", "acid_base", "glucose", "neuro_probes")),
                             "records_read": ["P2K5_respiratory_monotonicity.json", "P2J3_pressure_tone_filter.json"],
                             "simulations": 0, "region_rebuilt": False, "cartesian_sweep": False, "legacy_read": False}
        out["verdict"] = verdict(checks)
        out["recommendation"] = recommendation(out["verdict"])
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
        print(json.dumps(design(), indent=1, sort_keys=True, default=str))
    if args.run:
        if args.out is None:
            parser.error("--run needs --out")
        args.out.mkdir(parents=True, exist_ok=True)
        result = run()
        (args.out / "consciousness_audit.json").write_text(json.dumps(result, indent=1, sort_keys=True, default=str)
                                                           + "\n", encoding="utf-8")
        print(result["verdict"]["verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
