"""Phase 2 shadow core, P2K-4: the faculty's RR / ventilation observable-envelope filter for the current GI cases.

    python -m clinical_core.ventilation_filter --digest
    python -m clinical_core.ventilation_filter --design
    python -m clinical_core.ventilation_filter --run --out <directory outside the repository>

Shadow only and offline (faculty brief of 2026-10-31, recorded in FACULTY). P2K-3 built the respiratory decision surface;
the faculty answered with observable envelopes A-I. This module freezes the envelopes, the demand semantics, the matched
treatment comparators and their minutes, the R3 / R4 reading, the unchanged latent support and the filter order, then
filters the candidate space: each P2J-3 upstream survivor at its tone gain and demand, crossed with each latent
respiratory combination (drive gain, intrinsic RR per patient, ventilation gain, B, tau).

The trajectories are P2K-3's factorized ones: the certified deficit, the core's burden algebra per (B, tau), RR per (drive
gain, intrinsic RR), W / PaCO2 / pH per ventilation gain. Each rule is a table over the factors it reads, assembled per
upstream survivor as a bitset over the latent combinations, so every rule is evaluated for every candidate without a
Cartesian simulation. The upstream is reused, never changed; nothing is selected or approved; untreated pH never filters.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import replace
from pathlib import Path

from . import acid_base as ab
from . import baroreflex as br
from . import blood_anchors
from . import blood_fluid_calibration as bf
from . import calibration
from . import derived as dv
from . import gi_reference
from . import hr_envelope_filter as hf
from . import lactate_rebuild as lr
from . import pressure_tone as pt
from . import pressure_tone_filter as pf
from . import vascular_tone as vt
from . import ventilation as vn
from . import ventilation_surface as vs
from .derived import DEFAULT_PROFILE

DECIDED = "2026-10-31"
REVISION = "P2K-4"
ROOT = vs.ROOT
CASES = vs.CASES
C57, C72 = vs.C57, vs.C72
DEMANDS = vs.DEMANDS
LAMBDAS = vs.LAMBDAS
AFTERLOAD = vs.AFTERLOAD
TONE_GAINS = ab.TONE_GAINS
RESERVE = ab.RESERVE
MINUTE = 120
P2K3_RECORD = ROOT / "docs" / "revision" / "P2K3_ventilation_surface.json"
P2K3_DIGEST = "23f1673fe24fe6a49a9fed13e60088eb05f5f15c8cf5eec2700618bca2a897e3"

# The latent respiratory support (P2K-3's, unchanged; 0.08 excluded by the faculty) ------------------------------------

DRIVE_GAINS = vs.DRIVE_GAINS
INTRINSIC_RR = vs.INTRINSIC_RR
VENTILATION_GAINS = tuple(g for g in vs.VENTILATION_GAINS if g != 0.08)
STEADY_BURDENS = vs.STEADY_BURDENS
ACID_TAUS = vs.ACID_TAUS
#: Bitset order of a latent combination (the last dimension fastest).
DIMS = ("drive_gain", "intrinsic_57m", "intrinsic_72f", "ventilation_gain", "B", "tau")
VALUES = {"drive_gain": DRIVE_GAINS, "intrinsic_57m": INTRINSIC_RR, "intrinsic_72f": INTRINSIC_RR,
          "ventilation_gain": VENTILATION_GAINS, "B": STEADY_BURDENS, "tau": ACID_TAUS}
SIZES = tuple(len(VALUES[d]) for d in DIMS)
N_LATENT = math.prod(SIZES)
STRIDES = tuple(math.prod(SIZES[k + 1:]) for k in range(len(DIMS)))
FULL = (1 << N_LATENT) - 1
INTRINSIC_DIM = {C57: "intrinsic_57m", C72: "intrinsic_72f"}


def latent_index(digits: tuple) -> int:
    """The bit of a latent combination given its value indices in DIMS order."""
    return sum(d * s for d, s in zip(digits, STRIDES))


def latent_digits(index: int) -> tuple:
    return tuple((index // s) % n for s, n in zip(STRIDES, SIZES))


def latent_values(index: int) -> dict:
    return {d: VALUES[d][k] for d, k in zip(DIMS, latent_digits(index))}


def _dimension_masks() -> dict:
    out = {d: [0] * n for d, n in zip(DIMS, SIZES)}
    for index in range(N_LATENT):
        for d, k in zip(DIMS, latent_digits(index)):
            out[d][k] |= 1 << index
    return out


DIM_MASKS = _dimension_masks()
_MASKS: dict = {}


def mask(dims: tuple, digits: tuple) -> int:
    """Every latent combination with ``dims`` at the value indices ``digits`` (cached)."""
    key = (dims, digits)
    if key not in _MASKS:
        bits = FULL
        for d, k in zip(dims, digits):
            bits &= DIM_MASKS[d][k]
        _MASKS[key] = bits
    return _MASKS[key]


def bits_of(dims: tuple, passing) -> int:
    """The bitset of a rule over ``dims`` from the value-index tuples that pass it."""
    out = 0
    for digits in passing:
        out |= mask(dims, digits)
    return out


def combos(dims: tuple) -> list:
    """Every value-index tuple over ``dims`` (DIMS order kept within the tuple)."""
    out = [()]
    for d in dims:
        out = [c + (k,) for c in out for k in range(len(VALUES[d]))]
    return out


# 1. The faculty decisions (2026-10-31), frozen -------------------------------------------------------------------------

FACULTY = {
    "decided": DECIDED,
    "closed": "P2K-3 accepted and closed; RR_VENTILATION_DECISION_SURFACE_READY accepted",
    "goal": "bound the current respiratory candidate region with interpretable RR / PaCO2 / pH observables, keep the acid "
            "burden, drive, RR, W and PaCO2 separate, keep the latent uncertainty (no single set), and say whether the GI "
            "respiratory domain is bounded enough to move on",
    "priority": "a coherent common physiology with explicit plausible uncertainty and no causal contradiction, good "
                "enough to migrate other families; not a tighter fit of two GI cases; a non-empty region is acceptable",
    "demand": "BASELINE_RELATIVE: W is effective ventilation relative to the patient's baseline / current ventilatory "
              "requirement; demand 1.1 is not an absolute hypermetabolism with a new resting PaCO2; a modeling semantic "
              "decision, not an approval of demand 1.0 or 1.1",
    "support": "P2K-3's primary support unchanged: intrinsic RR 12 / 16 / 20 per patient, the frozen drive gains, "
               "ventilation gain 0.03-0.06 (0.08 excluded: it failed the arrival PaCO2 windows), B 13.4 / 19.4 / 28, "
               "tau 60 / 120 / 240; no value FACULTY_APPROVED",
    "references": "HCO3 24, PaCO2 40 (COMMON_REFERENCE_PROVISIONAL); arrival RR 57m 26 +/- 3, 72f 24 +/- 3; arrival "
                  "PaCO2 57m 31 +/- 3, 72f 33 +/- 3; arrival pH diagnostic only (same HCO3 and PaCO2)",
    "untreated_ph": "no untreated pH filter; its distribution reported; pH < 7.00 flagged UNTREATED_EXTREME_ACIDEMIA "
                    "(diagnostic, CONSCIOUSNESS_COLLAPSE_REVIEW)",
    "crystalloid": "E: P2J-3's matched comparator, R2 against R1 at P2J-3's minutes; only "
                   "RESPIRATORY_AND_PERFUSION_WORSEN rejects; never judged from RR alone",
    "prbc": "F: the red cells against matched trajectories omitting only the target exposure: R3 against R3 without "
            "the red cells; in R4 unit 1 and unit 2 each against L3 without it; never R3 against R4",
    "r3_r4": "similar R3 / R4 respiratory outputs at 120 are not a contradiction when neither has an effective deficit; "
             "the bleeding state, BloodState and chronology must differ where they should, else STOP",
    "early_stop": "an empty region or a causal contradiction STOPs; no widened envelope or tolerance, no new support "
                  "value, no gain 0.08, no B / tau change, no legacy fitting, no hypoxaemic drive, no tidal-volume or "
                  "fatigue state",
    "exit": "a coherent non-empty region, no contradiction, intact upstream, structurally coherent RR / W / PaCO2 / pH "
            "and plausible counterfactuals bound the current GI respiratory domain: default MOVE_FORWARD; broad B, "
            "tau, intrinsic RR or gains never call for another respiratory package",
    "scope": "shadow only; no runtime integration, migration, parameter approval, consciousness, collapse or legacy "
             "fitting; the upstream physiology reused, never reopened",
}
CARRIED = {"tone_gain": "PRIMARY 0.25 / 0.5 / 1.0 (P2J-3), causal through output, delivery and the deficit",
           "demand": "1.0 and 1.1 filtered separately; robustness across them diagnostic only",
           "not_multiplied": "MAP_set, the baroreflex gain, the HR latent region (no path to deficit, burden, RR or W)"}
DEMAND_NORMALIZATION = {
    "semantics": "BASELINE_RELATIVE (P2K-3): demand ratio = aux.oxygen_demand / the patient's baseline demand; the GI "
                 "runs carry no demand modifier, so the ratio is 1 and the class reaches W only through the deficit and "
                 "the burden",
    "status": "MODELING_SEMANTIC_DECISION; demand 1.0 and 1.1 not approved",
    "not_used": "an absolute demand index (it would make the 1.1 class hypercapnic at rest)"}
STATUS = {"latent": "EXPLORATORY (intrinsic RR, drive gain, ventilation gain, B, tau)",
          "envelopes": "FACULTY_CALIBRATION_ENVELOPE: case and scenario specific, not universal ranges",
          "excluded_gain_0.08": "EXCLUDED_BY_FACULTY_SUPPORT (not a rejection count)",
          "approved": "none FACULTY_APPROVED"}

# 2. The envelopes A-I, frozen ----------------------------------------------------------------------------------------------

ARRIVAL_RR = {C57: (26.0 - 3.0, 26.0 + 3.0), C72: (24.0 - 3.0, 24.0 + 3.0)}
ARRIVAL_PACO2 = {C57: (31.0 - 3.0, 31.0 + 3.0), C72: (33.0 - 3.0, 33.0 + 3.0)}
ENVELOPES = {
    "A": {"scenario": "P1", "case": C57, "rr": (24.0, 38.0), "text": "R1 57m untreated, RR at 120 in 24-38"},
    "B": {"scenario": "P1", "case": C72, "rr": (20.0, 36.0),
          "text": "R1 72f untreated, RR at 120 in 20-36; not required to be at or above the arrival RR"},
    "C": {"scenario": "P1", "case": C57, "paco2": (18.0, 35.0), "text": "R1 57m untreated, PaCO2 at 120 in 18-35"},
    "D": {"scenario": "P1", "case": C72, "paco2": (22.0, 38.0), "text": "R1 72f untreated, PaCO2 at 120 in 22-38"},
    "E": {"scenario": "P2", "text": "R2 against matched R1: no RESPIRATORY_AND_PERFUSION_WORSEN at the frozen minutes"},
    "F": {"scenario": "P3 / P4", "text": "red cells against matched no-PRBC trajectories: no "
                                          "PRBC_CAUSES_RESPIRATORY_AND_PERFUSION_WORSENING at the frozen minutes"},
    "G": {"scenario": "P4", "case": C57, "rr": (12.0, 27.0), "text": "R4 57m definitive, RR at 120 in 12-27"},
    "G2": {"scenario": "P4", "case": C72, "rr": (12.0, 24.0), "text": "R4 72f definitive, RR at 120 in 12-24"},
    "H": {"scenario": "P4", "case": None, "paco2": (30.0, 42.0), "ph": (7.35, 7.45),
          "text": "R4 both cases, PaCO2 at 120 in 30-42 and pH at 120 in 7.35-7.45"},
    "I": {"scenario": "P4", "residual": {C57: (0.0, 12.0), C72: (0.0, 10.0)},
          "text": "R4 at 120, RR - intrinsic RR in 0-12 (57m) and 0-10 (72f)"},
}
BOUNDS_RULE = ("Inclusive bounds, the faculty's numbers exactly, no tolerance; all at minute 120. An observable that "
               "does not exist (no pulse: RR 0, no PaCO2 or pH) fails the envelope that reads it.")
EXTREME_ACIDEMIA = 7.00
EXTREME_RULE = ("UNTREATED_EXTREME_ACIDEMIA: R1 pH below 7.00 at any minute 0-120 in either case; diagnostic, never a "
                "rejection; handed to CONSCIOUSNESS_COLLAPSE_REVIEW")


def inside(value, bounds) -> bool:
    return value is not None and bounds[0] <= value <= bounds[1]


# 3. Scenarios and matched comparators, frozen ------------------------------------------------------------------------------

#: The kinds of trajectory a candidate reads: P1-P4 (R1-R4), L3 without unit 1 / unit 2 (P2J-3's CF1 / CF2), and R3
#: without the red cells (NP).
NO_PRBC = "NP"
KINDS = ("P1", "P2", "P3", "P4", "CF1", "CF2", NO_PRBC)
CLINICAL = ("P1", "P2", "P3", "P4")
#: (treated, comparator, the target exposure the comparator omits, the comparison minutes).
COMPARATORS = {
    "E": (("P2", "P1", "Crystalloid", "crystalloid volume complete (P2J-3), and 120"),),
    "F": (("P3", NO_PRBC, "PackedRedCells", "unit 1 complete, unit 2 complete, and 120"),
          ("P4", "CF1", "PackedRedCells unit 1", "unit 1 complete (P2J-3), and 120"),
          ("P4", "CF2", "PackedRedCells unit 2", "unit 2 complete (P2J-3), and 120")),
}
COMPARATOR_RULE = (
    "Each comparator omits only the target exposure and keeps the blood set, the lactate-side point, the tone gain, the "
    "demand, the latent respiratory combination, the elapsed time, the bleeding chronology, the PPI and haemostasis "
    "timing. E is P2J-3's comparator (L2 against L1, the same blood set). F: R3 against R3's inputs without the red "
    "cells; in R4 each unit against L3 without it (P2J-3's CF1 / CF2). R3 is never compared with R4 as a red-cell "
    "counterfactual: that pair changes the haemostasis.")


def blood_keys(survivor: tuple, case: str) -> dict:
    """The blood trajectory of each kind a P2J-3 survivor (i, a, b, q, d) reads for one case."""
    i, _, _, q, d = survivor
    return {"P1": ("P1", case, i), "P2": ("P2", case, (i, d)), "P3": ("P3", case, q), "P4": ("P4", case, q),
            "CF1": ("CF1", case, q), "CF2": ("CF2", case, q), NO_PRBC: (NO_PRBC, case, q)}


def no_prbc_items(case: str, full: dict) -> tuple:
    """R3's inputs (L3 without the endoscopic haemostasis) without the red cells: the matched no-PRBC trajectory."""
    return tuple(item for item in pt.scenario_items(case, pt.NO_HAEMOSTASIS, full)
                 if type(item).__name__ != "PackedRedCells")


