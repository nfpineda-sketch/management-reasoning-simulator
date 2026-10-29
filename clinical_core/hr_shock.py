"""P2I-2AF: HR acute-shock drive and smooth sinus saturation (shadow only).

Faculty decisions (2026-10-29, P2I-2AF), recorded here:

1. The shock part of the arrival tachycardia must be generated from the current state and resolve when shock
   resolves. The constant arrival residual of P2I-2AE (S0 less the debt's share, solved from the authored HR) is
   removed: the acute signal is the effective oxygen deficit over the demand, with its own
   ``acute_deficit_to_sympathetic_gain``; the memory is debt_to_sympathetic_gain x D; tau_D only repays D. The arrival
   HR is the one the arrival physiology predicts; its mismatch with the authored HR is reported, never absorbed.
2. D's absolute scale is not approved: debt_to_sympathetic_gain is read with it (rescaling D by c and the gain by 1 / c
   leaves HR unchanged); the arrival-debt support is propagated uncertainty, not an anchor.
3. The sinus increment saturates smoothly: HR_RESERVE x tanh(unconstrained / HR_RESERVE), HR_RESERVE = sinus ceiling -
   the sinus base rate; no hard clip, no final reserve chosen.
4. The relative-pressure term stays, audited for double counting; no pressure calibration; RR, lactate and D are out of
   scope and must not move.

What this module does, frozen before any HR outcome: it audits the arrival residual (from the P2I-2AE record), audits
the new structure in the core's source, builds the candidate points of the two gains and of the ceiling from
dimensional consistency, the authored arrival HR, the intrinsic band, the current arrival support and a broad adult
maximal-sinus-rate range, reads the arrival HR mismatch analytically, and reads HR on the P2I-2AD representative
physiology (H1-H4, post-processed exactly from one core run each) and on synthetic probes (H5, H6). Nothing is fitted,
selected or approved; the legacy HR is read only after the verdict.
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
from . import hr_structure as hs
from . import lactate_closure as lc
from . import lactate_rebuild as lr
from . import lactate_slice
from .bands import Drift
from .derived import DEFAULT_PROFILE, derive, effective_delivery, effective_oxygen_deficit
from .integration import run as core_run
from .interventions.fluids import Crystalloid, PackedRedCells
from .modules.rhythm_events import ScriptedRhythmEvent
from .state import CoreInvariantError, RhythmCode, RhythmState

DECIDED = "2026-10-29"
REVISION = "P2I-2AF"
ROOT = lr.ROOT
CASES = lr.CASES
L1, L2, L3 = lr.L1, lr.L2, lr.L3
MINUTES, TIMES = lr.MINUTES, lr.TIMES
RESERVE = lr.RESERVE
LEVELS = hs.LEVELS
TAGS = ("LOW", "MID", "HIGH")
P2I2AE_RECORD = ROOT / "docs" / "revision" / "P2I2AE_hr_structure.json"
P2I2AE_DIGEST = "1b65d303831011014ca8cf8ce98e5fb880c5ea9cd3244f47773ce9d47b3712c8"

FACULTY = {
    "decided": DECIDED,
    "shock_recoverable": "the shock part of arrival tachycardia is generated from the current state and resolves when "
                         "shock resolves; no fixed case-specific offset; S0 is not forced to zero without replacing "
                         "its causal role",
    "acute_signal": "the effective oxygen deficit (over demand) is the acute shock signal; no absolute-pressure "
                    "reference; the relative-pressure term may stay if it does not double count (audited)",
    "d_scale": "D's absolute scale is not approved: debt_to_sympathetic_gain is read with it (D x c, gain / c leaves "
               "HR unchanged); the arrival-debt support is propagated uncertainty, never an anchor",
    "saturation": "a smooth monotone saturation of the sympathetic increment (no hard clip); no final reserve",
    "intrinsic": "60 / 80 / 100 stays STILL_VALID_CANDIDATE_RANGE; no value approved; cancellation is not equivalence",
    "scope": "shadow only; no pressure, RR or numeric HR calibration, no collapse, GI migration, second family or "
             "runtime integration; no hidden parameter approved",
}


# 1. The arrival residual (P2I-2AF-1), from the P2I-2AE record ---------------------------------------------------------

PHYSIOLOGIC_DYNAMIC, CASE_CALIBRATION_OFFSET = "PHYSIOLOGIC_DYNAMIC", "CASE_CALIBRATION_OFFSET"
LEGACY_ARTIFACT, STRUCTURAL_NECESSITY = "LEGACY_ARTIFACT", "STRUCTURAL_NECESSITY"
RESIDUAL_AUDIT = {
    "stored": "no state variable: derived.arrival_non_debt_drive (P2I-2AE) recomputed every minute from the anchors and "
              "added as a constant to sympathetic_target; before P2I-2AE, S0 itself inside the target",
    "calculation": "S0 = (authored arrival HR - intrinsic) / (25 (1 - beta)), less debt_to_sympathetic_gain x D0: "
                   "solved so that the arrival HR reproduces the authored one exactly (P2E-1, P2F-1, AC1)",
    "case_specific": True,
    "persists_indefinitely": True,
    "read_by": ["derived.sympathetic_target -> aux drive -> derive (sinus HR)", "derived.heart_rate_decomposition",
                "derived.arrival_layers (sympathetic_drive, sympathetic_bpm)", "decision_pack._record (sympathetic_bpm)",
                "hr_structure (P2I-2AE)"],
    "class": CASE_CALIBRATION_OFFSET,
    "why": "a per-case constant solved from the authored HR to force exact arrival matching; it has no dynamics, so the "
           "shock tachycardia it carried never resolved when the shock did",
}


def p2i2ae_record() -> dict:
    record = json.loads(P2I2AE_RECORD.read_text(encoding="utf-8"))
    if record["freeze_digest"] != P2I2AE_DIGEST:
        raise AssertionError("the P2I-2AE record is not the committed one")
    return record


def residual_amounts(record: dict) -> dict:
    """How much of the arrival sympathetic HR the residual held in P2I-2AE, per case over its consistent support."""
    out = {}
    for case in CASES:
        rows = [row for row in record["analytic"]["table"][case].values() if row["status"] != "ANALYTIC_REJECTION"]
        shares = [row["non_debt_bpm"] / row["sympathetic_bpm"] for row in rows if row["sympathetic_bpm"] > 0]
        reference = {f"{row['gain']!r}": {"residual_bpm": row["non_debt_bpm"], "of_bpm": row["sympathetic_bpm"]}
                     for row in rows if row["intrinsic"] == 80.0 and row["D0"] == 20.0}
        out[case] = {"residual_share_min": min(shares), "residual_share_max": max(shares),
                     "residual_bpm_min": min(row["non_debt_bpm"] for row in rows),
                     "residual_bpm_max": max(row["non_debt_bpm"] for row in rows),
                     "at_intrinsic_80_debt_20": reference, "rows": len(rows)}
    return out


# 2. The new structure, read from the core's source --------------------------------------------------------------------

def live_audit() -> dict:
    def body(function):
        return inspect.getsource(function).split('"""')[-1]
    target, update = body(derived.sympathetic_target), body(derived.sympathetic_after_minute)
    increment, rr = body(derived.sympathetic_increment), body(derived.respiratory_rate)
    sinus = inspect.getsource(derived.derive).split("RhythmCode.SINUS")[1].split("else:")[0]
    arrival = body(derived.arrival_state)
    reads = {"target_reads_acute_gain": "acute_deficit_to_sympathetic_gain" in target,
             "target_reads_effective_deficit": "effective_oxygen_deficit" in target,
             "target_reads_debt_gain": "debt_to_sympathetic_gain" in target,
             "target_reads_tau_d": "debt_clearance_tau_min" in target,
             "target_reads_lactate": "lactate" in target,
             "target_reads_authored_hr": "anchors.hr" in target or "arrival_sympathetic_drive" in target,
             "target_reads_residual": "arrival_non_debt_drive" in target,
             "arrival_solves_from_authored_hr": "anchors.hr" in arrival or "arrival_sympathetic_drive" in arrival,
             "update_reads_tau_d": "debt_clearance_tau_min" in update,
             "sinus_rate_saturates": "sympathetic_increment" in sinus,
             "saturation_is_tanh": "math.tanh" in increment,
             "saturation_hard_clip": any(word in increment for word in ("min(", "max(", "clamp")),
             "rr_reads_drive_or_rate": any(word in rr for word in ("sympathetic", "pulse_rate", "rate_bpm"))}
    no_residual = not (reads["target_reads_authored_hr"] or reads["target_reads_residual"]
                       or reads["arrival_solves_from_authored_hr"])
    return {"reads": reads, "no_residual": no_residual,
            "no_tau_d_in_hr": not (reads["target_reads_tau_d"] or reads["update_reads_tau_d"]),
            "acute_term": reads["target_reads_acute_gain"] and reads["target_reads_effective_deficit"],
            "smooth_saturation": reads["sinus_rate_saturates"] and reads["saturation_is_tanh"]
            and not reads["saturation_hard_clip"],
            "rr_independent_of_hr": not reads["rr_reads_drive_or_rate"]}


