"""The screen and the two documents read one assessment, so they cannot disagree."""
import re

import pytest
from pypdf import PdfReader
from io import BytesIO

import rubric
import rubric_presentation as present
from faculty_report import render_faculty_brief_pdf
from test_faculty_report import brief_example  # reuse the synthetic fixture


@pytest.fixture
def pair():
    report, record = brief_example()
    return record, report


def review(scores=None, events=(), status="confirmed", changes=None, reasons=None):
    scores = scores or {d: 2 for d in rubric.DOMAIN_IDS}
    return {
        "rubric_version": rubric.VERSION, "status": status, "case_id": "acs_48m_wellens",
        "scores": scores, "reasons": reasons or {}, "changes": changes or {},
        "critical_events": list(events),
        "totals": rubric.score(scores, events), "reviewer": "faculty", "sequence": 1,
    }


def text_of(blob):
    return " ".join(" ".join(page.extract_text() or "" for page in PdfReader(BytesIO(blob)).pages).split())


def both(record, brief, assessment):
    return (text_of(render_faculty_brief_pdf(brief, record, compact=True, assessment=assessment)),
            text_of(render_faculty_brief_pdf(brief, record, compact=False, assessment=assessment)))


def test_both_briefs_show_the_same_ratings_and_the_same_total(pair):
    assessment = present.summary(review())
    compact, full = both(*pair, assessment)
    for body in (compact, full):
        assert "Base 10/15" in body
        assert "Confirmed by faculty" in body
        # Spelled out, so a rubric domain cannot be read as a decision reference.
        for domain in rubric.DOMAIN_IDS:
            assert f"Domain {domain[1:]}" in body
        assert "2/3" in body


def test_a_confirmed_event_shows_its_penalty_in_both_and_stays_visible_at_the_top_score(pair):
    top = {d: 3 for d in rubric.DOMAIN_IDS}
    events = [{"event_id": "acs_no_antiplatelet", "status": "confirmed",
               "kind": "critical_omission", "action": "No antiplatelet is given.",
               "proposed_by_ai": True, "justification": ""}]
    assessment = present.summary(review(top, events))
    compact, full = both(*pair, assessment)
    for body in (compact, full):
        assert "Base 15/15" in body and "Adjusted 12/15" in body
        assert "acs_no_antiplatelet" in body
        assert "CRITICAL EVENTS CONFIRMED" in body
        # The double weight is stated rather than hidden.
        assert "deliberate" in body


def test_a_partial_assessment_shows_no_comparable_total_in_either_document(pair):
    scores = {d: 2 for d in rubric.DOMAIN_IDS}
    scores["D4"] = rubric.NOT_ASSESSABLE
    assessment = present.summary(review(scores, reasons={
        "D4": "The encounter closed before a response could be observed."}))
    compact, full = both(*pair, assessment)
    for body in (compact, full):
        assert "4 of 5 domains assessable" in body
        assert "no comparable total" in body
        assert "Base " not in body
        assert "Not assessable" in body


def test_a_changed_score_carries_its_justification_into_the_documents(pair):
    assessment = present.summary(review(
        {**{d: 2 for d in rubric.DOMAIN_IDS}, "D3": 0},
        changes={"D3": {"proposed": 2, "confirmed": 0,
                        "justification": "The antiplatelet was never executed."}}))
    compact, full = both(*pair, assessment)
    for body in (compact, full):
        assert "Changed from the proposed 2" in body
        assert "The antiplatelet was never executed" in body


def test_without_an_assessment_the_briefs_are_unchanged(pair):
    with_none = text_of(render_faculty_brief_pdf(pair[1], pair[0], compact=True))
    explicit = text_of(render_faculty_brief_pdf(pair[1], pair[0], compact=True, assessment=None))
    assert with_none == explicit
    assert "MANAGEMENT REASONING RUBRIC" not in with_none


def test_the_pilot_notice_travels_with_every_score(pair):
    assessment = present.summary(review())
    compact, full = both(*pair, assessment)
    for body in (compact, full):
        assert "Pilot rubric" in body
        assert "ACGME" in body            # says what it is not


def test_the_full_brief_carries_the_traceability_the_compact_does_not_need(pair):
    assessment = present.summary(review())
    compact, full = both(*pair, assessment)
    assert "Rubric version: 1.0-pilot" in full
    assert "Reviewed by: faculty" in full
    assert "Rubric version:" not in compact


def test_an_unresolved_proposal_is_shown_as_awaiting_and_costs_nothing(pair):
    proposal = {"rubric_version": rubric.VERSION, "model": "m", "prompt_version": "1.0",
                "generated_at": "2026-09-23T00:00:00+00:00", "coverage_version": "1.0",
                "case_id": "acs_48m_wellens",
                "proposal": {"domains": [], "critical_events": [
                    {"event_id": "acs_provocation_test", "evidence_refs": [],
                     "trigger_evidence": "A stress test was ordered.", "exclusions_checked": ""}],
                    "concerns_for_review": []}}
    assessment = present.summary(review(), proposal)
    compact, full = both(*pair, assessment)
    for body in (compact, full):
        assert "AWAITING YOUR DECISION" in body
        assert "acs_provocation_test" in body
        assert "carries no penalty until you decide" in body
    # And it does not reach the arithmetic.
    assert present.summary(review(), proposal)["totals"]["penalty"] == 0
