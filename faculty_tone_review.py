"""P3-404 to P3-409: the MULTIFAMILY FACULTY REVIEW of the common vascular tone / norepinephrine pathway -- the data model and the reviewer's durable state (pure: no Streamlit, no engine, no authority, no common core).

WHAT IT IS. The same review the faculty trajectory review and the re-review give (one page per scenario, the five questions Q1 to Q5, an optional comment, a first impression that is LOCKED and can never be edited, an
overall judgment with an optional comment, ONE submit that moves on, a summary), run on a DIFFERENT, versioned review set (``COMMON_TONE_V1_MULTIFAMILY_FACULTY_REVIEW``): the pressure response to ONE norepinephrine order
(10 mcg/min, started once and never changed) in five scenarios that stress the same common vascular-tone pathway in different states: a hemorrhage, a synthetic low-tone probe, a pump-limited ACS, a congested pulmonary
edema and an obstructive pulmonary embolism. It reuses ``faculty_trajectory_review`` (its event log, its lock, its atomic record, its progress) through ``faculty_trajectory_rereview`` (the blind, comparator-free
variant) and changes only what must change:

* every trajectory is the CENTER_REFERENCE trajectory exactly as the certified common-tone records and the certified harness produce it: nothing is recomputed, tuned or substituted here, and the stored set is pinned;
* NOTHING of the mechanism reaches the reviewer's first pass: no other setting of the response, no parameter, no earlier trajectory, no legacy engine value, no tone state, no flow, no delivery, no oxygen debt, no
  consciousness, no collapse state, and no heart rate or capillary refill (they were not recomputed for these trajectories);
* the limitations the review cannot judge are stored APART from the items and drawn ONLY in the final summary;
* an OPTIONAL sensitivity check (the other settings of the response on the same axes) exists but is reachable ONLY once every scenario has been submitted: the views are built here and raise ``Locked`` before that.

THE REVIEWER SEES clinical content only. THE RECORD KEEPS the audit metadata (set id and digest, item digest, the source records and their digests); the reviewer never types or sees it, and ``load_set`` returns it APART from
the items so that nothing the page puts in front of the reviewer can carry it.

NOTHING OF THE EARLIER REVIEWS IS READ OR WRITTEN: their sets, logs and records are other files; this review's logs and records live in ``tone_review/`` and ``tone_reviews/``, and a record or log of one can never be
mistaken for another. Earlier judgments are not transferred.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

import faculty_trajectory_review as ftr
import faculty_trajectory_rereview as rr

VERSION = "TONE-REVIEW-1"
ROOT = Path(__file__).resolve().parent
SET_PATH = ROOT / "docs" / "revision" / "PHASE3_COMMON_TONE_V1_MULTIFAMILY_REVIEW_SET.json"
SET_ID = "COMMON_TONE_V1_MULTIFAMILY_FACULTY_REVIEW"
SET_TYPE = "PHASE3_COMMON_TONE_MULTIFAMILY_REVIEW_SET"
RECORD_TYPE = "PHASE3_COMMON_TONE_MULTIFAMILY_REVIEW_RECORD"
SUMMARY_TYPE = "PHASE3_COMMON_TONE_MULTIFAMILY_REVIEW_SESSION_SUMMARY"
SUBDIR, RECORDS_SUBDIR, SENSITIVITY_SUBDIR = "tone_review", "tone_reviews", "tone_sensitivity"
#: The stored set, pinned IN CODE (the first review's rule: a digest the file attests about itself pins nothing). Regenerating the set is a deliberate, reviewed act that changes this line.
PINNED_SET_DIGEST = "22ed59069e441aca96939ccf359ceec00a8bd55ddc0b182ff7bbcfcdd6e91487"
_PIN = object()
WITNESS = "CENTER_REFERENCE"
STATEMENT = ("Synthetic development cases and one synthetic physiology probe. A faculty judgment of stored development trajectories of ONE norepinephrine order: not a clinical validation, not a calibrated "
             "configuration, not a score, not a resident pilot.")
#: The scenarios, all required, in the order the faculty asked for. The optional ones (opioid, asthma) are not part of this set: the reason is stored in the audit.
SEQUENCE = (("FR-F", True), ("SYNTH", True), ("ACS", True), ("PULM-EDEMA", True), ("PE", True))
SCENARIOS = tuple(identifier for identifier, _ in SEQUENCE)
KIND_CASE, KIND_PROBE = "AUTHORED_CASE", "SYNTHETIC_PROBE"
PROBE_BANNER = "SYNTHETIC DEVELOPMENT PHYSIOLOGY PROBE"
PROBE_NOTE = "This is a synthetic development physiology probe, not a clinical case."
CASE_BANNER = "SYNTHETIC DEVELOPMENT CASE"
CASE_NOTE = "An authored synthetic case for development, not a patient."
COMPLETION_NOTE = ("Your first impressions and overall judgments are saved and locked. They are your own judgments, tabulated: they are not a score, not a clinical validation, and not an approval.")

#: The pre-declared rule for the optional sensitivity check (fixed before any trajectory was looked at): a scenario is offered only where the other settings of the response MATERIALLY change the picture -- the pressure
#: at the last minute differs by at least this many mmHg between the weakest and the strongest setting, or the highest systolic pressure does. A trivial difference is not put in front of the reviewer.
MATERIAL_MAP_SPAN, MATERIAL_SBP_SPAN = 10, 15
SENSITIVITY_QUESTION = "Does the sensitivity range remain within a clinically defensible development envelope?"
SENSITIVITY_CHOICES = ("YES", "BORDERLINE", "NO")
SENSITIVITY_NAMES = ("LOW", "CENTER", "HIGH")          # the reviewer's labels, drawn only in the optional section; they carry no parameter value

#: Words a reviewer-facing field must never carry (defence in depth: the loader refuses an item that does). The identity of the configuration, the other settings, the earlier sets, the mechanism and the parameters are not
#: reviewer vocabulary. Upper-case LOW and HIGH are the names of the other settings (the clinical words "low" and "high" are ordinary).
_LEAK = re.compile(r"center_reference|witness|legacy|comparator|tone_gain|half[ _-]?effect|time[ _-]?constant|onset[ _]tau|offset[ _]tau|parameter|amendment|candidate|kernel|consciousness|cardiac output|cardiac index|"
                   r"oxygen|o2 debt|sensitivity|conjunto|joint[ _-]?region|heart[ _-]?rate|capillary|\bHR\b|\bCRT\b|lactate|mental status|tone state|collapse state", re.I)
_LEAK_NAMES = re.compile(r"\b(?:LOW|HIGH)\b")
_SHOWN_KEYS = ("scenario_id", "short", "title", "kind", "banner", "note", "context", "baseline_facts", "purpose", "arrival", "intervention", "timeline", "common", "table_minutes")
#: The exact keys of an item and of its parts. An item with another key (a comparator, a parameter, a heart rate) is not this package, even when re-signed and pinned: nothing the page does not draw may be stored with the item.
ITEM_KEYS = frozenset(_SHOWN_KEYS) | {"stopped", "required"}
ARRIVAL_KEYS = frozenset({"sbp", "dbp", "map", "spo2", "rr"})
ARRIVAL_SHOWN = ("sbp", "dbp", "map", "spo2", "rr")
ROW_KEYS = rr.ROW_KEYS
POINT_KEYS = rr.POINT_KEYS
SENSITIVITY_KEYS = frozenset({"scenario_id", "material", "points"})
LIMITATION_KEYS = frozenset({"id", "text"})
LIMITATION_IDS = ("COMMON_TONE_PUMP_DEPENDENCE_NOT_YET_VALIDATED", "CONSCIOUSNESS_UNDER_TONE_UNRESOLVED", "TITRATION_AND_STOP_NOT_SUPPORTED")


def _seal_digest(value: Any) -> str:
    """The digest a sealed historical record carries (the same canonical form as ``historical_records.digest_of``; a test holds the two equal). Kept here so this pure module imports nothing of the layer."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")).hexdigest()


