"""The fourth document: the score, large, and who is allowed to read it.

Three properties it has to keep, and all three are about restraint rather than
about layout: it releases nothing to a resident that a faculty member has not
completed, it computes no number of its own, and a domain that could not be
observed stays visibly unobserved.
"""
from io import BytesIO

import pytest
from pypdf import PdfReader

import rubric
import rubric_radar
from rubric_report import (FACULTY_ONLY, PROVISIONAL, RubricReportError,
                           build_rubric_document, render_rubric_report_pdf)
from test_rubric_reports import review


RECORD = {"id": "attempt-000000000001", "revision": 3, "updated_at": 1790000000}


def proposal(scores=None, events=(), quotes=True):
    scores = scores or {domain: 2 for domain in rubric.DOMAIN_IDS}
    return {
        "rubric_version": rubric.VERSION, "prompt_version": "1.0", "model": "test-model",
        "coverage_version": "1.0", "case_id": "acs_48m_wellens", "proposal_id": "p1",
        "generated_at": "2026-09-23T00:00:00+00:00",
        "proposal": {
            "domains": [{
                "domain_id": domain, "score": scores[domain], "evidence_refs": ["trace:0"],
                "rationale": f"Why {domain} is what it is.",
                "contrary_evidence": f"Against {domain}.", "limits": f"Limits of {domain}.",
                "learner_evidence": ([{"evidence_ref": "trace:0", "minute": 15,
                                       "quote": f"the learner's own words for {domain}"}]
                                     if quotes else []),
            } for domain in rubric.DOMAIN_IDS],
            "critical_events": [{"event_id": e, "evidence_refs": ["trace:0"],
                                 "trigger_evidence": f"why {e} fired",
                                 "exclusions_checked": "checked"} for e in events],
            "concerns_for_review": [{"concern": "Something nobody defined.",
                                     "evidence_refs": ["trace:0"]}],
            "assistance_recorded": [], "record_limits": [],
        },
    }


def text_of(blob):
    return " ".join(" ".join(page.extract_text() or ""
                             for page in PdfReader(BytesIO(blob)).pages).split())


def page_text(**kwargs):
    return text_of(render_rubric_report_pdf(**kwargs))


# --- who may read it ------------------------------------------------------

def test_a_draft_is_not_released_to_the_resident():
    with pytest.raises(RubricReportError) as error:
        render_rubric_report_pdf(review(status="draft"), proposal(), RECORD, audience="learner")
    assert "completed by a faculty member" in str(error.value)


def test_an_encounter_nobody_assessed_produces_no_document_at_all():
    with pytest.raises(RubricReportError):
        render_rubric_report_pdf(None, proposal(), RECORD)


def test_a_confirmed_assessment_is_released_to_the_resident():
    blob = render_rubric_report_pdf(review(), proposal(), RECORD, audience="learner")
    assert PdfReader(BytesIO(blob)).pages


def test_the_faculty_copy_says_it_is_the_faculty_copy():
    words = page_text(review=review(status="draft"), proposal=proposal(), record=RECORD)
    assert FACULTY_ONLY.split(".")[0] in words
    assert PROVISIONAL.split(".")[0] in words


def test_the_resident_copy_carries_no_faculty_only_banner():
    words = page_text(review=review(), proposal=proposal(), record=RECORD, audience="learner")
    assert FACULTY_ONLY.split(".")[0] not in words


def test_a_confirmed_faculty_copy_is_not_labelled_provisional():
    words = page_text(review=review(), proposal=proposal(), record=RECORD)
    assert PROVISIONAL.split(".")[0] not in words


@pytest.mark.parametrize("audience", ["resident", "", None, "admin"])
def test_only_the_two_audiences_the_rule_names_are_accepted(audience):
    with pytest.raises(RubricReportError):
        render_rubric_report_pdf(review(), proposal(), RECORD, audience=audience)


# --- what the number is ---------------------------------------------------

def test_the_adjusted_total_is_the_number_set_large():
    events = [{"event_id": "acs_no_antiplatelet", "status": "confirmed", "justification": "x"}]
    decided = review(events=events)
    words = page_text(review=decided, proposal=proposal(), record=RECORD)
    assert decided["totals"]["adjusted"] == 7
    assert "7 out of 15" in words
    # The base and the penalty stay beside it: a total with a silent deduction
    # inside it is a different number from the one the domains add up to.
    assert "Base 10/15" in words and "penalty -3" in words


