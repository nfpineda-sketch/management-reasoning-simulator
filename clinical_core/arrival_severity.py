"""Phase 2 shadow core, P2I-2AI: case-specific arrival-severity initialization and recertification.

    python -m clinical_core.arrival_severity --digest
    python -m clinical_core.arrival_severity --design
    python -m clinical_core.arrival_severity --run --out <directory outside the repository> [--workers N]

Shadow only and offline. Faculty decisions (2026-10-29), recorded in FACULTY:

1. The arrival oxygen debt D0 and the arrival delivery ratio are patient-state initial conditions: each case may sit
   at its own EXISTING arrival pair (the five P2F pairs the current physiology was certified on). No new value, no
   interpolation.
2. The non-HR perfusion phenotype makes 57m more severe than 72f at arrival. ORDERING_RULE (ordinal, frozen before any
   count): D0_57m >= D0_72f, delivery_57m <= delivery_72f, at least one strict. The pairing is built from the case
   bands and this rule only: no HR, tolerance, gain, ceiling or legacy value is read (severity_reads()).
3. The D / lactate region is recertified on the current physiology with P2I-2AD's own machinery (factorized
   haemodynamics, D and lactate post-processed, FD-LAC-01..06, L3 adequacy through 120, demand 0.9 / 1.0 / 1.1). Each
   case is filtered with its own pair; a case-pair candidate survives when both cases pass. The tied pairs reproduce
   P2I-2AD's committed region exactly (EQUIVALENCE), else the run stops.
4. HR: intrinsic 60 / 80 / 100 explored per case (patient-specific, never identified or approved); acute and debt
   gains common (P2I-2AF's five points each), total sinus ceilings 150 / 175 / 200 common, pressure DEFERRED
   (P2I-2AG's primary mode), arrival tolerance +-5 bpm unchanged. Only LACTATE_COMPATIBLE case pairs enter.

Nothing is fitted, selected or approved; the legacy HR and lactate are never read.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import inspect
import json
from dataclasses import replace
from pathlib import Path

from . import calibration, derived, gi_reference
from . import blood_fluid_calibration as bf
from . import faculty_constraints as fd
from . import hr_primary as hp
from . import hr_shock as hk
from . import hr_structure as hs
from . import lactate_adequacy as la
from . import lactate_closure as lc
from . import lactate_rebuild as lr

DECIDED = "2026-10-29"
REVISION = "P2I-2AI"
ROOT = lc.ROOT
CASES = lc.CASES
C57, C72 = CASES
L1, L2, L3 = lc.L1, lc.L2, lc.L3
RESERVE = lc.RESERVE
LAMBDAS = lc.LAMBDAS
INDEX = {point: index for index, point in enumerate(LAMBDAS)}
PAIRS = tuple(tuple(pair) for pair in lr.ARRIVAL_PAIRS)
BASES = tuple(dict.fromkeys(point[:5] for point in LAMBDAS))
ANALYTIC_REJECTION, SIMULATION_REJECTION = lc.ANALYTIC_REJECTION, lc.SIMULATION_REJECTION
P2I2AD_RECORD = ROOT / "docs" / "revision" / "P2I2AD_lactate_closure.json"
P2I2AD_DIGEST = hs.P2I2AD_DIGEST
P2I2AD_REGION_DIGEST = "9ddbcf24e6d2a80c404036895fc0ce1512b6e124e7243db771d0bad6dcc8d2a7"
P2I2AG_RECORD = ROOT / "docs" / "revision" / "P2I2AG_hr_primary.json"
P2I2AG_DIGEST = "94c94584009449c43b15bd3bb8673bccbead3db86fcf71fa10f508b674ccf763"

FACULTY = {
    "decided": DECIDED,
    "severity": "arrival D0 and arrival delivery are patient-state initial conditions: each case may take its own "
                "EXISTING certified arrival pair; no new D0 or delivery value, no interpolation, no case-specific "
                "sympathetic gain",
    "ordering": "the non-HR perfusion phenotype (57m: BP 88/54, lactate 4.4, CRT 5 s, IVC 0.9 cm near-complete "
                "collapse, near-obliterated LV, HCO3 17.3; 72f: 98/62, 3.4, 4 s, 1.1 cm > 50 %, hyperdynamic LV, "
                "19.8) makes 57m more severe; the slightly lower Hb of 72f does not reverse it; no exact severity is "
                "derived from a single observation",
    "no_hr": "the arrival HR (124 / 112) never chooses D0, delivery, a level or a pair; the pairing is frozen before any "
             "lactate or HR count",
    "recertification": "D / lactate recertified on the current physiology with P2I-2AD's machinery; D and D -> lactate "
                       "semantics, FD-LAC constraints, blood / fluid ranges, demand values, rho handling and L3 "
                       "adequacy unchanged; only the arrival case-pair assignment changes",
    "intrinsic": "intrinsic HR is patient-specific: 60 / 80 / 100 per case, candidate uncertainty, never identified "
                 "or approved, no extra value",
    "common": "acute and debt gains, the smooth saturation law and the total sinus ceilings 150 / 175 / 200 stay "
              "common; pressure stays DEFERRED (diagnostic only); arrival tolerance +-5 bpm",
    "scope": "shadow only; no HR latent selection, no trajectory envelope, no pressure / RR calibration, collapse, "
             "migration or runtime integration",
}

# 1. The existing arrival pairs and the faculty ordering (P2I-2AI-1, -2, -3) ---------------------------------------------

PAIR_LABELS = {("lower", "upper"): "none: no debt, full delivery", ("midpoint", "midpoint"): "middle",
               ("upper", "lower"): "severe: debt and low delivery", ("lower", "lower"): "mixed: no debt, low delivery",
               ("upper", "upper"): "mixed: debt, full delivery"}
PAIR_PROVENANCE = ("blood_fluid_readiness.ARRIVAL_PAIRS ('the P2F arrival (debt, delivery) pairs, unchanged "
                   "(calibration.gi_candidates)'), carried by lactate_rebuild / lactate_closure (P2I-2AB..AD); values "
                   "from gi_reference.arrival_debt_band and delivery_ratio_band; delivery re-anchored by the extraction "
                   "reserve 2.5 as the core builds the arrival")
ADMISSIBLE = "CLINICALLY_ADMISSIBLE"
ORDERING_RULE = (
    "A (57m pair, 72f pair) of the existing support is CLINICALLY_ADMISSIBLE when D0(57m) >= D0(72f) AND "
    "delivery(57m) <= delivery(72f) AND at least one inequality is strict (identical pairs are not a case-specific "
    "assignment). Ordinal only: it identifies no D0 and no delivery. Otherwise ANALYTIC_REJECTION with every reason: "
    "D57_BELOW_D72, DELIVERY57_ABOVE_DELIVERY72, IDENTICAL.")


def _level(band, level: str) -> float:
    return {"lower": band.lower, "midpoint": band.midpoint, "upper": band.upper}[level]


def pair_values(case: str, pair: tuple) -> dict:
    """The arrival values of one existing pair for one case, from the case bands only."""
    debt, delivery = pair
    bands = gi_reference.case_bands(case)
    ratio = _level(bands["arrival_delivery_ratio"], delivery)
    reanchored = ratio / RESERVE
    return {"D0": _level(bands["arrival_oxygen_debt"], debt), "delivery": ratio, "delivery_reanchored": reanchored,
            "x0": derived.effective_oxygen_deficit(1.0, reanchored, RESERVE)}


def case_pairs() -> list[dict]:
    """Every (57m pair, 72f pair) of the existing support with the frozen ordinal verdict (no physiology run)."""
    out = []
    for first in PAIRS:
        for second in PAIRS:
            a, b = pair_values(C57, first), pair_values(C72, second)
            reasons = []
            if a["D0"] < b["D0"]:
                reasons.append("D57_BELOW_D72")
            if a["delivery"] > b["delivery"]:
                reasons.append("DELIVERY57_ABOVE_DELIVERY72")
            if a["D0"] == b["D0"] and a["delivery"] == b["delivery"]:
                reasons.append("IDENTICAL")
            out.append({"57m": first, "72f": second, "reasons": reasons,
                        "status": ADMISSIBLE if not reasons else ANALYTIC_REJECTION})
    return out


def admissible() -> list[tuple]:
    return [(item["57m"], item["72f"]) for item in case_pairs() if item["status"] == ADMISSIBLE]


#: Names the severity constructor must never read (P2I-2AI-3).
HR_NAMES = ("hr", "pulse", "sympathetic", "ceiling", "tolerance", "authored", "legacy", "intrinsic", "acute", "gain",
            "hp", "hk", "hs", "heart")


def severity_reads() -> set:
    """Every name the severity constructor (pair_values, case_pairs, admissible, _level) reads."""
    names = set()
    for function in (pair_values, case_pairs, admissible, _level):
        for node in ast.walk(ast.parse(inspect.getsource(function))):
            if isinstance(node, ast.Name):
                names.add(node.id)
            elif isinstance(node, ast.Attribute):
                names.add(node.attr)
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                names.add(node.value)
    return names


def inventory(region_units: list) -> list[dict]:
    """P2I-2AI-1: the existing pairs, their values per case, label, provenance and P2I-2AD tied survivors."""
    tied = {pair: 0 for pair in PAIRS}
    for _, index, r, d in region_units:
        tied[tuple(LAMBDAS[index][5:])] += len(r) * len(d)
    out = []
    for pair in PAIRS:
        values = {case: pair_values(case, pair) for case in CASES}
        out.append({"pair": list(pair), "label": PAIR_LABELS[pair], **values[C57],
                    "same_values_both_cases": values[C57] == values[C72], "provenance": PAIR_PROVENANCE,
                    "p2i2ad_tied_survivors": tied[pair], "valid_after_p2i2ad": tied[pair] > 0})
    return out


# 2. The per-case filter (P2I-2AI-4, -5): P2I-2AD's units, each case kept apart ----------------------------------------

EQUIVALENCE = ("Each case is filtered at every lactate-side point with P2I-2AD's own series and checks (L1: FD-LAC-02/03, "
               "FD-LAC-01, FD-LAC-06; L3: adequacy INADEQUATE / LOST, FD-LAC-04 FAIL, FD-LAC-05 FAIL, FD-LAC-06 active "
               "and residual; L2: FD-LAC-06; a stopped or uncontrolled run fails), L1 then L3 then L2, per demand factor. "
               "A case-pair candidate (P3 set, crystalloid point, kinetics, excess, 57m pair, 72f pair) survives when "
               "both cases pass every unit it projects to. The tied pairs (the same pair for both cases) must reproduce "
               "P2I-2AD's committed region exactly at demand 1.0 (its region digest) and its survivor counts at 0.9 and "
               "1.1, else the run stops.")


def _l1_case(task: tuple) -> tuple:
    i, haemodynamic, arrivals, factor = task
    out = {}
    for case in CASES:
        passing = {}
        if haemodynamic[case]["stop"] is None:
            for index, lactate, debt, context in lc._series(haemodynamic[case], arrivals[case], range(len(LAMBDAS)),
                                                            factor, {}):
                if (fd.fd_lac_envelope(context.trajectory(lactate, debt), case, lc.SETTINGS)["passes"]
                        and lr.fd_lac_01(lactate, context)["passes"] and lc.fd_lac_06_run(lactate, context)["passes"]):
                    passing[index] = lactate[60]
        out[case] = passing
    return i, out


def _l3_case(task: tuple) -> tuple:
    q, haemodynamic, arrivals, wanted, factor = task
    out = {}
    for case in CASES:
        passing, notes = set(), {}
        own = haemodynamic[case]
        if own["stop"] is None and own["controlled_at"] is not None:
            for index, lactate, debt, context in lc._series(own, arrivals[case], wanted[case], factor, {}):
                status = context.adequacy["status"]
                response, residual = lc.fd_lac_04_05(lactate, debt, context, LAMBDAS[index], case)
                sixth = lc.fd_lac_06_run(lactate, context)
                if (status in (lc.L3_INADEQUATE, lc.L3_LOST) or response["status"] == fd.FAIL
                        or residual["status"] == fd.FAIL or sixth["active"] or sixth["residual"]):
                    continue
                passing.add(index)
                flags = (response["status"] in (fd.PASS, fd.ALREADY_NORMALIZED) and residual["status"] == fd.PASS,
                         response["trigger"] == context.adequacy["onset"],
                         not lc.debt_falls_outside_adequate_minutes(debt, context), status == lc.L3_ADEQUATE)
                if not all(flags):
                    notes[index] = flags
        out[case] = (passing, notes)
    return q, out


def _l2_case(task: tuple) -> tuple:
    unit, haemodynamic, arrivals, wanted, factor = task
    out = {}
    for case in CASES:
        passing = set()
        if haemodynamic[case]["stop"] is None:
            for index, lactate, _, context in lc._series(haemodynamic[case], arrivals[case], wanted[case], factor, {}):
                if lc.fd_lac_06_run(lactate, context)["passes"]:
                    passing.add(index)
        out[case] = passing
    return unit, out


def per_case_filter(source: dict, support: list, arrivals: dict, tasks: dict, store: dict, factor: float,
                    map_=map) -> dict:
    p1, children = source["p1"], source["children"]

    def trajectories(scenario, unit):
        return {case: store[tasks[(scenario, unit, case)]] for case in CASES}

    l1 = {case: {} for case in CASES}
    l60 = {case: {} for case in CASES}
    for i, out in map_(_l1_case, [(i, trajectories(L1, i), arrivals, factor) for i in range(len(p1))]):
        for case in CASES:
            l1[case][i] = set(out[case])
            l60[case].update({(i, index): value for index, value in out[case].items()})
    l3 = {case: {} for case in CASES}
    notes = {case: {} for case in CASES}
    work = [(q, trajectories(L3, q), arrivals, {case: sorted(l1[case][i]) for case in CASES}, factor)
            for i in range(len(p1)) for q in children[i]]
    for q, out in map_(_l3_case, work):
        for case in CASES:
            l3[case][q], notes[case][q] = out[case]
    wanted = {case: {i: sorted(index for index in l1[case][i] if any(index in l3[case][q] for q in children[i]))
                     for i in range(len(p1))} for case in CASES}
    l2 = {case: {} for case in CASES}
    work = [((i, d), trajectories(L2, (i, d)), arrivals, {case: wanted[case][i] for case in CASES}, factor)
            for i in range(len(p1)) for d in range(len(support)) if any(wanted[case][i] for case in CASES)]
    for unit, out in map_(_l2_case, work):
        for case in CASES:
            l2[case][unit] = out[case]
    evaluated = {"L1": len(p1) * len(LAMBDAS) * len(CASES),
                 "L3": sum(len(l1[case][i]) * len(children[i]) for case in CASES for i in range(len(p1))),
                 "L2": sum(len(wanted[case][i]) * len(support) for case in CASES for i in range(len(p1)))}
    return {"factor": factor, "l1": l1, "l3": l3, "l2": l2, "notes": notes, "l60": l60, "evaluated": evaluated}


def combine(per: dict, source: dict, n_support: int, pair_57: tuple, pair_72: tuple) -> list:
    """The surviving units of one case pair: (P1 set, 57m lambda, 72f lambda, [P3 sets], [crystalloid points])."""
    units = []
    for i, members in enumerate(source["children"]):
        for base in BASES:
            a, b = INDEX[(*base, *pair_57)], INDEX[(*base, *pair_72)]
            if a not in per["l1"][C57][i] or b not in per["l1"][C72][i]:
                continue
            r = tuple(q for q in members if a in per["l3"][C57][q] and b in per["l3"][C72][q])
            if not r:
                continue
            d = tuple(k for k in range(n_support)
                      if a in per["l2"][C57].get((i, k), ()) and b in per["l2"][C72].get((i, k), ()))
            if d:
                units.append((i, a, b, r, d))
    return sorted(units)


def region_digest(units: list) -> str:
    """P2I-2AD's region digest, over tied units (one lambda for both cases)."""
    tied = sorted((i, a, tuple(r), tuple(d)) for i, a, b, r, d in units if a == b)
    rows = [[i, index, list(r), list(d)] for i, index, r, d in tied]
    return hashlib.sha256(json.dumps(rows, separators=(",", ":")).encode("utf-8")).hexdigest()


