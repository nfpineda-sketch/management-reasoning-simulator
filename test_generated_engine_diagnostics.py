"""A repair sees independent contract failures without changing clinical data."""
from copy import deepcopy
import json

import pytest

from generated_engine import validate_declarative_case, _matches, _response_capability_probe
from generated_engine_diagnostics import collect_declarative_issues, ENGINE_ISSUE_CODES
from test_generated_engine import make_state


def case():
    return make_state()["encounter_spec"]["clinical_case"]


def test_valid_engine_has_no_diagnostics_and_is_unchanged():
    draft = case()
    before = deepcopy(draft)
    assert collect_declarative_issues(draft) == []
    validate_declarative_case(draft)
    assert draft == before


def test_one_report_contains_multiple_unreachable_rules_and_each_trajectory_failure():
    draft = case()
    draft["engine"]["response_rules"][0].update(route="IV", delta={"crt": -4, "spo2": 10})
    draft["engine"]["response_rules"][1]["route"] = "intravenous"
    draft["engine"]["untreated_drift_per_min"]["sbp"] = -1
    before = deepcopy(draft)

    issues = collect_declarative_issues(draft)

    unreachable = [item for item in issues if item["code"] == "RESPONSE_ORDER_UNREACHABLE"]
    assert {item["path"] for item in unreachable} == {"engine.response_rules[0]", "engine.response_rules[1]"}
    assert unreachable[0]["details"]["declared_matchers"]["route"] == "IV"
    assert unreachable[0]["details"]["normalized_matchers"]["route"] is None
    assert unreachable[1]["details"]["normalized_matchers"]["route"] == "IV"
    bounds = [item for item in issues if item["code"] == "TRAJECTORY_BOUNDS"]
    assert {item["details"]["field"] for item in bounds} >= {"crt", "spo2", "sbp"}
    assert any(item["code"] == "TRAJECTORY_PRESSURE" for item in issues)
    assert all(item["code"] in ENGINE_ISSUE_CODES for item in issues)
    assert json.loads(json.dumps(issues, allow_nan=False)) == issues
    assert draft == before
    with pytest.raises(ValueError):
        validate_declarative_case(draft)


@pytest.mark.parametrize("kind, dose_field, reference_dose, expected_units", [
    ("fluid", "volume_ml", 500, "mL"),
    ("blood", "units", 1, "units"),
])
def test_normalized_matcher_feedback_can_match_the_real_order(kind, dose_field, reference_dose, expected_units):
    draft = case()
    rule = draft["engine"]["response_rules"][0]
    rule.update(action_type=kind, dose_field=dose_field, reference_dose=reference_dose, route="IV", units="unrecognized")
    issue = next(item for item in collect_declarative_issues(draft) if item["code"] == "RESPONSE_ORDER_UNREACHABLE")
    normalized = issue["details"]["normalized_matchers"]
    assert normalized["units"] == expected_units
    # The engine intentionally falls back to action type for the agent matcher
    # (including fluid and blood); it does not require an explicit agent field.
    assert normalized["agent"] == kind
    rule.update(normalized)
    actions, error = _response_capability_probe(draft, rule)
    assert not error
    assert _matches(rule, actions[0])
    validate_declarative_case(draft)


def test_interior_response_peak_is_reported_with_actionable_admissible_interval():
    draft = case()
    draft["engine"]["untreated_drift_per_min"]["spo2"] = -.1
    draft["engine"]["response_rules"][0]["delta"] = {"spo2": 6}
    issues = collect_declarative_issues(draft)
    peaks = [item for item in issues if item["code"] == "TRAJECTORY_BOUNDS" and item["details"]["field"] == "spo2"]

    assert len(peaks) == 1
    peak = peaks[0]["details"]
    assert peak["time_min"] == 10
    assert peak["actual"] == 104
    assert peak["horizon_min"] == 180
    assert peak["baseline"] == 93
    assert peak["drift_per_min"] == -.1
    assert peak["response_delta"] == 6
    assert peak["exposure"] == 2
    assert peak["onset_min"] == 0
    assert peak["duration_min"] == 10
    assert peak["admissible_delta_at_this_time"] == {"lower": -31, "upper": 4}
    # Being within bounds at the horizon cannot excuse an earlier excursion.
    assert 30 <= 93 - .1 * 180 + 6 * 2 <= 100
    with pytest.raises(ValueError, match="trajectory exceeds"):
        validate_declarative_case(draft)


def test_repeated_breakpoint_failure_is_deduplicated_to_worst_extremum():
    draft = case()
    draft["engine"]["untreated_drift_per_min"]["spo2"] = -.5
    issues = collect_declarative_issues(draft)
    failures = [item for item in issues if item["code"] == "TRAJECTORY_BOUNDS" and item["details"]["field"] == "spo2"]
    # Responses with no effect on this field share the untreated path and do
    # not repeat its same error. Distinct response excursions remain separate.
    assert len(failures) == 1
    assert all(item["details"]["time_min"] == 180 for item in failures)
    untreated = next(item["details"] for item in failures if item["details"]["response_index"] is None)
    assert untreated["admissible_drift_at_this_time"]["lower"] == pytest.approx(-.35)
    assert untreated["actual"] == 3


def test_malformed_rule_does_not_hide_another_rules_failure_or_untreated_drift():
    draft = case()
    draft["engine"]["response_rules"][0].update(duration_min=0, delta=None)
    draft["engine"]["response_rules"][1]["route"] = "intravenous"
    draft["engine"]["untreated_drift_per_min"]["sbp"] = -1
    issues = collect_declarative_issues(draft)
    assert {item["code"] for item in issues} >= {"RESPONSE_TIMING", "NUMERIC_FIELDS", "RESPONSE_ORDER_UNREACHABLE", "TRAJECTORY_BOUNDS"}


@pytest.mark.parametrize("draft", [None, {}, {"engine": None}, {"engine": {"response_rules": [None], "state_rules": [None], "initial_labs": None, "untreated_drift_per_min": None}}])
def test_incomplete_declarations_have_diagnostics_instead_of_crashing(draft):
    assert collect_declarative_issues(draft)


def test_observation_rule_and_investigation_timing_are_reported_together():
    draft = case()
    draft["engine"]["state_rules"][0]["when"][0]["field"] = "learner_grade"
    draft["engine"]["state_rules"][0]["set"]["pulse_present"] = False
    draft["engine"]["state_rules"][0]["set"]["ecg_profile"] = "imaginary"
    draft["investigations"]["vbg"]["duration_min"] = 3.5
    assert {item["code"] for item in collect_declarative_issues(draft)} >= {"STATE_CONDITION", "ARREST_UNSUPPORTED", "STATE_ECG", "STUDY_TIMING"}
