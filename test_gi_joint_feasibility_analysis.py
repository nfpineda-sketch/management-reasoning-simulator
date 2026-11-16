"""P3-327 .. P3-336: can the CURRENT GI physiology satisfy the three faculty anchors at once?

MODEL_ANALYSIS, nothing else. TEST-SIDE and READ-ONLY: it imports the certified shadow core, the frozen faculty evaluators and the page-faithful
harness, and writes nothing to any encounter, authority record, snapshot, baseline, region or faculty review. It approves no bleed rate, no pressure
parameter and no kernel, it chooses no point, and it changes no physiology (``clinical_core/`` and ``family_engine.py`` are read, never edited). Every
mutation is a COUNTERFACTUAL copy made inside this process.

The three independent faculty constraints of the Amendment-3 gate (FD-RATE-13):

* A, untreated GI deterioration: the frozen faculty envelopes of the untreated output (U-OUT), per case;
* B, one unit of packed red cells (FD-RATE-09): about +8 to +18 mmHg of systolic pressure within about 15 to 30 simulated minutes, at the authored
  arrival, with the bleeding temporarily controlled and no other volume intervention;
* C, one litre of saline over 60 minutes during active bleeding (FD-RATE-10): about 15 to 35 % of the untreated pressure deterioration prevented at
  minute 60;

together with every constraint that already existed (FD-BLD-01 .. FD-BLD-09, U-HB, the closed crystalloid region), which FD-RATE-12 keeps untouched.

Regenerate the stored record with ``MRS_WRITE_JOINT_FEASIBILITY=1 python3 test_gi_joint_feasibility_analysis.py`` (the person who changes the analysis).
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import math
import os
import re
from pathlib import Path

import test_gi_frg_crystalloid_analysis as fa
import test_gi_bleed_rate_analysis as ga

ROOT = Path(__file__).resolve().parent
RECORD_PATH = ROOT / "docs" / "revision" / "PHASE3_GI_JOINT_FEASIBILITY_ANALYSIS.json"
WRITE_FLAG = "MRS_WRITE_JOINT_FEASIBILITY"
VERSION = "P3-327"
EVIDENCE_CLASS = "MODEL_ANALYSIS"

CASES = ga.CASES
#: FD-RATE-09 (faculty, 2026-11-15): a DEVELOPMENT behavioural region, not a clinical universal, a production rule or a resident-facing rule.
PRBC_SBP_RISE_MMHG = (8.0, 18.0)
PRBC_WINDOW_MIN = (15, 30)
PRBC_TOO_LARGE_FROM_MMHG = 25.0
PRBC_ORDER = ("Place an IV line.", "Transfuse 1 unit of packed red cells.")
PRBC_READ_MINUTES = (0, 5, 15, 30)
#: FD-RATE-10 (faculty, 2026-11-15): the share of the untreated pressure deterioration prevented at minute 60. Not an exact calibration target.
SLOW_CRYSTALLOID_SHARE = (0.15, 0.35)
SLOW_READ_MINUTE = 60
COMMITTED_FRACTION = ga.COMMITTED_FRACTION
#: A second SHARED arrival position, inside both cases' own bands ([0.2, 0.5] and [0.3, 0.6]): a sensitivity, never a choice.
SENSITIVITY_FRACTION = 0.4
INSIDE_C = {**ga.INSIDE_C, ("gi_bleed_57m", 0.4): 0.0026, ("gi_bleed_72f", 0.4): 0.0018}
#: The repository's own upper edge of a non-shock lactate (gi_reference: "a non-shock clearance baseline of 0.8-2.0 mmol/L"); used only to say that one
#: unit did not normalize perfusion, never as a target.
NON_SHOCK_LACTATE_UPPER = 2.0
TOLERANCE = 1e-4
INWARD = 1.005              # a witness sits half a percent inside the edge it names
AMBIGUOUS_BELOW = 0.01      # a feasible interval narrower than 1 % of its own value is reported NUMERICALLY_AMBIGUOUS, not NONEMPTY


# -- running the certified core --------------------------------------------------------------------------------------------------------------------------

def run(scenario: dict, minutes: int, *, rate=None, scale=None, kernel=None, drop_fluid: bool = False, fraction=None):
    """As ``test_gi_bleed_rate_analysis.run`` (counterfactual copies only), with the shadow core's own derived readings beside each minute."""
    from clinical_core import integration
    from clinical_core.interventions.fluids import Crystalloid
    anchors, contributors, _captured, profile = integration.scenario_from_dict(scenario)
    made = []
    for item in contributors:
        if isinstance(item, Crystalloid):
            if drop_fluid:
                continue
            if kernel is not None:
                item = dataclasses.replace(item, effective_ml_per_ml=float(kernel[0]), transient_share=float(kernel[1]), leak_tau_min=float(kernel[2]))
        elif rate is not None and type(item).__name__ == "GIHaemorrhage":
            item = dataclasses.replace(item, blood_loss_ml_per_min=float(rate))
        made.append(item)
    changes = {}
    if scale is not None:
        changes["preload_curve_scale_ml"] = float(scale)
    if fraction is not None:
        changes["arrival_preload_fraction"] = float(fraction)
    if changes:
        profile = dataclasses.replace(profile, **changes)
    stopped = None
    try:
        trajectory = integration.run(anchors, made, minutes, profile)
    except Exception as error:                       # the core's own boundary: reported, never worked around
        found = re.search(r"minute (\d+)", str(error))
        if found is None:
            raise
        stopped = int(found.group(1))
        trajectory = integration.run(anchors, made, stopped - 1, profile)
    rows = fa.per_minute(trajectory, anchors, profile)
    for row, reading in zip(rows, trajectory.derived()):
        derived = reading.to_dict()
        row.update({"shadow_hr": derived["monitor_rate_bpm"], "crt_s": derived["crt_s"], "lactate": derived["lactate"], "delivery_rel": derived["delivery_rel"]})
    return rows, stopped


