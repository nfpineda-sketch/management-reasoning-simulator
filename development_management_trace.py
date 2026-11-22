"""P3-504, P3-505, P3-509 and P3-512: the DEVELOPMENT MANAGEMENT TRACE of the GI haemorrhagic-shock development encounter (pure: no Streamlit, no engine, no authority, no common core).

WHAT IT IS. A faculty-facing, structured reading of ONE encounter, derived from the runtime events of that encounter and nothing else:

    STATE -> PRIORITY -> ACTION -> EXPECTED EFFECT -> OBSERVED RESPONSE -> REASSESSMENT -> NEW STATE

one step per turn. It is DERIVED, never primary: the resident's record is the page's own Management Trace (``management_trace_v1`` with its Phase-0 extensions), the authority's record is its sealed artifact, and
this module only reads both. It invents nothing: a field the runtime did not produce is ``UNKNOWN``, a reasoning the resident did not express is ``NOT_EXPRESSED``, and a scenario priority written for a development
path is stored APART from the resident's, under its own provenance.

WHAT EACH FIELD IS. Every value carries one provenance class and they are never collapsed:

* ``OBSERVED``           -- produced by the runtime of THIS encounter: the clock, the order ledger, the pressure the live development authority committed, what the resident could see;
* ``AUTHORED``           -- written before the encounter: the case's arrival, a scripted development action, a scenario priority or category proposed for faculty review;
* ``MODEL_DERIVED``      -- a fixed reading of what the ratified development model represents (an expected effect of an action class) or a fixed-threshold label of an observed number;
* ``FACULTY_DEFINED``    -- a decision the faculty made (the development boundary itself, FD-MTRACE-05);
* ``RESIDENT_EXPRESSED`` -- what the resident typed or answered, read from the page's own record;
* ``UNKNOWN``            -- the runtime did not say.

WHAT IT NEVER SAYS. A reading is a direction, a threshold and a caveat: "rose", "fell", "still hypotensive", "temporary pressure support". It never says "resuscitated", "shock corrected", "bleeding controlled",
"stable" or "recovered" (``claim_problems`` refuses them), and it never reads a vasopressor's pressure as control of the bleeding: the bleeding is not controlled in this encounter, and every step says so.

THE BOUNDARY (FD-MTRACE-05, P3-504). The encounter ends, deterministically, at the first of: a request for definitive control of the bleeding; an engine event of haemostasis (defence in depth); a stop of the live
authority (its own effective stop, with its own stop class); a terminal state of the legacy engine; or the development horizon. The boundary means "development model boundary" and nothing else.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Mapping, Sequence

import reasoning_provenance as slots

VERSION = "MTRACE-1"
SCHEMA = "gi_development_management_trace_v1"
RECORD_TYPE = "PHASE3_GI_DEVELOPMENT_MANAGEMENT_TRACE"

# -- provenance -------------------------------------------------------------------------------------------------------------------------------------------------------------------
OBSERVED, AUTHORED, MODEL_DERIVED, FACULTY_DEFINED, RESIDENT_EXPRESSED, UNKNOWN = ("OBSERVED", "AUTHORED", "MODEL_DERIVED", "FACULTY_DEFINED", "RESIDENT_EXPRESSED", "UNKNOWN")
PROVENANCE = (OBSERVED, AUTHORED, MODEL_DERIVED, FACULTY_DEFINED, RESIDENT_EXPRESSED, UNKNOWN)
NOT_EXPRESSED = "NOT_EXPRESSED"
PROVENANCE_LEGEND = {
    OBSERVED: "produced by the runtime of this encounter (clock, order ledger, committed authority pressure, what the resident could see)",
    AUTHORED: "written before the encounter (the case's arrival, a scripted development action, a scenario priority or category proposed for faculty review)",
    MODEL_DERIVED: "a fixed reading of what the ratified development model represents, or a fixed-threshold label of an observed number",
    FACULTY_DEFINED: "a decision the faculty made",
    RESIDENT_EXPRESSED: "what the resident typed or answered, read from the page's own record",
    UNKNOWN: "the runtime did not say",
}
#: Where the source of a step's text is a scripted development path (no resident typed it) or the page's own record (a resident did).
SCRIPTED, PAGE = "SCRIPTED_DEVELOPMENT_PATH", "PAGE_MANAGEMENT_TRACE"

# -- the development encounter (P3-504) ---------------------------------------------------------------------------------------------------------------------------------------------
ENCOUNTER_ID = "GI_HAEMORRHAGE_INITIAL_RESUSCITATION_DEVELOPMENT_ENCOUNTER_V1"
CASES = ("gi_bleed_57m", "gi_bleed_72f")
#: The development horizon: two hours from the authored arrival. AUTHORED for this package (FD-MTRACE-05 decides THAT there is a boundary; the number is proposed for faculty review): it covers the initial
#: resuscitation, at least one vasopressor start, titration and reassessment cycle, and the erosion of early gains under continuing bleeding, and ends before the course depends on definitive haemostasis.
HORIZON_MIN = 120
HORIZON_PROVENANCE = AUTHORED
ENTRY_CONDITIONS = (
    "an authored arrival of gi_bleed_57m or gi_bleed_72f, at minute 0, with no order executed",
    "the live development authority of the GI pressure open on that arrival under the norepinephrine development grant (the ratified pressure and tone snapshots)",
)
#: The exits, in the order they are tested after every turn. The first that holds is the boundary.
EXIT_DEFINITIVE_HAEMOSTASIS = "DEFINITIVE_HAEMOSTASIS_REQUESTED"
EXIT_HAEMOSTASIS_EVENT = "ENGINE_HAEMOSTASIS_EVENT"
EXIT_AUTHORITY_STOP = "AUTHORITY_STOP"
EXIT_TERMINAL = "LEGACY_TERMINAL_STATE"
EXIT_HORIZON = "DEVELOPMENT_HORIZON"
EXITS = (EXIT_DEFINITIVE_HAEMOSTASIS, EXIT_HAEMOSTASIS_EVENT, EXIT_AUTHORITY_STOP, EXIT_TERMINAL, EXIT_HORIZON)
EXIT_CONDITIONS = {
    EXIT_DEFINITIVE_HAEMOSTASIS: "a request for definitive control of the bleeding (a consultation of gastroenterology, surgery or interventional radiology, an endoscopy or an embolization), whatever the order "
                                 "ledger did with it (executed, recorded but not modelled, or not recognized): the boundary is the minute the request was made, and nothing after it belongs to the development "
                                 "encounter",
    EXIT_HAEMOSTASIS_EVENT: "an engine event reporting endoscopic control of the bleeding (defence in depth: the first exit comes before it): the boundary is the minute of the turn that carried it",
    EXIT_AUTHORITY_STOP: "the live development authority stopped (its own effective stop and stop class: collapse boundary, unsupported or malformed order, any hard failure): the boundary is the minute of the "
                         "turn it stopped in, and no turn after it belongs to the development encounter",
    EXIT_TERMINAL: "the legacy engine locked the encounter as terminal",
    EXIT_HORIZON: f"the clock reached minute {HORIZON_MIN}",
}
DEFINITIVE_SERVICES = ("gastroenterology", "surgery", "interventional radiology", "interventional_radiology")
#: The words of a request for definitive control of the bleeding, read on the order's own span and canonical form (never on the whole turn: "transfuse for the GI bleed" is not a request). A negated mention
#: ("no endoscopy yet") also matches: the boundary then comes EARLIER, the conservative direction for FD-MTRACE-05.
DEFINITIVE_WORDS = re.compile(r"\b(?:gi|gastro\w*|endoscop\w*|egd|ogd|scope|interventional\s+radiolog\w*|ir|emboli[sz]\w*|surg\w*|haemostas\w*|hemostas\w*)\b", re.I)
#: The order classes such a request can come as. A fluid, a drug or a reassessment that names the bleed is not one.
DEFINITIVE_CLASSES = ("consult", "endoscopy", "procedure", "plan", "unrecognized")
BOUNDARY_MESSAGE = ("Development model boundary. This development encounter covers only the initial resuscitation of an upper gastrointestinal bleed, up to two hours after arrival. The bleeding has not been "
                    "controlled in this encounter: definitive control of the bleeding source is outside this development model. Reaching this point does not mean that the patient has recovered, that the "
                    "bleeding has stopped, that management is complete, or that discharge is safe.")
BOUNDARY_MESSAGE_REQUEST = ("Development model boundary. The request for definitive control of the bleeding has been recorded. What follows it is outside this development model, so the development encounter ends "
                            "here. The bleeding has not been controlled in this encounter. Reaching this point does not mean that the patient has recovered, that the bleeding has stopped, that management is "
                            "complete, or that discharge is safe.")
AUTHORITY_STOP_MESSAGE = ("The development experiment stopped for an operational reason, before the development boundary. This is not a statement about the patient and not a judgement of the management.")
HAEMOSTASIS_EVENT_MESSAGE = ("Development model boundary. The legacy engine reported a procedure to control the bleeding. Definitive control of the bleeding is outside this development model and has not been "
                             "reviewed, so the development encounter ends here. Reaching this point does not mean that the patient has recovered, that the bleeding has stopped, that management is "
                             "complete, or that discharge is safe.")
TERMINAL_MESSAGE = ("The development encounter ended because the legacy engine closed the encounter. That closure is outside the development model under review and this trace does not interpret it. It is not "
                    "a judgement of the management.")
HORIZON_CROSSED_NOTE = " The last turn crossed the two-hour mark and is shown to its end."

# -- the timing contract (P3-509) ---------------------------------------------------------------------------------------------------------------------------------------------------
#: How long a turn lasts, read from the engine's own rule (``family_engine.execute_family_bundle``): a stated reassessment interval governs the turn; without one, the longest administration time of what was
#: given; information activities take their own minutes; a wait longer than the engine's step (120 min) is refused, never shortened. The pressure is OBSERVED at the end of every turn that moved the clock (one
#: committed authority minute per turn); the minutes inside a turn are validated by the authority but not observed.
TIMING_STATED, TIMING_ADMINISTRATION, TIMING_NONE = "STATED_REASSESSMENT_INTERVAL", "ADMINISTRATION_TIME_OF_WHAT_WAS_GIVEN", "NO_CLOCK_ADVANCE"

# -- the expected effect of each action class (MODEL_DERIVED: what the ratified development model represents; never a promise of magnitude) ----------------------------------------
EXPECTED = {
    "fluid": "Crystalloid adds circulating volume for a while; part of it leaves the circulation. It does not stop the bleeding.",
    "blood": "Red cells replace lost blood and support the pressure while they are given. They do not stop the bleeding.",
    "NE_START": "A vasopressor supports the pressure while it runs. It does not replace volume and does not stop the bleeding.",
    "NE_INCREASE": "More vasopressor support: the pressure may rise further while it runs. It does not replace volume and does not stop the bleeding.",
    "NE_DECREASE": "Less vasopressor support: the pressure it was supporting is expected to fall back.",
    "NE_STOP": "The vasopressor support wears off: the pressure it was supporting is expected to fall back.",
    "NE_UNCHANGED": "The vasopressor rate is unchanged.",
    "reassessment": "Time passes. The bleeding continues.",
    "vascular_access": "Vascular access only: no change in the patient is modelled.",
    "ppi": "Acid suppression: a modest reduction of the ongoing bleeding in this model. It is not control of the bleeding.",
    "consult_definitive": "Definitive control of the bleeding is outside this development model: the encounter reaches its boundary.",
    "consult": "A consultation is recorded: no change in the patient is modelled.",
}
NO_EXPECTATION = "No expected physiological effect is represented for this action in the development model."

# -- the fixed readings (MODEL_DERIVED labels of OBSERVED numbers) ------------------------------------------------------------------------------------------------------------------
HYPOTENSION_SBP, HYPOTENSION_MAP = 90, 65
CHANGE_MAP_MMHG = 3
ROSE, FELL, ABOUT_UNCHANGED = "ROSE", "FELL", "ABOUT_UNCHANGED"
LIMITATIONS = {
    "BLEEDING_NOT_CONTROLLED": "The bleeding continues throughout this development encounter: no step controls it.",
    "VASOPRESSOR_SUPPORT_IS_TEMPORARY": "While the vasopressor runs, part of the pressure is vasopressor support: it is temporary and it is not control of the bleeding.",
    "CONSCIOUSNESS_UNDER_TONE_UNRESOLVED": "Consciousness under vasopressor support is not represented by the development model: the mental status the page shows comes from the legacy engine and is not evidence of "
                                           "resuscitation.",
    "LEGACY_FIELDS_NOT_AUTHORITATIVE": "Only the blood pressure is produced by the development authority. Heart rate, mental status and the other findings come from the legacy engine and are not part of this trace's "
                                       "readings.",
    "OBSERVED_AT_REASSESSMENT_ONLY": "The pressure is observed at the end of each turn; the minutes between two reassessments are not observed.",
}
#: Words no generated reading may carry (FD-MTRACE-10). The boundary and limitation texts are fixed, reviewed constants that NEGATE these, and are not scanned.
FORBIDDEN_CLAIMS = re.compile(r"\bresuscitat(?:ed|ion (?:is )?(?:complete|successful|achieved))\b|\bsuccessful resuscitation\b|\bshock (?:is )?(?:corrected|resolved|reversed)\b|"
                              r"\bbleed(?:ing)? (?:is |has )?(?:controlled|stopped|resolved)\b|\bha?emostasis (?:is )?achieved\b|\bstabili[sz]ed\b|\bis stable\b|\brecovered\b|\bcured\b|"
                              r"\bsafe (?:for )?discharge\b|\bmanagement (?:is )?complete\b", re.I)


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def field(value: Any, provenance: str, source: str | None = None) -> dict:
    """One value with its provenance class (and, when it helps a reader, where it was read from)."""
    if provenance not in PROVENANCE:
        raise ValueError(f"unknown provenance {provenance!r}")
    return {"value": value, "provenance": provenance, **({"source": source} if source else {})}


def encounter_definition() -> dict:
    """The development encounter, as data: entry, exits, horizon, messages, timing contract, expectations, readings and limitations. Its digest binds every trace to the definition it was read with."""
    body = {"id": ENCOUNTER_ID, "version": VERSION, "family": "gi_bleed", "cases": list(CASES), "horizon_min": HORIZON_MIN, "horizon_provenance": HORIZON_PROVENANCE,
            "boundary_provenance": FACULTY_DEFINED, "entry": list(ENTRY_CONDITIONS), "exits": [{"id": key, "condition": EXIT_CONDITIONS[key]} for key in EXITS],
            "boundary_message": BOUNDARY_MESSAGE, "boundary_message_request": BOUNDARY_MESSAGE_REQUEST, "authority_stop_message": AUTHORITY_STOP_MESSAGE,
            "timing": [TIMING_STATED, TIMING_ADMINISTRATION, TIMING_NONE], "expected": dict(EXPECTED), "no_expectation": NO_EXPECTATION,
            "readings": {"hypotension": {"sbp_below": HYPOTENSION_SBP, "map_below": HYPOTENSION_MAP}, "change_map_mmhg": CHANGE_MAP_MMHG}, "limitations": dict(LIMITATIONS),
            "provenance_legend": dict(PROVENANCE_LEGEND)}
    return {**body, "definition_digest": digest(body)}


# -- the input: turns, as the runtime recorded them ------------------------------------------------------------------------------------------------------------------------------------
#: The fields a turn needs, under the names the page's ``management_trace_v1`` event uses. The headless development runner records the same fields from the same calls.
TURN_KEYS = ("text", "decision_minute", "response_minute", "executed", "terminal_locked", "orders", "events", "reasoning", "text_source")


#: The block the page APPENDS to the resident's entry after its reasoning gate: a labelled transcript the application formats from the gate's answers (and from a slot it composed). It is not what the resident
#: typed: the answers themselves reach the trace as reasoning, each under the page's own provenance. A "Reasoning clarification" the resident typed later stays in the text.
GUIDED_COMPLETION = re.compile(r"\n\nGuided reasoning completion: .*?(?=\n\nReasoning clarification: |\Z)", re.S)


def resident_text(learner_input: Any) -> str:
    """The resident's own entry of a page turn: the learner input without the transcript the page appended after its reasoning gate."""
    return GUIDED_COMPLETION.sub("", str(learner_input or ""))


