"""P2I-2AE: HR / sympathetic-response structural calibration for the GI cases (shadow only).

Faculty decisions (2026-10-29, P2I-2AE), recorded here:

1. tau_D is the oxygen-debt repayment time constant only. It no longer defines the sympathetic drive: the debt-driven
   drive is ``debt_to_sympathetic_gain`` x D (``derived.sympathetic_target``), 0 at D = 0, never decreasing in D, and the
   gain is never derived from tau_D (TD-92).
2. Arrival HR = intrinsic rate + a non-negative sympathetic contribution. The arrival drive splits into the arrival
   debt's share (gain x D0) and the rest (``derived.arrival_non_debt_drive``), both non-negative: an arrival whose debt
   alone would call for more drive than the observed HR carries is inconsistent and the core stops it. No GI-specific HR
   decrement; the legacy HR is not a target; the historical P2F HR1 rejection is not evidence.
3. Lactate stays closed (P2I-2AD): no lactate constraint, range or gain changes here.

What this module does, frozen before any HR outcome: it audits the HR derivation (contributors, every path by which
tau_D reached HR), states the authored HR anchors, audits the intrinsic band, builds the candidate range of the new gain
from dimensional consistency, the authored arrival HR, the intrinsic band, the arrival-debt scale and the non-negative
rule, rejects inconsistent arrival decompositions analytically, and reads HR on the P2I-2AD representative physiology
(H1-H4) and on synthetic fixed-state probes (H5). HR does not feed back into output, delivery, D or lactate, so each
representative run is simulated once and HR is post-processed for every (intrinsic, gain) pair, validated against full
core runs (else the run stops). Nothing is fitted, selected or approved; no SBP, MAP or RR is calibrated; collapse stays
off; the legacy HR is read only after the verdict.
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
from . import lactate_adequacy as la
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
REVISION = "P2I-2AE"
ROOT = lr.ROOT
CASES = lr.CASES
L1, L2, L3 = lr.L1, lr.L2, lr.L3
MINUTES, TIMES = lr.MINUTES, lr.TIMES
RESERVE = lr.RESERVE
LEVELS = ("lower", "midpoint", "upper")
P2I2AD_RECORD = ROOT / "docs" / "revision" / "P2I2AD_lactate_closure.json"
P2I2AD_DIGEST = "5cb48163da4ff081e752b7684f4b036dbcf3e2acb4f94ee1603aaec742fe7fcf"

FACULTY = {
    "decided": DECIDED,
    "td_92": "tau_D = oxygen-debt repayment only; it must not define the sympathetic drive. D -> drive through an "
             "independent debt_to_sympathetic_gain, never derived from tau_D.",
    "arrival": "arrival HR = intrinsic rhythm component + non-negative sympathetic contribution; no GI-specific HR "
               "decrement; legacy HR is not a target; the historical P2F HR1 rejection is not calibration evidence.",
    "lactate": "LACTATE_PHYSIOLOGY_READY_FOR_HR_DOMAIN accepted: lactate constraints, ranges and gains unchanged; the "
               "open upper edge of debt_to_lactate_gain is propagated uncertainty.",
    "scope": "shadow only; no pressure / vascular-tone, RR or numeric HR calibration; no collapse, GI migration, second "
             "family or runtime integration; no hidden parameter selected or approved.",
}


# 1. Audit of the HR derivation (P2I-2AE-1, P2I-2AE-3) -----------------------------------------------------------------

#: The HR derivation at e0dffa8, before this package changed it.
OLD_EQUATION = (
    "sinus: HR = R.rate_bpm + hr_per_sympathetic_drive (25) x (1 - beta_blockade) x drive; non-sinus: HR = R.rate_bpm; "
    "no pulse: no pulse rate, drive 0. drive: rises at once to the target, decays toward it with exp(-1 / 5 min). "
    "target = max(0, S0 + 1.0 x (1 - pressure_rel) + 0.5 x (D - D0) / tau_D + 0.02 x delta hypoxaemia(SpO2 < 94) + "
    "0.01 x delta hypoglycaemia(glucose < 70)), S0 = (HR_arrival - intrinsic) / (25 x (1 - beta)), intrinsic = the "
    "declared rate or the arrival HR, pressure_rel = output x tone relative to arrival.")
NEW_EQUATION = (
    "sinus: HR = R.rate_bpm + 25 x (1 - beta_blockade) x drive (unchanged); drive dynamics unchanged. target = max(0, "
    "S_rest + 1.0 x (1 - pressure_rel) + debt_to_sympathetic_gain x D + 0.02 x delta hypoxaemia + 0.01 x delta "
    "hypoglycaemia), S_rest = S0 - debt_to_sympathetic_gain x D0 >= 0 (else the arrival is inconsistent and the core "
    "stops). At arrival the target is S0, so the arrival HR is reproduced exactly; tau_D appears nowhere.")
CONTRIBUTORS = {
    "intrinsic_rate": "R.rate_bpm = intrinsic_sinus_rate (case parameter; undeclared: the arrival HR, no sympathetic "
                      "share). The sinus floor: the drive is never negative.",
    "sympathetic": "aux.sympathetic_drive x hr_per_sympathetic_drive (25 bpm per unit, ADOPTED) x (1 - beta_blockade).",
    "debt": "debt_to_sympathetic_gain x D (P2I-2AE; was sympathetic_per_debt x (D - D0) / tau_D).",
    "direct_deficit": "none: no term reads the instantaneous effective oxygen deficit or delivery.",
    "acute_haemodynamic": "sympathetic_per_pressure_deficit (1.0, PROVISIONAL) x (1 - pressure_rel), arrival-relative "
                          "(the baroreflex stimulus; already separate from D).",
    "other_stimuli": "hypoxaemia (0.02 per SpO2 point below 94) and hypoglycaemia (0.01 per mg/dL below 70), "
                     "arrival-relative.",
    "arrival_rest": "S_rest: the arrival drive the arrival debt does not explain (the arrival pressure deficit and "
                    "anything unmodelled), constant; only the arrival-relative stimuli move the drive below it.",
    "drugs_interventions": "none acts on HR directly: fluids, red cells, haemostasis and oxygen act through V, Hb, the "
                           "bleed flow and SpO2; beta_blockade is a constant case parameter (0: none authored).",
    "rhythm": "authoritative: a non-sinus perfusing rhythm keeps its own rate; no pulse, no pulse rate; scripted rhythm "
              "events and the collapse rule (off) change R.",
    "caps_floors": "floor: drive >= 0 (sinus HR >= intrinsic). No upper cap or saturation in the core (the family "
                   "engine clamps its display to [42, 180]: LEGACY_REFERENCE only).",
    "case_specific": "none: the GI module writes no HR or drive; no GI-specific decrement.",
}
VALID_CAUSAL_PATH, SEMANTIC_LEAK = "VALID_CAUSAL_PATH", "SEMANTIC_LEAK"
LEGACY_ARTIFACT, CASE_SPECIFIC_ARTIFACT = "LEGACY_ARTIFACT", "CASE_SPECIFIC_ARTIFACT"
TAU_D_PATHS = (
    {"path": "derived.sympathetic_target: sympathetic_per_debt x (D - D0) / tau_D", "class": SEMANTIC_LEAK,
     "status": "removed (P2I-2AE)",
     "why": "at fixed D and lactate, tau_D rescaled the debt term. Before P2I-2AC, D settled at deficit x tau_D, so D / "
            "tau_D read as a lagged deficit; since P2I-2AC D does not repay under a deficit and the division only "
            "rescaled the debt's drive by the repayment time."},
    {"path": "tau_D -> repayment of D across oxygen-adequate minutes -> debt_to_sympathetic_gain x D -> HR",
     "class": VALID_CAUSAL_PATH, "status": "kept",
     "why": "tau_D sets how fast D repays; the drive reads D itself."},
    {"path": "calibration.REGISTRY sympathetic_per_debt 0.25 / 0.5 / 1.0 'drive per unit D / tau_D'",
     "class": LEGACY_ARTIFACT, "status": "kept for history; the core no longer reads it",
     "why": "its units carry tau_D: one point meant three different gains across the tau_D grid."},
    {"path": "decision_pack.p2f_rejection: tau_D 30 x arrival debt upper rejected by HR1 (gi_bleed_72f)",
     "class": LEGACY_ARTIFACT, "status": "written history; no longer reproduced by the current core",
     "why": "a case-specific historical outcome of the leak (the drive fell as D repaid at 1 / 30 per minute during a "
            "synthetic volume loss); the faculty does not read it as evidence."},
    {"path": "calibration.check_hr HR1-HR4 over the tau_D levels; decision_pack HR effect tables over "
             "sympathetic_per_debt", "class": LEGACY_ARTIFACT, "status": "historical harness and tables",
     "why": "probes and tables built on the leak; not current evidence."},
    {"path": "gi_reference.arrival_debt_band rationale ('60 is the steady state ... at 60 min')",
     "class": LEGACY_ARTIFACT, "status": "values unchanged (lactate closed)",
     "why": "a pre-P2I-2AC steady-state reading; reaches HR only through D0 in the arrival decomposition."},
)
DEFICIT_AUDIT = {
    "A_instantaneous_effective_oxygen_deficit": False, "B_accumulated_D": True, "C_both": False,
    "acute_term_present": "the pressure deficit (1 - pressure_rel), arrival-relative: an acute haemodynamic stimulus, "
                          "separate from D before and after this package",
    "new_acute_term_needed": False,
    "why": "the faculty expectation (acute response to current shock, persistent drive with debt memory) is met "
           "structurally by the existing acute pressure term plus gain x D; an anaemia or hypoxaemic under-delivery "
           "at preserved pressure reaches the drive only through D (and SpO2 through hypoxaemia). Whether an "
           "oxygen-delivery term should be added is a faculty question, not a semantic error, so none is invented.",
}


def live_audit() -> dict:
    """What the current core reads, from its source: the drive's target, its update, the sinus rate and RR."""
    def body(function):
        return inspect.getsource(function).split('"""')[-1]
    target, update = body(derived.sympathetic_target), body(derived.sympathetic_after_minute)
    rest, rr = body(derived.arrival_non_debt_drive), body(derived.respiratory_rate)
    sinus = inspect.getsource(derived.derive).split("RhythmCode.SINUS")[1].split("else:")[0]
    reads = {"target_reads_debt_to_sympathetic_gain": "debt_to_sympathetic_gain" in target,
             "target_reads_tau_d": "debt_clearance_tau_min" in target,
             "target_reads_sympathetic_per_debt": "sympathetic_per_debt" in target,
             "update_reads_tau_d": "debt_clearance_tau_min" in update,
             "arrival_rest_reads_tau_d": "debt_clearance_tau_min" in rest,
             "target_reads_effective_deficit": "deficit" in target.replace("pressure_deficit", ""),
             "sinus_rate_reads_drive": "sympathetic_drive" in sinus and "hr_per_sympathetic_drive" in sinus,
             "rr_reads_drive_or_rate": any(word in rr for word in ("sympathetic", "pulse_rate", "rate_bpm"))}
    no_leak = (reads["target_reads_debt_to_sympathetic_gain"] and not reads["target_reads_tau_d"]
               and not reads["target_reads_sympathetic_per_debt"] and not reads["update_reads_tau_d"]
               and not reads["arrival_rest_reads_tau_d"])
    return {"reads": reads, "no_tau_d_in_hr": no_leak, "rr_independent_of_hr": not reads["rr_reads_drive_or_rate"],
            "acute_oxygen_deficit_term": reads["target_reads_effective_deficit"]}


