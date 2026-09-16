"""Every compile rejection must reach the repair request with an actionable cause.

Reproduces report 75e52322047c4e6cb6209d8414f3f15a (v0.24.13, challenge R1-05):
a ``dextrose`` response rule carrying ``washout_min: 30``. The value was inside
the permitted range; the action type was not an infusion. The compiler reported
CONTRACT_UNCLASSIFIED with the message "Infusion washout must be between 1 and
180 minutes.", no path and no details, so the paid correction adjusted a number
that was already valid and failed identically. 236 s and 31,970 tokens bought
two drafts and no encounter.

No paid calls: these checks run the local compiler only.
"""
from copy import deepcopy
import unittest

from case_authoring import AUTHOR_SCHEMA, UNUSABLE_RULE_FIELDS, expand_author_case
from generated_case_schema import compile_case
from generated_case_validation import ContractValidationError, safe_validation_codes
from generated_dynamics import INFUSIONS
from test_generated_case import novel_payload


RULE_SCHEMA = AUTHOR_SCHEMA["properties"]["engine"]["properties"]["response_rules"]["items"]
AUTHOR_ACTIONS = frozenset(RULE_SCHEMA["properties"]["action_type"]["enum"])


def codes_for(mutate):
    case = deepcopy(novel_payload())
    mutate(case)
    try:
        compile_case(case)
    except ContractValidationError as error:
        return safe_validation_codes(error), error.issues
    raise AssertionError("The mutated case was accepted by the compiler.")


class AuthorContractOffersOnlyUsableFields(unittest.TestCase):
    def test_no_offered_rule_field_is_unusable_by_every_allowed_action(self):
        """An option no allowed action can carry is a guaranteed fatal answer.

        Structured outputs require every property, so the author must emit the
        field; only ``null`` can ever compile. Offering it buys a failed draft.
        """
        restricted = {
            "washout_min": frozenset(INFUSIONS),
            "interpolate_settings": frozenset({"ventilator_adjustment"}),
            "mental_status_during": frozenset({"procedural_sedation"}),
            "mental_status_threshold": frozenset({"procedural_sedation"}),
            "rhythm_before": frozenset({"cardioversion"}),
            "rhythm_after": frozenset({"cardioversion"}),
            "recurrence": frozenset({"cardioversion"}),
            "settings": frozenset({"cardioversion", "ventilator_adjustment"}),
        }
        for field, kinds in restricted.items():
            usable = bool(kinds & AUTHOR_ACTIONS)
            self.assertEqual(usable, field in RULE_SCHEMA["properties"],
                             f"{field} is offered to the author but usable={usable}")

    def test_the_reported_failure_is_no_longer_expressible(self):
        self.assertNotIn("washout_min", RULE_SCHEMA["properties"])
        self.assertNotIn("washout_min", RULE_SCHEMA["required"])
        self.assertIn("washout_min", UNUSABLE_RULE_FIELDS)

    def test_expansion_restores_the_runtime_nulls_the_author_no_longer_writes(self):
        from test_compact_authoring import compact, fixture
        expanded = expand_author_case(compact(fixture()))
        self.assertTrue(expanded["engine"]["response_rules"])
        for rule in expanded["engine"]["response_rules"]:
            for field in UNUSABLE_RULE_FIELDS:
                self.assertIsNone(rule[field])
        compile_case(expanded)


class GateRejectionsCarryAnActionableCause(unittest.TestCase):
    """CONTRACT_UNCLASSIFIED sends a repair request with no path and no details."""

    def assert_classified(self, mutate, expected_code, expected_path_suffix):
        codes, issues = codes_for(mutate)
        self.assertNotIn("CONTRACT_UNCLASSIFIED", codes)
        self.assertIn(expected_code, codes)
        issue = next(item for item in issues if item["code"] == expected_code)
        self.assertTrue(issue["path"].endswith(expected_path_suffix), issue["path"])
        self.assertTrue(issue["details"], "the repair request needs the offending values")

    def test_washout_on_an_action_that_is_not_an_infusion(self):
        def mutate(case):
            rule = case["engine"]["response_rules"][0]
            self.assertNotIn(rule["action_type"], INFUSIONS)
            rule["washout_min"] = 30
        self.assert_classified(mutate, "RESPONSE_KINETICS", ".washout_min")
        _, issues = codes_for(mutate)
        message = next(i for i in issues if i["code"] == "RESPONSE_KINETICS")["message"]
        self.assertIn("titratable infusion", message)

    def test_setting_interpolation_outside_a_ventilator_grid(self):
        def mutate(case):
            case["engine"]["response_rules"][0]["interpolate_settings"] = True
        self.assert_classified(mutate, "RESPONSE_KINETICS", ".interpolate_settings")

    def test_sedated_mental_status_on_another_action(self):
        def mutate(case):
            case["engine"]["response_rules"][0]["mental_status_during"] = "Sedated"
        self.assert_classified(mutate, "RESPONSE_SEDATION", ".mental_status_during")

    def test_state_coupling_points_that_do_not_increase(self):
        def mutate(case):
            case["engine"]["response_rules"][0]["state_gain"] = {
                "field": "elapsed_min",
                "points": [{"value": 5, "factor": 1}, {"value": 5, "factor": 0}]}
        self.assert_classified(mutate, "RESPONSE_STATE_GAIN", ".state_gain.points")

    def test_an_infusion_washout_outside_its_range_names_the_field(self):
        """The runtime schema already rejects this one, and names the path."""
        case = deepcopy(novel_payload())
        rule = case["engine"]["response_rules"][0]
        rule.update(action_type="norepinephrine", agent="norepinephrine", route="IV",
                    units="mcg/min", dose_field="rate", reference_dose=5, washout_min=500)
        with self.assertRaises(ValueError) as raised:
            compile_case(case)
        self.assertIn("washout_min", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
