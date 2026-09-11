"""Offline tests of bounded composition and provider-failure containment."""

import ast
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

import encounter_generator as generator


def initial_state():
    tree = ast.parse(Path(__file__).with_name("app.py").read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "INITIAL_STATE"
            for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise AssertionError("The app must expose its pristine PS001 state.")


class FakeResponses:
    def __init__(self, value=None, status="completed", output=None, error=None):
        self.value = value or {
            "profile_id": "mixed_low_flow",
            "arrival_context": "at_home",
            "symptom_focus": "dizziness",
        }
        self.status = status
        self.output = output or []
        self.error = error
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(deepcopy(kwargs))
        if self.error:
            raise self.error
        return SimpleNamespace(
            status=self.status,
            output_text=self.value if isinstance(self.value, str) else json.dumps(self.value),
            output=self.output,
            usage=SimpleNamespace(input_tokens=120, output_tokens=34, total_tokens=154),
        )


class EncounterGenerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = initial_state()

    def compose(self, **kwargs):
        return generator.generate_encounter("R1-03", self.base, seed=17, **kwargs)

    def test_seeded_fallback_is_reproducible_and_detached(self):
        before = deepcopy(self.base)
        first = self.compose()
        second = self.compose()
        self.assertEqual(first, second)
        self.assertEqual(self.base, before)
        second_before = deepcopy(second)
        first["state"]["observable"]["hr"] = 0
        first["spec"]["patient_facts"]["age_years"] = 0
        self.assertEqual(second, second_before)
        self.assertEqual(first["state"]["encounter_spec"]["patient_facts"]["age_years"], 70)

    def test_all_profiles_have_exact_visible_narrative_and_coherent_entry_fields(self):
        for challenge in generator.SUPPORTED_CHALLENGES:
            for profile_id in generator.PROFILES:
                with self.subTest(challenge=challenge, profile=profile_id):
                    result = generator.generate_encounter(challenge, self.base, seed=4, profile_id=profile_id)
                    state, text = result["state"], result["presentation"]
                    o, h = state["observable"], state["hidden"]
                    self.assertEqual(state["case_id"], "PS001")
                    self.assertEqual(state["sim_time"], 0)
                    self.assertEqual(state["treatments"], self.base["treatments"])
                    self.assertIn(f"{o['sbp']}/{o['dbp']} mmHg", text)
                    self.assertIn(f"{o['hr']}/min", text)
                    self.assertIn(f"{o['spo2']}% on room air", text)
                    self.assertAlmostEqual(h["effective_map"], (o["sbp"] + 2 * o["dbp"]) / 3)
                    self.assertEqual(h["fluid_responsiveness"], h["preload_responsiveness"])
                    self.assertEqual(h["preload_state"], h["effective_volume"])
                    self.assertIn("70-year-old man", text)
                    self.assertEqual(state["encounter_facts"]["sex"], "male")
                    self.assertIn("He reports two days of dysuria", state["encounter_facts"]["focused_history"])
                    for hidden in (challenge, profile_id, "urinary", "objective", "challenge", "contractile reserve"):
                        self.assertNotIn(hidden, text)

    def test_model_result_changes_real_profile_and_preserves_api_contract(self):
        responses = FakeResponses()
        result = self.compose(client=SimpleNamespace(responses=responses), model="configured-test-model")
        self.assertEqual(result["source"], "ai")
        self.assertEqual(result["spec"]["profile_id"], "mixed_low_flow")
        self.assertEqual(result["state"]["hidden"]["contractile_reserve"], 0.8)
        self.assertEqual(result["spec"]["provenance"]["usage"]["total_tokens"], 154)
        self.assertIsNone(result["warning"])
        request = responses.calls[0]
        self.assertEqual(request["model"], "configured-test-model")
        self.assertTrue(request["text"]["format"]["strict"])
        self.assertEqual(request["text"]["format"]["type"], "json_schema")
        self.assertFalse(request["store"])
        self.assertNotIn("base_state", request["input"])
        self.assertNotIn("api_key", request)
        self.assertEqual(result["spec"]["content_sha256"], generator._spec_digest(result["spec"]))

    def test_invalid_schema_and_unbounded_values_use_whole_fallback(self):
        expected = self.compose()
        invalid_responses = [
            "not json",
            "[]",
            {"profile_id": "new_diagnosis", "arrival_context": "at_home", "symptom_focus": "dizziness"},
            {"profile_id": 1000, "arrival_context": "at_home", "symptom_focus": "dizziness"},
            {"profile_id": "mixed_low_flow", "arrival_context": "at_home", "symptom_focus": "dizziness", "sbp": 600},
            {"profile_id": "mixed_low_flow", "arrival_context": "shock after trauma", "symptom_focus": "dizziness"},
        ]
        for invalid in invalid_responses:
            with self.subTest(response=invalid):
                result = self.compose(client=SimpleNamespace(responses=FakeResponses(invalid)))
                self.assertEqual(result["source"], "fallback")
                self.assertEqual(result["spec"]["choices"], expected["spec"]["choices"])
                self.assertEqual(result["state"]["hidden"], expected["state"]["hidden"])
                self.assertEqual(result["spec"]["provenance"]["fallback_reason"], "invalid_or_incomplete_response")

    def test_incomplete_and_refused_outputs_are_not_accepted(self):
        refusal = [SimpleNamespace(content=[SimpleNamespace(type="refusal")])]
        for responses in (FakeResponses(status="incomplete"), FakeResponses(output=refusal)):
            result = self.compose(client=SimpleNamespace(responses=responses))
            self.assertEqual(result["source"], "fallback")
            self.assertIsNotNone(result["warning"])

    def test_provider_exception_never_echoes_secrets(self):
        responses = FakeResponses(error=TimeoutError("api-secret-value and private request"))
        result = self.compose(client=SimpleNamespace(responses=responses), api_key="api-secret-value")
        serialized = json.dumps(result)
        self.assertNotIn("api-secret-value", serialized)
        self.assertNotIn("private request", serialized)
        self.assertEqual(result["spec"]["provenance"]["fallback_reason"], "provider_unavailable")

    def test_faculty_profile_is_enforced_even_when_model_ignores_it(self):
        responses = FakeResponses()
        result = self.compose(client=SimpleNamespace(responses=responses), profile_id="volume_limited")
        self.assertEqual(result["spec"]["profile_id"], "volume_limited")
        self.assertNotEqual(result["source"], "ai")
        enum = responses.calls[0]["text"]["format"]["schema"]["properties"]["profile_id"]["enum"]
        self.assertEqual(enum, ["volume_limited"])

    def test_unsupported_challenges_and_nonfresh_states_fail_explicitly(self):
        for challenge in ("R3-10", "unknown"):
            with self.assertRaises(ValueError):
                generator.generate_encounter(challenge, self.base)
        used = deepcopy(self.base)
        used["sim_time"] = 1
        with self.assertRaises(ValueError):
            generator.generate_encounter("R1-03", used)
        for seed in (-1, 2**31, True, "17"):
            with self.assertRaises(ValueError):
                generator.generate_encounter("R1-03", self.base, seed=seed)


if __name__ == "__main__":
    unittest.main()
