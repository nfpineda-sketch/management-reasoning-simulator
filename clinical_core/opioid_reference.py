"""P2U-1: opioid_35m's and opioid_67f's repository truth, their arrival mapping and the common reference profile.

Shadow only. Nothing here is a default the core uses. Kept apart, as the ACS, oedema, PE and asthma packages do:
- A. repository truth: read from the case bank itself (``clinical_cases.py``), by path, never retyped;
- B. arrival mapping: each value the case does not state is neutral or a band built by an existing rule (gi_reference
  for the lactate and the intrinsic HR), declared ``synthetic_probe`` so the migration gate keeps blocking it, and
  classified CASE_AUTHORED / CASE_MAPPING / FAMILY_CANDIDATE; none is FACULTY_APPROVED_COMMON;
- C. the common reference profile: the ACS package's predeclared point with the P2S-2 respiratory mechanics candidate
  switched on (as asthma's); no value chosen for the opioid family. The P2T-5 link stays UNSET (R None) here.

The arrival central availability and mechanics efficiency are FAMILY_CANDIDATE latent arrival states, read together from
the authored RR and PaCO2 at each carried intrinsic RR (12 / 16 / 20), at the arrival demand ratio 1, with the arrival
excitatory drive the common composition gives (the acid drive from the authored HCO3; no distress, no hypoxaemic drive):
availability = authored RR / excitatory RR, efficiency = PaCO2_reference x intrinsic RR / (authored PaCO2 x authored RR)
(P2S-2-11's region). Never from the disease label, never a selected value. G, L and the distress stay neutral: the lungs
are authored clear (A-lines, no consolidation, clear radiograph) and the breathing is reduced, not laboured.
"""
from __future__ import annotations

import functools

from . import acs_reference as ar
from . import derived as dv
from . import gi_reference
from .state import Anchors, RhythmCode, RhythmState

CASE, SECONDARY, FAMILY = "opioid_35m", "opioid_67f", "opioid"
CASES = (CASE, SECONDARY)
SELECTION_RULE = ("the faculty's primary (opioid_35m: opioid toxidrome with respiratory depression after an uncertain "
                  "tablet) and secondary (opioid_67f: long-acting opioid ventilatory depression with recurrence risk); "
                  "the family's only two variants")
CASE_AUTHORED, CASE_MAPPING, FAMILY_CANDIDATE, SYNTHETIC_ONLY = ar.CASE_AUTHORED, ar.CASE_MAPPING, ar.FAMILY_CANDIDATE, \
    ar.SYNTHETIC_ONLY
LEVEL_OF = ar.LEVEL_OF
#: P2K-2's carried 12 / 16 / 20 (as asthma_reference.INTRINSIC_POINTS), the middle the representative point.
INTRINSIC_POINTS = {"lower": 12.0, "midpoint": ar.INTRINSIC_RR, "upper": 20.0}
ARRIVAL_DEMAND_RATIO = 1.0         # the arrival demand is the case's baseline by construction (BASELINE_RELATIVE)


# C. The common reference profile ---------------------------------------------------------------------------------------------

def common_profile(**changes):
    """The ACS package's predeclared common point with the P2S-2 respiratory mechanics candidate on (as asthma's); nothing
    chosen for the opioid family. The P2T-5 link stays UNSET; the analysis declares R only as P2T-5's synthetic
    reference."""
    return ar.common_profile(respiratory_mechanics=True, **changes)


@functools.lru_cache(maxsize=None)
def bank_case(case: str = CASE) -> dict:
    """The case exactly as the bank holds it."""
    import clinical_cases
    return next(c for c in clinical_cases.FAMILIES[FAMILY]["variants"] if c["id"] == case)


def _at(path: tuple, case: str):
    value = bank_case(case)
    for key in path:
        value = value[key]
    return value


# A. Repository truth -----------------------------------------------------------------------------------------------------------

