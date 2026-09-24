"""Bleeding that does not stop until somebody stops it.

Authored teaching magnitudes pending faculty review, used only by the bank's
trauma family. Nothing here is a prescribing threshold or a resuscitation
target.

Two faculty decisions of 2026-09-23 shape the whole of this module, and both are
about sequence rather than about numbers.

**The x of xABCDE.** Version 11 puts exsanguinating haemorrhage before the
airway, and the faculty asked for the engine to hold a resident to it. So an
uncontrolled external source bleeds every simulated minute until a tourniquet,
direct pressure or packing stops it, and the minutes spent intubating first are
paid for in volume. The engine refuses nothing and punishes nothing: it just
keeps bleeding, and the record shows when it stopped.

**The massive haemothorax is not a volume.** In the faculty's own words: it is
defined "no solo por el volumen sino que tambien por la inestabilidad
hemodinamica, independiente del volumen inicial que se drene. Si se drena y
sigue inestable, se debe volver a buscar un sitio de sangrado, intraabdominal,
pelvis por ejemplo. Si se ha descartado otro sitio de sangrado y sigue
hipotenso, mal perfundido con el tubo pleural instalado, debe ir a pabellon."

So the case is a sequence and not a threshold: drain, look again, and when there
is nowhere else to look and the patient is still bleeding, the treatment is a
theatre this engine does not have. The drained volume is recorded because a
resident should see it; it is not what decides anything.
"""

#: Millilitres lost per simulated minute from an uncontrolled source, at full
#: severity. An arterial limb wound empties a person faster than a pelvis does,
#: and the difference is the reason the x comes first.
BLEED_ML_PER_MIN = {
    "external": 145.0,
    "thoracic": 70.0,
    "pelvic": 55.0,
    "abdominal": 48.0,
}

#: What each control measure leaves behind. Zero is a source that is stopped;
#: the others are slowed, which is why they still end in an operating theatre.
RESIDUAL_AFTER_CONTROL = {
    "external": 0.0,      # a tourniquet above an arterial wound stops it
    "pelvic": .35,        # a binder reduces the volume it can bleed into
    "thoracic": .55,      # a drain empties the chest; it does not close the vessel
    "abdominal": 1.0,     # nothing in this department controls it
}

#: Tranexamic acid, given early. A modest, whole-patient reduction, not a
#: haemostat: it never turns an uncontrolled source into a controlled one.
TXA_REDUCTION = .12
TXA_WINDOW_MIN = 180

#: Circulating volume of the modelled adult, and what the deficit costs.
BLOOD_VOLUME_ML = 5000.0
#: Fraction of the deficit each replacement makes up. Blood replaces what was
#: lost; crystalloid fills a space without carrying anything.
BLOOD_REPLACEMENT_ML_PER_UNIT = 300.0
CRYSTALLOID_REPLACEMENT_FRACTION = .30

#: What a class of shock looks like, as fractions of the circulating volume.
SHOCK_SBP_AT_FULL = 90.0        # systolic lost at a 40% deficit
SHOCK_HR_AT_FULL = 70.0
SHOCK_CRT_AT_FULL = 5.0
FULL_DEFICIT_FRACTION = .40

ARREST_DEFICIT_FRACTION = .50
ARREST_TEXT = (
    "Circulatory arrest from uncontrolled haemorrhage. The bleeding had not been "
    "stopped, and no volume replaces a source that is still open."
)


def spec(state):
    case = state.get("encounter_spec", {}).get("clinical_case", {}) or {}
    return case.get("engine", {}).get("trauma", {}) or {}


def sources(state):
    """The bleeding sources this case carries, with their severities."""
    declared = spec(state).get("sources") or {}
    return {name: float(weight) for name, weight in declared.items()
            if name in BLEED_ML_PER_MIN and float(weight) > 0}


def controlled(f, source):
    """How much of this source's control has been achieved, from 0 to 1."""
    return min(1.0, float(f.get("hemorrhage_control", {}).get(source, 0.0)))


