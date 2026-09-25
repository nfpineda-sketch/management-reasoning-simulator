"""The AI proposal and the faculty's review, kept apart and kept in full.

Two append-only tables. A proposal is what a model suggested; a review is what a
faculty member decided. Neither overwrites the other and neither overwrites
itself: a change is a new revision, so the history of who changed what, and why,
survives.

A review carries the rubric version it was made under. Reading it never
recomputes it under a newer rubric, because an updated instrument must not
silently regrade an encounter that was assessed under the old one.

The totals are computed here by ``rubric.score`` from the saved values, and
recomputed on every read. A stored total that disagrees with the values beside
it is a fault, not a number to display.
"""
from __future__ import annotations

import json
import time
import uuid

from account_store import AccountError
from case_assessment import event_by_id, events as defined_events
from faculty_analysis import FacultyAnalysisError, source_fingerprint
from rubric import (DOMAIN_IDS, NOT_ASSESSABLE, RubricError, VERSION as RUBRIC_VERSION,
                    headline, score as compute_score, valid_score)
from rubric_analysis import (RubricAnalysisError, case_id_of, proposed_event_rows,
                             validate_rubric_proposal)


STAFF = frozenset({"faculty", "admin"})
REVIEW_STATUSES = ("draft", "confirmed")
EVENT_STATUSES = ("proposed", "confirmed", "dismissed")
MAX_REPORT_BYTES = 600_000
MAX_TEXT = 1200


def _text(value, *, required=False, field="justification"):
    value = str(value or "").strip()
    if len(value) > MAX_TEXT:
        raise AccountError(f"The {field} is too long.")
    if required and not value:
        raise AccountError(f"A {field} is required.")
    return value


def build_review(*, case_id, scores, reasons, events, justifications, status, proposal=None,
                 screening=None):
    """Validate a faculty decision and compute its totals. No database, no model.

    ``justifications`` explains each domain the faculty changed from the
    proposal. A change without one is refused: the record of why an assessment
    moved is the part that makes it reviewable later.

    ``screening`` is what ``rubric_screening`` read from the record. Confirming
    an event the record contradicts needs a written reason, exactly like
    confirming one the AI never proposed: the penalty of encounter 7 of the
    2026-09-24 batch was confirmed without anyone reading the two orders that
    made it impossible.
    """
    if status not in REVIEW_STATUSES:
        raise AccountError("A review is either a draft or confirmed.")
    proposed_scores = {}
    if proposal is not None:
        proposed_scores = {row["domain_id"]: row["score"] for row in proposal["proposal"]["domains"]}

    decided, why, changes = {}, {}, {}
    for domain in DOMAIN_IDS:
        if domain not in scores:
            if status == "confirmed":
                raise AccountError(f"{domain} has no decision; a confirmed review covers all five domains.")
            continue
        value = scores[domain]
        if not valid_score(value):
            raise AccountError(f"{domain} must be 0-3 or not assessable.")
        decided[domain] = value
        if value == NOT_ASSESSABLE:
            # A confirmed assessment must say why; a draft is work in progress
            # and is allowed to be incomplete. Since the reviewer's selector
            # starts every domain at "not assessable" (2026-09-23), requiring
            # the reason to save a draft would mean no draft could be saved at
            # all without writing five of them first.
            why[domain] = _text(reasons.get(domain), required=(status == "confirmed"),
                                field="reason for not assessable")
        elif reasons.get(domain):
            why[domain] = _text(reasons.get(domain), field="note")
        if domain in proposed_scores and proposed_scores[domain] != value:
            changes[domain] = {
                "proposed": proposed_scores[domain], "confirmed": value,
                "justification": _text(justifications.get(domain), required=True,
                                       field="justification for changing a proposed score"),
            }

    proposed_events = {row["event_id"] for row in proposed_event_rows(proposal)}
    against_record = {row["event_id"] for row in (screening or {}).get("events", [])
                      if row.get("status") in ("contradicted", "excluded")}
    known = {event["event_id"] for event in defined_events(case_id)} if case_id else set()
    decided_events, seen = [], set()
    for entry in events or []:
        event_id = str(entry.get("event_id") or "")
        if event_id in seen:
            raise AccountError("The same critical event was decided twice.")
        seen.add(event_id)
        if known and event_id not in known:
            raise AccountError("That critical event is not one defined for this case.")
        state = entry.get("status")
        if state not in EVENT_STATUSES:
            raise AccountError("A critical event is proposed, confirmed or dismissed.")
        definition = event_by_id(case_id, event_id) if case_id else None
        if state == "confirmed" and event_id in against_record:
            justification = _text(entry.get("justification"), required=True,
                                  field="reason for confirming an event the record contradicts")
        else:
            justification = _text(entry.get("justification"),
                                  required=state != "proposed" and event_id not in proposed_events,
                                  field="justification for a critical event the AI did not propose")
        decided_events.append({
            "event_id": event_id, "status": state,
            "kind": (definition or {}).get("kind", ""),
            "action": (definition or {}).get("action", ""),
            "proposed_by_ai": event_id in proposed_events,
            "record_contradicts": event_id in against_record,
            "justification": justification,
        })
    if status == "confirmed":
        unresolved = sorted(proposed_events - {e["event_id"] for e in decided_events
                                               if e["status"] != "proposed"})
        if unresolved:
            raise AccountError("Confirm or dismiss every proposed critical event before confirming: "
                               + ", ".join(unresolved))
    try:
        totals = compute_score(decided, decided_events)
    except RubricError as error:
        raise AccountError(str(error)) from None
    return {
        "rubric_version": RUBRIC_VERSION, "case_id": case_id, "status": status,
        "scores": decided, "reasons": why, "changes": changes,
        "critical_events": decided_events, "totals": totals,
        "headline": headline(totals),
    }


