"""Evidence provenance and simulation-only objective catalog contracts."""

from copy import deepcopy

import pytest

from curriculum import CHALLENGES
from objectives import AUTONOMY_LEVELS, DEPTH_LEVELS, OBJECTIVES, evidence_items


def decision(status="executed", **extra):
    record = {
        "execution_status": status,
        "learner_input": "Reassess perfusion now.",
        "interpreted_action": [{"type": "reassessment", "delay_min": 0}],
        "reasoning": {"expected_effect": "Compare perfusion with my earlier expectation."},
        "decision_time_min": 4,
        "state_before": {"sim_time_min": 4, "observable": {"sbp": 94, "rhythm": "AF"}},
        "state_after": {"sim_time_min": 4, "observable": {"sbp": 94, "rhythm": "AF"}},
    }
    record.update(extra)
    return record


def reflection(**extra):
    answers = {
        "working_model_update": "The observed perfusion remains impaired.",
        "priority_trigger": "The repeat examination differs from my expectation.",
        "alternative_action": "Reconsider another mechanism before escalating treatment.",
        "expected_response_reassessment": "Compare blood pressure and tissue perfusion after the next action.",
    }
    answers.update(extra)
    return answers


def test_targets_remain_program_config_and_do_not_alias_encounter_challenges():
    assert {key: value["target"] for key, value in OBJECTIVES.items()} == {
        "TD1": 10, "F1": 15, "C1": 40, "C2": 25,
        "C3": 20, "C4": 20, "C14": 50, "C15": 5,
    }
    assert not OBJECTIVES.keys() & CHALLENGES.keys()
    assert {key for key, value in OBJECTIVES.items() if not value["supported"]} == {"C2", "C15"}
    for value in OBJECTIVES.values():
        assert value["scope"] and value["limitation"]
        assert "not independently verified" in value["target_source"]
        assert value["assessment_scope"] == "simulated_management_component"
    assert DEPTH_LEVELS == ("foundational", "integrated", "complex")
    assert AUTONOMY_LEVELS == ("guided", "prompted", "independent")


def test_executed_evidence_references_stable_raw_positions_and_display_ordinals():
    payload = {"session": {"management_trace": [
        decision("clarification_required"),
        decision("executed"),
        decision("terminal_locked"),
        decision("deferred"),
        decision("executed"),
        decision("not_executed"),
    ]}}
    evidence = evidence_items(payload)
    assert [(item["ref"], item["label"]) for item in evidence] == [
        ("trace:1", "Decision 1"), ("trace:4", "Decision 3"),
    ]
    payload["session"]["management_trace"].append(decision())
    assert evidence_items(payload)[:2] == evidence
    assert evidence_items(payload)[2]["ref"] == "trace:6"
    assert all(item["details"]["execution_status"] == "executed" for item in evidence)


def test_trace_preserves_real_reasoning_actions_and_states_without_hidden_context():
    event = decision(
        unrelated_secret="private",
        state_before={
            "sim_time_min": 1, "observable": {"hr": 171},
            "diagnostics": {"pocus": {"available": True}},
            "physiology": {"hidden_driver": "test"},
            "encounter_spec": {"challenge_id": "R1-03"},
        },
        state_after={"sim_time_min": 2, "observable": {"hr": 98}, "treatments": {"cardioversions": 1}},
    )
    payload = {"session": {"management_trace": [event], "_account_token": "private"}}
    original = deepcopy(payload)
    item = evidence_items(payload)[0]
    assert item["details"]["reasoning"] == event["reasoning"]
    assert item["details"]["interpreted_action"] == event["interpreted_action"]
    assert item["details"]["state_before"] == {
        "sim_time_min": 1, "observable": {"hr": 171},
        "diagnostics": {"pocus": {"available": True}},
    }
    assert item["details"]["state_after"] == event["state_after"]
    assert "unrelated_secret" not in item["details"]
    item["details"]["state_after"]["observable"]["hr"] = 1
    assert payload == original  # Assessment UI cannot mutate the stored trace.


def test_favorable_outcome_and_keywords_do_not_create_a_grade_or_objective_match():
    payload = {"session": {
        "management_trace": [decision(learner_input="I performed POCUS sedation airway resuscitation perfectly.")],
        "state": {"observable": {"sbp": 120, "rhythm": "Sinus rhythm"}},
    }}
    item = evidence_items(payload)[0]
    assert set(item) == {"ref", "label", "kind", "details"}
    assert not {"satisfactory", "objective_id", "score", "depth", "autonomy"} & item.keys()
    assert evidence_items({"session": {"state": payload["session"]["state"]}}) == []


def test_only_complete_explicit_reflections_are_available_for_review():
    payload = {"session": {"decision_review": {
        "complete": reflection(),
        "missing": reflection(expected_response_reassessment="  "),
        "coerced": reflection(priority_trigger=True),
        "not_text": reflection(alternative_action={"some": "value"}),
        "malformed": [],
    }}}
    items = evidence_items(payload)
    assert [item["ref"] for item in items] == ["reflection:complete"]
    assert items[0]["details"] == reflection()
    assert items[0]["kind"] == "reflection"


def test_precomparison_reflections_preserve_original_answers_without_expert_replacement():
    payload = {"session": {
        "precomparison_decision_review": {"d1": reflection(working_model_update="My original interpretation.")},
        "decision_review": {"d1": reflection(working_model_update="Copied expert interpretation."), "d2": reflection()},
    }}
    items = evidence_items(payload)
    assert len(items) == 1
    assert items[0]["ref"] == "reflection:d1"
    assert items[0]["details"]["working_model_update"] == "My original interpretation."


@pytest.mark.parametrize("payload", [None, [], "", {}, {"session": []}, {"session": {"management_trace": {}}},
                                    {"session": {"management_trace": [None, []], "decision_review": []}}])
def test_missing_or_malformed_records_never_generate_evidence(payload):
    assert evidence_items(payload) == []


def test_reflection_reference_cannot_collide_with_trace_reference():
    items = evidence_items({"session": {"management_trace": [decision()], "decision_review": {"trace:0": reflection()}}})
    refs = [item["ref"] for item in items]
    assert len(refs) == len(set(refs)) == 2
    assert refs == ["trace:0", "reflection:trace:0"]
