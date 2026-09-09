"""Regression for the post-cardioversion free-text slot mix-up in v0.8.19."""

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


learner_turn = (
    "Although the rhythm is now sinus, reduced effective circulating volume may "
    "still be contributing to incomplete perfusion recovery. Give 500 mL normal "
    "saline IV. I want to improve preload and tissue perfusion. I expect improved "
    "blood pressure, capillary refill, and extremity temperature without worsening "
    "oxygenation or work of breathing. Reassess HR and rhythm, BP/MAP, capillary "
    "refill, extremities, mental status, SpO2, and work of breathing in 10 minutes."
)
parsed = namespace["clinical_interpreter"](learner_turn)
reasoning = parsed["reasoning"]

assert reasoning["problem_representation"].lower().startswith("although the rhythm is now sinus"), reasoning
assert "reduced effective circulating volume" in reasoning["problem_representation"].lower(), reasoning
assert reasoning["management_priority"].lower() == "improve preload and tissue perfusion", reasoning
assert "improved blood pressure" in reasoning["expected_effect"].lower(), reasoning
assert "capillary refill" in reasoning["expected_effect"].lower(), reasoning
assert reasoning["expected_effect"].lower() != reasoning["management_priority"].lower(), reasoning
assert "work of breathing" in reasoning["reassessment_target"].lower(), reasoning
assert namespace["reasoning_gate_missing"](parsed) == [], parsed

fluid = next(action for action in parsed["actions"] if action["type"] == "fluid")
assert fluid["volume_ml"] == 500, parsed
reassessment = next(action for action in parsed["actions"] if action["type"] == "reassessment")
assert reassessment["delay_min"] == 10, parsed

# A management goal is not also an expected effect unless the learner states a
# prospective outcome separately.
without_expectation = namespace["clinical_interpreter"](
    "I think reduced circulating volume is impairing perfusion. Give 500 mL NS IV. "
    "I want to improve preload and tissue perfusion. Reassess BP and capillary "
    "refill in 10 minutes."
)
assert without_expectation["reasoning"]["management_priority"] == "improve preload and tissue perfusion"
assert "expected_effect" not in without_expectation["reasoning"], without_expectation
assert namespace["reasoning_gate_missing"](without_expectation) == ["expected_effect"]

print("PASS: v0.8.19 separates post-cardioversion model, priority, and expected effect")
