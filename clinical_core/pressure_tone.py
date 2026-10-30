"""Phase 2 shadow core, P2J-1: the pressure / vascular-tone structural audit and calibration surface.

    python -m clinical_core.pressure_tone --digest
    python -m clinical_core.pressure_tone --design
    python -m clinical_core.pressure_tone --run --out <directory outside the repository>

Shadow only and offline. The first pressure-domain package (faculty brief of 2026-10-30, recorded in FACULTY):

1. Audit: the exact derivation of output, tone T, SBP, DBP, MAP, pulse pressure and the relative pressure the HR term
   reads, with every floor, cap and knee and each parameter's provenance (EQUATIONS); the knee classified on fixed
   states (``classify_mapping``); zero output and arrest; what T means and every path it takes (``tone_paths``); the
   pump / tone / output coupling; the authored pressures; the arrival reconstruction; the normalization.
2. One structural correction, the minimum the brief authorizes (P2J-1-9), made in ``derived.arterial_pressures``
   before this module was frozen: the relation the core read until P2I-2AK (``prior_pressures``) spliced the adopted
   linear relation (arrival less 45 / 25 mmHg per unit of 1 - pressure_rel) onto a proportional ramp at a provisional
   knee (0.5). The splice broke the slope (CONTINUOUS_WITH_KNEE) and the linear branch carried a resistance of its own
   that T did not (a hidden, flow-dependent tone). SBP and DBP are now the arrival values times pressure_rel = output
   x T over the whole range: no knee, no floor, no new parameter; the two gains and the knee stay in the profile,
   unread.
3. A candidate surface frozen before any trajectory (CANDIDATE_SURFACE, RANGE_RULE); decision trajectories P1-P7 on
   the retained physiology (the P2I-2AJ / P2I-2AK lactate units at demand 1.0 and 1.1, reproduced exactly); the
   directional invariants (DIRECTIONS); identifiability; the HR and demand propagation audits; a baroreflex
   reconnection plan; the readiness verdict.

Pressure never feeds HR here: the primary HR profile keeps the pressure term at 0 (PRESSURE_TERM_DIAGNOSTIC_ONLY).
Nothing is fitted, selected or approved, no hard pressure envelope is applied, and legacy pressure is never read.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from dataclasses import replace
from pathlib import Path

from . import blood_anchors, calibration, gi_reference
from . import blood_constraints as bc
from . import blood_fluid_calibration as bf
from . import hr_envelope_filter as hf
from . import hr_observables as ho
from . import hr_primary as hp
from . import lactate_adequacy as la
from . import lactate_closure as lc
from . import lactate_rebuild as lr
from .bands import ARRIVAL
from .derived import (DEFAULT_PROFILE, OUTPUT_EPSILON, arrival_filling, arrival_state, arterial_pressures, derive, effective_delivery,
                      effective_oxygen_deficit)
from .state import Anchors, RhythmState, UnresolvedBoundary, anchored_state

DECIDED = "2026-10-30"
REVISION = "P2J-1"
ROOT = lc.ROOT
CASES = lc.CASES
C57, C72 = CASES
L1, L2, L3 = lc.L1, lc.L2, lc.L3
#: L3 with only the endoscopic haemostasis omitted: PRBC with the bleeding still running (P3).
NO_HAEMOSTASIS = "L3_WITHOUT_HAEMOSTASIS"
SCENARIOS = {"P1": L1, "P2": L2, "P3": NO_HAEMOSTASIS, "P4": L3}
MINUTES = lr.MINUTES
TIMES = (0, 15, 30, 60, 90, 120)
RESERVE = lc.RESERVE
LAMBDAS = ho.LAMBDAS
DEMANDS = hf.DEMANDS
UNITS = hf.UNITS
TUPLE_ONLY = ("clinical_core/decision_pack.py", "clinical_core/lactate_slice.py")
OWN = ("clinical_core/pressure_tone.py",)
P2I2AK_RECORD = ROOT / "docs" / "revision" / "P2I2AK_hr_envelope_filter.json"
P2I2AK_DIGEST = "31f092650ee73ff4134fc9e5cc79b3a171fb7bb54de553fc2a7de2081f309dc3"
#: P2J-1's executable changes outside its own module, file by file: the file's hash at P2I-2AK (052d816), the top-level
#: statements P2J-1 changed (a definition by its name, any other statement by a name it reads), and the AST dump digest
#: of every other top-level statement, which must stay P2I-2AK's. derived.py: the pressure relation and the PARAMETERS
#: notes; shadow.py: the golden's difference registry and the consciousness attribution's cause labels.
DERIVED, SHADOW = "clinical_core/derived.py", "clinical_core/shadow.py"
P2J1_CHANGES = {
    DERIVED: {"sha_at_p2i2ak": "e53e2b388d4cfdef2dfc08afdc85573da62a2cacf40b1dca340d1fdbfa5961c9",
              "changed": ("arterial_pressures", "PARAMETERS"),
              "outside": "b44a729e1fe687d51941d9d8025fd2c19a9f44ca9e281d2649684be8c750baa8"},
    SHADOW: {"sha_at_p2i2ak": "b5a128b3dc9634ff60ab585677d6274e7b2fd613f8f7d5d097ddf8cc9307e693",
             "changed": ("DIFFERENCES", "_STRUCTURAL", "EXPECTED_DIFFERENCES", "DORMANT", "DECISIONS",
                         "consciousness_attribution"),
             "outside": "5b22d2194413bd75ebe79eb5988670a3866bfb00ec90f5ad95a3d324aaa5b5f1"},
}

FACULTY = {
    "decided": DECIDED,
    "hr": "P2I-2AK accepted (HR_OBSERVABLE_FILTER_SATISFIED); the HR region is carried as uncertainty: no intrinsic "
          "rate, acute-deficit gain, debt gain or sinus ceiling is selected or approved",
    "demand": "1.0 and 1.1 stay CURRENTLY_COMPATIBLE uncertainty states; robustness across them is not required; "
              "pressure is simulated once if it is invariant to demand",
    "pressure_to_hr": "PRESSURE_TERM_DIAGNOSTIC_ONLY: the pressure contribution to the sympathetic drive stays 0 in the "
                      "primary HR profile until pressure is structurally coherent and a later package reconnects it",
    "structure": "pressure continuous in output; never decreasing with output at a fixed tone or with tone at a fixed "
                 "output; approaching zero with output; no arbitrary positive floor without output; consistent with "
                 "pulse, rhythm and arrest. A smooth nonlinear mapping is acceptable; a physiologically meaningful knee "
                 "may be later; an arbitrary implementation discontinuity is not",
    "correction": "the minimum common-physiology correction of a clear structural defect; no fit to the two GI "
                  "pressures, no GI-specific term, no unnecessary change to output, no new parameter unless "
                  "structurally required (then stop for authorization before any range)",
    "scope": "shadow only; no runtime integration, GI or second-family migration, final pressure parameter, hard "
             "pressure envelope, pressure -> HR reconnection, RR calibration, collapse, legacy fitting or HR "
             "latent selection",
}

# 1. The derivation, term by term (P2J-1-1) --------------------------------------------------------------------------

AUTHORED, DERIVED_FROM_AUTHORED = "AUTHORED_OBSERVATION", "MODEL_DERIVED"
ADOPTED_LEGACY, PROVISIONAL, STRUCTURAL, NOT_READ = ("ADOPTED_LEGACY_MAGNITUDE", "PROVISIONAL_CANDIDATE", "STRUCTURAL",
                                                     "NOT_READ_SINCE_P2J1")
#: (term, equation, parameters, provenance, default, status, scope). No term is faculty-approved: ADOPTED_LEGACY is the
#: family engine's magnitude converted, never a faculty value for the core.
EQUATIONS = (
    ("output", "Q = P x (R.output_factor / arrival output_factor) x preload_rel x 1 / (1 + a (T - 1))",
     "P, rhythm output factor, preload curve (scale, arrival position, c), afterload_sensitivity a",
     "KD-S4, P2D-5 (derived._perfusion)", "a = 0.3", PROVISIONAL, "common (arrival position per case)"),
    ("preload_rel", "position(V) / position(0) on 1 - exp(-x / (scale x P^c)), x = arrival filling + V",
     "preload_curve_scale_ml, arrival_preload_fraction / case position, pump_preload_coupling",
     "KD-S4, P2D-5, P2I-2T (V from the shared blood state)", "scale 833.3 mL-eq, c = 1", PROVISIONAL,
     "common (position per case)"),
    ("vascular tone T", "a channel: multiplier, 1 at arrival; changed only by contributions (none in the GI cases)",
     "channel guard [0.1, 3.0]", "proposal §7.2, §7.4 (anchoring)", "1", STRUCTURAL, "common"),
    ("relative pressure", "p = Q x T (relative to arrival: 1 there)", "none", "KD-S4 (derived._perfusion)", "",
     STRUCTURAL, "common"),
    ("SBP", "SBP = SBP_arrival x max(0, p) (P2J-1; before: SBP_a - 45 (1 - p) above the knee, the knee value x p / "
     "knee below it)", "authored arrival SBP", "P2J-1 (derived.arterial_pressures)", "", STRUCTURAL,
     "scale per case (authored)"),
    ("DBP", "DBP = DBP_arrival x max(0, p) (P2J-1; before: DBP_a - 25 (1 - p) above the knee, ramp below)",
     "authored arrival DBP", "P2J-1", "", STRUCTURAL, "scale per case (authored)"),
    ("MAP", "MAP = (SBP + 2 DBP) / 3, so MAP = MAP_arrival x p since P2J-1", "none", "derived.derive", "", STRUCTURAL,
     "common"),
    ("pulse pressure", "PP = SBP - DBP = PP_arrival x p since P2J-1 (not modelled on its own)", "none", "derived",
     "", STRUCTURAL, "common"),
    ("HR pressure term", "sympathetic_per_pressure_deficit x (1 - p) in the drive target; 0 in the primary HR profile",
     "sympathetic_per_pressure_deficit", "KD-S2, P2I-2AG (PRESSURE_TERM_DIAGNOSTIC_ONLY)",
     "1.0 (default profile), 0.0 (primary HR profile)", PROVISIONAL, "common"),
    ("sbp_per_pressure_deficit", "read until P2I-2AK above the knee", "45 mmHg per unit", "family_engine._surface",
     "45", NOT_READ, "common"),
    ("dbp_per_pressure_deficit", "read until P2I-2AK above the knee", "25 mmHg per unit", "family_engine._surface",
     "25", NOT_READ, "common"),
    ("low_output_pressure_knee", "read until P2I-2AK: the splice point", "0.5 of p", "P2E-4", "0.5", NOT_READ,
     "common"),
    ("arrival anchors", "SBP 88 / DBP 54 (57m), 98 / 62 (72f)", "case bank", "clinical_cases.py:881, :910", "",
     AUTHORED, "per case"),
    ("consciousness by pressure", "level 1 below SBP 80, 2 below 65 (raw SBP)", "pressure_levels",
     "family_engine._PRESSURE_LEVELS", "(80, 1), (65, 2)", ADOPTED_LEGACY, "common"),
    ("zero output", "Q <= 1e-9 with a pulse: UnresolvedBoundary (the run stops); no pulse: SBP, DBP, MAP not measurable "
     "(None)", "OUTPUT_EPSILON (numerical, not clinical)", "P2D-2", "1e-9", STRUCTURAL, "common"),
)
FLOORS_CAPS_KNEES = {
    "before_p2j1": ["knee at p = 0.5 (low_output_pressure_knee, provisional): the slope of SBP and DBP changes there",
                    "max(0, .) on the linear branch (inactive for any arrival above 22.5 / 12.5 mmHg)",
                    "max(0, p) below the knee (p is never negative)", "no cap: linear above arrival, unbounded",
                    "T guard [0.1, 3.0] (a bound, recorded as a clamp when it acts)"],
    "since_p2j1": ["max(0, p) only (p is never negative: Q and T are)", "no knee, no floor, no cap",
                   "T guard [0.1, 3.0] (unchanged)", "afterload a < 1 (profile check): Q stays positive at any tone and "
                   "p rises with T", "Q <= 1e-9 with a pulse stops the run (unchanged)"],
}


def prior_pressures(rel: float, anchors: Anchors, gains: tuple = (45.0, 25.0), knee: float = 0.5) -> tuple:
    """The relation the core read until P2I-2AK (derived.arterial_pressures at 052d816), for the audit only."""
    def linear(value):
        return (max(0.0, anchors.sbp - gains[0] * (1.0 - value)), max(0.0, anchors.dbp - gains[1] * (1.0 - value)))
    if rel >= knee:
        return linear(rel)
    sbp_knee, dbp_knee = linear(knee)
    scale = max(0.0, rel) / knee
    return sbp_knee * scale, dbp_knee * scale


def current_pressures(rel: float, anchors: Anchors) -> tuple:
    return arterial_pressures(rel, anchors, DEFAULT_PROFILE)


def _map(pair: tuple) -> float:
    return (pair[0] + 2.0 * pair[1]) / 3.0


# 2. The knee, on fixed states (P2J-1-2) ----------------------------------------------------------------------------

GRID = tuple(round(0.002 * i, 3) for i in range(1001))   # p from 0 to 2
STEPS = (1e-5, 1e-6)     # one-sided slopes at two steps: a knee's gap stays, curvature's shrinks with the step
JUMP_STEP = 1e-10
SLOPE_TOLERANCE = 1e-4   # mmHg per unit of p: finite-difference noise only
MAPPING_RULE = (
    "Each mapping is read on p = 0 to 2 in steps of 0.002 and at the knee 0.5: DISCONTINUOUS if a value jumps (more "
    "than 1e-6 mmHg across 2e-10 around a point); CONTINUOUS_WITH_KNEE if the one-sided slopes differ by more than "
    "1e-4 mmHg per unit at a step of 1e-6 and the gap does not shrink to less than half of its size at 1e-5 (a "
    "kink; a smooth curve's gap shrinks with the step), anywhere inside (0, 2); OTHER if it is not "
    "non-decreasing, keeps a positive value at p = 0 or lets SBP fall below DBP; CONTINUOUS_AND_SMOOTH otherwise. "
    "The implicit resistance is MAP / (MAP_arrival x p): 1 everywhere means T is the only resistance.")


def classify_mapping(function, anchors: Anchors) -> dict:
    """Value and slope continuity, monotonicity, floor and the implicit resistance of a pressure mapping."""
    points = sorted(set(GRID) | {0.5})
    jumps, kinks, monotone, ordered = [], [], True, True
    previous = None
    for p in points:
        here = function(p, anchors)
        ordered = ordered and here[0] >= here[1] >= 0.0
        if previous is not None and (here[0] < previous[0] - 1e-12 or here[1] < previous[1] - 1e-12):
            monotone = False
        previous = here
        if 0.0 < p < 2.0:
            near_low, near_high = function(p - JUMP_STEP, anchors), function(p + JUMP_STEP, anchors)
            gaps = []
            for step in STEPS:
                low, high = function(p - step, anchors), function(p + step, anchors)
                gaps.append([((here[k] - low[k]) / step, (high[k] - here[k]) / step) for k in (0, 1)])
            for k in (0, 1):
                if abs(near_high[k] - near_low[k]) > 1e-6:
                    jumps.append([p, k])
                (left_wide, right_wide), (left, right) = gaps[0][k], gaps[1][k]
                if abs(right - left) > SLOPE_TOLERANCE and abs(right - left) > 0.5 * abs(right_wide - left_wide):
                    kinks.append({"p": p, "series": ("SBP", "DBP")[k], "left": left, "right": right})
    floor = max(function(0.0, anchors))
    label = ("DISCONTINUOUS" if jumps else "OTHER" if (not monotone or floor > 0.0 or not ordered)
             else "CONTINUOUS_WITH_KNEE" if kinks else "CONTINUOUS_AND_SMOOTH")
    arrival_map = (anchors.sbp + 2.0 * anchors.dbp) / 3.0
    resistance = {f"{p:g}": _map(function(p, anchors)) / (arrival_map * p) for p in (0.2, 0.3, 0.5, 0.75, 1.0, 1.5, 2.0)}
    return {"classification": label, "value_jumps": len(jumps), "kinks": kinks, "monotone": monotone,
            "value_at_zero": floor, "near_zero": max(function(1e-6, anchors)), "sbp_above_dbp": ordered,
            "implicit_resistance": resistance}


def _arrivals() -> dict:
    return {"GI 57m": gi_reference.canonical_anchors(C57), "GI 72f": gi_reference.canonical_anchors(C72),
            "neutral arrival": Anchors(**ARRIVAL)}


def knee_audit() -> dict:
    """The relation before P2J-1 and the current one, on each arrival (the knee, its slopes, the hidden tone)."""
    out = {}
    for name, anchors in _arrivals().items():
        prior = classify_mapping(prior_pressures, anchors)
        current = classify_mapping(lambda p, a: current_pressures(p, a), anchors)
        knee, step = 0.5, STEPS[1]
        above = [(prior_pressures(knee + step, anchors)[k] - prior_pressures(knee, anchors)[k]) / step for k in (0, 1)]
        below = [(prior_pressures(knee, anchors)[k] - prior_pressures(knee - step, anchors)[k]) / step for k in (0, 1)]
        arrival_map = (anchors.sbp + 2.0 * anchors.dbp) / 3.0
        out[name] = {"arrival": [anchors.sbp, anchors.dbp, arrival_map], "prior": prior, "current": current,
                     "prior_slopes_at_knee": {"SBP": {"below": below[0], "above": above[0], "ratio": below[0] / above[0]},
                                              "DBP": {"below": below[1], "above": above[1], "ratio": below[1] / above[1]}},
                     "prior_linear_intercept_map": arrival_map - (45.0 + 2.0 * 25.0) / 3.0,
                     "prior_narrow_pulse_limit_mmhg": (45.0 - 25.0) * (1.0 - knee),
                     "probes": {f"{p:g}": {"prior": list(prior_pressures(p, anchors)),
                                           "current": list(current_pressures(p, anchors))}
                                for p in (0.0, 1e-6, 0.1, 0.3, 0.49, 0.5, 0.51, 0.75, 1.0, 1.25, 1.5, 2.0)}}
    return out


def prior_matches_p2i2q() -> dict:
    """The replica of the prior relation against the committed P2I-2Q record (computed by the core before P2J-1)."""
    record = json.loads((ROOT / "docs" / "revision" / "P2I2Q_hemodynamic_probes.json").read_text(encoding="utf-8"))
    form = record["pressure_form"]
    worst = 0.0
    for name, anchors in _arrivals().items():
        arrival_map = (anchors.sbp + 2.0 * anchors.dbp) / 3.0
        for key, value in form[name]["implied_resistance"].items():
            p = float(key)
            worst = max(worst, abs(_map(prior_pressures(p, anchors)) / p / arrival_map - value))
        above = (prior_pressures(0.5 + 1e-6, anchors)[0] - prior_pressures(0.5, anchors)[0]) / 1e-6
        worst = max(worst, abs(above - form[name]["sbp_slope_above_knee"]) / 45.0)
    return {"max_difference": worst, "equal": worst < 1e-6}


# 3. Tone T, its paths, and the pump / tone coupling (P2J-1-4, P2J-1-5) ----------------------------------------------

TONE_RULE = (
    "Every read and write of the tone channel in clinical_core, found on the syntax tree: an attribute .T, a keyword "
    "T= (evolve), Channel.T, or a drift on channel \"T\". A writer outside a synthetic probe, a test or a bound is a "
    "clinical writer. T is relative systemic vascular resistance when it is the only resistance pressure reads "
    "(implicit resistance 1 everywhere) and it lowers output only through afterload; MIXED_CONSTRUCT when the "
    "pressure mapping carries a resistance of its own.")
#: Writers that are not clinical: synthetic probes, this module's probes, and the arrival value 1 (anchoring).
PROBE_MODULES = ("clinical_core/bands.py", "clinical_core/hemodynamic_probes.py", "clinical_core/pressure_tone.py")
ANCHORING = (("clinical_core/state.py", "anchored_state"),)


def tone_paths() -> dict:
    reads, writes = [], []
    for path in sorted((ROOT / "clinical_core").rglob("*.py")):
        relative = path.relative_to(ROOT).as_posix()
        for top in ast.parse(path.read_text(encoding="utf-8")).body:
            name = getattr(top, "name", "<module>")
            for node in ast.walk(top):
                if isinstance(node, ast.Attribute) and node.attr == "T":
                    target = writes if isinstance(node.ctx, ast.Store) else reads
                    kind = "Channel.T" if isinstance(node.value, ast.Name) and node.value.id == "Channel" else ".T"
                    target.append((relative, name, kind))
                elif isinstance(node, ast.keyword) and node.arg == "T":
                    writes.append((relative, name, "T="))
                elif isinstance(node, ast.Call) and any(isinstance(a, ast.Constant) and a.value == "T"
                                                       for a in node.args):
                    writes.append((relative, name, "drift on \"T\""))
    reads, writes = sorted(set(reads)), sorted(set(writes))
    clinical = [w for w in writes if w[0] not in PROBE_MODULES and (w[0], w[1]) not in ANCHORING]
    return {"reads": [list(r) for r in reads], "writes": [list(w) for w in writes],
            "clinical_writers": [list(w) for w in clinical], "rule": TONE_RULE}


TONES = (0.5, 0.75, 1.0, 1.5, 2.0, 3.0)
PUMPS = (0.1, 0.25, 0.5, 0.75, 1.0, 1.5)
VOLUME_SHARES = (-0.75, -0.5, 0.0, 0.5, 1.0)
AFTERLOAD = tuple(calibration.REGISTRY["afterload_sensitivity"].points())


def _read(state, anchors, profile) -> dict:
    view = derive(state, anchors, profile)
    return {"output": view.output_rel, "p": view.pressure_rel, "sbp": view.sbp, "dbp": view.dbp, "map": view.map}


def coupling_probes() -> dict:
    """P5, P6 and the P2J-1-5 coupling: fixed arrival preload and sinus rhythm, the canonical 57m arrival."""
    anchors = gi_reference.canonical_anchors(C57)
    base = anchored_state(anchors)
    p5 = {}
    for a in AFTERLOAD:
        profile = replace(DEFAULT_PROFILE, afterload_sensitivity=a)
        fixed_pump = {f"{t:g}": _read(base.evolve(T=t), anchors, profile) for t in TONES}
        # Fixed output: P chosen so that output stays the arrival's (P = 1 + a (T - 1)).
        fixed_output = {f"{t:g}": _read(base.evolve(T=t, P=1.0 + a * (t - 1.0)), anchors, profile) for t in TONES}
        p5[f"{a:g}"] = {"fixed_pump": fixed_pump, "fixed_output": fixed_output}
    p6 = {f"{t:g}": {f"{p:g}": _read(base.evolve(P=p, T=t), anchors, DEFAULT_PROFILE) for p in PUMPS}
          for t in (1.0, 2.0)}
    # V as shares of the arrival filling, so the emptiest probe keeps the ventricle filling.
    filling = arrival_filling(anchors, DEFAULT_PROFILE)
    p6["V at T 1"] = {f"{share:g} x filling": _read(base.evolve(V=share * filling), anchors, DEFAULT_PROFILE)
                      for share in VOLUME_SHARES}
    fp = p5[f"{DEFAULT_PROFILE.afterload_sensitivity:g}"]["fixed_pump"]
    coupling = {"tone_up": {"output_falls": fp["2"]["output"] < fp["1"]["output"],
                            "pressure_rises": fp["2"]["map"] > fp["1"]["map"]},
                "tone_down": {"output_rises": fp["0.5"]["output"] > fp["1"]["output"],
                              "pressure_falls": fp["0.5"]["map"] < fp["1"]["map"]},
                "pump_up": {"output_rises": p6["1"]["1.5"]["output"] > p6["1"]["1"]["output"],
                            "pressure_rises": p6["1"]["1.5"]["map"] > p6["1"]["1"]["map"]},
                "pressure_supremum_over_tone": 1.0 / DEFAULT_PROFILE.afterload_sensitivity}
    return {"anchors": C57, "P5": p5, "P6": p6, "coupling": coupling}


def zero_output_probe() -> dict:
    """P7: numerical zero with a pulse stops the run; small output gives a pressure near 0 at the tone bound; no pulse,
    no pressure."""
    anchors = gi_reference.canonical_anchors(C57)
    base = anchored_state(anchors)
    try:
        derive(base.evolve(P=OUTPUT_EPSILON / 10.0), anchors, DEFAULT_PROFILE)
        boundary = "MEASURED"
    except UnresolvedBoundary:
        boundary = "UNRESOLVED_BOUNDARY"
    small = {f"{p:g} at T {t:g}": _read(base.evolve(P=p, T=t), anchors, DEFAULT_PROFILE)
             for p in (1e-6, 1e-3, 0.05) for t in (1.0, 3.0)}
    pulseless = {}
    for name, rhythm in (("pea", RhythmState.pea(110.0)), ("asystole", RhythmState.asystole()), ("vf", RhythmState.vf())):
        view = derive(base.evolve(R=rhythm, terminal_since=0), anchors, DEFAULT_PROFILE)
        pulseless[name] = {"output": view.output_rel, "sbp": view.sbp, "dbp": view.dbp, "map": view.map,
                           "pulse": view.pulse_present}
    tiny = small["1e-06 at T 3"]
    return {"numerical_zero_with_pulse": boundary, "small_output": small, "pulseless": pulseless,
            "holds": boundary == "UNRESOLVED_BOUNDARY" and tiny["map"] < 1.0 and tiny["sbp"] < 1.0
            and all(v["sbp"] is None and v["map"] is None and v["output"] == 0.0 for v in pulseless.values())}


# 4. Authored pressures, arrival, normalization (P2J-1-6..8) ---------------------------------------------------------

def authored_pressures() -> dict:
    out = {}
    for case in CASES:
        items = {item.item: item for item in gi_reference.INVENTORY if item.case == case}
        out[case] = {"sbp": {"value": items["sbp"].value, "source": items["sbp"].source, "kind": AUTHORED},
                     "dbp": {"value": items["dbp"].value, "source": items["dbp"].source, "kind": AUTHORED},
                     "map": {"value": items["map"].value, "kind": DERIVED_FROM_AUTHORED,
                             "equation": "(SBP + 2 DBP) / 3"},
                     "later": sorted(name for name in items if name not in ("sbp", "dbp", "map")
                                     and any(word in name for word in ("bp", "pressure", "systolic", "diastolic"))),
                     "legacy": "LEGACY_REFERENCE: the family engine's pressure trajectories exist and are "
                                            "never read here"}
        out[case]["inventory_items"] = sorted(items)
    return out


def arrival_reconstruction() -> dict:
    """The retained arrival severity (P2I-2AJ) at demand 1.0 and 1.1: the derived arrival against the authored one."""
    out = {}
    for factor in DEMANDS:
        for case, pair in zip(CASES, ho.RETAINED):
            anchors = ho.anchors_at(case, "midpoint", pair, factor)
            view = derive(_arrival_state(anchors), anchors, hp.primary_profile())
            authored = (anchors.sbp, anchors.dbp, (anchors.sbp + 2.0 * anchors.dbp) / 3.0)
            out[f"{case} x{factor:g}"] = {
                "output": view.output_rel, "T": 1.0, "p": view.pressure_rel, "sbp": view.sbp, "dbp": view.dbp,
                "map": view.map, "authored": list(authored), "pair": list(pair),
                "mismatch": [view.sbp - authored[0], view.dbp - authored[1], view.map - authored[2]],
                "delivery_ratio": anchors.arrival_delivery_ratio, "D0": anchors.arrival_oxygen_debt}
    return out


def _arrival_state(anchors):
    return arrival_state(anchors, hp.primary_profile())


NORMALIZATION = (
    "Before P2J-1, MIXED: SBP and DBP in absolute mmHg, anchored on the authored arrival with absolute legacy gains, "
    "while p and the HR term are relative to arrival, and 1 - p did not equal the relative MAP deficit (the linear "
    "branch moved MAP by 31.7 mmHg per unit of p, about half of MAP_arrival). Since P2J-1, "
    "ABSOLUTE_MMHG_ANCHORED_ON_AUTHORED_ARRIVAL: SBP, DBP and MAP are absolute, clinically interpretable mmHg whose "
    "scale is the authored arrival pressure, and MAP / MAP_arrival = p exactly, so the relative pressure the HR term "
    "reads is the displayed MAP's deficit from arrival. No normal (euvolaemic) pressure is declared by either case, so "
    "none is invented: a baroreflex set point is a faculty number (BAROREFLEX_PLAN).")


# 5. The candidate surface, frozen before any trajectory (P2J-1-10) -------------------------------------------------

CANDIDATE_SURFACE = {
    "mapping": {"form": "SBP = SBP_arrival x p, DBP = DBP_arrival x p, p = output x T", "free_parameters": [],
                "status": "STRUCTURAL (the P2J-1 correction): no candidate"},
    "afterload_sensitivity": {"points": list(AFTERLOAD), "source": "calibration.REGISTRY band (P2G, provisional)",
                              "design": "one-dimensional, on the synthetic P5 probes only",
                              "reaches": "output and pressure only where T != 1"},
    "tone_reference": {"value": 1.0, "status": "the anchoring rule (proposal §7.4): T is 1 at arrival; not a candidate"},
    "tone_response": {"status": "NOT_AUTHORIZED: no mechanism writes T; a vascular-tone response needs new parameters "
                                "(gain, set point, time constant), whose ranges are the faculty's to authorize"},
    "pump": {"value": 1.0, "status": "no GI mechanism writes P; not a candidate"},
    "upstream": "the retained blood / fluid physiology (the P2I-2AJ / P2I-2AK lactate units at demand 1.0 and 1.1), "
                "carried as uncertainty, never reopened or refiltered",
}
RANGE_RULE = (
    "Built before any trajectory: the registered band of the only pressure-domain parameter left (afterload "
    "sensitivity 0.1 / 0.3 / 0.5, calibration.REGISTRY), its dimensional limit (a < 1, so output stays positive and "
    "pressure rises with tone), the authored arrival pressures as the mapping's scale and the synthetic probes. No GI "
    "trajectory and no legacy pressure is read to choose it. No hard pressure envelope exists beyond arrival, so no "
    "pressure filter is applied.")

# 6. Decision trajectories P1-P7 on the retained physiology (P2J-1-11) ---------------------------------------------

TRAJECTORY_RULE = (
    "Pressure reads output and tone only, and neither reads demand, D, lactate or HR (DEPENDENCY_RULE), so each "
    "trajectory is simulated once per blood set: P1 (L1) and P2 (L2, per crystalloid point) per P1 set, P3 (L3 with "
    "only the endoscopic haemostasis omitted) and P4 (L3) per P3 set, for every set the retained lactate units use at "
    "demand 1.0 or 1.1 (reproduced exactly from P2I-2AJ / P2I-2AK). Read at 0, 15, 30, 60, 90 and 120: output, T, "
    "SBP, DBP, MAP, pulse pressure and the intervention state, as LOW / median / HIGH over the blood sets; the same "
    "outputs read through the relation before P2J-1 give what changed. The effective deficit and D depend on the "
    "lactate side and the demand: they come from the validation sample's full runs (three units per demand), as "
    "context.")


def _median(values: list):
    ordered = sorted(values)
    return ordered[len(ordered) // 2]


def _spread(values: list):
    values = [v for v in values if v is not None]
    return {"low": min(values), "median": _median(values), "high": max(values), "n": len(values)} if values else None


def scenario_items(case: str, scenario: str, full: dict) -> tuple:
    if scenario == NO_HAEMOSTASIS:
        return tuple(i for i in lr.scenario_items(case, L3, full) if type(i).__name__ != "EndoscopicHemostasis")
    return lr.scenario_items(case, scenario, full)


def pressure_run(entry: dict, case: str, scenario: str, bag: dict | None = None) -> dict:
    """One blood set's trajectory, blood-side anchors only (as the P2I-2AB haemodynamic store builds them)."""
    values = lr.blood_values(entry, case, bag)
    anchors, profile, full = blood_anchors.setup(case, **values)
    states, stop = blood_anchors.trajectory(anchors, scenario_items(case, scenario, full), MINUTES, profile)
    return {"rows": _rows(states, anchors, profile, full), "stop": stop, "controlled_at": lr.controlled_at(states[-1]),
            "anchors": anchors}


