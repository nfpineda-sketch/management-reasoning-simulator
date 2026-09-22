"""The three documents of one encounter must agree with each other.

Faculty request 2026-09-23: the same visible identifier in all three, and the
compact and the full faculty brief carrying the same judgments, so that reading
one is never contradicted by reading another.
"""
from copy import deepcopy
from io import BytesIO

import pytest
from pypdf import PdfReader

import report_presentation as presentation
from faculty_report import (RECOMMENDATIONS, _COMPACT_RECOMMENDATIONS,
                            _encounter_identifier, render_faculty_brief_pdf)
from management_trace_report import render_management_trace_pdf
from test_faculty_report import brief_example
from test_management_trace_report import report_example


def text_of(data):
    return " ".join("\n".join(page.extract_text() for page in PdfReader(BytesIO(data)).pages).split())


def faculty_pair():
    report, record = brief_example()
    record.setdefault("payload", {}).setdefault("session", {})["state"] = {"case_id": "CE-shared-identifier"}
    return report, record


def test_the_faculty_documents_show_the_same_identifier():
    report, record = faculty_pair()
    identifier = _encounter_identifier(record)
    assert identifier == "CE-shared-identifier · " + record["challenge_id"]
    for compact in (True, False):
        assert identifier in text_of(render_faculty_brief_pdf(report, record, compact=compact))


def test_the_learner_report_shows_the_same_identifier():
    report, payload = report_example()
    # The analysis source deliberately drops identity fields, so the identifier
    # is read from the frozen payload and adding it cannot change the hash.
    payload["trace"][0]["state_before"]["case_id"] = "CE-shared-identifier"
    text = text_of(render_management_trace_pdf(report, payload, case_label="R1-04"))
    assert presentation.identifier("CE-shared-identifier", "R1-04") in text


def test_the_two_faculty_documents_carry_the_same_judgments():
    """The wording differs between the two; the judgment must not."""
    report, record = faculty_pair()
    report["analysis"]["objectives"][1]["recommendation"] = "needs_improvement"
    compact = text_of(render_faculty_brief_pdf(report, record))
    full = text_of(render_faculty_brief_pdf(report, record, compact=False))
    for item in report["analysis"]["objectives"]:
        assert item["objective_id"] in compact and item["objective_id"] in full
    for recommendation in {item["recommendation"] for item in report["analysis"]["objectives"]}:
        anchored = [item for item in report["analysis"]["objectives"]
                    if item["recommendation"] == recommendation and item["evidence_refs"]]
        if not anchored:
            continue
        assert _COMPACT_RECOMMENDATIONS[recommendation] in compact, recommendation
        assert RECOMMENDATIONS[recommendation] in full, recommendation


def test_an_objective_with_no_recorded_opportunity_says_so_in_both():
    report, record = faculty_pair()
    target = report["analysis"]["objectives"][0]
    target["recommendation"] = "insufficient_evidence"
    target["evidence_refs"] = []
    compact = text_of(render_faculty_brief_pdf(report, record))
    full = text_of(render_faculty_brief_pdf(report, record, compact=False))
    assert "Not assessed in this encounter" in compact
    assert "Not assessed in this encounter" in full


def test_an_objective_judged_on_evidence_is_not_relabelled():
    """Insufficient evidence with an anchor is a weak demonstration, not an absent one."""
    report, record = faculty_pair()
    target = report["analysis"]["objectives"][0]
    target["recommendation"] = "insufficient_evidence"
    assert target["evidence_refs"], "this objective cites evidence"
    compact = text_of(render_faculty_brief_pdf(report, record))
    assert _COMPACT_RECOMMENDATIONS["insufficient_evidence"] in compact
    full = text_of(render_faculty_brief_pdf(report, record, compact=False))
    assert RECOMMENDATIONS["insufficient_evidence"] in full


def test_the_learner_report_shows_no_machine_reference_in_its_reading_text():
    report, payload = report_example()
    text = text_of(render_management_trace_pdf(report, payload))
    assert "trace:" not in text and "reflection:decision" not in text and "encounter:" not in text
    assert "Based on:" in text


# --- pagination: nothing empty, nothing stranded ----------------------------

