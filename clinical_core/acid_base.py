"""Phase 2 shadow core, P2K-2: the metabolic acid burden and the effective-ventilation core.

    python -m clinical_core.acid_base --digest
    python -m clinical_core.acid_base --design
    python -m clinical_core.acid_base --run --out <directory outside the repository>

Shadow only and offline (faculty brief of 2026-10-31, recorded in FACULTY). P2K-1 found the RR structure not ready: the
only metabolic input to RR was the lactate concentration. P2K-2 adds to the core, off by default, the physiology the
faculty authorized: a metabolic acid burden with its own dynamics (production from the effective oxygen deficit,
first-order clearance), a respiratory drive read from that burden only, RR from the intrinsic RR and the drive, the
effective ventilation W as RR x efficiency relative to need, PaCO2 algebraic in W and anchored to the authored arrival
PaCO2, and pH from HCO3 and PaCO2. In that candidate physiology lactate, D and the W channel reach no RR term.

This module records the semantics, predeclares the exploratory candidate ranges from the authored arrival blood gas, the
arrival effective deficits and dimensional rules (before any clinical respiratory trajectory is read), runs the
structural probes A-H, reconstructs R1-R4 for both cases by factorized post-processing of the certified deficit
trajectories (validated against full core runs, upstream rows identical), and reads arrival compatibility, the key
questions, identifiability, the upstream dependencies and readiness. Nothing is selected or approved; no RR envelope
filters anything; the legacy RR is never read. It also holds the AST proof that P2K-2 changed the three core files only
by its declared, off-by-default insertions, and the dependency maps the closed packages' freezes rest on.
"""
from __future__ import annotations

import argparse
import ast
import copy
import functools
import hashlib
import json
import math
from dataclasses import replace
from pathlib import Path

from . import baroreflex as br
from . import blood_anchors
from . import blood_fluid_calibration as bf
from . import calibration
from . import derived as dv
from . import gi_reference
from . import lactate_adequacy as la
from . import lactate_rebuild as lr
from . import pressure_tone as pt
from . import rr_audit as ra
from . import vascular_tone as vt
from .derived import DEFAULT_PROFILE, arrival_state, derive, respiration
from .integration import step

DECIDED = "2026-10-31"
REVISION = "P2K-2"
ROOT = br.ROOT
CASES = br.CASES
C57, C72 = br.C57, br.C72
DEMANDS = br.DEMANDS
TONE_GAINS = br.TONE_GAINS
AFTERLOAD = br.AFTERLOAD
LAMBDAS = br.LAMBDAS
RESERVE = vt.RESERVE
P2K1_RECORD = ROOT / "docs" / "revision" / "P2K1_rr_audit.json"
P2K1_DIGEST = "a3f098deb7d643e6158da3aaa8852874d6fa35d981379be173a17d6d8d8ec427"

# 1. The faculty decisions (2026-10-31) -----------------------------------------------------------------------------------

FACULTY = {
    "decided": DECIDED,
    "closed": "P2K-1 accepted and closed: RR_STRUCTURE_NOT_READY - ACID_BASE_STATE_REQUIRED is a genuine structural "
              "blocker; RR is not calibrated numerically on the direct lactate -> RR proxy",
    "carried": "MAP_set 80 / 90 / 100 and the baroreflex gain conditional on demand (1.0: 0.25, 0.5; 1.1: 0.25, 0.5, 1.0, "
               "1.5) carried, not collapsed, not selected; nothing FACULTY_APPROVED",
    "acid_state": "a new common state, metabolic_acid_burden: a time-varying metabolic acid / bicarbonate-deficit burden, "
                  "not lactate, not D, not pH; burden = max(0, HCO3_reference - HCO3), HCO3_reference 24 mEq/L "
                  "COMMON_REFERENCE_PROVISIONAL, not FACULTY_APPROVED; the arrival burden from the bank's HCO3 (57m 17.3, "
                  "72f 19.8), never from lactate",
    "acid_dynamics": "dA/dt = production from the effective oxygen deficit - clearance; more deficit never less "
                     "production, no deficit no new production, gradual clearance, the burden may fall while a deficit "
                     "lasts, never below 0; D's no-repayment rule is not copied",
    "acid_parameters": "explicit exploratory deficit_to_acid_gain and acid_clearance_tau, independent of the debt and "
                       "lactate parameters; a small range predeclared before clinical outcomes, from dimensional "
                       "consistency, the authored arrival burden, the current deficit trajectories, synthetic probes and "
                       "no instantaneous normalization; no legacy RR fitting, no final value",
    "lactate": "once the acid burden is active, the lactate concentration drives no RR; lactate stays a biomarker; a "
               "guard proves lactate alone, with burden and ventilation fixed, leaves RR unchanged",
    "d": "D is oxygen-delivery debt and never drives RR directly; deficit -> acid burden -> drive is the metabolic path",
    "drive_rr_w": "respiratory drive (central command), RR (observable frequency) and W (effective alveolar ventilation "
                  "relative to metabolic need) are three quantities, never aliases; mechanics preserved, no support, no "
                  "fatigue in the GI cases, so RR and W correlate, but the structure lets them diverge",
    "drive": "drive from the acid burden only; no new drivers for D, lactate, pressure or HR; explicit "
             "acid_to_respiratory_drive_gain, no value approved; hypoxaemic drive audited, numerically deferred",
    "rr": "RR from the patient-specific intrinsic RR plus the non-negative drive, continuous and monotone, smoothly "
          "saturating; no lactate or D term; no hard clip as the primary physiology",
    "intrinsic_rr": "intrinsic RR 12 / 16 / 20 per patient, EXPLORATORY, not FACULTY_APPROVED; the two patients may "
                    "differ; no case-specific acid-drive gain; no value added after outcomes",
    "arrival": "57m RR 26, 72f RR 24 against the HCO3-derived burden; the drive range is built before arrival "
               "compatibility is counted; common acid-to-drive physiology, patient-specific intrinsic RR, no residual "
               "offset; mismatch at +/- 3 breaths/min, ARRIVAL_RR_TOLERANCE_PROVISIONAL, not a measurement error; "
               "zero common candidates is a stop, never a wider tolerance",
    "w": "W = effective alveolar ventilation relative to metabolic ventilatory need: 1 matches it, below 1 relative "
         "hypoventilation, above 1 relative hyperventilation; not the drive",
    "efficiency": "effective ventilation rises with RR in the spontaneous GI cases, with an explicit "
                  "ventilation_efficiency so a high RR does not guarantee a high W; 1 for the GI cases as a STRUCTURAL "
                  "REFERENCE, below 1 only in synthetic probes; no mechanics / fatigue grid",
    "paco2": "algebraic from W, higher W lower PaCO2, anchored to each patient's authored arrival PaCO2 (57m 31, 72f 33) "
             "so minute 0 is exact by construction; no PaCO2 time constant in P2K-2",
    "ph": "pH from HCO3 and PaCO2 by the bicarbonate / CO2 relation, never a tuned state; arrival 57m 7.37 and 72f 7.40 "
          "within source rounding, the exact error reported, no offset",
    "w_leak": "the old W use (W > 0 multiplying part of RR, W < 0 scaling it) is a SEMANTIC_LEAK retired in the "
              "candidate: drive -> RR, drive + efficiency -> W, W -> PaCO2, never W -> drive",
    "hypoxaemia": "HYPOXEMIC_DRIVE_DEFERRED: no new gain; the GI cases are not hypoxaemic; the architecture allows a later "
                  "term",
    "lgn": "L, G and N are not added as RR drivers for the GI cases: GENERALIZATION_PATH_RESERVED",
    "support": "spontaneous breathing, room air except FiO2 where represented, no NIV or invasive ventilation: the "
               "mechanical override is not a GI blocker; no NIV / mode / PEEP in P2K-2: FUTURE_GENERALIZATION_REQUIREMENT; "
               "FiO2 acts through oxygenation and delivery",
    "upstream": "BloodState, output, pressure / tone, DO2 / effective deficit, D, lactate and HR / baroreflex are reused "
                "and must not change; only respiratory outputs may",
    "early_stop": "algebraic non-uniqueness, unstable acid / ventilation feedback, evaluation-order dependence, impossible "
                  "pH / PaCO2 or an upstream regression stops the package; no parameter hides a structural problem",
    "scope": "shadow only: no runtime integration, GI or second-family migration, final RR / acid approval, hard RR "
             "envelope, consciousness recalibration, collapse activation, mechanical-ventilation calibration or legacy "
             "fitting",
}
CARRIED = ra.CARRIED

# 2. The semantics the core now holds (P2K-2-1 to P2K-2-9) ----------------------------------------------------------------

