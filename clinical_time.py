"""What each kind of clinical activity costs in simulated minutes.

**These are simulator assumptions pending clinical calibration.** They are here,
in one place, because until 2026-09-23 they were not anywhere: asking the
patient a question cost nothing, examining them cost nothing, and a patient who
was unstable and untreated stayed exactly as unstable while the resident spent
an afternoon gathering information. The clock only moved for treatments,
reassessments and studies.

Two different things are measured and they must not be confused.

**Active time** is the resident's own time: the minutes they spend asking,
examining, reading a result or writing an order. It advances the clock, and the
patient's physiology runs through it like any other minute.

**Result time** is the wait until a study is back. It does not occupy the
resident. Ordering a laboratory panel costs them a minute of active time and the
result arrives ten minutes later, during which they can treat, ask, examine or
reassess. Before 2026-09-23 the two were one number, so sending bloods froze the
resident for ten minutes and sending four studies froze them for the longest of
the four.

What is deliberately **not** here:

* No cost for re-rendering a screen, reopening the follow-up form, correcting an
  extraction or recovering from a refusal. Interface friction is not clinical time,
  and a resident must never pay a patient's minutes for one of this simulator's
  own limitations.
* No penalty for asking. The minutes are real and the patient moves through
  them, but nothing here makes a patient worse *because* a question was asked:
  the deterioration is whatever that case's own physiology does in that interval
  and nothing more.
"""

#: The resident's own time, in simulated minutes.
ACTIVE_MINUTES = {
    # Reading something that is already back. Short, and never repeats the study.
    "result_review": 1,
    # One question to the patient or the collateral source.
    "history_question": 2,
    # One region of the physical examination.
    "examination_region": 2,
    # Each further region in the same examination: the hands are already on the
    # patient, so the second region costs less than the first.
    "examination_extra_region": 1,
    # Writing a request for a study that somebody else performs.
    "study_request": 1,
}

#: The most an examination of many regions can cost, however many are named.
EXAMINATION_CEILING_MINUTES = 8

#: Studies the resident performs themselves at the bedside. Their active time is
#: the study's own duration and the result is there when they finish, because
#: they were the one looking.
BEDSIDE_STUDIES = frozenset({
    "ecg", "ecg_right", "ecg_posterior", "pocus", "efast", "poc_glucose", "temperature",
})


def examination_minutes(regions):
    """Active time for an examination of one or more regions."""
    count = max(1, len(regions or ()))
    total = (ACTIVE_MINUTES["examination_region"]
             + ACTIVE_MINUTES["examination_extra_region"] * (count - 1))
    return min(EXAMINATION_CEILING_MINUTES, total)


def study_active_minutes(diagnostic, result_minutes):
    """The resident's own time for a study: performing it, or asking for it."""
    if diagnostic in BEDSIDE_STUDIES:
        return max(1, int(result_minutes or 0))
    return ACTIVE_MINUTES["study_request"]


def study_result_minutes(diagnostic, result_minutes):
    """When the result is back, counted from the moment it was requested.

    A bedside study is back when the resident stops looking, so its result time
    equals its active time. Anything sent away comes back on its own schedule.
    """
    minutes = max(0, int(result_minutes or 0))
    return minutes if diagnostic not in BEDSIDE_STUDIES else study_active_minutes(
        diagnostic, minutes)
