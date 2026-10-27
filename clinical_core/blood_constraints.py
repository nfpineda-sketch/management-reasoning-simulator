"""P2I-2V / P2I-2V-R: the faculty's shared-blood anchors as operational constraints, frozen before filtering.

    python -m clinical_core.blood_constraints --sensitivity [--out <directory outside the repository>]
    python -m clinical_core.blood_constraints --filter --out <directory outside the repository>
    python -m clinical_core.blood_constraints --digest

Shadow, offline and read-only. The faculty approved patient-level envelopes for the shared haemorrhage
state (2026-10-27): the untreated output and Hb change of each GI case, FD-BLD-01..09 and the second-unit
rule. This module transcribes them as data (``DECISIONS``), states how each one is read from the model
(``IMPLEMENTATION``: every choice the faculty did not supply), declares the alternative readings in
advance (``VARIANTS``), and filters the P2I-2U candidate region with them (P2I-2V-2). It was frozen and
committed before the filter ran on any candidate of that region (P2I-2V-1): ``freeze_digest`` pins the
decisions, the readings, the variants and every clinical_core source the filter can read. The checks
run before the freeze (``sensitivity``, ``evaluate``) use only OFF-GRID probe points, never a candidate.

The envelopes are clinical envelopes, never exact targets: a constraint asks whether a reading falls
inside one, and nothing is fitted to its midpoint. No lactate, no legacy trajectory, no SBP or MAP and
no direct V or Hb write enters any constraint: every Hb and volume reading comes from the shared blood
state. The survivors are a FACULTY-CONSTRAINED SHARED-BLOOD CANDIDATE REGION, never approved parameter
values; no value is chosen among them, by frequency or otherwise.

P2I-2V-R (2026-10-27, refrozen before the refilter): the faculty withdrew the minimum untreated Hb
fall (U-HB v2: 0 to an upper bound, plus the invariant that untreated haemorrhage never raises Hb);
FD-BLD-03 is FACULTY_APPROVED_QUALITATIVE and NOT_YET_HARD_FILTER (reported, never filtering); V5 is
implemented exactly as declared in P2I-2V; the primary reading uses one common GI-family bleed rate
for both cases, case-specific rates being the sensitivity variant V8. The grid is unchanged. The
P2I-2V filter (freeze cfb8e508...) stays its historical record. V4's +250 mL-eq challenge is a
counterfactual reading of the preload curve, not a trajectory: no trajectory writes V or Hb directly.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from dataclasses import replace
from pathlib import Path

from . import blood_anchors, gi_reference
from .bands import BloodLoss
from .derived import derive, preload_position
from .integration import run
from .provenance import BloodProcess

CASES = gi_reference.GI_CASES
DECIDED = "2026-10-27"

# The faculty decisions (data) ---------------------------------------------------------------------------

#: What the faculty approved, transcribed. Envelopes are inclusive (low, high); minutes are from the
#: start of the scenario. Statements without a number are kept as text and read by IMPLEMENTATION.
DECISIONS = {
    "untreated_output": {
        "meaning": "effective output relative to the case's authored arrival output, untreated active bleeding",
        "gi_bleed_57m": {30: (0.85, 0.95), 60: (0.70, 0.85), 120: (0.45, 0.65)},
        "gi_bleed_72f": {30: (0.90, 0.98), 60: (0.80, 0.92), 120: (0.60, 0.78)},
        "note": "clinical calibration envelopes, not legacy targets; SBP / MAP stay context only",
    },
    "untreated_hb_fall": {
        "version": "v2 (P2I-2V-R): the mandatory minimum decline is withdrawn",
        "meaning": "Hb fall (g/dL) by the minute, untreated active bleeding: a concentration envelope arising from "
                   "shared blood-state physiology, with no minimum (whole-blood loss takes red cells and plasma "
                   "together, so Hb may change little at first; its later decline follows refill, fluid, "
                   "redistribution, ongoing loss and mixing); no Hb/min drift may be recreated",
        "gi_bleed_57m": {60: (0.0, 0.5), 120: (0.0, 0.9)},
        "gi_bleed_72f": {60: (0.0, 0.4), 120: (0.0, 0.7)},
        "invariant": "with ongoing haemorrhage and no red-cell source, Hb must not rise because of the haemorrhage "
                     "process itself; any rise needs an explicit volume / red-cell explanation",
    },
    "untreated_hb_fall_v1_withdrawn": {
        "meaning": "P2I-2V's envelopes, withdrawn by the faculty in P2I-2V-R (too restrictive: Hb is a "
                   "concentration, not an instantaneous measure of blood loss)",
        "gi_bleed_57m": {60: (0.2, 0.5), 120: (0.4, 0.9)},
        "gi_bleed_72f": {60: (0.1, 0.4), 120: (0.3, 0.7)},
    },
    "FD-BLD-01": {
        "meaning": "Hb increment from one packed red-cell unit, approximately; not a fixed +1 g/dL rule; after "
                   "reasonable mixing, absent an overwhelming simultaneous loss",
        "envelope": (0.7, 1.2),
    },
    "FD-BLD-02": {
        "meaning": "relative effective-output increase from one unit in a preload-responsive underfilled state: "
                   "clinical upper / behavioural envelopes, not mandatory responses; a less preload-responsive "
                   "state may respond less; no fixed increment is forced",
        "gi_bleed_57m": (0.15, 0.40),
        "gi_bleed_72f": (0.10, 0.30),
    },
    "FD-BLD-03": {
        "meaning": "one unit must not reliably normalize effective output in either GI case; 72f may approach an "
                   "adequate state when appropriately preload responsive; 57m should not move from severe "
                   "haemorrhagic physiology to fully normalized / euvolaemic output from one unit alone",
        "revision": "P2I-2V-R: the clinical decision stands, but the preload positions 0.6 / 0.7 come from candidate "
                    "internal bands, not from a faculty-approved definition of normalization: reported "
                    "diagnostically, never used to reject a candidate, until BP / HR / output-reference calibration "
                    "defines normalization; FD-BLD-02 stays the quantitative bound on the one-unit response",
    },
    "second_unit": {
        "meaning": "as preload responsiveness is exhausted, the haemodynamic benefit of unit 2 is at most that of "
                   "unit 1; the structural ~0.70 ratio is not approved as a physiological constant; Hb increments "
                   "may stay similar, modified by dilution and ongoing loss",
    },
    "FD-BLD-04": {
        "meaning": "1 L isotonic crystalloid in these hypovolaemic adults: initial / early effective circulating "
                   "contribution, as a share of the volume infused (~150-300 mL per litre); a clinical envelope, "
                   "not an exact conversion; the output response stays state-dependent",
        "envelope": (0.15, 0.30),
    },
    "FD-BLD-05": {
        "meaning": "share of the infused volume still contributing to the circulation; broad envelopes for this "
                   "reduced model; no exact exponential is forced",
        "envelopes": {30: (0.15, 0.25), 60: (0.10, 0.20), 120: (0.05, 0.15)},
    },
    "FD-BLD-06": {
        "meaning": "temporary Hb reduction (g/dL) from crystalloid in these modelled adults, partially reversing "
                   "as the intravascular effect redistributes; not universal human limits",
        "envelopes": {1000: (0.2, 0.5), 2000: (0.4, 0.8)},
    },
    "FD-BLD-07": {
        "meaning": "share of an acute circulating-volume deficit restored by endogenous refill; broad envelopes "
                   "are intentional",
        "envelopes": {60: (0.10, 0.25), 120: (0.20, 0.45), 240: (0.30, 0.60)},
    },
    "FD-BLD-08": {
        "meaning": "yes: plasma refill continues after haemostasis while a circulating-volume deficit remains and "
                   "refill capacity remains available; stopping the bleeding does not stop refill instantly",
    },
    "FD-BLD-09": {
        "meaning": "refill raises plasma / circulating volume, adds no red-cell mass, so it progressively dilutes "
                   "Hb; no fixed g/dL decrement is approved: the magnitude emerges from the shared blood state",
    },
    "bleed_rate_authority": {
        "meaning": "authority policy for the GI bleed rate: a verified case-specific rate or severity wins; an "
                   "approved GI-family value is only a fallback; with neither, migration fails closed. The policy "
                   "category only: no numeric bleed rate is approved",
        "family": "gi_bleed", "parameter": "blood_loss_ml_per_min", "policy": "CASE_OVERRIDES_FAMILY_DEFAULT",
    },
    "bleed_rate_analysis": {
        "meaning": "P2I-2V-R: for this calibration analysis the primary uses one common GI-family candidate rate for "
                   "both cases (no case declares a verified rate, and case differences are not to be explained "
                   "prematurely by separate rates); case-specific rates are the sensitivity variant. The production "
                   "authority policy is unchanged and no family default is populated",
    },
}
#: FD-BLD decisions: clinical behaviour / envelope approved; hidden model parameters remain unapproved.
FD_BLD_STATUS = {f"FD-BLD-0{index}": "FACULTY_APPROVED" for index in range(1, 10)}
FD_BLD_STATUS["FD-BLD-03"] = "FACULTY_APPROVED_QUALITATIVE / NOT_YET_HARD_FILTER"
U_HB_STATUS = "FACULTY_APPROVED v2"
APPROVAL_SCOPE = "clinical behavior/envelope approved; hidden model parameters remain unapproved"

# How each decision is read (the implementation choices the faculty did not supply) --------------------

MINUTES_OUTPUT = (30, 60, 120)
MINUTES_HB = (60, 120)
#: Blood-state quantities do not depend on lambda / kappa, the arrival position or rho (verified); they are
#: read with these haemodynamics, under which no surface stops, so no candidate is dropped from a blood
#: constraint because its circulation stopped: that is judged by the output envelopes.
BLOOD_READING = {"preload_scale_over_kappa_ml": 1500.0, "preload_fraction": "upper"}
UNIT_READ, SECOND_UNIT_READ = 30, 60
#: FD-BLD-03: the euvolaemic reference each case must not reach after one unit, as a point of the case's
#: reference_preload_fraction band (gi_reference): 57m not even its lower bound, 72f not its midpoint.
NORMALIZED_AT = {"gi_bleed_57m": "lower", "gi_bleed_72f": "midpoint"}
CRYSTALLOID_VOLUMES = (1000.0, 2000.0)
CRYSTALLOID_MINUTES = 140
EARLY_WINDOW = 30
DILUTION_WINDOW = 120
ACUTE_LOSS_ML, ACUTE_LOSS_MIN = 200.0, 10
REFILL_MINUTES = (60, 120, 240)
HAEMOSTASIS_AT, CONTINUE_MINUTES, REFILL_END = 60, tuple(range(61, 71)), 240
CHALLENGE_ML, RESPONSIVE_GAIN = 250.0, 0.10
TOLERANCE = 0.10
#: U-HB v2 invariant: the largest minute-to-minute Hb rise tolerated in the untreated run is numerical only
#: (whole-blood loss leaves Hb unchanged in exact arithmetic; refill lowers it).
HB_RISE_TOLERANCE = 1e-9

IMPLEMENTATION = {
    "envelopes": "inclusive, compared on the unrounded model value; nothing is fitted to a midpoint",
    "untreated": "the case's GI bleed at the candidate's rate from minute 0, no treatment, the candidate's own "
                 "haemodynamics; output relative to arrival read at minutes 30, 60 and 120; a run whose output "
                 "reached zero with a pulse stops there and reads output 0 afterwards, which fails the envelope",
    "untreated_hb": "U-HB v2: Hb fall = authored arrival Hb - Hb at minutes 60 and 120, read from the shared blood "
                    "state, inside [0, the case's upper bound]: no minimum decline; and in the untreated run (ongoing "
                    "haemorrhage, no red-cell source, no fluid) Hb never rises from one minute to the next over "
                    "minutes 0-120 by more than a numerical 1e-9 g/dL",
    "blood_reading": "every Hb, circulating-volume, refill and crystalloid quantity is read from the shared blood "
                     "state with lambda / kappa 1500 and the case's upper position, where no surface stops: blood "
                     "quantities do not depend on lambda / kappa, position or rho (verified on off-grid points, "
                     "and on every untreated candidate that does not stop)",
    "red_cells": "bleeding controlled (no simultaneous loss); unit 1 over minutes 0-30, unit 2 over 30-60 (P2I-2U); "
                 "unit 1 read at minute 30 (end of its infusion; the model mixes at once), unit 2 at minute 60",
    "FD-BLD-01": "Hb at 30 - Hb at 0 inside the envelope, in each case",
    "FD-BLD-02": "(output at 30 - output at 0) / output at 0 must not exceed the case's upper bound; the lower "
                 "bound is not enforced (the faculty: not mandatory; a less preload-responsive state may respond "
                 "less); every grid position lies in the case band below the euvolaemic reference (underfilled)",
    "FD-BLD-03": "DIAGNOSTIC ONLY since P2I-2V-R (never filters): how many survivors would reach the case's "
                 "euvolaemic reference after one unit, read as preload position at or above a point of the candidate "
                 "reference_preload_fraction band (0.6-0.7-0.8): 57m its lower bound and 72f its midpoint, and the "
                 "readings V2 (both midpoint) and V3 (both lower)",
    "second_unit": "output gain of unit 2 (30 to 60) <= output gain of unit 1 (0 to 30), in each case",
    "crystalloid": "the case's GI bleed continues at the candidate's rate; the bag runs over 20 min from minute 0 "
                   "(P2I-2U); compared with the same run without it",
    "FD-BLD-04": "early contribution = the largest retained intravascular crystalloid (in - out) over minutes "
                 "0-30, over the volume infused (1 L); V5 reads instead the largest net effect on C over minutes "
                 "0-30 (C with the bag - C without it, same bleeding), over the volume infused",
    "FD-BLD-05": "retained intravascular crystalloid at minutes 30, 60 and 120 from the start of the infusion, "
                 "over the volume infused (1 L)",
    "FD-BLD-06": "dilution = Hb without the bag - Hb with it, same bleeding; its peak over minutes 0-120 inside "
                 "the volume's envelope (1 L and 2 L); partial reversal: 0 < dilution at 120 < peak",
    "FD-BLD-07": "a synthetic acute loss of 200 mL-eq over 10 min from minute 0 (the P2I-2U surface faculty "
                 "saw); restored share = cumulative refill / volume shed at minutes 60, 120 and 240",
    "FD-BLD-08": "the case's GI bleed stopped completely at minute 60; where at minute 60 a deficit remains (C < 0) "
                 "and refill is below min(capacity, target share x shed), refill must be positive in every "
                 "minute 61-70 and larger at 240 than at 60; refill never exceeds the capacity",
    "FD-BLD-09": "the acute loss with and without refill: wherever refill > 0 at 60, 120 and 240, Hb with refill "
                 "< Hb without; no refill change carries red cells; red-cell content never rises",
    "joint": "P2I-2V-R primary: every model parameter and the bleed rate are common to both cases (one GI-family "
             "candidate rate); the arrival position is per case (a case band). V8 lets the rate differ by case",
    "rho": "no constraint reads rho: it stays in the region and only changes the extraction-state label",
    "region": "the P2I-2U exploration grid, three values per parameter (blood_anchors.EXPLORATION); feasibility "
              "between grid points is not assessed",
}

#: Alternative readings declared before the filter ran; each changes one choice and is reported beside
#: the primary reading, never in its place.
VARIANTS = {
    "V1_envelope_tolerance": "every numeric envelope widened by 10 % of its width at each end",
    "V2_fd03_both_midpoint": "FD-BLD-03 diagnostic read with both cases below the euvolaemic midpoint",
    "V3_fd03_both_lower": "FD-BLD-03 diagnostic read with both cases below the euvolaemic lower bound",
    "V4_fd02_lower_bound_when_responsive": "FD-BLD-02: the lower bound also enforced where a +250 mL-eq "
                                           "circulating challenge at arrival raises output by >= 10 %",
    "V5_fd04_net_effect": "FD-BLD-04: early contribution read as the bag's net effect on C (with - without)",
    "V6_fd06_from_arrival_hb": "FD-BLD-06: dilution read as arrival Hb - Hb with the bag",
    "V7_fd07_500_ml": "FD-BLD-07: acute loss of 500 mL-eq over 10 min",
    "V8_case_specific_bleed_rate": "the bleed rate may differ by case (P2I-2V's primary; P2I-2V-R makes the "
                                   "common rate primary)",
    "V9_fd05_from_end_of_infusion": "FD-BLD-05 read 30, 60 and 120 min after the end of the infusion "
                                    "(minutes 50, 80 and 140)",
    "V10_fd07_from_end_of_loss": "FD-BLD-07 read 60, 120 and 240 min after the end of the acute loss "
                                 "(minutes 70, 130 and 250)",
}

# The candidate region and its structure ---------------------------------------------------------------

PARAMETERS = blood_anchors.PARAMETERS
REGION = {name: tuple(blood_anchors.EXPLORATION[name]) for name in PARAMETERS}
CASE_DIMS = ("bleed_ml_per_min", "preload_fraction")
SHARED = tuple(name for name in PARAMETERS if name not in CASE_DIMS)
#: The constraints that filter (P2I-2V-R: FD-BLD-03 is reported, never filters); READINGS adds the diagnostic.
CONSTRAINTS = ("U-OUT", "U-HB", "FD-BLD-01", "FD-BLD-02", "SECOND-UNIT", "FD-BLD-04", "FD-BLD-05",
               "FD-BLD-06", "FD-BLD-07", "FD-BLD-08", "FD-BLD-09")
DIAGNOSTIC_ONLY = ("FD-BLD-03",)
READINGS = CONSTRAINTS + DIAGNOSTIC_ONLY
CASE_SPECIFIC = "V8_case_specific_bleed_rate"
#: With an empty region, the minimal sets of constraints with no joint survivor, searched up to this size.
CONFLICT_SIZE = 3
B0, LK, POS, BLEED = ("arrival_circulating_volume_ml", "preload_scale_over_kappa_ml", "preload_fraction",
                      "bleed_ml_per_min")
REFILL = ("plasma_refill_target_share", "plasma_refill_tau_min", "plasma_refill_capacity_ml")
UNIT = ("red_cell_unit_hb_g_dl", "red_cell_unit_volume_ml")
BAG = ("crystalloid_effective_ml_per_ml", "crystalloid_leak_tau_min", "crystalloid_transient_share")
#: The table each constraint reads, keyed by these parameters (everything else at the reference).
TABLE_KEYS = {
    "untreated": (BLEED, B0, LK, POS, *REFILL, "reserve"),
    "untreated_blood": (BLEED, B0, *REFILL),
    "red_cells": (B0, *UNIT, LK, POS, "reserve"),
    "retained": BAG,
    "crystalloid": (*BAG, B0, BLEED, *REFILL),
    "acute": (*REFILL, B0),
    "acute_off": (B0,),
    "stopped": (BLEED, B0, *REFILL),
}
READS = {"U-OUT": "untreated", "U-HB": "untreated_blood", "FD-BLD-01": "red_cells", "FD-BLD-02": "red_cells",
         "FD-BLD-03": "red_cells", "SECOND-UNIT": "red_cells", "FD-BLD-04": "retained", "FD-BLD-05": "retained",
         "FD-BLD-06": "crystalloid", "FD-BLD-07": "acute", "FD-BLD-08": "stopped", "FD-BLD-09": "acute"}
#: Representative surviving candidates (P2I-2V-5): rho at its reference; ordered by 57m output at 120,
#: then 72f output at 120, then the parameter values; low / middle / high = first, floor(n / 2)-th, last.
#: With no joint survivor, each case's own survivors in the same way; with none, no representative.
REPRESENTATIVE_LIMIT = 2_000_000
#: Identifiability after filtering (P2I-2V-4), at the grid's resolution, on the joint survivors (each
#: case's survivors when none is joint): one explored value left = WELL_CONSTRAINED; some excluded =
#: PARTIALLY_CONSTRAINED; none excluded = POORLY_IDENTIFIED; structural combinations (kappa, lambda: only
#: lambda / kappa; rho: only rho x the arrival delivery ratio, and no anchor here reads it) =
#: NON_IDENTIFIABLE_SEPARATELY. No value is chosen by its frequency among survivors.
WELL, PARTIAL, POOR, SEPARATELY = ("WELL_CONSTRAINED", "PARTIALLY_CONSTRAINED", "POORLY_IDENTIFIED",
                                   "NON_IDENTIFIABLE_SEPARATELY")
STRUCTURAL = {"volume_preload_kappa": "only lambda / kappa reaches any anchor; Hb never reads kappa",
              "preload_curve_scale_ml": "only lambda / kappa reaches any anchor",
              "reserve": "only rho x the arrival delivery ratio reaches D and the deficit; no constraint reads it"}


# Runs ---------------------------------------------------------------------------------------------------

def _setup(case: str, values: dict, blood: bool = False):
    return blood_anchors.setup(case, **({**values, **BLOOD_READING} if blood else values))


def _items(case: str, scenario: str, values: dict, volume_ml: float | None = None, loss_ml: float | None = None,
           duration_min: float = 20.0) -> tuple:
    if scenario in ("untreated", "red_cells", "stopped_bleed"):
        return blood_anchors.contributors(case, scenario, values)
    made = blood_anchors._templates(case)
    if scenario == "one_unit":
        return (replace(made["unit"], id="constraint-prbc", start_minute=0, units=1.0, duration_min=30.0,
                        stop_minute=None, queued_ahead_units=0.0, volume_ml_per_unit=values["red_cell_unit_volume_ml"],
                        unit_hb_g_dl=values["red_cell_unit_hb_g_dl"]),)
    if scenario == "crystalloid":
        bleed = replace(made["bleed"], blood_loss_ml_per_min=values[BLEED])
        return (bleed, replace(made["bag"], id="constraint-saline", start_minute=0, volume_ml=volume_ml,
                               duration_min=duration_min, stop_minute=None, stopped_by=None, queued_ahead_ml=0.0,
                               effective_ml_per_ml=values["crystalloid_effective_ml_per_ml"],
                               leak_tau_min=values["crystalloid_leak_tau_min"],
                               transient_share=values["crystalloid_transient_share"]))
    if scenario == "acute_loss":
        return (BloodLoss("constraint-acute-loss", 0, ACUTE_LOSS_MIN, loss_ml / ACUTE_LOSS_MIN),)
    raise ValueError(scenario)


def _run(case: str, values: dict, scenario: str, minutes: int, blood: bool = False, **extra):
    anchors, profile, full = _setup(case, values, blood)
    states, stop = blood_anchors.trajectory(anchors, _items(case, scenario, full, **extra), minutes, profile)
    if blood and stop is not None:
        raise AssertionError(f"{case}/{scenario}: the blood reading's haemodynamics stopped at {stop}")
    return anchors, profile, full, states, stop


def _output(state, anchors, profile) -> float:
    return derive(state, anchors, profile).output_rel


def untreated(case: str, values: dict) -> dict:
    """Untreated bleeding with the candidate's own haemodynamics: output (0 once stopped) and Hb."""
    anchors, profile, _, states, stop = _run(case, values, "untreated", max(MINUTES_OUTPUT))
    if abs(_output(states[0], anchors, profile) - 1.0) > 1e-9:
        raise AssertionError(f"{case}: output at arrival is not the authored arrival output")
    output = {m: (_output(states[m], anchors, profile) if m < len(states) else 0.0) for m in MINUTES_OUTPUT}
    hb = {m: (states[m].hb if m < len(states) else None) for m in MINUTES_HB}
    return {"output": output, "hb": hb, "stop": stop}


