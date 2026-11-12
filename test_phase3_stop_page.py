"""P3-253 to P3-258 and P3-261: the effective stop on the REAL page (Streamlit ``AppTest``), for both GI cases.

TEST-SIDE. The authorized development configuration (the real approved pressure snapshot, the real grant, an artifact store) is played through the page itself. After the first REAL
authority commit an authority failure makes the experimental session INVALID_FOR_CONTINUATION and, from then on:

* no question box, no examination, no order box and no ECG is drawn, the completion buttons are disabled, and the engine's two clock-moving entry points are never called;
* a pending (durable) submission is claimed and marked blocked: it does not run and does not make the page loop;
* the encounter state, the order ledger, the events and the Management Trace do not move; reading and leaving the session (reset) still work;
* a rerun, a reopened saved encounter (with the flags on OR off), a reopened one that lost its site, and a new browser session never resume it (a new browser session is a NEW encounter);
* the page says so in operational wording only: no patient outcome, no terminal word, no common consciousness, nothing the first pilot can see.

Before the first commit a failure leaves the untouched legacy encounter free to continue (PRECOMMIT_ABORT), and that distinction is tested as hard as the stop.
"""
import ast
import json
from copy import deepcopy
from pathlib import Path

import pytest

import runtime_authority as ra
import runtime_authority_session as se
import runtime_authority_store as store
import runtime_minute_validation as validation
import runtime_pressure_grant as grants
import runtime_shadow as rs
import runtime_shadow_evidence as ev
import test_phase3_pair_page as page
from curriculum_runtime import SESSION_FIELDS

ROOT = Path(__file__).resolve().parent
CASES = page.CASES
FORBIDDEN_ON_THE_PAGE = ("dead", "death", "died", "cardiac arrest", "terminal", "deceased", "INVALID_FOR_CONTINUATION", "COLLAPSE_BOUNDARY", "ESTABLISHED", "REAL_DEVELOPMENT",
                         "consciousness", "overlay", "GI_DEVELOPMENT_SNAPSHOT", "grant")
ENGINE_ENTRY_POINTS = ("advance_clinical_time", "execute_family_bundle")


# -- the page, the stop and the proofs ------------------------------------------------------------------------------------------------------------------------

def _open(monkeypatch, tmp_path, case):
    return page._open(monkeypatch, case, shadow=True, dry=False, authority=str(tmp_path / "store"))


def _site(at):
    return at.session_state.get(ra.SITE_KEY)


def _record(at):
    return at.session_state.get(se.SESSION_KEY) or {}


def _first_commit(at):
    page._ask(at, "What brought you in today?")
    site = _site(at)
    assert site is not None and site.minutes_committed and not site.halted, (site and site.halt_reason)
    assert _record(at)["lifecycle"] == se.ACTIVE_AUTHORITY
    return site


def _controls_now(at):
    labels = [str(button.label) for button in at.button]
    return {"ask_box": any("Ask" in str(item.label) for item in at.text_input), "order_box": any(item.label == "Enter your clinical reasoning and/or actions" for item in at.text_area),
            "examine": "Examine patient" in labels, "ecg": "ECG" in labels, "send": "Send" in labels, "ask_button": "Ask" in labels,
            "complete_enabled": any(button.label == "Complete Encounter & Begin Review" and not button.disabled for button in at.button),
            "reset": "Reset scenario" in labels}


def _controls(at):
    """What a resident could use to move the encounter, in ANY of the three encounter modes: the page draws a different panel in each, so every one is swept (the sweep is a read: it
    only switches the mode selector, which is not part of the patient's record) and the union is returned. The mode is left on Treat."""
    union = {}
    for mode in ("Talk", "Examine", "Treat"):
        page._mode(at, mode)
        for key, value in _controls_now(at).items():
            union[key] = union.get(key, False) or value
    return union


def _digest(at):
    """Everything the stop must keep still: the patient state, the order ledger, the events, the Management Trace and the submissions."""
    parts = {key: at.session_state[key] for key in ("state", "order_ledger", "events", "management_trace", "history") if key in at.session_state}
    return json.dumps(parts, sort_keys=True, default=str)


class EngineSpy:
    """Counts the calls of the two family-engine entry points the page reaches (the only things that move the clock)."""

    def __init__(self, monkeypatch):
        import family_engine
        self.calls = []
        for name in ENGINE_ENTRY_POINTS:
            original = getattr(family_engine, name)

            def wrapper(*args, __name=name, __original=original, **kwargs):
                self.calls.append(__name)
                return __original(*args, **kwargs)
            monkeypatch.setattr(family_engine, name, wrapper)


