"""End-to-end engine regressions for generated curriculum encounters.

These tests execute the actual parser, treatment bundle, physiology, ECG, and
review functions. The Streamlit page is not executed and no API key is needed.
Run with ``python -m unittest test_curriculum_trajectories -v``.
"""

import ast
from copy import deepcopy
from html import escape
from io import BytesIO
import json
import math
from pathlib import Path
import random
import re
import unittest

from encounter_generator import GENERATOR_VERSION, PROFILES, generate_encounter


ROOT = Path(__file__).resolve().parent


class SessionState(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__


class FakeStreamlit:
    def __init__(self):
        self.session_state = SessionState()


def load_engine():
    """Load production functions without the account gate or Streamlit page."""
    tree = ast.parse((ROOT / "app.py").read_text(encoding="utf-8"))
    constants = {
        "SIMULATOR_VERSION", "MANAGEMENT_TRACE_DEFINITION",
        "REVIEW_RESPONSE_FIELDS", "ADAPTATION_PLAN_FIELDS",
        "EXPERT_COMPARISON_FIELDS", "EXPERT_REASONING_MODELS",
        "INITIAL_STATE", "PRESENTATION", "PS002_PRESENTATION", "CASE_CONFIGS",
        "REASONING_GATE_ACTION_TYPES", "REASONING_GATE_FIELD_LABELS",
        "REASONING_GATE_FIELD_STEMS", "REASONING_GATE_OVERRIDE",
    }
    nodes = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            nodes.append(node)
        elif isinstance(node, ast.Assign):
            names = {target.id for target in node.targets if isinstance(target, ast.Name)}
            if names & constants:
                nodes.append(node)
    st = FakeStreamlit()
    namespace = {
        "st": st, "re": re, "math": math, "random": random,
        "json": json, "deepcopy": deepcopy, "escape": escape,
        "BytesIO": BytesIO, "__file__": str(ROOT / "app.py"),
    }
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(ROOT / "app.py"), "exec"), namespace)
    return namespace


PROCEDURE = (
    "The patient is hypotensive, poorly perfused, and tachycardic. My working "
    "model is that rapid atrial fibrillation contributes to the impaired "
    "perfusion. My priority is to restore effective rhythm and improve "
    "perfusion. Administer etomidate 8 mg IV and midazolam 2 mg IV for "
    "procedural sedation, followed by synchronized electrical cardioversion "
    "at 200 J. I expect conversion to sinus rhythm with improved perfusion. "
    "Immediately after cardioversion, reassess rhythm, heart rate, blood "
    "pressure, mental status, and perfusion."
)

IMMEDIATE_REASSESSMENT = (
    "Reassess rhythm, heart rate, blood pressure, capillary refill, extremity "
    "temperature, oxygenation, work of breathing, mental status, and urine "
    "output now."
)


def initialize(engine, state):
    session = engine["st"].session_state
    session.clear()
    session.update({
        "state": deepcopy(state), "events": [], "history": [],
        "management_trace": [], "rng_counter": 0,
        "pending_action": None, "pending_bundle": None,
        "pending_reasoning": None, "reasoning_gate_counter": 0,
        "last_executed_action": None,
    })
    return session


def execute_turn(engine, text):
    session = engine["st"].session_state
    before = engine["management_state_snapshot"](session.state)
    parsed = engine["clinical_interpreter"](text)
    result = engine["execute_bundle"](parsed)
    after = engine["management_state_snapshot"](session.state)
    engine["record_management_trace"](text, parsed, result, before, after)
    return parsed, result, before, after


class CurriculumTrajectoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = load_engine()

    def encounter(self, profile, seed=17):
        return generate_encounter(
            "R2-01" if profile == "mixed_low_flow" else "R1-03",
            self.engine["INITIAL_STATE"], seed=seed, profile_id=profile,
        )

    def assert_ecg_matches(self, observable):
        svg = self.engine["_ecg_strip_svg"](observable)
        rhythm = {
            "AF": "af", "Sinus rhythm": "sinus", "PEA": "pea",
        }[observable["rhythm"]]
        self.assertIn(f'data-rhythm="{rhythm}"', svg)
        self.assertIn(f'data-rate="{observable["hr"]}"', svg)
        self.assertIn("Synthetic lead II ECG", svg)
        return svg

    def test_every_profile_executes_bundle_and_zero_time_reassessment(self):
        """The reported dropped-cardioversion and Sedated crash stay fixed."""
        for profile in PROFILES:
            for seed in (17, 83):
                with self.subTest(profile=profile, seed=seed):
                    encounter = self.encounter(profile, seed)
                    session = initialize(self.engine, encounter["state"])
                    initial_svg = self.assert_ecg_matches(session.state["observable"])
                    parsed, result, before, after = execute_turn(self.engine, PROCEDURE)
                    self.assertEqual(self.engine["reasoning_gate_missing"](parsed), [])
                    self.assertTrue(result["executed"], result)
                    types = [action["type"] for action in parsed["actions"]]
                    self.assertEqual(types[:2], ["procedural_sedation", "cardioversion"])
                    self.assertEqual(session.state["treatments"]["cardioversions"], 1)
                    self.assertEqual(session.state["treatments"]["procedural_sedations"], 1)
                    self.assertEqual(session.state["treatments"]["etomidate_total_mg"], 8)
                    self.assertEqual(session.state["treatments"]["midazolam_total_mg"], 2)
                    self.assertTrue(any(summary.get("energy_j") == 200 for summary in result["action_summaries"]))
                    # This bounded engine converts at 200 J, but conversion is not
                    # treated as evidence of learner competence or full recovery.
                    self.assertNotEqual(self.assert_ecg_matches(after["observable"]), initial_svg)
                    frozen_before = deepcopy(before)
                    time_before = session.state["sim_time"]
                    treatments_before = deepcopy(session.state["treatments"])
                    _, reassessment, _, current = execute_turn(self.engine, IMMEDIATE_REASSESSMENT)
                    self.assertTrue(reassessment["executed"])
                    self.assertEqual(reassessment["reassess_delay"], 0)
                    self.assertEqual(session.state["sim_time"], time_before)
                    self.assertEqual(session.state["treatments"], treatments_before)
                    self.assertEqual(before, frozen_before)
                    self.assert_ecg_matches(current["observable"])
                    # Let sedation wash out through the real minute-by-minute
                    # integration; the old ValueError occurred on this path.
                    _, followup, _, later = execute_turn(
                        self.engine,
                        "Reassess blood pressure, rhythm, perfusion, and mental status in 10 minutes.",
                    )
                    self.assertTrue(followup["executed"])
                    self.assertIn(later["observable"]["mental_status"], {
                        "Alert", "Drowsy", "Obtunded", "Unresponsive", "Sedated",
                    })
                    self.assert_ecg_matches(later["observable"])
                    self.assertEqual(session.state["treatments"]["cardioversions"], 1)

    def test_frozen_initial_state_replays_identical_trajectory(self):
        for profile in PROFILES:
            with self.subTest(profile=profile):
                frozen_state = self.encounter(profile, 41)["state"]
                trajectories = []
                for _ in range(2):
                    session = initialize(self.engine, frozen_state)
                    for text in (PROCEDURE, IMMEDIATE_REASSESSMENT):
                        execute_turn(self.engine, text)
                    trajectories.append((deepcopy(session.state), deepcopy(session.management_trace)))
                self.assertEqual(trajectories[0], trajectories[1])
                self.assertEqual(frozen_state["sim_time"], 0)
                self.assertEqual(frozen_state["treatments"]["cardioversions"], 0)

    def test_profiles_produce_distinct_patient_responses(self):
        responses = set()
        for profile in PROFILES:
            session = initialize(self.engine, self.encounter(profile)["state"])
            execute_turn(self.engine, PROCEDURE)
            observable = session.state["observable"]
            responses.add((
                observable["sbp"], observable["dbp"], observable["hr"],
                observable["crt"], round(session.state["hidden"]["tissue_perfusion"], 4),
            ))
        self.assertEqual(len(responses), len(PROFILES), "Profiles must affect the patient, not just the introduction.")

    def test_generated_trace_cannot_select_original_classroom_outcomes(self):
        for profile in PROFILES:
            with self.subTest(profile=profile):
                session = initialize(self.engine, self.encounter(profile)["state"])
                snapshot = self.engine["management_state_snapshot"](session.state)
                self.assertEqual(snapshot.get("encounter_variant"), GENERATOR_VERSION)
                self.assertNotIn("encounter_spec", snapshot)
                self.assertNotIn("challenge_id", snapshot)
                # Deliberately match the original classroom action ordinals.
                # They must not pull in its prewritten outcomes for a new case.
                trace = []
                actions = {3: "diltiazem", 7: "cardioversion", 9: "dobutamine"}
                for decision in range(1, 10):
                    trace.append({
                        "execution_status": "executed",
                        "decision_time_min": decision - 1,
                        "response_time_min": decision,
                        "learner_input": "A recorded intervention in this generated encounter.",
                        "interpreted_action": [{"type": actions.get(decision, "reassessment")}],
                        "action_summaries": [], "reasoning": {},
                        "state_before": deepcopy(snapshot), "state_after": deepcopy(snapshot),
                    })
                self.assertIsNone(self.engine["_ps001_classroom_review_items"](list(enumerate(trace, 1))))
                for decision in actions:
                    prompt = {"kind": "decision", "decision": decision, "review_id": f"decision-{decision}"}
                    model = self.engine["_expert_model_for_prompt"]("PS001", prompt, trace)
                    self.assertTrue(model["trajectory_grounded"])
                    self.assertIn("no material observable change was recorded", model["framing"])
                    self.assertIn(
                        f'BP {snapshot["observable"]["sbp"]}/{snapshot["observable"]["dbp"]}',
                        model["framing"],
                    )


if __name__ == "__main__":
    unittest.main()
