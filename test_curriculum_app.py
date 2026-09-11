"""Real Streamlit integration checks against temporary persistent accounts."""
from copy import deepcopy
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest
from account_store import AccountStore, hash_password

APP = str(Path(__file__).with_name("app.py"))


@pytest.fixture
def cohort(tmp_path, monkeypatch):
    url = "sqlite:///" + str(tmp_path / "accounts.sqlite3")
    monkeypatch.setenv("MRS_AUTH_MODE", "accounts")
    monkeypatch.setenv("MRS_DATABASE_URL", url)
    monkeypatch.setenv("MRS_ALLOW_LOCAL_SQLITE", "true")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    store = AccountStore(url, allow_sqlite=True)
    store.bootstrap_admin("teacher", hash_password("local-test-password"))
    admin = store.authenticate("teacher", "local-test-password")
    code = store.create_invite(admin, "resident", 1)
    resident = store.register("resident-one", "local-resident-password", code)
    return store, admin, resident


def open_app(token):
    at = AppTest.from_file(APP, default_timeout=20)
    at.session_state["_account_token"] = token
    at.run()
    assert not at.exception
    return at


def click(at, label):
    next(button for button in at.button if button.label == label).click().run()
    assert not at.exception


def test_existing_shared_gate_remains_closed_until_password(monkeypatch):
    monkeypatch.setenv("MRS_AUTH_MODE", "shared")
    at = AppTest.from_file(APP, default_timeout=20)
    at.secrets["APP_PASSWORD"] = "local-shared-test-only"
    at.run()
    assert not at.exception
    assert not at.selectbox
    at.text_input[0].set_value("wrong")
    click(at, "Enter")
    assert not at.selectbox
    at.text_input[0].set_value("local-shared-test-only")
    click(at, "Enter")
    assert any(w.label == "Clinical surface" for w in at.selectbox)
    click(at, "Begin Encounter")
    assert at.session_state.state["case_id"] == "PS001"
    assert not any("Developer" in e.label for e in at.expander)


def test_resident_assignment_cardioversion_persistence_and_private_ui(cohort):
    store, admin, token = cohort
    at = open_app(token)
    assert not at.selectbox
    click(at, "Begin Encounter")
    assert not at.exception
    labels = [exp.label for exp in at.expander]
    assert "ECG" in labels
    assert not any("Developer" in label for label in labels)
    learner_text = " ".join(str(item.value) for item in at.markdown)
    assert "R1-03" not in learner_text and "R1-04" not in learner_text
    assert "volume_limited" not in learner_text and "Learning focus" not in learner_text
    text = (
        "The patient is poorly perfused with rapid atrial fibrillation. My working model is that "
        "the rhythm contributes to poor perfusion. My priority is to restore rhythm and improve perfusion. "
        "Administer etomidate 8 mg IV and midazolam 2 mg IV for procedural sedation, followed by "
        "synchronized electrical cardioversion at 200 J. I expect sinus rhythm and improved perfusion. "
        "Immediately after cardioversion, reassess rhythm, heart rate, blood pressure, mental status, and perfusion."
    )
    at.text_area[0].set_value(text)
    click(at, "Submit")
    assert at.session_state.state["treatments"]["cardioversions"] == 1
    assert at.session_state.state["observable"]["rhythm"] == "Sinus rhythm"
    saved_state = deepcopy(at.session_state.state)
    saved_rng = at.session_state.rng_counter
    attempt = store.list_attempts(token)[0]
    assert attempt["payload"]["session"]["state"] == saved_state
    # New browser session obtains the exact frozen case and trace.
    new = open_app(token)
    click(new, "Resume encounter")
    assert new.session_state.state == saved_state
    assert new.session_state.rng_counter == saved_rng
    click(new, "Save & return to dashboard")
    assert not new.selectbox
    teacher = open_app(admin)
    assert any(widget.label == "Management challenge" for widget in teacher.selectbox)
    assert any(exp.label == "Resident activity and recorded evidence" for exp in teacher.expander)


