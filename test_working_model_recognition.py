"""A working model written the way clinicians write it must be recognised.

In local testing the working model was the slot the interpreter missed most, and
a missed slot holds every order in the submission. Clinicians state it as a bare
diagnostic sentence ("Acute hypertensive pulmonary edema."), as "I think this is
...", with a hedge ("Likely ..."), or in Spanish, and all of those were refused.

The other half matters as much: nothing here may manufacture a working model the
resident did not express. Orders, priorities and expectations stay in their own
slots even when they name a condition.
"""
import ast
from copy import deepcopy
from html import escape
from io import BytesIO
import json
import math
from pathlib import Path
import random
import re

import pytest

ROOT = Path(__file__).resolve().parent


class _SessionState(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__


class _Streamlit:
    def __init__(self):
        self.session_state = _SessionState()


@pytest.fixture(scope="module")
def extract():
    source = (ROOT / "app.py").read_text()
    nodes = [n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef)]
    namespace = {"st": _Streamlit(), "re": re, "math": math, "random": random, "json": json,
                 "deepcopy": deepcopy, "escape": escape, "BytesIO": BytesIO, "__file__": "app.py"}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "app.py", "exec"), namespace)
    return namespace["extract_explicit_reasoning"]


@pytest.mark.parametrize("text,expected", [
    # The entry that was held during local testing.
    ("Acute hypertensive pulmonary edema after missing diuretics. My priority is oxygenation.",
     "Acute hypertensive pulmonary edema after missing diuretics"),
    ("Likely acute hypertensive pulmonary edema. My priority is oxygenation.",
     "acute hypertensive pulmonary edema"),
    # "this" is a dummy subject here, not a pronoun needing an antecedent.
    ("I think this is acute hypertensive pulmonary edema. My priority is oxygenation.",
     "acute hypertensive pulmonary edema"),
    ("I think it's septic shock. My priority is perfusion.", "septic shock"),
    ("My working model is that this is acute hypertensive pulmonary edema. My priority is oxygenation.",
     "acute hypertensive pulmonary edema"),
    ("Mi modelo de trabajo es edema pulmonar agudo hipertensivo. Mi prioridad es la oxigenación.",
     "edema pulmonar agudo hipertensivo"),
    ("Parece ICC descompensada. Mi prioridad es la oxigenación.", "ICC descompensada"),
    ("Creo que es un shock séptico. Mi prioridad es la perfusión.", "un shock séptico"),
    ("Sospecho que se trata de un TEP. Mi prioridad es la oxigenación.", "un TEP"),
    # Forms that already worked keep working.
    ("patient in shock. My priority is perfusion.", "in shock"),
    ("I think the patient has acute hypertensive pulmonary edema. My priority is oxygenation.",
     "the patient has acute hypertensive pulmonary edema"),
])
def test_a_clinically_written_working_model_is_recognised(extract, text, expected):
    assert extract(text).get("problem_representation") == expected


@pytest.mark.parametrize("text", [
    "Give furosemide 40 mg IV. Reassess in 10 minutes.",
    "Start BiPAP IPAP 12 EPAP 6 FiO2 60% for pulmonary edema.",
    # A priority or an expectation that names a condition is not a working model.
    "My priority is reducing congestion. Give furosemide 40 mg IV.",
    "Mi prioridad es la oxigenación. Dar furosemida 40 mg IV.",
    "I expect the congestion to improve. Reassess in 10 minutes.",
    # A generic complement still needs an explicit antecedent.
    "I think it is the primary problem.",
])
def test_nothing_is_attributed_that_the_resident_did_not_express(extract, text):
    assert not extract(text).get("problem_representation")


def test_mi_is_not_mistaken_for_an_acronym(extract):
    """"Mi" is Spanish for "my"; the acronym match is case-sensitive."""
    assert not extract("Mi prioridad es la perfusión.").get("problem_representation")


