"""Learner synthesis PDF provenance, exact charts and resilient document flow."""

from copy import deepcopy
from io import BytesIO

import pytest
from pypdf import PdfReader

from management_trace_analysis import source_fingerprint
from management_trace_report import render_management_trace_pdf, trend_points


def report_example():
    """Synthetic layout example; the analysis text is authored, not a model call."""
    samples = [
        (0, 126, 102, 62, 89, 30, "Alert", "Increased", 4),
        (4, 118, 106, 66, 92, 27, "Alert", "Increased", 4),
        (8, 122, 98, 60, 91, 31, "Drowsy", "Markedly increased", 5),
        (12, 112, 108, 68, 95, 24, "Alert", "Moderately increased", 3),
        (16, 108, 112, 70, 95, 22, "Alert", "Mildly increased", 3),
    ]

    def state(sample):
        time, hr, sbp, dbp, spo2, rr, mental, effort, crt = sample
        return {"sim_time_min": time, "observable": {
            "hr": hr, "sbp": sbp, "dbp": dbp, "spo2": spo2,
            "respiratory_rate": rr, "mental_status": mental,
            "work_of_breathing": effort, "crt": crt,
        }, "hidden": {"diagnosis": "PRIVATE_CASE_TRUTH"}, "diagnostics": {}}

    reasoning = [
        ("The patient has respiratory distress; the cause remains uncertain.",
         "Support oxygenation while obtaining further information.",
         "Oxygenation should improve while I reassess the breathing effort."),
        ("Oxygenation has improved somewhat, but distress persists.",
         "Reassess breathing effort and alertness before changing support.",
         "I expect to clarify whether the patient is sustaining the effort."),
        ("Worsening effort and reduced alertness change my immediate priority.",
         "Escalate respiratory support and ask for assistance.",
         "I expect reduced effort and improved engagement."),
        ("The subsequent observations suggest improved breathing and engagement.",
         "Continue support and reassess whether the response is sustained.",
         "I expect sustained oxygenation without increasing effort."),
    ]
    actions = [
        {"type": "oxygen", "device": "nasal cannula", "flow_lpm": 3},
        {"type": "reassess", "duration_min": 4},
        {"type": "niv", "mode": "BiPAP", "ipap_cmh2o": 10, "epap_cmh2o": 5, "fio2_percent": 40},
        {"type": "reassess", "duration_min": 4},
    ]
    trace = []
    for number, (model, priority, expectation) in enumerate(reasoning):
        trace.append({
            "execution_status": "executed", "decision_time_min": samples[number][0],
            "response_time_min": samples[number + 1][0],
            "state_before": state(samples[number]), "state_after": state(samples[number + 1]),
            "learner_input": model + " " + priority,
            "reasoning": {"problem_representation": model, "management_priority": priority,
                          "rationale": "I will use the observed response to update the working explanation.",
                          "expected_effect": expectation,
                          "reassessment_target": "Breathing effort, oxygenation and alertness at the next review."},
            "action_summaries": [actions[number]],
        })
    payload = {
        "encounter_ended": True, "reflection_locked": True, "trace": trace,
        "reflections": {"decision_3": {
            "working_model_update": "I changed my priority when effort and alertness worsened.",
            "priority_trigger": "Increasing effort despite the initial oxygenation change.",
            "alternative_action": "Seek help and reassess whether support is sufficient.",
            "expected_response_reassessment": "Compare effort and engagement with my expectation.",
        }},
        "reflection_prompts": [{"review_id": "decision_3", "decision": 3}],
        "faculty_brief": {"summary": "PRIVATE_FACULTY_JUDGMENT"},
    }

    def claim(text, *refs):
        return {"text": text, "evidence_refs": list(refs)}

    summaries = [
        ("An initial plan under uncertainty", "The recorded model acknowledges uncertainty while prioritizing oxygenation.",
         "Oxygenation increased after the recorded action; increased effort persisted.",
         "The next entry retains attention to breathing effort rather than relying on oxygenation alone."),
        ("Reassessment reveals a changing picture", "The recorded plan tests whether the initial change is accompanied by reduced distress.",
         "The subsequent record shows greater effort and reduced alertness.",
         "The following decision explicitly changes the immediate support priority."),
        ("Revising the immediate priority", "The recorded reasoning connects worsening effort and alertness to escalation and seeking help.",
         "Reduced effort and improved engagement were recorded afterward, consistent with the stated expectation.",
         "The next entry checks whether the observed response is sustained."),
        ("Checking the response over time", "The recorded working model incorporates the subsequent breathing and engagement observations.",
         "Oxygenation was maintained and respiratory rate decreased during the recorded interval.",
         "No later change to the working model is documented in this encounter."),
    ]
    moments = []
    for number, (title, interpretation, expected, adaptation) in enumerate(summaries):
        ref = f"trace:{number}"
        moments.append({"decision_ref": ref, "title": title,
                        "interpretation": claim(interpretation, ref),
                        "expected_vs_observed": claim(expected, ref),
                        "adaptation": claim(adaptation, ref, f"trace:{number + 1}") if number < 3 else claim(adaptation, ref),
                        "reflection_insight": claim("In the later reflection, the learner identifies effort and engagement as reasons to revise the priority.", "reflection:decision_3") if number == 2 else None})
    report = {
        "schema_version": "management_trace_analysis_v1", "prompt_version": "1.0",
        "source_hash": source_fingerprint(payload), "generated_at": "2026-09-13T18:00:00+00:00",
        "model": "synthetic-layout-example-no-model-call",
        "analysis": {
            "overview": claim("SYNTHETIC LAYOUT EXAMPLE. The recorded sequence moves from initial support under uncertainty to reassessment, revision of the immediate priority, and checking whether the response persists. The learner repeatedly connects the next observation to an expectation rather than treating an isolated monitor change as the whole picture.", "trace:0", "trace:2", "trace:3"),
            "trajectory": claim("The recorded course includes an initial oxygenation change, a later interval of greater respiratory effort and reduced engagement, and subsequent improvement in those observations. The sequence alone does not establish the cause of each change.", "trace:0", "trace:1", "trace:2", "trace:3"),
            "pivotal_decisions": moments,
            "strengths": [claim("The recorded priorities are revised as breathing effort and engagement change.", "trace:1", "trace:2"),
                          claim("The final recorded action checks whether the observed response persists.", "trace:3")],
            "questions": [claim("Which observation would prompt you to revise the support plan again, and what would you reassess first?", "trace:3")],
        },
    }
    return report, payload


