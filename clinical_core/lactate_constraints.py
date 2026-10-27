"""P2I-2R: apply the faculty-approved GI lactate constraints (FD-LAC-01..06) to P2F's admissible region.

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

The operational definitions are frozen: ``faculty_constraints.definitions_digest``, this module's
``pipeline_digest`` (how a core run becomes a ``Trajectory`` and how the region is evaluated) and
its ``reporting_digest`` (counts, classes, region, summaries, representatives, legacy position)
are pinned below before any filtering ran; the filter refuses to run on others. P2I-2R refroze all
three after the faculty clarified FD-LAC-01, FD-LAC-04 and FD-LAC-05 (2026-10-26).
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

FROZEN_DEFINITIONS_DIGEST = "092c32cf5a20cbf62e3e9df32a47896ccdef701f97170634740a8f8399d7982a"
FROZEN_PIPELINE_DIGEST = "4c326d6e60e9a96cde713afcf0fc38b14cf877b8521e60b7e33d584b24037394"
CASES = fc.CASES
L1, L2, L3 = fc.UNTREATED, fc.PARTIAL, fc.DEFINITIVE
SCENARIOS = (L1, L2, L3)
TIMES = lactate_slice.TIMES
KINETICS = ("debt_clearance_tau_min", "debt_per_delivery_deficit", "lactate_per_output_deficit",
            "lactate_clearance_tau_min")
#: P2I-2P (2026-10-27): the committed results were filtered on the pre-P2I-2P core. The faculty
#: stopped further filtering ("Do NOT continue filtering P2I-2R yet") until the oxygen-delivery
#: review lands and FD-LAC-06 is operationalized; the results stay as committed, stale by
#: construction, and this module's command refuses to produce new ones. None once a refilter is
#: authorized and run. P2I-2T (2026-10-27) then replaced the GI module's two independent drifts
#: with the shared blood state, which changed the GI trajectories and the calibration freeze: the
#: results also keep the freeze they were filtered under (``freeze_digest``).
RESULTS_PENDING_REFILTER = {
    "filter_digest": "58e988cf6b1c3d5bebab254305fdeec97ace1c11775db4753b458781a888d1bb",
    "freeze_digest": "152abc6cf3e2812fcade237f60db0430df78749e09f4199b0a0fff13a0dd4338",
    "since": "2026-10-27",
    "reason": "P2I-2P changed the shadow core's oxygen-debt formulation (neutral extraction reserve 1: canonical "
              "numbers unchanged, sources changed) and FD-LAC-06's trajectory semantics (FD-LAC-06 faculty "
              "decision, recorded in P2I-2P) are not yet operationalized; P2I-2T then replaced the two "
              "independent haemorrhage drifts with the shared blood state (GI trajectories and the calibration "
              "freeze changed); refiltering is not authorized",
}


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
    """Per case and constraint: how many runs pass, and every outcome (PASS, FAIL, NOT_APPLICABLE,
    NOT_EVALUABLE with its reason, ALREADY_NORMALIZED)."""
    table = {}
    for case in CASES:
        row = {}
        for item in fc.FACULTY_CLINICAL_CONSTRAINTS:
            if case not in item.cases:
                continue
            outcomes: dict = {}
            for verdict in verdicts.values():
                result = verdict["detail"][case][item.id]
                label = result["status"] + (f": {result['reason']}" if "reason" in result else "")
                outcomes[label] = outcomes.get(label, 0) + 1
            row[item.id] = {"passes": sum(1 for verdict in verdicts.values()
                                          if verdict["detail"][case][item.id]["passes"]),
                            "outcomes": dict(sorted(outcomes.items()))}
        table[case] = row
    return table


def sensitivity(members: dict) -> list:
    rows = []
    for name, overrides in fc.SENSITIVITY.items():
        found = counts(evaluate_region(members, fc.params(**overrides)))
        rows.append({"variant": name, "overrides": overrides, "survivors": found["survivors"],
                     "all_six": found["all_six"]})
    return rows


# The P2I-1 dissociations, revisited ----------------------------------------------------------

def dissociation(members: dict, survivors: list, settings: dict) -> list:
    """P2I-1's 'D rises while lactate falls' (untreated, 0-60 and 0-120 min), classified.

    B UNACCEPTABLE: a substantial sustained decline inside a window of active bleeding with
      inadequate delivery within the span (what FD-LAC-01/06 forbid);
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