def scenario_inputs(kind: str, case: str, full: dict) -> tuple:
    if kind in CLINICAL:
        return pt.scenario_items(case, vt.SCENARIOS[kind], full)
    if kind in ("CF1", "CF2"):
        return hf.counterfactual_items(case, full, 1 if kind == "CF1" else 2)
    if kind == NO_PRBC:
        return no_prbc_items(case, full)
    raise ValueError(kind)


def _blood_dict(states: list, stop, anchors, profile, full: dict) -> dict:
    """The cached blood trajectory, field for field as pressure_tone_filter._cf_blood_task keeps it."""
    unit = full.get("red_cell_unit_volume_ml")
    shed = [state.blood.shed_ml for state in states]
    flow = [after - before for before, after in zip(shed, shed[1:])]
    views = [vt.derive(state, anchors, profile) for state in states]
    if {state.aux.oxygen_demand for state in states} != {anchors.metabolic_demand_baseline}:
        raise AssertionError("a GI blood run carries a demand modifier: the reconstruction does not cover it")
    return {"output1": [v.output_rel for v in views], "hb": [s.hb for s in states], "spo2": [v.spo2 for v in views],
            "pulse": [v.pulse_present for v in views], "bleed": (flow[:1] or [0.0]) + flow,
            "crystalloid": [s.blood.crystalloid_in_ml for s in states],
            "prbc": [s.blood.transfused_ml / unit for s in states], "controlled_at": lr.controlled_at(states[-1]),
            "stop": stop, "demand": [s.aux.oxygen_demand for s in states]}


def _np_blood_task(task: tuple) -> tuple:
    """R3 without the red cells for one P3 set, as P2J-3 builds CF1 / CF2 (the same entry, setup and minutes)."""
    key, entry, case = task
    values = lr.blood_values(entry, case, None)
    anchors, profile, full = blood_anchors.setup(case, **values)
    states, stop = blood_anchors.trajectory(anchors, no_prbc_items(case, full), pf.MINUTES, profile)
    return key, _blood_dict(states, stop, anchors, profile, full)


def np_tasks(region: dict) -> list:
    keys = sorted({k for k in region["bloods"] if k[0] == "P3"}, key=str)
    return [((NO_PRBC, case, q), region["source"]["p3"][q], case) for _, case, q in keys]


def comparison_minutes(treated: str, comparator: str, blood: dict) -> tuple:
    """The frozen minutes from the treated trajectory's own blood record (P2J-3's rule where it exists)."""
    if (treated, comparator) == ("P2", "P1"):
        return pf.comparison_minutes("C", blood)
    if (treated, comparator) == ("P4", "CF1"):
        return pf.comparison_minutes("D", blood)
    if (treated, comparator) == ("P4", "CF2"):
        return pf.comparison_minutes("E", blood)
    if (treated, comparator) == ("P3", NO_PRBC):
        return pf.completion(blood["prbc"], 1.0), pf.completion(blood["prbc"], 2.0), MINUTE
    raise ValueError((treated, comparator))


def _entry(kind: str, k, source: dict, support: list) -> tuple:
    """The P2J-3 entry and crystalloid bag of one blood key."""
    if kind == "P1":
        return source["p1"][k], None
    if kind == "P2":
        return source["p1"][k[0]], support[k[1]]["bag"]
    return source["p3"][k], None


def comparator_inputs(region: dict, treated: str, comparator: str, case: str, k_treated, k_comparator) -> dict:
    """Structural equivalence of one matched pair: the same entry, and inputs equal once the target exposure is set
    aside (the target item removed for E and R3; for CF1 / CF2 every item but the red cells equal, the red cells one unit
    fewer)."""
    e1, bag1 = _entry(treated, k_treated, region["source"], region["support"])
    e2, bag2 = _entry(comparator, k_comparator, region["source"], region["support"])
    _, _, full1 = blood_anchors.setup(case, **lr.blood_values(e1, case, bag1))
    _, _, full2 = blood_anchors.setup(case, **lr.blood_values(e2, case, bag2))
    a, b = scenario_inputs(treated, case, full1), scenario_inputs(comparator, case, full2)
    name = lambda item: type(item).__name__
    target = "Crystalloid" if treated == "P2" else "PackedRedCells"
    rest_a, rest_b = [i for i in a if name(i) != target], [i for i in b if name(i) != target]
    units = lambda items: sum(i.units for i in items if name(i) == "PackedRedCells")
    out = {"same_entry": e1 is e2 or e1 == e2, "others_equal": rest_a == rest_b,
           "target_in_treated": any(name(i) == target for i in a)}
    if comparator in (NO_PRBC, "P1"):
        out["target_absent_in_comparator"] = not any(name(i) == target for i in b)
    else:
        out["one_unit_fewer"] = units(a) - units(b) == 1.0
    out["matched"] = all(out.values())
    return out


# 4. The counterfactual reading of E and F, frozen ---------------------------------------------------------------------------

WORSEN = "RESPIRATORY_AND_PERFUSION_WORSEN"
TREATED_ARREST = "TREATED_ARREST_WITH_COMPARATOR_BREATHING"
CLASSES = ("RESPIRATORY_AND_PERFUSION_IMPROVE", "RESPIRATORY_SIGNAL_NONIMPROVING_WITH_PERFUSION_IMPROVEMENT",
           "RESPIRATORY_IMPROVING_WITH_PERFUSION_WORSENING", "RESPIRATORY_UNCHANGED_WITH_PERFUSION_WORSENING",
           WORSEN, "NO_PERFUSION_CHANGE", "COMPARATOR_ARREST_WITH_TREATED_BREATHING", TREATED_ARREST,
           "NO_COMPARISON_BOTH_ARRESTED", "NO_COMPARISON_IMPOSSIBLE_VALUE")
REJECTING = (WORSEN, TREATED_ARREST)
F_REJECTION_NAME = "PRBC_CAUSES_RESPIRATORY_AND_PERFUSION_WORSENING"
SIGNAL_RULE = (
    "At each comparison minute, delta = treated - matched comparator, the same latent combination. Perfusion improves "
    "when the effective deficit is lower, worsens when higher. The respiratory signal reads the acid burden and the "
    "compensation state together: it improves when the burden is lower and pH higher, worsens when the burden is higher "
    "and pH lower (a physiologically worse compensation), and is otherwise not improving. RR and PaCO2 are reported and "
    "checked to follow the burden at fixed latent parameters (RR never lower, PaCO2 never higher when the burden is "
    "higher); RR alone never classifies. A delta within 1e-9 of its scale is no change (P2J-3's rule). Only "
    "RESPIRATORY_AND_PERFUSION_WORSEN rejects (for the red cells named PRBC_CAUSES_RESPIRATORY_AND_PERFUSION_WORSENING: "
    "worse deficit + worse burden + lower pH), and a treated arrest while the comparator still breathes; a comparator "
    "arrest with the treated breathing is the treated doing better.")


def _sign(delta: float, scale: float) -> int:
    return pf._sign(delta, scale)


def perfusion_signal(d_deficit: float, deficit_scale: float) -> int:
    return -_sign(d_deficit, deficit_scale)


def respiratory_signal(d_burden: float, d_ph: float, burden_scale: float, ph_scale: float) -> int:
    lower, higher_ph = -_sign(d_burden, burden_scale), _sign(d_ph, ph_scale)
    if lower > 0 and higher_ph > 0:
        return 1
    if lower < 0 and higher_ph < 0:
        return -1
    return 0


def classify(perfusion: int, respiratory: int) -> str:
    if perfusion > 0:
        return CLASSES[0] if respiratory > 0 else CLASSES[1]
    if perfusion < 0:
        return CLASSES[2] if respiratory > 0 else WORSEN if respiratory < 0 else CLASSES[3]
    return CLASSES[5]


def acid_series(deficit: list, case: str, b: float, tau: float) -> tuple:
    """The burden (the core's algebra, P2K-3's burden_series) and HCO3 of one deficit trajectory at one (B, tau)."""
    burden = ab.burden_series(deficit, ab.arrival_burden(case), b, tau)[:len(deficit)]
    return burden, vs.hco3_series(burden, case)


