"""Regression coverage for v0.8.9 prospective reasoning and action transparency."""

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
assert "_decision_review_v0819.pdf" in source
assert "_decision_review_v0819.md" in source
assert "_decision_review_v0819.json" in source
assert "ORDER HELD — REASONING REQUIRED" in source
assert "Recognized but not executed in this build" in source

tree = ast.parse(source)
nodes = []
state_names = {
    "INITIAL_STATE", "PRESENTATION", "PS002_PRESENTATION", "CASE_CONFIGS",
    "REASONING_GATE_ACTION_TYPES", "REASONING_GATE_FIELD_LABELS",
    "REASONING_GATE_OVERRIDE",
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
exec(compile(ast.Module(body=nodes, type_ignores=[]), "v089_subset", "exec"), namespace)


def initialize():
    st.session_state.state = deepcopy(namespace["INITIAL_STATE"])
    st.session_state.rng_counter = 0
    st.session_state.pending_action = None
    st.session_state.pending_bundle = None
    st.session_state.pending_reasoning = None
    st.session_state.last_executed_action = None
    st.session_state.management_trace = []


# The literal retrospective POCUS phrase that exposed the scoping defect must
# remain clinical evidence. It must not execute a new ultrasound.
retrospective = (
    "give 1000 NS, give ceftriaxone 2 gr, send cultures i would add CBC, RCP, "
    "urine analysis, chest x-ray Patient still tachycardic, POCUS shows that "
    "patient still tolerate more volumen. reassess in 15 min"
)
initialize()
parsed = namespace["clinical_interpreter"](retrospective)
types = [action["type"] for action in parsed["actions"]]
assert "pocus" not in types, types
assert {"fluid", "antibiotics", "blood_cultures", "basic_labs", "urinalysis", "chest_xray", "reassessment"} <= set(types), types

# Direct diagnostic language remains executable.
direct_pocus = namespace["clinical_interpreter"](
    "Repeat POCUS and lactate, then reassess BP and capillary refill in 10 minutes."
)
assert {"pocus", "lactate", "reassessment"} <= {
    action["type"] for action in direct_pocus["actions"]
}

# Executable procedural sedation and unsupported analgesia are both transparent.
sedation = namespace["clinical_interpreter"](
    "Perform synchronized cardioversion 200 J, sedation with etomidate 8 mg + "
    "midazolam 2 mg, and reassess rhythm in 5 minutes."
)
assert sedation["recognized_future_actions"] == [], sedation
sedation_actions = [
    action for action in sedation["actions"] if action["type"] == "procedural_sedation"
]
assert len(sedation_actions) == 1, sedation
assert [medication["agent"] for medication in sedation_actions[0]["medications"]] == [
    "etomidate", "midazolam"
], sedation

analgesia = namespace["clinical_interpreter"](
    "Give fentanyl 50 mcg for analgesia, 1000 cc NS, and reassess in 10 minutes."
)
assert analgesia["recognized_future_actions"] == ["fentanyl 50 mcg for analgesia"], analgesia

# A treatment-only order contains no invented reasoning and is held without any
# physiology or simulation-time change.
initialize()
treatment_only = namespace["clinical_interpreter"]("Give diltiazem 5 mg IV.")
assert treatment_only["reasoning"] == {}, treatment_only
assert namespace["reasoning_gate_missing"](treatment_only) == [
    "working_model", "management_priority", "expected_effect",
    "reassessment_target", "reassessment_timing",
]
before = deepcopy(st.session_state.state)
prompt = namespace["hold_pending_reasoning"](treatment_only)
assert st.session_state.state == before
assert "diltiazem 5 mg IV" in prompt
assert "patient state has not changed" in prompt

# The learner can supply only the missing reasoning. The original order remains
# pending, and execution occurs exactly once after all four requirements exist.
resolved = namespace["resolve_pending_reasoning"](
    "My working model is AF with RVR impairing cardiac filling. "
    "My priority is cautious rate control while preserving perfusion. "
    "I expect this to reduce heart rate without hypotension. "
    "Reassess HR and rhythm, BP, capillary refill, and mental status in 5 minutes."
)
assert resolved.get("parsed"), resolved
completed = resolved["parsed"]
assert namespace["reasoning_gate_missing"](completed) == []
assert [a["type"] for a in completed["actions"]].count("diltiazem") == 1
assert st.session_state.state == before
result = namespace["execute_bundle"](completed)
assert result.get("executed") is True, result
assert st.session_state.state["sim_time"] == 5

# Diagnostic-only and reassessment-only turns remain available without the gate.
initialize()
diagnostics_only = namespace["clinical_interpreter"](
    "Obtain POCUS, lactate, and VBG and reassess in 10 minutes."
)
assert namespace["reasoning_gate_missing"](diagnostics_only) == []
reassessment_only = namespace["clinical_interpreter"](
    "Reassess BP, HR, capillary refill, and mental status in 5 minutes."
)
assert namespace["reasoning_gate_missing"](reassessment_only) == []

# The explicit faculty override releases the held order and is auditable.
initialize()
override_order = namespace["clinical_interpreter"]("Give 500 mL normal saline.")
namespace["hold_pending_reasoning"](override_order)
override = namespace["resolve_pending_reasoning"]("execute without complete reasoning")
assert override.get("overridden") is True, override
assert override["parsed"]["reasoning_gate"]["status"] == "overridden"
assert st.session_state.pending_reasoning is None
assert st.session_state.state["treatments"]["cumulative_crystalloid_ml"] == 0

print("PASS: v0.8.9 prospective reasoning gate, retrospective diagnostics, and unsupported-action transparency")
