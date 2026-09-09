"""Regression coverage for v0.8.1 carry-forward adaptation and repeat attempts."""

import ast
from copy import deepcopy
from pathlib import Path


source = Path("app.py").read_text(encoding="utf-8")
assert 'SIMULATOR_VERSION = "0.8.21"' in source
assert "MVP v0.8.21 — dynamic learner-visible ECG with lower-pressure PS001 entry" in source
assert '"Repeat Encounter with This Adaptation Plan"' in source
assert 'f"### Attempt {attempt_number} · Carry-Forward Learning Goal"' in source
assert '"Previous Markdown"' in source and '"Previous JSON"' in source
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
    "_expert_comparison_complete",
    "_review_is_complete",
    "_review_payload",
    "_review_markdown",
    "begin_repeat_encounter",
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


def state_factory():
    return {"case_id": "PS002", "sim_time": 0, "seed": 17}


def add_event(kind, text, time=None):
    FakeSt.session_state.events.append({"kind": kind, "text": text, "time": int(time or 0)})


namespace = {
    "st": FakeSt(),
    "CASE_CONFIGS": {
        "PS002 · Acute Dyspnea with Shock": {
            "id": "PS002",
            "state_factory": state_factory,
            "presentation": "Repeat presentation",
        }
    },
    "add_event": add_event,
    "_trace_time": lambda minute: f"{int(minute) // 60:02d}:{int(minute) % 60:02d}",
}
exec(compile(ast.Module(body=nodes, type_ignores=[]), "v081_subset", "exec"), namespace)

plan = {
    "cue": "Pressure–perfusion mismatch.",
    "threshold": "Worsening CRT or lactate after intervention.",
    "next_priority": "Reassess pressure, flow, perfusion, and ventilator burden.",
    "alternative_action": "Repeat focused POCUS.",
    "expected_effect": "Improved tissue perfusion while preserving oxygenation.",
    "reassessment_plan": "BP, CRT, SpO2, and lactate within 5–10 minutes.",
}

session = namespace["st"].session_state
session.update({
    "selected_case": "PS002 · Acute Dyspnea with Shock",
    "attempt_number": 1,
    "encounter_closed_state": {"case_id": "PS002", "physiology": {"secret": True}},
    "encounter_closed_time_min": 95,
    "events": [{"kind": "old"}],
    "history": ["old"],
    "management_trace": [{"decision": 1}],
    "decision_review": {"decision-2": {"working_model_update": "old"}},
    "adaptation_plan": deepcopy(plan),
    "adaptation_plan_user_edited": {"cue": True},
    "expert_comparison_unlocked": True,
    "precomparison_decision_review": {"decision-2": {}},
    "expert_comparison_responses": {"decision-2": {"alignment": "old"}},
    "decision_review__decision-2__working_model_update": "stale widget",
    "adaptation_plan__cue": "stale widget",
    "expert_comparison__decision-2__alignment": "stale widget",
})

prior_record = {
    "schema": "management_reasoning_decision_review_v3",
    "learning_cycle": {"attempt_number": 1},
    "management_trace": {"events": [{"decision": 1}]},
    "hidden": {"secret": True},
}
prior = namespace["begin_repeat_encounter"](plan, prior_record)
assert session.attempt_number == 2
assert session.carry_forward_plan == plan
assert session.carry_forward_plan is not plan
assert prior["attempt_number"] == 1
assert prior["case_id"] == "PS002"
assert prior["closed_time_min"] == 95
assert prior["adaptation_plan"] == plan
assert session.prior_attempt_summary == prior
assert session.prior_attempt_record["management_trace"]["events"] == [{"decision": 1}]
assert "hidden" not in session.prior_attempt_record
assert session.state == {"case_id": "PS002", "sim_time": 0, "seed": 17}
assert session.management_trace == [] and session.history == []
assert session.events == [{"kind": "presentation", "text": "Repeat presentation", "time": 0}]
assert session.encounter_ended is False and session.encounter_closed_trace is None
assert session.decision_review == {} and session.adaptation_plan == {}
assert session.expert_comparison_unlocked is False
assert session.expert_comparison_responses == {}
assert not any(key.startswith(("decision_review__", "adaptation_plan__", "expert_comparison__")) for key in session)

# Attempt metadata and the prospective carry-forward plan are exported, while
# private state in the prior-attempt summary remains excluded.
payload = namespace["_review_payload"](
    "PS002 · Acute Dyspnea with Shock",
    10,
    [],
    {"case_id": "PS001"},
    [],
    {},
    {},
    {},
    False,
    2,
    plan,
    {**prior, "hidden": {"secret": True}},
)
assert payload["schema"] == "management_reasoning_decision_review_v3"
assert payload["learning_cycle"]["attempt_number"] == 2
assert payload["learning_cycle"]["carry_forward_plan"] == plan
assert "hidden" not in payload["learning_cycle"]["prior_attempt_summary"]
markdown = namespace["_review_markdown"](payload)
assert "**Attempt:** 2" in markdown
assert "## Carry-Forward Plan" in markdown
assert "Pressure–perfusion mismatch." in markdown

print("PASS: v0.8.1 carries the prospective plan into a clean, attempt-aware repeat encounter")