SEMANTICS = {
    "acid_burden": "aux.metabolic_acid_burden (mEq/L), a dynamic state: arrival = max(0, HCO3_reference - arrival HCO3); "
                   "each minute A' = A + deficit_to_acid_gain x effective_deficit - A / acid_clearance_tau "
                   "(derived.acid_burden_after_minute, integration._acid_burden); never below 0 (tau >= 1)",
    "production": "the minute's effective oxygen deficit, max(0, demand - reserve x delivery) at the start-of-minute "
                  "delivery and the minute's demand: the one D integrates; linear, so more deficit never produces less "
                  "and no deficit produces nothing",
    "clearance": "first-order, always on: the burden falls whenever A / tau exceeds the production, also while a "
                 "deficit lasts; no no-repayment rule",
    "bicarbonate": "HCO3 = arrival HCO3 - (A - arrival A) = HCO3_reference - A below the reference",
    "drive": "respiratory_drive = acid_to_drive_gain x A (breaths/min-equivalent): the burden only",
    "rr": "RR = intrinsic + S (1 - exp(-drive / S)), S = rr_drive_saturation (25, structural); rr_max a safety guard "
          "only; RR = 0 without a pulse",
    "w": "W = efficiency x (RR / intrinsic RR) / (demand / baseline demand): effective alveolar ventilation over the "
         "ventilation of the patient's eupnoea at the current CO2 production; 1 at the intrinsic RR with no drive and "
         "mechanics preserved. 'Need' is that eupnoeic ventilation: it is eucapnic only when the implied resting PaCO2 "
         "is (adversarial review)",
    "paco2": "PaCO2 = PaCO2_rest / W, PaCO2_rest = arrival PaCO2 x the arrival W at the reference efficiency 1 (the "
             "model's arrival RR): exact at minute 0 when the arrival efficiency is the reference (the GI cases); a lower "
             "efficiency lowers W and raises PaCO2 above that anchor (review: a constant efficiency used on both sides "
             "cancelled); PaCO2_rest is implied by the anchoring, not a parameter",
    "ph": "pH = 6.1 + log10(HCO3 / (0.03 PaCO2)), the case bank's own constants (clinical_cases._gas)",
    "w_channel": "the W channel (C7) is read by no candidate term: RESERVED for future families; the default profile "
                 "keeps the P2K-1 RR for the frozen records",
    "default": "off by default: the three gains None leave every default run, the golden and every closed record "
               "unchanged; the candidate is the profile with the three gains declared",
}
RETIRED = {
    "lactate_rr": "RETIRED_IN_CANDIDATE: no candidate RR term reads lactate (BIOMARKER_PROXY_REQUIRES_REFACTOR resolved "
                  "for the candidate); the default profile keeps it only for the frozen records",
    "d_rr": "NO_DIRECT_PATH: D reaches no RR term; the deficit D integrates also produces the acid burden, an explicit "
            "intermediate",
    "w_rr": "RETIRED_IN_CANDIDATE: the candidate RR reads no W channel; W is derived from RR and efficiency and feeds "
            "PaCO2 only (SEMANTIC_LEAK removed)",
}
#: The anchors' P2K-2 candidate inputs: in the arrival layers, outside the case-parameter / migration registry until
#: the faculty adopts the physiology (no GI migration is authorized); read only by the profile that declares it.
CANDIDATE_INPUTS = ("intrinsic_respiratory_rate", "arrival_bicarbonate", "arrival_paco2")
STATUS = {"bicarbonate_reference": "COMMON_REFERENCE_PROVISIONAL", "paco2_reference": "COMMON_REFERENCE_PROVISIONAL",
          "ventilation_efficiency": "STRUCTURAL_REFERENCE", "rr_drive_saturation": "STRUCTURAL_PROVISIONAL",
          "arrival_tolerance": "ARRIVAL_RR_TOLERANCE_PROVISIONAL", "hypoxaemic_drive": "HYPOXEMIC_DRIVE_DEFERRED",
          "lgn": "GENERALIZATION_PATH_RESERVED", "support": "FUTURE_GENERALIZATION_REQUIREMENT",
          "candidates": "EXPLORATORY", "approved": "none FACULTY_APPROVED"}
LGN = {"L": "C5 lung water / mechanics: no RR term; a future respiratory family may lower efficiency or load the drive",
       "G": "C6 gas exchange: no RR or SpO2 term; a future family may couple it to PaO2 / SpO2 and a hypoxaemic drive",
       "N": "C9 CNS depression: no RR term; a future family may scale the drive (depressants)"}
SUPPORT = {"fio2": "Oxygen sets FiO2, which moves SpO2 and, through delivery, the deficit, D, lactate and now the acid "
                   "burden; it touches no drive, RR or W directly",
           "niv": "NOT_MODELED", "invasive": "NOT_MODELED", "peep": "NOT_MODELED", "mode": "NOT_MODELED",
           "override": "NOT_A_GI_BLOCKER: no GI scenario ventilates; FUTURE_GENERALIZATION_REQUIREMENT for respiratory "
                       "families"}

# 3. The authored arrival blood gas -------------------------------------------------------------------------------------------

@functools.lru_cache(maxsize=None)
def _gas(case: str) -> tuple:
    text = gi_reference.authored(case, "abg")
    parts = dict(item.split(" ", 1) for item in text.split(" on ")[0].split(", "))
    return float(parts["pH"]), float(parts["PaCO2"]), float(parts["HCO3"]), float(parts["PaO2"])


def authored_gas(case: str) -> dict:
    """The arrival ABG as the case bank holds it: pH and PaCO2 authored, HCO3 the bank's own computation
    (clinical_cases._gas, rounded to 0.1), read from gi_reference's verified inventory."""
    ph, paco2, hco3, pao2 = _gas(case)
    return {"ph": ph, "paco2": paco2, "hco3": hco3, "pao2": pao2, "source": "gi_reference.INVENTORY (clinical_cases.py)"}


def arrival_burden(case: str, profile=DEFAULT_PROFILE) -> float:
    return max(0.0, profile.bicarbonate_reference_meq_l - authored_gas(case)["hco3"])


def ph_reconstruction(case: str) -> dict:
    gas = authored_gas(case)
    ph = dv.carbonic_ph(gas["hco3"], gas["paco2"])
    return {"authored_ph": gas["ph"], "derived_ph": ph, "error": ph - gas["ph"], "hco3": gas["hco3"],
            "paco2": gas["paco2"], "rounding": "HCO3 rounded to 0.1 by the bank: +/- 0.05 mEq/L is about +/- 0.0013 "
                                              "pH at these values"}


# 4. Predeclared exploratory candidates (P2K-2-1, P2K-2-3, P2K-2-4, P2K-2-12) -----------------------------------------------

INTRINSIC_RR = (12.0, 16.0, 20.0)
SATURATION = DEFAULT_PROFILE.rr_drive_saturation
ARRIVAL_TOLERANCE = 3.0
AUTHORED_RR = {C57: 26.0, C72: 24.0}
#: Exact-arrival drive gains: the gain that would reproduce each case's authored RR at each intrinsic RR. The candidate
#: range spans them on a geometric grid (ratio sqrt 2) from the power of two at or below the smallest to the power of
#: two at or above the largest: built before any compatibility is counted.
DRIVE_GAINS = (1.0, math.sqrt(2.0), 2.0, 2.0 * math.sqrt(2.0), 4.0)
#: The steady-state burden per unit of sustained effective deficit, B = deficit_to_acid_gain x tau (mEq/L per unit of
#: deficit). The arrival anchor: the burden the arrival deficit would hold at steady state equals the authored burden,
#: B = A0 / d0, at each case and demand (the carried region's arrival deficits); candidates = minimum, geometric mean
#: (to 0.1) and maximum of the four.
STEADY_BURDENS = (13.4, 19.4, 28.0)
#: Clearance time constants (min): no faster than 60 (no instantaneous normalization; the order of the debt and lactate
#: time constants), up to 240 (bicarbonate regeneration slower than lactate clearance).
ACID_TAUS = (60.0, 120.0, 240.0)
EFFICIENCY = 1.0
CANDIDATE_RULE = (
    "Predeclared before any clinical respiratory trajectory. Intrinsic RR: the faculty's 12 / 16 / 20, per patient. Drive "
    "gain: the exact-arrival solutions over both cases and the intrinsic support, spanned geometrically (1 to 4, ratio "
    "sqrt 2, five points), common to both cases. Acid production and clearance: the steady-state burden per unit of "
    "deficit B (k x tau) at the arrival anchor A0 / d0, three points, times three clearance constants 60 / 120 / 240 "
    "min; k = B / tau. Efficiency 1 (structural reference). 5 x 3 x 3 x 3 x 3 = 405 combinations, factorized: arrival "
    "compatibility reads (gain, intrinsic RR) analytically; the burden reads (B, tau) per deficit trajectory; RR, W, "
    "PaCO2 and pH are algebraic in the burden. No legacy RR, no outcome-chosen value.")


def exact_arrival_gains() -> dict:
    out = {}
    for case in CASES:
        burden = arrival_burden(case)
        for intrinsic in INTRINSIC_RR:
            rise = AUTHORED_RR[case] - intrinsic
            out[f"{case} {intrinsic:g}"] = -SATURATION * math.log(1.0 - rise / SATURATION) / burden
    return out


def drive_gain_support() -> tuple:
    gains = exact_arrival_gains().values()
    low, high = 2.0 ** math.floor(math.log2(min(gains))), 2.0 ** math.ceil(math.log2(max(gains)))
    steps = round(2 * math.log2(high / low))
    return tuple(low * 2.0 ** (i / 2) for i in range(steps + 1))


def arrival_deficits() -> dict:
    """The carried region's arrival effective deficit per case and demand: P2K-1's minute-0 share (deficit / demand,
    recorded under 'deficit') times the demand."""
    record = json.loads(P2K1_RECORD.read_text(encoding="utf-8"))
    out = {}
    for key, entry in record["reconstruction"].items():
        factor, _, _, case = key.split()
        share = entry["minutes"]["0"]["deficit"]
        if share["low"] != share["high"]:
            raise AssertionError("one arrival deficit per case and demand")
        out[f"{case} x{float(factor[1:]):g}"] = share["low"] * float(factor[1:])
    return out


def steady_burden_support() -> tuple:
    ratios = [arrival_burden(key.split()[0]) / d0 for key, d0 in arrival_deficits().items()]
    low, high = min(ratios), max(ratios)
    return (round(low, 1), round(math.sqrt(low * high), 1), round(high, 1))


def acid_pairs() -> tuple:
    return tuple((b, tau) for b in STEADY_BURDENS for tau in ACID_TAUS)


