"""Presentation rules shared by the learner report and the faculty brief.

Faculty request 2026-09-23, after reading the first three PDFs produced from a
real encounter. Three of the problems were common to both documents, so they
are answered once here.

**One visible identifier.** The learner report was headed by the authored case's
own id and the faculty brief by the challenge, so the same encounter looked like
two different ones. The identifier is now the encounter record's id, with the
challenge beside it, and both documents print it.

**Readable actions.** The learner report printed the engine's own field names —
``diagnostic (diagnostic type: pocus; duration min: 15)``. What the resident
ordered has to read as an order, keeping the dose, the route, the settings and
the timing, which are the clinically relevant parts.

**Honest text.** The analysis schema caps each field, and a model that writes up
to the cap is cut mid-word. A cut field is marked as cut rather than presented
as a finished sentence, and the redundant ``AI interpretation:`` prefix the model
repeats on every field is removed, because both documents already label the whole
section as interpretation.
"""
from __future__ import annotations

import re

# The caps the analysis schemas impose, current and historical. A field whose
# length is exactly one of them and that does not end a sentence was cut by the
# provider, not finished by the author; a report stored under an older cap has
# to be read the same way.
CLAIM_MAX_CHARS = 900
TITLE_MAX_CHARS = 140
CLAIM_CAPS = (600, CLAIM_MAX_CHARS)
TITLE_CAPS = (90, TITLE_MAX_CHARS)
# The caps each prompt version wrote under. A length is only evidence of a cut
# against the cap that applied, or a title that happens to be ninety characters
# long under the newer limit reads as if it had been chopped.
CAPS_BY_PROMPT = {
    "1.0": {"claim": (600,), "title": (90,)},
    "1.1": {"claim": (CLAIM_MAX_CHARS,), "title": (TITLE_MAX_CHARS,)},
}


def caps_for(prompt_version):
    """(claim caps, title caps) for a report written under this prompt."""
    known = CAPS_BY_PROMPT.get(str(prompt_version or "").strip())
    if known:
        return known["claim"], known["title"]
    return CLAIM_CAPS, TITLE_CAPS
TRUNCATION_NOTE = " […interrupted: the analysis reached its length limit]"
_SENTENCE_END = ".!?\"')]»"
_AI_PREFIX = re.compile(r"^\s*(?:AI\s+interpretation|AI\s+synthesis|Interpretación\s+de\s+la\s+IA)\s*[:\-—]\s*", re.I)


def identifier(case_id="", challenge_id="", fallback=""):
    """The one identifier both documents show for the same encounter."""
    parts = [str(value or "").strip() for value in (case_id, challenge_id)]
    visible = [part for part in parts if part]
    return " · ".join(visible) or str(fallback or "").strip() or "Encounter not identified"


def _clean(value):
    return _AI_PREFIX.sub("", str(value or "").strip()).strip()


def was_truncated(value, caps=CLAIM_CAPS):
    """The cap applied to what the model emitted, prefix included.

    The redundant ``AI interpretation:`` prefix is removed for display, so the
    cut has to be measured on the raw field or a capped 600-character answer
    looks like a 581-character finished one.
    """
    raw = str(value or "").strip()
    return bool(raw) and len(raw) in set(caps) and raw[-1] not in _SENTENCE_END


def claim_text(value, caps=CLAIM_CAPS):
    """Model prose as it should be read: no repeated prefix, cuts declared.

    The cut is judged on the original value, because removing the prefix makes
    a capped field shorter than its cap.
    """
    text = _clean(value)
    return text + TRUNCATION_NOTE if was_truncated(value, caps) else text


# --- what the resident ordered, written as an order -------------------------

_ROUTES = {"IV": "IV", "IO": "IO", "IM": "IM", "PO": "PO", "SC": "SC", "IN": "intranasal",
           "nebulized": "nebulised", "inhaled": "inhaled"}
_OPERATION = {"start": "started", "stop": "stopped", "adjust": "adjusted",
              "continue": "continued unchanged", "increase": "increased", "decrease": "decreased"}
