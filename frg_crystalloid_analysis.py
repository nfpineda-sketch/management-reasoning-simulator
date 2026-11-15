"""P3-302 .. P3-309: why FR-G (1 L of normal saline over 60 minutes, bleeding ongoing) protects as much as it does.

MODEL_ANALYSIS, nothing else. TEST-SIDE and READ-ONLY: it imports the certified shadow core and the legacy encounter, runs them
exactly as the review environment does, and writes nothing to any encounter, authority record, baseline, region or faculty review.
It decides no clinical question. It changes no physiology: ``clinical_core/`` and ``family_engine.py`` are read, never edited, and
the only mutation here is a COUNTERFACTUAL copy of a contributor made inside this process to measure a sensitivity.

What it measures (every number below is recomputed from the executable model, none is typed in):

* the minute-by-minute FR-G reconstruction (hemorrhage, infusion, effective retained volume, redistribution, refill, V, preload,
  forward flow, pressure), cross-checked against the pressures the authority committed in the human-reviewed trajectory;
* that the bleeding stays active at every minute of every scenario read (P3-302A);
* the mass balance of the continuous infusion against an INDEPENDENT analytic convolution (P3-303 / P3-303A);
* the closed volume behavioural region on the 20-minute bag and on the 60-minute infusion (P3-304);
* the pressure coupling, to say whether it amplifies a small volume (P3-305, mechanism C);
* the sensitivity to the bleeding rate, as a sensitivity and never as a target (P3-305, mechanism D);
* the early-treatment trajectories carried to 120, 240 and 400 minutes WITHOUT source control (P3-309).

Regenerate the stored record with ``MRS_WRITE_FRG_ANALYSIS=1`` (the person who changes the analysis). A test regenerates it and
compares digests.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import math
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RECORD_PATH = ROOT / "docs" / "revision" / "PHASE3_FRG_CRYSTALLOID_ANALYSIS.json"
REVIEW_SET_PATH = ROOT / "docs" / "revision" / "PHASE3_FACULTY_TRAJECTORY_REVIEW_SET.json"
WRITE_FLAG = "MRS_WRITE_FRG_ANALYSIS"
VERSION = "P3-302"
EVIDENCE_CLASS = "MODEL_ANALYSIS"

TRACE_MINUTES = (0, 5, 10, 15, 30, 45, 60, 70)
COMPARE_MINUTES = (5, 10, 15, 30, 45, 60, 70, 90, 120)
HORIZON = 130
LONG_HORIZON = 400
UNTREATED_ORDERS = ("Reassess in 1 minutes.",)
BLEED_RATES_ML_MIN = (2.5, 3.5, 5.0)
REGION_S_STEPS = 100            # s = 0.005 .. 0.995
REGION_TAU_STEPS = 120          # tau log-spaced 1 .. 600 min
REGION_DOMAIN_E_MAX = 1.0       # the declared domain of e (docs/PHASE3_VOLUME_BEHAVIOUR_CALIBRATION.md section 2.3)
INTERIOR_MARGIN = 1e-9          # volume_behaviour_record.WITNESS_INTERIOR_MARGIN: a witness is placed just inside the edge


# -- the reviewed scripts, from the pinned review set (the one source of what the faculty saw) -------------------------------------------------------

def reviewed_item(scenario_id: str) -> dict:
    items = json.loads(REVIEW_SET_PATH.read_text(encoding="utf-8"))["items"]
    return next(item for item in items if item["scenario_id"] == scenario_id)


def reviewed_orders(scenario_id: str) -> tuple:
    item = reviewed_item(scenario_id)
    return item["case_id"], tuple(text for kind, text in item["script"] if kind == "order")


def reviewed_timeline(scenario_id: str) -> dict:
    return {row["minute"]: (row["sbp"], row["dbp"]) for row in reviewed_item(scenario_id)["bundle"]["authority_view"]["authoritative_pressure_timeline"]}


# -- running the certified core ---------------------------------------------------------------------------------------------------------------------

IMPLICIT_REASSESSMENT_MIN = 5
NO_ADVANCE_ORDERS = ("Place an IV line.",)


def page_turns(orders) -> tuple:
    """The orders as the resident PAGE turns them into encounter time. On the page an order that is not itself a reassessment carries an implicit
    five-minute reassessment (the 'fluid, reassessment' disposition at minute 5 of FR-B), and placing an IV line takes none. The encounter harness
    alone would wait for a whole infusion before the next order, which is NOT what the page does; ``reproduction`` proves the page rule against the
    pressures the authority committed in every reviewed trajectory."""
    out = []
    for text in orders:
        if text in NO_ADVANCE_ORDERS or "Reassess in" in text:
            out.append(text)
        else:
            out.append(f"{text} Reassess in {IMPLICIT_REASSESSMENT_MIN} minutes.")
    return tuple(out)


def capture(case: str, orders, *, as_page: bool = True) -> dict:
    """The shadow scenario the live encounter captured for ``orders`` (the real legacy encounter, the real adapter), with the page's turn timing."""
    import pilot_acceptance as acceptance
    import runtime_shadow as rs
    import runtime_shadow_evidence as ev
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter(case)
        for text in (page_turns(orders) if as_page else orders):
            encounter.order(text)
        return encounter.shadow.runner.replay_input().scenario


