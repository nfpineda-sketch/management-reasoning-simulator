"""Who helped, and who says so: the assistance context of an encounter.

Faculty specification of 2026-09-24. Three things that used to share one
selector are kept apart:

* **the assistance context** -- the help the participant received during the
  encounter, declared by someone, at some moment, and possibly corrected later;
* **the observable performance** -- what the record shows, which is the record;
* **the assessed autonomy** -- the faculty's judgment of the level shown for
  each objective, recorded with that objective's assessment.

Until this date the faculty brief's "assistance" selector offered the three
autonomy levels themselves, so "unknown" -- its default, and the truth of most
encounters -- forced every autonomy to be empty, and an empty autonomy could
not be recorded. A batch declared "independent" to get past that, which is
true of a script and says nothing about a resident.

"Not reported" is a valid state here, never replaced by "independent" to get
past a technical block. "No external help" is not competence and is not the
highest autonomy. A synthetic run is recorded separately, as what it is: the
execution of a test, which demonstrates nothing about a resident's autonomy.

The declarations live in their own append-only table, outside the encounter's
payload. Completing or correcting one later therefore changes no fingerprint:
no saved brief, proposal or confirmed assessment is invalidated or overwritten,
and every earlier declaration stays in the history with who made it and when.
"""
from __future__ import annotations

import json
import time
import uuid

from account_store import AccountError


STAFF = frozenset({"faculty", "admin"})
FIELDS = ("assistance", "execution")
ASSISTANCE = ("none", "external_help", "not_reported")
EXECUTION = ("synthetic_agent",)
MAX_TEXT = 1000

LABELS = {
    ("assistance", "none"): ("No external help", "Sin ayuda externa"),
    ("assistance", "external_help"): ("External help received", "Con ayuda externa"),
    ("assistance", "not_reported"): ("Not reported", "No informado"),
    ("execution", "synthetic_agent"): (
        "Synthetic test: automated run without external assistance",
        "Prueba sintética: ejecución automatizada sin asistencia externa"),
}
AUTONOMY_NOT_DETERMINED = ("Autonomy not determined: requires faculty confirmation",
                           "Autonomía no determinada: requiere confirmación docente")
NO_CLINICAL_HELP_FEATURE = (
    "No clinical help is recorded: this version gives no hints, cue interpretations or "
    "recommended actions during an encounter. The prompts it does give -- to complete a "
    "missing reasoning category, or to clarify an order's format -- are neutral and are "
    "recorded with each decision.",
    "No hay ayudas clínicas registradas: esta versión no entrega pistas, interpretaciones de "
    "hallazgos ni acciones recomendadas durante el encuentro. Las preguntas que sí hace -- para "
    "completar una categoría de razonamiento o aclarar el formato de una orden -- son neutrales "
    "y quedan registradas con cada decisión.")


def label(field, value, language="en"):
    pair = LABELS.get((field, value))
    if pair is None:
        return str(value or "")
    return pair[1] if language == "es" else pair[0]


def _text(value, name):
    value = str(value or "").strip()
    if len(value) > MAX_TEXT:
        raise AccountError(f"The {name} is too long.")
    return value


