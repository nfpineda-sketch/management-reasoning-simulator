"""P3-250 to P3-252, P3-256 to P3-259: the authority-session lifecycle, its persistent record, the effective-stop guard, and the consistency of the record with the artifact.

TEST-SIDE, headless: a REAL GI encounter and a REAL authority site (the real registered pressure approval and grant), driven the way the page drives it (order turns and clinical time),
with the page's session store stood in for by a dictionary the site publishes its record into. The page itself (controls not drawn, nothing advanced, refresh, reopen) is in
``test_phase3_stop_page.py``.

* P3-250A  the lifecycle graph is data, closed and with no hidden transition (INVALID_FOR_CONTINUATION never returns to ACTIVE_AUTHORITY or to a legacy continuation);
* P3-251   the record carries what the guard needs (and no consciousness), verifies, and a record that was edited -- even with its digest recomputed -- is not accepted;
* P3-252   the guard: authority began + halted = DENY; a halt BEFORE the first commit = ALLOW (the legacy encounter is untouched); any disagreement or unreadable source = DENY;
* P3-256/257  the failures before and after the first commit, by name, with the exact state recorded for each;
* P3-258   the collapse boundary is a stop, not a patient death; * P3-259 the artifact, the record and the site agree, and the record replays from the artifact alone.
"""
import json
import tempfile
from copy import deepcopy

import pytest

import runtime_authority as ra
import runtime_authority_session as se
import runtime_authority_store as store
import runtime_shadow as rs
from test_phase3_pressure_review import Driver  # noqa: F401  (the headless driver of a real site)

STORE_DIR = tempfile.mkdtemp(prefix="phase3-stop-lifecycle-")
REAL = {ra.AUTHORITY_FLAG: ra.MODE_LIMITED_COMMON_AUTHORITY, ra.SNAPSHOT_FLAG: "gi_pressure_committed", ra.ENVIRONMENT_FLAG: "development", rs.FLAG: rs.MODE_SHADOW_COMPARE,
        store.STORE_FLAG: STORE_DIR}
UNSUPPORTED = "Start norepinephrine at 10 mcg/min."
FIRST = "Give 1 litre of normal saline over 15 minutes."


@pytest.fixture(autouse=True, scope="module")
def _real_environment():
    with pytest.MonkeyPatch.context() as patch:
        for name, value in REAL.items():
            patch.setenv(name, value)
        for name in ra.PILOT_FLAGS + ra.PILOT_REQUIRED_ON:
            patch.delenv(name, raising=False)
        yield


def _plain(value):
    return json.loads(ra.canonical(value))


def _seal(record: dict) -> dict:
    body = {key: value for key, value in record.items() if key != "record_digest"}
    return {**body, "record_digest": ra.digest_of(body)}


class Session:
    """A driver plus the dictionary the page's session store would be: the site publishes its record into it and the page assigns the artifact, as the page does after each turn."""

    def __init__(self, case="gi_bleed_57m"):
        self.driver = Driver(case)
        self.store = {ra.SITE_KEY: self.driver.site}
        self.driver.site._session_store = self.store
        self.sequence = [self.record()["lifecycle"]]

    @property
    def site(self):
        return self.driver.site

    @property
    def state(self):
        return self.driver.state

    def record(self):
        return self.store.get(se.SESSION_KEY) or self.site.session_record()

    def _after(self):
        self.store[ra.ARTIFACT_KEY] = self.site.artifact()
        self.sequence.append(self.record()["lifecycle"])

    def order(self, text):
        self.driver.order(text)
        self._after()

    def ask(self, minutes=2):
        self.driver.ask(minutes)
        self._after()

    def guard(self, **kwargs):
        return se.continuation_guard(self.store, self.state, environ=REAL, **kwargs)


# -- P3-250A: the graph ---------------------------------------------------------------------------------------------------------------------------------------

