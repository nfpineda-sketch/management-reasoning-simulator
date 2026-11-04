"""P2Q-2: the pulmonary-embolism cases' repository truth, their arrival mapping and the common reference profile.

Shadow only. Nothing here is a default the core uses. Kept apart, as P2N-2 (acs_reference) and P2P-1 (edema_reference) do:
- A. repository truth: read from the case bank itself (``clinical_cases.py``), by path, never retyped;
- B. arrival mapping: each value a case does not state is neutral or a band built by the rule the GI and ACS packages
  use where one exists (gi_reference), declared ``synthetic_probe`` so the migration gate keeps blocking it, and
  classified CASE_AUTHORED / CASE_MAPPING / FAMILY_CANDIDATE / SYNTHETIC_ONLY; none is FACULTY_APPROVED_COMMON;
- C. the common reference profile: the ACS package's predeclared point of the common uncertainty (acs_reference), the
  same values, chosen before any PE run, never because it fits these cases.

Faculty decisions (P2Q-2): V, the common effective forward-preload coordinate, is read from the authored LV filling (a
small, underfilled LV), never from the plethoric IVC or the raised jugular veins: in obstructive right-ventricular
failure a full right heart and an underfilled left ventricle coexist, so the IVC is not a universal proxy for V
(IVC_IS_NOT_UNIVERSAL_V_MAPPING); the IVC and the JVP stay RIGHT_SIDED / OBSERVATIONAL evidence. L is family-owned with
zero generation unless a case independently authors pulmonary edema (PE_L_ZERO_OWNER_AUTHORIZED). No sided preload,
pressure or pump state is added (SIDED_PRELOAD_COMMON_STATE_DEFERRED).
"""
from __future__ import annotations

import functools

from . import acs_reference as ar
from . import gi_reference
from .state import Anchors, RhythmCode, RhythmState

CASE, SECONDARY, FAMILY = "pulmonary_embolism_61m", "pulmonary_embolism_33f", "pulmonary_embolism"
CASES = (CASE, SECONDARY)
#: The cases, by the rule P2Q-1 predeclared and the faculty accepted: the primary is the variant with the richest authored
#: RV, preload, gas-exchange and haemodynamic physiology (obstructive shock); the secondary tests hypoxaemia / G without
#: major hypotension.
SELECTION_RULE = ("primary: the variant with the richest authored RV, preload, gas-exchange and haemodynamic physiology "
                  "(pulmonary_embolism_61m, high-risk PE with obstructive shock); secondary diagnostic: "
                  "pulmonary_embolism_33f (PE with hypoxaemia, initially without hypotension)")
CASE_AUTHORED, CASE_MAPPING, FAMILY_CANDIDATE, SYNTHETIC_ONLY = ar.CASE_AUTHORED, ar.CASE_MAPPING, ar.FAMILY_CANDIDATE, \
    ar.SYNTHETIC_ONLY
LEVEL_OF = ar.LEVEL_OF
INTRINSIC_RR = ar.INTRINSIC_RR     # acid_base.INTRINSIC_RR[1] (P2K-2 candidate input 12 / 16 / 20), as for ACS and edema


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
    "d_dimer_ng_ml": ("investigations", "d_dimer", "result", "d_dimer_ng_ml_feu"),
    "ecg_profile": ("ecg_profile",), "pocus_lv": ("investigations", "pocus", "result", "lv"),
    "pocus_rv": ("investigations", "pocus", "result", "rv"), "pocus_ivc": ("investigations", "pocus", "result", "ivc"),
    "pocus_lungs": ("investigations", "pocus", "result", "lungs"),
    "pocus_consolidation": ("investigations", "pocus", "result", "lung_consolidation"),
    "pocus_dvt_popliteal": ("investigations", "pocus", "result", "dvt_popliteal"),
    "chest_xray": ("investigations", "chest_xray", "result", "report"),
    "ctpa": ("investigations", "ctpa", "result", "report"),
    "respiratory_exam": ("examination", "Respiratory"), "cardiac_exam": ("examination", "Cardiac"),
    "neurological_exam": ("examination", "Neurological"), "extremities_exam": ("examination", "Extremities"),
    "onset": ("history", "onset"), "definitive_actions": ("engine", "definitive_actions"),
    "diagnosis": ("faculty", "diagnosis")}


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
#: The evidence each common coordinate reads (faculty decisions, P2Q-2). V: the authored LV filling only. The IVC and the
#: jugular veins (and the RV itself) are right-sided observations: they never inform V, L or the pump reserve.
V_EVIDENCE = ("pocus_lv",)
RIGHT_SIDED_OBSERVATION = ("pocus_ivc", "cardiac_exam", "pocus_rv")
L_EVIDENCE = ("pocus_lungs", "chest_xray", "respiratory_exam")


