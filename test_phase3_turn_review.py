"""P3-276: the repairs the independent review of the transactional turn required, each proved on the REAL page (Streamlit AppTest) against the two development cases.

H1  a clock turn the authority never judged was applied (and the session went on) when the shadow flag disappeared from the process;
M1  an encounter whose provenance anchor was deleted while its site, record and artifact were alive was allowed to continue;
M2  a zero-minute turn that the store could not write stayed in the artifact as a turn the encounter never had;
L2  covered by the unit tests (a turn left open by an earlier run);
and the routes the review found without a page test of their own (the history topic).

Nothing here changes a clinical value: every assertion is about what the real encounter is, or is not, after a refused turn.
"""
from __future__ import annotations

import json

import pytest

import runtime_authority as ra
import runtime_authority_session as se
import runtime_authority_turn as tu
import runtime_shadow as rs
import test_phase3_pair_page as page
import test_phase3_stop_page as stop
import test_phase3_turn_page as turn_page

CASES = page.CASES


def _topic(at):
    """The history-topic route: open the Talk mode, click 'Ask about this topic'."""
    page._mode(at, "Talk")
    next(b for b in at.button if b.label == "Ask about this topic").click().run()
    assert not at.exception, [str(item.value)[:300] for item in at.exception]


def _nothing_drawn(at):
    controls = stop._controls(at)
    assert not (controls["ask_box"] or controls["order_box"] or controls["examine"] or controls["ecg"] or controls["send"] or controls["ask_button"] or controls["complete_enabled"]), controls


# -- H1: the shadow flag is part of the configuration the experiment needs ------------------------------------------------------------------------------------

@pytest.mark.parametrize("case", CASES)
def test_v1_the_shadow_flag_disappearing_from_the_process_stops_the_session_and_no_turn_runs(monkeypatch, tmp_path, case):
    """Without the shadow the site is never shown a clock turn, so a configuration that lost it can no longer judge anything: the guard says so on every route and nothing is drawn."""
    at, site = turn_page._two_commits(monkeypatch, tmp_path, case)
    committed, minute, anchor = list(site.minutes_committed), page._minute(at), turn_page._anchor(at)
    monkeypatch.delenv(rs.FLAG)
    at.run()
    assert not at.exception
    decision = se.continuation_guard(at.session_state, at.session_state["state"])
    assert decision["allowed"] is False and decision["lifecycle"] == se.INVALID_FOR_CONTINUATION and decision["stop_class"] == se.STOP_CONFIGURATION, decision
    assert decision["legacy_fallback_allowed"] is False
    _nothing_drawn(at)
    before = turn_page._encounter(at)
    for attempt in (lambda: page._ask(at, "Where does it hurt?"), lambda: page._examine(at), lambda: page._order(at, "Reassess in 10 minutes.")):
        with pytest.raises(StopIteration):
            attempt()
    assert turn_page._encounter(at) == before and page._minute(at) == minute and list(site.minutes_committed) == committed and turn_page._anchor(at) == anchor


def test_v2_a_clock_turn_the_site_never_judged_is_not_applied_even_when_the_guard_lets_it_start(monkeypatch, tmp_path):
    """The second layer, independent of the guard: the site is made to ignore the clock route (a hook that is not firing), the configuration is intact, and the question runs -- on a working copy.
    The copy's clock moved and the site recorded nothing, so it is DISCARDED, the real encounter is exactly what it was, and the session stops with a reason that says why."""
    at, site = turn_page._two_commits(monkeypatch, tmp_path, CASES[0])
    committed, last, minute, anchor = list(site.minutes_committed), max(site.minutes_committed), page._minute(at), turn_page._anchor(at)
    real_minute = ra.AuthoritySite.minute

    def deaf_to_the_clock(self, before, after, session, ran, submission_id=None, route=ra.ORDER_TURN, settled=None):
        if route == "clinical_time_outside_an_order_turn":
            return None                                                  # the site is never shown the turn: nothing recorded, nothing committed, nothing refused
        return real_minute(self, before, after, session, ran, submission_id, route, settled)

    monkeypatch.setattr(ra.AuthoritySite, "minute", deaf_to_the_clock)
    events_before, trace_before = len(at.session_state["events"]), len(at.session_state["management_trace"])
    before = turn_page._encounter(at)
    page._ask(at, "Where does it hurt?")
    turn_page._refused_turn_proofs(at, site, before=before, minute=minute, committed=committed, last=last, anchor=anchor)
    assert len(at.session_state["events"]) == events_before and len(at.session_state["management_trace"]) == trace_before, "no 'you' line, no answer and no trace entry"
    record = stop._record(at)
    assert record["lifecycle"] == se.INVALID_FOR_CONTINUATION and record["halt_reason"].startswith(ra.TURN_NOT_JUDGED), record["halt_reason"]
    assert record["stop_class"] == se.STOP_INTERNAL and record["legacy_fallback_allowed"] is False and record["last_authoritative_minute"] == last
    monkeypatch.setattr(ra.AuthoritySite, "minute", real_minute)
    stop._assert_stopped(at, last_authoritative=last, stop_class=se.STOP_INTERNAL)
    stop._blocked_attempts(at, monkeypatch)


