"""Phase 2 shadow core, P2J-4: the direct baroreflex reconnected and the whole-patient HR recertified.

    python -m clinical_core.baroreflex --digest
    python -m clinical_core.baroreflex --design
    python -m clinical_core.baroreflex --run --out <directory outside the repository>

Shadow only and offline (faculty brief of 2026-10-30, recorded in FACULTY). The core gains a direct baroreflex
(derived.baroreflex_drive): baroreflex_to_sympathetic_gain x max(0, (MAP_set - MAP) / MAP_set) on the MAP the state
resolves, added to the sympathetic target after the acute-deficit, debt, hypoxaemia and hypoglycaemia terms: 0 at or
above MAP_set, never negative. The relative-pressure term (1 - pressure_rel) stays at 0 in every primary HR profile and
the core refuses both together. Off by default (gain 0, no MAP_set): the golden changes only by PARAMETERS entries.

Frozen here before any survivor count: the signal and its causal timing (ACYCLIC_SAME_STEP), the MAP_set (80 / 90 /
100 mmHg) and gain (0 reference; 0.25 / 0.5 / 1 / 1.5) candidates, the carried pressure / tone region (P2J-3: g 0.25 /
0.5 / 1 at a = 0.3, demand 1.0 and 1.1), P2I-2AK's surviving latent HR combinations, the arrival +-5 rule and
P2I-2AK's HR rules A-F unchanged, the filter order and rejection classes, the structural probes, the double-counting
classes, the non-regression checks, identifiability, verdict and recommendation rules. HR is rebuilt from each run's own
rows (hr_shock.hr_series' arithmetic plus derived.baroreflex_drive) and checked against the core's own HR; the legacy
HR and BP are never read; nothing is approved.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import statistics
from dataclasses import replace
from pathlib import Path

from . import blood_anchors
from . import blood_fluid_calibration as bf
from . import hr_envelope_filter as hf
from . import hr_observables as ho
from . import hr_primary as hp
from . import hr_structure as hs
from . import lactate_adequacy as la
from . import lactate_closure as lc
from . import lactate_rebuild as lr
from . import pressure_tone as pt
from . import pressure_tone_filter as pf
from . import vascular_tone as vt
from .derived import (DEFAULT_PROFILE, acute_deficit_signal, arrival_state, baroreflex_drive, baroreflex_signal, derive,
                      mean_arterial_pressure, sympathetic_target)
from .state import CoreInvariantError, RhythmCode

DECIDED = "2026-10-30"
REVISION = "P2J-4"
ROOT = pf.ROOT
CASES = pf.CASES
C57, C72 = pf.C57, pf.C72
L1, L3, CF1, CF2 = pf.L1, pf.L3, pf.CF1, pf.CF2
MINUTES = pf.MINUTES
DEMANDS = pf.DEMANDS
LAMBDAS = pf.LAMBDAS
RESERVE = vt.RESERVE
P2J3_RECORD = ROOT / "docs" / "revision" / "P2J3_pressure_tone_filter.json"
P2J3_DIGEST = "611e1702d44d97ec19c42a78ab1bf1f97de8f0001ec6eb148ed376990ebf2d28"
P2I2AK_RECORD = ROOT / "docs" / "revision" / "P2I2AK_hr_envelope_filter.json"
P2I2AK_DIGEST = "31f092650ee73ff4134fc9e5cc79b3a171fb7bb54de553fc2a7de2081f309dc3"

FACULTY = {
    "decided": DECIDED,
    "region": "P2J-3 accepted (PRESSURE_TONE_OBSERVABLE_FILTER_SATISFIED); its primary region carried as the current "
              "primary uncertainty: tone gain g 0.25 / 0.5 / 1.0, afterload a = 0.3 provisional, demand 1.0 and 1.1; "
              "none FACULTY_APPROVED; g 1.5 / 2.0 never in the primary baroreflex surface; g and a not further "
              "identified in this package",
    "signal": "MAP is the pressure signal: baroreflex_signal = max(0, (MAP_set - MAP) / MAP_set); 0 at or above "
              "MAP_set, positive below it, approaching 1 as MAP approaches 0, never negative (unlike the old "
              "1 - relative_pressure term, which could go negative and cancel acute / debt drive)",
    "contribution": "baroreflex_drive = baroreflex_to_sympathetic_gain x baroreflex_signal, added to the sympathetic "
                    "target alongside the acute effective-deficit and the accumulated-debt drives; never derived from "
                    "tau_D, the tone gain, the acute-deficit gain, the arrival HR or the legacy HR",
    "map_set": "80 / 90 / 100 mmHg: exploratory common physiological reference candidates; not case-specific, "
               "individualized, approved or fitted to the arrival pressures; no value added after outcomes",
    "gain": "0 DIAGNOSTIC_NO_BAROREFLEX_REFERENCE; 0.25 / 0.5 / 1.0 / 1.5 primary exploratory support; none approved; "
            "the range is not extended after outcomes",
    "timing": "the baroreflex at minute t reads the pressure already resolved at t and adds to HR without changing "
              "pressure in that step; no algebraic pressure <-> HR loop; if HR fed output or pressure the package "
              "stops",
    "orthogonality": "structural probes A-D before any clinical evaluation; no numeric gain approval from them",
    "double_counting": "clinical audit (correlation, joint and single positivity, contribution shares, ranking "
                       "changes); correlation is not rejected by itself; STRUCTURALLY_DISTINCT_BUT_CORRELATED / "
                       "FUNCTIONALLY_REDUNDANT_IN_CURRENT_CASES / PATHOLOGICAL_DOUBLE_COUNTING with no correlation "
                       "threshold",
    "old_term": "the 1 - relative_pressure contribution (PRESSURE_TERM_DIAGNOSTIC_ONLY) never active together with the "
                "baroreflex; retired from the primary HR physiology; no duplicate pressure signals",
    "latent": "only P2I-2AK's surviving latent HR combinations, demand 1.0 and 1.1 separately; the HR grid is not "
              "reopened; no combination selected",
    "arrival": "authored minute-0 HR 57m 124 and 72f 112 bpm, +-5 bpm, no residual offset, no wider tolerance, no "
               "case-specific MAP_set or gain, no change of the intrinsic grid; all candidates failing arrival stops "
               "with BAROREFLEX_INCOMPATIBLE_WITH_ARRIVAL_HR",
    "hr_rules": "P2I-2AK A-F repeated unchanged for every arrival-compatible candidate",
    "pressure": "P2J-3 A-I must not change (HR feeds no pressure or output); any change stops the package",
    "upstream": "BloodState, output, pressure, DO2, effective deficit, D, lactate and RR unchanged exactly",
    "scope": "shadow only; no runtime integration, GI or second-family migration, final baroreflex or HR latent "
             "approval, RR calibration, consciousness recalibration, collapse activation or legacy fitting",
}

# 1. The signal, the timing and the retired term --------------------------------------------------------------------

SIGNAL = ("baroreflex_signal = max(0, (MAP_set - MAP) / MAP_set), MAP = (SBP + 2 DBP) / 3 of the state as derive "
          "reports it (derived.mean_arterial_pressure, derived.baroreflex_signal); baroreflex_drive = "
          "baroreflex_to_sympathetic_gain x signal (derived.baroreflex_drive), added to the sympathetic target after "
          "the other terms; the target stays max(0, ...) and the drive keeps the common rise-at-once / tau 5 min decay")
TIMING = "ACYCLIC_SAME_STEP"
TIMING_RULE = (
    "integration.step resolves every channel of minute t (blood, V, Hb, P, T, D) and the auxiliary lactate and demand, "
    "then sets the drive from sympathetic_target on that end state: the baroreflex reads MAP(t) of the same state "
    "derive reports at t, and HR(t) = intrinsic + saturated increment of drive(t). _perfusion (output, pressure, "
    "delivery) and every contributor read no drive and no HR, so HR(t) never reaches pressure at t or later: no "
    "algebraic loop, no solver, no added lag. The drive's existing memory (rises at once, decays with tau 5 min, "
    "KD-S2) is common to all its terms, not a baroreflex time constant.")
OLD_TERM = "RETIRED_FROM_PRIMARY_HR"
OLD_TERM_RULE = (
    "Every P2J-4 profile carries hr_primary.PRIMARY_HR_CALIBRATION (sympathetic_per_pressure_deficit = 0), and the core "
    "refuses a profile with a baroreflex gain and a non-zero relative-pressure gain (CoreProfile). The common default "
    "keeps 1.0 with the baroreflex off, so the shadow baseline and the goldens stay identical; it never meets the "
    "baroreflex.")

# 2. The frozen candidates ------------------------------------------------------------------------------------------------

MAP_SETS = (80.0, 90.0, 100.0)
MAP_SET_STATUS = "EXPLORATORY_COMMON_REFERENCE"
REFERENCE_BARO = 0.0
PRIMARY_BARO = (0.25, 0.5, 1.0, 1.5)
BARO_STATUS = {0.0: "DIAGNOSTIC_NO_BAROREFLEX_REFERENCE", **{k: "PRIMARY_EXPLORATORY_SUPPORT" for k in PRIMARY_BARO}}
REFERENCE_POINT = (None, REFERENCE_BARO)
PRIMARY_POINTS = tuple((m, k) for m in MAP_SETS for k in PRIMARY_BARO)
POINTS = (REFERENCE_POINT, *PRIMARY_POINTS)
TONE_GAINS = pf.PRIMARY_GAINS
AFTERLOAD = pf.PRIMARY_A
EXCLUDED_TONE = (1.5, 2.0)
SCENARIOS = (L1, L3, CF1, CF2)
MINUTES_REPORTED = (0, 15, 30, 60, 90, 120)
CARRIED = {"tone_gain": list(TONE_GAINS), "afterload": AFTERLOAD, "demand": list(DEMANDS), "approved": []}

# 3. Rules, order and classes ---------------------------------------------------------------------------------------------

ORDER = ("SUPPORT", "DOMAIN", "SIMULATION", "ARRIVAL", "A", "B", "F", "E", "C", "D")
RULES = ORDER[1:]
REJECTION_CLASS = {"SUPPORT": "HR_PRIOR_REGION_REJECTION", "DOMAIN": "DOMAIN_REJECTION",
                   "SIMULATION": "SIMULATION_REJECTION", "ARRIVAL": "BAROREFLEX_REJECTION",
                   **{name: "HR_ENVELOPE_REJECTION" for name in ("A", "B", "F", "E", "C", "D")}}
ARRIVAL = {case: {"authored": hp.AUTHORED[case], "low": hp.WINDOWS[case][0], "high": hp.WINDOWS[case][1]}
           for case in CASES}
ENVELOPES = hf.ENVELOPES
CANDIDATE_RULE = (
    "A candidate row is (tone gain g, demand, lactate survivor of P2J-3's primary filter at that g and demand, "
    "P2I-2AK surviving latent HR combination at that demand, baroreflex point (MAP_set, gain)). Its rules read L1, L3 "
    "and L3's two counterfactuals, which depend on the P3 set and the two cases' lactate-side points only, so a row's "
    "verdict is its (P3 set, 57m point, 72f point) HR unit's verdict; rows are counted with that multiplicity. "
    "SUPPORT is the latent region (combinations outside P2I-2AK's survivors never enter; counted per combination). "
    "DOMAIN is analytic (MAP_set > 0, gain >= 0, ceiling above both intrinsic rates, g primary, a = 0.3, the profile "
    "constructible); SIMULATION a run that stops or an HR missing; ARRIVAL the authored +-5 window for both cases "
    "(BAROREFLEX_REJECTION: every entering combination is arrival-compatible without the baroreflex, P2I-2AK); A-F "
    "hr_envelope_filter.failures unchanged. Every rule is read for every row; the first failure in ORDER is counted, "
    "every failure too.")
EMPTY_RULE = (
    "When no row survives ARRIVAL at any primary baroreflex point, demand and tone gain, the package stops with "
    "BAROREFLEX_INCOMPATIBLE_WITH_ARRIVAL_HR (A-F still read, for the record). When rows pass ARRIVAL but none passes "
    "A-F, NOT_READY with NO_PRIMARY_SURVIVOR (the 'widespread failure of the certified HR A-F').")

# 4. Structural probes (P2J-4-2) --------------------------------------------------------------------------------------------

PROBE_MAP_SET = 100.0
PROBE_GAINS = {"acute": 1.0, "debt": 0.01, "baro": 1.0}
LOW, HIGH = (72.0, 44.0), (150.0, 100.0)
PROBES = {
    "A": {"what": "low MAP, effective deficit 0", "sbp_dbp": LOW, "demand": 1.0, "expect": "acute 0, baroreflex > 0"},
    "B": {"what": "MAP >= MAP_set, effective deficit > 0", "sbp_dbp": HIGH, "demand": 4.0,
          "expect": "baroreflex 0, acute > 0"},
    "C": {"what": "low MAP, effective deficit > 0", "sbp_dbp": LOW, "demand": 4.0, "expect": "both may be positive"},
    "D": {"what": "MAP >= MAP_set, effective deficit 0", "sbp_dbp": HIGH, "demand": 1.0, "expect": "both 0"},
}
PROBE_RULE = (
    "Synthetic arrival states, structural only (no gain read from them): the neutral arrival (demand met, tone 1) with "
    "its authored pressure set to 72/44 (MAP 53) or 150/100 (MAP 117) mmHg and its demand 1 or 4 times the baseline, at "
    "a synthetic profile (reserve 2.5, acute 1, debt 0.01, baroreflex 1, relative pressure 0) and every MAP_set "
    "candidate (PROBE_MAP_SET for the expected classes). Each probe reads the acute drive (gain x "
    "acute_deficit_signal), the baroreflex drive (derived.baroreflex_drive) and the core target (sympathetic_target), "
    "which must equal their sum. Nothing writes T. A also serves as B6 (isolated hypotension), B as B7 (isolated "
    "oxygen deficit).")


def _probe_profile(map_set: float):
    return replace(DEFAULT_PROFILE, oxygen_extraction_reserve=RESERVE, sympathetic_per_pressure_deficit=0.0,
                   acute_deficit_to_sympathetic_gain=PROBE_GAINS["acute"], debt_to_sympathetic_gain=PROBE_GAINS["debt"],
                   baroreflex_to_sympathetic_gain=PROBE_GAINS["baro"], baroreflex_map_set_mmhg=map_set)


def probe(name: str, map_set: float = PROBE_MAP_SET) -> dict:
    spec = PROBES[name]
    sbp, dbp = spec["sbp_dbp"]
    anchors, profile = replace(vt.NEUTRAL, sbp=sbp, dbp=dbp), _probe_profile(map_set)
    start = arrival_state(anchors, profile)
    state = start.evolve(aux=replace(start.aux, oxygen_demand=spec["demand"] * anchors.metabolic_demand_baseline))
    view = derive(state, anchors, profile)
    view_map = mean_arterial_pressure(view.pressure_rel, anchors, profile)
    if view_map != view.map:
        raise AssertionError("the baroreflex MAP is not the MAP derive reports")
    acute = profile.acute_deficit_to_sympathetic_gain * acute_deficit_signal(state, anchors, profile)
    baro = baroreflex_drive(view.pressure_rel, anchors, profile)
    target = sympathetic_target(state, anchors, profile)
    return {"map": view_map, "map_set": map_set, "signal": baroreflex_signal(view_map, map_set),
            "acute_drive": acute, "baroreflex_drive": baro, "debt_drive": profile.debt_to_sympathetic_gain * state.D,
            "target": target, "sum_equal": abs(target - (acute + baro + profile.debt_to_sympathetic_gain * state.D))
            <= 1e-12}


def probe_verdict(name: str, item: dict) -> bool:
    acute, baro = item["acute_drive"], item["baroreflex_drive"]
    below = item["map"] < item["map_set"]
    expected = {"A": acute == 0.0 and baro > 0.0, "B": baro == 0.0 and acute > 0.0,
                "C": acute >= 0.0 and baro > 0.0, "D": acute == 0.0 and baro == 0.0}[name]
    sign = baro >= 0.0 and (baro > 0.0) == below
    return expected and sign and item["sum_equal"]


def probes() -> dict:
    out = {}
    for name in PROBES:
        main = probe(name)
        out[name] = {**PROBES[name], **main, "passed": probe_verdict(name, main),
                     "by_map_set": {f"{m:g}": probe(name, m) for m in MAP_SETS}}
    high = probe("D", 80.0)
    out["high_pressure"] = {"map": high["map"], "map_set": 80.0, "baroreflex_drive": high["baroreflex_drive"],
                            "never_negative": high["baroreflex_drive"] == 0.0 and high["target"] >= 0.0}
    return out


# 5. HR from a run's own rows, with the baroreflex ---------------------------------------------------------------------------

def hr_series(run_: dict, rate: float, acute: float, debt: float, ceiling: float, map_set, baro: float) -> list[dict]:
    """hr_shock.hr_series with the relative-pressure term 0 (hr_primary.PRIMARY_HR_CALIBRATION) and the baroreflex added
    after the other terms through derived.baroreflex_drive: the core's sympathetic_target arithmetic, minute for
    minute."""
    anchors, profile, rows = run_["anchors"], run_["profile"], run_["rows"]
    on = replace(profile, **hp.PRIMARY_HR_CALIBRATION, baroreflex_to_sympathetic_gain=baro,
                 baroreflex_map_set_mmhg=map_set)
    beta = anchors.beta_blockade
    if not ceiling > rate:
        raise CoreInvariantError("the intrinsic rate is not below the sinus-rate ceiling")
    decay = math.exp(-1.0 / on.sympathetic_decay_tau_min)
    response = on.hr_per_sympathetic_drive * (1.0 - beta)
    out, drive = [], 0.0
    for minute, row in enumerate(rows):
        if not row["pulse"]:
            parts, target, drive = None, 0.0, 0.0
        else:
            hypoxaemia = (max(0.0, on.hypoxaemia_threshold_spo2 - row["spo2"])
                          - max(0.0, on.hypoxaemia_threshold_spo2 - anchors.spo2))
            hypoglycaemia = (max(0.0, on.hypoglycaemia_threshold_mg_dl - row["glucose"])
                             - max(0.0, on.hypoglycaemia_threshold_mg_dl - anchors.glucose))
            parts = {"acute": acute * (row["deficit"] / row["demand"]),
                     "pressure": on.sympathetic_per_pressure_deficit * (1.0 - row["pressure_rel"]),
                     "debt": debt * row["D"], "hypoxaemia": on.sympathetic_per_hypoxaemia_point * hypoxaemia,
                     "hypoglycaemia": on.sympathetic_per_hypoglycaemia_mg_dl * hypoglycaemia,
                     "baroreflex": baroreflex_drive(row["pressure_rel"], anchors, on)}
            target = max(0.0, (parts["acute"] + parts["pressure"] + parts["debt"] + parts["hypoxaemia"]
                               + parts["hypoglycaemia"]) + parts["baroreflex"])
            if minute == 0:
                drive = target
            else:
                held = drive if rows[minute - 1]["pulse"] else target
                drive = target if target >= held else target + (held - target) * decay
        if row["pulse"] and row["code"] == RhythmCode.SINUS.value:
            reserve = ceiling - rate
            hr = rate + reserve * math.tanh(response * drive / reserve)
        else:
            hr = row["rate_bpm"] if row["pulse"] else None
        out.append({"minute": minute, "drive": drive, "target": target, "hr": hr, "parts": parts, "response": response})
    return out


def _parts_bpm(point: dict) -> dict:
    parts = point["parts"] or {}
    return {name: point["response"] * parts.get(name, 0.0) for name in ("acute", "debt", "baroreflex")}


def _shares(series_: list) -> dict:
    totals = {name: math.fsum(p["parts"][name] for p in series_ if p["parts"]) for name in ("acute", "debt", "baroreflex")}
    whole = math.fsum(totals.values())
    return {name: (value / whole if whole > 0.0 else 0.0) for name, value in totals.items()}


def readings(runs: dict, rate: float, combo: dict, map_set, baro: float) -> dict:
    """hr_envelope_filter.readings' values for one (case, HR unit, latent combination, baroreflex point), from
    ``hr_series``, plus the arrival / untreated / definitive drive parts and the scenario shares of the target."""
    ceiling = combo["ceiling"]
    series_ = {key: hr_series(run_, rate, combo["acute"], combo["debt"], ceiling, map_set, baro)
               for key, run_ in runs.items()}
    series = {key: [p["hr"] for p in values] for key, values in series_.items()}
    if not all(None not in values and len(values) == MINUTES + 1 for values in series.values()):
        return {"complete": False}
    l1, l3 = series[L1], series[L3]
    unit_1, unit_2 = hf._units_minute(runs[L3]["rows"], 1.0), hf._units_minute(runs[L3]["rows"], 2.0)
    adequacy = runs[L3]["adequacy"]
    onset = adequacy["onset"] if adequacy["status"] == lc.L3_ADEQUATE else None
    sinus = [h for key, values in series.items() for h, row in zip(values, runs[key]["rows"])
             if row["code"] == RhythmCode.SINUS.value]
    peak = max(max(l1), max(l3))
    return {"complete": True, "arrival": l3[0], "l1_120": l1[120], "unit_1_minute": unit_1, "unit_2_minute": unit_2,
            "with_unit_1": l3[unit_1], "without_unit_1": series[CF1][unit_1],
            "benefit_1": series[CF1][unit_1] - l3[unit_1],
            "with_unit_2": l3[unit_2], "without_unit_2": series[CF2][unit_2],
            "benefit_2": series[CF2][unit_2] - l3[unit_2],
            "l3_60": l3[60], "l3_90": l3[90], "l3_120": l3[120], "onset": onset, "residual": l3[120] - rate,
            "max_hr": peak, "reserve_utilization": (peak - rate) / (ceiling - rate), "intrinsic": rate,
            "structural": all(rate <= h <= ceiling for h in sinus),
            "parts": {"arrival": _parts_bpm(series_[L3][0]), "l1_120": _parts_bpm(series_[L1][120]),
                      "l3_120": _parts_bpm(series_[L3][120])},
            "shares": _shares(series_[L1] + series_[L3])}


def rules(r57: dict, r72: dict) -> list[str]:
    """SIMULATION, ARRIVAL, then hr_envelope_filter.failures (A-F, unchanged), in ORDER."""
    if not (r57["complete"] and r72["complete"]):
        return ["SIMULATION"]
    out = []
    if not all(ARRIVAL[case]["low"] <= r["arrival"] <= ARRIVAL[case]["high"] for case, r in ((C57, r57), (C72, r72))):
        out.append("ARRIVAL")
    return out + hf.failures(r57, r72)


def _rule(name: str) -> str:
    return name.split()[0]


# 6. The per-unit task: four runs, the HR surface by reconstruction, the core's own HR and the non-regression ---------------

PHYSIOLOGY_FIELDS = ("minute", "pulse", "code", "pressure_rel", "spo2", "glucose", "D", "rr", "lactate", "output",
                     "delivery", "demand", "deficit", "bleed_ml_per_min", "prbc_units", "crystalloid_in_ml")


def _physiology(rows: list) -> list:
    return [tuple(row[name] for name in PHYSIOLOGY_FIELDS) for row in rows]


def _without_drive(states: list) -> list:
    return [state.evolve(aux=replace(state.aux, sympathetic_drive=0.0)) for state in states]


def combo_changes(combo: dict, map_set, baro: float) -> dict:
    return {"acute_deficit_to_sympathetic_gain": combo["acute"], "debt_to_sympathetic_gain": combo["debt"],
            "sinus_rate_ceiling_bpm": combo["ceiling"], "baroreflex_to_sympathetic_gain": baro,
            "baroreflex_map_set_mmhg": map_set}


def _unit_task(task: tuple) -> tuple:
    """One HR unit (tone gain, demand, P3 set, case, lactate-side point): L1, L3 and the two counterfactuals once (no
    baroreflex), HR rebuilt for every latent combination and baroreflex point; the core rerun with one combination and
    one primary point to check the rebuilt HR, every non-HR row and every L3 state but the drive."""
    key, entry, point, case, factor, gain, combos, position, check = task
    base = {"deficit_to_tone_gain": gain, "afterload_sensitivity": AFTERLOAD, **hp.PRIMARY_HR_CALIBRATION}
    inputs = {"entry": entry, "point": point, "bag": None}
    runs = {sc: hf.full_run(inputs, case, sc, factor, "midpoint", base) for sc in SCENARIOS}
    rates = hs.intrinsic_levels(case)
    out = {}
    for ci, combo in enumerate(combos):
        for map_set, baro in POINTS:
            out[(ci, map_set, baro)] = readings(runs, rates[combo["intrinsic"][position]], combo, map_set, baro)
    ci, (map_set, baro) = check
    combo = combos[ci]
    level = combo["intrinsic"][position]
    on_changes = {**base, **combo_changes(combo, map_set, baro)}
    on = {sc: hf.full_run(inputs, case, sc, factor, level, on_changes) for sc in SCENARIOS}
    rebuilt = {sc: [p["hr"] for p in hr_series(runs[sc], rates[level], combo["acute"], combo["debt"], combo["ceiling"],
                                               map_set, baro)] for sc in SCENARIOS}
    states_on, _ = blood_anchors.trajectory(on[L3]["anchors"], on[L3]["items"], MINUTES, on[L3]["profile"])
    states_off, _ = blood_anchors.trajectory(on[L3]["anchors"], on[L3]["items"], MINUTES,
                                             replace(on[L3]["profile"], baroreflex_to_sympathetic_gain=0.0))
    drive_differs = any(a.aux.sympathetic_drive != b.aux.sympathetic_drive for a, b in zip(states_on, states_off))
    signals = {}
    for sc in (L1, L3):
        anchors, profile = runs[sc]["anchors"], runs[sc]["profile"]
        signals[sc] = [(mean_arterial_pressure(row["pressure_rel"], anchors, profile), row["deficit"] / row["demand"])
                       if row["pulse"] else None for row in runs[sc]["rows"]]
    validation = {"hr_equal": all(rebuilt[sc] == [row["hr"] for row in on[sc]["rows"]] for sc in SCENARIOS),
                  "rows_equal": all(_physiology(runs[sc]["rows"]) == _physiology(on[sc]["rows"]) for sc in SCENARIOS),
                  "states_equal": _without_drive(states_on) == _without_drive(states_off),
                  "baroreflex_moved_drive": drive_differs, "check": [ci, map_set, baro],
                  "min_drive": min(state.aux.sympathetic_drive for state in states_on)}
    return key, {"readings": out, "validation": validation, "signals": signals}


# 7. The carried pressure / tone region (P2J-3, recomputed on the live code) and the latent HR region ---------------------

def p2j3_record() -> dict:
    record = json.loads(P2J3_RECORD.read_text(encoding="utf-8"))
    if record["freeze_digest"] != P2J3_DIGEST or record["verdict"]["verdict"] != pf.READY:
        raise AssertionError("the P2J-3 record is not the committed one")
    return record


def _json(value):
    return json.loads(json.dumps(value, sort_keys=True, default=str))


def pressure_tone_region(map_=map, say=lambda *_: None) -> dict:
    """P2J-3's primary filter (A-I) at a = 0.3, recomputed with P2J-3's own functions on the live core and compared
    with its record: the non-regression of the pressure / tone results and the carried survivors."""
    record = p2j3_record()
    source_record = la.record_p2i2ab()
    source, support_ = la.source_space(source_record), source_record["crystalloid_support"]
    arrivals = lr.arrival_table()
    tasks = lc.haemodynamic_tasks(source, support_)
    store = lc.haemodynamics(tasks, map_)
    units_by_demand, digests = {}, {}
    for factor in DEMANDS:
        region = ho.retained_region(source, support_, arrivals, tasks, store, factor, map_)
        units_by_demand[factor], digests[f"{factor:g}"] = region["units"], region["digest"]
    say("P2J-3 blood trajectories")
    group_map = pf.groups(units_by_demand)
    plain, counterfactual = pf.blood_task_list(group_map, source, support_)
    bloods = {**dict(map_(vt._blood_task, plain)), **dict(map_(pf._cf_blood_task, counterfactual))}
    say("P2J-3 primary filter")
    evaluated = pf._evaluate(pf.PRIMARY_PAIRS, units_by_demand, group_map, bloods, arrivals, map_)
    full = {f"{g:g}": {f"{f:g}": evaluated[(g, AFTERLOAD, f)] for f in DEMANDS} for g in TONE_GAINS}
    primary = {g: {f: pf._public(v) for f, v in by.items()} for g, by in full.items()}
    results = evaluated[("results", AFTERLOAD)]
    support_out = {f"g{g} x{f}": pf.support(units_by_demand, full[g][f], results, float(f), float(g))
                   for g in full for f in full[g] if full[g][f]["survivors"]}
    survivors = {(g, f): evaluated[(g, AFTERLOAD, f)]["_survivors"] for g in TONE_GAINS for f in DEMANDS}
    return {"unchanged": {"units": all(digests[f"{f:g}"] == pf.UNITS[f] for f in DEMANDS),
                          "primary": _json(primary) == record["primary"], "support": _json(support_out) == record["support"],
                          "demand_class": {g: pf.demand_class(by) for g, by in full.items()} == record["demand_class"]},
            "primary": primary, "survivors": survivors, "source": source, "support": support_, "bloods": bloods,
            "blood_runs": len(plain), "counterfactual_runs": len(counterfactual), "groups": len(group_map)}


def latent_region() -> dict:
    """P2I-2AK's surviving latent HR combinations per demand (its record), checked against P2I-2AJ's primary arrival
    pool, which P2I-2AK filtered without an envelope rejection."""
    record = json.loads(P2I2AK_RECORD.read_text(encoding="utf-8"))
    if record["freeze_digest"] != P2I2AK_DIGEST or record["verdict"]["verdict"] != hf.READY:
        raise AssertionError("the P2I-2AK record is not the committed one")
    surviving = record["cross_demand"]["surviving"]
    by = {1.0: surviving.get(hf.ROBUST, []) + surviving.get(hf.ONLY_1_0, []),
          1.1: surviving.get(hf.ROBUST, []) + surviving.get(hf.ONLY_1_1, [])}
    aj = hf.p2i2aj_record()
    out, equal = {}, True
    for factor in DEMANDS:
        pool = hf.arrival_pool(aj, factor)["primary"]
        mine = sorted(tuple(c) for c in by[factor])
        equal = equal and mine == sorted(hf.latent(s) for s in pool)
        out[factor] = [{"intrinsic": [c[0], c[1]], "acute": c[2], "debt": c[3], "ceiling": c[4]} for c in mine]
    universe = record["cross_demand"]["universe"]
    return {"combos": out, "equal_to_arrival_pool": equal, "universe": universe,
            "prior_region_rejection": {f"{f:g}": universe - len(out[f]) for f in DEMANDS}}


def hr_units(survivors: list) -> list:
    """(P3 set, 57m point, 72f point) -> how many lactate survivors project to it."""
    weights = {}
    for i, a, b, q, d in survivors:
        weights[(q, a, b)] = weights.get((q, a, b), 0) + 1
    return sorted(weights.items())


def unit_tasks(region: dict, latent: dict) -> list:
    tasks, index = [], 0
    for (gain, factor), survivors in sorted(region["survivors"].items()):
        combos = latent["combos"][factor]
        for (q, a, b), _ in hr_units(survivors):
            for case, lam, position in ((C57, a, 0), (C72, b, 1)):
                check = (index % len(combos), PRIMARY_POINTS[index % len(PRIMARY_POINTS)])
                tasks.append(((gain, factor, q, case, lam), region["source"]["p3"][q], LAMBDAS[lam], case, factor, gain,
                              combos, position, check))
                index += 1
    return tasks


# 8. The filter, support and cross-classification -----------------------------------------------------------------------------

def domain_ok(combo: dict, point: tuple, gain: float) -> bool:
    map_set, baro = point
    if baro < 0.0 or (baro > 0.0 and not (map_set is not None and map_set > 0.0)):
        return False
    if gain not in TONE_GAINS or gain in EXCLUDED_TONE:
        return False
    if not all(combo["ceiling"] > hs.intrinsic_levels(case)[combo["intrinsic"][pos]] for case, pos in ((C57, 0), (C72, 1))):
        return False
    try:
        replace(DEFAULT_PROFILE, **hp.PRIMARY_HR_CALIBRATION, **combo_changes(combo, *point))
    except CoreInvariantError:
        return False
    return True


def filter_point(gain: float, factor: float, point: tuple, units: list, combos: list, raw: dict) -> dict:
    first = {name: 0 for name in RULES}
    anyf = {name: 0 for name in RULES}
    by_case = {}
    survivors, entering, keys = 0, 0, []
    for (q, a, b), weight in units:
        r57s, r72s = raw[(gain, factor, q, C57, a)]["readings"], raw[(gain, factor, q, C72, b)]["readings"]
        for ci, combo in enumerate(combos):
            entering += weight
            failed = [] if domain_ok(combo, point, gain) else ["DOMAIN"]
            if not failed:
                failed = rules(r57s[(ci, *point)], r72s[(ci, *point)])
            names = list(dict.fromkeys(_rule(name) for name in failed))
            for name in names:
                anyf[name] += weight
            for name in failed:
                by_case[name] = by_case.get(name, 0) + weight
            if names:
                first[min(names, key=RULES.index)] += weight
            else:
                survivors += weight
                keys.append((q, a, b, ci))
    return {"entering": entering, "survivors": survivors, "first_failure": first, "any_failure": anyf,
            "by_case": dict(sorted(by_case.items())), "survivor_units": len({k[:3] for k in keys}),
            "survivor_combinations": sorted({k[3] for k in keys}), "_keys": keys}


def _point_key(point: tuple) -> str:
    map_set, baro = point
    return "reference" if map_set is None else f"MAP{map_set:g} k{baro:g}"


def _spread(values) -> dict:
    values = [v for v in values if v is not None]
    if not values:
        return {"n": 0}
    return {"n": len(values), "low": min(values), "median": statistics.median(values), "high": max(values)}


def support_tables(filtered: dict) -> dict:
    by = {"map_set": {}, "gain": {}, "tone": {}, "demand": {}}
    cross = {}
    for (g, f, point), item in filtered.items():
        if point == REFERENCE_POINT:
            continue
        m, k = point
        for name, value in (("map_set", f"{m:g}"), ("gain", f"{k:g}"), ("tone", f"{g:g}"), ("demand", f"{f:g}")):
            slot = by[name].setdefault(value, {"entering": 0, "survivors": 0})
            slot["entering"] += item["entering"]
            slot["survivors"] += item["survivors"]
        cross[f"x{f:g} g{g:g} {_point_key(point)}"] = item["survivors"]
    branches = {f"{g:g}": any(filtered[(g, f, p)]["survivors"] for f in DEMANDS for p in PRIMARY_POINTS)
                for g in TONE_GAINS}
    return {"by": by, "cross": cross, "tone_branch_compatible": branches,
            "incompatible_tone_branches": [g for g, ok in branches.items() if not ok]}


# 9. Observables, double counting, B1-B7 ----------------------------------------------------------------------------------------

OBSERVABLES = ("arrival", "l1_120", "benefit_1", "benefit_2", "l3_60", "l3_90", "l3_120", "residual", "max_hr")


def observables(filtered: dict, raw: dict) -> dict:
    out = {}
    for case, position in ((C57, 0), (C72, 1)):
        values = {name: [] for name in OBSERVABLES}
        values.update({f"{part}_{when}": [] for part in ("acute", "debt", "baroreflex")
                       for when in ("arrival", "l1_120", "l3_120")})
        values.update({f"baroreflex_increment_{when}": [] for when in ("arrival", "l1_120", "l3_120")})
        for (g, f, point), item in filtered.items():
            if point == REFERENCE_POINT:
                continue
            for q, a, b, ci in item["_keys"]:
                lam = a if position == 0 else b
                r = raw[(g, f, q, case, lam)]["readings"][(ci, *point)]
                ref = raw[(g, f, q, case, lam)]["readings"][(ci, *REFERENCE_POINT)]
                for name in OBSERVABLES:
                    values[name].append(r[name])
                for when in ("arrival", "l1_120", "l3_120"):
                    for part in ("acute", "debt", "baroreflex"):
                        values[f"{part}_{when}"].append(r["parts"][when][part])
                    values[f"baroreflex_increment_{when}"].append(r[when] - ref[when])
        out[case] = {name: _spread(v) for name, v in values.items()}
    return out


def increments(filtered: dict, raw: dict) -> dict:
    """The observable composite: HR(point) - HR(no baroreflex), same candidate, at arrival, untreated 120 and after
    definitive management 120, per baroreflex point, over the point's survivors (both cases)."""
    out = {}
    for point in PRIMARY_POINTS:
        values = {case: {w: [] for w in ("arrival", "l1_120", "l3_120")} for case in CASES}
        for (g, f, p), item in filtered.items():
            if p != point:
                continue
            for q, a, b, ci in item["_keys"]:
                for case, lam in ((C57, a), (C72, b)):
                    r = raw[(g, f, q, case, lam)]["readings"]
                    for w in values[case]:
                        values[case][w].append(r[(ci, *point)][w] - r[(ci, *REFERENCE_POINT)][w])
        out[_point_key(point)] = {case: {w: _spread(v) for w, v in by.items()} for case, by in values.items()}
    return out


