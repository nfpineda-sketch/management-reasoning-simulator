"""DF-24, the five changes the faculty approved on 2026-09-28 (cycle 7, C7-07).

I-F02 A, L-F02 A, the voided observation's reason A, the confirmed rubric's withdrawal A
and L-F07 B. Each is pinned by its current failure, the expected behaviour and what must
not move (docs/DF24_DECISIONS_FOR_NICOLAS.md). Nothing here touches a score, a domain, the
averaging or the radar's method: L-F02 changes only which revision of one encounter feeds
the profile.
"""
import inspect

import case_assessment_bank
import evaluation_basis
import hypoglycemia_catalog
import observation_opportunities as opportunities
import progress_portal
import report_language
import resident_portal
import rubric_portal
import rubric_progress
from rubric import DOMAIN_IDS
from test_rubric_store import cohort, completed_attempt  # noqa: F401  (fixture)


def _set(accounts, sql, values):
    with accounts._transaction(write=True) as connection:
        accounts._execute(connection, sql, values)


def _confirm(store, token, attempt_id, value):
    return store.save_review(token, attempt_id, scores={d: value for d in DOMAIN_IDS}, status="confirmed")


# --- I-F02 A · the export says who confirmed the rubric --------------------------------

def test_the_export_says_who_confirmed_the_rubric_as_the_pdf_does(cohort):  # noqa: F811
    accounts, store, users = cohort
    attempt = completed_attempt(accounts, users["resident"]["token"])
    _confirm(store, users["faculty"]["token"], attempt, 2)
    [review] = store.progress(users["resident"]["token"])
    # Before: the profile's query did not join the accounts, and the export wrote "".
    assert resident_portal._exported_review(review)["reviewed_by"] == "faculty"
    released, _ = store.released(users["resident"]["token"], attempt)
    assert released["reviewer"] == review["reviewer"]


def test_who_confirmed_changes_no_number(cohort):  # noqa: F811
    accounts, store, users = cohort
    for value in (1, 3):
        _confirm(store, users["faculty"]["token"], completed_attempt(accounts, users["resident"]["token"]), value)
    reviews = store.progress(users["resident"]["token"])
    without = [{key: value for key, value in review.items() if key != "reviewer"} for review in reviews]
    assert rubric_progress.aggregate(reviews) == rubric_progress.aggregate(without)


# --- L-F02 A · the revision with the highest number feeds the radar ---------------------

def test_a_late_clock_no_longer_puts_a_superseded_revision_in_the_radar(cohort):  # noqa: F811
    accounts, store, users = cohort
    attempt = completed_attempt(accounts, users["resident"]["token"])
    first = _confirm(store, users["faculty"]["token"], attempt, 3)
    second = _confirm(store, users["other_faculty"]["token"], attempt, 1)
    # The correction was stamped by a server ten seconds late.
    _set(accounts, "UPDATE mrs_rubric_reviews SET created_at = ? WHERE id = ?", (1_000_000, first["review_id"]))
    _set(accounts, "UPDATE mrs_rubric_reviews SET created_at = ? WHERE id = ?", (999_990, second["review_id"]))
    [review] = store.progress(users["resident"]["token"])
    assert (review["sequence"], review["scores"]["D1"], review["reviewer"]) == (2, 1, "other_faculty")
    assert rubric_progress.aggregate([review])["domains"]["D1"]["values"] == [1]
    # The resident's document already chose it by number; both now say the same.
    released, _ = store.released(users["resident"]["token"], attempt)
    assert released["sequence"] == review["sequence"]


def test_two_confirmations_in_the_same_second_take_the_higher_number(cohort):  # noqa: F811
    accounts, store, users = cohort
    attempt = completed_attempt(accounts, users["resident"]["token"])
    _confirm(store, users["faculty"]["token"], attempt, 3)
    _confirm(store, users["faculty"]["token"], attempt, 2)
    _set(accounts, "UPDATE mrs_rubric_reviews SET created_at = ? WHERE attempt_id = ?", (5_000, attempt))
    [review] = store.progress(users["resident"]["token"])
    assert (review["sequence"], review["scores"]["D1"]) == (2, 2)


def test_with_ordinary_clocks_nothing_changes(cohort):  # noqa: F811
    accounts, store, users = cohort
    first = completed_attempt(accounts, users["resident"]["token"])
    second = completed_attempt(accounts, users["resident"]["token"])
    _set(accounts, "UPDATE mrs_attempts SET created_at = ? WHERE id = ?", (1000, first))
    _set(accounts, "UPDATE mrs_attempts SET created_at = ? WHERE id = ?", (2000, second))
    for attempt, values in ((first, (3, 1)), (second, (2,))):
        for value in values:
            _confirm(store, users["faculty"]["token"], attempt, value)
    reviews = store.progress(users["resident"]["token"])
    # L-F04 is untouched: encounters in the order they were played, one revision each.
    assert [(r["attempt_id"], r["sequence"], r["scores"]["D1"]) for r in reviews] == [(first, 2, 1), (second, 1, 2)]
    assert rubric_progress.aggregate(reviews)["domains"]["D1"]["mean"] == 1.5


