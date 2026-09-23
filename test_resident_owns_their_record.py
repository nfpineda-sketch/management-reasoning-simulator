"""A resident's own record, and the wall around it.

Until 2026-09-23 a resident's work vanished when they finished it: the
Management Trace could be downloaded during the encounter and never again, a
confirmed rubric assessment reached the faculty and not the person it was
about, and the plan they wrote for next time was shown once and never
collected.

The wall is the other half. A resident reads their own encounters and nothing
of anybody else's, through stores that already enforce it; these tests state
that as a property rather than trusting it.
"""
import time
import uuid

import pytest

import resident_portal
import rubric
from account_store import AccountError, AccountStore, hash_password
from rubric_store import RubricStore


CASE = "acs_48m_wellens"


@pytest.fixture
def cohort(tmp_path):
    store = AccountStore(f"sqlite:///{tmp_path / 'accounts.sqlite3'}", allow_sqlite=True)
    people = {}
    with store._transaction(write=True) as connection:
        for username, role, year in (("faculty_one", "faculty", None),
                                     ("resident_one", "resident", 1),
                                     ("resident_two", "resident", 2)):
            user_id = uuid.uuid4().hex
            store._execute(connection, "INSERT INTO mrs_users VALUES (?, ?, ?, ?, ?, 1, ?)",
                           (user_id, username, hash_password("a-password-for-tests"),
                            role, year, int(time.time())))
            people[username] = {"id": user_id, "username": username, "role": role,
                                "training_year": year,
                                "token": store._new_session(connection, user_id)}
    return store, people


def context_for(store, person):
    return {"store": store, "token": person["token"], "user": person}


def completed(store, person, *, plan=None, challenge="R1-03"):
    token = person["token"]
    attempt_id = store.create_attempt(token, challenge, {"presentation": "A synthetic encounter"})
    store.save_attempt(token, attempt_id, {
        "schema_version": "mrs_attempt_v1",
        "session": {
            "review_completed": True,
            "encounter": {"authored_case_id": CASE},
            "adaptation_plan": plan or {},
            "management_trace": [
                {"execution_status": "executed", "learner_input": "Give aspirin 300 mg PO.",
                 "decision_time_min": 0, "response_time_min": 3,
                 "reasoning": {"problem_representation": "A synthetic working model"},
                 "state_before": {"observable": {"mental_status": "alert"}},
                 "state_after": {"observable": {"mental_status": "alert"}}}],
        },
    }, status="completed")
    return attempt_id


# --- what is mine -----------------------------------------------------------

def test_a_completed_encounter_appears_in_my_own_list(cohort):
    store, people = cohort
    attempt_id = completed(store, people["resident_one"])
    listed = resident_portal.own_encounters(context_for(store, people["resident_one"]))
    assert [item["id"] for item in listed] == [attempt_id]


def test_an_encounter_still_running_is_not_listed_as_completed(cohort):
    store, people = cohort
    store.create_attempt(people["resident_one"]["token"], "R1-03", {"presentation": "x"})
    assert resident_portal.own_encounters(context_for(store, people["resident_one"])) == []


def test_the_newest_encounter_is_first(cohort):
    store, people = cohort
    first = completed(store, people["resident_one"])
    time.sleep(1.1)
    second = completed(store, people["resident_one"])
    listed = resident_portal.own_encounters(context_for(store, people["resident_one"]))
    assert [item["id"] for item in listed] == [second, first]


# --- what is not mine -------------------------------------------------------

def test_a_resident_sees_only_their_own(cohort):
    store, people = cohort
    mine = completed(store, people["resident_one"])
    theirs = completed(store, people["resident_two"])
    listed = resident_portal.own_encounters(context_for(store, people["resident_one"]))
    assert [item["id"] for item in listed] == [mine]
    assert theirs not in [item["id"] for item in listed]


def test_a_resident_cannot_open_a_peers_encounter_by_its_identifier(cohort):
    store, people = cohort
    theirs = completed(store, people["resident_two"])
    assert store.get_attempt(people["resident_one"]["token"], theirs) is None


def test_a_resident_cannot_read_a_peers_confirmed_assessment(cohort):
    store, people = cohort
    theirs = completed(store, people["resident_two"])
    RubricStore(store).save_review(people["faculty_one"]["token"], theirs,
                                   scores={d: 3 for d in rubric.DOMAIN_IDS}, status="confirmed")
    with pytest.raises(AccountError):
        RubricStore(store).released(people["resident_one"]["token"], theirs)


def test_a_resident_cannot_export_a_peers_record(cohort):
    store, people = cohort
    completed(store, people["resident_two"], plan={"next_priority": "Their private plan."})
    bundle = resident_portal.account_export(context_for(store, people["resident_one"]))
    assert bundle["encounters"] == []
    assert "Their private plan." not in str(bundle)


# --- the confirmed assessment reaches the person it is about ---------------

def test_a_draft_assessment_is_not_released(cohort):
    store, people = cohort
    attempt_id = completed(store, people["resident_one"])
    RubricStore(store).save_review(people["faculty_one"]["token"], attempt_id,
                                   scores={d: 2 for d in rubric.DOMAIN_IDS}, status="draft")
    review, _ = RubricStore(store).released(people["resident_one"]["token"], attempt_id)
    assert review is None