# The region after filtering ----------------------------------------------------------------------

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


# Verifications and summaries that do not filter ------------------------------------------------

def fd01_summary(members: dict, verdicts: dict, settings: dict) -> dict:
    """FD-LAC-01's reasons, per case, and the untreated runs that pass it (no substantial sustained
    decline before 60 min) but decline after 60 min with inadequate delivery (FD-LAC-06's to judge)."""
    result = {}
    for case in CASES:
        before, after_only = 0, 0
        for key, verdict in verdicts.items():
            detail = verdict["detail"][case]
            if detail["FD-LAC-01"]["status"] == fc.FAIL:
                before += 1
            elif any(item["scenario"] == L1 for item in detail["FD-LAC-06"]["violations"]):
                after_only += 1
        result[case] = {"sustained_decline_before_60": before, "untreated_decline_only_after_60": after_only}
    return result


def _fall_bin(reduction: float) -> str:
    return ("no decrease" if reduction <= 0 else "0-5 %" if reduction < 0.05 else "5-10 %" if reduction < 0.10
            else "10-15 %" if reduction < 0.15 else "15 % or more")


def fd04_summary(members: dict, survivors: list, verdicts: dict, settings: dict) -> dict:
    """FD-LAC-04: where T* falls, every outcome, the reduction at T* + 30 (binned; region and
    survivors) and how many survivors would meet each reported threshold (information only)."""
    keep, result = set(survivors), {}
    for case in CASES:
        summary = {"triggers": {}, "first_adequate_minute": {}, "reduction": {}, "survivor_reduction": {},
                   "survivor_thresholds": {f"{threshold:g}": 0 for threshold in fc.REPORTED_FALL_THRESHOLDS},
                   "survivor_evaluated": 0}
        for key, verdict in verdicts.items():
            response = verdict["detail"][case]["FD-LAC-04"]
            trigger = str(response["trigger"])
            summary["triggers"][trigger] = summary["triggers"].get(trigger, 0) + 1
            run_ = members[key]["runs"][case][L3]
            first = next((minute for minute in range(run_.end + 1) if fc.adequate(run_, minute, settings)), None)
            bucket = "never" if first is None else "0" if first == 0 else "1-30" if first <= 30 else "31-59" \
                if first < 60 else "60 or later"
            summary["first_adequate_minute"][bucket] = summary["first_adequate_minute"].get(bucket, 0) + 1
            if "reduction_at_window" not in response:
                continue
            reduction = response["reduction_at_window"]
            label = _fall_bin(reduction)
            summary["reduction"][label] = summary["reduction"].get(label, 0) + 1
            if key in keep:
                summary["survivor_reduction"][label] = summary["survivor_reduction"].get(label, 0) + 1
                summary["survivor_evaluated"] += 1
                for threshold in fc.REPORTED_FALL_THRESHOLDS:
                    if reduction > 0 and reduction >= threshold:
                        summary["survivor_thresholds"][f"{threshold:g}"] += 1
        result[case] = summary
    return result


def survivor_reductions(survivors: list, verdicts: dict) -> list:
    """FD-LAC-04's actual reduction at T* + 30 for each surviving candidate (or its outcome)."""
    rows = []
    for key in survivors:
        row = {"candidate": key}
        for case in CASES:
            response = verdicts[key]["detail"][case]["FD-LAC-04"]
            row[case] = {"status": response["status"], "trigger": response["trigger"],
                         "at_trigger": response.get("at_trigger"), "at_trigger_plus_30": response.get(
                             "at_trigger_plus_window"), "reduction": response.get("reduction_at_window")}
        rows.append(row)
    return rows


