"""What the record can and cannot settle, read from the record itself.

Faculty review of 2026-09-23. Three of the corrections that had to be written
by hand for one encounter are really the same failure: a report stated, as
something the resident did or failed to do, something the record does not
establish. The corrections stay, and these checks run before any report is
shown so the next encounter does not need them.

Four things are computed here, all deterministic and all from the frozen
trace:

* **the first interval**, because no support can be shown earlier than the
  first reassessment the resident chose, and the encounter advances in the
  intervals it is given;
* **orders with no result**, separating the request, the sample and the
  report, which are three different moments;
* **descriptors that never moved**, because a flat value may be a patient who
  did not change or a variable this build does not model, and the record alone
  does not say which;
* **what backs a statement about urine**, which is a measured volume, an
  engine narrative, or nothing at all.

``unsettled`` then reads a claim and answers which of those the claim depends
on. It is used to hold a negative suggestion for faculty review rather than to
overturn it: the judgment stays with the faculty.
"""
from __future__ import annotations

import re

OBSERVED = (
    ("hr", "heart rate"), ("sbp", "systolic pressure"), ("dbp", "diastolic pressure"),
    ("spo2", "oxygen saturation"), ("respiratory_rate", "respiratory rate"),
    ("crt", "capillary refill"), ("mental_status", "alertness"),
    ("work_of_breathing", "work of breathing"), ("extremities", "extremities"),
)
URINE_WORDS = re.compile(r"\burine\b|\bdiuresis\b|\burinary output\b|\bfoley\b|\bcatheter\b", re.I)
_NO_URINE = re.compile(r"does not make any|no urine|produced no urine", re.I)


