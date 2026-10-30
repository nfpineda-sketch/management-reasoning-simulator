"""Phase 2 shadow core, P2I-2AK: the faculty HR observable-envelope filter.

    python -m clinical_core.hr_envelope_filter --digest
    python -m clinical_core.hr_envelope_filter --design
    python -m clinical_core.hr_envelope_filter --run --out <directory outside the repository>

Shadow only and offline. Faculty decisions (2026-10-30), recorded in FACULTY and frozen before any survivor count:

1. Demand: 0.9 (CURRENTLY_INCOMPATIBLE) stays out of the primary filter; 1.0 and 1.1 are filtered separately with the
   same rules, never pooled before filtering. Afterwards each latent HR combination is ROBUST_ACROSS_DEMAND,
   DEMAND_1_0_ONLY, DEMAND_1_1_ONLY or DEMAND_INCOMPATIBLE: diagnostic, never a filter; no demand approved.
2. Envelopes A-F (ENVELOPES): A untreated 57m 124 <= HR_120 <= 160; B untreated 72f 112 <= HR_120 <= 150 (faculty
   calibration envelopes for these cases, not 220 - age); C and D the PRBC units against their matched counterfactual
   (only the target unit omitted), direction only; E no sustained rise after adequacy (HR_120 <= HR_90 <= HR_60, adequacy
   sustained from minute 60); F 0 <= HR_120 - intrinsic <= 15 after definitive management.
3. Primary ceilings 150 / 175 (exploratory, not approved); 200 is OUT_OF_PRIMARY_RANGE_SENSITIVITY_REFERENCE, reported
   apart, never rescuing a candidate.
4. Unchanged: the retained arrival pair (P2I-2AJ), the arrival tolerance +-5, intrinsic 60 / 80 / 100 per case, common
   gains, pressure DEFERRED (P2I-2AG's primary mode). Nothing is fitted, selected or approved; legacy never read.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import replace
from pathlib import Path

from . import blood_anchors, calibration, gi_reference
from . import blood_constraints as bc
from . import blood_fluid_calibration as bf
from . import hr_observables as ho
from . import hr_primary as hp
from . import hr_structure as hs
from . import lactate_adequacy as la
from . import lactate_closure as lc
from . import lactate_rebuild as lr
from .derived import derive, effective_delivery, effective_oxygen_deficit
from .state import RhythmCode

DECIDED = "2026-10-30"
REVISION = "P2I-2AK"
ROOT = lc.ROOT
CASES = lc.CASES
C57, C72 = CASES
L1, L2, L3 = lc.L1, lc.L2, lc.L3
CF1, CF2 = "L3_WITHOUT_UNIT_1", "L3_WITHOUT_UNIT_2"
RESERVE = lc.RESERVE
MINUTES = lr.MINUTES
LAMBDAS = ho.LAMBDAS
P2I2AJ_RECORD = ROOT / "docs" / "revision" / "P2I2AJ_hr_observables.json"
P2I2AJ_DIGEST = "2437e1b1c3075e180ef0fec912867974af43242a828c356190193820933fec4d"
#: Every clinical_core source at P2I-2AJ's certified HEAD (9d97610) but the two exclusion-tuple files and this module.
DEPENDENCIES_AT_P2I2AJ = "dfb02ee2cb3065258d1b648be7278a385334f678a892feebd83e05c0d4e3c6da"
TUPLE_ONLY = ("clinical_core/decision_pack.py", "clinical_core/lactate_slice.py")
OWN = ("clinical_core/hr_envelope_filter.py",)
#: The retained pair's lactate units per filtered demand: P2I-2AI's record (1.0) and P2I-2AJ's recertification (1.1).
UNITS = {1.0: ho.P2I2AI_RETAINED_UNITS, 1.1: "515a157e21181013c631d4ff879dcb18986b9be89d40ad44654105781f1e2db0"}
DEMANDS = (1.0, 1.1)
EXCLUDED_DEMAND = 0.9

FACULTY = {
    "decided": DECIDED,
    "demand": "demand 0.9 (CURRENTLY_INCOMPATIBLE) is not in the primary HR filter; 1.0 and 1.1 are filtered "
              "separately with the same rules and never pooled before filtering; ROBUST_ACROSS_DEMAND, DEMAND_1_0_ONLY, "
              "DEMAND_1_1_ONLY and DEMAND_INCOMPATIBLE are diagnostic, never an acceptance criterion; no demand approved",
    "untreated": "A: untreated 57m at minute 120, authored arrival HR (124) <= HR <= 160; B: untreated 72f at minute 120, "
                 "112 <= HR <= 150; case-specific calibration envelopes in the current non-collapse model, not a "
                 "universal or 220 - age limit",
    "prbc": "C and D: each PRBC unit against its matched counterfactual at the same time (same case, latent HR, "
            "starting blood state, bleed, demand, other treatments, haemostasis and elapsed time; only the target unit "
            "omitted); HR with the unit <= HR without it; direction only, no minimum fall, no comparison between the "
            "units; the benefit HR_without - HR_with is reported, zero allowed",
    "definitive": "E: after sustained adequacy no sustained rise through 120: HR_120 <= HR_90 <= HR_60 with adequacy "
                  "sustained from minute 60; F: 0 <= HR_120 - intrinsic <= 15 after successful definitive management",
    "ceiling": "primary total sinus ceilings 150 and 175 (exploratory, not approved); 200 only as "
               "OUT_OF_PRIMARY_RANGE_SENSITIVITY_REFERENCE, never rescuing a primary rejection",
    "scope": "shadow only; no final latent HR selection, no pressure / vascular-tone or RR calibration, no collapse, no "
             "migration, no runtime integration; pressure stays DEFERRED",
}

# 1. The frozen rules ---------------------------------------------------------------------------------------------------

PRIMARY_CEILINGS = (150.0, 175.0)
SENSITIVITY_CEILINGS = (200.0,)
SENSITIVITY = "OUT_OF_PRIMARY_RANGE_SENSITIVITY_REFERENCE"
ENVELOPES = {
    "A": {"case": C57, "scenario": L1, "minute": 120, "low": float(gi_reference.authored(C57, "hr")), "high": 160.0,
          "rule": "untreated 57m (L1) HR at minute 120 within [authored arrival HR 124, 160]"},
    "B": {"case": C72, "scenario": L1, "minute": 120, "low": float(gi_reference.authored(C72, "hr")), "high": 150.0,
          "rule": "untreated 72f (L1) HR at minute 120 within [authored arrival HR 112, 150]"},
    "F": {"case": None, "scenario": L3, "minute": 120, "low": 0.0, "high": 15.0,
          "rule": "after definitive management (L3) HR at 120 minus intrinsic within [0, 15], each case"},
    "E": {"case": None, "scenario": L3, "minutes": (60, 90, 120), "onset_by": 60,
          "rule": "after definitive management (L3), adequacy sustained from minute 60 at the latest through 120 and "
                  "HR_120 <= HR_90 <= HR_60 (no tolerance), each case"},
    "C": {"case": None, "scenario": L3, "counterfactual": CF1, "unit": 1,
          "rule": "at the minute L3 completes unit 1, HR(L3) <= HR(L3 without unit 1), each case"},
    "D": {"case": None, "scenario": L3, "counterfactual": CF2, "unit": 2,
          "rule": "at the minute L3 completes unit 2, HR(L3) <= HR(L3 without unit 2), each case"},
}
ORDER = ("ARRIVAL", "PRIMARY_CEILING", "A", "B", "F", "E", "C", "D")
RULES = ORDER[2:]
ORDER_RULE = (
    "Frozen before any count, cheapest first: the arrival +-5 compatibility (analytic, P2I-2AJ's surface), the primary "
    "ceiling support (analytic), then A, B (L1), F, E (L3), C, D (L3 against its counterfactuals). Every rule is "
    "evaluated for every candidate; the first failure is read in this order and the overlaps are reported.")
COMPARATOR_RULE = (
    "A counterfactual is L3's own inputs with only the target PRBC unit removed. L3 infuses its units continuously "
    "(2 units over 60 min from minute 0: one unit per 30 min). Without unit 1: the infusion starts one unit-interval "
    "later with one unit less (unit 2 keeps its slot); without unit 2: the infusion stops after one unit-interval. The "
    "haemorrhage, PPI, endoscopic haemostasis, unit volume and Hb, blood state, demand, latent HR and elapsed time are "
    "L3's. The assessment minute is the first minute L3 has delivered that many units. Proved by tests: the "
    "counterfactual inputs equal L3's but for that one item; without unit 2 the run equals L3 minute for minute until "
    "unit 2 starts; the delivered units follow the omission; haemostasis lands at the same minute.")
CANDIDATE_RULE = (
    "A candidate is (latent HR combination, lactate survivor of the retained pair) at one demand; the latent HR "
    "combination is (57m intrinsic, 72f intrinsic, acute gain, debt gain, ceiling). The rules read L1, L3 and its "
    "counterfactuals, which do not depend on the crystalloid point: a lactate survivor's verdict is its (P3 set, 57m "
    "point, 72f point) verdict. A latent HR combination SURVIVES at a demand when at least one of its lactate survivors "
    "satisfies every rule (the lactate side is uncertainty, as demand); how many do is reported, and ROW_ROBUST marks "
    "the combinations whose every lactate survivor survives (diagnostic).")
SURVIVES, REJECTED = "SURVIVES", "REJECTED"
ROBUST, ONLY_1_0, ONLY_1_1, INCOMPATIBLE = ("ROBUST_ACROSS_DEMAND", "DEMAND_1_0_ONLY", "DEMAND_1_1_ONLY",
                                            "DEMAND_INCOMPATIBLE")
CASE_TRUTH_REJECTION, ARRIVAL_HR_REJECTION = "CASE_TRUTH_REJECTION", "ARRIVAL_HR_REJECTION"
HR_ENVELOPE_REJECTION, SIMULATION_REJECTION = "HR_ENVELOPE_REJECTION", "SIMULATION_REJECTION"
OUT_OF_PRIMARY = "OUT_OF_PRIMARY_CEILING_SUPPORT"


def counterfactual_items(case: str, full: dict, omit: int) -> tuple:
    """L3's inputs with only PRBC unit `omit` removed (COMPARATOR_RULE)."""
    out = []
    for item in lr.scenario_items(case, L3, full):
        if type(item).__name__ == "PackedRedCells":
            interval = item.duration_min / item.units
            if omit == 1:
                item = replace(item, start_minute=item.start_minute + interval, units=item.units - 1.0,
                               duration_min=item.duration_min - interval)
            elif omit == round(item.units):
                item = replace(item, units=item.units - 1.0, duration_min=item.duration_min - interval)
            else:
                raise ValueError("only the first or the last unit can be omitted from a continuous infusion")
        out.append(item)
    return tuple(out)


