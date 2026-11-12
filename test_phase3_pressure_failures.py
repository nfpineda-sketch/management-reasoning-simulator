"""P3-244, P3-244A and P3-245/245A: failure AFTER the first real commit, and the collapse boundary and window, on the real page.

TEST-SIDE. Each test plays the real page with the authorized development configuration (the real approved pressure snapshot and the real grant), lets the first real pressure
commit happen, injects ONE fault and then checks what the experiment does. Required in every case:

* the experiment is INVALID_FOR_CONTINUATION (``mixed_trajectory`` declared, the artifact and the faculty status say so), no later minute is ever authoritative, and the failing
  minute committed nothing and carries a rollback record;
* there is NO SILENT return to the legacy pressure: the encounter continues on the legacy engine, which is the only thing that can run it, and the experiment's own record
  says from which minute on the pressure is legacy and why. This is an EXPERIMENT termination, never a patient death: no resident-visible word changes and no terminal state exists;
* a fault BEFORE the first commit leaves the legacy encounter exactly as if the experiment had never been asked for (EXPERIMENT_HALTED, authority never began).
"""
import json
from copy import deepcopy

import pytest

import runtime_authority as ra
import runtime_minute_validation as validation
import runtime_pressure_grant as grants
import runtime_shadow_evidence as ev
import test_phase3_pair_page as page

CASES = page.CASES
FORBIDDEN_WORDS = ("INVALID_FOR_CONTINUATION", "EXPERIMENT_HALTED", "COLLAPSE_BOUNDARY", "ESTABLISHED", "EXPERIMENT_WINDOW", "REAL_DEVELOPMENT", "grant", "overlay")


@pytest.fixture
def real_page(monkeypatch, tmp_path):
    def open_it(case):
        at = page._open(monkeypatch, case, shadow=True, dry=False, authority=str(tmp_path / "store"))
        return at
    return open_it


def _site(at):
    return at.session_state.get(ra.SITE_KEY)


def _first_commit(at):
    page._ask(at, "What brought you in today?")
    site = _site(at)
    assert site is not None and site.minutes_committed and not site.halted, (site and site.halt_reason)
    return site


def _assert_invalid_after_a_commit(at, site, *, committed_before, kind, rederived=None):
    artifact = site.artifact()
    assert site.halted and site.halt_reason.startswith(kind), (kind, site.halt_reason)
    assert list(site.minutes_committed) == list(committed_before), "the failing turn committed nothing and no later minute is authoritative"
    status = ra.authority_status(at.session_state)
    assert status["halted"] and status["invalid_for_continuation"] == ra.INVALID_FOR_CONTINUATION and status["mixed_trajectory"] is True and status["experiment_state"] == ra.EXPERIMENT_HALTED
    assert artifact["mixed_trajectory"] is True and artifact["authority_began"] is True and artifact["experiment_outcome"] == "INVALID_FOR_CONTINUATION"
    assert artifact["post_commit_policy"]["silent_fallback_to_the_legacy_engine"] is False and artifact["post_commit_policy"]["is_patient_death"] is False
    failed = next(record for record in site.records if record["outcome"] == ra.ABORTED)
    assert failed["committed"] == [] and failed["rollback"] and failed["rollback"]["committed"] == [] and failed["failure_reason"].startswith(kind)
    # the declared (not silent) consequence: from the failed minute on, the pressure on the page is the legacy engine's, and the record has it
    observable = at.session_state["state"]["observable"]
    if failed.get("legacy_counterfactual"):
        assert (observable["sbp"], observable["dbp"]) == (failed["legacy_counterfactual"]["sbp"], failed["legacy_counterfactual"]["dbp"]) or ra.pressure_point(observable) != {}
    screen = page._screen(at)
    assert not any(word in screen for word in FORBIDDEN_WORDS), "no experiment word and no terminal word reaches the resident"
    assert observable.get("pulse_present", True) is not False and "terminal" not in json.dumps(artifact["post_commit_policy"]).lower().replace("is_a_terminal_state", "")
    assert ra.verify_artifact(artifact)["complete"] and ra.artifact_class(artifact) == ra.REAL_PRESSURE_LABEL
    replay = ra.replay_site_artifact(artifact)
    assert replay["halt_reason_replay"]["applicable"] and replay["halt_reason_replay"]["kind"].startswith(kind)
    if rederived is not None:
        assert replay["halt_reason_replay"]["rederived"] is rederived and replay["halt_reason_replay"]["reproduces"], replay["halt_reason_replay"]
    return artifact


