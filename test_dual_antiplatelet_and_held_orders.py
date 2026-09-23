"""Three defects found by playing the Wellens case (2026-09-22).

A resident wrote "start iv nytroglicerin 30 mg/min, clopidrogrel 180 mg po,
heparin 5000 IU iv". The reply quoted the misspelled nitroglycerin, said it
understood "heparin + admission", and the clopidogrel disappeared without ever
being named -- because the bank had no P2Y12 inhibitor at all, and because a
held submission names only its first unreadable order.

Faculty (2026-09-22): the P2Y12 inhibitor is the second antiplatelet, added to
aspirin. One of them is used, never two. Aspirin is the first agent and is
absent only when the patient cannot take it.
"""
import pytest

import language
from family_engine import execute_family_bundle
from family_parser import parse_family_actions
from test_cognitive_encounters import encounter
from test_curriculum_trajectories import load_engine


@pytest.fixture(scope="module")
def engine():
    return load_engine()


@pytest.fixture
def state(engine):
    return encounter(engine, "acs", "acs_48m_wellens")["state"]


def run(state, order):
    return execute_family_bundle(state, parse_family_actions(order))


@pytest.mark.parametrize("order, agent, dose", [
    ("clopidogrel 300 mg PO", "clopidogrel", 300),
    ("clopidrogrel 600 mg po", "clopidogrel", 600),     # as it was actually written
    ("Give ticagrelor 180 mg PO", "ticagrelor", 180),
    ("prasugrel 60 mg PO", "prasugrel", 60),
    ("dar clopidogrel 300 mg por via oral", "clopidogrel", 300),
    ("Administro ticagrelor 180 mg vo", "ticagrelor", 180),
])
def test_the_second_antiplatelet_is_an_order_the_bank_accepts(state, order, agent, dose):
    result = run(state, order)
    assert result["executed"], result["clarification"]
    summary = result["action_summaries"][0]
    assert (summary["type"], summary["agent"], summary["dose_mg"], summary["route"]) == ("p2y12", agent, dose, "PO")
    assert state["family_state"]["p2y12"] == agent


def test_aspirin_stays_the_first_antiplatelet_and_is_not_replaced(state):
    assert run(state, "Give aspirin 250 mg PO")["executed"]
    assert run(state, "clopidogrel 300 mg PO")["executed"]
    assert state["family_state"]["aspirin"] is True
    assert state["family_state"]["p2y12"] == "clopidogrel"


def test_only_one_p2y12_inhibitor_is_used(state):
    assert run(state, "ticagrelor 180 mg PO")["executed"]
    refused = run(state, "clopidogrel 300 mg PO")
    assert not refused["executed"]
    message = refused["clarification"]
    assert "ticagrelor" in message.lower() and "clopidogrel" in message.lower()
    assert "aspirin plus one P2Y12" in message
    # Refusing does not quietly undo what is already on board.
    assert state["family_state"]["p2y12"] == "ticagrelor"
    assert language.say(message, "es").startswith("Ticagrelor ya está administrado")


def test_a_repeat_of_the_same_inhibitor_is_not_read_as_a_second_one(state):
    assert run(state, "clopidogrel 300 mg PO")["executed"]
    assert run(state, "clopidogrel 300 mg PO")["executed"]


def test_the_question_names_the_drug_the_resident_wrote(state):
    refused = run(state, "clopidogrel 300 mg IV")
    assert not refused["executed"]
    assert refused["clarification"] == "Please specify a supported route for clopidogrel."
    assert "p2y12" not in refused["clarification"].lower()


def test_every_unreadable_order_is_named_at_once(state):
    refused = run(state, "Start iv nytroglicerin 30 mg/min, dar vitamina X 10 mg, heparin 5000 IU iv")
    assert not refused["executed"]
    message = refused["clarification"]
    assert "These orders were not recognized" in message
    assert "nytroglicerin" in message and "vitamina x" in message.lower()
    assert language.say(message, "es").startswith("Estas órdenes no se reconocieron")


def test_one_unreadable_order_still_reads_as_one(state):
    refused = run(state, "dar vitamina X 10 mg")
    assert not refused["executed"]
    assert refused["clarification"].startswith("This order was not recognized:")
    assert "These orders" not in refused["clarification"]


def test_an_infusion_rate_says_how_far_outside_the_range_it_is(state):
    refused = run(state, "Start iv nitroglycerin 30 mg/min")
    assert not refused["executed"]
    message = refused["clarification"]
    # 30 mg/min is read as 30,000 mcg/min: the magnitude is the lesson.
    assert "30000 mcg/min" in message and "75 times the supported maximum" in message
    assert "between 0.1 and 400 mcg/min" in message
    assert "es 75 veces el máximo soportado" in language.say(message, "es")


def test_a_rate_inside_the_range_is_simply_given(state):
    result = run(state, "Start iv nitroglycerin 30 mcg/min")
    assert result["executed"], result["clarification"]