def fd05_verification(members: dict, survivors: list, verdicts: dict) -> dict:
    """FD-LAC-05 on the survivors (residual range, below L(T*)) and the debt memory on the region:
    siblings that differ only in arrival debt (lower against upper, same delivery) and whether the
    higher debt leaves the higher residual. Nothing here filters."""
    result = {}
    for case in CASES:
        by_debt: dict = {}
        for key in survivors:
            item = members[key]
            by_debt.setdefault(item["candidate"].debt, []).append(item["runs"][case][L3].lactate[-1])
        pairs, higher = 0, 0
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
        memory = sorted(verdict["detail"][case]["FD-LAC-05"]["debt_memory_at_reference_debt"]
                        for verdict in verdicts.values())
        result[case] = {
            "survivor_residual_median_by_arrival_debt": {level: lactate_slice._quantile(sorted(values), 0.5)
                                                         for level, values in sorted(by_debt.items())},
            "survivor_residual_range": [residual[0], residual[-1]] if residual else None,
            "survivors_above_2_at_120": sum(1 for value in residual if value > fc.PRIMARY["already_normalized_mmol_l"]),
            "region_debt_pairs": pairs, "region_pairs_higher_debt_higher_residual": higher,
            "region_debt_memory_range": [memory[0], memory[-1]]}
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
                    "FD-LAC-05": detail["FD-LAC-05"] if scenario == L3 else None,
                    "FD-LAC-01": detail["FD-LAC-01"] if scenario == L1 else None}
    return chosen


# The legacy reference, last -----------------------------------------------------------------------

def legacy_position(settings: dict) -> dict:
    """LEGACY REFERENCE, NOT A CALIBRATION TARGET: where the family engine's lactate lies against the
    revised constraints, read only after filtering and never by it. The engine has no oxygen delivery
    in the core's sense, so only the lactate parts are placed: the 60-min envelope; substantial
    sustained declines untreated, before and after 60 min (as if delivery were inadequate throughout);
    and, after its own endoscopy minute taken as T*, the fall by T* + 30, the 120-min envelope and
    L120 < L(T*)."""
    result = {}
    change, span = settings["meaningful_change"], settings["sustained_min"]
    for case in CASES:
        envelope, late = fc.ENVELOPES[case], fc.ENVELOPES_120[case]
        untreated = [item["lactate_lab"] for item in calibration._legacy_run(case, lactate_slice.ORDERS[L1]).snapshots]
        definitive = [item["lactate_lab"] for item in calibration._legacy_run(case, lactate_slice.ORDERS[L3]).snapshots]

        def declines(first: int, last: int) -> int:
            points = fc.reassessments(first, last, settings)
            return sum(1 for index, early in enumerate(points) for later in points[index + 1:]
                       if later - early >= span and untreated[later] <= (1 - change) * untreated[early])
        trigger = lactate_slice.endoscopy_minute(case)
        window = settings["fd04_window_min"]
        at, after = definitive[trigger], definitive[trigger + window]
        result[case] = {
            "untreated": {minute: untreated[minute] for minute in TIMES},
            "definitive": {minute: definitive[minute] for minute in TIMES},
            "at_60": untreated[60], "envelope": [envelope["low"], envelope["high"]],
            "inside_envelope": envelope["low"] <= untreated[60] <= envelope["high"],
            "untreated_sustained_declines_before_60": declines(0, 60),
            "untreated_sustained_declines_0_120": declines(0, len(untreated) - 1),
            "trigger_minute": trigger, "at_trigger": at, "at_trigger_plus_30": after,
            "falls_by_trigger_plus_30": after < at, "reduction_at_30": (at - after) / at,
            "at_120": definitive[120], "envelope_120": [late["low"], late["high"]],
            "inside_envelope_120": late["low"] <= definitive[120] <= late["high"],
            "below_trigger_at_120": definitive[120] < at}
    return result


#: The reporting rules, frozen with the definitions before filtering.
REPORTING = (counts, per_case, sensitivity, dissociation, _level_values, parameter_region, fd01_summary, _fall_bin,
             fd04_summary, survivor_reductions, fd05_verification, robustness_start_of_minute, _points,
             representatives, legacy_position)
FROZEN_REPORTING_DIGEST = "9316d312946cb4b03b6f0ec29c396b312d8518c0a5eeceee7f2f9ecf63b62be2"


def reporting_digest() -> str:
    text = "\n".join(inspect.getsource(function) for function in REPORTING)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# The report --------------------------------------------------------------------------------------

