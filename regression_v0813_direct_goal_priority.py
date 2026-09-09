"""Regression coverage for v0.8.13 direct therapeutic-goal priorities."""

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
exec(compile(ast.Module(body=nodes, type_ignores=[]), "v0813_subset", "exec"), namespace)


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


# Literal reproduction of the learner wording in the second classroom
# screenshot. The clinical target is the priority; the drug remains the action.
initialize()
learner_turn = namespace["clinical_interpreter"](
    "I think patient is in shock due to afib. I want to control heart rate with "
    "diltiazem 5 mg iv. I expect decrease in heart rate and improve in clinical "
    "perfusion. reassess hr, bp, perfussion in 10 minutes"
)
reasoning = learner_turn["reasoning"]
assert reasoning["management_priority"] == "control heart rate", reasoning
assert "diltiazem" not in reasoning["management_priority"].lower(), reasoning
assert "shock" in reasoning["problem_representation"].lower(), reasoning
assert "decrease" in reasoning["expected_effect"].lower(), reasoning
assert "hr" in reasoning["reassessment_target"].lower(), reasoning
assert namespace["reasoning_gate_missing"](learner_turn) == [], learner_turn
assert [a["type"] for a in learner_turn["actions"]].count("diltiazem") == 1

# Equivalent direct goals are accepted while a medication proposal alone still
# cannot satisfy the management-priority field.
for phrase, expected in [
    ("I plan to restore perfusion with norepinephrine.", "restore perfusion"),
    ("I intend to treat AF with diltiazem.", "treat AF"),
    ("I will slow the ventricular rate with metoprolol.", "slow the ventricular rate"),
]:
    parsed = namespace["extract_explicit_reasoning"](phrase)
    assert parsed.get("management_priority") == expected, (phrase, parsed)

bounded = namespace["extract_explicit_reasoning"]("I want to give diltiazem 5 mg IV.")
assert "management_priority" not in bounded, bounded

print("PASS: v0.8.13 accepts direct therapeutic goals as priorities")
