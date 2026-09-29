"""The stores keep their histories whole (cycle 10, C10-03: TD-18 without I-F18).

I-F09: an encounter launched on a faculty directive and the directive's use are one transaction.
I-F10: a failure inside a transaction is logged by its class and place, never by its message.
I-F06: the numbered histories have unique indexes; a database with older repeats still opens.
I-F19: a duplicate current observation from an older version no longer locks the progress store.
I-F20: a corrupt JSON column is one row's problem, said on that row.
"""
import logging
import sqlite3
import time
import uuid

import pytest

import check_database
import store_integrity
from account_store import AccountError, AccountStore
from encounter_directives import DirectiveStore


def _store(tmp_path):
    AccountStore.forget_schemas()
    return AccountStore(f"sqlite:///{tmp_path / 'accounts.sqlite3'}", allow_sqlite=True)


@pytest.fixture
def cohort(tmp_path):
    accounts = _store(tmp_path)
    users = {}
    with accounts._transaction(write=True) as connection:
        for username, role, year in (("faculty_test", "faculty", None), ("admin_test", "admin", None),
                                     ("resident_test", "resident", 3)):
            user_id = uuid.uuid4().hex
            accounts._execute(connection, "INSERT INTO mrs_users VALUES (?, ?, ?, ?, ?, 1, ?)",
                              (user_id, username, "unused-fixture-hash", role, year, int(time.time())))
            users[username] = {"id": user_id, "token": accounts._new_session(connection, user_id)}
    directives = DirectiveStore(accounts)
    directives.grant(users["admin_test"]["token"], users["faculty_test"]["id"], users["resident_test"]["id"],
                     "Supervises this resident")
    return accounts, users, directives


def _direct(users, directives):
    return directives.direct(users["faculty_test"]["token"], users["resident_test"]["id"], "R2-05",
                             "gi_bleed_72f", "Test reason")["id"]


def _attempts(accounts, user_id):
    with accounts._transaction() as connection:
        return [row["id"] for row in accounts._execute(
            connection, "SELECT id FROM mrs_attempts WHERE user_id = ?", (user_id,)).fetchall()]


# --- I-F09 ------------------------------------------------------------------------------

def test_the_launch_writes_the_encounter_and_uses_the_directive_together(cohort):
    accounts, users, directives = cohort
    directive_id = _direct(users, directives)
    token = users["resident_test"]["token"]
    attempt_id = accounts.create_attempt(token, "R2-05", {"spec": {}}, then=directives.consumer(directive_id))
    [row] = directives.history(users["admin_test"]["token"], users["resident_test"]["id"])
    assert (row["state"], row["attempt_id"]) == ("used", attempt_id)
    assert _attempts(accounts, users["resident_test"]["id"]) == [attempt_id]


def test_a_directive_no_longer_waiting_writes_no_encounter(cohort):
    accounts, users, directives = cohort
    directive_id = _direct(users, directives)
    directives.cancel(users["faculty_test"]["token"], directive_id)
    with pytest.raises(AccountError, match="no longer waiting"):
        accounts.create_attempt(users["resident_test"]["token"], "R2-05", {"spec": {}},
                                then=directives.consumer(directive_id))
    assert _attempts(accounts, users["resident_test"]["id"]) == []


def test_an_active_encounter_is_returned_and_the_directive_keeps_waiting(cohort):
    accounts, users, directives = cohort
    token = users["resident_test"]["token"]
    active = accounts.create_attempt(token, "R2-05", {"spec": {}})
    directive_id = _direct(users, directives)
    assert accounts.create_attempt(token, "R2-05", {"spec": {}}, then=directives.consumer(directive_id)) == active
    assert directives.waiting(token)["id"] == directive_id


# --- I-F10 ------------------------------------------------------------------------------

def test_a_failure_is_logged_by_class_and_place_never_by_its_message(tmp_path, caplog):
    accounts = _store(tmp_path)
    secret = "postgresql://someone:hunter22@db.example.org/pilot"
    with caplog.at_level(logging.ERROR, logger="account_store"):
        with pytest.raises(AccountError, match="temporarily unavailable"):
            with accounts._transaction():
                raise KeyError(secret)
    [record] = [record for record in caplog.records if record.name == "account_store"]
    logged = record.getMessage()
    assert "KeyError" in logged and "test_store_integrity.py:" in logged
    assert "hunter22" not in logged and "db.example.org" not in logged
    assert record.exc_info is None


def test_a_refusal_is_not_logged_as_a_failure(tmp_path, caplog):
    accounts = _store(tmp_path)
    with caplog.at_level(logging.ERROR, logger="account_store"):
        with pytest.raises(AccountError, match="plain refusal"):
            with accounts._transaction():
                raise AccountError("plain refusal")
    assert not [record for record in caplog.records if record.name == "account_store"]


