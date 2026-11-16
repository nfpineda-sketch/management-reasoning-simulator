"""P3-350 to P3-355: the FACULTY TRAJECTORY RE-REVIEW -- the data model and the reviewer's durable state of a SECOND, BLIND faculty review (pure: no Streamlit, no engine, no authority, no common core).

WHAT IT IS. The same review the faculty trajectory review gives (one page per scenario, five questions, an optional comment, a first impression that is LOCKED and can never be edited, an overall judgment, a
submit that moves on, a summary), run on a DIFFERENT, versioned review set: the four scenarios FR-B, FR-C, FR-E and FR-G with the trajectories of ONE candidate configuration, taken from the certified static kit
(``docs/revision/PHASE3_JOINT_REGION_V1_CANDIDATE_REVIEW_SET.json``, first set). It reuses ``faculty_trajectory_review`` (its event log, its lock, its atomic record, its progress) and changes only what must change:

* there is NO comparator: nothing here can return a legacy number, an earlier trajectory or another candidate (FD-REREVIEW-05), so there is no reveal step and no question about one;
* the overall judgment is given after the lock, with an optional comment, and ONE submit closes the scenario;
* the items carry no bundle (no authority ran: the pressures are model analysis on a counterfactual copy of the captured scenario), so none is invented.

THE REVIEWER SEES clinical content only. THE RECORD KEEPS the audit metadata (set id and digest, item digest, which candidate and which witness, the digests of the sources); the reviewer never types or sees it, and ``load_set``
returns it APART from the items so that nothing the page puts in front of the reviewer can carry it.

NOTHING OF THE FIRST REVIEW IS READ OR WRITTEN: its set (``PHASE3_FACULTY_TRAJECTORY_REVIEW_SET.json``), its logs (``trajectory/``) and its records (``trajectory_reviews/``) are other files; the re-review logs and records live
in ``trajectory_rereview/`` and ``trajectory_rereviews/``, and a record or log of one can never be mistaken for the other. Original judgments are not transferred (FD-RATE-20).
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

import faculty_trajectory_review as ftr

VERSION = "REREVIEW-1"
ROOT = Path(__file__).resolve().parent
SET_PATH = ROOT / "docs" / "revision" / "PHASE3_JOINT_REGION_V1_FACULTY_REREVIEW_SET.json"
CANDIDATE_SET_PATH = ROOT / "docs" / "revision" / "PHASE3_JOINT_REGION_V1_CANDIDATE_REVIEW_SET.json"
BLIND_KEY_PATH = ROOT / "docs" / "revision" / "PHASE3_JOINT_REGION_V1_BLIND_KEY.json"
SET_ID = "GI_JOINT_REGION_V1_FACULTY_REREVIEW"
SET_TYPE = "PHASE3_FACULTY_TRAJECTORY_REREVIEW_SET"
RECORD_TYPE = "PHASE3_FACULTY_TRAJECTORY_REREVIEW_RECORD"
SUMMARY_TYPE = "PHASE3_FACULTY_TRAJECTORY_REREVIEW_SESSION_SUMMARY"
SUBDIR, RECORDS_SUBDIR = "trajectory_rereview", "trajectory_rereviews"
#: The stored re-review set, pinned IN CODE (the first review's rule: a digest the file attests about itself pins nothing). Regenerating the set is a deliberate, reviewed act that changes this line.
PINNED_SET_DIGEST = "c30ab7f1fae514ff7e7c4de50e1d11b60f08efc6021804e162b70100d52b344f"
_PIN = object()
CANDIDATE = "JOINT_REGION_V1_CANDIDATE"
WITNESS = "CENTER_REFERENCE"
CANDIDATE_SET_LABEL = "CONJUNTO-1"
STATEMENT = ("Synthetic development case. A faculty judgment of a stored candidate trajectory: not a clinical validation, not a calibrated configuration, not a score, not a resident pilot.")
#: Four scenarios, all required, in the order the faculty asked for. There is no optional scenario in this package.
SEQUENCE = (("FR-B", True), ("FR-C", True), ("FR-E", True), ("FR-G", True))
SCENARIOS = tuple(identifier for identifier, _ in SEQUENCE)
#: The wording the reviewer reads once the four scenarios are submitted. It states what the package is and what it is not; it names no configuration, hints at no other set and promises no comparison.
COMPLETION_NOTE = ("Your four first impressions and overall judgments are saved and locked. Nothing is compared with them in this step. Whether any comparison follows is a separate faculty decision.")
#: Words a reviewer-facing field must never carry (defence in depth: the loader refuses an item that does). The identity of the configuration, the other sets and the comparator are not reviewer vocabulary.
_LEAK = re.compile(r"center_reference|witness|legacy|comparator|conjunto|joint[ _-]?region|candidate|v1_|\bscale\b|kernel|parameter", re.I)
_SHOWN_KEYS = ("scenario_id", "title", "context", "purpose", "arrival", "timeline", "common", "context_vitals")
#: The exact keys of an item and of its parts. An item with another key (a comparator, a parameter, a bundle) is not this package, even when re-signed and pinned: nothing the page does not draw may be stored with the item.
ITEM_KEYS = frozenset(_SHOWN_KEYS) | {"stopped", "required"}
ARRIVAL_KEYS = frozenset({"sbp", "dbp", "map", "hr", "rr", "spo2", "crt"})
ROW_KEYS = frozenset({"n", "minute", "advance", "action", "result", "executed", "intervention"})
POINT_KEYS = frozenset({"minute", "sbp", "dbp", "map"})
VITAL_KEYS = frozenset({"minute", "hr", "crt"})


# -- building the set from the certified static kit (a tool's job: the page never calls it) -----------------------------------------------------------------------------------
def build_set(candidate: Mapping, first_review: Mapping, blind_key: Mapping) -> dict:
    """The re-review set: the first set of the certified candidate review set, and nothing else, in the shape the review page draws. ``first_review`` is used ONLY to give each timeline row the two flags
    the page needs to draw its intervention markers (executed, an intervention): the other five fields of each row must already be identical to the candidate's, or this raises. No pressure is computed here."""
    first_items = {item["scenario_id"]: item for item in first_review["items"]}
    chosen = {item["scenario_id"]: item for item in candidate["items"] if item["set"] == CANDIDATE_SET_LABEL}
    if sorted(chosen) != sorted(SCENARIOS):
        raise ValueError("the candidate review set does not hold exactly FR-B, FR-C, FR-E and FR-G in its first set")
    items = []
    for scenario_id in SCENARIOS:
        source = chosen[scenario_id]
        rows = ftr.timeline_rows(first_items[scenario_id])
        shown = [{key: row[key] for key in ("n", "minute", "advance", "action", "result")} for row in rows]
        if shown != source["timeline"]:
            raise ValueError(f"{scenario_id}: the timeline of the candidate is not the one the review page draws")
        items.append({"scenario_id": scenario_id, "title": source["title"], "context": source["context"], "purpose": source["purpose"], "arrival": dict(source["arrival"]),
                      "timeline": rows, "common": [dict(point) for point in source["common"]],
                      "context_vitals": [{"minute": row["minute"], "hr": row.get("hr"), "crt": row.get("crt")} for row in source["heart_rate_and_capillary_refill"]],
                      "stopped": bool(source["stopped"]), "required": True})
    body = {"record_type": SET_TYPE, "version": VERSION, "set_id": SET_ID, "statement": STATEMENT,
            "what_it_is": ("The four review scenarios FR-B, FR-C, FR-E and FR-G as the faculty trajectory review draws them, with the trajectories of one candidate configuration taken, unchanged, from the "
                           "certified static kit. No comparator, no earlier trajectory and no other set are part of it."),
            "order": list(SCENARIOS), "items": items,
            "audit": {"candidate": CANDIDATE, "witness": WITNESS, "candidate_set_label": CANDIDATE_SET_LABEL, "candidate_review_set_digest": candidate["record_digest"],
                      "blind_key_digest": blind_key["record_digest"], "timeline_flags_from_first_review_set_digest": first_review["record_digest"],
                      "candidate_item_ids": {scenario_id: chosen[scenario_id]["item_id"] for scenario_id in SCENARIOS}}}
    return {**body, "record_digest": ftr._digest(body)}


