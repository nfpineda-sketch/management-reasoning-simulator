"""C4 = NO across the observation environment (faculty, 2026-09-28: TDFC-7/8, and H4 of cycle 7).

The reason is the simulator's, not the cases': the engine does not model the procedural
components C4 observes, so no encounter it runs offers C4 -- a bank case, a generated case or an
encounter with no authored case (PS001). What these tests pin down:

* every bank case declares C4 NO explicitly, with its reason and who decided it;
* every new encounter is frozen with the environment's declaration, so generated cases and
  encounters without an authored case are NO too, and the faculty cannot confirm C4 in them;
* the declaration is prospective: an encounter frozen before it keeps the transition it started
  with, and an observation confirmed under that rule is neither lost nor re-read;
* nothing else moves: C14 and TD1 keep what they had outside the bank (L-F07 B), and the engine
  was not touched to create or remove an opportunity.
"""
import pytest

import case_assessment_bank
import evaluation_basis
import observation_opportunities as opportunities
from account_store import AccountError
from test_observation_opportunities import assessment, cohort, completed, progress_of  # noqa: F401  (fixture)

REASON = opportunities.C4_ENVIRONMENT_REASON


def record(basis, challenge_id="R2-03"):
    return {"id": "fixture", "challenge_id": challenge_id, "encounter": {"evaluation_basis": basis},
            "payload": {"session": {}}}


def generated():
    return evaluation_basis.freeze("AI-FIXTURE-1", spec={"case_family": "generated"})


def without_an_authored_case():
    # How a PS001 encounter is frozen: its clinical case names no bank case.
    return evaluation_basis.freeze("")


def before_the_environment(case_id):
    """A basis frozen before cycle 7: no environment block, and no C4 row in the case."""
    frozen = evaluation_basis.freeze(case_id)
    frozen.pop("environment"), frozen.pop("environment_fingerprint")
    if frozen.get("declaration"):
        frozen["declaration"]["objectives"].pop("C4", None)
        frozen["fingerprint"] = evaluation_basis.fingerprint(frozen["declaration"])
    return frozen


def test_every_bank_case_declares_c4_no_with_its_reason_and_provenance():
    declarations = case_assessment_bank.C4_DECLARATIONS
    assert set(declarations) == set(case_assessment_bank.CASES) and len(declarations) == 31
    for case_id, entry in declarations.items():
        assert case_assessment_bank.CASES[case_id]["objectives"]["C4"] is entry
        assert entry["opportunity"] == "no" and entry["reason"].startswith(REASON), case_id
        assert "expected_evidence" not in entry and "rationale" not in entry
        reviewed = entry["reviewed"]
        assert (reviewed["by"], reviewed["on"], reviewed["source"]) == (
            "Nicolás Pineda", "2026-09-28", "faculty_decision"), case_id
        # The colic's own analgesia is TDFC-8; every other case, TDFC-7.
        assert reviewed["decision_group"] == ("TDFC-8" if case_id == "renal_colic_34m" else "TDFC-7")
    assert opportunities.verify_bank() == []


def test_the_reason_points_to_other_sources_of_evidence_and_never_to_a_failure():
    assert "procedural simulation" in REASON and "workplace observation" in REASON
    assert "fail" not in REASON.lower()


@pytest.mark.parametrize("basis", [generated, without_an_authored_case], ids=["generated", "no_authored_case"])
def test_encounters_outside_the_bank_are_frozen_with_the_environment_s_no(basis):
    frozen = basis()
    assert frozen["environment"]["C4"]["opportunity"] == "no"
    view = opportunities.summary(record(frozen))
    c4 = view["C4"]
    assert (c4["state"], c4["eligible"], c4["rule"]) == ("no", False, "declared")
    assert c4["scope"] == "observation_environment" and c4["reason"] == REASON
    assert c4["declaration_source"] == "observation_environment"
    # Nothing else is declared for them: C14 and TD1 keep the transition (DF-12, L-F07 B).
    for objective_id in ("C14", "TD1", "F1", "C1", "C3"):
        assert (view[objective_id]["state"], view[objective_id]["rule"]) == ("not_reviewed", "transition_fallback")


def test_a_bank_case_reads_its_own_row_before_the_environment_s():
    view = opportunities.resolve("C4", record(evaluation_basis.freeze("renal_colic_34m")))
    assert (view["state"], view["rule"]) == ("no", "declared")
    assert "TDFC-8" in view["reason"] and view["reviewed"]["decision_group"] == "TDFC-8"
    assert "scope" not in view


def test_an_encounter_frozen_before_the_environment_keeps_the_transition():
    for case_id in ("pneumonia_46f", ""):
        view = opportunities.resolve("C4", record(before_the_environment(case_id)))
        assert (view["state"], view["eligible"], view["rule"]) == ("not_reviewed", True, "transition_fallback")


def test_a_tampered_environment_makes_the_basis_unreadable():
    frozen = generated()
    frozen["environment"]["C4"]["opportunity"] = "yes"
    assert evaluation_basis.resolve(record(frozen))["status"] == "corrupt"


@pytest.mark.parametrize("basis", [lambda: evaluation_basis.freeze("trauma_hemothorax_41m"), generated,
                                   without_an_authored_case], ids=["bank", "generated", "no_authored_case"])
def test_the_faculty_cannot_confirm_c4_in_a_new_encounter(cohort, basis):
    accounts, progress, users = cohort
    attempt_id = completed(accounts, users["resident"]["token"], basis=basis())
    with pytest.raises(AccountError, match="declares no opportunity"):
        progress.assess(users["faculty"]["token"], attempt_id, "C4", assessment())
    goal = progress_of(progress, users["resident"]["token"], "C4")
    assert (goal["count"], goal["observations"]) == (0, [])
    # Not offered, so it does not wait on the faculty; the objectives still open do.
    waiting = next(item for item in progress.pending_reviews(users["faculty"]["token"])
                   if item["attempt_id"] == attempt_id)
    assert "C4" not in waiting["pending_objectives"] and "TD1" in waiting["pending_objectives"]


def test_a_c4_observation_confirmed_before_stays_and_is_not_re_read(cohort):
    accounts, progress, users = cohort
    resident, faculty = users["resident"]["token"], users["faculty"]["token"]
    earlier = completed(accounts, resident, basis=before_the_environment("renal_colic_34m"))
    assert progress.assess(faculty, earlier, "C4", assessment())["status"] == "credited"
    later = completed(accounts, resident, basis=evaluation_basis.freeze("renal_colic_34m"))
    with pytest.raises(AccountError, match="declares no opportunity"):
        progress.assess(faculty, later, "C4", assessment())
    units = progress_of(progress, resident, "C4")["observations"]
    assert len(units) == 1 and units[0]["provenance"]["opportunity"]["rule"] == "transition_fallback"


def test_the_engine_offers_no_new_procedural_action_for_c4():
    # C4 = NO is a declaration, never a change to the engine: the modelled procedural
    # sedation is still the one the transition saw (pressure only, no depth).
    import family_engine
    source = open(family_engine.__file__, encoding="utf-8").read()
    assert "C4" not in source