def candidate_profile(gain: float, b: float, tau: float, base=DEFAULT_PROFILE, **changes):
    return replace(base, **{"deficit_to_acid_gain": b / tau, "acid_clearance_tau_min": tau, "acid_to_drive_gain": gain,
                            "ventilation_efficiency": EFFICIENCY, **changes})


def arrival_rr(gain: float, intrinsic: float, case: str) -> float:
    return dv.rate_from_drive(gain * arrival_burden(case), intrinsic, DEFAULT_PROFILE)


def arrival_compatibility() -> dict:
    """(drive gain, intrinsic 57m, intrinsic 72f): the arrival RR of each case against its authored RR at the provisional
    +/- 3 tolerance; analytic, one common gain, patient-specific intrinsic RR, no residual."""
    rows, compatible = [], []
    for gain in DRIVE_GAINS:
        for i57 in INTRINSIC_RR:
            for i72 in INTRINSIC_RR:
                m57, m72 = arrival_rr(gain, i57, C57), arrival_rr(gain, i72, C72)
                ok = abs(m57 - AUTHORED_RR[C57]) <= ARRIVAL_TOLERANCE and abs(m72 - AUTHORED_RR[C72]) <= ARRIVAL_TOLERANCE
                rows.append({"gain": gain, "intrinsic": {C57: i57, C72: i72}, "rr": {C57: m57, C72: m72},
                             "mismatch": {C57: m57 - AUTHORED_RR[C57], C72: m72 - AUTHORED_RR[C72]},
                             "compatible": ok})
                if ok:
                    compatible.append((gain, i57, i72))
    return {"rows": rows, "compatible": compatible, "count": len(compatible), "of": len(rows)}


ANALYTIC_REJECTION, SIMULATION_REJECTION = "ANALYTIC_REJECTION", "SIMULATION_REJECTION"


def analytic_rejections(gain: float, intrinsic: float, b: float, tau: float, d_max: float, case: str) -> list:
    """Reasons a combination is impossible before any simulation: the burden is bounded by max(A0, B x d_max), so
    HCO3 >= HCO3_ref - that bound; a negative drive gain, a non-positive intrinsic RR, an intrinsic RR whose saturated
    ceiling the safety guard would clip, or a clearance under one step."""
    out = []
    if gain < 0.0:
        out.append("negative respiratory drive")
    if not intrinsic > 0.0:
        out.append("invalid intrinsic RR")
    if intrinsic + SATURATION > DEFAULT_PROFILE.rr_max:
        out.append("RR saturation above the safety guard")
    if tau < 1.0 or b < 0.0:
        out.append("negative acid burden")
    if DEFAULT_PROFILE.bicarbonate_reference_meq_l - max(arrival_burden(case), b * d_max) <= 0.0:
        out.append("non-positive HCO3")
    return out


# 5. Structural probes A-H (P2K-2-6, P2K-2-8) ----------------------------------------------------------------------------

PROBE_GAS = {"arrival_bicarbonate": 20.0, "arrival_paco2": 36.0, "intrinsic_respiratory_rate": 16.0}
PROBE_ANCHORS = replace(vt.NEUTRAL, **PROBE_GAS)
PROBE_PROFILE = candidate_profile(2.0, 19.4, 120.0, base=replace(DEFAULT_PROFILE, oxygen_extraction_reserve=RESERVE))
PROBE_RULE = (
    "Synthetic, structural only, on the neutral probe arrival (no deficit) with a declared arrival gas (HCO3 20, PaCO2 36, "
    "intrinsic RR 16) and the probe profile (gain 2, B 19.4, tau 120, efficiency 1). A: burden 4 -> 8, oxygenation "
    "normal. B: lactate alone raised, burden fixed. C: D alone raised, burden fixed. D: 60 min with no deficit, lactate "
    "clearance slowed to 600 min: the burden clears, lactate stays high. E1: efficiency 0.5 in the core at a raised "
    "burden; E2: the core's functions with efficiency falling 1 -> 0.5 while the burden rises. F: CO2 production down "
    "(demand ratio 0.8), burden fixed. G: CO2 production up (1.25), burden fixed. H: pH from HCO3 and PaCO2 at fixed "
    "states. W channel: state W 0 -> +0.5 and -0.5 at a fixed burden. No number here is a candidate or a clinical value.")


def _probe_state(burden=None, **changes):
    state = arrival_state(PROBE_ANCHORS, PROBE_PROFILE)
    aux = state.aux if burden is None else replace(state.aux, metabolic_acid_burden=burden)
    for name in ("lactate_excess_mmol_l", "oxygen_demand"):
        if name in changes:
            aux = replace(aux, **{name: changes.pop(name)})
    return state.evolve(aux=aux, **changes)


def _resp(state, profile=PROBE_PROFILE) -> dict:
    r = respiration(state, PROBE_ANCHORS, profile)
    return {"burden": r.acid_burden, "hco3": r.bicarbonate, "drive": r.drive, "rr": r.respiratory_rate,
            "w": r.ventilation, "paco2": r.paco2, "ph": r.ph, "core_rr": derive(state, PROBE_ANCHORS, profile).respiratory_rate,
            "lactate": derive(state, PROBE_ANCHORS, profile).lactate, "D": state.D}


def probes() -> dict:
    base = _resp(_probe_state())
    a = _resp(_probe_state(8.0))
    b = _resp(_probe_state(lactate_excess_mmol_l=4.0))
    c = _resp(_probe_state(D=40.0))
    slow = replace(PROBE_PROFILE, lactate_clearance_tau_min=600.0)
    state = _probe_state(8.0, lactate_excess_mmol_l=4.0)
    start = _resp(state, slow)
    for _ in range(60):
        state, _ = step(state, (), PROBE_ANCHORS, slow)
    d_end = _resp(state, slow)
    weak = replace(PROBE_PROFILE, ventilation_efficiency=0.5)
    e1 = _resp(_probe_state(8.0), weak)
    # E2: the core's own functions, efficiency falling from 1 to 0.5 over 20 min while the burden rises 4 -> 10.
    intrinsic = dv.intrinsic_respiratory_rate(PROBE_ANCHORS)
    rest = dv.arrival_paco2(PROBE_ANCHORS, PROBE_PROFILE) * dv.arrival_alveolar_ventilation(PROBE_ANCHORS, PROBE_PROFILE)
    course = []
    for minute in range(21):
        burden, efficiency = 4.0 + 0.3 * minute, 1.0 - 0.025 * minute
        rate = dv.rate_from_drive(dv.respiratory_drive(burden, PROBE_PROFILE), intrinsic, PROBE_PROFILE)
        w = dv.alveolar_ventilation(rate, intrinsic, efficiency, 1.0)
        course.append({"minute": minute, "burden": burden, "efficiency": efficiency, "rr": rate, "w": w,
                       "paco2": rest / w})
    f = _resp(_probe_state(oxygen_demand=0.8))
    g = _resp(_probe_state(oxygen_demand=1.25))
    h_acid = _resp(_probe_state(10.0))
    w_up, w_down = _resp(_probe_state(W=0.5)), _resp(_probe_state(W=-0.5))
    h_low = dv.carbonic_ph(base["hco3"], base["paco2"] * 0.8)
    return {
        "rule": PROBE_RULE, "base": base,
        "A": {"result": a, "drive_rises": a["drive"] > base["drive"], "rr_rises": a["rr"] > base["rr"],
              "deficit": 0.0},
        "B": {"result": b, "rr_unchanged": b["rr"] == base["rr"] and b["core_rr"] == base["core_rr"],
              "lactate_raised": b["lactate"] > base["lactate"]},
        "C": {"result": c, "rr_unchanged": c["rr"] == base["rr"] and c["core_rr"] == base["core_rr"]},
        "D": {"start": start, "end": d_end, "burden_falls": d_end["burden"] < start["burden"],
              "rr_falls": d_end["rr"] < start["rr"], "lactate_stays_high": d_end["lactate"] > base["lactate"] + 2.0},
        "E1": {"result": e1, "w_at_most_1": e1["w"] <= 1.0, "rr_above_intrinsic": e1["rr"] > intrinsic,
               "paco2_above_arrival": e1["paco2"] > PROBE_GAS["arrival_paco2"]},
        "E2": {"course": course, "paco2_rises": course[-1]["paco2"] > course[0]["paco2"],
               "rr_rises": course[-1]["rr"] > course[0]["rr"], "w_falls_below_1": course[-1]["w"] < 1.0},
        "F": {"result": f, "w_rises": f["w"] > base["w"], "paco2_falls": f["paco2"] < base["paco2"],
              "rr_unchanged": f["rr"] == base["rr"]},
        "G": {"result": g, "w_falls": g["w"] < base["w"], "paco2_rises": g["paco2"] > base["paco2"]},
        "H": {"acid_up": h_acid, "ph_formula": abs(h_acid["ph"] - dv.carbonic_ph(h_acid["hco3"], h_acid["paco2"])) < 1e-12,
              "more_acid_lower_ph": h_acid["ph"] < base["ph"], "lower_paco2_higher_ph": h_low > base["ph"],
              "arrival_exact": abs(base["paco2"] - PROBE_GAS["arrival_paco2"]) < 1e-9},
        "W_channel": {"rr_unchanged": w_up["rr"] == base["rr"] == w_down["rr"] and w_up["core_rr"] == base["core_rr"]},
    }


# 6. The clinical scenarios R1-R4, factorized (P2K-2-10) -----------------------------------------------------------------------

R_SCENARIOS = ra.R_SCENARIOS
MINUTES_REPORTED = ra.MINUTES_REPORTED
RECONSTRUCTION_RULE = (
    "Every unique (scenario, blood set, lactate-side point) of the carried P2J-3 region at its demand and tone gain, as "
    "P2K-1 rebuilt it (vascular_tone.rebuild and debt_and_lactate): the effective deficit, D and lactate per minute. "
    "The burden is integrated from the deficit with the core's own acid_burden_after_minute for each (B, tau); RR, W, "
    "PaCO2 and pH are the core's algebra of the burden at each (gain, intrinsic RR). Validated against full core runs "
    "with the candidate declared, where every upstream row also equals the run without it. The P2K-1 RR of the same "
    "trajectories, recomputed, equals the P2K-1 record (default-profile non-regression).")