DOUBLE_COUNTING = ("STRUCTURALLY_DISTINCT_BUT_CORRELATED", "FUNCTIONALLY_REDUNDANT_IN_CURRENT_CASES",
                   "PATHOLOGICAL_DOUBLE_COUNTING")
DOUBLE_COUNTING_RULE = (
    "Frozen, threshold-free. PATHOLOGICAL_DOUBLE_COUNTING when a structural probe A-D fails or, on a clinical minute, "
    "the baroreflex signal is negative or positive at MAP >= MAP_set (it would then be reading something else). "
    "Otherwise FUNCTIONALLY_REDUNDANT_IN_CURRENT_CASES when, on the pooled clinical pulse minutes (L1 and L3 of every "
    "entering HR unit, every tone gain and demand) at that MAP_set, no minute has exactly one of the two signals "
    "positive; STRUCTURALLY_DISTINCT_BUT_CORRELATED when some minute has exactly one positive. The Pearson correlation, "
    "the joint and single positive fractions, the drive shares and the ranking changes are reported, never thresholded. "
    "The overall class is the most severe across MAP_set candidates.")


def _pearson(xs: list, ys: list):
    if len(xs) < 2 or len(set(xs)) < 2 or len(set(ys)) < 2:
        return None
    return statistics.correlation(xs, ys)