# A study is named the way it is asked for at the bedside, not by its key.
_STUDY_NAMES = {
    "ecg": "12-lead ECG", "ecg_right": "right-sided ECG (V3R-V4R)",
    "ecg_posterior": "posterior ECG (V7-V9)", "pocus": "bedside ultrasound (POCUS)",
    "chest_xray": "chest X-ray", "ctpa": "CT pulmonary angiography",
    "renal_ultrasound": "renal tract ultrasound",
    "efast": "extended FAST", "pelvis_xray": "pelvis X-ray",
    "basic_labs": "basic laboratory panel", "poc_glucose": "capillary glucose",
    "troponin": "troponin", "lactate": "lactate", "hemoglobin": "haemoglobin",
    "blood_cultures": "blood cultures", "urinalysis": "urinalysis",
    "temperature": "temperature", "abg": "arterial blood gas", "vbg": "venous blood gas",
    "blood_gas": "blood gas", "liver_panel": "liver panel",
    # Printed as "head ct" and "d dimer" until 2026-09-24: every study the
    # parser recognises has a bedside name.
    "head_ct": "head CT", "abdominal_ct": "abdominal CT", "d_dimer": "D-dimer",
    "cortisol": "cortisol", "thyroid_function": "thyroid function tests",
    "ketones": "ketones", "toxicology": "toxicology screen",
    "crossmatch": "blood group and crossmatch",
}
_ALREADY_IN_PLACE = re.compile(
    r"already (?:in place|contacted|requested|running)|not repeated", re.I)
_SUPPORT_NAMES = {
    "vascular_access": "peripheral IV access", "monitoring": "continuous monitoring and pulse oximetry",
    "urinary_catheter": "urinary catheter", "gastric_tube": "gastric tube", "npo": "nil by mouth",
    "oxygen": "oxygen", "niv": "non-invasive ventilation", "invasive_ventilation": "invasive ventilation",
    "bag_mask": "bag-mask ventilation", "disposition": "admission",
}


# A result key carries its unit as a suffix; a report has to print the unit.
_UNIT_SUFFIX = (
    ("_mmol_l", "mmol/L"), ("_mg_dl", "mg/dL"), ("_ng_l", "ng/L"), ("_ng_ml", "ng/mL"),
    ("_g_dl", "g/dL"), ("_mm_hg", "mmHg"), ("_cm_h2o", "cm H2O"), ("_l_min", "L/min"),
    ("_ml_h", "mL/h"), ("_percent", "%"), ("_c", "\u00b0C"), ("_s", "s"), ("_min", "min"),
    ("_cm", "cm"), ("_mm", "mm"), ("_j", "J"), ("_ma", "mA"),
)


def result_field(key, value):
    """``lactate_mmol_l: 3.2`` reads as ``lactate 3.2 mmol/L``."""
    name = str(key or "")
    unit = ""
    for suffix, written in _UNIT_SUFFIX:
        if name.endswith(suffix) and len(name) > len(suffix):
            name, unit = name[: -len(suffix)], written
            break
    label = _STUDY_NAMES.get(name, name.replace("_", " ")).strip()
    text = str(value if value is not None else "").strip()
    return " ".join(bit for bit in (label, text, unit) if bit)


def study_name(key):
    """The bedside name of a study, for a report a clinician reads."""
    return _STUDY_NAMES.get(str(key or ""), str(key or "study").replace("_", " "))


