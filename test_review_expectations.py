"""Clinical review must respect stated expectations and frozen decision context."""

from copy import deepcopy
import unittest

from test_curriculum_trajectories import load_engine


def event(expected, actions=("antibiotics",), sbp=112, dbp=72, crt=3):
    before = {
        "case_id": "PS001", "encounter_variant": "rhythm_contributor",
        "sim_time_min": 26,
        "observable": {
            "sbp": sbp, "dbp": dbp, "crt": crt, "hr": 94,
            "rhythm": "Sinus rhythm", "extremities": "Warm",
            "mental_status": "Sedated", "spo2": 93,
            "work_of_breathing": "Mildly increased",
        },
        "treatments": {"norepinephrine_rate": 0},
    }
    after = deepcopy(before)
    after["sim_time_min"] = 31
    after["observable"].update({"sbp": sbp - 4 if sbp else None,
                                "dbp": dbp - 3 if dbp else None,
                                "mental_status": "Alert"})
    return {
        "execution_status": "executed", "decision_time_min": 26,
        "response_time_min": 31, "elapsed_minutes": 5,
        "state_before": before, "state_after": after,
        "interpreted_action": [{"type": action} for action in actions],
        "reasoning": {
            "expected_effect": expected,
            "reassessment_target": "blood pressure, capillary refill, mental status, and oxygenation in 5 minutes",
        },
    }


class ReviewExpectationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = load_engine()

    def prompt(self, record):
        return self.engine["_expected_response_prompt"](record)

    def expert(self, record):
        return self.engine["_trajectory_expert_model"]({"decision": 6}, record)

    def test_reported_antibiotic_expectation_preserves_negation_and_time(self):
        record = event("treatment of the infection to support gradual recovery, without expecting an immediate blood pressure response")
        result = self.prompt(record)
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "Treatment timing and reassessment")
        self.assertNotIn("expected improvements were not demonstrated", result[1])
        self.assertIn("112/72", result[1])
        self.assertIn("108/69", result[1])

    def test_antibiotics_alone_do_not_label_short_term_response_as_efficacy(self):
        for expected in ("improved perfusion", "blood pressure to improve immediately",
                         "recuperación gradual, sin esperar mejoría inmediata de la presión arterial"):
            with self.subTest(expected=expected):
                result = self.prompt(event(expected))
                self.assertEqual(result[0], "Treatment timing and reassessment")

    def test_reassessment_does_not_reintroduce_negated_or_deferred_targets(self):
        for expected in (
            "I do not expect an immediate blood pressure response",
            "I don’t expect an immediate blood pressure response",
            "No immediate hemodynamic improvement is expected",
            "blood pressure will not improve immediately",
            "No espero mejoría inmediata de la presión arterial",
            "improved perfusion over the next several hours",
            "mejoría de la perfusión durante las próximas horas",
            "blood pressure to improve in 20 minutes",
            "improved blood pressure in the next hour",
            "mejoria de la presion arterial en una hora",
            "improved preload, but no immediate blood pressure response",
        ):
            with self.subTest(expected=expected):
                self.assertIsNone(self.prompt(event(expected, ("fluid",))))

    def test_explicit_horizon_can_be_compared_once_observed(self):
        for expected in ("blood pressure to improve in 5 minutes", "presion arterial mejora en 1 hora"):
            record = event(expected, ("fluid",))
            record["elapsed_minutes"] = 60
            self.assertIsNotNone(self.prompt(record))

    def test_compound_antibiotic_and_pressor_keeps_immediate_pressure_target(self):
        for conjunction in (", but", " and"):
            record = event("gradual recovery with antibiotics" + conjunction + " improved blood pressure now with norepinephrine",
                           ("antibiotics", "norepinephrine"), sbp=84, dbp=48, crt=5)
            result = self.prompt(record)
            self.assertEqual(result[0], "Expected effect vs observed response")
            self.assertIn("blood pressure decreased", result[1])

    def test_pressure_preservation_is_not_an_improvement_goal(self):
        record = event("blood pressure to remain stable", ("fluid",))
        self.assertIsNone(self.prompt(record))
        record["state_after"]["observable"]["sbp"] = 85
        result = self.prompt(record)
        self.assertEqual(result[0], "Preservation goal vs observed response")
        self.assertNotIn("expected improvements", result[1])

    def test_preservation_applies_only_to_its_own_endpoint(self):
        record = event("improved blood pressure while preserving oxygenation", ("fluid",))
        result = self.prompt(record)
        self.assertIn("blood pressure decreased", result[1])
        self.assertIn("oxygenation was preserved", result[1].lower())
        self.assertNotIn("oxygen saturation did not improve", result[1])
        record = event("unchanged blood pressure and improved oxygenation", ("oxygen",))
        result = self.prompt(record)
        self.assertIn("oxygen saturation did not improve", result[1])
        self.assertNotIn("blood pressure decreased", result[1])

    def test_negated_pressure_does_not_hide_immediate_oxygen_expectation(self):
        record = event("I do not expect blood pressure to improve, but oxygenation should improve immediately",
                       ("oxygen",))
        result = self.prompt(record)
        self.assertIsNotNone(result)
        self.assertIn("oxygen saturation did not improve", result[1])
        self.assertNotIn("blood pressure", result[1].split("Those expected improvements")[1])

    def test_spanish_immediate_effect_is_compared(self):
        record = event("mejoría inmediata de la presión arterial y del relleno capilar", ("fluid",))
        result = self.prompt(record)
        self.assertIsNotNone(result)
        self.assertIn("blood pressure decreased", result[1])

    def test_immediate_fluid_failure_and_mixed_response_remain_reviewable(self):
        record = event("improved blood pressure and capillary refill", ("fluid",))
        self.assertIn("capillary refill did not improve", self.prompt(record)[1])
        record["state_after"]["observable"]["sbp"] = 126
        self.assertEqual(self.prompt(record)[0], "Mixed response")

    def test_preservation_failure_survives_excluded_improvement(self):
        record = event("I do not expect blood pressure to improve", ("fluid",))
        record["reasoning"]["preservation_goal"] = "preserve oxygenation"
        record["state_after"]["observable"]["spo2"] = 88
        result = self.prompt(record)
        self.assertIsNotNone(result)
        self.assertIn("oxygenation also worsened", result[1].lower())
        self.assertNotIn("expected improvements", result[1])

    def test_antibiotic_with_adequate_map_does_not_recommend_pressor_escalation(self):
        model = self.expert(event("gradual recovery"))
        self.assertNotIn("Start or titrate norepinephrine", model["action"])
        self.assertIn("112/72", " ".join(model["cues"]))
        self.assertIn("antimicrobial", model["action"])

    def test_high_map_with_poor_perfusion_is_not_automatic_pressure_indication(self):
        record = event("improved perfusion", ("norepinephrine",), crt=6)
        record["state_before"]["observable"]["mental_status"] = "Drowsy"
        model = self.expert(record)
        self.assertNotIn("Start or titrate norepinephrine", model["action"])
        self.assertIn("perfusion", model["action"])
        self.assertNotIn("antimicrobial", model["action"])

    def test_low_map_retains_pressure_support(self):
        record = event("improved blood pressure", ("antibiotics", "norepinephrine"), sbp=84, dbp=48, crt=5)
        model = self.expert(record)
        self.assertIn("Start or titrate norepinephrine", model["action"])
        self.assertIn("antimicrobial", model["action"])

    def test_existing_pressor_at_target_is_not_automatically_escalated_or_stopped(self):
        record = event("gradual recovery")
        record["state_before"]["treatments"]["norepinephrine_rate"] = 0.05
        model = self.expert(record)
        self.assertNotIn("Start or titrate norepinephrine", model["action"])
        self.assertIn("ongoing pressure support", model["action"])

    def test_missing_bp_is_unknown_not_hypotension(self):
        record = event("gradual recovery", sbp=None, dbp=None)
        model = self.expert(record)
        self.assertNotIn("Start or titrate norepinephrine", model["action"])
        self.assertIn("unavailable", " ".join(model["cues"]))

    def test_expert_uses_frozen_predecision_state_not_later_pressure(self):
        record = event("gradual recovery")
        record["state_after"]["observable"].update({"sbp": 70, "dbp": 35})
        self.assertNotIn("Start or titrate norepinephrine", self.expert(record)["action"])


if __name__ == "__main__":
    unittest.main()