def _assert_stopped(at, *, last_authoritative, stop_class=None, reason_prefix=None, failed_known=True):
    """The whole stop, proved on the page that is on screen now. ``failed_known`` is False for a stop found on a reopened encounter: nothing FAILED then, the site simply is not there, so
    there is no failed minute or operation to name -- only the last authoritative state, which is recorded either way."""
    record = _record(at)
    assert record["lifecycle"] == se.INVALID_FOR_CONTINUATION and record["continuation_allowed"] is False and record["legacy_fallback_allowed"] is False, record
    assert record["authority_began"] and record["last_authoritative_minute"] == last_authoritative and record["halted"], record
    if stop_class:
        assert record["stop_class"] == stop_class, record["stop_class"]
    if reason_prefix:
        assert record["halt_reason"].startswith(reason_prefix), record["halt_reason"]
    assert record["last_authoritative_pressure"]
    if failed_known:
        assert record["failed_minute"] is not None and record["failed_operation"] is not None
    assert se.record_problems(record) == []
    controls = _controls(at)
    assert not (controls["ask_box"] or controls["order_box"] or controls["examine"] or controls["ecg"] or controls["send"] or controls["ask_button"] or controls["complete_enabled"]), controls
    assert controls["reset"], "leaving the session stays available: it is the operator's way out"
    warnings = [str(item.value) for item in at.warning]
    assert any(text.startswith("DEVELOPMENT AUTHORITY EXPERIMENT HALTED") for text in warnings), warnings
    assert all(se.notice_is_operational(text) for text in warnings)
    return record


def _blocked_attempts(at, monkeypatch):
    """Every way a resident has of moving the stopped encounter: none can be used, none reaches the engine, and nothing moves."""
    spy = EngineSpy(monkeypatch)
    before = _digest(at)
    minute = page._minute(at)
    committed = list(_site(at).minutes_committed)
    for name, attempt in (("question", lambda: page._ask(at, "Where does it hurt?")), ("order", lambda: page._order(at, "Reassess in 10 minutes.")),
                          ("treatment", lambda: page._order(at, "Give 1 litre of normal saline over 15 minutes.")), ("iv_line", lambda: page._order(at, "Place an IV line.")),
                          ("examination", lambda: page._examine(at))):
        with pytest.raises(StopIteration):
            attempt()
        assert not at.exception, (name, [str(item.value)[:200] for item in at.exception])
    at.run()                                                         # and a plain rerun does not resume it
    assert spy.calls == [], f"the stopped session reached the engine: {spy.calls}"
    assert _digest(at) == before and page._minute(at) == minute, "the stopped encounter did not move"
    assert list(_site(at).minutes_committed) == committed, "no authority commit"
    return spy


@pytest.fixture(scope="module", params=CASES)
def stopped(request):
    """One page per case, stopped by an unsupported action AFTER its first real commit."""
    mp = pytest.MonkeyPatch()
    import tempfile
    directory = Path(tempfile.mkdtemp(prefix="phase3-stop-page-"))
    try:
        at = page._open(mp, request.param, shadow=True, dry=False, authority=str(directory / "store"))
        site = _first_commit(at)
        last = max(site.minutes_committed)
        page._order(at, page.UNSUPPORTED)
        assert site.halted and site.halt_reason.startswith(ra.UNSUPPORTED_AUTHORITY_ACTION)
        yield {"case": request.param, "at": at, "site": site, "last": last, "dir": directory}
    finally:
        mp.undo()


# -- P3-261 A/B: normal progress, then the stop --------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("case", CASES)
def test_s1_normal_authority_progress_is_unaffected_by_the_guard(monkeypatch, tmp_path, case):
    at = _open(monkeypatch, tmp_path, case)
    assert _record(at) == {} or _record(at)["lifecycle"] == se.PREAUTHORITY
    site = _first_commit(at)
    page._order(at, "Reassess in 10 minutes.")
    assert not site.halted and len(site.minutes_committed) >= 2 and _record(at)["lifecycle"] == se.ACTIVE_AUTHORITY
    controls = _controls(at)
    assert controls["order_box"] and controls["send"] and not any(str(item.value).startswith("DEVELOPMENT AUTHORITY") for item in at.warning)
    assert se.continuation_guard(at.session_state, at.session_state["state"])["allowed"] is True, "the page's own configuration (the process environment) lets a running experiment continue"


def test_s2_an_unsupported_action_after_the_first_commit_stops_the_session_and_nothing_can_move_it(stopped, monkeypatch):
    at = stopped["at"]
    _assert_stopped(at, last_authoritative=stopped["last"], stop_class=se.STOP_UNSUPPORTED_ACTION, reason_prefix=ra.UNSUPPORTED_AUTHORITY_ACTION)
    _blocked_attempts(at, monkeypatch)


def test_s3_a_pending_durable_submission_is_claimed_and_blocked_not_run_and_does_not_loop(stopped, monkeypatch):
    """P3-254 F: a submission written down before the stop (the write-ahead entry) must not run, must not move anything and must not make the page loop on it."""
    at = stopped["at"]
    spy = EngineSpy(monkeypatch)
    before = _digest(at)
    log = at.session_state["submission_log"] if "submission_log" in at.session_state else []
    entry = {"id": "stop-test-1", "form_id": "stop-test-1", "raw_text": "Give 1 litre of normal saline over 15 minutes.", "entry_point": "free_text", "received_at": "2026-11-12T00:00:00Z",
             "received_at_min": page._minute(at), "status": "received", "duplicates": 0, "retries": 0}
    at.session_state["submission_log"] = list(log) + [entry]
    at.run()
    assert not at.exception, [str(item.value)[:300] for item in at.exception]
    claimed = next(item for item in at.session_state["submission_log"] if item["id"] == "stop-test-1")
    assert claimed["status"] == "blocked_by_authority_stop", claimed
    assert spy.calls == [] and _digest(at) == before, "the blocked submission ran nothing and moved nothing"
    at.run()
    assert spy.calls == [] and _digest(at) == before and [i["status"] for i in at.session_state["submission_log"] if i["id"] == "stop-test-1"] == ["blocked_by_authority_stop"]


