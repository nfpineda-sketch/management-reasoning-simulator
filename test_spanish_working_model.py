"""A Spanish causal statement is the resident's working model.

Found preparing an asthma series (2026-09-19): the Spanish capture filled
priority, expected effect and reassessment target but never the working model, so
every management order written in Spanish was held asking for one. English
phrasing is untouched.
"""
import pytest

from test_curriculum_trajectories import load_engine

ORDER = (" Prioridad: revertir la obstrucción. Administra salbutamol 5 mg nebulizado. "
         "Espero menos sibilancias. Reevalúa en 20 minutos SpO2 y frecuencia respiratoria.")


@pytest.fixture(scope="module")
def engine():
    return load_engine()


@pytest.mark.parametrize("model", [
    "Esto es una crisis asmática grave porque quedó sin su inhalador de mantenimiento",
    "La obstrucción persiste porque la inflamación no cede aún",
    "Se está agotando debido a la obstrucción prolongada",
    "Las sibilancias difusas sugieren broncoespasmo",
    "La hipotensión con llene capilar lento significa que la perfusión está comprometida",
])
def test_the_causal_sentence_fills_the_working_model(engine, model):
    reasoning = engine["extract_explicit_reasoning"](model + "." + ORDER)
    assert reasoning.get("problem_representation") == model
    parsed = {"actions": [{"type": "bronchodilator"}, {"type": "reassessment", "delay_min": 20}],
              "reasoning": reasoning}
    assert engine["reasoning_gate_missing"](parsed) == []


def test_an_order_or_a_priority_is_not_a_working_model(engine):
    reasoning = engine["extract_explicit_reasoning"](
        "Prioridad: revertir la obstrucción, así que administra salbutamol 5 mg nebulizado. "
        "Espero menos sibilancias. Reevalúa en 20 minutos SpO2.")
    assert not reasoning.get("problem_representation")
    assert reasoning["management_priority"] == "revertir la obstrucción"
