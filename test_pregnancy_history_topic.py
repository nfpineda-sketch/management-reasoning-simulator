"""DF-23 row 8 (faculty, 2026-09-29, A with modification): pregnancy is a topic of its own.

Questions about pregnancy, the last menstrual period (LMP, FUM, "última regla") or
menstruation never fall into symptom onset. A case that authored nothing on it answers
"Not documented." ("No documentado."): no last period, pregnancy status, contraceptive
adherence or test result is invented, and no provider is asked. pulmonary_embolism_33f
authors none (§4): until the faculty decides what it contains, it answers that way, and a
pregnancy test ordered stays ordered with no result modelled (TD-22, unchanged).
"""
import pytest

import history_review
import language
import patient_conversation as conversation
from clinical_scene import answer_history, history_facts
from family_engine import execute_family_bundle
from family_parser import parse_family_actions
from test_cognitive_encounters import encounter
from test_curriculum_trajectories import load_engine

QUESTIONS = ["When was your last menstrual period?", "Are you pregnant?", "LMP?", "When did your last period start?",
             "Is there any chance you could be pregnant?", "Are your periods regular?",
             "¿Cuándo fue su última regla?", "¿FUM?", "¿Está embarazada?", "¿Menstruación normal?"]
ONSET = "The breathing and chest discomfort started abruptly about two hours ago."


@pytest.fixture(scope="module")
def pe_33f():
    return encounter(load_engine(), "pulmonary_embolism", "pulmonary_embolism_33f")["state"]


class _NoProvider:
    """A client that fails if anything asks it."""

    @property
    def responses(self):
        raise AssertionError("a pregnancy question must never reach a provider")


@pytest.mark.parametrize("question", QUESTIONS)
def test_an_undocumented_pregnancy_question_answers_not_documented_and_never_onset(pe_33f, question):
    facts = history_facts("", pe_33f.get("case_id"), state=pe_33f)
    answer = answer_history(question, facts, api_key="sk-a-configured-key", client=_NoProvider(), state=pe_33f)
    assert answer == "Not documented." and ONSET not in answer
    assert language.case_words(answer, "es") == "No documentado."


def test_an_authored_pregnancy_topic_is_said_as_written():
    history = {"pregnancy": ["My last period was two weeks ago and I am not pregnant."],
               "onset": ["It started an hour ago."]}
    facts = ["It started an hour ago.", "My last period was two weeks ago and I am not pregnant."]
    assert conversation.answer_from_sources("When was your last period?", facts, history=history) == \
        "My last period was two weeks ago and I am not pregnant."


def test_onset_questions_still_reach_onset(pe_33f):
    facts = history_facts("", pe_33f.get("case_id"), state=pe_33f)
    assert ONSET in answer_history("When did this start?", facts, state=pe_33f)
    assert not conversation.asks_about_pregnancy("Over what period of time did it develop?")


def test_the_history_review_never_counts_a_period_question_as_onset():
    asked = [{"asked": "When did your last period start?"}]
    assert "onset" not in history_review.topics_named(asked)
    assert "onset" in history_review.topics_named(asked + [{"asked": "When did the pain start?"}])


@pytest.mark.parametrize("order", ["Order a urine pregnancy test.", "Solicitar test de embarazo."])
def test_a_pregnancy_test_is_ordered_with_no_result_modelled(order):
    state = encounter(load_engine(), "pulmonary_embolism", "pulmonary_embolism_33f")["state"]
    result = execute_family_bundle(state, parse_family_actions(order))
    assert result["executed"]
    [label] = [s["label"] for s in result["action_summaries"] if "Pregnancy test" in str(s.get("label"))]
    assert "not modelled" in label and "no result will be produced and none is invented" in label
