"""Locked reflection, chronology, provenance and privacy of learner AI synthesis."""

from copy import deepcopy
from datetime import datetime, timezone
import json
from types import SimpleNamespace

import pytest

from management_trace_analysis import (
    ManagementTraceAnalysisError, MAX_OUTPUT_TOKENS, MAX_TRACE_EVENTS,
    PROMPT_VERSION, SCHEMA_VERSION, build_analysis_source,
    generate_management_trace_analysis, source_fingerprint,
    validate_management_trace_analysis,
)


def sample_payload():
    before = {
        "sim_time_min": 0,
        "observable": {"sbp": 90, "dbp": 55, "hr": 130, "rhythm": "Sinus rhythm",
                       "crt": 4, "mental_status": "Alert", "spo2": 93},
        "treatments": {"oxygen": False, "cumulative_crystalloid_ml": 0},
        "diagnostics": {},
    }
    after = deepcopy(before)
    after["sim_time_min"] = 5
    after["observable"].update(sbp=98, hr=120)
    after["treatments"]["cumulative_crystalloid_ml"] = 250
    event = {
        "execution_status": "executed", "decision_time_min": 0, "response_time_min": 5,
        "learner_input": "Give 250 mL IV crystalloid and reassess perfusion in 5 minutes.",
        "reasoning": {"management_priority": "Improve perfusion",
                      "expected_effect": "I expect improved perfusion and will check breathing."},
        "action_summaries": [{"type": "fluid", "volume_ml": 250, "duration_min": 5, "route": "IV"}],
        "state_before": before, "state_after": after,
    }
    last_state = deepcopy(after)
    last_state["sim_time_min"] = 7
    second = {"execution_status": "executed", "decision_time_min": 5, "response_time_min": 7,
              "learner_input": "Reassess perfusion and breathing now.",
              "reasoning": {"problem_representation": "Response remains incomplete",
                            "management_priority": "Check the response before more fluid"},
              "action_summaries": [{"type": "reassess", "duration_min": 2}],
              "state_before": deepcopy(after), "state_after": last_state}
    answers = {
        "working_model_update": "The perfusion response remains uncertain.",
        "priority_trigger": "A change in perfusion or breathing would change my priority.",
        "alternative_action": "I would reassess the working model.",
        "expected_response_reassessment": "I would repeat the focused examination.",
    }
    return {"encounter_ended": True, "reflection_locked": True,
            "trace": [event, second], "reflections": {"decision-1": answers},
            "reflection_prompts": [{"review_id": "decision-1", "kind": "decision", "decision": 1}]}


def claim(text, *refs):
    return {"text": text, "evidence_refs": list(refs)}


def sample_analysis():
    return {
        "overview": claim("The recorded sequence moved from a fluid trial to checking its response.", "trace:0", "trace:1"),
        "pivotal_decisions": [{
            "decision_ref": "trace:0", "title": "A treatment trial followed by reassessment",
            "interpretation": claim("An explicit perfusion priority was recorded; a working explanation was not recorded at this point.", "trace:0"),
            "expected_vs_observed": claim("The recorded pressure increased after the trial, while the record does not establish its cause or complete resolution of the concern.", "trace:0"),
            "adaptation": claim("The next entry explicitly checked the response before additional fluid.", "trace:0", "trace:1"),
            "reflection_insight": claim("In the later reflection, the resident described the response as uncertain.", "reflection:decision-1"),
        }],
        "trajectory": claim("The expectation was followed by a documented reassessment priority, with continuing uncertainty expressed in the later model.", "trace:0", "trace:1"),
        "strengths": [claim("An expected effect was stated before the trial.", "trace:0")],
        "questions": [claim("Which recorded observation informed the decision to reassess before additional fluid?", "trace:1")],
    }


def sample_report(payload=None):
    return {"schema_version": SCHEMA_VERSION, "prompt_version": PROMPT_VERSION,
            "source_hash": source_fingerprint(payload or sample_payload()),
            "generated_at": datetime.now(timezone.utc).isoformat(), "model": "test-model",
            "analysis": sample_analysis()}