class EncounterContextStore:
    """Append-only declarations about one encounter, behind the account store."""

    def __init__(self, account_store):
        self.accounts = account_store
        self._execute = account_store._execute
        with self.accounts._transaction(write=True) as connection:
            self._execute(connection, """CREATE TABLE IF NOT EXISTS mrs_encounter_context (
                id TEXT PRIMARY KEY,
                attempt_id TEXT NOT NULL REFERENCES mrs_attempts(id),
                field TEXT NOT NULL CHECK (field IN ('assistance', 'execution')),
                sequence INTEGER NOT NULL CHECK (sequence >= 1),
                value TEXT NOT NULL,
                description TEXT NOT NULL,
                affected_json TEXT NOT NULL,
                note TEXT NOT NULL,
                actor_id TEXT NOT NULL REFERENCES mrs_users(id),
                actor_role TEXT NOT NULL,
                created_at BIGINT NOT NULL
            )""")
            self._execute(connection, """CREATE INDEX IF NOT EXISTS mrs_encounter_context_attempt
                ON mrs_encounter_context(attempt_id, field, sequence)""")

    def _attempt(self, connection, actor, attempt_id, *, write):
        if not isinstance(attempt_id, str) or not attempt_id or len(attempt_id) > 200:
            raise AccountError("Choose an encounter.")
        row = self._execute(connection, """SELECT a.*, u.username, u.role AS owner_role
            FROM mrs_attempts a JOIN mrs_users u ON u.id = a.user_id WHERE a.id = ?""",
            (attempt_id,)).fetchone()
        if row is None:
            raise AccountError("The encounter was not found.")
        owner = row["user_id"] == actor["id"]
        if actor["role"] in STAFF:
            # Staff complete or correct a resident's declaration; nobody
            # declares the context of their own sandbox as a resident's.
            if owner or row["owner_role"] != "resident":
                if write:
                    raise AccountError("The assistance context belongs to a resident's encounter.")
        elif not owner:
            raise AccountError("Your account does not have permission for this action.")
        return row

    def declare(self, token, attempt_id, *, value, field="assistance", description="",
                affected_refs=(), note="", synthetic_accounts=()):
        """Record one declaration. Nothing earlier is changed; the latest one is current.

        A resident declares the assistance context of their own encounter. A
        faculty member or an administrator may complete or correct it, and the
        history keeps both. The execution of a synthetic test is declared only
        by an account configured as a test account, or by an administrator
        correcting a record's provenance -- with a note saying so.
        """
        if field not in FIELDS:
            raise AccountError("Unknown encounter context.")
        allowed = ASSISTANCE if field == "assistance" else EXECUTION
        if value not in allowed:
            raise AccountError("Choose a valid assistance context.")
        description = _text(description, "description of the help")
        note = _text(note, "note")
        refs = [str(ref) for ref in (affected_refs or ()) if str(ref).strip()]
        if len(refs) > 50 or any(len(ref) > 200 for ref in refs):
            raise AccountError("Too many affected decisions.")
        if field == "assistance" and value != "external_help" and (description or refs):
            raise AccountError("Describe the help only when external help was received.")
        with self.accounts._transaction(write=True) as connection:
            actor = self.accounts._actor(connection, token)
            row = self._attempt(connection, actor, attempt_id, write=True)
            if field == "execution":
                test_account = (actor["role"] == "resident"
                                and actor["username"] in set(synthetic_accounts or ()))
                if not test_account and actor["role"] != "admin":
                    raise AccountError("Only a configured test account or an administrator records a "
                                       "synthetic run.")
                if actor["role"] == "admin" and not note:
                    raise AccountError("Say why the provenance of this record is being corrected.")
            if refs:
                from objectives import evidence_items
                record = self.accounts._attempt(row)
                known = {item["ref"] for item in evidence_items(record.get("payload") or {})
                         if item["kind"] == "decision"}
                if any(ref not in known for ref in refs):
                    raise AccountError("An affected decision is not part of this encounter.")
            highest = self._execute(connection, """SELECT COALESCE(MAX(sequence), 0) AS highest
                FROM mrs_encounter_context WHERE attempt_id = ? AND field = ?""",
                (attempt_id, field)).fetchone()
            sequence = int(highest["highest"] or 0) + 1
            identifier = uuid.uuid4().hex
            self._execute(connection, """INSERT INTO mrs_encounter_context
                (id, attempt_id, field, sequence, value, description, affected_json, note,
                 actor_id, actor_role, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (identifier, attempt_id, field, sequence, value, description,
                 json.dumps(refs), note, actor["id"], actor["role"], int(time.time())))
            return {"id": identifier, "field": field, "sequence": sequence, "value": value,
                    "description": description, "affected_refs": refs, "note": note,
                    "declared_by": actor["username"], "declared_by_role": actor["role"]}

    def history(self, token, attempt_id):
        """Every declaration, oldest first, with who made it and when."""
        with self.accounts._transaction() as connection:
            actor = self.accounts._actor(connection, token)
            self._attempt(connection, actor, attempt_id, write=False)
            rows = self._execute(connection, """SELECT c.*, u.username AS declared_by
                FROM mrs_encounter_context c JOIN mrs_users u ON u.id = c.actor_id
                WHERE c.attempt_id = ? ORDER BY c.field, c.sequence""", (attempt_id,)).fetchall()
            return [_row(row) for row in rows or []]

    def current(self, token, attempt_id):
        """The latest declaration of each kind, or None where nobody declared one."""
        latest = {"assistance": None, "execution": None}
        for row in self.history(token, attempt_id):
            latest[row["field"]] = row
        return latest


def _row(row):
    try:
        affected = json.loads(row["affected_json"] or "[]")
    except (TypeError, ValueError):
        affected = []
    return {"id": row["id"], "field": row["field"], "sequence": row["sequence"],
            "value": row["value"], "description": row["description"],
            "affected_refs": affected if isinstance(affected, list) else [],
            "note": row["note"], "declared_by": row["declared_by"],
            "declared_by_role": row["actor_role"], "declared_at": row["created_at"]}


def snapshot(current):
    """What an analysis is told, frozen at the moment it is requested.

    No username travels: the role that declared and when is what a reader
    needs, and an account name is not the model's business.
    """
    current = current or {}
    assistance = current.get("assistance")
    execution = current.get("execution")
    result = {
        "assistance": {"value": "not_reported", "label": label("assistance", "not_reported"),
                       "declared_by_role": None, "declared_at": None, "sequence": 0,
                       "description": "", "affected_refs": []}
        if assistance is None else
        {"value": assistance["value"], "label": label("assistance", assistance["value"]),
         "declared_by_role": assistance["declared_by_role"],
         "declared_at": assistance["declared_at"], "sequence": assistance["sequence"],
         "description": assistance["description"], "affected_refs": list(assistance["affected_refs"])},
        "execution": None if execution is None else
        {"value": execution["value"], "label": label("execution", execution["value"]),
         "declared_by_role": execution["declared_by_role"],
         "declared_at": execution["declared_at"], "sequence": execution["sequence"]},
    }
    return result


def not_reported():
    """The snapshot of an encounter nobody declared anything about."""
    return snapshot({})