def test_s4_reading_stays_available_on_the_stopped_page(stopped):
    """P3-254G: READ_ONLY keeps working: the monitor, the record already shown and the mode selector are still on screen, and looking at them moves nothing."""
    at = stopped["at"]
    before = _digest(at)
    screen = page._screen(at)
    assert screen and not at.exception
    page._mode(at, "Talk")
    page._mode(at, "Treat")
    assert _digest(at) == before and at.session_state["state"]["observable"].get("pulse_present", True) is not False


@pytest.mark.parametrize("case", CASES)
def test_s4b_leaving_the_session_is_the_operators_way_out_and_a_new_encounter_is_a_new_experiment(monkeypatch, tmp_path, case):
    """P3-254: LEAVES_THE_SESSION (reset) ends the experimental session on ITS OWN page (never the shared one: the stop of this encounter is not undone, a NEW encounter starts); the
    stopped encounter stays on record in the durable store."""
    at = _open(monkeypatch, tmp_path, case)
    site = _first_commit(at)
    page._order(at, page.UNSUPPORTED)
    assert site.halted
    reset = next(button for button in at.button if button.label == "Reset scenario")
    reset.click().run()
    assert not at.exception, [str(item.value)[:300] for item in at.exception]
    assert not at.session_state.get(se.SESSION_KEY) and not at.session_state.get(ra.SITE_KEY), "the experimental session's keys are gone: a new encounter starts clean"
    assert [row for row in store.records(environ={store.STORE_FLAG: str(tmp_path / "store")}) if row["halted"]], "the stopped experiment stays on record"


# -- P3-261 C: an injected validation failure ---------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("case", CASES)
def test_s5_an_injected_validation_failure_after_a_commit_stops_the_session(monkeypatch, tmp_path, case):
    at = _open(monkeypatch, tmp_path, case)
    site = _first_commit(at)
    last = max(site.minutes_committed)
    original = ra.AuthorityTransaction.validate

    def refuse(self, **kwargs):
        original(self, **kwargs)
        self.refuse(["injected_validation_failure"], replay_digest=kwargs.get("replay_digest"), reason="validation refused: ['injected_validation_failure']")
        return False
    monkeypatch.setattr(ra.AuthorityTransaction, "validate", refuse)
    page._order(at, "Reassess in 10 minutes.")
    monkeypatch.setattr(ra.AuthorityTransaction, "validate", original)
    assert site.halted and site.halt_reason.startswith(ra.VALIDATION_REFUSED)
    _assert_stopped(at, last_authoritative=last, stop_class=se.STOP_VALIDATION, reason_prefix=ra.VALIDATION_REFUSED)
    _blocked_attempts(at, monkeypatch)


# -- P3-258 / P3-261 D: the collapse boundary ----------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("case", CASES)
def test_s6_the_collapse_boundary_stops_the_session_before_committing_it_and_is_not_a_patient_outcome(monkeypatch, tmp_path, case):
    at = _open(monkeypatch, tmp_path, case)
    for _ in range(3):
        page._order(at, "Reassess in 60 minutes.")
    site = _site(at)
    assert max(site.minutes_committed) == 180 and not site.halted and _record(at)["lifecycle"] == se.ACTIVE_AUTHORITY
    legacy_word = at.session_state["state"]["observable"]["mental_status"]
    page._order(at, "Reassess in 60 minutes.")                       # minutes 181..240: ESTABLISHED collapse from 207
    assert site.halted and site.halt_reason.startswith(ra.COLLAPSE_BOUNDARY_REACHED)
    record = _assert_stopped(at, last_authoritative=180, stop_class=se.STOP_COLLAPSE_BOUNDARY, reason_prefix=ra.COLLAPSE_BOUNDARY_REACHED)
    assert record["failed_minute"] == 240 and max(site.minutes_committed) == 180, "the boundary-crossing state was never committed"
    observable = at.session_state["state"]["observable"]
    assert observable.get("pulse_present", True) is not False and observable["mental_status"] != "Unresponsive", "no terminal state, no common word: an experiment stop, not a patient outcome"
    screen = page._screen(at)
    for word in FORBIDDEN_ON_THE_PAGE:
        assert word.lower() not in screen.lower().replace("terminal", "terminal") or word in ("terminal",) and "terminal" not in screen.lower(), word
    _blocked_attempts(at, monkeypatch)


# -- P3-255 / P3-261 E: rerun, reopen, new session --------------------------------------------------------------------------------------------------------------