def full_run(inputs: dict, case: str, scenario: str, factor: float, intrinsic: str = "midpoint",
             profile_changes: dict | None = None) -> dict:
    """hr_observables.full_run, plus the two counterfactuals of L3 (CF1, CF2); validated in run()."""
    tau_d, gain_k, k, tau_l, excess, debt, delivery = inputs["point"]
    bag = inputs["bag"] if scenario == L2 else None
    values = {**lr.blood_values(inputs["entry"], case, bag), "reserve": RESERVE}
    _, profile, full = blood_anchors.setup(case, **values)
    case_values = calibration.case_values(case, calibration.GICandidate({}, excess=excess, debt=debt,
                                                                        delivery=delivery, intrinsic=intrinsic))
    case_values["preload_fraction"] = full[bc.POS]
    case_values["arrival_delivery_ratio"] /= RESERVE
    case_values["metabolic_demand_baseline"] *= factor
    anchors = gi_reference.candidate_anchors(case, case_values)
    profile = replace(profile, debt_clearance_tau_min=tau_d, debt_per_delivery_deficit=gain_k, debt_to_lactate_gain=k,
                      lactate_clearance_tau_min=tau_l, **(profile_changes or {}))
    items = {CF1: lambda: counterfactual_items(case, full, 1), CF2: lambda: counterfactual_items(case, full, 2)}.get(
        scenario, lambda: lr.scenario_items(case, scenario, full))()
    states, stop = blood_anchors.trajectory(anchors, items, MINUTES, profile)
    unit = full["red_cell_unit_volume_ml"]
    shed = [state.blood.shed_ml for state in states]
    flow = [after - before for before, after in zip(shed, shed[1:])]
    bleed = (flow[:1] or [0.0]) + flow
    rows = []
    for minute, state in enumerate(states):
        view = derive(state, anchors, profile)
        delivery_ = effective_delivery(view.delivery_rel, anchors)
        rows.append({"minute": minute, "pulse": state.R.pulse_present, "code": state.R.code.value,
                     "rate_bpm": state.R.rate_bpm, "pressure_rel": view.pressure_rel, "spo2": view.spo2,
                     "glucose": state.glucose, "D": state.D, "drive": state.aux.sympathetic_drive,
                     "hr": view.pulse_rate_bpm, "rr": view.respiratory_rate, "lactate": view.lactate,
                     "output": view.output_rel, "delivery": delivery_, "demand": state.aux.oxygen_demand,
                     "deficit": effective_oxygen_deficit(state.aux.oxygen_demand, delivery_, RESERVE),
                     "bleed_ml_per_min": bleed[minute], "prbc_units": state.blood.transfused_ml / unit,
                     "crystalloid_in_ml": state.blood.crystalloid_in_ml})
    controlled = lr.controlled_at(states[-1])
    context = lc.Context([row["delivery"] for row in rows], [row["demand"] for row in rows], bleed, controlled, stop,
                         RESERVE)
    return {"rows": rows, "stop": stop, "controlled_at": controlled, "adequacy": context.adequacy,
            "anchors": anchors, "profile": profile, "items": items}


