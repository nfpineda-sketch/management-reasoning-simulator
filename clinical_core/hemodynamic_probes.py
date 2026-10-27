"""P2I-2Q: haemodynamic plausibility before the lactate refilter (read-only probes).

    python -m clinical_core.hemodynamic_probes [--out <directory outside the repository>]
    python -m clinical_core.hemodynamic_probes --write <document> --json <probes JSON>

Shadow, offline and read-only: it audits V -> effective preload -> output -> pressure -> oxygen
delivery -> critical deficit -> collapse on the GI cases and on synthetic states, and changes no
default, band, registry, golden or rule. Oxygen is read with the faculty's P2I-2P semantics at the
candidate extraction reserve (2.0-3.0, midpoint 2.5: CANDIDATE, not approved) and the GI arrival
band re-anchored (ratio / reserve). Collapse burdens are computed here from each trajectory with the
calibration registry's candidate collapse values; the core's collapse rule stays off. No FD-LAC rule
or filter runs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import replace
from pathlib import Path

from . import calibration, decision_pack, gi_reference, lactate_slice
from .bands import ARRIVAL, Drift
from .calibration import REGISTRY
from .derived import (DEFAULT_PROFILE, LEGACY_ML_PER_CIRCULATION_UNIT, arrival_filling, arterial_pressures, derive,
                      effective_delivery, oxygen_balance, preload_position)
from .integration import run
from .legacy_adapter import LEGACY_LITERALS
from .modules import GIHaemorrhage
from .state import Anchors, Channel, UnresolvedBoundary, anchored_state

#: P2I-2P faculty decision 4: candidate physiological band and representative midpoint (not approved).
RESERVE = 2.5
RESERVE_BAND = (2.0, 2.5, 3.0)
CASES = gi_reference.GI_CASES
UNTREATED, PARTIAL, DEFINITIVE = "L1", "L2", "L3"
MINUTES = 120
AUDIT_TIMES = (0, 15, 30, 45, 60, 90, 120)
LOSSES = (0, 100, 200, 300, 400, 500, 750, 1000)
#: The representative: the all-midpoint member of the committed P2I-2R faculty-constrained region
#: (read, not refiltered). Haemodynamics are the same for every admissible candidate at the
#: midpoint preload; this one also keeps D and lactate inside the faculty's envelopes.
REPRESENTATIVE_KEY = ("debt_clearance_tau_min=60,lactate_clearance_tau_min=120,lactate_per_output_deficit=12;"
                      "excess=midpoint;intrinsic=midpoint;preload=midpoint;debt=midpoint;delivery=midpoint")
#: Synthetic arrivals for the incremental-loss table: positions on the preload curve.
POSITIONS = {"GI 57m arrival (0.35)": 0.35, "GI 72f arrival (0.45)": 0.45, "euvolaemic reference (0.70)": 0.70}
PUMPS = (1.0, 0.7)
SCALES = tuple(REGISTRY["preload_curve_scale_ml"].points())
COUPLINGS = (0.0, 1.0)
OUTPUT_LEVELS = (0.75, 0.5)
#: Synthetic collapse values: the calibration registry's candidate midpoints (none approved).
COLLAPSE = {"threshold": REGISTRY["collapse_output_threshold"].midpoint,
            "per_minute": REGISTRY["collapse_burden_per_minute"].midpoint,
            "limits": tuple(REGISTRY["collapse_burden_limit"].points()),
            "repayment_tau_min": REGISTRY["collapse_repayment_tau_min"].midpoint}
#: A synthetic "profound" critical-deficit fraction for the thresholded deficit signal (illustration).
PROFOUND_DEFICIT = 0.5
SIGNALS = ("output", "oxygen_deficit", "profound_oxygen_deficit", "combined")


def _profile(reserve: float = RESERVE, **extra):
    return replace(DEFAULT_PROFILE, oxygen_extraction_reserve=reserve, **extra)


def positioned(position: float) -> Anchors:
    """The neutral healthy arrival placed at ``position`` on the preload curve (a synthetic probe)."""
    return Anchors(**{**ARRIVAL, "preload_fraction": position}, declared={"preload_fraction": "synthetic_probe"})


def zero_flow_distance(position: float, scale: float = DEFAULT_PROFILE.preload_curve_scale_ml) -> float:
    """Effective preload above the zero-output point at arrival, mL-eq: -scale x ln(1 - position)."""
    return -scale * math.log1p(-position)


# Rows: one minute read through haemodynamics and the oxygen balance --------------------------------

def _row(state, anchors, profile, reserve: float, lost: float) -> dict:
    derived = derive(state, anchors, profile)
    position = preload_position(state, anchors, profile)
    arrival_position = preload_position(state, anchors, profile, volume=0.0)
    delivery = effective_delivery(derived.delivery_rel, anchors)
    balance = oxygen_balance(delivery, state.aux.oxygen_demand, reserve)
    return {"minute": state.minute, "lost_ml": lost, "V": state.V,
            "filling_ml": arrival_filling(anchors, profile) + state.V, "position": position,
            "preload_rel": position / arrival_position,
            "afterload": 1.0 / (1.0 + profile.afterload_sensitivity * (state.T - 1.0)), "P": state.P,
            "rhythm_factor": state.R.output_factor / anchors.rhythm.output_factor, "rhythm": state.R.code.value, "hr": derived.pulse_rate_bpm, "output_rel": derived.output_rel,
            "T": state.T, "sbp": derived.sbp, "dbp": derived.dbp, "map": derived.map, "hb": state.hb,
            "hb_ratio": state.hb / anchors.hb, "spo2": derived.spo2, "spo2_ratio": derived.spo2 / anchors.spo2,
            "do2": delivery, "demand": balance.demand, "state": balance.state,
            "effective_deficit": balance.effective_deficit, "deficit_fraction": balance.effective_deficit / balance.demand,
            "D": state.D, "lactate": derived.lactate, "consciousness": derived.consciousness_level}


def _run(anchors, contributors, profile):
    """A run that stops, as lactate_slice's do, where output reaches zero with a pulse (collapse off)."""
    try:
        return run(anchors, contributors, MINUTES, profile)
    except UnresolvedBoundary as error:
        return run(anchors, contributors, int(str(error).split(":")[0].split()[-1]) - 1, profile)