def is_material(low: Sequence[Mapping], high: Sequence[Mapping]) -> bool:
    """The pre-declared rule, on two trajectories of the same minutes."""
    return (abs(float(low[-1]["map"]) - float(high[-1]["map"])) >= MATERIAL_MAP_SPAN
            or abs(max(float(point["sbp"]) for point in low) - max(float(point["sbp"]) for point in high)) >= MATERIAL_SBP_SPAN)


# -- the stored set ---------------------------------------------------------------------------------------------------------------------------------------------------------------
def item_problems(item: Mapping) -> list:
    """Why a stored scenario cannot be reviewed. Empty means it can. Everything is checked here, nothing is trusted because it was stored; a malformed item is a problem, never an exception."""
    identifier = item.get("scenario_id") if isinstance(item, dict) else None
    try:
        return _item_problems(item)
    except Exception as error:                                                    # a malformed stored item must be refused, not crash the page
        return [f"{identifier or 'a scenario'}: the stored scenario cannot be checked ({type(error).__name__})"]


def _exact(value: Any, keys: frozenset) -> bool:
    return isinstance(value, dict) and set(value) == keys


def _whole_pressures(points: Sequence[Mapping], label: str) -> str | None:
    for point in points:
        try:
            values = [float(point[key]) for key in ("sbp", "dbp", "map")]
        except (KeyError, TypeError, ValueError):
            return f"{label}: a point of the trajectory is incomplete"
        if any(not value.is_integer() for value in values) or round((values[0] + 2 * values[1]) / 3) != values[2] or values[0] <= values[1] or min(values) <= 0:
            return f"{label}: a point is not whole mmHg, its MAP is not (SBP + 2 x DBP) / 3, or it is not a pulse pressure"
    return None


