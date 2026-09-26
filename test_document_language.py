"""An encounter's documents are written in the language it was played in.

Faculty, 2026-09-26: "if the encounter is run in Spanish, the PDFs are
generated in Spanish; if it is run in English, in English. Whatever the app
stores can be seen in either." The encounter records its language when it
closes; each document is written in it unless its reader chooses the other;
an encounter that closed before recorded none, and keeps following its
reader's choice -- it is never guessed.
"""
from io import BytesIO

import pytest
from pypdf import PdfReader

import curriculum_runtime
import document_language
import language


def text_of(blob):
    return " ".join(" ".join(page.extract_text() or "" for page in PdfReader(BytesIO(blob)).pages).split())


@pytest.fixture(autouse=True)
def english_reader(monkeypatch):
    monkeypatch.delenv("MRS_LANGUAGE", raising=False)


def test_a_document_has_its_own_language_and_the_session_keeps_its_own():
    assert language.current() == "en"
    with language.presenting("es"):
        assert language.current() == "es"
        with language.presenting("en"):
            assert language.current() == "en"
        assert language.current() == "es"
    assert language.current() == "en"
    # An unknown or empty choice changes nothing.
    for code in ("fr", "", None):
        with language.presenting(code):
            assert language.current() == "en"


def test_the_language_is_read_from_the_record_and_never_guessed(monkeypatch):
    assert document_language.recorded({"encounter_language": "es"}) == "es"
    assert document_language.recorded({"encounter_language": "fr"}) is None
    assert document_language.recorded({}) is None and document_language.recorded(None) is None
    assert document_language.of_record({"payload": {"session": {"encounter_language": "en"}}}) == "en"
    assert document_language.of_record({"payload": None}) is None
    # Nothing recorded: the reader's language, whichever it is.
    monkeypatch.setenv("MRS_LANGUAGE", "es")
    assert document_language.default({}) == "es"
    assert document_language.default({"encounter_language": "en"}) == "en"


def test_the_language_travels_with_the_saved_session():
    assert document_language.FIELD in curriculum_runtime.SESSION_FIELDS


def test_an_encounter_records_the_language_it_closes_in(monkeypatch):
    from test_curriculum_trajectories import initialize, load_engine
    engine = load_engine()
    session = initialize(engine, engine["INITIAL_STATE"])
    assert "encounter_language" not in session
    monkeypatch.setenv("MRS_LANGUAGE", "es")
    engine["begin_decision_review"]([], session["state"])
    assert session["encounter_ended"] is True and session["encounter_language"] == "es"


def test_the_encounter_page_records_the_language_it_was_played_in_and_saves_it(tmp_path, monkeypatch):
    from test_doses_by_solution_and_by_weight import ANTICOAGULATE, start, submit, widget
    at = start(tmp_path, monkeypatch, "pulmonary_embolism_33f", "R2-02")
    at.session_state["presentation_language"] = "es"
    at.run()
    submit(at, ANTICOAGULATE)
    submit(at, "Creo que es un tromboembolismo pulmonar. Mi prioridad es un destino monitorizado. "
               "La hospitalizo en UCI. Espero que se mantenga estable. Reevaluo en 15 minutos PA y saturacion.")
    widget(at.button, "Complete Encounter & Begin Review").click().run()
    assert not at.exception
    assert at.session_state["encounter_ended"] is True
    assert at.session_state["encounter_language"] == "es"
    from account_store import AccountStore
    import os
    accounts = AccountStore(os.environ["MRS_DATABASE_URL"], allow_sqlite=True)
    with accounts._transaction() as connection:
        row = accounts._execute(connection, "SELECT payload_json FROM mrs_attempts").fetchone()
    import json
    assert json.loads(row["payload_json"])["session"]["encounter_language"] == "es"


def test_a_new_encounter_does_not_inherit_the_last_one_s_language():
    # Every place that opens an encounter clears it, so the next one records its own.
    import ast
    from pathlib import Path
    tree = ast.parse((Path(__file__).with_name("app.py")).read_text(encoding="utf-8"))
    opened = cleared = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.Module)):
            body = ast.unparse(node) if isinstance(node, ast.FunctionDef) else ""
            if "st.session_state.encounter_ended = False" in body:
                opened += 1
                cleared += "st.session_state.pop('encounter_language', None)" in body
    assert opened >= 2 and cleared == opened


# --- each document, in the language it is given -------------------------------

