"""Internal identifiers in a model's prose, written back as what they point to.

Faculty review of 2026-09-24, over the 45 documents of a batch: ``trace:0`` and
``trace:4`` inside sentences of documents that call the same decisions
"D1 · 00:04", and ``unasked_history_topics`` -- the name of an input field --
in three of them. One conversion, from the encounter's own map, in every
renderer; the stored analysis, the raw response and the resident's own words
are never changed.
"""
import logging
from copy import deepcopy
from io import BytesIO

import pytest
from pypdf import PdfReader

import report_presentation as presentation


def _trace():
    """A question first, then a held order, then decisions: the stored position
    and the decision number part company, which is the whole point."""
    trace = [
        {"execution_status": "information", "decision_time_min": 0},
        {"execution_status": "executed", "decision_time_min": 4},
        {"execution_status": "clarification_required", "decision_time_min": 6},
        {"execution_status": "executed", "decision_time_min": 10},
    ]
    trace += [{"execution_status": "executed", "decision_time_min": 12 + i} for i in range(9)]
    return trace


LABELS = presentation.reference_labels(_trace())


def test_a_decision_is_its_place_among_decisions_not_its_position_plus_one():
    assert LABELS["trace:1"]["en"] == "D1 · 00:04"
    assert LABELS["trace:3"]["en"] == "D2 · 00:10"
    assert LABELS["trace:0"]["es"] == "información obtenida · 00:00"
    assert LABELS["trace:2"]["es"] == "orden no ejecutada · 00:06"


def test_valid_references_are_resolved_and_repeated_ones_consistently():
    text = "The oxygen (trace:1) and the fluid at trace:3; trace:1 again."
    assert presentation.humanize(text, LABELS) == (
        "The oxygen (D1 · 00:04) and the fluid at D2 · 00:10; D1 · 00:04 again.")


def test_several_digits_are_whole_tokens():
    """trace:1 must never be read inside trace:10 or trace:12."""
    text = "trace:1, trace:10 and trace:12, not retrace:1 or trace:1x."
    result = presentation.humanize(text, LABELS)
    assert result.startswith("D1 · 00:04, D9 · 00:18 and D11 · 00:20")
    assert "retrace:1" in result and "trace:1x" in result


def test_a_reference_that_cannot_be_resolved_is_said_and_logged_never_guessed(caplog):
    unresolved = []
    with caplog.at_level(logging.WARNING, logger="mrs.references"):
        result = presentation.humanize("Based on trace:99 and encounter:4.", LABELS, "es", unresolved)
    assert result == "Based on referencia no disponible and referencia no disponible."
    assert unresolved == ["trace:99", "encounter:4"]
    assert "trace:99" in caplog.text


def test_a_reflection_is_named_by_the_decisions_it_discusses():
    assert presentation.humanize("See reflection:decision-2 and reflection:decisions-2-3.", {}) == (
        "See later reflection on D2 and later reflection on D2-D3.")


def test_field_names_become_what_they_mean_and_no_more():
    en = presentation.humanize("It lists `unasked_history_topics` and decision_events.", {})
    assert en == "It lists history topics not explored and the recorded decisions."
    es = presentation.humanize("Revisar unasked_history_topics.", {}, "es")
    assert es == "Revisar antecedentes no explorados."
    # "Not explored" is what the field means. It is not rewritten as an omission.
    assert "omission" not in en and "omisión" not in es


def test_a_correction_runs_before_the_rewrite_and_both_are_reported():
    log = presentation.CorrectionLog(
        [{"original": "at trace:1 the rate was 40", "replacement": "at trace:1 the rate was 140",
          "reason": "transcription"}], references=LABELS)
    assert log("Noted at trace:1 the rate was 40.") == "Noted at D1 · 00:04 the rate was 140."
    assert log.lines() == ["transcription"]


