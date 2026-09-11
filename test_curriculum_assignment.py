"""Formative assignment and objective-visibility contracts for the pilot."""

import ast
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

from curriculum import CHALLENGES, assign_challenge, eligible_challenges, evidence_summary


def evidence_payload(complete=False):
    if not complete:
        return {"session": {"management_trace": [], "decision_review": {}}}
    return {"session": {
        "management_trace": [{
            "execution_status": "executed",
            "reasoning": {
                "problem_representation": "The rhythm may be contributing to poor perfusion.",
                "management_priority": "Restore perfusion.",
                "expected_effect": "I expect improved perfusion if the rhythm is contributing.",
            },
            "interpreted_action": [{"type": "reassessment", "delay_min": 0}],
        }],
        "decision_review": {"d1": {
            "working_model_update": "Persistent poor perfusion suggests an additional process.",
            "priority_trigger": "The repeat examination remains abnormal.",
            "alternative_action": "Review evidence for other circulatory mechanisms.",
            "expected_response_reassessment": "Compare several perfusion observations again.",
        }},
    }}


def attempt(challenge_id, position, complete_evidence=False, **overrides):
    record = {
        "challenge_id": challenge_id, "status": "completed", "is_sandbox": False,
        "updated_at": f"2026-01-{position:02d}T12:00:00Z",
        "payload": evidence_payload(complete_evidence),
    }
    record.update(overrides)
    return record


class AssignmentTests(unittest.TestCase):
    def test_only_implemented_challenges_within_assigned_year_are_eligible(self):
        self.assertEqual(set(eligible_challenges(1)), {"R1-03", "R1-04"})
        self.assertEqual(set(eligible_challenges(2)), {"R1-03", "R1-04", "R2-01"})
        self.assertEqual(eligible_challenges(3), eligible_challenges(2))
        for year in (0, 4, -1, True, False, 1.0, 1.9, "1", None):
            with self.subTest(year=year), self.assertRaises(ValueError):
                eligible_challenges(year)

    def test_new_resident_assignment_is_reproducible_and_never_uses_later_year(self):
        for seed in range(30):
            result = assign_challenge(1, [], seed)
            self.assertIn(result["challenge_id"], {"R1-03", "R1-04"})
            self.assertEqual(result, assign_challenge(1, [], seed))
            self.assertEqual(result["reason"], "initial_exposure")

    def test_active_abandoned_and_sandbox_attempts_do_not_confer_exposure(self):
        excluded = [
            attempt("R1-03", 1, True, status="active"),
            attempt("R1-04", 2, True, status="abandoned"),
            attempt("R2-01", 3, True, status="active"),
            attempt("R1-03", 4, True, is_sandbox=True),
            attempt("R1-04", 5, True, is_sandbox=True),
            attempt("R2-01", 6, True, is_sandbox=True),
        ]
        for seed in range(10):
            self.assertEqual(assign_challenge(2, excluded, seed), assign_challenge(2, [], seed))

    def test_initial_exposure_precedes_repeating_an_evidence_gap(self):
        attempts = [attempt("R1-03", 1), attempt("R1-04", 2)]
        result = assign_challenge(2, attempts, 17)
        self.assertEqual(result["challenge_id"], "R2-01")
        self.assertEqual(result["reason"], "initial_exposure")

    def test_revisit_uses_latest_evidence_and_interleaves(self):
        records = [
            attempt("R1-03", 1),
            attempt("R1-03", 2, True),  # Earlier absence is no longer the latest evidence.
            attempt("R1-04", 3),
            attempt("R2-01", 4, True),
        ]
        chosen = assign_challenge(2, records, 17)
        self.assertEqual(chosen["challenge_id"], "R1-04")
        self.assertEqual(chosen["reason"], "interleaved_evidence_review")
        records.append(attempt("R1-04", 5))
        self.assertNotEqual(assign_challenge(2, records, 17)["challenge_id"], "R1-04")

    def test_case_outcome_never_creates_evidence_or_mastery(self):
        records = [attempt(key, i) for i, key in enumerate(CHALLENGES, 1)]
        favorable = deepcopy(records)
        adverse = deepcopy(records)
        for record in favorable:
            record["payload"]["session"]["state"] = {"observable": {"sbp": 120, "rhythm": "Sinus rhythm"}}
        for record in adverse:
            record["payload"]["session"]["state"] = {"hidden": {"cardiac_arrest": True}, "observable": {"sbp": 0}}
        self.assertEqual(assign_challenge(2, favorable, 17), assign_challenge(2, adverse, 17))
        self.assertEqual(assign_challenge(2, favorable, 17)["competence_decision"], "Not assessed automatically")
        for result in (evidence_summary(favorable[0]["payload"]), evidence_summary(adverse[0]["payload"])):
            self.assertTrue(all(not value for value in result["recorded"].values()))

    def test_evidence_is_explicit_with_displayed_decision_ordinals(self):
        payload = evidence_payload(True)
        payload["session"]["management_trace"].insert(0, {
            "execution_status": "clarification_required",
            "reasoning": {"problem_representation": "An incomplete order requires clarification."},
            "interpreted_action": [{"type": "reassessment"}],
        })
        result = evidence_summary(payload)
        # These are the displayed Management Trace decision ordinals, not raw
        # array positions; clarification-only entries are not displayed decisions.
        self.assertEqual(result["recorded"]["working_model"], [1])
        self.assertEqual(result["recorded"]["reassessment"], [1])
        self.assertEqual(result["recorded"]["reflection"], ["d1"])
        self.assertIn("does not establish", result["interpretation"])

    def test_planned_reassessment_and_partial_reflection_are_not_counted_as_complete(self):
        payload = evidence_payload(True)
        event = payload["session"]["management_trace"][0]
        event["interpreted_action"] = [{"type": "cardioversion"}]
        event["reasoning"]["reassessment"] = "I will check perfusion later."
        payload["session"]["decision_review"]["d1"]["expected_response_reassessment"] = "  "
        result = evidence_summary(payload)["recorded"]
        self.assertEqual(result["reassessment"], [])
        self.assertEqual(result["reflection"], [])
        self.assertEqual(result["working_model"], [1])

    def test_deferred_or_terminal_locked_actions_do_not_supply_executed_evidence(self):
        payload = evidence_payload(True)
        event = payload["session"]["management_trace"][0]
        payload["session"]["management_trace"] = [
            dict(event, execution_status="deferred"),
            dict(event, execution_status="terminal_locked"),
            event,
        ]
        result = evidence_summary(payload)["recorded"]
        self.assertEqual(result["reassessment"], [2])
        self.assertEqual(result["working_model"], [2])


