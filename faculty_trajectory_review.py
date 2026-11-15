"""UX-002 to UX-010: the FACULTY TRAJECTORY REVIEW -- data model and the reviewer's durable state (pure: no Streamlit, no engine, no authority, no common core).

WHAT IT IS. A review of STORED, CERTIFIED trajectories. The faculty reviewer does not replay an encounter: the page shows the trajectory the pressure authority produced for one scripted review
scenario (captured ONCE from the real page into ``docs/revision/PHASE3_FACULTY_TRAJECTORY_REVIEW_SET.json`` and pinned by digest), takes the first-pass answers BLIND, locks them, and only then
shows the legacy comparator. Nothing here runs a physiology, an authority, a grant or an encounter: it reads the stored bundle, validates it with the bundle layer the page hands in, and records the reviewer's
answers.

THE REVIEWER SEES clinical content only: context, timeline of interventions, trajectory, five questions. THE RECORD KEEPS the audit metadata (bundle id, artifact id and digest, grant, snapshot, review set
digest, event-log head); the reviewer never types or sees any of it.

DURABILITY. One append-only, hash-chained event log per (reviewer, scenario, bundle), written under an exclusive ``flock`` and fsynced, so a refresh restores the answers, a locked first pass can never be
unlocked or edited (the writer refuses and the reader ignores any later blind answer), and a second submit cannot create a second record. The submitted record is create-only and atomic. A bundle that changes
(another bundle id) is another log: answers are never carried onto a different package.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

VERSION = "UX-002"
ROOT = Path(__file__).resolve().parent
SET_PATH = ROOT / "docs" / "revision" / "PHASE3_FACULTY_TRAJECTORY_REVIEW_SET.json"
SERIES_PATH = ROOT / "docs" / "revision" / "PHASE3_PRESSURE_AUTHORITY_SERIES.json"
SET_TYPE = "PHASE3_FACULTY_TRAJECTORY_REVIEW_SET"
RECORD_TYPE = "PHASE3_FACULTY_TRAJECTORY_REVIEW_RECORD"
SUMMARY_TYPE = "PHASE3_FACULTY_TRAJECTORY_REVIEW_SESSION_SUMMARY"
SUBDIR, RECORDS_SUBDIR = "trajectory", "trajectory_reviews"
#: The stored review set, pinned IN CODE (F7 of the adversarial review: a digest the file attests about itself pins nothing). Regenerating the set is a deliberate, reviewed act that changes this line.
PINNED_SET_DIGEST = "f65d1127f3fb97926334d695aeab37b92f3a44236cec2ae025025eec90ba1649"
_PIN = object()
STATEMENT = "Synthetic development case. A faculty judgment of a stored certified trajectory: not a clinical validation, not a score, not a resident pilot."

#: The order a reviewer sees: the five required scenarios first (the kit's core set), then the two optional ones. ``required=False`` scenarios may be skipped.
SEQUENCE = (("FR-B", True), ("FR-A", True), ("FR-E", True), ("FR-G", True), ("FR-F", True), ("FR-D", False), ("FR-C", False))
MINUTES_PER_SCENARIO = 4          # an ESTIMATE written by the author, never measured with a person

FIRST_PASS = (
    {"id": "Q1", "topic": "DIRECTION", "text": "Does the physiologic evolution move in the expected direction?", "choices": ("Expected", "Partly", "Wrong")},
    {"id": "Q2", "topic": "TIMING", "text": "Does the response occur:", "choices": ("Too early", "Plausible", "Too late")},
    {"id": "Q3", "topic": "MAGNITUDE", "text": "Is the magnitude:", "choices": ("Too small", "Plausible", "Too large")},
    {"id": "Q4", "topic": "MANAGEMENT RESPONSE", "text": "Is the response to intervention:", "choices": ("Coherent", "Uncertain", "Incoherent")},
    {"id": "Q5", "topic": "EDUCATIONAL RISK", "text": "Could this trajectory mislead a resident?", "choices": ("No", "Maybe", "Yes")},
)
#: Asked only where the experiment stopped: the halt-experience review the first protocol made of FR-A, FR-D and FR-F must not be lost.
HALT_QUESTION = {"id": "Q5H", "topic": "STOPPING POINT", "text": "Did the experiment stop at an understandable point?", "choices": ("Understandable", "Uncertain", "Not understandable")}
CHANGED = {"id": "R1", "text": "Did seeing the legacy comparator change your judgment?",
           "choices": ("No", "Yes — increases confidence in common-core trajectory", "Yes — increases concern about common-core trajectory")}
OVERALL = ("ACCEPT", "ACCEPT_WITH_LIMITATION", "RECALIBRATE", "REJECT")
MAX_COMMENT = 2000
#: The certified purpose line of FR-E also asks about a common-consciousness comparison that this page does not show: the page states only the part it asks.
PURPOSE_OVERRIDES = {"FR-E": "Is the recovery after delayed treatment coherent in direction, timing and magnitude?"}
COMPARATOR_LABEL = "Legacy comparator — nonauthoritative comparison"
COMPARATOR_NOTE = "A difference from the legacy engine is not an error and closeness to it is not success: it is context for your judgment, not a reference standard."
#: Identifier-like text a comment may not carry: the bundle layer's own tripwire is used when the page hands the layer in.
_FALLBACK_SENSITIVE = (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), re.compile(r"\b(?:mrn|dni|nhs|ssn|dob)\b\s*[:#]?\s*\d"), re.compile(r"\b\d{6,}\b"))


class Locked(Exception):
    """The comparator was asked for before the first pass was locked."""


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def reviewer_ref(user_id: Any) -> str:
    """An opaque, stable reference to the reviewer's account: neither the user name nor the account id is written to a review record."""
    return hashlib.sha256(("ftr|" + str(user_id)).encode("utf-8")).hexdigest()[:12]


