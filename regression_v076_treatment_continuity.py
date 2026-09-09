import ast
import math
import random
import re
from copy import deepcopy
from pathlib import Path


source = Path("app.py").read_text()
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
namespace = {"st": st, "re": re, "math": math, "random": random, "deepcopy": deepcopy}
exec(compile(ast.Module(body=nodes, type_ignores=[]), "v076_subset", "exec"), namespace)


def initialize(case_id="PS001"):
    st.session_state.state = (
        namespace["build_ps002_state"]()
        if case_id == "PS002"
        else deepcopy(namespace["INITIAL_STATE"])
    )
    st.session_state.rng_counter = 0
    st.session_state.pending_action = None
    st.session_state.pending_bundle = None
    st.session_state.last_executed_action = None
    st.session_state.management_trace = []


def execute(text, allow_clarification=False):
    parsed = namespace["clinical_interpreter"](text)
    before = namespace["management_state_snapshot"](st.session_state.state)
    result = namespace["execute_bundle"](parsed)
    after = namespace["management_state_snapshot"](st.session_state.state)
    event = namespace["record_management_trace"](text, parsed, result, before, after)
    if not allow_clarification:
        assert result.get("clarification") is None, result
    return parsed, result, event


# An active norepinephrine infusion is inherited by "continue" without a new
# action, dose clarification, unit conversion, or clock cost.
initialize("PS001")
execute("Start norepinephrine 0.1 mcg/kg/min and reassess perfusion in 5 minutes")
tr = st.session_state.state["treatments"]
assert tr["norepinephrine"] and tr["norepinephrine_rate"] == 0.1
assert tr["norepinephrine_units"] == "mcg/kg/min"

p2, r2, e2 = execute(
    "Proceed with intubation, continue norepinephrine, and start VC/AC ventilation "
    "with FiO2 100% and PEEP 10 cm H2O. Reassess oxygenation and perfusion in 10 minutes."
)
assert [a["type"] for a in p2["actions"]] == ["intubation", "reassessment"], p2
assert not any(a["type"] == "norepinephrine" for a in p2["actions"]), p2
assert r2.get("clarification") is None, r2
assert st.session_state.state["treatments"]["norepinephrine_rate"] == 0.1
assert st.session_state.state["treatments"]["norepinephrine_units"] == "mcg/kg/min"
assert "norepinephrine" not in namespace["_trace_action_text"](e2).lower()
assert e2["state_after"]["treatments"]["norepinephrine"]

p3, r3, e3 = execute(
    "Perform synchronized cardioversion with 200 J biphasic while continuing the "
    "current norepinephrine infusion. Reassess rhythm and perfusion immediately."
)
assert [a["type"] for a in p3["actions"]] == ["cardioversion", "reassessment"], p3
assert r3.get("clarification") is None, r3
assert namespace["_trace_action_text"](e3) == "synchronized cardioversion 200 J"
assert st.session_state.state["treatments"]["norepinephrine_rate"] == 0.1

# A genuinely different stated rate remains an executable titration.
p4, r4, _ = execute("Continue norepinephrine at 0.2 mcg/kg/min and reassess in 5 minutes")
norepi = next(a for a in p4["actions"] if a["type"] == "norepinephrine")
assert norepi["operation"] == "titrate" and norepi["rate"] == 0.2, norepi
assert r4.get("clarification") is None, r4
assert st.session_state.state["treatments"]["norepinephrine_rate"] == 0.2

# Without an active infusion, "continue" cannot invent a dose.
initialize("PS001")
_, inactive_result, _ = execute("Continue norepinephrine and reassess in 5 minutes", allow_clarification=True)
assert inactive_result.get("clarification"), inactive_result

# The reported PS002 claim now produces a non-scoring alignment prompt using
# only observations and diagnostics available at that decision point.
initialize("PS002")
execute(
    "start with 1500 cc NS, oxygen nasal canula 4L, do a POCUS, lactate, VBG, lab tests. "
    "reassess in 15 minutes"
)
execute(
    "better hemodynamic status, not shocked anymore, but despite oxygen, clearly with persistent "
    "respiratory distress. Start BiPAP 18/6 O2 100% reassess in 10 minutes"
)
items = namespace["_reflect_compare_items"](st.session_state.management_trace)
alignment = [item for item in items if item[1] == 2 and item[3] == "Stated interpretation vs available data"]
assert alignment, items
alignment_text = alignment[0][4]
assert "not shocked anymore" in alignment_text.lower(), alignment_text
assert "capillary refill 4 seconds" in alignment_text, alignment_text
assert "lactate 4.7 mmol/L" in alignment_text, alignment_text

# Unsupported respiratory and mental-status claims are also contrasted with the
# preceding visible response, while a supported PS002 claim is left alone.
previous = {
    "state_before": {"observable": {"mental_status": "Alert"}},
    "state_after": {"observable": {"mental_status": "Alert"}},
}
event = {
    "learner_input": (
        "Norepinephrine improved mental status, but refractory hypoxemic respiratory failure persists."
    ),
    "reasoning": {},
    "state_before": {
        "observable": {
            "sbp": 121, "dbp": 82, "hr": 174, "crt": 5,
            "mental_status": "Alert", "spo2": 99,
            "respiratory_rate": 22, "work_of_breathing": "Mildly increased",
        },
        "diagnostics": {},
    },
}
prompt = namespace["_reasoning_data_alignment_prompt"](event, previous)
assert prompt and prompt[0] == "Stated interpretation vs available data", prompt
assert "mental status was alert before and alert after" in prompt[1], prompt
assert "SpO₂ 99%" in prompt[1] and "respiratory rate 22/min" in prompt[1], prompt

supported = deepcopy(event)
supported["learner_input"] = "Persistent hypoxemic respiratory failure despite BiPAP."
supported["state_before"]["observable"].update({
    "spo2": 88, "respiratory_rate": 36, "work_of_breathing": "Severe",
})
assert namespace["_reasoning_data_alignment_prompt"](supported, previous) is None

print("PASS: v0.7.6 active-treatment continuity and reasoning-data alignment")
