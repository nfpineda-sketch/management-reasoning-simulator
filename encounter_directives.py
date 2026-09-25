"""A faculty member chooses a resident's next case, and says why.

Until 2026-09-24 a resident's next encounter was always the curriculum's
choice: the challenge from the assignment rule, and the case from that
challenge's families (generated, or drawn from the bank). Nothing let a faculty
member say "this resident's next case is this one". The synthetic batch of
twenty scenarios needed exactly that -- twenty chosen, tested cases, played by
a real resident account through the real circuit -- and so does a teacher who
wants a resident to meet a particular patient.

A directive is one-shot, explicit and on the record:

* a faculty member or an administrator names the resident, the challenge and
  one authored case that challenge offers, with a written reason;
* the resident's next launch uses it and consumes it; the assignment records
  that it was directed, by whom and why;
* a new directive for the same resident replaces the one waiting, and the
  replaced one stays in the history as cancelled. Nothing is deleted.

Without a directive, the curriculum's rule is exactly what it was.
"""
from __future__ import annotations

import time
import uuid

from account_store import AccountError

STAFF = frozenset({"faculty", "admin"})
MAX_REASON = 500


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
            self.accounts._actor(connection, token, STAFF)
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
                rows = self._execute(connection, """SELECT d.*, u.username AS directed_by,
                    r.username AS resident FROM mrs_encounter_directives d
                    JOIN mrs_users u ON u.id = d.created_by JOIN mrs_users r ON r.id = d.user_id
                    WHERE d.state = 'waiting' ORDER BY d.created_at""").fetchall()
                return [_row(row) for row in rows or []]
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
            self.accounts._actor(connection, token, STAFF)
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
