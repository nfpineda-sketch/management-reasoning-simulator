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
exec(compile(ast.Module(body=nodes, type_ignores=[]), "v074_subset", "exec"), namespace)


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


initialize()

p1, _, e1 = execute(
    "My working model is reduced effective circulating volume contributing to undifferentiated shock, "
    "with severe hypoxemia of unclear cause. My management priority is to improve perfusion while "
    "supporting oxygenation. Give 1000 mL normal saline and start nasal cannula 4 L/min. I expect "
    "this to improve blood pressure and capillary refill. Reassess perfusion and oxygenation in 15 min."
)
r1 = p1["reasoning"]
assert r1.get("problem_representation", "").startswith("reduced effective circulating volume"), r1
assert "rationale" not in r1, r1
assert r1.get("expected_effect") == "improve blood pressure and capillary refill", r1
assert namespace["_trace_state_text"](e1["state_before"]).endswith("SpO₂ 86% · RA"), namespace["_trace_state_text"](e1["state_before"])

p2, _, e2 = execute(
    "The initial hemodynamic response suggests some remaining preload responsiveness, but severe "
    "hypoxemia persists despite low-flow oxygen. My management priority is to improve oxygenation "
    "while completing initial circulatory support. Give 1000 mL normal saline, start BiPAP 16/8 "
    "with FiO2 100%, give ceftriaxone 2 g IV and azithromycin. I expect improved oxygenation with "
    "maintained perfusion. Reassess perfusion and oxygenation in 10 min."
)
r2 = p2["reasoning"]
assert r2.get("problem_representation", "").startswith("The initial hemodynamic response suggests"), r2
assert r2.get("expected_effect") == "improved oxygenation with maintained perfusion", r2
assert "ceftriaxone 2 g IV + azithromycin" in namespace["_trace_action_text"](e2), namespace["_trace_action_text"](e2)

p3, _, e3 = execute(
    "Persistent hypoxemia despite FiO2 100% and recurrent hemodynamic deterioration make additional "
    "fluid unlikely to provide sufficient benefit. My management priority is to restore perfusion "
    "pressure before airway escalation. Stop further fluids and start norepinephrine 0.1 mcg/kg/min. "
    "I expect improved blood pressure and capillary refill. Reassess perfusion in 5 min."
)
r3 = p3["reasoning"]
assert "additional fluid unlikely" in r3.get("problem_representation", ""), r3
assert r3.get("management_priority") == "restore perfusion pressure before airway escalation", r3
assert r3.get("expected_effect") == "improved blood pressure and capillary refill", r3
assert not any(a.get("type") == "fluid" for a in p3["actions"]), p3

p4, _, e4 = execute(
    "Perfusion pressure has improved, but severe hypoxemic respiratory failure persists despite "
    "BiPAP. My management priority is definitive airway and oxygenation support. Intubate and start "
    "invasive mechanical ventilation with FiO2 100% and PEEP 10 cm H2O. I expect improved "
    "oxygenation while maintaining perfusion. Reassess oxygenation and perfusion in 10 min."
)
r4 = p4["reasoning"]
types4 = [a.get("type") for a in p4["actions"]]
assert r4.get("problem_representation", "").startswith("Perfusion pressure has improved"), r4
assert types4 == ["intubation", "reassessment"], p4
assert not any(a.get("type") == "niv" for a in p4["actions"]), p4
assert "BiPAP 16/8 cm H₂O · FiO₂ 100%" in namespace["_trace_state_text"](e4["state_before"])
assert "BiPAP" not in namespace["_trace_action_text"](e4), namespace["_trace_action_text"](e4)
assert st.session_state.state["observable"]["mental_status"] == "Sedated", st.session_state.state["observable"]
assert "VC/AC · FiO₂ 100% · PEEP 10 cm H₂O" in namespace["_trace_state_text"](e4["state_after"])

items = namespace["_reflect_compare_items"](st.session_state.management_trace)
shift = [item for item in items if item[3] == "Management priority shift"]
mixed = [item for item in items if item[1] == 2 and item[3] == "Mixed response"]
assert shift, items
assert mixed, items
mixed_text = mixed[0][4]
assert "oxygen saturation increased only" in mixed_text.lower(), mixed_text
assert "remained severely impaired" in mixed_text, mixed_text
assert "blood pressure increased" in mixed_text.lower(), mixed_text
assert (
    "capillary refill prolonged" in mixed_text
    or "capillary refill remained 4 seconds" in mixed_text
), mixed_text
assert "Instead" not in mixed_text, mixed_text

print("PASS: v0.7.4 reasoning fidelity and post-intubation coherence")