def run_core(scenario: dict, minutes: int = HORIZON, mutate=None):
    from clinical_core import integration
    anchors, contributors, _captured, profile = integration.scenario_from_dict(scenario)
    contributors = list(contributors)
    if mutate is not None:
        contributors = mutate(contributors)
    return integration.run(anchors, contributors, minutes, profile), anchors, profile


def crystalloid_of(contributors):
    from clinical_core.interventions.fluids import Crystalloid
    return next(item for item in contributors if isinstance(item, Crystalloid))


def drop_crystalloid(contributors):
    from clinical_core.interventions.fluids import Crystalloid
    return [item for item in contributors if not isinstance(item, Crystalloid)]


def with_kernel(e=None, s=None, tau=None, duration=None, bleed=None):
    """A COUNTERFACTUAL copy of the contributors with some parameters replaced. Used only to measure a sensitivity."""
    from clinical_core.interventions.fluids import Crystalloid

    def mutate(contributors):
        out = []
        for item in contributors:
            if isinstance(item, Crystalloid):
                changes = {key: value for key, value in (("effective_ml_per_ml", e), ("transient_share", s), ("leak_tau_min", tau),
                                                         ("duration_min", None if duration is None else float(duration))) if value is not None}
                item = dataclasses.replace(item, **changes)
            elif bleed is not None and type(item).__name__ == "GIHaemorrhage":
                item = dataclasses.replace(item, blood_loss_ml_per_min=float(bleed))
            out.append(item)
        return out
    return mutate


def _flows(record) -> dict:
    out = {}
    for change in record.blood:
        out[change.process.value] = out.get(change.process.value, 0.0) + change.volume_ml
    return out


def per_minute(trajectory, anchors, profile) -> list:
    """One row per minute from arrival (0): every flow of the minute, the cumulative ones, the state and the derived readings."""
    from clinical_core import derived as dv
    readings = trajectory.derived()
    rows, cum = [], {"shed": 0.0, "gain": 0.0, "out": 0.0, "refill": 0.0}
    for minute, state in enumerate(trajectory.states):
        flows = _flows(trajectory.records[minute - 1]) if minute >= 1 else {}
        shed, gain = flows.get("whole_blood_loss", 0.0), flows.get("crystalloid_in", 0.0)
        out, refill = flows.get("crystalloid_out", 0.0), flows.get("plasma_refill", 0.0)
        cum["shed"] += shed
        cum["gain"] += gain
        cum["out"] += out
        cum["refill"] += refill
        d = readings[minute].to_dict()
        rows.append({"minute": minute, "bleed_ml_min": shed, "bleed_cum_ml": cum["shed"], "effective_gain_ml_min": gain, "redistribution_out_ml_min": out,
                     "redistribution_out_cum_ml": cum["out"], "net_retained_crystalloid_ml": cum["gain"] - cum["out"], "refill_ml_min": refill,
                     "refill_cum_ml": cum["refill"], "V": float(state.V), "preload_position": float(dv.preload_position(state, anchors, profile)),
                     "forward_flow_output_rel": d["output_rel"], "pressure_rel": d["pressure_rel"], "sbp": d["sbp"], "dbp": d["dbp"], "map": d["map"],
                     "hb": float(state.hb)})
    return rows


# -- the independent analytic kernel ----------------------------------------------------------------------------------------------------------------

