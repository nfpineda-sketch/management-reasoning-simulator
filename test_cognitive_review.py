"""Source-only clinical review and post-encounter cognitive-focus visibility."""

from copy import deepcopy
import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from cognitive_catalog import BIAS_CHALLENGES
from cognitive_review import trajectory_review, reflection_items
from test_curriculum_assignment import FakeStreamlit, runtime_functions


def decision():
    before = {"sim_time_min": 0, "case_id": "CE-HIDDEN_FAMILY",
              "observable": {"sbp": 122, "dbp": 74, "hr": 86, "mental_status": "Drowsy", "respiratory_rate": 6},
              "diagnostics": {}}
    after = deepcopy(before)
    after["sim_time_min"] = 5
    after["observable"].update(mental_status="Alert", respiratory_rate=14)
    return {"execution_status": "executed", "decision_time_min": 0, "response_time_min": 5,
            "state_before": before, "state_after": after,
            "interpreted_action": [{"type": "naloxone", "dose_mg": 0.4, "route": "IV"}],
            "action_summaries": [{"type": "naloxone", "agent": "naloxone", "dose_mg": 0.4, "route": "IV", "duration_min": 5}],
            "reasoning": {"problem_representation": "Reduced ventilation with decreased alertness",
                          "management_priority": "Support breathing",
                          "expected_effect": "Increased respiratory rate and improved engagement",
                          "rationale": "Evaluate the response to the proposed intervention",
                          "reassessment_target": "Respiratory rate, oxygenation, and alertness in 5 minutes"}}


@pytest.mark.parametrize("context", [None, {"user": {"role": "resident"}}])
def test_cognitive_focus_is_absent_before_end_and_visible_after_end(context):
    challenge = BIAS_CHALLENGES["R1-05"]
    state = {"encounter_spec": {"challenge_id": "R1-05"}}
    st = FakeStreamlit({"encounter_ended": False, "state": state,
                       "encounter_assignment": {"challenge_id": "R1-05"}})
    render = runtime_functions(st)["render_learning_focus"]
    render(context)
    assert st.rendered == []
    st.session_state["encounter_ended"] = True
    render(context)
    assert challenge["title"] in st.rendered
    assert "Cognitive focus: " + challenge["bias_name"] in st.rendered
    assert challenge["objective"] in st.rendered
    assert all(question in st.rendered for question in challenge["debrief_questions"])


def test_shared_review_uses_frozen_encounter_and_not_an_old_account_assignment():
    st = FakeStreamlit({"encounter_ended": True,
                       "encounter_assignment": {"challenge_id": "R1-05"},
                       "state": {"encounter_spec": {"challenge_id": "R2-02"}},
                       "encounter_closed_state": {"encounter_spec": {"challenge_id": "R1-06"}}})
    runtime_functions(st)["render_learning_focus"](None)
    assert "Cognitive focus: Premature closure" in st.rendered
    assert "Cognitive focus: Anchoring" not in st.rendered
    assert "Cognitive focus: Confirmation bias" not in st.rendered


def test_shared_review_falls_back_when_public_snapshot_omits_private_spec():
    st = FakeStreamlit({"encounter_ended": True,
                       "state": {"encounter_spec": {"challenge_id": "R1-06"}},
                       "encounter_closed_state": {"case_id": "CE-EXAMPLE", "observable": {"hr": 80}}})
    runtime_functions(st)["render_learning_focus"](None)
    assert "Cognitive focus: Premature closure" in st.rendered


