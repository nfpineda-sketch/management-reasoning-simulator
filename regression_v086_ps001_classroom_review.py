"""Regression coverage for the validated v0.8.6 PS001 classroom trajectory."""

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
assert 'file_name=f"{case_id}_decision_review_v0819.md"' in source
assert '<span class="mt-head-sep">·</span>' in source
assert '<ul class="mt-deltas">' in source

tree = ast.parse(source)
nodes = []
required_assignments = {
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
}
for node in tree.body:
    if isinstance(node, ast.FunctionDef):
        nodes.append(node)
    elif isinstance(node, ast.Assign):
        names = [target.id for target in node.targets if isinstance(target, ast.Name)]
        if any(name in required_assignments for name in names):
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
    "json": __import__("json"),
    "deepcopy": deepcopy,
    "escape": escape,
}
exec(compile(ast.Module(body=nodes, type_ignores=[]), "v086_subset", "exec"), namespace)


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
    assert result.get("executed"), result
    return parsed, result


ENTRIES = (
    (
        "My working model is AF with RVR and impaired peripheral perfusion, but the rhythm may be secondary "
        "to an acute illness rather than the sole cause of instability. My priority is to assess the hemodynamic "
        "phenotype and reversible causes before committing to rate control or cardioversion. Give 500 mL normal "
        "saline, obtain POCUS, lactate, VBG, basic labs, and ask about fever and urinary symptoms. I expect improved "
        "peripheral perfusion without worsening oxygenation or respiratory status. Reassess BP, "
        "HR and rhythm, capillary refill, extremities, mental status, SpO2, work of breathing, and lung findings "
        "in 5 minutes."
    ),
    (
        "The history, elevated inflammatory markers, lactate 4.9 mmol/L, hyperdynamic LV, and small collapsible "
        "IVC suggest urinary-source sepsis with persistent hypovolemia and impaired tissue perfusion. AF with RVR "
        "may be contributing, but it is not yet clearly the primary cause of instability. My priority is source-directed "
        "treatment and further cautious preload optimization before using an AV-nodal blocker. Obtain blood cultures "
        "and urinalysis, administer ceftriaxone 2 g IV, give an additional 500 mL of normal saline, and reassess BP, "
        "HR and rhythm, capillary refill, extremities, mental status, SpO2, work of breathing, and lung findings in "
        "10 minutes. I expect improved peripheral perfusion and possibly a partial reduction in heart rate without "
        "pulmonary congestion."
    ),
    (
        "The urinary source is now supported and antibiotics have been started. After 1000 mL of cumulative fluid, "
        "MAP remains 76 mmHg and mental status is preserved, with slightly warmer extremities but persistent capillary "
        "refill of 4 seconds and AF at 171/min. My working model is sepsis-driven AF with persistent RVR that may now "
        "be contributing to impaired forward flow. My priority is a cautious diagnostic-therapeutic trial of rate control "
        "rather than immediate cardioversion. Give diltiazem 5 mg IV and reassess HR and rhythm, BP and MAP, capillary "
        "refill, extremities, mental status, SpO2, and work of breathing in 5 minutes. I expect a modest reduction in "
        "heart rate without hypotension or worsening tissue perfusion. Do not give additional AV-nodal blocker if MAP "
        "falls below 65 mmHg, mental status worsens, or capillary refill increases."
    ),
    (
        "The heart rate decreased from 171 to 157/min after diltiazem without hypotension or worsening peripheral "
        "perfusion. This suggests that the ventricular response is partly responsive to AV-nodal blockade, although "
        "the persistent capillary refill of 4 seconds indicates that the underlying septic physiology remains active. "
        "My priority is cautious further rate control while preserving blood pressure and tissue perfusion. Give another "
        "diltiazem 5 mg IV and reassess HR and rhythm, BP and MAP, capillary refill, extremities, mental status, SpO2, "
        "and work of breathing in 5 minutes. I expect a further reduction in heart rate without a fall in MAP or worsening "
        "capillary refill."
    ),
    (
        "The ventricular rate has decreased from 171 to 138/min without hypotension, but capillary refill remains 4 "
        "seconds. This suggests that rate reduction alone has not corrected the perfusion abnormality. My priority is "
        "to reassess the septic hemodynamic phenotype before giving more AV-nodal blockade. Repeat POCUS and lactate, "
        "and reassess BP and MAP, HR and rhythm, capillary refill, extremities, mental status, SpO2, work of breathing, "
        "and lung findings in 10 minutes. I expect the heart rate to remain controlled without worsening pressure while "
        "the new data clarify whether further preload support or vasopressor therapy is needed."
    ),
    (
        "Despite substantial rate reduction, perfusion has worsened: MAP is 69 mmHg, capillary refill is 5 seconds, "
        "lactate is 5.0 mmol/L, and the current POCUS demonstrates moderately to severely reduced LV systolic function. "
        "My working model is evolving low-output septic shock, likely compounded by the cumulative hemodynamic effect "
        "of AV-nodal blockade, rather than instability caused primarily by the ventricular rate. My priority is to restore "
        "perfusion pressure without further rate-control medication. Start norepinephrine 0.05 mcg/kg/min and reassess "
        "BP and MAP, HR and rhythm, capillary refill, extremities, mental status, SpO2, and work of breathing in 5 minutes. "
        "I expect improved blood pressure, but I will not consider the intervention successful unless peripheral perfusion "
        "and mental status also stabilize or improve."
    ),
    (
        "Norepinephrine restored arterial pressure, but capillary refill has not improved and the patient is now drowsy "
        "despite a MAP of 85 mmHg. Persistent clinical instability despite adequate pressure raises concern that AF and "
        "loss of effective cardiac filling may still be contributing to low forward flow, even though the ventricular rate "
        "is lower. My priority is to test the contribution of the rhythm while maintaining circulatory support. Perform "
        "synchronized cardioversion with 200 J and reassess BP and MAP, HR and rhythm, capillary refill, extremities, mental "
        "status, SpO2, and work of breathing in 5 minutes. I expect conversion to sinus rhythm; clinical benefit would "
        "require improvement in capillary refill or mental status, not electrical conversion alone."
    ),
    (
        "Cardioversion restored sinus rhythm at 89/min, but capillary refill remains 5 seconds and mental status remains "
        "drowsy despite MAP 88 mmHg. This indicates that electrical conversion alone did not restore forward flow. My "
        "priority is to reassess current ventricular function and tissue perfusion before selecting further hemodynamic "
        "support. Repeat POCUS and lactate, and reassess BP and MAP, HR and rhythm, capillary refill, extremities, mental "
        "status, SpO2, and work of breathing in 10 minutes. I expect the rhythm to remain sinus; persistent LV dysfunction "
        "or rising lactate would support a low-output phenotype requiring flow-directed rather than rate-directed treatment."
    ),
    (
        "Cardioversion restored sinus rhythm, but the current POCUS demonstrates moderately to severely reduced LV "
        "systolic function and lactate has risen to 5.6 mmol/L. My working model is persistent low-output septic shock "
        "despite adequate arterial pressure and rhythm conversion. My priority is to improve forward flow while preserving "
        "MAP and oxygenation. Start dobutamine 2.5 mcg/kg/min, continue the current norepinephrine infusion, repeat lactate "
        "in 10 minutes, and reassess BP and MAP, HR and rhythm, capillary refill, extremities, mental status, SpO2, and work "
        "of breathing in 10 minutes. I expect improved capillary refill, mental status, and lactate without hypotension or "
        "recurrent tachyarrhythmia."
    ),
    (
        "The improvement in capillary refill from 5 to 3 seconds and warmer extremities suggests early forward-flow "
        "recruitment after dobutamine, but persistent drowsiness and lactate 5.8 mmol/L indicate incomplete recovery. My "
        "priority is to distinguish delayed metabolic and neurologic recovery from ongoing low output while avoiding "
        "premature escalation. Continue the current hemodynamic support unchanged. Repeat POCUS and lactate in 10 minutes, "
        "and reassess BP and MAP, HR and rhythm, capillary refill, extremities, mental status, SpO2, and work of breathing "
        "in 10 minutes. I expect sustained peripheral perfusion, improving ventricular function and lactate, and gradual "
        "recovery of mental status without hypotension or recurrent AF."
    ),
    (
        "The fall in lactate from 5.8 to 4.4 mmol/L together with sustained capillary refill of 3 seconds and warmer "
        "extremities indicates improving tissue perfusion despite persistent qualitative LV dysfunction. Mental recovery "
        "remains delayed. My priority is to preserve the current hemodynamic gains and reassess neurologic and metabolic "
        "recovery without escalating support solely because ventricular function remains abnormal on bedside imaging. "
        "Continue the current hemodynamic support unchanged, repeat lactate in 10 minutes, and reassess BP and MAP, HR "
        "and rhythm, capillary refill, extremities, mental status, SpO2, and work of breathing in 10 minutes. I expect "
        "further lactate clearance and gradual improvement in mental status while maintaining sinus rhythm, blood pressure, "
        "and peripheral perfusion."
    ),
)


