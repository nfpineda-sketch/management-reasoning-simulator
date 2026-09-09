"""Regression coverage for v0.8.4 conservative antibiotic intent parsing."""

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
namespace = {
    "st": st,
    "re": re,
    "math": math,
    "random": random,
    "deepcopy": deepcopy,
    "escape": escape,
}
exec(compile(ast.Module(body=nodes, type_ignores=[]), "v084_subset", "exec"), namespace)


def initialize():
    st.session_state.state = deepcopy(namespace["INITIAL_STATE"])
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


# Retrospective, continued, deferred, and expected antibiotic mentions are not orders.
initialize()
non_orders = (
    "The urinary source is now supported and antibiotics have been started.",
    "Antibiotics were already administered before transfer.",
    "After ceftriaxone, reassess perfusion in 5 minutes.",
    "Continue the current antibiotics and reassess.",
    "Consider broad-spectrum antibiotics if cultures are positive.",
    "Defer antibiotics until cultures are collected.",
    "I expect antibiotics to improve the infection.",
)
for text in non_orders:
    assert not namespace["is_explicit_antibiotic_order"](text), text
    assert "antibiotics" not in {a["type"] for a in namespace["clinical_interpreter"](text)["actions"]}, text

# Direct and compact orders remain executable.
orders = (
    "Administer ceftriaxone 2 g IV.",
    "Give azithromycin 500 mg IV.",
    "Start broad-spectrum antibiotics.",
    "Treat with antibiotics and reassess.",
    "Ceftriaxone 2 g IV and reassess.",
)
for text in orders:
    assert namespace["is_explicit_antibiotic_order"](text), text
    assert "antibiotics" in {a["type"] for a in namespace["clinical_interpreter"](text)["actions"]}, text


entry_1 = (
    "My working model is AF with RVR and impaired peripheral perfusion, but the rhythm may be "
    "secondary to an acute illness rather than the sole cause of instability. My priority is to "
    "assess the hemodynamic phenotype and reversible causes before committing to rate control or "
    "cardioversion. Give 500 mL normal saline, obtain POCUS, lactate, VBG, basic labs, and ask about "
    "fever and urinary symptoms. Reassess BP, HR and rhythm, capillary refill, extremities, mental "
    "status, SpO2, work of breathing, and lung findings in 5 minutes."
)
entry_2 = (
    "The history, elevated inflammatory markers, lactate 4.9 mmol/L, hyperdynamic LV, and small "
    "collapsible IVC suggest urinary-source sepsis with persistent hypovolemia and impaired tissue "
    "perfusion. AF with RVR may be contributing, but it is not yet clearly the primary cause of "
    "instability. My priority is source-directed treatment and further cautious preload optimization "
    "before using an AV-nodal blocker. Obtain blood cultures and urinalysis, administer ceftriaxone "
    "2 g IV, give an additional 500 mL of normal saline, and reassess BP, HR and rhythm, capillary "
    "refill, extremities, mental status, SpO2, work of breathing, and lung findings in 10 minutes. "
    "I expect improved peripheral perfusion and possibly a partial reduction in heart rate without "
    "pulmonary congestion."
)
entry_3 = (
    "The urinary source is now supported and antibiotics have been started. After 1000 mL of "
    "cumulative fluid, MAP remains 76 mmHg and mental status is preserved, with slightly warmer "
    "extremities but persistent capillary refill of 4 seconds and AF at 171/min. My working model is "
    "sepsis-driven AF with persistent RVR that may now be contributing to impaired forward flow. My "
    "priority is a cautious diagnostic-therapeutic trial of rate control rather than immediate "
    "cardioversion. Give diltiazem 5 mg IV and reassess HR and rhythm, BP and MAP, capillary refill, "
    "extremities, mental status, SpO2, and work of breathing in 5 minutes. I expect a modest reduction "
    "in heart rate without hypotension or worsening tissue perfusion. Do not give additional AV-nodal "
    "blocker if MAP falls below 65 mmHg, mental status worsens, or capillary refill increases."
)

initialize()
execute(entry_1)
parsed_2, result_2 = execute(entry_2)
assert "antibiotics" in {a["type"] for a in parsed_2["actions"]}, parsed_2
assert any(summary.get("support_type") == "antibiotics" for summary in result_2["action_summaries"]), result_2

parsed_3 = namespace["clinical_interpreter"](entry_3)
types_3 = [action["type"] for action in parsed_3["actions"]]
assert "antibiotics" not in types_3, parsed_3
assert "cardioversion" not in types_3, parsed_3
assert {"diltiazem", "reassessment"} <= set(types_3), parsed_3

before_antibiotic_total = st.session_state.state["treatments"]["antibiotics"]
_, result_3 = execute(entry_3)
assert before_antibiotic_total is True
assert not any(summary.get("support_type") == "antibiotics" for summary in result_3["action_summaries"]), result_3
assert [summary.get("agent") for summary in result_3["action_summaries"]] == ["diltiazem"], result_3
trace_action = namespace["_trace_action_text"]({
    "learner_input": entry_3,
    "action_summaries": result_3["action_summaries"],
})
assert trace_action == "diltiazem 5 mg IV", trace_action

observable = st.session_state.state["observable"]
assert observable["rhythm"] == "AF", observable
assert 150 <= observable["hr"] <= 160, observable
assert 100 <= observable["sbp"] <= 115, observable
assert 60 <= observable["dbp"] <= 75, observable
assert observable["crt"] == 4, observable
assert st.session_state.state["sim_time"] == 25, st.session_state.state["sim_time"]

print("PASS: v0.8.4 retrospective antibiotic status is not re-executed")