def _max_rise(states, minutes: int) -> float:
    """The largest minute-to-minute Hb rise over minutes 0..minutes (U-HB v2's invariant)."""
    return max(states[m + 1].hb - states[m].hb for m in range(minutes))


def untreated_blood(case: str, values: dict) -> dict:
    anchors, _, _, states, _ = _run(case, values, "untreated", max(MINUTES_HB), blood=True)
    return {"hb0": states[0].hb, "fall": {m: states[0].hb - states[m].hb for m in MINUTES_HB},
            "hb": {m: states[m].hb for m in MINUTES_HB}, "max_rise": _max_rise(states, max(MINUTES_HB))}


def red_cells(case: str, values: dict) -> dict:
    """Two units with bleeding controlled: Hb, output and position at 0, 30, 60; the +250 challenge."""
    anchors, profile, _, states, stop = _run(case, values, "red_cells", SECOND_UNIT_READ)
    if stop is not None or states[-1].blood.refill_ml != 0.0:
        raise AssertionError(f"{case}: the red-cell surface stopped or refilled")
    minutes = (0, UNIT_READ, SECOND_UNIT_READ)
    first = states[0]
    challenged = first.evolve(V=first.V + profile.volume_preload_kappa * CHALLENGE_ML)
    return {"hb": [states[m].hb for m in minutes], "output": [_output(states[m], anchors, profile) for m in minutes],
            "position": [preload_position(states[m], anchors, profile) for m in minutes],
            "challenge_gain": _output(challenged, anchors, profile) / _output(first, anchors, profile) - 1.0}


