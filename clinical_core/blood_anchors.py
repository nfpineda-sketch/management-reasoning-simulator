"""P2I-2U: patient-level faculty anchors for the shared haemorrhage state (decision support only).

    python -m clinical_core.blood_anchors [--out <directory outside the repository>]
    python -m clinical_core.blood_anchors --write <document> --json <anchors JSON>

Shadow, offline and read-only. The shared blood state's internal constants (B0, kappa, lambda,
refill target / capacity / tau, the red-cell unit's content and volume, crystalloid retention) are
never put to faculty on their own: this module shows what patient-level trajectories they produce,
so that faculty can later set patient-level envelopes (FD-BLD-01..09 and the untreated anchors
A-D), and says which of those constants each envelope would actually constrain.

Every value it explores is SYNTHETIC (an exploration range, not a candidate band, not approved);
the reference is the canonical provisional profile. Kappa is held at 1 and the preload scale is
explored as lambda / kappa, the only identifiable combination. Oxygen is read with the P2I-2P
candidate reserve 2.5 and the GI arrival band re-anchored (ratio / reserve); lactate is context
only (the P2F midpoint kinetics) and is never a calibration target here. Nothing is ranked by
similarity to the family engine; no FD-LAC rule or filter runs; no value is chosen or approved.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from dataclasses import replace
from pathlib import Path

from . import calibration, gi_reference, lactate_slice
from .bands import BloodLoss
from .derived import (DEFAULT_PROFILE, blood_haemoglobin, derive, effective_delivery, oxygen_balance,
                      preload_position)
from .integration import run
from .logistics import EndoscopicHemostasis
from .state import UnresolvedBoundary

CASES = gi_reference.GI_CASES
TIMES = (0, 30, 60, 120)
REFILL_TIMES = (30, 60, 120, 240)
#: P2I-2P candidate reserve (band 2.0-3.0), not approved; the GI arrival ratio is read as band / reserve.
RESERVE = 2.5
#: Lactate context only: the P2F midpoint kinetics (P2G's "medio" representative). Not a calibration target.
KINETICS = {"debt_clearance_tau_min": 60.0, "lactate_clearance_tau_min": 120.0, "lactate_per_output_deficit": 6.0}
#: The reference: the canonical provisional values (P2I-2T), the case band midpoints and the P2I-2P reserve.
REFERENCE = {"bleed_ml_per_min": 2.5, "arrival_circulating_volume_ml": 4000.0,
             "preload_scale_over_kappa_ml": DEFAULT_PROFILE.preload_curve_scale_ml, "preload_fraction": "midpoint",
             "plasma_refill_target_share": 0.5, "plasma_refill_tau_min": 120.0, "plasma_refill_capacity_ml": 1000.0,
             "red_cell_unit_hb_g_dl": 20.0, "red_cell_unit_volume_ml": 300.0, "crystalloid_effective_ml_per_ml": 0.125,
             "crystalloid_leak_tau_min": 30.0, "crystalloid_transient_share": 0.6, "reserve": RESERVE}
#: SYNTHETIC exploration ranges: neither candidate bands nor approved values. "preload_fraction" walks the
#: case band; the preload scale reuses the registry band of preload_curve_scale_ml, read as lambda / kappa.
EXPLORATION = {"bleed_ml_per_min": (1.25, 2.5, 5.0),
               "arrival_circulating_volume_ml": (3000.0, 4000.0, 5000.0),
               "preload_scale_over_kappa_ml": tuple(calibration.REGISTRY["preload_curve_scale_ml"].points()),
               "preload_fraction": ("lower", "midpoint", "upper"),
               "plasma_refill_target_share": (0.25, 0.5, 0.75),
               "plasma_refill_tau_min": (60.0, 120.0, 240.0),
               "plasma_refill_capacity_ml": (100.0, 500.0, 1000.0),
               "red_cell_unit_hb_g_dl": (18.0, 20.0, 22.0),
               "red_cell_unit_volume_ml": (250.0, 300.0, 350.0),
               "crystalloid_effective_ml_per_ml": (0.125, 0.2, 0.3),
               "crystalloid_leak_tau_min": (15.0, 30.0, 60.0),
               "crystalloid_transient_share": (0.4, 0.6, 0.8),
               "reserve": (1.0, 2.5, 3.0)}
#: Which dimensions each decision surface walks in full (the others stay at the reference).
UNTREATED_GRID = ("bleed_ml_per_min", "arrival_circulating_volume_ml", "preload_scale_over_kappa_ml",
                  "preload_fraction", "plasma_refill_target_share")
RED_CELL_GRID = ("red_cell_unit_hb_g_dl", "red_cell_unit_volume_ml", "preload_scale_over_kappa_ml",
                 "preload_fraction", "arrival_circulating_volume_ml")
CRYSTALLOID_GRID = ("crystalloid_effective_ml_per_ml", "crystalloid_leak_tau_min", "crystalloid_transient_share",
                    "preload_scale_over_kappa_ml", "arrival_circulating_volume_ml", "preload_fraction")
REFILL_GRID = ("plasma_refill_target_share", "plasma_refill_tau_min", "plasma_refill_capacity_ml",
               "arrival_circulating_volume_ml")
#: The refill surfaces: a synthetic acute loss (not a GI rate), and the GI bleed stopped completely at 60 min.
ACUTE_LOSS_ML, ACUTE_LOSS_MIN, HAEMOSTASIS_AT = 200.0, 10, 60
CRYSTALLOID_VOLUMES = (1000.0, 2000.0)
#: Added circulating volume used to read preload responsiveness (mL-eq, kappa x this in V).
RESPONSIVENESS_ML = 100.0


# Runs ---------------------------------------------------------------------------------------------------

def _values(case: str, **changes) -> dict:
    values = {**REFERENCE, **changes}
    band = gi_reference.case_bands(case)["preload_fraction"]
    if isinstance(values["preload_fraction"], str):
        values["preload_fraction"] = {"lower": band.lower, "midpoint": band.midpoint,
                                      "upper": band.upper}[values["preload_fraction"]]
    return values


def setup(case: str, kappa: float = 1.0, **changes):
    """The case's midpoint arrival and the profile a set of shared-blood values gives (kappa 1 by default)."""
    values = _values(case, **changes)
    case_values = calibration.case_values(case, calibration.GICandidate({}))
    case_values["preload_fraction"] = values["preload_fraction"]
    case_values["arrival_delivery_ratio"] /= values["reserve"]
    anchors = gi_reference.candidate_anchors(case, case_values)
    profile = replace(DEFAULT_PROFILE, **KINETICS, oxygen_extraction_reserve=values["reserve"],
                      arrival_circulating_volume_ml=values["arrival_circulating_volume_ml"],
                      volume_preload_kappa=kappa, preload_curve_scale_ml=kappa * values["preload_scale_over_kappa_ml"],
                      plasma_refill_target_share=values["plasma_refill_target_share"],
                      plasma_refill_tau_min=values["plasma_refill_tau_min"],
                      plasma_refill_capacity_ml=values["plasma_refill_capacity_ml"])
    return anchors, profile, values


def _templates(case: str) -> dict:
    items = {type(item).__name__: item for scenario in (lactate_slice.L1, lactate_slice.L2, lactate_slice.L3)
             for item in lactate_slice.scenario_inputs(case, scenario)}
    return {"bleed": items["GIHaemorrhage"], "bag": items["Crystalloid"], "unit": items["PackedRedCells"]}


def contributors(case: str, scenario: str, values: dict, volume_ml: float | None = None) -> tuple:
    """The inputs of one surface, built from the frozen family-engine path's own contributors."""
    made = _templates(case)
    bleed = replace(made["bleed"], blood_loss_ml_per_min=values["bleed_ml_per_min"])
    if scenario == "untreated":
        return (bleed,)
    if scenario == "red_cells":
        # Bleeding controlled: one unit over 0-30 min, the second over 30-60 min.
        return (replace(made["unit"], id="anchor-prbc", start_minute=0, units=2.0, duration_min=60.0,
                        stop_minute=None, queued_ahead_units=0.0, volume_ml_per_unit=values["red_cell_unit_volume_ml"],
                        unit_hb_g_dl=values["red_cell_unit_hb_g_dl"]),)
    if scenario == "crystalloid":
        return (bleed, replace(made["bag"], id="anchor-saline", start_minute=0, volume_ml=volume_ml, duration_min=20.0,
                               stop_minute=None, stopped_by=None, queued_ahead_ml=0.0,
                               effective_ml_per_ml=values["crystalloid_effective_ml_per_ml"],
                               leak_tau_min=values["crystalloid_leak_tau_min"],
                               transient_share=values["crystalloid_transient_share"]))
    if scenario == "acute_loss":
        return (BloodLoss("anchor-acute-loss", 0, ACUTE_LOSS_MIN, ACUTE_LOSS_ML / ACUTE_LOSS_MIN),)
    if scenario == "stopped_bleed":
        return (replace(bleed, fraction_after_hemostasis=0.0), EndoscopicHemostasis("anchor-endoscopy", HAEMOSTASIS_AT))
    raise ValueError(scenario)


def trajectory(anchors, items, minutes: int, profile):
    """States to ``minutes``, or to the minute before output reached zero with a pulse (collapse off)."""
    try:
        return run(anchors, items, minutes, profile).states, None
    except UnresolvedBoundary as boundary:
        stop = int(str(boundary).split(":")[0].split()[-1])
        return run(anchors, items, stop - 1, profile).states, stop


