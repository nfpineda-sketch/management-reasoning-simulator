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


#: The same observations named in Spanish; numbers and units stay as recorded
#: (decision 16), and a stored value ("Alert", "Cool") is said as the room says it.
_OBSERVATION_NAMES_ES = {
    "sbp": "PA sistólica", "dbp": "PA diastólica", "hr": "frecuencia cardíaca", "rhythm": "ritmo",
    "spo2": "SpO2", "respiratory_rate": "frecuencia respiratoria", "mental_status": "estado mental",
    "work_of_breathing": "esfuerzo respiratorio", "crt": "llene capilar", "extremities": "extremidades",
    "pulse_present": "pulso presente",
}


def _observation_text(snapshot, language="en"):
    observations = _mapping(snapshot.get("observable"))
    labels = []
    for key, label, unit in _OBSERVATIONS:
        value = _scalar(observations.get(key))
        if value:
            if language != "en":
                import language as languages
                label = _OBSERVATION_NAMES_ES.get(key, label)
                if isinstance(observations.get(key), (bool, str)):
                    value = languages.observed_value(value.capitalize() if isinstance(observations.get(key), bool)
                                                     else value, language)
                    # A value inside the sentence, as Spanish writes it; an acronym ("FA") keeps its case.
                    value = value if value.isupper() else value[:1].lower() + value[1:]
                if key == "rhythm" and value.startswith("ritmo "):
                    labels.append(value)  # "ritmo sinusal", not "ritmo ritmo sinusal"
                    continue
            labels.append(f"{label} {value}{(' ' + unit) if unit else ''}")
    if labels:
        return "; ".join(labels)
    return "no observable values were recorded" if language == "en" else "no se registraron valores observables"


def _diagnostic_text(snapshot, at_time, language="en"):
    if at_time is None:
        return []
    if language != "en":
        return _diagnostic_text_in(snapshot, at_time, language)
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


#: The report fields above, named in Spanish; units stay as recorded (decision 16).
_DIAGNOSTIC_LABELS_ES = {
    "cortisol": "cortisol", "TSH": "TSH", "free T4": "T4 libre", "ketones": "cetonas", "report": "informe",
    "finding": "hallazgo", "glucose": "glicemia", "troponin": "troponina",
    "upper reference": "límite superior de referencia", "hemoglobin": "hemoglobina",
    "measured concentration": "concentración medida", "lactate": "lactato", "pH": "pH", "PCO2": "PCO2",
    "PaCO2": "PaCO2", "PaO2": "PaO2", "bicarbonate": "bicarbonato", "potassium": "potasio",
    "sodium": "sodio", "WBC": "leucocitos", "temperature": "temperatura", "LV": "VI", "RV": "VD",
    "lungs": "pulmones", "IVC": "VCI", "pericardium": "pericardio",
}


def _diagnostic_text_in(snapshot, at_time, language):
    """The same reports in another language: study and field names from the
    documents' catalog, report prose as the room says it (and as the faculty
    approved the case's own words); numbers and units as recorded."""
    import language as languages
    import report_presentation as presentation
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
                if isinstance(result.get(field), str):
                    value = languages.say(value, language)
                fields.append(f"{_DIAGNOSTIC_LABELS_ES.get(label, label)}: {value}{(' ' + unit) if unit else ''}")
        if fields:
            collected = _time(result.get("collected_at_min"))
            collection_text = (f", tomada a los {collected} min"
                               if collected is not None and collected <= time else "")
            reports.append(f"{presentation.study_name(key, language)} disponible a los {time} min"
                           f"{collection_text} — " + "; ".join(fields))
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


def trajectory_review(trace, *, source_decision=None, language="en"):
    """Review one resolved event, or the last executed event in a trace.

    The caller supplies the displayed decision ordinal when resolving a prompt.
    A list defaults to its last executed/terminal-locked decision's ordinal.
    Missing event evidence returns ``None`` rather than an invented expert model.

    ``language`` writes the same review in another language (faculty,
    2026-09-26): the review's own words from the reviewed templates below, the
    resident's words quoted as they wrote them, never spliced into a sentence
    in the other language.
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
    if language != "en":
        return _review_in(language, event, before, after, before_time, after_time, source_decision,
                          action_types, explanation=explanation, priority=priority, expectation=expectation,
                          rationale=rationale, preservation=preservation, target=target)
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


def _quoted(text):
    """The resident's own words, quoted as written: never translated, never spliced."""
    return "\u00ab" + text + "\u00bb"


