"""Security, recovery and concurrency checks for account persistence.

Run: python -m unittest test_account_store -v
All credentials below are synthetic test data, never production credentials.
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sqlite3
import tempfile
import time
import unittest
from unittest.mock import patch

from account_store import AccountError, AccountStore, hash_password


PASSWORD = "Synthetic-test-password-2026!"


class AccountStoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.admin_hash = hash_password(PASSWORD)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "accounts.sqlite3"
        self.url = "sqlite:///" + str(self.path)
        self.store = AccountStore(self.url, allow_sqlite=True)
        self.assertTrue(self.store.bootstrap_admin("Teacher", self.admin_hash))
        self.admin = self.store.authenticate("teacher", PASSWORD)

    def tearDown(self):
        self.tmp.cleanup()

    def enroll(self, username="resident", role="resident", year=1):
        code = self.store.create_invite(self.admin, role, year if role == "resident" else None)
        return self.store.register(username, PASSWORD, code)

    def attempt(self, token, challenge="R1-03"):
        return self.store.create_attempt(token, challenge, {"version": "test", "seed": 17})

    def test_sqlite_requires_explicit_local_mode(self):
        with self.assertRaisesRegex(AccountError, "local development"):
            AccountStore(self.url)
        with self.assertRaisesRegex(AccountError, "absolute"):
            AccountStore("sqlite:///relative.sqlite3", allow_sqlite=True)
        with self.assertRaisesRegex(AccountError, "PostgreSQL"):
            AccountStore("https://example.com")

    def test_hashes_and_tokens_are_not_stored_in_cleartext(self):
        token = self.enroll()
        with sqlite3.connect(self.path) as connection:
            encoded = connection.execute("SELECT password_hash FROM mrs_users WHERE username = 'resident'").fetchone()[0]
            hashes = [row[0] for row in connection.execute("SELECT token_hash FROM mrs_sessions")]
        self.assertNotIn(PASSWORD, encoded)
        self.assertNotEqual(encoded, self.admin_hash)
        self.assertNotIn(token, hashes)
        self.assertTrue(all(len(value) == 64 for value in hashes))
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)

    def test_individual_identity_persists_across_store_instances(self):
        token = self.enroll("Student.One@Example.edu", year=2)
        attempt_id = self.attempt(token, "R2-01")
        self.assertEqual(self.store.save_attempt(token, attempt_id, {"trace": [{"action": "observe"}]}, expected_revision=0), 1)
        reopened = AccountStore(self.url, allow_sqlite=True)
        user = reopened.get_user(token)
        self.assertEqual(user["username"], "student.one@example.edu")
        self.assertEqual(user["training_year"], 2)
        self.assertEqual(reopened.get_attempt(token, attempt_id)["payload"]["trace"][0]["action"], "observe")
        self.assertNotIn("password_hash", user)

    def test_invitation_single_use_and_failed_registration_does_not_consume_it(self):
        code = self.store.create_invite(self.admin, "resident", 1)
        with self.assertRaises(AccountError):
            self.store.register("teacher", PASSWORD, code)
        token = self.store.register("student", PASSWORD, code)
        self.assertEqual(self.store.get_user(token)["role"], "resident")
        with self.assertRaisesRegex(AccountError, "already used"):
            self.store.register("second-student", PASSWORD, code)

    def test_invite_consumption_is_atomic_between_workers(self):
        code = self.store.create_invite(self.admin, "resident", 1)
        def register(name):
            try:
                return AccountStore(self.url, allow_sqlite=True).register(name, PASSWORD, code)
            except AccountError:
                return None
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(register, ("student-one", "student-two")))
        self.assertEqual(sum(result is not None for result in results), 1)
        self.assertEqual(len(self.store.list_users(self.admin)), 2)

    def test_invites_expire_and_roles_cannot_be_self_assigned(self):
        resident = self.enroll()
        resident_id = self.store.get_user(resident)["id"]
        for call in (
            lambda: self.store.create_invite(resident, "admin"),
            lambda: self.store.update_user(resident, resident_id, role="admin"),
            lambda: self.store.list_users(resident),
        ):
            with self.assertRaisesRegex(AccountError, "permission"):
                call()
        code = self.store.create_invite(self.admin, "resident", 1)
        with patch("account_store.time.time", return_value=time.time() + 8 * 86400):
            with self.assertRaisesRegex(AccountError, "expired"):
                self.store.register("expired", PASSWORD, code)

    def test_resident_record_isolation_and_staff_sandbox_is_enforced(self):
        first, second, faculty = self.enroll("first"), self.enroll("second"), self.enroll("faculty", "faculty")
        first_id, second_id, faculty_id = self.attempt(first), self.attempt(second), self.attempt(faculty)
        self.assertIsNone(self.store.get_attempt(first, second_id))
        self.assertEqual([row["id"] for row in self.store.list_attempts(first)], [first_id])
        self.assertEqual(len(self.store.list_attempts(faculty)), 3)
        self.assertTrue(self.store.get_attempt(faculty, faculty_id)["is_sandbox"])
        self.assertFalse(self.store.get_attempt(first, first_id)["is_sandbox"])
        for token in (second, faculty, self.admin):
            with self.assertRaises(AccountError):
                self.store.save_attempt(token, first_id, {"tampered": True}, expected_revision=0)
        with self.assertRaises(AccountError):
            self.store.create_attempt(first, "R1-03", {}, is_sandbox=True)
        with self.assertRaises(AccountError):
            self.attempt(first, "R2-01")

    def test_one_active_resident_attempt_resumes_frozen_encounter(self):
        resident = self.enroll()
        attempt_id = self.attempt(resident)
        self.assertEqual(self.store.create_attempt(resident, "R1-04", {"seed": 999}), attempt_id)
        record = self.store.get_attempt(resident, attempt_id)
        self.assertEqual(record["encounter"]["seed"], 17)
        self.assertEqual(record["challenge_id"], "R1-03")
        self.store.save_attempt(resident, attempt_id, {"trace": []}, "completed", expected_revision=0)
        self.assertNotEqual(self.attempt(resident), attempt_id)
        with self.assertRaisesRegex(AccountError, "cannot be reopened"):
            self.store.save_attempt(resident, attempt_id, {}, "active", expected_revision=1)

    def test_optimistic_revision_rejects_stale_tabs_without_losing_evidence(self):
        resident = self.enroll()
        attempt_id = self.attempt(resident)
        self.assertEqual(self.store.get_attempt(resident, attempt_id)["revision"], 0)
        self.assertEqual(self.store.save_attempt(resident, attempt_id, {"trace": ["first"]}, expected_revision=0), 1)
        with self.assertRaisesRegex(AccountError, "another session"):
            self.store.save_attempt(resident, attempt_id, {"trace": ["stale"]}, expected_revision=0)
        record = self.store.get_attempt(resident, attempt_id)
        self.assertEqual(record["revision"], 1)
        self.assertEqual(record["payload"]["trace"], ["first"])

    def test_logout_expiry_and_role_changes_revoke_access(self):
        resident = self.enroll()
        self.store.revoke_session(resident)
        self.assertIsNone(self.store.get_user(resident))
        resident = self.store.authenticate("resident", PASSWORD)
        with patch("account_store.time.time", return_value=time.time() + 13 * 3600):
            self.assertIsNone(self.store.get_user(resident))
        user_id = self.store.get_user(resident)["id"]
        self.store.update_user(self.admin, user_id, training_year=2)
        self.assertIsNone(self.store.get_user(resident))
        fresh = self.store.authenticate("resident", PASSWORD)
        self.assertEqual(self.store.get_user(fresh)["training_year"], 2)
        self.store.update_user(self.admin, user_id, active=False)
        self.assertIsNone(self.store.get_user(fresh))
        with self.assertRaises(AccountError):
            self.store.authenticate("resident", PASSWORD)

    def test_last_admin_protection_and_bootstrap_never_resets_existing_account(self):
        user = self.store.get_user(self.admin)
        with self.assertRaisesRegex(AccountError, "at least one"):
            self.store.update_user(self.admin, user["id"], active=False)
        self.assertFalse(self.store.bootstrap_admin("another-admin", self.admin_hash))
        self.assertEqual(len(self.store.list_users(self.admin)), 1)
        new_admin = self.enroll("second-admin", "admin")
        self.store.update_user(new_admin, user["id"], role="faculty")
        self.assertIsNone(self.store.get_user(self.admin))

    def test_login_throttle_is_persisted_and_expires(self):
        resident = self.enroll()
        for _ in range(5):
            with self.assertRaisesRegex(AccountError, "incorrect"):
                self.store.authenticate("resident", "incorrect-password")
        reopened = AccountStore(self.url, allow_sqlite=True)
        with self.assertRaisesRegex(AccountError, "Too many"):
            reopened.authenticate("resident", PASSWORD)
        with patch("account_store.time.time", return_value=time.time() + 901):
            token = reopened.authenticate("resident", PASSWORD)
            self.assertIsNotNone(reopened.get_user(token))
        self.assertIsNotNone(self.store.get_user(resident))

    def test_password_change_revokes_all_old_sessions(self):
        first = self.enroll()
        second = self.store.authenticate("resident", PASSWORD)
        token = self.store.change_password(first, PASSWORD, "Another-synthetic-password!")
        self.assertIsNone(self.store.get_user(first))
        self.assertIsNone(self.store.get_user(second))
        self.assertIsNotNone(self.store.get_user(token))
        with self.assertRaises(AccountError):
            self.store.authenticate("resident", PASSWORD)

    def test_invalid_payload_and_sql_looking_values_do_not_modify_schema(self):
        resident = self.enroll()
        attempt_id = self.attempt(resident)
        with self.assertRaises(AccountError):
            self.store.save_attempt(resident, attempt_id, {"nan": float("nan")})
        with self.assertRaises(AccountError):
            self.store.register("'; DROP TABLE mrs_users; --", PASSWORD, "fake")
        self.assertIsNone(self.store.get_attempt(resident, "' OR 1=1 --"))
        self.assertEqual(len(self.store.list_users(self.admin)), 2)


if __name__ == "__main__":
    unittest.main()
