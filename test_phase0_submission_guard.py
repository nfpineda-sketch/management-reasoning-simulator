"""Phase 0 (0D): a submission is written down before it runs, runs once, and is never lost.

Pre-pilot measurement safety, 2026-10-06. The clinical engine audit (§8 G) found that a
zero-gap double click on Send lost the order in a real browser, and that nothing in the
order path could tell a repeat from a new order. In Streamlit 1.64 a click arriving while
the page runs stops it at the next drawing call or session-state access, so a run can be
stopped anywhere in the processing of an order. These tests drive the guard directly and
through the real page (AppTest): a repeated click of the same form, the write-ahead before
a run that fails, a run stopped part way (undone and run once), a run stopped twice (said,
never repeated), a reload after processing, and a reload after the write-ahead and before
the run (resume). The real browser runs are in the Phase 0 report.
"""
import tomllib
from pathlib import Path

import pytest

import submission_guard as guard
from test_phase0_order_ledger import _encounter, submit

ORDER = ("I think this is an upper GI bleed with haemorrhagic shock. My priority is restoring perfusion. "
         "I expect the blood pressure to rise. Give 1 L LR. Reassess blood pressure in 10 minutes.")


def test_one_run_at_a_time_per_browser_session():
    # With fast reruns, a second click starts a second copy of the page beside the first.
    config = tomllib.loads(Path(__file__).with_name(".streamlit").joinpath("config.toml").read_text())
    assert config["runner"]["fastReruns"] is False


# --- the guard itself -----------------------------------------------------------------
def test_one_form_and_one_text_are_one_submission():
    session = {}
    form = guard.nonce(session)
    session[guard.text_key(form)] = "Give 1 L LR."
    first = guard.capture(session, form)
    assert first and first["status"] == "received" and first["id"] == form
    # The next form has a fresh id; a second click on the old one repeats the same text.
    assert guard.nonce(session) != form
    assert guard.capture(session, form) is None
    assert len(guard.log(session)) == 1 and guard.log(session)[0]["duplicates"] == 1
    # An empty box writes nothing.
    other = guard.nonce(session)
    assert guard.capture(session, other) is None


def test_a_different_text_on_the_old_form_is_a_new_submission_not_a_lost_one():
    session = {}
    form = guard.nonce(session)
    session[guard.text_key(form)] = "Give 1 L LR."
    guard.capture(session, form)
    session[guard.text_key(form)] = "Give 2 units PRBC."
    second = guard.capture(session, form)
    assert second and second["id"] != form and second["raw_text"] == "Give 2 units PRBC."
    assert [entry["status"] for entry in guard.log(session)] == ["received", "received"]


def test_a_stopped_run_is_undone_and_runs_again_once_then_is_said():
    fields = ("state", "events", "management_trace", guard.LOG_KEY)
    session = {"state": {"sim_time": 5}, "events": [], "management_trace": []}
    form = guard.nonce(session)
    session[guard.text_key(form)] = "Give 1 L LR."
    entry = guard.capture(session, form)
    assert entry["received_at_min"] == 5 and guard.waiting(session)
    guard.begin(session, entry, fields=fields)
    assert guard.pending(session) == [] and entry["status"] == "processing"
    # The run applies part of the order and is stopped: the next run puts it all back.
    session["state"]["sim_time"] = 25
    session["management_trace"].append({"half": True})
    found = guard.recover(session, fields)
    assert [e["id"] for e in found["retried"]] == [entry["id"]] and found["interrupted"] == []
    assert session["state"] == {"sim_time": 5} and session["management_trace"] == []
    assert entry["status"] == "received" and entry["retries"] == 1
    assert guard.pending(session) == [entry]
    # Stopped again: undone, and said once; it never runs again.
    guard.begin(session, entry, fields=fields)
    session["state"]["sim_time"] = 40
    found = guard.recover(session, fields)
    assert found["retried"] == [] and [e["id"] for e in found["interrupted"]] == [entry["id"]]
    assert session["state"] == {"sim_time": 5} and entry["status"] == "interrupted"
    assert not guard.waiting(session) and guard.pending(session) == []
    assert [e["id"] for e in guard.notices(session)] == [entry["id"]]
    assert guard.notices(session) == []
    assert "nothing of it was applied" in guard.interrupted_message(entry)


