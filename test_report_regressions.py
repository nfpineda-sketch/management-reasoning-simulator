"""Regressions for the report defects found between 2026-09-22 and 2026-09-23.

One test per defect, named for what went wrong, so that a future change that
brings it back fails here rather than in a faculty's hands.
"""
import json
from copy import deepcopy
from io import BytesIO

import pytest
from pypdf import PdfReader

import record_findings as findings
import report_presentation as presentation
from management_trace_report import render_management_trace_pdf
from test_report_contract import analysis_for, pages, saved_payload


def rendered(payload=None, analysis=None):
    payload = payload or saved_payload()
    return " ".join(pages(render_management_trace_pdf(analysis or analysis_for(payload), payload)))


# --- an order that was given but never listed --------------------------------

def test_a_study_ordered_here_appears_in_what_you_ordered():
    payload = saved_payload()
    stages = findings.order_stages(payload["trace"])
    requested = stages["trace:0"]["requested"]
    assert {"lactate", "troponin"} <= set(requested), requested
    text = rendered(payload)
    block = text[text.index("3 · WHAT YOU ORDERED"):]
    block = block[:block.index("4 · WHAT YOU EXPECTED")]
    for study in ("Lactate", "Troponin"):
        assert study in block, (study, block[:200])


# --- an order listed twice because its result arrived later ------------------

def test_a_result_arriving_later_is_not_a_second_order():
    payload = saved_payload()
    text = rendered(payload)
    # The lactate is ordered once, at the first decision.
    ordered_blocks = []
    cursor = 0
    while "3 · WHAT YOU ORDERED" in text[cursor:]:
        start = text.index("3 · WHAT YOU ORDERED", cursor)
        end = text.index("4 · WHAT YOU EXPECTED", start)
        ordered_blocks.append(text[start:end])
        cursor = end
    mentions = [block for block in ordered_blocks if "Lactate requested" in block]
    assert len(mentions) == 2, mentions  # the first order and the later control order


# --- a time that belonged to another moment ---------------------------------

def test_request_sample_and_report_keep_their_own_times():
    payload = saved_payload()
    row = next(r for r in findings.order_stages(payload["trace"])["trace:1"]["reported"]
               if r["study"] == "lactate")
    assert row["requested_at_decision"] == 1
    assert row["sampled_at_min"] == 0 and row["reported_at_min"] == 20
    assert "sampled at 0 min, reported at 20 min" in rendered(payload)


# --- absence read as zero ----------------------------------------------------

def test_an_absent_measurement_is_never_reported_as_zero():
    payload = saved_payload()
    assert findings.urine_evidence(payload["trace"])["kind"] != "measured"
    text = rendered(payload)
    assert "no urine volume was recorded" in text
    assert "produced no urine" not in text


# --- a recommendation resting on something the record cannot settle ---------

def test_a_negative_suggestion_on_unsettled_ground_is_held():
    payload = saved_payload()
    limits = findings.encounter_limits(payload["trace"])
    held = findings.hold_for_review(
        {"recommendation": "needs_improvement",
         "rationale": "Work of breathing was not adjusted or escalated."}, limits)
    assert held and findings.HELD_STATUS == "Requires faculty review"


# --- a continuation header on the wrong page --------------------------------

def test_a_continuation_header_only_appears_on_a_page_that_only_continues():
    import re
    payload = saved_payload()
    for page in pages(render_management_trace_pdf(analysis_for(payload), payload)):
        if "CONTINUED" not in page:
            continue
        assert not re.search(r"DECISION \d+ · \d+ min to", page), page[:160]


# --- text cut at the schema limit, presented as finished --------------------

def test_a_cut_passage_never_reaches_the_reading_as_a_finished_sentence():
    payload = saved_payload()
    analysis = analysis_for(payload, truncate=True)
    printed = pages(render_management_trace_pdf(analysis, payload))
    body, technical = printed[:-1], printed[-1]
    assert presentation.TRUNCATION_NOTE.split(":")[0].strip("[… ") not in " ".join(body)
    assert "Technical record" in technical


# --- a page that overflows or empties ---------------------------------------

def test_long_recorded_text_does_not_overflow_or_empty_a_page():
    payload = deepcopy(saved_payload())
    for event in payload["trace"]:
        reasoning = event.get("reasoning")
        if isinstance(reasoning, dict):
            for key in list(reasoning):
                if isinstance(reasoning[key], str) and reasoning[key]:
                    reasoning[key] = (reasoning[key] + " ") * 30
    printed = pages(render_management_trace_pdf(analysis_for(payload), payload))
    assert len(printed) > 7
    for number, page in enumerate(printed, 1):
        assert len(page.replace("MANAGEMENT REASONING SIMULATOR", "")) > 300, number
