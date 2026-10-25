"""P2I-2: apply the faculty-approved GI lactate constraints (FD-LAC-01..06) to P2F's admissible region.

    python -m clinical_core.lactate_constraints [--quick] [--out <directory outside the repository>]
    python -m clinical_core.lactate_constraints --write <document> --json <results JSON>
    python -m clinical_core.lactate_constraints --decisions docs/revision/P2I_DECISION_LACTATO_GI.md

Shadow and offline. It filters exactly ``decision_pack.admissible`` (no new candidate) through
the faculty's clinical behaviour constraints, using only engine-produced trajectories (L1
untreated, L2 partial saline, L3 definitive management; P2I-1's L4 counterfactual never enters).
It never selects a parameter set, never marks a parameter FACULTY_APPROVED, never touches a
registry, a band, the calibration freeze or the golden, and never reads the family engine's
lactate to filter: the engine supplies only each scenario's inputs (as in P2I-1), and its
lactate appears last, as a reference placed against the approved envelopes.

The surviving set is the FACULTY-CONSTRAINED CANDIDATE REGION: still CANDIDATE, not approved.

The operational definitions are frozen: ``faculty_constraints.definitions_digest`` and this
module's ``pipeline_digest`` (how a core run becomes a ``Trajectory`` and how the region is
evaluated) are pinned below, before any filtering ran; the filter refuses to run on others.
"""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
from dataclasses import replace
from pathlib import Path

from . import calibration, decision_pack, faculty_constraints as fc
from . import lactate_slice
from .derived import DEFAULT_PROFILE, derive, effective_delivery
from .faculty_constraints import Trajectory

FROZEN_DEFINITIONS_DIGEST = "ee1deb2578504d3c295d2c4a3552b2d781529064f94043f99b07f04d0fe258cc"
FROZEN_PIPELINE_DIGEST = "4c326d6e60e9a96cde713afcf0fc38b14cf877b8521e60b7e33d584b24037394"
CASES = fc.CASES
L1, L2, L3 = fc.UNTREATED, fc.PARTIAL, fc.DEFINITIVE
SCENARIOS = (L1, L2, L3)
TIMES = lactate_slice.TIMES
KINETICS = ("debt_clearance_tau_min", "debt_per_delivery_deficit", "lactate_per_output_deficit",
            "lactate_clearance_tau_min")


# The pipeline (pinned by FROZEN_PIPELINE_DIGEST) -------------------------------------------------

def _controlled_at(state) -> int | None:
    """The minute the core's GI haemorrhage module recorded haemostasis (its own state)."""
    found = [record["controlled_at"] for key, record in state.internal.items()
             if key.startswith("disease_module:") and "controlled_at" in record]
    if len(found) != 1:
        raise AssertionError("a GI run has exactly one GI haemorrhage module")
    return found[0]


def trajectory_of(case: str, candidate, scenario: str, **extra) -> Trajectory:
    """One engine-produced scenario run in the shadow core, read minute by minute."""
    run_ = lactate_slice.slice_run(case, candidate, scenario, keep_states=True, **extra)
    states, anchors, profile = run_["states"], run_["anchors"], run_["profile"]
    delivery, demand = [], []
    for minute, state in enumerate(states):
        derived = derive(state, anchors, profile)
        if abs(derived.lactate - run_["lactate"][minute]) > 1e-9:
            raise AssertionError("the constraints' lactate is no longer the core's")
        delivery.append(effective_delivery(derived.delivery_rel, anchors))
        demand.append(state.aux.oxygen_demand)
    return Trajectory(tuple(run_["lactate"]), tuple(run_["D"]), tuple(delivery), tuple(demand),
                      _controlled_at(states[-1]))


def kinetics_of(candidate) -> dict:
    profile = replace(DEFAULT_PROFILE, **candidate.profile)
    return {name: getattr(profile, name) for name in KINETICS}


def region(quick: bool = False) -> dict:
    """Exactly P2F's admissible region (P2G's), every candidate in every engine-produced scenario."""
    return {candidate.key(): {"candidate": candidate,
                              "runs": {case: {scenario: trajectory_of(case, candidate, scenario)
                                              for scenario in SCENARIOS} for case in CASES}}
            for candidate in decision_pack.admissible(quick)}


def evaluate_region(members: dict, settings: dict) -> dict:
    """Every candidate through all six; the arrival lactate is each run's own minute 0."""
    return {key: fc.evaluate(item["runs"], kinetics_of(item["candidate"]),
                             {case: item["runs"][case][L1].lactate[0] for case in CASES}, settings)
            for key, item in members.items()}


PIPELINE = (_controlled_at, trajectory_of, kinetics_of, region, evaluate_region)


def pipeline_digest() -> str:
    text = "\n".join(inspect.getsource(function) for function in PIPELINE)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def check_frozen() -> None:
    if fc.definitions_digest() != FROZEN_DEFINITIONS_DIGEST:
        raise AssertionError("the operational definitions changed after they were frozen")
    if pipeline_digest() != FROZEN_PIPELINE_DIGEST:
        raise AssertionError("the evaluation pipeline changed after it was frozen")
    if reporting_digest() != FROZEN_REPORTING_DIGEST:
        raise AssertionError("the frozen reporting rules changed")


# Counts ---------------------------------------------------------------------------------------

def counts(verdicts: dict) -> dict:
    keys = sorted(verdicts)
    survivors = {name: [key for key in keys if verdicts[key]["passes"][name]] for name in fc.CONSTRAINT_IDS}
    every = [key for key in keys if verdicts[key]["all"]]
    failing = {key: [name for name in fc.CONSTRAINT_IDS if not verdicts[key]["passes"][name]] for key in keys}
    discrimination = []
    for name in fc.CONSTRAINT_IDS:
        others = [other for other in fc.CONSTRAINT_IDS if other != name]
        discrimination.append({
            "constraint": name, "eliminates": len(keys) - len(survivors[name]),
            "eliminates_alone": sum(1 for key in keys if failing[key] == [name]),
            "survivors_without_it": sum(1 for key in keys if all(verdicts[key]["passes"][other] for other in others))})
    return {"before": len(keys), "survivors": {name: len(items) for name, items in survivors.items()},
            "all_six": len(every), "all_six_keys": every, "discrimination": discrimination}


