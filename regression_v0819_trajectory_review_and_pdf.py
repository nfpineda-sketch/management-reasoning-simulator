"""Regression for trajectory-grounded review, flexible capture, and PDF fidelity."""

import ast
import json
import math
import random
import re
from copy import deepcopy
from html import escape
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader


root = Path(__file__).resolve().parent
source = (root / "app.py").read_text(encoding="utf-8")
assert 'SIMULATOR_VERSION = "0.8.21"' in source
assert "MVP v0.8.21 — dynamic learner-visible ECG with lower-pressure PS001 entry" in source

tree = ast.parse(source)
nodes = []
state_names = {
    "SIMULATOR_VERSION",
    "MANAGEMENT_TRACE_DEFINITION",
    "REVIEW_RESPONSE_FIELDS",
    "ADAPTATION_PLAN_FIELDS",
    "EXPERT_COMPARISON_FIELDS",
    "EXPERT_REASONING_MODELS",
    "INITIAL_STATE",
    "PRESENTATION",
    "PS002_PRESENTATION",
    "CASE_CONFIGS",
    "REASONING_GATE_ACTION_TYPES",
    "REASONING_GATE_FIELD_LABELS",
    "REASONING_GATE_FIELD_STEMS",
    "REASONING_GATE_OVERRIDE",
}
for node in tree.body:
    if isinstance(node, ast.FunctionDef):
        nodes.append(node)
    elif isinstance(node, ast.Assign):
        names = [target.id for target in node.targets if isinstance(target, ast.Name)]
        if any(name in state_names for name in names):
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
    "json": json,
    "deepcopy": deepcopy,
    "escape": escape,
    "BytesIO": BytesIO,
    "__file__": str(root / "app.py"),
}
exec(compile(ast.Module(body=nodes, type_ignores=[]), "v0819_subset", "exec"), namespace)

st.session_state.state = deepcopy(namespace["INITIAL_STATE"])
st.session_state.events = []
st.session_state.management_trace = []


def interpret(text):
    return namespace["clinical_interpreter"](text)


# Free text supplies semantic slots without demanding exact sentence stems.
post_conversion_fluid = interpret(
    "Although the rhythm is now sinus, reduced effective circulating volume may still be "
    "contributing to incomplete perfusion recovery. Give 500 mL normal saline IV. I want "
    "to improve preload and tissue perfusion. I expect improved blood pressure, capillary "
    "refill, and extremity temperature without worsening oxygenation or work of breathing. "
    "Reassess HR and rhythm, BP/MAP, capillary refill, extremities, mental status, SpO2, "
    "and work of breathing in 10 minutes."
)
action_types = {action.get("type") for action in post_conversion_fluid["actions"]}
assert "fluid" in action_types
assert "temperature" not in action_types, post_conversion_fluid
assert post_conversion_fluid["reasoning"]["problem_representation"].lower().startswith("although")

for text, expected_fragment in (
    (
        "Obtain POCUS now to assess LV and RV function, IVC size and respiratory variation, "
        "the pericardium, and lung B-lines before deciding on additional support.",
        "assess lv and rv function",
    ),
    (
        "Obtain basic laboratory tests and lactate now to evaluate organ dysfunction, systemic "
        "inflammation, and the degree of tissue hypoperfusion.",
        "evaluate organ dysfunction",
    ),
    (
        "Obtain urinalysis and chest X-ray now to investigate a urinary or pulmonary infectious source.",
        "investigate a urinary or pulmonary infectious source",
    ),
):
    parsed = interpret(text)
    assert expected_fragment in parsed["reasoning"].get("management_priority", "").lower(), parsed

reassessment = interpret(
    "Reassess BP/MAP, HR and rhythm, capillary refill, extremities, mental status, SpO2, "
    "and work of breathing in 10 minutes."
)
assert not reassessment["reasoning"].get("problem_representation"), reassessment
assert "bp/map" in reassessment["reasoning"].get("reassessment_target", "").lower()
assert any(
    action.get("type") == "reassessment" and action.get("delay_min") == 10
    for action in reassessment["actions"]
), reassessment

late_fluid = interpret(
    "Patient hypotensive with slow perfusion and neurologic dysfunction; urinalysis positive "
    "for infection. Give 2000 cc NS. I want to improve arterial pressure and tissue perfusion. "
    "I expect pressure to increase and perfusion to improve. Reassess perfusion, HR, and BP in 5 minutes."
)
assert late_fluid["reasoning"].get("expected_effect") == "pressure to increase and perfusion to improve", late_fluid

