"""P2G: the faculty calibration decision pack. Analysis and decision support only.

    python -m clinical_core.decision_pack [--quick] [--out <directory outside the repository>]

Shadow and offline. It turns the structurally admissible region P2F left (docs/PHASE2_SHADOW_CORE.md
§12.7) into compact tables for a faculty decision. It never selects, ranks or recommends a value,
never marks anything FACULTY_APPROVED, never migrates GI, never changes a canonical default and
never uses the family engine's trajectories as a reference: the engine only supplies each
scenario's inputs, through the frozen path of P2G-1. Every number here is model-only evidence.

"low", "middle" and "high" are positions inside the admissible region for one read-out, not
preferences. An effect row changes one factor around the all-midpoint candidate; it shows a
direction and a size, not an interaction.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import replace
from pathlib import Path

from . import calibration, gi_reference
from .bands import ARRIVAL, Drift
from .calibration import LEVELS, REGISTRY, GICandidate
from .derived import DEFAULT_PROFILE, _metabolic_drive, preload_position, respiratory_rate
from .integration import run
from .legacy_adapter import contributors_from_legacy
from .modules import GIHaemorrhage
from .shadow import SCENARIOS as GI_SCENARIOS
from .state import Anchors, RhythmCode, UnresolvedBoundary

CASES = gi_reference.GI_CASES
TIMES = (0, 15, 30, 60, 90, 120)
KINETICS = ("debt_clearance_tau_min", "lactate_per_output_deficit", "lactate_clearance_tau_min")
#: Every band at its midpoint: the representative middle of the admissible region.
MIDDLE = GICandidate({name: REGISTRY[name].midpoint for name in KINETICS})

#: The scenarios the tables read. The untreated run is extended to 120 min (the core runs on, its
#: inputs are the engine's bleeding source with no order); the others are the GI golden scenarios.
DECISION_SCENARIOS = {
    "untreated_120": {"minutes": 120, "orders": {}},
    "fluids_alone": GI_SCENARIOS["saline_2l_over_20"],
    "prbc_alone": GI_SCENARIOS["prbc_2u_over_60"],
    "definitive_management": GI_SCENARIOS["definitive_management"],
    "aggressive_volume": GI_SCENARIOS["aggressive_volume"],
}
ENVELOPE_SCENARIOS = ("untreated_120", "fluids_alone", "prbc_alone", "definitive_management")

#: Labels for what a row is. None of them is a recommendation.
ADMISSIBLE, REJECTED, NOT_ASSESSED, SENSITIVITY = ("ADMISSIBLE", "REJECTED_BY_FROZEN_RULES", "NOT_ASSESSED",
                                                    "SENSITIVITY_PROBE")


# Admissible region ---------------------------------------------------------------------------

def p2f_rejection(candidate: GICandidate) -> str | None:
    """Why P2F's final sweep rejected this GI design point (docs §12.7), or None.

    The rule is the sweep's outcome written down, not a new rule; the tests check it against
    the frozen acceptance on both kinds of rejection and on admissible points.
    """
    if candidate.preload == "lower":
        return "HR1-HR4: the HR1 probe empties 57m's ventricle at preload position 0.2 (invalid state)"
    if candidate.profile.get("debt_clearance_tau_min") == 30.0 and candidate.debt == "upper":
        return ("HR1 (gi_bleed_72f): an arrival debt of 60 with a 30-min repayment; HR falls during the "
                "probe's synthetic volume loss")
    return None


def admissible(quick: bool = False) -> list[GICandidate]:
    """P2F's structurally admissible GI design points (all of them, or the kinetics corners)."""
    candidates = [candidate for candidate in calibration.gi_candidates() if p2f_rejection(candidate) is None]
    if quick:
        corners = [candidate for candidate in candidates
                   if (candidate.excess, candidate.intrinsic, candidate.debt, candidate.delivery, candidate.preload)
                   == ("midpoint",) * 5
                   and all(candidate.profile[name] != REGISTRY[name].midpoint for name in KINETICS)]
        candidates = corners + [MIDDLE]
    return candidates


_ASSESSED: dict = {}


def assess(candidate: GICandidate) -> dict:
    """A for any candidate: the frozen GI acceptance plus the mechanism rules it does not run."""
    key = candidate.key()
    if key not in _ASSESSED:
        gi = calibration.gi_physiology(candidate)
        rest = [name for name in calibration.CHECKS if name not in gi["passed"] and name not in gi["failed"]]
        mechanisms = calibration.physiology(candidate.profile, rest)
        failed = {**gi["failed"], **mechanisms["failed"]}
        _ASSESSED[key] = {"status": REJECTED if failed else ADMISSIBLE, "failed": failed}
    return _ASSESSED[key]


# Runs ----------------------------------------------------------------------------------------

_INPUTS: dict = {}


def scenario_contributors(case: str, scenario: str, source_scale: float = 1.0) -> tuple:
    """The scenario's inputs, from the frozen family-engine path; ``source_scale`` multiplies the
    bleeding source (a sensitivity probe: the source has no candidate band)."""
    key = (case, scenario)
    if key not in _INPUTS:
        _INPUTS[key] = contributors_from_legacy(calibration._legacy_run(case, DECISION_SCENARIOS[scenario]))
    if source_scale == 1.0:
        return _INPUTS[key]
    return tuple(replace(item, blood_loss_ml_per_min=item.blood_loss_ml_per_min * source_scale)
                 if isinstance(item, GIHaemorrhage) else item for item in _INPUTS[key])