# -- M1: an anchor deleted while everything else is alive ---------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("case", CASES)
def test_v3_an_encounter_whose_anchor_was_deleted_while_its_site_is_alive_is_stopped(monkeypatch, tmp_path, case):
    """'No anchor' is not 'authority never occurred': the site, the record and the artifact all say authority began, and the state that must carry the mark does not."""
    at, site = turn_page._two_commits(monkeypatch, tmp_path, case)
    committed, minute = list(site.minutes_committed), page._minute(at)
    at.session_state["state"].pop(ra.PROVENANCE_ANCHOR_KEY)
    decision = se.continuation_guard(at.session_state, at.session_state["state"])
    assert decision["allowed"] is False and decision["stop_class"] == se.STOP_PROVENANCE and decision["legacy_fallback_allowed"] is False, decision
    assert ra.PROVENANCE_LOST in decision["reason"]
    at.run()
    assert not at.exception
    _nothing_drawn(at)
    stored = at.session_state[se.SESSION_KEY]
    assert stored["lifecycle"] == se.INVALID_FOR_CONTINUATION and stored["stop_class"] == se.STOP_PROVENANCE, "the stop is recorded where a reopened copy will find it"
    before = turn_page._encounter(at)
    for attempt in (lambda: page._ask(at, "Where does it hurt?"), lambda: page._order(at, "Reassess in 10 minutes.")):
        with pytest.raises(StopIteration):
            attempt()
    assert turn_page._encounter(at) == before and page._minute(at) == minute and list(site.minutes_committed) == committed


def test_v3b_an_encounter_that_never_had_authority_is_not_stopped_for_having_no_anchor(monkeypatch, tmp_path):
    """The other side of M1: a session before its first commit has no anchor and nothing says authority began, so the legacy encounter continues exactly as before."""
    at = stop._open(monkeypatch, tmp_path, CASES[0])
    assert ra.PROVENANCE_ANCHOR_KEY not in at.session_state["state"]
    assert se.continuation_guard(at.session_state, at.session_state["state"])["allowed"] is True
    page._ask(at, "What brought you in today?")
    assert not at.exception


# -- M2: a quiet turn the store could not write ------------------------------------------------------------------------------------------------------------

def test_v4_a_zero_minute_turn_the_store_cannot_write_is_not_in_the_artifact_and_not_in_the_encounter(monkeypatch, tmp_path):
    at, site = turn_page._two_commits(monkeypatch, tmp_path, CASES[0])
    committed, last, minute, anchor = list(site.minutes_committed), max(site.minutes_committed), page._minute(at), turn_page._anchor(at)
    quiet_before = [dict(item) for item in site.no_advance_turns]
    stop._inject_persistence(monkeypatch)
    before = turn_page._execute(at, "Place an IV line.")
    turn_page._refused_turn_proofs(at, site, before=before, minute=minute, committed=committed, last=last, anchor=anchor)
    assert [dict(item) for item in site.no_advance_turns] == quiet_before, "the artifact lists no turn the encounter never had"
    assert len(site.artifact().get("no_advance_turns", [])) == len(quiet_before), "and the artifact body agrees with the site"
    record = stop._record(at)
    assert record["lifecycle"] == se.INVALID_FOR_CONTINUATION and record["halt_reason"].startswith(ra.ARTIFACT_PERSISTENCE_FAILED), record["halt_reason"]
    assert "zero-minute turn was not durable" in record["halt_reason"], "and the refusal says what was withdrawn"
    assert record["stop_class"] == se.STOP_PERSISTENCE and record["last_authoritative_minute"] == last
    assert [item for item in site.artifact()["minutes"] if item.get("outcome") == ra.ABORTED], "the refused turn is named as ABORTED"


def test_v4b_a_zero_minute_turn_that_was_written_stays_in_the_artifact(monkeypatch, tmp_path):
    """The other side of M2: a quiet turn the store DID write is durable and is never withdrawn."""
    at, site = turn_page._two_commits(monkeypatch, tmp_path, CASES[0])
    quiet_before = len(site.no_advance_turns)
    page._order(at, "Place an IV line.")
    assert not site.halted, site.halt_reason
    assert len(site.no_advance_turns) == quiet_before + 1, "the zero-minute turn is recorded in the artifact"
    assert getattr(site, "_unpersisted_quiet", False) is False, "a written turn is no longer pending"
    assert json.loads(json.dumps(site.artifact()["no_advance_turns"], default=str))[-1]["outcome"] == ra.NO_ADVANCE_TURN