class StubClient:
    def __init__(self, analysis=None, *, error=None, status="completed", output=None):
        self.responses = self
        self.calls = []
        self.analysis = analysis if analysis is not None else sample_analysis()
        self.error, self.status, self.output = error, status, output

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return SimpleNamespace(status=self.status,
                               output_text=self.output if self.output is not None else json.dumps(self.analysis))


def test_source_preserves_exact_evidence_without_mutating_log():
    payload = sample_payload()
    original = deepcopy(payload)
    source = build_analysis_source(payload)
    first = source["timeline"][0]
    assert first["learner_input"] == payload["trace"][0]["learner_input"]
    assert first["recorded_reasoning"]["problem_representation"] == ""
    assert first["state_before"]["observable"]["sbp"] == 90
    assert first["state_after"]["observable"]["sbp"] == 98
    assert first["executed_actions"][0]["volume_ml"] == 250
    assert source["reflections"][0]["timing"] == "retrospective_locked_before_comparison"
    assert payload == original


@pytest.mark.parametrize("field,value", [("encounter_ended", False), ("reflection_locked", False),
                                         ("reflection_locked", 1), ("reflections", {})])
def test_analysis_cannot_run_before_encounter_and_reflection_are_locked(field, value):
    payload, client = sample_payload(), StubClient()
    payload[field] = value
    with pytest.raises(ManagementTraceAnalysisError):
        generate_management_trace_analysis(payload, api_key="", model="test-model", client=client)
    assert client.calls == []


def test_every_reflection_field_must_be_completed():
    payload = sample_payload()
    payload["reflections"]["decision-1"]["working_model_update"] = "  "
    with pytest.raises(ManagementTraceAnalysisError):
        build_analysis_source(payload)


def test_private_truth_faculty_scores_and_future_results_never_enter_request():
    payload = sample_payload()
    payload.update(user_id="PRIVATE_ACCOUNT", faculty_report="PRIVATE_FACULTY", diagnosis="PRIVATE_DIAGNOSIS")
    first = payload["trace"][0]
    first["reasoning"]["score"] = "PRIVATE_GRADE"
    first["interpreted_action"] = [{"label": "PRIVATE_UNEXECUTED_ACTION"}]
    first["action_summaries"][0]["mechanism"] = "PRIVATE_ACTION_MECHANISM"
    for state in (first["state_before"], first["state_after"]):
        state["encounter_spec"] = {"bias": "PRIVATE_BIAS"}
        state["clinical_case"] = {"truth": "PRIVATE_TRUTH"}
        state["observable"]["glucose_mg_dl"] = "PRIVATE_UNMEASURED_GLUCOSE"
        state["physiology"] = {"shock": "PRIVATE_PHYSIOLOGY"}
        state["diagnostics"] = {
            "poc_glucose": {"glucose_mg_dl": "PRIVATE_UNMEASURED_RESULT"},
            "ctpa": {"time_min": 99, "report": "PRIVATE_FUTURE_REPORT"},
            "troponin": {"time_min": 0, "status": "pending", "value_ng_l": "PRIVATE_PENDING_REPORT"},
            "secret": {"time_min": 0, "report": "PRIVATE_UNKNOWN_DIAGNOSTIC"},
        }
    first["state_before"]["diagnostics"]["hemoglobin"] = {"time_min": 0, "collected_at_min": 0,
                                                              "hemoglobin_g_dl": 8, "truth": "PRIVATE_LAB_METADATA"}
    payload["reflection_prompts"][0]["prompt"] = "PRIVATE_EXPERT_HINT"
    payload["reflections"]["decision-1"]["faculty_note"] = "PRIVATE_FACULTY_NOTE"
    client = StubClient()
    generate_management_trace_analysis(payload, api_key="DO_NOT_SEND_KEY", model="test-model", client=client)
    request = client.calls[0]
    assert "PRIVATE_" not in request["input"]
    assert "DO_NOT_SEND_KEY" not in json.dumps(request)
    source = json.loads(request["input"])
    assert source["timeline"][0]["state_before"]["diagnostics_available"]["hemoglobin"]["hemoglobin_g_dl"] == 8
    assert request["store"] is False
    assert request["max_output_tokens"] == MAX_OUTPUT_TOKENS
    assert request["text"]["format"]["strict"] is True


