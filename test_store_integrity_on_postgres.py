"""Cycle 10's store changes on PostgreSQL, the engine of a deployed pilot (C10-03, C10-04, C10-05).

Runs only when ``MRS_TEST_POSTGRES_URL`` names a throwaway database: every test drops and
recreates its public schema. Without it the tests are skipped; test_store_integrity.py and
test_account_changes_are_audited.py cover the same rules on SQLite.
"""
import logging
import os
import time
import uuid

import pytest

import store_integrity
from account_store import AccountError, AccountStore
from encounter_directives import DirectiveStore

URL = os.environ.get("MRS_TEST_POSTGRES_URL", "")
pytestmark = pytest.mark.skipif(not URL.startswith("postgres"), reason="MRS_TEST_POSTGRES_URL is not set")


def _raw(sql, params=()):
    import psycopg
    with psycopg.connect(URL, autocommit=True) as connection:
        cursor = connection.execute(sql, params)
        return cursor.fetchall() if cursor.description else None


@pytest.fixture
def accounts():
    _raw("DROP SCHEMA public CASCADE")
    _raw("CREATE SCHEMA public")
    AccountStore.forget_schemas()
    return AccountStore(URL)


def _people(accounts):
    users = {}
    with accounts._transaction(write=True) as connection:
        for username, role, year in (("admin_test", "admin", None), ("faculty_test", "faculty", None),
                                     ("resident_test", "resident", 3)):
            user_id = uuid.uuid4().hex
            accounts._execute(connection, "INSERT INTO mrs_users VALUES (?, ?, ?, ?, ?, 1, ?)",
                              (user_id, username, "unused-fixture-hash", role, year, int(time.time())))
            users[username] = {"id": user_id, "token": accounts._new_session(connection, user_id)}
    return users


def test_every_unique_key_is_an_index_of_a_new_database(accounts):
    import image_bank
    import progress_store
    import rubric_store
    rubric_store.RubricStore(accounts)
    progress_store.ProgressStore(accounts)
    image_bank.ImageBank(accounts)
    names = {row[0] for row in _raw("SELECT indexname FROM pg_indexes WHERE schemaname = 'public'")}
    assert set(store_integrity.UNIQUE_KEYS) <= names


def test_an_old_repeat_no_longer_locks_the_store(accounts):
    import progress_store
    progress_store.ProgressStore(accounts)
    users = _people(accounts)
    _raw("DROP INDEX mrs_progress_current_observation")
    now = int(time.time())
    attempt = uuid.uuid4().hex
    _raw("""INSERT INTO mrs_attempts (id, user_id, challenge_id, encounter_json, payload_json, status, is_sandbox,
            created_at, updated_at) VALUES (%s, %s, 'R1-01', '{}', '{}', 'completed', 0, %s, %s)""",
         (attempt, users["resident_test"]["id"], now, now))
    objective = next(iter(__import__("objectives").OBJECTIVES))
    for _ in range(2):
        _raw("""INSERT INTO mrs_progress_observations (id, attempt_id, user_id, objective_id, assessor_id, satisfactory,
                depth, autonomy, context, evidence_json, notes, source_revision, payload_sha, created_at)
                VALUES (%s, %s, %s, %s, %s, 1, 'd', 'a', 'c', '[]', '', 0, 's', %s)""",
             (uuid.uuid4().hex, attempt, users["resident_test"]["id"], objective, users["admin_test"]["id"], now))
    AccountStore.forget_schemas()
    progress_store.ProgressStore(AccountStore(URL))              # opens; the index is left out
    with accounts._transaction() as connection:
        found = store_integrity.repeats(accounts._execute, connection, "mrs_progress_current_observation")
    assert [row["copies"] for row in found] == [2]


def test_the_directive_and_its_encounter_are_one_transaction(accounts):
    users = _people(accounts)
    directives = DirectiveStore(accounts)
    directives.grant(users["admin_test"]["token"], users["faculty_test"]["id"], users["resident_test"]["id"], "Supervises")
    directive_id = directives.direct(users["faculty_test"]["token"], users["resident_test"]["id"], "R2-05",
                                     "gi_bleed_72f", "Test reason")["id"]
    directives.cancel(users["faculty_test"]["token"], directive_id)
    with pytest.raises(AccountError, match="no longer waiting"):
        accounts.create_attempt(users["resident_test"]["token"], "R2-05", {"spec": {}},
                                then=directives.consumer(directive_id))
    assert _raw("SELECT COUNT(*) FROM mrs_attempts")[0][0] == 0
    directive_id = directives.direct(users["faculty_test"]["token"], users["resident_test"]["id"], "R2-05",
                                     "gi_bleed_72f", "Test reason")["id"]
    attempt_id = accounts.create_attempt(users["resident_test"]["token"], "R2-05", {"spec": {}},
                                         then=directives.consumer(directive_id))
    assert _raw("SELECT state, attempt_id FROM mrs_encounter_directives WHERE id = %s", (directive_id,)) == [
        ("used", attempt_id)]


def test_account_changes_are_written_with_author_and_time(accounts):
    users = _people(accounts)
    admin = users["admin_test"]["token"]
    accounts.update_user(admin, users["resident_test"]["id"], active=False)
    accounts.update_user(admin, users["resident_test"]["id"], active=False)
    [change] = accounts.account_changes(admin)
    assert change["changes"] == {"active": [True, False]} and change["changed_by"] == "admin_test"
    with pytest.raises(AccountError):
        accounts.account_changes(users["faculty_test"]["token"])


def test_a_driver_failure_is_logged_by_class_not_by_message(accounts, caplog):
    with caplog.at_level(logging.ERROR, logger="account_store"):
        with pytest.raises(AccountError, match="temporarily unavailable"):
            with accounts._transaction() as connection:
                accounts._execute(connection, "SELECT * FROM a_table_that_does_not_exist_hunter22")
    [record] = [record for record in caplog.records if record.name == "account_store"]
    assert "UndefinedTable" in record.getMessage() and "hunter22" not in record.getMessage()