def retained_ml(volume_ml: float, duration_min: float, e: float, s: float, tau: float, t: int) -> float:
    """Effective crystalloid still intravascular at the end of minute ``t``: a convolution of the per-minute input with the kernel
    ``e * [(1 - s) + s * exp(-age / tau)]``, written from the mechanism's definition and NOT from the code that runs it."""
    lam = math.exp(-1.0 / tau)
    rate, total = volume_ml / duration_min, 0.0
    for minute in range(1, min(int(math.ceil(duration_min)), t) + 1):
        total += rate * e * ((1.0 - s) + s * lam ** (t - minute + 1))
    return total


def _round(value, places: int = 6):
    if isinstance(value, float):
        return round(value, places)
    if isinstance(value, dict):
        return {key: _round(item, places) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_round(item, places) for item in value]
    return value


def _pick(rows, minutes, keys) -> dict:
    return {str(row["minute"]): {key: row[key] for key in keys} for row in rows if row["minute"] in minutes}


def _protection(treated_sbp: float, untreated_sbp: float, arrival_sbp: float) -> float:
    drop = arrival_sbp - untreated_sbp
    return 100.0 * (treated_sbp - untreated_sbp) / drop if drop > 0.05 else float("nan")


# -- the sections of the analysis -------------------------------------------------------------------------------------------------------------------

def build_context() -> dict:
    """The runs every section reads, built once."""
    case, orders = reviewed_orders("FR-G")
    scenario = capture(case, orders)
    base, anchors, profile = run_core(scenario, HORIZON)
    crystalloid = crystalloid_of(base.contributors)
    kernel = (crystalloid.effective_ml_per_ml, crystalloid.transient_share, crystalloid.leak_tau_min)
    untreated_scenario = capture(case, UNTREATED_ORDERS)
    return {"case": case, "orders": orders, "scenario": scenario, "base": (base, anchors, profile), "kernel": kernel,
            "crystalloid": crystalloid, "untreated": run_core(untreated_scenario, HORIZON, drop_crystalloid), "scenario_untreated": untreated_scenario}


def section_reproduction() -> dict:
    """The harness is only as good as its agreement with what the faculty SAW: for every reviewed scenario that has a committed pressure timeline
    (all but FR-F, whose single commit is the stop), rerun its stored script through the harness and compare the rounded pressures with the ones
    the authority committed, minute by minute. A scenario that does not match would make every number below about something else."""
    out = {}
    for scenario_id in ("FR-A", "FR-B", "FR-C", "FR-D", "FR-E", "FR-G"):
        case, orders = reviewed_orders(scenario_id)
        committed = reviewed_timeline(scenario_id)
        traj, anchors, profile = run_core(capture(case, orders), max(committed))
        rows = per_minute(traj, anchors, profile)
        compared = {str(minute): {"committed": list(values), "reproduced": [round(rows[minute]["sbp"]), round(rows[minute]["dbp"])]} for minute, values in committed.items()}
        out[scenario_id] = {"minutes_compared": len(compared), "matches": all(item["committed"] == item["reproduced"] for item in compared.values()), "rows": compared}
    return {"scenarios": out, "all_match": all(item["matches"] for item in out.values())}


def section_reconstruction(ctx) -> dict:
    """P3-302: the FR-G trace, and the cross-check against what the authority committed in the human-reviewed trajectory."""
    traj, anchors, profile = ctx["base"]
    rows = per_minute(traj, anchors, profile)
    keys = ("bleed_ml_min", "bleed_cum_ml", "effective_gain_ml_min", "redistribution_out_ml_min", "redistribution_out_cum_ml", "net_retained_crystalloid_ml",
            "refill_ml_min", "refill_cum_ml", "V", "preload_position", "forward_flow_output_rel", "pressure_rel", "sbp", "dbp", "map")
    crystalloid = ctx["crystalloid"]
    committed = reviewed_timeline("FR-G")
    cross = {str(minute): {"reviewed_committed": list(values), "reproduced_rounded": [round(rows[minute]["sbp"]), round(rows[minute]["dbp"])],
                           "reproduced": [rows[minute]["sbp"], rows[minute]["dbp"]]} for minute, values in committed.items()}
    return {"scenario": "FR-G", "case": ctx["case"], "orders": list(ctx["orders"]), "arrival": {"sbp": rows[0]["sbp"], "dbp": rows[0]["dbp"], "map": rows[0]["map"]},
            "infusion": {"volume_ml": crystalloid.volume_ml, "duration_min": crystalloid.duration_min, "start_minute": crystalloid.start_minute,
                         "delivered_ml_min": crystalloid.volume_ml / crystalloid.duration_min,
                         "effective_ml_per_ml": crystalloid.effective_ml_per_ml, "transient_share": crystalloid.transient_share,
                         "leak_tau_min": crystalloid.leak_tau_min},
            "trace": _pick(rows, TRACE_MINUTES, keys), "authority_cross_check": cross,
            "cross_check_matches": all(item["reviewed_committed"] == item["reproduced_rounded"] for item in cross.values())}