def double_counting(raw: dict, probes_: dict, filtered: dict) -> dict:
    per = {}
    probes_ok = all(probes_[name]["passed"] for name in PROBES)
    for m in MAP_SETS:
        b, s, wrong = [], [], 0
        for item in raw.values():
            for sc in (L1, L3):
                for pair in item["signals"][sc]:
                    if pair is None:
                        continue
                    mean, acute = pair
                    signal = baroreflex_signal(mean, m)
                    wrong += signal < 0.0 or (signal > 0.0 and mean >= m)
                    b.append(signal)
                    s.append(acute)
        n = len(b)
        both = sum(1 for x, y in zip(b, s) if x > 0.0 and y > 0.0)
        baro_only = sum(1 for x, y in zip(b, s) if x > 0.0 and y <= 0.0)
        acute_only = sum(1 for x, y in zip(b, s) if x <= 0.0 and y > 0.0)
        if not probes_ok or wrong:
            klass = DOUBLE_COUNTING[2]
        elif baro_only + acute_only == 0:
            klass = DOUBLE_COUNTING[1]
        else:
            klass = DOUBLE_COUNTING[0]
        per[f"{m:g}"] = {"minutes": n, "correlation": _pearson(b, s), "both_positive": both / n if n else None,
                         "baroreflex_only": baro_only / n if n else None, "acute_only": acute_only / n if n else None,
                         "neither": (n - both - baro_only - acute_only) / n if n else None, "sign_violations": wrong,
                         "class": klass}
    severity = max(per.values(), key=lambda v: DOUBLE_COUNTING.index(v["class"]))["class"]
    shares = {}
    for point in PRIMARY_POINTS:
        values = {name: [] for name in ("acute", "debt", "baroreflex")}
        for (g, f, p), item in filtered.items():
            if p != point:
                continue
            for q, a, bb, ci in item["_keys"]:
                for case, lam in ((C57, a), (C72, bb)):
                    r = raw[(g, f, q, case, lam)]["readings"][(ci, *point)]
                    for name in values:
                        values[name].append(r["shares"][name])
        shares[_point_key(point)] = {name: _spread(v) for name, v in values.items()}
    return {"by_map_set": per, "class": severity, "probes_passed": probes_ok, "shares": shares,
            "ranking": ranking_changes(raw, filtered)}


