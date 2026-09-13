"""Descriptive review of a frozen decision, without hidden case knowledge.

This comparison summarizes recorded observations and explicit learner reasoning.
It does not recommend disease-specific treatment, attribute a cognitive bias, or
infer a cause for altered consciousness. Temporal change is not proof of a
treatment's causal effect.
"""

from __future__ import annotations

import math


_OBSERVATIONS = (
    ("sbp", "systolic BP", "mmHg"), ("dbp", "diastolic BP", "mmHg"),
    ("hr", "heart rate", "/min"), ("rhythm", "rhythm", ""),
    ("spo2", "SpO2", "%"), ("respiratory_rate", "respiratory rate", "/min"),
    ("mental_status", "mental status", ""), ("work_of_breathing", "breathing effort", ""),
    ("crt", "capillary refill", "s"), ("extremities", "extremities", ""),
    ("pulse_present", "pulse present", ""),
)
_DIAGNOSTICS = frozenset((
    "pocus", "lactate", "vbg", "abg", "basic_labs", "temperature",
    "poc_glucose", "focused_history", "chest_xray", "urinalysis",
    "blood_cultures", "troponin", "ctpa", "hemoglobin",
    "head_ct", "abdominal_ct", "cortisol", "thyroid_function", "ketones", "toxicology",
))
_DIAGNOSTIC_FIELDS = (
    ("cortisol_ug_dl", "cortisol", "µg/dL"), ("tsh_miu_l", "TSH", "mIU/L"),
    ("free_t4_ng_dl", "free T4", "ng/dL"), ("ketones_mmol_l", "ketones", "mmol/L"),
    ("report", "report", ""), ("finding", "finding", ""),
    ("glucose_mg_dl", "glucose", "mg/dL"), ("value_ng_l", "troponin", "ng/L"),
    ("upper_reference_ng_l", "upper reference", "ng/L"),
    ("hemoglobin_g_dl", "hemoglobin", "g/dL"),
    ("value_mmol_l", "measured concentration", "mmol/L"),
    ("lactate_mmol_l", "lactate", "mmol/L"), ("ph", "pH", ""),
    ("pco2_mm_hg", "PCO2", "mmHg"), ("paco2_mm_hg", "PaCO2", "mmHg"),
    ("pao2_mm_hg", "PaO2", "mmHg"), ("bicarbonate_mmol_l", "bicarbonate", "mmol/L"),
    ("potassium_mmol_l", "potassium", "mmol/L"),
    ("sodium_mmol_l", "sodium", "mmol/L"), ("wbc_k_ul", "WBC", "K/uL"),
    ("temperature_c", "temperature", "C"), ("value_celsius", "temperature", "C"),
    ("lv", "LV", ""), ("rv", "RV", ""), ("lungs", "lungs", ""),
    ("ivc", "IVC", ""), ("pericardium", "pericardium", ""),
)
_ACTION_FIELDS = (
    "agent", "dose_mg", "dose_g", "dose", "units", "route", "volume_ml",
    "fluid_type", "device", "flow_lpm", "rate", "rate_mcg_min", "operation",
    "mode", "ipap_cmh2o", "epap_cmh2o", "fio2_percent", "ventilator_mode",
    "peep_cmh2o", "service", "destination", "diagnostic", "diagnostic_type",
    "delay_min", "duration_min", "time_min",
)


def _text(value):
    return value.strip()[:4000] if isinstance(value, str) else ""


def _scalar(value):
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, str):
        return _text(value)
    if type(value) in (int, float) and math.isfinite(value):
        return str(value)
    return ""


def _time(value):
    return value if type(value) in (int, float) and math.isfinite(value) and value >= 0 else None


def _mapping(value):
    return value if isinstance(value, dict) else {}


def _observation_text(snapshot):
    observations = _mapping(snapshot.get("observable"))
    labels = []
    for key, label, unit in _OBSERVATIONS:
        value = _scalar(observations.get(key))
        if value:
            labels.append(f"{label} {value}{(' ' + unit) if unit else ''}")
    return "; ".join(labels) or "no observable values were recorded"


def _diagnostic_text(snapshot, at_time):
    if at_time is None:
        return []
    reports = []
    for key, result in _mapping(snapshot.get("diagnostics")).items():
        if key not in _DIAGNOSTICS or not isinstance(result, dict):
            continue
        time = _time(result.get("time_min"))
        if time is None or time > at_time or result.get("status", "available") != "available":
            continue
        fields = []
        for field, label, unit in _DIAGNOSTIC_FIELDS:
            value = _scalar(result.get(field))
            if value:
                fields.append(f"{label}: {value}{(' ' + unit) if unit else ''}")
        if fields:
            collected = _time(result.get("collected_at_min"))
            collection_text = f", collected at {collected} min" if collected is not None and collected <= time else ""
            reports.append(f"{key.replace('_', ' ')} available at {time} min{collection_text} — " + "; ".join(fields))
    return reports


def _executed_actions(event):
    if event.get("execution_status") != "executed":
        return [], []
    summaries = event.get("action_summaries")
    if not isinstance(summaries, (list, tuple)):
        return [], []
    labels, types = [], set()
    for action in summaries:
        if not isinstance(action, dict):
            continue
        action_type = _text(action.get("type"))
        if action_type:
            types.add(action_type)
        label = _text(action.get("label")) or action_type.replace("_", " ")
        details = [f"{field.replace('_', ' ')}={_scalar(action[field])}"
                   for field in _ACTION_FIELDS if field in action and _scalar(action[field])]
        if label or details:
            labels.append(label + (" (" + "; ".join(details) + ")" if details else ""))
    return labels, sorted(types)