def test_shared_app_displays_focus_after_its_actual_snapshot_is_frozen(monkeypatch):
    monkeypatch.setenv("MRS_AUTH_MODE", "shared")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    app = AppTest.from_file(str(Path(__file__).with_name("app.py")), default_timeout=30)
    app.secrets["APP_PASSWORD"] = "test-only"
    app.session_state["_shared_access_granted"] = True
    app.run()
    assert not app.exception
    selector = next(item for item in app.selectbox if item.label == "Clinical problem")
    assert selector.value in BIAS_CHALLENGES
    selector.set_value("R1-06").run()
    next(item for item in app.button if item.label == "Begin Encounter").click().run()
    assert not app.exception
    assert not any("Cognitive focus:" in item.value for item in app.markdown)
    next(item for item in app.radio if item.label == "Encounter").set_value("Treat").run()
    app.text_area[0].set_value("Reassess now").run()
    next(item for item in app.button if item.label == "Submit").click().run()
    assert not app.exception
    next(item for item in app.button if item.label == "Complete Encounter & Begin Review").click().run()
    assert not app.exception
    assert app.session_state["encounter_ended"] is True
    assert "encounter_spec" not in app.session_state["encounter_closed_state"]
    assert any("Cognitive focus: Premature closure" in item.value for item in app.markdown)


def test_opioid_like_observations_are_not_reinterpreted_as_hypoperfusion():
    event = decision()
    review = trajectory_review(event, source_decision=4)
    encoded = json.dumps(review)
    assert "respiratory rate 6 /min" in encoded and "respiratory rate 14 /min" in encoded
    assert "Drowsy" in encoded and "Alert" in encoded
    assert "naloxone" in encoded and "dose mg=0.4" in encoded
    assert "hypoperfusion" not in encoded and "sepsis" not in encoded and "vasopressor" not in encoded
    assert "correct" not in encoded and "bias" not in encoded
    assert review["source_decision"] == 4
    assert review["source_action_types"] == ["naloxone"]
    assert review["trajectory_grounded"] is True


def test_hypoglycemic_state_uses_measured_glucose_without_hidden_diagnostic_story():
    event = decision()
    event["decision_time_min"] = 2
    event["state_before"]["sim_time_min"] = 2
    event["state_before"]["observable"]["glucose_mg_dl"] = "PRIVATE_UNMEASURED_VALUE"
    event["state_before"]["diagnostics"]["poc_glucose"] = {"time_min": 1, "collected_at_min": 0, "glucose_mg_dl": 36}
    event["state_after"]["diagnostics"]["poc_glucose"] = {"time_min": 5, "glucose_mg_dl": 105}
    event["reasoning"]["problem_representation"] = "A low measured glucose may contribute to the reduced alertness"
    event["reasoning"]["expected_effect"] = "Glucose and alertness should improve"
    event["action_summaries"] = [{"type": "dextrose", "agent": "dextrose", "dose_g": 25, "route": "IV"}]
    review = trajectory_review(event)
    encoded = json.dumps(review)
    assert "glucose: 36 mg/dL" in encoded and "glucose: 105 mg/dL" in encoded
    assert "available at 1 min, collected at 0 min" in encoded
    assert "dextrose" in encoded and "dose g=25" in encoded
    assert "PRIVATE_" not in encoded
    assert "hypoperfusion" not in encoded and "opioid" not in encoded
    assert review["source_action_types"] == ["dextrose"]


def test_hidden_case_bias_and_final_outcome_cannot_change_comparison():
    event = decision()
    original = trajectory_review(event)
    altered = deepcopy(event)
    altered["hidden"] = {"diagnosis": "PRIVATE_DIAGNOSIS", "bias_name": "PRIVATE_BIAS"}
    for snapshot in (altered["state_before"], altered["state_after"]):
        snapshot["encounter_spec"] = {"bias_id": "PRIVATE_BIAS", "diagnosis": "PRIVATE_DIAGNOSIS"}
        snapshot["physiology"] = {"perfusion": "PRIVATE_PHYSIOLOGY"}
        snapshot["outcome"] = "PRIVATE_FINAL_OUTCOME"
        snapshot["observable"]["internal"] = "PRIVATE_OBSERVABLE"
    altered["action_summaries"][0]["mechanism"] = "PRIVATE_MECHANISM"
    altered["reasoning"]["private_grading"] = "PRIVATE_GRADING"
    assert trajectory_review(altered) == original
    assert "PRIVATE_" not in json.dumps(trajectory_review(altered))


