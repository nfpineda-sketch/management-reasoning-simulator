"""Regression coverage for the v0.7.15 compact autosaving review workflow."""

import ast
from copy import deepcopy
from pathlib import Path


source = Path("app.py").read_text(encoding="utf-8")
assert "dynamic learner-visible ECG with lower-pressure PS001 entry" in source
assert 'st.progress(' in source
assert '"1 · Decision Review"' in source
assert '"2 · Expert Comparison"' in source
assert '"3 · Adaptation Plan"' in source
assert '"4 · Final Summary"' in source
assert 'st.markdown("### Other review points")' in source
assert 'st.expander(f\'{_review_heading(other)} · {status}\'' in source
assert '"Autosave is active when' in source
assert '_render_export_controls(' in source
assert '"top",' in source and '"summary",' in source
assert 'with st.form("decision_review_form")' not in source
assert 'Save Decision Review' not in source
assert 'file_name=f"{case_id}_decision_review_v0819.md"' in source
assert 'file_name=f"{case_id}_decision_review_v0819.json"' in source

tree = ast.parse(source)
selected_functions = {
    "_review_heading",
    "_review_is_complete",
    "_review_widget_key",
    "_adaptation_widget_key",
    "_compact_text",
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
    "_review_progress",
    "_review_missing_items",
    "_compact_review_summary",
    "_sync_compact_review_state",
}
selected_constants = {"REVIEW_RESPONSE_FIELDS", "ADAPTATION_PLAN_FIELDS", "EXPERT_COMPARISON_FIELDS"}
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


namespace = {"st": FakeSt()}
exec(compile(ast.Module(body=nodes, type_ignores=[]), "v0715_subset", "exec"), namespace)

prompts = [
    {"review_id": "decision-2", "kind": "decision", "decision": 2, "time": "00:15", "label": "Alignment"},
    {"review_id": "decision-9", "kind": "decision", "decision": 9, "time": "01:20", "label": "Adaptation"},
    {"review_id": "decision-11", "kind": "decision", "decision": 11, "time": "01:35", "label": "Expected response"},
]
responses = {
    "decision-2": {
        "working_model_update": "Shock persisted despite a modest pressure response.",
        "priority_trigger": "CRT remained 4 seconds with lactate 4.7 mmol/L.",
        "alternative_action": "Prepare norepinephrine before positive pressure.",
        "expected_response_reassessment": "I expect better perfusion. I would reassess BP and CRT in 5 minutes.",
    },
    "decision-9": {
        "working_model_update": "Pressure and tissue flow were dissociated.",
        "priority_trigger": "P/F 125 and rising lactate despite an acceptable MAP.",
        "alternative_action": "",
        "expected_response_reassessment": "",
    },
    "decision-11": {
        "working_model_update": "The combined intervention did not restore forward flow.",
        "priority_trigger": "CRT remained 8 seconds and lactate rose to 6.7 mmol/L.",
        "alternative_action": "Repeat focused POCUS and change one support variable at a time.",
        "expected_response_reassessment": "I expect improved peripheral perfusion. I would reassess BP, CRT, SpO2, and lactate in 5–10 minutes.",
    },
}

suggestions = namespace["_suggest_adaptation_plan"](prompts, responses)
assert suggestions["cue"].startswith("CRT remained 8 seconds")
assert suggestions["threshold"].startswith("Change course if ")
assert suggestions["next_priority"] == ""
assert suggestions["alternative_action"].startswith("Repeat focused POCUS")
assert suggestions["expected_effect"] == "I expect improved peripheral perfusion."
assert suggestions["reassessment_plan"].startswith("I would reassess BP")

merged = namespace["_merge_adaptation_suggestions"](
    {"alternative_action": "Learner-authored action"},
    {"alternative_action": True},
    suggestions,
)
assert merged["alternative_action"] == "Learner-authored action"
assert merged["cue"] == suggestions["cue"]
assert merged["next_priority"] == ""

progress = namespace["_review_progress"](prompts, responses, merged)
assert progress["decisions_complete"] == 2
assert progress["decisions_total"] == 3
assert progress["review_fields_filled"] == 10
assert progress["plan_fields_filled"] == 5
assert progress["filled_fields"] == 15 and progress["total_fields"] == 18
assert 0.83 < progress["fraction"] < 0.84

missing = namespace["_review_missing_items"](prompts, responses, merged)
assert any("Decision 9" in item and "alternative action" in item.lower() for item in missing)
assert any("Next management priority" in item for item in missing)
summary = namespace["_compact_review_summary"](prompts, responses)
assert [item["complete"] for item in summary] == [True, False, True]
assert summary[1]["heading"] == "01:20 · Decision 9"

# Exercise the autosave path itself. Widget values are copied into the durable
# review object, plan suggestions are generated, and learner-edited plan text is
# protected from later suggestion refreshes.
session = namespace["st"].session_state
session.decision_review = {}
session.adaptation_plan = {}
session.adaptation_plan_user_edited = {}
session.review_autosave_revision = 0
for field, _ in namespace["REVIEW_RESPONSE_FIELDS"]:
    session[namespace["_review_widget_key"]("decision-2", field)] = responses["decision-2"][field]

saved_responses, saved_plan, edited = namespace["_sync_compact_review_state"](prompts[:1])
assert saved_responses["decision-2"]["priority_trigger"].startswith("CRT remained")
assert saved_plan["alternative_action"] == "Prepare norepinephrine before positive pressure."
assert saved_plan["next_priority"] == ""
assert edited == {}
assert session.review_autosave_revision == 1

plan_key = namespace["_adaptation_widget_key"]("alternative_action")
session[plan_key] = "My manually edited action"
saved_responses, saved_plan, edited = namespace["_sync_compact_review_state"](prompts[:1])
assert edited["alternative_action"] is True
assert saved_plan["alternative_action"] == "My manually edited action"

session[namespace["_review_widget_key"]("decision-2", "alternative_action")] = "A newer reflected action"
_, saved_plan, edited = namespace["_sync_compact_review_state"](prompts[:1])
assert saved_plan["alternative_action"] == "My manually edited action"
assert edited["alternative_action"] is True

print("PASS: v0.7.15 compact one-decision flow, autosave, editable plan drafting, progress, summary, and persistent exports")