def gi_rows(case: str, candidate, scenario: str | None, reserve: float = RESERVE, **profile_extra) -> list:
    """An engine-produced GI scenario with the arrival band re-anchored (ratio / reserve), minute by
    minute; ``scenario`` None holds the arrival with no input at all (no bleeding). A run whose
    output reaches zero with a pulse stops there (collapse off)."""
    values = calibration.case_values(case, candidate)
    values["arrival_delivery_ratio"] /= reserve
    anchors = gi_reference.candidate_anchors(case, values)
    profile = _profile(reserve, **{**candidate.profile, **profile_extra})
    items = () if scenario is None else lactate_slice.scenario_inputs(case, scenario)
    result = _run(anchors, items, profile)
    bleeds = {item.source for item in items if isinstance(item, GIHaemorrhage)}
    lost, rows = 0.0, []
    for index, state in enumerate(result.states):
        if index:
            lost -= sum(delta.amount for delta in result.records[index - 1].deltas
                        if delta.source in bleeds and delta.channel is Channel.V)
        rows.append(_row(state, anchors, profile, reserve, lost))
    return rows


def probe_rows(contributors: tuple, reserve: float = RESERVE, anchors: Anchors | None = None) -> list:
    """A synthetic run from the neutral healthy arrival (normal DO2 at arrival)."""
    anchors = anchors or Anchors(**ARRIVAL)
    profile = _profile(reserve)
    result = _run(anchors, contributors, profile)
    return [_row(state, anchors, profile, reserve, 0.0) for state in result.states]


def hypoxaemia_rows(reserve: float = RESERVE, low_spo2: float = 45.0, minutes: int = 30) -> list:
    """Severe hypoxaemia with output and Hb preserved, computed OUTSIDE the core: the core's SpO2
    moves only with FiO2 (30 points per unit), so it cannot produce one. SpO2 falls linearly from
    97 % to ``low_spo2`` over ``minutes`` and holds; DO2 = SpO2 / 97."""
    rows = []
    for minute in range(MINUTES + 1):
        spo2 = 97.0 - (97.0 - low_spo2) * min(1.0, minute / minutes)
        balance = oxygen_balance(spo2 / 97.0, 1.0, reserve)
        rows.append({"minute": minute, "output_rel": 1.0, "spo2": spo2, "do2": balance.delivery,
                     "demand": balance.demand, "state": balance.state, "effective_deficit": balance.effective_deficit,
                     "deficit_fraction": balance.effective_deficit, "D": None, "consciousness": None})
    return rows


# Collapse burdens (synthetic, offline) -------------------------------------------------------------

def representative():
    return next(item for item in decision_pack.admissible() if item.key() == REPRESENTATIVE_KEY)


def severity(row: dict, signal: str) -> float:
    """A: the core's output form; B: the critical-deficit fraction; B': only its profound part
    (above PROFOUND_DEFICIT, rescaled to 0-1); C: the larger of A and B."""
    output = max(0.0, COLLAPSE["threshold"] - row["output_rel"]) / COLLAPSE["threshold"]
    deficit = row["deficit_fraction"]
    profound = max(0.0, deficit - PROFOUND_DEFICIT) / (1.0 - PROFOUND_DEFICIT)
    return {"output": output, "oxygen_deficit": deficit, "profound_oxygen_deficit": profound,
            "combined": max(output, deficit)}[signal]


def burden_track(rows: list, signal: str) -> dict:
    """The core's P2E-3 form fed by another signal: minute m adds the severity read at its start
    (the state of minute m - 1), and repays first order while that severity is 0 (the registry's
    candidate repayment). With the output signal it is the core's own burden, minute by minute."""
    burden, track = 0.0, [0.0]
    reached = {f"{limit:g}": None for limit in COLLAPSE["limits"]}
    for before, row in zip(rows, rows[1:]):
        value = severity(before, signal)
        burden = (burden + COLLAPSE["per_minute"] * value if value > 0.0
                  else burden * math.exp(-1.0 / COLLAPSE["repayment_tau_min"]))
        track.append(burden)
        for limit in COLLAPSE["limits"]:
            if reached[f"{limit:g}"] is None and burden >= limit:
                reached[f"{limit:g}"] = row["minute"]
    return {"reached": reached, "peak": max(track), "end": track[-1], "track": track}


# P2I-2Q-1: the untreated GI audit -----------------------------------------------------------------

AUDIT_FIELDS = ("lost_ml", "V", "filling_ml", "position", "preload_rel", "P", "rhythm", "hr", "output_rel", "T",
                "sbp", "dbp", "map", "hb", "do2", "demand", "state", "effective_deficit", "D", "lactate",
                "consciousness")


def _at(rows: list, minutes=AUDIT_TIMES) -> dict:
    return {str(minute): rows[minute] for minute in minutes if minute < len(rows)}


def _slim(row: dict, names=AUDIT_FIELDS) -> dict:
    return {name: row[name] for name in names}