def _nothing_more_commits(at, site):
    """ADAPTED in P3-253 (FD-STOP-02/03): after the halt the experimental session is STOPPED -- no question box and no order box is drawn, the legacy engine does not run the encounter on,
    and no minute is ever committed again. (Before the effective stop this ran a question and an order on the legacy engine and checked only that nothing committed.)"""
    held = list(site.minutes_committed)
    recorded = len(site.records)
    stopped = json.dumps(at.session_state["state"], sort_keys=True, default=str)
    with pytest.raises(StopIteration):
        page._ask(at, "Where does it hurt?")
    with pytest.raises(StopIteration):
        page._order(at, "Reassess in 10 minutes.")
    assert list(site.minutes_committed) == held, "after the halt no minute is ever committed again"
    assert json.dumps(at.session_state["state"], sort_keys=True, default=str) == stopped, "the stopped session does not advance"
    assert len(site.records) == recorded and site.halted, "the stopped session is not even offered to the site again: no new record, no SITE_HALTED turn (that record existed only while the legacy engine ran the encounter on)"
    assert ra.authority_status(at.session_state)["halted"] is True


@pytest.mark.parametrize("case", CASES)
def test_f1_an_unsupported_action_after_a_commit_invalidates_the_experiment(real_page, case):
    at = real_page(case)
    site = _first_commit(at)
    held = list(site.minutes_committed)
    page._order(at, page.UNSUPPORTED)
    _assert_invalid_after_a_commit(at, site, committed_before=held, kind=ra.UNSUPPORTED_AUTHORITY_ACTION, rederived=True)
    _nothing_more_commits(at, site)


def test_f2_a_lineage_mismatch_after_a_commit_stops_the_experiment_at_the_gate_and_commits_nothing(real_page, monkeypatch):
    at = real_page(CASES[0])
    site = _first_commit(at)
    held = list(site.minutes_committed)
    monkeypatch.setattr(ev, "core_lineage_ok", lambda: False)
    page._order(at, "Reassess in 10 minutes.")
    artifact = _assert_invalid_after_a_commit(at, site, committed_before=held, kind=ra.GATE_REFUSED if site.halt_reason.startswith(ra.GATE_REFUSED) else ra.VALIDATION_REFUSED)
    reasons = json.dumps([record.get("failure_reason") for record in site.records])
    assert "the common core lineage could not be evaluated" in reasons, reasons               # the gate condition that failed is NAMED in the recorded reason (it was an assertion that could not fail before the P3-248 review)
    monkeypatch.undo()
    _nothing_more_commits(at, site)


def test_f3_an_artifact_that_does_not_reproduce_the_minute_stops_the_experiment(real_page, monkeypatch):
    at = real_page(CASES[1])
    site = _first_commit(at)
    held = list(site.minutes_committed)
    monkeypatch.setattr(ra.AuthoritySite, "_replayed_point", staticmethod(lambda artifact, minute: {"sbp": 1, "dbp": 1, "map": 1}))
    page._order(at, "Reassess in 10 minutes.")
    _assert_invalid_after_a_commit(at, site, committed_before=held, kind=ra.VALIDATION_REFUSED, rederived=True)
    assert "minute_reproducible" in next(record for record in site.records if record["outcome"] == ra.ABORTED)["validation_failures"]