def build_context() -> dict:
    live = ga.constants()
    frg = json.loads(ga.FRG_RECORD_PATH.read_text(encoding="utf-8"))
    runtime, least = frg["mass_balance"]["kernel"], frg["volume_region"]["core_runs"]["region_least_protective"]["point"]
    extremes = next(value for value in frg["volume_region"].values() if isinstance(value, dict) and "region_most_retained_at_60_ml" in value)
    _case_g, orders_g = fa.reviewed_orders("FR-G")
    return {"live": live, "s0": live["default_preload_scale_ml"], "c0": live["legacy_circulation_per_min"], "rate0": live["runtime_rate_ml_min"],
            "unit_ml": live["red_cell_unit_volume_ml"],
            "prbc": {case: fa.capture(case, PRBC_ORDER) for case in CASES},
            "slow": {case: fa.capture(case, orders_g) for case in CASES},
            "untreated": {case: fa.capture(case, fa.UNTREATED_ORDERS) for case in CASES},
            "reviewed_untreated": {"gi_bleed_57m": "FR-A", "gi_bleed_72f": "FR-D"},
            "kernels": {"RUNTIME_OUTSIDE_THE_CLOSED_REGION": (runtime["e"], runtime["s"], runtime["tau"]),
                        "CLOSED_REGION_LEAST_PROTECTIVE": (least["e"], least["s"], least["tau"])},
            "closed_region_retained_60_ml": [extremes["region_least_retained_at_60_ml"], extremes["region_most_retained_at_60_ml"]],
            "depends_on": {"frg_crystalloid_analysis_record_digest": frg["record_digest"], "bleed_rate_scale_record_digest": ga.load_record()["record_digest"]}}


# -- the three readings ------------------------------------------------------------------------------------------------------------------------------------

def prbc_rows(ctx, case: str, scale: float, fraction=None, minutes: int = 45):
    """One unit at the authored arrival with the bleeding temporarily controlled (the counterfactual copy bleeds 0 mL/min) and nothing else given."""
    rows, _stopped = run(ctx["prbc"][case], minutes, rate=0.0, scale=scale, fraction=fraction)
    return rows


def prbc_rise(ctx, case: str, scale: float, fraction=None) -> float:
    rows = prbc_rows(ctx, case, scale, fraction, PRBC_WINDOW_MIN[1])
    return rows[PRBC_WINDOW_MIN[1]]["sbp"] - rows[0]["sbp"]


def prbc_rise_at(ctx, case: str, scale: float, minute: int, fraction=None) -> float:
    rows = prbc_rows(ctx, case, scale, fraction, PRBC_WINDOW_MIN[1])
    return rows[minute]["sbp"] - rows[0]["sbp"]


def slow_share(ctx, case: str, rate: float, scale: float, kernel, fraction=None):
    """The share of the untreated pressure deterioration that 1 L over 60 minutes prevents at minute 60 (None where a run stopped earlier)."""
    treated, _ = run(ctx["slow"][case], SLOW_READ_MINUTE + 1, rate=rate, scale=scale, kernel=kernel, fraction=fraction)
    plain, _ = run(ctx["untreated"][case], SLOW_READ_MINUTE + 1, rate=rate, scale=scale, fraction=fraction, drop_fluid=True)
    return ga.protection(treated, plain, SLOW_READ_MINUTE)


def frozen_verdicts(case: str, rate: float, scale: float, fraction: float, kernel) -> dict:
    """Every EXISTING constraint, from the frozen evaluator's own rows and its own primary verdicts."""
    from clinical_core import blood_constraints as bc
    values = {"bleed_ml_per_min": float(rate), "preload_scale_over_kappa_ml": float(scale), "preload_fraction": float(fraction),
              "crystalloid_effective_ml_per_ml": float(kernel[0]), "crystalloid_transient_share": float(kernel[1]), "crystalloid_leak_tau_min": float(kernel[2])}
    try:
        return {"readable": True, **bc.evaluate(case, values)["verdicts"]["primary"]}
    except AssertionError as error:
        return {"readable": False, "why": str(error)[:160]}


def every_existing_constraint_readable(rate: float, scale: float, kernel) -> bool:
    return all(frozen_verdicts(case, rate, scale, COMMITTED_FRACTION, kernel).get("readable", False) for case in CASES)


def readable_rate_limit(c: float, rate_low: float, rate_high: float, kernel):
    """The fastest bleed rate at which the frozen evaluator can still READ every existing constraint (its blood readings use one fixed haemodynamic
    reading, scale 1500, whose untreated run ends at the core's boundary when the bleed is fast enough). ``None``: readable up to ``rate_high``."""
    if every_existing_constraint_readable(rate_high, rate_high / c, kernel):
        return None
    if not every_existing_constraint_readable(rate_low, rate_low / c, kernel):
        return rate_low
    return ga.bisect(lambda rate: every_existing_constraint_readable(rate, rate / c, kernel), rate_low, rate_high, 1e-3)


# -- P3-327 and P3-327A: the mechanism and the timing of one unit ------------------------------------------------------------------------------------

