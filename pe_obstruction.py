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

Revised criterion (faculty, 2026-09-29). The hemodynamic basis for systemic
thrombolysis is either an obstructive shock the embolism explains -- a systolic
below 90 mmHg, or a vasopressor it really needs to stay above it, with a sign of
hypoperfusion -- which counts from arrival or whenever it appears, or, without
any sign of hypoperfusion, a hypotension that lasts 15 complete consecutive
minutes. Starting a vasopressor creates neither. The pressure is read as the
obstruction, the distended ventricle and positive pressure leave it, before any
rounding: drug-induced drops and bleeding after a thrombolytic keep their effect
on the patient but are never the embolism's shock. The 15 minutes approximate
the ESC 2019 persistent hypotension for teaching; they are not a literal copy of
that definition. Meeting the criterion is not the absence of contraindications,
nor leave for any modality or dose: every order is judged on the state of its
own minute, the history of having met it is kept, and a persisting shock does
not by itself make a second full dose indicated.
"""
import math

# Sustained hypotension: the indication, not a single low reading.
HYPOTENSION_SBP = 90
# Complete consecutive minutes; a minute the embolism leaves at or above the
# threshold, with no vasopressor it needs, starts the count again (2026-09-29).
SUSTAINED_HYPOTENSION_MIN = 15
# Hypoperfusion: any one sign the embolism explains is enough (faculty, 2026-09-29).
# Teaching parameters of this simulator, not clinical cut-offs it asserts.
LACTATE_HYPOPERFUSION_MMOL_L = 2.0     # the engine's own lactate, above this
# The lower edge of the engine's "impaired" perfusion. Cool extremities with a
# refill from 3.5 s, or cold ones (5.5 s and over), are the peripheral sign; cool
# extremities with a shorter refill ("mildly impaired") are not enough alone.
PERIPHERAL_HYPOPERFUSION_CRT_S = 3.5
ALTERED_BY_PRESSURE_SBP = 80           # the engine's threshold for a pressure that dulls consciousness
# The record every thrombolytic order carries since 2026-09-29. An older record
# without it is read by the rule of its own time, never as "no indication".
INDICATION_VERSION = 2
BASES = ("obstructive_shock", "persistent_hypotension")

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


def assessment(sbp, crt, lactate, altered, *, vasopressor_running=False, vasopressor_needed=None):
    """The pressure and the perfusion the embolism itself explains, compared before rounding.

    ``sbp`` is the systolic the obstruction, the distended ventricle and positive
    pressure leave, without a vasopressor's lift, drug-induced drops or bleeding
    after a thrombolytic. ``vasopressor_needed`` comes from an engine that cannot
    separate a vasopressor's lift from the pressure it shows (generated cases):
    True when one runs and was started on a systolic below the threshold.
    """
    low = sbp < HYPOTENSION_SBP or bool(vasopressor_needed)
    signs = []
    if altered:
        signs.append("altered_consciousness")
    if crt >= PERIPHERAL_HYPOPERFUSION_CRT_S:
        signs.append("peripheral_hypoperfusion")
    if lactate > LACTATE_HYPOPERFUSION_MMOL_L:
        signs.append("lactate")
    return {"sbp": round(float(sbp), 1), "low": bool(low), "signs": signs,
            "crt_s": round(float(crt), 1), "lactate_mmol_l": round(float(lactate), 1),
            "vasopressor_running": bool(vasopressor_running),
            "vasopressor_needed": bool(low and vasopressor_running)}


def basis(f, current=None):
    """The hemodynamic basis for systemic thrombolysis at this minute, or None."""
    current = current if current is not None else f.get("pe_attributable")
    if not current or not current.get("low"):
        return None
    if current.get("signs"):
        return "obstructive_shock"
    if f.get("sustained_hypotension_min", 0.0) >= SUSTAINED_HYPOTENSION_MIN:
        return "persistent_hypotension"
    return None


def indicated(f, current=None):
    """Whether the hemodynamic criterion holds now. Every order is judged afresh."""
    return basis(f, current) is not None


def criteria_met_before(f):
    """Whether the criterion held at some earlier minute: history, never a permit."""
    return bool(f.get("lysis_indication_met"))


def track_hypotension(f, current):
    """One minute of the embolism's own pressure: the consecutive count and the history."""
    if not current:
        return
    if current.get("low"):
        f["sustained_hypotension_min"] = f.get("sustained_hypotension_min", 0.0) + 1
    else:
        f["sustained_hypotension_min"] = 0.0
    now = int(f.get("elapsed", 0))
    if current.get("low") and current.get("signs"):
        f.setdefault("obstructive_shock_from_min", now)
        f["lysis_indication_met"] = True
    if f["sustained_hypotension_min"] >= SUSTAINED_HYPOTENSION_MIN:
        f.setdefault("persistent_hypotension_from_min", now)
        f["lysis_indication_met"] = True


def _record(f, elapsed, current):
    data = dict(current or {})
    data.update({"consecutive_low_min": int(f.get("sustained_hypotension_min", 0.0)),
                 "obstructive_shock_from_min": f.get("obstructive_shock_from_min"),
                 "persistent_hypotension_from_min": f.get("persistent_hypotension_from_min"),
                 # The engine's own values: they do not show that the resident obtained them.
                 "engine_internal": True})
    return {"version": INDICATION_VERSION, "minute": int(elapsed), "basis": None, "data": data}


