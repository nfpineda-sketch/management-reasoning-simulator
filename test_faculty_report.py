"""PDF content fidelity, stale-record rejection and hostile/long text layout."""

from copy import deepcopy
from io import BytesIO

import pytest
from pypdf import PdfReader

from faculty_report import render_faculty_brief_pdf
from objectives import OBJECTIVES


def brief_example():
    """Synthetic illustration fixture; no real model or clinical grading call."""
    record = {
        "id": "synthetic-faculty-report-example", "revision": 7,
        "username": "EXAMPLE - synthetic learner", "challenge_id": "R1-04",
        "updated_at": 1789231062, "status": "completed",
        "encounter": {"hidden": {"private_marker": "DO_NOT_PRINT_ENCOUNTER"}},
        "payload": {"session": {
            "review_completed": True, "state": {"case_id": "PS001"},
            "management_trace": [{
                "execution_status": "executed", "decision_time_min": 46,
                "learner_input": "Mantendré la reevaluación de perfusión; SpO₂ > 94% y pCO₂. <b>Literal learner text</b> & reasoning.",
                "state_before": {"hidden": {"private_marker": "DO_NOT_PRINT_STATE"}},
                "action_summaries": [{"hidden_marker": "DO_NOT_PRINT_ACTION"}],
            }],
            "precomparison_decision_review": {"1": {
                "working_model_update": "My pressure target was met but the perfusion examination remained abnormal.",
                "priority_trigger": "Recurrent deterioration in the recorded examination.",
                "alternative_action": "Reassess the mechanism before escalating support.",
                "expected_response_reassessment": "Compare the next response with my stated expectation.",
            }},
        }},
    }
    report = {
        "schema_version": "faculty_brief_v1", "prompt_version": "1.0",
        "source_hash": "a" * 64, "attempt_id": record["id"],
        "attempt_revision": record["revision"], "model": "synthetic-example-no-model-call",
        "generated_at": "2026-09-12T18:00:00+00:00",
        "assistance_context": "guided",
        "analysis": {
            "summary": "SYNTHETIC DESIGN EXAMPLE. The learner distinguishes pressure from tissue-perfusion findings and states a plan for reassessment. Faculty should inspect the cited reasoning and verify the interpretation before recording any judgment.",
            "strengths": ["The expectation and reassessment plan are explicit.", "The later reflection acknowledges uncertainty about mechanism."],
            "review_points": ["Verify that the interpretation uses information available at the decision time.", "Confirm the nature and timing of the assistance received."],
            "learning_cycle": "The recorded input is in-encounter evidence. The subsequent reflection adds a retrospective interpretation and cannot establish what the learner understood beforehand.",
            "limits": ["This is an illustrative fixture, not an evaluation of an actual resident.", "A favorable response alone cannot establish satisfactory management reasoning."],
            "key_decisions": [{
                "evidence_refs": ["trace:0", "reflection:1"],
                "analysis": "The input names tissue perfusion as a reassessment target. The later reflection states that pressure and perfusion may diverge. Confirm that the recorded action and observed findings support this account.",
                "question": "Which finding would change your next priority, and why?",
            }],
            "objectives": [],
        },
    }
    additional = [
        (49, "I will compare the next perfusion findings with my stated expectation and reassess the working model.",
         "The learner connects the next observation to an explicit expectation. Faculty should ask how an unexpected response would alter management.",
         "What alternative explanation would you consider if perfusion does not improve?"),
        (64, "I will preserve the current support while reassessing alertness, perfusion and breathing.",
         "The learner proposes reassessment at the current support. The record should establish whether this is a deliberate decision based on the observed trajectory.",
         "What finding would prompt you to change course?"),
    ]
    for minute, learner_input, interpretation, question in additional:
        trace = record["payload"]["session"]["management_trace"]
        reference = f"trace:{len(trace)}"
        trace.append({"execution_status": "executed", "decision_time_min": minute,
                      "learner_input": learner_input})
        report["analysis"]["key_decisions"].append({
            "evidence_refs": [reference], "analysis": interpretation, "question": question,
        })
    for objective_id, entry in OBJECTIVES.items():
        if not entry["supported"]:
            continue
        sufficient = objective_id in {"TD1", "F1", "C1"}
        report["analysis"]["objectives"].append({
            "objective_id": objective_id,
            "recommendation": "satisfactory" if sufficient else "insufficient_evidence",
            "rationale": "Illustrative provisional judgment: the cited input and reflection allow a focused review of prioritization and reassessment. Faculty must inspect the full sequence and the scope of this objective." if sufficient else "The selected example does not document enough of this specific simulated component to support a judgment. This does not establish poor performance.",
            "depth": "foundational" if sufficient else None,
            "autonomy": "guided" if sufficient else None,
            "context": "Synthetic simulated circulatory support and reassessment.",
            "evidence_refs": ["trace:0", "reflection:1"] if sufficient else [],
            "feedback": "Preserve the explicit link between your expected effect and the reassessment findings. Explain how discordant findings would change your next priority." if sufficient else "A future encounter should provide an opportunity to demonstrate and explain this component before it is assessed.",
            "questions": ["What additional evidence or discussion is needed before the faculty judgment?"],
        })
    return report, record