def _number(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return None if number != number or number in (float("inf"), float("-inf")) else number


def _observable(event, side):
    state = event.get(side) if isinstance(event.get(side), dict) else {}
    return state.get("observable") if isinstance(state.get("observable"), dict) else {}


def _executed(event):
    return [a for a in (event.get("executed_actions") or event.get("action_summaries") or [])
            if isinstance(a, dict)]


def _study_key(action):
    return action.get("diagnostic") or action.get("diagnostic_type")


def order_stages(trace):
    """Request, sample and report for every study, kept apart and paired.

    A study understood in one decision and reported in another is one order,
    not two; a second request for the same study is a second order and is
    paired with the next report that has not already been claimed. Returns
    ``{"trace:i": {"requested": [...], "reported": [...], "awaiting": [...]}}``.
    """
    trace = [event for event in (trace or []) if isinstance(event, dict)]
    reports = {}
    for position, event in enumerate(trace):
        for action in _executed(event):
            key = _study_key(action)
            if key:
                reports.setdefault(str(key), []).append((position, action))
    # Each request claims the next unclaimed report of its study, at or after
    # the decision that asked for it.
    claimed, origin_of = {}, {}
    for position, event in enumerate(trace):
        for action in event.get("interpreted_action") or []:
            key = _study_key(action) if isinstance(action, dict) else None
            if not key:
                continue
            key = str(key)
            taken = claimed.setdefault(key, set())
            match = next((index for index, (at, _) in enumerate(reports.get(key, []))
                          if index not in taken and at >= position), None)
            if match is None:
                origin_of.setdefault(key, []).append((position, None))
            else:
                taken.add(match)
                origin_of.setdefault(key, []).append((position, match))
    report_origin = {}
    for key, pairs in origin_of.items():
        for request_position, report_index in pairs:
            if report_index is not None:
                report_origin[(key, report_index)] = request_position
    stages = {}
    for position, event in enumerate(trace):
        requested, reported, awaiting = [], [], []
        for action in event.get("interpreted_action") or []:
            key = _study_key(action) if isinstance(action, dict) else None
            if key:
                requested.append(str(key))
        for key, entries in reports.items():
            for index, (at, action) in enumerate(entries):
                if at != position:
                    continue
                result = action.get("result") if isinstance(action.get("result"), dict) else {}
                origin = report_origin.get((key, index), position)
                reported.append({
                    "study": key, "requested_at_decision": origin + 1,
                    "requested_here": origin == position,
                    "sampled_at_min": _number(result.get("collected_at_min")),
                    "reported_at_min": _number(result.get("time_min")),
                })
        for key, pairs in origin_of.items():
            for request_position, report_index in pairs:
                if request_position == position and report_index is None:
                    awaiting.append(key)
        stages[f"trace:{position}"] = {"requested": requested, "reported": reported,
                                       "awaiting": awaiting}
    return stages


def urine_evidence(trace):
    """What, if anything, backs a statement about this encounter's urine.

    ``measured`` only when a volume exists. An engine sentence is a narrative,
    not a measurement, and the absence of both is neither.
    """
    trace = [event for event in (trace or []) if isinstance(event, dict)]
    for event in trace:
        for side in ("state_before", "state_after"):
            for key, value in (_observable(event, side) or {}).items():
                if "urine" in key.lower() and _number(value) is not None:
                    return {"kind": "measured", "value_ml": _number(value), "at_min": _number(event.get("response_time_min"))}
    for position, event in enumerate(trace):
        for action in _executed(event):
            label = str(action.get("label") or "")
            if URINE_WORDS.search(label) and _NO_URINE.search(label):
                return {"kind": "narrative", "text": " ".join(label.split()),
                        "at_min": _number(action.get("time_min")) if action.get("time_min") is not None
                        else _number(event.get("decision_time_min")),
                        "decision": position + 1}
    return {"kind": "absent"}


def urine_statement(trace):
    """One sentence that says exactly what the record holds about the urine."""
    evidence = urine_evidence(trace)
    closed = closing_minute(trace)
    ending = f" before the encounter ended at {closed:g} min" if closed is not None else ""
    if evidence["kind"] == "measured":
        when = f" at {evidence['at_min']:g} min" if evidence.get("at_min") is not None else ""
        return f"Urine volume recorded{when}: {evidence['value_ml']:g} mL."
    if evidence["kind"] == "narrative":
        when = f" at {evidence['at_min']:g} min" if evidence.get("at_min") is not None else ""
        return ("The engine reported" + when + " that the catheter was producing none; "
                "no urine volume was recorded" + ending + ".")
    return "No urine volume was recorded" + ending + "."


def closing_minute(trace):
    times = [_number(event.get("response_time_min")) for event in (trace or []) if isinstance(event, dict)]
    times = [minute for minute in times if minute is not None]
    return max(times) if times else None


def first_interval(trace):
    """The first reassessment interval: nothing can be shown earlier than it."""
    for event in trace or []:
        if not isinstance(event, dict):
            continue
        start, end = _number(event.get("decision_time_min")), _number(event.get("response_time_min"))
        if start is not None and end is not None:
            return end - start
    return None


def inert_observables(trace):
    """Descriptors the record never moves, which it cannot explain by itself."""
    trace = [event for event in (trace or []) if isinstance(event, dict)]
    if len(trace) < 2:
        return []
    inert = []
    for key, label in OBSERVED:
        values = []
        for event in trace:
            for side in ("state_before", "state_after"):
                value = (_observable(event, side) or {}).get(key)
                if value is not None:
                    values.append(value)
        if len(values) > 2 and len(set(map(str, values))) == 1:
            inert.append(label)
    return inert


VENTILATORY = ("oxygen", "niv", "invasive_ventilation", "bag_mask", "airway", "ventilation")
RESPIRATORY = (("work_of_breathing", "work of breathing"), ("respiratory_rate", "respiratory rate"))


def unresponsive_to_support(trace):
    """Respiratory descriptors that never move once support has been given.

    Support was given and the descriptor did not change afterwards. The record
    cannot say whether the patient did not respond or whether this build does
    not move that descriptor with ventilation, so a claim that the resident
    failed to adjust ventilation cannot rest on it alone.
    """
    trace = [event for event in (trace or []) if isinstance(event, dict)]
    first = None
    for position, event in enumerate(trace):
        for action in _executed(event):
            kind = str(action.get("type") or action.get("support_type") or "").lower()
            if any(word in kind for word in VENTILATORY):
                first = position if first is None else first
    if first is None:
        return []
    frozen = []
    for key, label in RESPIRATORY:
        values = []
        for event in trace[first:]:
            for side in ("state_before", "state_after"):
                value = (_observable(event, side) or {}).get(key)
                if value is not None:
                    values.append(str(value))
        if len(values) > 2 and len(set(values)) == 1:
            frozen.append(label)
    return frozen


def orders_without_result(trace):
    """Studies requested whose result never reached the record."""
    missing = []
    for value in order_stages(trace).values():
        for key in value["awaiting"]:
            if key not in missing:
                missing.append(key)
    return missing


def encounter_limits(trace):
    """Everything the record cannot settle on its own, in one place."""
    return {
        "first_interval_min": first_interval(trace),
        "closed_at_min": closing_minute(trace),
        "orders_without_result": orders_without_result(trace),
        "inert_observables": inert_observables(trace),
        "unresponsive_to_support": unresponsive_to_support(trace),
        "urine": urine_evidence(trace),
    }


_TIME_CLAIM = re.compile(r"\b(?:delay|delayed|late|later|not (?:started|initiated)|"
                         r"no (?:immediate|supplemental)|began|before)\b", re.I)


def unsettled(text, limits):
    """Which recorded limitations a claim depends on, if any.

    Conservative by design: it answers only for the limitations this record
    actually has, and it names them so a reader can check the call.
    """
    text = " ".join(str(text or "").split())
    if not text:
        return []
    reasons = []
    interval = (limits or {}).get("first_interval_min")
    if interval and _TIME_CLAIM.search(text) and re.search(r"\b%g\b" % interval, text):
        reasons.append(
            f"the first reassessment interval was {interval:g} min, so the record cannot separate a "
            "delay in support from the interval the encounter advances in")
    for study in (limits or {}).get("orders_without_result") or []:
        if re.search(r"\b" + re.escape(str(study).replace("_", " ")) + r"\b", text, re.I):
            closed = (limits or {}).get("closed_at_min")
            ending = f" and the encounter closed at {closed:g} min" if closed is not None else ""
            reasons.append(f"{study} was requested{ending} with no result recorded, so an unexecuted "
                           "order cannot be told apart from the end of the encounter")
    if URINE_WORDS.search(text) and (limits or {}).get("urine", {}).get("kind") != "measured":
        reasons.append("no urine volume was measured, so a statement about output rests on an engine "
                       "message rather than on a measurement")
    adjustment = re.search(r"\badjust|escalat|titrat|increase|wean\b", text, re.I)
    for label in (limits or {}).get("unresponsive_to_support") or []:
        if adjustment and re.search(r"\b" + re.escape(label) + r"\b", text, re.I):
            reasons.append(f"the {label} does not change in this record after ventilatory support was "
                           "given, so whether it could respond to an adjustment is not established here")
    for label in (limits or {}).get("inert_observables") or []:
        if re.search(r"\b" + re.escape(label) + r"\b", text, re.I):
            reasons.append(f"the {label} never changes in this record, which may be the patient or may "
                           "be a variable this build does not move")
    return reasons


HELD_STATUS = "Requires faculty review"


def hold_for_review(item, limits):
    """A negative suggestion whose basis the record cannot settle is held.

    The suggestion is not overturned and never becomes satisfactory: it is
    presented as needing the faculty's own reading, with the reason, and the
    original suggestion is preserved and shown beside it.
    """
    item = item if isinstance(item, dict) else {}
    if item.get("recommendation") != "needs_improvement":
        return []
    text = " ".join(str(item.get(key) or "") for key in ("rationale", "feedback", "context"))
    return unsettled(text, limits)
