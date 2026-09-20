"""The obstructed right ventricle (faculty decisions 2026-09-20).

Two decisions. Systemic thrombolysis in high-risk pulmonary embolism only with
sustained hypotension: not for a pressure that dips once, and not for a
normotensive patient with a large clot. And volume given fast is punished: the
right ventricle is already distended against a fixed obstruction, so a rapid
bolus raises its wall tension, worsens the septal shift and drops cardiac output
further. Volume given slowly, in modest amounts, is neither the treatment nor the
insult.

Reperfusion here is dissolution, not a balloon: the obstruction falls over about
half an hour once the drug is in, and what recovers is the circulation, not a
wall of myocardium.

Teaching magnitudes pending faculty review, and only the bank pulmonary embolism
family uses them.
"""
import math

# Sustained hypotension: the indication, not a single low reading.
HYPOTENSION_SBP = 90
SUSTAINED_HYPOTENSION_MIN = 15
HYPOTENSION_RESET_PER_MIN = 1.0    # a pressure that recovers gives the clock back

# Volume: tolerated rate, and the price of anything faster.
TOLERATED_ML_PER_MIN = 10.0        # about 600 mL/h: a maintenance-rate infusion
RV_STRAIN_PER_ML = .0006           # per mL per minute above the tolerated rate
RV_STRAIN_TAU_MIN = 45.0           # the distended ventricle recovers slowly
RV_STRAIN_LUNG_SHARE = .35         # part of the insult shows as worse oxygenation

# Thrombolysis: dissolution over half an hour.
LYSIS_ONSET_MIN = 5
LYSIS_TAU_MIN = 30.0
LYSIS_CIRCULATION_TARGET = .62     # what the obstruction falls to, from 1.0 at arrival
LYSIS_LUNG_TARGET = .80

# Bleeding is the price of the drug, indicated or not (faculty decision 2026-09-20).
LYSIS_HEMOGLOBIN_PER_MIN = .006    # occult loss: about 0.36 g/dL per hour
MAJOR_BLEED_AT_MIN = 20            # when the case carries a bleeding risk
MAJOR_BLEED_HEMOGLOBIN_PER_MIN = .03
MAJOR_BLEED_CIRCULATION_PER_MIN = .0015
BLEED_RISK_TEXT = {
    "recent_surgery": "the surgical site operated on twelve days ago",
    "severe_hypertension": "an uncontrolled arterial pressure",
}

# Positive pressure in obstructive shock empties an already obstructed circulation.
INTUBATION_CIRCULATION_COST = .40   # the induction and the positive pressure together
INTUBATION_PER_PEEP_CMH2O = .03


def indicated(f):
    """True once the hypotension has been sustained; the indication does not expire.

    A pressure held up by a vasopressor is still the hypotension of the
    obstruction, so those minutes count, and once the indication is met a later
    recovery does not remove it.
    """
    return bool(f.get("lysis_indication_met"))


def track_hypotension(f, observable):
    sbp = float(observable.get("sbp") or 0)
    on_vasopressor = float(f.get("norepinephrine") or 0) > 0
    minutes = f.get("sustained_hypotension_min", 0.0)
    minutes = minutes + 1 if (sbp < HYPOTENSION_SBP or on_vasopressor) else minutes - HYPOTENSION_RESET_PER_MIN
    f["sustained_hypotension_min"] = max(0.0, minutes)
    if f["sustained_hypotension_min"] >= SUSTAINED_HYPOTENSION_MIN:
        f["lysis_indication_met"] = True


def volume_insult(f, fluid_ml_this_minute):
    """Fast volume distends the obstructed ventricle; a slow drip does not."""
    excess = max(0.0, float(fluid_ml_this_minute or 0) - TOLERATED_ML_PER_MIN)
    if excess:
        f["rv_strain"] = f.get("rv_strain", 0.0) + excess * RV_STRAIN_PER_ML
    strain = f.get("rv_strain", 0.0)
    if strain:
        f["rv_strain"] = strain * math.exp(-1 / RV_STRAIN_TAU_MIN)
    return f.get("rv_strain", 0.0)