# -- the stored review set --------------------------------------------------------------------------------------------------------------------------------------------
def _reference(scenario: Mapping, series_runs: Sequence) -> tuple | None:
    row = next((item for item in series_runs if item.get("case") == scenario["case_id"] and item.get("scenario") == scenario["series"]), None)
    if row is None:
        return None
    seen: dict = {}
    legacy: dict = {}
    for minute, on, off in row["pressure_steps_on_off"]:
        seen.setdefault(int(minute), tuple(int(value) for value in on))
        legacy.setdefault(int(minute), tuple(int(value) for value in off))
    return [int(item) for item in row["committed_minutes"]], seen, legacy


def item_digest(item: Mapping) -> str:
    """The digest of everything the reviewer is shown for a scenario: a revised item is another item (and so another log) even when its bundle is the same."""
    return _digest(item)[:12]


def item_problems(item: Mapping, *, bundles: Any, scenario_of: Callable, series_runs: Sequence) -> list:
    """Why a stored scenario cannot be reviewed. Empty means it can. Everything is recomputed here (the bundle id, the evidence, the match to the certified series and to the certified scripted scenario,
    the arrival, the legacy values, the differences): nothing is trusted because it was stored."""
    body, problems = dict(item or {}), []
    identifier = body.get("scenario_id")
    scenario = scenario_of(identifier) if identifier else None
    if scenario is None:
        return [f"{identifier or 'a scenario'} is not in the review set"]
    bundle = dict(body.get("bundle") or {})
    failed = list(bundles.bundle_problems(bundle)) + list(bundles.evidence_problems(bundle))
    if failed:
        problems.append("the stored bundle does not hold: " + "; ".join(failed[:3]))
    encounter = dict(bundle.get("encounter") or {})
    if (encounter.get("scenario_id"), encounter.get("case_id")) != (identifier, scenario["case_id"]) or body.get("case_id") != scenario["case_id"]:
        problems.append("the stored bundle is for another scenario or case")
    if (body.get("title"), body.get("reason"), body.get("series")) != (scenario["title"], scenario["reason"], scenario["series"]) or [list(step) for step in scenario["steps"]] != [list(step) for step in body.get("script") or ()]:
        problems.append("the stored scenario text or script is not the certified scripted scenario")
    reference = _reference(scenario, series_runs)
    view = dict(bundle.get("authority_view") or {})
    timeline = list(view.get("authoritative_pressure_timeline") or [])
    legacy = list(dict(bundle.get("comparator") or {}).get("legacy_counterfactual_pressure_timeline") or [])
    if reference is None:
        problems.append("the certified series has no run for this scenario")
    else:
        minutes, pressures, legacy_pressures = reference
        if [int(row["minute"]) for row in timeline] != minutes or any(pressures.get(int(row["minute"])) != (round(float(row["sbp"])), round(float(row["dbp"]))) for row in timeline):
            problems.append("the stored trajectory does not match the certified series")
        if any(legacy_pressures.get(int(row.get("minute", -1))) != (round(float(row.get("sbp", -1))), round(float(row.get("dbp", -1)))) for row in legacy):
            problems.append("the stored comparator does not match the certified counterfactual of the series")
        arrival = dict(body.get("arrival") or {})
        if pressures.get(0) != (arrival.get("sbp"), arrival.get("dbp")) or arrival.get("map") != int(round((float(arrival.get("sbp") or 0) + 2 * float(arrival.get("dbp") or 0)) / 3)):
            problems.append("the stored arrival is not the certified arrival pressure")
    if [row.get("minute") for row in legacy] != [row.get("minute") for row in timeline]:
        problems.append("the stored comparator is not on the minutes of the trajectory")
    else:
        differences = list(dict(bundle.get("comparator") or {}).get("differences_from_legacy") or [])
        expected = [{"minute": common["minute"], **{f"{key}_difference": round(float(common[key]) - float(other[key]), 2) for key in ("sbp", "dbp", "map")}} for common, other in zip(timeline, legacy)]
        if [{key: value for key, value in row.items()} for row in differences] != expected:
            problems.append("the stored differences are not common minus legacy")
    return problems


