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
exec(compile(ast.Module(body=nodes, type_ignores=[]), "v075_subset", "exec"), namespace)


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


# Counterfactual 1: observation alone must not normalize shock.
initialize()
_, _, observed10 = execute("reassess in 10 minutes")
obs10 = observed10["state_after"]["observable"]
assert obs10["sbp"] <= 88, obs10
assert obs10["crt"] >= 4, obs10
assert obs10["spo2"] <= 86, obs10

# Counterfactual 2: BiPAP improves oxygenation but is not a pressor.
initialize()
p_bipap, _, bipap10 = execute("Start BiPAP 18/6 O2 100% and reassess in 10 minutes")
types = [a["type"] for a in p_bipap["actions"]]
assert types == ["niv", "reassessment"], p_bipap
niv = p_bipap["actions"][0]
assert niv["ipap_cmh2o"] == 18 and niv["epap_cmh2o"] == 6 and niv["fio2_percent"] == 100, niv
b10 = bipap10["state_after"]["observable"]
assert abs(b10["sbp"] - obs10["sbp"]) <= 3, (obs10, b10)
assert b10["spo2"] >= obs10["spo2"] + 2, (obs10, b10)

# Counterfactual 3: a first bolus has a partial, saturating pressure effect that
# is distinguishable from observation but does not erase shock.
initialize()
_, _, observed15 = execute("reassess in 15 minutes")
obs15 = observed15["state_after"]["observable"]
initialize()
_, _, fluid15 = execute("Give 1000 mL NS, start nasal cannula 4 L/min, and reassess in 15 minutes")
f15 = fluid15["state_after"]["observable"]
assert f15["sbp"] >= obs15["sbp"] + 10, (obs15, f15)
assert f15["sbp"] < 110, f15
assert f15["crt"] <= obs15["crt"], (obs15, f15)
assert fluid15["state_after"]["treatments"]["cumulative_crystalloid_ml"] == 1000

# Exact reported compound order: VBG executes and O2 shorthand remains scoped
# to the subsequent NIV order rather than creating conventional oxygen.
initialize()
p1, _, e1 = execute(
    "start with 1500 cc NS, oxygen nasal canula 4L do a POCUS, lactate, VBG, lab tests. "
    "reassess in 15 minutes"
)
assert {"fluid", "oxygen", "pocus", "lactate", "vbg", "basic_labs", "reassessment"} <= {a["type"] for a in p1["actions"]}
vbg = st.session_state.state["diagnostics"].get("vbg")
assert vbg and 6.9 <= vbg["ph"] <= 7.55 and vbg["lactate_mmol_l"] >= 2.0, vbg
assert "VBG" in namespace["_trace_action_text"](e1), namespace["_trace_action_text"](e1)
pressure_after_fluid = st.session_state.state["observable"]["sbp"]

p2, _, e2 = execute(
    "better hemodynamic status, not shocked anymore, but despite oxygen, clearly with persistent "
    "respiratory distress. Start BiPAP 18/6 O2 100% reassess in 10 minutes"
)
assert [a["type"] for a in p2["actions"]] == ["niv", "reassessment"], p2
assert p2["actions"][0]["fio2_percent"] == 100, p2
assert not any(a["type"] == "oxygen" for a in p2["actions"]), p2
assert st.session_state.state["treatments"]["niv"]
assert not st.session_state.state["treatments"]["oxygen"]
assert st.session_state.state["observable"]["sbp"] <= pressure_after_fluid, st.session_state.state["observable"]
assert namespace["respiratory_support_context"](st.session_state.state, True).startswith("BiPAP 18/6")

# The learner's attempted clarification is harmless when no clarification is pending.
followup = namespace["clinical_interpreter"]("oxygen will be delivered through BiPAP")
assert not any(a["type"] in {"oxygen", "niv"} for a in followup["actions"]), followup

# Defensive resolution of a stale compound bundle drops the erroneous oxygen
# slot but preserves the already specified NIV and reassessment actions.
st.session_state.pending_action = {"type": "oxygen", "device": None, "flow_lpm": None}
st.session_state.pending_bundle = {
    "raw_text": "Start BiPAP 18/6 O2 100% reassess in 10 minutes",
    "before": [{"type": "niv", "mode": "BiPAP", "pressure_cmh2o": 6.0,
                "ipap_cmh2o": 18.0, "epap_cmh2o": 6.0, "fio2_percent": 100.0,
                "operation": "start"}],
    "after": [{"type": "reassessment", "delay_min": 10, "focus": "general"}],
    "reasoning": {},
    "recognized_future_actions": [],
}
resolved = namespace["try_resolve_pending_action"]("oxygen will be delivered through BiPAP")
assert resolved and resolved.get("parsed"), resolved
assert [a["type"] for a in resolved["parsed"]["actions"]] == ["niv", "reassessment"], resolved
assert st.session_state.pending_action is None and st.session_state.pending_bundle is None

# Norepinephrine produces a distinct pressure response after the partial fluid response.
initialize()
execute("Give 1500 mL NS, start nasal cannula 4 L/min, and reassess in 15 minutes")
pre_pressor = st.session_state.state["observable"]["sbp"]
execute("Start norepinephrine 0.1 mcg/kg/min and reassess perfusion in 5 minutes")
post_pressor = st.session_state.state["observable"]["sbp"]
assert post_pressor >= pre_pressor + 15, (pre_pressor, post_pressor)

print("PASS: v0.7.5 counterfactual physiology, O2/NIV scoping, and VBG")
