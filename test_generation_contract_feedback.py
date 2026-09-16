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


class SimultaneousObservationRulesMustAgree(unittest.TestCase):
    """Both engines apply every matching rule in order, so the last one wins.

    A real paid generation of R1-05 spent three requests on a case whose
    hypotension rule asked for mottling and marked sweating while its hypoxia
    rule, matching at the very same minute, asked for none and mild. The engine
    preview showed a patient at a systolic pressure of 46 described as unmottled
    and the reviewer rejected the case. The contradiction is decidable locally.
    """

    def hypoxia_and_hypotension(self, case, *, later_mottling=False):
        rules = case["engine"]["state_rules"]
        rules[0] = {**rules[0], "id": "deterioration_hypotension",
                    "when": [{"field": "sbp", "operator": "lt", "value": 85}],
                    "set": {**rules[0]["set"], "extremities": "Cold",
                            "visual": {"expression": "markedly uncomfortable",
                                       "skin_color": "mild pallor",
                                       "diaphoresis": "marked", "mottling": True}}}
        rules[1] = {**rules[1], "id": "hypoxia_worse_breathing",
                    "when": [{"field": "spo2", "operator": "lt", "value": 90}],
                    "set": {**rules[1]["set"], "extremities": "Cold",
                            "visual": {"expression": "markedly uncomfortable",
                                       "skin_color": "mild pallor",
                                       "diaphoresis": "marked",
                                       "mottling": later_mottling}}}

    def test_overlapping_rules_that_disagree_are_rejected_with_both_indices(self):
        codes, issues = codes_for(lambda case: self.hypoxia_and_hypotension(case))
        self.assertNotIn("CONTRACT_UNCLASSIFIED", codes)
        self.assertIn("STATE_RULE_CONFLICT", codes)
        issue = next(i for i in issues if i["code"] == "STATE_RULE_CONFLICT")
        self.assertEqual(issue["path"], "engine.state_rules[1]")
        self.assertEqual(issue["details"]["conflicting_rule_index"], 0)
        self.assertEqual(issue["details"]["conflicting_rule_id"], "deterioration_hypotension")
        disagreements = {d["field"]: (d["earlier"], d["later"])
                         for d in issue["details"]["disagreements"]}
        self.assertEqual(disagreements["visual.mottling"], (True, False))

    def test_overlapping_rules_that_agree_are_accepted(self):
        """Overlap is allowed; only disagreement about the same finding is not."""
        case = deepcopy(novel_payload())
        self.hypoxia_and_hypotension(case)
        rules = case["engine"]["state_rules"]
        rules[1]["set"] = deepcopy(rules[0]["set"])
        rules[1]["examination"] = deepcopy(rules[0].get("examination") or [])
        compile_case(case)

    def test_rules_that_cannot_hold_together_are_not_reported(self):
        """Mutually exclusive thresholds may describe opposite states freely."""
        def mutate(case):
            rules = case["engine"]["state_rules"]
            rules[0] = {**rules[0], "when": [{"field": "sbp", "operator": "lt", "value": 85}],
                        "set": {**rules[0]["set"], "extremities": "Cold"}}
            rules[1] = {**rules[1], "when": [{"field": "sbp", "operator": "gte", "value": 90}],
                        "set": {**rules[1]["set"], "extremities": "Warm"}}
        case = deepcopy(novel_payload())
        mutate(case)
        compile_case(case)

    def test_an_overlap_only_outside_the_supported_range_is_not_reported(self):
        """sbp cannot exceed 300, so these two can never both hold."""
        def mutate(case):
            rules = case["engine"]["state_rules"]
            rules[0] = {**rules[0], "when": [{"field": "sbp", "operator": "gt", "value": 310}],
                        "set": {**rules[0]["set"], "extremities": "Cold"}}
            rules[1] = {**rules[1], "when": [{"field": "sbp", "operator": "gt", "value": 320}],
                        "set": {**rules[1]["set"], "extremities": "Warm"}}
        case = deepcopy(novel_payload())
        mutate(case)
        compile_case(case)
