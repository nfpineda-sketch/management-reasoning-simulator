"""C14 in the bank: the faculty's clinical review of 2026-09-28, applied (DF-13, cycle 5).

Fourteen cases declare a real opportunity to use POCUS to guide management and sixteen
declare there is none, each with who reviewed it, when, and under which decision (A-H of
docs/C14_DECISIONES_A_H.md). acs_54m_inferior stays not reviewed until its data are resolved
(docs/AUDITORIA_ACS_54M_INFERIOR.md). What the faculty asked these tests to show (§21, §22,
§36 to §39): an opportunity makes C14 assessable and never observes it; a NO is not
evaluable, never a failure; the not-reviewed case keeps only the transition; the target
does not decide C14; historical encounters and frozen declarations do not move; and several
POCUS findings in one encounter are one observation.
"""
import time
import uuid

import pytest

import c14_review
import case_assessment_bank
import evaluation_basis
import observation_opportunities as opportunities
from account_store import AccountError
from test_observation_opportunities import assessment, cohort, completed, progress_of  # noqa: F401  (fixture)

C14 = case_assessment_bank.C14_DECLARATIONS
YES, NO, NOT_REVIEWED = "pneumonia_46f", "hypoglycemia_28m", "acs_54m_inferior"
REVIEW = {"by": "Nicolás Pineda", "on": "2026-09-28", "source": "human_clinical_review",
          "version": "C14-REVIEW-1"}


def encounter(case_id, challenge_id="R2-03"):
    return {"id": "fixture", "challenge_id": challenge_id,
            "encounter": {"evaluation_basis": evaluation_basis.freeze(case_id)}, "payload": {"session": {}}}


def without_objectives(case_id):
    """The bank case as it stood before cycle 5 wrote its C14 row."""
    return {key: value for key, value in case_assessment_bank.CASES[case_id].items() if key != "objectives"}


def resident_in_year(accounts, year):
    """Another resident, as the cohort fixture makes them: an R3 target needs the third year."""
    user_id = uuid.uuid4().hex
    with accounts._transaction(write=True) as connection:
        accounts._execute(connection, "INSERT INTO mrs_users VALUES (?, ?, ?, ?, ?, 1, ?)",
                          (user_id, f"resident{year}", "unused-fixture-password-hash", "resident", year,
                           int(time.time())))
        return accounts._new_session(connection, user_id)


def played(accounts, token, case_id, challenge_id, inputs):
    """A completed encounter whose Management Trace records these decisions, in order."""
    attempt_id = accounts.create_attempt(token, challenge_id,
                                         {"evaluation_basis": evaluation_basis.freeze(case_id)})
    accounts.save_attempt(token, attempt_id, {"schema_version": "mrs_attempt_v1", "session": {
        "review_completed": True, "management_trace": [
            {"execution_status": "executed", "learner_input": text,
             "reasoning": {"problem_representation": "A fixture working model"}} for text in inputs]}},
        status="completed")
    return attempt_id


# --- the rows the faculty approved, and only those -----------------------------------------

def test_the_bank_holds_the_reviewed_rows_and_leaves_one_case_not_reviewed():
    assert set(C14) == set(c14_review.DRAFT) - {NOT_REVIEWED}
    states = [entry["opportunity"] for entry in C14.values()]
    assert (states.count("yes"), states.count("no")) == (14, 16)
    assert "C14" not in (case_assessment_bank.CASES[NOT_REVIEWED].get("objectives") or {})
    for case_id, entry in C14.items():
        assert case_assessment_bank.CASES[case_id]["objectives"]["C14"] is entry
        reviewed = entry["reviewed"]
        assert {key: reviewed[key] for key in REVIEW} == REVIEW, case_id
        # The decision that settled the row, or "clear" for a row the draft already classified.
        assert reviewed["decision_group"] in (c14_review.decisions_for(case_id) or ["clear"]), case_id
        if entry["opportunity"] == "yes":
            assert entry["rationale"] and entry["observable_component"] and entry["expected_evidence"], case_id
        else:
            # A NO is a clinical decision with its reason, never the absence of metadata.
            assert entry["reason"] and "expected_evidence" not in entry, case_id
    assert opportunities.verify_bank() == []