def unit_trajectory(blood: dict, case: str, lam: int, factor: float, gain: float, arrivals: dict) -> dict:
    """rr_audit.trajectory's reconstruction, with the effective deficit and the intervention state kept."""
    anchors = vt.tone_anchors(case, vt.level_of(lam), factor)
    rebuilt = vt.rebuild(blood, anchors, gain, AFTERLOAD)
    series = vt.debt_and_lactate(blood, rebuilt, case, lam, factor, arrivals)
    rows = rebuilt["rows"]
    n = len(rows)
    return {"rr": [ra.rr_from_lactate(anchors, series["lactate"][m], blood["pulse"][m]) for m in range(n)],
            "lactate": list(series["lactate"][:n]), "D": list(series["D"][:n]), "s": [row["s"] for row in rows],
            "metabolic": [dv._metabolic_drive(x, DEFAULT_PROFILE) for x in series["lactate"][:n]],
            "ventilatory": ra._ventilatory_part(anchors), "controlled_at": blood["controlled_at"],
            "stop": rebuilt["stop"], "deficit": [row["deficit"] for row in rows], "pulse": list(blood["pulse"][:n]),
            "crystalloid": list(blood["crystalloid"][:n]), "prbc": list(blood["prbc"][:n])}


def reconstruct(region: dict, arrivals: dict) -> dict:
    out = {}
    for (gain, factor), survivors in sorted(region["survivors"].items()):
        for name in ("P1", "P2", "P3", "P4"):
            for case, position in ((C57, 1), (C72, 2)):
                seen = {}
                for survivor in survivors:
                    lam = survivor[position]
                    key = (ra._blood_key(name, case, survivor), lam)
                    if key not in seen:
                        seen[key] = (survivor, unit_trajectory(region["bloods"][key[0]], case, lam, factor, gain,
                                                               arrivals))
                out[(gain, factor, name, case)] = seen
    return out


def burden_series(deficit: list, a0: float, b: float, tau: float) -> list:
    profile = candidate_profile(1.0, b, tau)
    series = [a0]
    for d in deficit[:-1]:
        series.append(dv.acid_burden_after_minute(series[-1], d, profile))
    return series


def _gas_at(burden: float, gain: float, intrinsic: float, case: str, rest: float, pulse: bool = True) -> dict:
    drive = gain * burden
    rate = dv.rate_from_drive(drive, intrinsic, DEFAULT_PROFILE) if pulse else 0.0
    w = dv.alveolar_ventilation(rate, intrinsic, EFFICIENCY, 1.0)
    hco3 = _gas(case)[2] - (burden - arrival_burden(case))
    paco2 = rest / w if w > 0.0 else None
    return {"burden": burden, "hco3": hco3, "drive": drive, "rr": rate, "w": w, "paco2": paco2,
            "ph": dv.carbonic_ph(hco3, paco2) if paco2 and hco3 > 0.0 else None}


def resting_paco2(gain: float, intrinsic: float, case: str) -> float:
    w0 = dv.alveolar_ventilation(arrival_rr(gain, intrinsic, case), intrinsic, EFFICIENCY, 1.0)
    return authored_gas(case)["paco2"] * w0