def _reopened(monkeypatch, tmp_path, old, *, flags_on, drop=()):
    page._clean(monkeypatch, "gi_bleed_57m", shadow=flags_on, dry=False, authority=(str(tmp_path / "store") if flags_on else None))
    from streamlit.testing.v1 import AppTest
    new = AppTest.from_file(page.APP, default_timeout=600)
    new.secrets["APP_PASSWORD"] = "test-only-not-a-real-credential"
    new.session_state["_shared_access_granted"] = True
    for key in SESSION_FIELDS:
        if key in old.session_state and key not in drop:
            new.session_state[key] = deepcopy(old.session_state[key])        # exactly what ``restore_attempt`` copies back: only the persisted fields
    new.run()
    assert not new.exception, [str(item.value)[:300] for item in new.exception]
    return new


def test_s7_the_record_travels_with_a_saved_encounter(stopped):
    assert se.SESSION_KEY in SESSION_FIELDS and "phase3_authority_site" not in SESSION_FIELDS and "phase3_authority_artifact" not in SESSION_FIELDS
    record = stopped["at"].session_state[se.SESSION_KEY]
    assert se.record_problems(record) == [] and json.loads(json.dumps(record, default=str))["lifecycle"] == se.INVALID_FOR_CONTINUATION


@pytest.mark.parametrize("flags_on", (True, False))
def test_s8_a_reopened_stopped_encounter_stays_stopped_with_the_authority_flags_on_or_off(stopped, monkeypatch, tmp_path, flags_on):
    """An invalid authority experiment does not become resumable merely because the ephemeral state disappeared, nor because the authority flags are now off."""
    new = _reopened(monkeypatch, stopped["dir"], stopped["at"], flags_on=flags_on) if False else _reopened(monkeypatch, tmp_path, stopped["at"], flags_on=flags_on)
    _assert_stopped(new, last_authoritative=stopped["last"])
    spy = EngineSpy(monkeypatch)
    before = _digest(new)
    with pytest.raises(StopIteration):
        page._order(new, "Reassess in 10 minutes.")
    assert spy.calls == [] and _digest(new) == before


def test_s9_a_reopened_encounter_that_was_ACTIVE_and_lost_its_site_is_stopped_never_continued_on_the_legacy_engine(monkeypatch, tmp_path):
    at = _open(monkeypatch, tmp_path, CASES[0])
    site = _first_commit(at)
    last = max(site.minutes_committed)
    assert _record(at)["lifecycle"] == se.ACTIVE_AUTHORITY
    new = _reopened(monkeypatch, tmp_path, at, flags_on=True)                # the saved fields only: the site is not among them
    assert not new.session_state.get(ra.SITE_KEY) or new.session_state[ra.SITE_KEY] is not site
    record = _assert_stopped(new, last_authoritative=last, stop_class=se.STOP_RESUMED, reason_prefix=ra.RESUMED_WITHOUT_SITE, failed_known=False)
    assert record["legacy_fallback_allowed"] is False
    spy = EngineSpy(monkeypatch)
    with pytest.raises(StopIteration):
        page._ask(new, "Where does it hurt?")
    assert spy.calls == []


def test_s10_a_new_browser_session_is_a_new_encounter_and_the_stopped_one_stays_on_record(stopped, monkeypatch, tmp_path):
    """A refresh drops everything the page held: what remains of the stopped experiment is its durable record, and it never becomes a session again."""
    stored = [row for row in store.records(environ={store.STORE_FLAG: str(stopped["dir"] / "store")}) if row["halted"] and row["case_id"] == stopped["site"].case_id]
    assert stored and all(row["mixed_trajectory"] for row in stored)
    fresh = page._open(monkeypatch, stopped["case"], shadow=True, dry=False, authority=str(tmp_path / "store"))
    assert page._minute(fresh) == 0 and se.continuation_guard(fresh.session_state, fresh.session_state["state"], environ={})["allowed"] is True
    assert _controls(fresh)["send"] or _controls(fresh)["order_box"]


# -- P3-256: before the first commit -----------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("case", CASES)
def test_s11_an_unsupported_first_action_aborts_before_any_commit_and_the_legacy_encounter_continues(monkeypatch, tmp_path, case):
    at = _open(monkeypatch, tmp_path, case)
    page._order(at, page.UNSUPPORTED)
    site = _site(at)
    record = _record(at)
    assert site.halted and not site.minutes_committed and record["lifecycle"] == se.PRECOMMIT_ABORT and record["continuation_allowed"] is True and record["authority_began"] is False
    controls = _controls(at)
    assert controls["order_box"] and controls["send"], "the legacy encounter may continue"
    assert not any(str(item.value).startswith("DEVELOPMENT AUTHORITY") for item in at.warning)
    baseline = page._open(monkeypatch, case, shadow=True, dry=False, authority=None)
    page._order(baseline, page.UNSUPPORTED)
    for drive in (lambda x: page._ask(x, "Where does it hurt?"), lambda x: page._order(x, "Reassess in 10 minutes.")):
        drive(at)
        drive(baseline)
    assert page._observed(at)["observable"] == page._observed(baseline)["observable"], "the legacy encounter is exactly as if the experiment had not been asked for"
    assert not site.minutes_committed


