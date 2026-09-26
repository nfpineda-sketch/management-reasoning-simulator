"""Faculty-reviewed longitudinal simulator evidence for one teaching program.

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
from competency_mapping import objective_is_eligible, objective_evidence_is_eligible
from objectives import AUTONOMY_LEVELS, DEPTH_LEVELS, OBJECTIVES, evidence_items


STAFF = {"faculty", "admin"}
# The faculty's explicit judgment that the level of autonomy could not be
# determined from what was observed (faculty specification 2026-09-24, §7).
# It is not "guided", not a failure and not independence: the observation is
# recorded and counts on its own merits, and the autonomy is said to be unknown.
AUTONOMY_NOT_DETERMINED = "not_determined"
DRAFT_FIELDS = ("satisfactory", "depth", "autonomy", "context", "evidence_refs", "notes", "ai_brief_id")


def meets_autonomy(autonomy, required):
    """Whether an observation's autonomy meets an objective's required level.

    Faculty decision 10 of 2026-09-25 ("Autonomía no determinada: opción C,
    distinguiendo observaciones de logro"). A validated observation whose
    autonomy could not be determined accumulates like any other, and how many
    have that condition is shown. When completing an objective requires a
    level of autonomy, such an observation does not meet it: nothing assumes
    the level that nobody could determine. With no required level, every
    satisfactory observation counts toward the target, as before.
    """
    if not required:
        return True
    if autonomy not in AUTONOMY_LEVELS or required not in AUTONOMY_LEVELS:
        return False
    return AUTONOMY_LEVELS.index(autonomy) >= AUTONOMY_LEVELS.index(required)


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
        if self.accounts.schema_ready("progress_store"):
            return
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
                count_at_confirmation INTEGER, observation_ids_json TEXT,
                PRIMARY KEY (user_id, objective_id)
            )""",
            # A faculty member's work in progress on one objective of one
            # encounter. Append-only; never counted; never shown to a resident.
            """CREATE TABLE IF NOT EXISTS mrs_progress_drafts (
                id TEXT PRIMARY KEY,
                attempt_id TEXT NOT NULL REFERENCES mrs_attempts(id),
                objective_id TEXT NOT NULL REFERENCES mrs_progress_targets(objective_id),
                sequence INTEGER NOT NULL CHECK (sequence >= 1),
                author_id TEXT NOT NULL REFERENCES mrs_users(id),
                draft_json TEXT NOT NULL,
                created_at BIGINT NOT NULL
            )""",
            """CREATE INDEX IF NOT EXISTS mrs_progress_drafts_attempt
                ON mrs_progress_drafts(attempt_id, objective_id, sequence)""",
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
            if "observation_ids_json" not in columns:
                self._execute(connection, "ALTER TABLE mrs_progress_confirmations ADD COLUMN observation_ids_json TEXT")
            # Snapshot legacy confirmations before accepting continued evidence.
            # IDs avoid ambiguous comparisons when assessments share a second.
            for confirmation in self._execute(connection, "SELECT user_id, objective_id FROM mrs_progress_confirmations WHERE observation_ids_json IS NULL").fetchall():
                ids = self._observation_ids(connection, confirmation["user_id"], confirmation["objective_id"])
                self._execute(connection, "UPDATE mrs_progress_confirmations SET observation_ids_json = ? WHERE user_id = ? AND objective_id = ?",
                              (_json(ids), confirmation["user_id"], confirmation["objective_id"]))
            for objective_id, definition in OBJECTIVES.items():
                self._execute(connection, """INSERT INTO mrs_progress_targets
                    (objective_id, target, revision, updated_by, updated_at)
                    VALUES (?, ?, 0, NULL, ?) ON CONFLICT(objective_id) DO NOTHING""",
                    (objective_id, definition["target"], int(time.time())))
        self.accounts.mark_schema_ready("progress_store")

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
        """Satisfactory observations that count toward the objective's target."""
        required = OBJECTIVES[objective_id].get("required_autonomy")
        rows = self._execute(connection, """SELECT autonomy FROM mrs_progress_observations
            WHERE user_id = ? AND objective_id = ? AND satisfactory = 1 AND voided_at IS NULL""",
            (user_id, objective_id)).fetchall()
        return sum(meets_autonomy(row["autonomy"], required) for row in rows)

    def _has_table(self, connection, name):
        if self.accounts._sqlite:
            return self._execute(connection, "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
                                 (name,)).fetchone() is not None
        return self._execute(connection, "SELECT table_name FROM information_schema.tables "
                             "WHERE table_schema = current_schema() AND table_name = ?",
                             (name,)).fetchone() is not None

    def _synthetic_attempts(self, connection, user_id):
        """The resident's encounters whose latest execution declaration is a synthetic run.

        The declaration lives in the encounter context (encounter_context.py),
        made by a configured test account or corrected by an administrator.
        An observation of such an encounter keeps saying so wherever the
        progress is shown: it is the run of a test, not a person's performance.
        """
        if not self._has_table(connection, "mrs_encounter_context"):
            return set()
        latest = {}
        for row in self._execute(connection, """SELECT c.attempt_id, c.value FROM mrs_encounter_context c
                JOIN mrs_attempts a ON a.id = c.attempt_id
                WHERE a.user_id = ? AND c.field = 'execution' ORDER BY c.attempt_id, c.sequence""",
                (user_id,)).fetchall():
            latest[row["attempt_id"]] = row["value"]
        return {attempt_id for attempt_id, value in latest.items() if value == "synthetic_agent"}

    def _target(self, connection, objective_id):
        return self._execute(connection, "SELECT * FROM mrs_progress_targets WHERE objective_id = ?",
                             (objective_id,)).fetchone()

    def _confirmation(self, connection, user_id, objective_id):
        return self._execute(connection, """SELECT c.*, u.username AS assessor
            FROM mrs_progress_confirmations c JOIN mrs_users u ON u.id = c.actor_id
            WHERE c.user_id = ? AND c.objective_id = ?""", (user_id, objective_id)).fetchone()

    def _observation_ids(self, connection, user_id, objective_id):
        return sorted(row["id"] for row in self._execute(connection,
            "SELECT id FROM mrs_progress_observations WHERE user_id = ? AND objective_id = ? AND voided_at IS NULL",
            (user_id, objective_id)).fetchall())

    def _set_confirmation(self, connection, actor, user_id, objective_id, confirmed, reason):
        if confirmed:
            target = self._target(connection, objective_id)["target"]
            count = self._count(connection, user_id, objective_id)
            observation_ids = _json(self._observation_ids(connection, user_id, objective_id))
        else:
            previous = self._confirmation(connection, user_id, objective_id)
            target = previous["target_at_confirmation"] if previous else None
            count = previous["count_at_confirmation"] if previous else None
            observation_ids = previous["observation_ids_json"] if previous else "[]"
        self._execute(connection, """INSERT INTO mrs_progress_confirmations
            (user_id, objective_id, confirmed, reason, actor_id, updated_at,
             target_at_confirmation, count_at_confirmation, observation_ids_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(user_id, objective_id) DO UPDATE SET
            confirmed = excluded.confirmed, reason = excluded.reason,
            actor_id = excluded.actor_id, updated_at = excluded.updated_at,
            target_at_confirmation = excluded.target_at_confirmation,
            count_at_confirmation = excluded.count_at_confirmation,
            observation_ids_json = excluded.observation_ids_json""",
            (user_id, objective_id, int(confirmed), reason, actor["id"], int(time.time()), target, count, observation_ids))

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
            synthetic = self._synthetic_attempts(connection, user["id"])
            objectives = []
            for objective_id, definition in OBJECTIVES.items():
                target = self._target(connection, objective_id)
                rows = self._execute(connection, """SELECT o.*, u.username AS assessor
                    FROM mrs_progress_observations o JOIN mrs_users u ON u.id = o.assessor_id
                    WHERE o.user_id = ? AND o.objective_id = ? ORDER BY o.created_at, o.id""",
                    (user["id"], objective_id)).fetchall()
                observations = [self._observation(row) for row in rows]
                for item in observations:
                    item["synthetic_execution"] = item["attempt_id"] in synthetic
                satisfactory = [item for item in observations if item["satisfactory"] and not item["voided"]]
                required = definition.get("required_autonomy")
                # What accumulates, and what completes the objective, are told
                # apart (decision 10): every satisfactory observation is shown;
                # only those meeting a required autonomy count toward the target.
                count = sum(meets_autonomy(item["autonomy"], required) for item in satisfactory)
                confirmation = self._confirmation(connection, user["id"], objective_id)
                confirmed = bool(confirmation and confirmation["confirmed"])
                reviewed_ids = set(json.loads(confirmation["observation_ids_json"] or "[]")) if confirmation else set()
                continued = [item for item in observations if not item["voided"] and item["id"] not in reviewed_ids] if confirmed else []
                later_concerns = sum(not item["satisfactory"] for item in continued)
                objectives.append({
                    **definition, "objective_id": objective_id, "target": target["target"],
                    "target_revision": target["revision"], "count": count,
                    "satisfactory_count": len(satisfactory),
                    "required_autonomy": required,
                    "autonomy_not_determined_count": sum(
                        item["autonomy"] == AUTONOMY_NOT_DETERMINED for item in satisfactory),
                    "below_required_autonomy_count": len(satisfactory) - count,
                    "synthetic_count": sum(item["synthetic_execution"] for item in satisfactory),
                    "status": "not_available" if not definition["supported"] else (
                        "confirmed" if confirmed else (
                            "target_reached" if count >= target["target"] else (
                                "developing" if any(not item["voided"] for item in observations)
                                else "not_observed"))),
                    "confirmed": confirmed,
                    "confirmation": dict(confirmation) if confirmation else None,
                    "observations": observations,
                    "assessed_count": sum(not item["voided"] for item in observations),
                    "needs_improvement_count": sum(not item["voided"] and not item["satisfactory"] for item in observations),
                    "target_reached": count >= target["target"],
                    "post_confirmation_count": len(continued),
                    "post_confirmation_needs_improvement_count": later_concerns,
                    "review_recommended": bool(confirmed and later_concerns),
                })
            return {"user": user, "objectives": objectives}

    def assess(self, token, attempt_id, objective_id, assessment):
        """Review one simulated component, never an entire workplace EPA.

        Required assessment fields: satisfactory (bool), depth, autonomy,
        context, evidence_refs (nonempty list of evidence_items refs), notes.
        Results: credited / recorded / duplicate. Targets and confirmation never
        stop new observations. Later concerns remain visible for faculty review;
        neither improvement nor concern automatically changes confirmation.
        """
        with self.accounts._transaction(write=True) as connection:
            actor = self.accounts._actor(connection, token, STAFF)
            definition = _objective(objective_id)
            if not definition["supported"]:
                raise AccountError("This objective is not supported by the current simulator.")
            attempt = self._execute(connection, """SELECT a.*, u.username, u.role AS owner_role
                FROM mrs_attempts a JOIN mrs_users u ON u.id = a.user_id WHERE a.id = ?""",
                (attempt_id,)).fetchone()
            if (attempt is None or attempt["owner_role"] != "resident" or attempt["is_sandbox"]
                    or attempt["status"] != "completed" or attempt["user_id"] == actor["id"]):
                raise AccountError("Review requires a completed, non-sandbox resident encounter.")
            payload = json.loads(attempt["payload_json"])
            session = payload.get("session") if isinstance(payload, dict) else None
            if not isinstance(session, dict) or session.get("review_completed") is not True:
                raise AccountError("Review requires the resident's completed encounter reflection.")
            if not objective_is_eligible(objective_id, self.accounts._attempt(attempt)):
                raise AccountError("This objective does not match the saved clinical challenge.")
            existing = self._execute(connection, """SELECT id FROM mrs_progress_observations
                WHERE attempt_id = ? AND objective_id = ? AND voided_at IS NULL""",
                (attempt_id, objective_id)).fetchone()
            count = self._count(connection, attempt["user_id"], objective_id)
            target = self._target(connection, objective_id)["target"]
            if existing:
                return {"status": "duplicate", "observation_id": existing["id"], "count": count, "target": target}
            confirmation = self._confirmation(connection, attempt["user_id"], objective_id)
            if not isinstance(assessment, dict) or not isinstance(assessment.get("satisfactory"), bool):
                raise AccountError("Choose whether the simulated component was demonstrated satisfactorily.")
            if assessment.get("depth") not in DEPTH_LEVELS:
                raise AccountError("Choose a valid simulation depth.")
            if assessment.get("autonomy") not in (*AUTONOMY_LEVELS, AUTONOMY_NOT_DETERMINED):
                # Asked for here, when this objective is confirmed, and only
                # here: the brief, the rubric and a draft never need it.
                raise AccountError("To confirm this objective, choose the level of autonomy observed, "
                                   "or record that it could not be determined. Everything else can "
                                   "be kept as a draft in the meantime.")
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
            if not objective_evidence_is_eligible(objective_id, selected):
                raise AccountError("Select a recorded management decision to support this challenge assessment.")
            encoded_evidence = _json(selected)
            if len(encoded_evidence.encode("utf-8")) > 1_000_000:
                raise AccountError("The selected evidence is too large to save.")
            ai_brief_id = assessment.get("ai_brief_id")
            if ai_brief_id is not None:
                # Attribute an explicitly reviewed draft without treating its
                # suggestions as the final assessment. Keep the source report
                # private; learner feedback contains only faculty-saved fields.
                from faculty_analysis import source_fingerprint
                ai_brief_id = _text(ai_brief_id, "the saved AI draft reference", 100)
                brief = self._execute(connection, """SELECT attempt_id, source_hash, attempt_revision
                    FROM mrs_faculty_briefs WHERE id = ?""", (ai_brief_id,)).fetchone()
                if (brief is None or brief["attempt_id"] != attempt_id
                        or brief["attempt_revision"] != attempt["revision"]
                        or brief["source_hash"] != source_fingerprint(self.accounts._attempt(attempt))):
                    raise AccountError("The AI draft does not match this completed encounter. Reload its analysis.")
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
                        {"target": target, "source_revision": attempt["revision"],
                         "after_target": count >= target,
                         "after_confirmation": bool(confirmation and confirmation["confirmed"]),
                         **({"ai_brief_id": ai_brief_id} if ai_brief_id is not None else {})})
            return {"status": status, "observation_id": observation_id,
                    "count": count + int(assessment["satisfactory"]), "target": target}

    def _assessable_attempt(self, connection, actor, attempt_id, objective_id):
        definition = _objective(objective_id)
        if not definition["supported"]:
            raise AccountError("This objective is not supported by the current simulator.")
        attempt = self._execute(connection, """SELECT a.*, u.username, u.role AS owner_role
            FROM mrs_attempts a JOIN mrs_users u ON u.id = a.user_id WHERE a.id = ?""",
            (attempt_id,)).fetchone()
        if (attempt is None or attempt["owner_role"] != "resident" or attempt["is_sandbox"]
                or attempt["status"] != "completed" or attempt["user_id"] == actor["id"]):
            raise AccountError("Review requires a completed, non-sandbox resident encounter.")
        return attempt

    def save_draft(self, token, attempt_id, objective_id, draft):
        """Keep a faculty member's unfinished assessment, with whatever is still pending.

        Saving the encounter, saving the AI's analysis, saving a draft and
        confirming an observation are four different things (2026-09-24, §7);
        the first three accept missing data. A draft never counts, never reaches
        the resident, and never replaces a recorded observation.
        """
        if not isinstance(draft, dict):
            raise AccountError("The draft has an invalid format.")
        clean = {}
        for field in DRAFT_FIELDS:
            value = draft.get(field)
            if value is None:
                continue
            if field == "satisfactory" and not isinstance(value, bool):
                raise AccountError("The draft decision has an invalid format.")
            if field == "depth" and value not in DEPTH_LEVELS:
                raise AccountError("Choose a valid simulation depth.")
            if field == "autonomy" and value not in (*AUTONOMY_LEVELS, AUTONOMY_NOT_DETERMINED):
                raise AccountError("Choose a valid level of autonomy.")
            if field in ("context", "notes", "ai_brief_id"):
                value = str(value)
                if len(value) > 4000:
                    raise AccountError("A draft field is too long.")
            if field == "evidence_refs":
                if not isinstance(value, list) or len(value) > 100 or any(not isinstance(r, str) for r in value):
                    raise AccountError("The draft evidence has an invalid format.")
                value = list(dict.fromkeys(value))
            clean[field] = value
        with self.accounts._transaction(write=True) as connection:
            actor = self.accounts._actor(connection, token, STAFF)
            attempt = self._assessable_attempt(connection, actor, attempt_id, objective_id)
            if clean.get("evidence_refs"):
                payload = json.loads(attempt["payload_json"])
                available = {item["ref"] for item in evidence_items(payload)}
                if any(ref not in available for ref in clean["evidence_refs"]):
                    raise AccountError("The selected evidence is not present in this completed encounter.")
            highest = self._execute(connection, """SELECT COALESCE(MAX(sequence), 0) AS highest
                FROM mrs_progress_drafts WHERE attempt_id = ? AND objective_id = ?""",
                (attempt_id, objective_id)).fetchone()
            sequence = int(highest["highest"] or 0) + 1
            self._execute(connection, """INSERT INTO mrs_progress_drafts
                (id, attempt_id, objective_id, sequence, author_id, draft_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (uuid.uuid4().hex, attempt_id, objective_id, sequence, actor["id"], _json(clean),
                 int(time.time())))
            return {"sequence": sequence, "draft": clean, "pending": pending_fields(clean)}

    def latest_draft(self, token, attempt_id, objective_id):
        """The most recent draft of one objective for one encounter, or None."""
        with self.accounts._transaction() as connection:
            actor = self.accounts._actor(connection, token, STAFF)
            self._assessable_attempt(connection, actor, attempt_id, objective_id)
            row = self._execute(connection, """SELECT d.*, u.username AS author
                FROM mrs_progress_drafts d JOIN mrs_users u ON u.id = d.author_id
                WHERE d.attempt_id = ? AND d.objective_id = ?
                ORDER BY d.sequence DESC LIMIT 1""", (attempt_id, objective_id)).fetchone()
            if row is None:
                return None
            draft = json.loads(row["draft_json"])
            return {"sequence": row["sequence"], "author": row["author"],
                    "created_at": row["created_at"], "draft": draft, "pending": pending_fields(draft)}

    def pending_reviews(self, token, user_id=None):
        """What is waiting on the faculty, encounter by encounter.

        For every completed resident encounter: which supported objectives still
        have no observation recorded, and which of those have a draft. Nothing
        here is a count of achievement.
        """
        from competency_mapping import objective_is_eligible
        with self.accounts._transaction() as connection:
            actor = self.accounts._actor(connection, token, STAFF)
            sql = """SELECT a.*, u.username, u.role AS owner_role FROM mrs_attempts a
                JOIN mrs_users u ON u.id = a.user_id
                WHERE u.role = 'resident' AND a.status = 'completed' AND a.is_sandbox = 0"""
            parameters = ()
            if user_id is not None:
                sql += " AND a.user_id = ?"
                parameters = (user_id,)
            rows = self._execute(connection, sql + " ORDER BY a.updated_at", parameters).fetchall()
            waiting = []
            for row in rows or []:
                record = self.accounts._attempt(row)
                assessed = {r["objective_id"] for r in self._execute(connection, """SELECT objective_id
                    FROM mrs_progress_observations WHERE attempt_id = ? AND voided_at IS NULL""",
                    (row["id"],)).fetchall()}
                drafted = {r["objective_id"] for r in self._execute(connection, """SELECT DISTINCT objective_id
                    FROM mrs_progress_drafts WHERE attempt_id = ?""", (row["id"],)).fetchall()}
                eligible = [key for key, value in OBJECTIVES.items()
                            if value["supported"] and objective_is_eligible(key, record)]
                pending = [key for key in eligible if key not in assessed]
                waiting.append({"attempt_id": row["id"], "user_id": row["user_id"],
                                "username": row["username"], "challenge_id": row["challenge_id"],
                                "updated_at": row["updated_at"], "pending_objectives": pending,
                                "drafted_objectives": sorted(drafted & set(pending)),
                                "assessed_objectives": sorted(assessed)})
            return waiting

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
            # A target is a review threshold, never a limit on accumulated evidence.
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
                raise AccountError("The numeric target must be reached before faculty confirmation."
                                   + (" Only observations at the required level of autonomy count toward "
                                      "it; an autonomy that could not be determined does not meet it."
                                      if definition.get("required_autonomy") else ""))
            existing = self._confirmation(connection, user["id"], objective_id)
            current_ids = self._observation_ids(connection, user["id"], objective_id)
            already_confirmed = bool(existing and existing["confirmed"])
            if already_confirmed and current_ids == json.loads(existing["observation_ids_json"] or "[]"):
                return {"status": "confirmed", "changed": False}
            self._set_confirmation(connection, actor, user["id"], objective_id, True, reason)
            self._audit(connection, actor, "confirmation_reviewed" if already_confirmed else "confirmed", user["id"], objective_id,
                        details={"reason": reason, "count": count, "target": target,
                                 "observation_ids": current_ids})
            return {"status": "confirmed", "changed": True}

    def reopen(self, token, user_id, objective_id, reason):
        """Remove confirmation, retaining all observations and numeric counts.

        Continued observation is always available, including while confirmed.
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
            if (confirmation and confirmation["confirmed"]
                    and observation["id"] in json.loads(confirmation["observation_ids_json"] or "[]")):
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


def pending_fields(draft):
    """What a draft still needs before it can be confirmed, in plain words."""
    missing = []
    if not isinstance((draft or {}).get("satisfactory"), bool):
        missing.append("the decision")
    if (draft or {}).get("depth") not in DEPTH_LEVELS:
        missing.append("the depth")
    if (draft or {}).get("autonomy") not in (*AUTONOMY_LEVELS, AUTONOMY_NOT_DETERMINED):
        missing.append("the autonomy (a level, or that it could not be determined)")
    if not str((draft or {}).get("context") or "").strip():
        missing.append("the clinical context")
    if not (draft or {}).get("evidence_refs"):
        missing.append("the supporting evidence")
    if not str((draft or {}).get("notes") or "").strip():
        missing.append("the rationale and feedback")
    return missing