def rr_parts(state, anchors: Anchors, profile, lactate: float) -> tuple[float, float]:
    """RR split as ``derived.respiratory_rate`` builds it: the ventilatory part (from W and the
    arrival RR left after its metabolic share) and the metabolic part (acidaemic drive)."""
    arrival_metabolic = _metabolic_drive(anchors.lactate, profile)
    share = min(arrival_metabolic, max(0.0, anchors.respiratory_rate - profile.rr_ventilatory_floor))
    ventilatory = (anchors.respiratory_rate - share) * (1.0 + max(0.0, state.W))
    now = _metabolic_drive(lactate, profile)
    metabolic = share + (now - arrival_metabolic) if now >= arrival_metabolic else share * now / arrival_metabolic
    drive = max(0.0, 1.0 + min(0.0, state.W))
    return drive * ventilatory, drive * metabolic


def _record(state, item, anchors: Anchors, profile) -> dict:
    beta_factor = 1.0 - anchors.beta_blockade
    intrinsic = state.R.rate_bpm
    sympathetic = (profile.hr_per_sympathetic_drive * beta_factor * state.aux.sympathetic_drive
                   if item.rhythm is RhythmCode.SINUS else 0.0)
    ventilatory, metabolic = rr_parts(state, anchors, profile, item.lactate)
    if abs(min(profile.rr_max, ventilatory + metabolic) - item.respiratory_rate) > 1e-9:
        raise AssertionError("the RR split no longer adds up to the core's RR")
    return {"sbp": item.sbp, "map": item.map, "hr": item.pulse_rate_bpm, "intrinsic_bpm": intrinsic,
            "sympathetic_bpm": sympathetic, "beta_factor": beta_factor,
            "other_chronotropic_bpm": item.pulse_rate_bpm - intrinsic - sympathetic,
            "lactate": item.lactate, "D": state.D, "rr": item.respiratory_rate, "rr_ventilatory": ventilatory,
            "rr_metabolic": metabolic, "output": item.output_rel, "V": state.V, "L": state.L,
            "preload_position": preload_position(state, anchors, profile), "delivery": item.delivery_rel}


def trajectory(case: str, candidate: GICandidate, scenario: str, *, source_scale: float = 1.0,
               case_extra: dict | None = None, times=TIMES) -> dict:
    """One run read at ``times``. A run whose output reaches zero with a pulse (collapse off, as
    in every canonical GI run) stops: the minutes before are kept and the stop is reported."""
    values = {**calibration.case_values(case, candidate), **(case_extra or {})}
    anchors = gi_reference.candidate_anchors(case, values)
    profile = replace(DEFAULT_PROFILE, **candidate.profile)
    items = scenario_contributors(case, scenario, source_scale)
    minutes = DECISION_SCENARIOS[scenario]["minutes"]
    stopped = None
    try:
        result = run(anchors, items, minutes, profile)
    except UnresolvedBoundary as error:
        stopped = int(str(error).split(":")[0].split()[-1])
        result = run(anchors, items, stopped - 1, profile)
    derived = result.derived()
    points = {minute: _record(result.states[minute], derived[minute], anchors, profile)
              for minute in times if minute < len(result.states)}
    return {"minutes": minutes, "stopped_at": stopped, "points": points,
            "final": _record(result.states[-1], derived[-1], anchors, profile)}


# Envelopes over the admissible region ---------------------------------------------------------

def envelope_runs(quick: bool = False) -> dict:
    """Every admissible candidate in every envelope scenario, for both cases."""
    runs = {}
    for candidate in admissible(quick):
        for case in CASES:
            for scenario in ENVELOPE_SCENARIOS:
                runs[(candidate.key(), case, scenario)] = trajectory(case, candidate, scenario)
    return runs


def envelope(runs: dict, case: str, scenario: str, field: str, minute: int) -> dict:
    """min / median / max of one read-out over the admissible region, with where they sit."""
    values = [(run_["points"][minute][field], key) for (key, case_, scenario_), run_ in runs.items()
              if case_ == case and scenario_ == scenario and minute in run_["points"]]
    stopped = sum(1 for (key, case_, scenario_), run_ in runs.items()
                  if case_ == case and scenario_ == scenario and minute not in run_["points"])
    if not values:
        return {"n": 0, "stopped_before": stopped}
    ordered = sorted(values)
    middle = len(ordered) // 2
    median = ordered[middle][0] if len(ordered) % 2 else (ordered[middle - 1][0] + ordered[middle][0]) / 2
    return {"n": len(values), "stopped_before": stopped, "min": ordered[0][0], "argmin": ordered[0][1],
            "median": median, "max": ordered[-1][0], "argmax": ordered[-1][1]}


def _candidate(key: str) -> GICandidate:
    return next(candidate for candidate in calibration.gi_candidates() if candidate.key() == key)


_DESIGN: set = set()


def in_p2f_design(case: str, candidate: GICandidate, options: dict) -> bool:
    """Whether P2F's sweep ran this exact set: a design point, the case's own source and reserve."""
    if not _DESIGN:
        _DESIGN.update(item.key() for item in calibration.gi_candidates())
    # A profile entry at the canonical default is the design's own value, not a moved parameter.
    profile = {name: value for name, value in candidate.profile.items()
               if name in KINETICS or value != getattr(DEFAULT_PROFILE, name)}
    if replace(candidate, profile=profile).key() not in _DESIGN or options.get("source_scale", 1.0) != 1.0:
        return False
    base = gi_reference.candidate_anchors(case, calibration.case_values(case, candidate))
    return all(getattr(base, name) == value for name, value in options.get("case_extra", {}).items())