def section_prbc_mechanism(ctx) -> dict:
    from clinical_core import integration
    out = {}
    for case in CASES:
        anchors, contributors, _minutes, profile = integration.scenario_from_dict(ctx["prbc"][case])
        unit = next(item for item in contributors if type(item).__name__ == "PackedRedCells")
        rows = prbc_rows(ctx, case, ctx["s0"])
        fraction, scale, kappa = profile.arrival_preload_fraction, profile.preload_curve_scale_ml, profile.volume_preload_kappa
        closed_form = rows[0]["sbp"] * (1.0 - fraction) * (1.0 - math.exp(-kappa * unit.volume_ml_per_unit / scale)) / fraction
        volume0 = profile.arrival_circulating_volume_ml
        hb_expected = (volume0 * rows[0]["hb"] + unit.volume_ml_per_unit * unit.unit_hb_g_dl) / (volume0 + unit.volume_ml_per_unit)
        out[case] = {"contributor": {"type": "PackedRedCells", "units": unit.units, "volume_ml_per_unit": unit.volume_ml_per_unit, "unit_hb_g_dl": unit.unit_hb_g_dl,
                                     "duration_min": unit.duration_min, "untimed_units_per_min": unit.untimed_units_per_min, "start_minute": unit.start_minute},
                     "chain_at_the_current_point": {str(m): {"transfused_ml_this_minute": rows[m]["V"] - rows[m - 1]["V"] if m else 0.0, "effective_volume_change_ml_eq": rows[m]["V"],
                                                             "hb": rows[m]["hb"], "preload_position": rows[m]["preload_position"], "forward_flow_output_rel": rows[m]["forward_flow_output_rel"],
                                                             "sbp": rows[m]["sbp"], "dbp": rows[m]["dbp"], "map": rows[m]["map"]} for m in (0, 5, 15, 30, 45)},
                     "sbp_rise_at_30_mmHg": rows[30]["sbp"] - rows[0]["sbp"], "sbp_rise_closed_form_mmHg": closed_form,
                     "closed_form_agrees": abs(rows[30]["sbp"] - rows[0]["sbp"] - closed_form) < 1e-9,
                     "hb_at_30": rows[30]["hb"], "hb_mixing_closed_form": hb_expected, "hb_agrees": abs(rows[30]["hb"] - hb_expected) < 1e-9,
                     "delivery_is_linear": all(abs(rows[m]["V"] - unit.volume_ml_per_unit * m / 30.0) < 1e-9 for m in (5, 15, 30)),
                     "nothing_after_the_unit_ends": abs(rows[45]["sbp"] - rows[30]["sbp"]) < 1e-9,
                     "share_of_the_response_at_15_min": (rows[15]["sbp"] - rows[0]["sbp"]) / (rows[30]["sbp"] - rows[0]["sbp"]),
                     "current_point_is_too_large_by_FD_RATE_09": rows[30]["sbp"] - rows[0]["sbp"] >= PRBC_TOO_LARGE_FROM_MMHG}
    return {"cases": out,
            "mechanism": ["each minute the unit delivers units x volume_ml_per_unit of circulating volume as ONE blood flow (RED_CELL_TRANSFUSION) at the unit's haemoglobin concentration",
                          "the shared blood state adds the volume and the red cells; haemoglobin is the mixed concentration, never a fixed step",
                          "V = kappa x circulating-volume change; the preload position is 1 - (1 - f) exp(-V / scale); output and pressure are that position over f (GI: P = 1, T = 1)",
                          "so the pressure response to one unit is SBP_arrival x (1 - f)(1 - exp(-kappa x unit_volume / scale)) / f: it reads the unit volume over the scale and nothing of the bleed rate"],
            "timing": {"class": "FINITE_DURATION_INFUSION", "default": "an untimed unit runs at 1/30 unit per minute: 30 minutes, linear",
                       "response_complete_at_minute": 30, "instantaneous": False,
                       "faculty_window_min": list(PRBC_WINDOW_MIN),
                       "mapping": "the faculty window of about 15 to 30 minutes is read at minute 30, the end of the default unit, where the whole response is present; at minute 15 half of the volume is in and slightly more than half of the pressure response; nothing in the infusion semantics was changed"},
            "bleeding_for_this_anchor": "temporarily controlled in a counterfactual copy (0 mL/min) for THIS reading only; no other scenario of this analysis stops the bleed"}


# -- P3-328: the reduced coordinates -----------------------------------------------------------------------------------------------------------------------

def section_reduction(ctx) -> dict:
    s0, c0, kernels = ctx["s0"], ctx["c0"], ctx["kernels"]
    case = "gi_bleed_72f"
    # B reads the scale only: not the bleed rate (the bleed is controlled) and not the crystalloid kernel (none is given)
    b_values = [prbc_rise(ctx, case, 2000.0), run(ctx["prbc"][case], 30, rate=0.0, scale=2000.0, kernel=kernels["CLOSED_REGION_LEAST_PROTECTIVE"])[0][30]["sbp"] - 98.0]
    # C reads the rate and the kernel only: the same on very different maps
    c_values = [slow_share(ctx, case, 8.0, scale, kernels["CLOSED_REGION_LEAST_PROTECTIVE"], fraction) for scale, fraction in ((1500.0, None), (2650.0, None), (3100.0, None), (2650.0, 0.4))]
    # the coupling of B and C through ONE volume channel: share prevented / one-unit gain is fixed by the kernel, whatever the scale
    coupling = {}
    for name, kernel in kernels.items():
        ratios = []
        for scale in (1500.0, 2200.0, 3000.0):
            gain = prbc_rise(ctx, case, scale) / 98.0
            ratios.append(slow_share(ctx, case, c0 * scale, scale, kernel) / gain)
        retained = fa.retained_ml(1000.0, 60, kernel[0], kernel[1], kernel[2], 60)
        coupling[name] = {"share_prevented_over_one_unit_gain_at_three_scales": ratios, "spread": max(ratios) - min(ratios),
                          "retained_at_60_ml": retained, "retained_over_one_unit_volume": retained / ctx["unit_ml"]}
    return {"coordinates": {"A_untreated": "c = bleed_rate x kappa / scale (with the arrival position f): the untreated course reads nothing else (P3-319: invariant to 1.6e-13 mmHg)",
                            "B_one_unit": "u = unit_volume x kappa / scale (with f): the one-unit response reads nothing else",
                            "C_slow_crystalloid": "q = crystalloid retained at 60 min / blood shed in 60 min = R60 / (bleed_rate x 60): the share prevented reads the rate and the kernel, not the map"},
            "free_coordinates": ["bleed_rate", "scale", "the kernel's retained volume R60 (inside the closed crystalloid region)", "the arrival position f (kept at the committed 0.5; 0.4 as a sensitivity)"],
            "three_constraints_on": "two map coordinates (c and scale, with bleed_rate = c x scale) and one kernel coordinate: A bounds c, B bounds scale, C bounds c x scale / R60",
            "b_reads_the_scale_only": {"sbp_rise_at_scale_2000_with_and_without_a_kernel_change": b_values, "holds": abs(b_values[0] - b_values[1]) < 1e-9},
            "c_reads_the_rate_and_the_kernel_only": {"share_at_8_ml_min_on_four_maps": c_values, "max_minus_min": max(c_values) - min(c_values), "holds": max(c_values) - min(c_values) < 0.05},
            "b_and_c_are_coupled_through_one_volume_channel": coupling,
            "coupling_reading": "blood and crystalloid act on pressure through the same effective volume, so the share a slow litre prevents is a FIXED multiple of the one-unit gain, set by how many unit-volumes the litre still retains at 60 min; changing the scale moves both together"}


# -- P3-329: the feasibility region ------------------------------------------------------------------------------------------------------------------------

def _interval_status(low: float, high: float) -> str:
    if high < low:
        return "EMPTY"
    return "NUMERICALLY_AMBIGUOUS" if (high - low) < AMBIGUOUS_BELOW * high else "NONEMPTY"


def constraint_a(fraction: float) -> dict:
    """The untreated constraint in its own coordinate: c = rate / scale admitted by the frozen U-OUT envelopes (measured at one scale; it is scale-free)."""
    scale = 2000.0
    per_case = {case: [value / scale for value in ga.u_out_interval(case, scale, fraction, INSIDE_C[(case, fraction)])] for case in CASES}
    common = [max(item[0] for item in per_case.values()), min(item[1] for item in per_case.values())]
    return {"per_case_c": per_case, "common_c": common, "status": _interval_status(*common)}


