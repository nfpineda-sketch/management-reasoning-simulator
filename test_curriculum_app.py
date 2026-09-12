"""Real Streamlit integration checks against temporary persistent accounts."""
from copy import deepcopy
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest
from account_store import AccountStore, hash_password
from objectives import OBJECTIVES

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


def resident_navigation(at, view=None):
    navigation = next(widget for widget in at.sidebar.radio if widget.label == "Navigation")
    assert navigation.key == "_resident_dashboard_view"
    assert navigation.options == ["Clinical encounters", "My progress"]
    if view is not None:
        navigation.set_value(view).run()
        assert not at.exception
    return next(widget for widget in at.sidebar.radio if widget.label == "Navigation").value


def assert_progress_hidden(at):
    """Check rendered content, including collapsed history and table widgets."""
    text = " ".join(
        str(item.value)
        for kind in ("title", "header", "subheader", "markdown", "caption")
        for item in getattr(at, kind)
    ) + " " + " ".join(item.label for item in at.expander)
    assert "Objective progress" not in text
    assert "Observation history" not in text
    for objective in OBJECTIVES.values():
        assert objective["title"] not in text
        assert objective["scope"] not in text
    assert not any("Objective" in item.value.columns for item in at.dataframe)


def assert_active_encounter_private(at):
    assert not at.session_state.encounter_ended
    assert not any(widget.label == "Navigation" for widget in at.sidebar.radio)
    assert not any("Learning focus" in item.label for item in at.expander)
    assert_progress_hidden(at)


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
    assert resident_navigation(at) == "Clinical encounters"
    assert_progress_hidden(at)
    click(at, "Begin Encounter")
    assert not at.exception
    assert_active_encounter_private(at)
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
    assert resident_navigation(new) == "Clinical encounters"
    assert_progress_hidden(new)
    teacher = open_app(admin)
    assert any(widget.label == "Management challenge" for widget in teacher.selectbox)
    assert any(exp.label == "Resident activity and recorded evidence" for exp in teacher.expander)


@pytest.mark.parametrize("role", ["admin", "faculty"])
def test_staff_dashboard_keeps_objective_progress(cohort, role):
    store, admin, _ = cohort
    token = admin
    if role == "faculty":
        invite = store.create_invite(admin, "faculty")
        token = store.register("faculty-one", "local-faculty-password", invite)
    at = open_app(token)
    assert not any(widget.label == "Navigation" for widget in at.sidebar.radio)
    assert any(item.value == "Objective progress" for item in at.subheader)
    assert any(widget.label == "Management challenge" for widget in at.selectbox)
    assert any("Objective" in item.value.columns for item in at.dataframe)


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


def test_full_app_faculty_brief_remains_visible_after_every_objective_is_assessed(cohort):
    """Previously credited objectives must not hide the independent AI report."""
    from test_curriculum_assignment import evidence_payload
    from progress_store import ProgressStore

    store, admin, resident = cohort
    attempt_id = store.create_attempt(resident, "R1-04", {"seed": 17})
    payload = evidence_payload(True)
    payload["session"].update(review_completed=True, encounter_ended=True)
    store.save_attempt(resident, attempt_id, payload, "completed", 0)
    progress = ProgressStore(store)
    for objective_id, definition in OBJECTIVES.items():
        if definition["supported"]:
            progress.assess(admin, attempt_id, objective_id, {
                "satisfactory": True, "depth": "integrated", "autonomy": "guided",
                "context": "Synthetic completed encounter used for dashboard regression.",
                "evidence_refs": ["trace:0"],
                "notes": "Faculty reviewed this simulated component before the AI report was requested.",
            })
    original = store.get_attempt(resident, attempt_id)
    recorded_progress = progress.get_progress(resident)

    faculty = open_app(admin)
    assert not faculty.error
    assert any("no additional eligible objectives" in item.value for item in faculty.info)
    assert any(item.label == "AI faculty assessment brief" for item in faculty.expander)
    generate = next(item for item in faculty.button if item.label == "Generate AI faculty brief")
    assert generate.disabled  # The faculty panel remains visible without a configured provider key.
    assert any(item.label == "Assistance received during this encounter" for item in faculty.selectbox)
    assert not any(item.label == "Record objective assessment" for item in faculty.button)
    assert store.get_attempt(resident, attempt_id) == original
    assert progress.get_progress(resident) == recorded_progress


def test_faculty_pdf_link_selects_encounter_once_and_keeps_review_manual(cohort):
    from test_curriculum_assignment import evidence_payload
    from progress_store import ProgressStore

    store, admin, resident = cohort
    completed = []
    for challenge in ("R1-04", "R1-03"):
        attempt = store.create_attempt(resident, challenge, {"seed": 17})
        payload = evidence_payload(True)
        payload["session"].update(review_completed=True, encounter_ended=True)
        store.save_attempt(resident, attempt, payload, "completed", 0)
        completed.append(attempt)
    original = store.get_attempt(admin, completed[0])
    progress = ProgressStore(store).get_progress(resident)
    faculty = AppTest.from_file(APP, default_timeout=20)
    faculty.session_state["_account_token"] = admin
    faculty.query_params["faculty_attempt"] = completed[0]
    faculty.run()
    assert not faculty.exception
    selector = next(item for item in faculty.selectbox if item.label == "Encounter record")
    assert selector.value == completed[0]
    assert next(item for item in faculty.expander if item.label == "Resident activity and recorded evidence").proto.expanded
    assert not next(item for item in faculty.expander if item.label == "Read the recorded evidence").proto.expanded
    selector.set_value(completed[1]).run()
    assert next(item for item in faculty.selectbox if item.label == "Encounter record").value == completed[1]
    assert store.get_attempt(admin, completed[0]) == original
    assert ProgressStore(store).get_progress(resident) == progress