def _pdf_text(data):
    reader = PdfReader(BytesIO(data))
    return reader, "\n".join(page.extract_text() for page in reader.pages)


def test_synthesis_preserves_distinct_evidence_interpretation_and_locked_reflection():
    report, payload = report_example()
    original = deepcopy((report, payload))
    reader, text = _pdf_text(render_management_trace_pdf(report, payload, case_label="Synthetic encounter", learner_label="Learner example"))
    assert 3 <= len(reader.pages) <= 5
    assert "Management Trace" in text
    assert "SYNTHETIC LAYOUT EXAMPLE" in text
    # The six blocks the faculty asked for on 2026-09-23, in order.
    for label in ("1 · WHAT YOU HAD OBSERVED", "2 · HOW YOU REASONED", "3 · WHAT YOU ORDERED",
                  "4 · WHAT YOU EXPECTED", "5 · WHAT WAS RECORDED NEXT", "6 · POINT TO REVISIT"):
        assert label in text, label
    assert text.count("4 · WHAT YOU EXPECTED") == 4
    assert "YOUR LATER REFLECTION" in text
    assert "D3" in text and "8 min to 12 min" in text
    # References are readable rather than machine ids (faculty request 2026-09-23),
    # and every claim still says what it rests on.
    assert "Based on:" in text and "trace:" not in text and "reflection:decision" not in text
    assert "your later reflection on D" in text
    # Settings survive the readable rewrite of the ordered actions.
    assert "3 L/min" in text and "10 cm H2O IPAP" in text
    assert "98" in text and "108" in text and "Drowsy" in text
    assert "DRAFT - REVIEW IN PROGRESS" in text
    assert "synthetic-layout-example-no-model-call" in text
    assert report["source_hash"] in text
    assert "PRIVATE_" not in text
    assert (report, payload) == original


