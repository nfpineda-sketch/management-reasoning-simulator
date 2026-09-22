"""The approved structure, applied to encounters other than the demonstration.

Closing check of 2026-09-23. The three documents must come out of the shared
templates for any encounter, bank or AI-authored, without a manual correction,
an identifier or a phrase belonging to one case. What varies with the encounter
is the content, the charts, the decisions, the assessable objectives and the
pagination; what does not vary is the structure.

The analyses here are authored fixtures built from each payload's own evidence
references, so no provider is called.
"""
import json
import os
from copy import deepcopy
from io import BytesIO
from pathlib import Path

import pytest
from pypdf import PdfReader

import record_findings as findings
import report_corrections
import report_presentation as presentation
from faculty_report import render_faculty_brief_pdf
from management_trace_analysis import build_analysis_source, source_fingerprint
from management_trace_report import render_management_trace_pdf
from test_faculty_report import brief_example


def analysis_for(payload, *, truncate=False):
    """A valid authored analysis for any frozen payload. No model is called."""
    source = build_analysis_source(payload)
    executed = [row for row in source["timeline"] if row["execution_status"] == "executed"]
    assert executed, "the fixture encounter has to contain an executed decision"
    reflections = {row["decision_ref"]: row["source_ref"] for row in source.get("reflections", [])}

    def claim(text, refs):
        return {"text": text, "evidence_refs": list(dict.fromkeys(refs))[:12]}

    def moment(row):
        before = row["state_before"]["encounter_evidence_refs"]
        after = row["state_after"]["encounter_evidence_refs"]
        insight = (claim("The later reflection revisits this decision.", [reflections[row["source_ref"]]])
                   if row["source_ref"] in reflections else None)
        return {
            "decision_ref": row["source_ref"],
            "title": ("A" * 90) if truncate else "A recorded decision and its response",
            "interpretation": claim("The record before this step is described here.",
                                    [row["source_ref"]] + list(before)[:3]),
            "expected_vs_observed": claim("The stated expectation is compared with the recorded response.",
                                          [row["source_ref"]] + list(after)[:3]),
            "adaptation": claim("The next recorded change is described here.",
                                [row["source_ref"]] + [r["source_ref"] for r in executed[:2]]),
            "reflection_insight": insight,
        }

    first = executed[0]["source_ref"]
    overview = ("B" * 600) if truncate else "The encounter is summarised here in one finished sentence."
    return {
        "schema_version": "management_trace_analysis_v1", "prompt_version": "1.0",
        "source_hash": source_fingerprint(payload),
        "generated_at": "2026-09-22T00:00:00+00:00", "model": "authored-fixture-no-model-call",
        "analysis": {
            "overview": claim(overview, [first]),
            "trajectory": claim("The trajectory is summarised here.", [first]),
            "pivotal_decisions": [moment(row) for row in executed[:5]],
            "strengths": [claim("A documented behaviour worth keeping.", [first])],
            "questions": [claim("An open question for the next encounter.", [first])],
        },
    }


def saved_payload():
    path = Path("local-data/demo_2026-09-22/management_trace_payload.json")
    if not path.exists():
        pytest.skip("the saved demonstration encounter is not present in this checkout")
    return json.loads(path.read_text())


def short_payload():
    """A two-decision encounter built from the saved one, to vary the length."""
    payload = deepcopy(saved_payload())
    payload["trace"] = payload["trace"][:2]
    payload["reflections"] = {key: value for key, value in (payload.get("reflections") or {}).items()
                              if key in {"decision-1", "decision-2"}}
    payload["reflection_prompts"] = [row for row in (payload.get("reflection_prompts") or [])
                                     if str(row.get("review_id")) in {"decision-1", "decision-2"}]
    return payload


def pages(data):
    return [" ".join(page.extract_text().split()) for page in PdfReader(BytesIO(data)).pages]


# --- the structure holds for encounters other than the demonstration --------

@pytest.mark.parametrize("builder", [saved_payload, short_payload])
def test_the_learner_structure_is_the_same_whatever_the_encounter(builder):
    payload = builder()
    printed = pages(render_management_trace_pdf(analysis_for(payload), payload, case_label="R1-05"))
    text = " ".join(printed)
    for section in ("The encounter in perspective", "Recorded patient trajectory",
                    "WHAT EACH MARK WAS", "What to carry forward", "Decisions worth revisiting",
                    "1 · WHAT YOU HAD OBSERVED", "2 · HOW YOU REASONED", "3 · WHAT YOU ORDERED",
                    "4 · WHAT YOU EXPECTED", "5 · WHAT WAS RECORDED NEXT", "Report provenance"):
        assert section in text, section


