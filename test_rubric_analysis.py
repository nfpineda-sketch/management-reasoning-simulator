"""What the model may propose, and what it may never do.

The proposal is a proposal: a faculty member confirms or changes every value,
and the totals are computed by ``rubric`` from saved numbers. These checks are
aimed at the ways that contract could quietly break -- an invented critical
event, a "not assessable" with no reason, a score with no evidence, a total
arriving from the model, or a provider failure leaving a zero behind.
"""
from copy import deepcopy
from types import SimpleNamespace
import json

import pytest

import rubric
from rubric_analysis import (LEGACY_PROMPT_VERSION, PROMPT_VERSION, SCHEMA_VERSION,
                             RubricAnalysisError, build_rubric_source, case_id_of,
                             event_verdicts, generate_rubric_proposal, proposed_event_rows,
                             validate_rubric_proposal)
from faculty_analysis import source_fingerprint
from test_faculty_analysis import sample_record

CASE = "acs_48m_wellens"


def record_on_case(case_id=CASE):
    record = sample_record()
    record["payload"]["session"]["encounter"] = {"authored_case_id": case_id}
    return record


def sample_proposal(refs=("trace:0",), events=()):
    return {
        "domains": [{
            "domain_id": domain,
            "score": 2,
            "evidence_refs": list(refs),
            "learner_evidence": [{"evidence_ref": refs[0], "minute": 0,
                                  "quote": "Give 250 mL IV crystalloid and reassess perfusion in 5 minutes."}],
            "rationale": "A limited trial with a stated expectation and interval was recorded.",
            "contrary_evidence": "Only one decision is recorded.",
            "limits": "The trace is short; the window observed is five minutes.",
        } for domain in rubric.DOMAIN_IDS],
        "critical_events": [{"event_id": e, "evidence_refs": list(refs),
                             "trigger_evidence": "Nothing was executed in the window.",
                             "exclusions_checked": "The encounter did not close early."} for e in events],
        "concerns_for_review": [],
        "assistance_recorded": [],
        "record_limits": ["One decision is recorded."],
    }


def sample_proposal_v11(record, occurred=(), refs=("trace:0",), opportunity="observed"):
    """The 1.1 shape: every domain states its opportunity, every defined event a verdict."""
    body = sample_proposal(refs)
    body.pop("critical_events")
    for row in body["domains"]:
        row["opportunity"] = opportunity
        row["next_level_gap"] = "Targets and alarm thresholds were not set."
    defined = [e["event_id"] for e in build_rubric_source(record)["defined_critical_events"]]
    if defined:
        body["event_verdicts"] = {event_id: {
            "verdict": "occurred" if event_id in occurred else "did_not_occur",
            "evidence_refs": list(refs),
            "trigger_evidence": "Nothing of this kind was executed in the window."
                                if event_id in occurred else "The trigger is not met by the record.",
            "exclusions_checked": "No exclusion applies." if event_id in occurred
                                  else "Not proposed: the trigger is not met.",
        } for event_id in defined}
    return body


def envelope(record, proposal, version=LEGACY_PROMPT_VERSION):
    """1.0 by default: those proposals are saved in the database and must keep validating."""
    return {
        "schema_version": SCHEMA_VERSION, "prompt_version": version,
        "rubric_version": rubric.VERSION, "coverage_version": "1.0",
        "source_hash": source_fingerprint(record), "attempt_id": record["id"],
        "attempt_revision": record["revision"],
        "generated_at": "2026-09-23T00:00:00+00:00", "model": "test-model",
        "assistance_context": "unknown", "case_id": case_id_of(record),
        "proposal": proposal,
    }


def test_the_source_carries_the_rubric_and_what_the_case_declared():
    source = build_rubric_source(record_on_case())
    assert source["rubric_version"] == rubric.VERSION
    assert [row["domain_id"] for row in source["rubric"]] == list(rubric.DOMAIN_IDS)
    assert all(set(row["levels"]) == {"0", "1", "2", "3"} for row in source["rubric"])
    assert {row["domain_id"] for row in source["case_opportunities"]} == set(rubric.DOMAIN_IDS)
    assert {e["event_id"] for e in source["defined_critical_events"]} == {
        "acs_no_antiplatelet", "acs_provocation_test"}
    assert source["engine_limitations"] and source["case_closure"]
    # Every event travels with its alternatives and its exclusions, so a valid
    # different choice and an engine failure cannot become a penalty.
    for event in source["defined_critical_events"]:
        assert event["acceptable_alternatives"] and event["exclusions"]


def test_a_previous_ai_interpretation_is_never_the_evidence():
    source = build_rubric_source(record_on_case())
    body = json.dumps(source)
    assert "objective_rubric" not in source
    assert "faculty_brief" not in body and "trace_analysis" not in body


def test_the_account_is_never_sent():
    body = json.dumps(build_rubric_source(record_on_case()))
    assert "DO_NOT_SEND_ACCOUNT_NAME" not in body and "DO_NOT_SEND_ACCOUNT_ID" not in body