def _units_minute(rows: list, units: float):
    return next((row["minute"] for row in rows if row["prbc_units"] >= units - 1e-9), None)


def readings(runs: dict, rate: float, candidate: dict) -> dict:
    """One (case, lactate survivor, latent HR combination): every value a rule or the report reads."""
    ceiling = candidate["ceiling"]
    series = {key: [p["hr"] for p in hp.primary_series(run_, rate, candidate["acute"], candidate["debt"], ceiling)]
              for key, run_ in runs.items()}
    complete = all(None not in values and len(values) == MINUTES + 1 for values in series.values())
    if not complete:
        return {"complete": False}
    l1, l3 = series[L1], series[L3]
    unit_1, unit_2 = _units_minute(runs[L3]["rows"], 1.0), _units_minute(runs[L3]["rows"], 2.0)
    adequacy = runs[L3]["adequacy"]
    onset = adequacy["onset"] if adequacy["status"] == lc.L3_ADEQUATE else None
    sinus = [h for key, values in series.items() for h, row in zip(values, runs[key]["rows"])
             if row["code"] == RhythmCode.SINUS.value]
    peak = max(max(l1), max(l3))  # the patient's own scenarios; the counterfactuals are comparators only
    return {"complete": True, "arrival": l3[0], "l1_120": l1[120], "unit_1_minute": unit_1, "unit_2_minute": unit_2,
            "with_unit_1": l3[unit_1], "without_unit_1": series[CF1][unit_1],
            "benefit_1": series[CF1][unit_1] - l3[unit_1],
            "with_unit_2": l3[unit_2], "without_unit_2": series[CF2][unit_2],
            "benefit_2": series[CF2][unit_2] - l3[unit_2],
            "l3_60": l3[60], "l3_90": l3[90], "l3_120": l3[120], "onset": onset, "residual": l3[120] - rate,
            "max_hr": peak, "reserve_utilization": (peak - rate) / (ceiling - rate), "intrinsic": rate,
            "structural": all(rate <= h <= ceiling for h in sinus)}


def failures(r57: dict, r72: dict) -> list[str]:
    """Every A-F rule a candidate fails, in ORDER (C-F per case)."""
    if not (r57["complete"] and r72["complete"]):
        return [SIMULATION_REJECTION]
    out = []
    a, b = ENVELOPES["A"], ENVELOPES["B"]
    if not a["low"] <= r57["l1_120"] <= a["high"]:
        out.append("A")
    if not b["low"] <= r72["l1_120"] <= b["high"]:
        out.append("B")
    for name, test in (("F", lambda r: ENVELOPES["F"]["low"] <= r["residual"] <= ENVELOPES["F"]["high"]),
                       ("E", lambda r: r["onset"] is not None and r["onset"] <= ENVELOPES["E"]["onset_by"]
                        and r["l3_120"] <= r["l3_90"] <= r["l3_60"]),
                       ("C", lambda r: r["with_unit_1"] <= r["without_unit_1"]),
                       ("D", lambda r: r["with_unit_2"] <= r["without_unit_2"])):
        for case, r in ((C57, r57), (C72, r72)):
            if not test(r):
                out.append(f"{name} {case}")
    return out


# 2. The pools: the retained pair's lactate survivors and P2I-2AJ's arrival survivors, per demand -------------------------