def _styles_used(value, found=None):
    """Every paragraph style in a flowable tree, however deeply it is nested."""
    found = set() if found is None else found
    if isinstance(value, (list, tuple)):
        for item in value:
            _styles_used(item, found)
        return found
    found.add(getattr(getattr(value, "style", None), "name", ""))
    for attribute in ("_content", "_cellvalues"):
        if hasattr(value, attribute):
            _styles_used(getattr(value, attribute), found)
    return found


def test_a_partial_assessment_shows_a_sentence_where_a_number_would_be():
    scores = {domain: 2 for domain in rubric.DOMAIN_IDS}
    scores["D5"] = rubric.NOT_ASSESSABLE
    words = page_text(review=review(scores), proposal=proposal(), record=RECORD)
    assert "4 of 5 domains assessable" in words
    assert "not comparable with a complete episode" in words
    # The sentence explains that there is no score out of 15; what must not
    # exist is a number set in the style reserved for one.
    partial, _ = build_rubric_document(review(scores), proposal(), RECORD)
    complete, _ = build_rubric_document(review(), proposal(), RECORD)
    assert "RubricScore" in _styles_used(complete)
    assert "RubricScore" not in _styles_used(partial)
    assert "RubricPartial" in _styles_used(partial)


def test_the_document_computes_nothing_of_its_own():
    decided = review()
    decided["totals"] = {**decided["totals"], "adjusted": 999}
    words = page_text(review=decided, proposal=proposal(), record=RECORD)
    # It prints the totals it was given. The arithmetic belongs to ``rubric``
    # and is checked where it is done, not repeated here.
    assert "999" in words


def test_every_domain_appears_with_its_score():
    words = page_text(review=review({"D1": 3, "D2": 2, "D3": 0, "D4": 1,
                                     "D5": rubric.NOT_ASSESSABLE}),
                      proposal=proposal(), record=RECORD)
    for number in range(1, 6):
        assert f"Domain {number}" in words
    assert "3/3" in words and "0/3" in words
    assert "Not assessable" in words


def test_a_rubric_domain_is_never_printed_as_a_decision_label():
    # "D3" is a decision elsewhere in these documents, so a rubric domain is
    # spelled out. The model's own prose may say anything; what this fixes is
    # the label the document itself writes in the first column.
    flow, _ = build_rubric_document(review(), proposal(), RECORD)
    table = [item for item in flow if hasattr(item, "_cellvalues")][-1]
    labels = [row[0][0].getPlainText() for row in table._cellvalues[1:]]
    assert labels == [f"Domain {number}" for number in range(1, 6)]


# --- the evidence ---------------------------------------------------------

def test_the_learners_own_words_travel_with_the_score():
    words = page_text(review=review(), proposal=proposal(), record=RECORD)
    for domain in rubric.DOMAIN_IDS:
        assert f"the learner's own words for {domain}" in words
    assert "00:15" in words


def test_the_reasoning_and_what_argues_against_it_both_appear():
    words = page_text(review=review(), proposal=proposal(), record=RECORD)
    assert "Why D1 is what it is." in words
    assert "Against: Against D1." in words
    assert "Limits: Limits of D1." in words


def test_a_score_the_faculty_changed_carries_why_they_changed_it():
    changed = review({**{d: 2 for d in rubric.DOMAIN_IDS}, "D2": 1},
                     changes={"D2": {"proposed": 2, "confirmed": 1,
                                     "justification": "The record does not support a 2."}})
    words = page_text(review=changed, proposal=proposal(), record=RECORD)
    assert "Changed from the proposed 2/3" in words
    assert "The record does not support a 2." in words


def test_a_not_assessable_domain_gives_its_reason_rather_than_a_score():
    scores = {**{d: 2 for d in rubric.DOMAIN_IDS}, "D5": rubric.NOT_ASSESSABLE}
    decided = review(scores, reasons={"D5": "The encounter closed before a disposition."})
    words = page_text(review=decided, proposal=proposal(), record=RECORD)
    assert "The encounter closed before a disposition." in words


