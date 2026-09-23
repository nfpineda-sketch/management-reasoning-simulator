"""Proposal and review kept apart, kept in full, and never silently regraded."""
from copy import deepcopy
import time
import uuid

import pytest

import rubric
from account_store import AccountError, AccountStore
from faculty_analysis import source_fingerprint
from rubric_analysis import PROMPT_VERSION, SCHEMA_VERSION
from rubric_store import RubricStore, build_review, totals_of

CASE = "acs_48m_wellens"


@pytest.fixture
def cohort(tmp_path):
    accounts = AccountStore(f"sqlite:///{tmp_path / 'accounts.sqlite3'}", allow_sqlite=True)
    users = {}
    with accounts._transaction(write=True) as connection:
        for username, role, year in (("faculty", "faculty", None), ("other_faculty", "faculty", None),
                                     ("resident", "resident", 1)):
            user_id = uuid.uuid4().hex
            accounts._execute(connection, "INSERT INTO mrs_users VALUES (?, ?, ?, ?, ?, 1, ?)",
                              (user_id, username, "unused-fixture-password-hash", role, year,
                               int(time.time())))
            users[username] = {"id": user_id, "token": accounts._new_session(connection, user_id)}
    return accounts, RubricStore(accounts), users


def completed_attempt(accounts, token):
    attempt_id = accounts.create_attempt(token, "R1-03", {"presentation": "Synthetic test encounter"})
    accounts.save_attempt(token, attempt_id, {
        "schema_version": "mrs_attempt_v1",
        "session": {
            "review_completed": True,
            "encounter": {"authored_case_id": CASE},
            "management_trace": [
                {"execution_status": "executed", "learner_input": "Give aspirin 300 mg PO.",
                 "decision_time_min": 0, "response_time_min": 3,
                 "reasoning": {"problem_representation": "A synthetic working model"},
                 "state_before": {"observable": {"mental_status": "alert"}},
                 "state_after": {"observable": {"mental_status": "alert"}}}],
        },
    }, status="completed")
    return attempt_id


def proposal_for(record, scores=None, events=()):
    scores = scores or {d: 2 for d in rubric.DOMAIN_IDS}
    return {
        "schema_version": SCHEMA_VERSION, "prompt_version": PROMPT_VERSION,
        "rubric_version": rubric.VERSION, "coverage_version": "1.0",
        "source_hash": source_fingerprint(record), "attempt_id": record["id"],
        "attempt_revision": record["revision"], "generated_at": "2026-09-23T00:00:00+00:00",
        "model": "fixture-model", "assistance_context": "unknown", "case_id": CASE,
        "proposal": {
            "domains": [{
                "domain_id": d, "score": scores[d], "evidence_refs": ["trace:0"],
                "learner_evidence": [{"evidence_ref": "trace:0", "minute": 0,
                                      "quote": "Give aspirin 300 mg PO."}],
                "rationale": "An antiplatelet was executed with a stated expectation.",
                "contrary_evidence": "Only one decision is recorded.",
                "limits": "A short trace.",
            } for d in rubric.DOMAIN_IDS],
            "critical_events": [{"event_id": e, "evidence_refs": ["trace:0"],
                                 "trigger_evidence": "Nothing was executed in the window.",
                                 "exclusions_checked": "The encounter did not close early."}
                                for e in events],
            "concerns_for_review": [], "assistance_recorded": [],
            "record_limits": ["One decision is recorded."],
        },
    }


# --- the decision itself, without a database --------------------------------
def test_a_confirmed_review_covers_all_five_domains():
    with pytest.raises(AccountError):
        build_review(case_id=CASE, scores={"D1": 2}, reasons={}, events=(),
                     justifications={}, status="confirmed")
    review = build_review(case_id=CASE, scores={d: 2 for d in rubric.DOMAIN_IDS},
                          reasons={}, events=(), justifications={}, status="confirmed")
    assert review["totals"]["base"] == 10 and review["totals"]["adjusted"] == 10


def test_not_assessable_must_carry_its_reason():
    scores = {d: 2 for d in rubric.DOMAIN_IDS} | {"D4": rubric.NOT_ASSESSABLE}
    with pytest.raises(AccountError):
        build_review(case_id=CASE, scores=scores, reasons={}, events=(),
                     justifications={}, status="confirmed")
    review = build_review(case_id=CASE, scores=scores,
                          reasons={"D4": "The encounter closed before a response could be observed."},
                          events=(), justifications={}, status="confirmed")
    assert review["totals"]["base"] is None
    assert review["reasons"]["D4"]