def test_diagnostic_availability_preserves_decision_time_boundary():
    payload = sample_payload()
    report = {"time_min": 4, "collected_at_min": 1, "value_ng_l": 160}
    payload["trace"][0]["state_before"]["diagnostics"]["troponin"] = report
    payload["trace"][0]["state_after"]["diagnostics"]["troponin"] = report
    source = build_analysis_source(payload)
    assert source["timeline"][0]["state_before"]["diagnostics_available"] == {}
    assert source["timeline"][0]["state_after"]["diagnostics_available"]["troponin"] == report


def test_novel_case_measured_reports_are_available_without_hidden_story():
    payload = sample_payload()
    payload["trace"][0]["state_after"]["diagnostics"] = {
        "head_ct": {"time_min": 5, "report": "No acute intracranial hemorrhage.", "truth": "PRIVATE_TRUTH"},
        "abdominal_ct": {"time_min": 5, "report": "No free intraperitoneal air."},
        "cortisol": {"time_min": 5, "cortisol_ug_dl": 2},
        "thyroid_function": {"time_min": 5, "tsh_miu_l": 0.01, "free_t4_ng_dl": 5},
        "ketones": {"time_min": 5, "ketones_mmol_l": 4},
        "toxicology": {"time_min": 5, "report": "Detected substance listed in measured report."},
    }
    result = build_analysis_source(payload)["timeline"][0]["state_after"]["diagnostics_available"]
    assert set(result) == {"head_ct", "abdominal_ct", "cortisol", "thyroid_function", "ketones", "toxicology"}
    assert result["thyroid_function"]["tsh_miu_l"] == 0.01
    assert "PRIVATE_TRUTH" not in json.dumps(result)


def test_only_acquired_ecg_parameters_are_evidence_without_case_profile():
    payload = sample_payload()
    recording = {"status": "available", "recording_id": "synthetic-recording",
                 "acquired_at_minutes": 3, "heart_rate": 122, "rhythm": "sinus",
                 "speed_mm_s": 25, "gain_mm_mv": 10,
                 "parameters": {"pr_s": .16, "qrs_s": .09, "qt_s": .35, "axis_deg": 55,
                                "engine_secret": "PRIVATE_PARAMETER"},
                 "profile": "PRIVATE_AUTHORED_PROFILE", "seed": "PRIVATE_SEED"}
    payload["trace"][0]["state_before"]["diagnostics"]["ecg"] = [recording]
    payload["trace"][0]["state_after"]["diagnostics"]["ecg"] = [recording]
    source = build_analysis_source(payload)
    assert source["timeline"][0]["state_before"]["ecg_recordings"] == []
    ecg = source["timeline"][0]["state_after"]["ecg_recordings"][0]
    assert ecg["time_min"] == 3 and ecg["waveform_parameters"]["qrs_s"] == .09
    assert "PRIVATE_" not in json.dumps(source)


def payload_with_events():
    payload = sample_payload()
    payload["encounter_events"] = [
        {"kind": "presentation", "time": 0, "text": "Visible arrival description."},
        {"kind": "patient_history", "time": 0, "text": "A symptom elicited after the first order."},
        {"kind": "you", "time": 0, "text": "I will now examine the patient."},
        {"kind": "examination", "time": 0, "text": "A finding elicited after the later order."},
        {"kind": "patient_history", "time": 0, "text": "UNSEEN_AFTER_FINAL_SNAPSHOT"},
        {"kind": "faculty_private", "time": 0, "text": "PRIVATE_FACULTY_INFO"},
    ]
    payload["trace"][0]["state_before"]["encounter_event_count"] = 1
    payload["trace"][0]["state_after"]["encounter_event_count"] = 2
    payload["trace"][1]["state_before"]["encounter_event_count"] = 3
    payload["trace"][1]["state_after"]["encounter_event_count"] = 4
    return payload