def test_a_well_formed_proposal_validates():
    record = record_on_case()
    saved = validate_rubric_proposal(envelope(record, sample_proposal()), record)
    assert len(saved["proposal"]["domains"]) == 5


def test_an_event_the_case_never_defined_is_refused():
    """A model may propose a defined event. It may not invent one."""
    record = record_on_case()
    with pytest.raises(RubricAnalysisError):
        validate_rubric_proposal(
            envelope(record, sample_proposal(events=("pe_no_anticoagulation",))), record)


def test_a_defined_event_is_accepted_and_counted_once():
    record = record_on_case()
    saved = validate_rubric_proposal(
        envelope(record, sample_proposal(events=("acs_no_antiplatelet",))), record)
    assert [e["event_id"] for e in saved["proposal"]["critical_events"]] == ["acs_no_antiplatelet"]


def test_the_same_event_cannot_be_proposed_twice():
    record = record_on_case()
    proposal = sample_proposal(events=("acs_no_antiplatelet", "acs_no_antiplatelet"))
    with pytest.raises(RubricAnalysisError):
        validate_rubric_proposal(envelope(record, proposal), record)


def test_not_assessable_must_say_why():
    record = record_on_case()
    proposal = sample_proposal()
    proposal["domains"][3].update(score=rubric.NOT_ASSESSABLE, rationale="   ", evidence_refs=[])
    with pytest.raises(RubricAnalysisError):
        validate_rubric_proposal(envelope(record, proposal), record)


def test_a_scored_domain_must_cite_its_evidence():
    record = record_on_case()
    proposal = sample_proposal()
    proposal["domains"][0]["evidence_refs"] = []
    with pytest.raises(RubricAnalysisError):
        validate_rubric_proposal(envelope(record, proposal), record)


def test_a_domain_cannot_be_missing_or_repeated():
    record = record_on_case()
    proposal = sample_proposal()
    proposal["domains"][1]["domain_id"] = "D1"
    with pytest.raises(RubricAnalysisError):
        validate_rubric_proposal(envelope(record, proposal), record)


def test_the_model_has_nowhere_to_put_a_total():
    """The arithmetic is code's. The schema admits no sum, penalty or total."""
    record = record_on_case()
    proposal = sample_proposal()
    for forbidden in ("total", "base", "adjusted", "penalty", "score_total"):
        assert forbidden not in proposal
        broken = {**proposal, forbidden: 12}
        with pytest.raises(RubricAnalysisError):
            validate_rubric_proposal(envelope(record, broken), record)


def test_a_proposal_does_not_match_another_encounter_or_revision():
    record = record_on_case()
    good = envelope(record, sample_proposal())
    for field, value in (("attempt_id", "other"), ("attempt_revision", 99),
                         ("source_hash", "0" * 64), ("case_id", "pneumonia_46f"),
                         ("prompt_version", "9.9"), ("schema_version", "other_v1")):
        with pytest.raises(RubricAnalysisError):
            validate_rubric_proposal({**good, field: value}, record)


def test_a_provider_failure_records_nothing():
    record = record_on_case()

    class Failing:
        class responses:
            @staticmethod
            def create(**kwargs):
                raise RuntimeError("sk-live-should-never-be-shown")

    with pytest.raises(RubricAnalysisError) as raised:
        generate_rubric_proposal(record, api_key="k", model="m", client=Failing())
    assert "sk-live" not in str(raised.value)
    assert "Nothing was recorded" in str(raised.value)


def test_an_incomplete_response_is_not_a_score():
    record = record_on_case()

    class Truncated:
        class responses:
            @staticmethod
            def create(**kwargs):
                return SimpleNamespace(status="incomplete", output_text="{}")

    with pytest.raises(RubricAnalysisError):
        generate_rubric_proposal(record, api_key="k", model="m", client=Truncated())


def test_one_request_is_made_and_it_carries_the_defined_events():
    record = record_on_case()
    seen = {}

    class Once:
        class responses:
            @staticmethod
            def create(**kwargs):
                seen.update(kwargs)
                seen["calls"] = seen.get("calls", 0) + 1
                return SimpleNamespace(status="completed",
                                       output_text=json.dumps(sample_proposal_v11(record)))

    saved = generate_rubric_proposal(record, api_key="k", model="gpt-test", client=Once())
    assert saved["prompt_version"] == PROMPT_VERSION
    assert seen["calls"] == 1
    assert seen["store"] is False
    assert "acs_no_antiplatelet" in seen["input"]
    assert "never decide anything" in seen["instructions"]
    assert saved["model"] == "gpt-test" and saved["rubric_version"] == rubric.VERSION


def test_an_encounter_with_no_authored_case_still_has_the_rubric_but_no_events():
    record = record_on_case("")
    source = build_rubric_source(record)
    assert source["defined_critical_events"] == []
    assert source["case_opportunities"] == []
    assert [row["domain_id"] for row in source["rubric"]] == list(rubric.DOMAIN_IDS)


