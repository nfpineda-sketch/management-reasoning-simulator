"""New-family faculty evidence stays observed, timestamped, and source-bounded."""

from copy import deepcopy
import json

import pytest

from faculty_analysis import FacultyAnalysisError, build_analysis_source
from test_faculty_analysis import sample_record


def _event(record):
    return record["payload"]["session"]["management_trace"][0]


def test_new_reports_keep_exact_values_and_exclude_future_or_private_findings():
    record = sample_record()
    event = _event(record)
    troponin = {
        "time_min": 3, "collected_at_min": 0, "value_ng_l": 164, "upper_reference_ng_l": 14,
        "report": "High-sensitivity troponin: 164 ng/L (upper reference 14 ng/L).",
        "faculty_diagnosis": "PRIVATE_FACULTY_DIAGNOSIS",
    }
    hemoglobin = {"time_min": 4, "hemoglobin_g_dl": 7.2,
                  "report": "Hemoglobin 7.2 g/dL.", "hidden_source": "PRIVATE_SOURCE"}
    ctpa = {"time_min": 12, "report": "FUTURE_CTPA_RESULT"}
    event["state_before"]["diagnostics"] = {"troponin": deepcopy(troponin), "ctpa": deepcopy(ctpa)}
    event["state_after"]["diagnostics"] = {
        "troponin": troponin, "hemoglobin": hemoglobin, "ctpa": ctpa,
        "family_spec": {"report": "PRIVATE_CASE_SPEC"},
    }
    event["state_after"]["encounter_spec"] = {"diagnosis": "PRIVATE_ENCOUNTER_SPEC"}
    event["state_after"]["hidden"] = {"cause": "PRIVATE_CAUSE"}
    original = deepcopy(record)
    source = build_analysis_source(record)
    selected = source["decision_events"][0]
    assert selected["state_before"]["diagnostics_available"] == {}
    assert selected["state_after"]["diagnostics_available"] == {
        "troponin": {key: troponin[key] for key in ("time_min", "collected_at_min", "value_ng_l", "upper_reference_ng_l", "report")},
        "hemoglobin": {key: hemoglobin[key] for key in ("time_min", "hemoglobin_g_dl", "report")},
    }
    assert "PRIVATE_" not in json.dumps(source)
    assert "FUTURE_CTPA_RESULT" not in json.dumps(source)
    assert record == original


def test_glucose_is_evidence_only_after_its_documented_measurement():
    record = sample_record()
    event = _event(record)
    # Even if a source snapshot accidentally carries the private physiologic
    # value as an observable, the faculty extractor must not promote it.
    for snapshot in (event["state_before"], event["state_after"]):
        snapshot["observable"].update(glucose_mg_dl=36, temperature_c=38.4)
        snapshot["diagnostics"]["poc_glucose"] = {"time_min": 2, "glucose_mg_dl": 36}
    selected = build_analysis_source(record)["decision_events"][0]
    assert "glucose_mg_dl" not in selected["state_before"]["observable"]
    assert "temperature_c" not in selected["state_before"]["observable"]
    assert "poc_glucose" not in selected["state_before"]["diagnostics_available"]
    assert selected["state_after"]["diagnostics_available"]["poc_glucose"] == {
        "time_min": 2, "glucose_mg_dl": 36,
    }


def test_generated_case_diagnostics_are_included_only_when_available():
    record = sample_record()
    event = _event(record)
    for key, scalar in (("cortisol", "cortisol_ug_dl"), ("thyroid_function", "tsh_miu_l"), ("ketones", "ketones_mmol_l")):
        for side in ("state_before", "state_after"):
            event[side]["diagnostics"][key] = {"time_min": 2, scalar: 1.5, "private_truth": "DO_NOT_SEND"}
    event["state_after"]["diagnostics"]["head_ct"] = {"time_min": 2, "report": "Recorded CT result."}
    event["state_after"]["diagnostics"]["abdominal_ct"] = {"time_min": 50, "report": "FUTURE_RESULT"}
    selected = build_analysis_source(record)["decision_events"][0]
    assert "cortisol" not in selected["state_before"]["diagnostics_available"]
    assert selected["state_after"]["diagnostics_available"]["cortisol"]["cortisol_ug_dl"] == 1.5
    assert selected["state_after"]["diagnostics_available"]["head_ct"]["report"] == "Recorded CT result."
    assert "FUTURE_RESULT" not in json.dumps(selected) and "DO_NOT_SEND" not in json.dumps(selected)


