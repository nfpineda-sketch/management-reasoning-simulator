"""Regression coverage for v0.8.10 semantic capture and guided completion."""

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
assert "Equivalent wording is accepted" in source
assert "Complete the sentence starters" in source
assert "My working model is…" in source
assert "My management priority is…" in source
assert "I will reassess these variables…" in source
assert "complete_pending_reasoning_fields" in source
assert "upsert_reasoning_gate_clarification" in source

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
exec(compile(ast.Module(body=nodes, type_ignores=[]), "v0810_subset", "exec"), namespace)


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


# The learner can communicate all four prospective elements without using the
# simulator's exact labels or boilerplate sentence stems.
initialize()
natural = namespace["clinical_interpreter"](
    "I think AFib is the primary problem and is causing poor forward flow, so if "
    "we control heart rate, the patient should feel better. Give diltiazem 5 mg IV. "
    "Reassess HR, rhythm, perfusion, and blood pressure in 10 minutes."
)
assert natural["reasoning"]["problem_representation"]
assert natural["reasoning"]["management_priority"]
assert natural["reasoning"]["expected_effect"] == "feel better"
assert natural["reasoning"]["reassessment_target"]
assert namespace["reasoning_gate_missing"](natural) == [], natural

# Dictation punctuation and direct "addressing first" language are interpreted
# semantically when supplied as a follow-up to a held order.
initialize()
treatment_only = namespace["clinical_interpreter"]("Give diltiazem 5 mg IV.")
before = deepcopy(st.session_state.state)
namespace["hold_pending_reasoning"](treatment_only)
resolved = namespace["resolve_pending_reasoning"](
    "I.m addressing heart rate first. I think AF is contributing to poor perfusion. "
    "With diltiazem I expect a moderate decrease in heart rate. "
    "Reassess HR, perfusion, and blood pressure in 10 minutes."
)
assert resolved.get("parsed"), resolved
completed = resolved["parsed"]
assert completed["reasoning"]["management_priority"] == "heart rate"
assert namespace["reasoning_gate_missing"](completed) == []
assert [a["type"] for a in completed["actions"]].count("diltiazem") == 1
assert st.session_state.state == before

# A vague "reassess patient" keeps only the genuinely missing item open; the
# other natural statements should not be rejected for lacking exact labels.
initialize()
partly_specific = namespace["clinical_interpreter"](
    "I think AFib is the primary problem. If we control heart rate, the patient "
    "should improve. Give diltiazem 5 mg IV and reassess the patient in 10 minutes."
)
assert namespace["reasoning_gate_missing"](partly_specific) == ["reassessment_target"]

# Repeated incomplete attempts replace the gate prompt instead of accumulating
# duplicate clarification blocks.
initialize()
namespace["hold_pending_reasoning"](treatment_only)
namespace["upsert_reasoning_gate_clarification"](
    treatment_only,
    namespace["reasoning_gate_missing"](treatment_only),
)
partial = namespace["resolve_pending_reasoning"](
    "I think AF is contributing to impaired perfusion."
)
assert partial.get("clarification"), partial
active = st.session_state.pending_reasoning
namespace["upsert_reasoning_gate_clarification"](
    active["parsed"], partial["missing"]
)
gate_events = [
    event for event in st.session_state.events
    if "ORDER HELD — REASONING REQUIRED" in event.get("text", "")
]
assert len(gate_events) == 1, gate_events

# The structured fallback writes the learner's own completions directly into
# the held order, retains one treatment action, and still does not change the
# patient until normal bundle execution occurs.
guided = namespace["complete_pending_reasoning_fields"](
    "AF with RVR is contributing to impaired forward flow",
    "test cautious rate control while protecting perfusion",
    "a moderate heart-rate reduction without hypotension",
    "HR and rhythm, BP/MAP, capillary refill, and mental status",
    5,
)
assert guided.get("parsed"), guided
guided_parsed = guided["parsed"]
assert namespace["reasoning_gate_missing"](guided_parsed) == []
assert [a["type"] for a in guided_parsed["actions"]].count("diltiazem") == 1
assert st.session_state.pending_reasoning is None
assert st.session_state.state == before
assert not any(
    "ORDER HELD — REASONING REQUIRED" in event.get("text", "")
    for event in st.session_state.events
)

print("PASS: v0.8.10 flexible semantic reasoning, guided completion, and prompt deduplication")
