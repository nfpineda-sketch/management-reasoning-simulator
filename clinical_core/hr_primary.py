"""Phase 2 shadow core, P2I-2AG: defer the pressure feedback and freeze the primary HR calibration surface.

    python -m clinical_core.hr_primary --digest
    python -m clinical_core.hr_primary --design
    python -m clinical_core.hr_primary --run --out <directory outside the repository>

Shadow only and offline. Faculty decisions (2026-10-29), recorded in FACULTY:

1. PRESSURE_SYMPATHETIC_CONTRIBUTION = DEFERRED for the primary HR calibration. The relative-pressure term (referenced
   to the shocked arrival; the pressure domain is uncalibrated) selects no gain, compensates no acute or debt drive and
   enters no arrival matching or ranking: the primary mode zeroes its gain in the analysis profile only
   (PRIMARY_HR_CALIBRATION), and its raw value is reported apart (PRESSURE_TERM_DIAGNOSTIC_ONLY). The common
   physiology keeps it (default gain 1.0, unchanged), for the pressure domain.
2. Every calibration candidate declares its intrinsic HR (60 / 80 / 100): CALIBRATION_REQUIRES_EXPLICIT_INTRINSIC_HR.
   The recorded-HR fallback stays for shadow behaviour outside calibration.
3. HR1 / HR2 are structural tests of the current predicted-arrival model (calibration.FROZEN_RULES), never clinical
   evidence.
4. Authored arrivals 57m 124 and 72f 112 bpm; arrival match tolerance +-5 bpm per case, frozen here before any count.
5. Common acute and debt gains; common intrinsic first; a case-specific intrinsic only as sensitivity, never approved.
6. The P2I-2AF saturation form and candidate set (150 / 175 / 200, the frozen sinus-rate ceilings; HR_RESERVE =
   ceiling - intrinsic), not extended, not approved. D's scale is not approved. Non-sinus edges stay
   GENERALIZATION_BLOCKER_ONLY.

The surface is analytic at arrival (no simulation per candidate); trajectories reuse the P2I-2AD representatives'
physiology (HR reaches no output, D, lactate or RR). Zero joint arrival survivors stops the package
(HR_NUMERIC_CALIBRATION_BLOCKED_BY_ARRIVAL_RECONSTRUCTION): no trajectory decision pack, no envelope proposal.
The legacy HR is never read.
"""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import math
from dataclasses import replace
from pathlib import Path

from . import blood_anchors, calibration, derived, gi_reference
from . import blood_constraints as bc
from . import blood_fluid_calibration as bf
from . import hr_shock as hk
from . import hr_structure as hs
from . import lactate_rebuild as lr
from .bands import Drift
from .derived import DEFAULT_PROFILE, derive
from .integration import run as core_run
from .state import CoreInvariantError, RhythmCode, RhythmState

DECIDED = "2026-10-29"
REVISION = "P2I-2AG"
ROOT = hk.ROOT
CASES = hk.CASES
TAGS = hk.TAGS
L1, L2, L3 = hk.L1, hk.L2, hk.L3
MINUTES = hk.MINUTES
P2I2AF_RECORD = ROOT / "docs" / "revision" / "P2I2AF_hr_shock.json"
P2I2AF_DIGEST = "adb3767b4e8042b9976057587ab337fd5de5cd25119a1bb28e7a119d85768ed3"

FACULTY = {
    "decided": DECIDED,
    "pressure": "PRESSURE_SYMPATHETIC_CONTRIBUTION = DEFERRED for the primary HR calibration: the relative-pressure "
                "term (referenced to the shocked arrival; pressure domain uncalibrated; correlated with the acute "
                "deficit; unloading the drive while a deficit persists) selects no HR gain, compensates no acute or "
                "debt drive and enters no arrival matching or ranking; reported as PRESSURE_TERM_DIAGNOSTIC_ONLY; not "
                "rejected: kept in the common physiology for the pressure domain; no absolute pressure reference",
    "intrinsic": "every HR calibration candidate declares its intrinsic HR (60 / 80 / 100); no implicit recorded-HR "
                 "floor (CALIBRATION_REQUIRES_EXPLICIT_INTRINSIC_HR); the fallback stays outside calibration",
    "hr1_hr2": "accepted only as structural tests of the current predicted-arrival model, never historical clinical "
               "evidence; HR2: with no sympathetic contribution the predicted arrival HR reduces to the declared "
               "intrinsic, rhythm-consistent rate",
    "arrival": "authored 57m 124 and 72f 112 bpm (no later authored HR); arrival match tolerance +-5 bpm for each case, "
               "an educational calibration tolerance, not a measurement-error model; never tuned after counts",
    "common_gains": "acute and debt gains common to both cases; common intrinsic first; a case-specific intrinsic only "
                    "as sensitivity / identifiability, never approved",
    "saturation": "the P2I-2AF smooth form unchanged; candidates 150 / 175 / 200 bpm, exploratory, not approved, not "
                  "extended",
    "d_scale": "D's scale is not approved: HR depends on the observable debt contribution; D 20 / 60 are never "
               "faculty constants",
    "rhythm": "non-sinus and complete beta-blockade edges stay GENERALIZATION_BLOCKER_ONLY; they do not block GI",
    "scope": "shadow only; no final HR approval, no hard trajectory envelope, no pressure / vascular-tone or RR "
             "calibration, no collapse, migration or runtime integration",
}

# 1. The primary mode and the explicit-intrinsic guard ---------------------------------------------------------------