def audit() -> dict:
    out = {}
    bleed_rate = v_interpretation()["bleed_ml_eq_per_min"]
    for case in CASES:
        rows = gi_rows(case, representative(), UNTREATED)
        burdens = {signal: burden_track(rows, signal) for signal in ("output", "oxygen_deficit")}
        end = rows[-1]
        band = gi_reference.case_bands(case)["preload_fraction"]
        out[case] = {
            "points": {minute: {**_slim(row), **{f"burden_{signal}": burdens[signal]["track"][int(minute)]
                                                 for signal in burdens}}
                       for minute, row in _at(rows).items()},
            "collapse_reached": {signal: burdens[signal]["reached"] for signal in burdens},
            "factors_at_end": {"P": end["P"], "rhythm": end["rhythm_factor"], "preload_rel": end["preload_rel"],
                               "afterload": end["afterload"], "output_rel": end["output_rel"],
                               "hb_ratio": end["hb_ratio"], "spo2_ratio": end["spo2_ratio"]},
            "zero_flow": {level: {"position": value, "distance_ml": zero_flow_distance(value),
                                  "minutes_at_bleed_rate": zero_flow_distance(value) / bleed_rate}
                          for level, value in (("lower", band.lower), ("midpoint", band.midpoint),
                                               ("upper", band.upper))}}
    return out


def v_interpretation() -> dict:
    """What moves V, in mL-eq, in the GI scenarios (from the engine-produced inputs)."""
    items = {type(item).__name__: item for scenario in (UNTREATED, PARTIAL, DEFINITIVE)
             for item in lactate_slice.scenario_inputs(CASES[0], scenario)}
    bleed, saline, blood = items["GIHaemorrhage"], items["Crystalloid"], items["PackedRedCells"]
    return {"ml_eq_per_legacy_circulation_unit": LEGACY_ML_PER_CIRCULATION_UNIT,
            "bleed_ml_eq_per_min": bleed.blood_loss_ml_per_min,
            # P2I-2T: the module's former Hb drift and the unit's former Hb step, kept as legacy references.
            "bleed_hb_g_dl_per_min": LEGACY_LITERALS["gi_bleeding_hemoglobin_per_min"][0],
            "bleed_fraction_with_ppi": bleed.fraction_with_ppi,
            "bleed_fraction_after_haemostasis": bleed.fraction_after_hemostasis,
            "saline_effective_ml_eq_per_ml": saline.effective_ml_per_ml, "saline_transient_share": saline.transient_share,
            "saline_leak_tau_min": saline.leak_tau_min, "prbc_ml_eq_per_unit": blood.volume_ml_per_unit,
            "prbc_hb_g_dl_per_unit": LEGACY_LITERALS["blood_hemoglobin_per_unit"][0],
            "curve_scale_ml_eq": DEFAULT_PROFILE.preload_curve_scale_ml,
            "curve_scale_band": list(SCALES)}


# P2I-2Q-2/3/4: synthetic incremental loss --------------------------------------------------------------

def _synthetic(position: float, pump: float, loss: float, reserve: float = RESERVE, **profile_extra) -> dict:
    anchors = positioned(position)
    profile = _profile(reserve, **profile_extra)
    state = anchored_state(anchors).evolve(V=-float(loss), P=pump)
    filling = arrival_filling(anchors, profile) - loss
    try:
        row = _row(state, anchors, profile, reserve, loss)
    except UnresolvedBoundary:
        balance = oxygen_balance(0.0, 1.0, reserve)
        return {"lost_ml": loss, "filling_ml": filling, "position": 0.0, "preload_rel": 0.0, "output_rel": 0.0,
                "sbp": None, "map": None, "do2": 0.0, "state": balance.state,
                "effective_deficit": balance.effective_deficit, "no_output": True}
    return {**{name: row[name] for name in ("lost_ml", "filling_ml", "position", "preload_rel", "output_rel", "sbp",
                                             "map", "do2", "state", "effective_deficit")}, "no_output": False}


def loss_to(position: float, pump: float, output: float, relative: bool = False, **profile_extra) -> float | None:
    """The mL-eq of loss at which output falls to ``output`` (of the state's own no-loss output when
    ``relative``; bisection; None if never within 3 L)."""
    base = _synthetic(position, pump, 0.0, **profile_extra)["output_rel"] if relative else 1.0

    def out(loss):
        return _synthetic(position, pump, loss, **profile_extra)["output_rel"] / base
    if out(0.0) <= output:
        return 0.0
    low, high = 0.0, 3000.0
    if out(high) > output:
        return None
    for _ in range(60):
        middle = (low + high) / 2
        low, high = (middle, high) if out(middle) > output else (low, middle)
    return (low + high) / 2


def volume_loss() -> dict:
    tables = {}
    for name, position in POSITIONS.items():
        for pump in PUMPS:
            tables[f"{name}; P {pump:g}"] = {
                "position": position, "pump": pump,
                "rows": [_synthetic(position, pump, loss) for loss in LOSSES],
                "loss_to_own_output": {f"{level:g}": loss_to(position, pump, level, relative=True)
                                       for level in OUTPUT_LEVELS},
                "loss_to_critical": loss_to(position, pump, 1.0 / RESERVE),
                "zero_flow_ml": zero_flow_distance(position)}
    scales = {f"{scale:g}": {"rows": [_synthetic(0.35, 1.0, loss, preload_curve_scale_ml=scale) for loss in LOSSES],
                             "zero_flow_ml": zero_flow_distance(0.35, scale),
                             "loss_to_critical": loss_to(0.35, 1.0, 1.0 / RESERVE, preload_curve_scale_ml=scale)}
              for scale in SCALES}
    couplings = {f"{coupling:g}": {f"{pump:g}": {"rows": [_synthetic(0.35, pump, loss, pump_preload_coupling=coupling)
                                                       for loss in LOSSES],
                                              "loss_to_critical": loss_to(0.35, pump, 1.0 / RESERVE,
                                                                          pump_preload_coupling=coupling)}
                                     for pump in PUMPS}
                 for coupling in COUPLINGS}
    return {"tables": tables, "scales_at_0_35": scales, "pump_couplings_at_0_35": couplings,
            "critical_output_at_normal_arrival_do2": 1.0 / RESERVE}