# 2. Repository-truth HR anchors and the intrinsic band (P2I-2AE-4, P2I-2AE-7) -------------------------------------------

AUTHORED_OBSERVATION, MODEL_DERIVED, LEGACY_REFERENCE = "AUTHORED_OBSERVATION", "MODEL_DERIVED", "LEGACY_REFERENCE"
STILL_VALID, NEEDS_REJUSTIFICATION, SEMANTICALLY_INVALID = (
    "STILL_VALID_CANDIDATE_RANGE", "NEEDS_REJUSTIFICATION", "SEMANTICALLY_INVALID")


def anchors_table() -> dict:
    """Only what the repository authors; later HR is not authored and is never invented."""
    out = {}
    for case in CASES:
        rows = {entry.item: entry for entry in gi_reference.INVENTORY if entry.case == case}
        out[case] = {
            "arrival_hr": {"value": rows["hr"].value, "label": AUTHORED_OBSERVATION, "source": rows["hr"].source},
            "rhythm": {"value": rows["rhythm"].value, "label": AUTHORED_OBSERVATION, "source": rows["rhythm"].source,
                       "note": rows["rhythm"].note},
            "medications": {"value": rows["medications"].value, "label": AUTHORED_OBSERVATION,
                            "note": "no beta-blocker or rate control authored: beta_blockade stays 0"},
            "later_hr": {"value": "not authored", "label": AUTHORED_OBSERVATION,
                         "note": "no HR after arrival is stated by the case"},
            "core_hr_after_arrival": {"label": MODEL_DERIVED, "note": "this package's trajectories; not observations"},
            "family_engine_hr": {"label": LEGACY_REFERENCE, "note": "read only after the verdict (legacy_reference)"}}
    return out


def intrinsic_audit() -> dict:
    """The intrinsic band's provenance and role under the current physiology."""
    source = inspect.getsource(gi_reference.intrinsic_hr_band)
    from_hr1 = any(word in source for word in ("HR1", "check_hr", "debt", "tau", "sympathetic_per"))
    bands = {case: [gi_reference.intrinsic_hr_band(case).lower, gi_reference.intrinsic_hr_band(case).midpoint,
                    gi_reference.intrinsic_hr_band(case).upper] for case in CASES}
    return {"band": bands, "resting_hr": list(gi_reference.RESTING_HR), "derived_from_hr1": from_hr1,
            "status": SEMANTICALLY_INVALID if from_hr1 else STILL_VALID,
            "why": "gi_reference.RESTING_HR is the resting adult sinus range (60 / 80 / 100), capped at the authored "
                   "arrival HR; its rule reads no HR1 probe, no D, no tau_D and no gain. Under the current physiology "
                   "it keeps one role: the sinus floor R.rate_bpm the drive falls back to (the arrival share is the "
                   "authored HR less it). P2I-2AE adds only a joint constraint, intrinsic + 25 x gain x D0 <= arrival "
                   "HR (non-negative S_rest), applied as an analytic rejection, never by moving the band."}


# 3. The candidate range of debt_to_sympathetic_gain (P2I-2AE-6) --------------------------------------------------------

#: The resolution at which the authored arrival HR are stated (integers, bpm).
HR_RESOLUTION_BPM = 1.0
GAIN_POINT_COUNT = 5
#: No debt-driven drive at all: a synthetic reference, never counted.
GAIN_SYNTHETIC_REFERENCE = 0.0
OLD_RANGE_STATUS = "OLD_SYMPATHETIC_PER_DEBT_RANGE_SEMANTICALLY_INVALID"
OLD_RANGE_REASON = ("sympathetic_per_debt (0.25 / 0.5 / 1.0) was a drive per unit of D / tau_D: one point meant a "
                    "different gain at each tau_D, so the range carries tau_D in its units and cannot be translated "
                    "into an independent gain. The gains it induced are reported for comparison only.")