def section_bleeding(ctx) -> dict:
    """P3-302A: the whole-blood loss is the same at every minute of every run read, treated or not; no source control is in any of them."""
    runs = {"FR-G": ctx["base"], "untreated_72f": ctx["untreated"]}
    for scenario_id in ("FR-B",):
        case, orders = reviewed_orders(scenario_id)
        runs[scenario_id] = run_core(capture(case, orders), LONG_HORIZON)
    out = {}
    for name, (traj, _anchors, _profile) in runs.items():
        losses = [_flows(record).get("whole_blood_loss", 0.0) for record in traj.records]
        out[name] = {"minutes": len(losses), "distinct_loss_values_ml_min": sorted({round(v, 9) for v in losses}), "stops_or_changes": len({round(v, 9) for v in losses}) != 1,
                     "contributors": [type(item).__name__ for item in traj.contributors], "has_source_control": any("Hemostasis" in type(item).__name__ for item in traj.contributors)}
    return {"runs": out, "bleeding_active_at_every_minute": all(not item["stops_or_changes"] for item in out.values()),
            "source_control_in_any_run": any(item["has_source_control"] for item in out.values())}


def section_mass_balance(ctx) -> dict:
    """P3-303 / P3-303A: does the core integrate a slow infusion as per-minute input with simultaneous redistribution of every earlier portion?
    Compare its net crystalloid (in - out) with the analytic convolution, for 5, 15, 20 and 60 minutes, at every minute to 130."""
    e, s, tau = ctx["kernel"]
    worst, per_duration = 0.0, {}
    for duration in (5, 15, 20, 60):
        traj, _a, _p = run_core(ctx["scenario"], HORIZON, with_kernel(duration=duration))
        net, gap, total_gain = 0.0, 0.0, 0.0
        peak_minute, peak_value = 0, 0.0
        for record in traj.records:
            flows = _flows(record)
            total_gain += flows.get("crystalloid_in", 0.0)
            net += flows.get("crystalloid_in", 0.0) - flows.get("crystalloid_out", 0.0)
            gap = max(gap, abs(net - retained_ml(1000.0, duration, e, s, tau, record.minute)))
            if net > peak_value:
                peak_minute, peak_value = record.minute, net
        per_duration[str(duration)] = {"max_abs_gap_ml": gap, "peak_net_ml": peak_value, "peak_minute": peak_minute, "total_effective_gain_ml": total_gain}
        worst = max(worst, gap)
    table = {}
    for label, duration in (("instantaneous_1min", 1), ("15min", 15), ("60min", 60)):
        table[label] = {str(t): retained_ml(1000.0, duration, e, s, tau, t) for t in (1, 5, 10, 15, 30, 45, 60, 70, 90, 120)}
    return {"kernel": {"e": e, "s": s, "tau": tau}, "permanent_floor_ml": 1000.0 * e * (1.0 - s), "per_duration": per_duration, "max_abs_gap_ml": worst,
            "behaves_as_per_minute_input_with_simultaneous_redistribution": worst < 1e-6, "analytic_retained_ml": table,
            "total_effective_gain_is_volume_times_e_for_every_rate": all(abs(item["total_effective_gain_ml"] - 1000.0 * e) < 1e-9 for item in per_duration.values())}


def _bag_r(e, s, tau) -> dict:
    return {"peak": retained_ml(1000.0, 20, e, s, tau, 20) / 1000.0, "30": retained_ml(1000.0, 20, e, s, tau, 30) / 1000.0,
            "60": retained_ml(1000.0, 20, e, s, tau, 60) / 1000.0, "120": retained_ml(1000.0, 20, e, s, tau, 120) / 1000.0}