def test_a_draft_is_never_part_of_the_profile(cohort):  # noqa: F811
    accounts, store, users = cohort
    attempt = completed_attempt(accounts, users["resident"]["token"])
    _confirm(store, users["faculty"]["token"], attempt, 3)
    store.save_review(users["faculty"]["token"], attempt, scores={d: 0 for d in DOMAIN_IDS}, status="draft")
    [review] = store.progress(users["resident"]["token"])
    assert (review["sequence"], review["scores"]["D1"]) == (1, 3)


# --- the confirmed rubric's withdrawal: A, a warning, no new state ----------------------

def test_a_draft_after_a_confirmation_is_said_to_withdraw_nothing(cohort):  # noqa: F811
    accounts, store, users = cohort
    attempt = completed_attempt(accounts, users["resident"]["token"])
    _confirm(store, users["faculty"]["token"], attempt, 1)
    store.save_review(users["faculty"]["token"], attempt, scores={d: 3 for d in DOMAIN_IDS}, status="draft")
    history = store.history(users["faculty"]["token"], attempt)
    standing = rubric_portal.superseded_by_draft(history[0], history)
    assert standing["sequence"] == 1 and standing["status"] == "confirmed"
    # What the warning says is what happens: the resident still reads the confirmed revision.
    released, _ = store.released(users["resident"]["token"], attempt)
    assert released["sequence"] == 1
    assert "superseded_by_draft(review, history)" in inspect.getsource(rubric_portal._review_form)
    notice = ("This draft does not replace confirmed revision {v0}: the resident, the profile and the radar keep "
              "showing that revision until you confirm another.")
    assert notice in inspect.getsource(rubric_portal._review_form).replace('"\n                      "', "")
    assert report_language.t(notice, "es") != notice


def test_no_warning_when_nothing_confirmed_stands_under_the_draft(cohort):  # noqa: F811
    accounts, store, users = cohort
    attempt = completed_attempt(accounts, users["resident"]["token"])
    store.save_review(users["faculty"]["token"], attempt, scores={d: 2 for d in DOMAIN_IDS}, status="draft")
    history = store.history(users["faculty"]["token"], attempt)
    assert rubric_portal.superseded_by_draft(history[0], history) is None
    _confirm(store, users["faculty"]["token"], attempt, 2)
    history = store.history(users["faculty"]["token"], attempt)
    assert rubric_portal.superseded_by_draft(history[0], history) is None


# --- the voided observation: A, the resident reads the reason, and the form says so ------

def test_the_void_form_says_the_resident_reads_the_reason():
    source = inspect.getsource(progress_portal._render_observation_correction)
    assert "_t(VOID_REASON_NOTICE)" in source
    assert source.index("VOID_REASON_NOTICE") < source.index("Reason for voiding assessment")
    assert "resident reads this reason" in progress_portal.VOID_REASON_NOTICE
    assert report_language.t(progress_portal.VOID_REASON_NOTICE, "es").startswith("La persona residente lee")


def test_what_the_resident_sees_of_a_voided_observation_is_unchanged():
    # A keeps it: the judgment, the notes, the notice and the reason (progress_portal).
    source = inspect.getsource(progress_portal)
    assert '"Voided" if row.get("voided")' in source
    assert "This observation was voided and contributes no credit." in source
    assert 'observation.get("void_reason", "")' in source


# --- L-F07 B · the compositions carry their origin's C14 NO ------------------------------

def test_each_composition_carries_the_c14_row_of_the_bank_case_it_derives_from():
    candidates = case_assessment_bank.CANDIDATES
    assert len(candidates) == 9
    for candidate_id, declaration in candidates.items():
        origin = hypoglycemia_catalog.configuration(candidate_id)["derived_from"]
        row, source = declaration["objectives"]["C14"], case_assessment_bank.CASES[origin]["objectives"]["C14"]
        assert (row["opportunity"], row["reason"]) == ("no", source["reason"]), candidate_id
        assert row["reviewed"] == {**source["reviewed"], "inherited_from": origin, "inherited_by": "DF-24 L-F07 B"}
        # Only C14 is added; the rest of the composition's declaration is its own.
        assert set(declaration["objectives"]) == {"C14"}
    assert opportunities.verify_bank() == []


def test_a_new_composition_encounter_reads_c14_as_declared_no():
    candidate = "hypoglycemia_cfg_insulin_failed_severe"
    frozen = evaluation_basis.freeze(candidate)
    record = {"id": "fixture", "challenge_id": "R2-03", "encounter": {"evaluation_basis": frozen},
              "payload": {"session": {}}}
    view = opportunities.resolve("C14", record)
    assert (view["state"], view["eligible"], view["rule"]) == ("no", False, "declared")
    assert view["reviewed"]["inherited_from"] == "hypoglycemia_28m"


def test_generated_cases_and_encounters_without_a_case_keep_the_transition():
    for frozen in (evaluation_basis.freeze("AI-FIXTURE-1", spec={"case_family": "generated"}),
                   evaluation_basis.freeze("")):
        record = {"id": "fixture", "challenge_id": "R2-03", "encounter": {"evaluation_basis": frozen},
                  "payload": {"session": {}}}
        view = opportunities.resolve("C14", record)
        assert (view["state"], view["rule"]) == ("not_reviewed", "transition_fallback")