def _item_problems(item: Any) -> list:
    if not isinstance(item, dict):
        return ["a stored scenario is not an object"]
    body, problems = dict(item), []
    identifier = body.get("scenario_id")
    if identifier not in SCENARIOS:
        return [f"{identifier or 'a scenario'} is not in the review set"]
    if set(body) != ITEM_KEYS:
        return [f"{identifier}: it does not have exactly the stored keys of a scenario (extra: {sorted(set(body) - ITEM_KEYS)}, missing: {sorted(ITEM_KEYS - set(body))})"]
    for key in _SHOWN_KEYS:
        if body[key] in (None, "", [], {}):
            problems.append(f"{identifier}: {key} is missing")
    if problems:
        return problems
    strings = ("short", "title", "kind", "banner", "note", "context", "purpose", "intervention")
    if (not all(isinstance(body[key], str) for key in strings) or not isinstance(body["timeline"], list) or not isinstance(body["common"], list) or not isinstance(body["baseline_facts"], list)
            or not isinstance(body["table_minutes"], list) or any(not isinstance(fact, str) or not fact for fact in body["baseline_facts"])):
        return [f"{identifier}: a field has the wrong type"]
    if not _exact(body["arrival"], ARRIVAL_KEYS) or any(not _exact(row, ROW_KEYS) for row in body["timeline"]) or any(not _exact(point, POINT_KEYS) for point in body["common"]):
        return [f"{identifier}: the arrival, a timeline row or a pressure point does not have exactly the stored keys"]
    if body["kind"] not in (KIND_CASE, KIND_PROBE):
        problems.append(f"{identifier}: its kind is neither an authored case nor a synthetic probe")
    elif body["kind"] == KIND_PROBE and (body["banner"] != PROBE_BANNER or body["note"] != PROBE_NOTE):
        problems.append(f"{identifier}: a synthetic probe must be labelled as one, in the exact words")
    elif body["kind"] == KIND_CASE and (body["banner"] != CASE_BANNER or body["note"] != CASE_NOTE):
        problems.append(f"{identifier}: an authored case must carry its own label")
    if body.get("stopped") is not False or body.get("required") is not True:
        problems.append(f"{identifier}: the page draws no stop and every scenario of this package is required")
    arrival, points = dict(body["arrival"]), list(body["common"])
    minutes = [point.get("minute") for point in points]
    if minutes[0] != 0 or any(not isinstance(a, int) or not isinstance(b, int) or b <= a for a, b in zip(minutes, minutes[1:])):
        problems.append(f"{identifier}: the minutes of the trajectory do not start at 0 and increase")
    problem = _whole_pressures(points, identifier)
    if problem:
        problems.append(problem)
    if (points[0].get("sbp"), points[0].get("dbp"), points[0].get("map")) != (arrival.get("sbp"), arrival.get("dbp"), arrival.get("map")):
        problems.append(f"{identifier}: the first point is not the baseline pressure")
    if body["kind"] == KIND_CASE and any(not isinstance(arrival.get(key), int) or isinstance(arrival.get(key), bool) for key in ARRIVAL_KEYS):
        problems.append(f"{identifier}: an authored case states its arrival pressure, saturation and respiratory rate")
    if body["kind"] == KIND_PROBE and (arrival.get("spo2") is not None or arrival.get("rr") is not None):
        problems.append(f"{identifier}: a synthetic probe has no saturation or respiratory rate")
    rows = list(body["timeline"])
    if [row.get("n") for row in rows] != list(range(1, len(rows) + 1)) or any(not isinstance(row.get("executed"), bool) or not isinstance(row.get("intervention"), bool) for row in rows):
        problems.append(f"{identifier}: the timeline is not numbered or lacks its marker flags")
    elif any(row["minute"] not in minutes for row in rows if row["intervention"]):
        problems.append(f"{identifier}: an intervention is not at a minute of the trajectory")
    tables = list(body["table_minutes"])
    if tables[0] != 0 or tables[-1] != minutes[-1] or any(not isinstance(a, int) or not isinstance(b, int) or b <= a for a, b in zip(tables, tables[1:])) or any(minute not in minutes for minute in tables):
        problems.append(f"{identifier}: the table minutes are not minutes of the trajectory, from the first to the last")
    text = json.dumps(body, sort_keys=True)
    found = _LEAK.search(text) or _LEAK_NAMES.search(text)
    if found:
        problems.append(f"{identifier}: a reviewer-facing field carries '{found.group(0)}'")
    return problems


