"""The R-2 notes cover exactly the C14 YES cases and nothing the residents or faculty run reads them.

Faculty decision of 2026-09-30: the arrival POCUS of the 14 C14 YES cases is reviewed clinically, case by
case, before the pilot. ``pocus_review_notes`` holds the AI Advisor's draft reading for that review; the
sheet ``docs/revision/R2_POCUS_C14.md`` joins it to the cases, and no case changes.
"""
import ast
from pathlib import Path

import case_assessment_bank
import pocus_review_notes

ROOT = Path(__file__).resolve().parent
FIELDS = {"application", "interpret", "management", "acep", "issue", "recommendation"}


def test_one_note_for_each_c14_yes_case_and_no_other():
    yes = {case_id for case_id, spec in case_assessment_bank.CASES.items()
           if (spec.get("objectives") or {}).get("C14", {}).get("opportunity") == "yes"}
    assert len(yes) == 14 and set(pocus_review_notes.NOTES) == yes


def test_every_note_is_complete_and_recommends_one_of_the_three():
    assert pocus_review_notes.STATUS == "draft_for_faculty_review"
    for case_id, note in pocus_review_notes.NOTES.items():
        assert set(note) == FIELDS, case_id
        assert all(isinstance(value, str) and value.strip() for value in note.values()), case_id
        assert note["recommendation"] in pocus_review_notes.RECOMMENDATIONS, case_id


def test_only_the_review_sheet_reads_the_notes():
    readers = []
    for path in ROOT.glob("*.py"):
        if path.name.startswith("test_") or path.name == "pocus_review_notes.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names = ([alias.name for alias in node.names] if isinstance(node, ast.Import)
                     else [node.module or ""] if isinstance(node, ast.ImportFrom) else [])
            if "pocus_review_notes" in names:
                readers.append(path.name)
    assert sorted(set(readers)) == ["tools_review_sheets.py"]