def _rows(states, anchors, profile, full) -> list:
    unit = full.get("red_cell_unit_volume_ml")
    shed = [state.blood.shed_ml for state in states]
    flow = [after - before for before, after in zip(shed, shed[1:])]
    bleed = (flow[:1] or [0.0]) + flow
    rows = []
    for minute, state in enumerate(states):
        view = derive(state, anchors, profile)
        rows.append({"minute": minute, "pulse": view.pulse_present, "output": view.output_rel, "T": state.T,
                     "P": state.P, "p": view.pressure_rel, "sbp": view.sbp, "dbp": view.dbp, "map": view.map,
                     "pp": None if view.sbp is None else view.sbp - view.dbp, "hr": view.pulse_rate_bpm,
                     "D": state.D, "lactate": view.lactate, "rr": view.respiratory_rate,
                     "delivery_rel": view.delivery_rel, "demand": state.aux.oxygen_demand,
                     "bleed_ml_per_min": bleed[minute], "crystalloid_in_ml": state.blood.crystalloid_in_ml,
                     "prbc_units": state.blood.transfused_ml / unit if unit else 0.0})
    return rows


def full_run(entry: dict, case: str, scenario: str, factor: float, point: tuple, bag: dict | None = None,
             intrinsic: str = "midpoint", profile_changes: dict | None = None) -> dict:
    """hr_envelope_filter.full_run's construction (lactate side, arrival severity, demand factor, HR profile), with P3
    and the pressure readings."""
    tau_d, gain_k, k, tau_l, excess, debt, delivery = point
    values = {**lr.blood_values(entry, case, bag), "reserve": RESERVE}
    _, profile, full = blood_anchors.setup(case, **values)
    case_values = calibration.case_values(case, calibration.GICandidate({}, excess=excess, debt=debt,
                                                                        delivery=delivery, intrinsic=intrinsic))
    case_values["preload_fraction"] = full[bc.POS]
    case_values["arrival_delivery_ratio"] /= RESERVE
    case_values["metabolic_demand_baseline"] *= factor
    anchors = gi_reference.candidate_anchors(case, case_values)
    profile = replace(profile, debt_clearance_tau_min=tau_d, debt_per_delivery_deficit=gain_k, debt_to_lactate_gain=k,
                      lactate_clearance_tau_min=tau_l, **(profile_changes or {}))
    states, stop = blood_anchors.trajectory(anchors, scenario_items(case, scenario, full), MINUTES, profile)
    rows = _rows(states, anchors, profile, full)
    for row in rows:
        delivery_ = effective_delivery(row["delivery_rel"], anchors)
        row["deficit"] = effective_oxygen_deficit(row["demand"], delivery_, RESERVE)
    return {"rows": rows, "stop": stop, "controlled_at": lr.controlled_at(states[-1]), "anchors": anchors}