def test_same_timestamp_history_and_examination_are_ordered_by_frozen_cursor():
    source = build_analysis_source(payload_with_events())
    first, second = source["timeline"]
    assert first["state_before"]["encounter_evidence_refs"] == ["encounter:0"]
    assert first["state_after"]["encounter_evidence_refs"] == ["encounter:0", "encounter:1"]
    assert second["state_before"]["encounter_evidence_refs"] == ["encounter:0", "encounter:1", "encounter:2"]
    assert second["state_after"]["encounter_evidence_refs"] == ["encounter:0", "encounter:1", "encounter:2", "encounter:3"]
    assert "UNSEEN_AFTER_FINAL_SNAPSHOT" not in json.dumps(source)
    assert "PRIVATE_" not in json.dumps(source)


def test_legacy_trace_without_cursor_cannot_inherit_later_same_time_events():
    payload = payload_with_events()
    for event in payload["trace"]:
        for side in ("state_before", "state_after"):
            event[side].pop("encounter_event_count")
    source = build_analysis_source(payload)
    assert source["encounter_events"] == []
    assert "A symptom elicited" not in json.dumps(source)


def test_event_time_must_also_be_available_even_with_matching_capture_cursor():
    payload = payload_with_events()
    payload["encounter_events"][1]["time"] = 99
    source = build_analysis_source(payload)
    assert "encounter:1" not in json.dumps(source)
    assert "A symptom elicited" not in json.dumps(source)


def test_known_event_citations_are_accepted_but_later_same_time_history_is_rejected():
    payload = payload_with_events()
    report = sample_report(payload)
    moment = report["analysis"]["pivotal_decisions"][0]
    moment["interpretation"]["evidence_refs"].append("encounter:0")
    moment["expected_vs_observed"]["evidence_refs"].append("encounter:1")
    moment["adaptation"]["evidence_refs"].append("encounter:3")
    assert validate_management_trace_analysis(report, payload) == report
    moment["interpretation"]["evidence_refs"].append("encounter:1")
    with pytest.raises(ManagementTraceAnalysisError, match="later"):
        validate_management_trace_analysis(report, payload)


def test_claim_cannot_use_a_later_examination_as_earlier_observed_response():
    payload = payload_with_events()
    report = sample_report(payload)
    report["analysis"]["pivotal_decisions"][0]["expected_vs_observed"]["evidence_refs"].append("encounter:3")
    with pytest.raises(ManagementTraceAnalysisError, match="own decision"):
        validate_management_trace_analysis(report, payload)


@pytest.mark.parametrize("value", [-1, 999, True, "2"])
def test_invalid_event_capture_cursor_cannot_broaden_disclosure(value):
    payload = payload_with_events()
    payload["trace"][0]["state_before"]["encounter_event_count"] = value
    with pytest.raises(ManagementTraceAnalysisError, match="cursor"):
        build_analysis_source(payload)


def test_encounter_cursor_cannot_move_back_between_management_decisions():
    payload = payload_with_events()
    payload["trace"][1]["state_before"]["encounter_event_count"] = 1
    with pytest.raises(ManagementTraceAnalysisError, match="previously available"):
        build_analysis_source(payload)


def test_fingerprint_changes_for_acquired_history_but_not_future_uncaptured_history():
    payload = payload_with_events()
    report = sample_report(payload)
    payload["encounter_events"][4]["text"] = "Another uncaptured later detail."
    assert validate_management_trace_analysis(report, payload) == report
    payload["encounter_events"][1]["text"] = "An amended acquired symptom."
    with pytest.raises(ManagementTraceAnalysisError, match="does not match"):
        validate_management_trace_analysis(report, payload)


