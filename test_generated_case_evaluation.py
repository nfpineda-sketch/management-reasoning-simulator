"""Opening the rubric or the analysis of a generated encounter does not break the circuit.

Faculty instruction of 2026-09-25, point 7. A generated case is named
"AI-<hash>"; until then case_assessment raised CoverageError for it and nothing
caught it. Built here from a stub author (no provider, no payment) and a local
account store: what the faculty sees is the encounter, its documents, the five
domains, and the limitation -- no opportunity, no event, no zero and no total
that was not there.
"""
import json
from types import SimpleNamespace

import pytest

import evaluation_basis
import rubric
from account_store import AccountError
from faculty_analysis import case_id_of
from rubric_analysis import build_rubric_source, generate_rubric_proposal
from rubric_store import RubricStore
from test_faculty_analysis_store import cohort  # noqa: F401  (fixture)
from test_generated_case import AuthorClient, clean_base
from test_rubric_portal import page


def _generated():
    from generated_case import generate_ai_encounter
    return generate_ai_encounter("R1-05", clean_base(), seed=5, client=AuthorClient())


def _attempt(accounts, token, *, frozen=True):
    generated = _generated()
    spec = generated["spec"]
    encounter = {"presentation": generated["presentation"], "spec": spec}
    if frozen:
        encounter["evaluation_basis"] = evaluation_basis.freeze(spec["clinical_case"]["id"], spec=spec)
    attempt_id = accounts.create_attempt(token, "R1-05", encounter)
    accounts.save_attempt(token, attempt_id, {
        "schema_version": "mrs_attempt_v1",
        "session": {"review_completed": True, "state": generated["state"],
                    "management_trace": [
                        {"execution_status": "executed", "learner_input": "Give 500 mL normal saline.",
                         "decision_time_min": 0, "response_time_min": 10,
                         "reasoning": {"problem_representation": "Shock of uncertain cause"},
                         "state_before": {"observable": {"mental_status": "alert"}},
                         "state_after": {"observable": {"mental_status": "alert"}}}]},
    }, status="completed")
    return attempt_id


@pytest.mark.parametrize("frozen", [True, False])
def test_the_analyses_read_a_generated_encounter_without_declarations(cohort, frozen):
    accounts, _, users = cohort
    attempt_id = _attempt(accounts, users["resident"]["token"], frozen=frozen)
    record = accounts.get_attempt(users["faculty"]["token"], attempt_id)
    case_id = case_id_of(record)
    assert case_id.startswith("AI-")
    import history_review
    import rubric_screening
    screening = rubric_screening.screening(record, case_id)
    assert screening["events"] == []
    assert all(row["window_min"] is None for row in screening["domains"])
    assert history_review.unasked_for_events(record, case_id) == []
    source = build_rubric_source(record)
    assert source["defined_critical_events"] == [] and source["case_opportunities"] == []
    # The model reads no invented declaration; the limitation is the basis's own,
    # which the portal shows the faculty (it is not part of the model's input).
    assert "evaluation_basis" not in source
    basis = evaluation_basis.resolve(record)
    assert basis["status"] == "generated" and "generated case" in basis["limitation"]["en"]


def test_the_rubric_circuit_reads_a_generated_encounter(cohort):
    accounts, _, users = cohort
    attempt_id = _attempt(accounts, users["resident"]["token"])
    record = accounts.get_attempt(users["faculty"]["token"], attempt_id)
    app = page(cohort, attempt_id)
    assert len([s for s in app.selectbox if s.label == "Your score"]) == len(rubric.DOMAIN_IDS)
    assert not [r for r in app.radio if r.label == "Your decision"]
    assert any("generated case" in item.value for item in app.info)

    body = {"domains": [{
        "domain_id": domain, "score": 2, "evidence_refs": ["trace:0"], "opportunity": "observed",
        "learner_evidence": [{"evidence_ref": "trace:0", "minute": 0, "quote": "Give 500 mL normal saline."}],
        "rationale": "One decision is recorded.", "contrary_evidence": "Only one decision.",
        "limits": "Short trace.", "next_level_gap": "No reassessment."} for domain in rubric.DOMAIN_IDS],
        "concerns_for_review": [], "assistance_recorded": [], "record_limits": ["One decision."]}

    class Stub:
        class responses:
            @staticmethod
            def create(**kwargs):
                return SimpleNamespace(status="completed", output_text=json.dumps(body))

    store = RubricStore(accounts)
    report = generate_rubric_proposal(record, api_key="k", model="stub", client=Stub())
    saved = store.save_proposal(users["faculty"]["token"], attempt_id, report)
    assert "event_verdicts" not in saved["proposal"]
    review = store.save_review(users["faculty"]["token"], attempt_id,
                               scores={d: 2 for d in rubric.DOMAIN_IDS}, proposal_id=saved["proposal_id"])
    assert review["critical_events"] == []
    with pytest.raises(AccountError, match="No critical event is defined"):
        store.save_review(users["faculty"]["token"], attempt_id, scores={"D1": 2},
                          events=[{"event_id": "acs_no_antiplatelet", "status": "confirmed",
                                   "justification": "invented"}])
    # The documents are still built from the same record.
    from rubric_report import build_rubric_document
    flow, assessment = build_rubric_document(review, saved, record, language="es")
    assert flow and assessment["totals"]["penalty"] == 0


def test_an_invalid_identifier_is_reported_as_one(cohort):
    from test_rubric_portal import attempt_on_case
    accounts, _, users = cohort
    attempt_id = attempt_on_case(accounts, users["resident"]["token"], case_id="acs_99z_unknown")
    app = page(cohort, attempt_id)
    assert any("invalid identifier" in item.value for item in app.error)
    assert len([s for s in app.selectbox if s.label == "Your score"]) == len(rubric.DOMAIN_IDS)