@pytest.fixture(scope="module")
def gate():
    source = (ROOT / "app.py").read_text()
    tree = ast.parse(source)
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) or (
        isinstance(n, ast.Assign) and any(getattr(t, "id", "").startswith(("_ES_", "REASONING_GATE"))
                                          for t in n.targets))]
    namespace = {"st": _Streamlit(), "re": re, "math": math, "random": random, "json": json,
                 "deepcopy": deepcopy, "escape": escape, "BytesIO": BytesIO, "__file__": "app.py"}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "app.py", "exec"), namespace)
    return namespace


SPANISH = ("Parece ICC descompensada. Mi prioridad es mejorar la oxigenación. "
           "Iniciar BiPAP IPAP 12 EPAP 6 FiO2 60%. Espero que la SpO2 suba sobre 92%. "
           "Reevaluar SpO2 y trabajo respiratorio en 10 minutos.")


def test_a_complete_spanish_order_passes_the_reasoning_gate(gate):
    """A Spanish-speaking resident met the gate in three of five slots."""
    from family_parser import parse_family_actions
    reasoning = gate["extract_explicit_reasoning"](SPANISH)
    assert reasoning["problem_representation"] == "ICC descompensada"
    assert reasoning["management_priority"] == "mejorar la oxigenación"
    assert reasoning["expected_effect"] == "la SpO2 suba sobre 92%"
    assert reasoning["reassessment_target"] == "SpO2 y trabajo respiratorio"
    parsed = parse_family_actions(SPANISH)
    parsed["reasoning"] = reasoning
    assert gate["reasoning_gate_missing"](parsed) == []


@pytest.mark.parametrize("text,slot,expected", [
    ("Mi prioridad es la diuresis. Dar furosemida 80 mg IV.", "management_priority", "diuresis"),
    ("Mi objetivo principal es la perfusión. Dar 500 mL de suero.", "management_priority", "perfusión"),
    ("Anticipo que mejore la presión arterial.", "expected_effect", "mejore la presión arterial"),
    # A negated expectation keeps its negation, as in English.
    ("No espero que baje la presión.", "expected_effect", "no espero que baje la presión"),
    ("Dar furosemida y reevaluar SpO2 y frecuencia respiratoria en 15 minutos.",
     "reassessment_target", "SpO2 y frecuencia respiratoria"),
    # Timing first, then the target.
    ("Reevaluar en 10 minutos la presión y el llenado capilar.",
     "reassessment_target", "presión y el llenado capilar"),
])
def test_spanish_slots_are_captured_in_the_residents_words(gate, text, slot, expected):
    assert gate["extract_explicit_reasoning"](text).get(slot) == expected


@pytest.mark.parametrize("text,slot", [
    # "Espero" is also "I wait".
    ("Espero 10 minutos antes de reevaluar.", "expected_effect"),
    ("Espero a ver la respuesta.", "expected_effect"),
    ("Dar furosemida 40 mg IV.", "management_priority"),
    ("Dar furosemida 40 mg IV.", "expected_effect"),
    # Timing alone, or the patient as a whole, is not a reassessment target.
    ("Reevaluar en 10 minutos.", "reassessment_target"),
    ("Reevaluar al paciente en 10 minutos.", "reassessment_target"),
])
def test_spanish_capture_invents_nothing(gate, text, slot):
    assert not gate["extract_explicit_reasoning"](text).get(slot)


def test_an_english_slot_is_never_overwritten_by_the_spanish_capture(gate):
    text = ("Acute pulmonary edema. My priority is oxygenation. Start BiPAP IPAP 12 EPAP 6 FiO2 60%. "
            "I expect SpO2 to rise. Reassess SpO2 in 10 minutes.")
    reasoning = gate["extract_explicit_reasoning"](text)
    assert reasoning["management_priority"] == "oxygenation"
    assert reasoning["expected_effect"] == "SpO2 to rise"
    assert reasoning["reassessment_target"] == "SpO2"