EXPECTED_STATES = (
    (10, 106, 64, 171, "AF", 4, "Cool", "Alert", 93),
    (20, 102, 63, 171, "AF", 4, "Warmer", "Alert", 93),
    (25, 101, 63, 157, "AF", 4, "Warmer", "Alert", 93),
    (30, 101, 63, 138, "AF", 4, "Warmer", "Alert", 93),
    (40, 94, 57, 126, "AF", 5, "Cool", "Alert", 93),
    (45, 108, 73, 126, "AF", 5, "Cool", "Drowsy", 93),
    (50, 112, 76, 89, "Sinus rhythm", 5, "Cool", "Drowsy", 93),
    (60, 111, 74, 89, "Sinus rhythm", 5, "Cool", "Drowsy", 92),
    (70, 112, 72, 89, "Sinus rhythm", 3, "Warmer", "Drowsy", 92),
    (80, 111, 71, 89, "Sinus rhythm", 3, "Warmer", "Drowsy", 92),
    (90, 110, 71, 89, "Sinus rhythm", 3, "Warm", "Alert", 92),
)


initialize()
for entry, expected in zip(ENTRIES, EXPECTED_STATES):
    execute(entry)
    state = st.session_state.state
    observed = state["observable"]
    actual = (
        state["sim_time"],
        observed["sbp"],
        observed["dbp"],
        observed["hr"],
        observed["rhythm"],
        observed["crt"],
        observed["extremities"],
        observed["mental_status"],
        observed["spo2"],
    )
    assert actual == expected, (len(st.session_state.management_trace), actual, expected)