def _effects(case, scenario, factors, field, times) -> list[dict]:
    """One factor at a time around MIDDLE: (factor, level, label, status, read-outs).

    Most rows are not P2F design points (the design varies only the three kinetics and fixed
    combinations of the case-band levels): ``in_p2f_design`` says which are."""
    rows = []
    for factor, variants in factors.items():
        for label, candidate, options in variants:
            options = dict(options)
            status = options.pop("status", None)
            run_ = trajectory(case, candidate, scenario, times=times, **options)
            rows.append({"factor": factor, "level": label,
                         "status": status or assess(candidate)["status"],
                         "in_p2f_design": in_p2f_design(case, candidate, options),
                         "stopped_at": run_["stopped_at"],
                         "values": {minute: run_["points"].get(minute, {}).get(field) for minute in times}})
    return rows


def _levels(field: str) -> list:
    return [(level, replace(MIDDLE, **{field: level}), {}) for level in LEVELS]


def _kinetic(name: str) -> list:
    return [(f"{point:g}", replace(MIDDLE, profile={**MIDDLE.profile, name: point}), {})
            for point in REGISTRY[name].points()]


def _profile_points(name: str) -> list:
    return [(f"{point:g}", replace(MIDDLE, profile={**MIDDLE.profile, name: point}), {})
            for point in REGISTRY[name].points()]


# P2G-2 lactate --------------------------------------------------------------------------------

LACTATE_TIMES = (0, 30, 60, 120)


def lactate_tables(runs: dict) -> dict:
    tables = {}
    for case in CASES:
        envelopes = {scenario: {minute: envelope(runs, case, scenario, "lactate", minute)
                                for minute in LACTATE_TIMES}
                     for scenario in ("untreated_120", "definitive_management")}
        low = envelopes["untreated_120"][60]["argmin"]
        high = envelopes["untreated_120"][60]["argmax"]
        representatives = {}
        for label, key in (("low", low), ("middle", MIDDLE.key()), ("high", high)):
            representatives[label] = {"candidate": key, "trajectories": {
                scenario: {minute: runs[(key, case, scenario)]["points"].get(minute, {}).get("lactate")
                           for minute in LACTATE_TIMES}
                for scenario in ("untreated_120", "definitive_management")}}
        factors = {"arrival_oxygen_debt": [(level, replace(MIDDLE, debt=level), {}) for level in LEVELS],
                   "arrival_lactate_excess": _levels("excess"),
                   "lactate_per_output_deficit": _kinetic("lactate_per_output_deficit"),
                   "lactate_clearance_tau_min": _kinetic("lactate_clearance_tau_min")}
        tables[case] = {"envelopes": envelopes, "representatives": representatives,
                        "fractions": lactate_fractions(runs, case),
                        "effects": {scenario: _effects(case, scenario, factors, "lactate", LACTATE_TIMES)
                                    for scenario in ("untreated_120", "definitive_management")}}
    return tables


def lactate_fractions(runs: dict, case: str) -> dict:
    """Share of the admissible region on each side of the faculty questions' thresholds (model-only).

    ``n`` counts the runs that reach the minute read; a run that stopped earlier is not counted.
    """
    def share(scenario, minute, test):
        values = [(run_["points"][0]["lactate"], run_["points"][minute]["lactate"])
                  for (key, case_, scenario_), run_ in runs.items()
                  if case_ == case and scenario_ == scenario and minute in run_["points"]]
        return {"n": len(values), "fraction": sum(1 for arrival, now in values if test(arrival, now)) / len(values)}
    return {"untreated 60 min above arrival": share("untreated_120", 60, lambda arrival, now: now > arrival),
            "untreated 60 min more than 1 mmol/L above arrival":
                share("untreated_120", 60, lambda arrival, now: now > arrival + 1.0),
            "definitive 30 min below arrival": share("definitive_management", 30, lambda arrival, now: now < arrival),
            "definitive 120 min below arrival": share("definitive_management", 120,
                                                      lambda arrival, now: now < arrival)}


# P2G-3 heart rate ------------------------------------------------------------------------------

HR_TIMES = (0, 30, 60, 120)


def _resolution(case: str, candidate: GICandidate, scenario: str) -> dict:
    """Two descriptive speeds of HR resolution in one run (neither is a criterion).

    - ``sympathetic_half_min``: first minute the sympathetic share of HR is at most half its
      arrival value. It depends on the intrinsic rate: a higher intrinsic rate leaves a smaller
      sympathetic share at the same arrival HR.
    - ``half_of_fall_min``: first minute HR has covered half of its own fall from arrival to the
      end of the run. HR - arrival HR is the same whatever the intrinsic rate while the sympathetic
      drive stays above its floor of zero; where it nears zero (``sympathetic_end_bpm``), HR stops at
      the intrinsic rate and the fall is shorter.
    """
    run_ = trajectory(case, candidate, scenario, times=range(DECISION_SCENARIOS[scenario]["minutes"] + 1))
    points = run_["points"]
    arrival, last = points[0], points[max(points)]
    fall = arrival["hr"] - last["hr"]
    return {"sympathetic_half_min": next((minute for minute, point in points.items()
                                          if minute and point["sympathetic_bpm"] <= arrival["sympathetic_bpm"] / 2),
                                         None),
            "half_of_fall_min": (next(minute for minute, point in points.items()
                                      if point["hr"] <= arrival["hr"] - fall / 2) if fall > 0 else None),
            "hr_end": last["hr"], "fall_bpm": fall, "sympathetic_end_bpm": last["sympathetic_bpm"]}


