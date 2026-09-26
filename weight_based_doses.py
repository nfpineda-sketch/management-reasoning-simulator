"""A dose written per kilogram, and the weight it needs.

Faculty decision 2 of 2026-09-25 ("Concentración, volumen y dosis por kilo").
A dose per kilogram is accepted for the medicines the engine supports, and the
dose it becomes is shown next to how it was calculated. The weight comes from
the case when the case states one, or from the resident; when neither has
given it, the order is kept whole and only the weight is asked for. A reader's
question is not a clinical minute: asking costs no time.

Until 2026-09-25 the engine assumed 70 kg for the airway drugs when the case
said nothing, and refused every other dose per kilogram. No bank case stated a
weight, so every such order asked for one -- the transitional rule the faculty
accepted until the cases carried verified weights. Encounters launched before
2026-09-27 keep exactly that rule.

Weight rules of 2026-09-27 (faculty; ``patient_body``). The weight is in the
chart and the reader does not ask for it again. For each order per kilogram it
uses, in this order:

1. the weight type the resident wrote with it ("1.2 mg/kg de peso ideal");
2. the one the resident chose earlier in this encounter for the same drug;
3. a rule the faculty agreed for that drug and context (none yet for medicines);
4. the chart's actual weight, and says so -- unless the weight type changes the
   dose materially (actual weight at least 30% above ideal, ``patient_body``). Then
   it asks once which weight is meant, keeps the whole order, and remembers the
   answer for that drug.

Every such order records the weight it used, what kind of weight it was and where
it came from, beside the dose it became. The same executed amount has the same
simulated effect however it was written.
"""
from __future__ import annotations

import re

import patient_body

#: The kinds whose dose may be written per kilogram, and the field each fills.
DOSE_FIELD = {
    "procedural_sedation": "dose_mg", "neuromuscular_blockade": "dose_mg", "opioid_analgesia": "dose_mg",
    "steroid": "dose_mg", "magnesium": "dose_mg", "anticoagulation": "dose", "dextrose": "dose_g",
    "fluid": "volume_ml",
}
#: The per-kilogram fields a parsed order may carry, with the unit each is in.
PER_KG = (("dose_mg_per_kg", "mg"), ("dose_units_per_kg", "units"), ("dose_g_per_kg", "g"),
          ("volume_ml_per_kg", "mL"))
#: Infusions the engine converts from per-kilogram rates at execution.
INFUSIONS = frozenset({"norepinephrine", "epinephrine", "dobutamine"})

WEIGHT_QUESTION = ("This order is written per kilogram and the patient's weight is not recorded. "
                   "What does the patient weigh, in kg? The whole order is kept; only the weight is missing.")
WEIGHT_RETRY = ("Give the patient's weight in kg (for example, 60 kg). "
                "The whole order is kept; only the weight is missing.")
BASIS_RETRY = ("Say which weight this dose should use: actual, ideal or adjusted (or give the weight in kg). "
               "The whole order is kept; nothing has run.")

_KG = r"(?:kg|kgs|kilos?|kilogramos?|kilograms?)"
_STATED = re.compile(r"\b(?:pesa|peso(?:\s+(?:de|aproximado|estimado))?|weighs|weight(?:\s+(?:of|is))?)\s*"
                     r"(?:(?:de|es|:|~|unos|aprox\.?|aproximadamente|about|around)\s*)*(\d+(?:[.,]\d+)?)\s*"
                     + _KG + r"?\b", re.I)
_BARE = re.compile(r"^\s*(?:(?:unos|aprox\.?|aproximadamente|about|around|~)\s*)?(\d+(?:[.,]\d+)?)\s*"
                   + _KG + r"?\s*\.?\s*$", re.I)
_WITH_UNIT = re.compile(r"(\d+(?:[.,]\d+)?)\s*" + _KG + r"\b", re.I)
MIN_KG, MAX_KG = 20.0, 300.0