def turn_from_page_event(event: Mapping) -> dict:
    """One turn read from the page's own Management Trace event (``management_trace_v1`` + ``phase0_v1``). The resident's reasoning is the page's parsed reasoning, exactly; nothing is added. The action text is the
    resident's own entry (``resident_text``): the transcript the page appends after its reasoning gate is the application's formatting, never the resident's words."""
    event = dict(event or {})
    status = str(event.get("execution_status") or "")
    return {"text": resident_text(event.get("learner_input")), "decision_minute": int(event.get("decision_time_min") or 0), "response_minute": int(event.get("response_time_min") or 0),
            "executed": status in ("executed",), "terminal_locked": status == "terminal_locked", "orders": [dict(order) for order in event.get("orders") or ()],
            "events": [dict(item) for item in event.get("events") or ()], "reasoning": dict(event.get("reasoning") or {}), "text_source": PAGE}


def turn_from_runner_entry(entry: Mapping) -> dict:
    """One turn read from the development runner's entry (the same fields ``pilot_acceptance.Encounter.order`` records). A scripted path expresses no reasoning: the field is empty, never filled in."""
    entry = dict(entry or {})
    return {"text": str(entry.get("text") or ""), "decision_minute": int(entry.get("decision_time_min") or 0), "response_minute": int(entry.get("response_time_min") or 0),
            "executed": bool(entry.get("executed")), "terminal_locked": bool(entry.get("terminal_locked")), "orders": [dict(order) for order in entry.get("orders") or ()],
            "events": [dict(item) for item in entry.get("events") or ()], "reasoning": {}, "text_source": SCRIPTED}


