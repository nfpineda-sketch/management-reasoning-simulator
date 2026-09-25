
import re
import math
import random
import json
import os
import hmac
from io import BytesIO
from html import escape
from copy import deepcopy
import streamlit as st

SIMULATOR_VERSION = "0.24.13-clinical-encounter"

import importlib
import generation_reload as _generation_reload
# Upgrade cached bootstrap dependency lists under their existing shared lock.
with _generation_reload._LOCK:
    if getattr(_generation_reload, 'RELOAD_VERSION', None) != SIMULATOR_VERSION.split('-')[0]:
        importlib.reload(_generation_reload)
    _generation_reload.refresh_generation_modules(SIMULATOR_VERSION.split("-")[0])
    _generation_reload.refresh_visual_modules()

from curriculum import CHALLENGES
import patient_appearance as _appearance
import encounter_generator as _encounter_generator
if getattr(_encounter_generator, "GENERATOR_VERSION", "") != SIMULATOR_VERSION.split("-")[0]:
    importlib.reload(_encounter_generator)
import clinical_scene as _clinical_scene
import resuscitation_room as _room
from resuscitation_room import render_room, render_bedside_tools
from encounter_workspace import render_encounter_workspace
from ai_interpreter import AIInterpretationError, normalize_with_ai
from account_portal import accounts_enabled, require_account_access, render_account_sidebar
import curriculum_runtime as _curriculum_runtime
if getattr(_curriculum_runtime, "RUNTIME_VERSION", "") != SIMULATOR_VERSION.split("-")[0]:
    importlib.reload(_curriculum_runtime)
from curriculum_runtime import (
    save_session, render_dashboard, start_encounter, render_learning_focus,
    return_to_dashboard,
)

st.set_page_config(page_title=f"Management Reasoning Simulator — Clinical encounter v{SIMULATOR_VERSION.split('-')[0]}", page_icon="🩺", layout="wide")


def require_shared_password():
    """Fail-closed shared-password gate backed by Streamlit Secrets."""
    try:
        configured_password = str(st.secrets.get("APP_PASSWORD", "")).strip()
    except Exception:
        configured_password = ""

    if not configured_password:
        st.title("Management Reasoning Simulator")
        st.error("Access is temporarily closed. The application password has not been configured.")
        st.stop()

    if st.session_state.get("_shared_access_granted", False):
        return

    st.title("Management Reasoning Simulator")
    st.caption("Restricted access")
    with st.form("shared_password_form"):
        entered_password = st.text_input("Password", type="password")
        submitted_password = st.form_submit_button("Enter", type="primary")

    if submitted_password:
        if hmac.compare_digest(entered_password, configured_password):
            st.session_state["_shared_access_granted"] = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()


ACCOUNT_CONTEXT = require_account_access() if accounts_enabled() else None
if ACCOUNT_CONTEXT is None:
    require_shared_password()
else:
    render_account_sidebar(ACCOUNT_CONTEXT)


def faculty_access():
    context = globals().get("ACCOUNT_CONTEXT")
    return bool(context and context["user"]["role"] in {"faculty", "admin"})


def rerun_app():
    context = globals().get("ACCOUNT_CONTEXT")
    if context:
        save_session(context)
    st.rerun()

# Historical source markers retained so the v0.8.21 regression lineage remains auditable.
LEGACY_REGRESSION_VERSION_MARKER = 'SIMULATOR_VERSION = "0.8.21"'
LEGACY_REGRESSION_CAPTION = "MVP v0.8.21 — dynamic learner-visible ECG with lower-pressure PS001 entry"
MANAGEMENT_TRACE_DEFINITION = (
    "Management Trace is a time-resolved record of how a learner translates patient state into "
    "management priorities and actions, anticipates their effects, observes the resulting patient "
    "response, and adapts subsequent management."
)

REVIEW_RESPONSE_FIELDS = (
    ("working_model_update", "How has your working model changed?"),
    ("priority_trigger", "What finding or threshold should influence your next priority?"),
    ("alternative_action", "What alternative action would you take?"),
    ("expected_response_reassessment", "What response would you expect, and what would you reassess?"),
)

ADAPTATION_PLAN_FIELDS = (
    ("cue", "Clinical cue to watch"),
    ("threshold", "Threshold for changing course"),
    ("next_priority", "Next management priority"),
    ("alternative_action", "Alternative action"),
    ("expected_effect", "Expected effect"),
    ("reassessment_plan", "Reassessment target and timing"),
)

EXPERT_COMPARISON_FIELDS = (
    ("alignment", "Where did your reasoning align with this model?"),
    ("adjustment", "What will you change or preserve next time?"),
)

# Faculty-validation drafts for the validated PS001 and PS002 trajectories in
# this MVP. Each is one defensible expert approach, not an answer key and not a
# claim that other safe strategies are incorrect.
EXPERT_REASONING_MODELS = {
    "PS001": {
        3: {
            "framing": (
                "AF with RVR is occurring in urinary-source sepsis with incomplete tissue perfusion. "
                "The rhythm may now impair filling and forward flow, but it has not been established as "
                "the sole or primary cause of instability."
            ),
            "priority": (
                "Use a small, closely monitored AV-nodal-blockade trial to test rate contribution while "
                "protecting arterial pressure and tissue perfusion."
            ),
            "cues": [
                "MAP is 76 mmHg and mental status is alert after source treatment and 1000 mL cumulative fluid.",
                "AF remains approximately 171/min despite initial resuscitation.",
                "Capillary refill remains 4 seconds and lactate is 4.9 mmol/L, so perfusion is not normal.",
            ],
            "action": (
                "Give a cautious diltiazem 5 mg IV trial, reassess in 5 minutes, and do not automatically "
                "repeat it if MAP, mental status, or peripheral perfusion worsens."
            ),
            "tradeoff": (
                "Slowing the ventricular response may improve filling, but negative inotropy or vasodilation "
                "can worsen forward flow in evolving septic or myocardial dysfunction."
            ),
            "reassessment": (
                "HR and rhythm, BP/MAP, capillary refill, extremities, mental status, SpO2, and work of breathing."
            ),
        },
        7: {
            "framing": (
                "Norepinephrine restored arterial pressure, but capillary refill and mental status did not "
                "improve. AF at a lower rate may still reduce filling, yet adequate MAP has not restored tissue flow."
            ),
            "priority": (
                "Test the causal contribution of the rhythm while maintaining circulatory support, and define "
                "success by clinical perfusion rather than electrical conversion alone."
            ),
            "cues": [
                "MAP is 85 mmHg on norepinephrine, while capillary refill remains 5 seconds.",
                "The patient is now drowsy despite restored pressure.",
                "AF persists near 126/min after rate control and the current POCUS shows reduced LV function.",
            ],
            "action": (
                "Perform synchronized cardioversion at 200 J while continuing pressure support, then reassess "
                "rhythm and clinical perfusion within 5 minutes."
            ),
            "tradeoff": (
                "Cardioversion may restore atrial contribution and filling, but electrical success may not "
                "reverse sepsis-driven low output and exposes the patient to procedural and sedation risk."
            ),
            "reassessment": (
                "Rhythm and HR, BP/MAP, capillary refill, extremity temperature, mental status, SpO2, and work of breathing."
            ),
        },
        9: {
            "framing": (
                "Sinus rhythm and adequate MAP coexist with cool extremities, prolonged capillary refill, "
                "drowsiness, reduced LV systolic function, and rising lactate. This is pressure–flow–perfusion "
                "dissociation rather than persistent instability explained by tachyarrhythmia alone."
            ),
            "priority": (
                "Support forward flow while preserving arterial pressure and watching for recurrent tachyarrhythmia "
                "or deterioration in oxygenation."
            ),
            "cues": [
                "Cardioversion produced sinus rhythm near 89/min without restoring capillary refill or mental status.",
                "MAP remains approximately 86 mmHg on norepinephrine.",
                "POCUS shows moderately to severely reduced LV systolic function and lactate has risen to 5.6 mmol/L.",
            ],
            "action": (
                "Start low-dose dobutamine while continuing norepinephrine, then follow bedside perfusion, rhythm, "
                "pressure, oxygenation, and the planned lactate trend."
            ),
            "tradeoff": (
                "Dobutamine may improve cardiac output but can cause vasodilation, hypotension, or recurrent "
                "tachyarrhythmia; lactate and mental status may also lag behind early peripheral improvement."
            ),
            "reassessment": (
                "BP/MAP, HR and rhythm, capillary refill, extremities, mental status, SpO2 and work of breathing "
                "within 10 minutes, with lactate and repeat cardiac imaging interpreted as trends."
            ),
        },
    },
    "PS002": {
        2: {
            "framing": (
                "The pressure response to fluid is modest, but tissue-perfusion markers and severe "
                "respiratory distress show that circulatory and respiratory failure remain active."
            ),
            "priority": (
                "Protect perfusion while escalating respiratory support and anticipate the reduction "
                "in venous return caused by positive pressure."
            ),
            "cues": [
                "Capillary refill remains 4 seconds and lactate is 4.7 mmol/L.",
                "Tachycardia and hypotension persist despite partial fluid responsiveness.",
                "Severe work of breathing and hypoxemia still require escalation.",
            ],
            "action": (
                "Avoid routine additional fluid, prepare or start norepinephrine before or with NIV, "
                "and reassess both perfusion and respiratory response within about 5 minutes."
            ),
            "tradeoff": (
                "NIV may improve oxygenation and work of breathing while simultaneously worsening "
                "preload and tissue perfusion."
            ),
            "reassessment": (
                "BP/MAP, capillary refill, extremity temperature, mental status, SpO2, and work of breathing."
            ),
        },
        9: {
            "framing": (
                "An SpO2 of 93% on FiO2 60% does not represent normal gas exchange. Significant "
                "hypoxemic respiratory failure coexists with worsening shock and pressure–flow dissociation."
            ),
            "priority": (
                "Reassess the hemodynamic phenotype and the circulatory burden of ventilation before "
                "assuming that more vasoconstriction is the best next intervention."
            ),
            "cues": [
                "P/F ratio is approximately 125 despite an apparently acceptable SpO2.",
                "Capillary refill, extremity temperature, and lactate worsen despite an acceptable MAP.",
                "High PEEP may contribute to impaired venous return or forward flow.",
            ],
            "action": (
                "Repeat focused cardiac and lung ultrasound, verify treatment delivery and trends, and "
                "use the reassessed phenotype to choose the next support change."
            ),
            "tradeoff": (
                "Further norepinephrine may raise arterial pressure without restoring tissue flow; reducing "
                "PEEP may help circulation but can worsen oxygenation."
            ),
            "reassessment": (
                "BP/MAP, capillary refill, extremities, SpO2, ventilator interaction, focused POCUS, and lactate trend."
            ),
        },
        11: {
            "framing": (
                "The available POCUS does not show RV dilation or diffuse congestion and the LV is preserved "
                "to hyperdynamic, yet cold shock persists. Forward flow and ventilator burden remain plausible targets."
            ),
            "priority": (
                "Improve tissue perfusion while preserving oxygenation and retain the ability to identify "
                "which intervention caused the response."
            ),
            "cues": [
                "Persistent cold extremities, prolonged capillary refill, and rising lactate indicate inadequate tissue flow.",
                "Minimal MAP response to norepinephrine suggests pressure alone is not solving perfusion.",
                "Preserved or hyperdynamic LV function and absent RV dilation or diffuse B-lines refine the phenotype.",
            ],
            "action": (
                "Verify delivery and measurements, reduce excessive intrathoracic-pressure burden with close "
                "oxygenation monitoring, and test vasoactive or inotropic support sequentially when feasible."
            ),
            "tradeoff": (
                "Changing PEEP, norepinephrine, and dobutamine simultaneously may be clinically necessary, "
                "but it reduces causal attribution and can trade perfusion improvement against oxygenation."
            ),
            "reassessment": (
                "BP/MAP, capillary refill, extremities, SpO2, cardiac function, ventilator interaction within "
                "about 5 minutes, and lactate at the planned interval."
            ),
        },
    }
}

INITIAL_STATE = {
    "case_id": "PS001",
    "sim_time": 0,
    "seed": 17,
    "hidden": {
        "effective_volume": 0.35,
        "vasomotor_tone": 0.40,
        "tissue_perfusion": 0.35,
        "sympathetic_drive": 0.85,
        "cardiac_function": 0.80,
        "inflammatory_drive": 0.85,
        # Additional case-specific distributive/vasoplegic physiology. Zero in
        # PS001; PS002 uses it to keep the displayed shock state aligned with the
        # coupled engine instead of spontaneously normalizing on the first tick.
        "vasoplegia_severity": 0.0,
        "af_burden": 0.70,
        "af_causal_weight": 0.25,
        "minutes_since_cardioversion": None,
        # Dynamic electrophysiology / pharmacology state.
        "af_recurrence_pressure": 0.0,
        # Electrical stability acquired after successful cardioversion.
        # This decays gradually; recurrence requires both loss of stability and
        # persistent AF substrate rather than an isolated random minute.
        "sinus_stability": 0.0,
        "metoprolol_effect": 0.0,
        "propranolol_effect": 0.0,
        "metoprolol_depot": 0.0,
        "propranolol_depot": 0.0,
        "diltiazem_effect": 0.0,
        "diltiazem_depot": 0.0,
        "amiodarone_effect": 0.0,
        "amiodarone_depot": 0.0,
        # Transient effect-site signal for executable procedural sedation.
        # It is separate from neurologic injury and decays after administration.
        "procedural_sedation_effect": 0.0,
        "procedural_sedation_minutes": 0.0,
        "pulmonary_congestion": 0.05,
        # Patient-specific fluid phenotype. These are hidden engine variables.
        # PS001: 70 y/o with preserved LV systolic function, but age/comorbidity
        # reduce reserve relative to a young healthy adult.
        "fluid_responsiveness": 0.95,
        "fluid_tolerance": 0.58,
        "fluid_load": 0.00,
        # v0.6 preload/fluid-responsiveness state.
        # effective_intravascular_fluid is the currently retained crystalloid effect,
        # normalized to the size of the patient's circulating-volume deficit.
        "effective_intravascular_fluid": 0.0,
        # Fluid that has redistributed out of the useful intravascular compartment.
        # This is tracked separately so waning preload benefit does not make the
        # administered fluid disappear from the physiology engine.
        "extravascular_fluid_burden": 0.0,
        "preload_state": 0.35,
        "preload_responsiveness": 0.88,
        "afterload_factor": 0.40,
        # v0.6.0.3: continuous right-side Frank-Starling / hydrostatic overload state.
        "overfill_burden": 0.00,
        "respiratory_failure_severity": 0.00,
        # Case-level non-hydrostatic respiratory burden (0 in PS001).
        "primary_respiratory_burden": 0.00,
        "furosemide_effect": 0.0,
        "nitroglycerin_effect": 0.0,
        "global_perfusion_failure": 0.00,
        "peri_arrest_risk": 0.00,
        "cardiac_arrest": False,
        # v0.5 coupled state-engine variables.
        "hemodynamic_reserve": 0.72,
        "stroke_volume_efficiency": 0.72,
        "oxygen_delivery": 0.42,
        "vascular_support": 0.40,
        "cardiac_output_index": 0.46,
        "diastolic_filling_efficiency": 0.60,
        "rate_output_efficiency": 0.72,
        "contractile_reserve": 1.0,
        "low_flow_burden": 0.0,
        # Minutes of sustained adequate perfusion pressure. This is deliberately
        # separate from MAP itself: pressure can recover before the microcirculation
        # and cerebral function recover.
        "adequate_perfusion_minutes": 0.0,
        "cerebral_recovery_minutes": 0.0,
        # v0.6.0.16: sustained peripheral recovery is tracked separately from
        # instantaneous peripheral flow so extremity temperature can lag CRT.
        "peripheral_recovery_minutes": 0.0,
        # v0.6.0.11: pressure, forward flow, and tissue perfusion are explicit
        # longitudinally coupled but non-equivalent states.
        # Match the deliberately lower learner-visible PS001 entry pressure.
        "effective_map": 66.0,
        "pressure_support_state": 0.0,
        "forward_flow_state": 0.46,
        "dobutamine_effect": 0.0,
        "dobutamine_minutes": 0.0,
        "terminal_collapse": False,
    },
    "observable": {
        "sbp": 90,
        "dbp": 54,
        "hr": 162,
        "rhythm": "AF",
        "spo2": 93,
        "crt": 5,
        "mental_status": "Alert",
        "extremities": "Cool",
        "work_of_breathing": "Mildly increased",
        "respiratory_rate": 22,
        "pulse_present": True,
        "temperature_c": 37.1,
    },
    "diagnostics": {
        "pocus": None,
        "lactate": None,
        "vbg": None,
        "abg": None,
        "basic_labs": None,
    },
    # Learner-visible continuity metadata for ongoing supports. Clinical state
    # remains in treatments; this records when each support began and last changed.
    "treatment_timeline": {},
    "treatments": {
        "cumulative_crystalloid_ml": 0,
        "oxygen": False,
        "antibiotics": False,
        "norepinephrine": False,
        "norepinephrine_rate": 0.0,
        "norepinephrine_units": None,
        "dobutamine": False,
        "dobutamine_rate": 0.0,
        "dobutamine_units": "mcg/kg/min",
        "oxygen_device": None,
        "oxygen_flow_lpm": 0.0,
        "diltiazem_total_mg": 0.0,
        "amiodarone_total_mg": 0.0,
        "metoprolol_total_mg": 0.0,
        "propranolol_total_mg": 0.0,
        "cardioversions": 0,
        "procedural_sedations": 0,
        "etomidate_total_mg": 0.0,
        "midazolam_total_mg": 0.0,
        "last_procedural_sedation": [],
        "furosemide_total_mg": 0.0,
        "nitroglycerin": False,
        "nitroglycerin_rate_mcg_min": 0.0,
        "niv": False,
        "niv_mode": None,
        "niv_pressure_cmh2o": 0.0,
        "niv_ipap_cmh2o": None,
        "niv_epap_cmh2o": None,
        "niv_fio2_percent": None,
        "invasive_ventilation": False,
        "ventilator_mode": None,
        "ventilator_fio2_percent": None,
        "ventilator_peep_cmh2o": None,
        "airway_prepared": False,
        "disposition": None,
    },
}

PRESENTATION = (
    "70-year-old man with hypertension and type 2 diabetes presents with dizziness, "
    "fatigue, and exertional dyspnea beginning sometime this morning. He cannot identify "
    "the exact onset. He felt normal yesterday and was at his usual baseline. He is alert "
    "and conversant but appears uncomfortable. BP is 90/54 mmHg. Capillary refill is approximately 5 seconds "
    "and his distal extremities are cool. A 12-lead ECG has been obtained and is available "
    "for review."
)


def build_ps002_state():
    """A second clinical surface using the same longitudinal decision-response engine."""
    state = deepcopy(INITIAL_STATE)
    state["case_id"] = "PS002"
    state["seed"] = 29
    h = state["hidden"]
    h.update({
        "effective_volume": 0.42,
        "vasomotor_tone": 0.34,
        "tissue_perfusion": 0.40,
        "sympathetic_drive": 0.90,
        "cardiac_function": 0.86,
        "inflammatory_drive": 0.92,
        "vasoplegia_severity": 1.0,
        "af_burden": 0.0,
        "af_causal_weight": 0.0,
        "sinus_stability": 1.0,
        "pulmonary_congestion": 0.06,
        "primary_respiratory_burden": 0.66,
        "respiratory_failure_severity": 0.58,
        "fluid_responsiveness": 0.72,
        "fluid_tolerance": 0.48,
        "preload_state": 0.42,
        "preload_responsiveness": 0.68,
        "afterload_factor": 0.34,
        "hemodynamic_reserve": 0.60,
        "stroke_volume_efficiency": 0.76,
        "oxygen_delivery": 0.34,
        "vascular_support": 0.34,
        "cardiac_output_index": 0.72,
        "forward_flow_state": 0.72,
        "effective_map": 65.0,
    })
    state["observable"].update({
        "sbp": 88, "dbp": 54, "hr": 124, "rhythm": "Sinus rhythm",
        "spo2": 86, "crt": 4, "mental_status": "Alert", "extremities": "Warm",
        "work_of_breathing": "Markedly increased", "respiratory_rate": 32,
        "pulse_present": True,
        "temperature_c": 38.6,
    })
    return state

PS002_PRESENTATION = (
    "64-year-old woman with hypertension presents with rapidly progressive shortness of breath, "
    "weakness, and lightheadedness over the past day. She is alert and speaking in short phrases. "
    "Respiratory rate is 32/min with markedly increased work of breathing. SpO₂ is 86% on room air. "
    "Capillary refill is approximately 4 seconds; her extremities are warm. BP is 88/54 mmHg and "
    "HR is 124/min. There is no obvious external bleeding. The cause of her "
    "respiratory and hemodynamic compromise is not yet established."
)

CASE_CONFIGS = {
    "PS001 · Tachyarrhythmia in an Acutely Ill Patient": {
        "id": "PS001", "state_factory": lambda: deepcopy(INITIAL_STATE), "presentation": PRESENTATION
    },
    "PS002 · Acute Dyspnea with Shock": {
        "id": "PS002", "state_factory": build_ps002_state, "presentation": PS002_PRESENTATION
    },
}

def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))

def _default_challenge():
    """The challenge the picker opens on.

    A local switch for playing one family repeatedly: the faculty restarts the
    offline server on the challenge they are working through instead of choosing
    it again after every restart. Unset, or set to something that is not a
    challenge, it is the first-year problem the app has always opened on.
    """
    choice = os.environ.get("MRS_DEFAULT_CHALLENGE", "").strip()
    return choice if choice in CHALLENGES else "R1-05"


def reset_session():
    for key in list(st.session_state):
        if str(key).startswith("_learner_trace_"):
            del st.session_state[key]
    st.session_state.started = False
    st.session_state.selected_case = _default_challenge()
    st.session_state.state = deepcopy(INITIAL_STATE)
    st.session_state.events = []
    st.session_state.history = []
    # v0.6.0.21: structured Management Trace event log. This is intentionally
    # separate from the learner-facing narrative event stream so the encounter UI
    # remains unchanged while each decision can later support review/comparison.
    st.session_state.management_trace = []
    st.session_state.encounter_ended = False
    st.session_state.encounter_closed_trace = None
    st.session_state.encounter_closed_events = None
    st.session_state.encounter_closed_state = None
    st.session_state.encounter_closed_time_min = None
    st.session_state.review_prompts = []
    st.session_state.decision_review = {}
    st.session_state.adaptation_plan = {}
    st.session_state.adaptation_plan_user_edited = {}
    st.session_state.review_completed = False
    st.session_state.review_stage = "decision"
    st.session_state.active_review_index = 0
    st.session_state.active_comparison_index = 0
    st.session_state.review_autosave_revision = 0
    st.session_state.expert_comparison_unlocked = False
    st.session_state.precomparison_decision_review = {}
    st.session_state.expert_comparison_responses = {}
    st.session_state.attempt_number = 1
    st.session_state.carry_forward_plan = {}
    st.session_state.prior_attempt_summary = None
    st.session_state.prior_attempt_record = None
    st.session_state.last_parse = None
    st.session_state.rng_counter = 0
    st.session_state.pending_action = None
    st.session_state.pending_bundle = None
    st.session_state.pending_reasoning = None
    st.session_state.reasoning_gate_counter = 0
    st.session_state.last_executed_action = None
    # A new encounter gets a new budget, and only a new encounter does.
    st.session_state.ai_calls_spent = 0
    st.session_state.ai_call_ledger = []

if "started" not in st.session_state:
    reset_session()

# Hot-reload compatibility for a v0.7.14 session that was already open when the
# compact review state was introduced.
for _key, _default in {
    "adaptation_plan_user_edited": {},
    "review_stage": "decision",
    "active_review_index": 0,
    "active_comparison_index": 0,
    "review_autosave_revision": 0,
    "expert_comparison_unlocked": False,
    "precomparison_decision_review": {},
    "expert_comparison_responses": {},
    "attempt_number": 1,
    "carry_forward_plan": {},
    "prior_attempt_summary": None,
    "prior_attempt_record": None,
    "pending_reasoning": None,
    "ai_calls_spent": 0,
    "ai_call_ledger": [],
    "reasoning_gate_counter": 0,
}.items():
    if _key not in st.session_state:
        st.session_state[_key] = deepcopy(_default)

def rng():
    seed = st.session_state.state["seed"] + st.session_state.rng_counter * 997
    st.session_state.rng_counter += 1
    return random.Random(seed)

def _snapshot_respiratory_support(state):
    """Return only the respiratory support currently visible to the learner."""
    tr = state.get("treatments", {}) or {}
    if tr.get("invasive_ventilation"):
        mode = tr.get("ventilator_mode") or "VC/AC"
        fio2 = tr.get("ventilator_fio2_percent") or 40.0
        peep = tr.get("ventilator_peep_cmh2o") or 5.0
        return f"{mode} · FiO₂ {fio2:g}% · PEEP {peep:g}"
    if tr.get("niv"):
        fio2 = tr.get("niv_fio2_percent")
        fio = f" · FiO₂ {fio2:g}%" if fio2 is not None else ""
        if (
            tr.get("niv_mode") == "BiPAP"
            and tr.get("niv_ipap_cmh2o") is not None
            and tr.get("niv_epap_cmh2o") is not None
        ):
            return f"BiPAP {tr.get('niv_ipap_cmh2o'):g}/{tr.get('niv_epap_cmh2o'):g}{fio}"
        return f"{tr.get('niv_mode') or 'NIV'} {tr.get('niv_pressure_cmh2o', 0):g}{fio}"
    if tr.get("oxygen"):
        return f"{tr.get('oxygen_device')} {tr.get('oxygen_flow_lpm'):g} L/min"
    return "Room air"


def learner_vitals_snapshot(state):
    """Freeze the learner-visible patient state without private engine variables."""
    o = state.get("observable", {}) or {}
    pulse_present = bool(o.get("pulse_present", True))
    sbp = o.get("sbp")
    dbp = o.get("dbp")
    map_value = None
    if pulse_present and sbp is not None and dbp is not None:
        map_value = int(round((float(sbp) + 2.0 * float(dbp)) / 3.0))
    return {
        "sim_time_min": int(state.get("sim_time", 0)),
        "pulse_present": pulse_present,
        "sbp": sbp,
        "dbp": dbp,
        "map": map_value,
        "hr": o.get("hr"),
        "rhythm": o.get("rhythm"),
        "spo2": o.get("spo2"),
        "respiratory_support": _snapshot_respiratory_support(state),
        "respiratory_rate": o.get("respiratory_rate"),
        "work_of_breathing": o.get("work_of_breathing"),
        "crt": o.get("crt"),
        "extremities": o.get("extremities"),
        "mental_status": o.get("mental_status"),
    }


def add_event(kind, text, time=None):
    if time is None:
        time = st.session_state.state["sim_time"]
    event = {"kind": kind, "time": int(time), "text": text}
    if kind == "clinical_update":
        # A response card must remain a historical snapshot. It must not silently
        # acquire the newest vitals when a later decision changes the patient.
        event["learner_vitals"] = learner_vitals_snapshot(st.session_state.state)
    st.session_state.events.append(event)

def sim_time_label(minutes):
    h = minutes // 60
    m = minutes % 60
    return f"{h:02d}:{m:02d}"

def management_state_snapshot(state):
    """Return a compact, review-ready snapshot of the longitudinal patient state.

    Pressure, forward flow, and tissue perfusion are stored explicitly rather than
    inferred from one another. Treatment state is copied so later review can
    reconstruct exactly what support was active at each decision point.
    """
    o = state.get("observable", {})
    h = state.get("hidden", {})
    tr = state.get("treatments", {})
    return {
        "case_id": state.get("case_id"),
        "encounter_variant": (state.get("encounter_spec") or {}).get("generator_version"),
        "encounter_event_count": len(st.session_state.get("events") or []),
        "sim_time_min": int(state.get("sim_time", 0)),
        "observable": {
            "sbp": o.get("sbp"),
            "dbp": o.get("dbp"),
            "hr": o.get("hr"),
            "rhythm": o.get("rhythm"),
            "spo2": o.get("spo2"),
            "crt": o.get("crt"),
            "mental_status": o.get("mental_status"),
            "extremities": o.get("extremities"),
            "respiratory_rate": o.get("respiratory_rate"),
            "work_of_breathing": o.get("work_of_breathing"),
            "pulse_present": o.get("pulse_present"),
        },
        "physiology": {
            "effective_map": h.get("effective_map"),
            "pressure_support_state": h.get("pressure_support_state"),
            "forward_flow_state": h.get("forward_flow_state"),
            "cardiac_output_index": h.get("cardiac_output_index"),
            "tissue_perfusion": h.get("tissue_perfusion"),
            "low_flow_burden": h.get("low_flow_burden"),
            "pulmonary_congestion": h.get("pulmonary_congestion"),
            "respiratory_failure_severity": h.get("respiratory_failure_severity"),
        },
        "diagnostics": deepcopy(state.get("diagnostics", {})),
        "treatment_timeline": deepcopy(state.get("treatment_timeline", {})),
        "treatments": {
            "norepinephrine": bool(tr.get("norepinephrine")),
            "norepinephrine_rate": tr.get("norepinephrine_rate", 0.0),
            "norepinephrine_units": tr.get("norepinephrine_units"),
            "dobutamine": bool(tr.get("dobutamine")),
            "dobutamine_rate": tr.get("dobutamine_rate", 0.0),
            "dobutamine_units": tr.get("dobutamine_units"),
            "nitroglycerin": bool(tr.get("nitroglycerin")),
            "nitroglycerin_rate_mcg_min": tr.get("nitroglycerin_rate_mcg_min", 0.0),
            "oxygen": bool(tr.get("oxygen")),
            "oxygen_device": tr.get("oxygen_device"),
            "oxygen_flow_lpm": tr.get("oxygen_flow_lpm", 0.0),
            "niv": bool(tr.get("niv")),
            "niv_mode": tr.get("niv_mode"),
            "niv_pressure_cmh2o": tr.get("niv_pressure_cmh2o", 0.0),
            "niv_ipap_cmh2o": tr.get("niv_ipap_cmh2o"),
            "niv_epap_cmh2o": tr.get("niv_epap_cmh2o"),
            "niv_fio2_percent": tr.get("niv_fio2_percent"),
            "invasive_ventilation": bool(tr.get("invasive_ventilation")),
            "bag_mask": bool(tr.get("bag_mask")),
            "ventilator_mode": tr.get("ventilator_mode"),
            "ventilator_fio2_percent": tr.get("ventilator_fio2_percent"),
            "ventilator_peep_cmh2o": tr.get("ventilator_peep_cmh2o"),
            "airway_prepared": bool(tr.get("airway_prepared")),
            "disposition": tr.get("disposition"),
            "cumulative_crystalloid_ml": tr.get("cumulative_crystalloid_ml", 0),
            "total_crystalloid_ml": tr.get("total_crystalloid_ml", 0),
            "packed_red_cells_units": tr.get("packed_red_cells_units", 0),
            "furosemide_total_mg": tr.get("furosemide_total_mg", 0.0),
            "cardioversions": tr.get("cardioversions", 0),
            "procedural_sedations": tr.get("procedural_sedations", 0),
            "etomidate_total_mg": tr.get("etomidate_total_mg", 0.0),
            "midazolam_total_mg": tr.get("midazolam_total_mg", 0.0),
            "last_procedural_sedation": deepcopy(tr.get("last_procedural_sedation", [])),
        },
    }


def observable_state_changed(before, after):
    """Return whether a learner-visible physiologic variable changed."""
    before_observable = (before or {}).get("observable", {}) or {}
    after_observable = (after or {}).get("observable", {}) or {}
    keys = (
        "sbp", "dbp", "hr", "rhythm", "spo2", "crt", "mental_status",
        "extremities", "respiratory_rate", "work_of_breathing", "pulse_present",
    )
    return any(before_observable.get(key) != after_observable.get(key) for key in keys)

def _pending_results_now():
    """Studies requested and not back yet, for whichever engine is running."""
    state = st.session_state.get("state") or {}
    if not state.get("engine_family"):
        return []
    try:
        from family_engine import pending_results
        return pending_results(state)
    except Exception:
        return []


def spend_clinical_time(minutes, *, activity, request, response=""):
    """Let an information activity cost what it costs, and record it.

    Asking the patient a question and examining them are clinical activities.
    Until 2026-09-23 they cost nothing: the clock did not move, the illness did
    not move, and a patient who was unstable and untreated stayed exactly as
    unstable however long the resident spent gathering information.

    The minutes are real and the patient runs through them on the same temporal
    engine as any order. Nothing here makes a patient worse *because* a question
    was asked: what happens in the interval is whatever that case's physiology
    does in an interval of that length.
    """
    state = st.session_state.get("state") or {}
    if not state.get("engine_family") or int(minutes or 0) <= 0:
        return None
    from family_engine import advance_clinical_time, pending_results

    before = management_state_snapshot(state)
    started = int(state.get("sim_time", 0))
    result = advance_clinical_time(state, minutes, label=activity)
    after = management_state_snapshot(st.session_state.state)
    for summary in result.get("action_summaries", []) or []:
        label = str(summary.get("label") or "")
        if summary.get("type") == "diagnostic":
            add_event("diagnostic_result", format_diagnostic_summary(summary))
        elif label:
            add_event("clinical_update", label)
    record_information_activity(activity, request, response, started, result, before, after)
    return result


def record_information_activity(activity, request, response, started, result, before, after):
    """One information activity in the Management Trace, with its interval.

    Section 7 of the faculty specification of 2026-09-23: the record has to show
    that a resident spent an interval obtaining history while the patient was
    still unstable and still untreated -- and has to show it as a fact, not as a
    judgement. Nothing here calls a delay an error; whether it was the right use
    of those minutes is read from what was known at the time.
    """
    from family_engine import pending_results

    elapsed = int(result.get("elapsed_min", 0) or 0)
    st.session_state.management_trace.append({
        "trace_schema": "management_trace_v1",
        "activity_kind": str(activity),
        "decision_time_min": started,
        "response_time_min": started + elapsed,
        "elapsed_minutes": elapsed,
        "learner_input": str(request),
        "information_obtained": str(response),
        "interpreted_action": [],
        "reasoning": {},
        "reasoning_observations": [],
        "reasoning_gate": {"required": False, "status": "not_required"},
        "execution_status": "information",
        "action_summaries": deepcopy(result.get("action_summaries", [])),
        "results_pending": pending_results(st.session_state.state),
        "concurrent_treatments": deepcopy(
            (st.session_state.state.get("treatments") or {}).get("administered_medications", [])),
        "state_before": deepcopy(before),
        "state_after": deepcopy(after),
    })


def record_management_trace(learner_input, parsed, result, state_before, state_after):
    """Append one structured decision-response event to the Management Trace."""
    status = "executed" if result.get("executed") else "not_executed"
    if result.get("clarification"):
        status = "clarification_required"
    elif result.get("terminal_locked"):
        status = "terminal_locked"

    event = {
        "trace_schema": "management_trace_v1",
        "decision_time_min": state_before.get("sim_time_min", 0),
        "response_time_min": state_after.get("sim_time_min", 0),
        "elapsed_minutes": int(result.get("elapsed_min", 0) or 0),
        "learner_input": learner_input,
        # Preserve what the engine understood separately from what the learner typed.
        "interpreted_action": deepcopy(parsed.get("actions", [])),
        "reasoning": deepcopy(parsed.get("reasoning", {})),
        "reasoning_observations": deepcopy(parsed.get("reasoning_observations", [])),
        "reasoning_recognition": deepcopy(parsed.get("reasoning_recognition")),
        "cue_recognition": deepcopy(parsed.get("cue_recognition")),
        # What is still out at the moment of this decision, so that no result is
        # ever read as having been known before it was back.
        "results_pending": _pending_results_now(),
        "reasoning_gate": deepcopy(parsed.get("reasoning_gate", {"required": False, "status": "not_required"})),
        "recognized_future_actions": deepcopy(parsed.get("recognized_future_actions", [])),
        # What each of them is: an unmodelled medicine, a prescription for home, a
        # conditional plan or advice (faculty decision 3, 2026-09-25).
        "future_details": deepcopy(parsed.get("future_details", [])),
        "interpretation_mode": parsed.get("interpretation_mode", "deterministic"),
        "ai_interpretation": deepcopy(parsed.get("ai_interpretation")),
        "ai_fallback_reason": parsed.get("ai_fallback_reason"),
        "execution_status": status,
        "clarification": result.get("clarification"),
        "action_summaries": deepcopy(result.get("action_summaries", [])),
        "state_before": deepcopy(state_before),
        "state_after": deepcopy(state_after),
    }
    st.session_state.management_trace.append(event)
    return event

def _trace_time(minutes):
    return sim_time_label(int(minutes or 0))


def _patient_diagnostic_heading(label, result):
    """Time-anchor the latest diagnostic displayed in Patient Data."""
    time_min = (result or {}).get("time_min")
    return f"**{label} · {_trace_time(time_min)}**" if time_min is not None else f"**{label}**"

def _trace_state_text(snapshot):
    """Learner-facing observable state only; never expose hidden physiology."""
    o = (snapshot or {}).get("observable", {})
    tr = (snapshot or {}).get("treatments", {}) or {}
    parts = []
    rhythm = o.get("rhythm")
    hr = o.get("hr")
    if rhythm and hr is not None:
        parts.append(f"{rhythm}, HR {hr}/min")
    elif hr is not None:
        parts.append(f"HR {hr}/min")
    sbp, dbp = o.get("sbp"), o.get("dbp")
    if sbp is not None and dbp is not None:
        parts.append(f"BP {sbp}/{dbp}")
    crt = o.get("crt")
    if crt is not None:
        parts.append(f"CRT {crt} s")
    ext = o.get("extremities")
    if ext:
        parts.append(str(ext).lower())
    mental = o.get("mental_status")
    if mental:
        parts.append(str(mental).lower())
    spo2 = o.get("spo2")
    if spo2 is not None:
        parts.append(f"SpO₂ {spo2}%")
        # The active respiratory interface is part of the observable state.
        # Keep this formatter self-contained for isolated regression extracts.
        if tr.get("invasive_ventilation"):
            parts.append(
                f'{tr.get("ventilator_mode") or "VC/AC"} · '
                f'FiO₂ {tr.get("ventilator_fio2_percent") or 40:g}% · '
                f'PEEP {tr.get("ventilator_peep_cmh2o") or 5:g} cm H₂O'
            )
        elif tr.get("niv"):
            fio2 = tr.get("niv_fio2_percent")
            fio = f' · FiO₂ {fio2:g}%' if fio2 is not None else ""
            if (tr.get("niv_mode") == "BiPAP" and
                    tr.get("niv_ipap_cmh2o") is not None and
                    tr.get("niv_epap_cmh2o") is not None):
                parts.append(
                    f'BiPAP {tr.get("niv_ipap_cmh2o"):g}/'
                    f'{tr.get("niv_epap_cmh2o"):g} cm H₂O{fio}'
                )
            else:
                parts.append(
                    f'{tr.get("niv_mode") or "NIV"} '
                    f'{tr.get("niv_pressure_cmh2o", 0):g} cm H₂O{fio}'
                )
        elif tr.get("oxygen"):
            parts.append(
                f'{tr.get("oxygen_device") or "Oxygen"} '
                f'{tr.get("oxygen_flow_lpm", 0):g} L/min'
            )
        else:
            parts.append("RA")
    # Active infusions belong to the state available at the decision point. They
    # remain visible longitudinally without being repeated as a new action when
    # the learner simply continues an unchanged treatment.
    if tr.get("norepinephrine"):
        parts.append(
            f'Norepinephrine {tr.get("norepinephrine_rate", 0):g} '
            f'{tr.get("norepinephrine_units") or "mcg/kg/min"} active'
        )
    if tr.get("dobutamine"):
        parts.append(
            f'Dobutamine {tr.get("dobutamine_rate", 0):g} '
            f'{tr.get("dobutamine_units") or "mcg/kg/min"} active'
        )
    if tr.get("nitroglycerin"):
        parts.append(
            f'Nitroglycerin {tr.get("nitroglycerin_rate_mcg_min", 0):g} mcg/min active'
        )
    d = (snapshot or {}).get("diagnostics", {}) or {}
    lact = d.get("lactate")
    if lact and lact.get("value_mmol_l") is not None:
        parts.append(f'Lactate {lact["value_mmol_l"]:.1f} mmol/L')
    vbg = d.get("vbg")
    if vbg and vbg.get("ph") is not None:
        parts.append(
            f'VBG: pH {vbg["ph"]:.2f}, pCO₂ {vbg.get("pco2_mm_hg"):g} mmHg, '
            f'HCO₃ {vbg.get("bicarbonate_mmol_l"):g} mmol/L'
        )
    abg = d.get("abg")
    if abg and abg.get("ph") is not None:
        parts.append(
            f'ABG: pH {abg["ph"]:.2f}, PaCO₂ {abg.get("paco2_mm_hg"):g} mmHg, '
            f'PaO₂ {abg.get("pao2_mm_hg"):g} mmHg, P/F {abg.get("pf_ratio"):g}'
        )
    pocus = d.get("pocus")
    if pocus:
        # The trace records what the resident knew when deciding, so it carries
        # the findings as reported rather than a summary guessed from wording.
        # The old summary matched phrases, dropped RV and B-lines when the
        # wording changed, and never included the IVC at all.
        from pocus_report import format_pocus
        sections = format_pocus(pocus, compact=True).splitlines()[1:]
        parts.append("POCUS: " + " | ".join(sections))
    labs = d.get("basic_labs")
    if labs:
        lab_bits = []
        if labs.get("wbc_k_ul") is not None:
            lab_bits.append(f'WBC {labs["wbc_k_ul"]:g} K/µL')
        if labs.get("bicarbonate_mmol_l") is not None:
            lab_bits.append(f'HCO₃ {labs["bicarbonate_mmol_l"]:g} mmol/L')
        if labs.get("creatinine_mg_dl") is not None:
            lab_bits.append(f'Cr {labs["creatinine_mg_dl"]:g} mg/dL')
        if lab_bits:
            parts.append("Labs: " + ", ".join(lab_bits))
        else:
            parts.append("Basic labs result available")
    return " · ".join(parts) if parts else "—"

def _trace_reasoning_text(reasoning):
    r = reasoning or {}
    labels = [
        ("Problem", "problem_representation"),
        ("Priority", "management_priority"),
        ("Rationale", "rationale"),
        ("Expected", "expected_effect"),
        ("Preserve", "preservation_goal"),
        ("Reassess", "reassessment_target"),
    ]
    derived = _derived_slots(r)
    parts = [f"**{label}:** {r[key]}" + (DERIVED_SLOT_NOTE if key in derived else "")
             for label, key in labels if r.get(key)]
    return "  \n".join(parts) if parts else "—"


def _fluid_order_label(summary, now_min):
    """Name the ordered volume and, while it is still running, what has gone in.

    A bolus is delivered on the simulation clock. Reporting only the ordered
    volume told the resident that 1000 mL had been given when 500 mL had.
    """
    label = str(summary.get("label") or f'{summary["volume_ml"]:g} mL {summary["fluid_type"]}')
    start = summary.get("delivery_starts_at_min")
    duration = summary.get("administration_duration_min")
    if start is None or not duration:
        return label
    infused = summary["volume_ml"] * min(1, max(0, (now_min - start) / duration))
    if infused >= summary["volume_ml"]:
        return label
    due = start + duration
    return (f'{label} ({infused:.0f} mL of {summary["volume_ml"]:g} mL infused by '
            f'{now_min:g} min; remainder due at {due:g} min)')


def _norepinephrine_summary_label(summary):
    if summary.get("operation") == "stop":
        return "norepinephrine stopped"
    rate = float(summary.get("rate") or 0.0)
    units = summary.get("units") or "mcg/kg/min"
    old_rate = summary.get("old_rate")
    old_units = summary.get("old_units")
    if summary.get("operation") == "titrate" and old_rate is not None and old_units == units:
        old_rate = float(old_rate)
        direction = "increased" if rate > old_rate else ("decreased" if rate < old_rate else "maintained")
        return f'norepinephrine {direction} from {old_rate:g} to {rate:g} {units}'
    return f'norepinephrine {rate:g} {units}'


def _summary_source_position(summary, learner_input, fallback_index=0):
    """Locate an executed action in the learner's wording for display order.

    The physiology engine keeps its validated execution sequence, while the
    learner-facing trace mirrors the order in which actions were communicated.
    The last matching mention favors an executable clause over an earlier
    retrospective/state description of the same action.
    """
    text = str(learner_input or "").lower().replace("₂", "2")
    patterns = []
    dtype = summary.get("diagnostic_type")
    support = summary.get("support_type")
    agent = str(summary.get("agent_name") or summary.get("agent") or "").lower()

    if "volume_ml" in summary:
        volume = summary.get("volume_ml")
        patterns = [
            rf"\b{volume:g}\s*(?:ml|cc)\b" if isinstance(volume, (int, float)) else r"\b(?:fluid|saline|crystalloid)\b",
            r"\b(?:normal\s+saline|saline|crystalloid|fluid|fluids|ns|lr)\b",
        ]
    elif summary.get("energy_j") is not None:
        patterns = [r"\b(?:cardiovert|cardioversion|synchronized\s+shock|synchronised\s+shock)\b"]
    elif support == "oxygen":
        patterns = [r"\b(?:nasal\s+can+ula|non-?rebreather|nrb|simple\s+mask|face\s+mask|oxygen|o2)\b"]
    elif support == "norepinephrine":
        patterns = [r"\b(?:norepinephrine|noradrenaline|levophed|norepi|levo)\b"]
    elif support == "dobutamine":
        patterns = [r"\bdobutamine\b"]
    elif support == "nitroglycerin":
        patterns = [r"\b(?:nitroglycerin|nitroglycerine|gtn|nitro)\b"]
    elif support == "procedural_sedation":
        patterns = [r"\b(?:sedation|sedate|etomidate|midazolam)\b"]
    elif support == "niv":
        patterns = [r"\b(?:bipap|cpap|niv|nimv|nippv|vmni|non-?invasive)\b"]
    elif support == "airway_preparation":
        patterns = [r"\b(?:prepare|preparation)\b[^.;]{0,40}\bintubat"]
    elif support == "invasive_ventilation":
        patterns = ([r"\bintubat(?:e|ion|ing)\b"] if summary.get("operation") == "start"
                    else [r"\b(?:peep|fio2|ventilator|ventilation|ventilator\s+settings?)\b"])
    elif support == "disposition":
        patterns = [r"\b(?:admit|admission|transfer|discharge|home|icu|intensive\s+care|coronary)\b"]
    elif support == "antibiotics" or agent:
        terms = [x for x in (agent, "ceftriaxone", "azithromycin", "antibiotics") if x]
        patterns = [rf"\b(?:{'|'.join(re.escape(x) for x in terms)})\b"]
    elif dtype == "pocus":
        patterns = [r"\b(?:pocus|point[- ]of[- ]care\s+ultrasound)\b"]
    elif dtype == "lactate":
        patterns = [r"\blactate\b"]
    elif dtype == "vbg":
        patterns = [r"\b(?:vbg|venous\s+(?:blood\s+)?gas)\b"]
    elif dtype == "abg":
        patterns = [r"\b(?:abg|arterial\s+(?:blood\s+)?gas)\b"]
    elif dtype == "basic_labs":
        patterns = [r"\b(?:basic\s+labs?|lab(?:oratory)?\s+(?:tests?|exams?)|labs|blood\s+(?:work|tests)|cbc|bmp|cmp|crp)\b"]
    elif dtype == "temperature":
        patterns = [r"\b(?:temperature|temp)\b"]
    elif dtype == "poc_glucose":
        patterns = [r"\b(?:glucose|blood\s+sugar|finger\s*stick)\b"]
    elif dtype == "focused_history":
        patterns = [r"\b(?:history|symptoms)\b"]
    elif dtype == "chest_xray":
        patterns = [r"\b(?:chest\s+x[- ]?ray|cxr|chest\s+radiograph)\b"]
    elif dtype == "urinalysis":
        patterns = [r"\b(?:urinalysis|urine\s+(?:analysis|dip)|ua)\b"]
    elif dtype == "blood_cultures":
        patterns = [r"\b(?:blood\s+cultures?|cultures?)\b"]

    positions = [m.start() for pattern in patterns for m in re.finditer(pattern, text, re.I)]
    return max(positions) if positions else len(text) + fallback_index


def _summaries_in_learner_order(summaries, learner_input):
    indexed = list(enumerate(summaries or []))
    indexed.sort(key=lambda item: (_summary_source_position(item[1], learner_input, item[0]), item[0]))
    ordered = [summary for _, summary in indexed]
    # When sedation and cardioversion belong to the same order, display the
    # clinically executed sequence even if the learner mentioned the shock first.
    sedations = [s for s in ordered if s.get("support_type") == "procedural_sedation"]
    shocks = [s for s in ordered if s.get("energy_j") is not None]
    if sedations and shocks:
        procedure_indices = [
            idx for idx, summary in enumerate(ordered)
            if summary in sedations or summary in shocks
        ]
        insertion = min(procedure_indices)
        others = [s for s in ordered if s not in sedations and s not in shocks]
        insertion = min(insertion, len(others))
        ordered = others[:insertion] + sedations + shocks + others[insertion:]
    return ordered

def _trace_action_text(event):
    summaries = _summaries_in_learner_order(
        event.get("action_summaries") or [], event.get("learner_input", "")
    )
    labels = []
    for s in summaries:
        if s.get("label"):
            labels.append(str(s["label"]))
        elif "volume_ml" in s:
            labels.append(f'{s["volume_ml"]} mL {s.get("fluid_type", "crystalloid")}')
        elif s.get("agent") == "furosemide":
            labels.append(f'furosemide {s.get("dose_mg", 0):g} mg {s.get("route", "IV")}'
                          + (f' over {s["administration_duration_min"]:g} min' if s.get("administration_duration_min") else ""))
        elif "agent" in s:
            labels.append(f'{s["agent"]} {s.get("dose_mg", 0):g} mg {s.get("route", "")}'.strip()
                          + (f' over {s["administration_duration_min"]:g} min' if s.get("administration_duration_min") else ""))
        elif s.get("support_type") == "procedural_sedation":
            labels.append(procedural_sedation_label(s))
        elif "energy_j" in s:
            labels.append(f'synchronized cardioversion {s["energy_j"]} J')
        elif s.get("support_type") == "oxygen":
            labels.append(f'{s.get("device", "oxygen")} {s.get("flow_lpm", 0):g} L/min')
        elif s.get("support_type") == "norepinephrine":
            labels.append(_norepinephrine_summary_label(s))
        elif s.get("support_type") == "dobutamine":
            labels.append("stop dobutamine" if s.get("operation") == "stop"
                          else f'dobutamine {s.get("rate", 5):g} {s.get("units") or "mcg/kg/min"}')
        elif s.get("support_type") == "nitroglycerin":
            labels.append("stop nitroglycerin" if s.get("operation") == "stop"
                          else f'nitroglycerin {s.get("rate_mcg_min", 0):g} mcg/min')
        elif s.get("support_type") == "niv":
            if s.get("operation") == "stop":
                labels.append("stop NIV")
            elif s.get("mode") == "BiPAP" and s.get("ipap_cmh2o") is not None and s.get("epap_cmh2o") is not None:
                fio = f' · FiO₂ {s.get("fio2_percent"):g}%' if s.get("fio2_percent") is not None else ""
                labels.append(f'BiPAP {s.get("ipap_cmh2o"):g}/{s.get("epap_cmh2o"):g} cm H₂O{fio}')
            else:
                fio = f' · FiO₂ {s.get("fio2_percent"):g}%' if s.get("fio2_percent") is not None else ""
                labels.append(f'{s.get("mode", "NIV")} {s.get("pressure_cmh2o", 0):g} cm H₂O{fio}')
        elif s.get("support_type") == "airway_preparation":
            labels.append("prepare for intubation")
        elif s.get("support_type") == "invasive_ventilation":
            operation = s.get("operation", "start")
            prefix = {
                "continue": "continue",
                "adjust": "adjust",
                "start": "intubation +",
            }.get(operation, "adjust")
            labels.append(
                f'{prefix} {s.get("ventilator_mode", "VC/AC")} ventilation · '
                f'FiO₂ {s.get("fio2_percent", 100):g}% · PEEP {s.get("peep_cmh2o", 8):g} cm H₂O'
            )
        elif s.get("support_type") == "disposition":
            labels.append('Discharge home' if s.get("destination") == "home"
                          else f'Admit to {s.get("destination", "ICU")}')
        elif s.get("support_type") == "antibiotics":
            name = str(s.get("agent_name") or "broad-spectrum antibiotics")
            if name.lower() == "ceftriaxone + azithromycin":
                ceftriaxone = "ceftriaxone"
                if s.get("dose_g") is not None:
                    ceftriaxone += f' {s.get("dose_g"):g} g'
                if s.get("route"):
                    ceftriaxone += f' {s.get("route")}'
                name = ceftriaxone + " + azithromycin"
            else:
                if s.get("dose_g") is not None:
                    name += f' {s.get("dose_g"):g} g'
                if s.get("route"):
                    name += f' {s.get("route")}'
            labels.append(name)
        elif s.get("diagnostic_type") == "pocus":
            labels.append("POCUS")
        elif s.get("diagnostic_type") == "lactate":
            labels.append("lactate")
        elif s.get("diagnostic_type") == "vbg":
            labels.append("VBG")
        elif s.get("diagnostic_type") == "abg":
            labels.append("ABG")
        elif s.get("diagnostic_type") == "basic_labs":
            labels.append("basic laboratory tests")
        elif s.get("diagnostic_type") == "temperature":
            labels.append("temperature")
        elif s.get("diagnostic_type") == "poc_glucose":
            labels.append("point-of-care glucose")
        elif s.get("diagnostic_type") == "focused_history":
            labels.append("focused history")
        elif s.get("diagnostic_type") == "chest_xray":
            labels.append("chest X-ray")
        elif s.get("diagnostic_type") == "urinalysis":
            labels.append("urinalysis")
        elif s.get("diagnostic_type") == "blood_cultures":
            labels.append("blood cultures")
    # Preserve learner-requested actions that the prototype recognized but could
    # not yet execute. They are still part of the decision pathway and should not
    # be mislabeled as a pure reassessment in the learner-facing trace.
    import unexecuted_items
    for item, kind_label in (unexecuted_items.trace_labels(event)
                             if event.get("recognized_future_actions") else []):
        if not item:
            continue
        # An older record, or an item with no kind, keeps the original wording.
        labels.append(f"{item} ({kind_label})" if kind_label else f"{item} (recognized; not yet executable)")

    if not labels:
        # Fall back to interpreted executable actions, excluding reassessment.
        for a in event.get("interpreted_action") or []:
            if a.get("type") == "reassessment":
                continue
            labels.append(str(a.get("type", "action")).replace("_", " "))
    return " + ".join(labels) if labels else "Reassessment"

DERIVED_SLOT_NOTE = " · composed by the app from the resident's own words, not stated as such"


def _derived_slots(reasoning):
    values = (reasoning or {}).get("derived_slots")
    return frozenset(values) if isinstance(values, (list, tuple, set)) else frozenset()


def _trace_reasoning_items(reasoning):
    r = reasoning or {}
    derived = _derived_slots(r)
    labels = [("Problem", "problem_representation"), ("Priority", "management_priority"), ("Rationale", "rationale"), ("Expected effect", "expected_effect"), ("Preservation goal", "preservation_goal"), ("Reassessment target", "reassessment_target")]
    return [(label + (DERIVED_SLOT_NOTE if key in derived else ""), str(r[key]))
            for label, key in labels if r.get(key)]


def _trace_observable_delta(before, after, reasoning=None):
    """Compact response showing changes plus explicitly targeted stable findings."""
    b = (before or {}).get("observable", {})
    a = (after or {}).get("observable", {})
    values = [
        ("Rhythm", b.get("rhythm"), a.get("rhythm"), lambda v: str(v)),
        ("HR", b.get("hr"), a.get("hr"), lambda v: f"{v}/min"),
        ("BP", f'{b.get("sbp")}/{b.get("dbp")}' if b.get("sbp") is not None and b.get("dbp") is not None else None, f'{a.get("sbp")}/{a.get("dbp")}' if a.get("sbp") is not None and a.get("dbp") is not None else None, lambda v: v),
        ("CRT", b.get("crt"), a.get("crt"), lambda v: f"{v} s"),
        ("Extremities", b.get("extremities"), a.get("extremities"), lambda v: str(v).lower()),
        ("Mental status", b.get("mental_status"), a.get("mental_status"), lambda v: str(v).lower()),
        ("SpO₂", b.get("spo2"), a.get("spo2"), lambda v: f"{v}%"),
        ("Respiratory rate", b.get("respiratory_rate"), a.get("respiratory_rate"), lambda v: f"{v}/min"),
        ("Work of breathing", b.get("work_of_breathing"), a.get("work_of_breathing"), lambda v: str(v).lower()),
    ]
    target = str((reasoning or {}).get("reassessment_target", "")).lower()
    targeted = set()
    if "perfusion" in target:
        targeted.update({"BP", "CRT", "Extremities", "Mental status"})
    if "hemodynamic" in target:
        targeted.update({"Rhythm", "HR", "BP", "CRT", "Extremities"})
    if "rhythm" in target:
        targeted.add("Rhythm")
    if "heart rate" in target or re.search(r"\bhr\b", target):
        targeted.add("HR")
    if ("blood pressure" in target or "arterial pressure" in target or
            re.search(r"\b(?:bp|map)\b", target)):
        targeted.add("BP")
    if "capillary refill" in target or re.search(r"\bcrt\b", target):
        targeted.add("CRT")
    if "extremit" in target or "mottling" in target:
        targeted.add("Extremities")
    if any(term in target for term in ("mental status", "mentation", "consciousness", "neurologic")):
        targeted.add("Mental status")
    if any(term in target for term in ("oxygenation", "spo2", "saturation")):
        targeted.add("SpO₂")
    if "respiratory status" in target:
        targeted.update({"SpO₂", "Respiratory rate", "Work of breathing"})
    if "respiratory rate" in target or "breathing rate" in target:
        targeted.add("Respiratory rate")
    if "work of breathing" in target or "respiratory distress" in target:
        targeted.add("Work of breathing")

    changed = [
        (label, fmt(bv), fmt(av))
        for label, bv, av, fmt in values
        if bv is not None and av is not None and (bv != av or label in targeted)
    ]
    before_vent = bool(((before or {}).get("treatments") or {}).get("invasive_ventilation"))
    after_vent = bool(((after or {}).get("treatments") or {}).get("invasive_ventilation"))
    if after_vent and not before_vent:
        changed = [
            (label, bv, "sedated after intubation" if label == "Mental status" and av == "sedated" else av)
            for label, bv, av in changed
        ]
    return changed


def _trace_diagnostic_results(event):
    """Return newly available diagnostic results for one decision interval.

    Results belong to the observed response, not only to the next decision's
    patient-state snapshot. Keeping them here also makes the final decision in
    an encounter reviewable when no later decision follows it.
    """
    results = []
    summaries = sorted(
        [s for s in (event.get("action_summaries") or []) if s.get("diagnostic_type")],
        key=lambda s: (s.get("result") or {}).get("time_min", event.get("response_time_min", 0)),
    )
    for summary in summaries:
        result = summary.get("result") or {}
        text = format_diagnostic_summary(summary).strip()
        if not text:
            continue
        results.append((
            _trace_time(result.get("time_min", event.get("response_time_min", 0))),
            text,
        ))
    return results


def _reasoning_present(reasoning):
    """True when the learner explicitly supplied at least one reasoning slot."""
    r = reasoning or {}
    return any(r.get(k) for k in ("problem_representation", "management_priority", "rationale", "expected_effect", "preservation_goal", "reassessment_target"))


def _perfusion_response_direction(event):
    """Conservative direction of observable perfusion response: improve / worsen / mixed / unchanged.

    This deliberately uses only state_before -> state_after. It does not diagnose
    fluid responsiveness or judge the management decision.
    """
    b = ((event.get("state_before") or {}).get("observable") or {})
    a = ((event.get("state_after") or {}).get("observable") or {})
    good = bad = 0

    # BP: require a modest change to avoid over-reading tiny numeric noise.
    if b.get("sbp") is not None and a.get("sbp") is not None:
        d = a["sbp"] - b["sbp"]
        if d >= 5: good += 1
        elif d <= -5: bad += 1
    if b.get("crt") is not None and a.get("crt") is not None:
        d = a["crt"] - b["crt"]
        if d <= -1: good += 1
        elif d >= 1: bad += 1

    rank_ext = {"mottled/cold": 0, "cold": 1, "cool": 2, "warm": 3, "warmer": 4}
    be, ae = str(b.get("extremities", "")).lower(), str(a.get("extremities", "")).lower()
    if be in rank_ext and ae in rank_ext:
        if rank_ext[ae] > rank_ext[be]: good += 1
        elif rank_ext[ae] < rank_ext[be]: bad += 1

    rank_ms = {"unresponsive": 0, "drowsy": 1, "confused": 1, "alert": 2}
    bm, am = str(b.get("mental_status", "")).lower(), str(a.get("mental_status", "")).lower()
    if bm in rank_ms and am in rank_ms:
        if rank_ms[am] > rank_ms[bm]: good += 1
        elif rank_ms[am] < rank_ms[bm]: bad += 1

    if good and not bad: return "improve"
    if bad and not good: return "worsen"
    if good and bad: return "mixed"
    return "unchanged"


def _review_expectation_text(text):
    """Normalize only review matching; retain the learner's original wording."""
    return str(text or "").lower().translate(str.maketrans("áéíóúüñ’", "aeiouun'"))


def _immediate_expectation_text(expected, event):
    """Keep affirmative effects whose stated horizon fits this observation.

    This is deliberately conservative: an excluded clause cannot be restored
    through the reassessment list, which describes what to check, not what must
    improve. Separate clauses preserve immediate effects in compound orders.
    """
    normalized = _review_expectation_text(expected)
    elapsed = event.get("elapsed_minutes")
    if elapsed is None:
        start = event.get("decision_time_min", (event.get("state_before") or {}).get("sim_time_min"))
        end = event.get("response_time_min", (event.get("state_after") or {}).get("sim_time_min"))
        elapsed = max(0, float(end) - float(start)) if start is not None and end is not None else None
    clauses = re.split(
        r"(?<!\d)[.;](?!\d)|\b(?:but|whereas|while|pero|mientras|aunque)\b|"
        r",\s*(?=(?:without|sin|no\b|not\b|i\b|we\b|and\b|y\b))|"
        r"\b(?:and|y)\s+(?=(?:i|we|norepinephrine|noradrenalina|oxygen|oxigeno|fluids|liquidos|antibiotics|antibioticos)\b)|"
        r"\b(?:and|y)\s+(?=(?:improved|better|mejoria)[^.;]*\b(?:now|immediately|promptly|ahora|inmediata\w*)\b)",
        normalized,
    )
    immediate = []
    for clause in clauses:
        # A trailing 'without worsening oxygenation' qualifies preservation;
        # it must not turn oxygenation into an expected improvement.
        clause = re.split(r"\b(?:without|sin)\b", clause, maxsplit=1)[0].strip()
        if not clause or re.search(r"\b(?:no|not|never|don't|doesn't|won't|wouldn't|cannot|can't|unlikely)\b", clause):
            continue
        horizon = re.search(
            r"\b(?:in|after|within|en|a los|dentro de)\s+"
            r"(?:(?:the\s+)?next\s+|la\s+proxima\s+)?"
            r"(?:(\d+(?:\.\d+)?|one|an?|una?)\s*)?"
            r"(minutes?|mins?|minutos?|hours?|horas?)\b", clause)
        if horizon:
            amount = horizon.group(1) or "1"
            minutes = (float(amount) if re.fullmatch(r"\d+(?:\.\d+)?", amount) else 1) * (60 if horizon.group(2).startswith(("hour", "hora")) else 1)
            if elapsed is None or minutes > float(elapsed):
                continue
        elif re.search(
            r"\b(?:gradual\w*|paulatin\w*|eventual\w*|later|delayed|over time|con el tiempo|mas tarde)\b|"
            r"\b(?:over|during|after|durante|despues de|en)\b[^.;]*\b(?:hours|horas)\b",
            clause,
        ):
            continue
        immediate.append(clause)
    return "; ".join(immediate)


def _expected_response_prompt(event):
    """Return a target-aware, non-scoring expectation/response prompt."""
    r = event.get("reasoning") or {}
    expected = str(r.get("expected_effect", "")).strip()
    preservation = str(r.get("preservation_goal", "")).strip()
    target = str(r.get("reassessment_target", "")).strip().lower()
    if not expected and not preservation:
        return None

    exp = _immediate_expectation_text(expected, event)
    preservation_text = _review_expectation_text(preservation)
    target = _review_expectation_text(target)
    # Bind preservation to its own clause and endpoint. For example, preserving
    # oxygenation must not convert an explicit BP improvement into a stable-BP
    # goal, or require the preserved oxygenation to improve.
    effect_clauses = re.split(
        r";|\b(?:with|con)\s+(?=(?:maintain\w*|preserv\w*|mantener\w*)\b)|"
        r"\b(?:and|y)\s+(?=(?:improv\w*|better|mejor\w*|preserv\w*|maintain\w*|unchanged)\b)", exp
    )
    preservation_clauses = [clause for clause in effect_clauses if re.search(
        r"\b(?:maintain\w*|preserv\w*|remain\s+stable|stay\s+stable|unchanged|mantener\w*|estable)\b", clause
    )]
    pressure_preservation_target = any(re.search(
        r"blood pressure|arterial pressure|presion arterial|\b(?:bp|map|pam)\b", clause
    ) for clause in preservation_clauses)
    inline_oxygen_preservation = any(re.search(
        r"oxygen\w*|oxigen\w*|spo2|saturation|saturacion|respirator\w*", clause
    ) for clause in preservation_clauses)
    perfusion_preservation = any(re.search(r"perfusion|hemodynamic|hemodinamic", clause)
                                for clause in preservation_clauses) or bool(re.search(
                                    r"perfusion|hemodynamic|hemodinamic", preservation_text))
    exp = "; ".join(clause for clause in effect_clauses if clause not in preservation_clauses)
    if preservation_clauses and not preservation:
        preservation = expected
    # Antimicrobial efficacy cannot be determined from one immediate snapshot.
    # Apply this only to antibiotic-only treatment, so a simultaneous fluid,
    # pressor, or respiratory intervention retains its own immediate review.
    treatment_types = _action_types_for_event(event) - {
        "reassessment", "pocus", "lactate", "vbg", "abg", "basic_labs",
        "urinalysis", "chest_xray", "blood_cultures", "temperature", "focused_history",
    }
    if expected and treatment_types == {"antibiotics"}:
        changes = _trace_observable_delta(event.get("state_before"), event.get("state_after"), r)
        observed = "; ".join(f"{label} {old} to {new}" for label, old, new in changes)
        return (
            "Treatment timing and reassessment",
            f"Your stated expectation was: {expected}. The recorded response was {observed or 'no recorded observable change'}. "
            "This before/after comparison alone does not establish antimicrobial success or failure. "
            "How does the expected treatment time course affect your interpretation, and which findings would prompt "
            "immediate supportive treatment or reassessment of the infectious source?",
        )
    mechanistic_terms = (
        "preload", "contractility", "cardiac output", "stroke volume",
        "afterload", "vascular tone", "filling", "venous return"
    )
    is_mechanistic = any(term in exp for term in mechanistic_terms)
    observable_targets = {
        "perfusion", "blood pressure", "bp", "map", "mental status",
        "capillary refill", "crt", "oxygenation", "spo2", "work of breathing",
        "respiratory status", "heart rate", "hr", "rhythm", "lactate"
    }
    target_is_observable = any(key in target for key in observable_targets)
    if is_mechanistic and not target_is_observable:
        return None

    bstate = event.get("state_before") or {}
    astate = event.get("state_after") or {}
    b = bstate.get("observable") or {}
    a = astate.get("observable") or {}
    tr_after = astate.get("treatments") or {}

    perfusion_target = any(x in exp for x in (
        "perfusion", "blood pressure", "arterial pressure", "capillary refill", "crt", "hemodynamic",
        "presion arterial", "relleno capilar", "hemodinamic",
    )) or bool(re.search(r"\b(?:bp|map|pam)\b", exp)) or pressure_preservation_target or perfusion_preservation
    oxygen_improvement_target = any(x in exp for x in (
        "oxygen", "spo2", "respiratory", "oxigen", "saturacion", "respiratori"
    ))
    oxygen_preservation_target = any(x in preservation_text for x in (
        "oxygen", "spo2", "saturation", "respiratory", "oxigen", "saturacion", "respiratori"
    )) or inline_oxygen_preservation
    lactate_target = "lactate" in exp or "lactato" in exp
    # Reassessment can disambiguate an unqualified mechanistic expectation,
    # but it must not undo excluded time horizons or negated targets.
    limited_expectation = bool(re.search(
        r"\b(?:no|not|without|sin|never|don't|doesn't|won't|unlikely|gradual\w*|later|delayed|hours?|horas?|minutes?|minutos?)\b",
        _review_expectation_text(expected),
    ))
    if (exp and is_mechanistic and not limited_expectation and not perfusion_target
            and not oxygen_improvement_target and not lactate_target):
        perfusion_target = any(x in target for x in (
            "perfusion", "blood pressure", "arterial pressure", "capillary refill", "crt", "hemodynamic"
        ))
        oxygen_improvement_target = any(x in target for x in ("oxygen", "spo2", "respiratory"))
        lactate_target = "lactate" in target
    if not perfusion_target and not oxygen_improvement_target and not oxygen_preservation_target and not lactate_target:
        return None

    positive, negative, neutral = [], [], []
    preservation_met, preservation_failed = [], []

    if ((oxygen_improvement_target or oxygen_preservation_target)
            and b.get("spo2") is not None and a.get("spo2") is not None):
        delta = a["spo2"] - b["spo2"]
        support = ""
        if tr_after.get("invasive_ventilation"):
            support = (
                f' on invasive ventilation at FiO₂ '
                f'{tr_after.get("ventilator_fio2_percent") or 40:g}%'
            )
        elif tr_after.get("niv"):
            mode = tr_after.get("niv_mode") or "NIV"
            if (mode == "BiPAP" and tr_after.get("niv_ipap_cmh2o") is not None and
                    tr_after.get("niv_epap_cmh2o") is not None):
                mode += f' {tr_after.get("niv_ipap_cmh2o"):g}/{tr_after.get("niv_epap_cmh2o"):g}'
            fio2 = tr_after.get("niv_fio2_percent")
            support = f' on {mode}' + (f' at FiO₂ {fio2:g}%' if fio2 is not None else "")
        if oxygen_improvement_target:
            if delta >= 3:
                positive.append(f"oxygen saturation improved from {b['spo2']}% to {a['spo2']}%{support}")
            elif delta > 0 and a["spo2"] <= 90:
                negative.append(
                    f"oxygen saturation increased only from {b['spo2']}% to {a['spo2']}%{support} and remained severely impaired"
                )
            elif delta <= 0:
                negative.append(
                    f"oxygen saturation did not improve ({b['spo2']}% to {a['spo2']}%){support}"
                )
            else:
                neutral.append(f"oxygen saturation changed from {b['spo2']}% to {a['spo2']}%{support}")
        elif delta >= 0:
            preservation_met.append(
                f"oxygenation was preserved ({b['spo2']}% to {a['spo2']}%){support}"
            )
        else:
            preservation_failed.append(
                f"oxygenation also worsened despite the stated goal to preserve it "
                f"({b['spo2']}% to {a['spo2']}%){support}"
            )

    if perfusion_target:
        expects_pressure_improvement = (any(x in exp for x in ("blood pressure", "arterial pressure", "presion arterial")) or bool(re.search(r"\b(?:bp|map|pam)\b", exp))) and not pressure_preservation_target
        expects_crt_improvement = any(x in exp for x in ("capillary refill", "crt", "relleno capilar"))
        if b.get("sbp") is not None and a.get("sbp") is not None:
            pressure_delta = a["sbp"] - b["sbp"]
            pressure_fact = f"blood pressure {b.get('sbp')}/{b.get('dbp')} to {a.get('sbp')}/{a.get('dbp')}"
            if pressure_delta >= 5:
                positive.append("blood pressure increased from " + pressure_fact.replace("blood pressure ", ""))
            elif pressure_delta <= -5 or (expects_pressure_improvement and pressure_delta < 0):
                negative.append("blood pressure decreased from " + pressure_fact.replace("blood pressure ", ""))
            elif expects_pressure_improvement and pressure_delta == 0:
                negative.append(f"blood pressure did not improve ({b.get('sbp')}/{b.get('dbp')} to {a.get('sbp')}/{a.get('dbp')})")
            else:
                neutral.append("blood pressure remained broadly stable (" + pressure_fact.replace("blood pressure ", "") + ")")
        if b.get("crt") is not None and a.get("crt") is not None:
            crt_delta = a["crt"] - b["crt"]
            if crt_delta <= -1:
                positive.append(f"capillary refill shortened from {b['crt']} to {a['crt']} seconds")
            elif crt_delta >= 1:
                negative.append(f"capillary refill prolonged from {b['crt']} to {a['crt']} seconds")
            elif expects_crt_improvement:
                negative.append(f"capillary refill did not improve and remained {a['crt']} seconds")
            else:
                neutral.append(f"capillary refill remained {a['crt']} seconds")
        rank_ext = {"mottled/cold": 0, "very cold": 0, "cold": 1, "cool": 2, "warmer": 3, "warm": 3}
        be, ae = str(b.get("extremities", "")).lower(), str(a.get("extremities", "")).lower()
        if be in rank_ext and ae in rank_ext:
            if rank_ext[ae] > rank_ext[be]:
                positive.append(f"extremities changed from {be} to {ae}")
            elif rank_ext[ae] < rank_ext[be]:
                negative.append(f"extremities changed from {be} to {ae}")
        # Sedation after intubation is an intervention state, not a neurologic
        # perfusion endpoint. Only compare physiologic mental-status categories.
        rank_ms = {"unresponsive": 0, "obtunded": 1, "drowsy": 2, "confused": 2, "alert": 3}
        bm, am = str(b.get("mental_status", "")).lower(), str(a.get("mental_status", "")).lower()
        if bm in rank_ms and am in rank_ms:
            if rank_ms[am] > rank_ms[bm]:
                positive.append(f"mental status changed from {bm} to {am}")
            elif rank_ms[am] < rank_ms[bm]:
                negative.append(f"mental status changed from {bm} to {am}")

    if lactate_target:
        bdiag = bstate.get("diagnostics") or {}
        adiag = astate.get("diagnostics") or {}
        before_lactate = (bdiag.get("lactate") or {}).get("value_mmol_l")
        after_lactate = (adiag.get("lactate") or {}).get("value_mmol_l")
        if before_lactate is not None and after_lactate is not None:
            lactate_delta = float(after_lactate) - float(before_lactate)
            if lactate_delta <= -0.2:
                positive.append(
                    f"lactate decreased from {before_lactate:.1f} to {after_lactate:.1f} mmol/L"
                )
            elif lactate_delta >= 0.2:
                negative.append(
                    f"lactate increased from {before_lactate:.1f} to {after_lactate:.1f} mmol/L"
                )
            else:
                negative.append(
                    f"lactate did not improve ({before_lactate:.1f} to {after_lactate:.1f} mmol/L)"
                )

    if not negative and not preservation_failed:
        return None

    def joined_facts(items):
        if len(items) < 2:
            return items[0] if items else ""
        return ", ".join(items[:-1]) + ", and " + items[-1]

    if positive or preservation_met:
        favorable = joined_facts(positive + preservation_met + neutral[:1])
        unfavorable = joined_facts(negative + preservation_failed)
        favorable_sentence = favorable[:1].upper() + favorable[1:]
        return (
            "Mixed response",
            f"You expected {expected}. {favorable_sentence}; however, {unfavorable}. "
            "How did you weigh the favorable and unfavorable findings when updating your working model and next priority?"
        )

    observed = joined_facts(negative + neutral[:1])
    if pressure_preservation_target and not re.search(r"improv\w*|increase\w*|shorten\w*|mejor\w*", exp):
        return (
            "Preservation goal vs observed response",
            f"Your stated expectation was: {expected}. The recorded findings were {joined_facts(negative + preservation_failed + neutral[:1])}. "
            "How did these findings affect your assessment of whether the preservation goal was met and your next priority?",
        )
    preservation_sentence = ""
    if preservation_failed:
        preservation_sentence = " " + joined_facts(preservation_failed)[:1].upper() + joined_facts(preservation_failed)[1:] + "."
    priority = str(r.get("management_priority", "")).lower()
    if "fluid responsive" in priority or "fluid responsiveness" in priority:
        return (
            "Expected effect vs observed response",
            f"You expected {expected} after another fluid bolus. Instead, {observed}.{preservation_sentence} "
            "How did this response affect your assessment of fluid responsiveness and your working model?"
        )
    if exp:
        return (
            "Expected effect vs observed response",
            f"You expected {expected}. Those expected improvements were not demonstrated: {observed}."
            f"{preservation_sentence} How did this response affect your assessment of the patient's physiology and your working model?"
        )
    return (
        "Preservation goal vs observed response",
        f"You aimed to {preservation}. {preservation_sentence.strip()} "
        "How did this response affect your assessment of the patient's physiology and your working model?"
    )

def _model_shift_prompt(previous_event, event):
    """Detect only explicit, text-level working-model shifts between decisions."""
    pr = previous_event.get("reasoning") or {}
    cr = event.get("reasoning") or {}
    prev = " ".join(str(pr.get(k, "")) for k in ("problem_representation", "rationale", "management_priority") if pr.get(k)).lower()
    curr = " ".join(str(cr.get(k, "")) for k in ("problem_representation", "rationale", "management_priority") if cr.get(k)).lower()
    if not prev or not curr:
        return None

    # Conservative MVP: recognize an explicit transition from volume/preload/fluid
    # framing to an explicitly different/another shock-cause framing.
    prev_volume = any(x in prev for x in ("reduced effective circulating volume", "low preload", "preload respons", "fluid responsive", "fluid responsiveness", "hypovolem"))
    curr_other_shock = ("another cause of shock" in curr or "other cause of shock" in curr or "different cause of shock" in curr)
    if prev_volume and curr_other_shock:
        return ("Working model shift", "You moved from a reduced-effective-circulating-volume/fluid-responsiveness model toward another cause of shock. What features of the preceding response prompted this change, and how did the subsequently available diagnostic information support or challenge your revised model?")

    curr_fluid_limit = any(x in curr for x in (
        "additional fluid unlikely", "further fluid unlikely", "stop further fluid",
        "avoid further fluid", "no further fluid"
    ))
    curr_pressure_or_airway = any(x in curr for x in (
        "restore perfusion pressure", "pressor", "norepinephrine", "airway escalation"
    ))
    if prev_volume and curr_fluid_limit and curr_pressure_or_airway:
        return (
            "Management priority shift",
            "You explicitly moved from further preload-directed treatment toward perfusion-pressure stabilization before airway escalation. Which features of the preceding response set your threshold for that change?"
        )
    return None


def _critical_adaptation_prompt(event):
    """Identify a high-salience state/action/response pivot without scoring it."""
    before = event.get("state_before") or {}
    after = event.get("state_after") or {}
    if before.get("case_id") != "PS002":
        return None
    summaries = event.get("action_summaries") or []
    prior_fluid = ((before.get("treatments") or {}).get("cumulative_crystalloid_ml") or 0)
    if not any(s.get("volume_ml", 0) > 0 for s in summaries) or prior_fluid < 1500:
        return None
    b = before.get("observable") or {}
    a = after.get("observable") or {}
    worsening = 0
    facts = []
    if b.get("sbp") is not None and a.get("sbp") is not None and a["sbp"] <= b["sbp"] - 8:
        worsening += 1
        facts.append(f"blood pressure fell from {b.get('sbp')}/{b.get('dbp')} to {a.get('sbp')}/{a.get('dbp')}")
    if b.get("crt") is not None and a.get("crt") is not None and a["crt"] >= b["crt"] + 1:
        worsening += 1
        facts.append(f"capillary refill prolonged from {b.get('crt')} to {a.get('crt')} seconds")
    mental_rank = {"alert": 3, "drowsy": 2, "obtunded": 1, "unresponsive": 0}
    bm, am = str(b.get("mental_status", "")).lower(), str(a.get("mental_status", "")).lower()
    if bm in mental_rank and am in mental_rank and mental_rank[am] < mental_rank[bm]:
        worsening += 1
        facts.append(f"mental status changed from {bm} to {am}")
    if worsening < 2 or a.get("spo2") is None or a.get("spo2") > 90:
        return None
    reasoning = event.get("reasoning") or {}
    priority = str(reasoning.get("management_priority") or "").strip()
    opening = (
        f'You stated the management priority: “{priority}.” '
        if priority else
        "The action sequence continued respiratory and circulatory support. "
    )
    facts.append(f"oxygen saturation remained {a.get('spo2')}%")
    observed = "; ".join(facts)
    return (
        "Critical adaptation point",
        opening
        + "The observed response showed " + observed + ". Which finding should have changed your next "
        "management priority, and what alternative action would you take?",
    )


def _reasoning_data_alignment_prompt(event, previous_event=None):
    """Identify explicit learner claims that conflict with available observations.

    This is deliberately conservative and descriptive. It does not infer a hidden
    diagnosis, decide whether an action was correct, or score the learner. A prompt
    is produced only for a small set of explicit claims when the contradictory
    evidence was already visible at the time of the decision.
    """
    learner_text = " ".join(
        str(x) for x in [
            event.get("learner_input", ""),
            " ".join(str(v) for v in (event.get("reasoning") or {}).values()),
        ] if x
    )
    t = re.sub(r"\s+", " ", learner_text).strip().lower()
    if not t:
        return None

    before = event.get("state_before") or {}
    o = before.get("observable") or {}
    diagnostics = before.get("diagnostics") or {}
    treatments = before.get("treatments") or {}
    claims = []
    facts = []

    shock_resolution_claim = bool(re.search(
        r"\b(?:not shocked anymore|no longer (?:in )?shock|shock (?:has )?resolved|"
        r"shock is resolved|not in shock anymore)\b",
        t,
    ))
    if shock_resolution_claim:
        shock_facts = []
        if o.get("sbp") is not None and o.get("sbp") < 100:
            shock_facts.append(f'BP {o.get("sbp")}/{o.get("dbp")} mmHg')
        if o.get("crt") is not None and o.get("crt") >= 4:
            shock_facts.append(f'capillary refill {o.get("crt")} seconds')
        if o.get("hr") is not None and o.get("hr") >= 120:
            shock_facts.append(f'HR {o.get("hr")}/min')
        mental = str(o.get("mental_status") or "").lower()
        if mental in {"drowsy", "confused", "obtunded", "unresponsive"}:
            shock_facts.append(f'mental status {mental}')
        lactate = diagnostics.get("lactate") or {}
        if lactate.get("value_mmol_l") is not None and lactate.get("value_mmol_l") >= 2.0:
            shock_facts.append(f'lactate {lactate.get("value_mmol_l"):.1f} mmol/L')
        # Require multiple visible abnormalities so a borderline pressure alone
        # never triggers a disagreement prompt.
        if len(shock_facts) >= 2:
            claims.append('the patient was “not shocked anymore”')
            facts.extend(shock_facts)

    respiratory_failure_claim = bool(re.search(
        r"\b(?:refractory|severe|persistent|persisting)\s+(?:hypoxemic\s+)?respiratory\s+"
        r"(?:failure|distress)\b|\b(?:persistent\s+hypoxemia|hypoxemia\s+persists?|"
        r"refractory\s+hypoxemia)\b",
        t,
    ))
    if respiratory_failure_claim:
        spo2 = o.get("spo2")
        rr = o.get("respiratory_rate")
        wob = str(o.get("work_of_breathing") or "").lower()
        reassuring = []
        if spo2 is not None and spo2 >= 94:
            reassuring.append(f'SpO₂ {spo2}%')
        if rr is not None and rr <= 24:
            reassuring.append(f'respiratory rate {rr}/min')
        if wob in {"normal", "mild", "mildly increased"}:
            reassuring.append(f'work of breathing {wob}')
        if len(reassuring) >= 2 and any(x.startswith("SpO₂") for x in reassuring):
            claims.append("persistent severe or hypoxemic respiratory failure")
            facts.extend(reassuring)

    adequate_oxygenation_claim = bool(re.search(
        r"\b(?:adequate oxygenation|oxygenation (?:is|was|appears|seems) adequate|"
        r"adequately oxygenated)\b",
        t,
    ))
    if adequate_oxygenation_claim:
        abg = diagnostics.get("abg") or {}
        pf_ratio = abg.get("pf_ratio")
        fio2 = abg.get("fio2_percent")
        if fio2 is None:
            if treatments.get("invasive_ventilation"):
                fio2 = treatments.get("ventilator_fio2_percent")
            elif treatments.get("niv"):
                fio2 = treatments.get("niv_fio2_percent")
        oxygenation_facts = []
        if o.get("spo2") is not None and fio2 is not None and o.get("spo2") < 94 and float(fio2) >= 40:
            oxygenation_facts.append(f'SpO₂ {o.get("spo2")}% on FiO₂ {float(fio2):g}%')
        if pf_ratio is not None and float(pf_ratio) < 200:
            oxygenation_facts.append(f'P/F ratio {float(pf_ratio):g}')
        # Require either measured severe gas-exchange impairment or both a low
        # saturation and substantial supplemental oxygen. This keeps the prompt
        # conservative and tied to data already visible to the learner.
        if ((pf_ratio is not None and float(pf_ratio) < 200) or len(oxygenation_facts) >= 1):
            claims.append("oxygenation was adequate")
            facts.extend(oxygenation_facts)

    # Compare an explicitly stated *current* respiratory interface with the
    # interface visible at the decision point. Future transition language (for
    # example, "switch from BiPAP to invasive ventilation") is not treated as a
    # mismatch.
    support_reference = re.search(
        r"\b(?:despite|on|while\s+on|currently\s+on|receiving)\s+(?:the\s+)?"
        r"(bipap|cpap|niv|noninvasive ventilation|non-invasive ventilation|"
        r"nasal cannula|nasal canula|low-flow oxygen|room air|"
        r"invasive ventilation|mechanical ventilation|vc\s*/\s*ac|pc\s*/\s*ac)\b",
        t,
    )
    # Older traces (and imported events) may not contain a treatment snapshot.
    # Without that contemporaneous state, there is no reliable basis for an
    # interface-mismatch prompt.
    if support_reference and "treatments" in before:
        stated_raw = support_reference.group(1).lower()
        if stated_raw in {"bipap", "cpap", "niv", "noninvasive ventilation", "non-invasive ventilation"}:
            stated_support = "BiPAP" if stated_raw == "bipap" else ("CPAP" if stated_raw == "cpap" else "NIV")
        elif stated_raw in {"invasive ventilation", "mechanical ventilation", "vc/ac", "pc/ac"}:
            stated_support = "invasive ventilation"
        elif stated_raw == "room air":
            stated_support = "room air"
        else:
            stated_support = "conventional oxygen"

        if treatments.get("invasive_ventilation"):
            active_kind = "invasive ventilation"
            active_label = (
                f'{treatments.get("ventilator_mode") or "VC/AC"} invasive ventilation at FiO₂ '
                f'{treatments.get("ventilator_fio2_percent") or 40:g}% and PEEP '
                f'{treatments.get("ventilator_peep_cmh2o") or 5:g} cm H₂O'
            )
        elif treatments.get("niv"):
            active_mode = treatments.get("niv_mode") or "NIV"
            active_kind = active_mode
            active_label = active_mode
        elif treatments.get("oxygen"):
            active_kind = "conventional oxygen"
            active_label = (
                f'{treatments.get("oxygen_device") or "oxygen"} '
                f'{treatments.get("oxygen_flow_lpm") or 0:g} L/min'
            )
        else:
            active_kind = "room air"
            active_label = "room air"

        matches_active = (
            stated_support == active_kind
            or (stated_support == "NIV" and active_kind in {"BiPAP", "CPAP", "NIV"})
        )
        if not matches_active:
            claims.append(f"the current response was occurring on {stated_support}")
            facts.append(f"active respiratory support was {active_label}")

    mental_improvement_claim = bool(re.search(
        r"\b(?:mental status|mentation|mental state)\s+(?:has\s+)?improved\b|"
        r"\bimproved\s+(?:the\s+)?(?:mental status|mentation|mental state)\b",
        t,
    ))
    if mental_improvement_claim and previous_event:
        previous_before = ((previous_event.get("state_before") or {}).get("observable") or {})
        previous_after = ((previous_event.get("state_after") or {}).get("observable") or {})
        bm = str(previous_before.get("mental_status") or "").lower()
        am = str(previous_after.get("mental_status") or "").lower()
        physiologic_states = {"alert", "confused", "drowsy", "obtunded", "unresponsive"}
        rank = {"unresponsive": 0, "obtunded": 1, "confused": 2, "drowsy": 2, "alert": 3}
        if bm in physiologic_states and am in physiologic_states and rank.get(am, 0) <= rank.get(bm, 0):
            claims.append("mental status improved")
            facts.append(f'mental status was {bm} before and {am} after the preceding response')

    if not claims:
        return None

    def join_items(items):
        unique = []
        for item in items:
            if item not in unique:
                unique.append(item)
        if len(unique) == 1:
            return unique[0]
        return ", ".join(unique[:-1]) + ", and " + unique[-1]

    return (
        "Stated interpretation vs available data",
        f'You stated that {join_items(claims)}. At that decision point, the available data included '
        f'{join_items(facts)}. Which findings supported your interpretation, which findings challenged it, '
        "and how should that uncertainty have affected your next management priority?",
    )


def _ps001_classroom_review_items(events):
    """Return the three validated tachyarrhythmia teaching pivots when present.

    This mapping is deliberately narrow: alternate PS001 paths continue through
    the adaptive selector below instead of being forced into a mismatched review.
    """
    if len(events) < 9:
        return None
    first_state = (events[0][1].get("state_before") or {})
    if first_state.get("case_id") != "PS001" or first_state.get("encounter_variant"):
        return None

    action_types = {
        decision: {
            str(action.get("type") or "")
            for action in (event.get("interpreted_action") or [])
        }
        for decision, event in events
    }
    required = {
        3: "diltiazem",
        7: "cardioversion",
        9: "dobutamine",
    }
    if not all(action_type in action_types.get(decision, set()) for decision, action_type in required.items()):
        return None

    prompts = {
        3: (
            "Rate control as a diagnostic–therapeutic trial",
            "The ventricular rate fell after cautious diltiazem without immediate hypotension, while capillary "
            "refill remained abnormal. How should that response change your estimate of whether AF was a cause, "
            "a contributor, or a marker of the acute illness, and what stopping thresholds should govern another dose?",
        ),
        7: (
            "Electrical success versus clinical benefit",
            "Synchronized cardioversion converted AF to sinus rhythm and arterial pressure remained adequate, but "
            "capillary refill and mental status did not promptly improve. What does electrical success without clinical "
            "recovery imply about the arrhythmia's causal contribution, and what should become the next priority?",
        ),
        9: (
            "Pressure–flow–perfusion adaptation",
            "With sinus rhythm and an adequate MAP, reduced LV systolic function, rising lactate, cool extremities, "
            "and delayed mental recovery supported a low-output phenotype. How would you judge the benefit and risks "
            "of flow-directed support, and which early and delayed responses would determine whether to continue it?",
        ),
    }
    selected = []
    by_decision = dict(events)
    for decision in (3, 7, 9):
        event = by_decision[decision]
        label, prompt = prompts[decision]
        selected.append((
            "decision",
            decision,
            _trace_time(event.get("decision_time_min", 0)),
            label,
            prompt,
        ))
    return selected


def _reflect_compare_items(trace):
    """Generate 1–3 high-value, non-scoring prompts from structured trace data.

    Priority: stated interpretation/data alignment > critical adaptation point >
    explicit working-model shift > expected-effect/observed-response mismatch >
    missing reasoning.
    """
    filtered_events = [e for e in trace if e.get("execution_status") in {"executed", "terminal_locked"}]
    if filtered_events and str((filtered_events[0].get("state_before") or {}).get("case_id", "")).startswith("CE-"):
        from cognitive_review import reflection_items
        return reflection_items(trace)
    events = list(enumerate(filtered_events, 1))
    ps001_selector = globals().get("_ps001_classroom_review_items")
    ps001_classroom_items = ps001_selector(events) if ps001_selector else None
    if ps001_classroom_items:
        return ps001_classroom_items
    candidates = []
    covered = set()

    # 0) Explicit claims contradicted by observations already available to the
    # learner. This is a reflection trigger, not a correctness score.
    for pos, (i, event) in enumerate(events):
        previous = events[pos - 1][1] if pos > 0 else None
        prompt = _reasoning_data_alignment_prompt(event, previous)
        if prompt:
            label, text = prompt
            candidates.append((0, i, ("decision", i, _trace_time(event.get("decision_time_min", 0)), label, text)))
            covered.add(i)

    for i, event in events:
        prompt = _critical_adaptation_prompt(event)
        if prompt:
            label, text = prompt
            candidates.append((1, i, ("decision", i, _trace_time(event.get("decision_time_min", 0)), label, text)))
            covered.add(i)

    # 1) Explicit working-model shifts.
    for pos in range(1, len(events)):
        i, event = events[pos]
        _, previous = events[pos - 1]
        prompt = _model_shift_prompt(previous, event)
        if prompt:
            label, text = prompt
            candidates.append((2, i, ("decision", i, _trace_time(event.get("decision_time_min", 0)), label, text)))
            covered.add(i)

    # 2) Expected-effect/response mismatch or an explicit treatment-timing review.
    for i, event in events:
        if i in covered:
            continue
        prompt = _expected_response_prompt(event)
        if prompt:
            label, text = prompt
            candidates.append((3, i, ("decision", i, _trace_time(event.get("decision_time_min", 0)), label, text)))
            covered.add(i)

    # 3) Missing reasoning, collapsed when consecutive. Do not compete with a
    # stronger prompt on the same decision.
    missing = [(i, e) for i, e in events if i not in covered and not _reasoning_present(e.get("reasoning"))]
    groups = []
    for item in missing:
        if groups and item[0] == groups[-1][-1][0] + 1:
            groups[-1].append(item)
        else:
            groups.append([item])
    for group in groups:
        if len(group) == 1:
            i, event = group[0]
            candidates.append((4, i, ("decision", i, _trace_time(event.get("decision_time_min", 0)), "Reasoning not explicitly stated", "No management reasoning was explicitly stated. What problem representation, priority, and expected effect were guiding this action?")))
        else:
            first_i, first_e = group[0]
            last_i, last_e = group[-1]
            candidates.append((4, first_i, ("longitudinal", (first_i, last_i), (_trace_time(first_e.get("decision_time_min", 0)), _trace_time(last_e.get("decision_time_min", 0))), "Reasoning across decisions", "You made several management decisions without explicitly stating the reasoning guiding them. Looking back across this sequence, what problem representation and management priorities drove your actions, and when did your working model change?")))

    ordered = sorted(candidates, key=lambda x: (x[0], x[1]))
    expected_candidates = [candidate for candidate in candidates if candidate[0] == 3]
    if expected_candidates:
        # Reserve one reflection slot for the latest explicit expectation that
        # was not demonstrated. This prevents several earlier alignment prompts
        # from hiding the encounter's final adaptation/learning cycle.
        latest_expected = max(expected_candidates, key=lambda x: x[1])
        selected = [latest_expected]
        remaining = [candidate for candidate in ordered if candidate is not latest_expected]
        slots = 2
        while slots and remaining:
            best_priority = remaining[0][0]
            group = [candidate for candidate in remaining if candidate[0] == best_priority]
            if len(group) <= slots:
                chosen = group
            elif slots == 1:
                chosen = [group[-1]]
            else:
                # With two slots, retain both the earliest and most recent
                # example from an otherwise repetitive trigger category.
                chosen = [group[0], group[-1]]
            selected.extend(chosen)
            slots -= len(chosen)
            remaining = [candidate for candidate in remaining if candidate not in chosen]
    else:
        selected = ordered[:3]
    selected.sort(key=lambda x: x[1])
    return [x[2] for x in selected]


def render_reflect_compare(trace):
    st.markdown("### Reflect & Compare")
    st.caption("Use your Management Trace to examine how your stated interpretation aligned with the patient state available at the time. This section is reflective, not scored.")
    items = _reflect_compare_items(trace)
    if not items:
        st.info("No high-value reflection trigger was identified from the reasoning explicitly captured in this trace. Review whether each observed response matched the effect you expected.")
        return
    for kind, decision, time_text, label, text in items:
        if kind == "longitudinal":
            first_i, last_i = decision
            first_time, last_time = time_text
            heading = "Across Decisions " + str(first_i) + "–" + str(last_i) + " · " + first_time + "–" + last_time
        else:
            heading = str(time_text) + " · Decision " + str(decision)
        st.markdown("**" + heading + "**  \n*" + label + "*  \n" + text)


def _review_heading(prompt):
    """Return a stable learner-facing heading for a selected reflection prompt."""
    if prompt.get("kind") == "longitudinal":
        decisions = prompt.get("decision_range") or ["?", "?"]
        times = prompt.get("time_range") or ["?", "?"]
        return (
            f'Across Decisions {decisions[0]}–{decisions[1]} · '
            f'{times[0]}–{times[1]}'
        )
    return f'{prompt.get("time", "?")} · Decision {prompt.get("decision", "?")}'


def _review_prompt_records(trace):
    """Convert selected reflection items into stable, exportable prompt records."""
    records = []
    for kind, decision, time_text, label, prompt_text in _reflect_compare_items(trace):
        if kind == "longitudinal":
            first_i, last_i = decision
            first_time, last_time = time_text
            record = {
                "review_id": f"decisions-{first_i}-{last_i}",
                "kind": "longitudinal",
                "decision_range": [first_i, last_i],
                "time_range": [first_time, last_time],
                "label": label,
                "prompt": prompt_text,
            }
        else:
            record = {
                "review_id": f"decision-{decision}",
                "kind": "decision",
                "decision": decision,
                "time": time_text,
                "label": label,
                "prompt": prompt_text,
            }
        records.append(record)
    # A coherent, uncomplicated variant still deserves reflection. Do not
    # require a mismatch or missing reasoning before opening the learning cycle.
    if not records:
        executed = [e for e in trace if e.get("execution_status") in {"executed", "terminal_locked"}]
        if executed and (executed[-1].get("state_before") or {}).get("encounter_variant"):
            records.append({
                "review_id": "decision-" + str(len(executed)),
                "kind": "decision", "decision": len(executed),
                "time": _trace_time(executed[-1].get("decision_time_min", 0)),
                "label": "Review your management model",
                "prompt": "What response did you expect, what did you observe, and how would those observations influence your next priority?",
            })
    return records


def _event_for_review_prompt(prompt, trace):
    """Resolve a review prompt to the executed event it actually references."""
    executed = [
        event for event in (trace or [])
        if event.get("execution_status") in {"executed", "terminal_locked"}
    ]
    if prompt.get("kind") == "decision":
        decision = int(prompt.get("decision") or 0)
    elif prompt.get("kind") == "longitudinal":
        decision_range = prompt.get("decision_range") or []
        decision = int(decision_range[-1] or 0) if decision_range else 0
    else:
        decision = 0
    return executed[decision - 1] if 1 <= decision <= len(executed) else None


def _action_types_for_event(event):
    return {
        str(action.get("type") or "")
        for action in ((event or {}).get("interpreted_action") or [])
        if str(action.get("type") or "")
    }


def _trajectory_expert_model(prompt, event):
    """Build a comparison model from the referenced event, never its ordinal alone.

    This is intentionally descriptive and non-scoring. It uses only the state,
    action, learner-stated reasoning, and response stored in the frozen trace.
    """
    if not event:
        return None
    before = event.get("state_before") or {}
    if str(before.get("case_id", "")).startswith("CE-"):
        from cognitive_review import trajectory_review
        return trajectory_review(event, source_decision=prompt.get("decision"))
    after = event.get("state_after") or {}
    observable = before.get("observable") or {}
    reasoning = event.get("reasoning") or {}
    action_types = _action_types_for_event(event)
    action_text = _trace_action_text(event)
    state_text = _trace_state_text(before)
    deltas = _trace_observable_delta(before, after, reasoning)
    delta_text = "; ".join(
        f"{label} changed from {old} to {new}" for label, old, new in deltas
    ) or "no material observable change was recorded"
    sbp, dbp = observable.get("sbp"), observable.get("dbp")
    map_value = (float(sbp) + 2 * float(dbp)) / 3 if sbp is not None and dbp is not None else None
    # SSC 2026 favors an initial MAP near 65 over higher targets. Adequate
    # pressure does not exclude hypoperfusion or prove existing support is
    # unnecessary; assess those questions separately in the frozen state.
    # https://www.sccm.org/clinical-resources/guidelines/guidelines/surviving-sepsis-campaign-international-guidelines-for-management-of-sepsis-and-septic-shock-2026
    hypotension = map_value is not None and map_value < 65
    crt = int(observable.get("crt") or 0)
    impaired_perfusion = crt >= 4 or str(observable.get("mental_status") or "").lower() in {
        "drowsy", "obtunded", "unresponsive"
    } or str(observable.get("extremities") or "").lower() in {"cold", "cool", "mottled/cold"}
    existing_pressure_support = bool((before.get("treatments") or {}).get("norepinephrine_rate", 0))

    learner_problem = str(reasoning.get("problem_representation") or "").strip()
    framing = (
        f"The learner framed the problem as {learner_problem}. The actual decision began with {state_text}. "
        f"After {action_text}, {delta_text}."
        if learner_problem else
        f"The actual decision began with {state_text}. After {action_text}, {delta_text}."
    )

    if "fluid" in action_types:
        if hypotension:
            priority = (
                "Restore arterial pressure and tissue perfusion while testing preload responsiveness, without delaying "
                "vasopressor support or treatment of the underlying cause."
            )
            action = (
                "Use reassessed crystalloid aliquots with explicit pulmonary stopping criteria and begin vasopressor and "
                "cause-directed treatment concurrently when hypotension persists."
            )
        elif impaired_perfusion or map_value is None:
            priority = "Clarify pressure, tissue perfusion, and preload responsiveness before selecting further circulatory support."
            action = (
                "Reassess pressure and tissue-perfusion findings, use POCUS and a dynamic assessment of preload responsiveness "
                "when available, and give further fluid only for a demonstrated need with explicit stopping criteria. "
                "Impaired perfusion alone does not establish a need to raise arterial pressure."
            )
        else:
            priority = (
                "Verify that a clinically important preload deficit remains before giving more volume when pressure and "
                "peripheral perfusion are already adequate."
            )
            action = (
                "Observation with early reassessment or POCUS is defensible; if preload is still uncertain, use a limited "
                "fluid challenge with predefined benefit and stopping criteria."
            )
        tradeoff = (
            "Fluid may recruit preload, but an unstructured bolus can cause congestion and can delay vasopressor or "
            "source-directed treatment when vasoplegia or low output is dominant."
        )
    elif "norepinephrine" in action_types or "antibiotics" in action_types:
        if hypotension:
            priority = "Restore perfusion pressure while evaluating tissue flow and the cause of the circulatory impairment."
            action = (
                "Start or titrate norepinephrine for persistent hypotension, with reassessment of MAP and bedside "
                "tissue-perfusion markers against an individualized pressure target."
            )
        elif map_value is None:
            priority = "Establish the current arterial pressure and tissue-perfusion state before selecting pressure support."
            action = "Obtain a reliable blood pressure and reassess perfusion before deciding whether to initiate or change vasopressor support."
        elif existing_pressure_support:
            priority = "Distinguish adequate pressure on treatment from adequate tissue flow and reassess the continuing support requirement."
            action = (
                "Reassess ongoing pressure support against the individualized MAP target and tissue-perfusion findings. "
                "An adequate MAP on norepinephrine does not by itself justify either escalation or discontinuation."
            )
        else:
            priority = "Reassess tissue perfusion and the underlying cause while maintaining adequate arterial pressure."
            action = (
                "Reassess tissue perfusion, cardiac function, and the clinical trajectory before adding pressure support. "
                "The recorded arterial pressure alone does not justify starting or increasing norepinephrine."
            )
        tradeoff = (
            "Raising arterial pressure may not correct impaired tissue flow; unnecessary vasoconstriction can add harm."
        )
        if "antibiotics" in action_types:
            priority += " Treat the suspected infectious source and assess its clinical course."
            action += " Administer appropriate source-directed antimicrobials and reassess the source and treatment as further evidence becomes available."
            tradeoff += " A short-term blood pressure change alone does not establish antimicrobial efficacy or failure."
    elif "cardioversion" in action_types:
        priority = (
            "Test the causal contribution of the rhythm while protecting perfusion, and define success by clinical recovery "
            "rather than electrical conversion alone."
        )
        action = (
            "Perform synchronized cardioversion with appropriate procedural sedation and ongoing circulatory monitoring, "
            "then reassess rhythm and tissue perfusion promptly."
        )
        tradeoff = (
            "Electrical conversion may improve filling, but it may not reverse another cause of shock and introduces "
            "procedural and sedation risk."
        )
    elif "dobutamine" in action_types:
        priority = (
            "Improve forward flow while preserving arterial pressure and monitoring for recurrent tachyarrhythmia."
        )
        action = (
            "Use a low-dose inotropic trial while maintaining necessary pressure support, with explicit continuation and "
            "stopping criteria based on perfusion, pressure, and rhythm."
        )
        tradeoff = (
            "Dobutamine may improve cardiac output but can cause vasodilation, hypotension, or tachyarrhythmia; lactate and "
            "mental status may lag behind early peripheral changes."
        )
    elif action_types & {"pocus", "lactate", "vbg", "abg", "basic_labs", "urinalysis", "chest_xray", "blood_cultures"}:
        priority = (
            str(reasoning.get("management_priority") or "Clarify the active physiologic phenotype or underlying cause before the next treatment change.")
        )
        action = (
            f"Obtain {action_text}, interpret the results with the current clinical state, and avoid allowing diagnostic delay "
            "to postpone immediate support when the patient is unstable."
        )
        tradeoff = (
            "Diagnostic information can refine treatment, but waiting for results during deterioration can delay time-sensitive support."
        )
    elif "reassessment" in action_types:
        priority = "Determine whether the current trajectory is stable, improving, or deteriorating before the next intervention."
        action = f"Perform the planned {action_text} and respond immediately to predefined pressure, perfusion, neurologic, or respiratory thresholds."
        tradeoff = "Observation preserves diagnostic clarity, but passive delay is unsafe if predefined deterioration thresholds are already present."
    else:
        priority = str(reasoning.get("management_priority") or "Address the dominant physiologic threat and reassess its response explicitly.")
        action = f"A defensible approach is {action_text}, paired with explicit benefit, harm, and reassessment thresholds."
        tradeoff = "The expected benefit must be weighed against treatment harm and the risk of delaying management of another active problem."

    pressure_label = f"{sbp}/{dbp} mmHg" if map_value is not None else "unavailable"
    map_label = f"MAP approximately {round(map_value)}" if map_value is not None else "MAP unavailable"
    before_cue = (
        f"At the decision point: BP {pressure_label} ({map_label}), "
        f"HR {observable.get('hr')}/min in {observable.get('rhythm')}."
    )
    perfusion_cue = (
        f"Tissue-perfusion findings were capillary refill {observable.get('crt')} seconds, "
        f"{str(observable.get('extremities') or '').lower()} extremities, and mental status "
        f"{str(observable.get('mental_status') or '').lower()}."
    )
    response_cue = f"Observed after the action: {delta_text}."
    reassessment = str(reasoning.get("reassessment_target") or "BP/MAP, HR and rhythm, capillary refill, extremities, mental status, SpO2, and work of breathing")
    if not re.search(r"\b(?:minute|minutes|\bmin\b|hour|hours)\b", reassessment, re.I):
        reassessment += " at the explicitly planned interval"
    return {
        "framing": framing,
        "priority": priority,
        "cues": [before_cue, perfusion_cue, response_cue],
        "action": action,
        "tradeoff": tradeoff,
        "reassessment": reassessment + ".",
        "trajectory_grounded": True,
        "source_decision": prompt.get("decision"),
        "source_action_types": sorted(action_types),
    }


def _expert_model_for_prompt(case_id, prompt, trace=None):
    """Return a model only when it matches the referenced frozen-trace action."""
    event = _event_for_review_prompt(prompt, trace) if trace is not None else None
    if trace is not None and not event:
        return None

    if event and (event.get("state_before") or {}).get("encounter_variant"):
        return _trajectory_expert_model(prompt, event)

    static_model = None
    if prompt.get("kind") == "decision":
        static_model = deepcopy(
            (EXPERT_REASONING_MODELS.get(str(case_id or ""), {}) or {}).get(prompt.get("decision"))
        )
    # Static faculty drafts are valid only for their validated action pivot.
    required_actions = {
        "PS001": {3: {"diltiazem"}, 7: {"cardioversion"}, 9: {"dobutamine"}},
        "PS002": {2: {"niv"}, 9: {"norepinephrine"}, 11: {"dobutamine"}},
    }
    required = (required_actions.get(str(case_id or ""), {}) or {}).get(prompt.get("decision"))
    if static_model and (trace is None or not required or required <= _action_types_for_event(event)):
        static_model["trajectory_grounded"] = True
        static_model["source_decision"] = prompt.get("decision")
        static_model["source_action_types"] = sorted(_action_types_for_event(event)) if event else []
        return static_model
    return _trajectory_expert_model(prompt, event) if trace is not None else static_model


def _expert_models_for_prompts(case_id, prompts, trace=None):
    models = {}
    for prompt in prompts or []:
        model = _expert_model_for_prompt(case_id, prompt, trace)
        if model:
            models[prompt.get("review_id")] = model
    return models


def _decision_review_complete(prompts, responses):
    if not prompts:
        return False
    for prompt in prompts:
        answer = responses.get(prompt.get("review_id"), {}) or {}
        if any(not str(answer.get(field) or "").strip() for field, _ in REVIEW_RESPONSE_FIELDS):
            return False
    return True


def _expert_comparison_complete(expert_models, comparison_responses):
    if not expert_models:
        return True
    for review_id in expert_models:
        answer = comparison_responses.get(review_id, {}) or {}
        if any(not str(answer.get(field) or "").strip() for field, _ in EXPERT_COMPARISON_FIELDS):
            return False
    return True


def _strip_private_review_data(value):
    """Deep-copy learner export data while excluding engine-only physiology."""
    private_keys = {
        "physiology", "hidden", "developer_state", "encounter_spec", "encounter_facts",
        "clinical_case", "faculty", "faculty_brief", "faculty_analysis", "faculty_assessment",
        "teaching_context", "response_rules", "engine_config",
    }
    if isinstance(value, dict):
        return {
            key: _strip_private_review_data(item)
            for key, item in value.items()
            if key not in private_keys
        }
    if isinstance(value, list):
        return [_strip_private_review_data(item) for item in value]
    if isinstance(value, tuple):
        return [_strip_private_review_data(item) for item in value]
    return deepcopy(value)


def _review_is_complete(
    prompts,
    responses,
    adaptation_plan,
    expert_models=None,
    comparison_responses=None,
    comparison_unlocked=False,
):
    """A review is complete only when every selected prompt and plan field is addressed."""
    if not prompts:
        return False
    for prompt in prompts:
        answer = responses.get(prompt.get("review_id"), {}) or {}
        for field, _ in REVIEW_RESPONSE_FIELDS:
            if not str(answer.get(field) or "").strip():
                return False
    for field, _ in ADAPTATION_PLAN_FIELDS:
        if not str((adaptation_plan or {}).get(field) or "").strip():
            return False
    if expert_models:
        if not comparison_unlocked:
            return False
        if not _expert_comparison_complete(expert_models, comparison_responses or {}):
            return False
    return True


def _review_payload(
    case_label,
    closed_time_min,
    trace,
    final_state,
    prompts,
    responses,
    adaptation_plan,
    comparison_responses=None,
    comparison_unlocked=False,
    attempt_number=1,
    carry_forward_plan=None,
    prior_attempt_summary=None,
):
    """Build the versioned, learner-facing Decision Review export payload."""
    clean_trace = _strip_private_review_data(trace or [])
    clean_final_state = _strip_private_review_data(final_state or {})
    prompt_reviews = []
    for prompt in prompts or []:
        record = _strip_private_review_data(prompt)
        record["heading"] = _review_heading(prompt)
        record["responses"] = {
            field: str((responses.get(prompt.get("review_id"), {}) or {}).get(field) or "").strip()
            for field, _ in REVIEW_RESPONSE_FIELDS
        }
        prompt_reviews.append(record)
    clean_plan = {
        field: str((adaptation_plan or {}).get(field) or "").strip()
        for field, _ in ADAPTATION_PLAN_FIELDS
    }
    clean_carry_forward = {
        field: str((carry_forward_plan or {}).get(field) or "").strip()
        for field, _ in ADAPTATION_PLAN_FIELDS
    }
    expert_models = _expert_models_for_prompts(
        clean_final_state.get("case_id"), prompts or [], clean_trace
    )
    comparison_records = []
    if comparison_unlocked:
        for prompt in prompts or []:
            review_id = prompt.get("review_id")
            model = expert_models.get(review_id)
            if not model:
                continue
            comparison_records.append({
                "review_id": review_id,
                "heading": _review_heading(prompt),
                "model_status": "faculty-validation draft",
                "expert_model": _strip_private_review_data(model),
                "learner_comparison": {
                    field: str(((comparison_responses or {}).get(review_id, {}) or {}).get(field) or "").strip()
                    for field, _ in EXPERT_COMPARISON_FIELDS
                },
            })
    return {
        "schema": "management_reasoning_decision_review_v3",
        "simulator": {
            "name": "Management Reasoning Simulator",
            "version": SIMULATOR_VERSION,
        },
        "encounter": {
            "case_id": clean_final_state.get("case_id"),
            # Which authored case this was, read before the spec is stripped. The
            # spec itself never leaves the engine: it holds the answers. This is
            # only its identifier, and the rubric cannot look up a case's declared
            # opportunities and critical events without it.
            "authored_case_id": str((((final_state or {}).get("encounter_spec") or {})
                                     .get("clinical_case") or {}).get("id") or ""),
            "case_label": case_label,
            "closed_time_min": int(closed_time_min or 0),
            "final_patient_state": clean_final_state,
        },
        "learning_cycle": {
            "attempt_number": max(1, int(attempt_number or 1)),
            "carry_forward_plan": clean_carry_forward,
            "prior_attempt_summary": _strip_private_review_data(prior_attempt_summary),
        },
        "management_trace": {
            "definition": MANAGEMENT_TRACE_DEFINITION,
            "descriptive_not_scored": True,
            "events": clean_trace,
        },
        "decision_review": {
            "retrospective": True,
            "locked_before_expert_reveal": bool(comparison_unlocked),
            "prompts": prompt_reviews,
        },
        "expert_comparison": {
            "revealed": bool(comparison_unlocked),
            "non_scoring": True,
            "one_defensible_approach_not_answer_key": True,
            "comparisons": comparison_records,
        },
        "adaptation_plan": {
            "prospective": True,
            **clean_plan,
        },
        "review_complete": _review_is_complete(
            prompts or [],
            responses or {},
            adaptation_plan or {},
            expert_models,
            comparison_responses or {},
            bool(comparison_unlocked),
        ),
    }


def _review_markdown(payload):
    """Render a portable Markdown review without hidden engine state."""
    encounter = payload.get("encounter", {})
    trace_block = payload.get("management_trace", {})
    lines = [
        "# Management Reasoning Decision Review",
        "",
        f'- **Simulator:** Management Reasoning Simulator v{payload.get("simulator", {}).get("version", SIMULATOR_VERSION)}',
        f'- **Case:** {encounter.get("case_label") or encounter.get("case_id") or "—"}',
        f'- **Encounter closed:** {_trace_time(encounter.get("closed_time_min", 0))}',
        f'- **Attempt:** {int((payload.get("learning_cycle", {}) or {}).get("attempt_number", 1))}',
        f'- **Review status:** {"Complete" if payload.get("review_complete") else "Draft"}',
        "",
    ]
    carry_forward = (payload.get("learning_cycle", {}) or {}).get("carry_forward_plan", {}) or {}
    if any(str(carry_forward.get(field) or "").strip() for field, _ in ADAPTATION_PLAN_FIELDS):
        lines.extend([
            "## Carry-Forward Plan",
            "",
            "Prospective learning intention brought into this repeat attempt.",
            "",
        ])
        for field, label in ADAPTATION_PLAN_FIELDS:
            lines.extend([f'**{label}**', "", str(carry_forward.get(field) or "—"), ""])
    lines.extend([
        "## Management Trace",
        "",
        "> " + str(trace_block.get("definition") or MANAGEMENT_TRACE_DEFINITION),
        "",
        "This trace is descriptive and non-scoring. It does not add reasoning that the learner did not explicitly state.",
        "",
    ])
    events = [
        event for event in trace_block.get("events", [])
        if event.get("execution_status") in {"executed", "terminal_locked"}
    ]
    if not events:
        lines.extend(["No executed management decisions were recorded.", ""])
    for index, event in enumerate(events, 1):
        before = event.get("state_before") or {}
        after = event.get("state_after") or {}
        response_time = after.get("sim_time_min", event.get("response_time_min", 0))
        lines.extend([
            f'### {_trace_time(event.get("decision_time_min", 0))} · Decision {index}',
            "",
            "**Patient state**",
            "",
            _trace_state_text(before),
            "",
            "**Management reasoning**",
            "",
        ])
        reasoning_items = _trace_reasoning_items(event.get("reasoning"))
        if reasoning_items:
            for label, value in reasoning_items:
                lines.append(f'- **{label}:** {value}')
        else:
            lines.append("*Not explicitly stated*")
        lines.extend([
            "",
            "**Original learner input**",
            "",
            str(event.get("learner_input") or "—"),
            "",
            "**Action**",
            "",
            _trace_action_text(event),
            "",
            f'**Observed response · {_trace_time(response_time)}**',
            "",
        ])
        deltas = _trace_observable_delta(before, after, event.get("reasoning"))
        diagnostics = _trace_diagnostic_results(event)
        if deltas:
            for label, old, new in deltas:
                lines.append(f'- **{label}:** {old} → {new}')
        if diagnostics:
            for time_text, result_text in diagnostics:
                # Keep a multi-line report such as POCUS inside its list item.
                lines.append(f'- **Diagnostic result · {time_text}:** ' + str(result_text).replace("\n", "  \n  "))
        if not deltas and not diagnostics:
            lines.append("*No material observable change recorded.*")
        lines.append("")

    lines.extend([
        "## Decision Review",
        "",
        "Retrospective learner reflection. These responses do not alter the Management Trace above.",
        "",
    ])
    prompts = payload.get("decision_review", {}).get("prompts", [])
    if not prompts:
        lines.extend(["No reflection prompt was generated.", ""])
    for prompt in prompts:
        lines.extend([
            f'### {prompt.get("heading", "Review prompt")}',
            "",
            f'*{prompt.get("label", "Reflection")}*',
            "",
            str(prompt.get("prompt") or ""),
            "",
        ])
        answers = prompt.get("responses", {}) or {}
        for field, label in REVIEW_RESPONSE_FIELDS:
            lines.extend([f'**{label}**', "", str(answers.get(field) or "*Not answered*"), ""])

    lines.extend([
        "## Expert Comparison",
        "",
        "One defensible expert reasoning model for comparison. It is non-scoring, is not an answer key, and requires faculty validation.",
        "",
    ])
    comparison_block = payload.get("expert_comparison", {}) or {}
    comparisons = comparison_block.get("comparisons", []) if comparison_block.get("revealed") else []
    if not comparisons:
        lines.extend(["Expert comparison has not been revealed.", ""])
    for comparison in comparisons:
        model = comparison.get("expert_model", {}) or {}
        learner_comparison = comparison.get("learner_comparison", {}) or {}
        lines.extend([
            f'### {comparison.get("heading", "Comparison point")}',
            "",
            "**Expert framing**",
            "",
            str(model.get("framing") or "—"),
            "",
            "**Management priority**",
            "",
            str(model.get("priority") or "—"),
            "",
            "**Key cues**",
            "",
        ])
        for cue in model.get("cues", []) or []:
            lines.append("- " + str(cue))
        lines.extend([
            "",
            "**One defensible action**",
            "",
            str(model.get("action") or "—"),
            "",
            "**Trade-off to manage**",
            "",
            str(model.get("tradeoff") or "—"),
            "",
            "**Reassessment targets**",
            "",
            str(model.get("reassessment") or "—"),
            "",
        ])
        for field, label in EXPERT_COMPARISON_FIELDS:
            lines.extend([f'**{label}**', "", str(learner_comparison.get(field) or "*Not answered*"), ""])

    lines.extend([
        "## Adaptation Plan",
        "",
        "Prospective commitment for a similar future encounter.",
        "",
    ])
    plan = payload.get("adaptation_plan", {}) or {}
    for field, label in ADAPTATION_PLAN_FIELDS:
        lines.extend([f'**{label}**', "", str(plan.get(field) or "*Not answered*"), ""])
    lines.extend([
        "---",
        "This review is reflective and non-scoring. The expert model is one defensible approach, not an answer key.",
        "",
    ])
    return "\n".join(lines)


def _review_json(payload):
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _pdf_safe_text(value):
    """Normalize learner-facing text for ReportLab's built-in PDF fonts."""
    text = str(value if value is not None else "")
    replacements = {
        "SpO₂": "SpO2",
        "FiO₂": "FiO2",
        "pCO₂": "pCO2",
        "HCO₃": "HCO3",
        "H₂O": "H2O",
        "₂": "2",
        "₃": "3",
        "µ": "u",
        "→": "->",
        "–": "-",
        "—": "-",
        "‑": "-",
        "−": "-",
        "≥": ">=",
        "≤": "<=",
        "≈": "approximately",
        "×": "x",
        "•": "-",
        "“": '"',
        "”": '"',
        "’": "'",
        "‘": "'",
        "…": "...",
        "\u00a0": " ",
        "\u202f": " ",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    return text


def _review_pdf(payload):
    """Render a printable, privacy-safe PDF of the learner review record."""
    from pathlib import Path
    from xml.sax.saxutils import escape as xml_escape

    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (
        CondPageBreak,
        KeepTogether,
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
    from pathlib import Path

    # Embed a complete font family so the PDF renders identically on macOS,
    # Windows, and Linux. The prior non-embedded Helvetica metrics produced
    # excessive character spacing and nearly invisible word spaces in some PDF
    # viewers and Poppler substitutions.
    font_dir = Path(globals().get("__file__", "app.py")).resolve().parent / "assets" / "fonts"
    font_files = {
        "MRS-Regular": font_dir / "LiberationSans-Regular.ttf",
        "MRS-Bold": font_dir / "LiberationSans-Bold.ttf",
        "MRS-Italic": font_dir / "LiberationSans-Italic.ttf",
    }
    registered = set(pdfmetrics.getRegisteredFontNames())
    for font_name, font_path in font_files.items():
        if font_name not in registered:
            pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
    pdfmetrics.registerFontFamily(
        "MRS",
        normal="MRS-Regular",
        bold="MRS-Bold",
        italic="MRS-Italic",
        boldItalic="MRS-Bold",
    )

    navy = colors.HexColor("#17324D")
    blue = colors.HexColor("#357ABD")
    pale_blue = colors.HexColor("#F2F7FC")
    pale_green = colors.HexColor("#EEF8F0")
    mid_gray = colors.HexColor("#66758A")
    light_gray = colors.HexColor("#E4EAF0")
    dark = colors.HexColor("#1F2937")

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "MRS_Title",
        parent=styles["Title"],
        fontName="MRS-Bold",
        fontSize=21,
        leading=25,
        textColor=navy,
        alignment=TA_LEFT,
        spaceAfter=8,
    )
    subtitle_style = ParagraphStyle(
        "MRS_Subtitle",
        parent=styles["Normal"],
        fontName="MRS-Regular",
        fontSize=9.5,
        leading=13,
        textColor=mid_gray,
        spaceAfter=13,
    )
    section_style = ParagraphStyle(
        "MRS_Section",
        parent=styles["Heading1"],
        fontName="MRS-Bold",
        fontSize=15,
        leading=18,
        textColor=navy,
        spaceBefore=4,
        spaceAfter=9,
    )
    decision_style = ParagraphStyle(
        "MRS_Decision",
        parent=styles["Heading2"],
        fontName="MRS-Bold",
        fontSize=11.5,
        leading=14,
        textColor=blue,
        spaceBefore=8,
        spaceAfter=5,
    )
    body_style = ParagraphStyle(
        "MRS_Body",
        parent=styles["BodyText"],
        fontName="MRS-Regular",
        fontSize=9,
        leading=12.2,
        textColor=dark,
        spaceAfter=4,
    )
    small_style = ParagraphStyle(
        "MRS_Small",
        parent=body_style,
        fontSize=8,
        leading=10.5,
        textColor=mid_gray,
    )
    label_style = ParagraphStyle(
        "MRS_Label",
        parent=body_style,
        fontName="MRS-Bold",
        fontSize=8.2,
        leading=10,
        textColor=navy,
        spaceBefore=3,
        spaceAfter=2,
    )
    centered_small_style = ParagraphStyle(
        "MRS_CenteredSmall",
        parent=small_style,
        alignment=TA_CENTER,
    )

    def safe(value):
        return xml_escape(_pdf_safe_text(value)).replace("\n", "<br/>")

    def paragraph(value, style=body_style):
        normalized = str(value or "").strip()
        return Paragraph(safe(normalized or "Not recorded"), style)

    def add_labeled_value(story, label, value, missing="Not answered"):
        story.append(Paragraph(safe(label), label_style))
        story.append(paragraph(value or missing))

    encounter = payload.get("encounter", {}) or {}
    learning_cycle = payload.get("learning_cycle", {}) or {}
    case_id = str(encounter.get("case_id") or "Encounter")
    case_label = encounter.get("case_label") or case_id
    version = str((payload.get("simulator", {}) or {}).get("version") or SIMULATOR_VERSION)
    status = "Complete" if payload.get("review_complete") else "Draft"

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.62 * inch,
        rightMargin=0.62 * inch,
        topMargin=0.67 * inch,
        bottomMargin=0.58 * inch,
        title=f"{case_id} Management Reasoning Decision Review",
        author="Management Reasoning Simulator",
        subject="Reflective, non-scoring clinical management review",
    )

    def draw_page_frame(canvas, doc):
        page_width, page_height = letter
        canvas.saveState()
        canvas.setStrokeColor(light_gray)
        canvas.setLineWidth(0.6)
        canvas.line(doc.leftMargin, page_height - 0.45 * inch, page_width - doc.rightMargin, page_height - 0.45 * inch)
        canvas.setFont("MRS-Bold", 7.5)
        canvas.setFillColor(navy)
        canvas.drawString(doc.leftMargin, page_height - 0.31 * inch, f"Management Reasoning Simulator v{version}")
        canvas.setFont("MRS-Regular", 7.5)
        canvas.setFillColor(mid_gray)
        canvas.drawRightString(page_width - doc.rightMargin, page_height - 0.31 * inch, _pdf_safe_text(case_id))
        canvas.line(doc.leftMargin, 0.43 * inch, page_width - doc.rightMargin, 0.43 * inch)
        canvas.drawString(doc.leftMargin, 0.25 * inch, "Educational simulation - reflective and non-scoring")
        canvas.drawRightString(page_width - doc.rightMargin, 0.25 * inch, f"Page {doc.page}")
        canvas.restoreState()

    story = [
        Paragraph("Management Reasoning<br/>Decision Review", title_style),
        Paragraph(
            "A portable record of the clinical trajectory, learner reflection, expert comparison, and prospective adaptation plan.",
            subtitle_style,
        ),
    ]
    metadata = [
        [Paragraph("CASE", label_style), Paragraph("CLOSED", label_style), Paragraph("ATTEMPT", label_style), Paragraph("STATUS", label_style)],
        [
            paragraph(case_label),
            paragraph(_trace_time(encounter.get("closed_time_min", 0))),
            paragraph(str(max(1, int(learning_cycle.get("attempt_number", 1) or 1)))),
            Paragraph(safe(status), ParagraphStyle("MRS_Status", parent=body_style, fontName="MRS-Bold", textColor=colors.HexColor("#16743B") if status == "Complete" else colors.HexColor("#9A6700"))),
        ],
    ]
    metadata_table = Table(metadata, colWidths=[document.width * 0.46, document.width * 0.18, document.width * 0.16, document.width * 0.20])
    metadata_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), pale_blue),
        ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#B9CCE0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, light_gray),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.extend([metadata_table, Spacer(1, 10)])

    carry_forward = learning_cycle.get("carry_forward_plan", {}) or {}
    if any(str(carry_forward.get(field) or "").strip() for field, _ in ADAPTATION_PLAN_FIELDS):
        story.append(Paragraph("Carry-Forward Plan", section_style))
        story.append(Paragraph("Prospective learning intention brought into this repeat attempt.", small_style))
        for field, label in ADAPTATION_PLAN_FIELDS:
            add_labeled_value(story, label, carry_forward.get(field), missing="Not specified")
        story.append(PageBreak())

    trace_block = payload.get("management_trace", {}) or {}
    story.append(Paragraph("Management Trace", section_style))
    definition_table = Table([[paragraph(trace_block.get("definition") or MANAGEMENT_TRACE_DEFINITION, small_style)]], colWidths=[document.width])
    definition_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), pale_blue),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#B9CCE0")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.extend([
        definition_table,
        Spacer(1, 5),
        Paragraph("Descriptive and non-scoring. No reasoning is added unless the learner explicitly stated it.", small_style),
    ])
    events = [
        event for event in trace_block.get("events", [])
        if event.get("execution_status") in {"executed", "terminal_locked"}
    ]
    if not events:
        story.append(paragraph("No executed management decisions were recorded."))
    for index, event in enumerate(events, 1):
        before = event.get("state_before") or {}
        after = event.get("state_after") or {}
        response_time = after.get("sim_time_min", event.get("response_time_min", 0))
        heading = f'{_trace_time(event.get("decision_time_min", 0))} | Decision {index}'
        story.append(CondPageBreak(3.15 * inch))
        story.append(KeepTogether([
            Paragraph(safe(heading), decision_style),
            Table(
                [[Paragraph("PATIENT STATE", label_style), paragraph(_trace_state_text(before))]],
                colWidths=[document.width * 0.18, document.width * 0.82],
                style=TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FAFBFC")),
                    ("BOX", (0, 0), (-1, -1), 0.45, light_gray),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]),
            ),
        ]))
        story.append(Paragraph("Management reasoning", label_style))
        reasoning_items = _trace_reasoning_items(event.get("reasoning"))
        if reasoning_items:
            for label, value in reasoning_items:
                story.append(Paragraph(f"<b>{safe(label)}:</b> {safe(value)}", body_style))
        else:
            story.append(Paragraph("<i>Not explicitly stated</i>", body_style))
        add_labeled_value(story, "Original learner input", event.get("learner_input"), missing="Not recorded")
        add_labeled_value(story, "Action", _trace_action_text(event), missing="No executed action recorded")
        response_story = [Paragraph(safe(f"Observed response | {_trace_time(response_time)}"), label_style)]
        deltas = _trace_observable_delta(before, after, event.get("reasoning"))
        diagnostics = _trace_diagnostic_results(event)
        if deltas:
            for label, old, new in deltas:
                response_story.append(Paragraph(f"- <b>{safe(label)}:</b> {safe(old)} -&gt; {safe(new)}", body_style))
        if diagnostics:
            for time_text, result_text in diagnostics:
                response_story.append(Paragraph(f"- <b>Diagnostic result | {safe(time_text)}:</b> " + safe(result_text).replace("\n", "<br/>"), body_style))
        if not deltas and not diagnostics:
            response_story.append(Paragraph("<i>No material observable change recorded.</i>", body_style))
        story.append(KeepTogether(response_story))
        story.append(Spacer(1, 5))

    story.append(PageBreak())
    story.append(Paragraph("Decision Review", section_style))
    story.append(Paragraph("Retrospective learner reflection. These responses do not alter the Management Trace.", small_style))
    prompts = (payload.get("decision_review", {}) or {}).get("prompts", []) or []
    if not prompts:
        story.append(paragraph("No reflection prompt was generated."))
    for prompt in prompts:
        story.append(CondPageBreak(2.9 * inch))
        story.append(Paragraph(safe(prompt.get("heading") or "Review prompt"), decision_style))
        if prompt.get("label"):
            story.append(Paragraph(f"<i>{safe(prompt.get('label'))}</i>", body_style))
        story.append(paragraph(prompt.get("prompt"), small_style))
        answers = prompt.get("responses", {}) or {}
        for field, label in REVIEW_RESPONSE_FIELDS:
            add_labeled_value(story, label, answers.get(field))

    story.append(PageBreak())
    story.append(Paragraph("Expert Comparison", section_style))
    story.append(Paragraph(
        "One defensible expert reasoning model for comparison. It is non-scoring, is not an answer key, and requires faculty validation.",
        small_style,
    ))
    comparison_block = payload.get("expert_comparison", {}) or {}
    comparisons = comparison_block.get("comparisons", []) if comparison_block.get("revealed") else []
    if not comparisons:
        story.append(paragraph("Expert comparison has not been revealed."))
    for comparison in comparisons:
        model = comparison.get("expert_model", {}) or {}
        learner_comparison = comparison.get("learner_comparison", {}) or {}
        comparison_story = [
            Paragraph(safe(comparison.get("heading") or "Comparison point"), decision_style)
        ]
        add_labeled_value(comparison_story, "Expert framing", model.get("framing"), missing="Not specified")
        add_labeled_value(comparison_story, "Management priority", model.get("priority"), missing="Not specified")
        comparison_story.append(Paragraph("Key cues", label_style))
        cues = model.get("cues", []) or []
        if cues:
            for cue in cues:
                comparison_story.append(Paragraph(f"- {safe(cue)}", body_style))
        else:
            comparison_story.append(paragraph("Not specified", body_style))
        add_labeled_value(comparison_story, "One defensible action", model.get("action"), missing="Not specified")
        add_labeled_value(comparison_story, "Trade-off to manage", model.get("tradeoff"), missing="Not specified")
        add_labeled_value(comparison_story, "Reassessment targets", model.get("reassessment"), missing="Not specified")
        for field, label in EXPERT_COMPARISON_FIELDS:
            add_labeled_value(comparison_story, label, learner_comparison.get(field))
        story.append(KeepTogether(comparison_story))
        story.append(Spacer(1, 6))

    story.append(PageBreak())
    story.append(Paragraph("Prospective Adaptation Plan", section_style))
    story.append(Paragraph("A learner-authored commitment for a similar future encounter.", small_style))
    plan = payload.get("adaptation_plan", {}) or {}
    plan_rows = []
    for field, label in ADAPTATION_PLAN_FIELDS:
        plan_rows.append([
            Paragraph(safe(label), label_style),
            paragraph(plan.get(field) or "Not answered"),
        ])
    plan_table = Table(plan_rows, colWidths=[document.width * 0.28, document.width * 0.72], repeatRows=0)
    plan_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), pale_blue),
        ("BACKGROUND", (1, 0), (1, -1), colors.white),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#B9CCE0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, light_gray),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.extend([plan_table, Spacer(1, 12)])
    closing_table = Table(
        [[Paragraph(
            safe("Review complete and ready to export." if payload.get("review_complete") else "Draft review - incomplete fields remain."),
            centered_small_style,
        )]],
        colWidths=[document.width],
    )
    closing_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), pale_green if payload.get("review_complete") else colors.HexColor("#FFF7E6")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#BFD9C6") if payload.get("review_complete") else colors.HexColor("#E6C56E")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.extend([
        closing_table,
        Spacer(1, 9),
        Paragraph(
            "This report supports facilitated reflection and deliberate practice. It does not provide a score or replace clinical supervision.",
            centered_small_style,
        ),
    ])

    document.build(story, onFirstPage=draw_page_frame, onLaterPages=draw_page_frame)
    return buffer.getvalue()


def _review_widget_key(review_id, field):
    return f"decision_review__{review_id}__{field}"


def _adaptation_widget_key(field):
    return f"adaptation_plan__{field}"


def _comparison_widget_key(review_id, field):
    return f"expert_comparison__{review_id}__{field}"


def _compact_text(value, limit=220):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "…"


def _latest_review_response(prompts, responses, field):
    for prompt in reversed(prompts or []):
        answer = (responses.get(prompt.get("review_id"), {}) or {}).get(field)
        if str(answer or "").strip():
            return str(answer).strip()
    return ""


def _normalize_review_text(text):
    """Normalize pasted review prose without changing its clinical content."""
    value = re.sub(r"\s+", " ", str(text or "")).strip()
    # A rapid paste can join two answers as ``threshold.Immediately``. Restore
    # the sentence boundary so downstream drafting cannot merge plan fields.
    return re.sub(r"(?<=[.!?])(?=[A-Z])", " ", value)


def _first_review_sentence(text):
    """Return one complete learner-authored sentence from a review response."""
    value = _normalize_review_text(text)
    if not value:
        return ""
    return re.split(r"(?<=[.!?])\s+(?=[A-Z])", value, maxsplit=1)[0].strip()


def _ensure_terminal_punctuation(text):
    value = str(text or "").strip()
    if value and value[-1] not in ".!?":
        value += "."
    return value


def _cue_from_priority_trigger(text):
    """Isolate clinical conditions without relabeling a treatment as a cue."""
    value = _normalize_review_text(text)
    if not value:
        return ""
    conditions = []
    for sentence in re.split(r"(?<=[.!?])\s+", value):
        sentence = sentence.strip()
        if not sentence:
            continue
        trigger = re.search(r"\b(?:should|would|must|will)\s+trigger\b", sentence, re.I)
        if trigger:
            candidate = sentence[:trigger.start()].rstrip(" ,;:-")
        else:
            conditional = re.search(r"\b(?:if|when|while|unless)\s+(.+)$", sentence, re.I)
            if conditional:
                candidate = conditional.group(1)
                candidate = re.split(
                    r",\s*(?:the\s+)?(?:hemodynamic\s+phenotype|management|priority|course|"
                    r"treatment|support)\s+(?:should|would|must|will)\b",
                    candidate,
                    maxsplit=1,
                    flags=re.I,
                )[0]
            elif re.search(
                r"\b(?:start|stop|give|administer|titrate|increase|decrease|continue|"
                r"reassess|perform|obtain)\b",
                sentence,
                re.I,
            ):
                # This sentence is an action without an explicit condition.
                continue
            else:
                candidate = sentence
        candidate = _clean_reasoning_phrase(candidate)
        if candidate and candidate.lower() not in {item.lower() for item in conditions}:
            conditions.append(candidate)
    return _ensure_terminal_punctuation("; ".join(conditions[:3]))


def _threshold_from_priority_trigger(text):
    """Turn the learner's clinical conditions into one nonduplicated threshold."""
    value = _normalize_review_text(text)
    if not value:
        return ""
    sentence = _first_review_sentence(value)
    if re.search(r"\b(?:should|would|must|will)\s+trigger\b", sentence, re.I):
        return _ensure_terminal_punctuation(sentence)
    cue = _cue_from_priority_trigger(value).rstrip(".!? ")
    if cue:
        return _ensure_terminal_punctuation("Change course if " + cue)
    return ""


def _split_expected_reassessment(text):
    """Separate an expected response from an explicitly stated reassessment clause."""
    value = _normalize_review_text(text)
    if not value:
        return "", ""
    match = re.search(r"\b(?:(?:and\s+)?(?:I\s+)?would\s+)?reassess\b", value, re.I)
    if not match:
        return value, value
    expected = _ensure_terminal_punctuation(value[:match.start()].rstrip(" ;,."))
    reassessment = value[match.start():].strip()
    if re.match(r"and\s+would\s+reassess", reassessment, re.I):
        reassessment = re.sub(r"^and\s+would\s+reassess", "Reassess", reassessment, flags=re.I)
    return expected or value, reassessment or value


def _suggest_adaptation_plan(prompts, responses):
    """Draft only the plan fields that can be grounded in the learner's own review."""
    trigger = _latest_review_response(prompts, responses, "priority_trigger")
    action = _latest_review_response(prompts, responses, "alternative_action")
    expected_text = _latest_review_response(prompts, responses, "expected_response_reassessment")
    expected, reassessment = _split_expected_reassessment(expected_text)
    return {
        "cue": _cue_from_priority_trigger(trigger),
        "threshold": _threshold_from_priority_trigger(trigger),
        # Deliberately left for the learner: a priority should not be inferred
        # from an action or silently added to the Management Trace.
        "next_priority": "",
        "alternative_action": action,
        "expected_effect": expected,
        "reassessment_plan": reassessment,
    }


def _merge_adaptation_suggestions(adaptation_plan, user_edited, suggestions):
    """Refresh suggested text without overwriting any field the learner edited."""
    merged = deepcopy(adaptation_plan or {})
    for field, _ in ADAPTATION_PLAN_FIELDS:
        if not bool((user_edited or {}).get(field)) and str((suggestions or {}).get(field) or "").strip():
            merged[field] = str(suggestions[field]).strip()
        else:
            merged.setdefault(field, "")
    return merged


def _review_progress(
    prompts,
    responses,
    adaptation_plan,
    expert_models=None,
    comparison_responses=None,
):
    decisions_complete = 0
    review_fields_filled = 0
    for prompt in prompts or []:
        answer = responses.get(prompt.get("review_id"), {}) or {}
        filled = sum(bool(str(answer.get(field) or "").strip()) for field, _ in REVIEW_RESPONSE_FIELDS)
        review_fields_filled += filled
        if filled == len(REVIEW_RESPONSE_FIELDS):
            decisions_complete += 1
    plan_fields_filled = sum(
        bool(str((adaptation_plan or {}).get(field) or "").strip())
        for field, _ in ADAPTATION_PLAN_FIELDS
    )
    comparison_fields_filled = 0
    for review_id in (expert_models or {}):
        answer = (comparison_responses or {}).get(review_id, {}) or {}
        comparison_fields_filled += sum(
            bool(str(answer.get(field) or "").strip()) for field, _ in EXPERT_COMPARISON_FIELDS
        )
    comparison_fields_total = len(expert_models or {}) * len(EXPERT_COMPARISON_FIELDS)
    total_fields = (
        len(prompts or []) * len(REVIEW_RESPONSE_FIELDS)
        + comparison_fields_total
        + len(ADAPTATION_PLAN_FIELDS)
    )
    filled_fields = review_fields_filled + comparison_fields_filled + plan_fields_filled
    return {
        "decisions_complete": decisions_complete,
        "decisions_total": len(prompts or []),
        "review_fields_filled": review_fields_filled,
        "review_fields_total": len(prompts or []) * len(REVIEW_RESPONSE_FIELDS),
        "comparison_fields_filled": comparison_fields_filled,
        "comparison_fields_total": comparison_fields_total,
        "comparisons_complete": sum(
            all(str(((comparison_responses or {}).get(review_id, {}) or {}).get(field) or "").strip()
                for field, _ in EXPERT_COMPARISON_FIELDS)
            for review_id in (expert_models or {})
        ),
        "comparisons_total": len(expert_models or {}),
        "plan_fields_filled": plan_fields_filled,
        "plan_fields_total": len(ADAPTATION_PLAN_FIELDS),
        "filled_fields": filled_fields,
        "total_fields": total_fields,
        "fraction": (filled_fields / total_fields) if total_fields else 0.0,
    }


def _review_missing_items(
    prompts,
    responses,
    adaptation_plan,
    expert_models=None,
    comparison_responses=None,
):
    missing = []
    for prompt in prompts or []:
        answer = responses.get(prompt.get("review_id"), {}) or {}
        for field, label in REVIEW_RESPONSE_FIELDS:
            if not str(answer.get(field) or "").strip():
                missing.append(f'{_review_heading(prompt)} — {label}')
    for field, label in ADAPTATION_PLAN_FIELDS:
        if not str((adaptation_plan or {}).get(field) or "").strip():
            missing.append(f'Adaptation Plan — {label}')
    for prompt in prompts or []:
        review_id = prompt.get("review_id")
        if review_id not in (expert_models or {}):
            continue
        answer = (comparison_responses or {}).get(review_id, {}) or {}
        for field, label in EXPERT_COMPARISON_FIELDS:
            if not str(answer.get(field) or "").strip():
                missing.append(f'Expert Comparison — {_review_heading(prompt)} — {label}')
    return missing


def _compact_review_summary(prompts, responses):
    records = []
    for prompt in prompts or []:
        answer = responses.get(prompt.get("review_id"), {}) or {}
        filled = sum(bool(str(answer.get(field) or "").strip()) for field, _ in REVIEW_RESPONSE_FIELDS)
        preview = next(
            (_compact_text(answer.get(field), 180) for field, _ in REVIEW_RESPONSE_FIELDS if str(answer.get(field) or "").strip()),
            "No response recorded yet.",
        )
        records.append({
            "review_id": prompt.get("review_id"),
            "heading": _review_heading(prompt),
            "label": prompt.get("label", "Reflection"),
            "complete": filled == len(REVIEW_RESPONSE_FIELDS),
            "filled": filled,
            "total": len(REVIEW_RESPONSE_FIELDS),
            "preview": preview,
        })
    return records


def _sync_compact_review_state(prompts, review_locked=False):
    """Autosave widget values and refresh untouched plan suggestions."""
    if review_locked and st.session_state.get("precomparison_decision_review"):
        responses = deepcopy(st.session_state.get("precomparison_decision_review", {}) or {})
    else:
        responses = deepcopy(st.session_state.get("decision_review", {}) or {})
    plan = deepcopy(st.session_state.get("adaptation_plan", {}) or {})
    user_edited = deepcopy(st.session_state.get("adaptation_plan_user_edited", {}) or {})
    changed = False

    # Capture learner edits to plan fields before refreshing suggestions. This
    # ordering prevents a stale suggested widget value from being mistaken for
    # the learner's text.
    for field, _ in ADAPTATION_PLAN_FIELDS:
        key = _adaptation_widget_key(field)
        if key in st.session_state:
            widget_value = str(st.session_state.get(key) or "")
            if widget_value != str(plan.get(field) or ""):
                plan[field] = widget_value
                user_edited[field] = True
                changed = True

    for prompt in ([] if review_locked else (prompts or [])):
        review_id = prompt.get("review_id")
        current = deepcopy(responses.get(review_id, {}) or {})
        for field, _ in REVIEW_RESPONSE_FIELDS:
            key = _review_widget_key(review_id, field)
            if key in st.session_state:
                widget_value = str(st.session_state.get(key) or "")
                if widget_value != str(current.get(field) or ""):
                    current[field] = widget_value
                    changed = True
        responses[review_id] = current

    suggestions = _suggest_adaptation_plan(prompts, responses)
    merged_plan = _merge_adaptation_suggestions(plan, user_edited, suggestions)
    if merged_plan != plan:
        plan = merged_plan
        changed = True

    # Keep not-yet-edited widgets synchronized with their regenerated draft.
    # This runs before plan widgets are instantiated during the current rerun.
    for field, _ in ADAPTATION_PLAN_FIELDS:
        key = _adaptation_widget_key(field)
        if not user_edited.get(field) and key in st.session_state:
            st.session_state[key] = str(plan.get(field) or "")

    st.session_state.decision_review = responses
    st.session_state.adaptation_plan = plan
    st.session_state.adaptation_plan_user_edited = user_edited
    st.session_state.review_completed = _review_is_complete(prompts or [], responses, plan)
    if changed:
        st.session_state.review_autosave_revision = int(st.session_state.get("review_autosave_revision", 0)) + 1
    return responses, plan, user_edited


def _sync_expert_comparison_state(expert_models, unlocked):
    """Autosave learner-authored comparison insights after expert reveal."""
    responses = deepcopy(st.session_state.get("expert_comparison_responses", {}) or {})
    if not unlocked:
        return {}
    changed = False
    for review_id in expert_models or {}:
        current = deepcopy(responses.get(review_id, {}) or {})
        for field, _ in EXPERT_COMPARISON_FIELDS:
            key = _comparison_widget_key(review_id, field)
            if key in st.session_state:
                widget_value = str(st.session_state.get(key) or "")
                if widget_value != str(current.get(field) or ""):
                    current[field] = widget_value
                    changed = True
        responses[review_id] = current
    st.session_state.expert_comparison_responses = responses
    if changed:
        st.session_state.review_autosave_revision = int(st.session_state.get("review_autosave_revision", 0)) + 1
    return responses


def _render_export_controls(
    trace,
    final_state,
    prompts,
    responses,
    adaptation_plan,
    comparison_responses=None,
    comparison_unlocked=False,
    location="top",
):
    payload = _review_payload(
        st.session_state.get("selected_case"),
        st.session_state.get("encounter_closed_time_min", 0),
        trace,
        final_state,
        prompts,
        responses,
        adaptation_plan,
        comparison_responses or {},
        bool(comparison_unlocked),
        st.session_state.get("attempt_number", 1),
        st.session_state.get("carry_forward_plan", {}),
        st.session_state.get("prior_attempt_summary"),
    )
    case_id = str((final_state or {}).get("case_id") or "encounter").lower()
    with st.expander("Complete original encounter record · PDF, Markdown and JSON", expanded=False):
        info, col_pdf, col_md, col_json = st.columns([1.9, 1, 1, 1])
        with info:
            status = "Complete review" if payload.get("review_complete") else "Draft export available"
            st.markdown("**" + status + "**")
            st.caption("The frozen trace and current autosaved responses are exportable at any stage.")
        with col_pdf:
            st.download_button(
                "Download PDF",
                data=_review_pdf(payload),
                file_name=f"{case_id}_decision_review_v0819.pdf",
                mime="application/pdf",
                use_container_width=True,
                key=f"download_pdf_{location}",
            )
        with col_md:
            st.download_button(
                "Download Markdown",
                data=_review_markdown(payload),
                file_name=f"{case_id}_decision_review_v0819.md",
                mime="text/markdown",
                use_container_width=True,
                key=f"download_markdown_{location}",
            )
        with col_json:
            st.download_button(
                "Download JSON",
                data=_review_json(payload),
                file_name=f"{case_id}_decision_review_v0819.json",
                mime="application/json",
                use_container_width=True,
                key=f"download_json_{location}",
            )
    return payload


def _render_analyzed_management_trace():
    """Analyze only frozen decisions and the locked independent reflection."""
    from management_trace_store import analysis_payload_from_session
    from management_trace_portal import render_management_trace_analysis
    if not st.session_state.get("expert_comparison_unlocked"):
        return
    context = globals().get("ACCOUNT_CONTEXT")
    if context:
        save_session(context)
    payload = analysis_payload_from_session(dict(st.session_state))
    return render_management_trace_analysis(
        payload, api_key=_runtime_secret("OPENAI_API_KEY"),
        model=_runtime_secret("MRS_TRACE_MODEL") or _runtime_secret("OPENAI_MODEL") or "gpt-5-mini",
        context=context, case_label=str(st.session_state.get("selected_case") or "Clinical encounter"),
        review_completed=bool(st.session_state.get("review_completed")),
        adaptation_plan=st.session_state.get("adaptation_plan") or {},
    )


def begin_decision_review(trace, state):
    """Freeze the encounter and initialize a separate retrospective review layer."""
    frozen_trace = deepcopy(trace or [])
    frozen_state = management_state_snapshot(state)
    st.session_state.encounter_ended = True
    st.session_state.encounter_closed_trace = frozen_trace
    st.session_state.encounter_closed_events = deepcopy(st.session_state.get("events") or [])
    st.session_state.encounter_closed_state = frozen_state
    st.session_state.encounter_closed_time_min = int(state.get("sim_time", 0))
    st.session_state.review_prompts = _review_prompt_records(frozen_trace)
    st.session_state.decision_review = {}
    st.session_state.adaptation_plan = {}
    st.session_state.adaptation_plan_user_edited = {}
    st.session_state.review_completed = False
    st.session_state.review_stage = "decision"
    st.session_state.active_review_index = 0
    st.session_state.active_comparison_index = 0
    st.session_state.review_autosave_revision = 0
    st.session_state.expert_comparison_unlocked = False
    st.session_state.precomparison_decision_review = {}
    st.session_state.expert_comparison_responses = {}


def generate_problem_config(challenge_id):
    from curriculum import CHALLENGES
    from encounter_generator import generate_encounter
    from generated_case import GeneratedCaseError
    from generation_progress import encounter_preparation
    from scene_preparation import ScenePreparation
    if challenge_id not in CHALLENGES:
        raise ValueError("Choose an implemented clinical problem.")
    from offline_cases import launch_options
    account = globals().get("ACCOUNT_CONTEXT") or {}
    generation, scene_key = launch_options(
        _runtime_secret("OPENAI_API_KEY"), (account.get("user") or {}).get("role"))
    try:
        with ScenePreparation(scene_key,
                              _runtime_secret("MRS_IMAGE_MODEL") or "gpt-image-1.5",
                              _runtime_secret("MRS_IMAGE_REVIEW_MODEL") or "gpt-5-mini") as scene:
            with encounter_preparation(st) as progress:
                generated = generate_encounter(challenge_id, INITIAL_STATE,
                    model=_runtime_secret("MRS_GENERATOR_MODEL") or _runtime_secret("OPENAI_MODEL") or "gpt-5-mini",
                    progress=progress, on_case_compiled=scene.on_case_compiled, **generation)
            scene.adopt(st.session_state, generated["state"], st.session_state.get("_attempt_id"))
    except GeneratedCaseError as exc:
        # Without an account store this was the only handler, and it dropped the
        # draft, the validator issues and the request ledger of a paid failure.
        from generation_diagnostics import save_failure
        save_failure(exc, challenge_id=challenge_id)
        st.error(str(exc))
        st.stop()
    return {"state_factory": lambda: deepcopy(generated["state"]),
            "presentation": generated["presentation"]}


def begin_repeat_encounter(adaptation_plan, prior_attempt_record=None):
    """Start a clean repeat attempt while preserving only the prospective plan."""
    context = globals().get("ACCOUNT_CONTEXT")
    if context:
        save_session(context)
        choice = (st.session_state.get("encounter_assignment") or {}).get("challenge_id")
        from generated_case import GeneratedCaseError
        try:
            start_encounter(context, INITIAL_STATE, reset_session, choice, adaptation_plan, prior_attempt_record)
        except GeneratedCaseError as exc:
            st.error(str(exc))
            st.stop()
        return {"adaptation_plan": deepcopy(adaptation_plan)}
    selected = (st.session_state.state.get("encounter_spec") or {}).get("challenge_id") or "R1-05"
    cfg = generate_problem_config(selected)
    st.session_state.selected_case = selected
    current_attempt = max(1, int(st.session_state.get("attempt_number", 1)))
    carried_plan = {
        field: str((adaptation_plan or {}).get(field) or "").strip()
        for field, _ in ADAPTATION_PLAN_FIELDS
    }
    st.session_state.prior_attempt_summary = {
        "attempt_number": current_attempt,
        "case_id": (st.session_state.get("encounter_closed_state") or {}).get("case_id"),
        "case_label": selected,
        "closed_time_min": int(st.session_state.get("encounter_closed_time_min") or 0),
        "adaptation_plan": deepcopy(carried_plan),
    }
    st.session_state.prior_attempt_record = _strip_private_review_data(prior_attempt_record)
    st.session_state.attempt_number = current_attempt + 1
    st.session_state.carry_forward_plan = deepcopy(carried_plan)

    for key in list(st.session_state.keys()):
        if str(key).startswith(("decision_review__", "adaptation_plan__", "expert_comparison__")):
            del st.session_state[key]

    # Clinical and reflective records start clean. The prior descriptive trace
    # is not copied into the new encounter and remains available in its export.
    st.session_state.state = cfg["state_factory"]()
    st.session_state.events = []
    st.session_state.history = []
    st.session_state.management_trace = []
    st.session_state.encounter_ended = False
    st.session_state.encounter_closed_trace = None
    st.session_state.encounter_closed_events = None
    st.session_state.encounter_closed_state = None
    st.session_state.encounter_closed_time_min = None
    st.session_state.review_prompts = []
    st.session_state.decision_review = {}
    st.session_state.adaptation_plan = {}
    st.session_state.adaptation_plan_user_edited = {}
    st.session_state.review_completed = False
    st.session_state.review_stage = "decision"
    st.session_state.active_review_index = 0
    st.session_state.active_comparison_index = 0
    st.session_state.review_autosave_revision = 0
    st.session_state.expert_comparison_unlocked = False
    st.session_state.precomparison_decision_review = {}
    st.session_state.expert_comparison_responses = {}
    st.session_state.last_parse = None
    st.session_state.rng_counter = 0
    st.session_state.pending_action = None
    st.session_state.pending_bundle = None
    st.session_state.pending_reasoning = None
    st.session_state.reasoning_gate_counter = 0
    st.session_state.last_executed_action = None
    st.session_state.started = True
    # The presentation is the clinician's one-line identity; the handover is
    # what the patient or the informant says, and when it began. Together they
    # are what a resident is given before they ask anything. Faculty request of
    # 2026-09-23: enough to situate a line of thinking, and no more -- the
    # observables are on the monitor and the appearance is in the photograph.
    import arrival_brief
    add_event("presentation",
              cfg["presentation"] + arrival_brief.handover(st.session_state.state), 0)
    return deepcopy(st.session_state.prior_attempt_summary)


def render_decision_review(trace, final_state):
    """Guided self-review, delayed expert comparison, adaptation, and summary."""
    prompts = st.session_state.get("review_prompts") or _review_prompt_records(trace)
    case_id = str((final_state or {}).get("case_id") or "")
    expert_models = _expert_models_for_prompts(case_id, prompts, trace)
    comparison_unlocked = bool(st.session_state.get("expert_comparison_unlocked"))
    if not prompts:
        st.session_state.review_stage = "adaptation"
        comparison_unlocked = True

    responses, adaptation_plan, user_edited = _sync_compact_review_state(
        prompts, review_locked=comparison_unlocked
    )
    comparison_responses = _sync_expert_comparison_state(expert_models, comparison_unlocked)
    progress = _review_progress(
        prompts, responses, adaptation_plan, expert_models, comparison_responses
    )
    st.session_state.review_completed = _review_is_complete(
        prompts,
        responses,
        adaptation_plan,
        expert_models,
        comparison_responses,
        comparison_unlocked,
    )

    st.markdown("## Decision Review")
    st.caption(
        "First record your own retrospective reasoning. The expert model remains hidden until your "
        "reflection is complete and locked; comparison is reflective and non-scoring."
    )
    progress_parts = [
        f'{progress["filled_fields"]}/{progress["total_fields"]} fields autosaved',
        f'{progress["decisions_complete"]}/{progress["decisions_total"]} decisions',
    ]
    if expert_models:
        progress_parts.append(
            f'{progress["comparisons_complete"]}/{progress["comparisons_total"]} comparisons'
        )
    progress_parts.append(f'{progress["plan_fields_filled"]}/{progress["plan_fields_total"]} plan fields')
    st.progress(progress["fraction"], text=" · ".join(progress_parts))
    st.caption("Autosave is active when you leave a field or move to another step.")
    _render_analyzed_management_trace()
    _render_export_controls(
        trace,
        final_state,
        prompts,
        responses,
        adaptation_plan,
        comparison_responses,
        comparison_unlocked,
        "top",
    )

    stage = st.session_state.get("review_stage", "decision")
    if not comparison_unlocked and stage != "decision":
        stage = "decision"
        st.session_state.review_stage = "decision"
    nav_decision, nav_comparison, nav_plan, nav_summary = st.columns(4)
    with nav_decision:
        if st.button("1 · Decision Review", use_container_width=True, disabled=stage == "decision"):
            st.session_state.review_stage = "decision"
            rerun_app()
    with nav_comparison:
        if st.button(
            "2 · Expert Comparison",
            use_container_width=True,
            disabled=(stage == "comparison" or not comparison_unlocked),
        ):
            st.session_state.review_stage = "comparison"
            rerun_app()
    with nav_plan:
        if st.button(
            "3 · Adaptation Plan",
            use_container_width=True,
            disabled=(stage == "adaptation" or not comparison_unlocked),
        ):
            st.session_state.review_stage = "adaptation"
            rerun_app()
    with nav_summary:
        if st.button(
            "4 · Final Summary",
            use_container_width=True,
            disabled=(stage == "summary" or not comparison_unlocked),
        ):
            st.session_state.review_stage = "summary"
            rerun_app()

    if stage == "decision":
        if not prompts:
            st.info("No reflection prompt was generated. Continue to the Adaptation Plan.")
            return

        active_index = max(0, min(int(st.session_state.get("active_review_index", 0)), len(prompts) - 1))
        st.session_state.active_review_index = active_index
        prompt = prompts[active_index]
        review_id = prompt["review_id"]
        answer = responses.get(review_id, {}) or {}

        if comparison_unlocked:
            st.info("Your original reflection is locked because the expert model has been revealed.")
        with st.container(border=True):
            st.caption(f'Review point {active_index + 1} of {len(prompts)}')
            st.markdown("### " + _review_heading(prompt))
            st.markdown("*" + prompt.get("label", "Reflection") + "*")
            st.write(prompt.get("prompt", ""))
            for field, label in REVIEW_RESPONSE_FIELDS:
                key = _review_widget_key(review_id, field)
                if key not in st.session_state or comparison_unlocked:
                    st.session_state[key] = str(answer.get(field) or "")
                st.text_area(label, key=key, height=88, disabled=comparison_unlocked)

        previous_col, next_col = st.columns(2)
        with previous_col:
            if st.button("Previous decision", use_container_width=True, disabled=active_index == 0):
                st.session_state.active_review_index = active_index - 1
                rerun_app()
        with next_col:
            if active_index < len(prompts) - 1:
                if st.button("Next decision", type="primary", use_container_width=True):
                    st.session_state.active_review_index = active_index + 1
                    rerun_app()
            elif comparison_unlocked:
                if st.button("Continue to Expert Comparison", type="primary", use_container_width=True):
                    st.session_state.review_stage = "comparison"
                    rerun_app()

        if len(prompts) > 1:
            st.markdown("### Other review points")
            for index, other in enumerate(prompts):
                if index == active_index:
                    continue
                other_answer = responses.get(other.get("review_id"), {}) or {}
                filled = sum(bool(str(other_answer.get(field) or "").strip()) for field, _ in REVIEW_RESPONSE_FIELDS)
                status = "Complete" if filled == len(REVIEW_RESPONSE_FIELDS) else f"{filled}/{len(REVIEW_RESPONSE_FIELDS)} fields"
                with st.expander(f'{_review_heading(other)} · {status}', expanded=False):
                    st.markdown("*" + other.get("label", "Reflection") + "*")
                    st.write(other.get("prompt", ""))
                    preview = next(
                        (_compact_text(other_answer.get(field), 220) for field, _ in REVIEW_RESPONSE_FIELDS if str(other_answer.get(field) or "").strip()),
                        "No response recorded yet.",
                    )
                    st.caption("Saved response preview: " + preview)
                    if st.button("Review this decision", key=f"open_review_{other.get('review_id')}"):
                        st.session_state.active_review_index = index
                        rerun_app()

        if not comparison_unlocked:
            st.markdown("### Reveal comparison")
            decision_complete = _decision_review_complete(prompts, responses)
            st.caption(
                "Complete all four fields for every selected decision. Revealing the model locks these "
                "responses so the comparison cannot rewrite your initial reflection."
            )
            if st.button(
                "Lock Decision Review & Reveal Expert Comparison",
                type="primary",
                use_container_width=True,
                disabled=not decision_complete,
            ):
                st.session_state.precomparison_decision_review = deepcopy(responses)
                st.session_state.decision_review = deepcopy(responses)
                st.session_state.expert_comparison_unlocked = True
                st.session_state.review_stage = "comparison"
                st.session_state.active_comparison_index = 0
                rerun_app()

    elif stage == "comparison":
        st.markdown("## Expert Comparison")
        st.caption(
            "Compare your locked reflection with one defensible expert reasoning model. This is a "
            "faculty-validation draft, not an answer key and not a score."
        )
        comparison_prompts = [p for p in prompts if p.get("review_id") in expert_models]
        if not comparison_prompts:
            st.info("No faculty-validation expert model is available for these review points.")
            if st.button("Continue to Adaptation Plan", type="primary"):
                st.session_state.review_stage = "adaptation"
                rerun_app()
            return

        active_index = max(
            0,
            min(int(st.session_state.get("active_comparison_index", 0)), len(comparison_prompts) - 1),
        )
        st.session_state.active_comparison_index = active_index
        prompt = comparison_prompts[active_index]
        review_id = prompt.get("review_id")
        model = expert_models.get(review_id, {}) or {}
        comparison_answer = comparison_responses.get(review_id, {}) or {}

        with st.container(border=True):
            st.caption(f'Comparison point {active_index + 1} of {len(comparison_prompts)}')
            st.markdown("### " + _review_heading(prompt))
            with st.expander("Your locked reflection", expanded=False):
                for field, label in REVIEW_RESPONSE_FIELDS:
                    st.markdown("**" + label + "**")
                    st.write((responses.get(review_id, {}) or {}).get(field) or "—")
            st.markdown("#### Expert reasoning model")
            st.markdown("**Framing**")
            st.write(model.get("framing") or "—")
            st.markdown("**Management priority**")
            st.write(model.get("priority") or "—")
            st.markdown("**Key cues**")
            for cue in model.get("cues", []) or []:
                st.write("• " + str(cue))
            left, right = st.columns(2)
            with left:
                st.markdown("**One defensible action**")
                st.write(model.get("action") or "—")
                st.markdown("**Reassessment targets**")
                st.write(model.get("reassessment") or "—")
            with right:
                st.markdown("**Trade-off to manage**")
                st.write(model.get("tradeoff") or "—")
            st.markdown("#### Your comparison")
            for field, label in EXPERT_COMPARISON_FIELDS:
                key = _comparison_widget_key(review_id, field)
                if key not in st.session_state:
                    st.session_state[key] = str(comparison_answer.get(field) or "")
                st.text_area(label, key=key, height=88)

        previous_col, next_col = st.columns(2)
        with previous_col:
            if st.button("Previous comparison", use_container_width=True, disabled=active_index == 0):
                st.session_state.active_comparison_index = active_index - 1
                rerun_app()
        with next_col:
            next_label = "Continue to Adaptation Plan" if active_index == len(comparison_prompts) - 1 else "Next comparison"
            if st.button(next_label, type="primary", use_container_width=True):
                if active_index == len(comparison_prompts) - 1:
                    st.session_state.review_stage = "adaptation"
                else:
                    st.session_state.active_comparison_index = active_index + 1
                rerun_app()

        if len(comparison_prompts) > 1:
            st.markdown("### Other comparison points")
            for index, other in enumerate(comparison_prompts):
                if index == active_index:
                    continue
                other_answer = comparison_responses.get(other.get("review_id"), {}) or {}
                filled = sum(bool(str(other_answer.get(field) or "").strip()) for field, _ in EXPERT_COMPARISON_FIELDS)
                status = "Complete" if filled == len(EXPERT_COMPARISON_FIELDS) else f"{filled}/{len(EXPERT_COMPARISON_FIELDS)} fields"
                with st.expander(f'{_review_heading(other)} · {status}', expanded=False):
                    st.caption("Expert model available · faculty-validation draft")
                    if st.button("Compare this decision", key=f"open_comparison_{other.get('review_id')}"):
                        st.session_state.active_comparison_index = index
                        rerun_app()

    elif stage == "adaptation":
        suggestions = _suggest_adaptation_plan(prompts, responses)
        suggested_count = sum(
            bool(str(suggestions.get(field) or "").strip()) and not bool(user_edited.get(field))
            for field, _ in ADAPTATION_PLAN_FIELDS
        )
        st.markdown("## Adaptation Plan")
        st.caption(
            f'{suggested_count} fields were drafted from your locked reflection. Use the comparison '
            "insights to define your next management priority; every field remains editable."
        )
        with st.container(border=True):
            field_pairs = [
                (("cue", "Clinical cue to watch"), ("threshold", "Threshold for changing course")),
                (("next_priority", "Next management priority"), ("alternative_action", "Alternative action")),
                (("expected_effect", "Expected effect"), ("reassessment_plan", "Reassessment target and timing")),
            ]
            for left_field, right_field in field_pairs:
                left_col, right_col = st.columns(2)
                for column, (field, label) in ((left_col, left_field), (right_col, right_field)):
                    with column:
                        key = _adaptation_widget_key(field)
                        if key not in st.session_state:
                            st.session_state[key] = str(adaptation_plan.get(field) or "")
                        source = " · drafted from your review" if suggestions.get(field) and not user_edited.get(field) else ""
                        st.text_area(label + source, key=key, height=92)

        back_col, summary_col = st.columns(2)
        with back_col:
            if st.button("Back to Expert Comparison", use_container_width=True):
                st.session_state.review_stage = "comparison"
                rerun_app()
        with summary_col:
            if st.button("Continue to Final Summary", type="primary", use_container_width=True):
                st.session_state.review_stage = "summary"
                rerun_app()

    else:
        st.markdown("## Final Summary")
        status_cols = st.columns(4)
        status_cols[0].metric("Decisions", f'{progress["decisions_complete"]}/{progress["decisions_total"]}')
        status_cols[1].metric("Comparisons", f'{progress["comparisons_complete"]}/{progress["comparisons_total"]}')
        status_cols[2].metric("Plan fields", f'{progress["plan_fields_filled"]}/{progress["plan_fields_total"]}')
        status_cols[3].metric("Status", "Complete" if st.session_state.review_completed else "Draft")

        if st.session_state.review_completed:
            st.success("Decision Review, Expert Comparison, and Adaptation Plan are complete and ready to export.")
        else:
            missing = _review_missing_items(
                prompts, responses, adaptation_plan, expert_models, comparison_responses
            )
            st.warning(f'{len(missing)} field(s) remain incomplete. The current draft can still be exported.')
            with st.expander("Show incomplete fields", expanded=False):
                for item in missing:
                    st.write("• " + item)

        st.markdown("### Decision synthesis")
        for record in _compact_review_summary(prompts, responses):
            icon = "✓" if record["complete"] else "○"
            with st.expander(f'{icon} {record["heading"]} · {record["filled"]}/{record["total"]}', expanded=False):
                st.markdown("*" + record["label"] + "*")
                st.write(record["preview"])

        st.markdown("### Comparison synthesis")
        for prompt in prompts:
            review_id = prompt.get("review_id")
            if review_id not in expert_models:
                continue
            answer = comparison_responses.get(review_id, {}) or {}
            filled = sum(bool(str(answer.get(field) or "").strip()) for field, _ in EXPERT_COMPARISON_FIELDS)
            with st.expander(f'{_review_heading(prompt)} · {filled}/{len(EXPERT_COMPARISON_FIELDS)}', expanded=False):
                for field, label in EXPERT_COMPARISON_FIELDS:
                    st.markdown("**" + label + "**")
                    st.write(answer.get(field) or "—")

        st.markdown("### Prospective Adaptation Plan")
        with st.container(border=True):
            for index in range(0, len(ADAPTATION_PLAN_FIELDS), 2):
                columns = st.columns(2)
                for column, (field, label) in zip(columns, ADAPTATION_PLAN_FIELDS[index:index + 2]):
                    with column:
                        st.markdown("**" + label + "**")
                        st.write(adaptation_plan.get(field) or "—")

        view_decision, edit_comparison, edit_plan = st.columns(3)
        with view_decision:
            if st.button("View Locked Review", use_container_width=True):
                st.session_state.review_stage = "decision"
                rerun_app()
        with edit_comparison:
            if st.button("Edit Comparison", use_container_width=True):
                st.session_state.review_stage = "comparison"
                rerun_app()
        with edit_plan:
            if st.button("Edit Adaptation Plan", use_container_width=True):
                st.session_state.review_stage = "adaptation"
                rerun_app()

        st.markdown("### Download complete record")
        summary_payload = _render_export_controls(
            trace,
            final_state,
            prompts,
            responses,
            adaptation_plan,
            comparison_responses,
            comparison_unlocked,
            "summary",
        )

        st.markdown("### Adapt & Repeat")
        st.caption(
            ("Start a new assigned encounter with your Adaptation Plan. The next clinical trajectory and review begin empty."
             if globals().get("ACCOUNT_CONTEXT") else
             "Start a clean attempt of the same encounter. Only the prospective Adaptation Plan is carried forward; the clinical trajectory, Management Trace, self-review, and comparison restart empty.")
        )
        if st.button(
            ("Next Encounter with This Adaptation Plan" if globals().get("ACCOUNT_CONTEXT") else "Repeat Encounter with This Adaptation Plan"),
            type="primary",
            use_container_width=True,
            disabled=not st.session_state.review_completed,
        ):
            begin_repeat_encounter(adaptation_plan, summary_payload)
            rerun_app()


def management_trace_rows(trace):
    """Compatibility helper retained for regression tests and future exports."""
    rows = []
    for event in trace:
        if event.get("execution_status") not in {"executed", "terminal_locked"}:
            continue
        rows.append({"Time": _trace_time(event.get("decision_time_min", 0)), "Patient state": _trace_state_text(event.get("state_before")), "Management reasoning": _trace_reasoning_text(event.get("reasoning")), "Action": _trace_action_text(event), "Observed response": _trace_state_text(event.get("state_after"))})
    return rows


def render_management_trace(trace):
    """Post-encounter learner timeline: state -> stated reasoning -> action -> response."""
    events = [e for e in trace if e.get("execution_status") in {"executed", "terminal_locked"}]
    if not events:
        st.info("No executed management decisions were recorded in this encounter.")
        return
    st.markdown("""<style>
    .mt-card{border:1px solid #d9dee7;border-radius:14px;padding:18px 20px;margin:0 0 18px;background:#fff;box-shadow:0 1px 2px rgba(0,0,0,.03)}
    .mt-head{display:flex;align-items:baseline;gap:8px;margin-bottom:14px}.mt-time{font-size:.84rem;font-weight:700;color:#596273}.mt-head-sep{color:#8a93a2}.mt-title{font-size:1.12rem;font-weight:700;color:#20242d}
    .mt-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.mt-block{border-radius:10px;background:#f7f8fa;padding:13px 15px;min-height:92px}.mt-label{font-size:.76rem;text-transform:uppercase;letter-spacing:.055em;color:#6b7280;font-weight:700;margin-bottom:7px}.mt-body{font-size:.96rem;line-height:1.48;color:#252a34}.mt-reason{margin:0 0 5px}.mt-muted{color:#7a808b;font-style:italic}.mt-response-group{margin:0 0 10px}.mt-response-title{font-size:.72rem;text-transform:uppercase;letter-spacing:.045em;color:#778091;font-weight:700;margin:0 0 6px}.mt-deltas{list-style:none;margin:0;padding:0}.mt-delta{display:inline-block;margin:0 10px 6px 0;padding:4px 8px;border-radius:7px;background:#eef1f5;font-size:.9rem}.mt-result-list{display:grid;gap:7px}.mt-result{display:block;padding:9px 11px;border:1px solid #d8dee8;border-left:4px solid #65758d;border-radius:7px;background:#fff;font-size:.9rem;line-height:1.42}.mt-result-time{display:block;color:#596579;font-size:.78rem;font-weight:700;margin:0 0 3px}.mt-result-text{display:block;color:#2f3642}.mt-arrow{color:#737b88;padding:0 4px}@media(max-width:850px){.mt-grid{grid-template-columns:1fr}}
    </style>""", unsafe_allow_html=True)
    import html
    for i, event in enumerate(events, 1):
        t0 = _trace_time(event.get("decision_time_min", 0))
        t1 = _trace_time((event.get("state_after") or {}).get("sim_time_min", event.get("response_time_min", 0)))
        state = html.escape(_trace_state_text(event.get("state_before")))
        action = html.escape(_trace_action_text(event))
        reasoning = _trace_reasoning_items(event.get("reasoning"))
        reasoning_html = "".join(f'<div class="mt-reason"><strong>{html.escape(label)}:</strong> {html.escape(value)}</div>' for label, value in reasoning) if reasoning else '<div class="mt-muted">Not explicitly stated</div>'
        deltas = _trace_observable_delta(event.get("state_before"), event.get("state_after"), event.get("reasoning"))
        diagnostics = _trace_diagnostic_results(event)
        clinical_items = "".join(f'<li class="mt-delta"><strong>{html.escape(label)}</strong>: {html.escape(before)} <span class="mt-arrow">→</span> {html.escape(after)}</li>' for label, before, after in deltas)
        delta_html = f'<div class="mt-response-group"><div class="mt-response-title">Clinical response</div><ul class="mt-deltas">{clinical_items}</ul></div>' if clinical_items else ""
        diagnostic_items = "".join(f'<div class="mt-result"><span class="mt-result-time">Diagnostic result · {html.escape(time_text)}:</span><span class="mt-result-text">{html.escape(result_text).replace(chr(10), "<br>")}</span></div>' for time_text, result_text in diagnostics)
        diagnostic_html = f'<div class="mt-response-group"><div class="mt-response-title">New diagnostic information</div><div class="mt-result-list">{diagnostic_items}</div></div>' if diagnostic_items else ""
        if not delta_html and not diagnostic_html:
            delta_html = '<span class="mt-muted">No material observable change recorded.</span>'
        delta_html += diagnostic_html
        card = f'<div class="mt-card"><div class="mt-head"><span class="mt-time">{t0}</span><span class="mt-head-sep">·</span><span class="mt-title">Decision {i}</span></div><div class="mt-grid"><div class="mt-block"><div class="mt-label">Patient state</div><div class="mt-body">{state}</div></div><div class="mt-block"><div class="mt-label">Management reasoning</div><div class="mt-body">{reasoning_html}</div></div><div class="mt-block"><div class="mt-label">Action</div><div class="mt-body">{action}</div></div><div class="mt-block"><div class="mt-label">Observed response · {t1}</div><div class="mt-body">{delta_html}</div></div></div></div>'
        st.markdown(card, unsafe_allow_html=True)


def _quantity_is_respiratory_support(text, start, end):
    """Return True when a liter quantity belongs to an oxygen-support clause."""
    t = text.lower()
    suffix = t[end:end + 55]

    # These continuations make the unit respiratory even when the learner omits
    # "/min", as in "O2 3lt nassal canula" or "oxygen 4 L nasal cannula".
    if re.match(
        r"\s*(?:/?\s*(?:min|minute|minutes)\b|(?:by|via|on|with|at)?\s*"
        r"(?:nas+al\s+can+ula|nc\b|non-?rebreather|nrb\b|simple\s+mask|face\s+mask))",
        suffix,
    ):
        return True

    prefix = t[:start]

    def last_match(pattern):
        matches = list(re.finditer(pattern, prefix, re.I))
        return matches[-1].start() if matches else -1

    last_oxygen = last_match(
        r"\b(?:o2|oxygen|nas+al\s+can+ula|nc|non-?rebreather|nrb|simple\s+mask|face\s+mask)\b"
    )
    last_fluid = last_match(
        r"\b(?:ns|normal\s+saline|saline|lr|lactated\s+ringers?|ringer'?s?|crystalloid|fluids?|iv|bolus)\b"
    )
    last_admin = last_match(r"\b(?:give|administer|infuse|bolus)\b")

    # The closest semantic anchor owns the quantity. A new administration verb
    # after an oxygen clause permits compact orders such as "O2 3 L, give 1 L".
    return last_oxygen > max(last_fluid, last_admin)


def parse_volume_ml(text):
    from shared_order_quantities import parse_volume_ml as shared_parse_volume
    return shared_parse_volume(text)


def parse_delay_min(text):
    """
    Parse common reassessment/observation time expressions.

    Examples:
      reassess 5 min
      reassess in 5 min
      reassess in 5 minutes
      recheck after 10 mins
      observe 15 m
      watch for 1 hour
    """
    t = text.lower().strip()
    # "Give 500 mL over 30 minutes" states how long the infusion runs, not when to
    # reassess. It must not replace the learner's own reassessment interval.
    t = re.sub(
        r"\b(?:over|durante)\s+\d+(?:\.\d+)?\s*(?:s|sec|secs|seconds?|m|min|mins|minutes?|minutos?|h|hr|hrs|hours?|horas?)\b",
        " ", t,
    )

    # A learner may request a checkpoint without advancing simulated time.
    # Keep this scoped to reassessment verbs so unrelated uses of "now" or
    # "immediately" do not become timing instructions.
    immediate_reassessment = re.search(
        r"\b(?:reassess|re-assess|reevaluate|re-evaluate|recheck|re-check|observe|check)\b"
        r"[^.;]{0,300}\b(?:now|immediately)\b",
        t,
    ) or re.search(
        r"\bimmediately\s+(?:reassess|re-assess|reevaluate|re-evaluate|recheck|re-check|observe|check)\b",
        t,
    )
    if immediate_reassessment or re.search(r"\bon\s+immediate\s+reassessment\b", t):
        return 0

    # Event-anchored reassessment is an explicit immediate checkpoint even
    # when the learner does not supply a clock interval.
    if re.search(
        r"\b(?:immediately\s+)?after\s+(?:the\s+)?"
        r"(?:(?:synchronized|synchronised)\s+)?(?:electrical\s+)?cardioversion\b",
        t,
    ):
        return 0

    # Minutes: accept min, mins, minute(s), and standalone m after a number.
    m = re.search(
        r"\b(?:in|after|for)?\s*(\d+(?:\.\d+)?)\s*(?:m|min|mins|minute|minutes)\b",
        t,
    )
    if m:
        return int(round(float(m.group(1))))

    # Hours.
    m = re.search(
        r"\b(?:in|after|for)?\s*(\d+(?:\.\d+)?)\s*(?:h|hr|hrs|hour|hours)\b",
        t,
    )
    if m:
        return int(round(float(m.group(1)) * 60))

    return None


def parse_requested_diagnostic_delay(text, aliases):
    """Return an explicitly requested future diagnostic time, if locally stated.

    ``Obtain lactate, then reassess in 10 minutes`` means obtain it now with its
    usual turnaround. ``Reassess ... and lactate in 10 minutes`` or ``repeat
    lactate in 10 minutes`` schedules that diagnostic for the requested time.
    """
    raw = re.sub(r"\s+", " ", text.lower()).strip()
    alias_list = sorted([a.lower() for a in aliases], key=len, reverse=True)
    segments = [s.strip() for s in re.split(r"\bthen\b|[.;]", raw) if s.strip()]
    reassess_words = r"reassess|re-assess|recheck|re-check|reevaluate|re-evaluate"
    diagnostic_words = r"repeat|redraw|draw|obtain|check|recheck|re-check"

    for segment in segments:
        found = [(segment.find(alias), alias) for alias in alias_list if segment.find(alias) >= 0]
        if not found:
            continue
        pos, matched_alias = min(found, key=lambda item: item[0])
        prefix = segment[:pos]
        tail = segment[pos + len(matched_alias):]
        delay = parse_delay_min(tail)
        if delay is None:
            continue
        time_match = re.search(
            r"\b(?:in|after|for)?\s*\d+(?:\.\d+)?\s*(?:m|min|mins|minute|minutes|h|hr|hrs|hour|hours)\b",
            tail,
        )
        between = tail[:time_match.start()] if time_match else tail
        # In ``obtain lactate and reassess in 10 minutes``, the time belongs to
        # the reassessment rather than the diagnostic turnaround.
        if re.search(rf"\band\s+(?:{reassess_words})\b", between):
            continue
        if re.search(rf"\b(?:{reassess_words})\b", prefix):
            return delay
        if re.search(rf"\b(?:{diagnostic_words})\b[^.;,]{{0,45}}$", prefix):
            return delay
    return None


def explicit_diagnostic_request(text, aliases):
    """Distinguish a diagnostic request from a result mentioned in reasoning."""
    raw = re.sub(r"\s+", " ", text.lower()).strip()
    alias_list = sorted([a.lower() for a in aliases], key=len, reverse=True)
    alias_pattern = "(?:" + "|".join(re.escape(a) for a in alias_list) + ")"
    alias_matches = list(re.finditer(rf"\b{alias_pattern}\b", raw))
    result_verbs = r"shows?|showed|demonstrates?|demonstrated|reveals?|revealed|indicates?|indicated"

    # A learner may cite an already available result while explaining the next
    # decision ("POCUS shows ..."). That is evidence, not a new test order.
    # Keep it inert unless another occurrence of the same diagnostic is locally
    # attached to an explicit request verb.
    result_mentions = {
        match.start()
        for match in alias_matches
        if re.match(rf"\s+(?:{result_verbs})\b", raw[match.end():])
    }
    request_verbs = (
        r"obtain|order|send|check|draw|redraw|repeat|reassess|re-assess|"
        r"recheck|re-check|measure|do|perform"
    )
    # Commas delimit compact orders. A verb such as "send" must not reach over
    # several comma-separated clauses and turn a later result statement into an
    # order. Dedicated bundle handling below preserves valid test lists.
    explicit_matches = list(re.finditer(
        rf"\b(?:{request_verbs})\b[^.;,]{{0,110}}\b{alias_pattern}\b", raw
    ))
    if explicit_matches:
        return True
    # A diagnostic can be the final item in a comma-separated reassessment list:
    # "reassess BP, CRT, and lactate in 10 minutes". The local timing after the
    # alias distinguishes that request from a result statement such as
    # "POCUS shows ...".
    if re.search(
        rf"\b(?:reassess|re-assess|recheck|re-check|reevaluate|re-evaluate)\b"
        rf"[^.;]{{0,180}}\b{alias_pattern}\b\s*(?:in|after)\s+\d+(?:\.\d+)?\s*"
        rf"(?:m|min|mins|minute|minutes|h|hr|hrs|hour|hours)\b",
        raw,
    ):
        return True
    # Permit compact diagnostic bundles such as ``do POCUS, lactate, VBG``.
    if re.search(
        rf"(?:^|[,;])\s*(?:and\s+)?(?:a\s+|an\s+)?{alias_pattern}\b"
        rf"(?=\s*(?:,|;|\.|\bthen\b|$))",
        raw,
    ):
        return True

    # Accept a compact multi-test list attached to an explicit treatment order,
    # even when the learner omits "obtain" before the first test, for example:
    # "give 1000 NS IV POCUS, lactate, VBG initiate O2...". Requiring at least
    # two recognized tests plus a nearby command keeps narrative mentions inert.
    diagnostic_aliases = (
        "point-of-care ultrasound", "point of care ultrasound", "pocus",
        "lactate", "venous blood gas", "venous gas", "vbg",
        "arterial blood gas", "arterial gas", "abg", "basic labs", "labs",
    )
    diagnostic_pattern = "(?:" + "|".join(
        re.escape(alias) for alias in sorted(diagnostic_aliases, key=len, reverse=True)
    ) + ")"
    bundle_matches = list(re.finditer(rf"\b{diagnostic_pattern}\b", raw))
    requested_matches = list(re.finditer(rf"\b{alias_pattern}\b", raw))
    if len(bundle_matches) >= 2 and requested_matches:
        bundle_start = bundle_matches[0].start()
        bundle_end = bundle_matches[-1].end()
        bundle_text = raw[bundle_start:bundle_end]
        command_prefix = raw[max(0, bundle_start - 100):bundle_start]
        if "," in bundle_text and re.search(
            r"\b(?:give|administer|infuse|bolus|start|initiate|obtain|order|do|perform)\b",
            command_prefix,
        ):
            eligible = [
                match for match in requested_matches
                if bundle_start <= match.start() < bundle_end and match.start() not in result_mentions
            ]
            return bool(eligible)
    return False

def detect_fluid_type(text):
    t = text.lower()
    if "lactated ringer" in t or re.search(r"\blr\b", t):
        return "Lactated Ringer's"
    if "normal saline" in t or "saline" in t or re.search(r"\bns\b", t):
        return "Normal saline"
    if "balanced crystalloid" in t:
        return "Balanced crystalloid"
    return "Crystalloid"



def parse_dose_mg(text):
    from shared_order_language import _normalize, _amount
    value, units = _amount(_normalize(text), r"mg|g|mcg|ug")
    return None if value is None else value * (1000 if units == "g" else .001 if units in {"mcg", "ug"} else 1)


def parse_route(text):
    from shared_order_language import _normalize, _route
    return _route(_normalize(text))


def parse_energy_j(text):
    t = text.lower().replace(",", "")
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:j|joule|joules)\b", t)
    return int(round(float(m.group(1)))) if m else None

def detect_cardioversion(text):
    t = text.lower()
    return bool(re.search(r"\b(cardiovert|cardioversion|synchronized\s+shock|synchronised\s+shock)\b", t))


def is_explicit_cardioversion_order(text):
    """Require action language before executing a cardioversion mention.

    Management reasoning may compare, defer, or discuss cardioversion. Those
    references must remain reasoning and must never trigger an energy prompt.
    Compact clinical orders such as ``cardiovert 200 J`` remain executable.
    """
    normalized = re.sub(r"\s+", " ", text.lower()).strip()
    clauses = [clause.strip() for clause in re.split(r"[.;\n]+", normalized) if clause.strip()]

    for clause in clauses:
        if not detect_cardioversion(clause):
            continue

        explicit_command = bool(
            re.search(
                r"\b(?:perform|order|repeat|attempt|deliver|do|start|initiate)\b[^,]{0,50}\b"
                r"(?:synchronized\s+|synchronised\s+)?(?:electrical\s+)?cardioversion\b",
                clause,
            )
            or re.search(
                r"\bproceed\s+with\b[^,]{0,35}\b"
                r"(?:synchronized\s+|synchronised\s+)?cardioversion\b",
                clause,
            )
            or re.search(
                r"\bfollowed\s+by\s+"
                r"(?:synchronized\s+|synchronised\s+)?(?:electrical\s+)?cardioversion\b",
                clause,
            )
            or re.search(
                r"(?:^|,\s*|\band\s+|\bthen\s+|\bso\s+|\bplease\s+|"
                r"\bi\s+(?:want|will|would\s+like|plan|intend)\s+to\s+)"
                r"cardiovert\b",
                clause,
            )
        )
        compact_energy_order = bool(re.search(
            r"(?:^|,\s*|\band\s+|\bthen\s+)"
            r"(?:synchronized\s+|synchronised\s+)?(?:electrical\s+)?cardioversion\s*"
            r"(?:at|with)?\s*\d+(?:\.\d+)?\s*(?:j|joules?)\b",
            clause,
        ))
        if not (explicit_command or compact_energy_order):
            continue

        retrospective = bool(re.search(
            r"\b(?:after|following|since|despite)\s+(?:the\s+)?"
            r"(?:synchronized\s+|synchronised\s+)?cardioversion\b",
            clause,
        ))
        deferred_or_negated = bool(
            re.search(
                r"\b(?:do\s+not|don't|not\s+yet|avoid|defer|hold|withhold|delay)\b"
                r"[^,]{0,65}\b(?:cardiovert|cardioversion)\b",
                clause,
            )
            or re.search(
                r"\bbefore\s+(?:committing|commit|deciding|choosing|proceeding)\b"
                r"[^,]{0,80}\b(?:cardiovert|cardioversion)\b",
                clause,
            )
            or re.search(
                r"\b(?:consider|discuss|evaluate|assess)\b[^,]{0,55}\b"
                r"(?:cardiovert|cardioversion)\b",
                clause,
            )
            or re.search(r"\bprepare\s+(?:for|to)\s+(?:cardiovert|cardioversion)\b", clause)
        )
        if deferred_or_negated:
            continue
        if retrospective and not explicit_command:
            continue
        return True

    return False


def is_explicit_antibiotic_order(text):
    """Require explicit administration intent before executing antibiotics.

    Antibiotics are often mentioned retrospectively in the learner's working
    model (for example, ``antibiotics have been started``). Those statements
    describe the current patient state and must not administer another dose.
    Direct commands and compact medication orders remain executable.
    """
    normalized = re.sub(r"\s+", " ", text.lower()).strip()
    aliases = r"(?:ceftriaxone|azithromycin|broad[- ]?spectrum antibiotics?|antibiotics?)"
    clauses = [clause.strip() for clause in re.split(r"[.;\n]+", normalized) if clause.strip()]

    for clause in clauses:
        if not re.search(rf"\b{aliases}\b", clause):
            continue

        explicit_command = bool(
            re.search(
                rf"\b(?:give|administer|order|infuse|start|initiate|begin)\b[^,;]{{0,65}}\b{aliases}\b",
                clause,
            )
            or re.search(
                rf"\b(?:treat|cover)\b[^,;]{{0,35}}\bwith\b[^,;]{{0,35}}\b{aliases}\b",
                clause,
            )
        )
        compact_named_order = bool(re.search(
            r"(?:^|,\s*|\band\s+|\bthen\s+)"
            r"(?:iv\s+)?(?:ceftriaxone|azithromycin)\b[^,;.]{0,25}"
            r"\d+(?:\.\d+)?\s*(?:g|gr|grams?|mg)\b",
            clause,
        ))
        if not (explicit_command or compact_named_order):
            continue

        retrospective_or_completed = bool(
            re.search(
                rf"\b(?:after|following|since|despite)\b[^,;]{{0,50}}\b{aliases}\b",
                clause,
            )
            or re.search(
                rf"\b{aliases}\b[^,;]{{0,30}}\b(?:has|have|had|was|were)\b"
                r"[^,;]{0,20}\b(?:already\s+)?(?:been\s+)?(?:started|given|administered|initiated)\b",
                clause,
            )
        )
        deferred_or_negated = bool(
            re.search(
                rf"\b(?:do\s+not|don't|avoid|defer|hold|withhold|delay|stop)\b"
                rf"[^,;]{{0,65}}\b{aliases}\b",
                clause,
            )
            or re.search(
                rf"\b(?:consider|discuss|evaluate|prepare\s+for)\b[^,;]{{0,55}}\b{aliases}\b",
                clause,
            )
            or re.search(
                rf"\b(?:continue|maintain)\b[^,;]{{0,35}}\b(?:current\s+)?{aliases}\b",
                clause,
            )
        )
        if retrospective_or_completed or deferred_or_negated:
            continue
        return True

    return False

def detect_beta_blocker(text):
    t = text.lower()
    if "metoprolol" in t:
        return "metoprolol"
    if "propranolol" in t:
        return "propranolol"
    return None



def parse_mcg_rate(text):
    """Return (rate, units) for norepinephrine-like infusion expressions."""
    t = text.lower().replace("μ", "u").replace("µ", "u")
    m = re.search(
        r"(\d+(?:\.\d+)?)\s*(?:mcg|ug|microgram|micrograms)\s*/\s*kg\s*/\s*(?:min|minute)",
        t,
    )
    if m:
        return float(m.group(1)), "mcg/kg/min"

    m = re.search(
        r"(\d+(?:\.\d+)?)\s*(?:mcg|ug|microgram|micrograms)\s*/\s*(?:min|minute)",
        t,
    )
    if m:
        return float(m.group(1)), "mcg/min"

    return None, None




def local_command_operation(text, aliases, active=False):
    """Resolve start/stop/titrate from the clause containing a specific drug.

    Prevents a verb attached to one infusion (e.g. ``stop norepinephrine``) from
    leaking across a compound order and being applied to another infusion
    (e.g. ``continue dobutamine``).
    """
    t = text.lower()
    clauses = [c.strip() for c in re.split(r"\s*(?:,|;|\band\b|\bthen\b)\s*", t) if c.strip()]
    alias_list = sorted([a.lower() for a in aliases], key=len, reverse=True)
    local = next((c for c in clauses if any(a in c for a in alias_list)), t)
    if re.search(r"\b(stop|discontinue|hold|turn\s+off)\b", local):
        return "stop"
    if re.search(r"\b(increase|decrease|titrate|up[- ]?titrate|down[- ]?titrate)\b", local):
        return "titrate"
    if re.search(r"\b(continue|continuing|maintain|maintaining|keep|keeping)\b", local):
        return "continue"
    return "start"


def explicit_infusion_order(text, aliases):
    """Return True only when a named infusion occurs in an actionable clause.

    Clinical reasoning often refers retrospectively to treatment (for example,
    ``after increasing norepinephrine``). Those words describe the preceding
    response and must not be executed again. Terse dose orders remain supported.
    """
    raw = re.sub(r"\s+", " ", text.lower()).strip()
    alias_list = sorted([a.lower() for a in aliases], key=len, reverse=True)
    alias_pattern = "(?:" + "|".join(re.escape(a) for a in alias_list) + ")"
    clauses = [
        c.strip() for c in re.split(r"\s*(?:[.;,]|\bthen\b|\band\s+then\b)\s*", raw)
        if c.strip()
    ]
    command_verbs = (
        r"start|initiate|begin|give|administer|infuse|increase|decrease|"
        r"titrate|up[- ]?titrate|down[- ]?titrate|stop|discontinue|hold|"
        r"continue|maintain|keep"
    )
    retrospective_verbs = (
        r"start(?:ed|ing)?|initiat(?:ed|ing)|increas(?:ed|ing)|decreas(?:ed|ing)|"
        r"titrat(?:ed|ing)|giv(?:en|ing)|administ(?:ered|ering)|continu(?:ed|ing)|"
        r"stopp(?:ed|ing)|discontinu(?:ed|ing)"
    )

    for clause in clauses or [raw]:
        if not re.search(rf"\b{alias_pattern}\b", clause):
            continue
        if re.search(
            rf"\b(?:after|following|since|despite)\s+(?:having\s+)?(?:{retrospective_verbs})\b"
            rf"[^.;,]{{0,55}}\b{alias_pattern}\b",
            clause,
        ):
            continue
        if re.search(
            rf"\b{alias_pattern}\b\s+(?:was|were|has\s+been|had\s+been)\s+"
            rf"(?:{retrospective_verbs})\b",
            clause,
        ):
            continue
        if re.search(rf"\b(?:{command_verbs})\b[^.;,]{{0,65}}\b{alias_pattern}\b", clause):
            return True
        # Accept clinically common terse orders such as
        # ``norepinephrine 0.1 mcg/kg/min`` when no retrospective cue is present.
        if re.search(rf"\b{alias_pattern}\b[^.;,]{{0,65}}\d+(?:\.\d+)?\s*(?:mcg|ug|µg|μg)", clause):
            return True
    return False

def parse_agent_mcg_rate(text, aliases):
    """Parse a mcg infusion rate nearest a named drug, avoiding cross-drug capture."""
    raw = text.lower().replace("μ", "u").replace("µ", "u")
    for alias in sorted(aliases, key=len, reverse=True):
        pos = raw.find(alias)
        if pos < 0:
            continue
        window = raw[pos:pos + 110]
        m = re.search(
            r"(?:at|to|rate(?:\s+of)?|infusion(?:\s+at)?)?\s*(\d+(?:\.\d+)?)\s*"
            r"(?:mcg|ug|microgram|micrograms)\s*/\s*kg\s*/\s*(?:min|minute)",
            window,
        )
        if m:
            return float(m.group(1)), "mcg/kg/min"
        m = re.search(
            r"(?:at|to|rate(?:\s+of)?|infusion(?:\s+at)?)?\s*(\d+(?:\.\d+)?)\s*"
            r"(?:mcg|ug|microgram|micrograms)\s*/\s*(?:min|minute)",
            window,
        )
        if m:
            return float(m.group(1)), "mcg/min"
    return None, None


def parse_fio2_percent(text):
    raw = text.lower().replace("₂", "2")
    m = re.search(r"(?:fio2|ifo2)\s*(?:of|=|at|to)?\s*(\d+(?:\.\d+)?)\s*%?", raw)
    if not m:
        m = re.search(r"(\d+(?:\.\d+)?)\s*%\s*(?:fio2|ifo2)", raw)
    # In a positive-pressure ventilation clause, clinicians commonly write
    # "O2 100%" as shorthand for FiO2. Scope this alias to NIV/intubation so it
    # cannot become a separate low-flow oxygen order.
    ventilation_context = bool(re.search(
        r"\b(?:cpap|bipap|niv|nimv|nippv|vmni|intubat|invasive\s+(?:mechanical\s+)?ventilation)\b",
        raw,
    ))
    if not m and ventilation_context:
        m = re.search(r"\b(?:o2|oxygen)\s*(?:of|=|at|to)?\s*(\d+(?:\.\d+)?)\s*%", raw)
    if not m and ventilation_context:
        m = re.search(r"(\d+(?:\.\d+)?)\s*%\s*(?:o2|oxygen)\b", raw)
    if not m:
        return None
    value = float(m.group(1))
    if value <= 1:
        value *= 100
    return float(value) if 21 <= value <= 100 else None


def parse_ventilator_fio2_percent(text, active_invasive=False):
    """Parse FiO2, allowing O2 shorthand when an invasive ventilator is active."""
    value = parse_fio2_percent(text)
    if value is not None or not active_invasive:
        return value
    raw = text.lower().replace("₂", "2")
    m = re.search(r"\b(?:o2|oxygen)\s*(?:of|=|at|to)?\s*(\d+(?:\.\d+)?)\s*%", raw)
    if not m:
        m = re.search(r"(\d+(?:\.\d+)?)\s*%\s*(?:o2|oxygen)\b", raw)
    if not m:
        return None
    value = float(m.group(1))
    if value <= 1:
        value *= 100
    return value if 21 <= value <= 100 else None


def parse_ventilator_mode(text):
    raw = text.lower().replace("–", "-")
    if re.search(r"\b(?:vc\s*/\s*ac|ac\s*/\s*vc|volume[- ]control(?:led)?(?:\s+assist[- ]control)?)\b", raw):
        return "VC/AC"
    if re.search(r"\b(?:pc\s*/\s*ac|ac\s*/\s*pc|pressure[- ]control(?:led)?(?:\s+assist[- ]control)?)\b", raw):
        return "PC/AC"
    return None


def parse_niv_order(text):
    """Return mode, effective pressure, IPAP, EPAP, and FiO2."""
    raw = text.lower().replace("₂", "2")
    if not any(k in raw for k in [
        "cpap","bipap","niv","nimv","nippv","vmni",
        "noninvasive ventilation","non-invasive ventilation",
        "noninvasive mechanical ventilation","non-invasive mechanical ventilation"
    ]):
        return None, None, None, None, parse_fio2_percent(text)

    mode = "BiPAP" if "bipap" in raw else "CPAP"
    fio2 = parse_fio2_percent(text)

    pair = re.search(r"\b(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)\b", raw)
    if pair:
        ipap, epap = float(pair.group(1)), float(pair.group(2))
        return "BiPAP", epap, ipap, epap, fio2

    ipm = re.search(r"\bipap\s*(?:=|at|to)?\s*(\d+(?:\.\d+)?)", raw)
    epm = re.search(r"\bepap\s*(?:=|at|to)?\s*(\d+(?:\.\d+)?)", raw)
    if ipm or epm:
        ipap = float(ipm.group(1)) if ipm else None
        epap = float(epm.group(1)) if epm else None
        return "BiPAP", epap, ipap, epap, fio2

    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:(?:cm|cc)\s*h2o|cmh2o)", raw)
    pressure = float(m.group(1)) if m else None
    return mode, pressure, None, None, fio2


def parse_nitroglycerin_rate(text):
    t = text.lower().replace("μ", "u").replace("µ", "u")
    m = re.search(
        r"(\d+(?:\.\d+)?)\s*(?:mcg|ug|microgram|micrograms)\s*/\s*(?:min|minute)",
        t,
    )
    return float(m.group(1)) if m else None


def _oxygen_order_clauses(text):
    """Find locally ordered conventional oxygen, preserving intent and scope.

    Device names in history, monitoring, negated plans, and conditional plans
    are not new orders. Keep the command's own clause so a fluid quantity or
    another oxygen device elsewhere in the turn cannot supply its parameters.
    """
    raw = str(text or "").lower().replace("₂", "2").replace("’", "'")
    # Bounded bilingual order vocabulary also protects the raw-text fallback.
    for pattern, replacement in (
        (r"\box[ií]geno\b", "oxygen"),
        (r"\bc[aá]nula\s+nasal\b", "nasal cannula"),
        (r"\b(?:iniciar|inicia|inicie|comenzar)\b", "start"),
        (r"\b(?:administrar|administra|administre|aplicar)\b", "administer"),
        (r"\b(?:colocar|coloca|coloque|poner|pon|ponga)\b", "place"),
        (r"\b(?:mantener|mantenga|mant[eé]n|continuar|contin[uú]a)\b", "continue"),
        (r"\b(?:aumentar|aumenta|aumente|subir|sube|suba)\b", "increase"),
        (r"\b(?:disminuir|disminuye|disminuya|reducir|reduce|reduzca|bajar|baja|baje)\b", "decrease"),
        (r"\bpero\b", "but"),
        (r"\b(?:si|cuando|considerar|considerar[ií]a|podr[ií]a|deber[ií]a|evitar|suspender|previamente)\b", "if"),
    ):
        raw = re.sub(pattern, replacement, raw)
    aliases = r"(?:oxygen|o2|nas+al\s+can+ula|nc|non-?rebreather|nrb|simple\s+mask|face\s+mask)"
    commands = r"(?:start|initiate|give|administer|apply|increase|decrease|switch|change|place|put|continue|provide|order|deliver|set|begin|supplement)"
    observations = r"(?:re-?assess|re-?check|re-?evaluate|assess|check|monitor|measure|observe|evaluar|reevaluar|revaluar|medir|vigilar|monitorizar)"
    boundaries = commands + "|" + observations + r"|obtain|infuse|bolus|perform|intubate"
    clauses = []
    for sentence in re.split(r"\.(?!\d)|[;\n]", raw):
        mentions = list(re.finditer(rf"\b{aliases}\b", sentence))
        for mention in mentions:
            prefix = sentence[:mention.start()]
            tail = sentence[mention.end():]
            # Oxygen saturation is a measured variable, even in a comma-separated
            # reassessment list or a stated goal to increase saturation. Its name
            # must not become a bare oxygen-administration order. Keep actual
            # directives such as "give oxygen to target saturation 94%" intact.
            if mention.group() in {"oxygen", "o2"} and (
                re.match(r"\s+(?:saturations?|sats?|levels?|readings?|saturaci[oó]n)\b", tail)
                or re.search(
                    r"\b(?:saturations?|sats?|levels?|readings?|saturaci[oó]n|niveles?)\s+(?:(?:of|de|del)\s+)?$",
                    prefix,
                )
            ):
                continue
            command_matches = list(re.finditer(rf"\b{commands}\b", prefix))
            command = command_matches[-1] if command_matches else None
            observation_matches = list(re.finditer(rf"\b{observations}\b", prefix))
            if observation_matches and (
                command is None or observation_matches[-1].start() > command.start()
            ):
                # An observation verb still governs later items in its list;
                # only a subsequent treatment command starts a new order.
                continue
            commanded = bool(command and mention.start() - command.end() <= 65)
            if commanded:
                start = command.start()
            else:
                compact = re.search(r"(?:^|,|\band\b)\s*$", prefix)
                if not compact:
                    continue
                start = mention.start()
            next_command = re.search(rf"\b(?:{boundaries})\b", tail)
            end = mention.end() + next_command.start() if next_command else len(sentence)
            # A later independent command owns its negation/condition. Examples:
            # "start oxygen ... and do not give fluids"; "..., and if BP falls ...".
            following_clause = re.search(
                rf"(?:,|\band\b|\bbut\b)\s*(?:and\s+)?"
                rf"(?=(?:do not|don't|if|unless|when|{boundaries})\b)",
                sentence[mention.end():end],
            )
            if following_clause:
                end = mention.end() + following_clause.start()
            clause = sentence[start:end].strip(" ,")
            preceding = sentence[:start]
            local_prefix = re.split(r",|\band\b|\bbut\b", preceding)[-1] if commanded else preceding
            # A leading conditional before the comma still governs its order:
            # "If saturation falls, start oxygen ...". An explicit "but"
            # introduces an independent directive.
            condition_scope = re.split(r"\bbut\b", preceding)[-1]
            leading_condition = bool(re.match(r"\s*(?:if|unless|when|previously|already)\b", condition_scope))
            intent_context = local_prefix + clause
            if leading_condition or "?" in clause or re.search(
                r"\b(?:do not|don't|didn't|won't|not|no|never|avoid|defer|hold|withhold|stop|"
                r"if|unless|when|consider|might|may|could|would|should|whether|previously|already|"
                r"was|were|had|received|receiving)\b", intent_context,
            ):
                continue
            if re.search(r"\b(?:cpap|bipap|niv|nimv|nippv|vmni|noninvasive|non-invasive|ventilat\w*)\b", clause):
                continue
            if clause and clause not in clauses:
                # Oxygen and its device can both match in the same command.
                if not any(clause in prior for prior in clauses):
                    clauses.append(clause)
    return clauses


def parse_oxygen_order(text):
    """Read explicit device/flow only; missing parameters require clarification."""
    t = str(text or "").lower().replace("₂", "2")
    device_patterns = (
        (r"\b(?:non-?rebreather|nrb)\b", "Non-rebreather mask"),
        (r"\b(?:nas+al\s+can+ula|nc)\b", "Nasal cannula"),
        (r"\b(?:simple\s+mask|(?:simple\s+)?face\s+mask)\b", "Simple face mask"),
    )
    devices = {name for pattern, name in device_patterns if re.search(pattern, t)}
    device = next(iter(devices)) if len(devices) == 1 else None
    if len(devices) > 1:
        destination = re.search(r"\bto\s+(.+)$", t)
        targets = {name for pattern, name in device_patterns if destination and re.search(pattern, destination.group(1))}
        device = next(iter(targets)) if len(targets) == 1 else None
    flows = []
    for match in re.finditer(
        r"(?<![\w.\-])(\d+(?:\.\d+)?)\s*(?:liters?|litres?|lts?|l)\b"
        r"(?:\s*/?\s*(?:minutes?|mins?)\b)?", t,
    ):
        if _quantity_is_respiratory_support(t, match.start(), match.end()) or re.fullmatch(
            r"\s*(?:(?:at|to|use)\s+)?\d+(?:\.\d+)?\s*(?:liters?|litres?|lts?|l)\s*/\s*(?:minutes?|mins?)\s*(?:please)?\s*[.]?", t,
        ):
            flows.append(float(match.group(1)))
    if len(flows) == 1:
        flow = flows[0]
    elif len(flows) == 2 and re.search(r"\bfrom\b.+\bto\b", t):
        flow = flows[-1]
    else:
        flow = None
    if flow is not None and flow <= 0:
        flow = None
    return device, flow


def explicit_oxygen_actions(text):
    return [
        {"type": "oxygen", "device": device, "flow_lpm": flow}
        for clause in _oxygen_order_clauses(text)
        for device, flow in [parse_oxygen_order(clause)]
    ]


def detect_diltiazem(text):
    return "diltiazem" in text.lower()


def detect_amiodarone(text):
    return "amiodarone" in text.lower() or "amio" in text.lower()



def try_resolve_pending_action(text):
    pending = st.session_state.get("pending_action")
    if not pending:
        return None

    if pending.get("type") == "family_bundle":
        from pending_family_orders import complete_bundle
        resolution = complete_bundle(pending, text)
        if resolution and resolution.get("superseded"):
            # The resident wrote a new order instead of answering. It runs, and
            # what it costs is stated rather than dropped in silence.
            held = _understood_order_labels(pending.get("parsed") or {})
            st.session_state.pending_action = None
            if held:
                add_event("order_cancelled", "The held order was discarded to run this one: "
                          + " + ".join(held) + ". None of it was administered.")
            return None
        from family_parser import _COMMAND, _normalize, _NEGATION
        if (resolution and resolution.get("parsed")) or (resolution is None and (_COMMAND.match(_normalize(text)) or _NEGATION.match(_normalize(text)))):
            st.session_state.pending_action = None
        return resolution

    if pending.get("type") == "fluid":
        resolved = dict(pending)
        if resolved.get("volume_ml") is None:
            vol = parse_volume_ml(text)
            if vol is None:
                bare = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*", text)
                if bare:
                    vol = int(round(float(bare.group(1))))
            if vol is None:
                return {"clarification": "Please specify the fluid volume (for example, 500 mL or 1 L)."}
            resolved["volume_ml"] = vol

        if not resolved.get("fluid_type"):
            tt = text.lower().strip()
            ft = detect_fluid_type(text)
            if re.search(r"\b(?:ns|normal\s+saline|saline)\b", tt):
                ft = "Normal saline"
            elif re.search(r"\b(?:lr|lactated\s+ringers?|ringer'?s?)\b", tt):
                ft = "Lactated Ringer's"
            elif not ft or ft == "Crystalloid":
                return {"clarification": "Which crystalloid would you like to give (for example, normal saline or LR)?"}
            resolved["fluid_type"] = ft

        st.session_state.pending_action = None
        return {"parsed": {
            "raw_text": text,
            "reasoning": {},
            "actions": [resolved],
            "recognized_future_actions": [],
            "resolved_from_clarification": True,
        }}

    if pending.get("type") == "beta_blocker":
        resolved = dict(pending)
        if resolved.get("dose_mg") is None:
            dose = parse_dose_mg(text)
            if dose is None:
                bare = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*", text)
                if bare:
                    dose = float(bare.group(1))
            if dose is None:
                return {"clarification": f'What dose of {resolved.get("agent", "the beta-blocker")} would you like to give?'}
            resolved["dose_mg"] = dose

        if resolved.get("route") is None:
            route = parse_route(text)
            if route is None:
                return {"clarification": "What route would you like to use (IV or PO)?"}
            resolved["route"] = route

        st.session_state.pending_action = None
        return {"parsed": {
            "raw_text": text,
            "reasoning": {},
            "actions": [resolved],
            "recognized_future_actions": [],
            "resolved_from_clarification": True,
        }}

    if pending.get("type") == "procedural_sedation":
        resolved = deepcopy(pending)
        raw = str(text or "").lower()
        missing = []
        for medication in resolved.get("medications", []) or []:
            if medication.get("dose") is not None:
                continue
            agent = str(medication.get("agent") or "")
            after = re.search(
                rf"\b{re.escape(agent)}\b\s*(\d+(?:\.\d+)?)\s*(mcg|µg|ug|mg|g)\b",
                raw,
            )
            before = re.search(
                rf"\b(\d+(?:\.\d+)?)\s*(mcg|µg|ug|mg|g)\s+(?:of\s+)?{re.escape(agent)}\b",
                raw,
            )
            match = after or before
            if match:
                medication["dose"] = float(match.group(1))
                medication["units"] = match.group(2)
                medication["route"] = medication.get("route") or "IV"
            else:
                missing.append(agent or "sedative")
        if missing:
            return {
                "clarification": "Please specify the dose for " + " and ".join(missing) + "."
            }
        st.session_state.pending_action = None
        return {"parsed": {
            "raw_text": text,
            "reasoning": {},
            "actions": [resolved],
            "recognized_future_actions": [],
            "resolved_from_clarification": True,
        }}

    if pending.get("type") == "cardioversion":
        resolved = dict(pending)
        energy = parse_energy_j(text)
        if energy is None:
            bare = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*", text)
            if bare:
                energy = int(round(float(bare.group(1))))
        if energy is None:
            return {"clarification": "What energy would you like to use (in joules)?"}
        resolved["energy_j"] = energy
        st.session_state.pending_action = None
        return {"parsed": {"raw_text": text, "reasoning": {}, "actions": [resolved], "recognized_future_actions": [], "resolved_from_clarification": True}}


    if pending.get("type") in ["diltiazem", "amiodarone"]:
        resolved = dict(pending)
        if resolved.get("dose_mg") is None:
            dose = parse_dose_mg(text)
            if dose is None:
                bare = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*", text)
                if bare:
                    dose = float(bare.group(1))
            if dose is None:
                return {"clarification": f'What dose of {pending.get("type")} would you like to give?'}
            resolved["dose_mg"] = dose
        if resolved.get("route") is None:
            route = parse_route(text)
            if route is None:
                return {"clarification": "What route would you like to use (IV or PO)?"}
            resolved["route"] = route
        st.session_state.pending_action = None
        return {"parsed": {
            "raw_text": text, "reasoning": {}, "actions": [resolved],
            "recognized_future_actions": [], "resolved_from_clarification": True
        }}

    if pending.get("type") == "dobutamine":
        resolved = dict(pending)
        if resolved.get("operation") != "stop" and resolved.get("rate") is None:
            rate, units = parse_agent_mcg_rate(text, ["dobutamine"])
            if rate is None:
                rate, units = parse_mcg_rate(text)
            if rate is None:
                bare = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*", text)
                if bare:
                    rate = float(bare.group(1))
                    units = "mcg/kg/min"
            if rate is None or units != "mcg/kg/min":
                return {"clarification": "Please specify the dobutamine dose in mcg/kg/min (for example, 5 mcg/kg/min)."}
            resolved["rate"] = rate
            resolved["units"] = units
        st.session_state.pending_action = None
        return {"parsed": {
            "raw_text": text, "reasoning": {}, "actions": [resolved],
            "recognized_future_actions": [], "resolved_from_clarification": True
        }}

    if pending.get("type") == "niv":
        resolved = dict(pending)
        raw = text.lower().replace("₂", "2").strip()

        pair = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)\s*", raw)
        if pair:
            resolved["mode"] = "BiPAP"
            resolved["ipap_cmh2o"] = float(pair.group(1))
            resolved["epap_cmh2o"] = float(pair.group(2))
            resolved["pressure_cmh2o"] = float(pair.group(2))
        else:
            mode, pressure, ipap, epap, fio2 = parse_niv_order(text)
            if mode is None:
                bare = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*", raw)
                if bare:
                    mode = resolved.get("mode") or "CPAP"
                    pressure = float(bare.group(1))
                else:
                    return {"clarification": "Please specify CPAP pressure (for example, CPAP 8 cm H2O) or BiPAP IPAP/EPAP (for example, 16/8)."}
            resolved["mode"] = mode or resolved.get("mode") or "CPAP"
            if pressure is not None:
                resolved["pressure_cmh2o"] = pressure
            if ipap is not None:
                resolved["ipap_cmh2o"] = ipap
            if epap is not None:
                resolved["epap_cmh2o"] = epap
                resolved["pressure_cmh2o"] = epap
            if fio2 is not None:
                resolved["fio2_percent"] = fio2

        if resolved.get("mode") == "BiPAP":
            if resolved.get("ipap_cmh2o") is None or resolved.get("epap_cmh2o") is None:
                return {"clarification": "What BiPAP IPAP/EPAP would you like to use (for example, 16/8 cm H2O)?"}
        elif resolved.get("pressure_cmh2o") is None:
            return {"clarification": "What CPAP pressure would you like to use (for example, 8 cm H2O)?"}

        st.session_state.pending_action = None
        return {"parsed": {
            "raw_text": text, "reasoning": {}, "actions": [resolved],
            "recognized_future_actions": [], "resolved_from_clarification": True
        }}

    if pending.get("type") == "norepinephrine":
        resolved = dict(pending)
        rate, units = parse_mcg_rate(text)
        active = st.session_state.state["treatments"]
        if rate is None:
            bare = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*", text)
            if bare and active.get("norepinephrine"):
                rate = float(bare.group(1))
                units = active.get("norepinephrine_units")
            else:
                return {"clarification": "What norepinephrine infusion rate would you like to use (for example, 0.05 mcg/kg/min or 5 mcg/min)?"}
        if units is None and active.get("norepinephrine"):
            units = active.get("norepinephrine_units")
        resolved["rate"] = rate
        resolved["units"] = units
        st.session_state.pending_action = None
        return {"parsed": {
            "raw_text": text, "reasoning": {}, "actions": [resolved],
            "recognized_future_actions": [], "resolved_from_clarification": True
        }}

    if pending.get("type") == "oxygen":
        if re.search(r"\b(?:cpap|bipap|niv|nimv|nippv|vmni|noninvasive|non-invasive)\b", text, re.I):
            # Defensive recovery for a stale/older parse that created an
            # unnecessary conventional-oxygen slot beside an already specified
            # NIV order. Drop only the oxygen slot and preserve the rest of the
            # learner's original compound bundle.
            bundle = st.session_state.get("pending_bundle") or {}
            preserved = deepcopy(bundle.get("before", [])) + deepcopy(bundle.get("after", []))
            if any(a.get("type") == "niv" for a in preserved):
                st.session_state.pending_action = None
                st.session_state.pending_bundle = None
                return {"parsed": {
                    "raw_text": bundle.get("raw_text") or text,
                    "reasoning": deepcopy(bundle.get("reasoning", {})),
                    "actions": preserved,
                    "recognized_future_actions": deepcopy(bundle.get("recognized_future_actions", [])),
                    "future_details": deepcopy(bundle.get("future_details", [])),
                    "resolved_from_clarification": True,
                }}
        resolved = dict(pending)
        if re.search(
            r"\b(?:not|no|never|avoid|defer|hold|withhold|stop|if|unless|when|consider|might|may|could|would|previously|already|was|were|received)\b",
            str(text or ""), re.I,
        ):
            return {"clarification": "The oxygen order is still held. Please state the device and flow to use now, without a conditional or retrospective instruction."}
        device, flow = parse_oxygen_order(text)
        if device is None and flow is None:
            return {"clarification": "What oxygen device or flow would you like to use (for example, nasal cannula 4 L/min or non-rebreather mask)?"}
        resolved["device"] = device or resolved.get("device")
        resolved["flow_lpm"] = flow if flow is not None else resolved.get("flow_lpm")
        st.session_state.pending_action = resolved
        if resolved.get("device") is None:
            return {"clarification": "Which oxygen device would you like to use?"}
        if resolved.get("flow_lpm") is None:
            return {"clarification": "What oxygen flow would you like to use?"}
        st.session_state.pending_action = None
        return {"parsed": {
            "raw_text": text, "reasoning": {}, "actions": [resolved],
            "recognized_future_actions": [], "resolved_from_clarification": True
        }}

    return None

def parse_contextual_followup(text):
    last = st.session_state.get("last_executed_action")
    if not last:
        return None

    t = text.lower().strip()
    if not any(cue in t for cue in ["more", "another", "again", "repeat", "same"]):
        return None

    if last.get("type") == "fluid":
        vol = parse_volume_ml(text)
        if vol is None:
            m = re.search(r"\b(\d+(?:\.\d+)?)\b", t)
            if m:
                value = float(m.group(1))
                prior_ml = last.get("volume_ml") or 0
                if prior_ml >= 1000 and value <= 10:
                    vol = int(round(value * 1000))
                elif value >= 100:
                    vol = int(round(value))
                elif prior_ml < 1000 and abs(value - 1.0) < 1e-9:
                    vol = int(prior_ml)
        if vol is None and any(cue in t for cue in ["repeat", "same", "again", "another"]):
            vol = last.get("volume_ml")
        if vol is None:
            return None
        return {
            "raw_text": text,
            "reasoning": {},
            "actions": [{
                "type": "fluid",
                "fluid_type": last.get("fluid_type", "Crystalloid"),
                "volume_ml": vol,
                "rate": "rapid" if ("rapid" in t or "bolus" in t) else last.get("rate", "standard"),
            }],
            "recognized_future_actions": [],
            "resolved_from_context": True,
        }

    if last.get("type") == "beta_blocker":
        dose = parse_dose_mg(text)
        if dose is None and any(cue in t for cue in ["repeat", "same", "again", "another"]):
            dose = last.get("dose_mg")
        if dose is None:
            return None
        return {
            "raw_text": text,
            "reasoning": {},
            "actions": [{
                "type": "beta_blocker",
                "agent": last.get("agent"),
                "dose_mg": dose,
                "route": parse_route(text) or last.get("route"),
            }],
            "recognized_future_actions": [],
            "resolved_from_context": True,
        }

    return None

def _clean_reasoning_phrase(value):
    if not value:
        return None
    # Decimal points are protected during sentence-boundary matching so values
    # such as lactate 5.4 mmol/L remain intact in the learner's reasoning.
    value = value.replace("\ue000", ".")
    value = re.sub(r"\s+", " ", value).strip(" ,.;:-")
    # Keep capture faithful to learner wording, but remove common discourse lead-ins.
    value = re.sub(r"^(?:that\s+)", "", value, flags=re.I)
    return value or None


def _resolve_reasoning_coreference(phrase, context, statement_start):
    """Resolve a leading ``it/this/that`` only from a nearby explicit antecedent.

    The learner may say, for example, "I'm addressing heart rate first because
    I think it is the primary problem." In that construction ``heart rate`` is
    an explicit, high-confidence antecedent. If no such antecedent is present,
    return ``None`` so the simulator asks the learner instead of inventing one.
    """
    candidate = _clean_reasoning_phrase(phrase)
    if not candidate:
        return None
    candidate = re.sub(
        r"^(?:i\s+(?:think|believe|suspect)\s+)",
        "",
        candidate,
        flags=re.I,
    )
    if not re.match(r"^(?:it|this|that)\b", candidate, re.I):
        return candidate

    # "I think this is acute pulmonary oedema": ``this`` is a dummy subject and
    # the learner has named the problem in full. Only a generic complement such
    # as "the primary problem" still needs an explicit antecedent.
    frame = re.match(
        r"^(?:it|this|that)\s*(?:'s|\s+is|\s+looks\s+like|\s+seems\s+like|\s+seems\s+to\s+be|"
        r"\s+appears\s+to\s+be|\s+(?:could|may|might|must)\s+be|\s+is\s+(?:likely|probably|possibly))"
        r"\s+(.+)$",
        candidate, re.I,
    )
    if frame:
        complement = _clean_reasoning_phrase(frame.group(1))
        complement = re.sub(r"^(?:likely|probably|possibly)\s+", "", complement or "", flags=re.I)
        generic = re.fullmatch(
            r"(?:the|a|an|my|our)?\s*(?:(?:main|primary|real|underlying|biggest|key|first|immediate)\s+)?"
            r"(?:problem|issue|cause|concern|priority|thing|driver|reason|explanation|diagnosis)",
            complement or "", re.I,
        )
        if complement and not generic:
            return complement

    prefix = str(context or "")[:max(0, int(statement_start or 0))]
    patterns = [
        r"\bi(?:'m| am)\s+(?:addressing|treating|targeting|prioritizing|focusing\s+on)\s+"
        r"(.+?)(?=\s+first\b|[.;,]|$)",
        r"\b(?:my|the)\s+(?:(?:main|first|immediate|management)\s+)?priority\s+is\s+"
        r"(?:to\s+)?(.+?)(?=[.;,]|$)",
    ]
    antecedents = []
    for pattern in patterns:
        antecedents.extend(
            match.group(1) for match in re.finditer(pattern, prefix, re.I)
        )
    antecedent = _clean_reasoning_phrase(antecedents[-1]) if antecedents else None
    if not antecedent or antecedent.lower() in {"it", "this", "that", "him", "her"}:
        return None
    return _clean_reasoning_phrase(
        re.sub(r"^(?:it|this|that)\b", antecedent, candidate, count=1, flags=re.I)
    )

def extract_explicit_reasoning(text):
    """Capture reasoning the learner states in ordinary clinical language.

    Semantic slots remain distinct and turn-isolated, but v0.8.19 recognizes
    equivalent natural phrasing rather than requiring sentence-template words.
    problem_representation describes the clinical problem the learner states;
    rationale preserves an explicitly stated causal explanation; priority,
    expected effect, and reassessment target are captured when their meaning is
    stated directly or can be faithfully paraphrased from the learner's words.
    Treatment choice alone never manufactures reasoning.
    """
    reasoning = {}
    joined = re.sub(r"\s+", " ", text).strip()
    # Tolerate common dictated/typed variants such as ``i.m`` and ``im``.
    joined = re.sub(r"\bi\s*[.'’]?\s*m\b", "I'm", joined, flags=re.I)
    joined = re.sub(r"\brythm\b", "rhythm", joined, flags=re.I)
    # Common typed misspellings seen in local testing: "stil", "reasses".
    joined = re.sub(r"\bstil\b", "still", joined, flags=re.I)
    joined = re.sub(r"\bre-?as+es+(?=\b|ment)", "reassess", joined, flags=re.I)
    joined = re.sub(
        r"\b(?:urianalysis|urinealysis|urinalisis|urinanalysis)\b",
        "urinalysis",
        joined,
        flags=re.I,
    )
    joined = re.sub(r"(?<=\d)\.(?=\d)", "\ue000", joined)
    working_model_explicit = bool(re.search(
        r"\b(?:my working model is|mi modelo de trabajo es)\b", joined, re.I))

    thought = None
    m = re.search(
        r"\b(?:i think|i believe|i suspect|my impression is|my working diagnosis is|my working model is|i am concerned that|i\'m concerned that|this (?:looks|seems) like|"
        # Spanish lead-ins. The capture below still copies only the learner's words.
        r"creo que|pienso que|sospecho que|considero que|mi impresi[oó]n es(?: que)?|mi modelo de trabajo es|"
        r"mi diagn[oó]stico de trabajo es|me preocupa que)\s+"
        r"(.+?)(?=\s*,?\s*(?:so\b|therefore\b|thus\b|because\b|and i\b (?:want|will|would)\b|so i\b|"
        r"por lo que\b|as[ií] que\b|porque\b|entonces\b)|[.;]|$)",
        joined, re.I
    )
    if m:
        thought = _resolve_reasoning_coreference(m.group(1), joined, m.start())
        if thought:
            # Spanish copular frames: "creo que es X", "creo que se trata de X".
            thought = re.sub(r"^(?:es|ser[ií]a|se trata de|corresponde a|parece(?: ser)?)\s+",
                             "", thought, flags=re.I) or thought

    # A sentence that opens with a hedge names the learner's working model even
    # without "I think": "Likely septic shock." / "Parece ICC descompensada."
    if not thought:
        m = re.search(
            r"(?:^|[.;]\s*)(?:likely|probably|probable|possible|possibly|suspected|suspect|"
            r"consistent with|concern(?:ing)? for|picture of|looks like|seems like|"
            r"probablemente|probable|posible|sospecha de|parece(?: ser| un| una)?|impresiona(?: como)?|"
            r"se trata de|cuadro (?:compatible con|sugerente de|de)|compatible con|sugerente de)\s+"
            r"(.+?)(?=\s*,?\s*(?:so\b|therefore\b|because\b|por lo que\b|porque\b)|[.;]|$)",
            joined, re.I,
        )
        if m:
            thought = _clean_reasoning_phrase(m.group(1))

    # A finding that "suggests" a diagnosis names the working model too:
    # "Chest pressure suggests acute coronary syndrome." / "La hipotensión sugiere
    # shock vasodilatador." An order is never the subject of such a sentence.
    if not thought:
        m = re.search(
            r"(?:^|[.;]\s*)(?!(?:give|start|order|begin|administer|stop|increase|decrease|reassess|"
            r"dar|administra|inicia|iniciar|pide|pedir|reeval)\w*\b)([^.;]{3,160}?)\s+"
            r"(?:suggests?|is suggestive of|are suggestive of|points? to|is consistent with|are consistent with|"
            r"is compatible with|are compatible with|favou?rs?|"
            r"sugiere(?:n)?|orienta(?:n)? a|es compatible con|son compatibles con|es sugerente de)\s+"
            r"(?:an?\s+|the\s+|un\s+|una\s+)?(.+?)(?=\s*,?\s*(?:so\b|therefore\b|because\b|por lo que\b|porque\b)|[.;]|$)",
            joined, re.I,
        )
        if m:
            # Keep the learner's whole statement: the finding is part of the model.
            thought = _clean_reasoning_phrase(joined[m.start(1):m.end(2)])

    # When the learner explicitly states cause -> consequence, keep the full
    # causal statement as rationale and create a distinct problem representation
    # using only concepts already present in the learner's own words.
    causal = None
    if thought:
        causal = re.match(
            r"(.+?)\s+(?:is|are|may be|might be|could be)?\s*"
            r"(caus(?:es|ing)|contribut(?:e|es|ing)(?:\s+to)?|driv(?:e|es|ing)|"
            r"limit(?:s|ing)|impair(?:s|ing)|worsen(?:s|ing))\s+(.+)",
            thought, re.I
        )

    if causal and not working_model_explicit:
        cause = _clean_reasoning_phrase(causal.group(1))
        effect = _clean_reasoning_phrase(causal.group(3))
        if cause and effect:
            effect = re.sub(r"^(?:the|a|an)\s+", "", effect, flags=re.I)
            reasoning["problem_representation"] = f"{effect} with {cause}"
        reasoning["rationale"] = thought
    elif thought:
        reasoning["problem_representation"] = thought

    # A concise persistence statement can be a genuine working model even when
    # it is not introduced by "I think": "Still in AF, I want to do rhythm
    # management." Preserve the learner's wording and let the later review
    # discuss its clinical depth rather than blocking on a sentence template.
    if "problem_representation" not in reasoning:
        m = re.search(
            r"(?:^|[.;])\s*((?:(?:the\s+)?patient|he|she)?\s*(?:is\s+)?still\s+"
            r"(?:in\s+)?(?:a-?fib|af|atrial\s+fibrillation|shock|hypotensive|"
            r"hypoxemic|hypoxic|tachycardic|"
            # A persisting named condition, wherever in the turn it is stated:
            # "... reassess BP. still pulmonary edema".
            r"(?:acute\s+|hypertensive\s+|cardiogenic\s+|flash\s+)*pulmonary\s+o?edema|o?edematous|"
            r"congested|congestive|overloaded|volume\s+overloaded|in\s+failure|decompensated|"
            r"hypertensive|septic|bleeding|wheezy|bronchospastic))(?=\s*,|[.;]|$)",
            joined,
            re.I,
        )
        if m:
            reasoning["problem_representation"] = _clean_reasoning_phrase(m.group(1))

    if "problem_representation" not in reasoning:
        m = re.search(
            r"(?:^|[.;])\s*((?:el\s+paciente\s+|la\s+paciente\s+)?(?:sigue|persiste|contin[uú]a)\s+"
            r"(?:en\s+|con\s+|el\s+|la\s+)?(?:congestiv[oa]|edema(?:\s+pulmonar)?|hipotens[oa]|hipertens[oa]|"
            r"hip[oó]xic[oa]|taquic[aá]rdic[oa]|en\s+shock|en\s+choque|s[eé]ptic[oa]|sangrando|"
            r"descompensad[oa]|sobrecargad[oa]|con\s+sobrecarga))(?=\s*,|[.;]|$)",
            joined, re.I,
        )
        if m:
            reasoning["problem_representation"] = _clean_reasoning_phrase(m.group(1))

    # Explicit patient-state statement even without an 'I think' lead-in.
    if "problem_representation" not in reasoning:
        m = re.search(
            r"\b(?:the patient|patient|he|she)\s+(?:is|remains|appears|looks|seems|has|continues\s+to\s+have)\s+"
            r"(.+?)(?=\s*,?\s*(?:so\b|therefore\b|because\b|and i\b (?:want|will|would))|[.;]|$)",
            joined, re.I
        )
        if m:
            candidate = _clean_reasoning_phrase(m.group(1))
            prefix = joined[max(0, m.start()-20):m.start()].lower()
            embedded_hypothesis = bool(re.search(r"whether\s+(?:the\s+)?$", prefix))
            if candidate and not embedded_hypothesis and not re.search(
                r"\b(?:give|start|stop|continue|increase|decrease|cardiovert|reassess|order)\b",
                candidate, re.I
            ):
                reasoning["problem_representation"] = candidate

    # Preserve an explicitly stated inference such as "This indicates that
    # electrical conversion alone did not restore forward flow." This is the
    # learner's own problem representation, not an inference from the action.
    if "problem_representation" not in reasoning:
        m = re.search(
            r"\bthis\s+(?:indicates|suggests|supports|shows)\s+that\s+"
            r"(.+?)(?=\s*,?\s*\bmy (?:management )?priority\b|[.;]|$)",
            joined,
            re.I,
        )
        if m:
            candidate = _clean_reasoning_phrase(m.group(1))
            if candidate:
                reasoning["problem_representation"] = candidate

    # Preserve an explicit response appraisal when the learner opens the turn by
    # describing what changed. This copies the learner's first sentence verbatim;
    # it does not infer a diagnosis or rationale from the treatment selected.
    if "problem_representation" not in reasoning:
        first = re.match(r"^(.+?)(?=[.;]|\bMy (?:management )?priority\b|$)", joined, re.I)
        candidate = _clean_reasoning_phrase(first.group(1)) if first else None
        response_language = bool(candidate and re.search(
            r"\b(?:response suggests|persistent|persists|has improved|have improved|"
            r"deteriorat|hypox|hemodynamic|perfusion pressure|perfusion recovery|"
            r"perfusion abnormality|additional fluid|hypovolem|reduced (?:effective )?"
            r"circulating volume|reduced preload)\b",
            candidate, re.I,
        ))
        action_language = bool(candidate and re.match(
            r"^(?:give|administer|start|stop|continue|increase|decrease|intubate|order|obtain|perform)\b",
            candidate, re.I,
        ))
        if response_language and not action_language:
            reasoning["problem_representation"] = candidate

    # Compact clinical shorthand can state a genuine working model without a
    # copula: "Patient hypotensive, slow perfusion ...; urinalysis positive for
    # infection." Preserve those learner-supplied findings before the first
    # treatment command. This is a bounded semantic capture, not a diagnosis
    # inferred from the selected intervention.
    if "problem_representation" not in reasoning:
        command = re.search(
            r"(?:^|[.;])\s*(?:give|administer|infuse|bolus|start|stop|continue|"
            r"increase|decrease|cardiovert|perform|intubate|apply|place|put|"
            r"order|obtain|reassess|re-assess|recheck|re-check|reevaluate|re-evaluate|observe|watch|"
            r"dar|administrar|iniciar|comenzar|poner|suspender|aumentar|subir|bajar|disminuir|"
            r"intubar|pedir|solicitar|reevaluar|revaluar|controlar)\b",
            joined,
            re.I,
        )
        clinical_prefix = joined[:command.start()] if command else joined
        cue_pattern = re.compile(
            r"\b(?:shock|hypotens\w*|poor\s+perfusion|slow\s+perfusion|"
            r"hypoperfus\w*|tachycard\w*|bradycard\w*|neurologic\w*|"
            r"mental\s+status|obtund\w*|drows\w*|hypox\w*|dyspn\w*|"
            r"respiratory\w*|atrial\s+fibrillation|a-?fib|afib|arrhythm\w*|"
            r"sepsis|septic|infect\w*|urinalysis|lactate|capillary\s+refill|"
            r"(?:cold|cool)\s+extremit\w*|"
            # A named condition is a working model in its own right: "Acute
            # hypertensive pulmonary edema after missing diuretics."
            r"o?edema|heart\s+failure|cardiac\s+failure|failure|overload\w*|congesti\w*|"
            r"decompensat\w*|cardiogenic|embol\w*|pneumon\w*|exacerbat\w*|asthma|"
            r"anaphyla\w*|ketoacidosis|hypoglyc\w*|hyperglyc\w*|overdose|toxicity|"
            r"intoxicat\w*|opioid\w*|bleed\w*|ha?emorrhag\w*|dehydrat\w*|hypovol[ae]m\w*|"
            r"infarct\w*|ischa?em\w*|tamponade|pneumothorax|adrenal\w*|"
            r"insuficiencia|descompensad\w*|sobrecarga|congesti[oó]n|cardiog[eé]nic\w*|"
            r"embolia|tromboembolismo|neumon[ií]a|exacerbaci[oó]n|asma|anafila\w*|"
            r"cetoacidosis|hipoglic\w*|hiperglic\w*|intoxicaci[oó]n|sangrado|hemorragia|"
            r"deshidrataci[oó]n|hipovolemi\w*|infarto|isquemi\w*|taponamiento|neumot[oó]rax|"
            r"choque|s[eé]ptic\w*|hipotens\w*|hipox\w*|hipoperfusi[oó]n|taquicardi\w*|"
            r"bradicardi\w*|arritmi\w*|fibrilaci[oó]n|shock)\b",
            re.I,
        )
        # Acronyms are matched case-sensitively: "mi" is Spanish for "my".
        acronym_pattern = re.compile(
            r"\b(?:ICC|EAP|CHF|ADHF|HF|TEP|PE|EPOC|COPD|DKA|CAD|IAM|SCA|ACS|STEMI|NSTEMI|AF|FA|SVT|TSV)\b")
        # A clause that already states another slot is not a working model:
        # "My priority is reducing congestion" names congestion but is a priority.
        other_slot = re.compile(
            r"^(?:my\s+(?:management\s+|main\s+|first\s+)?(?:priority|goal|aim|plan)|"
            r"i\s+(?:expect|anticipate|want|will|would|plan|intend)|"
            r"(?:i\s+am|i'm)\s+(?:addressing|treating|targeting|prioriti[sz]ing|expecting|aiming)|"
            r"expected\s+effect|to\s+(?:improve|reduce|treat|address|correct)|"
            # Same determiners the priority pattern reads, kept inline because the
            # AST-subset regressions load this function without module constants.
            r"(?:mi|la|el|nuestra|nuestro)\s+(?:prioridad|objetivo|meta|plan)|espero|anticipo|quiero|voy\s+a|"
            r"pretendo|busco|para\s+(?:mejorar|reducir|tratar|corregir))\b",
            re.I,
        )
        clinical_clauses = []
        for clause in re.split(r"[.;]+", clinical_prefix):
            candidate = _clean_reasoning_phrase(clause)
            if candidate and other_slot.match(candidate):
                continue
            candidate = re.sub(r"^(?:the\s+)?patient\s+", "", candidate or "", flags=re.I)
            if candidate and (cue_pattern.search(candidate) or acronym_pattern.search(candidate)):
                clinical_clauses.append(candidate)
        if clinical_clauses:
            reasoning["problem_representation"] = "; ".join(clinical_clauses[:3])

    # A diagnostic request can carry meaningful management reasoning in its
    # purpose clause even when the learner does not use a template phrase. For
    # example, "Obtain POCUS to assess ventricular function before deciding on
    # more fluid" explicitly states the decision question. Preserve that stated
    # purpose as a management priority; do not invent a diagnosis from the test.
    if "management_priority" not in reasoning:
        diagnostic_purpose = re.search(
            r"\b(?:obtain|order|request|perform|repeat|check|send)\b"
            r"[^.;]{0,180}?\bto\s+"
            r"((?:assess|evaluate|investigate|identify|clarify|determine|look\s+for|"
            r"search\s+for|reassess)\b.+?)(?=[.;]|$)",
            joined,
            re.I,
        )
        if diagnostic_purpose:
            purpose = _clean_reasoning_phrase(diagnostic_purpose.group(1))
            if purpose:
                reasoning["management_priority"] = purpose

    # Other explicit rationale language. Never derive rationale from the action.
    if "rationale" not in reasoning:
        m = re.search(
            r"\bbecause\s+(.+?)(?=\s*,?\s*(?:so\b|therefore\b|thus\b|and i\b (?:want|will|would))|[.;]|$)",
            joined, re.I
        )
        if m:
            rationale = _resolve_reasoning_coreference(m.group(1), joined, m.start())
            if rationale:
                reasoning["rationale"] = rationale
        elif thought and not working_model_explicit and re.search(
            r"\b(?:caus(?:e|es|ing)|contribut(?:e|es|ing)|driv(?:e|es|ing)|"
            r"limit(?:s|ing)|impair(?:s|ing)|worsen(?:s|ing))\b", thought, re.I
        ):
            reasoning["rationale"] = thought

    # Explicit management priority only. An order in the same sentence ends it:
    # "My priority is perfusion, give 1000 mL NS". A goal verb with a
    # physiological object does not: "and increase the MAP above 65".
    _en_order_clause = (
        r"\s*(?:,\s*(?:(?:and|then)\s+)?|\s(?:and|then)\s+)"
        r"(?:(?:give|start|begin|initiate|administer|infuse|bolus|"
        r"(?:reassess|recheck)(?=[^.;]*\d)|intubate|place|apply|stop|discontinue|hold|transfuse|"
        r"consult|call|push|hang|put)\b"
        # A study verb ends the priority only when it names a study: "check lactate",
        # not "check for early fluid overload".
        r"|(?:order|obtain|request|send|draw|check|get|repeat|perform)\s+(?=[^.;,]*\b(?:lactate|vbg|abg|"
        r"blood\s+gas|pocus|ultrasound|x-?ray|cxr|ecg|ekg|cultures?|troponin|glucose|labs?|hemoglobin|"
        r"urinalysis|ct|ctpa)\b)"
        r"|(?:increase|decrease|titrate|wean)\b(?!\s+(?:the\s+|her\s+|his\s+)?(?:preload|afterload|"
        r"perfusion|oxygenation|ventilation|blood\s+pressure|bp|map|pressure|heart\s+rate|"
        r"work\s+of\s+breathing|congestion|oxygen\s+delivery|demand)\b))"
    )
    m = re.search(
        # A labelled priority counts the same: "Priority: restore oxygen delivery."
        r"(?:\b(?:my|the) (?:(?:main|first|immediate|management) )?priority is (?:to )?|"
        r"(?:^|(?<=[.;]))\s*(?:(?:main|first|immediate|management) )?priority\s*:\s*(?:to )?)"
        r"(.+?)(?=\s*,?\s*(?:so\b|therefore\b|and i\b)|" + _en_order_clause + r"|[.;]|$)", joined, re.I
    )
    if not m:
        m = re.search(
            r"\bi (?:need|want) to prioritize\s+(.+?)(?=\s*,?\s*(?:so\b|therefore\b|and\b)|[.;]|$)",
            joined, re.I
        )
    if not m:
        m = re.search(
            r"\b(?:my|the) (?:management )?goal is (?:to )?(.+?)(?=\s*,?\s*(?:so\b|therefore\b|and i\b)|"
            + _en_order_clause + r"|[.;]|$)",
            joined, re.I
        )
    # Natural equivalents: "I'm addressing heart rate first", "I will focus on
    # perfusion first", or "First I need to restore pressure".
    if not m:
        m = re.search(
            r"\bi(?:'m| am)\s+(?:addressing|treating|targeting|prioritizing|focusing\s+on)\s+"
            r"(.+?)(?=\s+first\b|\s+before\b|\s+then\b|\s+reassess\b|[.;]|$)",
            joined,
            re.I,
        )
    if not m:
        m = re.search(
            r"\bi\s+(?:will|would|want|need|plan)\s+(?:to\s+)?"
            r"(?:address|treat|target|prioritize|focus\s+on)\s+"
            r"(.+?)(?=\s+first\b|\s+before\b|\s+then\b|\s+reassess\b|[.;]|$)",
            joined,
            re.I,
        )
    # Direct therapeutic-goal language also states a priority even when the
    # learner does not say "priority" or "first": "I want to control heart
    # rate with diltiazem." Stop before the treatment introduced by ``with`` so
    # the priority remains the clinical target rather than the medication.
    if not m:
        m = re.search(
            r"\bi\s+(?:will|would|want|need|plan|intend)\s+(?:to\s+)?"
            r"((?:control|improve|restore|support|reduce|increase|stabilize|"
            r"treat|address|correct|optimize|lower|raise|slow)\b.+?)"
            r"(?=\s+with\b|\s+first\b|\s+before\b|\s+then\b|\s+reassess\b|[.;]|$)",
            joined,
            re.I,
        )
    # Bounded management-domain language: "I want to do rhythm management"
    # states the problem being addressed even though it uses neither a priority
    # label nor a therapeutic verb such as control/restore. Do not generalize
    # "do" to arbitrary procedures, which would turn an action into reasoning.
    if not m:
        m = re.search(
            r"\bi\s+(?:will|would|want|need|plan|intend)\s+(?:to\s+)?"
            r"(?:do|pursue|use)\s+"
            r"((?:rate|rhythm|hemodynamic|perfusion|airway|oxygenation|"
            r"ventilatory|shock|source|infection)\s+"
            r"(?:control|management|support|optimization|treatment|resuscitation))"
            r"(?=\s+first\b|\s+before\b|\s+then\b|\s+with\b|[.;]|$)",
            joined,
            re.I,
        )
    if not m:
        m = re.search(
            r"\bfirst\s*,?\s+i\s+(?:will|would|want|need|plan)\s+(?:to\s+)?"
            r"(.+?)(?=\s+then\b|\s+and\s+(?:i|we)\b|\s+reassess\b|[.;]|$)",
            joined,
            re.I,
        )
    # A tentative first-person plan can still state the learner's management
    # priority without using the word "priority": "I would try to control
    # heart rate." Restrict the capture to management-directed verbs so a
    # generic statement such as "I would try diltiazem" is not relabeled as a
    # problem priority.
    if not m:
        m = re.search(
            r"\bi\s+(?:would|will|want|plan|intend)\s+(?:first\s+)?"
            r"(?:try|attempt)\s+to\s+"
            r"((?:control|improve|restore|support|reduce|increase|stabilize|treat|address)\b.+?)"
            r"(?=\s+first\b|\s+before\b|\s+then\b|\s+reassess\b|[.;]|$)",
            joined,
            re.I,
        )
    if m:
        reasoning["management_priority"] = _clean_reasoning_phrase(m.group(1))

    # "AF is the primary problem" explicitly ranks the management problem even
    # without the literal word "priority". Preserve the learner's concept and
    # add only the minimal verb needed for the priority slot.
    if "management_priority" not in reasoning:
        primary_problem = re.search(
            r"\b(?:i\s+(?:think|believe|suspect)\s+)?(.+?)\s+is\s+"
            r"(?:the\s+)?(?:primary|main|first)\s+problem\b",
            joined,
            re.I,
        )
        if primary_problem:
            concept = _clean_reasoning_phrase(primary_problem.group(1))
            concept = re.sub(r"^(?:that\s+)?", "", concept or "", flags=re.I)
            if (
                concept
                and concept.lower() not in {"it", "this", "that", "him", "her"}
                and len(concept.split()) <= 16
            ):
                reasoning["management_priority"] = f"address {concept}"
                if "problem_representation" not in reasoning:
                    reasoning["problem_representation"] = (
                        f"{concept} is the primary problem"
                    )

    # A causal treatment test also conveys priority: "if we control heart rate,
    # the patient should improve". Do not infer this from an order alone.
    if "management_priority" not in reasoning:
        conditional_priority = re.search(
            r"\bif\s+(?:i|we)\s+(?:can\s+)?"
            r"((?:control|improve|restore|support|reduce|increase|stabilize)\s+.+?)"
            r"\s*,\s*(?:the\s+)?(?:patient|he|she)\s+(?:should|would)\b",
            joined,
            re.I,
        )
        if conditional_priority:
            reasoning["management_priority"] = _clean_reasoning_phrase(
                conditional_priority.group(1)
            )

    # Preserve an explicitly stated constraint separately from the desired
    # improvement. Example: "support forward flow ... while preserving
    # oxygenation" contains both a priority and a preservation goal; oxygenation
    # should not be mislabeled as an expected improvement.
    priority_value = str(reasoning.get("management_priority") or "")
    preserve_match = re.search(
        r"\bwhile\s+(preserv(?:e|ing)|maintain(?:ing)?)\s+(.+)$",
        priority_value,
        re.I,
    )
    if preserve_match:
        preserve_object = _clean_reasoning_phrase(preserve_match.group(2))
        if preserve_object:
            verb = "preserve" if preserve_match.group(1).lower().startswith("preserv") else "maintain"
            reasoning["preservation_goal"] = f"{verb} {preserve_object}"
    elif re.search(r"\bwithout\s+compromising\s+(.+?)(?=[.;]|$)", joined, re.I):
        preserve_object = _clean_reasoning_phrase(
            re.search(r"\bwithout\s+compromising\s+(.+?)(?=[.;]|$)", joined, re.I).group(1)
        )
        if preserve_object:
            reasoning["preservation_goal"] = f"preserve {preserve_object}"

    # Capture the complete subject-predicate expectation before searching for a
    # later infinitive. Without this precedence, "I expect pressure to increase
    # and perfusion to improve" was truncated to "increase and perfusion to
    # improve" because the generic parser started at the second word "to".
    # Keep every explicit expectation in sentence order, preserving negation.
    # A negative oxygenation expectation must not erase a separate positive
    # pressure expectation, or be inverted by the later infinitive fallback.
    expectation_clauses = []
    direct_expectations = re.finditer(
        r"\b(?:i|we)\s+(?:(?P<negation>do\s+not|don['’]t|would\s+not|wouldn['’]t)\s+|would\s+)?"
        r"(?:expect|anticipate)\s+(?P<effect>.+?)"
        r"(?=\s+if\b|\s*,?\s*(?:and\s+)?(?:reassess|recheck|reevaluate)\b|[.;]|$)",
        joined,
        re.I,
    )
    for expectation in direct_expectations:
        if expectation.group("negation"):
            candidate = _clean_reasoning_phrase(expectation.group())
        else:
            candidate = _clean_reasoning_phrase(expectation.group("effect"))
            candidate = re.sub(
                r"^(?:this|it|that)\s+(?:to|will)\s+",
                "",
                candidate or "",
                flags=re.I,
            )
        if candidate:
            expectation_clauses.append(candidate)
    if expectation_clauses:
        reasoning["expected_effect"] = "; ".join(expectation_clauses)

    # Explicit intended/expected effect only. Search all candidate purpose clauses
    # and reject clauses that belong to a stated priority/goal rather than an
    # anticipated treatment effect.
    effect_pattern = re.compile(
        r"(?<!priority is )\b(?:in order to|to|hoping to|expect(?:ing)? to)\s+"
        r"(improve|restore|increase|decrease|reduce|support|correct|stabilize)\s+"
        r"(.+?)(?=\s*,?\s*(?:and then|and reassess|and recheck|then|reassess|recheck)|[.;]|$)", re.I
    )
    for em in ([] if "expected_effect" in reasoning else effect_pattern.finditer(joined)):
        prefix = joined[max(0, em.start()-90):em.start()].lower()
        if re.search(
            r"(?:(?:priority|goal) is|\bi\s+(?:want|need|plan|intend|will|would))\s*$",
            prefix,
        ):
            continue
        reasoning["expected_effect"] = _clean_reasoning_phrase(f"{em.group(1)} {em.group(2)}")
        break
    if "expected_effect" not in reasoning:
        m2 = re.search(
            r"\b(?:i expect|i would expect|i'm expecting|i am expecting) (?:this|it|that)?\s*(?:to|will)\s+"
            r"(improve|restore|increase|decrease|reduce|support|correct|stabilize)\s+"
            r"(.+?)(?=\s*,?\s*(?:and then|and reassess|and recheck|then|reassess|recheck)|[.;]|$)", joined, re.I
        )
        if m2:
            reasoning["expected_effect"] = _clean_reasoning_phrase(f"{m2.group(1)} {m2.group(2)}")

    # Explicit outcome phrasing without "this/it to", e.g.
    # "I expect further improvement in perfusion if low preload is still important."
    if "expected_effect" not in reasoning:
        m3 = re.search(
            r"\bi expect\s+(.+?)(?=\s+if\b|\s*,?\s*(?:and then|and reassess|and recheck|then|reassess|recheck)\b|[.;]|$)",
            joined, re.I
        )
        if m3:
            candidate = _clean_reasoning_phrase(m3.group(1))
            if candidate and re.search(
                r"\b(?:improv|restor|increas|decreas|reduc|support|correct|stabili|"
                r"remain|maintain|preserv|sustain|convert|conversion)",
                candidate,
                re.I,
            ):
                reasoning["expected_effect"] = candidate

    # Accept ordinary prospective language, including a qualitative expectation
    # such as "the patient should feel better". Specificity can be discussed in
    # review; it should not cause a syntactic dead end during the encounter.
    if "expected_effect" not in reasoning:
        natural_effect = re.search(
            r"\b(?:the\s+)?(?:patient|he|she|this|it)\s+(?:should|would)\s+"
            r"(.+?)(?=\s*,?\s*(?:and\s+)?(?:reassess|recheck|reevaluate)\b|[.;]|$)",
            joined,
            re.I,
        )
        if natural_effect:
            reasoning["expected_effect"] = _clean_reasoning_phrase(
                natural_effect.group(1)
            )

    if "expected_effect" not in reasoning:
        natural_expectation = re.search(
            r"\b(?:(?:i|we)\s+(?:expect|anticipate)|expecting|anticipating|esperando)\s+(.+?)"
            r"(?=\s*,?\s*(?:and\s+)?(?:reassess|recheck|reevaluate)\b|[.;]|$)",
            joined,
            re.I,
        )
        if natural_expectation:
            reasoning["expected_effect"] = _clean_reasoning_phrase(
                natural_expectation.group(1)
            )

    # A purpose clause is an expectation written the short way. "500 mL to raise
    # the MAP" and "salbutamol para mejorar el broncoespasmo" say what the
    # learner expects the intervention to do; held orders in the 2026-09-23
    # measurement were lost to exactly this phrasing. The clause must name a
    # physiologic direction, so "fentanyl for analgesia" stays an indication,
    # and it must not already belong to another slot, so a priority written as
    # "my priority is to reduce afterload" is not counted twice.
    if "expected_effect" not in reasoning:
        direction = (r"(?:rais|increas|improv|restor|reestablish|lower|drop|reduc|decreas|"
                     r"limit|control|correct|stabili[sz]|reliev|revers|unload|support|"
                     r"maintain|prevent|avoid|clear|open|oxygenat|perfus|convert|"
                     # Spanish is matched by stem: a resident writes "suba",
                     # "baje" and "orine", not the infinitive the parser knows.
                     r"sub[ai]|baj|mejor|aument|disminu|limit|corrig|correg|estabiliz|"
                     r"alivi|reviert|revert|descarg|manten|preven|evit|abr|oxigen|"
                     r"perfund|compens|fren|orin|diure|ced|normaliz|recuper)")
        purpose = re.search(
            r"\b(?:to|para|a\s+fin\s+de|con\s+el\s+fin\s+de|buscando|"
            r"in\s+order\s+to)\s+(" + direction + r"\w*\s+.+?)"
            r"(?=\s*,?\s*(?:and\s+|y\s+)?(?:reassess|recheck|reevaluate|reevaluar|"
            r"revaluar|controlo|controlar|then|luego)\b|[.;]|$)",
            joined, re.I,
        )
        candidate = _clean_reasoning_phrase(purpose.group(1)) if purpose else None
        if candidate:
            claimed = " ".join(
                str(reasoning.get(key) or "")
                for key in ("management_priority", "problem_representation", "rationale")
            ).lower()
            if candidate.lower() not in claimed:
                reasoning["expected_effect"] = candidate

    # A stated aim is an expectation written forwards: "busco subir la presion",
    # "quiero frenar la agregacion", "the aim is to unload the work of
    # breathing". The candidate has to name a physiologic direction, so "quiero
    # dar aspirina" stays an order and does not become an expectation.
    if "expected_effect" not in reasoning:
        aim = re.search(
            r"\b(?:busco|buscando|quiero|pretendo|intento|apunto\s+a|apuntando\s+a|"
            r"la\s+idea\s+es(?:\s+que)?|el\s+plan\s+es|me\s+interesa|"
            r"the\s+(?:goal|aim|idea|plan)\s+is(?:\s+to)?|my\s+(?:goal|aim)\s+is(?:\s+to)?|"
            r"i\s+am\s+aiming\s+(?:for|to)|aiming\s+(?:for|to)|looking\s+to)\s+"
            r"(.+?)(?=\s*,?\s*(?:and\s+|y\s+)?(?:reassess|recheck|reevaluate|reevaluar|"
            r"reevalu[oa]|controlo|control\s+de|reviso|then|luego|i\s+will\s+\w+)\b|[.;]|$)",
            joined, re.I,
        )
        candidate = _clean_reasoning_phrase(aim.group(1)) if aim else None
        target_value = re.search(
            r"\b(?:sobre|bajo|mayor|menor|arriba|encima|debajo|above|below|over|under|"
            r"at\s+least|to)\s*(?:de\s+|que\s+)?[<>]?\s*\d|[<>]\s*\d",
            candidate or "", re.I)
        if candidate and (re.search(direction, candidate, re.I) or target_value):
            reasoning["expected_effect"] = candidate

    # Explicit reassessment target only; timing remains in the action schema.
    reassessment_matches = list(re.finditer(
        r"\b(?:reassess|re-assess|recheck|re-check|reevaluate|re-evaluate)\s+"
        r"(?:the )?(.+?)(?=\s+(?:in|after)\s+\d+(?:\.\d+)?\s*"
        r"(?:m|min|mins|minute|minutes|h|hr|hrs|hour|hours)\b|"
        r",\s*(?:and\s+)?(?:then\s+)?(?:give|administer|start|stop|continue|increase|decrease|"
        r"intubate|order|obtain|perform|reassess|re-assess|recheck|re-check|"
        r"reevaluate|re-evaluate)\b|[.;]|$)",
        joined, re.I
    ))
    # The final explicit reassessment usually carries the executable target and
    # timing. Earlier uses can be part of a priority statement ("my priority is
    # to reassess...") or a diagnostic description.
    m = reassessment_matches[-1] if reassessment_matches else None
    if m:
        target = _clean_reasoning_phrase(m.group(1))
        if target and not re.match(r"^(?:in|after)\s+\d+", target, re.I) and target.lower() not in {"him", "her", "patient", "again", "general"}:
            reasoning["reassessment_target"] = target

    # A pure observation/reassessment command states what and when to recheck;
    # it does not, by itself, state a new problem representation. This prevents
    # the entire sentence from being displayed as "Problem" in the trace.
    pure_reassessment = bool(re.match(
        r"^\s*(?:reassess|re-assess|recheck|re-check|reevaluate|re-evaluate|observe|watch)\b",
        joined,
        re.I,
    ))
    if pure_reassessment:
        for key in ("problem_representation", "rationale", "management_priority", "expected_effect"):
            value = str(reasoning.get(key) or "")
            if re.match(
                r"^\s*(?:reassess|re-assess|recheck|re-check|reevaluate|re-evaluate|observe|watch)\b",
                value,
                re.I,
            ):
                reasoning.pop(key, None)

    # Accept the equally natural timing-first order used in the screenshot:
    # "Reassess in 10 minutes, rhythm, HR, BP and perfusion."
    if "reassessment_target" not in reasoning:
        timing_first = re.search(
            r"\b(?:reassess|re-assess|recheck|re-check|reevaluate|re-evaluate)\s+"
            r"(?:in|after)\s+\d+(?:\.\d+)?\s*"
            r"(?:m|min|mins|minute|minutes|h|hr|hrs|hour|hours)\b\s*,?\s*"
            r"(?:the\s+)?(.+?)(?=[.;]|$)",
            joined,
            re.I,
        )
        if timing_first:
            target = _clean_reasoning_phrase(timing_first.group(1))
            if target and target.lower() not in {"him", "her", "patient", "again", "general"}:
                reasoning["reassessment_target"] = target

    # A resident who says what they will watch has named the reassessment, even
    # without the word "reassess": "I will look at the sat and the RR in 10
    # minutes". Tried last, so it never displaces an explicit reassessment.
    if "reassessment_target" not in reasoning:
        watched = re.search(
            r"\b(?:i|we)\s+(?:will\s+|am\s+going\s+to\s+)?"
            r"(?:look\s+at|keep\s+an\s+eye\s+on|watch|follow|track)\s+"
            r"(?:the\s+)?(.+?)(?=\s+(?:in|after)\s+\d|[.;]|$)",
            joined, re.I,
        )
        if watched:
            target = _clean_reasoning_phrase(watched.group(1))
            if target and target.lower() not in {"him", "her", "patient", "again"}:
                reasoning["reassessment_target"] = target

    # If the learner explicitly states the clinical problem and anticipated
    # physiologic direction, that combination can faithfully express the
    # management priority even without the words "priority" or "first". Keep
    # the mapping narrow and grounded in the learner's own expected effect.
    def _capture_spanish_reasoning(joined, reasoning):
        """Fill priority, expected effect and reassessment target from Spanish.

        The interpreter's English patterns are pinned by many regressions, so Spanish
        is captured separately and only for a slot that is still empty, using
        Spanish markers alone. English behaviour therefore cannot change. As with
        English, only the learner's own words are kept.

        Nested here rather than a module function: several regressions load a named
        subset of app.py's functions through ast, so this must travel with its caller.
        """
        # Imported here, not at module scope: the AST-subset regressions load this
        # function on its own and it must carry its own dependencies.
        from family_parser import _ES_ENCLITIC_FORMS
        _ES_ORDER_VERBS = (r"dar|administrar|administra|iniciar|inicia|comenzar|comienza|poner|pon|coloca|"
                           r"suspender|suspende|intubar|intuba|"
                           r"pedir|pide|solicitar|solicita|reevaluar|reeval[uú]a|revaluar|re-evaluar|controlar|controla|"
                           r"volver\s+a\s+evaluar|"
                           # "Mi prioridad es la perfusion, dale 1000 mL": a verb
                           # carrying its pronoun is an order, so the priority ends
                           # there. Derived from the parser's own forms, with the
                           # written accent the enclitic adds ("subele" -> "súbele"),
                           # because this capture reads the learner's own words and
                           # never the normalized ones.
                           + "|".join("".join({"a": "[aá]", "e": "[eé]", "i": "[ií]",
                                               "o": "[oó]", "u": "[uú]"}.get(letter, letter)
                                              for letter in form)
                                      for form in sorted(_ES_ENCLITIC_FORMS, key=len, reverse=True)))
        # These also state goals ("bajar precarga"), so only a non-physiological object ends the priority.
        _ES_GOAL_VERBS = r"aumentar|aumenta|subir|bajar|disminuir|disminuye"
        # "bajar precarga y poscarga" is part of a goal, not an order that ends it.
        _ES_PHYSIOLOGY = (r"(?:(?:el|la|los|las)\s+)?(?:precarga|pos(?:t)?carga|presi[oó]n|pas?|pam|fc|fr|"
                          r"frecuencia|trabajo|congesti[oó]n|oxigenaci[oó]n|perfusi[oó]n|lactato|hipoxemia|"
                          r"spo2|saturaci[oó]n|resistencia|demanda|consumo)\b")
        _ES_TIME = r"(?:en|a\s+los|tras|despu[eé]s\s+de)\s+\d+(?:[.,]\d+)?\s*(?:min|mins|minutos?|h|horas?)\b"
        _ES_REASSESS = (r"reevaluar|revaluar|re-evaluar|reeval[uú][oae]|controlar|controla|"
                        r"controlo|chequear|chequeo|vigilar|vigilo|revisar|reviso|"
                        r"medir|mido|monitorizar|monitorizo|monitorear|monitoreo|"
                        r"volver\s+a\s+evaluar")
        # The separator is mandatory: without it "sin inundar el pulmon" ended the
        # priority at "inun", because "dar" matched inside the word.
        gap = r"(?:\s*,\s*|\s+)"
        stop = (r"(?=" + gap + r"(?:y\s+)?(?:" + _ES_ORDER_VERBS + r")\b"
                r"|" + gap + r"(?:y\s+)?(?:" + _ES_GOAL_VERBS + r")\b(?!\s+" + _ES_PHYSIOLOGY + r")"
                # A connector introduces the order that follows, not more priority.
                r"|" + gap + r"(?:as[ií]\s+que|por\s+lo\s+que|entonces)\b"
                r"|" + gap + r"(?:y\s+)?(?:espero|anticipo)\b"
                # The reassessment clause belongs to its own slot: without this
                # "espero que suba la presion, reevaluo PAM en 10 minutos" kept
                # the whole tail as the expectation.
                r"|" + gap + r"(?:y\s+)?(?:" + _ES_REASSESS + r")\b|[.;]|$)")

        # A Spanish causal statement is the resident's working model: "Esto es una
        # crisis asmática grave porque se quedó sin su inhalador", "La obstrucción
        # persiste porque la inflamación no cede". Without this, every Spanish
        # management order was held asking for a working model it could not read.
        if not (reasoning.get("problem_representation") or reasoning.get("rationale")):
            _ES_CAUSAL = (r"\b(?:porque|debido\s+a(?:l)?|por\s+lo\s+que|as[ií]\s+que|sugiere[n]?|indica[n]?|"
                          r"significa[n]?\s+que|refleja[n]?|corresponde[n]?\s+a|es\s+compatible\s+con|"
                          r"se\s+explica\s+por|traduce)\b")
            for sentence in re.split(r"(?<=[.;])\s+", joined):
                clause = sentence.strip(" .;")
                if not clause or not re.search(_ES_CAUSAL, clause, re.I):
                    continue
                # A priority or an expectation belongs to its own slot, but it is
                # often written in the same sentence as the model: "Con la presion
                # controlada, debido a la respuesta, la prioridad ahora es...".
                # Cut there and keep what comes before instead of losing both.
                # The marker is the statement, not the bare noun: "el pH está bajo
                # el objetivo" is a finding, and cutting there lost the model.
                clause = re.split(r"\b(?:(?:mi|la|el|nuestra|nuestro)\s+)?(?:prioridad|objetivo|meta)"
                                  r"(?:\s+(?:principal|inicial|inmediata|ahora))?\s+(?:es|ser[aá])\b"
                                  r"|(?:^|\b)prioridad(?:\s+(?:principal|inicial|inmediata))?\s*:"
                                  r"|\b(?:espero|anticipo|preveo|reeval)",
                                  clause, maxsplit=1, flags=re.I)[0].strip(" ,;.")
                # An order still belongs to its own slot, and so does a clause that
                # kept nothing causal once the priority was removed.
                if not clause or not re.search(_ES_CAUSAL, clause, re.I):
                    continue
                if re.search(r"\b(?:" + _ES_ORDER_VERBS + r")\b", clause, re.I):
                    continue
                phrase = _clean_reasoning_phrase(clause)
                if phrase:
                    reasoning["problem_representation"] = phrase
                    break

        if "management_priority" not in reasoning:
            m = re.search(
                r"\b(?:(?:mi|la|el|nuestra|nuestro)\s+(?:prioridad|objetivo|meta)(?:\s+(?:principal|inicial|inmediata|ahora))?"
                r"\s+(?:es|ser[aá])|lo\s+primero\s+es|me\s+enfoco(?:\s+primero)?\s+en|priorizo|"
                r"(?:(?:^|(?<=[.;] )|(?<=[.;]))prioridad(?:\s+(?:principal|inicial|inmediata))?\s*:))"
                r"\s*(?:(?:el|la|los|las|lo)\s+)?(.+?)" + stop,
                joined, re.I,
            )
            if m and _clean_reasoning_phrase(m.group(1)):
                reasoning["management_priority"] = _clean_reasoning_phrase(m.group(1))

        if "expected_effect" not in reasoning:
            # "Espero" is also "I wait": "Espero 10 minutos" is not an expectation.
            m = re.search(
                # "Espero" is also "I wait": "espero el resultado" is waiting for
                # a laboratory, not an expectation about the patient (2026-09-24).
                r"\b(?P<neg>no\s+)?(?:espero|anticipo|preveo)"
                r"(?!\s+(?:\d|a\s|hasta\b|unos?\b|un\s+momento"
                r"|(?:el|los|la|las)\s+(?:resultados?|examen|ex[aá]menes|laboratorio)))"
                r"(?:\s+que)?\s+(?P<effect>.+?)" + stop,
                joined, re.I,
            )
            if not m:
                m = re.search(r"\bel\s+efecto\s+esperado\s+es\s+(?:que\s+)?(?P<effect>.+?)" + stop,
                              joined, re.I)
            if m:
                effect = _clean_reasoning_phrase(m.group("effect"))
                if effect:
                    negated = "neg" in m.groupdict() and m.group("neg")
                    reasoning["expected_effect"] = ("no espero que " + effect) if negated else effect

        def _stated_priority(match):
            # "Mi prioridad es controlar la alergia" says what the resident is
            # trying to bring under control, not what they will check: read as
            # a reassessment target, it answered the question for them
            # (rehearsal of the twenty-scenario batch, 2026-09-24).
            return bool(re.search(r"\b(?:prioridad|objetivo|meta)\s+(?:ahora\s+)?es\s+(?:\w+\s+){0,2}$",
                                  joined[:match.start()], re.I))

        if "reassessment_target" not in reasoning:
            # "reevaluar SpO2 y FR en 15 minutos" and "reevaluar en 15 minutos SpO2 y FR".
            m = next((found for found in re.finditer(
                r"\b(?:" + _ES_REASSESS + r")\s+"
                r"(?!" + _ES_TIME + r")(?:(?:el|la|los|las)\s+)?(.+?)(?=\s+" + _ES_TIME + r"|[.;]|$)",
                joined, re.I) if not _stated_priority(found)), None)
            target = _clean_reasoning_phrase(m.group(1)) if m else None
            if not target:
                m = re.search(
                    r"\b(?:" + _ES_REASSESS + r")\s+" + _ES_TIME +
                    r"\s*,?\s*(?:(?:el|la|los|las)\s+)?(.+?)(?=[.;]|$)",
                    joined, re.I,
                )
                target = _clean_reasoning_phrase(m.group(1)) if m else None
            if not target:
                m = re.search(
                    r"\bcontrol(?:es)?\s+de\s+(?:(?:el|la|los|las)\s+)?(.+?)\s+" + _ES_TIME,
                    joined, re.I,
                )
                target = _clean_reasoning_phrase(m.group(1)) if m else None
            if not target:
                # What the resident says they will watch is the reassessment,
                # without the word "reevaluo": "voy a mirar la saturacion",
                # "miro FC y PA", "veo si despierta". Asked "what will you
                # check?", residents answered like this and were asked again
                # (rehearsal of the twenty-scenario batch, 2026-09-24). "Veo que
                # ..." reports what is seen and is left out.
                m = re.search(
                    r"\b(?:(?:voy|vamos)\s+a\s+)?(?:mirar|miro|ver(?!\s+que)|veo(?!\s+que)|revisar|reviso|"
                    r"controlar|controlo|contar|cuento|medir|mido|vigilar|vigilo|chequear|chequeo)\s+"
                    r"(?:si\s+|que\s+)?(?:(?:el|la|los|las)\s+)?(.+?)(?=\s+" + _ES_TIME + r"|[.;]|$)",
                    joined, re.I,
                )
                # "Mi prioridad es mirar la via aerea" states the priority.
                if m and _stated_priority(m):
                    m = None
                target = _clean_reasoning_phrase(m.group(1)) if m else None
            if target and target.lower() not in {"al paciente", "paciente", "de nuevo", "nuevamente", "otra vez"}:
                reasoning["reassessment_target"] = target

    _capture_spanish_reasoning(joined, reasoning)

    if "management_priority" not in reasoning and reasoning.get("expected_effect"):
        grounded = " ".join(
            str(reasoning.get(key) or "")
            for key in ("problem_representation", "rationale", "expected_effect")
        ).lower()
        # This slot is composed by the app, not written by the resident. Record
        # that so the trace, the PDF and the faculty analysis never present the
        # app's wording as a priority the resident stated.
        before_synthesis = dict(reasoning)
        if re.search(r"\b(?:perfusion|capillary\s+refill|crt)\b", grounded):
            if re.search(r"\b(?:pressure|blood\s+pressure|bp|map|hypotens\w*)\b", grounded):
                reasoning["management_priority"] = "improve arterial pressure and tissue perfusion"
            else:
                reasoning["management_priority"] = "improve tissue perfusion"
        elif re.search(r"\b(?:oxygenation|spo2|hypox\w*)\b", grounded):
            reasoning["management_priority"] = "improve oxygenation"
        elif re.search(r"\b(?:ventilation|respiratory\s+status|work\s+of\s+breathing)\b", grounded):
            reasoning["management_priority"] = "improve ventilation and respiratory status"
        elif re.search(r"\b(?:sinus\s+rhythm|convert|conversion|rhythm)\b", grounded):
            reasoning["management_priority"] = "restore an effective rhythm"
        elif re.search(r"\b(?:heart\s+rate|\bhr\b|tachycard\w*|bradycard\w*)\b", grounded):
            reasoning["management_priority"] = "optimize heart rate"
        if reasoning.get("management_priority") != before_synthesis.get("management_priority"):
            reasoning["derived_slots"] = sorted(
                set(reasoning.get("derived_slots") or ()) | {"management_priority"})

    # Guard against semantically useless duplication between slots.
    if (reasoning.get("problem_representation") and reasoning.get("rationale") and
            reasoning["problem_representation"].strip().lower() == reasoning["rationale"].strip().lower()):
        reasoning.pop("rationale", None)

    reasoning = {k: v for k, v in reasoning.items() if v}

    # The findings the learner named, inside the working model and never as a
    # fifth requirement: their absence alone holds nothing (faculty
    # specification 2026-09-23, section 3).
    import reasoning_cues
    import reasoning_provenance

    named = reasoning_cues.cues(text)
    if named:
        reasoning["mentioned_findings"] = named
    return reasoning_provenance.mark(reasoning, reasoning_provenance.STATED)


def parse_procedural_sedation_order(text):
    """Parse executable etomidate/midazolam procedural-sedation orders.

    The medication names alone are not enough: the turn must contain an explicit
    administration or sedation context. In this procedural context the route is
    treated as IV unless the learner explicitly states another route.
    """
    raw = re.sub(r"\s+", " ", str(text or "").lower()).strip()
    medications = []
    for name in ("etomidate", "midazolam"):
        for match in re.finditer(rf"\b{re.escape(name)}\b", raw):
            segment_start = max(raw.rfind(".", 0, match.start()), raw.rfind(";", 0, match.start())) + 1
            segment_end_candidates = [
                pos for pos in (raw.find(".", match.end()), raw.find(";", match.end())) if pos >= 0
            ]
            segment_end = min(segment_end_candidates) if segment_end_candidates else len(raw)
            segment = raw[segment_start:segment_end]
            local_prefix = raw[max(segment_start, match.start() - 90):match.start()]
            local_tail = raw[match.end():min(segment_end, match.end() + 55)]

            negated = bool(re.search(
                r"\b(?:do not|don't|avoid|defer|hold|withhold|no)\b[^,;.]{0,35}$",
                local_prefix,
            ))
            explicit_order = bool(re.search(
                r"\b(?:give|administer|start|use|provide|sedate with|sedation with|"
                r"sedation using|premedicate with)\b[^,;.]{0,85}$",
                local_prefix,
            ))
            chained_sedation = bool(
                re.search(r"\b(?:sedation|sedate)\s+(?:with|using)\b", segment[:match.start() - segment_start])
                and re.search(r"(?:\+|\band\b)[^,;.]{0,35}$", local_prefix)
            )
            purpose_context = bool(re.search(r"\bfor\s+(?:procedural\s+)?sedation\b", local_tail))
            if negated or not (explicit_order or chained_sedation or purpose_context):
                continue

            dose_match = re.match(r"\s*(\d+(?:\.\d+)?)\s*(mcg|µg|ug|mg|g)\b", local_tail)
            dose = float(dose_match.group(1)) if dose_match else None
            units = dose_match.group(2) if dose_match else "mg"
            route_match = re.search(r"\b(iv|intravenous|im|intramuscular|po|oral)\b", segment)
            route = "IV" if not route_match or route_match.group(1) in {"iv", "intravenous"} else route_match.group(1).upper()
            medications.append({
                "agent": name,
                "dose": dose,
                "units": units,
                "route": route,
            })
            break

    if not medications:
        return None
    return {
        "type": "procedural_sedation",
        "medications": medications,
        "purpose": "procedural sedation",
        "operation": "administer",
    }


def procedural_sedation_label(payload):
    """Stable learner-facing label for a sedation action or action summary."""
    labels = []
    for medication in payload.get("medications", []) or []:
        agent = str(medication.get("agent") or "sedative")
        dose = medication.get("dose")
        units = medication.get("units") or "mg"
        route = medication.get("route") or "IV"
        if dose is None:
            labels.append(f"{agent} {route}")
        else:
            labels.append(f"{agent} {dose:g} {units} {route}")
    return "procedural sedation with " + " + ".join(labels) if labels else "procedural sedation"


def recognized_unimplemented_medications(text):
    """Return explicitly ordered medications not modeled by the MVP.

    These orders must never disappear silently. They remain non-executable, but
    are surfaced to the learner before any supported actions in the same bundle
    produce a patient response.
    """
    raw = re.sub(r"\s+", " ", str(text or "").lower()).strip()
    medication_names = (
        "fentanyl", "ketamine", "propofol", "morphine",
        "hydromorphone", "lorazepam", "diazepam",
    )
    found = []
    for name in medication_names:
        for match in re.finditer(rf"\b{re.escape(name)}\b", raw):
            segment_start = max(raw.rfind(".", 0, match.start()), raw.rfind(";", 0, match.start())) + 1
            segment_end_candidates = [
                pos for pos in (raw.find(".", match.end()), raw.find(";", match.end())) if pos >= 0
            ]
            segment_end = min(segment_end_candidates) if segment_end_candidates else len(raw)
            segment = raw[segment_start:segment_end]
            local_prefix = raw[max(segment_start, match.start() - 85):match.start()]
            local_tail = raw[match.end():min(segment_end, match.end() + 55)]

            negated = bool(re.search(
                r"\b(?:do not|don't|avoid|defer|hold|withhold|no)\b[^,;.]{0,35}$",
                local_prefix,
            ))
            ordered = bool(re.search(
                r"\b(?:give|administer|start|use|provide|sedate with|sedation with|"
                r"analgesia with|premedicate with)\b[^,;.]{0,80}$",
                local_prefix,
            ))
            # In a chained phrase such as "sedation with etomidate + midazolam",
            # the second drug inherits the explicit procedural context.
            chained_context = bool(
                re.search(r"\b(?:sedation|analgesia)\s+with\b", segment[:match.start() - segment_start])
                and re.search(r"(?:\+|\band\b)[^,;.]{0,35}$", local_prefix)
            )
            purpose_context = bool(re.search(r"\bfor\s+(?:analgesia|sedation)\b", local_tail))
            if negated or not (ordered or chained_context or purpose_context):
                continue

            dose_match = re.match(
                r"\s*(\d+(?:\.\d+)?)\s*(mcg|µg|ug|mg|g)\b",
                local_tail,
            )
            dose = f" {dose_match.group(1)} {dose_match.group(2)}" if dose_match else ""
            if "analges" in segment or name in {"fentanyl", "morphine", "hydromorphone"}:
                purpose = " for analgesia"
            elif "sedat" in segment or name in {"etomidate", "midazolam", "ketamine", "propofol"}:
                purpose = " for procedural sedation"
            else:
                purpose = ""
            found.append((match.start(), f"{name}{dose}{purpose}"))

    labels = []
    for _, label in sorted(found, key=lambda item: item[0]):
        if label not in labels:
            labels.append(label)
    return labels


def _understood_order_labels(parsed):
    """Everything in a turn that the engine read as an order, named for the resident."""
    from family_reports import TEST_LABELS
    others = [a for a in (parsed.get("actions", []) or []) if a.get("type") != "clarification"]
    labels = []
    if any(a.get("type") in REASONING_GATE_ACTION_TYPES for a in others):
        labels.append(_reasoning_gate_action_summary({"actions": others}))
    labels.extend(
        TEST_LABELS.get(a.get("diagnostic"), str(a.get("diagnostic") or "").replace("_", " "))
        for a in others if a.get("type") == "diagnostic"
    )
    return [label for label in labels if label]


def _held_order_prompt(parsed, message):
    """A parser clarification that names the rest of the order it is holding.

    One ambiguous action holds the whole turn, which is deliberate: the engine
    never guesses at an order. But everything else in the turn is parsed and
    then discarded, so a septic patient can lose an antibiotic to a quibble
    about an oxygen device without the resident noticing. The hold is now
    declared the way the reasoning gate declares its own.
    """
    actions = parsed.get("actions", []) or []
    labels = _understood_order_labels(parsed)
    # One order the engine itself questions describes its own problem. The block
    # is for what the resident would otherwise lose without being told: another
    # order in the same turn, or an item the parser could not read at all.
    unreadable = any(a.get("type") == "clarification" for a in actions)
    if not labels or (len(labels) < 2 and not unreadable):
        return message
    return "\n".join([
        "**ORDER HELD — CLARIFICATION REQUIRED**",
        "",
        "I understood: **" + " + ".join(label for label in labels if label) + "**.",
        "Nothing in this order was executed and the patient state has not changed.",
        "",
        message,
    ])


def clinical_interpreter(text):
    if (st.session_state.get("state") or {}).get("engine_family"):
        from family_parser import parse_family_actions
        parsed = parse_family_actions(text)
        parsed["reasoning"] = extract_explicit_reasoning(text)
        unresolved = next((a for a in parsed.get("actions", []) if a.get("type") == "clarification"), None)
        if unresolved:
            parsed["clarification"] = unresolved.get("message") or "Please clarify the order."
        return parsed
    t = text.lower()
    reasoning = extract_explicit_reasoning(text)

    actions = []

    # v0.6.0.34: mentions of fluids in reasoning are not treatment orders.
    # Require an explicit administration verb (or "another X mL") in this turn.
    # This prevents phrases such as "response to the first fluid bolus was limited"
    # from creating a new fluid action and keeps each learner turn isolated.
    fluid_words = ["fluid", "fluids", "crystalloid", "saline", "ringer"]
    implicit_iv_volume = bool(
        re.search(r"\b\d+(?:\.\d+)?\s*(?:ml|cc)\b[^.;,]*\biv\b", t)
        or re.search(r"\b\d+(?:\.\d+)?\s*(?:l|lt|liter|litre|liters|litres)\b(?!\s*/?\s*(?:min|minute|minutes|hr|hour|hours)\b)[^.;,]*\biv\b", t)
    )
    explicit_fluid_order = bool(
        re.search(r"\b(?:give|administer|order|infuse|bolus|start)\b[^.;]{0,80}\b(?:fluid|fluids|crystalloid|saline|normal\s+saline|ringer|lr|ns|\d+(?:\.\d+)?\s*(?:ml|cc|l|liter|litre))\b", t)
        or re.search(r"\banother\s+\d+(?:\.\d+)?\s*(?:ml|cc|l|liter|litre)?\s*(?:of\s+)?(?:ns|lr|normal\s+saline|saline|crystalloid|fluid)?\b", t)
    )
    if explicit_fluid_order and (any(w in t for w in fluid_words) or re.search(r"\b(?:lr|ns)\b", t) or implicit_iv_volume):
        named_fluid = any(w in t for w in fluid_words) or bool(re.search(r"\b(?:lr|ns)\b", t))
        actions.append({
            "type": "fluid",
            "fluid_type": detect_fluid_type(text) if named_fluid else None,
            "volume_ml": parse_volume_ml(text),
            "rate": "rapid" if re.search(r"\b(?:rapid|rapidly)\b", t) else "standard",
        })

    beta_agent = detect_beta_blocker(text)
    if beta_agent:
        actions.append({
            "type": "beta_blocker",
            "agent": beta_agent,
            "dose_mg": parse_dose_mg(text),
            "route": parse_route(text),
        })

    if detect_diltiazem(text):
        actions.append({
            "type": "diltiazem",
            "dose_mg": parse_dose_mg(text),
            "route": parse_route(text),
        })

    if detect_amiodarone(text):
        actions.append({
            "type": "amiodarone",
            "dose_mg": parse_dose_mg(text),
            "route": parse_route(text),
        })

    if any(k in t for k in ["furosemide", "lasix"]):
        actions.append({
            "type": "furosemide",
            "dose_mg": parse_dose_mg(text),
            "route": parse_route(text),
        })

    nitro_alias = any(k in t for k in [
        "nitroglycerin", "nitroglycerine", "glyceryl trinitrate", "gtn",
        "nitro drip", "nitro infusion"
    ])
    if nitro_alias:
        actions.append({
            "type": "nitroglycerin",
            "rate_mcg_min": parse_nitroglycerin_rate(text),
            "operation": "stop" if ("stop" in t or "discontinue" in t) else "start",
        })

    niv_mode, niv_pressure, niv_ipap, niv_epap, niv_fio2 = parse_niv_order(text)
    # A support modality mentioned in the learner's reasoning is not necessarily
    # a new order (for example, "hypoxemia persists despite BiPAP"). Require a
    # local command verb, while still accepting terse orders such as "BiPAP 16/8".
    explicit_niv_order = bool(re.search(
        r"\b(?:start|initiate|apply|place|put|increase|decrease|change|switch|continue|stop|discontinue|set|adjust)\b"
        r"[^.;]{0,70}\b(?:cpap|bipap|niv|nimv|nippv|vmni|noninvasive|non-invasive)\b",
        t,
    ))
    bare_niv_order = bool(
        re.search(r"(?:^|[,;])\s*(?:cpap|bipap)\b", t)
        and (
            re.search(r"\b\d+(?:\.\d+)?\s*/\s*\d+(?:\.\d+)?\b", t)
            or re.search(r"\b\d+(?:\.\d+)?\s*(?:(?:cm|cc)\s*h2o|cmh2o)\b", t)
        )
    )
    explicit_niv_order = explicit_niv_order or bare_niv_order
    if niv_mode and explicit_niv_order:
        niv_stop = bool(re.search(
            r"\b(?:stop|discontinue)\b[^.;]{0,25}\b(?:cpap|bipap|niv|nimv|nippv|vmni|noninvasive|non-invasive)\b",
            t,
        ))
        actions.append({
            "type": "niv",
            "mode": niv_mode,
            "pressure_cmh2o": niv_pressure,
            "ipap_cmh2o": niv_ipap,
            "epap_cmh2o": niv_epap,
            "fio2_percent": niv_fio2,
            "operation": "stop" if niv_stop else "start",
        })

    invasive_airway_mentioned = bool(
        re.search(r"\bintubat(?:e|ion|ing)\b", t)
        or re.search(r"\binvasive\s+(?:mechanical\s+)?ventilation\b", t)
    )
    airway_negated = bool(re.search(
        r"\b(?:do\s+not|don't|does\s+not|doesn't|not|no\s+need\s+to|avoid|defer)\b[^.;]{0,45}\bintubat",
        t,
    ))
    airway_retrospective = bool(re.search(
        r"\b(?:after|following|since|despite)\s+(?:the\s+)?(?:patient\s+was\s+)?"
        r"(?:intubat(?:ion|ed|ing)|invasive\s+(?:mechanical\s+)?ventilation)\b",
        t,
    ))
    airway_preparation = bool(re.search(
        r"\b(?:prepare|set\s+up|get\s+ready|ready)\b[^.;]{0,35}\b(?:for\s+)?intubat",
        t,
    ))
    active_invasive = bool(st.session_state.state["treatments"].get("invasive_ventilation"))
    current_vent = st.session_state.state["treatments"]
    requested_mode = parse_ventilator_mode(text)
    requested_fio2 = parse_ventilator_fio2_percent(text, active_invasive=active_invasive)
    peep_matches = list(re.finditer(r"\bpeep\s*(?:=|of|at|to)?\s*(\d+(?:\.\d+)?)", t))
    peep_match = peep_matches[-1] if peep_matches else None
    requested_peep = float(peep_match.group(1)) if peep_match else None
    explicit_ventilator_command = bool(
        active_invasive
        and not explicit_niv_order
        and (
            requested_mode is not None
            or requested_fio2 is not None
            or requested_peep is not None
            or re.search(
                r"\b(?:continue|maintain|keep|adjust|change|increase|decrease|reduce|wean|set)\b"
                r"[^.;]{0,55}\b(?:ventilator|ventilation|ventilator settings?)\b",
                t,
            )
        )
    )
    if invasive_airway_mentioned and not airway_negated and not airway_retrospective:
        if airway_preparation:
            actions.append({"type": "airway_preparation"})
        elif active_invasive:
            current_mode = current_vent.get("ventilator_mode") or "VC/AC"
            current_fio2 = float(current_vent.get("ventilator_fio2_percent") or 40.0)
            current_peep = float(current_vent.get("ventilator_peep_cmh2o") or 5.0)
            desired_mode = requested_mode or current_mode
            desired_fio2 = requested_fio2 if requested_fio2 is not None else current_fio2
            desired_peep = requested_peep if requested_peep is not None else current_peep
            changed = (
                desired_mode != current_mode
                or abs(desired_fio2 - current_fio2) > 1e-9
                or abs(desired_peep - current_peep) > 1e-9
            )
            actions.append({
                "type": "ventilator_adjustment" if changed else "ventilator_continuation",
                "ventilator_mode": desired_mode,
                "fio2_percent": desired_fio2,
                "peep_cmh2o": desired_peep,
            })
        else:
            actions.append({
                "type": "intubation",
                "ventilator_mode": requested_mode or "VC/AC",
                "fio2_percent": requested_fio2 if requested_fio2 is not None else 100.0,
                "peep_cmh2o": requested_peep if requested_peep is not None else 8.0,
            })
    elif explicit_ventilator_command:
        current_mode = current_vent.get("ventilator_mode") or "VC/AC"
        current_fio2 = float(current_vent.get("ventilator_fio2_percent") or 40.0)
        current_peep = float(current_vent.get("ventilator_peep_cmh2o") or 5.0)
        desired_mode = requested_mode or current_mode
        desired_fio2 = requested_fio2 if requested_fio2 is not None else current_fio2
        desired_peep = requested_peep if requested_peep is not None else current_peep
        changed = (
            desired_mode != current_mode
            or abs(desired_fio2 - current_fio2) > 1e-9
            or abs(desired_peep - current_peep) > 1e-9
        )
        actions.append({
            "type": "ventilator_adjustment" if changed else "ventilator_continuation",
            "ventilator_mode": desired_mode,
            "fio2_percent": desired_fio2,
            "peep_cmh2o": desired_peep,
        })

    dobutamine_alias = any(k in t for k in [
        "dobutamine", "dobutamine infusion", "inotrope with dobutamine"
    ])
    explicit_dobutamine_order = dobutamine_alias and explicit_infusion_order(text, ["dobutamine"])
    active_dobutamine = st.session_state.state["treatments"].get("dobutamine")
    dobutamine_context = active_dobutamine and any(k in t for k in [
        "increase dobutamine", "decrease dobutamine", "continue dobutamine",
        "stop dobutamine", "titrate dobutamine"
    ])
    if explicit_dobutamine_order or dobutamine_context:
        rate, units = parse_agent_mcg_rate(text, ["dobutamine"])
        op = local_command_operation(text, ["dobutamine"], active=bool(active_dobutamine))
        active_tr = st.session_state.state["treatments"]
        if op == "continue" and active_dobutamine:
            current_rate = active_tr.get("dobutamine_rate")
            current_units = active_tr.get("dobutamine_units") or "mcg/kg/min"
            if units is None:
                units = current_units
            # Continuing an unchanged active infusion is longitudinal state, not
            # a new intervention. Preserve it without clarification or duplicate
            # action. An explicitly different rate remains an executable titration.
            if rate is None or (units == current_units and float(rate) == float(current_rate)):
                rate = None
            else:
                op = "titrate"
        if not (op == "continue" and active_dobutamine and rate is None):
            actions.append({
                "type": "dobutamine",
                "rate": rate,
                "units": units,
                "operation": op,
            })

    norepi_alias = any(k in t for k in ["norepinephrine", "noradrenaline", "levophed", "norepi", "levo"])
    explicit_norepi_order = norepi_alias and explicit_infusion_order(
        text, ["norepinephrine", "noradrenaline", "levophed", "norepi", "levo"]
    )
    active_norepi = st.session_state.state["treatments"].get("norepinephrine")
    drip_context = (not dobutamine_alias) and active_norepi and any(k in t for k in [
        "increase drip", "decrease drip", "increase infusion", "decrease infusion",
        "titrate drip", "titrate infusion", "stop drip", "stop infusion"
    ])
    if explicit_norepi_order or drip_context:
        rate, units = (
            parse_agent_mcg_rate(text, ["norepinephrine", "noradrenaline", "levophed", "norepi", "levo"])
            if norepi_alias else parse_mcg_rate(text)
        )
        op = local_command_operation(
            text, ["norepinephrine", "noradrenaline", "levophed", "norepi", "levo"], active=bool(active_norepi)
        )
        active_tr = st.session_state.state["treatments"]
        if op == "continue" and active_norepi:
            current_rate = active_tr.get("norepinephrine_rate")
            current_units = active_tr.get("norepinephrine_units")
            if units is None:
                units = current_units
            # "Continue the current norepinephrine" inherits the active rate.
            # It must not create a new start, consume time, or request the dose
            # again. A different explicitly stated rate is treated as titration.
            if rate is None or (units == current_units and float(rate) == float(current_rate)):
                rate = None
            else:
                op = "titrate"
        if not (op == "continue" and active_norepi and rate is None):
            actions.append({
                "type": "norepinephrine",
                "rate": rate,
                "units": units,
                "operation": op,
            })

    actions.extend(explicit_oxygen_actions(text))

    # Procedural sedation is deliberately placed before cardioversion in the
    # executable bundle even when the learner mentions the shock first. This
    # preserves the intended clinical sequence without hiding either action.
    sedation_action = parse_procedural_sedation_order(text)
    if sedation_action:
        actions.append(sedation_action)

    if is_explicit_cardioversion_order(text):
        actions.append({"type": "cardioversion", "energy_j": parse_energy_j(text), "synchronized": True})

    if any(k in t for k in [
        "reassess", "re-assess", "recheck", "re-check",
        "re-evaluate", "reevaluate", "observe", "watch"
    ]):
        actions.append({
            "type": "reassessment",
            "delay_min": parse_delay_min(text),
            "focus": "perfusion" if ("perfusion" in t or "hemodynamic" in t) else "general",
        })

    # v0.6.0.31: diagnostic information layer. These requests are now executable
    # informational actions. They return patient-state-coherent results without
    # directly changing physiology.
    if explicit_diagnostic_request(
        text, ["point-of-care ultrasound", "point of care ultrasound", "pocus"]
    ):
        actions.append({
            "type": "pocus",
            "requested_delay_min": parse_requested_diagnostic_delay(
                text, ["point-of-care ultrasound", "point of care ultrasound", "pocus"]
            ),
        })
    if explicit_diagnostic_request(text, ["lactate"]):
        actions.append({
            "type": "lactate",
            "requested_delay_min": parse_requested_diagnostic_delay(text, ["lactate"]),
        })
    if explicit_diagnostic_request(text, ["venous blood gas", "venous gas", "vbg"]):
        actions.append({
            "type": "vbg",
            "requested_delay_min": parse_requested_diagnostic_delay(
                text, ["venous blood gas", "venous gas", "vbg"]
            ),
        })
    if explicit_diagnostic_request(text, ["arterial blood gas", "arterial gas", "abg"]):
        actions.append({
            "type": "abg",
            "requested_delay_min": parse_requested_diagnostic_delay(
                text, ["arterial blood gas", "arterial gas", "abg"]
            ),
        })
    if explicit_diagnostic_request(
        text,
        [
            "basic laboratory tests", "basic lab tests", "basic labs", "laboratory tests",
            "laboratory exams", "lab tests", "lab exams", "labs", "blood work", "blood tests", "cbc", "creatinine",
            "chemistry", "bmp", "cmp", "crp",
        ],
    ):
        actions.append({"type": "basic_labs"})

    # v0.7.2 clinical query / infection layer.
    # Measure temperature only when it is actually requested. Mentions such as
    # "extremity temperature" are reassessment targets, and "ask about fever"
    # is history rather than a temperature order.
    if (
        explicit_diagnostic_request(text, ["temperature", "temp"])
        or re.search(r"\bfever\s*\?", str(text or ""), re.I)
    ):
        actions.append({"type": "temperature"})
    if re.search(r"\b(?:glucose|blood sugar|fingerstick|finger stick|poc glucose)\b", t):
        actions.append({"type": "poc_glucose"})
    if re.search(
        r"\b(?:other symptoms|new symptoms|associated symptoms|review symptoms|any symptoms|"
        r"urinary symptoms|fever and urinary symptoms|dysuria|urinary frequency|flank pain|chills)\b",
        t,
    ):
        actions.append({"type": "focused_history"})
    if re.search(r"\b(?:chest x[- ]?ray|cxr|chest radiograph|x[- ]?ray)\b", t):
        actions.append({"type": "chest_xray"})
    if re.search(r"\b(?:urinalysis|urine analysis|urine dip|ua)\b", t) or ("urine" in t and any(k in t for k in ["lab", "test", "exam", "send", "check"])):
        actions.append({"type": "urinalysis"})
    if re.search(r"\b(?:blood cultures?|cultures?)\b", t):
        actions.append({"type": "blood_cultures"})
    if is_explicit_antibiotic_order(text):
        if re.search(r"\bceftriaxone\b", t):
            dose_g = None
            dm = re.search(r"ceftriaxone.{0,30}?(\d+(?:\.\d+)?)\s*(?:g|gr|gram|grams)\b", t)
            if dm:
                dose_g = float(dm.group(1))
            agent = "ceftriaxone + azithromycin" if re.search(r"\bazithromycin\b", t) else "ceftriaxone"
            actions.append({
                "type": "antibiotics", "agent": agent,
                "dose_g": dose_g, "route": "IV" if re.search(r"\biv\b", t) else None,
            })
        elif re.search(r"\bazithromycin\b", t):
            actions.append({"type": "antibiotics", "agent": "azithromycin", "dose_g": None,
                            "route": "IV" if re.search(r"\biv\b", t) else None})
        else:
            actions.append({"type": "antibiotics", "agent": "broad-spectrum antibiotics", "dose_g": None, "route": None})

    # "Stop the normal saline" ends a running infusion; it is never a new bolus.
    if re.search(r"\b(?:stop|discontinue)\b[^.;]{0,30}\b(?:fluids?|saline|ns|lr|ringer'?s?|crystalloid|bolus)\b", t):
        actions.append({"type": "fluid_stop"})
    if re.search(r"\b(?:admit|admission|transfer)\b", t) and re.search(r"\b(?:icu|intensive care|critical care)\b", t):
        actions.append({"type": "disposition", "destination": "ICU"})

    future = recognized_unimplemented_medications(text)

    # A delivery duration belongs to the single treatment named in the same clause:
    # "Give 500 mL NS over 30 minutes", "metoprolol 5 mg IV over 2 minutes".
    duration_clarification = None
    timed_names = {
        "fluid": r"\b(?:\d+(?:\.\d+)?\s*(?:ml|cc|l|liters?|litres?)|saline|ns|lr|ringer'?s?|crystalloid|fluids?|bolus)\b",
        "beta_blocker": r"\b(?:metoprolol|propranolol)\b",
        "diltiazem": r"\bdiltiazem\b",
        "amiodarone": r"\bamiodarone\b",
        "furosemide": r"\b(?:furosemide|lasix)\b",
        "antibiotics": r"\b(?:ceftriaxone|azithromycin|antibiotics?|piperacillin|vancomycin)\b",
    }
    for clause in re.split(r"[.;\n]+", t):
        for m in re.finditer(
            r"\bover\s+(\d+(?:\.\d+)?)\s*(s|sec|secs|seconds?|m|min|mins|minutes?|h|hr|hrs|hours?)\b", clause
        ):
            minutes = float(m.group(1)) * (60 if m.group(2).startswith("h") else 1 / 60 if m.group(2).startswith("s") else 1)
            named = {kind for kind, pattern in timed_names.items() if re.search(pattern, clause)}
            targets = [a for a in actions if a.get("type") in named]
            if len(targets) == 1 and minutes > 0:
                targets[0]["administration_duration_min"] = minutes
            else:
                duration_clarification = (
                    "Specify one delivery duration for each fluid or medication, "
                    "in the same sentence as that order."
                )

    parsed = {
        "raw_text": text,
        "reasoning": reasoning,
        "actions": actions,
        "recognized_future_actions": future,
    }
    if duration_clarification:
        parsed["clarification"] = duration_clarification
    return parsed


def _runtime_secret(name, default=""):
    """Read deployment secrets without requiring them in local/test environments."""
    try:
        value = st.secrets.get(name, "")
    except Exception:
        value = ""
    from offline_cases import withhold
    return withhold(name, str(value or os.environ.get(name, default) or "").strip())


def ai_interpretation_enabled():
    return bool(_runtime_secret("OPENAI_API_KEY"))


def ai_language_interpretation_enabled():
    """True only when the paid per-order language normalization is switched on.

    A key alone no longer turns it on: it is a cost of one provider request per
    submission, and the deterministic parser reads the Spanish this faculty
    writes. Set MRS_AI_LANGUAGE to enable it.
    """
    setting = str(_runtime_secret("MRS_AI_LANGUAGE", "")).strip().lower()
    return bool(_runtime_secret("OPENAI_API_KEY")) and setting in {"1", "true", "yes", "on"}


def _numeric_tokens(text):
    """Return quantities whose preservation is clinically safety-relevant.

    Spanish ordinal shorthand such as ``1rio``/``2do`` is lexical rather than
    a clinical quantity and may legitimately disappear during translation.
    Attached clinical units (for example ``200J`` or ``5min``) remain protected.
    """
    protected_units = {
        "j", "joule", "joules", "mg", "mcg", "ug", "g", "kg",
        "ml", "l", "cc", "min", "mins", "minute", "minutes",
        "h", "hr", "hrs", "hour", "hours", "bpm", "mmhg", "%",
    }
    tokens = []
    raw = str(text or "")
    # Formatting-only thousands separators do not change a quantity: 1000 and
    # 1,000 must compare identically across bilingual normalization.
    raw = re.sub(r"(?<=\d),(?=\d{3}\b)", "", raw)
    for match in re.finditer(r"(?<![A-Za-z])\d+(?:\.\d+)?", raw):
        suffix_match = re.match(r"[A-Za-z%]+", raw[match.end():])
        if suffix_match and suffix_match.group(0).lower() not in protected_units:
            continue
        tokens.append(match.group(0))
    return tokens


def normalize_clinical_turn(text):
    """Return English canonical text plus an auditable interpretation record.

    Any unavailable, ambiguous, low-confidence, or locally invalid AI result
    falls back to the original text. This helper is used before direct orders,
    pending-order clarifications, and reasoning completions alike.
    """
    # Faculty decision B4, 2026-09-23: the deterministic parser is the default.
    # This helper runs before every order, every clarification and every
    # reasoning completion, so with a key configured it cost one paid request
    # per submission — measured as six requests in a five-order encounter. It is
    # now opt-in, and the engine understands Spanish without it.
    if not ai_language_interpretation_enabled():
        return text, {"mode": "deterministic"}
    api_key = _runtime_secret("OPENAI_API_KEY")
    if not api_key:
        return text, {"mode": "deterministic"}

    model = _runtime_secret("OPENAI_MODEL", "gpt-5.6-luna")
    if not spend_ai_call("language normalization"):
        return text, {"mode": "deterministic", "fallback_reason": "encounter call budget spent"}
    visible_state = deepcopy((st.session_state.get("state") or {}).get("observable") or {})
    try:
        normalized = normalize_with_ai(text, visible_state, api_key=api_key, model=model)
        if sorted(_numeric_tokens(normalized.canonical_text)) != sorted(_numeric_tokens(text)):
            raise AIInterpretationError("AI normalization introduced or removed a numeric value.")
        if explicit_oxygen_actions(text) != explicit_oxygen_actions(normalized.canonical_text):
            raise AIInterpretationError("AI normalization changed or omitted an explicit oxygen order.")
        if normalized.confidence == "low" or normalized.ambiguities:
            raise AIInterpretationError("AI normalization retained unresolved ambiguity.")
        return normalized.canonical_text, {
            "mode": "ai-assisted",
            "canonical_text": normalized.canonical_text,
            "confidence": normalized.confidence,
            "model": normalized.model,
        }
    except AIInterpretationError as exc:
        return text, {
            "mode": "deterministic-fallback",
            "fallback_reason": str(exc),
        }


def _restore_original_turn(parsed, processed_text, original_text):
    """Keep the learner's literal language in the longitudinal audit trail."""
    raw = str(parsed.get("raw_text") or "")
    if processed_text != original_text and raw.endswith(processed_text):
        raw = raw[: len(raw) - len(processed_text)] + original_text
    elif not raw:
        raw = original_text
    parsed["raw_text"] = raw
    return parsed


def _attach_interpretation_audit(parsed, audit):
    parsed["interpretation_mode"] = audit.get("mode", "deterministic")
    if audit.get("mode") == "ai-assisted":
        parsed["ai_interpretation"] = {
            key: audit[key] for key in ("canonical_text", "confidence", "model") if audit.get(key)
        }
    elif audit.get("fallback_reason"):
        parsed["ai_fallback_reason"] = audit["fallback_reason"]
    return parsed


def interpret_clinical_input(text):
    """Backward-compatible direct-turn entry point for tests and integrations."""
    processed, audit = normalize_clinical_turn(text)
    parsed = clinical_interpreter(processed)
    _restore_original_turn(parsed, processed, text)
    return _attach_interpretation_audit(parsed, audit)


REASONING_GATE_ACTION_TYPES = {
    "fluid", "beta_blocker", "diltiazem", "amiodarone", "furosemide",
    "nitroglycerin", "niv", "airway_preparation", "intubation",
    "ventilator_adjustment", "ventilator_continuation", "dobutamine",
    "norepinephrine", "oxygen", "procedural_sedation", "cardioversion",
    "antibiotics", "disposition",
    "repeat_order", "respiratory_adjustment", "bronchodilator", "steroid", "ppi", "aspirin", "p2y12", "diuretic", "dextrose",
    "naloxone", "blood", "anticoagulation", "bag_mask", "consult", "nitroglycerin_bolus", "magnesium",
    "epinephrine", "epinephrine_bolus", "epinephrine_im", "continuous_bronchodilator",
    # Named by its role; the engine resolves which infusion before it runs.
    "infusion_adjustment",
    # Treatments the parser learned after this list was written, each with a
    # gated counterpart above (a drug, a reversal, cardioversion, blood). They
    # ran with no stated expectation: "Doy atropina 1 mg ev" executed where
    # "Doy naloxona 0.1 mg ev" was asked what it was for (rehearsal of the
    # twenty-scenario batch, 2026-09-24). Support orders stay out by design,
    # and whether the trauma bedside procedures belong here is the faculty's
    # (docs/DECISIONES_CLINICAS_PENDIENTES.md).
    "atropine", "transcutaneous_pacing", "glucagon", "calcium", "thiamine", "octreotide",
    "thrombolysis", "tranexamic_acid", "opioid_analgesia", "antipyretic", "oral_carbohydrate",
    "dextrose_infusion", "naloxone_infusion", "neuromuscular_blockade", "sedation_infusion",
    # Urgent interventions record what was stated and what was not, and run
    # without being held (urgent_interventions, faculty decision 12, 2026-09-25).
    "chest_decompression", "hemorrhage_control", "pelvic_binder",
}

REASONING_GATE_FIELD_LABELS = {
    "working_model": "What do you think is going on?",
    "management_priority": "Which problem are you addressing first? (optional)",
    "expected_effect": "What do you expect to happen, or what are you trying to clarify?",
    "reassessment_target": "What will you check, and when?",
    "reassessment_timing": "When will you check it?",
}

REASONING_GATE_FIELD_STEMS = {
    "working_model": "What do you think is going on?",
    "management_priority": "Which problem are you addressing first? (optional)",
    "expected_effect": "What do you expect to happen, or what are you trying to clarify?",
    "reassessment_target": "What will you check?",
}

REASONING_GATE_OVERRIDE = "execute without complete reasoning"

# The four things a management order has to carry: the working model, what the
# learner expects, what they will reassess, and the action itself. The action is
# the fourth, and it is what makes the gate fire at all, so it can never be the
# field that is missing.
#
# Two fields that used to hold an order no longer do. Measured on 2026-09-23
# against fifteen orders that named all four categories in ordinary prose, seven
# were held; in five of those the only absent field was management_priority. The
# resident had written the model, the expectation, the reassessment and the
# order, and the encounter stopped to ask for a heading. Reassessment timing
# behaved the same way. Both are still extracted, still recorded, and still
# reach the faculty as gaps in ``reasoning_gate["noted"]`` — noted rather than
# enforced, which is how this simulator treats every other omission a resident
# makes rather than standing in the doorway over it.
REASONING_GATE_BLOCKING = ("working_model", "expected_effect", "reassessment_target")
REASONING_GATE_NOTED = ("management_priority", "reassessment_timing")


def reasoning_gate_gaps(parsed):
    """Return every prospective reasoning field absent from a management order."""
    if parsed.get("clarification"):
        return []
    actions = parsed.get("actions", []) or []
    requires_gate = any(a.get("type") in REASONING_GATE_ACTION_TYPES for a in actions)
    if not requires_gate:
        return []

    reasoning = parsed.get("reasoning", {}) or {}
    gaps = []
    # A causal explanation can itself be the learner's working model even when
    # it was not introduced with the literal phrase "my working model is".
    if not (reasoning.get("problem_representation") or reasoning.get("rationale")):
        gaps.append("working_model")
    if not reasoning.get("management_priority"):
        gaps.append("management_priority")
    if not reasoning.get("expected_effect"):
        gaps.append("expected_effect")

    reassessments = [a for a in actions if a.get("type") == "reassessment"]
    timed_reassessment = any(a.get("delay_min") is not None for a in reassessments)
    if not reasoning.get("reassessment_target"):
        gaps.append("reassessment_target")
    # A discharge's follow-up says when on its own ("en 48 horas"), and it is
    # never a reassessment the clinical clock should run to.
    from discharge_follow_up import dated as follow_up_is_dated
    if not timed_reassessment and not follow_up_is_dated(parsed):
        gaps.append("reassessment_timing")
    return gaps


def reasoning_gate_missing(parsed):
    """Return the prospective fields whose absence holds the order.

    An urgent intervention is never held (faculty decision 12, 2026-09-25): its
    gaps are recorded as noted and may be explained afterwards, as retrospective.
    """
    from urgent_interventions import is_urgent
    if is_urgent(parsed):
        return []
    return [field for field in reasoning_gate_gaps(parsed)
            if field in REASONING_GATE_BLOCKING]


def reasoning_gate_noted(parsed):
    """Return prospective gaps that are recorded and never hold the order.

    These travel with the decision into the Management Trace, so the faculty
    reads "no stated priority" where it happened instead of the encounter
    refusing to move until the resident supplies the word.
    """
    from urgent_interventions import is_urgent
    if is_urgent(parsed):
        return reasoning_gate_gaps(parsed)
    return [field for field in reasoning_gate_gaps(parsed)
            if field in REASONING_GATE_NOTED]


def carried_reasoning(trace=None):
    """The interpretation the resident last stated, and the decision they said it in.

    A resident who explained what they think is happening does not have to write
    it again before every order in the same encounter. Carrying it is not the
    same as hearing it twice: the attribution points at the decision and the
    minute where it was actually said, so the record never reads as a fresh
    reaffirmation (faculty decision 2026-09-23, section 6).

    Only the interpretation travels. An expectation and a reassessment plan
    belong to the action that produced them, and carrying those would attach a
    resident's words to a decision they were never about.
    """
    import reasoning_provenance

    events = list(trace if trace is not None
                  else st.session_state.get("management_trace", []) or [])
    for index in range(len(events) - 1, -1, -1):
        event = events[index]
        if event.get("execution_status") != "executed":
            continue
        reasoning = event.get("reasoning") or {}
        provenance = reasoning.get("slot_provenance") or {}
        # Look for where it was said, not for where it was carried, so a third
        # order still names the first.
        firsthand = {reasoning_provenance.STATED, reasoning_provenance.COMPLETED}
        found = {field: reasoning[field] for field in reasoning_provenance.CARRYABLE
                 if reasoning.get(field) and provenance.get(field) in firsthand}
        if found.get("problem_representation") or found.get("rationale"):
            # The decision's own number among the decisions the resident made,
            # not its stored position plus one: questions, examinations and
            # held orders sit in the same list (2026-09-24). The position is
            # kept too, so a reader can always resolve it again.
            ordinal = sum(1 for earlier in events[:index + 1]
                          if earlier.get("execution_status") in ("executed", "terminal_locked"))
            return {"reasoning": found, "decision": ordinal, "trace_index": index,
                    "minute": event.get("decision_time_min")}
    return None


def apply_carried_reasoning(parsed, missing):
    """Fill a working model the resident already gave, rather than asking again."""
    import reasoning_provenance

    missing = list(missing or [])
    if "working_model" not in missing:
        return missing
    carried = carried_reasoning()
    if not carried:
        return missing

    reasoning = parsed.setdefault("reasoning", {})
    provenance = dict(reasoning.get("slot_provenance") or {})
    for field, value in carried["reasoning"].items():
        if reasoning.get(field):
            continue
        reasoning[field] = value
        provenance[field] = reasoning_provenance.CARRIED
    reasoning["slot_provenance"] = provenance
    reasoning["carried_from"] = {"decision": carried["decision"],
                                 "trace_index": carried["trace_index"],
                                 "minute": carried["minute"]}
    return reasoning_gate_missing(parsed)


#: Adjuncts that ride on a plan the resident already explained: an antipyretic or
#: a snack inside it does not open another form (faculty decision 6, 2026-09-25).
PLAN_ADJUNCTS = frozenset({"antipyretic", "oral_carbohydrate", "ppi", "thiamine"})


def plan_reasoning(trace=None):
    """The last plan the resident explained: its expectation, its reassessment, what it ordered.

    A decision is a plan when its expectation and its reassessment were written
    by the resident for it, in the entry or in the follow-up. A decision that only
    shared them is not a new plan, so the search goes back to the one that said them.
    """
    import reasoning_provenance

    events = list(trace if trace is not None
                  else st.session_state.get("management_trace", []) or [])
    firsthand = {reasoning_provenance.STATED, reasoning_provenance.COMPLETED}
    for index in range(len(events) - 1, -1, -1):
        event = events[index]
        if event.get("execution_status") != "executed":
            continue
        reasoning = event.get("reasoning") or {}
        provenance = reasoning.get("slot_provenance") or {}
        if not all(reasoning.get(field) and provenance.get(field) in firsthand
                   for field in reasoning_provenance.SHAREABLE):
            continue
        kinds = {str(a.get("type")) for a in event.get("interpreted_action") or [] if isinstance(a, dict)}
        decision = sum(1 for e in events[:index + 1] if e.get("execution_status") in ("executed", "terminal_locked"))
        return {"reasoning": {field: reasoning[field] for field in reasoning_provenance.SHAREABLE},
                "kinds": kinds, "decision": decision, "trace_index": index,
                "minute": event.get("decision_time_min")}
    return None


def _kind_of(action):
    """What a repeat repeats, so that it can be recognised as part of its plan."""
    if action.get("type") != "repeat_order":
        return action.get("type")
    if action.get("target"):
        return action["target"]
    from family_parser import _AGENTS
    return next((kind for kind, agents in _AGENTS.items() if action.get("agent") in agents), "repeat_order")


def apply_plan(parsed, missing):
    """Share the plan's expectation and reassessment with an order inside it.

    Inside it: every order that needs the four is an adjunct, or a repeat of what
    the plan already ordered. Anything else is a relevant new decision, and it is
    still asked about -- with the plan's own answers offered in the form.
    """
    import reasoning_provenance

    missing = list(missing or [])
    wanted = [field for field in reasoning_provenance.SHAREABLE if field in missing]
    if not wanted:
        return missing
    plan = plan_reasoning()
    if not plan:
        return missing
    gated = {_kind_of(a) for a in parsed.get("actions", []) or []
             if a.get("type") in REASONING_GATE_ACTION_TYPES}
    if gated and gated <= (PLAN_ADJUNCTS | plan["kinds"]):
        reasoning = parsed.setdefault("reasoning", {})
        provenance = dict(reasoning.get("slot_provenance") or {})
        for field in wanted:
            reasoning[field] = plan["reasoning"][field]
            provenance[field] = reasoning_provenance.SHARED
        reasoning["slot_provenance"] = provenance
        reasoning["shared_from"] = {"decision": plan["decision"], "trace_index": plan["trace_index"],
                                    "minute": plan["minute"]}
        return reasoning_gate_missing(parsed)
    parsed["plan_suggestion"] = {field: plan["reasoning"][field] for field in wanted}
    return missing


def ai_call_budget():
    """How many provider requests one encounter may spend, at most.

    A bounded budget has been the standing condition on every paid call in this
    project. Until now it was a promise kept by hand; this is the counter that
    keeps it. Set MRS_AI_CALL_BUDGET to change it.
    """
    raw = str(_runtime_secret("MRS_AI_CALL_BUDGET", "")).strip()
    try:
        return max(0, int(raw))
    except ValueError:
        return 8


def ai_calls_spent():
    return int(st.session_state.get("ai_calls_spent", 0) or 0)


def spend_ai_call(purpose):
    """Take one request from this encounter's budget, or refuse it.

    Refusing is not an error. Every caller of this falls back to the
    deterministic reading it would have used anyway, and says in the record that
    the budget was the reason rather than the resident.
    """
    if ai_calls_spent() >= ai_call_budget():
        return False
    st.session_state.ai_calls_spent = ai_calls_spent() + 1
    ledger = list(st.session_state.get("ai_call_ledger", []) or [])
    ledger.append({
        "purpose": str(purpose),
        "minute": (st.session_state.get("state") or {}).get("sim_time"),
    })
    st.session_state.ai_call_ledger = ledger[:200]
    return True


def ai_cue_mode():
    """Whether a model is asked to read the findings, and how often.

    ``held`` costs nothing beyond what is already being spent: the question
    rides along on the request a held order was going to make anyway -- the
    second reader's, MRS_AI_REASONING -- so without that reader there is no
    request to ride and ``held`` is ``off`` (2026-09-24: it used to report
    ``held`` and read nothing). ``always`` reads every decision and costs one
    request each, which is the difference between an exception and a per-order
    charge. Set MRS_AI_CUES.

    What a model reads is only ever the resident's own words about one of their
    decisions: nothing it returns is shown to the resident while they decide,
    and nothing it returns reaches the faculty brief, the rubric or the record's
    screening -- those read the record, never the cues.
    """
    setting = str(_runtime_secret("MRS_AI_CUES", "")).strip().lower()
    if setting not in {"held", "always"} or not _runtime_secret("OPENAI_API_KEY"):
        return "off"
    if setting == "held" and not ai_reasoning_recognition_enabled():
        return "off"
    return setting


def merge_cues(parsed, found, refused=0):
    """Add what the model read to what the patterns read, without duplicating.

    The patterns come first and keep their rows: they carry the statement behind
    each finding, and they are free. A model row survives only where the
    patterns saw nothing, and says so, because the faculty reading a cue should
    know which of the two read it.
    """
    import reasoning_cues

    reasoning = parsed.setdefault("reasoning", {})
    existing = list(reasoning.get("mentioned_findings") or [])
    for row in existing:
        row.setdefault("source", "pattern")
    seen = {reasoning_cues.key(row.get("finding")) for row in existing}
    added = 0
    not_observations = 0
    text = str(parsed.get("raw_text") or "")
    for row in found or ():
        key = reasoning_cues.key(row.get("finding"))
        # One finding written twice at different lengths is one finding. A real
        # encounter on 2026-09-23 produced "crepitantes" from the patterns and
        # "crepitantes en la base derecha" from the model, and listing both
        # would count one observation as two.
        if not key or any(key in other or other in key for other in seen):
            continue
        # The patterns' rule binds the model too: words inside an expectation or
        # a plan are not something the resident observed, and recording them as
        # a finding would present an expected response as one they had seen.
        if not reasoning_cues.observed(text, row.get("finding")):
            not_observations += 1
            continue
        seen.add(key)
        existing.append(dict(row))
        added += 1
    if existing:
        reasoning["mentioned_findings"] = reasoning_cues.sanitise(existing)
    audit = dict(parsed.get("cue_recognition") or {})
    audit.update({"status": "read", "added_by_model": added,
                  "rejected": int(refused) + not_observations,
                  "not_an_observation": not_observations})
    parsed["cue_recognition"] = audit
    return parsed


def recognize_cues_for(parsed):
    """Ask a model for the findings in a decision that was not held.

    This is the one path that costs a request per decision rather than per held
    order, so it is off unless MRS_AI_CUES is "always" and it takes its request
    from the same encounter budget as everything else.
    """
    if ai_cue_mode() != "always":
        return parsed
    text = str(parsed.get("raw_text") or "").strip()
    if not text or not any(a.get("type") in REASONING_GATE_ACTION_TYPES
                           for a in parsed.get("actions", []) or []):
        return parsed
    if not spend_ai_call("cue recognition"):
        parsed["cue_recognition"] = {"status": "budget_exhausted",
                                     "spent": ai_calls_spent(),
                                     "budget": ai_call_budget()}
        return parsed

    from reasoning_recognition import ReasoningRecognitionError, recognize
    try:
        found = recognize(
            text, (), cues=True,
            api_key=_runtime_secret("OPENAI_API_KEY"),
            model=_runtime_secret("OPENAI_MODEL", "gpt-5.6-luna"),
        )
    except ReasoningRecognitionError as exc:
        # A failure of the model is a failure of the model. The entry is intact
        # and the patterns already read it; nothing is presented as something
        # the resident omitted (specification section 8).
        parsed["cue_recognition"] = {"status": "unavailable", "reason": str(exc)}
        return parsed
    return merge_cues(parsed, found.cues, found.cues_rejected)


def ai_reasoning_recognition_enabled():
    """True only when the second reader for held orders is switched on.

    It is deliberately separate from MRS_AI_LANGUAGE. That one normalizes every
    submission and costs a request per order; this one is asked only about an
    order the deterministic parser was about to hold, so a resident who writes
    the four categories in a way the patterns already read never buys anything.
    Set MRS_AI_REASONING to enable it.
    """
    setting = str(_runtime_secret("MRS_AI_REASONING", "")).strip().lower()
    return bool(_runtime_secret("OPENAI_API_KEY")) and setting in {"1", "true", "yes", "on"}


def reasoning_still_missing(parsed):
    """The categories a submission still lacks once everything free has been tried.

    Free before paid: what the resident already said in this encounter is
    consulted before a model is asked to read this submission again, and a
    model is asked only about an order that would otherwise be held. With
    ``MRS_AI_CUES=held``, that one request also reads the findings.
    """
    # After a discharge the reassessment is the follow-up the resident arranged
    # (faculty decision 1, 2026-09-25): read before anything is asked again.
    from discharge_follow_up import adopt as adopt_discharge_follow_up
    adopt_discharge_follow_up(parsed)
    missing = reasoning_gate_missing(parsed)
    if missing:
        missing = apply_carried_reasoning(parsed, missing)
    if missing:
        missing = apply_plan(parsed, missing)
    if missing:
        missing = recognize_held_reasoning(parsed, missing)
    return missing


def recognize_held_reasoning(parsed, missing):
    """One last look before an order is held: did the resident already write it?

    Returns the fields that are still missing afterwards. The model may only
    point at the resident's own words — every span it returns is checked against
    the submission and dropped unless it is in it verbatim — so this can rescue
    an order from a phrasing the patterns did not know, and cannot put a
    sentence the resident never wrote into the record the faculty assesses.
    """
    missing = list(missing or [])
    if not missing or not ai_reasoning_recognition_enabled():
        return missing
    from reasoning_recognition import (
        SLOT_FIELDS, ReasoningRecognitionError, recognize)

    text = str(parsed.get("raw_text") or "").strip()
    if not text:
        return missing
    # The request is already being paid for, so ask about the gaps that would
    # only have been noted as well: the answer enriches the trace for free.
    asked = missing + [field for field in reasoning_gate_noted(parsed)
                       if field in SLOT_FIELDS and field not in missing]
    if not spend_ai_call("held-order recognition"):
        parsed["reasoning_recognition"] = {"status": "budget_exhausted",
                                           "spent": ai_calls_spent(),
                                           "budget": ai_call_budget()}
        return missing
    # The findings ride along on a request that is already being paid for, so
    # asking for them here costs nothing beyond it (specification section 8).
    with_cues = ai_cue_mode() != "off"
    try:
        found = recognize(
            text, asked, cues=with_cues,
            api_key=_runtime_secret("OPENAI_API_KEY"),
            model=_runtime_secret("OPENAI_MODEL", "gpt-5.6-luna"),
        )
    except ReasoningRecognitionError as exc:
        # An unavailable second reader holds the order exactly as before.
        parsed["reasoning_recognition"] = {"status": "unavailable", "reason": str(exc)}
        return missing
    if with_cues:
        merge_cues(parsed, found.cues, found.cues_rejected)

    reasoning = parsed.setdefault("reasoning", {})
    for category, quote in found.slots.items():
        slot = SLOT_FIELDS.get(category)
        if slot and not reasoning.get(slot):
            reasoning[slot] = quote
    if found.slots:
        reasoning["recognized_slots"] = sorted(
            set(reasoning.get("recognized_slots") or ()) | set(found.slots))
    parsed["reasoning_recognition"] = {
        "status": "read",
        "model": found.model,
        "recognized": sorted(found.slots),
        "absent": list(found.absent),
        # A span the model did not copy accurately is refused, and saying so is
        # how a drift in its behaviour becomes visible rather than silent.
        "rejected": list(found.rejected),
    }
    return reasoning_gate_missing(parsed)


def reasoning_state_observations(parsed, state):
    """Return neutral, non-blocking checks against the current visible state."""
    actions = parsed.get("actions", []) or []
    if not any(action.get("type") in REASONING_GATE_ACTION_TYPES for action in actions):
        return []

    reasoning = parsed.get("reasoning", {}) or {}
    text = " ".join(
        [str(parsed.get("raw_text") or "")]
        + [str(value or "") for value in reasoning.values() if isinstance(value, str)]
    ).lower()
    observable = (state or {}).get("observable", {}) or {}
    notes = []

    hr = observable.get("hr")
    if hr is not None and hr <= 100 and re.search(r"\b(?:tachycardia|tachycardic)\b", text):
        notes.append(
            f"Your reasoning mentions tachycardia; the current HR is {hr}/min. "
            "This does not block the order. If you mean relative tachycardia or an earlier state, you can clarify it."
        )

    rhythm = str(observable.get("rhythm") or "")
    if re.search(r"\bsinus\s+rhythm\b", rhythm, re.I) and re.search(
        r"\b(?:still|persistent|persists?|remains?)\b.{0,24}\b(?:a-?fib|afib|atrial\s+fibrillation|af)\b",
        text,
        re.I,
    ):
        notes.append(
            f"Your reasoning describes persistent atrial fibrillation; the current rhythm is {rhythm}. "
            "This context check does not block the order."
        )
    return notes


def _reasoning_gate_action_summary(parsed):
    """Human-readable summary of executable actions currently being held."""
    labels = []
    for action in parsed.get("actions", []) or []:
        atype = action.get("type")
        if atype not in REASONING_GATE_ACTION_TYPES:
            continue
        if atype == "fluid":
            volume = action.get("volume_ml")
            fluid = action.get("fluid_type") or "crystalloid"
            labels.append(f"{volume:g} mL {fluid}" if volume is not None else fluid)
        elif atype in {"beta_blocker", "diltiazem", "amiodarone", "furosemide", "antibiotics", "bronchodilator", "steroid", "ppi", "aspirin", "p2y12", "diuretic", "naloxone", "magnesium"}:
            agent = action.get("agent") or atype.replace("_", " ")
            dose = action.get("dose_mg")
            route = action.get("route") or ""
            labels.append(f"{agent} {dose:g} mg {route}".strip() if dose is not None else agent)
        elif atype in {"dextrose", "anticoagulation", "blood"}:
            dose = action.get("dose_g") if atype == "dextrose" else action.get("dose") if atype == "anticoagulation" else action.get("units")
            units = "g" if atype == "dextrose" else action.get("units", "") if atype == "anticoagulation" else "unit(s)"
            agent = action.get("agent") or atype
            route = action.get("route") or ""
            labels.append(f"{agent} {dose:g} {units} {route}".strip() if dose is not None else agent)
        elif atype == "oxygen":
            device = action.get("device") or "oxygen"
            flow = action.get("flow_lpm")
            labels.append(f"{device} {flow:g} L/min" if flow is not None else device)
        elif atype == "cardioversion":
            energy = action.get("energy_j")
            labels.append(f"synchronized cardioversion {energy:g} J" if energy is not None else "synchronized cardioversion")
        elif atype == "epinephrine_im":
            labels.append(f"epinephrine {action.get('dose_mg', 0):g} mg {action.get('route') or 'IM'}")
        elif atype == "procedural_sedation":
            labels.append(procedural_sedation_label(action))
        elif atype in {"norepinephrine", "dobutamine"}:
            rate = action.get("rate")
            operation = action.get("operation") or "start"
            if operation == "stop":
                labels.append(f"stop {atype}")
            elif rate is not None:
                labels.append(f"{operation} {atype} {rate:g} {action.get('units') or 'mcg/kg/min'}")
            else:
                labels.append(f"{operation} {atype}")
        elif atype == "nitroglycerin":
            rate = action.get("rate_mcg_min")
            operation = action.get("operation") or "start"
            labels.append(f"{operation} nitroglycerin {rate:g} mcg/min" if rate is not None else f"{operation} nitroglycerin")
        elif atype == "niv":
            mode = action.get("mode") or "NIV"
            if action.get("ipap_cmh2o") is not None and action.get("epap_cmh2o") is not None:
                labels.append(f"{mode} {action['ipap_cmh2o']:g}/{action['epap_cmh2o']:g}")
            else:
                labels.append(mode)
        elif atype == "infusion_adjustment":
            rate, units = action.get("rate_value"), action.get("rate_units")
            operation = action.get("operation") or "adjust"
            labels.append(f"{operation} the running infusion"
                          + (f" at {rate:g} {units}" if rate is not None else ""))
        elif atype == "airway_preparation":
            labels.append("prepare for intubation")
        elif atype == "intubation":
            labels.append("intubation with invasive ventilation")
        elif atype in {"ventilator_adjustment", "ventilator_continuation"}:
            labels.append(atype.replace("_", " "))
        elif atype == "antibiotics":
            labels.append(str(action.get("agent") or "antibiotics"))
        elif atype == "disposition":
            # Going home is a discharge: a held "Lo envio a su casa" read back
            # as "admission to home" (rehearsal of the twenty-scenario batch).
            labels.append("discharge home" if action.get("destination") == "home"
                          else f"admission to {action.get('destination') or 'ICU'}")
        else:
            labels.append(atype.replace("_", " "))
    return " + ".join(labels) if labels else "management intervention"


def _held_order_summary(parsed):
    """What a held turn says it understood: interventions and investigations."""
    return " + ".join(_understood_order_labels(parsed)) or "management intervention"


def _joined_clauses(items):
    """"a", "a and b", "a, b and c" — said the way a person says a short list."""
    items = [item for item in items if item]
    if len(items) <= 1:
        return items[0] if items else ""
    return ", ".join(items[:-1]) + " and " + items[-1]


def reasoning_gate_prompt(parsed, missing):
    """Say what was recognised before saying what is missing.

    A hold that only lists demands reads as a rejection of the whole entry. The
    resident wrote most of this; naming that first is the difference between
    "you did not do it right" and "two of the four are here"
    (faculty specification 2026-09-23, section 4).
    """
    missing = list(missing)
    import reasoning_questions

    recognised = ["action"] + [field for field, _, _ in reasoning_questions.QUESTIONS
                               if field != "action" and field not in missing]
    lines = [
        "**ORDER HELD — REASONING REQUIRED**",
        "",
        f"I understood: **{_held_order_summary(parsed)}**.",
        "The order has not been executed and the patient state has not changed.",
        "",
        "I recognised " + _joined_clauses(
            [reasoning_questions.SHORT[field] for field in recognised]) + ".",
        "Still to state: " + _joined_clauses(
            [reasoning_questions.SHORT[field] for field in missing]) + ".",
        "",
        "In your own words, or in the fields on screen:",
    ]
    lines.extend(f"- {REASONING_GATE_FIELD_LABELS[field]}" for field in missing)
    recognized_unmodeled = [
        str(item) for item in (parsed.get("recognized_future_actions") or []) if item
    ]
    if recognized_unmodeled:
        lines.extend([
            "",
            "**Also recognized but not executable in this build:** "
            + ", ".join(recognized_unmodeled)
            + ". These medications have not been administered.",
        ])
    lines.extend([
        "",
        "You do not need to repeat the order. What you already wrote is kept.",
    ])
    return "\n".join(lines)


def clear_reasoning_gate_clarification():
    """Remove the transient gate prompt so it never accumulates in the timeline."""
    marker = "ORDER HELD — REASONING REQUIRED"
    events = list(st.session_state.get("events", []) or [])
    st.session_state.events = [
        event for event in events
        if not (
            event.get("kind") == "clarification"
            and marker in str(event.get("text") or "")
        )
    ]


def upsert_reasoning_gate_clarification(parsed, missing):
    """Keep one current reasoning prompt rather than repeating it after each try."""
    prompt = reasoning_gate_prompt(parsed, missing)
    clear_reasoning_gate_clarification()
    add_event("clarification", prompt)
    return prompt


def next_reasoning_gate_id():
    """Return a fresh widget namespace whenever held reasoning is revised."""
    gate_id = int(st.session_state.get("reasoning_gate_counter", 0)) + 1
    st.session_state.reasoning_gate_counter = gate_id
    return gate_id


def hold_pending_reasoning(parsed, missing=None):
    """Freeze an interpreted order until its prospective reasoning is complete."""
    missing = list(missing if missing is not None else reasoning_gate_missing(parsed))
    existing = st.session_state.get("pending_reasoning") or {}
    if existing:
        gate_id = int(existing.get("gate_id") or 1)
        held_at = existing.get("held_at_min")
        held_after = existing.get("held_after_decisions")
    else:
        gate_id = next_reasoning_gate_id()
        held_at = (st.session_state.get("state") or {}).get("sim_time")
        held_after = len(st.session_state.get("management_trace", []) or [])
    st.session_state.pending_reasoning = {
        "parsed": deepcopy(parsed),
        "missing": missing,
        "gate_id": gate_id,
        # The moment the order was held, so that an explanation written later can
        # be told from one written before this decision had any results. A held
        # order cannot execute and no other order runs while it waits, so these
        # should never move; recording them is how a future change that opens
        # that door becomes visible instead of quietly improving a score.
        "held_at_min": held_at,
        "held_after_decisions": held_after,
        # What the application asked for, each time it asked (2026-09-24): a
        # neutral request is not clinical help, and a reader must be able to
        # tell what was said spontaneously from what was said when asked.
        "asked": list(existing.get("asked") or []) + [{"minute": held_at, "missing": missing}],
    }
    return reasoning_gate_prompt(parsed, missing)


def _rehold(held, pending, missing):
    """Hold again after a partial answer, keeping when it was first held and what was asked."""
    now = (st.session_state.get("state") or {}).get("sim_time")
    st.session_state.pending_reasoning = {
        "parsed": deepcopy(held),
        "missing": missing,
        "gate_id": next_reasoning_gate_id(),
        "held_at_min": (pending or {}).get("held_at_min"),
        "held_after_decisions": (pending or {}).get("held_after_decisions"),
        "asked": list((pending or {}).get("asked") or []) + [{"minute": now, "missing": missing}],
    }


def _seal_reasoning(held, pending, via=""):
    """Record when this decision's justification was fixed, and against what.

    Faculty decision 2026-09-23, sections 6 and 7: a follow-up that completes a
    decision must happen before that decision's own results are revealed, and an
    explanation written afterwards must never be attributed back to it.

    Since 2026-09-24 it also records which categories the application asked
    for (``asked_for``) and how the answer came back (``answered_via``: the four
    questions' form, free text, or a facilitator override).
    """
    now = (st.session_state.get("state") or {}).get("sim_time")
    decisions = len(st.session_state.get("management_trace", []) or [])
    held_at = (pending or {}).get("held_at_min")
    held_after = (pending or {}).get("held_after_decisions")
    late = bool(
        (held_at is not None and now is not None and now != held_at)
        or (held_after is not None and decisions != held_after)
    )
    gate = dict(held.get("reasoning_gate") or {})
    gate["sealed_at_min"] = now
    gate["completed_after_results"] = late
    asked = [entry for entry in ((pending or {}).get("asked") or []) if isinstance(entry, dict)]
    if not asked and (pending or {}).get("missing"):
        asked = [{"minute": held_at, "missing": list(pending.get("missing") or [])}]
    gate["asked_for"] = list(dict.fromkeys(
        field for entry in asked for field in (entry.get("missing") or []) if isinstance(field, str)))
    gate["prompts"] = asked
    if via:
        gate["answered_via"] = via
    held["reasoning_gate"] = gate
    return held


def cancel_pending_order():
    """Discard unexecuted orders, preserving patient state and encounter evidence."""
    from pending_cancellation import clear_pending_orders
    if not clear_pending_orders(st.session_state):
        return False
    clear_reasoning_gate_clarification()
    next_reasoning_gate_id()
    add_event("order_cancelled", "Pending orders cancelled before execution. No treatment administered; simulation time unchanged.")
    return True


def complete_pending_reasoning_fields(
    working_model,
    management_priority,
    expected_effect,
    reassessment_target,
    reassessment_delay_min,
):
    """Complete a held order from sentence-stem fields without reparsing prose."""
    pending = st.session_state.get("pending_reasoning")
    if not pending:
        return None

    import reasoning_provenance

    held = deepcopy(pending.get("parsed") or {})
    reasoning = deepcopy(held.get("reasoning", {}) or {})
    field_values = {
        "problem_representation": working_model,
        "management_priority": management_priority,
        "expected_effect": expected_effect,
        "reassessment_target": reassessment_target,
    }
    provenance = dict(reasoning.get("slot_provenance") or {})
    for field, value in field_values.items():
        cleaned = _clean_reasoning_phrase(str(value or ""))
        # The form arrives prefilled with what was extracted, so a field the
        # resident left untouched keeps the hand that first wrote it. Only a
        # field they actually changed or supplied becomes theirs to own here.
        if cleaned != str(reasoning.get(field) or ""):
            provenance[field] = reasoning_provenance.COMPLETED
        if cleaned:
            reasoning[field] = cleaned
        else:
            reasoning.pop(field, None)
            provenance.pop(field, None)
    reasoning["slot_provenance"] = provenance
    reasoning_provenance.mark(reasoning, reasoning_provenance.COMPLETED)
    held["reasoning"] = reasoning

    delay = None
    try:
        if reassessment_delay_min is not None:
            delay = max(1, int(round(float(reassessment_delay_min))))
    except (TypeError, ValueError):
        delay = None

    actions = deepcopy(held.get("actions", []) or [])
    replacement = {
        "type": "reassessment",
        "delay_min": delay,
        "focus": "perfusion" if re.search(
            r"\b(?:perfusion|capillary|crt|blood pressure|bp|map)\b",
            str(reassessment_target or ""),
            re.I,
        ) else "general",
    }
    replaced = False
    revised_actions = []
    for action in actions:
        if action.get("type") == "reassessment":
            if not replaced:
                revised_actions.append(deepcopy(replacement))
                replaced = True
            continue
        revised_actions.append(action)
    if not replaced:
        revised_actions.append(deepcopy(replacement))
    held["actions"] = revised_actions

    # Use field labels rather than rebuilding prose around learner fragments.
    # This avoids joining a sentence stem to an already complete clause and
    # keeps the learner's wording visibly separate from system scaffolding.
    transcript = (
        f"**Working model:** {reasoning.get('problem_representation', '')}  \n"
        f"**Management priority:** {reasoning.get('management_priority', '')}  \n"
        f"**Expected effect:** {reasoning.get('expected_effect', '')}  \n"
        f"**Reassessment:** {reasoning.get('reassessment_target', '')} "
        f"in {delay if delay is not None else '[time]'} minutes"
    )
    held["raw_text"] = (
        str(held.get("raw_text") or "").strip()
        + "\n\nGuided reasoning completion: " + transcript
    ).strip()

    missing = reasoning_gate_missing(held)
    if missing:
        _rehold(held, pending, missing)
        return {
            "clarification": reasoning_gate_prompt(held, missing),
            "missing": missing,
        }

    held["reasoning_gate"] = {"required": True, "status": "complete", "missing": [],
                              "noted": reasoning_gate_noted(held)}
    _seal_reasoning(held, pending, "form")
    st.session_state.pending_reasoning = None
    clear_reasoning_gate_clarification()
    return {"parsed": held, "overridden": False, "transcript": transcript}


def resolve_pending_reasoning(text):
    """Merge a reasoning-only follow-up into the held order without reordering it."""
    pending = st.session_state.get("pending_reasoning")
    if not pending:
        return None

    held = deepcopy(pending.get("parsed") or {})
    normalized = re.sub(r"[^a-z]+", " ", str(text or "").lower()).strip()
    if normalized == REASONING_GATE_OVERRIDE:
        if "ACCOUNT_CONTEXT" in globals() and not faculty_access():
            return {"clarification": "Complete the requested reasoning to continue.", "missing": list(pending.get("missing") or [])}
        held["raw_text"] = (
            str(held.get("raw_text") or "").strip()
            + "\n\nFacilitator override: " + str(text).strip()
        ).strip()
        held["reasoning_gate"] = {
            "required": True,
            "status": "overridden",
            "missing": list(pending.get("missing") or []),
            "noted": reasoning_gate_noted(held),
        }
        _seal_reasoning(held, pending, "override")
        st.session_state.pending_reasoning = None
        clear_reasoning_gate_clarification()
        return {"parsed": held, "overridden": True}

    import reasoning_provenance

    supplemental = clinical_interpreter(text)
    merged_reasoning = deepcopy(held.get("reasoning", {}))
    provenance = dict(merged_reasoning.get("slot_provenance") or {})
    # A natural-language follow-up is primarily completing missing slots. Do
    # not let a bounded inference from the supplemental sentence overwrite a
    # field the learner already stated in the held turn.
    for key, value in deepcopy(supplemental.get("reasoning", {})).items():
        if key in ("slot_provenance", "derived_slots"):
            continue
        if not merged_reasoning.get(key):
            merged_reasoning[key] = value
            provenance[key] = reasoning_provenance.COMPLETED
    merged_reasoning["slot_provenance"] = provenance
    reasoning_provenance.mark(merged_reasoning, reasoning_provenance.COMPLETED)

    held_actions = deepcopy(held.get("actions", []))
    supplemental_reassessment = [
        a for a in supplemental.get("actions", []) if a.get("type") == "reassessment"
    ]
    if supplemental_reassessment:
        held_actions = [a for a in held_actions if a.get("type") != "reassessment"]
        held_actions.extend(deepcopy(supplemental_reassessment))

    held["reasoning"] = merged_reasoning
    held["actions"] = held_actions
    held["raw_text"] = (
        str(held.get("raw_text") or "").strip()
        + "\n\nReasoning clarification: " + str(text).strip()
    ).strip()
    held["recognized_future_actions"] = list(dict.fromkeys(
        list(held.get("recognized_future_actions", []) or [])
        + list(supplemental.get("recognized_future_actions", []) or [])
    ))
    known = {d.get("text") for d in held.get("future_details") or []}
    held["future_details"] = list(held.get("future_details") or []) + [
        d for d in supplemental.get("future_details") or [] if d.get("text") not in known]
    # "Control en policlinico en 48 horas", as the answer to a held discharge.
    from discharge_follow_up import adopt as adopt_discharge_follow_up
    adopt_discharge_follow_up(held)

    missing = reasoning_gate_missing(held)
    if missing:
        _rehold(held, pending, missing)
        return {"clarification": reasoning_gate_prompt(held, missing), "missing": missing}

    held["reasoning_gate"] = {"required": True, "status": "complete", "missing": [],
                              "noted": reasoning_gate_noted(held)}
    _seal_reasoning(held, pending, "free_text")
    st.session_state.pending_reasoning = None
    clear_reasoning_gate_clarification()
    return {"parsed": held, "overridden": False}

def classify_volume_state(ev):
    from clinical_physiology import invoke
    return invoke("classify_volume_state", (ev,), {}, rng, sim_time_label)


def fluid_responsiveness(ev):
    from clinical_physiology import invoke
    return invoke("fluid_responsiveness", (ev,), {}, rng, sim_time_label)


def update_fluid_phenotype(state):
    from clinical_physiology import invoke
    return invoke("update_fluid_phenotype", (state,), {}, rng, sim_time_label)

def fluid_intolerance_pressure(state, incoming_ml):
    from clinical_physiology import invoke
    return invoke("fluid_intolerance_pressure", (state, incoming_ml), {}, rng, sim_time_label)

def pulmonary_clinical_signal(state):
    from clinical_physiology import invoke
    return invoke("pulmonary_clinical_signal", (state,), {}, rng, sim_time_label)


def congestion_stage(congestion):
    from clinical_physiology import invoke
    return invoke("congestion_stage", (congestion,), {}, rng, sim_time_label)


def update_decompensation(state, added_fluid_ml=0, elapsed_min=0):
    from clinical_physiology import invoke
    return invoke("update_decompensation", (state, added_fluid_ml, elapsed_min), {}, rng, sim_time_label)


def total_beta_blockade(state):
    from clinical_physiology import invoke
    return invoke("total_beta_blockade", (state,), {}, rng, sim_time_label)


def beta_av_nodal_effect(state):
    from clinical_physiology import invoke
    return invoke("beta_av_nodal_effect", (state,), {}, rng, sim_time_label)


def beta_myocardial_depression(state):
    from clinical_physiology import invoke
    return invoke("beta_myocardial_depression", (state,), {}, rng, sim_time_label)


def total_av_nodal_suppression(state):
    from clinical_physiology import invoke
    return invoke("total_av_nodal_suppression", (state,), {}, rng, sim_time_label)


def af_substrate(state):
    from clinical_physiology import invoke
    return invoke("af_substrate", (state,), {}, rng, sim_time_label)


def af_ventricular_rate(state):
    from clinical_physiology import invoke
    return invoke("af_ventricular_rate", (state,), {}, rng, sim_time_label)


def advance_beta_pharmacodynamics(state, minutes=1):
    from clinical_physiology import invoke
    return invoke("advance_beta_pharmacodynamics", (state, minutes), {}, rng, sim_time_label)

        # Norepinephrine is represented as CURRENT exogenous vascular support.
        # Do not permanently accumulate it into endogenous vasomotor tone: doing so
        # creates hysteresis and makes down-titration unrealistically weak.
        # The current dose is applied centrally in recompute_coupled_physiology().

        # Oxygen support is represented in the treatment state. Final saturation
        # is generated by the central coupled physiology engine.


def update_dynamic_rhythm(state, minutes=1):
    from clinical_physiology import invoke
    return invoke("update_dynamic_rhythm", (state, minutes), {}, rng, sim_time_label)


def norepinephrine_normalized(state):
    from clinical_physiology import invoke
    return invoke("norepinephrine_normalized", (state,), {}, rng, sim_time_label)


def dobutamine_normalized(state):
    from clinical_physiology import invoke
    return invoke("dobutamine_normalized", (state,), {}, rng, sim_time_label)


def oxygen_support_fraction(state):
    from clinical_physiology import invoke
    return invoke("oxygen_support_fraction", (state,), {}, rng, sim_time_label)


def recompute_coupled_physiology(state, elapsed_min=1):
    from clinical_physiology import invoke
    return invoke("recompute_coupled_physiology", (state, elapsed_min), {}, rng, sim_time_label)


def update_perfusion_surface(state):
    from clinical_physiology import invoke
    return invoke("update_perfusion_surface", (state,), {}, rng, sim_time_label)


def apply_natural_disease(state, minutes):
    from clinical_physiology import invoke
    return invoke("apply_natural_disease", (state, minutes), {}, rng, sim_time_label)

def fluid_transition(state, volume_ml, fluid_type="Crystalloid", rate="standard"):
    from clinical_physiology import invoke
    return invoke("fluid_transition", (state, volume_ml, fluid_type, rate), {}, rng, sim_time_label)



def beta_blocker_transition(state, agent, dose_mg, route):
    from clinical_physiology import invoke
    return invoke("beta_blocker_transition", (state, agent, dose_mg, route), {}, rng, sim_time_label)


def diltiazem_transition(state, dose_mg, route):
    from clinical_physiology import invoke
    return invoke("diltiazem_transition", (state, dose_mg, route), {}, rng, sim_time_label)


def amiodarone_transition(state, dose_mg, route):
    from clinical_physiology import invoke
    return invoke("amiodarone_transition", (state, dose_mg, route), {}, rng, sim_time_label)


def _record_treatment_timing(state, key, operation="start"):
    from clinical_physiology import invoke
    return invoke("_record_treatment_timing", (state, key, operation), {}, rng, sim_time_label)


def _treatment_timing_suffix(state, key):
    from clinical_physiology import invoke
    return invoke("_treatment_timing_suffix", (state, key), {}, rng, sim_time_label)


def dobutamine_transition(state, rate, units="mcg/kg/min", operation="start"):
    from clinical_physiology import invoke
    return invoke("dobutamine_transition", (state, rate, units, operation), {}, rng, sim_time_label)


def norepinephrine_transition(state, rate, units, operation="start"):
    from clinical_physiology import invoke
    return invoke("norepinephrine_transition", (state, rate, units, operation), {}, rng, sim_time_label)


def furosemide_transition(state, dose_mg, route):
    from clinical_physiology import invoke
    return invoke("furosemide_transition", (state, dose_mg, route), {}, rng, sim_time_label)


def oxygen_transition(state, device, flow_lpm):
    from clinical_physiology import invoke
    return invoke("oxygen_transition", (state, device, flow_lpm), {}, rng, sim_time_label)



def nitroglycerin_transition(state, rate_mcg_min, operation="start"):
    from clinical_physiology import invoke
    return invoke("nitroglycerin_transition", (state, rate_mcg_min, operation), {}, rng, sim_time_label)


def niv_transition(state, mode, pressure_cmh2o, operation="start", ipap_cmh2o=None, epap_cmh2o=None, fio2_percent=None):
    from clinical_physiology import invoke
    return invoke("niv_transition", (state, mode, pressure_cmh2o, operation, ipap_cmh2o, epap_cmh2o, fio2_percent), {}, rng, sim_time_label)


def airway_preparation_transition(state):
    from clinical_physiology import invoke
    return invoke("airway_preparation_transition", (state,), {}, rng, sim_time_label)


def intubation_transition(state, ventilator_mode="VC/AC", fio2_percent=100.0, peep_cmh2o=8.0):
    from clinical_physiology import invoke
    return invoke("intubation_transition", (state, ventilator_mode, fio2_percent, peep_cmh2o), {}, rng, sim_time_label)


def ventilator_adjustment_transition(state, ventilator_mode=None, fio2_percent=None, peep_cmh2o=None):
    from clinical_physiology import invoke
    return invoke("ventilator_adjustment_transition", (state, ventilator_mode, fio2_percent, peep_cmh2o), {}, rng, sim_time_label)


def ventilator_continuation_transition(state):
    from clinical_physiology import invoke
    return invoke("ventilator_continuation_transition", (state,), {}, rng, sim_time_label)


def procedural_sedation_transition(state, medications):
    from clinical_physiology import invoke
    return invoke("procedural_sedation_transition", (state, medications), {}, rng, sim_time_label)


def cardioversion_transition(state, energy_j):
    from clinical_physiology import invoke
    return invoke("cardioversion_transition", (state, energy_j), {}, rng, sim_time_label)



def _diagnostic_timestamp(state, delay_min=0):
    from clinical_diagnostics import _diagnostic_timestamp as diagnostic
    return diagnostic(state, delay_min)


def pocus_transition(state, requested_delay_min=None):
    from clinical_diagnostics import pocus_transition as diagnostic
    return diagnostic(state, requested_delay_min)


def lactate_transition(state, requested_delay_min=None):
    from clinical_diagnostics import lactate_transition as diagnostic
    return diagnostic(state, requested_delay_min)


def vbg_transition(state, requested_delay_min=None):
    from clinical_diagnostics import vbg_transition as diagnostic
    return diagnostic(state, requested_delay_min)


def abg_transition(state, requested_delay_min=None):
    from clinical_diagnostics import abg_transition as diagnostic
    return diagnostic(state, requested_delay_min)


def basic_labs_transition(state):
    """Return a compact basic laboratory panel coherent with PS001's current illness."""
    h = state["hidden"]
    d = state.setdefault("diagnostics", {})
    perf = clamp(float(h.get("tissue_perfusion", 0.5)))
    inflammatory = clamp(float(h.get("inflammatory_drive", 0.0)))
    low_flow = clamp(float(h.get("low_flow_burden", 0.0)))
    fluid_ml = float(state.get("treatments", {}).get("cumulative_crystalloid_ml", 0) or 0)

    wbc = round(9.0 + 8.0 * inflammatory, 1)
    creat = round(1.0 + 0.9 * (1.0 - perf) + 0.5 * low_flow, 1)
    bicarb = int(round(max(14, 24 - 6.0 * (1.0 - perf) - 3.0 * low_flow)))
    sodium = int(round(138 - min(3.0, fluid_ml / 1200.0)))
    potassium = round(4.1 + 0.5 * low_flow, 1)
    glucose = int(round(145 + 45 * inflammatory))
    crp = round(12 + 138 * inflammatory, 1)
    hemoglobin = round(max(10.5, 13.8 - 0.0007 * fluid_ml), 1)
    platelets = int(round(245 - 45 * inflammatory))
    bun = int(round(18 + 17 * (1.0 - perf) + 8 * low_flow))

    result = {
        "time_min": _diagnostic_timestamp(state, 10),
        "wbc_k_ul": wbc,
        "hemoglobin_g_dl": hemoglobin,
        "platelets_k_ul": platelets,
        "sodium_mmol_l": sodium,
        "potassium_mmol_l": potassium,
        "bicarbonate_mmol_l": bicarb,
        "bun_mg_dl": bun,
        "creatinine_mg_dl": creat,
        "glucose_mg_dl": glucose,
        "crp_mg_l": crp,
    }
    d["basic_labs"] = result
    return {"duration_min": 10, "diagnostic_type": "basic_labs", "result": deepcopy(result)}



def disposition_transition(state, destination="ICU"):
    state["treatments"]["disposition"] = destination
    return {"duration_min": 0, "support_type": "disposition", "destination": destination, "operation": "admit"}

def temperature_transition(state):
    d = state.setdefault("diagnostics", {})
    result = {"time_min": _diagnostic_timestamp(state, 0),
              "temperature_c": round(float(state.get("observable", {}).get("temperature_c", 37.2)), 1)}
    d["temperature"] = result
    return {"duration_min": 0, "diagnostic_type": "temperature", "result": deepcopy(result)}

def poc_glucose_transition(state):
    d = state.setdefault("diagnostics", {})
    value = (d.get("basic_labs") or {}).get("glucose_mg_dl")
    if value is None:
        value = int(round(145 + 45 * clamp(float(state.get("hidden", {}).get("inflammatory_drive", 0.0)))))
    result = {"time_min": _diagnostic_timestamp(state, 0), "glucose_mg_dl": int(value)}
    d["poc_glucose"] = result
    return {"duration_min": 0, "diagnostic_type": "poc_glucose", "result": deepcopy(result)}

def focused_history_transition(state):
    d = state.setdefault("diagnostics", {})
    history = (
        "She reports feverishness and chills since last night with a new productive cough. "
        "No dysuria, flank pain, vomiting, melena, hematemesis, or obvious bleeding."
        if state.get("case_id") == "PS002"
        else (
            "He reports two days of dysuria and urinary frequency, followed by chills, poor oral intake, "
            "and progressive weakness today. He denies chest pain, gastrointestinal bleeding, vomiting, "
            "diarrhea, cough, or focal neurologic symptoms."
        )
    )
    result = {"time_min": _diagnostic_timestamp(state, 0), "history": history}
    d["focused_history"] = result
    return {"duration_min": 0, "diagnostic_type": "focused_history", "result": deepcopy(result)}

def chest_xray_transition(state):
    d = state.setdefault("diagnostics", {})
    congestion = float(state.get("hidden", {}).get("pulmonary_congestion", 0.0))
    if state.get("case_id") == "PS002":
        finding = ("Patchy right basilar airspace opacity with superimposed bilateral interstitial pulmonary edema."
                   if congestion >= 0.35 else
                   "Patchy right basilar airspace opacity suspicious for pneumonia; no pleural effusion or pneumothorax.")
    else:
        finding = "No focal airspace opacity, pleural effusion, or pneumothorax."
    result = {"time_min": _diagnostic_timestamp(state, 8), "finding": finding}
    d["chest_xray"] = result
    return {"duration_min": 8, "diagnostic_type": "chest_xray", "result": deepcopy(result)}

def urinalysis_transition(state):
    d = state.setdefault("diagnostics", {})
    finding = (
        "Negative nitrite, trace leukocyte esterase, 2–5 WBC/hpf; no strong evidence of a urinary source."
        if state.get("case_id") == "PS002"
        else "Positive nitrite and leukocyte esterase with >50 WBC/hpf and many bacteria, supporting a urinary source."
    )
    result = {"time_min": _diagnostic_timestamp(state, 7), "finding": finding}
    d["urinalysis"] = result
    return {"duration_min": 7, "diagnostic_type": "urinalysis", "result": deepcopy(result)}

def blood_cultures_transition(state):
    d = state.setdefault("diagnostics", {})
    result = {"time_min": _diagnostic_timestamp(state, 2),
              "finding": "Two sets of blood cultures collected; microbiology results are pending."}
    d["blood_cultures"] = result
    return {"duration_min": 2, "diagnostic_type": "blood_cultures", "result": deepcopy(result)}

def antibiotics_transition(state, agent="broad-spectrum antibiotics", dose_g=None, route=None):
    state["treatments"]["antibiotics"] = True
    return {"duration_min": 2, "support_type": "antibiotics",
            "agent_name": agent, "dose_g": dose_g, "route": route, "operation": "start"}


def format_diagnostic_summary(summary):
    dtype = summary.get("diagnostic_type")
    r = summary.get("result") or {}
    if r.get("report") or (st.session_state.get("state") or {}).get("engine_family"):
        from family_reports import format_result
        return format_result(dtype, r)
    if dtype == "pocus":
        from pocus_report import format_pocus
        return format_pocus(r)
    if dtype == "lactate":
        return f'Lactate: {r.get("value_mmol_l", 0):.1f} mmol/L.'
    if dtype == "vbg":
        return (
            f'VBG: pH {r.get("ph", 0):.2f}, pCO₂ {r.get("pco2_mm_hg")} mmHg, '
            f'HCO₃ {r.get("bicarbonate_mmol_l")} mmol/L, base excess '
            f'{r.get("base_excess_mmol_l"):+g} mmol/L, lactate {r.get("lactate_mmol_l", 0):.1f} mmol/L.'
        )
    if dtype == "abg":
        return (
            f'ABG: pH {r.get("ph", 0):.2f}, PaCO₂ {r.get("paco2_mm_hg")} mmHg, '
            f'PaO₂ {r.get("pao2_mm_hg")} mmHg, HCO₃ {r.get("bicarbonate_mmol_l")} mmol/L, '
            f'base excess {r.get("base_excess_mmol_l"):+g} mmol/L, FiO₂ '
            f'{r.get("fio2_percent", 21):g}%, P/F ratio {r.get("pf_ratio")}.'
        )
    if dtype == "basic_labs":
        return (
            f'Basic labs: WBC {r.get("wbc_k_ul")} K/µL, Hgb {r.get("hemoglobin_g_dl")} g/dL, '
            f'platelets {r.get("platelets_k_ul")} K/µL, Na {r.get("sodium_mmol_l")} mmol/L, '
            f'K {r.get("potassium_mmol_l")} mmol/L, HCO₃ {r.get("bicarbonate_mmol_l")} mmol/L, '
            f'BUN {r.get("bun_mg_dl")} mg/dL, creatinine {r.get("creatinine_mg_dl")} mg/dL, '
            f'glucose {r.get("glucose_mg_dl")} mg/dL, CRP {r.get("crp_mg_l")} mg/L.'
        )
    if dtype == "temperature":
        return f'Temperature: {r.get("temperature_c"):.1f} °C.'
    if dtype == "poc_glucose":
        return f'Point-of-care glucose: {r.get("glucose_mg_dl")} mg/dL.'
    if dtype == "focused_history":
        return "Focused history: " + str(r.get("history", ""))
    if dtype in {"chest_xray", "urinalysis", "blood_cultures"}:
        prefix = {"chest_xray":"Chest X-ray", "urinalysis":"Urinalysis", "blood_cultures":"Blood cultures"}[dtype]
        return prefix + ": " + str(r.get("finding", ""))
    return "Diagnostic result available."


def hold_pending_bundle(parsed, idx):
    """Pause one unresolved action slot without losing the original decision bundle."""
    st.session_state.pending_bundle = {
        "raw_text": parsed.get("raw_text", ""),
        "before": deepcopy(parsed.get("actions", [])[:idx]),
        "after": deepcopy(parsed.get("actions", [])[idx+1:]),
        "reasoning": deepcopy(parsed.get("reasoning", {})),
        "recognized_future_actions": deepcopy(parsed.get("recognized_future_actions", [])),
        "future_details": deepcopy(parsed.get("future_details", [])),
    }

def merge_pending_bundle(parsed):
    bundle = st.session_state.get("pending_bundle")
    if not bundle:
        return parsed
    merged = {
        "raw_text": bundle.get("raw_text") or parsed.get("raw_text", ""),
        "reasoning": deepcopy(bundle.get("reasoning", {})),
        "actions": deepcopy(bundle.get("before", [])) + deepcopy(parsed.get("actions", [])) + deepcopy(bundle.get("after", [])),
        "recognized_future_actions": deepcopy(bundle.get("recognized_future_actions", [])),
        "future_details": deepcopy(bundle.get("future_details", [])),
        "resolved_from_clarification": True,
    }
    st.session_state.pending_bundle = None
    return merged


def execute_bundle(parsed):
    # Nested so that regressions loading execute_bundle through ast keep its helpers.
    def _record_administration_time(res, action):
        """Keep a stated administration time on a medication summary.

        The legacy medication models keep their own onset kinetics; the stated time
        is recorded, shown, and advances the clock when no reassessment is given.
        """
        duration = action.get("administration_duration_min")
        if duration:
            res["administration_duration_min"] = duration
            res["duration_min"] = max(int(res.get("duration_min", 0) or 0), math.ceil(duration))

    def _start_timed_fluid(state, action):
        """Queue a crystalloid order to run evenly over its stated duration."""
        queue = state.setdefault("timed_fluids", [])
        now = int(state.get("sim_time", 0))
        # A second bag follows the one still running rather than doubling the rate.
        start = max([now] + [item["start"] + item["duration"] for item in queue])
        duration = float(action["administration_duration_min"])
        queue.append({"fluid_type": action["fluid_type"], "rate": action.get("rate", "standard"),
                      "volume_ml": float(action["volume_ml"]), "delivered_ml": 0.0,
                      "start": start, "duration": duration})
        return {
            "fluid_type": action["fluid_type"], "volume_ml": action["volume_ml"],
            "administration_duration_min": duration,
            "delivery_starts_at_min": start, "delivery_due_at_min": start + duration,
            "duration_min": math.ceil(start - now + duration),
            "cumulative_ml": state["treatments"]["cumulative_crystalloid_ml"],
        }


    def _advance_with_timed_fluids(state, elapsed):
        """Advance the clock, delivering any timed crystalloid minute by minute.

        Without a timed fluid the clock advances in one call, exactly as before. With
        one, each minute's share goes through the same fluid transition, counting the
        volume already given from that order so the saturating response adds up to
        the same whole-bag effect.
        """
        if not state.get("timed_fluids"):
            apply_natural_disease(state, elapsed)
            state["sim_time"] += elapsed
            return
        for _ in range(int(elapsed)):
            now = state["sim_time"] + 1
            for item in state["timed_fluids"]:
                target = item["volume_ml"] * min(1, max(0, (now - item["start"]) / item["duration"]))
                change = target - item["delivered_ml"]
                if change <= 0:
                    continue
                state["_fluid_delivery"] = {"before_ml": item["delivered_ml"]}
                try:
                    fluid_transition(state, change, item["fluid_type"], item["rate"])
                finally:
                    state.pop("_fluid_delivery", None)
                item["delivered_ml"] = target
            state["timed_fluids"] = [item for item in state["timed_fluids"]
                                     if item["delivered_ml"] < item["volume_ml"]]
            apply_natural_disease(state, 1)
            state["sim_time"] = now

    state = st.session_state.state
    if state.get("engine_family"):
        from family_engine import execute_family_bundle
        from pending_family_orders import hold_incomplete_bundle
        import weight_based_doses
        waiting = weight_based_doses.resolve(parsed, state)
        if waiting:
            # Asking the weight is the reader's question, not a clinical minute:
            # nothing runs and the clock does not move (faculty decision 2).
            st.session_state.pending_action = {"type": "family_bundle", "parsed": deepcopy(parsed),
                                               "index": waiting[0]}
            return {"executed": False, "action_summaries": [], "elapsed_min": 0,
                    "clarification": _held_order_prompt(parsed, weight_based_doses.WEIGHT_QUESTION)}
        result = execute_family_bundle(state, parsed)
        if result.get("executed"):
            weight_based_doses.remember(state, parsed)
        if not result.get("executed") and result.get("clarification"):
            result["clarification"] = _held_order_prompt(parsed, result["clarification"])
            pending = hold_incomplete_bundle(parsed, state)
            if pending:
                st.session_state.pending_action = pending
        return result

    # Keep the learner input available after collapse, but do not run ordinary
    # intervention/reassessment physiology as though spontaneous circulation persists.
    # Arrest-management actions are intentionally outside the scope of v0.5.6.1.
    if state["hidden"].get("terminal_collapse"):
        return {
            "executed": False,
            "terminal_locked": True,
            "action_summaries": [],
            "reassess_delay": None,
            "elapsed_min": 0,
        }

    if parsed.get("clarification"):
        return {"clarification": parsed["clarification"], "executed": False}

    summaries = []
    reassess_delay = None

    for idx, a in enumerate(parsed["actions"]):
        if a["type"] == "fluid" and a["volume_ml"] is None:
            st.session_state.pending_action = dict(a)
            hold_pending_bundle(parsed, idx)
            return {"clarification": "How much fluid would you like to give?", "executed": False}
        if a["type"] == "fluid" and not a.get("fluid_type"):
            st.session_state.pending_action = dict(a)
            hold_pending_bundle(parsed, idx)
            return {"clarification": "Which crystalloid would you like to give (for example, normal saline or LR)?", "executed": False}

        if a["type"] == "fluid" and a.get("volume_ml") is not None and a.get("volume_ml") > 3000:
            # Safety/parser guardrail: a very large crystalloid order is more likely to
            # represent a parsing/unit error than an intended single bolus. Never execute
            # it silently; require the learner to confirm/restate the amount.
            st.session_state.pending_action = dict(a)
            hold_pending_bundle(parsed, idx)
            return {"clarification": f'I understood {a.get("volume_ml")} mL of crystalloid. Please confirm or restate the intended volume.', "executed": False}

        if a["type"] == "procedural_sedation":
            missing_agents = [
                str(medication.get("agent") or "sedative")
                for medication in a.get("medications", []) or []
                if medication.get("dose") is None
            ]
            if missing_agents:
                st.session_state.pending_action = dict(a)
                hold_pending_bundle(parsed, idx)
                return {
                    "clarification": (
                        "What dose would you like to give for "
                        + " and ".join(missing_agents)
                        + "?"
                    ),
                    "executed": False,
                }

        if a["type"] == "cardioversion" and a.get("energy_j") is None:
            st.session_state.pending_action = dict(a)
            hold_pending_bundle(parsed, idx)
            return {"clarification": "What energy would you like to use (in joules)?", "executed": False}
        if a["type"] == "cardioversion" and state["observable"].get("rhythm") != "AF":
            return {
                "clarification": (
                    f'The current rhythm is {state["observable"].get("rhythm")}, not atrial fibrillation. '
                    "Synchronized cardioversion was not repeated; please specify a different action or reassessment."
                ),
                "executed": False,
            }

        if a["type"] == "beta_blocker":
            if a.get("dose_mg") is None:
                st.session_state.pending_action = dict(a)
                hold_pending_bundle(parsed, idx)
                return {"clarification": f'What dose of {a.get("agent")} would you like to give?', "executed": False}
            if a.get("route") is None:
                st.session_state.pending_action = dict(a)
                hold_pending_bundle(parsed, idx)
                return {"clarification": "What route would you like to use (IV or PO)?", "executed": False}

        if a["type"] in ["diltiazem", "amiodarone"]:
            if a.get("dose_mg") is None:
                st.session_state.pending_action = dict(a)
                hold_pending_bundle(parsed, idx)
                return {"clarification": f'What dose of {a["type"]} would you like to give?', "executed": False}
            if a.get("route") is None:
                st.session_state.pending_action = dict(a)
                hold_pending_bundle(parsed, idx)
                return {"clarification": "What route would you like to use (IV or PO)?", "executed": False}

        if a["type"] == "furosemide":
            if a.get("dose_mg") is None:
                st.session_state.pending_action = dict(a)
                hold_pending_bundle(parsed, idx)
                return {"clarification": "What dose of furosemide would you like to give?", "executed": False}
            if a.get("route") is None:
                st.session_state.pending_action = dict(a)
                hold_pending_bundle(parsed, idx)
                return {"clarification": "What route would you like to use (IV or PO)?", "executed": False}

        if a["type"] == "nitroglycerin" and a.get("operation") != "stop" and a.get("rate_mcg_min") is None:
            st.session_state.pending_action = dict(a)
            hold_pending_bundle(parsed, idx)
            return {"clarification": "What IV nitroglycerin infusion rate would you like to start (for example, 20 mcg/min)?", "executed": False}

        if a["type"] == "niv" and a.get("operation") != "stop":
            if state["treatments"].get("invasive_ventilation"):
                return {
                    "clarification": "The patient is currently intubated. Extubation or transition back to NIV is not executable in this build.",
                    "executed": False,
                }
            needs_bipap = a.get("mode") == "BiPAP" and (a.get("ipap_cmh2o") is None or a.get("epap_cmh2o") is None)
            needs_cpap = a.get("mode") != "BiPAP" and a.get("pressure_cmh2o") is None
            if needs_bipap or needs_cpap:
                st.session_state.pending_action = dict(a)
                hold_pending_bundle(parsed, idx)
                prompt = ("What BiPAP IPAP/EPAP would you like to use (for example, 16/8 cm H2O)?"
                          if a.get("mode") == "BiPAP"
                          else "What noninvasive ventilation pressure would you like to use (for example, CPAP 8 cm H2O or BiPAP 16/8)?")
                return {"clarification": prompt, "executed": False}

        if a["type"] == "airway_preparation" and state["treatments"].get("invasive_ventilation"):
            return {
                "clarification": (
                    "The patient is already intubated; airway preparation was not repeated. "
                    "Specify a ventilator adjustment or reassessment."
                ),
                "executed": False,
            }

        if a["type"] == "intubation" and state["treatments"].get("invasive_ventilation"):
            return {
                "clarification": (
                    "The patient is already intubated. Continue current invasive ventilation or specify new FiO2/PEEP settings."
                ),
                "executed": False,
            }

        if a["type"] in {"ventilator_adjustment", "ventilator_continuation"}:
            if not state["treatments"].get("invasive_ventilation"):
                return {
                    "clarification": "The patient is not currently intubated; specify the intended respiratory interface.",
                    "executed": False,
                }
            peep = float(a.get("peep_cmh2o") or 0.0)
            fio2 = float(a.get("fio2_percent") or 0.0)
            if not (0.0 <= peep <= 30.0):
                return {"clarification": "Please specify a PEEP between 0 and 30 cm H2O.", "executed": False}
            if not (21.0 <= fio2 <= 100.0):
                return {"clarification": "Please specify FiO2 between 21% and 100%.", "executed": False}

        if a["type"] == "dobutamine" and a.get("operation") != "stop":
            if a.get("rate") is None or a.get("units") != "mcg/kg/min":
                st.session_state.pending_action = dict(a)
                hold_pending_bundle(parsed, idx)
                return {"clarification": "What dobutamine dose would you like to use in mcg/kg/min (for example, 5 mcg/kg/min)?", "executed": False}
            if not (2.5 <= float(a.get("rate")) <= 20.0):
                st.session_state.pending_action = dict(a)
                hold_pending_bundle(parsed, idx)
                return {"clarification": "Please specify a dobutamine dose between 2.5 and 20 mcg/kg/min.", "executed": False}

        if a["type"] == "norepinephrine" and a.get("operation") != "stop" and a.get("rate") is None:
            st.session_state.pending_action = dict(a)
            hold_pending_bundle(parsed, idx)
            return {"clarification": "What norepinephrine infusion rate would you like to start (for example, 0.05 mcg/kg/min or 5 mcg/min)?", "executed": False}

        if a["type"] == "oxygen" and state["treatments"].get("invasive_ventilation"):
            return {
                "clarification": (
                    "The patient is currently receiving invasive ventilation. Conventional oxygen was not added; "
                    "specify a ventilator FiO2 adjustment or an explicit extubation plan."
                ),
                "executed": False,
            }

        if a["type"] == "oxygen" and (a.get("device") is None or a.get("flow_lpm") is None):
            st.session_state.pending_action = dict(a)
            hold_pending_bundle(parsed, idx)
            return {"clarification": "What oxygen device/flow would you like to use (for example, nasal cannula 4 L/min or non-rebreather mask)?", "executed": False}

        if (a["type"] == "disposition" and state["treatments"].get("disposition")
                == a.get("destination", "ICU")):
            return {
                "clarification": (
                    f'The patient is already admitted to {a.get("destination", "ICU")}; '
                    "the disposition was not repeated. Specify the next treatment or reassessment."
                ),
                "executed": False,
            }

    # Interventions in a single learner order begin at the same decision time.
    # Their onset/administration clocks overlap with the requested reassessment
    # interval instead of being serially added to it.
    max_action_duration = 0
    reassess_delay = None

    for a in parsed["actions"]:
        if a["type"] == "fluid_stop":
            remaining = sum(item["volume_ml"] - item["delivered_ml"] for item in state.get("timed_fluids", []))
            state["timed_fluids"] = []
            summaries.append({"label": (f"stopping crystalloid ({remaining:.0f} mL not given)" if remaining > 0
                                        else "withholding further fluid (none was running)"),
                              "duration_min": 0})
            continue

        if a["type"] == "fluid":
            if a.get("administration_duration_min"):
                res = _start_timed_fluid(state, a)
            else:
                res = fluid_transition(state, a["volume_ml"], a["fluid_type"], a["rate"])
            max_action_duration = max(max_action_duration, res["duration_min"])
            summaries.append(res)
            st.session_state.last_executed_action = {
                "type": "fluid",
                "fluid_type": a["fluid_type"],
                "volume_ml": a["volume_ml"],
                "rate": a["rate"],
            }

        elif a["type"] == "beta_blocker":
            res = beta_blocker_transition(state, a["agent"], a["dose_mg"], a["route"])
            _record_administration_time(res, a)
            max_action_duration = max(max_action_duration, res["duration_min"])
            summaries.append(res)
            st.session_state.last_executed_action = {
                "type": "beta_blocker",
                "agent": a["agent"],
                "dose_mg": a["dose_mg"],
                "route": a["route"],
            }

        elif a["type"] == "diltiazem":
            res = diltiazem_transition(state, a["dose_mg"], a["route"])
            _record_administration_time(res, a)
            max_action_duration = max(max_action_duration, res["duration_min"])
            summaries.append(res)
            st.session_state.last_executed_action = {
                "type": "diltiazem", "dose_mg": a["dose_mg"], "route": a["route"]
            }

        elif a["type"] == "amiodarone":
            res = amiodarone_transition(state, a["dose_mg"], a["route"])
            _record_administration_time(res, a)
            max_action_duration = max(max_action_duration, res["duration_min"])
            summaries.append(res)
            st.session_state.last_executed_action = {
                "type": "amiodarone", "dose_mg": a["dose_mg"], "route": a["route"]
            }

        elif a["type"] == "furosemide":
            res = furosemide_transition(state, a["dose_mg"], a["route"])
            _record_administration_time(res, a)
            max_action_duration = max(max_action_duration, res["duration_min"])
            summaries.append(res)
            st.session_state.last_executed_action = {
                "type": "furosemide", "dose_mg": a["dose_mg"], "route": a["route"]
            }

        elif a["type"] == "nitroglycerin":
            res = nitroglycerin_transition(
                state, a.get("rate_mcg_min"), a.get("operation", "start")
            )
            max_action_duration = max(max_action_duration, res["duration_min"])
            summaries.append(res)
            st.session_state.last_executed_action = {
                "type": "nitroglycerin",
                "rate_mcg_min": a.get("rate_mcg_min"),
                "operation": a.get("operation", "start"),
            }

        elif a["type"] == "niv":
            res = niv_transition(
                state, a.get("mode"), a.get("pressure_cmh2o"), a.get("operation", "start"),
                ipap_cmh2o=a.get("ipap_cmh2o"), epap_cmh2o=a.get("epap_cmh2o"),
                fio2_percent=a.get("fio2_percent")
            )
            max_action_duration = max(max_action_duration, res["duration_min"])
            summaries.append(res)
            st.session_state.last_executed_action = {
                "type": "niv",
                "mode": a.get("mode"),
                "pressure_cmh2o": a.get("pressure_cmh2o"),
                "operation": a.get("operation", "start"),
            }

        elif a["type"] == "airway_preparation":
            res = airway_preparation_transition(state)
            max_action_duration = max(max_action_duration, res["duration_min"])
            summaries.append(res)
            st.session_state.last_executed_action = {"type": "airway_preparation"}

        elif a["type"] == "intubation":
            res = intubation_transition(
                state,
                ventilator_mode=a.get("ventilator_mode", "VC/AC"),
                fio2_percent=a.get("fio2_percent", 100.0),
                peep_cmh2o=a.get("peep_cmh2o", 8.0),
            )
            max_action_duration = max(max_action_duration, res["duration_min"])
            summaries.append(res)
            st.session_state.last_executed_action = {
                "type": "intubation",
                "ventilator_mode": res.get("ventilator_mode"),
                "fio2_percent": res.get("fio2_percent"),
                "peep_cmh2o": res.get("peep_cmh2o"),
            }

        elif a["type"] == "ventilator_adjustment":
            res = ventilator_adjustment_transition(
                state,
                ventilator_mode=a.get("ventilator_mode"),
                fio2_percent=a.get("fio2_percent"),
                peep_cmh2o=a.get("peep_cmh2o"),
            )
            max_action_duration = max(max_action_duration, res["duration_min"])
            summaries.append(res)
            st.session_state.last_executed_action = {
                "type": "ventilator_adjustment",
                "ventilator_mode": res.get("ventilator_mode"),
                "fio2_percent": res.get("fio2_percent"),
                "peep_cmh2o": res.get("peep_cmh2o"),
            }

        elif a["type"] == "ventilator_continuation":
            res = ventilator_continuation_transition(state)
            summaries.append(res)
            st.session_state.last_executed_action = {
                "type": "ventilator_continuation",
                "ventilator_mode": res.get("ventilator_mode"),
                "fio2_percent": res.get("fio2_percent"),
                "peep_cmh2o": res.get("peep_cmh2o"),
            }

        elif a["type"] == "dobutamine":
            res = dobutamine_transition(
                state, a.get("rate", 5.0), a.get("units", "mcg/kg/min"), a.get("operation", "start")
            )
            max_action_duration = max(max_action_duration, res["duration_min"])
            summaries.append(res)
            st.session_state.last_executed_action = {
                "type": "dobutamine", "rate": res.get("rate"),
                "units": res.get("units"), "operation": res.get("operation", "start")
            }

        elif a["type"] == "norepinephrine":
            res = norepinephrine_transition(
                state, a.get("rate"), a.get("units"), a.get("operation", "start")
            )
            max_action_duration = max(max_action_duration, res["duration_min"])
            summaries.append(res)
            st.session_state.last_executed_action = {
                "type": "norepinephrine",
                "rate": a.get("rate"),
                "units": a.get("units"),
                "operation": a.get("operation", "start"),
            }

        elif a["type"] == "oxygen":
            res = oxygen_transition(state, a["device"], a["flow_lpm"])
            max_action_duration = max(max_action_duration, res["duration_min"])
            summaries.append(res)
            st.session_state.last_executed_action = {
                "type": "oxygen", "device": a["device"], "flow_lpm": a["flow_lpm"]
            }

        elif a["type"] == "procedural_sedation":
            res = procedural_sedation_transition(state, a.get("medications", []))
            max_action_duration = max(max_action_duration, res["duration_min"])
            summaries.append(res)
            st.session_state.last_executed_action = {
                "type": "procedural_sedation",
                "medications": deepcopy(res.get("medications", [])),
            }

        elif a["type"] == "cardioversion":
            res = cardioversion_transition(state, a["energy_j"])
            max_action_duration = max(max_action_duration, res["duration_min"])
            summaries.append(res)
            st.session_state.last_executed_action = {
                "type": "cardioversion", "energy_j": a["energy_j"]
            }

        elif a["type"] == "pocus":
            res = pocus_transition(state, a.get("requested_delay_min"))
            max_action_duration = max(max_action_duration, res["duration_min"])
            summaries.append(res)
            st.session_state.last_executed_action = {"type": "pocus"}

        elif a["type"] == "lactate":
            res = lactate_transition(state, a.get("requested_delay_min"))
            max_action_duration = max(max_action_duration, res["duration_min"])
            summaries.append(res)
            st.session_state.last_executed_action = {"type": "lactate"}

        elif a["type"] == "vbg":
            res = vbg_transition(state, a.get("requested_delay_min"))
            max_action_duration = max(max_action_duration, res["duration_min"])
            summaries.append(res)
            st.session_state.last_executed_action = {"type": "vbg"}

        elif a["type"] == "abg":
            res = abg_transition(state, a.get("requested_delay_min"))
            max_action_duration = max(max_action_duration, res["duration_min"])
            summaries.append(res)
            st.session_state.last_executed_action = {"type": "abg"}

        elif a["type"] == "basic_labs":
            res = basic_labs_transition(state)
            max_action_duration = max(max_action_duration, res["duration_min"])
            summaries.append(res)
            st.session_state.last_executed_action = {"type": "basic_labs"}

        elif a["type"] == "temperature":
            summaries.append(temperature_transition(state))
            st.session_state.last_executed_action = {"type": "temperature"}
        elif a["type"] == "poc_glucose":
            summaries.append(poc_glucose_transition(state))
            st.session_state.last_executed_action = {"type": "poc_glucose"}
        elif a["type"] == "focused_history":
            summaries.append(focused_history_transition(state))
            st.session_state.last_executed_action = {"type": "focused_history"}
        elif a["type"] == "chest_xray":
            res = chest_xray_transition(state); summaries.append(res)
            max_action_duration = max(max_action_duration, res["duration_min"])
            st.session_state.last_executed_action = {"type": "chest_xray"}
        elif a["type"] == "urinalysis":
            res = urinalysis_transition(state); summaries.append(res)
            max_action_duration = max(max_action_duration, res["duration_min"])
            st.session_state.last_executed_action = {"type": "urinalysis"}
        elif a["type"] == "blood_cultures":
            res = blood_cultures_transition(state); summaries.append(res)
            max_action_duration = max(max_action_duration, res["duration_min"])
            st.session_state.last_executed_action = {"type": "blood_cultures"}
        elif a["type"] == "antibiotics":
            res = antibiotics_transition(
                state, a.get("agent", "broad-spectrum antibiotics"),
                dose_g=a.get("dose_g"), route=a.get("route")
            )
            _record_administration_time(res, a)
            summaries.append(res); max_action_duration = max(max_action_duration, res["duration_min"])
            st.session_state.last_executed_action = {
                "type": "antibiotics", "agent": a.get("agent"),
                "dose_g": a.get("dose_g"), "route": a.get("route")
            }

        elif a["type"] == "disposition":
            res = disposition_transition(state, a.get("destination", "ICU"))
            summaries.append(res)
            st.session_state.last_executed_action = {"type": "disposition", "destination": a.get("destination", "ICU")}

        elif a["type"] == "reassessment":
            reassess_delay = a["delay_min"]

    # A learner-requested reassessment is an observation checkpoint, not extra time
    # added after an intervention. For treatment-only bundles, respect that explicit
    # checkpoint even when the order's nominal administration time is longer (for
    # example, "give 2000 mL and reassess in 5 minutes"). Diagnostic results still
    # cannot appear before their processing delay, so a diagnostic in the same bundle
    # may extend the elapsed interval. Without an explicit checkpoint, retain the
    # longest action duration as the default clock advance.
    diagnostic_duration = max(
        (
            int(summary.get("duration_min", 0) or 0)
            for summary in summaries
            if summary.get("diagnostic_type")
        ),
        default=0,
    )
    if reassess_delay is not None and reassess_delay > 0:
        elapsed = max(int(reassess_delay), diagnostic_duration)
    else:
        elapsed = max_action_duration

    if elapsed > 0:
        _advance_with_timed_fluids(state, elapsed)
    # When FiO2 alone is reduced, ongoing recruitment may still improve the
    # underlying lung state, but the learner-facing response must not imply that
    # lowering FiO2 directly raised saturation. Stability is allowed; an increase
    # requires a concurrent PEEP or mode change in the same order.
    for summary in summaries:
        if summary.get("support_type") != "invasive_ventilation" or summary.get("operation") != "adjust":
            continue
        fio2_reduced = float(summary.get("fio2_percent") or 0.0) < float(summary.get("old_fio2_percent") or 0.0)
        same_peep = float(summary.get("peep_cmh2o") or 0.0) == float(summary.get("old_peep_cmh2o") or 0.0)
        same_mode = summary.get("ventilator_mode") == summary.get("old_ventilator_mode")
        pre_spo2 = summary.get("pre_adjustment_spo2")
        if fio2_reduced and same_peep and same_mode and pre_spo2 is not None:
            state["observable"]["spo2"] = min(state["observable"].get("spo2", pre_spo2), pre_spo2)
    # Zero-time information and disposition actions do not alter physiology.

    return {
        "clarification": None,
        "executed": bool(summaries) or (reassess_delay is not None),
        "action_summaries": summaries,
        "reassess_delay": reassess_delay,
        "elapsed_min": elapsed,
    }

def _vitals_cells(snapshot):
    pulse_present = bool(snapshot.get("pulse_present", True))
    if pulse_present:
        bp = f'{snapshot.get("sbp")}/{snapshot.get("dbp")} · MAP {snapshot.get("map")}'
        spo2 = f'{snapshot.get("spo2")}% · {snapshot.get("respiratory_support")}'
        crt = "Not measured" if snapshot.get("crt") is None else f'{snapshot.get("crt")} s'
    else:
        bp = "No measurable BP"
        spo2 = "No reliable reading"
        crt = "Not measurable"

    rr = snapshot.get("respiratory_rate")
    wob = snapshot.get("work_of_breathing") or "—"
    rr_value = f'{rr}/min · {wob}' if rr is not None else wob
    extremities = snapshot.get("extremities") or "—"
    perfusion = f"{crt} · {extremities}"
    return (
        ("SIM TIME", sim_time_label(int(snapshot.get("sim_time_min", 0) or 0))),
        ("BP · MAP", bp),
        # Rate only: the resident reads the rhythm off the monitor trace and the
        # 12-lead. The snapshot still records it for the Management Trace.
        ("HR", f'{snapshot.get("hr", "—")}/min' if snapshot.get("hr") is not None else "—"),
        ("SpO₂ · SUPPORT", spo2),
        ("RR · WORK OF BREATHING", rr_value),
        ("CRT · EXTREMITIES", perfusion),
        ("MENTAL STATUS", snapshot.get("mental_status") or "—"),
    )


def _ecg_strip_svg(observable, duration_seconds=5.0):
    """Create a deterministic educational lead-II rhythm strip from visible state.

    The tracing is intentionally synthetic: it depicts only the rhythm, ventricular
    rate, and narrow-complex morphology already exposed to the learner. It does not
    invent axis, ischemia, chamber enlargement, or interval abnormalities.
    """
    try:
        hr = float(observable.get("hr") or 80.0)
    except (TypeError, ValueError):
        hr = 80.0
    if not math.isfinite(hr):
        hr = 80.0
    hr = max(20.0, min(240.0, hr))
    duration = max(3.0, min(8.0, float(duration_seconds)))
    rhythm = str(observable.get("rhythm") or "Unknown rhythm")
    normalized = rhythm.strip().lower()
    if normalized == "af":
        rhythm_key = "af"
    elif normalized == "sinus rhythm":
        rhythm_key = "sinus"
    elif normalized == "pea" or not observable.get("pulse_present", True):
        rhythm_key = "pea"
    else:
        rhythm_key = "organized"

    left, right, baseline = 22.0, 878.0, 108.0
    plot_width = right - left
    amplitude = 47.0
    mean_rr = 60.0 / hr

    beat_centers = []
    if rhythm_key == "af":
        beat_time = 0.10
        beat_index = 0
        while beat_time < duration + 0.45:
            variability = (
                0.95
                + 0.25 * math.sin((beat_index + 1) * 1.91 + hr * 0.013)
                + 0.12 * math.sin((beat_index + 1) * 0.73 + 0.4)
            )
            beat_time += mean_rr * max(0.62, min(1.38, variability))
            beat_centers.append(beat_time)
            beat_index += 1
    else:
        beat_time = 0.24
        while beat_time < duration + 0.45:
            beat_centers.append(beat_time)
            beat_time += mean_rr

    def gaussian(value, center, spread):
        return math.exp(-0.5 * ((value - center) / spread) ** 2)

    points = []
    samples = max(750, int(duration * 220))
    for index in range(samples + 1):
        t = duration * index / samples
        if rhythm_key == "af":
            signal = (
                0.042 * math.sin(2.0 * math.pi * 7.1 * t + 0.3)
                + 0.026 * math.sin(2.0 * math.pi * 9.3 * t + 1.1)
            )
        else:
            signal = 0.008 * math.sin(2.0 * math.pi * 0.33 * t)

        for center in beat_centers:
            relative = t - center
            if relative < -0.24 or relative > 0.48:
                continue
            if rhythm_key == "sinus":
                signal += 0.15 * gaussian(relative, -0.16, 0.032)
            signal += -0.12 * gaussian(relative, -0.019, 0.009)
            signal += 1.05 * gaussian(relative, 0.0, 0.010)
            signal += -0.30 * gaussian(relative, 0.024, 0.012)
            signal += (0.24 if rhythm_key == "af" else 0.31) * gaussian(relative, 0.19, 0.055)

        x = left + plot_width * t / duration
        y = baseline - amplitude * signal
        points.append(f"{x:.1f},{y:.1f}")

    path_data = "M " + " L ".join(points)
    grid_step = plot_width / (duration * 25.0)
    major_step = grid_step * 5.0
    id_suffix = f"{rhythm_key}-{int(round(hr))}"
    small_grid_id = f"mrs-ecg-small-{id_suffix}"
    grid_id = f"mrs-ecg-grid-{id_suffix}"
    # Describe the trace, never interpret it: a screen-reader user must read the
    # rhythm from the same evidence as everyone else.
    rate_label = f"approximately {int(round(hr))} complexes per minute"
    pulse_label = "" if observable.get("pulse_present", True) else " No palpable pulse is recorded."
    accessible_label = escape(f"Synthetic lead II rhythm strip at {rate_label}.{pulse_label}", quote=True)

    return f"""
    <div class="mrs-ecg-strip" data-rhythm="{escape(rhythm_key)}" data-rate="{int(round(hr))}">
      <svg viewBox="0 0 900 228" role="img" aria-label="{accessible_label}"
           preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <pattern id="{small_grid_id}" width="{grid_step:.3f}" height="{grid_step:.3f}" patternUnits="userSpaceOnUse">
            <path d="M {grid_step:.3f} 0 L 0 0 0 {grid_step:.3f}" fill="none" stroke="#f3d6d8" stroke-width="0.55"/>
          </pattern>
          <pattern id="{grid_id}" width="{major_step:.3f}" height="{major_step:.3f}" patternUnits="userSpaceOnUse">
            <rect width="{major_step:.3f}" height="{major_step:.3f}" fill="url(#{small_grid_id})"/>
            <path d="M {major_step:.3f} 0 L 0 0 0 {major_step:.3f}" fill="none" stroke="#ddaeb2" stroke-width="0.85"/>
          </pattern>
        </defs>
        <rect x="0.5" y="0.5" width="899" height="227" rx="10" fill="#fffdfd" stroke="#d9c3c5"/>
        <rect x="1" y="1" width="898" height="226" rx="10" fill="url(#{grid_id})"/>
        <text x="22" y="24" fill="#5b2328" font-family="system-ui, sans-serif" font-size="15" font-weight="700">II</text>
        <path d="M 26 196 h 11 v -36 h 31 v 36 h 11" fill="none" stroke="#722d35" stroke-width="2"/>
        <path d="{path_data}" fill="none" stroke="#18212b" stroke-width="2.15" stroke-linejoin="round" stroke-linecap="round"/>
        <text x="878" y="215" text-anchor="end" fill="#6f6062" font-family="system-ui, sans-serif" font-size="12">25 mm/s · 10 mm/mV · {duration:g} s</text>
      </svg>
    </div>
    <style>
      .mrs-ecg-strip {{ width: 100%; margin: .15rem 0 .35rem; }}
      .mrs-ecg-strip svg {{ display: block; width: 100%; height: auto; min-height: 145px; }}
    </style>
    """


def _vitals_grid_html(snapshot, variant="live"):
    import language
    cells = "".join(
        '<div class="mrs-vital-cell">'
        f'<div class="mrs-vital-label">{escape(str(label))}</div>'
        f'<div class="mrs-vital-value">{escape(str(value))}</div>'
        "</div>"
        for label, value in _vitals_cells(snapshot)
    )
    return f'<div class="mrs-vitals-grid mrs-vitals-grid--{escape(variant)}">{cells}</div>'


def current_status():
    """Render the current learner-visible state as an always-visible monitor."""
    snapshot = learner_vitals_snapshot(st.session_state.state)
    st.markdown(
        """
        <style>
        div[data-testid="stElementContainer"]:has(.mrs-persistent-monitor) {
            position: sticky;
            top: 3.35rem;
            z-index: 1000;
        }
        .mrs-persistent-monitor {
            border: 1px solid #9fb4c7;
            border-radius: 12px;
            background: rgba(247, 250, 252, 0.98);
            box-shadow: 0 6px 18px rgba(25, 45, 65, 0.13);
            padding: 10px 12px 12px;
            backdrop-filter: blur(8px);
        }
        .mrs-monitor-heading {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            margin: 0 2px 8px;
        }
        .mrs-monitor-title {
            color: #17324d;
            font-size: .78rem;
            font-weight: 800;
            letter-spacing: .065em;
            text-transform: uppercase;
        }
        .mrs-monitor-note {
            color: #5d6d7d;
            font-size: .76rem;
        }
        .mrs-vitals-grid {
            display: grid;
            grid-template-columns: .72fr 1fr 1.16fr 1.28fr 1.35fr 1.05fr 1fr;
            gap: 8px;
        }
        .mrs-vital-cell {
            min-width: 0;
            border-radius: 8px;
            background: #ffffff;
            padding: 8px 9px;
        }
        .mrs-vital-label {
            color: #667789;
            font-size: .63rem;
            font-weight: 800;
            letter-spacing: .045em;
            line-height: 1.2;
            text-transform: uppercase;
        }
        .mrs-vital-value {
            color: #172433;
            font-size: .91rem;
            font-weight: 700;
            line-height: 1.25;
            margin-top: 4px;
            overflow-wrap: anywhere;
        }
        .mrs-vitals-grid--response {
            grid-template-columns: repeat(4, minmax(0, 1fr));
            margin-top: 12px;
        }
        .mrs-vitals-grid--response .mrs-vital-cell {
            border: 1px solid #d7e0e8;
            background: #f7fafc;
        }
        @media (max-width: 1150px) {
            .mrs-vitals-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
        }
        @media (max-width: 760px) {
            div[data-testid="stElementContainer"]:has(.mrs-persistent-monitor) { top: 3rem; }
            .mrs-vitals-grid,
            .mrs-vitals-grid--response { grid-template-columns: repeat(2, minmax(0, 1fr)); }
            .mrs-monitor-note { display: none; }
        }
        </style>
        """
        + '<div class="mrs-persistent-monitor">'
        + '<div class="mrs-monitor-heading">'
        + '<span class="mrs-monitor-title">Live patient state</span>'
        + '<span class="mrs-monitor-note">Updates after each executed intervention</span>'
        + "</div>"
        + _vitals_grid_html(snapshot, variant="live")
        + "</div>",
        unsafe_allow_html=True,
    )


def respiratory_support_context(state, compact=False):
    tr = state["treatments"]
    if tr.get("invasive_ventilation"):
        mode = tr.get("ventilator_mode") or "VC/AC"
        fio2 = tr.get("ventilator_fio2_percent") or 40.0
        peep = tr.get("ventilator_peep_cmh2o") or 5.0
        label = f'{mode} · FiO₂ {fio2:g}% · PEEP {peep:g} cm H₂O'
        return label if compact else f'on invasive ventilation ({label})'
    if tr.get("niv"):
        fio2 = tr.get("niv_fio2_percent")
        fio = f' · FiO₂ {fio2:g}%' if fio2 is not None else ""
        if tr.get("niv_mode") == "BiPAP" and tr.get("niv_ipap_cmh2o") is not None and tr.get("niv_epap_cmh2o") is not None:
            label = f'BiPAP {tr.get("niv_ipap_cmh2o"):g}/{tr.get("niv_epap_cmh2o"):g} cm H₂O{fio}'
        else:
            label = f'{tr.get("niv_mode") or "NIV"} {tr.get("niv_pressure_cmh2o", 0):g} cm H₂O{fio}'
        return label if compact else f'on {label}'
    if tr.get("oxygen"):
        label = f'{tr.get("oxygen_device")} {tr.get("oxygen_flow_lpm"):g} L/min'
        return label if compact else f'on {label}'
    return "RA" if compact else "on room air"


def oxygen_context():
    return respiratory_support_context(st.session_state.state, compact=False)


def format_clinical_update():
    if st.session_state.state.get("engine_family"):
        from family_engine import clinical_update
        return clinical_update(st.session_state.state)
    o = st.session_state.state["observable"]
    h = st.session_state.state["hidden"]

    if h.get("cardiac_arrest"):
        return (
            "The patient becomes unresponsive. No palpable pulse is present. "
            f'The monitor shows organized electrical activity at approximately {o["hr"]}/min '
            "without a palpable pulse, consistent with PEA. "
            "There are no spontaneous respirations."
        )

    text = (
        f'BP is {o["sbp"]}/{o["dbp"]} mmHg, HR is {o["hr"]}/min, '
        f'capillary refill is approximately {o["crt"]} seconds, and the extremities are {o["extremities"].lower()}.'
    )

    stage = congestion_stage(pulmonary_clinical_signal(st.session_state.state))
    if stage == "none" and h.get("primary_respiratory_burden", 0.0) > 0:
        if o.get("work_of_breathing") == "Ventilator-supported":
            text += f' SpO₂ is {o["spo2"]}% {oxygen_context()}. Ventilator rate is {o["respiratory_rate"]}/min.'
        else:
            text += (
                f' SpO₂ is {o["spo2"]}% {oxygen_context()}. Respiratory rate is {o["respiratory_rate"]}/min '
                f'with {o["work_of_breathing"].lower()} work of breathing.'
            )
    elif stage == "early":
        text += (
            f' SpO₂ is {o["spo2"]}% {oxygen_context()}. Scattered new B-lines are present.'
        )
    elif stage == "moderate":
        text += (
            f' SpO₂ is {o["spo2"]}% {oxygen_context()}. Respiratory rate is {o["respiratory_rate"]}/min '
            f'with {o["work_of_breathing"].lower()} work of breathing. '
            "Bilateral B-lines and bibasilar crackles are present."
        )
    elif stage == "marked":
        text += (
            f' SpO₂ is {o["spo2"]}% {oxygen_context()}. Respiratory rate is {o["respiratory_rate"]}/min '
            f'with {o["work_of_breathing"].lower()} work of breathing. '
            "Diffuse bilateral B-lines and crackles are present."
        )

    # Always state mental status in reassessment text. In prior builds an Alert
    # patient silently lost the field, which made recovery look like missing data.
    text += f' Mental status: {o["mental_status"].lower()}.'

    return text

# Faculty decision 16 of 2026-09-21: the record is stored in English, which is
# the engine's canonical form, and presented in the reading language. The
# resident's own words and the authored narrative are never rewritten, so a
# sentence in one language is never spliced into a sentence in the other.
_TRANSLATED_EVENTS = frozenset({
    "clinical_update", "clarification", "procedure", "diagnostic_result",
    "prototype", "reasoning_note", "reasoning_completion", "study_not_performed",
})


def render_event(event):
    import language
    body = language.say(event["text"]) if event["kind"] in _TRANSLATED_EVENTS else event["text"]
    labels = {
        "patient_history": "PATIENT HISTORY",
        "examination": "EXAMINATION",
        "presentation": "INITIAL PRESENTATION",
        "you": "YOU",
        "reasoning_completion": "REASONING COMPLETION",
        "clinical_update": "CLINICAL UPDATE",
        "reasoning_note": "CONTEXT CHECK — DOES NOT BLOCK EXECUTION",
        "clarification": "CLARIFICATION",
        "prototype": "PROTOTYPE",
        "diagnostic_result": "DIAGNOSTIC RESULTS",
        "procedure": "PROCEDURE",
        # A study asked for that produces no result, with the reason in the text
        # (2026-09-24): recorded, never answered with an invented result.
        "study_not_performed": "STUDY REQUESTED",
    }
    if event["kind"] == "clinical_update":
        with st.container(border=True):
            st.markdown(f"**{language.say('PATIENT RESPONSE')} · {sim_time_label(event['time'])}**")
            st.write(body)
            snapshot = event.get("learner_vitals")
            if snapshot:
                st.markdown(_vitals_grid_html(snapshot, variant="response"), unsafe_allow_html=True)
        return
    st.markdown(f"**{language.say(labels.get(event['kind'], event['kind'].upper()))} · {sim_time_label(event['time'])}**")
    # A structured report such as POCUS uses one line per section; markdown would
    # otherwise run the lines together.
    st.write(str(body).replace("\n", "  \n"))

def _language_selector():
    """Choose the language the encounter is presented in.

    It changes nothing but the presentation: the same stored encounter is shown
    again, with the same numbers, doses, times and drug names (faculty decision
    16, 2026-09-21). Writing an order in Spanish does not move it.
    """
    if not (st.session_state.get("_shared_access_granted") or globals().get("ACCOUNT_CONTEXT")):
        # Nothing but the password belongs on the access screen.
        return
    import language
    options = list(language.LANGUAGES)
    if st.session_state.get("presentation_language") not in options:
        st.session_state["presentation_language"] = language.configured()
    st.sidebar.selectbox(
        "Idioma · Language", options, key="presentation_language",
        format_func=lambda code: language.LANGUAGES[code],
        help="Presentation only. Orders are read in Spanish and English either way.",
    )


_language_selector()
st.caption(f"Management Reasoning Simulator · Clinical encounter v{SIMULATOR_VERSION.split('-')[0]}")
if faculty_access():
    st.caption("AI language interpretation is active." if ai_language_interpretation_enabled() else "Local language interpretation is active.")

if not st.session_state.started:
    if ACCOUNT_CONTEXT:
        render_dashboard(ACCOUNT_CONTEXT, INITIAL_STATE, reset_session)
        st.stop()
    st.subheader("Choose a clinical problem")
    from cognitive_catalog import BIAS_CHALLENGES
    problem_ids = list(BIAS_CHALLENGES) + [key for key in CHALLENGES if key not in BIAS_CHALLENGES]
    previous_problem = st.session_state.get("selected_case")
    selected = st.selectbox(
        "Clinical problem", problem_ids,
        index=problem_ids.index(previous_problem) if previous_problem in problem_ids else 0,
        format_func=lambda key: key + " · " + CHALLENGES[key]["title"],
        label_visibility="collapsed",
    )
    st.session_state.selected_case = selected
    st.write(
        "You are the treating clinician. Manage the patient as you normally would. "
        "Ask for information, order tests, perform interventions, and reassess as the case evolves."
    )
    if st.button("Begin Encounter", type="primary"):
        cfg = generate_problem_config(selected)
        st.session_state.state = cfg["state_factory"]()
        st.session_state.events = []
        st.session_state.history = []
        st.session_state.management_trace = []
        st.session_state.encounter_ended = False
        st.session_state.encounter_closed_trace = None
        st.session_state.encounter_closed_events = None
        st.session_state.encounter_closed_state = None
        st.session_state.encounter_closed_time_min = None
        st.session_state.review_prompts = []
        st.session_state.decision_review = {}
        st.session_state.adaptation_plan = {}
        st.session_state.adaptation_plan_user_edited = {}
        st.session_state.review_completed = False
        st.session_state.review_stage = "decision"
        st.session_state.active_review_index = 0
        st.session_state.active_comparison_index = 0
        st.session_state.review_autosave_revision = 0
        st.session_state.expert_comparison_unlocked = False
        st.session_state.precomparison_decision_review = {}
        st.session_state.expert_comparison_responses = {}
        st.session_state.attempt_number = 1
        st.session_state.carry_forward_plan = {}
        st.session_state.prior_attempt_summary = None
        st.session_state.prior_attempt_record = None
        st.session_state.last_parse = None
        st.session_state.rng_counter = 0
        st.session_state.pending_action = None
        st.session_state.pending_bundle = None
        st.session_state.pending_reasoning = None
        st.session_state.last_executed_action = None
        st.session_state.started = True
        import arrival_brief
        add_event("presentation",
                  cfg["presentation"] + arrival_brief.handover(st.session_state.state), 0)
        rerun_app()
    st.stop()

if ACCOUNT_CONTEXT and st.session_state.get("_attempt_status") == "completed":
    st.subheader("Completed encounter review")
    st.caption("This saved review is read-only. Start a new encounter to apply your Adaptation Plan.")
    render_learning_focus(ACCOUNT_CONTEXT)
    frozen_trace = st.session_state.get("encounter_closed_trace") or []
    frozen_state = st.session_state.get("encounter_closed_state") or {}
    # The answer about help received can be given or changed after the review
    # is locked: it lives beside the record, not inside it.
    import language
    from assistance_portal import render_closing_question
    render_closing_question(ACCOUNT_CONTEXT, st.session_state.get("_attempt_id"), frozen_trace,
                            language=language.current())
    _render_analyzed_management_trace()
    with st.expander("Original decision-by-decision record", expanded=False):
        render_management_trace(frozen_trace)
    prompts = st.session_state.get("review_prompts") or []
    responses = st.session_state.get("precomparison_decision_review") or st.session_state.get("decision_review") or {}
    models = _expert_models_for_prompts(frozen_state.get("case_id"), prompts, frozen_trace)
    for prompt in prompts:
        with st.expander(_review_heading(prompt)):
            st.write(prompt.get("prompt", ""))
            for field, label in REVIEW_RESPONSE_FIELDS:
                st.markdown("**" + label + "**")
                st.write((responses.get(prompt["review_id"]) or {}).get(field, ""))
            model = models.get(prompt["review_id"]) or {}
            if model:
                st.markdown("**Expert comparison · faculty-validation draft**")
                for field in ("framing", "priority", "action", "tradeoff", "reassessment"):
                    st.write(str(model.get(field) or ""))
                for field, label in EXPERT_COMPARISON_FIELDS:
                    st.markdown("**" + label + "**")
                    st.write(((st.session_state.get("expert_comparison_responses") or {}).get(prompt["review_id"]) or {}).get(field, ""))
    plan = st.session_state.get("adaptation_plan") or {}
    st.subheader("Your Adaptation Plan")
    for field, label in ADAPTATION_PLAN_FIELDS:
        st.write(label + ": " + str(plan.get(field) or ""))
    payload = _render_export_controls(
        frozen_trace, frozen_state, prompts, responses, plan,
        st.session_state.get("expert_comparison_responses") or {}, True, "saved",
    )
    if st.button("Next Encounter with This Adaptation Plan", type="primary"):
        begin_repeat_encounter(plan, payload)
        rerun_app()
    if st.button("Return to dashboard"):
        return_to_dashboard(ACCOUNT_CONTEXT, reset_session)
    st.stop()

if not st.session_state.encounter_ended:
    render_room(st.session_state.state, st.session_state.events, _ecg_strip_svg, render_event, sim_time_label(st.session_state.state["sim_time"]))
with st.container(key="encounter-console"):
    if render_bedside_tools(st.session_state.state, st.session_state.events, render_event) and ACCOUNT_CONTEXT:
        save_session(ACCOUNT_CONTEXT)
    encounter_mode = st.radio("Encounter", ["Talk", "Examine", "Tests", "Treat"], index=3, horizontal=True, label_visibility="collapsed")
    st.caption("Act · anticipate the response · reassess")
    orders_panel = st.container()
    from clinical_scene import history_facts, answer_history, associated_symptoms, history_topics, history_topic_facts, setting as scene_setting
    if encounter_mode == "Talk" and not st.session_state.encounter_ended:
        clinical_case = st.session_state.state.get("encounter_spec", {}).get("clinical_case", {})
        history_source = clinical_case.get("history_source")
        has_collateral = bool(history_source and str(history_source).strip().lower() not in {"patient", "the patient"})
        cannot_speak = str(st.session_state.state['observable'].get('mental_status', '')).lower() in {'unresponsive', 'obtunded', 'sedated'}
        if cannot_speak and not has_collateral:
            st.info('The patient cannot provide a history at present. Review the history already obtained in the clinical chart.')
        else:
            if history_source:
                st.caption("History source: " + str(history_source))
            if cannot_speak:
                st.info("The patient cannot answer at present. Questions are directed to the available collateral source.")
            presentation = next((e["text"] for e in st.session_state.events if e["kind"] == "presentation"), "")
            facts = history_facts(presentation, st.session_state.state.get("case_id"), state=st.session_state.state)
            with st.form("patient_conversation"):
                question = st.text_input("Ask the available history source" if cannot_speak else "Ask the patient", placeholder="What brought you in today?")
                ask_patient = st.form_submit_button("Ask")
            if ask_patient and question.strip():
                answer = answer_history(question, facts, scene_setting("OPENAI_API_KEY"), state=st.session_state.state)
                add_event("you", question)
                add_event("patient_history", answer)
                import clinical_time as _clock
                spend_clinical_time(_clock.ACTIVE_MINUTES["history_question"],
                                    activity="history_question", request=question, response=answer)
                rerun_app()
            with st.expander("History topics"):
                case_topics = history_topics(st.session_state.state)
                topic = st.selectbox("Explore", case_topics or ["Presenting symptoms and onset", "Associated symptoms", "Previous health"])
                if st.button("Ask about this topic"):
                    if case_topics:
                        response = " ".join(history_topic_facts(st.session_state.state, topic))
                    elif topic == "Associated symptoms":
                        response = associated_symptoms(facts)
                    elif topic == "Previous health":
                        response = "Hypertension." if st.session_state.state.get("case_id") == "PS002" else "Hypertension and type 2 diabetes."
                    else:
                        response = " ".join(f for f in facts if not f.startswith(("I ", "It has burned")))
                    add_event("you", "Ask about " + topic.lower())
                    add_event("patient_history", response)
                    import clinical_time as _clock
                    spend_clinical_time(_clock.ACTIVE_MINUTES["history_question"],
                                        activity="history_question",
                                        request="Ask about " + topic.lower(), response=response)
                    rerun_app()
    # Like talking and treating, examining ends with the encounter: after the
    # close it added a decision to the saved record and moved the clinical
    # clock, and with it the closing minute the rubric's screening reads.
    if encounter_mode == "Examine" and not st.session_state.encounter_ended:
        family_findings = {}
        if st.session_state.state.get("engine_family"):
            from family_engine import current_findings
            family_findings = current_findings(st.session_state.state)
        area = st.selectbox("Examine", list(dict.fromkeys(["General appearance", "Breathing", "Peripheral perfusion"] + list(family_findings))))
        if st.button("Examine patient"):
            observed = st.session_state.state["observable"]
            if st.session_state.state.get("engine_family"):
                from family_engine import examination_finding
                finding = examination_finding(st.session_state.state, area)
            elif area == "General appearance":
                from patient_appearance import appearance_summary
                finding = appearance_summary(st.session_state.state)
            elif area in family_findings:
                finding = family_findings[area]
            elif area == "Breathing":
                finding = "Respiratory rate: " + str(observed.get("respiratory_rate", "—")) + "/min. Work of breathing: " + str(observed.get("work_of_breathing", "Not documented"))
            elif not observed.get("pulse_present", True):
                finding = "Pulse absent. Capillary refill is not measurable."
            else:
                finding = "Capillary refill: " + str(observed.get("crt", "—")) + " s. Extremities: " + str(observed.get("extremities", "Not documented"))
            add_event("you", "Examine: " + area)
            add_event("examination", finding)
            import clinical_time as _clock
            spend_clinical_time(_clock.examination_minutes([area]),
                                activity="examination", request="Examine: " + area,
                                response=finding)
            rerun_app()

    carry_forward_plan = st.session_state.get("carry_forward_plan", {}) or {}
    attempt_number = max(1, int(st.session_state.get("attempt_number", 1)))
    if attempt_number > 1 and any(
        str(carry_forward_plan.get(field) or "").strip() for field, _ in ADAPTATION_PLAN_FIELDS
    ):
        st.markdown(f"### Attempt {attempt_number} · Carry-Forward Learning Goal")
        st.caption(
            "This prospective plan came from the previous attempt. Use it as an intention for action and "
            "reassessment; the new Management Trace records only what you actually do now."
        )
        with st.container(border=True):
            cue_col, priority_col, target_col = st.columns(3)
            with cue_col:
                st.markdown("**Clinical cue to watch**")
                st.write(carry_forward_plan.get("cue") or "—")
                st.markdown("**Threshold for changing course**")
                st.write(carry_forward_plan.get("threshold") or "—")
            with priority_col:
                st.markdown("**Next management priority**")
                st.write(carry_forward_plan.get("next_priority") or "—")
                st.markdown("**Alternative action**")
                st.write(carry_forward_plan.get("alternative_action") or "—")
            with target_col:
                st.markdown("**Expected effect**")
                st.write(carry_forward_plan.get("expected_effect") or "—")
                st.markdown("**Reassessment target and timing**")
                st.write(carry_forward_plan.get("reassessment_plan") or "—")
        prior_attempt_record = st.session_state.get("prior_attempt_record") or {}
        if prior_attempt_record:
            prior_cycle = prior_attempt_record.get("learning_cycle", {}) or {}
            prior_number = max(1, int(prior_cycle.get("attempt_number", attempt_number - 1) or 1))
            prior_case = str((prior_attempt_record.get("encounter", {}) or {}).get("case_id") or "encounter").lower()
            prior_info, prior_pdf, prior_md, prior_json = st.columns([1.9, 1, 1, 1])
            with prior_info:
                st.markdown(f"**Previous attempt record · Attempt {prior_number}**")
                st.caption("The completed prior trajectory remains separate and available for download.")
            with prior_pdf:
                st.download_button(
                    "Previous PDF",
                    data=_review_pdf(prior_attempt_record),
                    file_name=f"{prior_case}_attempt_{prior_number}_review_v0819.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key=f"previous_pdf_{prior_number}",
                )
            with prior_md:
                st.download_button(
                    "Previous Markdown",
                    data=_review_markdown(prior_attempt_record),
                    file_name=f"{prior_case}_attempt_{prior_number}_review_v0819.md",
                    mime="text/markdown",
                    use_container_width=True,
                    key=f"previous_markdown_{prior_number}",
                )
            with prior_json:
                st.download_button(
                    "Previous JSON",
                    data=_review_json(prior_attempt_record),
                    file_name=f"{prior_case}_attempt_{prior_number}_review_v0819.json",
                    mime="application/json",
                    use_container_width=True,
                    key=f"previous_json_{prior_number}",
                )
    st.divider()

    with st.expander("Clinical chart · examination · results · treatment record", expanded=False):
        left, right = st.columns([2, 1])

        with left:
            render_encounter_workspace(st.session_state.events, render_event)

        with right:
            st.subheader("At the bedside")
            o = st.session_state.state["observable"]
            h = st.session_state.state["hidden"]
            with st.expander("Vitals", expanded=True):
                # Naming the rhythm here does the resident's interpretation for
                # them. The bedside waveform and the 12-lead are where it is read.
                if not o.get("pulse_present", True):
                    import language as _lang
                    st.write(_lang.say("BP: no measurable blood pressure"))
                    st.write(_lang.say(f'Monitor: organized electrical activity at {o["hr"]}/min, no palpable pulse'))
                    st.write(_lang.say("SpO₂: no reliable reading"))
                    st.write(_lang.say("CRT: not measurable"))
                else:
                    import language as _lang
                    st.write(_lang.say(f'BP: {o["sbp"]}/{o["dbp"]} mmHg'))
                    st.write(_lang.say(f'HR: {o["hr"]}/min'))
                    st.write(_lang.say(f'SpO₂: {o["spo2"]}%'))
                    st.write(_lang.say(f'CRT: {o["crt"]} s'))
            with st.expander("ECG", expanded=False):
                st.caption("Acquire and compare 12-lead tracings using ECG above.")

            for pending_study in st.session_state.state.get("pending_investigations", []):
                from family_reports import TEST_LABELS
                st.caption(f"{TEST_LABELS.get(pending_study['diagnostic_type'], pending_study['diagnostic_type'])}: pending · expected at {pending_study['available_at_min']} min")
            diagnostics = st.session_state.state.get("diagnostics", {}) or {}
            if st.session_state.state.get("engine_family") and diagnostics:
                from family_reports import TEST_LABELS, format_result
                with st.expander("Diagnostics", expanded=True):
                    for test_id, result in diagnostics.items():
                        if not isinstance(result, dict):
                            continue
                        import language as _lang
                        st.markdown(_lang.say(_patient_diagnostic_heading(TEST_LABELS.get(test_id, "Investigation"), result)))
                        st.write(_lang.say(format_result(test_id, result)).replace("\n", "  \n"))
            elif any(diagnostics.get(k) for k in ["pocus", "lactate", "vbg", "abg", "basic_labs"]):
                with st.expander("Diagnostics", expanded=True):
                    p = diagnostics.get("pocus")
                    if p:
                        st.markdown(_patient_diagnostic_heading("POCUS", p))
                        st.write(p.get("lv"))
                        st.write(p.get("rv"))
                        st.write(p.get("pericardium"))
                        st.write(p.get("ivc"))
                        st.write(p.get("lungs"))
                    lac = diagnostics.get("lactate")
                    if lac:
                        st.markdown(_patient_diagnostic_heading("Lactate", lac))
                        st.write(f'{lac.get("value_mmol_l"):.1f} mmol/L')
                    vbg = diagnostics.get("vbg")
                    if vbg:
                        st.markdown(_patient_diagnostic_heading("VBG", vbg))
                        st.write(
                            f'pH {vbg.get("ph"):.2f} · pCO₂ {vbg.get("pco2_mm_hg")} mmHg · '
                            f'HCO₃ {vbg.get("bicarbonate_mmol_l")} mmol/L · '
                            f'Base excess {vbg.get("base_excess_mmol_l"):+g} mmol/L · '
                            f'Lactate {vbg.get("lactate_mmol_l"):.1f} mmol/L'
                        )
                    abg = diagnostics.get("abg")
                    if abg:
                        st.markdown(_patient_diagnostic_heading("ABG", abg))
                        st.write(
                            f'pH {abg.get("ph"):.2f} · PaCO₂ {abg.get("paco2_mm_hg")} mmHg · '
                            f'PaO₂ {abg.get("pao2_mm_hg")} mmHg · HCO₃ '
                            f'{abg.get("bicarbonate_mmol_l")} mmol/L · Base excess '
                            f'{abg.get("base_excess_mmol_l"):+g} mmol/L · FiO₂ '
                            f'{abg.get("fio2_percent"):g}% · P/F ratio {abg.get("pf_ratio")}'
                        )
                    labs = diagnostics.get("basic_labs")
                    if labs:
                        st.markdown(_patient_diagnostic_heading("Basic laboratory tests", labs))
                        st.write(
                            f'WBC {labs.get("wbc_k_ul")} K/µL · Hgb {labs.get("hemoglobin_g_dl")} g/dL · '
                            f'Plt {labs.get("platelets_k_ul")} K/µL'
                        )
                        st.write(
                            f'Na {labs.get("sodium_mmol_l")} · K {labs.get("potassium_mmol_l")} · '
                            f'HCO₃ {labs.get("bicarbonate_mmol_l")} mmol/L'
                        )
                        st.write(
                            f'BUN {labs.get("bun_mg_dl")} mg/dL · Cr {labs.get("creatinine_mg_dl")} mg/dL · '
                            f'Glucose {labs.get("glucose_mg_dl")} mg/dL'
                        )

            with st.expander("Respiratory examination", expanded=True):
                if not o.get("pulse_present", True):
                    st.write("SpO₂: no reliable reading")
                    st.write("Respirations: absent")
                else:
                    st.write(f'SpO₂: {o["spo2"]}%')
                    st.write(f'Respiratory rate: {o.get("respiratory_rate", 22)}/min')
                    st.write(f'Work of breathing: {o.get("work_of_breathing", "Mildly increased")}')
                stage = "family" if st.session_state.state.get("engine_family") else congestion_stage(pulmonary_clinical_signal(st.session_state.state))
                if stage == "family":
                    from family_engine import current_findings
                    st.write(current_findings(st.session_state.state).get("Respiratory", "No additional examination finding recorded."))
                if stage == "none":
                    st.write("Lungs: no new congestion findings")
                elif stage == "early":
                    st.write("Lungs: scattered new B-lines")
                elif stage == "moderate":
                    st.write("Lungs: bilateral B-lines with bibasilar crackles")
                elif stage != "family":
                    st.write("Lungs: diffuse bilateral B-lines and crackles")

            with st.expander("Current treatments", expanded=True):
                tr = st.session_state.state["treatments"]
                if st.session_state.state.get("engine_family"):
                    if tr.get("packed_red_cells_units"):
                        from family_reports import format_transfusion
                        st.write(format_transfusion(tr["packed_red_cells_units"],
                                                    st.session_state.state.get("family_state", {}).get("pending_blood_units", 0)))
                    for medication in tr.get("administered_medications", []):
                        from family_reports import format_administration
                        st.write(format_administration(medication))
                    if tr.get("bag_mask"):
                        st.write("Bag-mask assisted ventilation")
                st.write(f'Cumulative crystalloid: {float(tr["cumulative_crystalloid_ml"]):.0f} mL')
                remaining = st.session_state.state.get('family_state', {}).get('pending_fluid_ml', 0)
                timed_deliveries = (st.session_state.state.get('generated_state', {}).get('native_deliveries', [])
                                    + st.session_state.state.get('family_state', {}).get('deliveries', []))
                for delivery in timed_deliveries:
                    if delivery.get('key', [None])[0] == 'fluid':
                        st.write(f"Fluid order: {delivery['amount']:g} mL over {delivery['duration']:g} min; delivered {delivery['delivered']:.0f} mL.")
                # Float residue from paced delivery (1e-13 mL) is not volume still to run.
                if remaining >= .5:
                    st.write(f'Crystalloid pending: {remaining:.0f} mL. Delivery continues as simulation time advances.')
                if st.session_state.state.get('engine_family') == 'generated':
                    st.caption('Orders and tests do not automatically wait for completion. Specify a reassessment interval to advance time.')
                if tr["metoprolol_total_mg"] > 0:
                    st.write(f'Metoprolol: {tr["metoprolol_total_mg"]:g} mg total')
                if tr["propranolol_total_mg"] > 0:
                    st.write(f'Propranolol: {tr["propranolol_total_mg"]:g} mg total')
                if tr["diltiazem_total_mg"] > 0:
                    st.write(f'Diltiazem: {tr["diltiazem_total_mg"]:g} mg total')
                if tr["amiodarone_total_mg"] > 0:
                    st.write(f'Amiodarone: {tr["amiodarone_total_mg"]:g} mg total')
                if tr.get("procedural_sedations", 0) > 0:
                    sedatives = []
                    if tr.get("etomidate_total_mg", 0) > 0:
                        sedatives.append(f'Etomidate {tr["etomidate_total_mg"]:g} mg total')
                    if tr.get("midazolam_total_mg", 0) > 0:
                        sedatives.append(f'Midazolam {tr["midazolam_total_mg"]:g} mg total')
                    st.write(
                        "Procedural sedation administered: "
                        + " + ".join(sedatives)
                        + _treatment_timing_suffix(st.session_state.state, "procedural_sedation")
                    )
                if tr.get("norepinephrine"):
                    st.write(
                        f'Norepinephrine: {tr["norepinephrine_rate"]:g} {tr["norepinephrine_units"]}'
                        + _treatment_timing_suffix(st.session_state.state, "norepinephrine")
                    )
                if tr.get("dobutamine"):
                    st.write(
                        f'Dobutamine: {tr["dobutamine_rate"]:g} mcg/kg/min'
                        + _treatment_timing_suffix(st.session_state.state, "dobutamine")
                    )
                if tr.get("furosemide_total_mg", 0) > 0:
                    st.write(f'Furosemide administered: {tr["furosemide_total_mg"]:g} mg total')
                if tr.get("oxygen"):
                    st.write(
                        f'Oxygen: {tr["oxygen_device"]} at {tr["oxygen_flow_lpm"]:g} L/min'
                        + _treatment_timing_suffix(st.session_state.state, "oxygen")
                    )
                if tr.get("nitroglycerin"):
                    st.write(
                        f'Nitroglycerin: {tr["nitroglycerin_rate_mcg_min"]:g} mcg/min'
                        + _treatment_timing_suffix(st.session_state.state, "nitroglycerin")
                    )
                if tr.get("niv"):
                    if tr.get("niv_mode") == "BiPAP" and tr.get("niv_ipap_cmh2o") is not None and tr.get("niv_epap_cmh2o") is not None:
                        fio = f' · FiO₂ {tr.get("niv_fio2_percent"):g}%' if tr.get("niv_fio2_percent") is not None else ""
                        st.write(
                            f'BiPAP: {tr["niv_ipap_cmh2o"]:g}/{tr["niv_epap_cmh2o"]:g} cm H2O{fio}'
                            + _treatment_timing_suffix(st.session_state.state, "niv")
                        )
                    else:
                        fio = f' · FiO₂ {tr.get("niv_fio2_percent"):g}%' if tr.get("niv_fio2_percent") is not None else ""
                        st.write(
                            f'{tr["niv_mode"]}: {tr["niv_pressure_cmh2o"]:g} cm H2O{fio}'
                            + _treatment_timing_suffix(st.session_state.state, "niv")
                        )
                if tr.get("airway_prepared") and not tr.get("invasive_ventilation"):
                    st.write("Airway equipment and team prepared for intubation")
                if tr.get("invasive_ventilation"):
                    st.write(
                        f'Invasive ventilation: {tr.get("ventilator_mode") or "VC/AC"} · '
                        f'FiO₂ {tr.get("ventilator_fio2_percent", 100):g}% · '
                        f'PEEP {tr.get("ventilator_peep_cmh2o", 8):g} cm H2O'
                        + _treatment_timing_suffix(st.session_state.state, "invasive_ventilation")
                    )
                if tr.get("disposition"):
                    st.write(f'Disposition: {tr.get("disposition")}')
            if faculty_access() and not st.session_state.state.get("engine_family"):
                with st.expander("Developer state", expanded=False):
                    st.caption("Hidden from learners in production.")
                    st.json({
                        "effective_volume": round(h["effective_volume"], 3),
                        "preload_state": round(h.get("preload_state", h["effective_volume"]), 3),
                        "preload_responsiveness": round(h.get("preload_responsiveness", 0.0), 3),
                        "effective_intravascular_fluid": round(h.get("effective_intravascular_fluid", 0.0), 3),
                        "extravascular_fluid_burden": round(h.get("extravascular_fluid_burden", 0.0), 3),
                        "retained_preload_contribution": round(
                            h.get("effective_intravascular_fluid", 0.0)
                            * (0.18 + 0.20 * h.get("preload_responsiveness", 0.0)),
                            3
                        ),
                        "overfill_burden": round(h.get("overfill_burden", 0.0), 3),
                        "pulmonary_congestion": round(h.get("pulmonary_congestion", 0.0), 3),
                        "pulmonary_clinical_signal": round(pulmonary_clinical_signal(st.session_state.state), 3),
                        "respiratory_failure_severity": round(h.get("respiratory_failure_severity", 0.0), 3),
                        "total_beta_blockade": round(total_beta_blockade(st.session_state.state), 3),
                        "beta_av_nodal_effect": round(beta_av_nodal_effect(st.session_state.state), 3),
                        "beta_myocardial_depression": round(beta_myocardial_depression(st.session_state.state), 3),
                        "af_substrate": round(af_substrate(st.session_state.state), 3),
                        "fluid_clock_integration": "single-pass",
                        "tissue_perfusion": round(h["tissue_perfusion"], 3),
                        "sympathetic_drive": round(h["sympathetic_drive"], 3),
                        "af_recurrence_pressure": round(h.get("af_recurrence_pressure", 0.0), 3),
                        "sinus_stability": round(h.get("sinus_stability", 0.0), 3),
                        "nitroglycerin_effect": round(h.get("nitroglycerin_effect", 0.0), 3),
                        "metoprolol_effect": round(h.get("metoprolol_effect", 0.0), 3),
                        "propranolol_effect": round(h.get("propranolol_effect", 0.0), 3),
                        "metoprolol_depot": round(h.get("metoprolol_depot", 0.0), 3),
                        "propranolol_depot": round(h.get("propranolol_depot", 0.0), 3),
                        "diltiazem_effect": round(h.get("diltiazem_effect", 0.0), 3),
                        "diltiazem_depot": round(h.get("diltiazem_depot", 0.0), 3),
                        "amiodarone_effect": round(h.get("amiodarone_effect", 0.0), 3),
                        "amiodarone_depot": round(h.get("amiodarone_depot", 0.0), 3),
                        "procedural_sedation_effect": round(h.get("procedural_sedation_effect", 0.0), 3),
                        "procedural_sedation_minutes": round(h.get("procedural_sedation_minutes", 0.0), 1),
                        "pulmonary_congestion": round(h["pulmonary_congestion"], 3),
                        "effective_map": round(h.get("effective_map", 0.0), 2),
                        "pressure_support_state": round(h.get("pressure_support_state", 0.0), 3),
                        "vascular_support": round(h.get("vascular_support", 0.0), 3),
                        "forward_flow_state": round(h.get("forward_flow_state", h.get("cardiac_output_index", 0.0)), 3),
                        "dobutamine_effect": round(h.get("dobutamine_effect", 0.0), 3),
                        "dobutamine_minutes": round(h.get("dobutamine_minutes", 0.0), 1),
                        "stroke_volume_efficiency": round(h.get("stroke_volume_efficiency", 0.0), 3),
                        "afterload_factor": round(h.get("afterload_factor", 0.0), 3),
                        "cardiac_output_index": round(h.get("cardiac_output_index", 0.0), 3),
                        "oxygen_delivery": round(h.get("oxygen_delivery", 0.0), 3),
                        "peripheral_flow": round(h.get("peripheral_flow", 0.0), 3),
                        "contractile_reserve": round(h.get("contractile_reserve", 1.0), 3),
                        "low_flow_burden": round(h.get("low_flow_burden", 0.0), 3),
                        "sympathetic_drive": round(h.get("sympathetic_drive", 0.0), 3),
                        "cardiac_arrest": bool(h.get("cardiac_arrest", False)),
                        "terminal_collapse": bool(h.get("terminal_collapse", False)),
                        "fluid_responsiveness": round(h["fluid_responsiveness"], 3),
                        "fluid_tolerance": round(h["fluid_tolerance"], 3),
                        "fluid_load": round(h["fluid_load"], 3),
                        "vasoplegia_severity": round(h.get("vasoplegia_severity", 0.0), 3),
                        "respiratory_failure_severity": round(h["respiratory_failure_severity"], 3),
                        "global_perfusion_failure": round(h["global_perfusion_failure"], 3),
                        "peri_arrest_risk": round(h["peri_arrest_risk"], 3),
                        "cardiac_arrest": h["cardiac_arrest"],
                        "pending_action": st.session_state.get("pending_action"),
                        "pending_reasoning": st.session_state.get("pending_reasoning"),
                        "last_executed_action": st.session_state.get("last_executed_action"),
                    })

    st.divider()
    submitted = False
    submission_text = ""
    submission_parsed = None
    with orders_panel:
        if not st.session_state.encounter_ended and (encounter_mode in {"Tests", "Treat"} or st.session_state.get("pending_reasoning")):
            import language as _lang
            st.markdown(_lang.say("### Orders" if encounter_mode == "Tests" else "### Management"))
            st.caption(_lang.say(
                "Write what you are doing in your own words: what you think is going on, "
                "what you are going to do, what you expect, and what you will check."
            ))
            pending_reasoning = st.session_state.get("pending_reasoning")
            if pending_reasoning:
                pending_missing = pending_reasoning.get("missing", []) or []
                held_parsed = pending_reasoning.get("parsed", {}) or {}
                held_reasoning = held_parsed.get("reasoning", {}) or {}
                held_reassessment = next(
                    (
                        action for action in held_parsed.get("actions", [])
                        if action.get("type") == "reassessment"
                    ),
                    {},
                )
                gate_id = int(pending_reasoning.get("gate_id") or 1)
                st.warning(
                    "An understood order is being held. The patient state is unchanged; "
                    "complete the reasoning in your own words or use the guided fields."
                )
                st.markdown(f"**Held order:** {_reasoning_gate_action_summary(held_parsed)}")
                held_unmodeled = [
                    str(item)
                    for item in (held_parsed.get("recognized_future_actions") or [])
                    if item
                ]
                if held_unmodeled:
                    st.info(
                        "Also recognized but not executable in this build: "
                        + ", ".join(held_unmodeled)
                        + ". These medications have not been administered."
                    )
                for observation in held_parsed.get("reasoning_observations", []) or []:
                    st.info(observation)
                import reasoning_questions as _questions
                st.markdown(_lang.say("  \n".join(
                    ("○ " if field in pending_missing else "✓ ") + question
                    for field, question, _ in _questions.QUESTIONS
                )))

                st.markdown(_lang.say("#### Answer what is missing"))
                with st.form(f"reasoning_completion_form_{gate_id}"):
                    left, right = st.columns(2)
                    with left:
                        guided_working_model = st.text_area(
                            _lang.say(_questions.QUESTION["working_model"]),
                            value=str(
                                held_reasoning.get("problem_representation")
                                or held_reasoning.get("rationale")
                                or ""
                            ),
                            height=78,
                            help=_lang.say(_questions.HELP["working_model"]),
                            key=f"reasoning_model_{gate_id}",
                        )
                        guided_expected_effect = st.text_area(
                            _lang.say(_questions.QUESTION["expected_effect"]),
                            value=str(held_reasoning.get("expected_effect")
                                      or (held_parsed.get("plan_suggestion") or {}).get("expected_effect") or ""),
                            height=78,
                            help=_lang.say(_questions.HELP["expected_effect"]),
                            key=f"reasoning_effect_{gate_id}",
                        )
                    with right:
                        # The action is one of the four and the only one that is
                        # never a field here. This form completes the reasoning
                        # around an order the engine already read; a box that
                        # could change it would let the follow-up administer a
                        # drug, and it provably cannot (specification §4).
                        st.text_area(
                            _lang.say(_questions.QUESTION["action"]),
                            value=_held_order_summary(held_parsed),
                            height=78,
                            disabled=True,
                            help=_lang.say(
                                "This is what the engine understood. To change it, cancel "
                                "and write the order again below."),
                            key=f"reasoning_action_{gate_id}",
                        )
                        guided_reassessment_target = st.text_area(
                            _lang.say(_questions.QUESTION["reassessment_target"]),
                            value=str(held_reasoning.get("reassessment_target")
                                      or (held_parsed.get("plan_suggestion") or {}).get("reassessment_target") or ""),
                            height=78,
                            help=_lang.say(_questions.HELP["reassessment_target"]),
                            key=f"reasoning_reassessment_{gate_id}",
                            placeholder="e.g. HR and rhythm, BP/MAP, capillary refill, mental status",
                        )
                    guided_reassessment_delay = st.number_input(
                        _lang.say("I will check in… minutes"),
                        min_value=1,
                        max_value=240,
                        value=min(240, max(1, int(held_reassessment.get("delay_min") or 5))),
                        step=1,
                        key=f"reasoning_delay_{gate_id}",
                    )
                    # Recorded because it is useful to read, never because it
                    # holds anything. It is asked last and says it is optional.
                    guided_priority = st.text_area(
                        _lang.say(REASONING_GATE_FIELD_STEMS["management_priority"]),
                        value=str(held_reasoning.get("management_priority") or ""),
                        height=68,
                        key=f"reasoning_priority_{gate_id}",
                    )
                    guided_submitted = st.form_submit_button(
                        "Complete reasoning & execute held order",
                        type="primary",
                    )

                if guided_submitted:
                    guided_resolution = complete_pending_reasoning_fields(
                        guided_working_model,
                        guided_priority,
                        guided_expected_effect,
                        guided_reassessment_target,
                        guided_reassessment_delay,
                    )
                    if guided_resolution and guided_resolution.get("clarification"):
                        active_pending = st.session_state.get("pending_reasoning") or {}
                        upsert_reasoning_gate_clarification(
                            active_pending.get("parsed", held_parsed),
                            guided_resolution.get("missing", []),
                        )
                        rerun_app()
                    if guided_resolution and guided_resolution.get("parsed"):
                        submission_parsed = guided_resolution["parsed"]
                        submission_text = guided_resolution.get("transcript") or "Guided reasoning completed."
                        submitted = True

                st.caption(
                    "Or answer naturally below. You only need to add what is missing; "
                    "you do not need to repeat the held order."
                )

            from urgent_interventions import awaiting_explanation, record_retrospective
            urgent_index = awaiting_explanation(st.session_state.get("management_trace") or [])
            if urgent_index is not None and not st.session_state.get("pending_reasoning"):
                urgent_entry = st.session_state.management_trace[urgent_index]
                unstated = [field for field in (urgent_entry.get("reasoning_gate") or {}).get("noted") or []
                            if field in REASONING_GATE_BLOCKING]
                with st.expander("Explain an urgent decision afterwards (optional, recorded as retrospective)"):
                    st.caption("The intervention already ran. What you write here is recorded as written now, "
                               "after the decision, and never as reasoning shown when it was taken.")
                    with st.form(f"retrospective_{urgent_index}"):
                        retrospective_answers = {
                            {"working_model": "problem_representation"}.get(field, field): st.text_area(
                                REASONING_GATE_FIELD_LABELS[field], key=f"retrospective_{urgent_index}_{field}",
                                height=68)
                            for field in unstated}
                        if st.form_submit_button("Save retrospective explanation"):
                            if record_retrospective(urgent_entry, retrospective_answers,
                                                    st.session_state.state.get("sim_time")):
                                if ACCOUNT_CONTEXT:
                                    save_session(ACCOUNT_CONTEXT)
                                rerun_app()

            if not submitted:
                with st.form("learner_form", clear_on_submit=True):
                    natural_text = st.text_area(
                        "Enter your clinical reasoning and/or actions",
                        height=100,
                        label_visibility="collapsed",
                        placeholder=(
                            "Describe your reasoning naturally. For example: I think...; "
                            "I am addressing... first; I expect...; reassess ... in ... minutes."
                        ),
                    )
                    natural_submitted = st.form_submit_button("Submit", type="primary")
                if natural_submitted:
                    submission_text = natural_text.strip()
                    submitted = True

            if any(st.session_state.get(key) for key in ("pending_reasoning", "pending_action", "pending_bundle")):
                if st.button("Cancel pending orders", key="cancel_pending_orders"):
                    cancel_pending_order()
                    rerun_app()

            if pending_reasoning and faculty_access():
                st.caption(
                    f"Facilitator override: type `{REASONING_GATE_OVERRIDE}` in the natural-language box."
                )

    if submitted and submission_text.strip():
        learner_input = submission_text.strip()
        from pending_cancellation import is_cancellation
        if is_cancellation(learner_input):
            if not cancel_pending_order():
                add_event("clarification", "There are no pending orders to cancel.")
            rerun_app()
        add_event(
            "reasoning_completion" if submission_parsed is not None else "you",
            learner_input,
        )
        trace_state_before = management_state_snapshot(st.session_state.state)
        processing_input = learner_input
        interpretation_audit = {"mode": "guided-form"}
        if submission_parsed is None:
            processing_input, interpretation_audit = normalize_clinical_turn(learner_input)

        if submission_parsed is not None:
            parsed = submission_parsed
        else:
            reasoning_resolution = resolve_pending_reasoning(processing_input)
            if reasoning_resolution and reasoning_resolution.get("clarification"):
                active_pending = st.session_state.get("pending_reasoning") or {}
                upsert_reasoning_gate_clarification(
                    active_pending.get("parsed", {}),
                    reasoning_resolution.get("missing", []),
                )
                rerun_app()

            if reasoning_resolution and reasoning_resolution.get("parsed"):
                parsed = reasoning_resolution["parsed"]
            else:
                pending_resolution = try_resolve_pending_action(processing_input)
                if pending_resolution and pending_resolution.get("clarification"):
                    add_event("clarification", pending_resolution["clarification"])
                    rerun_app()

                if pending_resolution and pending_resolution.get("parsed"):
                    parsed = merge_pending_bundle(pending_resolution["parsed"])
                else:
                    # Parse the current turn in full before considering contextual
                    # shorthand. Context resolution is a fallback only when this turn does
                    # not already contain an explicit executable action.
                    direct = clinical_interpreter(processing_input)
                    direct_non_reassess = [
                        a for a in direct.get("actions", []) if a.get("type") != "reassessment"
                    ]
                    if direct_non_reassess or st.session_state.state.get("engine_family"):
                        parsed = direct
                    else:
                        contextual = parse_contextual_followup(processing_input)
                        if contextual:
                            contextual["reasoning"] = direct.get("reasoning", {})
                            reassess = [a for a in direct.get("actions", []) if a.get("type") == "reassessment"]
                            contextual["actions"] = [
                                a for a in contextual.get("actions", []) if a.get("type") != "reassessment"
                            ] + reassess
                            parsed = contextual
                        else:
                            parsed = direct

            _restore_original_turn(parsed, processing_input, learner_input)
            _attach_interpretation_audit(parsed, interpretation_audit)

        parsed["reasoning_observations"] = reasoning_state_observations(
            parsed, st.session_state.state
        )
        missing_reasoning = reasoning_still_missing(parsed)
        gate_status = (parsed.get("reasoning_gate") or {}).get("status")
        if missing_reasoning and gate_status != "overridden":
            st.session_state.last_parse = parsed
            hold_pending_reasoning(parsed, missing_reasoning)
            upsert_reasoning_gate_clarification(parsed, missing_reasoning)
            rerun_app()
        if gate_status is None and any(
            action.get("type") in REASONING_GATE_ACTION_TYPES
            for action in parsed.get("actions", [])
        ):
            from urgent_interventions import is_urgent, present_categories
            if is_urgent(parsed):
                noted = reasoning_gate_noted(parsed)
                parsed["reasoning_gate"] = {"required": True, "status": "urgent_unheld", "missing": [],
                                            "noted": noted, "present": present_categories(parsed)}
                gate_status = "urgent_unheld"
                if [field for field in noted if field in REASONING_GATE_BLOCKING]:
                    add_event("prototype", "Urgent intervention executed without waiting for the reasoning. "
                              "Not stated: " + ", ".join(REASONING_GATE_FIELD_LABELS[field].rstrip("?").lower()
                                                         for field in noted if field in REASONING_GATE_BLOCKING)
                              + ". You can explain it afterwards; it is recorded as a retrospective explanation.")
            else:
                parsed["reasoning_gate"] = {"required": True, "status": "complete", "missing": [],
                                            "noted": reasoning_gate_noted(parsed)}
                gate_status = "complete"

        recognize_cues_for(parsed)

        for observation in parsed.get("reasoning_observations", []) or []:
            add_event("reasoning_note", observation)

        st.session_state.last_parse = parsed
        st.session_state.history.append(parsed)
        trace_input = parsed.get("raw_text") or learner_input

        result = execute_bundle(parsed)
        trace_state_after = management_state_snapshot(st.session_state.state)
        recorded_trace_event = record_management_trace(
            trace_input, parsed, result, trace_state_before, trace_state_after
        )

        if gate_status == "overridden":
            add_event(
                "prototype",
                "Facilitator override accepted. The held order was executed with incomplete prospective reasoning."
            )

        if parsed["recognized_future_actions"] and not result.get("terminal_locked"):
            import unexecuted_items
            said, unclassified = unexecuted_items.messages(parsed)
            for line in said:
                add_event("prototype", line)
            if unclassified:
                add_event(
                    "prototype",
                    "Recognized but not executed in this build: "
                    + ", ".join(unclassified)
                    + ". Any supported actions in the same order continue separately."
                )

        if result.get("clarification"):
            add_event("clarification", result["clarification"])
        else:
            summaries = _summaries_in_learner_order(
                result.get("action_summaries", []), trace_input
            )
            if summaries:
                # All actions in one learner order are integrated into one longitudinal
                # patient state and produce one learner-facing update at the reassessment time.
                labels = []
                for s in summaries:
                    # A call or admission request reads as part of "After ..., BP ...";
                    # its stored label ("ICU contacted; definitive ...") does not.
                    if s.get("type") == "procedure":
                        continue
                    # An examination is an observation: it carries its own entry,
                    # exactly as the Examine control writes it.
                    if s.get("type") == "examination":
                        continue
                    if s.get("type") in {"consult", "reperfusion_referral"}:
                        service = s.get("service") or s.get("destination")
                        if s.get("pathway_note"):
                            labels.append(str(s["label"]))
                        else:
                            labels.append(f'{service} already contacted (not repeated)' if s.get("repeated")
                                          else f'contacting {service} (no intervention yet)')
                            continue
                    elif s.get("type") == "disposition":
                        # Going home is a discharge, not an admission to a place.
                        home = s.get("destination") == "home"
                        labels.append(
                            ('discharge home already requested (not repeated)' if home else
                             f'admission to {s.get("destination")} already requested (not repeated)')
                            if s.get("repeated") else
                            ('discharging the patient home' if home else f'requesting admission to {s.get("destination")}'))
                    elif "volume_ml" in s and s.get("fluid_type"):
                        labels.append(_fluid_order_label(s, st.session_state.state["sim_time"]))
                    elif s.get("label"):
                        labels.append(str(s["label"]))
                    elif "volume_ml" in s:
                        labels.append(f'{s["volume_ml"]} mL {s["fluid_type"]}')
                    elif s.get("type") == "magnesium":
                        labels.append(f'magnesium sulfate {s["dose_mg"] / 1000:g} g {s.get("route", "IV")}'
                                      + (f' over {s["administration_duration_min"]:g} min' if s.get("administration_duration_min") else ""))
                    elif s.get("agent") == "furosemide":
                        labels.append(f'furosemide {s["dose_mg"]:g} mg {s["route"]}'
                                      + (f' over {s["administration_duration_min"]:g} min' if s.get("administration_duration_min") else ""))
                    elif "agent" in s:
                        labels.append(f'{s["agent"]} {s["dose_mg"]:g} mg {s["route"]}'
                                      + (f' over {s["administration_duration_min"]:g} min' if s.get("administration_duration_min") else ""))
                    elif s.get("support_type") == "procedural_sedation":
                        labels.append(procedural_sedation_label(s))
                    elif "energy_j" in s:
                        labels.append(f'synchronized cardioversion {s["energy_j"]} J')
                    elif s.get("support_type") == "oxygen":
                        labels.append(f'{s["device"]} {s["flow_lpm"]:g} L/min')
                    elif s.get("support_type") == "norepinephrine":
                        if s.get("operation") == "stop":
                            labels.append("norepinephrine stopped")
                        else:
                            labels.append(_norepinephrine_summary_label(s))
                    elif s.get("support_type") == "dobutamine":
                        if s.get("operation") == "stop":
                            labels.append("dobutamine stopped")
                        else:
                            labels.append(f'dobutamine {s.get("rate", 5):g} mcg/kg/min')
                    elif s.get("support_type") == "epinephrine":
                        labels.append("epinephrine stopped" if s.get("operation") == "stop"
                                      else f'epinephrine {s.get("rate", 0):g} {s.get("units", "mcg/min")}')
                    elif s.get("support_type") == "nitroglycerin":
                        if s.get("operation") == "stop":
                            labels.append("nitroglycerin stopped")
                        else:
                            labels.append(f'nitroglycerin {s["rate_mcg_min"]:g} mcg/min')
                    elif s.get("support_type") == "niv":
                        if s.get("operation") == "stop":
                            labels.append("noninvasive ventilation stopped")
                        elif s.get("mode") == "BiPAP" and s.get("ipap_cmh2o") is not None and s.get("epap_cmh2o") is not None:
                            fio = f' at FiO2 {s.get("fio2_percent"):g}%' if s.get("fio2_percent") is not None else ""
                            labels.append(f'BiPAP {s.get("ipap_cmh2o"):g}/{s.get("epap_cmh2o"):g} cm H2O{fio}')
                        else:
                            fio = f' at FiO2 {s.get("fio2_percent"):g}%' if s.get("fio2_percent") is not None else ""
                            labels.append(f'{s["mode"]} {s["pressure_cmh2o"]:g} cm H2O{fio}')
                    elif s.get("support_type") == "airway_preparation":
                        labels.append("airway preparation for intubation")
                    elif s.get("support_type") == "invasive_ventilation":
                        operation = s.get("operation", "start")
                        prefix = {
                            "continue": "continued",
                            "adjust": "adjusted",
                            "start": "intubation +",
                        }.get(operation, "adjusted")
                        labels.append(
                            f'{prefix} {s.get("ventilator_mode", "VC/AC")} ventilation '
                            f'at FiO2 {s.get("fio2_percent", 100):g}% and PEEP {s.get("peep_cmh2o", 8):g} cm H2O'
                        )
                    elif s.get("support_type") == "disposition":
                        labels.append("discharge home" if s.get("destination") == "home"
                                      else f'admission to {s.get("destination", "ICU")}')
                    elif s.get("support_type") == "antibiotics":
                        antibiotic = str(s.get("agent_name") or "broad-spectrum antibiotics")
                        if antibiotic.lower() == "ceftriaxone + azithromycin":
                            ceftriaxone = "ceftriaxone"
                            if s.get("dose_g") is not None:
                                ceftriaxone += f' {s.get("dose_g"):g} g'
                            if s.get("route"):
                                ceftriaxone += f' {s.get("route")}'
                            antibiotic = ceftriaxone + " + azithromycin"
                        else:
                            if s.get("dose_g") is not None:
                                antibiotic += f' {s.get("dose_g"):g} g'
                            if s.get("route"):
                                antibiotic += f' {s.get("route")}'
                        if s.get("administration_duration_min"):
                            antibiotic += f' over {s["administration_duration_min"]:g} min'
                        labels.append(antibiotic)

                diagnostic_summaries = sorted(
                    [x for x in summaries if x.get("diagnostic_type")],
                    key=lambda x: (x.get("result") or {}).get("time_min", st.session_state.state["sim_time"]),
                )
                treatment_labels = [x for x in labels if x]
                # Diagnostic information becomes available during the interval and is
                # rendered before the scheduled reassessment update.
                # Results and any procedure the course produced (an endoscopy) are
                # reported in the order they happened.
                timed_events = [("diagnostic_result", format_diagnostic_summary(ds),
                                 (ds.get("result") or {}).get("time_min", st.session_state.state["sim_time"]))
                                for ds in diagnostic_summaries]
                timed_events += [("procedure", x["label"], x["time_min"]) for x in summaries if x.get("type") == "procedure"]
                timed_events += [("study_not_performed", x["label"], x["time_min"])
                                 for x in summaries if x.get("type") == "study_not_performed"]
                timed_events += [("examination", x["label"], x.get("time_min", st.session_state.state["sim_time"]))
                                 for x in summaries if x.get("type") == "examination"]
                # The reperfusion pathway is reported as its own entry, at the minute
                # the resident decided it.
                timed_events += [("procedure", str(x["pathway_note"]), st.session_state.state["sim_time"])
                                 for x in summaries if x.get("pathway_note")]
                for kind, text, time in sorted(timed_events, key=lambda item: item[2]):
                    add_event(kind, text, time=time)
                if treatment_labels:
                    lead = "After " + " + ".join(treatment_labels) + ", "
                    add_event("clinical_update", lead + format_clinical_update())
                elif (
                    diagnostic_summaries
                    # A reassessment the resident asked for is reported as such, even
                    # when the results arrived before it.
                    and result.get("reassess_delay") is None
                    and int(result.get("elapsed_min", 0) or 0) > 0
                    and observable_state_changed(trace_state_before, trace_state_after)
                ):
                    elapsed = int(result.get("elapsed_min", 0) or 0)
                    add_event(
                        "clinical_update",
                        f"While awaiting diagnostic results over {elapsed} minutes, "
                        + format_clinical_update(),
                    )
                elif result.get("reassess_delay") is not None:
                    d = result.get("reassess_delay") or 0
                    add_event(
                        "clinical_update",
                        ("On immediate reassessment, " if d == 0 else f"After {d} minutes, ")
                        + format_clinical_update()
                    )

            # A reassessment-only order has no treatment/diagnostic summaries, so
            # it needs its own learner-facing patient update.
            if result.get("reassess_delay") is not None and not result.get("action_summaries"):
                d = result["reassess_delay"] or 0
                add_event(
                    "clinical_update",
                    ("On immediate reassessment, " if d == 0 else f"After {d} minutes, ")
                    + format_clinical_update()
                )

            if result.get("terminal_locked"):
                add_event(
                    "prototype",
                    "Cardiovascular collapse is a terminal state in this build. Ordinary reassessment is paused; arrest-management actions are not yet executable."
                )

            if not result.get("executed") and not parsed["recognized_future_actions"] and not result.get("terminal_locked"):
                add_event(
                    "prototype",
                    "I preserved your input, but this build does not yet execute that action."
                )

        # The events this order produced are appended above, after the decision
        # was recorded, so the recorded response window used to end just before
        # its own response. The Management Trace analysis is validated against
        # that window, and was rejected for citing the very update it described
        # (2026-09-22, preparing the learner report). The cursor is therefore
        # advanced once the response is on the record.
        recorded_trace_event["state_after"]["encounter_event_count"] = len(
            st.session_state.get("events") or []
        )
        rerun_app()

    st.divider()

    if not st.session_state.encounter_ended:
        if st.button(
            "Complete Encounter & Begin Review",
            type="primary",
            disabled=not bool(st.session_state.management_trace),
        ):
            begin_decision_review(st.session_state.management_trace, st.session_state.state)
            rerun_app()
    else:
        frozen_trace = st.session_state.get("encounter_closed_trace")
        if frozen_trace is None:
            # Backward-compatible recovery for an in-memory session opened in an
            # earlier build before encounter snapshots were introduced.
            begin_decision_review(st.session_state.management_trace, st.session_state.state)
            frozen_trace = st.session_state.encounter_closed_trace
        frozen_state = st.session_state.get("encounter_closed_state") or management_state_snapshot(st.session_state.state)
        render_learning_focus(ACCOUNT_CONTEXT)
        # One short, optional question about help received, at the close and
        # never before (faculty specification 2026-09-24, section 3).
        if ACCOUNT_CONTEXT:
            import language
            from assistance_portal import render_closing_question
            render_closing_question(ACCOUNT_CONTEXT, st.session_state.get("_attempt_id"),
                                    frozen_trace, language=language.current())
        with st.expander("Original decision-by-decision record", expanded=False):
            st.caption("Your original orders, stated reasoning and recorded responses remain unchanged.")
            render_management_trace(frozen_trace)
        if not st.session_state.get("expert_comparison_unlocked"):
            st.caption("Complete your independent reflection to receive an analyzed Management Trace with your clinical trajectory and key decisions.")
        render_decision_review(frozen_trace, frozen_state)

    st.divider()
    if ACCOUNT_CONTEXT:
        if st.button("Save & return to dashboard", type="secondary"):
            return_to_dashboard(ACCOUNT_CONTEXT, reset_session)
        if st.button("End this attempt without completing review", type="secondary"):
            return_to_dashboard(ACCOUNT_CONTEXT, reset_session, abandon=True)
    else:
        if st.button("Reset scenario", type="secondary"):
            reset_session()
            rerun_app()

    if faculty_access():
        if st.session_state.last_parse:
            with st.expander("Developer: last structured interpretation", expanded=False):
                st.json(st.session_state.last_parse)
        with st.expander("Developer: Management Trace", expanded=False):
            st.caption("Structured longitudinal decision-response log for faculty inspection.")
            st.json(st.session_state.management_trace)

    if ACCOUNT_CONTEXT:
        save_session(ACCOUNT_CONTEXT)
    st.caption(f"Management Reasoning Simulator · Clinical encounter v{SIMULATOR_VERSION.split('-')[0]}")

    # Compatibility marker for v0.6.0.27 regression lineage.