def gain_design() -> dict:
    """The candidate range of debt_to_sympathetic_gain (drive units per unit of D), frozen before any HR outcome, from
    dimensional consistency (debt-driven drive = gain x D; 25 bpm per unit of drive, ADOPTED; D in the index-minutes
    of the arrival-debt band, unchanged since P2F), the authored arrival HR, the intrinsic band and the non-negative
    rule only:
    - highest gain: the largest gain any declared arrival can hold with a non-negative rest of the arrival drive, the
      maximum over cases, intrinsic levels and non-zero arrival-debt levels of (HR - intrinsic) / (25 x D0);
    - lowest gain: the largest declared arrival debt moves the arrival HR by the authored HR resolution (1 bpm),
      1 / (25 x max D0); below it the debt's share of the arrival HR is under what the case can show.
    Five points, log-spaced (equal ratios) between the two, both included; 0 is a synthetic reference (no debt-driven
    drive), never counted. Never read: tau_D, any trajectory, the legacy HR, the historical sympathetic_per_debt."""
    bpm = DEFAULT_PROFILE.hr_per_sympathetic_drive
    debts = sorted({level for case in CASES for level in gi_reference.arrival_debt_band(case).points() if level > 0})
    shares = {case: {level: gi_reference.authored(case, "hr") - value for level, value in intrinsic_levels(case).items()}
              for case in CASES}
    ratios = [share / (bpm * d0) for case in CASES for share in shares[case].values() for d0 in debts]
    high, low = max(ratios), HR_RESOLUTION_BPM / (bpm * max(debts))
    ratio = (high / low) ** (1.0 / (GAIN_POINT_COUNT - 1))
    points = tuple(low * ratio ** i for i in range(GAIN_POINT_COUNT - 1)) + (high,)
    old = {f"{tau:g}": [p / tau for p in calibration.REGISTRY["sympathetic_per_debt"].points()]
           for tau in calibration.REGISTRY["debt_clearance_tau_min"].points()}
    return {"units": "drive units per unit of D (index-minutes)", "bpm_per_drive": bpm,
            "hr_resolution_bpm": HR_RESOLUTION_BPM, "debt_levels": debts, "arrival_shares_bpm": shares,
            "low": low, "high": high, "points": points, "ratio": ratio, "synthetic_reference": GAIN_SYNTHETIC_REFERENCE,
            "every_declared_arrival_consistent_below": min(ratios), "default": DEFAULT_PROFILE.debt_to_sympathetic_gain,
            "old_status": OLD_RANGE_STATUS, "old_reason": OLD_RANGE_REASON,
            "old_induced_gains_for_comparison_only": old}


def intrinsic_levels(case: str) -> dict:
    band = gi_reference.intrinsic_hr_band(case)
    return {"lower": band.lower, "midpoint": band.midpoint, "upper": band.upper}


GAIN_RULE = gain_design.__doc__
GAINS = gain_design()["points"]
#: The gain at which the intrinsic slice is read: the range's log-midpoint, a scan anchor, not a selection.
GAIN_ANCHOR = GAINS[2]
GAIN_SCAN = GAINS + (GAIN_SYNTHETIC_REFERENCE,)


# 4. Arrival decomposition and analytic rejection (P2I-2AE-9 prefilter, items 24-25) -----------------------------------

ANALYTIC_REJECTION = "ANALYTIC_REJECTION"
ANALYTIC_RULE = ("Before any run: for every case, intrinsic level, arrival-debt level and gain, the arrival drive "
                 "S0 = (HR - intrinsic) / 25 must hold the debt's share gain x D0 (S_rest = S0 - gain x D0 >= 0, exact, "
                 "as derived.arrival_non_debt_drive computes it). Otherwise ANALYTIC_REJECTION: the arrival would need a "
                 "negative sympathetic contribution, and the core itself refuses it. No simulation reads such a pair.")


def case_anchors(case: str, intrinsic: str = "midpoint", debt: str = "midpoint"):
    values = calibration.case_values(case, calibration.GICandidate({}, intrinsic=intrinsic, debt=debt))
    return gi_reference.candidate_anchors(case, values)


def decomposition(case: str, intrinsic: str, debt: str, gain: float) -> dict:
    anchors = case_anchors(case, intrinsic, debt)
    profile = replace(DEFAULT_PROFILE, debt_to_sympathetic_gain=gain)
    try:
        split = derived.heart_rate_decomposition(anchors, profile)
    except CoreInvariantError as error:
        return {"status": ANALYTIC_REJECTION, "reason": str(error), "intrinsic": derived.intrinsic_sinus_rate(anchors),
                "D0": anchors.arrival_oxygen_debt, "gain": gain}
    reproduced = derive(derived.arrival_state(anchors, profile), anchors, profile).pulse_rate_bpm
    return {"status": "CONSISTENT", "intrinsic": split["intrinsic_sinus_rate"], "D0": anchors.arrival_oxygen_debt,
            "gain": gain, "arrival_hr": anchors.hr, "reproduced_hr": reproduced,
            "sympathetic_bpm": split["arrival_sympathetic_bpm"], "debt_bpm": split["arrival_debt_bpm"],
            "non_debt_bpm": split["arrival_non_debt_bpm"], "non_debt_drive": split["arrival_non_debt_drive"]}


def arrival_decompositions() -> dict:
    out = {}
    for case in CASES:
        out[case] = {f"{intrinsic}|{debt}|{gain!r}": decomposition(case, intrinsic, debt, gain)
                     for intrinsic in LEVELS for debt in LEVELS for gain in GAIN_SCAN}
    rejected = sum(1 for table in out.values() for row in table.values() if row["status"] == ANALYTIC_REJECTION)
    exact = all(row["reproduced_hr"] == row["arrival_hr"] for table in out.values() for row in table.values()
                if row["status"] != ANALYTIC_REJECTION)
    return {"rule": ANALYTIC_RULE, "table": out, "analytic_rejections": rejected,
            "combinations": sum(len(table) for table in out.values()), "arrival_reproduced_exactly": exact}


# 5. The representative physiology and HR post-processing (H1-H4) --------------------------------------------------------

#: H1-H4 read on the P2I-2AD representatives (LOW / MID / HIGH, its committed record): (scenario, minutes).
H_SCENARIOS = {"H1": (L1, TIMES), "H2": (L2, TIMES), "H3": (L3, (0, 15, 30, 60)), "H4": (L3, (60, 90, 120))}
H_TITLES = {"H1": "untreated active bleed (L1)", "H2": "crystalloid 2 L over 20 min with continued bleeding (L2)",
            "H3": "PRBC before haemostasis (L3, 2 units over 0-60 min, PPI)",
            "H4": "definitive management: haemostasis at 60 and restored adequacy (L3, 60-120 min)"}
FACTORIZATION = (
    "HR does not reach output, delivery, D, lactate or RR (live_audit; the drive is read only by derive's sinus rate). "
    "Each representative (tag, case, scenario) is simulated once by the full core at the default gain and intrinsic "
    "midpoint; for any other (intrinsic, gain) the drive is recomputed minute by minute from that run's pressure_rel, "
    "SpO2, glucose, D and rhythm with the core's own arithmetic (target, rise at once, decay with tau 5). Validated on "
    "full core reruns (gain at both range ends and 0, intrinsic lower / upper at the scan anchor): drive, HR, RR, D and "
    "lactate equal exactly, else the run stops.")


def p2i2ad_record() -> dict:
    record = json.loads(P2I2AD_RECORD.read_text(encoding="utf-8"))
    if record["freeze_digest"] != P2I2AD_DIGEST:
        raise AssertionError("the P2I-2AD record is not the committed one")
    return record


def representative_inputs(record: dict) -> dict:
    p2i2ab = la.record_p2i2ab()
    source, support = la.source_space(p2i2ab), p2i2ab["crystalloid_support"]
    out = {}
    for tag, item in record["representatives"].items():
        pick = item["pick"]
        if lc.lambda_label(pick["lambda"]) != item["lambda"]:
            raise AssertionError(f"{tag}: the lactate-side point is not the recorded one")
        out[tag] = {"entry": source["p3"][pick["p3"]], "bag": support[pick["support"]]["bag"],
                    "point": lc.LAMBDAS[pick["lambda"]], "pick": pick}
    return out


def full_run(inputs: dict, case: str, scenario: str, intrinsic: str = "midpoint", gain: float | None = None) -> dict:
    """One full core run of a representative (P2I-2AD's full_run at reserve 2.5, demand 1.0), with the gain set."""
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
                      lactate_clearance_tau_min=tau_l,
                      debt_to_sympathetic_gain=DEFAULT_PROFILE.debt_to_sympathetic_gain if gain is None else gain)
    states, stop = blood_anchors.trajectory(anchors, lr.scenario_items(case, scenario, full), MINUTES, profile)
    unit = full["red_cell_unit_volume_ml"]
    rows = []
    shed = [state.blood.shed_ml for state in states]
    flow = [after - before for before, after in zip(shed, shed[1:])]
    bleed = (flow[:1] or [0.0]) + flow
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


