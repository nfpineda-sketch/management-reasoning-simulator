"""A new encounter starts without the last encounter's close.

2026-09-28, found by the cycle 5 night audit (59Z, encounter isolation). Going
back to the dashboard reset the encounter but not how the last one had ended:

* a close warning left open ("How is this encounter ending?") opened the next
  encounter, at minute 0 and with nothing done, offering "Finish now";
* the last close record ("clinical_close" at minute 2) was saved in the next
  encounter's record, and stayed there if that encounter was abandoned, where
  the faculty brief and the rubric screening read it as that encounter's close.

Each encounter keeps its own: a resumed encounter still has its warning, and a
closed one its record.
"""
import time
import uuid

import pytest
from streamlit.testing.v1 import AppTest

from pathlib import Path

from account_store import AccountStore

APP = str(Path(__file__).with_name("app.py"))


def widget(elements, label):
    return next(item for item in elements if item.label == label)


def offered(at):
    return {button.label for button in at.button}


@pytest.fixture
def page(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'accounts.sqlite3'}"
    accounts = AccountStore(url, allow_sqlite=True)
    with accounts._transaction(write=True) as connection:
        user_id = uuid.uuid4().hex
        accounts._execute(connection, "INSERT INTO mrs_users VALUES (?, ?, ?, ?, ?, 1, ?)",
                          (user_id, "resident_test", "unused-fixture-hash", "resident", 1, int(time.time())))
        token = accounts._new_session(connection, user_id)
    for name, value in (("MRS_AUTH_MODE", "accounts"), ("MRS_DATABASE_URL", url),
                        ("MRS_ALLOW_LOCAL_SQLITE", "true"), ("MRS_OFFLINE_CASES", "1"),
                        ("MRS_DEFAULT_VARIANT", "hypoglycemia_28m")):
        monkeypatch.setenv(name, value)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    import curriculum_runtime
    monkeypatch.setattr(curriculum_runtime, "assign_challenge", lambda *args, **kwargs: {
        "challenge_id": "R1-06", "reason": "test", "assignment_seed": 17,
        "competence_decision": "Not assessed automatically"})
    from resident_profile import ProfileStore
    ProfileStore(accounts).decline(token)
    at = AppTest.from_file(APP, default_timeout=120)
    at.session_state["_account_token"] = token
    at.run()
    return accounts, token, at


def begin_and_ask_to_close(at):
    """One timed decision, then the close without a destination: the warning."""
    widget(at.button, "Begin Encounter").click().run()
    widget(at.radio, "Encounter").set_value("Examine").run()
    widget(at.selectbox, "Examine").set_value("General appearance").run()
    widget(at.button, "Examine patient").click().run()
    widget(at.button, "Complete Encounter & Begin Review").click().run()
    assert not at.exception
    assert at.session_state["close_pending"] and "Finish now" in offered(at)


def stored(accounts, token, attempt_id):
    return next(a for a in accounts.list_attempts(token) if a["id"] == attempt_id)


def test_a_close_warning_left_open_does_not_open_the_next_encounter(page):
    accounts, token, at = page
    begin_and_ask_to_close(at)
    first = at.session_state["_attempt_id"]
    widget(at.button, "End this attempt without completing review").click().run()
    assert stored(accounts, token, first)["payload"]["session"]["close_pending"] is True

    widget(at.button, "Begin Encounter").click().run()
    assert not at.exception
    second = at.session_state["_attempt_id"]
    assert second != first and at.session_state["management_trace"] == []
    assert not at.session_state.get("close_pending")
    assert "Finish now" not in offered(at) and "Continue the encounter" not in offered(at)
    assert not stored(accounts, token, second)["payload"]["session"].get("close_pending")


def test_the_last_close_record_is_not_the_next_encounter_s(page):
    accounts, token, at = page
    begin_and_ask_to_close(at)
    widget(at.button, "Finish now").click().run()
    first = at.session_state["_attempt_id"]
    close = at.session_state["encounter_close"]
    assert close["kind"] == "clinical_close" and at.session_state["encounter_ended"]
    widget(at.button, "End this attempt without completing review").click().run()
    # The closed encounter keeps its own record.
    assert stored(accounts, token, first)["payload"]["session"]["encounter_close"] == close

    widget(at.button, "Begin Encounter").click().run()
    second = at.session_state["_attempt_id"]
    assert second != first
    assert at.session_state.get("encounter_close") is None
    assert stored(accounts, token, second)["payload"]["session"].get("encounter_close") is None
    # Abandoned before any close, it is saved with no close at all.
    widget(at.button, "End this attempt without completing review").click().run()
    abandoned = stored(accounts, token, second)
    assert abandoned["status"] == "abandoned"
    assert abandoned["payload"]["session"].get("encounter_close") is None


def test_a_resumed_encounter_keeps_its_own_close_warning(page):
    accounts, token, at = page
    begin_and_ask_to_close(at)
    first = at.session_state["_attempt_id"]
    widget(at.button, "Save & return to dashboard").click().run()
    assert not at.session_state.get("close_pending")

    widget(at.button, "Resume encounter").click().run()
    assert not at.exception
    assert at.session_state["_attempt_id"] == first
    assert at.session_state["close_pending"] and "Finish now" in offered(at)
