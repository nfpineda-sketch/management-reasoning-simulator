"""The Spanish drafts of cycle 10 (C10-08, packet R-4): the engine's sentences, decided and active; C14, drafts.

``spanish_drafts`` holds two sets: the engine's sentences a Spanish reader still sees in English
(the rest of DF-23 row 11) and the C14 declarations the Spanish faculty portal shows in English
(TD-07). A draft reaches a reader only after a faculty member approves it and a later, recorded
change moves it into ``language`` or the portal.
"""
import ast
import re
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


def test_every_engine_sentence_is_said_as_the_faculty_approved_it():
    """B-5, IG-5 (2026-10-08): the engine's sentences the faculty decided on 2026-10-07 (packet, block A) are
    active. The room says each one exactly as approved; the C14 drafts still wait."""
    assert spanish_drafts.STATUS == "draft_pending_faculty_review"
    assert spanish_drafts.ENGINE_STATUS == "approved_active"
    assert len(spanish_drafts.ENGINE) == 22
    for row in spanish_drafts.ENGINE:
        assert set(row) >= {"kind", "english", "example", "spanish", "cases", "seen", "note"}, row
        assert harvest.template(row["example"]) == row["english"]
        said = harvest.presented(row["example"], narrative=[], kind=row["kind"])
        numbers = iter(re.findall(r"\d+(?:[.,]\d+)?", row["example"]))
        approved = re.sub(r"\{n\}", lambda _: next(numbers), row["spanish"])
        assert said == approved, (row["english"], said)
        assert not harvest.residue(said), said


def test_every_engine_sentence_has_its_review_reading_and_nothing_else_does():
    # R-4 (2026-09-30): the context, recommendation and ambiguity the faculty reads beside each draft.
    assert set(spanish_drafts.ENGINE_REVIEW) == {row["english"] for row in spanish_drafts.ENGINE}
    for reading in spanish_drafts.ENGINE_REVIEW.values():
        assert len(reading) == 3 and all(isinstance(part, str) and part.strip() for part in reading)
        assert reading[1].startswith(("Aprobar", "Cambiar"))


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
