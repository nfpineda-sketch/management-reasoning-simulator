"""P2I-2S: haemorrhage / preload scale calibration constraints (read-only probes).

    python -m clinical_core.haemorrhage_probes [--out <directory outside the repository>]
    python -m clinical_core.haemorrhage_probes --write <document> --json <probes JSON>

Shadow, offline and read-only. V stays an internal effective-preload coordinate in mL-eq (never
literal blood volume). The probes audit how the GI haemorrhage, transfusion and crystalloid move V
and Hb, explore the curve scale and arrival position on a deterministic grid against qualitative
response requirements, probe transfusion and crystalloid, and give compact GI envelopes. They
choose no value, change no default, band, registry, golden or rule, run no FD-LAC rule or filter
and never rank by similarity to the family engine. Oxygen is read with the accepted P2I-2P
semantics at the candidate reserve 2.5 and the GI arrival band re-anchored (ratio / reserve).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import replace
from pathlib import Path

from . import calibration, gi_reference, lactate_slice
from . import hemodynamic_probes as hp
from .bands import Drift
from .derived import DEFAULT_PROFILE, arrival_state
from .interventions.fluids import Crystalloid, PackedRedCells
from . import legacy_adapter
from .legacy_adapter import LEGACY_LITERALS
from .modules import GIHaemorrhage

RESERVE = hp.RESERVE
CASES = hp.CASES
CURRENT_SCALE = DEFAULT_PROFILE.preload_curve_scale_ml
#: Explored, never approved: the current scale, intermediate values, 1500, 2000 and above.
SCALES = (CURRENT_SCALE, 1000.0, 1250.0, 1500.0, 1750.0, 2000.0, 2500.0, 3000.0)
POSITIONS = (0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.6, 0.7)
#: Incremental-loss anchors after arrival, as minutes of the GI module's untreated bleeding.
ANCHORS = {"small": 30, "moderate": 60, "severe continued": 120, "very severe / prolonged": 240}
ENVELOPE_SCALES = (CURRENT_SCALE, 1250.0, 1500.0, 2000.0, 2500.0)
TRAJECTORY_SCALES = (CURRENT_SCALE, 1500.0, 2000.0)
#: Mixing volumes for the discussion analogue only (orientation, never a parameter): mL.
MIXING_VOLUMES = (3000.0, 4000.0, 5000.0)
#: The PROBE's criteria, read on the module's own anchors (minutes of the inherited bleed literal,
#: so they constrain bleed / lambda and the position, not lambda; not faculty numbers): a quarter of
#: the output lost to the small anchor, or zero flow before the severe one, is too sensitive;
#: output still above 0.9 after the very severe / prolonged anchor is too insensitive.
CLEARLY_TOO_SENSITIVE = {"anchor": "small", "output_below": 0.75, "zero_flow_before": "severe continued"}
CLEARLY_TOO_INSENSITIVE = {"anchor": "very severe / prolonged", "output_above": 0.9}
#: An EXAMPLE window for the minutes of this bleed to halve output from the 57m arrival: only to
#: show how a faculty anchor would narrow the region. Not a proposal.
EXAMPLE_HALF_OUTPUT_MINUTES = (120.0, 240.0)


def _inputs(case: str = CASES[0]) -> dict:
    items = {type(item).__name__: item for scenario in ("L1", "L2", "L3")
             for item in lactate_slice.scenario_inputs(case, scenario)}
    return {"bleed": items["GIHaemorrhage"], "saline": items["Crystalloid"], "prbc": items["PackedRedCells"]}


# P2I-2S-1: the haemorrhage state audit ----------------------------------------------------------------

def implied_bleed(hb0: float, hb_fall: float, v_loss: float, mixing: float) -> dict:
    """Discussion analogue only: the whole-blood loss B and the share refilled by plasma (phi) that
    would give both the Hb fall and the V loss from one bleed in a mixing volume (V read 1:1 as
    circulating volume). Lowest loss consistent with the Hb fall alone: full refill, B = M x dHb / Hb."""
    hb1 = hb0 - hb_fall
    # Hb1 = Hb0 (M - B) / (M - v_loss)  with (1 - phi) B = v_loss
    blood = mixing - hb1 * (mixing - v_loss) / hb0
    return {"mixing_ml": mixing, "minimum_blood_loss_ml": mixing * hb_fall / hb0, "blood_loss_ml": blood,
            "refilled_share": 1.0 - v_loss / blood if blood > 0 else None,
            "blood_loss_over_v_loss": blood / v_loss if v_loss else None}


def implied_prbc_hb(hb0: float, rise: float, volume: float, mixing: float) -> float:
    """The Hb concentration of the transfused unit that the per-unit rise implies (mixing analogue)."""
    return ((hb0 + rise) * (mixing + volume) - hb0 * mixing) / volume


def implied_retained(hb0: float, fall: float, mixing: float) -> float:
    """The retained crystalloid volume that the dilution implies (mixing analogue)."""
    return mixing * (hb0 / (hb0 - fall) - 1.0)


def _saline_peak(case: str) -> float:
    """The V the 2 L bag actually reaches (20 min, no bleeding): the gross gain less the leak meanwhile."""
    bag = replace(_inputs(case)["saline"], id="saline", start_minute=0, volume_ml=2000.0, duration_min=20.0)
    return max(row["V"] for row in _gi_run(case, CURRENT_SCALE, (bag,)))


#: P2I-2T: the Hb drifts this audit describes are no longer in the core (they were the GI module's,
#: the crystalloid's and the red-cell order's own); they stay here as the legacy references they were.
LEGACY_HB_PER_MIN = LEGACY_LITERALS["gi_bleeding_hemoglobin_per_min"][0]
LEGACY_HB_PER_UNIT = LEGACY_LITERALS["blood_hemoglobin_per_unit"][0]


def _legacy_dilution_per_ml() -> float:
    return float(legacy_adapter._engine().GI_BLEED["hemodilution_g_dl_per_ml"])


def audit() -> dict:
    out = {}
    for case in CASES:
        inputs = _inputs(case)
        bleed, saline, prbc = inputs["bleed"], inputs["saline"], inputs["prbc"]
        anchors = gi_reference.canonical_anchors(case)
        bands = gi_reference.case_bands(case)
        two_hours = {"v_loss": bleed.blood_loss_ml_per_min * 120, "hb_fall": LEGACY_HB_PER_MIN * 120}
        saline_given = 2000.0
        saline_peak = saline_given * saline.effective_ml_per_ml
        saline_fall = saline_given * _legacy_dilution_per_ml()
        out[case] = {
            "arrival": {"V": 0.0, "hb": anchors.hb, "preload_fraction_band": [bands["preload_fraction"].lower,
                                                                               bands["preload_fraction"].midpoint,
                                                                               bands["preload_fraction"].upper],
                        "reference_preload_fraction_band": [bands["reference_preload_fraction"].lower,
                                                            bands["reference_preload_fraction"].midpoint,
                                                            bands["reference_preload_fraction"].upper]},
            "bleed": {"v_ml_eq_per_min": bleed.blood_loss_ml_per_min, "hb_g_dl_per_min": LEGACY_HB_PER_MIN,
                      "hb_per_v": LEGACY_HB_PER_MIN / bleed.blood_loss_ml_per_min,
                      "fraction_with_ppi": bleed.fraction_with_ppi,
                      "fraction_after_haemostasis": bleed.fraction_after_hemostasis, **two_hours,
                      "relative_hb_fall": two_hours["hb_fall"] / anchors.hb,
                      "implied": [implied_bleed(anchors.hb, two_hours["hb_fall"], two_hours["v_loss"], mixing)
                                  for mixing in MIXING_VOLUMES]},
            "prbc": {"v_ml_eq_per_unit": prbc.volume_ml_per_unit, "hb_g_dl_per_unit": LEGACY_HB_PER_UNIT,
                     "implied_unit_hb_g_dl": [implied_prbc_hb(anchors.hb, LEGACY_HB_PER_UNIT, prbc.volume_ml_per_unit,
                                                              mixing) for mixing in MIXING_VOLUMES]},
            "saline_2l": {"v_gross_gain_ml_eq": saline_peak, "v_peak_in_run_ml_eq": _saline_peak(case),
                          "v_retained_ml_eq": saline_peak * (1 - saline.transient_share),
                          "leak_tau_min": saline.leak_tau_min, "hb_fall": saline_fall,
                          "dilution_independent_of_leak": True,
                          "implied_retained_ml": [implied_retained(anchors.hb, saline_fall, mixing)
                                                  for mixing in MIXING_VOLUMES],
                          "v_per_implied_retained_ml": [saline_peak * (1 - saline.transient_share)
                                                        / implied_retained(anchors.hb, saline_fall, mixing)
                                                        for mixing in MIXING_VOLUMES]}}
    return out


# Shared helpers: GI-like and neutral arrivals at a chosen scale / position ---------------------------

def gi_anchors(case: str, position: float | None = None, reserve: float = RESERVE):
    values = calibration.case_values(case, hp.representative())
    values["arrival_delivery_ratio"] /= reserve
    if position is not None:
        values["preload_fraction"] = position
    return gi_reference.candidate_anchors(case, values)


def gi_profile(scale: float, reserve: float = RESERVE, **extra):
    return hp._profile(reserve, **{**hp.representative().profile, "preload_curve_scale_ml": scale, **extra})


def static_row(anchors, profile, loss: float, hb_fall: float) -> dict:
    """The arrival state with V and Hb moved by an incremental loss (no time course)."""
    state = arrival_state(anchors, profile).evolve(V=-float(loss), hb=anchors.hb - hb_fall)
    try:
        row = hp._row(state, anchors, profile, RESERVE, loss)
    except hp.UnresolvedBoundary:
        balance = hp.oxygen_balance(0.0, state.aux.oxygen_demand, RESERVE)
        return {"lost_ml": loss, "V": -loss, "hb": anchors.hb - hb_fall, "filling_ml": None, "output_rel": 0.0,
                "sbp": None, "map": None, "do2": 0.0, "state": balance.state,
                "effective_deficit": balance.effective_deficit,
                "deficit_fraction": balance.effective_deficit / balance.demand, "perfusing": False}
    return {**{name: row[name] for name in ("lost_ml", "V", "hb", "filling_ml", "output_rel", "sbp", "map", "do2",
                                             "state", "effective_deficit", "deficit_fraction")}, "perfusing": True}


# P2I-2S-2: clinical anchor scenarios ----------------------------------------------------------------

def anchor_scenarios() -> dict:
    bleed = _inputs()["bleed"]
    out = {}
    for case in CASES:
        anchors = gi_anchors(case)
        for scale in TRAJECTORY_SCALES:
            profile = gi_profile(scale)
            out[f"{case} {scale:g}"] = {
                name: static_row(anchors, profile, bleed.blood_loss_ml_per_min * minutes,
                                 LEGACY_HB_PER_MIN * minutes) for name, minutes in ANCHORS.items()}
    return out


# P2I-2S-4: the scale / position grid ------------------------------------------------------------------

def _region(outputs: dict, zero_flow: float, losses: dict) -> str:
    if (outputs[CLEARLY_TOO_SENSITIVE["anchor"]] < CLEARLY_TOO_SENSITIVE["output_below"]
            or zero_flow <= losses[CLEARLY_TOO_SENSITIVE["zero_flow_before"]]):
        return "too sensitive by the probe's criterion"
    if outputs[CLEARLY_TOO_INSENSITIVE["anchor"]] > CLEARLY_TOO_INSENSITIVE["output_above"]:
        return "too insensitive by the probe's criterion"
    return "needs a faculty anchor"


def _example(half_minutes: float | None) -> str:
    low, high = EXAMPLE_HALF_OUTPUT_MINUTES
    if half_minutes is None or half_minutes > high:
        return "slower"
    return "faster" if half_minutes < low else "inside"


def grid() -> list:
    """Every scale x position from the 57m arrival (its Hb, re-anchored DO2), the GI bleed applied as
    V and Hb at each anchor; plus the loss to the critical boundary from a normal-DO2 arrival."""
    bleed, prbc = _inputs()["bleed"], _inputs()["prbc"]
    losses = {name: bleed.blood_loss_ml_per_min * minutes for name, minutes in ANCHORS.items()}
    rows = []
    for scale in SCALES:
        for position in POSITIONS:
            anchors, profile = gi_anchors(CASES[0], position), gi_profile(scale)
            points = {name: static_row(anchors, profile, losses[name], LEGACY_HB_PER_MIN * minutes)
                      for name, minutes in ANCHORS.items()}
            outputs = {name: point["output_rel"] for name, point in points.items()}
            zero_flow = hp.zero_flow_distance(position, scale)
            to = {f"{level:g}": hp.loss_to(position, 1.0, level, relative=True, preload_curve_scale_ml=scale)
                  for level in (0.75, 0.5)}
            minutes = {level: (None if loss is None else loss / bleed.blood_loss_ml_per_min)
                       for level, loss in to.items()}
            rows.append({"scale": scale, "position": position, "zero_flow_ml": zero_flow,
                         "bleed_over_scale_per_min": bleed.blood_loss_ml_per_min / scale,
                         "unit_over_scale": prbc.volume_ml_per_unit / scale,
                         "zero_flow_over_scale": zero_flow / scale,
                         "zero_flow_minutes": zero_flow / bleed.blood_loss_ml_per_min,
                         "minutes_to_output": minutes, "example_window": _example(minutes["0.5"]),
                         "points": {name: {key: point[key] for key in ("output_rel", "do2", "deficit_fraction",
                                                                       "perfusing")}
                                    for name, point in points.items()},
                         "loss_to_critical_from_normal_arrival": hp.loss_to(position, 1.0, 1.0 / RESERVE,
                                                                            preload_curve_scale_ml=scale),
                         # A second, independent anchor: the output after one unit's volume (static).
                         "output_after_one_unit": static_row(anchors, profile, -prbc.volume_ml_per_unit,
                                                             -LEGACY_HB_PER_UNIT)["output_rel"],
                         "region": _region(outputs, zero_flow, losses)})
    return rows


# P2I-2S-3 (13-15): trajectories under the GI bleed process from synthetic arrivals ------------------

TRAJECTORY_ARRIVALS = {"normal preload (0.70)": (0.70, ()),
                       "underfilled (0.35)": (0.35, ()),
                       "severely underfilled (0.20)": (0.20, ()),
                       "depressed pump (0.35, P to 0.7 by 10 min)": (0.35, (Drift("pump", "P", 0, 10, -0.03),))}
TRAJECTORY_MINUTES = 240
TRAJECTORY_TIMES = (0, 60, 120, 180, 240)


def trajectories() -> dict:
    bleed = replace(_inputs()["bleed"], id="gi_haemorrhage")
    out = {}
    for name, (position, extra) in TRAJECTORY_ARRIVALS.items():
        for scale in TRAJECTORY_SCALES:
            anchors = hp.positioned(position)
            profile = hp._profile(RESERVE, preload_curve_scale_ml=scale)
            try:
                result = hp.run(anchors, (bleed, *extra), TRAJECTORY_MINUTES, profile)
            except hp.UnresolvedBoundary as error:
                result = hp.run(anchors, (bleed, *extra), int(str(error).split(":")[0].split()[-1]) - 1, profile)
            rows = [hp._row(state, anchors, profile, RESERVE, 0.0) for state in result.states]
            out[f"{name}; {scale:g}"] = {
                "points": {str(minute): {key: rows[minute][key] for key in ("output_rel", "sbp", "hb", "do2", "state",
                                                                            "deficit_fraction")}
                           for minute in TRAJECTORY_TIMES if minute < len(rows)},
                "first_critical": next((row["minute"] for row in rows if row["state"] == "CRITICAL"), None),
                "first_half_output": next((row["minute"] for row in rows if row["output_rel"] <= 0.5), None),
                "zero_flow_minute": None if len(rows) > TRAJECTORY_MINUTES else len(rows)}
    return out


# P2I-2S-6/7: transfusion and crystalloid -------------------------------------------------------------

#: Volume per unit: the current mapping and two smaller effective-preload shares (sensitivity only).
UNIT_VOLUMES = (300.0, 200.0, 120.0)


def _gi_run(case: str, scale: float, items: tuple, minutes: int = 120) -> list:
    anchors, profile = gi_anchors(case), gi_profile(scale)
    result = hp._run(anchors, items, profile) if minutes == hp.MINUTES else hp.run(anchors, items, minutes, profile)
    return [hp._row(state, anchors, profile, RESERVE, 0.0) for state in result.states]


def transfusion() -> dict:
    prbc = _inputs()["prbc"]
    out = {}
    for case in CASES:
        for units, duration in ((1.0, 30.0), (2.0, 60.0)):
            for scale in TRAJECTORY_SCALES:
                for volume in UNIT_VOLUMES:
                    unit = replace(prbc, id="prbc", start_minute=0, units=units, duration_min=duration,
                                   volume_ml_per_unit=volume)
                    rows = _gi_run(case, scale, (unit,), 90)
                    end = rows[-1]
                    out[f"{case}; {units:g} U; {scale:g}; {volume:g}"] = {
                        "before": {key: rows[0][key] for key in ("V", "hb", "output_rel", "do2", "state",
                                                                  "effective_deficit")},
                        "after": {key: end[key] for key in ("V", "hb", "output_rel", "sbp", "do2", "state",
                                                            "effective_deficit")}}
    return out


def transfusion_attribution() -> dict:
    """The 2-unit L3 output rise (bleeding, PPI, haemostasis at 60) by scale and volume per unit; and,
    at the current scale, moving only the unit / lambda or only the bleed / lambda ratio to the value
    a larger lambda would give."""
    out = {}
    for case in CASES:
        items = lactate_slice.scenario_inputs(case, "L3")
        for scale in TRAJECTORY_SCALES[1:]:
            ratio = CURRENT_SCALE / scale
            for label, unit, bleed in (("unit ratio only", ratio, 1.0), ("bleed ratio only", 1.0, ratio),
                                       ("both ratios", ratio, ratio)):
                rows = _gi_run(case, CURRENT_SCALE, _scaled_inputs(items, bleed=bleed, unit=unit))
                out[f"{case}; ratios of {scale:g}; {label}"] = {"peak_output": max(row["output_rel"] for row in rows)}
    for case in CASES:
        items = lactate_slice.scenario_inputs(case, "L3")
        for scale in TRAJECTORY_SCALES:
            for volume in UNIT_VOLUMES:
                varied = tuple(replace(item, volume_ml_per_unit=volume) if isinstance(item, PackedRedCells) else item
                               for item in items)
                rows = _gi_run(case, scale, varied)
                out[f"{case}; {scale:g}; {volume:g}"] = {"peak_output": max(row["output_rel"] for row in rows),
                                                         "peak_do2": max(row["do2"] for row in rows),
                                                         "V_at_60": rows[60]["V"]}
    return out


def crystalloid() -> dict:
    saline = _inputs()["saline"]
    out = {}
    for case in CASES:
        for volume in (1000.0, 2000.0):
            for bleeding in (False, True):
                for scale in TRAJECTORY_SCALES:
                    bag = replace(saline, id="saline", start_minute=0, volume_ml=volume, duration_min=20.0)
                    items = (bag, _inputs(case)["bleed"]) if bleeding else (bag,)
                    rows = _gi_run(case, scale, items)
                    peak = max(rows, key=lambda row: row["output_rel"])
                    out[f"{case}; {volume:g} mL; {'bleeding' if bleeding else 'no bleeding'}; {scale:g}"] = {
                        "peak": {"minute": peak["minute"], "output_rel": peak["output_rel"], "do2": peak["do2"],
                                 "hb": peak["hb"]},
                        "points": {str(minute): {key: rows[minute][key] for key in ("V", "hb", "output_rel", "do2",
                                                                                    "state")}
                                   for minute in (0, 20, 60, 120)}}
    return out


# The gauge: lambda is a unit convention for V -----------------------------------------------------

def _scaled_inputs(items: tuple, volume: float = 1.0, bleed: float = 1.0, unit: float = 1.0) -> tuple:
    """Every V input multiplied: crystalloid by ``volume``, the bleed by ``bleed``, the unit by ``unit``."""
    out = []
    for item in items:
        if isinstance(item, GIHaemorrhage):
            item = replace(item, blood_loss_ml_per_min=item.blood_loss_ml_per_min * bleed * volume)
        elif isinstance(item, PackedRedCells):
            item = replace(item, volume_ml_per_unit=item.volume_ml_per_unit * unit * volume)
        elif isinstance(item, Crystalloid):
            item = replace(item, effective_ml_per_ml=item.effective_ml_per_ml * volume)
        out.append(item)
    return tuple(out)


def gauge() -> dict:
    """V reaches the physiology only as V / lambda: doubling lambda and every V input leaves every
    run unchanged, so only the ratios input / lambda (and the position) are physiology. At the current
    lambda those ratios are the family engine's literals."""
    largest = 0.0
    for case in CASES:
        for scenario in ("L1", "L2", "L3"):
            items = lactate_slice.scenario_inputs(case, scenario)
            base = _gi_run(case, CURRENT_SCALE, items)
            doubled = _gi_run(case, 2 * CURRENT_SCALE, _scaled_inputs(items, volume=2.0))
            largest = max([largest, abs(len(base) - len(doubled))]
                          + [abs(a[name] - b[name]) for a, b in zip(base, doubled) for name in ("output_rel", "do2", "D")])
    inputs = _inputs()
    return {"largest_change_when_doubled": largest,
            "bleed_over_scale_per_min": inputs["bleed"].blood_loss_ml_per_min / CURRENT_SCALE,
            "unit_over_scale": inputs["prbc"].volume_ml_per_unit / CURRENT_SCALE,
            "saline_over_scale_per_ml": inputs["saline"].effective_ml_per_ml / CURRENT_SCALE}