def reading(state, anchors, profile) -> dict:
    derived = derive(state, anchors, profile)
    delivery = effective_delivery(derived.delivery_rel, anchors)
    balance = oxygen_balance(delivery, state.aux.oxygen_demand, profile.oxygen_extraction_reserve)
    more = derive(state.evolve(V=state.V + profile.volume_preload_kappa * RESPONSIVENESS_ML), anchors, profile)
    blood = state.blood
    return {"minute": state.minute, "shed_ml": blood.shed_ml, "circulating_ml": blood.volume_ml,
            "red_cells_change": blood.red_cells - 1.0, "hb": state.hb, "hb_change": state.hb - anchors.hb,
            "position": preload_position(state, anchors, profile), "output_rel": derived.output_rel,
            "responsiveness": more.output_rel - derived.output_rel, "do2": delivery, "state": balance.state,
            "effective_deficit": balance.effective_deficit, "sbp": derived.sbp, "map": derived.map,
            "lactate": derived.lactate, "refill_ml": blood.refill_ml,
            "crystalloid_ml": blood.crystalloid_in_ml - blood.crystalloid_out_ml,
            "transfused_ml": blood.transfused_ml}


def _grid(dimensions):
    for combination in itertools.product(*(EXPLORATION[name] for name in dimensions)):
        yield dict(zip(dimensions, combination))


# Envelopes ----------------------------------------------------------------------------------------------

NUMBERS = ("shed_ml", "circulating_ml", "red_cells_change", "hb", "hb_change", "position", "output_rel",
           "responsiveness", "do2", "effective_deficit", "sbp", "map", "lactate", "refill_ml", "crystalloid_ml")


def _median(values: list) -> float:
    ordered, middle = sorted(values), len(values) // 2
    return ordered[middle] if len(ordered) % 2 else (ordered[middle - 1] + ordered[middle]) / 2


def envelope(values: list) -> dict | None:
    values = [value for value in values if value is not None]
    if not values:
        return None
    return {"min": min(values), "median": _median(values), "max": max(values), "n": len(values)}


def _states_count(rows: list) -> dict:
    counts = {}
    for row in rows:
        if row is not None:
            counts[row["state"]] = counts.get(row["state"], 0) + 1
    return dict(sorted(counts.items()))


# P2I-2U-5: untreated bleeding ---------------------------------------------------------------------------

def untreated(case: str) -> dict:
    """The envelopes summarize the runs still perfusing at each minute ("perfusing" counts them); "with_stopped"
    adds the stopped runs with output 0 and the deficit they stopped with (a lower bound: untreated, it cannot
    improve). A stopped run has no Hb."""
    grid, stops, lasts = [], [], []
    for changes in _grid(UNTREATED_GRID):
        anchors, profile, values = setup(case, **changes)
        states, stop = trajectory(anchors, contributors(case, "untreated", values), max(TIMES), profile)
        grid.append({minute: (reading(states[minute], anchors, profile) if minute < len(states) else None)
                     for minute in TIMES})
        stops.append(stop)
        lasts.append(reading(states[-1], anchors, profile))
    anchors, profile, values = setup(case)
    states, stop = trajectory(anchors, contributors(case, "untreated", values), max(TIMES), profile)
    reference = {str(minute): reading(states[minute], anchors, profile) for minute in TIMES if minute < len(states)}
    return {"reference": reference, "reference_stop": stop, "runs": len(grid),
            "stopped_before_120": sum(1 for stop in stops if stop is not None and stop <= max(TIMES)),
            "envelopes": {str(minute): {name: envelope([row[minute][name] if row[minute] else None for row in grid])
                                        for name in NUMBERS} for minute in TIMES},
            "perfusing": {str(minute): sum(1 for row in grid if row[minute]) for minute in TIMES},
            "with_stopped": {str(minute): {
                "output_rel": envelope([row[minute]["output_rel"] if row[minute] else 0.0 for row in grid]),
                "effective_deficit": envelope([row[minute]["effective_deficit"] if row[minute]
                                               else last["effective_deficit"] for row, last in zip(grid, lasts)])}
                for minute in TIMES},
            "states": {str(minute): _states_count([row[minute] for row in grid]) for minute in TIMES},
            "stopped_by_dimension": _stopped_by_dimension(UNTREATED_GRID, stops)}


def _stopped_by_dimension(dimensions, stops) -> dict:
    out = {}
    for index, name in enumerate(dimensions):
        for value in EXPLORATION[name]:
            members = [stop for changes, stop in zip(_grid(dimensions), stops) if changes[name] == value]
            out.setdefault(name, {})[str(value)] = sum(1 for stop in members if stop is not None) / len(members)
    return out


# P2I-2U-6 / 7: one and two units of packed red cells --------------------------------------------------------

def _red_cell_rows(case: str, **changes):
    anchors, profile, values = setup(case, **changes)
    states, stop = trajectory(anchors, contributors(case, "red_cells", values), 60, profile)
    if stop is not None:
        raise AssertionError(f"{case}: a transfusion without bleeding cannot empty the ventricle")
    return [reading(states[minute], anchors, profile) for minute in (0, 30, 60)], anchors, values


def red_cells(case: str) -> dict:
    reference_position = gi_reference.case_bands(case)["reference_preload_fraction"]
    rows = []
    for changes in _grid(RED_CELL_GRID):
        (before, one, two), anchors, values = _red_cell_rows(case, **changes)
        rows.append({"position_level": changes["preload_fraction"], "before": before, "one": one, "two": two})
    deltas = {"hb_1": [r["one"]["hb"] - r["before"]["hb"] for r in rows],
              "hb_2": [r["two"]["hb"] - r["one"]["hb"] for r in rows],
              "output_1": [r["one"]["output_rel"] - r["before"]["output_rel"] for r in rows],
              "output_2": [r["two"]["output_rel"] - r["one"]["output_rel"] for r in rows],
              "do2_1": [r["one"]["do2"] - r["before"]["do2"] for r in rows],
              "do2_2": [r["two"]["do2"] - r["one"]["do2"] for r in rows],
              "responsiveness_1": [r["before"]["responsiveness"] for r in rows],
              "responsiveness_2": [r["one"]["responsiveness"] for r in rows]}
    by_position = {}
    for level in EXPLORATION["preload_fraction"]:
        members = [r for r in rows if r["position_level"] == level]
        by_position[level] = {
            "position_before": envelope([r["before"]["position"] for r in members]),
            "position_after_one": envelope([r["one"]["position"] for r in members]),
            "output_gain_one": envelope([r["one"]["output_rel"] - r["before"]["output_rel"] for r in members]),
            "output_gain_two": envelope([r["two"]["output_rel"] - r["one"]["output_rel"] for r in members]),
            "responsiveness_before": envelope([r["before"]["responsiveness"] for r in members])}
    reference = _red_cell_rows(case)[0]
    return {"runs": len(rows), "reference": {"before": reference[0], "one": reference[1], "two": reference[2]},
            "before": {name: envelope([r["before"][name] for r in rows]) for name in NUMBERS},
            "one": {name: envelope([r["one"][name] for r in rows]) for name in NUMBERS},
            "two": {name: envelope([r["two"][name] for r in rows]) for name in NUMBERS},
            "deltas": {name: envelope(values) for name, values in deltas.items()},
            "states": {"before": _states_count([r["before"] for r in rows]),
                       "one": _states_count([r["one"] for r in rows]), "two": _states_count([r["two"] for r in rows])},
            "by_position": by_position,
            "reference_position_band": [reference_position.lower, reference_position.midpoint,
                                        reference_position.upper],
            "one_reaches_reference": {
                "lower": sum(r["one"]["position"] >= reference_position.lower for r in rows) / len(rows),
                "midpoint": sum(r["one"]["position"] >= reference_position.midpoint for r in rows) / len(rows)},
            "two_reaches_reference": {
                "lower": sum(r["two"]["position"] >= reference_position.lower for r in rows) / len(rows),
                "midpoint": sum(r["two"]["position"] >= reference_position.midpoint for r in rows) / len(rows)},
            "diminishing_output": sum(o2 < o1 for o1, o2 in zip(deltas["output_1"], deltas["output_2"])) / len(rows),
            "smaller_second_hb": sum(h2 < h1 for h1, h2 in zip(deltas["hb_1"], deltas["hb_2"])) / len(rows)}


# P2I-2U-8: crystalloid during ongoing haemorrhage ---------------------------------------------------------

CRYSTALLOID_TIMES = (20, 30, 60, 120)