pressors = interpret(
    "Start norepinephrine 0.1 mcg/kg/min and give ceftriaxone 2 g IV. I think this is urinary-source "
    "septic shock with vasoplegia. My priority is to restore perfusion pressure and treat the source. "
    "I expect MAP to increase and peripheral perfusion to stop worsening. Reassess BP/MAP, capillary "
    "refill, extremities, mental status, HR and rhythm, SpO2, and work of breathing in 5 minutes."
)
assert pressors["reasoning"].get("expected_effect") == "MAP to increase and peripheral perfusion to stop worsening", pressors


def snapshot(time_min, sbp, dbp, hr, rhythm, crt, extremities, mental, spo2=93):
    return {
        "case_id": "PS001",
        "sim_time_min": time_min,
        "observable": {
            "sbp": sbp,
            "dbp": dbp,
            "hr": hr,
            "rhythm": rhythm,
            "crt": crt,
            "extremities": extremities,
            "mental_status": mental,
            "spo2": spo2,
            "respiratory_rate": 22,
            "work_of_breathing": "Mildly increased",
        },
        "treatments": {},
    }


def event(decision, before, after, learner_input, actions, summaries, reasoning):
    return {
        "execution_status": "executed",
        "decision_time_min": before["sim_time_min"],
        "response_time_min": after["sim_time_min"],
        "elapsed_minutes": after["sim_time_min"] - before["sim_time_min"],
        "learner_input": learner_input,
        "interpreted_action": actions,
        "action_summaries": summaries,
        "reasoning": reasoning,
        "state_before": before,
        "state_after": after,
        "recognized_future_actions": [],
    }


dummy = event(
    1,
    snapshot(0, 90, 54, 162, "AF", 5, "Cool", "Alert"),
    snapshot(10, 120, 75, 97, "Sinus rhythm", 2, "Warm", "Sedated"),
    "Cardioversion with procedural sedation.",
    [{"type": "procedural_sedation"}, {"type": "cardioversion"}],
    [
        {"support_type": "procedural_sedation", "agents": []},
        {"energy_j": 200},
    ],
    {"management_priority": "restore sinus rhythm and improve forward flow"},
)

trace = [deepcopy(dummy) for _ in range(8)]
trace[1] = event(
    2,
    snapshot(10, 120, 75, 97, "Sinus rhythm", 2, "Warm", "Sedated"),
    snapshot(20, 113, 71, 96, "Sinus rhythm", 2, "Warm", "Sedated"),
    "Give 500 mL normal saline for possible reduced effective circulating volume.",
    [{"type": "fluid", "volume_ml": 500, "fluid_type": "Normal saline"}],
    [{"volume_ml": 500, "fluid_type": "Normal saline"}],
    {
        "problem_representation": "reduced effective circulating volume may contribute to incomplete perfusion recovery",
        "management_priority": "improve preload and tissue perfusion",
        "expected_effect": "improved blood pressure and peripheral perfusion",
        "reassessment_target": "HR and rhythm, BP/MAP, capillary refill, extremities, mental status, SpO2, and work of breathing in 10 minutes",
    },
)
for index in range(2, 6):
    trace[index] = event(
        index + 1,
        snapshot(20 + index, 110 - index, 68 - index, 96, "Sinus rhythm", min(5, index + 1), "Warm", "Alert"),
        snapshot(21 + index, 109 - index, 67 - index, 96, "Sinus rhythm", min(5, index + 1), "Warm", "Alert"),
        "Obtain diagnostic data and reassess.",
        [{"type": "reassessment"}],
        [],
        {"management_priority": "clarify the active physiology", "reassessment_target": "BP and perfusion in 10 minutes"},
    )
trace[6] = event(
    7,
    snapshot(50, 79, 45, 97, "Sinus rhythm", 6, "Cold", "Obtunded"),
    snapshot(55, 84, 48, 96, "Sinus rhythm", 5, "Cool", "Drowsy"),
    "Give 2000 mL normal saline for urinary-source shock and reassess in 5 minutes.",
    [{"type": "fluid", "volume_ml": 2000, "fluid_type": "Normal saline"}],
    [{"volume_ml": 2000, "fluid_type": "Normal saline"}],
    {
        "problem_representation": "urinary-source shock with hypotension and impaired perfusion",
        "management_priority": "improve arterial pressure and tissue perfusion",
        "expected_effect": "pressure to increase and perfusion to improve",
        "reassessment_target": "perfusion, HR, and BP in 5 minutes",
    },
)
trace[7] = event(
    8,
    snapshot(55, 84, 48, 96, "Sinus rhythm", 5, "Cool", "Drowsy"),
    snapshot(60, 102, 61, 95, "Sinus rhythm", 4, "Warmer", "Drowsy"),
    "Start norepinephrine and give ceftriaxone for urinary-source septic shock.",
    [
        {"type": "norepinephrine", "rate": 0.1},
        {"type": "antibiotics", "agent": "ceftriaxone", "dose_g": 2, "route": "IV"},
    ],
    [
        {"support_type": "norepinephrine", "operation": "start", "rate": 0.1, "units": "mcg/kg/min"},
        {"support_type": "antibiotics", "agent_name": "ceftriaxone", "dose_g": 2, "route": "IV"},
    ],
    {
        "problem_representation": "urinary-source septic shock with vasoplegia",
        "management_priority": "restore perfusion pressure and treat the source",
        "expected_effect": "MAP to increase and peripheral perfusion to stop worsening",
        "reassessment_target": "BP/MAP, perfusion, mental status, HR and rhythm in 5 minutes",
    },
)