# 3. Candidate points, predeclared (P2I-2AF-2, -4, -5) -------------------------------------------------------------------

HR_RESOLUTION_BPM = hs.HR_RESOLUTION_BPM
POINT_COUNT = 5
SYNTHETIC_REFERENCE = 0.0
#: The broad adult maximal sinus rate (bpm): from about 150 (an older adult) to about 200 (a young adult), the span of
#: the age-predicted maximum over adult ages. General physiology, not repository truth; exploratory, not approved.
CEILINGS = (150.0, 175.0, 200.0)
CEILING_RULE = (
    "Three sinus-rate ceilings, 150 / 175 / 200 bpm: the broad adult maximal-sinus-rate range (about 150 for an older "
    "adult to about 200 for a young adult, the span of the age-predicted maximum over adult ages; general physiology, "
    "not repository truth) and its midpoint. HR_RESERVE = ceiling - sinus base rate. Checked before any run: every "
    "ceiling lies above every authored GI arrival HR and every intrinsic level (the authored arrival stays reachable), "
    "and at every (ceiling, intrinsic) the smallest authored arrival sympathetic share is read almost linearly "
    "(saturation takes off less than the authored HR resolution, 1 bpm). Never read: legacy HR, any trajectory.")


def analysis_anchors(case: str, intrinsic: str, debt: str, delivery: str):
    """A GI arrival as the representatives' runs build it: the case's band levels, arrival delivery re-anchored by the
    extraction reserve (2.5)."""
    values = calibration.case_values(case, calibration.GICandidate({}, intrinsic=intrinsic, debt=debt,
                                                                   delivery=delivery))
    values["arrival_delivery_ratio"] /= RESERVE
    return gi_reference.candidate_anchors(case, values)


def arrival_support() -> dict:
    """The current arrival support the gains are read against (propagated uncertainty, not approval): the acute signal
    at arrival, 1 - arrival delivery ratio (demand 1, re-anchored by the extraction reserve), and the arrival debt."""
    profile = replace(DEFAULT_PROFILE, oxygen_extraction_reserve=RESERVE)
    out = []
    for debt, delivery in lr.ARRIVAL_PAIRS:
        anchors = analysis_anchors(CASES[0], "midpoint", debt, delivery)
        state = derived.arrival_state(anchors, profile)
        out.append({"debt": debt, "delivery": delivery, "D0": anchors.arrival_oxygen_debt,
                    "x0": derived.acute_deficit_signal(state, anchors, profile)})
    return {"pairs": out, "x0": sorted({row["x0"] for row in out}), "D0": sorted({row["D0"] for row in out})}


def _shares() -> list[tuple]:
    return [(case, level, gi_reference.authored(case, "hr") - rate) for case in CASES
            for level, rate in hs.intrinsic_levels(case).items()]


def _gain_design(scale: str) -> dict:
    support = arrival_support()
    values = [v for v in support[scale] if v > 0.0]
    bpm = DEFAULT_PROFILE.hr_per_sympathetic_drive
    bounds = []
    for case, level, share in _shares():
        rate = hs.intrinsic_levels(case)[level]
        for ceiling in CEILINGS:
            reserve = ceiling - rate
            for value in values:
                bounds.append(reserve * math.atanh(share / reserve) / (bpm * value))
    high, low = max(bounds), HR_RESOLUTION_BPM / (bpm * max(values))
    ratio = (high / low) ** (1.0 / (POINT_COUNT - 1))
    points = tuple(low * ratio ** i for i in range(POINT_COUNT - 1)) + (high,)
    return {"scale": scale, "support": values, "low": low, "high": high, "ratio": ratio, "points": points,
            "synthetic_reference": SYNTHETIC_REFERENCE}


def acute_gain_design() -> dict:
    """The candidate points of acute_deficit_to_sympathetic_gain (drive per unit of deficit / demand), predeclared from
    dimensional consistency (drive = gain x signal, 25 bpm per unit, ADOPTED), the authored arrival HR, the intrinsic
    band, the ceilings and the current arrival support of the signal (0.15 and 0.4; 0 adds nothing):
    - highest: the gain at which the acute signal alone carries an authored arrival share through the saturation, the
      maximum over cases, intrinsic levels, ceilings and non-zero signals of HR_RESERVE atanh(share / HR_RESERVE) /
      (25 x signal);
    - lowest: the largest arrival signal moves HR by the authored resolution, 1 / (25 x max signal).
    Five log-spaced points, both ends included; 0 a synthetic reference. Never read: tau_D, lactate, legacy, any run."""
    return _gain_design("x0")


def debt_gain_design() -> dict:
    """The candidate points of debt_to_sympathetic_gain, by the same rule on the current arrival-debt support (20 and
    60). D's absolute scale is not approved: the support is propagated uncertainty, and the points mean nothing apart
    from it (D x c with gain / c is the same HR); they are reported with the HR increments they give."""
    return _gain_design("D0")


def ceiling_design() -> dict:
    authored = max(gi_reference.authored(case, "hr") for case in CASES)
    intrinsic = max(rate for case in CASES for rate in hs.intrinsic_levels(case).values())
    smallest = min(share for _, _, share in _shares() if share > 0)
    linear = {}
    for ceiling in CEILINGS:
        for case in CASES:
            for level, rate in hs.intrinsic_levels(case).items():
                reserve = ceiling - rate
                linear[f"{ceiling:g}|{case}|{level}"] = smallest - reserve * math.tanh(smallest / reserve)
    return {"ceilings": CEILINGS, "rule": CEILING_RULE, "above_authored_and_intrinsic": all(
        c > authored and c > intrinsic for c in CEILINGS), "smallest_share_bpm": smallest,
        "compression_at_smallest_share_bpm": linear,
        "near_linear": all(value < HR_RESOLUTION_BPM for value in linear.values())}


ACUTE = acute_gain_design()["points"]
DEBT = debt_gain_design()["points"]
ACUTE_SCAN, DEBT_SCAN = ACUTE + (SYNTHETIC_REFERENCE,), DEBT + (SYNTHETIC_REFERENCE,)
#: The anchor of the one-dimensional slices: each range's log-midpoint, the ceiling midpoint, intrinsic midpoint. A
#: reading point, not a selection.
ANCHOR = {"acute": ACUTE[2], "debt": DEBT[2], "ceiling": CEILINGS[1], "intrinsic": "midpoint"}


def analysis_profile(acute: float | None = None, debt: float | None = None, ceiling: float | None = None):
    return replace(DEFAULT_PROFILE, oxygen_extraction_reserve=RESERVE,
                   acute_deficit_to_sympathetic_gain=ANCHOR["acute"] if acute is None else acute,
                   debt_to_sympathetic_gain=ANCHOR["debt"] if debt is None else debt,
                   sinus_rate_ceiling_bpm=ANCHOR["ceiling"] if ceiling is None else ceiling)


# 4. The arrival HR mismatch, analytically (P2I-2AF-6) --------------------------------------------------------------------

ANALYTIC_REJECTION = "ANALYTIC_REJECTION"
MISMATCH_RULE = (
    "Arrival mismatch = predicted arrival HR (intrinsic + the saturated acute and debt increments the arrival physiology "
    "produces, derived.heart_rate_decomposition) - authored arrival HR, in bpm, signed. No tolerance exists, so none is "
    "applied: the distribution is reported, binned by |mismatch| at 1 / 5 / 10 / 20 bpm for presentation only (1 bpm is "
    "the authored resolution). ANALYTIC_REJECTION only for a domain violation (a sinus base rate at or above the "
    "ceiling); a mismatch is never a rejection here.")
BINS = (1.0, 5.0, 10.0, 20.0)


def _bin(value: float) -> str:
    for edge in BINS:
        if abs(value) <= edge:
            return f"<= {edge:g}"
    return f"> {BINS[-1]:g}"


