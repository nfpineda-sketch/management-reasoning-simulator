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
    # Calcium does not lower the potassium; it makes the membrane survive it.
    # That is why it buys a rate and a pressure here and why the potassium in
    # the record is unchanged afterwards.
    "hyperk": {"calcium": 14.0, "glucagon": 0.0},
}
#: And the systolic pressure each buys beyond what the rate alone gives back,
#: because a calcium-channel blockade is a vascular problem as well as a rate one.
ANTIDOTE_SBP = {
    "ccb": {"calcium": 14.0, "glucagon": 5.0},
    "bb": {"calcium": 4.0, "glucagon": 12.0},
    "avb3": {"calcium": 0.0, "glucagon": 0.0},
    "hyperk": {"calcium": 10.0, "glucagon": 0.0},
}

# --- severe hyperkalaemia ---------------------------------------------------
# Faculty decision 2026-09-23, in their own words: "mientras mas enfermo el
# paciente, mas lenta la FC y mas ancho el QRS en el ECG... debe sospechar y
# hacer incluso antes de tener el resultado. El gluconato de calcio debe
# administrarse apenas exista la sospecha clinica."
#
# So the tracing carries the severity and the laboratory only confirms it. Both
# the rate and the width move with the potassium, together, and the resident can
# read the patient getting worse without a number ever arriving.
K_THRESHOLD = 5.5                 # below this the potassium is not what is wrong
K_SEVERE = 7.5                    # at and above it, the width is at its worst
QRS_NARROW_MS = 92.0
QRS_WIDE_MS = 180.0
K_RATE_LOSS_AT_SEVERE = 34.0      # beats the potassium takes at its worst

#: What lowers the potassium itself, per simulated minute at a full dose. Both
#: are shifts: they move it into the cell and do not remove it from the body,
#: which is the reason the case ends in a referral and not in a cure.
SALBUTAMOL_K_PER_MIN = .010
DEXTROSE_K_PER_MIN = .004
#: And it comes back, because nothing here has removed any of it.
K_REBOUND_PER_MIN = .0018


def potassium_severity(potassium):
    """0 when the potassium is not the problem, 1 when it is as bad as modelled."""
    value = max(0.0, float(potassium or 0))
    if value <= K_THRESHOLD:
        return 0.0
    return min(1.0, (value - K_THRESHOLD) / (K_SEVERE - K_THRESHOLD))


def qrs_ms(potassium, membrane_protection=0.0):
    """The width the tracing shows. Calcium narrows it without moving the potassium."""
    severity = potassium_severity(potassium) * max(0.0, 1 - min(1.0, membrane_protection))
    return QRS_NARROW_MS + (QRS_WIDE_MS - QRS_NARROW_MS) * severity


def potassium_rate_loss(potassium, membrane_protection=0.0):
    severity = potassium_severity(potassium) * max(0.0, 1 - min(1.0, membrane_protection))
    return K_RATE_LOSS_AT_SEVERE * severity


def membrane_protection(f):
    """How much of the potassium's electrical effect the calcium is holding off."""
    calcium = min(2.0, float(f.get("calcium_units", 0.0)) / CALCIUM_REFERENCE_UNITS)
    return min(1.0, .55 * calcium) * _faded(f, f.get("calcium_at"))


def step_potassium(f, state):
    """Move the potassium by what was given. Returns nothing; the record is f."""
    if cause(state) != "hyperk":
        return
    f.setdefault("potassium", float(spec(state).get("potassium", 7.4)))
    shift = (SALBUTAMOL_K_PER_MIN * min(1.0, float(f.get("bronchodilation", 0.0)))
             + DEXTROSE_K_PER_MIN * min(1.0, float(f.get("dextrose_g", 0.0)) / 25))
    # Nothing given here removes potassium from the body, so what was shifted
    # into the cell drifts back out. The treatment that removes it is the one
    # this engine does not run.
    rebound = K_REBOUND_PER_MIN if f.get("shifted_k", 0.0) > 0 else 0.0
    f["shifted_k"] = max(0.0, f.get("shifted_k", 0.0) + shift - rebound)
    # An anuric patient keeps making potassium nobody is removing, so the number
    # climbs while the shift only borrows against it (2026-09-24).
    f["retained_k"] = f.get("retained_k", 0.0) + K_RISE_PER_MIN
    arrival = float(spec(state).get("potassium", 7.4))
    f["potassium"] = max(3.0, min(9.5, arrival + f["retained_k"] - f["shifted_k"]))
#: What the antidotes buy fades: neither is definitive, which is why the case
#: is about asking for what is.
DECAY_TAU_MIN = 22.0

# --- what happens while nothing is done -------------------------------------
# Measured on 2026-09-24 across the whole bank: this was the one family whose
# patient did not move at all. A man at 74/44 with a rate of 38 sat there
# unchanged for an hour, which teaches that an unstable bradycardia is not
# urgent. Each cause progresses in its own way and for its own reason, and none
# of it is a penalty for time passing.
#
#: Beats the rate still loses per simulated minute, untreated.
# Calibrated against one clinical endpoint: an untreated patient of each of
# these is peri-arrest at about an hour, which is where the rate reaches
# ARREST_RATE from that case's own arrival.
PROGRESSION_BEATS_PER_MIN = {
    # A tablet is still being absorbed, and a sustained-release one for hours.
    "ccb": .30,
    "bb": .28,
    # An escape rhythm nobody is supporting is not one to rely on, and the
    # hypoperfusion it causes makes conduction worse rather than better.
    "avb3": .18,
    # The potassium climbs as well, and a repeat panel shows a worse number.
    "hyperk": .20,
}
#: An anuric patient's potassium keeps climbing: about 0.6 mmol/L an hour.
K_RISE_PER_MIN = .010

#: The rate at which this engine stops pretending there is an output.
ARREST_RATE = 20
ARREST_TEXT = (
    "The rate has fallen away and the circulation with it. Nothing given so far "
    "reached the cause, and the rate was the only thing holding the output up."
)


def step(f, state):
    """Advance one minute of an untreated bradycardia.

    The antidotes are added on top of what this takes, so treatment outpaces the
    course while it lasts and stops outpacing it when it fades.
    """
    step_potassium(f, state)
    f["rate_lost"] = f.get("rate_lost", 0.0) + PROGRESSION_BEATS_PER_MIN[cause(state)]


def arrest_event(f, rate):
    """The moment the rate stops being an output, said once."""
    if rate > ARREST_RATE or f.get("bradycardia_arrest"):
        return None
    f["bradycardia_arrest"] = True
    return ARREST_TEXT


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
