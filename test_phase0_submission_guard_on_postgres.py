"""Phase 0 closure: the submission guard on PostgreSQL, the engine of a deployed pilot (A-F).

Pre-pilot measurement safety, closure pass of 2026-10-06. The guard (0D) was proved on SQLite
through the real page; a deployed pilot keeps its encounters in PostgreSQL. These are the same
runs through the real page (AppTest) against a PostgreSQL database:

A. the order is written down and saved before it runs, runs once, and is saved as processed;
B. a second click on the same form, with the same words, runs nothing more;
C. a reload after the write-ahead and before the run executes the order once, on resume;
D. a reload after the run executes nothing again;
E. a run stopped part way is undone and runs again once; stopped twice, it is said, never run;
F. two sessions on one encounter: the store's revision check refuses the later save, says so,
   and no order is run twice in the database or lost without a word.

Runs only when ``MRS_TEST_POSTGRES_URL`` names a throwaway database: the fixture drops and
recreates its public schema. Never point it at a database whose data matters. Without it the
tests are skipped; ``test_phase0_submission_guard.py`` covers the same runs on SQLite.
"""
import os
import time
import uuid

import pytest

import submission_guard as guard
from account_store import AccountStore
from test_phase0_order_ledger import APP, submit
from test_phase0_submission_guard import (
    ORDER, _executed, _resume, _saved_session,
    test_a_reload_after_processing_re_executes_nothing as test_d_a_reload_after_processing_re_executes_nothing,
    test_a_reload_between_the_write_ahead_and_the_run_executes_once_on_resume as
    test_c_a_reload_between_the_write_ahead_and_the_run_executes_once_on_resume,
    test_a_run_stopped_part_way_is_undone_and_the_order_runs_once as
    test_e_a_run_stopped_part_way_is_undone_and_the_order_runs_once,
    test_a_run_stopped_twice_is_said_once_and_never_repeated as
    test_e_a_run_stopped_twice_is_said_once_and_never_repeated,
    test_a_second_click_on_the_same_form_executes_nothing_more as
    test_b_a_second_click_on_the_same_form_executes_nothing_more,
    test_the_order_is_in_the_database_before_it_runs as test_a_the_order_is_in_the_database_before_it_runs,
)

URL = os.environ.get("MRS_TEST_POSTGRES_URL", "")
pytestmark = pytest.mark.skipif(not URL.startswith("postgres"), reason="MRS_TEST_POSTGRES_URL is not set")


def _raw(sql):
    import psycopg
    with psycopg.connect(URL, autocommit=True) as connection:
        cursor = connection.execute(sql)
        return cursor.fetchall() if cursor.description else None