def hr_series(run_: dict, intrinsic_rate: float, gain: float) -> list[dict]:
    """The drive and HR of a run for another (intrinsic, gain), with the core's own arithmetic, and each contribution
    in bpm. Raises CoreInvariantError where the core would (an inconsistent arrival)."""
    anchors, profile, rows = run_["anchors"], run_["profile"], run_["rows"]
    response = profile.hr_per_sympathetic_drive * (1.0 - anchors.beta_blockade)
    share = anchors.hr - intrinsic_rate
    drive0 = share / response if share > 0.0 else 0.0
    debt0 = gain * anchors.arrival_oxygen_debt
    if debt0 > drive0:
        raise CoreInvariantError(f"arrival debt share {debt0!r} above the arrival drive {drive0!r}: negative "
                                 "sympathetic contribution")
    rest = drive0 - debt0
    decay = math.exp(-1.0 / profile.sympathetic_decay_tau_min)
    out, drive = [], drive0
    for minute, row in enumerate(rows):
        if minute == 0:
            parts = {"rest": rest, "debt": debt0, "pressure": 0.0, "hypoxaemia": 0.0, "hypoglycaemia": 0.0}
            target = drive = drive0
        elif not row["pulse"]:
            parts, target, drive = None, 0.0, 0.0
        else:
            hypoxaemia = (max(0.0, profile.hypoxaemia_threshold_spo2 - row["spo2"])
                          - max(0.0, profile.hypoxaemia_threshold_spo2 - anchors.spo2))
            hypoglycaemia = (max(0.0, profile.hypoglycaemia_threshold_mg_dl - row["glucose"])
                             - max(0.0, profile.hypoglycaemia_threshold_mg_dl - anchors.glucose))
            parts = {"rest": rest, "pressure": profile.sympathetic_per_pressure_deficit * (1.0 - row["pressure_rel"]),
                     "debt": gain * row["D"], "hypoxaemia": profile.sympathetic_per_hypoxaemia_point * hypoxaemia,
                     "hypoglycaemia": profile.sympathetic_per_hypoglycaemia_mg_dl * hypoglycaemia}
            target = max(0.0, (rest + parts["pressure"] + parts["debt"] + parts["hypoxaemia"]
                               + parts["hypoglycaemia"]))
            held = drive if rows[minute - 1]["pulse"] else target
            drive = target if target >= held else target + (held - target) * decay
        sinus = row["code"] == RhythmCode.SINUS.value
        hr = (intrinsic_rate + response * drive if sinus else row["rate_bpm"]) if row["pulse"] else None
        out.append({"minute": minute, "drive": drive, "target": target, "hr": hr, "parts": parts,
                    "response": response, "intrinsic": intrinsic_rate})
    return out


def contributions(point: dict) -> dict:
    """One minute's HR split in bpm: intrinsic, the arrival rest, the debt, the acute pressure term, the other stimuli,
    the floor and the decay lag; they add up to the HR."""
    if point["parts"] is None:
        return {"hr": None}
    r, parts = point["response"], point["parts"]
    total = sum((parts["rest"], parts["pressure"], parts["debt"], parts["hypoxaemia"], parts["hypoglycaemia"]))
    floor = max(0.0, total) - total
    return {"intrinsic": point["intrinsic"], "arrival_rest_bpm": r * parts["rest"], "debt_bpm": r * parts["debt"],
            "acute_pressure_bpm": r * parts["pressure"],
            "other_stimuli_bpm": r * (parts["hypoxaemia"] + parts["hypoglycaemia"]), "floor_bpm": r * floor,
            "lag_bpm": r * (point["drive"] - max(0.0, total)), "hr": point["hr"]}


def validate(runs: dict, inputs: dict) -> dict:
    """Full core reruns against the post-processing: exact equality of drive, HR, RR, D and lactate, else stop."""
    results = []
    for (tag, case, scenario), base in runs.items():
        own = hr_series(base, derived.intrinsic_sinus_rate(base["anchors"]), base["profile"].debt_to_sympathetic_gain)
        variants = [("midpoint", gain) for gain in (GAINS[0], GAINS[-1], GAIN_SYNTHETIC_REFERENCE)] + [
            (level, GAIN_ANCHOR) for level in ("lower", "upper")]
        checks = [{"variant": "base", "exact": [p["drive"] for p in own] == [r["drive"] for r in base["rows"]]
                   and [p["hr"] for p in own] == [r["hr"] for r in base["rows"]]}]
        for level, gain in variants:
            rate = intrinsic_levels(case)[level]
            try:
                series = hr_series(base, rate, gain)
            except CoreInvariantError:
                series = None
            try:
                full = full_run(inputs[tag], case, scenario, level, gain)
            except CoreInvariantError:
                full = None
            if series is None or full is None:
                checks.append({"variant": f"{level}|{gain!r}", "rejected_by_both": series is None and full is None,
                               "exact": series is None and full is None})
                continue
            rows = full["rows"]
            same = {"drive": [p["drive"] for p in series] == [r["drive"] for r in rows],
                    "hr": [p["hr"] for p in series] == [r["hr"] for r in rows],
                    "rr": [r["rr"] for r in rows] == [r["rr"] for r in base["rows"]],
                    "D": [r["D"] for r in rows] == [r["D"] for r in base["rows"]],
                    "lactate": [r["lactate"] for r in rows] == [r["lactate"] for r in base["rows"]],
                    "haemodynamics": [(r["pressure_rel"], r["output"], r["deficit"]) for r in rows]
                    == [(r["pressure_rel"], r["output"], r["deficit"]) for r in base["rows"]]}
            checks.append({"variant": f"{level}|{gain!r}", "same": same, "exact": all(same.values())})
        results.append({"tag": tag, "case": case, "scenario": scenario, "checks": checks,
                        "agree": all(check["exact"] for check in checks)})
    return {"rule": FACTORIZATION, "full_reruns": sum(len(r["checks"]) - 1 for r in results),
            "agree": all(r["agree"] for r in results), "disagreements": [r for r in results if not r["agree"]],
            "results": results}


def unchanged_physiology(runs: dict, record: dict) -> dict:
    """The representatives' D and lactate at the reported minutes equal P2I-2AD's record (L1, L3): the HR change moved
    no D, lactate or haemodynamics."""
    checked, equal = 0, True
    for tag, item in record["representatives"].items():
        for key, recorded in item["runs"].items():
            case, scenario = key.split("|")
            rows = runs[(tag, case, scenario)]["rows"]
            for row in recorded["rows"]:
                mine = rows[row["minute"]]
                checked += 1
                equal &= mine["D"] == row["D"] and mine["lactate"] == row["lactate"] and mine["deficit"] == row[
                    "effective_deficit"] and mine["output"] == row["output_rel"]
    return {"rows_checked": checked, "equal": equal}


# 6. Patient-like flags and the directional invariants (P2I-2AE-9) ------------------------------------------------------

FLAG_RULES = {
    "ARRIVAL_NOT_REPRODUCED": "HR at minute 0 differs from the authored arrival HR (exact)",
    "HR_BELOW_INTRINSIC": "a sinus HR below the intrinsic rate at any minute",
    "NEGATIVE_CONTRIBUTION": "a negative drive, arrival rest or debt contribution at any minute",
    "DRIVE_FALLS_AGAINST_ITS_TARGET": "the drive falls in a minute whose target is at or above the drive before",
    "INSTANT_NORMALIZATION_AT_HAEMOSTASIS": "with a positive gain and D > 0 one minute after haemostasis, HR is "
                                            "already at the intrinsic rate",
    "NO_DEBT_RECOVERY_AFTER_ADEQUACY": "with a positive gain, a T* (sustained adequacy) and D(T*) > 0, the debt "
                                       "contribution at 120 is not below the one at T*",
}
FLAG_POLICY = ("Structural flags only, declared before any run. No bpm threshold is used: none is committed, and the "
               "magnitudes (including the absence of any saturation) are reported on the decision surface for the "
               "faculty.")


def flags(series: list[dict], run_: dict, gain: float) -> dict:
    rows, anchors = run_["rows"], run_["anchors"]
    sinus = [(p, r) for p, r in zip(series, rows) if r["pulse"] and r["code"] == RhythmCode.SINUS.value]
    out = {"ARRIVAL_NOT_REPRODUCED": series[0]["hr"] != anchors.hr,
           "HR_BELOW_INTRINSIC": any(p["hr"] < p["intrinsic"] for p, _ in sinus),
           "NEGATIVE_CONTRIBUTION": any(p["drive"] < 0.0 or (p["parts"] is not None and (
               p["parts"]["rest"] < 0.0 or p["parts"]["debt"] < 0.0)) for p in series),
           "DRIVE_FALLS_AGAINST_ITS_TARGET": any(b["drive"] < a["drive"] and b["target"] >= a["drive"]
                                                  for a, b in zip(series, series[1:])),
           "INSTANT_NORMALIZATION_AT_HAEMOSTASIS": False, "NO_DEBT_RECOVERY_AFTER_ADEQUACY": False}
    controlled = run_["controlled_at"]
    if controlled is not None and controlled + 1 < len(series) and gain > 0.0:
        after = series[controlled + 1]
        out["INSTANT_NORMALIZATION_AT_HAEMOSTASIS"] = rows[controlled + 1]["D"] > 0.0 and after["hr"] == after[
            "intrinsic"]
    adequacy = run_["adequacy"]
    if adequacy and adequacy["onset"] is not None and gain > 0.0 and len(series) > MINUTES:
        onset = adequacy["onset"]
        if rows[onset]["D"] > 0.0:
            out["NO_DEBT_RECOVERY_AFTER_ADEQUACY"] = not series[MINUTES]["parts"]["debt"] < series[onset]["parts"][
                "debt"]
    return out


