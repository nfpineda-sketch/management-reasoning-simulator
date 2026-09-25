"""The review circuit and the cumulative profile, checked in isolation.

Faculty specification of 2026-09-24, sections 12-14. Everything here runs on a
temporary database with accounts made for the test: the batch's own pending
evaluations are never read, confirmed or touched, and no approval is attributed
to a real faculty member.

Section 14, one test each:
  1. encounters and suggestions reach the resident (by permission) and the
     administrator's review queue;
  2. confirming a rubric updates the cumulative chart;
  3. confirming a challenge observation updates the history and progress;
  4. the two confirmations are independent;
  5. correcting an evaluation updates it without duplicating, and keeps the trail;
  6. reloading, regenerating a document or saving twice duplicates nothing;
  7. everything survives signing out and back in, and a restart.
"""
import time
import uuid

import pytest

import rubric
import rubric_progress
from account_store import AccountError, AccountStore
from progress_store import ProgressStore
from rubric_store import RubricStore
from test_assistance_autonomy_and_what_waits_for_the_faculty import completed


@pytest.fixture
def cohort(tmp_path):
    path = tmp_path / "accounts.sqlite3"
    accounts = AccountStore(f"sqlite:///{path}", allow_sqlite=True)
    users = {}
    with accounts._transaction(write=True) as connection:
        for username, role, year in (("faculty_test", "faculty", None), ("admin_test", "admin", None),
                                     ("resident_test", "resident", 3), ("other_test", "resident", 2)):
            user_id = uuid.uuid4().hex
            accounts._execute(connection, "INSERT INTO mrs_users VALUES (?, ?, ?, ?, ?, 1, ?)",
                              (user_id, username, "unused-fixture-hash", role, year, int(time.time())))
            users[username] = {"id": user_id, "token": accounts._new_session(connection, user_id)}
    return accounts, users, path


def scores(**changes):
    return {**{domain: 2 for domain in rubric.DOMAIN_IDS}, **changes}


OBSERVATION = {"satisfactory": True, "depth": "integrated", "autonomy": "prompted",
               "context": "Septic shock", "evidence_refs": ["trace:0"],
               "notes": "Recognised the hypotension and reassessed it."}


# --- section 12: the cumulative profile ----------------------------------------

def review(version=rubric.VERSION, created_at=1, attempt="a", events=(), **domain_scores):
    values = scores(**domain_scores)
    return {"status": "confirmed", "rubric_version": version, "created_at": created_at,
            "sequence": 1, "attempt_id": attempt, "challenge_id": "R1-03", "case_id": "x",
            "scores": values, "critical_events": list(events),
            "totals": rubric.score(values, events)}


def test_a_draft_never_reaches_the_profile():
    draft = {**review(), "status": "draft"}
    assert rubric_progress.aggregate([draft])["encounters"] == 0


def test_a_domain_averages_only_where_it_was_assessable_and_not_assessable_is_not_zero():
    summary = rubric_progress.aggregate([
        review(attempt="a", created_at=1, D4=rubric.NOT_ASSESSABLE, D1=3),
        review(attempt="b", created_at=2, D4=0, D1=1)])
    assert summary["domains"]["D4"]["mean"] == 0 and summary["domains"]["D4"]["encounters"] == 1
    assert summary["domains"]["D1"]["mean"] == 2 and summary["domains"]["D1"]["encounters"] == 2


def test_a_domain_nobody_could_assess_has_no_data():
    summary = rubric_progress.aggregate([review(D5=rubric.NOT_ASSESSABLE)])
    assert summary["domains"]["D5"]["mean"] is None
    row = next(r for r in rubric_progress.table(summary, "es") if r["domain_id"] == "D5")
    assert row["mean_label"] == "—" and row["note"] == "Sin encuentro en que fuera evaluable"


def test_two_rubric_versions_are_never_averaged_together():
    summary = rubric_progress.aggregate([
        review(version="0.9-draft", attempt="old", created_at=1, D1=0),
        review(attempt="new", created_at=2, D1=3)])
    assert summary["rubric_version"] == rubric.VERSION
    assert summary["encounters"] == 1 and summary["domains"]["D1"]["mean"] == 3
    assert summary["set_apart"] == {"0.9-draft": 1}
    # Still reachable, and marked as not averaged.
    assert [(row["attempt_id"], row["included"]) for row in summary["results"]] == [
        ("old", False), ("new", True)]