#: The current 57m distance to zero flow, held while lambda (and so the position) changes.
FIXED_ZERO_FLOW = hp.zero_flow_distance(0.35)
FIXED_ZERO_FLOW_SCALES = (600.0, CURRENT_SCALE, 1500.0, 3000.0)


def fixed_zero_flow() -> dict:
    """What the GI data identify: at a fixed distance to zero flow the loss response barely moves
    with lambda, the transfusion response does (it reads the curvature, i.e. the position)."""
    out = {}
    bleed, prbc = _inputs()["bleed"], _inputs()["prbc"]
    for scale in FIXED_ZERO_FLOW_SCALES:
        position = -math.expm1(-FIXED_ZERO_FLOW / scale)
        anchors, profile = gi_anchors(CASES[0], position), gi_profile(scale)
        loss = {name: static_row(anchors, profile, bleed.blood_loss_ml_per_min * minutes,
                                 LEGACY_HB_PER_MIN * minutes)["output_rel"] for name, minutes in ANCHORS.items()}
        half = hp.loss_to(position, 1.0, 0.5, relative=True, preload_curve_scale_ml=scale)
        two_units = static_row(anchors, profile, -2 * prbc.volume_ml_per_unit, -2 * LEGACY_HB_PER_UNIT)["output_rel"]
        out[f"{scale:g}"] = {"position": position, "loss_outputs": loss,
                             "minutes_to_half_output": half / bleed.blood_loss_ml_per_min,
                             "output_after_two_units": two_units}
    return out