def test_brief_pdf_preserves_user_text_provenance_and_distinct_recommendations():
    report, record = brief_example()
    before = deepcopy((report, record))
    pdf = render_faculty_brief_pdf(report, record, compact=False)
    reader = PdfReader(BytesIO(pdf))
    text = "\n".join(page.extract_text() for page in reader.pages)
    assert len(reader.pages) == 5
    assert "SYNTHETIC DESIGN EXAMPLE" in text
    assert "Mantendré" in text and "SpO2 > 94%" in text
    assert "<b>Literal learner text</b> & reasoning." in " ".join(text.split())
    assert "Decision 1 | 00:46 [trace:0]" in text
    assert "Reflection 1 | Post-encounter reflection [reflection:1]" in text
    assert "Insufficient evidence to judge" in text
    assert "Needs faculty judgment" in text
    assert "Guided - structured help directed the reasoning (faculty-reported)." in text
    assert "a" * 64 in text
    assert "Prompt version: 1.0" in text
    for marker in ("DO_NOT_PRINT_ENCOUNTER", "DO_NOT_PRINT_STATE", "DO_NOT_PRINT_ACTION"):
        assert marker not in text
    assert (report, record) == before


def test_long_feedback_flows_without_lost_text_or_layout_failure():
    report, record = brief_example()
    long_feedback = "Español & <literal>: reassess pCO₂ and SpO₂. " * 80 + "UNIQUE_END_OF_LONG_FEEDBACK"
    report["analysis"]["objectives"][0]["feedback"] = long_feedback
    report["analysis"]["objectives"][0]["recommendation"] = "needs_improvement"
    reader = PdfReader(BytesIO(render_faculty_brief_pdf(report, record, compact=False)))
    text = "\n".join(page.extract_text() for page in reader.pages)
    assert len(reader.pages) >= 6
    assert "UNIQUE_END_OF_LONG_FEEDBACK" in text
    assert "Suggested improvement needed" in text
    assert "Insufficient evidence to judge" in text
    assert "\x00" not in text


@pytest.mark.parametrize("field,value", [("attempt_id", "other"), ("attempt_revision", 8)])
def test_renderer_rejects_mixed_record(field, value):
    report, record = brief_example()
    report[field] = value
    with pytest.raises(ValueError, match="different encounter"):
        render_faculty_brief_pdf(report, record)


def test_renderer_rejects_unresolved_citation():
    report, record = brief_example()
    report["analysis"]["key_decisions"][0]["evidence_refs"] = ["trace:999"]
    with pytest.raises(ValueError, match="unavailable"):
        render_faculty_brief_pdf(report, record)



