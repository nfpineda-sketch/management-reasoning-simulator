"""A closed encounter is examined, timed and traced no further.

2026-09-25, found while closing the twenty-scenario batch. After "Complete
Encounter & Begin Review" the Examine panel still examined: each examination
added a decision to the saved Management Trace and moved the clinical clock --
and with it the closing minute the rubric's screening reads, which decides
whether a domain's window had opened. The ECG button still acquired new
tracings. Talking and treating already ended with the encounter; examining and
acquiring now do too. What was acquired before the close stays viewable.
"""
import time
import uuid
from copy import deepcopy
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from account_store import AccountStore

APP = str(Path(__file__).with_name("app.py"))


def widget(elements, label):
    return next(item for item in elements if item.label == label)


@pytest.fixture
def closed(tmp_path, monkeypatch):
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
    widget(at.button, "Begin Encounter").click().run()
    assert at.session_state["state"]["encounter_spec"]["variant_id"] == "hypoglycemia_28m"
    widget(at.button, "ECG").click().run()
    widget(at.radio, "Encounter").set_value("Examine").run()
    widget(at.selectbox, "Examine").set_value("General appearance").run()
    widget(at.button, "Examine patient").click().run()
    assert not at.exception
    widget(at.button, "Complete Encounter & Begin Review").click().run()
    assert not at.exception and at.session_state["encounter_ended"]
    return accounts, at


def test_examining_before_the_close_is_a_timed_decision(closed):
    """The premise: examining is traced and costs clinical time, so it matters."""
    _, at = closed
    assert [entry.get("learner_input") for entry in at.session_state["management_trace"]] == [
        "Examine: General appearance"]
    assert at.session_state["state"]["sim_time"] > 0


def test_after_the_close_nothing_is_examined_or_acquired(closed):
    accounts, at = closed
    trace = deepcopy(at.session_state["management_trace"])
    state = deepcopy(at.session_state["state"])
    events = len(at.session_state["events"])
    widget(at.radio, "Encounter").set_value("Examine").run()
    assert not at.exception
    offered = {button.label for button in at.button}
    assert "Examine patient" not in offered and "ECG" not in offered
    assert at.session_state["management_trace"] == trace
    assert at.session_state["state"] == state
    assert len(at.session_state["events"]) == events
    # The tracing acquired before the close is still there to look at.
    widget(at.button, "View recording")
    # And what is saved closes where the resident closed it.
    from rubric_screening import facts
    [attempt] = [a for a in accounts.list_attempts(at.session_state["_account_token"])]
    record = accounts.get_attempt(at.session_state["_account_token"], attempt["id"])
    assert facts(record, "hypoglycemia_28m")["closed_at"] == state["sim_time"]