#: item -> path in the case bank. Every value is read, none retyped.
TRUTH_PATHS = {
    "sbp": ("observable", "sbp"), "dbp": ("observable", "dbp"), "hr": ("observable", "hr"),
    "rhythm": ("observable", "rhythm"), "spo2": ("observable", "spo2"),
    "respiratory_rate": ("observable", "respiratory_rate"), "work_of_breathing": ("observable", "work_of_breathing"),
    "crt_s": ("observable", "crt"), "extremities": ("observable", "extremities"),
    "mental_status": ("observable", "mental_status"), "temperature_c": ("observable", "temperature_c"),
    "peripheral_perfusion": ("observable", "peripheral_perfusion"),
    "glucose_mg_dl": ("observable", "glucose_mg_dl"),
    "lactate_mmol_l": ("investigations", "lactate", "result", "lactate_mmol_l"),
    "hb_g_dl": ("investigations", "basic_labs", "result", "hemoglobin_g_dl"),
    "potassium_mmol_l": ("investigations", "basic_labs", "result", "potassium_mmol_l"),
    "creatinine_mg_dl": ("investigations", "basic_labs", "result", "creatinine_mg_dl"),
    "abg_ph": ("investigations", "abg", "result", "ph"), "abg_paco2": ("investigations", "abg", "result", "paco2_mm_hg"),
    "abg_pao2": ("investigations", "abg", "result", "pao2_mm_hg"),
    "abg_hco3": ("investigations", "abg", "result", "bicarbonate_mmol_l"),
    "abg_fio2_percent": ("investigations", "abg", "result", "fio2_percent"),
    "vbg_ph": ("investigations", "vbg", "result", "ph"), "vbg_pco2": ("investigations", "vbg", "result", "pco2_mm_hg"),
    "pocus_lungs": ("investigations", "pocus", "result", "lungs"),
    "pocus_consolidation": ("investigations", "pocus", "result", "lung_consolidation"),
    "pocus_lv": ("investigations", "pocus", "result", "lv"), "pocus_ivc": ("investigations", "pocus", "result", "ivc"),
    "chest_xray": ("investigations", "chest_xray", "result", "report"),
    "troponin_ng_l": ("investigations", "troponin", "result", "value_ng_l"),
    "respiratory_exam": ("examination", "Respiratory"), "neurological_exam": ("examination", "Neurological"),
    "cardiac_exam": ("examination", "Cardiac"), "presentation": ("presentation",),
    "medications": ("history", "medications"), "exposure": ("history", "exposure"), "onset": ("history", "onset"),
    "breathing": ("history", "breathing"), "comorbidities": ("patient", "comorbidities"),
    "definitive_actions": ("engine", "definitive_actions"), "recurrence_risk": ("engine", "recurrence_risk"),
    "diagnosis": ("faculty", "diagnosis"), "discriminating_findings": ("faculty", "discriminating_findings")}


def truth(case: str = CASE) -> dict:
    out = {}
    for item, path in TRUTH_PATHS.items():
        try:
            out[item] = _at(path, case)
        except (KeyError, TypeError):
            out[item] = None
    return out


def authored_map(t: dict) -> float:
    return (t["sbp"] + 2.0 * t["dbp"]) / 3.0


# B. Arrival mapping ----------------------------------------------------------------------------------------------------------

Band = ar.Band


def implied_efficiency(t: dict, intrinsic: float, demand_ratio: float = ARRIVAL_DEMAND_RATIO) -> float:
    """P2S-2-11's analytic arrival efficiency: the one the common form needs for the authored RR and PaCO2."""
    return dv.DEFAULT_PROFILE.paco2_reference_mmhg * demand_ratio * intrinsic / (float(t["abg_paco2"])
                                                                                   * float(t["respiratory_rate"]))


def excitatory_rr(t: dict, intrinsic: float, profile=None) -> float:
    """The RR the arrival excitatory drive gives with the central machinery intact (the common composition: the acid
    drive from the authored HCO3; no distress, no hypoxaemic drive)."""
    p = common_profile() if profile is None else profile
    burden = max(0.0, p.bicarbonate_reference_meq_l - float(t["abg_hco3"]))
    return dv.rate_from_drive(dv.respiratory_drive(burden, p), intrinsic, p)


def implied_availability(t: dict, intrinsic: float, profile=None) -> float:
    """The arrival central availability the composition needs for the authored RR: authored RR / excitatory RR."""
    return float(t["respiratory_rate"]) / excitatory_rr(t, intrinsic, profile)