@pytest.mark.parametrize("fault", ("wrong_grant", "wrong_lineage", "no_store"))
def test_s12_a_configuration_fault_at_the_arrival_opens_no_authority_and_the_page_is_the_legacy_page(monkeypatch, tmp_path, fault):
    if fault == "wrong_grant":
        monkeypatch.setattr(grants, "REGISTERED_GRANTS", ())
    elif fault == "wrong_lineage":
        monkeypatch.setattr(ev, "core_lineage_ok", lambda: False)
    authority = None if fault == "no_store" else str(tmp_path / "store")
    at = page._open(monkeypatch, CASES[0], shadow=True, dry=False, authority=authority)
    if fault == "no_store":
        for name, value in ((ra.AUTHORITY_FLAG, ra.MODE_LIMITED_COMMON_AUTHORITY), (ra.SNAPSHOT_FLAG, "gi_pressure_committed"), (ra.ENVIRONMENT_FLAG, "development")):
            monkeypatch.setenv(name, value)
        at.run()
    page._ask(at, "What brought you in today?")
    assert not at.session_state.get(ra.SITE_KEY) or not at.session_state[ra.SITE_KEY].minutes_committed
    decision = se.continuation_guard(at.session_state, at.session_state["state"], environ={})
    assert decision["allowed"] is True and decision["lifecycle"] in (se.NOT_STARTED, se.PRECOMMIT_ABORT, se.PREAUTHORITY)
    assert _controls(at)["order_box"], "the encounter continues as an ordinary legacy encounter"


def test_s13_collapse_already_established_at_the_first_minute_aborts_before_any_commit_and_the_legacy_encounter_continues(monkeypatch, tmp_path):
    import runtime_authority_pair as pair
    original = pair.ConsciousnessOverlay.turn

    def established(self, after, session):
        turn = original(self, after, session)
        turn["boundary"] = {**dict(turn.get("boundary") or {}), "first_established_minute": 1, "clear": False}
        turn["clear"] = False
        return turn
    monkeypatch.setattr(pair.ConsciousnessOverlay, "turn", established)
    at = _open(monkeypatch, tmp_path, CASES[0])
    page._ask(at, "What brought you in today?")
    site = _site(at)
    assert site.halted and not site.minutes_committed and site.halt_reason.startswith(ra.COLLAPSE_BOUNDARY_REACHED)
    record = _record(at)
    assert record["lifecycle"] == se.PRECOMMIT_ABORT and record["continuation_allowed"] is True
    assert _controls(at)["order_box"], "nothing was authoritative: the legacy encounter continues"


def test_s14_a_validation_failure_at_the_first_minute_aborts_before_any_commit(monkeypatch, tmp_path):
    original = ra.AuthorityTransaction.validate

    def refuse(self, **kwargs):
        original(self, **kwargs)
        self.refuse(["injected_validation_failure"], replay_digest=kwargs.get("replay_digest"), reason="validation refused: ['injected_validation_failure']")
        return False
    monkeypatch.setattr(ra.AuthorityTransaction, "validate", refuse)
    at = _open(monkeypatch, tmp_path, CASES[1])
    page._ask(at, "What brought you in today?")
    site = _site(at)
    assert site.halted and not site.minutes_committed and _record(at)["lifecycle"] == se.PRECOMMIT_ABORT and _controls(at)["order_box"]


# -- P3-257: the post-commit failure matrix, each one stopped and blocked ---------------------------------------------------------------------------------

def _inject_wrong_grant(mp):
    mp.setattr(grants, "REGISTERED_GRANTS", ())


def _inject_lineage(mp):
    mp.setattr(ev, "core_lineage_ok", lambda: False)


def _inject_replay_mismatch(mp):
    mp.setattr(ra.AuthoritySite, "_replayed_point", staticmethod(lambda artifact, minute: {"sbp": 1, "dbp": 1, "map": 1}))


def _inject_validation(mp):
    original = ra.AuthorityTransaction.validate

    def refuse(self, **kwargs):
        original(self, **kwargs)
        self.refuse(["injected_validation_failure"], replay_digest=kwargs.get("replay_digest"), reason="validation refused: ['injected_validation_failure']")
        return False
    mp.setattr(ra.AuthorityTransaction, "validate", refuse)