# --- I-F06 and I-F19 --------------------------------------------------------------------

def _indexes(path):
    with sqlite3.connect(path) as connection:
        return {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'index'")}


def test_every_unique_key_is_an_index_of_a_new_database(tmp_path):
    accounts = _store(tmp_path)
    import image_bank
    import progress_store
    import rubric_store
    rubric_store.RubricStore(accounts)
    progress_store.ProgressStore(accounts)
    image_bank.ImageBank(accounts)
    assert set(store_integrity.UNIQUE_KEYS) <= _indexes(tmp_path / "accounts.sqlite3")


def _old_database_with_a_repeated_observation(tmp_path):
    """What an older version could leave: two current observations of one objective of one encounter."""
    import progress_store
    accounts = _store(tmp_path)
    store = progress_store.ProgressStore(accounts)
    path = tmp_path / "accounts.sqlite3"
    now = int(time.time())
    with sqlite3.connect(path) as connection:
        connection.execute("DROP INDEX mrs_progress_current_observation")
        user = uuid.uuid4().hex
        connection.execute("INSERT INTO mrs_users VALUES (?, 'resident_old', 'x', 'resident', 1, 1, ?)", (user, now))
        attempt = uuid.uuid4().hex
        connection.execute("""INSERT INTO mrs_attempts (id, user_id, challenge_id, encounter_json, payload_json,
            status, is_sandbox, created_at, updated_at) VALUES (?, ?, 'R1-01', '{}', '{}', 'completed', 0, ?, ?)""",
                           (attempt, user, now, now))
        objective = next(iter(__import__("objectives").OBJECTIVES))
        for evidence, provenance in (('[]', None), ('{not json', '{also not json')):
            connection.execute("""INSERT INTO mrs_progress_observations (id, attempt_id, user_id, objective_id,
                assessor_id, satisfactory, depth, autonomy, context, evidence_json, notes, source_revision,
                payload_sha, created_at, provenance_json) VALUES (?, ?, ?, ?, ?, 1, 'd', 'a', 'c', ?, '', 0, 's', ?, ?)""",
                               (uuid.uuid4().hex, attempt, user, objective, user, evidence, now, provenance))
    return accounts, store, path, user, objective


def test_an_old_repeat_no_longer_locks_the_store_and_is_reported(tmp_path, capsys, monkeypatch):
    accounts, _, path, user, objective = _old_database_with_a_repeated_observation(tmp_path)
    import progress_store
    AccountStore.forget_schemas()
    reopened = progress_store.ProgressStore(accounts)            # before cycle 10 this raised
    assert "mrs_progress_current_observation" not in _indexes(path)
    with accounts._transaction() as connection:
        found = store_integrity.repeats(accounts._execute, connection, "mrs_progress_current_observation")
    assert [row["copies"] for row in found] == [2] and found[0]["objective_id"] == objective
    assert reopened is not None
    assert check_database.report_integrity(f"sqlite:///{path}") == 2
    printed = capsys.readouterr().out
    assert "mrs_progress_observations" in printed and "2 copies" in printed and "resident_old" not in printed


def test_a_corrupt_column_is_said_on_its_row_and_the_page_still_reads(tmp_path):
    accounts, store, path, user, objective = _old_database_with_a_repeated_observation(tmp_path)
    with accounts._transaction(write=True) as connection:
        admin = uuid.uuid4().hex
        accounts._execute(connection, "INSERT INTO mrs_users VALUES (?, 'admin_new', 'x', 'admin', NULL, 1, ?)",
                          (admin, int(time.time())))
        token = accounts._new_session(connection, admin)
    progress = store.get_progress(token, user)
    goal = next(goal for goal in progress["objectives"] if goal["objective_id"] == objective)
    unreadable = [item for item in goal["observations"] if item.get("unreadable")]
    assert len(goal["observations"]) == 2 and len(unreadable) == 1
    assert unreadable[0]["unreadable"] == ["evidence", "provenance"]
    assert unreadable[0]["evidence"] == [] and unreadable[0]["provenance"] is None
    assert unreadable[0]["satisfactory"] is True


def test_decode_reads_what_it_can_and_names_the_row_when_it_cannot(caplog):
    assert store_integrity.decode('{"a": 1}', None, table="t", row_id="r1", column="c") == ({"a": 1}, True)
    assert store_integrity.decode(None, [], table="t", row_id="r1", column="c") == ([], True)
    with caplog.at_level(logging.WARNING, logger="store_integrity"):
        assert store_integrity.decode("{broken secret", [], table="t", row_id="r2", column="c") == ([], False)
    assert "r2" in caplog.text and "secret" not in caplog.text