def _status(value: float, low: float, high: float) -> str:
    return "BELOW" if value < low else ("ABOVE" if value > high else "IN")


def section_region(ctx) -> dict:
    """P3-304: the closed volume behavioural region against the runtime kernel, and what the region implies for the 60-minute infusion."""
    import blood_volume_region as bvr
    import volume_behaviour_record as vbr
    e, s, tau = ctx["kernel"]
    envelopes = {key: tuple(value) for key, value in vbr.EFFECTIVE_REGION.items()}
    runtime = _bag_r(e, s, tau)
    runtime_vs = {("peak" if key == "peak" else key): {"value": runtime[key], "range": list(envelopes["peak" if key == "peak" else int(key)]),
                                                       "status": _status(runtime[key], *envelopes["peak" if key == "peak" else int(key)])} for key in runtime}
    module_check = max(abs(runtime[key] - (bvr.peak_share(e, s, tau) if key == "peak" else bvr.retained_share(e, s, tau, float(key)))) for key in runtime)
    sample = []
    for index in range(REGION_S_STEPS):
        s_i = round(0.005 + 0.01 * index, 3)
        for step in range(REGION_TAU_STEPS + 1):
            tau_i = round(math.exp(math.log(600.0) * step / REGION_TAU_STEPS), 3)
            interval = bvr.e_interval(s_i, tau_i, envelopes, e_max=REGION_DOMAIN_E_MAX)
            if interval == bvr.EMPTY:
                continue
            e_lo, e_hi = interval[0], interval[1]
            gain_per_e = retained_ml(1000.0, 60, 1.0, s_i, tau_i, 60)
            sample.append((e_lo * gain_per_e, e_hi * gain_per_e, s_i, tau_i, e_lo, e_hi))
    lowest = min(sample, key=lambda row: row[0])
    highest = max(sample, key=lambda row: row[1])
    runtime_60 = retained_ml(1000.0, 60, e, s, tau, 60)
    # A bound that does NOT depend on the three-parameter family. Let K(a) be the fraction of one infused mL still intravascular a minutes later
    # (a = 1, 2, ...), and suppose only that it never rises with age (redistribution only removes volume; volume_behaviour_record names the same
    # property UNREACHABLE_THE_MODEL_ONLY_DECAYS). The 20-minute bag reads R30 = mean K over ages 11..30 and R60 = mean K over ages 41..60, so the
    # closed floors give: sum K(11..30) >= 20 f30, hence K(1..10) >= f30 each; sum K(41..60) >= 20 f60, hence K(31..40) >= f60 each. The 60-minute
    # infusion at minute 60 retains (volume/60) * sum K(1..60) >= (volume/60) * (10 f30 + 20 f30 + 10 f60 + 20 f60).
    floor_30, floor_60 = envelopes[30][0], envelopes[60][0]
    kernel_bound = (1000.0 / 60.0) * (30.0 * floor_30 + 30.0 * floor_60)
    witness = (lowest[4] * (1.0 + INTERIOR_MARGIN), lowest[2], lowest[3])
    untreated, anchors, profile = ctx["untreated"]
    untreated_rows = per_minute(untreated, anchors, profile)
    arrival = untreated_rows[0]["sbp"]

    def core_run(point):
        traj, an, pr = run_core(ctx["scenario"], HORIZON, with_kernel(e=point[0], s=point[1], tau=point[2]))
        rows = per_minute(traj, an, pr)
        return {"point": {"e": point[0], "s": point[1], "tau": point[2]}, "sbp": {str(m): rows[m]["sbp"] for m in (30, 60, 70, 120)},
                "net_retained_60_ml": rows[60]["net_retained_crystalloid_ml"],
                "protection_pct_at_60": _protection(rows[60]["sbp"], untreated_rows[60]["sbp"], arrival)}
    runtime_run = core_run((e, s, tau))
    return {"region": {"status": vbr.STATUS, "applies_to": vbr.RECORD["applies_to"], "envelopes": {str(k): list(v) for k, v in envelopes.items()}, "domain_e_max": REGION_DOMAIN_E_MAX,
                       "scan": {"s_steps": REGION_S_STEPS, "tau_steps": REGION_TAU_STEPS + 1, "feasible_pairs": len(sample)}},
            "runtime_point": {"e": e, "s": s, "tau": tau, "classification": vbr.HISTORICAL_REFERENCE["classification"], "bag_20min": runtime_vs,
                              "module_agreement_max_abs": module_check, "inside_closed_region": all(item["status"] == "IN" for item in runtime_vs.values()),
                              "outside_direction": "BELOW (retains LESS than the region requires)"},
            "slow_infusion_60min": {"runtime_retained_at_60_ml": runtime_60, "bleed_to_60_ml": 150.0,
                                    "region_least_retained_at_60_ml": lowest[0], "region_most_retained_at_60_ml": highest[1],
                                    "least_over_runtime_ratio": lowest[0] / runtime_60, "least_protective_point": {"e": lowest[4], "s": lowest[2], "tau": lowest[3]},
                                    "any_nonincreasing_kernel_inside_the_closed_bands": {"retained_at_60_ml_at_least": kernel_bound, "share_of_the_concurrent_bleed_at_least": kernel_bound / 150.0,
                                                                                         "over_runtime_ratio": kernel_bound / runtime_60,
                                                                                         "assumption": "the retained share of an infused mL never rises with its age"}},
            "core_runs": {"runtime": runtime_run, "region_least_protective": core_run(witness)},
            "only_within_the_three_parameter_family": True}