INVARIANTS = {
    1: "increasing D with all else fixed never lowers HR",
    2: "a larger acute critical deficit never lowers the sympathetic drive",
    3: "restoring adequate oxygen delivery permits sympathetic recovery",
    4: "HR recovery may lag because D persists",
    5: "haemostasis alone does not force immediate HR normalization",
    6: "one PRBC unit does not force a fixed HR decrement",
    7: "the second unit's effect may differ by state",
    8: "the crystalloid HR response depends on the resulting physiology, not on the fluid's identity",
    9: "the intrinsic rate is the floor of the sinus rate",
    10: "zero output / no pulse stays consistent with the rhythm and pulse semantics",
}


def _probe_profile(gain: float = GAIN_ANCHOR, **changes):
    return replace(DEFAULT_PROFILE, debt_to_sympathetic_gain=gain, **changes)


def _hr(state, anchors, profile):
    return derive(state, anchors, profile).pulse_rate_bpm


def synthetic_probes() -> dict:
    """H5: fixed-state probes on both GI arrivals (intrinsic and arrival debt at their midpoints), straight on the core.
    Each returns its readings and whether its invariant holds."""
    out = {}
    taus = calibration.REGISTRY["debt_clearance_tau_min"].points()
    for case in CASES:
        anchors = case_anchors(case)
        d0 = anchors.arrival_oxygen_debt
        base_profile = _probe_profile()
        arrival = derived.arrival_state(anchors, base_profile)
        probe = {}
        # tau_D at fixed D: the target and the one-minute drive, for every tau_D level.
        rows = []
        for debt in (0.0, d0, 2 * d0, 4 * d0):
            state = arrival.evolve(D=debt)
            readings = [(derived.sympathetic_target(state, anchors, _probe_profile(debt_clearance_tau_min=tau)),
                         derived.sympathetic_after_minute(arrival, state, anchors,
                                                          _probe_profile(debt_clearance_tau_min=tau))) for tau in taus]
            rows.append({"D": debt, "targets": [r[0] for r in readings], "equal": len(set(readings)) == 1})
        probe["tau_d_at_fixed_D"] = {"tau_levels": list(taus), "rows": rows, "holds": all(r["equal"] for r in rows)}
        # 1. D up, all else fixed.
        debts = (0.0, 5.0, 10.0, 20.0, 40.0, 80.0, 160.0)
        targets = [derived.sympathetic_target(arrival.evolve(D=d), anchors, base_profile) for d in debts]
        rates = [_hr(arrival.evolve(D=d).evolve(aux=replace(arrival.aux, sympathetic_drive=t)), anchors, base_profile)
                 for d, t in zip(debts, targets)]
        shares = [base_profile.debt_to_sympathetic_gain * d for d in debts]
        probe["inv1_more_debt"] = {"D": list(debts), "targets": targets, "hr": rates, "debt_drive": shares,
                                   "holds": all(b >= a for a, b in zip(targets, targets[1:]))
                                   and all(b >= a for a, b in zip(rates, rates[1:])) and shares[0] == 0.0}
        # 2. A larger acute deficit: the pump lower at the same D; red cells lower at the same pump and D.
        pumps = (1.0, 0.9, 0.8, 0.7, 0.6, 0.5)
        by_pump = [derived.sympathetic_target(arrival.evolve(P=p), anchors, base_profile) for p in pumps]
        hbs = (anchors.hb, anchors.hb - 1.0, anchors.hb - 2.0)
        by_hb = [derived.sympathetic_target(arrival.evolve(hb=h), anchors, base_profile) for h in hbs]
        one_minute = []
        for p in (1.0, 0.7):
            states = core_run(anchors, (Drift("pump", "P", 0, 1, p - 1.0),), 2, base_profile).states
            one_minute.append(states[-1].aux.sympathetic_drive)
        probe["inv2_acute_deficit"] = {"pump": list(pumps), "targets_by_pump": by_pump, "hb": list(hbs),
                                       "targets_by_hb": by_hb, "drive_after_two_minutes": one_minute,
                                       "holds": all(b >= a for a, b in zip(by_pump, by_pump[1:]))
                                       and all(b >= a for a, b in zip(by_hb, by_hb[1:]))
                                       and one_minute[1] >= one_minute[0],
                                       "note": "Hb alone leaves the target unchanged: no acute oxygen-delivery term; a "
                                               "lower Hb reaches the drive only through D"}
        # 9. The floor: stimuli far below arrival (pressure three times arrival's, no debt; synthetic).
        relieved = arrival.evolve(P=3.0, D=0.0)
        target = derived.sympathetic_target(relieved, anchors, base_profile)
        rate = _hr(relieved.evolve(aux=replace(arrival.aux, sympathetic_drive=target)), anchors, base_profile)
        probe["inv9_floor"] = {"target": target, "hr": rate, "intrinsic": derived.intrinsic_sinus_rate(anchors),
                               "holds": target >= 0.0 and rate >= derived.intrinsic_sinus_rate(anchors)}
        # 6 / 7. Red cells alone (no bleeding): two units over 60 min, read at the end of each unit.
        unit = PackedRedCells("probe_prbc", 0, 2.0, 60.0, 2.0 / 60.0, 300.0, 20.0)
        transfused = core_run(anchors, (unit,), 60, base_profile)
        hrs = [item.pulse_rate_bpm for item in transfused.derived()]
        probe["inv6_7_red_cells"] = {"hr_0_30_60": [hrs[0], hrs[30], hrs[60]], "first_unit_change": hrs[30] - hrs[0],
                                     "second_unit_change": hrs[60] - hrs[30]}
        # 8. The same crystalloid on two physiologies: the arrival and the arrival with a weaker pump.
        fluid = Crystalloid("probe_fluid", 0, 500.0, 10.0, 50.0, 1.0, 0.0, 60.0)
        responses = []
        for pump in (1.0, 0.7):
            start = (Drift("pump", "P", 0, 1, pump - 1.0),)
            alone = [item.pulse_rate_bpm for item in core_run(anchors, start, 30, base_profile).derived()]
            given = core_run(anchors, start + (fluid,), 30, base_profile)
            with_fluid = [item.pulse_rate_bpm for item in given.derived()]
            responses.append({"pump": pump, "hr_change_at_30": with_fluid[30] - alone[30],
                              "pressure_rel_at_30": given.derived()[30].pressure_rel})
        probe["inv8_crystalloid"] = {"responses": responses}
        # 10. No pulse: a scripted PEA at minute 10 during bleeding; a paced perfusing rhythm keeps its own rate.
        falling = (Drift("pump", "P", 0, 30, -0.01),)
        arrest = core_run(anchors, falling + (ScriptedRhythmEvent("probe_pea", 10, RhythmState.pea(40.0), "probe"),), 20,
                          base_profile)
        paced = core_run(anchors, falling + (ScriptedRhythmEvent("probe_paced", 10, RhythmState(RhythmCode.PACED, 70.0,
                                                                                               1.0, True), "probe"),),
                         20, base_profile)
        probe["inv10_rhythm"] = {
            "pea_pulse_rates": sorted({str(item.pulse_rate_bpm) for item in arrest.derived()[10:]}),
            "pea_drives": sorted({state.aux.sympathetic_drive for state in arrest.states[10:]}),
            "paced_rates": sorted({item.pulse_rate_bpm for item in paced.derived()[10:]}),
            "holds": all(item.pulse_rate_bpm is None for item in arrest.derived()[10:])
            and all(state.aux.sympathetic_drive == 0.0 for state in arrest.states[10:])
            and {item.pulse_rate_bpm for item in paced.derived()[10:]} == {70.0}}
        out[case] = probe
    # 6 / 7 / 8 across both cases: the changes are state-dependent, never one constant.
    first = [out[c]["inv6_7_red_cells"]["first_unit_change"] for c in CASES]
    second = [out[c]["inv6_7_red_cells"]["second_unit_change"] for c in CASES]
    crystalloid = [r["hr_change_at_30"] for c in CASES for r in out[c]["inv8_crystalloid"]["responses"]]
    out["inv6_one_unit_not_fixed"] = {"first_unit_changes": first, "holds": len(set(first)) > 1}
    out["inv7_second_unit_may_differ"] = {"second_unit_changes": second,
                                          "holds": any(a != b for a, b in zip(first, second))}
    out["inv8_physiology_not_identity"] = {
        "changes": crystalloid, "holds": len(set(crystalloid)) > 1 and all(
            "intervention" not in inspect.signature(f).parameters and "items" not in inspect.signature(f).parameters
            for f in (derive, derived.sympathetic_target, derived.sympathetic_after_minute))}
    out["d_scale"] = d_scale_probe()
    return out


