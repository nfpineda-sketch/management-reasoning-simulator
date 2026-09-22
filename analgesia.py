"""Morphine: analgesia, preload, consciousness and the price of each.

Faculty decision 10 of 2026-09-21, from the full bank review. "Indica morfina
3 mg IV" was not recognised in any family. The decision was that the drug
exists everywhere, that recognising the order is not the same as approving it,
and that its effects are told apart rather than bundled:

  * it relieves pain, and relieving pain does not open a coronary artery;
  * it venodilates, and what that costs depends on the patient: a
    preload-dependent right ventricle and a bleeding circulation pay most,
    a well-filled patient with a normal pressure pays almost nothing;
  * it sedates and depresses ventilation with dose and accumulation, so a
    respiratory rate that falls after morphine is not an improvement;
  * nausea and vomiting are frequent, not obligatory, and they are separate
    from the nausea the infarct itself causes.

Naloxone reverses what the morphine did, including the analgesia: the pain
comes back with the breathing.
"""

# Pain the case arrives with, when the case does not say otherwise, on 0-10.
ARRIVAL_PAIN = {"acs": 7.0, "gi_bleed": 2.0, "pulmonary_embolism": 4.0,
                "pneumonia": 2.0, "pulmonary_edema": 2.0, "asthma": 1.0,
                "hypoglycemia": 0.0, "opioid": 0.0}
RELIEF_HALF_MG = 4.0              # mg at which half the maximum relief is bought
MAX_RELIEF_POINTS = 7.0           # points of pain a saturating dose removes
ONSET_TAU_MIN = 4.0               # analgesia arrives over minutes
CLEARANCE_TAU_MIN = 150.0         # and the whole effect fades over hours

# Venodilation, as systolic mmHg per mg, before the patient's own vulnerability.
PRELOAD_SBP_PER_MG = 1.1
PRELOAD_TAU_MIN = 6.0
RV_FACTOR = 2.2                   # a right ventricle that lives on its preload
HYPOVOLEMIA_FACTOR = 2.0          # a circulation that is short of volume
WELL_FILLED_SBP = 130.0           # above this pressure the fall hardly shows
WELL_FILLED_FACTOR = .35

SEDATION_MG = 11.0                # cumulative mg at which consciousness dips
DEEP_SEDATION_MG = 9.0            # mg beyond that before it costs a second step
RR_PER_MG_ABOVE_SEDATION = .8
NAUSEA_MG = 6.0                   # dose at which a susceptible patient vomits
# Nausea is frequent, not obligatory: two patients in three are susceptible, and
# which one this is belongs to the case, not to the minute (2026-09-21).
NAUSEA_SUSCEPTIBLE_IN = 3


def arrival_pain(state):
    case = state.get("encounter_spec", {}).get("clinical_case", {})
    declared = case.get("observable", {}).get("pain_score")
    if declared is not None:
        return float(declared)
    return ARRIVAL_PAIN.get(state.get("engine_family"), 0.0)


def _vulnerability(state, sbp):
    """How much this patient's pressure depends on the preload morphine takes."""
    import acs_reperfusion
    family = state.get("engine_family")
    spec = acs_reperfusion.coronary(state) or {}
    if family == "acs" and spec.get("rv_involvement"):
        return RV_FACTOR
    if family == "gi_bleed":
        return HYPOVOLEMIA_FACTOR
    if sbp >= WELL_FILLED_SBP:
        return WELL_FILLED_FACTOR
    return 1.0


def step(state, sbp):
    """Advance morphine one minute; return an event or None."""
    f = state["family_state"]
    load = float(f.get("morphine_mg") or 0)
    if load <= 0 and not f.get("morphine_relief") and not f.get("morphine_preload_drop"):
        return None
    # The drug leaves slowly; naloxone removes its effect, not the drug.
    f["morphine_mg"] = load * (1 - 1 / CLEARANCE_TAU_MIN)
    active = max(0.0, f["morphine_mg"] - float(f.get("morphine_reversed_mg") or 0))
    target_relief = MAX_RELIEF_POINTS * active / (active + RELIEF_HALF_MG) if active > 0 else 0.0
    relief = f.get("morphine_relief", 0.0)
    f["morphine_relief"] = relief + (target_relief - relief) / ONSET_TAU_MIN
    target_drop = PRELOAD_SBP_PER_MG * active * _vulnerability(state, sbp)
    drop = f.get("morphine_preload_drop", 0.0)
    f["morphine_preload_drop"] = drop + (target_drop - drop) / PRELOAD_TAU_MIN
    susceptible = int(state.get("seed") or 0) % NAUSEA_SUSCEPTIBLE_IN != 0
    if susceptible and active >= NAUSEA_MG and not f.get("morphine_nausea_reported"):
        f["morphine_nausea_reported"] = True
        return ("The patient retches and vomits shortly after the morphine. It is the drug's own effect, "
                "not a new ischaemic symptom, and anything given by mouth is now of uncertain absorption.")
    return None


def pain(state):
    """The pain the patient reports now, on 0-10."""
    f = state["family_state"]
    base = float(f.get("pain_baseline", arrival_pain(state)))
    return max(0.0, min(10.0, base - float(f.get("morphine_relief") or 0)))


def descriptor(score):
    return ("no pain" if score < .5 else "mild pain" if score < 3
            else "moderate pain" if score < 6 else "severe pain")


def sedation(state):
    """(mental steps down, respiratory rate cost) from the morphine on board."""
    f = state["family_state"]
    active = max(0.0, float(f.get("morphine_mg") or 0) - float(f.get("morphine_reversed_mg") or 0))
    if active <= SEDATION_MG:
        return 0, 0.0
    excess = active - SEDATION_MG
    return (1 if excess < DEEP_SEDATION_MG else 2), RR_PER_MG_ABOVE_SEDATION * excess