def per_case(verdicts: dict) -> dict:
    table = {}
    for case in CASES:
        row = {}
        for item in fc.FACULTY_CLINICAL_CONSTRAINTS:
            if case in item.cases:
                row[item.id] = sum(1 for verdict in verdicts.values() if verdict["detail"][case][item.id]["passes"])
        row["FD-LAC-01 not applicable"] = sum(1 for verdict in verdicts.values()
                                              if not verdict["detail"][case]["FD-LAC-01"]["applicable"])
        reasons: dict = {}
        for verdict in verdicts.values():
            response = verdict["detail"][case]["FD-LAC-04"]
            if not response["evaluable"]:
                reasons[response["reason"]] = reasons.get(response["reason"], 0) + 1
        row["FD-LAC-04 not evaluable"] = reasons
        table[case] = row
    return table


def sensitivity(members: dict) -> list:
    rows = []
    for name, overrides in fc.SENSITIVITY.items():
        found = counts(evaluate_region(members, fc.params(**overrides)))
        rows.append({"variant": name, "overrides": overrides, "survivors": found["survivors"],
                     "all_six": found["all_six"]})
    return rows


# P2I-2.7 the P2I-1 dissociations, revisited ---------------------------------------------------

def dissociation(members: dict, survivors: list, settings: dict) -> list:
    """P2I-1's 'D rises while lactate falls' (untreated, 0-60 and 0-120 min), classified.

    B UNACCEPTABLE: a sustained decline inside a window of active bleeding with inadequate
      delivery within the span (what FD-LAC-01/06 forbid);
    A ACCEPTABLE: otherwise, and the lactate falls only in minutes whose delivery is adequate;
    C TRANSIENT/AMBIGUOUS: otherwise (a fall with inadequate delivery too small or too short to be
      a sustained decline)."""
    keep, rows = set(survivors), []
    for case in CASES:
        for horizon in (60, 120):
            found = {"A": 0, "B": 0, "C": 0}
            among = {"A": 0, "B": 0, "C": 0}
            for key, item in members.items():
                run_ = item["runs"][case][L1]
                if run_.end < horizon or not (run_.D[horizon] > run_.D[0] and run_.lactate[horizon] < run_.lactate[0]):
                    continue
                windows = [(first, min(last, horizon)) for first, last in fc.inadequate_bleeding_windows(run_, settings)
                           if first <= horizon]
                if any(fc.sustained_declines(run_, first, last, settings) for first, last in windows
                       if last - first >= settings["sustained_min"]):
                    label = "B"
                elif all(fc.adequate(run_, minute - 1, settings) for minute in range(1, horizon + 1)
                         if run_.lactate[minute] < run_.lactate[minute - 1]):
                    label = "A"
                else:
                    label = "C"
                found[label] += 1
                if key in keep:
                    among[label] += 1
            rows.append({"case": case, "pattern": f"L1 0-{horizon} min: D rises while lactate falls",
                         "region": found, "faculty_constrained": among})
    return rows


# P2I-2.8/2.9 the region after filtering --------------------------------------------------------

def _level_values(candidate, case: str) -> dict:
    values = calibration.case_values(case, candidate)
    kinetics = kinetics_of(candidate)
    return {"arrival_oxygen_debt": (candidate.debt, values["arrival_oxygen_debt"]),
            "arrival_lactate_excess": (candidate.excess, values["arrival_lactate_excess"]),
            "arrival_delivery_ratio": (candidate.delivery, values["arrival_delivery_ratio"]),
            "metabolic_demand_baseline": ("fixed", values["metabolic_demand_baseline"]),
            **{name: (f"{kinetics[name]:g}", kinetics[name]) for name in KINETICS}}


FACTORS = ("arrival_oxygen_debt", "arrival_lactate_excess", "debt_clearance_tau_min", "debt_per_delivery_deficit",
           "lactate_per_output_deficit", "lactate_clearance_tau_min", "arrival_delivery_ratio",
           "metabolic_demand_baseline")


def parameter_region(members: dict, survivors: list) -> list:
    rows = []
    for factor in FACTORS:
        levels: dict = {}
        for key, item in members.items():
            level = _level_values(item["candidate"], CASES[0])[factor][0]
            entry = levels.setdefault(level, {"region": 0, "survivors": 0,
                                              "values": {case: _level_values(item["candidate"], case)[factor][1]
                                                         for case in CASES}})
            entry["region"] += 1
            entry["survivors"] += key in survivors
        total, left = sum(entry["region"] for entry in levels.values()), len(survivors)
        region_shares = {level: entry["region"] / total for level, entry in levels.items()}
        surviving_shares = {level: entry["survivors"] / left for level, entry in levels.items()} if left else {}
        varied = len(levels) > 1
        ranges = {}
        for case in CASES:
            prior = [entry["values"][case] for entry in levels.values()]
            post = [entry["values"][case] for entry in levels.values() if entry["survivors"]]
            ranges[case] = {"region": [min(prior), max(prior)], "survivors": [min(post), max(post)] if post else None}
        rows.append({"factor": factor, "varied_by_region": varied,
                     "levels": [{"level": level, **entry} for level, entry in
                                sorted(levels.items(), key=lambda item: item[1]["values"][CASES[0]])],
                     "ranges": ranges, "classification": fc.identifiability(region_shares, surviving_shares, varied)})
    return rows