def mismatch_surface() -> dict:
    table, rejections = {}, 0
    for case in CASES:
        rows = {}
        for level in LEVELS:
            for debt, delivery in lr.ARRIVAL_PAIRS:
                anchors = analysis_anchors(case, level, debt, delivery)
                for acute in ACUTE_SCAN:
                    for gain in DEBT_SCAN:
                        for ceiling in CEILINGS:
                            key = f"{level}|{debt}|{delivery}|{acute!r}|{gain!r}|{ceiling:g}"
                            try:
                                split = derived.heart_rate_decomposition(anchors, analysis_profile(acute, gain, ceiling))
                            except CoreInvariantError as error:
                                rows[key] = {"status": ANALYTIC_REJECTION, "reason": str(error)}
                                rejections += 1
                                continue
                            rows[key] = {"status": "READ", "intrinsic": split["intrinsic_sinus_rate"],
                                         "x0": split["acute_deficit_signal"], "D0": anchors.arrival_oxygen_debt,
                                         "acute_unconstrained_bpm": split["acute_unconstrained_bpm"],
                                         "debt_unconstrained_bpm": split["debt_unconstrained_bpm"],
                                         "acute_bpm": split["acute_bpm"], "debt_bpm": split["debt_bpm"],
                                         "pressure_and_other_unconstrained_bpm": split["unconstrained_bpm"]
                                         - split["acute_unconstrained_bpm"] - split["debt_unconstrained_bpm"],
                                         "saturated_bpm": split["saturated_bpm"],
                                         "predicted": split["predicted_arrival_hr"], "mismatch": split["mismatch_bpm"]}
        table[case] = rows
    summary = {}
    for case in CASES:
        values = sorted(row["mismatch"] for row in table[case].values() if row["status"] == "READ")
        bins = {}
        for value in values:
            bins[_bin(value)] = bins.get(_bin(value), 0) + 1
        quantile = lambda q: values[min(len(values) - 1, round(q * (len(values) - 1)))]  # noqa: E731
        summary[case] = {"n": len(values), "min": values[0], "q10": quantile(0.1), "median": quantile(0.5),
                         "q90": quantile(0.9), "max": values[-1], "bins": bins,
                         "within_resolution": sum(1 for v in values if abs(v) <= HR_RESOLUTION_BPM)}
    # The two cases share the gains and (in the source space) the arrival levels; the intrinsic rate may differ by case.
    joint, shared = None, None
    for key in table[CASES[0]]:
        level, rest = key.split("|", 1)
        if table[CASES[0]][key]["status"] != "READ":
            continue
        same = table[CASES[1]][key]
        if same["status"] == "READ":
            worst = max(abs(table[CASES[0]][key]["mismatch"]), abs(same["mismatch"]))
            shared = worst if shared is None else min(shared, worst)
        for other in LEVELS:
            pair = table[CASES[1]].get(f"{other}|{rest}")
            if pair and pair["status"] == "READ":
                worst = max(abs(table[CASES[0]][key]["mismatch"]), abs(pair["mismatch"]))
                joint = worst if joint is None else min(joint, worst)
    return {"rule": MISMATCH_RULE, "table": table, "summary": summary, "analytic_rejections": rejections,
            "best_joint_worst_mismatch_shared_intrinsic": shared, "best_joint_worst_mismatch_case_intrinsic": joint,
            "identical_prediction_for_both_cases": all(
                table[CASES[0]][k].get("predicted") == table[CASES[1]][k].get("predicted") for k in table[CASES[0]]
                if table[CASES[0]][k]["status"] == "READ")}


# 5. The representative physiology and the post-processed HR (H1-H4) -------------------------------------------------------

FACTORIZATION = (
    "HR reaches no output, delivery, D, lactate or RR. Each representative (tag, case, scenario) is simulated once by "
    "the full core; for any (intrinsic, acute gain, debt gain, ceiling) the drive is recomputed minute by minute from "
    "that run's acute signal (effective deficit over demand), pressure_rel, SpO2, glucose, D and rhythm with the core's "
    "own arithmetic, and HR = intrinsic + HR_RESERVE tanh(25 (1 - beta) drive / HR_RESERVE). Validated on full core "
    "reruns at the ends of every range (exact drive, HR, RR, D, lactate and haemodynamics), else the run stops.")


def full_run(inputs: dict, case: str, scenario: str, intrinsic: str = "midpoint", profile_changes: dict | None = None):
    """One full core run of a representative (P2I-2AD's physiology at reserve 2.5, demand 1.0)."""
    tau_d, gain_k, k, tau_l, excess, debt, delivery = inputs["point"]
    bag = inputs["bag"] if scenario == L2 else None
    values = {**lr.blood_values(inputs["entry"], case, bag), "reserve": RESERVE}
    _, profile, full = blood_anchors.setup(case, **values)
    case_values = calibration.case_values(case, calibration.GICandidate({}, excess=excess, debt=debt,
                                                                        delivery=delivery, intrinsic=intrinsic))
    case_values["preload_fraction"] = full[bc.POS]
    case_values["arrival_delivery_ratio"] /= RESERVE
    anchors = gi_reference.candidate_anchors(case, case_values)
    profile = replace(profile, debt_clearance_tau_min=tau_d, debt_per_delivery_deficit=gain_k, debt_to_lactate_gain=k,
                      lactate_clearance_tau_min=tau_l, **(profile_changes or {}))
    states, stop = blood_anchors.trajectory(anchors, lr.scenario_items(case, scenario, full), MINUTES, profile)
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
            "anchors": anchors, "profile": profile}


def hr_series(run_: dict, intrinsic_rate: float, acute: float, gain: float, ceiling: float) -> list[dict]:
    """The drive and HR of a run for another (intrinsic, acute gain, debt gain, ceiling), with the core's arithmetic."""
    anchors, profile, rows = run_["anchors"], run_["profile"], run_["rows"]
    beta = anchors.beta_blockade
    if not ceiling > intrinsic_rate:
        raise CoreInvariantError("the intrinsic rate is not below the sinus-rate ceiling")
    decay = math.exp(-1.0 / profile.sympathetic_decay_tau_min)
    out, drive = [], 0.0
    for minute, row in enumerate(rows):
        if not row["pulse"]:
            parts, target, drive = None, 0.0, 0.0
        else:
            demand = row["demand"]
            hypoxaemia = (max(0.0, profile.hypoxaemia_threshold_spo2 - row["spo2"])
                          - max(0.0, profile.hypoxaemia_threshold_spo2 - anchors.spo2))
            hypoglycaemia = (max(0.0, profile.hypoglycaemia_threshold_mg_dl - row["glucose"])
                             - max(0.0, profile.hypoglycaemia_threshold_mg_dl - anchors.glucose))
            parts = {"acute": acute * (row["deficit"] / demand),
                     "pressure": profile.sympathetic_per_pressure_deficit * (1.0 - row["pressure_rel"]),
                     "debt": gain * row["D"], "hypoxaemia": profile.sympathetic_per_hypoxaemia_point * hypoxaemia,
                     "hypoglycaemia": profile.sympathetic_per_hypoglycaemia_mg_dl * hypoglycaemia}
            target = max(0.0, (parts["acute"] + parts["pressure"] + parts["debt"] + parts["hypoxaemia"]
                               + parts["hypoglycaemia"]))
            if minute == 0:
                drive = target
            else:
                held = drive if rows[minute - 1]["pulse"] else target
                drive = target if target >= held else target + (held - target) * decay
        sinus = row["code"] == RhythmCode.SINUS.value
        if row["pulse"] and sinus:
            reserve = ceiling - intrinsic_rate
            unconstrained = profile.hr_per_sympathetic_drive * (1.0 - beta) * drive
            increment = reserve * math.tanh(unconstrained / reserve)
            hr = intrinsic_rate + increment
        else:
            unconstrained = increment = 0.0
            hr = row["rate_bpm"] if row["pulse"] else None
        out.append({"minute": minute, "drive": drive, "target": target, "hr": hr, "parts": parts,
                    "unconstrained": unconstrained, "increment": increment, "intrinsic": intrinsic_rate,
                    "response": profile.hr_per_sympathetic_drive * (1.0 - beta), "ceiling": ceiling})
    return out