def constraint_b(ctx, fraction: float) -> dict:
    """The one-unit constraint in its own coordinate: the scales at which the rise at minute 30 is inside +8 .. +18 mmHg, per case and common."""
    low_rise, high_rise = PRBC_SBP_RISE_MMHG
    per_case = {}
    for case in CASES:
        smallest = ga.bisect(lambda scale: prbc_rise(ctx, case, scale, fraction) <= high_rise, 300.0, 20000.0)
        largest = ga.bisect(lambda scale: prbc_rise(ctx, case, scale, fraction) >= low_rise, 300.0, 20000.0)
        per_case[case] = [smallest, largest]
    common = [max(item[0] for item in per_case.values()), min(item[1] for item in per_case.values())]
    return {"per_case_scale_ml_eq": per_case, "common_scale_ml_eq": common, "status": _interval_status(*common),
            "binding": {"smallest_scale": "the +18 mmHg ceiling in 72f (the higher arrival pressure)", "largest_scale": "the +8 mmHg floor in 57m (the lower arrival pressure)"}}


def constraint_c(ctx, a: dict, b: dict, kernel, fraction: float) -> dict:
    """Where the slow-crystalloid share falls inside the box A x B for ONE kernel, and the sub-box it leaves (projections by bisection)."""
    case = ga.FRG_CASE
    low_share, high_share = SLOW_CRYSTALLOID_SHARE
    (c_low, c_high), (s_low, s_high) = a["common_c"], b["common_scale_ml_eq"]
    share = lambda c, s: slow_share(ctx, case, c * s, s, kernel, fraction)          # noqa: E731
    smallest_share, largest_share = share(c_high, s_high), share(c_low, s_low)
    out = {"share_at_the_most_protected_corner": largest_share, "share_at_the_least_protected_corner": smallest_share,
           "retained_at_60_ml": fa.retained_ml(1000.0, 60, kernel[0], kernel[1], kernel[2], 60)}
    if smallest_share > high_share or largest_share < low_share:
        return {**out, "status": "EMPTY", "why": "even at the corner of the box most favourable to it, the share is " + ("above the ceiling" if smallest_share > high_share else "below the floor")}
    scale_low = s_low if share(c_high, s_low) <= high_share else ga.bisect(lambda s: share(c_high, s) <= high_share, s_low, s_high)
    scale_high = s_high if share(c_low, s_high) >= low_share else ga.bisect(lambda s: share(c_low, s) >= low_share, s_low, s_high)
    c_min_at_top = c_low if share(c_low, s_high) <= high_share else ga.bisect(lambda c: share(c, s_high) <= high_share, c_low, c_high, 1e-8)
    rate_low = min(c * s for c, s in ((c_high, scale_low), (c_min_at_top, s_high)))
    rate_high = c_high * scale_high
    rises = {case_id: [prbc_rise(ctx, case_id, scale_high, fraction), prbc_rise(ctx, case_id, scale_low, fraction)] for case_id in CASES}
    return {**out, "status": _interval_status(scale_low, scale_high), "scale_ml_eq": [scale_low, scale_high], "bleed_rate_ml_min": [rate_low, rate_high],
            "c_at_the_largest_scale": [c_min_at_top, c_high], "one_unit_sbp_rise_mmHg": rises,
            "share_prevented": [max(low_share, smallest_share), min(high_share, largest_share)],
            "binding": {"smallest_scale": "the 35 % ceiling of the slow-crystalloid share" if scale_low > s_low * (1 + 1e-6) else "the +18 mmHg ceiling of one unit",
                        "largest_scale": "the +8 mmHg floor of one unit" if scale_high >= s_high * (1 - 1e-6) else "the 15 % floor of the slow-crystalloid share"}}


def kernel_fibre(ctx, a: dict, b: dict, fraction: float) -> dict:
    """How much of the CLOSED crystalloid region is compatible: walk the fibre of the least protective kernel (same s and tau, larger e), every point
    of which is inside the closed region by its own exact interval, and find the largest e that still leaves a feasible point."""
    import blood_volume_region as bvr
    import volume_behaviour_record as vbr
    e0, s, tau = ctx["kernels"]["CLOSED_REGION_LEAST_PROTECTIVE"]
    envelopes = {key: tuple(value) for key, value in vbr.EFFECTIVE_REGION.items()}
    e_low, e_high = bvr.e_interval(s, tau, envelopes, e_max=1.0)[:2]
    (_c_low, c_high), (_s_low, s_high) = a["common_c"], b["common_scale_ml_eq"]
    feasible = lambda e: slow_share(ctx, ga.FRG_CASE, c_high * s_high, s_high, (e, s, tau), fraction) <= SLOW_CRYSTALLOID_SHARE[1]      # noqa: E731
    start = max(e0, e_low * (1 + 1e-9))
    if not feasible(start):
        return {"status": "EMPTY", "fibre_e": [e_low, e_high]}
    largest = e_high if feasible(e_high * (1 - 1e-9)) else ga.bisect(feasible, start, e_high * (1 - 1e-9), 1e-7)
    retained = lambda e: fa.retained_ml(1000.0, 60, e, s, tau, 60)          # noqa: E731
    low_mark, high_mark = ctx["closed_region_retained_60_ml"]
    return {"status": "NONEMPTY", "fibre": {"s": s, "tau": tau, "e_inside_the_closed_region": [e_low, e_high]}, "largest_feasible_e": largest,
            "retained_at_60_ml_feasible": [retained(start), retained(largest)], "retained_at_60_ml_whole_closed_region": [low_mark, high_mark],
            "share_of_the_closed_region_span_compatible": (retained(largest) - low_mark) / (high_mark - low_mark),
            "the_most_retaining_kernel_of_the_region_is_compatible": retained(largest) >= high_mark * (1 - 1e-6)}


