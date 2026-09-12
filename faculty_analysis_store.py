"""Private, immutable AI drafts that do not confer assessment credit.

The account database is the authorization boundary on every read and write.
Drafts are bound to the finalized encounter revision and to its source hash;
they are never embedded in learner-visible attempt payloads.
"""
from __future__ import annotations

import json
import time
import uuid

from account_store import AccountError
from faculty_analysis import FacultyAnalysisError, source_fingerprint, validate_brief


STAFF = frozenset({"faculty", "admin"})
ASSISTANCE_CONTEXTS = frozenset({"unknown", "guided", "prompted", "independent"})
MAX_REPORT_BYTES = 500_000


def _context(value, *, optional=False):
    if value is None and optional:
        return None
    if not isinstance(value, str) or value not in ASSISTANCE_CONTEXTS:
        raise AccountError("Choose the assistance context for this faculty analysis.")
    return value


def _validated(report, record, assistance_context):
    """Keep storage metadata outside the strict model-generated envelope."""
    if not isinstance(report, dict):
        raise AccountError("The faculty analysis is not a valid report.")
    report = {key: value for key, value in report.items() if key != "brief_id"}
    try:
        return validate_brief(report, record, assistance_context)
    except FacultyAnalysisError as exc:
        raise AccountError(str(exc)) from None


class FacultyBriefStore:
    """Save separate faculty drafts; only explicit ProgressStore writes count.

    Construction performs the idempotent schema setup under AccountStore's
    existing write transaction lock, including its PostgreSQL advisory lock.
    No model call is made or expected inside a storage transaction.
    """

    def __init__(self, account_store):
        self.accounts = account_store
        self._execute = account_store._execute
        self._initialize()

    def _initialize(self):
        statements = [
            """CREATE TABLE IF NOT EXISTS mrs_faculty_briefs (
                id TEXT PRIMARY KEY,
                attempt_id TEXT NOT NULL REFERENCES mrs_attempts(id),
                source_hash TEXT NOT NULL,
                attempt_revision INTEGER NOT NULL CHECK (attempt_revision >= 0),
                prompt_version TEXT NOT NULL,
                model TEXT NOT NULL,
                assistance_context TEXT NOT NULL CHECK (
                    assistance_context IN ('unknown', 'guided', 'prompted', 'independent')),
                generated_at TEXT NOT NULL,
                created_at BIGINT NOT NULL,
                generator_user_id TEXT NOT NULL REFERENCES mrs_users(id),
                report_json TEXT NOT NULL
            )""",
            """CREATE INDEX IF NOT EXISTS mrs_faculty_briefs_source
                ON mrs_faculty_briefs(attempt_id, source_hash, attempt_revision, created_at, id)""",
        ]
        with self.accounts._transaction(write=True) as connection:
            for statement in statements:
                self._execute(connection, statement)

    def _record(self, connection, actor, attempt_id):
        if not isinstance(attempt_id, str) or not attempt_id or len(attempt_id) > 200:
            raise AccountError("Choose a completed resident encounter for faculty analysis.")
        row = self._execute(connection, """SELECT a.*, u.username, u.role AS owner_role
            FROM mrs_attempts a JOIN mrs_users u ON u.id = a.user_id WHERE a.id = ?""",
            (attempt_id,)).fetchone()
        if (row is None or row["owner_role"] != "resident" or row["is_sandbox"]
                or row["status"] != "completed" or row["user_id"] == actor["id"]):
            raise AccountError("Faculty analysis requires a completed, non-sandbox resident encounter.")
        record = self.accounts._attempt(row)
        payload = record.get("payload")
        session = payload.get("session") if isinstance(payload, dict) else None
        if not isinstance(session, dict) or session.get("review_completed") is not True:
            raise AccountError("Faculty analysis requires the resident's completed encounter reflection.")
        return record

    def get_latest(self, token, attempt_id, assistance_context=None):
        """Return the latest matching private envelope, or None if absent.

        An omitted context selects the latest draft across contexts. A supplied
        context selects only that exact assistance context. Stale source
        revisions are retained for audit but never returned as current drafts.
        """
        with self.accounts._transaction() as connection:
            if not self.accounts._sqlite:
                self._execute(connection, "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
            actor = self.accounts._actor(connection, token, STAFF)
            record = self._record(connection, actor, attempt_id)
            assistance_context = _context(assistance_context, optional=True)
            fingerprint = source_fingerprint(record)
            query = """SELECT * FROM mrs_faculty_briefs
                WHERE attempt_id = ? AND source_hash = ? AND attempt_revision = ?"""
            parameters = (attempt_id, fingerprint, record["revision"])
            if assistance_context is not None:
                query += " AND assistance_context = ?"
                parameters += (assistance_context,)
            row = self._execute(connection, query + " ORDER BY created_at DESC, id DESC LIMIT 1",
                                parameters).fetchone()
            if row is None:
                return None
            try:
                report = json.loads(row["report_json"])
            except (TypeError, ValueError):
                raise AccountError("The saved faculty analysis could not be read. Generate a new analysis.") from None
            report = _validated(report, record, row["assistance_context"])
            return {**report, "brief_id": row["id"]}

    def save(self, token, attempt_id, report):
        """Append a valid draft after rechecking auth and the frozen source.

        This check happens after generation, so revoked sessions and a source
        changed while the AI request was in flight cannot save a stale result.
        Existing drafts are never updated or deleted by this store.
        """
        with self.accounts._transaction(write=True) as connection:
            actor = self.accounts._actor(connection, token, STAFF)
            record = self._record(connection, actor, attempt_id)
            if not isinstance(report, dict):
                raise AccountError("The faculty analysis is not a valid report.")
            assistance_context = _context(report.get("assistance_context"))
            fingerprint = source_fingerprint(record)
            if (report.get("attempt_id") != attempt_id
                    or type(report.get("attempt_revision")) is not int
                    or report["attempt_revision"] != record["revision"]
                    or report.get("source_hash") != fingerprint):
                raise AccountError("This encounter changed after analysis. Generate a new faculty analysis.")
            report = _validated(report, record, assistance_context)
            try:
                encoded = json.dumps(report, ensure_ascii=False, allow_nan=False, sort_keys=True)
            except (TypeError, ValueError, OverflowError):
                raise AccountError("The faculty analysis contains unsupported values.") from None
            if len(encoded.encode("utf-8")) > MAX_REPORT_BYTES:
                raise AccountError("The faculty analysis is too large to save.")
            brief_id = f"{time.time_ns():020d}_{uuid.uuid4().hex}"
            self._execute(connection, """INSERT INTO mrs_faculty_briefs
                (id, attempt_id, source_hash, attempt_revision, prompt_version, model,
                 assistance_context, generated_at, created_at, generator_user_id, report_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (brief_id, attempt_id, fingerprint, record["revision"], report["prompt_version"],
                 report["model"], assistance_context, report["generated_at"], int(time.time()),
                 actor["id"], encoded))
            return {**report, "brief_id": brief_id}