def hr_tables(runs: dict) -> dict:
    tables = {}
    for case in CASES:
        bands = gi_reference.case_bands(case)
        middle = trajectory(case, MIDDLE, "definitive_management")["points"][0]
        scenarios = {}
        for scenario in ENVELOPE_SCENARIOS:
            times = [minute for minute in HR_TIMES if minute <= DECISION_SCENARIOS[scenario]["minutes"]]
            decomposition = {}
            for label, candidate in (("intrinsic lower", replace(MIDDLE, intrinsic="lower")), ("middle", MIDDLE),
                                     ("intrinsic upper", replace(MIDDLE, intrinsic="upper"))):
                points = trajectory(case, candidate, scenario, times=times)["points"]
                decomposition[label] = {minute: {field: points[minute][field] for field in
                                                 ("hr", "intrinsic_bpm", "sympathetic_bpm", "beta_factor",
                                                  "other_chronotropic_bpm")} for minute in points}
            scenarios[scenario] = {"envelope": {minute: envelope(runs, case, scenario, "hr", minute)
                                                for minute in times},
                                   "decomposition": decomposition}
        factors = {"intrinsic_sinus_rate": _levels("intrinsic"),
                   "sympathetic_decay_tau_min": _profile_points("sympathetic_decay_tau_min"),
                   "sympathetic_per_pressure_deficit": _profile_points("sympathetic_per_pressure_deficit"),
                   "sympathetic_per_debt": _profile_points("sympathetic_per_debt")}
        tables[case] = {
            "arrival_hr": middle["hr"],
            "intrinsic_band": [bands["intrinsic_sinus_rate"].lower, bands["intrinsic_sinus_rate"].midpoint,
                               bands["intrinsic_sinus_rate"].upper],
            "sympathetic_band_bpm": [middle["hr"] - bands["intrinsic_sinus_rate"].upper,
                                     middle["hr"] - bands["intrinsic_sinus_rate"].midpoint,
                                     middle["hr"] - bands["intrinsic_sinus_rate"].lower],
            "scenarios": scenarios,
            "resolution": {decay: {level: _resolution(case, replace(candidate, intrinsic=level),
                                                      "definitive_management") for level in LEVELS}
                           for decay, candidate, _ in _profile_points("sympathetic_decay_tau_min")},
            "effects": {scenario: _effects(case, scenario, factors, "hr", HR_TIMES)
                        for scenario in ("untreated_120", "definitive_management")}}
    return tables


# P2G-4 untreated pressure -------------------------------------------------------------------------

BP_TIMES = (0, 15, 30, 60, 120)


def bp_tables(runs: dict) -> dict:
    tables = {}
    for case in CASES:
        reserve = gi_reference.case_bands(case)["pump_reserve"]
        factors = {
            "bleeding source (x rate)": [(f"x{scale:g}", MIDDLE, {"source_scale": scale, "status": SENSITIVITY})
                                         for scale in (0.5, 1.0, 2.0, 4.0)],
            "preload_fraction": _levels("preload"),
            "preload_curve_scale_ml": _profile_points("preload_curve_scale_ml"),
            "pump_preload_coupling": _profile_points("pump_preload_coupling"),
            "afterload_sensitivity": _profile_points("afterload_sensitivity"),
            "pump_reserve": [(f"{value:g}", MIDDLE, {"case_extra": {"pump_reserve": value}, "status": NOT_ASSESSED})
                             for value in (reserve.lower, reserve.upper)],
            "low_output_pressure_knee": _profile_points("low_output_pressure_knee"),
            "sbp_per_pressure_deficit": _profile_points("sbp_per_pressure_deficit"),
            "dbp_per_pressure_deficit": _profile_points("dbp_per_pressure_deficit")}
        tables[case] = {"envelopes": {field: {minute: envelope(runs, case, "untreated_120", field, minute)
                                              for minute in BP_TIMES} for field in ("sbp", "map")},
                        "effects": {field: _effects(case, "untreated_120", factors, field, BP_TIMES)
                                    for field in ("sbp", "map")}}
    return tables


# P2G-5 terminal collapse (synthetic) ---------------------------------------------------------------

#: Output patterns on the neutral synthetic arrival (bands.ARRIVAL): (output level, minutes at it).
#: The durations are chosen against the midpoint rule (threshold 0.3, gain 1, limit 15) so each
#: pattern shows its own behaviour; they are illustrations, not proposed limits.
COLLAPSE_PATTERNS = {
    "transient moderate low flow (0.25 for 10 min)": (0.25, 10),
    "sustained moderate low flow (0.25)": (0.25, 240),
    "profound low flow (0.1)": (0.1, 240),
    "recovery before substantial burden (0.15 for 10 min)": (0.15, 10),
    "recovery after substantial burden (0.15 for 26 min)": (0.15, 26),
}
COLLAPSE_MIDDLE = {"collapse_output_threshold": REGISTRY["collapse_output_threshold"].midpoint,
                   "collapse_burden_per_minute": REGISTRY["collapse_burden_per_minute"].midpoint,
                   "collapse_burden_limit": REGISTRY["collapse_burden_limit"].midpoint,
                   "collapse_repayment_tau_min": REGISTRY["collapse_repayment_tau_min"].midpoint}