def contributions(point: dict) -> dict:
    """One minute's HR in bpm: intrinsic, each stimulus's unconstrained increment, the floor and the decay lag, the
    unconstrained total, the saturated increment and its proportional attribution."""
    if point["parts"] is None:
        return {"hr": None}
    r, parts = point["response"], point["parts"]
    total = sum((parts["acute"], parts["pressure"], parts["debt"], parts["hypoxaemia"], parts["hypoglycaemia"]))
    share = point["increment"] / point["unconstrained"] if point["unconstrained"] > 0.0 else 0.0
    return {"intrinsic": point["intrinsic"], "acute_bpm": r * parts["acute"], "debt_bpm": r * parts["debt"],
            "pressure_bpm": r * parts["pressure"], "other_bpm": r * (parts["hypoxaemia"] + parts["hypoglycaemia"]),
            "floor_bpm": r * (max(0.0, total) - total), "lag_bpm": r * (point["drive"] - max(0.0, total)),
            "unconstrained_bpm": point["unconstrained"], "saturated_bpm": point["increment"],
            "acute_attributed_bpm": r * parts["acute"] * share, "debt_attributed_bpm": r * parts["debt"] * share,
            "hr": point["hr"]}


def validate(runs: dict, inputs: dict) -> dict:
    results = []
    variants = [("midpoint", {"acute_deficit_to_sympathetic_gain": a}) for a in (ACUTE[0], ACUTE[-1], 0.0)] + [
        ("midpoint", {"debt_to_sympathetic_gain": g}) for g in (DEBT[0], DEBT[-1])] + [
        ("midpoint", {"sinus_rate_ceiling_bpm": c}) for c in (CEILINGS[0], CEILINGS[-1])] + [
        (level, {}) for level in ("lower", "upper")]
    for (tag, case, scenario), base in runs.items():
        checks = []
        for level, changes in variants:
            profile = {**{"acute_deficit_to_sympathetic_gain": ANCHOR["acute"],
                          "debt_to_sympathetic_gain": ANCHOR["debt"], "sinus_rate_ceiling_bpm": ANCHOR["ceiling"]},
                       **changes}
            full = full_run(inputs[tag], case, scenario, level, profile)
            series = hr_series(base, hs.intrinsic_levels(case)[level], profile["acute_deficit_to_sympathetic_gain"],
                               profile["debt_to_sympathetic_gain"], profile["sinus_rate_ceiling_bpm"])
            rows = full["rows"]
            same = {"drive": [p["drive"] for p in series] == [r["drive"] for r in rows],
                    "hr": [p["hr"] for p in series] == [r["hr"] for r in rows],
                    "rr": [r["rr"] for r in rows] == [r["rr"] for r in base["rows"]],
                    "D": [r["D"] for r in rows] == [r["D"] for r in base["rows"]],
                    "lactate": [r["lactate"] for r in rows] == [r["lactate"] for r in base["rows"]],
                    "haemodynamics": [(r["pressure_rel"], r["output"], r["deficit"]) for r in rows]
                    == [(r["pressure_rel"], r["output"], r["deficit"]) for r in base["rows"]]}
            checks.append({"variant": f"{level}|{json.dumps(changes, sort_keys=True)}", "same": same,
                           "exact": all(same.values())})
        results.append({"tag": tag, "case": case, "scenario": scenario, "checks": checks,
                        "agree": all(c["exact"] for c in checks)})
    return {"rule": FACTORIZATION, "full_reruns": sum(len(r["checks"]) for r in results),
            "agree": all(r["agree"] for r in results), "disagreements": [r for r in results if not r["agree"]],
            "results": results}


# 6. The scan: one-dimensional slices and the acute x debt plane, post-processed --------------------------------------------

SCAN_RULE = (
    "On each of the 18 representative runs (3 tags x 2 cases x L1 / L2 / L3), post-processed, no further simulation: "
    "the one-dimensional slices through the anchor (acute gain over its five points and 0; debt gain likewise; ceiling "
    "150 / 175 / 200; intrinsic lower / midpoint / upper) and the acute x debt plane (6 x 6) at the anchor's ceiling and "
    "intrinsic. The anchor is a reading point, not a selection. No Cartesian product with blood, fluid or lactate.")


def scan_points() -> list[tuple]:
    points = {(ANCHOR["intrinsic"], a, g, ANCHOR["ceiling"]) for a in ACUTE_SCAN for g in DEBT_SCAN}
    points |= {(ANCHOR["intrinsic"], ANCHOR["acute"], ANCHOR["debt"], c) for c in CEILINGS}
    points |= {(level, ANCHOR["acute"], ANCHOR["debt"], ANCHOR["ceiling"]) for level in LEVELS}
    return sorted(points, key=lambda p: (LEVELS.index(p[0]), p[1], p[2], p[3]))


def _key(tag, case, scenario, point) -> str:
    level, acute, gain, ceiling = point
    return f"{tag}|{case}|{scenario}|{level}|{acute!r}|{gain!r}|{ceiling:g}"


def scan(runs: dict) -> dict:
    out = {}
    for (tag, case, scenario), run_ in runs.items():
        for point in scan_points():
            level, acute, gain, ceiling = point
            series = hr_series(run_, hs.intrinsic_levels(case)[level], acute, gain, ceiling)
            rows = run_["rows"]
            adequacy = run_["adequacy"]
            onset = adequacy["onset"] if adequacy else None
            out[_key(tag, case, scenario, point)] = {
                "tag": tag, "case": case, "scenario": scenario, "intrinsic": level, "acute": acute, "debt": gain,
                "ceiling": ceiling, "stop": run_["stop"], "controlled_at": run_["controlled_at"], "onset": onset,
                "series": series, "rows": rows}
    return out


def _hr_at(item: dict, minute: int):
    return item["series"][minute]["hr"] if minute < len(item["series"]) else None


def _point(item: dict, minute: int) -> dict:
    point, row = item["series"][minute], item["rows"][minute]
    return {**contributions(point), "D": row["D"], "effective_deficit": row["deficit"],
            "acute_signal": row["deficit"] / row["demand"], "output": row["output"],
            "bleed_ml_per_min": row["bleed_ml_per_min"], "prbc_units": row["prbc_units"],
            "crystalloid_in_ml": row["crystalloid_in_ml"],
            "haemostasis": item["controlled_at"] is not None and minute >= item["controlled_at"]}


FLAG_RULES = {
    "HR_BELOW_INTRINSIC": "a sinus HR below the intrinsic rate",
    "HR_ABOVE_CEILING": "a sinus HR above the ceiling (tanh reaches 1, and the HR the ceiling, only at floating-point "
                        "precision, beyond an unconstrained increment of about 19 reserves)",
    "NEGATIVE_INCREMENT": "a negative drive or sympathetic increment",
    "ACUTE_WITHOUT_DEFICIT": "an acute contribution while the effective deficit is 0",
    "DRIVE_FALLS_FASTER_THAN_ITS_DECAY": "the drive falls by more than its decay (exp(-1 / tau)) allows in one minute",
    "INSTANT_NORMALIZATION_AT_HAEMOSTASIS": "one minute after haemostasis the sinus HR is at the intrinsic rate while "
                                            "the drive before haemostasis was positive",
    "NO_DEBT_RECOVERY_AFTER_ADEQUACY": "with a positive debt gain, a T* and D(T*) > 0, the debt contribution at 120 is "
                                       "not below the one at T*",
    "ACUTE_PERSISTS_AFTER_ADEQUACY": "with a T*, an acute contribution remains at some minute from T* to 120",
}
FLAG_POLICY = ("Structural flags only, declared before any run; no bpm threshold (none is committed). Magnitudes and the "
               "arrival mismatch are reported on the decision surface for the faculty.")


def flags(item: dict) -> dict:
    series, rows = item["series"], item["rows"]
    decay = math.exp(-1.0 / DEFAULT_PROFILE.sympathetic_decay_tau_min)
    sinus = [(p, r) for p, r in zip(series, rows) if r["pulse"] and r["code"] == RhythmCode.SINUS.value]
    out = {"HR_BELOW_INTRINSIC": any(p["hr"] < p["intrinsic"] for p, _ in sinus),
           "HR_ABOVE_CEILING": any(p["hr"] > p["ceiling"] for p, _ in sinus),
           "NEGATIVE_INCREMENT": any(p["drive"] < 0.0 or p["increment"] < 0.0 for p in series),
           "ACUTE_WITHOUT_DEFICIT": any(p["parts"] is not None and r["deficit"] == 0.0 and p["parts"]["acute"] != 0.0
                                        for p, r in zip(series, rows)),
           "DRIVE_FALLS_FASTER_THAN_ITS_DECAY": any(b["drive"] < a["drive"] * decay - 1e-12
                                                    for a, b in zip(series, series[1:]) if b["parts"] is not None),
           "INSTANT_NORMALIZATION_AT_HAEMOSTASIS": False, "NO_DEBT_RECOVERY_AFTER_ADEQUACY": False,
           "ACUTE_PERSISTS_AFTER_ADEQUACY": False}
    controlled = item["controlled_at"]
    if controlled is not None and controlled + 1 < len(series):
        out["INSTANT_NORMALIZATION_AT_HAEMOSTASIS"] = (series[controlled]["drive"] > 0.0
                                                       and series[controlled + 1]["hr"] == item["series"][0]["intrinsic"])
    onset = item["onset"]
    if onset is not None and len(series) > MINUTES:
        if item["debt"] > 0.0 and rows[onset]["D"] > 0.0:
            out["NO_DEBT_RECOVERY_AFTER_ADEQUACY"] = not (series[MINUTES]["parts"]["debt"] < series[onset]["parts"]["debt"])
        out["ACUTE_PERSISTS_AFTER_ADEQUACY"] = any(series[m]["parts"]["acute"] != 0.0 for m in range(onset, MINUTES + 1))
    return out