def _crystalloid_pair(case: str, volume_ml: float, baselines: dict, **changes) -> dict:
    anchors, profile, values = setup(case, **changes)
    key = (values["preload_scale_over_kappa_ml"], values["arrival_circulating_volume_ml"], values["preload_fraction"])
    if key not in baselines:
        states, stop = trajectory(anchors, contributors(case, "untreated", values), 120, profile)
        baselines[key] = (states, stop)
    base, base_stop = baselines[key]
    states, stop = trajectory(anchors, contributors(case, "crystalloid", values, volume_ml), 120, profile)
    common = min(len(states), len(base))
    effect = [states[m].blood.volume_ml - base[m].blood.volume_ml for m in range(common)]
    dilution = [base[m].hb - states[m].hb for m in range(common)]
    peak_dilution = max(dilution)
    retained = [states[m].blood.crystalloid_in_ml - states[m].blood.crystalloid_out_ml for m in range(len(states))]
    out = {"peak_effect_ml": max(effect), "peak_minute": effect.index(max(effect)),
           "peak_retained_ml": max(retained), "peak_dilution": peak_dilution, "stop": stop, "base_stop": base_stop}
    for minute in CRYSTALLOID_TIMES:
        if minute < common:
            with_, without = reading(states[minute], anchors, profile), reading(base[minute], anchors, profile)
            out[str(minute)] = {"retained_ml": retained[minute], "retained_share": retained[minute] / max(retained),
                                "net_effect_ml": effect[minute], "dilution": dilution[minute],
                                "reversal": 1.0 - dilution[minute] / peak_dilution if peak_dilution > 0 else None,
                                "output_rel": with_["output_rel"], "output_gain": with_["output_rel"] - without["output_rel"],
                                "do2": with_["do2"], "effective_deficit": with_["effective_deficit"],
                                "state": with_["state"], "sbp": with_["sbp"]}
    return out


def crystalloid(case: str, volume_ml: float) -> dict:
    baselines, grid = {}, list(_grid(CRYSTALLOID_GRID))
    rows = [_crystalloid_pair(case, volume_ml, baselines, **changes) for changes in grid]
    reference = _crystalloid_pair(case, volume_ml, baselines)
    summary = {name: envelope([row[name] for row in rows]) for name in ("peak_effect_ml", "peak_retained_ml",
                                                                         "peak_dilution")}
    times = {}
    for minute in CRYSTALLOID_TIMES:
        key = str(minute)
        times[key] = {name: envelope([row[key][name] for row in rows if key in row])
                      for name in ("retained_ml", "retained_share", "net_effect_ml", "dilution", "reversal",
                                   "output_rel", "output_gain", "do2", "effective_deficit", "sbp")}
        times[key]["states"] = _states_count([row.get(key) for row in rows])
    by_position = {level: envelope([row["20"]["output_gain"] for changes, row in zip(grid, rows)
                                    if changes["preload_fraction"] == level and "20" in row])
                   for level in EXPLORATION["preload_fraction"]}
    return {"runs": len(rows), "reference": reference, "summary": summary, "times": times,
            "output_gain_20_by_position": by_position,
            "stopped_with": sum(1 for row in rows if row["stop"] is not None),
            "stopped_without": sum(1 for row in rows if row["base_stop"] is not None)}


# P2I-2U-9: plasma refill --------------------------------------------------------------------------------------

def _refill_pair(case: str, scenario: str, offs: dict, **changes) -> dict:
    anchors, profile, values = setup(case, **changes)
    off_profile = replace(profile, plasma_refill_target_share=0.0)
    key = values["arrival_circulating_volume_ml"]
    if key not in offs:
        offs[key] = trajectory(anchors, contributors(case, scenario, values), max(REFILL_TIMES), off_profile)[0]
    off = offs[key]
    states, stop = trajectory(anchors, contributors(case, scenario, values), max(REFILL_TIMES), profile)
    out = {"stop": stop}
    for minute in REFILL_TIMES:
        if minute < len(states) and minute < len(off):
            blood = states[minute].blood
            target = min(profile.plasma_refill_capacity_ml, profile.plasma_refill_target_share * blood.shed_ml)
            out[str(minute)] = {"refill_ml": blood.refill_ml,
                                "restored_share": blood.refill_ml / blood.shed_ml if blood.shed_ml else None,
                                "refill_dilution": off[minute].hb - states[minute].hb,
                                "target_reached": blood.refill_ml >= 0.99 * target if target > 0 else False,
                                "capacity_binds": profile.plasma_refill_target_share * blood.shed_ml
                                                  > profile.plasma_refill_capacity_ml,
                                "circulating_ml": blood.volume_ml, "hb": states[minute].hb}
    if scenario == "stopped_bleed" and str(max(REFILL_TIMES)) in out:
        out["refill_after_haemostasis_ml"] = (states[max(REFILL_TIMES)].blood.refill_ml
                                              - states[HAEMOSTASIS_AT].blood.refill_ml)
    return out


def refill(case: str, scenario: str) -> dict:
    offs = {}
    rows = [_refill_pair(case, scenario, offs, **changes) for changes in _grid(REFILL_GRID)]
    reference = _refill_pair(case, scenario, offs)
    times = {}
    for minute in REFILL_TIMES:
        key = str(minute)
        members = [row[key] for row in rows if key in row]
        times[key] = {name: envelope([row[name] for row in members])
                      for name in ("refill_ml", "restored_share", "refill_dilution", "circulating_ml")}
        times[key]["target_reached"] = sum(row["target_reached"] for row in members) / len(members)
        times[key]["capacity_binds"] = sum(row["capacity_binds"] for row in members) / len(members)
    out = {"runs": len(rows), "reference": reference, "times": times}
    if scenario == "stopped_bleed":
        out["refill_after_haemostasis_ml"] = envelope([row.get("refill_after_haemostasis_ml") for row in rows])
    return out


# P2I-2U-11: identifiability ---------------------------------------------------------------------------------

#: Patient-level anchors, each a scalar read from one surface at the reference of the others.
ANCHORS = ("untreated_hb_change_120", "untreated_output_60", "untreated_output_120", "untreated_deficit_120",
           "one_unit_hb_gain", "one_unit_output_gain", "second_unit_output_ratio", "crystalloid_1l_peak_effect",
           "crystalloid_1l_output_gain_20", "crystalloid_1l_retained_60", "crystalloid_1l_retained_share_60",
           "crystalloid_2l_peak_dilution", "refill_share_120", "refill_dilution_120")
PARAMETERS = ("bleed_ml_per_min", "arrival_circulating_volume_ml", "preload_scale_over_kappa_ml", "preload_fraction",
              "plasma_refill_target_share", "plasma_refill_tau_min", "plasma_refill_capacity_ml",
              "red_cell_unit_hb_g_dl", "red_cell_unit_volume_ml", "crystalloid_effective_ml_per_ml",
              "crystalloid_leak_tau_min", "crystalloid_transient_share", "reserve")


def anchor_values(case: str, kappa: float = 1.0, **changes) -> dict:
    anchors, profile, values = setup(case, kappa=kappa, **changes)
    states, stop = trajectory(anchors, contributors(case, "untreated", values), 120, profile)
    last = reading(states[-1], anchors, profile)

    def at(minute, name):
        """As in untreated(): a stopped run has output 0 and the deficit it stopped with; no Hb."""
        if minute < len(states):
            return reading(states[minute], anchors, profile)[name]
        return {"output_rel": 0.0, "effective_deficit": last["effective_deficit"]}.get(name)
    out = {"untreated_hb_change_120": at(120, "hb_change"), "untreated_output_60": at(60, "output_rel"),
           "untreated_output_120": at(120, "output_rel"), "untreated_deficit_120": at(120, "effective_deficit")}
    cells, _ = trajectory(anchors, contributors(case, "red_cells", values), 60, profile)
    before, one, two = (reading(cells[minute], anchors, profile) for minute in (0, 30, 60))
    gain_one = one["output_rel"] - before["output_rel"]
    out.update({"one_unit_hb_gain": one["hb"] - before["hb"], "one_unit_output_gain": gain_one,
                "second_unit_output_ratio": (two["output_rel"] - one["output_rel"]) / gain_one if gain_one else None})
    for volume, label in ((1000.0, "1l"), (2000.0, "2l")):
        base, _ = trajectory(anchors, contributors(case, "untreated", values), 120, profile)
        given, _ = trajectory(anchors, contributors(case, "crystalloid", values, volume), 120, profile)
        common = min(len(base), len(given))
        if label == "1l":
            out["crystalloid_1l_peak_effect"] = max(given[m].blood.volume_ml - base[m].blood.volume_ml
                                                    for m in range(common))
            out["crystalloid_1l_output_gain_20"] = (reading(given[20], anchors, profile)["output_rel"]
                                                    - reading(base[20], anchors, profile)["output_rel"]
                                                    if common > 20 else None)
            retained = [given[m].blood.crystalloid_in_ml - given[m].blood.crystalloid_out_ml for m in range(len(given))]
            out["crystalloid_1l_retained_60"] = retained[60] if len(retained) > 60 else None
            out["crystalloid_1l_retained_share_60"] = retained[60] / max(retained) if len(retained) > 60 else None
        else:
            out["crystalloid_2l_peak_dilution"] = max(base[m].hb - given[m].hb for m in range(common))
    refill_on, _ = trajectory(anchors, contributors(case, "acute_loss", values), 120, profile)
    refill_off, _ = trajectory(anchors, contributors(case, "acute_loss", values), 120,
                               replace(profile, plasma_refill_target_share=0.0))
    perfusing = len(refill_on) > 120 and len(refill_off) > 120
    out["refill_share_120"] = refill_on[120].blood.refill_ml / refill_on[120].blood.shed_ml if perfusing else None
    out["refill_dilution_120"] = refill_off[120].hb - refill_on[120].hb if perfusing else None
    return out