def _sensitivity_problems(entries: Any, items: Mapping) -> list:
    """The stored sensitivity section: exact keys, the same minutes as the item, one baseline for every setting, the same whole-mmHg rules, and the stored ``material`` flag equal to the pre-declared rule recomputed."""
    if not isinstance(entries, list) or [entry.get("scenario_id") if isinstance(entry, dict) else None for entry in entries] != list(SCENARIOS):
        return ["the sensitivity section does not hold exactly one entry per scenario, in order"]
    problems = []
    for entry in entries:
        identifier = entry["scenario_id"]
        if not _exact(entry, SENSITIVITY_KEYS) or not isinstance(entry.get("material"), bool) or not _exact(entry.get("points"), frozenset({"LOW", "HIGH"})):
            problems.append(f"{identifier}: its sensitivity entry does not have exactly the stored keys")
            continue
        centre = items[identifier]["common"]
        for name in ("LOW", "HIGH"):
            points = entry["points"][name]
            if not isinstance(points, list) or any(not _exact(point, POINT_KEYS) for point in points) or [point.get("minute") for point in points] != [point["minute"] for point in centre]:
                problems.append(f"{identifier}: the {name} trajectory is not on the minutes of the scenario")
                break
            problem = _whole_pressures(points, f"{identifier} {name}")
            if problem:
                problems.append(problem)
                break
            if points[0] != centre[0]:
                problems.append(f"{identifier}: the {name} trajectory does not start from the same baseline pressure")
                break
        else:
            if entry["material"] != is_material(entry["points"]["LOW"], entry["points"]["HIGH"]):
                problems.append(f"{identifier}: the stored 'material' flag is not the pre-declared rule applied to its trajectories")
    return problems


def _limitation_problems(limitations: Any) -> list:
    if (not isinstance(limitations, list) or [entry.get("id") if isinstance(entry, dict) else None for entry in limitations] != list(LIMITATION_IDS)
            or any(not _exact(entry, LIMITATION_KEYS) or not isinstance(entry["text"], str) or not entry["text"] for entry in limitations)):
        return ["the limitations of the review are not the three the review states"]
    return []


