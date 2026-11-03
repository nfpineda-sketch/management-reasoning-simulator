"""P2P-1: pulmonary_edema_58m's repository truth, its arrival mapping and the common reference profile it runs on.

Shadow only. Nothing here is a default the core uses. Kept apart, as P2N-2 does for acs_70f_left_main:
- A. repository truth: read from the case bank itself (``clinical_cases.py``), by path, never retyped;
- B. arrival mapping: each value the case does not state is neutral or a band built by the rule the GI and ACS packages
  use where one exists (gi_reference), declared ``synthetic_probe`` so the migration gate keeps blocking it, and
  classified CASE_AUTHORED / CASE_MAPPING / FAMILY_CANDIDATE / SYNTHETIC_ONLY; none is FACULTY_APPROVED_COMMON;
- C. the common reference profile: the ACS package's predeclared point of the common uncertainty (acs_reference), the
  same values, chosen before any edema run, never because it fits this case.

V and L are mapped apart (P2O-3 decision 7): V from the preload evidence (the IVC, the jugular veins, the case's own
congestion block), L from the pulmonary congestion evidence (B-lines, crackles, the radiograph). B-lines never inform V,
the pump or its reserve. L = 0 is the arrival congestion, read as an observation, never dry lungs.
"""
from __future__ import annotations

import functools
from dataclasses import dataclass

from . import acs_reference as ar
from . import gi_reference
from .state import Anchors, RhythmCode, RhythmState

CASE, FAMILY = "pulmonary_edema_58m", "pulmonary_edema"
#: The case, chosen by a rule fixed before any run: the family has two approved variants and no canonical one; the
#: brief asks for the acute cardiogenic pulmonary edema case, and only pulmonary_edema_58m's authored diagnosis is that
#: ("Hypertensive acute cardiogenic pulmonary edema"; pulmonary_edema_75f's is "Acute decompensated systolic heart
#: failure with pulmonary edema", with volume overload). It is also the family's first variant.
SELECTION_RULE = ("the variant whose authored faculty diagnosis names acute cardiogenic pulmonary edema; the other "
                  "variant (pulmonary_edema_75f: decompensated HFrEF with volume overload and CKD) is left for later")
OTHER_VARIANT = "pulmonary_edema_75f"
CASE_AUTHORED, CASE_MAPPING, FAMILY_CANDIDATE, SYNTHETIC_ONLY = ar.CASE_AUTHORED, ar.CASE_MAPPING, ar.FAMILY_CANDIDATE, \
    ar.SYNTHETIC_ONLY
LEVEL_OF = ar.LEVEL_OF
INTRINSIC_RR = ar.INTRINSIC_RR     # acid_base.INTRINSIC_RR[1] (P2K-2 candidate input 12 / 16 / 20), as for ACS


@functools.lru_cache(maxsize=None)
def bank_case(case: str = CASE) -> dict:
    """The case exactly as the bank holds it."""
    import clinical_cases
    return next(c for c in clinical_cases.FAMILIES[FAMILY]["variants"] if c["id"] == case)


def _at(path: tuple, case: str = CASE):
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
    "lactate_mmol_l": ("investigations", "lactate", "result", "lactate_mmol_l"),
    "hb_g_dl": ("investigations", "basic_labs", "result", "hemoglobin_g_dl"),
    "glucose_mg_dl": ("investigations", "basic_labs", "result", "glucose_mg_dl"),
    "potassium_mmol_l": ("investigations", "basic_labs", "result", "potassium_mmol_l"),
    "creatinine_mg_dl": ("investigations", "basic_labs", "result", "creatinine_mg_dl"),
    "abg_ph": ("investigations", "abg", "result", "ph"), "abg_paco2": ("investigations", "abg", "result", "paco2_mm_hg"),
    "abg_pao2": ("investigations", "abg", "result", "pao2_mm_hg"),
    "abg_hco3": ("investigations", "abg", "result", "bicarbonate_mmol_l"),
    "abg_fio2_percent": ("investigations", "abg", "result", "fio2_percent"),
    "vbg_ph": ("investigations", "vbg", "result", "ph"), "vbg_pco2": ("investigations", "vbg", "result", "pco2_mm_hg"),
    "troponin_ng_l": ("investigations", "troponin", "result", "value_ng_l"),
    "ecg_profile": ("ecg_profile",), "pocus_lv": ("investigations", "pocus", "result", "lv"),
    "pocus_ivc": ("investigations", "pocus", "result", "ivc"), "pocus_lungs": ("investigations", "pocus", "result", "lungs"),
    "pocus_consolidation": ("investigations", "pocus", "result", "lung_consolidation"),
    "chest_xray": ("investigations", "chest_xray", "result", "report"),
    "respiratory_exam": ("examination", "Respiratory"), "cardiac_exam": ("examination", "Cardiac"),
    "neurological_exam": ("examination", "Neurological"),
    "onset": ("history", "onset"), "definitive_actions": ("engine", "definitive_actions"),
    "congestion_block": ("engine", "congestion"), "diagnosis": ("faculty", "diagnosis")}