def d_scale_probe() -> dict:
    """Only gain x g and gain x D0 reach HR: (g, gain, D0) -> (c g, gain / c, c D0) leaves every minute's HR unchanged
    (to rounding) on a synthetic untreated run whose D accrues."""
    case = CASES[0]
    anchors = case_anchors(case)
    out = []
    for c in (0.5, 2.0):
        scaled = replace(anchors, arrival_oxygen_debt=c * anchors.arrival_oxygen_debt)
        rates = []
        for a, profile in ((anchors, _probe_profile()),
                           (scaled, _probe_profile(GAIN_ANCHOR / c,
                                                   debt_per_delivery_deficit=c * DEFAULT_PROFILE.debt_per_delivery_deficit))):
            rates.append([item.pulse_rate_bpm for item in
                          core_run(a, (Drift("pump", "P", 0, 90, -0.005),), 90, profile).derived()])
        out.append({"c": c, "max_gap_bpm": max(abs(x - y) for x, y in zip(*rates))})
    return {"rows": out, "holds": all(row["max_gap_bpm"] <= 1e-9 for row in out)}


def run_invariants(scan: dict, probes: dict) -> dict:
    """The ten directions, on the synthetic probes (exact) and on every scanned representative run."""
    every = [item for item in scan.values() if item["status"] != ANALYTIC_REJECTION]
    positive = [item for item in every if item["gain"] > 0.0]
    l3 = [item for item in positive if item["scenario"] == L3]
    recovery = [item for item in l3 if item["adequacy_onset"] is not None and item["debt_at_onset"] > 0.0]
    probes_ok = lambda name: all(probes[c][name]["holds"] for c in CASES)  # noqa: E731
    results = {
        1: probes_ok("inv1_more_debt") and probes_ok("tau_d_at_fixed_D"),
        2: probes_ok("inv2_acute_deficit"),
        3: bool(recovery) and all(item["debt_bpm_120"] < item["debt_bpm_onset"] for item in recovery),
        4: bool(recovery) and all(item["debt_bpm_onset_plus_1"] > 0.0 for item in recovery),
        5: bool(l3) and not any(item["flags"]["INSTANT_NORMALIZATION_AT_HAEMOSTASIS"] for item in l3),
        6: probes["inv6_one_unit_not_fixed"]["holds"],
        7: probes["inv7_second_unit_may_differ"]["holds"],
        8: probes["inv8_physiology_not_identity"]["holds"],
        9: probes_ok("inv9_floor") and not any(item["flags"]["HR_BELOW_INTRINSIC"] for item in every),
        10: probes_ok("inv10_rhythm"),
    }
    return {"statements": INVARIANTS, "results": results, "all_pass": all(results.values()),
            "recovery_runs": len(recovery), "l3_runs": len(l3)}


# 7. The scan: the (intrinsic, gain) plane post-processed on each representative run -----------------------------------

SCAN_RULE = ("The (intrinsic level, gain) plane, 3 x 6 (five range points and the 0 reference), post-processed on each "
             "of the 18 representative runs (3 tags x 2 cases x L1 / L2 / L3): no simulation beyond the 18 runs and "
             "the validation reruns. Analytically rejected pairs are never read. The intrinsic slice is read at the "
             "gain anchor (the range's log-midpoint) and the gain slice at intrinsic midpoint; neither is a selection.")


def scan(runs: dict) -> dict:
    out = {}
    for (tag, case, scenario), run_ in runs.items():
        levels = intrinsic_levels(case)
        for level in LEVELS:
            for gain in GAIN_SCAN:
                key = f"{tag}|{case}|{scenario}|{level}|{gain!r}"
                try:
                    series = hr_series(run_, levels[level], gain)
                except CoreInvariantError:
                    out[key] = {"tag": tag, "case": case, "scenario": scenario, "intrinsic": level, "gain": gain,
                                "status": ANALYTIC_REJECTION}
                    continue
                adequacy = run_["adequacy"]
                onset = adequacy["onset"] if adequacy else None
                rows = run_["rows"]
                debt_bpm = [None if p["parts"] is None else p["response"] * p["parts"]["debt"] for p in series]
                out[key] = {"tag": tag, "case": case, "scenario": scenario, "intrinsic": level, "gain": gain,
                            "status": "READ", "flags": flags(series, run_, gain), "stop": run_["stop"],
                            "hr": [p["hr"] for p in series],
                            "floor_minutes": sum(1 for p in series if p["parts"] is not None and sum(
                                p["parts"].values()) < 0.0),
                            "points": {str(m): {**contributions(series[m]), "D": rows[m]["D"],
                                                "effective_deficit": rows[m]["deficit"], "output": rows[m]["output"],
                                                "bleed_ml_per_min": rows[m]["bleed_ml_per_min"],
                                                "prbc_units": rows[m]["prbc_units"],
                                                "crystalloid_in_ml": rows[m]["crystalloid_in_ml"],
                                                "haemostasis": run_["controlled_at"] is not None
                                                and m >= run_["controlled_at"], "rr": rows[m]["rr"],
                                                "lactate": rows[m]["lactate"]}
                                       for m in TIMES if m < len(series)},
                            "adequacy_onset": onset,
                            "debt_at_onset": rows[onset]["D"] if onset is not None else None,
                            "debt_bpm_onset": debt_bpm[onset] if onset is not None else None,
                            "debt_bpm_onset_plus_1": debt_bpm[onset + 1] if onset is not None else None,
                            "debt_bpm_120": debt_bpm[MINUTES] if len(series) > MINUTES else None,
                            "hr_at_onset": series[onset]["hr"] if onset is not None else None}
    return out


def trajectories(scan_: dict) -> dict:
    """H1-H4 per case at their minutes, for the gain slice (intrinsic midpoint) and the intrinsic slice (gain anchor)."""
    out = {}
    for name, (scenario, minutes) in H_SCENARIOS.items():
        out[name] = {"title": H_TITLES[name], "scenario": scenario, "minutes": list(minutes), "cases": {}}
        for case in CASES:
            table = {}
            for key, item in scan_.items():
                if item["case"] != case or item["scenario"] != scenario:
                    continue
                if not (item["intrinsic"] == "midpoint" or item["gain"] == GAIN_ANCHOR):
                    continue
                label = f"{item['tag']}|{item['intrinsic']}|{item['gain']!r}"
                table[label] = (ANALYTIC_REJECTION if item["status"] == ANALYTIC_REJECTION else
                                {str(m): item["points"][str(m)] for m in minutes if str(m) in item["points"]})
            out[name]["cases"][case] = table
    return out