def test_a_confirmed_assessment_is_released_to_its_owner(cohort):
    store, people = cohort
    attempt_id = completed(store, people["resident_one"])
    RubricStore(store).save_review(people["faculty_one"]["token"], attempt_id,
                                   scores={d: 2 for d in rubric.DOMAIN_IDS}, status="confirmed")
    review, _ = RubricStore(store).released(people["resident_one"]["token"], attempt_id)
    assert review["totals"]["base"] == 10
    assert review["status"] == "confirmed"


def test_the_latest_confirmed_revision_is_the_one_released(cohort):
    store, people = cohort
    attempt_id = completed(store, people["resident_one"])
    store_r = RubricStore(store)
    store_r.save_review(people["faculty_one"]["token"], attempt_id,
                        scores={d: 1 for d in rubric.DOMAIN_IDS}, status="confirmed")
    store_r.save_review(people["faculty_one"]["token"], attempt_id,
                        scores={d: 3 for d in rubric.DOMAIN_IDS}, status="confirmed")
    review, _ = store_r.released(people["resident_one"]["token"], attempt_id)
    assert review["scores"]["D1"] == 3


def test_faculty_can_read_it_too(cohort):
    store, people = cohort
    attempt_id = completed(store, people["resident_one"])
    RubricStore(store).save_review(people["faculty_one"]["token"], attempt_id,
                                   scores={d: 2 for d in rubric.DOMAIN_IDS}, status="confirmed")
    review, _ = RubricStore(store).released(people["faculty_one"]["token"], attempt_id)
    assert review is not None


# --- the thread -------------------------------------------------------------

def test_the_plans_collect_in_the_order_they_were_written(cohort):
    store, people = cohort
    completed(store, people["resident_one"], plan={"next_priority": "Ask about medications."})
    time.sleep(1.1)
    completed(store, people["resident_one"], plan={"next_priority": "State the disposition."})
    rows = resident_portal.adaptation_thread(context_for(store, people["resident_one"]))
    assert [row["plan"]["next_priority"] for row in rows] == [
        "Ask about medications.", "State the disposition."]


def test_each_plan_names_the_encounter_that_followed_it(cohort):
    store, people = cohort
    completed(store, people["resident_one"], plan={"next_priority": "Ask about medications."},
              challenge="R1-03")
    time.sleep(1.1)
    completed(store, people["resident_one"], challenge="R1-04")
    rows = resident_portal.adaptation_thread(context_for(store, people["resident_one"]))
    assert rows[0]["next_challenge"] == "R1-04"


def test_the_most_recent_plan_has_nothing_after_it_yet(cohort):
    store, people = cohort
    completed(store, people["resident_one"], plan={"next_priority": "Ask about medications."})
    rows = resident_portal.adaptation_thread(context_for(store, people["resident_one"]))
    assert rows[0]["next_attempt_id"] is None


def test_an_encounter_with_no_plan_is_not_an_empty_row(cohort):
    store, people = cohort
    completed(store, people["resident_one"], plan={"next_priority": "   "})
    assert resident_portal.adaptation_thread(context_for(store, people["resident_one"])) == []


# --- the record they leave with --------------------------------------------

def test_the_export_carries_the_encounters_and_the_profile(cohort):
    store, people = cohort
    attempt_id = completed(store, people["resident_one"],
                           plan={"next_priority": "Ask about medications."})
    RubricStore(store).save_review(people["faculty_one"]["token"], attempt_id,
                                   scores={d: 2 for d in rubric.DOMAIN_IDS}, status="confirmed")
    bundle = resident_portal.account_export(context_for(store, people["resident_one"]))
    assert bundle["schema"] == "mrs_resident_record_v1"
    assert bundle["resident"]["username"] == "resident_one"
    assert bundle["resident"]["training_year"] == 1
    assert len(bundle["encounters"]) == 1
    entry = bundle["encounters"][0]
    assert entry["management_trace"]
    assert entry["your_adaptation_plan"]["next_priority"] == "Ask about medications."
    assert entry["confirmed_rubric"]["totals"]["base"] == 10
    assert bundle["rubric_profile"]["encounters_assessed"] == 1
    assert bundle["rubric_profile"]["per_domain"]["D1"]["mean"] == 2


def test_an_unassessed_encounter_exports_without_a_score_rather_than_a_zero(cohort):
    store, people = cohort
    completed(store, people["resident_one"])
    bundle = resident_portal.account_export(context_for(store, people["resident_one"]))
    assert bundle["encounters"][0]["confirmed_rubric"] is None
    assert bundle["rubric_profile"]["encounters_assessed"] == 0


def test_a_draft_assessment_never_reaches_the_export(cohort):
    store, people = cohort
    attempt_id = completed(store, people["resident_one"])
    RubricStore(store).save_review(people["faculty_one"]["token"], attempt_id,
                                   scores={d: 0 for d in rubric.DOMAIN_IDS}, status="draft")
    bundle = resident_portal.account_export(context_for(store, people["resident_one"]))
    assert bundle["encounters"][0]["confirmed_rubric"] is None


def test_the_export_carries_the_notice_with_it(cohort):
    store, people = cohort
    completed(store, people["resident_one"])
    bundle = resident_portal.account_export(context_for(store, people["resident_one"]))
    assert "not a" in bundle["notice"]
    assert "not ACGME Milestone levels" in bundle["notice"]