# -- the history topic: a clock route with no page test of its own -------------------------------------------------------------------------------------------

def test_v5_a_refused_history_topic_never_happened_to_the_real_encounter(monkeypatch, tmp_path):
    at, site = turn_page._two_commits(monkeypatch, tmp_path, CASES[0])
    committed, last, minute, anchor = list(site.minutes_committed), max(site.minutes_committed), page._minute(at), turn_page._anchor(at)
    events_before, trace_before = len(at.session_state["events"]), len(at.session_state["management_trace"])
    stop._inject_validation(monkeypatch)
    before = turn_page._encounter(at)
    _topic(at)
    turn_page._refused_turn_proofs(at, site, before=before, minute=minute, committed=committed, last=last, anchor=anchor)
    assert len(at.session_state["events"]) == events_before and len(at.session_state["management_trace"]) == trace_before, "no 'Ask about' line, no answer and no trace entry"
    record = stop._record(at)
    assert record["lifecycle"] == se.INVALID_FOR_CONTINUATION and record["stop_class"] == se.STOP_VALIDATION and record["last_authoritative_minute"] == last


# -- M2, the other edge: a durable zero-minute turn is never withdrawn by a LATER failed write ------------------------------------------------------------

def test_v4c_a_zero_minute_turn_that_was_durable_stays_when_a_later_write_of_the_same_turn_fails(monkeypatch, tmp_path):
    """The quiet turn was written (durable); the write that follows it (the settlement of its classes) fails. A durable record is never taken back (faculty decision F): only what was in memory
    alone when the store failed is withdrawn."""
    import runtime_authority_store as authority_store
    at, site = turn_page._two_commits(monkeypatch, tmp_path, CASES[0])
    quiet_before = len(site.no_advance_turns)
    real_persist = authority_store.persist

    def fails_once_the_turn_is_durable(artifact, environ=None):
        quiet = list(dict(artifact).get("no_advance_turns") or [])
        if len(quiet) > quiet_before and quiet[-1].get("provenance_settled"):
            return {"stored": False, "why": "STORE_ERROR OSError: disk full"}
        return real_persist(artifact, environ=environ)

    monkeypatch.setattr(authority_store, "persist", fails_once_the_turn_is_durable)
    page._order(at, "Place an IV line.")
    assert site.halted and site.halt_reason.startswith(ra.ARTIFACT_PERSISTENCE_FAILED), site.halt_reason
    assert "zero-minute turn was not durable" not in site.halt_reason, "nothing was withdrawn: the turn had been written"
    assert len(site.no_advance_turns) == quiet_before + 1, "the durable quiet turn is still in the artifact"


# -- L2: a turn an earlier page run left open ---------------------------------------------------------------------------------------------------------------

def test_v6_a_turn_left_open_by_an_earlier_page_run_is_closed_when_the_next_run_starts(monkeypatch, tmp_path):
    at, site = turn_page._two_commits(monkeypatch, tmp_path, CASES[0])
    minute, committed = page._minute(at), list(site.minutes_committed)
    original = at.session_state["state"]
    turn = tu.begin(at.session_state, route="killed")
    assert isinstance(turn, tu.AuthorityTurn)
    turn.__enter__()                                                   # the earlier run died right here: the working copies are the encounter and the turn is still open
    at.session_state["state"]["sim_time"] = minute + 2                 # ... and the copy had moved the clock, unjudged
    assert tu.TURN_KEY in at.session_state and at.session_state["state"] is not original
    at.run()
    assert not at.exception
    assert tu.TURN_KEY not in at.session_state, "the new run closed the stale turn"
    assert at.session_state["state"] is original and page._minute(at) == minute, "with its own verdict: the unjudged copy was dropped and the real encounter is back"
    assert list(site.minutes_committed) == committed and not site.halted
    page._ask(at, "Where does it hurt?")                               # and the next turn is an ordinary, transactional one
    assert not site.halted and page._minute(at) > minute and tu.TURN_KEY not in at.session_state


def test_v6b_the_page_closes_a_stale_turn_before_it_asks_the_guard():
    """Static tripwire for L2: the reset is the first thing the workspace does with the authority, so no later statement of the run sees a stale turn."""
    import re
    source = open(page.APP, encoding="utf-8").read()
    body = source[source.index("def _clinical_encounter_workspace():"):]
    end = body.find("\ndef ", 10)
    body = body if end < 0 else body[:end]
    assert "_authority_turn_reset()" in body, "the workspace never closes a stale turn"
    assert body.index("_authority_turn_reset()") < body.index("_authority_continuation()"), "the reset must come before the guard is asked"
    assert len(re.findall(r"\b_authority_turn_reset\(\)", source)) == 2, "one definition and one call: a second call would hide a stale turn from the check that follows"