# P2I-2S-5: a coherent single-bleed prototype (outside the core) -----------------------------------

def coherent_prototype(case: str, blood_ml_per_min: float, refill_tau_min: float | None, mixing: float,
                       minutes: int = 240, stop_at: int | None = 120) -> list:
    """ILLUSTRATION outside the core: one bleed drives both. Whole blood leaves at the current Hb;
    plasma refills the lost circulating volume first order (``refill_tau_min``; None: no refill)
    toward the ARRIVAL volume (an illustrative target: the arrival is already hypovolaemic, and the
    target, TBD, decides how far a transfusion is later offset);
    Hb = Hb mass / circulating volume; V moves 1:1 with the circulating-volume change (no other
    mapping is assumed). Bleeding stops at ``stop_at``. Nothing here enters a run."""
    hb0 = gi_reference.canonical_anchors(case).hb
    volume, mass, rows = mixing, hb0 * mixing, []
    for minute in range(minutes + 1):
        rows.append({"minute": minute, "V": volume - mixing, "hb": mass / volume})
        bleed = blood_ml_per_min if stop_at is None or minute < stop_at else 0.0
        mass -= bleed * mass / volume
        volume -= bleed
        if refill_tau_min:
            volume += (mixing - volume) * (1 - math.exp(-1 / refill_tau_min))
    return rows


