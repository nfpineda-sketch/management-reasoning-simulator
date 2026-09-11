"""Real Streamlit progress controls backed by temporary account/progress storage."""

import pytest
from streamlit.testing.v1 import AppTest

from account_store import AccountStore, hash_password
from progress_store import ProgressStore


PASSWORD = "Synthetic-progress-ui-password"
APP = """
import streamlit as st
from account_store import AccountStore
from progress_portal import render_progress_dashboard, render_attempt_assessment
store = AccountStore(st.session_state['database_url'], allow_sqlite=True)
token = st.session_state['test_token']
context = {'store': store, 'token': token, 'user': store.get_user(token)}
if st.session_state.get('test_attempt'):
    render_attempt_assessment(context, store.get_attempt(token, st.session_state['test_attempt']))
render_progress_dashboard(context)
"""


@pytest.fixture(scope="module")
def password_hash():
    return hash_password(PASSWORD)


@pytest.fixture
def accounts(tmp_path, password_hash):
    url = "sqlite:///" + str(tmp_path / "progress.sqlite3")
    store = AccountStore(url, allow_sqlite=True)
    store.bootstrap_admin("admin", password_hash)
    admin = store.authenticate("admin", PASSWORD)
    code = store.create_invite(admin, "resident", 1)
    resident = store.register("resident.one", PASSWORD, code)
    faculty_code = store.create_invite(admin, "faculty")
    faculty = store.register("faculty.one", PASSWORD, faculty_code)
    return {"url": url, "store": store, "admin": admin, "resident": resident,
            "faculty": faculty,
            "resident_id": store.get_user(resident)["id"], "progress": ProgressStore(store)}


def completed_attempt(accounts):
    store, resident = accounts["store"], accounts["resident"]
    attempt_id = store.create_attempt(resident, "R1-03", {"private_marker": "never expose the next case"})
    payload = {"session": {"review_completed": True, "management_trace": [{
        "execution_status": "executed",
        "learner_input": "Reassess perfusion after simulated intervention.",
        "reasoning": {"expected_effect": "Improved perfusion"},
        "state_before": {"observable": {"heart_rate": 160}, "hidden": {"private": True}},
        "state_after": {"observable": {"heart_rate": 100}},
    }]}}
    store.save_attempt(resident, attempt_id, payload, "completed", expected_revision=0)
    return attempt_id


def page(accounts, role="admin", attempt_id=None):
    app = AppTest.from_string(APP, default_timeout=15)
    app.session_state["database_url"] = accounts["url"]
    app.session_state["test_token"] = accounts[role]
    if attempt_id:
        app.session_state["test_attempt"] = attempt_id
    app.run()
    assert not app.exception
    return app


def widget(app, kind, label):
    return next(item for item in getattr(app, kind) if item.label == label)


def goal(accounts, objective_id):
    return next(row for row in accounts["progress"].get_progress(accounts["resident"])["objectives"]
                if row["objective_id"] == objective_id)


def submit_assessment(app, objective_id="C4", satisfactory=True):
    widget(app, "selectbox", "Objective observed in this encounter").set_value(objective_id).run()
    widget(app, "checkbox", "Satisfactory demonstration of this simulated component").set_value(satisfactory)
    widget(app, "text_input", "Observed clinical context").set_value("Simulated procedural care and reassessment")
    widget(app, "multiselect", "Evidence supporting your judgment").set_value(["trace:0"])
    widget(app, "text_area", "Faculty rationale and feedback").set_value("The selected decision supports this observed component.")
    widget(app, "button", "Record objective assessment").click().run()
    assert not app.exception


def test_resident_progress_is_read_only_and_own_record_only(accounts):
    attempt_id = completed_attempt(accounts)
    accounts["progress"].assess(accounts["admin"], attempt_id, "TD1", {
        "satisfactory": True, "depth": "foundational", "autonomy": "prompted",
        "context": "Initial simulated support", "evidence_refs": ["trace:0"],
        "notes": "Resident-owned faculty feedback",
    })
    app = page(accounts, "resident", attempt_id)
    assert not app.button
    assert not app.selectbox
    assert not app.text_input
    assert not app.text_area
    assert any("Resident-owned faculty feedback" in item.value for item in app.markdown)
    assert not any("never expose the next case" in item.value for item in app.markdown)
    assert len(app.dataframe) >= 1
    overview = app.dataframe[0].value
    assert overview.loc[overview["Objective"].str.startswith("TD1"), "Satisfactory observations"].iloc[0] == "1/10"