def load_set(path: Path | None = None, *, bundles: Any, scenario_of: Callable, series_path: Path | None = None, expected_digest: Any = _PIN) -> dict:
    """The stored review set, verified. ``{"ok", "problems", "digest", "items"}``: a scenario that does not verify is simply NOT offered (it is listed in ``problems``), and a set whose own digest does not
    recompute offers nothing. Never raises."""
    result: dict = {"ok": False, "problems": [], "digest": None, "items": {}}
    try:
        record = json.loads(Path(path or SET_PATH).read_text(encoding="utf-8"))
        series_runs = list(json.loads(Path(series_path or SERIES_PATH).read_text(encoding="utf-8"))["runs"])
    except Exception as error:
        return {**result, "problems": [f"the review set cannot be read ({type(error).__name__})"]}
    claimed = record.get("record_digest")
    rest = {key: value for key, value in record.items() if key != "record_digest"}
    if record.get("record_type") != SET_TYPE or claimed != _digest(rest):
        return {**result, "problems": ["the review set is not the stored one (its digest does not recompute)"]}
    pin = PINNED_SET_DIGEST if expected_digest is _PIN else expected_digest
    if pin is not None and claimed != pin:
        return {**result, "problems": ["the review set is not the pinned one (a re-signed or regenerated set is refused until its digest is pinned in code)"]}
    items = {}
    for item in record.get("items") or ():
        problems = item_problems(item, bundles=bundles, scenario_of=scenario_of, series_runs=series_runs)
        if problems:
            result["problems"].append(f"{dict(item).get('scenario_id')}: " + "; ".join(problems))
        else:
            items[item["scenario_id"]] = item
    result.update(items=items, digest=claimed, ok=bool(items))
    return result


# -- what the reviewer is shown ---------------------------------------------------------------------------------------------------------------------------------------
_REASONING_TAIL = re.compile(r"\n\s*\n\s*Guided reasoning completion:.*", re.S)
_NOT_REPEATED = re.compile(r"not repeated", re.I)


def _clean(text: Any) -> str:
    return _REASONING_TAIL.sub("", str(text or "")).strip()


def timeline_rows(item: Mapping) -> list:
    """The reviewer's timeline: minute, what was asked or ordered (the order text only, never the reasoning form), and what the encounter did with it. No identifiers."""
    rows, number = [], 0
    for entry in dict(dict(item["bundle"]).get("authority_view") or {}).get("management_timeline") or ():
        entry = dict(entry)
        executed = entry.get("status") in ("executed", "information", "examined")
        actions = [str(action) for action in entry.get("actions") or () if action]
        number += 1
        text = _clean(entry.get("input"))
        rows.append({"n": number, "minute": entry.get("decision_time_min"), "advance": entry.get("elapsed_minutes"),
                     "action": text or ("Asked the patient" if entry.get("activity") == "question" else "Examined the patient" if entry.get("activity") == "examination" else "—"),
                     "result": ("; ".join(actions) if actions else ("Answered" if entry.get("activity") == "question" or entry.get("status") == "information" else
                                                                       f"{entry.get('elapsed_minutes')} min passed" if executed and entry.get("elapsed_minutes") else "—" if executed else "Not executed: the experiment had stopped")),
                     "executed": executed, "intervention": bool(actions) and not all(_NOT_REPEATED.search(action) for action in actions)})
    return rows


def _pressure_points(rows: Sequence, arrival: Mapping) -> list:
    points = [{"minute": 0, "sbp": float(arrival["sbp"]), "dbp": float(arrival["dbp"]), "map": float(arrival["map"])}]
    points += [{"minute": int(row["minute"]), "sbp": float(row["sbp"]), "dbp": float(row["dbp"]), "map": float(row["map"])} for row in rows]
    return points


def blind_view(item: Mapping) -> dict:
    """EVERYTHING the reviewer may see before the first pass is locked. It carries no comparator, no legacy number and no audit identifier: the comparator is built by ``comparator_view`` and only on a locked state."""
    bundle = dict(item["bundle"])
    view = dict(bundle["authority_view"])
    halts = [dict(event) for event in view.get("halt_events") or ()]
    arrival = dict(item["arrival"])
    return {"scenario_id": item["scenario_id"], "title": item["title"], "context": item["clinical_context"], "purpose": PURPOSE_OVERRIDES.get(item["scenario_id"], item["reason"]),
            "arrival": arrival, "timeline": timeline_rows(item), "halted": bool(view.get("halted")), "stop_minute": (halts[0].get("minute") if halts else None),
            "common": _pressure_points(view.get("authoritative_pressure_timeline") or (), arrival),
            "context_vitals": [dict(row) for row in item.get("context_vitals") or ()],
            "questions": [dict(question, choices=list(question["choices"])) for question in required_questions(item)[0]]}


