"""Regression coverage for v0.8.3 action intent and PS001 trigger disclosure."""

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
exec(compile(ast.Module(body=nodes, type_ignores=[]), "v083_subset", "exec"), namespace)


def initialize():
    st.session_state.state = deepcopy(namespace["INITIAL_STATE"])
    st.session_state.rng_counter = 0
    st.session_state.pending_action = None
    st.session_state.pending_bundle = None
    st.session_state.last_executed_action = None
    st.session_state.management_trace = []


initialize()
entry_1 = (
    "My working model is AF with RVR and impaired peripheral perfusion, but the rhythm may be "
    "secondary to an acute illness rather than the sole cause of instability. My priority is to "
    "assess the hemodynamic phenotype and reversible causes before committing to rate control or "
    "cardioversion. Give 500 mL normal saline, obtain POCUS, lactate, VBG, basic labs, and ask about "
    "fever and urinary symptoms. Reassess BP, HR and rhythm, capillary refill, extremities, mental "
    "status, SpO2, work of breathing, and lung findings in 5 minutes."
)
parsed = namespace["clinical_interpreter"](entry_1)
action_types = [action["type"] for action in parsed["actions"]]
assert "cardioversion" not in action_types, parsed
assert {"fluid", "pocus", "lactate", "vbg", "basic_labs", "focused_history", "reassessment"} <= set(action_types), parsed

before = namespace["management_state_snapshot"](st.session_state.state)
result = namespace["execute_bundle"](parsed)
after = namespace["management_state_snapshot"](st.session_state.state)
namespace["record_management_trace"](entry_1, parsed, result, before, after)
assert result.get("clarification") is None, result
assert st.session_state.state["treatments"]["cardioversions"] == 0
assert st.session_state.state["observable"]["rhythm"] == "AF"
assert "dysuria" in st.session_state.state["diagnostics"]["focused_history"]["history"].lower()
assert "urinary frequency" in st.session_state.state["diagnostics"]["focused_history"]["history"].lower()

# Discussion, deferral, preparation, and retrospective wording remain non-actions.
non_orders = (
    "Before committing to cardioversion, I want more information.",
    "Consider cardioversion if the patient deteriorates.",
    "Defer cardioversion and reassess in 5 minutes.",
    "Prepare for cardioversion while evaluating the cause.",
    "After synchronized cardioversion, reassess perfusion.",
)
for text in non_orders:
    assert not namespace["is_explicit_cardioversion_order"](text), text

# Direct and compact orders remain executable.
orders = (
    "Cardiovert 200 J and reassess.",
    "I want to cardiovert 200 J.",
    "Perform synchronized cardioversion with 200 J.",
    "Synchronized cardioversion 200 J.",
)
for text in orders:
    assert namespace["is_explicit_cardioversion_order"](text), text

urine = namespace["urinalysis_transition"](deepcopy(namespace["INITIAL_STATE"]))
assert "positive nitrite" in urine["result"]["finding"].lower()
assert "urinary source" in urine["result"]["finding"].lower()

print("PASS: v0.8.3 defers discussed cardioversion and reveals the PS001 urinary trigger")
