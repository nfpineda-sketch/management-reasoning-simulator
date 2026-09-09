import ast
import math
import random
import re
from copy import deepcopy
from pathlib import Path


source = Path("app.py").read_text()
assert "MVP v0.8.21 — dynamic learner-visible ECG with lower-pressure PS001 entry" in source

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
exec(compile(ast.Module(body=nodes, type_ignores=[]), "v0713_subset", "exec"), namespace)


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
    return event


entries = [
    "start with 1500 cc NS, oxygen nasal canula 4L, do a POCUS, lactate, VBG, lab tests. reassess in 15 minutes",
    "better hemodynamic status, not shocked anymore, but despite oxygen, clearly with persistent respiratory distress. Start BiPAP 18/6 O2 100% reassess in 10 minutes",
    "The patient remains in shock despite partial fluid responsiveness, and BiPAP has worsened perfusion while hypoxemia persists. My priority is to restore perfusion pressure before intubation. Start norepinephrine 0.1 mcg/kg/min and prepare for intubation. I expect improved blood pressure and capillary refill. Reassess perfusion in 5 minutes.",
    "Perfusion pressure has improved, but severe hypoxemic respiratory failure persists despite BiPAP. My priority is definitive airway and oxygenation support while maintaining vasopressor support. Proceed with intubation, continue the current norepinephrine infusion, and start VC/AC ventilation with FiO2 100% and PEEP 10 cm H2O. Reassess oxygenation and perfusion in 10 minutes.",
    "Perfusion pressure has improved, but severe hypoxemic respiratory failure persists despite BiPAP. My priority is definitive airway and oxygenation support while maintaining vasopressor support. Proceed with intubation, continue the current norepinephrine infusion, and start VC/AC ventilation with FiO2 100% and PEEP 10 cm H2O. Reassess oxygenation and perfusion in 10 minutes.",
    "Increase PEEP to 14 cm H2O and reassess oxygenation and perfusion in 10 minutes.",
    "Decrease ventilator FiO2 to 60% and reassess oxygenation in 10 minutes.",
    "Obtain an ABG and repeat lactate, then reassess oxygenation and perfusion in 10 minutes.",
    "Despite adequate oxygenation, the patient has worsening shock with BP 94/53, capillary refill 7 seconds, very cold extremities, and lactate 5.5 mmol/L. My priority is to improve perfusion. Increase norepinephrine to 0.2 mcg/kg/min, continue the current ventilator settings, and reassess blood pressure, capillary refill, extremities, and lactate in 10 minutes.",
    "The MAP changed minimally after increasing norepinephrine, while capillary refill, extremity perfusion, and lactate worsened. My working model is persistent shock with pressure-flow dissociation, possibly compounded by high intrathoracic pressure and vasoconstriction. My priority is to reassess the hemodynamic phenotype before further escalation. Repeat POCUS to reassess LV function, RV size, IVC, and lung B-lines, and reassess perfusion in 5 minutes.",
    "The available POCUS shows preserved to hyperdynamic LV function without RV dilation or diffuse B-lines, while shock persists. My priority is to support forward flow and reduce intrathoracic-pressure burden while preserving oxygenation. Reduce PEEP to 10 cm H2O, increase norepinephrine to 0.3 mcg/kg/min, start dobutamine 2.5 mcg/kg/min, and repeat lactate in 10 minutes. I expect improved blood pressure, capillary refill, and lactate. Reassess blood pressure, capillary refill, extremities, oxygenation, and lactate in 10 minutes.",
]


initialize()
events = [execute(text) for text in entries]
state = st.session_state.state

# The maintained guide must quote the observations actually available at the
# start of Decision 9; recalibration must not silently stale its fixed values.
decision9_before = events[8]["state_before"]
assert decision9_before["observable"]["sbp"] == 94, decision9_before
assert decision9_before["observable"]["dbp"] == 53, decision9_before
assert decision9_before["diagnostics"]["lactate"]["value_mmol_l"] == 5.5, decision9_before
assert "BP 94/53" in events[8]["reasoning"]["problem_representation"]
assert "lactate 5.5 mmol/L" in events[8]["reasoning"]["problem_representation"]

# Sedation is an intubation transition once, not a repeated historical event.
intubation_delta = namespace["_trace_observable_delta"](
    events[3]["state_before"], events[3]["state_after"], events[3]["reasoning"]
)
assert ("Mental status", "alert", "sedated after intubation") in intubation_delta, intubation_delta
continuation_delta = namespace["_trace_observable_delta"](
    events[4]["state_before"], events[4]["state_after"], events[4]["reasoning"]
)
assert ("Mental status", "sedated", "sedated") in continuation_delta, continuation_delta
assert all(after != "sedated after intubation" for _, _, after in continuation_delta)

# Improvement, preservation, and reassessment remain distinct reasoning slots.
final_reasoning = events[-1]["reasoning"]
assert final_reasoning["expected_effect"] == "improved blood pressure, capillary refill, and lactate"
assert final_reasoning["preservation_goal"] == "preserve oxygenation", final_reasoning
assert final_reasoning["reassessment_target"] == "blood pressure, capillary refill, extremities, oxygenation, and lactate"

prompt = namespace["_expected_response_prompt"](events[-1])
assert prompt and prompt[0] == "Expected effect vs observed response", prompt
assert "Those expected improvements were not demonstrated" in prompt[1], prompt
assert "Oxygenation also worsened despite the stated goal to preserve it" in prompt[1], prompt

# Active-treatment history exposes start and last-adjustment times.
timeline = state["treatment_timeline"]
assert timeline["norepinephrine"]["started_min"] == 25, timeline
assert timeline["norepinephrine"]["last_changed_min"] == 95, timeline
assert timeline["invasive_ventilation"]["started_min"] == 30, timeline
assert timeline["invasive_ventilation"]["last_changed_min"] == 95, timeline
assert timeline["dobutamine"]["started_min"] == 95, timeline
assert namespace["_treatment_timing_suffix"](state, "norepinephrine") == " — started 00:25 · last adjusted 01:35"
assert namespace["_treatment_timing_suffix"](state, "invasive_ventilation") == " — started 00:30 · last adjusted 01:35"
assert namespace["_treatment_timing_suffix"](state, "dobutamine") == " — started 01:35"

# PS002 sinus rate is longitudinal rather than frozen at its initial 124/min.
final_hr = state["observable"]["hr"]
assert final_hr != 124, final_hr
assert 105 <= final_hr <= 145, final_hr
assert any(
    event["state_after"]["observable"]["hr"] != event["state_before"]["observable"]["hr"]
    for event in events
), [event["state_after"]["observable"]["hr"] for event in events]

# Adaptive reflection still preserves the intended early/middle/final structure.
items = namespace["_reflect_compare_items"](st.session_state.management_trace)
assert [item[1] for item in items] == [2, 9, 11], items

print("PASS: v0.7.13 transition integrity, separated intent, treatment timing, and dynamic sinus rate")