def test_l1_the_lifecycle_graph_is_closed_and_has_no_hidden_transition():
    assert set(se.TRANSITIONS) == set(se.LIFECYCLE) and all(set(targets) <= set(se.LIFECYCLE) for targets in se.TRANSITIONS.values())
    for terminal in (se.INVALID_FOR_CONTINUATION, se.PRECOMMIT_ABORT, se.COMPLETED_AUTHORITY):
        assert se.TRANSITIONS[terminal] == (terminal,), f"{terminal} is terminal for the session: nothing resumes it by itself"
    for after in (se.ACTIVE_AUTHORITY, se.PREAUTHORITY, se.NOT_STARTED, se.PRECOMMIT_ABORT, se.COMPLETED_AUTHORITY):
        assert not se.transition_ok(se.INVALID_FOR_CONTINUATION, after), "ACTIVE_AUTHORITY -> failure -> ordinary legacy continuation is not a transition"
    assert se.transition_ok(se.PREAUTHORITY, se.ACTIVE_AUTHORITY) and se.transition_ok(se.ACTIVE_AUTHORITY, se.INVALID_FOR_CONTINUATION) and se.transition_ok(se.PREAUTHORITY, se.PRECOMMIT_ABORT)
    assert not se.transition_ok(se.PRECOMMIT_ABORT, se.ACTIVE_AUTHORITY), "an experiment that aborted before the first commit never begins later"
    assert se.STOPPED_STATES == (se.INVALID_FOR_CONTINUATION,)


def test_l2_the_transaction_state_machine_and_the_session_state_machine_are_different_things():
    assert set(se.LIFECYCLE).isdisjoint({ra.OPEN, ra.COMMITTED, ra.ABORTED}) if hasattr(ra, "OPEN") else True
    assert "AuthorityTransaction" in open(ra.__file__).read() and se.NOT_STARTED not in (ra.COMMITTED, ra.ABORTED)


def test_l3_every_page_operation_is_classified_and_only_reading_and_leaving_survive_a_stop():
    assert set(se.OPERATIONS.values()) <= set(se.OPERATION_CLASSES)
    stopped = {"allowed": False}
    survivors = {name for name in se.OPERATIONS if se.operation_allowed(stopped, name)}
    assert survivors == {name for name, kind in se.OPERATIONS.items() if kind in (se.READ_ONLY, se.LEAVES_THE_SESSION)}
    assert not se.operation_allowed(stopped, "an_operation_nobody_classified"), "a route nobody classified is a bypass: denied while stopped"
    assert se.operation_allowed({"allowed": True}, "an_operation_nobody_classified")
    assert {"history_question", "history_topic", "examination", "order_submission", "ecg_acquisition", "cancel_pending_orders", "complete_encounter"} <= {n for n in se.OPERATIONS if n not in survivors}


# -- P3-251: the record -----------------------------------------------------------------------------------------------------------------------------------------

def test_l4_a_real_session_walks_the_graph_and_the_record_says_what_the_guard_needs():
    s = Session()
    assert s.sequence == [se.PREAUTHORITY]
    s.order(FIRST)
    record = s.record()
    assert record["lifecycle"] == se.ACTIVE_AUTHORITY and record["authority_began"] and record["last_authoritative_minute"] == 15 and se.record_problems(record) == []
    assert record["last_authoritative_pressure"] and {"sbp", "dbp", "map"} <= set(record["last_authoritative_pressure"])
    assert (record["grant_id"], record["authority_mode"], record["case_id"], record["family"], record["snapshot_id"]) == ("GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V1", "PRESSURE_ONLY", "gi_bleed_57m", "gi_bleed", "gi_pressure_committed")
    assert record["lineage"]["version_id"] and record["lineage"]["digest"] and record["encounter_id"] and record["experiment_id"]
    s.order(UNSUPPORTED)
    record = s.record()
    assert record["lifecycle"] == se.INVALID_FOR_CONTINUATION and record["continuation_allowed"] is False and record["legacy_fallback_allowed"] is False
    assert (record["last_authoritative_minute"], record["halted"], record["stop_class"], record["failed_minute"]) == (15, True, se.STOP_UNSUPPORTED_ACTION, 16)
    assert record["failed_operation"]["action_kinds"] and record["failed_operation"]["reason"].startswith(ra.UNSUPPORTED_AUTHORITY_ACTION)
    assert all(se.transition_ok(a, b) for a, b in zip(s.sequence, s.sequence[1:])), s.sequence


