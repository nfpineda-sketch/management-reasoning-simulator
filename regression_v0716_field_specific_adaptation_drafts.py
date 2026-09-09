"""Regression for v0.7.16 field-specific Adaptation Plan drafting."""

import ast
from pathlib import Path


source = Path("app.py").read_text(encoding="utf-8")
assert 'SIMULATOR_VERSION = "0.8.21"' in source
assert "MVP v0.8.21 — dynamic learner-visible ECG with lower-pressure PS001 entry" in source
assert 'file_name=f"{case_id}_decision_review_v0819.md"' in source
assert 'file_name=f"{case_id}_decision_review_v0819.json"' in source

tree = ast.parse(source)
selected_functions = {
    "_latest_review_response",
    "_normalize_review_text",
    "_first_review_sentence",
    "_ensure_terminal_punctuation",
    "_clean_reasoning_phrase",
    "_cue_from_priority_trigger",
    "_threshold_from_priority_trigger",
    "_split_expected_reassessment",
    "_suggest_adaptation_plan",
}
nodes = []
for node in tree.body:
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        if not any(alias.name == "streamlit" for alias in node.names):
            nodes.append(node)
    elif isinstance(node, ast.FunctionDef) and node.name in selected_functions:
        nodes.append(node)

namespace = {}
exec(compile(ast.Module(body=nodes, type_ignores=[]), "v0716_subset", "exec"), namespace)

prompts = [
    {"review_id": "decision-2", "decision": 2},
    {"review_id": "decision-9", "decision": 9},
    {"review_id": "decision-11", "decision": 11},
]

# Reproduce the real pasted text that exposed the bug: the next answer begins
# immediately after the trigger sentence, without a separating space.
joined_trigger = (
    "No improvement in capillary refill and an increase in lactate from 5.6 to 6.7 mmol/L, "
    "accompanied by falling blood pressure and SpO2, should trigger immediate reassessment "
    "rather than automatic further escalation of norepinephrine or dobutamine."
    "Immediately reassess the hemodynamic phenotype, verify treatment delivery and measurements."
)
responses = {
    "decision-11": {
        "priority_trigger": joined_trigger,
        "alternative_action": (
            "Immediately reassess the hemodynamic phenotype, verify treatment delivery and measurements, "
            "repeat focused cardiac and lung ultrasound, and reconsider the differential diagnosis. "
            "I would adjust one support variable at a time using predefined response and stopping thresholds."
        ),
        "expected_response_reassessment": (
            "I would expect improved peripheral perfusion and lactate without loss of blood pressure or oxygenation."
            "I would reassess BP, MAP, capillary refill, extremities, SpO2, cardiac function, and ventilator "
            "interaction within 5 minutes."
        ),
    }
}

suggestions = namespace["_suggest_adaptation_plan"](prompts, responses)

assert suggestions["cue"] == (
    "No improvement in capillary refill and an increase in lactate from 5.6 to 6.7 mmol/L, "
    "accompanied by falling blood pressure and SpO2."
)
assert suggestions["threshold"].endswith("further escalation of norepinephrine or dobutamine.")
assert suggestions["threshold"].startswith("No improvement in capillary refill")
assert "Immediately reassess the hemodynamic phenotype" not in suggestions["cue"]
assert "Immediately reassess the hemodynamic phenotype" not in suggestions["threshold"]
assert suggestions["next_priority"] == ""
assert suggestions["alternative_action"].startswith("Immediately reassess the hemodynamic phenotype")
assert suggestions["expected_effect"].endswith("oxygenation.")
assert suggestions["reassessment_plan"].startswith("I would reassess BP, MAP")

# The two semantic fields must no longer be duplicates.
assert suggestions["cue"] != suggestions["threshold"]

print("PASS: v0.7.16 separates cue, change threshold, alternative action, expected effect, and reassessment")