def pages(data):
    return [" ".join(page.extract_text().split()) for page in PdfReader(BytesIO(data)).pages]


def test_no_page_of_any_document_is_empty():
    report, record = faculty_pair()
    learner, payload = report_example()
    documents = {
        "compact": render_faculty_brief_pdf(report, record),
        "full": render_faculty_brief_pdf(report, record, compact=False),
        "learner": render_management_trace_pdf(learner, payload),
    }
    for name, data in documents.items():
        for number, page in enumerate(pages(data), 1):
            # A page carrying only the running header and footer is empty.
            body = page.replace("MANAGEMENT REASONING SIMULATOR", "")
            assert len(body) > 350, (name, number, len(body))


def test_the_compact_brief_is_two_pages_with_its_rationales_intact():
    report, record = faculty_pair()
    printed = pages(render_faculty_brief_pdf(report, record))
    assert len(printed) == 2
    assert "Review the full rationale in the app" not in " ".join(printed)


def test_a_decision_that_spans_two_pages_says_it_continues():
    report, payload = report_example()
    printed = pages(render_management_trace_pdf(report, payload))
    for number, page in enumerate(printed):
        if "CONTINUED" not in page:
            continue
        # A continuation names its decision and is never the first page.
        assert number > 0
        assert "DECISION" in page.split("CONTINUED")[0][-40:]


def test_the_continuation_marker_is_absent_where_nothing_continues():
    report, payload = report_example()
    printed = pages(render_management_trace_pdf(report, payload))
    assert "CONTINUED" not in printed[0]


# --- the same correction reaches every document that shows the text ---------

def test_a_correction_applies_in_both_faculty_documents():
    report, record = faculty_pair()
    # An objective that keeps its full row in the concise brief: the ones
    # suggested satisfactory are shown there as one line, by design.
    target = next(item for item in report["analysis"]["objectives"]
                  if item["recommendation"] != "satisfactory")
    original = target["rationale"]
    correction = [{"original": original, "replacement": "A corrected rationale sentence.",
                   "reason": "checked against the record"}]
    for compact in (True, False):
        text = text_of(render_faculty_brief_pdf(report, record, compact=compact, corrections=correction))
        assert "A corrected rationale sentence." in text
        assert "factual correction" in text
    # The stored brief is untouched.
    assert target["rationale"] == original


# --- the concise brief directs attention without losing an objective --------

def test_every_objective_reaches_the_concise_brief():
    report, record = faculty_pair()
    text = text_of(render_faculty_brief_pdf(report, record))
    for item in report["analysis"]["objectives"]:
        assert item["objective_id"] in text, item["objective_id"]


def test_what_needs_a_decision_keeps_its_rationale_in_the_concise_brief():
    report, record = faculty_pair()
    target = next(item for item in report["analysis"]["objectives"]
                  if item["recommendation"] != "satisfactory")
    first_sentence = target["rationale"].split(".")[0]
    assert first_sentence in text_of(render_faculty_brief_pdf(report, record))


def test_a_settled_satisfactory_objective_is_one_line_with_its_evidence():
    report, record = faculty_pair()
    settled = next(item for item in report["analysis"]["objectives"]
                   if item["recommendation"] == "satisfactory")
    compact = text_of(render_faculty_brief_pdf(report, record))
    full = text_of(render_faculty_brief_pdf(report, record, compact=False))
    assert "Suggested satisfactory, and settled by the record" in compact
    # Its judgment and evidence are shown; its rationale is read in the full PDF.
    assert settled["objective_id"] in compact
    assert settled["rationale"].split(".")[0] not in compact
    assert settled["rationale"].split(".")[0] in full


def test_a_held_suggestion_never_becomes_a_one_line_entry():
    report, record = faculty_pair()
    target = report["analysis"]["objectives"][0]
    target["recommendation"] = "needs_improvement"
    target["rationale"] = "Support began 15 minutes later than it could have."
    # The first decision's interval is what the record cannot separate from it.
    first = record["payload"]["session"]["management_trace"][0]
    first["decision_time_min"], first["response_time_min"] = 0, 15
    compact = text_of(render_faculty_brief_pdf(report, record))
    assert "Requires faculty review" in compact
    assert target["rationale"].split(".")[0] in compact