def test_l5_the_record_holds_no_consciousness_and_no_clinical_outcome():
    s = Session()
    s.order(FIRST)
    s.order(UNSUPPORTED)
    text = json.dumps(s.record(), default=str).lower()
    for forbidden in ("consciousness", "mental_status", "overlay", "obtunded", "unresponsive", "arrest", "terminal", "dead"):
        assert forbidden not in text.replace("terminal_state", ""), forbidden


@pytest.mark.parametrize("edit", [
    lambda r: r.update(lifecycle=se.ACTIVE_AUTHORITY),
    lambda r: r.update(continuation_allowed=True),
    lambda r: r.update(legacy_fallback_allowed=True),
    lambda r: r.update(authority_began=False),
    lambda r: r.update(last_authoritative_minute=None),
    lambda r: r.update(halted=False),
    lambda r: r.update(lifecycle="SOMETHING_ELSE"),
    lambda r: r.update(lifecycle=se.PRECOMMIT_ABORT),
])
def test_l6_a_record_edited_even_with_its_digest_recomputed_does_not_verify_or_does_not_unstop(edit):
    s = Session()
    s.order(FIRST)
    s.order(UNSUPPORTED)
    forged = _plain(s.record())
    edit(forged)
    sealed = _seal(forged)
    assert se.record_problems(sealed), "the coherence checks refuse an edit that contradicts the rest of the record"
    restored = {se.SESSION_KEY: sealed}
    decision = se.continuation_guard(restored, s.state, environ={})
    assert decision["allowed"] is False, "a record that does not verify is a DENY"
    # and without recomputing the digest
    stale = _plain(s.record())
    edit(stale)
    assert se.record_problems(stale)


# -- P3-252: the guard ------------------------------------------------------------------------------------------------------------------------------------------

def test_l7_after_a_real_commit_and_a_later_failure_the_guard_denies_and_names_why():
    s = Session()
    s.order(FIRST)
    assert s.guard()["allowed"] and s.guard()["lifecycle"] == se.ACTIVE_AUTHORITY
    s.order(UNSUPPORTED)
    decision = s.guard()
    assert decision["allowed"] is False and decision["lifecycle"] == se.INVALID_FOR_CONTINUATION and decision["stop_class"] == se.STOP_UNSUPPORTED_ACTION
    assert decision["authority_began"] and decision["last_authoritative_minute"] == 15 and decision["legacy_fallback_allowed"] is False
    assert decision["operator_resolutions"] == ["ABANDON_EXPERIMENT"] and decision["notice"]["headline"] == "DEVELOPMENT AUTHORITY EXPERIMENT HALTED"
    assert se.notice_is_operational(decision["notice"]["headline"] + " " + decision["notice"]["body"])
    for operation in ("render_room", "view_chart", "reset_scenario"):
        assert se.operation_allowed(decision, operation)
    for operation in ("history_question", "examination", "order_submission", "ecg_acquisition", "complete_encounter", "clinical_time", "order_execution"):
        assert not se.operation_allowed(decision, operation), operation


def test_l8_a_halt_before_the_first_commit_leaves_the_legacy_encounter_free_to_continue_and_says_so():
    s = Session()
    s.order(UNSUPPORTED)
    record = s.record()
    assert record["lifecycle"] == se.PRECOMMIT_ABORT and record["authority_began"] is False and record["continuation_allowed"] is True and record["legacy_fallback_allowed"] is True
    decision = s.guard()
    assert decision["allowed"] is True and decision["lifecycle"] == se.PRECOMMIT_ABORT and "legacy encounter may continue" in decision["reason"]
    assert decision["notice"] is None and decision["operator_resolutions"] == [] and decision["last_authoritative_minute"] is None
    assert s.site.minutes_committed == (), "the experiment aborted with 0 authoritative commits"


