"""The profile's trajectory follows the encounters, not the confirmations (L-F04).

Found by the cycle 5 night audit and decided on 2026-09-28: the profile ordered
the confirmed rubrics by when a faculty member confirmed them. Confirming an
earlier encounter later made it the "latest", and a resident who went from 1
to 3 was shown "-2 on the previous one". The trajectory is now ordered by when
each encounter was played; when it was confirmed is kept as audit metadata.
The means do not depend on the order and do not change. Which revision of one
encounter counts (L-F02) is a separate decision and is not touched here.
"""
import rubric
import rubric_progress
from rubric import DOMAIN_IDS
from test_rubric_store import cohort, completed_attempt  # noqa: F401  (fixture)


def _set(accounts, sql, values):
    with accounts._transaction(write=True) as connection:
        accounts._execute(connection, sql, values)


def test_confirming_an_earlier_encounter_later_does_not_make_it_the_latest(cohort):  # noqa: F811
    accounts, store, users = cohort
    first = completed_attempt(accounts, users["resident"]["token"])
    second = completed_attempt(accounts, users["resident"]["token"])
    _set(accounts, "UPDATE mrs_attempts SET created_at = ? WHERE id = ?", (1000, first))
    _set(accounts, "UPDATE mrs_attempts SET created_at = ? WHERE id = ?", (2000, second))
    token = users["faculty"]["token"]
    # The second encounter is confirmed first; the first one only later.
    store.save_review(token, second, scores={d: 3 for d in DOMAIN_IDS}, status="confirmed")
    store.save_review(token, first, scores={d: 1 for d in DOMAIN_IDS}, status="confirmed")
    _set(accounts, "UPDATE mrs_rubric_reviews SET created_at = ? WHERE attempt_id = ?", (3000, second))
    _set(accounts, "UPDATE mrs_rubric_reviews SET created_at = ? WHERE attempt_id = ?", (4000, first))

    reviews = store.progress(token, users["resident"]["id"])
    assert [review["attempt_id"] for review in reviews] == [first, second]
    # When each was confirmed is kept, beside when it was played.
    assert [(review["encounter_at"], review["created_at"]) for review in reviews] == [(1000, 4000), (2000, 3000)]

    summary = rubric_progress.aggregate(reviews)
    domain = summary["domains"]["D1"]
    assert domain["values"] == [1, 3]
    assert domain["latest"] == 3 and domain["change"] == 2
    assert domain["mean"] == 2.0

    rows = rubric_progress.results(reviews)
    assert [(row["attempt_id"], row["encounter_at"], row["confirmed_at"]) for row in rows] == [
        (first, 1000, 4000), (second, 2000, 3000)]


def test_the_means_are_the_same_whatever_the_order_of_confirmation():
    def review(encounter_at, confirmed_at, value):
        return {"status": "confirmed", "encounter_at": encounter_at, "created_at": confirmed_at, "sequence": 1,
                "scores": {d: value for d in DOMAIN_IDS}, "rubric_version": rubric.VERSION,
                "totals": {"critical_events": 0, "coverage": {"complete": True}, "adjusted": 5 * value}}

    by_encounter = rubric_progress.aggregate([review(1, 9, 1), review(2, 8, 2), review(3, 7, 3)])
    shuffled = rubric_progress.aggregate([review(3, 7, 3), review(1, 9, 1), review(2, 8, 2)])
    assert by_encounter == shuffled
    assert by_encounter["domains"]["D2"]["values"] == [1, 2, 3]
    assert by_encounter["domains"]["D2"]["mean"] == 2.0
    assert by_encounter["mean_adjusted"] == 10.0


def test_a_review_that_does_not_say_when_it_was_played_keeps_its_place_by_confirmation():
    reviews = [{"status": "confirmed", "created_at": 9, "sequence": 1, "scores": {"D1": 1},
                "rubric_version": rubric.VERSION, "totals": {}},
               {"status": "confirmed", "created_at": 2, "sequence": 1, "scores": {"D1": 3},
                "rubric_version": rubric.VERSION, "totals": {}}]
    assert rubric_progress.aggregate(reviews)["domains"]["D1"]["values"] == [3, 1]
