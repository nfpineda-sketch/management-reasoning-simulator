"""An order in the same sentence as the resident's priority is still an order.

"My priority is perfusion, give 1000 mL normal saline" used to lose the fluid in
both languages: a sentence that opened with reasoning was skipped whole. In
English the captured priority also swallowed the order ("perfusion, give 1000
mL normal saline").

The boundary matters as much: a goal stays reasoning. "and reducing preload",
"y bajar precarga" and "and increase the MAP above 65" are not orders.
"""
import pytest

from family_parser import parse_family_actions
from test_curriculum_trajectories import load_engine


@pytest.fixture(scope="module")
def engine():
    return load_engine()


def summary(text):
    return [(a["type"], a.get("volume_ml") or a.get("diagnostic") or a.get("delay_min")
             or a.get("rate_mcg_kg_min") or a.get("operation"))
            for a in parse_family_actions(text)["actions"]]


@pytest.mark.parametrize("text, priority", [
    ("My priority is perfusion, give 1000 mL normal saline.", "perfusion"),
    ("My priority is perfusion and give 1000 mL normal saline.", "perfusion"),
    ("Mi prioridad es la perfusión y dar 1000 mL de suero fisiológico.", "perfusión"),
    ("Mi prioridad es la perfusión, administra 1000 mL de suero fisiológico.", "perfusión"),
])
def test_the_order_is_executed_and_the_priority_stays_a_priority(engine, text, priority):
    assert summary(text) == [("fluid", 1000.0)]
    assert engine["extract_explicit_reasoning"](text)["management_priority"] == priority


@pytest.mark.parametrize("text", [
    "My priority is oxygenation and reducing preload and afterload.",
    "My priority is perfusion and increase the MAP above 65.",
    "Mi prioridad es la oxigenación y bajar precarga y poscarga.",
    "Mi prioridad es la perfusión y aumentar la presión arterial.",
    "My priority is to start BiPAP.",
])
def test_a_goal_is_never_turned_into_an_order(text):
    assert summary(text) == []


def test_a_goal_verb_with_a_treatment_is_an_order(engine):
    text = "My priority is oxygenation, increase FiO2 to 80%."
    assert [kind for kind, _ in summary(text)] == ["respiratory_adjustment"]
    assert engine["extract_explicit_reasoning"](text)["management_priority"] == "oxygenation"


def test_an_expectation_followed_by_a_reassessment_schedules_it():
    assert summary("I expect lactate to fall, reassess in 30 minutes.") == [("reassessment", 30.0)]


def test_an_order_after_a_rationale_is_kept():
    text = "Give 1000 mL NS because she is hypotensive, and start oxygen 4 L nasal cannula."
    assert [kind for kind, _ in summary(text)] == ["fluid", "oxygen"]


def test_a_conditional_or_negated_order_after_a_priority_is_not_executed():
    assert summary("My priority is perfusion, do not give fluids.") == []
    parsed = parse_family_actions("My priority is perfusion, give 500 mL NS if MAP stays below 65.")
    assert parsed["actions"] == []
    assert parsed["recognized_future_actions"] == ["give 500 ml ns if map stays below 65"]


def test_the_reported_mixed_order_is_unchanged():
    text = ("patient in shock. Give 1000 NS, start oxygen 4l/m nasal cannula. "
            "POCUS, VBG, lactate need to improve oxygenation and perfusion. "
            "Reassess in 10 min, hr,bp, O2")
    assert [kind for kind, _ in summary(text)] == [
        "fluid", "oxygen", "diagnostic", "diagnostic", "diagnostic", "reassessment"]


def test_an_untimed_reassessment_inside_a_priority_is_an_intention(engine):
    text = "My priority is to restore glucose availability and reassess the patient."
    assert summary(text) == []
    assert engine["extract_explicit_reasoning"](text)["management_priority"] == \
        "restore glucose availability and reassess the patient"


def test_a_study_verb_without_a_study_stays_reasoning(engine):
    # Reported: ", check for early fluid overload" became an unrecognized study
    # and held the whole turn, and the priority was cut to "stop routine fluid".
    text = ("My priority is to stop routine fluid, check for early fluid overload "
            "and secure the right level of care.")
    assert parse_family_actions(text)["actions"] == []
    assert engine["extract_explicit_reasoning"](text)["management_priority"] == (
        "stop routine fluid, check for early fluid overload and secure the right level of care")


@pytest.mark.parametrize("text, priority", [
    ("My priority is perfusion, check lactate and VBG.", "perfusion"),
    ("Mi prioridad es la perfusión, pide lactato.", "perfusión"),
])
def test_a_study_named_after_the_priority_is_ordered(engine, text, priority):
    assert [kind for kind, _ in summary(text)] == ["diagnostic"] * len(parse_family_actions(text)["actions"])
    assert summary(text)
    assert engine["extract_explicit_reasoning"](text)["management_priority"] == priority


def test_interconsulta_is_a_consult_order():
    assert parse_family_actions("Interconsulta a UCI.")["actions"] == [{"type": "consult", "service": "ICU"}]
