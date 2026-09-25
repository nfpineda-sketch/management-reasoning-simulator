"""A faculty member's clinical review of one catalogue configuration, at one version.

"Clinically reviewed" is the one state of a configuration that no test can
produce (case_catalog). It exists only as a recorded action of an identified
faculty member or administrator, and it refers to the configuration's
fingerprint at that moment: its conditions, rules, parameters, cues, narrative
and evaluation. When any of those changes, the review stands as *outdated*
until someone reviews it again -- unless the corrections registry declares
that exact change cosmetic.

Nothing here records a review on anyone's behalf, and nothing turns a passing
battery into a review. Append-only: a new review is a new row, and the old one
stays in the history.
"""
from __future__ import annotations

import json
import time
import uuid

from account_store import AccountError

STAFF = frozenset({"faculty", "admin"})
MAX_NOTE = 1200


class CatalogReviewStore:
    def __init__(self, account_store):
        self.accounts = account_store
        self._execute = account_store._execute
        with self.accounts._transaction(write=True) as connection:
            self._execute(connection, """CREATE TABLE IF NOT EXISTS mrs_catalog_reviews (
                id TEXT PRIMARY KEY,
                configuration_id TEXT NOT NULL,
                catalog_version TEXT NOT NULL,
                fingerprint_json TEXT NOT NULL,
                decision TEXT NOT NULL CHECK (decision IN ('approved', 'changes_requested', 'rejected')),
                note TEXT NOT NULL,
                reviewer_user_id TEXT NOT NULL REFERENCES mrs_users(id),
                reviewer_role TEXT NOT NULL,
                created_at BIGINT NOT NULL
            )""")
            self._execute(connection, """CREATE INDEX IF NOT EXISTS mrs_catalog_reviews_configuration
                ON mrs_catalog_reviews(configuration_id, created_at)""")

    def record(self, token, configuration_id, decision, note):
        """One review, by the signed-in faculty member, of the configuration as it is now."""
        import case_catalog
        import hypoglycemia_catalog
        if decision not in case_catalog.REVIEW_DECISIONS:
            raise AccountError("A review approves, asks for changes, or rejects.")
        note = str(note or "").strip()
        if not note:
            raise AccountError("A clinical review needs a written note: what was reviewed and why.")
        if len(note) > MAX_NOTE:
            raise AccountError("The review note is too long.")
        try:
            configuration = hypoglycemia_catalog.configuration(configuration_id)
        except ValueError:
            raise AccountError("That configuration is not in the catalogue.") from None
        fingerprint = hypoglycemia_catalog.fingerprint(configuration)
        with self.accounts._transaction(write=True) as connection:
            actor = self.accounts._actor(connection, token, STAFF)
            identifier = uuid.uuid4().hex
            now = int(time.time())
            self._execute(connection, """INSERT INTO mrs_catalog_reviews
                (id, configuration_id, catalog_version, fingerprint_json, decision, note, reviewer_user_id,
                 reviewer_role, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (identifier, configuration_id, fingerprint["catalog_version"],
                 json.dumps(fingerprint, sort_keys=True), decision, note, actor["id"], actor["role"], now))
            return {"id": identifier, "configuration_id": configuration_id, "decision": decision, "note": note,
                    "fingerprint": fingerprint, "reviewer": {"username": actor["username"], "role": actor["role"]},
                    "created_at": now}

    def reviews(self, token, configuration_id=None):
        """Every recorded review, oldest first, with who made it."""
        with self.accounts._transaction() as connection:
            self.accounts._actor(connection, token, STAFF)
            query = """SELECT r.*, u.username FROM mrs_catalog_reviews r
                JOIN mrs_users u ON u.id = r.reviewer_user_id"""
            parameters = ()
            if configuration_id:
                query += " WHERE r.configuration_id = ?"
                parameters = (configuration_id,)
            rows = self._execute(connection, query + " ORDER BY r.created_at, r.id", parameters).fetchall()
        return [{"id": row["id"], "configuration_id": row["configuration_id"],
                 "catalog_version": row["catalog_version"], "fingerprint": json.loads(row["fingerprint_json"]),
                 "decision": row["decision"], "note": row["note"],
                 "reviewer": {"username": row["username"], "role": row["reviewer_role"]},
                 "created_at": row["created_at"]} for row in rows]

    def statuses(self, token):
        """Where each configuration's clinical review stands against the code as it is now."""
        import case_catalog
        import corrections_registry
        import hypoglycemia_catalog
        reviews = self.reviews(token)
        waivers = corrections_registry.cosmetic_waivers()
        rows = []
        for configuration in hypoglycemia_catalog.configurations():
            current = hypoglycemia_catalog.current_fingerprint(configuration["id"])
            status = case_catalog.review_status(configuration["id"], current, reviews, waivers)
            rows.append({"configuration_id": configuration["id"], "origin": configuration["origin"],
                         "axes": dict(configuration["axes"]), "fingerprint": current["whole"],
                         "compatible": hypoglycemia_catalog.current_compatibility(configuration["id"])["compatible"],
                         **status})
        return rows
