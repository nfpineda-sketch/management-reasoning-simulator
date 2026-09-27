"""What counts as help when autonomy is judged, said the same way in both languages (faculty, 2026-09-27).

The autonomy scale does not change. A request to complete the documentation is
not lower clinical autonomy; a suggestion with clinical content is help and is
recorded as help received; choosing a clinical answer the system offered is not
formulating it unprompted; and help nobody reported is never read as
independent performance. The faculty's instructions say so in English and in
Spanish, where help is declared and where autonomy is recorded.
"""
from pathlib import Path

import encounter_context
import language

ROOT = Path(__file__).resolve().parent


def test_the_guidance_says_the_same_three_things_in_both_languages():
    english, spanish = encounter_context.AUTONOMY_GUIDANCE
    for phrase in ("request to complete the documentation", "does not by itself show lower clinical autonomy",
                   "adds clinical content", "is assistance and must be recorded as help received",
                   "Choosing a clinical answer offered by the system is not the same as formulating it unprompted",
                   "keeps where each answer came from", "never read as independent performance"):
        assert phrase in english, phrase
    for phrase in ("solicitud para completar la documentación", "«falta registrar qué vas a reevaluar»",
                   "no demuestra por sí sola menor autonomía clínica", "aporta contenido clínico",
                   "sí constituye asistencia y debe quedar registrada",
                   "Elegir una respuesta clínica ofrecida por el sistema no equivale a formularla espontáneamente",
                   "conserva la procedencia de cada respuesta", "nunca se lee como desempeño independiente"):
        assert phrase in spanish, phrase
    # An unknown context keeps the name the declaration form gives it.
    assert "«" + encounter_context.label("assistance", "not_reported", "es") + "»" in spanish
    assert "“" + encounter_context.label("assistance", "not_reported") + "”" in english


def test_each_form_where_autonomy_is_judged_shows_it_in_the_language_on_screen():
    assert "encounter_context.said(encounter_context.AUTONOMY_GUIDANCE)" in (ROOT / "faculty_portal.py").read_text(encoding="utf-8")
    assert "_said(AUTONOMY_GUIDANCE)" in (ROOT / "progress_portal.py").read_text(encoding="utf-8")
    assert encounter_context.said(encounter_context.AUTONOMY_GUIDANCE) == encounter_context.AUTONOMY_GUIDANCE[0]
    with language.presenting("es"):
        assert encounter_context.said(encounter_context.AUTONOMY_GUIDANCE) == encounter_context.AUTONOMY_GUIDANCE[1]
        assert encounter_context.said(encounter_context.NO_CLINICAL_HELP_FEATURE).startswith("No hay ayudas clínicas")
    faculty = (ROOT / "faculty_portal.py").read_text(encoding="utf-8")
    assert "NO_CLINICAL_HELP_FEATURE[0]" not in faculty and "AUTONOMY_NOT_DETERMINED[0] +" not in faculty


def test_the_scale_and_the_brief_s_instructions_are_unchanged():
    import faculty_analysis
    from objectives import AUTONOMY_LEVELS
    assert AUTONOMY_LEVELS == ("guided", "prompted", "independent")
    # 1.6 (2026-09-27) changed which objectives a brief lists (observation
    # opportunities, and R1-03, R1-04 and R2-01); the instructions below did not.
    assert faculty_analysis.PROMPT_VERSION == "1.6"
    prompt = faculty_analysis.SYSTEM_PROMPT if hasattr(faculty_analysis, "SYSTEM_PROMPT") else ""
    source = (ROOT / "faculty_analysis.py").read_text(encoding="utf-8")
    for rule in ("A neutral request to complete a category, a format clarification",
                 "not by itself a loss of autonomy",
                 'If assistance_declaration is "not_reported"',
                 "return null autonomy for every objective"):
        assert rule in (prompt or source), rule


def test_a_faculty_member_reads_it_where_help_is_declared_and_where_autonomy_is_recorded(tmp_path):
    """A representative render of the real faculty page, in English and in Spanish."""
    from streamlit.testing.v1 import AppTest
    from test_faculty_analysis_store import completed_attempt
    from test_faculty_portal import APP
    accounts, storage, users = cohort_for(tmp_path)
    attempt_id = completed_attempt(accounts, users["resident"]["token"])
    for code, guidance in (("en", encounter_context.AUTONOMY_GUIDANCE[0]), ("es", encounter_context.AUTONOMY_GUIDANCE[1])):
        app = AppTest.from_string(APP, default_timeout=15)
        app.session_state["database_url"] = accounts._url
        app.session_state["test_token"] = users["faculty"]["token"]
        app.session_state["test_attempt"] = attempt_id
        app.session_state["presentation_language"] = code
        app.run()
        assert not app.exception
        captions = [str(item.value) for item in app.caption]
        assert guidance in captions, code
        autonomy = [item for item in app.selectbox if item.label in ("Observed autonomy", "Autonomía observada")]
        assert autonomy and guidance in (autonomy[0].help or ""), code
        # The level a resident reaches with help is "Con orientación" in Spanish (faculty, 2026-09-27).
        assert ("Con orientación" if code == "es" else "Prompted") in autonomy[0].options, code
        assert "Con indicaciones" not in autonomy[0].options


def cohort_for(tmp_path):
    """The accounts test_faculty_portal's page expects, built directly: an admin, a faculty member, residents."""
    import time
    import uuid
    from account_store import AccountStore
    from faculty_analysis_store import FacultyBriefStore
    accounts = AccountStore(f"sqlite:///{tmp_path / 'accounts.sqlite3'}", allow_sqlite=True)
    users = {}
    with accounts._transaction(write=True) as connection:
        for username, role, year in (("admin", "admin", None), ("faculty", "faculty", None),
                                      ("resident", "resident", 1)):
            user_id = uuid.uuid4().hex
            accounts._execute(connection, "INSERT INTO mrs_users VALUES (?, ?, ?, ?, ?, 1, ?)",
                              (user_id, username, "unused-fixture-hash", role, year, int(time.time())))
            users[username] = {"id": user_id, "token": accounts._new_session(connection, user_id)}
    return accounts, FacultyBriefStore(accounts), users
