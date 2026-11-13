"""P3-273 to P3-274: the durable authority PROVENANCE ANCHOR (R-FAILOPEN-2) and the lost-state recovery matrix.

TEST-SIDE. The anchor is one monotonic mark, ``AUTHORITY_OCCURRED``, that every REAL commit writes into the patient state itself (a top-level key outside the observable and outside the authority
domain). This file proves, with stubs and plain dictionaries:

* it is created at the first real commit and only ADVANCES (first minute and the experiment never change, the last minute and the count only go up); every refusal to advance is a ``ValueError``
  the site turns into a refusal of the minute, never a silent reset;
* it is digest-sealed (it detects corruption and a half-edit; it is NOT a signature -- a forger who recomputes the digest is the declared limit);
* the guard treats it as the strongest evidence that authority occurred: an anchor with NO other evidence (no site, no record, no artifact) is a stop, never an inferred legacy-only encounter; an anchor
  that does not verify, is another encounter's, or disagrees with any claim is a stop; an anchor with agreeing claims raises no objection;
* with no anchor, nothing else changed: no claims and every flag off is the plain legacy encounter, one handful of lookups.

The same matrix on the REAL page (site/record/artifact present, missing or corrupt, and the legacy engine having advanced) is in the second half of this file.
"""
from copy import deepcopy

import pytest

import runtime_authority as ra
import runtime_authority_session as se

CASE = "gi_bleed_57m"
PRESSURE = {"sbp": 82, "dbp": 48, "map": 59}


class StubSite:
    def __init__(self, *, committed=(), grant_id="grant-1", fingerprint="fp-1", encounter_id="enc-1"):
        self.case_id, self.family, self.encounter_id, self.experiment_id, self.snapshot_id = CASE, "gi_bleed", encounter_id, "exp-1", "snap-1"
        self.grant = {"grant_id": grant_id, "fingerprint": fingerprint}
        self.minutes_committed = tuple(committed)


def _state(minute, anchor=None, case=CASE):
    state = {"encounter_spec": {"variant_id": case}, "sim_time": minute, "observable": {"sbp": 80, "dbp": 50}}
    if anchor is not None:
        state[ra.PROVENANCE_ANCHOR_KEY] = anchor
    return state


def _first(minute=2):
    return se.advance_anchor(None, StubSite(), minute, PRESSURE)


def _record(anchor, **override):
    record = se.record_from_anchor(anchor, "test")
    return record


# -- the anchor itself ---------------------------------------------------------------------------------------------------------------------------------------

def test_a1_the_first_real_commit_creates_a_verifying_anchor_that_says_authority_occurred():
    anchor = _first(2)
    assert se.anchor_problems(anchor) == []
    assert anchor["authority_state"] == se.STATE_AUTHORITY_OCCURRED and anchor["record_type"] == se.ANCHOR_TYPE
    assert (anchor["first_authority_minute"], anchor["last_authority_minute"], anchor["commits"]) == (2, 2, 1)
    assert anchor["case_id"] == CASE and anchor["grant_id"] == "grant-1" and anchor["grant_fingerprint"] == "fp-1" and anchor["last_pressure"] == PRESSURE


def test_a2_a_later_commit_advances_it_and_never_rewrites_its_origin():
    one = _first(2)
    two = se.advance_anchor(one, StubSite(committed=(2,)), 7, {"sbp": 90, "dbp": 55, "map": 67})
    assert se.anchor_problems(two) == []
    assert (two["first_authority_minute"], two["last_authority_minute"], two["commits"]) == (2, 7, 2), "first stays, last and count go up"
    for name in ("case_id", "encounter_id", "experiment_id", "grant_id", "grant_fingerprint", "snapshot_id"):
        assert two[name] == one[name], name
    assert two["anchor_digest"] != one["anchor_digest"]


@pytest.mark.parametrize("label,previous,site,minute,why", [
    ("a minute that does not follow", lambda: _first(7), lambda: StubSite(committed=(7,)), 7, "does not precede"),
    ("a minute before the last", lambda: _first(7), lambda: StubSite(committed=(7,)), 3, "does not precede"),
    ("another experiment's encounter", lambda: _first(2), lambda: StubSite(committed=(2,), encounter_id="enc-2"), 7, "another experiment"),
    ("another grant", lambda: _first(2), lambda: StubSite(committed=(2,), grant_id="grant-2"), 7, "another experiment"),
    ("another grant fingerprint", lambda: _first(2), lambda: StubSite(committed=(2,), fingerprint="fp-2"), 7, "another experiment"),
    ("a count that is not the site's", lambda: _first(2), lambda: StubSite(committed=(2, 4)), 7, "counts 1 commit"),
    ("an anchor from an earlier experiment (the site has made no commit)", lambda: _first(2), lambda: StubSite(committed=()), 7, "counts 1 commit"),
    ("an encounter that LOST its anchor (the site made commits and the state carries none)", lambda: None, lambda: StubSite(committed=(2,)), 7, "lost its provenance anchor"),
])
def test_a3_an_anchor_that_cannot_advance_honestly_is_an_error_never_a_reset(label, previous, site, minute, why):
    with pytest.raises(ValueError) as error:
        se.advance_anchor(previous(), site(), minute, PRESSURE)
    assert why in str(error.value), (label, str(error.value))