def per_kg(action):
    """(value, unit) of a dose written per kilogram, or (None, None)."""
    for field, unit in PER_KG:
        if (action or {}).get(field) is not None:
            return float(action[field]), unit
    return None, None


def _rate_per_kg(action):
    """(rate, text) of an infusion written per kilogram, or (None, None)."""
    action = action or {}
    if action.get("type") in INFUSIONS and action.get("units") == "mcg/kg/min" and action.get("rate") is not None:
        return float(action["rate"]), f"{float(action['rate']):g} mcg/kg/min"
    if (action.get("type") == "sedation_infusion" and str(action.get("units", "")).startswith("mg/kg/")
            and action.get("rate") is not None and action.get("operation") != "stop"):
        return float(action["rate"]), f"{float(action['rate']):g} {action['units']}"
    return None, None


def needs_weight(action):
    """Whether this order waits for a weight (or a weight type) before it can run."""
    value, _ = per_kg(action)
    if value is not None and action.get("weight_kg") is None:
        return True
    return bool(action and action.get("weight_question") and action.get("weight_kg") is None)


def _number(text):
    value = float(str(text).replace(",", "."))
    return value if MIN_KG <= value <= MAX_KG else None


def stated_in(text):
    """A weight the resident wrote: "pesa 60 kg", "peso estimado 80", "weighs 60 kg"."""
    match = _STATED.search(str(text or ""))
    return _number(match.group(1)) if match else None


def from_reply(text):
    """The weight given as the answer to the question: "60 kg", "pesa 60", "60"."""
    text = str(text or "")
    for pattern in (_STATED, _BARE, _WITH_UNIT):
        match = pattern.search(text)
        if match:
            return _number(match.group(1))
    return None


def weight_of(state):
    """(kg, source) the encounter already knows, or (None, None). The rule before 2026-09-27."""
    case = (((state or {}).get("encounter_spec") or {}).get("clinical_case") or {})
    declared = (case.get("patient") or {}).get("weight_kg")
    if declared:
        return float(declared), "case"
    stated = (state or {}).get("stated_weight") or {}
    if stated.get("kg"):
        return float(stated["kg"]), "resident"
    return None, None


def _patient(state):
    return patient_body.case_of(state).get("patient") or {}


def drug_of(action):
    """What a remembered weight type belongs to: the drug, not the order."""
    action = action or {}
    return f"{action.get('type')}:{action.get('agent') or ''}"


def _label(action):
    name = action.get("agent") or {"fluid": "The fluid", "dextrose": "Dextrose"}.get(action.get("type"),
                                                                                   action.get("type"))
    value, unit = per_kg(action)
    if value is not None:
        return str(name).capitalize(), f"{value:g} {unit}/kg"
    rate, text = _rate_per_kg(action)
    return str(name).capitalize(), text


def apply(action, kg, source, basis=None, description=None):
    """Turn a per-kilogram order into its dose (or its rate's weight), and say how it was calculated."""
    value, unit = per_kg(action)
    rate, rate_text = _rate_per_kg(action)
    if value is None and rate is None:
        return action
    if value is not None and action.get("type") not in DOSE_FIELD:
        return action
    kg = round(float(kg), 1)
    result = ""
    if value is not None:
        dose = round(value * kg, 3)
        field = DOSE_FIELD[action["type"]]
        action[field] = dose
        if field == "dose":
            action["units"] = unit
        written = f"{value:g} {unit}/kg"
    else:
        # A rate stays as written; what it amounts to on this weight is shown.
        written = rate_text
        per = "mcg/min" if action.get("type") in INFUSIONS else action["units"].replace("/kg", "")
        result = f" = {round(rate * kg, 2):g} {per}"
    action["weight_kg"] = kg
    action["weight_source"] = source
    action.pop("weight_question", None)
    if basis:
        action["weight_basis"] = basis
    how = f", {description}" if description else ""
    action["dose_basis"] = f"{written} × {kg:g} kg{result}{how}"
    return action