def test_completed_review_readonly_and_revision_conflict_recovery(cohort):
    store, _, token = cohort
    at = open_app(token)
    click(at, "Begin Encounter")
    other = open_app(token)
    click(other, "Resume encounter")
    at.text_area[0].set_value("My working model is that reduced preload contributes to poor perfusion. My priority is to improve perfusion. Give 500 mL normal saline IV. I expect improved blood pressure and capillary refill. Reassess blood pressure, heart rate, mental status, and perfusion in 5 minutes.")
    click(at, "Submit")
    # Second browser has the stale revision, and gets an explicit way out.
    other.text_area[0].set_value("Reassess blood pressure and perfusion now.")
    click(other, "Submit")
    assert any("another session" in str(item.value) for item in other.error)
    click(other, "Discard this tab's unsaved changes and reopen dashboard")
    assert any(b.label == "Resume encounter" for b in other.button)
    click(other, "Resume encounter")
    click(other, "Complete Encounter & Begin Review")
    record = store.list_attempts(token)[0]
    payload = deepcopy(record["payload"])
    ss = payload["session"]
    prompts = ss["review_prompts"]
    assert prompts
    fields = ("working_model_update", "priority_trigger", "alternative_action", "expected_response_reassessment")
    ss["decision_review"] = {p["review_id"]: {f: "I will compare the observed perfusion response." for f in fields} for p in prompts}
    ss["precomparison_decision_review"] = deepcopy(ss["decision_review"])
    ss["expert_comparison_responses"] = {p["review_id"]: {"alignment": "Perfusion remains a concern.", "adjustment": "Reassess the response."} for p in prompts}
    ss["adaptation_plan"] = {f: "Reassess perfusion in context." for f in ("cue", "threshold", "next_priority", "alternative_action", "expected_effect", "reassessment_plan")}
    ss["review_completed"] = True
    ss["expert_comparison_unlocked"] = True
    store.save_attempt(token, record["id"], payload, "completed", record["revision"])
    final_record = store.get_attempt(token, record["id"])
    completed = open_app(token)
    click(completed, "Open review")
    assert not completed.text_area
    assert any("read-only" in str(c.value) for c in completed.caption)
    assert store.get_attempt(token, record["id"])["revision"] == final_record["revision"]
    click(completed, "Next Encounter with This Adaptation Plan")
    assert completed.session_state.state["sim_time"] == 0
    assert completed.session_state.state["seed"] != ss["state"]["seed"]
    assert completed.session_state.carry_forward_plan == ss["adaptation_plan"]


def test_full_app_multiobjective_faculty_assessment_and_resident_progress(cohort):
    """Exercise the real dashboard hooks, forms and persistent resident view."""
    from test_curriculum_assignment import evidence_payload
    from progress_store import ProgressStore

    store, admin, resident = cohort
    resident_id = store.get_user(resident)["id"]
    attempt_id = store.create_attempt(resident, "R1-03", {"seed": 17})
    payload = evidence_payload(True)
    payload["session"]["review_completed"] = True
    payload["session"]["encounter_ended"] = True
    store.save_attempt(resident, attempt_id, payload, "completed", 0)

    def widget(at, kind, label):
        return next(item for item in getattr(at, kind) if item.label == label)

    faculty = open_app(admin)
    for objective in ("C4", "F1"):
        widget(faculty, "selectbox", "Objective observed in this encounter").set_value(objective).run()
        assert not faculty.exception
        widget(faculty, "checkbox", "Satisfactory demonstration of this simulated component").check()
        widget(faculty, "selectbox", "Observed depth").set_value("integrated")
        widget(faculty, "selectbox", "Observed autonomy").set_value("prompted")
        widget(faculty, "text_input", "Observed clinical context").set_value("Faculty review fixture: rhythm and perfusion.")
        widget(faculty, "multiselect", "Evidence supporting your judgment").set_value(["trace:0"])
        widget(faculty, "text_area", "Faculty rationale and feedback").set_value("Test assessment with specific saved reasoning evidence.")
        click(faculty, "Record objective assessment")
        assert not faculty.error

    progress = ProgressStore(store)
    goals = {g["objective_id"]: g for g in progress.get_progress(admin, resident_id)["objectives"]}
    assert goals["C4"]["count"] == goals["F1"]["count"] == 1
    assert goals["C4"]["observations"][0]["depth"] == "integrated"
    assert store.get_attempt(resident, attempt_id)["payload"] == payload

    # Adjust the pilot quota through the admin form, then confirm separately.
    widget(faculty, "selectbox", "Objective target").set_value("C4").run()
    widget(faculty, "number_input", "Required satisfactory observations").set_value(1)
    widget(faculty, "text_area", "Reason for target change").set_value("One-observation test quota.")
    click(faculty, "Save program target")
    widget(faculty, "selectbox", "Objective for faculty decision").set_value("C4").run()
    widget(faculty, "text_area", "Reason for faculty decision").set_value("Formative test confirmation after reviewing the evidence.")
    click(faculty, "Confirm simulated-component achievement")
    assert not faculty.error
    learner = open_app(resident)
    assert not learner.selectbox
    assert not any(b.label in {"Record objective assessment", "Save program target"} for b in learner.button)
    table = learner.dataframe[0].value
    row = table[table["Objective"].str.startswith("C4 ·")].iloc[0]
    assert row["Satisfactory observations"] == "1/1"
    assert row["Status"] == "Confirmed"
    assert any("Test assessment with specific saved reasoning evidence." in str(m.value) for m in learner.markdown)