REUSE_RULE = (
    "Reused, never re-derived: the retained pair and its lactate survivors per demand (P2I-2AJ's retained_region, "
    "reproduced exactly: units digest 06f6d5c8... at 1.0 and 515a157e... at 1.1, else stop), the arrival surface "
    "(P2I-2AJ's analytic arrival table; its joint survivors equal its record's, else stop) and the executable "
    "dependencies (every clinical_core source equal to P2I-2AJ's certified HEAD but the exclusion tuples and this "
    "module, else stop). The physiology is the full core per (case, P3 set, lactate-side point, demand): L1, L3 and the "
    "two counterfactuals once each, HR post-processed for every latent HR combination; L2 only for the survivors (the "
    "72f crystalloid diagnostic and the maximum HR). No blood, fluid or lactate re-calibration.")


def dependency_digest() -> str:
    sources = {k: v for k, v in bf.freeze_sources().items() if k not in TUPLE_ONLY + OWN}
    return hashlib.sha256(json.dumps(sources, sort_keys=True).encode("utf-8")).hexdigest()


def p2i2aj_record() -> dict:
    record = json.loads(P2I2AJ_RECORD.read_text(encoding="utf-8"))
    if record["freeze_digest"] != P2I2AJ_DIGEST or record["verdict"]["verdict"] != ho.READY:
        raise AssertionError("the P2I-2AJ record is not the committed one")
    return record


def latent(s: dict) -> tuple:
    return (s["intrinsic"][0], s["intrinsic"][1], s["acute"], s["debt"], s["ceiling"])


def arrival_pool(record: dict, factor: float) -> dict:
    surface = ho.surface(ho.arrival_table(factor))
    mine = [{k: s[k] for k in ("intrinsic", "acute", "debt", "ceiling", "predicted")} for s in surface["survivors"]]
    theirs = [{k: s[k] for k in ("intrinsic", "acute", "debt", "ceiling", "predicted")}
              for s in record["hr_surfaces"][f"{factor:g}"]["survivors"]]
    if mine != theirs:
        raise AssertionError(f"the demand-{factor:g} arrival surface is not P2I-2AJ's")
    primary = [s for s in mine if s["ceiling"] in PRIMARY_CEILINGS]
    sensitivity = [s for s in mine if s["ceiling"] in SENSITIVITY_CEILINGS]
    universe = len(hp.INTRINSIC) ** 2 * len(hp.ACUTE) * len(hp.DEBT) * len(PRIMARY_CEILINGS)
    return {"primary": primary, "sensitivity": sensitivity, "universe": universe,
            "arrival_rejected": universe - len(primary), "out_of_primary": len(sensitivity)}


# 3. The filter -------------------------------------------------------------------------------------------------------

def _physiology_task(task: tuple) -> tuple:
    """One (case, P3 set, lactate-side point) at one demand: L1, L3 and the two counterfactuals, every latent HR
    combination post-processed."""
    key, entry, point, case, factor, candidates, position = task
    inputs = {"entry": entry, "point": point, "bag": None}
    runs = {scenario: full_run(inputs, case, scenario, factor) for scenario in (L1, L3, CF1, CF2)}
    out = []
    for candidate in candidates:
        rate = hs.intrinsic_levels(case)[candidate["intrinsic"][position]]
        out.append(readings(runs, rate, candidate))
    return key, out


def _survivor_task(task: tuple) -> tuple:
    """L2 (and L3 beside it) for a surviving (case, P3 set, crystalloid point, point): L2's maximum HR and the 72f
    fluid / PRBC contrast."""
    key, entry, bag, point, case, factor, candidates, position = task
    inputs = {"entry": entry, "point": point, "bag": bag}
    runs = {scenario: full_run(inputs, case, scenario, factor) for scenario in (L2, L3)}
    out = []
    for n, candidate in candidates:
        rate = hs.intrinsic_levels(case)[candidate["intrinsic"][position]]
        series = {sc: [p["hr"] for p in hp.primary_series(runs[sc], rate, candidate["acute"], candidate["debt"],
                                                          candidate["ceiling"])] for sc in (L2, L3)}
        if None in series[L2]:
            raise AssertionError("a surviving crystalloid trajectory lost its pulse")
        item = {"candidate": n, "l2_max": max(series[L2])}
        if case == C72:
            item["fluid_vs_prbc"] = ho.fluid_vs_prbc(runs, series)
        out.append(item)
    return key, out


def physiology_units(units: list) -> list[tuple]:
    """(P3 set, 57m point, 72f point, crystalloid points) of the retained pair's lactate survivors."""
    return sorted({(q, a, b, tuple(ds)) for _, a, b, r, ds in units for q in r})


def filter_demand(source: dict, support: list, units: list, candidates: list, factor: float, map_=map) -> dict:
    """Every rule on every (latent HR combination, lactate survivor) at one demand; the first failure in ORDER."""
    phys = physiology_units(units)
    tasks = []
    for q, a, b, _ in phys:
        for case, index, position in ((C57, a, 0), (C72, b, 1)):
            tasks.append(((case, q, index), source["p3"][q], LAMBDAS[index], case, factor, candidates, position))
    values = dict(map_(_physiology_task, tasks))
    rows = []
    for q, a, b, ds in phys:
        for n, candidate in enumerate(candidates):
            r57, r72 = values[(C57, q, a)][n], values[(C72, q, b)][n]
            rows.append({"candidate": n, "q": q, "a": a, "b": b, "weight": len(ds), "ds": ds,
                         "failures": failures(r57, r72), "r57": r57, "r72": r72})
    return {"factor": factor, "rows": rows, "physiology_units": len(phys), "full_runs": 4 * len(tasks)}


def subset(filtered: dict, first: int, count: int) -> dict:
    """The rows of candidates first .. first + count - 1, re-indexed from 0."""
    rows = [{**r, "candidate": r["candidate"] - first} for r in filtered["rows"]
            if first <= r["candidate"] < first + count]
    return {**filtered, "rows": rows}


def _rank(name: str) -> int:
    return -1 if name == SIMULATION_REJECTION else RULES.index(name)


