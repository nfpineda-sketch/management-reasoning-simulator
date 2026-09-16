"""The preview shown to the reviewer must not violate the contract it is given.

Four paid generations of R1-05 were rejected largely for contradictions the
author never wrote. The executor reported extremities the declared enum did not
contain ("Very cold", "Mottled/Cold"), a systolic pressure of 0 at arrest while
trajectory_numeric_bounds declared a minimum of 20, a rhythm canonicalized away
from the authored label, and "Mottled/Cold" extremities with visual.mottling
false. The reviewer was doing its job; the contract was wrong.

No paid calls.
"""
import ast
from pathlib import Path
import unittest

from coupled_encounter import sync_mottling
from generated_case_capabilities import executable_generation_constraints
from generated_case_schema import STATE_TEXT

ROOT = Path(__file__).resolve().parent
ALLOWED_EXTREMITIES = tuple(STATE_TEXT["extremities"]["enum"])


def _assigned_strings(node, found):
    """Only the value itself, including each branch of a conditional."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        found.add(node.value)
    elif isinstance(node, ast.IfExp):
        _assigned_strings(node.body, found)
        _assigned_strings(node.orelse, found)


def extremities_the_core_can_report():
    """Every literal the shared core assigns to observable['extremities']."""
    source = (ROOT / "clinical_physiology.py").read_text()
    found = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if (isinstance(target, ast.Subscript) and isinstance(target.slice, ast.Constant)
                        and target.slice.value == "extremities"):
                    _assigned_strings(node.value, found)
        elif isinstance(node, ast.Call):
            for keyword in node.keywords or []:
                if keyword.arg == "extremities":
                    _assigned_strings(keyword.value, found)
    return found


class TheDeclaredContractMatchesTheExecutor(unittest.TestCase):
    def test_every_extremity_the_core_reports_is_a_declared_value(self):
        reported = extremities_the_core_can_report()
        self.assertTrue(reported, "the extraction found nothing; the core changed shape")
        undeclared = sorted(reported - set(ALLOWED_EXTREMITIES))
        self.assertEqual(undeclared, [], f"the executor reports {undeclared}, the contract does not")

    def test_the_contract_says_arrest_leaves_the_trajectory_bounds(self):
        notes = " ".join(executable_generation_constraints()["contract_notes"]).lower()
        self.assertIn("terminal collapse", notes)
        self.assertIn("pressure read 0", notes)
        self.assertIn("not a bounds violation", notes)

    def test_the_contract_says_which_rhythm_labels_are_canonicalized(self):
        notes = " ".join(executable_generation_constraints()["contract_notes"])
        self.assertIn("canonicalizes", notes)
        self.assertIn("'Sinus rhythm'", notes)
        self.assertIn("'AF'", notes)

    def test_the_canonicalization_note_describes_what_the_engine_does(self):
        """Derived from the engine, not from the note's wording."""
        from copy import deepcopy
        from ecg12 import RHYTHMS
        from generated_case_schema import compile_case
        from coupled_encounter import preview
        from test_generated_case import novel_payload

        for authored, expected in (("sinus tachycardia", "Sinus rhythm"),
                                   ("sinus bradycardia", "Sinus rhythm"),
                                   ("atrial fibrillation", "AF")):
            self.assertIn(authored, RHYTHMS)
            raw = deepcopy(novel_payload())
            raw["observable"]["rhythm"] = authored
            for rule in raw["engine"]["state_rules"]:
                if "rhythm" in rule.get("set", {}):
                    rule["set"]["rhythm"] = authored
            got = preview(compile_case(raw), seed=17)[0]["observable"]["rhythm"]
            self.assertEqual(got, expected, authored)


class MottlingAgreesWithTheReportedExtremities(unittest.TestCase):
    def test_mottled_extremities_set_the_flag(self):
        for extremities in ("Mottled/Cold", "Mottled/cold", "mottled and cold"):
            observable = {"extremities": extremities, "visual": {"mottling": False}}
            self.assertTrue(sync_mottling(observable)["visual"]["mottling"], extremities)

    def test_unmottled_extremities_never_invent_it(self):
        for extremities in ("Warm", "Cool", "Cold", "Very cold"):
            observable = {"extremities": extremities, "visual": {"mottling": False}}
            self.assertFalse(sync_mottling(observable)["visual"]["mottling"], extremities)

    def test_mottling_already_recorded_is_not_erased(self):
        observable = {"extremities": "Cool", "visual": {"mottling": True}}
        self.assertTrue(sync_mottling(observable)["visual"]["mottling"])

    def test_a_missing_visual_block_is_created_rather_than_crashing(self):
        self.assertTrue(sync_mottling({"extremities": "Mottled/Cold"})["visual"]["mottling"])

    def test_the_preview_never_contradicts_itself_through_collapse(self):
        from copy import deepcopy
        from generated_case_schema import compile_case
        from coupled_encounter import preview
        from test_generated_case import novel_payload

        case = compile_case(deepcopy(novel_payload()))
        for frame in preview(case, seed=17):
            observable = frame["observable"]
            if "mottled" in str(observable.get("extremities", "")).lower():
                self.assertTrue(observable["visual"]["mottling"], frame["time_min"])


if __name__ == "__main__":
    unittest.main()