def blood_sets(units_by_demand: dict) -> dict:
    """The distinct blood sets the retained units use at either demand, per scenario and case."""
    sets = {"P1": set(), "P2": set(), "P3": set(), "P4": set()}
    for units in units_by_demand.values():
        for i, a, b, r, ds in units:
            sets["P1"].add(i)
            sets["P2"].update((i, d) for d in ds)
            sets["P3"].update(r)
            sets["P4"].update(r)
    return {name: sorted(values) for name, values in sets.items()}


def _pressure_task(task: tuple) -> tuple:
    key, entry, case, scenario, bag = task
    result = pressure_run(entry, case, scenario, bag)
    keep = ("minute", "pulse", "output", "T", "P", "p", "sbp", "dbp", "map", "pp", "bleed_ml_per_min",
            "crystalloid_in_ml", "prbc_units")
    return key, {"rows": [{name: row[name] for name in keep} for row in result["rows"]], "stop": result["stop"],
                 "controlled_at": result["controlled_at"], "arrival": [result["anchors"].sbp, result["anchors"].dbp]}


def pressure_tasks(source: dict, support: list, sets: dict) -> list:
    tasks = []
    for case in CASES:
        for i in sets["P1"]:
            tasks.append((("P1", case, i), source["p1"][i], case, L1, None))
        for i, d in sets["P2"]:
            tasks.append((("P2", case, (i, d)), source["p1"][i], case, L2, support[d]["bag"]))
        for q in sets["P3"]:
            tasks.append((("P3", case, q), source["p3"][q], case, NO_HAEMOSTASIS, None))
            tasks.append((("P4", case, q), source["p3"][q], case, L3, None))
    return tasks


