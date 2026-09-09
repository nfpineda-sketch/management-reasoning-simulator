"""Regression coverage for partial reasoning and held procedural actions."""

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
assert "procedural_sedation" in source

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


# Literal reproduction of the screenshot. Three reasoning components are
# present in natural language; only the expected effect is actually absent.
initialize()
learner_turn = namespace["clinical_interpreter"](
    "Still in afib, i want to do rythm management. Cardiovert sincronized 200 j. "
    "Sedation with etomidate 8 mg + midazolam 2 mg. Reassess in 10 minutes, "
    "rhythm, hr, bp and perfusion"
)
reasoning = learner_turn["reasoning"]
assert "still" in reasoning["problem_representation"].lower(), reasoning
assert reasoning["management_priority"].lower() == "rhythm management", reasoning
assert "expected_effect" not in reasoning, reasoning
assert "rhythm" in reasoning["reassessment_target"].lower(), reasoning
assert "perfusion" in reasoning["reassessment_target"].lower(), reasoning
assert namespace["reasoning_gate_missing"](learner_turn) == ["expected_effect"], learner_turn
assert [a["type"] for a in learner_turn["actions"]].count("procedural_sedation") == 1
assert [a["type"] for a in learner_turn["actions"]].count("cardioversion") == 1
assert [a["type"] for a in learner_turn["actions"]].count("reassessment") == 1
assert learner_turn["recognized_future_actions"] == [], learner_turn
sedation = next(a for a in learner_turn["actions"] if a["type"] == "procedural_sedation")
assert [(m["agent"], m["dose"], m["route"]) for m in sedation["medications"]] == [
    ("etomidate", 8.0, "IV"),
    ("midazolam", 2.0, "IV"),
], sedation

# The clarification must hold sedation and cardioversion together; neither can
# produce a patient response until the missing effect is supplied.
prompt = namespace["hold_pending_reasoning"](learner_turn)
assert "Expected effect" in prompt, prompt
assert "Working model" not in prompt, prompt
assert "Management priority" not in prompt, prompt
assert "Reassessment target" not in prompt, prompt
assert "etomidate 8 mg" in prompt and "midazolam 2 mg" in prompt, prompt
assert prompt.index("procedural sedation") < prompt.index("synchronized cardioversion"), prompt
assert "not executable" not in prompt, prompt

# Supplying only the missing effect completes the held order and preserves all
# previously recognized reasoning and actions.
resolved = namespace["resolve_pending_reasoning"](
    "I expect conversion to sinus rhythm with improved perfusion."
)
assert resolved.get("parsed"), resolved
completed = resolved["parsed"]
assert namespace["reasoning_gate_missing"](completed) == [], completed
assert completed["reasoning"]["management_priority"].lower() == "rhythm management"
assert completed["recognized_future_actions"] == learner_turn["recognized_future_actions"]
assert [a["type"] for a in completed["actions"]].count("procedural_sedation") == 1
assert [a["type"] for a in completed["actions"]].count("cardioversion") == 1

# Bounded behavior: an action proposal using "do" is not relabeled as a
# management priority, while timing-first reassessment wording is accepted.
bounded = namespace["extract_explicit_reasoning"]("I want to do cardioversion 200 J.")
assert "management_priority" not in bounded, bounded
timing_first = namespace["extract_explicit_reasoning"](
    "Reassess after 5 minutes, mental status, BP/MAP and capillary refill."
)
assert "mental status" in timing_first["reassessment_target"].lower(), timing_first

print("PASS: partial reasoning preserves the executable sedation-cardioversion bundle")
