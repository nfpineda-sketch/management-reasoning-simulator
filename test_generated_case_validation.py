"""A correction must see independent clinical flaws without accepting any one."""
from copy import deepcopy
from types import SimpleNamespace

import pytest

from generated_case_schema import CASE_SCHEMA, compile_case, validate_schema
from generated_case_validation import ContractValidationError, safe_validation_codes
from test_generated_case import novel_payload


def issues_for(raw):
    before = deepcopy(raw)
    validate_schema(raw, CASE_SCHEMA)
    with pytest.raises(ContractValidationError) as caught:
        compile_case(raw)
    assert raw == before
    return caught.value.issues


def gas(values):
    return {"id": "vbg", "duration_min": 3,
            "result": [{"field": field, "value": value} for field, value in values.items()],
            "result_bindings": []}


def test_one_draft_reports_clinical_and_executable_failures_together():
    raw = novel_payload()
    raw["patient"]["pronouns"] = "he/him"
    raw["observable"]["mental_status"] = "Unresponsive"
    raw["observable"]["peripheral_perfusion"] = "critical"
    raw["observable"]["visual"]["expression"] = "neutral"
    raw["investigations"][0]["result_bindings"] = []
    raw["investigations"][0]["result"][0]["value"] = 20
    raw["engine"]["state_rules"][0]["examination"] = None
    raw["engine"]["response_rules"][0]["route"] = "IV"
    raw["engine"]["response_rules"][0]["delta"][2]["value"] = -4
    issues = issues_for(raw)
    codes = {issue["code"] for issue in issues}
    assert {"PATIENT_PRONOUNS", "HISTORY_SOURCE", "VISUAL_PERFUSION", "DIAGNOSTIC_BASELINE",
            "NEUROLOGICAL_UPDATE", "RESPONSE_ORDER_UNREACHABLE", "TRAJECTORY_BOUNDS"} <= codes
    measurements = [issue for issue in issues if issue["code"] == "DIAGNOSTIC_BASELINE"]
    assert measurements[0]["path"] == "case.investigations.poc_glucose.result.glucose_mg_dl"
    assert measurements[0]["details"]["result"] == 20
    assert measurements[0]["details"]["baseline"] == 95


@pytest.mark.parametrize("field", ["ph", "pco2_mm_hg", "bicarbonate_mmol_l"])
def test_schema_allowed_text_in_gas_is_a_correctable_issue_not_a_type_error(field):
    raw = novel_payload()
    values = {"ph": 7.42, "pco2_mm_hg": 35, "bicarbonate_mmol_l": 22}
    values[field] = "not numerical"
    raw["investigations"].append(gas(values))
    issues = issues_for(raw)
    assert "BLOOD_GAS_NUMERIC" in {issue["code"] for issue in issues}


def test_wrong_binding_and_multiple_unbound_measurements_all_explain_the_contradiction():
    raw = novel_payload()
    raw["investigations"][0]["result_bindings"][0]["observable_field"] = "temperature_c"
    raw["investigations"][0]["result"][0]["value"] = 30
    raw["investigations"][2]["result_bindings"] = []
    raw["investigations"][2]["result"][2]["value"] = 4
    raw["investigations"].append(gas({"ph": 7.0, "pco2_mm_hg": 35, "bicarbonate_mmol_l": 22}))
    issues = issues_for(raw)
    assert len([issue for issue in issues if issue["code"] == "DIAGNOSTIC_BASELINE"]) == 2
    assert {"DIAGNOSTIC_BINDING", "BLOOD_GAS_CONSISTENCY"} <= {issue["code"] for issue in issues}


def test_all_duplicate_locations_are_reported_before_ambiguous_normalization():
    raw = novel_payload()
    raw["examination"][-1] = deepcopy(raw["examination"][0])
    raw["investigations"].append(deepcopy(raw["investigations"][0]))
    raw["investigations"][0]["result"].append(deepcopy(raw["investigations"][0]["result"][0]))
    raw["investigations"][0]["result_bindings"].append(deepcopy(raw["investigations"][0]["result_bindings"][0]))
    raw["engine"]["untreated_drift_per_min"].append(deepcopy(raw["engine"]["untreated_drift_per_min"][0]))
    raw["engine"]["response_rules"][0]["delta"].append(deepcopy(raw["engine"]["response_rules"][0]["delta"][0]))
    raw["engine"]["state_rules"][0]["examination"].append(deepcopy(raw["engine"]["state_rules"][0]["examination"][0]))
    issues = issues_for(raw)
    assert len(issues) == 7
    assert {issue["code"] for issue in issues} == {"DUPLICATE_FIELD", "DUPLICATE_STUDY"}
    assert len({issue["path"] for issue in issues}) == 7


def test_missing_essential_study_does_not_hide_other_checks_or_raise_key_error():
    raw = novel_payload()
    raw["investigations"] = raw["investigations"][1:]
    raw["patient"]["pronouns"] = "he/him"
    issues = issues_for(raw)
    assert {"ESSENTIAL_STUDY_MISSING", "PATIENT_PRONOUNS"} <= {issue["code"] for issue in issues}
    missing = next(issue for issue in issues if issue["code"] == "ESSENTIAL_STUDY_MISSING")
    assert missing["details"]["study_id"] == "poc_glucose"


def test_an_authoritative_gate_still_blocks_when_new_rule_has_no_collector(monkeypatch):
    def reject_new_rule(case):
        raise ValueError("A future clinical gate rejected this case.")
    monkeypatch.setattr("generated_engine.validate_declarative_case", reject_new_rule)
    issues = issues_for(novel_payload())
    assert issues == [{"code": "CONTRACT_UNCLASSIFIED", "path": "case",
                       "message": "A future clinical gate rejected this case.", "details": {}}]


def test_only_allowlisted_codes_can_leave_private_validation_feedback():
    error = SimpleNamespace(issues=[{"code": "DIAGNOSTIC_BASELINE", "path": "private", "message": "private", "details": {"secret": "private"}},
                                    {"code": "RESPONSE_ORDER_UNREACHABLE"}, {"code": "secret diagnostic"},
                                    {"code": ["DIAGNOSTIC_BASELINE"]}, "private", {"code": None}])
    assert safe_validation_codes(error) == ["DIAGNOSTIC_BASELINE", "RESPONSE_ORDER_UNREACHABLE"]
    assert safe_validation_codes(ValueError("private")) == ["CONTRACT_UNCLASSIFIED"]