def test_future_pending_unmeasured_and_unknown_diagnostics_are_not_review_evidence():
    event = decision()
    event["state_before"]["diagnostics"] = {
        "troponin": {"time_min": 4, "report": "FUTURE_REPORT"},
        "ctpa": {"time_min": 0, "status": "pending", "report": "PENDING_REPORT"},
        "poc_glucose": {"glucose_mg_dl": "UNMEASURED_RESULT"},
        "unknown_family": {"time_min": 0, "report": "UNKNOWN_REPORT"},
    }
    review = json.dumps(trajectory_review(event))
    assert all(value not in review for value in ("FUTURE_REPORT", "PENDING_REPORT", "UNMEASURED_RESULT", "UNKNOWN_REPORT"))


def test_list_resolution_uses_executed_evidence_and_never_adopts_proposed_medication():
    first = decision()
    deferred = deepcopy(first)
    deferred["execution_status"] = "deferred"
    deferred["action_summaries"] = [{"type": "antibiotics", "agent": "NOT_ADMINISTERED"}]
    review = trajectory_review([first, deferred])
    assert review["source_decision"] == 1
    assert review["source_action_types"] == ["naloxone"]
    assert "NOT_ADMINISTERED" not in json.dumps(review)
    deferred_review = trajectory_review(deferred, source_decision=2)
    assert deferred_review["source_action_types"] == []
    assert "NOT_ADMINISTERED" not in json.dumps(deferred_review)


@pytest.mark.parametrize("trace", [None, [], {}, {"state_before": {}}, [dict(execution_status="deferred")]])
def test_missing_frozen_evidence_does_not_invent_a_model(trace):
    assert trajectory_review(trace) is None


def test_reflection_items_preserve_ordinals_and_use_first_model_change_and_last():
    first = decision()
    locked = deepcopy(first)
    locked["execution_status"] = "terminal_locked"
    second = deepcopy(first)
    second["decision_time_min"] = 6
    second["reasoning"]["problem_representation"] = "The respiratory response remains incomplete"
    last = deepcopy(second)
    last["decision_time_min"] = 70
    ignored = deepcopy(last)
    ignored["execution_status"] = "deferred"
    ignored["reasoning"]["expected_effect"] = "PRIVATE_PROPOSED_EXPECTATION"
    items = reflection_items([first, locked, second, last, ignored])
    assert [item[1] for item in items] == [1, 3, 4]
    assert [item[2] for item in items] == ["00:00", "00:06", "01:10"]
    assert all(item[0] == "decision" and len(item) == 5 for item in items)
    assert items[1][3] == "Review a change in your explanation"
    assert "PRIVATE_PROPOSED_EXPECTATION" not in json.dumps(items)


@pytest.mark.parametrize("expected_effect", ["Improved ventilation and alertness", "Higher measured glucose and improved alertness"])
def test_reflection_prompts_do_not_relabel_neurologic_or_respiratory_findings(expected_effect):
    event = decision()
    event["reasoning"]["expected_effect"] = expected_effect
    event["state_before"]["observable"].update(spo2=99, respiratory_rate=6, mental_status="Drowsy")
    event["state_before"]["hidden"] = {"hypoperfusion": True, "diagnosis": "PRIVATE_CAUSE"}
    items = reflection_items([event])
    encoded = json.dumps(items).lower()
    assert len(items) == 1
    assert expected_effect.lower() in encoded
    assert all(forbidden not in encoded for forbidden in ("hypoperfusion", "sepsis", "atrial", "reassuring", "private_cause", "incorrect"))
    assert "observations supported or challenged" in encoded


def test_reflection_without_executed_evidence_is_empty():
    assert reflection_items([]) == []
    assert reflection_items([{"execution_status": "deferred"}]) == []
