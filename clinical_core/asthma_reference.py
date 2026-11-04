"""P2S-3: asthma_49m's and asthma_24f's repository truth, their arrival mapping and the common reference profile.

Shadow only. Nothing here is a default the core uses. Kept apart, as the ACS, oedema and PE packages do:
- A. repository truth: read from the case bank itself (``clinical_cases.py``), by path, never retyped;
- B. arrival mapping: each value the case does not state is neutral or a band built by an existing rule (gi_reference
  for the lactate and the intrinsic HR), declared ``synthetic_probe`` so the migration gate keeps blocking it, and
  classified CASE_AUTHORED / CASE_MAPPING / FAMILY_CANDIDATE; none is FACULTY_APPROVED_COMMON;
- C. the common reference profile: the ACS package's predeclared point with the P2S-2 respiratory mechanics candidate
  switched on; no value chosen for asthma.

The arrival mechanics efficiency is a FAMILY_CANDIDATE latent arrival state (P2S-2): the analytic region the authored RR
and PaCO2 imply, E = PaCO2_reference x demand x intrinsic RR / (PaCO2 x RR), with the carried intrinsic RR (12 / 16 /
20) declared together with its own efficiency, at the arrival demand ratio 1. Never from the disease label, never a
selected value. Central availability stays 1: the drowsiness is authored with the hypercapnia, not as an independent
CNS depression.
"""
from __future__ import annotations

import functools

from . import acs_reference as ar
from . import derived as dv
from . import gi_reference
from .state import Anchors, RhythmCode, RhythmState

CASE, SECONDARY, FAMILY = "asthma_49m", "asthma_24f", "asthma"
CASES = (CASE, SECONDARY)
#: The cases, by a rule fixed before any run: the faculty names both (primary 49m, secondary 24f); they are the family's
#: only two variants.
SELECTION_RULE = ("the faculty's primary (asthma_49m: life-threatening asthma with fatigue and hypercapnia) and secondary "
                  "(asthma_24f: acute severe asthma, compensated ventilation); the family's only two variants")
CASE_AUTHORED, CASE_MAPPING, FAMILY_CANDIDATE, SYNTHETIC_ONLY = ar.CASE_AUTHORED, ar.CASE_MAPPING, ar.FAMILY_CANDIDATE, \
    ar.SYNTHETIC_ONLY
LEVEL_OF = ar.LEVEL_OF
#: The intrinsic RR points, declared (P2S-2 review: an undeclared intrinsic RR would read the authored RR as W's
#: reference): P2K-2's carried 12 / 16 / 20 (acid_base.INTRINSIC_RR, not imported: this mapping stays in the P2G pack
#: digest, the analysis modules do not), the middle the representative point, as for ACS, oedema and PE.
INTRINSIC_POINTS = {"lower": 12.0, "midpoint": ar.INTRINSIC_RR, "upper": 20.0}
ARRIVAL_DEMAND_RATIO = 1.0         # the arrival demand is the case's baseline by construction (BASELINE_RELATIVE)


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
    "abg_ph": ("investigations", "abg", "result", "ph"), "abg_paco2": ("investigations", "abg", "result", "paco2_mm_hg"),
    "abg_pao2": ("investigations", "abg", "result", "pao2_mm_hg"),
    "abg_hco3": ("investigations", "abg", "result", "bicarbonate_mmol_l"),
    "abg_fio2_percent": ("investigations", "abg", "result", "fio2_percent"),
    "vbg_ph": ("investigations", "vbg", "result", "ph"), "vbg_pco2": ("investigations", "vbg", "result", "pco2_mm_hg"),
    "pocus_lungs": ("investigations", "pocus", "result", "lungs"),
    "pocus_lv": ("investigations", "pocus", "result", "lv"), "pocus_ivc": ("investigations", "pocus", "result", "ivc"),
    "pocus_consolidation": ("investigations", "pocus", "result", "lung_consolidation"),
    "pocus_sliding": ("investigations", "pocus", "result", "lung_sliding"),
    "chest_xray": ("investigations", "chest_xray", "result", "report"),
    "respiratory_exam": ("examination", "Respiratory"), "neurological_exam": ("examination", "Neurological"),
    "cardiac_exam": ("examination", "Cardiac"), "presentation": ("presentation",),
    "medications": ("history", "medications"), "onset": ("history", "onset"), "breathing": ("history", "breathing"),
    "definitive_actions": ("engine", "definitive_actions"), "diagnosis": ("faculty", "diagnosis")}


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


def peak_flow(t: dict) -> str:
    """The authored peak flow, read from the respiratory examination text: a statement, never a number fitted."""
    text = str(t["respiratory_exam"])
    if "peak expiratory flow is" in text.lower():
        return text[text.lower().index("peak expiratory flow is"):].split(".")[0]
    if "peak-flow" in text.lower() or "peak flow" in text.lower():
        return [s for s in text.split(". ") if "peak" in s.lower()][0].rstrip(".")
    return "not authored"


# B. Arrival mapping ----------------------------------------------------------------------------------------------------------

Band = ar.Band


def implied_efficiency(t: dict, intrinsic: float, demand_ratio: float = ARRIVAL_DEMAND_RATIO) -> float:
    """P2S-2-11's analytic arrival efficiency: the one the common form needs for the authored RR and PaCO2."""
    return dv.DEFAULT_PROFILE.paco2_reference_mmhg * demand_ratio * intrinsic / (float(t["abg_paco2"])
                                                                                   * float(t["respiratory_rate"]))


