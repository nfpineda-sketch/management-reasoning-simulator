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
exec(compile(ast.Module(body=nodes, type_ignores=[]), "v073_subset", "exec"), namespace)


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
    namespace["record_management_trace"](text, parsed, result, before, after)
    assert result.get("clarification") is None, result
    return parsed, result


initialize()
execute("give 1000 mL normal saline, nasal cannula 4 L/min, reassess in 15 min")
execute("give 1000 mL normal saline, BiPAP 16/8 FiO2 100%, ceftriaxone 2 g IV and azithromycin, reassess in 10 min")
assert namespace["respiratory_support_context"](st.session_state.state, True).startswith("BiPAP 16/8")
assert not st.session_state.state["treatments"]["oxygen"]

execute(
    "give 500 cc ns, lab exams, urine. The patient is still hypoxic. "
    "Increase CPAP to 10 cm H2O and reassess in 15 min"
)
items = namespace["_reflect_compare_items"](st.session_state.management_trace)
assert any(item[3] == "Critical adaptation point" for item in items), items

before_disposition = deepcopy(st.session_state.state["observable"])
execute("admit to ICU")
assert st.session_state.state["observable"] == before_disposition

negated = namespace["clinical_interpreter"]("I think she doesn't need intubation at this point")
assert not any(action["type"] == "intubation" for action in negated["actions"]), negated

initialize()
execute("give 1000 mL normal saline, nasal cannula 4 L/min, reassess in 15 min")
execute("give 1000 mL normal saline, BiPAP 16/8 FiO2 100%, ceftriaxone 2 g IV and azithromycin, reassess in 10 min")
pressure_before_pressor = st.session_state.state["observable"]["sbp"]
execute("start norepinephrine 0.1 mcg/kg/min and reassess perfusion in 5 min")
pressure_after_pressor = st.session_state.state["observable"]["sbp"]
execute("intubate with FiO2 100% PEEP 10 and reassess in 10 min")
observable = st.session_state.state["observable"]
assert pressure_after_pressor >= 110, pressure_after_pressor
assert pressure_after_pressor >= pressure_before_pressor + 15, (pressure_before_pressor, pressure_after_pressor)
assert observable["sbp"] >= 105, observable
assert observable["spo2"] >= 92, observable
assert st.session_state.state["treatments"]["invasive_ventilation"]
assert namespace["respiratory_support_context"](st.session_state.state, True).startswith("VC/AC")

print("PASS: v0.7.3 clinical coherence, adaptation point, and rescue branch")
