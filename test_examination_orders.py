"""Examining the patient, written as an order (faculty decision 2026-09-21).

Found playing the thiamine-depleted hypoglycaemia: "Pídele glicemia capilar y
examina el estado neurológico" answered "The requested study was not
recognized" and held the turn, and the five turns that repeated it were refused
one after another while the clock stayed at minute 10 and the patient stayed
confused. The examination lived only in its own control.
"""
import pytest

from family_engine import available_regions, examination_finding, execute_family_bundle
from family_parser import parse_family_actions
from test_cognitive_encounters import encounter
from test_curriculum_trajectories import load_engine


@pytest.fixture(scope="module")
def engine():
    return load_engine()


def actions(text):
    return parse_family_actions(text)["actions"]


@pytest.mark.parametrize("text, region", [
    ("Examina el estado neurológico.", "Neurological"),
    ("Ausculta el tórax.", "Respiratory"),
    ("Examina el abdomen.", "Abdomen"),
    ("Revisa la perfusión periférica.", "Peripheral perfusion"),
    ("Explora el corazón.", "Cardiac"),
    ("Examine the abdomen.", "Abdomen"),
    ("Auscultate the chest.", "Respiratory"),
    ("Examine the general appearance.", "General appearance"),
])
def test_an_examination_is_an_order(text, region):
    parsed = actions(text)
    assert [a["type"] for a in parsed] == ["examination"], parsed
    assert parsed[0]["region"] == region


def test_an_examination_without_a_region_names_the_choices():
    parsed = actions("Examina al paciente.")
    assert parsed[0]["type"] == "clarification"
    assert "neurological" in parsed[0]["message"]


def test_it_travels_with_the_rest_of_the_turn(engine):
    state = encounter(engine, "hypoglycemia", "hypoglycemia_54m_thiamine")["state"]
    result = execute_family_bundle(state, parse_family_actions(
        "Pídele glicemia capilar y examina el estado neurológico. Reevalúa en 10 minutos."))
    assert result["executed"], result.get("clarification")
    kinds = [s.get("diagnostic_type") or s.get("type") for s in result["action_summaries"]]
    assert "examination" in kinds and "poc_glucose" in kinds
    assert state["sim_time"] == 10


def test_the_finding_is_the_one_the_control_would_show(engine):
    state = encounter(engine, "hypoglycemia", "hypoglycemia_54m_thiamine")["state"]
    result = execute_family_bundle(state, parse_family_actions("Examina el abdomen. Reevalúa en 5 minutos."))
    finding = next(s["label"] for s in result["action_summaries"] if s.get("type") == "examination")
    assert finding == examination_finding(state, "Abdomen")


def test_a_region_that_does_not_exist_is_answered_with_the_ones_that_do(engine):
    state = encounter(engine, "hypoglycemia", "hypoglycemia_54m_thiamine")["state"]
    result = execute_family_bundle(state, parse_family_actions("Examina la nariz. Reevalúa en 5 minutos."))
    assert result["executed"] or "examination to perform" in result["clarification"]


def test_every_region_of_the_menu_can_be_examined(engine):
    state = encounter(engine, "asthma", "asthma_49m")["state"]
    for region in available_regions(state):
        assert examination_finding(state, region)