def _discordance(xs: list, ys: list) -> float | None:
    pairs = discordant = 0
    for i in range(len(xs)):
        for j in range(i + 1, len(xs)):
            dx, dy = xs[i] - xs[j], ys[i] - ys[j]
            if dx == 0.0 or dy == 0.0:
                continue
            pairs += 1
            discordant += (dx > 0.0) != (dy > 0.0)
    return discordant / pairs if pairs else None


def ranking_changes(raw: dict, filtered: dict) -> dict:
    """Per (tone gain, demand, point): rows the reference keeps and the point loses, and the share of discordant pairs
    in the order of the untreated 120 HR (57m and 72f) over the entering (HR unit, combination) items."""
    out = {}
    for (g, f, point), item in filtered.items():
        if point == REFERENCE_POINT:
            continue
        ref = filtered[(g, f, REFERENCE_POINT)]
        lost = len(set(ref["_keys"]) - set(item["_keys"]))
        order = {}
        for case, pos in ((C57, 0), (C72, 1)):
            xs, ys = [], []
            for key, value in raw.items():
                if key[0] != g or key[1] != f or key[3] != case:
                    continue
                for (ci, m, k), r in value["readings"].items():
                    if (m, k) == point and r["complete"]:
                        base = value["readings"][(ci, *REFERENCE_POINT)]
                        if base["complete"]:
                            xs.append(base["l1_120"])
                            ys.append(r["l1_120"])
            order[case] = _discordance(xs, ys)
        out[f"x{f:g} g{g:g} {_point_key(point)}"] = {"reference_survivors_lost": lost, "discordant_pairs": order}
    return out