PROTOTYPES = {"V-literal blood loss, no refill": (2.5, None), "V-literal blood loss, refill τ 60": (2.5, 60.0),
              "Hb-consistent blood loss, refill τ 60": (8.0, 60.0)}


def prototypes() -> dict:
    out = {}
    for name, (rate, tau) in PROTOTYPES.items():
        rows = coherent_prototype(CASES[0], rate, tau, 4000.0)
        out[name] = {str(minute): rows[minute] for minute in (0, 60, 120, 180, 240)}
    return out


# P2I-2S-8: GI envelopes ----------------------------------------------------------------------------------

def envelopes() -> dict:
    out = {}
    for case in CASES:
        band = gi_reference.case_bands(case)["preload_fraction"]
        for scale in ENVELOPE_SCALES:
            for level, position in (("lower", band.lower), ("midpoint", band.midpoint), ("upper", band.upper)):
                anchors, profile = gi_anchors(case, position), gi_profile(scale)
                untreated = [hp._row(state, anchors, profile, RESERVE, 0.0)
                             for state in hp._run(anchors, lactate_slice.scenario_inputs(case, "L1"), profile).states]
                definitive = [hp._row(state, anchors, profile, RESERVE, 0.0)
                              for state in hp._run(anchors, lactate_slice.scenario_inputs(case, "L3"), profile).states]
                out[f"{case}; {scale:g}; {level}"] = {
                    "position": position, "zero_flow_ml": hp.zero_flow_distance(position, scale),
                    "untreated": {str(minute): ({key: untreated[minute][key] for key in ("output_rel", "sbp", "map", "do2",
                                                                                         "effective_deficit")}
                                                if minute < len(untreated) else None) for minute in (30, 60, 120)},
                    "definitive": {str(minute): {key: definitive[minute][key] for key in ("output_rel", "hb", "do2",
                                                                                          "effective_deficit")}
                                   for minute in (60, 120)}}
    return out