def retained(case: str, values: dict, volume_ml: float = 1000.0) -> dict:
    """The bag's retained intravascular volume (in - out) per minute, as a share of the volume infused."""
    _, _, _, states, _ = _run(case, values, "crystalloid", CRYSTALLOID_MINUTES, blood=True, volume_ml=volume_ml)
    share = [(s.blood.crystalloid_in_ml - s.blood.crystalloid_out_ml) / volume_ml for s in states]
    return {"early": max(share[:EARLY_WINDOW + 1]), "share": {m: share[m] for m in (30, 50, 60, 80, 120, 140)},
            "series": share}


def crystalloid(case: str, values: dict, volume_ml: float, baseline: list | None = None) -> dict:
    """Dilution against the same bleeding without the bag; the net effect on C; the retained share."""
    anchors, _, _, states, _ = _run(case, values, "crystalloid", CRYSTALLOID_MINUTES, blood=True, volume_ml=volume_ml)
    if baseline is None:
        baseline = _run(case, values, "untreated", CRYSTALLOID_MINUTES, blood=True)[3]
    window = range(DILUTION_WINDOW + 1)
    dilution = [baseline[m].hb - states[m].hb for m in window]
    from_arrival = [anchors.hb - states[m].hb for m in window]
    net = [(states[m].blood.volume_ml - baseline[m].blood.volume_ml) / volume_ml for m in range(EARLY_WINDOW + 1)]
    share = [(s.blood.crystalloid_in_ml - s.blood.crystalloid_out_ml) / volume_ml for s in states]
    return {"peak": max(dilution), "at_120": dilution[DILUTION_WINDOW], "peak_from_arrival": max(from_arrival),
            "from_arrival_120": from_arrival[DILUTION_WINDOW], "net_early": max(net),
            "retained_early": max(share[:EARLY_WINDOW + 1]),
            "retained": {m: share[m] for m in (30, 50, 60, 80, 120, 140)}}


