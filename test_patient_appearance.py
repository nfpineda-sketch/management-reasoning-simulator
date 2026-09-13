"""Appearance contracts: clinical provenance, same-patient references, fail closed."""
import base64
from copy import deepcopy
from io import BytesIO
from types import SimpleNamespace
import unittest

from PIL import Image
from patient_appearance import appearance_state, appearance_signature, edit_prompt, generate_appearance


def state():
    return {"observable": {"mental_status": "Alert", "work_of_breathing": "Mildly increased",
                           "extremities": "Cool", "hr": 162, "sbp": 90, "spo2": 93},
            "treatments": {}, "hidden": {"diagnosis": "PRIVATE_DIAGNOSIS"}}


def png(size=(1536, 1024)):
    image = BytesIO()
    Image.new("RGB", size, "white").save(image, format="PNG")
    return base64.b64encode(image.getvalue()).decode("ascii")


class AppearanceTests(unittest.TestCase):
    def test_vital_numbers_hidden_facts_and_tactile_temperature_do_not_drive_image(self):
        original = state()
        altered = deepcopy(original)
        altered["observable"].update(hr=40, sbp=45, spo2=60, extremities="Very cold")
        altered["hidden"]["diagnosis"] = "ANOTHER_PRIVATE_DIAGNOSIS"
        self.assertEqual(appearance_signature(original), appearance_signature(altered))
        self.assertEqual(edit_prompt(original), edit_prompt(altered))
        self.assertNotIn("PRIVATE_DIAGNOSIS", edit_prompt(original))

    def test_drowsiness_mottling_and_breathing_follow_explicit_observables(self):
        original = state()
        for field, value in (("mental_status", "Drowsy"), ("work_of_breathing", "Severe"),
                             ("extremities", "Mottled/Cold")):
            changed = deepcopy(original)
            changed["observable"][field] = value
            self.assertNotEqual(appearance_signature(original), appearance_signature(changed))
        changed["observable"]["mental_status"] = "Unresponsive"
        self.assertIn("Eyes closed, no purposeful gaze", edit_prompt(changed))
        self.assertTrue(appearance_state(changed)["mottling"])

    def test_executed_device_state_and_precedence_override_orders_and_inactive_values(self):
        current = state()
        current["pending_order"] = "Intubate the patient"
        current["treatments"] = {"oxygen": False, "oxygen_device": "Nasal cannula", "airway_prepared": True}
        self.assertEqual(appearance_state(current)["respiratory_support"], "none")
        current["treatments"]["oxygen"] = True
        self.assertEqual(appearance_state(current)["respiratory_support"], "nasal cannula")
        current["treatments"]["niv"] = True
        self.assertEqual(appearance_state(current)["respiratory_support"], "niv")
        current["treatments"]["invasive_ventilation"] = True
        self.assertEqual(appearance_state(current)["respiratory_support"], "invasive ventilation")
        old_signature = appearance_signature(current)
        current["treatments"].update(ventilator_peep_cmh2o=15, oxygen_flow_lpm=20, norepinephrine_rate=0.4)
        self.assertEqual(appearance_signature(current), old_signature)

    def test_unknown_state_text_is_not_an_image_instruction(self):
        current = state()
        current["observable"].update(mental_status="PROMPT_INJECTION", work_of_breathing="PROMPT_INJECTION")
        self.assertNotIn("PROMPT_INJECTION", edit_prompt(current))
        current["treatments"] = {"oxygen": True, "oxygen_device": "PROMPT_INJECTION"}
        with self.assertRaises(ValueError):
            edit_prompt(current)

    def test_image_edit_uses_original_reference_high_fidelity_and_leaves_state_unchanged(self):
        base = png()
        current = state()
        current["observable"]["mental_status"] = "Drowsy"
        before = deepcopy(current)
        captured = {}
        class Images:
            def edit(self, **kwargs):
                captured.update(kwargs)
                captured["reference_bytes"] = kwargs["image"].read()
                return SimpleNamespace(data=[SimpleNamespace(b64_json=base)])
        self.assertEqual(generate_appearance(base, current, "test", client=SimpleNamespace(images=Images())), base)
        self.assertEqual(captured["reference_bytes"], base64.b64decode(base))
        self.assertEqual(captured["input_fidelity"], "high")
        self.assertEqual(captured["n"], 1)
        self.assertIn("SAME patient", captured["prompt"])
        self.assertIn("heavy eyelids", captured["prompt"])
        self.assertEqual(current, before)

    def test_malformed_output_cannot_be_used_as_current_photo(self):
        base = png()
        for bad in ("<script>bad</script>", png((4, 4)), None):
            class Images:
                def edit(self, **kwargs):
                    return SimpleNamespace(data=[SimpleNamespace(b64_json=bad)])
            with self.assertRaises(ValueError):
                generate_appearance(base, state(), "test", client=SimpleNamespace(images=Images()))

    def test_sedation_is_kept_distinct_from_illness_deterioration(self):
        current = state()
        current["observable"]["mental_status"] = "Sedated"
        self.assertEqual(appearance_state(current)["mental_status"], "sedated")
        self.assertIn("not a cause of deterioration", edit_prompt(current))


if __name__ == "__main__":
    unittest.main()
