"""P2N-2: acs_70f_left_main's repository truth, its arrival mapping and the common reference profile it runs on.

Shadow only. Nothing here is a default the core uses. Kept apart, as P2F-5 does for the GI cases:
- A. repository truth: read from the case bank itself (``clinical_cases.py``), by path, never retyped;
- B. arrival mapping: each value the case does not state is a band with its own rationale, built by the same rule the GI
  cases use where one exists (gi_reference), declared ``synthetic_probe`` so the migration gate keeps blocking it, and
  classified CASE_AUTHORED / CASE_MAPPING / FAMILY_CANDIDATE / SYNTHETIC_ONLY; none is FACULTY_APPROVED_COMMON;
- C. the common reference profile: one point of the common uncertainty already carried by the GI packages (each value
  with its source), chosen by a predeclared rule before any ACS run, never because it fits this case.

No history is inferred: the authored onset (60 min) is read as truth, nothing is assumed about the shock's or the
ischaemia's duration, fluids, catecholamines or medication effects. The arrival oxygen debt D is a latent arrival-state
variable on the variable's own scale; it is never computed from the arrival lactate (there is no lactate -> D rule).
"""
from __future__ import annotations

import functools
from dataclasses import dataclass, replace

from . import gi_reference
from .derived import DEFAULT_PROFILE
from .state import Anchors, RhythmCode, RhythmState

CASE, FAMILY = "acs_70f_left_main", "acs"
CASE_AUTHORED, CASE_MAPPING, FAMILY_CANDIDATE, SYNTHETIC_ONLY = ("CASE_AUTHORED", "CASE_MAPPING", "FAMILY_CANDIDATE",
                                                                 "SYNTHETIC_ONLY")
ARRIVAL_MAPPING = "ARRIVAL_MAPPING"
LEVEL_OF = {"Alert": 0, "Drowsy": 1, "Obtunded": 2, "Unresponsive": 3}
#: Common values the mapping reads, written here with their source (see COMMON_REFERENCE).
RESERVE = 2.5                      # vascular_tone.RESERVE (P2I-2P)
INTRINSIC_RR = 16.0                # acid_base.INTRINSIC_RR[1] (P2K-2 candidate input 12 / 16 / 20)


@functools.lru_cache(maxsize=None)
def bank_case() -> dict:
    """The case exactly as the bank holds it."""
    import clinical_cases
    return next(case for case in clinical_cases.FAMILIES[FAMILY]["variants"] if case["id"] == CASE)


def _at(path: tuple):
    value = bank_case()
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
    "troponin_ng_l": ("investigations", "troponin", "result", "value_ng_l"),
    "ecg_profile": ("ecg_profile",), "pocus_lv": ("investigations", "pocus", "result", "lv"),
    "pocus_ivc": ("investigations", "pocus", "result", "ivc"), "pocus_lungs": ("investigations", "pocus", "result", "lungs"),
    "chest_xray": ("investigations", "chest_xray", "result", "report"),
    "respiratory_exam": ("examination", "Respiratory"), "cardiac_exam": ("examination", "Cardiac"),
    "definitive_actions": ("engine", "definitive_actions"), "coronary": ("engine", "coronary"),
    "diagnosis": ("faculty", "diagnosis")}


def truth() -> dict:
    return {item: _at(path) for item, path in TRUTH_PATHS.items()}


def authored_map(t: dict | None = None) -> float:
    t = truth() if t is None else t
    return (t["sbp"] + 2.0 * t["dbp"]) / 3.0


# B. Arrival mapping ----------------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Band:
    name: str
    lower: float
    upper: float
    midpoint: float
    classification: str
    rule: str