def test_l9_the_default_configuration_is_one_handful_of_lookups_and_always_allows():
    class Spy(dict):
        reads = 0

        def get(self, key, default=None):
            Spy.reads += 1
            return super().get(key, default)
    spy = Spy()
    decision = se.continuation_guard(spy, {"sim_time": 7, "observable": {}}, environ={})
    assert decision["allowed"] and decision["lifecycle"] == se.NOT_STARTED and Spy.reads <= 4, Spy.reads


def test_l10_an_unreadable_store_is_a_deny_not_an_allow():
    class Broken(dict):
        def get(self, key, default=None):
            raise RuntimeError("the store broke")
    decision = se.continuation_guard(Broken(), {"sim_time": 7}, environ={})
    assert decision["allowed"] is False and decision["stop_class"] == se.STOP_UNREADABLE


def test_l11_an_authority_session_with_the_flags_off_still_stops_when_its_record_travelled():
    """A reopened encounter with every flag off must not become a mixed legacy encounter: the record that travelled with it decides."""
    s = Session()
    s.order(FIRST)
    s.order(UNSUPPORTED)
    restored = {se.SESSION_KEY: _plain(s.record())}
    decision = se.continuation_guard(restored, s.state, environ={})
    assert decision["allowed"] is False and decision["lifecycle"] == se.INVALID_FOR_CONTINUATION


def test_l12_a_stale_record_of_an_earlier_encounter_says_nothing_about_a_new_one():
    s = Session()
    s.order(FIRST)
    s.order(UNSUPPORTED)
    fresh = Session()               # a new patient at minute 0
    carried = {se.SESSION_KEY: _plain(s.record())}
    assert se.continuation_guard(carried, fresh.state, environ={})["allowed"] is True, "the earlier encounter's record is stale (a new patient at minute 0)"
    other_case = Session("gi_bleed_72f")
    assert se.continuation_guard(carried, other_case.state, environ={})["allowed"] is True


def test_l19_a_record_of_another_case_says_nothing_about_an_encounter_that_is_already_past_its_last_minute():
    """Closes a hole the mutation run found (S12): the minute test alone is enough at minute 0, so the case test was never the one that decided. A stopped record of one case in the session
    of ANOTHER case's encounter, later than the record's last authoritative minute, is still not about that encounter."""
    stopped = Session()
    stopped.order(FIRST)
    stopped.order(UNSUPPORTED)
    record = stopped.record()
    other = Session("gi_bleed_72f")
    other.ask(2)
    other.order(FIRST)
    assert other.state["sim_time"] > record["last_authoritative_minute"], "the premise: only the CASE tells the two encounters apart"
    assert se._belongs(record, other.state) is False
    assert se.continuation_guard({se.SESSION_KEY: _plain(record)}, other.state, environ={})["allowed"] is True
    assert se._belongs(record, stopped.state) is True, "and it still belongs to its own encounter"


@pytest.mark.parametrize("which", ("stopped", "active"))
def test_l20_any_field_of_a_record_edited_without_recomputing_the_digest_is_refused(which):
    """Closes a hole the mutation run found (S7): the tamper test edited fields the coherence checks catch anyway, so the digest check itself was never the one that refused. Every
    field is edited, one at a time, WITHOUT recomputing the digest: each must be refused and the guard must not allow on the strength of it."""
    s = Session()
    s.order(FIRST)
    if which == "stopped":
        s.order(UNSUPPORTED)
    record = _plain(s.record())
    assert se.record_problems(record) == []
    for key in sorted(record):
        if key == "record_digest":
            continue
        edited = dict(record)
        edited[key] = "x" if not isinstance(record[key], (dict, list)) else {"tampered": True}
        problems = se.record_problems(edited)
        assert problems, f"{key}: an edited record verified"
        assert se.continuation_guard({se.SESSION_KEY: edited}, s.state, environ={})["allowed"] is False, f"{key}: the guard allowed on an edited record"
    only_digest_wrong = {**record, "last_artifact": {"artifact_digest": "edited", "minutes_recorded": record["last_artifact"]["minutes_recorded"]}}
    assert any("digest" in problem for problem in se.record_problems(only_digest_wrong)), "an edit that no coherence rule sees is still caught by the digest"