def bundle(rows: list, pulse: list, case: str, b: float, tau: float) -> dict:
    """One rebuilt trajectory at one (B, tau): deficit, pulse, burden, HCO3 and W / PaCO2 / pH per ventilation gain."""
    n = len(rows)
    deficit, pulse = [row["deficit"] for row in rows], list(pulse[:n])
    burden, hco3 = acid_series(deficit, case, b, tau)
    gas = {gain: vs.gas_series(burden, hco3, pulse, gain) for gain in VENTILATION_GAINS}
    return {"n": n, "deficit": deficit, "pulse": pulse, "burden": burden, "hco3": hco3, "gas": gas}


def reading(t: dict, c: dict, minute: int, gain: float) -> dict:
    """One comparison minute of a matched pair at one ventilation gain."""
    alive_t = minute < t["n"] and t["pulse"][minute]
    alive_c = minute < c["n"] and c["pulse"][minute]
    out = {"minute": minute, "alive": [alive_t, alive_c]}
    if not alive_t or not alive_c:
        out["class"] = (TREATED_ARREST if alive_c else "NO_COMPARISON_BOTH_ARRESTED") if not alive_t \
            else "COMPARATOR_ARREST_WITH_TREATED_BREATHING"
        return out
    ph_t, ph_c = t["gas"][gain][2][minute], c["gas"][gain][2][minute]
    paco2_t, paco2_c = t["gas"][gain][1][minute], c["gas"][gain][1][minute]
    if None in (ph_t, ph_c, paco2_t, paco2_c):
        out["class"] = CLASSES[-1]   # HCO3 <= 0: SIMULATION rejects the (B, tau); the reading only records it
        return out
    deltas = {"burden": t["burden"][minute] - c["burden"][minute], "ph": ph_t - ph_c, "paco2": paco2_t - paco2_c,
              "deficit": t["deficit"][minute] - c["deficit"][minute]}
    perfusion = perfusion_signal(deltas["deficit"], c["deficit"][minute])
    respiratory = respiratory_signal(deltas["burden"], deltas["ph"], c["burden"][minute], ph_c)
    out.update(deltas)
    out.update({"class": classify(perfusion, respiratory), "perfusion": perfusion, "respiratory": respiratory,
                "burden_t": t["burden"][minute], "burden_c": c["burden"][minute]})
    return out


def rr_follows_burden(burden_t: float, burden_c: float) -> bool:
    """At fixed latent parameters RR is non-decreasing in the burden: over every drive gain and intrinsic RR of the
    support, delta RR is zero or has the burden's sign (the respiratory signal never needs RR)."""
    sign_b = _sign(burden_t - burden_c, burden_c)
    for gain in DRIVE_GAINS:
        for intrinsic in INTRINSIC_RR:
            d = vs.rr_series([burden_t], [True], gain, intrinsic)[0] - vs.rr_series([burden_c], [True], gain, intrinsic)[0]
            if _sign(d, intrinsic) not in (0, sign_b):
                return False
    return True


# 5. Rules as bitsets, order and rejection classes, frozen ---------------------------------------------------------------

ORDER = ("SIMULATION", "ARRIVAL_RR", "ARRIVAL_PACO2", "A", "B", "G", "G2", "H_PACO2", "H_PH", "I", "C", "D", "E", "F")
REJECTION_CLASS = {"SIMULATION": "SIMULATION_REJECTION", "ARRIVAL_RR": "ARRIVAL_RR_REJECTION",
                   "ARRIVAL_PACO2": "ARRIVAL_PACO2_REJECTION", "A": "RR_ENVELOPE_REJECTION",
                   "B": "RR_ENVELOPE_REJECTION", "G": "RR_ENVELOPE_REJECTION", "G2": "RR_ENVELOPE_REJECTION",
                   "I": "RR_ENVELOPE_REJECTION", "H_PACO2": "PACO2_ENVELOPE_REJECTION",
                   "C": "PACO2_ENVELOPE_REJECTION", "D": "PACO2_ENVELOPE_REJECTION", "H_PH": "PH_ENVELOPE_REJECTION",
                   "E": "TREATMENT_DIRECTION_REJECTION", "F": "TREATMENT_DIRECTION_REJECTION"}
REJECTION_CLASSES = ("SIMULATION_REJECTION", "ARRIVAL_RR_REJECTION", "ARRIVAL_PACO2_REJECTION", "RR_ENVELOPE_REJECTION",
                     "PACO2_ENVELOPE_REJECTION", "PH_ENVELOPE_REJECTION", "TREATMENT_DIRECTION_REJECTION")
ORDER_RULE = (
    "Frozen before any count: the faculty's order (arrival RR, arrival PaCO2, A, B, G / G2, H, I, C, D, E, F), H split "
    "into its PaCO2 and pH parts, behind one structural guard (SIMULATION: a trajectory the candidate reads lacks minute "
    "120, has HCO3 <= 0, W <= 0 while breathing, or stops / clamps where its blood run does not). Every rule is evaluated "
    "for every candidate as a bitset, so the order changes no cost and is kept as given; the first failure in ORDER is "
    "the counted one, and every failure, every sole failure and every pair of failures is reported too.")
RR_DIMS = {case: ("drive_gain", INTRINSIC_DIM[case], "B", "tau") for case in CASES}
GAS_DIMS = ("ventilation_gain", "B", "tau")
ACID_DIMS = ("B", "tau")
ARRIVAL_RR_DIMS = ("drive_gain", "intrinsic_57m", "intrinsic_72f")


def arrival_rr_bits() -> int:
    passing = [(g, i, j) for g, gain in enumerate(DRIVE_GAINS) for i, i57 in enumerate(INTRINSIC_RR)
               for j, i72 in enumerate(INTRINSIC_RR)
               if inside(ab.arrival_rr(gain, i57, C57), ARRIVAL_RR[C57])
               and inside(ab.arrival_rr(gain, i72, C72), ARRIVAL_RR[C72])]
    return bits_of(ARRIVAL_RR_DIMS, passing)


def arrival_paco2_bits() -> int:
    passing = [(v,) for v, gain in enumerate(VENTILATION_GAINS)
               if all(inside(vs.predicted_paco2(gain, case), ARRIVAL_PACO2[case]) for case in CASES)]
    return bits_of(("ventilation_gain",), passing)


def arrival_ph_diagnostic() -> dict:
    """The arrival pH per ventilation gain: derived from the authored HCO3 and the predicted PaCO2; never a filter."""
    return {f"{gain:g}": {case: {"ph": vs.predicted_ph(gain, case),
                                 "class": vs.ph_class(vs.predicted_ph(gain, case) - ab.authored_gas(case)["ph"])}
                          for case in CASES} for gain in VENTILATION_GAINS}


def summarize(bundles: dict, structural: bool) -> dict:
    """What the rules and diagnostics read of one trajectory, per (B, tau) value indices: the burden and pulse at 120,
    PaCO2 / pH at 120 per ventilation gain, the pH range and lowest pH over 0-120, and the SIMULATION flag."""
    out = {}
    for key, t in bundles.items():
        sim = structural or t["n"] <= MINUTE or min(t["hco3"]) <= 0.0
        gas = {}
        for v, gain in enumerate(VENTILATION_GAINS):
            w, paco2, ph = t["gas"][gain]
            breathing = [m for m in range(min(t["n"], MINUTE + 1)) if t["pulse"][m]]
            if any(not (w[m] > 0.0 and math.isfinite(w[m])) for m in breathing):
                sim = True
            known = [(ph[m], m) for m in breathing if ph[m] is not None]
            low = min(known) if known else (None, None)
            gas[v] = {"paco2_120": paco2[MINUTE] if t["n"] > MINUTE else None,
                      "ph_120": ph[MINUTE] if t["n"] > MINUTE else None,
                      "ph_low": low[0], "ph_high": max(known)[0] if known else None, "ph_low_minute": low[1],
                      "at_low": None if low[1] is None else {"burden": t["burden"][low[1]],
                                                            "deficit": t["deficit"][low[1]],
                                                            "paco2": paco2[low[1]]}}
        out[key] = {"sim": sim, "b120": t["burden"][MINUTE] if t["n"] > MINUTE else None,
                    "p120": t["n"] > MINUTE and t["pulse"][MINUTE], "gas": gas}
    return out


def rr_at_120(summary: dict, key: tuple, gain: float, intrinsic: float) -> float:
    s = summary[key]
    if s["b120"] is None:
        return 0.0
    return vs.rr_series([s["b120"]], [s["p120"]], gain, intrinsic)[0]


def rr_bits(summary: dict, case: str, bounds: tuple, residual: bool = False) -> int:
    passing = []
    for g, gain in enumerate(DRIVE_GAINS):
        for i, intrinsic in enumerate(INTRINSIC_RR):
            for key in summary:
                rr = rr_at_120(summary, key, gain, intrinsic)
                if inside(rr - intrinsic if residual else rr, bounds):
                    passing.append((g, i) + key)
    return bits_of(RR_DIMS[case], passing)


def gas_bits(summary: dict, quantity: str, bounds: tuple) -> int:
    return bits_of(GAS_DIMS, [(v,) + key for key, s in summary.items() for v in s["gas"]
                              if inside(s["gas"][v][quantity], bounds)])


def sim_bits(summary: dict) -> int:
    return bits_of(ACID_DIMS, [key for key, s in summary.items() if not s["sim"]])


def pair_bits(readings: dict) -> int:
    """readings: (v, b, t) value indices -> the readings at the comparison minutes; passes when none rejects."""
    return bits_of(GAS_DIMS, [key for key, rs in readings.items() if not any(r["class"] in REJECTING for r in rs)])


class Tally:
    """Per demand: entering candidates, first / any / sole failures, pairs of failures, classes, survivors."""

    def __init__(self):
        self.entering, self.survivors, self.units, self.units_with_survivors = 0, 0, 0, 0
        self.first = {name: 0 for name in ORDER}
        self.any = {name: 0 for name in ORDER}
        self.only = {name: 0 for name in ORDER}
        self.pairs = {f"{a}+{b}": 0 for k, a in enumerate(ORDER) for b in ORDER[k + 1:]}
        self.class_first = {c: 0 for c in REJECTION_CLASSES}
        self.class_any = {c: 0 for c in REJECTION_CLASSES}
        self.by_tone = {}
        self.latent = 0

    def add(self, rules: dict, tone: float) -> int:
        bits = [rules[name] for name in ORDER]
        fails = [FULL & ~b for b in bits]
        prefix, suffix = [FULL], [FULL]
        for b in bits:
            prefix.append(prefix[-1] & b)
        for b in reversed(bits):
            suffix.append(suffix[-1] & b)
        suffix = suffix[::-1]
        survivors = prefix[-1]
        for k, name in enumerate(ORDER):
            self.first[name] += (prefix[k] & fails[k]).bit_count()
            self.any[name] += fails[k].bit_count()
            self.only[name] += (fails[k] & prefix[k] & suffix[k + 1]).bit_count()
            for j in range(k + 1, len(ORDER)):
                self.pairs[f"{name}+{ORDER[j]}"] += (fails[k] & fails[j]).bit_count()
        for c in REJECTION_CLASSES:
            members = [k for k, name in enumerate(ORDER) if REJECTION_CLASS[name] == c]
            self.class_first[c] += sum((prefix[k] & fails[k]).bit_count() for k in members)
            union = 0
            for k in members:
                union |= fails[k]
            self.class_any[c] += union.bit_count()
        n = survivors.bit_count()
        self.entering += N_LATENT
        self.survivors += n
        self.units += 1
        self.units_with_survivors += n > 0
        row = self.by_tone.setdefault(f"{tone:g}", {"entering": 0, "survivors": 0, "units": 0})
        row["entering"] += N_LATENT
        row["survivors"] += n
        row["units"] += 1
        self.latent |= survivors
        return survivors

    def public(self) -> dict:
        return {"entering": self.entering, "survivors": self.survivors, "first_failure": self.first,
                "any_failure": self.any, "only_failure": self.only, "overlap": self.pairs,
                "rejection_classes_first": self.class_first, "rejection_classes_any": self.class_any,
                "by_tone_gain": self.by_tone, "upstream_units": self.units,
                "upstream_units_with_survivors": self.units_with_survivors,
                "latent_survivors": self.latent.bit_count()}