def lv_underfilled(case: str = CASE, t: dict | None = None) -> bool:
    """Whether the authored LV reads underfilled: the only evidence the preload mapping takes (V_EVIDENCE)."""
    t = truth(case) if t is None else t
    return "underfilled" in str(t["pocus_lv"]).lower()


#: The neutral arrival position (derived.CoreProfile.arrival_preload_fraction's default, PROVISIONAL): "underfilled"
#: never places arrival above it. Written here because the reference does not import the profile; the tests check it.
NEUTRAL_PRELOAD_POSITION = 0.5


def preload_band(case: str = CASE, t: dict | None = None) -> Band | None:
    """The arrival preload position from LV underfilling alone (V_EVIDENCE), or None (the profile's provisional position,
    nothing declared) when the LV is not read as underfilled. The IVC is never read here.

    Only the scale is borrowed: no common rule maps an LV finding alone to a position. The GI bands
    (gi_reference.PRELOAD_BANDS) were built from a collapsing IVC together with a small or hyperdynamic LV in
    hypovolaemic cases, so neither GI band is transferred as such: the band runs from the deepest GI underfilling point
    (their lowest bound) up to the neutral position (an underfilled LV is never above neutral), its midpoint the middle.
    The magnitude is FAMILY_CANDIDATE, the faculty's to set."""
    if not lv_underfilled(case, t):
        return None
    low = min(b[0] for b in gi_reference.PRELOAD_BANDS.values())
    high = NEUTRAL_PRELOAD_POSITION
    return Band("preload_fraction", low, high, (low + high) / 2.0, FAMILY_CANDIDATE,
                "the authored small, underfilled LV with vigorous contraction (V_EVIDENCE) places arrival below the "
                "neutral position: from the deepest GI underfilling point (min of gi_reference.PRELOAD_BANDS, whose GI "
                "bands also read a collapsing IVC and are not transferred as such) up to the neutral position, midpoint "
                "the middle; the plethoric IVC and the raised JVP are right-sided observations and are not read "
                "(IVC_IS_NOT_UNIVERSAL_V_MAPPING); the magnitude is the faculty's")


def impaired_perfusion(case: str = CASE, t: dict | None = None) -> bool:
    t = truth(case) if t is None else t
    return str(t["peripheral_perfusion"]).lower() == "impaired"


#: Terms that would author pulmonary congestion in an L_EVIDENCE text, and the markers that negate a term within its clause.
EDEMA_TERMS = ("b-line", "edema", "oedema", "crackle", "congestion")
NEGATIONS = ("no ", "without ")


def _clauses(text: str) -> list:
    text = str(text).lower()
    for separator in (";", ".", " but ", " however"):
        text = text.replace(separator, "|")
    return [c.strip() for c in text.split("|") if c.strip()]


def authored_pulmonary_edema(case: str = CASE) -> bool:
    """Whether the case independently authors pulmonary edema, read on every L_EVIDENCE text (the POCUS lungs, the
    radiograph, the respiratory examination): a congestion term in a clause with no negation before it authors edema.
    The reading fails closed: an unnegated term anywhere reads edema, and the owner's zero generation is then refused
    (``lung_water_generation``)."""
    t = truth(case)
    for item in L_EVIDENCE:
        for clause in _clauses(t[item]):
            for term in EDEMA_TERMS:
                at = clause.find(term)
                if at >= 0 and not any(n in clause[:at] for n in NEGATIONS):
                    return True
    return False


def lung_water_generation(case: str = CASE) -> float:
    """The family L owner's own generation: zero without authored pulmonary edema (PE_L_ZERO_OWNER_AUTHORIZED). With
    authored edema the rate is the faculty's, not chosen here."""
    if authored_pulmonary_edema(case):
        raise ValueError(f"{case} authors pulmonary edema: its generation rate is a faculty decision")
    return 0.0


