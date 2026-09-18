"""Owner-readable learner analyses stored separately from frozen encounter evidence.

These artifacts contain no faculty assessment. Every operation rechecks the
account session and the frozen trace/reflection fingerprint. Generating an
analysis after a completed encounter does not mutate that encounter's record.
"""
from __future__ import annotations

import json
import time
import uuid
from copy import deepcopy

from account_store import AccountError
from management_trace_analysis import (
    ManagementTraceAnalysisError, source_fingerprint,
    validate_management_trace_analysis,
)


def analysis_payload_from_session(session):
    """Choose the original frozen evidence and pre-comparison reflection only."""
    session = session if isinstance(session, dict) else {}
    return {
        "encounter_ended": session.get("encounter_ended") is True,
        "reflection_locked": session.get("expert_comparison_unlocked") is True,
        "trace": deepcopy(session.get("encounter_closed_trace") or []),
        "reflections": deepcopy(session.get("precomparison_decision_review") or {}),
        "reflection_prompts": deepcopy(session.get("review_prompts") or []),
        "encounter_events": deepcopy(session.get("encounter_closed_events") or []),
    }


class ManagementTraceStore:
    def __init__(self, accounts):
        self.accounts = accounts
        self._execute = accounts._execute
        with accounts._transaction(write=True) as connection:
            self._execute(connection, """CREATE TABLE IF NOT EXISTS mrs_learner_trace_analyses (
                id TEXT PRIMARY KEY,
                attempt_id TEXT NOT NULL REFERENCES mrs_attempts(id),
                source_hash TEXT NOT NULL,
                creator_user_id TEXT NOT NULL REFERENCES mrs_users(id),
                created_at BIGINT NOT NULL,
                report_json TEXT NOT NULL
            )""")
            self._execute(connection, """CREATE INDEX IF NOT EXISTS mrs_learner_trace_source
                ON mrs_learner_trace_analyses(attempt_id, source_hash, created_at, id)""")

    def _source(self, connection, actor, attempt_id):
        if not isinstance(attempt_id, str) or not attempt_id or len(attempt_id) > 200:
            raise AccountError("Choose an encounter with a completed, locked reflection.")
        row = self._execute(connection, """SELECT a.*, u.username FROM mrs_attempts a
            JOIN mrs_users u ON u.id = a.user_id WHERE a.id = ?""", (attempt_id,)).fetchone()
        if row is None or (actor["role"] == "resident" and row["user_id"] != actor["id"]):
            raise AccountError("This encounter analysis is not available to your account.")
        record = self.accounts._attempt(row)
        payload = analysis_payload_from_session((record.get("payload") or {}).get("session"))
        try:
            fingerprint = source_fingerprint(payload)
        except ManagementTraceAnalysisError:
            raise AccountError("Complete and lock your encounter reflection before requesting analysis.") from None
        return payload, fingerprint

    def get_latest(self, token, attempt_id):
        with self.accounts._transaction() as connection:
            if not self.accounts._sqlite:
                self._execute(connection, "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
            actor = self.accounts._actor(connection, token, {"resident", "faculty", "admin"})
            source, fingerprint = self._source(connection, actor, attempt_id)
            row = self._execute(connection, """SELECT report_json FROM mrs_learner_trace_analyses
                WHERE attempt_id = ? AND source_hash = ? ORDER BY created_at DESC, id DESC LIMIT 1""",
                (attempt_id, fingerprint)).fetchone()
            if row is None:
                return None
            try:
                return validate_management_trace_analysis(json.loads(row["report_json"]), source)
            except (ValueError, TypeError, ManagementTraceAnalysisError):
                raise AccountError("The saved analysis needs to be generated again.") from None

    def save(self, token, attempt_id, report):
        with self.accounts._transaction(write=True) as connection:
            actor = self.accounts._actor(connection, token, {"resident", "faculty", "admin"})
            source, fingerprint = self._source(connection, actor, attempt_id)
            try:
                clean = validate_management_trace_analysis(report, source)
                encoded = json.dumps(clean, ensure_ascii=False, allow_nan=False, sort_keys=True)
            except (ValueError, TypeError, ManagementTraceAnalysisError):
                raise AccountError("The analysis no longer matches this encounter. Generate it again.") from None
            if len(encoded.encode("utf-8")) > 500_000:
                raise AccountError("This analysis is too large to save.")
            identifier = f"{time.time_ns():020d}_{uuid.uuid4().hex}"
            self._execute(connection, """INSERT INTO mrs_learner_trace_analyses
                (id, attempt_id, source_hash, creator_user_id, created_at, report_json)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (identifier, attempt_id, fingerprint, actor["id"], int(time.time()), encoded))
            return clean