def mechanics_band(case: str = CASE) -> Band:
    t = truth(case)
    values = {point: implied_efficiency(t, i) for point, i in INTRINSIC_POINTS.items()}
    return Band("arrival_mechanics_efficiency", values["lower"], values["upper"], values["midpoint"], FAMILY_CANDIDATE,
                "P2S-2-11's analytic region: PaCO2_reference x demand x intrinsic RR / (authored PaCO2 x authored RR), "
                "each point with its own declared intrinsic RR (12 / 16 / 20), the arrival demand ratio 1; no value "
                "selected, nothing fitted to a later course")


def availability_band(case: str = CASE) -> Band:
    t = truth(case)
    values = {point: implied_availability(t, i) for point, i in INTRINSIC_POINTS.items()}
    return Band("arrival_central_availability", values["upper"], values["lower"], values["midpoint"], FAMILY_CANDIDATE,
                "the composition read backwards: authored RR / the excitatory RR at each declared intrinsic RR (12 / 16 / "
                "20; the arrival acid drive from the authored HCO3, no distress, no hypoxaemic drive); the lower bound "
                "goes with the upper intrinsic RR; no value selected")


def bands(case: str = CASE) -> dict:
    t = truth(case)
    low, mid, high = gi_reference.BASELINE_LACTATE
    rest_low, rest_mid, rest_high = gi_reference.RESTING_HR
    return {b.name: b for b in (
        Band("arrival_lactate_excess", round(t["lactate_mmol_l"] - high, 6), round(t["lactate_mmol_l"] - low, 6),
             round(t["lactate_mmol_l"] - mid, 6), CASE_MAPPING,
             "gi_reference.lactate_excess_band's rule: the arrival lactate less a non-shock clearance baseline of "
             "0.8-2.0 mmol/L; the baseline is not stated"),
        Band("intrinsic_sinus_rate", rest_low, min(rest_high, t["hr"]), min(rest_mid, t["hr"]), CASE_MAPPING,
             "gi_reference.intrinsic_hr_band's rule: the resting adult sinus rate, at most the observed HR; no "
             "beta-blocker or opioid HR effect is authored"),
        mechanics_band(case), availability_band(case))}


def anchors(case: str = CASE, point: str = "midpoint", **changes) -> Anchors:
    """The case's arrival anchors: authored values exactly, the bands at ``point`` (the intrinsic RR with its own implied
    availability and efficiency), every value the case does not state declared as a synthetic probe."""
    t = truth(case)
    b = bands(case)
    intrinsic = changes.pop("intrinsic_respiratory_rate", INTRINSIC_POINTS[point])
    mechanics = changes.pop("arrival_mechanics_efficiency", implied_efficiency(t, intrinsic))
    availability = changes.pop("arrival_central_availability", implied_availability(t, intrinsic))
    candidates = {"arrival_lactate_excess": getattr(b["arrival_lactate_excess"], point),
                  "intrinsic_sinus_rate": getattr(b["intrinsic_sinus_rate"], point), **changes}
    if not str(t["rhythm"]).lower().startswith("sinus"):
        raise ValueError("only a sinus arrival is anchored")
    return Anchors(case_id=case, sbp=float(t["sbp"]), dbp=float(t["dbp"]), hr=float(t["hr"]), spo2=float(t["spo2"]),
                   respiratory_rate=float(t["respiratory_rate"]), crt_s=float(t["crt_s"]),
                   lactate=float(t["lactate_mmol_l"]), hb=float(t["hb_g_dl"]), glucose=float(t["glucose_mg_dl"]),
                   k=float(t["potassium_mmol_l"]), fio2=t["abg_fio2_percent"] / 100.0,
                   rhythm=RhythmState(RhythmCode.SINUS, float(t["hr"]), 1.0, True),
                   consciousness_level=LEVEL_OF[t["mental_status"]],
                   intrinsic_respiratory_rate=intrinsic, arrival_bicarbonate=float(t["abg_hco3"]),
                   arrival_paco2=float(t["abg_paco2"]), arrival_mechanics_efficiency=mechanics,
                   arrival_central_availability=availability,
                   declared={name: "synthetic_probe" for name in candidates if name in ar._CASE_PARAMETER_NAMES},
                   **candidates)