def acute(case: str, values: dict, loss_ml: float = ACUTE_LOSS_ML, refill: bool = True) -> dict:
    """The synthetic acute loss, with or without refill: the share restored, Hb, and what refill carries."""
    anchors, profile, full = _setup(case, values, blood=True)
    if not refill:
        profile = replace(profile, plasma_refill_target_share=0.0)
    result = run(anchors, _items(case, "acute_loss", full, loss_ml=loss_ml), max(REFILL_MINUTES) + ACUTE_LOSS_MIN,
                 profile)
    states = result.states
    return {"share": {m: states[m].blood.refill_ml / states[m].blood.shed_ml
                      for m in (*REFILL_MINUTES, *(m + ACUTE_LOSS_MIN for m in REFILL_MINUTES))},
            "refill": {m: states[m].blood.refill_ml for m in REFILL_MINUTES},
            "hb": {m: states[m].hb for m in REFILL_MINUTES},
            "cells_never_rise": all(b.blood.red_cells <= a.blood.red_cells for a, b in zip(states, states[1:])),
            "refill_carries_no_cells": all(change.red_cells == 0.0 for record in result.records
                                           for change in record.blood if change.process is BloodProcess.PLASMA_REFILL)}


def stopped(case: str, values: dict) -> dict:
    anchors, profile, _, states, _ = _run(case, values, "stopped_bleed", REFILL_END, blood=True)
    at = states[HAEMOSTASIS_AT].blood
    target = min(profile.plasma_refill_capacity_ml, profile.plasma_refill_target_share * at.shed_ml)
    refill = [s.blood.refill_ml for s in states]
    return {"applies": at.volume_ml < 0 and at.refill_ml < target,
            "continues": all(refill[m] - refill[m - 1] > 0 for m in CONTINUE_MINUTES),
            "grows": refill[REFILL_END] > refill[HAEMOSTASIS_AT],
            "within_capacity": max(refill) <= profile.plasma_refill_capacity_ml,
            "after_ml": refill[REFILL_END] - refill[HAEMOSTASIS_AT]}


# Constraints --------------------------------------------------------------------------------------------

def _bounds(bounds, variant: str | None) -> tuple[float, float]:
    low, high = bounds
    if variant == "V1_envelope_tolerance":
        width = high - low
        return low - TOLERANCE * width, high + TOLERANCE * width
    return low, high


def _inside(value, bounds, variant) -> bool:
    if value is None:
        return False
    low, high = _bounds(bounds, variant)
    return low <= value <= high


def _normalized_at(case: str, variant: str | None) -> float:
    point = {"V2_fd03_both_midpoint": "midpoint", "V3_fd03_both_lower": "lower"}.get(variant, NORMALIZED_AT[case])
    return getattr(gi_reference.case_bands(case)["reference_preload_fraction"], point)


def passes(name: str, case: str, row: dict, variant: str | None = None, off: dict | None = None) -> bool:
    """Whether one table row meets one constraint in one case (``off``: the refill-off acute row)."""
    if name == "U-OUT":
        return all(_inside(row["output"][m], DECISIONS["untreated_output"][case][m], variant) for m in MINUTES_OUTPUT)
    if name == "U-HB":
        return (all(_inside(row["fall"][m], DECISIONS["untreated_hb_fall"][case][m], variant) for m in MINUTES_HB)
                and row["max_rise"] <= HB_RISE_TOLERANCE)
    if name == "FD-BLD-01":
        return _inside(row["hb"][1] - row["hb"][0], DECISIONS["FD-BLD-01"]["envelope"], variant)
    if name == "FD-BLD-02":
        low, high = _bounds(DECISIONS["FD-BLD-02"][case], variant)
        gain = row["output"][1] / row["output"][0] - 1.0
        if gain > high:
            return False
        if variant == "V4_fd02_lower_bound_when_responsive" and row["challenge_gain"] >= RESPONSIVE_GAIN:
            return gain >= low
        return True
    if name == "FD-BLD-03":
        return row["position"][1] < _normalized_at(case, variant)
    if name == "SECOND-UNIT":
        return row["output"][2] - row["output"][1] <= row["output"][1] - row["output"][0]
    if name == "FD-BLD-04":
        # V5 (declared in P2I-2V, implemented in P2I-2V-R): the bag's net effect on C, from the crystalloid row.
        value = row[1000.0]["net_early"] if variant == "V5_fd04_net_effect" else row["early"]
        return _inside(value, DECISIONS["FD-BLD-04"]["envelope"], variant)
    if name == "FD-BLD-05":
        shift = 20 if variant == "V9_fd05_from_end_of_infusion" else 0
        return all(_inside(row["share"][m + shift], bounds, variant)
                   for m, bounds in DECISIONS["FD-BLD-05"]["envelopes"].items())
    if name == "FD-BLD-06":
        for volume in CRYSTALLOID_VOLUMES:
            item = row[volume]
            peak, end = ((item["peak_from_arrival"], item["from_arrival_120"]) if variant == "V6_fd06_from_arrival_hb"
                         else (item["peak"], item["at_120"]))
            if not (_inside(peak, DECISIONS["FD-BLD-06"]["envelopes"][int(volume)], variant) and 0 < end < peak):
                return False
        return True
    if name == "FD-BLD-07":
        shift = ACUTE_LOSS_MIN if variant == "V10_fd07_from_end_of_loss" else 0
        return all(_inside(row["share"][m + shift], bounds, variant)
                   for m, bounds in DECISIONS["FD-BLD-07"]["envelopes"].items())
    if name == "FD-BLD-08":
        return row["within_capacity"] and (not row["applies"] or (row["continues"] and row["grows"]))
    if name == "FD-BLD-09":
        return (row["cells_never_rise"] and row["refill_carries_no_cells"]
                and all(row["hb"][m] < off["hb"][m] for m in REFILL_MINUTES if row["refill"][m] > 0))
    raise KeyError(name)