# 6. R3 / R4: respiratory convergence against the underlying state, frozen ---------------------------------------------------

R3R4_CLASSES = ("PHYSIOLOGICAL_RESPIRATORY_CONVERGENCE", "RESPIRATORY_OUTPUTS_DISTINCT", "SCENARIO_STATE_COLLAPSE_BUG")
#: Near-identity of the respiratory outputs at 120 (over the surviving latent combinations of the pair).
R3R4_NEAR = {"rr": 0.1, "paco2": 0.1, "ph": 0.001, "w": 0.005, "burden": 0.01}
R3R4_RULE = (
    "For every surviving (tone gain, demand, case, red-cell set, lactate-side level), R3 (L3 without haemostasis) and R4 "
    "(L3) are compared at 120. Underlying: the haemostasis minute, the active bleed rate and the cumulative blood loss, "
    "the circulating volume and red-cell content of the core's BloodState, Hb, output and delivery, the effective "
    "deficit; the red-cell and crystalloid chronology must be the same. Respiratory: burden, RR, W, PaCO2 and pH over the "
    "pair's surviving latent combinations. SCENARIO_STATE_COLLAPSE_BUG (a STOP) when the bleeding state or the "
    "BloodState does not differ or the chronology differs beyond the haemostasis; otherwise "
    "PHYSIOLOGICAL_RESPIRATORY_CONVERGENCE when the respiratory outputs are within R3R4_NEAR, else "
    "RESPIRATORY_OUTPUTS_DISTINCT. Respiratory identity is never required to differ by treatment identity.")


def _state_task(task: tuple) -> tuple:
    """The core's BloodState and bleed of one red-cell set's R3 or R4 run at 120 (blood-side anchors, as P2J-3)."""
    key, entry, case = task
    kind = key[0]
    values = lr.blood_values(entry, case, None)
    anchors, profile, full = blood_anchors.setup(case, **values)
    states, stop = blood_anchors.trajectory(anchors, scenario_inputs(kind, case, full), pf.MINUTES, profile)
    if len(states) <= MINUTE:
        return key, {"complete": False, "stop": stop}
    blood = states[MINUTE].blood
    return key, {"complete": True, "stop": stop, "blood": blood.to_dict(), "volume_ml": blood.volume_ml,
                 "red_cells": blood.red_cells, "hb": states[MINUTE].hb, "shed_ml": blood.shed_ml,
                 "bleed_rate": blood.shed_ml - states[MINUTE - 1].blood.shed_ml,
                 "controlled_at": lr.controlled_at(states[-1])}


def state_tasks(region: dict, qs: dict) -> list:
    """qs: case -> the red-cell sets the survivors read."""
    return [((kind, case, q), region["source"]["p3"][q], case) for case in CASES for q in sorted(qs.get(case, ()))
            for kind in ("P3", "P4")]


def underlying(s3: dict, s4: dict, b3: dict, b4: dict, r3: list, r4: list) -> dict:
    """The underlying comparison of one R3 / R4 pair: core states at 120, the cached blood records and the rebuilt rows."""
    diff = lambda x, y: abs(x - y) > 1e-9 * max(1.0, abs(y))
    out = {"complete": s3["complete"] and s4["complete"] and len(r3) > MINUTE and len(r4) > MINUTE}
    if not out["complete"]:
        out["distinct"] = False
        return out
    out.update({
        "haemostasis": [s3["controlled_at"], s4["controlled_at"]],
        "bleed_rate_120": [s3["bleed_rate"], s4["bleed_rate"]], "shed_ml_120": [s3["shed_ml"], s4["shed_ml"]],
        "volume_ml_120": [s3["volume_ml"], s4["volume_ml"]], "red_cells_120": [s3["red_cells"], s4["red_cells"]],
        "hb_120": [s3["hb"], s4["hb"]], "output_120": [r3[MINUTE]["output"], r4[MINUTE]["output"]],
        "delivery_120": [r3[MINUTE]["delivery_rel"], r4[MINUTE]["delivery_rel"]],
        "deficit_120": [r3[MINUTE]["deficit"], r4[MINUTE]["deficit"]],
        "deficit_max_abs_difference": max(abs(x["deficit"] - y["deficit"]) for x, y in zip(r3, r4)),
        "chronology_same": b3["prbc"] == b4["prbc"] and b3["crystalloid"] == b4["crystalloid"]})
    out["bleeding_differs"] = s3["controlled_at"] != s4["controlled_at"] and (
        diff(s3["bleed_rate"], s4["bleed_rate"]) or diff(s3["shed_ml"], s4["shed_ml"]))
    out["blood_state_differs"] = diff(s3["volume_ml"], s4["volume_ml"]) or diff(s3["red_cells"], s4["red_cells"]) \
        or diff(s3["shed_ml"], s4["shed_ml"])
    out["hb_differs"] = diff(s3["hb"], s4["hb"])
    out["output_differs"] = diff(r3[MINUTE]["output"], r4[MINUTE]["output"])
    out["distinct"] = out["bleeding_differs"] and out["blood_state_differs"] and out["chronology_same"]
    return out


def respiratory_gap(sum3: dict, sum4: dict, case: str, surviving_rr: set, surviving_gas: set) -> dict:
    """The largest R3 - R4 respiratory differences at 120 over the pair's surviving latent combinations.

    surviving_rr: (drive gain, intrinsic, B, tau) value indices; surviving_gas: (ventilation gain, B, tau)."""
    gap = {"burden": 0.0, "rr": 0.0, "w": 0.0, "paco2": 0.0, "ph": 0.0}
    for g, i, b, t in surviving_rr:
        key = (b, t)
        gap["burden"] = max(gap["burden"], abs(sum3[key]["b120"] - sum4[key]["b120"]))
        gap["rr"] = max(gap["rr"], abs(rr_at_120(sum3, key, DRIVE_GAINS[g], INTRINSIC_RR[i])
                                       - rr_at_120(sum4, key, DRIVE_GAINS[g], INTRINSIC_RR[i])))
    for v, b, t in surviving_gas:
        x, y = sum3[(b, t)]["gas"][v], sum4[(b, t)]["gas"][v]
        if None in (x["paco2_120"], y["paco2_120"], x["ph_120"], y["ph_120"]):
            gap["paco2"] = gap["ph"] = math.inf
            continue
        gap["paco2"] = max(gap["paco2"], abs(x["paco2_120"] - y["paco2_120"]))
        gap["ph"] = max(gap["ph"], abs(x["ph_120"] - y["ph_120"]))
        gap["w"] = max(gap["w"], abs(PACO2_REF / x["paco2_120"] - PACO2_REF / y["paco2_120"]))
    return gap


PACO2_REF = vs.PACO2_REFERENCE


def r3r4_class(state: dict, gap: dict) -> str:
    if not state.get("distinct"):
        return R3R4_CLASSES[2]
    near = all(gap[k] <= R3R4_NEAR[k] for k in R3R4_NEAR)
    return R3R4_CLASSES[0] if near else R3R4_CLASSES[1]


# 7. The filter per (tone gain, demand): trajectories, rule parts, upstream units -------------------------------------------

ACID_KEYS = tuple((b, t) for b in range(len(STEADY_BURDENS)) for t in range(len(ACID_TAUS)))


def trajectory(bloods: dict, key: tuple, level: str, factor: float, gain: float) -> dict:
    """One blood record rebuilt at (tone gain, demand, level) by P2J-3's rebuild, its bundles per (B, tau)."""
    case = key[1]
    blood = bloods[key]
    rebuilt = vt.rebuild(blood, vt.tone_anchors(case, level, factor), gain, AFTERLOAD)
    rows = rebuilt["rows"]
    bundles = {(b, t): bundle(rows, blood["pulse"], case, STEADY_BURDENS[b], ACID_TAUS[t]) for b, t in ACID_KEYS}
    return {"blood": blood, "rows": rows, "structural": pf._sim(rebuilt, blood), "bundles": bundles}


def pair_readings(treated: dict, comparator: dict, kinds: tuple) -> dict:
    minutes = comparison_minutes(*kinds, treated["blood"])
    return {"minutes": list(minutes),
            "readings": {(v,) + key: [reading(treated["bundles"][key], comparator["bundles"][key], m, gain)
                                      for m in minutes]
                         for v, gain in enumerate(VENTILATION_GAINS) for key in ACID_KEYS}}


def needed(survivors: list) -> dict:
    """The (case, level, key) each kind needs at one (tone gain, demand), grouped by blood set."""
    out = {"P1": {}, "Q": set()}
    for i, a, b, q, d in survivors:
        for case, lam in ((C57, a), (C72, b)):
            level = vt.level_of(lam)
            out["P1"].setdefault((case, level, i), set()).add(d)
            out["Q"].add((case, level, q))
    return out


def evaluate_parts(bloods: dict, survivors: list, factor: float, gain: float) -> dict:
    """Every trajectory the survivors read at one (tone gain, demand), summarized, with the matched readings and the
    R3 / R4 rows kept; bundles dropped once read."""
    parts = {}
    need = needed(survivors)
    for (case, level, i), ds in sorted(need["P1"].items(), key=str):
        p1 = trajectory(bloods, ("P1", case, i), level, factor, gain)
        parts[("P1", case, level, i)] = {"summary": summarize(p1["bundles"], p1["structural"])}
        for d in sorted(ds):
            p2 = trajectory(bloods, ("P2", case, (i, d)), level, factor, gain)
            parts[("P2", case, level, (i, d))] = {"summary": summarize(p2["bundles"], p2["structural"]),
                                                  "pairs": {"P1": pair_readings(p2, p1, ("P2", "P1"))}}
    for case, level, q in sorted(need["Q"], key=str):
        run = {kind: trajectory(bloods, (kind, case, q), level, factor, gain)
               for kind in ("P3", "P4", "CF1", "CF2", NO_PRBC)}
        for kind, t in run.items():
            parts[(kind, case, level, q)] = {"summary": summarize(t["bundles"], t["structural"])}
        parts[("P3", case, level, q)]["pairs"] = {NO_PRBC: pair_readings(run["P3"], run[NO_PRBC], ("P3", NO_PRBC))}
        parts[("P4", case, level, q)]["pairs"] = {"CF1": pair_readings(run["P4"], run["CF1"], ("P4", "CF1")),
                                                  "CF2": pair_readings(run["P4"], run["CF2"], ("P4", "CF2"))}
        for kind in ("P3", "P4"):
            parts[(kind, case, level, q)]["rows"] = run[kind]["rows"]
    return parts


def _part_bits(part: dict, name: str, compute) -> int:
    cache = part.setdefault("bits", {})
    if name not in cache:
        cache[name] = compute()
    return cache[name]


def unit_keys(survivor: tuple) -> dict:
    """case -> kind -> the part key one upstream survivor reads."""
    i, a, b, q, d = survivor
    out = {}
    for case, lam in ((C57, a), (C72, b)):
        level = vt.level_of(lam)
        out[case] = {kind: (kind, case, level, key[2]) for kind, key in blood_keys(survivor, case).items()}
    return out