# 7. Synthetic probes (H5) and the saturation probe (H6) ---------------------------------------------------------------------

INVARIANTS = {
    1: "a larger effective deficit, all else fixed, never lowers HR",
    2: "a larger D, all else fixed, never lowers HR",
    3: "tau_D at fixed D leaves HR unchanged",
    4: "the acute contribution resolves when the effective deficit resolves",
    5: "D may keep a delayed tachycardia after the acute deficit resolves",
    6: "as D repays, the debt-driven contribution may fall",
    7: "haemostasis alone does not instantly normalize HR",
    8: "the crystalloid effect arises through physiology, not fluid identity",
    9: "the PRBC effect arises through physiology, not a fixed HR decrement",
    10: "high sympathetic drive approaches saturation smoothly",
    11: "no discontinuous HR jump at saturation",
    12: "the intrinsic rhythm and the rhythm state remain authoritative",
}


def _hr_with(state, drive, anchors, profile):
    return derive(state.evolve(aux=replace(state.aux, sympathetic_drive=drive)), anchors, profile).pulse_rate_bpm


def synthetic_probes() -> dict:
    """H5: fixed-state probes on both GI arrivals at the anchor, straight on the core."""
    profile = analysis_profile()
    out = {}
    for case in CASES:
        anchors = analysis_anchors(case, "midpoint", "midpoint", "midpoint")
        arrival = derived.arrival_state(anchors, profile)
        probe = {}
        # 1. A larger effective deficit at the same pump, tone, volume and D: lower Hb lowers delivery only.
        hbs = (anchors.hb, anchors.hb - 0.5, anchors.hb - 1.0, anchors.hb - 2.0)
        targets = [derived.sympathetic_target(arrival.evolve(hb=h), anchors, profile) for h in hbs]
        signals = [derived.acute_deficit_signal(arrival.evolve(hb=h), anchors, profile) for h in hbs]
        rates = [_hr_with(arrival.evolve(hb=h), t, anchors, profile) for h, t in zip(hbs, targets)]
        probe["inv1_deficit"] = {"hb": list(hbs), "signal": signals, "targets": targets, "hr": rates,
                                 "holds": signals == sorted(signals) and targets == sorted(targets)
                                 and rates == sorted(rates) and targets[-1] > targets[0]}
        # 2. A larger D.
        debts = (0.0, 5.0, 20.0, 60.0, 240.0)
        targets = [derived.sympathetic_target(arrival.evolve(D=d), anchors, profile) for d in debts]
        rates = [_hr_with(arrival.evolve(D=d), t, anchors, profile) for d, t in zip(debts, targets)]
        probe["inv2_debt"] = {"D": list(debts), "targets": targets, "hr": rates,
                              "holds": targets == sorted(targets) and rates == sorted(rates)}
        # 3. tau_D at fixed D.
        taus = (7.5, 30.0, 60.0, 120.0, 480.0)
        readings = {(derived.sympathetic_target(arrival.evolve(D=d), anchors, replace(profile, debt_clearance_tau_min=t)),
                     derived.sympathetic_after_minute(arrival, arrival.evolve(D=d), anchors,
                                                      replace(profile, debt_clearance_tau_min=t)))
                    for t in taus for d in (40.0,)}
        probe["inv3_tau_d"] = {"tau_levels": list(taus), "distinct_readings": len(readings), "holds": len(readings) == 1}
        # 4. No deficit -> no acute contribution: delivery restored (Hb up) at no D.
        restored = arrival.evolve(hb=anchors.hb * 2.0, D=0.0)
        signal = derived.acute_deficit_signal(restored, anchors, profile)
        probe["inv4_resolves"] = {"signal": signal, "target": derived.sympathetic_target(restored, anchors, profile),
                                  "holds": signal == 0.0}
        # 12. Rhythm: a paced rhythm keeps its rate; PEA has no pulse rate and no drive.
        falling = (Drift("pump", "P", 0, 30, -0.01),)
        paced = core_run(anchors, falling + (ScriptedRhythmEvent("probe_paced", 10, RhythmState(
            RhythmCode.PACED, 70.0, 1.0, True), "probe"),), 20, profile)
        arrest = core_run(anchors, falling + (ScriptedRhythmEvent("probe_pea", 10, RhythmState.pea(40.0), "probe"),), 20,
                          profile)
        probe["inv12_rhythm"] = {"paced_rates": sorted({d.pulse_rate_bpm for d in paced.derived()[10:]}),
                                 "holds": {d.pulse_rate_bpm for d in paced.derived()[10:]} == {70.0}
                                 and all(d.pulse_rate_bpm is None for d in arrest.derived()[10:])
                                 and all(s.aux.sympathetic_drive == 0.0 for s in arrest.states[10:])}
        # 8 / 9. The same fluid or red cells on two physiologies (pump 1.0 and 0.7): the HR change follows the state.
        changes = {}
        for name, item in (("crystalloid", Crystalloid("probe_fluid", 0, 500.0, 10.0, 50.0, 1.0, 0.0, 60.0)),
                           ("red_cells", PackedRedCells("probe_prbc", 0, 1.0, 30.0, 1.0 / 30.0, 300.0, 20.0))):
            values = []
            for pump in (1.0, 0.7):
                start = (Drift("pump", "P", 0, 1, pump - 1.0),)
                alone = core_run(anchors, start, 30, profile).derived()[30].pulse_rate_bpm
                given = core_run(anchors, start + (item,), 30, profile).derived()[30].pulse_rate_bpm
                values.append(given - alone)
            changes[name] = values
        probe["inv8_9_through_physiology"] = changes
        out[case] = probe
    signature_free = all("intervention" not in inspect.signature(f).parameters
                         and "items" not in inspect.signature(f).parameters
                         for f in (derive, derived.sympathetic_target, derived.sympathetic_after_minute,
                                   derived.sympathetic_increment))
    crystalloid = [v for c in CASES for v in out[c]["inv8_9_through_physiology"]["crystalloid"]]
    red_cells = [v for c in CASES for v in out[c]["inv8_9_through_physiology"]["red_cells"]]
    out["inv8_crystalloid"] = {"changes": crystalloid, "holds": signature_free and len(set(crystalloid)) > 1}
    out["inv9_red_cells"] = {"changes": red_cells, "holds": signature_free and len(set(red_cells)) > 1}
    out["d_scale"] = d_scale_probe()
    out["authored_hr_reaches_no_dynamics"] = authored_hr_probe()
    out["non_sinus_and_beta"] = non_sinus_probe()
    return out


def d_scale_probe() -> dict:
    """D x c with debt_to_sympathetic_gain / c (and the deficit-to-D gain x c, the arrival debt x c) leaves HR unchanged on
    a synthetic untreated run whose D accrues."""
    anchors = analysis_anchors(CASES[0], "midpoint", "midpoint", "midpoint")
    rows = []
    for c in (0.37, 3.0):
        scaled = replace(anchors, arrival_oxygen_debt=c * anchors.arrival_oxygen_debt)
        base = core_run(anchors, (Drift("pump", "P", 0, 90, -0.005),), 90, analysis_profile())
        other = core_run(scaled, (Drift("pump", "P", 0, 90, -0.005),), 90, replace(
            analysis_profile(debt=ANCHOR["debt"] / c), debt_per_delivery_deficit=c * DEFAULT_PROFILE.debt_per_delivery_deficit))
        rows.append({"c": c, "max_gap_bpm": max(abs(a.pulse_rate_bpm - b.pulse_rate_bpm)
                                                for a, b in zip(base.derived(), other.derived()))})
    return {"rows": rows, "holds": all(row["max_gap_bpm"] <= 1e-9 for row in rows)}