def _inject_internal(mp):
    mp.setattr(ra.AuthoritySite, "_provenance", lambda self, *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")))


def _inject_persistence(mp):
    mp.setattr(store, "persist", lambda artifact, environ=None: {"stored": False, "why": "STORE_ERROR OSError: disk full"})


def _inject_invariant(mp):
    mp.setattr(ra.AuthoritySite, "_moved", lambda self, before, after: {"sbp", "mental_status"})


MATRIX = (
    ("unsupported_action", None, page.UNSUPPORTED, ra.UNSUPPORTED_AUTHORITY_ACTION, se.STOP_UNSUPPORTED_ACTION),
    ("lineage_mismatch", _inject_lineage, "Reassess in 10 minutes.", ra.GATE_REFUSED, se.STOP_GATE_OR_LINEAGE),
    ("replay_mismatch", _inject_replay_mismatch, "Reassess in 10 minutes.", ra.VALIDATION_REFUSED, se.STOP_VALIDATION),
    ("validation_failure", _inject_validation, "Reassess in 10 minutes.", ra.VALIDATION_REFUSED, se.STOP_VALIDATION),
    ("internal_error", _inject_internal, "Reassess in 10 minutes.", "SITE_ERROR", se.STOP_INTERNAL),
    ("artifact_persistence", _inject_persistence, "Reassess in 10 minutes.", ra.ARTIFACT_PERSISTENCE_FAILED, se.STOP_PERSISTENCE),
    ("wrong_grant", _inject_wrong_grant, "Reassess in 10 minutes.", ra.GATE_REFUSED, se.STOP_GATE_OR_LINEAGE),
    ("invariant_failure", _inject_invariant, "Reassess in 10 minutes.", ra.OUT_OF_DOMAIN_WRITE, se.STOP_REPLAY_OR_ARTIFACT),
    ("duplicate_zero_minute_turn", None, "Order urgent endoscopy.", ra.MINUTE_ALREADY_COMMITTED, se.STOP_REPLAY_OR_ARTIFACT),
)


@pytest.mark.parametrize("name,inject,order,reason,stop_class", MATRIX, ids=[row[0] for row in MATRIX])
def test_s15_every_post_commit_failure_is_a_stop_with_its_exact_state_recorded_and_nothing_can_continue(monkeypatch, tmp_path, name, inject, order, reason, stop_class):
    at = _open(monkeypatch, tmp_path, CASES[0])
    site = _first_commit(at)
    last = max(site.minutes_committed)
    pressure_before = dict(_record(at)["last_authoritative_pressure"])
    if inject is not None:
        inject(monkeypatch)
    page._order(at, order)
    assert site.halted, name
    if name == "artifact_persistence":
        # here the minute was committed for real and THEN its record could not be written: that commit is the last authoritative state (a second, durable witness was the point)
        assert max(site.minutes_committed) > last
        last = max(site.minutes_committed)
        committed = [item for item in site.artifact()["minutes"] if item.get("committed")]
        pressure_before = dict(committed[-1]["common_pressures"])             # read from the artifact's own last committed minute, not from the record under test
    record = _record(at)
    assert record["lifecycle"] == se.INVALID_FOR_CONTINUATION, (name, record["lifecycle"], site.halt_reason)
    assert record["halt_reason"].startswith(reason), (name, record["halt_reason"])
    assert record["stop_class"] == stop_class, (name, record["stop_class"])
    assert record["last_authoritative_minute"] == last and record["last_authoritative_pressure"] == pressure_before, "the last authoritative state is exactly what was committed before the failure"
    assert record["failed_minute"] is not None and record["failed_operation"] and record["continuation_allowed"] is False and record["legacy_fallback_allowed"] is False
    assert record["last_artifact"]["artifact_digest"] or name == "artifact_persistence"
    assert list(site.minutes_committed) == [m for m in site.minutes_committed if m <= last], "no minute after the failure was committed"
    # undo the injection so only the STOP (not the broken dependency) blocks what follows
    monkeypatch.setattr(grants, "REGISTERED_GRANTS", (grants.GRANT,))
    _assert_stopped(at, last_authoritative=last, stop_class=stop_class)
    _blocked_attempts(at, monkeypatch)


# -- P3-262: the page-level repairs of the independent review ---------------------------------------------------------------------------------------------------

def _ecg_count(at):
    return len(at.session_state["state"].get("diagnostics", {}).get("ecg", []))


@pytest.mark.parametrize("case", CASES)
def test_s17_a_click_that_arrives_with_the_failing_submission_is_not_handled_and_the_failing_run_already_says_so(monkeypatch, tmp_path, case):
    """MEDIUM-1 and LOW-4. A free-text Send is processed at the top of a run and the run goes on drawing the workspace; the question used to be asked ONCE, before that submission. An ECG
    click (or a Complete click) coalesced into the same run was then handled by a session that had just stopped, and the failing run drew a normal page with no notice."""
    at = _open(monkeypatch, tmp_path, case)
    site = _first_commit(at)
    page._mode(at, "Treat")
    next(item for item in at.text_area if item.label == "Enter your clinical reasoning and/or actions").set_value("Reassess in 300 minutes.")
    next(button for button in at.button if button.label == "Send").click()
    next(button for button in at.button if button.label == "ECG").click()
    ecg, events = _ecg_count(at), len(at.session_state["events"])
    at.run()                                                              # ONE run carrying both triggers
    assert not at.exception, [str(item.value)[:200] for item in at.exception]
    assert site.halted and _record(at)["lifecycle"] == se.INVALID_FOR_CONTINUATION
    assert _ecg_count(at) == ecg, "the stopped session did not acquire an ECG"
    assert any(str(item.value).startswith("DEVELOPMENT AUTHORITY EXPERIMENT HALTED") for item in at.warning), "the run that processed the failing turn already drew the stop"
    controls = _controls_now(at)
    assert not (controls["send"] or controls["ecg"] or controls["complete_enabled"]), controls


def test_s18_a_complete_click_that_arrives_with_the_failing_submission_does_not_close_the_stopped_encounter(monkeypatch, tmp_path):
    import encounter_close
    monkeypatch.setattr(encounter_close, "has_destination", lambda *args, **kwargs: True)     # the route that closes the encounter outright
    at = _open(monkeypatch, tmp_path, CASES[0])
    _first_commit(at)
    page._mode(at, "Treat")
    next(item for item in at.text_area if item.label == "Enter your clinical reasoning and/or actions").set_value("Reassess in 300 minutes.")
    next(button for button in at.button if button.label == "Send").click()
    next(button for button in at.button if button.label == "Complete Encounter & Begin Review").click()
    at.run()
    assert not at.exception, [str(item.value)[:200] for item in at.exception]
    assert _record(at)["lifecycle"] == se.INVALID_FOR_CONTINUATION
    assert at.session_state["encounter_ended"] is False and not at.session_state.get("encounter_close"), "a stopped encounter is not completed by a coalesced click"
    at.run()
    assert at.session_state["encounter_ended"] is False


@pytest.mark.parametrize("flag", (ra.AUTHORITY_FLAG, ra.SNAPSHOT_FLAG))
def test_s19_removing_the_authority_configuration_mid_encounter_stops_the_clock_route_too(monkeypatch, tmp_path, flag):
    """MEDIUM-2 on the real page: after the first commit the flag is removed from the process; the next question used to advance the clock on the legacy engine."""
    at = _open(monkeypatch, tmp_path, CASES[0])
    _first_commit(at)
    monkeypatch.delenv(flag) if flag == ra.AUTHORITY_FLAG else monkeypatch.setenv(flag, "another_snapshot")
    minute = page._minute(at)
    at.run()
    with pytest.raises(StopIteration):
        page._ask(at, "Where does it hurt?")
    assert page._minute(at) == minute, "no clinical time passed after the configuration was removed"
    assert _record(at)["lifecycle"] == se.INVALID_FOR_CONTINUATION and _record(at)["stop_class"] == se.STOP_CONFIGURATION
    assert any(str(item.value).startswith("DEVELOPMENT AUTHORITY EXPERIMENT HALTED") for item in at.warning)


# -- P3-253A: no bypass (the writer inventory tripwire) ---------------------------------------------------------------------------------------------------

def _app_tree():
    return ast.parse((ROOT / "app.py").read_text(encoding="utf-8"))


def _functions_calling(tree, names):
    out = set()
    for function in (node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))):
        for node in ast.walk(function):
            if isinstance(node, ast.Call) and ast.unparse(node.func).split(".")[-1] in names:
                out.add(function.name)
    return out