def decision_surface(scan_: dict) -> dict:
    """P2I-2AE-5: what faculty would set numbers on, per case and landmark, across the gain range (intrinsic midpoint)
    and the representatives. No envelope is drawn: the readings only."""
    landmarks = {"arrival": (L1, 0), "untreated_30": (L1, 30), "untreated_60": (L1, 60), "untreated_120": (L1, 120),
                 "after_crystalloid_30": (L2, 30), "crystalloid_120": (L2, 120), "after_prbc_unit_1": (L3, 30),
                 "after_prbc_unit_2_and_haemostasis": (L3, 60), "after_haemostasis_90": (L3, 90),
                 "restored_adequacy_120": (L3, 120), "persistent_critical_120": (L1, 120)}
    out = {}
    for case in CASES:
        out[case] = {}
        for name, (scenario, minute) in landmarks.items():
            cell = {}
            for gain in GAIN_SCAN:
                values = {}
                for tag in ("LOW", "MID", "HIGH"):
                    item = scan_[f"{tag}|{case}|{scenario}|midpoint|{gain!r}"]
                    if item["status"] == ANALYTIC_REJECTION:
                        values[tag] = ANALYTIC_REJECTION
                    elif str(minute) in item["points"]:
                        point = item["points"][str(minute)]
                        values[tag] = {"hr": point["hr"], "debt_bpm": point.get("debt_bpm"),
                                       "acute_pressure_bpm": point.get("acute_pressure_bpm"),
                                       "arrival_rest_bpm": point.get("arrival_rest_bpm"),
                                       "lag_bpm": point.get("lag_bpm"), "D": point["D"]}
                    else:
                        values[tag] = "STOPPED"
                cell[repr(gain)] = values
            out[case][name] = cell
        onsets = {}
        for tag in ("LOW", "MID", "HIGH"):
            item = scan_[f"{tag}|{case}|{L3}|midpoint|{GAIN_ANCHOR!r}"]
            onsets[tag] = None if item["status"] == ANALYTIC_REJECTION else {
                "onset": item["adequacy_onset"], "hr_at_onset": item["hr_at_onset"]}
        out[case]["restored_adequacy_onset_at_gain_anchor"] = onsets
    return {"landmarks": {k: list(v) for k, v in landmarks.items()}, "table": out,
            "note": "no committed numeric HR band exists; nothing here is an envelope or a target"}


# 8. Identifiability (P2I-2AE-10) ---------------------------------------------------------------------------------------

NON_IDENTIFIABLE = "NON_IDENTIFIABLE"
IDENTIFIABILITY_RULE = (
    "Available HR observations: the authored arrival HR of each case only. Exact structure: while the drive is "
    "positive, HR(t) = HR_arrival + 25 x [gain x (D(t) - D0) + pressure, hypoxaemia and glucose deviations] with the "
    "decay lag, so the intrinsic rate cancels and reaches HR only where the floor binds; the arrival HR fixes "
    "intrinsic + 25 x (S_rest + gain x D0) and S_rest is free and non-negative, so it constrains only the sum "
    "intrinsic + 25 x gain x D0 <= HR_arrival.")


def identifiability(scan_: dict, analytic: dict, probes: dict) -> dict:
    gaps, floor_binds = [], 0
    for key, item in scan_.items():
        if item["status"] == ANALYTIC_REJECTION or item["intrinsic"] != "midpoint":
            continue
        for level in ("lower", "upper"):
            other = scan_[key.replace("|midpoint|", f"|{level}|")]
            if other["status"] == ANALYTIC_REJECTION:
                continue
            if item["floor_minutes"] or other["floor_minutes"]:
                floor_binds += 1
                continue
            gaps.append(max(abs(a - b) for a, b in zip(item["hr"], other["hr"])))
    consistent = {case: sorted({(row["intrinsic"], row["D0"]) for row in analytic["table"][case].values()
                                if row["status"] != ANALYTIC_REJECTION}) for case in CASES}
    return {"rule": IDENTIFIABILITY_RULE,
            "intrinsic_vs_gain": {"pairs_compared": len(gaps), "max_hr_gap_bpm": max(gaps, default=0.0),
                                  "pairs_where_the_floor_binds": floor_binds,
                                  "status": NON_IDENTIFIABLE,
                                  "why": "every consistent (intrinsic, gain) pair reproduces the arrival HR exactly; "
                                         "above the floor the intrinsic rate cancels (the HR gaps between intrinsic "
                                         "levels at the same gain are rounding only); no post-arrival HR is authored "
                                         "to separate the gain"},
            "dimensions": {
                "intrinsic_sinus_rate": {"status": NON_IDENTIFIABLE, "support": "the band (60 / 80 / 100, capped at the "
                                         "arrival HR) less the analytic rejections",
                                         "consistent_intrinsic_D0": consistent},
                "debt_to_sympathetic_gain": {"status": NON_IDENTIFIABLE, "support": f"[{GAINS[0]:.4g}, {GAINS[-1]:.4g}] "
                                             "less the analytic rejections; only gain x D0 at arrival and gain x g "
                                             "over a run reach HR"},
                "sympathetic_per_pressure_deficit": {"status": "NOT_EVALUATED_PRESSURE_DOMAIN",
                                                     "support": "1.0 (PROVISIONAL), not varied: it sets how far "
                                                                "restored pressure unloads the arrival rest"},
                "saturation_or_cap": {"status": "NO_PARAMETER", "support": "the core has no HR cap or saturation"},
                "d_scale": {"status": NON_IDENTIFIABLE, "support": "(g, gain, D0) -> (c g, gain / c, c D0) leaves HR "
                            "unchanged", "probe": probes["d_scale"]},
                "sympathetic_decay_tau_min": {"status": "NOT_VARIED", "support": "5 min (PROVISIONAL)"}}}


# 9. RR, legacy, verdict and freeze ---------------------------------------------------------------------------------------

def rr_audit(validation: dict, audit: dict, unchanged: dict) -> dict:
    same_rr = all(check["same"]["rr"] for r in validation["results"] for check in r["checks"] if "same" in check)
    return {"source": "derived.respiratory_rate reads lactate and W only; no drive, pulse rate or rhythm rate",
            "rr_reads_hr": not audit["rr_independent_of_hr"], "rr_equal_across_gain_and_intrinsic": same_rr,
            "d_and_lactate_unchanged_from_p2i2ad": unchanged["equal"],
            "changes_rr": not (audit["rr_independent_of_hr"] and same_rr and unchanged["equal"]),
            "calibrated": False}


LEGACY_RULE = ("LEGACY REFERENCE, NOT A CALIBRATION TARGET: the family engine's HR at 0, 15, 30, 60, 90 and 120 min, "
               "read after the verdict, never by the gain range, a flag, an invariant, identifiability or the verdict.")


def legacy_reference(scan_: dict) -> dict:
    if lr.LegacyLock.held:
        raise AssertionError("the legacy HR is read only after the verdict")
    out = {}
    for case in CASES:
        out[case] = {}
        for scenario in (L1, L2, L3):
            snapshots = {item["minute"]: item for item in
                         calibration._legacy_run(case, lactate_slice.ORDERS[scenario]).snapshots}
            out[case][scenario] = {str(m): snapshots[m]["hr"] for m in TIMES if m in snapshots}
    beside = {}
    for case in CASES:
        for scenario in (L1, L2, L3):
            core = {}
            for m in TIMES:
                values = [scan_[f"{tag}|{case}|{scenario}|midpoint|{gain!r}"]["points"].get(str(m), {}).get("hr")
                          for tag in ("LOW", "MID", "HIGH") for gain in GAINS
                          if scan_[f"{tag}|{case}|{scenario}|midpoint|{gain!r}"]["status"] != ANALYTIC_REJECTION]
                values = [v for v in values if v is not None]
                core[str(m)] = [min(values), max(values)] if values else None
            beside[f"{case}|{scenario}"] = {"core_range_over_gains_and_tags": core,
                                            "legacy": out[case][scenario]}
    return {"rule": LEGACY_RULE, "legacy": out, "beside": beside}


READY = "HR_STRUCTURE_READY_FOR_NUMERIC_FACULTY_CALIBRATION"
NOT_READY = "HR_STRUCTURE_NOT_READY"
VERDICT_RULE = (
    "HR_STRUCTURE_READY_FOR_NUMERIC_FACULTY_CALIBRATION when every check holds: (1) tau_D no longer reaches HR (the "
    "core's source and the fixed-D probe at every tau_D level); (2) the contributors are explicit (the audit, and every "
    "reported minute's contributions add up to its HR within 1e-9); (3) the arrival decomposition is coherent (every "
    "consistent pair reproduces the arrival HR exactly, the analytic rejections are exactly the pairs the core refuses, "
    "and each case keeps a consistent pair with a positive gain at every arrival-debt level); (4) the ten directional "
    "invariants pass; (5) no structural patient-like flag in any read run; (6) the support is explicit (gain range "
    "and identifiability table); (7) nothing is approved (no value selected; the default profile unchanged); and the "
    "post-processing agrees with the full core. Otherwise HR_STRUCTURE_NOT_READY with the first blocker. No numeric HR "
    "band is required.")
