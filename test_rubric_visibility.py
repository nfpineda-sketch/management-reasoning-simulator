"""The learner's document carries no rubric score, and nothing leaks into it.

The rubric is faculty decision support, like the faculty brief beside it. The
existing visibility rule is that a faculty judgement reaches a resident only
through what the faculty records for them, never through the learner's own
Management Trace -- which is written and downloaded before any review exists.

So the Management Trace keeps its narrative and temporal function and says
nothing about a score. This is a decision, not an omission: it is written here
so that adding a score later is a deliberate change with a test to update.
"""
from io import BytesIO

import pytest
from pypdf import PdfReader

import rubric
import rubric_presentation as present
from management_trace_report import render_management_trace_pdf
from test_management_trace_report import report_example


@pytest.fixture
def learner_document():
    report, payload = report_example()
    return render_management_trace_pdf(report, payload, case_label="Synthetic encounter",
                                       learner_label="Learner example"), payload


def text_of(blob):
    return " ".join(" ".join(page.extract_text() or "" for page in
                             PdfReader(BytesIO(blob)).pages).split())


def test_the_learner_document_says_nothing_about_a_rubric_score(learner_document):
    body = text_of(learner_document[0])
    for forbidden in ("MANAGEMENT REASONING RUBRIC", "Pilot rubric", "Adjusted ",
                      "critical event", "Not assessable"):
        assert forbidden not in body, forbidden
    # "D1 · 0 min" in this document is a decision, not a rubric domain: the
    # documents spell a domain out precisely so the two cannot be confused.
    for domain in rubric.DOMAIN_IDS:
        assert f"Domain {domain[1:]}" not in body


def test_the_renderer_takes_no_assessment_argument():
    """It cannot be passed one by accident from a shared call site."""
    import inspect
    assert "assessment" not in inspect.signature(render_management_trace_pdf).parameters


def test_a_summary_built_for_the_faculty_never_reaches_the_learner_payload(learner_document):
    """The assessment lives outside the learner's record entirely."""
    import json
    assessment = present.summary({
        "rubric_version": rubric.VERSION, "status": "confirmed", "case_id": "acs_48m_wellens",
        "scores": {d: 3 for d in rubric.DOMAIN_IDS}, "reasons": {}, "changes": {},
        "critical_events": [], "totals": rubric.score({d: 3 for d in rubric.DOMAIN_IDS}),
    })
    body = json.dumps(learner_document[1], default=str)
    assert "rubric" not in body.lower()
    assert assessment["headline"]           # it exists, it just does not live there
