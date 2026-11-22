"""P3-514: the GI MANAGEMENT-TRACE FACULTY REVIEW -- the data model and the reviewer's durable state (pure: no Streamlit, no engine, no authority, no common core).

WHAT IT IS. The same review the faculty trajectory review, the re-review, the tone review and the titration review give (one page per scenario, the five questions Q1 to Q5, an optional comment, a first impression
that is LOCKED and can never be edited, an overall judgment, ONE submit that moves on, a summary), run on a DIFFERENT, versioned review set (``GI_MANAGEMENT_TRACE_V1_FACULTY_REVIEW``): ten management paths of ONE
upper gastrointestinal hemorrhage case from the same arrival, played through the live development authority, each shown as its action sequence, its committed pressure trajectory, its management trace and its
development boundary. ONE focused question is added to the five (FD-MTRACE-02): Q6, the MANAGEMENT MEANING of the path (reasonable, temporizing, incomplete, clearly nonbeneficial), answered blind; the category the
path was written with is a proposal and is shown only in the final summary, beside the reviewer's own answers.

NOTHING OF THE MECHANISM reaches the reviewer: no grant, snapshot, digest, tone value, parameter, writer, heart rate, capillary refill or mental status; the structured trace and its provenance stay in the set's audit,
apart from the items, and the limitations the review cannot judge are drawn ONLY in the final summary. Earlier reviews' sets, logs and records are other files; nothing of them is read or written here.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

import faculty_tone_review as ftm
import faculty_trajectory_review as ftr
import faculty_trajectory_rereview as rr

VERSION = "MANAGEMENT-REVIEW-1"
ROOT = Path(__file__).resolve().parent
SET_PATH = ROOT / "docs" / "revision" / "PHASE3_GI_MANAGEMENT_TRACE_V1_REVIEW_SET.json"
SET_ID = "GI_MANAGEMENT_TRACE_V1_FACULTY_REVIEW"
SET_TYPE = "PHASE3_GI_MANAGEMENT_TRACE_REVIEW_SET"
RECORD_TYPE = "PHASE3_GI_MANAGEMENT_TRACE_REVIEW_RECORD"
SUMMARY_TYPE = "PHASE3_GI_MANAGEMENT_TRACE_REVIEW_SESSION_SUMMARY"
SUBDIR, RECORDS_SUBDIR = "management_review", "management_reviews"
#: The stored set, pinned IN CODE (a digest the file attests about itself pins nothing). Regenerating the set is a deliberate, reviewed act that changes this line.
PINNED_SET_DIGEST = "235b5a40443de28191166334d5ae46c6ccb7e498520235bb900901cae7230c8b"
_PIN = object()
STATEMENT = ("Synthetic development case. A faculty judgment of stored development paths of management of one upper gastrointestinal bleed, played through the development model: not a clinical validation, not a "
             "calibrated configuration, not a score, not a resident pilot.")
PATHS = ("A", "B", "C", "D", "E", "F", "G", "H", "I", "J")
SEQUENCE = tuple((f"MT-{path}", True) for path in PATHS)
SCENARIOS = tuple(identifier for identifier, _ in SEQUENCE)
KIND_CASE, CASE_BANNER, CASE_NOTE = ftm.KIND_CASE, ftm.CASE_BANNER, ftm.CASE_NOTE
COMPLETION_NOTE = ("Your first impressions and overall judgments are saved and locked. They are your own judgments, tabulated: they are not a score, not a clinical validation, and not an approval.")
EXTRA_QUESTIONS = ("Q6",)
CATEGORY_WORDS = {"REASONABLE": "Reasonable", "TEMPORIZING": "Temporizing", "INCOMPLETE": "Incomplete", "CLEARLY_NONBENEFICIAL": "Clearly nonbeneficial"}
LIMITATION_IDS = ("BLEEDING_NOT_CONTROLLED", "SOURCE_CONTROL_REACHABLE_IN_THE_LIVE_PAGE_NOT_REVIEWED", "CONSCIOUSNESS_UNDER_TONE_UNRESOLVED", "ONLY_THE_BLOOD_PRESSURE_IS_AUTHORITATIVE",
                  "RED_CELL_RESPONSE_AT_THE_LOW_END", "TURN_TIMING", "COMMON_TONE_PUMP_DEPENDENCE_NOT_YET_VALIDATED", "SCRIPTED_PATHS")
LIMITATIONS = (
    {"id": LIMITATION_IDS[0], "text": "The bleeding continues in every path: no path controls it, and every path ends at a development boundary before definitive control of the bleeding."},
    {"id": LIMITATION_IDS[1], "text": ("In the live development page, a consultation of gastroenterology can lead to an endoscopy performed by the simulator, with control of the bleeding. That course has never been "
                                       "reviewed and is outside this package (the development encounter ends at the request). Whether it may be reviewed, or must be blocked, is a faculty decision.")},
    {"id": LIMITATION_IDS[2], "text": ("Consciousness under vasopressor support is not represented. The mental status the live page shows comes from the earlier engine: under a vasopressor it can stay normal while the "
                                       "pressure shown falls. It is not shown in this review and is not evidence of resuscitation.")},
    {"id": LIMITATION_IDS[3], "text": "Only the blood pressure is produced by the development model under review; heart rate, capillary refill and the other findings are not part of these trajectories."},
    {"id": LIMITATION_IDS[4], "text": "The pressure response to red cells is at the low end of what was ratified for development (a monitored limitation, not recalibrated)."},
    {"id": LIMITATION_IDS[5], "text": ("Without a stated reassessment interval, a turn lasts as long as what was given (two units of red cells hold the encounter for 60 minutes). Every path here states its "
                                       "reassessment interval, and the pressure is seen only at each reassessment.")},
    {"id": LIMITATION_IDS[6], "text": "How strongly the pressure response depends on the state of the pump is not yet validated: nothing here supports a vasopressor in pump-limited conditions."},
    {"id": LIMITATION_IDS[7], "text": ("Every path is a scripted development path: no resident typed these orders and no resident reasoning is shown. The scenario priorities and the categories are proposals for "
                                       "faculty review, not the faculty's and not a resident's.")},
)
#: Words a reviewer-facing field must never carry (defence in depth: the loader refuses an item that does). The tone review's list, the titration review's additions and this package's own: the identity of the
#: configuration, the provenance machinery and the words of recovery that the development model does not support.
_LEAK = re.compile(ftm._LEAK.pattern + r"|grant|fingerprint|digest|snapshot|lineage|artifact|shadow|authorit|writer|rate[ _]history|\btau\b|\bgain\b|titrat|"
                   r"resuscitation (?:is )?(?:complete|successful)|successful resuscitation|shock (?:is )?(?:corrected|resolved)|bleeding (?:is |has )?(?:controlled|stopped)|\bstabili[sz]ed\b|\brecovered\b", re.I)
_LEAK_NAMES = ftm._LEAK_NAMES
#: Fixed texts that NEGATE the words above and are reviewed as they stand (the boundary messages): they are checked for equality, not scanned.
_FIXED = ("boundary",)
_SHOWN_KEYS = ("scenario_id", "short", "title", "kind", "banner", "note", "context", "baseline_facts", "purpose", "arrival", "timeline", "common", "markers", "trace", "boundary")
ITEM_KEYS = frozenset(_SHOWN_KEYS) | {"stopped", "required"}
ARRIVAL_KEYS, ARRIVAL_SHOWN = ftm.ARRIVAL_KEYS, ftm.ARRIVAL_SHOWN
ROW_KEYS, POINT_KEYS = rr.ROW_KEYS, rr.POINT_KEYS
MARKER_KEYS = frozenset({"minute", "label"})
BLOCK_KEYS, BOUNDARY_BLOCK_KEYS, LINE_KEYS = frozenset({"n", "minutes", "orders", "lines"}), frozenset({"n", "minutes", "orders", "lines", "boundary"}), frozenset({"label", "text", "provenance"})
BOUNDARY_KEYS = frozenset({"minute", "message"})
LIMITATION_KEYS = frozenset({"id", "text"})
PROVENANCE_WORDS = {"OBSERVED": "observed", "AUTHORED": "development path", "MODEL_DERIVED": "model reading", "FACULTY_DEFINED": "faculty decision", "RESIDENT_EXPRESSED": "resident", "UNKNOWN": "not known"}
#: The fixed boundary texts of the development encounter (``development_management_trace``): an item's boundary must be exactly one of them. Copied here so this pure module imports nothing of the trace module;
#: a test holds the copies equal.
BOUNDARY_MESSAGES = (
    ("Development model boundary. This development encounter covers only the initial resuscitation of an upper gastrointestinal bleed, up to two hours after arrival. The bleeding has not been controlled in this "
     "encounter: definitive control of the bleeding source is outside this development model. Reaching this point does not mean that the patient has recovered, that the bleeding has stopped, that management is "
     "complete, or that discharge is safe."),
    ("Development model boundary. The request for definitive control of the bleeding has been recorded. What follows it is outside this development model, so the development encounter ends here. The bleeding "
     "has not been controlled in this encounter. Reaching this point does not mean that the patient has recovered, that the bleeding has stopped, that management is complete, or that discharge is safe."),
)


def _seal_digest(value: Any) -> str:
    return ftm._seal_digest(value)


def _exact(value: Any, keys: frozenset) -> bool:
    return isinstance(value, dict) and set(value) == keys


def _scan(value: Any) -> str | None:
    text = json.dumps(value, sort_keys=True)
    found = _LEAK.search(text) or _LEAK_NAMES.search(text)
    return found.group(0) if found else None


# -- the stored set ---------------------------------------------------------------------------------------------------------------------------------------------------------------
def item_problems(item: Mapping) -> list:
    """Why a stored scenario cannot be reviewed. Empty means it can. A malformed item is a problem, never an exception."""
    identifier = item.get("scenario_id") if isinstance(item, dict) else None
    try:
        return _item_problems(item)
    except Exception as error:
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
        if body[key] in (None, "", [], {}) and key != "markers":
            problems.append(f"{identifier}: {key} is missing")
    if problems:
        return problems
    strings = ("short", "title", "kind", "banner", "note", "context", "purpose")
    if (not all(isinstance(body[key], str) for key in strings) or not all(isinstance(body[key], list) for key in ("timeline", "common", "markers", "trace", "baseline_facts"))
            or any(not isinstance(fact, str) or not fact for fact in body["baseline_facts"])):
        return [f"{identifier}: a field has the wrong type"]
    if (not _exact(body["arrival"], ARRIVAL_KEYS) or any(not _exact(row, ROW_KEYS) for row in body["timeline"]) or any(not _exact(point, POINT_KEYS) for point in body["common"])
            or any(not _exact(marker, MARKER_KEYS) for marker in body["markers"]) or not _exact(body["boundary"], BOUNDARY_KEYS)):
        return [f"{identifier}: the arrival, a timeline row, a pressure point, a marker or the boundary does not have exactly the stored keys"]
    if body["kind"] != KIND_CASE or body["banner"] != CASE_BANNER or body["note"] != CASE_NOTE:
        problems.append(f"{identifier}: an authored case must carry its own label")
    if body.get("stopped") is not False or body.get("required") is not True:
        problems.append(f"{identifier}: the page draws no stop and every scenario of this package is required")
    arrival, points = dict(body["arrival"]), list(body["common"])
    minutes = [point.get("minute") for point in points]
    if minutes[0] != 0 or any(not isinstance(a, int) or not isinstance(b, int) or b <= a for a, b in zip(minutes, minutes[1:])):
        problems.append(f"{identifier}: the minutes of the trajectory do not start at 0 and increase")
    problem = ftm._whole_pressures(points, identifier)
    if problem:
        problems.append(problem)
    if (points[0].get("sbp"), points[0].get("dbp"), points[0].get("map")) != (arrival.get("sbp"), arrival.get("dbp"), arrival.get("map")):
        problems.append(f"{identifier}: the first point is not the arrival pressure")
    if any(not isinstance(arrival.get(key), int) or isinstance(arrival.get(key), bool) for key in ARRIVAL_KEYS):
        problems.append(f"{identifier}: an authored case states its arrival pressure, saturation and respiratory rate")
    rows = list(body["timeline"])
    if [row.get("n") for row in rows] != list(range(1, len(rows) + 1)):
        problems.append(f"{identifier}: the rows of what was done are not numbered in order")
    if any(marker["minute"] not in {row["minute"] for row in rows} for marker in body["markers"]):
        problems.append(f"{identifier}: a marker is not at the minute of an action")
    boundary = dict(body["boundary"])
    if boundary["message"] not in BOUNDARY_MESSAGES or not isinstance(boundary["minute"], int) or boundary["minute"] < minutes[-1]:
        problems.append(f"{identifier}: the boundary is not one of the development boundaries, or it comes before the last reading")
    blocks = list(body["trace"])
    for block in blocks:
        keys = BOUNDARY_BLOCK_KEYS if isinstance(block, dict) and block.get("boundary") else BLOCK_KEYS
        if not _exact(block, keys) or any(not _exact(line, LINE_KEYS) or line["provenance"] not in PROVENANCE_WORDS for line in block["lines"]):
            return problems + [f"{identifier}: a block of the management trace does not have exactly its stored keys and a known provenance"]
    steps = [block for block in blocks if not block.get("boundary")]
    if len(steps) != len(rows) or [block["n"] for block in steps] != [row["n"] for row in rows]:
        problems.append(f"{identifier}: the management trace does not have one block per row of what was done")
    if not blocks or not blocks[-1].get("boundary") or blocks[-1]["lines"][0]["text"] != boundary["message"]:
        problems.append(f"{identifier}: the management trace does not end at its development boundary")
    shown = {key: value for key, value in body.items() if key != "boundary"}
    shown["trace"] = [block for block in blocks if not block.get("boundary")]
    found = _scan(shown)
    if found:
        problems.append(f"{identifier}: a reviewer-facing field carries '{found}'")
    return problems


def _limitation_problems(limitations: Any) -> list:
    if (not isinstance(limitations, list) or [entry.get("id") if isinstance(entry, dict) else None for entry in limitations] != list(LIMITATION_IDS)
            or any(not _exact(entry, LIMITATION_KEYS) or not isinstance(entry["text"], str) or not entry["text"] for entry in limitations)):
        return ["the limitations of the review are not the ones the review states"]
    return []


def load_set(path: Path | None = None, *, expected_digest: Any = _PIN) -> dict:
    """The stored set, verified. ``{"ok", "problems", "digest", "items", "limitations", "categories", "audit"}``; ``items`` are what the reviewer may see, ``limitations`` and ``categories`` are what the final summary
    states, and ``audit`` is kept apart from all of them. Never raises."""
    result: dict = {"ok": False, "problems": [], "digest": None, "items": {}, "limitations": [], "categories": {}, "audit": {}}
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
    audit = record.get("audit")
    if not isinstance(audit, dict):
        return {**result, "problems": problems + ["the review set does not hold its audit as a record"]}
    try:
        problems += _limitation_problems(record.get("limitations"))
        categories = {identifier: CATEGORY_WORDS[dict(audit["paths"][identifier])["category_proposed"]] for identifier in SCENARIOS}
    except Exception as error:
        return {**result, "problems": problems + [f"the limitations or the proposed categories cannot be checked ({type(error).__name__})"]}
    if problems:
        return {**result, "problems": problems}
    items = {item["scenario_id"]: dict(item, extra_questions=list(EXTRA_QUESTIONS)) for item in listed}
    return {"ok": True, "problems": [], "digest": claimed, "items": items, "limitations": [dict(entry) for entry in record["limitations"]], "categories": categories, "audit": dict(audit)}


# -- what the reviewer is shown --------------------------------------------------------------------------------------------------------------------------------------------------
def blind_view(item: Mapping) -> dict:
    """EVERYTHING the reviewer sees for a scenario. There is no other view: no proposed category, no audit, no mechanism, no heart rate and no mental status exist in it."""
    return {"scenario_id": item["scenario_id"], "short": item["short"], "title": item["title"], "kind": item["kind"], "banner": item["banner"], "note": item["note"], "context": item["context"],
            "baseline_facts": list(item["baseline_facts"]), "purpose": item["purpose"], "arrival": {key: item["arrival"][key] for key in ARRIVAL_SHOWN},
            "timeline": [dict(row) for row in item["timeline"]], "halted": False, "stop_minute": None, "common": [dict(point) for point in item["common"]], "markers": [dict(marker) for marker in item["markers"]],
            "trace": [dict(block, lines=[dict(line, tag=PROVENANCE_WORDS[line["provenance"]]) for line in block["lines"]]) for block in item["trace"]], "boundary": dict(item["boundary"]),
            "questions": [dict(question, choices=list(question["choices"])) for question in ftr.required_questions(item)[0]]}


def sequence(items: Mapping) -> list:
    return [{"scenario_id": identifier, "required": required} for identifier, required in SEQUENCE if identifier in items]


def values_table(item: Mapping) -> list:
    return [{"minute": point["minute"], "sbp": int(point["sbp"]), "dbp": int(point["dbp"]), "map": int(point["map"])} for point in item["common"]]


def y_axis_max(item: Mapping, floor: int = 140) -> int:
    return ftm.y_axis_max(item, floor)


# -- the durable review ----------------------------------------------------------------------------------------------------------------------------------------------------------
class ManagementReviewLog(rr.ReReviewLog):
    """The durable state of ONE reviewer on ONE scenario of this set: the blind re-review's append-only, hash-chained, locked event log (no comparator step) in this review's own files, with Q6."""
    SUBDIR_NAME, RECORDS_NAME = SUBDIR, RECORDS_SUBDIR

    def _stem(self) -> str:
        return f"{self.item['scenario_id']}__{SET_ID}__{self.set_digest[:12]}__{self.item_digest}"

    def _record(self, state: Mapping) -> dict:
        body = {"record_type": RECORD_TYPE, "version": VERSION, "reviewer_ref": self.reviewer, "reviewer_role": self.account.get("role"), "set_id": SET_ID, "scenario_id": self.item["scenario_id"],
                "linkage": {"set_digest": self.set_digest, "item_digest": self.item_digest, "trace_digest": dict(dict(self.audit.get("paths") or {}).get(self.item["scenario_id"]) or {}).get("trace_digest")},
                "first_pass": {"answers": dict(state["locked_answers"] or state["blind"]), "comment": state["locked_comment"] if state["locked_comment"] is not None else state["blind_comment"],
                               "locked_at": state["locked_at"], "answers_at_lock": dict(state["locked_answers"] or state["blind"])},
                "overall": {"judgment": state["overall"], "comment": state["overall_comment"]},
                "comparator_shown": False, "event_log_head": state["head"], "statement": STATEMENT}
        body["record_id"] = ftr._digest(body)[:16]
        return body


def _as_dict(value: Any) -> dict:
    return dict(value) if isinstance(value, dict) else {}


def record_problems(record: Mapping, state: Mapping, log: ManagementReviewLog) -> list:
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
def progress(logs: Mapping[str, ManagementReviewLog], order: Sequence[Mapping]) -> dict:
    return ftr.progress(logs, order)


def summarize(root: Path, reviewer: str, items: Mapping, order: Sequence[Mapping], set_digest: str, audit: Mapping | None = None, limitations: Sequence[Mapping] = (), categories: Mapping | None = None, *,
              bundles: Any = None) -> dict:
    """The technical session summary, derived ONLY from records on disk that VERIFY against the log that closed them (the titration review's own rule). A record that does not verify is NOT counted and is reported.
    It tabulates what the reviewer answered and counts judgments; it never scores or interprets them. The limitations and, beside each Q6 answer, the category the path was written with (a proposal) are stated
    only once the review is complete."""
    submitted, technical, counts = [], [], {choice: 0 for choice in ftr.OVERALL}
    for entry in order:
        identifier, item = entry["scenario_id"], items[entry["scenario_id"]]
        log = ManagementReviewLog(root, reviewer, item, set_digest=set_digest, audit=audit, bundles=bundles)
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
        except Exception as error:
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
    for row in submitted:
        row["proposed_category"] = dict(categories or {}).get(row["scenario_id"]) if complete else None
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