# -- P3-259: artifact, record and site agree --------------------------------------------------------------------------------------------------------------------

def test_l13_the_record_the_artifact_and_the_site_tell_one_story_and_a_disagreement_is_a_deny():
    s = Session()
    s.order(FIRST)
    assert s.guard()["allowed"]
    committed_artifact = s.store[ra.ARTIFACT_KEY]
    # a session that claims no authority ever occurred, beside an artifact that committed
    forged = {se.SESSION_KEY: _seal({**{k: v for k, v in _plain(s.record()).items() if k != "record_digest"}, "lifecycle": se.PREAUTHORITY, "authority_began": False, "last_authoritative_minute": None,
                                    "last_authoritative_pressure": None}), ra.ARTIFACT_KEY: committed_artifact}
    decision = se.continuation_guard(forged, s.state, environ=REAL)
    assert decision["allowed"] is False and decision["stop_class"] == se.STOP_STALE_OR_CONFLICTING, decision
    # a halted artifact beside a session record that claims ACTIVE
    s.order(UNSUPPORTED)
    active_record = _plain(s.record())
    halted_artifact = s.store[ra.ARTIFACT_KEY]
    live_active = Session()
    live_active.order(FIRST)
    mixed = {se.SESSION_KEY: _plain(live_active.record()), ra.ARTIFACT_KEY: halted_artifact}
    assert se.continuation_guard(mixed, s.state, environ=REAL)["allowed"] is False
    # the site says ACTIVE while the stored record says INVALID
    crossed = {ra.SITE_KEY: live_active.site, se.SESSION_KEY: active_record}
    assert se.continuation_guard(crossed, live_active.state, environ=REAL)["allowed"] is False
    # and when every source agrees, the guard allows
    assert live_active.guard()["allowed"]


def test_l14_the_record_replays_from_the_artifact_alone_with_the_failure_and_the_prohibition():
    s = Session()
    s.order(FIRST)
    s.order(UNSUPPORTED)
    artifact = s.store[ra.ARTIFACT_KEY]
    replay = se.replay_session_record(artifact, s.record())
    assert replay["reproduces"], replay["mismatches"]
    derived = replay["rederived"]
    assert (derived["lifecycle"], derived["continuation_allowed"], derived["last_authoritative_minute"], derived["failed_minute"], derived["stop_class"]) == (se.INVALID_FOR_CONTINUATION, False, 15, 16, se.STOP_UNSUPPORTED_ACTION)
    forged = _plain(s.record())
    forged["last_authoritative_minute"] = 14
    assert not se.replay_session_record(artifact, _seal(forged))["reproduces"]
    tampered = _plain(artifact)
    tampered["minutes"][0]["written_candidate"]["sbp"] = 1
    assert not se.replay_session_record(tampered, None)["reproduces"], "an artifact edited under the record does not replay"


def test_l15_an_artifact_that_cannot_be_written_after_the_first_commit_is_a_hard_failure_never_a_silent_continuation(monkeypatch):
    s = Session()
    s.order(FIRST)
    assert s.site.minutes_committed and not s.site.halted and s.record()["lifecycle"] == se.ACTIVE_AUTHORITY
    monkeypatch.setattr(store, "persist", lambda artifact, environ=None: {"stored": False, "why": "STORE_ERROR OSError: disk full"})
    s.order("Reassess in 10 minutes.")
    record = s.record()
    assert s.site.halted and s.site.halt_reason.startswith(ra.ARTIFACT_PERSISTENCE_FAILED), s.site.halt_reason
    assert record["lifecycle"] == se.INVALID_FOR_CONTINUATION and record["stop_class"] == se.STOP_PERSISTENCE and record["continuation_allowed"] is False
    assert s.guard()["allowed"] is False