# P2I-2Q-4/1: pressure consistency, P2I-2Q-1: oxygen trajectories -----------------------------------

def oxygen_trajectories() -> dict:
    out = {}
    for case in CASES:
        for scenario in (UNTREATED, PARTIAL, DEFINITIVE):
            rows = gi_rows(case, representative(), scenario)
            out[f"{scenario} {case}"] = {minute: _slim(row, ("lost_ml", "V", "output_rel", "sbp", "map", "hb", "do2",
                                                             "state", "effective_deficit", "D", "lactate"))
                                         for minute, row in _at(rows).items()}
    return out


def pressure_form() -> dict:
    """The adopted pressure relation at fixed tone (KD-S4, P2E-4): the MAP / output ratio it implies
    (a resistance relative to arrival's) and the jump of the SBP slope at the knee, per arrival."""
    out = {}
    knee = DEFAULT_PROFILE.low_output_pressure_knee
    for name, anchors in (("GI 57m", gi_reference.canonical_anchors(CASES[0])),
                          ("GI 72f", gi_reference.canonical_anchors(CASES[1])), ("neutral arrival", Anchors(**ARRIVAL))):
        arrival_map = (anchors.sbp + 2 * anchors.dbp) / 3

        def pressures(rel):
            sbp, dbp = arterial_pressures(rel, anchors, DEFAULT_PROFILE)
            return sbp, (sbp + 2 * dbp) / 3
        step = 1e-6
        above = (pressures(knee + step)[0] - pressures(knee)[0]) / step
        below = (pressures(knee)[0] - pressures(knee - step)[0]) / step
        out[name] = {"implied_resistance": {f"{rel:g}": pressures(rel)[1] / rel / arrival_map
                                            for rel in (1.0, 0.75, 0.5, 0.3, 0.2)},
                     "sbp_slope_above_knee": above, "sbp_slope_below_knee": below, "slope_ratio": below / above}
    return out


#: (P, T) states from the neutral arrival: the same derivation, read for perfusion and for pressure.
PRESSURE_PROXY_STATES = ((1.0, 1.0), (0.35, 1.0), (0.25, 3.0))


def pressure_as_perfusion() -> list:
    """Where the core's consciousness reads pressure: a vasoconstricted low-output state keeps SBP."""
    anchors, profile = Anchors(**ARRIVAL), _profile()
    rows = []
    for pump, tone in PRESSURE_PROXY_STATES:
        row = _row(anchored_state(anchors).evolve(P=pump, T=tone), anchors, profile, RESERVE, 0.0)
        rows.append({"P": pump, "T": tone, **{name: row[name] for name in ("output_rel", "sbp", "map", "do2", "state",
                                                                          "consciousness")}})
    return rows


# P2I-2Q-7: transfusion in corrected units ------------------------------------------------------------------

def transfusion() -> dict:
    out = {}
    upper = replace(representative(), delivery="upper")   # a probe variant, not an admissibility claim
    for case in CASES:
        for label, candidate in (("representative", representative()), ("arrival ratio upper", upper)):
            by_reserve = {f"{reserve:g}": gi_rows(case, candidate, DEFINITIVE, reserve) for reserve in RESERVE_BAND}
            rows = by_reserve[f"{RESERVE:g}"]
            out[f"{case} {label}"] = {
                "points": {minute: {**_slim(row, ("V", "hb", "output_rel", "sbp", "dbp", "map", "hr", "demand")),
                                    **{f"do2_{reserve}": items[int(minute)]["do2"] for reserve, items in by_reserve.items()},
                                    **{f"state_{reserve}": items[int(minute)]["state"]
                                       for reserve, items in by_reserve.items()},
                                    "effective_deficit": row["effective_deficit"]}
                           for minute, row in _at(rows).items()},
                "peak_output": max(row["output_rel"] for row in rows),
                "peak_sbp": max(row["sbp"] for row in rows),
                "peak_do2": {reserve: max(row["do2"] for row in items) for reserve, items in by_reserve.items()}}
    return out


# P2I-2Q-8: candidate curve scales (for faculty review; nothing changes canonically) ----------------

#: The current scale, the registry band's upper end and one value outside the band (illustration).
CANDIDATE_SCALES = (DEFAULT_PROFILE.preload_curve_scale_ml, 1500.0, 2000.0)