@pytest.mark.parametrize("value", [True, False, 1.5, "2", None, 4, -1])
def test_a_score_that_is_not_one_of_the_four_levels_is_refused(value):
    """A boolean is an int in Python: True must never pass as the score 1."""
    record = record_on_case()
    proposal = sample_proposal()
    proposal["domains"][0]["score"] = value
    with pytest.raises(RubricAnalysisError):
        validate_rubric_proposal(envelope(record, proposal), record)


def test_every_level_of_the_rubric_is_accepted():
    record = record_on_case()
    for level in (0, 1, 2, 3, rubric.NOT_ASSESSABLE):
        proposal = sample_proposal()
        proposal["domains"][0]["score"] = level
        saved = validate_rubric_proposal(envelope(record, proposal), record)
        assert saved["proposal"]["domains"][0]["score"] == level


def test_a_concern_outside_the_defined_events_is_flagged_and_carries_no_penalty():
    """A worry the case never defined is for the faculty, not a deduction."""
    record = record_on_case()
    proposal = sample_proposal()
    proposal["concerns_for_review"] = [
        {"concern": "The nitrate rate was never restated after the pressure fell.",
         "evidence_refs": ["trace:0"]}]
    saved = validate_rubric_proposal(envelope(record, proposal), record)
    assert saved["proposal"]["concerns_for_review"]
    assert saved["proposal"]["critical_events"] == []
    # Concerns are not events: they never reach the arithmetic.
    result = rubric.score({d: 2 for d in rubric.DOMAIN_IDS},
                          saved["proposal"]["critical_events"])
    assert result["penalty"] == 0


# --- prompt 1.1: a verdict for every event, an opportunity for every domain ---
def test_a_1_1_proposal_validates_and_its_proposed_events_are_the_occurred_verdicts():
    record = record_on_case()
    saved = validate_rubric_proposal(
        envelope(record, sample_proposal_v11(record, occurred=("acs_no_antiplatelet",)), PROMPT_VERSION),
        record)
    assert [row["event_id"] for row in proposed_event_rows(saved)] == ["acs_no_antiplatelet"]
    assert set(event_verdicts(saved)) == {"acs_no_antiplatelet", "acs_provocation_test"}


def test_a_1_1_proposal_cannot_leave_a_defined_event_without_a_verdict():
    """Encounter 8 of 2026-09-24: the event the model never proposed had nowhere to be refused."""
    record = record_on_case()
    body = sample_proposal_v11(record)
    del body["event_verdicts"]["acs_provocation_test"]
    with pytest.raises(RubricAnalysisError):
        validate_rubric_proposal(envelope(record, body, PROMPT_VERSION), record)


def test_the_1_1_request_schema_demands_a_verdict_per_event_and_an_opportunity_per_domain():
    record = record_on_case()
    seen = {}

    class Once:
        class responses:
            @staticmethod
            def create(**kwargs):
                seen.update(kwargs)
                return SimpleNamespace(status="completed",
                                       output_text=json.dumps(sample_proposal_v11(record)))

    generate_rubric_proposal(record, api_key="k", model="m", client=Once())
    schema = seen["text"]["format"]["schema"]
    verdicts = schema["properties"]["event_verdicts"]
    assert set(verdicts["required"]) == {"acs_no_antiplatelet", "acs_provocation_test"}
    assert verdicts["additionalProperties"] is False
    domain = schema["properties"]["domains"]["items"]
    assert "opportunity" in domain["required"] and "next_level_gap" in domain["required"]
    # The request carries what the record settles, computed before any reading.
    source = json.loads(seen["input"])
    assert {row["event_id"] for row in source["record_screening"]["events"]} == {
        "acs_no_antiplatelet", "acs_provocation_test"}
    assert [row["domain_id"] for row in source["record_screening"]["domains"]] == list(rubric.DOMAIN_IDS)


def test_the_1_1_instructions_keep_identifiers_out_of_prose():
    from rubric_analysis import _INSTRUCTIONS
    assert "never by an identifier" in _INSTRUCTIONS
    # The old instruction asked for the identifier in the prose itself.
    assert "Cite decisions by their evidence_ref and name the minute" not in _INSTRUCTIONS
    assert "Give a verdict for every event" in _INSTRUCTIONS


def test_a_saved_1_0_proposal_still_reads_its_events():
    record = record_on_case()
    saved = validate_rubric_proposal(
        envelope(record, sample_proposal(events=("acs_no_antiplatelet",))), record)
    assert [row["event_id"] for row in proposed_event_rows(saved)] == ["acs_no_antiplatelet"]
    assert event_verdicts(saved) == {}


def test_an_encounter_without_defined_events_has_no_verdict_field():
    record = record_on_case("")
    body = sample_proposal_v11(record)
    assert "event_verdicts" not in body
    saved = validate_rubric_proposal(envelope(record, body, PROMPT_VERSION), record)
    assert proposed_event_rows(saved) == []