# Tables over the region -------------------------------------------------------------------------------------

def _grid(region: dict, names: tuple):
    for combination in itertools.product(*(region[name] for name in names)):
        yield combination, dict(zip(names, combination))


def tables(region: dict = REGION, cases=CASES, progress=None) -> dict:
    """Every reading the constraints need, keyed by TABLE_KEYS, with the cross-checks that make the blood
    reading safe: Hb from the candidate's own haemodynamics equals the blood reading wherever the run did
    not stop, and the retained crystalloid is the same whatever the bleeding, B0 or refill."""
    out = {}
    for case in cases:
        say = progress or (lambda *_: None)
        item = {}
        say(case, "untreated")
        item["untreated"] = {key: untreated(case, values) for key, values in _grid(region, TABLE_KEYS["untreated"])}
        say(case, "untreated_blood")
        baselines, item["untreated_blood"] = {}, {}
        for key, values in _grid(region, TABLE_KEYS["untreated_blood"]):
            states = _run(case, values, "untreated", CRYSTALLOID_MINUTES, blood=True)[3]
            baselines[key] = states
            item["untreated_blood"][key] = {"hb0": states[0].hb, "hb": {m: states[m].hb for m in MINUTES_HB},
                                            "fall": {m: states[0].hb - states[m].hb for m in MINUTES_HB},
                                            "max_rise": _max_rise(states, max(MINUTES_HB))}
        names = TABLE_KEYS["untreated"]
        for key, row in item["untreated"].items():
            values = dict(zip(names, key))
            blood = item["untreated_blood"][tuple(values[n] for n in TABLE_KEYS["untreated_blood"])]
            for m in MINUTES_HB:
                if row["hb"][m] is not None and abs(row["hb"][m] - blood["hb"][m]) > 1e-9:
                    raise AssertionError(f"{case}: Hb depends on the haemodynamics at {values}")
        say(case, "red_cells")
        item["red_cells"] = {key: red_cells(case, values) for key, values in _grid(region, TABLE_KEYS["red_cells"])}
        say(case, "retained")
        item["retained"] = {key: retained(case, values) for key, values in _grid(region, TABLE_KEYS["retained"])}
        say(case, "crystalloid")
        item["crystalloid"] = {}
        for key, values in _grid(region, TABLE_KEYS["crystalloid"]):
            base = baselines[tuple(values[n] for n in TABLE_KEYS["untreated_blood"])]
            row = {volume: crystalloid(case, values, volume, base) for volume in CRYSTALLOID_VOLUMES}
            reference = item["retained"][tuple(values[n] for n in BAG)]
            if (abs(row[1000.0]["retained_early"] - reference["early"]) > 1e-12
                    or any(abs(row[1000.0]["retained"][m] - reference["share"][m]) > 1e-12 for m in reference["share"])):
                raise AssertionError(f"{case}: the retained crystalloid depends on more than its kinetics at {values}")
            item["crystalloid"][key] = row
        say(case, "acute")
        for loss in (ACUTE_LOSS_ML, 500.0):
            item[f"acute_{int(loss)}"] = {key: acute(case, values, loss)
                                          for key, values in _grid(region, TABLE_KEYS["acute"])}
            item[f"acute_off_{int(loss)}"] = {key: acute(case, values, loss, refill=False)
                                              for key, values in _grid(region, TABLE_KEYS["acute_off"])}
        say(case, "stopped")
        item["stopped"] = {key: stopped(case, values) for key, values in _grid(region, TABLE_KEYS["stopped"])}
        out[case] = item
    return out


def _source(name: str, variant: str | None) -> str:
    """The table a constraint reads: V5 reads FD-BLD-04 from the crystalloid table (with and without the bag)."""
    return "crystalloid" if name == "FD-BLD-04" and variant == "V5_fd04_net_effect" else READS[name]


def _row(table: dict, case: str, name: str, values: dict, variant: str | None):
    """The row constraint ``name`` reads for a candidate (and the refill-off row for FD-BLD-09)."""
    source = _source(name, variant)
    keys = TABLE_KEYS[source]
    if source == "acute":
        loss = 500 if variant == "V7_fd07_500_ml" else int(ACUTE_LOSS_ML)
        row = table[case][f"acute_{loss}"][tuple(values[n] for n in keys)]
        return row, table[case][f"acute_off_{loss}"][(values[B0],)]
    return table[case][source][tuple(values[n] for n in keys)], None


def _depends(name: str, variant: str | None = None) -> tuple:
    source = _source(name, variant)
    return TABLE_KEYS[source] + ((B0,) if source == "acute" else ())


def masks(table: dict, region: dict, variant: str | None, names=CONSTRAINTS) -> dict:
    """For each case and constraint: shared sub-key -> 9-bit mask over (bleed index, position index)."""
    bleeds, positions = region[BLEED], region[POS]
    out = {}
    for case in table:
        out[case] = {}
        for name in names:
            shared = tuple(n for n in SHARED if n in _depends(name, variant))
            table_name = {}
            for key, values in _grid(region, shared):
                mask = 0
                for b_index, bleed in enumerate(bleeds):
                    for p_index, position in enumerate(positions):
                        candidate = {**values, BLEED: bleed, POS: position}
                        row, off = _row(table, case, name, candidate, variant)
                        if passes(name, case, row, variant, off):
                            mask |= 1 << (3 * b_index + p_index)
                table_name[key] = mask
            out[case][name] = (shared, table_name)
    return out


def _popcount(mask: int) -> int:
    return bin(mask).count("1")


ROWS = tuple(sum(1 << (3 * b + p) for p in range(3)) for b in range(3))
COLUMNS = tuple(sum(1 << (3 * b + p) for b in range(3)) for p in range(3))