def _at(series: list, minutes=MINUTES_REPORTED) -> list:
    return [series[m] if m < len(series) else None for m in minutes]


def scenario_behaviour(raw: dict, region: dict, probes_: dict) -> dict:
    """B1-B7: the baroreflex signal per MAP_set and its unconstrained contribution per unit of gain (25 bpm x signal;
    the contribution is gain x that) at 0 / 15 / 30 / 60 / 90 / 120, per case, over the entering units of every tone
    gain and demand. B1 arrival, B2 L1 and B5 L3 from the HR runs; B3 (L2) and B4 (L3 without haemostasis) from P2J-3's
    cached blood trajectories rebuilt at the tone gain (vascular_tone.rebuild, exact); B6 / B7 the synthetic probes A /
    B."""
    response = DEFAULT_PROFILE.hr_per_sympathetic_drive
    table = {}

    def add(name, case, maps):
        for m in MAP_SETS:
            slot = table.setdefault(name, {}).setdefault(case, {}).setdefault(f"{m:g}", [[] for _ in MINUTES_REPORTED])
            for index, value in enumerate(_at(maps)):
                if value is not None:
                    slot[index].append(baroreflex_signal(value, m))

    for (g, f, q, case, lam), item in raw.items():
        l1 = [p[0] if p else None for p in item["signals"][L1]]
        l3 = [p[0] if p else None for p in item["signals"][L3]]
        add("B1", case, l3[:1])
        add("B2", case, l1)
        add("B5", case, l3)
    for (g, f), survivors in region["survivors"].items():
        seen = set()
        for i, a, b, q, d in survivors:
            for case, lam in ((C57, a), (C72, b)):
                anchors = vt.tone_anchors(case, vt.level_of(lam), f)
                for name, key in (("B3", ("P2", case, (i, d))), ("B4", ("P3", case, q))):
                    if (name, key, g, f, lam) in seen:
                        continue
                    seen.add((name, key, g, f, lam))
                    rows = vt.rebuild(region["bloods"][key], anchors, g, AFTERLOAD)["rows"]
                    add(name, case, [row["map"] for row in rows])
    out = {}
    for name, by_case in table.items():
        out[name] = {case: {m: [{"minute": minute, "signal": _spread(v),
                                 "bpm_per_unit_gain": _spread([response * x for x in v])}
                                for minute, v in zip(MINUTES_REPORTED, values)]
                            for m, values in by_m.items()} for case, by_m in by_case.items()}
    out["B6"] = {"probe": "A", **{k: probes_["A"][k] for k in ("map", "acute_drive", "baroreflex_drive", "passed")}}
    out["B7"] = {"probe": "B", **{k: probes_["B"][k] for k in ("map", "acute_drive", "baroreflex_drive", "passed")}}
    return out