def load_set(path: Path | None = None, *, expected_digest: Any = _PIN) -> dict:
    """The stored set, verified. ``{"ok", "problems", "digest", "items", "sensitivity", "limitations", "audit"}``; ``items`` are what the reviewer may see in the first pass, ``sensitivity`` is what the optional check may
    show once every scenario is submitted, ``limitations`` is what the final summary states, and ``audit`` is kept apart from all of them. A set whose own digest does not recompute, that is not the pinned one, or that does
    not hold exactly the scenarios offers nothing. Never raises."""
    result: dict = {"ok": False, "problems": [], "digest": None, "items": {}, "sensitivity": [], "limitations": [], "audit": {}}
    try:
        record = json.loads(Path(path or SET_PATH).read_text(encoding="utf-8"))
    except Exception as error:
        return {**result, "problems": [f"the review set cannot be read ({type(error).__name__})"]}
    if not isinstance(record, dict):
        return {**result, "problems": ["the review set is not the stored one (it is not a record)"]}
    claimed = record.get("record_digest")
    rest = {key: value for key, value in record.items() if key != "record_digest"}
    try:
        recomputes = record.get("record_type") == SET_TYPE and claimed == _seal_digest(rest)
    except (TypeError, ValueError):
        recomputes = False
    if not recomputes:
        return {**result, "problems": ["the review set is not the stored one (its digest does not recompute)"]}
    pin = PINNED_SET_DIGEST if expected_digest is _PIN else expected_digest
    if pin is not None and claimed != pin:
        return {**result, "problems": ["the review set is not the pinned one (a re-signed or regenerated set is refused until its digest is pinned in code)"]}
    listed = record.get("items")
    if record.get("set_id") != SET_ID or not isinstance(listed, list) or any(not isinstance(item, dict) for item in listed) or [item.get("scenario_id") for item in listed] != list(SCENARIOS):
        return {**result, "problems": ["the review set does not hold exactly its scenarios in order"]}
    problems = [problem for item in listed for problem in item_problems(item)]
    items = {item["scenario_id"]: item for item in listed}
    section, audit = record.get("sensitivity"), record.get("audit")
    if not isinstance(section, dict) or not isinstance(audit, dict):
        return {**result, "problems": problems + ["the review set does not hold its sensitivity section and its audit as records"]}
    try:
        problems += _sensitivity_problems(section.get("scenarios"), items) if not problems else []
        problems += _limitation_problems(record.get("limitations"))
    except Exception as error:                                                    # a malformed stored section is refused, never an exception
        problems.append(f"the sensitivity section or the limitations cannot be checked ({type(error).__name__})")
    if problems:
        return {**result, "problems": problems}
    return {"ok": True, "problems": [], "digest": claimed, "items": items, "sensitivity": list(section["scenarios"]), "limitations": [dict(entry) for entry in record["limitations"]], "audit": dict(audit)}


# -- what the reviewer is shown --------------------------------------------------------------------------------------------------------------------------------------------------
def blind_view(item: Mapping) -> dict:
    """EVERYTHING the reviewer sees for a scenario in the first pass. There is no other view: no other setting of the response, no comparator, no heart rate and no capillary refill exist in it."""
    return {"scenario_id": item["scenario_id"], "short": item["short"], "title": item["title"], "kind": item["kind"], "banner": item["banner"], "note": item["note"], "context": item["context"],
            "baseline_facts": list(item["baseline_facts"]), "purpose": item["purpose"], "arrival": {key: item["arrival"][key] for key in ARRIVAL_SHOWN}, "intervention": item["intervention"],
            "timeline": [dict(row) for row in item["timeline"]], "halted": False, "stop_minute": None, "common": [dict(point) for point in item["common"]],
            "questions": [dict(question, choices=list(question["choices"])) for question in ftr.required_questions(item)[0]]}


def sequence(items: Mapping) -> list:
    """The scenarios actually offered, in order: ``[{"scenario_id", "required"}]``."""
    return [{"scenario_id": identifier, "required": required} for identifier, required in SEQUENCE if identifier in items]


def values_table(item: Mapping) -> list:
    """The pressure points of the table next to the chart (the minutes the item names): minute, SBP, DBP, MAP. Nothing else."""
    shown = set(item["table_minutes"])
    return [{"minute": point["minute"], "sbp": int(point["sbp"]), "dbp": int(point["dbp"]), "map": int(point["map"])} for point in item["common"] if point["minute"] in shown]