def _spread(values) -> dict:
    values = sorted(v for v in values if v is not None)
    if not values:
        return {"n": 0}
    n = len(values)
    median = values[n // 2] if n % 2 else (values[n // 2 - 1] + values[n // 2]) / 2
    return {"n": n, "low": values[0], "median": median, "high": values[-1]}


def _intervention(t: dict, minute: int) -> dict:
    return {"crystalloid_ml": t["crystalloid"][minute], "prbc_units": t["prbc"][minute],
            "haemostasis": t["controlled_at"] is not None and minute >= t["controlled_at"]}


class _Tally:
    """The key questions, read combination by combination without keeping the trajectories."""

    def __init__(self):
        self.counts, self.values = {}, {}

    def count(self, name: str, ok: bool) -> None:
        n, true = self.counts.get(name, (0, 0))
        self.counts[name] = (n + 1, true + (1 if ok else 0))

    def add(self, name: str, value: float) -> None:
        self.values.setdefault(name, []).append(value)

    def share(self, name: str) -> dict:
        n, true = self.counts.get(name, (0, 0))
        return {"n": n, "true": true}

    def spread(self, name: str) -> dict:
        return _spread(self.values.get(name, []))


def _read(tally: _Tally, name: str, case: str, t: dict, series: list, b: float, tau: float, gain: float,
          intrinsic: float, rest: float) -> None:
    n = len(series)
    rr = [dv.rate_from_drive(gain * x, intrinsic, DEFAULT_PROFILE) for x in series]
    if name == "P1":
        rising = all(y >= x - 1e-12 for x, y in zip(series, series[1:]))
        for key in ("r1", f"r1 {b:g}/{tau:g}", f"r1 {case}"):
            tally.count(key, rising)
        tally.count("r1_120_at_or_above_arrival", series[min(120, n - 1)] >= series[0] - 1e-12)
        if case == C72:
            dip = rr[0] - min(rr[:31])
            tally.count("dip", dip > 1e-9)
            tally.count(f"dip {b:g}", dip > 1e-9)
            tally.add("dip_depth", dip)
    lactate = t["lactate"][:n]
    tally.count("opposite", any((lactate[m] - lactate[m - 1]) * (rr[m] - rr[m - 1]) < -1e-12 for m in range(1, n)))
    if name == "P4":
        last = min(120, n - 1)
        tally.add("rr_120_above_intrinsic", rr[last] - intrinsic)
        tally.add("rest_paco2", rest)
        tally.add("paco2_120_below_rest", rest - rest / dv.alveolar_ventilation(rr[last], intrinsic, EFFICIENCY, 1.0))
        tally.add("max_rr_step", max(abs(y - x) for x, y in zip(rr, rr[1:])) if n > 1 else 0.0)
        h = t["controlled_at"]
        if h is not None and h + 1 < n:
            steps = [abs(y - x) for x, y in zip(rr, rr[1:])]
            tally.count("haemostasis_step", steps[h] <= max(steps[:h] + steps[h + 1:]))
            above = rr[min(h + 15, n - 1)] - intrinsic
            tally.add("rr_15_after_haemostasis_above_intrinsic", above)
            tally.count("no_instant_normalization", above >= 1.0)


def evaluate(store: dict, compatible: list) -> dict:
    """Per (tone gain, demand, scenario, case): the burden per (B, tau) and the respiratory algebra per compatible
    (gain, intrinsic RR), at the reported minutes and at each trajectory's burden extremes; the key questions tallied."""
    per_case = {C57: sorted({(g, i57) for g, i57, _ in compatible}), C72: sorted({(g, i72) for g, _, i72 in compatible})}
    tables, tally, rejections = {}, _Tally(), {ANALYTIC_REJECTION: 0, SIMULATION_REJECTION: 0}
    for (tgain, factor, name, case), seen in sorted(store.items(), key=lambda kv: str(kv[0])):
        key = f"x{factor:g} g{tgain:g} {name} {case}"
        a0 = arrival_burden(case)
        cells = {str(m): {q: [] for q in ("rr", "drive", "burden", "hco3", "w", "paco2", "ph")} for m in MINUTES_REPORTED}
        upstream = {str(m): {q: [] for q in ("lactate", "D", "deficit", "crystalloid_ml", "prbc_units")}
                    for m in MINUTES_REPORTED}
        haemostasis = {str(m): 0 for m in MINUTES_REPORTED}
        summary = {q: [] for q in ("rr_peak", "rr_120", "rr_min", "ph_low", "ph_high", "paco2_120", "burden_peak",
                                   "burden_120", "max_one_minute_burden_fall", "rr_change_0_30")}
        for _, t in seen.values():
            n = len(t["deficit"])
            for m in MINUTES_REPORTED:
                if m < n:
                    row = upstream[str(m)]
                    row["lactate"].append(t["lactate"][m])
                    row["D"].append(t["D"][m])
                    row["deficit"].append(t["deficit"][m])
                    row["crystalloid_ml"].append(t["crystalloid"][m])
                    row["prbc_units"].append(t["prbc"][m])
                    haemostasis[str(m)] += 1 if t["controlled_at"] is not None and m >= t["controlled_at"] else 0
            d_max = max(t["deficit"])
            for b, tau in acid_pairs():
                series = burden_series(t["deficit"], a0, b, tau)
                for gain, intrinsic in per_case[case]:
                    if analytic_rejections(gain, intrinsic, b, tau, d_max, case):
                        rejections[ANALYTIC_REJECTION] += 1
                        continue
                    rest = resting_paco2(gain, intrinsic, case)
                    points = {m: _gas_at(series[m], gain, intrinsic, case, rest, t["pulse"][m])
                              for m in MINUTES_REPORTED if m < n}
                    extremes = [_gas_at(x, gain, intrinsic, case, rest) for x in (min(series), max(series))]
                    if any(p["hco3"] <= 0.0 or (p["paco2"] is not None and p["paco2"] <= 0.0) for p in
                           list(points.values()) + extremes):
                        rejections[SIMULATION_REJECTION] += 1
                        continue
                    for m, p in points.items():
                        for q in cells[str(m)]:
                            cells[str(m)][q].append(p[q])
                    phs = [p["ph"] for p in list(points.values()) + extremes if p["ph"] is not None]
                    summary["rr_peak"].append(extremes[1]["rr"])
                    summary["rr_min"].append(extremes[0]["rr"])
                    summary["burden_peak"].append(max(series))
                    summary["max_one_minute_burden_fall"].append(max([0.0] + [x - y for x, y in zip(series, series[1:])]))
                    summary["ph_low"].append(min(phs))
                    summary["ph_high"].append(max(phs))
                    if 120 < n:
                        summary["rr_120"].append(points[120]["rr"])
                        summary["paco2_120"].append(points[120]["paco2"])
                        summary["burden_120"].append(series[120])
                    if 30 < n:
                        summary["rr_change_0_30"].append(points[30]["rr"] - points[0]["rr"])
                    _read(tally, name, case, t, series, b, tau, gain, intrinsic, rest)
        tables[key] = {"trajectories": len(seen),
                       "minutes": {m: {q: _spread(v) for q, v in cells[m].items()} for m in cells},
                       "upstream": {m: {q: _spread(v) for q, v in upstream[m].items()} for m in upstream},
                       "haemostasis": haemostasis, "summary": {q: _spread(v) for q, v in summary.items()},
                       "efficiency": EFFICIENCY, "intrinsic": sorted({i for _, i in per_case[case]}),
                       "gains": sorted({g for g, _ in per_case[case]})}
    return {"tables": tables, "tally": tally, "rejections": rejections}


# 7. Validation against the core, upstream non-regression ----------------------------------------------------------------------

VALIDATION_CANDIDATE = (2.0, 16.0, 16.0, 19.4, 120.0)


def _run_states(entry, case, scenario, factor, point, bag, profile_changes, gas=None) -> dict:
    """pressure_tone.full_run's construction, keeping the states, with the case's arrival gas and an intrinsic RR
    declared when ``gas`` is given."""
    tau_d, gain_k, k, tau_l, excess, debt, delivery = point
    values = {**lr.blood_values(entry, case, bag), "reserve": RESERVE}
    _, profile, full = blood_anchors.setup(case, **values)
    case_values = calibration.case_values(case, calibration.GICandidate({}, excess=excess, debt=debt,
                                                                        delivery=delivery, intrinsic="midpoint"))
    case_values["preload_fraction"] = full[pt.bc.POS]
    case_values["arrival_delivery_ratio"] /= RESERVE
    case_values["metabolic_demand_baseline"] *= factor
    anchors = gi_reference.candidate_anchors(case, case_values)
    if gas is not None:
        anchors = replace(anchors, arrival_bicarbonate=gas["hco3"], arrival_paco2=gas["paco2"],
                          intrinsic_respiratory_rate=gas["intrinsic"])
    profile = replace(profile, debt_clearance_tau_min=tau_d, debt_per_delivery_deficit=gain_k, debt_to_lactate_gain=k,
                      lactate_clearance_tau_min=tau_l, **profile_changes)
    states, stop = blood_anchors.trajectory(anchors, pt.scenario_items(case, scenario, full), pt.MINUTES, profile)
    return {"states": states, "anchors": anchors, "profile": profile, "rows": pt._rows(states, anchors, profile, full),
            "stop": stop}


def _upstream(state) -> dict:
    """The whole state but the acid burden: every channel, the rhythm, the blood state, every other auxiliary value."""
    data = state.to_dict()
    data["aux"] = {k: v for k, v in data["aux"].items() if k != "metabolic_acid_burden"}
    return data


def validate(region: dict, store: dict) -> dict:
    """One full core run per (tone gain, demand, scenario, case) with the validation candidate declared, and the same run
    without it: the burden, RR, W, PaCO2 and pH equal the factorized reconstruction, and every upstream row (output,
    pressure, tone, delivery, demand, D, lactate, HR, blood) equals the run without the candidate."""
    gain, i57, i72, b, tau = VALIDATION_CANDIDATE
    compared, equal, upstream_equal, max_diff, default_rr = 0, True, True, 0.0, True
    for (tgain, factor, name, case), seen in sorted(store.items(), key=lambda kv: str(kv[0])):
        if not seen:
            continue
        (_, lam), (survivor, traj) = sorted(seen.items(), key=lambda kv: str(kv[0]))[0]
        entry, bag = ra._entry(name, survivor, region["source"], region["support"])
        intrinsic = i57 if case == C57 else i72
        gas = {**authored_gas(case), "intrinsic": intrinsic}
        tone = {"deficit_to_tone_gain": tgain, "afterload_sensitivity": AFTERLOAD}
        plain = _run_states(entry, case, pt.SCENARIOS[name], factor, LAMBDAS[lam], bag, tone)
        live = _run_states(entry, case, pt.SCENARIOS[name], factor, LAMBDAS[lam], bag,
                           {**tone, "deficit_to_acid_gain": b / tau, "acid_clearance_tau_min": tau,
                            "acid_to_drive_gain": gain, "ventilation_efficiency": EFFICIENCY}, gas)
        compared += 1
        # The default profile's RR through derive equals the P2K-1 RR of the same trajectory (review: p2k1_unchanged
        # reads respiratory_rate directly, so derive itself is compared here).
        default_rr = default_rr and [row["rr"] for row in plain["rows"]] == traj["rr"][:len(plain["rows"])]
        series = burden_series(traj["deficit"], arrival_burden(case), b, tau)
        rest = resting_paco2(gain, intrinsic, case)
        for m, state in enumerate(live["states"]):
            r = respiration(state, live["anchors"], live["profile"])
            want = _gas_at(series[m], gain, intrinsic, case, rest, state.R.pulse_present)
            for got, exp in ((r.acid_burden, want["burden"]), (r.respiratory_rate, want["rr"]),
                             (r.ventilation, want["w"]), (r.paco2, want["paco2"]), (r.ph, want["ph"]),
                             (r.bicarbonate, want["hco3"])):
                if got is None or exp is None:
                    equal = equal and got is exp
                    continue
                max_diff = max(max_diff, abs(got - exp))
            equal = equal and live["rows"][m]["rr"] == r.respiratory_rate
        upstream_equal = upstream_equal and len(plain["rows"]) == len(live["rows"]) and all(
            {k: v for k, v in p.items() if k != "rr"} == {k: v for k, v in q.items() if k != "rr"}
            for p, q in zip(plain["rows"], live["rows"])) and all(
            _upstream(s) == _upstream(t) for s, t in zip(plain["states"], live["states"]))
        equal = equal and len(series) >= len(live["states"])
    return {"compared": compared, "equal": equal and max_diff <= 1e-9, "max_abs_diff": max_diff,
            "upstream_equal": upstream_equal, "default_rr_equal": default_rr, "candidate": list(VALIDATION_CANDIDATE)}


def p2k1_unchanged(store: dict) -> bool:
    """The P2K-1 RR, D, lactate and deficit share of the same trajectories, recomputed on the live (default) core, equal
    the P2K-1 record."""
    record = json.loads(P2K1_RECORD.read_text(encoding="utf-8"))
    return json.loads(json.dumps(ra.summarize(store))) == record["reconstruction"]


# 8. Key questions, dependencies, identifiability, readiness (P2K-2-11 to P2K-2-16) ------------------------------------------

def key_questions(evaluated: dict, probes_: dict) -> dict:
    tally = evaluated["tally"]
    return {
        "1_untreated_acid_and_drive": {
            "burden_non_decreasing": tally.share("r1"),
            "burden_120_at_or_above_arrival": tally.share("r1_120_at_or_above_arrival"),
            "by_pair": {f"{b:g}/{tau:g}": tally.share(f"r1 {b:g}/{tau:g}") for b, tau in acid_pairs()},
            "by_case": {case: tally.share(f"r1 {case}") for case in CASES}},
        "2_72f_early_dip": {"dip": tally.share("dip"), "by_b": {f"{b:g}": tally.share(f"dip {b:g}")
                                                                for b in STEADY_BURDENS},
                            "depth": tally.spread("dip_depth"),
                            "mechanism": "acid clearance A0 / tau above production B / tau x d0 at the arrival deficit "
                                         "(B x d0 < A0); never lactate"},
        "3_post_resuscitation": {
            "max_rr_step": tally.spread("max_rr_step"),
            "rr_120_above_intrinsic": tally.spread("rr_120_above_intrinsic"),
            "rest_paco2": tally.spread("rest_paco2"),
            "paco2_120_below_rest": tally.spread("paco2_120_below_rest"),
            "haemostasis_step_vs_others": tally.share("haemostasis_step"),
            "rr_15_after_haemostasis_above_intrinsic": tally.spread("rr_15_after_haemostasis_above_intrinsic"),
            "no_instant_normalization": tally.share("no_instant_normalization")},
        "4_lactate_rr_opposite": tally.share("opposite"),
        "5_rr_w_dissociation": {"E1_w_at_most_1": probes_["E1"]["w_at_most_1"],
                                "E2_paco2_rises_despite_tachypnoea": probes_["E2"]["paco2_rises"]
                                and probes_["E2"]["rr_rises"]},
    }


def dependencies(store: dict, evaluated: dict) -> dict:
    """Which upstream uncertainty reaches the new physiology: demand and tone gain through the deficit; MAP_set, the
    baroreflex and the HR latent region have no path (they move only the sympathetic drive and HR, which no deficit,
    burden, drive or RR term reads; P2J-4: every non-HR row equal with the baroreflex on and off)."""
    by = {}
    for key, table in evaluated["tables"].items():
        factor, tgain, name, case = key.split()
        by.setdefault((factor, name, case), {})[tgain] = table["minutes"]["120"]["burden"].get("median")
    tone = [max(v.values()) - min(v.values()) for v in by.values() if len(v) > 1 and None not in v.values()]
    demand = {}
    for key, table in evaluated["tables"].items():
        factor, tgain, name, case = key.split()
        demand.setdefault((tgain, name, case), {})[factor] = table["minutes"]["120"]["burden"].get("median")
    demand_diff = [abs(v["x1.1"] - v["x1"]) for v in demand.values() if {"x1", "x1.1"} <= set(v) and None not in v.values()]
    return {"demand": {"path": "demand -> effective deficit -> acid burden -> drive -> RR / W / PaCO2 / pH",
                       "median_burden_120_difference": _spread(demand_diff)},
            "tone_gain": {"path": "g -> T -> output -> delivery -> deficit -> acid burden",
                          "median_burden_120_spread": _spread(tone)},
            "map_set": {"path": "NONE", "proof": "P2J-4 rows_equal (654 units): the baroreflex moves only the "
                                                 "sympathetic drive; no deficit, burden or RR term reads it"},
            "baroreflex_gain": {"path": "NONE", "proof": "as MAP_set"},
            "hr_latent": {"path": "NONE", "proof": "HR reaches no output, delivery, deficit, D, lactate or burden "
                                                   "(P2I-2AG, P2J-1)"},
            "multiplied": ["demand", "tone_gain"]}


IDENTIFIABILITY_CLASSES = ("WELL_CONSTRAINED", "PARTIALLY_CONSTRAINED", "POORLY_IDENTIFIED", "NON_IDENTIFIABLE")
IDENTIFIABILITY_RULE = (
    "Frozen. Arrival compatibility (+/- 3, provisional) is the only authored respiratory constraint besides the arrival "
    "gas: a quantity is WELL_CONSTRAINED when one value is compatible, PARTIALLY_CONSTRAINED when some but not all are, "
    "NON_IDENTIFIABLE when every value is or the arrival does not read it; the arrival burden is exact from the authored "
    "HCO3. B and tau reach only trajectories with no authored later observation: NON_IDENTIFIABLE from authored data, "
    "their trajectory sensitivity reported. The implied resting PaCO2 is reported, never filtered. No best set.")


def _class(values, support) -> str:
    values = set(values)
    if not values or values == set(support):
        return "NON_IDENTIFIABLE"
    return "WELL_CONSTRAINED" if len(values) == 1 else "PARTIALLY_CONSTRAINED"


def identifiability(compat: dict) -> dict:
    ok = compat["compatible"]
    rest = {case: _spread([resting_paco2(g, i57 if case == C57 else i72, case) for g, i57, i72 in ok]) for case in CASES}
    return {
        "intrinsic_rr_57m": {"class": _class([c[1] for c in ok], INTRINSIC_RR), "values": sorted({c[1] for c in ok})},
        "intrinsic_rr_72f": {"class": _class([c[2] for c in ok], INTRINSIC_RR), "values": sorted({c[2] for c in ok})},
        "acid_to_drive_gain": {"class": _class([c[0] for c in ok], DRIVE_GAINS), "values": sorted({c[0] for c in ok})},
        "deficit_to_acid_gain": {"class": "NON_IDENTIFIABLE", "why": "no authored observation after arrival"},
        "acid_clearance_tau": {"class": "NON_IDENTIFIABLE", "why": "no authored observation after arrival"},
        "acid_burden": {"class": "WELL_CONSTRAINED", "why": "at arrival, exact from the authored HCO3; after arrival it "
                                                            "follows (B, tau), which nothing authored reads"},
        "w_efficiency": {"class": "NON_IDENTIFIABLE", "why": "efficiency fixed at the structural reference 1 and read by "
                                                            "no authored observation (review: the frozen rule); W's "
                                                            "absolute scale and the resting PaCO2 follow the intrinsic "
                                                            "RR, itself constrained only jointly with the gain",
                         "resting_paco2": rest},
        "rule": IDENTIFIABILITY_RULE}


READY = "ACID_BASE_RR_STRUCTURE_READY_FOR_NUMERIC_FACULTY_CALIBRATION"
NOT_READY = "ACID_BASE_RR_STRUCTURE_NOT_READY"
CRITERIA = ("acid_burden_causal", "lactate_retired", "d_not_direct", "distinct_drive_rr_w", "paco2_ph_coherent",
            "rr_w_dissociation", "patient_like", "no_upstream_regression", "bounded_surface", "nothing_approved")
VERDICT_RULE = (
    "Frozen. READY when every criterion holds: the burden is an explicit state driving RR (probe A), lactate and D reach "
    "no candidate RR term (probes B, C, the W channel), drive, RR and W are distinct (E1, E2, F), PaCO2 and pH are "
    "coherent (F, G, H, the arrival reconstruction), the RR / W dissociation works (E1, E2), the trajectories are "
    "patient-like (for some predeclared (B, tau) the untreated burden never falls in any R1 trajectory of either case; "
    "in every R4 trajectory RR stays at least 1 breath/min above intrinsic 15 min after haemostasis and the haemostasis "
    "minute moves RR no more than another minute), the upstream rows are identical and the core "
    "reproduces the reconstruction, a bounded candidate surface exists (at least one arrival-compatible common "
    "candidate) and nothing is approved. Otherwise NOT_READY with the first failing criterion as the blocker.")


def verdict(checks: dict) -> dict:
    failing = [name for name in CRITERIA if not checks[name]]
    return {"verdict": READY if not failing else f"{NOT_READY} - {failing[0].upper()}", "checks": checks,
            "failing": failing}


DECISION_PACK = ("arrival RR compatibility (per gain and intrinsic RR, +/- 3 provisional)", "untreated RR at 120 (R1)",
                 "RR after crystalloid (R2)", "RR after PRBC without haemostasis (R3)",
                 "RR after definitive resuscitation (R4)", "HCO3 / pH / PaCO2 trajectories (R1-R4)",
                 "implied resting PaCO2 per intrinsic RR")
POLICY = ("Shadow only. The acid-base physiology is in the core and off by default; the candidate is the profile with "
          "its three gains declared. Candidates predeclared and exploratory; nothing selected or approved; no RR "
          "envelope filters anything (ANALYTIC_REJECTION and SIMULATION_REJECTION mark only impossible values: HCO3 "
          "or PaCO2 not positive). The P2J-3 region recomputed through P2J-4's machinery; legacy RR never read.")


# 9. P2K-2's insertions into the core, proven (closure of the closed packages) --------------------------------------------------

DERIVED, INTEGRATION, STATE = "clinical_core/derived.py", "clinical_core/integration.py", "clinical_core/state.py"
CORE_FILES = (DERIVED, INTEGRATION, STATE)
#: Every identifier P2K-2 put in the core: fields, parameters, functions, the aux field and the source.
P2K2_NAMES = frozenset({
    "ACID_BASE", "metabolic_acid_burden", "bicarbonate_reference_meq_l", "paco2_reference_mmhg", "deficit_to_acid_gain",
    "acid_clearance_tau_min", "acid_to_drive_gain", "rr_drive_saturation", "ventilation_efficiency", "CARBONIC_PK",
    "CO2_SOLUBILITY", "acid_base_active", "arrival_bicarbonate", "arrival_acid_burden", "arrival_paco2",
    "intrinsic_respiratory_rate", "acid_burden_after_minute", "respiratory_drive", "rate_from_drive",
    "alveolar_ventilation", "bicarbonate", "carbonic_ph", "arrival_alveolar_ventilation", "Respiration", "respiration",
    "respiratory_rate_decomposition", "_acid_burden", "REFERENCE_VENTILATION_EFFICIENCY"})
#: The statements that existed before P2K-2 and that it changed, only by inserting what names P2K2_NAMES.
P2K2_CHANGED = {DERIVED: ("CoreProfile", "PARAMETERS", "arrival_state", "check_arrival_reconstruction", "derive"),
                INTEGRATION: ("from .derived", "step"),
                STATE: ("ARRIVAL_LAYERS", "Anchors", "AUXILIARY_FIELDS", "AuxiliaryState")}
#: The top-level statements P2K-2 added (none in state.py), and the one keyed entry it appended to AUXILIARY_SOURCES.
P2K2_NEW = {DERIVED: ("ACID_BASE", "CARBONIC_PK", "CO2_SOLUBILITY", "acid_base_active", "arrival_bicarbonate",
                      "arrival_acid_burden", "arrival_paco2", "intrinsic_respiratory_rate", "acid_burden_after_minute",
                      "respiratory_drive", "rate_from_drive", "alveolar_ventilation", "bicarbonate", "carbonic_ph",
                      "arrival_alveolar_ventilation", "Respiration", "respiration", "respiratory_rate_decomposition",
                      "REFERENCE_VENTILATION_EFFICIENCY"),
            INTEGRATION: ("_acid_burden",), STATE: ()}
P2K2_KEYED = {DERIVED: ("AUXILIARY_SOURCES", "metabolic_acid_burden")}
#: What P2K-2 inserted in each file, its AST digest (``insertions_digest``) as frozen after the adversarial review.
INSERTIONS_AT_P2K2 = {DERIVED: "f24467d418473740459bdec14de1c2d72046f1db65a98301cb4734d7a81e75a6",
                      INTEGRATION: "37f5b725a4de9cca5e417fb5fbf5b75b71f4d740b28c6119d5658f7cd5c31da6",
                      STATE: "a40b09886a578f14201d9f54ae96d8d52eec57f677fb2cabd7a3718b211c1240"}
#: The three files at P2K-1 (81ed6b8, P2J-4's core): their hashes and the AST digest of every top-level statement.
CORE_AT_P2K1 = dict(ra.CORE_AT_P2J4)
WHOLE_AT_P2K1 = {DERIVED: "9403bacd4e6ca4a1e9e777e03782e45d35c5147643c0ff83dafc1527b8a64d63",
                 INTEGRATION: "097843018a1c3753c3dc9583482d369a185b72f1b66065ce2b04e3316a2a4ea9",
                 STATE: "382eaed9cef2b58186afa762f8b258d5dfa0c87c9f0ea234aaacd786b24afabc"}


def _mentions(node) -> bool:
    for n in ast.walk(node):
        if (isinstance(n, ast.Name) and n.id in P2K2_NAMES) or (isinstance(n, ast.Attribute) and n.attr in P2K2_NAMES) \
                or (isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value in P2K2_NAMES) \
                or (isinstance(n, ast.keyword) and n.arg in P2K2_NAMES) \
                or (isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in P2K2_NAMES) \
                or (isinstance(n, ast.alias) and n.name in P2K2_NAMES):
            return True
    return False


class StripP2K2(ast.NodeTransformer):
    """What P2K-2 inserted inside a statement that existed before it, removed: fields and dict entries named in
    P2K2_NAMES, the checks and loops that read them, the keyword arguments and imported names, and the tuple entries.
    What is left must equal the statement at P2K-1."""

    def generic_visit(self, node):
        # Decide on the children as they are, then descend into what is kept.
        if isinstance(node, ast.Dict):
            pairs, kept = list(zip(node.keys, node.values)), []
            for k, v in pairs:
                if isinstance(k, ast.Constant) and k.value in P2K2_NAMES:
                    self.dropped.append(ast.dump(k) + ast.dump(v))
                else:
                    kept.append((k, v))
            node.keys, node.values = [k for k, _ in kept], [v for _, v in kept]
        else:
            for field, value in ast.iter_fields(node):
                if isinstance(value, list):
                    setattr(node, field, [v for v in value if not self._dropped(v)])
        return super().generic_visit(node)

    def __init__(self):
        self.uninert, self.dropped = [], []

    def _dropped(self, v) -> bool:
        # An inserted check names a P2K-2 field or function in its test; a check that existed before and only gained
        # names in a literal set or tuple keeps its place (those names are stripped as constants). Everything dropped is
        # recorded, so its content is pinned (INSERTIONS_AT_P2K2) and cannot change unproven.
        inserted_if = isinstance(v, ast.If) and _mentions(_ConstantsOnly().visit(copy.deepcopy(v.test)))
        if inserted_if or (isinstance(v, ast.For) and _mentions(v.iter)):
            if not _inert(v):
                self.uninert.append(ast.dump(v)[:120])
            self.dropped.append(ast.dump(v))
            return True
        dropped = ((isinstance(v, ast.AnnAssign) and isinstance(v.target, ast.Name) and v.target.id in P2K2_NAMES)
                   or (isinstance(v, ast.keyword) and v.arg in P2K2_NAMES)
                   or (isinstance(v, ast.alias) and v.name in P2K2_NAMES)
                   or (isinstance(v, ast.Constant) and isinstance(v.value, str) and v.value in P2K2_NAMES))
        if dropped:
            self.dropped.append(ast.dump(v))
        return dropped


class _ConstantsOnly(ast.NodeTransformer):
    """Only the P2K-2 names a literal collection lists, removed."""

    def generic_visit(self, node):
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                setattr(node, field, [v for v in value if not (isinstance(v, ast.Constant) and isinstance(v.value, str)
                                                               and v.value in P2K2_NAMES)])
        return super().generic_visit(node)


#: The only guarded statements P2K-2 may insert into an existing statement, under exactly ``acid_base_active(profile)``.
GUARD = ast.dump(ast.parse("acid_base_active(profile)", mode="eval").body)
GUARDED = {ast.dump(ast.parse(s).body[0]) for s in ("rr = respiration(state, anchors, profile).respiratory_rate",
                                                    "expected.pop('respiratory_rate')")}


def _raise_only(node) -> bool:
    return not node.orelse and all(isinstance(item, ast.Raise) or (isinstance(item, ast.If) and _raise_only(item))
                                   for item in node.body)


def _inert(node) -> bool:
    """What an inserted check or loop may be inside a statement that existed before P2K-2 (adversarial review): a check
    that only raises; a check whose test is exactly ``acid_base_active(profile)`` and whose body is exactly one of the
    GUARDED statements; a loop over a literal tuple of P2K-2 names holding only raising checks. Anything else would be
    logic hidden from the proof."""
    if isinstance(node, ast.For):
        return (isinstance(node.iter, ast.Tuple) and not node.orelse and all(
            isinstance(e, ast.Constant) and e.value in P2K2_NAMES for e in node.iter.elts)
            and all(isinstance(item, ast.If) and _raise_only(item) for item in node.body))
    if _raise_only(node):
        return True
    return (ast.dump(node.test) == GUARD and not node.orelse and len(node.body) == 1
            and ast.dump(node.body[0]) in GUARDED)


def _keys(index: int, node) -> set:
    if index == 0 and isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(
            node.value.value, str):
        return {"__doc__"}
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return {node.name}
    if isinstance(node, ast.ImportFrom):
        return {f"from {'.' * node.level}{node.module or ''}"}
    if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        return {n.id for t in targets for n in ast.walk(t) if isinstance(n, ast.Name)}
    return set()


def _keyed(relative: str, node) -> bool:
    if relative not in P2K2_KEYED or not isinstance(node, ast.Assign) or len(node.targets) != 1:
        return False
    target, (name, key) = node.targets[0], P2K2_KEYED[relative]
    return isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name) and target.value.id == name and \
        isinstance(target.slice, ast.Constant) and target.slice.value == key