# -- the reading of one order ---------------------------------------------------------------------------------------------------------------------------------------------------------
def _executed(order: Mapping) -> bool:
    return str(order.get("fate") or "").upper() == "EXECUTED"


def is_definitive_request(order: Mapping) -> bool:
    """A request for definitive control of the bleeding (P3-504, first exit), WHATEVER the ledger did with it: executed, recorded but not modelled ("Consult GI.", "Consult interventional radiology for
    embolization."), held, or not recognized ("Page the gastroenterologist."). A request is the resident's decision; that the engine did not model it does not let the encounter go on past it."""
    kind = str(order.get("class") or "").lower()
    if kind in ("endoscopy", "procedure"):
        return True
    words = f"{order.get('canonical') or ''} {order.get('span') or ''}".replace("_", " ")
    return kind in DEFINITIVE_CLASSES and (bool(DEFINITIVE_WORDS.search(words)) or any(service.replace("_", " ") in words.lower() for service in DEFINITIVE_SERVICES))


def is_haemostasis_event(event: Mapping) -> bool:
    words = f"{event.get('label') or ''} {event.get('text') or ''} {event.get('type') or ''}".lower()
    return "endoscop" in words and ("controlled" in words or "treated" in words)


def _ne_operation(order: Mapping, running: float, ever: bool) -> tuple:
    """(operation, rate after) of one executed norepinephrine order, from the ledger's own words and rate. The operation is what the rate did, never what the words claim."""
    words = str(order.get("canonical") or "").lower()
    if "stop" in words:
        return ("NE_STOP" if running > 0 else "NE_UNCHANGED"), 0.0
    try:
        rate = float(order.get("rate"))
    except (TypeError, ValueError):
        return "NE_UNCHANGED", running
    if running <= 0:
        return ("NE_RESTART" if ever else "NE_START"), rate
    if rate > running:
        return "NE_INCREASE", rate
    if rate < running:
        return "NE_DECREASE", rate
    return "NE_UNCHANGED", rate