def bands() -> dict:
    """Every arrival value the case does not state, by the GI rule where one exists (same numbers, same reasoning)."""
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
             "beta-blocker or rate control is authored (metformin, losartan, statin)"),
        Band("arrival_oxygen_debt", 0.0, 60.0, 20.0, FAMILY_CANDIDATE,
             "gi_reference.arrival_debt_band's scale (0-60 index-minutes, the same for every case): a latent "
             "arrival-state variable, never computed from the arrival lactate; the authored onset (60 min) does not "
             "set it (no history is reconstructed)"),
        Band("arrival_delivery_ratio", 0.6 / RESERVE, 1.0 / RESERVE, 0.85 / RESERVE, FAMILY_CANDIDATE,
             "gi_reference.delivery_ratio_band (0.6-1.0, at or below adequacy: cool extremities, CRT 3 s, mildly "
             "impaired perfusion, lactate 3.1) read under the extraction reserve as ratio / reserve (P2I-2P), as every "
             "GI package does"),
        Band("pump_reserve", 0.3, 0.7, 0.5, FAMILY_CANDIDATE,
             "the case shows reduced reserve (globally mildly reduced LV contraction, bibasal B-lines, mild "
             "congestion on the radiograph, basal crackles, troponin 260): below the GI band's 0.7-1.0, which had no "
             "such evidence; the value is not stated: faculty decision"))}


#: Classification of every arrival field (P2N-2A, P2N-2Q): all ARRIVAL_MAPPING, none a common equation.
ARRIVAL_CLASSES = {
    "sbp": CASE_AUTHORED, "dbp": CASE_AUTHORED, "hr": CASE_AUTHORED, "spo2": CASE_AUTHORED,
    "respiratory_rate": CASE_AUTHORED, "crt_s": CASE_AUTHORED, "lactate": CASE_AUTHORED, "hb": CASE_AUTHORED,
    "glucose": CASE_AUTHORED, "k": CASE_AUTHORED, "fio2": CASE_AUTHORED, "rhythm": CASE_AUTHORED,
    "consciousness_level": CASE_AUTHORED, "arrival_bicarbonate": CASE_AUTHORED, "arrival_paco2": CASE_AUTHORED,
    "preload_fraction": "CASE_MAPPING (neutral: IVC 1.9 cm with ~50% collapse is neither collapsing nor plethoric; "
                        "the profile's provisional arrival position, nothing declared)",
    "beta_blockade": "CASE_MAPPING (0: no beta-blocker authored)",
    "metabolic_demand_baseline": "CASE_MAPPING (1: afebrile 36.9, alert, no hypermetabolic evidence; gi_reference."
                                 "demand_band's rule)",
    "intrinsic_respiratory_rate": "FAMILY_CANDIDATE (P2K-2's candidate input, the middle of its 12 / 16 / 20)",
    **{name: band.classification for name, band in bands().items()}}
#: The channels at arrival (P2N-2 channel interpretation), checked rather than forced.
CHANNEL_ROLES = {"V": "NORMAL_OR_NEUTRAL", "T": "SECONDARY_RESPONSE", "P": "PRIMARY_DRIVER",
                 "R": "SECONDARY_RESPONSE (sinus tachycardia)", "L": "SECONDARY_RESPONSE (congestion present)",
                 "G": "SECONDARY_RESPONSE (mild gas-exchange impairment)", "W": "SECONDARY_RESPONSE",
                 "D": "SECONDARY_RESPONSE (prior oxygen-delivery debt)", "N": "NORMAL_OR_NEUTRAL"}


def arrival_oxygen_debt(point: str = "midpoint") -> float:
    """The latent arrival D at a band point. It takes no lactate: no lactate -> D rule exists."""
    return getattr(bands()["arrival_oxygen_debt"], point)


def anchors(point: str = "midpoint", **changes) -> Anchors:
    """The case's arrival anchors: authored values exactly, the mapping's bands at ``point``, every value the case does
    not state declared as a synthetic probe (never as case truth or an approved default)."""
    t = truth()
    b = bands()
    candidates = {"arrival_lactate_excess": getattr(b["arrival_lactate_excess"], point),
                  "intrinsic_sinus_rate": getattr(b["intrinsic_sinus_rate"], point),
                  "arrival_oxygen_debt": arrival_oxygen_debt(point),
                  "arrival_delivery_ratio": getattr(b["arrival_delivery_ratio"], point),
                  "pump_reserve": getattr(b["pump_reserve"], point), **changes}
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
                   declared={name: "synthetic_probe" for name in candidates if name in _CASE_PARAMETER_NAMES},
                   **candidates)


_CASE_PARAMETER_NAMES = ("arrival_lactate_excess", "intrinsic_sinus_rate", "arrival_oxygen_debt",
                         "arrival_delivery_ratio", "pump_reserve", "preload_fraction", "metabolic_demand_baseline",
                         "beta_blockade", "reference_preload_fraction")