def mechanics_band(case: str = CASE) -> Band:
    t = truth(case)
    values = {point: implied_efficiency(t, i) for point, i in INTRINSIC_POINTS.items()}
    return Band("arrival_mechanics_efficiency", values["lower"], values["upper"], values["midpoint"], FAMILY_CANDIDATE,
                "P2S-2-11's analytic region: PaCO2_reference x demand x intrinsic RR / (authored PaCO2 x authored RR), "
                "each point with its own declared intrinsic RR (12 / 16 / 20), the arrival demand ratio 1; no value "
                "selected, nothing fitted to a later course")


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
             "beta-blocker is authored (the authored repeated beta-agonist use is a confounder, not modelled)"),
        mechanics_band(case))}


def anchors(case: str = CASE, point: str = "midpoint", **changes) -> Anchors:
    """The case's arrival anchors: authored values exactly, the bands at ``point`` (the intrinsic RR with its own implied
    efficiency), every value the case does not state declared as a synthetic probe."""
    t = truth(case)
    b = bands(case)
    mechanics = changes.pop("arrival_mechanics_efficiency", getattr(b["arrival_mechanics_efficiency"], point))
    intrinsic = changes.pop("intrinsic_respiratory_rate", INTRINSIC_POINTS[point])
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
                   declared={name: "synthetic_probe" for name in candidates if name in ar._CASE_PARAMETER_NAMES},
                   **candidates)


#: Classification of every arrival field: all ARRIVAL_MAPPING, none a common equation.
ARRIVAL_CLASSES = {
    "sbp": CASE_AUTHORED, "dbp": CASE_AUTHORED, "hr": CASE_AUTHORED, "spo2": CASE_AUTHORED,
    "respiratory_rate": CASE_AUTHORED, "crt_s": CASE_AUTHORED, "lactate": CASE_AUTHORED, "hb": CASE_AUTHORED,
    "glucose": CASE_AUTHORED, "k": CASE_AUTHORED, "fio2": CASE_AUTHORED, "rhythm": CASE_AUTHORED,
    "consciousness_level": CASE_AUTHORED, "arrival_bicarbonate": CASE_AUTHORED, "arrival_paco2": CASE_AUTHORED,
    "arrival_mechanics_efficiency": FAMILY_CANDIDATE + " (the analytic region; LATENT_ARRIVAL_STATE)",
    "intrinsic_respiratory_rate": FAMILY_CANDIDATE + " (P2K-2's 12 / 16 / 20, declared with its own efficiency)",
    "central_drive_availability": "CASE_MAPPING (1: no CNS depression independent of the hypercapnia is authored)",
    "preload_fraction": "CASE_MAPPING (the profile's provisional position: IVC collapsing, LV preserved, no preload "
                        "evidence of a deficit or excess)",
    "pump_reserve": "CASE_MAPPING (neutral 1)",
    "arrival_delivery_ratio": "CASE_MAPPING (neutral 1: perfusion authored as preserved, warm, CRT 2 s)",
    "arrival_oxygen_debt": "CASE_MAPPING (neutral 0; never computed from the lactate)",
    "beta_blockade": "CASE_MAPPING (0: no beta-blocker authored)",
    "metabolic_demand_baseline": "CASE_MAPPING (1: afebrile; the respiratory muscles' demand is not modelled)",
    "reversible_lung_water": "CASE_MAPPING (0: A-line pattern, no B-lines, no consolidation; L is not an asthma channel)",
    **{name: band.classification for name, band in bands(CASE).items()}}
#: The channels at arrival, checked rather than forced.
CHANNEL_ROLES = {
    "V": "NORMAL_OR_NEUTRAL (V = 0; IVC collapsing, LV preserved)",
    "T": "NORMAL_OR_NEUTRAL (T = 1; warm, preserved perfusion, BP 142/86 and 138/84)",
    "P": "NORMAL_OR_NEUTRAL (P = 1; LV preserved, troponin 8)",
    "R": "SECONDARY_RESPONSE (sinus tachycardia 132 / 126; repeated beta-agonist use authored)",
    "L": "NORMAL_OR_NEUTRAL (L = 0: A-lines, no B-lines; asthma writes no L)",
    "G": "SECONDARY_RESPONSE (SpO2 89 / 90, PaO2 57 / 59 on room air: the arrival gas exchange is the anchored arrival "
         "state, G = 0; no later V/Q change is authored)",
    "W": "PRIMARY_DRIVER through the mechanics efficiency (W derived; 49m PaCO2 51 pH 7.30, 24f PaCO2 31 pH 7.45)",
    "D": "NORMAL_OR_NEUTRAL (perfusion preserved; lactate 2.6 / 2.1 mapped as clearable excess, no prior debt)",
    "N": "SECONDARY_RESPONSE (49m drowsy with hypercapnia; 24f alert)",
    "Hb": "NORMAL_OR_NEUTRAL", "Glu": "NORMAL_OR_NEUTRAL", "K": "NORMAL_OR_NEUTRAL (4.1; beta-agonist kalaemia not "
                                                                 "modelled)"}
OBSERVATION_LAYER = {
    "wheeze_air_entry_peak_flow": "observations of the mechanics efficiency (the quieter chest of 49m is poor air entry, "
                                  "not improvement); no common observation mapping exists yet",
    "work_of_breathing": "an observation of the respiratory load; the core has no distress or mechanoreceptor drive",
    "hyperinflation_on_radiograph": "an observation of the obstruction; no lung-volume state",
    "rhythm": "R (sinus, its rate from the common HR physiology)"}


# C. The common reference profile ---------------------------------------------------------------------------------------------

def common_profile(**changes):
    """The ACS package's predeclared common point with the P2S-2 respiratory mechanics candidate on; nothing chosen for
    asthma (the analysis adds P2O-1's SYNTHETIC_ONLY gas-exchange reference)."""
    return ar.common_profile(respiratory_mechanics=True, **changes)
