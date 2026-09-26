"""Weight and height: what the chart shows, and the weight each calculation uses (faculty, 2026-09-27).

The faculty approved weight and height in every bank case, shown in the
patient's chart, for new encounters only. The table below (``BODIES``) was drawn
once and reproducibly (``docs/PESOS_CASOS.md``: seed, method, constraints) and
checked against the faculty's conditions: body habitus independent of age,
diagnosis, severity, response to treatment and expected conduct; nobody given a
normal weight because of chemotherapy, alcohol or poor intake; heights that vary
as adults' do. No clinical history was changed to justify a weight, and no weight
was chosen to fit a photograph.

What a case records, in ``patient["body"]``:

- ``weight_kg`` with ``weight_how`` (measured, reported or estimated) and
  ``weight_by`` (where, or by whom). The engine uses the number the chart
  shows. An estimate is labelled as one; it is never corrected in secret.
- ``height_m`` with ``height_how`` and ``height_by``.
- ``dry_weight_kg`` with ``dry_weight_by``: a previous dry weight (dialysis). It
  is never today's weight, and no dose is calculated on it unless the resident
  asks for it by name.

Which rules an encounter follows. An encounter launched from 2026-09-27 carries
``weight_rules`` in its spec. One launched before has none, and every
calculation keeps the rules it started with: the engine's 70 kg for the
physiology, and the resident's own weight for a dose per kilogram. Nothing
already played is recalculated.

The weight of each calculation (``dosing_weight``):

- A tidal volume per kilogram uses the predicted body weight (faculty decision
  B, 2026-09-27): Devine/ARDSNet, from sex and height, with the formula shown.
- A dose per kilogram uses the weight type the resident wrote ("peso ideal",
  "actual body weight", ...). Otherwise it uses the chart's weight, and says so.
- When the resident names no weight type, no rule has been agreed for the drug,
  and the choice changes the dose materially (actual weight at least 30% above
  ideal), the reader asks once per drug per encounter, and remembers the
  answer.
- The engine's physiology parameters whose weight basis the faculty has not
  decided keep the weight they were calibrated on (``engine_reference_weight``):
  required minute ventilation, the ventilator's default tidal volume, and
  baseline urine output. Adding a weight to the chart does not silently change
  them.
"""
from __future__ import annotations

import re
from copy import deepcopy

#: Marks the encounters that follow these rules. Stored in the spec at launch.
RULES = "2026-09-27"
#: The weight every bank case was computed at before cases carried one.
ENGINE_REFERENCE_WEIGHT_KG = 70.0
#: The actual weight above which the weight type changes a dose materially
#: (actual weight / ideal weight). A simulator convention, pending the faculty's
#: decision table.
RELEVANT_RATIO = 1.30

_SOURCE_DRAW = "docs/PESOS_CASOS.md"


def _body(weight, how, by, height, height_how=None, height_by=None, **extra):
    return {"weight_kg": weight, "weight_how": how, "weight_by": by, "height_m": height,
            "height_how": height_how or how, "height_by": height_by or by, **extra}


