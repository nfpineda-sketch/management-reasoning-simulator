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
exec(compile(ast.Module(body=nodes, type_ignores=[]), "v077_subset", "exec"), namespace)


def initialize():
    st.session_state.state = namespace["build_ps002_state"]()
    st.session_state.rng_counter = 0
    st.session_state.pending_action = None
    st.session_state.pending_bundle = None
    st.session_state.last_executed_action = None
    st.session_state.management_trace = []


def execute(text):
    parsed = namespace["clinical_interpreter"](text)
    before = namespace["management_state_snapshot"](st.session_state.state)
    result = namespace["execute_bundle"](parsed)
    after = namespace["management_state_snapshot"](st.session_state.state)
    event = namespace["record_management_trace"](text, parsed, result, before, after)
    assert result.get("clarification") is None, result
    return parsed, result, event


# "so" must function as a connector only at a word boundary. It cannot truncate
# vasopressor, vasopressor-dependent, or another word containing those letters.
exact = (
    "Perfusion pressure has improved, but severe hypoxemic respiratory failure persists despite BiPAP. "
    "My priority is definitive airway and oxygenation support while maintaining vasopressor support. "
    "Proceed with intubation, continue the current norepinephrine infusion, and start VC/AC ventilation "
    "with FiO2 100% and PEEP 10 cm H2O. Reassess oxygenation and perfusion in 10 minutes."
)
reasoning = namespace["extract_explicit_reasoning"](exact)
assert reasoning.get("management_priority") == (
    "definitive airway and oxygenation support while maintaining vasopressor support"
), reasoning

connector = namespace["extract_explicit_reasoning"](
    "My priority is to restore perfusion, so start norepinephrine 0.1 mcg/kg/min."
)
assert connector.get("management_priority") == "restore perfusion", connector


# Active norepinephrine remains part of Patient state at subsequent decisions,
# while continuation is not duplicated as a new Action.
initialize()
execute("Start norepinephrine 0.1 mcg/kg/min and reassess perfusion in 5 minutes")
active_snapshot = namespace["management_state_snapshot"](st.session_state.state)
active_text = namespace["_trace_state_text"](active_snapshot)
assert "Norepinephrine 0.1 mcg/kg/min active" in active_text, active_text

p2, r2, e2 = execute(exact)
assert r2.get("clarification") is None, r2
assert not any(a.get("type") == "norepinephrine" for a in p2["actions"]), p2
assert p2["reasoning"].get("management_priority", "").endswith("vasopressor support"), p2
assert "Norepinephrine 0.1 mcg/kg/min active" in namespace["_trace_state_text"](e2["state_before"])
assert "Norepinephrine 0.1 mcg/kg/min active" in namespace["_trace_state_text"](e2["state_after"])
action_text = namespace["_trace_action_text"](e2)
assert "intubation" in action_text.lower(), action_text
assert "norepinephrine" not in action_text.lower(), action_text


# Other continuous vasoactive infusions use the same visible-state convention.
snapshot = deepcopy(active_snapshot)
snapshot["treatments"].update({
    "dobutamine": True,
    "dobutamine_rate": 5.0,
    "dobutamine_units": "mcg/kg/min",
    "nitroglycerin": True,
    "nitroglycerin_rate_mcg_min": 20.0,
})
state_text = namespace["_trace_state_text"](snapshot)
assert "Dobutamine 5 mcg/kg/min active" in state_text, state_text
assert "Nitroglycerin 20 mcg/min active" in state_text, state_text

print("PASS: v0.7.7 complete priority capture and visible active-infusion state")