def comparator_view(item: Mapping, state: Mapping | None) -> dict:
    """The legacy comparator and the differences, ONLY for a state whose first pass is locked. Anything else raises ``Locked``: there is no other way to obtain these numbers from this module."""
    if not dict(state or {}).get("locked"):
        raise Locked("the first impression is not locked")
    comparator = dict(dict(item["bundle"]).get("comparator") or {})
    arrival = dict(item["arrival"])
    legacy = [{"minute": int(row["minute"]), "sbp": float(row["sbp"]), "dbp": float(row["dbp"]), "map": float(row["map"])} for row in comparator.get("legacy_counterfactual_pressure_timeline") or ()]
    legacy.insert(0, {"minute": 0, "sbp": float(arrival["sbp"]), "dbp": float(arrival["dbp"]), "map": float(arrival["map"])})
    differences = [{"minute": int(row["minute"]), "sbp": row.get("sbp_difference"), "dbp": row.get("dbp_difference"), "map": row.get("map_difference")} for row in comparator.get("differences_from_legacy") or ()]
    return {"label": COMPARATOR_LABEL, "note": COMPARATOR_NOTE, "legacy": legacy, "differences": differences,
            "post_questions": [dict(CHANGED, choices=list(CHANGED["choices"]))], "overall_choices": list(OVERALL)}


def required_questions(item: Mapping) -> tuple:
    """(the questions that must be answered before the lock, their ids). The stopping-point question exists only where the experiment stopped."""
    halted = bool(dict(dict(item["bundle"]).get("authority_view") or {}).get("halted"))
    questions = list(FIRST_PASS) + ([HALT_QUESTION] if halted else [])
    return questions, [question["id"] for question in questions]


def choices_of(question_id: str) -> tuple | None:
    for question in tuple(FIRST_PASS) + (HALT_QUESTION, CHANGED):
        if question["id"] == question_id:
            return tuple(question["choices"])
    return None


def sequence(items: Mapping) -> list:
    """The scenarios actually offered, in order: ``[{"scenario_id", "required"}]``."""
    return [{"scenario_id": identifier, "required": required} for identifier, required in SEQUENCE if identifier in items]


# -- the durable event log ---------------------------------------------------------------------------------------------------------------------------------------------
_GUARD = threading.RLock()


def comment_problem(text: str, *, bundles: Any = None) -> str | None:
    """Why a free-text comment is refused, or None. Uses the bundle layer's own identifier tripwire when it is handed in (a tripwire, not a proof)."""
    text = str(text or "")
    if len(text) > MAX_COMMENT:
        return "the comment is too long"
    if bundles is not None and hasattr(bundles, "_normalised") and hasattr(bundles, "_SENSITIVE"):
        seen = bundles._normalised(text)
        patterns = tuple(bundles._SENSITIVE)
    else:
        seen, patterns = text.lower(), _FALLBACK_SENSITIVE
    if any(pattern.search(seen) for pattern in patterns):
        return "the comment looks like it carries a personal or real-patient identifier: these are synthetic development cases"
    return None


