"""Regression coverage for v0.8.8 fluid-volume and oxygen-flow scoping."""

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
for node in tree.body:
    if isinstance(node, ast.FunctionDef):
        nodes.append(node)
    elif isinstance(node, ast.Assign):
        names = [target.id for target in node.targets if isinstance(target, ast.Name)]
        if any(name in {"INITIAL_STATE", "PRESENTATION", "PS002_PRESENTATION", "CASE_CONFIGS"} for name in names):
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
exec(compile(ast.Module(body=nodes, type_ignores=[]), "v088_subset", "exec"), namespace)


def initialize():
    st.session_state.state = deepcopy(namespace["INITIAL_STATE"])
    st.session_state.rng_counter = 0
    st.session_state.pending_action = None
    st.session_state.pending_bundle = None
    st.session_state.last_executed_action = None
    st.session_state.management_trace = []


# Literal learner input that exposed the defect: the fluid parser must bind 1000
# to NS and leave 3lt to oxygen, including the learner's device spelling.
entry = "give 1000 NS iv POCUS, lactate, VBG initiate O2 3lt nassal canula reassess in 10 minutes"
initialize()
parsed = namespace["clinical_interpreter"](entry)
actions = {action["type"]: action for action in parsed["actions"]}

assert actions["fluid"]["volume_ml"] == 1000, actions
assert actions["fluid"]["fluid_type"] == "Normal saline", actions
assert actions["oxygen"]["device"] == "Nasal cannula", actions
assert actions["oxygen"]["flow_lpm"] == 3.0, actions
assert {"pocus", "lactate", "vbg", "reassessment"} <= set(actions), actions
assert actions["reassessment"]["delay_min"] == 10, actions

result = namespace["execute_bundle"](parsed)
assert result.get("clarification") is None, result
assert result.get("executed") is True, result

fluid_summaries = [s for s in result["action_summaries"] if "volume_ml" in s]
oxygen_summaries = [s for s in result["action_summaries"] if s.get("support_type") == "oxygen"]
assert len(fluid_summaries) == 1 and fluid_summaries[0]["volume_ml"] == 1000, result
assert len(oxygen_summaries) == 1 and oxygen_summaries[0]["flow_lpm"] == 3.0, result
assert st.session_state.state["treatments"]["cumulative_crystalloid_ml"] == 1000
assert st.session_state.state["sim_time"] == 10

# Named-fluid quantities win regardless of order or unit spelling.
volume_cases = {
    "give 1000 NS IV and oxygen 3lt nasal cannula": 1000,
    "give NS 1000 IV and oxygen 3 L nasal cannula": 1000,
    "give 1 L NS and oxygen 3 L/min": 1000,
    "give one liter normal saline and oxygen 3 L": 1000,
    "give 1 L IV and start O2 3 L": 1000,
    "bolus 1 L, then start oxygen 3 L": 1000,
    "O2 3 L, give 1 L": 1000,
}
for order, expected in volume_cases.items():
    assert namespace["parse_volume_ml"](order) == expected, order

# An oxygen flow can never silently supply a missing crystalloid volume.
oxygen_only_cases = (
    "Give NS IV and start O2 3lt nasal cannula",
    "Start oxygen 3 L nasal cannula",
    "Apply nasal cannula 4 litres",
)
for order in oxygen_only_cases:
    assert namespace["parse_volume_ml"](order) is None, order

missing_volume = namespace["clinical_interpreter"](oxygen_only_cases[0])
initialize()
clarification = namespace["execute_bundle"](missing_volume)
assert clarification.get("clarification") == "How much fluid would you like to give?", clarification
assert st.session_state.state["treatments"]["cumulative_crystalloid_ml"] == 0

print("PASS: v0.8.8 keeps IV fluid volume separate from oxygen flow in compound orders")
