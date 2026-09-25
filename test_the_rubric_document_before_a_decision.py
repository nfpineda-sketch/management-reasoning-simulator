"""The rubric document can be printed from the AI proposal, before any decision.

The batch of 2026-09-24 must leave every evaluation pending the faculty's
review and still have its four documents. The rubric document used to exist
only once a review was saved, and saving a draft just to print it would start
the reviewer at the AI's values instead of at "not assessable" (faculty
decision, 2026-09-23). The proposal now prints on its own, in the approved
layout, saying on its face that nobody has decided anything; a resident never
receives it.
"""
import pytest

from rubric_report import RubricReportError, build_rubric_document, render_rubric_report_pdf
from test_rubric_reports import text_of
from test_the_record_settles_what_it_can import proposal_1_1
from tools_rubric_runs import BY_ID, play_orders


@pytest.fixture(scope="module")
def record():
    played, _ = play_orders(BY_ID["asthma_24f"])
    return played


@pytest.fixture(scope="module")
def proposal(record):
    return proposal_1_1(record, scores={"D1": 3, "D4": 1})


@pytest.mark.parametrize("language, words", [
    ("en", ["No faculty decision yet", "AI proposal", "Provisional"]),
    ("es", ["Sin decisión docente", "propuesta IA", "Provisional"]),
])
def test_the_proposal_prints_and_says_nobody_has_decided(record, proposal, language, words):
    import rubric_presentation
    text = text_of(render_rubric_report_pdf(None, proposal, record, language=language))
    for word in words + [rubric_presentation.score_label(3, language)]:
        assert word in text, (word, text[:800])
    assert "out of 15" not in text and "de 15" not in text


def test_its_shape_is_the_proposal_s_and_is_labelled_as_one(record, proposal):
    _, assessment = build_rubric_document(None, proposal, record)
    assert assessment["status"]["state"] == "proposed"
    assert {row["domain_id"]: row["proposed"] for row in assessment["profile"]}["D1"] == 3
    assert not any(row["decided"] for row in assessment["profile"])


def test_a_resident_never_receives_a_proposal(record, proposal):
    with pytest.raises(RubricReportError):
        render_rubric_report_pdf(None, proposal, record, audience="learner")


def test_nothing_to_print_without_a_proposal_or_a_review(record):
    with pytest.raises(RubricReportError):
        render_rubric_report_pdf(None, None, record)
