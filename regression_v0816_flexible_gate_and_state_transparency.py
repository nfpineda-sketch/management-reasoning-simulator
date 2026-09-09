"""Regression coverage for v0.8.19 flexible capture and state transparency."""

import ast
import math
import random
import re
from copy import deepcopy
from html import escape
from pathlib import Path


source = Path("app.py").read_text(encoding="utf-8")
assert 'SIMULATOR_VERSION = "0.8.21"' in source
assert "MVP v0.8.21 — dynamic learner-visible ECG with lower-pressure PS001 entry" in source
assert "While awaiting diagnostic results over" in source
assert '"procedural_sedation"' in source

tree = ast.parse(source)
nodes = []
state_names = {
    "INITIAL_STATE", "PRESENTATION", "PS002_PRESENTATION", "CASE_CONFIGS",
    "REASONING_GATE_ACTION_TYPES", "REASONING_GATE_FIELD_LABELS",
    "REASONING_GATE_FIELD_STEMS", "REASONING_GATE_OVERRIDE",
}
for node in tree.body:
    if isinstance(node, ast.FunctionDef):
        nodes.append(node)
    elif isinstance(node, ast.Assign):
        names = [target.id for target in node.targets if isinstance(target, ast.Name)]
        if any(name in state_names for name in names):
            nodes.append(node)


class SessionState(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__


class FakeStreamlit:
    def __init__(self):
        self.session_state = SessionState()


st = FakeStreamlit()
namespace = {
    "st": st,
    "re": re,
    "math": math,
    "random": random,
    "deepcopy": deepcopy,
    "escape": escape,
}
exec(compile(ast.Module(body=nodes, type_ignores=[]), "v0818_subset", "exec"), namespace)


st.session_state.state = deepcopy(namespace["INITIAL_STATE"])
st.session_state.events = []
st.session_state.rng_counter = 0
st.session_state.pending_action = None
st.session_state.pending_bundle = None
st.session_state.pending_reasoning = None
st.session_state.reasoning_gate_counter = 0
st.session_state.last_executed_action = None
st.session_state.management_trace = []


# Literal classroom input: compact findings and the intended physiologic effect
# should populate all semantic fields except the genuinely omitted time.
literal = (
    "Patient hypotensive, slow perfusion, tachycardia, neurologic dysfunction. "
    "urianalysis positive for infection. give 2000 cc NS, reassess perfusion, hr, bp. "
    "I expect pressure to increase, decrease hr and improving perfusion"
)
parsed = namespace["clinical_interpreter"](literal)
fluid = next(action for action in parsed["actions"] if action["type"] == "fluid")
assert fluid["volume_ml"] == 2000, parsed
reasoning = parsed["reasoning"]
assert "hypotensive" in reasoning["problem_representation"].lower(), reasoning
assert "urinalysis positive for infection" in reasoning["problem_representation"].lower(), reasoning
assert reasoning["management_priority"] == "improve arterial pressure and tissue perfusion", reasoning
assert "pressure to increase" in reasoning["expected_effect"].lower(), reasoning
assert all(token in reasoning["reassessment_target"].lower() for token in ("perfusion", "hr", "bp")), reasoning
assert namespace["reasoning_gate_missing"](parsed) == ["reassessment_timing"], parsed

timed = namespace["clinical_interpreter"](literal + " in 5 minutes")
assert namespace["reasoning_gate_missing"](timed) == [], timed

# Relaxation remains bounded: an order alone must not manufacture reasoning.
treatment_only = namespace["clinical_interpreter"]("Give 2000 cc NS.")
assert namespace["reasoning_gate_missing"](treatment_only) == [
    "working_model", "management_priority", "expected_effect",
    "reassessment_target", "reassessment_timing",
], treatment_only

# A mismatch with current data is a neutral observation and never a gate item.
current = {"observable": {"hr": 96, "rhythm": "Sinus rhythm"}}
notes = namespace["reasoning_state_observations"](parsed, current)
assert notes and "current HR is 96/min" in notes[0], notes
assert "does not block" in notes[0], notes
assert namespace["reasoning_gate_missing"](parsed) == ["reassessment_timing"]
assert namespace["reasoning_state_observations"](
    parsed, {"observable": {"hr": 110, "rhythm": "Sinus rhythm"}}
) == []

before = {"observable": {"sbp": 113, "crt": 2, "mental_status": "Alert"}}
after = {"observable": {"sbp": 97, "crt": 5, "mental_status": "Alert"}}
assert namespace["observable_state_changed"](before, after) is True
assert namespace["observable_state_changed"](before, deepcopy(before)) is False

# v0.8.15 procedural sedation remains executable and precedes cardioversion.
sedation = namespace["clinical_interpreter"](
    "Perform synchronized cardioversion at 200 J with etomidate 8 mg IV and "
    "midazolam 2 mg IV for procedural sedation. I think AF with RVR impairs "
    "filling and perfusion. My priority is to restore sinus rhythm. I expect "
    "conversion with improved perfusion. Reassess rhythm, HR, BP and perfusion "
    "in 10 minutes."
)
types = [action["type"] for action in sedation["actions"]]
assert types[:2] == ["procedural_sedation", "cardioversion"], sedation
medications = sedation["actions"][0]["medications"]
assert [(med["agent"], med["dose"]) for med in medications] == [
    ("etomidate", 8.0), ("midazolam", 2.0)
]
assert namespace["reasoning_gate_missing"](sedation) == [], sedation

print("PASS: v0.8.19 flexibly fills reasoning fields, preserves sedation, and exposes non-blocking state checks")
