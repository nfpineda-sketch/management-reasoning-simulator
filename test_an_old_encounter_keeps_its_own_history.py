"""An old encounter is read with the case it was played on, not today's bank (L-F01).

Found by the cycle 5 night audit and approved for cycle 6 (2026-09-28): the
history topics a case offered were read from the live bank. A topic added to a
case later showed an old encounter as "never asked"; a topic removed hid what
had been asked; and the critical-event screening that turns on a question
(``bradycardia_cause_unexamined`` asks whether the medications were asked
about) moved from "contradicted" to "reading" with it. Nothing the resident did
had changed.

The topics now come from the case frozen with the encounter. An encounter that
carries no case is legacy: what its case offered then cannot be known, and the
bank as it stands today is not read in its place.

The acceptance test the faculty set: version A, change the bank to B, reopen,
and the meaning stays A.
"""
import json
from copy import deepcopy

import pytest

import clinical_cases
import history_review
import rubric_screening
from management_trace_analysis import source_fingerprint
from management_trace_store import analysis_payload_from_session


def asked(question, answer="An answer.", minute=0):
    return [{"kind": "you", "time": minute, "text": question},
            {"kind": "patient_history", "time": minute, "text": answer}]


def launched(case_id, events):
    """A record the way the store keeps one: the case frozen at launch, twice."""
    case = {"id": case_id, "history": deepcopy(clinical_cases.variant_by_id(case_id)["history"])}
    spec = {"clinical_case": case, "case_family": "authored"}
    return {"encounter": {"spec": deepcopy(spec)},
            "payload": {"session": {"state": {"encounter_spec": deepcopy(spec)}, "events": list(events),
                                    "management_trace": []}}}


@pytest.fixture
def bank_b(monkeypatch):
    """Change the bank after the encounter: one topic removed, one added."""
    real = clinical_cases.variant_by_id

    def changed(case_id, *args, **kwargs):
        variant = deepcopy(real(case_id, *args, **kwargs))
        history = variant.setdefault("history", {})
        for topic in ("allergies", "medications"):
            history.pop(topic, None)
        history["vaccination"] = ["Added to the case after the encounter."]
        return variant

    monkeypatch.setattr(clinical_cases, "variant_by_id", changed)
    return real


def test_version_a_stays_a_after_the_bank_changes_to_b(monkeypatch):
    case_id = "hypoglycemia_76f"
    record = launched(case_id, asked("¿Qué medicamentos toma?", "Tomo glimepirida."))
    before = history_review.review(record, case_id)
    events_before = history_review.unasked_for_events(record, case_id)
    real = clinical_cases.variant_by_id

    def changed(identifier, *args, **kwargs):
        variant = deepcopy(real(identifier, *args, **kwargs))
        variant["history"].pop("allergies", None)
        variant["history"]["vaccination"] = ["Added later."]
        return variant

    monkeypatch.setattr(clinical_cases, "variant_by_id", changed)
    # The bank did change ...
    assert "allergies" not in clinical_cases.variant_by_id(case_id)["history"]
    # ... and the encounter still reads as it was played.
    after = history_review.review(record, case_id)
    assert after == before
    assert after["topics_source"] == "frozen"
    assert "Allergies" in [row["label"] for row in after["not_named"]]
    assert "vaccination" not in [row["topic"] for row in after["offered"]]
    assert history_review.unasked_for_events(record, case_id) == events_before


def test_the_critical_event_screening_keeps_the_question_that_was_asked(bank_b):
    """bradycardia_cause_unexamined turns on whether the medications were asked about."""
    case_id = "bradycardia_bb_54f"
    # The record was launched on the bank as it was (before the change the
    # fixture made): build it from the real variant.
    case = {"id": case_id, "history": deepcopy(bank_b(case_id)["history"])}
    assert "medications" in case["history"]
    spec = {"clinical_case": case, "case_family": "authored"}
    record = {"encounter": {"spec": spec},
              "payload": {"session": {"state": {"encounter_spec": deepcopy(spec)},
                                      "events": asked("¿Qué medicamentos toma?", "Un betabloqueador."),
                                      "management_trace": []}}}
    assert "medications" not in clinical_cases.variant_by_id(case_id)["history"]
    assert "medications" in rubric_screening.facts(record, case_id)["asked_topics"]


def test_a_legacy_encounter_without_its_case_is_unavailable_not_today_s_bank():
    record = {"payload": {"session": {"encounter": {"authored_case_id": "hypoglycemia_76f"},
                                      "events": asked("¿Tiene alergias?")}}}
    summary = history_review.review(record, "hypoglycemia_76f")
    assert summary["topics_source"] == "unavailable"
    assert summary["offered"] == [] and summary["not_named"] == []
    # What the resident asked is still read, and still reaches its topic.
    assert "allergies" in summary["named"]


def test_a_generated_case_declared_no_topics():
    spec = {"clinical_case": {"id": "AI-123", "history": {"medications": ["x"]}}, "case_family": "generated"}
    record = {"encounter": {"spec": spec}, "payload": {"session": {"events": []}}}
    summary = history_review.review(record, "AI-123")
    assert summary["topics_source"] == "generated" and summary["offered"] == []


def test_the_frozen_session_is_read_when_the_store_column_is_absent():
    record = launched("hypoglycemia_76f", [])
    del record["encounter"]
    assert history_review.frozen_topics(record)[1] == "frozen"


def test_the_analysis_payload_carries_topic_names_never_the_case(bank_b):
    case_id = "hypoglycemia_76f"
    history = deepcopy(bank_b(case_id)["history"])
    session = {"encounter_ended": True, "expert_comparison_unlocked": True,
               "encounter_closed_trace": [], "precomparison_decision_review": {}, "review_prompts": [],
               "encounter_closed_events": [],
               "encounter_closed_state": {"encounter_spec": {"clinical_case": {"id": case_id, "history": history}}}}
    payload = analysis_payload_from_session(session)
    assert payload["history_topics"] == list(history) and payload["history_topics_source"] == "frozen"
    # The names of the topics, not what the patient would have said.
    words = json.dumps(payload, ensure_ascii=False)
    for answers in history.values():
        for answer in answers:
            assert answer not in words
    # Read back from the payload, the topics are the frozen ones, not the changed bank's.
    summary = history_review.review({"payload": payload}, case_id)
    assert summary["topics_source"] == "frozen"
    assert "medications" in [row["topic"] for row in summary["offered"]]


def test_carrying_the_topic_names_changes_no_saved_analysis_fingerprint():
    from test_management_trace_report import report_example
    _, fixture = report_example()
    session = {"encounter_ended": True, "expert_comparison_unlocked": True,
               "encounter_closed_trace": fixture["trace"], "precomparison_decision_review": fixture["reflections"],
               "review_prompts": fixture["reflection_prompts"], "encounter_closed_events": [],
               "encounter_closed_state": {"encounter_spec": {"clinical_case": {
                   "id": "hypoglycemia_76f", "history": {"medications": ["-"]}}}}}
    payload = analysis_payload_from_session(session)
    without = {key: value for key, value in payload.items()
               if key not in {"history_topics", "history_topics_source"}}
    assert payload["history_topics"] == ["medications"]
    assert source_fingerprint(payload) == source_fingerprint(without)