def test_the_write_ahead_is_recorded_only_when_the_store_took_it():
    session = {}
    form = guard.nonce(session)
    session[guard.text_key(form)] = "Give 1 L LR."
    entry = guard.capture(session, form)
    assert guard.write_ahead(session, lambda: RuntimeError("changed in another session")) == []
    assert "saved_before_run" not in entry
    assert guard.write_ahead(session, lambda: None) == [entry] and entry["saved_before_run"] is True
    assert guard.write_ahead(session, lambda: None) == []  # nothing left to save


# --- the real page --------------------------------------------------------------------
@pytest.fixture
def gi_bleed(tmp_path, monkeypatch):
    return _encounter(tmp_path, monkeypatch, "gi_bleed_57m", "R2-05")


def _executed(at):
    return [e for e in at.session_state["management_trace"] if e["execution_status"] == "executed"]


def test_a_second_click_on_the_same_form_executes_nothing_more(gi_bleed):
    at = gi_bleed
    submit(at, ORDER)
    entry = guard.log(at.session_state)[-1]
    assert entry["status"] == "processed"
    assert len(_executed(at)) == 1
    minute = at.session_state["state"]["sim_time"]
    delivered = at.session_state["state"]["family_state"].get("pending_fluid_ml", 0)
    # The double click's second request: the same form id with the same words.
    at.session_state[guard.text_key(entry["form_id"])] = ORDER
    assert guard.capture(at.session_state, entry["form_id"]) is None
    at.run()
    assert not at.exception
    assert len(_executed(at)) == 1
    assert at.session_state["state"]["sim_time"] == minute
    assert at.session_state["state"]["family_state"].get("pending_fluid_ml", 0) == delivered
    assert guard.log(at.session_state)[-1]["duplicates"] == 1


def test_the_order_is_in_the_database_before_it_runs(gi_bleed, monkeypatch):
    import order_pipeline
    from test_phase0_order_ledger import APP  # noqa: F401
    at = gi_bleed
    real_open_turn = order_pipeline.open_turn

    def failing_open_turn(*args, **kwargs):
        raise RuntimeError("the processing failed part way")
    monkeypatch.setattr(order_pipeline, "open_turn", failing_open_turn)
    next(r for r in at.radio if r.label == "Encounter").set_value("Treat").run()
    next(a for a in at.text_area if a.label == "Enter your clinical reasoning and/or actions").set_value(ORDER)
    next(b for b in at.button if b.label == "Send").click().run()
    assert at.exception, "the processing failed"
    saved = _saved_session(at)
    assert [(e["status"], e["raw_text"]) for e in saved["submission_log"]] == [("received", ORDER)]
    assert not saved.get("management_trace")
    # The page that failed is gone (a reload); the encounter is resumed and the order runs once.
    monkeypatch.setattr(order_pipeline, "open_turn", real_open_turn)
    again = _resume(at.session_state["_account_token"])
    assert len(_executed(again)) == 1
    assert [e["status"] for e in guard.log(again.session_state)] == ["processed"]
    again.run()
    assert len(_executed(again)) == 1


def test_a_run_stopped_part_way_is_undone_and_the_order_runs_once(gi_bleed):
    from curriculum_runtime import SESSION_FIELDS
    at = gi_bleed
    start = at.session_state["state"]["sim_time"]
    form = guard.nonce(at.session_state)
    at.session_state[guard.text_key(form)] = ORDER
    entry = guard.capture(at.session_state, form)
    guard.begin(at.session_state, entry, fields=SESSION_FIELDS)
    # What a stopped run had applied before a click stopped it.
    at.session_state["state"]["sim_time"] = start + 30
    at.session_state["management_trace"].append({"execution_status": "executed", "half_applied": True})
    at.run()
    assert not at.exception
    trace = at.session_state["management_trace"]
    assert [e for e in trace if e.get("half_applied")] == []
    assert len(_executed(at)) == 1
    assert at.session_state["state"]["sim_time"] == start + 10
    written = guard.log(at.session_state)[-1]
    assert written["status"] == "processed" and written["retries"] == 1
    assert trace[-1]["submission"]["retried_after_interruption"] == 1