def _fold(lines: Sequence[str], item: Mapping) -> dict:
    """The state an event log describes, or ``status == "UNREADABLE"`` when its chain does not verify or an event is malformed. Pure; never raises. A blind answer after the lock is IGNORED here (and refused at
    write time): the lock is final. A lock counts only when EVERY required question has an answer in the log, and what it locks is what the log holds, never what the event claims."""
    _, required = required_questions(item)
    state: dict = {"status": "NEW", "blind": {}, "blind_comment": "", "locked": False, "locked_at": None, "locked_answers": None, "locked_comment": None, "post": {}, "after_reveal_comment": "",
                   "overall": None, "submitted": False, "submitted_at": None, "submitted_prev": None, "record_id": None, "head": "0" * 64, "events": 0}
    previous = "0" * 64
    for index, line in enumerate(lines):
        try:
            event = json.loads(line)
            if not isinstance(event, dict):
                raise ValueError("event")
            claimed = event.pop("hash")
            if event.get("seq") != index + 1 or event.get("prev") != previous or claimed != _digest({**event}):
                raise ValueError("chain")
            previous, kind, data = claimed, event["kind"], event.get("data")
            if not isinstance(kind, str) or not isinstance(data, dict):
                raise ValueError("event shape")
            done = state["submitted"]
            if kind == "blind" and not state["locked"] and not done and data.get("id") in required and data.get("value") in (choices_of(data["id"]) or ()):
                state["blind"][data["id"]] = data["value"]
            elif kind == "blind_comment" and not state["locked"] and not done:
                state["blind_comment"] = str(data.get("text") or "")
            elif kind == "lock" and not state["locked"] and not done and all(question in state["blind"] for question in required):
                state.update(locked=True, locked_at=event.get("at"), locked_answers=dict(state["blind"]), locked_comment=state["blind_comment"])
            elif state["locked"] and not done and kind == "post" and data.get("id") == "R1" and data.get("value") in CHANGED["choices"]:
                state["post"]["R1"] = data["value"]
            elif state["locked"] and not done and kind == "overall" and data.get("value") in OVERALL:
                state["overall"] = data["value"]
            elif state["locked"] and not done and kind == "after_reveal_comment":
                state["after_reveal_comment"] = str(data.get("text") or "")
            elif kind == "submitted" and state["locked"] and not done:
                state.update(submitted=True, submitted_at=event.get("at"), submitted_prev=event.get("prev"), record_id=data.get("record_id"))
        except (KeyError, TypeError, ValueError, AttributeError):
            return {**state, "status": "UNREADABLE", "why": f"the saved answers do not verify (event {index + 1})"}
    state["head"], state["events"] = previous, len(lines)
    state["status"] = "SUBMITTED" if state["submitted"] else "LOCKED" if state["locked"] else "IN_PROGRESS" if (state["blind"] or state["blind_comment"]) else "NEW"
    return state