# C. The common reference profile ---------------------------------------------------------------------------------------------

#: One point of the common uncertainty the GI packages carry, by a predeclared rule (the middle of each committed set;
#: the P2J-4 probe gains for the HR drives), fixed before any ACS run. Nothing here is approved. The values are written
#: here, with their source, because this module stays in the P2G pack digest and may not import the analysis modules
#: that hold them; the tests check each against its source exactly.
COMMON_REFERENCE = {
    "oxygen_extraction_reserve": (RESERVE, "vascular_tone.RESERVE: the P2I-2P reserve, every GI package"),
    "deficit_to_tone_gain": (0.5, "baroreflex.TONE_GAINS[1]: P2J-3 primary tone gains 0.25 / 0.5 / 1.0, the middle"),
    "afterload_sensitivity": (0.3, "baroreflex.AFTERLOAD: P2J-1 / P2J-4 afterload"),
    "acute_deficit_to_sympathetic_gain": (1.0, "baroreflex.PROBE_GAINS['acute']: P2J-4 probe gains"),
    "debt_to_sympathetic_gain": (0.01, "baroreflex.PROBE_GAINS['debt']: P2J-4 probe gains"),
    "baroreflex_to_sympathetic_gain": (1.0, "baroreflex.PROBE_GAINS['baro']: P2J-4 probe gains (inside 0.25-1.5)"),
    "baroreflex_map_set_mmhg": (90.0, "baroreflex.MAP_SETS[1]: P2J-4 exploratory MAP set 80 / 90 / 100, the middle"),
    "sympathetic_per_pressure_deficit": (0.0, "retired whenever the baroreflex is active (P2J-4)"),
    "debt_clearance_tau_min": (60.0, "blood_anchors.KINETICS; lambda set 30 / 60 / 120: the middle"),
    "debt_per_delivery_deficit": (1.0, "lambda set 0.5 / 1 / 2: the middle"),
    "debt_to_lactate_gain": (0.00024532669073132904, "lactate_closure.K_LD[2]: P2I-2AD k_LD's five points, the middle"),
    "lactate_clearance_tau_min": (120.0, "blood_anchors.KINETICS; lambda set 45 / 120 / 240: the middle"),
    "acid": ((2.0, 19.4, 120.0), "acid_base DRIVE_GAINS[2], STEADY_BURDENS[1], ACID_TAUS[1]: P2K-2 drive gain 1-4, "
                                 "B 13.4 / 19.4 / 28, tau 60 / 120 / 240, the middles; acid_base.candidate_profile's "
                                 "construction (efficiency 1)")}
#: The tone gain is the primary carried common uncertainty: a 1-D sensitivity, nothing else is swept.
TONE_SENSITIVITY = (0.25, 0.5, 1.0)  # baroreflex.TONE_GAINS


def common_profile(**changes):
    values = {k: v for k, (v, _) in COMMON_REFERENCE.items() if k != "acid"}
    gain, b, tau = COMMON_REFERENCE["acid"][0]
    # acid_base.candidate_profile: the acid gain is B / tau, the clearance tau, the drive gain, efficiency 1.
    acid = {"deficit_to_acid_gain": b / tau, "acid_clearance_tau_min": tau, "acid_to_drive_gain": gain,
            "ventilation_efficiency": 1.0}
    return replace(DEFAULT_PROFILE, **{**values, **acid, **changes})


# Observation layer (P2N-2F): what the family shows, read from the common state, never a channel ------------------------------

OBSERVATION_LAYER = {
    "lv_function": "an observation of P: the authored 'globally mildly reduced contraction' is the arrival reading "
                   "(P = 1 with the reduced reserve and delivery the arrival layer declares); a fall of P from arrival "
                   "reads worse, a recovery toward 1 reads back to the authored finding",
    "ecg_ischaemia": "a family observation (diffuse ST depression with aVR elevation while the artery is occluded); no "
                     "common channel",
    "b_lines_congestion": "an observation of L: the authored bibasal B-lines and mild congestion are the arrival "
                          "reading (L = 0 is arrival); L above 0 reads more congestion",
    "rhythm": "R (sinus, its rate from the common HR physiology)",
    "troponin": "a family observation (the legacy curve is LEGACY_REFERENCE_ONLY); no common channel"}