def give_thrombolysis(f, elapsed, current, observable=None):
    """Record a thrombolytic order and judge it on this minute's state. Returns (note, record)."""
    record = _record(f, elapsed, current)
    shown = (observable or {}).get("sbp")
    shown = int(round(float(shown))) if shown is not None else int(round((current or {}).get("sbp", 0)))
    first = f.get("lysis_at")
    if first is not None:
        # A persisting shock is not leave for another full dose; the first dose goes
        # on doing what it does, and what a repeat adds is a decision still open.
        record["repeat_of_minute"] = int(first)
        record["criteria_present"] = basis(f, current)
        f.setdefault("lysis_doses", []).append(record)
        return (f"A second systemic thrombolytic dose is recorded; the first was given at minute {int(first)}. "
                "A persisting shock does not by itself indicate repeating a full dose, and this simulator gives "
                "the repeated dose no effect of its own.", record)
    found = basis(f, current)
    record["basis"] = found
    f["lysis_at"] = elapsed
    f["lysis_indicated"] = found is not None
    f["lysis_basis"] = found
    f.setdefault("lysis_doses", []).append(record)
    if found == "obstructive_shock":
        return ("Systemic thrombolysis given in obstructive shock, a hypotension with signs of hypoperfusion: the "
                "obstruction begins to fall within minutes and keeps falling for about half an hour.", record)
    if found == "persistent_hypotension":
        return (f"Systemic thrombolysis given for sustained hypotension ({SUSTAINED_HYPOTENSION_MIN} consecutive "
                "minutes): the obstruction begins to fall within minutes and keeps falling for about half an hour.",
                record)
    if current and current.get("low"):
        so_far = int(f.get("sustained_hypotension_min", 0.0))
        return (f"Systemic thrombolysis given without the hemodynamic indication: systolic {shown} mmHg with no sign "
                f"of hypoperfusion, low for {so_far} of the {SUSTAINED_HYPOTENSION_MIN} consecutive minutes a "
                "hypotension without them requires. The bleeding risk is taken without the indication, and the "
                "obstruction is unchanged.", record)
    support = " on a vasopressor the pressure does not need" if (current or {}).get("vasopressor_running") else ""
    return (f"Systemic thrombolysis given without the hemodynamic indication: systolic {shown} mmHg{support}, with no "
            "hypotension from the embolism. The bleeding risk is taken without the indication, and the obstruction "
            "is unchanged.", record)


def volume_insult(f, fluid_ml_this_minute):
    """Fast volume distends the obstructed ventricle; a slow drip does not."""
    excess = max(0.0, float(fluid_ml_this_minute or 0) - TOLERATED_ML_PER_MIN)
    if excess:
        f["rv_strain"] = f.get("rv_strain", 0.0) + excess * RV_STRAIN_PER_ML
    strain = f.get("rv_strain", 0.0)
    if strain:
        f["rv_strain"] = strain * math.exp(-1 / RV_STRAIN_TAU_MIN)
    return f.get("rv_strain", 0.0)


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
    track_hypotension(f, f.get("pe_attributable"))
    strain = volume_insult(f, fluid_ml_this_minute)
    share = lysis_effect(f)
    if share:
        # Dissolution pulls the obstruction and the dead space towards their targets.
        # It acts on the embolism's share of the circulation, so bleeding after the
        # drug keeps its own effect (2026-09-29).
        embolism = f["circulation"] - f.get("pe_bleed_circulation", 0.0)
        f["circulation"] += (LYSIS_CIRCULATION_TARGET + strain - embolism) * (1 / LYSIS_TAU_MIN)
        f["lung"] += (LYSIS_LUNG_TARGET - f["lung"]) * (1 / LYSIS_TAU_MIN)
    if f.get("lysis_at") is not None:
        # The drug bleeds whether or not it was indicated.
        f["hemoglobin"] -= LYSIS_HEMOGLOBIN_PER_MIN
        since = f["elapsed"] - f["lysis_at"]
        risk = bleeding_risk(state)
        if risk and since >= MAJOR_BLEED_AT_MIN:
            f["hemoglobin"] -= MAJOR_BLEED_HEMOGLOBIN_PER_MIN
            f["circulation"] += MAJOR_BLEED_CIRCULATION_PER_MIN
            # Bleeding lowers the pressure; it is not the embolism's shock.
            f["pe_bleed_circulation"] = f.get("pe_bleed_circulation", 0.0) + MAJOR_BLEED_CIRCULATION_PER_MIN
            if not f.get("major_bleed_reported"):
                f["major_bleed_reported"] = True
                return (f"Bleeding from {BLEED_RISK_TEXT.get(risk, 'the declared site')}: the haemoglobin is falling "
                        "and the pressure with it. This is the risk the thrombolytic carries, and it was taken in a "
                        "patient who had a reason to bleed.")
    if strain > 0 and not f.get("rv_strain_reported") and strain >= .10:
        f["rv_strain_reported"] = True
        return ("The fluid was given faster than the obstructed right ventricle can accept: it distends, the septum "
                "shifts and the output falls. Volume here is given slowly and in small amounts, or not at all.")
    # Written only when it happened: 15 consecutive minutes the embolism kept low.
    # An obstructive shock is not announced, so the room never names the diagnosis.
    if (f.get("sustained_hypotension_min", 0.0) >= SUSTAINED_HYPOTENSION_MIN and f.get("lysis_at") is None
            and not f.get("hypotension_reported")):
        f["hypotension_reported"] = True
        if (f.get("pe_attributable") or {}).get("vasopressor_running"):
            return (f"The systolic pressure has needed a vasopressor to stay at {HYPOTENSION_SBP} mmHg or above, or "
                    f"stayed below it, for {SUSTAINED_HYPOTENSION_MIN} consecutive minutes: this is sustained "
                    "hypotension from the obstruction.")
        return (f"The systolic pressure has stayed below {HYPOTENSION_SBP} mmHg for "
                f"{SUSTAINED_HYPOTENSION_MIN} consecutive minutes: this is sustained hypotension from the obstruction.")
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
