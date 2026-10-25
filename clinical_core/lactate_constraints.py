"""P2I-2: apply the faculty-approved GI lactate constraints (FD-LAC-01..06) to P2F's admissible region.

    python -m clinical_core.lactate_constraints [--quick] [--out <directory outside the repository>]

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
        peak = max(range(haemostasis, len(definitive)), key=lambda minute: (definitive[minute], -minute))
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


# The report --------------------------------------------------------------------------------------

def filter_digest() -> str:
    """Every shadow-core source (no exclusion), the calibration freeze, the scenario orders and the
    frozen definitions: a change to any of them makes the results stale."""
    orders = {name: [spec["minutes"], {str(minute): order for minute, order in spec["orders"].items()}]
              for name, spec in lactate_slice.ORDERS.items() if name in SCENARIOS}
    text = json.dumps({"freeze": calibration.frozen_digest(), "orders": orders,
                       "sources": lactate_slice.slice_sources(), "definitions": fc.definitions_digest(),
                       "pipeline": pipeline_digest()}, sort_keys=True)
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
    data = {**digests, "quick": quick, "admissible_candidates": len(members), "settings": settings,
            "decisions": decision_records(), "counts": {name: value for name, value in found.items()
                                                         if name != "all_six_keys"},
            "faculty_constrained_region": survivors, "per_case": per_case(verdicts),
            "sensitivity": sensitivity(members), "dissociation": dissociation(members, survivors, settings),
            "parameter_region": parameter_region(members, survivors),
            "fd05": fd05_verification(members, survivors, verdicts),
            "representatives": representatives(members, survivors, verdicts, settings)}
    # Last and apart: never an input to anything above.
    data["legacy_position"] = legacy_position(settings)
    return data


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    text = json.dumps(report(args.quick), indent=1, sort_keys=True, default=str)
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "lactate_constraints.json").write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