# -- the stored re-review set --------------------------------------------------------------------------------------------------------------------------------------------------
def item_problems(item: Mapping) -> list:
    """Why a stored scenario cannot be reviewed. Empty means it can. Everything is checked here, nothing is trusted because it was stored; a malformed item is a problem, never an exception."""
    identifier = item.get("scenario_id") if isinstance(item, dict) else None
    try:
        return _item_problems(item)
    except Exception as error:                                                    # a malformed stored item must be refused, not crash the page
        return [f"{identifier or 'a scenario'}: the stored scenario cannot be checked ({type(error).__name__})"]


def _exact(value: Any, keys: frozenset) -> bool:
    return isinstance(value, dict) and set(value) == keys


def _item_problems(item: Any) -> list:
    if not isinstance(item, dict):
        return ["a stored scenario is not an object"]
    body, problems = dict(item), []
    identifier = body.get("scenario_id")
    if identifier not in SCENARIOS:
        return [f"{identifier or 'a scenario'} is not in the re-review set"]
    if set(body) != ITEM_KEYS:
        return [f"{identifier}: it does not have exactly the stored keys of a scenario (extra: {sorted(set(body) - ITEM_KEYS)}, missing: {sorted(ITEM_KEYS - set(body))})"]
    for key in _SHOWN_KEYS:
        if body[key] in (None, "", [], {}):
            problems.append(f"{identifier}: {key} is missing")
    if problems:
        return problems
    if not all(isinstance(body[key], str) for key in ("title", "context", "purpose")) or not isinstance(body["timeline"], list) or not isinstance(body["common"], list) or not isinstance(body["context_vitals"], list):
        return [f"{identifier}: a field has the wrong type"]
    if not _exact(body["arrival"], ARRIVAL_KEYS) or any(not _exact(row, ROW_KEYS) for row in body["timeline"]) or any(not _exact(point, POINT_KEYS) for point in body["common"]) \
            or any(not _exact(row, VITAL_KEYS) for row in body["context_vitals"]):
        return [f"{identifier}: the arrival, a timeline row, a pressure point or a vital-sign row does not have exactly the stored keys"]
    if body.get("stopped") or body.get("required") is not True:
        problems.append(f"{identifier}: the page draws no stop and every scenario of this package is required")
    arrival, points = dict(body["arrival"]), list(body["common"])
    minutes = [point.get("minute") for point in points]
    if minutes[0] != 0 or any(not isinstance(a, int) or not isinstance(b, int) or b <= a for a, b in zip(minutes, minutes[1:])):
        problems.append(f"{identifier}: the minutes of the trajectory do not start at 0 and increase")
    for point in points:
        try:
            values = [float(point[key]) for key in ("sbp", "dbp", "map")]
        except (KeyError, TypeError, ValueError):
            problems.append(f"{identifier}: a point of the trajectory is incomplete")
            break
        if any(not value.is_integer() for value in values) or round((values[0] + 2 * values[1]) / 3) != values[2]:
            problems.append(f"{identifier}: a point is not whole mmHg or its MAP is not (SBP + 2 x DBP) / 3")
            break
    if (points[0].get("sbp"), points[0].get("dbp"), points[0].get("map")) != (arrival.get("sbp"), arrival.get("dbp"), arrival.get("map")):
        problems.append(f"{identifier}: the first point is not the arrival pressure")
    rows = list(body["timeline"])
    if [row.get("n") for row in rows] != list(range(1, len(rows) + 1)) or any(not isinstance(row.get("executed"), bool) or not isinstance(row.get("intervention"), bool) for row in rows):
        problems.append(f"{identifier}: the timeline is not numbered or lacks its marker flags")
    found = _LEAK.search(json.dumps(body, sort_keys=True))
    if found:
        problems.append(f"{identifier}: a reviewer-facing field carries '{found.group(0)}'")
    return problems