class FakeStreamlit:
    def __init__(self, session=None):
        self.session_state = session or {}
        self.rendered = []
        self.selectors = []
        self.sidebar = self
        self.navigation = []

    def subheader(self, value):
        self.rendered.append(str(value))

    caption = subheader
    write = subheader
    json = subheader
    dataframe = lambda self, value, **kwargs: self.subheader(value)

    def button(self, *args, **kwargs):
        return False

    def expander(self, value, **kwargs):
        self.rendered.append(str(value))
        return self

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def selectbox(self, label, options, **kwargs):
        self.selectors.append(str(label))
        return list(options)[0]

    def radio(self, label, options, **kwargs):
        self.navigation.append((str(label), list(options)))
        return list(options)[kwargs.get("index", 0)]


def runtime_functions(fake_st):
    path = Path(__file__).with_name("curriculum_runtime.py")
    tree = ast.parse(path.read_text())
    selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in {"render_dashboard", "render_learning_focus"}]
    namespace = {"st": fake_st, "CHALLENGES": CHALLENGES,
                 "render_progress_dashboard": lambda context: None,
                 "render_attempt_assessment": lambda context, record: None}
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(path), "exec"), namespace)
    return namespace


class ObjectiveVisibilityTests(unittest.TestCase):
    def context(self, role="resident"):
        return {
            "user": {"id": "learner1", "role": role, "training_year": 1},
            "token": "test-token",
            "store": SimpleNamespace(list_attempts=lambda token: []),
        }

    def test_resident_dashboard_does_not_offer_a_challenge_selector_or_cue(self):
        st = FakeStreamlit()
        runtime_functions(st)["render_dashboard"](self.context(), {}, lambda: None)
        self.assertEqual(st.selectors, [])
        self.assertEqual(st.navigation, [("Navigation", ["Clinical encounters", "My progress"])])
        rendered = json.dumps(st.rendered)
        for key, challenge in CHALLENGES.items():
            self.assertNotIn(key, rendered)
            self.assertNotIn(challenge["title"], rendered)
            self.assertNotIn(challenge["objective"], rendered)

    def test_assigned_objective_is_revealed_only_after_encounter_end(self):
        st = FakeStreamlit({"encounter_ended": False, "encounter_assignment": {"challenge_id": "R1-03"}})
        render = runtime_functions(st)["render_learning_focus"]
        render(self.context())
        self.assertEqual(st.rendered, [])
        st.session_state["encounter_ended"] = True
        render(self.context())
        self.assertIn(CHALLENGES["R1-03"]["title"], st.rendered)
        self.assertIn(CHALLENGES["R1-03"]["objective"], st.rendered)

    def test_authorized_faculty_dashboard_has_sandbox_selector(self):
        st = FakeStreamlit()
        runtime_functions(st)["render_dashboard"](self.context("faculty"), {}, lambda: None)
        self.assertIn("Management challenge", st.selectors)
        self.assertIn("Faculty sandbox", st.rendered)


if __name__ == "__main__":
    unittest.main()