def window_reading_sensitivity(ctx, a: dict, b: dict, fraction: float) -> dict:
    """The STRICTER reading of the faculty window, as a sensitivity: the +8 mmHg floor already present at minute 15 (the start of the window, with half of the
    default unit in), the +18 mmHg ceiling still held at minute 30. The declared reading (P3-327A) takes both at minute 30, where the unit ends."""
    low_rise, early = PRBC_SBP_RISE_MMHG[0], PRBC_WINDOW_MIN[0]
    per_case = {case: [b["per_case_scale_ml_eq"][case][0],
                       ga.bisect(lambda scale, case=case: prbc_rise_at(ctx, case, scale, early, fraction) >= low_rise, 300.0, 20000.0)] for case in CASES}
    common = [max(item[0] for item in per_case.values()), min(item[1] for item in per_case.values())]
    strict = {"per_case_scale_ml_eq": per_case, "common_scale_ml_eq": common, "status": _interval_status(*common)}
    by_kernel = {}
    for name, kernel in ctx["kernels"].items():
        if strict["status"] == "EMPTY":
            by_kernel[name] = {"status": "EMPTY", "why": "the one-unit region itself is empty under this reading"}
            continue
        item = constraint_c(ctx, a, strict, kernel, fraction)
        by_kernel[name] = {key: item[key] for key in ("status", "share_at_the_least_protected_corner", "share_at_the_most_protected_corner", "scale_ml_eq", "bleed_rate_ml_min") if key in item}
    full_unit = {case: [prbc_rise(ctx, case, common[1], fraction), prbc_rise(ctx, case, common[0], fraction)] for case in CASES} if strict["status"] != "EMPTY" else None
    return {"reading": "the +8 mmHg floor required already at minute 15, the +18 mmHg ceiling at minute 30", "is_the_declared_reading": False,
            "B_one_unit_under_this_reading": strict, "full_unit_sbp_rise_at_30_mmHg_it_implies": full_unit, "C_slow_crystalloid_by_kernel": by_kernel,
            "status_with_the_closed_crystalloid_region": by_kernel["CLOSED_REGION_LEAST_PROTECTIVE"]["status"],
            "status_with_the_runtime_kernel_for_information": by_kernel["RUNTIME_OUTSIDE_THE_CLOSED_REGION"]["status"]}


def section_feasibility(ctx) -> dict:
    out = {}
    for fraction in (COMMITTED_FRACTION, SENSITIVITY_FRACTION):
        a, b = constraint_a(fraction), constraint_b(ctx, fraction)
        per_kernel = {name: constraint_c(ctx, a, b, kernel, fraction) for name, kernel in ctx["kernels"].items()}
        band = [max(b["common_scale_ml_eq"][0], ga.DECLARED_SCALE_BAND[0]), min(b["common_scale_ml_eq"][1], ga.DECLARED_SCALE_BAND[1])]
        inside_band = {}
        for name, kernel in ctx["kernels"].items():
            if band[1] < band[0]:
                inside_band[name] = {"status": "EMPTY", "why": "the one-unit region and the declared scale band do not overlap"}
                continue
            best = slow_share(ctx, ga.FRG_CASE, a["common_c"][1] * band[1], band[1], kernel, fraction)
            inside_band[name] = {"smallest_share_reachable": best, "status": "NONEMPTY" if best <= SLOW_CRYSTALLOID_SHARE[1] else "EMPTY"}
        out[f"{fraction}"] = {"A_untreated": a, "B_one_unit": b, "C_slow_crystalloid_by_kernel": per_kernel, "closed_region_fibre": kernel_fibre(ctx, a, b, fraction),
                              "A_x_B_bleed_rate_ml_min": [a["common_c"][0] * b["common_scale_ml_eq"][0], a["common_c"][1] * b["common_scale_ml_eq"][1]],
                              "inside_the_declared_scale_band": {"one_unit_region_within_the_band_ml_eq": band, "by_kernel": inside_band}}
    primary = out[f"{COMMITTED_FRACTION}"]
    closed = primary["C_slow_crystalloid_by_kernel"]["CLOSED_REGION_LEAST_PROTECTIVE"]
    stricter = window_reading_sensitivity(ctx, primary["A_untreated"], primary["B_one_unit"], COMMITTED_FRACTION)
    readable = None
    if closed.get("bleed_rate_ml_min"):
        limit = readable_rate_limit(primary["A_untreated"]["common_c"][1], closed["bleed_rate_ml_min"][0] * INWARD, closed["bleed_rate_ml_min"][1], ctx["kernels"]["CLOSED_REGION_LEAST_PROTECTIVE"])
        top_rate = closed["bleed_rate_ml_min"][1] if limit is None else limit
        readable = {"fastest_readable_bleed_rate_ml_min": limit, "limited_by": None if limit is None else "FD-BLD-06 in 57m: the frozen 140-minute crystalloid blood reading ends at the core's boundary (UNREADABLE, not failed)",
                    "bleed_rate_ml_min": [closed["bleed_rate_ml_min"][0], top_rate],
                    "scale_ml_eq": [closed["scale_ml_eq"][0], min(closed["scale_ml_eq"][1], top_rate / primary["A_untreated"]["common_c"][0])],
                    "status": _interval_status(closed["bleed_rate_ml_min"][0], top_rate)}
    return {"by_shared_arrival_position": out, "status": closed["status"] if readable is None else readable["status"],
            "three_anchors_only_status": closed["status"], "with_every_existing_constraint_readable_and_met": readable,
            "window_reading": {"declared": "both ends of the +8 .. +18 mmHg window are read at minute 30, where the default 30-minute unit ends and the whole response is present (P3-327A)",
                               "stricter_reading_as_a_sensitivity": stricter}, "status_is_for": "all three faculty anchors AND every existing constraint, the closed crystalloid region included, at the committed arrival position",
            "projections": {"bleed_rate_ml_min": closed.get("bleed_rate_ml_min"), "scale_ml_eq": closed.get("scale_ml_eq"), "c_rate_over_scale": primary["A_untreated"]["common_c"],
                            "one_unit_sbp_rise_mmHg": closed.get("one_unit_sbp_rise_mmHg"), "share_prevented_at_60": closed.get("share_prevented"),
                            "crystalloid_retained_at_60_ml": primary["closed_region_fibre"].get("retained_at_60_ml_feasible")},
            "relative_to_the_declared_scale_band": {"band_ml_eq": list(ga.DECLARED_SCALE_BAND), "band_status": "CANDIDATE (a declared domain, not evidence)",
                                                    "feasible_region_is_entirely_above_the_band": bool(closed.get("scale_ml_eq")) and closed["scale_ml_eq"][0] > ga.DECLARED_SCALE_BAND[1],
                                                    "smallest_feasible_scale_over_the_band_top": (closed["scale_ml_eq"][0] / ga.DECLARED_SCALE_BAND[1]) if closed.get("scale_ml_eq") else None},
            "relative_to_the_historical_reference": {"rate_ml_min": ctx["rate0"], "smallest_feasible_rate_over_it": (closed["bleed_rate_ml_min"][0] / ctx["rate0"]) if closed.get("bleed_rate_ml_min") else None,
                                                     "largest_feasible_rate_over_it": (closed["bleed_rate_ml_min"][1] / ctx["rate0"]) if closed.get("bleed_rate_ml_min") else None}}