def _order_reading(order: Mapping, running: float, ever: bool) -> tuple:
    """(row, expected text, rate after) of one order. The row is OBSERVED (the ledger); the expectation is MODEL_DERIVED (or UNKNOWN when the model represents nothing for the class)."""
    kind = str(order.get("class") or "").lower()
    row = {"order_id": order.get("order_id"), "class": kind, "order": order.get("canonical") or order.get("span"), "fate": order.get("fate"), "rate_mcg_min": order.get("rate") if kind == "norepinephrine" else None}
    if not _executed(order):
        return row, None, running
    if kind == "norepinephrine":
        operation, after = _ne_operation(order, running, ever)
        row["operation"] = operation
        return row, EXPECTED["NE_START" if operation == "NE_RESTART" else operation], after
    if kind == "consult":
        return row, EXPECTED["consult_definitive" if is_definitive_request(order) else "consult"], running
    return row, EXPECTED.get(kind), running


def _pressure(point: Mapping | None) -> dict | None:
    if not point:
        return None
    try:
        return {"sbp": int(round(float(point["sbp"]))), "dbp": int(round(float(point["dbp"]))), "map": int(round(float(point["map"])))}
    except (KeyError, TypeError, ValueError):
        return None


def hypotensive(pressure: Mapping | None) -> bool | None:
    if not pressure:
        return None
    return pressure["sbp"] < HYPOTENSION_SBP or pressure["map"] < HYPOTENSION_MAP


def direction(before: Mapping | None, after: Mapping | None) -> str | None:
    if not before or not after:
        return None
    change = after["map"] - before["map"]
    return ROSE if change >= CHANGE_MAP_MMHG else FELL if change <= -CHANGE_MAP_MMHG else ABOUT_UNCHANGED


def pressure_text(pressure: Mapping | None) -> str:
    return f"BP {pressure['sbp']}/{pressure['dbp']} mmHg (MAP {pressure['map']})" if pressure else "pressure not observed"


def state_reading(pressure: Mapping | None, *, vasopressor_running: bool) -> str:
    """The fixed reading of a state (MODEL_DERIVED): the threshold, the bleeding and, when it runs, the vasopressor. Never a word of recovery."""
    if not pressure:
        return "Pressure not observed."
    parts = ["hypotensive (SBP below 90 mmHg or MAP below 65 mmHg)" if hypotensive(pressure) else "not hypotensive at this reading"]
    if vasopressor_running:
        parts.append("on vasopressor support (temporary)")
    parts.append("bleeding not controlled")
    return pressure_text(pressure) + " · " + " · ".join(parts) + "."


def reassessment_reading(before: Mapping | None, after: Mapping | None, *, vasopressor_running: bool) -> str:
    """The fixed reading of a reassessment (MODEL_DERIVED): the direction of the MAP since the last reading, the threshold, the vasopressor and the bleeding."""
    if not after:
        return "No new reading: the clock did not move."
    move = direction(before, after)
    change = (after["map"] - before["map"]) if before else 0
    words = {ROSE: f"MAP rose by {change} mmHg since the last reading", FELL: f"MAP fell by {-change} mmHg since the last reading",
             ABOUT_UNCHANGED: "MAP about unchanged since the last reading", None: "first reading"}[move]
    low_now, low_before = hypotensive(after), bool(before and hypotensive(before))
    parts = [words, ("still hypotensive" if low_before else "hypotensive (SBP below 90 mmHg or MAP below 65 mmHg)") if low_now else "not hypotensive at this reading"]
    if vasopressor_running:
        parts.append("the pressure is partly vasopressor support: temporary, not control of the bleeding")
    parts.append("the bleeding is not controlled in this encounter")
    return "; ".join(parts) + "."


#: The page's own record of where each slot came from (``reasoning_provenance``): what was written at a DIFFERENT moment keeps that label; what the APPLICATION composed is never the resident's.
SLOT_LABELS = {slots.COMPLETED: slots.LABELS[slots.COMPLETED], slots.CARRIED: slots.LABELS[slots.CARRIED], slots.SHARED: slots.LABELS[slots.SHARED],
               slots.RETROSPECTIVE: slots.LABELS[slots.RETROSPECTIVE]}
COMPOSED_NOTE = "a phrase the application composed from other words is not shown as the resident's"