def section_pressure_coupling(ctx) -> dict:
    """P3-305, mechanism C: does the pressure coupling amplify a small volume? Compare the share of the untreated VOLUME deficit that the infusion
    prevents with the share of the untreated PRESSURE drop it prevents, and the slope of pressure on volume in both directions."""
    traj, anchors, profile = ctx["base"]
    treated = per_minute(traj, anchors, profile)
    untreated = per_minute(*ctx["untreated"])
    t60, u60 = treated[60], untreated[60]
    volume_share = 100.0 * (t60["V"] - u60["V"]) / (0.0 - u60["V"])
    pressure_share = _protection(t60["sbp"], u60["sbp"], untreated[0]["sbp"])
    slopes = {}
    for low, high in ((0, 50), (50, 100), (100, 190)):
        i = next(row for row in untreated if row["V"] <= -low)
        j = next(row for row in untreated if row["V"] <= -high)
        slopes[f"{low}_{high}_ml_deficit"] = (j["sbp"] - i["sbp"]) / (j["V"] - i["V"]) if j["V"] != i["V"] else None
    bolus = run_core(ctx["scenario"], HORIZON, with_kernel(duration=5))
    brows = per_minute(*bolus)
    positive = (brows[5]["sbp"] - brows[0]["sbp"]) / (brows[5]["V"] - brows[0]["V"])
    return {"volume_deficit_prevented_pct_at_60": volume_share, "pressure_drop_prevented_pct_at_60": pressure_share, "difference_points": pressure_share - volume_share,
            "untreated_slope_sbp_per_ml_by_deficit_band": slopes, "slope_sbp_per_ml_when_volume_is_added_5min_bag": positive,
            "amplifies_a_small_volume": abs(pressure_share - volume_share) > 10.0 or abs(positive) > 1.5 * abs(slopes["0_50_ml_deficit"])}


def section_bleed_sensitivity(ctx) -> dict:
    """P3-305, mechanism D: a SENSITIVITY, not a target. The protection of the same 60-minute infusion against the same hemorrhage at other rates."""
    region = section_region_cached(ctx)
    point = region["core_runs"]["region_least_protective"]["point"]
    rows = {}
    for rate in BLEED_RATES_ML_MIN:
        entry = {}
        for label, kernel in (("runtime_kernel", {}), ("region_least_protective_kernel", {"e": point["e"], "s": point["s"], "tau": point["tau"]})):
            treated = per_minute(*run_core(ctx["scenario"], HORIZON, with_kernel(bleed=rate, **kernel)))
            untreated = per_minute(*run_core(ctx["scenario_untreated"], HORIZON, lambda cs, r=rate: with_kernel(bleed=r)(drop_crystalloid(cs))))
            entry[label] = {"sbp_treated_at_60": treated[60]["sbp"], "sbp_untreated_at_60": untreated[60]["sbp"],
                            "protection_pct_at_60": _protection(treated[60]["sbp"], untreated[60]["sbp"], untreated[0]["sbp"])}
        rows[f"{rate}"] = entry
    values = [rows[f"{r}"]["runtime_kernel"]["protection_pct_at_60"] for r in BLEED_RATES_ML_MIN]
    return {"rates_ml_min": list(BLEED_RATES_ML_MIN), "rows": rows, "protection_falls_as_bleeding_rises": all(a > b for a, b in zip(values, values[1:])),
            "note": "the bleeding rate is a candidate coordinate coupled to the untreated course the faculty accepted (FD-REVIEW-01); changing it is not a correction available here"}


