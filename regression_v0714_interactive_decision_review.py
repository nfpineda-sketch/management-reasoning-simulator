"""Regression coverage for the v0.7.14 frozen review and export layer."""

import ast
import json
from copy import deepcopy
from pathlib import Path


source = Path("app.py").read_text(encoding="utf-8")
assert "MVP v0.8.21 — dynamic learner-visible ECG with lower-pressure PS001 entry" in source
assert "Complete Encounter & Begin Review" in source
assert "Autosave is active" in source
assert "Download Markdown" in source and "Download JSON" in source

tree = ast.parse(source)
selected_functions = {
    "_review_heading",
    "_review_prompt_records",
    "_event_for_review_prompt",
    "_action_types_for_event",
    "_trajectory_expert_model",
    "_expert_model_for_prompt",
    "_expert_models_for_prompts",
    "_trace_action_text",
    "_trace_state_text",
    "_trace_observable_delta",
    "_summaries_in_learner_order",
    "_summary_source_position",
    "_norepinephrine_summary_label",
    "procedural_sedation_label",
    "_decision_review_complete",
    "_expert_comparison_complete",
    "_strip_private_review_data",
    "_review_is_complete",
    "_review_payload",
    "_review_markdown",
    "_review_json",
    "begin_decision_review",
}
selected_constants = {
    "SIMULATOR_VERSION",
    "MANAGEMENT_TRACE_DEFINITION",
    "REVIEW_RESPONSE_FIELDS",
    "ADAPTATION_PLAN_FIELDS",
    "EXPERT_COMPARISON_FIELDS",
    "EXPERT_REASONING_MODELS",
}
nodes = []
for node in tree.body:
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        if not any(alias.name == "streamlit" for alias in node.names):
            nodes.append(node)
    elif isinstance(node, ast.Assign):
        names = {target.id for target in node.targets if isinstance(target, ast.Name)}
        if names & selected_constants:
            nodes.append(node)
    elif isinstance(node, ast.FunctionDef) and node.name in selected_functions:
        nodes.append(node)


