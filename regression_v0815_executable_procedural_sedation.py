"""Regression coverage for v0.8.19 executable procedural sedation."""

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


learner_text = (
    "Still in afib, i want to do rythm management. Cardiovert sincronized 200 j. "
    "Sedation with etomidate 8 mg + midazolam 2 mg. I expect conversion to sinus "
    "rhythm with improved perfusion. Reassess in 10 minutes, rhythm, hr, bp and perfusion"
)

initialize()
parsed = namespace["clinical_interpreter"](learner_text)
types = [action["type"] for action in parsed["actions"]]
assert types[:2] == ["procedural_sedation", "cardioversion"], parsed
assert types.count("reassessment") == 1, parsed
assert parsed["recognized_future_actions"] == [], parsed
assert namespace["reasoning_gate_missing"](parsed) == [], parsed

before = namespace["management_state_snapshot"](st.session_state.state)
result = namespace["execute_bundle"](parsed)
after = namespace["management_state_snapshot"](st.session_state.state)
assert result["executed"] is True, result
assert result["elapsed_min"] == 10, result
assert [s.get("support_type") for s in result["action_summaries"][:1]] == ["procedural_sedation"], result
assert result["action_summaries"][1].get("energy_j") == 200, result

ordered = namespace["_summaries_in_learner_order"](result["action_summaries"], learner_text)
assert ordered[0].get("support_type") == "procedural_sedation", ordered
assert ordered[1].get("energy_j") == 200, ordered

tr = st.session_state.state["treatments"]
assert tr["procedural_sedations"] == 1, tr
assert tr["etomidate_total_mg"] == 8.0, tr
assert tr["midazolam_total_mg"] == 2.0, tr
assert tr["cardioversions"] == 1, tr
assert st.session_state.state["observable"]["rhythm"] == "Sinus rhythm"
assert st.session_state.state["observable"]["mental_status"] in {"Sedated", "Drowsy"}
assert after["treatments"]["last_procedural_sedation"][0]["agent"] == "etomidate"

# Natural canonical English produced from a Spanish learner turn must remain
# executable, including equivalent "order", "electrical", and "using" syntax.
canonical_spanish_turn = (
    "The patient is hypotensive, poorly perfused, and tachycardic. I think the primary problem is "
    "atrial fibrillation, so I order synchronized electrical cardioversion at 200 J, with sedation "
    "using etomidate 8 mg and midazolam 2 mg. I expect conversion to sinus rhythm and improvement in "
    "the signs of perfusion. After cardioversion, reassess the rhythm, heart rate, blood pressure, and perfusion."
)
initialize()
canonical_parsed = namespace["clinical_interpreter"](canonical_spanish_turn)
canonical_types = [action["type"] for action in canonical_parsed["actions"]]
assert canonical_types[:2] == ["procedural_sedation", "cardioversion"], canonical_parsed
assert namespace["reasoning_gate_missing"](canonical_parsed) == [], canonical_parsed
canonical_result = namespace["execute_bundle"](canonical_parsed)
assert canonical_result["executed"] is True, canonical_result
assert canonical_result["elapsed_min"] == 3, canonical_result
assert canonical_result["reassess_delay"] == 0, canonical_result
assert st.session_state.state["observable"]["rhythm"] == "Sinus rhythm"

namespace["record_management_trace"](learner_text, parsed, result, before, after)
trace_label = namespace["_trace_action_text"](st.session_state.management_trace[-1])
assert trace_label.index("procedural sedation") < trace_label.index("synchronized cardioversion"), trace_label
assert "etomidate 8 mg IV" in trace_label and "midazolam 2 mg IV" in trace_label, trace_label

# Unsupported alternatives remain visible but cannot be mistaken for an
# administered etomidate/midazolam regimen.
unsupported = namespace["clinical_interpreter"](
    "Sedation with fentanyl 50 mcg before synchronized cardioversion 200 J."
)
assert unsupported["recognized_future_actions"] == ["fentanyl 50 mcg for analgesia"], unsupported
assert not any(a["type"] == "procedural_sedation" for a in unsupported["actions"]), unsupported

print("PASS: v0.8.19 executes and records etomidate/midazolam procedural sedation before cardioversion")
