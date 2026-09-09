"""Regression coverage for v0.8.12 natural priority phrasing."""

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
exec(compile(ast.Module(body=nodes, type_ignores=[]), "v0812_subset", "exec"), namespace)


def initialize():
    st.session_state.state = deepcopy(namespace["INITIAL_STATE"])
    st.session_state.events = []
    st.session_state.rng_counter = 0
    st.session_state.pending_action = None
    st.session_state.pending_bundle = None
    st.session_state.pending_reasoning = None
    st.session_state.reasoning_gate_counter = 0
    st.session_state.last_executed_action = None
    st.session_state.management_trace = []


# Literal reproduction of the learner wording in the classroom screenshot.
# The tentative phrase still explicitly states rate control as the priority.
initialize()
learner_turn = namespace["clinical_interpreter"](
    "I think patient is in shock, probably driven by the afib. i would try to "
    "control heart rate. Give diltiazem 5 mg iv, I would expect heart rate to "
    "decrease and better perfusion reassess hr, BP, perfusion in 10 minutes"
)
reasoning = learner_turn["reasoning"]
assert reasoning["management_priority"] == "control heart rate", reasoning
assert "shock" in reasoning["problem_representation"].lower(), reasoning
assert "decrease" in reasoning["expected_effect"].lower(), reasoning
assert reasoning["reassessment_target"].lower() == "hr, bp, perfusion", reasoning
assert namespace["reasoning_gate_missing"](learner_turn) == [], learner_turn
assert [a["type"] for a in learner_turn["actions"]].count("diltiazem") == 1

# The parser should capture equivalent tentative wording without requiring the
# learner to use "my priority is" or "first".
equivalent = namespace["extract_explicit_reasoning"](
    "I would attempt to restore perfusion. Give norepinephrine 0.05 mcg/kg/min."
)
assert equivalent["management_priority"] == "restore perfusion", equivalent

# A medication trial by itself remains an action proposal, not a problem
# priority, which keeps the semantic relaxation bounded.
bounded = namespace["extract_explicit_reasoning"](
    "I would try diltiazem 5 mg IV."
)
assert "management_priority" not in bounded, bounded

print("PASS: v0.8.12 accepts natural tentative priority phrasing")
