"""The Spanish drafts of cycle 10 wait for the faculty and none of them is shown (C10-08, packet R-4).

``spanish_drafts`` holds two sets: the engine's sentences a Spanish reader still sees in English
(the rest of DF-23 row 11) and the C14 declarations the Spanish faculty portal shows in English
(TD-07). A draft reaches a reader only after a faculty member approves it and a later, recorded
change moves it into ``language`` or the portal.
"""
import ast
from pathlib import Path

import language
import spanish_drafts
import tools_engine_spanish as harvest

ROOT = Path(__file__).resolve().parent
#: Where the drafts may be read: the draft module itself, the sheet that shows them to the faculty,
#: and the tests.
READERS = {"spanish_drafts.py", "tools_review_sheets.py"}


def _imports_drafts(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        names = ([alias.name for alias in node.names] if isinstance(node, ast.Import)
                 else [node.module or ""] if isinstance(node, ast.ImportFrom) else [])
        if "spanish_drafts" in names:
            return True
    return False


def test_nothing_the_residents_or_the_faculty_run_reads_the_drafts():
    readers = sorted(path.name for path in ROOT.glob("*.py")
                     if not path.name.startswith("test_") and _imports_drafts(path))
    assert set(readers) <= READERS, readers


def test_every_c14_text_of_the_bank_has_one_draft_and_no_draft_is_stale():
    texts = spanish_drafts.c14_texts()
    assert set(texts) == set(spanish_drafts.C14)
    assert all(spanish_drafts.C14[english].strip() and spanish_drafts.C14[english] != english for english in texts)


def test_the_c14_drafts_are_not_what_the_portal_says():
    # The portal passes the declaration through as it is: English, until an approval changes that.
    for english, draft in spanish_drafts.C14.items():
        assert language.say(english, "es") != draft


def test_every_engine_draft_answers_a_sentence_that_still_shows_english():
    assert spanish_drafts.STATUS == "draft_pending_faculty_review"
    assert spanish_drafts.ENGINE
    for row in spanish_drafts.ENGINE:
        assert set(row) >= {"kind", "english", "example", "spanish", "cases", "seen", "note"}, row
        # Still English as the room presents it today: the draft is neither active nor made
        # unnecessary by another change.
        said = harvest.presented(row["example"], kind=row["kind"])
        assert harvest.still_english(said, row["example"]), row["english"]
        assert harvest.template(row["example"]) == row["english"]
        assert not harvest.residue(row["spanish"].replace("{n}", "0")), row["spanish"]


def test_the_residue_check_sees_english_and_leaves_quotes_alone():
    assert harvest.residue("The anterior wall and apex show mildly reducido contraction") == [
        "The", "and", "contraction", "mildly", "show", "wall"]
    assert harvest.residue("Registrado como indicación al paciente: «vuelva if it hurts».") == []
    assert harvest.residue("Presión arterial 90/60 mmHg, FC 110 lpm, SpO2 94 %.") == []
    assert harvest.template("Glucose 34 mg/dL at minute 12: «repeat it»") == "Glucose {n} mg/dL at minute {n}: «…»"
    # A sentence of content words only is still English when the room leaves it as it was.
    assert harvest.still_english("Respiratory rate 6 /min; breaths remain shallow.",
                                 "Respiratory rate 6 /min; breaths remain shallow.")
    assert not harvest.still_english("Frecuencia respiratoria 6/min.", "Respiratory rate 6 /min.")


def test_the_room_kinds_are_read_from_the_page():
    translated, told = harvest.room_kinds()
    assert "diagnostic_result" in translated and "presentation" in told and "examination" in told