def totals_of(review):
    """Recompute the totals of a saved review from its own saved values.

    A review made under an earlier rubric keeps its own numbers: the arithmetic
    is only recomputed when the stored version is the one in force.
    """
    if review.get("rubric_version") != RUBRIC_VERSION:
        return {**review.get("totals", {}), "recomputed": False,
                "rubric_version": review.get("rubric_version")}
    return {**compute_score(review.get("scores", {}), review.get("critical_events", [])),
            "recomputed": True}


class RubricStore:
    """Append-only storage for proposals and reviews, behind the account store."""

    def __init__(self, account_store):
        self.accounts = account_store
        self._execute = account_store._execute
        self._initialize()

    def _initialize(self):
        statements = [
            """CREATE TABLE IF NOT EXISTS mrs_rubric_proposals (
                id TEXT PRIMARY KEY,
                attempt_id TEXT NOT NULL REFERENCES mrs_attempts(id),
                -- Its own order, because two writes in the same second cannot be
                -- separated by a timestamp and a random identifier is not a history.
                sequence INTEGER NOT NULL CHECK (sequence >= 1),
                source_hash TEXT NOT NULL,
                attempt_revision INTEGER NOT NULL CHECK (attempt_revision >= 0),
                rubric_version TEXT NOT NULL,
                coverage_version TEXT NOT NULL,
                prompt_version TEXT NOT NULL,
                model TEXT NOT NULL,
                case_id TEXT NOT NULL,
                generated_at TEXT NOT NULL,
                created_at BIGINT NOT NULL,
                generator_user_id TEXT NOT NULL REFERENCES mrs_users(id),
                report_json TEXT NOT NULL
            )""",
            """CREATE INDEX IF NOT EXISTS mrs_rubric_proposals_source
                ON mrs_rubric_proposals(attempt_id, source_hash, attempt_revision, sequence)""",
            """CREATE TABLE IF NOT EXISTS mrs_rubric_reviews (
                id TEXT PRIMARY KEY,
                attempt_id TEXT NOT NULL REFERENCES mrs_attempts(id),
                sequence INTEGER NOT NULL CHECK (sequence >= 1),
                source_hash TEXT NOT NULL,
                attempt_revision INTEGER NOT NULL CHECK (attempt_revision >= 0),
                rubric_version TEXT NOT NULL,
                case_id TEXT NOT NULL,
                proposal_id TEXT,
                status TEXT NOT NULL CHECK (status IN ('draft', 'confirmed')),
                reviewer_user_id TEXT NOT NULL REFERENCES mrs_users(id),
                created_at BIGINT NOT NULL,
                base_score INTEGER,
                adjusted_score INTEGER,
                penalty INTEGER NOT NULL,
                domains_assessed INTEGER NOT NULL,
                review_json TEXT NOT NULL
            )""",
            """CREATE INDEX IF NOT EXISTS mrs_rubric_reviews_source
                ON mrs_rubric_reviews(attempt_id, source_hash, attempt_revision, sequence)""",
        ]
        with self.accounts._transaction(write=True) as connection:
            for statement in statements:
                self._execute(connection, statement)

    def _next(self, connection, table, attempt_id):
        """The next revision number for this encounter, inside the write lock."""
        row = self._execute(
            connection,
            f"SELECT COALESCE(MAX(sequence), 0) AS highest FROM {table} WHERE attempt_id = ?",
            (attempt_id,)).fetchone()
        # A sqlite row is not a dict and has no .get.
        return (int(row["highest"]) if row is not None and row["highest"] is not None else 0) + 1

    def _record(self, connection, actor, attempt_id):
        if not isinstance(attempt_id, str) or not attempt_id or len(attempt_id) > 200:
            raise AccountError("Choose a completed resident encounter to assess.")
        row = self._execute(connection, """SELECT a.*, u.username, u.role AS owner_role
            FROM mrs_attempts a JOIN mrs_users u ON u.id = a.user_id WHERE a.id = ?""",
            (attempt_id,)).fetchone()
        if (row is None or row["owner_role"] != "resident" or row["is_sandbox"]
                or row["status"] != "completed" or row["user_id"] == actor["id"]):
            raise AccountError("A rubric assessment requires a completed, non-sandbox resident encounter.")
        record = self.accounts._attempt(row)
        session = (record.get("payload") or {}).get("session")
        if not isinstance(session, dict) or session.get("review_completed") is not True:
            raise AccountError("A rubric assessment requires the resident's completed encounter reflection.")
        return record

    # --- the AI proposal ----------------------------------------------------
    def save_proposal(self, token, attempt_id, report):
        with self.accounts._transaction(write=True) as connection:
            actor = self.accounts._actor(connection, token, STAFF)
            record = self._record(connection, actor, attempt_id)
            try:
                report = validate_rubric_proposal(
                    {k: v for k, v in dict(report).items() if k != "proposal_id"}, record)
            except (RubricAnalysisError, FacultyAnalysisError) as exc:
                raise AccountError(str(exc)) from None
            body = json.dumps(report, ensure_ascii=False, sort_keys=True)
            if len(body.encode("utf-8")) > MAX_REPORT_BYTES:
                raise AccountError("The rubric proposal is too large to store.")
            identifier = uuid.uuid4().hex
            sequence = self._next(connection, "mrs_rubric_proposals", attempt_id)
            self._execute(connection, """INSERT INTO mrs_rubric_proposals
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (identifier, attempt_id, sequence, report["source_hash"], report["attempt_revision"],
                 report["rubric_version"], report["coverage_version"], report["prompt_version"],
                 report["model"], report["case_id"], report["generated_at"], int(time.time()),
                 actor["id"], body))
            return {**report, "proposal_id": identifier, "sequence": sequence}

    def latest_proposal(self, token, attempt_id):
        with self.accounts._transaction() as connection:
            actor = self.accounts._actor(connection, token, STAFF)
            record = self._record(connection, actor, attempt_id)
            row = self._execute(connection, """SELECT * FROM mrs_rubric_proposals
                WHERE attempt_id = ? AND source_hash = ? AND attempt_revision = ?
                ORDER BY sequence DESC LIMIT 1""",
                (attempt_id, source_fingerprint(record), record["revision"])).fetchone()
            if row is None:
                return None
            try:
                report = json.loads(row["report_json"])
            except (TypeError, ValueError):
                raise AccountError("The saved rubric proposal could not be read.") from None
            return {**report, "proposal_id": row["id"], "sequence": row["sequence"]}

    def proposal(self, token, attempt_id, proposal_id):
        """One saved proposal of this encounter, by its identifier.

        A faculty decision names the proposal it started from; its final
        document compares the decision with that proposal, never with one
        generated afterwards (faculty decision 15 of 2026-09-25).
        """
        with self.accounts._transaction() as connection:
            actor = self.accounts._actor(connection, token, STAFF)
            self._record(connection, actor, attempt_id)
            row = self._execute(connection, """SELECT * FROM mrs_rubric_proposals
                WHERE id = ? AND attempt_id = ?""", (proposal_id, attempt_id)).fetchone()
            if row is None:
                return None
            try:
                report = json.loads(row["report_json"])
            except (TypeError, ValueError):
                raise AccountError("The saved rubric proposal could not be read.") from None
            return {**report, "proposal_id": row["id"], "sequence": row["sequence"]}

    # --- the faculty's own decision ----------------------------------------
    def save_review(self, token, attempt_id, *, scores, reasons=None, events=(),
                    justifications=None, status="draft", proposal_id=None):
        with self.accounts._transaction(write=True) as connection:
            actor = self.accounts._actor(connection, token, STAFF)
            record = self._record(connection, actor, attempt_id)
            fingerprint = source_fingerprint(record)
            proposal = None
            if proposal_id:
                row = self._execute(connection, """SELECT * FROM mrs_rubric_proposals
                    WHERE id = ? AND attempt_id = ? AND source_hash = ? AND attempt_revision = ?""",
                    (proposal_id, attempt_id, fingerprint, record["revision"])).fetchone()
                if row is None:
                    raise AccountError("That rubric proposal does not belong to this encounter revision.")
                proposal = json.loads(row["report_json"])
            import rubric_screening
            case_id = case_id_of(record)
            review = build_review(
                case_id=case_id, scores=dict(scores or {}),
                reasons=dict(reasons or {}), events=list(events or ()),
                justifications=dict(justifications or {}), status=status, proposal=proposal,
                screening=rubric_screening.screening(record, case_id) if case_id else None)
            body = json.dumps(review, ensure_ascii=False, sort_keys=True)
            if len(body.encode("utf-8")) > MAX_REPORT_BYTES:
                raise AccountError("The rubric review is too large to store.")
            identifier = uuid.uuid4().hex
            totals = review["totals"]
            sequence = self._next(connection, "mrs_rubric_reviews", attempt_id)
            self._execute(connection, """INSERT INTO mrs_rubric_reviews
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (identifier, attempt_id, sequence, fingerprint, record["revision"], review["rubric_version"],
                 review["case_id"], proposal_id, status, actor["id"], int(time.time()),
                 totals["base"], totals["adjusted"], totals["penalty"],
                 totals["coverage"]["assessed"], body))
            return {**review, "review_id": identifier, "reviewer": actor["username"],
                    "proposal_id": proposal_id, "sequence": sequence}

    def latest_review(self, token, attempt_id):
        """The current review, with its totals recomputed from its own values."""
        for row in self.history(token, attempt_id):
            return row
        return None

    def released(self, token, attempt_id):
        """One encounter's **confirmed** assessment, for the person it is about.

        The reviewing methods refuse the owner on purpose: a resident must not
        read a draft, and must never be the reviewer of their own encounter.
        This is the other side of that rule -- once a faculty member completes
        the assessment it belongs to the resident too, which is the decision
        recorded on 2026-09-23. A draft answers ``None``, not a score.

        Returns ``(review, proposal)`` or ``(None, None)``.
        """
        with self.accounts._transaction() as connection:
            actor = self.accounts._actor(connection, token)
            row = self._execute(connection, """SELECT a.*, u.username, u.role AS owner_role
                FROM mrs_attempts a JOIN mrs_users u ON u.id = a.user_id WHERE a.id = ?""",
                (attempt_id,)).fetchone()
            if row is None:
                raise AccountError("The encounter was not found.")
            if actor["role"] not in STAFF and row["user_id"] != actor["id"]:
                raise AccountError("Your account does not have permission for this action.")
            record = self.accounts._attempt(row)
            fingerprint = source_fingerprint(record)
            review_row = self._execute(connection, """SELECT r.*, u.username AS reviewer
                FROM mrs_rubric_reviews r JOIN mrs_users u ON u.id = r.reviewer_user_id
                WHERE r.attempt_id = ? AND r.source_hash = ? AND r.attempt_revision = ?
                  AND r.status = 'confirmed'
                ORDER BY r.sequence DESC LIMIT 1""",
                (attempt_id, fingerprint, record["revision"])).fetchone()
            if review_row is None:
                return None, None
            try:
                review = json.loads(review_row["review_json"])
            except (TypeError, ValueError):
                raise AccountError("A saved rubric review could not be read.") from None
            review = {**review, "review_id": review_row["id"],
                      "reviewer": review_row["reviewer"], "created_at": review_row["created_at"],
                      "sequence": review_row["sequence"], "totals": totals_of(review)}
            proposal = None
            proposal_row = self._execute(connection, """SELECT id, sequence, report_json FROM mrs_rubric_proposals
                WHERE id = ?""", (review_row["proposal_id"],)).fetchone() if review_row["proposal_id"] else None
            if proposal_row is not None:
                try:
                    proposal = {**json.loads(proposal_row["report_json"]),
                                "proposal_id": proposal_row["id"], "sequence": proposal_row["sequence"]}
                except (TypeError, ValueError):
                    proposal = None
            return review, proposal

    def progress(self, token, user_id=None):
        """Every confirmed review of one resident, oldest first.

        Staff may read any resident's; a resident may read only their own, and
        only what a faculty member confirmed. A draft is somebody's work in
        progress and is never part of a profile.
        """
        with self.accounts._transaction() as connection:
            actor = self.accounts._actor(connection, token)
            if actor["role"] in STAFF:
                target = user_id or actor["id"]
            elif user_id in (None, actor["id"]):
                target = actor["id"]
            else:
                raise AccountError("Your account does not have permission for this action.")
            rows = self._execute(connection, """SELECT r.*, a.challenge_id, a.updated_at
                FROM mrs_rubric_reviews r JOIN mrs_attempts a ON a.id = r.attempt_id
                WHERE a.user_id = ? AND r.status = 'confirmed'
                ORDER BY r.created_at ASC, r.sequence ASC""", (target,)).fetchall()
            # One encounter contributes once: the latest confirmed revision of
            # it, not every revision a reviewer saved on the way there.
            latest = {}
            for row in rows or []:
                try:
                    review = json.loads(row["review_json"])
                except (TypeError, ValueError):
                    raise AccountError("A saved rubric review could not be read.") from None
                latest[row["attempt_id"]] = {
                    **review, "review_id": row["id"], "attempt_id": row["attempt_id"],
                    "challenge_id": row["challenge_id"], "created_at": row["created_at"],
                    "sequence": row["sequence"], "totals": totals_of(review)}
            return sorted(latest.values(),
                          key=lambda item: (item["created_at"], item["sequence"]))

    def history(self, token, attempt_id):
        """Every review revision, newest first. Nothing is ever overwritten."""
        with self.accounts._transaction() as connection:
            actor = self.accounts._actor(connection, token, STAFF)
            record = self._record(connection, actor, attempt_id)
            rows = self._execute(connection, """SELECT r.*, u.username AS reviewer
                FROM mrs_rubric_reviews r JOIN mrs_users u ON u.id = r.reviewer_user_id
                WHERE r.attempt_id = ? AND r.source_hash = ? AND r.attempt_revision = ?
                ORDER BY r.sequence DESC""",
                (attempt_id, source_fingerprint(record), record["revision"])).fetchall()
            history = []
            for row in rows or []:
                try:
                    review = json.loads(row["review_json"])
                except (TypeError, ValueError):
                    raise AccountError("A saved rubric review could not be read.") from None
                history.append({**review, "review_id": row["id"], "reviewer": row["reviewer"],
                                "created_at": row["created_at"], "proposal_id": row["proposal_id"],
                                "sequence": row["sequence"], "totals": totals_of(review)})
            return history