def summarize(filtered: dict, candidates: list) -> dict:
    rows = filtered["rows"]
    entering = sum(r["weight"] for r in rows)
    first, any_, patterns = {}, {}, {}
    for r in rows:
        if not r["failures"]:
            continue
        label = r["failures"][0]
        first[label] = first.get(label, 0) + r["weight"]
        for name in r["failures"]:
            any_[name] = any_.get(name, 0) + r["weight"]
        pattern = "+".join(sorted({name.split(" ")[0] for name in r["failures"]}, key=_rank))
        patterns[pattern] = patterns.get(pattern, 0) + r["weight"]
    per_candidate = []
    for n, candidate in enumerate(candidates):
        mine = [r for r in rows if r["candidate"] == n]
        alive = sum(r["weight"] for r in mine if not r["failures"])
        total = sum(r["weight"] for r in mine)
        own_first = {}
        for r in mine:
            if r["failures"]:
                own_first[r["failures"][0]] = own_first.get(r["failures"][0], 0) + r["weight"]
        per_candidate.append({"latent": list(latent(candidate)), "predicted": candidate["predicted"],
                              "lactate_survivors": total, "surviving": alive,
                              "status": SURVIVES if alive else REJECTED, "row_robust": alive == total and total > 0,
                              "first_failures": own_first})
    by_rule = {name: sum(w for label, w in first.items() if label.split(" ")[0] == name)
               for name in RULES + (SIMULATION_REJECTION,)}
    return {"entering": entering, "surviving": sum(r["weight"] for r in rows if not r["failures"]),
            "first_failure": dict(sorted(first.items(), key=lambda kv: (_rank(kv[0].split(" ")[0]), kv[0]))),
            "first_failure_by_rule": by_rule, "any_failure": dict(sorted(any_.items())),
            "failure_patterns": dict(sorted(patterns.items())), "candidates": per_candidate,
            "surviving_candidates": sum(1 for c in per_candidate if c["status"] == SURVIVES)}


def margins(filtered: dict) -> dict:
    """Diagnostic margins of the boundary rules over every candidate (no rule changes)."""
    rows = [r for r in filtered["rows"] if r["r57"]["complete"] and r["r72"]["complete"]]
    out = {"A_l1_120": [r["r57"]["l1_120"] for r in rows], "B_l1_120": [r["r72"]["l1_120"] for r in rows]}
    for case, key in ((C57, "r57"), (C72, "r72")):
        out[f"F_residual {case}"] = [r[key]["residual"] for r in rows]
        out[f"E_largest_rise {case}"] = [max(r[key]["l3_90"] - r[key]["l3_60"], r[key]["l3_120"] - r[key]["l3_90"])
                                         for r in rows]
        out[f"C_benefit {case}"] = [r[key]["benefit_1"] for r in rows]
        out[f"D_benefit {case}"] = [r[key]["benefit_2"] for r in rows]
    weights = [r["weight"] for r in rows]
    return {name: ho._spread([v for v, w in zip(values, weights) for _ in range(w)]) for name, values in out.items()}


# 4. Cross-demand classification, identifiability, observables ---------------------------------------------------------

def cross_demand(summaries: dict) -> dict:
    alive = {f: {tuple(c["latent"]) for c in s["candidates"] if c["status"] == SURVIVES} for f, s in summaries.items()}
    universe = [(a, b, acute, gain, ceiling) for a in hp.INTRINSIC for b in hp.INTRINSIC for acute in hp.ACUTE
                for gain in hp.DEBT for ceiling in PRIMARY_CEILINGS]
    out = {}
    for item in universe:
        first, second = item in alive.get(1.0, set()), item in alive.get(1.1, set())
        out[item] = ROBUST if first and second else ONLY_1_0 if first else ONLY_1_1 if second else INCOMPATIBLE
    counts = {status: sum(1 for v in out.values() if v == status) for status in (ROBUST, ONLY_1_0, ONLY_1_1,
                                                                                  INCOMPATIBLE)}
    return {"counts": counts, "universe": len(universe), "is_filter": False,
            "surviving": {status: [list(k) for k, v in out.items() if v == status] for status in (ROBUST, ONLY_1_0,
                                                                                                 ONLY_1_1)}}


IDENTIFIABILITY_RULE = (
    "P2I-2AJ's rule on the surviving latent HR combinations, with the primary ceiling grid 150 / 175: "
    "NON_IDENTIFIABLE for the debt gain (only gain x D reaches HR, the D scale unapproved); POORLY_IDENTIFIED when two "
    "or more grid values survive or the one survivor is an edge of the explored support; PARTIALLY_CONSTRAINED for one "
    "interior value bracketed by rejected neighbours while the point observations (the two arrival HRs; envelopes A-F "
    "are inequalities, not observations) are fewer than the latents; WELL_CONSTRAINED only with as many point "
    "observations as latents. A narrow grid survivor set is never called identification.")


def identifiability(latents: list[tuple]) -> dict:
    grids = {"intrinsic_57m": list(hp.INTRINSIC), "intrinsic_72f": list(hp.INTRINSIC), "acute": list(hp.ACUTE),
             "debt": list(hp.DEBT), "ceiling": list(PRIMARY_CEILINGS)}
    out = {}
    for position, name in enumerate(ho.LATENTS):
        grid = grids[name]
        values = sorted({item[position] for item in latents}, key=grid.index)
        bracket = None
        if name in ho.STRUCTURAL:
            status = ho.NON
        elif not values:
            status = ho.NOT_EVALUABLE
        elif len(values) > 1 or values[0] in (grid[0], grid[-1]):
            status = ho.POOR
        else:
            index = grid.index(values[0])
            bracket = [grid[index - 1], grid[index + 1]]
            status = ho.PARTIAL if len(ho.OBSERVATIONS) < len(ho.LATENTS) else ho.WELL
        support = {f"{value}": sum(1 for item in latents if item[position] == value) for value in grid}
        out[name] = {"status": status, "surviving": values, "of": grid, "bracket_rejected_neighbours": bracket,
                     "support": support}
    out["rule"] = IDENTIFIABILITY_RULE
    return out