def control(f, source, fraction=1.0):
    """Record that a control measure was applied to a source."""
    achieved = f.setdefault("hemorrhage_control", {})
    achieved[source] = min(1.0, achieved.get(source, 0.0) + float(fraction))
    f.setdefault("hemorrhage_control_at", {}).setdefault(source, f.get("elapsed", 0))


def bleeding_ml_per_min(f, state):
    """What is being lost this minute, from every source that is still open."""
    total = 0.0
    for source, severity in sources(state).items():
        residual = 1.0 - controlled(f, source) * (1 - RESIDUAL_AFTER_CONTROL[source])
        total += BLEED_ML_PER_MIN[source] * severity * residual
    if f.get("txa_at") is not None and f["elapsed"] - f["txa_at"] <= TXA_WINDOW_MIN:
        total *= (1 - TXA_REDUCTION)
    return total


def deficit_fraction(f):
    """How much of the circulating volume is missing, after replacement."""
    replaced = (float(f.get("blood_delivered_units", 0)) * BLOOD_REPLACEMENT_ML_PER_UNIT
                + float(f.get("fluid_delivered_ml", 0)) * CRYSTALLOID_REPLACEMENT_FRACTION)
    missing = max(0.0, float(f.get("blood_lost_ml", 0.0)) - replaced)
    return min(1.0, missing / BLOOD_VOLUME_ML)


def step(f, state):
    """Lose a minute's worth of blood. Returns a procedure event, or None.

    The arrival deficit is seeded as blood already lost, so that the numbers the
    case authors are the numbers the engine starts from. Without it, stopping
    the bleeding raised the pressure above what the patient arrived with, which
    is not what a tourniquet does.
    """
    arrival = float(spec(state).get("arrival_deficit", 0.0))
    f.setdefault("arrival_deficit", arrival)
    f.setdefault("blood_lost_ml", arrival * BLOOD_VOLUME_ML)
    f["blood_lost_ml"] += bleeding_ml_per_min(f, state)
    if (deficit_fraction(f) >= ARREST_DEFICIT_FRACTION and not f.get("hemorrhage_arrest")):
        f["hemorrhage_arrest"] = True
        return ARREST_TEXT
    return None


def observables(f):
    """What the deficit is doing to the numbers, as differences from arrival."""
    moved = min(1.0, deficit_fraction(f) / FULL_DEFICIT_FRACTION)
    arrival = min(1.0, float(f.get("arrival_deficit", 0.0)) / FULL_DEFICIT_FRACTION)
    change = moved - arrival
    return {"sbp_drop": SHOCK_SBP_AT_FULL * change,
            "hr_rise": SHOCK_HR_AT_FULL * change,
            "crt_rise": SHOCK_CRT_AT_FULL * change}


# --- the massive haemothorax, as a sequence rather than a threshold ---------

def drained_ml(f):
    return float(f.get("thoracic_drained_ml", 0.0))


def unstable(observable):
    """The instability that defines this haemothorax, whatever volume came out."""
    o = observable or {}
    try:
        return float(o.get("sbp", 120)) < 90 or float(o.get("crt", 2)) >= 4
    except (TypeError, ValueError):
        return False


def searched_again(f):
    """True when another site was looked for after the chest was drained.

    The E-FAST and the pelvic radiograph are the two this engine has. Looking
    before the drain does not count: the decision the faculty described is what
    the resident does **after** the chest has been emptied and the patient is
    still unstable.
    """
    drained_at = f.get("thoracostomy_at")
    if drained_at is None:
        return False
    return any(when is not None and when >= drained_at
               for when in (f.get("efast_at"), f.get("pelvis_xray_at")))


def theatre_indicated(f, observable):
    """Drained, still unstable, and nowhere else left to look."""
    return bool(f.get("thoracostomy_at") is not None
                and unstable(observable)
                and searched_again(f)
                and not f.get("other_site_found"))
