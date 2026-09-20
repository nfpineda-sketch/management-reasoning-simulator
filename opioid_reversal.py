"""Naloxone titrated to ventilation, not to consciousness (faculty, 2026-09-20).

The bank modelled a single decay for every opioid and no price for giving too
much naloxone. The faculty asked for three things: a long-acting opioid that
outlasts the antidote, so that boluses alone are not enough and an infusion is
the treatment; acute withdrawal when the antidote is pushed past what ventilation
needs; and an end for apnoea that is never supported.

Teaching magnitudes pending faculty review, and only the bank opioid family uses
them.
"""
DECAY_PER_MIN = .999               # a short-acting opioid: about eleven hours
LONG_ACTING_DECAY_PER_MIN = .9997  # a long-acting one outlasts the encounter
NALOXONE_DECAY_PER_MIN = .975      # about twenty-seven minutes

# An infusion holds the antidote where a bolus cannot.
INFUSION_LEVEL_PER_MG_H = 2.5      # 0.4 mg/h holds a level of about 1.0

# Withdrawal: the price of titrating to consciousness.
WITHDRAWAL_LEVEL = 1.2
WITHDRAWAL_HR = 25
WITHDRAWAL_SBP = 20
WITHDRAWAL_RR = 6
WITHDRAWAL_TEXT = ("Acute withdrawal: the patient is agitated, retching and sweating, with a rising pressure and "
                   "rate. The target of the antidote is ventilation, not consciousness.")

# Apnoea nobody supports.
APNOEA_RR = 6
APNOEA_SPO2 = 80
ARREST_AFTER_MIN = 20
ARREST_TEXT = ("Respiratory arrest after twenty minutes of unsupported apnoeic breathing, and the circulation "
               "follows it. Ventilation was the treatment that was missing, with or without the antidote.")


def long_acting(state):
    case = state.get("encounter_spec", {}).get("clinical_case", {}).get("engine", {})
    return bool(case.get("recurrence_risk"))


def naloxone_level(f):
    return max(0.0, float(f.get("naloxone") or 0))


def suppression(f):
    return max(0.0, float(f.get("opioid") or 0) - naloxone_level(f))


def withdrawal(f):
    """How far past the ventilation target the antidote has been pushed."""
    return max(0.0, naloxone_level(f) - WITHDRAWAL_LEVEL)


def step(state):
    """One minute of opioid, antidote and the breathing between them."""
    f = state["family_state"]
    f["opioid"] *= LONG_ACTING_DECAY_PER_MIN if long_acting(state) else DECAY_PER_MIN
    rate = float(f.get("naloxone_infusion_mg_h") or 0)
    if rate:
        # The infusion holds a level; boluses on top still peak above it.
        target = INFUSION_LEVEL_PER_MG_H * rate
        if f.get("naloxone", 0) < target:
            f["naloxone"] = min(target, f.get("naloxone", 0) + target / 10)
    observable = state.get("observable", {})
    unsupported = not (f.get("bag_mask") or f.get("invasive"))
    failing = float(observable.get("respiratory_rate", 12)) <= APNOEA_RR or float(observable.get("spo2", 100)) < APNOEA_SPO2
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