# -- P3-330 .. P3-332: the witnesses ---------------------------------------------------------------------------------------------------------------------------

def _witness_points(ctx, feasibility) -> list:
    """Three TEST witnesses inside the feasible region of the closed-region kernel. They span it; none is a chosen point."""
    primary = feasibility["by_shared_arrival_position"][f"{COMMITTED_FRACTION}"]
    c_low, c_high = primary["A_untreated"]["common_c"]
    s_low, s_high = primary["C_slow_crystalloid_by_kernel"]["CLOSED_REGION_LEAST_PROTECTIVE"]["scale_ml_eq"]
    limit = (feasibility["with_every_existing_constraint_readable_and_met"] or {}).get("fastest_readable_bleed_rate_ml_min")
    c_top, c_bottom, c_middle = c_high / INWARD, c_low * INWARD, math.sqrt(c_low * c_high)
    high_scale = s_high / INWARD if limit is None else min(s_high / INWARD, limit / (c_bottom * INWARD))
    return [("LOW", c_top, s_low * INWARD, "the smallest feasible scale, at the fastest untreated course the envelopes admit: the largest one-unit response the region allows, the slow-crystalloid share at its 35 % ceiling"),
            ("CENTER", c_middle, math.sqrt(s_low * INWARD * high_scale), "the geometric middle of the feasible scales and of the admitted untreated courses"),
            ("HIGH", c_bottom, high_scale, "the largest feasible scale, at the slowest untreated course the envelopes admit (the nearest to the accepted one): the one-unit response near its +8 mmHg floor in 57m")]


def section_witnesses(ctx, feasibility) -> dict:
    kernel = ctx["kernels"]["CLOSED_REGION_LEAST_PROTECTIVE"]
    out = {}
    for label, c, scale, why in _witness_points(ctx, feasibility):
        rate = c * scale
        cases = {}
        for case in CASES:
            unit = prbc_rows(ctx, case, scale)
            treated, stop_t = run(ctx["slow"][case], 130, rate=rate, scale=scale, kernel=kernel)
            plain, stop_u = run(ctx["untreated"][case], 240, rate=rate, scale=scale, drop_fluid=True)
            accepted, _ = run(ctx["untreated"][case], 240, drop_fluid=True)
            share = {str(m): ga.protection(treated, plain, m) for m in (30, 60, 70, 120)}
            sbp = [row["sbp"] for row in plain]
            verdicts = frozen_verdicts(case, rate, scale, COMMITTED_FRACTION, kernel)
            cases[case] = {
                "one_unit_bleeding_controlled": {str(m): {"sbp": unit[m]["sbp"], "dbp": unit[m]["dbp"], "map": unit[m]["map"], "shadow_hr_non_authoritative": unit[m]["shadow_hr"],
                                                          "effective_volume_change_ml_eq": unit[m]["V"], "hb": unit[m]["hb"], "crt_s": unit[m]["crt_s"], "lactate": unit[m]["lactate"]}
                                                 for m in PRBC_READ_MINUTES},
                "one_unit_sbp_rise_at_30_mmHg": unit[30]["sbp"] - unit[0]["sbp"], "one_unit_sbp_rise_at_15_mmHg": unit[15]["sbp"] - unit[0]["sbp"],
                "one_unit_inside_FD_RATE_09": PRBC_SBP_RISE_MMHG[0] <= unit[30]["sbp"] - unit[0]["sbp"] <= PRBC_SBP_RISE_MMHG[1],
                "one_unit_not_instantaneous": 0.0 < unit[5]["sbp"] - unit[0]["sbp"] < 0.5 * (unit[30]["sbp"] - unit[0]["sbp"]),
                "one_unit_does_not_normalize_perfusion": bool(verdicts.get("FD-BLD-03", False)) and unit[30]["lactate"] > NON_SHOCK_LACTATE_UPPER and unit[30]["crt_s"] > 0.5 * unit[0]["crt_s"],
                "one_unit_below_the_too_large_mark": unit[30]["sbp"] - unit[0]["sbp"] < PRBC_TOO_LARGE_FROM_MMHG,
                "slow_crystalloid": {"untreated_sbp": {str(m): plain[m]["sbp"] for m in (30, 60, 70, 120)}, "treated_sbp": {str(m): treated[m]["sbp"] for m in (30, 60, 70, 120)},
                                     "untreated_deterioration_at_60_mmHg": plain[0]["sbp"] - plain[60]["sbp"], "treated_deterioration_at_60_mmHg": treated[0]["sbp"] - treated[60]["sbp"],
                                     "share_prevented": share, "retained_crystalloid_at_60_ml": treated[60]["net_retained_crystalloid_ml"], "blood_lost_by_60_ml": treated[60]["bleed_cum_ml"],
                                     "net_effective_volume_balance_at_60_ml": treated[60]["V"], "untreated_effective_volume_balance_at_60_ml": plain[60]["V"],
                                     "inside_FD_RATE_10": SLOW_CRYSTALLOID_SHARE[0] <= share["60"] <= SLOW_CRYSTALLOID_SHARE[1], "fades_after_the_infusion": share["120"] < share["60"],
                                     "bleeding_ml_min_distinct": sorted({round(row["bleed_ml_min"], 9) for row in treated[1:]}), "core_boundary_minute": stop_t},
                "untreated": {"sbp": {str(m): (plain[m]["sbp"] if m < len(plain) else None) for m in (60, 120, 180)},
                              "accepted_course_sbp": {str(m): accepted[m]["sbp"] for m in (60, 120, 180)},
                              "progressive_deterioration": all(later <= earlier + 1e-9 for earlier, later in zip(sbp, sbp[1:])),
                              "u_out_faculty_envelopes": ga.u_out(case, rate, scale, COMMITTED_FRACTION), "core_boundary_minute": stop_u,
                              "hb_fall_at_120": plain[0]["hb"] - plain[120]["hb"] if len(plain) > 120 else None},
                "existing_constraints_frozen_evaluator": verdicts,
                "every_existing_constraint_holds": verdicts.get("readable", False) and all(value for key, value in verdicts.items() if key != "readable")}
        ordering = all(cases["gi_bleed_57m"]["untreated"]["sbp"][m] < cases["gi_bleed_72f"]["untreated"]["sbp"][m] for m in ("60", "120") if cases["gi_bleed_57m"]["untreated"]["sbp"][m] is not None)
        out[label] = {"why": why, "bleed_rate_ml_min": rate, "scale_ml_eq": scale, "c_rate_over_scale": c, "arrival_position": COMMITTED_FRACTION,
                      "kernel": "CLOSED_REGION_LEAST_PROTECTIVE", "is_a_chosen_point": False, "cases": cases, "case_ordering_57m_below_72f": ordering,
                      "all_three_anchors_and_every_existing_constraint": ordering and all(item["one_unit_inside_FD_RATE_09"] and item["slow_crystalloid"]["inside_FD_RATE_10"]
                                                                                           and item["untreated"]["u_out_faculty_envelopes"] and item["every_existing_constraint_holds"]
                                                                                           and item["one_unit_not_instantaneous"] and item["one_unit_does_not_normalize_perfusion"]
                                                                                           and item["one_unit_below_the_too_large_mark"] for item in cases.values())}
    return out