def _survivors(units: list) -> int:
    return sum(len(r) * len(d) for *_, r, d in units)


def _ids(units: list) -> set:
    return {(q, k, a, b) for _, a, b, r, d in units for q in r for k in d}


def statistics(per: dict, units: list) -> dict:
    """Per case-pair survivors: FD-LAC-04 / 05 evaluated in both cases, T* = adequacy onset, D coherent, adequate."""
    counts = {"evaluated_both": 0, "trigger_is_onset": 0, "debt_coherent": 0, "adequate_through_120": 0}
    for _, a, b, r, d in units:
        for q in r:
            flags = [per["notes"][C57][q].get(a, (True,) * 4), per["notes"][C72][q].get(b, (True,) * 4)]
            for position, name in enumerate(counts):
                counts[name] += len(d) * all(item[position] for item in flags)
    return counts


def representatives(per: dict, source: dict, units: list) -> dict:
    """P2I-2AD's rule on a case pair: ordered by 57m L1 lactate at 60, then 72f, then P1 set, lambdas, P3 set and
    crystalloid point in source order; LOW = first, MID = floor(n / 2)-th, HIGH = last."""
    if not units:
        return {}
    ordered = sorted(units, key=lambda u: (per["l60"][C57][(u[0], u[1])], per["l60"][C72][(u[0], u[2])], u[0], u[1],
                                           u[2]))
    total = _survivors(units)
    out = {}
    for tag, rank in (("LOW", 0), ("MID", total // 2), ("HIGH", total - 1)):
        cumulative = 0
        for i, a, b, r, d in ordered:
            size = len(r) * len(d)
            if rank < cumulative + size:
                offset = rank - cumulative
                out[tag] = {"p1": i, "lambda_57m": a, "lambda_72f": b, "p3": r[offset // len(d)],
                            "support": d[offset % len(d)], "rank": rank}
                break
            cumulative += size
    return out


def review(source: dict, support: list, arrivals: dict, tasks: dict, store: dict, picks: dict) -> dict:
    """Each representative re-run by the full core (each case with its own pair, L1 and L3), with P2I-2AD's flags and
    D checks, and compared with its factorized reading."""
    out = {}
    for tag, pick in picks.items():
        entry = source["p3"][pick["p3"]]
        item = {"pick": pick, "runs": {}}
        for case, index in ((C57, pick["lambda_57m"]), (C72, pick["lambda_72f"])):
            point = LAMBDAS[index]
            for scenario in (L1, L3):
                full = lc.full_run(entry, case, scenario, point)
                unit = entry["p1"] if scenario == L1 else pick["p3"]
                lactate, debt, _ = lc.factorized(store[tasks[(scenario, unit, case)]], arrivals[case], point)
                series = {"lactate": full["lactate"], "deficit": full["deficit"], "D": full["D"], "stop": full["stop"],
                          "output": full["output"], "hb": [state.hb for state, _ in full["views"]]}
                item["runs"][f"{case}|{scenario}"] = {
                    "lambda": lc.lambda_label(index), "flags": lr._flags(series, scenario),
                    "debt": lc.debt_checks(full), "rerun_equals_factorized": lactate == full["lactate"] and debt == full["D"],
                    "L60": full["lactate"][60] if len(full["lactate"]) > 60 else None,
                    "L120": full["lactate"][-1], "D_end": full["D"][-1]}
        out[tag] = item
    return out


LACTATE_COMPATIBLE, LACTATE_INCOMPATIBLE = "LACTATE_COMPATIBLE", "LACTATE_INCOMPATIBLE"
COMPATIBILITY_RULE = (
    "A clinically admissible case pair is LACTATE_COMPATIBLE when P2I-2AD's readiness checks hold on its own region at "
    "demand 1.0: at least one survivor; every survivor L3_RESUSCITATION_ADEQUATE_THROUGH_120, FD-LAC-04 PASS or "
    "ALREADY_NORMALIZED and FD-LAC-05 PASS (evaluated) in both cases, its FD-LAC-04 T* its adequacy onset and its D "
    "falling only across deficit-free minutes; its LOW / MID / HIGH representatives patient-like (no "
    "WORSENING_CRITICAL_WITH_LARGE_LACTATE_FALL, INSTANT_NORMALIZATION or INCOMPATIBLE_WITH_SURVIVAL flag, no D fall "
    "outside adequate minutes, no critical minute below the arrival D) and each full rerun equal to its factorized "
    "reading. Otherwise LACTATE_INCOMPATIBLE with the first failing check. Robustness across demand is reported, never "
    "a filter (as P2I-2AD). No pair is approved.")


def classify(survivors: int, stats: dict, reviewed: dict) -> tuple:
    runs = [run_ for item in reviewed.values() for run_ in item["runs"].values()]
    checks = [
        ("survivors", survivors > 0),
        ("adequate_through_120", stats["adequate_through_120"] == survivors),
        ("fd04_05_evaluated", stats["evaluated_both"] == survivors),
        ("trigger_is_onset", stats["trigger_is_onset"] == survivors),
        ("debt_coherent", stats["debt_coherent"] == survivors),
        ("patient_like", bool(runs) and all(
            not any(r["flags"][n] for n in ("WORSENING_CRITICAL_WITH_LARGE_LACTATE_FALL", "INSTANT_NORMALIZATION",
                                            "INCOMPATIBLE_WITH_SURVIVAL"))
            and not r["debt"]["falls_outside_adequate_minutes"] and r["debt"]["critical_minutes_below_arrival"] == 0
            for r in runs)),
        ("reruns_exact", bool(runs) and all(r["rerun_equals_factorized"] for r in runs)),
    ]
    failed = [name for name, passed in checks if not passed]
    return (LACTATE_COMPATIBLE if not failed else LACTATE_INCOMPATIBLE), {name: passed for name, passed in checks}, (
        failed[0] if failed else None)


# 3. The arrival HR surface (P2I-2AI-8, -9, -10) ---------------------------------------------------------------------

HR_RULE = (
    "Arrival HR is analytic (derived.heart_rate_decomposition at the case's own arrival pair, P2I-2AG's primary profile: "
    "pressure 0): 57m intrinsic 60 / 80 / 100 x 72f intrinsic 60 / 80 / 100 x the five common acute gains x the five "
    "common debt gains x the common ceilings 150 / 175 / 200, on the LACTATE_COMPATIBLE case pairs only. JOINT when "
    "|HR57 - 124| <= 5 and |HR72 - 112| <= 5. No best candidate.")
COMPARISON_RULE = (
    "A: the same pair for both cases (the five tied pairs, all valid in P2I-2AD) and the same intrinsic level; B: the "
    "LACTATE_COMPATIBLE case pairs, the same intrinsic level; C: the tied pairs, intrinsic per case; D: the "
    "LACTATE_COMPATIBLE case pairs, intrinsic per case. Gains and ceilings common in all four; analytic on the same "
    "arrival decompositions. A change restores compatibility when its joint count exceeds A's; BOTH_CONTRIBUTE is "
    "confirmed when case severity (B) and patient-specific intrinsic (C) each restore it.")


def arrival_hr_table() -> dict:
    """Every arrival decomposition the surface can read: case x existing pair x intrinsic x gains x ceiling."""
    table = {}
    for case in CASES:
        for pair in PAIRS:
            for level in hp.INTRINSIC:
                anchors = hk.analysis_anchors(case, level, *pair)
                hp.require_explicit_intrinsic(anchors)
                for acute in hp.ACUTE:
                    for gain in hp.DEBT:
                        for ceiling in hp.CEILINGS:
                            split = derived.heart_rate_decomposition(anchors, hp.primary_profile(acute, gain, ceiling))
                            table[(case, pair, level, acute, gain, ceiling)] = {
                                "predicted": split["predicted_arrival_hr"], "x0": split["acute_deficit_signal"],
                                "D0": anchors.arrival_oxygen_debt, "intrinsic": split["intrinsic_sinus_rate"],
                                "acute_unconstrained_bpm": split["acute_unconstrained_bpm"],
                                "debt_unconstrained_bpm": split["debt_unconstrained_bpm"],
                                "saturated_bpm": split["saturated_bpm"]}
    return table


def _joint(table: dict, combos: list, intrinsic_pairs: list) -> list:
    out = []
    for pair_57, pair_72 in combos:
        for level_57, level_72 in intrinsic_pairs:
            for acute in hp.ACUTE:
                for gain in hp.DEBT:
                    for ceiling in hp.CEILINGS:
                        first = table[(C57, pair_57, level_57, acute, gain, ceiling)]["predicted"]
                        second = table[(C72, pair_72, level_72, acute, gain, ceiling)]["predicted"]
                        if hp.compatible(C57, first) and hp.compatible(C72, second):
                            out.append({"pair_57m": list(pair_57), "pair_72f": list(pair_72),
                                        "intrinsic": [level_57, level_72], "acute": acute, "debt": gain,
                                        "ceiling": ceiling, "predicted": [first, second],
                                        "mismatch": [first - hp.AUTHORED[C57], second - hp.AUTHORED[C72]]})
    return out


def hr_surface(table: dict, compatible: list) -> dict:
    per_case = [(a, b) for a in hp.INTRINSIC for b in hp.INTRINSIC]
    joint = _joint(table, compatible, per_case)
    rows = {(case, pair, level, acute, gain, ceiling) for pair_57, pair_72 in compatible
            for case, pair in ((C57, pair_57), (C72, pair_72)) for level in hp.INTRINSIC for acute in hp.ACUTE
            for gain in hp.DEBT for ceiling in hp.CEILINGS}
    candidates = [(table[(C57, pair_57, a, acute, gain, ceiling)]["predicted"],
                   table[(C72, pair_72, b, acute, gain, ceiling)]["predicted"])
                  for pair_57, pair_72 in compatible for a, b in per_case for acute in hp.ACUTE for gain in hp.DEBT
                  for ceiling in hp.CEILINGS]
    support = {
        "intrinsic_pairs": {f"{a}|{b}": sum(1 for s in joint if s["intrinsic"] == [a, b]) for a, b in per_case},
        "acute": {f"{v!r}": sum(1 for s in joint if s["acute"] == v) for v in hp.ACUTE},
        "debt": {f"{v!r}": sum(1 for s in joint if s["debt"] == v) for v in hp.DEBT},
        "ceiling": {f"{v:g}": sum(1 for s in joint if s["ceiling"] == v) for v in hp.CEILINGS},
        "case_pairs": {f"{'/'.join(s['pair_57m'])}|{'/'.join(s['pair_72f'])}": 0 for s in joint}}
    for s in joint:
        support["case_pairs"][f"{'/'.join(s['pair_57m'])}|{'/'.join(s['pair_72f'])}"] += 1
    distinct_predictions = len({(round(s["predicted"][0], 9), round(s["predicted"][1], 9)) for s in joint})
    return {"rule": HR_RULE, "joint_candidates": len(candidates), "decompositions": len(rows),
            "compatible_decompositions": {case: sum(1 for r in rows if r[0] == case
                                                    and hp.compatible(case, table[r]["predicted"])) for case in CASES},
            "compatible_57m": sum(1 for first, _ in candidates if hp.compatible(C57, first)),
            "compatible_72f": sum(1 for _, second in candidates if hp.compatible(C72, second)),
            "joint": len(joint), "distinct_case_pairs": len(support["case_pairs"]),
            "distinct_predictions": distinct_predictions, "support": support, "survivors": joint}


def comparison(table: dict, compatible: list) -> dict:
    tied = [(pair, pair) for pair in PAIRS]
    common = [(level, level) for level in hp.INTRINSIC]
    per_case = [(a, b) for a in hp.INTRINSIC for b in hp.INTRINSIC]
    out = {}
    for name, combos, levels in (("A", tied, common), ("B", compatible, common), ("C", tied, per_case),
                                 ("D", compatible, per_case)):
        joint = _joint(table, combos, levels)
        out[name] = {"joint": len(joint), "of": len(combos) * len(levels) * len(hp.ACUTE) * len(hp.DEBT)
                     * len(hp.CEILINGS),
                     "distinct_predictions": len({(round(s["predicted"][0], 9), round(s["predicted"][1], 9))
                                                  for s in joint})}
    out["rule"] = COMPARISON_RULE
    out["case_severity_restores"] = out["B"]["joint"] > out["A"]["joint"]
    out["case_intrinsic_restores"] = out["C"]["joint"] > out["A"]["joint"]
    out["both_contribute_confirmed"] = out["case_severity_restores"] and out["case_intrinsic_restores"]
    return out


# 4. Trajectory distributions for the joint survivors (P2I-2AI-11, no envelope) ----------------------------------------

TRAJECTORY_RULE = (
    "For each LACTATE_COMPATIBLE case pair with joint arrival survivors: its LOW / MID / HIGH lactate representatives, "
    "each case run once by the full core with its own pair (L1, L2 at the representative's crystalloid point, L3), and "
    "the primary HR (pressure 0) post-processed for every joint survivor of that pair; distributions (min / median / "
    "max) per case over representatives x survivors. One survivor per representative and case is re-run by the full "
    "core at L3 (exact HR, else the run stops). No envelope filters anything.")
READINGS = {"H1_untreated": (L1, (0, 30, 60, 120)), "H2_crystalloid": (L2, (0, 15, 30, 120)),
            "H3_prbc": (L3, (0, 30, 60)), "H4_definitive": (L3, (60, 90, 120))}


def _spread(values: list):
    values = sorted(v for v in values if v is not None)
    if not values:
        return None
    return {"min": values[0], "median": values[len(values) // 2], "max": values[-1], "n": len(values)}


def trajectories(source: dict, support: list, compatible_regions: dict, joint: list) -> dict:
    out, checks = {}, []
    for key, item in compatible_regions.items():
        survivors = [s for s in joint if f"{'/'.join(s['pair_57m'])}|{'/'.join(s['pair_72f'])}" == key]
        if not survivors:
            continue
        readings = {case: {} for case in CASES}
        for tag, pick in item["picks"].items():
            entry = source["p3"][pick["p3"]]
            for case, index, position in ((C57, pick["lambda_57m"], 0), (C72, pick["lambda_72f"], 1)):
                inputs = {"entry": entry, "bag": support[pick["support"]]["bag"], "point": LAMBDAS[index]}
                runs = {scenario: hk.full_run(inputs, case, scenario) for scenario in (L1, L2, L3)}
                for n, s in enumerate(survivors):
                    rate = hs.intrinsic_levels(case)[s["intrinsic"][position]]
                    series = {sc: hp.primary_series(runs[sc], rate, s["acute"], s["debt"], s["ceiling"])
                              for sc in runs}
                    for name, (scenario, minutes) in READINGS.items():
                        for minute in minutes:
                            value = series[scenario][minute]["hr"] if minute < len(series[scenario]) else None
                            readings[case].setdefault(f"{name}@{minute}", []).append(value)
                    l1, l3 = series[L1], series[L3]
                    readings[case].setdefault("H1_change_0_120", []).append(
                        l1[120]["hr"] - l1[0]["hr"] if len(l1) > 120 else None)
                    readings[case].setdefault("H1_max", []).append(max(p["hr"] for p in l1 if p["hr"] is not None))
                    readings[case].setdefault("H4_change_60_120", []).append(
                        l3[120]["hr"] - l3[60]["hr"] if len(l3) > 120 else None)
                    readings[case].setdefault("delayed_tachycardia_120", []).append(
                        l3[120]["hr"] - rate if len(l3) > 120 else None)
                    peak = max(p["hr"] for sc in series for p in series[sc] if p["hr"] is not None)
                    readings[case].setdefault("max_saturated_hr", []).append(peak)
                    readings[case].setdefault("distance_from_ceiling", []).append(s["ceiling"] - peak)
                    if n == 0:
                        changes = {"acute_deficit_to_sympathetic_gain": s["acute"], "debt_to_sympathetic_gain": s["debt"],
                                   "sinus_rate_ceiling_bpm": s["ceiling"], **hp.PRIMARY_HR_CALIBRATION}
                        full = hk.full_run(inputs, case, L3, s["intrinsic"][position], changes)
                        checks.append([p["hr"] for p in series[L3]] == [r["hr"] for r in full["rows"]])
        out[key] = {"survivors": len(survivors), "readings": {case: {name: _spread(values)
                                                                     for name, values in readings[case].items()}
                                                              for case in CASES}}
    return {"rule": TRAJECTORY_RULE, "by_case_pair": out, "validation_reruns": len(checks), "exact": all(checks),
            "full_runs": len(checks) + sum(3 * len(CASES) * 3 for _ in out)}


# 5. Verdict, design, freeze ---------------------------------------------------------------------------------------

READY, NOT_READY = hp.READY, hp.NOT_READY
UNRESOLVED = "ARRIVAL_HR_MODEL_REMAINS_STRUCTURALLY_UNRESOLVED"
VERDICT_RULE = (
    f"{READY} when: (1) the arrival severity is case-specific without HR (severity_reads() names no HR quantity) and at "
    "least one case pair is admissible; (2) the D / lactate recertification passes: the factorization agrees with the "
    "full core, the tied pairs reproduce P2I-2AD exactly, and at least one admissible pair is LACTATE_COMPATIBLE; (3) "
    "the intrinsic rate is declared per case (explicit; no fallback); (4) the gains are common (by construction); (5) at "
    f"least one jointly arrival-compatible candidate exists (else {UNRESOLVED}); (6) the pressure contribution is 0 in "
    "the primary profile; (7) no D / lactate / RR regression (tied equivalence, the core unchanged); (8) no structural "
    "contradiction (the HR reconstruction equals the full core on the representatives). The suite criterion is the "
    f"final certification's. Otherwise {NOT_READY} with the first blocker. Nothing is approved.")
POLICY = ("Shadow only. P2I-2AB's current source space and P2I-2AD's machinery (its committed records), never the P2F "
          "historical region (P2FGuard); legacy never read (LegacyLock). Existing arrival pairs only, ordered without "
          "HR before any count; haemodynamics simulated once, D and lactate post-processed per case (validated, else "
          "stop); arrival HR analytic; trajectories post-processed and validated; no Cartesian product with blood, "
          "fluid, lactate and HR; nothing selected or approved.")


def verdict(pairs: list, validation: dict, equivalence: dict, compatible: list, surface: dict | None,
            traj: dict | None) -> dict:
    reads = {name.lower() for name in severity_reads()}
    checks = [
        ("severity_without_hr", not any(word in name for name in reads for word in HR_NAMES) and bool(pairs),
         "the arrival severity reads an HR quantity or no case pair is admissible"),
        ("recertification", validation["agree"] and equivalence["equal"] and bool(compatible),
         "the D / lactate recertification fails or no admissible case pair is LACTATE_COMPATIBLE"),
        ("explicit_intrinsic", True, "an implicit intrinsic rate"),
        ("common_gains", True, "a case-specific gain"),
        ("joint_arrival", bool(surface and surface["joint"]), UNRESOLVED),
        ("pressure_deferred", hp.PRIMARY_HR_CALIBRATION == {"sympathetic_per_pressure_deficit": 0.0},
         "the pressure contribution is active"),
        ("no_regression", equivalence["equal"], "D / lactate changed"),
        ("structural", traj is None or traj["exact"], "the HR reconstruction disagrees with the full core"),
    ]
    blockers = [why for _, passed, why in checks if not passed]
    return {"verdict": READY if not blockers else f"{NOT_READY} — {blockers[0]}",
            "checks": {name: passed for name, passed, _ in checks}, "blockers": blockers, "rule": VERDICT_RULE,
            "approved": False}


def design() -> dict:
    return {"faculty": FACULTY, "pairs": [list(p) for p in PAIRS], "pair_labels": {"/".join(k): v for k, v in
                                                                                 PAIR_LABELS.items()},
            "provenance": PAIR_PROVENANCE, "ordering": ORDERING_RULE, "hr_names": HR_NAMES,
            "equivalence": EQUIVALENCE, "compatibility": COMPATIBILITY_RULE, "hr": HR_RULE,
            "comparison": COMPARISON_RULE, "trajectories": TRAJECTORY_RULE, "readings": READINGS,
            "demand_factors": lc.DEMAND_FACTORS, "verdict": VERDICT_RULE, "policy": POLICY}


def freeze_digest() -> str:
    records = {name: hashlib.sha256(path.read_bytes()).hexdigest()
               for name, path in (("P2I-2AD", P2I2AD_RECORD), ("P2I-2AF", hp.P2I2AF_RECORD),
                                  ("P2I-2AG", P2I2AG_RECORD))}
    text = json.dumps({"revision": REVISION, "records": records, "design": design(), "sources": bf.freeze_sources()},
                      sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def p2i2ad_region() -> list:
    record = json.loads(P2I2AD_RECORD.read_text(encoding="utf-8"))
    if record["freeze_digest"] != P2I2AD_DIGEST or record["region"]["digest"] != P2I2AD_REGION_DIGEST:
        raise AssertionError("the P2I-2AD record is not the committed one")
    return record


def _key(pair_57, pair_72) -> str:
    return f"{'/'.join(pair_57)}|{'/'.join(pair_72)}"


def run(progress=None, map_=map) -> dict:
    say = progress or (lambda *_: None)
    with lr.P2FGuard(), lr.LegacyLock():
        ad = p2i2ad_region()
        if json.loads(P2I2AG_RECORD.read_text(encoding="utf-8"))["freeze_digest"] != P2I2AG_DIGEST:
            raise AssertionError("the P2I-2AG record is not the committed one")
        record = la.record_p2i2ab()
        source, support = la.source_space(record), record["crystalloid_support"]
        arrivals = lr.arrival_table()
        pairs = case_pairs()
        allowed = admissible()
        say("haemodynamics")
        tasks = lc.haemodynamic_tasks(source, support)
        store = lc.haemodynamics(tasks, map_)
        say("validation")
        validation = lc.validate(source, support, arrivals, tasks, store, map_)
        out = {"freeze_digest": freeze_digest(), "decided": DECIDED, "revision": REVISION, "policy": POLICY,
               "faculty": FACULTY, "records": {"P2I-2AD": P2I2AD_DIGEST, "P2I-2AG": P2I2AG_DIGEST},
               "inventory": inventory(ad["region"]["inline"]), "case_pairs": pairs,
               "admissible": [list(map(list, combo)) for combo in allowed],
               "analytic_rejections": {reason: sum(1 for p in pairs if reason in p["reasons"])
                                       for reason in ("D57_BELOW_D72", "DELIVERY57_ABOVE_DELIVERY72", "IDENTICAL")},
               "severity_reads": sorted(severity_reads()),
               "validation": {**{k: v for k, v in validation.items() if k not in ("sample", "disagreements")},
                              "disagreements": len(validation["disagreements"])}}
        if not validation["agree"]:
            out["verdict"] = verdict(allowed, validation, {"equal": False}, [], None, None)
            return out
        per, regions = {}, {}
        for factor in lc.DEMAND_FACTORS:
            say(f"filter x{factor:g}")
            per[factor] = per_case_filter(source, support, arrivals, tasks, store, factor, map_)
            regions[factor] = {_key(*combo): combine(per[factor], source, len(support), *combo)
                               for combo in [(p, p) for p in PAIRS] + allowed}
            if factor != lc.PRIMARY_DEMAND:
                per[factor] = {"evaluated": per[factor]["evaluated"]}
        primary = lc.PRIMARY_DEMAND
        tied = [unit for p in PAIRS for unit in regions[primary][_key(p, p)]]
        recorded = {f"{f:g}": ad["filter"][f"{f:g}"]["survivors"] for f in lc.DEMAND_FACTORS}
        mine = {f"{f:g}": sum(_survivors(regions[f][_key(p, p)]) for p in PAIRS) for f in lc.DEMAND_FACTORS}
        equivalence = {"rule": EQUIVALENCE, "region_digest": region_digest(tied),
                       "recorded_digest": P2I2AD_REGION_DIGEST, "survivors": mine, "recorded_survivors": recorded}
        equivalence["equal"] = equivalence["region_digest"] == P2I2AD_REGION_DIGEST and mine == recorded
        out["equivalence"] = equivalence
        if not equivalence["equal"]:
            out["verdict"] = verdict(allowed, validation, equivalence, [], None, None)
            return out
        say("case pairs")
        recert, compatible, compatible_regions = {}, [], {}
        candidates = len(source["p3"]) * len(support) * len(BASES)
        for combo in allowed:
            key = _key(*combo)
            units = regions[primary][key]
            survivors = _survivors(units)
            ids = {f: _ids(regions[f][key]) for f in lc.DEMAND_FACTORS}
            robust = len(ids[primary] & ids[0.9] & ids[1.1]) if survivors else 0
            stats = statistics(per[primary], units)
            picks = representatives(per[primary], source, units)
            reviewed = review(source, support, arrivals, tasks, store, picks)
            status, checks, first = classify(survivors, stats, reviewed)
            recert[key] = {"pair_57m": list(combo[0]), "pair_72f": list(combo[1]), "candidates": candidates,
                           "survivors": survivors, "units": len(units),
                           "survivors_by_demand": {f"{f:g}": _survivors(regions[f][key]) for f in lc.DEMAND_FACTORS},
                           "robust_across_demand": robust, "statistics": stats, "status": status, "checks": checks,
                           "first_failure": first, "representatives": reviewed,
                           "digest": hashlib.sha256(json.dumps([[i, a, b, list(r), list(d)] for i, a, b, r, d in units],
                                                               separators=(",", ":")).encode()).hexdigest()}
            if status == LACTATE_COMPATIBLE:
                compatible.append(combo)
                compatible_regions[key] = {"picks": picks}
        out["recertification"] = recert
        out["lactate_compatible"] = [list(map(list, combo)) for combo in compatible]
        say("arrival HR")
        table = arrival_hr_table()
        surface = hr_surface(table, compatible) if compatible else None
        out["comparison"] = comparison(table, compatible)
        traj = None
        if surface and surface["joint"]:
            say("trajectories")
            traj = trajectories(source, support, compatible_regions, surface["survivors"])
        out["hr_surface"] = surface
        out["trajectories"] = traj
        out["verdict"] = verdict(allowed, validation, equivalence, compatible, surface, traj)
    out["efficiency"] = {
        "haemodynamic_trajectories": len(store), "validation_full_runs": validation["runs"],
        "representative_full_runs": sum(len(item["representatives"]) * 4 for item in recert.values()),
        "post_processed_units": {f"{f:g}": per[f]["evaluated"] for f in lc.DEMAND_FACTORS},
        "case_pairs": len(pairs), "analytic_rejections": len(pairs) - len(allowed),
        "simulation_rejections": len(allowed) - len(compatible),
        "arrival_hr_decompositions": len(table),
        "trajectory_full_runs": traj["full_runs"] if traj else 0, "cartesian_sweep": False, "legacy_read": False}
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--digest", action="store_true")
    parser.add_argument("--design", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--out")
    parser.add_argument("--workers", type=int, default=1)
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
        if args.workers > 1:
            import multiprocessing
            with multiprocessing.Pool(args.workers) as pool:
                result = run(lambda step: print(step, flush=True), lambda f, xs: pool.imap(f, xs, chunksize=4))
        else:
            result = run(lambda step: print(step, flush=True))
        (out / "arrival_severity.json").write_text(json.dumps(result, indent=1, sort_keys=True, default=str),
                                                   encoding="utf-8")
        print(out / "arrival_severity.json")
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