#: Classification of every arrival field: all ARRIVAL_MAPPING, none a common equation.
ARRIVAL_CLASSES = {
    "sbp": CASE_AUTHORED, "dbp": CASE_AUTHORED, "hr": CASE_AUTHORED, "spo2": CASE_AUTHORED,
    "respiratory_rate": CASE_AUTHORED, "crt_s": CASE_AUTHORED, "lactate": CASE_AUTHORED, "hb": CASE_AUTHORED,
    "glucose": CASE_AUTHORED, "k": CASE_AUTHORED, "fio2": CASE_AUTHORED, "rhythm": CASE_AUTHORED,
    "consciousness_level": CASE_AUTHORED, "arrival_bicarbonate": CASE_AUTHORED, "arrival_paco2": CASE_AUTHORED,
    "arrival_central_availability": FAMILY_CANDIDATE + " (the composition read backwards; LATENT_ARRIVAL_STATE)",
    "arrival_mechanics_efficiency": FAMILY_CANDIDATE + " (P2S-2-11's analytic region; LATENT_ARRIVAL_STATE)",
    "intrinsic_respiratory_rate": FAMILY_CANDIDATE + " (P2K-2's 12 / 16 / 20, declared with its own availability and "
                                                     "efficiency)",
    "arrival_respiratory_distress": "CASE_MAPPING (0: the breathing is authored reduced, not laboured)",
    "preload_fraction": "CASE_MAPPING (the profile's provisional position: IVC 1.8 / 1.9 cm, LV preserved)",
    "pump_reserve": "CASE_MAPPING (neutral 1)",
    "arrival_delivery_ratio": "CASE_MAPPING (neutral 1: perfusion authored as preserved, warm, CRT 2 s)",
    "arrival_oxygen_debt": "CASE_MAPPING (neutral 0; never computed from the lactate)",
    "beta_blockade": "CASE_MAPPING (0: no beta-blocker authored)",
    "metabolic_demand_baseline": "CASE_MAPPING (1: afebrile)",
    "reversible_lung_water": "CASE_MAPPING (0: A-line pattern, no B-lines, no consolidation, clear radiograph)",
    **{name: band.classification for name, band in bands(CASE).items()}}
#: The channels at arrival, checked rather than forced.
CHANNEL_ROLES = {
    "V": "NORMAL_OR_NEUTRAL (V = 0; IVC 1.8 / 1.9 cm, LV preserved)",
    "T": "NORMAL_OR_NEUTRAL (T = 1; warm, preserved perfusion, BP 106/64 and 104/62)",
    "P": "NORMAL_OR_NEUTRAL (P = 1; LV preserved, troponin 7 / 11)",
    "R": "NORMAL_OR_NEUTRAL (sinus 68 / 62; no opioid HR term)",
    "L": "NORMAL_OR_NEUTRAL (L = 0: A-lines, no B-lines, clear radiograph)",
    "G": "NORMAL_OR_NEUTRAL (G = 0: the arrival SpO2 80 / 84, PaO2 45 / 50 on room air is the anchored arrival state; no "
         "pulmonary pathology is authored, so no G writer)",
    "W": "SECONDARY_RESPONSE (W derived from the expressed RR and the mechanics; PaCO2 69 / 61, pH 7.21 / 7.25)",
    "D": "NORMAL_OR_NEUTRAL (perfusion preserved; lactate 2.6 / 2.2 mapped as clearable excess, no prior debt)",
    "N": "NORMAL_OR_NEUTRAL (obtunded with small pupils: the toxidrome, not a primary neurological process; N is P2L-2's "
         "and stays unread: CONSCIOUSNESS_INTEGRATION_DEBT)",
    "central_availability": "PRIMARY_DRIVER (the family's mechanism: the arrival latent availability and the writers)",
    "Hb": "NORMAL_OR_NEUTRAL", "Glu": "NORMAL_OR_NEUTRAL", "K": "NORMAL_OR_NEUTRAL (4.1)"}
OBSERVATION_LAYER = {
    "mental_status_and_pupils": "observations of the toxidrome (obtunded, small reactive pupils): diagnostic only; the "
                                "common consciousness integration is deferred",
    "slow_shallow_breaths": "observations of the expressed RR and the effort; the shallow-breath descriptor is not read "
                            "into the mechanics (see the steady-state tension in the analysis)",
    "work_of_breathing": "'Reduced': no distress; the distress readers stay UNSET and the distress 0",
    "rhythm": "R (sinus, its rate from the common HR physiology)"}