def trajectory_review(trace, *, source_decision=None):
    """Review one resolved event, or the last executed event in a trace.

    The caller supplies the displayed decision ordinal when resolving a prompt.
    A list defaults to its last executed/terminal-locked decision's ordinal.
    Missing event evidence returns ``None`` rather than an invented expert model.
    """
    if isinstance(trace, (list, tuple)):
        candidates = [event for event in trace if isinstance(event, dict)
                      and event.get("execution_status") in {"executed", "terminal_locked"}]
        if not candidates:
            return None
        event = candidates[-1]
        if source_decision is None:
            source_decision = len(candidates)
    elif isinstance(trace, dict):
        event = trace
    else:
        return None
    before = _mapping(event.get("state_before"))
    after = _mapping(event.get("state_after"))
    if not before or not after:
        return None
    before_time = _time(event.get("decision_time_min", before.get("sim_time_min")))
    after_time = _time(event.get("response_time_min", after.get("sim_time_min")))
    if before_time is None or after_time is None or after_time < before_time:
        return None
    reasoning = _mapping(event.get("reasoning"))
    explanation = _text(reasoning.get("problem_representation"))
    priority = _text(reasoning.get("management_priority"))
    expectation = _text(reasoning.get("expected_effect"))
    rationale = _text(reasoning.get("rationale"))
    preservation = _text(reasoning.get("preservation_goal"))
    target = _text(reasoning.get("reassessment_target"))
    action_labels, action_types = _executed_actions(event)
    before_description = _observation_text(before)
    after_description = _observation_text(after)
    framing = (
        f"Learner-stated explanation: {explanation}. " if explanation else
        "No working explanation was explicitly recorded. "
    )
    framing += (
        f"The decision began at {before_time} min with {before_description}. "
        f"At {after_time} min, the recorded observations were {after_description}."
    )
    cues = [f"Before the decision ({before_time} min): {before_description}.",
            f"After the decision ({after_time} min): {after_description}."]
    before_reports = _diagnostic_text(before, before_time)
    after_reports = _diagnostic_text(after, after_time)
    cues.extend("Available before this decision: " + result for result in before_reports)
    cues.extend("Recorded after this decision: " + result for result in after_reports if result not in before_reports)
    if expectation:
        cues.append("Learner-stated expected effect: " + expectation)
    tradeoff_parts = []
    if rationale:
        tradeoff_parts.append("Recorded rationale: " + rationale)
    if preservation:
        tradeoff_parts.append("Recorded preservation goal: " + preservation)
    if not tradeoff_parts:
        tradeoff_parts.append("No explicit treatment rationale or preservation goal was recorded.")
    tradeoff_parts.append(
        "Compare the expected benefit with the observed response and unresolved findings; "
        "a change after treatment does not by itself establish its cause."
    )
    return {
        "framing": framing,
        "priority": "Learner-stated priority: " + priority if priority else "No management priority was explicitly recorded.",
        "cues": cues,
        "action": ("Recorded executed actions: " + "; ".join(action_labels) + ".") if action_labels else "No executed action summary is available for this decision.",
        "tradeoff": " ".join(tradeoff_parts),
        "reassessment": ("Recorded reassessment target: " + target + ". ") if target else "No reassessment target was explicitly recorded. ",
        "trajectory_grounded": True,
        "source_decision": source_decision,
        "source_action_types": action_types,
    }


def reflection_items(trace):
    """Select at most three source-bound decisions for open reflection.

    Ordinals match the visible trace's executed/terminal-locked numbering. Only
    executed decisions are selected. A model shift means an explicit change in
    the learner's recorded explanation; it is not an inferred cognitive process.
    """
    if not isinstance(trace, (list, tuple)):
        return []
    visible = [event for event in trace if isinstance(event, dict)
               and event.get("execution_status") in {"executed", "terminal_locked"}]
    executed = [(ordinal, event) for ordinal, event in enumerate(visible, 1)
                if event.get("execution_status") == "executed"]
    if not executed:
        return []
    selections = [(executed[0], "Review your first management decision")]
    previous_explanation = _text(_mapping(executed[0][1].get("reasoning")).get("problem_representation"))
    for item in executed[1:]:
        explanation = _text(_mapping(item[1].get("reasoning")).get("problem_representation"))
        if explanation and previous_explanation and explanation != previous_explanation:
            selections.append((item, "Review a change in your explanation"))
            break
        if explanation:
            previous_explanation = explanation
    if executed[-1][0] not in {item[0][0] for item in selections}:
        selections.append((executed[-1], "Review your latest management decision"))
    items = []
    for (ordinal, event), label in selections[:3]:
        before = _mapping(event.get("state_before"))
        time = _time(event.get("decision_time_min", before.get("sim_time_min")))
        if time is None:
            continue
        whole_minutes = int(time)
        time_label = f"{whole_minutes // 60:02d}:{whole_minutes % 60:02d}"
        expectation = _text(_mapping(event.get("reasoning")).get("expected_effect"))
        if expectation:
            prompt = (
                f"Your recorded expected effect was: {expectation}. "
                "Which observations supported or challenged that expectation, "
                "what remained uncertain, and what would guide your next management step?"
            )
        else:
            prompt = (
                "What did you expect at this decision, what did you observe on "
                "reassessment, and how would those observations influence your next priority?"
            )
        items.append(("decision", ordinal, time_label, label, prompt))
    return items
