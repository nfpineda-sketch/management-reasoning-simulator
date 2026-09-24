"""Anaphylaxis: the route matters, and the resident can watch it matter.

Authored teaching magnitudes pending faculty review, used only by the bank's
anaphylaxis family. Nothing here is a prescribing threshold.

Three things this family is built to teach, and each of them is something the
resident observes rather than is told:

* **Adrenaline is the treatment.** An antihistamine, a steroid and a
  bronchodilator change nothing here. They are recorded, they are answered for,
  and the reaction continues. That is not a punishment; it is the reason the
  omission is the most studied one in the specialty.
* **The route is visible.** Intramuscular adrenaline is a depot: it is absorbed
  over minutes and reaches its effect at about four. Intravenous is nearly
  immediate. A resident who gives it IM and reassesses at two minutes sees
  nothing yet, and what they do with that is the decision the case is about.
  Until 2026-09-23 the engine could not administer IM at all -- the gap was
  found by a measurement, not by a test.
* **Refractory is a question, not a dose.** In the beta-blocked variant the
  adrenaline does a third of what it should, and no amount of repeating it
  closes the gap. Glucagon does. The information that says so is in the
  medication history, and it is there for the asking.

The biphasic return is the family's premature-closure teaching: the reaction
settles, and if nobody is watching it comes back.
"""

# --- the reaction ----------------------------------------------------------
#: How fast an untreated reaction still worsens, per simulated minute. Tuned so
#: that twenty-five untreated minutes take an arrival at 84/46 to a pressure
#: that makes the arrest that follows it legible: at .010 the patient still
#: looked survivable when the event fired, which reads as the engine lying.
PROGRESSION_PER_MIN = .030
#: Below this the reaction is no longer driving the physiology.
RESOLVED = .15

# --- adrenaline ------------------------------------------------------------
#: One intramuscular adult dose. Doses are scaled to this, so half a dose does
#: half the work rather than nothing.
IM_REFERENCE_MG = 0.5
IV_REFERENCE_MG = 0.05          # a push dose; the infusion is the ordinary route

#: The depot. Each minute this fraction of what is left in the muscle is taken
#: up, which puts the effect at roughly four minutes and keeps it arriving
#: afterwards rather than landing all at once.
IM_UPTAKE_PER_MIN = .28
IV_UPTAKE_PER_MIN = .85

#: How much of the reaction one absorbed reference dose removes each minute at
#: full effect. Tuned so that a first intramuscular dose takes a severity of 1.0
#: to about a third by ten minutes and close to settled by twenty, which is the
#: response a resident should be able to recognise as adequate.
EFFECT_PER_DOSE = .55
RELIEF_PER_MIN = .16
#: What is absorbed leaves at this rate; a single dose wears off in about twenty
#: minutes, which is why a severe reaction needs the infusion and not repetition.
CLEARANCE_PER_MIN = .955

#: A beta-blocked receptor answers about a third as well.
BETA_BLOCKED_RESPONSE = .35
#: Glucagon does not act through the beta receptor, so it restores what the
#: blockade took. One adult dose.
GLUCAGON_REFERENCE_MG = 1.0
GLUCAGON_RESTORES = .85
GLUCAGON_CLEARANCE_PER_MIN = .97

# --- what the reaction does ------------------------------------------------
# These are **differences from the state the patient arrived in**, not absolute
# effects. The authored arrival numbers already contain the reaction; applying
# the whole of it again put a patient who walked in at 84/46 into a clamped
# 50/25 within ten minutes, with no room left for anyone to act. What the
# resident sees is how far the reaction moves from where they found it.
SBP_PER_SEVERITY = 40            # per unit of severity, from the arrival severity
HR_PER_SEVERITY = 30
OBSTRUCTION_PER_SEVERITY = .45   # the bronchospasm, in the family's own units
STRIDOR_AT = .80                 # above this the upper airway is audible

# --- the biphasic return ---------------------------------------------------
#: Minutes after the reaction first settles before it can return.
BIPHASIC_DELAY_MIN = 75
BIPHASIC_SEVERITY = .60
BIPHASIC_TEXT = (
    "The reaction returns: the wheeze and the flushing are back and the pressure "
    "is falling again, more than an hour after it first settled. The adrenaline "
    "that treated the first reaction has long since worn off."
)

ARREST_AFTER_MIN = 25
ARREST_TEXT = (
    "Circulatory arrest after twenty-five minutes of untreated anaphylaxis. "
    "Adrenaline was the treatment that was missing; nothing else that was given "
    "acts on the reaction."
)


def _case(state):
    return state.get("encounter_spec", {}).get("clinical_case", {}) or {}


def spec(state):
    """This case's anaphylaxis parameters, or an empty mapping."""
    return _case(state).get("engine", {}).get("anaphylaxis", {}) or {}