@pytest.fixture
def gi_bleed(monkeypatch):
    """A resident's encounter of the GI bleed case, kept in the throwaway PostgreSQL database."""
    from streamlit.testing.v1 import AppTest
    _raw("DROP SCHEMA public CASCADE")
    _raw("CREATE SCHEMA public")
    AccountStore.forget_schemas()
    accounts = AccountStore(URL)
    with accounts._transaction(write=True) as connection:
        user_id = uuid.uuid4().hex
        accounts._execute(connection, "INSERT INTO mrs_users VALUES (?, ?, ?, ?, ?, 1, ?)",
                          (user_id, "resident_test", "unused-fixture-hash", "resident", 3, int(time.time())))
        token = accounts._new_session(connection, user_id)
    for name, value in (("MRS_AUTH_MODE", "accounts"), ("MRS_DATABASE_URL", URL), ("MRS_OFFLINE_CASES", "1"),
                        ("MRS_DEFAULT_VARIANT", "gi_bleed_57m")):
        monkeypatch.setenv(name, value)
    monkeypatch.delenv("MRS_ALLOW_LOCAL_SQLITE", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    import curriculum_runtime
    monkeypatch.setattr(curriculum_runtime, "assign_challenge", lambda *args, **kwargs: {
        "challenge_id": "R2-05", "reason": "test", "assignment_seed": 17,
        "competence_decision": "Not assessed automatically"})
    from resident_profile import ProfileStore
    ProfileStore(accounts).decline(token)
    at = AppTest.from_file(APP, default_timeout=300)
    at.session_state["_account_token"] = token
    at.run()
    next(b for b in at.button if b.label == "Begin Encounter").click().run()
    assert not at.exception
    return at


def test_the_encounter_is_kept_in_postgresql(gi_bleed):
    assert gi_bleed.session_state["_attempt_id"]
    assert _raw("SELECT count(*) FROM mrs_attempts")[0][0] == 1
    assert URL.startswith("postgres") and "sqlite" not in os.environ["MRS_DATABASE_URL"]


def test_a_an_order_is_saved_before_it_runs_runs_once_and_is_saved_processed(gi_bleed):
    at = gi_bleed
    submit(at, ORDER)
    saved = _saved_session(at)
    [entry] = saved["submission_log"]
    assert entry["status"] == "processed" and entry["saved_before_run"] is True and entry["raw_text"] == ORDER
    assert len([e for e in saved["management_trace"] if e["execution_status"] == "executed"]) == 1
    assert len(_executed(at)) == 1


def test_f_two_sessions_on_one_encounter_never_run_an_order_twice_nor_lose_one_silently(gi_bleed):
    first = gi_bleed
    second = _resume(first.session_state["_account_token"])  # a second tab on the same encounter
    submit(first, ORDER)
    saved = _saved_session(first)
    assert len([e for e in saved["management_trace"] if e["execution_status"] == "executed"]) == 1
    # The second tab still holds the revision before the first tab's save. Its order is refused
    # by the store, and the page says so; nothing of it reaches the database.
    other = "Give 500 mL LR. Reassess blood pressure in 10 minutes."
    next(r for r in second.radio if r.label == "Encounter").set_value("Treat").run()
    next(a for a in second.text_area if a.label == "Enter your clinical reasoning and/or actions").set_value(other)
    next(b for b in second.button if b.label == "Send").click().run()
    shown = " ".join(str(element.value) for element in second.error)
    assert "This encounter changed in another session" in shown
    after = _saved_session(first)
    assert after["submission_log"] == saved["submission_log"]
    assert after["management_trace"] == saved["management_trace"]
    assert not any(entry.get("raw_text") == other for entry in after["submission_log"])
    # Reopened, the second tab has the first tab's order once, and its own is not there to run twice.
    again = _resume(first.session_state["_account_token"])
    assert len(_executed(again)) == 1
    assert [entry["raw_text"] for entry in guard.log(again.session_state)] == [ORDER]


def test_an_order_written_after_an_answer_is_saved_with_it_and_runs_once(gi_bleed):
    """F0-12 on PostgreSQL: the order written after the answer is saved with the answer, then runs once."""
    at = gi_bleed
    submit(at, "I think this is an upper GI bleed with haemorrhagic shock. My priority is restoring perfusion. "
               "I expect the blood pressure to rise. Give normal saline. Reassess blood pressure in 10 minutes.")
    assert at.session_state.get("pending_action")
    submit(at, "1000 mL, and give 500 mL LR.")
    saved = _saved_session(at)
    derived = [entry for entry in saved["submission_log"] if entry.get("derived_from")]
    assert len(derived) == 1 and derived[0]["status"] == "processed" and derived[0]["raw_text"] == "give 500 mL LR."
    assert [entry["status"] for entry in saved["submission_log"]] == ["processed"] * len(saved["submission_log"])
    orders = [order for order in saved["order_ledger"] if order.get("derived_from")]
    assert len(orders) == 1 and orders[0]["written_at_min"] == 0
    again = _resume(at.session_state["_account_token"])
    assert [entry["status"] for entry in guard.log(again.session_state)] == ["processed"] * len(saved["submission_log"])
    assert again.session_state["order_ledger"] == saved["order_ledger"]