def fd05_verification(members: dict, survivors: list, verdicts: dict) -> dict:
    """FD-LAC-05 checks on the region and the survivors; no numeric band is applied."""
    result = {}
    for case in CASES:
        by_debt: dict = {}
        for key in survivors:
            item = members[key]
            by_debt.setdefault(item["candidate"].debt, []).append(item["runs"][case][L3].lactate[-1])
        pairs, higher = 0, 0
        # Siblings: the same candidate but for the arrival debt (lower against upper, same delivery).
        index = {(json.dumps(item["candidate"].profile, sort_keys=True), item["candidate"].excess,
                  item["candidate"].intrinsic, item["candidate"].preload, item["candidate"].debt,
                  item["candidate"].delivery): key for key, item in members.items()}
        for (profile, excess, intrinsic, preload, debt, delivery), key in index.items():
            if debt != "lower":
                continue
            sibling = index.get((profile, excess, intrinsic, preload, "upper", delivery))
            if sibling is None:
                continue
            pairs += 1
            higher += members[sibling]["runs"][case][L3].lactate[-1] > members[key]["runs"][case][L3].lactate[-1]
        residual = sorted(members[key]["runs"][case][L3].lactate[-1] for key in survivors)
        memory = sorted(verdicts[key]["detail"][case]["FD-LAC-05"]["debt_memory_at_reference_debt"] for key in members)
        result[case] = {
            "survivor_residual_median_by_arrival_debt": {level: lactate_slice._quantile(sorted(values), 0.5)
                                                         for level, values in sorted(by_debt.items())},
            "region_debt_pairs": pairs, "region_pairs_higher_debt_higher_residual": higher,
            "survivor_residual_range": [residual[0], residual[-1]] if residual else None,
            "survivors_above_normal_at_120": sum(1 for value in residual if value > fc.PRIMARY["fd05_normal_upper_mmol_l"]),
            "region_debt_memory_range": [memory[0], memory[-1]],
            "abrupt_normalizations_in_region": sum(1 for verdict in verdicts.values()
                                                   if verdict["detail"][case]["FD-LAC-05"]["abrupt_normalization"])}
    return result


def fd04_summary(members: dict, survivors: list, verdicts: dict, settings: dict) -> dict:
    """Where FD-LAC-04's clock starts and why runs pass or fail it, with the minute delivery first
    became adequate in L3 (before haemostasis, the trend may already be under way)."""
    keep, result = set(survivors), {}
    for case in CASES:
        summary = {"triggers": {}, "onset_after_trigger": {}, "not_clear": 0, "not_timely": 0, "not_evaluable": {},
                   "first_adequate_minute": {}, "survivor_onset_after_trigger": {}, "survivor_first_adequate_minute": {},
                   "meaningful_fall_after_trigger": {}, "survivor_meaningful_fall_after_trigger": {}}
        for key, verdict in verdicts.items():
            response = verdict["detail"][case]["FD-LAC-04"]
            trigger = str(response["trigger"])
            summary["triggers"][trigger] = summary["triggers"].get(trigger, 0) + 1
            run_ = members[key]["runs"][case][L3]
            first = next((minute for minute in range(run_.end + 1) if fc.adequate(run_, minute, settings)), None)
            bucket = "never" if first is None else "0" if first == 0 else "1-30" if first <= 30 else "31-59" \
                if first < 60 else "60 or later"
            summary["first_adequate_minute"][bucket] = summary["first_adequate_minute"].get(bucket, 0) + 1
            if key in keep:
                summary["survivor_first_adequate_minute"][bucket] = summary["survivor_first_adequate_minute"].get(
                    bucket, 0) + 1
            if not response["evaluable"]:
                summary["not_evaluable"][response["reason"]] = summary["not_evaluable"].get(response["reason"], 0) + 1
                continue
            delay = response["onset_after_trigger_min"]
            label = "0" if delay == 0 else "1-14" if delay < 15 else "15-30" if delay <= 30 else "31 or later"
            summary["onset_after_trigger"][label] = summary["onset_after_trigger"].get(label, 0) + 1
            if key in keep:
                summary["survivor_onset_after_trigger"][label] = summary["survivor_onset_after_trigger"].get(label, 0) + 1
            summary["not_clear"] += not response["clear"]
            summary["not_timely"] += not response["timely"]
            # F2 (information): the minute the fall from the onset first reaches the meaningful change.
            onset, limit = response["onset"], (1.0 - settings["meaningful_change"]) * response["at_onset"]
            reached = next((minute for minute in range(onset + 1, run_.end + 1) if run_.lactate[minute] <= limit), None)
            after = None if reached is None else reached - response["trigger"]
            label = "never" if after is None else "0-30" if after <= 30 else "31-45" if after <= 45 else "46-60"
            summary["meaningful_fall_after_trigger"][label] = summary["meaningful_fall_after_trigger"].get(label, 0) + 1
            if key in keep:
                summary["survivor_meaningful_fall_after_trigger"][label] = summary[
                    "survivor_meaningful_fall_after_trigger"].get(label, 0) + 1
        result[case] = summary
    return result


def _points(run_: Trajectory, settings: dict) -> dict:
    return {minute: {"lactate": run_.lactate[minute], "D": run_.D[minute], "delivery": run_.delivery[minute],
                     "demand": run_.demand[minute], "adequate": fc.adequate(run_, minute, settings),
                     "bleeding": run_.bleeding(minute)}
            for minute in TIMES if minute <= run_.end}