# 10. Identifiability, verdict and recommendation ----------------------------------------------------------------------------

CLASSES = ("WELL_CONSTRAINED", "PARTIALLY_CONSTRAINED", "POORLY_IDENTIFIED", "NON_IDENTIFIABLE")
IDENTIFIABILITY_RULE = (
    "Frozen, on the primary survivors only (the gain-0 reference never counts). For a quantity with levels (MAP_set: "
    "80 / 90 / 100; gain: 0.25 / 0.5 / 1 / 1.5), the survivor set of a level is the set of (tone gain, demand, HR unit, "
    "latent combination, other baroreflex coordinate) it keeps. WELL_CONSTRAINED when exactly one level keeps "
    "survivors; PARTIALLY_CONSTRAINED when at least one level is emptied and two or more keep survivors; "
    "POORLY_IDENTIFIED when no level is emptied but the sets differ; NON_IDENTIFIABLE when every level keeps the same "
    "set. Interactions are read the same way on the admissible baroreflex points: COUPLED when the set of (MAP_set, "
    "gain) points a latent combination (acute / debt gains, intrinsic rates, ceiling) or a tone gain keeps differs "
    "across combinations or tone gains, UNCOUPLED when it is the same.")


def _classify(sets: dict) -> str:
    alive = [k for k, v in sets.items() if v]
    if not alive:
        return "NOT_EVALUABLE"
    if len(alive) == 1:
        return CLASSES[0]
    if len(alive) < len(sets):
        return CLASSES[1]
    values = list(sets.values())
    return CLASSES[3] if all(v == values[0] for v in values) else CLASSES[2]


def identifiability(filtered: dict) -> dict:
    map_sets = {f"{m:g}": set() for m in MAP_SETS}
    gains = {f"{k:g}": set() for k in PRIMARY_BARO}
    by_combo, by_tone = {}, {}
    for (g, f, point), item in filtered.items():
        if point == REFERENCE_POINT:
            continue
        m, k = point
        for q, a, b, ci in item["_keys"]:
            map_sets[f"{m:g}"].add((g, f, q, a, b, ci, k))
            gains[f"{k:g}"].add((g, f, q, a, b, ci, m))
            by_combo.setdefault(f"x{f:g} c{ci}", set()).add(point)
            by_tone.setdefault(f"x{f:g}", {}).setdefault(f"{g:g}", set()).add(point)
    combo_sets = {}
    for key, points in by_combo.items():
        combo_sets.setdefault(key.split()[0], []).append(points)
    combos = {f: ("COUPLED" if any(p != lists[0] for p in lists) else "UNCOUPLED") for f, lists in combo_sets.items()}
    tones = {f: ("COUPLED" if any(p != list(by.values())[0] for p in by.values()) or len(by) < len(TONE_GAINS)
                 else "UNCOUPLED") for f, by in by_tone.items()}
    return {"map_set": {"class": _classify(map_sets), "survivors": {k: len(v) for k, v in map_sets.items()}},
            "gain": {"class": _classify(gains), "survivors": {k: len(v) for k, v in gains.items()}},
            "latent_combinations": {"class": combos, "points": {k: sorted([_point_key(p) for p in v])
                                                                for k, v in sorted(by_combo.items())}},
            "tone_gain": {"class": tones, "points": {f: {g: sorted(_point_key(p) for p in v) for g, v in by.items()}
                                                     for f, by in by_tone.items()}}}


READY = "BAROREFLEX_HR_RECERTIFICATION_SATISFIED"
NOT_READY = "BAROREFLEX_HR_RECERTIFICATION_NOT_READY"
ARRIVAL_STOP = "BAROREFLEX_INCOMPATIBLE_WITH_ARRIVAL_HR"
VERDICT_RULE = (
    "READY when: (1) some primary row survives (some baroreflex point with gain > 0, tone gain and demand); (2) every "
    "survivor is arrival-compatible and passes A-F (by the filter); (3) P2J-3's pressure / tone A-I results recompute "
    "exactly on the live core (units, primary filter, support, demand classes); (4) the baroreflex is non-negative and "
    "structurally distinct (probes A-D pass, no clinical sign violation, the double-counting class is not "
    "PATHOLOGICAL_DOUBLE_COUNTING); (5) no upstream change (every validation run: non-HR rows and every L3 state but "
    "the drive equal with the baroreflex on and off, the rebuilt HR equal to the core's, the drive never negative); "
    "(6) the gain-0 reference reproduces P2J-3's HR diagnostic (same rows, no A-F failure) and the latent region is "
    "P2I-2AK's; (7) the relative-pressure term is 0 in every profile used; (8) nothing is approved. Otherwise NOT_READY "
    "with the first failing check (BAROREFLEX_INCOMPATIBLE_WITH_ARRIVAL_HR when no row passes ARRIVAL at any primary "
    "point; NO_PRIMARY_SURVIVOR when rows pass ARRIVAL but none passes A-F).")