def filter_digest() -> str:
    """Every shadow-core source (no exclusion), the calibration freeze, the scenario orders and the
    frozen definitions, pipeline and reporting rules: a change to any of them makes the results stale."""
    orders = {name: [spec["minutes"], {str(minute): order for minute, order in spec["orders"].items()}]
              for name, spec in lactate_slice.ORDERS.items() if name in SCENARIOS}
    text = json.dumps({"freeze": calibration.frozen_digest(), "orders": orders,
                       "sources": lactate_slice.slice_sources(), "definitions": fc.definitions_digest(),
                       "pipeline": pipeline_digest(), "reporting": reporting_digest()}, sort_keys=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def decision_records() -> list:
    return [{"id": item.id, "title": item.title, "status": item.status, "decided": item.decided,
             "clarified": item.clarified, "version": item.version, "decision": item.decision,
             "clarification": item.clarification, "rationale": item.rationale, "observable": item.observable,
             "scenarios": list(item.scenarios), "cases": list(item.cases),
             "approves_parameter_values": list(item.approves_parameter_values), "scope_note": item.scope_note}
            for item in fc.FACULTY_CLINICAL_CONSTRAINTS]


def report(quick: bool = False) -> dict:
    check_frozen()
    digests = {"filter_digest": filter_digest(), "definitions_digest": fc.definitions_digest(),
               "pipeline_digest": pipeline_digest(), "reporting_digest": reporting_digest(),
               "freeze_digest": calibration.frozen_digest()}
    settings = fc.params()
    members = region(quick)
    verdicts = evaluate_region(members, settings)
    found = counts(verdicts)
    survivors = found["all_six_keys"]
    data = {**digests, "quick": quick, "admissible_candidates": len(members), "settings": settings,
            "decisions": decision_records(), "confirmed_definitions": list(fc.FACULTY_CONFIRMED_DEFINITIONS),
            "counts": {name: value for name, value in found.items() if name != "all_six_keys"},
            "faculty_constrained_region": survivors, "per_case": per_case(verdicts),
            "sensitivity": sensitivity(members), "dissociation": dissociation(members, survivors, settings),
            "parameter_region": parameter_region(members, survivors),
            "fd01": fd01_summary(members, verdicts, settings),
            "fd04": fd04_summary(members, survivors, verdicts, settings),
            "survivor_reductions": survivor_reductions(survivors, verdicts),
            "fd05": fd05_verification(members, survivors, verdicts),
            "robustness_start_of_minute_delivery": robustness_start_of_minute(members, verdicts),
            "representatives": representatives(members, survivors, verdicts, settings)}
    # Last and apart: never an input to anything above.
    data["legacy_position"] = legacy_position(settings)
    return data


# Rendering the results into docs/revision/P2I2_RESTRICCIONES_LACTATO_GI.md --------------------

OPENING, CLOSING = "<!-- generado:restricciones-lactato -->\n", "<!-- /generado:restricciones-lactato -->"
VARIANTS_ES = {
    "decline threshold 5 %": "umbral de descenso 5 %", "decline threshold 15 %": "umbral de descenso 15 %",
    "decline threshold 20 %": "umbral de descenso 20 %",
    "adequacy tolerance 5 %": "tolerancia de adecuación 5 %", "adequacy tolerance 10 %": "tolerancia de adecuación 10 %",
    "reassessment every 10 min": "reevaluación cada 10 min", "reassessment every 30 min": "reevaluación cada 30 min",
    "sustained over 15 min": "sostenido en 15 min", "sustained over 45 min": "sostenido en 45 min",
    "sustained over 60 min": "sostenido en 60 min",
    "FD-LAC-01 not applicable counts as failing": "FD-LAC-01: lo no aplicable cuenta como falla",
    "FD-LAC-02/03 as displayed (1 decimal)": "FD-LAC-02/03 con el valor redondeado a un decimal",
    "FD-LAC-04 fall >= 5 % by T*+30": "FD-LAC-04: caída ≥ 5 % en T*+30 (sólo sensibilidad)",
    "FD-LAC-04 fall >= 10 % by T*+30": "FD-LAC-04: caída ≥ 10 % en T*+30 (sólo sensibilidad)",
    "FD-LAC-04 fall >= 15 % by T*+30": "FD-LAC-04: caída ≥ 15 % en T*+30 (sólo sensibilidad)",
    "FD-LAC-04 without the ongoing-clearance check": "FD-LAC-04 sin la condición de aclaramiento en curso",
    "FD-LAC-04 delivery sustained 15 min": "FD-LAC-04: entrega sostenida 15 min",
    "FD-LAC-04 delivery sustained 60 min": "FD-LAC-04: entrega sostenida 60 min",
    "FD-LAC-04 not evaluable counts as failing": "FD-LAC-04: lo no evaluable cuenta como falla",
    "FD-LAC-05 as displayed (1 decimal)": "FD-LAC-05 con el valor redondeado a un decimal",
    "FD-LAC-05 decline not required when already normalized": "FD-LAC-05: sin exigir L120 < L(T*) si L(T*) ≤ 2,0",
    "FD-LAC-05 not evaluable counts as failing": "FD-LAC-05: lo no evaluable cuenta como falla"}
STATUS_ES = {"PASS": "pasa", "FAIL": "falla", "NOT_APPLICABLE": "NOT_APPLICABLE", "NOT_EVALUABLE": "NOT_EVALUABLE",
             "ALREADY_NORMALIZED": "ALREADY_NORMALIZED"}
REASONS_ES = {"no haemostasis with sustained adequate delivery": "sin hemostasia con entrega adecuada sostenida",
              "less than 30 min of follow-up after T*": "menos de 30 min de seguimiento tras T*",
              "delivery ceased to be adequate within 30 min of T*": "la entrega dejó de ser adecuada antes de T*+30",
              "no T* within the run": "sin T*",
              "delivery not adequate throughout from T* to 120 min": "entrega no adecuada en todo T*–120"}
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
FALL_ES = {"no decrease": "sin descenso", "0-5 %": "0–5 %", "5-10 %": "5–10 %", "10-15 %": "10–15 %",
           "15 % or more": "≥ 15 %"}


def _n(value, digits: int = 2) -> str:
    return lactate_slice._n(value, digits)


def _share(part: int, whole: int) -> str:
    return f"{part} ({lactate_slice._pct(part / whole)})" if whole else str(part)


def _distribution(counts_: dict, labels: dict) -> str:
    return ", ".join(f"{label}: {counts_[name]}" for name, label in labels.items() if counts_.get(name))


def _outcomes(outcomes: dict) -> str:
    parts = []
    for label, count in outcomes.items():
        status, _, reason = label.partition(": ")
        text = STATUS_ES[status] + (f" ({REASONS_ES.get(reason, reason)})" if reason else "")
        parts.append(f"{text}: {count}")
    return "; ".join(parts)


def _percent(value) -> str:
    return "—" if value is None else f"{_n(100 * value, 1)} %"


def render(data: dict) -> str:
    """The generated part of the P2I-2R document, from the results JSON."""
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
        "cinco. Resultado de cada corrida, por caso (NOT_APPLICABLE, NOT_EVALUABLE y ALREADY_NORMALIZED no cuentan como "
        "contradicción):\n")
    add("| Caso | Decisión | Pasan | Resultados |")
    add("|---|---|---|---|")
    for case in CASES:
        for name, row in data["per_case"][case].items():
            add(f"| {case} | {name} | {row['passes']} | {_outcomes(row['outcomes'])} |")
    add("")
    add("### 4.2 Sensibilidad (una definición por vez; ninguna variante selecciona candidatos)\n")
    add("| Variante | FD-LAC-01 | FD-LAC-02 | FD-LAC-03 | FD-LAC-04 | FD-LAC-05 | FD-LAC-06 | Las seis |")
    add("|---|---|---|---|---|---|---|---|")
    add("| **Definición principal** | " + " | ".join(str(found["survivors"][name]) for name in fc.CONSTRAINT_IDS)
        + f" | **{found['all_six']}** |")
    for row in data["sensitivity"]:
        add(f"| {VARIANTS_ES[row['variant']]} | " + " | ".join(str(row["survivors"][name]) for name in fc.CONSTRAINT_IDS)
            + f" | {row['all_six']} |")
    add("")
    add("### 4.3 FD-LAC-01 y FD-LAC-04 en detalle\n")
    add("| Caso | FD-LAC-01: descenso sustancial sostenido antes de los 60 min | Sin tratar: pasa FD-LAC-01 pero baja de forma "
        "sostenida después de los 60 min (lo juzga FD-LAC-06) |")
    add("|---|---|---|")
    for case in CASES:
        row = data["fd01"][case]
        add(f"| {case} | {row['sustained_decline_before_60']} | {row['untreated_decline_only_after_60']} |")
    add("")
    add("**FD-LAC-04: T\\*, primer minuto con entrega adecuada en L3 y reducción a los 30 min**\n")
    add("| Caso | T* (minuto: corridas) | Primer minuto con entrega adecuada | Reducción en T*+30 (corridas evaluadas) | "
        "Reducción en T*+30 (sobrevivientes) | Sobrevivientes que alcanzarían: cualquier descenso / ≥ 5 % / ≥ 10 % / ≥ 15 % |")
    add("|---|---|---|---|---|---|")
    for case in CASES:
        row = data["fd04"][case]
        triggers = ", ".join(f"{minute}: {count}" for minute, count in sorted(row["triggers"].items()))
        thresholds = " / ".join(str(row["survivor_thresholds"][f"{threshold:g}"])
                                for threshold in fc.REPORTED_FALL_THRESHOLDS)
        add(f"| {case} | {triggers} | {_distribution(row['first_adequate_minute'], FIRST_ADEQUATE_ES)} | "
            f"{_distribution(row['reduction'], FALL_ES) or '—'} | {_distribution(row['survivor_reduction'], FALL_ES) or '—'} | "
            f"{thresholds} (de {row['survivor_evaluated']} evaluados) |")
    add("")
    add("Los umbrales de ≥ 5 %, 10 % y 15 % se informan sólo como sensibilidad: ninguno está aprobado ni selecciona "
        "candidatos. La reducción de cada sobreviviente está en el anexo (§4.9).\n")
    robust = data["robustness_start_of_minute_delivery"]
    add("**Robustez de la convención de minuto (no filtra).** El núcleo acumula la deuda de cada minuto con la entrega "
        "al comienzo de ese minuto; la definición congelada lee la entrega al final del minuto, uno antes. Releyendo "
        "todas las corridas con la entrega al comienzo del minuto: "
        + ", ".join(f"{name} {robust['survivors'][name]}" for name in fc.CONSTRAINT_IDS)
        + f"; las seis juntas, {robust['all_six']}; candidatos que cambian de grupo, {robust['changed_membership']}.\n")
    add("### 4.4 FD-LAC-05: envolvente a los 120 min y memoria de la deuda\n")
    add("| Caso | Residual de los sobrevivientes a los 120 min | Mediana del residual por deuda de llegada | "
        "Sobrevivientes > 2,0 mmol/L a los 120 min | Lactato que deja una deuda de 60 a los 120 min (región) | "
        "Pares de la región: más deuda → más residual |")
    add("|---|---|---|---|---|---|")
    for case in CASES:
        row = data["fd05"][case]
        medians = ", ".join(f"{LEVELS_ES[level]} {_n(value)}" for level, value in
                            sorted(row["survivor_residual_median_by_arrival_debt"].items(),
                                   key=lambda item: ("lower", "midpoint", "upper").index(item[0])))
        residual = row["survivor_residual_range"]
        add(f"| {case} | {(_n(residual[0]) + ' a ' + _n(residual[1])) if residual else '—'} | {medians or '—'} | "
            f"{row['survivors_above_2_at_120']} de {found['all_six']} | {_n(row['region_debt_memory_range'][0])} a "
            f"{_n(row['region_debt_memory_range'][1])} | {row['region_pairs_higher_debt_higher_residual']} de "
            f"{row['region_debt_pairs']} |")
    add("")
    add("### 4.5 Disociación D–lactato de P2I-1, reclasificada con las reglas vigentes\n")
    add("| Caso | Patrón | Región: A aceptable | B inaceptable | C transitoria | Región restringida: A | B | C |")
    add("|---|---|---|---|---|---|---|---|")
    for row in data["dissociation"]:
        region_, kept = row["region"], row["faculty_constrained"]
        pattern = row["pattern"].replace("L1 0-", "L1, 0–").replace(" min: D rises while lactate falls",
                                                                      " min: D sube mientras el lactato baja")
        add(f"| {row['case']} | {pattern} | {region_['A']} | {region_['B']} | {region_['C']} | {kept['A']} | {kept['B']} | "
            f"{kept['C']} |")
    add("")
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
                    detail = f"hemostasia {response['haemostasis']}, T* {response['trigger']}, {STATUS_ES[response['status']]}"
                    if "reduction_at_window" in response:
                        detail += (f"; L(T*) {_n(response['at_trigger'])} → L(T*+30) "
                                   f"{_n(response['at_trigger_plus_window'])} ({_percent(response['reduction_at_window'])})")
                else:
                    windows = item["FD-LAC-01"]["windows"]
                    detail = "; ".join(f"tramo inadecuado {window['window'][0]}–{window['window'][1]}" for window in windows)
                add(f"| {POSITIONS_ES[position]} | {parameters} | {cells} | {detail} |")
            add("")
    add("### 4.8 REFERENCIA HEREDADA — NO ES OBJETIVO DE CALIBRACIÓN\n")
    add("Se ubica después del filtro y nunca entró en él. El motor de familias no tiene una entrega de O2 como la del "
        "núcleo, así que sólo se ubican las partes que dependen del lactato: los descensos se cuentan como si la entrega "
        "fuera inadecuada en todo momento, y T* se toma en el minuto de su propia endoscopia.\n")
    add("| Caso | Sin tratar: " + ", ".join(f"{minute}" for minute in TIMES) + " min | 60 min frente a la envolvente | "
        "Descensos sustanciales sostenidos (antes de 60; 0–120) | Manejo definitivo: "
        + ", ".join(f"{minute}" for minute in TIMES) + " min | T* + 30 | 120 min frente a la envolvente | L120 < L(T*) |")
    add("|---|---|---|---|---|---|---|---|")
    for case in CASES:
        row = data["legacy_position"][case]
        untreated = "; ".join(_n(row["untreated"][str(minute)], 1) for minute in TIMES)
        definitive = "; ".join(_n(row["definitive"][str(minute)], 1) for minute in TIMES)
        add(f"| {case} | {untreated} | {_n(row['at_60'], 1)}: {'dentro' if row['inside_envelope'] else 'fuera'} de "
            f"{_n(row['envelope'][0], 1)}–{_n(row['envelope'][1], 1)} | {row['untreated_sustained_declines_before_60']}; "
            f"{row['untreated_sustained_declines_0_120']} | {definitive} | T* {row['trigger_minute']}: "
            f"{_n(row['at_trigger'], 1)} → {_n(row['at_trigger_plus_30'], 1)} "
            f"({'baja' if row['falls_by_trigger_plus_30'] else 'no baja'}; reducción {_percent(row['reduction_at_30'])}) | "
            f"{_n(row['at_120'], 1)}: {'dentro' if row['inside_envelope_120'] else 'fuera'} de "
            f"{_n(row['envelope_120'][0], 1)}–{_n(row['envelope_120'][1], 1)} | "
            f"{'sí' if row['below_trigger_at_120'] else 'no'} |")
    add("")
    add("### 4.9 Anexo: reducción del lactato en T\\* + 30 min de cada sobreviviente\n")
    if not data["survivor_reductions"]:
        add("Sin sobrevivientes.\n")
    else:
        add("| Candidato | " + " | ".join(f"{case}: T*, L(T*) → L(T*+30), reducción" for case in CASES) + " |")
        add("|---|" + "---|" * len(CASES))
        for row in data["survivor_reductions"]:
            cells = []
            for case in CASES:
                item = row[case]
                if item["reduction"] is None:
                    cells.append(f"T* {item['trigger']}: {STATUS_ES[item['status']]}")
                else:
                    cells.append(f"T* {item['trigger']}: {_n(item['at_trigger'])} → {_n(item['at_trigger_plus_30'])}, "
                                 f"{_percent(item['reduction'])}")
            add(f"| `{row['candidate']}` | " + " | ".join(cells) + " |")
        add("")
    return "\n".join(lines)


