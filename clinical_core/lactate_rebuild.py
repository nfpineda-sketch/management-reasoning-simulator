"""P2I-2AB: the GI lactate rebuild on current physiology (shadow only).

    python -m clinical_core.lactate_rebuild --digest
    python -m clinical_core.lactate_rebuild --design
    python -m clinical_core.lactate_rebuild --run --out <directory outside the repository>

Shadow, offline and read-only. The faculty decided (2026-10-28) that the open crystalloid tau edge does not block the
rebuild: readiness is READY_FOR_CURRENT_PHYSIOLOGY_LACTATE_REBUILD_WITH_PROPAGATED_FLUID_UNCERTAINTY and tau is
STRUCTURALLY_IDENTIFIABLE BUT PRACTICALLY_WEAKLY_IDENTIFIED_WITHIN_120_MIN_HORIZON: no tau is approved or preferred,
nothing above 240 is added, and the whole certified crystalloid support (P2I-2Y / P2I-2Z / P2I-2AA) propagates.

1. Source space (P2I-2AB-1), from current certified physiology only. Blood: P2I-2Y's robustness region (P2I-2V-R's
   surviving values with P2I-2W's refill extension) at the rates 2.5, 5 and 6 and at every case-band position, kept
   where the current blood constraints that do not read the crystalloid hold in both cases; the enumeration must
   reproduce the certified joint survivor counts. Crystalloid: the P2I-2AA support. Reserve, haemostasis (the
   engine's own endoscopy) and the fixed L3 modifiers as recorded. The historical P2F candidate region is never read:
   the run executes inside ``P2FGuard``.
2. Lactate side (P2I-2AB-2): the registry candidate points of tau_D, the deficit-to-D gain, the D-to-lactate gain and
   the lactate clearance tau, the case arrival-excess band and P2F's arrival (debt, delivery) pairs, unchanged. The
   demand baseline is not variable (the registry: never a free parameter for lactate).
3. Factorization (P2I-2AB-3): the haemodynamics do not read the lactate side, the arrival debt, the arrival delivery
   level, the reserve or the intrinsic rate, so each (case, scenario, blood input) is simulated once by the core and
   D and lactate are post-processed with the core's own arithmetic. A deterministic sample of full core runs must
   agree exactly; otherwise the run stops (no cartesian fallback).
4. FD-LAC with the current semantics (P2I-2AB-5..9): adequate oxygen availability is effective_oxygen_deficit == 0;
   a substantial sustained decline during active bleeding with deficit > 0 fails only when the deficit at its later
   reassessment point is not below the earlier one (PERSISTENT_OR_WORSENING_CRITICAL); RECOVERING_CRITICAL may fall.
   FD-LAC-02..05 are faculty_constraints' frozen functions, read with oxygen available = reserve x delivery so that
   their adequacy is exactly deficit == 0.
5. Sequential filter (P2I-2AB-10), in an order fixed by cost before any result: L1, then L3, then L2.
6. Identifiability, representatives, physiological flags, and the legacy lactate as a reference read only after the
   filter. Nothing is fitted, selected or approved: the survivors are a FACULTY-CONSTRAINED CURRENT-PHYSIOLOGY
   LACTATE REGION.

The definitions, rules, factorization method, filter order and reporting rules were frozen and committed before any
candidate was evaluated (``freeze_digest``).
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from dataclasses import replace
from pathlib import Path

from . import blood_anchors, calibration, gi_reference, lactate_slice
from . import blood_constraints as bc
from . import blood_extension as be
from . import blood_fluid_calibration as bf
from . import blood_fluid_readiness as fr
from . import blood_fluid_tau_closure as tc
from . import blood_rate_boundary as rb
from . import faculty_constraints as fd
from .derived import derive, effective_delivery, effective_oxygen_deficit, lactate_baseline
from .integration import CHANNEL_BOUNDS
from .state import Channel

DECIDED = "2026-10-28"
REVISION = "P2I-2AB"
ROOT = bc.ROOT
CASES = bc.CASES
L1, L2, L3 = lactate_slice.L1, lactate_slice.L2, lactate_slice.L3
SCENARIOS = (L1, L2, L3)
MINUTES = lactate_slice.MINUTES
TIMES = lactate_slice.TIMES
RESERVE = blood_anchors.RESERVE
PROFILE = blood_anchors.DEFAULT_PROFILE
P2I2AA_RECORD = tc.ROOT / "docs" / "revision" / "P2I2AA_blood_fluid_tau_closure.json"
P2I2AA_DIGEST = "5087cf022f928fed5d3893a00a4907578e7f91b3543ee10c6ba3786abde01001"

# 0. The faculty decisions and the readiness they give ----------------------------------------------------------------

READINESS = "READY_FOR_CURRENT_PHYSIOLOGY_LACTATE_REBUILD_WITH_PROPAGATED_FLUID_UNCERTAINTY"
TAU_STATUS = "STRUCTURALLY_IDENTIFIABLE BUT PRACTICALLY_WEAKLY_IDENTIFIED_WITHIN_120_MIN_HORIZON"
FACULTY = {
    "readiness": "The open crystalloid tau edge does not block the lactate rebuild: readiness becomes " + READINESS
                 + ". This approves no tau value.",
    "tau": "tau is " + TAU_STATUS + ". Every certified crystalloid point propagates as fluid uncertainty; no preferred "
           "tau is chosen and nothing above 240 min is added.",
    "adequacy": "Adequate oxygen availability for lactate production is effective_oxygen_deficit == 0 (ADEQUATE and "
                "COMPENSATED); CRITICAL is effective_oxygen_deficit > 0. Normal resting DO2 is not required.",
    "recovery": "FD-LAC-06 with active bleeding: PERSISTENT_OR_WORSENING_CRITICAL when the deficit > 0 is stable or "
                "worsening over the reassessment interval; RECOVERING_CRITICAL when the deficit > 0 decreases over "
                "it, and lactate may fall. The net trajectory at the reassessment points decides, not minute-to-minute "
                "monotonicity. No active treatment order is required; no percentage tolerance is added to the deficit.",
    "rates": "Bleed rates 2.5, 5 and 6 mL-eq/min; none is approved; 7 and above are excluded.",
    "preload": "Primary support 57m 0.5 and 72f 0.6; a lower position enters only where it survives the current "
               "blood constraints; the positions that enter are reported exactly.",
    "l3": "fraction_with_ppi 0.8 and fraction_after_hemostasis 0.1: FIXED_PROVISIONAL_FOR_PRIMARY_LACTATE_ANALYSIS "
          "and FACULTY_DECISION_PENDING. No range exists, so there is no sensitivity on them.",
}
LACTATE_RATES = tc.LACTATE_RATES


def record_p2i2aa() -> dict:
    record = json.loads(P2I2AA_RECORD.read_text(encoding="utf-8"))
    if record["freeze_digest"] != P2I2AA_DIGEST:
        raise AssertionError("the P2I-2AA record is not the committed one")
    return record


def readiness(record: dict) -> dict:
    """P2I-2AA was NOT_READY on the crystalloid criterion alone (tau open at 240); the faculty's decision lifts exactly
    that blocker and no other. Anything else blocking keeps the rebuild NOT_READY."""
    blockers = list(record["readiness"]["blockers"])
    lifted = blockers == [tc.CRYSTALLOID_CRITERION]
    others = all(item["passed"] for name, item in record["readiness"]["criteria"].items()
                 if name != tc.CRYSTALLOID_CRITERION)
    region = record["region"]
    active = all(fr.calibration_status(*(float(v) for v in key.split("|")[:2])) == fr.ACTIVE for key in region)
    return {"previous": record["readiness"]["verdict"], "previous_blockers": blockers,
            "tau": {"boundary": record["boundary"]["status"], "practical": record["practical"]["classification"],
                    "status": TAU_STATUS},
            "verdict": READINESS if lifted and others and region and active else tc.NOT_READY,
            "faculty": FACULTY["readiness"]}


def crystalloid_support(record: dict) -> list[dict]:
    """D: the certified P2I-2AA crystalloid support, unchanged (no point added, removed or preferred)."""
    out = []
    for key in record["region"]:
        f0, finf, tau = (float(v) for v in key.split("|"))
        if tau > tc.TAU_CAP:
            raise AssertionError("the crystalloid support exceeds tau 240")
        out.append({"key": key, "F0": f0, "Finf": finf, "tau": tau, "bag": bf.bag(f0, finf, tau)})
    return out


# 1. The blood source space -------------------------------------------------------------------------------------------

#: Blood dimensions besides the rate and the positions (the old crystalloid bag is replaced by the support D).
BLOOD_DIMS = tuple(name for name in bc.SHARED if name not in bc.BAG)
#: The current blood constraints that do not read the crystalloid (FD-BLD-04, 05 and 06 are the support's own).
NON_BAG = tuple(name for name in bc.CONSTRAINTS if name not in bf.CRYSTALLOID_CONSTRAINTS)
RATE_FREE = tuple(name for name in NON_BAG if bc.BLEED not in bc._depends(name))
RATE_BOUND = tuple(name for name in NON_BAG if name not in RATE_FREE)
P1_DIMS = (bc.B0, bc.LK, *bc.REFILL)
P3_DIMS = P1_DIMS + bc.UNIT
KEY_DIMS = bf.PROBE_KEYS


def blood_design() -> dict:
    region = bf.robustness_region()
    shared = {name: tuple(region["shared"][name]) for name in BLOOD_DIMS}
    bags = [dict(zip(bc.BAG, values)) for values in itertools.product(*(region["shared"][n] for n in bc.BAG))]
    return {"rates": list(LACTATE_RATES), "shared": shared,
            "positions": {case: tuple(region["positions"][case]) for case in CASES}, "old_bags": bags,
            "combinations_per_rate": math.prod(len(v) for v in shared.values()),
            "non_bag_constraints": list(NON_BAG), "rate_free": list(RATE_FREE), "rate_bound": list(RATE_BOUND)}


def certified_counts() -> dict:
    """The certified joint survivor counts per rate (crystalloid bag and reserve included) and the refill pairs each
    certified count covers: P2I-2V-R and P2I-2W's in-band boxes at 2.5, P2I-2Y's robustness at 5 and 6."""
    base = be.base_box(be.record())
    vr = be.record()["primary"]["marginal"]["bleed_ml_per_min|common"]["2.5"]
    parts = {"P2I-2V-R": {"pairs": [f"{t:g}|{u:g}" for t, u in itertools.product(base[bf.TARGET], base[bf.TAU])],
                          "count": vr}}
    for box, values, rates in tc.p2i2w_boxes():
        if bf.TARGET in box["fixed"] or bf.TAU in box["fixed"]:
            if set(box["fixed"]) - {bf.TARGET, bf.TAU}:
                continue
            parts[f"P2I-2W {box['name']}"] = {
                "pairs": [f"{t:g}|{u:g}" for t, u in itertools.product(values[bf.TARGET], values[bf.TAU])],
                "count": rates.get("2.5", 0)}
    out = {"2.5": {"total": sum(p["count"] for p in parts.values()), "parts": parts}}
    robustness = fr.record_p2i2y()["robustness"]["rates"]
    for rate in ("5.0", "6.0"):
        out[rate] = {"total": robustness[rate]["joint"],
                     "parts": {f"P2I-2Y {pair}": {"pairs": [pair], "count": n}
                               for pair, n in robustness[rate]["by_refill"].items()}}
    return out


def _row_tasks(case: str, names, values: dict) -> list:
    out = []
    for name in names:
        sources = [bc._source(name, None)]
        if sources[0] == "acute":
            sources = [f"acute_{int(bc.ACUTE_LOSS_ML)}", f"acute_off_{int(bc.ACUTE_LOSS_ML)}"]
        out.extend((case, source, tuple(values[n] for n in be._keys(source))) for source in sources)
    return out


def _compute_rows(rows, tasks: list, map_) -> None:
    """The frozen row functions (P2I-2W's _compute), each row once; neighbours share a crystalloid baseline."""
    pending = [task for task in dict.fromkeys(tasks) if task[2] not in rows.table[task[0]][task[1]]]
    pending.sort(key=lambda t: (t[0], t[1], repr(t[2][3:]), repr(t[2])) if t[1] == "crystalloid"
                 else (t[0], t[1], repr(t[2])))
    for (case, source, key), row in map_(be._compute, pending):
        rows.table[case][source][key] = row
        rows.computed += 1


def _state(verdicts) -> str:
    verdicts = list(verdicts)
    return "fail" if False in verdicts else "unreadable" if None in verdicts else "pass"


def _with(combo: dict, rate: float, position: float) -> dict:
    return {**combo, bc.BLEED: rate, bc.POS: position}


def _key_label(values: dict) -> str:
    return "|".join(f"{values[n]:g}" for n in KEY_DIMS)


def blood_source(rows, map_=map, progress=None) -> dict:
    """The blood source space: every shared value set (reserve included) at every rate and case-band position where
    the non-crystalloid constraints hold in both cases. Then FD-BLD-04 / 05 / 06 of the old crystalloid grid give the
    multiplicity m(key) that must reproduce the certified joint counts. Raises when it does not (stop)."""
    say = progress or (lambda *_: None)
    design = blood_design()
    shared, positions = design["shared"], design["positions"]
    combos = [dict(zip(BLOOD_DIMS, values)) for values in itertools.product(*(shared[n] for n in BLOOD_DIMS))]
    say("blood: rate-free rows")
    tasks = [task for case in CASES for combo in combos for position in positions[case]
             for task in _row_tasks(case, RATE_FREE, _with(combo, LACTATE_RATES[0], position))]
    tasks += [task for case in CASES for bag in design["old_bags"]
              for task in _row_tasks(case, ("FD-BLD-04", "FD-BLD-05"), bag)]
    _compute_rows(rows, tasks, map_)
    free = {case: {} for case in CASES}
    unreadable = {"rate_free": 0, "rate_bound": 0, "FD-BLD-06": 0}
    for case in CASES:
        for index, combo in enumerate(combos):
            kept = []
            for position in positions[case]:
                state = _state(rows.verdict(case, n, _with(combo, LACTATE_RATES[0], position)) for n in RATE_FREE)
                unreadable["rate_free"] += state == "unreadable"
                if state == "pass":
                    kept.append(position)
            if kept:
                free[case][index] = kept
    say("blood: rate-bound rows")
    tasks = [task for rate in LACTATE_RATES for case in CASES for index, kept in free[case].items()
             for position in kept for task in _row_tasks(case, RATE_BOUND, _with(combos[index], rate, position))]
    _compute_rows(rows, tasks, map_)
    alive = {}
    by_position = {f"{rate:g}": {case: {f"{p:g}": 0 for p in positions[case]} for case in CASES}
                   for rate in LACTATE_RATES}
    for rate in LACTATE_RATES:
        for index in sorted(set(free[CASES[0]]) & set(free[CASES[1]])):
            kept = {}
            for case in CASES:
                kept[case] = []
                for position in free[case][index]:
                    state = _state(rows.verdict(case, n, _with(combos[index], rate, position)) for n in RATE_BOUND)
                    unreadable["rate_bound"] += state == "unreadable"
                    if state == "pass":
                        kept[case].append(position)
            if all(kept.values()):
                alive[(rate, index)] = kept
                for case in CASES:
                    for position in kept[case]:
                        by_position[f"{rate:g}"][case][f"{position:g}"] += 1
    say("blood: crystalloid multiplicity")
    bags = [bag for bag in design["old_bags"]
            if all(rows.verdict(case, n, bag) is True for case in CASES for n in ("FD-BLD-04", "FD-BLD-05"))]
    keys = sorted({tuple({**combos[index], bc.BLEED: rate}[n] for n in KEY_DIMS) for rate, index in alive})
    tasks = [task for key in keys for bag in bags for case in CASES
             for task in _row_tasks(case, ("FD-BLD-06",), {**bag, **dict(zip(KEY_DIMS, key))})]
    _compute_rows(rows, tasks, map_)
    multiplicity = {}
    for key in keys:
        n = 0
        for bag in bags:
            verdicts = [rows.verdict(case, "FD-BLD-06", {**bag, **dict(zip(KEY_DIMS, key))}) for case in CASES]
            unreadable["FD-BLD-06"] += _state(verdicts) == "unreadable"
            n += all(v is True for v in verdicts)
        multiplicity[_key_label(dict(zip(KEY_DIMS, key)))] = n
    reproduced = {f"{rate:g}": {} for rate in LACTATE_RATES}
    for (rate, index), kept in alive.items():
        combo = combos[index]
        label = _key_label({**combo, bc.BLEED: rate})
        pair = f"{combo[bf.TARGET]:g}|{combo[bf.TAU]:g}"
        count = math.prod(len(v) for v in kept.values()) * multiplicity[label]
        reproduced[f"{rate:g}"][pair] = reproduced[f"{rate:g}"].get(pair, 0) + count
    certified = certified_counts()
    comparison, agree = {}, True
    for rate, item in certified.items():
        mine = reproduced[f"{float(rate):g}"]
        rows_ = {}
        for name, part in item["parts"].items():
            got = sum(mine.get(pair, 0) for pair in part["pairs"])
            rows_[name] = {"certified": part["count"], "reproduced": got}
            agree &= got == part["count"]
        covered = {pair for part in item["parts"].values() for pair in part["pairs"]}
        stray = {pair: n for pair, n in mine.items() if pair not in covered and n}
        agree &= not stray and sum(mine.values()) == item["total"]
        comparison[rate] = {"total": {"certified": item["total"], "reproduced": sum(mine.values())}, "parts": rows_,
                            "uncovered_pairs": stray}
    if not agree:
        raise AssertionError(f"the blood source space does not reproduce the certified joint counts: {comparison}")
    sets = _sets(combos, alive, multiplicity)
    return {"design": {k: v for k, v in design.items() if k != "old_bags"}, "old_bags": len(design["old_bags"]),
            "old_bags_passing_fd04_05": len(bags), "by_position": by_position, "unreadable": unreadable,
            "multiplicity": multiplicity, "reproduction": comparison, "reproduced": agree, **sets}


def _sets(combos: list, alive: dict, multiplicity: dict) -> dict:
    """P3 sets (blood values, rate, positions; reserve collapsed with its multiplicity) and their P1 projections."""
    grouped = {}
    for (rate, index), kept in alive.items():
        combo = combos[index]
        for pair in itertools.product(*(kept[case] for case in CASES)):
            key = (rate, *(combo[n] for n in P3_DIMS), *pair)
            grouped.setdefault(key, []).append(combo["reserve"])
    p3, p1, parents = [], [], {}
    for key in sorted(grouped):
        rate, values, pair = key[0], dict(zip(P3_DIMS, key[1:1 + len(P3_DIMS)])), key[1 + len(P3_DIMS):]
        label = _key_label({**values, bc.BLEED: rate})
        if multiplicity[label] <= 0:
            raise AssertionError(f"{label}: no certified crystalloid passes FD-BLD-06 at this key (stop)")
        parent = (rate, *(values[n] for n in P1_DIMS), *pair)
        if parent not in parents:
            parents[parent] = len(p1)
            p1.append({"rate": rate, **{n: values[n] for n in P1_DIMS}, "positions": dict(zip(CASES, pair)),
                       "key": label})
        p3.append({"rate": rate, **values, "positions": dict(zip(CASES, pair)), "reserves": sorted(grouped[key]),
                   "key": label, "p1": parents[parent]})
    children = [[] for _ in p1]
    for q, entry in enumerate(p3):
        children[entry["p1"]].append(q)
    return {"p1": p1, "p3": p3, "children": children}


def source_keys_certified(source: dict, record: dict) -> dict:
    """Every source key must be one where the crystalloid support is certified compatible: P2I-2Y's survivor keys at
    5 and 6 (the support is robust there by construction) and the rate-2.5 keys P2I-2AA checked (no exclusion)."""
    certified = {fr._blood_label(key) for key in fr.blood_keys(fr.record_p2i2y())["certified"]}
    rate25 = {fr._blood_label(key) for key in tc.rate25_keys()}
    keys = sorted({entry["key"] for entry in source["p3"]})
    outside = [k for k in keys if k not in (rate25 if float(k.split("|")[1]) == 2.5 else certified)]
    excluded = {k: v for k, v in record["rate25_compatibility"].items() if v}
    return {"keys": len(keys), "outside_certified": outside, "rate_2_5_exclusions": excluded,
            "certified": not outside and not excluded}


def components(source: dict, support: list) -> dict:
    """The source space A-H as built (P2I-2AB-1)."""
    p1, p3 = source["p1"], source["p3"]
    rates = {f"{rate:g}": {"P1": sum(e["rate"] == rate for e in p1), "P3": sum(e["rate"] == rate for e in p3)}
             for rate in LACTATE_RATES}
    entering = {rate: {case: [p for p, n in by_case.items() if n] for case, by_case in item.items()}
                for rate, item in source["by_position"].items()}
    return {"A_blood": {"P1_sets": len(p1), "P3_sets": len(p3), "by_rate": rates,
                        "values": {n: sorted({e[n] for e in p3}) for n in P1_DIMS}},
            "B_positions": entering, "C_rates": list(LACTATE_RATES), "D_crystalloid": [p["key"] for p in support],
            "E_red_cells": {n: sorted({e[n] for e in p3}) for n in bc.UNIT},
            "F_oxygen": {"reserves": sorted({r for e in p3 for r in e["reserves"]}), "simulated_at": RESERVE,
                         "adequacy": FACULTY["adequacy"]},
            "G_haemostasis": {case: lactate_slice.endoscopy_minute(case) for case in CASES},
            "H_l3": {n: [a["value"], a["status"]] for n, a in tc.l3_audit().items()},
            "lactate_side": len(LAMBDAS),
            "candidates": len(p3) * len(support) * len(LAMBDAS),
            "candidates_with_reserve_multiplicity": sum(len(e["reserves"]) for e in p3) * len(support) * len(LAMBDAS)}


# 2. The lactate side -------------------------------------------------------------------------------------------------

KINETIC = ("debt_clearance_tau_min", "debt_per_delivery_deficit", "lactate_per_output_deficit",
           "lactate_clearance_tau_min")
LEVELS = fr.LACTATE_LEVELS
ARRIVAL_PAIRS = tc.ARRIVAL_PAIRS
DEMAND_RULE = ("metabolic_demand_baseline is not variable: the registry has no candidate point for it (1 for "
               "uncomplicated haemorrhage; never a free parameter for lactate) and calibration.case_values fixes 1.0. "
               "The earlier draft's 0.9 / 1.1 sensitivity is not a registry range and is not applied.")
INTRINSIC_RULE = "intrinsic_sinus_rate stays at its band midpoint: it reaches no haemodynamics, D or lactate (checked)."


def kinetic_points() -> dict:
    return {name: tuple(calibration.REGISTRY[name].points()) for name in KINETIC}


def lambdas() -> list[tuple]:
    """Every lactate-side combination: (tau_D, deficit-to-D gain, D-to-lactate gain, tau_lactate, excess level,
    arrival debt level, arrival delivery level)."""
    points = kinetic_points()
    return [(*kinetics, excess, debt, delivery)
            for kinetics in itertools.product(*(points[name] for name in KINETIC))
            for excess in LEVELS for debt, delivery in ARRIVAL_PAIRS]


LAMBDAS = lambdas()


def lambda_label(index: int) -> dict:
    tau_d, gain_k, gain, tau_l, excess, debt, delivery = LAMBDAS[index]
    return {"debt_clearance_tau_min": tau_d, "debt_per_delivery_deficit": gain_k, "lactate_per_output_deficit": gain,
            "lactate_clearance_tau_min": tau_l, "arrival_lactate_excess": excess, "arrival_oxygen_debt": debt,
            "arrival_delivery_ratio": delivery}


def arrival_table() -> dict:
    """Each case's arrival values per band level, built as the core builds them (ratio re-anchored as ratio / rho)."""
    out = {}
    for case in CASES:
        found = {}
        for excess, debt, delivery in itertools.product(LEVELS, LEVELS, LEVELS):
            values = calibration.case_values(case, calibration.GICandidate({}, excess=excess, debt=debt,
                                                                           delivery=delivery))
            values["arrival_delivery_ratio"] /= RESERVE
            anchors = gi_reference.candidate_anchors(case, values)
            found[(excess, debt, delivery)] = anchors
        lactate = {a.lactate for a in found.values()}
        floor = {min(PROFILE.lactate_floor, a.lactate) for a in found.values()}
        demand = {a.metabolic_demand_baseline for a in found.values()}
        table = {"lactate": lactate.pop(), "floor": floor.pop(), "demand_baseline": demand.pop(),
                 "excess": {}, "baseline": {}, "debt": {}, "ratio": {}}
        if lactate or floor or demand:
            raise AssertionError(f"{case}: the arrival lactate, floor or demand depends on a band level")
        for (excess, debt, delivery), anchors in found.items():
            for name, level, value in (("excess", excess, anchors.arrival_lactate_excess),
                                       ("baseline", excess, lactate_baseline(anchors)),
                                       ("debt", debt, anchors.arrival_oxygen_debt),
                                       ("ratio", delivery, anchors.arrival_delivery_ratio)):
                if table[name].setdefault(level, value) != value:
                    raise AssertionError(f"{case}: {name} depends on another band level")
        out[case] = table
    return out


# 3. Haemodynamics once, D and lactate post-processed ------------------------------------------------------------------

FACTORIZATION = (
    "Each case's haemodynamic trajectory (delivery_rel and demand every minute, the GI module's haemostasis minute and "
    "any stop) is simulated once per scenario and blood input by the core: L1 per P1 set, L2 per P1 set and "
    "crystalloid point, L3 per P3 set, at reserve 2.5, the band-midpoint arrival and the P2F midpoint kinetics, none "
    "of which reaches it. For each arrival delivery level the deficit is effective_oxygen_deficit(demand, ratio x "
    "delivery_rel, 2.5) with ratio = level / 2.5; D follows the core's minute exactly (D + (g x deficit(delivery of "
    "the minute before, demand of the minute) - D / tau_D), within the channel guard), lactate excess X its exact "
    "recurrence (X + G / (tau_D tau_L) x D of the minute before - X / tau_L) and lactate = max(min(floor, arrival), "
    "baseline + X). FD-LAC reads deficit, D and lactate of each minute's end state. A sample of full core runs (every "
    "scenario, three blood sets per rate, six lactate-side points; reserve 1 and 3 and intrinsic lower / upper on "
    "the canonical point) must agree: exactly at reserve 2.5, within 1e-9 with identical verdicts at the other "
    "reserves (rho cancels only up to rounding).")


def scenario_items(case: str, scenario: str, values: dict) -> tuple:
    """The engine-produced scenario's inputs with the candidate's blood, crystalloid and red-cell values."""
    out = []
    for item in lactate_slice.scenario_inputs(case, scenario):
        kind = type(item).__name__
        if kind == "GIHaemorrhage":
            item = replace(item, blood_loss_ml_per_min=values[bc.BLEED])
        elif kind == "Crystalloid":
            item = replace(item, effective_ml_per_ml=values[bf.EFFECTIVE], leak_tau_min=values[bf.LEAK],
                           transient_share=values[bf.TRANSIENT])
        elif kind == "PackedRedCells":
            item = replace(item, volume_ml_per_unit=values["red_cell_unit_volume_ml"],
                           unit_hb_g_dl=values["red_cell_unit_hb_g_dl"])
        elif kind not in ("ProtonPumpInhibitor", "EndoscopicHemostasis"):
            raise AssertionError(f"{case} {scenario}: unexpected input {kind}")
        out.append(item)
    return tuple(out)


def controlled_at(state) -> int | None:
    """The minute the core's GI haemorrhage module recorded haemostasis (its own state)."""
    found = [record["controlled_at"] for key, record in state.internal.items()
             if key.startswith("disease_module:") and "controlled_at" in record]
    if len(found) != 1:
        raise AssertionError("a GI run has exactly one GI haemorrhage module")
    return found[0]


def blood_values(entry: dict, case: str, bag: dict | None = None) -> dict:
    values = {name: entry[name] for name in (P3_DIMS if bc.UNIT[0] in entry else P1_DIMS)}
    values[bc.BLEED], values[bc.POS], values["reserve"] = entry["rate"], entry["positions"][case], RESERVE
    return {**values, **(bag or {})}


def _haemodynamic(task: tuple) -> tuple:
    case, scenario, items = task
    values = dict(items)
    anchors, profile, full = blood_anchors.setup(case, **values)
    states, stop = blood_anchors.trajectory(anchors, scenario_items(case, scenario, full), MINUTES, profile)
    return task, {"delivery_rel": [derive(s, anchors, profile).delivery_rel for s in states],
                  "demand": [s.aux.oxygen_demand for s in states], "controlled_at": controlled_at(states[-1]),
                  "stop": stop}


def haemodynamic_task(case: str, scenario: str, values: dict) -> tuple:
    return case, scenario, tuple(sorted(values.items()))


def debt_series(debt_input: list, d0: float, tau_d: float, gain_k: float) -> list:
    """The core's D, minute by minute (integration._oxygen_debt and the channel guard)."""
    lower, upper = CHANNEL_BOUNDS[Channel.D][:2]
    out, debt = [d0], d0
    for deficit in debt_input:
        debt = min(upper, max(lower, debt + (gain_k * deficit - debt / tau_d)))
        out.append(debt)
    return out


def lactate_series(debt: list, x0: float, tau_d: float, tau_l: float, gain: float, baseline: float,
                   floor: float) -> list:
    """The core's lactate excess (derived.lactate_after_minute, from the D of the minute before) and the lactate
    derive() reads from it."""
    production = gain / (tau_d * tau_l)
    excess = x0
    out = [max(floor, baseline + excess)]
    for d in debt[:-1]:
        excess = excess + production * d - excess / tau_l
        out.append(max(floor, baseline + excess))
    return out


# 4. FD-LAC with the current semantics --------------------------------------------------------------------------------

SETTINGS = fd.params()
RECOVERING, PERSISTENT = "RECOVERING_CRITICAL", "PERSISTENT_OR_WORSENING_CRITICAL"
ADEQUATE = "ADEQUATE"
CURRENT_RULES = {
    "adequacy": "minute m is adequate when effective_oxygen_deficit(demand_m, delivery_m, reserve) == 0, i.e. reserve "
                "x delivery >= demand; faculty_constraints.adequate reads exactly that with delivery := reserve x "
                "effective delivery and tolerance 0",
    "windows": "a critical bleeding window is a maximal span of minutes with active bleeding (before the GI module's "
               "haemostasis minute) and deficit > 0; it is judged when it lasts at least sustained_min (30)",
    "declines": "inside a window, a substantial sustained decline is two reassessment points (the window's ends and "
                "every multiple of 15 min) at least 30 min apart with L(late) <= (1 - 0.10) L(early) (FD-LAC v2's "
                "frozen threshold, unchanged)",
    "classification": "each such pair is RECOVERING_CRITICAL when deficit(late) < deficit(early) and "
                      "PERSISTENT_OR_WORSENING_CRITICAL otherwise (stable or worsening); exact comparison, no "
                      "tolerance",
    "FD-LAC-01": "L1 before minute 60 (windows clipped at 60): no PERSISTENT_OR_WORSENING_CRITICAL decline; no window "
                 "to judge is NOT_APPLICABLE (passes, FD-LAC v2)",
    "FD-LAC-02/03": "faculty_constraints.fd_lac_envelope: L60 of L1 inside 4.4-7.0 (57m) / 3.4-5.5 (72f), inclusive",
    "FD-LAC-04": "faculty_constraints.fd_lac_04 with the adequacy above: T* = later of haemostasis and the onset of "
                 "adequacy sustained 30 min; L(T*+30) < L(T*) with ongoing clearance (L(T*+30) <= L(T*+15)); "
                 "ALREADY_NORMALIZED at L(T*) <= 2.0; NOT_EVALUABLE without sustained adequacy (passes, FD-LAC v2); "
                 "the reduction at 30 min is reported, the 5, 10 and 15 % thresholds are sensitivity only",
    "FD-LAC-05": "faculty_constraints.fd_lac_05 with the adequacy above: L120 inside 1.5-4.0 (57m) / 1.2-3.5 (72f) and "
                 "L120 < L(T*), with adequacy from T* to 120; otherwise NOT_EVALUABLE (passes, FD-LAC v2)",
    "FD-LAC-06": "every engine-produced run (L1, L2, L3): no PERSISTENT_OR_WORSENING_CRITICAL decline in any judged "
                 "window; RECOVERING_CRITICAL declines and declines while adequate are allowed",
    "stopped": "a haemodynamic trajectory that stops before minute 120 (output reached zero with a pulse; collapse "
               "stays off) rejects every candidate that reads it (STOPPED_TRAJECTORY, counted apart)",
}


class Context:
    """One run's oxygen side as FD-LAC reads it, everything that does not depend on the lactate side, computed once:
    effective delivery, oxygen available (reserve x delivery), demand and deficit of each minute's end state, the
    deficit the core's D update reads (delivery of the minute before, demand of the minute), and the judged windows and
    reassessment pairs."""

    __slots__ = ("delivery", "available", "demand", "deficit", "debt_input", "controlled_at", "stop", "factor",
                 "fd01_windows", "fd01_pairs", "fd06_windows", "fd06_pairs", "trajectory_delivery",
                 "trajectory_demand")

    def __init__(self, delivery: list, demand: list, haemostasis: int | None, stop: int | None,
                 reserve: float = RESERVE, settings: dict = SETTINGS):
        self.delivery, self.demand, self.controlled_at, self.stop = delivery, demand, haemostasis, stop
        self.available = [reserve * d for d in delivery]
        self.deficit = [max(0.0, need - have) for need, have in zip(demand, self.available)]
        self.debt_input = [max(0.0, demand[m] - self.available[m - 1]) for m in range(1, len(demand))]
        self.factor = 1.0 - settings["meaningful_change"]
        self.trajectory_delivery, self.trajectory_demand = tuple(self.available), tuple(demand)
        windows = critical_windows(self.deficit, haemostasis)
        until, span = settings["fd01_until_min"], settings["sustained_min"]
        clipped = [(first, min(last, until)) for first, last in windows if first <= until]
        self.fd01_windows = [w for w in clipped if w[1] - w[0] >= span]
        self.fd06_windows = [w for w in windows if w[1] - w[0] >= span]
        self.fd01_pairs = _pairs(self.deficit, self.fd01_windows, settings)
        self.fd06_pairs = _pairs(self.deficit, self.fd06_windows, settings)

    def trajectory(self, lactate, debt) -> fd.Trajectory:
        return fd.Trajectory(tuple(lactate), tuple(debt), self.trajectory_delivery, self.trajectory_demand,
                             self.controlled_at)


def context_of(haemodynamic: dict, ratio: float) -> Context:
    """The factorized reading: effective delivery = ratio x delivery_rel (derived.effective_delivery)."""
    return Context([ratio * d for d in haemodynamic["delivery_rel"]], haemodynamic["demand"],
                   haemodynamic["controlled_at"], haemodynamic["stop"])


def critical_windows(deficit: list, haemostasis: int | None) -> list:
    """The maximal spans of minutes with active bleeding and deficit > 0, as (first, last)."""
    found, start = [], None
    for minute, value in enumerate(deficit):
        if (haemostasis is None or minute < haemostasis) and value > 0.0:
            start = minute if start is None else start
        elif start is not None:
            found.append((start, minute - 1))
            start = None
    if start is not None:
        found.append((start, len(deficit) - 1))
    return found


def classify_pair(deficit: list, early: int, late: int) -> str:
    return RECOVERING if deficit[late] < deficit[early] else PERSISTENT


def interval_classes(deficit: list, haemostasis: int | None, settings: dict = SETTINGS) -> list:
    """FD-LAC-06's reading of each reassessment interval with active bleeding: ADEQUATE when the deficit at its end is
    0, else RECOVERING_CRITICAL when it is below the start's, else PERSISTENT_OR_WORSENING_CRITICAL (reported)."""
    step, end = settings["reassessment_interval_min"], len(deficit) - 1
    out = []
    for start in range(0, end, step):
        stop = min(start + step, end)
        if haemostasis is not None and start >= haemostasis:
            break
        label = ADEQUATE if deficit[stop] == 0.0 else classify_pair(deficit, start, stop)
        out.append([start, stop, label])
    return out


def _pairs(deficit: list, windows: list, settings: dict) -> dict:
    """Every reassessment pair a sustained decline could use, split by the deficit's net classification."""
    out = {RECOVERING: [], PERSISTENT: []}
    for first, last in windows:
        points = fd.reassessments(first, last, settings)
        for index, early in enumerate(points):
            for late in points[index + 1:]:
                if late - early >= settings["sustained_min"]:
                    out[classify_pair(deficit, early, late)].append((early, late))
    return out


def _falls(lactate: list, pairs: list, factor: float) -> list:
    return [(early, late) for early, late in pairs if lactate[late] <= factor * lactate[early]]


def fd_lac_01(lactate: list, context: Context, settings: dict = SETTINGS) -> dict:
    """FD-LAC-01 (current semantics) on the untreated run before minute 60."""
    if not context.fd01_windows:
        return {"status": fd.NOT_APPLICABLE, "passes": settings["fd01_unapplicable_passes"], "persistent": [],
                "recovering": []}
    persistent = _falls(lactate, context.fd01_pairs[PERSISTENT], context.factor)
    recovering = _falls(lactate, context.fd01_pairs[RECOVERING], context.factor)
    return {"status": fd.FAIL if persistent else fd.PASS, "passes": not persistent, "persistent": persistent,
            "recovering": recovering}


def fd_lac_06_run(lactate: list, context: Context) -> dict:
    """FD-LAC-06 (current semantics) on one engine-produced run; the constraint holds when every run of the case
    passes."""
    persistent = _falls(lactate, context.fd06_pairs[PERSISTENT], context.factor)
    recovering = _falls(lactate, context.fd06_pairs[RECOVERING], context.factor)
    return {"status": fd.FAIL if persistent else fd.PASS, "passes": not persistent, "persistent": persistent,
            "recovering": recovering}


def kinetics_of(point: tuple) -> dict:
    tau_d, _, gain, tau_l = point[:4]
    return {"debt_clearance_tau_min": tau_d, "lactate_per_output_deficit": gain, "lactate_clearance_tau_min": tau_l}


# 5. The sequential filter ---------------------------------------------------------------------------------------------

FILTER_ORDER = (
    (L1, ("FD-LAC-02/03", "FD-LAC-01", "FD-LAC-06")),
    (L3, ("FD-LAC-04", "FD-LAC-05", "FD-LAC-06")),
    (L2, ("FD-LAC-06",)),
)
COST_RATIONALE = ("Fixed by cost before any result: L1 needs one trajectory per P1 set and case and its envelope reads "
                  "one minute; L3 needs one per P3 set (fewer than P1 sets x crystalloid points); L2 one per P1 set "
                  "and crystalloid point, the most. Within a stage every constraint is evaluated for both cases "
                  "(complete failure counts); the first failure is read in the listed order, 57m before 72f.")
STOPPED = "STOPPED_TRAJECTORY"
BITS = {
    L1: (tuple((name, case) for name in ("FD-LAC-02/03", "FD-LAC-01", "FD-LAC-06") for case in CASES)
         + ((STOPPED, None),)),
    L3: tuple((name, case) for name in ("FD-LAC-04", "FD-LAC-05", "FD-LAC-06") for case in CASES) + ((STOPPED, None),),
    L2: tuple((name, case) for name in ("FD-LAC-06",) for case in CASES) + ((STOPPED, None),),
}
ANALYTIC_REJECTION, SIMULATION_REJECTION = bf.ANALYTIC_REJECTION, bf.SIMULATION_REJECTION
REJECTION_RULE = (
    "SIMULATION_REJECTION: a candidate whose own post-processed trajectory (from the core's simulated haemodynamics) "
    "fails a constraint of the stage. Distinct evaluated units (L1: P1 set x lactate side; L3: P3 set x lactate side; "
    "L2: P1 set x crystalloid point x lactate side) carry the verdict for every candidate that projects to them: L1 "
    "reads neither the red-cell unit nor the crystalloid, L3 not the crystalloid, L2 not the red-cell unit (exact, "
    "validated). ANALYTIC_REJECTION: a candidate rejected without any trajectory of its own being evaluated; this "
    "design has none (0), and the trajectories never simulated because an earlier stage rejected the candidate are "
    "counted as simulations avoided, never as rejections.")


def _series(haemodynamic: dict, arrival: dict, wanted, cache: dict):
    """(lambda index, lactate, D, context) for the wanted lactate-side points; contexts and D series are shared."""
    contexts, debts = cache.setdefault("contexts", {}), cache.setdefault("debts", {})
    for index in wanted:
        tau_d, gain_k, gain, tau_l, excess, debt, delivery = LAMBDAS[index]
        context = contexts.get(delivery)
        if context is None:
            context = contexts[delivery] = context_of(haemodynamic, arrival["ratio"][delivery])
        key = (delivery, debt, tau_d, gain_k)
        series = debts.get(key)
        if series is None:
            series = debts[key] = debt_series(context.debt_input, arrival["debt"][debt], tau_d, gain_k)
        lactate = lactate_series(series, arrival["excess"][excess], tau_d, tau_l, gain, arrival["baseline"][excess],
                                 arrival["floor"])
        yield index, lactate, series, context


def _bit(scenario: str, name: str, case: str | None) -> int:
    return 1 << BITS[scenario].index((name, case))


def _l1_unit(task: tuple) -> tuple:
    unit, haemodynamic, arrivals, wanted = task
    masks = dict.fromkeys(wanted, 0)
    for case in CASES:
        if haemodynamic[case]["stop"] is not None:
            for index in masks:
                masks[index] |= _bit(L1, STOPPED, None)
            continue
        for index, lactate, debt, context in _series(haemodynamic[case], arrivals[case], wanted, {}):
            envelope = fd.fd_lac_envelope(context.trajectory(lactate, debt), case, SETTINGS)["passes"]
            masks[index] |= (0 if envelope else _bit(L1, "FD-LAC-02/03", case))
            masks[index] |= (0 if fd_lac_01(lactate, context)["passes"] else _bit(L1, "FD-LAC-01", case))
            masks[index] |= (0 if fd_lac_06_run(lactate, context)["passes"] else _bit(L1, "FD-LAC-06", case))
    return unit, masks


def _l3_unit(task: tuple) -> tuple:
    unit, haemodynamic, arrivals, wanted = task
    masks = dict.fromkeys(wanted, 0)
    for case in CASES:
        if haemodynamic[case]["stop"] is not None:
            for index in masks:
                masks[index] |= _bit(L3, STOPPED, None)
            continue
        for index, lactate, debt, context in _series(haemodynamic[case], arrivals[case], wanted, {}):
            trajectory = context.trajectory(lactate, debt)
            response = fd.fd_lac_04(trajectory, SETTINGS)
            residual = fd.fd_lac_05(trajectory, response["trigger"], kinetics_of(LAMBDAS[index]), lactate[0],
                                    SETTINGS, case)
            masks[index] |= (0 if response["passes"] else _bit(L3, "FD-LAC-04", case))
            masks[index] |= (0 if residual["passes"] else _bit(L3, "FD-LAC-05", case))
            masks[index] |= (0 if fd_lac_06_run(lactate, context)["passes"] else _bit(L3, "FD-LAC-06", case))
    return unit, masks


def _l2_unit(task: tuple) -> tuple:
    unit, haemodynamic, arrivals, wanted = task
    masks = dict.fromkeys(wanted, 0)
    for case in CASES:
        if haemodynamic[case]["stop"] is not None:
            for index in masks:
                masks[index] |= _bit(L2, STOPPED, None)
            continue
        for index, lactate, _, context in _series(haemodynamic[case], arrivals[case], wanted, {}):
            masks[index] |= (0 if fd_lac_06_run(lactate, context)["passes"] else _bit(L2, "FD-LAC-06", case))
    return unit, masks


def _first(scenario: str, mask: int) -> str:
    name, case = BITS[scenario][(mask & -mask).bit_length() - 1]
    return name if case is None else f"{name} {case}"


def _failures(scenario: str, mask: int) -> list:
    return [name if case is None else f"{name} {case}" for bit, (name, case) in enumerate(BITS[scenario])
            if mask >> bit & 1]


class Stage:
    """Candidate-weighted accounting of one stage."""

    def __init__(self, scenario: str):
        self.scenario = scenario
        self.entering = self.rejected = self.units = self.units_rejected = 0
        self.first = {}
        self.any = {}

    def add(self, mask: int, weight: int) -> None:
        self.entering += weight
        self.units += 1
        if mask:
            self.rejected += weight
            self.units_rejected += 1
            first = _first(self.scenario, mask)
            self.first[first] = self.first.get(first, 0) + weight
            for name in _failures(self.scenario, mask):
                self.any[name] = self.any.get(name, 0) + weight

    def report(self) -> dict:
        order = [n if c is None else f"{n} {c}" for n, c in BITS[self.scenario]]
        return {"scenario": self.scenario, "entering": self.entering, "rejected": self.rejected,
                "survivors": self.entering - self.rejected, SIMULATION_REJECTION: self.rejected,
                ANALYTIC_REJECTION: 0, "units_evaluated": self.units, "units_rejected": self.units_rejected,
                "first_failure": {n: self.first[n] for n in order if n in self.first},
                "any_failure": {n: self.any[n] for n in order if n in self.any}}


def _haemodynamics(tasks: list, map_, store: dict) -> None:
    pending = [task for task in dict.fromkeys(tasks) if task not in store]
    for task, result in map_(_haemodynamic, pending):
        store[task] = result


def filter_(source: dict, support: list, arrivals: dict, map_=map, progress=None) -> dict:
    """L1, then L3, then L2. A candidate is (P3 set, crystalloid point, lactate side); it survives when every unit it
    projects to passes in both cases."""
    say = progress or (lambda *_: None)
    p1, p3, children = source["p1"], source["p3"], source["children"]
    n_lambda, n_support = len(LAMBDAS), len(support)
    store, simulated = {}, {s: 0 for s in SCENARIOS}
    stages = {s: Stage(s) for s in SCENARIOS}
    # L1
    say("L1")
    tasks = {(i, case): haemodynamic_task(case, L1, blood_values(entry, case)) for i, entry in enumerate(p1)
             for case in CASES}
    _haemodynamics(list(tasks.values()), map_, store)
    simulated[L1] = len(set(tasks.values()))
    passing = {}
    work = [(i, {case: store[tasks[(i, case)]] for case in CASES}, arrivals, range(n_lambda)) for i in range(len(p1))]
    for i, masks in map_(_l1_unit, work):
        weight = len(children[i]) * n_support
        passing[i] = []
        for index in range(n_lambda):
            stages[L1].add(masks[index], weight)
            if not masks[index]:
                passing[i].append(index)
    # L3
    say("L3")
    alive_p1 = [i for i in range(len(p1)) if passing[i]]
    tasks = {(q, case): haemodynamic_task(case, L3, blood_values(p3[q], case)) for i in alive_p1 for q in children[i]
             for case in CASES}
    _haemodynamics(list(tasks.values()), map_, store)
    simulated[L3] = len(set(tasks.values()))
    r_ok = {}
    work = [(q, {case: store[tasks[(q, case)]] for case in CASES}, arrivals, passing[i])
            for i in alive_p1 for q in children[i]]
    for q, masks in map_(_l3_unit, work):
        i = p3[q]["p1"]
        for index in passing[i]:
            stages[L3].add(masks[index], n_support)
            if not masks[index]:
                r_ok.setdefault((i, index), []).append(q)
    # L2
    say("L2")
    wanted = {i: [index for index in passing[i] if (i, index) in r_ok] for i in alive_p1}
    alive_p1 = [i for i in alive_p1 if wanted[i]]
    tasks = {(i, d, case): haemodynamic_task(case, L2, blood_values(p1[i], case, support[d]["bag"]))
             for i in alive_p1 for d in range(n_support) for case in CASES}
    _haemodynamics(list(tasks.values()), map_, store)
    simulated[L2] = len(set(tasks.values()))
    d_ok = {}
    work = [((i, d), {case: store[tasks[(i, d, case)]] for case in CASES}, arrivals, wanted[i])
            for i in alive_p1 for d in range(n_support)]
    for (i, d), masks in map_(_l2_unit, work):
        for index in wanted[i]:
            stages[L2].add(masks[index], len(r_ok[(i, index)]))
            if not masks[index]:
                d_ok.setdefault((i, index), []).append(d)
    units = sorted((i, index, tuple(r_ok[(i, index)]), tuple(d_ok[(i, index)])) for i, index in d_ok)
    survivors = sum(len(r) * len(d) for _, _, r, d in units)
    with_reserve = sum(len(p3[q]["reserves"]) * len(d) for _, _, r, d in units for q in r)
    total = sum(len(children[i]) for i in range(len(p1))) * n_support * n_lambda
    return {"stages": [stages[s].report() for s, _ in FILTER_ORDER], "simulated": simulated,
            "candidates": total, "survivors": survivors, "survivors_with_reserve_multiplicity": with_reserve,
            "units": units, "store": store}


# 6. Validation of the factorization (P2I-2AB-3) -----------------------------------------------------------------------

VALIDATION_RULE = ("Blood sets: per rate the first, middle (floor(n / 2)) and last P3 set in source order. Lactate "
                   "side: "
                   "indices 0, n/4, n/2, 3n/4, n-1 (floor) and the canonical point (tau_D 60, g 1, G 6, tau_L 120, "
                   "midpoint excess, midpoint pair). Scenarios L1, L3 and L2 at the first and last crystalloid point, "
                   "both cases, reserve 2.5 and intrinsic midpoint: exact equality of every minute's lactate, D and "
                   "deficit, of haemostasis and stop. On the canonical point also reserve 1 and 3 (1e-9 and identical "
                   "FD-LAC verdicts) and intrinsic lower / upper (exact). Any disagreement stops the run.")
CANONICAL = (60.0, 1.0, 6.0, 120.0, "midpoint", "midpoint", "midpoint")
TOLERANCE = 1e-9


def validation_sample(source: dict, support: list) -> list[dict]:
    p3 = source["p3"]
    sets = []
    for rate in LACTATE_RATES:
        members = [q for q, entry in enumerate(p3) if entry["rate"] == rate]
        if members:
            sets.extend(dict.fromkeys((members[0], members[len(members) // 2], members[-1])))
    n = len(LAMBDAS)
    canonical = LAMBDAS.index(CANONICAL)
    points = list(dict.fromkeys((0, n // 4, n // 2, 3 * n // 4, n - 1, canonical)))
    bags = sorted({0, len(support) - 1})
    out = []
    for q in sets:
        for case in CASES:
            for index in points:
                runs = [(L1, None), (L3, None)] + [(L2, d) for d in bags]
                for scenario, d in runs:
                    variants = [(RESERVE, "midpoint")]
                    if index == canonical:
                        variants += [(1.0, "midpoint"), (3.0, "midpoint"), (RESERVE, "lower"), (RESERVE, "upper")]
                    for reserve, intrinsic in variants:
                        out.append({"q": q, "case": case, "lambda": index, "scenario": scenario, "support": d,
                                    "reserve": reserve, "intrinsic": intrinsic})
    return out


def full_run(entry: dict, case: str, scenario: str, point: tuple, bag: dict | None = None, reserve: float = RESERVE,
             intrinsic: str = "midpoint") -> dict:
    """The full core run of one blood entry and lactate-side point (no factorization): its own anchors, profile and
    inputs."""
    tau_d, gain_k, gain, tau_l, excess, debt, delivery = point
    values = {**blood_values(entry, case, bag), "reserve": reserve}
    _, profile, full = blood_anchors.setup(case, **values)
    case_values = calibration.case_values(case, calibration.GICandidate({}, excess=excess, debt=debt,
                                                                        delivery=delivery, intrinsic=intrinsic))
    case_values["preload_fraction"] = full[bc.POS]
    case_values["arrival_delivery_ratio"] /= reserve
    anchors = gi_reference.candidate_anchors(case, case_values)
    profile = replace(profile, debt_clearance_tau_min=tau_d, debt_per_delivery_deficit=gain_k,
                      lactate_per_output_deficit=gain, lactate_clearance_tau_min=tau_l)
    states, stop = blood_anchors.trajectory(anchors, scenario_items(case, scenario, full), MINUTES, profile)
    lactate, debts, deficits, available, demand, delivery_index, views = [], [], [], [], [], [], []
    for state in states:
        view = derive(state, anchors, profile)
        delivery_ = effective_delivery(view.delivery_rel, anchors)
        lactate.append(view.lactate)
        debts.append(state.D)
        deficits.append(effective_oxygen_deficit(state.aux.oxygen_demand, delivery_, reserve))
        available.append(reserve * delivery_)
        demand.append(state.aux.oxygen_demand)
        delivery_index.append(delivery_)
        views.append((state, view))
    return {"lactate": lactate, "D": debts, "deficit": deficits, "available": available, "demand": demand,
            "delivery": delivery_index, "controlled_at": controlled_at(states[-1]), "stop": stop,
            "anchors": anchors, "profile": profile, "views": views}


def _verdicts(case: str, scenario: str, lactate: list, debt: list, context: Context, point: tuple) -> dict:
    out = {"FD-LAC-06": fd_lac_06_run(lactate, context)["passes"]}
    trajectory = context.trajectory(lactate, debt)
    if scenario == L1:
        out["FD-LAC-02/03"] = fd.fd_lac_envelope(trajectory, case, SETTINGS)["passes"]
        out["FD-LAC-01"] = fd_lac_01(lactate, context)["status"]
    if scenario == L3:
        response = fd.fd_lac_04(trajectory, SETTINGS)
        out["FD-LAC-04"] = response["status"]
        out["FD-LAC-05"] = fd.fd_lac_05(trajectory, response["trigger"], kinetics_of(point), lactate[0], SETTINGS,
                                        case)["status"]
    return out


def _gap(a: list, b: list) -> float:
    if len(a) != len(b):
        return math.inf
    return max((abs(x - y) for x, y in zip(a, b)), default=0.0)


def factorized(haemodynamic: dict, arrival: dict, point: tuple) -> tuple:
    """(lactate, D, context) of one lactate-side point post-processed on a simulated haemodynamic trajectory."""
    tau_d, gain_k, gain, tau_l, excess, debt, delivery = point
    context = context_of(haemodynamic, arrival["ratio"][delivery])
    series = debt_series(context.debt_input, arrival["debt"][debt], tau_d, gain_k)
    lactate = lactate_series(series, arrival["excess"][excess], tau_d, tau_l, gain, arrival["baseline"][excess],
                             arrival["floor"])
    return lactate, series, context


def compare(full: dict, factorized_: tuple, haemodynamic: dict, case: str, scenario: str, point: tuple,
            reserve: float) -> dict:
    """A full core run against the factorized reading of the same candidate."""
    lactate, series, context = factorized_
    # The full run is read on its own: its delivery, demand, reserve, haemostasis and stop decide its windows.
    own = Context(full["delivery"], full["demand"], full["controlled_at"], full["stop"], reserve)
    adequacy = (own.deficit == full["deficit"] and all(
        fd.adequate(own.trajectory(full["lactate"], full["D"]), m, SETTINGS) == (full["deficit"][m] == 0.0)
        for m in range(len(full["deficit"]))))
    gaps = {"lactate": _gap(lactate, full["lactate"]), "D": _gap(series, full["D"]),
            "deficit": _gap(context.deficit, full["deficit"])}
    exact = lactate == full["lactate"] and series == full["D"] and context.deficit == full["deficit"]
    events = full["controlled_at"] == haemodynamic["controlled_at"] and full["stop"] == haemodynamic["stop"]
    mine = _verdicts(case, scenario, lactate, series, context, point)
    theirs = _verdicts(case, scenario, full["lactate"], full["D"], own, point)
    strict = reserve == RESERVE
    agrees = events and adequacy and mine == theirs and (exact if strict else max(gaps.values()) <= TOLERANCE)
    return {"exact": exact, "gaps": gaps, "events": events, "adequacy_is_no_deficit": adequacy, "verdicts": mine,
            "verdicts_equal": mine == theirs, "agrees": agrees}


def _validate_one(task: tuple) -> dict:
    """One sampled candidate: its full core run against the factorized reading of the filter's own haemodynamic
    trajectory (the P1 trajectory for L1 and L2, the P3 one for L3)."""
    item, entry, bag, haemodynamic, arrival = task
    case, scenario, point = item["case"], item["scenario"], LAMBDAS[item["lambda"]]
    full = full_run(entry, case, scenario, point, bag, item["reserve"], item["intrinsic"])
    return {**item, **compare(full, factorized(haemodynamic, arrival, point), haemodynamic, case, scenario, point,
                              item["reserve"])}


def _sample_task(item: dict, source: dict, support: list) -> tuple:
    entry = source["p3"][item["q"]]
    if item["scenario"] == L3:
        return haemodynamic_task(item["case"], L3, blood_values(entry, item["case"]))
    parent = source["p1"][entry["p1"]]
    bag = support[item["support"]]["bag"] if item["scenario"] == L2 else None
    return haemodynamic_task(item["case"], item["scenario"], blood_values(parent, item["case"], bag))


def validate(source: dict, support: list, arrivals: dict, map_=map) -> dict:
    sample, store = validation_sample(source, support), {}
    tasks = [_sample_task(item, source, support) for item in sample]
    _haemodynamics(tasks, map_, store)
    work = [(item, source["p3"][item["q"]], support[item["support"]]["bag"] if item["scenario"] == L2 else None,
             store[task], arrivals[item["case"]]) for item, task in zip(sample, tasks)]
    results = list(map_(_validate_one, work))
    statuses = {}
    for result in results:
        for name, value in result.pop("verdicts").items():
            label = f"{result['scenario']} {name} {value}"
            statuses[label] = statuses.get(label, 0) + 1
    return {"rule": VALIDATION_RULE, "runs": len(results), "agree": all(r["agrees"] for r in results),
            "verdicts_seen": dict(sorted(statuses.items())),
            "exact_at_reserve_2_5": all(r["exact"] for r in results if r["reserve"] == RESERVE),
            "max_gap_other_reserves": max((max(r["gaps"].values()) for r in results if r["reserve"] != RESERVE),
                                          default=0.0),
            "disagreements": [r for r in results if not r["agrees"]], "sample": results}


def structural_products() -> dict:
    """Only G x g and G x arrival debt reach lactate (given tau_D and tau_L): two lactate-side points with the same
    products give the same lactate up to rounding, on a synthetic deficit path."""
    deficit = [0.1 + 0.002 * m for m in range(MINUTES)]
    a = lactate_series(debt_series(deficit, 20.0, 60.0, 2.0), 3.4, 60.0, 120.0, 6.0, 1.0, 0.8)
    b = lactate_series(debt_series(deficit, 10.0, 60.0, 1.0), 3.4, 60.0, 120.0, 12.0, 1.0, 0.8)
    return {"same_products_gap": _gap(a, b), "rule": "lactate = baseline + X0 a^t + G D0 W1(tau_D, tau_L) + G g "
                                                     "W2(tau_D, tau_L, deficit): only G x g and G x D0 reach it"}


# 7. Survivors: statistics, identifiability, representatives -----------------------------------------------------------

FD04_THRESHOLDS = fd.REPORTED_FALL_THRESHOLDS
HISTOGRAM_STEP = 0.001


def _weighted_quantiles(histogram: dict, total: int) -> dict | None:
    if not total:
        return None
    ordered = sorted(histogram.items())
    out, cumulative = {}, 0
    targets = {"p05": 0.05, "median": 0.5, "p95": 0.95}
    for value, weight in ordered:
        cumulative += weight
        for name, share in list(targets.items()):
            if cumulative >= share * total:
                out[name] = value * HISTOGRAM_STEP
                del targets[name]
    return out


class Summary:
    """Exact min / max, weighted counts and a 0.001-wide histogram (quantiles at that resolution)."""

    def __init__(self):
        self.low = self.high = None
        self.total = 0
        self.histogram = {}

    def add(self, value: float, weight: int) -> None:
        self.low = value if self.low is None else min(self.low, value)
        self.high = value if self.high is None else max(self.high, value)
        self.total += weight
        slot = math.floor(value / HISTOGRAM_STEP + 0.5)
        self.histogram[slot] = self.histogram.get(slot, 0) + weight

    def report(self) -> dict | None:
        if not self.total:
            return None
        return {"min": self.low, "max": self.high, "weight": self.total,
                **_weighted_quantiles(self.histogram, self.total), "resolution": HISTOGRAM_STEP}


def _survivor_l1(task: tuple) -> tuple:
    unit, haemodynamic, arrivals, wanted = task
    out = {}
    for case in CASES:
        for index, lactate, _, context in _series(haemodynamic[case], arrivals[case], wanted, {}):
            first = fd_lac_01(lactate, context)
            sixth = fd_lac_06_run(lactate, context)
            out[(index, case)] = {"L60": lactate[60], "L0": lactate[0], "fd01": first["status"],
                                  "recovering": len(first["recovering"]) + len(sixth["recovering"])}
    return unit, out


def _after_haemostasis(context: Context, settings: dict = SETTINGS) -> list:
    """Reported only (FD-LAC judges active bleeding): the PERSISTENT_OR_WORSENING_CRITICAL reassessment pairs of the
    critical windows after haemostasis, at least sustained_min long."""
    if context.controlled_at is None:
        return []
    windows = [(max(first, context.controlled_at), last) for first, last in critical_windows(context.deficit, None)
               if last >= context.controlled_at]
    return _pairs(context.deficit, [w for w in windows if w[1] - w[0] >= settings["sustained_min"]],
                  settings)[PERSISTENT]


def _survivor_l3(task: tuple) -> tuple:
    unit, haemodynamic, arrivals, wanted = task
    out = {}
    for case in CASES:
        later = {}
        for index, lactate, debt, context in _series(haemodynamic[case], arrivals[case], wanted, {}):
            trajectory = context.trajectory(lactate, debt)
            response = fd.fd_lac_04(trajectory, SETTINGS)
            residual = fd.fd_lac_05(trajectory, response["trigger"], kinetics_of(LAMBDAS[index]), lactate[0],
                                    SETTINGS, case)
            trigger = response["trigger"]
            compensated = trigger is not None and any(
                context.deficit[m] == 0.0 and context.delivery[m] < context.demand[m]
                for m in range(trigger, min(trigger + SETTINGS["fd04_window_min"], len(lactate) - 1) + 1))
            after = later.get(id(context))
            if after is None:
                after = later[id(context)] = _after_haemostasis(context)
            out[(index, case)] = {"fd04": response["status"], "reduction": response.get("reduction_at_window"),
                                  "after_haemostasis": bool(_falls(lactate, after, context.factor)),
                                  "fd05": residual["status"], "L120": lactate[120], "trigger": trigger,
                                  "at_trigger": response.get("at_trigger"),
                                  "recovering": len(fd_lac_06_run(lactate, context)["recovering"]),
                                  "compensated_after_trigger": compensated,
                                  "memory": residual["debt_memory_at_reference_debt"]}
    return unit, out


def _survivor_l2(task: tuple) -> tuple:
    unit, haemodynamic, arrivals, wanted = task
    out = {}
    for case in CASES:
        for index, lactate, _, context in _series(haemodynamic[case], arrivals[case], wanted, {}):
            out[(index, case)] = {"recovering": len(fd_lac_06_run(lactate, context)["recovering"])}
    return unit, out


def survivor_statistics(source: dict, support: list, arrivals: dict, filtered: dict, map_=map) -> dict:
    """Recomputes the survivors' readings (never their verdicts) to report distributions, FD-LAC-04 sensitivity, the
    RECOVERING_CRITICAL declines the current semantics allowed, and adequacy reached only by compensation."""
    p1, p3, store = source["p1"], source["p3"], filtered["store"]
    units = filtered["units"]
    by_p1, by_p3, by_d = {}, {}, {}
    for i, index, r, d in units:
        by_p1.setdefault(i, []).append(index)
        for q in r:
            by_p3.setdefault(q, []).append(index)
        for k in d:
            by_d.setdefault((i, k), []).append(index)
    l1 = dict(map_(_survivor_l1, [(i, {c: store[haemodynamic_task(c, L1, blood_values(p1[i], c))] for c in CASES},
                                   arrivals, idx) for i, idx in sorted(by_p1.items())]))
    l3 = dict(map_(_survivor_l3, [(q, {c: store[haemodynamic_task(c, L3, blood_values(p3[q], c))] for c in CASES},
                                   arrivals, idx) for q, idx in sorted(by_p3.items())]))
    l2 = dict(map_(_survivor_l2, [((i, k), {c: store[haemodynamic_task(c, L2, blood_values(p1[i], c,
                                                                                         support[k]["bag"]))]
                                            for c in CASES}, arrivals, idx) for (i, k), idx in sorted(by_d.items())]))
    summaries = {name: {case: Summary() for case in CASES} for name in ("L60", "L120", "reduction", "at_trigger",
                                                                       "memory")}
    fd04 = {case: {} for case in CASES}
    fd05 = {case: {} for case in CASES}
    fd01 = {case: {} for case in CASES}
    sensitivity = {f"{t:g}": 0 for t in FD04_THRESHOLDS}
    recovering = {L1: 0, L3: 0, L2: 0}
    compensated = after_haemostasis = 0
    trigger_minutes = {case: {} for case in CASES}
    for i, index, r, d in units:
        n_r, n_d = len(r), len(d)
        for case in CASES:
            item = l1[i][(index, case)]
            summaries["L60"][case].add(item["L60"], n_r * n_d)
            fd01[case][item["fd01"]] = fd01[case].get(item["fd01"], 0) + n_r * n_d
        if any(l1[i][(index, case)]["recovering"] for case in CASES):
            recovering[L1] += n_r * n_d
        for q in r:
            items = {case: l3[q][(index, case)] for case in CASES}
            for case, item in items.items():
                fd04[case][item["fd04"]] = fd04[case].get(item["fd04"], 0) + n_d
                fd05[case][item["fd05"]] = fd05[case].get(item["fd05"], 0) + n_d
                summaries["L120"][case].add(item["L120"], n_d)
                summaries["memory"][case].add(item["memory"], n_d)
                trigger_minutes[case][str(item["trigger"])] = trigger_minutes[case].get(str(item["trigger"]), 0) + n_d
                if item["reduction"] is not None:
                    summaries["reduction"][case].add(item["reduction"], n_d)
                if item["at_trigger"] is not None:
                    summaries["at_trigger"][case].add(item["at_trigger"], n_d)
            for threshold in FD04_THRESHOLDS:
                if all(item["fd04"] != fd.PASS or item["reduction"] >= threshold for item in items.values()):
                    sensitivity[f"{threshold:g}"] += n_d
            if any(item["recovering"] for item in items.values()):
                recovering[L3] += n_d
            if any(item["compensated_after_trigger"] for item in items.values()):
                compensated += n_d
            if any(item["after_haemostasis"] for item in items.values()):
                after_haemostasis += n_d
        for k in d:
            if any(l2[(i, k)][(index, case)]["recovering"] for case in CASES):
                recovering[L2] += n_r
    survivors = filtered["survivors"]
    return {"L60": {c: summaries["L60"][c].report() for c in CASES},
            "L120": {c: summaries["L120"][c].report() for c in CASES},
            "fd04_reduction": {c: summaries["reduction"][c].report() for c in CASES},
            "fd04_at_trigger": {c: summaries["at_trigger"][c].report() for c in CASES},
            "fd05_debt_memory_at_reference_debt": {c: summaries["memory"][c].report() for c in CASES},
            "fd01_status": fd01, "fd04_status": fd04, "fd05_status": fd05, "trigger_minute": trigger_minutes,
            "fd04_sensitivity": {"thresholds": sensitivity, "survivors": survivors,
                                 "note": "sensitivity only: survivors that would also pass FD-LAC-04 with the fall "
                                         "required at the threshold; never filters"},
            "recovering_declines_allowed": {"survivors_with_one": recovering,
                                            "note": "survivors whose run had a sustained substantial decline that the "
                                                    "current semantics allowed as RECOVERING_CRITICAL"},
            "adequacy_by_compensation_after_trigger": compensated,
            "persistent_critical_decline_after_haemostasis": {
                "survivors": after_haemostasis,
                "note": "reported, never filtered: FD-LAC-06 judges active bleeding only; L3 runs with a sustained "
                        "substantial lactate fall during a persistent or worsening deficit after haemostasis"},
            "weights": {"survivor_units": len(units)},
            "_l60": {(i, index): {case: l1[i][(index, case)]["L60"] for case in CASES} for i, index, _, _ in units}}


SEPARATELY = bc.SEPARATELY
IDENTIFIABILITY_RULE = ("On the survivors, per dimension, against the values present in the source space (the "
                        "reserve read from each P3 set's reserves): one value explored = NOT_VARIED; one left = "
                        "WELL_CONSTRAINED; some excluded = PARTIALLY_CONSTRAINED; none excluded = POORLY_IDENTIFIED; "
                        "structural = NON_IDENTIFIABLE_SEPARATELY (G and g reach lactate only as G x g with G x "
                        "arrival debt; rho cancels). Edge status: INTERIOR / OPEN_* of blood_extension.edge_status on "
                        "varied numeric or band-level dimensions (lower < midpoint < upper). No value is chosen by its "
                        "frequency.")
STRUCTURAL = {"debt_per_delivery_deficit": "only G x g (and G x arrival debt) reaches lactate",
              "lactate_per_output_deficit": "only G x g (and G x arrival debt) reaches lactate",
              "reserve": "rho cancels in the deficit, D, lactate and adequacy (ratio re-anchored as ratio / rho)"}


def _dimension_values(source: dict, support: list):
    """(dimension, value) pairs of a candidate's three parts."""
    def blood(q):
        entry = source["p3"][q]
        out = [("bleed_ml_per_min", entry["rate"])] + [(n, entry[n]) for n in P3_DIMS]
        return out + [(f"{bc.POS}|{case}", entry["positions"][case]) for case in CASES]

    def reserves(q):
        return [("reserve", r) for r in source["p3"][q]["reserves"]]

    def crystalloid(k):
        return [("crystalloid_point", support[k]["key"]), ("crystalloid_Finf", support[k]["Finf"]),
                ("crystalloid_tau", support[k]["tau"]), ("crystalloid_F0", support[k]["F0"])]

    def lactate(index):
        tau_d, gain_k, gain, tau_l, excess, debt, delivery = LAMBDAS[index]
        return [("debt_clearance_tau_min", tau_d), ("debt_per_delivery_deficit", gain_k),
                ("lactate_per_output_deficit", gain), ("lactate_clearance_tau_min", tau_l),
                ("arrival_lactate_excess", excess), ("arrival_pair", f"{debt}|{delivery}"),
                ("arrival_oxygen_debt", debt), ("arrival_delivery_ratio", delivery),
                ("G x g", gain * gain_k)]
    return blood, reserves, crystalloid, lactate


def identifiability(source: dict, support: list, filtered: dict) -> dict:
    blood, reserves, crystalloid, lactate = _dimension_values(source, support)
    n_lambda, n_support = len(LAMBDAS), len(support)
    explored, surviving = {}, {}

    def add(table, pairs, weight):
        for name, value in pairs:
            key = f"{value:g}" if isinstance(value, float) else str(value)
            table.setdefault(name, {})
            table[name][key] = table[name].get(key, 0) + weight

    n_p3 = len(source["p3"])
    for q in range(n_p3):
        add(explored, blood(q) + reserves(q), n_support * n_lambda)
    for k in range(n_support):
        add(explored, crystalloid(k), n_p3 * n_lambda)
    for index in range(n_lambda):
        add(explored, lactate(index), n_p3 * n_support)
    for _, index, r, d in filtered["units"]:
        for q in r:
            add(surviving, blood(q) + reserves(q), len(d))
        for k in d:
            add(surviving, crystalloid(k), len(r))
        add(surviving, lactate(index), len(r) * len(d))
    out = {}
    for name in explored:
        values = sorted(explored[name], key=_order)
        left = sorted((v for v, n in surviving.get(name, {}).items() if n), key=_order)
        if name in STRUCTURAL:
            status = SEPARATELY
        elif len(values) == 1:
            status = "NOT_VARIED"
        elif not left:
            status = "NOT_ASSESSABLE (no survivors)"
        elif len(left) == 1:
            status = bc.WELL
        elif len(left) < len(values):
            status = bc.PARTIAL
        else:
            status = bc.POOR
        edge = None
        if len(values) > 1 and left and all(_is_number(v) or v in LEVELS for v in values):
            edge = be.edge_status([_order(v) for v in values], [_order(v) for v in left])
        out[name] = {"explored": values, "surviving": left, "status": status, "edge": edge,
                     "structural": STRUCTURAL.get(name), "explored_weight": explored[name],
                     "surviving_weight": surviving.get(name, {})}
    return {"rule": IDENTIFIABILITY_RULE, "dimensions": out}


def _is_number(value: str) -> bool:
    try:
        float(value)
    except ValueError:
        return False
    return True


def _order(value: str):
    """Numbers by value, band levels by their order (lower < midpoint < upper); other labels last, by name."""
    return (0, float(value), "") if _is_number(value) else (1, LEVELS.index(value) if value in LEVELS else 3, value)


REPRESENTATIVE_RULE = ("Among all surviving candidates (reserve collapsed), ordered by the 57m L1 lactate at 60 min, "
                       "then the 72f L1 lactate at 60 min, then P1 set, lactate side, P3 set and crystalloid point in "
                       "source order: LOW = first, MID = floor(n / 2)-th, HIGH = last. Each is re-run by the full core "
                       "(57m and 72f, L1 and L3) and read at 0, 15, 30, 60, 90 and 120 min.")
FLAG_RULES = {
    "WORSENING_CRITICAL_WITH_LARGE_LACTATE_FALL": "two reassessment points (multiples of 15) >= 30 min apart, "
                                                  "deficit > "
                                                  "0 at every minute between them, deficit(late) >= deficit(early) and "
                                                  "L(late) <= 0.90 L(early), bleeding active or not",
    "ADEQUATE_WITH_DELAYED_CLEARANCE": "a reassessment point t with deficit == 0 from t to t + 30, L(t) > 2.0 and "
                                       "L(t + 30) >= L(t)",
    "PERSISTENT_HIGH_D": "L3 only (after definitive management): D at 120 min >= 50 % of the run's peak D (peak > 0)",
    "INSTANT_NORMALIZATION": "a one-minute lactate fall larger than 10 % of the minute before",
    "INCOMPATIBLE_WITH_SURVIVAL": "PROPOSED review markers, not faculty-approved: the run stopped, effective output < "
                                  "0.25 of arrival, lactate >= 10 mmol/L or Hb < 5 g/dL at any minute",
}


def representatives(source: dict, support: list, filtered: dict, statistics_l1: dict) -> dict:
    units = filtered["units"]
    if not units:
        return {}
    ordered = sorted(units, key=lambda u: (statistics_l1[(u[0], u[1])][CASES[0]], statistics_l1[(u[0], u[1])][CASES[1]],
                                           u[0], u[1]))
    total = filtered["survivors"]
    picks = {"LOW": 0, "MID": total // 2, "HIGH": total - 1}
    out = {}
    for tag, rank in picks.items():
        cumulative = 0
        for i, index, r, d in ordered:
            size = len(r) * len(d)
            if rank < cumulative + size:
                offset = rank - cumulative
                q, k = r[offset // len(d)], d[offset % len(d)]
                out[tag] = {"p1": i, "lambda": index, "p3": q, "support": k, "rank": rank}
                break
            cumulative += size
    return out


def _flags(series: dict, scenario: str) -> dict:
    lactate, deficit, debt = series["lactate"], series["deficit"], series["D"]
    points = list(range(0, len(lactate), 15))
    worsening = any(late - early >= 30 and all(deficit[m] > 0.0 for m in range(early, late + 1))
                    and deficit[late] >= deficit[early] and lactate[late] <= 0.9 * lactate[early]
                    for a, early in enumerate(points) for late in points[a + 1:])
    delayed = any(t + 30 < len(lactate) and all(deficit[m] == 0.0 for m in range(t, t + 31)) and lactate[t] > 2.0
                  and lactate[t + 30] >= lactate[t] for t in points)
    peak = max(debt)
    falls = [(lactate[m - 1] - lactate[m]) / lactate[m - 1] for m in range(1, len(lactate))]
    incompatible = (series["stop"] is not None or min(series["output"]) < 0.25 or max(lactate) >= 10.0
                    or min(series["hb"]) < 5.0)
    return {"WORSENING_CRITICAL_WITH_LARGE_LACTATE_FALL": worsening, "ADEQUATE_WITH_DELAYED_CLEARANCE": delayed,
            "PERSISTENT_HIGH_D": scenario == L3 and peak > 0.0 and debt[-1] >= 0.5 * peak,
            "INSTANT_NORMALIZATION": max(falls, default=0.0) > 0.10, "INCOMPATIBLE_WITH_SURVIVAL": incompatible}


def review(source: dict, support: list, picks: dict) -> dict:
    """P2I-2AB-12: the representatives re-run by the full core, read at TIMES, with the predeclared flags."""
    out = {}
    for tag, pick in picks.items():
        entry = source["p3"][pick["p3"]]
        item = {"pick": pick, "lambda": lambda_label(pick["lambda"]), "blood": {
            "rate": entry["rate"], **{n: entry[n] for n in P3_DIMS}, "positions": entry["positions"],
            "reserves": entry["reserves"]}, "crystalloid": support[pick["support"]]["key"], "runs": {}}
        for case in CASES:
            for scenario in (L1, L3):
                full = full_run(entry, case, scenario, LAMBDAS[pick["lambda"]])
                rows = []
                for minute in TIMES:
                    if minute >= len(full["views"]):
                        continue
                    state, _ = full["views"][minute]
                    reading = blood_anchors.reading(state, full["anchors"], full["profile"])
                    rows.append({"minute": minute, "circulating_ml": reading["circulating_ml"],
                                 "shed_ml": reading["shed_ml"], "hb": reading["hb"], "refill_ml": reading["refill_ml"],
                                 "transfused_ml": reading["transfused_ml"], "output_rel": reading["output_rel"],
                                 "do2": reading["do2"], "state": reading["state"],
                                 "effective_deficit": reading["effective_deficit"], "D": state.D,
                                 "lactate": full["lactate"][minute]})
                series = {"lactate": full["lactate"], "deficit": full["deficit"], "D": full["D"], "stop": full["stop"],
                          "output": [view.output_rel for _, view in full["views"]],
                          "hb": [state.hb for state, _ in full["views"]]}
                item["runs"][f"{case}|{scenario}"] = {"rows": rows, "flags": _flags(series, scenario),
                                                       "intervals": interval_classes(full["deficit"],
                                                                                     full["controlled_at"]),
                                                       "controlled_at": full["controlled_at"], "stop": full["stop"]}
        out[tag] = item
    return out


# 8. The legacy lactate: a reference, read only after the filter ------------------------------------------------------

LEGACY_RULE = ("LEGACY REFERENCE, NOT A CALIBRATION TARGET: the family engine's own lactate at 0, 15, 30, 60, 90 and "
               "120 min, read after the filter and the representatives, never by a constraint or an ordering.")


class LegacyLock:
    """While held, reading the legacy lactate raises: the filter cannot use it."""

    held = False

    def __enter__(self):
        LegacyLock.held = True
        return self

    def __exit__(self, *exc):
        LegacyLock.held = False
        return False


def legacy_reference(review_: dict) -> dict:
    if LegacyLock.held:
        raise AssertionError("the legacy lactate is read only after the filter")
    out = {}
    for case in CASES:
        out[case] = {}
        for scenario in SCENARIOS:
            snapshots = {item["minute"]: item for item in
                         calibration._legacy_run(case, lactate_slice.ORDERS[scenario]).snapshots}
            out[case][scenario] = {str(m): snapshots[m]["lactate_lab"] for m in TIMES if m in snapshots}
    beside = {}
    for tag, item in review_.items():
        beside[tag] = {}
        for key, run_ in item["runs"].items():
            case, scenario = key.split("|")
            beside[tag][key] = {str(row["minute"]): {"core": row["lactate"],
                                                     "legacy": out[case][scenario].get(str(row["minute"]))}
                                for row in run_["rows"]}
    return {"rule": LEGACY_RULE, "legacy": out, "beside_representatives": beside}


# 9. The P2F guard -----------------------------------------------------------------------------------------------------

class P2FRegionConsumed(AssertionError):
    pass


#: The entry points of the historical P2F candidate region and of everything built on it.
P2F_ENTRY_POINTS = ((lactate_slice.decision_pack, "admissible"), (calibration, "gi_candidates"),
                    (lactate_slice, "region_runs"))


class P2FGuard:
    """While held, every P2F entry point raises: the source space and the filter cannot consume that region."""

    def __enter__(self):
        self.saved = [(module, name, getattr(module, name)) for module, name in P2F_ENTRY_POINTS]

        def refuse(*_, **__):
            raise P2FRegionConsumed("the historical P2F candidate region is not an input of the lactate rebuild")
        for module, name, _ in self.saved:
            setattr(module, name, refuse)
        return self

    def __exit__(self, *exc):
        for module, name, original in self.saved:
            setattr(module, name, original)
        return False


def guard_worker() -> None:
    """A worker process's initializer: the P2F guard and the legacy lock for the worker's whole life."""
    P2FGuard().__enter__()
    LegacyLock().__enter__()


# 10. Verdict, region and freeze -------------------------------------------------------------------------------------

SATISFIED, NOT_READY = "LACTATE_CALIBRATION_CONSTRAINTS_SATISFIED", "LACTATE_NOT_READY"
REGION_STATUS = "FACULTY-CONSTRAINED CURRENT-PHYSIOLOGY LACTATE REGION (no value selected or approved)"
VERDICT_RULE = ("LACTATE_CALIBRATION_CONSTRAINTS_SATISFIED when readiness is the faculty's READY, the blood source "
                "reproduces the certified counts, its keys are certified for the crystalloid support, the "
                "factorization agrees with the full core, at least one candidate survives, and among the survivors "
                "FD-LAC-04 and FD-LAC-05 are actually evaluated (PASS or ALREADY_NORMALIZED) in both cases for at "
                "least "
                "one candidate, so the definitive-management constraints are not met only as NOT_EVALUABLE. Otherwise "
                "LACTATE_NOT_READY with the first blocker. No candidate, value or parameter is selected or approved.")
NEXT_DOMAIN = ("Recommended next domain (not started; needs its own authorization): blood-pressure and heart-rate "
               "calibration of the shadow core on the faculty-constrained blood, crystalloid and lactate region, "
               "before collapse, GI migration or any runtime integration.")
INLINE_UNITS = 20000
POLICY = ("Shadow only. Current certified physiology only: the P2F historical region is never read (P2FGuard). Blood "
          "constraints and FD-BLD envelopes are the frozen ones; FD-LAC-02..05 are faculty_constraints' frozen "
          "functions; FD-LAC-01 and 06 read the faculty's 2026-10-28 recovery semantics; adequacy is deficit == 0. "
          "The crystalloid support propagates whole; no tau is preferred. Haemodynamics are simulated once and D and "
          "lactate post-processed exactly (validated against full runs, else stop). Filter order L1, L3, L2. The "
          "legacy lactate is read after the filter only. Nothing is fitted, selected or approved; no SBP, MAP or HR "
          "is calibrated; collapse stays off.")


def verdict(ready: dict, source: dict, keys: dict, validation: dict, filtered: dict | None,
            statistics: dict | None) -> dict:
    checks = [("readiness", ready["verdict"] == READINESS, "readiness is not the faculty's READY"),
              ("source", source["reproduced"], "the blood source does not reproduce the certified counts"),
              ("keys", keys["certified"], "a source key is not certified for the crystalloid support"),
              ("factorization", validation["agree"], "the factorization does not agree with the full core")]
    if filtered is not None:
        checks.append(("survivors", filtered["survivors"] > 0,
                       "no current-physiology candidate meets FD-LAC-01..06 jointly"))
    if statistics is not None and filtered and filtered["survivors"]:
        evaluated = all(statistics["fd04_status"][c].get(fd.PASS, 0) + statistics["fd04_status"][c].get(
            fd.ALREADY_NORMALIZED, 0) > 0 and statistics["fd05_status"][c].get(fd.PASS, 0) > 0 for c in CASES)
        checks.append(("definitive_management_evaluated", evaluated,
                       "FD-LAC-04 / 05 are met only as NOT_EVALUABLE among the survivors"))
    blockers = [why for _, passed, why in checks if not passed]
    return {"verdict": SATISFIED if not blockers and filtered is not None else
            f"{NOT_READY} — {blockers[0] if blockers else 'the filter did not run'}",
            "checks": {name: passed for name, passed, _ in checks}, "blockers": blockers, "rule": VERDICT_RULE,
            "next_domain": NEXT_DOMAIN}


def region_record(filtered: dict) -> dict:
    units = [[i, index, list(r), list(d)] for i, index, r, d in filtered["units"]]
    digest = hashlib.sha256(json.dumps(units, separators=(",", ":")).encode("utf-8")).hexdigest()
    return {"status": REGION_STATUS, "units": len(units), "candidates": filtered["survivors"],
            "candidates_with_reserve_multiplicity": filtered["survivors_with_reserve_multiplicity"],
            "digest": digest, "inline": units if len(units) <= INLINE_UNITS else None,
            "format": "[P1 set, lactate-side index, [P3 sets], [crystalloid points]]"}


def design() -> dict:
    return {"faculty": FACULTY, "readiness": READINESS, "tau": TAU_STATUS, "blood": blood_design(),
            "lactate_side": {"points": kinetic_points(), "levels": list(LEVELS),
                             "arrival_pairs": [list(p) for p in ARRIVAL_PAIRS], "size": len(LAMBDAS),
                             "demand": DEMAND_RULE, "intrinsic": INTRINSIC_RULE},
            "rules": CURRENT_RULES, "settings": SETTINGS, "factorization": FACTORIZATION,
            "filter_order": [[s, list(n)] for s, n in FILTER_ORDER], "cost": COST_RATIONALE,
            "rejections": REJECTION_RULE, "validation": VALIDATION_RULE, "identifiability": IDENTIFIABILITY_RULE,
            "representatives": REPRESENTATIVE_RULE, "flags": FLAG_RULES, "legacy": LEGACY_RULE,
            "verdict": VERDICT_RULE, "region": REGION_STATUS, "policy": POLICY}


def freeze_digest() -> str:
    records = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in
               (("P2I-2AA", P2I2AA_RECORD), ("P2I-2Z", tc.P2I2Z_RECORD), ("P2I-2V-R", be.P2I2VR_RECORD))}
    text = json.dumps({"revision": REVISION, "records": records, "design": design(), "lambdas": LAMBDAS,
                       "bits": {s: [list(b) for b in v] for s, v in BITS.items()}, "fd_lac": fd.definitions_digest(),
                       "thresholds": list(FD04_THRESHOLDS), "histogram": HISTOGRAM_STEP, "inline": INLINE_UNITS,
                       "tolerance": TOLERANCE, "canonical": CANONICAL, "sources": bf.freeze_sources()},
                      sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run(progress=None, map_=map) -> dict:
    say = progress or (lambda *_: None)
    with P2FGuard(), LegacyLock():
        record = record_p2i2aa()
        ready = readiness(record)
        support = crystalloid_support(record)
        arrivals = arrival_table()
        rows = rb.Rows()
        say("blood source")
        source = blood_source(rows, map_, say)
        keys = source_keys_certified(source, record)
        say("factorization")
        validation = validate(source, support, arrivals, map_)
        out = {"freeze_digest": freeze_digest(), "decided": DECIDED, "revision": REVISION, "policy": POLICY,
               "records": {"P2I-2AA": record["freeze_digest"]}, "faculty": FACULTY, "readiness": ready,
               "crystalloid_support": support, "l3": tc.l3_audit(),
               "lactate_side": {"points": kinetic_points(), "size": len(LAMBDAS), "demand": DEMAND_RULE,
                                "intrinsic": INTRINSIC_RULE, "arrivals": arrivals},
               "source": {k: v for k, v in source.items() if k != "children"}, "source_keys": keys,
               "components": components(source, support),
               "validation": {k: v for k, v in validation.items() if k != "sample"},
               "validation_sample": validation["sample"], "structural_products": structural_products(),
               "rows_computed": rows.computed, "contradictions": be.contradictions(rows.table)}
        if not (ready["verdict"] == READINESS and keys["certified"] and validation["agree"]):
            out["verdict"] = verdict(ready, source, keys, validation, None, None)
            return out
        say("filter")
        filtered = filter_(source, support, arrivals, map_, say)
        statistics, picks, reviewed = None, {}, {}
        if filtered["units"]:
            say("survivors")
            statistics = survivor_statistics(source, support, arrivals, filtered, map_)
            picks = representatives(source, support, filtered, statistics.pop("_l60"))
            say("review")
            reviewed = review(source, support, picks)
        out.update({"filter": {k: v for k, v in filtered.items() if k not in ("store", "units")},
                    "region": region_record(filtered), "statistics": statistics,
                    "identifiability": identifiability(source, support, filtered), "representatives": reviewed,
                    "verdict": verdict(ready, source, keys, validation, filtered, statistics)})
    out["legacy_reference"] = legacy_reference(reviewed)
    out["efficiency"] = {"haemodynamic_trajectories": filtered["simulated"],
                         "naive_core_runs": filtered["candidates"] * len(SCENARIOS) * len(CASES),
                         "factorized_core_runs": sum(filtered["simulated"].values()),
                         "validation_full_runs": validation["runs"], "blood_rows": rows.computed,
                         "survivor_units": len(filtered["units"])}
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
        (out / "lactate_rebuild.json").write_text(json.dumps(result, indent=1, sort_keys=True, default=str),
                                                  encoding="utf-8")
        print(out / "lactate_rebuild.json")
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
