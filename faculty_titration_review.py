"""P3-440 to P3-443: the NOREPINEPHRINE TITRATION FACULTY REVIEW -- the data model and the reviewer's durable state (pure: no Streamlit, no engine, no authority, no common core).

WHAT IT IS. The same review the faculty trajectory review, the re-review and the multifamily tone review give (one page per scenario, the five questions Q1 to Q5, an optional comment, a first impression that is
LOCKED and can never be edited, an overall judgment with an optional comment, ONE submit that moves on, a summary), run on a DIFFERENT, versioned review set (``NOREPINEPHRINE_TITRATION_V1_FACULTY_REVIEW``): the
pressure response of ONE hemorrhage case (the upper gastrointestinal bleed the reviewer already knows) to a norepinephrine rate that is CHANGED by explicit orders in mcg/min -- an increase, a decrease, a stop, a
sequence of changes and a restart. It reuses ``faculty_trajectory_review`` (its event log, its lock, its atomic record, its progress) through ``faculty_trajectory_rereview`` (the blind, comparator-free variant) and
changes only what must change:

* every trajectory is the CENTER_REFERENCE trajectory exactly as the certified titration probes record holds it: nothing is recomputed, tuned or substituted here, and the stored set is pinned;
* NOTHING of the mechanism reaches the reviewer: no other setting of the response (no LOW, no HIGH), no parameter, no time constant, no tone state, no writer or rate history, no earlier trajectory or judgment, no
  legacy engine value, no flow, no delivery, no consciousness, no collapse state, and no heart rate or capillary refill (they were not recomputed for these trajectories);
* the limitations the review cannot judge are stored APART from the items and drawn ONLY in the final summary.

THE REVIEWER SEES clinical content only. THE RECORD KEEPS the audit metadata (set id and digest, item digest, the certified source and its digests); the reviewer never types or sees it, and ``load_set`` returns it
APART from the items so that nothing the page puts in front of the reviewer can carry it.

NOTHING OF THE EARLIER REVIEWS IS READ OR WRITTEN: their sets, logs and records are other files; this review's logs and records live in ``titration_review/`` and ``titration_reviews/``, and a record or log of one can
never be mistaken for another. Earlier judgments are not transferred.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

import faculty_tone_review as ftm
import faculty_trajectory_review as ftr
import faculty_trajectory_rereview as rr

VERSION = "TITRATION-REVIEW-1"
ROOT = Path(__file__).resolve().parent
SET_PATH = ROOT / "docs" / "revision" / "PHASE3_NOREPINEPHRINE_TITRATION_V1_REVIEW_SET.json"
SET_ID = "NOREPINEPHRINE_TITRATION_V1_FACULTY_REVIEW"
SET_TYPE = "PHASE3_NOREPINEPHRINE_TITRATION_REVIEW_SET"
RECORD_TYPE = "PHASE3_NOREPINEPHRINE_TITRATION_REVIEW_RECORD"
SUMMARY_TYPE = "PHASE3_NOREPINEPHRINE_TITRATION_REVIEW_SESSION_SUMMARY"
SUBDIR, RECORDS_SUBDIR = "titration_review", "titration_reviews"
#: The stored set, pinned IN CODE (the first review's rule: a digest the file attests about itself pins nothing). Regenerating the set is a deliberate, reviewed act that changes this line.
PINNED_SET_DIGEST = "576e11f2555012932c26ead757e932eeae15672bf9af05df724dec688fd2bb59"
_PIN = object()
WITNESS = "CENTER_REFERENCE"
STATEMENT = ("Synthetic development case. A faculty judgment of stored development trajectories of explicit norepinephrine rate changes (mcg/min): not a clinical validation, not a calibrated configuration, "
             "not a dose-response, not a score, not a resident pilot.")
#: The scenarios, all required, in the order the faculty asked for (FD-TITREV-04). The simple start-only case is NOT part of this review (FD-TITREV-05): it was reviewed in an earlier review.
SEQUENCE = (("TIT-1", True), ("TIT-2", True), ("TIT-3", True), ("TIT-4", True), ("TIT-5", True))
SCENARIOS = tuple(identifier for identifier, _ in SEQUENCE)
KIND_CASE = ftm.KIND_CASE
CASE_BANNER, CASE_NOTE = ftm.CASE_BANNER, ftm.CASE_NOTE
COMPLETION_NOTE = ("Your first impressions and overall judgments are saved and locked. They are your own judgments, tabulated: they are not a score, not a clinical validation, and not an approval.")
OPERATIONS = ("START", "INCREASE", "DECREASE", "STOP", "RESTART")
#: What each scenario IS (FD-TITREV-04): ``(minute, operation, rate in mcg/min after the change)``. The loader holds the stored item to it, so that a set cannot be re-signed with another history.
RATE_PLAN = {
    "TIT-1": ((2, "START", 5.0), (10, "INCREASE", 10.0)),
    "TIT-2": ((2, "START", 10.0), (10, "DECREASE", 4.0)),
    "TIT-3": ((2, "START", 10.0), (10, "STOP", 0.0)),
    "TIT-4": ((2, "START", 5.0), (10, "INCREASE", 10.0), (18, "DECREASE", 4.0), (25, "STOP", 0.0)),
    "TIT-5": ((2, "START", 10.0), (10, "STOP", 0.0), (18, "RESTART", 10.0)),
}
#: The question each scenario asks, in the words of the faculty decision (FD-TITREV-07). Drawn as "What you are judging"; the loader refuses an item whose purpose is anything else.
QUESTIONS = {
    "TIT-1": "Does the pressure response increase smoothly and at an appropriate time after the norepinephrine rate is increased?",
    "TIT-2": "Does the pressure response decrease smoothly and at an appropriate time after the norepinephrine rate is reduced?",
    "TIT-3": "After norepinephrine is stopped, does the pressure effect decay with a clinically plausible delay rather than disappearing instantly?",
    "TIT-4": "Across sequential rate changes, does the pressure trajectory follow the ordered norepinephrine dose changes in the correct direction and sequence?",
    "TIT-5": ("After norepinephrine is stopped and later restarted at an explicit valid rate, does the pressure response reappear causally without retaining an inappropriate residual effect?"),
}
#: The limitations the review cannot judge (P3-443), stored apart from the items and drawn only in the final summary.
LIMITATION_IDS = ("EXPLICIT_ABSOLUTE_MCG_MIN_ONLY", "NO_WEIGHT_BASED_DOSING", "NO_MAP_TARGET_TITRATION", "MALFORMED_ORDER_CLOSES_THE_MODELLED_INFUSION", "CONSCIOUSNESS_UNDER_TONE_UNRESOLVED",
                  "COMMON_TONE_PUMP_DEPENDENCE_NOT_YET_VALIDATED")
LIMITATIONS = (
    {"id": LIMITATION_IDS[0], "text": "Only explicit absolute norepinephrine rates in mcg/min are represented. A relative instruction (for example, \"increase norepinephrine\") while no infusion is running is not supported."},
    {"id": LIMITATION_IDS[1], "text": "Weight-based doses (mcg/kg/min) are not represented and are never converted."},
    {"id": LIMITATION_IDS[2], "text": "Titration to a pressure target (for example, \"titrate to MAP 65\") is not represented: no rate is ever chosen from a pressure."},
    {"id": LIMITATION_IDS[3], "text": ("An order the system cannot read as an explicit absolute rate (an unsupported or malformed order) ends the modelled infusion for the rest of the encounter. "
                                      "It is declared, and nothing later in that encounter recovers it.")},
    {"id": LIMITATION_IDS[4], "text": "Consciousness under vascular-tone support was neither shown nor judged in this review. It remains unresolved."},
    {"id": LIMITATION_IDS[5], "text": ("How strongly the pressure response depends on the state of the pump is not yet validated. This review used a hemorrhage case and does not support the use of a vasopressor "
                                       "in pump-limited conditions.")},
)

#: Words a reviewer-facing field must never carry (defence in depth: the loader refuses an item that does). The identity of the configuration, the other settings, the earlier sets, the mechanism and the
#: parameters are not reviewer vocabulary. Upper-case LOW and HIGH are the names of the other settings (the clinical words "low" and "high" are ordinary).
_LEAK = re.compile(ftm._LEAK.pattern + r"|writer|rate[ _]history|shadow|artifact|snapshot|lineage|mcg/kg|mg/kg|dose[ _-]response|map[ _-]target|steady[ _-]state|\bsupport[ _]level\b|\btau\b|time[ _-]constants?|cardiac[ _-]flow|"
                   r"delivery of|o2 delivery|\bpulse\b|\bgain\b|titrat|soft collapse", re.I)
_LEAK_NAMES = ftm._LEAK_NAMES
_SHOWN_KEYS = ("scenario_id", "short", "title", "kind", "banner", "note", "context", "baseline_facts", "purpose", "arrival", "intervention", "timeline", "rate_changes", "common", "table_minutes")
#: The exact keys of an item and of its parts. An item with another key (a comparator, a parameter, a heart rate) is not this package, even when re-signed and pinned: nothing the page does not draw may be stored
#: with the item.
ITEM_KEYS = frozenset(_SHOWN_KEYS) | {"stopped", "required"}
ARRIVAL_KEYS = ftm.ARRIVAL_KEYS
ARRIVAL_SHOWN = ftm.ARRIVAL_SHOWN
ROW_KEYS = rr.ROW_KEYS
POINT_KEYS = rr.POINT_KEYS
CHANGE_KEYS = frozenset({"n", "minute", "operation", "rate_mcg_min"})
LIMITATION_KEYS = frozenset({"id", "text"})
MARKER_WORDS = {"START": "start {rate}", "INCREASE": "up to {rate}", "DECREASE": "down to {rate}", "STOP": "stop", "RESTART": "restart {rate}"}


def _seal_digest(value: Any) -> str:
    """The digest a sealed historical record carries (the same canonical form as ``historical_records.digest_of``; a test holds the two equal). Kept here so this pure module imports nothing of the layer."""
    return ftm._seal_digest(value)


def rate_text(rate: float) -> str:
    return f"{rate:g}"


def change_text(change: Mapping) -> str:
    """The order of one change as the reviewer reads it ('Start norepinephrine 5 mcg/min', 'Stop norepinephrine')."""
    operation, rate = change["operation"], rate_text(change["rate_mcg_min"])
    return {"START": f"Start norepinephrine {rate} mcg/min", "INCREASE": f"Increase norepinephrine to {rate} mcg/min", "DECREASE": f"Decrease norepinephrine to {rate} mcg/min",
            "STOP": "Stop norepinephrine", "RESTART": f"Restart norepinephrine at {rate} mcg/min"}[operation]


def marker_label(change: Mapping) -> str:
    """The short label drawn on the graph at the minute of a change: the number of the row in the table of what was done and what the change was."""
    return f"{change['n']} · " + MARKER_WORDS[change["operation"]].format(rate=rate_text(change["rate_mcg_min"]))


def markers(item: Mapping) -> list:
    """Where the graph marks each change of the rate: ``[{"minute", "label"}]`` -- one per change, nothing else."""
    return [{"minute": int(change["minute"]), "label": marker_label(change)} for change in item["rate_changes"]]


def _exact(value: Any, keys: frozenset) -> bool:
    return isinstance(value, dict) and set(value) == keys


def _whole_pressures(points: Sequence[Mapping], label: str) -> str | None:
    return ftm._whole_pressures(points, label)


def _transition_problem(previous: float, operation: str, rate: float) -> str | None:
    """Whether a change of the rate is what its name says: from the rate that ran before it (0 when nothing ran)."""
    ok = {"START": previous == 0 and rate > 0, "RESTART": previous == 0 and rate > 0, "INCREASE": previous > 0 and rate > previous, "DECREASE": 0 < rate < previous, "STOP": previous > 0 and rate == 0}[operation]
    return None if ok else f"{operation} from {previous:g} to {rate:g} mcg/min is not what its name says"


# -- the stored set ---------------------------------------------------------------------------------------------------------------------------------------------------------------
def item_problems(item: Mapping) -> list:
    """Why a stored scenario cannot be reviewed. Empty means it can. Checked here: the exact keys, the types, the label, the question (the faculty's own), the rate plan and what each change is, the table of what was
    done, the whole-mmHg pressures and the minutes, and that no reviewer-facing field carries a word of the mechanism. NOT re-derived: the authored narrative (context, baseline findings, the result column of the table), which
    only the digest pinned in code guards. A malformed item is a problem, never an exception."""
    identifier = item.get("scenario_id") if isinstance(item, dict) else None
    try:
        return _item_problems(item)
    except Exception as error:                                                    # a malformed stored item must be refused, not crash the page
        return [f"{identifier or 'a scenario'}: the stored scenario cannot be checked ({type(error).__name__})"]


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
            or not isinstance(body["table_minutes"], list) or not isinstance(body["rate_changes"], list) or any(not isinstance(fact, str) or not fact for fact in body["baseline_facts"])):
        return [f"{identifier}: a field has the wrong type"]
    if (not _exact(body["arrival"], ARRIVAL_KEYS) or any(not _exact(row, ROW_KEYS) for row in body["timeline"]) or any(not _exact(point, POINT_KEYS) for point in body["common"])
            or any(not _exact(change, CHANGE_KEYS) for change in body["rate_changes"])):
        return [f"{identifier}: the arrival, a timeline row, a rate change or a pressure point does not have exactly the stored keys"]
    if body["kind"] != KIND_CASE or body["banner"] != CASE_BANNER or body["note"] != CASE_NOTE:
        problems.append(f"{identifier}: an authored case must carry its own label")
    if body["purpose"] != QUESTIONS[identifier]:
        problems.append(f"{identifier}: the question is not the faculty's own")
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
    if any(not isinstance(arrival.get(key), int) or isinstance(arrival.get(key), bool) for key in ARRIVAL_KEYS):
        problems.append(f"{identifier}: an authored case states its arrival pressure, saturation and respiratory rate")
    changes, rows = list(body["rate_changes"]), list(body["timeline"])
    plan = RATE_PLAN[identifier]
    if [(change.get("minute"), change.get("operation"), change.get("rate_mcg_min")) for change in changes] != [tuple(step) for step in plan] or [change.get("n") for change in changes] != list(range(1, len(plan) + 1)):
        problems.append(f"{identifier}: the rate changes are not the ones this scenario is (its plan is fixed in code)")
    else:
        previous = 0.0
        for change in changes:
            wrong = _transition_problem(previous, change["operation"], float(change["rate_mcg_min"]))
            if wrong:
                problems.append(f"{identifier}: {wrong}")
            previous = float(change["rate_mcg_min"])
    if [row.get("n") for row in rows] != list(range(1, len(rows) + 1)) or any(row.get("executed") is not True or row.get("intervention") is not True for row in rows):
        problems.append(f"{identifier}: every row of the timeline is one executed change of the rate, numbered")
    elif len(rows) != len(changes) or any((row["minute"], row["action"]) != (change["minute"], change_text(change)) for row, change in zip(rows, changes)):
        problems.append(f"{identifier}: the table of what was done is not the changes of the rate")
    elif any(row["minute"] not in minutes for row in rows):
        problems.append(f"{identifier}: a change is not at a minute of the trajectory")
    tables = list(body["table_minutes"])
    if (tables[0] != 0 or tables[-1] != minutes[-1] or any(not isinstance(a, int) or not isinstance(b, int) or b <= a for a, b in zip(tables, tables[1:])) or any(minute not in minutes for minute in tables)
            or any(change["minute"] not in tables for change in changes)):
        problems.append(f"{identifier}: the table minutes are not minutes of the trajectory, from the first to the last, including every change")
    text = json.dumps(body, sort_keys=True)
    found = _LEAK.search(text) or _LEAK_NAMES.search(text)
    if found:
        problems.append(f"{identifier}: a reviewer-facing field carries '{found.group(0)}'")
    return problems


def _limitation_problems(limitations: Any) -> list:
    if (not isinstance(limitations, list) or [entry.get("id") if isinstance(entry, dict) else None for entry in limitations] != list(LIMITATION_IDS)
            or any(not _exact(entry, LIMITATION_KEYS) or not isinstance(entry["text"], str) or not entry["text"] for entry in limitations)):
        return ["the limitations of the review are not the ones the review states"]
    return []


def load_set(path: Path | None = None, *, expected_digest: Any = _PIN) -> dict:
    """The stored set, verified. ``{"ok", "problems", "digest", "items", "limitations", "audit"}``; ``items`` are what the reviewer may see, ``limitations`` is what the final summary states, and ``audit`` is kept apart
    from both. A set whose own digest does not recompute, that is not the pinned one, or that does not hold exactly the scenarios offers nothing. Never raises."""
    result: dict = {"ok": False, "problems": [], "digest": None, "items": {}, "limitations": [], "audit": {}}
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
    audit = record.get("audit")
    if not isinstance(audit, dict):
        return {**result, "problems": problems + ["the review set does not hold its audit as a record"]}
    try:
        problems += _limitation_problems(record.get("limitations"))
    except Exception as error:                                                    # a malformed stored section is refused, never an exception
        problems.append(f"the limitations cannot be checked ({type(error).__name__})")
    if problems:
        return {**result, "problems": problems}
    return {"ok": True, "problems": [], "digest": claimed, "items": items, "limitations": [dict(entry) for entry in record["limitations"]], "audit": dict(audit)}


# -- what the reviewer is shown --------------------------------------------------------------------------------------------------------------------------------------------------
def blind_view(item: Mapping) -> dict:
    """EVERYTHING the reviewer sees for a scenario. There is no other view: no other setting of the response, no comparator, no heart rate and no capillary refill exist in it."""
    return {"scenario_id": item["scenario_id"], "short": item["short"], "title": item["title"], "kind": item["kind"], "banner": item["banner"], "note": item["note"], "context": item["context"],
            "baseline_facts": list(item["baseline_facts"]), "purpose": item["purpose"], "arrival": {key: item["arrival"][key] for key in ARRIVAL_SHOWN}, "intervention": item["intervention"],
            "timeline": [dict(row) for row in item["timeline"]], "halted": False, "stop_minute": None, "common": [dict(point) for point in item["common"]], "markers": markers(item),
            "questions": [dict(question, choices=list(question["choices"])) for question in ftr.required_questions(item)[0]]}


def sequence(items: Mapping) -> list:
    """The scenarios actually offered, in order: ``[{"scenario_id", "required"}]``."""
    return [{"scenario_id": identifier, "required": required} for identifier, required in SEQUENCE if identifier in items]


def values_table(item: Mapping) -> list:
    """The pressure points of the table next to the chart (the minutes the item names): minute, SBP, DBP, MAP. Nothing else."""
    return ftm.values_table(item)


def y_axis_max(item: Mapping, floor: int = 140) -> int:
    return ftm.y_axis_max(item, floor)


# -- the durable review ----------------------------------------------------------------------------------------------------------------------------------------------------------------
class TitrationReviewLog(rr.ReReviewLog):
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


def record_problems(record: Mapping, state: Mapping, log: TitrationReviewLog) -> list:
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


# -- progress and the final summary ----------------------------------------------------------------------------------------------------------------------------------------------------------
def progress(logs: Mapping[str, TitrationReviewLog], order: Sequence[Mapping]) -> dict:
    """Where the reviewer is (the first review's own function: it reads only each log's status)."""
    return ftr.progress(logs, order)


def summarize(root: Path, reviewer: str, items: Mapping, order: Sequence[Mapping], set_digest: str, audit: Mapping | None = None, limitations: Sequence[Mapping] = (), *, bundles: Any = None) -> dict:
    """The technical session summary, derived ONLY from records on disk that VERIFY against the log that closed them. A record that does not verify is NOT counted and is reported. It tabulates what the reviewer
    answered and counts judgments; it never scores or interprets them. The limitations are copied from the verified set and only once the review is complete."""
    submitted, technical, counts = [], [], {choice: 0 for choice in ftr.OVERALL}
    for entry in order:
        identifier, item = entry["scenario_id"], items[entry["scenario_id"]]
        log = TitrationReviewLog(root, reviewer, item, set_digest=set_digest, audit=audit, bundles=bundles)
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
    body = {"record_type": SUMMARY_TYPE, "version": VERSION, "reviewer_ref": reviewer, "set_id": SET_ID, "review_set_digest": set_digest,
            "scenarios_offered": [entry["scenario_id"] for entry in order], "scenarios_reviewed": reviewed, "complete": complete,
            "judgments": counts, "scenarios": submitted, "technical_problems": technical,
            "comments": [{"scenario_id": row["scenario_id"], "overall": row["overall"], "text": text, "stage": stage} for row in submitted
                         for stage, text in (("first pass", row["first_pass_comment"]), ("overall", row["overall_comment"])) if text],
            "limitations": [dict(entry) for entry in limitations] if complete else [],
            "statement": STATEMENT + " The counts are the reviewer's own judgments, tabulated; the software has not interpreted them."}
    return {**body, "summary_digest": ftr._digest(body)[:16]}


def write_summary(root: Path, summary: Mapping) -> dict:
    """The technical summary file, in this review's own directory (never next to another review's)."""
    return ftr.write_summary(root, summary, subdir=SUBDIR)