def test_default_concise_pdf_preserves_suggestions_citations_and_faculty_route():
    report, record = brief_example()
    report["assistance_context"] = "unknown"
    report["analysis"]["limits"].insert(0, "Autonomy cannot be assessed because assistance is unknown.")
    report["analysis"]["objectives"][1]["recommendation"] = "needs_improvement"
    before = deepcopy((report, record))
    reader = PdfReader(BytesIO(render_faculty_brief_pdf(
        report, record, app_url="https://faculty.example/app?token=PRIVATE_TOKEN&other=value#secret",
    )))
    text = "\n".join(page.extract_text() for page in reader.pages)
    assert len(reader.pages) == 2
    for objective in report["analysis"]["objectives"]:
        assert objective["objective_id"] in reader.pages[0].extract_text()
    assert "Satisfactory" in text
    assert "Needs improvement" in text
    assert "Insufficient evidence" in " ".join(text.split())
    assert "D1 00:46" in text
    assert "Reflection 1" in text
    assert "Not known / not documented" in text
    assert text.count("Assistance and autonomy:") == 1
    assert "Autonomy cannot be assessed because assistance is unknown" not in text
    assert "selected review priorities" in text
    assert "Rationale excerpts" in text
    assert "Full citations, feedback and rationales" in text
    assert "not image acquisition" in text
    assert "review and record your assessment" in text
    assert "Prompt 1.0" in text
    assert "PRIVATE_TOKEN" not in text
    assert "DO_NOT_PRINT" not in text
    links = [
        str(annotation.get_object()["/A"]["/URI"])
        for page in reader.pages for annotation in page.get("/Annots", [])
        if annotation.get_object().get("/A", {}).get("/S") == "/URI"
    ]
    assert links == ["https://faculty.example/app?faculty_attempt=synthetic-faculty-report-example"]
    assert (report, record) == before


def test_verbose_legacy_report_fits_two_pages_without_shrinking_or_silent_clause_clipping():
    report, record = brief_example()
    report["analysis"]["summary"] *= 8
    report["analysis"]["learning_cycle"] *= 8
    for item in report["analysis"]["objectives"]:
        item["rationale"] = "The learner " + "considered perfusion and oxygenation " * 10 + ". More details. "
        item["feedback"] = "Preserve the reasoning. " * 150 + "UNIQUE_FULL_ANALYSIS_TAIL"
    report["analysis"]["review_points"] = [
        "Review " + "the recorded response and management strategy " * 11 + ". Additional sentence."
    ] * 5
    for item in report["analysis"]["key_decisions"]:
        item["question"] = "How " + "would you reassess the response to treatment " * 6 + "? Extra question?"
    before = deepcopy((report, record))
    reader = PdfReader(BytesIO(render_faculty_brief_pdf(report, record)))
    text = "\n".join(page.extract_text() for page in reader.pages)
    assert len(reader.pages) == 2
    assert "1 / 2" in reader.pages[0].extract_text()
    assert "2 / 2" in reader.pages[1].extract_text()
    assert "Review the full rationale in the app before judging this objective" in text
    assert "First 3 of 5 review points" in text
    assert "read the complete" in text.lower() or "context cannot be safely shortened" in text
    assert "UNIQUE_FULL_ANALYSIS_TAIL" not in text
    text_runs = []
    for page in reader.pages:
        page.extract_text(visitor_text=lambda value, cm, tm, font, size: text_runs.append((value, size)))
    # Only running headers/footer may be smaller; main text remains readable.
    for value, size in text_runs:
        if "Review the full rationale" in value or "recorded response" in value:
            assert size >= 9.3
    full_reader = PdfReader(BytesIO(render_faculty_brief_pdf(report, record, compact=False)))
    assert "UNIQUE_FULL_ANALYSIS_TAIL" in "\n".join(page.extract_text() for page in full_reader.pages)
    assert (report, record) == before


def test_concise_pdf_keeps_airway_review_concern_and_plain_language():
    report, record = brief_example()
    report["analysis"]["review_points"] = [
        "The record shows procedural sedation was executed while airway_prepared remained false; review preparation and monitoring without inferring unrecorded skill performance."
    ]
    text = "\n".join(page.extract_text() for page in PdfReader(BytesIO(
        render_faculty_brief_pdf(report, record))).pages)
    assert "airway preparation was not marked as completed" in text
    assert "without inferring unrecorded skill performance" in text
    assert "airway_prepared" not in text
    assert "airway_prepared" in report["analysis"]["review_points"][0]


@pytest.mark.parametrize("app_url", ["javascript:alert(1)", "https://user:secret@faculty.example/", "file:///report", "https:///missing-host"])
def test_concise_pdf_rejects_unsafe_application_urls(app_url):
    report, record = brief_example()
    with pytest.raises(ValueError, match="public HTTP"):
        render_faculty_brief_pdf(report, record, app_url=app_url)