def unit_rules(parts: dict, survivor: tuple, arrival: dict) -> dict:
    """The fourteen rule bitsets of one upstream survivor over the latent combinations."""
    keys = unit_keys(survivor)
    part = lambda case, kind: parts[keys[case][kind]]
    rules = {"ARRIVAL_RR": arrival["rr"], "ARRIVAL_PACO2": arrival["paco2"]}
    sim = FULL
    for case in CASES:
        for kind in KINDS:
            p = part(case, kind)
            sim &= _part_bits(p, "SIM", lambda p=p: sim_bits(p["summary"]))
    rules["SIMULATION"] = sim
    rr = lambda case, kind, name, bounds, residual=False: _part_bits(
        part(case, kind), name, lambda: rr_bits(part(case, kind)["summary"], case, bounds, residual))
    gas = lambda case, kind, name, quantity, bounds: _part_bits(
        part(case, kind), name, lambda: gas_bits(part(case, kind)["summary"], quantity, bounds))
    rules["A"] = rr(C57, "P1", "A", ENVELOPES["A"]["rr"])
    rules["B"] = rr(C72, "P1", "B", ENVELOPES["B"]["rr"])
    rules["G"] = rr(C57, "P4", "G", ENVELOPES["G"]["rr"])
    rules["G2"] = rr(C72, "P4", "G2", ENVELOPES["G2"]["rr"])
    rules["H_PACO2"] = gas(C57, "P4", "H_PACO2", "paco2_120", ENVELOPES["H"]["paco2"]) & \
        gas(C72, "P4", "H_PACO2", "paco2_120", ENVELOPES["H"]["paco2"])
    rules["H_PH"] = gas(C57, "P4", "H_PH", "ph_120", ENVELOPES["H"]["ph"]) & \
        gas(C72, "P4", "H_PH", "ph_120", ENVELOPES["H"]["ph"])
    rules["I"] = rr(C57, "P4", "I", ENVELOPES["I"]["residual"][C57], True) & \
        rr(C72, "P4", "I", ENVELOPES["I"]["residual"][C72], True)
    rules["C"] = gas(C57, "P1", "C", "paco2_120", ENVELOPES["C"]["paco2"])
    rules["D"] = gas(C72, "P1", "D", "paco2_120", ENVELOPES["D"]["paco2"])
    rules["E"] = FULL
    rules["F"] = FULL
    for case in CASES:
        p2 = part(case, "P2")
        rules["E"] &= _part_bits(p2, "E", lambda p2=p2: pair_bits(p2["pairs"]["P1"]["readings"]))
        for kind, comparator in (("P3", NO_PRBC), ("P4", "CF1"), ("P4", "CF2")):
            p = part(case, kind)
            rules["F"] &= _part_bits(p, f"F {comparator}",
                                     lambda p=p, c=comparator: pair_bits(p["pairs"][c]["readings"]))
    return rules


# 8. What the survivors show: observables, extreme acidemia, counterfactual signs, R3 / R4 -----------------------------------

PAIR_TAGS = (("P2", "P1", "crystalloid"), ("P3", NO_PRBC, "prbc_R3"), ("P4", "CF1", "prbc_R4_unit1"),
             ("P4", "CF2", "prbc_R4_unit2"))


class Observed:
    """Per demand: survivor observables over unique (trajectory, latent sub-combination) entries."""

    def __init__(self):
        self.values, self.classes, self.minutes = {}, {}, {}
        self.signs = {"rr_follows_burden": [0, 0], "paco2_follows_burden": [0, 0]}
        self.extreme = {"survivors": 0, "flagged": 0, "by_case": {C57: 0, C72: 0}, "lowest": None}
        self.r3r4 = {"classes": {c: 0 for c in R3R4_CLASSES}, "pairs": [], "bug": False}

    def add(self, name: str, case: str, value) -> None:
        if value is not None:
            self.values.setdefault(f"{name} {case}", []).append(value)

    def public(self) -> dict:
        return {"observables": {k: ab._spread(v) for k, v in sorted(self.values.items())},
                "classes": self.classes, "comparison_minutes": {k: sorted(v) for k, v in self.minutes.items()},
                "signs": {k: {"checked": n, "held": h} for k, (n, h) in self.signs.items()},
                "extreme_acidemia": self.extreme, "r3r4": self.r3r4}


def _surviving(bits: int, dims: tuple) -> list:
    return [c for c in combos(dims) if bits & mask(dims, c)]


def _extreme_bits(part: dict) -> int:
    return _part_bits(part, "EXTREME", lambda: bits_of(GAS_DIMS, [
        (v,) + key for key, s in part["summary"].items() for v, g in s["gas"].items()
        if g["ph_low"] is not None and g["ph_low"] < EXTREME_ACIDEMIA]))


def observe(obs: Observed, parts: dict, units: list, states: dict, bloods: dict) -> None:
    """units: (upstream survivor, survivor bitset) at one (tone gain, demand)."""
    seen, quad = set(), {}
    for survivor, bits in units:
        if not bits:
            continue
        keys = unit_keys(survivor)
        flagged = 0
        for case in CASES:
            x = _extreme_bits(parts[keys[case]["P1"]])
            obs.extreme["by_case"][case] += (bits & x).bit_count()
            flagged |= x
        obs.extreme["survivors"] += bits.bit_count()
        obs.extreme["flagged"] += (bits & flagged).bit_count()
        for case in CASES:
            k = keys[case]
            rr_c, gas_c = _surviving(bits, RR_DIMS[case]), _surviving(bits, GAS_DIMS)
            for c in rr_c:
                seen.add(("arrival_rr", case, c[:2]))
                for tag, kind in (("untreated_rr", "P1"), ("definitive_rr", "P4")):
                    seen.add((tag, k[kind], c))
                for treated, comparator, tag in PAIR_TAGS:
                    seen.add((tag + "_rr", (k[treated], comparator), c))
            for c in gas_c:
                seen.add(("arrival_gas", case, c[:1]))
                for tag, kind in (("untreated_gas", "P1"), ("definitive_gas", "P4")):
                    seen.add((tag, k[kind], c))
                for treated, comparator, tag in PAIR_TAGS:
                    seen.add((tag, (k[treated], comparator), c))
                for kind in CLINICAL:
                    seen.add(("ph_range", k[kind], c))
            entry = quad.setdefault(k["P3"][1:], (set(), set()))
            entry[0].update(rr_c)
            entry[1].update(gas_c)
    rr_of = {}
    for tag, where, c in seen:
        if tag == "untreated_rr":
            rr_of.setdefault(where, set()).add(c)
    lowest = obs.extreme["lowest"]
    for tag, where, c in sorted(seen, key=str):
        if tag == "arrival_rr":
            obs.add("arrival_rr", where, ab.arrival_rr(DRIVE_GAINS[c[0]], INTRINSIC_RR[c[1]], where))
        elif tag == "arrival_gas":
            gain = VENTILATION_GAINS[c[0]]
            obs.add("arrival_paco2", where, vs.predicted_paco2(gain, where))
            obs.add("arrival_ph_diagnostic", where, vs.predicted_ph(gain, where))
        elif tag in ("untreated_rr", "definitive_rr"):
            g, i, b, t = c
            rr = rr_at_120(parts[where]["summary"], (b, t), DRIVE_GAINS[g], INTRINSIC_RR[i])
            obs.add(f"{tag}_120", where[1], rr)
            if tag == "definitive_rr":
                obs.add("residual_rr_above_intrinsic_120", where[1], rr - INTRINSIC_RR[i])
        elif tag in ("untreated_gas", "definitive_gas"):
            v, b, t = c
            g_ = parts[where]["summary"][(b, t)]["gas"][v]
            obs.add(f"{tag.split('_')[0]}_paco2_120", where[1], g_["paco2_120"])
            obs.add(f"{tag.split('_')[0]}_ph_120", where[1], g_["ph_120"])
            if tag == "untreated_gas":
                obs.add("untreated_ph_lowest_0_120", where[1], g_["ph_low"])
                if g_["ph_low"] is not None and (lowest is None or g_["ph_low"] < lowest["ph"]):
                    lowest = {"ph": g_["ph_low"], "case": where[1], "minute": g_["ph_low_minute"], **g_["at_low"],
                              "_where": where, "_acid": (b, t)}
        elif tag == "ph_range":
            v, b, t = c
            g_ = parts[where]["summary"][(b, t)]["gas"][v]
            obs.add("ph_lowest_any_scenario", where[1], g_["ph_low"])
            obs.add("ph_highest_any_scenario", where[1], g_["ph_high"])
        else:
            _observe_pair(obs, parts, tag, where, c)
    if lowest is not None and "_where" in lowest:
        where, (b, t) = lowest.pop("_where"), lowest.pop("_acid")
        burden = lowest["burden"]
        lowest["rr"] = ab._spread([vs.rr_series([burden], [True], DRIVE_GAINS[g], INTRINSIC_RR[i])[0]
                                   for g, i, b_, t_ in rr_of.get(where, ()) if (b_, t_) == (b, t)])
        lowest["flag"] = "CONSCIOUSNESS_COLLAPSE_REVIEW" if lowest["ph"] < EXTREME_ACIDEMIA else None
    obs.extreme["lowest"] = lowest
    for (case, level, q), (rr_c, gas_c) in sorted(quad.items(), key=str):
        p3, p4 = parts[("P3", case, level, q)], parts[("P4", case, level, q)]
        state = underlying(states[("P3", case, q)], states[("P4", case, q)], bloods[("P3", case, q)],
                           bloods[("P4", case, q)], p3["rows"], p4["rows"])
        gap = respiratory_gap(p3["summary"], p4["summary"], case, rr_c, gas_c)
        klass = r3r4_class(state, gap)
        obs.r3r4["classes"][klass] += 1
        obs.r3r4["bug"] |= klass == R3R4_CLASSES[2]
        if len(obs.r3r4["pairs"]) < 4 or klass == R3R4_CLASSES[2]:
            obs.r3r4["pairs"].append({"case": case, "level": level, "q": q, "class": klass, "gap": gap,
                                      "underlying": state})


def _observe_pair(obs: Observed, parts: dict, tag: str, where: tuple, c: tuple) -> None:
    key, comparator = where
    case = key[1]
    pair = parts[key]["pairs"][comparator]
    if tag.endswith("_rr"):
        g, i, b, t = c
        name = tag[:-3]
        for j, r in enumerate(pair["readings"][(0, b, t)]):
            if "burden_t" not in r:
                continue
            rate = lambda x: vs.rr_series([x], [True], DRIVE_GAINS[g], INTRINSIC_RR[i])[0]
            d_rr = rate(r["burden_t"]) - rate(r["burden_c"])
            obs.add(f"{name} delta_rr m{j}", case, d_rr)
            sign_b = _sign(r["burden"], r["burden_c"])
            obs.signs["rr_follows_burden"][0] += 1
            obs.signs["rr_follows_burden"][1] += _sign(d_rr, INTRINSIC_RR[i]) in (0, sign_b)
        return
    obs.minutes.setdefault(tag, set()).update(pair["minutes"])
    for j, r in enumerate(pair["readings"][c]):
        counts = obs.classes.setdefault(f"{tag} m{j} {case}", {})
        counts[r["class"]] = counts.get(r["class"], 0) + 1
        if "burden" not in r:
            continue
        for q in ("burden", "paco2", "ph", "deficit"):
            obs.add(f"{tag} delta_{q} m{j}", case, r[q])
        obs.signs["paco2_follows_burden"][0] += 1
        obs.signs["paco2_follows_burden"][1] += paco2_follows_burden(r["burden"], r["burden_c"], r["paco2"])