RECOMMENDATION_RULE = (
    "Frozen. If READY: ONE_MORE_BAROREFLEX_DECISION when (a) a tone-gain branch has no survivor at any primary point "
    "and demand, (b) the double-counting class is FUNCTIONALLY_REDUNDANT_IN_CURRENT_CASES, (c) a whole MAP_set or gain "
    "level is emptied (identifiability PARTIALLY_CONSTRAINED or WELL_CONSTRAINED, a faculty choice the envelopes "
    "forced) or (d) one demand keeps no survivor at all; each names the decision. Otherwise RR_NEXT, carrying the "
    "surviving (MAP_set, gain) points with g and demand as uncertainty. RR is not started either way.")
PROPOSED_ORDER = ("tone_branch", "redundant", "level_emptied", "demand_empty")


def verdict(checks: dict, arrival_any: bool, survivors_any: bool) -> dict:
    if not arrival_any:
        return {"verdict": f"{NOT_READY} — {ARRIVAL_STOP}", "blockers": [ARRIVAL_STOP], "checks": checks,
                "approved": [], "rule": VERDICT_RULE}
    if not survivors_any:
        return {"verdict": f"{NOT_READY} — NO_PRIMARY_SURVIVOR", "blockers": ["NO_PRIMARY_SURVIVOR"], "checks": checks,
                "approved": [], "rule": VERDICT_RULE}
    blockers = [name for name, ok in checks.items() if not ok]
    return {"verdict": READY if not blockers else f"{NOT_READY} — {blockers[0]}", "blockers": blockers,
            "checks": checks, "approved": [], "rule": VERDICT_RULE}


def recommendation(tables: dict, dc: dict, ident: dict) -> dict:
    reasons = {"tone_branch": bool(tables["incompatible_tone_branches"]),
               "redundant": dc["class"] == DOUBLE_COUNTING[1],
               "level_emptied": any(ident[q]["class"] in CLASSES[:2] for q in ("map_set", "gain")),
               "demand_empty": any(v["survivors"] == 0 for v in tables["by"]["demand"].values())}
    needed = [name for name in PROPOSED_ORDER if reasons[name]]
    return {"recommendation": "ONE_MORE_BAROREFLEX_DECISION" if needed else "RR_NEXT", "reasons": reasons,
            "decisions": needed, "rule": RECOMMENDATION_RULE}


POLICY = ("Shadow only. P2J-3's and P2I-2AK's committed records and machinery; legacy HR and BP never read (LegacyLock), "
          "the P2F region never consumed (P2FGuard); MAP_set and gains predeclared and never extended; the relative-"
          "pressure term 0; HR never feeds pressure; nothing approved; RR, consciousness and collapse untouched.")

# 11. What P2J-4 changed outside its own module (the AST proof for the closed packages' guards) ---------------------------

DERIVED = vt.DERIVED
P2J4_STATEMENTS = ("CoreProfile", "PARAMETERS", "sympathetic_target", "mean_arterial_pressure", "baroreflex_signal",
                   "baroreflex_drive")
#: derived.py: its hash at P2J-3 (789b6f4, the P2J-2 file), at P2J-1 and at P2I-2AK; the statements P2J-4 changed, and
#: those with P2J-2's (since P2J-1) and with P2J-1's and P2J-2's (since P2I-2AK); the AST digest of every other
#: statement at each, which the live file must keep.
P2J4_CHANGES = {
    DERIVED: {"sha_at_p2j3": "6974d0fcf5159e9a67aa18fc030d9a65d87da40a5d776b3be258d3589ba2bfda",
              "sha_at_p2j1": vt.P2J2_CHANGES[DERIVED]["sha_at_p2j1"],
              "sha_at_p2i2ak": vt.P2J2_CHANGES[DERIVED]["sha_at_p2i2ak"],
              "changed": P2J4_STATEMENTS,
              "since_p2j1": tuple(dict.fromkeys(vt.P2J2_CHANGES[DERIVED]["changed"] + P2J4_STATEMENTS)),
              "since_p2i2ak": tuple(dict.fromkeys(vt.P2J2_CHANGES[DERIVED]["since_p2i2ak"] + P2J4_STATEMENTS)),
              "outside_p2j3": "4ea9aff1c37ee63f47dbed264850e505a97464d42beb9d85507d355ba69877bf",
              "outside_p2j1": "483dd9ccdc84fa8598ee67fcf8cc3e6902bdf8b27fd7d4d506a4d94a4cdbc711",
              "outside_p2i2ak": "84156e60e839111dd0f9e5da64af69f8fabda2b31d542d506ec14c40722998fb"},
}
#: The two tuple-only files at P2J-3: P2J-4 adds its modules to their tuples, nothing else (the rest is P2J-1's).
TUPLE_AT_P2J3 = {"clinical_core/lactate_slice.py": "edba551675eebd8902f9730d2496810f493d42e1a39cabc2c45479e52e73b16f",
                 "clinical_core/decision_pack.py": "d99f7a3027f5e451847673edb3b7cb3254eeb4a397661dfa069cecfa8cb8948c"}


BARO_NAMES = ("baroreflex_to_sympathetic_gain", "baroreflex_map_set_mmhg")
AMENDED_ENTRY = "sympathetic_per_pressure_deficit"


def _mentions(node, name: str) -> bool:
    return any((isinstance(n, ast.Name) and n.id == name) or (isinstance(n, ast.Attribute) and n.attr == name)
               for n in ast.walk(node))


class StripP2J4(ast.NodeTransformer):
    """What P2J-4 put inside its declared statements, removed: the baroreflex fields and checks of CoreProfile, the
    baroreflex PARAMETERS entries and the amended text of the relative-pressure entry, and the baroreflex line and the
    docstring of sympathetic_target. What is left must equal the statement before P2J-4."""

    def generic_visit(self, node):
        super().generic_visit(node)
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                setattr(node, field, [v for v in value if not self._dropped(v)])
        if isinstance(node, ast.Dict):
            pairs = [(k, v) for k, v in zip(node.keys, node.values)
                     if not (isinstance(k, ast.Constant) and k.value in BARO_NAMES)]
            node.keys = [k for k, _ in pairs]
            node.values = [ast.Constant(value=None) if isinstance(k, ast.Constant) and k.value == AMENDED_ENTRY else v
                           for k, v in pairs]
        if isinstance(node, ast.FunctionDef) and node.name == "sympathetic_target" and isinstance(
                node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant):
            node.body = node.body[1:]
        return node

    @staticmethod
    def _dropped(v) -> bool:
        return ((isinstance(v, ast.AnnAssign) and isinstance(v.target, ast.Name) and v.target.id in BARO_NAMES)
                or (isinstance(v, ast.If) and any(_mentions(v.test, name) for name in BARO_NAMES))
                or (isinstance(v, ast.AugAssign) and _mentions(v.value, "baroreflex_drive")))


def statement(text: str, name: str):
    for node in ast.parse(text).body:
        targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(
            node, ast.AnnAssign) else []
        if getattr(node, "name", None) == name or any(isinstance(t, ast.Name) and t.id == name for t in targets):
            return node
    raise KeyError(name)


def inside_digest(text: str, name: str, *more) -> str:
    """The AST digest of one top-level statement with P2J-4's insertions removed (and any further transformers')."""
    node = StripP2J4().visit(statement(text, name))
    for transformer in more:
        node = transformer.visit(node)
    return hashlib.sha256(ast.dump(node).encode("utf-8")).hexdigest()


#: Inside the three statements P2J-4 changed and that existed before it, nothing but the baroreflex: their stripped AST
#: digests at P2J-3 (789b6f4).
INSIDE_AT_P2J3 = {"CoreProfile": "6d357e68f7374751e1f2ac7ddd5f404369e792cd275f95c4d09baac7c186db6a",
                  "PARAMETERS": "84a4e34aae2dfa3dc2da7e8be76997113597563c5eacebea577304746ef534a8",
                  "sympathetic_target": "fbec4f280ca8db70a65398d2580e91ab29bd007a5676fd6f818989f449576af1"}


def _proved(relative: str, names, digest: str) -> bool:
    return vt.outside_digest(vt._live(relative), names) == digest