# The 31 bank cases (2026-09-27): seed "pesos-casos-2026-09-27", see _SOURCE_DRAW.
# How each was obtained follows the arrival: an alert, stable patient is weighed
# and measured at triage; an alert patient too unwell to stand reports it; a
# patient who cannot answer has it reported by the family member who came, or
# estimated by the team when nobody present would know it.
BODIES = {
    "pneumonia_46f": _body(58, "measured", "at triage", 1.59),
    "pneumonia_83m": _body(77, "reported", "by his daughter", 1.71),
    "pulmonary_edema_58m": _body(75, "reported", "by the patient", 1.66),
    "pulmonary_edema_75f": _body(120, "reported", "by the patient", 1.66),
    "acs_54m_inferior": _body(85, "measured", "at triage", 1.62),
    "acs_66f_nonst": _body(50, "measured", "at triage", 1.59),
    "acs_61m_posterior": _body(99, "measured", "at triage", 1.72),
    "acs_52m_de_winter": _body(96, "measured", "at triage", 1.62),
    "acs_48m_wellens": _body(75, "measured", "at triage", 1.57),
    "acs_70f_left_main": _body(60, "measured", "at triage", 1.43),
    "pulmonary_embolism_33f": _body(47, "measured", "at triage", 1.54),
    "pulmonary_embolism_61m": _body(83, "reported", "by the patient", 1.69),
    "asthma_24f": _body(83, "measured", "at triage", 1.70),
    "asthma_49m": _body(76, "reported", "by his partner", 1.75),
    "gi_bleed_57m": _body(111, "reported", "by the patient", 1.76),
    "gi_bleed_72f": _body(75, "measured", "at triage", 1.65),
    "hypoglycemia_28m": _body(102, "estimated", "by the team", 1.73),
    "hypoglycemia_76f": _body(89, "reported", "by her son", 1.62),
    "hypoglycemia_54m_thiamine": _body(77, "estimated", "by the team", 1.89),
    "opioid_35m": _body(81, "estimated", "by the team", 1.67),
    "opioid_67f": _body(82, "reported", "by her spouse", 1.55),
    "anaphylaxis_29f": _body(73, "reported", "by the patient", 1.65),
    "anaphylaxis_63m_betablocked": _body(115, "reported", "by his wife", 1.72),
    "renal_colic_34m": _body(109, "measured", "at triage", 1.68),
    "obstructive_pyelonephritis_58f": _body(78, "measured", "at triage", 1.69),
    "bradycardia_ccb_68m": _body(65, "reported", "by his daughter", 1.71),
    "bradycardia_avb3_78f": _body(54, "reported", "by her son", 1.55),
    "bradycardia_bb_54f": _body(64, "reported", "by her partner", 1.47),
    # He missed his last two dialysis sessions and has eaten and drunk as usual:
    # today's weight is above the dry weight his dialysis unit set.
    "bradycardia_hyperk_63m": _body(122, "measured", "on the bed scale", 1.64, "reported", "by the patient",
                                    dry_weight_kg=117,
                                    dry_weight_by="his dialysis unit's record, before the two missed sessions"),
    "trauma_limb_hemorrhage_27m": _body(74, "reported", "by the patient", 1.66),
    "trauma_hemothorax_41m": _body(56, "reported", "by the patient", 1.70),
}


def body_for(case_id):
    """The recorded body of a bank case, as a copy, or None."""
    record = BODIES.get(case_id)
    return deepcopy(record) if record is not None else None


# --------------------------------------------------------------------------- which rules

def case_of(state):
    return ((state or {}).get("encounter_spec") or {}).get("clinical_case") or {}


def rules_apply(state):
    """Whether this encounter was launched under the 2026-09-27 weight rules."""
    return bool(((state or {}).get("encounter_spec") or {}).get("weight_rules"))


# --------------------------------------------------------------------------- the body

def body(patient):
    """What the case records about weight and height, or None.

    A bank case records ``patient["body"]``. A generated case records only a
    weight (``patient["weight_kg"]``), which the chart shows as recorded in the
    case, with no height.
    """
    patient = patient or {}
    recorded = patient.get("body")
    if isinstance(recorded, dict) and _number(recorded.get("weight_kg")):
        return recorded
    weight = patient.get("weight_kg")
    if _number(weight):
        return {"weight_kg": float(weight), "weight_how": "recorded", "weight_by": "in the case",
                "height_m": patient.get("height_m") if _number(patient.get("height_m")) else None}
    return None


def _number(value):
    return not isinstance(value, bool) and isinstance(value, (int, float)) and value > 0


def predicted_weight(sex, height_m):
    """Predicted (= ideal) body weight, Devine/ARDSNet, in kg, to one decimal."""
    if sex not in ("male", "female") or not _number(height_m):
        return None
    return round((50.0 if sex == "male" else 45.5) + 0.91 * (height_m * 100 - 152.4), 1)


def predicted_formula(sex, height_m):
    """The calculation, written out: "50 + 0.91 × (170 − 152.4) = 66.0 kg"."""
    value = predicted_weight(sex, height_m)
    if value is None:
        return None
    base = "50" if sex == "male" else "45.5"
    return f"{base} + 0.91 × ({height_m * 100:.0f} − 152.4) = {value:.1f} kg"