PRESSURE_SYMPATHETIC_CONTRIBUTION = "DEFERRED"
PRESSURE_TERM_DIAGNOSTIC_ONLY = "PRESSURE_TERM_DIAGNOSTIC_ONLY"
#: The primary HR calibration's only change to the analysis profile: the relative-pressure gain is 0. The common
#: default (DEFAULT_PROFILE.sympathetic_per_pressure_deficit) is untouched.
PRIMARY_HR_CALIBRATION = {"sympathetic_per_pressure_deficit": 0.0}
CALIBRATION_REQUIRES_EXPLICIT_INTRINSIC_HR = calibration.CALIBRATION_REQUIRES_EXPLICIT_INTRINSIC_HR


def primary_profile(acute: float | None = None, debt: float | None = None, ceiling: float | None = None):
    """The P2I-2AF analysis profile (reserve 2.5) with the pressure contribution neutralized."""
    return replace(hk.analysis_profile(acute, debt, ceiling), **PRIMARY_HR_CALIBRATION)


def require_explicit_intrinsic(anchors) -> float:
    """The declared intrinsic rate, or CALIBRATION_REQUIRES_EXPLICIT_INTRINSIC_HR (never the recorded arrival HR)."""
    if anchors.intrinsic_sinus_rate is None or dict(anchors.declared).get("intrinsic_sinus_rate") in (None,
                                                                                                   "default_unmapped"):
        raise CoreInvariantError(f"{CALIBRATION_REQUIRES_EXPLICIT_INTRINSIC_HR}: {anchors.case_id} declares no "
                                 "intrinsic sinus rate")
    return anchors.intrinsic_sinus_rate


def pressure_diagnostic_bpm(pressure_rel: float, beta: float = 0.0) -> float:
    """PRESSURE_TERM_DIAGNOSTIC_ONLY: what the common pressure term would add, unconstrained, in bpm. Never read by an
    acceptance, a match or a ranking."""
    return DEFAULT_PROFILE.hr_per_sympathetic_drive * (1.0 - beta) * DEFAULT_PROFILE.sympathetic_per_pressure_deficit * (
        1.0 - pressure_rel)


# 2. The frozen arrival tolerance and candidate surface ---------------------------------------------------------------

AUTHORED = {case: float(gi_reference.authored(case, "hr")) for case in CASES}
TOLERANCE_BPM = 5.0
WINDOWS = {case: (AUTHORED[case] - TOLERANCE_BPM, AUTHORED[case] + TOLERANCE_BPM) for case in CASES}
INTRINSIC = hk.LEVELS
ACUTE = hk.ACUTE
DEBT = hk.DEBT
CEILINGS = hk.CEILINGS
SURFACE_RULE = (
    "Primary surface: intrinsic 60 / 80 / 100 (declared) x acute_deficit_to_sympathetic_gain at the five frozen P2I-2AF "
    "points x debt_to_sympathetic_gain at the five frozen P2I-2AF points x the three frozen P2I-2AF ceilings 150 / 175 "
    "/ 200 (HR_RESERVE = ceiling - intrinsic): 225 candidates, gains and intrinsic common to both cases, pressure "
    "contribution 0. Arrival physiology: the three P2I-2AD representatives (LOW / MID / HIGH, its committed record) as "
    "the core builds them. Arrival HR is analytic (derived.heart_rate_decomposition), no simulation per candidate. "
    "Sensitivity only: the intrinsic may differ by case (3 x 3 pairs), the gains and ceiling stay common.")
ARRIVAL_RULE = (
    f"ARRIVAL-COMPATIBLE for a case: |predicted arrival HR - authored| <= {TOLERANCE_BPM:g} bpm (57m 119-129, 72f "
    "107-117). JOINT: both cases at once with the same candidate. Fixed before any count; never loosened.")
ANALYTIC_RULES = {
    "IMPLICIT_RECORDED_HR_FALLBACK": "a candidate arrival without a declared intrinsic rate",
    "INVALID_RESERVE_BASE": "a sinus base rate at or above the ceiling (HR_RESERVE <= 0)",
    "NEGATIVE_SYMPATHETIC_COMPONENT": "a negative acute or debt contribution",
    "IDENTICAL_PREDICTION_DISJOINT_WINDOWS": "joint, common intrinsic: both cases' arrival physiology is identical "
                                             "(same signal, debt, beta and rhythm), so the predicted arrival HR is "
                                             "identical, and the two tolerance windows do not overlap",
}
CONSTRAINT_RULE = (
    "Per latent dimension, over a set of arrival-compatible candidates: WELL_CONSTRAINED when one value survives; "
    "PARTIALLY_CONSTRAINED when more than one but not all survive; POORLY_IDENTIFIED when all survive and the "
    "least-supported value holds less than half the survivors of the most-supported; NON_IDENTIFIABLE when all survive "
    "and it holds at least half; EMPTY when the set has no survivor (no constraint is assessable).")


def compatible(case: str, hr: float) -> bool:
    return abs(hr - AUTHORED[case]) <= TOLERANCE_BPM


def candidates() -> list[tuple]:
    return [(level, acute, gain, ceiling) for level in INTRINSIC for acute in ACUTE for gain in DEBT
            for ceiling in CEILINGS]


def _key(tag, case, level, acute, gain, ceiling) -> str:
    return f"{tag}|{case}|{level}|{acute!r}|{gain!r}|{ceiling:g}"


# 3. The representatives' physiology (cached, as P2I-2AF builds it) ----------------------------------------------------

def representative_runs(inputs: dict, profile_changes: dict | None = None) -> dict:
    return {(tag, case, scenario): hk.full_run(inputs[tag], case, scenario, "midpoint", profile_changes)
            for tag in TAGS for case in CASES for scenario in (L1, L2, L3)}


def arrival_anchors(runs: dict, tag: str, case: str, level: str):
    """The representative's arrival with the intrinsic level declared (only the intrinsic value differs by level)."""
    return replace(runs[(tag, case, L1)]["anchors"], intrinsic_sinus_rate=hs.intrinsic_levels(case)[level])