class Session(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


class FakeSt:
    session_state = Session()


def fake_reflect_compare_items(_trace):
    return [
        ("decision", 2, "00:15", "Stated interpretation vs available data", "Which data challenged the model?"),
        ("decision", 9, "01:20", "Expected effect vs observed response", "What response changed the priority?"),
        ("decision", 11, "01:35", "Mixed response", "How did you update the model?"),
    ]


namespace = {
    "st": FakeSt(),
    "_reflect_compare_items": fake_reflect_compare_items,
    "_trace_time": lambda minute: f"{int(minute) // 60:02d}:{int(minute) % 60:02d}",
    "_trace_state_text": lambda snapshot: f'BP {(snapshot.get("observable") or {}).get("sbp")}',
    "_trace_reasoning_items": lambda reasoning: [
        ("Problem", reasoning["problem_representation"])
    ] if reasoning and reasoning.get("problem_representation") else [],
    "_trace_action_text": lambda event: "norepinephrine titration",
    "_trace_observable_delta": lambda before, after, reasoning=None: [
        ("BP", str((before.get("observable") or {}).get("sbp")), str((after.get("observable") or {}).get("sbp")))
    ],
    "_trace_diagnostic_results": lambda event: [],
    "management_state_snapshot": lambda state: deepcopy(state["snapshot"]),
}
exec(compile(ast.Module(body=nodes, type_ignores=[]), "v0714_subset", "exec"), namespace)

prompts = namespace["_review_prompt_records"]([{"execution_status": "executed"}])
assert [prompt["review_id"] for prompt in prompts] == ["decision-2", "decision-9", "decision-11"]
assert namespace["_review_heading"](prompts[0]) == "00:15 · Decision 2"

trace = [{
    "execution_status": "executed",
    "decision_time_min": 15,
    "response_time_min": 25,
    "learner_input": "Increase norepinephrine and reassess.",
    "reasoning": {"problem_representation": "persistent shock"},
    "state_before": {
        "observable": {"sbp": 84},
        "physiology": {"forward_flow_state": 0.21},
        "hidden": {"secret": True},
    },
    "state_after": {
        "observable": {"sbp": 104},
        "physiology": {"forward_flow_state": 0.24},
    },
    "action_summaries": [{"support_type": "norepinephrine", "rate": 0.2}],
}]

responses = {}
for prompt in prompts:
    responses[prompt["review_id"]] = {
        "working_model_update": "Pressure improved but flow remained impaired.",
        "priority_trigger": "Persistent CRT prolongation and rising lactate.",
        "alternative_action": "Reassess flow and reduce excessive intrathoracic pressure.",
        "expected_response_reassessment": "Improved CRT and lactate; reassess in 10 minutes.",
    }
plan = {
    "cue": "Pressure–perfusion dissociation",
    "threshold": "CRT worsens despite MAP response",
    "next_priority": "Reassess forward flow",
    "alternative_action": "Repeat POCUS and revise support",
    "expected_effect": "Improved peripheral perfusion",
    "reassessment_plan": "BP, CRT, extremities, and lactate in 10 minutes",
}
final_state = {
    # Use an unmapped case here so this historical privacy/freeze regression
    # remains independent of later expert-comparison models.
    "case_id": "PS003",
    "sim_time_min": 25,
    "observable": {"sbp": 104},
    "physiology": {"effective_map": 77.0},
}

payload = namespace["_review_payload"](
    "PS002 · Acute Dyspnea with Shock", 25, trace, final_state, prompts, responses, plan
)
assert payload["review_complete"] is True
assert payload["management_trace"]["definition"].startswith("Management Trace is a time-resolved record")
assert "physiology" not in payload["management_trace"]["events"][0]["state_before"]
assert "hidden" not in payload["management_trace"]["events"][0]["state_before"]
assert "physiology" not in payload["encounter"]["final_patient_state"]
assert trace[0]["state_before"]["physiology"]["forward_flow_state"] == 0.21

markdown = namespace["_review_markdown"](payload)
assert "## Management Trace" in markdown
assert "## Decision Review" in markdown
assert "## Expert Comparison" in markdown
assert "## Adaptation Plan" in markdown
assert "Pressure improved but flow remained impaired." in markdown
assert "Pressure–perfusion dissociation" in markdown
assert "reflective and non-scoring" in markdown
assert "forward_flow_state" not in markdown

json_text = namespace["_review_json"](payload)
decoded = json.loads(json_text)
assert decoded["schema"] == "management_reasoning_decision_review_v3"
assert decoded["decision_review"]["prompts"][1]["review_id"] == "decision-9"
assert "forward_flow_state" not in json_text

incomplete = deepcopy(responses)
incomplete["decision-9"]["alternative_action"] = ""
assert namespace["_review_is_complete"](prompts, responses, plan) is True
assert namespace["_review_is_complete"](prompts, incomplete, plan) is False

# Closing the encounter freezes independent copies; subsequent live mutation must
# not rewrite either the Management Trace or the final state used for review.
fake_state = {"sim_time": 25, "snapshot": deepcopy(final_state)}
namespace["begin_decision_review"](trace, fake_state)
trace[0]["learner_input"] = "mutated live trace"
fake_state["snapshot"]["observable"]["sbp"] = 1
session = namespace["st"].session_state
assert session.encounter_ended is True
assert session.encounter_closed_trace[0]["learner_input"] == "Increase norepinephrine and reassess."
assert session.encounter_closed_state["observable"]["sbp"] == 104
assert session.review_prompts[0]["review_id"] == "decision-2"
assert session.decision_review == {} and session.adaptation_plan == {}

print("PASS: v0.7.14 frozen Decision Review, Adaptation Plan, and privacy-safe Markdown/JSON export")