def trajectory_table(runs: dict) -> dict:
    """LOW / median / HIGH at the reading times, per scenario and case, and what the relation before P2J-1 gives."""
    out = {}
    for name in SCENARIOS:
        for case in CASES:
            chosen = [run_ for (scenario, c, _), run_ in runs.items() if scenario == name and c == case]
            anchors = gi_reference.canonical_anchors(case)
            table = {}
            for minute in TIMES:
                rows = [run_["rows"][minute] for run_ in chosen if minute < len(run_["rows"])]
                prior = [_map(prior_pressures(row["p"], anchors)) for row in rows if row["pulse"]]
                table[str(minute)] = {
                    **{field: _spread([row[field] for row in rows])
                       for field in ("output", "T", "sbp", "dbp", "map", "pp", "bleed_ml_per_min",
                                     "crystalloid_in_ml", "prbc_units")},
                    "map_prior": _spread(prior),
                    "map_change": _spread([row["map"] - m for row, m in zip([r for r in rows if r["pulse"]], prior)])}
            controlled = sorted({run_["controlled_at"] for run_ in chosen}, key=lambda v: (v is None, v))
            out[f"{name} {case}"] = {"blood_sets": len(chosen), "stops": sum(run_["stop"] is not None for run_ in chosen),
                                     "controlled_at": controlled, "times": table}
    return out