NEXT_STEP = ("Next step (not started; needs its own authorization): a small faculty HR numeric-calibration "
             "package (intrinsic rate, debt_to_sympathetic_gain, whether a sinus-rate ceiling or saturation is wanted, "
             "and HR readings at the decision-surface landmarks). Pressure and vascular tone follow HR; not started.")


def verdict(audit: dict, probes: dict, analytic: dict, scan_: dict, invariants: dict, validation: dict,
            identifiable: dict, refused: dict) -> dict:
    read = [item for item in scan_.values() if item["status"] != ANALYTIC_REJECTION]
    sums = all(abs(sum(v for k, v in point.items() if k.endswith("_bpm")) + point["intrinsic"] - point["hr"]) <= 1e-9
               for item in read for point in item["points"].values() if point.get("hr") is not None
               and "intrinsic" in point)
    coverage = all(any(row["status"] != ANALYTIC_REJECTION and row["gain"] > 0.0 and row["D0"] == d0
                       for row in analytic["table"][case].values())
                   for case in CASES for d0 in {row["D0"] for row in analytic["table"][case].values()})
    flagged = sorted({name for item in read for name, on in item["flags"].items() if on})
    checks = [
        ("factorization", validation["agree"], "the post-processing does not agree with the full core"),
        ("no_tau_d_leak", audit["no_tau_d_in_hr"] and all(probes[c]["tau_d_at_fixed_D"]["holds"] for c in CASES),
         "tau_D still reaches HR at fixed D"),
        ("contributors_explicit", sums, "a reported HR is not the sum of its contributions"),
        ("arrival_coherent", analytic["arrival_reproduced_exactly"] and refused["agree"] and coverage,
         "the arrival decomposition is not coherent"),
        ("invariants", invariants["all_pass"], "a directional invariant fails"),
        ("patient_like", not flagged, f"structural flags: {flagged}"),
        ("support_explicit", len(GAINS) == GAIN_POINT_COUNT and all(
            "status" in row for row in identifiable["dimensions"].values()), "the support is not explicit"),
        ("nothing_approved", DEFAULT_PROFILE == derived.CoreProfile() and derived.PARAMETERS[
            "debt_to_sympathetic_gain"][0] == derived.PROVISIONAL, "a value is approved"),
    ]
    blockers = [why for _, passed, why in checks if not passed]
    return {"verdict": READY if not blockers else f"{NOT_READY} — {blockers[0]}",
            "checks": {name: passed for name, passed, _ in checks}, "blockers": blockers, "flags_seen": flagged,
            "rule": VERDICT_RULE, "next_step": NEXT_STEP if not blockers else None}


def refused_by_core(analytic: dict) -> dict:
    """The analytic rejections are exactly the arrivals the core refuses (arrival_state raises)."""
    mismatches = []
    for case in CASES:
        for key, row in analytic["table"][case].items():
            intrinsic, debt, gain = key.split("|")
            anchors = case_anchors(case, intrinsic, debt)
            try:
                derived.arrival_state(anchors, replace(DEFAULT_PROFILE, debt_to_sympathetic_gain=float(gain)))
                refused = False
            except CoreInvariantError:
                refused = True
            if refused != (row["status"] == ANALYTIC_REJECTION):
                mismatches.append(f"{case}|{key}")
    return {"agree": not mismatches, "mismatches": mismatches}


POLICY = ("Shadow only. The P2I-2AD representatives (its committed record) and synthetic probes on the GI arrivals, "
          "never the P2F historical region. tau_D repays D only; the debt-driven drive is debt_to_sympathetic_gain x D, "
          "explored on a range built before any HR outcome; the arrival HR is intrinsic + a non-negative sympathetic "
          "contribution, inconsistent arrivals rejected analytically. HR post-processed exactly (validated, else stop). "
          "No HR envelope is invented; no SBP, MAP or RR is calibrated; the legacy HR is read after the verdict only; "
          "nothing is fitted, selected or approved; collapse stays off.")


def design() -> dict:
    return {"faculty": FACULTY, "old_equation": OLD_EQUATION, "new_equation": NEW_EQUATION,
            "contributors": CONTRIBUTORS, "tau_d_paths": list(TAU_D_PATHS), "deficit_audit": DEFICIT_AUDIT,
            "gain": {**gain_design(), "rule": GAIN_RULE, "anchor": GAIN_ANCHOR, "scan": list(GAIN_SCAN)},
            "analytic": ANALYTIC_RULE, "scenarios": {k: [v[0], list(v[1])] for k, v in H_SCENARIOS.items()},
            "titles": H_TITLES, "factorization": FACTORIZATION, "scan": SCAN_RULE, "flags": FLAG_RULES,
            "flag_policy": FLAG_POLICY, "invariants": INVARIANTS, "identifiability": IDENTIFIABILITY_RULE,
            "legacy": LEGACY_RULE, "verdict": VERDICT_RULE, "next_step": NEXT_STEP, "policy": POLICY}


def freeze_digest() -> str:
    text = json.dumps({"revision": REVISION, "record": hashlib.sha256(P2I2AD_RECORD.read_bytes()).hexdigest(),
                       "design": design(), "sources": bf.freeze_sources()}, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run(progress=None) -> dict:
    say = progress or (lambda *_: None)
    with lr.P2FGuard(), lr.LegacyLock():
        record = p2i2ad_record()
        audit = live_audit()
        say("analytic")
        analytic = arrival_decompositions()
        refused = refused_by_core(analytic)
        say("probes")
        probes = synthetic_probes()
        say("representatives")
        inputs = representative_inputs(record)
        runs = {(tag, case, scenario): full_run(inputs[tag], case, scenario)
                for tag in inputs for case in CASES for scenario in (L1, L2, L3)}
        say("validation")
        validation = validate(runs, inputs)
        unchanged = unchanged_physiology(runs, record)
        out = {"freeze_digest": freeze_digest(), "decided": DECIDED, "revision": REVISION, "policy": POLICY,
               "faculty": FACULTY, "records": {"P2I-2AD": P2I2AD_DIGEST}, "audit": {
                   "old_equation": OLD_EQUATION, "new_equation": NEW_EQUATION, "contributors": CONTRIBUTORS,
                   "tau_d_paths": list(TAU_D_PATHS), "deficit": DEFICIT_AUDIT, "live": audit},
               "anchors": anchors_table(), "intrinsic": intrinsic_audit(), "gain": gain_design(),
               "analytic": analytic, "refused_by_core": refused, "probes": probes,
               "validation": {k: v for k, v in validation.items() if k != "results"},
               "unchanged_physiology": unchanged}
        if not validation["agree"]:
            out["verdict"] = {"verdict": f"{NOT_READY} — the post-processing does not agree with the full core"}
            return out
        say("scan")
        scanned = scan(runs)
        invariants = run_invariants(scanned, probes)
        identifiable = identifiability(scanned, analytic, probes)
        out.update({"scan_rule": SCAN_RULE, "trajectories": trajectories(scanned),
                    "decision_surface": decision_surface(scanned), "invariants": invariants,
                    "flags": {name: sum(1 for item in scanned.values() if item["status"] != ANALYTIC_REJECTION
                                        and item["flags"][name]) for name in FLAG_RULES},
                    "identifiability": identifiable, "rr": rr_audit(validation, audit, unchanged),
                    "verdict": verdict(audit, probes, analytic, scanned, invariants, validation, identifiable,
                                       refused)})
    out["legacy_reference"] = legacy_reference(scanned)
    out["efficiency"] = {
        "representative_runs": len(runs), "validation_full_reruns": validation["full_reruns"],
        "post_processed_series": sum(1 for item in scanned.values() if item["status"] != ANALYTIC_REJECTION),
        "scan_pairs_rejected_analytically": sum(1 for item in scanned.values() if item["status"] == ANALYTIC_REJECTION),
        "analytic_rejections": analytic["analytic_rejections"], "analytic_combinations": analytic["combinations"],
        "naive_core_runs": len(scanned), "simulations_avoided": len(scanned) - len(runs) - validation["full_reruns"],
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
        (out / "hr_structure.json").write_text(json.dumps(result, indent=1, sort_keys=True, default=str),
                                               encoding="utf-8")
        print(out / "hr_structure.json")
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