def paco2_follows_burden(d_burden: float, burden_c: float, d_paco2: float) -> bool:
    """PaCO2 = 40 / (1 + gain x burden) at a fixed gain: a higher burden never gives a higher PaCO2, and no burden change
    gives no PaCO2 change (a negligible PaCO2 change beside a burden change is accepted)."""
    sign_b, sign_p = _sign(d_burden, burden_c), _sign(d_paco2, PACO2_REF)
    return sign_p == -sign_b or (sign_p == 0 and sign_b != 0)


# 9. Latent support, identifiability, cross-demand classes -----------------------------------------------------------------

IDENTIFIABILITY_CLASSES = ("WELL_CONSTRAINED", "PARTIALLY_CONSTRAINED", "POORLY_IDENTIFIED", "NON_IDENTIFIABLE")
IDENTIFIABILITY_RULE = (
    "Per demand, on the survivors: NON_IDENTIFIABLE when no candidate survives, or when the filter does not read the "
    "parameter (for every upstream unit, every combination of the other parameters survives at all its values or at "
    "none); WELL_CONSTRAINED when one value survives; PARTIALLY_CONSTRAINED when some but not all do; POORLY_IDENTIFIED "
    "when all survive although the filter reads it (trade-offs). No best combination is selected.")
DEMAND_CLASSES = ("ROBUST_ACROSS_DEMAND", "DEMAND_1_0_ONLY", "DEMAND_1_1_ONLY", "DEMAND_INCOMPATIBLE")


def invariant(bits: int, dim: str) -> bool:
    """Every combination of the other parameters survives at all values of ``dim`` or at none."""
    k = DIMS.index(dim)
    base = bits & DIM_MASKS[dim][0]
    return all((bits & DIM_MASKS[dim][v]) >> (v * STRIDES[k]) == base for v in range(1, SIZES[k]))


def latent_support(union: int, units: list) -> dict:
    out = {}
    for dim in DIMS:
        values = [VALUES[dim][v] for v in range(len(VALUES[dim])) if union & DIM_MASKS[dim][v]]
        counts = {f"{VALUES[dim][v]:g}": (union & DIM_MASKS[dim][v]).bit_count() for v in range(len(VALUES[dim]))}
        reads = not all(invariant(bits, dim) for bits in units)
        if not values or not reads:
            klass = "NON_IDENTIFIABLE"
        elif len(values) == 1:
            klass = "WELL_CONSTRAINED"
        else:
            klass = "POORLY_IDENTIFIED" if len(values) == len(VALUES[dim]) else "PARTIALLY_CONSTRAINED"
        out[dim] = {"class": klass, "values": values, "latent_combinations_by_value": counts, "filter_reads_it": reads}
    return out


def cross_demand(unions: dict) -> dict:
    one, other = unions.get(1.0, 0), unions.get(1.1, 0)
    sets = {"ROBUST_ACROSS_DEMAND": one & other, "DEMAND_1_0_ONLY": one & ~other & FULL,
            "DEMAND_1_1_ONLY": other & ~one & FULL, "DEMAND_INCOMPATIBLE": FULL & ~(one | other)}
    return {name: {"count": bits.bit_count(),
                   "support": {dim: [VALUES[dim][v] for v in range(len(VALUES[dim])) if bits & DIM_MASKS[dim][v]]
                               for dim in DIMS}} for name, bits in sets.items()}


# 10. The filter driver and its independent direct check ---------------------------------------------------------------------

def arrival_bits() -> dict:
    return {"rr": arrival_rr_bits(), "paco2": arrival_paco2_bits()}


def filter_point(bloods: dict, survivors: list, factor: float, gain: float, arrival: dict, tally: Tally,
                 obs: Observed, states: dict) -> list:
    """One (tone gain, demand): the rule bitsets of every upstream survivor, tallied; the survivors observed."""
    parts = evaluate_parts(bloods, survivors, factor, gain)
    units, sample = [], []
    for n, survivor in enumerate(survivors):
        rules = unit_rules(parts, survivor, arrival)
        units.append((survivor, tally.add(rules, gain)))
        if n in (0, len(survivors) - 1):
            sample.append((gain, factor, survivor, rules))
    observe(obs, parts, units, states, bloods)
    return units, sample


DIRECT_RULE = ("An independent recomputation for a predeclared sample (the first and last upstream survivor of every "
               "tone gain and demand, all latent combinations): each rule evaluated from the rebuilt series and the "
               "core algebra written out (burden_series, rate_from_drive, PaCO2 = 40 / (1 + gain x burden), "
               "carbonic_ph), never through the summaries, tables or bitsets; it must equal the filter bit for bit.")


def _direct_series(bloods: dict, cache: dict, kind: str, case: str, k, level: str, factor: float, gain: float,
                   b: float, tau: float) -> dict:
    key = (kind, case, k, level, b, tau)
    if key not in cache:
        blood = bloods[(kind, case, k)]
        rebuilt = vt.rebuild(blood, vt.tone_anchors(case, level, factor), gain, AFTERLOAD)
        rows = rebuilt["rows"]
        deficit = [row["deficit"] for row in rows]
        burden = ab.burden_series(deficit, ab.arrival_burden(case), b, tau)[:len(rows)]
        hco3_0, a0 = ab.authored_gas(case)["hco3"], ab.arrival_burden(case)
        cache[key] = {"n": len(rows), "deficit": deficit, "pulse": list(blood["pulse"][:len(rows)]), "burden": burden,
                      "hco3": [hco3_0 - (x - a0) for x in burden], "blood": blood,
                      "structural": rebuilt["clamps"] > 0 or (rebuilt["stop"] is not None and blood["stop"] is None)}
    return cache[key]


def _direct_gas(s: dict, m: int, gain: float) -> tuple:
    if m >= s["n"] or not s["pulse"][m]:
        return None, None
    paco2 = PACO2_REF / (1.0 + gain * s["burden"][m])
    return paco2, dv.carbonic_ph(s["hco3"][m], paco2) if s["hco3"][m] > 0.0 else None


def _direct_rr(s: dict, gain: float, intrinsic: float) -> float:
    if s["n"] <= MINUTE or not s["pulse"][MINUTE]:
        return 0.0
    return dv.rate_from_drive(gain * s["burden"][MINUTE], intrinsic, DEFAULT_PROFILE)


def _direct_worse(t: dict, c: dict, minutes, vgain: float) -> bool:
    for m in minutes:
        alive_t, alive_c = m < t["n"] and t["pulse"][m], m < c["n"] and c["pulse"][m]
        if not alive_t:
            if alive_c:
                return True
            continue
        if not alive_c:
            continue
        ph_t, ph_c = _direct_gas(t, m, vgain)[1], _direct_gas(c, m, vgain)[1]
        if ph_t is None or ph_c is None:
            continue
        tol = lambda d, s: abs(d) <= 1e-9 * max(1.0, abs(s))
        d_def, d_b, d_ph = t["deficit"][m] - c["deficit"][m], t["burden"][m] - c["burden"][m], ph_t - ph_c
        if not tol(d_def, c["deficit"][m]) and d_def > 0 and not tol(d_b, c["burden"][m]) and d_b > 0 \
                and not tol(d_ph, ph_c) and d_ph < 0:
            return True
    return False


def direct_rules(bloods: dict, survivor: tuple, factor: float, gain: float, index: int, cache: dict) -> dict:
    v = latent_values(index)
    keys = {case: blood_keys(survivor, case) for case in CASES}
    level = {C57: vt.level_of(survivor[1]), C72: vt.level_of(survivor[2])}
    s = lambda kind, case: _direct_series(bloods, cache, kind, case, keys[case][kind][2], level[case], factor, gain,
                                          v["B"], v["tau"])
    intrinsic = {C57: v["intrinsic_57m"], C72: v["intrinsic_72f"]}
    out = {"SIMULATION": not any(x["structural"] or x["n"] <= MINUTE or min(x["hco3"]) <= 0.0
                                 for case in CASES for x in (s(kind, case) for kind in KINDS))}
    out["ARRIVAL_RR"] = all(abs(dv.rate_from_drive(v["drive_gain"] * ab.arrival_burden(case), intrinsic[case],
                                                   DEFAULT_PROFILE) - (26.0 if case == C57 else 24.0)) <= 3.0
                            for case in CASES)
    out["ARRIVAL_PACO2"] = all(abs(PACO2_REF / (1.0 + v["ventilation_gain"] * ab.arrival_burden(case))
                                   - (31.0 if case == C57 else 33.0)) <= 3.0 for case in CASES)
    rr = lambda kind, case: _direct_rr(s(kind, case), v["drive_gain"], intrinsic[case])
    gas = lambda kind, case: _direct_gas(s(kind, case), MINUTE, v["ventilation_gain"])
    out["A"] = 24.0 <= rr("P1", C57) <= 38.0
    out["B"] = 20.0 <= rr("P1", C72) <= 36.0
    out["G"] = 12.0 <= rr("P4", C57) <= 27.0
    out["G2"] = 12.0 <= rr("P4", C72) <= 24.0
    out["H_PACO2"] = all(gas("P4", case)[0] is not None and 30.0 <= gas("P4", case)[0] <= 42.0 for case in CASES)
    out["H_PH"] = all(gas("P4", case)[1] is not None and 7.35 <= gas("P4", case)[1] <= 7.45 for case in CASES)
    out["I"] = 0.0 <= rr("P4", C57) - intrinsic[C57] <= 12.0 and 0.0 <= rr("P4", C72) - intrinsic[C72] <= 10.0
    out["C"] = gas("P1", C57)[0] is not None and 18.0 <= gas("P1", C57)[0] <= 35.0
    out["D"] = gas("P1", C72)[0] is not None and 22.0 <= gas("P1", C72)[0] <= 38.0
    out["E"] = not any(_direct_worse(s("P2", case), s("P1", case),
                                     comparison_minutes("P2", "P1", s("P2", case)["blood"]), v["ventilation_gain"])
                       for case in CASES)
    out["F"] = not any(_direct_worse(s(t, case), s(c, case), comparison_minutes(t, c, s(t, case)["blood"]),
                                     v["ventilation_gain"])
                       for case in CASES for t, c in (("P3", NO_PRBC), ("P4", "CF1"), ("P4", "CF2")))
    return out


def direct_check(bloods: dict, sample: list, arrival: dict) -> dict:
    """sample: (tone gain, demand, upstream survivor, its filter bits per rule). Every rule, every latent combination."""
    out = {"units": 0, "candidates": 0, "mismatches": 0, "first_mismatch": None}
    for gain, factor, survivor, rules in sample:
        cache = {}
        out["units"] += 1
        for index in range(N_LATENT):
            direct = direct_rules(bloods, survivor, factor, gain, index, cache)
            out["candidates"] += 1
            for name in ORDER:
                if bool(rules[name] >> index & 1) != direct[name]:
                    out["mismatches"] += 1
                    if out["first_mismatch"] is None:
                        out["first_mismatch"] = {"rule": name, "tone_gain": gain, "demand": factor,
                                                 "survivor": list(survivor), "latent": latent_values(index)}
    out["equal"] = out["units"] > 0 and out["mismatches"] == 0
    return out


# 11. Upstream non-regression: P2K-3 reproduced, the new comparators against the core -----------------------------------------

VALIDATION_CANDIDATE = vs.VALIDATION_CANDIDATE