def apply(document: str, block: str) -> str:
    return apply_block(document, block, OPENING, CLOSING)


# The decision record in the P2I-1 faculty document ---------------------------------------------

DECISIONS_OPENING, DECISIONS_CLOSING = "<!-- generado:decisiones-lactato -->\n", "<!-- /generado:decisiones-lactato -->"
#: The option each answer selects among those P2I-1 offered (§10 of the P2I-1 document), as clarified.
SELECTION_ES = {
    "FD-LAC-01": "C. subir o seguir elevado en general; sin descenso sostenido y sustancial antes de los 60 min; "
                 "sin subida mínima obligatoria",
    "FD-LAC-02": "4,4–7,0 mmol/L a los 60 min: envolvente clínica, no un objetivo",
    "FD-LAC-03": "3,4–5,5 mmol/L a los 60 min: envolvente clínica, no un objetivo",
    "FD-LAC-04": "15–30 min: L(T*+30) < L(T*) con aclaramiento en curso; ningún porcentaje fijo aprobado",
    "FD-LAC-05": "a los 120 min con entrega adecuada sostenida: 1,5–4,0 (57m) y 1,2–3,5 (72f) mmol/L, y L120 < L(T*)",
    "FD-LAC-06": "SÓLO SI LA ENTREGA ES ADECUADA",
}
OBSERVABLES_ES = {
    "FD-LAC-01": "trayectoria del lactato antes de los 60 min, con sangrado activo y entrega de O2 inadecuada",
    "FD-LAC-02": "lactato (mmol/L) a los 60 min sin tratar",
    "FD-LAC-03": "lactato (mmol/L) a los 60 min sin tratar",
    "FD-LAC-04": "lactato en T* + 30 min frente a T*, tras la hemostasia y con entrega adecuada sostenida",
    "FD-LAC-05": "lactato (mmol/L) a los 120 min del manejo definitivo, con entrega adecuada sostenida",
    "FD-LAC-06": "trayectoria del lactato con sangrado activo, según la adecuación de la entrega",
}


