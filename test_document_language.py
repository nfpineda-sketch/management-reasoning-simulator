"""An encounter's documents are written in the language it was played in.

Faculty, 2026-09-26: "if the encounter is run in Spanish, the PDFs are
generated in Spanish; if it is run in English, in English. Whatever the app
stores can be seen in either." The encounter records its language when it
closes; each document is written in it unless its reader chooses the other;
an encounter that closed before recorded none, and keeps following its
reader's choice -- it is never guessed.

Faculty, 2026-09-27: the encounter's language is the one chosen when it
starts, fixed until it closes, with the selector locked meanwhile; the
screens keep following whoever reads them.
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


def test_closing_keeps_the_language_the_encounter_started_in(monkeypatch):
    from test_curriculum_trajectories import initialize, load_engine
    engine = load_engine()
    session = initialize(engine, engine["INITIAL_STATE"])
    session["encounter_language"] = "en"
    monkeypatch.setenv("MRS_LANGUAGE", "es")
    engine["begin_decision_review"]([], session["state"])
    assert session["encounter_ended"] is True and session["encounter_language"] == "en"


def test_an_encounter_that_recorded_no_language_at_its_start_records_the_one_it_closes_in(monkeypatch):
    """An encounter already under way on 2026-09-27 keeps the earlier rule; nothing is migrated."""
    from test_curriculum_trajectories import initialize, load_engine
    engine = load_engine()
    session = initialize(engine, engine["INITIAL_STATE"])
    assert "encounter_language" not in session
    monkeypatch.setenv("MRS_LANGUAGE", "es")
    engine["begin_decision_review"]([], session["state"])
    assert session["encounter_ended"] is True and session["encounter_language"] == "es"


@pytest.mark.parametrize("played, other", [("es", "en"), ("en", "es")])
def test_the_language_chosen_at_the_start_holds_through_the_encounter_and_its_documents(
        tmp_path, monkeypatch, played, other):
    """Smoke test, both ways: start in one language, try to switch mid-encounter, close, download."""
    from test_doses_by_solution_and_by_weight import ANTICOAGULATE, start, submit, widget
    # The deployment's default language is the one chosen: AppTest formats a translated option
    # outside the app's session, where only that default can be read.
    monkeypatch.setenv("MRS_LANGUAGE", played)
    at = start(tmp_path, monkeypatch, "pulmonary_embolism_33f", "R2-02", language=played)
    assert at.session_state["encounter_language"] == played
    selector = widget(at.selectbox, "Idioma · Language")
    assert selector.disabled and selector.value == played
    # A change forced on the widget mid-encounter does not take: the encounter keeps its language.
    at.session_state["presentation_language"] = other
    at.run()
    assert at.session_state["presentation_language"] == played and at.session_state["encounter_language"] == played
    submit(at, ANTICOAGULATE)
    submit(at, "Creo que es un tromboembolismo pulmonar. Mi prioridad es un destino monitorizado. "
               "La hospitalizo en UCI. Espero que se mantenga estable. Reevaluo en 15 minutos PA y saturacion.")
    widget(at.button, "Complete Encounter & Begin Review").click().run()
    assert not at.exception
    assert at.session_state["encounter_ended"] is True
    assert at.session_state["encounter_language"] == played
    from account_store import AccountStore
    import json
    import os
    accounts = AccountStore(os.environ["MRS_DATABASE_URL"], allow_sqlite=True)
    with accounts._transaction() as connection:
        row = accounts._execute(connection, "SELECT payload_json FROM mrs_attempts").fetchone()
    assert json.loads(row["payload_json"])["session"]["encounter_language"] == played
    # Closed: the selector is the reader's again, and the record's download starts in the encounter's
    # language and can be taken in the other one on request.
    assert not widget(at.selectbox, "Idioma · Language").disabled
    documents = [item for item in at.radio if item.label == "Idioma del documento · Document language"]
    assert documents and all(item.value == played for item in documents)
    documents[0].set_value(other).run()
    assert not at.exception
    assert [item for item in at.radio if item.label == "Idioma del documento · Document language"][0].value == other
    assert at.session_state["encounter_language"] == played


@pytest.mark.parametrize("viewer", ["en", "es"])
def test_a_faculty_member_reads_in_their_own_language_and_the_documents_start_in_the_encounter_s(
        tmp_path, viewer):
    from streamlit.testing.v1 import AppTest
    from test_autonomy_guidance import cohort_for
    from test_faculty_portal import APP
    accounts, _, users = cohort_for(tmp_path)
    token = users["resident"]["token"]
    attempt_id = accounts.create_attempt(token, "R1-03", {"presentation": "Synthetic test encounter"})
    accounts.save_attempt(token, attempt_id, {
        "schema_version": "mrs_attempt_v1",
        "session": {"review_completed": True, "encounter_language": "es",  # played in Spanish
                    "management_trace": [
                        {"execution_status": "executed", "learner_input": "Reassess the patient in three minutes.",
                         "decision_time_min": 0, "response_time_min": 3,
                         "reasoning": {"problem_representation": "A synthetic working model"},
                         "state_before": {"observable": {"mental_status": "alert"}},
                         "state_after": {"observable": {"mental_status": "alert"}}}]},
    }, status="completed")

    def page():
        app = AppTest.from_string(APP, default_timeout=15)
        app.session_state["database_url"] = accounts._url
        app.session_state["test_token"] = users["faculty"]["token"]
        app.session_state["test_attempt"] = attempt_id
        app.session_state["presentation_language"] = viewer
        app.run()
        assert not app.exception
        return app

    app = page()
    shown = " ".join(str(item.value) for item in app.markdown)
    heading = {"en": "**Assistance context**", "es": "**" + language_t("Assistance context", "es") + "**"}[viewer]
    assert heading in shown
    documents = next(item for item in app.radio if item.label == "Idioma del documento · Document language")
    assert documents.value == "es"
    documents.set_value("en").run()
    assert not app.exception
    assert next(item for item in app.radio if item.label == "Idioma del documento · Document language").value == "en"


def language_t(text, code):
    import report_language
    return report_language.t(text, code)


def test_a_new_encounter_does_not_inherit_the_last_one_s_language():
    # Every place that opens an encounter fixes the language on screen as it starts,
    # or clears the last one (the reset), so none carries an earlier encounter's.
    import ast
    from pathlib import Path
    tree = ast.parse((Path(__file__).with_name("app.py")).read_text(encoding="utf-8"))
    opened = cleared = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.Module)):
            body = ast.unparse(node) if isinstance(node, ast.FunctionDef) else ""
            if "st.session_state.encounter_ended = False" in body:
                opened += 1
                cleared += ("st.session_state.pop('encounter_language', None)" in body
                            or "st.session_state.encounter_language = language.current()" in body)
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


# --- the document's own words, all of them ----------------------------------

# The document's own labels. The resident's words keep whatever language they were
# written in ("Breathing effort, oxygenation and alertness at the next review").
ENGLISH_FURNITURE = ("DECISION 1", "Based on:", "Changed:", "Unchanged:", "(available at", ", sampled at",
                     " requested", "Alertness ", "Breathing effort Increased", "Extremities ",
                     "Pulse present", "Domain ", "Rubric version", "Assessment status")


def test_a_spanish_document_says_its_own_words_in_spanish():
    """What the record assembled around its values -- headings, references, observations,
    study requests, the rubric's traceability -- was English inside a Spanish document
    until 2026-09-26. The model's prose and the case's narrative have their own stages."""
    from faculty_report import render_faculty_brief_pdf
    from management_trace_report import render_management_trace_pdf
    from rubric_report import render_rubric_report_pdf
    from test_faculty_report import brief_example
    from test_management_trace_report import report_example
    from test_rubric_document import RECORD, proposal
    from test_rubric_reports import review
    trace_report, payload = report_example()
    report, record = brief_example()
    spanish = {
        "trace": text_of(render_management_trace_pdf(trace_report, payload, language="es")),
        "brief": text_of(render_faculty_brief_pdf(report, record, compact=False, language="es")),
        "rubric": text_of(render_rubric_report_pdf(review(), proposal(), RECORD, language="es")),
    }
    english = {
        "trace": text_of(render_management_trace_pdf(trace_report, payload, language="en")),
        "rubric": text_of(render_rubric_report_pdf(review(), proposal(), RECORD, language="en")),
    }
    for name, text in spanish.items():
        leaks = [word for word in ENGLISH_FURNITURE if word in text]
        assert not leaks, (name, leaks)
    assert "DECISIÓN 1" in spanish["trace"] and "Basado en:" in spanish["trace"]
    assert "DECISION 1" in english["trace"] and "Based on:" in english["trace"]
    assert "Versión de la rúbrica" in spanish["rubric"] and "Rubric version" in english["rubric"]


def test_an_order_is_written_in_spanish_with_its_dose_untouched():
    import report_presentation as presentation
    orders = [({"type": "diagnostic", "diagnostic": "lactate", "result": {"time_min": 7}},
               "Lactate requested · result at 7 min", "Solicitud de lactato · resultado a los 7 min"),
              ({"type": "disposition", "destination": "ward"}, "Admission to ward", "Ingreso a sala"),
              ({"type": "consult", "service": "gastroenterology"}, "Gastroenterology contacted",
               "Interconsulta a gastroenterología"),
              ({"type": "fluid", "volume_ml": 1000, "fluid_type": "normal saline", "route": "IV"},
               "1000 mL normal saline IV", "1000 mL suero fisiológico IV"),
              ({"type": "oxygen", "flow_lpm": 10, "device": "Simple mask"},
               "Oxygen 10 L/min via Simple mask", "Oxígeno 10 L/min por mascarilla simple"),
              ({"agent": "epinephrine", "rate": 0.1, "units": "mcg/kg/min", "operation": "start"},
               # V-9 (faculty, 2026-10-07; B-5, IG-5): the drug by its Spanish name in a Spanish document.
               "Epinephrine 0.1 mcg/kg/min (started)", "Adrenalina 0.1 mcg/kg/min (iniciado)")]
    for action, english, spanish in orders:
        assert presentation.action_phrase(action) == english
        assert presentation.action_phrase(action, "es") == spanish
    assert presentation.study_name("abg", "es") == "gases arteriales"
    assert presentation.result_field("lactate_mmol_l", "4.4", "es") == "lactato 4.4 mmol/L"
    assert presentation.result_field("lactate_mmol_l", "4.4") == "lactate 4.4 mmol/L"


def test_the_history_topics_have_spanish_names():
    from history_topics import HISTORY_TOPIC_LABELS, HISTORY_TOPIC_LABELS_ES, topic_label
    assert set(HISTORY_TOPIC_LABELS) == set(HISTORY_TOPIC_LABELS_ES)
    assert topic_label("medications", "es") == "Medicamentos"
    assert topic_label("medications") == "Medications"