def _strip(relative: str, text: str | None = None) -> tuple:
    tree = ast.parse(text if text is not None else vt._live(relative))
    out, uninert, dropped = [], [], []
    for index, node in enumerate(tree.body):
        keys = _keys(index, node)
        if keys & set(P2K2_CHANGED.get(relative, ())):
            stripper = StripP2K2()
            out.append(stripper.visit(node))
            uninert.extend(stripper.uninert)
            dropped.extend(stripper.dropped)
        elif (keys and keys <= set(P2K2_NEW.get(relative, ()))) or _keyed(relative, node):
            dropped.append(ast.dump(node))
        else:
            out.append(node)
    return out, uninert, hashlib.sha256("\n".join(dropped).encode("utf-8")).hexdigest()


def insertions_digest(relative: str, text: str | None = None) -> str:
    """The AST digest of everything P2K-2 put in the file: its new statements, its fields with their defaults, its
    checks, entries, keywords and imported names, in order."""
    return _strip(relative, text)[2]


def stripped_body(relative: str, text: str | None = None) -> list:
    """The file's top-level statements without P2K-2: its declared new statements dropped (P2K2_NEW, P2K2_KEYED), its
    insertions stripped from the declared changed statements; every other statement kept as it is."""
    return _strip(relative, text)[0]