def test_unknown_or_resident_pdf_link_cannot_expose_private_faculty_analysis(cohort):
    from test_curriculum_assignment import evidence_payload

    store, admin, resident = cohort
    attempt = store.create_attempt(resident, "R1-04", {"seed": 17})
    payload = evidence_payload(True)
    payload["session"].update(review_completed=True, encounter_ended=True)
    store.save_attempt(resident, attempt, payload, "completed", 0)
    for token in (admin, resident):
        page = AppTest.from_file(APP, default_timeout=20)
        page.session_state["_account_token"] = token
        page.query_params["faculty_attempt"] = "unavailable-encounter" if token == admin else attempt
        page.run()
        assert not page.exception
        if token == admin:
            assert any("linked encounter is not available" in item.value for item in page.info)
            assert next(item for item in page.selectbox if item.label == "Encounter record").value == attempt
        else:
            assert not any(item.label == "AI faculty assessment brief" for item in page.expander)
            assert not any(item.label == "Encounter record" for item in page.selectbox)
            assert not page.get("download_button")


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
    assert resident_navigation(learner) == "Clinical encounters"
    assert_progress_hidden(learner)
    resident_navigation(learner, "My progress")
    assert any(item.value == "My progress" for item in learner.subheader)
    assert not learner.selectbox
    assert not any(b.label in {"Record objective assessment", "Save program target"} for b in learner.button)
    assert not any(b.label in {"Begin Encounter", "Resume encounter"} for b in learner.button)
    table = learner.dataframe[0].value
    row = table[table["Objective"].str.startswith("C4 ·")].iloc[0]
    assert row["Satisfactory observations"] == "1/1"
    assert row["Status"] == "Confirmed"
    assert any("Test assessment with specific saved reasoning evidence." in str(m.value) for m in learner.markdown)

    # Returning to launch removes prior objective history before a new case.
    resident_navigation(learner, "Clinical encounters")
    assert_progress_hidden(learner)
    click(learner, "Begin Encounter")
    assert_active_encounter_private(learner)
    learner.text_area[0].set_value(
        "My working model is that reduced preload contributes to poor perfusion. "
        "My priority is to improve perfusion. Give 500 mL normal saline IV. "
        "I expect improved blood pressure and capillary refill. Reassess blood pressure, "
        "heart rate, mental status, and perfusion in 5 minutes."
    )
    click(learner, "Submit")
    assert learner.session_state.management_trace
    assert_active_encounter_private(learner)
    active_id = learner.session_state["_attempt_id"]
    saved_state = deepcopy(learner.session_state.state)
    saved_trace = deepcopy(learner.session_state.management_trace)
    saved_rng = learner.session_state.rng_counter
    active_record = store.get_attempt(resident, active_id)
    recorded_progress = progress.get_progress(resident)

    click(learner, "Save & return to dashboard")
    assert resident_navigation(learner) == "Clinical encounters"
    assert_progress_hidden(learner)
    assert any(b.label == "Resume encounter" for b in learner.button)
    resident_navigation(learner, "My progress")
    assert any(item.value == "My progress" for item in learner.subheader)
    assert not any(b.label in {"Begin Encounter", "Resume encounter"} for b in learner.button)
    table = learner.dataframe[0].value
    row = table[table["Objective"].str.startswith("C4 ·")].iloc[0]
    assert row["Satisfactory observations"] == "1/1"
    assert row["Status"] == "Confirmed"
    assert store.get_attempt(resident, active_id) == active_record
    assert progress.get_progress(resident) == recorded_progress

    resident_navigation(learner, "Clinical encounters")
    assert_progress_hidden(learner)
    click(learner, "Resume encounter")
    assert_active_encounter_private(learner)
    assert learner.session_state["_attempt_id"] == active_id
    assert learner.session_state.state == saved_state
    assert learner.session_state.management_trace == saved_trace
    assert learner.session_state.rng_counter == saved_rng
    assert store.get_attempt(resident, active_id) == active_record

    click(learner, "Complete Encounter & Begin Review")
    assert learner.session_state.encounter_ended
    assert any(item.label == "Learning focus for this encounter" for item in learner.expander)
    assert not any(widget.label == "Navigation" for widget in learner.sidebar.radio)
    assert not any("Objective" in item.value.columns for item in learner.dataframe)
    assert store.get_attempt(resident, attempt_id)["payload"] == payload
    assert progress.get_progress(resident) == recorded_progress