def test_nonexecuted_attempts_cannot_become_treatment_or_shift_decision_links():
    payload = sample_payload()
    pending = deepcopy(payload["trace"][0])
    pending.update(execution_status="clarification_required", response_time_min=0)
    pending["state_after"] = deepcopy(pending["state_before"])
    payload["trace"].insert(0, pending)
    source = build_analysis_source(payload)
    assert source["timeline"][0]["executed_actions"] == []
    assert source["timeline"][0]["decision_number"] is None
    assert source["timeline"][1]["decision_number"] == 1
    assert source["reflections"][0]["decision_ref"] == "trace:1"


def test_longitudinal_reflection_maps_only_to_its_actual_decision_range():
    payload = sample_payload()
    payload["reflection_prompts"][0].update(kind="longitudinal", decision_range=[1, 2])
    source = build_analysis_source(payload)
    assert source["reflections"][0]["decision_refs"] == ["trace:0", "trace:1"]
    assert source["reflections"][0]["decision_ref"] == "trace:1"
    payload["reflection_prompts"][0]["decision_range"] = [1, 3]
    with pytest.raises(ManagementTraceAnalysisError):
        build_analysis_source(payload)


@pytest.mark.parametrize("change", ["evidence", "reflection", "prompt_mapping"])
def test_fingerprint_invalidates_stale_analysis_on_relevant_source_change(change):
    payload = sample_payload()
    report = sample_report(payload)
    if change == "evidence":
        payload["trace"][0]["state_after"]["observable"]["sbp"] = 96
    elif change == "reflection":
        payload["reflections"]["decision-1"]["working_model_update"] = "A revised locked answer."
    else:
        payload["reflection_prompts"][0]["decision"] = 2
    with pytest.raises(ManagementTraceAnalysisError, match="does not match"):
        validate_management_trace_analysis(report, payload)


def test_fingerprint_ignores_hidden_truth_and_later_plan_and_copies_output():
    payload = sample_payload()
    report = sample_report(payload)
    payload["clinical_case"] = {"truth": "hidden"}
    payload["trace"][0]["state_before"]["hidden"] = {"seed": "hidden"}
    payload["adaptation_plan"] = {"next_priority": "A later prospective plan."}
    validated = validate_management_trace_analysis(report, payload)
    assert validated == report
    validated["analysis"]["overview"]["text"] = "Changed returned copy."
    assert validated != report


@pytest.mark.parametrize("mutation", [
    "unknown_ref", "later_ref_for_interpretation", "reflection_as_contemporaneous",
    "wrong_response_ref", "unrelated_reflection", "invented_measurement", "extra_field",
    "duplicate_pivot", "wrong_version", "missing_provenance",
])
def test_invalid_or_hindsight_analysis_is_rejected(mutation):
    payload = sample_payload()
    report = sample_report(payload)
    first = report["analysis"]["pivotal_decisions"][0]
    if mutation == "unknown_ref":
        report["analysis"]["overview"]["evidence_refs"] = ["trace:99"]
    elif mutation == "later_ref_for_interpretation":
        first["interpretation"]["evidence_refs"] = ["trace:0", "trace:1"]
    elif mutation == "reflection_as_contemporaneous":
        first["interpretation"]["evidence_refs"] = ["trace:0", "reflection:decision-1"]
    elif mutation == "wrong_response_ref":
        first["expected_vs_observed"]["evidence_refs"] = ["trace:1"]
    elif mutation == "unrelated_reflection":
        payload["reflection_prompts"][0]["decision"] = 2
        report["source_hash"] = source_fingerprint(payload)
    elif mutation == "invented_measurement":
        first["expected_vs_observed"]["text"] = "Systolic pressure reached 180 mmHg."
    elif mutation == "extra_field":
        report["analysis"]["score"] = 99
    elif mutation == "duplicate_pivot":
        report["analysis"]["pivotal_decisions"].append(deepcopy(first))
    elif mutation == "wrong_version":
        report["prompt_version"] = "obsolete"
    else:
        del report["source_hash"]
    with pytest.raises(ManagementTraceAnalysisError):
        validate_management_trace_analysis(report, payload)