def changed_outputs(runs: dict) -> dict:
    """Which modelled pressure outputs P2J-1 changed: the same outputs through both relations, every minute."""
    largest, unchanged_at_arrival, count = {"sbp": 0.0, "dbp": 0.0, "map": 0.0}, True, 0
    for (_, case, _), run_ in runs.items():
        anchors = gi_reference.canonical_anchors(case)
        for row in run_["rows"]:
            if not row["pulse"]:
                continue
            prior = prior_pressures(row["p"], anchors)
            for name, value in (("sbp", prior[0]), ("dbp", prior[1]), ("map", _map(prior))):
                largest[name] = max(largest[name], abs(row[name] - value))
            if row["minute"] == 0:
                unchanged_at_arrival = unchanged_at_arrival and abs(row["map"] - _map(prior)) < 1e-9
            count += 1
    return {"largest_change_mmhg": largest, "arrival_unchanged": unchanged_at_arrival, "minutes_compared": count,
            "changed": ["SBP", "DBP", "MAP", "pulse pressure", "consciousness (SBP thresholds 80 / 65)"],
            "unchanged": ["output", "T", "p", "BloodState", "V", "Hb", "delivery", "deficit", "D", "lactate", "RR",
                          "HR (the drive reads p, not SBP)", "CRT"]}


# 7. Directional invariants (P2J-1-12) ------------------------------------------------------------------------------