OBSERVABLE_READINGS = {"arrival": "arrival HR", "l1_120": "untreated HR at 120", "benefit_1": "unit-1 benefit",
                       "benefit_2": "unit-2 benefit", "l3_60": "H4 HR 60", "l3_90": "H4 HR 90", "l3_120": "H4 HR 120",
                       "residual": "residual above intrinsic at 120"}


def observables(filtered: dict, extras: dict) -> dict:
    """LOW / median / HIGH over the surviving candidates (lactate survivors x latent HR combinations), per case."""
    survivors = [r for r in filtered["rows"] if not r["failures"]]
    out = {}
    for case, key in ((C57, "r57"), (C72, "r72")):
        out[case] = {name: ho._spread([r[key][name] for r in survivors for _ in range(r["weight"])])
                     for name in OBSERVABLE_READINGS}
        out[case]["max_hr"] = ho._spread([x["max_hr"] for x in extras[case]])
        out[case]["reserve_utilization"] = ho._spread([x["reserve_utilization"] for x in extras[case]])
    return out


# 5. Verdict, design, freeze, run --------------------------------------------------------------------------------------

READY = "HR_OBSERVABLE_FILTER_SATISFIED"
NOT_READY = "HR_OBSERVABLE_FILTER_NOT_READY"
EMPTY = "HR_OBSERVABLE_FILTER_EMPTY"
VERDICT_RULE = (
    f"{READY} when: (1) at least one candidate survives at demand 1.0 or 1.1 (else {EMPTY}, for faculty review, nothing "
    "loosened or restored); (2) every final survivor satisfies A-F (re-checked); (3) the sympathetic gains and ceiling "
    "are common (one triple per combination, both cases); (4) the pressure contribution is 0 in the primary profile and "
    "every validation rerun; (5) the upstream physiology is unchanged (dependencies, lactate units and arrival surface "
    "reproduced; the runs equal lactate_closure.full_run and, at demand 1.0, hr_shock.full_run); (6) no structural HR "
    "contradiction (exact reconstruction; every sinus HR within [intrinsic, ceiling]). Cross-demand robustness is not "
    f"required. Otherwise {NOT_READY} with the first blocker. Nothing is approved.")
POLICY = ("Shadow only. P2I-2AJ's committed record and machinery; legacy never read (LegacyLock), P2F region never "
          "(P2FGuard). Rules frozen before any count; arrival and ceiling analytic; physiology once per (case, P3 set, "
          "point, demand), HR post-processed; no Cartesian sweep, no re-calibration, nothing selected or approved.")