def test_f4_a_validation_failure_at_the_end_minute_stops_the_experiment(real_page, monkeypatch):
    at = real_page(CASES[0])
    site = _first_commit(at)
    held = list(site.minutes_committed)
    original = ra.AuthorityTransaction.validate

    def refuse(self, **kwargs):
        original(self, **kwargs)
        self.refuse(["injected_validation_failure"], replay_digest=kwargs.get("replay_digest"), reason="validation refused: ['injected_validation_failure']")
        return False
    monkeypatch.setattr(ra.AuthorityTransaction, "validate", refuse)
    page._order(at, "Reassess in 10 minutes.")
    _assert_invalid_after_a_commit(at, site, committed_before=held, kind=ra.VALIDATION_REFUSED, rederived=True)


@pytest.mark.parametrize("failing_offset", (1, 20, 59))
def test_f5_an_internal_minute_failure_in_a_long_infusion_aborts_the_whole_interval(real_page, monkeypatch, failing_offset):
    """``VALIDATED_ATOMIC_INTERVAL`` on the real page: a 60-minute infusion validated at EVERY internal minute; the first failing minute aborts all of it, nothing is committed
    for the turn and the record names the minute."""
    at = real_page(CASES[0])
    page._order(at, "Place an IV line.")
    site = _first_commit(at)
    held = list(site.minutes_committed)
    start = at.session_state["state"]["sim_time"]
    target = start + failing_offset
    original = validation.pressure_failures

    def failing(minute, **kwargs):
        found = list(original(minute, **kwargs))
        return found + ["injected_internal_minute_failure"] if minute == target else found
    monkeypatch.setattr(validation, "pressure_failures", failing)
    page._order(at, "Give 1 litre of normal saline over 60 minutes. Reassess in 60 minutes.")
    artifact = _assert_invalid_after_a_commit(at, site, committed_before=held, kind=ra.VALIDATION_REFUSED, rederived=True)
    failed = next(record for record in site.records if record["outcome"] == ra.ABORTED)
    detail = failed["interval_validation"]
    assert detail["first_failed_minute"] == target and detail["interval_minutes"][1] - detail["interval_minutes"][0] + 1 >= 59 and (not detail["ineligible_after"] or min(detail["ineligible_after"]) == target + 1), detail
    assert not any(minute > start for minute in site.minutes_committed), "no hidden failed internal minute: the interval committed nothing"