# -- P3-333 .. P3-335: the intersection, the structure and the gate -------------------------------------------------------------------------------------

def section_structure(ctx, reduction, feasibility) -> dict:
    primary = feasibility["by_shared_arrival_position"][f"{COMMITTED_FRACTION}"]
    kernels = primary["C_slow_crystalloid_by_kernel"]
    closed, runtime = kernels["CLOSED_REGION_LEAST_PROTECTIVE"], kernels["RUNTIME_OUTSIDE_THE_CLOSED_REGION"]
    case = ga.FRG_CASE
    middle_rise = sum(PRBC_SBP_RISE_MMHG) / 2.0
    middle_share = sum(SLOW_CRYSTALLOID_SHARE) / 2.0
    middle_scale = ga.bisect(lambda scale: prbc_rise(ctx, case, scale) <= middle_rise, 300.0, 20000.0)
    c_low, c_high = primary["A_untreated"]["common_c"]
    at_middle = {name: [slow_share(ctx, case, c * middle_scale, middle_scale, kernel) for c in (c_low, c_high)] for name, kernel in ctx["kernels"].items()}
    upper_scale = primary["B_one_unit"]["common_scale_ml_eq"][0]
    at_strong_unit = slow_share(ctx, case, c_high * upper_scale, upper_scale, ctx["kernels"]["CLOSED_REGION_LEAST_PROTECTIVE"])
    return {"why_the_region_is_nonempty": "the two faculty windows are wide enough to overlap along the one line the physiology allows: with a closed-region kernel the share a slow litre prevents is about three times the one-unit gain, so a unit worth +8 to about +12 mmHg in 72f goes with a share of about 25 to 35 %",
            "where_it_sits": {"one_unit_window_used_mmHg_72f": closed.get("one_unit_sbp_rise_mmHg", {}).get(case), "faculty_window_mmHg": list(PRBC_SBP_RISE_MMHG),
                              "share_window_used": closed.get("share_prevented"), "faculty_share_window": list(SLOW_CRYSTALLOID_SHARE),
                              "reading": "a CORNER: the lower part of the one-unit window with the upper part of the slow-crystalloid window, and only the least-retaining part of the closed crystalloid region"},
            "the_middles_of_the_two_windows": {"one_unit_rise_mmHg": middle_rise, "scale_ml_eq": middle_scale, "share_wanted": middle_share, "share_given_at_that_scale_c_low_to_c_high": at_middle,
                                               "closed_region_kernel_reaches_the_middle_share": min(at_middle["CLOSED_REGION_LEAST_PROTECTIVE"]) <= middle_share,
                                               "runtime_kernel_reaches_the_middle_share": min(at_middle["RUNTIME_OUTSIDE_THE_CLOSED_REGION"]) <= middle_share <= max(at_middle["RUNTIME_OUTSIDE_THE_CLOSED_REGION"]) + 0.05,
                                               "reading": "the centres of the two faculty windows are mutually compatible only with a kernel that retains about as little as the runtime one, which is BELOW the floor of the closed crystalloid region"},
            "near_conflicts": [
                {"subset": ["B at its +18 mmHg end", "C", "the closed crystalloid region"], "empty": at_strong_unit > SLOW_CRYSTALLOID_SHARE[1], "measured_share": at_strong_unit,
                 "reading": "a unit worth +18 mmHg in 72f leaves a slow litre preventing this share with the least protective closed-region kernel"},
                {"subset": ["the declared CANDIDATE scale band", "B", "C", "the closed crystalloid region"],
                 "empty": primary["inside_the_declared_scale_band"]["by_kernel"]["CLOSED_REGION_LEAST_PROTECTIVE"]["status"] == "EMPTY",
                 "reading": "inside the declared band the three anchors cannot be met with a closed-region kernel; the band is a declared domain, not evidence"},
                {"subset": ["the most retaining kernel of the closed region", "A", "B", "C"], "empty": not primary["closed_region_fibre"].get("the_most_retaining_kernel_of_the_region_is_compatible", False),
                 "reading": "the more retaining part of the closed crystalloid region is incompatible with the three anchors"}],
            "structural_causes": {
                "A_one_effective_volume_channel": {"present": True, "does_it_empty_the_intersection": False,
                                                   "quantified": {name: item["retained_over_one_unit_volume"] for name, item in reduction["b_and_c_are_coupled_through_one_volume_channel"].items()},
                                                   "reading": "it is what makes the region a corner: a slow litre is worth 0.27 (runtime) to 0.45 (closed region, least) of a red-cell unit at 60 min, and B and C move together"},
                "B_no_infusion_rate_dependence_of_retention": {"present": True, "does_it_empty_the_intersection": False,
                                                              "reading": "the kernel is time-invariant (P3-303): a slow litre retains MORE at its own end than a bolus does at the same minute; it narrows the region, it does not empty it"},
                "C_pressure_map_cannot_hold_untreated_and_transfusion": {"present": False,
                                                                         "reading": "the map holds both: A fixes rate / scale and B fixes the scale, on separate coordinates"},
                "D_another_mechanism": {"present": False}},
            "runtime_kernel_for_information": {"status": runtime["status"], "bleed_rate_ml_min": runtime.get("bleed_rate_ml_min"), "scale_ml_eq": runtime.get("scale_ml_eq"),
                                               "note": "the runtime kernel is outside the closed crystalloid region (it fails FD-BLD-04 and FD-BLD-05): shown for information, not counted as feasible"}}