BURDEN_TIMES = (0, 10, 26, 30, 60, 90, 120, 240)


def _collapse_run(episodes, rule: dict, horizon: int = 240) -> dict:
    """Output held at a level over each (start, stop, level) episode, 1 otherwise."""
    anchors = Anchors(**ARRIVAL)
    probes = []
    for index, (start, stop, level) in enumerate(episodes):
        probes.append(Drift(f"down{index}", "P", start, start + 1, level - 1.0))
        if stop < horizon:
            probes.append(Drift(f"up{index}", "P", stop, stop + 1, 1.0 - level))
    result = run(anchors, tuple(probes), horizon, replace(DEFAULT_PROFILE, **rule))
    arrest = next((state.minute for state in result.states if not state.R.pulse_present), None)
    burden = [state.aux.collapse_burden for state in result.states]
    return {"arrest_minute": arrest, "terminal_rhythm": result.states[-1].R.code.value if arrest else None,
            "peak_burden": max(burden),
            "burden_at": {minute: burden[minute] for minute in BURDEN_TIMES if minute < len(burden)}}


def _thousandths(value: float) -> int:
    scaled = round(value * 1000)
    if abs(value * 1000 - scaled) > 1e-6:
        raise ValueError(f"{value} is not exact in thousandths")
    return scaled