def count(table: dict, region: dict, variant: str | None = None, names=CONSTRAINTS, survivors: bool = False,
          built: dict | None = None) -> dict:
    """Survivors over the region: joint with one common bleed rate (the P2I-2V-R primary) or with case-specific
    rates (V8), and each case alone; marginal counts of every explored value; optionally the joint survivors.
    ``built``: masks already computed for this reading (any superset of ``names``)."""
    common = variant != CASE_SPECIFIC
    reading = None if variant == CASE_SPECIFIC else variant
    if built is None:
        built = masks(table, region, reading, names)
    built = {case: {name: built[case][name] for name in names} for case in built}
    cases = list(table)
    index = {n: i for i, n in enumerate(SHARED)}
    projections = {case: [(tuple(index[n] for n in shared), lookup) for shared, lookup in built[case].values()]
                   for case in cases}
    joint = common_total = 0
    alone = {case: 0 for case in cases}
    marginal = {f"{n}": {str(v): 0 for v in region[n]} for n in SHARED}
    for case in cases:
        for n in CASE_DIMS:
            marginal[f"{n}|{case}"] = {str(v): 0 for v in region[n]}
    alone_marginal = {case: {n: {str(v): 0 for v in region[n]} for n in PARAMETERS} for case in cases}
    found = []
    for combination in itertools.product(*(region[n] for n in SHARED)):
        case_masks = {}
        for case in cases:
            mask = 0x1FF
            for positions, lookup in projections[case]:
                mask &= lookup[tuple(combination[i] for i in positions)]
                if not mask:
                    break
            case_masks[case] = mask
        for case in cases:
            n_case = _popcount(case_masks[case])
            alone[case] += n_case
            if n_case:
                for i, n in enumerate(SHARED):
                    alone_marginal[case][n][str(combination[i])] += n_case
                for b, value in enumerate(region[BLEED]):
                    alone_marginal[case][BLEED][str(value)] += _popcount(case_masks[case] & ROWS[b])
                for p, value in enumerate(region[POS]):
                    alone_marginal[case][POS][str(value)] += _popcount(case_masks[case] & COLUMNS[p])
        if len(cases) < 2:
            continue
        a, b = (case_masks[case] for case in cases)
        if common:
            weight = sum(_popcount(a & row) * _popcount(b & row) for row in ROWS)
        else:
            weight = _popcount(a) * _popcount(b)
        if not weight:
            continue
        joint += weight
        for i, n in enumerate(SHARED):
            marginal[n][str(combination[i])] += weight
        for case, mine, other in ((cases[0], a, b), (cases[1], b, a)):
            for bi, value in enumerate(region[BLEED]):
                part = (_popcount(mine & ROWS[bi]) * _popcount(other & ROWS[bi]) if common
                        else _popcount(mine & ROWS[bi]) * _popcount(other))
                marginal[f"{BLEED}|{case}"][str(value)] += part
            for pi, value in enumerate(region[POS]):
                part = (sum(_popcount(mine & ROWS[r] & COLUMNS[pi]) * _popcount(other & ROWS[r]) for r in range(3))
                        if common else _popcount(mine & COLUMNS[pi]) * _popcount(other))
                marginal[f"{POS}|{case}"][str(value)] += part
        if survivors and combination[index["reserve"]] == blood_anchors.REFERENCE["reserve"]:
            for bit_a in range(9):
                if a >> bit_a & 1:
                    for bit_b in range(9):
                        if b >> bit_b & 1 and (not common or bit_a // 3 == bit_b // 3):
                            found.append((combination, bit_a, bit_b))
                            if len(found) > REPRESENTATIVE_LIMIT:
                                raise AssertionError("too many joint survivors to order: refused (frozen limit)")
    result = {"joint": joint, "alone": alone, "marginal": marginal, "alone_marginal": alone_marginal}
    if survivors:
        result["found"] = found
    return result


def region_size(region: dict, cases=CASES, common: bool = False) -> dict:
    shared = math.prod(len(region[n]) for n in SHARED)
    per_case = math.prod(len(region[n]) for n in CASE_DIMS)
    return {"joint": shared * per_case ** len(cases) // (len(region[BLEED]) if common and len(cases) > 1 else 1),
            "alone": shared * per_case}


def _candidate(combination: tuple, bit: int, region: dict) -> dict:
    values = dict(zip(SHARED, combination))
    values[BLEED] = region[BLEED][bit // 3]
    values[POS] = region[POS][bit % 3]
    return values


def classify(marginal: dict, region: dict, keys: dict) -> dict:
    """The frozen identifiability rule, on the explored values that survive (``keys``: label -> parameter)."""
    out = {}
    for label, parameter in keys.items():
        left = [value for value in region[parameter] if marginal[label][str(value)] > 0]
        if parameter in STRUCTURAL:
            out[label] = {"class": SEPARATELY, "left": [str(v) for v in left]}
        elif not left:
            out[label] = {"class": None, "left": []}
        else:
            # A single value left at the edge of the explored grid is bounded by the grid, not identified.
            out[label] = {"class": WELL if len(left) == 1 else PARTIAL if len(left) < len(region[parameter]) else POOR,
                          "left": [str(v) for v in left],
                          "grid_edge": len(left) == 1 and left[0] in (region[parameter][0], region[parameter][-1])}
    for name, why in STRUCTURAL.items():
        out.setdefault(name, {"class": SEPARATELY, "left": None, "why": why})
        out[name]["why"] = why
    return out


# Patient-like trajectories (P2I-2V-5) ------------------------------------------------------------------

def _reading(state, anchors, profile) -> dict:
    item = blood_anchors.reading(state, anchors, profile)
    return {name: item[name] for name in ("minute", "hb", "red_cells_change", "circulating_ml", "position",
                                          "output_rel", "do2", "state", "effective_deficit", "lactate", "sbp", "map",
                                          "refill_ml", "crystalloid_ml")}


def trajectories(case: str, values: dict) -> dict:
    """Every surface with the candidate's own haemodynamics (lactate, SBP and MAP are context only)."""
    out = {}
    anchors, profile, _, states, stop = _run(case, values, "untreated", 120)
    out["untreated"] = {"stop": stop, "rows": [_reading(states[m], anchors, profile) for m in (0, 30, 60, 120)
                                               if m < len(states)]}
    anchors, profile, _, states, stop = _run(case, values, "red_cells", 60)
    out["red_cells"] = {"stop": stop, "rows": [_reading(states[m], anchors, profile) for m in (0, 30, 60)]}
    for volume in CRYSTALLOID_VOLUMES:
        anchors, profile, _, states, stop = _run(case, values, "crystalloid", 120, volume_ml=volume)
        out[f"crystalloid_{int(volume)}"] = {"stop": stop, "rows": [_reading(states[m], anchors, profile)
                                                                    for m in (0, 20, 30, 60, 120) if m < len(states)]}
    anchors, profile, _, states, stop = _run(case, values, "stopped_bleed", REFILL_END)
    out["stopped_bleed"] = {"stop": stop, "rows": [_reading(states[m], anchors, profile)
                                                   for m in (0, HAEMOSTASIS_AT, 120, REFILL_END) if m < len(states)]}
    return out


def evaluate(case: str, values: dict) -> dict:
    """One candidate (or off-grid probe) through every reading and every constraint, primary and variants."""
    full = {**blood_anchors.REFERENCE, **values}
    rows = {"untreated": untreated(case, full), "untreated_blood": untreated_blood(case, full),
            "red_cells": red_cells(case, full), "retained": retained(case, full),
            "crystalloid": {v: crystalloid(case, full, v) for v in CRYSTALLOID_VOLUMES},
            "stopped": stopped(case, full)}
    for loss in (ACUTE_LOSS_ML, 500.0):
        rows[f"acute_{int(loss)}"] = acute(case, full, loss)
        rows[f"acute_off_{int(loss)}"] = acute(case, full, loss, refill=False)
    verdicts = {}
    for variant in (None, *VARIANTS):
        if variant == CASE_SPECIFIC:
            continue
        loss = 500 if variant == "V7_fd07_500_ml" else int(ACUTE_LOSS_ML)
        source = {"U-OUT": rows["untreated"], "U-HB": rows["untreated_blood"],
                  "FD-BLD-04": rows["crystalloid"] if variant == "V5_fd04_net_effect" else rows["retained"],
                  "FD-BLD-05": rows["retained"], "FD-BLD-06": rows["crystalloid"], "FD-BLD-07": rows[f"acute_{loss}"],
                  "FD-BLD-08": rows["stopped"], "FD-BLD-09": rows[f"acute_{loss}"]}
        verdicts[variant or "primary"] = {
            name: passes(name, case, source.get(name, rows["red_cells"]), variant,
                         rows[f"acute_off_{loss}"] if name == "FD-BLD-09" else None) for name in READINGS}
    return {"rows": rows, "verdicts": verdicts}


# Pre-freeze checks on off-grid probe points only ---------------------------------------------------------

#: Two probe points outside the explored grid in every parameter (the position inside both case bands).
PROBES = {
    "P1": {"bleed_ml_per_min": 3.0, "arrival_circulating_volume_ml": 4500.0, "preload_scale_over_kappa_ml": 1000.0,
           "preload_fraction": 0.4, "plasma_refill_target_share": 0.6, "plasma_refill_tau_min": 90.0,
           "plasma_refill_capacity_ml": 750.0, "red_cell_unit_hb_g_dl": 21.0, "red_cell_unit_volume_ml": 320.0,
           "crystalloid_effective_ml_per_ml": 0.25, "crystalloid_leak_tau_min": 45.0,
           "crystalloid_transient_share": 0.7, "reserve": 2.0},
    "P2": {"bleed_ml_per_min": 2.0, "arrival_circulating_volume_ml": 3500.0, "preload_scale_over_kappa_ml": 700.0,
           "preload_fraction": 0.48, "plasma_refill_target_share": 0.4, "plasma_refill_tau_min": 150.0,
           "plasma_refill_capacity_ml": 300.0, "red_cell_unit_hb_g_dl": 19.0, "red_cell_unit_volume_ml": 280.0,
           "crystalloid_effective_ml_per_ml": 0.15, "crystalloid_leak_tau_min": 20.0,
           "crystalloid_transient_share": 0.5, "reserve": 2.75},
}


def off_grid(point: dict) -> bool:
    """No value of the probe is one the region explores (positions compared as numbers in each case)."""
    for name, value in point.items():
        explored = REGION[name]
        if name == POS:
            explored = [getattr(gi_reference.case_bands(case)["preload_fraction"], label)
                        for case in CASES for label in ("lower", "midpoint", "upper")]
        if any(abs(value - other) < 1e-9 for other in explored):
            return False
    return True


def sensitivity() -> dict:
    """How much each reading the faculty did not fix moves the metric itself, on the off-grid probes: the
    minute, the mixing time, the challenge, early versus net effect, the clock of FD-BLD-05, the dilution's
    baseline, the 2 L infusion's speed and the size of the acute loss. Never a candidate of the region."""
    out = {}
    for label, point in PROBES.items():
        if not off_grid(point):
            raise AssertionError(f"{label} is not off the grid")
        for case in CASES:
            values = {**blood_anchors.REFERENCE, **point}
            item = {}
            anchors, profile, _, states, stop = _run(case, values, "untreated", 125)
            item["untreated_output"] = {m: (_output(states[m], anchors, profile) if m < len(states) else 0.0)
                                        for m in (25, 30, 35, 55, 60, 65, 115, 120, 125)}
            blood = _run(case, values, "untreated", 125, blood=True)[3]
            item["untreated_hb_fall"] = {m: blood[0].hb - blood[m].hb for m in (55, 60, 65, 115, 120, 125)}
            item["untreated_hb_max_rise"] = _max_rise(blood, 120)
            anchors, profile, _, states, _ = _run(case, values, "one_unit", 60)
            item["one_unit"] = {m: {"hb_gain": states[m].hb - states[0].hb,
                                    "output_gain": _output(states[m], anchors, profile) - 1.0,
                                    "position": preload_position(states[m], anchors, profile)} for m in (30, 45, 60)}
            first = states[0]
            item["challenge_gain"] = {int(ml): _output(first.evolve(V=first.V + profile.volume_preload_kappa * ml),
                                                       anchors, profile) - 1.0 for ml in (100.0, 250.0, 500.0)}
            item["normalized_points"] = {label: getattr(gi_reference.case_bands(case)["reference_preload_fraction"],
                                                        label) for label in ("lower", "midpoint", "upper")}
            row = crystalloid(case, values, 1000.0)
            item["crystalloid_1000"] = {"retained_early": row["retained_early"], "net_early": row["net_early"],
                                        "retained": row["retained"], "peak": row["peak"], "at_120": row["at_120"],
                                        "peak_from_arrival": row["peak_from_arrival"],
                                        "from_arrival_120": row["from_arrival_120"]}
            fast = crystalloid(case, values, 2000.0)
            anchors, _, _, slow_states, _ = _run(case, values, "crystalloid", 120, blood=True, volume_ml=2000.0,
                                                 duration_min=40.0)
            base = _run(case, values, "untreated", 120, blood=True)[3]
            item["crystalloid_2000"] = {"peak_20_min": fast["peak"],
                                        "peak_40_min": max(base[m].hb - slow_states[m].hb for m in range(121))}
            loss = {}
            for size in (ACUTE_LOSS_ML, 500.0):
                anchors, _, _, states, _ = _run(case, values, "acute_loss", 250, blood=True, loss_ml=size)
                loss[int(size)] = {m: states[m].blood.refill_ml / states[m].blood.shed_ml
                                   for m in (60, 70, 120, 130, 240, 250)}
            item["acute_loss"] = loss
            item["stopped"] = stopped(case, values)
            out[f"{label}|{case}"] = item
    return out


def dependencies() -> dict:
    """The blood reading's premise, on the off-grid probes: changing lambda / kappa, the position or rho moves
    no blood quantity of any surface (largest difference found)."""
    largest = 0.0
    for point in PROBES.values():
        for case in CASES:
            base = {**blood_anchors.REFERENCE, **point}
            for name, other in ((LK, 1200.0), (POS, 0.45), ("reserve", 1.5)):
                for scenario, extra in (("untreated", {}), ("crystalloid", {"volume_ml": 1000.0}),
                                        ("acute_loss", {"loss_ml": ACUTE_LOSS_ML}), ("stopped_bleed", {})):
                    one = _run(case, base, scenario, 120, **extra)[3]
                    two = _run(case, {**base, name: other}, scenario, 120, **extra)[3]
                    for a, b in zip(one, two):
                        largest = max(largest, abs(a.hb - b.hb), abs(a.blood.volume_ml - b.blood.volume_ml),
                                      abs(a.blood.refill_ml - b.blood.refill_ml))
    return {"largest_blood_difference": largest}


# The freeze -----------------------------------------------------------------------------------------------

#: Report-only modules the filter never reads; everything else under clinical_core is pinned.
FREEZE_EXCLUDED = ("clinical_core/blood_filter_report.py",)
ROOT = Path(__file__).resolve().parent.parent


def freeze_sources() -> dict[str, str]:
    out = {}
    for path in sorted((ROOT / "clinical_core").rglob("*.py")):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in FREEZE_EXCLUDED:
            out[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def _plain(value):
    return json.loads(json.dumps(value, sort_keys=True, default=str))


def freeze_digest() -> str:
    text = json.dumps({"decisions": _plain(DECISIONS), "implementation": IMPLEMENTATION, "variants": VARIANTS,
                       "status": FD_BLD_STATUS, "scope": APPROVAL_SCOPE, "sources": freeze_sources()},
                      sort_keys=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# The filter (P2I-2V-2 to 5) ---------------------------------------------------------------------------------

def minimal_conflicts(table: dict, region: dict, built: dict, size: int = CONFLICT_SIZE) -> list:
    """The minimal sets of filtering constraints (up to ``size``) with no joint survivor (primary reading)."""
    found = []
    for k in range(1, size + 1):
        for subset in itertools.combinations(CONSTRAINTS, k):
            if any(set(item["constraints"]) <= set(subset) for item in found):
                continue
            counted = count(table, region, None, subset, built=built)
            if counted["joint"] == 0:
                found.append({"constraints": list(subset), "alone": counted["alone"]})
    return found


def run_filter(region: dict = REGION, progress=None) -> dict:
    """P2I-2V-R: the primary reading uses one common bleed rate; FD-BLD-03 is reported, never filters; V5 is
    real; with an empty region, the minimal unsatisfied sets are searched. The grid is P2I-2U's."""
    table = tables(region, CASES, progress)
    sizes = {"common_bleed": region_size(region, common=True)["joint"],
             "case_specific": region_size(region)["joint"], "alone": region_size(region)["alone"]}
    built = {variant: masks(table, region, variant, READINGS)
             for variant in (None, *VARIANTS) if variant != CASE_SPECIFIC}
    primary = count(table, region, None, CONSTRAINTS, survivors=True, built=built[None])
    found = primary.pop("found")
    single = {name: count(table, region, None, (name,), built=built[None]) for name in CONSTRAINTS}
    without = {name: count(table, region, None, tuple(n for n in CONSTRAINTS if n != name), built=built[None])
               for name in CONSTRAINTS}
    variants = {variant: count(table, region, variant, CONSTRAINTS,
                               built=built[None] if variant == CASE_SPECIFIC else built[variant])
                for variant in VARIANTS}
    fd_bld_03 = {reading or "primary": count(table, region, reading, CONSTRAINTS + DIAGNOSTIC_ONLY,
                                             built=built[reading])
                 for reading in (None, "V2_fd03_both_midpoint", "V3_fd03_both_lower")}
    conflicts = minimal_conflicts(table, region, built[None]) if primary["joint"] == 0 else []
    primary["marginal"][f"{BLEED}|common"] = dict(primary["marginal"][f"{BLEED}|{CASES[0]}"])
    keys = {f"{POS}|{case}": POS for case in CASES}
    keys[f"{BLEED}|common"] = BLEED
    keys.update({n: n for n in SHARED})
    if primary["joint"]:
        basis, classes = "joint", classify(primary["marginal"], region, keys)
    else:
        basis = "each case alone (no joint survivor)"
        classes = {case: classify(primary["alone_marginal"][case], region, {n: n for n in PARAMETERS})
                   for case in CASES}
    representatives = {}
    if found:
        def key(item):
            combination, bit_a, bit_b = item
            values = [_candidate(combination, bit, region) for bit in (bit_a, bit_b)]
            outputs = [table[case]["untreated"][tuple(v[n] for n in TABLE_KEYS["untreated"])]["output"][120]
                       for case, v in zip(CASES, values)]
            return (*outputs, json.dumps(values, sort_keys=True, default=str))
        ordered = sorted(found, key=key)
        picks = {"low": ordered[0], "middle": ordered[len(ordered) // 2], "high": ordered[-1]}
        for label, (combination, bit_a, bit_b) in picks.items():
            values = {case: _candidate(combination, bit, region) for case, bit in zip(CASES, (bit_a, bit_b))}
            representatives[label] = {"values": values, "trajectories": {case: trajectories(case, values[case])
                                                                         for case in CASES}}
    else:
        representatives = _case_representatives(table, region)
    metrics = _metric_envelopes(table, region)
    return {"freeze_digest": freeze_digest(), "decided": DECIDED, "revision": "P2I-2V-R",
            "primary_reading": "one common GI-family candidate bleed rate for both cases",
            "region": {n: list(region[n]) for n in PARAMETERS}, "sizes": sizes, "primary": primary,
            "single": single, "without": without, "variants": variants, "fd_bld_03": fd_bld_03,
            "conflicts": conflicts, "identifiability": {"basis": basis, "classes": classes},
            "representatives": representatives, "metrics": metrics, "survivors_listed": len(found)}


def _case_representatives(table: dict, region: dict) -> dict:
    """With no joint survivor: each case's own survivors, rho at its reference, ordered by output at 120."""
    out = {}
    for case in CASES:
        single = {case: table[case]}
        built = masks(single, region, None)
        index = {n: i for i, n in enumerate(SHARED)}
        projections = [(tuple(index[n] for n in shared), lookup) for shared, lookup in built[case].values()]
        found = []
        for combination in itertools.product(*(region[n] for n in SHARED)):
            if combination[index["reserve"]] != blood_anchors.REFERENCE["reserve"]:
                continue
            mask = 0x1FF
            for positions, lookup in projections:
                mask &= lookup[tuple(combination[i] for i in positions)]
            for bit in range(9):
                if mask >> bit & 1:
                    values = _candidate(combination, bit, region)
                    output = table[case]["untreated"][tuple(values[n] for n in TABLE_KEYS["untreated"])]["output"][120]
                    found.append((output, json.dumps(values, sort_keys=True, default=str), values))
                    if len(found) > REPRESENTATIVE_LIMIT:
                        raise AssertionError("too many survivors to order: refused (frozen limit)")
        found.sort(key=lambda item: item[:2])
        if found:
            picks = {"low": found[0], "middle": found[len(found) // 2], "high": found[-1]}
            out[case] = {label: {"values": item[2], "trajectories": {case: trajectories(case, item[2])}}
                         for label, item in picks.items()}
        else:
            out[case] = {}
    return out


def _envelope(values: list) -> dict | None:
    values = sorted(v for v in values if v is not None)
    if not values:
        return None
    middle = len(values) // 2
    median = values[middle] if len(values) % 2 else (values[middle - 1] + values[middle]) / 2
    return {"min": values[0], "median": median, "max": values[-1], "n": len(values)}


def _metric_envelopes(table: dict, region: dict) -> dict:
    """What each constraint reads, over its whole table (context for the counts; nothing is fitted)."""
    out = {}
    for case in CASES:
        t = table[case]
        out[case] = {
            "untreated_output": {m: _envelope([r["output"][m] for r in t["untreated"].values()]) for m in MINUTES_OUTPUT},
            "untreated_stopped": sum(1 for r in t["untreated"].values() if r["stop"] is not None),
            "untreated_hb_fall": {m: _envelope([r["fall"][m] for r in t["untreated_blood"].values()]) for m in MINUTES_HB},
            "untreated_hb_max_rise": _envelope([r["max_rise"] for r in t["untreated_blood"].values()]),
            "crystalloid_net_early": _envelope([r[1000.0]["net_early"] for r in t["crystalloid"].values()]),
            "one_unit_hb_gain": _envelope([r["hb"][1] - r["hb"][0] for r in t["red_cells"].values()]),
            "one_unit_relative_output_gain": _envelope([r["output"][1] / r["output"][0] - 1 for r in t["red_cells"].values()]),
            "one_unit_position": _envelope([r["position"][1] for r in t["red_cells"].values()]),
            "second_over_first": _envelope([(r["output"][2] - r["output"][1]) / (r["output"][1] - r["output"][0])
                                            for r in t["red_cells"].values()]),
            "crystalloid_early": _envelope([r["early"] for r in t["retained"].values()]),
            "crystalloid_retained": {m: _envelope([r["share"][m] for r in t["retained"].values()]) for m in (30, 60, 120)},
            "crystalloid_peak_dilution": {int(v): _envelope([r[v]["peak"] for r in t["crystalloid"].values()])
                                          for v in CRYSTALLOID_VOLUMES},
            "refill_share": {m: _envelope([r["share"][m] for r in t["acute_200"].values()]) for m in REFILL_MINUTES},
            "refill_after_haemostasis_ml": _envelope([r["after_ml"] for r in t["stopped"].values()]),
        }
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--digest", action="store_true", help="print the freeze digest")
    parser.add_argument("--sensitivity", action="store_true", help="the pre-freeze checks on off-grid probes")
    parser.add_argument("--filter", action="store_true", help="run the frozen filter on the candidate region")
    parser.add_argument("--out", type=Path, help="directory for the JSON (outside the repository)")
    args = parser.parse_args(argv)
    if args.digest:
        print(freeze_digest())
        return 0
    if args.sensitivity:
        data = _plain({"freeze_digest": freeze_digest(), "sensitivity": sensitivity(), "dependencies": dependencies()})
        name = "blood_sensitivity.json"
    elif args.filter:
        data = _plain(run_filter(progress=lambda case, step: print(f"{case}: {step}", flush=True)))
        name = "blood_filter.json"
    else:
        parser.error("choose --digest, --sensitivity or --filter")
    text = json.dumps(data, indent=1, sort_keys=True, ensure_ascii=False)
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / name).write_text(text + "\n", encoding="utf-8")
        print(args.out / name)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
