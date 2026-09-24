"""Coverage and formative-assignment contracts for the cognitive catalog."""

from copy import deepcopy
import unittest

from cognitive_catalog import BIAS_CHALLENGES, BIAS_CONTEXTS, FAMILY_LABELS, EVIDENCE_INTERPRETATION
from curriculum import CHALLENGES, assign_challenge, eligible_challenges, evidence_summary


class CognitiveCatalogTests(unittest.TestCase):
    def test_initial_assignment_prioritizes_new_families_before_foundations(self):
        self.assertIn(next(iter(CHALLENGES)), BIAS_CHALLENGES)
        for year in (1, 2, 3):
            eligible_biases = {key for key in eligible_challenges(year) if key in BIAS_CHALLENGES}
            for seed in range(30):
                self.assertIn(assign_challenge(year, [], seed)["challenge_id"], eligible_biases)
            completed_biases = [{"challenge_id": key, "status": "completed", "is_sandbox": False,
                                "updated_at": f"2026-09-{index + 1:02d}", "payload": {}}
                               for index, key in enumerate(sorted(eligible_biases))]
            foundations = set(eligible_challenges(year)) - eligible_biases
            self.assertTrue(foundations)
            for seed in range(10):
                result = assign_challenge(year, completed_biases, seed)
                self.assertIn(result["challenge_id"], foundations)
                self.assertEqual(result["reason"], "initial_exposure")

    def test_distinct_biases_cover_multiple_real_clinical_families(self):
        self.assertEqual(len(BIAS_CHALLENGES), 8)
        self.assertEqual(len({c["bias_id"] for c in BIAS_CHALLENGES.values()}), 8)
        # Eleven since 2026-09-23: anaphylaxis, the flank-pain pair and the
        # unstable bradycardia. Every family is still covered by a challenge,
        # which is the property below and the one that matters.
        self.assertEqual(len(FAMILY_LABELS), 12)
        covered = set()
        for challenge in BIAS_CHALLENGES.values():
            with self.subTest(bias=challenge["bias_id"]):
                families = challenge["families"]
                self.assertGreaterEqual(len(set(families)), 2)
                self.assertEqual(len(families), len(set(families)))
                self.assertTrue(set(families) <= set(FAMILY_LABELS))
                self.assertNotIn("PS001", families)
                self.assertNotIn("PS002", families)
                covered.update(families)
        self.assertEqual(covered, set(FAMILY_LABELS))

    def test_formative_metadata_integrates_with_existing_evidence_fields(self):
        existing_fields = set(evidence_summary({})["recorded"])
        self.assertEqual(len(CHALLENGES), 11)
        self.assertTrue({"R1-03", "R1-04", "R2-01"} <= set(CHALLENGES))
        for key, challenge in BIAS_CHALLENGES.items():
            with self.subTest(challenge=key):
                self.assertEqual(CHALLENGES[key], challenge)
                self.assertTrue(set(challenge["evidence_fields"]) <= existing_fields)
                self.assertGreaterEqual(len(challenge["debrief_questions"]), 2)
                self.assertTrue(all(q.endswith("?") for q in challenge["debrief_questions"]))
                self.assertIn("MK2", challenge["acgme"])
                self.assertTrue(challenge["royal_college"])
                self.assertTrue(challenge["competency_mapping"])
                self.assertNotIn(challenge["bias_id"].replace("_", " "), challenge["title"].lower())
                self.assertNotIn("bias", challenge["title"].lower())

    def test_full_first_exposure_cycle_reaches_each_eligible_challenge(self):
        for year in (1, 2, 3):
            records = []
            expected = set(eligible_challenges(year))
            encountered = set()
            for position in range(len(expected)):
                assignment = assign_challenge(year, records, seed=30 + position)
                key = assignment["challenge_id"]
                self.assertNotIn(key, encountered)
                self.assertLessEqual(CHALLENGES[key]["year"], year)
                self.assertEqual(assignment["reason"], "initial_exposure")
                encountered.add(key)
                records.append({
                    "challenge_id": key, "status": "completed", "is_sandbox": False,
                    "updated_at": f"2026-09-{position + 1:02d}", "payload": {},
                })
            self.assertEqual(encountered, expected)
            next_assignment = assign_challenge(year, records, seed=40)
            self.assertNotEqual(next_assignment["challenge_id"], records[-1]["challenge_id"])
            self.assertEqual(next_assignment["reason"], "interleaved_evidence_review")

    def test_assignment_and_evidence_do_not_diagnose_bias_from_outcome(self):
        records = [{
            "challenge_id": key, "status": "completed", "is_sandbox": False,
            "updated_at": f"2026-09-{index + 1:02d}",
            "payload": {"session": {"management_trace": []}},
        } for index, key in enumerate(CHALLENGES)]
        good = deepcopy(records)
        bad = deepcopy(records)
        for record in good:
            record["payload"]["session"]["state"] = {"outcome": "recovered"}
        for record in bad:
            record["payload"]["session"]["state"] = {"outcome": "deteriorated"}
        self.assertEqual(assign_challenge(3, good, 25), assign_challenge(3, bad, 25))
        self.assertEqual(assign_challenge(3, bad, 25)["competence_decision"], "Not assessed automatically")
        self.assertEqual(evidence_summary(good[0]["payload"]), evidence_summary(bad[0]["payload"]))
        self.assertIn("does not establish cognitive bias or competence", EVIDENCE_INTERPRETATION)

    def test_availability_context_is_an_explicit_fictional_exposure(self):
        availability = [c for c in BIAS_CHALLENGES.values() if c["bias_id"] == "availability"]
        self.assertEqual(len(availability), 1)
        context = BIAS_CONTEXTS["availability"]["prime_text"]
        self.assertIn("simulated shift", context)
        self.assertIn("Earlier", context)
        self.assertNotIn("bias", context.lower())
        self.assertNotIn("pulmonary embolism", context.lower())


if __name__ == "__main__":
    unittest.main()
