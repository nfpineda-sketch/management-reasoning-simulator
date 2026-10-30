"""P2I-1: the GI lactate decision slice. Decision support only.

    python -m clinical_core.lactate_slice [--quick] [--out <directory outside the repository>]

Shadow and offline. It reruns P2G's structurally admissible region (``decision_pack.admissible``)
in four clinical trajectory questions and reports what the model does with lactate, so faculty
can make the first numerical decision. It never selects, ranks or recommends a value, never
marks anything FACULTY_APPROVED, never touches a registry, the golden or a band, and never uses
the family engine's lactate to classify a candidate: the engine supplies each scenario's inputs
(the frozen path of P2G-1) and, separately and last, a reference trajectory labelled as such.

The scenarios, all 120 min, use existing orders and existing core inputs; nothing here is new
physiology:
- L1 untreated active bleeding: no order;
- L2 transient, partial resuscitation: 2 L saline over 20 min, no haemostasis;
- L3 definitive control and adequate resuscitation: P2G's definitive management (2 units of red
  cells over 60 min, a PPI and urgent endoscopy; the engine performs it at minute 60);
- L4 haemostasis without perfusion recovery: a PPI and urgent endoscopy with no volume. The
  family engine defers that endoscopy (SBP below 90), so L4 is a MANUAL COUNTERFACTUAL
  COMPOSITION: L4's own engine-produced inputs plus an endoscopic haemostasis added by hand at
  L3's minute, under its own id (COUNTERFACTUAL_HEMOSTASIS_ID). The engine never produces it.
  L1-L3 are engine-produced trajectories; L4 is labelled counterfactual wherever it appears and
  is never pooled with them.

The lactate model is linear given the path of the delivery deficit s (KD-S1, P2E-2, with the
P2I-2AC and P2I-2AD debt semantics): D' = g s while s > 0 at the start of the minute (accrued,
never repaid), D' = -D / tau_D across a minute without deficit at its start and its end, no change
across a minute that crosses into a deficit, and X' = k D - X / tau_L with k the debt-to-lactate
gain (its own parameter since P2I-2AD), lactate = baseline + X. So, given s,
the excess X splits exactly into what is left of the arrival excess, what the arrival debt
still produces (the arrival debt is repaid only in the minutes without a deficit) and what the
deficit since arrival produced. The split is exact for these recurrences; it is not a causal
attribution between parameters, which interact through s (the deficit depends on the
haemodynamics the parameters move).

Thresholds such as 0.5 and 2 mmol/L are presentation bins for the tables, not criteria.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import replace
from pathlib import Path

from . import calibration, decision_pack, gi_reference
from .calibration import REGISTRY, GICandidate
from .decision_pack import MIDDLE
from .derived import DEFAULT_PROFILE, derive, effective_delivery, effective_oxygen_deficit, lactate_baseline
from .integration import run
from .legacy_adapter import contributors_from_legacy
from .logistics import EndoscopicHemostasis
from .shadow import SCENARIOS as GI_SCENARIOS
from .state import UnresolvedBoundary

CASES = gi_reference.GI_CASES
TIMES = (0, 15, 30, 60, 90, 120)
MINUTES = 120
#: Presentation bins (mmol/L), not criteria.
FLAT, SUBSTANTIAL, CLEAR_FALL = 0.5, 2.0, 0.5

L1, L2, L3, L4 = "L1", "L2", "L3", "L4"
#: How each scenario's inputs arise. Only L4 is composed by hand.
ENGINE_PRODUCED = "engine-produced inputs (frozen family-engine path)"
COUNTERFACTUAL = ("manual counterfactual composition: the endoscopic haemostasis is added by hand at L3's "
                  "minute; the family engine defers this endoscopy and never produces it")
TRAJECTORY_KIND = {L1: ENGINE_PRODUCED, L2: ENGINE_PRODUCED, L3: ENGINE_PRODUCED, L4: COUNTERFACTUAL}
#: The id of the haemostasis added by hand in L4; the engine's own is "gastroenterology_endoscopy".
COUNTERFACTUAL_HEMOSTASIS_ID = "p2i_counterfactual_manual_hemostasis"
SCENARIO_TITLES = {
    L1: "untreated active bleeding",
    L2: "transient, partial resuscitation (2 L saline over 20 min, bleeding continues)",
    L3: "definitive control and adequate resuscitation (2 units over 60 min, PPI, endoscopy)",
    L4: "haemostasis without perfusion recovery (PPI and endoscopy, no volume): MANUAL COUNTERFACTUAL COMPOSITION",
}
ORDERS = {
    L1: {"minutes": MINUTES, "orders": {}},
    L2: {"minutes": MINUTES, "orders": {0: "Give 2000 mL normal saline IV over 20 minutes."}},
    L3: GI_SCENARIOS["definitive_management"],
    L4: {"minutes": MINUTES, "orders": {0: "Give pantoprazole 80 mg IV. Consult gastroenterology for urgent endoscopy."}},
}
#: The parameters the sensitivity reads; each with where its levels come from.
DESIGN_FACTORS = ("arrival_oxygen_debt", "arrival_lactate_excess", "arrival_delivery_ratio",
                  "debt_clearance_tau_min", "lactate_per_output_deficit", "lactate_clearance_tau_min")
PROBE_FACTORS = {"debt_per_delivery_deficit": tuple(REGISTRY["debt_per_delivery_deficit"].points()),
                 "metabolic_demand_baseline": (0.9, 1.0, 1.1)}
#: Repository-truth items relevant to lactate, in the order the tables show them.
TRUTH_ITEMS = ("lactate_mmol_l", "sbp", "dbp", "map", "hr", "hb_g_dl", "spo2", "crt_s", "extremities",
               "peripheral_perfusion", "mental_status", "neurological_exam", "active_bleeding",
               "prehospital_therapy")


# Inputs -------------------------------------------------------------------------------------

def endoscopy_minute(case: str) -> int:
    """The minute the family engine performs the endoscopy in L3 (its own rule, unchanged)."""
    minute = calibration._legacy_run(case, ORDERS[L3]).final_state["family_state"].get("endoscopy_at")
    if minute is None:
        raise AssertionError(f"{case}: the L3 endoscopy no longer happens within {MINUTES} min")
    return int(minute)


_INPUTS: dict = {}


def scenario_inputs(case: str, scenario: str) -> tuple:
    """The scenario's core inputs from the frozen family-engine path; L4 adds, by hand, L3's haemostasis."""
    if (case, scenario) not in _INPUTS:
        legacy = calibration._legacy_run(case, ORDERS[scenario])
        items = contributors_from_legacy(legacy)
        if scenario == L4:
            if legacy.final_state["family_state"].get("endoscopy_at") is not None:
                raise AssertionError(f"{case}: the engine now performs the L4 endoscopy itself; L4 needs no composition")
            items = (*items, EndoscopicHemostasis(COUNTERFACTUAL_HEMOSTASIS_ID, endoscopy_minute(case)))
        _INPUTS[(case, scenario)] = items
    return _INPUTS[(case, scenario)]


# Runs ---------------------------------------------------------------------------------------

def slice_run(case: str, candidate: GICandidate, scenario: str, *, profile_extra: dict | None = None,
              case_extra: dict | None = None, keep_states: bool = False) -> dict:
    """One 120-min run: lactate and D every minute, haemodynamics at TIMES. A run whose output
    reaches zero with a pulse (collapse off, as in every canonical GI run) stops there."""
    values = {**calibration.case_values(case, candidate), **(case_extra or {})}
    anchors = gi_reference.candidate_anchors(case, values)
    profile = replace(DEFAULT_PROFILE, **{**candidate.profile, **(profile_extra or {})})
    if profile.oxygen_extraction_reserve != 1.0 and "arrival_delivery_ratio" not in (case_extra or {}):
        # P2I-2P: only reserve x arrival_delivery_ratio reaches D, and the GI band is in units of the
        # critical delivery; a reserve needs the band's reading stated, never applied silently.
        raise ValueError("an extraction reserve other than 1 needs arrival_delivery_ratio stated in case_extra "
                         "(the GI band read as fixed, or re-anchored as ratio / reserve)")
    items = scenario_inputs(case, scenario)
    stopped = None
    try:
        result = run(anchors, items, MINUTES, profile)
    except UnresolvedBoundary as error:
        stopped = int(str(error).split(":")[0].split()[-1])
        result = run(anchors, items, stopped - 1, profile)
    states = result.states
    baseline = lactate_baseline(anchors)
    floor = min(profile.lactate_floor, anchors.lactate)
    lactate = [max(floor, baseline + state.aux.lactate_excess_mmol_l) for state in states]
    points = {}
    for minute in TIMES:
        if minute < len(states):
            derived = derive(states[minute], anchors, profile)
            if abs(derived.lactate - lactate[minute]) > 1e-9:
                raise AssertionError("the slice's lactate is no longer the core's")
            points[minute] = {"lactate": lactate[minute], "D": states[minute].D, "map": derived.map,
                              "output": derived.output_rel, "V": states[minute].V,
                              "delivery": effective_delivery(derived.delivery_rel, anchors),
                              "demand": anchors.metabolic_demand_baseline}
    out = {"stopped_at": stopped, "lactate": lactate, "D": [state.D for state in states], "points": points,
           "baseline": baseline}
    if keep_states:
        out.update(states=states, anchors=anchors, profile=profile)
    return out


def region_runs(quick: bool = False) -> dict:
    """Every admissible candidate (P2G's region) in every scenario, for both cases. P2I-2AE: an arrival the core refuses
    at the default gain runs without the debt-driven drive, which reaches nothing the slice reads (no HR here)."""
    return {(candidate.key(), case, scenario): slice_run(case, candidate, scenario,
                                                         profile_extra=decision_pack.run_profile_extra(candidate))
            for candidate in decision_pack.admissible(quick) for case in CASES for scenario in ORDERS}


def _cases_runs(runs: dict, case: str, scenario: str) -> list:
    return [(key, run_) for (key, case_, scenario_), run_ in runs.items() if case_ == case and scenario_ == scenario]


# P2I-1.3 trajectory tables -------------------------------------------------------------------

def _quantile(ordered: list, q: float) -> float:
    return ordered[min(len(ordered) - 1, max(0, round(q * (len(ordered) - 1))))]


def trajectory_table(runs: dict, case: str, scenario: str) -> dict:
    """Per time: the spread over the region and the shares moving from arrival (runs that reach it)."""
    table = {}
    members = _cases_runs(runs, case, scenario)
    for minute in TIMES:
        reached = [(key, run_["lactate"][0], run_["lactate"][minute]) for key, run_ in members
                   if minute < len(run_["lactate"])]
        values = sorted(now for _, _, now in reached)
        changes = [now - arrival for _, arrival, now in reached]
        n = len(values)
        if not n:
            table[minute] = {"n": 0, "stopped_before": len(members)}
            continue
        table[minute] = {
            "n": n, "stopped_before": len(members) - n,
            "min": values[0], "p10": _quantile(values, 0.1), "median": _quantile(values, 0.5),
            "p90": _quantile(values, 0.9), "max": values[-1],
            "rising": sum(change > 1e-9 for change in changes) / n,
            "falling": sum(change < -1e-9 for change in changes) / n,
            "changed_more_than_1": sum(abs(change) > 1.0 for change in changes) / n,
            "changed_more_than_2": sum(abs(change) > 2.0 for change in changes) / n}
    return table


# P2I-1.5 behaviour classes -------------------------------------------------------------------

FALLS, FLAT_CLASS, MODEST, SUBSTANTIAL_CLASS, STOPPED = ("A falls", "B approximately flat", "C rises modestly",
                                                         "D rises substantially", "stopped (output reached zero)")
PROMPT, LATER, ELEVATED_RESTORED, ELEVATED_UNRESTORED = (
    "E falls clearly within 30 min", "E' falls clearly after 30 min",
    "F stays elevated with delivery restored", "F' stays elevated with delivery not restored")


def change_class(run_: dict, minute: int) -> str:
    if minute >= len(run_["lactate"]):
        return STOPPED
    change = run_["lactate"][minute] - run_["lactate"][0]
    if change <= -FLAT:
        return FALLS
    if change < FLAT:
        return FLAT_CLASS
    return MODEST if change < SUBSTANTIAL else SUBSTANTIAL_CLASS


def first_clear_fall(run_: dict) -> int | None:
    """The first minute lactate is at least CLEAR_FALL below arrival, or None within the run."""
    arrival = run_["lactate"][0]
    return next((minute for minute, value in enumerate(run_["lactate"]) if value <= arrival - CLEAR_FALL), None)


def recovery_class(run_: dict) -> str:
    fall = first_clear_fall(run_)
    if fall is not None:
        return PROMPT if fall <= 30 else LATER
    final = run_["points"].get(MINUTES)
    restored = final is not None and final["delivery"] >= final["demand"]
    return ELEVATED_RESTORED if restored else ELEVATED_UNRESTORED


_CANDIDATES: dict = {}


def candidate_of(key: str) -> GICandidate:
    if not _CANDIDATES:
        _CANDIDATES.update((candidate.key(), candidate) for candidate in calibration.gi_candidates())
    return _CANDIDATES[key]


def _levels_of(key: str) -> dict:
    candidate = candidate_of(key)
    return {"arrival_oxygen_debt": candidate.debt, "arrival_lactate_excess": candidate.excess,
            "arrival_delivery_ratio": candidate.delivery,
            **{name: f"{candidate.profile[name]:g}" for name in decision_pack.KINETICS}}


def _composition(keys: list) -> dict:
    """For a class: the share of its members at each level of each factor."""
    composition = {}
    for factor in DESIGN_FACTORS:
        counts: dict = {}
        for key in keys:
            level = _levels_of(key)[factor]
            counts[level] = counts.get(level, 0) + 1
        composition[factor] = {level: count / len(keys) for level, count in sorted(counts.items())}
    return composition


def classes(runs: dict, case: str) -> dict:
    """Clinically interpretable bins of the region's runs (counts and where they come from)."""
    result = {}
    for scenario in (L1, L2):
        for minute in (60, MINUTES):
            members: dict = {}
            for key, run_ in _cases_runs(runs, case, scenario):
                members.setdefault(change_class(run_, minute), []).append(key)
            deteriorated = sum(1 for key in members.get(FALLS, [])
                               if runs[(key, case, scenario)]["points"][minute]["delivery"]
                               < runs[(key, case, scenario)]["points"][0]["delivery"])
            result[f"{scenario} at {minute} min"] = {
                "classes": {name: {"n": len(keys), "composition": _composition(keys)}
                            for name, keys in sorted(members.items())},
                "falls_while_delivery_fell": deteriorated}
    for scenario in (L3, L4):
        members = {}
        for key, run_ in _cases_runs(runs, case, scenario):
            members.setdefault(recovery_class(run_), []).append(key)
        result[f"{scenario} over {MINUTES} min"] = {
            "classes": {name: {"n": len(keys), "composition": _composition(keys)}
                        for name, keys in sorted(members.items())}}
    return result


# P2I-1.4 mechanism decomposition --------------------------------------------------------------

def decomposition(case: str, candidate: GICandidate, scenario: str) -> dict:
    """The exact split of the excess for one run, given its deficit path (see the module docstring)."""
    run_ = slice_run(case, candidate, scenario, keep_states=True,
                     profile_extra=decision_pack.run_profile_extra(candidate))
    profile, states = run_["profile"], run_["states"]
    tau_d, tau_l, gain = profile.debt_clearance_tau_min, profile.lactate_clearance_tau_min, \
        profile.lactate_per_output_deficit
    g, k = profile.debt_per_delivery_deficit, profile.debt_to_lactate_gain
    a, b = 1.0 - 1.0 / tau_l, 1.0 - 1.0 / tau_d
    anchors, reserve = run_["anchors"], profile.oxygen_extraction_reserve
    arrival_debt_left, excess0 = states[0].D, states[0].aux.lactate_excess_mmol_l
    from_arrival_debt, from_new_deficit, accrued, repaid = 0.0, 0.0, 0.0, 0.0
    rows = {}
    for minute, state in enumerate(states):
        excess = state.aux.lactate_excess_mmol_l
        arrival_excess_left = excess0 * a ** minute
        if abs(arrival_excess_left + from_arrival_debt + from_new_deficit - excess) > 1e-9:
            raise AssertionError("the decomposition no longer adds up to the core's excess")
        if minute in TIMES:
            point = run_["points"][minute]
            rows[minute] = {
                "lactate": run_["lactate"][minute], "baseline": run_["baseline"],
                "arrival_excess_left": arrival_excess_left, "from_arrival_debt": from_arrival_debt,
                "from_deficit_since_arrival": from_new_deficit, "D": state.D,
                "D_arrival_left": arrival_debt_left, "D_since_arrival": state.D - arrival_debt_left,
                "D_accrued_so_far": accrued, "D_repaid_so_far": repaid,
                "delivery": point["delivery"], "demand": point["demand"],
                "deficit": max(0.0, point["demand"] - point["delivery"])}
        if minute + 1 < len(states):
            # The core's minute (P2I-2AC, P2I-2AD): with a deficit at its start the debt accrues and nothing
            # is repaid, the arrival debt included; without one at its start or its end it all repays
            # first-order; crossing into a deficit it neither accrues nor repays.
            after = states[minute + 1]
            delivery = effective_delivery(derive(state, anchors, profile).delivery_rel, anchors)
            deficit = effective_oxygen_deficit(after.aux.oxygen_demand, delivery, reserve)
            end = effective_oxygen_deficit(after.aux.oxygen_demand,
                                           effective_delivery(derive(after, anchors, profile).delivery_rel, anchors),
                                           reserve)
            if deficit > 0.0:
                accrued += after.D - state.D
                next_left = arrival_debt_left
            elif end == 0.0:
                repaid += state.D - after.D
                next_left = arrival_debt_left * b
            else:
                next_left = arrival_debt_left
            from_arrival_debt = from_arrival_debt * a + k * arrival_debt_left
            from_new_deficit = from_new_deficit * a + k * (state.D - arrival_debt_left)
            arrival_debt_left = next_left
    return {"candidate": candidate.key(), "stopped_at": run_["stopped_at"],
            "parameters": {"debt_clearance_tau_min": tau_d, "debt_per_delivery_deficit": g,
                           "lactate_per_output_deficit": gain, "lactate_clearance_tau_min": tau_l,
                           "production_per_debt_unit_per_min": k,
                           **{name: getattr(run_["anchors"], name) for name in
                              ("arrival_oxygen_debt", "arrival_lactate_excess", "arrival_delivery_ratio",
                               "metabolic_demand_baseline")}},
            "rows": rows}


def representatives(runs: dict, case: str) -> dict:
    """Low, middle and high of L1 at 60 min, each decomposed in L1 and L3."""
    members = [(run_["lactate"][60], key) for key, run_ in _cases_runs(runs, case, L1) if 60 < len(run_["lactate"])]
    members.sort()
    chosen = {"low": members[0][1], "middle": MIDDLE.key(), "high": members[-1][1]}
    return {label: {scenario: decomposition(case, candidate_of(key), scenario) for scenario in (L1, L3)}
            for label, key in chosen.items()}


# P2I-1.7 D and lactate apart ------------------------------------------------------------------

def dissociation(runs: dict, case: str) -> dict:
    """Runs in which D and lactate move apart, with a few examples each (not judged invalid)."""
    def examples(rows):
        rows.sort(key=lambda row: row[0])
        picks = [rows[0], rows[len(rows) // 2], rows[-1]] if len(rows) >= 3 else rows
        return [{"candidate": key, "D_from": d0, "D_to": d1, "lactate_from": l0, "lactate_to": l1}
                for _, key, d0, d1, l0, l1 in picks]

    def window(scenario, start, end, test, sort):
        rows = []
        for key, run_ in _cases_runs(runs, case, scenario):
            if end < len(run_["lactate"]):
                d0, d1, l0, l1 = run_["D"][start], run_["D"][end], run_["lactate"][start], run_["lactate"][end]
                if test(d0, d1, l0, l1, run_):
                    rows.append((sort(d0, d1, l0, l1), key, d0, d1, l0, l1))
        total = sum(1 for _, run_ in _cases_runs(runs, case, scenario) if end < len(run_["lactate"]))
        return {"n": len(rows), "of": total, "examples": examples(rows) if rows else []}

    return [{"pattern": pattern, **found} for pattern, found in (
        ("L1 0-60 min: D rises while lactate falls", window(
            L1, 0, 60, lambda d0, d1, l0, l1, r: d1 > d0 and l1 < l0, lambda d0, d1, l0, l1: l1 - l0)),
        ("L1 0-120 min: D rises while lactate falls", window(
            L1, 0, MINUTES, lambda d0, d1, l0, l1, r: d1 > d0 and l1 < l0, lambda d0, d1, l0, l1: l1 - l0)),
        ("L3 0-120 min: D falls while lactate stays within 0.5 mmol/L of arrival or above", window(
            L3, 0, MINUTES, lambda d0, d1, l0, l1, r: d1 < d0 and l1 > l0 - FLAT, lambda d0, d1, l0, l1: d1 - d0)),
        ("L4 0-120 min: D stays at or above arrival while lactate moves less than 0.5 mmol/L", window(
            L4, 0, MINUTES, lambda d0, d1, l0, l1, r: d1 >= d0 and abs(l1 - l0) < FLAT,
            lambda d0, d1, l0, l1: d1 - d0)))]


# P2I-1.8 parameter impact ---------------------------------------------------------------------

READOUTS = {
    "L1 change at 60 min (mmol/L)": (L1, lambda run_: run_["lactate"][60] - run_["lactate"][0]
                                     if 60 < len(run_["lactate"]) else None),
    "L3 first clear fall (min; 121 = not within 120)": (L3, lambda run_: first_clear_fall(run_)
                                                         if first_clear_fall(run_) is not None else 121),
    "L3 lactate at 120 min (mmol/L)": (L3, lambda run_: run_["lactate"][MINUTES]
                                       if MINUTES < len(run_["lactate"]) else None),
}


def _impact(spread: float, readout: str) -> str:
    high, medium = (30.0, 10.0) if "(min" in readout else (1.0, 0.3)
    return "HIGH" if spread >= high else "MEDIUM" if spread >= medium else "LOW"


def _direction(values: list) -> str:
    if values[-1] > values[0] and all(x <= y for x, y in zip(values, values[1:])):
        return "increases it"
    if values[-1] < values[0] and all(x >= y for x, y in zip(values, values[1:])):
        return "decreases it"
    return "non-monotonic" if values[-1] != values[0] else "no effect"


def sensitivity(runs: dict, case: str) -> dict:
    """Main effects over the region (median of the read-out at each level of a design factor) and,
    for the two factors the region does not vary, one-at-a-time probes around MIDDLE."""
    order = {"lower": 0, "midpoint": 1, "upper": 2}
    table = {}
    for readout, (scenario, measure) in READOUTS.items():
        rows = {}
        members = [(key, measure(run_)) for key, run_ in _cases_runs(runs, case, scenario)]
        for factor in DESIGN_FACTORS:
            by_level: dict = {}
            for key, value in members:
                if value is not None:
                    by_level.setdefault(_levels_of(key)[factor], []).append(value)
            levels = sorted(by_level, key=lambda level: order.get(level, 0) if level in order else float(level))
            medians = [_quantile(sorted(by_level[level]), 0.5) for level in levels]
            spread = max(medians) - min(medians)
            rows[factor] = {"source": "main effect over the admissible region",
                            "levels": dict(zip(levels, medians)), "spread": spread,
                            "impact": _impact(spread, readout), "direction": _direction(medians)}
        for factor, points in PROBE_FACTORS.items():
            values = []
            for point in points:
                options = ({"profile_extra": {factor: point}} if factor == "debt_per_delivery_deficit"
                           else {"case_extra": {factor: point}})
                values.append(measure(slice_run(case, MIDDLE, scenario, **options)))
            present = [value for value in values if value is not None]
            spread = max(present) - min(present) if present else 0.0
            rows[factor] = {"source": "one-at-a-time probe around the middle candidate (the region does not vary it)",
                            "levels": {f"{point:g}": value for point, value in zip(points, values)},
                            "spread": spread, "impact": _impact(spread, readout),
                            "direction": _direction(present) if present else "no effect"}
        table[readout] = [{"factor": factor, **row}
                          for factor, row in sorted(rows.items(), key=lambda item: -item[1]["spread"])]
    return table


# P2I-1.6 worksheet support, P2I-1.1 truth and P2I-1.9 legacy reference ------------------------

def worksheet_support(runs: dict, case: str) -> dict:
    """What the model offers for FD-LAC-02/03/04/05 and 06 (model-only; nothing is selected)."""
    untreated = trajectory_table(runs, case, L1)[60]
    falls = [first_clear_fall(run_) for _, run_ in _cases_runs(runs, case, L3)]
    bins = {"within 15 min": 0, "15-30 min": 0, "30-60 min": 0, "after 60 min": 0, "not within 120 min": 0}
    for fall in falls:
        bins["not within 120 min" if fall is None else "within 15 min" if fall <= 15 else "15-30 min" if fall <= 30
             else "30-60 min" if fall <= 60 else "after 60 min"] += 1
    final = [(run_["lactate"][MINUTES], run_["baseline"], key) for key, run_ in _cases_runs(runs, case, L3)
             if MINUTES < len(run_["lactate"])]
    by_debt: dict = {}
    for value, _, key in final:
        by_debt.setdefault(candidate_of(key).debt, []).append(value)
    persistent = [(key, run_) for key, run_ in _cases_runs(runs, case, L1) if 60 < len(run_["lactate"])
                  and all(point["delivery"] < point["demand"] for minute, point in run_["points"].items()
                          if minute <= 60)]
    return {
        "FD-LAC-02/03 untreated lactate at 60 min": {name: untreated[name] for name in
                                                     ("min", "p10", "median", "p90", "max", "n")},
        "FD-LAC-04 first clear fall after definitive management": {name: count / len(falls)
                                                                   for name, count in bins.items()},
        "FD-LAC-05 lactate at 120 min after definitive management": {
            "min": min(value for value, _, _ in final), "median": _quantile(sorted(v for v, _, _ in final), 0.5),
            "max": max(value for value, _, _ in final),
            "median_above_candidate_baseline": _quantile(sorted(v - base for v, base, _ in final), 0.5),
            "median_by_arrival_debt": {level: _quantile(sorted(values), 0.5) for level, values in by_debt.items()}},
        "FD-LAC-06 untreated runs with delivery below demand at 0, 15, 30 and 60 min": {
            "n": len(persistent),
            "lactate_falls_by_60": sum(1 for _, run_ in persistent if run_["lactate"][60] < run_["lactate"][0])}}


def repository_truth() -> dict:
    """The authored arrival facts relevant to lactate, with their source lines (no inference)."""
    rows = {case: [] for case in CASES}
    for entry in gi_reference.INVENTORY:
        if entry.case in rows and entry.item in TRUTH_ITEMS:
            rows[entry.case].append({"item": entry.item, "value": entry.value, "source": entry.source})
    for case in rows:
        rows[case].sort(key=lambda row: TRUTH_ITEMS.index(row["item"]))
    return rows


def legacy_reference() -> dict:
    """LEGACY REFERENCE, NOT A CALIBRATION TARGET: the family engine's own lactate. Read last, never
    by the tables or the classes above."""
    reference = {}
    for case in CASES:
        reference[case] = {}
        for scenario in (L1, L2, L3):
            snapshots = {item["minute"]: item for item in calibration._legacy_run(case, ORDERS[scenario]).snapshots}
            reference[case][scenario] = {minute: snapshots[minute]["lactate_lab"] for minute in TIMES
                                         if minute in snapshots}
        reference[case][L4] = None   # the engine defers this endoscopy: it has no L4 trajectory
    return reference


# The slice ------------------------------------------------------------------------------------

#: P2I-2X-4: render-only reports of later, separate artifacts (P2I-2V-R, P2I-2W, P2I-2X, P2I-2Y). They are strictly
#: downstream: no other clinical_core module imports them (a test checks every module's imports), so they cannot
#: change the slice or any artifact hashed with these sources; each keeps its own generated-document test.
DOWNSTREAM_REPORTS = ("clinical_core/blood_filter_report.py", "clinical_core/blood_extension_report.py",
                      "clinical_core/blood_rate_report.py", "clinical_core/blood_fluid_report.py",
                      "clinical_core/blood_fluid_readiness_report.py",
                      "clinical_core/blood_fluid_tau_closure_report.py", "clinical_core/lactate_rebuild_report.py",
                      "clinical_core/lactate_adequacy_report.py", "clinical_core/lactate_closure_report.py",
                      "clinical_core/hr_structure_report.py", "clinical_core/hr_shock_report.py",
                      "clinical_core/hr_primary_report.py", "clinical_core/arrival_severity_report.py",
                      "clinical_core/hr_observables_report.py", "clinical_core/hr_envelope_filter_report.py",
                      "clinical_core/pressure_tone_report.py", "clinical_core/vascular_tone_report.py",
                      "clinical_core/pressure_tone_filter_report.py")


def slice_sources() -> dict[str, str]:
    """Every shadow-core source, by hash: the core, the harness, the pack it reuses, this module and its own
    renderers. Only DOWNSTREAM_REPORTS are left out. A change to any other makes the slice stale."""
    package = calibration.REPOSITORY / "clinical_core"
    paths = sorted(path.relative_to(calibration.REPOSITORY).as_posix() for path in package.rglob("*.py")
                   if "__pycache__" not in path.parts and path.is_file() and not path.name.startswith(".")
                   and path.relative_to(calibration.REPOSITORY).as_posix() not in DOWNSTREAM_REPORTS)
    return {path: hashlib.sha256(calibration._source_bytes(path)).hexdigest() for path in paths}


def slice_digest() -> str:
    orders = {name: [spec["minutes"], {str(minute): order for minute, order in spec["orders"].items()}]
              for name, spec in ORDERS.items()}
    text = json.dumps({"freeze": calibration.frozen_digest(), "orders": orders, "sources": slice_sources()},
                      sort_keys=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def report(quick: bool = False) -> dict:
    digests = {"slice_digest": slice_digest(), "freeze_digest": calibration.frozen_digest()}
    runs = region_runs(quick)
    per_case = {case: {"trajectories": {scenario: trajectory_table(runs, case, scenario) for scenario in ORDERS},
                       "classes": classes(runs, case), "representatives": representatives(runs, case),
                       "dissociation": dissociation(runs, case), "sensitivity": sensitivity(runs, case),
                       "worksheet": worksheet_support(runs, case)}
                for case in CASES}
    return {**digests, "quick": quick, "admissible_candidates": len(decision_pack.admissible(quick)),
            "read_without_debt_drive": len(decision_pack.admissible(quick)) - len(decision_pack.runnable(quick)),
            "scenarios": {name: {"title": SCENARIO_TITLES[name], "minutes": spec["minutes"],
                                 "orders": {str(minute): order for minute, order in spec["orders"].items()},
                                 "trajectory_kind": TRAJECTORY_KIND[name],
                                 "counterfactual": TRAJECTORY_KIND[name] == COUNTERFACTUAL}
                          for name, spec in ORDERS.items()},
            "endoscopy_minute": {case: endoscopy_minute(case) for case in CASES},
            "repository_truth": repository_truth(), "cases": per_case,
            # Last and apart: never an input to anything above.
            "legacy_reference": legacy_reference()}


# Rendering into the faculty document --------------------------------------------------------------

TITLES_ES = {
    L1: "hemorragia activa sin tratar",
    L2: "reanimación transitoria y parcial (2 L de salina en 20 min; el sangrado sigue)",
    L3: "control definitivo y reanimación adecuada (2 unidades en 60 min, IBP y endoscopia)",
    L4: ("hemostasia sin recuperar la perfusión (IBP y endoscopia sin volumen) — COMPOSICIÓN CONTRAFACTUAL MANUAL: "
         "la hemostasia se agregó a mano en el minuto de L3; el motor no la produce"),
}
CLASSES_ES = {FALLS: "A baja", FLAT_CLASS: "B aproximadamente estable", MODEST: "C sube moderadamente",
              SUBSTANTIAL_CLASS: "D sube sustancialmente", STOPPED: "detenida (el gasto llegó a cero)",
              PROMPT: "E baja claramente en 30 min", LATER: "E' baja claramente después de 30 min",
              ELEVATED_RESTORED: "F sigue elevado con la entrega restaurada",
              ELEVATED_UNRESTORED: "F' sigue elevado sin restaurar la entrega"}
WINDOWS = [(f"{scenario} at {minute} min", f"{scenario} a los {minute} min")
           for scenario in (L1, L2) for minute in (60, MINUTES)] + \
          [(f"{L3} over {MINUTES} min", f"{L3} en {MINUTES} min"),
           (f"{L4} over {MINUTES} min", f"{L4} (contrafactual) en {MINUTES} min")]
READOUTS_ES = {"L1 change at 60 min (mmol/L)": "L1: cambio a los 60 min (mmol/L)",
               "L3 first clear fall (min; 121 = not within 120)": "L3: primera caída clara (min; 121 = no en 120)",
               "L3 lactate at 120 min (mmol/L)": "L3: lactato a los 120 min (mmol/L)"}
PATTERNS_ES = {
    "L1 0-60 min: D rises while lactate falls": "L1, 0–60 min: D sube mientras el lactato baja",
    "L1 0-120 min: D rises while lactate falls": "L1, 0–120 min: D sube mientras el lactato baja",
    "L3 0-120 min: D falls while lactate stays within 0.5 mmol/L of arrival or above":
        "L3, 0–120 min: D baja mientras el lactato sigue a menos de 0,5 mmol/L de la llegada o por encima",
    "L4 0-120 min: D stays at or above arrival while lactate moves less than 0.5 mmol/L":
        "L4 (contrafactual), 0–120 min: D sigue igual o por encima de la llegada mientras el lactato se mueve menos "
        "de 0,5 mmol/L"}
DIRECTIONS_ES = {"increases it": "la aumenta", "decreases it": "la disminuye", "non-monotonic": "no monótona",
                 "no effect": "sin efecto"}
SOURCES_ES = {"main effect over the admissible region": "efecto principal sobre la región admisible",
              "one-at-a-time probe around the middle candidate (the region does not vary it)":
                  "sonda de a uno alrededor del candidato medio (la región no lo varía)"}
LEVELS_ES = {"lower": "inferior", "midpoint": "medio", "upper": "superior"}
BINS_ES = {"within 15 min": "en 15 min", "15-30 min": "15–30 min", "30-60 min": "30–60 min",
           "after 60 min": "después de 60 min", "not within 120 min": "no en 120 min"}

def _n(value, digits: int = 2) -> str:
    if value is None:
        return "—"
    if isinstance(value, str):
        return value
    text = f"{value:.{digits}f}"
    return text.replace(".", ",")


def _pct(value: float) -> str:
    return f"{round(100 * value)} %"


#: Markers the inventory writes in English; the case's own words are quoted as authored.
TRUTH_MARKERS_ES = {"(derived, not authored)": "(derivada, no escrita en el caso)", "not stated": "no consta"}


def _truth_value(value) -> str:
    text = str(value)
    for marker, spanish in TRUTH_MARKERS_ES.items():
        if text == marker or text.endswith(" " + marker):
            text = text[: len(text) - len(marker)] + spanish
    head, space, rest = text.partition(" ")
    try:
        float(head)
    except ValueError:
        return text
    return head.replace(".", ",") + space + rest


def _level_key(level: str):
    order = {"lower": 0, "midpoint": 1, "upper": 2}
    return (0, order[level]) if level in order else (1, float(level))


def _level_es(level: str) -> str:
    return LEVELS_ES.get(level, level.replace(".", ","))


#: P2I-1.2, written into the document by the renderer so that every L4 mention carries its label.
SCENARIO_ROWS_ES = {
    L1: ("Hemorragia activa sin tratar", "sin órdenes"),
    L2: ("Reanimación transitoria y parcial; el sangrado sigue",
         "2 L de solución salina en 20 min; sin IBP ni endoscopia"),
    L3: ("Control definitivo y reanimación adecuada",
         "el manejo definitivo de P2G: 2 unidades de glóbulos rojos en 60 min, IBP y endoscopia urgente; el motor "
         "hace la endoscopia en el minuto {minutes}"),
    L4: ("Hemostasia sin recuperar la perfusión — **composición contrafactual manual**",
         "IBP y endoscopia urgente, sin volumen. El motor de familias difiere esa endoscopia (PAS bajo 90) y nunca "
         "produce esta hemostasia. Se agregó a mano, en el mismo minuto que en L3 y con un identificador propio "
         f"(`{COUNTERFACTUAL_HEMOSTASIS_ID}`), sobre las entradas que el motor sí produce para estas órdenes. Es una "
         "pregunta contrafactual"),
}


def render(data: dict) -> str:
    """The generated part of docs/revision/P2I_DECISION_LACTATO_GI.md, from the slice's JSON."""
    lines = []
    add = lines.append
    add("## 1. Verdad del repositorio (sin inferencia)\n")
    for case in CASES:
        add(f"**{case}**\n")
        add("| Dato | Valor del caso | Fuente |")
        add("|---|---|---|")
        for row in data["repository_truth"][case]:
            add(f"| `{row['item']}` | {_truth_value(row['value'])} | `{row['source']}` |")
        add("")
    add("Los textos clínicos se citan tal como los escribe el caso, en inglés. La duración del shock antes de la "
        "llegada no consta en ninguno de los dos casos y no se infiere.\n")
    add("## 2. Las cuatro preguntas de trayectoria\n")
    add("Las cuatro corren 120 min con órdenes y tipos de entrada que ya existen; no se agrega fisiología. L1, L2 y "
        "L3 sólo usan lo que el motor produce para sus órdenes; L4 (contrafactual) le agrega a mano una "
        "hemostasia.\n")
    add("| Escenario | Qué representa | Cómo se construye |")
    add("|---|---|---|")
    endoscopy = sorted(set(data["endoscopy_minute"].values()))
    for scenario in ORDERS:
        meaning, construction = SCENARIO_ROWS_ES[scenario]
        add(f"| {scenario} | {meaning} | "
            f"{construction.format(minutes=' y '.join(str(minute) for minute in endoscopy))} |")
    add("")
    add("**Dos tipos de trayectoria.** L1, L2 y L3 usan sólo entradas que produce el motor de familias por el camino "
        "congelado; su hemostasia, en L3, es la del propio motor. L4 es una composición contrafactual manual, y cada "
        "vez que aparece en este documento lleva esa etiqueta: ninguna pregunta de la hoja de trabajo la usa "
        "(FD-LAC-01, -02, -03 y -06 se leen en L1, y FD-LAC-04 y -05 en L3) y sólo sirve de contraste, para mostrar "
        "qué hace el modelo si el sangrado se detiene sin reanimación.\n")
    add("**Cómo se forma el lactato en el modelo.** D (la deuda de O2) acumula el déficit de entrega y lo paga con "
        "τ_D. El exceso de lactato X se produce desde D con ganancia G y se aclara con τ_L. El lactato visible es la "
        "basal candidata más X, y la basal candidata es el lactato de llegada menos `arrival_lactate_excess`. Dada "
        "la trayectoria del déficit, X se separa de forma exacta en tres partes: lo que queda del exceso de llegada, "
        "lo que todavía produce la D de llegada y lo que produjo el déficit posterior (§5). La separación es exacta "
        "para las ecuaciones del modelo, pero no es una atribución causal entre parámetros, porque éstos interactúan "
        "a través del déficit.\n")
    add("## 3. Tablas de trayectoria del lactato (mmol/L, región admisible)\n")
    for scenario in ORDERS:
        add(f"**{scenario} · {TITLES_ES[scenario]}**\n")
        if TRAJECTORY_KIND[scenario] == COUNTERFACTUAL:
            add("> L4 contrafactual: no es una trayectoria que el motor heredado produzca. Se muestra sólo como "
                "contraste y ninguna pregunta de la hoja de trabajo la usa.\n")
        add("| Caso | min | n | mínimo | p10 | mediana | p90 | máximo | sube | baja | cambia > 1 | cambia > 2 |")
        add("|---|---|---|---|---|---|---|---|---|---|---|---|")
        for case in CASES:
            for minute, row in data["cases"][case]["trajectories"][scenario].items():
                stopped = f" (+{row['stopped_before']} detenidas)" if row["stopped_before"] else ""
                if not row["n"]:
                    add(f"| {case} | {minute} | 0{stopped} |" + " — |" * 9)
                    continue
                add(f"| {case} | {minute} | {row['n']}{stopped} | {_n(row['min'])} | {_n(row['p10'])} | "
                    f"{_n(row['median'])} | {_n(row['p90'])} | {_n(row['max'])} | {_pct(row['rising'])} | "
                    f"{_pct(row['falling'])} | {_pct(row['changed_more_than_1'])} | "
                    f"{_pct(row['changed_more_than_2'])} |")
        add("")
    add("## 4. Clases de comportamiento (conteos sobre la región; ninguna se declara correcta)\n")
    for case in CASES:
        add(f"**{case}**\n")
        add("| Escenario y lectura | Clase | n | Dónde se concentra (mayor proporción por factor) |")
        add("|---|---|---|---|")
        for window, label in WINDOWS:
            entry = data["cases"][case]["classes"][window]
            for name, item in entry["classes"].items():
                where = "; ".join(f"`{factor}` {LEVELS_ES.get(top, top)} ({_pct(levels[top])})"
                                  for factor, levels in item["composition"].items()
                                  for top in [max(levels, key=levels.get)])
                add(f"| {label} | {CLASSES_ES[name]} | {item['n']} | {where} |")
            if "falls_while_delivery_fell" in entry:
                add(f"| {label} | de las que bajan: con la entrega de O2 cayendo | "
                    f"{entry['falls_while_delivery_fell']} | |")
        add("")
    add("## 5. Descomposición del mecanismo (exacta dada la trayectoria del déficit)\n")
    add("Exceso de lactato = lo que queda del exceso de llegada + lo que produce la D de llegada + lo producido por "
        "el déficit posterior. Suma exacta para las recurrencias del modelo; no es una atribución causal entre "
        "parámetros.\n")
    for case in CASES:
        for label, label_es in (("low", "bajo"), ("middle", "medio"), ("high", "alto")):
            for scenario, item in data["cases"][case]["representatives"][label].items():
                p = item["parameters"]
                add(f"**{case} · {label_es} · {scenario}** — `arrival_oxygen_debt` {_n(p['arrival_oxygen_debt'], 0)}, "
                    f"`arrival_lactate_excess` {_n(p['arrival_lactate_excess'])}, `arrival_delivery_ratio` "
                    f"{_n(p['arrival_delivery_ratio'])}, τ_D {_n(p['debt_clearance_tau_min'], 0)}, "
                    f"g {_n(p['debt_per_delivery_deficit'], 1)}, G {_n(p['lactate_per_output_deficit'], 0)}, "
                    f"τ_L {_n(p['lactate_clearance_tau_min'], 0)}, demanda {_n(p['metabolic_demand_baseline'])}\n")
                add("| min | lactato | basal | exceso de llegada restante | de la D de llegada | del déficit posterior "
                    "| D | D de llegada restante | D acumulada desde la llegada | D pagada | entrega | déficit |")
                add("|---|---|---|---|---|---|---|---|---|---|---|---|")
                for minute, row in item["rows"].items():
                    add(f"| {minute} | {_n(row['lactate'])} | {_n(row['baseline'])} | "
                        f"{_n(row['arrival_excess_left'])} | {_n(row['from_arrival_debt'])} | "
                        f"{_n(row['from_deficit_since_arrival'])} | {_n(row['D'], 1)} | {_n(row['D_arrival_left'], 1)} "
                        f"| {_n(row['D_accrued_so_far'], 1)} | {_n(row['D_repaid_so_far'], 1)} | "
                        f"{_n(row['delivery'])} | {_n(row['deficit'])} |")
                add("")
    add("## 6. D frente a lactato (no se declaran inválidos)\n")
    add("| Caso | Patrón | corridas | de | ejemplos (D desde → hasta; lactato desde → hasta) |")
    add("|---|---|---|---|---|")
    for case in CASES:
        for item in data["cases"][case]["dissociation"]:
            pattern = PATTERNS_ES[item["pattern"]]
            examples = "; ".join(f"D {_n(e['D_from'], 1)}→{_n(e['D_to'], 1)}, lactato {_n(e['lactate_from'])}→"
                                 f"{_n(e['lactate_to'])}" for e in item["examples"])
            add(f"| {case} | {pattern} | {item['n']} | {item['of']} | {examples} |")
    add("")
    add("## 7. Impacto de cada parámetro en las lecturas de las decisiones\n")
    add("ALTO ≥ 1 mmol/L (o ≥ 30 min), MEDIO ≥ 0,3 mmol/L (o ≥ 10 min), BAJO por debajo: bandas de presentación, "
        "no criterios. Cada valor por nivel es la mediana de la lectura sobre los conjuntos con ese nivel. La región "
        "no es un diseño balanceado: no contiene τ_D = 30 con la deuda de llegada alta, así que el efecto de "
        "`debt_clearance_tau_min` se mezcla en parte con el de la deuda. `debt_per_delivery_deficit` y "
        "`metabolic_demand_baseline` no varían en la región; se sondean de a uno alrededor del candidato medio.\n")
    for case in CASES:
        for readout, rows in data["cases"][case]["sensitivity"].items():
            add(f"**{case} · {READOUTS_ES[readout]}**\n")
            add("| Parámetro | Impacto | Dirección (de bajo a alto) | Valor por nivel | Rango | Origen |")
            add("|---|---|---|---|---|---|")
            digits = 0 if "first clear fall" in readout else 2
            for row in rows:
                levels = ", ".join(f"{_level_es(level)}: {_n(row['levels'][level], digits)}"
                                   for level in sorted(row["levels"], key=_level_key))
                impact = {"HIGH": "ALTO", "MEDIUM": "MEDIO", "LOW": "BAJO"}[row["impact"]]
                add(f"| `{row['factor']}` | {impact} | {DIRECTIONS_ES[row['direction']]} | {levels} | "
                    f"{_n(row['spread'], digits)} | {SOURCES_ES[row['source']]} |")
            add("")
    add("## 8. Lo que el modelo ofrece para cada pregunta (sólo modelo)\n")
    add("Sólo trayectorias producidas por el motor: L1 para FD-LAC-02/03/06 y L3 para FD-LAC-04/05. La composición "
        "contrafactual L4 no entra en ninguna.\n")
    for case in CASES:
        support = data["cases"][case]["worksheet"]
        untreated = support["FD-LAC-02/03 untreated lactate at 60 min"]
        falls = support["FD-LAC-04 first clear fall after definitive management"]
        final = support["FD-LAC-05 lactate at 120 min after definitive management"]
        persistent = support["FD-LAC-06 untreated runs with delivery below demand at 0, 15, 30 and 60 min"]
        arrival = next(row["value"] for row in data["repository_truth"][case] if row["item"] == "lactate_mmol_l")
        add(f"**{case}** (lactato de llegada {_n(float(arrival), 1)})\n")
        add(f"- Sin tratar, a los 60 min (FD-LAC-02/03): mínimo {_n(untreated['min'])}, p10 {_n(untreated['p10'])}, "
            f"mediana {_n(untreated['median'])}, p90 {_n(untreated['p90'])}, máximo {_n(untreated['max'])} "
            f"({untreated['n']} corridas).")
        add("- Primera caída clara (≥ 0,5 mmol/L bajo la llegada) tras el manejo definitivo (FD-LAC-04): "
            + ", ".join(f"{BINS_ES[name]}: {_pct(falls[name])}" for name in BINS_ES) + ".")
        add(f"- A los 120 min tras el manejo definitivo (FD-LAC-05): de {_n(final['min'])} a {_n(final['max'])}, mediana "
            f"{_n(final['median'])}; mediana sobre la basal candidata {_n(final['median_above_candidate_baseline'])}; "
            "mediana según la deuda de llegada: "
            + ", ".join(f"{LEVELS_ES[level]} {_n(value)}" for level, value in sorted(
                final["median_by_arrival_debt"].items(), key=lambda item: ("lower", "midpoint", "upper").index(item[0])))
            + ".")
        add(f"- Sin tratar, con la entrega bajo la demanda a los 0, 15, 30 y 60 min (FD-LAC-06): {persistent['n']} corridas; "
            f"en {persistent['lactate_falls_by_60']} el lactato baja.")
        add("")
    add("## 9. REFERENCIA HEREDADA — NO ES OBJETIVO DE CALIBRACIÓN\n")
    add("El lactato que reporta el motor de familias en los mismos escenarios. Ninguna tabla ni clase de arriba la lee.\n")
    add("| Caso | Escenario | " + " | ".join(f"{minute} min" for minute in TIMES) + " |")
    add("|---|---|" + "---|" * len(TIMES))
    for case in CASES:
        for scenario, values in data["legacy_reference"][case].items():
            cells = (" | ".join(_n(values.get(str(minute), values.get(minute)), 1) for minute in TIMES)
                     if values else " | ".join("—" for _ in TIMES))
            note = "" if values else (" (contrafactual: el motor difiere esta endoscopia y no tiene trayectoria "
                                      "L4)")
            add(f"| {case} | {scenario}{note} | {cells} |")
    add("")
    return "\n".join(lines)


OPENING, CLOSING = "<!-- generado:lactato -->\n", "<!-- /generado:lactato -->"


def apply(document: str, block: str) -> str:
    start = document.index(OPENING) + len(OPENING)
    end = document.index(CLOSING)
    return document[:start] + block + "\n" + document[end:]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--write", type=Path, help="render a slice JSON into this document (with --json)")
    parser.add_argument("--json", type=Path)
    args = parser.parse_args(argv)
    if args.write:
        data = json.loads(args.json.read_text(encoding="utf-8"))
        args.write.write_text(apply(args.write.read_text(encoding="utf-8"), render(data)), encoding="utf-8")
        return 0
    text = json.dumps(report(args.quick), indent=1, sort_keys=True, default=str)
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "lactate_slice.json").write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
