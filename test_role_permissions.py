"""Role permissions held by the stores, not only by the page (cycle 9, §154CA–§154CE).

The resident views, the faculty evaluates, the administrator governs. What only the
administrator may do is refused to a faculty token by the store itself, and deactivating
an account ends its use without erasing its record. Synthetic accounts only.
"""
from pathlib import Path
import tempfile
import unittest

from account_store import AccountError, AccountStore, hash_password
from encounter_directives import DirectiveStore, case_options
from progress_store import ProgressStore
from rubric_store import RubricStore

PASSWORD = "Synthetic-test-password-2026!"


class RolePermissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.admin_hash = hash_password(PASSWORD)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = AccountStore("sqlite:///" + str(Path(self.tmp.name) / "accounts.sqlite3"), allow_sqlite=True)
        self.assertTrue(self.store.bootstrap_admin("Teacher", self.admin_hash))
        self.admin = self.store.authenticate("teacher", PASSWORD)
        self.faculty = self.enroll("faculty_member", role="faculty")
        self.resident = self.enroll("resident_one")
        self.resident_id = self.store.get_user(self.resident)["id"]

    def tearDown(self):
        self.tmp.cleanup()

    def enroll(self, username, role="resident", year=1):
        code = self.store.create_invite(self.admin, role, year if role == "resident" else None)
        return self.store.register(username, PASSWORD, code)

    def completed_encounter(self):
        attempt = self.store.create_attempt(self.resident, "R1-03", {"version": "test", "seed": 17})
        self.store.save_attempt(self.resident, attempt, {"evidence": {"note": "synthetic"}}, status="completed")
        return attempt

    def test_a_faculty_member_cannot_govern_accounts_through_the_store(self):
        refused = (
            lambda: self.store.create_invite(self.faculty, "resident", 1),
            lambda: self.store.create_invite(self.faculty, "admin"),
            lambda: self.store.list_users(self.faculty),
            lambda: self.store.update_user(self.faculty, self.resident_id, active=False),
            lambda: self.store.update_user(self.faculty, self.resident_id, active=True),
            lambda: self.store.update_user(self.faculty, self.resident_id, role="faculty"),
            lambda: self.store.update_user(self.faculty, self.resident_id, training_year=3),
        )
        for call in refused:
            with self.assertRaises(AccountError):
                call()
        user = self.store.get_user(self.resident)
        self.assertEqual((user["role"], user["training_year"], user["active"]), ("resident", 1, True))

    def test_a_resident_cannot_govern_accounts_either(self):
        for call in (lambda: self.store.list_users(self.resident),
                     lambda: self.store.update_user(self.resident, self.resident_id, training_year=3)):
            with self.assertRaises(AccountError):
                call()

    def test_deactivation_ends_use_keeps_the_record_and_reactivation_returns_it(self):
        attempt = self.completed_encounter()
        progress = ProgressStore(self.store)
        before = progress.get_progress(self.faculty, self.resident_id)
        self.store.update_user(self.admin, self.resident_id, active=False)
        # The account cannot be used: its session ended and it cannot sign in.
        self.assertIsNone(self.store.get_user(self.resident))
        with self.assertRaises(AccountError):
            self.store.list_attempts(self.resident)
        with self.assertRaises(AccountError):
            self.store.authenticate("resident_one", PASSWORD)
        # Its record stays, and faculty and the administrator still read it.
        for reader in (self.faculty, self.admin):
            self.assertEqual(self.store.get_attempt(reader, attempt)["id"], attempt)
            self.assertEqual(progress.get_progress(reader, self.resident_id)["objectives"], before["objectives"])
            self.assertEqual(RubricStore(self.store).progress(reader, self.resident_id), [])
        [listed] = [row for row in progress.list_residents(self.faculty) if row["id"] == self.resident_id]
        self.assertFalse(listed["active"])
        # Reactivated, the same account returns to the same record; nothing is duplicated.
        self.store.update_user(self.admin, self.resident_id, active=True)
        token = self.store.authenticate("resident_one", PASSWORD)
        self.assertEqual(self.store.get_user(token)["id"], self.resident_id)
        self.assertEqual([row["id"] for row in self.store.list_attempts(token)], [attempt])
        self.assertEqual([row["username"] for row in self.store.list_users(self.admin)].count("resident_one"), 1)

    def test_an_inactive_resident_is_neither_offered_nor_given_a_new_case(self):
        directives = DirectiveStore(self.store)
        variant = case_options("R2-05")[0][0]
        self.assertIn(self.resident_id, [row["id"] for row in directives.residents_in_scope(self.admin)])
        self.store.update_user(self.admin, self.resident_id, active=False)
        self.assertNotIn(self.resident_id, [row["id"] for row in directives.residents_in_scope(self.admin)])
        with self.assertRaisesRegex(AccountError, "inactive"):
            directives.direct(self.admin, self.resident_id, "R2-05", variant, "Program choice")
        self.store.update_user(self.admin, self.resident_id, active=True)
        self.assertEqual(directives.direct(self.admin, self.resident_id, "R2-05", variant, "Program choice")["state"],
                         "waiting")

    def test_a_resident_reads_only_their_own_and_cannot_write_evidence(self):
        other = self.enroll("resident_two")
        other_id = self.store.get_user(other)["id"]
        progress = ProgressStore(self.store)
        with self.assertRaises(AccountError):
            progress.get_progress(self.resident, other_id)
        with self.assertRaises(AccountError):
            RubricStore(self.store).progress(self.resident, other_id)
        with self.assertRaises(AccountError):
            progress.list_residents(self.resident)
        attempt = self.completed_encounter()
        # Another resident's encounter is simply not there for them.
        self.assertIsNone(self.store.get_attempt(other, attempt))
        self.assertEqual(self.store.list_attempts(other), [])


if __name__ == "__main__":
    unittest.main()