def validate(source: dict, support: list, units: list, candidates: list, factor: float) -> dict:
    """The full core against the reconstruction on the first, middle and last physiology unit."""
    phys = physiology_units(units)
    sample = sorted({phys[0], phys[len(phys) // 2], phys[-1]})
    checks, runs = [], 0
    for q, a, b, ds in sample:
        entry, bag = source["p3"][q], support[ds[0]]["bag"]
        for case, index, position in ((C57, a, 0), (C72, b, 1)):
            inputs = {"entry": entry, "bag": bag, "point": LAMBDAS[index]}
            base = {sc: full_run(inputs, case, sc, factor) for sc in (L1, L2, L3, CF1, CF2)}
            runs += 5
            for scenario in (L1, L2, L3):
                theirs = lc.full_run(entry, case, scenario, LAMBDAS[index], bag if scenario == L2 else None,
                                     factor=factor)
                runs += 1
                checks.append(("lactate_closure", [r["lactate"] for r in base[scenario]["rows"]] == theirs["lactate"]
                               and [r["D"] for r in base[scenario]["rows"]] == theirs["D"]))
                reference = ho.full_run(inputs, case, scenario, factor)
                runs += 1
                checks.append(("hr_observables", base[scenario]["rows"] == reference["rows"]))
            l3, cf1, cf2 = base[L3]["rows"], base[CF1]["rows"], base[CF2]["rows"]
            start_2 = _units_minute(l3, 1.0)
            checks.append(("comparator_prefix", cf2[:start_2 + 1] == l3[:start_2 + 1]))
            checks.append(("comparator_units", _units_minute(cf1, 1.0) == _units_minute(l3, 2.0)
                           and cf1[start_2]["prbc_units"] == 0.0 and _units_minute(cf2, 2.0) is None
                           and cf2[-1]["prbc_units"] == l3[start_2]["prbc_units"]))
            checks.append(("comparator_haemostasis", base[L3]["controlled_at"] == base[CF1]["controlled_at"]
                           == base[CF2]["controlled_at"]))
            for candidate in candidates:
                level = candidate["intrinsic"][position]
                changes = {"acute_deficit_to_sympathetic_gain": candidate["acute"],
                           "debt_to_sympathetic_gain": candidate["debt"],
                           "sinus_rate_ceiling_bpm": candidate["ceiling"], **hp.PRIMARY_HR_CALIBRATION}
                fulls = {}
                for scenario in (L1, L3, CF1, CF2):
                    full = fulls[scenario] = full_run(inputs, case, scenario, factor, level, changes)
                    runs += 1
                    post = hp.primary_series(base[scenario], hs.intrinsic_levels(case)[level], candidate["acute"],
                                             candidate["debt"], candidate["ceiling"])
                    checks.append(("hr", [p["hr"] for p in post] == [r["hr"] for r in full["rows"]]))
                    checks.append(("lactate_unchanged_by_hr", [r["lactate"] for r in full["rows"]]
                                   == [r["lactate"] for r in base[scenario]["rows"]]
                                   and [r["D"] for r in full["rows"]] == [r["D"] for r in base[scenario]["rows"]]
                                   and [r["rr"] for r in full["rows"]] == [r["rr"] for r in base[scenario]["rows"]]))
                checks.append(("arrival", abs(fulls[L3]["rows"][0]["hr"] - candidate["predicted"][position]) <= 1e-9))
    names = sorted({name for name, _ in checks})
    return {"sample": [[q, a, b] for q, a, b, _ in sample], "full_runs": runs,
            "checks": {name: all(ok for n, ok in checks if n == name) for name in names},
            "exact": all(ok for _, ok in checks)}


def verdict(per_demand: dict, validations: dict, reuse_equal: bool) -> dict:
    survivors = {f: [r for r in d["filtered"]["rows"] if not r["failures"]] for f, d in per_demand.items()}
    recheck = all(not failures(r["r57"], r["r72"]) for rows in survivors.values() for r in rows)
    structural = all(r[key]["structural"] for d in per_demand.values() for r in d["filtered"]["rows"]
                     for key in ("r57", "r72") if r[key]["complete"])
    checks = [
        ("survivors", any(survivors.values()), EMPTY),
        ("envelopes_hold", recheck, "a final survivor fails an envelope"),
        # By construction: one candidate (acute, debt, ceiling) feeds both cases' readings (filter_demand).
        ("common_gains_by_construction", True, "a case-specific gain"),
        ("pressure_deferred", hp.PRIMARY_HR_CALIBRATION == {"sympathetic_per_pressure_deficit": 0.0},
         "the pressure contribution is active"),
        ("upstream_unchanged", reuse_equal and all(v["checks"].get("lactate_closure", False)
                                                   and v["checks"].get("lactate_unchanged_by_hr", False)
                                                   for v in validations.values()), "the upstream physiology changed"),
        ("structural", structural and all(v["exact"] for v in validations.values()),
         "a structural HR contradiction"),
    ]
    blockers = [why for _, passed, why in checks if not passed]
    return {"verdict": READY if not blockers else f"{NOT_READY} — {blockers[0]}",
            "checks": {name: passed for name, passed, _ in checks}, "blockers": blockers, "rule": VERDICT_RULE,
            "cross_demand_required": False, "approved": False}


def design() -> dict:
    return {"faculty": FACULTY, "demands": list(DEMANDS), "excluded_demand": EXCLUDED_DEMAND,
            "envelopes": ENVELOPES, "order": list(ORDER), "order_rule": ORDER_RULE, "comparator": COMPARATOR_RULE,
            "candidate": CANDIDATE_RULE, "primary_ceilings": list(PRIMARY_CEILINGS),
            "sensitivity_ceilings": list(SENSITIVITY_CEILINGS), "sensitivity": SENSITIVITY, "reuse": REUSE_RULE,
            "identifiability": IDENTIFIABILITY_RULE, "verdict": VERDICT_RULE, "policy": POLICY, "units": UNITS,
            "dependencies_at_p2i2aj": DEPENDENCIES_AT_P2I2AJ}


def freeze_digest() -> str:
    text = json.dumps({"revision": REVISION, "p2i2aj": hashlib.sha256(P2I2AJ_RECORD.read_bytes()).hexdigest(),
                       "design": design(), "sources": bf.freeze_sources()}, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sensitivity(filtered: dict, candidates: list) -> dict:
    return {"status": SENSITIVITY, "rescues": False, "summary": summarize(filtered, candidates)}


def run(progress=None, map_=map) -> dict:
    say = progress or (lambda *_: None)
    with lr.P2FGuard(), lr.LegacyLock():
        record = p2i2aj_record()
        out = {"freeze_digest": freeze_digest(), "decided": DECIDED, "revision": REVISION, "policy": POLICY,
               "faculty": FACULTY, "record": P2I2AJ_DIGEST}
        dependency = {"digest": dependency_digest(), "at_p2i2aj": DEPENDENCIES_AT_P2I2AJ}
        dependency["equal"] = dependency["digest"] == DEPENDENCIES_AT_P2I2AJ
        if not dependency["equal"]:
            raise AssertionError("an executable dependency changed since P2I-2AJ")
        say("haemodynamics")
        source_record = la.record_p2i2ab()
        source, support = la.source_space(source_record), source_record["crystalloid_support"]
        arrivals = lr.arrival_table()
        tasks = lc.haemodynamic_tasks(source, support)
        store = lc.haemodynamics(tasks, map_)
        per_demand, validations, units_digests = {}, {}, {}
        for factor in DEMANDS:
            say(f"pool x{factor:g}")
            region = ho.retained_region(source, support, arrivals, tasks, store, factor, map_)
            units_digests[f"{factor:g}"] = region["digest"]
            if region["digest"] != UNITS[factor]:
                raise AssertionError(f"the demand-{factor:g} lactate units are not P2I-2AJ's")
            pool = arrival_pool(record, factor)
            say(f"validation x{factor:g}")
            validations[f"{factor:g}"] = validate(source, support, region["units"], pool["primary"]
                                                  + pool["sensitivity"], factor)
            if not validations[f"{factor:g}"]["exact"]:
                raise AssertionError(f"the demand-{factor:g} reconstruction disagrees with the full core")
            say(f"filter x{factor:g}")
            both = filter_demand(source, support, region["units"], pool["primary"] + pool["sensitivity"], factor,
                                 map_)
            filtered = subset(both, 0, len(pool["primary"]))
            sensitivity = subset(both, len(pool["primary"]), len(pool["sensitivity"])) if pool["sensitivity"] else None
            summary = summarize(filtered, pool["primary"])
            per_demand[factor] = {"filtered": filtered, "summary": summary, "pool": pool, "region": region,
                                  "sensitivity": sensitivity}
        say("survivors")
        extras = {}
        for factor, item in per_demand.items():
            survivors = [r for r in item["filtered"]["rows"] if not r["failures"]]
            candidates = item["pool"]["primary"]
            wanted = {}
            for r in survivors:
                for d in r["ds"]:
                    for case, index, position in ((C57, r["a"], 0), (C72, r["b"], 1)):
                        wanted.setdefault((case, r["q"], index, d, position), set()).add(r["candidate"])
            tasks2 = [((case, q, index, d), source["p3"][q], support[d]["bag"], LAMBDAS[index], case, factor,
                       [(n, candidates[n]) for n in sorted(ns)], position)
                      for (case, q, index, d, position), ns in sorted(wanted.items())]
            values = {key: {x["candidate"]: x for x in items} for key, items in map_(_survivor_task, tasks2)}
            mine = {C57: [], C72: []}
            contrast = []
            for r in survivors:
                for d in r["ds"]:
                    for case, index, key in ((C57, r["a"], "r57"), (C72, r["b"], "r72")):
                        x = values[(case, r["q"], index, d)][r["candidate"]]
                        peak = max(r[key]["max_hr"], x["l2_max"])
                        rate, ceiling = r[key]["intrinsic"], candidates[r["candidate"]]["ceiling"]
                        mine[case].append({"max_hr": peak, "reserve_utilization": (peak - rate) / (ceiling - rate)})
                        if case == C72:
                            contrast.append(x["fluid_vs_prbc"])
            extras[factor] = {"cases": mine, "contrast": contrast, "l2_runs": len(tasks2) * 2}
        summaries = {f: item["summary"] for f, item in per_demand.items()}
        out["reuse"] = {"rule": REUSE_RULE, "dependency": dependency, "units_digests": units_digests,
                        "expected_units": {f"{f:g}": UNITS[f] for f in DEMANDS}, "equal": True,
                        "arrival_surface_equal": True}
        out["counts"] = {
            CASE_TRUTH_REJECTION: {"case_pairs": 1, "lactate_survivors": record["efficiency"][
                "case_truth_rejected_lactate_survivors"]},
            ARRIVAL_HR_REJECTION: {f"{f:g}": item["pool"]["arrival_rejected"] for f, item in per_demand.items()},
            OUT_OF_PRIMARY: {f"{f:g}": item["pool"]["out_of_primary"] for f, item in per_demand.items()},
            HR_ENVELOPE_REJECTION: {f"{f:g}": item["summary"]["entering"] - item["summary"]["surviving"]
                                    - item["summary"]["first_failure"].get(SIMULATION_REJECTION, 0)
                                    for f, item in per_demand.items()},
            SIMULATION_REJECTION: {f"{f:g}": item["summary"]["first_failure"].get(SIMULATION_REJECTION, 0)
                                   for f, item in per_demand.items()}}
        out["demands"] = {f"{f:g}": {"pool": {k: v for k, v in item["pool"].items() if k not in ("primary",
                                                                                                   "sensitivity")},
                                     "entering_latent_combinations": len(item["pool"]["primary"]),
                                     "lactate_survivors": item["region"]["survivors"],
                                     "physiology_units": item["filtered"]["physiology_units"],
                                     "summary": item["summary"], "margins": margins(item["filtered"]),
                                     "sensitivity_200": (_sensitivity(item["sensitivity"], item["pool"]["sensitivity"])
                                                         if item["sensitivity"] else None),
                                     "observables": observables(item["filtered"], extras[f]["cases"]),
                                     "fluid_vs_prbc_72f": {
                                         "pairs": len(extras[f]["contrast"]),
                                         "never_diverge": sum(1 for c in extras[f]["contrast"]
                                                              if c["diverges_at"] is None),
                                         **{name: ho._spread([c[name] for c in extras[f]["contrast"]])
                                            for name in ("diverges_at", "diverges_by_1_bpm_at", "largest_difference",
                                                         "prbc_minus_fluid_at_largest")},
                                         "first_input": {str(kind).lower(): sum(1 for c in extras[f]["contrast"]
                                                                                if c["first_input"] == kind)
                                                         for kind in ("acute", "debt", None)}}}
                         for f, item in per_demand.items()}
        out["cross_demand"] = cross_demand(summaries)
        alive = {f: [tuple(c["latent"]) for c in s["candidates"] if c["status"] == SURVIVES]
                 for f, s in summaries.items()}
        out["identifiability"] = {**{f"{f:g}": identifiability(v) for f, v in alive.items()},
                                  "union": identifiability([x for v in alive.values() for x in v])}
        out["validation"] = validations
        out["verdict"] = verdict(per_demand, validations, True)
    out["efficiency"] = {
        "haemodynamic_trajectories": len(store),
        "physiology_full_runs": {f"{f:g}": item["filtered"]["physiology_units"] * 2 * 4
                                 for f, item in per_demand.items()},
        "survivor_full_runs": {f"{f:g}": extras[f]["l2_runs"] for f in extras},
        "validation_full_runs": sum(v["full_runs"] for v in validations.values()),
        "hr_post_processed": {f"{f:g}": len(item["filtered"]["rows"]) * 2 for f, item in per_demand.items()},
        "analytic_arrival_decompositions": len(DEMANDS) * 450, "cartesian_sweep": False, "legacy_read": False}
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--digest", action="store_true")
    parser.add_argument("--design", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--out")
    args = parser.parse_args(argv)
    if args.digest:
        print(freeze_digest())
        return 0
    if args.design:
        print(json.dumps(design(), indent=1, default=str))
        return 0
    if args.run:
        if not args.out:
            parser.error("--run needs --out (a directory outside the repository)")
        out = Path(args.out)
        if out.resolve().is_relative_to(ROOT):
            parser.error("--out must be outside the repository")
        out.mkdir(parents=True, exist_ok=True)
        result = run(lambda step: print(step, flush=True))
        (out / "hr_envelope_filter.json").write_text(json.dumps(result, indent=1, sort_keys=True, default=str),
                                                     encoding="utf-8")
        print(out / "hr_envelope_filter.json")
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
