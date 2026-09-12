"""Real form behavior: AI is optional, private and never auto-submits credit."""
from copy import deepcopy
import json

import pytest
from streamlit.testing.v1 import AppTest

from account_store import AccountError
from faculty_analysis import FacultyAnalysisError
from faculty_analysis_store import FacultyBriefStore
from progress_store import ProgressStore
from test_faculty_analysis_store import cohort, completed_attempt, brief


APP = """
import streamlit as st
from account_store import AccountStore
from faculty_portal import render_faculty_analysis
from progress_portal import render_attempt_assessment
store = AccountStore(st.session_state['database_url'], allow_sqlite=True)
token = st.session_state['test_token']
context = {'store': store, 'token': token, 'user': store.get_user(token)}
record = store.get_attempt(token, st.session_state['test_attempt'])
render_faculty_analysis(context, record)
render_attempt_assessment(context, record)
"""


def page(cohort, attempt_id, actor="faculty"):
    accounts, _, users = cohort
    app = AppTest.from_string(APP, default_timeout=15)
    app.session_state["database_url"] = accounts._url
    app.session_state["test_token"] = users[actor]["token"]
    app.session_state["test_attempt"] = attempt_id
    app.run()
    assert not app.exception
    return app


def widget(app, kind, label):
    return next(item for item in getattr(app, kind) if item.label == label)


def setup_brief(cohort, recommendation="satisfactory", assistance="guided"):
    accounts, storage, users = cohort
    attempt_id = completed_attempt(accounts, users["resident"]["token"])
    record = accounts.get_attempt(users["faculty"]["token"], attempt_id)
    report = brief(record, assistance)
    row = report["analysis"]["objectives"][0]
    row.update(recommendation=recommendation, evidence_refs=["trace:0"])
    if recommendation != "insufficient_evidence":
        row.update(depth="integrated", autonomy=None if assistance == "unknown" else assistance)
    report = storage.save(users["faculty"]["token"], attempt_id, report)
    return attempt_id, report


def count(cohort, objective_id="TD1"):
    accounts, _, users = cohort
    result = ProgressStore(accounts).get_progress(users["resident"]["token"])
    return next(row["count"] for row in result["objectives"] if row["objective_id"] == objective_id)


def test_loading_rerunning_and_pdf_never_grant_credit_then_faculty_edit_is_saved(cohort):
    attempt_id, report = setup_brief(cohort)
    app = page(cohort, attempt_id)
    assert count(cohort) == 0
    widget(app, "button", "Load AI suggestion into editable form").click().run()
    assert not app.exception
    assert widget(app, "selectbox", "Observed depth").value == "integrated"
    assert widget(app, "selectbox", "Observed autonomy").value == "guided"
    assert widget(app, "selectbox", "Faculty assessment decision").value == "Satisfactory"
    app.run()
    assert count(cohort) == 0
    widget(app, "button", "Record objective assessment").click().run()
    assert any("confirm your review" in item.value for item in app.error)
    assert count(cohort) == 0
    widget(app, "text_area", "Faculty rationale and feedback").set_value("Faculty independently reviewed the selected evidence and amended this feedback.")
    widget(app, "checkbox", "I reviewed the AI draft and confirmed the assessment fields").set_value(True)
    widget(app, "button", "Record objective assessment").click().run()
    assert not app.exception
    assert count(cohort) == 1
    accounts, _, users = cohort
    goal = ProgressStore(accounts).get_progress(users["resident"]["token"])["objectives"][0]
    assert goal["observations"][0]["notes"].startswith("Faculty independently")
    with accounts._transaction() as connection:
        row = accounts._execute(connection, "SELECT details_json FROM mrs_progress_audit WHERE action = 'credited'").fetchone()
    assert json.loads(row["details_json"])["ai_brief_id"] == report["brief_id"]


