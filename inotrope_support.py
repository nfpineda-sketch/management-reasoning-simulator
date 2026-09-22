"""Dobutamine in a bank encounter: output, pressure and rate, told apart.

Faculty decision 6 of 2026-09-21, from the full bank review. A left-main
cardiogenic shock refused the classic inotrope decision with a message about
"a generated encounter with an explicit response rule". The drug now exists in
every family, with the same engine, and it is never an automatic improvement:

  * it relieves the share of the low-output burden that is contractile, so it
    does most in an infarcting ventricle and little in an obstructed one;
  * the pressure is computed separately, because the output gain and the
    afterload fall pull in opposite directions and the fall wins at high rates;
  * it is always chronotropic, and above a dose the rate becomes the problem;
  * nothing here opens a coronary artery: the reperfusion is still owed.
"""

# Magnitudes are teaching parameters, not a pharmacological model.
HALF_EFFECT_MCG_KG_MIN = 5.0      # half of the maximum inotropic effect
MAX_BURDEN_RELIEF = .35           # units of circulation burden at saturation
ONSET_TAU_MIN = 3.0               # the haemodynamic change arrives in minutes
HR_PER_MCG_KG_MIN = 2.2           # chronotropy, with no ceiling of its own
VASODILATION_SBP_PER_MCG_KG_MIN = .9   # the afterload fall that fights the gain
ARRHYTHMIA_RATE_MCG_KG_MIN = 10.0      # above this the rate is the new problem
ARRHYTHMIA_EXTRA_HR = 14.0

# How much of this family's low-output burden a pure inotrope can relieve. An
# infarcting ventricle is contractile failure; an obstructed right ventricle, a
# bleeding circulation and a vasoplegic one are not.
CONTRACTILE_SHARE = {
    "acs": 1.0, "pulmonary_edema": .6, "pneumonia": .2, "pulmonary_embolism": .15,
    "gi_bleed": .1, "asthma": .1, "hypoglycemia": .1, "opioid": .1,
}


def rate_per_kg(state):
    """The running dobutamine rate in mcg/kg/min, from the stored mcg/min."""
    weight = float((state.get("encounter_spec", {}).get("clinical_case", {})
                    .get("patient", {}).get("weight_kg") or 70) or 70)
    return max(0.0, float(state["family_state"].get("dobutamine") or 0)) / max(1.0, weight)


def _saturating(rate):
    return MAX_BURDEN_RELIEF * rate / (rate + HALF_EFFECT_MCG_KG_MIN) if rate > 0 else 0.0


def step(state):
    """Advance the inotropic effect one minute; return an event or None."""
    f = state["family_state"]
    rate = rate_per_kg(state)
    target = _saturating(rate) * CONTRACTILE_SHARE.get(state.get("engine_family"), .2)
    effect = f.get("dobutamine_effect", 0.0)
    f["dobutamine_effect"] = effect + (target - effect) / ONSET_TAU_MIN
    if rate > ARRHYTHMIA_RATE_MCG_KG_MIN and not f.get("dobutamine_arrhythmia_reported"):
        f["dobutamine_arrhythmia_reported"] = True
        return (f"Dobutamine at {rate:.3g} mcg/kg/min: the rate climbs and frequent ventricular ectopy "
                "appears on the monitor. The inotrope is buying contraction with myocardial oxygen demand.")
    if rate <= ARRHYTHMIA_RATE_MCG_KG_MIN:
        f["dobutamine_arrhythmia_reported"] = False
    return None


def burden_relief(f):
    """Circulation burden the running inotrope is currently carrying."""
    return max(0.0, float(f.get("dobutamine_effect") or 0))


def surface(state):
    """(sbp_delta, hr_delta) the inotrope adds on top of the relieved burden."""
    rate = rate_per_kg(state)
    if rate <= 0:
        return 0.0, 0.0
    hr = HR_PER_MCG_KG_MIN * rate
    if rate > ARRHYTHMIA_RATE_MCG_KG_MIN:
        hr += ARRHYTHMIA_EXTRA_HR
    return -VASODILATION_SBP_PER_MCG_KG_MIN * rate, hr
