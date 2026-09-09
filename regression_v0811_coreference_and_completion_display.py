"""Regression coverage for v0.8.11 coreference and completion display."""

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
assert '"reasoning_completion": "REASONING COMPLETION"' in source
assert '"reasoning_completion" if submission_parsed is not None else "you"' in source
assert "My working model is it is" not in source

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
exec(compile(ast.Module(body=nodes, type_ignores=[]), "v0811_subset", "exec"), namespace)


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


# Literal reproduction of the learner wording that exposed the bug. ``it`` must
# resolve to the explicit nearby antecedent rather than becoming a free-floating
# working model.
initialize()
learner_turn = namespace["clinical_interpreter"](
    "give paciente diltiazem 5 mg iv. Im addressing heart rate first, because i "
    "think it is the primary problem. I expect a moderate decrease in heart rate, "
    "maybe better perfusion. reassess in 10 minutes"
)
reasoning = learner_turn["reasoning"]
assert reasoning["problem_representation"] == "heart rate is the primary problem", reasoning
assert reasoning["management_priority"] == "heart rate", reasoning
assert "it is the primary problem" not in set(reasoning.values())
assert namespace["reasoning_gate_missing"](learner_turn) == ["reassessment_target"]

# Without a high-confidence antecedent the parser must ask rather than invent a
# referent or accept an unusable pronoun-only working model.
initialize()
unresolved = namespace["clinical_interpreter"](
    "I think it is the primary problem. Give diltiazem 5 mg IV. "
    "I expect a lower heart rate. Reassess HR and BP in 5 minutes."
)
assert "problem_representation" not in unresolved["reasoning"], unresolved
assert "working_model" in namespace["reasoning_gate_missing"](unresolved)

# Guided completion uses labeled fields, not sentence reconstruction, and keeps
# the original treatment pending until the normal execution path runs.
initialize()
namespace["hold_pending_reasoning"](
    learner_turn,
    namespace["reasoning_gate_missing"](learner_turn),
)
before = deepcopy(st.session_state.state)
guided = namespace["complete_pending_reasoning_fields"](
    reasoning["problem_representation"],
    reasoning["management_priority"],
    reasoning["expected_effect"],
    "HR, BP, and perfusion",
    10,
)
assert guided.get("parsed"), guided
transcript = guided["transcript"]
assert transcript.startswith("**Working model:** heart rate is the primary problem")
assert "My working model is" not in transcript
assert "is it is" not in transcript
assert [a["type"] for a in guided["parsed"]["actions"]].count("diltiazem") == 1
assert st.session_state.state == before

print("PASS: v0.8.11 resolves explicit pronouns and labels guided reasoning cleanly")
