"""The bradycardia whose treatment is not the rate.

Authored teaching magnitudes pending faculty review, used only by the bank's
bradycardia family. Nothing here is a prescribing threshold.

``bradycardia_support`` already models what an inferior infarct's block answers
to: atropine where the block is nodal, and pacing where it is not. This module
adds the other half of the differential, which is the one the resident has to
ask about rather than read off the monitor:

* **A calcium-channel blockade** takes the rate and the vascular tone together,
  and its clue is on the glucose: the same channels release insulin. Calcium
  restores part of it and does not last; the definitive answer is the one this
  engine does not run, so the case is about recognising it and asking for help.
* **A beta blockade** takes the rate and the contractility, and leaves the
  glucose alone. Glucagon works past the blocked receptor; calcium does less.
* **A complete infranodal block** answers to neither, and to no dose of
  atropine. It answers to a pacing wire, and to nothing the resident can give.

The point the three share: the rate is a symptom, and giving it back without
naming what took it is the omission this family is built to show.
"""

#: One adult ampoule of calcium gluconate, in the units the engine counts.
CALCIUM_REFERENCE_UNITS = 1.0
#: One adult dose of glucagon, in milligrams.
GLUCAGON_REFERENCE_MG = 5.0

#: Beats one reference dose of each antidote buys back, by cause. A number of
#: zero is a statement: this antidote does not act on this poisoning.
ANTIDOTE_BEATS = {
    "ccb": {"calcium": 16.0, "glucagon": 6.0},
    "bb": {"calcium": 5.0, "glucagon": 18.0},
    "avb3": {"calcium": 0.0, "glucagon": 0.0},
}
#: And the systolic pressure each buys beyond what the rate alone gives back,
#: because a calcium-channel blockade is a vascular problem as well as a rate one.
ANTIDOTE_SBP = {
    "ccb": {"calcium": 14.0, "glucagon": 5.0},
    "bb": {"calcium": 4.0, "glucagon": 12.0},
    "avb3": {"calcium": 0.0, "glucagon": 0.0},
}
#: What the antidotes buy fades: neither is definitive, which is why the case
#: is about asking for what is.
DECAY_TAU_MIN = 22.0


def spec(state):
    case = state.get("encounter_spec", {}).get("clinical_case", {}) or {}
    return case.get("engine", {}).get("bradycardia", {}) or {}


def cause(state):
    value = str(spec(state).get("cause") or "avb3").strip().lower()
    return value if value in ANTIDOTE_BEATS else "avb3"


def _faded(f, given_at):
    if given_at is None:
        return 0.0
    elapsed = max(0.0, f["elapsed"] - given_at)
    return DECAY_TAU_MIN / (DECAY_TAU_MIN + elapsed)


def antidote_gain(f, which):
    """Beats and systolic pressure the antidotes still contribute."""
    table_beats, table_sbp = ANTIDOTE_BEATS[which], ANTIDOTE_SBP[which]
    calcium = min(3.0, float(f.get("calcium_units", 0.0)) / CALCIUM_REFERENCE_UNITS)
    glucagon = min(3.0, float(f.get("glucagon_doses", 0) or 0)
                   * 1.0 * (GLUCAGON_REFERENCE_MG / GLUCAGON_REFERENCE_MG))
    beats = (table_beats["calcium"] * calcium * _faded(f, f.get("calcium_at"))
             + table_beats["glucagon"] * glucagon * _faded(f, f.get("glucagon_at")))
    pressure = (table_sbp["calcium"] * calcium * _faded(f, f.get("calcium_at"))
                + table_sbp["glucagon"] * glucagon * _faded(f, f.get("glucagon_at")))
    return beats, pressure