def test_f6_an_internal_error_inside_the_site_is_a_visible_halt_not_a_silent_return(real_page, monkeypatch):
    at = real_page(CASES[1])
    site = _first_commit(at)
    held = list(site.minutes_committed)
    monkeypatch.setattr(ra.AuthoritySite, "_provenance", lambda self, *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")))
    page._order(at, "Reassess in 10 minutes.")
    _assert_invalid_after_a_commit(at, site, committed_before=held, kind="SITE_ERROR", rederived=False)


@pytest.mark.parametrize("case", CASES)
def test_f7_a_fault_before_the_first_commit_leaves_the_legacy_encounter_as_if_the_experiment_had_not_been_asked_for(real_page, case, monkeypatch, tmp_path):
    """Authority never began: the page is the legacy page at every step (the experiment's record says it was halted, and nothing was ever authored)."""
    at = real_page(case)
    page._order(at, page.UNSUPPORTED)
    site = _site(at)
    assert site is not None and site.halted and not site.minutes_committed
    artifact = site.artifact()
    assert artifact["authority_began"] is False and artifact["experiment_outcome"] == "EXPERIMENT_HALTED" and artifact["mixed_trajectory"] is False
    baseline = page._open(monkeypatch, case, shadow=True, dry=False, authority=None)
    page._order(baseline, page.UNSUPPORTED)
    assert page._observed(at)["observable"] == page._observed(baseline)["observable"], "the legacy encounter is exactly as if the experiment had not been asked for"
    assert page._observed(at)["ledger"] == page._observed(baseline)["ledger"]


# -- P3-245: the boundary and the window ------------------------------------------------------------------------------------------------------------------

def test_b1_established_collapse_inside_an_interval_stops_the_experiment_before_that_interval_is_committed(real_page):
    at = real_page(CASES[0])
    for _ in range(3):
        page._order(at, "Reassess in 60 minutes.")
    site = _site(at)
    last = max(site.minutes_committed)
    assert last == 180 and not site.halted
    page._order(at, "Reassess in 60 minutes.")                     # minutes 181..240: the common core is ESTABLISHED from minute 207
    assert site.halted and site.halt_reason.startswith(ra.COLLAPSE_BOUNDARY_REACHED) and max(site.minutes_committed) == last
    artifact = site.artifact()
    boundary = artifact["collapse_boundary"]
    assert boundary["last_authoritative_commit_minute"] == 180 and boundary["first_rejected_minute"] == 240 and boundary["rejection_reason"].startswith(ra.COLLAPSE_BOUNDARY_REACHED)
    state = boundary["common_state_at_rejection"]
    assert state["rows"][-1]["minute"] == 240 and state["rows"][-1]["collapse_state"] == 2 and state["rows"][-1]["mental_status"] == "Unresponsive" and state["legacy_mental_status"] == "Obtunded"
    failed = next(record for record in site.records if record["outcome"] == ra.ABORTED)
    assert failed["collapse_boundary"]["first_established_minute"] == 207 and failed["committed"] == []
    assert at.session_state["state"]["observable"]["mental_status"] == state["legacy_mental_status"] != "Unresponsive", "the resident keeps the legacy word: no terminal word, no common word"
    assert at.session_state["state"]["observable"].get("pulse_present", True) is not False
    replay = ra.replay_site_artifact(artifact)
    assert replay["overlay_replay"]["reproduces"] and replay["halt_reason_replay"]["reproduces"] and replay["halt_reason_replay"]["first_established_minute"] == 207


def test_b2_impending_collapse_is_not_a_stop_and_the_overlay_records_it(real_page):
    at = real_page(CASES[1])
    for _ in range(3):
        page._order(at, "Reassess in 60 minutes.")
    page._order(at, "Reassess in 15 minutes.")                     # minutes 181..195 include IMPENDING (from 189), not ESTABLISHED
    site = _site(at)
    assert not site.halted and max(site.minutes_committed) == 195, site.halt_reason
    rows = [row for turn in site.artifact()["consciousness_overlay"]["turns"] for row in turn["rows"]]
    assert {row["collapse_state"] for row in rows if row["minute"] >= 189} == {1} and {row["collapse_state"] for row in rows if row["minute"] < 189} == {0}


def test_b3_a_minute_past_the_window_is_never_committed(real_page):
    at = real_page(CASES[0])
    page._order(at, "Place an IV line.")
    page._order(at, "Give 1 litre of normal saline over 15 minutes.")
    page._order(at, "Transfuse 2 units of packed red cells.")
    for _ in range(5):
        page._order(at, "Reassess in 60 minutes.")
        if _site(at).halted:
            break
    site = _site(at)
    assert site.halted and site.halt_reason.startswith(ra.WINDOW_CLOSED), site.halt_reason
    assert all(minute <= grants.WINDOW_MINUTES for minute in site.minutes_committed) and max(site.minutes_committed) <= 240
    replay = ra.replay_site_artifact(site.artifact())
    assert replay["halt_reason_replay"]["reproduces"] and replay["halt_reason_replay"]["kind"] == ra.WINDOW_CLOSED


def test_b4_when_the_overlay_cannot_be_built_the_boundary_cannot_be_verified_and_nothing_is_committed(real_page, monkeypatch):
    """Fail closed: no overlay, no verifiable boundary, no commit (the experiment halts before the first commit; the legacy encounter is untouched)."""
    import runtime_authority_pair as pair
    monkeypatch.setattr(pair, "bind", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("the snapshot binding was refused")))
    at = real_page(CASES[0])
    page._ask(at, "What brought you in today?")
    site = _site(at)
    assert site.halted and site.halt_reason.startswith(ra.COLLAPSE_BOUNDARY_NOT_VERIFIABLE) and not site.minutes_committed
    assert site.artifact()["authority_began"] is False and site.artifact()["consciousness_overlay"]["available"] is False
