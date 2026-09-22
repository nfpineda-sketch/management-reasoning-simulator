"""Naloxone titrated to ventilation, not to consciousness (faculty, 2026-09-20).

The bank modelled a single decay for every opioid and no price for giving too
much naloxone. The faculty asked for three things: a long-acting opioid that
outlasts the antidote, so that boluses alone are not enough and an infusion is
the treatment; acute withdrawal when the antidote is pushed past what ventilation
needs; and an end for apnoea that is never supported.

Teaching magnitudes pending faculty review, and only the bank opioid family uses
them.
"""
# Faculty decision 2026-09-21: the short-acting opioid was barely moving inside
# the encounter (an eleven-hour half-life), so nothing the resident watched ever
# wore off. Four hours is the most acceleration that keeps the other teaching
# intact: an unsupported patient still arrests at twenty minutes, because the
# suppression has not yet lifted him above the apnoeic threshold.
DECAY_PER_MIN = .99712             # a short-acting opioid: a four-hour half-life
LONG_ACTING_DECAY_PER_MIN = .9997  # a long-acting one outlasts the encounter
NALOXONE_DECAY_PER_MIN = .975      # about twenty-seven minutes

# An infusion holds the antidote where a bolus cannot.
INFUSION_LEVEL_PER_MG_H = 2.5      # 0.4 mg/h holds a level of about 1.0

# Withdrawal: the price of titrating to consciousness. It is precipitated by the
# antidote that exceeds the agonist on board, not by an absolute dose (faculty,
# 2026-09-21): a heavier intoxication needs more naloxone before it withdraws,
# and a patient must never be depressed and withdrawing at the same time.
WITHDRAWAL_MARGIN = .2
WITHDRAWAL_LEVEL = 1.0 + WITHDRAWAL_MARGIN   # what it is for a case that arrives at 1.0
WITHDRAWAL_HR = 25
WITHDRAWAL_SBP = 20
WITHDRAWAL_RR = 6
WITHDRAWAL_TEXT = ("Acute withdrawal: the patient is agitated, retching and sweating, with a rising pressure and "
                   "rate. The target of the antidote is ventilation, not consciousness.")

# Apnoea nobody supports. The threshold is the depth of the ventilatory
# suppression rather than the rate the monitor renders, so that reshaping the
# dose-response curve (faculty decision 3b, 2026-09-21) cannot quietly remove
# the arrest this family is built on.
APNOEA_RR = 6
APNOEA_SPO2 = 80
APNOEA_SUPPRESSION = .85
ARREST_AFTER_MIN = 20
ARREST_TEXT = ("Respiratory arrest after twenty minutes of unsupported apnoeic breathing, and the circulation "
               "follows it. Ventilation was the treatment that was missing, with or without the antidote.")


def long_acting(state):
    case = state.get("encounter_spec", {}).get("clinical_case", {}).get("engine", {})
    return bool(case.get("recurrence_risk"))


# Faculty decision 3b of 2026-09-21: concentration and effect are not the same
# thing, and the model was treating them as one, so the patient stayed sleepy
# for as long as any drug remained. Below a threshold of free agonist the
# clinical effect is gone although the drug is not, which is what lets an
# isolated immediate-release overdose recover fully and become a candidate for
# discharge after an adequate observation, without waiting for zero.
#
# The two effects are separate and have different sensitivities, which is the
# same teaching the antidote carries: ventilation comes back first and
# consciousness follows it, so a patient can be breathing adequately and still
# be too drowsy to send home.
VENTILATION_THRESHOLD = .50       # free agonist below which breathing is normal
CONSCIOUSNESS_THRESHOLD = .32     # and below which the patient is properly awake
EFFECT_CEILING = 1.0              # the free agonist at which the case's own state is described

# An oral dose is still being absorbed when the patient arrives, so the
# concentration rises before it falls. The depot is what has not been absorbed
# yet, as a share of the arrival concentration, and this is how fast it enters.
ABSORPTION_PER_MIN = .035         # about a twenty-minute absorption half-life


def _effect(free, threshold):
    if free <= threshold:
        return 0.0
    return min(1.0, (free - threshold) / max(1e-6, EFFECT_CEILING - threshold))


def naloxone_level(f):
    return max(0.0, float(f.get("naloxone") or 0))


def free_agonist(f):
    """Agonist on board that the antidote is not holding."""
    return max(0.0, float(f.get("opioid") or 0) - naloxone_level(f))


def suppression(f):
    """The ventilatory depression, which is what the antidote is titrated to."""
    return _effect(free_agonist(f), VENTILATION_THRESHOLD)


def sedation(f):
    """The depression of consciousness, which recovers after the breathing."""
    return _effect(free_agonist(f), CONSCIOUSNESS_THRESHOLD)


def withdrawal(f):
    """How far past the ventilation target the antidote has been pushed.

    Measured against the opioid still on board: reversing what is there is the
    treatment, and only the excess over it is withdrawal.
    """
    return max(0.0, naloxone_level(f) - (float(f.get("opioid") or 0) + WITHDRAWAL_MARGIN))


def step(state):
    """One minute of opioid, antidote and the breathing between them."""
    f = state["family_state"]
    # What was swallowed and not yet absorbed keeps arriving, so an oral
    # overdose is still climbing when the resident meets it.
    depot = float(f.get("opioid_depot") or 0)
    if depot > 0:
        entering = depot * ABSORPTION_PER_MIN
        f["opioid_depot"] = depot - entering
        f["opioid"] = float(f.get("opioid") or 0) + entering
    f["opioid"] *= LONG_ACTING_DECAY_PER_MIN if long_acting(state) else DECAY_PER_MIN
    # The antidote is cleared here, so both engines share one decay.
    f["naloxone"] = float(f.get("naloxone") or 0) * NALOXONE_DECAY_PER_MIN
    rate = float(f.get("naloxone_infusion_mg_h") or 0)
    if rate:
        # The infusion holds a level; boluses on top still peak above it.
        target = INFUSION_LEVEL_PER_MG_H * rate
        if f.get("naloxone", 0) < target:
            f["naloxone"] = min(target, f.get("naloxone", 0) + target / 10)
    observable = state.get("observable", {})
    unsupported = not (f.get("bag_mask") or f.get("invasive"))
    # The core reports a fractional rate, so compare with a tolerance.
    failing = (suppression(f) >= APNOEA_SUPPRESSION
               or float(observable.get("respiratory_rate", 12)) <= APNOEA_RR + .5
               or float(observable.get("spo2", 100)) <= APNOEA_SPO2)
    if unsupported and failing:
        f["apnoea_min"] = f.get("apnoea_min", 0.0) + 1
    else:
        f["apnoea_min"] = 0.0
    if withdrawal(f) > 0 and not f.get("withdrawal_reported"):
        f["withdrawal_reported"] = True
        return WITHDRAWAL_TEXT
    if f.get("arrest_at") is None and f.get("apnoea_min", 0) >= ARREST_AFTER_MIN:
        f["arrest_at"] = f["elapsed"]
        return ARREST_TEXT
    return None
