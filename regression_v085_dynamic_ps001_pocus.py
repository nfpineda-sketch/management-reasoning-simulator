"""Regression coverage for v0.8.5 dynamic PS001 POCUS contractility."""

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
assert 'h["effective_contractility"] = effective_contractility' in source

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
exec(compile(ast.Module(body=nodes, type_ignores=[]), "v085_subset", "exec"), namespace)


def initialize(state=None):
    st.session_state.state = deepcopy(state or namespace["INITIAL_STATE"])
    st.session_state.rng_counter = 0
    st.session_state.pending_action = None
    st.session_state.pending_bundle = None
    st.session_state.last_executed_action = None
    st.session_state.management_trace = []


def execute(text):
    parsed = namespace["clinical_interpreter"](text)
    result = namespace["execute_bundle"](parsed)
    assert result.get("clarification") is None, result
    return parsed, result


# The first POCUS still reports the patient's preserved baseline phenotype.
initialize()
initial_pocus = namespace["pocus_transition"](deepcopy(st.session_state.state))["result"]
assert initial_pocus["lv"] == "preserved to hyperdynamic LV systolic function", initial_pocus

# Reproduce the treatment/time sequence that generated the classroom finding.
for entry in (
    "Give 500 mL normal saline, obtain POCUS, lactate, VBG, basic labs, and reassess in 5 minutes.",
    "Administer ceftriaxone 2 g IV, give 500 mL normal saline, and reassess in 10 minutes.",
    "Give diltiazem 5 mg IV and reassess in 5 minutes.",
    "Give another diltiazem 5 mg IV and reassess in 5 minutes.",
):
    execute(entry)

state = st.session_state.state
assert state["sim_time"] == 30, state["sim_time"]
assert state["hidden"]["effective_contractility"] < 0.60, state["hidden"]
repeat_pocus = namespace["pocus_transition"](deepcopy(state))["result"]
assert repeat_pocus["lv"] == "moderately to severely reduced LV systolic function", repeat_pocus
assert "1.4 cm" in repeat_pocus["ivc"] and ">50%" in repeat_pocus["ivc"], repeat_pocus
assert repeat_pocus["lungs"] == "no diffuse B-line pattern", repeat_pocus

# Describing the available dynamic POCUS in the next reasoning turn is not a new order.
retrospective_pocus = namespace["clinical_interpreter"](
    "Despite substantial rate reduction, perfusion has worsened: MAP is 69 mmHg, "
    "capillary refill is 5 seconds, lactate is 5.0 mmol/L, and the current POCUS "
    "demonstrates moderately to severely reduced LV systolic function. My priority "
    "is to restore perfusion pressure without further rate-control medication. "
    "Start norepinephrine 0.05 mcg/kg/min and reassess in 5 minutes."
)
assert [action["type"] for action in retrospective_pocus["actions"]] == [
    "norepinephrine",
    "reassessment",
], retrospective_pocus

# Inotropic recruitment changes subsequent imaging rather than leaving a fixed label.
execute("Start norepinephrine 0.05 mcg/kg/min and reassess in 5 minutes.")
execute("Perform synchronized cardioversion with 200 J and reassess in 5 minutes.")
pre_inotrope = namespace["pocus_transition"](deepcopy(state))["result"]
assert pre_inotrope["lv"] == "moderately to severely reduced LV systolic function", pre_inotrope
execute("Start dobutamine 2.5 mcg/kg/min and reassess in 10 minutes.")
post_inotrope = namespace["pocus_transition"](deepcopy(state))["result"]
assert post_inotrope["lv"] == "mildly reduced LV systolic function", post_inotrope

# PS002 retains the already validated case-specific imaging phenotype.
ps002 = namespace["build_ps002_state"]()
ps002["hidden"]["effective_contractility"] = 0.20
ps002_pocus = namespace["pocus_transition"](ps002)["result"]
assert ps002_pocus["lv"] == "preserved to hyperdynamic LV systolic function", ps002_pocus

print("PASS: v0.8.5 PS001 POCUS follows dynamic contractility and preserves PS002")