def _number(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return None if number != number or number in (float("inf"), float("-inf")) else number


def _amount(value, unit):
    number = _number(value)
    return f"{number:g} {unit}" if number is not None else ""


def _timing(action):
    """Delivery time and availability, which are clinical, not bookkeeping."""
    bits = []
    over = _number(action.get("administration_duration_min"))
    if over:
        bits.append(f"over {over:g} min")
    result = action.get("result") if isinstance(action.get("result"), dict) else {}
    available = _number(result.get("time_min"))
    if available is not None:
        bits.append(f"result at {available:g} min")
    elif action.get("type") == "diagnostic":
        duration = _number(action.get("duration_min"))
        if duration:
            bits.append(f"takes {duration:g} min")
    return bits


def action_phrase(action):
    """One executed action, written the way it was ordered.

    Doses, routes, settings and timings are kept; the engine's bookkeeping
    fields are not. An action this function does not know is described by its
    own label rather than by its field dump.
    """
    if not isinstance(action, dict):
        return ""
    # The engine already writes the plain sentence for something that was
    # standing rather than started. Found 2026-09-23: an intravenous line
    # recorded as "already in place; not repeated" was printed as "(started)".
    label = " ".join(str(action.get("label") or "").split())
    if label and _ALREADY_IN_PLACE.search(label):
        return label[:1].upper() + label[1:]
    kind = str(action.get("type") or action.get("support_type") or "").strip()
    route = _ROUTES.get(str(action.get("route") or ""), str(action.get("route") or ""))
    operation = _OPERATION.get(str(action.get("operation") or ""), "")
    timing = _timing(action)

    if kind == "diagnostic":
        key = str(action.get("diagnostic") or action.get("diagnostic_type") or "study")
        phrase = _STUDY_NAMES.get(key, key.replace("_", " ")) + " requested"
    elif kind == "reassessment":
        delay = _number(action.get("delay_min"))
        phrase = "reassessment" + (f" after {delay:g} min" if delay is not None else "")
    elif kind == "fluid":
        volume = _amount(action.get("volume_ml"), "mL")
        fluid = str(action.get("fluid_type") or "fluid")
        phrase = " ".join(bit for bit in (volume, fluid, route) if bit)
        if operation == "stopped":
            phrase = f"{fluid} infusion stopped"
    elif kind in {"disposition"}:
        destination = str(action.get("destination") or "")
        phrase = "discharge home" if destination == "home" else f"admission to {destination or 'a ward'}"
    elif kind in {"consult", "reperfusion_referral"}:
        phrase = f"{action.get('service') or action.get('destination') or 'specialty'} contacted"
    elif kind == "cardioversion":
        phrase = "synchronized cardioversion " + _amount(action.get("energy_j"), "J")
    elif kind == "oxygen" or action.get("support_type") == "oxygen":
        flow = _amount(action.get("flow_lpm") or action.get("flow_l_min"), "L/min")
        device = str(action.get("device") or "").strip()
        phrase = " ".join(bit for bit in ("oxygen", flow, f"via {device}" if device else "") if bit)
    elif kind == "niv" or action.get("support_type") == "niv":
        settings = [_amount(action.get("ipap_cmh2o"), "cm H2O IPAP"),
                    _amount(action.get("epap_cmh2o"), "cm H2O EPAP"),
                    _amount(action.get("fio2_percent"), "% FiO2")]
        phrase = "non-invasive ventilation " + ", ".join(bit for bit in settings if bit)
    elif kind == "invasive_ventilation" or action.get("support_type") == "invasive_ventilation":
        settings = [str(action.get("ventilator_mode") or "").strip(),
                    _amount(action.get("fio2_percent"), "% FiO2"),
                    _amount(action.get("peep_cmh2o"), "cm H2O PEEP")]
        phrase = "invasive ventilation " + ", ".join(bit for bit in settings if bit)
    elif kind == "transcutaneous_pacing":
        settings = [_amount(action.get("rate_per_min"), "/min"), _amount(action.get("output_ma"), "mA")]
        phrase = "transcutaneous pacing " + ", ".join(bit for bit in settings if bit)
    elif action.get("rate") is not None or action.get("rate_mcg_min") is not None:
        agent = str(action.get("agent") or kind).replace("_", " ")
        rate = (_amount(action.get("rate_mcg_min"), "mcg/min") if action.get("rate_mcg_min") is not None
                else f"{_number(action.get('rate')):g} {action.get('units') or ''}".strip())
        phrase = " ".join(bit for bit in (agent, rate, route) if bit)
    elif action.get("agent") or action.get("dose_mg") is not None or action.get("dose_g") is not None:
        agent = str(action.get("agent") or action.get("agent_name") or kind).replace("_", " ")
        dose = (_amount(action.get("dose_g"), "g") if action.get("dose_g") is not None
                else _amount(action.get("dose_mg"), "mg") if action.get("dose_mg") is not None
                else _amount(action.get("dose"), str(action.get("units") or "")).strip())
        phrase = " ".join(bit for bit in (agent, dose, route) if bit)
    elif kind in _SUPPORT_NAMES:
        phrase = _SUPPORT_NAMES[kind]
    else:
        phrase = str(action.get("label") or kind or "action").replace("_", " ")

    # A compound order (induction, sedation) carries its own drug list; the
    # drugs given are the clinical content and must not be summarised away.
    given = []
    for medication in action.get("medications") or []:
        if not isinstance(medication, dict):
            continue
        name = str(medication.get("agent") or "").replace("_", " ")
        dose = (_amount(medication.get("dose_g"), "g") if medication.get("dose_g") is not None
                else _amount(medication.get("dose_mg"), "mg") if medication.get("dose_mg") is not None
                else _amount(medication.get("dose"), str(medication.get("units") or "")).strip())
        way = _ROUTES.get(str(medication.get("route") or ""), str(medication.get("route") or ""))
        written = " ".join(bit for bit in (name, dose, way) if bit)
        if written:
            given.append(written)
    if given:
        phrase = f"{phrase} with " + " + ".join(given)

    phrase = " ".join(phrase.split())
    if operation and operation not in phrase and kind not in {"diagnostic", "reassessment", "disposition", "consult"}:
        phrase = f"{phrase} ({operation})"
    if action.get("repeated"):
        phrase += " — already in place, not repeated"
    if timing:
        phrase += " · " + ", ".join(timing)
    if not phrase:
        return ""
    return phrase if phrase[:2].isupper() else phrase[:1].upper() + phrase[1:]


def action_lines(actions):
    """Every executed action of one decision, deduplicated, in order.

    A ``procedure`` summary is the engine narrating what happened ("the monitor
    watches the patient and treats nothing"), not something the resident wrote;
    it belongs to the recorded response, not to the list of orders.
    """
    seen, lines = set(), []
    for action in actions or []:
        if isinstance(action, dict) and action.get("type") == "procedure":
            continue
        phrase = action_phrase(action)
        if phrase and phrase not in seen:
            seen.add(phrase)
            lines.append(phrase)
    return lines


def understood_but_not_executed(event):
    """Orders the engine read in this submission that produced no action.

    A request is not an execution, and an execution is not a result. Found
    2026-09-23 reading D4 of the demonstration encounter: the resident asked
    for a control lactate, the engine understood it, and no lactate was drawn,
    yet the analysis read the missing value as monitoring the resident had
    failed to do.
    """
    if not isinstance(event, dict):
        return []
    executed = set()
    for action in (event.get("executed_actions") or event.get("action_summaries") or []):
        if not isinstance(action, dict):
            continue
        key = action.get("diagnostic") or action.get("diagnostic_type")
        executed.add(("diagnostic", str(key)) if key else (str(action.get("type") or ""), ""))
    missing = []
    for action in event.get("interpreted_action") or []:
        if not isinstance(action, dict):
            continue
        kind = str(action.get("type") or "")
        if kind in {"reassessment", "clarification"}:
            continue
        key = action.get("diagnostic") or action.get("diagnostic_type")
        signature = ("diagnostic", str(key)) if key else (kind, "")
        if signature in executed:
            continue
        name = study_name(key) if key else kind.replace("_", " ")
        if name and (signature, name) not in [(s, n) for s, n in missing]:
            missing.append((signature, name))
    return missing


def order_fates(trace):
    """For every decision, what became of each order the engine understood.

    Four states, which the record distinguishes and a reader must not confuse:
    executed here, executed later in the encounter, never executed, and never
    executed because the encounter ended first.
    """
    trace = [event for event in (trace or []) if isinstance(event, dict)]
    executed_later = {}
    for position, event in enumerate(trace):
        for action in (event.get("executed_actions") or event.get("action_summaries") or []):
            if not isinstance(action, dict):
                continue
            key = action.get("diagnostic") or action.get("diagnostic_type")
            signature = ("diagnostic", str(key)) if key else (str(action.get("type") or ""), "")
            executed_later.setdefault(signature, []).append((position, action))
    closes = [_number(event.get("response_time_min")) for event in trace]
    close = max([minute for minute in closes if minute is not None] or [None]) if trace else None
    fates = {}
    for position, event in enumerate(trace):
        lines = []
        for signature, name in understood_but_not_executed(event):
            later = [(index, action) for index, action in executed_later.get(signature, []) if index > position]
            if later:
                index, action = later[0]
                result = action.get("result") if isinstance(action.get("result"), dict) else {}
                minute = result.get("time_min")
                when = f" at {float(minute):g} min" if isinstance(minute, (int, float)) else ""
                number = decision_ordinals(trace).get(index)
                under = f", under decision {number}" if number else ""
                lines.append(f"{name}: requested here; the result was reported{when}{under}")
            else:
                # No inference about why. The time the encounter closed is the
                # fact a reader needs to tell a missing result from an omission.
                ending = f" before the encounter closed at {close:g} min" if close is not None else ""
                lines.append(f"{name}: requested; no result was recorded{ending}")
        fates[f"trace:{position}"] = lines
    return fates


# --- corrections to the model's own text, applied in the open ---------------

class CorrectionLog:
    """Applies recorded factual corrections and remembers which ones landed.

    The saved analysis is never modified. A correction is an exact substring
    written for one passage, so it applies to that passage or to nothing, and
    the document that used it lists what was corrected and why.

    Given ``references`` -- the labels of one encounter, from
    ``reference_labels`` -- it also writes the internal identifiers a model
    left in its prose back as what they point to (faculty review 2026-09-24).
    That runs after the corrections, because a correction is written against
    the stored words.
    """

    def __init__(self, corrections=None, references=None, language="en"):
        self.corrections = [c for c in (corrections or []) if isinstance(c, dict)]
        self.applied = []
        self.references = references
        self.language = language
        self.unresolved = []

    def __call__(self, text):
        result, applied = apply_corrections(text, self.corrections)
        for correction in applied:
            if correction not in self.applied:
                self.applied.append(correction)
        if self.references is not None:
            result = humanize(result, self.references, self.language, self.unresolved)
        return result

    def lines(self):
        return [f"{c.get('reason') or 'factual correction'}"
                for c in self.applied]


# --- identifiers the model wrote into its prose ------------------------------
#
# Faculty review of 2026-09-24, across the 45 documents of a batch: no empty
# page, no cut text, and two kinds of internal name inside the sentences a
# model wrote -- ``trace:0`` for a decision the same document calls
# "D1 · 00:04", and ``unasked_history_topics``, the name of an input field.
# The citation fields were already written as labels; the prose was not.
#
# One conversion, used by every renderer, from the encounter's own map. A
# decision's number is its place among the decisions the resident actually
# made, never its position in the stored list plus one: the list also holds
# questions, examinations and orders that were not executed.

REFERENCE_UNAVAILABLE = {"en": "reference unavailable", "es": "referencia no disponible"}
# A decision or an encounter record is a number; a reflection is its review key.
_REFERENCE = re.compile(
    r"`?(?<![\w:/-])(?:(trace|encounter):(\d+)|(reflection):([A-Za-z0-9](?:[A-Za-z0-9_-]*[A-Za-z0-9])?))"
    r"(?![\w-])`?")
# Field names a model has been seen, or could be expected, to copy from its
# input. What each means, in each language -- and no more than what it means:
# "history topics not explored" is not "a relevant omission".
FIELD_PHRASES = {
    "unasked_history_topics": ("history topics not explored", "antecedentes no explorados"),
    "history_topics_offered": ("history topics the case offers", "temas de anamnesis que ofrece el caso"),
    "history_obtained": ("history obtained", "anamnesis obtenida"),
    "history_availability": ("history availability", "disponibilidad de la anamnesis"),
    "decision_events": ("the recorded decisions", "las decisiones registradas"),
    "recorded_reasoning": ("the recorded reasoning", "el razonamiento registrado"),
    "learner_input": ("the resident's entry", "la entrada del residente"),
    "interpreted_actions": ("the orders as understood", "las órdenes interpretadas"),
    "interpreted_action": ("the orders as understood", "las órdenes interpretadas"),
    "executed_action_summaries": ("the executed orders", "las órdenes ejecutadas"),
    "execution_status": ("the execution status", "el estado de ejecución"),
    "state_before": ("the state before the decision", "el estado antes de la decisión"),
    "state_after": ("the state after the decision", "el estado después de la decisión"),
    "diagnostics_available": ("the results available", "los resultados disponibles"),
    "results_pending": ("the results pending", "los resultados pendientes"),
    "information_available_on_asking": ("the information available on asking",
                                        "la información disponible al preguntar"),
    "information_on_asking_rule": ("the rule on information available on asking",
                                   "la regla de la información disponible al preguntar"),
    "defined_critical_events": ("the critical events defined for the case",
                                "los eventos críticos definidos para el caso"),
    "case_opportunities": ("the opportunities the case declares",
                           "las oportunidades que declara el caso"),
    "case_information_available": ("the information the case makes available",
                                   "la información que el caso pone a disposición"),
    "engine_limitations": ("the simulator's limitations", "las limitaciones del simulador"),
    "record_screening": ("the record check", "la verificación del registro"),
    "acceptable_alternatives": ("the acceptable alternatives", "las alternativas aceptables"),
    "evidence_refs": ("the cited evidence", "la evidencia citada"),
    "evidence_ref": ("the cited evidence", "la evidencia citada"),
    "learner_evidence": ("the resident's words", "las palabras del residente"),
    "reflection_decision_links": ("the reflections and the decisions they discuss",
                                  "las reflexiones y las decisiones que comentan"),
    "recorded_reflections": ("the recorded reflections", "las reflexiones registradas"),
    "later_expert_comparison_responses": ("the later comparison with the expert",
                                          "la comparación posterior con el experto"),
    "later_adaptation_plan": ("the later adaptation plan", "el plan de adaptación posterior"),
    "assistance_context": ("the assistance context", "el contexto de asistencia"),
    "assistance_provenance": ("where the assistance context came from",
                              "la procedencia del contexto de asistencia"),
    "management_trace": ("the Management Trace", "el Management Trace"),
    "reasoning_gate": ("the reasoning check", "la verificación del razonamiento"),
    "decision_time_min": ("the decision time", "la hora de la decisión"),
    "response_time_min": ("the response time", "la hora de la respuesta"),
    "airway_prepared": ("airway preparation", "la preparación de la vía aérea"),
}
_FIELD = re.compile(r"`?\b(" + "|".join(sorted(map(re.escape, FIELD_PHRASES), key=len, reverse=True))
                    + r")\b`?")
# Whole phrases whose field name also carries a value: rewriting the name alone
# would leave "airway preparation remained false", which says something else.
PHRASE_REWRITES = (
    (re.compile(r"`?airway_prepared`?\s+(?:remained|was|stayed)\s+false", re.I),
     ("airway preparation was not marked as completed",
      "la preparación de la vía aérea no quedó marcada como completada")),
)


def _clock(value):
    number = _number(value)
    if number is None or number < 0:
        return None
    minute = int(number)
    return f"{minute // 60:02d}:{minute % 60:02d}"


def decision_ordinals(trace):
    """``{stored position: decision number}`` for the decisions the resident made."""
    ordinals, count = {}, 0
    for position, event in enumerate(trace or []):
        if isinstance(event, dict) and event.get("execution_status") in (None, "executed", "terminal_locked"):
            count += 1
            ordinals[position] = count
    return ordinals


def carried_decision(carried_from, trace):
    """The decision number an interpretation was first stated in.

    Records saved before 2026-09-24 wrote the stored position plus one; newer
    ones write the decision number and keep the position beside it. Both are
    resolved against the trace, so an old record prints the right decision too.
    """
    carried_from = carried_from if isinstance(carried_from, dict) else {}
    ordinals = decision_ordinals(trace)
    position = carried_from.get("trace_index")
    if isinstance(position, int) and not isinstance(position, bool):
        return ordinals.get(position)
    decision = carried_from.get("decision")
    if isinstance(decision, int) and not isinstance(decision, bool) and decision >= 1:
        return ordinals.get(decision - 1)
    return None


def reference_labels(trace=None, encounter_events=None):
    """The real label of every reference one encounter can be cited by.

    ``{"trace:4": {"en": "D2 · 00:04", "es": "D2 · 00:04"}, ...}``. A decision is
    numbered by its place among executed decisions -- the same ordinal the
    evidence selector, the trace and the review use. An entry that was not a
    decision is named for what it was. A reflection written about decisions is
    named by them. Anything this map does not hold is unavailable, and is
    said to be.
    """
    labels = {}
    ordinal = 0
    for position, event in enumerate(trace or []):
        if not isinstance(event, dict):
            continue
        status = event.get("execution_status")
        clock = _clock(event.get("decision_time_min"))
        at = f" · {clock}" if clock else ""
        if status in (None, "executed", "terminal_locked"):
            ordinal += 1
            label = {"en": f"D{ordinal}{at}", "es": f"D{ordinal}{at}"}
        elif status == "information":
            label = {"en": f"information obtained{at}", "es": f"información obtenida{at}"}
        else:
            label = {"en": f"order not executed{at}", "es": f"orden no ejecutada{at}"}
        labels[f"trace:{position}"] = label
    for position, event in enumerate(encounter_events or []):
        if not isinstance(event, dict):
            continue
        clock = _clock(event.get("time_min"))
        at = f" · {clock}" if clock else ""
        labels[f"encounter:{position}"] = {"en": f"encounter record{at}",
                                           "es": f"registro del encuentro{at}"}
    return labels


def _reflection_label(key):
    """``decision-3`` and ``decisions-2-3`` are display ordinals, as the review writes them."""
    single = re.fullmatch(r"decision[-_](\d+)", key or "")
    if single:
        return {"en": f"later reflection on D{single.group(1)}",
                "es": f"reflexión posterior sobre D{single.group(1)}"}
    span = re.fullmatch(r"decisions[-_](\d+)[-_](\d+)", key or "")
    if span:
        return {"en": f"later reflection on D{span.group(1)}-D{span.group(2)}",
                "es": f"reflexión posterior sobre D{span.group(1)}-D{span.group(2)}"}
    return None


def humanize(text, labels, language="en", unresolved=None):
    """Write every internal identifier in a passage as what it points to.

    Whole tokens only: ``trace:1`` is never read inside ``trace:10``. A
    reference this encounter cannot resolve becomes "reference unavailable"
    and is added to ``unresolved`` -- never guessed at. The language is the
    passage's own: an English sentence keeps English words, because a Spanish
    phrase inside an English sentence is the mixed sentence decision 16 refused.
    """
    lang = "es" if language == "es" else "en"
    labels = labels or {}

    def reference(match):
        kind = match.group(1) or match.group(3)
        key = match.group(2) or match.group(4)
        token = f"{kind}:{key}"
        label = labels.get(token)
        if label is None and kind == "reflection":
            label = _reflection_label(key)
        if label is None:
            if unresolved is not None and token not in unresolved:
                unresolved.append(token)
                import logging
                logging.getLogger("mrs.references").warning(
                    "An internal reference in model prose could not be resolved: %s", token)
            return REFERENCE_UNAVAILABLE[lang]
        return label[lang]

    result = _REFERENCE.sub(reference, str(text or ""))
    for pattern, replacement in PHRASE_REWRITES:
        result = pattern.sub(replacement[1 if lang == "es" else 0], result)
    return _FIELD.sub(lambda match: FIELD_PHRASES[match.group(1)][1 if lang == "es" else 0], result)


def apply_corrections(text, corrections):
    """Replace a model sentence that the record does not support.

    Corrections are exact substrings, never patterns, so a correction either
    applies to the text it was written for or does not apply at all. The
    original analysis is never modified; this runs at render time and every
    applied correction is reported in the document.
    """
    applied = []
    result = str(text or "")
    for correction in corrections or []:
        original = str((correction or {}).get("original") or "")
        replacement = str((correction or {}).get("replacement") or "")
        if original and original in result:
            result = result.replace(original, replacement)
            applied.append(correction)
    return result, applied


# --- what the record does and does not establish ----------------------------

NOT_REQUESTED = "Not requested in this encounter"
REQUESTED_NOT_EXECUTED = "Requested but not executed"
PENDING_AT_CLOSE = "Still pending when the encounter closed"
RESULT_NOT_RECORDED = "Requested; no result recorded"
NOT_OBSERVED = "No opportunity to demonstrate in this encounter"


def study_status(action, closed_at_min=None):
    """Distinguish an order never given from one given whose result never came."""
    if not isinstance(action, dict):
        return NOT_REQUESTED
    result = action.get("result") if isinstance(action.get("result"), dict) else None
    if result:
        available = _number(result.get("time_min"))
        if available is None:
            return RESULT_NOT_RECORDED
        if closed_at_min is not None and available > closed_at_min:
            return PENDING_AT_CLOSE
        return ""
    return RESULT_NOT_RECORDED