def render_decisions() -> str:
    """§12 of docs/revision/P2I_DECISION_LACTATO_GI.md, from the registry (never by hand)."""
    lines = ["## 12. Registro de decisiones docentes (P2I-2 y P2I-2R)\n",
             f"Respondidas por la docencia el {fc.DECIDED} y aclaradas el {fc.CLARIFIED} (versión «{fc.VERSION}»), "
             "registradas en `clinical_core/faculty_constraints.py`. Son restricciones clínicas de comportamiento del "
             "lactato observable, con estado FACULTY_APPROVED. **No aprueban ningún valor de parámetro oculto:** "
             + ", ".join(f"`{name}`" for name in fc.HIDDEN_PARAMETERS)
             + " siguen CANDIDATE, y nada de esto entra en los registros de autoridad de migración. Las envolventes "
             "de FD-LAC-05 son envolventes clínicas de calibración para estos casos GI, no límites fisiológicos "
             "universales. El texto que rige es el original, en inglés: la decisión y, cuando la hay, su aclaración. "
             "La docencia no dio un fundamento aparte: la columna «Frase clave» cita la frase de su propio texto que "
             "lo expresa. Su aplicación a la región candidata está en `docs/revision/P2I2_RESTRICCIONES_LACTATO_GI.md`.\n",
             "| ID | Estado | Fecha · versión | Observable | Escenarios · casos | Decisión (texto original) | "
             "Aclaración docente (texto original) | Frase clave del texto docente | Valores de parámetros que aprueba |",
             "|---|---|---|---|---|---|---|---|---|"]
    for item in fc.FACULTY_CLINICAL_CONSTRAINTS:
        dates = item.decided + (f", aclarada {item.clarified}" if item.clarified else "")
        clarification = f"«{item.clarification}»" if item.clarification else "sin cambios"
        lines.append(f"| {item.id} | {item.status} | {dates} · {item.version} | {OBSERVABLES_ES[item.id]} | "
                     f"{', '.join(item.scenarios)} · {', '.join(case[-3:] for case in item.cases)} | "
                     f"«{item.decision}» | {clarification} | «{item.rationale}» | ninguno |")
    lines.append("")
    lines.append("**Definiciones operativas confirmadas por la docencia (2026-10-26, texto original):** "
                 + "; ".join(f"«{text}»" for text in fc.FACULTY_CONFIRMED_DEFINITIONS) + ".\n")
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
    if RESULTS_PENDING_REFILTER is not None:
        parser.error("the P2I-2R results are pending a refilter that is not authorized yet "
                     f"(since {RESULTS_PENDING_REFILTER['since']}): {RESULTS_PENDING_REFILTER['reason']}")
    text = json.dumps(report(args.quick), indent=1, sort_keys=True, default=str)
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "lactate_constraints.json").write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
