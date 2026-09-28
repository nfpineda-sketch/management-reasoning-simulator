"""The C14 review derives rows from the faculty's answers and writes nothing (DF-13, 2026-09-28)."""
import itertools

import pytest

import c14_review
from c14_review import DECISIONS, DRAFT, RECOMMENDED, counts, derive


def test_the_draft_covers_every_bank_case_once():
    import clinical_cases
    bank = [case["id"] for family in clinical_cases.FAMILIES.values() for case in family["variants"]]
    assert sorted(DRAFT) == sorted(bank) and len(bank) == 31
    assert counts(DRAFT) == {"yes": 6, "no": 6, "uncertain": 19}


def test_no_answer_leaves_the_draft_as_it_is():
    assert derive({}) == DRAFT


def test_every_uncertain_row_has_a_question_and_the_clear_rows_have_none():
    for case_id, drafted in DRAFT.items():
        letters = c14_review.decisions_for(case_id)
        if drafted == "uncertain":
            assert letters, case_id
        elif case_id == "pulmonary_embolism_61m":
            # Its draft YES rests on the right ventricle, which is question G.
            assert letters == ["G"]
        else:
            assert letters == [], case_id


def test_the_recommendations_derive_the_table_the_document_shows():
    rows = derive(RECOMMENDED)
    assert counts(rows) == {"yes": 14, "no": 16, "uncertain": 1}
    # Its authored POCUS contradicts the case: the uncertainty stays visible.
    assert [case for case, state in rows.items() if state == "uncertain"] == ["acs_54m_inferior"]
    assert rows["obstructive_pyelonephritis_58f"] == "yes" and rows["renal_colic_34m"] == "no"
    assert rows["pneumonia_46f"] == rows["pneumonia_83m"] == "yes"


def test_an_unanswered_question_never_becomes_a_no():
    rows = derive({"C": "reject"})
    # The pneumonias still wait on F, and the pyelonephritis on H.
    assert rows["pneumonia_46f"] == rows["obstructive_pyelonephritis_58f"] == "uncertain"
    assert rows["gi_bleed_57m"] == "no"


def test_every_combination_of_answers_gives_a_state_to_every_row():
    for answers in itertools.product(("approve", "reject"), repeat=len(DECISIONS)):
        rows = derive(dict(zip(DECISIONS, answers)))
        assert set(rows) == set(DRAFT) and set(rows.values()) <= set(c14_review.STATES)
        # Once all eight are answered, only the data inconsistency can stay uncertain.
        assert {case for case, state in rows.items() if state == "uncertain"} <= {"acs_54m_inferior"}


@pytest.mark.parametrize("answers", [{"Z": "approve"}, {"A": "modify"}])
def test_an_answer_outside_the_scheme_is_refused(answers):
    with pytest.raises(ValueError):
        derive(answers)


def test_the_bank_carries_exactly_what_the_approved_answers_derive():
    import case_assessment_bank
    rows = derive(c14_review.APPROVED)
    for case_id, state in rows.items():
        declared = (case_assessment_bank.CASES[case_id].get("objectives") or {}).get("C14")
        if state == "uncertain":
            # Uncertain after the answers: left out of the bank, so not reviewed.
            assert declared is None, case_id
        else:
            assert declared["opportunity"] == state, case_id