def _minutes_to_limit(threshold: float, gain: float, limit: float, output: float) -> int | None:
    """Whole minutes of burden accrual to the limit at a constant output, in exact arithmetic.

    burden += gain x (threshold - output) / threshold per minute, so the limit needs
    limit x threshold / (gain x (threshold - output)) minutes, rounded up. A simulated arrest comes
    one minute later (the minute the output takes to fall), and one more when this quotient is a
    whole number, because the model's floating-point sum stops just under the limit.
    """
    t, g, l, o = (_thousandths(value) for value in (threshold, gain, limit, output))
    if o >= t:
        return None
    return -(-(l * t) // (g * (t - o)))


def collapse_tables() -> dict:
    """Decision support for the collapse rule. Canonical GI runs keep it off (threshold None)."""
    analytic = []
    for threshold in REGISTRY["collapse_output_threshold"].points():
        for gain in REGISTRY["collapse_burden_per_minute"].points():
            for limit in REGISTRY["collapse_burden_limit"].points():
                row = {"threshold": threshold, "gain": gain, "limit": limit, "minutes_to_transition": {}}
                for output in (0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35):
                    row["minutes_to_transition"][output] = _minutes_to_limit(threshold, gain, limit, output)
                analytic.append(row)
    patterns = {name: _collapse_run(((0, minutes, level),), COLLAPSE_MIDDLE)
                for name, (level, minutes) in COLLAPSE_PATTERNS.items()}
    repayment = {}
    for tau in (None, *REGISTRY["collapse_repayment_tau_min"].points()):
        rule = {**COLLAPSE_MIDDLE, "collapse_repayment_tau_min": tau}
        repayment["none" if tau is None else f"{tau:g}"] = {
            "after 26 min at 0.15": _collapse_run(((0, 26, 0.15),), rule),
            "26 min at 0.15, 30 min recovered, 15 min at 0.15": _collapse_run(((0, 26, 0.15), (56, 71, 0.15)), rule)}
    rhythm = {option: _collapse_run(((0, 240, 0.1),), {**COLLAPSE_MIDDLE, "collapse_terminal_rhythm": option})[
        "terminal_rhythm"] for option in REGISTRY["collapse_terminal_rhythm"].options}
    return {"canonical_threshold": DEFAULT_PROFILE.collapse_output_threshold, "midpoint_rule": COLLAPSE_MIDDLE,
            "analytic_minutes": analytic, "patterns": patterns, "repayment": repayment,
            "terminal_rhythm_by_policy": rhythm}


# P2G-6 aggressive volume ---------------------------------------------------------------------------

def volume_grid(quick: bool = False) -> list[dict]:
    """aggressive_volume over the preload, congestion and reserve dimensions (kinetics at midpoint)."""
    rows = []
    levels = ("midpoint",) if quick else LEVELS
    scales = REGISTRY["preload_curve_scale_ml"].points()[1:2] if quick else REGISTRY["preload_curve_scale_ml"].points()
    knees = REGISTRY["congestion_preload_knee"].points()[1:2] if quick else REGISTRY["congestion_preload_knee"].points()
    gains = (REGISTRY["congestion_per_excess_preload"].points()[1:2] if quick
             else REGISTRY["congestion_per_excess_preload"].points())
    for case in CASES:
        reserve = gi_reference.case_bands(case)["pump_reserve"]
        for preload in levels:
            for scale in scales:
                for knee in knees:
                    for gain in gains:
                        for pump_reserve in (reserve.lower, reserve.upper):
                            candidate = replace(MIDDLE, preload=preload, profile={
                                **MIDDLE.profile, "preload_curve_scale_ml": scale, "congestion_preload_knee": knee,
                                "congestion_per_excess_preload": gain})
                            run_ = trajectory(case, candidate, "aggressive_volume",
                                              case_extra={"pump_reserve": pump_reserve},
                                              times=range(DECISION_SCENARIOS["aggressive_volume"]["minutes"] + 1))
                            rows.append(_volume_row(case, candidate, pump_reserve, run_))
    return rows


def _volume_row(case, candidate, pump_reserve, run_) -> dict:
    points = run_["points"]
    first, last = points[0], points[max(points)]
    peak = max(points, key=lambda minute: points[minute]["sbp"])
    added = last["V"] - first["V"]
    # Marginal responsiveness at the end: output gained by the next 500 mL-eq relative to the first
    # 500 mL-eq from arrival, on the curve as it stands (a model descriptor, not a criterion).
    position = last["preload_position"]
    scale = candidate.profile["preload_curve_scale_ml"]
    arrival = points[0]["preload_position"]
    gain_end = (1 - position) * -math.expm1(-500 / scale)
    gain_start = (1 - arrival) * -math.expm1(-500 / scale)
    return {"case": case, "preload_fraction": candidate.preload, "preload_curve_scale_ml": scale,
            "congestion_preload_knee": candidate.profile["congestion_preload_knee"],
            "congestion_per_excess_preload": candidate.profile["congestion_per_excess_preload"],
            "pump_reserve": pump_reserve, "stopped_at": run_["stopped_at"], "net_V_ml_eq": added,
            "arrival_sbp": first["sbp"], "peak_sbp": points[peak]["sbp"], "peak_minute": peak,
            "peak_map": max(point["map"] for point in points.values()),
            "peak_output": max(point["output"] for point in points.values()), "final_hr": last["hr"],
            "final_L": last["L"], "arrival_position": arrival, "final_position": position,
            "marginal_responsiveness": gain_end / gain_start if gain_start else None}


def volume_summary(rows: list[dict]) -> dict:
    """Per case and preload position x curve scale (the dimensions that move pressure and output):
    the read-outs, the range of lung water over the congestion dimensions and reserve, and the
    frozen-rule status. ``marginal_responsiveness`` is the output the next 500 mL-eq would add at
    the end, relative to the first 500 mL-eq from arrival: a model descriptor, not a criterion."""
    summary = {}
    for case in CASES:
        cells = {}
        for row in (row for row in rows if row["case"] == case):
            key = f"{row['preload_fraction']}|{row['preload_curve_scale_ml']:g}"
            cell = cells.setdefault(key, {"preload_fraction": row["preload_fraction"],
                                          "preload_curve_scale_ml": row["preload_curve_scale_ml"], "rows": []})
            cell["rows"].append(row)
        for cell in cells.values():
            mine = cell.pop("rows")
            first = mine[0]
            candidate = replace(MIDDLE, preload=first["preload_fraction"],
                                profile={**MIDDLE.profile, "preload_curve_scale_ml": first["preload_curve_scale_ml"]})
            cell.update({key: first[key] for key in ("arrival_sbp", "peak_sbp", "peak_map", "peak_output",
                                                      "final_hr", "arrival_position", "final_position",
                                                      "marginal_responsiveness", "net_V_ml_eq", "stopped_at")})
            cell["final_L"] = [min(row["final_L"] for row in mine), max(row["final_L"] for row in mine)]
            cell["status"] = assess(candidate)["status"]
            # P2F's design varies the preload position only at the default curve scale.
            cell["in_p2f_design"] = cell["preload_curve_scale_ml"] == DEFAULT_PROFILE.preload_curve_scale_ml
        summary[case] = sorted(cells.values(), key=lambda cell: (LEVELS.index(cell["preload_fraction"]),
                                                                 cell["preload_curve_scale_ml"]))
    congestion = {}
    for name in ("congestion_preload_knee", "congestion_per_excess_preload"):
        congestion[name] = {f"{point:g}": assess(replace(MIDDLE, profile={**MIDDLE.profile, name: point}))["status"]
                            for point in REGISTRY[name].points()}
    return {"cells": summary, "congestion_parameter_status": congestion}


# P2G-7 respiratory rate -----------------------------------------------------------------------------

RR_TIMES = (0, 30, 60, 120)
#: Shock severity at arrival as the P2F design spans it: (arrival debt, arrival delivery) levels.
SEVERITIES = {"mild (debt 0, delivery 1.0)": ("lower", "upper"),
              "moderate (debt 20, delivery 0.85)": ("midpoint", "midpoint"),
              "severe (debt 60, delivery 0.6)": ("upper", "lower")}


def rr_bounds(case: str) -> dict:
    """Where RR can go in this case over the RR band grid, read from ``derived.respiratory_rate``.

    With W = 0 (no GI module moves it), RR is the arrival RR less its metabolic share plus the
    metabolic drive now. Its ceiling (lactate without limit) is RR_arrival - the arrival drive +
    rr_metabolic_max; its floor (lactate under the threshold) is RR_arrival - the share. rr_max
    then caps the ceiling: the table reads the ceiling at each rr_max band point.
    """
    anchors = gi_reference.candidate_anchors(case, calibration.case_values(case, MIDDLE))
    state = run(anchors, (), 0, replace(DEFAULT_PROFILE, **MIDDLE.profile)).states[0]
    if state.W != 0.0:
        raise AssertionError("the bounds assume W = 0 at a GI arrival")
    rows = []
    for cap in REGISTRY["rr_metabolic_max"].points():
        for gain in REGISTRY["rr_per_lactate"].points():
            for threshold in REGISTRY["lactate_drive_threshold_mmol_l"].points():
                for floor in REGISTRY["rr_ventilatory_floor"].points():
                    row = {"rr_metabolic_max": cap, "rr_per_lactate": gain, "lactate_drive_threshold_mmol_l": threshold,
                           "rr_ventilatory_floor": floor}
                    for rr_max in sorted(set(REGISTRY["rr_max"].points())):
                        profile = replace(DEFAULT_PROFILE, rr_metabolic_max=cap, rr_per_lactate=gain,
                                          lactate_drive_threshold_mmol_l=threshold, rr_ventilatory_floor=floor,
                                          rr_max=rr_max)
                        row[f"ceiling at rr_max {rr_max:g}"] = respiratory_rate(state, anchors, profile, 1e6)
                        row["floor"] = respiratory_rate(state, anchors, profile, 0.0)
                    rows.append(row)
    ceilings = sorted({key for row in rows for key in row if key.startswith("ceiling")})
    by_cap = {f"{cap:g}": {key: [min(row[key] for row in rows if row["rr_metabolic_max"] == cap),
                                 max(row[key] for row in rows if row["rr_metabolic_max"] == cap)]
                           for key in (*ceilings, "floor")}
              for cap in REGISTRY["rr_metabolic_max"].points()}
    return {"arrival_rr": anchors.respiratory_rate, "arrival_lactate": anchors.lactate, "by_cap": by_cap,
            "rows": rows}


def rr_tables(runs: dict) -> dict:
    tables = {}
    for case in CASES:
        severities = {}
        for label, (debt, delivery) in SEVERITIES.items():
            candidate = replace(MIDDLE, debt=debt, delivery=delivery)
            severities[label] = {
                scenario: {minute: {field: point[field] for field in ("rr", "rr_ventilatory", "rr_metabolic",
                                                                       "lactate")}
                           for minute, point in trajectory(case, candidate, scenario, times=RR_TIMES)["points"].items()}
                for scenario in ("untreated_120", "definitive_management")}
            severities[label]["status"] = assess(candidate)["status"]
        factors = {name: _profile_points(name) for name in
                   ("rr_per_lactate", "rr_metabolic_max", "rr_ventilatory_floor", "lactate_drive_threshold_mmol_l")}
        tables[case] = {
            "envelopes": {scenario: {minute: envelope(runs, case, scenario, "rr", minute) for minute in RR_TIMES}
                          for scenario in ("untreated_120", "definitive_management")},
            "severities": severities,
            "bounds": rr_bounds(case),
            "effects": {scenario: _effects(case, scenario, factors, "rr", RR_TIMES)
                        for scenario in ("untreated_120", "definitive_management")},
            "ceiling": max(point["rr"] for (key, case_, scenario), run_ in runs.items() if case_ == case
                           for point in run_["points"].values()),
            "floor": min(point["rr"] for (key, case_, scenario), run_ in runs.items() if case_ == case
                         for point in run_["points"].values())}
    return tables


# P2G-11 the preload-0.2 edge -----------------------------------------------------------------------

def preload_edge() -> dict:
    """57m around preload position 0.2: the HR1 probe, the case's own untreated bleed, neighbours."""
    case = "gi_bleed_57m"
    profile = replace(DEFAULT_PROFILE, **MIDDLE.profile)
    rows = []
    for position in (0.18, 0.2, 0.22, 0.25, 0.3, 0.35):
        for scale in REGISTRY["preload_curve_scale_ml"].points():
            values = {**calibration.case_values(case, MIDDLE), "preload_fraction": position}
            anchors = gi_reference.candidate_anchors(case, values)
            filling = -scale * math.log1p(-position)
            row = {"preload_fraction": position, "preload_curve_scale_ml": scale, "arrival_filling_ml_eq": filling}
            for label, rate in (("probe 8 mL/min", 8.0), ("probe 4 mL/min", 4.0), ("case source 2.5 mL/min", None)):
                if rate is None:
                    items, minutes = scenario_contributors(case, "untreated_120"), 120
                else:
                    items, minutes = (Drift("loss", "V", 0, 30, -rate),), 30
                try:
                    run(anchors, items, minutes, replace(profile, preload_curve_scale_ml=scale))
                    row[label] = None
                except UnresolvedBoundary as error:
                    row[label] = int(str(error).split(":")[0].split()[-1])
            rows.append(row)
    return {"case": case, "rows": rows}


# P2G-9 PL2 -------------------------------------------------------------------------------------------

def pl2_analysis() -> dict:
    """PL2 as frozen (check_preload), clause by clause, around the region it rejects.

    Clause 1: 500 mL on a pump at 0.6 gains no more output than on a normal pump.
    Clause 2: 500 mL on a pump at 0.6 does not restore the arrival output (output stays < 1).
    Both read the neutral probe arrival at the profile's default preload position.
    """
    from .calibration import NEUTRAL, _output
    rows = []
    for position in (0.3, 0.35, 0.4, 0.5, 0.7):
        for scale in (600.0, 700.0, 833.3333333333334, 1000.0, 1200.0, 1500.0):
            for coupling in REGISTRY["pump_preload_coupling"].points():
                profile = replace(DEFAULT_PROFILE, arrival_preload_fraction=position, preload_curve_scale_ml=scale,
                                  pump_preload_coupling=coupling)
                normal = _output(profile, NEUTRAL, V=500.0) - _output(profile, NEUTRAL)
                weak_after = _output(profile, NEUTRAL, P=0.6, V=500.0)
                weak = weak_after - _output(profile, NEUTRAL, P=0.6)
                rows.append({"arrival_preload_fraction": position, "preload_curve_scale_ml": scale,
                             "pump_preload_coupling": coupling, "gain_normal_pump": normal,
                             "gain_pump_0_6": weak, "output_pump_0_6_after_500": weak_after,
                             "clause_1_holds": weak <= normal, "clause_2_holds": weak_after < 1.0,
                             "in_registry_band": position in REGISTRY["arrival_preload_fraction"].points()
                             and scale in REGISTRY["preload_curve_scale_ml"].points()})
    return {"rule": calibration.FROZEN_RULES["PL2"].__dict__, "rows": rows}


# P2G-10 arrival-D reachability ------------------------------------------------------------------------

def reachability_analysis() -> dict:
    """What arrival_D <= gain x demand x tau_D would exclude. It is not a rule: nothing applies it.

    In the model, dD/dt = gain x max(0, demand - delivery) - D / tau_D, so above that bound D
    falls whatever the delivery, even at none; below it, a sustained deficit can reach it.
    """
    design = calibration.gi_candidates()
    demand = 1.0
    rows = []
    for candidate in design:
        tau = candidate.profile.get("debt_clearance_tau_min", DEFAULT_PROFILE.debt_clearance_tau_min)
        gain = candidate.profile.get("debt_per_delivery_deficit", DEFAULT_PROFILE.debt_per_delivery_deficit)
        debt = calibration.case_values(CASES[0], candidate)["arrival_oxygen_debt"]
        if debt > gain * demand * tau:
            rows.append({"candidate": candidate.key(), "arrival_D": debt, "bound": gain * demand * tau,
                         "p2f": p2f_rejection(candidate) or ADMISSIBLE})
    bands = []
    for tau in REGISTRY["debt_clearance_tau_min"].points():
        for gain in REGISTRY["debt_per_delivery_deficit"].points():
            band = gi_reference.case_bands(CASES[0])["arrival_oxygen_debt"]
            bands.append({"debt_clearance_tau_min": tau, "debt_per_delivery_deficit": gain,
                          "bound_at_demand_1": gain * tau,
                          "excluded_arrival_D_levels": [level for level, value in
                                                        zip(LEVELS, (band.lower, band.midpoint, band.upper))
                                                        if value > gain * tau]})
    return {"excluded_design_points": len(rows), "all_rejected_by_p2f": all(row["p2f"] != ADMISSIBLE for row in rows),
            "rows": rows, "by_kinetics": bands}


# The pack ---------------------------------------------------------------------------------------

#: Not hashed: modules the pack's numbers cannot depend on. The renderer only writes the pack into
#: the faculty document; the P2I decision slices, the P2I-2 faculty constraints and the P2I-2P,
#: P2I-2Q and P2I-2S probes read the pack, never the other way round (a test runs the pack and
#: checks that it never loads them).
PACK_DIGEST_EXCLUDED = ("clinical_core/decision_pack_markdown.py", "clinical_core/lactate_slice.py",
                        "clinical_core/faculty_constraints.py", "clinical_core/lactate_constraints.py",
                        "clinical_core/oxygen_probes.py", "clinical_core/hemodynamic_probes.py",
                        "clinical_core/haemorrhage_probes.py", "clinical_core/blood_probes.py",
                        "clinical_core/blood_anchors.py", "clinical_core/blood_constraints.py",
                        "clinical_core/blood_filter_report.py", "clinical_core/blood_extension.py",
                        "clinical_core/blood_extension_report.py")


def pack_sources() -> dict[str, str]:
    """Every shadow-core source the tables can depend on (the model, the harness and this module), by hash."""
    package = calibration.REPOSITORY / "clinical_core"
    paths = sorted(path.relative_to(calibration.REPOSITORY).as_posix() for path in package.rglob("*.py")
                   if "__pycache__" not in path.parts and path.is_file() and not path.name.startswith("."))
    return {path: hashlib.sha256(calibration._source_bytes(path)).hexdigest()
            for path in paths if path not in PACK_DIGEST_EXCLUDED}


def pack_digest() -> str:
    """What the tables were generated from: the calibration freeze, the core sources and the scenarios."""
    scenarios = {name: [spec["minutes"], {str(minute): order for minute, order in spec["orders"].items()}]
                 for name, spec in DECISION_SCENARIOS.items()}
    text = json.dumps({"freeze": calibration.frozen_digest(), "scenarios": scenarios, "sources": pack_sources()},
                      sort_keys=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def report(quick: bool = False) -> dict:
    # Recorded first: the digests name the code and inputs the tables are computed from.
    digests = {"pack_digest": pack_digest(), "freeze_digest": calibration.frozen_digest()}
    runs = envelope_runs(quick)
    grid = volume_grid(quick)
    return {**digests, "admissible_candidates": len(admissible(quick)), "quick": quick,
            "lactate": lactate_tables(runs), "hr": hr_tables(runs), "bp": bp_tables(runs),
            "collapse": collapse_tables(), "volume": {"rows": grid, "summary": volume_summary(grid)},
            "rr": rr_tables(runs), "preload_edge": preload_edge(), "pl2": pl2_analysis(),
            "reachability": reachability_analysis()}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    result = report(args.quick)
    text = json.dumps(result, indent=1, sort_keys=True, default=str)
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "decision_pack.json").write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
