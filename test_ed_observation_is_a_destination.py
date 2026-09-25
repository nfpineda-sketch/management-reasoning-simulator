"""Observation in the emergency department is a destination; keeping monitored is not.

Faculty decision 4 of 2026-09-25 ("Observación: opción C, con duración y estado
explícitos"). "Dejar en observación en urgencias durante N horas" is recorded
as a destination with its duration; "mantener monitorizado" stays monitoring.
Ordering six hours of observation is not having completed them, and not a safe
discharge by itself: only time that actually runs completes the period, with
the evolution and the reassessments that come with it.
"""
import time
import uuid
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import rubric_screening
from account_store import AccountStore
from family_parser import parse_family_actions

APP = str(Path(__file__).with_name("app.py"))


@pytest.mark.parametrize("text, hours", [
    ("La dejo en observacion 6 horas", 6.0),
    ("Queda en observacion en urgencias por 6 horas", 6.0),
    ("Lo dejo en observacion", None),
    ("Keep in ED observation for 6 hours", 6.0),
])
def test_observation_is_a_destination_with_its_duration(text, hours):
    [action] = [a for a in parse_family_actions(text)["actions"] if a["type"] == "disposition"]
    assert action == {"type": "disposition", "destination": "ED observation", "duration_h": hours}


@pytest.mark.parametrize("text, destination", [
    ("La hospitalizo en sala para observacion con glicemia cada hora", "ward"),
    ("Lo mantengo monitorizado", None),
])
def test_an_admission_for_observation_and_monitoring_are_something_else(text, destination):
    actions = parse_family_actions(text)["actions"]
    assert [a.get("destination") for a in actions if a["type"] == "disposition"] == (
        [destination] if destination else [])


def _entry(minute, summaries):
    return {"execution_status": "executed", "decision_time_min": minute, "response_time_min": minute,
            "learner_input": "", "interpreted_action": [], "action_summaries": summaries}


def test_a_discharge_before_the_hours_ran_says_the_period_was_not_completed():
    record = {"payload": {"session": {"management_trace": [
        _entry(5, [{"type": "naloxone", "label": "Naloxone 0.4 mg IV"}]),
        _entry(20, [{"type": "disposition", "destination": "ED observation", "duration_h": 6}]),
        _entry(80, [{"type": "disposition", "destination": "home"}]),
    ]}}}
    row = {r["event_id"]: r for r in rubric_screening.screen_events(record, "opioid_67f")}["opioid_unsafe_discharge"]
    text = " ".join(fact["en"] for fact in row["facts"])
    assert "observation for 6 h was ordered at 20 min" in text and "not completed" in text
    assert row["status"] == "reading"


@pytest.fixture
def anaphylaxis(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'accounts.sqlite3'}"
    accounts = AccountStore(url, allow_sqlite=True)
    with accounts._transaction(write=True) as connection:
        user_id = uuid.uuid4().hex
        accounts._execute(connection, "INSERT INTO mrs_users VALUES (?, ?, ?, ?, ?, 1, ?)",
                          (user_id, "resident_test", "unused-fixture-hash", "resident", 1, int(time.time())))
        token = accounts._new_session(connection, user_id)
    for name, value in (("MRS_AUTH_MODE", "accounts"), ("MRS_DATABASE_URL", url),
                        ("MRS_ALLOW_LOCAL_SQLITE", "true"), ("MRS_OFFLINE_CASES", "1"),
                        ("MRS_DEFAULT_VARIANT", "anaphylaxis_29f")):
        monkeypatch.setenv(name, value)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    import curriculum_runtime
    monkeypatch.setattr(curriculum_runtime, "assign_challenge", lambda *args, **kwargs: {
        "challenge_id": "R1-06", "reason": "test", "assignment_seed": 17,
        "competence_decision": "Not assessed automatically"})
    from resident_profile import ProfileStore
    ProfileStore(accounts).decline(token)
    at = AppTest.from_file(APP, default_timeout=180)
    at.session_state["_account_token"] = token
    at.run()
    next(b for b in at.button if b.label == "Begin Encounter").click().run()
    return at


def submit(at, text):
    next(r for r in at.radio if r.label == "Encounter").set_value("Treat").run()
    next(a for a in at.text_area if a.label == "Enter your clinical reasoning and/or actions").set_value(text)
    next(b for b in at.button if b.label == "Submit").click().run()
    assert not at.exception


def test_ordered_hours_complete_only_when_the_time_runs(anaphylaxis):
    at = anaphylaxis
    submit(at, "Creo que es una anafilaxia, porque tiene rash, edema facial y PA baja. Mi prioridad es la "
               "adrenalina. Doy adrenalina 0.5 mg im. Espero que suba la PA. Reevaluo en 10 minutos PA.")
    submit(at, "Mi prioridad es vigilar la reaccion bifasica. La dejo en observacion 6 horas. Espero que no "
               "recurra. Reevaluo en 30 minutos PA y via aerea.")
    labels = [s.get("label") for e in at.session_state["management_trace"] for s in e.get("action_summaries", [])]
    assert "ED observation for 6 h ordered; the period has not been completed" in labels
    assert at.session_state["state"]["disposition"] == "ED observation"
    said = lambda: " ".join(str(e.get("text")) for e in at.session_state["events"])
    assert "emergency department observation ordered at" not in said()
    for _ in range(3):
        submit(at, "Reevaluo en 120 minutos")
    assert "of emergency department observation ordered at" in said() and "are complete" in said()