def lean_weight(sex, weight_kg, height_m):
    """Lean body weight (Janmahasatian 2005), in kg, to one decimal."""
    if sex not in ("male", "female") or not _number(weight_kg) or not _number(height_m):
        return None
    bmi = weight_kg / height_m ** 2
    if sex == "male":
        return round(9270 * weight_kg / (6680 + 216 * bmi), 1)
    return round(9270 * weight_kg / (8780 + 244 * bmi), 1)


def bmi(patient):
    """Body-mass index from the recorded weight and height, or None."""
    recorded = body(patient)
    if not recorded or not _number(recorded.get("height_m")):
        return None
    return round(recorded["weight_kg"] / recorded["height_m"] ** 2, 1)


#: Weight types a resident can name, and what the record calls each.
BASES = {
    "actual": "actual body weight",
    "ideal": "ideal body weight",
    "predicted": "predicted body weight",
    "adjusted": "adjusted body weight",
    "lean": "lean body weight",
    "dry": "previous dry weight",
}


def weights(patient):
    """{basis: kg} for every weight type this case allows; missing ones are None."""
    recorded = body(patient) or {}
    actual = float(recorded["weight_kg"]) if _number(recorded.get("weight_kg")) else None
    sex = (patient or {}).get("sex")
    ideal = predicted_weight(sex, recorded.get("height_m"))
    adjusted = round(ideal + 0.4 * (actual - ideal), 1) if actual and ideal and actual > ideal else (
        actual if actual and ideal else None)
    return {"actual": actual, "ideal": ideal, "predicted": ideal, "adjusted": adjusted,
            "lean": lean_weight(sex, actual, recorded.get("height_m")),
            "dry": float(recorded["dry_weight_kg"]) if _number(recorded.get("dry_weight_kg")) else None}


def relevant_ambiguity(patient):
    """Whether actual and ideal weight differ enough that the weight type changes a dose."""
    known = weights(patient)
    return bool(known["actual"] and known["ideal"] and known["actual"] >= RELEVANT_RATIO * known["ideal"])


def engine_reference_weight(patient):
    """The weight of the physiology parameters whose weight basis is still undecided.

    Required minute ventilation, the ventilator's default tidal volume and
    baseline urine output were calibrated with every bank case at 70 kg. Until
    the faculty decides their basis (docs/PESOS_CASOS.md, pending decisions),
    they keep what each case used before: a generated case's own recorded
    weight, and 70 kg for a bank case.
    """
    weight = (patient or {}).get("weight_kg")
    return float(weight) if _number(weight) else ENGINE_REFERENCE_WEIGHT_KG


# --------------------------------------------------------------------------- weight types in the resident's words

_BASIS_WORDS = (
    ("dry", r"peso\s+seco|dry\s+(?:body\s+)?weight"),
    ("adjusted", r"peso\s+(?:corporal\s+)?ajustado|adjusted\s+(?:body\s+)?weight|\badjbw\b"),
    ("lean", r"peso\s+(?:corporal\s+)?magro|lean\s+(?:body\s+)?(?:weight|mass)|\blbw\b"),
    ("predicted", r"peso\s+(?:corporal\s+)?predicho|predicted\s+(?:body\s+)?weight|\bpbw\b"),
    ("ideal", r"peso\s+(?:corporal\s+)?ideal|ideal\s+(?:body\s+)?weight|\bibw\b"),
    ("actual", r"peso\s+(?:corporal\s+)?(?:real|actual|total)|(?:actual|total|real)\s+(?:body\s+)?weight"
               r"|\btbw\b"),
)
_BASIS_PATTERNS = tuple((basis, re.compile(pattern, re.I)) for basis, pattern in _BASIS_WORDS)


def basis_in(text):
    """The weight type a resident named in this text, or None ("ABW" is ambiguous and is not read)."""
    text = str(text or "")
    for basis, pattern in _BASIS_PATTERNS:
        if pattern.search(text):
            return basis
    return None


_ANSWERS = (
    ("actual", r"^\s*(?:el\s+|la\s+)?(?:real|actual|total|tbw|the\s+actual|actual\s+one|peso\s+real|peso\s+actual)\b"),
    ("ideal", r"^\s*(?:el\s+|la\s+)?(?:ideal|ibw|the\s+ideal|peso\s+ideal)\b"),
    ("predicted", r"^\s*(?:el\s+|la\s+)?(?:predicho|predicted|pbw|peso\s+predicho)\b"),
    ("adjusted", r"^\s*(?:el\s+|la\s+)?(?:ajustado|adjusted|adjbw|peso\s+ajustado)\b"),
    ("lean", r"^\s*(?:el\s+|la\s+)?(?:magro|lean|lbw|peso\s+magro)\b"),
    ("dry", r"^\s*(?:el\s+|la\s+)?(?:seco|dry|peso\s+seco)\b"),
)


