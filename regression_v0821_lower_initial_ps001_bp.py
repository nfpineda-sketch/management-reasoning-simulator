"""Regression for the lower, internally coherent PS001 entry pressure."""

import ast
from pathlib import Path


source = Path("app.py").read_text(encoding="utf-8")
tree = ast.parse(source)

assignments = {}
for node in tree.body:
    if not isinstance(node, ast.Assign):
        continue
    for target in node.targets:
        if isinstance(target, ast.Name) and target.id in {"SIMULATOR_VERSION", "INITIAL_STATE", "PRESENTATION"}:
            assignments[target.id] = ast.literal_eval(node.value)

assert assignments["SIMULATOR_VERSION"] in {"0.8.21", "0.9.0-ai-preview", "0.10.0-curriculum-pilot", "0.11.0-curriculum-pilot"}
state = assignments["INITIAL_STATE"]
observable = state["observable"]

assert observable["sbp"] == 90
assert observable["dbp"] == 54
assert round((observable["sbp"] + 2 * observable["dbp"]) / 3) == 66
assert state["hidden"]["effective_map"] == 66.0
assert "BP is 90/54 mmHg" in assignments["PRESENTATION"]

# Preserve the other clinically important entry cues.
assert observable["hr"] == 162
assert observable["rhythm"] == "AF"
assert observable["crt"] == 5
assert observable["extremities"] == "Cool"
assert observable["mental_status"] == "Alert"

print("PASS: v0.8.21 PS001 starts at 90/54 mmHg with matching visible and hidden MAP")
