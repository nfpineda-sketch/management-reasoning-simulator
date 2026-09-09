"""Regression coverage for the v0.8.7 native, privacy-safe PDF export."""

import ast
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader


root = Path(__file__).resolve().parent
source = (root / "app.py").read_text(encoding="utf-8")

assert 'SIMULATOR_VERSION = "0.8.21"' in source
assert "MVP v0.8.21 — dynamic learner-visible ECG with lower-pressure PS001 entry" in source
assert '"Download PDF"' in source
assert 'file_name=f"{case_id}_decision_review_v0819.pdf"' in source
assert '"Previous PDF"' in source
assert 'file_name=f"{prior_case}_attempt_{prior_number}_review_v0819.pdf"' in source
assert 'mime="application/pdf"' in source

requirements = (root / "requirements.txt").read_text(encoding="utf-8")
assert "reportlab" in requirements
assert "pypdf" in requirements

tree = ast.parse(source)
selected = {
    "_pdf_safe_text",
    "_review_pdf",
}
nodes = [
    node for node in tree.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in selected
]
assert {node.name for node in nodes} == selected

namespace = {
    "BytesIO": BytesIO,
    "SIMULATOR_VERSION": "0.8.9",
    "MANAGEMENT_TRACE_DEFINITION": "A time-resolved learner-facing record.",
    "REVIEW_RESPONSE_FIELDS": (
        ("working_model_update", "How has your working model changed?"),
        ("priority_trigger", "What finding or threshold should influence your next priority?"),
        ("alternative_action", "What alternative action would you take?"),
        ("expected_response_reassessment", "What response would you expect, and what would you reassess?"),
    ),
    "EXPERT_COMPARISON_FIELDS": (
        ("alignment", "Where did your reasoning align with this model?"),
        ("change", "What will you change or preserve next time?"),
    ),
    "ADAPTATION_PLAN_FIELDS": (
        ("cue", "Clinical cue to watch"),
        ("threshold", "Threshold for changing course"),
        ("next_priority", "Next management priority"),
        ("alternative_action", "Alternative action"),
        ("expected_effect", "Expected effect"),
        ("reassessment_plan", "Reassessment target and timing"),
    ),
    "_trace_time": lambda minutes: f"{int(minutes) // 60:02d}:{int(minutes) % 60:02d}",
    "_trace_state_text": lambda snapshot: "AF, HR 171/min, BP 102/63, CRT 4 s, SpO₂ 93%",
    "_trace_reasoning_items": lambda reasoning: [
        ("Problem", reasoning.get("problem_representation")),
        ("Priority", reasoning.get("management_priority")),
    ],
    "_trace_action_text": lambda event: "diltiazem 5 mg IV",
    "_trace_observable_delta": lambda before, after, reasoning=None: [
        ("HR", "171/min", "157/min"),
        ("BP", "102/63", "101/63"),
    ],
    "_trace_diagnostic_results": lambda event: [("00:25", "Lactate 4.9 mmol/L")],
}
exec(compile(ast.Module(body=nodes, type_ignores=[]), "v087_pdf_subset", "exec"), namespace)

complete_answers = {
    "working_model_update": "Sepsis is the primary driver; AF may still impair filling.",
    "priority_trigger": "Persistent CRT and lactate despite MAP above 65 mmHg.",
    "alternative_action": "Use a small monitored AV-nodal-blockade trial.",
    "expected_response_reassessment": "Expect lower HR without worse pressure-flow-perfusion.",
}
payload = {
    "schema": "management_reasoning_decision_review_v3",
    "simulator": {"name": "Management Reasoning Simulator", "version": "0.8.9"},
    "encounter": {
        "case_id": "PS001",
        "case_label": "PS001 · Irregular Tachycardia",
        "closed_time_min": 90,
        "hidden": {"forward_flow_state": "must never be exported"},
    },
    "learning_cycle": {"attempt_number": 1, "carry_forward_plan": {}},
    "management_trace": {
        "definition": "A time-resolved learner-facing record.",
        "events": [{
            "execution_status": "executed",
            "decision_time_min": 20,
            "response_time_min": 25,
            "learner_input": "Give diltiazem 5 mg IV and reassess SpO₂ and pressure–flow response.",
            "reasoning": {
                "problem_representation": "AF with RVR during urinary-source sepsis.",
                "management_priority": "Test rate contribution while protecting perfusion.",
            },
            "state_before": {},
            "state_after": {"sim_time_min": 25},
            "developer_state": {"effective_map": 999},
        }],
    },
    "decision_review": {
        "prompts": [{
            "heading": "00:20 · Decision 3",
            "label": "Rate-control trade-off",
            "prompt": "How did the response change your model?",
            "responses": complete_answers,
        }],
    },
    "expert_comparison": {
        "revealed": True,
        "comparisons": [{
            "heading": "00:20 · Decision 3",
            "expert_model": {
                "framing": "AF with RVR is occurring in sepsis.",
                "priority": "Protect tissue perfusion.",
                "cues": ["MAP 76 mmHg", "CRT 4 seconds"],
                "action": "Give a cautious diltiazem trial.",
                "tradeoff": "Negative inotropy may worsen forward flow.",
                "reassessment": "HR, rhythm, BP, CRT, and mental status.",
            },
            "learner_comparison": {
                "alignment": "I used the same diagnostic-therapeutic trial.",
                "change": "I will define stopping thresholds explicitly.",
            },
        }],
    },
    "adaptation_plan": {
        "cue": "Pressure-perfusion mismatch.",
        "threshold": "CRT remains above 3 seconds.",
        "next_priority": "Reassess forward flow independently from HR.",
        "alternative_action": "Use flow-directed support.",
        "expected_effect": "Improve peripheral perfusion.",
        "reassessment_plan": "Reassess within 10 minutes.",
    },
    "review_complete": True,
}

pdf_bytes = namespace["_review_pdf"](payload)
assert pdf_bytes.startswith(b"%PDF-")
assert len(pdf_bytes) > 5000

reader = PdfReader(BytesIO(pdf_bytes))
assert len(reader.pages) >= 4
assert reader.metadata.title == "PS001 Management Reasoning Decision Review"
text = "\n".join(page.extract_text() or "" for page in reader.pages)

for heading in (
    "Management Trace",
    "Decision Review",
    "Expert Comparison",
    "Prospective Adaptation Plan",
    "Educational simulation - reflective and non-scoring",
):
    assert heading in text

assert "diltiazem 5 mg IV" in text
assert "SpO2 93%" in text
assert "pressure-flow response" in text
assert "forward_flow_state" not in text
assert "effective_map" not in text
assert "must never be exported" not in text
assert "\ufffd" not in text

print("PASS: v0.8.7 native PDF export is valid, readable, complete, and privacy-safe")
