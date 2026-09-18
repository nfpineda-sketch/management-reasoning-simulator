"""Integrity gates for the authored multi-family clinical source bank."""
import json
import unittest

from clinical_cases import FAMILIES, INVESTIGATION_IDS, variant_by_id
from ecg12 import RHYTHMS
from visual_observations import visual_observations


CASES = [(family, case) for family, entry in FAMILIES.items() for case in entry["variants"]]


class ClinicalCaseBankTests(unittest.TestCase):
    def test_eight_clinical_families_have_distinct_complete_variants(self):
        self.assertEqual(set(FAMILIES), {
            "pneumonia", "pulmonary_edema", "acs", "pulmonary_embolism",
            "asthma", "gi_bleed", "hypoglycemia", "opioid",
        })
        identifiers = [case["id"] for _, case in CASES]
        self.assertEqual(len(identifiers), 16)
        self.assertEqual(len(set(identifiers)), 16)
        for family, entry in FAMILIES.items():
            with self.subTest(family=family):
                self.assertEqual(len(entry["variants"]), 2)
                first, second = entry["variants"]
                self.assertNotEqual(first["patient"], second["patient"])
                self.assertNotEqual(first["history"], second["history"])
                self.assertNotEqual(first["presentation"], second["presentation"])
                self.assertNotEqual(first["observable"], second["observable"])
        # This is not a renamed family of 70-year-old AF patients.
        self.assertGreaterEqual(len({case["patient"]["age_years"] for _, case in CASES}), 12)
        self.assertEqual({case["patient"]["sex"] for _, case in CASES}, {"male", "female"})
        self.assertTrue(all("atrial fibrillation" not in case["observable"]["rhythm"].lower()
                            for _, case in CASES))

    def test_bank_is_serializable_and_cases_have_complete_source_contract(self):
        json.dumps(FAMILIES, allow_nan=False)
        required = {"id", "patient", "presentation", "history", "history_source",
                    "examination", "observable", "ecg_profile", "investigations",
                    "visual_profile", "engine", "faculty"}
        required_history = {"chief_complaint", "associated_symptoms", "medical_history",
                            "medications", "allergies", "onset", "risk_factors"}
        for family, case in CASES:
            with self.subTest(case=case["id"]):
                self.assertTrue(required.issubset(case))
                self.assertEqual(case["engine"]["family"], family)
                self.assertTrue(required_history.issubset(case["history"]))
                self.assertLessEqual(len(case["presentation"].split()), 70)
                self.assertLessEqual(len(case["history"]["chief_complaint"]), 2)
                for sentences in case["history"].values():
                    self.assertIsInstance(sentences, list)
                    self.assertTrue(sentences)
                    self.assertTrue(all(isinstance(s, str) and s.strip() for s in sentences))
                self.assertTrue({"Cardiac", "Respiratory", "Abdomen", "Neurological"}.issubset(case["examination"]))
                self.assertTrue(case["faculty"]["discriminating_findings"])
                self.assertTrue(case["faculty"]["sources"])
                self.assertTrue(all(url.startswith("https://") for url in case["faculty"]["sources"]))

    def test_initial_vitals_and_diagnostic_samples_agree(self):
        required = {"sbp", "dbp", "hr", "spo2", "respiratory_rate", "work_of_breathing",
                    "crt", "extremities", "mental_status", "rhythm", "pulse_present",
                    "temperature_c", "glucose_mg_dl", "peripheral_perfusion"}
        for _, case in CASES:
            with self.subTest(case=case["id"]):
                o, studies = case["observable"], case["investigations"]
                self.assertTrue(required.issubset(o))
                self.assertGreater(o["sbp"], o["dbp"])
                self.assertGreater(o["hr"], 0)
                self.assertTrue(o["pulse_present"])
                self.assertIn(o["rhythm"].lower(), RHYTHMS)
                self.assertGreaterEqual(o["spo2"], 0)
                self.assertLessEqual(o["spo2"], 100)
                self.assertEqual(o["glucose_mg_dl"], studies["poc_glucose"]["result"]["glucose_mg_dl"])
                self.assertEqual(o["glucose_mg_dl"], studies["basic_labs"]["result"]["glucose_mg_dl"])
                self.assertEqual(o["temperature_c"], studies["temperature"]["result"]["temperature_c"])
                self.assertEqual(studies["hemoglobin"]["result"]["hemoglobin_g_dl"],
                                 studies["basic_labs"]["result"]["hemoglobin_g_dl"])
                self.assertEqual(case["engine"]["baseline_lactate"], studies["lactate"]["result"]["lactate_mmol_l"])

    def test_studies_are_bounded_and_unavailable_results_are_not_normal(self):
        for family, case in CASES:
            with self.subTest(case=case["id"]):
                self.assertTrue(set(case["investigations"]).issubset(INVESTIGATION_IDS))
                for study in case["investigations"].values():
                    self.assertIsInstance(study["duration_min"], int)
                    self.assertGreaterEqual(study["duration_min"], 0)
                    self.assertIsInstance(study["result"], dict)
                    self.assertTrue(study["result"])
                if family == "pulmonary_embolism":
                    self.assertIn("ctpa", case["investigations"])
                    self.assertIn("filling defects", case["investigations"]["ctpa"]["result"]["report"])
                else:
                    self.assertNotIn("ctpa", case["investigations"])
                culture = case["investigations"]["blood_cultures"]["result"]["report"].lower()
                self.assertIn("pending", culture)
                self.assertNotIn("positive", culture)

    def test_disease_discriminators_are_consistent_without_forcing_a_diagnosis_in_handover(self):
        for family, case in CASES:
            with self.subTest(case=case["id"]):
                self.assertNotIn(case["faculty"]["diagnosis"].lower(), case["presentation"].lower())
                self.assertNotIn("cognitive bias", case["presentation"].lower())
                o = case["observable"]
                if family == "hypoglycemia":
                    self.assertLess(o["glucose_mg_dl"], 54)
                    self.assertIn(o["mental_status"], {"Drowsy", "Obtunded"})
                    self.assertEqual(o["peripheral_perfusion"], "preserved")
                if family == "opioid":
                    self.assertLessEqual(o["respiratory_rate"], 8)
                    self.assertEqual(o["work_of_breathing"], "Reduced")
                    self.assertGreater(case["investigations"]["abg"]["result"]["paco2_mm_hg"], 50)
                if family == "gi_bleed":
                    self.assertLess(case["engine"]["baseline_hemoglobin"], 7)
                    self.assertGreaterEqual(o["spo2"], 96)
                if family == "acs":
                    self.assertIn(case["ecg_profile"], {"st_elevation_inferior", "st_depression"})
                    self.assertGreater(case["investigations"]["troponin"]["result"]["value_ng_l"], 19)
                if family == "pneumonia":
                    self.assertIn("consolidation", json.dumps(case["investigations"]["pocus"]).lower())
                if family == "pulmonary_edema":
                    self.assertIn("diffuse bilateral b-lines", json.dumps(case["investigations"]["pocus"]).lower())

    def test_reduced_consciousness_has_an_explicit_collateral_source(self):
        for _, case in CASES:
            if case["observable"]["mental_status"] != "Alert":
                with self.subTest(case=case["id"]):
                    self.assertNotEqual(case["history_source"], "Patient")
                    self.assertTrue(case["history"]["chief_complaint"][0].startswith(("His ", "Her ")))

    def test_visual_contract_matches_authored_initial_state(self):
        for family, case in CASES:
            with self.subTest(case=case["id"]):
                visible = visual_observations({"observable": case["observable"],
                    "encounter_spec": {"visual_profile": case["visual_profile"]}})
                self.assertEqual(visible["mental_status"], case["observable"]["mental_status"].lower())
                self.assertNotEqual(visible["skin_color"], "not recorded")
                self.assertNotEqual(visible["expression"], "neutral")
                if family == "opioid":
                    self.assertEqual(visible["expression"], "passive")
                if case["observable"]["peripheral_perfusion"] == "impaired":
                    self.assertIn(visible["skin_color"], {"mild pallor", "pallor"})
                if family == "hypoglycemia":
                    self.assertIn(visible["diaphoresis"], {"mild", "marked"})

    def test_variant_lookup_returns_an_isolated_frozen_source(self):
        identifier = CASES[0][1]["id"]
        first = variant_by_id(identifier)
        first["history"]["chief_complaint"].append("tampered")
        first["observable"]["hr"] = 0
        second = variant_by_id(identifier)
        self.assertNotIn("tampered", second["history"]["chief_complaint"])
        self.assertGreater(second["observable"]["hr"], 0)
        with self.assertRaises(KeyError):
            variant_by_id("not_a_case")


if __name__ == "__main__":
    unittest.main()