def beta_blocked(state):
    return bool(spec(state).get("beta_blocked"))


def biphasic(state):
    return bool(spec(state).get("biphasic"))


def give_epinephrine(f, milligrams, route):
    """Put a dose where the route puts it: in a muscle, or in the circulation."""
    milligrams = max(0.0, float(milligrams or 0))
    if not milligrams:
        return
    if str(route or "").upper() in {"IV", "IO"}:
        f["epi_iv_pool"] = f.get("epi_iv_pool", 0.0) + milligrams / IV_REFERENCE_MG
    else:
        # IM, SC and anything else that is not in a vein: the muscle holds it.
        f["epi_im_depot"] = f.get("epi_im_depot", 0.0) + milligrams / IM_REFERENCE_MG


def give_glucagon(f, milligrams):
    f["glucagon_level"] = f.get("glucagon_level", 0.0) + max(0.0, float(milligrams or 0)) / GLUCAGON_REFERENCE_MG


def responsiveness(f, is_beta_blocked):
    """How much of the adrenaline's effect this patient can actually have."""
    if not is_beta_blocked:
        return 1.0
    restored = min(1.0, f.get("glucagon_level", 0.0)) * GLUCAGON_RESTORES
    return BETA_BLOCKED_RESPONSE + (1 - BETA_BLOCKED_RESPONSE) * restored


def step(state):
    """Advance one simulated minute. Returns a procedure event, or None.

    The order of the minute is the order of the physiology: what is in the
    muscle is absorbed, what is absorbed acts, what acted decays, and only then
    does the reaction move.
    """
    f = state["family_state"]
    f.setdefault("reaction", float(spec(state).get("severity", 1.0)))
    f.setdefault("epi_im_depot", 0.0)
    f.setdefault("epi_iv_pool", 0.0)
    f.setdefault("epi_effect", 0.0)
    f.setdefault("glucagon_level", 0.0)
    f.setdefault("untreated_min", 0)

    absorbed = f["epi_im_depot"] * IM_UPTAKE_PER_MIN + f["epi_iv_pool"] * IV_UPTAKE_PER_MIN
    f["epi_im_depot"] *= (1 - IM_UPTAKE_PER_MIN)
    f["epi_iv_pool"] *= (1 - IV_UPTAKE_PER_MIN)
    # An adrenaline infusion holds what a bolus cannot.
    absorbed += float(f.get("epinephrine", 0) or 0) * .06
    f["epi_effect"] = f["epi_effect"] * CLEARANCE_PER_MIN + absorbed
    f["glucagon_level"] *= GLUCAGON_CLEARANCE_PER_MIN

    working = f["epi_effect"] * responsiveness(f, beta_blocked(state))
    f["reaction"] = max(0.0, f["reaction"] + PROGRESSION_PER_MIN
                        - EFFECT_PER_DOSE * RELIEF_PER_MIN * min(2.0, working))

    if f["reaction"] >= RESOLVED and working < .05:
        f["untreated_min"] += 1
    else:
        f["untreated_min"] = 0

    event = None
    if f["reaction"] < RESOLVED and f.get("settled_at") is None:
        f["settled_at"] = f["elapsed"]
    if (biphasic(state) and f.get("settled_at") is not None
            and f.get("biphasic_at") is None
            and f["elapsed"] - f["settled_at"] >= BIPHASIC_DELAY_MIN):
        f["biphasic_at"] = f["elapsed"]
        f["reaction"] = BIPHASIC_SEVERITY
        f["settled_at"] = None
        event = BIPHASIC_TEXT
    if f["untreated_min"] >= ARREST_AFTER_MIN and not f.get("arrested"):
        f["arrested"] = True
        event = ARREST_TEXT
    return event


def observables(f, state=None):
    """How far the reaction has moved from the state the patient arrived in.

    Positive means worse than arrival. A settled reaction returns the numbers
    towards where they would have been without it, which is what recovery has
    to look like for the resident to be able to see it happen.
    """
    arrival = float(f.setdefault("reaction_baseline", f.get("reaction", 1.0)))
    severity = max(0.0, min(1.8, float(f.get("reaction", 0.0))))
    moved = severity - arrival
    # A blunted receptor does not mount the tachycardia either: in the
    # beta-blocked case the missing rate is itself the finding.
    hr_scale = float((spec(state) if state is not None else {}).get("hr_response", 1.0))
    return {
        "sbp_drop": SBP_PER_SEVERITY * moved,
        "hr_rise": HR_PER_SEVERITY * moved * hr_scale,
        "obstruction": OBSTRUCTION_PER_SEVERITY * moved,
        "stridor": severity >= STRIDOR_AT,
    }