def bands(case: str = CASE, t: dict | None = None) -> dict:
    """The arrival values the case does not state, by the GI rule where one exists (same numbers, same reasoning)."""
    t = truth(case) if t is None else t
    low, mid, high = gi_reference.BASELINE_LACTATE
    rest_low, rest_mid, rest_high = gi_reference.RESTING_HR
    out = [
        Band("arrival_lactate_excess", round(t["lactate_mmol_l"] - high, 6), round(t["lactate_mmol_l"] - low, 6),
             round(t["lactate_mmol_l"] - mid, 6), CASE_MAPPING,
             "gi_reference.lactate_excess_band's rule: the arrival lactate less a non-shock clearance baseline of "
             "0.8-2.0 mmol/L; the baseline is not stated"),
        Band("intrinsic_sinus_rate", rest_low, min(rest_high, t["hr"]), min(rest_mid, t["hr"]), CASE_MAPPING,
             "gi_reference.intrinsic_hr_band's rule: the resting adult sinus rate, at most the observed HR; no "
             "beta-blocker or rate control is authored")]
    if impaired_perfusion(case, t):
        delivery = gi_reference.delivery_ratio_band(gi_reference.GI_CASES[0])
        debt = gi_reference.arrival_debt_band(gi_reference.GI_CASES[0])
        out += [
            Band("arrival_delivery_ratio", delivery.lower / ar.RESERVE, delivery.upper / ar.RESERVE,
                 delivery.midpoint / ar.RESERVE, FAMILY_CANDIDATE,
                 "gi_reference.delivery_ratio_band (0.6-1.0, at or below adequacy: CRT 5 s, cool extremities, impaired "
                 "perfusion, hypotension, lactate 4.8) read under the extraction reserve as ratio / reserve (P2I-2P), "
                 "as ACS does"),
            Band("arrival_oxygen_debt", debt.lower, debt.upper, debt.midpoint, FAMILY_CANDIDATE,
                 "gi_reference.arrival_debt_band's scale (0-60 index-minutes, the same for every case): a latent "
                 "arrival-state variable constrained by the authored shock, never computed from the arrival lactate; "
                 "the authored onset (45 min) does not set it (no history is reconstructed)")]
    preload = preload_band(case, t)
    if preload is not None:
        out.append(preload)
    return {b.name: b for b in out}


def _classes(case: str) -> dict:
    t = truth(case)
    shock = impaired_perfusion(case)
    return {
        "sbp": CASE_AUTHORED, "dbp": CASE_AUTHORED, "hr": CASE_AUTHORED, "spo2": CASE_AUTHORED,
        "respiratory_rate": CASE_AUTHORED, "crt_s": CASE_AUTHORED, "lactate": CASE_AUTHORED, "hb": CASE_AUTHORED,
        "glucose": CASE_AUTHORED, "k": CASE_AUTHORED, "fio2": CASE_AUTHORED, "rhythm": CASE_AUTHORED,
        "consciousness_level": CASE_AUTHORED, "arrival_bicarbonate": CASE_AUTHORED, "arrival_paco2": CASE_AUTHORED,
        "preload_fraction": (FAMILY_CANDIDATE + " (LV underfilling alone, V_EVIDENCE: see the band; the IVC is not read; "
                                                "the GI bands' IVC evidence is not transferred)") if lv_underfilled(case)
        else (CASE_MAPPING + f" (neutral: the authored LV '{t['pocus_lv']}' is not read as underfilled; the profile's "
                             "provisional position, nothing declared; the IVC is not read)"),
        "pump_reserve": CASE_MAPPING + " (neutral 1, nothing declared: read only by the common overload coupling, which "
                                       "the family's L authority keeps off; RV dysfunction is never a left reserve)",
        "arrival_delivery_ratio": FAMILY_CANDIDATE if shock else
        CASE_MAPPING + " (neutral 1: perfusion authored as preserved, warm extremities)",
        "arrival_oxygen_debt": FAMILY_CANDIDATE if shock else
        CASE_MAPPING + " (neutral 0: no delivery deficit is read, so no pre-arrival debt; never from the lactate)",
        "beta_blockade": CASE_MAPPING + " (0: no beta-blocker authored)",
        "metabolic_demand_baseline": CASE_MAPPING + " (1: afebrile, no hypermetabolic evidence; the respiratory "
                                                    "muscles' demand under the authored work of breathing is not modelled)",
        "reference_preload_fraction": "UNDEFINED_BY_CASE (no euvolemic reference is authored)",
        "intrinsic_respiratory_rate": FAMILY_CANDIDATE + " (P2K-2's candidate input, the middle of its 12 / 16 / 20)",
        "reversible_lung_water": CASE_MAPPING + " (default 0: no authored pulmonary edema; L is family-owned at zero "
                                                "generation)",
        **{name: band.classification for name, band in bands(case).items()}}