def truth() -> dict:
    out = {}
    for item, path in TRUTH_PATHS.items():
        try:
            out[item] = _at(path)
        except (KeyError, TypeError):
            out[item] = None
    return out


def authored_map(t: dict | None = None) -> float:
    t = truth() if t is None else t
    return (t["sbp"] + 2.0 * t["dbp"]) / 3.0


# B. Arrival mapping ----------------------------------------------------------------------------------------------------------

Band = ar.Band


def bands() -> dict:
    """The arrival values the case does not state that the GI rule maps (same numbers, same reasoning)."""
    t = truth()
    low, mid, high = gi_reference.BASELINE_LACTATE
    rest_low, rest_mid, rest_high = gi_reference.RESTING_HR
    return {b.name: b for b in (
        Band("arrival_lactate_excess", round(t["lactate_mmol_l"] - high, 6), round(t["lactate_mmol_l"] - low, 6),
             round(t["lactate_mmol_l"] - mid, 6), CASE_MAPPING,
             "gi_reference.lactate_excess_band's rule: the arrival lactate less a non-shock clearance baseline of "
             "0.8-2.0 mmol/L; the baseline is not stated"),
        Band("intrinsic_sinus_rate", rest_low, min(rest_high, t["hr"]), min(rest_mid, t["hr"]), CASE_MAPPING,
             "gi_reference.intrinsic_hr_band's rule: the resting adult sinus rate, at most the observed HR; no "
             "beta-blocker or rate control is authored (an unnamed antihypertensive, missed for four days)"))}


#: Classification of every arrival field: all ARRIVAL_MAPPING, none a common equation.
ARRIVAL_CLASSES = {
    "sbp": CASE_AUTHORED, "dbp": CASE_AUTHORED, "hr": CASE_AUTHORED, "spo2": CASE_AUTHORED,
    "respiratory_rate": CASE_AUTHORED, "crt_s": CASE_AUTHORED, "lactate": CASE_AUTHORED, "hb": CASE_AUTHORED,
    "glucose": CASE_AUTHORED, "k": CASE_AUTHORED, "fio2": CASE_AUTHORED, "rhythm": CASE_AUTHORED,
    "consciousness_level": CASE_AUTHORED, "arrival_bicarbonate": CASE_AUTHORED, "arrival_paco2": CASE_AUTHORED,
    "preload_fraction": "CASE_MAPPING_GAP (the IVC 2.4 cm with <50% collapse and the raised JVP read a full filling "
                        "state, but the case's own congestion block says little excess circulating volume "
                        "(volume_overload false); no common IVC -> fraction rule exists, so the profile's provisional "
                        "position stays, nothing declared; B-lines are not read)",
    "pump_reserve": "CASE_MAPPING (neutral 1, nothing declared: read only by the common overload coupling, which the "
                    "family's authority keeps off; the moderately reduced LV is an observation of P, never a reserve "
                    "value; B-lines are never pump evidence)",
    "arrival_delivery_ratio": "CASE_MAPPING (neutral 1: perfusion authored as preserved, warm extremities, CRT 2 s)",
    "arrival_oxygen_debt": "CASE_MAPPING (neutral 0: no delivery deficit is read, so no pre-arrival debt is declared; "
                           "never computed from the lactate)",
    "beta_blockade": "CASE_MAPPING (0: no beta-blocker authored)",
    "metabolic_demand_baseline": "CASE_MAPPING (1: afebrile 36.6, no hypermetabolic evidence; the respiratory muscles' "
                                 "demand under severe work of breathing is not modelled)",
    "reference_preload_fraction": "UNDEFINED_BY_CASE (no euvolemic reference is authored)",
    "intrinsic_respiratory_rate": "FAMILY_CANDIDATE (P2K-2's candidate input, the middle of its 12 / 16 / 20)",
    "reversible_lung_water": "CASE/FAMILY REFERENCE PARAMETER at its default 0 (P2O-3): no authored observation "
                             "after arrival states an improvement below the arrival congestion",
    **{name: band.classification for name, band in bands().items()}}
