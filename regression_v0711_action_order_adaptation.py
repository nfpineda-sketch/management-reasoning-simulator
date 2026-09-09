import ast
import math
import random
import re
from copy import deepcopy
from pathlib import Path


source = Path("app.py").read_text()
assert "MVP v0.8.21 — dynamic learner-visible ECG with lower-pressure PS001 entry" in source
assert "Clinical response" in source
assert "New diagnostic information" in source
assert "mt-result-list" in source

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
exec(compile(ast.Module(body=nodes, type_ignores=[]), "v0711_subset", "exec"), namespace)


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


# Diagnostic actions are displayed in learner order, not parser declaration order.
initialize()
_, _, gas_event = execute(
    "Obtain an ABG and repeat lactate, then reassess oxygenation and perfusion in 10 minutes."
)
assert namespace["_trace_action_text"](gas_event) == "ABG + lactate", namespace["_trace_action_text"](gas_event)


# Compound treatment/diagnostic actions retain the communicated sequence.
state = st.session_state.state
state["treatments"].update({
    "invasive_ventilation": True,
    "ventilator_mode": "VC/AC",
    "ventilator_fio2_percent": 60.0,
    "ventilator_peep_cmh2o": 14.0,
    "norepinephrine": True,
    "norepinephrine_rate": 0.1,
    "norepinephrine_units": "mcg/kg/min",
})
state["observable"].update({"sbp": 94, "dbp": 54, "crt": 7, "extremities": "Very cold", "spo2": 93})
state["diagnostics"]["lactate"] = {
    "time_min": state["sim_time"], "value_mmol_l": 5.4, "flag": "elevated"
}
order_text = (
    "Despite adequate oxygenation, the patient has worsening shock with lactate 5.4 mmol/L. "
    "Increase norepinephrine to 0.2 mcg/kg/min, continue the current ventilator settings, "
    "and reassess blood pressure and lactate in 10 minutes."
)
_, _, order_event = execute(order_text)
order_label = namespace["_trace_action_text"](order_event)
assert order_label.startswith("norepinephrine increased from 0.1 to 0.2 mcg/kg/min + continue VC/AC ventilation"), order_label
assert order_label.endswith("+ lactate"), order_label


# When reasoning mentions the current PEEP before a new order, the final explicit
# PEEP value governs the ventilator adjustment.
peep_text = (
    "The prior POCUS was obtained while the patient was on PEEP 14 cm H2O. "
    "Reduce PEEP to 10 cm H2O and reassess perfusion and oxygenation in 5 minutes."
)
peep_parsed = namespace["clinical_interpreter"](peep_text)
peep_action = next(a for a in peep_parsed["actions"] if a["type"] == "ventilator_adjustment")
assert peep_action["peep_cmh2o"] == 10.0, peep_parsed


# A post-POCUS adaptive bundle remains executable and longitudinally traceable.
adaptive_text = (
    "The available POCUS shows preserved to hyperdynamic LV function without RV dilation or diffuse "
    "B-lines, while shock persists. My priority is to support forward flow and reduce intrathoracic-pressure "
    "burden while preserving oxygenation. Reduce PEEP to 10 cm H2O, increase norepinephrine to "
    "0.3 mcg/kg/min, start dobutamine 2.5 mcg/kg/min, and repeat lactate in 10 minutes. I expect improved "
    "blood pressure, capillary refill, and lactate. Reassess blood pressure, capillary refill, extremities, "
    "oxygenation, and lactate in 10 minutes."
)
before_time = state["sim_time"]
adaptive_parsed, adaptive_result, adaptive_event = execute(adaptive_text)
adaptive_types = [a["type"] for a in adaptive_parsed["actions"]]
assert "ventilator_adjustment" in adaptive_types and "norepinephrine" in adaptive_types, adaptive_parsed
assert "dobutamine" in adaptive_types and "lactate" in adaptive_types, adaptive_parsed
assert state["treatments"]["ventilator_peep_cmh2o"] == 10.0
assert state["treatments"]["norepinephrine_rate"] == 0.3
assert state["treatments"]["dobutamine_rate"] == 2.5
assert state["sim_time"] == before_time + 10
lactate_summary = next(s for s in adaptive_result["action_summaries"] if s.get("diagnostic_type") == "lactate")
assert lactate_summary["result"]["time_min"] == before_time + 10, lactate_summary
adaptive_label = namespace["_trace_action_text"](adaptive_event)
assert adaptive_label.index("adjust VC/AC") < adaptive_label.index("norepinephrine") < adaptive_label.index("dobutamine") < adaptive_label.index("lactate"), adaptive_label
diagnostic_response = namespace["_trace_diagnostic_results"](adaptive_event)
assert any("Lactate:" in result for _, result in diagnostic_response), diagnostic_response

print("PASS: v0.7.11 learner-order display, final-parameter fidelity, and post-POCUS adaptation")