def test_ctpa_actions_preserve_delivered_report_and_consultation_without_hidden_spec():
    record = sample_record()
    event = _event(record)
    event["decision_time_min"] = 10
    event["response_time_min"] = 16
    event["state_before"]["sim_time_min"] = 10
    event["state_after"]["sim_time_min"] = 16
    report = {"time_min": 15, "report": "CT pulmonary angiography shows bilateral pulmonary arterial filling defects."}
    event["interpreted_action"] = [{"type": "diagnostic", "diagnostic": "ctpa", "private_intent": "PRIVATE_INTENT"}]
    event["action_summaries"] = [
        {"type": "diagnostic", "diagnostic": "ctpa", "time_min": 15,
         "result": {**report, "clinical_family": "PRIVATE_FAMILY"}},
        {"type": "consultation", "service": "critical care", "label": "Critical care consultation requested", "time_min": 16,
         "faculty_notes": "PRIVATE_FACULTY_NOTES"},
    ]
    selected = build_analysis_source(record)["decision_events"][0]
    assert selected["interpreted_actions"] == [{"type": "diagnostic", "diagnostic": "ctpa"}]
    assert selected["executed_action_summaries"] == [
        {"type": "diagnostic", "diagnostic": "ctpa", "time_min": 15, "result": report},
        {"type": "consultation", "service": "critical care", "label": "Critical care consultation requested", "time_min": 16},
    ]
    assert "PRIVATE_" not in json.dumps(selected)


def test_new_diagnostic_action_does_not_expose_future_or_unknown_result():
    record = sample_record()
    event = _event(record)
    event["action_summaries"] = [
        {"diagnostic": "troponin", "result": {"time_min": 10, "report": "FUTURE_TROPONIN"}},
        {"diagnostic": "unknown_case_lookup", "result": {"time_min": 0, "report": "PRIVATE_UNKNOWN_REPORT"}},
    ]
    summaries = build_analysis_source(record)["decision_events"][0]["executed_action_summaries"]
    assert all("result" not in summary for summary in summaries)


def test_administered_medication_summary_keeps_agent_dose_route_units_and_time():
    record = sample_record()
    event = _event(record)
    administration = {"type": "medication", "agent": "naloxone", "dose": 0.4,
                      "units": "mg", "route": "IV", "time_min": 2}
    event["interpreted_action"] = [{"type": "medication", "agent": "naloxone", "dose": 0.4, "units": "mg", "route": "IV"}]
    event["action_summaries"] = [{**administration, "mechanism": "PRIVATE_RECEPTOR_STATE"}]
    event["state_after"]["treatment_log"] = [{**administration, "debug": "PRIVATE_DEBUG"}]
    selected = build_analysis_source(record)["decision_events"][0]
    assert selected["executed_action_summaries"] == [administration]
    assert "treatment_log" not in selected["state_after"]
    assert "PRIVATE_" not in json.dumps(selected)
    # A proposed/deferred dose must never be represented as administered.
    deferred = deepcopy(event)
    deferred["execution_status"] = "deferred"
    record["payload"]["session"]["management_trace"].append(deferred)
    assert build_analysis_source(record)["decision_events"][1]["executed_action_summaries"] == []


def test_delivered_resuscitation_totals_preserved_without_engine_medication_state():
    record = sample_record()
    event = _event(record)
    event["state_before"]["treatments"].update(total_crystalloid_ml=0, packed_red_cells_units=0)
    event["state_after"]["treatments"].update({
        "total_crystalloid_ml": 500, "packed_red_cells_units": 2, "bag_mask": True,
        "administered_medications": [{"agent": "PRIVATE_UNCHECKED_NESTED_VALUE"}],
        "blood_effect": "PRIVATE_BLOOD_EFFECT",
    })
    selected = build_analysis_source(record)["decision_events"][0]
    assert selected["state_before"]["treatments"]["total_crystalloid_ml"] == 0
    assert selected["state_before"]["treatments"]["packed_red_cells_units"] == 0
    assert selected["state_after"]["treatments"]["total_crystalloid_ml"] == 500
    assert selected["state_after"]["treatments"]["packed_red_cells_units"] == 2
    assert selected["state_after"]["treatments"]["bag_mask"] is True
    assert "PRIVATE_" not in json.dumps(selected)


@pytest.mark.parametrize("diagnostic", ["troponin", "ctpa", "hemoglobin"])
def test_nested_report_objects_cannot_be_stringified_into_provider_input(diagnostic):
    record = sample_record()
    _event(record)["state_after"]["diagnostics"][diagnostic] = {
        "time_min": 2, "report": {"hidden": "PRIVATE_REPORT_OBJECT"},
    }
    with pytest.raises(FacultyAnalysisError, match="invalid format"):
        build_analysis_source(record)