def authored_hr_probe() -> dict:
    """The authored arrival HR reaches no dynamics: two arrivals identical but for their authored HR (and the sinus rate
    they show) run the same drive, and HR minus the arrival's own minute-0 base is the same. Before P2I-2AF the
    authored HR set the residual and so the whole drive."""
    anchors = analysis_anchors(CASES[0], "midpoint", "midpoint", "midpoint")
    other = replace(anchors, hr=anchors.hr - 10.0, rhythm=RhythmState.sinus(anchors.hr - 10.0))
    runs = [core_run(a, (Drift("pump", "P", 0, 60, -0.006),), 60, analysis_profile()) for a in (anchors, other)]
    drives = [[s.aux.sympathetic_drive for s in r.states] for r in runs]
    rates = [[d.pulse_rate_bpm for d in r.derived()] for r in runs]
    return {"same_drive": drives[0] == drives[1], "same_hr": rates[0] == rates[1],
            "holds": drives[0] == drives[1] and rates[0] == rates[1]}


def non_sinus_probe() -> dict:
    """TD-93(5): a paced arrival, or complete beta-blockade, with an arrival debt: refused in P2I-2AE (no residual to
    hold the debt's drive). Since P2I-2AF it runs; the rhythm keeps its rate, and beta 1 leaves the sinus rate intrinsic."""
    base = gi_reference.candidate_anchors(CASES[0], {})
    paced = replace(base, rhythm=RhythmState(RhythmCode.PACED, base.hr, 1.0, True), arrival_oxygen_debt=5.0,
                    declared={"arrival_oxygen_debt": "synthetic_probe"})
    blocked = replace(base, beta_blockade=1.0, arrival_oxygen_debt=5.0,
                      declared={"arrival_oxygen_debt": "synthetic_probe", "beta_blockade": "synthetic_probe"})
    out = {}
    for name, anchors in (("paced", paced), ("beta_1", blocked)):
        try:
            trajectory = core_run(anchors, (Drift("pump", "P", 0, 30, -0.005),), 30, analysis_profile())
            rates = sorted({d.pulse_rate_bpm for d in trajectory.derived()})
            out[name] = {"runs": True, "rates": rates if len(rates) <= 3 else [rates[0], rates[-1]],
                         "rate_constant": rates == [base.hr]}
        except CoreInvariantError as error:
            out[name] = {"runs": False, "error": str(error)}
    return {"cases": out, "classification": "GENERALIZATION_BLOCKER_ONLY",
            "status": "RESOLVED_BY_P2I2AF" if all(item["runs"] and item["rate_constant"] for item in out.values())
            else "OPEN", "affects_gi": False}


def saturation_probe() -> dict:
    """H6: the increment over a fine drive grid at every (ceiling, intrinsic) and a synthetic extreme-drive run. The
    grid reaches a drive of 20 (an unconstrained 500 bpm, ten reserves at the smallest), where tanh is still below 1."""
    grid = [i * 0.01 for i in range(0, 2001)]  # drive 0 to 20
    curves = {}
    for ceiling in CEILINGS:
        for level, rate in hs.intrinsic_levels(CASES[0]).items():
            profile = analysis_profile(ceiling=ceiling)
            values = [derived.sympathetic_increment(d, rate, 0.0, profile) for d in grid]
            steps = [b - a for a, b in zip(values, values[1:])]
            slope0 = values[1] / derived.unconstrained_increment(grid[1], 0.0, profile)
            curves[f"{ceiling:g}|{level}"] = {
                "reserve": ceiling - rate, "max_increment": values[-1], "below_reserve": values[-1] < ceiling - rate,
                "monotone": all(s >= 0.0 for s in steps),
                "lipschitz": all(s <= DEFAULT_PROFILE.hr_per_sympathetic_drive * 0.01 + 1e-12 for s in steps),
                "slope_at_zero": slope0, "at_drive_2": values[200], "linear_at_drive_2": 25.0 * 2.0}
    anchors = analysis_anchors(CASES[0], "lower", "upper", "lower")
    profile = analysis_profile(ACUTE[-1], DEBT[-1], CEILINGS[0])
    states, stop = blood_anchors.trajectory(anchors, (Drift("pump", "P", 0, 100, -0.007),), 100, profile)
    rates = [derive(state, anchors, profile).pulse_rate_bpm for state in states]
    jumps = [abs(b - a) for a, b in zip(rates, rates[1:])]
    return {"curves": curves, "extreme_run": {"ceiling": CEILINGS[0], "max_hr": max(rates), "hr_0_50_end": [
        rates[0], rates[min(50, len(rates) - 1)], rates[-1]], "minutes": len(rates) - 1, "stop": stop,
        "largest_minute_change": max(jumps), "below_ceiling": max(rates) < CEILINGS[0]},
        "holds": all(c["below_reserve"] and c["monotone"] and c["lipschitz"] and abs(c["slope_at_zero"] - 1.0) < 1e-3
                     for c in curves.values()) and max(rates) < CEILINGS[0]}


def run_invariants(scan_: dict, probes: dict, saturation: dict) -> dict:
    items = list(scan_.values())
    ok = lambda name: all(probes[c][name]["holds"] for c in CASES)  # noqa: E731
    flagged = {item_key: flags(item) for item_key, item in scan_.items()}
    l3 = [item for item in items if item["scenario"] == L3 and item["onset"] is not None and len(item["series"]) > MINUTES]
    delayed = [item for item in l3 if item["debt"] > 0.0 and item["rows"][item["onset"]]["D"] > 0.0]
    results = {
        1: ok("inv1_deficit"), 2: ok("inv2_debt"), 3: ok("inv3_tau_d"),
        4: ok("inv4_resolves") and bool(l3) and not any(f["ACUTE_PERSISTS_AFTER_ADEQUACY"] for f in flagged.values()),
        5: bool(delayed) and all(item["series"][item["onset"]]["parts"]["debt"] > 0.0 for item in delayed),
        6: bool(delayed) and not any(f["NO_DEBT_RECOVERY_AFTER_ADEQUACY"] for f in flagged.values()),
        7: bool(l3) and not any(f["INSTANT_NORMALIZATION_AT_HAEMOSTASIS"] for f in flagged.values())
        and not any(f["DRIVE_FALLS_FASTER_THAN_ITS_DECAY"] for f in flagged.values()),
        8: probes["inv8_crystalloid"]["holds"], 9: probes["inv9_red_cells"]["holds"],
        10: saturation["holds"] and not any(f["HR_ABOVE_CEILING"] for f in flagged.values()),
        11: all(c["lipschitz"] for c in saturation["curves"].values()),
        12: ok("inv12_rhythm") and not any(f["HR_BELOW_INTRINSIC"] for f in flagged.values()),
    }
    margins = [item["series"][item["controlled_at"] + 1]["hr"] - item["series"][0]["intrinsic"] for item in l3]
    counts = {name: sum(1 for f in flagged.values() if f[name]) for name in FLAG_RULES}
    return {"statements": INVARIANTS, "results": results, "all_pass": all(results.values()), "flags": counts,
            "l3_runs": len(l3), "delayed_runs": len(delayed),
            "min_margin_after_haemostasis_bpm": min(margins) if margins else None}


# 8. Decision surface, pressure audit, identifiability -------------------------------------------------------------------------

LANDMARKS = {"arrival": (L1, 0), "untreated_30": (L1, 30), "untreated_60": (L1, 60), "untreated_120": (L1, 120),
             "after_crystalloid_30": (L2, 30), "crystalloid_120": (L2, 120), "after_prbc_unit_1": (L3, 30),
             "after_prbc_unit_2_and_haemostasis": (L3, 60), "after_haemostasis_90": (L3, 90),
             "restored_adequacy_120": (L3, 120)}


def trajectories(scan_: dict) -> dict:
    """H1-H4 per case and tag at the anchor (the full slices are in the scan, summarized on the decision surface)."""
    anchor = (ANCHOR["intrinsic"], ANCHOR["acute"], ANCHOR["debt"], ANCHOR["ceiling"])
    out = {}
    for name, (scenario, minutes) in hs.H_SCENARIOS.items():
        out[name] = {"title": hs.H_TITLES[name], "scenario": scenario, "minutes": list(minutes), "cases": {
            case: {tag: {str(m): _point(scan_[_key(tag, case, scenario, anchor)], m) for m in minutes
                         if m < len(scan_[_key(tag, case, scenario, anchor)]["series"])} for tag in TAGS}
            for case in CASES}}
    return out