def p2k3_record() -> dict:
    record = json.loads(P2K3_RECORD.read_text(encoding="utf-8"))
    if record["freeze_digest"] != P2K3_DIGEST or record["verdict"]["verdict"] != vs.READY:
        raise AssertionError("the P2K-3 record is not the committed one")
    return record


def p2k3_reproduced(region: dict, store: dict, record: dict) -> dict:
    """P2K-3's reconstruction, decision pack and core validation recomputed on the live code equal its record."""
    joint = vs.joint_surface(ab.arrival_compatibility(), vs.paco2_compatibility())["joint"]
    evaluated = vs.evaluate(store, joint)
    validation = vs.validate(region, store)
    return {"reconstruction": vs._json(evaluated["tables"]) == record["reconstruction"],
            "decision_pack": vs._json(vs.decision_pack(evaluated)) == record["decision_pack"],
            "rejections": vs._json(evaluated["rejections"]) == record["rejections"],
            "plausible": vs._json(evaluated["plausible"]) == record["plausible"],
            "validation": vs._json(validation) == record["validation"], "p2k1_unchanged": ab.p2k1_unchanged(store),
            "p2j3_region": all(region["unchanged"].values())}


def _run_items(entry: dict, case: str, kind: str, factor: float, point: tuple, profile_changes: dict,
               gas: dict | None = None) -> dict:
    """acid_base._run_states's construction for any kind, the comparators included (their inputs from scenario_inputs)."""
    tau_d, gain_k, k, tau_l, excess, debt, delivery = point
    values = {**lr.blood_values(entry, case, None), "reserve": RESERVE}
    _, profile, full = blood_anchors.setup(case, **values)
    case_values = calibration.case_values(case, calibration.GICandidate({}, excess=excess, debt=debt,
                                                                        delivery=delivery, intrinsic="midpoint"))
    case_values["preload_fraction"] = full[pt.bc.POS]
    case_values["arrival_delivery_ratio"] /= RESERVE
    case_values["metabolic_demand_baseline"] *= factor
    anchors = gi_reference.candidate_anchors(case, case_values)
    if gas is not None:
        anchors = replace(anchors, arrival_bicarbonate=gas["hco3"], arrival_paco2=gas["paco2"],
                          intrinsic_respiratory_rate=gas["intrinsic"])
    profile = replace(profile, debt_clearance_tau_min=tau_d, debt_per_delivery_deficit=gain_k, debt_to_lactate_gain=k,
                      lactate_clearance_tau_min=tau_l, **profile_changes)
    states, stop = blood_anchors.trajectory(anchors, scenario_inputs(kind, case, full), pt.MINUTES, profile)
    return {"states": states, "anchors": anchors, "profile": profile, "rows": pt._rows(states, anchors, profile, full),
            "stop": stop}


def validate_comparators(region: dict, bloods: dict) -> dict:
    """For the comparators P2K-3 never reconstructed (CF1, CF2, NP): one full core run each per case and tone gain at
    demand 1.0 for the first upstream survivor, with the validation candidate declared and without it. The factorized
    burden, RR, W, PaCO2 and pH equal the ventilation module on the core's states; every upstream row and state but the
    burden equals the run without the candidate."""
    drive_gain, i57, i72, b, tau, vgain = VALIDATION_CANDIDATE
    candidate = vn.VentilationCandidate(vgain)
    out = {"compared": 0, "equal": True, "max_abs_diff": 0.0, "upstream_equal": True,
           "domains": {name: True for name in vs.UPSTREAM_DOMAINS}, "candidate": list(VALIDATION_CANDIDATE)}
    for gain in TONE_GAINS:
        survivor = sorted(region["survivors"][(gain, 1.0)])[0]
        for case, lam in ((C57, survivor[1]), (C72, survivor[2])):
            q = survivor[3]
            intrinsic = i57 if case == C57 else i72
            gas = {**ab.authored_gas(case), "intrinsic": intrinsic}
            tone = {"deficit_to_tone_gain": gain, "afterload_sensitivity": AFTERLOAD}
            level = vt.level_of(lam)
            for kind in ("CF1", "CF2", NO_PRBC):
                entry = region["source"]["p3"][q]
                plain = _run_items(entry, case, kind, 1.0, LAMBDAS[lam], tone)
                live = _run_items(entry, case, kind, 1.0, LAMBDAS[lam],
                                  {**tone, "deficit_to_acid_gain": b / tau, "acid_clearance_tau_min": tau,
                                   "acid_to_drive_gain": drive_gain, "ventilation_efficiency": vs.EFFICIENCY}, gas)
                out["compared"] += 1
                t = trajectory(bloods, (kind, case, q), level, 1.0, gain)["bundles"][(STEADY_BURDENS.index(b),
                                                                                      ACID_TAUS.index(tau))]
                states = live["states"]
                n = min(len(states), t["n"])
                out["equal"] &= len(states) == t["n"] and t["pulse"][:n] == [st.R.pulse_present for st in states[:n]]
                rr = vs.rr_series(t["burden"], t["pulse"], drive_gain, intrinsic)
                w, paco2, ph = t["gas"][vgain]
                for m, state in enumerate(states[:n]):
                    r = vn.ventilated_respiration(state, live["anchors"], live["profile"], candidate)
                    for got, exp in ((r.acid_burden, t["burden"][m]), (r.respiratory_rate, rr[m]),
                                     (r.ventilation, w[m]), (r.paco2, paco2[m]), (r.ph, ph[m])):
                        if got is None or exp is None:
                            out["equal"] &= got is exp
                            continue
                        out["max_abs_diff"] = max(out["max_abs_diff"], abs(got - exp))
                out["upstream_equal"] &= len(plain["rows"]) == len(live["rows"]) and all(
                    {k: v for k, v in p.items() if k != "rr"} == {k: v for k, v in q_.items() if k != "rr"}
                    for p, q_ in zip(plain["rows"], live["rows"])) and all(
                    ab._upstream(s) == ab._upstream(u) for s, u in zip(plain["states"], live["states"]))
                for domain, (rows, fields) in vs.UPSTREAM_DOMAINS.items():
                    out["domains"][domain] &= vs._domain_equal(plain, live, rows, fields)
    out["equal"] = out["equal"] and out["max_abs_diff"] <= 1e-9
    return out


def comparators_matched(region: dict) -> dict:
    """comparator_inputs over every blood set the comparators use, both cases."""
    out = {"checked": 0, "matched": True, "first_failure": None}
    p1 = sorted({k[2] for k in region["bloods"] if k[0] == "P2"}, key=str)
    qs = sorted({k[2] for k in region["bloods"] if k[0] == "P3"})
    pairs = [("P2", "P1", k, k[0]) for k in p1] + [(t, c, q, q) for q in qs
                                                   for t, c in (("P3", NO_PRBC), ("P4", "CF1"), ("P4", "CF2"))]
    for case in CASES:
        for treated, comparator, k1, k2 in pairs:
            result = comparator_inputs(region, treated, comparator, case, k1, k2)
            out["checked"] += 1
            if not result["matched"] and out["first_failure"] is None:
                out["first_failure"] = {"case": case, "treated": treated, "comparator": comparator, "key": str(k1),
                                        "result": result}
            out["matched"] &= result["matched"]
    return out


# 12. Readiness, recommendation, policy -----------------------------------------------------------------------------------

READY = "RR_VENTILATION_OBSERVABLE_FILTER_SATISFIED"
NOT_READY = "RR_VENTILATION_OBSERVABLE_FILTER_NOT_READY"
EMPTY = "RR_VENTILATION_FILTER_EMPTY"
CRITERIA = ("upstream_unchanged", "comparators_matched", "survivors_exist", "filter_consistent", "envelopes_hold",
            "arrival_compatible", "ph_coherent", "treatment_responses_coherent", "r3_r4_physiological",
            "nothing_approved")
VERDICT_RULE = (
    "Frozen. EMPTY when no candidate survives at either demand (a STOP: nothing is widened). READY when every criterion "
    "holds: the upstream is unchanged (the closed files at their ef2cfe8 bytes, the P2J-3 region, P2K-1 and the P2K-3 "
    "record reproduced, the new comparators equal the core with every upstream row unchanged); every comparator omits "
    "only its target exposure; some candidate survives at some demand (robustness across demands is diagnostic, never "
    "required); the independent direct check equals the filter; every survivor's observables lie in A-I; its arrival "
    "RR and PaCO2 lie in their windows (arrival pH never filters); pH stays within 6.8-7.8 on every clinical "
    "trajectory and the bank's pH is reproduced within 0.005; no survivor's matched comparison rejects and RR and PaCO2 "
    "follow the burden in every reading; no R3 / R4 pair is a SCENARIO_STATE_COLLAPSE_BUG (a STOP); nothing is "
    "approved. Otherwise NOT_READY with the first failing criterion as the blocker; an early stop lists what it never "
    "reached as not evaluated.")
NEXT_RULE = (
    "Predeclared. When READY: MOVE_FORWARD (the GI respiratory domain is bounded for the current cases; consciousness / "
    "neurologic response is next and is not begun here), the diagnostics forwarded: untreated extreme acidemia to "
    "CONSCIOUSNESS_COLLAPSE_REVIEW, the cross-demand classes to the demand question, the latent classes as explicit "
    "uncertainty (broad B, tau, intrinsic RR or gains never call for another respiratory package). Otherwise "
    "STOP_FOR_FACULTY_REVIEW with the blocker.")
POLICY = ("Shadow only. P2K-3's committed trajectories and machinery, the P2J-3 comparators, the legacy RR never read; "
          "no envelope, window or support changed after a count; untreated and arrival pH never filter; demand "
          "robustness never required; RR alone never judges a treatment; R3 and R4 never required to differ by "
          "treatment identity; nothing selected or approved.")
MIGRATION_GATE = ("MIGRATION_GATE_CLOSED: no runtime integration, GI or second-family migration or parameter approval "
                  "is authorized; consciousness and collapse are not calibrated")


def verdict(checks: dict) -> dict:
    failing = [name for name in CRITERIA if checks.get(name) is False]
    unevaluated = [name for name in CRITERIA if name not in checks]
    if checks.get("survivors_exist") is False:
        result = EMPTY
    elif failing:
        result = f"{NOT_READY} - {failing[0].upper()}"
    else:
        result = READY if not unevaluated else f"{NOT_READY} - NOT_EVALUATED"
    return {"verdict": result, "checks": checks, "failing": failing, "not_evaluated": unevaluated}


def recommendation(result: dict) -> dict:
    if result["verdict"] == READY:
        return {"recommendation": "MOVE_FORWARD", "next": "CONSCIOUSNESS / NEUROLOGIC RESPONSE (not begun)",
                "forwarded": {"untreated_extreme_acidemia": "CONSCIOUSNESS_COLLAPSE_REVIEW",
                              "cross_demand": "the demand question (diagnostic)",
                              "latent": "explicit uncertainty; no respiratory package for identifiability alone"},
                "rule": NEXT_RULE}
    return {"recommendation": "STOP_FOR_FACULTY_REVIEW", "blocker": result["verdict"], "rule": NEXT_RULE}


def _within(spread: dict, bounds: tuple) -> bool:
    return spread.get("n", 0) > 0 and bounds[0] <= spread["low"] and spread["high"] <= bounds[1]