def test_yes_no_and_not_reviewed_resolve_from_the_frozen_basis():
    yes = opportunities.resolve("C14", encounter(YES))
    assert (yes["state"], yes["eligible"], yes["rule"]) == ("yes", True, "declared")
    assert yes["expected_evidence"] == C14[YES]["expected_evidence"]
    assert yes["reviewed"]["decision_group"] == "C"
    no = opportunities.resolve("C14", encounter(NO))
    assert (no["state"], no["eligible"], no["rule"]) == ("no", False, "declared")
    assert no["reason"] == C14[NO]["reason"]
    # Only the documented transition: assessable as before, and labelled not reviewed.
    pending = opportunities.resolve("C14", encounter(NOT_REVIEWED))
    assert (pending["state"], pending["eligible"], pending["rule"]) == ("not_reviewed", True, "transition_fallback")
    assert pending["declaration_source"] == "case_without_objectives"
    assert not {"reason", "rationale", "expected_evidence", "reviewed"} & set(pending)


def test_the_encounter_target_never_decides_c14():
    from curriculum import CHALLENGES
    for case_id in c14_review.DRAFT:
        basis = evaluation_basis.freeze(case_id)
        seen = {tuple(opportunities.resolve("C14", {
            "id": "fixture", "challenge_id": challenge_id, "encounter": {"evaluation_basis": basis},
            "payload": {"session": {}}})[key] for key in ("state", "eligible", "rule"))
            for challenge_id in CHALLENGES}
        declared = (C14.get(case_id) or {}).get("opportunity")
        expected = {"yes": ("yes", True, "declared"), "no": ("no", False, "declared")}.get(
            declared, ("not_reviewed", True, "transition_fallback"))
        assert seen == {expected}, case_id


# --- frozen at the start; historical encounters do not move ---------------------------------

def test_the_c14_row_is_frozen_when_the_encounter_starts(monkeypatch):
    started = encounter(YES)
    monkeypatch.setitem(case_assessment_bank.CASES, YES,
                        {**case_assessment_bank.CASES[YES], "objectives": {"C14": C14[NO]}})
    assert opportunities.resolve("C14", started)["state"] == "yes"
    assert opportunities.resolve("C14", encounter(YES))["state"] == "no"


def test_an_encounter_frozen_before_the_review_keeps_the_transition(monkeypatch):
    with monkeypatch.context() as before:
        before.setitem(case_assessment_bank.CASES, NO, without_objectives(NO))
        earlier = encounter(NO)
    view = opportunities.resolve("C14", earlier)
    assert view["declaration_source"] == "case_without_objectives"
    assert (view["state"], view["eligible"], view["rule"]) == ("not_reviewed", True, "transition_fallback")
    # The review applies from the next encounter on.
    assert opportunities.resolve("C14", encounter(NO))["state"] == "no"
    # A record with no frozen copy never takes the current row either.
    legacy = {"id": "fixture", "challenge_id": "R1-06", "encounter": {},
              "payload": {"session": {"state": {"encounter_spec": {"clinical_case": {"id": NO}}}}}}
    assert opportunities.resolve("C14", legacy)["rule"] == "transition_fallback"


