"""Regression for explicit reassessment timing after a large crystalloid order."""

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


def execute(text):
    parsed = namespace["clinical_interpreter"](text)
    result = namespace["execute_bundle"](parsed)
    assert result.get("executed") is True, (text, parsed, result)
    return parsed, result


initialize()

# Reproduce the reported trajectory up to the late shock state.
execute(
    "Perform synchronized cardioversion at 200 J with etomidate 8 mg IV and "
    "midazolam 2 mg IV for procedural sedation. I think AF with RVR is impairing "
    "cardiac filling and tissue perfusion. I want to restore an effective rhythm "
    "and improve forward flow. I expect conversion to sinus rhythm, a lower heart "
    "rate, and improved capillary refill without hypotension. Reassess rhythm, HR, "
    "BP/MAP, capillary refill, extremities, mental status, SpO2, and work of "
    "breathing in 10 minutes."
)
execute(
    "Although the rhythm is now sinus, reduced effective circulating volume may "
    "still be contributing to incomplete perfusion recovery. Give 500 mL normal "
    "saline IV. I want to improve preload and tissue perfusion. I expect improved "
    "blood pressure, capillary refill, and extremity temperature without worsening "
    "oxygenation or work of breathing. Reassess HR and rhythm, BP/MAP, capillary "
    "refill, extremities, mental status, SpO2, and work of breathing in 10 minutes."
)
execute("Obtain POCUS now to assess LV and RV function, IVC, pericardium, and lung B-lines.")
execute("Obtain basic laboratory tests and lactate now.")
execute("Obtain urinalysis and chest X-ray now.")
execute("Reassess BP/MAP, HR and rhythm, capillary refill, extremities, mental status, SpO2, and work of breathing in 10 minutes.")

assert st.session_state.state["sim_time"] == 50, st.session_state.state
pre = deepcopy(st.session_state.state["observable"])

parsed, result = execute(
    "Patient hypotensive with slow perfusion and neurologic dysfunction; urianalysis "
    "positive for infection. Give 2000 cc NS. I want to improve arterial pressure "
    "and tissue perfusion. I expect pressure to increase and perfusion to improve. "
    "Reassess perfusion, HR, and BP in 5 minutes."
)

fluid = next(action for action in parsed["actions"] if action["type"] == "fluid")
assert fluid["volume_ml"] == 2000, parsed
assert result["elapsed_min"] == 5, result
assert st.session_state.state["sim_time"] == 55, st.session_state.state

post = st.session_state.state["observable"]
assert post["sbp"] >= pre["sbp"], (pre, post)
pre_map = (pre["sbp"] + 2 * pre["dbp"]) / 3.0
post_map = (post["sbp"] + 2 * post["dbp"]) / 3.0
assert post_map >= pre_map, (pre, post)
assert post["crt"] <= pre["crt"], (pre, post)
assert post["mental_status"] != "Unresponsive", (pre, post)
assert st.session_state.state["treatments"]["cumulative_crystalloid_ml"] == 2500

# Diagnostic processing remains a lower bound when results and reassessment are
# requested together: a 10-minute basic panel cannot be returned at minute 5.
initialize()
_, diagnostic_result = execute(
    "Obtain basic laboratory tests and reassess BP and perfusion in 5 minutes."
)
assert diagnostic_result["elapsed_min"] == 10, diagnostic_result

print("PASS: v0.8.19 respects treatment reassessment checkpoints and preserves diagnostic delays")
