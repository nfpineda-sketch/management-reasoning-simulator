"""Regression coverage for v0.8.2 persistent and historical vital-sign visibility."""

import ast
from copy import deepcopy
from html import escape
from pathlib import Path
from types import SimpleNamespace


source = Path("app.py").read_text(encoding="utf-8")

assert 'SIMULATOR_VERSION = "0.8.21"' in source
assert "MVP v0.8.21 — dynamic learner-visible ECG with lower-pressure PS001 entry" in source
assert 'position: sticky' in source
assert 'class="mrs-persistent-monitor"' in source
assert "Live patient state" in source
assert "Updates after each executed intervention" in source
assert 'event["learner_vitals"] = learner_vitals_snapshot' in source
assert "PATIENT RESPONSE" in source
assert '_vitals_grid_html(snapshot, variant="response")' in source

module = ast.parse(source)
required = {
    "_snapshot_respiratory_support",
    "learner_vitals_snapshot",
    "add_event",
    "sim_time_label",
    "_vitals_cells",
    "_vitals_grid_html",
}
nodes = [
    node for node in module.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in required
]
assert {node.name for node in nodes} == required

state = {
    "sim_time": 5,
    "hidden": {"forward_flow_state": 0.12, "tissue_perfusion": 0.18},
    "observable": {
        "pulse_present": True,
        "sbp": 100,
        "dbp": 60,
        "hr": 162,
        "rhythm": "AF",
        "spo2": 93,
        "respiratory_rate": 22,
        "work_of_breathing": "Mildly increased",
        "crt": 5,
        "extremities": "Cool",
        "mental_status": "Alert",
        "temperature_c": 37.1,
    },
    "treatments": {
        "oxygen": False,
        "niv": False,
        "invasive_ventilation": False,
    },
}
session_state = SimpleNamespace(state=state, events=[])
namespace = {
    "escape": escape,
    "st": SimpleNamespace(session_state=session_state),
}
exec(compile(ast.Module(body=nodes, type_ignores=[]), "v082_subset", "exec"), namespace)

snapshot = namespace["learner_vitals_snapshot"](state)
assert snapshot["map"] == 73
assert snapshot["respiratory_support"] == "Room air"
assert "hidden" not in snapshot
assert "forward_flow_state" not in snapshot
assert "temperature_c" not in snapshot

namespace["add_event"]("clinical_update", "The patient changes state.")
saved_event = deepcopy(session_state.events[-1])
assert saved_event["learner_vitals"]["hr"] == 162
assert saved_event["learner_vitals"]["sim_time_min"] == 5

# A later clinical transition must not rewrite an earlier response card.
state["sim_time"] = 10
state["observable"]["hr"] = 138
state["observable"]["sbp"] = 92
assert session_state.events[-1]["learner_vitals"] == saved_event["learner_vitals"]

html = namespace["_vitals_grid_html"](snapshot, variant="response")
for label in (
    "SIM TIME",
    "BP · MAP",
    "HR · RHYTHM",
    "SpO₂ · SUPPORT",
    "RR · WORK OF BREATHING",
    "CRT · EXTREMITIES",
    "MENTAL STATUS",
):
    assert label in html
assert "100/60 · MAP 73" in html
assert "162 · AF" in html

print("PASS: v0.8.2 persistent live monitor and immutable post-intervention vitals")