def test_historical_observations_are_neither_reanalysed_nor_lost(cohort, monkeypatch):
    accounts, progress, users = cohort
    resident, faculty = users["resident"]["token"], users["faculty"]["token"]
    with monkeypatch.context() as before:
        before.setitem(case_assessment_bank.CASES, NO, without_objectives(NO))
        observed = completed(accounts, resident, "R1-06", evaluation_basis.freeze(NO))
        assert progress.assess(faculty, observed, "C14", assessment())["status"] == "credited"
        waiting = completed(accounts, resident, "R1-06", evaluation_basis.freeze(NO))
    # After the review: the earlier observation still counts, and the encounter that started
    # under the transition can still be assessed under it.
    assert progress_of(progress, resident, "C14")["count"] == 1
    assert progress.assess(faculty, waiting, "C14", assessment())["status"] == "credited"
    units = progress_of(progress, resident, "C14")["observations"]
    assert [unit["provenance"]["opportunity"]["rule"] for unit in units] == ["transition_fallback"] * 2
    # A new encounter of the same case follows the review.
    new = completed(accounts, resident, "R1-06", evaluation_basis.freeze(NO))
    with pytest.raises(AccountError, match="declares no opportunity"):
        progress.assess(faculty, new, "C14", assessment())
    assert progress_of(progress, resident, "C14")["count"] == 2


# --- YES is assessable, never observed by itself; the faculty decides ------------------------

def test_a_yes_encounter_adds_nothing_until_the_faculty_assesses_it(cohort):
    accounts, progress, users = cohort
    resident, faculty = users["resident"]["token"], users["faculty"]["token"]
    attempt_id = completed(accounts, resident, "R1-05", evaluation_basis.freeze(YES))
    goal = progress_of(progress, resident, "C14")
    assert (goal["count"], goal["observations"], goal["status"]) == (0, [], "not_observed")
    waiting = next(item for item in progress.pending_reviews(faculty) if item["attempt_id"] == attempt_id)
    assert "C14" in waiting["pending_objectives"]
    # The resident cannot confirm it; a faculty member can.
    with pytest.raises(AccountError):
        progress.assess(resident, attempt_id, "C14", assessment())
    assert progress.assess(faculty, attempt_id, "C14", assessment())["status"] == "credited"
    goal = progress_of(progress, resident, "C14")
    assert goal["count"] == 1 and goal["confirmed"] is False
    opportunity = goal["observations"][0]["provenance"]["opportunity"]
    assert (opportunity["rule"], opportunity["state"]) == ("declared", "yes")
    assert opportunity["reviewed"]["by"] == "Nicolás Pineda"


def test_the_faculty_can_judge_that_a_declared_opportunity_was_not_met(cohort):
    accounts, progress, users = cohort
    resident, faculty = users["resident"]["token"], users["faculty"]["token"]
    attempt_id = completed(accounts, resident, "R1-05", evaluation_basis.freeze(YES))
    assert progress.assess(faculty, attempt_id, "C14", assessment(satisfactory=False))["status"] == "recorded"
    goal = progress_of(progress, resident, "C14")
    assert (goal["count"], goal["needs_improvement_count"]) == (0, 1)


def test_the_expected_evidence_guides_and_never_filters(cohort):
    accounts, progress, users = cohort
    resident, faculty = users["resident"]["token"], users["faculty"]["token"]
    # Nothing in this decision matches the case's expected evidence word for word.
    attempt_id = played(accounts, resident, YES, "R1-05", ["Norepinephrine 0.05 mcg/kg/min, the IVC is now full"])
    assert not any("norepinephrine" in line.lower() for line in C14[YES]["expected_evidence"])
    assert progress.assess(faculty, attempt_id, "C14", assessment())["status"] == "credited"


# --- NO: not evaluable, never a failure ----------------------------------------------------

def test_a_no_encounter_cannot_confirm_c14_and_records_no_failure(cohort):
    accounts, progress, users = cohort
    resident, faculty = users["resident"]["token"], users["faculty"]["token"]
    attempt_id = completed(accounts, resident, "R1-06", evaluation_basis.freeze(NO))
    for satisfactory in (True, False):
        with pytest.raises(AccountError, match="declares no opportunity"):
            progress.assess(faculty, attempt_id, "C14", assessment(satisfactory=satisfactory))
    goal = progress_of(progress, resident, "C14")
    assert (goal["count"], goal["assessed_count"], goal["needs_improvement_count"]) == (0, 0, 0)
    assert (goal["observations"], goal["status"]) == ([], "not_observed")
    # Not offered, so it does not wait on the faculty; the other objectives still do.
    waiting = next(item for item in progress.pending_reviews(faculty) if item["attempt_id"] == attempt_id)
    assert "C14" not in waiting["pending_objectives"] and "TD1" in waiting["pending_objectives"]
    assert progress.assess(faculty, attempt_id, "TD1", assessment())["status"] == "credited"