def _states(inputs: dict, case: str, scenario: str, profile_changes: dict):
    """The full states of a representative run (hk.full_run's setup, kept to compare whole states)."""
    tau_d, gain_k, k, tau_l, excess, debt, delivery = inputs["point"]
    bag = inputs["bag"] if scenario == L2 else None
    values = {**lr.blood_values(inputs["entry"], case, bag), "reserve": hk.RESERVE}
    _, profile, full = blood_anchors.setup(case, **values)
    case_values = calibration.case_values(case, calibration.GICandidate({}, excess=excess, debt=debt,
                                                                        delivery=delivery, intrinsic="midpoint"))
    case_values["preload_fraction"] = full[bc.POS]
    case_values["arrival_delivery_ratio"] /= hk.RESERVE
    anchors = gi_reference.candidate_anchors(case, case_values)
    profile = replace(profile, debt_clearance_tau_min=tau_d, debt_per_delivery_deficit=gain_k, debt_to_lactate_gain=k,
                      lactate_clearance_tau_min=tau_l, **profile_changes)
    states, _ = blood_anchors.trajectory(anchors, lr.scenario_items(case, scenario, full), MINUTES, profile)
    return anchors, profile, states


def primary_series(run_: dict, intrinsic_rate: float, acute: float, gain: float, ceiling: float) -> list[dict]:
    """HR with the pressure contribution 0 (hk.hr_series on the same physiology), plus the diagnostic column."""
    view = {**run_, "profile": replace(run_["profile"], **PRIMARY_HR_CALIBRATION)}
    series = hk.hr_series(view, intrinsic_rate, acute, gain, ceiling)
    beta = run_["anchors"].beta_blockade
    for point, row in zip(series, run_["rows"]):
        point[PRESSURE_TERM_DIAGNOSTIC_ONLY] = pressure_diagnostic_bpm(row["pressure_rel"], beta) if row["pulse"] else None
    return series


# 4. The arrival surface, the analytic prefilter and the filter (P2I-2AG-4, -5) ----------------------------------------

def arrival_surface(runs: dict) -> dict:
    rows, rejections = {}, {name: 0 for name in ANALYTIC_RULES}
    for tag in TAGS:
        for case in CASES:
            for level in INTRINSIC:
                anchors = arrival_anchors(runs, tag, case, level)
                try:
                    require_explicit_intrinsic(anchors)
                except CoreInvariantError:
                    rejections["IMPLICIT_RECORDED_HR_FALLBACK"] += len(ACUTE) * len(DEBT) * len(CEILINGS)
                    continue
                for acute in ACUTE:
                    for gain in DEBT:
                        for ceiling in CEILINGS:
                            if not ceiling > anchors.intrinsic_sinus_rate:
                                rejections["INVALID_RESERVE_BASE"] += 1
                                continue
                            split = derived.heart_rate_decomposition(anchors, primary_profile(acute, gain, ceiling))
                            if min(split["acute_unconstrained_bpm"], split["debt_unconstrained_bpm"]) < 0.0:
                                rejections["NEGATIVE_SYMPATHETIC_COMPONENT"] += 1
                                continue
                            pressure_on = derived.heart_rate_decomposition(
                                anchors, hk.analysis_profile(acute, gain, ceiling))["predicted_arrival_hr"]
                            hr = split["predicted_arrival_hr"]
                            rows[_key(tag, case, level, acute, gain, ceiling)] = {
                                "tag": tag, "case": case, "intrinsic_level": level, "acute": acute, "debt": gain,
                                "ceiling": ceiling, "intrinsic": split["intrinsic_sinus_rate"],
                                "x0": split["acute_deficit_signal"], "D0": anchors.arrival_oxygen_debt,
                                "beta": anchors.beta_blockade, "rhythm": anchors.rhythm.code.value,
                                "acute_unconstrained_bpm": split["acute_unconstrained_bpm"],
                                "debt_unconstrained_bpm": split["debt_unconstrained_bpm"],
                                "acute_bpm": split["acute_bpm"], "debt_bpm": split["debt_bpm"],
                                "saturated_bpm": split["saturated_bpm"],
                                "reserve_utilization": split["saturated_bpm"] / (ceiling - split["intrinsic_sinus_rate"]),
                                "predicted": hr, "mismatch": hr - AUTHORED[case], "compatible": compatible(case, hr),
                                "pressure_on_predicted": pressure_on}
    # Joint, common intrinsic: the analytic rejection is decided from the inputs, then checked against the outputs.
    disjoint = max(low for low, _ in WINDOWS.values()) > min(high for _, high in WINDOWS.values())
    identical = {}
    same_levels = all(hs.intrinsic_levels(case) == hs.intrinsic_levels(CASES[0]) for case in CASES)
    for tag in TAGS:
        first = [rows[_key(tag, case, "midpoint", ACUTE[0], DEBT[0], CEILINGS[0])] for case in CASES]
        identical[tag] = same_levels and all((a["x0"], a["D0"], a["beta"], a["rhythm"]) == (b["x0"], b["D0"], b["beta"],
                                                                                           b["rhythm"])
                                             for a, b in zip(first, first[1:]))
    joint, joint_survivors = {}, []
    for tag in TAGS:
        for candidate in candidates():
            items = [rows[_key(tag, case, *candidate)] for case in CASES]
            if identical[tag] and disjoint:
                if len({item["predicted"] for item in items}) != 1:
                    raise AssertionError("identical arrival physiology gave different predictions")
                rejections["IDENTICAL_PREDICTION_DISJOINT_WINDOWS"] += 1
                status = hk.ANALYTIC_REJECTION
            else:
                status = "JOINT" if all(item["compatible"] for item in items) else "NOT_JOINT"
            joint[f"{tag}|{candidate[0]}|{candidate[1]!r}|{candidate[2]!r}|{candidate[3]:g}"] = status
            if status == "JOINT":
                joint_survivors.append((tag, *candidate))
    sensitivity = []
    for tag in TAGS:
        for first in INTRINSIC:
            for second in INTRINSIC:
                for acute in ACUTE:
                    for gain in DEBT:
                        for ceiling in CEILINGS:
                            pair = [rows[_key(tag, CASES[0], first, acute, gain, ceiling)],
                                    rows[_key(tag, CASES[1], second, acute, gain, ceiling)]]
                            if all(item["compatible"] for item in pair):
                                sensitivity.append({"tag": tag, "intrinsic": [first, second], "acute": acute,
                                                    "debt": gain, "ceiling": ceiling,
                                                    "predicted": [item["predicted"] for item in pair]})
    return {"rows": rows, "analytic_rejections": rejections, "identical_arrival_physiology": identical,
            "windows_disjoint": disjoint, "joint": joint, "joint_survivors": joint_survivors,
            "case_intrinsic_sensitivity": sensitivity,
            "pressure_on_equal_at_arrival": all(r["predicted"] == r["pressure_on_predicted"] for r in rows.values())}