def _resident(reasoning: Mapping, keys: Sequence[str]) -> dict:
    """What the resident expressed under any of ``keys``, exactly, or NOT_EXPRESSED. Never inferred from the action, and never what the application composed: the page marks a slot it phrased itself
    (``derived_slots`` / ``slot_provenance`` = composed) and that slot is NOT_EXPRESSED here, with a note. A slot written at another moment (carried from an earlier decision, shared with a plan, completed in the
    follow-up, written afterwards as a retrospective) is the resident's words under the page's own label for that moment."""
    reasoning = dict(reasoning or {})
    composed = {str(name) for name in reasoning.get("derived_slots") or ()}
    for key in keys:
        text = str(reasoning.get(key) or "").strip()
        if not text:
            continue
        slot = slots.of(reasoning, key)
        if key in composed or slot == slots.COMPOSED:
            return {**field(NOT_EXPRESSED, RESIDENT_EXPRESSED, f"reasoning.{key}"), "note": COMPOSED_NOTE}
        found = field(text, RESIDENT_EXPRESSED, f"reasoning.{key}")
        return {**found, "as": SLOT_LABELS[slot]} if slot in SLOT_LABELS else found
    return field(NOT_EXPRESSED, RESIDENT_EXPRESSED)


def _timing(orders: Sequence[Mapping], advanced: int) -> str:
    if advanced <= 0:
        return TIMING_NONE
    stated = any(str(order.get("class") or "") == "reassessment" and _executed(order) and dict(order.get("timing") or {}).get("delay_min") is not None for order in orders)
    return TIMING_STATED if stated else TIMING_ADMINISTRATION


# -- the extraction (P3-512) ---------------------------------------------------------------------------------------------------------------------------------------------------------------
def authority_points(artifact: Mapping | None) -> dict:
    """``{minute: {"pressure", "candidate_digest", "grant_id", "snapshot_id"}}`` of every minute the live authority COMMITTED, read from its artifact. Nothing else is a pressure transition of this trace, and a
    minute the authority committed and then DISOWNED (a later record of the same minute that is not a commit, e.g. a provenance contradiction found after the commit) is not one either."""
    points, disowned = {}, set()
    for record in list(dict(artifact or {}).get("minutes") or ()):
        record = dict(record or {})
        minute = int(record.get("minute") or 0)
        if not record.get("committed") or record.get("outcome") != "COMMITTED":
            if minute in points:
                disowned.add(minute)
            continue
        pressure = _pressure(record.get("written_candidate"))
        if pressure is None:
            continue
        points[minute] = {"pressure": pressure, "candidate_digest": record.get("candidate_digest"), "grant_id": record.get("grant_id"), "snapshot_id": record.get("snapshot_id")}
    return {minute: point for minute, point in points.items() if minute not in disowned}


def halt_minute(artifact: Mapping | None) -> int | None:
    """The minute of the turn the live authority stopped in (its first record that is not a commit), or None when it did not stop or left no record of where."""
    artifact = dict(artifact or {})
    if not artifact.get("halted"):
        return None
    stopped = [int(dict(record or {}).get("minute") or 0) for record in artifact.get("minutes") or () if dict(record or {}).get("outcome") != "COMMITTED"]
    return min(stopped) if stopped else None


#: What of an authority artifact the extraction reads, and nothing else: persisting this view with the turns is enough to re-extract the same trace after a restart (P3-512, P3-515 #10).
_VIEW_TOP = ("artifact_digest", "experiment_id", "encounter_id", "case_id", "authority_label", "snapshot_id", "halted", "halt_reason", "experiment_state")
_VIEW_MINUTE = ("minute", "committed", "outcome", "candidate_digest", "grant_id", "snapshot_id")


def artifact_view(artifact: Mapping | None) -> dict:
    """The part of an authority artifact the trace reads (its identity, grant, tone snapshot id, stop, and every minute record with its committed pressure). The full artifact stays the authority's record."""
    artifact = dict(artifact or {})
    grant = dict(artifact.get("grant") or {})
    tone = dict(dict(artifact.get("norepinephrine_authority") or {}).get("tone_configuration") or {})
    minutes = []
    for record in artifact.get("minutes") or ():
        record = dict(record or {})
        pressure = _pressure(record.get("written_candidate"))
        minutes.append({**{key: record.get(key) for key in _VIEW_MINUTE}, "written_candidate": pressure})
    return {**{key: artifact.get(key) for key in _VIEW_TOP}, "grant": {"grant_id": grant.get("grant_id"), "fingerprint": grant.get("fingerprint")},
            "norepinephrine_authority": {"tone_configuration": {"snapshot_id": tone.get("snapshot_id")}}, "minutes": minutes}


def authority_summary(artifact: Mapping | None) -> dict:
    """What of the artifact the trace binds: its identity, its grant, its snapshots, whether it stopped. No mechanism value (no tone value, no parameter) is copied."""
    artifact = dict(artifact or {})
    grant = dict(artifact.get("grant") or {})
    tone = dict(dict(artifact.get("norepinephrine_authority") or {}).get("tone_configuration") or {})
    return {"artifact_digest": artifact.get("artifact_digest"), "experiment_id": artifact.get("experiment_id"), "encounter_id": artifact.get("encounter_id"), "case_id": artifact.get("case_id"),
            "authority_label": artifact.get("authority_label"), "grant_id": grant.get("grant_id"), "grant_fingerprint": grant.get("fingerprint"), "snapshot_id": artifact.get("snapshot_id"),
            "tone_snapshot_id": tone.get("snapshot_id"), "halted": bool(artifact.get("halted")), "halt_reason": artifact.get("halt_reason") or "", "experiment_state": artifact.get("experiment_state")}


