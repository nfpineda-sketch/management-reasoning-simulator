"""A faculty member chooses a resident's next case, and says why.

Until 2026-09-24 a resident's next encounter was always the curriculum's
choice: the challenge from the assignment rule, and the case from that
challenge's families (generated, or drawn from the bank). Nothing let a faculty
member say "this resident's next case is this one". The synthetic batch of
twenty scenarios needed exactly that -- twenty chosen, tested cases, played by
a real resident account through the real circuit -- and so does a teacher who
wants a resident to meet a particular patient.

A directive is one-shot, explicit and on the record:

* an administrator, or a faculty member an administrator authorized for that
  resident, names the resident, the challenge and one authored case that
  challenge offers, with a written reason;
* the resident's next launch uses it and consumes it; the assignment records
  that it was directed and by whom, and points to the directive;
* a new directive for the same resident replaces the one waiting, and the
  replaced one stays in the history as cancelled. Nothing is deleted.

Without a directive, the curriculum's rule is exactly what it was.

Faculty decision 14 of 2026-09-25 ("aprobar A con permisos acotados"). The
permission is scoped: an administrator may direct any resident's next case; a
faculty member only the residents an administrator authorized them for, each
authorization with its reason and kept, like the directives, when revoked. The
choice reveals nothing to the resident: the faculty's reason -- which may name
the diagnosis or what the case is meant to teach -- stays in this staff-only
history and never enters the resident's encounter record, and nothing on the
resident's page says that the case was chosen, or which one it is.
"""
from __future__ import annotations

import time
import uuid

from account_store import AccountError

STAFF = frozenset({"faculty", "admin"})
MAX_REASON = 500
NOT_AUTHORIZED = ("Your account is not authorized to choose this resident's cases. An administrator "
                  "can authorize it.")


def case_options(challenge_id):
    """The authored cases a challenge offers: [(variant_id, family, presentation)]."""
    from clinical_cases import FAMILIES
    from curriculum import CHALLENGES
    challenge = CHALLENGES.get(challenge_id)
    if not challenge:
        return []
    return [(variant["id"], family, variant.get("presentation", ""))
            for family in (challenge.get("families") or ())
            for variant in FAMILIES.get(family, {}).get("variants", [])]