def load_set(path: Path | None = None, *, expected_digest: Any = _PIN) -> dict:
    """The stored re-review set, verified. ``{"ok", "problems", "digest", "items", "audit"}``; ``items`` are what the reviewer may see and ``audit`` is kept apart. A set whose own digest does not recompute, that
    is not the pinned one, or that does not hold exactly the four scenarios offers nothing. Never raises."""
    result: dict = {"ok": False, "problems": [], "digest": None, "items": {}, "audit": {}}
    try:
        record = json.loads(Path(path or SET_PATH).read_text(encoding="utf-8"))
    except Exception as error:
        return {**result, "problems": [f"the re-review set cannot be read ({type(error).__name__})"]}
    if not isinstance(record, dict):
        return {**result, "problems": ["the re-review set is not the stored one (it is not a record)"]}
    claimed = record.get("record_digest")
    rest = {key: value for key, value in record.items() if key != "record_digest"}
    if record.get("record_type") != SET_TYPE or claimed != ftr._digest(rest):
        return {**result, "problems": ["the re-review set is not the stored one (its digest does not recompute)"]}
    pin = PINNED_SET_DIGEST if expected_digest is _PIN else expected_digest
    if pin is not None and claimed != pin:
        return {**result, "problems": ["the re-review set is not the pinned one (a re-signed or regenerated set is refused until its digest is pinned in code)"]}
    listed = record.get("items")
    if record.get("set_id") != SET_ID or not isinstance(listed, list) or any(not isinstance(item, dict) for item in listed) or [item.get("scenario_id") for item in listed] != list(SCENARIOS):
        return {**result, "problems": ["the re-review set does not hold exactly its four scenarios in order"]}
    problems = [problem for item in listed for problem in item_problems(item)]
    if problems:
        return {**result, "problems": problems}
    return {"ok": True, "problems": [], "digest": claimed, "items": {item["scenario_id"]: item for item in listed}, "audit": dict(record.get("audit") or {})}