def extract(turns: Sequence[Mapping], artifact: Mapping | None, arrival: Mapping, *, scenario: Mapping | None = None) -> dict:
    """The trace of ONE encounter: its turns (as the runtime recorded them), the artifact of its live authority, and its authored arrival pressure. ``scenario`` (optional) carries what a development path
    AUTHORED -- its id, its plan digest, the priority written for each step and its proposed category -- and is stored apart from anything the resident expressed. Pure; deterministic; never raises on a
    well-formed input."""
    definition = encounter_definition()
    scenario = dict(scenario or {})
    priorities = {int(key): str(value) for key, value in dict(scenario.get("priorities") or {}).items()}
    points = authority_points(artifact)
    summary = authority_summary(artifact)
    stopped_at = halt_minute(artifact)
    start = _pressure(arrival)
    # what the resident sees now, with where it came from: the authored arrival until the live authority commits a minute; a turn that does not move the clock leaves it as it was
    last, last_source = start, (AUTHORED, "authored arrival")
    running, ever = 0.0, False
    steps, boundary = [], None
    beyond = field(None, UNKNOWN, "beyond the development boundary")
    for number, turn in enumerate(turns, 1):
        turn = dict(turn)
        decision, response = int(turn["decision_minute"]), int(turn["response_minute"])
        orders = [dict(order) for order in turn.get("orders") or ()]
        running_before = running
        rows, expectations = [], []
        for order in orders:
            row, expected, running_after = _order_reading(order, running, ever)
            if row["class"] == "norepinephrine" and _executed(order):
                ever = ever or running_after > 0
                running = running_after
            rows.append(row)
            if expected and expected not in expectations:
                expectations.append(expected)
        definitive = any(is_definitive_request(order) for order in orders)
        haemostasis = any(is_haemostasis_event(event) for event in turn.get("events") or ())
        stopped_here = stopped_at is not None and response >= stopped_at          # the turn the live authority stopped in (the page lets no turn follow it)
        moved = response > decision
        observed_point = points.get(response) if moved else None
        if observed_point:
            after, after_source = observed_point["pressure"], (OBSERVED, "live development authority")
        elif not moved:
            after, after_source = last, last_source
        else:
            after, after_source = None, (UNKNOWN, "the live development authority stopped at this turn" if stopped_here else "no committed authority minute")
        vaso_running = running > 0
        text_provenance = RESIDENT_EXPRESSED if turn.get("text_source") == PAGE else AUTHORED
        step = {
            "n": number,
            "decision_minute": field(decision, OBSERVED, "clock"),
            "response_minute": field(response, OBSERVED, "clock"),
            "state": {"pressure": field(last, *last_source), "reading": field(state_reading(last, vasopressor_running=running_before > 0), MODEL_DERIVED)},
            "priority": {"scenario": field(priorities[number], AUTHORED, "development path (proposed for faculty review)") if number in priorities else field(None, UNKNOWN),
                         "resident": _resident(turn.get("reasoning") or {}, ("management_priority",))},
            "action": {"text": field(str(turn.get("text") or ""), text_provenance, turn.get("text_source")), "orders": field(rows, OBSERVED, "order ledger"),
                       "executed": field(bool(turn.get("executed")), OBSERVED, "order ledger")},
            "expected": {"model": field(expectations or [NO_EXPECTATION], MODEL_DERIVED if expectations else UNKNOWN, "development encounter definition"),
                         "resident": _resident(turn.get("reasoning") or {}, ("expected_effect",))},
            "observed": {"pressure": field(after, *(after_source if moved or after is None else (after_source[0], "no clock advance: the last reading stands"))),
                         "authority": field({"minute": response, "candidate_digest": observed_point["candidate_digest"], "grant_id": observed_point["grant_id"], "snapshot_id": observed_point["snapshot_id"]}
                                            if observed_point else None, OBSERVED if observed_point else UNKNOWN, "authority artifact")},
            "reassessment": {"at_minute": field(response, OBSERVED, "clock"), "timing": field(_timing(orders, response - decision), MODEL_DERIVED, "the engine's turn rule, read from the order ledger"),
                             "reading": field(reassessment_reading(last, after, vasopressor_running=vaso_running) if moved else "No new reading: the clock did not move.", MODEL_DERIVED),
                             "resident": _resident(turn.get("reasoning") or {}, ("reassessment_target", "reassessment_plan"))},
            "new_state": {"pressure": field(after, *after_source), "reading": field(state_reading(after, vasopressor_running=vaso_running), MODEL_DERIVED)},
            "limitations": field(sorted(["BLEEDING_NOT_CONTROLLED", "LEGACY_FIELDS_NOT_AUTHORITATIVE", "OBSERVED_AT_REASSESSMENT_ONLY"]
                                        + (["VASOPRESSOR_SUPPORT_IS_TEMPORARY", "CONSCIOUSNESS_UNDER_TONE_UNRESOLVED"] if (vaso_running or running_before > 0) else [])), MODEL_DERIVED),
        }
        # the exits of THIS turn, earliest minute first (a request is made at the decision; a stop, a terminal lock or the horizon at the end of the turn); the others of the same turn are named, never hidden
        here = [kind for kind, holds in ((EXIT_DEFINITIVE_HAEMOSTASIS, definitive), (EXIT_HAEMOSTASIS_EVENT, haemostasis), (EXIT_AUTHORITY_STOP, stopped_here),
                                         (EXIT_TERMINAL, bool(turn.get("terminal_locked"))), (EXIT_HORIZON, response >= HORIZON_MIN)) if holds]
        if here and here[0] in (EXIT_DEFINITIVE_HAEMOSTASIS, EXIT_HAEMOSTASIS_EVENT):
            kind = here[0]
            boundary = _boundary(kind, decision, BOUNDARY_MESSAGE_REQUEST if kind == EXIT_DEFINITIVE_HAEMOSTASIS else HAEMOSTASIS_EVENT_MESSAGE, also=here[1:])
            step["observed"]["pressure"], step["observed"]["authority"] = beyond, beyond
            step["reassessment"]["reading"] = field("Beyond the development boundary: the response to this turn is not part of the development encounter.", MODEL_DERIVED)
            step["new_state"] = {"pressure": beyond, "reading": field("Beyond the development boundary.", MODEL_DERIVED)}
            steps.append(step)
            break
        steps.append(step)
        last, last_source = after, after_source
        if here:
            kind = here[0]
            if kind == EXIT_AUTHORITY_STOP:
                boundary = _boundary(kind, stopped_at, AUTHORITY_STOP_MESSAGE, halt_reason=summary["halt_reason"], also=here[1:])
            elif kind == EXIT_TERMINAL:
                boundary = _boundary(kind, response, TERMINAL_MESSAGE, also=here[1:])
            else:                                                                   # a turn that crosses the horizon is the last one and is shown whole
                boundary = _boundary(kind, response, BOUNDARY_MESSAGE + (HORIZON_CROSSED_NOTE if response > HORIZON_MIN else ""))
            break
    if boundary is None and summary["halted"]:
        boundary = _boundary(EXIT_AUTHORITY_STOP, stopped_at if stopped_at is not None else (max(points) if points else 0), AUTHORITY_STOP_MESSAGE, halt_reason=summary["halt_reason"])
    observed = [(0, start)] + [(minute, points[minute]["pressure"]) for minute in sorted(points) if boundary is None or minute <= boundary["minute"]]
    body = {"record_type": RECORD_TYPE, "schema": SCHEMA, "version": VERSION, "encounter": {"id": ENCOUNTER_ID, "definition_digest": definition["definition_digest"]},
            "scenario": {"id": scenario.get("id"), "case_id": scenario.get("case_id") or summary["case_id"], "plan_digest": scenario.get("plan_digest"),
                         "category": field(scenario["category"], AUTHORED, "development path (proposed for faculty review)") if scenario.get("category") else field(None, UNKNOWN)},
            "authority": summary, "arrival": field(start, AUTHORED, "authored arrival"), "steps": steps,
            "boundary": boundary or {"kind": None, "reached": False, "minute": None, "message": None, "provenance": FACULTY_DEFINED},
            "course": field(course(observed), MODEL_DERIVED), "provenance_legend": dict(PROVENANCE_LEGEND)}
    return {**body, "trace_digest": digest(body)}


