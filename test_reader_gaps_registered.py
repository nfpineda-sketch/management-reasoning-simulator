"""TD-45 (2026-09-29): the frozen reader's gaps, pinned as they are today.

The reader is frozen after V3 (§112, §120): what it misses is registered, not
fixed, until an approved cycle. Each example here is reproducible and asserts
what the reader and the room answer now, so that no interpretation changes in
silence: when one starts to work, its test fails and TD-45 is updated with it.
"""
import pytest

from family_engine import execute_family_bundle
from family_parser import parse_family_actions
from test_cognitive_encounters import encounter
from test_curriculum_trajectories import load_engine


@pytest.fixture(scope="module")
def engine():
    return load_engine()


def kinds(text):
    return [action["type"] for action in parse_family_actions(text)["actions"]]


def room(engine, text, before=()):
    state = encounter(engine, "hypoglycemia", "hypoglycemia_54m_thiamine")["state"]
    for order in before:
        assert execute_family_bundle(state, parse_family_actions(order))["executed"]
    return execute_family_bundle(state, parse_family_actions(text))


def test_a_verb_less_drug_in_a_list_is_lost_while_the_rest_runs():
    """TD-45a (KD-02): the aspirin is not read and nothing says so."""
    assert kinds("- Aspirin\n- Ticagrelor 180 mg PO\n- ECG now") == ["p2y12", "diagnostic"]
    assert kinds("Aspirin, heparin 5000 units IV, ECG") == ["anticoagulation", "diagnostic"]


def test_a_fluid_named_without_a_verb_is_held():
    """TD-45b (KD-15): held with a notice; with a verb it runs."""
    [held] = parse_family_actions("IV fluids 1 L")["actions"]
    assert held["type"] == "clarification" and 'This order was not recognized: "IV fluids 1 L"' in held["message"]
    assert kinds("Give IV fluids 1 L now") == ["fluid"]


@pytest.mark.parametrize("text, answer", [
    ("Check the IV.", "The requested study was not recognized."),
    ("Flush the IV.", "Please specify a question, investigation, treatment, or reassessment."),
    ("Replace the IV.", "Please specify a question, investigation, treatment, or reassessment."),
    ("Get another IV.", "Specify which recorded drug or fluid to repeat."),
    ("IO, then D50.", "Please specify a question, investigation, treatment, or reassessment."),
])
def test_line_orders_the_reader_does_not_read_are_held_with_these_answers(engine, text, answer):
    """TD-45c-f: nothing runs; the answer is generic or names the wrong thing."""
    result = room(engine, text)
    assert not result["executed"] and result["clarification"].startswith(answer)


@pytest.mark.parametrize("text", ["Stop the dextrose infusion.", "Suspender la infusión de glucosado."])
def test_stopping_the_dextrose_infusion_by_that_name_says_none_is_running(engine, text):
    """TD-45g: the D10 infusion is running, and the answer says it is not; 'Stop the D10.' stops it."""
    result = room(engine, text, before=("Start D10 infusion at 100 mL/h.",))
    assert not result["executed"] and result["clarification"].startswith("No infusion is running.")
    assert room(engine, "Stop the D10.", before=("Start D10 infusion at 100 mL/h.",))["executed"]


def test_a_time_written_after_the_source_of_a_prior_treatment_stays_in_its_text():
    """TD-45h: 'given at OSH at 10:40' keeps no separate time; the text still has it."""
    [detail] = parse_family_actions("Epinephrine 0.5 mg IM given at OSH at 10:40.")["future_details"]
    assert detail["kind"] == "prior_treatment" and detail.get("reported_time") is None
    assert "10:40" in detail["text"]