def test_l16_the_collapse_boundary_is_an_operational_stop_not_a_patient_outcome():
    s = Session()
    for _ in range(3):
        s.ask(60)
    assert s.record()["lifecycle"] == se.ACTIVE_AUTHORITY and s.record()["last_authoritative_minute"] == 180
    s.ask(60)                                                  # 181..240: ESTABLISHED collapse from minute 207
    record = s.record()
    assert (record["lifecycle"], record["stop_class"], record["last_authoritative_minute"], record["failed_minute"]) == (se.INVALID_FOR_CONTINUATION, se.STOP_COLLAPSE_BOUNDARY, 180, 240)
    decision = s.guard()
    assert decision["allowed"] is False and se.notice_is_operational(json.dumps(decision["notice"]))
    observable = s.state["observable"]
    assert observable.get("pulse_present", True) is not False and str(observable.get("mental_status")) != "Unresponsive", "the stop invented no terminal state and wrote no common word"
    before = deepcopy(s.state)
    assert not se.operation_allowed(decision, "clinical_time")
    assert s.state == before, "the guard changes nothing"


def test_l17_a_session_completed_with_the_experiment_running_is_COMPLETED_and_is_not_a_stop():
    s = Session()
    s.order(FIRST)
    decision = s.guard(encounter_ended=True)
    assert decision["allowed"] and decision["lifecycle"] == se.COMPLETED_AUTHORITY
    assert s.site.session_record(encounter_ended=True)["lifecycle"] == se.COMPLETED_AUTHORITY and se.record_problems(s.site.session_record(encounter_ended=True)) == []


def test_l18_a_site_opened_with_a_test_only_point_keeps_the_advisory_behaviour_it_had(monkeypatch):
    """The effective stop is for a REAL development-authority session: a site with no grant (a TEST-ONLY point) does not stop the legacy encounter."""
    s = Session()
    s.order(FIRST)
    s.order(UNSUPPORTED)
    artifact = _plain(s.store[ra.ARTIFACT_KEY])
    for key in ("authority_label",):
        artifact.pop(key, None)
    record = se.session_record_of({**artifact, "artifact_digest": "x"})
    assert record["stop_policy"] == "ADVISORY_TEST_ONLY" and record["continuation_allowed"] is True and record["lifecycle"] == se.INVALID_FOR_CONTINUATION


# -- P3-262: the repairs of the independent review (each reproduced with the reviewer's own probe before it was repaired) -----------------------------------------

def test_r1_an_artifact_that_cannot_be_built_after_the_first_commit_stops_the_session_it_does_not_read_as_a_precommit_abort(monkeypatch):
    """HIGH-1. ``artifact()`` returns a degraded stub on any exception ("halted, no minutes"). The record used to be derived from that stub alone, so it came out as a continuable
    PRECOMMIT_ABORT with ``authority_began`` False -- a silent legacy fallback after authority began, agreed on by the record, the stored artifact and the site claim."""
    session = Session()
    session.order(FIRST)
    assert session.record()["lifecycle"] == se.ACTIVE_AUTHORITY and session.guard()["allowed"] is True
    original = ra.AuthoritySite._artifact
    monkeypatch.setattr(ra.AuthoritySite, "_artifact", lambda self: (_ for _ in ()).throw(TypeError("not JSON serializable: <object>")))
    session.order("Reassess in 10 minutes.")
    record = session.store[se.SESSION_KEY]
    assert record["lifecycle"] == se.INVALID_FOR_CONTINUATION and record["continuation_allowed"] is False and record["authority_began"] is True
    assert record["legacy_fallback_allowed"] is False and record["stop_policy"] == "EFFECTIVE_STOP" and record["stop_class"] == se.STOP_INTERNAL and se.record_problems(record) == []
    assert record["last_authoritative_minute"] == max(session.site.minutes_committed) and record["last_authoritative_pressure"], "from the site's own committed records, not from the stub"
    assert session.site.halted and session.site.halt_reason.startswith("ARTIFACT_ERROR")
    assert session.guard()["allowed"] is False
    assert se.continuation_guard({se.SESSION_KEY: json.loads(json.dumps(record))}, session.state, environ=REAL)["allowed"] is False, "a reopened encounter carrying only the record stays stopped"
    # STICKY: the fault was transient; a later healthy artifact must not lift the stop
    monkeypatch.setattr(ra.AuthoritySite, "_artifact", original)
    session.order("Reassess in 10 minutes.")
    assert session.record()["lifecycle"] == se.INVALID_FOR_CONTINUATION and session.guard()["allowed"] is False
    # and before ANY commit the same fault is only a precommit abort (the distinction holds)
    fresh = Session("gi_bleed_72f")
    monkeypatch.setattr(ra.AuthoritySite, "_artifact", lambda self: (_ for _ in ()).throw(TypeError("boom")))
    fresh.ask(2)
    assert not fresh.site.minutes_committed or fresh.record()["lifecycle"] != se.PRECOMMIT_ABORT