def y_axis_max(item: Mapping, floor: int = 140) -> int:
    """The top of the pressure axis: the chart's usual 140 mmHg, or the next 20 mmHg above the highest pressure of the scenario (a hypertensive arrival must not be clipped)."""
    highest = max(float(point["sbp"]) for point in item["common"])
    return max(floor, int(-(-highest // 20) * 20))


def map_axis_range(points: Sequence[Mapping], margin: int = 10) -> list:
    """The mean-arterial-pressure axis of the optional check: from just below the lowest to just above the highest pressure of the three settings, in tens of mmHg (a zero-based axis would flatten the very difference the
    reviewer is asked to judge)."""
    lowest, highest = min(float(point["map"]) for point in points), max(float(point["map"]) for point in points)
    return [int((lowest - margin) // 10 * 10), int(-(-(highest + margin) // 10) * 10)]


def sensitivity_view(sensitivity: Sequence[Mapping], items: Mapping, prog: Mapping) -> list:
    """The OPTIONAL sensitivity check, ONLY once every scenario is submitted; anything earlier raises ``Locked`` and there is no other way to obtain the other settings from this module. Only the scenarios where the
    other settings MATERIALLY change the picture (the pre-declared rule) are offered; the middle line is the scenario's own trajectory, unchanged."""
    if not dict(prog or {}).get("required_done"):
        raise ftr.Locked("the scenarios are not all submitted")
    offered = []
    for entry in sensitivity:
        if not entry["material"]:
            continue
        item = items[entry["scenario_id"]]
        offered.append({"scenario_id": entry["scenario_id"], "title": item["title"], "kind": item["kind"], "table_minutes": list(item["table_minutes"]), "map_range": map_axis_range(item["common"] + entry["points"]["LOW"] + entry["points"]["HIGH"]),
                        "witnesses": {"LOW": [dict(point) for point in entry["points"]["LOW"]], "CENTER": [dict(point) for point in item["common"]], "HIGH": [dict(point) for point in entry["points"]["HIGH"]]}})
    return offered


# -- the durable review ----------------------------------------------------------------------------------------------------------------------------------------------------------------
class ToneReviewLog(rr.ReReviewLog):
    """The durable state of ONE reviewer on ONE scenario of this set: the blind re-review's append-only, hash-chained, locked event log (no comparator step) in this review's own files."""
    SUBDIR_NAME, RECORDS_NAME = SUBDIR, RECORDS_SUBDIR

    def _stem(self) -> str:
        return f"{self.item['scenario_id']}__{SET_ID}__{self.set_digest[:12]}__{self.item_digest}"          # another set (another digest) is another log: answers are never carried onto it

    def _record(self, state: Mapping) -> dict:
        source = dict(dict(self.audit.get("sources") or {}).get(self.item["scenario_id"]) or {})
        body = {"record_type": RECORD_TYPE, "version": VERSION, "reviewer_ref": self.reviewer, "reviewer_role": self.account.get("role"), "set_id": SET_ID, "scenario_id": self.item["scenario_id"],
                "linkage": {"set_digest": self.set_digest, "item_digest": self.item_digest, "witness": self.audit.get("witness"), "source_record_id": source.get("source_record_id"),
                            "source_record_digest": source.get("source_record_digest")},
                "first_pass": {"answers": dict(state["locked_answers"] or state["blind"]), "comment": state["locked_comment"] if state["locked_comment"] is not None else state["blind_comment"],
                               "locked_at": state["locked_at"], "answers_at_lock": dict(state["locked_answers"] or state["blind"])},
                "overall": {"judgment": state["overall"], "comment": state["overall_comment"]},
                "comparator_shown": False, "event_log_head": state["head"], "statement": STATEMENT}
        body["record_id"] = ftr._digest(body)[:16]
        return body


def _as_dict(value: Any) -> dict:
    """A stored field as a plain dict; anything else (a forged record may hold a list, a string, a number) is an empty one, so a malformed record simply fails to verify."""
    return dict(value) if isinstance(value, dict) else {}


def record_problems(record: Mapping, state: Mapping, log: ToneReviewLog) -> list:
    """Why a record cannot be counted: it must recompute its identity, belong to THIS reviewer, scenario, set and item, and AGREE field by field with the log that closed it."""
    if not isinstance(record, dict):
        return ["the record is not a record"]
    problems = []
    body = {key: value for key, value in record.items() if key != "record_id"}
    link, first, overall = (_as_dict(record.get("linkage")), _as_dict(record.get("first_pass")), _as_dict(record.get("overall")))
    if record.get("record_type") != RECORD_TYPE or record.get("record_id") != ftr._digest(body)[:16]:
        problems.append("the record does not recompute its identity")
    if record.get("scenario_id") != log.item["scenario_id"] or record.get("reviewer_ref") != log.reviewer or record.get("set_id") != SET_ID:
        problems.append("the record belongs to another scenario, reviewer or set")
    if link.get("set_digest") != log.set_digest or link.get("item_digest") != log.item_digest:
        problems.append("the record is linked to another review set or item")
    if record.get("record_id") != state.get("record_id") or record.get("event_log_head") != state.get("submitted_prev"):
        problems.append("the record is not the one that closed the event log")
    if (_as_dict(first.get("answers_at_lock")) != dict(state.get("locked_answers") or {}) or _as_dict(first.get("answers")) != dict(state.get("locked_answers") or {})
            or first.get("comment") != state.get("locked_comment") or first.get("locked_at") != state.get("locked_at")):
        problems.append("the record's first pass differs from the log")
    if overall.get("judgment") != state.get("overall") or overall.get("comment") != state.get("overall_comment") or record.get("comparator_shown") is not False:
        problems.append("the record's overall judgment differs from the log")
    return problems


def _sensitivity_fold(lines: Sequence[str], allowed: Sequence[str]) -> dict:
    """The state of the sensitivity log, or ``status == "UNREADABLE"`` when its chain does not verify. Pure; never raises. Anything but an answer or a note about an offered scenario is ignored."""
    state: dict = {"status": "NEW", "answers": {}, "comments": {}, "head": "0" * 64, "events": 0}
    previous = "0" * 64
    for index, line in enumerate(lines):
        try:
            event = json.loads(line)
            if not isinstance(event, dict):
                raise ValueError("event")
            claimed = event.pop("hash")
            if event.get("seq") != index + 1 or event.get("prev") != previous or claimed != ftr._digest({**event}):
                raise ValueError("chain")
            previous, kind, data = claimed, event["kind"], event.get("data")
            if not isinstance(kind, str) or not isinstance(data, dict):
                raise ValueError("event shape")
            if kind == "envelope" and data.get("id") in allowed and data.get("value") in SENSITIVITY_CHOICES:
                state["answers"][data["id"]] = data["value"]
            elif kind == "envelope_comment" and data.get("id") in allowed:
                state["comments"][data["id"]] = str(data.get("text") or "")
        except (KeyError, TypeError, ValueError, AttributeError):
            return {**state, "status": "UNREADABLE", "why": f"the saved answers do not verify (event {index + 1})"}
    state["head"], state["events"] = previous, len(lines)
    state["status"] = "IN_PROGRESS" if (state["answers"] or state["comments"]) else "NEW"
    return state


class SensitivityLog(ftr.ReviewLog):
    """The durable state of the OPTIONAL sensitivity check of ONE reviewer: one append-only, hash-chained log with an autosaved answer and note per offered scenario. It has no lock, no submit and no record: the main
    review never depends on it. It uses the review log's own writer (an exclusive lock, an fsync, a chain)."""
    SUBDIR_NAME, RECORDS_NAME = SENSITIVITY_SUBDIR, RECORDS_SUBDIR

    def __init__(self, root: Path, reviewer: str, scenario_ids: Sequence[str], *, set_digest: str, bundles: Any = None, account: Mapping | None = None):
        self.scenario_ids = tuple(scenario_ids)
        super().__init__(root, reviewer, {"scenario_id": "SENSITIVITY", "scenarios": list(self.scenario_ids)}, set_digest=set_digest, bundles=bundles, account=account)

    def _stem(self) -> str:
        return f"SENSITIVITY__{SET_ID}__{self.set_digest[:12]}__{self.item_digest}"

    def _replay(self, lines: Sequence[str]) -> dict:
        return _sensitivity_fold(lines, self.scenario_ids)

    def set_envelope(self, scenario_id: str, value: str) -> dict:
        def decide(state: dict) -> str | None:
            return None if scenario_id in self.scenario_ids and value in SENSITIVITY_CHOICES else "not one of the scenarios or choices"
        return self._append("envelope", {"id": scenario_id, "value": value}, decide)

    def set_note(self, scenario_id: str, text: str) -> dict:
        problem = ftr.comment_problem(text, bundles=self.bundles)
        if problem:
            return {"ok": False, "why": problem, "state": self.state()}
        return self._append("envelope_comment", {"id": scenario_id, "text": str(text)}, lambda s: None if scenario_id in self.scenario_ids else "not one of the scenarios")

    def _refuse(self, *_: Any, **__: Any) -> dict:
        return {"ok": False, "why": "the sensitivity check has no such step", "state": self.state()}
    answer = comment = lock = set_overall = submit = _refuse


# -- progress and the final summary ----------------------------------------------------------------------------------------------------------------------------------------------------------
def progress(logs: Mapping[str, ToneReviewLog], order: Sequence[Mapping]) -> dict:
    """Where the reviewer is (the first review's own function: it reads only each log's status)."""
    return ftr.progress(logs, order)


def summarize(root: Path, reviewer: str, items: Mapping, order: Sequence[Mapping], set_digest: str, audit: Mapping | None = None, limitations: Sequence[Mapping] = (),
              sensitivity_ids: Sequence[str] = (), *, bundles: Any = None) -> dict:
    """The technical session summary, derived ONLY from records on disk that VERIFY against the log that closed them. A record that does not verify is NOT counted and is reported. It tabulates what the reviewer
    answered and counts judgments; it never scores or interprets them. The limitations are copied from the verified set; the optional sensitivity answers are listed when they exist and never required."""
    submitted, technical, counts = [], [], {choice: 0 for choice in ftr.OVERALL}
    for entry in order:
        identifier, item = entry["scenario_id"], items[entry["scenario_id"]]
        log = ToneReviewLog(root, reviewer, item, set_digest=set_digest, audit=audit, bundles=bundles)
        state = log.state()
        record = ftr.read_record(log.record_path) if log.record_path.exists() else None
        if state["status"] == "UNREADABLE":
            technical.append(f"{identifier}: the saved answers cannot be read")
            continue
        if not state["submitted"]:
            if record is not None:
                technical.append(f"{identifier}: a record exists but the review was never closed (an interrupted submit)")
            continue
        if record is None:
            technical.append(f"{identifier}: the record of a submitted review is missing")
            continue
        try:
            problems = record_problems(record, state, log)
        except Exception as error:                                                # a record that cannot even be checked does not verify; it never takes the screen down
            problems = [f"the record cannot be checked ({type(error).__name__})"]
        if problems:
            technical.extend(f"{identifier}: {problem}" for problem in problems)
            continue
        judgment = record["overall"]["judgment"]
        counts[judgment] = counts.get(judgment, 0) + 1
        first = record["first_pass"]
        submitted.append({"scenario_id": identifier, "title": item["title"], "record_id": record["record_id"], "overall": judgment, "overall_comment": record["overall"].get("comment") or "",
                          "first_pass": dict(first.get("answers") or {}), "first_pass_comment": first.get("comment") or "", "locked_at": first.get("locked_at"), "linkage": _as_dict(record.get("linkage"))})
    reviewed = [row["scenario_id"] for row in submitted]
    complete = reviewed == [entry["scenario_id"] for entry in order]
    envelope: list = []
    if sensitivity_ids and complete:
        sens = SensitivityLog(root, reviewer, sensitivity_ids, set_digest=set_digest, bundles=bundles).state()
        if sens["status"] == "UNREADABLE":
            technical.append("the optional sensitivity answers cannot be read")
        else:
            envelope = [{"scenario_id": identifier, "answer": sens["answers"].get(identifier), "comment": sens["comments"].get(identifier, "")} for identifier in sensitivity_ids]
    body = {"record_type": SUMMARY_TYPE, "version": VERSION, "reviewer_ref": reviewer, "set_id": SET_ID, "review_set_digest": set_digest,
            "scenarios_offered": [entry["scenario_id"] for entry in order], "scenarios_reviewed": reviewed, "complete": complete,
            "judgments": counts, "scenarios": submitted, "technical_problems": technical,
            "comments": [{"scenario_id": row["scenario_id"], "overall": row["overall"], "text": text, "stage": stage} for row in submitted
                         for stage, text in (("first pass", row["first_pass_comment"]), ("overall", row["overall_comment"])) if text],
            "limitations": [dict(entry) for entry in limitations] if complete else [],
            "sensitivity": envelope,
            "statement": STATEMENT + " The counts are the reviewer's own judgments, tabulated; the software has not interpreted them."}
    return {**body, "summary_digest": ftr._digest(body)[:16]}


def write_summary(root: Path, summary: Mapping) -> dict:
    """The technical summary file, in this review's own directory (never next to another review's)."""
    return ftr.write_summary(root, summary, subdir=SUBDIR)