def test_the_evidence_survives_a_document_with_no_proposal_beside_it():
    words = page_text(review=review(), proposal=None, record=RECORD)
    assert "Domain 1" in words and "2/3" in words


# --- the events -----------------------------------------------------------

def test_a_confirmed_event_names_itself_and_its_double_weight():
    events = [{"event_id": "acs_no_antiplatelet", "status": "confirmed",
               "justification": "No antiplatelet reached the patient."}]
    words = page_text(review=review(events=events), proposal=proposal(), record=RECORD)
    assert "acs_no_antiplatelet" in words
    assert "No antiplatelet reached the patient." in words
    assert "double weight is deliberate" in words


def test_an_event_the_model_proposed_and_nobody_decided_costs_nothing_yet():
    words = page_text(review=review(), proposal=proposal(events=["acs_provocation_test"]),
                      record=RECORD)
    assert "AWAITING YOUR DECISION" in words
    assert "carries no penalty until you decide" in words
    assert "why acs_provocation_test fired" in words


def test_a_concern_nobody_defined_is_flagged_without_a_deduction():
    words = page_text(review=review(), proposal=proposal(), record=RECORD)
    assert "carrying no deduction: Something nobody defined." in words


# --- the shape ------------------------------------------------------------

def test_the_chart_draws_the_scores_the_page_prints():
    scores = {"D1": 3, "D2": 2, "D3": 0, "D4": 1, "D5": rubric.NOT_ASSESSABLE}
    flow, assessment = build_rubric_document(review(scores), proposal(), RECORD)
    drawn = rubric_radar.geometry([{
        "values": {row["domain_id"]: row["score"] for row in assessment["profile"]
                   if row["decided"]}}])["series"][0]
    assert drawn["values"]["D1"] == 3.0 and drawn["values"]["D3"] == 0.0
    assert drawn["gaps"] == ["D5"]


def test_a_second_outline_appears_only_when_an_average_is_given():
    alone, _ = build_rubric_document(review(), proposal(), RECORD)
    with_average, _ = build_rubric_document(
        review(), proposal(), RECORD,
        average={"label": "Average", "values": {d: 2 for d in rubric.DOMAIN_IDS},
                 "caption": "Across six encounters."})
    assert len(with_average) > len(alone)
    assert "Across six encounters." in text_of(render_rubric_report_pdf(
        review(), proposal(), RECORD,
        average={"label": "Average", "values": {d: 2 for d in rubric.DOMAIN_IDS},
                 "caption": "Across six encounters."}))


# --- the rest -------------------------------------------------------------

def test_the_pilot_notice_travels_with_the_score():
    words = page_text(review=review(), proposal=proposal(), record=RECORD)
    assert "not ACGME Milestone levels" in words


def test_the_traceability_says_where_every_number_came_from():
    words = page_text(review=review(), proposal=proposal(), record=RECORD)
    for expected in ("Rubric version: 1.0-pilot", "Proposal model: test-model",
                     "Authored case: acs_48m_wellens", "Encounter revision: 3"):
        assert expected in words


def test_the_spanish_document_is_spanish_throughout():
    words = page_text(review=review(), proposal=proposal(), record=RECORD, language="es")
    assert "Dominio 1" in words and "Domain 1" not in words
    assert "de 15" in words
    assert "Documento docente" in words
    assert "Reconocimiento de gravedad" in words


def test_the_spanish_partial_assessment_says_so_in_spanish():
    scores = {**{d: 2 for d in rubric.DOMAIN_IDS}, "D5": rubric.NOT_ASSESSABLE}
    words = page_text(review=review(scores), proposal=proposal(), record=RECORD, language="es")
    assert "4 de 5 dominios evaluables" in words
    assert "No evaluable" in words


def test_the_spanish_document_says_the_model_wrote_in_english():
    # The proposal is generated in English by contract. A Spanish page that
    # printed English prose without saying so would look like a bug.
    words = page_text(review=review(), proposal=proposal(), record=RECORD, language="es")
    assert "se genera en inglés" in words
    assert "se genera en inglés" not in page_text(
        review=review(), proposal=proposal(), record=RECORD)