def test_source_binding_prevents_old_analysis_over_new_encounter_or_reflection():
    report, payload = report_example()
    payload["trace"][0]["state_after"]["observable"]["spo2"] = 94
    with pytest.raises(ValueError, match="does not match"):
        render_management_trace_pdf(report, payload)
    report, payload = report_example()
    payload["reflections"]["decision_3"]["working_model_update"] = "Different reflection."
    with pytest.raises(ValueError, match="does not match"):
        render_management_trace_pdf(report, payload)


def test_precise_chart_values_skip_missing_nonfinite_and_boolean_measurements():
    timeline = [
        {"source_ref": "trace:0", "decision_time_min": 0, "response_time_min": 4,
         "state_before": {"observable": {"hr": 120}}, "state_after": {"observable": {"hr": 116}}},
        {"source_ref": "trace:1", "decision_time_min": 4, "response_time_min": 8,
         "state_before": {"observable": {"hr": 116}}, "state_after": {"observable": {"hr": None}}},
        {"source_ref": "trace:2", "decision_time_min": 9, "response_time_min": 10,
         "state_before": {"observable": {"hr": True}}, "state_after": {"observable": {"hr": float("nan")}}},
        {"source_ref": "trace:3", "decision_time_min": 10, "response_time_min": 14,
         "state_before": {"observable": {"hr": 110}}, "state_after": {"observable": {"hr": 109.5}}},
    ]
    points = trend_points(timeline, "hr")
    assert [(point["time_min"], point["value"]) for point in points] == [(0, 120), (4, 116), (8, None), (9, None), (10, None), (10, 110), (14, 109.5)]
    assert points[1]["evidence_refs"] == ["trace:0", "trace:1"]
    with pytest.raises(ValueError, match="supported"):
        trend_points(timeline, "hidden_glucose")


def test_final_later_plan_does_not_change_or_relabel_the_frozen_ai_source():
    report, payload = report_example()
    reader, text = _pdf_text(render_management_trace_pdf(
        report, payload, review_completed=True,
        adaptation_plan={"cue": "Effort & alertness; no monitor-only shortcut.",
                         "reassessment_plan": "Reevaluaré SpO₂ > 94% y el esfuerzo. <b>literal</b>"},
    ))
    assert "REVIEW COMPLETE" in text
    assert "DRAFT - REVIEW IN PROGRESS" not in text
    assert "Written by you after the comparison" in text
    assert "Reevaluaré SpO2 > 94%" in text and "<b>literal</b>" in text
    assert report["source_hash"] in text


def test_long_bilingual_evidence_and_plan_flow_to_end_without_xml_or_layout_failure():
    report, payload = report_example()
    payload["trace"][0]["reasoning"]["expected_effect"] = (
        "Reevaluaré perfusión & oxigenación. <tag>Texto literal</tag> SpO₂ > 94%. " * 80
        + "END_OF_LONG_EXPECTATION")
    report["source_hash"] = source_fingerprint(payload)
    _, text = _pdf_text(render_management_trace_pdf(
        report, payload, adaptation_plan={"cue": "Palidez & cansancio. " * 300 + "END_OF_LONG_PLAN"}))
    assert "END_OF_LONG_EXPECTATION" in text and "END_OF_LONG_PLAN" in text
    assert "<tag>Texto literal</tag>" in text
    assert "Reevaluaré" in text and "SpO2 > 94%" in text
    assert "\x00" not in text


def test_acquired_result_keeps_collection_and_availability_times_and_actual_sedation():
    report, payload = report_example()
    payload["trace"][0]["state_after"]["diagnostics"]["poc_glucose"] = {
        "time_min": 4, "collected_at_min": 2, "glucose_mg_dl": 83,
        "private_metadata": "PRIVATE_RESULT"}
    payload["trace"][0]["action_summaries"].append({
        "type": "sedation", "medications": [{"agent": "example", "dose_mg": 2, "route": "IV"}],
        "private_mechanism": "PRIVATE_ACTION"})
    report["source_hash"] = source_fingerprint(payload)
    _, text = _pdf_text(render_management_trace_pdf(report, payload))
    assert "available at 4 min, sampled at 2 min" in " ".join(text.split())
    assert "glucose 83 mg/dL" in text
    assert "with example 2 mg IV" in " ".join(text.split())
    assert "PRIVATE_" not in text