def inert(relative: str) -> bool:
    """Every check P2K-2 inserted into an existing statement only raises, sets the derived RR or drops the RR
    reconstruction requirement."""
    return not _strip(relative)[1]


def body_digest(body: list, changed=()) -> str:
    """vascular_tone.outside_digest's digest over a statement list: every statement but the ``changed`` ones."""
    kept = [node for index, node in enumerate(body) if not (_keys(index, node) & set(changed))]
    return hashlib.sha256("\n".join(ast.dump(n) for n in kept).encode("utf-8")).hexdigest()


def proved(relative: str) -> bool:
    """The live file is the P2K-1 file plus exactly P2K-2's frozen insertions (their AST digest pinned), every inserted
    check inert: nothing outside them changed, and they are what was frozen and evaluated."""
    body, uninert, inserted = _strip(relative)
    return not uninert and body_digest(body) == WHOLE_AT_P2K1[relative] and inserted == INSERTIONS_AT_P2K2[relative]


def stripped_text(relative: str, text: str | None = None) -> str:
    """A core file (the live one, or ``text``) with P2K-2's insertions removed, as source."""
    return ast.unparse(ast.Module(body=stripped_body(relative, text), type_ignores=[]))


def p2k1_text(relative: str) -> str:
    """The live core file with P2K-2's insertions removed, as source: AST-identical to the P2K-1 file (checked), so the
    closed packages' text-based proofs read it in place of the live file."""
    if not proved(relative):
        raise AssertionError(f"{relative} is not the P2K-1 file plus P2K-2's declared insertions")
    return stripped_text(relative)


def proofs() -> dict:
    return {relative: proved(relative) for relative in CORE_FILES}


#: The two tuple-only files at P2K-1 (81ed6b8): P2K-2 adds its modules to their tuples, nothing else.
TUPLE_AT_P2K1 = {"clinical_core/lactate_slice.py": "7ca12f9057e73a2d1f10cc676f8edc0e1e95be2e94832a2d876badf8e99514e6",
                 "clinical_core/decision_pack.py": "6ca008ec70fb405e0cf770bd099062ced28e098e1eaa774d4f61899ed51aff65"}


def _core_at_p2k1(out: dict) -> dict:
    for relative in CORE_FILES:
        if relative in out and proved(relative):
            out[relative] = CORE_AT_P2K1[relative]
    return out


def p2k1_sources(sources: dict) -> dict:
    """A P2K-1 dependency map: the two tuple-only files at their P2K-1 hashes while only their tuples changed, and each
    core file at its P2K-1 hash when P2K-2 only inserted its declared, off-by-default names there."""
    out = dict(sources)
    for relative, sha in TUPLE_AT_P2K1.items():
        item = vt.TUPLE_CHANGES[relative]
        if relative in out and vt.outside_digest(vt._live(relative), item["changed"]) == item["outside_p2j1"]:
            out[relative] = sha
    return _core_at_p2k1(out)


def p2j4_sources(sources: dict) -> dict:
    """rr_audit.p2j4_sources (the tuple files at P2J-4) with the core files at their P2J-4 hashes (P2K-1's), proven."""
    return _core_at_p2k1(ra.p2j4_sources(sources))