def _choice(state, action):
    return ((state or {}).get("weight_choices") or {}).get(drug_of(action))


def _choose(action, state, written=None):
    """(kg, source, basis, description) for this order, or (None, question kind, basis, text)."""
    patient = _patient(state)
    named = action.get("weight_basis")
    if named:
        kg, description = patient_body.dosing_weight(patient, named)
        if kg is None:
            return None, "weight", named, description
        return kg, "resident", named, description
    if written:
        # A weight the resident wrote with the order is the one they dosed on; the
        # chart keeps its own, and the record shows both.
        chart, _ = patient_body.dosing_weight(patient, "actual")
        return written, "resident", None, ("the weight written with the order"
                                           + (f"; the chart records {chart:g} kg" if chart and chart != written else ""))
    remembered = _choice(state, action)
    if remembered:
        if remembered.get("basis"):
            kg, description = patient_body.dosing_weight(patient, remembered["basis"])
            if kg is not None:
                return kg, "resident", remembered["basis"], f"{description}; chosen earlier for this drug"
        if remembered.get("kg"):
            return float(remembered["kg"]), "resident", None, "the weight the resident gave for this drug"
    agreed = patient_body.agreed_basis(action.get("type"), action.get("context"))
    if agreed:
        kg, description = patient_body.dosing_weight(patient, agreed)
        if kg is not None:
            return kg, "rule", agreed, description
    kg, description = patient_body.dosing_weight(patient, "actual")
    if kg is None:
        stated = (state or {}).get("stated_weight") or {}
        if stated.get("kg"):
            return float(stated["kg"]), "resident", None, "the weight the resident gave"
        return None, "weight", None, None
    if patient_body.relevant_ambiguity(patient):
        return None, "basis", None, None
    return kg, "chart", "actual", description


def question_for(parsed, waiting, state):
    """The reader's one question for every order in this submission waiting for its weight."""
    actions = [(parsed or {}).get("actions", [])[index] for index in waiting]
    if actions and all(action.get("weight_question") == "basis" for action in actions):
        names = [" ".join(_label(action)) for action in actions]
        names = names[:1] + [name[0].lower() + name[1:] for name in names[1:]]
        joined = names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]
        return patient_body.basis_question(joined, _patient(state), None)
    return question(actions[0], state) if actions else WEIGHT_QUESTION


def question(action, state):
    """The reader's question for an order waiting for its weight."""
    kind = action.get("weight_question")
    name, written = _label(action)
    if kind == "basis":
        return patient_body.basis_question(f"{name} {written}", _patient(state), None)
    if kind == "weight" and action.get("weight_basis"):
        _, why = patient_body.dosing_weight(_patient(state), action["weight_basis"])
        return (f"{name} {written} names the {patient_body.BASES[action['weight_basis']]}, but {why}, so it cannot "
                f"be calculated. What weight should this dose use, in kg? The whole order is kept; nothing has run.")
    return WEIGHT_QUESTION


def resolve(parsed, state):
    """Fill every per-kilogram dose the known weight allows; return what still waits.

    Before 2026-09-27 the weight is the case's, then one the resident already
    gave in this encounter, then one written in this very order. Returns the
    indices of the actions still waiting for a weight (or a weight type).
    """
    actions = (parsed or {}).get("actions", []) or []
    if not patient_body.rules_apply(state):
        known, source = weight_of(state)
        if known is None:
            written = stated_in((parsed or {}).get("raw_text", ""))
            if written is not None:
                known, source = written, "resident"
        waiting = []
        for index, action in enumerate(actions):
            if not needs_weight(action):
                continue
            if known is None:
                waiting.append(index)
            else:
                apply(action, known, source)
        return waiting
    waiting = []
    written = stated_in((parsed or {}).get("raw_text", ""))
    for index, action in enumerate(actions):
        value, _ = per_kg(action)
        rate, _ = _rate_per_kg(action)
        if (value is None and rate is None) or action.get("weight_kg") is not None:
            continue
        kg, source, basis, description = _choose(action, state, written)
        if kg is None:
            action["weight_question"] = source
            if basis:
                action["weight_basis"] = basis
            waiting.append(index)
        else:
            apply(action, kg, source, basis, description)
    return waiting


