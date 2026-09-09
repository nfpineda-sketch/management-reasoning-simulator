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
exec(compile(ast.Module(body=nodes, type_ignores=[]), "v078_subset", "exec"), namespace)


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


# Establish invasive ventilation and an active pressor.
initialize("PS002")
execute("Start norepinephrine 0.1 mcg/kg/min and reassess perfusion in 5 minutes")
_, _, intubation = execute(
    "Proceed with intubation and start VC/AC ventilation with FiO2 100% and PEEP 10 cm H2O. "
    "Reassess oxygenation and perfusion in 10 minutes."
)
tr = st.session_state.state["treatments"]
assert tr["invasive_ventilation"] and tr["ventilator_peep_cmh2o"] == 10
assert tr["ventilator_fio2_percent"] == 100
assert st.session_state.state["observable"]["mental_status"] == "Sedated"


# Repeating the exact intubation order at identical settings is a continuation,
# not another procedure or sedation event.
repeat_text = (
    "Perfusion pressure has improved, but severe hypoxemic respiratory failure persists despite BiPAP. "
    "My priority is definitive airway and oxygenation support while maintaining vasopressor support. "
    "Proceed with intubation, continue the current norepinephrine infusion, and start VC/AC ventilation "
    "with FiO2 100% and PEEP 10 cm H2O. Reassess oxygenation and perfusion in 10 minutes."
)
pre_repeat_time = st.session_state.state["sim_time"]
p_repeat, r_repeat, e_repeat = execute(repeat_text)
types = [a["type"] for a in p_repeat["actions"]]
assert types == ["ventilator_continuation", "reassessment"], p_repeat
assert not any(a["type"] in {"intubation", "norepinephrine"} for a in p_repeat["actions"]), p_repeat
vent_summary = next(s for s in r_repeat["action_summaries"] if s.get("support_type") == "invasive_ventilation")
assert vent_summary["operation"] == "continue", vent_summary
assert st.session_state.state["sim_time"] == pre_repeat_time + 10
assert st.session_state.state["observable"]["mental_status"] == "Sedated"
action_text = namespace["_trace_action_text"](e_repeat)
assert "continue VC/AC ventilation" in action_text, action_text
assert "intubation" not in action_text.lower(), action_text
assert "norepinephrine" not in action_text.lower(), action_text

# The reasoning named BiPAP although the active support was invasive ventilation.
alignment = namespace["_reasoning_data_alignment_prompt"](e_repeat, intubation)
assert alignment and alignment[0] == "Stated interpretation vs available data", alignment
assert "current response was occurring on BiPAP" in alignment[1], alignment
assert "active respiratory support was VC/AC invasive ventilation" in alignment[1], alignment


# Independent ventilator adjustments are executable and never repeat intubation.
p_peep, r_peep, e_peep = execute("Increase PEEP to 14 cm H2O and reassess in 10 minutes")
assert [a["type"] for a in p_peep["actions"]] == ["ventilator_adjustment", "reassessment"], p_peep
assert st.session_state.state["treatments"]["ventilator_peep_cmh2o"] == 14
assert st.session_state.state["treatments"]["ventilator_fio2_percent"] == 100
assert "adjust VC/AC ventilation" in namespace["_trace_action_text"](e_peep)

p_fio2, _, e_fio2 = execute("Decrease FiO2 to 60% and reassess oxygenation in 10 minutes")
assert [a["type"] for a in p_fio2["actions"]] == ["ventilator_adjustment", "reassessment"], p_fio2
assert st.session_state.state["treatments"]["ventilator_fio2_percent"] == 60
assert st.session_state.state["treatments"]["ventilator_peep_cmh2o"] == 14
assert "FiO₂ 60%" in namespace["_trace_action_text"](e_fio2)

p_continue, _, e_continue = execute("Continue current ventilator settings and reassess in 10 minutes")
assert [a["type"] for a in p_continue["actions"]] == ["ventilator_continuation", "reassessment"], p_continue
assert "continue VC/AC ventilation" in namespace["_trace_action_text"](e_continue)


# ABG is executable and carries a support-aware P/F ratio.
p_abg, _, e_abg = execute("Obtain an ABG and repeat lactate, then reassess in 10 minutes")
assert {a["type"] for a in p_abg["actions"]} >= {"abg", "lactate", "reassessment"}, p_abg
abg = st.session_state.state["diagnostics"].get("abg")
assert abg and 6.9 <= abg["ph"] <= 7.6, abg
assert abg["pao2_mm_hg"] >= 35 and abg["paco2_mm_hg"] >= 22, abg
assert abg["fio2_percent"] == 60, abg
assert abg["pf_ratio"] == round(abg["pao2_mm_hg"] / 0.60), abg
assert "ABG" in namespace["_trace_action_text"](e_abg)
assert "P/F ratio" in namespace["format_diagnostic_summary"](
    next(s for s in e_abg["action_summaries"] if s.get("diagnostic_type") == "abg")
)


# Incompatible respiratory interfaces are blocked without changing state/time.
pre_conflict = deepcopy(st.session_state.state)
_, oxygen_conflict, _ = execute(
    "Start nasal cannula 4 L/min and reassess in 10 minutes", allow_clarification=True
)
assert "invasive ventilation" in oxygen_conflict.get("clarification", "").lower(), oxygen_conflict
assert st.session_state.state["sim_time"] == pre_conflict["sim_time"]
assert st.session_state.state["treatments"]["invasive_ventilation"]
assert not st.session_state.state["treatments"]["oxygen"]

_, niv_conflict, _ = execute("Start BiPAP 16/8 and reassess in 10 minutes", allow_clarification=True)
assert "currently intubated" in niv_conflict.get("clarification", "").lower(), niv_conflict

_, prep_conflict, _ = execute("Prepare for intubation and reassess in 5 minutes", allow_clarification=True)
assert "already intubated" in prep_conflict.get("clarification", "").lower(), prep_conflict


# State-dependent one-time actions do not silently repeat.
initialize("PS001")
execute("Perform synchronized cardioversion with 200 J and reassess immediately")
assert st.session_state.state["observable"]["rhythm"] == "Sinus rhythm"
cardioversions = st.session_state.state["treatments"]["cardioversions"]
_, repeat_cv, _ = execute(
    "Perform synchronized cardioversion with 200 J and reassess immediately", allow_clarification=True
)
assert "current rhythm is sinus rhythm" in repeat_cv.get("clarification", "").lower(), repeat_cv
assert st.session_state.state["treatments"]["cardioversions"] == cardioversions

initialize("PS002")
execute("Admit to ICU")
_, repeat_icu, _ = execute("Admit to ICU", allow_clarification=True)
assert "already admitted to ICU" in repeat_icu.get("clarification", ""), repeat_icu

print("PASS: v0.7.8 state-aware respiratory orders, ABG, and one-time action integrity")