def test_alerts_are_listed_with_their_encounter_and_date_and_never_averaged():
    event = {"event_id": "opioid_unsafe_discharge", "status": "confirmed"}
    first = review(attempt="a", created_at=100, D5=0, events=(event,))
    summary = rubric_progress.aggregate([first, review(attempt="b", created_at=200)])
    assert summary["critical_events"] == 1
    assert summary["alerts"] == [{"event_id": "opioid_unsafe_discharge", "attempt_id": "a",
                                  "confirmed_at": 100, "rubric_version": rubric.VERSION}]
    assert summary["domains"]["D5"]["mean"] == 1.0  # (0 + 2) / 2: the penalty is not in it


def test_every_result_stays_reachable_with_its_date():
    summary = rubric_progress.aggregate([review(attempt="a", created_at=100),
                                         review(attempt="b", created_at=200, D2=rubric.NOT_ASSESSABLE)])
    assert [row["confirmed_at"] for row in summary["results"]] == [100, 200]
    assert summary["results"][1]["scores"]["D2"] == rubric.NOT_ASSESSABLE
    assert summary["results"][1]["adjusted"] is None and summary["results"][1]["assessed"] == 4


def test_the_profile_says_what_it_is_not():
    assert "not a validated measure of current competence" in rubric_progress.FRAMING[0]
    assert "No es una medida validada de competencia actual" in rubric_progress.FRAMING[1]


# --- section 14 ------------------------------------------------------------------

def test_14_1_the_encounter_reaches_the_resident_and_the_review_queue(cohort):
    accounts, users, _ = cohort
    attempt_id = completed(accounts, users["resident_test"]["token"])
    mine = accounts.list_attempts(users["resident_test"]["token"])
    assert [a["id"] for a in mine] == [attempt_id]
    assert accounts.list_attempts(users["other_test"]["token"]) == []  # nobody else's
    from curriculum_runtime import _awaiting_review
    queue = _awaiting_review({"store": accounts, "token": users["admin_test"]["token"]})
    assert queue[attempt_id].startswith("rubric")


def test_14_2_confirming_a_rubric_updates_the_cumulative_chart(cohort):
    accounts, users, _ = cohort
    attempt_id = completed(accounts, users["resident_test"]["token"])
    store = RubricStore(accounts)
    resident = users["resident_test"]["id"]
    before = rubric_progress.aggregate(store.progress(users["admin_test"]["token"], resident))
    store.save_review(users["faculty_test"]["token"], attempt_id, scores=scores(), status="draft")
    drafted = rubric_progress.aggregate(store.progress(users["admin_test"]["token"], resident))
    store.save_review(users["faculty_test"]["token"], attempt_id, scores=scores(D1=3), status="confirmed")
    after = rubric_progress.aggregate(store.progress(users["admin_test"]["token"], resident))
    assert before["encounters"] == drafted["encounters"] == 0
    assert after["encounters"] == 1 and after["domains"]["D1"]["mean"] == 3


def test_14_3_confirming_a_challenge_observation_updates_history_and_progress(cohort):
    accounts, users, _ = cohort
    attempt_id = completed(accounts, users["resident_test"]["token"])
    progress = ProgressStore(accounts)
    progress.assess(users["faculty_test"]["token"], attempt_id, "TD1", OBSERVATION)
    goal = next(g for g in progress.get_progress(users["faculty_test"]["token"],
                                                 users["resident_test"]["id"])["objectives"]
                if g["objective_id"] == "TD1")
    [observation] = goal["observations"]
    assert goal["count"] == 1 and observation["attempt_id"] == attempt_id
    assert observation["assessor"] == "faculty_test" and observation["created_at"]
    # An observation is not a completed challenge: that is a separate decision.
    assert goal["confirmed"] is False