class DirectiveStore:
    """Append-only directives, behind the account store."""

    def __init__(self, account_store):
        self.accounts = account_store
        self._execute = account_store._execute
        if not self.accounts.schema_ready("encounter_directives"):
            with self.accounts._transaction(write=True) as connection:
                self._execute(connection, """CREATE TABLE IF NOT EXISTS mrs_encounter_directives (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL REFERENCES mrs_users(id),
                    challenge_id TEXT NOT NULL,
                    variant_id TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    created_by TEXT NOT NULL REFERENCES mrs_users(id),
                    created_at BIGINT NOT NULL,
                    state TEXT NOT NULL CHECK (state IN ('waiting', 'used', 'cancelled')),
                    attempt_id TEXT,
                    closed_at BIGINT
                )""")
                self._execute(connection, """CREATE INDEX IF NOT EXISTS mrs_encounter_directives_user
                    ON mrs_encounter_directives(user_id, state, created_at)""")
                # Which faculty member may direct which resident's next case. An
                # administrator grants and revokes; nothing is deleted.
                self._execute(connection, """CREATE TABLE IF NOT EXISTS mrs_direction_grants (
                    id TEXT PRIMARY KEY,
                    faculty_id TEXT NOT NULL REFERENCES mrs_users(id),
                    user_id TEXT NOT NULL REFERENCES mrs_users(id),
                    reason TEXT NOT NULL,
                    granted_by TEXT NOT NULL REFERENCES mrs_users(id),
                    granted_at BIGINT NOT NULL,
                    revoked_by TEXT REFERENCES mrs_users(id),
                    revoked_at BIGINT,
                    revoke_reason TEXT
                )""")
                self._execute(connection, """CREATE INDEX IF NOT EXISTS mrs_direction_grants_faculty
                    ON mrs_direction_grants(faculty_id, user_id, revoked_at)""")
            self.accounts.mark_schema_ready("encounter_directives")

    # --- who may direct whom -------------------------------------------------------

    def _authorized(self, connection, actor, user_id):
        if actor["role"] == "admin":
            return True
        if actor["role"] != "faculty":
            return False
        return self._execute(connection, """SELECT id FROM mrs_direction_grants
            WHERE faculty_id = ? AND user_id = ? AND revoked_at IS NULL""",
            (actor["id"], user_id)).fetchone() is not None

    def _scope(self, connection, actor):
        """The residents this staff member may direct: None means every resident."""
        if actor["role"] == "admin":
            return None
        return {row["user_id"] for row in self._execute(connection, """SELECT user_id
            FROM mrs_direction_grants WHERE faculty_id = ? AND revoked_at IS NULL""",
            (actor["id"],)).fetchall()}

    def residents_in_scope(self, token):
        """The residents whose next case this account may choose."""
        with self.accounts._transaction() as connection:
            actor = self.accounts._actor(connection, token, STAFF)
            scope = self._scope(connection, actor)
            rows = self._execute(connection, "SELECT * FROM mrs_users WHERE role = 'resident' "
                                 "ORDER BY username").fetchall()
            return [self.accounts._public_user(row) for row in rows
                    if scope is None or row["id"] in scope]

    def faculty_members(self, token):
        with self.accounts._transaction() as connection:
            self.accounts._actor(connection, token, {"admin"})
            return [self.accounts._public_user(row) for row in self._execute(
                connection, "SELECT * FROM mrs_users WHERE role = 'faculty' ORDER BY username").fetchall()]

    def grant(self, token, faculty_id, user_id, reason):
        """An administrator authorizes one faculty member to direct one resident's cases."""
        reason = str(reason or "").strip()
        if not reason:
            raise AccountError("Say why this faculty member may choose this resident's cases.")
        if len(reason) > MAX_REASON:
            raise AccountError("The reason is too long.")
        with self.accounts._transaction(write=True) as connection:
            actor = self.accounts._actor(connection, token, {"admin"})
            faculty = self._execute(connection, "SELECT id, role FROM mrs_users WHERE id = ?",
                                    (faculty_id,)).fetchone()
            resident = self._execute(connection, "SELECT id, role FROM mrs_users WHERE id = ?",
                                     (user_id,)).fetchone()
            if faculty is None or faculty["role"] != "faculty":
                raise AccountError("Choose a faculty member.")
            if resident is None or resident["role"] != "resident":
                raise AccountError("Choose a resident.")
            existing = self._execute(connection, """SELECT id FROM mrs_direction_grants
                WHERE faculty_id = ? AND user_id = ? AND revoked_at IS NULL""",
                (faculty_id, user_id)).fetchone()
            if existing is not None:
                return {"id": existing["id"], "changed": False}
            identifier = uuid.uuid4().hex
            self._execute(connection, """INSERT INTO mrs_direction_grants
                (id, faculty_id, user_id, reason, granted_by, granted_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (identifier, faculty_id, user_id, reason, actor["id"], int(time.time())))
            return {"id": identifier, "changed": True}

    def revoke(self, token, grant_id, reason):
        reason = str(reason or "").strip()
        if not reason:
            raise AccountError("Say why the authorization is revoked.")
        with self.accounts._transaction(write=True) as connection:
            actor = self.accounts._actor(connection, token, {"admin"})
            updated = self._execute(connection, """UPDATE mrs_direction_grants
                SET revoked_by = ?, revoked_at = ?, revoke_reason = ?
                WHERE id = ? AND revoked_at IS NULL""",
                (actor["id"], int(time.time()), reason[:MAX_REASON], grant_id))
            if getattr(updated, "rowcount", 1) == 0:
                raise AccountError("That authorization is no longer active.")

    def grants(self, token):
        """Every authorization, active and revoked, for the administrator."""
        with self.accounts._transaction() as connection:
            self.accounts._actor(connection, token, {"admin"})
            rows = self._execute(connection, """SELECT g.*, f.username AS faculty, r.username AS resident,
                a.username AS granted_by_name FROM mrs_direction_grants g
                JOIN mrs_users f ON f.id = g.faculty_id JOIN mrs_users r ON r.id = g.user_id
                JOIN mrs_users a ON a.id = g.granted_by ORDER BY g.granted_at""").fetchall()
            return [{"id": row["id"], "faculty": row["faculty"], "resident": row["resident"],
                     "reason": row["reason"], "granted_by": row["granted_by_name"],
                     "granted_at": row["granted_at"], "active": row["revoked_at"] is None,
                     "revoked_at": row["revoked_at"], "revoke_reason": row["revoke_reason"]}
                    for row in rows or []]

    # --- directives -----------------------------------------------------------------

    def direct(self, token, user_id, challenge_id, variant_id, reason):
        """Record the next case for one resident. Returns the directive."""
        reason = str(reason or "").strip()
        if not reason:
            raise AccountError("Say why this resident's next case is being chosen.")
        if len(reason) > MAX_REASON:
            raise AccountError("The reason is too long.")
        if variant_id not in {option[0] for option in case_options(challenge_id)}:
            raise AccountError("That case is not one this challenge offers.")
        with self.accounts._transaction(write=True) as connection:
            actor = self.accounts._actor(connection, token, STAFF)
            row = self._execute(connection, "SELECT id, role FROM mrs_users WHERE id = ?",
                                (user_id,)).fetchone()
            if row is None or row["role"] != "resident":
                raise AccountError("Choose a resident.")
            if not self._authorized(connection, actor, user_id):
                raise AccountError(NOT_AUTHORIZED)
            now = int(time.time())
            self._execute(connection, """UPDATE mrs_encounter_directives SET state = 'cancelled',
                closed_at = ? WHERE user_id = ? AND state = 'waiting'""", (now, user_id))
            identifier = uuid.uuid4().hex
            self._execute(connection, """INSERT INTO mrs_encounter_directives
                (id, user_id, challenge_id, variant_id, reason, created_by, created_at, state)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'waiting')""",
                (identifier, user_id, challenge_id, variant_id, reason, actor["id"], now))
            return {"id": identifier, "user_id": user_id, "challenge_id": challenge_id,
                    "variant_id": variant_id, "reason": reason, "directed_by": actor["username"],
                    "state": "waiting"}

    def cancel(self, token, directive_id):
        with self.accounts._transaction(write=True) as connection:
            actor = self.accounts._actor(connection, token, STAFF)
            row = self._execute(connection, "SELECT user_id FROM mrs_encounter_directives WHERE id = ?",
                                (directive_id,)).fetchone()
            if row is not None and not self._authorized(connection, actor, row["user_id"]):
                raise AccountError(NOT_AUTHORIZED)
            updated = self._execute(connection, """UPDATE mrs_encounter_directives
                SET state = 'cancelled', closed_at = ? WHERE id = ? AND state = 'waiting'""",
                (int(time.time()), directive_id))
            if getattr(updated, "rowcount", 1) == 0:
                raise AccountError("That directive is no longer waiting.")

    def waiting(self, token, user_id=None):
        """The directive waiting for a resident: their own, or any resident's for staff."""
        with self.accounts._transaction() as connection:
            actor = self.accounts._actor(connection, token)
            if actor["role"] not in STAFF:
                user_id = actor["id"]
            elif user_id is None:
                scope = self._scope(connection, actor)
                rows = self._execute(connection, """SELECT d.*, u.username AS directed_by,
                    r.username AS resident FROM mrs_encounter_directives d
                    JOIN mrs_users u ON u.id = d.created_by JOIN mrs_users r ON r.id = d.user_id
                    WHERE d.state = 'waiting' ORDER BY d.created_at""").fetchall()
                return [_row(row) for row in rows or [] if scope is None or row["user_id"] in scope]
            elif not self._authorized(connection, actor, user_id):
                raise AccountError(NOT_AUTHORIZED)
            row = self._execute(connection, """SELECT d.*, u.username AS directed_by,
                r.username AS resident FROM mrs_encounter_directives d
                JOIN mrs_users u ON u.id = d.created_by JOIN mrs_users r ON r.id = d.user_id
                WHERE d.user_id = ? AND d.state = 'waiting' ORDER BY d.created_at DESC""",
                (user_id,)).fetchone()
            return _row(row) if row else None

    def use(self, token, directive_id, attempt_id):
        """The launch that consumed it. Only the resident's own launch uses it."""
        with self.accounts._transaction(write=True) as connection:
            actor = self.accounts._actor(connection, token)
            updated = self._execute(connection, """UPDATE mrs_encounter_directives
                SET state = 'used', attempt_id = ?, closed_at = ?
                WHERE id = ? AND user_id = ? AND state = 'waiting'""",
                (attempt_id, int(time.time()), directive_id, actor["id"]))
            if getattr(updated, "rowcount", 1) == 0:
                raise AccountError("That directive is no longer waiting.")

    def history(self, token, user_id):
        with self.accounts._transaction() as connection:
            actor = self.accounts._actor(connection, token, STAFF)
            if not self._authorized(connection, actor, user_id):
                raise AccountError(NOT_AUTHORIZED)
            rows = self._execute(connection, """SELECT d.*, u.username AS directed_by,
                r.username AS resident FROM mrs_encounter_directives d
                JOIN mrs_users u ON u.id = d.created_by JOIN mrs_users r ON r.id = d.user_id
                WHERE d.user_id = ? ORDER BY d.created_at""", (user_id,)).fetchall()
            return [_row(row) for row in rows or []]


def _row(row):
    return {"id": row["id"], "user_id": row["user_id"], "resident": row["resident"],
            "challenge_id": row["challenge_id"], "variant_id": row["variant_id"],
            "reason": row["reason"], "directed_by": row["directed_by"],
            "created_at": row["created_at"], "state": row["state"],
            "attempt_id": row["attempt_id"], "closed_at": row["closed_at"]}