def _support(items: list[dict], name: str, values) -> dict:
    return {f"{value!r}" if isinstance(value, float) else value: sum(1 for item in items if item[name] == value)
            for value in values}


def filter_report(surface: dict) -> dict:
    rows = list(surface["rows"].values())
    per_case = {case: [r for r in rows if r["case"] == case and r["compatible"]] for case in CASES}
    out = {"rule": ARRIVAL_RULE, "windows": WINDOWS, "total_decompositions": len(rows),
           "analytic_rejections": surface["analytic_rejections"], "simulation_rejections": 0,
           "candidates_per_representative": len(candidates()),
           "compatible": {case: len(items) for case, items in per_case.items()},
           "compatible_by_representative": {tag: {case: sum(1 for r in per_case[case] if r["tag"] == tag)
                                                  for case in CASES} for tag in TAGS},
           "joint_common_intrinsic": len(surface["joint_survivors"]),
           "joint_by_representative": {tag: sum(1 for s in surface["joint_survivors"] if s[0] == tag) for tag in TAGS},
           "identical_arrival_physiology": surface["identical_arrival_physiology"],
           "windows_disjoint": surface["windows_disjoint"],
           "pressure_on_equal_at_arrival": surface["pressure_on_equal_at_arrival"],
           "case_specific_gain_required": False,
           "minimum_common_mismatch_bound_bpm": abs(AUTHORED[CASES[0]] - AUTHORED[CASES[1]]) / 2.0,
           "support": {case: {"intrinsic": _support(items, "intrinsic_level", INTRINSIC),
                              "acute": _support(items, "acute", ACUTE), "debt": _support(items, "debt", DEBT),
                              "ceiling": _support(items, "ceiling", CEILINGS)} for case, items in per_case.items()}}
    sens = surface["case_intrinsic_sensitivity"]
    out["case_intrinsic_sensitivity"] = {
        "joint": len(sens), "of": len(TAGS) * len(INTRINSIC) ** 2 * len(ACUTE) * len(DEBT) * len(CEILINGS),
        "by_representative": {tag: sum(1 for s in sens if s["tag"] == tag) for tag in TAGS},
        "intrinsic_pairs": {f"{a}|{b}": sum(1 for s in sens if s["intrinsic"] == [a, b]) for a in INTRINSIC
                            for b in INTRINSIC},
        "acute": {f"{v!r}": sum(1 for s in sens if s["acute"] == v) for v in ACUTE},
        "debt": {f"{v!r}": sum(1 for s in sens if s["debt"] == v) for v in DEBT},
        "ceiling": {f"{v:g}": sum(1 for s in sens if s["ceiling"] == v) for v in CEILINGS},
        "approved": False}
    return out


def _constraint(counts: dict) -> str:
    values = list(counts.values())
    alive = [v for v in values if v > 0]
    if not alive:
        return "EMPTY"
    if len(alive) == 1:
        return "WELL_CONSTRAINED"
    if len(alive) < len(values):
        return "PARTIALLY_CONSTRAINED"
    return "POORLY_IDENTIFIED" if min(alive) < max(alive) / 2.0 else "NON_IDENTIFIABLE"


