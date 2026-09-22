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
    "basic_labs": "basic laboratory panel", "poc_glucose": "capillary glucose",
    "troponin": "troponin", "lactate": "lactate", "hemoglobin": "haemoglobin",
    "blood_cultures": "blood cultures", "urinalysis": "urinalysis",
    "temperature": "temperature", "abg": "arterial blood gas", "vbg": "venous blood gas",
    "blood_gas": "blood gas", "liver_panel": "liver panel",
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
                lines.append(f"{name}: requested here; the result was reported{when}, under decision {index + 1}")
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
    """

    def __init__(self, corrections=None):
        self.corrections = [c for c in (corrections or []) if isinstance(c, dict)]
        self.applied = []

    def __call__(self, text):
        result, applied = apply_corrections(text, self.corrections)
        for correction in applied:
            if correction not in self.applied:
                self.applied.append(correction)
        return result

    def lines(self):
        return [f"{c.get('reason') or 'factual correction'}"
                for c in self.applied]


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