#: The probe's classification criterion (not a clinical one), applied to the one-at-a-time effects s(p, a) =
#: the anchor's range over p's exploration values, over the largest such range on that anchor:
#: - NON_IDENTIFIABLE_SEPARATELY: the parameter enters only through a combination (structural);
#: - WELL_CONSTRAINABLE: it is the largest driver of some anchor and no other driver of that anchor reaches half
#:   its effect;
#: - PARTIALLY_CONSTRAINABLE: it reaches a quarter of the largest effect on some anchor (shared with others);
#: - POORLY_IDENTIFIED: below a quarter on every anchor.
WELL, PARTIAL, POOR, SEPARATELY = ("WELL_CONSTRAINABLE", "PARTIALLY_CONSTRAINABLE", "POORLY_IDENTIFIED",
                                   "NON_IDENTIFIABLE_SEPARATELY")
DOMINANT, NOTICEABLE = 0.5, 0.25
#: Structural degeneracies: only the combination reaches every anchor.
COMBINATIONS = {
    "volume_preload_kappa": "only lambda / kappa reaches output, pressure and delivery (V enters only as V / lambda); Hb "
                            "never reads kappa",
    "preload_curve_scale_ml": "the same: lambda is identifiable only as lambda / kappa",
    "reserve": "with the GI arrival band re-anchored, only reserve x arrival_delivery_ratio reaches D and the deficit "
               "(P2I-2P); alone it moves only the ADEQUATE / COMPENSATED label",
}


def identifiability() -> dict:
    effects = {}
    for case in CASES:
        reference = anchor_values(case)
        for parameter in PARAMETERS:
            readings = [anchor_values(case, **{parameter: value}) for value in EXPLORATION[parameter]]
            for anchor in ANCHORS:
                values = [item[anchor] for item in readings if item[anchor] is not None]
                spread = (max(values) - min(values)) if len(values) > 1 else 0.0
                effects.setdefault(anchor, {}).setdefault(parameter, 0.0)
                effects[anchor][parameter] = max(effects[anchor][parameter], spread)
        effects.setdefault("_reference", {})[case] = reference
    reference = effects.pop("_reference")
    shares = {}
    for anchor in ANCHORS:
        largest = max(effects[anchor].values())
        shares[anchor] = {parameter: (effect / largest if largest > 0 else 0.0)
                          for parameter, effect in effects[anchor].items()}
    classes = {}
    for parameter in PARAMETERS:
        if parameter in COMBINATIONS:
            classes[parameter] = SEPARATELY
            continue
        dominant = any(shares[anchor][parameter] == 1.0 and sorted(shares[anchor].values())[-2] < DOMINANT
                       for anchor in ANCHORS)
        best = max(shares[anchor][parameter] for anchor in ANCHORS)
        classes[parameter] = WELL if dominant else PARTIAL if best >= NOTICEABLE else POOR
    for name in ("volume_preload_kappa", "preload_curve_scale_ml"):
        classes[name] = SEPARATELY
    return {"effects": effects, "shares": shares, "classes": classes, "reference": reference,
            "drivers": {anchor: sorted((p for p, share in shares[anchor].items() if share >= NOTICEABLE),
                                       key=lambda p: -shares[anchor][p]) for anchor in ANCHORS},
            "gauge": gauge(), "combinations": COMBINATIONS}


def gauge() -> dict:
    """(kappa, lambda) scaled together leaves every anchor where it was; the reserve, re-anchored, leaves D alone."""
    out = {}
    for case in CASES:
        one = anchor_values(case)
        two = anchor_values(case, kappa=2.0)       # lambda scales with kappa in setup: lambda / kappa is kept
        out[case] = max(abs((one[a] or 0.0) - (two[a] or 0.0)) for a in ANCHORS)
    reserve = {}
    for case in CASES:
        rows = [anchor_values(case, reserve=value) for value in EXPLORATION["reserve"]]
        reserve[case] = max(abs((rows[0][a] or 0.0) - (row[a] or 0.0)) for row in rows for a in ANCHORS)
    return {"kappa_lambda_largest_change": out, "reserve_largest_change": reserve}


# P2I-2U-10: bleed-rate authority -------------------------------------------------------------------------------

POLICY_COMPARISON = {
    "CASE_OVERRIDES_FAMILY_DEFAULT": {
        "meaning": "a case may declare a verified bleed rate or severity; an approved GI-family default is the "
                   "fallback when it does not",
        "authoring": "optional per case: a new authoring field (rate or severity grade) plus a registered mapping "
                     "from severity to rate; the family default must be approved once",
        "clinical": "cases can differ (brisk versus slow bleeding) where their authors say so; undeclared cases "
                    "bleed at the family default",
        "risk": "the default silently governs every undeclared case, so its value matters as much as any case's; "
                "a severity-to-rate mapping is itself a faculty decision",
        "gate": "migratable with the approved default alone; a case declaration needs trusted provenance",
    },
    "CASE_REQUIRED": {
        "meaning": "every GI case must declare its own verified rate; no fallback",
        "authoring": "mandatory new field in every GI case before migration",
        "clinical": "every case's haemorrhage is explicit; no case inherits a rate it was not authored for",
        "risk": "neither bank case states a rate today (melena since yesterday; three days and another episode), "
                "so both stay blocked until authored",
        "gate": "fails closed for every case without the field",
    },
    "FAMILY_FIXED_VALUE": {
        "meaning": "one approved GI-family rate for every case; cases cannot override it",
        "authoring": "none per case",
        "clinical": "every GI patient bleeds alike; a brisk and a slow bleed cannot be distinguished",
        "risk": "one GI constant becomes universal truth for the family (the faculty already rejected treating the "
                "legacy literal so)",
        "gate": "migratable with the approved value alone",
    },
    # Not one of the three P2I-2U names; added because P2G lists it for blood_loss_ml_per_min (FD-50).
    "FAMILY_ALLOWED_RANGE": {
        "meaning": "the family approves a range as an authorization envelope, not as the source of the value: the "
                   "rate is the case's verified one and must fall inside it",
        "authoring": "the same new per-case field as CASE_OVERRIDES_FAMILY_DEFAULT, plus the range's bounds",
        "clinical": "brisk and slow bleeding can differ within approved limits",
        "risk": "without a case rate it runs only on an explicitly approved range fallback; otherwise it closes, "
                "as CASE_REQUIRED does for both bank cases today; both bounds are faculty decisions",
        "gate": "fails closed without a verified case rate, unless the approval defines a fallback",
    },
}
#: The policy P2I-2U was asked to evaluate as the preferred one, not adopted there; the faculty approved its
#: category for the bleed rate in P2I-2V (migration_authority.AUTHORITY_POLICIES), no rate.
PREFERRED_POLICY = "CASE_OVERRIDES_FAMILY_DEFAULT"


# The report ------------------------------------------------------------------------------------------------------