def _spread(values: list[float]):
    if not values:
        return None
    values = sorted(values)
    return {"min": values[0], "median": values[len(values) // 2], "max": values[-1], "n": len(values)}


def identifiability(surface: dict, report: dict) -> dict:
    """P2I-2AG-8: what +-5 bpm at arrival constrains, per set, by the frozen rule; and the observable composites."""
    out = {"rule": CONSTRAINT_RULE, "sets": {}}
    for case in CASES:
        support = report["support"][case]
        out["sets"][f"{case} alone"] = {dim: _constraint(support[dim]) for dim in ("intrinsic", "acute", "debt",
                                                                                     "ceiling")}
    joint = surface["joint_survivors"]
    out["sets"]["joint, common intrinsic (primary)"] = {
        dim: _constraint({value: sum(1 for item in joint if item[index] == value) for value in values})
        for dim, index, values in (("intrinsic", 1, INTRINSIC), ("acute", 2, ACUTE), ("debt", 3, DEBT),
                                   ("ceiling", 4, CEILINGS))}
    sens = report["case_intrinsic_sensitivity"]
    first = {level: sum(v for k, v in sens["intrinsic_pairs"].items() if k.split("|")[0] == level) for level in INTRINSIC}
    second = {level: sum(v for k, v in sens["intrinsic_pairs"].items() if k.split("|")[1] == level) for level in INTRINSIC}
    out["sets"]["joint, case-specific intrinsic (sensitivity)"] = {
        f"intrinsic {CASES[0]}": _constraint(first), f"intrinsic {CASES[1]}": _constraint(second),
        "acute": _constraint(sens["acute"]), "debt": _constraint(sens["debt"]), "ceiling": _constraint(sens["ceiling"])}
    rows = list(surface["rows"].values())
    out["composites"] = {
        case: {name: _spread([r[field] for r in rows if r["case"] == case and r["compatible"]])
               for name, field in (("acute_increment_at_arrival_bpm", "acute_unconstrained_bpm"),
                                   ("debt_increment_at_arrival_bpm", "debt_unconstrained_bpm"),
                                   ("total_sympathetic_increment_bpm", "saturated_bpm"),
                                   ("saturated_reserve_utilization", "reserve_utilization"))}
        for case in CASES}
    out["d_scale"] = "the debt increment is gain x D0: only gain x D scale is observable"
    return out


def examples(surface: dict) -> dict:
    """The first compatible decomposition per representative and case, in surface order (an illustration, never a
    ranking), and the first case-specific-intrinsic joint pair."""
    out = {}
    for tag in TAGS:
        for case in CASES:
            hit = next((surface["rows"][_key(tag, case, *c)] for c in candidates()
                        if surface["rows"][_key(tag, case, *c)]["compatible"]), None)
            out[f"{tag}|{case}"] = hit
        out[f"{tag}|sensitivity"] = next((s for s in surface["case_intrinsic_sensitivity"] if s["tag"] == tag), None)
    return out


# 5. Reconstruction validation and non-regression (P2I-2AG-11) ---------------------------------------------------------

def validate(inputs: dict, runs: dict) -> dict:
    """The primary reconstruction against full core reruns with the pressure gain 0 (drive and HR exact), and the
    analytic arrival HR against the core's minute 0 at every intrinsic level."""
    checks = []
    variants = [("midpoint", hk.ANCHOR["acute"], hk.ANCHOR["debt"], hk.ANCHOR["ceiling"]),
                ("lower", ACUTE[-1], DEBT[-1], CEILINGS[0]), ("upper", ACUTE[0], DEBT[0], CEILINGS[-1])]
    for (tag, case, scenario), base in runs.items():
        for level, acute, gain, ceiling in variants:
            changes = {"acute_deficit_to_sympathetic_gain": acute, "debt_to_sympathetic_gain": gain,
                       "sinus_rate_ceiling_bpm": ceiling, **PRIMARY_HR_CALIBRATION}
            full = hk.full_run(inputs[tag], case, scenario, level, changes)
            series = primary_series(base, hs.intrinsic_levels(case)[level], acute, gain, ceiling)
            arrival = derived.heart_rate_decomposition(arrival_anchors(runs, tag, case, level),
                                                       primary_profile(acute, gain, ceiling))
            checks.append({"key": f"{tag}|{case}|{scenario}|{level}",
                           "drive": [p["drive"] for p in series] == [r["drive"] for r in full["rows"]],
                           "hr": [p["hr"] for p in series] == [r["hr"] for r in full["rows"]],
                           "arrival": arrival["predicted_arrival_hr"] == full["rows"][0]["hr"],
                           "no_pressure": all(p["parts"] is None or p["parts"]["pressure"] == 0.0 for p in series)})
    return {"full_reruns": len(checks), "agree": all(all(v for k, v in c.items() if k != "key") for c in checks),
            "no_pressure": all(c["no_pressure"] for c in checks),
            "disagreements": [c for c in checks if not all(v for k, v in c.items() if k != "key")]}


def non_regression(inputs: dict, runs: dict, ad: dict) -> dict:
    """P2I-2AG-11: the pressure neutralization moves nothing but the drive and HR. Whole core states (BloodState, V,
    Hb, D, lactate, oxygen demand...) are equal with and without it once the drive is set aside; the derived delivery,
    effective deficit and RR are equal; D and lactate equal P2I-2AD's record."""
    states_equal = derived_equal = True
    compared = 0
    changes = {"acute_deficit_to_sympathetic_gain": hk.ANCHOR["acute"],
               "debt_to_sympathetic_gain": hk.ANCHOR["debt"], "sinus_rate_ceiling_bpm": hk.ANCHOR["ceiling"]}
    for tag in TAGS:
        for case in CASES:
            for scenario in (L1, L2, L3):
                a_on, p_on, on = _states(inputs[tag], case, scenario, changes)
                a_off, p_off, off = _states(inputs[tag], case, scenario, {**changes, **PRIMARY_HR_CALIBRATION})
                for x, y in zip(on, off):
                    compared += 1
                    states_equal &= replace(x, aux=replace(x.aux, sympathetic_drive=0.0)) == replace(
                        y, aux=replace(y.aux, sympathetic_drive=0.0))
                    dx, dy = derive(x, a_on, p_on), derive(y, a_off, p_off)
                    derived_equal &= (dx.delivery_rel, dx.respiratory_rate, dx.lactate, dx.output_rel,
                                      dx.pressure_rel) == (dy.delivery_rel, dy.respiratory_rate, dy.lactate,
                                                           dy.output_rel, dy.pressure_rel)
                rows = runs[(tag, case, scenario)]["rows"]
                derived_equal &= len(rows) == len(on) and all(r["D"] == s.D for r, s in zip(rows, on))
    recorded = hs.unchanged_physiology(runs, ad)
    return {"states_compared": compared, "states_equal_but_drive": states_equal,
            "delivery_deficit_rr_lactate_equal": derived_equal, "d_lactate_vs_p2i2ad": recorded,
            "unchanged": states_equal and derived_equal and recorded["equal"]}


# 6. Pressure double-counting audit on the P2I-2AF sample (P2I-2AG-2, diagnostic only) ------------------------------------

def _correlation(pairs: list[tuple]) -> float | None:
    n = len(pairs)
    if n < 2:
        return None
    ma, mb = sum(a for a, _ in pairs) / n, sum(b for _, b in pairs) / n
    cov = sum((a - ma) * (b - mb) for a, b in pairs) / n
    sa = math.sqrt(sum((a - ma) ** 2 for a, _ in pairs) / n)
    sb = math.sqrt(sum((b - mb) ** 2 for _, b in pairs) / n)
    return cov / (sa * sb) if sa and sb else None


def _quantiles(values: list[float]):
    if not values:
        return None
    values = sorted(values)
    pick = lambda q: values[min(len(values) - 1, round(q * (len(values) - 1)))]  # noqa: E731
    return {"min": values[0], "q10": pick(0.1), "median": pick(0.5), "q90": pick(0.9), "max": values[-1],
            "n": len(values)}


def _discordant(on: list[float], off: list[float]) -> dict:
    pairs = discordant = ties_changed = 0
    for i in range(len(on)):
        for j in range(i + 1, len(on)):
            pairs += 1
            a, b = on[i] - on[j], off[i] - off[j]
            discordant += a * b < 0
            ties_changed += (a == 0) != (b == 0)
    return {"pairs": pairs, "discordant": discordant, "ties_changed": ties_changed}


def pressure_audit(runs: dict) -> dict:
    """Signals from the 18 representative runs (the P2I-2AF sample); HR with the pressure term on (the common
    physiology) and neutralized (primary), on the P2I-2AF plane at the anchor's ceiling and intrinsic."""
    minutes = []
    for run_ in runs.values():
        for row in run_["rows"][1:]:
            if row["pulse"]:
                minutes.append((row["deficit"] / row["demand"], 1.0 - row["pressure_rel"], row["D"]))
    both = [m for m in minutes if m[0] > 0.0 and m[1] > 0.0]
    against = [m for m in minutes if m[0] > 0.0 and m[1] < 0.0]
    a_p, bpm = DEFAULT_PROFILE.sympathetic_per_pressure_deficit, DEFAULT_PROFILE.hr_per_sympathetic_drive
    anchor_share = [-(a_p * p) / (hk.ANCHOR["acute"] * x + hk.ANCHOR["debt"] * d) for x, p, d in against]
    plane = [(acute, gain) for acute in ACUTE for gain in DEBT]
    series = {}
    for (tag, case, scenario), run_ in runs.items():
        rate = hs.intrinsic_levels(case)["midpoint"]
        series[(tag, case, scenario)] = (
            [[p["hr"] for p in hk.hr_series(run_, rate, a, g, hk.ANCHOR["ceiling"])] for a, g in plane],
            [[p["hr"] for p in primary_series(run_, rate, a, g, hk.ANCHOR["ceiling"])] for a, g in plane])
    landmarks, rankings = {}, {}
    for name, (scenario, minute) in hk.LANDMARKS.items():
        diffs, on_minus, off_minus = [], [], []
        for tag in TAGS:
            for case in CASES:
                hr_on, hr_off = series[(tag, case, scenario)]
                if minute >= len(hr_on[0]):
                    continue
                rate = hs.intrinsic_levels(case)["midpoint"]
                on = [values[minute] for values in hr_on]
                off = [values[minute] for values in hr_off]
                diffs += [x - y for x, y in zip(on, off)]
                on_minus += [x - rate for x in on]
                off_minus += [y - rate for y in off]
                rankings[f"{name}|{tag}|{case}"] = _discordant(on, off)
        landmarks[name] = {"hr_on_minus_off_bpm": _quantiles(diffs), "on_above_intrinsic_bpm": _quantiles(on_minus),
                           "off_above_intrinsic_bpm": _quantiles(off_minus),
                           "on_above_intrinsic_count": sum(1 for v in on_minus if v > 0.0),
                           "off_above_intrinsic_count": sum(1 for v in off_minus if v > 0.0), "readings": len(diffs)}
    totals = {"pairs": sum(r["pairs"] for r in rankings.values()),
              "discordant": sum(r["discordant"] for r in rankings.values()),
              "ties_changed": sum(r["ties_changed"] for r in rankings.values())}
    return {"minutes": len(minutes), "correlation_signals": _correlation([(x, p) for x, p, _ in minutes]),
            "both_push_up": len(both), "both_push_up_share": len(both) / len(minutes),
            "pressure_down_while_deficit": len(against), "pressure_down_while_deficit_share": len(against) / len(minutes),
            "deficit_signal_in_those_minutes": _quantiles([x for x, _, _ in against]),
            "pressure_cancellation_bpm": _quantiles([bpm * a_p * p for _, p, _ in against]),
            "cancelled_share_of_acute_and_debt_at_anchor": _quantiles(anchor_share),
            "landmarks": landmarks, "ranking_changes": totals, "ranking_detail": rankings,
            "arrival_unaffected": "pressure_rel is 1 at arrival, so the arrival filter is the same on and off",
            "classification": hk.NEEDS_PRESSURE_DOMAIN_REVIEW, "calibrated": False}


# 7. D-scale, rhythm and the HR1 / HR2 semantics (P2I-2AG-3, -9, -10) ---------------------------------------------------

def d_scale_probe() -> dict:
    """D x c with debt gain / c (deficit-to-D gain x c, arrival debt x c) gives the same primary HR; without the gain
    division it does not (the probe discriminates)."""
    anchors = hk.analysis_anchors(CASES[0], "midpoint", "midpoint", "midpoint")
    falling = (Drift("pump", "P", 0, 90, -0.005),)
    base = core_run(anchors, falling, 90, primary_profile())
    rows = []
    for c in (0.37, 3.0):
        scaled = replace(anchors, arrival_oxygen_debt=c * anchors.arrival_oxygen_debt)
        accrual = c * DEFAULT_PROFILE.debt_per_delivery_deficit
        other = core_run(scaled, falling, 90, replace(primary_profile(debt=hk.ANCHOR["debt"] / c),
                                                     debt_per_delivery_deficit=accrual))
        wrong = core_run(scaled, falling, 90, replace(primary_profile(), debt_per_delivery_deficit=accrual))
        rows.append({"c": c, "max_gap_bpm": max(abs(a.pulse_rate_bpm - b.pulse_rate_bpm)
                                                 for a, b in zip(base.derived(), other.derived())),
                     "without_gain_division_gap_bpm": max(abs(a.pulse_rate_bpm - b.pulse_rate_bpm)
                                                          for a, b in zip(base.derived(), wrong.derived()))})
    return {"rows": rows, "holds": all(r["max_gap_bpm"] <= 1e-9 < r["without_gain_division_gap_bpm"] for r in rows)}


def rhythm_probe() -> dict:
    """The P2I-2AF edges under the primary mode: a paced arrival (no intrinsic sinus rate exists for it) and a sinus
    arrival under complete beta-blockade (its declared intrinsic is its arrival HR: the anchors allow no sympathetic
    share under beta 1), both with an arrival debt."""
    canonical = gi_reference.candidate_anchors(CASES[0], {})
    paced = replace(canonical, rhythm=RhythmState(RhythmCode.PACED, canonical.hr, 1.0, True), arrival_oxygen_debt=5.0,
                    declared={**dict(canonical.declared), "arrival_oxygen_debt": "synthetic_probe"})
    base = gi_reference.candidate_anchors(CASES[0], {"intrinsic_sinus_rate": canonical.hr})
    blocked = replace(base, beta_blockade=1.0, arrival_oxygen_debt=5.0,
                      declared={**dict(base.declared), "arrival_oxygen_debt": "synthetic_probe",
                                "beta_blockade": "synthetic_probe"})
    out = {}
    for name, anchors, expected in (("paced", paced, canonical.hr), ("beta_1", blocked, canonical.hr)):
        rates = {d.pulse_rate_bpm for d in core_run(anchors, (Drift("pump", "P", 0, 30, -0.005),), 30,
                                                    primary_profile()).derived()}
        out[name] = {"rates": sorted(rates), "rate_constant": rates == {expected}}
    return {"cases": out, "classification": "GENERALIZATION_BLOCKER_ONLY", "affects_gi": False,
            "holds": all(item["rate_constant"] for item in out.values())}


def hr_semantics() -> dict:
    """P2I-2AG-3: the modern invariants HR1 / HR2 protect, read from the frozen rules and check_hr."""
    source = inspect.getsource(calibration.check_hr)
    rules = calibration.FROZEN_RULES
    guard = gi_reference.candidate_anchors(CASES[0], {})
    try:
        calibration.check_hr(DEFAULT_PROFILE, {CASES[0]: guard})
        refused = False
    except calibration.Failed as error:
        refused = CALIBRATION_REQUIRES_EXPLICIT_INTRINSIC_HR in str(error)
    return {"HR1": {"rule": rules["HR1"].rule, "probe": rules["HR1"].probe},
            "HR2": {"rule": rules["HR2"].rule, "probe": rules["HR2"].probe},
            "structural_only": all("never clinical calibration evidence" in rules[n].probe for n in ("HR1", "HR2")),
            "check_hr_requires_explicit_intrinsic": CALIBRATION_REQUIRES_EXPLICIT_INTRINSIC_HR in source and refused,
            "hr2_arrival_reduction_encoded": "arrival_state(arrival, profile).aux.sympathetic_drive == 0.0" in source,
            "no_authored_or_legacy_target": "arrival.hr" not in source and "_legacy_run" not in source,
            "fallback_outside_calibration": derived.intrinsic_sinus_rate(guard) == guard.hr}


# 8. Verdict, next step, freeze --------------------------------------------------------------------------------------

READY = "HR_NUMERIC_DECISION_SURFACE_READY_FOR_FACULTY"
NOT_READY = "HR_NUMERIC_DECISION_SURFACE_NOT_READY"
BLOCKED_BY_ARRIVAL = "HR_NUMERIC_CALIBRATION_BLOCKED_BY_ARRIVAL_RECONSTRUCTION"
VERDICT_RULE = (
    f"{READY} when: (1) the pressure contribution enters no candidate acceptance (the primary profile zeroes it; the "
    "reconstruction reads no pressure; its value is reported apart, diagnostic only); (2) every candidate declares its "
    "intrinsic rate (no fallback); (3) HR1 / HR2 carry the current structural semantics (frozen rule texts, check_hr's "
    "guard and HR2 arrival reduction); (4) at least one candidate is jointly arrival-compatible with COMMON intrinsic "
    "and common gains; (5) no case-specific gain (by construction); (6) D, lactate, RR, BloodState and DO2 / effective "
    "deficit unchanged, and the reconstruction agrees with the full core. The suite criterion (no new failure) is the "
    f"final certification's, outside this module. Otherwise {NOT_READY} with the first blocker; zero joint survivors "
    f"is {BLOCKED_BY_ARRIVAL} and stops the package: no trajectory decision pack (P2I-2AG-6) and no envelope proposal "
    "(P2I-2AG-7) is built, and the tolerance is never loosened.")
POLICY = ("Shadow only. The P2I-2AD representatives (its committed record) and synthetic probes; the P2F region "
          "never; the legacy HR never read. Arrival analytic; trajectories post-processed from the cached physiology "
          "and validated on full reruns; no Cartesian product with blood, fluid or lactate; no pressure, RR or lactate "
          "change; nothing selected or approved.")


def verdict(filter_: dict, semantics: dict, validation: dict, unchanged: dict) -> dict:
    checks = [
        ("pressure_excluded", PRIMARY_HR_CALIBRATION["sympathetic_per_pressure_deficit"] == 0.0
         and validation["no_pressure"] and validation["agree"], "the pressure contribution reaches acceptance"),
        ("explicit_intrinsic", filter_["analytic_rejections"]["IMPLICIT_RECORDED_HR_FALLBACK"] == 0
         and semantics["check_hr_requires_explicit_intrinsic"], "an implicit recorded-HR fallback"),
        ("hr_semantics", semantics["structural_only"] and semantics["hr2_arrival_reduction_encoded"]
         and semantics["no_authored_or_legacy_target"], "HR1 / HR2 lack the current structural semantics"),
        ("joint_arrival", filter_["joint_common_intrinsic"] > 0, BLOCKED_BY_ARRIVAL),
        ("common_gains", not filter_["case_specific_gain_required"], "a case-specific gain is required"),
        ("unchanged_physiology", unchanged["unchanged"] and validation["agree"],
         "D, lactate, RR, BloodState or DO2 changed, or the reconstruction disagrees"),
    ]
    blockers = [why for _, passed, why in checks if not passed]
    return {"verdict": READY if not blockers else f"{NOT_READY} — {blockers[0]}",
            "checks": {name: passed for name, passed, _ in checks}, "blockers": blockers, "rule": VERDICT_RULE,
            "stopped": BLOCKED_BY_ARRIVAL in blockers, "approved": False}


def design() -> dict:
    return {"faculty": FACULTY, "primary_mode": {"pressure": PRESSURE_SYMPATHETIC_CONTRIBUTION,
                                                 "profile_changes": PRIMARY_HR_CALIBRATION,
                                                 "diagnostic_column": PRESSURE_TERM_DIAGNOSTIC_ONLY},
            "guard": CALIBRATION_REQUIRES_EXPLICIT_INTRINSIC_HR, "authored": AUTHORED, "tolerance_bpm": TOLERANCE_BPM,
            "windows": WINDOWS, "surface": {"rule": SURFACE_RULE, "intrinsic": INTRINSIC, "acute": ACUTE,
                                            "debt": DEBT, "ceilings": CEILINGS, "count": len(candidates())},
            "arrival_rule": ARRIVAL_RULE, "analytic_rules": ANALYTIC_RULES, "constraint_rule": CONSTRAINT_RULE,
            "verdict": VERDICT_RULE, "policy": POLICY}


def p2i2af_record() -> dict:
    record = json.loads(P2I2AF_RECORD.read_text(encoding="utf-8"))
    if record["freeze_digest"] != P2I2AF_DIGEST:
        raise AssertionError("the P2I-2AF record is not the committed one")
    return record


def freeze_digest() -> str:
    records = {name: hashlib.sha256(path.read_bytes()).hexdigest()
               for name, path in (("P2I-2AD", hs.P2I2AD_RECORD), ("P2I-2AE", hk.P2I2AE_RECORD),
                                  ("P2I-2AF", P2I2AF_RECORD))}
    text = json.dumps({"revision": REVISION, "records": records, "design": design(), "sources": bf.freeze_sources()},
                      sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run(progress=None) -> dict:
    say = progress or (lambda *_: None)
    with lr.P2FGuard(), lr.LegacyLock():
        ad = hs.p2i2ad_record()
        p2i2af_record()
        inputs = hs.representative_inputs(ad)
        say("representatives")
        runs = representative_runs(inputs)
        say("arrival")
        surface = arrival_surface(runs)
        filter_ = filter_report(surface)
        say("validation")
        validation = validate(inputs, runs)
        unchanged = non_regression(inputs, runs, ad)
        semantics = hr_semantics()
        say("diagnostics")
        audit_pressure = pressure_audit(runs)
        out = {"freeze_digest": freeze_digest(), "decided": DECIDED, "revision": REVISION, "policy": POLICY,
               "faculty": FACULTY, "records": {"P2I-2AD": hs.P2I2AD_DIGEST, "P2I-2AE": hk.P2I2AE_DIGEST,
                                               "P2I-2AF": P2I2AF_DIGEST},
               "design": {k: v for k, v in design().items() if k not in ("faculty", "policy")},
               "hr_semantics": semantics, "arrival": filter_, "examples": examples(surface),
               "identifiability": identifiability(surface, filter_), "pressure_audit": audit_pressure,
               "d_scale": d_scale_probe(), "rhythm": rhythm_probe(), "validation": validation,
               "non_regression": unchanged}
        out["verdict"] = verdict(filter_, semantics, validation, unchanged)
        if not out["verdict"]["stopped"]:
            raise NotImplementedError("joint arrival survivors exist: the decision pack (P2I-2AG-6 / -7) is a separate "
                                      "step, not built in this freeze")
    out["efficiency"] = {"representative_runs": len(runs), "validation_full_reruns": validation["full_reruns"],
                         "non_regression_state_runs": 2 * len(runs), "arrival_decompositions_analytic": len(
                             surface["rows"]), "analytic_rejections": filter_["analytic_rejections"],
                         "simulation_rejections": 0, "post_processed_series": 2 * len(runs) * len(ACUTE) * len(DEBT),
                         "trajectory_decision_pack_built": False, "cartesian_sweep": False,
                         "legacy_read": False}
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
        (out / "hr_primary.json").write_text(json.dumps(result, indent=1, sort_keys=True, default=str), encoding="utf-8")
        print(out / "hr_primary.json")
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
