"""Faculty-reviewed, capped simulator evidence for one teaching program.

The configured targets are program choices, not certification requirements.
No encounter or AI output earns credit without an explicit faculty assessment.
All writes share AccountStore's transaction lock, including concurrent graders.
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid

from account_store import AccountError
from objectives import AUTONOMY_LEVELS, DEPTH_LEVELS, OBJECTIVES, evidence_items


STAFF = {"faculty", "admin"}


def _text(value, label, maximum=4000):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise AccountError(f"Provide {label} (1–{maximum} characters).")
    return value.strip()


def _objective(objective_id):
    if not isinstance(objective_id, str) or objective_id not in OBJECTIVES:
        raise AccountError("Choose a valid simulation objective.")
    return OBJECTIVES[objective_id]


def _json(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True)


class ProgressStore:
    """Persist reviewed evidence without changing any completed encounter.

    Assessments are immutable: void with a reason, then review again to correct
    one. Only one non-void assessment may exist per encounter and objective.
    A target applies across all depth levels, rather than once per depth.
    """

    def __init__(self, account_store):
        self.accounts = account_store
        self._execute = account_store._execute
        self._initialize()

    def _initialize(self):
        statements = [
            """CREATE TABLE IF NOT EXISTS mrs_progress_targets (
                objective_id TEXT PRIMARY KEY, target INTEGER NOT NULL,
                revision INTEGER NOT NULL DEFAULT 0,
                updated_by TEXT REFERENCES mrs_users(id), updated_at BIGINT NOT NULL,
                CHECK (target > 0 AND target <= 1000)
            )""",
            """CREATE TABLE IF NOT EXISTS mrs_progress_observations (
                id TEXT PRIMARY KEY,
                attempt_id TEXT NOT NULL REFERENCES mrs_attempts(id),
                user_id TEXT NOT NULL REFERENCES mrs_users(id),
                objective_id TEXT NOT NULL REFERENCES mrs_progress_targets(objective_id),
                assessor_id TEXT NOT NULL REFERENCES mrs_users(id),
                satisfactory INTEGER NOT NULL CHECK (satisfactory IN (0,1)),
                depth TEXT NOT NULL, autonomy TEXT NOT NULL, context TEXT NOT NULL,
                evidence_json TEXT NOT NULL, notes TEXT NOT NULL,
                source_revision INTEGER NOT NULL, payload_sha TEXT NOT NULL,
                created_at BIGINT NOT NULL,
                voided_at BIGINT, voided_by TEXT REFERENCES mrs_users(id), void_reason TEXT
            )""",
            """CREATE UNIQUE INDEX IF NOT EXISTS mrs_progress_current_observation
                ON mrs_progress_observations(attempt_id, objective_id) WHERE voided_at IS NULL""",
            """CREATE INDEX IF NOT EXISTS mrs_progress_user_objective
                ON mrs_progress_observations(user_id, objective_id)""",
            """CREATE TABLE IF NOT EXISTS mrs_progress_confirmations (
                user_id TEXT NOT NULL REFERENCES mrs_users(id),
                objective_id TEXT NOT NULL REFERENCES mrs_progress_targets(objective_id),
                confirmed INTEGER NOT NULL CHECK (confirmed IN (0,1)),
                reason TEXT NOT NULL, actor_id TEXT NOT NULL REFERENCES mrs_users(id),
                updated_at BIGINT NOT NULL, target_at_confirmation INTEGER,
                count_at_confirmation INTEGER, PRIMARY KEY (user_id, objective_id)
            )""",
            """CREATE TABLE IF NOT EXISTS mrs_progress_audit (
                id TEXT PRIMARY KEY, action TEXT NOT NULL,
                actor_id TEXT NOT NULL REFERENCES mrs_users(id),
                user_id TEXT REFERENCES mrs_users(id),
                objective_id TEXT REFERENCES mrs_progress_targets(objective_id),
                observation_id TEXT REFERENCES mrs_progress_observations(id),
                details_json TEXT NOT NULL, created_at BIGINT NOT NULL
            )""",
        ]
        with self.accounts._transaction(write=True) as connection:
            for statement in statements:
                self._execute(connection, statement)
            if self.accounts._sqlite:
                columns = {row["name"] for row in self._execute(connection,
                    "PRAGMA table_info(mrs_progress_confirmations)").fetchall()}
            else:
                columns = {row["column_name"] for row in self._execute(connection,
                    "SELECT column_name FROM information_schema.columns WHERE table_schema = current_schema() "
                    "AND table_name = 'mrs_progress_confirmations'").fetchall()}
            for column in ("target_at_confirmation", "count_at_confirmation"):
                if column not in columns:
                    self._execute(connection, f"ALTER TABLE mrs_progress_confirmations ADD COLUMN {column} INTEGER")
            for objective_id, definition in OBJECTIVES.items():
                self._execute(connection, """INSERT INTO mrs_progress_targets
                    (objective_id, target, revision, updated_by, updated_at)
                    VALUES (?, ?, 0, NULL, ?) ON CONFLICT(objective_id) DO NOTHING""",
                    (objective_id, definition["target"], int(time.time())))

    def _resident(self, connection, actor, user_id=None):
        user_id = actor["id"] if user_id is None else user_id
        if actor["role"] == "resident" and user_id != actor["id"]:
            raise AccountError("Your account can only access your own progress.")
        row = self._execute(connection, "SELECT * FROM mrs_users WHERE id = ? AND role = 'resident'",
                            (user_id,)).fetchone()
        if row is None:
            raise AccountError("The resident was not found.")
        return self.accounts._public_user(row)

    def _audit(self, connection, actor, action, user_id=None, objective_id=None,
               observation_id=None, details=None):
        self._execute(connection, "INSERT INTO mrs_progress_audit VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                      (f"{time.time_ns():020d}_{uuid.uuid4().hex}", action, actor["id"], user_id, objective_id,
                       observation_id, _json(details or {}), int(time.time())))

    def _count(self, connection, user_id, objective_id):
        return self._execute(connection, """SELECT COUNT(*) AS n FROM mrs_progress_observations
            WHERE user_id = ? AND objective_id = ? AND satisfactory = 1 AND voided_at IS NULL""",
            (user_id, objective_id)).fetchone()["n"]

    def _target(self, connection, objective_id):
        return self._execute(connection, "SELECT * FROM mrs_progress_targets WHERE objective_id = ?",
                             (objective_id,)).fetchone()

    def _confirmation(self, connection, user_id, objective_id):
        return self._execute(connection, """SELECT c.*, u.username AS assessor
            FROM mrs_progress_confirmations c JOIN mrs_users u ON u.id = c.actor_id
            WHERE c.user_id = ? AND c.objective_id = ?""", (user_id, objective_id)).fetchone()

    def _set_confirmation(self, connection, actor, user_id, objective_id, confirmed, reason):
        if confirmed:
            target = self._target(connection, objective_id)["target"]
            count = self._count(connection, user_id, objective_id)
        else:
            previous = self._confirmation(connection, user_id, objective_id)
            target = previous["target_at_confirmation"] if previous else None
            count = previous["count_at_confirmation"] if previous else None
        self._execute(connection, """INSERT INTO mrs_progress_confirmations
            (user_id, objective_id, confirmed, reason, actor_id, updated_at,
             target_at_confirmation, count_at_confirmation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(user_id, objective_id) DO UPDATE SET
            confirmed = excluded.confirmed, reason = excluded.reason,
            actor_id = excluded.actor_id, updated_at = excluded.updated_at,
            target_at_confirmation = excluded.target_at_confirmation,
            count_at_confirmation = excluded.count_at_confirmation""",
            (user_id, objective_id, int(confirmed), reason, actor["id"], int(time.time()), target, count))

    @staticmethod
    def _observation(row):
        result = dict(row)
        result["satisfactory"] = bool(result["satisfactory"])
        result["voided"] = result["voided_at"] is not None
        result["evidence"] = json.loads(result.pop("evidence_json"))
        result["evidence_refs"] = [item["ref"] for item in result["evidence"]]
        return result

    def list_residents(self, token):
        with self.accounts._transaction() as connection:
            self.accounts._actor(connection, token, STAFF)
            return [self.accounts._public_user(row) for row in self._execute(connection,
                "SELECT * FROM mrs_users WHERE role = 'resident' ORDER BY username").fetchall()]

    def list_targets(self, token):
        """Read program targets even before any residents are enrolled."""
        with self.accounts._transaction() as connection:
            self.accounts._actor(connection, token, STAFF)
            targets = {row["objective_id"]: row for row in self._execute(connection,
                "SELECT * FROM mrs_progress_targets").fetchall()}
            return [{**definition, "objective_id": objective_id,
                     "target": targets[objective_id]["target"],
                     "target_revision": targets[objective_id]["revision"]}
                    for objective_id, definition in OBJECTIVES.items()]

    def get_progress(self, token, user_id=None):
        """Residents see their own record; staff must choose a resident ID."""
        with self.accounts._transaction() as connection:
            if not self.accounts._sqlite:
                # Target, count and confirmation must describe one snapshot,
                # even while another grader or administrator commits a change.
                self._execute(connection, "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
            actor = self.accounts._actor(connection, token)
            user = self._resident(connection, actor, user_id)
            objectives = []
            for objective_id, definition in OBJECTIVES.items():
                target = self._target(connection, objective_id)
                rows = self._execute(connection, """SELECT o.*, u.username AS assessor
                    FROM mrs_progress_observations o JOIN mrs_users u ON u.id = o.assessor_id
                    WHERE o.user_id = ? AND o.objective_id = ? ORDER BY o.created_at, o.id""",
                    (user["id"], objective_id)).fetchall()
                observations = [self._observation(row) for row in rows]
                count = sum(item["satisfactory"] and not item["voided"] for item in observations)
                confirmation = self._confirmation(connection, user["id"], objective_id)
                confirmed = bool(confirmation and confirmation["confirmed"])
                objectives.append({
                    **definition, "objective_id": objective_id, "target": target["target"],
                    "target_revision": target["revision"], "count": count,
                    "status": "not_available" if not definition["supported"] else (
                        "confirmed" if confirmed else (
                            "target_reached" if count >= target["target"] else (
                                "developing" if any(not item["voided"] for item in observations)
                                else "not_observed"))),
                    "confirmed": confirmed,
                    "confirmation": dict(confirmation) if confirmation else None,
                    "observations": observations,
                    "assessed_count": sum(not item["voided"] for item in observations),
                })
            return {"user": user, "objectives": objectives}

    def assess(self, token, attempt_id, objective_id, assessment):
        """Review one simulated component, never an entire workplace EPA.

        Required assessment fields: satisfactory (bool), depth, autonomy,
        context, evidence_refs (nonempty list of evidence_items refs), notes.
        Results: credited / recorded / capped / duplicate. Once capped or
        confirmed, no new objective observation is inserted, even unsuccessful.
        """
        with self.accounts._transaction(write=True) as connection:
            actor = self.accounts._actor(connection, token, STAFF)
            definition = _objective(objective_id)
            if not definition["supported"]:
                raise AccountError("This objective is not supported by the current simulator.")
            attempt = self._execute(connection, """SELECT a.*, u.role AS owner_role
                FROM mrs_attempts a JOIN mrs_users u ON u.id = a.user_id WHERE a.id = ?""",
                (attempt_id,)).fetchone()
            if (attempt is None or attempt["owner_role"] != "resident" or attempt["is_sandbox"]
                    or attempt["status"] != "completed" or attempt["user_id"] == actor["id"]):
                raise AccountError("Review requires a completed, non-sandbox resident encounter.")
            payload = json.loads(attempt["payload_json"])
            session = payload.get("session") if isinstance(payload, dict) else None
            if not isinstance(session, dict) or session.get("review_completed") is not True:
                raise AccountError("Review requires the resident's completed encounter reflection.")
            existing = self._execute(connection, """SELECT id FROM mrs_progress_observations
                WHERE attempt_id = ? AND objective_id = ? AND voided_at IS NULL""",
                (attempt_id, objective_id)).fetchone()
            count = self._count(connection, attempt["user_id"], objective_id)
            target = self._target(connection, objective_id)["target"]
            if existing:
                return {"status": "duplicate", "observation_id": existing["id"], "count": count, "target": target}
            confirmation = self._confirmation(connection, attempt["user_id"], objective_id)
            if count >= target or (confirmation and confirmation["confirmed"]):
                return {"status": "capped", "count": count, "target": target}
            if not isinstance(assessment, dict) or not isinstance(assessment.get("satisfactory"), bool):
                raise AccountError("Choose whether the simulated component was demonstrated satisfactorily.")
            if assessment.get("depth") not in DEPTH_LEVELS:
                raise AccountError("Choose a valid simulation depth.")
            if assessment.get("autonomy") not in AUTONOMY_LEVELS:
                raise AccountError("Choose a valid level of assistance.")
            context = _text(assessment.get("context"), "the case context", 1000)
            notes = _text(assessment.get("notes"), "your assessment rationale")
            refs = assessment.get("evidence_refs")
            if (not isinstance(refs, list) or not refs or len(refs) > 100
                    or any(not isinstance(ref, str) for ref in refs) or len(set(refs)) != len(refs)):
                raise AccountError("Select at least one distinct item of saved encounter evidence.")
            available = {item["ref"]: item for item in evidence_items(payload)}
            if any(ref not in available for ref in refs):
                raise AccountError("The selected evidence is not present in this completed encounter.")
            selected = [available[ref] for ref in refs]
            encoded_evidence = _json(selected)
            if len(encoded_evidence.encode("utf-8")) > 1_000_000:
                raise AccountError("The selected evidence is too large to save.")
            observation_id = uuid.uuid4().hex
            self._execute(connection, """INSERT INTO mrs_progress_observations
                (id, attempt_id, user_id, objective_id, assessor_id, satisfactory, depth,
                 autonomy, context, evidence_json, notes, source_revision, payload_sha, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (observation_id, attempt_id, attempt["user_id"], objective_id, actor["id"],
                 int(assessment["satisfactory"]), assessment["depth"], assessment["autonomy"],
                 context, encoded_evidence, notes, attempt["revision"],
                 hashlib.sha256(_json(payload).encode("utf-8")).hexdigest(), int(time.time())))
            status = "credited" if assessment["satisfactory"] else "recorded"
            self._audit(connection, actor, status, attempt["user_id"], objective_id, observation_id,
                        {"target": target, "source_revision": attempt["revision"]})
            return {"status": status, "observation_id": observation_id,
                    "count": count + int(assessment["satisfactory"]), "target": target}

    def set_target(self, token, objective_id, target, reason):
        """Set a program target; never truncate previously accepted evidence."""
        with self.accounts._transaction(write=True) as connection:
            actor = self.accounts._actor(connection, token, {"admin"})
            _objective(objective_id)
            if isinstance(target, bool) or not isinstance(target, int) or not 1 <= target <= 1000:
                raise AccountError("The program target must be a whole number between 1 and 1,000.")
            reason = _text(reason, "the reason for changing the program target")
            row = self._target(connection, objective_id)
            if row["target"] == target:
                return {"target": target, "revision": row["revision"], "changed": False}
            maximum = self._execute(connection, """SELECT COUNT(*) AS n FROM mrs_progress_observations
                WHERE objective_id = ? AND satisfactory = 1 AND voided_at IS NULL
                GROUP BY user_id ORDER BY n DESC LIMIT 1""", (objective_id,)).fetchone()
            if maximum and maximum["n"] > target:
                raise AccountError("The target cannot be lower than an existing accepted observation count.")
            self._execute(connection, """UPDATE mrs_progress_targets SET target = ?,
                revision = revision + 1, updated_by = ?, updated_at = ? WHERE objective_id = ?""",
                (target, actor["id"], int(time.time()), objective_id))
            self._audit(connection, actor, "target_changed", objective_id=objective_id,
                        details={"before": row["target"], "after": target, "reason": reason})
            return {"target": target, "revision": row["revision"] + 1, "changed": True}

    def confirm(self, token, user_id, objective_id, reason):
        """Confirm a simulator learning goal after faculty quality review."""
        with self.accounts._transaction(write=True) as connection:
            actor = self.accounts._actor(connection, token, STAFF)
            definition = _objective(objective_id)
            user = self._resident(connection, actor, user_id)
            reason = _text(reason, "the faculty confirmation rationale")
            if not definition["supported"]:
                raise AccountError("This objective is not supported by the current simulator.")
            count = self._count(connection, user["id"], objective_id)
            target = self._target(connection, objective_id)["target"]
            if count < target:
                raise AccountError("The numeric target must be reached before faculty confirmation.")
            existing = self._confirmation(connection, user["id"], objective_id)
            if existing and existing["confirmed"]:
                return {"status": "confirmed", "changed": False}
            self._set_confirmation(connection, actor, user["id"], objective_id, True, reason)
            self._audit(connection, actor, "confirmed", user["id"], objective_id,
                        details={"reason": reason, "count": count, "target": target})
            return {"status": "confirmed", "changed": True}

    def reopen(self, token, user_id, objective_id, reason):
        """Remove confirmation, retaining all observations and numeric counts.

        Reopening does not itself create capacity. An administrator must raise
        the program target to collect more observations after the cap is met.
        """
        with self.accounts._transaction(write=True) as connection:
            actor = self.accounts._actor(connection, token, STAFF)
            _objective(objective_id)
            user = self._resident(connection, actor, user_id)
            reason = _text(reason, "the reason for reopening this learning goal")
            existing = self._confirmation(connection, user["id"], objective_id)
            if not existing or not existing["confirmed"]:
                return {"changed": False}
            self._set_confirmation(connection, actor, user["id"], objective_id, False, reason)
            self._audit(connection, actor, "reopened", user["id"], objective_id, details={"reason": reason})
            return {"changed": True}

    def void_observation(self, token, observation_id, reason):
        """Retain a mistaken assessment, excluding it from counts, with audit."""
        with self.accounts._transaction(write=True) as connection:
            actor = self.accounts._actor(connection, token, STAFF)
            reason = _text(reason, "the reason for voiding this assessment")
            observation = self._execute(connection, "SELECT * FROM mrs_progress_observations WHERE id = ?",
                                        (observation_id,)).fetchone()
            if observation is None:
                raise AccountError("The assessment was not found.")
            if observation["user_id"] == actor["id"]:
                raise AccountError("Faculty cannot change assessments of their own encounters.")
            if observation["voided_at"] is not None:
                return {"changed": False}
            self._execute(connection, """UPDATE mrs_progress_observations
                SET voided_at = ?, voided_by = ?, void_reason = ? WHERE id = ? AND voided_at IS NULL""",
                (int(time.time()), actor["id"], reason, observation_id))
            self._audit(connection, actor, "voided", observation["user_id"], observation["objective_id"],
                        observation_id, {"reason": reason})
            confirmation = self._confirmation(connection, observation["user_id"], observation["objective_id"])
            if confirmation and confirmation["confirmed"]:
                self._set_confirmation(connection, actor, observation["user_id"], observation["objective_id"],
                                       False, "Assessment voided: " + reason)
                self._audit(connection, actor, "reopened_after_void", observation["user_id"],
                            observation["objective_id"], observation_id, {"reason": reason})
            return {"changed": True}

    def list_audit(self, token, user_id=None):
        with self.accounts._transaction() as connection:
            actor = self.accounts._actor(connection, token, STAFF)
            sql = """SELECT a.*, u.username AS actor FROM mrs_progress_audit a
                JOIN mrs_users u ON u.id = a.actor_id"""
            parameters = ()
            if user_id is not None:
                self._resident(connection, actor, user_id)
                # Program-wide target changes also affect this resident.
                sql += " WHERE a.user_id = ? OR a.user_id IS NULL"
                parameters = (user_id,)
            result = []
            for row in self._execute(connection, sql + " ORDER BY a.created_at, a.id", parameters).fetchall():
                item = dict(row)
                item["details"] = json.loads(item.pop("details_json"))
                result.append(item)
            return result