# -- what the reviewer is shown ------------------------------------------------------------------------------------------------------------------------------------------------
#: What of the arrival the reviewer is shown. Heart rate and capillary refill are NOT (FD-REREVIEW-23): the values stored with each scenario were produced by the earlier encounter's trajectory and were not recomputed
#: for the pressure of this set, so they could carry that trajectory and contradict this one. They stay in the stored set, untouched (the set is pinned), and leave the process only through this function, which drops them.
ARRIVAL_SHOWN = ("sbp", "dbp", "map", "spo2", "rr")


def blind_view(item: Mapping) -> dict:
    """EVERYTHING the reviewer sees for a scenario, in the shape the trajectory review page draws. There is no other view: no comparator, no heart rate and no capillary refill exist in it."""
    return {"scenario_id": item["scenario_id"], "title": item["title"], "context": item["context"], "purpose": item["purpose"], "arrival": {key: item["arrival"][key] for key in ARRIVAL_SHOWN},
            "timeline": [dict(row) for row in item["timeline"]], "halted": False, "stop_minute": None, "common": [dict(point) for point in item["common"]],
            "questions": [dict(question, choices=list(question["choices"])) for question in ftr.required_questions(item)[0]]}


def sequence(items: Mapping) -> list:
    """The scenarios actually offered, in order: ``[{"scenario_id", "required"}]``."""
    return [{"scenario_id": identifier, "required": required} for identifier, required in SEQUENCE if identifier in items]


def values_table(item: Mapping) -> list:
    """The pressure points, for a table next to the chart: minute, SBP, DBP, MAP. Nothing else (FD-REREVIEW-23)."""
    return [{"minute": point["minute"], "sbp": int(point["sbp"]), "dbp": int(point["dbp"]), "map": int(point["map"])} for point in item["common"]]


