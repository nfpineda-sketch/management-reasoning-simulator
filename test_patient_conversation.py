"""Regression checks for available, source-grounded patient conversation."""
from copy import deepcopy
from types import SimpleNamespace

import pytest

from patient_conversation import answer_from_sources, local_question_ids


@pytest.fixture
def facts():
    return [
        "He presents with dizziness, fatigue, and breathlessness on exertion.",
        "The symptoms began this morning; he cannot identify the exact onset.",
        "It has burned when I urinate for two days, and I have been going more often.",
        "I have had chills.",
        "I have not been eating or drinking much.",
        "I have no chest pain.",
        "I have no cough or focal neurological symptoms.",
        "He has hypertension and type 2 diabetes.",
        "I have not had vomiting or diarrhea.",
    ]


class Responses:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.response


def client_for(response=None, error=None):
    return SimpleNamespace(responses=Responses(response, error))


def assert_source_join(reply, sources):
    """Accept selected source sentences, preserving their exact wording/order."""
    remainder = reply
    selected = []
    while remainder:
        matches = [source for source in sources if remainder.startswith(source)]
        assert matches, f"Response contains prose outside the source facts: {remainder!r}"
        source = max(matches, key=len)
        selected.append(source)
        remainder = remainder[len(source):]
        if remainder:
            assert remainder.startswith(" ")
            remainder = remainder[1:]
    return selected


@pytest.mark.parametrize("question", [
    "How can I help you?",
    "What brought you in today?",
    "¿Cómo puedo ayudarle?",
    "¿Qué le pasa?",
])
def test_opening_question_works_without_provider_and_does_not_reveal_full_ros(facts, question):
    client = client_for(error=AssertionError("An opener must not need a provider"))
    before = deepcopy(facts)
    reply = answer_from_sources(question, facts, api_key="configured", client=client)
    selected = assert_source_join(reply, facts)
    assert facts[0] in selected
    assert len(selected) <= 2
    assert facts[2] not in selected
    assert facts[5] not in selected
    assert not client.responses.calls
    assert facts == before


@pytest.mark.parametrize(("question", "source_index"), [
    ("Does it burn when you urinate?", 2),
    ("¿Le arde al orinar?", 2),
    ("Do you have chest pain?", 5),
    ("¿Tiene dolor de pecho?", 5),
    ("Have you had chills?", 3),
    ("¿Ha tenido escalofríos?", 3),
    ("Have you been eating or drinking?", 4),
    ("Have you had vomiting or diarrhea?", 8),
])
def test_targeted_question_returns_the_requested_fact_immediately(facts, question, source_index):
    assert answer_from_sources(question, facts) == facts[source_index]


def test_known_topic_without_a_source_does_not_invent_a_negative():
    reply = answer_from_sources("Do you have chest pain?", ["I feel dizzy."])
    assert "not documented" in reply.lower()
    assert "no chest pain" not in reply.lower()


@pytest.mark.parametrize("question", ["Any other symptoms?", "¿Otros síntomas?"])
def test_broad_symptoms_give_a_brief_answer_without_a_full_review(facts, question):
    reply = answer_from_sources(question, facts)
    selected = assert_source_join(reply, facts)
    assert 1 <= len(selected) <= 2
    assert facts[2] in selected
    assert facts[5] not in selected
    assert facts[6] not in selected


def test_unknown_question_without_key_is_a_match_failure_not_a_clinical_denial(facts):
    question = "Could you elaborate on that episode?"
    assert local_question_ids(question, facts) is None
    reply = answer_from_sources(question, facts)
    assert "not documented" not in reply.lower()
    assert "unavailable" not in reply.lower()
    assert any(word in reply.lower() for word in ("question", "rephrase", "match"))
    assert facts[2] not in reply


def test_provider_paraphrase_preserves_sources_and_deduplicates_ids(facts):
    client = client_for(SimpleNamespace(status="completed", output_text='{"ids":[3,2,3]}'))
    reply = answer_from_sources("Could you elaborate on that episode?", facts, client=client)
    assert reply == " ".join((facts[3], facts[2]))
    assert len(client.responses.calls) == 1
    request = client.responses.calls[0]
    assert request["max_output_tokens"] >= 2048
    assert request["store"] is False
    assert request["text"]["format"]["strict"] is True


def test_successful_empty_provider_selection_means_not_documented(facts):
    client = client_for(SimpleNamespace(status="completed", output_text='{"ids":[]}'))
    reply = answer_from_sources("Could you elaborate on that episode?", facts, client=client)
    assert "not documented" in reply.lower()


@pytest.mark.parametrize("response", [
    SimpleNamespace(status="incomplete", output_text='{"ids":[]}',
                    incomplete_details=SimpleNamespace(reason="max_output_tokens")),
    SimpleNamespace(status="completed", output_text=""),
    SimpleNamespace(status="completed", output_text="not json"),
    SimpleNamespace(status="completed", output_text="[]"),
    SimpleNamespace(status="completed", output_text='{"ids":"0"}'),
    SimpleNamespace(status="completed", output_text='{"ids":[true]}'),
    SimpleNamespace(status="completed", output_text='{"ids":[999]}'),
    SimpleNamespace(status="completed", output_text='{"ids":[-1]}'),
    SimpleNamespace(status="completed", output_text='{"other":[]}'),
    SimpleNamespace(status="completed", output_text='{"ids":[],"invented":"No allergies"}'),
])
def test_invalid_provider_output_is_not_misrepresented_as_a_patient_fact(facts, response):
    client = client_for(response)
    reply = answer_from_sources("Could you elaborate on that episode?", facts, client=client)
    assert "not documented" not in reply.lower()
    assert "unavailable" not in reply.lower()
    assert any(word in reply.lower() for word in ("question", "rephrase", "match"))
    assert "No allergies" not in reply
    assert facts[2] not in reply


def test_provider_failure_does_not_log_question_sources_or_credentials(facts, caplog):
    sensitive = "sk-private-test-value"
    question = "Could you elaborate on that episode?"
    client = client_for(error=RuntimeError(sensitive + " " + question + " " + facts[2]))
    reply = answer_from_sources(question, facts, api_key=sensitive, client=client)
    assert "not documented" not in reply.lower()
    assert sensitive not in reply
    assert sensitive not in caplog.text
    assert question not in caplog.text
    assert facts[2] not in caplog.text


def test_client_initialization_failure_is_caught(monkeypatch, facts):
    import openai

    def broken_client(**kwargs):
        raise RuntimeError("Constructor failure")

    monkeypatch.setattr(openai, "OpenAI", broken_client)
    reply = answer_from_sources("Could you elaborate on that episode?", facts, api_key="configured")
    assert "not documented" not in reply.lower()
    assert "unavailable" not in reply.lower()
    assert any(word in reply.lower() for word in ("question", "rephrase", "match"))
