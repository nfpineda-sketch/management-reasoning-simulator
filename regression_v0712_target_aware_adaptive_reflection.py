import ast
import math
import random
import re
from copy import deepcopy
from pathlib import Path


source = Path("app.py").read_text()
assert "MVP v0.8.21 — dynamic learner-visible ECG with lower-pressure PS001 entry" in source
assert '_patient_diagnostic_heading("POCUS", p)' in source
assert '_patient_diagnostic_heading("Lactate", lac)' in source
assert '_patient_diagnostic_heading("ABG", abg)' in source

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
exec(compile(ast.Module(body=nodes, type_ignores=[]), "v0712_subset", "exec"), namespace)


before = {
    "case_id": "PS002",
    "sim_time_min": 95,
    "observable": {
        "rhythm": "Sinus rhythm", "hr": 124, "sbp": 87, "dbp": 51,
        "crt": 8, "extremities": "Mottled/Cold", "mental_status": "Sedated",
        "spo2": 93, "respiratory_rate": 20, "work_of_breathing": "Ventilator-supported",
    },
    "treatments": {
        "invasive_ventilation": True, "ventilator_mode": "VC/AC",
        "ventilator_fio2_percent": 60.0, "ventilator_peep_cmh2o": 14.0,
    },
    "diagnostics": {"lactate": {"time_min": 90, "value_mmol_l": 5.6}},
}
after = deepcopy(before)
after["sim_time_min"] = 105
after["observable"].update({"sbp": 83, "dbp": 46, "spo2": 91})
after["treatments"]["ventilator_peep_cmh2o"] = 10.0
after["diagnostics"]["lactate"] = {"time_min": 105, "value_mmol_l": 6.7}
reasoning = {
    "problem_representation": "shock persists",
    "management_priority": "support forward flow and reduce intrathoracic-pressure burden while preserving oxygenation",
    "expected_effect": "improved blood pressure, capillary refill, and lactate",
    "preservation_goal": "preserve oxygenation",
    "reassessment_target": "blood pressure, capillary refill, extremities, oxygenation, and lactate",
}


# Explicit reassessment targets remain visible even when unchanged.
deltas = namespace["_trace_observable_delta"](before, after, reasoning)
labels = [label for label, _, _ in deltas]
assert labels == ["BP", "CRT", "Extremities", "SpO₂"], deltas
assert next(item for item in deltas if item[0] == "CRT") == ("CRT", "8 s", "8 s")
assert next(item for item in deltas if item[0] == "Extremities") == (
    "Extremities", "mottled/cold", "mottled/cold"
)


# Expected-effect review includes pressure, stable CRT, oxygenation, and lactate.
adaptive_event = {
    "execution_status": "executed",
    "decision_time_min": 95,
    "response_time_min": 105,
    "learner_input": "I expect improved blood pressure, capillary refill, and lactate.",
    "reasoning": reasoning,
    "action_summaries": [{
        "diagnostic_type": "lactate",
        "result": {"time_min": 105, "value_mmol_l": 6.7, "flag": "elevated"},
    }],
    "state_before": before,
    "state_after": after,
}
prompt = namespace["_expected_response_prompt"](adaptive_event)
assert prompt and prompt[0] == "Expected effect vs observed response", prompt
prompt_text = prompt[1]
assert "blood pressure decreased from 87/51 to 83/46" in prompt_text, prompt_text
assert "capillary refill did not improve and remained 8 seconds" in prompt_text, prompt_text
assert "lactate increased from 5.6 to 6.7 mmol/L" in prompt_text, prompt_text
assert "Oxygenation also worsened despite the stated goal to preserve it (93% to 91%)" in prompt_text, prompt_text


def neutral_event(index):
    state = deepcopy(before)
    state["sim_time_min"] = index * 10
    return {
        "execution_status": "executed",
        "decision_time_min": index * 10,
        "response_time_min": index * 10 + 5,
        "learner_input": "Reassess the patient.",
        "reasoning": {"problem_representation": "ongoing illness"},
        "action_summaries": [],
        "state_before": state,
        "state_after": deepcopy(state),
    }


# The latest explicit expectation mismatch is reserved a reflection slot even
# when three earlier data-alignment prompts are available.
trace = [neutral_event(i) for i in range(11)]
trace[1]["learner_input"] = "The patient is not shocked anymore. Reassess perfusion."
trace[1]["reasoning"] = {"problem_representation": "not shocked anymore"}
trace[1]["state_before"]["observable"].update({"sbp": 96, "dbp": 50, "crt": 4, "hr": 124})
trace[1]["state_before"]["diagnostics"]["lactate"] = {"time_min": 5, "value_mmol_l": 4.7}

trace[4]["learner_input"] = "Severe respiratory failure persists despite BiPAP. Reassess oxygenation."
trace[4]["reasoning"] = {"problem_representation": "severe respiratory failure persists despite BiPAP"}
trace[4]["state_before"]["treatments"].update({
    "invasive_ventilation": True, "ventilator_mode": "VC/AC",
    "ventilator_fio2_percent": 100.0, "ventilator_peep_cmh2o": 10.0,
})

trace[8]["learner_input"] = "Despite adequate oxygenation, shock persists. Reassess perfusion."
trace[8]["reasoning"] = {"problem_representation": "adequate oxygenation with persistent shock"}
trace[8]["state_before"]["observable"]["spo2"] = 93
trace[8]["state_before"]["treatments"].update({
    "invasive_ventilation": True, "ventilator_mode": "VC/AC",
    "ventilator_fio2_percent": 60.0, "ventilator_peep_cmh2o": 14.0,
})
trace[8]["state_before"]["diagnostics"]["abg"] = {"time_min": 83, "pf_ratio": 125}

trace[10] = adaptive_event
items = namespace["_reflect_compare_items"](trace)
decisions = [item[1] for item in items]
assert decisions == [2, 9, 11], items
assert items[-1][3] == "Expected effect vs observed response", items
assert "lactate increased from 5.6 to 6.7 mmol/L" in items[-1][4], items[-1]


# Patient Data headings make acquisition context explicit.
assert namespace["_patient_diagnostic_heading"]("POCUS", {"time_min": 92}) == "**POCUS · 01:32**"
assert namespace["_patient_diagnostic_heading"]("Lactate", {"time_min": 105}) == "**Lactate · 01:45**"

print("PASS: v0.7.12 target-aware stable findings, adaptive reflection, and diagnostic timestamps")