def test_the_management_trace_is_written_in_the_language_it_is_given(monkeypatch):
    from management_trace_report import render_management_trace_pdf
    from test_management_trace_analysis import sample_payload, sample_report
    payload = sample_payload()
    report = sample_report(payload)
    assert "What to carry forward" in text_of(render_management_trace_pdf(report, payload, language="en"))
    assert "Qué llevarse de aquí" in text_of(render_management_trace_pdf(report, payload, language="es"))
    # A Spanish reader can still have an English encounter's document in English,
    # and without a choice the reader's language stands, as before.
    monkeypatch.setenv("MRS_LANGUAGE", "es")
    assert "What to carry forward" in text_of(render_management_trace_pdf(report, payload, language="en"))
    assert "Qué llevarse de aquí" in text_of(render_management_trace_pdf(report, payload))
    assert language.current() == "es"


def test_the_faculty_brief_is_written_in_the_language_it_is_given():
    from faculty_report import render_faculty_brief_pdf
    from test_faculty_report import brief_example
    report, record = brief_example()
    for compact in (True, False):
        english = text_of(render_faculty_brief_pdf(report, record, compact=compact, language="en"))
        spanish = text_of(render_faculty_brief_pdf(report, record, compact=compact, language="es"))
        assert "Performance synthesis" in english and "Síntesis del desempeño" in spanish
    assert language.current() == "en"


def test_the_rubric_document_is_written_in_the_language_it_is_given():
    from rubric_report import render_rubric_report_pdf
    from test_rubric_document import RECORD, proposal
    from test_rubric_reports import review
    english = text_of(render_rubric_report_pdf(review(), proposal(), RECORD, language="en"))
    spanish = text_of(render_rubric_report_pdf(review(), proposal(), RECORD, language="es"))
    assert "Evidence from the encounter" in english and "Evidencia del encuentro" in spanish


# --- where the documents are offered ------------------------------------------

from test_faculty_analysis_store import cohort  # noqa: E402,F401  (the fixture)

LABEL = "Idioma del documento · Document language"


def _completed(accounts, token, played=None):
    """A completed encounter, played in ``played`` -- or before the language was recorded."""
    attempt_id = accounts.create_attempt(token, "R1-03", {"presentation": "Synthetic test encounter"})
    session = {"review_completed": True, "management_trace": [
        {"execution_status": "executed", "learner_input": "Reevalúo al paciente en tres minutos.",
         "decision_time_min": 0, "response_time_min": 3,
         "reasoning": {"problem_representation": "A synthetic working model"},
         "state_before": {"observable": {"mental_status": "alert"}},
         "state_after": {"observable": {"mental_status": "alert"}}}]}
    if played:
        session["encounter_language"] = played
    accounts.save_attempt(token, attempt_id, {"schema_version": "mrs_attempt_v1", "session": session},
                          status="completed")
    return attempt_id


def test_the_faculty_page_offers_the_encounter_s_language_first(cohort):
    from test_faculty_portal import page
    accounts, _, users = cohort
    spanish = _completed(accounts, users["resident"]["token"], played="es")
    app = page(cohort, spanish)
    choice = next(item for item in app.radio if item.label == LABEL)
    assert choice.value == "es"
    assert any("Played in Spanish." in str(item.value) for item in app.caption)
    # One that closed before recorded nothing: the reader's language, and it says so.
    older = _completed(accounts, users["resident"]["token"])
    app = page(cohort, older)
    choice = next(item for item in app.radio if item.label == LABEL)
    assert choice.value == "en"
    assert any("did not record its language" in str(item.value) for item in app.caption)


def test_the_faculty_brief_downloaded_is_in_the_chosen_language(cohort):
    from faculty_analysis_store import FacultyBriefStore
    from test_faculty_analysis_store import brief
    from test_faculty_portal import page
    accounts, storage, users = cohort
    attempt_id = _completed(accounts, users["resident"]["token"], played="es")
    record = accounts.get_attempt(users["faculty"]["token"], attempt_id)
    storage.save(users["faculty"]["token"], attempt_id, brief(record))
    app = page(cohort, attempt_id)

    def briefs(app):
        return [value for key, value in app.session_state.to_dict().items()
                if "faculty_pdf_v4" in str(key) and isinstance(value, bytes)]

    assert briefs(app) and all("Síntesis del desempeño" in text_of(blob) for blob in briefs(app))
    next(item for item in app.radio if item.label == LABEL).set_value("en").run()
    assert not app.exception
    english = [blob for blob in briefs(app) if "Performance synthesis" in text_of(blob)]
    assert english, "choosing English writes the same brief in English"