DIRECTIONS = {
    "1": "falling output at fixed T never raises MAP: P6 and every consecutive minute pair of every trajectory (T = 1)",
    "2": "rising output at fixed T never lowers MAP: the same pairs",
    "3": "more tone at fixed output never lowers MAP: P5 fixed-output probes, every afterload point",
    "4": "zero output never preserves a normal pressure: P7 (numerical zero with a pulse stops the run; MAP below "
         "1 mmHg at output 1e-6 even at the tone bound 3; no pulse, no pressure)",
    "5": "untreated haemorrhage never normalizes pressure on its own: P1, MAP never above the arrival MAP in minutes "
         "1-120, every blood set",
    "6": "effective resuscitation may improve pressure: P4, MAP at 120 above arrival on at least one blood set "
         "(reachability, counted)",
    "7": "haemostasis alone forces no instantaneous normalization: with h the minute the GI module records the source "
         "controlled (its step into h already bleeds at the residual rate), P4 equals P3 before h, and P4's MAP step "
         "into h is no larger than its largest one-minute step before h, every blood set; the haemostasis minute's own "
         "effect, MAP_P4(h) - MAP_P3(h), is reported",
    "8": "the pressure response to fluid or blood arises through physiology, not treatment identity: every minute "
         "MAP = MAP_arrival x output x T exactly, and arterial_pressures reads only p and the arrival anchors",
}


def _same_sign(rows) -> bool:
    for before, after in zip(rows, rows[1:]):
        if not (before["pulse"] and after["pulse"]) or after["T"] != before["T"]:
            continue
        dq, dm = after["output"] - before["output"], after["map"] - before["map"]
        if (dq < 0.0 < dm) or (dm < 0.0 < dq):
            return False
    return True


def directions(runs: dict, coupling: dict, zero: dict) -> dict:
    by, controlled = {}, {key: run_["controlled_at"] for key, run_ in runs.items()}
    for (name, case, unit), run_ in runs.items():
        by.setdefault(name, {})[(case, unit)] = run_["rows"]
    p6_monotone = all(
        all(b["map"] >= a["map"] for a, b in zip(list(series.values()), list(series.values())[1:]))
        for key, series in coupling["P6"].items())
    pairs = all(_same_sign(rows) for scenario in by.values() for rows in scenario.values())
    p5 = all(all(b["map"] >= a["map"] - 1e-12 for a, b in zip(list(v["fixed_output"].values()),
                                                              list(v["fixed_output"].values())[1:]))
             for v in coupling["P5"].values())
    untreated = [max(row["map"] for row in rows[1:] if row["pulse"]) <= rows[0]["map"] + 1e-12
                 for rows in by["P1"].values()]
    improved = [rows[-1]["map"] > rows[0]["map"] for rows in by["P4"].values()]
    seven, effect = [], []
    for (case, q), rows in by["P4"].items():
        twin, h = by["P3"][(case, q)], controlled[("P4", case, q)]
        prefix = all(rows[m] == twin[m] for m in range(h))
        steps = [abs(rows[m]["map"] - rows[m - 1]["map"]) for m in range(1, h)]
        seven.append(prefix and abs(rows[h]["map"] - rows[h - 1]["map"]) <= max(steps) + 1e-12)
        effect.append(rows[h]["map"] - twin[h]["map"])
    identity = True
    for (name, case, unit), run_ in runs.items():
        arrival_map = (run_["arrival"][0] + 2.0 * run_["arrival"][1]) / 3.0
        identity = identity and all(abs(row["map"] - arrival_map * row["output"] * row["T"]) <= 1e-9 * arrival_map
                                    for row in run_["rows"] if row["pulse"])
    reads = sorted({node.id for stmt in _function("clinical_core/derived.py", "arterial_pressures").body
                    for node in ast.walk(stmt) if isinstance(node, ast.Name)})
    return {
        "1": {"holds": pairs and p6_monotone, "pairs_checked": sum(len(r) - 1 for s in by.values() for r in s.values())},
        "2": {"holds": pairs and p6_monotone},
        "3": {"holds": p5},
        "4": {"holds": zero["holds"]},
        "5": {"holds": all(untreated), "blood_sets": len(untreated), "failing": untreated.count(False)},
        "6": {"reachable": any(improved), "improved": improved.count(True), "blood_sets": len(improved)},
        "7": {"holds": all(seven), "blood_sets": len(seven), "failing": seven.count(False),
              "haemostasis_minute": sorted(set(controlled[k] for k in controlled if k[0] == "P4")),
              "haemostasis_minute_effect_map": _spread(effect)},
        "8": {"holds": identity and set(reads) <= {"max", "pressure_rel", "anchors", "scale"}, "names_read": reads},
        "rule": DIRECTIONS}


def _function(relative: str, name: str):
    tree = ast.parse((ROOT / relative).read_text(encoding="utf-8"))
    return next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)


# 8. Identifiability (P2J-1-13) -------------------------------------------------------------------------------------

IDENTIFIABILITY = {
    "tone reference level": ("NON_IDENTIFIABLE", "T is 1 at arrival by the anchoring rule and no GI mechanism moves it: "
                                                 "any reference is absorbed by the authored arrival pressure"),
    "pressure mapping scale": ("WELL_CONSTRAINED", "by anchoring only: each case's authored arrival SBP and DBP, "
                                                   "exactly; the arrival reconstruction is exact by construction and no "
                                                   "later authored pressure exists, so the form beyond arrival is "
                                                   "untested"),
    "nonlinear shape / knee": ("NON_IDENTIFIABLE", "before P2J-1 the knee and the two gains had no authored pressure "
                                                   "off arrival to constrain them; since P2J-1 there is no shape "
                                                   "parameter"),
    "low-output parameter": ("NON_IDENTIFIABLE", "none remains: OUTPUT_EPSILON is numerical and the collapse rule is "
                                                 "off"),
    "afterload sensitivity": ("NON_IDENTIFIABLE", "reaches output and pressure only through T != 1, and T is 1 in "
                                                  "every GI scenario"),
    "pump / tone interaction": ("NON_IDENTIFIABLE", "P and T are 1 in every GI scenario; only the synthetic P5 / P6 "
                                                    "probes move them"),
}
IDENTIFIABILITY_RULE = (
    "WELL_CONSTRAINED: fixed by the observations; PARTIALLY_CONSTRAINED: narrowed, not fixed; POORLY_IDENTIFIED: "
    "several values fit; NON_IDENTIFIABLE: no observation reaches it. Two authored pressures (one per case, at arrival, "
    "where the model reproduces them by construction) are the only pressure observations. No best set is chosen.")

# 9. HR and demand propagation (P2J-1-14, P2J-1-15) -----------------------------------------------------------------

#: The derived.py functions on the path from the state to output, p and the pressures.
PRESSURE_PATH = ("_perfusion", "preload_position", "arrival_filling", "arrival_preload", "arterial_pressures")
#: What the pressure path must not read: demand, D, lactate, the drive, the sinus rate, the HR profile.
FORBIDDEN = ("oxygen_demand", "aux", "D", "sympathetic_drive", "rate_bpm", "beta_blockade", "intrinsic_sinus_rate",
             "metabolic_demand_baseline", "arrival_oxygen_debt", "arrival_delivery_ratio", "lactate",
             "acute_deficit_to_sympathetic_gain", "debt_to_sympathetic_gain", "sinus_rate_ceiling_bpm",
             "sympathetic_per_pressure_deficit")
DEPENDENCY_RULE = (
    "Code: the derived.py functions from the state to output, p and the pressures (PRESSURE_PATH) read none of "
    "FORBIDDEN, and no GI contributor reads a derived quantity. Numbers: on the validation sample (the first, middle "
    "and last retained unit at each demand, every scenario, both cases), full runs at demand 1.0 and 1.1, at the "
    "unit's lactate-side point and another, under the primary HR profile with its highest gains and ceiling 150, "
    "intrinsic upper, and under the default profile's diagnostic pressure term, give the blood-only run's output, p, "
    "SBP, DBP and MAP exactly, while D differs with demand.")


def path_reads() -> dict:
    names = set()
    for function in PRESSURE_PATH:
        for node in (n for stmt in _function("clinical_core/derived.py", function).body for n in ast.walk(stmt)):
            if isinstance(node, ast.Attribute):
                names.add(node.attr)
            elif isinstance(node, ast.Name):
                names.add(node.id)
    contributors = []
    for relative in ("clinical_core/modules/gi_haemorrhage.py", "clinical_core/interventions/fluids.py",
                     "clinical_core/interventions/modifiers.py", "clinical_core/interventions/timing.py",
                     "clinical_core/logistics.py"):
        tree = ast.parse((ROOT / relative).read_text(encoding="utf-8"))
        contributors += [relative for node in ast.walk(tree) if isinstance(node, ast.Name)
                         and node.id in ("derive", "_perfusion", "arterial_pressures", "delivery_rel_of")]
    return {"reads": sorted(names), "forbidden_read": sorted(names & set(FORBIDDEN)),
            "contributors_reading_derived": sorted(set(contributors))}