def scale_candidates() -> dict:
    out = {}
    for scale in CANDIDATE_SCALES:
        item = {"euvolaemic_zero_flow_ml": zero_flow_distance(0.7, scale),
                "euvolaemic_loss_to_critical": loss_to(0.7, 1.0, 1.0 / RESERVE, preload_curve_scale_ml=scale),
                "euvolaemic_loss_to_half_output": loss_to(0.7, 1.0, 0.5, preload_curve_scale_ml=scale), "cases": {}}
        for case in CASES:
            untreated = gi_rows(case, representative(), UNTREATED, preload_curve_scale_ml=scale)
            definitive = gi_rows(case, representative(), DEFINITIVE, preload_curve_scale_ml=scale)
            position = gi_reference.case_bands(case)["preload_fraction"].midpoint
            item["cases"][case] = {
                "zero_flow_ml": zero_flow_distance(position, scale),
                "untreated": {minute: _slim(row, ("output_rel", "sbp", "map", "do2", "state", "deficit_fraction"))
                              for minute, row in _at(untreated, (60, 120)).items()},
                "first_minute_output_half": next((row["minute"] for row in untreated if row["output_rel"] <= 0.5), None),
                "definitive_peak_output": max(row["output_rel"] for row in definitive),
                "definitive_peak_sbp": max(row["sbp"] for row in definitive)}
        out[f"{scale:g}"] = item
    return out


# P2I-2Q-5/6: collapse signals and mental status ---------------------------------------------------

COLLAPSE_SCENARIOS = {
    "severe haemorrhage: GI 57m untreated": lambda: gi_rows(CASES[0], representative(), UNTREATED),
    "severe haemorrhage: GI 72f untreated": lambda: gi_rows(CASES[1], representative(), UNTREATED),
    "GI 57m held at arrival, no bleeding": lambda: gi_rows(CASES[0], representative(), None),
    "massive haemorrhage: healthy arrival, V -10 mL-eq/min": lambda: probe_rows(
        (Drift("bleed", "V", 0, MINUTES, -10.0),), anchors=positioned(0.7)),
    "severe anaemia, output preserved: Hb 13 to 3 g/dL": lambda: probe_rows((Drift("hb", "hb", 0, MINUTES, -0.09),)),
    "severe hypoxaemia, output and Hb preserved: SpO2 97 to 45 % (outside the core)": hypoxaemia_rows,
    "extreme hypoxaemia, output and Hb preserved: SpO2 97 to 30 % (outside the core)": lambda: hypoxaemia_rows(
        low_spo2=30.0),
    "recovery: pump to 0.25 by 30 min, restored by 60": lambda: probe_rows(
        (Drift("fall", "P", 0, 30, -0.025), Drift("restore", "P", 30, 60, 0.025))),
    "recovery: GI 57m definitive management": lambda: gi_rows(CASES[0], representative(), DEFINITIVE),
    "partial treatment: GI 57m saline only": lambda: gi_rows(CASES[0], representative(), PARTIAL),
}


def collapse_and_mental_status() -> dict:
    out = {}
    for name, build in COLLAPSE_SCENARIOS.items():
        rows = build()
        out[name] = {"signals": {signal: {key: value for key, value in burden_track(rows, signal).items()
                                          if key != "track"} for signal in SIGNALS},
                     "first_critical": next((row["minute"] for row in rows if row["state"] == "CRITICAL"), None),
                     "points": {minute: {key: row.get(key) for key in ("output_rel", "do2", "state", "deficit_fraction",
                                                                        "D", "consciousness", "sbp", "spo2")}
                                for minute, row in _at(rows, (0, 30, 60, 90, 120)).items()}}
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
    return {"probes_digest": probes_digest(), "reserve": RESERVE, "reserve_band": list(RESERVE_BAND),
            "representative": REPRESENTATIVE_KEY, "collapse": {**COLLAPSE, "limits": list(COLLAPSE["limits"]), "profound_deficit": PROFOUND_DEFICIT},
            "admissible_preload_levels": _preload_levels(), "v_interpretation": v_interpretation(),
            "audit": audit(), "volume_loss": volume_loss(), "oxygen": oxygen_trajectories(),
            "transfusion": transfusion(), "collapse_and_mental_status": collapse_and_mental_status(),
            "scale_candidates": scale_candidates(), "pressure_form": pressure_form(),
            "pressure_as_perfusion": pressure_as_perfusion()}


def _preload_levels() -> dict:
    counts: dict = {}
    for item in decision_pack.admissible():
        counts[item.preload] = counts.get(item.preload, 0) + 1
    return counts


# Rendering ---------------------------------------------------------------------------------------

OPENING, CLOSING = "<!-- generado:hemodinamica -->\n", "<!-- /generado:hemodinamica -->"
STATES_ES = {"ADEQUATE": "adecuada", "COMPENSATED": "compensada", "CRITICAL": "crítica"}
SIGNALS_ES = {"output": "A · gasto", "oxygen_deficit": "B · déficit crítico", "profound_oxygen_deficit":
              "B' · déficit crítico profundo", "combined": "C · combinada (máx. de A y B)"}
SCENARIOS_ES = {
    "severe haemorrhage: GI 57m untreated": "hemorragia grave: GI 57m sin tratar",
    "severe haemorrhage: GI 72f untreated": "hemorragia grave: GI 72f sin tratar",
    "massive haemorrhage: healthy arrival, V -10 mL-eq/min": "hemorragia masiva: llegada sana, V −10 mL-eq/min",
    "severe anaemia, output preserved: Hb 13 to 3 g/dL": "anemia grave con gasto conservado: Hb de 13 a 3 g/dL",
    "severe hypoxaemia, output and Hb preserved: SpO2 97 to 45 % (outside the core)":
        "hipoxemia grave con gasto y Hb conservados: SpO2 de 97 a 45 % (fuera del núcleo)",
    "extreme hypoxaemia, output and Hb preserved: SpO2 97 to 30 % (outside the core)":
        "hipoxemia extrema con gasto y Hb conservados: SpO2 de 97 a 30 % (fuera del núcleo)",
    "recovery: pump to 0.25 by 30 min, restored by 60": "recuperación: bomba a 0,25 hasta el min 30, restituida al 60",
    "recovery: GI 57m definitive management": "recuperación: GI 57m con manejo definitivo",
    "partial treatment: GI 57m saline only": "tratamiento parcial: GI 57m sólo con salino",
    "GI 57m held at arrival, no bleeding": "GI 57m mantenido en la llegada, sin sangrado",
}
POSITIONS_ES = {"GI 57m arrival (0.35)": "llegada GI 57m (0,35)", "GI 72f arrival (0.45)": "llegada GI 72f (0,45)",
                "euvolaemic reference (0.70)": "referencia euvolémica (0,70)"}