# -- the durable review ----------------------------------------------------------------------------------------------------------------------------------------------------------
class ReReviewLog(ftr.ReviewLog):
    """The durable state of ONE reviewer on ONE scenario of the re-review set: the first review's append-only, hash-chained, locked event log in other files, with no comparator step."""
    SUBDIR_NAME, RECORDS_NAME = SUBDIR, RECORDS_SUBDIR

    def __init__(self, root: Path, reviewer: str, item: Mapping, *, set_digest: str, audit: Mapping | None = None, bundles: Any = None, account: Mapping | None = None):
        super().__init__(root, reviewer, item, set_digest=set_digest, bundles=bundles, account=account)
        self.audit = dict(audit or {})

    def _stem(self) -> str:
        return f"{self.item['scenario_id']}__{SET_ID}__{self.item_digest}"

    def _replay(self, lines: Sequence[str]) -> dict:
        state = super()._replay(lines)
        if state["status"] != "UNREADABLE" and state["submitted"] and not state["overall"]:          # only a forged (but well-chained) log closes a scenario with no overall judgment
            return {**state, "status": "UNREADABLE", "why": "the saved answers do not verify (closed without an overall judgment)"}
        return state

    def _may_submit(self, state: Mapping) -> str | None:
        return None if state["locked"] and state["overall"] else "make the overall judgment first"

    def answer(self, question_id: str, value: str) -> dict:
        if question_id not in ftr.required_questions(self.item)[1]:
            return {"ok": False, "why": "not one of the questions or choices", "state": self.state()}
        return super().answer(question_id, value)

    def comment(self, text: str, *, after_reveal: bool = False) -> dict:
        if after_reveal:
            return {"ok": False, "why": "there is no comparison in this review", "state": self.state()}
        return super().comment(text)

    def overall_comment(self, text: str) -> dict:
        problem = ftr.comment_problem(text, bundles=self.bundles)
        if problem:
            return {"ok": False, "why": problem, "state": self.state()}
        return self._append("overall_comment", {"text": str(text)}, lambda s: "the first impression is not locked yet" if not s["locked"] else "already submitted" if s["submitted"] else None)

    def _record(self, state: Mapping) -> dict:
        body = {"record_type": RECORD_TYPE, "version": VERSION, "reviewer_ref": self.reviewer, "reviewer_role": self.account.get("role"), "set_id": SET_ID,
                "scenario_id": self.item["scenario_id"],
                "linkage": {"set_digest": self.set_digest, "item_digest": self.item_digest, "candidate": self.audit.get("candidate"), "witness": self.audit.get("witness"),
                            "candidate_item_id": dict(self.audit.get("candidate_item_ids") or {}).get(self.item["scenario_id"]),
                            "candidate_review_set_digest": self.audit.get("candidate_review_set_digest"), "blind_key_digest": self.audit.get("blind_key_digest")},
                "first_pass": {"answers": dict(state["locked_answers"] or state["blind"]), "comment": state["locked_comment"] if state["locked_comment"] is not None else state["blind_comment"],
                               "locked_at": state["locked_at"], "answers_at_lock": dict(state["locked_answers"] or state["blind"])},
                "overall": {"judgment": state["overall"], "comment": state["overall_comment"]},
                "comparator_shown": False, "event_log_head": state["head"], "statement": STATEMENT}
        body["record_id"] = ftr._digest(body)[:16]
        return body