def _boundary(kind: str, minute: int, message: str, *, halt_reason: str = "", also: Sequence[str] = ()) -> dict:
    """The boundary the encounter reached; ``also`` names the other exits that held in the same turn, so that none is hidden behind the one that came first."""
    return {"kind": kind, "reached": True, "minute": int(minute), "message": message, "provenance": FACULTY_DEFINED, **({"halt_reason": halt_reason} if halt_reason else {}),
            **({"also": list(also)} if also else {})}


def course(observed: Sequence[tuple]) -> dict:
    """The course of the observed pressure (MODEL_DERIVED arithmetic of OBSERVED points): the peak MAP and its minute, the last reading, how far it fell from the peak, and where it ends against the arrival."""
    points = [(int(minute), dict(pressure)) for minute, pressure in observed if pressure]
    if not points:
        return {}
    peak_minute, peak = max(points, key=lambda item: (item[1]["map"], -item[0]))
    last_minute, last = points[-1]
    arrival = points[0][1]
    return {"arrival_map": arrival["map"], "peak_map": peak["map"], "peak_minute": peak_minute, "last_map": last["map"], "last_minute": last_minute, "fall_from_peak_mmhg": peak["map"] - last["map"],
            "last_against_arrival": "ABOVE" if last["map"] - arrival["map"] >= CHANGE_MAP_MMHG else "BELOW" if arrival["map"] - last["map"] >= CHANGE_MAP_MMHG else "ABOUT_THE_SAME",
            "last_hypotensive": hypotensive(last)}


def trajectory(trace: Mapping) -> list:
    """The observed pressure points of a trace, in order (arrival, then every committed authority minute up to the boundary): ``[{"minute", "sbp", "dbp", "map"}]``."""
    points = [{"minute": 0, **dict(trace["arrival"]["value"])}]
    for step in trace["steps"]:
        pressure, minute = step["observed"]["pressure"]["value"], step["response_minute"]["value"]
        if pressure and step["observed"]["authority"]["value"] and minute > points[-1]["minute"]:
            points.append({"minute": minute, **dict(pressure)})
    return points


# -- validation -------------------------------------------------------------------------------------------------------------------------------------------------------------------
def _fields(value: Any, path: str = "") -> list:
    """Every ``{"value", "provenance"}`` field of a trace, with its path."""
    found = []
    if isinstance(value, dict):
        if "provenance" in value and "value" in value:
            found.append((path, value))
        for key, inner in value.items():
            if key != "value":
                found.extend(_fields(inner, f"{path}.{key}" if path else str(key)))
    elif isinstance(value, list):
        for index, inner in enumerate(value):
            found.extend(_fields(inner, f"{path}[{index}]"))
    return found


def claim_problems(trace: Mapping) -> list:
    """Every generated reading or expectation that claims more than the model supports (FD-MTRACE-10). The fixed boundary and limitation texts are not generated and are not scanned."""
    problems = []
    for path, item in _fields(trace):
        if item["provenance"] not in (MODEL_DERIVED, AUTHORED):
            continue
        for text in (item["value"] if isinstance(item["value"], list) else [item["value"]]):
            if isinstance(text, str):
                found = FORBIDDEN_CLAIMS.search(text)
                if found:
                    problems.append(f"{path}: '{found.group(0)}' claims more than the development model supports")
    return problems


