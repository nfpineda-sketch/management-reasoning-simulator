"""Who may read a resident's profile, and what a profile is allowed to contain.

The decision recorded here (faculty, 2026-09-23): the rubric document is the
faculty's until a faculty member completes it, and once it is confirmed the
resident may see it. So a profile is built from confirmed reviews only.

A draft on a resident's record would be a score nobody gave them.
"""
import rubric
import rubric_progress
from account_store import AccountError
from rubric_store import RubricStore
from test_rubric_store import cohort, completed_attempt  # noqa: F401  (fixtures)

import pytest


def confirmed(store, users, attempt_id, scores, status="confirmed"):
    return store.save_review(users["faculty"]["token"], attempt_id, scores=scores, status=status)


def test_a_resident_reads_their_own_profile(cohort):
    accounts, store, users = cohort
    attempt_id = completed_attempt(accounts, users["resident"]["token"])
    confirmed(store, users, attempt_id, {d: 2 for d in rubric.DOMAIN_IDS})
    rows = store.progress(users["resident"]["token"])
    assert [row["attempt_id"] for row in rows] == [attempt_id]
    assert rubric_progress.aggregate(rows)["domains"]["D1"]["mean"] == 2


def test_a_resident_cannot_read_another_residents_profile(cohort):
    accounts, store, users = cohort
    with pytest.raises(AccountError):
        store.progress(users["resident"]["token"], users["faculty"]["id"])


def test_faculty_read_the_resident_they_selected(cohort):
    accounts, store, users = cohort
    attempt_id = completed_attempt(accounts, users["resident"]["token"])
    confirmed(store, users, attempt_id, {d: 3 for d in rubric.DOMAIN_IDS})
    rows = store.progress(users["faculty"]["token"], users["resident"]["id"])
    assert [row["attempt_id"] for row in rows] == [attempt_id]


def test_a_draft_never_reaches_the_profile(cohort):
    accounts, store, users = cohort
    attempt_id = completed_attempt(accounts, users["resident"]["token"])
    confirmed(store, users, attempt_id, {d: 0 for d in rubric.DOMAIN_IDS}, status="draft")
    assert store.progress(users["resident"]["token"]) == []


def test_confirming_a_draft_brings_that_encounter_in(cohort):
    accounts, store, users = cohort
    attempt_id = completed_attempt(accounts, users["resident"]["token"])
    confirmed(store, users, attempt_id, {d: 0 for d in rubric.DOMAIN_IDS}, status="draft")
    confirmed(store, users, attempt_id, {d: 2 for d in rubric.DOMAIN_IDS})
    rows = store.progress(users["resident"]["token"])
    assert len(rows) == 1 and rows[0]["scores"]["D1"] == 2


def test_one_encounter_contributes_once_however_often_it_was_revised(cohort):
    accounts, store, users = cohort
    attempt_id = completed_attempt(accounts, users["resident"]["token"])
    confirmed(store, users, attempt_id, {d: 1 for d in rubric.DOMAIN_IDS})
    confirmed(store, users, attempt_id, {d: 3 for d in rubric.DOMAIN_IDS})
    rows = store.progress(users["resident"]["token"])
    assert len(rows) == 1
    # The latest confirmed revision is the one that counts, not the first.
    assert rows[0]["scores"]["D1"] == 3
    assert rubric_progress.aggregate(rows)["encounters"] == 1


def test_an_unassessed_encounter_is_absent_rather_than_a_zero(cohort):
    accounts, store, users = cohort
    completed_attempt(accounts, users["resident"]["token"])
    assessed = completed_attempt(accounts, users["resident"]["token"])
    confirmed(store, users, assessed, {d: 3 for d in rubric.DOMAIN_IDS})
    summary = rubric_progress.aggregate(store.progress(users["resident"]["token"]))
    assert summary["encounters"] == 1
    assert summary["domains"]["D1"]["mean"] == 3


def test_the_profile_is_ordered_by_when_the_encounters_were_assessed(cohort):
    accounts, store, users = cohort
    first = completed_attempt(accounts, users["resident"]["token"])
    second = completed_attempt(accounts, users["resident"]["token"])
    confirmed(store, users, first, {d: 1 for d in rubric.DOMAIN_IDS})
    confirmed(store, users, second, {d: 3 for d in rubric.DOMAIN_IDS})
    rows = store.progress(users["resident"]["token"])
    assert [row["attempt_id"] for row in rows] == [first, second]
    assert rubric_progress.aggregate(rows)["domains"]["D1"]["values"] == [1, 3]


def test_a_signed_out_token_reads_nothing(cohort):
    accounts, store, users = cohort
    with pytest.raises(AccountError):
        store.progress("not-a-token")
