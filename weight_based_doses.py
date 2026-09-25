"""A dose written per kilogram, and the weight it needs.

Faculty decision 2 of 2026-09-25 ("Concentración, volumen y dosis por kilo").
A dose per kilogram is accepted for the medicines the engine supports, and the
dose it becomes is shown next to how it was calculated. The weight comes from
the case when the case states one, or from the resident; when neither has
given it, the order is kept whole and only the weight is asked for. A reader's
question is not a clinical minute: asking costs no time.

Until 2026-09-25 the engine assumed 70 kg for the airway drugs when the case
said nothing, and refused every other dose per kilogram. No bank case states a
weight, so today every such order asks for one -- the transitional rule the
faculty accepted until the cases carry verified weights.
"""
from __future__ import annotations

import re

#: The kinds whose dose may be written per kilogram, and the field each fills.
DOSE_FIELD = {
    "procedural_sedation": "dose_mg", "neuromuscular_blockade": "dose_mg", "opioid_analgesia": "dose_mg",
    "steroid": "dose_mg", "magnesium": "dose_mg", "anticoagulation": "dose", "dextrose": "dose_g",
}
#: The per-kilogram fields a parsed order may carry, with the unit each is in.
PER_KG = (("dose_mg_per_kg", "mg"), ("dose_units_per_kg", "units"), ("dose_g_per_kg", "g"))

WEIGHT_QUESTION = ("This order is written per kilogram and the patient's weight is not recorded. "
                   "What does the patient weigh, in kg? The whole order is kept; only the weight is missing.")

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


def needs_weight(action):
    value, _ = per_kg(action)
    return value is not None and action.get("weight_kg") is None


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
    """(kg, source) the encounter already knows, or (None, None)."""
    case = (((state or {}).get("encounter_spec") or {}).get("clinical_case") or {})
    declared = (case.get("patient") or {}).get("weight_kg")
    if declared:
        return float(declared), "case"
    stated = (state or {}).get("stated_weight") or {}
    if stated.get("kg"):
        return float(stated["kg"]), "resident"
    return None, None


def apply(action, kg, source):
    """Turn a per-kilogram dose into the dose, and say how it was calculated."""
    value, unit = per_kg(action)
    if value is None or action.get("type") not in DOSE_FIELD:
        return action
    dose = round(value * kg, 3)
    field = DOSE_FIELD[action["type"]]
    action[field] = dose
    if field == "dose":
        action["units"] = unit
    action["weight_kg"] = kg
    action["weight_source"] = source
    action["dose_basis"] = f"{value:g} {unit}/kg × {kg:g} kg"
    return action


def resolve(parsed, state):
    """Fill every per-kilogram dose the known weight allows; return what still waits.

    The weight is the case's, then one the resident already gave in this
    encounter, then one written in this very order. Returns the indices of the
    actions still waiting for a weight.
    """
    known, source = weight_of(state)
    if known is None:
        written = stated_in((parsed or {}).get("raw_text", ""))
        if written is not None:
            known, source = written, "resident"
    waiting = []
    for index, action in enumerate((parsed or {}).get("actions", []) or []):
        if not needs_weight(action):
            continue
        if known is None:
            waiting.append(index)
        else:
            apply(action, known, source)
    return waiting


def remember(state, parsed):
    """Keep a weight the resident gave, so the next order per kilogram uses it."""
    for action in (parsed or {}).get("actions", []) or []:
        if action.get("weight_source") == "resident" and action.get("weight_kg"):
            if not (state.get("stated_weight") or {}).get("kg"):
                state["stated_weight"] = {"kg": float(action["weight_kg"]), "source": "resident",
                                          "at_min": state.get("sim_time", 0)}
            return