def test_the_brief_is_offered_c14_where_the_case_declares_it():
    import faculty_analysis
    yes, no, pending = encounter(YES), encounter(NO), encounter(NOT_REVIEWED)
    assert "C14" in faculty_analysis.supported_objectives(yes)
    assert "C14" not in faculty_analysis.supported_objectives(no)
    assert "C14" in faculty_analysis.supported_objectives(pending)
    guidance = faculty_analysis._objective_rubric("C14", yes)["observation_opportunity"]
    assert guidance["expected_evidence"] == C14[YES]["expected_evidence"]
    assert "not evidence that it happened" in guidance["guidance"]
    assert "observation_opportunity" not in faculty_analysis._objective_rubric("C14", pending)


# --- incidental C14 under another target ---------------------------------------------------

@pytest.mark.parametrize("case_id, challenge_id", [
    ("pneumonia_46f", "R1-05"), ("gi_bleed_57m", "R2-05"), ("pulmonary_edema_75f", "R3-01")])
def test_c14_is_observed_incidentally_under_another_target(cohort, case_id, challenge_id):
    accounts, progress, users = cohort
    faculty = users["faculty"]["token"]
    resident = resident_in_year(accounts, int(challenge_id[1]))
    attempt_id = completed(accounts, resident, challenge_id, evaluation_basis.freeze(case_id))
    for objective_id in (challenge_id, "C14"):
        assert progress.assess(faculty, attempt_id, objective_id, assessment())["status"] == "credited"
    rules = {objective_id: progress_of(progress, resident, objective_id)["observations"][0]["provenance"]
             ["opportunity"]["rule"] for objective_id in (challenge_id, "C14")}
    assert rules == {challenge_id: "generation_target", "C14": "declared"}


# --- no double counting (§22) ---------------------------------------------------------------

def test_several_pocus_findings_in_one_encounter_are_one_observation(cohort):
    accounts, progress, users = cohort
    resident, faculty = users["resident"]["token"], users["faculty"]["token"]
    attempt_id = played(accounts, resident, YES, "R1-05", [
        "POCUS: IVC, heart and lungs", "500 mL crystalloid bolus because the IVC collapses",
        "Repeat POCUS after the bolus"])
    first = progress.assess(faculty, attempt_id, "C14", assessment(evidence_refs=["trace:0", "trace:1", "trace:2"]))
    assert (first["status"], first["count"]) == ("credited", 1)
    again = progress.assess(faculty, attempt_id, "C14", assessment(evidence_refs=["trace:2"]))
    assert (again["status"], again["count"]) == ("duplicate", 1)
    goal = progress_of(progress, resident, "C14")
    assert goal["count"] == 1 and len(goal["observations"]) == 1
    assert goal["observations"][0]["evidence_refs"] == ["trace:0", "trace:1", "trace:2"]


# --- the final table is what the bank declares ----------------------------------------------

def test_the_final_table_document_is_the_bank_s_declarations():
    from pathlib import Path
    document = (Path(__file__).resolve().parent / "docs" / "C14_TABLA_FINAL.md").read_text(encoding="utf-8")
    assert document.endswith(c14_review.final_table_markdown())
    rows = c14_review.final_table()
    assert [row["case_id"] for row in rows] == list(c14_review.DRAFT)
    assert {row["opportunity"] for row in rows if row["case_id"] == NOT_REVIEWED} == {"NOT REVIEWED"}