def test_a_draft_may_be_saved_before_the_reasons_are_written():
    """A draft is work in progress; the confirmation is where it is held.

    The reviewer's selector starts every domain at "not assessable"
    (2026-09-23), so requiring the reason to save a draft would mean no draft
    could be saved without writing five of them first.
    """
    scores = {domain: rubric.NOT_ASSESSABLE for domain in rubric.DOMAIN_IDS}
    draft = build_review(case_id=CASE, scores=scores, reasons={}, events=(),
                         justifications={}, status="draft")
    assert draft["status"] == "draft"
    assert draft["totals"]["coverage"]["assessed"] == 0
    # Confirming the same thing is still refused until each one says why.
    with pytest.raises(AccountError):
        build_review(case_id=CASE, scores=scores, reasons={}, events=(),
                     justifications={}, status="confirmed")


def test_changing_a_proposed_score_requires_a_justification():
    record = {"id": "a", "revision": 0}
    proposal = {"proposal": {"domains": [{"domain_id": d, "score": 2} for d in rubric.DOMAIN_IDS],
                             "critical_events": []}}
    scores = {d: 2 for d in rubric.DOMAIN_IDS} | {"D3": 0}
    with pytest.raises(AccountError):
        build_review(case_id=CASE, scores=scores, reasons={}, events=(), justifications={},
                     status="confirmed", proposal=proposal)
    review = build_review(case_id=CASE, scores=scores, reasons={}, events=(),
                          justifications={"D3": "The antiplatelet was never executed."},
                          status="confirmed", proposal=proposal)
    assert review["changes"]["D3"] == {"proposed": 2, "confirmed": 0,
                                       "justification": "The antiplatelet was never executed."}
    assert "D1" not in review["changes"]


def test_an_event_the_case_never_defined_cannot_be_confirmed():
    with pytest.raises(AccountError):
        build_review(case_id=CASE, scores={d: 2 for d in rubric.DOMAIN_IDS}, reasons={},
                     events=[{"event_id": "invented_event", "status": "confirmed",
                              "justification": "x"}],
                     justifications={}, status="confirmed")


def test_a_proposed_event_must_be_resolved_before_confirming():
    proposal = {"proposal": {"domains": [{"domain_id": d, "score": 2} for d in rubric.DOMAIN_IDS],
                             "critical_events": [{"event_id": "acs_no_antiplatelet"}]}}
    scores = {d: 2 for d in rubric.DOMAIN_IDS}
    with pytest.raises(AccountError) as raised:
        build_review(case_id=CASE, scores=scores, reasons={}, events=(), justifications={},
                     status="confirmed", proposal=proposal)
    assert "acs_no_antiplatelet" in str(raised.value)
    dismissed = build_review(case_id=CASE, scores=scores, reasons={},
                             events=[{"event_id": "acs_no_antiplatelet", "status": "dismissed"}],
                             justifications={}, status="confirmed", proposal=proposal)
    assert dismissed["totals"]["penalty"] == 0
    confirmed = build_review(case_id=CASE, scores=scores, reasons={},
                             events=[{"event_id": "acs_no_antiplatelet", "status": "confirmed"}],
                             justifications={}, status="confirmed", proposal=proposal)
    assert confirmed["totals"]["penalty"] == 3 and confirmed["totals"]["adjusted"] == 7


def test_an_event_the_faculty_adds_alone_needs_a_justification():
    scores = {d: 2 for d in rubric.DOMAIN_IDS}
    with pytest.raises(AccountError):
        build_review(case_id=CASE, scores=scores, reasons={},
                     events=[{"event_id": "acs_provocation_test", "status": "confirmed"}],
                     justifications={}, status="confirmed")
    review = build_review(case_id=CASE, scores=scores, reasons={},
                          events=[{"event_id": "acs_provocation_test", "status": "confirmed",
                                   "justification": "A stress test was ordered at minute 20."}],
                          justifications={}, status="confirmed")
    assert review["critical_events"][0]["proposed_by_ai"] is False
    assert review["critical_events"][0]["kind"] == "dangerous_action"


def test_the_same_event_is_not_decided_twice():
    with pytest.raises(AccountError):
        build_review(case_id=CASE, scores={d: 2 for d in rubric.DOMAIN_IDS}, reasons={},
                     events=[{"event_id": "acs_no_antiplatelet", "status": "confirmed",
                              "justification": "x"},
                             {"event_id": "acs_no_antiplatelet", "status": "dismissed",
                              "justification": "y"}],
                     justifications={}, status="confirmed")