ARRIVAL_CLASSES = {case: _classes(case) for case in CASES}
#: The channels at arrival (P2Q-2 channel interpretation), checked rather than forced.
CHANNEL_ROLES = {
    CASE: {
        "V": "NORMAL_OR_NEUTRAL as a deviation (V = 0 at arrival; no volume lost or gained); its arrival POSITION is the "
             "underfilled LV's (low on the preload curve). Never the plethoric IVC (IVC_IS_NOT_UNIVERSAL_V_MAPPING)",
        "T": "SECONDARY_RESPONSE (vasoconstriction: the existing common tone response to the deficit)",
        "P": "PRIMARY_DRIVER (the obstruction: unsided forward-flow capacity of the series circuit; not LV contractility, "
             "the authored LV contracts vigorously)",
        "R": "SECONDARY_RESPONSE (sinus tachycardia 132)",
        "L": "NORMAL_OR_NEUTRAL (no B-lines, no edema on the radiograph): family-owned at zero generation",
        "G": "PRIMARY_DRIVER (dead space / V/Q mismatch: SpO2 88, PaO2 55 on room air): direct, never through L",
        "W": "SECONDARY_RESPONSE (RR 32, markedly increased work, PaCO2 28: hyperventilation)",
        "D": "SECONDARY_RESPONSE (obstructive shock: a latent arrival debt, never from the lactate 4.8)",
        "N": "NORMAL_OR_NEUTRAL (alert, faint)",
        "Hb": "NORMAL_OR_NEUTRAL (11.6)", "Glu": "NORMAL_OR_NEUTRAL (136: stress)", "K": "NORMAL_OR_NEUTRAL (4.1)"},
    SECONDARY: {
        "V": "NORMAL_OR_NEUTRAL (V = 0; the LV is preserved, not read as underfilled: the profile's position)",
        "T": "NORMAL_OR_NEUTRAL (no shock)",
        "P": "NORMAL_OR_NEUTRAL at arrival (mild RV enlargement, no D-sign, no McConnell, normotension)",
        "R": "SECONDARY_RESPONSE (sinus tachycardia 124)",
        "L": "NORMAL_OR_NEUTRAL (no B-lines, no edema): family-owned at zero generation",
        "G": "PRIMARY_DRIVER (SpO2 90, PaO2 59 on room air): direct",
        "W": "SECONDARY_RESPONSE (RR 30, PaCO2 30)",
        "D": "NORMAL_OR_NEUTRAL (perfusion preserved; lactate 2.0 mapped as clearable excess, no prior debt)",
        "N": "NORMAL_OR_NEUTRAL (alert)",
        "Hb": "NORMAL_OR_NEUTRAL (12.6)", "Glu": "NORMAL_OR_NEUTRAL (108)", "K": "NORMAL_OR_NEUTRAL (4.1)"}}


def anchors(case: str = CASE, point: str = "midpoint", t: dict | None = None, **changes) -> Anchors:
    """The case's arrival anchors: authored values exactly, the mapping's bands at ``point``, every value the case does
    not state declared as a synthetic probe (never as case truth or an approved default). ``t`` replaces the bank's
    truth (an analysis probe only)."""
    t = truth(case) if t is None else t
    candidates = {name: getattr(band, point) for name, band in bands(case, t).items()}
    candidates.update(changes)
    if not str(t["rhythm"]).lower().startswith("sinus"):
        raise ValueError("only a sinus arrival is anchored")
    return Anchors(case_id=case, sbp=float(t["sbp"]), dbp=float(t["dbp"]), hr=float(t["hr"]), spo2=float(t["spo2"]),
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
    "rv_findings": "an observation of the obstruction (P): the authored RV larger than the LV, the D-sign and McConnell's "
                   "sign are the arrival reading (P = 1); P below arrival reads a more obstructed circuit",
    "lv_underfilled": "an observation of the arrival preload position (V_EVIDENCE): low on the curve; the vigorous "
                      "contraction says P is not LV contractility",
    "ivc_jvp": "RIGHT_SIDED / OBSERVATIONAL evidence: the plethoric IVC and the raised JVP are the obstructed right heart's "
               "filling; never V, never L, never the pump reserve (IVC_IS_NOT_UNIVERSAL_V_MAPPING)",
    "lungs": "an observation of L: no B-lines and no edema are the arrival reading (L = 0, family-owned, zero generation)",
    "ecg_ctpa_troponin_d_dimer": "family observations of the embolism; no common channel",
    "work_of_breathing": "an observation of W and the respiratory load; the common model has no dead-space, mechanics or "
                         "receptor drive (an expected respiratory extension); the hypoxaemic drive is UNSET",
    "rhythm": "R (sinus, its rate from the common HR physiology)"}
