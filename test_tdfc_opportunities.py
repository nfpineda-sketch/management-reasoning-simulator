"""TD1, F1, C1 and C3 declared case by case from the faculty's TDFC decisions (cycle 8).

The faculty approved TDFC-1 to 6 and 8 conceptually as recommended on 2026-09-28 (cycle 7
instruction, §28) and deferred the implementation to cycle 8; the model is C14's (§92):
draft -> decision -> declaration per case -> provenance -> frozen with the encounter. A YES
names the component it lets the faculty observe and what stays outside (§30); C4 stays out
(§93). acs_54m_inferior waited for DF-20 (the recommendation of TDFC-5); the faculty closed DF-20
with no change on 2026-09-29 (cycle 9) and its rows are declared.
"""
import pytest

import case_assessment_bank
import evaluation_basis
import faculty_analysis
import observation_opportunities as opportunities
import tdfc_declarations
import tdfc_review

TD_F_C = ("TD1", "F1", "C1", "C3")


def record(basis, challenge_id="R2-03"):
    return {"id": "fixture", "challenge_id": challenge_id, "encounter": {"evaluation_basis": basis},
            "payload": {"session": {}}}


def test_the_bank_declares_exactly_the_rows_the_approved_decisions_derive():
    final = tdfc_review.final_states()
    assert set(final) == set(case_assessment_bank.CASES) - set(tdfc_review.PENDING)
    for case_id, rows in final.items():
        declared = case_assessment_bank.CASES[case_id]["objectives"]
        assert {objective: declared[objective]["opportunity"] for objective in TD_F_C} == rows, case_id


def test_the_counts_are_the_totals_the_faculty_approved():
    # With acs_54m_inferior's rows, since DF-20 was closed (cycle 9): TD1 26/5, F1 26/5, C1 19/12,
    # C3 10/21 (docs/tdfc/TDFC_DECISIONS_FOR_NICOLAS.md).
    assert tdfc_review.PENDING == {}
    assert tdfc_review.counts() == {"TD1": (26, 5), "F1": (26, 5), "C1": (19, 12), "C3": (10, 21)}
    assert tdfc_review.counts(tdfc_review.derive(tdfc_review.APPROVED)) == tdfc_review.counts()


def test_tdfc_6_is_the_recommendation_not_the_draft():
    final = tdfc_review.final_states()
    assert {case: final[case]["C3"] for case in ("pneumonia_46f", "pneumonia_83m", "pulmonary_embolism_61m",
                                                 "pulmonary_embolism_33f", "asthma_24f",
                                                 "anaphylaxis_63m_betablocked")} == {
        "pneumonia_46f": "yes", "pneumonia_83m": "yes", "pulmonary_embolism_61m": "yes",
        "pulmonary_embolism_33f": "no", "asthma_24f": "no", "anaphylaxis_63m_betablocked": "no"}


def test_a_yes_names_its_component_and_what_stays_outside_and_a_no_its_reason():
    for case_id, rows in tdfc_declarations.DECLARATIONS.items():
        for objective, row in rows.items():
            if row["opportunity"] == "yes":
                assert row["rationale"] and row["observable_component"] and row["expected_evidence"], (case_id, objective)
                assert row["outside_the_encounter"].startswith(tdfc_declarations.OUTSIDE[objective])
            else:
                assert row["reason"] and "observable_component" not in row, (case_id, objective)
    assert opportunities.verify_bank() == []


def test_each_row_says_which_decision_settled_it_and_on_what_basis():
    for case_id, rows in tdfc_declarations.DECLARATIONS.items():
        for objective, row in rows.items():
            reviewed = row["reviewed"]
            assert (reviewed["by"], reviewed["on"], reviewed["source"], reviewed["version"]) == (
                "Nicolás Pineda", "2026-09-28", "faculty_decision", "TDFC-REVIEW-1")
            assert reviewed["decision_group"] == tdfc_review.decision_group(case_id, objective)
            assert "§28" in reviewed["basis"]
    groups = {row["reviewed"]["decision_group"] for rows in tdfc_declarations.DECLARATIONS.values()
              for row in rows.values()}
    assert groups == {"clear", "TDFC-1", "TDFC-2", "TDFC-3", "TDFC-4", "TDFC-5", "TDFC-6"}


def test_a_new_encounter_freezes_the_rows_and_reads_them_as_declared():
    view = opportunities.summary(record(evaluation_basis.freeze("acs_66f_nonst")))
    for objective in TD_F_C:
        assert (view[objective]["state"], view[objective]["eligible"], view[objective]["rule"]) == (
            "no", False, "declared"), objective
    c3 = opportunities.resolve("C3", record(evaluation_basis.freeze("pneumonia_46f")))
    assert (c3["state"], c3["eligible"], c3["rule"]) == ("yes", True, "declared")
    assert c3["observable_component"] and c3["outside_the_encounter"]
    assert c3["reviewed"]["decision_group"] == "TDFC-6"


def test_an_encounter_frozen_before_keeps_the_transition_it_started_with():
    frozen = evaluation_basis.freeze("pneumonia_46f")
    for objective in TD_F_C:
        frozen["declaration"]["objectives"].pop(objective)
    frozen["fingerprint"] = evaluation_basis.fingerprint(frozen["declaration"])
    view = opportunities.summary(record(frozen))
    for objective in TD_F_C:
        assert (view[objective]["state"], view[objective]["eligible"], view[objective]["rule"]) == (
            "not_reviewed", True, "transition_fallback")


@pytest.mark.parametrize("basis", [
    lambda: evaluation_basis.freeze("AI-FIXTURE-1", spec={"case_family": "generated"}),
    lambda: evaluation_basis.freeze(""),
])
def test_generated_cases_and_encounters_without_a_case_keep_the_transition(basis):
    view = opportunities.summary(record(basis()))
    for objective in TD_F_C:
        assert (view[objective]["state"], view[objective]["rule"]) == ("not_reviewed", "transition_fallback")
    assert (view["C4"]["state"], view["C4"]["eligible"]) == ("no", False)


def test_c4_stays_out_whatever_the_case():
    for case_id in case_assessment_bank.CASES:
        assert case_assessment_bank.CASES[case_id]["objectives"]["C4"]["opportunity"] == "no"
        assert "C4" not in tdfc_declarations.DECLARATIONS.get(case_id, {})


def test_the_brief_is_told_the_component_and_what_stays_outside_and_offered_only_the_declared_yes():
    yes = record(evaluation_basis.freeze("pneumonia_46f"))
    row = faculty_analysis._objective_rubric("C3", yes)
    assert set(row["observation_opportunity"]) >= {"rationale", "observable_component", "expected_evidence",
                                                   "outside_the_encounter", "guidance"}
    offered = faculty_analysis.supported_objectives(yes)
    assert {"TD1", "F1", "C1", "C3"} <= set(offered)
    stable = faculty_analysis.supported_objectives(record(evaluation_basis.freeze("acs_66f_nonst")))
    assert not {"TD1", "F1", "C1", "C3", "C4"} & set(stable)


def test_the_published_final_table_is_the_bank_s():
    from pathlib import Path
    document = (Path(__file__).resolve().parent / "docs" / "tdfc" / "TDFC_TABLA_FINAL.md").read_text(encoding="utf-8")
    assert document.endswith(tdfc_review.final_table_markdown())