def decide(ctx, feasibility, witnesses, structure) -> dict:
    status = feasibility["status"]
    witnesses_hold = all(item["all_three_anchors_and_every_existing_constraint"] for item in witnesses.values())
    sensitivity = feasibility["by_shared_arrival_position"][f"{SENSITIVITY_FRACTION}"]["C_slow_crystalloid_by_kernel"]["CLOSED_REGION_LEAST_PROTECTIVE"]["status"]
    projections = feasibility["with_every_existing_constraint_readable_and_met"] or feasibility["projections"]
    widths = {name: (projections[name][1] / projections[name][0]) for name in ("bleed_rate_ml_min", "scale_ml_eq") if projections.get(name)}
    weak = any(value > 3.0 for value in widths.values())
    if status == "NONEMPTY" and witnesses_hold:
        verdict = "B" if weak else "A"
    elif status == "EMPTY":
        verdict = "C"
    else:
        verdict = "E"
    names = {"A": "CURRENT_PHYSIOLOGY_HAS_FEASIBLE_JOINT_REGION", "B": "JOINT_REGION_EXISTS_BUT_TOO_WEAKLY_IDENTIFIED",
             "C": "AMENDMENT_3_JUSTIFIED_BY_INCOMPATIBLE_BEHAVIORAL_CONSTRAINTS", "E": "INSUFFICIENT_INFORMATION"}
    stricter = feasibility["window_reading"]["stricter_reading_as_a_sensitivity"]["status_with_the_closed_crystalloid_region"]
    return {"intersection_status": status, "one_shared_family_region": status == "NONEMPTY", "case_specific_parameters_introduced": False,
            "witnesses_satisfy_everything": witnesses_hold, "status_at_the_sensitivity_position": sensitivity,
            "conditional_on_the_window_reading": {"declared_reading_status": status, "stricter_reading_status": stricter, "verdict_survives_the_stricter_reading": stricter == "NONEMPTY",
                                                  "needs_faculty_confirmation": stricter != status,
                                                  "reading": "the verdict is for the declared reading (the one-unit effect read at minute 30, where the unit ends); if the +8 mmHg floor had to be present already at minute 15, the status with the closed crystalloid region would be the stricter one"},
            "identification": {"largest_over_smallest": widths, "weakly_identified": weak},
            "amendment_3_gate": {"verdict": verdict, "name": names[verdict], "amendment_3": "NOT_JUSTIFIED__NOT_OPENED" if verdict in ("A", "B") else "SEE_VERDICT",
                                 "design_written": False,
                                 "exact_reason": "the current equations satisfy the untreated envelopes, the one-unit region and the slow-crystalloid region together, with every existing constraint and a kernel inside the closed crystalloid region; by FD-RATE-13 a nonempty feasible region means Amendment 3 is not opened",
                                 "what_the_region_costs": ["it lies entirely above the declared CANDIDATE band of the preload scale and at three to four times the historical bleed-rate reference",
                                                           "it is a corner: the lower part of the one-unit window, the upper part of the slow-crystalloid window, the least-retaining part of the closed crystalloid region",
                                                           "the current point satisfies neither new anchor; every treated trajectory changes magnitude at any feasible point, so FR-B, FR-C, FR-E and FR-G would all need a new blinded human review",
                                                           "applying any point needs a new pressure snapshot and a certified successor of the core, because the bleed rate is computed inside clinical_core and the scale band is declared there"],
                                 "why_not": {"B": "each coordinate is identified within a factor of about 1.2 to 1.4: the region is narrow, not weakly identified",
                                             "C": "the intersection is not empty", "D": "the pressure map holds the untreated course and the transfusion response on separate coordinates",
                                             "E": "the three anchors and the existing constraints decide it"}}}


def build() -> dict:
    ctx = build_context()
    mechanism = section_prbc_mechanism(ctx)
    reduction = section_reduction(ctx)
    feasibility = section_feasibility(ctx)
    witnesses = section_witnesses(ctx, feasibility)
    structure = section_structure(ctx, reduction, feasibility)
    record = {"record_type": "GI_JOINT_FEASIBILITY_ANALYSIS", "version": VERSION, "evidence_class": EVIDENCE_CLASS, "executable_change": False,
              "what_it_is": "A read-only feasibility and identifiability analysis of the three faculty anchors under the current GI physiology. MODEL_ANALYSIS: it approves no rate, no pressure parameter and no kernel, chooses no point, and is not clinical validation.",
              "depends_on": ctx["depends_on"],
              "faculty_anchors": {"FD-RATE-09": {"one_unit_sbp_rise_mmHg": list(PRBC_SBP_RISE_MMHG), "window_min": list(PRBC_WINDOW_MIN), "too_large_from_mmHg": PRBC_TOO_LARGE_FROM_MMHG,
                                                 "status": "FACULTY_DEFINED_DEVELOPMENT_BEHAVIORAL_REGION"},
                                  "FD-RATE-10": {"share_of_untreated_deterioration_prevented_at_60": list(SLOW_CRYSTALLOID_SHARE), "status": "FACULTY_DEFINED_DEVELOPMENT_BEHAVIORAL_REGION"},
                                  "FD-RATE-11": "no absolute bleed-rate point is approved: UNRESOLVED_ABSOLUTE_SCALE", "FD-RATE-12": "the closed crystalloid region is not modified",
                                  "FD-RATE-13": "Amendment 3 only if A, B and C cannot hold together"},
              "prbc_mechanism": mechanism, "reduction": reduction, "feasibility": feasibility, "witnesses": witnesses, "structure": structure,
              "decision": decide(ctx, feasibility, witnesses, structure)}
    record = fa._round(record)
    record["record_digest"] = digest(record)
    return record


def digest(record: dict) -> str:
    body = {key: value for key, value in record.items() if key != "record_digest"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=True).encode("utf-8")).hexdigest()


def load_record() -> dict:
    return json.loads(RECORD_PATH.read_text(encoding="utf-8"))


if __name__ == "__main__":
    result = build()
    if os.environ.get(WRITE_FLAG) == "1":
        RECORD_PATH.write_text(json.dumps(result, indent=1, sort_keys=True, ensure_ascii=False, allow_nan=True) + "\n", encoding="utf-8")
        print("written", RECORD_PATH, result["record_digest"])
    else:
        print(result["record_digest"], result["feasibility"]["status"], result["decision"]["amendment_3_gate"]["verdict"])