prompts = [
    {"review_id": f"decision-{decision}", "kind": "decision", "decision": decision, "time": time, "label": "Review", "prompt": "Reflect."}
    for decision, time in ((2, "00:10"), (7, "00:50"), (8, "00:55"))
]
models = namespace["_expert_models_for_prompts"]("PS001", prompts, trace)
assert set(models) == {"decision-2", "decision-7", "decision-8"}, models
assert all(model.get("trajectory_grounded") for model in models.values())
assert models["decision-7"]["source_action_types"] == ["fluid"], models["decision-7"]
assert "cardioversion" not in models["decision-7"]["action"].lower(), models["decision-7"]
assert "79/45" in " ".join(models["decision-7"]["cues"]), models["decision-7"]
assert set(models["decision-8"]["source_action_types"]) == {"antibiotics", "norepinephrine"}

reflection = (
    "Norepinephrine should be titrated while MAP remains below 65 mmHg. If MAP reaches the target "
    "but capillary refill remains above 4 seconds, mental status remains impaired, or lactate fails "
    "to decrease, the hemodynamic phenotype should be reassessed."
)
cue = namespace["_cue_from_priority_trigger"](reflection)
threshold = namespace["_threshold_from_priority_trigger"](reflection)
assert "norepinephrine should be titrated" not in cue.lower(), cue
assert "norepinephrine should be titrated" not in threshold.lower(), threshold
assert "map remains below 65" in cue.lower(), cue
assert "capillary refill remains above 4" in cue.lower(), cue

responses = {
    prompt["review_id"]: {
        "working_model_update": "The active physiology changed over the trajectory.",
        "priority_trigger": reflection,
        "alternative_action": "Use concurrent pressure and source-directed support with frequent reassessment.",
        "expected_response_reassessment": "Expect MAP and perfusion to improve; reassess BP/MAP, CRT, mental status, and lactate.",
    }
    for prompt in prompts
}
comparisons = {
    prompt["review_id"]: {
        "alignment": "I linked the action to an explicit physiologic goal.",
        "adjustment": "I will define benefit, harm, and escalation thresholds before treatment.",
    }
    for prompt in prompts
}
plan = {
    "cue": cue,
    "threshold": threshold,
    "next_priority": "Restore pressure and forward flow while treating the source.",
    "alternative_action": "Use norepinephrine and ceftriaxone concurrently with reassessed fluid aliquots.",
    "expected_effect": "Restore MAP above 65 mmHg and stabilize bedside perfusion.",
    "reassessment_plan": "Reassess BP/MAP, CRT, extremities, mental status, HR, rhythm, and breathing in 5 minutes; repeat lactate in 10-20 minutes.",
}
payload = namespace["_review_payload"](
    "PS001 · Tachyarrhythmia in an Acutely Ill Patient",
    60,
    trace,
    trace[-1]["state_after"],
    prompts,
    responses,
    plan,
    comparisons,
    True,
)
comparison_records = payload["expert_comparison"]["comparisons"]
assert [record["review_id"] for record in comparison_records] == ["decision-2", "decision-7", "decision-8"]

pdf_bytes = namespace["_review_pdf"](payload)
assert pdf_bytes.startswith(b"%PDF-")
assert b"/FontFile2" in pdf_bytes, "PDF must embed the bundled TrueType font"
reader = PdfReader(BytesIO(pdf_bytes))
pdf_text = "\n".join(page.extract_text() or "" for page in reader.pages)
for heading in ("Decision 2", "Decision 7", "Decision 8", "Expert Comparison", "Prospective Adaptation Plan"):
    assert heading in pdf_text, heading
assert "synchronized cardioversion at 200 J while continuing pressure support" not in pdf_text

print("PASS: v0.8.19 grounds every comparison in the actual trajectory and embeds PDF fonts")