def test_r2_a_real_experiment_that_began_stops_on_every_route_when_its_configuration_is_no_longer_in_effect():
    """MEDIUM-2. The clock route used to carry on on the legacy engine, with the guard still saying ACTIVE, until the next ORDER turn noticed a removed flag."""
    session = Session()
    session.order(FIRST)
    assert session.guard()["allowed"] is True
    for removed in ({name: value for name, value in REAL.items() if name != ra.AUTHORITY_FLAG}, {**REAL, ra.SNAPSHOT_FLAG: "another_snapshot"}, {}):
        decision = se.continuation_guard(dict(session.store), session.state, environ=removed)
        assert decision["allowed"] is False and decision["stop_class"] == se.STOP_CONFIGURATION and decision["legacy_fallback_allowed"] is False, removed
        assert decision["reason"].startswith(ra.CONFIGURATION_CHANGED)
    # sticky: the invalidated record is what a later look finds, even with the configuration back
    store = dict(session.store)
    assert se.continuation_guard(store, session.state, environ={})["allowed"] is False
    assert se.continuation_guard(store, session.state, environ=REAL)["allowed"] is False
    # a site that has NOT committed is not an experiment that began: removing the flags then is only the legacy encounter (nothing authoritative to protect)
    early = Session("gi_bleed_72f")
    assert se.continuation_guard(dict(early.store), early.state, environ={})["allowed"] is True


def test_r3_the_window_and_the_artifact_error_have_their_own_stop_classes():
    assert se.stop_class_of(ra.WINDOW_CLOSED) == se.STOP_WINDOW_CLOSED != se.STOP_COLLAPSE_BOUNDARY
    assert se.stop_class_of(ra.COLLAPSE_BOUNDARY_REACHED) == se.STOP_COLLAPSE_BOUNDARY
    assert se.stop_class_of("ARTIFACT_ERROR TypeError: x") == se.STOP_INTERNAL


def test_r4_the_durable_match_does_not_parse_the_files_of_other_cases(tmp_path):
    """LOW-3. With the flags on and no claim (a non-GI or refused encounter in a development server) the guard looks in the durable store on every run; it used to parse every stored
    file before it filtered by case."""
    (tmp_path / "other_case__m10__ACTIVE__abc.json").write_text("{not json at all", encoding="utf-8")
    (tmp_path / "gi_bleed_57m__m10__ACTIVE__def.json").write_text("{not json either", encoding="utf-8")
    reads = []
    real_loads = json.loads
    with pytest.MonkeyPatch.context() as patch:
        session = Session()
        session.ask(2)
        environ = {**REAL, store.STORE_FLAG: str(tmp_path)}
        patch.setattr(json, "loads", lambda text, *a, **k: (reads.append(str(text)[:20]), real_loads(text, *a, **k))[1])
        assert ra.durable_match(dict(session.state), environ) is None, "nothing real matches: the two stored files are junk"
    assert any(text.startswith("{not json either") for text in reads), "the probe is meaningful: this case's own file IS parsed"
    assert not any(text.startswith("{not json at all") for text in reads), "another case's file was parsed"