def test_insufficient_evidence_is_unanswered_not_an_automatic_failed_assessment(cohort):
    attempt_id, _ = setup_brief(cohort, "insufficient_evidence", "unknown")
    app = page(cohort, attempt_id)
    widget(app, "button", "Load AI suggestion into editable form").click().run()
    for label in ("Faculty assessment decision", "Observed depth", "Observed autonomy"):
        assert widget(app, "selectbox", label).value is None
    widget(app, "checkbox", "I reviewed the AI draft and confirmed the assessment fields").set_value(True)
    widget(app, "button", "Record objective assessment").click().run()
    assert not app.exception
    assert count(cohort) == 0
    accounts, _, users = cohort
    assert ProgressStore(accounts).get_progress(users["resident"]["token"])["objectives"][0]["assessed_count"] == 0


def test_unknown_autonomy_requires_faculty_input_and_draft_does_not_bleed_between_objectives(cohort):
    attempt_id, _ = setup_brief(cohort, assistance="unknown")
    app = page(cohort, attempt_id)
    widget(app, "button", "Load AI suggestion into editable form").click().run()
    assert widget(app, "selectbox", "Observed autonomy").value is None
    widget(app, "text_area", "Faculty rationale and feedback").set_value("Unsaved TD1-specific edit")
    widget(app, "selectbox", "Objective observed in this encounter").set_value("C4").run()
    assert widget(app, "text_area", "Faculty rationale and feedback").value != "Unsaved TD1-specific edit"
    assert not any(item.label == "Faculty assessment decision" for item in app.selectbox)
    assert count(cohort) == 0


def test_resident_never_receives_private_brief_or_draft_controls(cohort):
    attempt_id, _ = setup_brief(cohort)
    app = page(cohort, attempt_id, "resident")
    assert not app.button and not app.selectbox and not app.dataframe
    assert not app.get("download_button")


def test_concise_and_full_downloads_reuse_saved_analysis_without_credit(cohort):
    attempt_id, report = setup_brief(cohort)
    app = page(cohort, attempt_id)
    labels = [item.label for item in app.get("download_button")]
    assert "Download 2-page faculty brief (PDF)" in labels
    assert "Download full faculty analysis (PDF)" in labels
    app.run()
    assert count(cohort) == 0
    accounts, storage, users = cohort
    assert storage.get_latest(users["faculty"]["token"], attempt_id)["brief_id"] == report["brief_id"]


def test_compact_layout_failure_preserves_full_report_and_manual_assessment(cohort, monkeypatch):
    import faculty_portal
    render = faculty_portal.render_faculty_brief_pdf
    def oversized(report, record, *, compact=True, app_url=None):
        if compact:
            raise ValueError("Content exceeds compact page budget")
        return render(report, record, compact=False, app_url=app_url)
    monkeypatch.setattr(faculty_portal, "render_faculty_brief_pdf", oversized)
    attempt_id, _ = setup_brief(cohort)
    app = page(cohort, attempt_id)
    assert any("could not be fitted" in item.value for item in app.warning)
    assert any(item.label == "Download full faculty analysis (PDF)" for item in app.get("download_button"))
    assert widget(app, "button", "Record objective assessment")
    assert count(cohort) == 0


@pytest.mark.parametrize("url", ["https://user:password@example.org/", "https://example.org/?token=private", "javascript:alert(1)", "https://example.org/#secret", "https://[invalid/"])
def test_public_pdf_url_rejects_credentials_and_private_query_parameters(monkeypatch, url):
    import faculty_portal
    monkeypatch.setattr(faculty_portal, "_secret", lambda *args: url)
    assert faculty_portal._public_app_url() is None


def test_changing_assistance_invalidates_loaded_draft_and_acknowledgement(cohort):
    attempt_id, _ = setup_brief(cohort, assistance="independent")
    app = page(cohort, attempt_id)
    widget(app, "button", "Load AI suggestion into editable form").click().run()
    widget(app, "checkbox", "I reviewed the AI draft and confirmed the assessment fields").set_value(True).run()
    assert widget(app, "selectbox", "Observed autonomy").value == "independent"
    widget(app, "selectbox", "Assistance received during this encounter").set_value("guided").run()
    assert not app.exception
    assert not any(item.label == "Faculty assessment decision" for item in app.selectbox)
    assert widget(app, "selectbox", "Observed autonomy").value != "independent"
    assert not any(item.label == "I reviewed the AI draft and confirmed the assessment fields" for item in app.checkbox)
    assert count(cohort) == 0