HR_VARIANTS = {
    "primary, highest gains, ceiling 150, intrinsic upper": (
        "upper", {**hp.PRIMARY_HR_CALIBRATION, "acute_deficit_to_sympathetic_gain": hp.ACUTE[-1],
                  "debt_to_sympathetic_gain": hp.DEBT[-1], "sinus_rate_ceiling_bpm": 150.0}),
    "default diagnostic pressure term, intrinsic lower": ("lower", {"sympathetic_per_pressure_deficit": 1.0}),
}
COMPARED = ("output", "p", "sbp", "dbp", "map", "T")


def sample_units(units_by_demand: dict) -> list:
    out = []
    for factor in DEMANDS:
        units = units_by_demand[factor]
        for index in sorted({0, len(units) // 2, len(units) - 1}):
            out.append((factor, units[index]))
    return out


def validate(source: dict, support: list, units_by_demand: dict, runs: dict) -> dict:
    """The dependency proof and the deficit / D context, on the validation sample."""
    equal, d_moves, checked, context = True, False, 0, {}
    for factor, (i, a, b, r, ds) in sample_units(units_by_demand):
        q, d = r[0], ds[0]
        for case, index in ((C57, a), (C72, b)):
            other = LAMBDAS[(index + 1) % len(LAMBDAS)]
            for name, scenario, entry, bag, key in (("P1", L1, source["p1"][i], None, i),
                                                    ("P2", L2, source["p1"][i], support[d]["bag"], (i, d)),
                                                    ("P3", NO_HAEMOSTASIS, source["p3"][q], None, q),
                                                    ("P4", L3, source["p3"][q], None, q)):
                reference = runs[(name, case, key)]["rows"]
                variants = [full_run(entry, case, scenario, f, LAMBDAS[index], bag) for f in DEMANDS]
                variants.append(full_run(entry, case, scenario, factor, other, bag))
                for intrinsic, changes in HR_VARIANTS.values():
                    variants.append(full_run(entry, case, scenario, factor, LAMBDAS[index], bag, intrinsic, changes))
                for variant in variants:
                    checked += 1
                    equal = equal and all(row[f] == ref[f] for row, ref in zip(variant["rows"], reference)
                                          for f in COMPARED) and len(variant["rows"]) == len(reference)
                d_moves = d_moves or any(x["D"] != y["D"] for x, y in zip(variants[0]["rows"], variants[1]["rows"]))
                at = variants[DEMANDS.index(factor)]["rows"]
                slot = context.setdefault(f"{name} {case} x{factor:g}", {str(m): {"deficit": [], "D": []} for m in TIMES})
                for minute in TIMES:
                    slot[str(minute)]["deficit"].append(at[minute]["deficit"])
                    slot[str(minute)]["D"].append(at[minute]["D"])
    context = {key: {m: {f: _spread(v) for f, v in item.items()} for m, item in value.items()}
               for key, value in context.items()}
    return {"pressure_equal": equal, "d_moves_with_demand": d_moves, "full_runs": checked,
            "sample": [[f, list(u[:3])] for f, u in sample_units(units_by_demand)], "context": context,
            "rule": DEPENDENCY_RULE}


# 10. The baroreflex reconnection plan (P2J-1-16): a plan, nothing reconnected ---------------------------------------

BAROREFLEX_PLAN = {
    "status": "PLAN_ONLY: pressure -> HR stays PRESSURE_TERM_DIAGNOSTIC_ONLY in P2J-1",
    "signal": "the absolute MAP the pressure domain derives (mmHg, anchored on the authored arrival) against a set point "
              "the faculty sets, max(0, MAP_set - MAP) / MAP_set; not the arrival-relative 1 - p",
    "sign": "the drive rises as MAP falls below the set point and is 0 at or above it; never negative (P2D-3), so no "
            "baroreflex bradycardia without an explicit source that changes R",
    "current_term": "1 - p should not survive as it is: relative to arrival, it reads 0 at a hypotensive arrival "
                    "(88 / 54 is its zero), it goes negative above arrival and offsets the other stimuli in the sum, "
                    "and until P2J-1 it disagreed with the displayed MAP by a factor of about two (since P2J-1 it is "
                    "the displayed MAP's relative deficit from arrival exactly)",
    "double_counting": "the acute oxygen-deficit signal and a pressure deficit both fall with output (correlation 0.75, "
                       "P2I-2AF): the pressure term reads pressure (MAP) and the acute term oxygen availability; the "
                       "acute gain is re-explored jointly with the baroreflex gain on the same arrival surface and "
                       "their shared variance reported; the term is never added on top of the current acute region",
    "repeat": ["the arrival HR window +-5 bpm (P2I-2AI / P2I-2AJ)", "A untreated 57m 124-160 at 120",
               "B untreated 72f 112-150 at 120", "C unit-1 benefit >= 0", "D unit-2 benefit >= 0",
               "E HR_120 <= HR_90 <= HR_60 with adequacy from 60", "F 0 <= HR_120 - intrinsic <= 15"],
    "requires": "faculty pressure envelopes first; then a set point and a gain range authorized before any value",
}

# 11. The verdict (P2J-1-17) ----------------------------------------------------------------------------------------

READY = "PRESSURE_STRUCTURE_READY_FOR_NUMERIC_FACULTY_CALIBRATION"
NOT_READY = "PRESSURE_STRUCTURE_NOT_READY"
VERDICT_RULE = (
    "READY when the pressure mapping is CONTINUOUS_AND_SMOOTH, non-decreasing, 0 at 0 and with implicit resistance 1; "
    "T's paths are enumerated and it has no clinical writer; zero output and arrest hold (P7); no floor or knee "
    "remains; the arrival reconstruction is available for both cases; the candidate surface is the frozen one, with "
    "every afterload point below 1 and admissible on the P5 probes; the upstream physiology is unchanged (the lactate "
    "units reproduce P2I-2AK's digests, derived.py and shadow.py are P2I-2AK's outside the statements P2J-1 declares, "
    "pressure equals across demand, lactate side and HR profile); HR feedback stays deferred "
    "(the primary profile's pressure term 0); and directions 1-5, 7 and 8 hold. Otherwise NOT_READY with the first "
    "failing check as the blocker.")
POLICY = ("Shadow only. P2I-2AK's committed record and the P2I-2AJ / P2I-2AK machinery; legacy pressure never read "
          "(no shadow, legacy adapter or family-engine import), the P2F region never consumed (P2FGuard), no hard "
          "pressure envelope, nothing approved or selected, pressure -> HR not reconnected.")


def outside_digest(relative: str, text: str | None = None) -> str:
    """The AST dump digest of every top-level statement of a P2J-1-changed file but the ones P2J-1 changed."""
    changed = P2J1_CHANGES[relative]["changed"]
    tree = ast.parse(text if text is not None else (ROOT / relative).read_text(encoding="utf-8"))

    def kept(node):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            return node.name not in changed
        return not any(isinstance(n, ast.Name) and n.id in changed for n in ast.walk(node))
    return hashlib.sha256("\n".join(ast.dump(n) for n in tree.body if kept(n)).encode("utf-8")).hexdigest()


def outside_unchanged() -> dict:
    return {relative: outside_digest(relative) == item["outside"] for relative, item in P2J1_CHANGES.items()}


def pressure_only_sources(sources: dict) -> dict:
    """An earlier package's dependency sources with each P2J-1-changed file at its P2I-2AK hash, when P2J-1 changed
    only the declared statements there (the rest of its syntax tree is P2I-2AK's); a file changed elsewhere keeps its
    live hash, so that guard fails."""
    out = dict(sources)
    for relative, item in P2J1_CHANGES.items():
        if relative in out and outside_digest(relative) == item["outside"]:
            out[relative] = item["sha_at_p2i2ak"]
    return out


def p2i2ak_record() -> dict:
    record = json.loads(P2I2AK_RECORD.read_text(encoding="utf-8"))
    if record["freeze_digest"] != P2I2AK_DIGEST or record["verdict"]["verdict"] != hf.READY:
        raise AssertionError("the P2I-2AK record is not the committed one")
    return record


def _tone_admissible(point: dict) -> bool:
    """At one afterload point: output falls with tone at a fixed pump, pressure rises with tone at a fixed output."""
    pump, output = list(point["fixed_pump"].values()), list(point["fixed_output"].values())
    return (all(b["output"] < a["output"] for a, b in zip(pump, pump[1:]))
            and all(b["map"] > a["map"] for a, b in zip(output, output[1:])))


def verdict(audit: dict, tone: dict, coupling: dict, zero: dict, arrival: dict, reuse: dict, dependency: dict,
            path: dict, invariants: dict) -> dict:
    current = [item["current"] for item in audit.values()]
    checks = {
        "mapping_coherent": all(c["classification"] == "CONTINUOUS_AND_SMOOTH" and c["monotone"] and c["value_at_zero"]
                                == 0.0 and all(abs(v - 1.0) < 1e-12 for v in c["implicit_resistance"].values())
                                for c in current),
        "tone_semantics_explicit": bool(tone["reads"]) and not tone["clinical_writers"],
        "zero_output_consistent": zero["holds"],
        "no_floor_or_knee": all(not c["kinks"] and not c["value_jumps"] and c["value_at_zero"] == 0.0 for c in current),
        "arrival_reconstruction_available": len(arrival) == len(CASES) * len(DEMANDS)
                                            and all(max(map(abs, r["mismatch"])) < 1e-9 for r in arrival.values()),
        "candidate_surface_explicit": bool(AFTERLOAD) and all(a < 1.0 for a in AFTERLOAD)
                                      and not CANDIDATE_SURFACE["mapping"]["free_parameters"]
                                      and all(_tone_admissible(v) for v in coupling["P5"].values()),
        "upstream_unchanged": reuse["units_equal"] and all(reuse["outside_unchanged"].values())
                              and dependency["pressure_equal"] and not path["forbidden_read"]
                              and not path["contributors_reading_derived"],
        "hr_feedback_deferred": hp.PRIMARY_HR_CALIBRATION == {"sympathetic_per_pressure_deficit": 0.0}
                                and hp.primary_profile().sympathetic_per_pressure_deficit == 0.0,
        "directions_hold": all(invariants[k]["holds"] for k in ("1", "2", "3", "4", "5", "7", "8")),
    }
    failing = [name for name, ok in checks.items() if not ok]
    return {"verdict": READY if not failing else f"{NOT_READY} — {failing[0]}", "checks": checks,
            "blockers": failing, "approved": [], "rule": VERDICT_RULE}


# 12. Freeze, run, CLI ----------------------------------------------------------------------------------------------

def design() -> dict:
    return {"faculty": FACULTY, "equations": [list(e) for e in EQUATIONS], "floors_caps_knees": FLOORS_CAPS_KNEES,
            "mapping_rule": MAPPING_RULE, "grid": [GRID[0], GRID[-1], len(GRID)], "tone_rule": TONE_RULE,
            "tones": list(TONES), "pumps": list(PUMPS), "volume_shares": list(VOLUME_SHARES), "afterload": list(AFTERLOAD), "normalization": NORMALIZATION,
            "candidate_surface": CANDIDATE_SURFACE, "range_rule": RANGE_RULE, "scenarios": SCENARIOS,
            "times": list(TIMES), "trajectory_rule": TRAJECTORY_RULE, "directions": DIRECTIONS,
            "identifiability": IDENTIFIABILITY, "identifiability_rule": IDENTIFIABILITY_RULE,
            "pressure_path": list(PRESSURE_PATH), "forbidden": list(FORBIDDEN), "dependency_rule": DEPENDENCY_RULE,
            "hr_variants": {k: [v[0], v[1]] for k, v in HR_VARIANTS.items()}, "baroreflex_plan": BAROREFLEX_PLAN,
            "verdict_rule": VERDICT_RULE, "policy": POLICY, "units": UNITS, "p2j1_changes": P2J1_CHANGES}


def freeze_digest() -> str:
    text = json.dumps({"revision": REVISION, "p2i2ak": hashlib.sha256(P2I2AK_RECORD.read_bytes()).hexdigest(),
                       "design": design(), "sources": bf.freeze_sources()}, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run(progress=None, map_=map) -> dict:
    say = progress or (lambda *_: None)
    with lr.P2FGuard(), lr.LegacyLock():
        p2i2ak_record()
        out = {"freeze_digest": freeze_digest(), "decided": DECIDED, "revision": REVISION, "policy": POLICY,
               "faculty": FACULTY, "record": P2I2AK_DIGEST}
        say("audit")
        audit = knee_audit()
        tone, coupling, zero = tone_paths(), coupling_probes(), zero_output_probe()
        arrival, path = arrival_reconstruction(), path_reads()
        out.update({"equations": [list(e) for e in EQUATIONS], "floors_caps_knees": FLOORS_CAPS_KNEES,
                    "knee": audit, "prior_matches_p2i2q": prior_matches_p2i2q(), "tone": tone, "coupling": coupling,
                    "zero_output": zero, "authored": authored_pressures(), "arrival": arrival,
                    "normalization": NORMALIZATION, "path": path})
        say("haemodynamics")
        source_record = la.record_p2i2ab()
        source, support = la.source_space(source_record), source_record["crystalloid_support"]
        arrivals = lr.arrival_table()
        tasks = lc.haemodynamic_tasks(source, support)
        store = lc.haemodynamics(tasks, map_)
        units_by_demand, digests = {}, {}
        for factor in DEMANDS:
            say(f"units x{factor:g}")
            region = ho.retained_region(source, support, arrivals, tasks, store, factor, map_)
            units_by_demand[factor], digests[f"{factor:g}"] = region["units"], region["digest"]
        reuse = {"units_digests": digests, "units_equal": all(digests[f"{f:g}"] == UNITS[f] for f in DEMANDS),
                 "outside_unchanged": outside_unchanged(),
                 "haemodynamic_trajectories": len(set(tasks.values()))}
        if not reuse["units_equal"]:
            raise AssertionError("the retained lactate units are not P2I-2AK's")
        sets = blood_sets(units_by_demand)
        say("pressure trajectories")
        runs = dict(map_(_pressure_task, pressure_tasks(source, support, sets)))
        say("validation")
        dependency = validate(source, support, units_by_demand, runs)
        invariants = directions(runs, coupling, zero)
        out.update({"reuse": reuse, "blood_sets": {k: len(v) for k, v in sets.items()},
                    "trajectories": trajectory_table(runs), "changed": changed_outputs(runs), "dependency": dependency,
                    "directions": invariants, "candidate_surface": CANDIDATE_SURFACE, "range_rule": RANGE_RULE,
                    "identifiability": IDENTIFIABILITY, "identifiability_rule": IDENTIFIABILITY_RULE,
                    "baroreflex_plan": BAROREFLEX_PLAN,
                    "efficiency": {"pressure_runs": len(runs), "validation_full_runs": dependency["full_runs"],
                                   "haemodynamic_trajectories": reuse["haemodynamic_trajectories"],
                                   "pressure_runs_without_sharing": _without_sharing(units_by_demand),
                                   "cartesian_sweep": False, "legacy_read": False}})
        out["verdict"] = verdict(audit, tone, coupling, zero, arrival, reuse, dependency, path, invariants)
    return out


def _without_sharing(units_by_demand: dict) -> int:
    """Runs a per-candidate design would need: every row (P3 set x crystalloid point x lactate-side point) at each
    demand, its own four trajectories per case."""
    return sum(len(CASES) * len(SCENARIOS) * len(r) * len(ds) for units in units_by_demand.values()
               for _, _, _, r, ds in units)


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
        path = args.out / "pressure_tone.json"
        path.write_text(json.dumps(run(print), indent=1, sort_keys=True, default=str), encoding="utf-8")
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