# The report ----------------------------------------------------------------------------------------


#: P2I-2T (2026-10-27): this audit describes the shadow core before the shared blood state replaced
#: the GI module's independent V and Hb drifts. Its committed JSON and document stay as the historical
#: record they were accepted as (probes digest below) and are not regenerated: the command refuses to
#: produce new results, and only re-renders the committed JSON. None for an authorized re-audit.
HISTORICAL = {"probes_digest": "760627b365b161b166872b932b2bd5cf4fdba6b3507ad17a28215dfb2a8f1357",
              "since": "2026-10-27",
              "reason": "P2I-2T replaced the independent haemorrhage drifts with the shared blood state; this audit "
                        "is the record of the core before it"}


def probes_digest() -> str:
    text = json.dumps({"sources": lactate_slice.slice_sources(), "freeze": calibration.frozen_digest()}, sort_keys=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def report() -> dict:
    return {"probes_digest": probes_digest(), "reserve": RESERVE, "representative": hp.REPRESENTATIVE_KEY,
            "anchors_minutes": ANCHORS, "clearly_criteria": {"too_sensitive": CLEARLY_TOO_SENSITIVE,
                                                             "too_insensitive": CLEARLY_TOO_INSENSITIVE},
            "example_half_output_minutes": list(EXAMPLE_HALF_OUTPUT_MINUTES),
            "audit": audit(), "anchor_scenarios": anchor_scenarios(), "grid": grid(),
            "trajectories": trajectories(), "transfusion": transfusion(),
            "transfusion_attribution": transfusion_attribution(), "crystalloid": crystalloid(),
            "prototypes": prototypes(), "envelopes": envelopes(), "gauge": gauge(),
            "fixed_zero_flow": fixed_zero_flow()}


# Rendering ---------------------------------------------------------------------------------------

OPENING, CLOSING = "<!-- generado:hemorragia -->\n", "<!-- /generado:hemorragia -->"
STATES_ES = hp.STATES_ES
ANCHORS_ES = {"small": "pequeña", "moderate": "moderada", "severe continued": "grave continua",
              "very severe / prolonged": "muy grave o prolongada"}
REGIONS_ES = {"too sensitive by the probe's criterion": "demasiado sensible según el criterio de la sonda",
              "too insensitive by the probe's criterion": "demasiado insensible según el criterio de la sonda",
              "needs a faculty anchor": "requiere un ancla docente"}
EXAMPLE_ES = {"faster": "más rápida", "inside": "dentro", "slower": "más lenta"}
ARRIVALS_ES = {"normal preload (0.70)": "precarga normal (0,70)", "underfilled (0.35)": "infrallenado (0,35)",
               "severely underfilled (0.20)": "infrallenado grave (0,20)",
               "depressed pump (0.35, P to 0.7 by 10 min)": "bomba deprimida (0,35; P a 0,7 en 10 min)"}
PROTOTYPES_ES = {"V-literal blood loss, no refill": "pérdida de sangre = literal de V, sin relleno",
                 "V-literal blood loss, refill τ 60": "pérdida de sangre = literal de V, relleno τ 60",
                 "Hb-consistent blood loss, refill τ 60": "pérdida coherente con la Hb (8 mL/min), relleno τ 60"}
LEVELS_ES = hp.LEVELS_ES


def _n(value, digits: int = 2) -> str:
    return hp._n(value, digits)


def _scale(value) -> str:
    return _n(float(value), 0)


def render(data: dict) -> str:
    data = json.loads(json.dumps(data, sort_keys=True, default=str))
    lines = []
    add = lines.append
    add(f"Generado desde las sondas `{data['probes_digest']}` (`python -m clinical_core.haemorrhage_probes`). Oxígeno con la "
        f"reserva candidata {_n(data['reserve'], 1)} y la banda de llegada re-anclada; representante `{data['representative']}`. "
        "Anclas de pérdida incremental = minutos del sangrado no tratado del módulo GI: "
        + ", ".join(f"{ANCHORS_ES[name]} {minutes} min" for name, minutes in ANCHORS.items())
        + ". V es una coordenada interna (mL-eq), no volumen de sangre.\n")
    add("### 4.1 Auditoría del estado de hemorragia\n")
    add("| Caso | Llegada: V, Hb, banda de posición (ref. euvolémica) | Sangrado: V/min, Hb/min (g/dL), Hb por mL-eq | "
        "2 h de sangrado: ΔV, ΔHb (relativa) | Análogo, sin suponer nada sobre V (mezcla 3 / 4 / 5 L): sangre mínima que "
        "explica la caída de Hb | Análogo SUPONIENDO V = volumen circulante (κ = 1): sangre que daría ambas, fracción "
        "rellenada, sangre / ΔV | GR por unidad: V, Hb; Hb de la unidad implícita | Salino 2 L: ganancia bruta / pico real / "
        "retenido en V, ΔHb; retenido implícito por la dilución; V por mL retenido implícito |")
    add("|---|---|---|---|---|---|---|---|")
    for case in CASES:
        item = data["audit"][case]
        arrival, bleed, prbc, saline = item["arrival"], item["bleed"], item["prbc"], item["saline_2l"]
        implied = "; ".join(f"{_n(row['blood_loss_ml'], 0)} mL, {_n(row['refilled_share'])}, ×{_n(row['blood_loss_over_v_loss'], 1)}"
                            for row in bleed["implied"])
        minimum = " / ".join(_n(row["minimum_blood_loss_ml"], 0) for row in bleed["implied"])
        add(f"| {case} | 0, {_n(arrival['hb'], 1)}, {' / '.join(_n(v) for v in arrival['preload_fraction_band'])} "
            f"({' / '.join(_n(v) for v in arrival['reference_preload_fraction_band'])}) | {_n(bleed['v_ml_eq_per_min'], 1)}, "
            f"{_n(bleed['hb_g_dl_per_min'], 3)}, {_n(bleed['hb_per_v'], 4)} | −{_n(bleed['v_loss'], 0)}, −{_n(bleed['hb_fall'])} "
            f"({_n(100 * bleed['relative_hb_fall'], 0)} %) | {minimum} mL | {implied} | +{_n(prbc['v_ml_eq_per_unit'], 0)}, "
            f"+{_n(prbc['hb_g_dl_per_unit'])}; {' / '.join(_n(v, 1) for v in prbc['implied_unit_hb_g_dl'])} g/dL | "
            f"+{_n(saline['v_gross_gain_ml_eq'], 0)} / +{_n(saline['v_peak_in_run_ml_eq'], 0)} / +{_n(saline['v_retained_ml_eq'], 0)}, "
            f"−{_n(saline['hb_fall'], 1)}; {' / '.join(_n(v, 0) for v in saline['implied_retained_ml'])} mL; "
            f"{' / '.join(_n(v) for v in saline['v_per_implied_retained_ml'])} |")
    add("")
    add("### 4.2 Anclas clínicas de pérdida incremental tras la llegada\n")
    add("| Caso; λ | Ancla | ΔV (mL-eq) | Hb | Llenado efectivo | Gasto | PAS / PAM | DO2 / normal | Estado | Fracción de déficit |")
    add("|---|---|---|---|---|---|---|---|---|---|")
    for case in CASES:
        for scale in TRAJECTORY_SCALES:
            points = data["anchor_scenarios"][f"{case} {scale:g}"]
            for name in ANCHORS:
                row = points[name]
                add(f"| {case}; {_scale(scale)} | {ANCHORS_ES[name]} | {_n(row['V'], 0)} | {_n(row['hb'])} | "
                    f"{_n(row['filling_ml'], 0)} | {_n(row['output_rel'])} | {_n(row['sbp'], 0)} / {_n(row['map'], 0)} | "
                    f"{_n(row['do2'])} | {STATES_ES[row['state']]} | {_n(row['deficit_fraction'])} |")
    add("")
    add("### 4.3 Cuadrícula λ × posición de llegada (desde la llegada de 57m)\n")
    add("λ es una convención de unidades (§4.8): con las entradas fijas, cada fila es una razón sangrado/λ y unidad/λ, "
        "indicadas junto a λ. Cada celda: minutos de este sangrado hasta perder la mitad del gasto / hasta el flujo cero; gasto "
        "tras 1 unidad de GR; región. Criterio DE LA SONDA (minutos del literal heredado de sangrado; no son números docentes): "
        "demasiado sensible si el ancla pequeña (30 min) quita más de un cuarto del gasto o el flujo cero llega antes del ancla "
        "grave (120 min); demasiado insensible si el gasto sigue > 0,9 tras el ancla muy grave (240 min). Ventana de EJEMPLO, "
        f"no propuesta: mitad del gasto en {_n(data['example_half_output_minutes'][0], 0)}–"
        f"{_n(data['example_half_output_minutes'][1], 0)} min.\n")
    add("| λ \\ posición | " + " | ".join(_n(position) for position in POSITIONS) + " |")
    add("|---|" + "---|" * len(POSITIONS))
    for scale in SCALES:
        cells = []
        for position in POSITIONS:
            row = next(item for item in data["grid"] if item["scale"] == scale and item["position"] == position)
            half = row["minutes_to_output"]["0.5"]
            region = {"too sensitive by the probe's criterion": "S", "too insensitive by the probe's criterion": "I",
                      "needs a faculty anchor": "·"}[row["region"]]
            example = {"faster": "<", "inside": "=", "slower": ">"}[row["example_window"]]
            cells.append(f"{_n(half, 0)} / {_n(row['zero_flow_minutes'], 0)}; {_n(row['output_after_one_unit'])}; "
                         f"{region}{example}")
        first = next(item for item in data["grid"] if item["scale"] == scale)
        add(f"| {_scale(scale)} ({_n(first['bleed_over_scale_per_min'], 4)}/min; {_n(first['unit_over_scale'])}) | "
            + " | ".join(cells) + " |")
    add("")
    add("Claves: S demasiado sensible y I demasiado insensible según el criterio de la sonda, · requiere un ancla docente; "
        "< más rápida, = dentro, > más lenta que la ventana de ejemplo.\n")
    add("| λ \\ posición (gasto tras las anclas pequeña · moderada · grave · muy grave; DO2 tras la grave) | "
        + " | ".join(_n(position) for position in POSITIONS) + " |")
    add("|---|" + "---|" * len(POSITIONS))
    for scale in SCALES:
        cells = []
        for position in POSITIONS:
            row = next(item for item in data["grid"] if item["scale"] == scale and item["position"] == position)
            outputs = " · ".join(_n(row["points"][name]["output_rel"]) for name in ANCHORS)
            cells.append(f"{outputs}; {_n(row['points']['severe continued']['do2'])}")
        add(f"| {_scale(scale)} | " + " | ".join(cells) + " |")
    add("")
    add("### 4.4 Trayectorias con el sangrado GI desde llegadas sintéticas (llegada sana, DO2 normal)\n")
    add("| Llegada; λ | " + " | ".join(f"{minute} min: gasto, DO2, estado" for minute in TRAJECTORY_TIMES)
        + " | Primer min crítico | Gasto ≤ 0,5 desde | Flujo cero |")
    add("|---|" + "---|" * (len(TRAJECTORY_TIMES) + 3))
    for name in TRAJECTORY_ARRIVALS:
        for scale in TRAJECTORY_SCALES:
            item = data["trajectories"][f"{name}; {scale:g}"]
            cells = []
            for minute in TRAJECTORY_TIMES:
                point = item["points"].get(str(minute))
                cells.append("—" if point is None else
                             f"{_n(point['output_rel'])}, {_n(point['do2'])}, {STATES_ES[point['state']]}")
            add(f"| {ARRIVALS_ES[name]}; {_scale(scale)} | " + " | ".join(cells)
                + f" | {hp._minute(item['first_critical'])} | {hp._minute(item['first_half_output'])} | "
                f"{hp._minute(item['zero_flow_minute'])} |")
    add("")
    add("### 4.5 Transfusión sin sangrado (1 unidad en 30 min, 2 en 60), por λ y volumen por unidad\n")
    add("| Caso | Unidades | λ | mL-eq por unidad | V | Hb | Gasto | PAS | DO2 (antes → después) | Estado |")
    add("|---|---|---|---|---|---|---|---|---|---|")
    for case in CASES:
        for units in (1.0, 2.0):
            for scale in TRAJECTORY_SCALES:
                for volume in UNIT_VOLUMES:
                    item = data["transfusion"][f"{case}; {units:g} U; {scale:g}; {volume:g}"]
                    after, before = item["after"], item["before"]
                    add(f"| {case} | {_n(units, 0)} | {_scale(scale)} | {_n(volume, 0)} | +{_n(after['V'], 0)} | "
                        f"{_n(before['hb'])} → {_n(after['hb'])} | {_n(after['output_rel'])} | {_n(after['sbp'], 0)} | "
                        f"{_n(before['do2'])} → {_n(after['do2'])} | {STATES_ES[after['state']]} |")
    add("")
    add("Atribución del aumento de gasto en L3 (2 unidades, IBP, hemostasia a los 60 min): gasto máximo por λ y volumen por "
        "unidad; y, con λ 833, moviendo sólo la razón unidad/λ, sólo la razón sangrado/λ o ambas al valor que daría otra λ.\n")
    add("| Caso | λ | 300 mL-eq | 200 mL-eq | 120 mL-eq |")
    add("|---|---|---|---|---|")
    for case in CASES:
        for scale in TRAJECTORY_SCALES:
            add(f"| {case} | {_scale(scale)} | " + " | ".join(
                _n(data["transfusion_attribution"][f"{case}; {scale:g}; {volume:g}"]["peak_output"])
                for volume in UNIT_VOLUMES) + " |")
    add("")
    add("| Caso | Razones de la λ | Sólo unidad/λ | Sólo sangrado/λ | Ambas |")
    add("|---|---|---|---|---|")
    for case in CASES:
        for scale in TRAJECTORY_SCALES[1:]:
            add(f"| {case} | {_scale(scale)} | " + " | ".join(
                _n(data["transfusion_attribution"][f"{case}; ratios of {scale:g}; {label}"]["peak_output"])
                for label in ("unit ratio only", "bleed ratio only", "both ratios")) + " |")
    add("")
    add("### 4.6 Cristaloide solo (en 20 min), con y sin sangrado\n")
    add("| Caso; volumen; sangrado; λ | Pico de gasto (min) | " + " | ".join(f"{minute} min: gasto, Hb, DO2"
                                                                     for minute in (0, 20, 60, 120)) + " |")
    add("|---|---|" + "---|" * 4)
    for case in CASES:
        for volume in (1000.0, 2000.0):
            for bleeding in (False, True):
                for scale in TRAJECTORY_SCALES:
                    item = data["crystalloid"][f"{case}; {volume:g} mL; {'bleeding' if bleeding else 'no bleeding'}; {scale:g}"]
                    cells = " | ".join(f"{_n(item['points'][str(minute)]['output_rel'])}, {_n(item['points'][str(minute)]['hb'])}, "
                                       f"{_n(item['points'][str(minute)]['do2'])}" for minute in (0, 20, 60, 120))
                    add(f"| {case}; {_n(volume, 0)} mL; {'con' if bleeding else 'sin'} sangrado; {_scale(scale)} | "
                        f"{_n(item['peak']['output_rel'])} ({item['peak']['minute']}) | {cells} |")
    add("")
    add("### 4.7 Prototipo de un solo sangrado (FUERA del núcleo; ilustración, mezcla 4 L, sangrado hasta el min 120)\n")
    add("| Prototipo | " + " | ".join(f"{minute} min: V, Hb" for minute in (0, 60, 120, 180, 240)) + " |")
    add("|---|" + "---|" * 5)
    for name in PROTOTYPES:
        points = data["prototypes"][name]
        add(f"| {PROTOTYPES_ES[name]} | " + " | ".join(f"{_n(points[str(minute)]['V'], 0)}, {_n(points[str(minute)]['hb'])}"
                                                       for minute in (0, 60, 120, 180, 240)) + " |")
    add("")
    gauge_ = data["gauge"]
    add("### 4.8 λ es una convención de unidades\n")
    add(f"Con λ y todas las entradas de V duplicadas, L1, L2 y L3 de ambos casos no cambian: diferencia máxima de gasto, DO2 o "
        f"D = {_n(gauge_['largest_change_when_doubled'], 3)}. Con la λ actual, las razones son exactamente los literales "
        f"heredados: sangrado/λ {_n(gauge_['bleed_over_scale_per_min'], 4)} por min, unidad/λ "
        f"{_n(gauge_['unit_over_scale'])}, salino/λ {_n(gauge_['saline_over_scale_per_ml'], 5)} por mL.\n")
    add(f"Distancia al flujo cero fija en {_n(FIXED_ZERO_FLOW, 0)} mL-eq (la de 57m hoy), con λ y la posición cambiando juntas:\n")
    add("| λ | Posición | Gasto tras las anclas pequeña · moderada · grave · muy grave | Mitad del gasto (min) | Gasto tras 2 unidades |")
    add("|---|---|---|---|---|")
    for scale in FIXED_ZERO_FLOW_SCALES:
        item = data["fixed_zero_flow"][f"{scale:g}"]
        add(f"| {_scale(scale)} | {_n(item['position'], 3)} | " + " · ".join(_n(item["loss_outputs"][name]) for name in ANCHORS)
            + f" | {_n(item['minutes_to_half_output'], 0)} | {_n(item['output_after_two_units'])} |")
    add("")
    add("### 4.9 Envolventes GI para la docencia (por λ y posición de llegada)\n")
    add("| Caso; λ; posición | Flujo cero | Sin tratar 30 · 60 · 120 min: gasto (PAS/PAM) DO2 déficit | "
        "Manejo definitivo 60 · 120 min: gasto, Hb, DO2, déficit |")
    add("|---|---|---|---|")
    for case in CASES:
        for scale in ENVELOPE_SCALES:
            for level in ("lower", "midpoint", "upper"):
                item = data["envelopes"][f"{case}; {scale:g}; {level}"]
                untreated = " · ".join(
                    "—" if item["untreated"][str(minute)] is None else
                    f"{_n(item['untreated'][str(minute)]['output_rel'])} ({_n(item['untreated'][str(minute)]['sbp'], 0)}/"
                    f"{_n(item['untreated'][str(minute)]['map'], 0)}) {_n(item['untreated'][str(minute)]['do2'])} "
                    f"{_n(item['untreated'][str(minute)]['effective_deficit'])}" for minute in (30, 60, 120))
                definitive = " · ".join(
                    f"{_n(item['definitive'][str(minute)]['output_rel'])}, {_n(item['definitive'][str(minute)]['hb'])}, "
                    f"{_n(item['definitive'][str(minute)]['do2'])}, {_n(item['definitive'][str(minute)]['effective_deficit'])}"
                    for minute in (60, 120))
                add(f"| {case}; {_scale(scale)}; {_n(item['position'])} ({LEVELS_ES[level]}) | {_n(item['zero_flow_ml'], 0)} | "
                    f"{untreated} | {definitive} |")
    add("")
    return "\n".join(lines)


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
    if HISTORICAL is not None:
        parser.error(f"a historical record since {HISTORICAL['since']} ({HISTORICAL['reason']}): its results are not "
                     "regenerated without authorization")
    text = json.dumps(report(), indent=1, sort_keys=True, default=str)
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "haemorrhage_probes.json").write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