@pytest.mark.parametrize("builder", [saved_payload, short_payload])
def test_no_page_is_empty_whatever_the_encounter(builder):
    payload = builder()
    for number, page in enumerate(pages(render_management_trace_pdf(analysis_for(payload), payload)), 1):
        assert len(page.replace("MANAGEMENT REASONING SIMULATOR", "")) > 350, (number, page[:120])


def test_the_pagination_follows_the_evidence_and_is_not_fixed():
    long_pages = len(pages(render_management_trace_pdf(analysis_for(saved_payload()), saved_payload())))
    short_pages = len(pages(render_management_trace_pdf(analysis_for(short_payload()), short_payload())))
    assert short_pages < long_pages


# --- an incomplete analysis degrades without blocking the report ------------

def test_a_cut_analysis_keeps_the_record_and_says_the_interpretation_is_incomplete():
    payload = saved_payload()
    printed = pages(render_management_trace_pdf(analysis_for(payload, truncate=True), payload))
    text = " ".join(printed)
    assert "AI INTERPRETATION INCOMPLETE" in text
    assert "is not an interpretation" in text
    assert "Recorded course:" in text
    assert "Technical record" in text
    # The cut fragment is kept, and not read as a finished sentence.
    assert presentation.TRUNCATION_NOTE.strip().split(":")[0].strip("[… ") in text


def test_a_complete_analysis_says_nothing_about_being_incomplete():
    payload = saved_payload()
    text = " ".join(pages(render_management_trace_pdf(analysis_for(payload), payload)))
    assert "AI INTERPRETATION INCOMPLETE" not in text
    assert "Technical record" not in text


# --- the app and the PDFs read the same corrections -------------------------

def test_the_shared_store_is_what_a_renderer_reads_when_nothing_is_passed(tmp_path, monkeypatch):
    payload = saved_payload()
    case_id = payload["trace"][0]["state_before"]["case_id"]
    (tmp_path / (case_id + ".json")).write_text(json.dumps({"corrections": [
        {"original": "The trajectory is summarised here.",
         "replacement": "A CORRECTION FROM THE SHARED STORE.",
         "reason": "checked against the record"}]}))
    monkeypatch.setenv(report_corrections.ENV, str(tmp_path))
    text = " ".join(pages(render_management_trace_pdf(analysis_for(payload), payload)))
    assert "A CORRECTION FROM THE SHARED STORE." in text
    assert "factual correction" in text


def test_without_the_store_nothing_is_corrected(monkeypatch):
    monkeypatch.delenv(report_corrections.ENV, raising=False)
    payload = saved_payload()
    text = " ".join(pages(render_management_trace_pdf(analysis_for(payload), payload)))
    assert "The trajectory is summarised here." in text
    assert "factual correction" not in text


def test_a_faculty_record_reads_the_same_store(tmp_path, monkeypatch):
    report, record = brief_example()
    record.setdefault("payload", {}).setdefault("session", {})["state"] = {"case_id": "CE-contract-check"}
    target = next(item for item in report["analysis"]["objectives"]
                  if item["recommendation"] != "satisfactory")
    original = target["rationale"]
    (tmp_path / "CE-contract-check.json").write_text(json.dumps({"corrections": [
        {"original": original, "replacement": "A CORRECTED FACULTY RATIONALE.", "reason": "checked"}]}))
    monkeypatch.setenv(report_corrections.ENV, str(tmp_path))
    for compact in (True, False):
        assert "A CORRECTED FACULTY RATIONALE." in " ".join(
            pages(render_faculty_brief_pdf(report, record, compact=compact)))
    # The stored brief is never modified.
    assert target["rationale"] == original


def test_a_malformed_store_does_not_break_a_report(tmp_path, monkeypatch):
    payload = saved_payload()
    case_id = payload["trace"][0]["state_before"]["case_id"]
    (tmp_path / (case_id + ".json")).write_text("{not json")
    monkeypatch.setenv(report_corrections.ENV, str(tmp_path))
    assert report_corrections.for_payload(payload) == []
    assert pages(render_management_trace_pdf(analysis_for(payload), payload))