#: The channels at arrival (P2P-1 channel interpretation), checked rather than forced.
CHANNEL_ROLES = {
    "V": "NORMAL_OR_NEUTRAL (no excess circulating volume by the case's congestion block; the full IVC and JVP read a "
         "full filling state, mapped to no V deviation)",
    "T": "PRIMARY_DRIVER (the precipitant: uncontrolled hypertension, SBP 218 after missing antihypertensives; T = 1 "
         "is that arrival tone; its coupling to congestion is not modelled: the family writer does not read T)",
    "P": "NORMAL_OR_NEUTRAL (P = 1 is the authored moderately reduced LV; no ischaemic process: a single troponin 28)",
    "R": "SECONDARY_RESPONSE (sinus tachycardia 126)",
    "L": "PRIMARY_DRIVER (diffuse bilateral B-lines, widespread crackles, perihilar edema on the radiograph)",
    "G": "SECONDARY_RESPONSE (severe hypoxaemia: SpO2 81, PaO2 46 on room air)",
    "W": "SECONDARY_RESPONSE (RR 38, severe work of breathing, PaCO2 49 with pH 7.29: ventilation failing)",
    "D": "NORMAL_OR_NEUTRAL (perfusion preserved; lactate 2.8 mapped as clearable excess, no prior debt)",
    "N": "NORMAL_OR_NEUTRAL (awake, oriented, distressed)",
    "Hb": "NORMAL_OR_NEUTRAL (14.3)", "Glu": "NORMAL_OR_NEUTRAL (148: mild stress hyperglycaemia)",
    "K": "NORMAL_OR_NEUTRAL (4.1)"}


def anchors(point: str = "midpoint", **changes) -> Anchors:
    """The case's arrival anchors: authored values exactly, the GI-rule bands at ``point``, every value the case does not
    state declared as a synthetic probe (never as case truth or an approved default)."""
    t = truth()
    b = bands()
    candidates = {"arrival_lactate_excess": getattr(b["arrival_lactate_excess"], point),
                  "intrinsic_sinus_rate": getattr(b["intrinsic_sinus_rate"], point), **changes}
    if not str(t["rhythm"]).lower().startswith("sinus"):
        raise ValueError("only a sinus arrival is anchored")
    return Anchors(case_id=CASE, sbp=float(t["sbp"]), dbp=float(t["dbp"]), hr=float(t["hr"]), spo2=float(t["spo2"]),
                   respiratory_rate=float(t["respiratory_rate"]), crt_s=float(t["crt_s"]),
                   lactate=float(t["lactate_mmol_l"]), hb=float(t["hb_g_dl"]), glucose=float(t["glucose_mg_dl"]),
                   k=float(t["potassium_mmol_l"]), fio2=t["abg_fio2_percent"] / 100.0,
                   rhythm=RhythmState(RhythmCode.SINUS, float(t["hr"]), 1.0, True),
                   consciousness_level=LEVEL_OF[t["mental_status"]],
                   intrinsic_respiratory_rate=INTRINSIC_RR, arrival_bicarbonate=float(t["abg_hco3"]),
                   arrival_paco2=float(t["abg_paco2"]),
                   declared={name: "synthetic_probe" for name in candidates if name in ar._CASE_PARAMETER_NAMES},
                   **candidates)


# C. The common reference profile ---------------------------------------------------------------------------------------------

def common_profile(**changes):
    """acs_reference.common_profile: the ACS package's predeclared point of the common uncertainty, unchanged."""
    return ar.common_profile(**changes)


# Observation layer: what the family shows, read from the common state, never a channel ----------------------------------------

OBSERVATION_LAYER = {
    "b_lines_crackles_radiograph": "an observation of L: the authored diffuse B-lines, widespread crackles and "
                                   "perihilar edema are the arrival reading (L = 0 is that congestion, never dry lungs); "
                                   "L above 0 reads more congestion, L back at 0 the arrival finding again",
    "lv_function": "an observation of P: the authored moderately reduced global contraction is the arrival reading (P = 1)",
    "ivc_jvp": "an observation of the filling state (V and the preload position), never of L",
    "work_of_breathing": "an observation of W and the respiratory load; the common model has no congestion-driven drive "
                         "or mechanics (an expected respiratory extension)",
    "rhythm": "R (sinus, its rate from the common HR physiology)"}