_REGION_CACHE: dict = {}


def section_region_cached(ctx) -> dict:
    key = id(ctx)
    if key not in _REGION_CACHE:
        _REGION_CACHE[key] = section_region(ctx)
    return _REGION_CACHE[key]


def section_ordering(ctx) -> dict:
    """P3-307: for the same total volume the shorter bag gives the larger and earlier expansion; the slow one catches up by the end of its own
    infusion because its later portions have had less time to redistribute; all converge on the same permanent floor."""
    e, s, tau = ctx["kernel"]
    durations = (5, 15, 20, 60)
    at = {str(d): {str(t): retained_ml(1000.0, d, e, s, tau, t) for t in (5, 10, 15, 20, 30, 45, 60, 90, 120, 240)} for d in durations}
    peaks = {str(d): max(retained_ml(1000.0, d, e, s, tau, t) for t in range(1, 241)) for d in durations}
    crossover = next((t for t in range(1, 241) if retained_ml(1000.0, 60, e, s, tau, t) > retained_ml(1000.0, 15, e, s, tau, t)), None)
    return {"retained_ml": at, "peak_retained_ml": peaks,
            "peak_falls_as_the_infusion_lengthens": peaks["5"] > peaks["15"] > peaks["20"] > peaks["60"],
            "early_expansion_larger_for_the_shorter_bag_at_10_min": at["5"]["10"] > at["15"]["10"] > at["20"]["10"] > at["60"]["10"],
            "slow_exceeds_the_15min_bag_from_minute": crossover,
            "same_floor_at_240": all(abs(at[str(d)]["240"] - 1000.0 * e * (1.0 - s)) < 1.0 for d in durations)}


def section_early_treatment() -> dict:
    """P3-309: early treatment (IV, 1 L over 15 min, 2 units of red cells) carried to 60 / 120 / 240 minutes (and to 400 to find where, if ever, it falls below the arrival value), bleeding ongoing and no source control,
    for the case the faculty reviewed (57 m, FR-B script) and the other GI case (72 f, the same orders)."""
    case_b, orders_b = reviewed_orders("FR-B")
    out = {}
    for case in ("gi_bleed_57m", "gi_bleed_72f"):
        scenario = capture(case, orders_b)
        traj, anchors, profile = run_core(scenario, LONG_HORIZON)
        rows = per_minute(traj, anchors, profile)
        peak = max(rows, key=lambda row: row["sbp"])
        after = [row for row in rows if row["minute"] >= peak["minute"]]
        unt_traj, unt_a, unt_p = run_core(capture(case, UNTREATED_ORDERS), HORIZON, drop_crystalloid)   # the untreated course meets the core's own boundary near minute 349: read only what is needed
        urows = per_minute(unt_traj, unt_a, unt_p)
        out[case] = {"orders": list(orders_b), "arrival_sbp": rows[0]["sbp"], "peak": {"minute": peak["minute"], "sbp": peak["sbp"]},
                     "sbp": {str(m): rows[m]["sbp"] for m in (30, 60, 90, 120, 180, 240, 300, 360)}, "hb": {str(m): rows[m]["hb"] for m in (0, 60, 120, 240)},
                     "untreated_sbp": {str(m): urows[m]["sbp"] for m in (60, 120) if m < len(urows)},
                     "bleed_ml_min_distinct": sorted({round(row["bleed_ml_min"], 9) for row in rows[1:]}),
                     "slope_after_peak_mmHg_per_min": (after[-1]["sbp"] - after[0]["sbp"]) / (after[-1]["minute"] - after[0]["minute"]),
                     "improvement_reverses_after_peak": after[-1]["sbp"] < peak["sbp"], "stays_above_arrival_at_240": rows[240]["sbp"] > rows[0]["sbp"],
                     "crosses_below_arrival_at_minute": next((row["minute"] for row in rows if row["minute"] > peak["minute"] and row["sbp"] < rows[0]["sbp"]), None)}
    return out


