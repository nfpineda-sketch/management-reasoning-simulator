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
exec(compile(ast.Module(body=nodes, type_ignores=[]), "v079_subset", "exec"), namespace)


def initialize(case_id="PS002"):
    st.session_state.state = (
        namespace["build_ps002_state"]()
        if case_id == "PS002"
        else deepcopy(namespace["INITIAL_STATE"])
    )
    st.session_state.rng_counter = 0
    st.session_state.pending_action = None
    st.session_state.pending_bundle = None
    st.session_state.last_executed_action = None
    st.session_state.management_trace = []


def execute(text, allow_clarification=False):
    parsed = namespace["clinical_interpreter"](text)
    before = namespace["management_state_snapshot"](st.session_state.state)
    result = namespace["execute_bundle"](parsed)
    after = namespace["management_state_snapshot"](st.session_state.state)
    event = namespace["record_management_trace"](text, parsed, result, before, after)
    if not allow_clarification:
        assert result.get("clarification") is None, result
    return parsed, result, event


initialize()
execute("Start norepinephrine 0.1 mcg/kg/min and reassess perfusion in 5 minutes")
execute(
    "Proceed with intubation and start VC/AC ventilation with FiO2 100% and PEEP 14 cm H2O. "
    "Reassess oxygenation and perfusion in 10 minutes."
)


# Lowering FiO2 alone cannot be presented as causing a higher SpO2 during the
# same response interval. Ongoing recruitment may keep saturation stable.
st.session_state.state["observable"]["spo2"] = 92
pre_fio2_spo2 = st.session_state.state["observable"]["spo2"]
p_fio2, _, _ = execute("Decrease ventilator FiO2 to 60% and reassess oxygenation in 10 minutes")
assert [a["type"] for a in p_fio2["actions"]] == ["ventilator_adjustment", "reassessment"], p_fio2
assert st.session_state.state["observable"]["spo2"] <= pre_fio2_spo2


# Reproduce the exact reported pressor-titration turn.
state = st.session_state.state
state["observable"].update({
    "sbp": 94,
    "dbp": 54,
    "crt": 7,
    "extremities": "Very cold",
    "spo2": 93,
})
state["diagnostics"]["lactate"] = {
    "time_min": state["sim_time"], "value_mmol_l": 5.4, "flag": "elevated"
}
state["diagnostics"]["abg"] = {
    "time_min": state["sim_time"],
    "ph": 7.39,
    "paco2_mm_hg": 29,
    "pao2_mm_hg": 82,
    "bicarbonate_mmol_l": 17,
    "base_excess_mmol_l": -7,
    "fio2_percent": 60.0,
    "pf_ratio": 137,
}
titration_text = (
    "Despite adequate oxygenation, the patient has worsening shock with BP 94/54, capillary refill "
    "7 seconds, very cold extremities, and lactate 5.4 mmol/L. My priority is to improve perfusion. "
    "Increase norepinephrine to 0.2 mcg/kg/min, continue the current ventilator settings, and reassess "
    "blood pressure, capillary refill, extremities, and lactate in 10 minutes."
)
pre_titration_time = state["sim_time"]
p_titrate, r_titrate, e_titrate = execute(titration_text)
types = [a["type"] for a in p_titrate["actions"]]
assert types == ["ventilator_continuation", "norepinephrine", "reassessment", "lactate"], p_titrate
assert p_titrate["reasoning"]["problem_representation"].startswith("worsening shock"), p_titrate["reasoning"]
assert p_titrate["reasoning"]["management_priority"] == "improve perfusion", p_titrate["reasoning"]
assert p_titrate["reasoning"]["reassessment_target"] == (
    "blood pressure, capillary refill, extremities, and lactate"
), p_titrate["reasoning"]
lactate_action = next(a for a in p_titrate["actions"] if a["type"] == "lactate")
assert lactate_action["requested_delay_min"] == 10, lactate_action
lactate_summary = next(s for s in r_titrate["action_summaries"] if s.get("diagnostic_type") == "lactate")
assert lactate_summary["result"]["time_min"] == pre_titration_time + 10, lactate_summary
assert state["sim_time"] == pre_titration_time + 10
norepi_summary = next(s for s in r_titrate["action_summaries"] if s.get("support_type") == "norepinephrine")
assert norepi_summary["operation"] == "titrate", norepi_summary
assert norepi_summary["old_rate"] == 0.1 and norepi_summary["rate"] == 0.2, norepi_summary
assert "increased from 0.1 to 0.2 mcg/kg/min" in namespace["_trace_action_text"](e_titrate)

alignment = namespace["_reasoning_data_alignment_prompt"](e_titrate)
assert alignment and alignment[0] == "Stated interpretation vs available data", alignment
assert "oxygenation was adequate" in alignment[1], alignment
assert "SpO₂ 93% on FiO₂ 60%" in alignment[1], alignment
assert "P/F ratio 137" in alignment[1], alignment


# A retrospective treatment mention must remain reasoning, not an executable
# norepinephrine action. The only requested information is repeat POCUS.
retrospective_text = (
    "The MAP changed minimally after increasing norepinephrine, while capillary refill, extremity "
    "perfusion, and lactate worsened. My working model is persistent shock with pressure-flow "
    "dissociation, possibly compounded by high intrathoracic pressure and vasoconstriction. My priority "
    "is to reassess the hemodynamic phenotype before further escalation. Repeat POCUS to reassess LV "
    "function, RV size, IVC, and lung B-lines, and reassess perfusion in 5 minutes."
)
pre_pocus_time = state["sim_time"]
p_pocus, r_pocus, e_pocus = execute(retrospective_text)
assert not any(a["type"] == "norepinephrine" for a in p_pocus["actions"]), p_pocus
assert {a["type"] for a in p_pocus["actions"]} == {"pocus", "reassessment"}, p_pocus
pocus_action = next(a for a in p_pocus["actions"] if a["type"] == "pocus")
assert pocus_action["requested_delay_min"] is None, pocus_action
pocus_summary = next(s for s in r_pocus["action_summaries"] if s.get("diagnostic_type") == "pocus")
assert pocus_summary["result"]["time_min"] == pre_pocus_time + 2, pocus_summary
assert state["sim_time"] == pre_pocus_time + 5
assert p_pocus["reasoning"]["problem_representation"].startswith("persistent shock with pressure-flow dissociation")
assert p_pocus["reasoning"]["reassessment_target"] == "perfusion", p_pocus["reasoning"]
assert "norepinephrine" not in namespace["_trace_action_text"](e_pocus).lower()


# Other retrospective one-time-treatment references are not repeated either.
p_airway = namespace["clinical_interpreter"](
    "Following intubation, oxygenation is unchanged. Reassess oxygenation in 5 minutes."
)
assert [a["type"] for a in p_airway["actions"]] == ["reassessment"], p_airway
p_cv = namespace["clinical_interpreter"](
    "After synchronized cardioversion, perfusion remains abnormal. Reassess perfusion in 5 minutes."
)
assert [a["type"] for a in p_cv["actions"]] == ["reassessment"], p_cv


# Preserve immediate diagnostic turnaround when the later time belongs to a
# separate reassessment clause.
p_now = namespace["clinical_interpreter"](
    "Obtain an ABG and repeat lactate, then reassess oxygenation and perfusion in 10 minutes."
)
assert next(a for a in p_now["actions"] if a["type"] == "abg")["requested_delay_min"] is None
assert next(a for a in p_now["actions"] if a["type"] == "lactate")["requested_delay_min"] is None

print("PASS: v0.7.9 temporal fidelity, retrospective-action isolation, and complete reasoning targets")