# --- in the documents ---------------------------------------------------------
def _brief_with_identifiers():
    from test_faculty_report import brief_example
    report, record = brief_example()
    session = record["payload"]["session"]
    # An information entry first, so position and decision number differ.
    session["management_trace"].insert(0, {
        "execution_status": "information", "decision_time_min": 40, "response_time_min": 41,
        "learner_input": "Pregunto por medicamentos", "interpreted_action": [],
        "state_before": deepcopy(session["management_trace"][0]["state_before"]),
        "state_after": deepcopy(session["management_trace"][0]["state_before"])})
    # Every citation moves with the decision it cites.
    def shift(refs):
        return [f"trace:{int(ref.split(':')[1]) + 1}" if ref.startswith("trace:") else ref
                for ref in refs]
    for row in report["analysis"]["key_decisions"] + report["analysis"]["objectives"]:
        row["evidence_refs"] = shift(row["evidence_refs"])
    for key in ("summary", "learning_cycle"):
        report["analysis"][key] = ("At trace:1 the resident did not ask about "
                                   "unasked_history_topics; see trace:7.")
    return report, record


def test_the_briefs_print_decisions_not_identifiers_and_store_nothing_new():
    from faculty_report import render_faculty_brief_pdf
    report, record = _brief_with_identifiers()
    before = deepcopy(report)
    for compact in (False, True):
        pdf = render_faculty_brief_pdf(report, record, compact=compact)
        text = " ".join(" ".join(page.extract_text() for page in PdfReader(BytesIO(pdf)).pages).split())
        assert "trace:" not in text and "unasked_history_topics" not in text
        if not compact:
            assert "At D1 · 00:46 the resident did not ask about history topics not explored" in text
            assert "reference unavailable" in text
    assert report == before


def test_the_compact_brief_numbers_the_decision_it_cites():
    """It used to print the stored position plus one: D2 for the first decision."""
    from faculty_report import _compact_references, _evidence_index
    _, record = _brief_with_identifiers()
    index = _evidence_index(record)
    assert _compact_references(["trace:1"], index) == "D1 00:46"


def test_the_rubric_prose_is_resolved_and_the_quotes_are_not():
    import rubric
    import rubric_presentation
    from tools_rubric_runs import play
    record, _ = play("hypoglycemia_76f")
    proposal = {"prompt_version": "1.0", "proposal": {
        "domains": [{"domain_id": d, "score": 2, "evidence_refs": ["trace:3"],
                     "learner_evidence": [{"evidence_ref": "trace:3", "minute": 13,
                                           "quote": "La envio a su casa (trace:3 literal)"}],
                     "rationale": "An executed discharge disposition was recorded (trace:3 "
                                  "decision at minute 13).",
                     "contrary_evidence": "unasked_history_topics include medications.",
                     "limits": "None."} for d in rubric.DOMAIN_IDS],
        "critical_events": [], "concerns_for_review": [], "assistance_recorded": [],
        "record_limits": []}}
    summary = rubric_presentation.summary(None, proposal, record=record)
    row = summary["profile"][0]
    assert "trace:" not in row["rationale"] and "D4 · 00:13" in row["rationale"]
    assert row["contrary_evidence"] == "history topics not explored include medications."
    # What the resident wrote is quoted as written.
    assert row["quotes"][0]["quote"] == "La envio a su casa (trace:3 literal)"
    # And nothing stored changed.
    assert "trace:3" in proposal["proposal"]["domains"][0]["rationale"]


def test_the_learner_trace_keeps_resolving_older_carried_decisions():
    """Records saved before 2026-09-24 wrote a carried interpretation's position plus one."""
    trace = [{"execution_status": "information"}, {"execution_status": "executed"},
             {"execution_status": "executed"}]
    assert presentation.carried_decision({"decision": 2, "minute": 4}, trace) == 1
    assert presentation.carried_decision({"decision": 1, "trace_index": 1}, trace) == 1
    assert presentation.carried_decision({"decision": 7}, trace) is None