def _fsync_directory(directory: Path) -> None:
    fd = os.open(str(directory), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


SAVE_FAILED = "it could not be saved (a disk error): nothing was changed"


class ReviewLog:
    """The durable state of ONE reviewer on ONE scenario of ONE stored item. Every method is safe to call again and again (a refresh, a double click): it re-reads the log under an exclusive lock, and no
    method ever raises or reveals a path."""

    def __init__(self, root: Path, reviewer: str, item: Mapping, *, set_digest: str, bundles: Any = None, account: Mapping | None = None):
        self.item, self.reviewer, self.set_digest, self.bundles = dict(item), str(reviewer), str(set_digest), bundles
        self.account = dict(account or {})
        self.item_digest = item_digest(item)
        bundle_id = dict(item["bundle"])["bundle_id"]
        stem = f"{item['scenario_id']}__{bundle_id}__{self.item_digest}"
        self.directory = Path(root) / SUBDIR / self.reviewer
        self.path = self.directory / f"{stem}.jsonl"
        self.records = Path(root) / RECORDS_SUBDIR
        self.record_path = self.records / f"{self.reviewer}__{stem}.json"

    # ---- reading
    def _read(self) -> list:
        try:
            raw = self.path.read_bytes()
        except FileNotFoundError:
            return []
        complete = raw[: raw.rfind(b"\n") + 1]          # a torn tail was never acknowledged: it is not part of the log
        return [line for line in complete.decode("utf-8", "replace").split("\n") if line]

    def state(self) -> dict:
        try:
            return _fold(self._read(), self.item)
        except OSError:
            return {**_fold([], self.item), "status": "UNREADABLE", "why": "the saved answers cannot be read"}

    # ---- writing
    def _append(self, kind: str, data: Any, decide: Callable[[dict], str | None], before: Callable[[dict, dict], str | None] | None = None) -> dict:
        """Append one event if ``decide(state)`` allows it, atomically with respect to every other writer: the state is read, decided on, ``before`` (e.g. the record file) runs and the event is written
        ALL under one exclusive lock, so nothing can change in between. Returns ``{"ok", "why", "state"}``; an I/O error is a refusal, never an exception."""
        fd = None
        state: dict = {}
        try:
            with _GUARD:
                created = not self.path.exists()
                self.directory.mkdir(parents=True, exist_ok=True)
                os.chmod(self.directory, 0o700)
                fd = os.open(str(self.path), os.O_RDWR | os.O_CREAT | os.O_APPEND, 0o600)
                fcntl.flock(fd, fcntl.LOCK_EX)
                raw = self.path.read_bytes()
                keep = raw[: raw.rfind(b"\n") + 1]
                if len(keep) != len(raw):                 # drop an unacknowledged torn tail before appending
                    os.ftruncate(fd, len(keep))
                lines = [line for line in keep.decode("utf-8", "replace").split("\n") if line]
                state = _fold(lines, self.item)
                if state["status"] == "UNREADABLE":
                    return {"ok": False, "why": state["why"], "state": state}
                refusal = decide(state)
                if refusal:
                    return {"ok": False, "why": refusal, "state": state}
                payload = dict(data(state) if callable(data) else data)
                if before is not None:
                    problem = before(state, payload)
                    if problem:
                        return {"ok": False, "why": problem, "state": state}
                event = {"seq": len(lines) + 1, "prev": state["head"], "kind": kind, "at": _now(), "data": payload}
                line = (json.dumps({**event, "hash": _digest(event)}, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
                if os.write(fd, line) != len(line):
                    raise OSError("short write")
                os.fsync(fd)
                if created:
                    _fsync_directory(self.directory)
                return {"ok": True, "why": "", "state": _fold(lines + [line.decode("utf-8").strip()], self.item)}
        except OSError:
            return {"ok": False, "why": SAVE_FAILED, "state": state or self.state()}
        finally:
            if fd is not None:
                try:
                    fcntl.flock(fd, fcntl.LOCK_UN)
                finally:
                    os.close(fd)

    def answer(self, question_id: str, value: str) -> dict:
        """One blind answer (before the lock) or the post-reveal question (after it)."""
        if question_id == "R1":
            return self._append("post", {"id": "R1", "value": value}, lambda s: ("the first impression is not locked yet" if not s["locked"] else "already submitted" if s["submitted"] else
                                                                               None if value in CHANGED["choices"] else "not one of the choices"))
        _, required = required_questions(self.item)

        def decide(state: dict) -> str | None:
            if state["locked"]:
                return "the first impression is locked: it cannot be changed"
            if question_id not in required or value not in (choices_of(question_id) or ()):
                return "not one of the questions or choices"
            return None
        return self._append("blind", {"id": question_id, "value": value}, decide)

    def comment(self, text: str, *, after_reveal: bool = False) -> dict:
        problem = comment_problem(text, bundles=self.bundles)
        if problem:
            return {"ok": False, "why": problem, "state": self.state()}
        if after_reveal:
            return self._append("after_reveal_comment", {"text": str(text)}, lambda s: "the first impression is not locked yet" if not s["locked"] else "already submitted" if s["submitted"] else None)
        return self._append("blind_comment", {"text": str(text)}, lambda s: "the first impression is locked: it cannot be changed" if s["locked"] else None)

    def lock(self) -> dict:
        """Lock the first impression. The answers locked are the ones in the LOG (never the caller's), and only when every required question has one."""
        _, required = required_questions(self.item)

        def decide(state: dict) -> str | None:
            if state["locked"]:
                return "already locked"
            missing = [question for question in required if question not in state["blind"]]
            return f"answer {', '.join(missing)} first" if missing else None
        return self._append("lock", lambda state: {"answers": dict(state["blind"]), "comment": state["blind_comment"]}, decide)

    def set_overall(self, value: str) -> dict:
        return self._append("overall", {"value": value}, lambda s: "the first impression is not locked yet" if not s["locked"] else "already submitted" if s["submitted"] else None if value in OVERALL else "not one of the choices")

    def submit(self) -> dict:
        """Submit: ONE critical section builds the record from the log as it stands, writes it and closes the log, so the record and the log cannot disagree and no other writer can slip in between. A second call
        (a double click, a retry after a crash) never creates a second record; an interrupted earlier record is kept aside (``superseded``) and replaced, never left to block the reviewer."""
        written: dict = {}

        def decide(state: dict) -> str | None:
            if state["submitted"]:
                return "already submitted"
            if not state["locked"] or not state["overall"] or not state["post"].get("R1"):
                return "answer the question about the comparator and the overall judgment first"
            return None

        def data(state: dict) -> dict:
            return {"record_id": self._record(state)["record_id"], "reviewer_role": self.account.get("role")}

        def before(state: dict, payload: dict) -> str | None:
            result = self._write_record(self._record(state), replace_orphan=True)
            written.update(result)
            return None if result["stored"] else result["why"]
        outcome = self._append("submitted", data, decide, before)
        if outcome["ok"] or outcome["why"] == "already submitted":
            return {**outcome, "record_id": outcome["state"]["record_id"], "path": written.get("path", str(self.record_path))}
        return outcome

    # ---- the record
    def _record(self, state: Mapping) -> dict:
        bundle = dict(self.item["bundle"])
        evidence = dict(bundle.get("evidence") or {})
        configuration = dict(bundle.get("faculty_review_configuration") or {})
        body = {"record_type": RECORD_TYPE, "version": VERSION, "reviewer_ref": self.reviewer, "reviewer_role": self.account.get("role"),
                "scenario_id": self.item["scenario_id"], "case_id": self.item["case_id"], "series": self.item.get("series"),
                "linkage": {"bundle_id": bundle["bundle_id"], "artifact_id": evidence.get("artifact_id"), "artifact_digest": evidence.get("artifact_digest"),
                            "grant_id": configuration.get("grant_id"), "snapshot_id": dict(bundle.get("authority_view") or {}).get("snapshot_id"),
                            "review_set_digest": self.set_digest, "item_digest": self.item_digest, "legacy_comparator": "bundle.comparator.legacy_counterfactual_pressure_timeline"},
                "first_pass": {"answers": dict(state["locked_answers"] or state["blind"]), "comment": state["locked_comment"] if state["locked_comment"] is not None else state["blind_comment"],
                               "locked_at": state["locked_at"], "answers_at_lock": dict(state["locked_answers"] or state["blind"])},
                "comparator_revealed_at": state["locked_at"],
                "post_reveal": {"changed_judgment": state["post"].get("R1"), "after_reveal_comment": state["after_reveal_comment"], "overall": state["overall"]},
                "event_log_head": state["head"], "statement": STATEMENT}
        body["record_id"] = _digest(body)[:16]
        return body

    def _write_record(self, record: Mapping, *, replace_orphan: bool = False) -> dict:
        """Create the record once, atomically. An existing different record is replaced ONLY by a caller that holds the log lock and has just verified the log is not submitted (an interrupted earlier
        attempt): the old one is moved aside as ``superseded`` and kept."""
        try:
            self.records.mkdir(parents=True, exist_ok=True)
            os.chmod(self.records, 0o700)
            path = self.record_path
            payload = json.dumps(record, indent=1, sort_keys=True)
            temporary = path.with_name(f".tmp-{os.getpid()}-{threading.get_ident()}-{path.name}")
            fd = os.open(str(temporary), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    handle.write(payload)
                    handle.flush()
                    os.fsync(handle.fileno())
                try:
                    os.link(str(temporary), str(path))
                except FileExistsError:
                    try:
                        existing = json.loads(path.read_text(encoding="utf-8"))
                    except Exception:
                        existing = None
                    if existing == json.loads(payload):
                        return {"stored": True, "path": str(path), "why": ""}
                    if not replace_orphan:
                        return {"stored": False, "path": str(path), "why": "a different record already has this identity"}
                    old_id = (existing or {}).get("record_id") or _digest(path.read_text(encoding="utf-8", errors="replace"))[:16]
                    os.replace(str(path), str(path.with_name(f"{path.stem}.superseded-{old_id}.json")))
                    os.link(str(temporary), str(path))
                _fsync_directory(self.records)
                return {"stored": True, "path": str(path), "why": ""}
            finally:
                try:
                    os.unlink(str(temporary))
                except OSError:
                    pass
        except OSError:
            return {"stored": False, "path": "", "why": SAVE_FAILED}


# -- progress and the final summary --------------------------------------------------------------------------------------------------------------------------------------
def progress(logs: Mapping[str, ReviewLog], order: Sequence[Mapping]) -> dict:
    """Where the reviewer is: per scenario status, the current (first unsubmitted required, else first unsubmitted optional) scenario, the scenarios that may be entered, counts and the estimated time left."""
    statuses = {entry["scenario_id"]: logs[entry["scenario_id"]].state()["status"] for entry in order}
    required = [entry["scenario_id"] for entry in order if entry["required"]]
    pending_required = [identifier for identifier in required if statuses[identifier] != "SUBMITTED"]
    pending_optional = [entry["scenario_id"] for entry in order if not entry["required"] and statuses[entry["scenario_id"]] != "SUBMITTED"]
    submitted = [identifier for identifier, status in statuses.items() if status == "SUBMITTED"]
    enterable = set(submitted) | ({(pending_required or pending_optional or [None])[0]} - {None}) | (set(pending_optional) if not pending_required else set())
    return {"statuses": statuses, "required": required, "submitted": submitted, "enterable": enterable,
            "current": (pending_required or pending_optional or [None])[0], "required_done": not pending_required, "all_done": not pending_required and not pending_optional,
            "remaining_required": len(pending_required), "estimated_minutes_left": MINUTES_PER_SCENARIO * len(pending_required)}


def read_record(path: Path) -> dict | None:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return None


def record_problems(record: Mapping, state: Mapping, log: ReviewLog) -> list:
    """Why a record cannot be counted: it must recompute its identity, belong to THIS reviewer, scenario, package, item and review set, and AGREE field by field with the log that closed it."""
    problems = []
    body = {key: value for key, value in record.items() if key != "record_id"}
    link = dict(record.get("linkage") or {})
    first, post = dict(record.get("first_pass") or {}), dict(record.get("post_reveal") or {})
    if record.get("record_type") != RECORD_TYPE or record.get("record_id") != _digest(body)[:16]:
        problems.append("the record does not recompute its identity")
    if record.get("scenario_id") != log.item["scenario_id"] or record.get("reviewer_ref") != log.reviewer:
        problems.append("the record belongs to another scenario or reviewer")
    if link.get("bundle_id") != dict(log.item["bundle"])["bundle_id"] or link.get("review_set_digest") != log.set_digest or link.get("item_digest") != log.item_digest:
        problems.append("the record is linked to another package or review set")
    if record.get("record_id") != state.get("record_id") or record.get("event_log_head") != state.get("submitted_prev"):
        problems.append("the record is not the one that closed the event log")
    if (dict(first.get("answers_at_lock") or {}) != dict(state.get("locked_answers") or {}) or dict(first.get("answers") or {}) != dict(state.get("locked_answers") or {})
            or first.get("comment") != state.get("locked_comment") or first.get("locked_at") != state.get("locked_at")):
        problems.append("the record's first pass differs from the log")
    if (post.get("overall") != state.get("overall") or post.get("changed_judgment") != dict(state.get("post") or {}).get("R1")
            or post.get("after_reveal_comment") != state.get("after_reveal_comment")):
        problems.append("the record's post-reveal answers differ from the log")
    return problems


def summarize(root: Path, reviewer: str, items: Mapping, order: Sequence[Mapping], set_digest: str, *, bundles: Any = None) -> dict:
    """The technical session summary, derived ONLY from records on disk that VERIFY against the log that closed them. A record that does not verify (altered, foreign, missing) is NOT counted and is reported; a
    scenario is counted only when its record agrees with its log. It tabulates what the reviewer answered and counts judgments; it never scores or interprets them."""
    submitted, technical, counts = [], [], {choice: 0 for choice in OVERALL}
    for entry in order:
        identifier, item = entry["scenario_id"], items[entry["scenario_id"]]
        log = ReviewLog(root, reviewer, item, set_digest=set_digest, bundles=bundles)
        state = log.state()
        record = read_record(log.record_path) if log.record_path.exists() else None
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
        if bundles is not None and not problems:
            stored = bundles.load(dict(item["bundle"])["bundle_id"], environ={"MRS_PHASE3_AUTHORITY_STORE": str(Path(root).parent)})
            if stored is not None and stored != json.loads(json.dumps(item["bundle"], default=str)):
                problems.append("the bundle in the reviewer's store differs from the review set")
        if problems:
            technical.extend(f"{identifier}: {problem}" for problem in problems)
            continue
        overall = dict(record["post_reveal"]).get("overall")
        counts[overall] = counts.get(overall, 0) + 1
        first, post = dict(record["first_pass"]), dict(record["post_reveal"])
        submitted.append({"scenario_id": identifier, "required": entry["required"], "title": item["title"], "record_id": record["record_id"], "overall": overall,
                          "first_pass": dict(first.get("answers") or {}), "first_pass_comment": first.get("comment") or "", "changed_judgment": post.get("changed_judgment"),
                          "after_reveal_comment": post.get("after_reveal_comment") or "", "locked_at": first.get("locked_at"), "linkage": dict(record.get("linkage") or {})})
    required_ids = [entry["scenario_id"] for entry in order if entry["required"]]
    reviewed = [row["scenario_id"] for row in submitted]
    body = {"record_type": SUMMARY_TYPE, "version": VERSION, "reviewer_ref": reviewer, "review_set_digest": set_digest,
            "scenarios_offered": [entry["scenario_id"] for entry in order], "required_scenarios": required_ids,
            "scenarios_reviewed": reviewed, "required_reviewed": sum(1 for row in submitted if row["required"]), "optional_reviewed": sum(1 for row in submitted if not row["required"]),
            "complete": all(identifier in reviewed for identifier in required_ids),
            "judgments": counts, "scenarios": submitted, "technical_problems": technical,
            "comments": [{"scenario_id": row["scenario_id"], "overall": row["overall"], "text": text, "stage": stage} for row in submitted
                         for stage, text in (("first pass", row["first_pass_comment"]), ("after reveal", row["after_reveal_comment"])) if text],
            "statement": STATEMENT + " The counts are the reviewer's own judgments, tabulated; the software has not interpreted them."}
    return {**body, "summary_digest": _digest(body)[:16]}


def write_summary(root: Path, summary: Mapping) -> dict:
    """The technical summary file, written without any action from the reviewer (private: 0600 in a 0700 directory). It is DERIVED, so a rewrite replaces it atomically (never a partial file)."""
    try:
        directory = Path(root) / SUBDIR
        directory.mkdir(parents=True, exist_ok=True)
        os.chmod(directory, 0o700)
        path = directory / f"session_summary_{summary['reviewer_ref']}.json"
        temporary = path.with_name(f".tmp-{os.getpid()}-{threading.get_ident()}-{path.name}")
        fd = os.open(str(temporary), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(summary, indent=1, sort_keys=True))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(str(temporary), str(path))
        return {"written": True, "path": str(path)}
    except OSError as error:
        return {"written": False, "path": "", "why": type(error).__name__}