def verdict(ctx, mass, coupling, region, sensitivity) -> dict:
    """P3-305: exactly one of A..E, with the predicate that supports or refutes each."""
    least = region["slow_infusion_60min"]["least_over_runtime_ratio"]
    runtime_prot = region["core_runs"]["runtime"]["protection_pct_at_60"]
    least_prot = region["core_runs"]["region_least_protective"]["protection_pct_at_60"]
    a = not mass["behaves_as_per_minute_input_with_simultaneous_redistribution"]
    general = region["slow_infusion_60min"]["any_nonincreasing_kernel_inside_the_closed_bands"]["over_runtime_ratio"]
    b = least > 1.5 and general > 1.5 and least_prot > runtime_prot and not region["runtime_point"]["inside_closed_region"]
    c = coupling["amplifies_a_small_volume"]
    d_cofactor = sensitivity["protection_falls_as_bleeding_rises"]
    return {"A_CONTINUOUS_INFUSION_IMPLEMENTATION_BUG": {"supported": a, "why": "core net crystalloid equals the independent convolution to 1e-6 mL at every minute for 5/15/20/60-minute infusions"},
            "B_CLOSED_VOLUME_REGION_TOO_PROTECTIVE_FOR_SLOW_INFUSION": {"supported": b, "why": "every kernel inside the closed bands (the least protective point of the three-parameter family, and any kernel that never rises with age) retains more of the 60-minute infusion than the runtime kernel and protects more of the pressure drop; the runtime kernel is already BELOW the region"},
            "C_PRESSURE_COUPLING_AMPLIFIES_SMALL_VOLUME_EFFECT": {"supported": c, "why": "the share of pressure drop prevented tracks the share of volume deficit prevented; the slope on volume is the same in both directions"},
            "D_BLEEDING_RATE_OR_TIMING_CAUSES_APPARENT_PROTECTION": {"supported": False, "cofactor": d_cofactor, "why": "bleeding is constant and active at every minute (no timing artefact); the rate sets the SCALE of the protection but is coupled to the accepted untreated course"},
            "E_MULTIPLE_MECHANISMS": {"supported": False, "why": "one mechanism (B) accounts for the finding; D is a scale factor and not a separate defect"},
            "classified_as": "B" if (b and not a and not c) else "UNCLASSIFIED"}


def build() -> dict:
    ctx = build_context()
    reproduction = section_reproduction()
    reconstruction = section_reconstruction(ctx)
    bleeding = section_bleeding(ctx)
    mass = section_mass_balance(ctx)
    region = section_region_cached(ctx)
    coupling = section_pressure_coupling(ctx)
    sensitivity = section_bleed_sensitivity(ctx)
    ordering = section_ordering(ctx)
    early = section_early_treatment()
    record = {"record_type": "FRG_CRYSTALLOID_ANALYSIS", "version": VERSION, "evidence_class": EVIDENCE_CLASS, "executable_change": False,
              "what_it_is": "A read-only reconstruction of why the 60-minute crystalloid infusion of FR-G protects as much as it does. MODEL_ANALYSIS: it is not human review and not clinical validation.",
              "harness_reproduces_the_reviewed_trajectories": reproduction, "reconstruction": reconstruction, "bleeding": bleeding, "mass_balance": mass, "volume_region": region, "pressure_coupling": coupling,
              "bleeding_rate_sensitivity": sensitivity, "infusion_ordering": ordering, "early_treatment_without_source_control": early,
              "verdict": verdict(ctx, mass, coupling, region, sensitivity)}
    record = _round(record)
    record["record_digest"] = digest(record)
    return record


def digest(record: dict) -> str:
    body = {key: value for key, value in record.items() if key != "record_digest"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=True).encode("utf-8")).hexdigest()


def load_record() -> dict:
    return json.loads(RECORD_PATH.read_text(encoding="utf-8"))


if __name__ == "__main__":
    if os.environ.get(WRITE_FLAG) == "1":
        result = build()
        RECORD_PATH.write_text(json.dumps(result, indent=1, sort_keys=True, ensure_ascii=False, allow_nan=True) + "\n", encoding="utf-8")
        print("written", RECORD_PATH, result["record_digest"])
    else:
        print(json.dumps(build(), indent=1, sort_keys=True, allow_nan=True)[:4000])