def basis_answer(text):
    """The weight type given as the answer to the reader's question, or None."""
    text = str(text or "")
    named = basis_in(text)
    if named:
        return named
    for basis, pattern in _ANSWERS:
        if re.search(pattern, text, re.I):
            return basis
    return None


# --------------------------------------------------------------------------- the weight each calculation uses

#: Rules the faculty agreed: (kind, context) -> basis. Decision B of 2026-09-27.
AGREED = {("ventilator", "tidal_volume"): "predicted"}


def agreed_basis(kind, context=None):
    return AGREED.get((kind, context))


def dosing_weight(patient, basis):
    """(kg, description) of one weight type for this patient, or (None, why not)."""
    known = weights(patient)
    kg = known.get(basis)
    recorded = body(patient) or {}
    if kg is None:
        if basis in ("ideal", "predicted", "adjusted", "lean") and not _number(recorded.get("height_m")):
            return None, "the height is not recorded"
        if basis == "dry":
            return None, "no dry weight is recorded"
        return None, "the weight is not recorded"
    if basis == "actual":
        how = recorded.get("weight_how")
        source = (f"{how} {recorded.get('weight_by', '')}".strip() if how else "chart")
        return kg, f"actual body weight, {source}"
    if basis in ("ideal", "predicted"):
        return kg, f"{BASES[basis]}: {predicted_formula((patient or {}).get('sex'), recorded['height_m'])}"
    if basis == "adjusted":
        return kg, (f"adjusted body weight: ideal {known['ideal']:g} + 0.4 × (actual {known['actual']:g} − "
                    f"ideal {known['ideal']:g})")
    if basis == "lean":
        return kg, "lean body weight (Janmahasatian)"
    return kg, f"previous dry weight, {recorded.get('dry_weight_by', 'recorded')}"


def basis_question(label, patient, _unused=None):
    """The reader's question when the weight type changes a dose materially."""
    known = weights(patient)
    options = [f"actual {known['actual']:g} kg", f"ideal {known['ideal']:g} kg"]
    if known.get("adjusted") and known["adjusted"] not in (known["actual"], known["ideal"]):
        options.append(f"adjusted {known['adjusted']:g} kg")
    plural = " and " in label
    return (f"{label} {'are' if plural else 'is'} written per kilogram and no weight type was named. This "
            f"patient's actual weight is well above the ideal weight, so the dose depends on which is meant: "
            f"{', '.join(options)}. Which weight should {'they' if plural else 'it'} use? The whole order is kept; "
            f"nothing has run.")


# --------------------------------------------------------------------------- the chart

_HOW = {"measured": "measured", "reported": "reported", "estimated": "estimated, not weighed",
        "recorded": "recorded"}


def chart_lines(patient):
    """What the patient's chart shows about weight and height, one line each."""
    recorded = body(patient)
    if not recorded:
        return ["Weight not recorded"]
    how = recorded.get("weight_how")
    by = recorded.get("weight_by", "")
    if how == "estimated":
        weight = f"Weight {recorded['weight_kg']:g} kg (estimated {by}; the patient could not be weighed)"
    else:
        weight = f"Weight {recorded['weight_kg']:g} kg ({_HOW.get(how, how)} {by})".replace(" )", ")")
    lines = [weight]
    if _number(recorded.get("dry_weight_kg")):
        lines.append(f"Previous dry weight {recorded['dry_weight_kg']:g} kg ({recorded.get('dry_weight_by', '')}; "
                     f"not today's weight)")
    if _number(recorded.get("height_m")):
        height_how = recorded.get("height_how", how)
        height_by = recorded.get("height_by", by)
        lines.append(f"Height {recorded['height_m']:.2f} m ({_HOW.get(height_how, height_how)} {height_by})"
                     .replace("(estimated, not weighed", "(estimated"))
    else:
        lines.append("Height not recorded")
    return lines