def decision_surface(scan_: dict) -> dict:
    """Per case, landmark and tag: HR across the acute x debt plane (anchor ceiling and intrinsic) and across the ceiling
    and intrinsic slices. Readings only, no envelope."""
    out = {}
    for case in CASES:
        out[case] = {}
        for name, (scenario, minute) in LANDMARKS.items():
            plane = {}
            for acute in ACUTE_SCAN:
                for gain in DEBT_SCAN:
                    point = (ANCHOR["intrinsic"], acute, gain, ANCHOR["ceiling"])
                    plane[f"{acute!r}|{gain!r}"] = {tag: _hr_at(scan_[_key(tag, case, scenario, point)], minute)
                                                    for tag in TAGS}
            ceilings = {f"{c:g}": {tag: _hr_at(scan_[_key(tag, case, scenario, (
                ANCHOR["intrinsic"], ANCHOR["acute"], ANCHOR["debt"], c))], minute) for tag in TAGS} for c in CEILINGS}
            intrinsic = {level: {tag: _hr_at(scan_[_key(tag, case, scenario, (
                level, ANCHOR["acute"], ANCHOR["debt"], ANCHOR["ceiling"]))], minute) for tag in TAGS}
                for level in LEVELS}
            out[case][name] = {"plane": plane, "ceiling": ceilings, "intrinsic": intrinsic}
    return {"landmarks": {k: list(v) for k, v in LANDMARKS.items()}, "table": out,
            "note": "no committed numeric HR band exists; nothing here is an envelope or a target"}


KEEP_FOR_NOW, REDUNDANT, NEEDS_PRESSURE_DOMAIN_REVIEW = "KEEP_FOR_NOW", "REDUNDANT", "NEEDS_PRESSURE_DOMAIN_REVIEW"


def pressure_audit(scan_: dict) -> dict:
    """P2I-2AF-9: what the relative-pressure term adds next to the acute deficit, at the anchor."""
    anchor = (ANCHOR["intrinsic"], ANCHOR["acute"], ANCHOR["debt"], ANCHOR["ceiling"])
    together = opposite = pressure_only = deficit_only = minutes = 0
    sums = []
    for tag in TAGS:
        for case in CASES:
            for scenario in (L1, L2, L3):
                item = scan_[_key(tag, case, scenario, anchor)]
                for point, row in zip(item["series"][1:], item["rows"][1:]):
                    if point["parts"] is None:
                        continue
                    minutes += 1
                    acute, pressure = point["parts"]["acute"], point["parts"]["pressure"]
                    together += acute > 0.0 and pressure > 0.0
                    opposite += acute > 0.0 and pressure < 0.0
                    pressure_only += acute == 0.0 and pressure > 0.0
                    deficit_only += acute > 0.0 and pressure <= 0.0
                    sums.append((acute, pressure))
    n = len(sums)
    mean_a, mean_p = sum(a for a, _ in sums) / n, sum(p for _, p in sums) / n
    cov = sum((a - mean_a) * (p - mean_p) for a, p in sums) / n
    sd_a = math.sqrt(sum((a - mean_a) ** 2 for a, _ in sums) / n)
    sd_p = math.sqrt(sum((p - mean_p) ** 2 for _, p in sums) / n)
    return {"minutes": minutes, "both_positive": together, "deficit_with_pressure_above_arrival": opposite,
            "pressure_without_deficit": pressure_only, "deficit_without_pressure_drive": deficit_only,
            "correlation": cov / (sd_a * sd_p) if sd_a and sd_p else None,
            "delta_from_arrival": True, "circular_dependency": False,
            "classification": NEEDS_PRESSURE_DOMAIN_REVIEW,
            "why": "the term is a deviation from arrival (0 at arrival, negative above arrival pressure) of output x tone, "
                   "and both it and the deficit fall with output, so in bleeding they rise together (partial double "
                   "counting of one shock); it also carries what the deficit does not (tone, and pressure falling while "
                   "extraction still compensates) and, above arrival pressure, unloads the drive while a deficit "
                   "persists. Neither reads the drive (no circularity). Whether it stays, becomes absolute or is "
                   "removed is a pressure-domain decision; it is neither removed nor recalibrated here."}


NON_IDENTIFIABLE = "NON_IDENTIFIABLE"


def identifiability(scan_: dict, surface: dict, probes: dict) -> dict:
    anchor_key = lambda tag, case, scenario, level: _key(tag, case, scenario, (  # noqa: E731
        level, ANCHOR["acute"], ANCHOR["debt"], ANCHOR["ceiling"]))
    shifts = []
    for tag in TAGS:
        for case in CASES:
            for scenario in (L1, L2, L3):
                mid = scan_[anchor_key(tag, case, scenario, "midpoint")]["series"]
                for level in ("lower", "upper"):
                    other = scan_[anchor_key(tag, case, scenario, level)]["series"]
                    gaps = [(a["hr"] - a["intrinsic"]) - (b["hr"] - b["intrinsic"]) for a, b in zip(mid, other)
                            if a["hr"] is not None and b["hr"] is not None]
                    shifts.append(max(abs(g) for g in gaps))
    composites = {
        "arrival_hr": "intrinsic + HR_RESERVE tanh(25 (acute gain x arrival signal + debt gain x D0) / HR_RESERVE), "
                      "HR_RESERVE = ceiling - intrinsic: one equation per case",
        "acute_increment_at_arrival": "25 x acute gain x arrival signal (bpm, unconstrained)",
        "debt_increment_at_arrival": "25 x debt gain x D0 (bpm, unconstrained; D scale latent)",
        "debt_over_time": "debt gain x D(t) = debt gain x D0 x D(t) / D0: only gain x scale is observable"}
    return {"composites": composites, "dimensions": {
        "intrinsic_sinus_rate": {"status": NON_IDENTIFIABLE, "support": "60 / 80 / 100 (STILL_VALID_CANDIDATE_RANGE)",
                                 "note": "no longer an exact shift: through HR_RESERVE it changes the saturated "
                                         "increment (largest change of HR - intrinsic between levels at the anchor "
                                         f"{max(shifts):.3g} bpm); not identifiable from the arrival HR alone"},
        "acute_deficit_to_sympathetic_gain": {"status": NON_IDENTIFIABLE, "support": f"[{ACUTE[0]:.3g}, {ACUTE[-1]:.3g}] "
                                              "and 0", "note": "shares the arrival equation with the debt gain; it "
                                              "resolves with the deficit and the debt persists, so post-arrival HR would "
                                              "separate them; none is authored"},
        "debt_to_sympathetic_gain": {"status": NON_IDENTIFIABLE, "support": f"[{DEBT[0]:.3g}, {DEBT[-1]:.3g}] and 0, on "
                                     "the current D support", "note": "only gain x D scale; D x c, gain / c gives the "
                                     "same HR", "probe": probes["d_scale"]},
        "sinus_rate_ceiling_bpm": {"status": NON_IDENTIFIABLE, "support": "150 / 175 / 200",
                                   "note": "visible only where the increment approaches the reserve (high drive); the "
                                           "authored arrival shares sit in the near-linear range"},
        "sympathetic_per_pressure_deficit": {"status": "NOT_EVALUATED_PRESSURE_DOMAIN", "support": "1.0 (PROVISIONAL)"},
        "d_scale": {"status": NON_IDENTIFIABLE, "support": "propagated (0 / 20 / 60), not approved"}},
        "intrinsic_shift_max_bpm": max(shifts)}


# 9. RR, legacy, verdict, next step, freeze --------------------------------------------------------------------------------------

def rr_audit(validation: dict, audit: dict, unchanged: dict) -> dict:
    same = all(c["same"]["rr"] and c["same"]["D"] and c["same"]["lactate"] for r in validation["results"]
               for c in r["checks"])
    return {"rr_reads_hr": not audit["rr_independent_of_hr"], "rr_d_lactate_equal_across_hr_parameters": same,
            "d_lactate_unchanged_from_p2i2ad": unchanged["equal"], "changes_rr": not (
                audit["rr_independent_of_hr"] and same and unchanged["equal"]), "calibrated": False}


LEGACY_RULE = hs.LEGACY_RULE


def legacy_reference(scan_: dict) -> dict:
    if lr.LegacyLock.held:
        raise AssertionError("the legacy HR is read only after the verdict")
    legacy = {}
    for case in CASES:
        legacy[case] = {}
        for scenario in (L1, L2, L3):
            snapshots = {item["minute"]: item for item in
                         calibration._legacy_run(case, lactate_slice.ORDERS[scenario]).snapshots}
            legacy[case][scenario] = {str(m): snapshots[m]["hr"] for m in TIMES if m in snapshots}
    anchor = (ANCHOR["intrinsic"], ANCHOR["acute"], ANCHOR["debt"], ANCHOR["ceiling"])
    beside = {f"{case}|{scenario}": {str(m): {"core_at_anchor": {tag: _hr_at(scan_[_key(tag, case, scenario, anchor)], m)
                                                                   for tag in TAGS},
                                              "legacy": legacy[case][scenario].get(str(m))} for m in TIMES}
        for case in CASES for scenario in (L1, L2, L3)}
    return {"rule": LEGACY_RULE, "legacy": legacy, "beside": beside}