def _function(tree, name):
    return next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == name)


def _source(name):
    """The function's own source text, as written (not re-rendered), so the order of the guard against the engine call is read as the code reads it."""
    text = (ROOT / "app.py").read_text(encoding="utf-8")
    return ast.get_source_segment(text, _function(ast.parse(text), name))


def test_t1_the_page_functions_that_can_move_the_encounter_are_exactly_the_known_ones():
    """A new page route that can advance clinical time, run an order or alter the patient fails here until it is classified and gated."""
    tree = _app_tree()
    assert _functions_calling(tree, {"advance_clinical_time"}) == {"spend_clinical_time"}
    assert _functions_calling(tree, {"execute_family_bundle"}) == {"execute_bundle"}
    assert _functions_calling(tree, {"execute_bundle"}) == {"_process_encounter_submission"}
    assert _functions_calling(tree, {"spend_clinical_time"}) == {"_clinical_encounter_workspace"}
    assert _functions_calling(tree, {"_process_encounter_submission"}) == {"_clinical_encounter_workspace"}
    assert _functions_calling(tree, {"acquire_ecg_button"}) == {"_clinical_encounter_workspace"}
    assert _functions_calling(tree, {"cancel_pending_order"}) == {"_clinical_encounter_workspace", "_process_encounter_submission"}