def answer(action, text, state):
    """Complete a waiting order with the resident's answer; returns the retry message if unanswered."""
    kind = action.get("weight_question") or "weight"
    if kind == "basis":
        basis = patient_body.basis_answer(text)
        if basis:
            kg, description = patient_body.dosing_weight(_patient(state), basis)
            if kg is not None:
                apply(action, kg, "resident", basis, description)
                return None
        kg = from_reply(text)
        if kg is None:
            return BASIS_RETRY
        apply(action, kg, "resident", None, "the weight the resident gave")
        return None
    kg = from_reply(text)
    if kg is None:
        return WEIGHT_RETRY
    apply(action, kg, "resident", action.get("weight_basis") if action.get("weight_question") else None,
          "the weight the resident gave" if patient_body.rules_apply(state) else None)
    return None


def remember(state, parsed):
    """Keep what the resident gave, so the next order per kilogram uses it."""
    if patient_body.rules_apply(state):
        for action in (parsed or {}).get("actions", []) or []:
            if action.get("weight_source") != "resident" or not action.get("weight_kg"):
                continue
            state.setdefault("weight_choices", {})[drug_of(action)] = {
                "basis": action.get("weight_basis"), "kg": float(action["weight_kg"]),
                "at_min": state.get("sim_time", 0)}
        return
    for action in (parsed or {}).get("actions", []) or []:
        if action.get("weight_source") == "resident" and action.get("weight_kg"):
            if not (state.get("stated_weight") or {}).get("kg"):
                state["stated_weight"] = {"kg": float(action["weight_kg"]), "source": "resident",
                                          "at_min": state.get("sim_time", 0)}
            return


# --------------------------------------------------------------------------- the engine's side

def fallback_weight(state, action):
    """The weight of a per-kilogram order that reached the engine without the reader (tools, harnesses).

    Nobody is there to answer a question, so under the 2026-09-27 rules it is the
    weight the order names or the chart's actual weight; before, the case's or 70 kg.
    """
    if not patient_body.rules_apply(state):
        return float(_patient(state).get("weight_kg") or 70)
    kg, _, _, _ = _choose(action, state)
    if kg is None:
        kg, _ = patient_body.dosing_weight(_patient(state), "actual")
    return float(kg or 70)


def infusion_weight(state, action):
    """(kg, basis) that turns this infusion's mcg/kg/min into mcg/min."""
    if action.get("weight_kg"):
        return float(action["weight_kg"]), action.get("weight_basis")
    if not patient_body.rules_apply(state):
        return float(_patient(state).get("weight_kg") or 70), None
    remembered = _choice(state, action)
    if remembered and remembered.get("kg"):
        return float(remembered["kg"]), remembered.get("basis")
    kg, _ = patient_body.dosing_weight(_patient(state), "actual")
    return (float(kg), "actual") if kg else (float(_patient(state).get("weight_kg") or 70), None)


def effect_weight(state):
    """The weight a drug's simulated effect is measured against.

    One weight per patient, whatever weight type the order was written on, so
    the same executed amount always has the same effect. Under the 2026-09-27
    rules it is the chart's actual weight -- the engine's convention until the
    faculty decides each drug (decisions C and E); before, the case's or 70 kg.
    """
    if patient_body.rules_apply(state):
        kg, _ = patient_body.dosing_weight(_patient(state), "actual")
        if kg:
            return float(kg)
    return float(_patient(state).get("weight_kg") or 70)