def test_a_run_stopped_twice_is_said_once_and_never_repeated(gi_bleed):
    from curriculum_runtime import SESSION_FIELDS
    at = gi_bleed
    start = at.session_state["state"]["sim_time"]
    form = guard.nonce(at.session_state)
    at.session_state[guard.text_key(form)] = ORDER
    entry = guard.capture(at.session_state, form)
    entry["retries"] = guard.MAX_RETRIES  # already run again once after a stop
    guard.begin(at.session_state, entry, fields=SESSION_FIELDS)
    at.session_state["state"]["sim_time"] = start + 30
    at.run()
    assert not at.exception
    assert _executed(at) == [] and at.session_state["state"]["sim_time"] == start
    texts = [event["text"] for event in at.session_state["events"]]
    said = [text for text in texts if "was interrupted while it was being processed" in text]
    assert len(said) == 1 and "nothing of it was applied" in said[0]
    assert guard.log(at.session_state)[-1]["status"] == "interrupted"
    at.run()
    texts = [event["text"] for event in at.session_state["events"]]
    assert len([t for t in texts if "was interrupted while it was being processed" in t]) == 1
    assert _executed(at) == []


def test_the_send_button_is_disabled_while_a_submission_waits(gi_bleed, monkeypatch):
    at = gi_bleed
    form = guard.nonce(at.session_state)
    at.session_state[guard.text_key(form)] = ORDER
    guard.capture(at.session_state, form)
    import submission_guard
    # Draw the page without processing it, to see the form as the browser sees it while the
    # submission waits: the received entry is left pending.
    monkeypatch.setattr(submission_guard, "pending", lambda session: [])
    at.run()
    send = next(b for b in at.button if b.label == "Send")
    assert send.disabled


def _resume(token):
    from streamlit.testing.v1 import AppTest
    from test_phase0_order_ledger import APP
    at = AppTest.from_file(APP, default_timeout=180)
    at.session_state["_account_token"] = token
    at.run()
    next(b for b in at.button if b.label == "Resume encounter").click().run()
    assert not at.exception
    return at


def _saved_session(at):
    import os
    from account_store import AccountStore
    store = AccountStore(os.environ["MRS_DATABASE_URL"], allow_sqlite=True)
    record = store.get_attempt(at.session_state["_account_token"], at.session_state["_attempt_id"])
    return (record.get("payload") or {}).get("session") or {}


def test_a_reload_after_processing_re_executes_nothing(gi_bleed):
    at = gi_bleed
    submit(at, ORDER)
    token = at.session_state["_account_token"]
    minute, trace = at.session_state["state"]["sim_time"], len(at.session_state["management_trace"])
    again = _resume(token)
    assert again.session_state["state"]["sim_time"] == minute
    assert len(again.session_state["management_trace"]) == trace
    assert [e["status"] for e in guard.log(again.session_state)] == ["processed"]
    again.run()
    assert len(again.session_state["management_trace"]) == trace


def test_a_reload_between_the_write_ahead_and_the_run_executes_once_on_resume(gi_bleed):
    import os
    from copy import deepcopy
    from account_store import AccountStore
    from curriculum_runtime import PAYLOAD_VERSION, SESSION_FIELDS, evidence_summary
    at = gi_bleed
    # The Send callback wrote the order down and saved it (the write-ahead); the browser
    # reloaded before the run executed it. The database holds a received entry.
    form = guard.nonce(at.session_state)
    at.session_state[guard.text_key(form)] = ORDER
    assert guard.capture(at.session_state, form)
    payload = {"schema_version": PAYLOAD_VERSION,
               "session": {key: deepcopy(at.session_state[key]) for key in SESSION_FIELDS if key in at.session_state}}
    payload["evidence"] = evidence_summary(payload)
    store = AccountStore(os.environ["MRS_DATABASE_URL"], allow_sqlite=True)
    token = at.session_state["_account_token"]
    store.save_attempt(token, at.session_state["_attempt_id"], payload, "active",
                       expected_revision=at.session_state["_attempt_revision"])
    assert _executed(at) == []
    # A new browser session resumes the encounter: the order runs once, and only once.
    again = _resume(token)
    assert len(_executed(again)) == 1
    assert [e["status"] for e in guard.log(again.session_state)] == ["processed"]
    again.run()
    assert len(_executed(again)) == 1