def record_problems(record: Mapping, state: Mapping, log: ReReviewLog) -> list:
    """Why a record cannot be counted: it must recompute its identity, belong to THIS reviewer, scenario, set and item, and AGREE field by field with the log that closed it."""
    problems = []
    body = {key: value for key, value in record.items() if key != "record_id"}
    link, first, overall = dict(record.get("linkage") or {}), dict(record.get("first_pass") or {}), dict(record.get("overall") or {})
    if record.get("record_type") != RECORD_TYPE or record.get("record_id") != ftr._digest(body)[:16]:
        problems.append("the record does not recompute its identity")
    if record.get("scenario_id") != log.item["scenario_id"] or record.get("reviewer_ref") != log.reviewer or record.get("set_id") != SET_ID:
        problems.append("the record belongs to another scenario, reviewer or set")
    if link.get("set_digest") != log.set_digest or link.get("item_digest") != log.item_digest:
        problems.append("the record is linked to another review set or item")
    if record.get("record_id") != state.get("record_id") or record.get("event_log_head") != state.get("submitted_prev"):
        problems.append("the record is not the one that closed the event log")
    if (dict(first.get("answers_at_lock") or {}) != dict(state.get("locked_answers") or {}) or dict(first.get("answers") or {}) != dict(state.get("locked_answers") or {})
            or first.get("comment") != state.get("locked_comment") or first.get("locked_at") != state.get("locked_at")):
        problems.append("the record's first pass differs from the log")
    if overall.get("judgment") != state.get("overall") or overall.get("comment") != state.get("overall_comment") or record.get("comparator_shown") is not False:
        problems.append("the record's overall judgment differs from the log")
    return problems


# -- progress and the final summary -------------------------------------------------------------------------------------------------------------------------------------------------
def progress(logs: Mapping[str, ReReviewLog], order: Sequence[Mapping]) -> dict:
    """Where the reviewer is (the first review's own function: it reads only each log's status)."""
    return ftr.progress(logs, order)


def summarize(root: Path, reviewer: str, items: Mapping, order: Sequence[Mapping], set_digest: str, audit: Mapping | None = None, *, bundles: Any = None) -> dict:
    """The technical session summary, derived ONLY from records on disk that VERIFY against the log that closed them. A record that does not verify is NOT counted and is reported. It tabulates what the
    reviewer answered and counts judgments; it never scores or interprets them."""
    submitted, technical, counts = [], [], {choice: 0 for choice in ftr.OVERALL}
    for entry in order:
        identifier, item = entry["scenario_id"], items[entry["scenario_id"]]
        log = ReReviewLog(root, reviewer, item, set_digest=set_digest, audit=audit, bundles=bundles)
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
        problems = record_problems(record, state, log)
        if problems:
            technical.extend(f"{identifier}: {problem}" for problem in problems)
            continue
        judgment = dict(record["overall"])["judgment"]
        counts[judgment] = counts.get(judgment, 0) + 1
        first = dict(record["first_pass"])
        submitted.append({"scenario_id": identifier, "title": item["title"], "record_id": record["record_id"], "overall": judgment, "overall_comment": dict(record["overall"]).get("comment") or "",
                          "first_pass": dict(first.get("answers") or {}), "first_pass_comment": first.get("comment") or "", "locked_at": first.get("locked_at"), "linkage": dict(record.get("linkage") or {})})
    reviewed = [row["scenario_id"] for row in submitted]
    body = {"record_type": SUMMARY_TYPE, "version": VERSION, "reviewer_ref": reviewer, "set_id": SET_ID, "review_set_digest": set_digest,
            "scenarios_offered": [entry["scenario_id"] for entry in order], "scenarios_reviewed": reviewed, "complete": reviewed == [entry["scenario_id"] for entry in order],
            "judgments": counts, "scenarios": submitted, "technical_problems": technical,
            "comments": [{"scenario_id": row["scenario_id"], "overall": row["overall"], "text": text, "stage": stage} for row in submitted
                         for stage, text in (("first pass", row["first_pass_comment"]), ("overall", row["overall_comment"])) if text],
            "statement": STATEMENT + " The counts are the reviewer's own judgments, tabulated; the software has not interpreted them."}
    return {**body, "summary_digest": ftr._digest(body)[:16]}


def write_summary(root: Path, summary: Mapping) -> dict:
    """The technical summary file, in the re-review's own directory (never next to the first review's)."""
    return ftr.write_summary(root, summary, subdir=SUBDIR)
