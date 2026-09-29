"""DC9 (faculty, 2026-09-29): the compositions' TD/F/C rows are their origin's, as a pending proposal.

Each of the nine hypoglycaemia compositions carries its origin case's TD1, F1, C1 and C3 rows
as a traceable proposal, pending review. A proposal is never a declaration: the composition's
objectives stay as they were (the transition), the approved reference is unchanged, and a
composition with a pending proposal is offered to no resident.
"""
import case_assessment_bank
import encounter_directives
import hypoglycemia_catalog
import observation_opportunities
import tdfc_declarations
from curriculum import CHALLENGES

OBJECTIVES = ("TD1", "F1", "C1", "C3")


def test_every_composition_has_its_origin_s_rows_as_a_pending_proposal():
    proposals = tdfc_declarations.composition_proposals()
    compositions = {c["id"]: c["derived_from"] for c in hypoglycemia_catalog.review_candidates()}
    assert set(proposals) == set(compositions) and len(proposals) == 9
    for case_id, rows in proposals.items():
        origin = tdfc_declarations.DECLARATIONS[compositions[case_id]]
        assert set(rows) == set(OBJECTIVES)
        for objective, row in rows.items():
            assert row["status"] == tdfc_declarations.COMPOSITION_PROPOSAL_STATUS and row["reviewed"] is None
            assert row["proposal"]["proposed_from"] == compositions[case_id]
            assert row["proposal"]["origin_review"] == origin[objective]["reviewed"]
            kept = {k: v for k, v in row.items() if k not in {"status", "reviewed", "proposal"}}
            assert kept == {k: v for k, v in origin[objective].items() if k != "reviewed"}


def test_a_proposal_is_never_a_declaration_and_the_reference_is_untouched():
    assert not set(tdfc_declarations.DECLARATIONS) & set(tdfc_declarations.composition_proposals())
    for case_id, candidate in case_assessment_bank.CANDIDATES.items():
        assert not set(candidate.get("objectives", {})) & set(OBJECTIVES), case_id
    tdfc_declarations.composition_proposals()["hypoglycemia_cfg_insulin_failed_severe"]["TD1"]["rationale"] = "x"
    assert all(row["reviewed"] for rows in tdfc_declarations.DECLARATIONS.values() for row in rows.values())
    assert not observation_opportunities.verify_bank()


def test_no_composition_is_exposable_or_reachable_by_a_resident_path():
    for case_id in tdfc_declarations.composition_proposals():
        assert tdfc_declarations.composition_exposable(case_id) is False
    assert tdfc_declarations.composition_exposable("hypoglycemia_28m") is True
    offered = {option[0] for challenge in CHALLENGES for option in encounter_directives.case_options(challenge)}
    assert not offered & set(tdfc_declarations.composition_proposals())