@pytest.mark.parametrize("client", [StubClient(error=RuntimeError("sk-PRIVATE secret prompt")),
                                     StubClient(status="incomplete"), StubClient(output="not-json"),
                                     StubClient(output="{}")])
def test_failed_generation_is_explicit_unavailable_without_secret_or_template(client):
    with pytest.raises(ManagementTraceAnalysisError) as caught:
        generate_management_trace_analysis(sample_payload(), api_key="", model="test-model", client=client)
    assert "PRIVATE" not in str(caught.value)
    assert len(client.calls) == 1


def test_missing_key_fails_before_provider_request():
    with pytest.raises(ManagementTraceAnalysisError, match="OPENAI_API_KEY"):
        generate_management_trace_analysis(sample_payload(), api_key="", model="test-model")


def test_successful_generation_is_provenanced_and_retains_original_record():
    payload = sample_payload()
    original = deepcopy(payload)
    result = generate_management_trace_analysis(payload, api_key="", model="test-model", client=StubClient())
    assert result["source_hash"] == source_fingerprint(payload)
    assert result["schema_version"] == SCHEMA_VERSION
    assert result["analysis"] == sample_analysis()
    assert payload == original


@pytest.mark.parametrize("kind", ["overlap", "nan", "unknown_status", "too_many_events", "invalid_collection"])
def test_invalid_source_timeline_is_rejected_before_ai(kind):
    payload, client = sample_payload(), StubClient()
    if kind == "overlap":
        payload["trace"][1]["decision_time_min"] = 4
    elif kind == "nan":
        payload["trace"][0]["state_before"]["observable"]["hr"] = float("nan")
    elif kind == "unknown_status":
        payload["trace"][0]["execution_status"] = "assumed_executed"
    elif kind == "too_many_events":
        payload["trace"] *= MAX_TRACE_EVENTS
    else:
        payload["trace"][0]["state_before"]["diagnostics"]["troponin"] = {"time_min": 0, "collected_at_min": 1, "value_ng_l": 100}
    with pytest.raises(ManagementTraceAnalysisError):
        generate_management_trace_analysis(payload, api_key="", model="test-model", client=client)
    assert client.calls == []


def test_the_request_offers_each_part_of_a_decision_only_what_the_validator_accepts():
    # Scenario 2 of the 2026-09-24 batch lost its document A four times: the
    # schema let an adaptation cite a later reflection, and the validator then
    # refuses the whole report (faculty decision B3). The request now narrows
    # each part to the references its rule allows; the rules are unchanged.
    client = StubClient()
    generate_management_trace_analysis(sample_payload(), api_key="", model="test-model", client=client)
    schema = client.calls[0]["text"]["format"]["schema"]
    moment = schema["properties"]["pivotal_decisions"]["items"]["properties"]

    def offered(part):
        return set(part["properties"]["evidence_refs"]["items"]["enum"])

    for key in ("interpretation", "expected_vs_observed", "adaptation"):
        assert "reflection:decision-1" not in offered(moment[key])
        assert {"trace:0", "trace:1"} <= offered(moment[key])
    assert offered(moment["reflection_insight"]["anyOf"][0]) == {"reflection:decision-1"}
    assert "reflection:decision-1" in offered(schema["properties"]["overview"])


def test_an_adaptation_citing_a_later_reflection_is_still_refused():
    report = sample_report()
    report["analysis"]["pivotal_decisions"][0]["adaptation"]["evidence_refs"].append("reflection:decision-1")
    with pytest.raises(ManagementTraceAnalysisError):
        validate_management_trace_analysis(report, sample_payload())