def test_multiple_objectives_are_reviewed_separately_and_capped_form_is_removed(accounts):
    attempt_id = completed_attempt(accounts)
    accounts["progress"].set_target(accounts["admin"], "C4", 1, "UI cap regression")
    app = page(accounts, attempt_id=attempt_id)
    assert widget(app, "checkbox", "Satisfactory demonstration of this simulated component").value is False
    options = widget(app, "selectbox", "Objective observed in this encounter").options
    assert not any(option.startswith(("C2 ·", "C15 ·")) for option in options)
    submit_assessment(app, "C4")
    assert goal(accounts, "C4")["count"] == 1
    assert not any(option.startswith("C4 ·") for option in widget(app, "selectbox", "Objective observed in this encounter").options)
    assert any("Satisfactory observation saved" in item.value for item in app.success)
    submit_assessment(app, "C1", satisfactory=False)
    assert goal(accounts, "C1")["count"] == 0
    assert goal(accounts, "C1")["assessed_count"] == 1
    assert goal(accounts, "C4")["count"] == 1


def test_confirmation_and_void_require_explicit_faculty_actions(accounts):
    attempt_id = completed_attempt(accounts)
    accounts["progress"].set_target(accounts["admin"], "C4", 1, "Confirmation regression")
    app = page(accounts, attempt_id=attempt_id)
    submit_assessment(app)
    assert goal(accounts, "C4")["status"] == "target_reached"
    widget(app, "selectbox", "Objective for faculty decision").set_value("C4").run()
    widget(app, "text_area", "Reason for faculty decision").set_value("Consistent simulated component evidence reviewed.")
    widget(app, "button", "Confirm simulated-component achievement").click().run()
    assert not app.exception
    assert goal(accounts, "C4")["confirmed"]
    widget(app, "text_area", "Reason for faculty decision").set_value("Reopen for further review of depth.")
    widget(app, "button", "Reopen objective").click().run()
    assert not app.exception
    assert not goal(accounts, "C4")["confirmed"]
    assert goal(accounts, "C4")["count"] == 1
    widget(app, "text_area", "Reason for voiding assessment").set_value("Incorrect objective selected in this test judgment.")
    widget(app, "button", "Void assessment").click().run()
    assert not app.exception
    assert goal(accounts, "C4")["count"] == 0
    assert goal(accounts, "C4")["observations"][0]["voided"]


def test_active_attempt_has_no_assessment_controls(accounts):
    attempt_id = accounts["store"].create_attempt(accounts["resident"], "R1-03", {})
    app = page(accounts, attempt_id=attempt_id)
    assert not any(item.label == "Record objective assessment" for item in app.button)
    assert any("Complete the encounter and reflection" in item.value for item in app.caption)


def test_faculty_can_review_but_cannot_change_program_targets(accounts):
    attempt_id = completed_attempt(accounts)
    app = page(accounts, "faculty", attempt_id)
    assert not any(item.label == "Save program target" for item in app.button)
    widget(app, "button", "Record objective assessment").click().run()
    assert not app.exception
    assert app.error
    assert goal(accounts, "TD1")["assessed_count"] == 0
    submit_assessment(app, "TD1")
    assert goal(accounts, "TD1")["count"] == 1


def test_admin_can_configure_targets_without_residents(tmp_path, password_hash):
    url = "sqlite:///" + str(tmp_path / "empty_program.sqlite3")
    store = AccountStore(url, allow_sqlite=True)
    store.bootstrap_admin("admin", password_hash)
    admin = store.authenticate("admin", PASSWORD)
    app = page({"url": url, "admin": admin})
    widget(app, "selectbox", "Objective target").set_value("C4").run()
    widget(app, "number_input", "Required satisfactory observations").set_value(22)
    widget(app, "text_area", "Reason for target change").set_value("Faculty-approved program target adjustment.")
    widget(app, "button", "Save program target").click().run()
    assert not app.exception
    assert any("Program target saved" in item.value for item in app.success)
    target = next(row for row in ProgressStore(store).list_targets(admin) if row["objective_id"] == "C4")
    assert target["target"] == 22
