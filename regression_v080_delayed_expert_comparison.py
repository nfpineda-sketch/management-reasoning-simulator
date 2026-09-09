"""Regression coverage for v0.8.0 delayed, non-scoring expert comparison."""

import ast
import json
from copy import deepcopy
from pathlib import Path


source = Path("app.py").read_text(encoding="utf-8")
assert 'SIMULATOR_VERSION = "0.8.21"' in source
assert "MVP v0.8.21 — dynamic learner-visible ECG with lower-pressure PS001 entry" in source
assert '"2 · Expert Comparison"' in source
assert '"Lock Decision Review & Reveal Expert Comparison"' in source
assert "Your original reflection is locked" in source
assert "faculty-validation draft, not an answer key" in source
assert 'file_name=f"{case_id}_decision_review_v0819.md"' in source
assert 'file_name=f"{case_id}_decision_review_v0819.json"' in source

tree = ast.parse(source)
selected_functions = {
    "_review_heading",
    "_strip_private_review_data",
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
    "_review_is_complete",
    "_review_payload",
    "_review_markdown",
    "_review_json",
    "_review_widget_key",
    "_adaptation_widget_key",
    "_comparison_widget_key",
    "_latest_review_response",
    "_normalize_review_text",
    "_first_review_sentence",
    "_ensure_terminal_punctuation",
    "_clean_reasoning_phrase",
    "_cue_from_priority_trigger",
    "_threshold_from_priority_trigger",
    "_split_expected_reassessment",
    "_suggest_adaptation_plan",
    "_merge_adaptation_suggestions",
    "_sync_compact_review_state",
    "_sync_expert_comparison_state",
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


namespace = {
    "st": FakeSt(),
    "_trace_time": lambda minute: f"{int(minute) // 60:02d}:{int(minute) % 60:02d}",
    "_trace_state_text": lambda snapshot: "BP 94/53 · SpO2 93%",
    "_trace_reasoning_items": lambda reasoning: [],
    "_trace_action_text": lambda event: "support adjustment",
    "_trace_observable_delta": lambda before, after, reasoning=None: [],
    "_trace_diagnostic_results": lambda event: [],
}
exec(compile(ast.Module(body=nodes, type_ignores=[]), "v080_subset", "exec"), namespace)

prompts = [
    {"review_id": "decision-2", "kind": "decision", "decision": 2, "time": "00:15", "label": "Alignment", "prompt": "Review 2"},
    {"review_id": "decision-9", "kind": "decision", "decision": 9, "time": "01:20", "label": "Adaptation", "prompt": "Review 9"},
    {"review_id": "decision-11", "kind": "decision", "decision": 11, "time": "01:35", "label": "Expected response", "prompt": "Review 11"},
]
responses = {
    prompt["review_id"]: {
        "working_model_update": "Shock and respiratory failure remained active.",
        "priority_trigger": "Worsening capillary refill and lactate should trigger reassessment.",
        "alternative_action": "Repeat focused POCUS and change one support variable at a time.",
        "expected_response_reassessment": "I expect better perfusion. I would reassess BP, CRT, SpO2, and lactate.",
    }
    for prompt in prompts
}
plan = {
    "cue": "Pressure–perfusion mismatch.",
    "threshold": "Worsening CRT or lactate after intervention.",
    "next_priority": "Reassess pressure, flow, perfusion, and ventilator burden.",
    "alternative_action": "Repeat focused POCUS.",
    "expected_effect": "Improved tissue perfusion while preserving oxygenation.",
    "reassessment_plan": "BP, CRT, SpO2, and lactate within 5–10 minutes.",
}
comparison_responses = {
    prompt["review_id"]: {
        "alignment": "I recognized persistent shock and the need for reassessment.",
        "adjustment": "I will separate pressure from flow and change one support variable at a time.",
    }
    for prompt in prompts
}
base_event = {
    "execution_status": "executed",
    "decision_time_min": 15,
    "response_time_min": 25,
    "learner_input": "Start BiPAP and reassess.",
    "interpreted_action": [{"type": "reassessment"}],
    "action_summaries": [],
    "reasoning": {},
    "state_before": {
        "observable": {"sbp": 94, "dbp": 60, "hr": 120, "rhythm": "AF", "crt": 4,
                       "extremities": "Cool", "mental_status": "Alert", "spo2": 93,
                       "respiratory_rate": 28, "work_of_breathing": "Increased"},
        "treatments": {},
        "physiology": {"forward_flow_state": 0.3},
    },
    "state_after": {
        "observable": {"sbp": 90, "dbp": 58, "hr": 118, "rhythm": "AF", "crt": 5,
                       "extremities": "Cool", "mental_status": "Drowsy", "spo2": 92,
                       "respiratory_rate": 28, "work_of_breathing": "Increased"},
        "treatments": {},
        "hidden": {"secret": True},
    },
}
trace = [deepcopy(base_event) for _ in range(11)]
trace[1]["interpreted_action"] = [{"type": "niv"}]
trace[1]["action_summaries"] = [{"support_type": "niv", "mode": "BiPAP", "ipap_cmh2o": 12, "epap_cmh2o": 6}]
trace[8]["interpreted_action"] = [{"type": "norepinephrine"}]
trace[8]["action_summaries"] = [{"support_type": "norepinephrine", "operation": "start", "rate": 0.1, "units": "mcg/kg/min"}]
trace[10]["interpreted_action"] = [{"type": "dobutamine"}]
trace[10]["action_summaries"] = [{"support_type": "dobutamine", "operation": "start", "rate": 5, "units": "mcg/kg/min"}]
final_state = {
    "case_id": "PS002",
    "observable": {"sbp": 94, "spo2": 93},
    "physiology": {"forward_flow_state": 0.2},
}

models = namespace["_expert_models_for_prompts"]("PS002", prompts)
assert set(models) == {"decision-2", "decision-9", "decision-11"}
assert "positive pressure" in models["decision-2"]["priority"]
assert "P/F ratio" in models["decision-9"]["cues"][0]
assert "simultaneously" in models["decision-11"]["tradeoff"]
assert namespace["_decision_review_complete"](prompts, responses) is True
assert namespace["_expert_comparison_complete"](models, comparison_responses) is True

# Before reveal, neither export format may disclose the expert model.
hidden_payload = namespace["_review_payload"](
    "PS002 · Acute Dyspnea with Shock",
    95,
    trace,
    final_state,
    prompts,
    responses,
    plan,
    {},
    False,
)
assert hidden_payload["schema"] == "management_reasoning_decision_review_v3"
assert hidden_payload["expert_comparison"]["revealed"] is False
assert hidden_payload["expert_comparison"]["comparisons"] == []
assert hidden_payload["review_complete"] is False
hidden_json = namespace["_review_json"](hidden_payload)
assert "Protect perfusion while escalating respiratory support" not in hidden_json

# After reveal, the model and learner comparison are exported separately and
# completion requires both comparison fields for all three decisions.
revealed_payload = namespace["_review_payload"](
    "PS002 · Acute Dyspnea with Shock",
    95,
    trace,
    final_state,
    prompts,
    responses,
    plan,
    comparison_responses,
    True,
)
assert revealed_payload["review_complete"] is True
assert revealed_payload["decision_review"]["locked_before_expert_reveal"] is True
assert len(revealed_payload["expert_comparison"]["comparisons"]) == 3
assert revealed_payload["expert_comparison"]["comparisons"][2]["learner_comparison"]["adjustment"].startswith("I will separate")
revealed_markdown = namespace["_review_markdown"](revealed_payload)
assert "## Expert Comparison" in revealed_markdown
assert "**Trade-off to manage**" in revealed_markdown
assert "one defensible approach, not an answer key" in revealed_markdown
assert "forward_flow_state" not in revealed_markdown
assert "forward_flow_state" not in namespace["_review_json"](revealed_payload)

incomplete_comparison = deepcopy(comparison_responses)
incomplete_comparison["decision-9"]["adjustment"] = ""
assert namespace["_review_is_complete"](
    prompts, responses, plan, models, incomplete_comparison, True
) is False

# Once revealed, a stale or modified review widget cannot rewrite the locked
# pre-comparison reflection.
session = namespace["st"].session_state
session.decision_review = deepcopy(responses)
session.precomparison_decision_review = deepcopy(responses)
session.adaptation_plan = {}
session.adaptation_plan_user_edited = {}
session.review_autosave_revision = 0
session[namespace["_review_widget_key"]("decision-2", "working_model_update")] = "contaminated after reveal"
locked_responses, _, _ = namespace["_sync_compact_review_state"](prompts, review_locked=True)
assert locked_responses["decision-2"]["working_model_update"] == "Shock and respiratory failure remained active."

# Comparison insights autosave independently from the locked Decision Review.
session.expert_comparison_responses = {}
for field, _ in namespace["EXPERT_COMPARISON_FIELDS"]:
    session[namespace["_comparison_widget_key"]("decision-2", field)] = comparison_responses["decision-2"][field]
saved_comparison = namespace["_sync_expert_comparison_state"](models, True)
assert saved_comparison["decision-2"]["alignment"].startswith("I recognized")
assert session.precomparison_decision_review == responses

print("PASS: v0.8.0 delays expert reveal, locks self-reflection, captures comparison, and exports both layers")