def give_thrombolysis(f, elapsed, observable):
    """Record the decision and say whether it was indicated. Returns the note."""
    f["lysis_at"] = elapsed
    f["lysis_indicated"] = indicated(f)
    if f["lysis_indicated"]:
        return ("Systemic thrombolysis given for sustained hypotension: the obstruction begins to fall within "
                "minutes and keeps falling for about half an hour.")
    sbp = observable.get("sbp")
    so_far = int(f.get("sustained_hypotension_min", 0.0))
    return (f"Systemic thrombolysis given before the hypotension was sustained (systolic {sbp} mmHg, low for "
            f"{so_far} of the {SUSTAINED_HYPOTENSION_MIN} minutes the indication requires): the bleeding risk is "
            "taken without the indication, and the obstruction is unchanged.")


def lysis_effect(f):
    """Share of the dissolution achieved so far, 0 before the drug works."""
    if f.get("lysis_at") is None or not f.get("lysis_indicated"):
        return 0.0
    since = f["elapsed"] - f["lysis_at"] - LYSIS_ONSET_MIN
    return 0.0 if since <= 0 else 1 - math.exp(-since / LYSIS_TAU_MIN)


def bleeding_risk(state):
    """A declared reason this patient bleeds with a thrombolytic, or None."""
    case = state.get("encounter_spec", {}).get("clinical_case", {})
    return case.get("engine", {}).get("lysis_bleeding_risk")


def step(state, fluid_ml_this_minute):
    """One minute of the obstructed ventricle. Returns an event text or None."""
    f = state["family_state"]
    track_hypotension(f, state.get("observable", {}))
    strain = volume_insult(f, fluid_ml_this_minute)
    share = lysis_effect(f)
    if share:
        # Dissolution pulls the obstruction and the dead space towards their targets.
        f["circulation"] += (LYSIS_CIRCULATION_TARGET + strain - f["circulation"]) * (1 / LYSIS_TAU_MIN)
        f["lung"] += (LYSIS_LUNG_TARGET - f["lung"]) * (1 / LYSIS_TAU_MIN)
    if f.get("lysis_at") is not None:
        # The drug bleeds whether or not it was indicated.
        f["hemoglobin"] -= LYSIS_HEMOGLOBIN_PER_MIN
        since = f["elapsed"] - f["lysis_at"]
        risk = bleeding_risk(state)
        if risk and since >= MAJOR_BLEED_AT_MIN:
            f["hemoglobin"] -= MAJOR_BLEED_HEMOGLOBIN_PER_MIN
            f["circulation"] += MAJOR_BLEED_CIRCULATION_PER_MIN
            if not f.get("major_bleed_reported"):
                f["major_bleed_reported"] = True
                return (f"Bleeding from {BLEED_RISK_TEXT.get(risk, 'the declared site')}: the haemoglobin is falling "
                        "and the pressure with it. This is the risk the thrombolytic carries, and it was taken in a "
                        "patient who had a reason to bleed.")
    if strain > 0 and not f.get("rv_strain_reported") and strain >= .10:
        f["rv_strain_reported"] = True
        return ("The fluid was given faster than the obstructed right ventricle can accept: it distends, the septum "
                "shifts and the output falls. Volume here is given slowly and in small amounts, or not at all.")
    if indicated(f) and f.get("lysis_at") is None and not f.get("hypotension_reported"):
        f["hypotension_reported"] = True
        return (f"The systolic pressure has stayed below {HYPOTENSION_SBP} mmHg for "
                f"{SUSTAINED_HYPOTENSION_MIN} minutes: this is sustained hypotension from the obstruction.")
    return None


def positive_pressure_cost(f, peep_cmh2o):
    """What invasive ventilation costs a circulation that is already obstructed.

    It fades as the obstruction dissolves: the same tube is tolerated once the
    right ventricle is no longer working against a closed pulmonary circulation.
    """
    if not f.get("invasive"):
        return 0.0
    remaining = 1 - lysis_effect(f)
    return (INTUBATION_CIRCULATION_COST + INTUBATION_PER_PEEP_CMH2O * max(0.0, float(peep_cmh2o or 0) - 5)) * remaining


def surface_penalty(f, peep_cmh2o=0):
    """(circulation penalty, lung penalty) from the distended, ventilated ventricle.

    Fast volume costs output and oxygenation; positive pressure costs output alone,
    because the tube has already taken over the oxygenation.
    """
    strain = f.get("rv_strain", 0.0)
    return (strain * (1 - RV_STRAIN_LUNG_SHARE) + positive_pressure_cost(f, peep_cmh2o),
            strain * RV_STRAIN_LUNG_SHARE)