def p2j3_sources(sources: dict) -> dict:
    """A P2J-3 (and P2J-2) dependency map: derived.py at its P2J-3 hash when P2J-4 changed only its declared statements,
    and the two tuple-only files at their P2J-3 hashes when only their tuples changed."""
    out = dict(sources)
    item = P2J4_CHANGES[DERIVED]
    if DERIVED in out and _proved(DERIVED, item["changed"], item["outside_p2j3"]):
        out[DERIVED] = item["sha_at_p2j3"]
    for relative, sha in TUPLE_AT_P2J3.items():
        if relative in out and _proved(relative, vt.TUPLE_CHANGES[relative]["changed"],
                                       vt.TUPLE_CHANGES[relative]["outside_p2j1"]):
            out[relative] = sha
    return out


def p2j1_sources(sources: dict) -> dict:
    """vascular_tone.p2j1_sources with derived.py proven against P2J-2's and P2J-4's statements together."""
    out = vt.p2j1_sources(sources)
    item = P2J4_CHANGES[DERIVED]
    if DERIVED in out and _proved(DERIVED, item["since_p2j1"], item["outside_p2j1"]):
        out[DERIVED] = item["sha_at_p2j1"]
    return out


def p2i2ak_sources(sources: dict) -> dict:
    """vascular_tone.p2i2ak_sources with derived.py proven against P2J-1's, P2J-2's and P2J-4's statements together."""
    out = vt.p2i2ak_sources(sources)
    item = P2J4_CHANGES[DERIVED]
    if DERIVED in out and _proved(DERIVED, item["since_p2i2ak"], item["outside_p2i2ak"]):
        out[DERIVED] = item["sha_at_p2i2ak"]
    return out


# 12. Design, freeze, run -------------------------------------------------------------------------------------------------------

def design() -> dict:
    return {"revision": REVISION, "decided": DECIDED, "faculty": FACULTY, "signal": SIGNAL, "timing": TIMING,
            "timing_rule": TIMING_RULE, "old_term": OLD_TERM, "old_term_rule": OLD_TERM_RULE,
            "map_sets": list(MAP_SETS), "map_set_status": MAP_SET_STATUS,
            "baro_gains": {f"{k:g}": v for k, v in BARO_STATUS.items()}, "carried": CARRIED,
            "excluded_tone": list(EXCLUDED_TONE), "order": list(ORDER), "rejection_class": REJECTION_CLASS,
            "arrival": ARRIVAL, "envelopes": ENVELOPES, "candidate_rule": CANDIDATE_RULE, "empty_rule": EMPTY_RULE,
            "probes": PROBES, "probe_rule": PROBE_RULE, "probe_gains": PROBE_GAINS, "probe_map_set": PROBE_MAP_SET,
            "double_counting_rule": DOUBLE_COUNTING_RULE, "identifiability_rule": IDENTIFIABILITY_RULE,
            "verdict_rule": VERDICT_RULE, "recommendation_rule": RECOMMENDATION_RULE, "policy": POLICY,
            "minutes_reported": list(MINUTES_REPORTED), "p2j4_changes": P2J4_CHANGES, "tuple_at_p2j3": TUPLE_AT_P2J3}


def freeze_digest() -> str:
    text = json.dumps({"revision": REVISION, "p2j3": hashlib.sha256(P2J3_RECORD.read_bytes()).hexdigest(),
                       "design": design(), "sources": bf.freeze_sources()}, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _public(item: dict) -> dict:
    return {k: v for k, v in item.items() if not k.startswith("_")}


def run(progress=None, map_=map) -> dict:
    say = progress or (lambda *_: None)
    with lr.P2FGuard(), lr.LegacyLock():
        p2j3_record()
        out = {"freeze_digest": freeze_digest(), "decided": DECIDED, "revision": REVISION, "policy": POLICY,
               "faculty": FACULTY, "record": P2J3_DIGEST, "design": design()}
        say("probes")
        probes_ = probes()
        say("pressure / tone region (P2J-3 recomputed)")
        region = pressure_tone_region(map_, say)
        latent = latent_region()
        say("HR units")
        tasks = unit_tasks(region, latent)
        raw = dict(map_(_unit_task, tasks))
        say("filter")
        filtered = {}
        for (g, f), survivors in region["survivors"].items():
            units = hr_units(survivors)
            for point in POINTS:
                filtered[(g, f, point)] = filter_point(g, f, point, units, latent["combos"][f], raw)
        validations = [item["validation"] for item in raw.values()]
        p2j3_hr = p2j3_record()["hr"]["by_point"]
        reference = {f"g{g:g} x{f:g}": {"candidate_rows": filtered[(g, f, REFERENCE_POINT)]["entering"],
                                        "failures": {k: v for k, v in filtered[(g, f, REFERENCE_POINT)]["by_case"].items()}}
                     for g in TONE_GAINS for f in DEMANDS if region["survivors"][(g, f)]}
        reference_ok = all(reference[k]["candidate_rows"] == p2j3_hr[k]["candidate_rows"] and
                           reference[k]["failures"] == p2j3_hr[k]["failures"] for k in reference)
        primary = {k: v for k, v in filtered.items() if k[2] != REFERENCE_POINT}
        arrival_any = any(item["survivors"] or item["entering"] - item["first_failure"]["ARRIVAL"]
                          - item["first_failure"]["DOMAIN"] - item["first_failure"]["SIMULATION"] > 0
                          for item in primary.values())
        survivors_any = any(item["survivors"] for item in primary.values())
        tables = support_tables(filtered)
        say("double counting, scenarios, identifiability")
        dc = double_counting(raw, probes_, filtered)
        ident = identifiability(filtered)
        checks = {"pressure_tone_unchanged": all(region["unchanged"].values()),
                  "signal_nonnegative_and_distinct": all(probes_[n]["passed"] for n in PROBES)
                  and probes_["high_pressure"]["never_negative"] and dc["class"] != DOUBLE_COUNTING[2],
                  "upstream_unchanged": all(v["rows_equal"] and v["states_equal"] for v in validations),
                  "reconstruction_exact": all(v["hr_equal"] for v in validations),
                  "drive_never_negative": all(v["min_drive"] >= 0.0 for v in validations),
                  "reference_reproduces_p2j3_hr": reference_ok,
                  "latent_region_p2i2ak": latent["equal_to_arrival_pool"],
                  "old_term_retired": hp.PRIMARY_HR_CALIBRATION == {"sympathetic_per_pressure_deficit": 0.0},
                  "nothing_approved": True}
        out.update({
            "probes": probes_, "pressure_tone": {"unchanged": region["unchanged"], "primary": region["primary"]},
            "latent": {"combos": {f"{f:g}": v for f, v in latent["combos"].items()},
                       "equal_to_arrival_pool": latent["equal_to_arrival_pool"], "universe": latent["universe"],
                       "HR_PRIOR_REGION_REJECTION": latent["prior_region_rejection"]},
            "filter": {f"g{g:g} x{f:g} {_point_key(p)}": _public(v) for (g, f, p), v in filtered.items()},
            "reference": reference, "support": tables, "observables": observables(filtered, raw),
            "increments": increments(filtered, raw), "double_counting": dc,
            "scenarios": scenario_behaviour(raw, region, probes_), "identifiability": ident,
            "validation": {"tasks": len(validations), "hr_equal": checks["reconstruction_exact"],
                           "rows_equal": all(v["rows_equal"] for v in validations),
                           "states_equal": all(v["states_equal"] for v in validations),
                           "baroreflex_moved_drive": sum(v["baroreflex_moved_drive"] for v in validations),
                           "checked_points": sorted({_point_key(tuple(v["check"][1:])) for v in validations})},
            "efficiency": {"p2j3_blood_runs": region["blood_runs"], "p2j3_counterfactual_runs":
                           region["counterfactual_runs"], "p2j3_groups": region["groups"],
                           "hr_runs_without_baroreflex": len(SCENARIOS) * len(tasks),
                           "hr_validation_runs": len(SCENARIOS) * len(tasks), "state_runs": 2 * len(tasks),
                           "reconstructed_series": sum(len(SCENARIOS) * len(t[6]) * len(POINTS) for t in tasks),
                           "cartesian_sweep": False, "legacy_read": False}})
        out["verdict"] = verdict(checks, arrival_any, survivors_any)
        if out["verdict"]["verdict"] == READY:
            out["recommendation"] = recommendation(tables, dc, ident)
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
        path = args.out / "baroreflex.json"
        path.write_text(json.dumps(run(lambda step: print(step, flush=True)), sort_keys=True, separators=(",", ":"),
                                   default=str), encoding="utf-8")
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