def _said(text):
    """A quotation that ends a sentence: its own full stop is the sentence's."""
    return _quoted(text) + ("" if text.rstrip().endswith((".", "!", "?", "\u2026")) else ".")


def _review_in(language, event, before, after, before_time, after_time, source_decision, action_types, *,
               explanation, priority, expectation, rationale, preservation, target):
    """``trajectory_review`` in Spanish, from the same recorded evidence."""
    import report_presentation as presentation
    before_description = _observation_text(before, language)
    after_description = _observation_text(after, language)
    framing = (f"Explicación declarada por el residente: {_said(explanation)} " if explanation else
               "No se registró explícitamente una explicación de trabajo. ")
    framing += (f"La decisión comenzó a los {before_time} min con {before_description}. "
                f"A los {after_time} min, las observaciones registradas fueron {after_description}.")
    cues = [f"Antes de la decisión ({before_time} min): {before_description}.",
            f"Después de la decisión ({after_time} min): {after_description}."]
    before_reports = _diagnostic_text(before, before_time, language)
    after_reports = _diagnostic_text(after, after_time, language)
    cues.extend("Disponible antes de esta decisión: " + result for result in before_reports)
    cues.extend("Registrado después de esta decisión: " + result for result in after_reports
                if result not in before_reports)
    if expectation:
        cues.append("Efecto esperado declarado por el residente: " + _quoted(expectation))
    tradeoff_parts = []
    if rationale:
        tradeoff_parts.append("Fundamento registrado: " + _said(rationale))
    if preservation:
        tradeoff_parts.append("Objetivo de preservación registrado: " + _said(preservation))
    if not tradeoff_parts:
        tradeoff_parts.append("No se registró un fundamento explícito del tratamiento ni un objetivo de preservación.")
    tradeoff_parts.append(
        "Compara el beneficio esperado con la respuesta observada y los hallazgos no resueltos; "
        "un cambio después del tratamiento no establece por sí solo su causa."
    )
    actions = []
    if event.get("execution_status") == "executed" and isinstance(event.get("action_summaries"), (list, tuple)):
        # "reassess" is the older name of the same order.
        actions = presentation.action_lines([{**action, "type": "reassessment"} if action.get("type") == "reassess"
                                             else action for action in event["action_summaries"]
                                             if isinstance(action, dict)], language)
    return {
        "framing": framing,
        "priority": ("Prioridad declarada por el residente: " + _said(priority) if priority
                     else "No se registró explícitamente una prioridad de manejo."),
        "cues": cues,
        "action": ("Acciones ejecutadas registradas: " + "; ".join(actions) + ".") if actions
        else "No hay un resumen de las acciones ejecutadas en esta decisión.",
        "tradeoff": " ".join(tradeoff_parts),
        "reassessment": ("Objetivo de reevaluación registrado: " + _said(target) + " ") if target
        else "No se registró explícitamente un objetivo de reevaluación. ",
        "trajectory_grounded": True,
        "source_decision": source_decision,
        "source_action_types": action_types,
    }


#: The review's labels and prompts, as the resident reads them in Spanish.
LABELS_ES = {
    "Review your first management decision": "Revisa tu primera decisión de manejo",
    "Review a change in your explanation": "Revisa un cambio en tu explicación",
    "Review your latest management decision": "Revisa tu última decisión de manejo",
}
_EXPECTED_EN = ("Your recorded expected effect was: ", ". Which observations supported or challenged that "
                "expectation, what remained uncertain, and what would guide your next management step?")
_NO_EXPECTATION_EN = ("What did you expect at this decision, what did you observe on "
                      "reassessment, and how would those observations influence your next priority?")


def prompt_in(text, language="es"):
    """A stored review prompt in another language, or None when it is none of this module's.

    The prompt was stored in English as the resident's review began; it is said
    again from its own template, with the resident's expected effect quoted as
    they wrote it.
    """
    text = str(text or "")
    if language == "en":
        return text
    if text == _NO_EXPECTATION_EN:
        return ("¿Qué esperabas en esta decisión, qué observaste al reevaluar y cómo influirían esas "
                "observaciones en tu siguiente prioridad?")
    head, tail = _EXPECTED_EN
    if text.startswith(head) and text.endswith(tail) and len(text) > len(head) + len(tail):
        expectation = text[len(head):-len(tail)]
        return ("Tu efecto esperado registrado fue: " + _said(expectation) + " ¿Qué observaciones "
                "apoyaron o cuestionaron esa expectativa, qué quedó incierto y qué guiaría tu siguiente paso "
                "de manejo?")
    return None


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