trace = st.session_state.management_trace
assert len(trace) == 11

# The two reasoning-capture defects found during the manual PS001 review stay fixed.
decision_8_reasoning = trace[7]["reasoning"]
assert decision_8_reasoning["problem_representation"] == "electrical conversion alone did not restore forward flow"
assert decision_8_reasoning["expected_effect"] == "the rhythm to remain sinus"
decision_11_reasoning = trace[10]["reasoning"]
assert decision_11_reasoning["rationale"] == "ventricular function remains abnormal on bedside imaging"
assert "Continue the current" not in decision_11_reasoning["rationale"]

# The validated classroom path reviews rate control, rhythm conversion, and flow support.
items = namespace["_reflect_compare_items"](trace)
assert [item[1] for item in items] == [3, 7, 9], items
assert [item[3] for item in items] == [
    "Rate control as a diagnostic–therapeutic trial",
    "Electrical success versus clinical benefit",
    "Pressure–flow–perfusion adaptation",
]
models = namespace["_expert_models_for_prompts"]("PS001", namespace["_review_prompt_records"](trace))
assert set(models) == {"decision-3", "decision-7", "decision-9"}, models
assert all(len(model.get("cues", [])) == 3 for model in models.values())

# Portable Markdown and copied UI labels retain explicit separators and line structure.
markdown = namespace["_review_markdown"]({
    "simulator": {"version": "0.8.9"},
    "encounter": {"case_id": "PS001", "case_label": "PS001", "closed_time_min": 90},
    "learning_cycle": {"attempt_number": 1, "carry_forward_plan": {}},
    "review_complete": False,
    "management_trace": {"definition": namespace["MANAGEMENT_TRACE_DEFINITION"], "events": trace},
    "decision_review": {"prompts": []},
    "expert_comparison": {"revealed": False, "comparisons": []},
    "adaptation_plan": {},
})
assert "- **Simulator:** Management Reasoning Simulator v0.8.9\n- **Case:** PS001" in markdown
assert "### 00:00 · Decision 1\n\n**Patient state**" in markdown
assert "- **Rhythm:** AF → AF" in markdown
assert "**00:00Decision 1**" not in markdown

print("PASS: v0.8.6 literal PS001 trajectory, reasoning fidelity, classroom review, and readable export")