def test_expired_staff_session_is_handled_before_private_report_access(cohort):
    from faculty_portal import _staff_record
    accounts, _, users = cohort
    attempt_id, _ = setup_brief(cohort)
    token = users["faculty"]["token"]
    context = {"store": accounts, "token": token, "user": accounts.get_user(token)}
    record = accounts.get_attempt(token, attempt_id)
    accounts.logout(token)
    with pytest.raises(AccountError, match="Faculty analysis"):
        _staff_record(context, record)


def test_brief_reload_error_does_not_relabel_loaded_ai_fields_as_manual(cohort, monkeypatch):
    import faculty_portal
    attempt_id, _ = setup_brief(cohort)
    app = page(cohort, attempt_id)
    widget(app, "button", "Load AI suggestion into editable form").click().run()
    def fail(*args, **kwargs):
        raise AccountError("The saved faculty analysis could not be read.")
    monkeypatch.setattr(faculty_portal, "_current_report", fail)
    app.run()
    assert not app.exception
    assert widget(app, "selectbox", "Faculty assessment decision").value == "Satisfactory"
    assert not widget(app, "checkbox", "I reviewed the AI draft and confirmed the assessment fields").value
    widget(app, "button", "Record objective assessment").click().run()
    assert count(cohort) == 0
    assert any("confirm your review" in item.value for item in app.error)


def test_generation_is_explicit_saved_once_and_rerun_uses_saved_result(cohort, monkeypatch):
    import faculty_portal
    accounts, storage, users = cohort
    attempt_id = completed_attempt(accounts, users["resident"]["token"])
    calls = []
    monkeypatch.setattr(faculty_portal, "_secret", lambda name, default="": "fixture-key" if name == "OPENAI_API_KEY" else "fixture-model")
    def generate(record, **kwargs):
        calls.append(record["id"])
        return brief(record, kwargs["assistance_context"])
    monkeypatch.setattr(faculty_portal, "generate_faculty_brief", generate)
    app = page(cohort, attempt_id)
    assert calls == []
    widget(app, "button", "Generate AI faculty brief").click().run()
    assert not app.exception and calls == [attempt_id]
    assert storage.get_latest(users["faculty"]["token"], attempt_id)
    assert app.get("download_button")
    app.run()
    assert calls == [attempt_id] and count(cohort) == 0


def test_provider_failure_keeps_manual_evaluation_available(cohort, monkeypatch):
    import faculty_portal
    accounts, storage, users = cohort
    attempt_id = completed_attempt(accounts, users["resident"]["token"])
    monkeypatch.setattr(faculty_portal, "_secret", lambda name, default="": "fixture-value")
    def fail(*args, **kwargs):
        raise FacultyAnalysisError("Faculty analysis could not be generated. No assessment was recorded.")
    monkeypatch.setattr(faculty_portal, "generate_faculty_brief", fail)
    app = page(cohort, attempt_id)
    widget(app, "button", "Generate AI faculty brief").click().run()
    assert not app.exception
    assert app.error
    assert widget(app, "button", "Record objective assessment")
    assert storage.get_latest(users["faculty"]["token"], attempt_id) is None


def test_progress_rejects_attribution_to_another_encounter(cohort):
    attempt_id, report = setup_brief(cohort)
    accounts, _, users = cohort
    second = completed_attempt(accounts, users["resident"]["token"])
    with pytest.raises(AccountError, match="does not match"):
        ProgressStore(accounts).assess(users["faculty"]["token"], second, "TD1", {
            "satisfactory": True, "depth": "integrated", "autonomy": "guided",
            "context": "Synthetic test", "evidence_refs": ["trace:0"], "notes": "Faculty reviewed.",
            "ai_brief_id": report["brief_id"],
        })
    assert count(cohort) == 0