def anchors_digest() -> str:
    text = json.dumps({"artifact": "P2I-2U shared-haemorrhage anchors", "sources": lactate_slice.slice_sources(),
                       "freeze": calibration.frozen_digest()}, sort_keys=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def report() -> dict:
    return {"anchors_digest": anchors_digest(), "reference": REFERENCE, "exploration": EXPLORATION,
            "kinetics": KINETICS, "reserve": RESERVE,
            "grids": {"untreated": UNTREATED_GRID, "red_cells": RED_CELL_GRID, "crystalloid": CRYSTALLOID_GRID,
                      "refill": REFILL_GRID},
            "untreated": {case: untreated(case) for case in CASES},
            "red_cells": {case: red_cells(case) for case in CASES},
            "crystalloid": {case: {str(int(volume)): crystalloid(case, volume) for volume in CRYSTALLOID_VOLUMES}
                            for case in CASES},
            "refill": {case: {scenario: refill(case, scenario) for scenario in ("acute_loss", "stopped_bleed")}
                       for case in CASES},
            "identifiability": identifiability(), "policies": POLICY_COMPARISON, "preferred_policy": PREFERRED_POLICY}


# The faculty worksheet (FD-BLD-01..09): questions only; the selections stay blank -----------------------------

WORKSHEET = (
    ("FD-BLD-01", "What Hb increment from one unit should be acceptable in these modeled adults?",
     ("one_unit_hb_gain",)),
    ("FD-BLD-02", "How much improvement in effective output should one unit be allowed to cause when the patient is "
                  "preload responsive?", ("one_unit_output_gain",)),
    ("FD-BLD-03", "Should one unit alone be capable of normalizing output in either GI case?",
     ("one_unit_output_gain",)),
    ("FD-BLD-04", "How large should the transient haemodynamic response to 1 L crystalloid be?",
     ("crystalloid_1l_output_gain_20", "crystalloid_1l_peak_effect")),
    ("FD-BLD-05", "How much effective intravascular crystalloid effect should remain at 30/60 min?",
     ("crystalloid_1l_retained_60", "crystalloid_1l_retained_share_60")),
    ("FD-BLD-06", "How much Hb dilution should be acceptable from 1-2 L crystalloid?",
     ("crystalloid_2l_peak_dilution",)),
    ("FD-BLD-07", "What fraction of an acute circulating-volume deficit should endogenous refill be capable of "
                  "replacing over ~1-2 h?", ("refill_share_120",)),
    ("FD-BLD-08", "Should refill remain active after haemostasis while a deficit remains?", ("refill_share_120",)),
    ("FD-BLD-09", "What qualitative Hb effect should refill produce over 1-2 h?", ("refill_dilution_120",)),
)
#: The untreated anchors faculty set later (P2I-2U-5): the questions, never answered here.
UNTREATED_QUESTIONS = (
    ("A", "acceptable Hb change by 60 / 120 min", ("untreated_hb_change_120",)),
    ("B", "acceptable output deterioration by 60 / 120 min", ("untreated_output_60", "untreated_output_120")),
    ("C", "acceptable transition into compensated / critical oxygen availability", ("untreated_deficit_120",)),
    ("D", "whether each case should remain perfusing at 120 min untreated", ("untreated_output_120",)),
)


# Rendering (Spanish) ----------------------------------------------------------------------------------------------

OPENING, CLOSING = "<!-- generado:anclas-hemorragia -->\n", "<!-- /generado:anclas-hemorragia -->"
STATES_ES = {"ADEQUATE": "adecuada", "COMPENSATED": "compensada", "CRITICAL": "crítica"}
PARAMETERS_ES = {
    "bleed_ml_per_min": "tasa de sangrado (mL-eq/min)", "arrival_circulating_volume_ml": "B0 (mL-eq)",
    "preload_scale_over_kappa_ml": "λ/κ (mL-eq)", "preload_fraction": "posición de precarga de llegada",
    "plasma_refill_target_share": "meta del relleno (fracción de lo perdido)",
    "plasma_refill_tau_min": "τ del relleno (min)", "plasma_refill_capacity_ml": "capacidad del relleno (mL-eq)",
    "red_cell_unit_hb_g_dl": "Hb de la unidad de GR (g/dL)", "red_cell_unit_volume_ml": "volumen de la unidad (mL-eq)",
    "crystalloid_effective_ml_per_ml": "retención intravascular del cristaloide",
    "crystalloid_leak_tau_min": "τ de redistribución del cristaloide (min)",
    "crystalloid_transient_share": "fracción transitoria del cristaloide", "reserve": "ρ (reserva de extracción)",
    "volume_preload_kappa": "κ (por separado)", "preload_curve_scale_ml": "λ (por separado)"}
ANCHORS_ES = {
    "untreated_hb_change_120": "sin tratar: cambio de Hb a 120′", "untreated_output_60": "sin tratar: gasto a 60′",
    "untreated_output_120": "sin tratar: gasto a 120′", "untreated_deficit_120": "sin tratar: déficit efectivo a 120′",
    "one_unit_hb_gain": "1 U: ΔHb", "one_unit_output_gain": "1 U: Δgasto",
    "second_unit_output_ratio": "2.ª U: Δgasto / Δgasto de la 1.ª", "crystalloid_1l_peak_effect": "1 L: efecto pico en C",
    "crystalloid_1l_output_gain_20": "1 L: Δgasto al terminar (20′)",
    "crystalloid_1l_retained_60": "1 L: cristaloide retenido a 60′",
    "crystalloid_1l_retained_share_60": "1 L: retenido / pico a 60′", "crystalloid_2l_peak_dilution": "2 L: dilución pico",
    "refill_share_120": "relleno: fracción repuesta a 120′", "refill_dilution_120": "relleno: dilución a 120′"}
CLASSES_ES = {WELL: "WELL_CONSTRAINABLE (bien acotable)", PARTIAL: "PARTIALLY_CONSTRAINABLE (parcialmente)",
              POOR: "POORLY_IDENTIFIED (mal identificado)", SEPARATELY: "NON_IDENTIFIABLE_SEPARATELY (sólo en combinación)"}
QUESTIONS_ES = {
    "FD-BLD-01": "¿Qué aumento de Hb por una unidad debería ser aceptable en estos adultos modelados?",
    "FD-BLD-02": "¿Cuánto debería poder mejorar el gasto efectivo una unidad cuando el paciente responde a la precarga?",
    "FD-BLD-03": "¿Una unidad sola debería poder normalizar el gasto en alguno de los dos casos GI?",
    "FD-BLD-04": "¿Qué tamaño debería tener la respuesta hemodinámica transitoria a 1 L de cristaloide?",
    "FD-BLD-05": "¿Cuánto efecto intravascular efectivo del cristaloide debería quedar a los 30 y 60 min?",
    "FD-BLD-06": "¿Cuánta dilución de la Hb debería ser aceptable con 1–2 L de cristaloide?",
    "FD-BLD-07": "¿Qué fracción de un déficit agudo de volumen circulante debería poder reponer el relleno endógeno en "
                 "~1–2 h?",
    "FD-BLD-08": "¿El relleno debería seguir activo después de la hemostasia mientras quede déficit?",
    "FD-BLD-09": "¿Qué efecto cualitativo sobre la Hb debería producir el relleno en 1–2 h?"}
UNTREATED_ES = {"A": "cambio de Hb aceptable a los 60 / 120 min",
                "B": "deterioro del gasto aceptable a los 60 / 120 min",
                "C": "transición aceptable a disponibilidad de O2 compensada / crítica",
                "D": "si cada caso debe seguir perfundiendo a los 120 min sin tratamiento"}
POLICIES_ES = {
    "CASE_OVERRIDES_FAMILY_DEFAULT": {
        "meaning": "el caso puede declarar una tasa o gravedad verificada; el valor de familia GI aprobado es sólo respaldo",
        "authoring": "opcional por caso: un campo de autoría nuevo (tasa o grado de gravedad) y un mapeo registrado de "
                     "gravedad a tasa; el valor de familia se aprueba una vez",
        "clinical": "los casos pueden diferir (sangrado rápido o lento) donde su autor lo dice; los que no declaran "
                    "sangran al valor de familia",
        "risk": "el valor de familia gobierna en silencio cada caso sin declaración, así que su valor pesa tanto como el "
                "de cualquier caso; el mapeo gravedad → tasa es a su vez una decisión docente",
        "gate": "migrable con el valor de familia aprobado; una declaración del caso necesita procedencia de confianza"},
    "CASE_REQUIRED": {
        "meaning": "cada caso GI debe declarar su propia tasa verificada; sin respaldo",
        "authoring": "un campo nuevo obligatorio en cada caso GI antes de migrar",
        "clinical": "la hemorragia de cada caso es explícita; ningún caso hereda una tasa para la que no se escribió",
        "risk": "hoy ningún caso del banco declara una tasa (melena desde ayer; tres días y otro episodio hoy): los dos "
                "quedan bloqueados hasta que se escriba",
        "gate": "falla cerrado para todo caso sin el campo"},
    "FAMILY_FIXED_VALUE": {
        "meaning": "una tasa de familia GI aprobada para todos los casos; ningún caso la cambia",
        "authoring": "ninguna por caso",
        "clinical": "todo paciente GI sangra igual; no se distingue un sangrado rápido de uno lento",
        "risk": "una constante GI se vuelve verdad universal de la familia (la docencia ya rechazó tratar así el literal "
                "heredado)",
        "gate": "migrable con el valor aprobado"},
    "FAMILY_ALLOWED_RANGE": {
        "meaning": "la familia aprueba un rango como envoltura de autorización, no como fuente del valor: la tasa es la "
                   "verificada del caso y debe caer dentro",
        "authoring": "el mismo campo nuevo por caso que `CASE_OVERRIDES_FAMILY_DEFAULT`, más los límites del rango",
        "clinical": "el sangrado rápido y el lento pueden diferir dentro de límites aprobados",
        "risk": "sin tasa del caso sólo corre con un respaldo del rango aprobado explícitamente; si no, cierra, como "
                "`CASE_REQUIRED` hoy para los dos casos del banco; los dos límites son decisiones docentes",
        "gate": "falla cerrado sin tasa del caso verificada, salvo que la aprobación defina un respaldo"},
}


def _n(value, digits: int = 2) -> str:
    if value is None:
        return "—"
    if isinstance(value, str):
        return STATES_ES.get(value, value)
    return lactate_slice._n(value, digits)


def _v(value) -> str:
    """An exploration or reference value, with the digits it needs."""
    if isinstance(value, str):
        return {"lower": "inf.", "midpoint": "medio", "upper": "sup."}.get(value, value)
    if float(value).is_integer() or abs(value) >= 100:
        return _n(value, 0)
    return _n(value, 3).rstrip("0").rstrip(",")


COMBINATIONS_ES = {
    "volume_preload_kappa": "sólo λ/κ llega al gasto, la presión y la entrega (V entra sólo como V/λ); la Hb nunca lee κ",
    "preload_curve_scale_ml": "lo mismo: λ sólo es identificable como λ/κ",
    "reserve": "con la banda de entrega de llegada re-anclada, sólo ρ × arrival_delivery_ratio llega a D y al déficit "
               "(P2I-2P); sola, sólo cambia la etiqueta adecuada / compensada"}


def _env(item, digits=2, reference=None) -> str:
    if item is None:
        return "—"
    span = f"{_n(item['min'], digits)}–{_n(item['max'], digits)}"
    return f"{_n(reference, digits)} ({span})" if reference is not None else f"{_n(item['median'], digits)} ({span})"


def _pct(share) -> str:
    return f"{_n(100 * share, 0)} %"


UNTREATED_ROWS = (("shed_ml", "sangre total perdida (mL-eq)", 0), ("circulating_ml", "desviación circulante C (mL-eq)", 0),
                  ("red_cells_change", "cambio del contenido de GR", 3), ("hb", "Hb (g/dL)", 2),
                  ("position", "precarga efectiva (posición 0–1)", 2), ("output_rel", "gasto relativo", 2),
                  ("do2", "índice de DO2", 2), ("effective_deficit", "déficit efectivo", 2),
                  ("sbp", "PAS (contexto)", 0), ("map", "PAM (contexto)", 0), ("lactate", "lactato (contexto)", 1))


def render(data: dict) -> str:
    data = json.loads(json.dumps(data, sort_keys=True, default=str))
    lines = []
    add = lines.append
    reference, exploration = data["reference"], data["exploration"]
    add(f"Generado desde las anclas `{data['anchors_digest']}` (`python -m clinical_core.blood_anchors`). Llegada: cada "
        "caso GI con sus bandas en el punto medio (posición de precarga: la que indique la tabla), cinética del lactato "
        "del punto medio de P2F (sólo contexto), ρ "
        f"{_n(data['reserve'], 1)} con la banda de entrega de llegada re-anclada. κ = 1: la escala se explora como λ/κ. "
        "**Todos los rangos son exploraciones SINTÉTICAS, no valores aprobados ni bandas nuevas:** λ/κ reutiliza los "
        "tres puntos candidatos del registro de `preload_curve_scale_ml` y la posición recorre la banda del caso; el "
        "resto no es una banda candidata. Cada celda: referencia (mínimo–máximo en la cuadrícula).\n")
    add("| Parámetro | Referencia (provisional) | Exploración sintética |")
    add("|---|---|---|")
    for name in PARAMETERS:
        add(f"| {PARAMETERS_ES[name]} | "
            f"{'punto medio de la banda del caso' if isinstance(reference[name], str) else _v(reference[name])} | "
            + " / ".join(_v(value) for value in exploration[name]) + " |")
    add("")
    # Untreated
    add("### A.1 Sangrado sin tratar (P2I-2U-5)\n")
    for case in CASES:
        item = data["untreated"][case]
        add(f"**{case}** — {item['runs']} combinaciones de la cuadrícula "
            f"({', '.join(PARAMETERS_ES[name] for name in data['grids']['untreated'])}); "
            f"{item['stopped_before_120']} se detienen antes de los 120 min (el gasto llega a 0 con pulso; colapso "
            "apagado). Referencia: " + ("sigue perfundiendo a los 120 min." if item["reference_stop"] is None
                                        else f"se detiene en el minuto {item['reference_stop']}.") + "\n")
        add("| Magnitud | " + " | ".join(f"{minute}′" for minute in TIMES) + " |")
        add("|---|" + "---|" * len(TIMES))
        add("| corridas que siguen perfundiendo | " + " | ".join(
            f"{item['perfusing'][str(minute)]} de {item['runs']}" for minute in TIMES) + " |")
        for name, label, digits in UNTREATED_ROWS:
            cells = []
            for minute in TIMES:
                ref = item["reference"].get(str(minute), {}).get(name)
                cells.append(_env(item["envelopes"][str(minute)][name], digits, ref))
            add(f"| {label} | " + " | ".join(cells) + " |")
        for name, label in (("output_rel", "gasto relativo, con las detenidas en 0"),
                            ("effective_deficit", "déficit efectivo, con las detenidas en su valor al detenerse")):
            add(f"| {label} | " + " | ".join(_env(item["with_stopped"][str(minute)][name], 2,
                                                  item["reference"].get(str(minute), {}).get(name)) for minute in TIMES)
                + " |")
        add("")
        add("El mínimo–máximo de cada fila resume sólo las corridas que siguen perfundiendo en ese minuto (primera "
            "fila); las dos últimas filas incluyen las detenidas: gasto 0 y el déficit con que se detuvieron, que es "
            "un piso (sin tratamiento no mejora). Una corrida detenida no tiene Hb.\n")
        add("Estado del O2 en la cuadrícula (corridas que siguen perfundiendo): " + "; ".join(
            f"{minute}′ " + ", ".join(f"{STATES_ES[state]} {count}" for state, count in item["states"][str(minute)].items())
            for minute in TIMES) + ". Con la banda de entrega de llegada en su punto medio, la llegada ya está en déficit "
            "crítico.")
        stopped = item["stopped_by_dimension"]
        add("")
        add("Proporción de corridas que se detienen antes de los 120 min, por valor de cada dimensión: "
            + "; ".join(f"{PARAMETERS_ES[name]}: " + ", ".join(
                f"{_v(value)} {_pct(stopped[name][str(value)])}" for value in exploration[name])
                for name in data["grids"]["untreated"]) + ".\n")
    # Red cells
    add("### A.2 Una y dos unidades de GR, con el sangrado controlado (P2I-2U-6 y 7)\n")
    for case in CASES:
        item = data["red_cells"][case]
        ref = item["reference"]
        add(f"**{case}** — {item['runs']} combinaciones ({', '.join(PARAMETERS_ES[n] for n in data['grids']['red_cells'])}); "
            "unidad 1 en 0–30 min, unidad 2 en 30–60 min.\n")
        add("| Magnitud | antes | tras 1 U | tras 2 U |")
        add("|---|---|---|---|")
        for name, label, digits in (("hb", "Hb (g/dL)", 2), ("circulating_ml", "desviación circulante C (mL-eq)", 0),
                                    ("position", "precarga efectiva (posición)", 2), ("output_rel", "gasto relativo", 2),
                                    ("responsiveness", "respuesta a +100 mL-eq (Δgasto)", 3), ("do2", "índice de DO2", 2),
                                    ("effective_deficit", "déficit efectivo", 2), ("sbp", "PAS (contexto)", 0)):
            add(f"| {label} | " + " | ".join(_env(item[stage][name], digits, ref[stage][name])
                                            for stage in ("before", "one", "two")) + " |")
        add("")
        add("| Incremento | unidad 1 | unidad 2 |")
        add("|---|---|---|")
        for key, label, digits in (("hb", "ΔHb (g/dL)", 2), ("output", "Δgasto", 3), ("do2", "ΔDO2", 3),
                                   ("responsiveness", "respuesta a la precarga antes de la unidad", 3)):
            add(f"| {label} | {_env(item['deltas'][key + '_1'], digits)} | {_env(item['deltas'][key + '_2'], digits)} |")
        add("")
        band = item["reference_position_band"]
        add(f"- Rendimiento decreciente del gasto (Δ de la 2.ª < Δ de la 1.ª): {_pct(item['diminishing_output'])} de la "
            "cuadrícula. Es estructural, no un hallazgo: con la curva de precarga exponencial, Δgasto de la 2.ª / "
            "Δgasto de la 1.ª = exp(−volumen de la unidad / (λ/κ)) en toda la cuadrícula; la posición, B0 y la Hb de "
            f"la unidad no entran. ΔHb de la 2.ª menor que la de la 1.ª: {_pct(item['smaller_second_hb'])}.")
        add(f"- Posición tras 1 U en la referencia euvolémica del caso (banda {_n(band[0])}–{_n(band[2])}): "
            f"≥ {_n(band[0])} en {_pct(item['one_reaches_reference']['lower'])}, ≥ {_n(band[1])} en "
            f"{_pct(item['one_reaches_reference']['midpoint'])}; tras 2 U: {_pct(item['two_reaches_reference']['lower'])} y "
            f"{_pct(item['two_reaches_reference']['midpoint'])}.")
        add("- Por posición de llegada (respuesta a la precarga): " + "; ".join(
            f"{ {'lower': 'inf.', 'midpoint': 'medio', 'upper': 'sup.'}[level]}: posición "
            f"{_env(entry['position_before'])} → {_env(entry['position_after_one'])}, Δgasto 1.ª "
            f"{_env(entry['output_gain_one'], 3)}, 2.ª {_env(entry['output_gain_two'], 3)}"
            for level, entry in item["by_position"].items()) + ".\n")
    # Crystalloid
    add("### A.3 Cristaloide durante sangrado continuo (P2I-2U-8)\n")
    for case in CASES:
        for volume, item in data["crystalloid"][case].items():
            ref = item["reference"]
            add(f"**{case}, {int(volume) // 1000} L en 20 min** — {item['runs']} combinaciones "
                f"({', '.join(PARAMETERS_ES[n] for n in data['grids']['crystalloid'])}); comparado con el mismo sangrado "
                f"sin cristaloide; antes de los 120 min se detienen {item['stopped_with']} corridas con cristaloide y "
                f"{item['stopped_without']} sin él, y cada fila resume sólo los pares que siguen perfundiendo los dos "
                f"(columna n). Efecto pico en C {_env(item['summary']['peak_effect_ml'], 0, ref['peak_effect_ml'])} "
                f"mL-eq (minuto {ref['peak_minute']} en la referencia); cristaloide retenido pico "
                f"{_env(item['summary']['peak_retained_ml'], 0, ref['peak_retained_ml'])} mL-eq; dilución pico de Hb "
                f"{_env(item['summary']['peak_dilution'], 2, ref['peak_dilution'])} g/dL. Δgasto al terminar, por "
                "posición de llegada: " + ", ".join(
                    f"{_v(level)} {_env(entry, 2)}" for level, entry in item["output_gain_20_by_position"].items())
                + ".\n")
            add("| Minuto | n | retenido (mL-eq) | retenido / pico | efecto neto en C | dilución de Hb | reversión | gasto | "
                "Δgasto | DO2 | déficit | PAS (contexto) |")
            add("|---|---|---|---|---|---|---|---|---|---|---|---|")
            for minute in CRYSTALLOID_TIMES:
                key, row = str(minute), item["times"][str(minute)]
                r = ref.get(key, {})
                add(f"| {minute} | {row['output_rel']['n'] if row['output_rel'] else 0} | "
                    f"{_env(row['retained_ml'], 0, r.get('retained_ml'))} | "
                    f"{_env(row['retained_share'], 2, r.get('retained_share'))} | {_env(row['net_effect_ml'], 0, r.get('net_effect_ml'))} | "
                    f"{_env(row['dilution'], 2, r.get('dilution'))} | {_env(row['reversal'], 2, r.get('reversal'))} | "
                    f"{_env(row['output_rel'], 2, r.get('output_rel'))} | {_env(row['output_gain'], 2, r.get('output_gain'))} | "
                    f"{_env(row['do2'], 2, r.get('do2'))} | {_env(row['effective_deficit'], 2, r.get('effective_deficit'))} | "
                    f"{_env(row['sbp'], 0, r.get('sbp'))} |")
            add("")
    add("«Retenido» es el cristaloide que sigue en la circulación (estado sanguíneo); «efecto neto en C» lo compara con el "
        "mismo sangrado sin cristaloide, y es menor porque mientras la circulación está sobre la llegada el relleno espera.\n")
    # Refill
    add("### A.4 Relleno plasmático (P2I-2U-9)\n")
    names = {"acute_loss": f"pérdida aguda sintética de {_n(ACUTE_LOSS_ML, 0)} mL-eq en {ACUTE_LOSS_MIN} min (no es una tasa GI)",
             "stopped_bleed": f"sangrado GI de referencia detenido por completo a los {HAEMOSTASIS_AT} min"}
    for case in CASES:
        for scenario, item in data["refill"][case].items():
            ref = item["reference"]
            add(f"**{case}, {names[scenario]}** — {item['runs']} combinaciones "
                f"({', '.join(PARAMETERS_ES[n] for n in data['grids']['refill'])}).\n")
            add("| Minuto | relleno (mL-eq) | fracción de lo perdido repuesta | dilución de Hb por el relleno | C (mL-eq) | "
                "meta alcanzada | la capacidad limita |")
            add("|---|---|---|---|---|---|---|")
            for minute in REFILL_TIMES:
                key, row = str(minute), item["times"][str(minute)]
                r = ref.get(key, {})
                add(f"| {minute} | {_env(row['refill_ml'], 0, r.get('refill_ml'))} | "
                    f"{_env(row['restored_share'], 2, r.get('restored_share'))} | "
                    f"{_env(row['refill_dilution'], 3, r.get('refill_dilution'))} | {_env(row['circulating_ml'], 0, r.get('circulating_ml'))} | "
                    f"{_pct(row['target_reached'])} | {_pct(row['capacity_binds'])} |")
            if "refill_after_haemostasis_ml" in item:
                add(f"\nRelleno después de la hemostasia (minutos {HAEMOSTASIS_AT}–{max(REFILL_TIMES)}): "
                    f"{_env(item['refill_after_haemostasis_ml'], 0, ref.get('refill_after_haemostasis_ml'))} mL-eq; en el "
                    "modelo actual el relleno sigue mientras quede déficit y distancia a la meta.")
            add("")
    # Identifiability
    ident = data["identifiability"]
    add("### A.5 Identificabilidad (P2I-2U-11)\n")
    add("Efecto de cada parámetro sobre cada ancla, variándolo solo en su rango sintético (el resto en la referencia), "
        "como fracción del mayor efecto sobre esa ancla (máximo de los dos casos). Criterio de la sonda, no clínico: "
        f"bien acotable si es el mayor motor de un ancla y ningún otro llega a {_n(DOMINANT, 2)} de su efecto; "
        f"parcialmente si llega a {_n(NOTICEABLE, 2)} en alguna; mal identificado si no.\n")
    add("| Ancla | " + " | ".join(PARAMETERS_ES[p] for p in PARAMETERS) + " |")
    add("|---|" + "---|" * len(PARAMETERS))
    for anchor in ANCHORS:
        add(f"| {ANCHORS_ES[anchor]} | " + " | ".join(_n(ident["shares"][anchor][p], 2) for p in PARAMETERS) + " |")
    add("")
    add("| Parámetro | Clase | Anclas que mueve (≥ " + _n(NOTICEABLE, 2) + ") |")
    add("|---|---|---|")
    for parameter in (*PARAMETERS, "volume_preload_kappa", "preload_curve_scale_ml"):
        moved = [ANCHORS_ES[a] for a in ANCHORS if parameter in ident["drivers"][a]]
        note = COMBINATIONS_ES.get(parameter) if parameter in ident["combinations"] else None
        add(f"| {PARAMETERS_ES[parameter]} | {CLASSES_ES[ident['classes'][parameter]]} | "
            + ("; ".join(moved) if moved else (note or "—")) + (f" ({note})" if note and moved else "") + " |")
    add("")
    gauge_ = ident["gauge"]
    add("Comprobaciones estructurales: con (κ, λ) y (2κ, 2λ) el mayor cambio de cualquier ancla es "
        + ", ".join(f"{case} {_n(value, 12)}" for case, value in gauge_["kappa_lambda_largest_change"].items())
        + "; con ρ 1 / 2,5 / 3 y la banda re-anclada, "
        + ", ".join(f"{case} {_n(value, 12)}" for case, value in gauge_["reserve_largest_change"].items()) + ".\n")
    add("Combinaciones que mueven cada ancla (en orden de efecto): " + "; ".join(
        f"{ANCHORS_ES[a]}: " + ", ".join(PARAMETERS_ES[p] for p in ident["drivers"][a]) for a in ANCHORS) + ".\n")
    # Worksheet
    add("### A.6 Hoja de trabajo FD-BLD (P2I-2U-6, 8 y 9)\n")
    add("En esta hoja cada cifra es la mediana (mínimo–máximo) de la cuadrícula de su superficie, no la referencia; las "
        "de A.1 y A.3 resumen sólo las corridas que siguen perfundiendo (n en sus tablas), salvo donde se dice. "
        "«Qué acotaría» son los parámetros internos que mueven las anclas de la evidencia mostrada (A.5), en orden de "
        "efecto; ninguno se decide por separado.\n")
    add("**Estado (P2I-2V, 2026-10-27).** La docencia aprobó FD-BLD-01 a 09 y las anclas sin tratar A y B. "
        "FACULTY_APPROVED quiere decir: conducta clínica / envolvente aprobada; los parámetros ocultos del modelo "
        "siguen sin aprobar. Las envolventes son envolventes clínicas, no objetivos exactos. Cómo se leen y qué región "
        "dejan: `docs/revision/P2I2V_ANCLAS_APROBADAS_FILTRO.md`. **P2I-2V-R:** A pasa a v2, sin caída mínima de Hb; "
        "FD-BLD-03 queda FACULTY_APPROVED_QUALITATIVE / NOT_YET_HARD_FILTER (se informa, no filtra): "
        "`docs/revision/P2I2VR_RESTRICCIONES_REVISADAS_FILTRO.md`.\n")
    add("| ID | Pregunta | Lo que muestra el modelo (sólo modelo) | Qué acotaría | Selección docente | Estado |")
    add("|---|---|---|---|---|---|")
    for identifier, _, anchors in WORKSHEET:
        add(f"| {identifier} | {QUESTIONS_ES[identifier]} | {_worksheet_evidence(identifier, data)} | "
            + ", ".join(PARAMETERS_ES[p] for p in _drivers(ident, anchors))
            + f" | {_approved(identifier)} | {_approved_status(identifier)} |")
    add("")
    add("| Ancla sin tratar | Pregunta | Lo que muestra el modelo | Qué acotaría | Selección docente | Estado |")
    add("|---|---|---|---|---|---|")
    for letter, _, anchors in UNTREATED_QUESTIONS:
        add(f"| {letter} | {UNTREATED_ES[letter]} | {_untreated_evidence(letter, data)} | "
            + ", ".join(PARAMETERS_ES[p] for p in _drivers(ident, anchors))
            + f" | {_approved(letter)} | {_approved_status(letter)} |")
    add("")
    add("C y D no se decidieron. D queda implícita en la envolvente de B a los 120 min (un gasto de 0,45–0,65 o "
        "0,60–0,78 exige seguir perfundiendo), pero no se decidió por separado.\n")
    # Policies
    add("### A.7 Autoridad de la tasa de sangrado (P2I-2U-10)\n")
    add("`FAMILY_ALLOWED_RANGE` no está entre las tres que pide el encargo; se añade porque P2G la lista para "
        "`blood_loss_ml_per_min` (FD-50). En P2I-2U no se adoptó ninguna. **P2I-2V (2026-10-27):** la docencia aprobó "
        "la categoría `CASE_OVERRIDES_FAMILY_DEFAULT` para esta tasa, sin aprobar ningún valor numérico.\n")
    add("| Política | Significado | Autoría | Consecuencia clínica | Riesgo | Puerta de migración |")
    add("|---|---|---|---|---|---|")
    for policy in data["policies"]:
        entry = POLICIES_ES[policy]
        add(f"| `{policy}`{' (la que el encargo pide evaluar como preferida; no adoptada)' if policy == data['preferred_policy'] else ''} | "
            f"{entry['meaning']} | {entry['authoring']} | {entry['clinical']} | {entry['risk']} | {entry['gate']} |")
    return "\n".join(lines)


def _drivers(ident: dict, anchors: tuple) -> list:
    """The parameters that move any of the anchors (share >= NOTICEABLE), largest share first."""
    shares = {}
    for anchor in anchors:
        for parameter in ident["drivers"][anchor]:
            shares[parameter] = max(shares.get(parameter, 0.0), ident["shares"][anchor][parameter])
    return sorted(shares, key=lambda parameter: -shares[parameter])


def _range(pair, digits: int = 2) -> str:
    return f"{_n(pair[0], digits)}–{_n(pair[1], digits)}"


def _percent(pair) -> str:
    return f"{_n(100 * pair[0], 0)}–{_n(100 * pair[1], 0)} %"


def _approved(identifier: str) -> str:
    """The faculty's selection (P2I-2V), written from blood_constraints.DECISIONS; blank while open."""
    from . import blood_constraints  # imported here: it imports this module
    d = blood_constraints.DECISIONS
    cases = gi_reference.GI_CASES
    if identifier == "FD-BLD-01":
        return (f"≈ {_range(d['FD-BLD-01']['envelope'], 1)} g/dL por unidad; no es una regla fija de +1 g/dL; tras "
                "mezcla razonable y sin una pérdida simultánea abrumadora")
    if identifier == "FD-BLD-02":
        return ("con respuesta a la precarga y llenado bajo: " + "; ".join(
            f"{case} ≈ {_percent(d['FD-BLD-02'][case])}" for case in cases)
            + " de aumento del gasto efectivo; envolventes de techo / conducta, no respuestas obligatorias")
    if identifier == "FD-BLD-03":
        return ("una unidad no debe normalizar de forma fiable el gasto efectivo en ninguno de los dos casos; 72f puede "
                "acercarse a un estado adecuado si responde a la precarga; 57m no pasa de fisiología hemorrágica grave "
                "a gasto normalizado / euvolémico con una sola unidad. Segunda unidad: beneficio ≤ el de la primera "
                "(la razón ~0,70 no se aprueba)")
    if identifier == "FD-BLD-04":
        return (f"≈ {_percent(d['FD-BLD-04']['envelope'])} del volumen infundido (≈ 150–300 mL por litro); envolvente "
                "clínica, no una conversión exacta")
    if identifier == "FD-BLD-05":
        return "; ".join(f"≈ {_percent(pair)} a los ~{minute} min"
                         for minute, pair in d["FD-BLD-05"]["envelopes"].items())
    if identifier == "FD-BLD-06":
        return ("; ".join(f"{volume // 1000} L: descenso transitorio de ≈ {_range(pair, 1)} g/dL"
                          for volume, pair in d["FD-BLD-06"]["envelopes"].items()) + "; con reversión parcial")
    if identifier == "FD-BLD-07":
        return "; ".join(f"≈ {_percent(pair)} a los ~{minute} min"
                         for minute, pair in d["FD-BLD-07"]["envelopes"].items())
    if identifier == "FD-BLD-08":
        return "sí: sigue después de la hemostasia mientras quede déficit circulante y capacidad de relleno"
    if identifier == "FD-BLD-09":
        return ("aumenta el volumen plasmático / circulante, no la masa de GR, y diluye la Hb progresivamente; ningún "
                "decremento fijo en g/dL: la magnitud sale del estado sanguíneo compartido")
    if identifier == "A":
        return "v2 (P2I-2V-R), sin caída mínima: caída de Hb " + "; ".join(
            f"{case} " + ", ".join(f"{_range(pair, 1)} g/dL a los {minute} min"
                                   for minute, pair in d["untreated_hb_fall"][case].items()) for case in cases) + (
            "; con hemorragia en curso y sin fuente de GR, la Hb no sube por la hemorragia misma")
    if identifier == "B":
        return "gasto efectivo relativo a la llegada: " + "; ".join(
            f"{case} " + ", ".join(f"{_range(pair)} a los {minute} min"
                                   for minute, pair in d["untreated_output"][case].items()) for case in cases)
    return ""


def _approved_status(identifier: str) -> str:
    from . import blood_constraints
    if identifier in blood_constraints.FD_BLD_STATUS:
        return blood_constraints.FD_BLD_STATUS[identifier]
    return {"A": blood_constraints.U_HB_STATUS, "B": "FACULTY_APPROVED"}.get(identifier, "ABIERTA")


def _worksheet_evidence(identifier: str, data: dict) -> str:
    cases = CASES
    if identifier == "FD-BLD-01":
        return "; ".join(f"{case}: ΔHb {_env(data['red_cells'][case]['deltas']['hb_1'], 2)} g/dL" for case in cases)
    if identifier == "FD-BLD-02":
        return "; ".join(f"{case}: Δgasto {_env(data['red_cells'][case]['deltas']['output_1'], 2)} (posición inf. "
                         f"{_env(data['red_cells'][case]['by_position']['lower']['output_gain_one'], 2)})" for case in cases)
    if identifier == "FD-BLD-03":
        return "; ".join(f"{case}: llega a la referencia euvolémica inferior en "
                         f"{_pct(data['red_cells'][case]['one_reaches_reference']['lower'])} de la cuadrícula" for case in cases)
    if identifier == "FD-BLD-04":
        return "; ".join(f"{case}: Δgasto al terminar 1 L {_env(item['times']['20']['output_gain'], 2)} (posición de "
                         "llegada " + ", ".join(f"{_v(level)} {_env(entry, 2)}"
                                                for level, entry in item["output_gain_20_by_position"].items())
                         + f"); efecto pico en C {_env(item['summary']['peak_effect_ml'], 0)} mL-eq"
                         for case, item in ((case, data["crystalloid"][case]["1000"]) for case in cases))
    if identifier == "FD-BLD-05":
        return "; ".join(f"{case}: retenido a 30′ {_env(item['times']['30']['retained_ml'], 0)} y a 60′ "
                         f"{_env(item['times']['60']['retained_ml'], 0)} mL-eq; retenido / pico a 30′ "
                         f"{_env(item['times']['30']['retained_share'], 2)}, a 60′ {_env(item['times']['60']['retained_share'], 2)}"
                         for case, item in ((case, data["crystalloid"][case]["1000"]) for case in cases))
    if identifier == "FD-BLD-06":
        return "; ".join(f"{case}: dilución pico 1 L {_env(data['crystalloid'][case]['1000']['summary']['peak_dilution'], 2)}, "
                         f"2 L {_env(data['crystalloid'][case]['2000']['summary']['peak_dilution'], 2)} g/dL" for case in cases)
    if identifier == "FD-BLD-07":
        return "; ".join(f"{case}: repuesto a 60′ {_env(data['refill'][case]['acute_loss']['times']['60']['restored_share'], 2)}, "
                         f"a 120′ {_env(data['refill'][case]['acute_loss']['times']['120']['restored_share'], 2)}" for case in cases)
    if identifier == "FD-BLD-08":
        return "; ".join(f"{case}: relleno tras la hemostasia {_env(data['refill'][case]['stopped_bleed']['refill_after_haemostasis_ml'], 0)} "
                         "mL-eq (hoy sigue mientras quede déficit)" for case in cases)
    if identifier == "FD-BLD-09":
        return "; ".join(f"{case}: dilución por relleno a 120′ {_env(data['refill'][case]['acute_loss']['times']['120']['refill_dilution'], 2)} "
                         "g/dL (baja la Hb; no crea GR)" for case in cases)
    raise KeyError(identifier)


def _untreated_evidence(letter: str, data: dict) -> str:
    out = []
    for case in CASES:
        item = data["untreated"][case]
        if letter == "A":
            out.append(f"{case}: ΔHb a 60′ {_env(item['envelopes']['60']['hb_change'], 2)}, a 120′ "
                       f"{_env(item['envelopes']['120']['hb_change'], 2)}")
        elif letter == "B":
            out.append(f"{case}: gasto a 60′ {_env(item['envelopes']['60']['output_rel'], 2)} (n = {item['perfusing']['60']}), "
                       f"a 120′ {_env(item['envelopes']['120']['output_rel'], 2)} (n = {item['perfusing']['120']} de "
                       f"{item['runs']} que siguen perfundiendo); con las detenidas en 0: 60′ "
                       f"{_env(item['with_stopped']['60']['output_rel'], 2)}, 120′ "
                       f"{_env(item['with_stopped']['120']['output_rel'], 2)}")
        elif letter == "C":
            out.append(f"{case}: déficit a 120′ {_env(item['envelopes']['120']['effective_deficit'], 2)} (n = "
                       f"{item['perfusing']['120']} que siguen perfundiendo); con las detenidas en su déficit al "
                       f"detenerse: {_env(item['with_stopped']['120']['effective_deficit'], 2)}; la llegada ya está en "
                       "déficit crítico con la banda de entrega en su punto medio")
        else:
            out.append(f"{case}: {item['stopped_before_120']} de {item['runs']} se detienen antes de 120′")
    return "; ".join(out)


def apply(document: str, block: str) -> str:
    start = document.index(OPENING) + len(OPENING)
    end = document.index(CLOSING)
    return document[:start] + block + "\n" + document[end:]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path)
    parser.add_argument("--write", type=Path)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args(argv)
    if args.write:
        data = json.loads(args.json.read_text(encoding="utf-8"))
        args.write.write_text(apply(args.write.read_text(encoding="utf-8"), render(data)), encoding="utf-8")
        return 0
    text = json.dumps(report(), indent=1, sort_keys=True, default=str)
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "blood_anchors.json").write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