RHYTHMS_ES = {"sinus": "sinusal"}
LEVELS_ES = {"lower": "inferior", "midpoint": "media", "upper": "superior"}


def _loss_tables(loss: dict):
    """The incremental-loss tables in POSITIONS x PUMPS order (the JSON sorts its keys)."""
    return [(f"{name}; P {pump:g}", loss["tables"][f"{name}; P {pump:g}"]) for name in POSITIONS for pump in PUMPS]


def _n(value, digits: int = 2) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "sí" if value else "no"
    if isinstance(value, str):
        return STATES_ES.get(value, value)
    return lactate_slice._n(value, digits)


def _minute(value) -> str:
    return "—" if value is None else f"min {value}"


def _sorted(points: dict):
    return sorted(points.items(), key=lambda item: int(item[0]))


def render(data: dict) -> str:
    # The JSON sorts its keys; render the same thing from report() and from the file.
    data = json.loads(json.dumps(data, sort_keys=True, default=str))
    lines = []
    add = lines.append
    collapse = data["collapse"]
    add(f"Generado desde las sondas `{data['probes_digest']}` (`python -m clinical_core.hemodynamic_probes`). Oxígeno "
        f"con la reserva candidata {_n(data['reserve'], 1)} (banda {_n(data['reserve_band'][0], 1)}–"
        f"{_n(data['reserve_band'][-1], 1)}, no aprobada) y la banda de llegada re-anclada. Representante: "
        f"`{data['representative']}`, miembro de la región restringida comprometida de P2I-2R (leída, no refiltrada). "
        f"Cargas de colapso sintéticas con los valores candidatos del registro: umbral de gasto "
        f"{_n(collapse['threshold'], 1)}, {_n(collapse['per_minute'], 1)} por minuto a severidad plena, límites "
        f"{' / '.join(_n(item, 0) for item in collapse['limits'])}, repago τ {_n(collapse['repayment_tau_min'], 0)} min; "
        f"umbral de déficit profundo {_n(collapse['profound_deficit'], 1)}. La regla del núcleo sigue apagada.\n")
    v = data["v_interpretation"]
    add("### 4.1 Qué mueve V (mL-eq) en los escenarios GI\n")
    add("| Entrada | Valor |")
    add("|---|---|")
    for label, value in (("mL-eq por unidad de «circulación» heredada (300 mL de GR = 0,36)", v["ml_eq_per_legacy_circulation_unit"]),
                         ("sangrado activo, mL-eq/min (literal heredado 0,003 × 833)", v["bleed_ml_eq_per_min"]),
                         ("fracción del sangrado con IBP / tras la hemostasia", f"{_n(v['bleed_fraction_with_ppi'])} / "
                                                                                 f"{_n(v['bleed_fraction_after_haemostasis'])}"),
                         ("Hb perdida por minuto de sangrado, g/dL", v["bleed_hb_g_dl_per_min"]),
                         ("glóbulos rojos, mL-eq por unidad / Hb por unidad", f"{_n(v['prbc_ml_eq_per_unit'], 0)} / "
                                                                              f"{_n(v['prbc_hb_g_dl_per_unit'])}"),
                         ("salino, mL-eq por mL infundido; fracción transitoria; τ de fuga (min)",
                          f"{_n(v['saline_effective_ml_eq_per_ml'], 3)}; {_n(v['saline_transient_share'])}; "
                          f"{_n(v['saline_leak_tau_min'], 0)}"),
                         ("escala de la curva de precarga λ, mL-eq (banda del registro)",
                          f"{_n(v['curve_scale_ml_eq'], 1)} ({' / '.join(_n(item, 0) for item in v['curve_scale_band'])})")):
        add(f"| {label} | {_n(value, 4) if isinstance(value, float) else value} |")
    add("")
    add("### 4.2 Auditoría GI sin tratar (L1)\n")
    for case, item in data["audit"].items():
        add(f"**{case}** — hemodinámica:\n")
        add("| Min | Perdido (mL-eq) | V | Llenado efectivo x (mL-eq) | Posición | Respuesta de precarga | P | Ritmo, FC | "
            "Gasto rel. | T | PAS / PAD / PAM |")
        add("|---|---|---|---|---|---|---|---|---|---|---|")
        for minute, row in _sorted(item["points"]):
            add(f"| {minute} | {_n(row['lost_ml'], 0)} | {_n(row['V'], 0)} | {_n(row['filling_ml'], 0)} | "
                f"{_n(row['position'], 3)} | {_n(row['preload_rel'])} | {_n(row['P'])} | "
                f"{RHYTHMS_ES.get(row['rhythm'], row['rhythm'])}, {_n(row['hr'], 0)} | "
                f"{_n(row['output_rel'])} | {_n(row['T'])} | {_n(row['sbp'], 0)} / {_n(row['dbp'], 0)} / {_n(row['map'], 0)} |")
        add("")
        add(f"**{case}** — oxígeno, deuda y colapso sintético:\n")
        add("| Min | Hb | DO2 / normal | Demanda | Estado | Déficit efectivo | D | Lactato | Conciencia | Carga A (gasto) | "
            "Carga B (déficit) |")
        add("|---|---|---|---|---|---|---|---|---|---|---|")
        for minute, row in _sorted(item["points"]):
            add(f"| {minute} | {_n(row['hb'])} | {_n(row['do2'])} | {_n(row['demand'])} | {_n(row['state'])} | "
                f"{_n(row['effective_deficit'])} | {_n(row['D'], 1)} | {_n(row['lactate'])} | {row['consciousness']} | "
                f"{_n(row['burden_output'], 1)} | {_n(row['burden_oxygen_deficit'], 1)} |")
        add("")
        factors = item["factors_at_end"]
        zero = item["zero_flow"]
        add(f"Al final: gasto {_n(factors['output_rel'])} = P {_n(factors['P'])} × ritmo {_n(factors['rhythm'])} × respuesta "
            f"de precarga {_n(factors['preload_rel'])} × poscarga {_n(factors['afterload'])}; la entrega suma Hb "
            f"{_n(factors['hb_ratio'])} y SpO2 {_n(factors['spo2_ratio'])} de la llegada. Distancia al flujo cero en la "
            "llegada (mL-eq, y minutos a 2,5 mL-eq/min): "
            + "; ".join(f"posición {_n(zero[name]['position'])} ({LEVELS_ES[name]}): {_n(zero[name]['distance_ml'], 0)} "
                        f"({_n(zero[name]['minutes_at_bleed_rate'], 0)} min)" for name in LEVELS_ES) + ".\n")
    loss = data["volume_loss"]
    add("### 4.3 Pérdida incremental sintética (estados por lo demás idénticos)\n")
    add(f"Llegada neutra sana colocada en cada posición, Hb y SpO2 sin cambio, tono 1; el índice DO2 supone una entrega "
        f"normal en esa llegada, así que la frontera crítica es un gasto de {_n(loss['critical_output_at_normal_arrival_do2'])}.\n")
    add("| Llegada; bomba | " + " | ".join(f"−{loss_ml} mL-eq" for loss_ml in LOSSES) + " |")
    add("|---|" + "---|" * len(LOSSES))
    for name, table in _loss_tables(loss):
        position, pump = name.split("; ")
        cells = " | ".join(("sin gasto" if row["no_output"] else
                            f"{_n(row['output_rel'])} · PAS {_n(row['sbp'], 0)} · {_n(row['state'])}")
                           for row in table["rows"])
        add(f"| {POSITIONS_ES[position]}; {pump.replace('.', ',')} | {cells} |")
    add("")
    add("| Llegada; bomba | Pérdida hasta 75 % / 50 % de su propio gasto | Pérdida hasta la frontera crítica | Distancia al flujo cero |")
    add("|---|---|---|---|")
    for name, table in _loss_tables(loss):
        position, pump = name.split("; ")
        own = table["loss_to_own_output"]
        add(f"| {POSITIONS_ES[position]}; {pump.replace('.', ',')} | {_n(own['0.75'], 0)} / {_n(own['0.5'], 0)} | "
            f"{_n(table['loss_to_critical'], 0)} | {_n(table['zero_flow_ml'], 0)} |")
    add("")
    add("Escala λ en la posición 0,35 (bomba normal), gasto por pérdida:\n")
    add("| λ (mL-eq) | " + " | ".join(f"−{loss_ml}" for loss_ml in LOSSES) + " | Pérdida hasta la frontera crítica | Flujo cero |")
    add("|---|" + "---|" * (len(LOSSES) + 2))
    for scale, item in sorted(loss["scales_at_0_35"].items(), key=lambda item: float(item[0])):
        add(f"| {_n(float(scale), 0)} | " + " | ".join(_n(row["output_rel"]) for row in item["rows"])
            + f" | {_n(item['loss_to_critical'], 0)} | {_n(item['zero_flow_ml'], 0)} |")
    add("")
    add("Acoplamiento bomba–precarga c en la posición 0,35:\n")
    add("| c | P | " + " | ".join(f"−{loss_ml}" for loss_ml in LOSSES) + " | Pérdida hasta la frontera crítica |")
    add("|---|---|" + "---|" * (len(LOSSES) + 1))
    for coupling, by_pump in loss["pump_couplings_at_0_35"].items():
        for pump, item in by_pump.items():
            add(f"| {coupling} | {pump.replace('.', ',')} | " + " | ".join(_n(row["output_rel"]) for row in item["rows"])
                + f" | {_n(item['loss_to_critical'], 0)} |")
    add("")
    add("### 4.4 DO2 corregido y déficit crítico en L1, L2 y L3 (representante)\n")
    add("| Escenario y caso | Min | Perdido | V | Gasto | PAS | Hb | DO2 / normal | Estado | Déficit efectivo | D | Lactato |")
    add("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for name, points in data["oxygen"].items():
        for minute, row in _sorted(points):
            add(f"| {name} | {minute} | {_n(row['lost_ml'], 0)} | {_n(row['V'], 0)} | {_n(row['output_rel'])} | "
                f"{_n(row['sbp'], 0)} | {_n(row['hb'])} | {_n(row['do2'])} | {_n(row['state'])} | "
                f"{_n(row['effective_deficit'])} | {_n(row['D'], 1)} | {_n(row['lactate'])} |")
    add("")
    add("### 4.5 Transfusión de 2 unidades (L3) en unidades corregidas\n")
    add("| Caso | Min | V | Hb | Gasto | PAS / PAM | FC | Demanda | DO2 / normal con ρ 2 · 2,5 · 3 | Estado con ρ 2 · 2,5 · 3 | "
        "Déficit efectivo |")
    add("|---|---|---|---|---|---|---|---|---|---|---|")
    for name, item in data["transfusion"].items():
        for minute, row in _sorted(item["points"]):
            reserves = [f"{reserve:g}" for reserve in data["reserve_band"]]
            add(f"| {name.replace('representative', 'representante').replace('arrival ratio upper', 'relación de llegada superior')} "
                f"| {minute} | {_n(row['V'], 0)} | {_n(row['hb'])} | {_n(row['output_rel'])} | "
                f"{_n(row['sbp'], 0)} / {_n(row['map'], 0)} | {_n(row['hr'], 0)} | {_n(row['demand'])} | "
                + " · ".join(_n(row[f"do2_{reserve}"]) for reserve in reserves) + " | "
                + " · ".join(_n(row[f"state_{reserve}"]) for reserve in reserves) + f" | {_n(row['effective_deficit'])} |")
    add("")
    add("### 4.6 Señales de colapso y estado mental\n")
    add("| Escenario | Primer minuto crítico | Señal | Alcanza " + " / ".join(_n(item, 0) for item in collapse["limits"])
        + " | Carga máxima | Carga al final |")
    add("|---|---|---|---|---|---|")
    for name in COLLAPSE_SCENARIOS:
        item = data["collapse_and_mental_status"][name]
        for signal in SIGNALS:
            result = item["signals"][signal]
            reached = " / ".join(_minute(result["reached"][f"{limit:g}"]) for limit in collapse["limits"])
            add(f"| {SCENARIOS_ES[name]} | {_minute(item['first_critical'])} | {SIGNALS_ES[signal]} | {reached} | "
                f"{_n(result['peak'], 1)} | {_n(result['end'], 1)} |")
    add("")
    add("| Escenario | Min | Gasto | DO2 / normal | Estado | Fracción de déficit | D | Conciencia del núcleo | PAS | SpO2 |")
    add("|---|---|---|---|---|---|---|---|---|---|")
    for name in COLLAPSE_SCENARIOS:
        item = data["collapse_and_mental_status"][name]
        for minute, row in _sorted(item["points"]):
            add(f"| {SCENARIOS_ES[name]} | {minute} | {_n(row['output_rel'])} | {_n(row['do2'])} | {_n(row['state'])} | "
                f"{_n(row['deficit_fraction'])} | {_n(row['D'], 1)} | {_n(row['consciousness'], 0)} | "
                f"{_n(row['sbp'], 0)} | {_n(row['spo2'], 0)} |")
    add("")
    add("### 4.7 Forma de la presión a tono fijo\n")
    add("Resistencia implícita (PAM / gasto, relativa a la de llegada) y salto de la pendiente de la PAS en la rodilla "
        "(0,5 de presión relativa).\n")
    add("| Llegada | Resistencia implícita con gasto 1 · 0,75 · 0,5 · 0,3 · 0,2 | Pendiente de la PAS sobre / bajo la rodilla "
        "(mmHg por unidad) | Salto |")
    add("|---|---|---|---|")
    for name, item in data["pressure_form"].items():
        resistance = item["implied_resistance"]
        add(f"| {name} | " + " · ".join(_n(resistance[key]) for key in ("1", "0.75", "0.5", "0.3", "0.2"))
            + f" | {_n(item['sbp_slope_above_knee'], 0)} / {_n(item['sbp_slope_below_knee'], 0)} | "
            f"×{_n(item['slope_ratio'], 1)} |")
    add("")
    add("La presión como sustituto de la perfusión (llegada neutra):\n")
    add("| P | T | Gasto | PAS / PAM | DO2 / normal | Estado | Conciencia del núcleo |")
    add("|---|---|---|---|---|---|---|")
    for row in data["pressure_as_perfusion"]:
        add(f"| {_n(row['P'])} | {_n(row['T'])} | {_n(row['output_rel'])} | {_n(row['sbp'], 0)} / {_n(row['map'], 0)} | "
            f"{_n(row['do2'])} | {_n(row['state'])} | {row['consciousness']} |")
    add("")
    add("### 4.8 Escalas candidatas de la curva (para revisión docente; nada cambia en lo canónico)\n")
    add("| λ (mL-eq) | Euvolemia: flujo cero / frontera crítica / mitad del gasto (mL-eq perdidos) | Caso | Flujo cero en la "
        "llegada | L1 a los 60 min: gasto, PAS, DO2, fracción de déficit | L1 a los 120 min | L1: gasto ≤ 0,5 desde | "
        "L3: gasto y PAS máximos |")
    add("|---|---|---|---|---|---|---|---|")
    for scale, item in sorted(data["scale_candidates"].items(), key=lambda item: float(item[0])):
        for case, row in item["cases"].items():
            points = row["untreated"]
            add(f"| {_n(float(scale), 0)} | {_n(item['euvolaemic_zero_flow_ml'], 0)} / "
                f"{_n(item['euvolaemic_loss_to_critical'], 0)} / {_n(item['euvolaemic_loss_to_half_output'], 0)} | {case} | "
                f"{_n(row['zero_flow_ml'], 0)} | "
                + " | ".join(f"{_n(points[minute]['output_rel'])}, {_n(points[minute]['sbp'], 0)}, "
                             f"{_n(points[minute]['do2'])}, {_n(points[minute]['deficit_fraction'])}" for minute in ("60", "120"))
                + f" | {_minute(row['first_minute_output_half'])} | {_n(row['definitive_peak_output'])}, "
                f"{_n(row['definitive_peak_sbp'], 0)} |")
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
        (args.out / "hemodynamic_probes.json").write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
