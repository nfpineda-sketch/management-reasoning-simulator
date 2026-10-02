"""D-4, D-5 and D-6 (faculty, 2026-10-02): what the room says when a PE thrombolytic is given.

D-4: the note names the whole criterion -- a systolic below 90 mmHg, or a vasopressor
needed to reach it, with signs of hypoperfusion -- and says that shock indicates it as
soon as it is present: the fifteen minutes belong to a hypotension without those signs,
as the engine's rule (``pe_obstruction.basis``) does.
D-5: in Spanish «administrada», «Trombólisis» with its accent, the drug's Spanish name,
and the bleeding note, which had none. D-6: row 18 keeps its verb.
"""
import re
from pathlib import Path

import language
import pe_obstruction
import spanish_drafts


def given(basis_minutes, *, sbp=84, crt=4.0, lactate=4.0, altered=True, dose_mg=100.0, earlier=None):
    f = {"elapsed": 30, "sustained_hypotension_min": basis_minutes}
    if earlier is not None:
        f.update(earlier)
    current = pe_obstruction.assessment(sbp, crt, lactate, altered)
    note, record = pe_obstruction.give_thrombolysis(f, 30, current, agent="alteplase", dose_mg=dose_mg)
    return note, record


def test_shock_is_named_whole_and_never_waits_fifteen_minutes():
    note, record = given(0)
    assert record["basis"] == "obstructive_shock"
    assert note.startswith(
        "Systemic thrombolysis given in obstructive shock: systolic below 90 mmHg, or a vasopressor needed to reach "
        "90 mmHg, with signs of hypoperfusion. In shock it is indicated as soon as the shock is present; the 15 "
        "consecutive minutes apply only to a hypotension without those signs. ")
    assert note.endswith(pe_obstruction.ACTS)


def test_a_hypotension_without_signs_needs_its_fifteen_minutes():
    note, record = given(15, sbp=84, crt=2.0, lactate=1.5, altered=False)
    assert record["basis"] == "persistent_hypotension"
    assert note == pe_obstruction.SUSTAINED_NOTE + pe_obstruction.ACTS
    assert "a vasopressor needed to keep it at 90 mmHg or above, for 15 consecutive minutes" in note
    early, record = given(14, sbp=84, crt=2.0, lactate=1.5, altered=False)
    assert record["basis"] is None and "without the hemodynamic indication" in early


def test_the_notes_in_spanish_say_administrada_and_the_whole_criterion():
    shock, _ = given(0)
    sustained, _ = given(15, sbp=84, crt=2.0, lactate=1.5, altered=False)
    unindicated, _ = given(0, sbp=110, crt=2.0, lactate=1.5, altered=False)
    assert language.say(shock, "es").startswith(
        "Trombólisis sistémica administrada en shock obstructivo: sistólica bajo 90 mmHg, o un vasopresor necesario "
        "para llegar a 90 mmHg, con signos de hipoperfusión. En shock está indicada desde que el shock está presente; "
        "los 15 minutos consecutivos aplican sólo a una hipotensión sin esos signos.")
    assert language.say(sustained, "es").startswith(
        "Trombólisis sistémica administrada por hipotensión sostenida: sistólica bajo 90 mmHg, o un vasopresor "
        "necesario para mantenerla en 90 mmHg o más, durante 15 minutos consecutivos.")
    assert language.say(unindicated, "es").startswith("Trombólisis sistémica administrada sin la indicación hemodinámica")
    for note in (shock, sustained, unindicated):
        assert not re.search(r"\b(?:given|thrombolysis|drug|clot)\b", language.say(note, "es"))


def doses(*amounts):
    """The notes of successive alteplase doses, as the engine records them on one patient."""
    f = {"elapsed": 0, "sustained_hypotension_min": 0}
    current = pe_obstruction.assessment(84, 4.0, 4.0, True)
    notes = []
    for minute, amount in amounts:
        f["elapsed"] = minute
        notes.append(pe_obstruction.give_thrombolysis(f, minute, current, agent="alteplase", dose_mg=amount))
    return notes


def test_the_regimen_and_the_second_course_name_the_drug_in_spanish():
    _, (regimen, record) = doses((0, 50.0), (30, 50.0))
    assert record["course"] == "initial_regimen"
    assert language.say(regimen, "es").startswith("Se registran 50 mg de alteplasa como parte del esquema inicial")
    _, (second, record) = doses((0, 100.0), (30, 100.0))
    assert record["course"] == "second_course"
    assert "(alteplasa 100 mg)" in language.say(second, "es")
    assert "trombólisis sistémica" in language.say(second, "es")


def test_the_bleeding_note_has_its_spanish():
    note = ("Bleeding from the surgical site operated on twelve days ago: the haemoglobin is falling. This is the risk "
            "the thrombolytic carries, and it was taken in a patient who had a reason to bleed.")
    assert language.say(note, "es") == (
        "Sangrado del sitio operado hace doce días: la hemoglobina está bajando. Es el riesgo que conlleva el "
        "trombolítico, y se asumió en una persona que tenía un motivo para sangrar.")


def test_the_room_never_writes_trombolisis_without_its_accent():
    assert "rombolisis" not in Path("language.py").read_text(encoding="utf-8")


def test_row_18_keeps_its_verb_in_the_room_and_in_the_draft():
    said = language.say("Dextrose 10% runs at 100 mL/h through the cannula in the left forearm.", "es")
    assert said == "El suero glucosado al 10 % pasa a 100 mL/h por la cánula del antebrazo izquierdo."
    row = next(r for r in spanish_drafts.ENGINE if r["english"].startswith("Dextrose {n}% runs"))
    assert row["spanish"] == "El suero glucosado al {n} % pasa a {n} mL/h por la cánula del antebrazo izquierdo."
