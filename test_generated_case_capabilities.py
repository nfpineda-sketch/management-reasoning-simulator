"""Case authors see contracts that the actual parser and engine can execute."""
from copy import deepcopy
import json

import pytest

from generated_case_capabilities import executable_generation_constraints
from generated_case_schema import ACTIONS, compile_case, validate_schema, CASE_SCHEMA
from generated_engine import BOUNDS, _matches, _validate_response_capability
from family_engine import _MEDICINES
from test_generated_case import novel_payload


def test_capabilities_cover_only_existing_actions_and_remain_json_ready():
    constraints = executable_generation_constraints()
    assert set(constraints["action_contracts"]) == set(ACTIONS)
    assert json.loads(json.dumps(constraints, allow_nan=False)) == constraints
    assert constraints["trajectory_numeric_bounds"] == {key: list(value) for key, value in BOUNDS.items()}
    for kind, (_, lower, upper) in _MEDICINES.items():
        assert constraints["action_contracts"][kind]["reference_dose_software_bounds"] == {
            "minimum": lower, "maximum": upper,
        }


@pytest.mark.parametrize("kind", ACTIONS)
def test_every_capability_example_matches_a_real_normalized_order(kind):
    contract = executable_generation_constraints()["action_contracts"][kind]
    rule, action = contract["matching_response_fields_example"], contract["validated_order_example"]
    _validate_response_capability({"observable": {"mental_status": "Alert"}}, rule)
    assert _matches(rule, action)
    for field, options in (("route", "route_values"), ("units", "unit_values"), ("device", "device_values")):
        assert rule[field] in contract[options]
        for value in contract[options]:
            _validate_response_capability({"observable": {"mental_status": "Alert"}}, {**rule, field: value})


def test_natural_but_unreachable_fluid_route_is_explicitly_excluded_for_author():
    raw = novel_payload()
    raw["engine"]["response_rules"][0]["route"] = "IV"
    validate_schema(raw, CASE_SCHEMA)  # Valid model schema, but not a live-order match.
    with pytest.raises(ValueError, match="cannot be reached"):
        compile_case(raw)
    constraints = executable_generation_constraints()
    fluid = constraints["action_contracts"]["fluid"]
    assert fluid["route_values"] == [None]
    raw["engine"]["response_rules"][0]["route"] = fluid["matching_response_fields_example"]["route"]
    compile_case(raw)


def test_authored_medication_can_use_actual_dose_units_and_canonical_route():
    raw = novel_payload()
    contract = executable_generation_constraints()["action_contracts"]["steroid"]
    rule = raw["engine"]["response_rules"][1]
    rule["route"] = "intravenous"
    validate_schema(raw, CASE_SCHEMA)
    with pytest.raises(ValueError, match="cannot be reached"):
        compile_case(raw)
    assert "intravenous" not in contract["route_values"]
    rule.update(deepcopy(contract["matching_response_fields_example"]))
    compile_case(raw)
    assert rule["dose_field"] == "dose_mg"
    assert rule["agent"] == "hydrocortisone"
    assert rule["units"] == "mg"


def test_unreachable_oxygen_device_and_wrong_infusion_units_are_not_advertised():
    contracts = executable_generation_constraints()["action_contracts"]
    assert "high-flow nasal cannula" not in contracts["oxygen"]["device_values"]
    assert None not in contracts["oxygen"]["device_values"]
    assert set(contracts["norepinephrine"]["unit_values"]) == {"mcg/min", "mcg/kg/min"}
    assert contracts["norepinephrine"]["route_values"] == ["IV"]


def test_capability_results_are_independent_between_calls():
    altered = executable_generation_constraints()
    altered["trajectory_numeric_bounds"]["spo2"][1] = 120
    altered["action_contracts"]["fluid"]["matching_response_fields_example"]["route"] = "IV"
    fresh = executable_generation_constraints()
    assert fresh["trajectory_numeric_bounds"]["spo2"][1] == 100
    assert fresh["action_contracts"]["fluid"]["route_values"] == [None]