def test_a3b_an_anchor_that_does_not_verify_cannot_be_advanced():
    tampered = dict(_first(2), last_authority_minute=3)
    with pytest.raises(ValueError, match="does not verify"):
        se.advance_anchor(tampered, StubSite(committed=(2,)), 7, PRESSURE)


@pytest.mark.parametrize("label,mutate", [
    ("a field edited without recomputing the digest", lambda anchor: anchor.update(last_authority_minute=9)),
    ("the digest removed", lambda anchor: anchor.pop("anchor_digest")),
    ("a field removed", lambda anchor: anchor.pop("grant_id")),
    ("the state set back to NO_AUTHORITY", lambda anchor: anchor.update(authority_state=se.STATE_NO_AUTHORITY)),
    ("a minute that is not an integer", lambda anchor: anchor.update(last_authority_minute="7")),
    ("a boolean as a minute", lambda anchor: anchor.update(commits=True)),
    ("another record type", lambda anchor: anchor.update(record_type="something_else")),
])
def test_a4_a_corrupted_anchor_does_not_verify(label, mutate):
    anchor = deepcopy(_first(2))
    mutate(anchor)
    assert se.anchor_problems(anchor), label


def test_a4a_a_sealed_anchor_that_says_no_authority_is_not_an_anchor_of_authority():
    """The monotonic mark only moves NO_AUTHORITY -> AUTHORITY_OCCURRED: a record sealed with the other state (digest recomputed, so only the state check can refuse it) never verifies."""
    body = {key: value for key, value in deepcopy(_first(2)).items() if key != "anchor_digest"}
    body["authority_state"] = se.STATE_NO_AUTHORITY
    sealed = {**body, "anchor_digest": ra.digest_of(body)}
    assert any("does not say authority occurred" in problem for problem in se.anchor_problems(sealed))


def test_a4b_the_seal_detects_corruption_and_a_half_edit_but_not_a_forger_who_recomputes_it():
    """The declared limit: a digest is not a signature. The test pins that the limit is real, so nobody mistakes the seal for one."""
    anchor = deepcopy(_first(2))
    forged = {key: value for key, value in anchor.items() if key != "anchor_digest"}
    forged["authority_state"] = se.STATE_AUTHORITY_OCCURRED
    forged["last_authority_minute"] = 5
    forged["anchor_digest"] = ra.digest_of(forged)
    assert se.anchor_problems(forged) == [], "a recomputed digest verifies: signing needs a key, a faculty decision"


def test_a5_a_record_built_from_the_anchor_alone_verifies_and_names_no_failed_minute():
    anchor = _first(7)
    record = se.record_from_anchor(anchor, "provenance lost")
    assert se.record_problems(record) == []
    assert record["lifecycle"] == se.INVALID_FOR_CONTINUATION and record["continuation_allowed"] is False and record["legacy_fallback_allowed"] is False
    assert record["authority_began"] and record["last_authoritative_minute"] == 7 and record["failed_minute"] is None and record["failed_operation"] is None
    assert record["case_id"] == CASE and record["grant_id"] == "grant-1"


# -- what the guard does with it -------------------------------------------------------------------------------------------------------------------------------

FLAGS_OFF = {}


def _guard(store, state, environ=FLAGS_OFF):
    return se.continuation_guard(store, state, environ=environ)