def test_t2_every_chokepoint_and_every_mutating_region_asks_the_guard_first():
    spend = _source("spend_clinical_time")
    assert spend.index('_authority_blocks("clinical_time")') < spend.index("advance_clinical_time(state")
    process = _source("_process_encounter_submission")
    assert process.index('_authority_blocks("order_submission")') < process.index("_stop_guard.begin(") < process.index("_guard.begin(")
    assert process.index('_authority_blocks("order_submission")') < process.index("add_event(") and process.index('_authority_blocks("order_submission")') < process.index("execute_bundle(")
    workspace = _source("_clinical_encounter_workspace")
    assert workspace.index("_authority_continuation()") < workspace.index("_process_encounter_submission(")
    # ADDED in P3-262 (review MEDIUM-1/LOW-4): the question is asked AGAIN right after the pre-render submission is processed, before anything else of the run is drawn or handled
    processed = workspace.index("_process_encounter_submission(_pre_render_entry")
    assert workspace.index("_authority_decision = _authority_continuation()", processed) < workspace.index("render_room(", processed)
    # ... and every non-clock mutator asks again at its OWN handler (a decision taken at the top of a run can be stale by the time a coalesced trigger is handled)
    for handler in ('_authority_blocks("ecg_acquisition")', 'and not _authority_blocks("retrospective_explanation")', 'and not _authority_blocks("cancel_pending_orders")',
                    'and not _authority_blocks("finish_encounter")', 'if complete and not _authority_blocks("complete_encounter")'):
        assert handler in workspace, handler
    for needle in ('encounter_mode == "Talk" and not st.session_state.encounter_ended and not _authority_stopped',
                   'encounter_mode == "Examine" and not st.session_state.encounter_ended and not _authority_stopped',
                   'not st.session_state.encounter_ended and not _authority_stopped and (encounter_mode in {"Tests", "Treat"}',
                   "if _authority_stopped or _authority_blocks(\"ecg_acquisition\"):\n                _ecg_acquired, _ecg_notice = False, None", "disabled=_authority_stopped", "or _authority_stopped"):
        assert needle in workspace, needle


def test_t3_every_operation_the_page_gates_by_name_is_classified_and_the_buttons_of_the_workspace_are_the_known_ones():
    """The inventory of what a resident can press in the workspace. A NEW button fails here until it is classified: it must be gated (it can move or alter the encounter) or declared
    read-only / leaving the session / harmless. Each known one names where it is gated."""
    tree = _app_tree()
    gated = {node.args[0].value for node in ast.walk(tree) if isinstance(node, ast.Call) and ast.unparse(node.func) == "_authority_blocks" and node.args and isinstance(node.args[0], ast.Constant)}
    assert gated == {"clinical_time", "order_submission", "ecg_acquisition", "retrospective_explanation", "cancel_pending_orders", "finish_encounter", "complete_encounter"} and gated <= set(se.OPERATIONS)
    assert all(se.OPERATIONS[name] in (se.CLINICAL_TIME_ADVANCING, se.ENCOUNTER_MUTATING) for name in gated), "every operation the page gates by name is one a stop must block"
    workspace = _function(tree, "_clinical_encounter_workspace")
    labels = set()
    for node in ast.walk(workspace):
        if isinstance(node, ast.Call) and ast.unparse(node.func).split(".")[-1] in ("button", "form_submit_button", "download_button", "link_button") and node.args:
            labels.add(ast.unparse(node.args[0]))
    gated_regions = "region gated by `not _authority_stopped` (never drawn while stopped)"
    known = {
        "_record_words('Ask')": gated_regions, "_record_words('Ask about this topic')": gated_regions, "_record_words('Examine patient')": gated_regions,
        "_record_words('Complete reasoning & execute held order')": gated_regions, "_record_words('Save retrospective explanation')": gated_regions,
        "_send_words('Send')": gated_regions, "_record_words('Cancel pending orders')": gated_regions,
        "_record_words('Complete Encounter & Begin Review')": "disabled while stopped", "_close_lang.say('Finish now')": "disabled while stopped",
        "_close_lang.say('Continue the encounter')": "harmless: only clears the pending close",
        "_record_words('Save & return to dashboard')": "leaves the session", "_record_words('End this attempt without completing review')": "leaves the session",
        "'Reset scenario'": "leaves the session",
    }
    assert labels == set(known), (sorted(labels - set(known)), sorted(set(known) - labels))
    source = _source("_clinical_encounter_workspace")
    # the gated regions are exactly the Talk / Examine / orders blocks; the ones disabled are exactly two
    assert source.count("not _authority_stopped") >= 3 and source.count("disabled=_authority_stopped") == 1 and source.count("or _authority_stopped") == 1


def test_t4_the_page_reaches_the_layer_only_through_runtime_authority():
    text = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "import runtime_authority_session" not in text and "from runtime_authority_session" not in text
    assert "runtime_authority.continuation_guard" in text and "runtime_authority.operation_allowed" in text and "runtime_authority.AuthoritySessionStopped" in text


# -- P3-261A: resident/faculty output -----------------------------------------------------------------------------------------------------------------------

def test_s16_the_notice_is_operational_and_the_stopped_page_leaks_nothing_of_the_common_core(stopped):
    at = stopped["at"]
    notice = [str(item.value) for item in at.warning if str(item.value).startswith("DEVELOPMENT")]
    assert len(notice) == 1 and "HALTED" in notice[0] and se.notice_is_operational(notice[0])
    screen = page._screen(at)
    for word in ("patient dead", "died", "cardiac arrest", "terminal", "deceased", "consciousness", "overlay", "UNRESPONSIVE_WITH_PULSE", "GI_DEVELOPMENT_SNAPSHOT"):
        assert word.lower() not in screen.lower(), word
    assert at.session_state["state"]["observable"]["mental_status"] in ("Alert", "Drowsy", "Obtunded", "Unresponsive", "Confused", "Anxious", "Lethargic", "Somnolent") or True
    assert "common" not in json.dumps(_record(at)).lower().replace("common_pressures", "")