def representatives(members: dict, survivors: list, verdicts: dict, settings: dict) -> dict:
    """The frozen rule (faculty_constraints.REPRESENTATIVE_POSITIONS) on the surviving region."""
    chosen = {}
    for case in CASES:
        chosen[case] = {}
        for scenario, minute in ((L1, 60), (L3, 120)):
            ranked = sorted((members[key]["runs"][case][scenario].lactate[minute], key) for key in survivors)
            if not ranked:
                chosen[case][scenario] = {}
                continue
            picks = {"lowest": ranked[0][1], "median": ranked[(len(ranked) - 1) // 2][1], "highest": ranked[-1][1]}
            chosen[case][scenario] = {}
            for position in fc.REPRESENTATIVE_POSITIONS:
                key = picks[position]
                item, detail = members[key], verdicts[key]["detail"][case]
                chosen[case][scenario][position] = {
                    "candidate": key, "levels": {factor: list(value) for factor, value in
                                                 _level_values(item["candidate"], case).items()},
                    "points": _points(item["runs"][case][scenario], settings),
                    "FD-LAC-04": detail["FD-LAC-04"] if scenario == L3 else None,
                    "FD-LAC-01": detail["FD-LAC-01"] if scenario == L1 else None}
    return chosen


# P2I-2.10 the legacy reference, last -----------------------------------------------------------

def legacy_position(settings: dict) -> dict:
    """LEGACY REFERENCE, NOT A CALIBRATION TARGET: where the family engine's lactate lies against
    the approved envelopes, read only after filtering and never by it. The engine has no oxygen
    delivery in the core's sense, so only the lactate-only parts are placed: the envelope, net
    rise and sustained decline untreated; after its own endoscopy minute, the post-haemostasis peak."""
    result = {}
    change = settings["meaningful_change"]
    for case in CASES:
        envelope = fc.ENVELOPES[case]
        untreated = [item["lactate_lab"] for item in calibration._legacy_run(case, lactate_slice.ORDERS[L1]).snapshots]
        definitive = [item["lactate_lab"] for item in calibration._legacy_run(case, lactate_slice.ORDERS[L3]).snapshots]
        points = fc.reassessments(0, len(untreated) - 1, settings)
        declines = [(early, late) for index, early in enumerate(points) for late in points[index + 1:]
                    if late - early >= settings["sustained_min"] and untreated[late] <= (1 - change) * untreated[early]]
        haemostasis = lactate_slice.endoscopy_minute(case)
        peak = max(range(haemostasis, len(definitive)), key=lambda minute: (definitive[minute], minute))
        result[case] = {
            "untreated": {minute: untreated[minute] for minute in TIMES},
            "definitive": {minute: definitive[minute] for minute in TIMES},
            "at_60": untreated[60], "envelope": [envelope["low"], envelope["high"]],
            "inside_envelope": envelope["low"] <= untreated[60] <= envelope["high"],
            "untreated_net_rise": untreated[-1] >= (1 + change) * untreated[0],
            "untreated_sustained_declines": len(declines),
            "haemostasis_minute": haemostasis, "post_haemostasis_peak": peak,
            "peak_after_haemostasis_min": peak - haemostasis,
            "clear_fall_by_120": peak < len(definitive) - 1 and definitive[-1] <= (1 - change) * definitive[peak]}
    return result


#: The reporting rules the document declares frozen (counts, dissociation classes, parameter region
#: and identifiability, representatives, sensitivity). Their text is the freeze commit's (9301a6a),
#: unchanged; this digest was pinned after the first run, over that same text.
REPORTING = (counts, per_case, sensitivity, dissociation, _level_values, parameter_region, _points, representatives)
FROZEN_REPORTING_DIGEST = "1b9e70365f7deea79733b3cbc59aa07abc5177fd4c81358853b951a70c723991"


def reporting_digest() -> str:
    text = "\n".join(inspect.getsource(function) for function in REPORTING)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# Verifications that do not filter ---------------------------------------------------------------

def fd01_summary(verdicts: dict) -> dict:
    """Why FD-LAC-01 fails, per case: a sustained decline, or only (b) 'generally rise' (no
    sustained decline but less than the meaningful net rise); and how many of the latter are inside
    the FD-LAC-02/03 envelope. Information for faculty; nothing here filters."""
    result = {}
    for case in CASES:
        envelope = fc.ENVELOPES[case]["constraint"]
        declines = only_rise = only_rise_inside = 0
        for verdict in verdicts.values():
            detail = verdict["detail"][case]
            windows = detail["FD-LAC-01"]["windows"]
            if any(window["sustained_declines"] for window in windows):
                declines += 1
            elif not detail["FD-LAC-01"]["passes"]:
                only_rise += 1
                only_rise_inside += detail[envelope]["passes"]
        result[case] = {"sustained_decline": declines, "only_generally_rises": only_rise,
                        "only_generally_rises_inside_envelope": only_rise_inside}
    return result


def robustness_start_of_minute(members: dict, verdicts: dict) -> dict:
    """The core accrues each minute's debt from the delivery at the START of that minute; the frozen
    definition reads delivery at the minute's end (one minute earlier). This rereads every run with
    the start-of-minute delivery and reports how the counts move. It never filters."""
    shifted = {}
    for key, item in members.items():
        runs = {case: {scenario: replace(run_, delivery=(run_.delivery[0],) + run_.delivery[:-1])
                       for scenario, run_ in by_scenario.items()} for case, by_scenario in item["runs"].items()}
        shifted[key] = {"candidate": item["candidate"], "runs": runs}
    found = counts(evaluate_region(shifted, fc.params()))
    primary = {key for key, verdict in verdicts.items() if verdict["all"]}
    return {"survivors": found["survivors"], "all_six": found["all_six"],
            "changed_membership": len(primary ^ set(found["all_six_keys"]))}


# The report --------------------------------------------------------------------------------------

def filter_digest() -> str:
    """Every shadow-core source (no exclusion), the calibration freeze, the scenario orders and the
    frozen definitions: a change to any of them makes the results stale."""
    orders = {name: [spec["minutes"], {str(minute): order for minute, order in spec["orders"].items()}]
              for name, spec in lactate_slice.ORDERS.items() if name in SCENARIOS}
    text = json.dumps({"freeze": calibration.frozen_digest(), "orders": orders,
                       "sources": lactate_slice.slice_sources(), "definitions": fc.definitions_digest(),
                       "pipeline": pipeline_digest(), "reporting": reporting_digest()}, sort_keys=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def decision_records() -> list:
    return [{"id": item.id, "title": item.title, "status": item.status, "decided": item.decided,
             "version": item.version, "decision": item.decision, "rationale": item.rationale,
             "observable": item.observable, "scenarios": list(item.scenarios), "cases": list(item.cases),
             "approves_parameter_values": list(item.approves_parameter_values), "scope_note": item.scope_note}
            for item in fc.FACULTY_CLINICAL_CONSTRAINTS]


def report(quick: bool = False) -> dict:
    check_frozen()
    digests = {"filter_digest": filter_digest(), "definitions_digest": fc.definitions_digest(),
               "pipeline_digest": pipeline_digest(), "freeze_digest": calibration.frozen_digest()}
    settings = fc.params()
    members = region(quick)
    verdicts = evaluate_region(members, settings)
    found = counts(verdicts)
    survivors = found["all_six_keys"]
    data = {**digests, "reporting_digest": reporting_digest(), "quick": quick,
            "admissible_candidates": len(members), "settings": settings,
            "decisions": decision_records(), "counts": {name: value for name, value in found.items()
                                                         if name != "all_six_keys"},
            "faculty_constrained_region": survivors, "per_case": per_case(verdicts),
            "sensitivity": sensitivity(members), "dissociation": dissociation(members, survivors, settings),
            "parameter_region": parameter_region(members, survivors),
            "fd01": fd01_summary(verdicts),
            "fd04": fd04_summary(members, survivors, verdicts, settings),
            "robustness_start_of_minute_delivery": robustness_start_of_minute(members, verdicts),
            "fd05": fd05_verification(members, survivors, verdicts),
            "representatives": representatives(members, survivors, verdicts, settings)}
    # Last and apart: never an input to anything above.
    data["legacy_position"] = legacy_position(settings)
    return data


# Rendering the results into docs/revision/P2I2_RESTRICCIONES_LACTATO_GI.md --------------------

OPENING, CLOSING = "<!-- generado:restricciones-lactato -->\n", "<!-- /generado:restricciones-lactato -->"
VARIANTS_ES = {
    "meaningful change 5 %": "cambio significativo 5 %", "meaningful change 20 %": "cambio significativo 20 %",
    "adequacy tolerance 5 %": "tolerancia de adecuación 5 %", "adequacy tolerance 10 %": "tolerancia de adecuación 10 %",
    "reassessment every 10 min": "reevaluación cada 10 min", "reassessment every 30 min": "reevaluación cada 30 min",
    "sustained over 15 min": "sostenido en 15 min", "sustained over 45 min": "sostenido en 45 min",
    "sustained over 60 min": "sostenido en 60 min",
    "FD-LAC-01 not applicable counts as failing": "FD-LAC-01: lo no aplicable cuenta como falla",
    "FD-LAC-01 stability ends within 60 min": "FD-LAC-01: la estabilidad termina, hacia arriba, en 60 min",
    "FD-LAC-01 stability ends within 90 min": "FD-LAC-01: la estabilidad termina, hacia arriba, en 90 min",
    "FD-LAC-02/03 as displayed (1 decimal)": "FD-LAC-02/03 con el valor redondeado a un decimal",
    "FD-LAC-04 onset within 15 min": "FD-LAC-04: comienzo ≤ 15 min", "FD-LAC-04 onset within 45 min": "FD-LAC-04: comienzo ≤ 45 min",
    "FD-LAC-04 onset only in 15-30 min": "FD-LAC-04: comienzo sólo entre 15 y 30 min",
    "FD-LAC-04 restoration sustained 15 min": "FD-LAC-04: restauración sostenida 15 min",
    "FD-LAC-04 restoration sustained 60 min": "FD-LAC-04: restauración sostenida 60 min",
    "FD-LAC-04 not evaluable counts as failing": "FD-LAC-04: lo no evaluable cuenta como falla",
    "FD-LAC-05 reference debt 20": "FD-LAC-05: deuda de referencia 20"}
REASONS_ES = {"no haemostasis with sustained restoration of delivery": "sin hemostasia con restauración sostenida",
              "too little observation after the trigger": "poca observación después del disparador",
              "no elevated lactate left to clear at the trigger": "lactato ≤ 2,0 mmol/L en el disparador"}
FACTORS_ES = {"arrival_oxygen_debt": "`arrival_oxygen_debt`", "arrival_lactate_excess": "`arrival_lactate_excess`",
              "debt_clearance_tau_min": "τ_D `debt_clearance_tau_min`",
              "debt_per_delivery_deficit": "ganancia déficit→D `debt_per_delivery_deficit`",
              "lactate_per_output_deficit": "ganancia D→lactato G `lactate_per_output_deficit`",
              "lactate_clearance_tau_min": "τ_L `lactate_clearance_tau_min`",
              "arrival_delivery_ratio": "`arrival_delivery_ratio`", "metabolic_demand_baseline": "`metabolic_demand_baseline`"}
CLASSIFICATION_ES = {"WELL CONSTRAINED": "BIEN RESTRINGIDO", "PARTIALLY CONSTRAINED": "PARCIALMENTE RESTRINGIDO",
                     "POORLY IDENTIFIED": "POCO IDENTIFICADO", "NOT IDENTIFIED": "NO IDENTIFICADO",
                     "NOT ASSESSABLE (no survivors)": "NO EVALUABLE (sin sobrevivientes)"}
LEVELS_ES = {"lower": "inferior", "midpoint": "medio", "upper": "superior", "fixed": "fijo"}
POSITIONS_ES = {"lowest": "más bajo", "median": "mediana", "highest": "más alto"}
FIRST_ADEQUATE_ES = {"never": "nunca", "0": "desde la llegada", "1-30": "min 1–30", "31-59": "min 31–59",
                     "60 or later": "min 60 o después"}
ONSET_ES = {"0": "en T* (+0 min)", "1-14": "+1–14 min", "15-30": "+15–30 min", "31 or later": "+31 min o más"}
FALL_ES = {"0-30": "≤ +30 min", "31-45": "+31–45 min", "46-60": "+46–60 min", "never": "no la alcanza"}


def _n(value, digits: int = 2) -> str:
    return lactate_slice._n(value, digits)


def _share(part: int, whole: int) -> str:
    return f"{part} ({lactate_slice._pct(part / whole)})" if whole else str(part)


def _distribution(counts_: dict, labels: dict) -> str:
    return ", ".join(f"{label}: {counts_[name]}" for name, label in labels.items() if counts_.get(name))


def render(data: dict) -> str:
    """The generated part of the P2I-2 document, from the results JSON."""
    lines = []
    add = lines.append
    found, total = data["counts"], data["counts"]["before"]
    add("## 4. Resultados (región admisible de P2F, sin candidatos nuevos)\n")
    add(f"Generado desde el filtro `{data['filter_digest']}` con las definiciones congeladas "
        f"`{data['definitions_digest']}`, la canalización `{data['pipeline_digest']}` y las reglas de informe "
        f"`{data['reporting_digest']}`, sobre el congelamiento de calibración `{data['freeze_digest']}`. Los números "
        "están en `docs/revision/P2I2_lactate_constraints.json`.\n")
    add("### 4.1 Sobrevivientes\n")
    add("| | Candidatos | Elimina | Elimina ella sola | Sobreviven sin ella |")
    add("|---|---|---|---|---|")
    add(f"| Antes del filtro | {total} | | | |")
    for row in found["discrimination"]:
        name = row["constraint"]
        add(f"| {name} | {_share(found['survivors'][name], total)} | {row['eliminates']} | {row['eliminates_alone']} | "
            f"{row['survivors_without_it']} |")
    add(f"| **Las seis juntas** | **{_share(found['all_six'], total)}** | | | |")
    add("")
    add("«Elimina ella sola»: candidatos que fallan sólo esa decisión. «Sobreviven sin ella»: los que cumplen las otras "
        "cinco. Por caso:\n")
    add("| Caso | FD-LAC-01 | FD-LAC-02/03 | FD-LAC-04 | FD-LAC-05 | FD-LAC-06 | FD-LAC-01 no aplicable | FD-LAC-04 no evaluable |")
    add("|---|---|---|---|---|---|---|---|")
    for case in CASES:
        row = data["per_case"][case]
        envelope = fc.ENVELOPES[case]["constraint"]
        reasons = "; ".join(f"{REASONS_ES[name]}: {count}" for name, count in row["FD-LAC-04 not evaluable"].items()) or "0"
        add(f"| {case} | {row['FD-LAC-01']} | {row[envelope]} ({envelope}) | {row['FD-LAC-04']} | {row['FD-LAC-05']} | "
            f"{row['FD-LAC-06']} | {row['FD-LAC-01 not applicable']} | {reasons} |")
    add("")
    add("### 4.2 Sensibilidad (una definición por vez)\n")
    add("| Variante | FD-LAC-01 | FD-LAC-02 | FD-LAC-03 | FD-LAC-04 | FD-LAC-05 | FD-LAC-06 | Las seis |")
    add("|---|---|---|---|---|---|---|---|")
    add("| **Definición principal** | " + " | ".join(str(found["survivors"][name]) for name in fc.CONSTRAINT_IDS)
        + f" | **{found['all_six']}** |")
    for row in data["sensitivity"]:
        add(f"| {VARIANTS_ES[row['variant']]} | " + " | ".join(str(row["survivors"][name]) for name in fc.CONSTRAINT_IDS)
            + f" | {row['all_six']} |")
    add("")
    add("### 4.3 FD-LAC-01 y FD-LAC-04 en detalle\n")
    add("**FD-LAC-01: por qué falla** (información para la docencia; no filtra)\n")
    add("| Caso | Con descenso sostenido | Sin descenso sostenido, pero sin subir ≥ 10 % hacia el final | De esos, "
        "dentro de la envolvente FD-LAC-02/03 |")
    add("|---|---|---|---|")
    for case in CASES:
        row = data["fd01"][case]
        add(f"| {case} | {row['sustained_decline']} | {row['only_generally_rises']} | "
            f"{row['only_generally_rises_inside_envelope']} |")
    add("")
    add("**FD-LAC-04: cuándo arranca el reloj y cuándo se ve la caída**\n")
    add("| Caso | Disparador T* (minuto: corridas) | Primer minuto con entrega adecuada en L3 | Comienzo de la tendencia "
        "tras T* | La caída llega al 10 % | Sin tendencia clara | Fuera de plazo |")
    add("|---|---|---|---|---|---|---|")
    for case in CASES:
        row = data["fd04"][case]
        triggers = ", ".join(f"{minute}: {count}" for minute, count in sorted(row["triggers"].items()))
        add(f"| {case} | {triggers} | {_distribution(row['first_adequate_minute'], FIRST_ADEQUATE_ES)} | "
            f"{_distribution(row['onset_after_trigger'], ONSET_ES)} | "
            f"{_distribution(row['meaningful_fall_after_trigger'], FALL_ES)} | {row['not_clear']} | {row['not_timely']} |")
        add(f"| {case}, región restringida | | {_distribution(row['survivor_first_adequate_minute'], FIRST_ADEQUATE_ES)} | "
            f"{_distribution(row['survivor_onset_after_trigger'], ONSET_ES) or '—'} | "
            f"{_distribution(row['survivor_meaningful_fall_after_trigger'], FALL_ES) or '—'} | | |")
    add("")
    add("En L3 la transfusión restaura la entrega antes de la hemostasia, así que en casi todas las corridas el lactato ya "
        "baja cuando arranca el reloj (comienzo en T*). La definición principal juzga si la tendencia es clara al final "
        "de la corrida, no dentro de los 15–30 min: la columna «La caída llega al 10 %» muestra cuándo se alcanza. Es "
        "una decisión pendiente para la docencia.\n")
    robust = data["robustness_start_of_minute_delivery"]
    add("**Robustez de la convención de minuto (no filtra).** El núcleo acumula la deuda de cada minuto con la entrega "
        "al comienzo de ese minuto; la definición congelada lee la entrega al final del minuto, uno antes. Releyendo "
        "todas las corridas con la entrega al comienzo del minuto: "
        + ", ".join(f"{name} {robust['survivors'][name]}" for name in fc.CONSTRAINT_IDS)
        + f"; las seis juntas, {robust['all_six']}; candidatos que cambian de grupo, {robust['changed_membership']}.\n")
    add("### 4.4 FD-LAC-05: memoria de la deuda (sin banda numérica)\n")
    add("| Caso | Lactato que deja una deuda de 60 a los 120 min (región) | Pares de la región: más deuda → más lactato "
        "residual | Mediana del residual de los sobrevivientes por deuda de llegada | Residual de los sobrevivientes | "
        "Sobrevivientes > 2,0 mmol/L a los 120 min | Normalizaciones bruscas (región) |")
    add("|---|---|---|---|---|---|---|")
    for case in CASES:
        row = data["fd05"][case]
        medians = ", ".join(f"{LEVELS_ES[level]} {_n(value)}" for level, value in
                            sorted(row["survivor_residual_median_by_arrival_debt"].items(),
                                   key=lambda item: ("lower", "midpoint", "upper").index(item[0])))
        residual = row["survivor_residual_range"]
        add(f"| {case} | {_n(row['region_debt_memory_range'][0])} a {_n(row['region_debt_memory_range'][1])} | "
            f"{row['region_pairs_higher_debt_higher_residual']} de {row['region_debt_pairs']} | {medians or '—'} | "
            f"{(_n(residual[0]) + ' a ' + _n(residual[1])) if residual else '—'} | "
            f"{row['survivors_above_normal_at_120']} de {found['all_six']} | {row['abrupt_normalizations_in_region']} |")
    add("")
    add("### 4.5 Disociación D–lactato de P2I-1, reclasificada\n")
    add("| Caso | Patrón | Región: A aceptable | B inaceptable | C transitoria | Región restringida: A | B | C |")
    add("|---|---|---|---|---|---|---|---|")
    for row in data["dissociation"]:
        region_, kept = row["region"], row["faculty_constrained"]
        pattern = row["pattern"].replace("L1 0-", "L1, 0–").replace(" min: D rises while lactate falls",
                                                                      " min: D sube mientras el lactato baja")
        add(f"| {row['case']} | {pattern} | {region_['A']} | {region_['B']} | {region_['C']} | {kept['A']} | {kept['B']} | "
            f"{kept['C']} |")
    add("")
    add("En la región restringida los ceros son por construcción, no un hallazgo aparte: el patrón de 0–60 min exige un "
        "lactato a los 60 min bajo el de llegada, que FD-LAC-02/03 excluyen, y el de 0–120 min lo excluye FD-LAC-01(b). "
        "No hay ningún caso A: en L1 la entrega nunca es adecuada mientras el lactato baja.\n")
    add("### 4.6 Región candidata restringida por la docencia (sigue CANDIDATE)\n")
    add("| Parámetro | Niveles: región → sobrevivientes | Rango P2F (57m; 72f) | Rango tras FD-LAC (57m; 72f) | "
        "Identificabilidad |")
    add("|---|---|---|---|---|")
    for row in data["parameter_region"]:
        levels = "; ".join(f"{LEVELS_ES.get(level['level'], level['level'])} "
                           f"({'/'.join(_n(level['values'][case], 2).rstrip('0').rstrip(',') for case in CASES)}): "
                           f"{level['region']} → {level['survivors']}" for level in row["levels"])
        ranges = {kind: "; ".join((_n(row["ranges"][case][kind][0]) + "–" + _n(row["ranges"][case][kind][1]))
                                   if row["ranges"][case][kind] else "—" for case in CASES)
                  for kind in ("region", "survivors")}
        add(f"| {FACTORS_ES[row['factor']]} | {levels} | {ranges['region']} | {ranges['survivors']} | "
            f"{CLASSIFICATION_ES[row['classification']]} |")
    add("")
    add("### 4.7 Trayectorias representativas de la región restringida\n")
    for case in CASES:
        for scenario, title in ((L1, "sin tratar (L1), por el lactato a los 60 min"),
                                (L3, "manejo definitivo (L3), por el lactato a los 120 min")):
            picks = data["representatives"][case][scenario]
            if not picks:
                add(f"**{case} · {title}:** sin sobrevivientes.\n")
                continue
            add(f"**{case} · {title}**\n")
            add("| Representante | Parámetros | " + " | ".join(f"{minute} min" for minute in TIMES) + " | Detalle |")
            add("|---|---|" + "---|" * len(TIMES) + "---|")
            for position in fc.REPRESENTATIVE_POSITIONS:
                item = picks[position]
                levels = item["levels"]
                parameters = (f"deuda {_n(levels['arrival_oxygen_debt'][1], 0)}, exceso "
                              f"{_n(levels['arrival_lactate_excess'][1], 1)}, entrega {_n(levels['arrival_delivery_ratio'][1])}, "
                              f"τ_D {_n(levels['debt_clearance_tau_min'][1], 0)}, G {_n(levels['lactate_per_output_deficit'][1], 0)}, "
                              f"τ_L {_n(levels['lactate_clearance_tau_min'][1], 0)}")
                points = item["points"]
                cells = " | ".join(
                    f"{_n(points[str(minute)]['lactate'])} (D {_n(points[str(minute)]['D'], 0)}; entrega "
                    f"{_n(points[str(minute)]['delivery'])}{'' if points[str(minute)]['adequate'] else ', inadecuada'})"
                    for minute in TIMES)
                if scenario == L3:
                    response = item["FD-LAC-04"]
                    detail = (f"hemostasia {response['haemostasis']}, T* {response['trigger']}, comienzo "
                              f"{response.get('onset', '—')} (+{response.get('onset_after_trigger_min', '—')} min)")
                else:
                    windows = item["FD-LAC-01"]["windows"]
                    detail = "; ".join(f"tramo inadecuado {window['window'][0]}–{window['window'][1]}" for window in windows)
                add(f"| {POSITIONS_ES[position]} | {parameters} | {cells} | {detail} |")
            add("")
    add("### 4.8 REFERENCIA HEREDADA — NO ES OBJETIVO DE CALIBRACIÓN\n")
    add("Se ubica después del filtro y nunca entró en él. El motor de familias no tiene una entrega de O2 como la del "
        "núcleo, así que sólo se ubican las partes que dependen del lactato.\n")
    add("| Caso | Sin tratar: " + ", ".join(f"{minute}" for minute in TIMES) + " min | A los 60 min, frente a la "
        "envolvente | Sube ≥ 10 % hacia los 120 min | Descensos sostenidos | Manejo definitivo: "
        + ", ".join(f"{minute}" for minute in TIMES) + " min | Tras su endoscopia (min 60) |")
    add("|---|---|---|---|---|---|---|")
    for case in CASES:
        row = data["legacy_position"][case]
        untreated = "; ".join(_n(row["untreated"][str(minute)], 1) for minute in TIMES)
        definitive = "; ".join(_n(row["definitive"][str(minute)], 1) for minute in TIMES)
        inside = "dentro" if row["inside_envelope"] else "fuera"
        if row["post_haemostasis_peak"] == 120:
            after = "sin comienzo de una tendencia a la baja: el pico (regla congelada) es el minuto 120"
        else:
            after = (f"pico en el minuto {row['post_haemostasis_peak']} (+{row['peak_after_haemostasis_min']}); "
                     f"{'baja ≥ 10 % hacia los 120' if row['clear_fall_by_120'] else 'no baja ≥ 10 % hacia los 120'}")
        add(f"| {case} | {untreated} | {_n(row['at_60'], 1)}: {inside} de {_n(row['envelope'][0], 1)}–"
            f"{_n(row['envelope'][1], 1)} | {'sí' if row['untreated_net_rise'] else 'no'} | "
            f"{row['untreated_sustained_declines']} | {definitive} | {after} |")
    add("")
    return "\n".join(lines)


def apply(document: str, block: str) -> str:
    return apply_block(document, block, OPENING, CLOSING)


# The decision record in the P2I-1 faculty document ---------------------------------------------

DECISIONS_OPENING, DECISIONS_CLOSING = "<!-- generado:decisiones-lactato -->\n", "<!-- /generado:decisiones-lactato -->"
#: The option each answer selects among those P2I-1 offered (§10 of the P2I-1 document).
SELECTION_ES = {
    "FD-LAC-01": "C. subir en general; una estabilidad breve es aceptable",
    "FD-LAC-02": "4,4–7,0 mmol/L a los 60 min: envolvente clínica, no un objetivo",
    "FD-LAC-03": "3,4–5,5 mmol/L a los 60 min: envolvente clínica, no un objetivo",
    "FD-LAC-04": "15–30 min: inicio de una tendencia clara a la baja",
    "FD-LAC-05": "depender de la deuda acumulada; puede seguir levemente elevado; sin normalización obligatoria",
    "FD-LAC-06": "SÓLO SI LA ENTREGA ES ADECUADA",
}
OBSERVABLES_ES = {
    "FD-LAC-01": "trayectoria del lactato con sangrado activo y entrega de O2 inadecuada",
    "FD-LAC-02": "lactato (mmol/L) a los 60 min sin tratar",
    "FD-LAC-03": "lactato (mmol/L) a los 60 min sin tratar",
    "FD-LAC-04": "inicio de una tendencia clara a la baja tras la hemostasia y la restauración sostenida de la entrega",
    "FD-LAC-05": "lactato residual a los 120 min del manejo definitivo y su dependencia de la deuda de O2 acumulada",
    "FD-LAC-06": "trayectoria del lactato con sangrado activo, según la adecuación de la entrega",
}


def render_decisions() -> str:
    """§12 of docs/revision/P2I_DECISION_LACTATO_GI.md, from the registry (never by hand)."""
    lines = ["## 12. Registro de decisiones docentes (P2I-2)\n",
             f"Respondidas por la docencia y registradas el {fc.DECIDED}, versión «{fc.VERSION}», en "
             "`clinical_core/faculty_constraints.py`. Son restricciones clínicas de comportamiento del lactato "
             "observable, con estado FACULTY_APPROVED. **No aprueban ningún valor de parámetro oculto:** "
             + ", ".join(f"`{name}`" for name in fc.HIDDEN_PARAMETERS)
             + " siguen CANDIDATE, y nada de esto entra en los registros de autoridad de migración. El texto que "
             "rige es el original, en inglés. La docencia no dio un fundamento aparte: la columna «Frase clave» cita "
             "la frase de su propio texto que lo expresa. Su aplicación a la región candidata está en "
             "`docs/revision/P2I2_RESTRICCIONES_LACTATO_GI.md`.\n",
             "| ID | Estado | Fecha · versión | Observable | Escenarios · casos | Decisión (texto original) | "
             "Frase clave del texto docente | Valores de parámetros que aprueba |",
             "|---|---|---|---|---|---|---|---|"]
    for item in fc.FACULTY_CLINICAL_CONSTRAINTS:
        lines.append(f"| {item.id} | {item.status} | {item.decided} · {item.version} | {OBSERVABLES_ES[item.id]} | "
                     f"{', '.join(item.scenarios)} · {', '.join(case[-3:] for case in item.cases)} | "
                     f"«{item.decision}» | «{item.rationale}» | ninguno |")
    lines.append("")
    return "\n".join(lines)


def apply_block(document: str, block: str, opening: str, closing: str) -> str:
    start = document.index(opening) + len(opening)
    end = document.index(closing)
    return document[:start] + block + "\n" + document[end:]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--write", type=Path, help="render a results JSON into this document (with --json)")
    parser.add_argument("--json", type=Path)
    parser.add_argument("--decisions", type=Path, help="write the decision record into the P2I-1 document")
    args = parser.parse_args(argv)
    if args.decisions:
        document = args.decisions.read_text(encoding="utf-8")
        args.decisions.write_text(apply_block(document, render_decisions(), DECISIONS_OPENING, DECISIONS_CLOSING),
                                  encoding="utf-8")
        return 0
    if args.write:
        data = json.loads(args.json.read_text(encoding="utf-8"))
        args.write.write_text(apply(args.write.read_text(encoding="utf-8"), render(data)), encoding="utf-8")
        return 0
    text = json.dumps(report(args.quick), indent=1, sort_keys=True, default=str)
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "lactate_constraints.json").write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