def _outside(relative: str, changed) -> str:
    return body_digest(stripped_body(relative), changed)


def p2j3_sources(sources: dict) -> dict:
    """baroreflex.p2j3_sources on the P2K-1 core recovered from the live one: derived.py at its P2J-3 hash when the
    stripped file proves P2J-4's statements only; integration.py and state.py did not change between P2J-3 and P2K-1."""
    out = br.p2j3_sources(sources)
    item = br.P2J4_CHANGES[DERIVED]
    if DERIVED in out and proved(DERIVED) and _outside(DERIVED, item["changed"]) == item["outside_p2j3"]:
        out[DERIVED] = item["sha_at_p2j3"]
    for relative in (INTEGRATION, STATE):
        if relative in out and proved(relative):
            out[relative] = CORE_AT_P2K1[relative]
    return out


def p2j1_sources(sources: dict) -> dict:
    """baroreflex.p2j1_sources on the recovered P2K-1 core: derived.py through P2J-2's and P2J-4's statements,
    integration.py through P2J-2's, state.py unchanged since before P2J-1."""
    out = br.p2j1_sources(sources)
    item, integration = br.P2J4_CHANGES[DERIVED], vt.P2J2_CHANGES[INTEGRATION]
    if DERIVED in out and proved(DERIVED) and _outside(DERIVED, item["since_p2j1"]) == item["outside_p2j1"]:
        out[DERIVED] = item["sha_at_p2j1"]
    if INTEGRATION in out and proved(INTEGRATION) and \
            _outside(INTEGRATION, integration["changed"]) == integration["outside_p2j1"]:
        out[INTEGRATION] = integration["sha_at_p2j1"]
    if STATE in out and proved(STATE):
        out[STATE] = CORE_AT_P2K1[STATE]
    return out


def p2i2ak_sources(sources: dict) -> dict:
    """baroreflex.p2i2ak_sources on the recovered P2K-1 core (P2J-1's, P2J-2's and P2J-4's statements together)."""
    out = br.p2i2ak_sources(sources)
    item, integration = br.P2J4_CHANGES[DERIVED], vt.P2J2_CHANGES[INTEGRATION]
    if DERIVED in out and proved(DERIVED) and _outside(DERIVED, item["since_p2i2ak"]) == item["outside_p2i2ak"]:
        out[DERIVED] = item["sha_at_p2i2ak"]
    if INTEGRATION in out and proved(INTEGRATION) and \
            _outside(INTEGRATION, integration["since_p2i2ak"]) == integration["outside_p2i2ak"]:
        out[INTEGRATION] = integration["sha_at_p2i2ak"]
    if STATE in out and proved(STATE):
        out[STATE] = CORE_AT_P2K1[STATE]
    return out


# 10. Design, freeze, run -------------------------------------------------------------------------------------------------------

def design() -> dict:
    return {"revision": REVISION, "decided": DECIDED, "faculty": FACULTY, "carried": CARRIED, "semantics": SEMANTICS,
            "retired": RETIRED, "status": STATUS, "candidate_inputs": list(CANDIDATE_INPUTS), "lgn": LGN, "support": SUPPORT, "intrinsic_rr": list(INTRINSIC_RR),
            "drive_gains": list(DRIVE_GAINS), "steady_burdens": list(STEADY_BURDENS), "acid_taus": list(ACID_TAUS),
            "efficiency": EFFICIENCY, "saturation": SATURATION, "arrival_tolerance": ARRIVAL_TOLERANCE,
            "authored_rr": AUTHORED_RR, "candidate_rule": CANDIDATE_RULE, "probe_gas": PROBE_GAS,
            "probe_rule": PROBE_RULE, "reconstruction_rule": RECONSTRUCTION_RULE,
            "validation_candidate": list(VALIDATION_CANDIDATE), "identifiability_rule": IDENTIFIABILITY_RULE,
            "criteria": list(CRITERIA), "verdict_rule": VERDICT_RULE, "decision_pack": list(DECISION_PACK),
            "policy": POLICY, "p2k2_names": sorted(P2K2_NAMES), "p2k2_changed": P2K2_CHANGED, "p2k2_new": P2K2_NEW,
            "p2k2_keyed": P2K2_KEYED, "tuple_at_p2k1": TUPLE_AT_P2K1,
            "core_at_p2k1": CORE_AT_P2K1, "whole_at_p2k1": WHOLE_AT_P2K1}


def freeze_digest() -> str:
    text = json.dumps({"revision": REVISION, "p2k1": hashlib.sha256(P2K1_RECORD.read_bytes()).hexdigest(),
                       "design": design(), "sources": bf.freeze_sources()}, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def p2k1_record() -> dict:
    record = json.loads(P2K1_RECORD.read_text(encoding="utf-8"))
    if record["freeze_digest"] != P2K1_DIGEST or not record["verdict"]["verdict"].startswith(ra.NOT_READY):
        raise AssertionError("the P2K-1 record is not the committed one")
    return record


def run(progress=None, map_=map) -> dict:
    say = progress or (lambda *_: None)
    with lr.P2FGuard(), lr.LegacyLock():
        p2k1_record()
        out = {"freeze_digest": freeze_digest(), "decided": DECIDED, "revision": REVISION, "policy": POLICY,
               "faculty": FACULTY, "record": P2K1_DIGEST, "design": design()}
        say("structure, arrival and probes")
        compat = arrival_compatibility()
        probes_ = probes()
        say("certified physiology (P2J-3 region)")
        region = br.pressure_tone_region(map_, say)
        arrivals = lr.arrival_table()
        say("deficit trajectories")
        store = reconstruct(region, arrivals)
        say("acid-base reconstruction")
        evaluated = evaluate(store, compat["compatible"])
        say("validation against the core")
        validation = validate(region, store)
        questions = key_questions(evaluated, probes_)
        dependencies_ = dependencies(store, evaluated)
        r1 = questions["1_untreated_acid_and_drive"]["by_pair"]
        r4 = questions["3_post_resuscitation"]
        checks = {
            "acid_burden_causal": probes_["A"]["drive_rises"] and probes_["A"]["rr_rises"],
            "lactate_retired": probes_["B"]["rr_unchanged"] and probes_["D"]["rr_falls"],
            "d_not_direct": probes_["C"]["rr_unchanged"],
            "distinct_drive_rr_w": probes_["E1"]["w_at_most_1"] and probes_["E1"]["paco2_above_arrival"]
            and probes_["F"]["rr_unchanged"] and probes_["F"]["w_rises"] and probes_["W_channel"]["rr_unchanged"],
            "paco2_ph_coherent": probes_["F"]["paco2_falls"] and probes_["G"]["paco2_rises"]
            and probes_["H"]["ph_formula"] and probes_["H"]["more_acid_lower_ph"] and probes_["H"]["arrival_exact"]
            and all(abs(ph_reconstruction(case)["error"]) <= 0.005 for case in CASES),
            "rr_w_dissociation": probes_["E1"]["w_at_most_1"] and probes_["E1"]["paco2_above_arrival"]
            and probes_["E1"]["rr_above_intrinsic"] and probes_["E2"]["paco2_rises"],
            "patient_like": any(v["n"] and v["true"] == v["n"] for v in r1.values())
            and r4["no_instant_normalization"]["n"] > 0
            and r4["no_instant_normalization"]["true"] == r4["no_instant_normalization"]["n"]
            and r4["haemostasis_step_vs_others"]["true"] == r4["haemostasis_step_vs_others"]["n"],
            "no_upstream_regression": validation["equal"] and validation["upstream_equal"]
            and validation["default_rr_equal"] and all(region["unchanged"].values()) and p2k1_unchanged(store),
            "bounded_surface": compat["count"] > 0,
            "nothing_approved": True}
        out.update({
            "authored_gas": {case: authored_gas(case) for case in CASES},
            "arrival_burden": {case: arrival_burden(case) for case in CASES},
            "ph_reconstruction": {case: ph_reconstruction(case) for case in CASES},
            "exact_arrival_gains": exact_arrival_gains(), "drive_gain_support": list(drive_gain_support()),
            "arrival_deficits": arrival_deficits(), "steady_burden_support": list(steady_burden_support()),
            "arrival_compatibility": compat, "probes": probes_, "pressure_tone_unchanged": region["unchanged"],
            "reconstruction": evaluated["tables"], "rejections": evaluated["rejections"], "validation": validation,
            "p2k1_unchanged": p2k1_unchanged(store), "key_questions": questions, "dependencies": dependencies_,
            "identifiability": identifiability(compat), "proofs": proofs(),
            "efficiency": {"p2j3_blood_runs": region["blood_runs"], "p2j3_counterfactual_runs": region["counterfactual_runs"],
                           "deficit_trajectories": sum(len(seen) for seen in store.values()),
                           "acid_pairs": len(acid_pairs()), "compatible_triples": compat["count"],
                           "core_validation_runs": 2 * validation["compared"], "cartesian_sweep": False,
                           "legacy_read": False, "combinations": len(DRIVE_GAINS) * 9 * len(acid_pairs())}})
        out["verdict"] = verdict(checks)
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--digest", action="store_true")
    parser.add_argument("--design", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    if args.digest:
        print(freeze_digest())
    if args.design:
        print(json.dumps(design(), indent=1, sort_keys=True, default=str))
    if args.run:
        if args.out is None:
            parser.error("--run needs --out")
        args.out.mkdir(parents=True, exist_ok=True)
        result = run(progress=lambda *m: print(*m, flush=True))
        (args.out / "acid_base.json").write_text(json.dumps(result, indent=1, sort_keys=True, default=str) + "\n",
                                                 encoding="utf-8")
        print(result["verdict"]["verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