def test_a_review_from_an_earlier_rubric_is_not_recomputed():
    """An updated instrument must not silently regrade an earlier encounter."""
    review = build_review(case_id=CASE, scores={d: 3 for d in rubric.DOMAIN_IDS}, reasons={},
                          events=(), justifications={}, status="confirmed")
    assert totals_of(review)["recomputed"] is True
    old = {**review, "rubric_version": "0.9-earlier",
           "totals": {**review["totals"], "base": 11, "adjusted": 11}}
    kept = totals_of(old)
    assert kept["recomputed"] is False and kept["base"] == 11
    assert kept["rubric_version"] == "0.9-earlier"


# --- the store --------------------------------------------------------------
def test_a_proposal_and_a_review_are_stored_apart_and_both_survive(cohort):
    accounts, store, users = cohort
    attempt_id = completed_attempt(accounts, users["resident"]["token"])
    token = users["faculty"]["token"]

    saved = store.save_proposal(token, attempt_id, proposal_for(
        accounts.get_attempt(token, attempt_id), events=("acs_no_antiplatelet",)))
    assert saved["proposal_id"]
    assert store.latest_proposal(token, attempt_id)["proposal_id"] == saved["proposal_id"]

    review = store.save_review(token, attempt_id, proposal_id=saved["proposal_id"],
                               scores={d: 2 for d in rubric.DOMAIN_IDS},
                               events=[{"event_id": "acs_no_antiplatelet", "status": "dismissed",
                                        "justification": "Aspirin was executed at minute 0."}],
                               status="confirmed")
    assert review["totals"]["adjusted"] == 10 and review["totals"]["penalty"] == 0
    # The proposal is untouched by the review that disagreed with it.
    assert store.latest_proposal(token, attempt_id)["proposal"]["critical_events"][0][
        "event_id"] == "acs_no_antiplatelet"


def test_every_change_is_a_new_revision_and_the_history_is_kept(cohort):
    accounts, store, users = cohort
    attempt_id = completed_attempt(accounts, users["resident"]["token"])
    token = users["faculty"]["token"]
    store.save_review(token, attempt_id, scores={d: 1 for d in rubric.DOMAIN_IDS}, status="draft")
    store.save_review(token, attempt_id, scores={d: 2 for d in rubric.DOMAIN_IDS}, status="draft")
    store.save_review(token, attempt_id, scores={d: 3 for d in rubric.DOMAIN_IDS},
                      status="confirmed")
    history = store.history(token, attempt_id)
    assert [row["status"] for row in history] == ["confirmed", "draft", "draft"]
    assert [row["totals"]["base"] for row in history] == [15, 10, 5]
    assert store.latest_review(token, attempt_id)["totals"]["base"] == 15
    assert len({row["review_id"] for row in history}) == 3


def test_only_a_confirmed_review_says_it_is_confirmed(cohort):
    accounts, store, users = cohort
    attempt_id = completed_attempt(accounts, users["resident"]["token"])
    token = users["faculty"]["token"]
    draft = store.save_review(token, attempt_id, scores={"D1": 2}, status="draft")
    assert draft["status"] == "draft"
    assert draft["totals"]["base"] is None      # a partial draft has no total
    assert store.latest_review(token, attempt_id)["status"] == "draft"


def test_the_reviewer_is_recorded(cohort):
    accounts, store, users = cohort
    attempt_id = completed_attempt(accounts, users["resident"]["token"])
    store.save_review(users["faculty"]["token"], attempt_id,
                      scores={d: 2 for d in rubric.DOMAIN_IDS}, status="confirmed")
    store.save_review(users["other_faculty"]["token"], attempt_id,
                      scores={d: 3 for d in rubric.DOMAIN_IDS}, status="confirmed")
    history = store.history(users["faculty"]["token"], attempt_id)
    assert [row["reviewer"] for row in history] == ["other_faculty", "faculty"]


def test_a_resident_can_neither_propose_nor_review(cohort):
    accounts, store, users = cohort
    attempt_id = completed_attempt(accounts, users["resident"]["token"])
    token = users["resident"]["token"]
    with pytest.raises(AccountError):
        store.latest_proposal(token, attempt_id)
    with pytest.raises(AccountError):
        store.save_review(token, attempt_id, scores={d: 3 for d in rubric.DOMAIN_IDS})


def test_a_proposal_from_another_encounter_is_refused(cohort):
    accounts, store, users = cohort
    first = completed_attempt(accounts, users["resident"]["token"])
    second = completed_attempt(accounts, users["resident"]["token"])
    token = users["faculty"]["token"]
    record = accounts.get_attempt(token, first)
    with pytest.raises(AccountError):
        store.save_proposal(token, second, proposal_for(record))
