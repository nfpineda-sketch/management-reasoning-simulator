"""Gaps found playing the GI bleed case (2026-09-19).

"Priority: restore oxygen-carrying capacity." was not read as a priority, so the
transfusion was held asking for one. A compound history question about stools,
vomited blood and medicines answered only the medicines.
"""
import pytest

from clinical_cases import FAMILIES
from patient_conversation import answer_from_sources
from test_curriculum_trajectories import load_engine


@pytest.fixture(scope="module")
def engine():
    return load_engine()


@pytest.mark.parametrize("text, priority", [
    ("Shock with hemoglobin 6.7. Priority: restore oxygen-carrying capacity. Transfuse 2 units of packed red cells.",
     "restore oxygen-carrying capacity"),
    ("Priority: perfusion, give 1000 mL normal saline.", "perfusion"),
    ("Shock con hemoglobina 6.7. Prioridad: restaurar la capacidad de transporte de oxígeno. Transfunde 2 unidades.",
     "restaurar la capacidad de transporte de oxígeno"),
])
def test_a_labelled_priority_is_a_priority(engine, text, priority):
    assert engine["extract_explicit_reasoning"](text)["management_priority"] == priority


def test_the_word_priority_inside_a_sentence_is_not_a_label(engine):
    reasoning = engine["extract_explicit_reasoning"]("Bleeding is a high priority: give blood.")
    assert "management_priority" not in reasoning


@pytest.mark.parametrize("question", [
    "What colour are your stools, and have you vomited blood? Which medicines do you take for your joints?",
    "¿De qué color son sus deposiciones y ha vomitado sangre? ¿Qué medicamentos toma para las articulaciones?",
])
def test_a_compound_question_answers_every_part(question):
    for variant in FAMILIES["gi_bleed"]["variants"]:
        history = variant["history"]
        facts = [fact for items in history.values() for fact in (items if isinstance(items, list) else [items])]
        answer = answer_from_sources(question, facts, history=history)
        for fact in history["bleeding"] + history["medications"]:
            assert fact in answer


def test_spanish_e_before_i_joins_orders():
    from family_parser import parse_family_actions
    text = ("Transfunde 2 unidades de glóbulos rojos en 60 minutos, administra pantoprazol 80 mg IV "
            "e interconsulta a gastroenterología para endoscopia urgente.")
    assert [a["type"] for a in parse_family_actions(text)["actions"]] == ["blood", "ppi", "consult"]