def test_14_4_the_two_confirmations_are_independent(cohort):
    accounts, users, _ = cohort
    attempt_id = completed(accounts, users["resident_test"]["token"])
    progress, store = ProgressStore(accounts), RubricStore(accounts)
    store.save_review(users["faculty_test"]["token"], attempt_id, scores=scores(), status="confirmed")
    assert all(goal["assessed_count"] == 0 for goal in progress.get_progress(
        users["faculty_test"]["token"], users["resident_test"]["id"])["objectives"])
    other = completed(accounts, users["resident_test"]["token"])
    progress.assess(users["faculty_test"]["token"], other, "TD1", OBSERVATION)
    assert [r["attempt_id"] for r in store.progress(users["admin_test"]["token"],
                                                    users["resident_test"]["id"])] == [attempt_id]


def test_14_5_a_correction_replaces_without_duplicating_and_keeps_the_trail(cohort):
    accounts, users, _ = cohort
    attempt_id = completed(accounts, users["resident_test"]["token"])
    store = RubricStore(accounts)
    faculty = users["faculty_test"]["token"]
    store.save_review(faculty, attempt_id, scores=scores(D3=1), status="confirmed")
    store.save_review(faculty, attempt_id, scores=scores(D3=3), status="confirmed")
    profile = store.progress(users["admin_test"]["token"], users["resident_test"]["id"])
    assert len(profile) == 1 and profile[0]["scores"]["D3"] == 3
    assert [row["sequence"] for row in store.history(faculty, attempt_id)] == [2, 1]
    # A challenge observation is corrected by voiding it with a reason: both stay.
    progress = ProgressStore(accounts)
    first = progress.assess(faculty, attempt_id, "TD1", OBSERVATION)
    progress.void_observation(users["admin_test"]["token"], first["observation_id"], "Recorded against the wrong objective.")
    goal = next(g for g in progress.get_progress(faculty, users["resident_test"]["id"])["objectives"]
                if g["objective_id"] == "TD1")
    assert goal["count"] == 0 and [o["voided"] for o in goal["observations"]] == [True]


def test_14_6_reloading_regenerating_or_saving_twice_duplicates_nothing(cohort):
    accounts, users, _ = cohort
    attempt_id = completed(accounts, users["resident_test"]["token"])
    store, progress = RubricStore(accounts), ProgressStore(accounts)
    faculty = users["faculty_test"]["token"]
    for _ in range(2):
        store.save_review(faculty, attempt_id, scores=scores(), status="confirmed")
    assert len(store.progress(faculty, users["resident_test"]["id"])) == 1
    progress.assess(faculty, attempt_id, "TD1", OBSERVATION)
    assert progress.assess(faculty, attempt_id, "TD1", OBSERVATION)["status"] == "duplicate"
    # A document is rendered from what is stored and writes nothing back.
    from rubric_report import render_rubric_report_pdf
    latest = store.latest_review(faculty, attempt_id)
    record = accounts.get_attempt(faculty, attempt_id)
    snapshot = store.progress(faculty, users["resident_test"]["id"])
    render_rubric_report_pdf(latest, None, record)
    render_rubric_report_pdf(latest, None, record)
    assert store.progress(faculty, users["resident_test"]["id"]) == snapshot


def test_14_7_everything_survives_signing_out_and_a_restart(cohort):
    accounts, users, path = cohort
    attempt_id = completed(accounts, users["resident_test"]["token"])
    RubricStore(accounts).save_review(users["faculty_test"]["token"], attempt_id,
                                      scores=scores(), status="confirmed")
    ProgressStore(accounts).assess(users["faculty_test"]["token"], attempt_id, "TD1", OBSERVATION)
    # A restart: a new store over the same database, and a new session.
    restarted = AccountStore(f"sqlite:///{path}", allow_sqlite=True)
    with restarted._transaction(write=True) as connection:
        token = restarted._new_session(connection, users["admin_test"]["id"])
    assert len(RubricStore(restarted).progress(token, users["resident_test"]["id"])) == 1
    goal = next(g for g in ProgressStore(restarted).get_progress(token, users["resident_test"]["id"])["objectives"]
                if g["objective_id"] == "TD1")
    assert goal["count"] == 1
    with pytest.raises(AccountError):
        # The resident's old session still reads only their own record.
        RubricStore(restarted).progress(users["resident_test"]["token"], users["other_test"]["id"])