def test_g1_an_anchor_with_no_other_evidence_is_a_stop_never_a_legacy_only_encounter():
    """R-FAILOPEN-2, the all-lost case: no site, no session record, no artifact, every flag off, the legacy engine may even have advanced past the last authoritative minute."""
    anchor = _first(7)
    store: dict = {}
    for clock in (7, 19, 60):                                # the clock where authority left it, and well beyond it
        decision = _guard(store, _state(clock, anchor))
        assert decision["allowed"] is False and decision["lifecycle"] == se.INVALID_FOR_CONTINUATION, clock
        assert decision["stop_class"] == se.STOP_PROVENANCE and decision["legacy_fallback_allowed"] is False
        assert decision["last_authoritative_minute"] == 7 and decision["operator_resolutions"] == list(se.OPERATOR_RESOLUTIONS)
        assert ra.PROVENANCE_LOST in decision["reason"]
    assert se.record_problems(store[se.SESSION_KEY]) == [], "the stop is written as a verifying record, so it travels with the encounter and a reopened copy stays stopped"
    assert store[se.SESSION_KEY]["stop_class"] == se.STOP_PROVENANCE


def test_g1b_the_same_state_with_no_anchor_and_no_claims_is_the_plain_legacy_encounter():
    decision = _guard({}, _state(19))
    assert decision["allowed"] is True and decision["lifecycle"] == se.NOT_STARTED


def test_g2_an_anchor_that_does_not_verify_is_a_stop_because_authority_may_have_occurred():
    decision = _guard({}, _state(7, dict(_first(7), commits=5)))
    assert decision["allowed"] is False and decision["stop_class"] == se.STOP_PROVENANCE and ra.PROVENANCE_ANCHOR_INVALID in decision["reason"]
    assert decision["legacy_fallback_allowed"] is False


def test_g3_an_anchor_that_is_not_this_encounters_is_a_stop():
    other_case = _guard({}, _state(7, _first(7), case="gi_bleed_72f"))
    assert other_case["allowed"] is False and other_case["stop_class"] == se.STOP_PROVENANCE and "not this encounter's" in other_case["reason"]
    clock_before_the_anchor = _guard({}, _state(3, _first(7)))
    assert clock_before_the_anchor["allowed"] is False and "not this encounter's" in clock_before_the_anchor["reason"], "an anchor from the future of the encounter is corruption, and it is the belonging check that says so"


def test_g4_an_anchor_that_agrees_with_every_claim_raises_no_objection():
    anchor = _first(7)
    agreeing = {**se.record_from_anchor(anchor, "x"), "lifecycle": se.ACTIVE_AUTHORITY, "continuation_allowed": True, "halted": False, "halt_reason": "", "stop_class": "",
                "legacy_fallback_allowed": True, "failed_minute": None}
    body = {key: value for key, value in agreeing.items() if key != "record_digest"}
    record = {**body, "record_digest": ra.digest_of(body)}
    assert se.record_problems(record) == []
    assert se._anchor_check(anchor, {"record": record}, _state(7, anchor), {}) is None


@pytest.mark.parametrize("label,override", [
    ("says authority never began", {"authority_began": False, "last_authoritative_minute": None}),
    ("puts the last authoritative minute elsewhere", {"last_authoritative_minute": 3}),
    ("is about another encounter", {"encounter_id": "enc-9"}),
    ("names another grant", {"grant_id": "grant-9"}),
])
def test_g5_a_claim_that_disagrees_with_the_anchor_is_a_stop(label, override):
    anchor = _first(7)
    claim = {**se.record_from_anchor(anchor, "x"), **override}
    stopped = se._anchor_check(anchor, {"record": claim}, _state(7, anchor), {})
    assert stopped is not None and stopped["allowed"] is False and stopped["stop_class"] == se.STOP_STALE_OR_CONFLICTING, label


def test_g6_the_guards_cheap_path_gains_one_state_lookup_and_no_store_lookup():
    class Spy(dict):
        reads = 0

        def get(self, key, default=None):
            Spy.reads += 1
            return super().get(key, default)
    decision = _guard(Spy(), _state(0))
    assert decision["allowed"] and decision["lifecycle"] == se.NOT_STARTED and Spy.reads <= 4, Spy.reads


def test_g7_the_guard_fails_closed_when_the_anchor_cannot_be_read():
    """Never raises: a state whose anchor lookup fails, and a state whose case cannot be read once an anchor is there, are both a stop."""
    class Unreadable(dict):
        def get(self, key, default=None):
            if key == ra.PROVENANCE_ANCHOR_KEY:
                raise RuntimeError("boom")
            return super().get(key, default)
    decision = _guard({}, Unreadable(_state(7)))
    assert decision["allowed"] is False and decision["stop_class"] == se.STOP_UNREADABLE and decision["legacy_fallback_allowed"] is False
    anchor = _first(7)
    caseless = {"sim_time": 7, ra.PROVENANCE_ANCHOR_KEY: anchor}                 # no case: the anchor cannot be matched to this encounter
    assert _guard({}, caseless)["allowed"] is False