READY = hs.READY
NOT_READY = hs.NOT_READY
VERDICT_RULE = (
    "HR_STRUCTURE_READY_FOR_NUMERIC_FACULTY_CALIBRATION when every check holds: (1) no arrival residual (the core's source "
    "and the probe in which the authored HR reaches no dynamics); (2) the acute contribution is explicit and recoverable "
    "(the source; 0 at no deficit; no acute contribution after sustained adequacy in any read L3 run); (3) tau_D does not "
    "reach HR at fixed D; (4) D x c with gain / c gives the same HR; (5) smooth saturation (tanh, no clip) and no sinus HR "
    "at or above the ceiling anywhere; (6) the twelve directions pass; (7) D, lactate and RR unchanged (P2I-2AD record "
    "and every validation rerun); (8) no structural flag; and the post-processing agrees with the full core. Otherwise "
    "HR_STRUCTURE_NOT_READY with the first blocker. The arrival mismatch is reported for the faculty, never a gate; no "
    "numeric parameter needs to be identified.")
NEXT_DESIGN = {
    "status": "PREPARED_NOT_EXECUTED",
    "observables": ["arrival HR mismatch (57m 124, 72f 112)", "untreated HR trajectory (30 / 60 / 120)",
                    "HR response to crystalloid (end of bolus, 120)", "HR response to each PRBC unit (30, 60)",
                    "HR after sustained adequacy (T*, 90, 120)", "residual delayed tachycardia (debt share at 120)"],
    "faculty_inputs": ["an arrival HR tolerance", "envelopes on the observable trajectories above, per case",
                       "whether the intrinsic rate may differ by case (the two authored arrivals differ by 12 bpm while "
                       "the gains are common)", "the sinus-ceiling range (150-200 proposed here, general physiology)",
                       "whether the relative-pressure term stays (pressure domain)"],
    "method": "filter the acute x debt x ceiling x intrinsic points (and their D support) against the faculty envelopes "
              "on observables, post-processed from the cached physiology; report survivors and composites, never one "
              "best set; latent gains are never approved directly",
}
POLICY = ("Shadow only. The P2I-2AD representatives (its committed record) and synthetic probes, never the P2F region. "
          "No arrival residual: the arrival HR is predicted and its mismatch reported. Candidate points predeclared; "
          "HR post-processed exactly (validated, else stop); no Cartesian product with blood, fluid or lactate; no "
          "pressure, RR or lactate change; the legacy HR read after the verdict only; nothing selected or approved.")


def verdict(audit: dict, probes: dict, saturation: dict, invariants: dict, validation: dict, rr: dict) -> dict:
    checks = [
        ("factorization", validation["agree"], "the post-processing does not agree with the full core"),
        ("no_residual", audit["no_residual"] and probes["authored_hr_reaches_no_dynamics"]["holds"],
         "an arrival residual still reaches the drive"),
        ("acute_recoverable", audit["acute_term"] and invariants["results"][4], "the acute contribution does not resolve"),
        ("no_tau_d_leak", audit["no_tau_d_in_hr"] and invariants["results"][3], "tau_D reaches HR at fixed D"),
        ("d_scale_invariance", probes["d_scale"]["holds"], "D scale and gain are not interchangeable"),
        ("smooth_saturation", audit["smooth_saturation"] and saturation["holds"] and invariants["results"][10],
         "saturation is missing, not smooth, or HR reaches the ceiling"),
        ("invariants", invariants["all_pass"], "a directional invariant fails"),
        ("d_lactate_rr_unchanged", not rr["changes_rr"], "D, lactate or RR changed"),
        ("patient_like", not any(invariants["flags"].values()), "a structural flag is raised"),
    ]
    blockers = [why for _, passed, why in checks if not passed]
    return {"verdict": READY if not blockers else f"{NOT_READY} — {blockers[0]}",
            "checks": {name: passed for name, passed, _ in checks}, "blockers": blockers, "rule": VERDICT_RULE,
            "next_design": NEXT_DESIGN if not blockers else None}


def design() -> dict:
    return {"faculty": FACULTY, "residual_audit": RESIDUAL_AUDIT,
            "acute": {**acute_gain_design(), "rule": acute_gain_design.__doc__},
            "debt": {**debt_gain_design(), "rule": debt_gain_design.__doc__},
            "ceiling": ceiling_design(), "anchor": ANCHOR, "mismatch": MISMATCH_RULE, "bins": list(BINS),
            "scenarios": {k: [v[0], list(v[1])] for k, v in hs.H_SCENARIOS.items()}, "factorization": FACTORIZATION,
            "scan": SCAN_RULE, "scan_points": scan_points(), "flags": FLAG_RULES, "flag_policy": FLAG_POLICY,
            "invariants": INVARIANTS, "landmarks": {k: list(v) for k, v in LANDMARKS.items()}, "legacy": LEGACY_RULE,
            "verdict": VERDICT_RULE, "next_design": NEXT_DESIGN, "policy": POLICY}


def freeze_digest() -> str:
    records = {name: hashlib.sha256(path.read_bytes()).hexdigest()
               for name, path in (("P2I-2AD", hs.P2I2AD_RECORD), ("P2I-2AE", P2I2AE_RECORD))}
    text = json.dumps({"revision": REVISION, "records": records, "design": design(), "sources": bf.freeze_sources()},
                      sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run(progress=None) -> dict:
    say = progress or (lambda *_: None)
    with lr.P2FGuard(), lr.LegacyLock():
        ad, ae = hs.p2i2ad_record(), p2i2ae_record()
        audit = live_audit()
        say("arrival")
        surface_arrival = mismatch_surface()
        say("probes")
        probes, saturation = synthetic_probes(), saturation_probe()
        say("representatives")
        inputs = hs.representative_inputs(ad)
        runs = {(tag, case, scenario): full_run(inputs[tag], case, scenario)
                for tag in TAGS for case in CASES for scenario in (L1, L2, L3)}
        say("validation")
        validation = validate(runs, inputs)
        unchanged = hs.unchanged_physiology(runs, ad)
        out = {"freeze_digest": freeze_digest(), "decided": DECIDED, "revision": REVISION, "policy": POLICY,
               "faculty": FACULTY, "records": {"P2I-2AD": hs.P2I2AD_DIGEST, "P2I-2AE": P2I2AE_DIGEST},
               "residual": {**RESIDUAL_AUDIT, "amounts": residual_amounts(ae)}, "audit": audit,
               "design": {"acute": acute_gain_design(), "debt": debt_gain_design(), "ceiling": ceiling_design(),
                          "anchor": ANCHOR, "support": arrival_support()},
               "arrival": surface_arrival, "probes": probes, "saturation": saturation,
               "validation": {k: v for k, v in validation.items() if k != "results"}, "unchanged_physiology": unchanged}
        if not validation["agree"]:
            out["verdict"] = {"verdict": f"{NOT_READY} — the post-processing does not agree with the full core"}
            return out
        say("scan")
        scanned = scan(runs)
        invariants = run_invariants(scanned, probes, saturation)
        rr = rr_audit(validation, audit, unchanged)
        surface = decision_surface(scanned)
        out.update({"scan_rule": SCAN_RULE, "trajectories": trajectories(scanned), "decision_surface": surface,
                    "invariants": invariants, "pressure": pressure_audit(scanned),
                    "identifiability": identifiability(scanned, surface, probes), "rr": rr,
                    "verdict": verdict(audit, probes, saturation, invariants, validation, rr)})
    out["legacy_reference"] = legacy_reference(scanned)
    out["efficiency"] = {"representative_runs": len(runs), "validation_full_reruns": validation["full_reruns"],
                         "post_processed_series": len(scanned), "arrival_decompositions_analytic": sum(
                             len(t) for t in surface_arrival["table"].values()),
                         "analytic_rejections": surface_arrival["analytic_rejections"],
                         "simulations_avoided": len(scanned) - len(runs) - validation["full_reruns"],
                         "cartesian_sweep": False}
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
        (out / "hr_shock.json").write_text(json.dumps(result, indent=1, sort_keys=True, default=str), encoding="utf-8")
        print(out / "hr_shock.json")
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