def survivor_checks(public: dict) -> dict:
    """The criteria the survivors' own observables decide, per demand with survivors (observed independently of the
    bitsets that selected them)."""
    out = {"envelopes_hold": True, "arrival_compatible": True, "ph_coherent": True,
           "treatment_responses_coherent": True, "r3_r4_physiological": True, "read": 0}
    for factor, data in public.items():
        if not data["filter"]["survivors"]:
            continue
        out["read"] += 1
        o = data["observed"]["observables"]
        get = lambda name, case: o.get(f"{name} {case}", {})
        for case, (a, g) in ((C57, ("A", "G")), (C72, ("B", "G2"))):
            out["envelopes_hold"] &= _within(get("untreated_rr_120", case), ENVELOPES[a]["rr"])
            out["envelopes_hold"] &= _within(get("untreated_paco2_120", case),
                                             ENVELOPES["C" if case == C57 else "D"]["paco2"])
            out["envelopes_hold"] &= _within(get("definitive_rr_120", case), ENVELOPES[g]["rr"])
            out["envelopes_hold"] &= _within(get("definitive_paco2_120", case), ENVELOPES["H"]["paco2"])
            out["envelopes_hold"] &= _within(get("definitive_ph_120", case), ENVELOPES["H"]["ph"])
            out["envelopes_hold"] &= _within(get("residual_rr_above_intrinsic_120", case),
                                             ENVELOPES["I"]["residual"][case])
            out["arrival_compatible"] &= _within(get("arrival_rr", case), ARRIVAL_RR[case])
            out["arrival_compatible"] &= _within(get("arrival_paco2", case), ARRIVAL_PACO2[case])
            out["ph_coherent"] &= _within(get("ph_lowest_any_scenario", case), vs.PH_PLAUSIBLE)
            out["ph_coherent"] &= _within(get("ph_highest_any_scenario", case), vs.PH_PLAUSIBLE)
        classes = data["observed"]["classes"]
        out["treatment_responses_coherent"] &= bool(classes) and not any(
            counts.get(c) for counts in classes.values() for c in REJECTING)
        for checked, held in ((s["checked"], s["held"]) for s in data["observed"]["signs"].values()):
            out["treatment_responses_coherent"] &= checked > 0 and checked == held
        r3r4 = data["observed"]["r3r4"]
        out["r3_r4_physiological"] &= not r3r4["bug"] and sum(r3r4["classes"].values()) > 0
    out["ph_coherent"] &= all(abs(ab.ph_reconstruction(case)["error"]) <= 0.005 for case in CASES)
    return out


# 13. Closure: the closed files at ef2cfe8, P2K-3's freeze map --------------------------------------------------------------

CLOSED_AT_P2K3 = {**vs.CORE_AT_P2K2,
                  "clinical_core/ventilation.py": "260393add18e2275ee21411512d18531a74387f853bb76a2f33f89d5cb1bafe9",
                  "clinical_core/ventilation_surface.py":
                      "d361b500ccaf059784ea7e7662b6be5dd7d02019174c2f66cc0ca0ff24245825"}
OWN = ("clinical_core/ventilation_filter.py",)
REPORT = "clinical_core/ventilation_filter_report.py"
#: The two tuple-only files at P2K-3 (ef2cfe8): P2K-4 adds its modules to their tuples, nothing else.
TUPLE_AT_P2K3 = {"clinical_core/lactate_slice.py": "20aee425ac512b3e1c82871ac685a3d89b532ba187f01fd6d3c21e44171a0f8a",
                 "clinical_core/decision_pack.py": "e828cd8202ba37721da077002edd0f712b420f9153d14164c1de5041aefe9a80"}
TUPLES_ADDED = {"DOWNSTREAM_REPORTS": (REPORT,), "PACK_DIGEST_EXCLUDED": ("clinical_core/ventilation_filter.py", REPORT)}


def closed_unchanged() -> dict:
    return {relative: hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == sha
            for relative, sha in CLOSED_AT_P2K3.items()}


def p2k3_sources(sources: dict) -> dict:
    """A P2K-3 dependency map: P2K-4's module removed, the two tuple-only files at their P2K-3 hashes while only their
    tuples changed (the tuple content itself is pinned by the tests)."""
    out = {k: v for k, v in sources.items() if k not in OWN}
    for relative, sha in TUPLE_AT_P2K3.items():
        item = vt.TUPLE_CHANGES[relative]
        if relative in out and vt.outside_digest(vt._live(relative), item["changed"]) == item["outside_p2j1"]:
            out[relative] = sha
    return out


# 14. Design, freeze, run --------------------------------------------------------------------------------------------------

def design() -> dict:
    return {"revision": REVISION, "decided": DECIDED, "faculty": FACULTY, "carried": CARRIED,
            "demand_normalization": DEMAND_NORMALIZATION, "status": STATUS, "dims": list(DIMS),
            "values": {d: list(v) for d, v in VALUES.items()}, "excluded_gains": [0.08], "minute": MINUTE,
            "arrival_rr": ARRIVAL_RR, "arrival_paco2": ARRIVAL_PACO2, "envelopes": ENVELOPES, "bounds_rule": BOUNDS_RULE,
            "extreme_acidemia": EXTREME_ACIDEMIA, "extreme_rule": EXTREME_RULE, "kinds": list(KINDS),
            "comparators": COMPARATORS, "comparator_rule": COMPARATOR_RULE, "classes": list(CLASSES),
            "rejecting": list(REJECTING), "f_rejection_name": F_REJECTION_NAME, "signal_rule": SIGNAL_RULE,
            "order": list(ORDER), "rejection_class": REJECTION_CLASS, "order_rule": ORDER_RULE,
            "r3r4_classes": list(R3R4_CLASSES), "r3r4_near": R3R4_NEAR, "r3r4_rule": R3R4_RULE,
            "identifiability_rule": IDENTIFIABILITY_RULE, "demand_classes": list(DEMAND_CLASSES),
            "direct_rule": DIRECT_RULE, "validation_candidate": list(VALIDATION_CANDIDATE), "criteria": list(CRITERIA),
            "verdict_rule": VERDICT_RULE, "next_rule": NEXT_RULE, "policy": POLICY, "migration_gate": MIGRATION_GATE,
            "closed_at_p2k3": CLOSED_AT_P2K3, "own": list(OWN), "report": REPORT, "tuple_at_p2k3": TUPLE_AT_P2K3,
            "tuples_added": {k: list(v) for k, v in TUPLES_ADDED.items()}}


def freeze_digest() -> str:
    text = json.dumps({"revision": REVISION, "p2k3": hashlib.sha256(P2K3_RECORD.read_bytes()).hexdigest(),
                       "design": design(), "sources": bf.freeze_sources()}, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _stopped(out: dict, checks: dict, why: str) -> dict:
    out["stopped"] = why
    out["verdict"] = verdict(checks)
    out["recommendation"] = recommendation(out["verdict"])
    return out


def run(progress=None, map_=map) -> dict:
    say = progress or (lambda *_: None)
    with lr.P2FGuard(), lr.LegacyLock():
        record = p2k3_record()
        out = {"freeze_digest": freeze_digest(), "decided": DECIDED, "revision": REVISION, "policy": POLICY,
               "record": P2K3_DIGEST, "design": design(), "closed_unchanged": closed_unchanged(),
               "arrival_ph_diagnostic": arrival_ph_diagnostic(), "approval": STATUS["approved"],
               "migration_gate": MIGRATION_GATE}
        checks = {"nothing_approved": True}
        if not all(out["closed_unchanged"].values()):
            checks["upstream_unchanged"] = False
            return _stopped(out, checks, "a closed file changed (P2K-4-9): STOP")
        say("certified physiology (P2J-3 region), comparators, P2K-3 store")
        region = br.pressure_tone_region(map_, say)
        arrivals = lr.arrival_table()
        bloods = {**region["bloods"], **dict(map_(_np_blood_task, np_tasks(region)))}
        store = ab.reconstruct(region, arrivals)
        say("upstream non-regression")
        reproduced = p2k3_reproduced(region, store, record)
        comparators = validate_comparators(region, bloods)
        out.update({"p2k3_reproduced": reproduced, "comparator_validation": comparators,
                    "arrival_reproduced": {"rr": vs._json(ab.arrival_compatibility()) == record["arrival_rr"],
                                           "paco2": vs._json(vs.paco2_compatibility()) == record["arrival_paco2"]}})
        checks["upstream_unchanged"] = all(reproduced.values()) and comparators["equal"] and \
            comparators["upstream_equal"] and all(comparators["domains"].values())
        if not checks["upstream_unchanged"]:
            return _stopped(out, checks, "the upstream physiology or P2K-3 is not reproduced (P2K-4-9): STOP")
        matched = comparators_matched(region)
        out["comparators_matched"] = matched
        checks["comparators_matched"] = matched["matched"]
        if not matched["matched"]:
            return _stopped(out, checks, "a comparator changes more than its target exposure: STOP")
        say("R3 / R4 core states")
        qs = {case: {s[3] for units in region["survivors"].values() for s in units} for case in CASES}
        states = dict(map_(_state_task, state_tasks(region, qs)))
        arrival = arrival_bits()
        say("filter")
        tallies, observed, unions, by_unit, sample = {}, {}, {}, {}, []
        for (gain, factor), survivors in sorted(region["survivors"].items()):
            say(f"tone {gain:g}, demand {factor:g}")
            tally, obs = tallies.setdefault(factor, Tally()), observed.setdefault(factor, Observed())
            units, picked = filter_point(bloods, sorted(survivors), factor, gain, arrival, tally, obs, states)
            by_unit.setdefault(factor, []).extend(bits for _, bits in units)
            unions[factor] = unions.get(factor, 0) | tally.latent
            sample.extend(picked)
        public = {f"{factor:g}": {"filter": tallies[factor].public(), "observed": observed[factor].public(),
                                  "latent_support": latent_support(unions[factor], by_unit[factor])}
                  for factor in sorted(tallies)}
        out["demands"] = public
        out["cross_demand"] = cross_demand(unions)
        checks["survivors_exist"] = any(t.survivors for t in tallies.values())
        if not checks["survivors_exist"]:
            return _stopped(out, checks, "no candidate survives at either demand: STOP (RR_VENTILATION_FILTER_EMPTY)")
        say("direct check")
        direct = direct_check(bloods, sample, arrival)
        out["direct_check"] = direct
        checks["filter_consistent"] = direct["equal"]
        decided = survivor_checks(public)
        for name in ("envelopes_hold", "arrival_compatible", "ph_coherent", "treatment_responses_coherent",
                     "r3_r4_physiological"):
            checks[name] = decided[name]
        checks["arrival_compatible"] &= all(out["arrival_reproduced"].values())
        if not checks["r3_r4_physiological"]:
            return _stopped(out, checks, "R3 / R4 underlying states collapse (SCENARIO_STATE_COLLAPSE_BUG): STOP")
        out["efficiency"] = {"p2j3_blood_runs": region["blood_runs"], "p2j3_counterfactual_runs":
                             region["counterfactual_runs"], "no_prbc_runs": len(np_tasks(region)),
                             "r3r4_state_runs": len(states), "comparator_core_runs": 2 * comparators["compared"],
                             "p2k3_validation_runs": 2 * record["validation"]["compared"],
                             "latent_combinations": N_LATENT,
                             "candidates_evaluated": sum(t.entering for t in tallies.values()),
                             "upstream_units": sum(t.units for t in tallies.values()),
                             "direct_check_candidates": direct["candidates"], "cartesian_sweep": False,
                             "legacy_read": False, "bitset_rules": len(ORDER)}
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
        result = run(progress=lambda *m: print(*m, flush=True))
        (args.out / "ventilation_filter.json").write_text(json.dumps(result, indent=1, sort_keys=True, default=str)
                                                          + "\n", encoding="utf-8")
        print(result["verdict"]["verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