def trace_problems(trace: Mapping, turns: Sequence[Mapping] | None = None) -> list:
    """Why a trace cannot be trusted. Empty means it can: its digest recomputes; every field carries one known provenance; every resident field is either NOT_EXPRESSED or EXACTLY the text of the turn's
    reasoning; every observed pressure after the arrival is a committed authority minute; the minutes move forward; nothing claims more than the model supports; and the boundary is one of the exits."""
    problems = []
    body = {key: value for key, value in trace.items() if key != "trace_digest"}
    if trace.get("trace_digest") != digest(body):
        problems.append("the trace digest does not recompute")
    if trace.get("schema") != SCHEMA or trace.get("encounter", {}).get("definition_digest") != encounter_definition()["definition_digest"]:
        problems.append("the trace was read with another schema or another encounter definition")
    for path, item in _fields(trace):
        if item["provenance"] not in PROVENANCE:
            problems.append(f"{path}: unknown provenance {item['provenance']!r}")
    minutes, previous = [], None
    arrival = trace.get("arrival") or {}
    for index, step in enumerate(trace.get("steps") or ()):
        decision, response = step["decision_minute"]["value"], step["response_minute"]["value"]
        minutes.append((decision, response))
        observed, authority = step["observed"]["pressure"], step["observed"]["authority"]
        for name, item in (("observed", observed), ("new state", step["new_state"]["pressure"])):
            if item.get("source") == "live development authority" and (item["provenance"] != OBSERVED or not authority["value"] or authority["value"].get("minute") != response):
                problems.append(f"step {index + 1}: the {name} pressure is labelled as the live authority's without its committed minute")
        expected_state = (dict(arrival, source="authored arrival") if previous is None else previous)
        state = step["state"]["pressure"]
        if (state.get("value"), state.get("provenance"), state.get("source")) != (expected_state.get("value"), expected_state.get("provenance"), expected_state.get("source")):
            problems.append(f"step {index + 1}: the state is not the new state of the step before it (or the authored arrival) under the same provenance")
        previous = step["new_state"]["pressure"]
        if turns is not None and index < len(turns):
            reasoning = dict(turns[index].get("reasoning") or {})
            for part, keys in (("priority", ("management_priority",)), ("expected", ("expected_effect",)), ("reassessment", ("reassessment_target", "reassessment_plan"))):
                if step[part]["resident"] != _resident(reasoning, keys):
                    problems.append(f"step {index + 1}: the resident's {part} is not exactly what the resident expressed, under the page's own provenance of it")
            text_provenance = RESIDENT_EXPRESSED if turns[index].get("text_source") == PAGE else AUTHORED
            if step["action"]["text"]["value"] != str(turns[index].get("text") or "") or step["action"]["text"]["provenance"] != text_provenance:
                problems.append(f"step {index + 1}: the action is not the turn's own text under its own provenance")
    if any(b < a for a, b in minutes) or any(minutes[i + 1][0] < minutes[i][1] for i in range(len(minutes) - 1)):
        problems.append("the minutes of the trace do not move forward")
    boundary = trace.get("boundary") or {}
    if boundary.get("reached") and boundary.get("kind") not in EXITS:
        problems.append("the boundary is not one of the exits")
    problems += claim_problems(trace)
    return problems


# -- the faculty-readable rendering (P3-512A) --------------------------------------------------------------------------------------------------------------------------------------------
def _join(value: Any) -> str:
    return " ".join(value) if isinstance(value, list) else str(value)


def _resident_line(resident: Mapping, label: str) -> str:
    if resident["value"] == NOT_EXPRESSED:
        return f"Resident {label}: not expressed" + (f" ({resident['note']})" if resident.get("note") else "")
    return f"Resident {label} (as expressed" + (f"; {resident['as']}" if resident.get("as") else "") + f"): {resident['value']}"


def _resident_label(resident: Mapping, part: str) -> str:
    return f"{part} (resident, as expressed" + (f"; {resident['as']}" if resident.get("as") else "") + ")"


def render(trace: Mapping) -> list:
    """The trace as a faculty reader reads it: one block per step, each line with its provenance, and the boundary. A resident priority appears only when it was expressed; a scenario priority is labelled as
    the development path's, proposed for faculty review. No identifier, digest, grant or snapshot appears here (they stay in the structured trace)."""
    blocks = []
    for step in trace["steps"]:
        decision, response = step["decision_minute"]["value"], step["response_minute"]["value"]
        rows = [row for row in step["action"]["orders"]["value"] if row["class"] != "reassessment"]
        observed = step["observed"]["pressure"]
        lines = [("State", step["state"]["reading"]["value"], step["state"]["reading"]["provenance"])]
        if step["priority"]["scenario"]["value"]:
            lines.append(("Scenario priority (development path, proposed for faculty review)", step["priority"]["scenario"]["value"], AUTHORED))
        lines.append(("Resident reasoning", _resident_line(step["priority"]["resident"], "priority"), RESIDENT_EXPRESSED))
        lines.append(("Action", step["action"]["text"]["value"], step["action"]["text"]["provenance"]))
        lines.append(("Expected (model)", _join(step["expected"]["model"]["value"]), step["expected"]["model"]["provenance"]))
        if step["expected"]["resident"]["value"] != NOT_EXPRESSED:
            lines.append((_resident_label(step["expected"]["resident"], "Expected"), step["expected"]["resident"]["value"], RESIDENT_EXPRESSED))
        lines.append(("Observed", (pressure_text(observed["value"]) + f" at minute {response}") if observed["value"] and response > decision else
                      "No new reading: the clock did not move." if response <= decision and observed["value"] else "Not part of the development encounter.", observed["provenance"]))
        lines.append(("Reassessment", step["reassessment"]["reading"]["value"], MODEL_DERIVED))
        if step["reassessment"]["resident"]["value"] != NOT_EXPRESSED:
            lines.append((_resident_label(step["reassessment"]["resident"], "Reassessment"), step["reassessment"]["resident"]["value"], RESIDENT_EXPRESSED))
        lines.append(("New state", step["new_state"]["reading"]["value"], MODEL_DERIVED))
        blocks.append({"n": step["n"], "minutes": f"Minute {decision}" + (f" → {response}" if response > decision else ""), "orders": [row["order"] for row in rows if row["order"]],
                       "lines": [{"label": label, "text": text, "provenance": provenance} for label, text, provenance in lines]})
    boundary = dict(trace.get("boundary") or {})
    if not boundary.get("reached"):
        return blocks
    lines = [{"label": "Development boundary", "text": boundary["message"], "provenance": FACULTY_DEFINED}]
    also = [ALSO_WORDS[kind] for kind in boundary.get("also") or () if kind in ALSO_WORDS]
    if also:
        lines.append({"label": "Also in this turn", "text": " ".join(also), "provenance": OBSERVED})
    return blocks + [{"n": None, "minutes": f"Minute {boundary['minute']}", "orders": [], "boundary": True, "lines": lines}]


#: How the other exits of the same turn are named on the boundary block (never hidden behind the first one).
ALSO_WORDS = {EXIT_HAEMOSTASIS_EVENT: "The legacy engine reported a procedure to control the bleeding.", EXIT_AUTHORITY_STOP: "The development experiment stopped for an operational reason.",
              EXIT_TERMINAL: "The legacy engine closed the encounter.", EXIT_HORIZON: "The clock reached the two-hour development horizon."}
