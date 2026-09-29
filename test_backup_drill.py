"""The backup drill's comparison sees every row, and only the rows (cycle 10, C10-05).

The full drill -- the smoke run, the backup, the restore and reading every encounter back -- was
run on SQLite and on a local, throwaway PostgreSQL 16 (docs/RESPALDO_Y_RESTAURACION.md); it takes
minutes, so the suite checks the parts it rests on.
"""
import shutil
import sqlite3
import time
import uuid

import tools_backup_drill as drill
from account_store import AccountStore


def _database(tmp_path, name="source.sqlite3"):
    AccountStore.forget_schemas()
    path = tmp_path / name
    store = AccountStore(f"sqlite:///{path}", allow_sqlite=True)
    with store._transaction(write=True) as connection:
        for username in ("drill_one", "drill_two"):
            user_id = uuid.uuid4().hex
            store._execute(connection, "INSERT INTO mrs_users VALUES (?, ?, 'x', 'resident', 1, 1, ?)",
                           (user_id, username, int(time.time())))
            store._new_session(connection, user_id)
    return path


def test_a_backup_restored_is_identical_and_a_changed_cell_is_not(tmp_path):
    source = _database(tmp_path)
    copy = tmp_path / "restored.sqlite3"
    with sqlite3.connect(source) as live, sqlite3.connect(copy) as backup:
        live.backup(backup)
    report = drill.compare(f"sqlite:///{source}", f"sqlite:///{copy}")
    assert report["passed"] and report["tables"]["mrs_users"] == {
        "source_rows": 2, "restored_rows": 2, "identical": True}
    with sqlite3.connect(copy) as connection:
        connection.execute("UPDATE mrs_users SET training_year = 2 WHERE username = 'drill_two'")
    report = drill.compare(f"sqlite:///{source}", f"sqlite:///{copy}")
    assert not report["passed"] and not report["tables"]["mrs_users"]["identical"]


def test_sessions_are_left_out_and_nothing_is_printed_but_counts_and_hashes(tmp_path, capsys):
    source = _database(tmp_path)
    fingerprint = drill.fingerprint(f"sqlite:///{source}")
    assert "mrs_sessions" not in fingerprint and fingerprint["mrs_users"]["rows"] == 2
    shutil.copyfile(source, tmp_path / "copy.sqlite3")
    assert drill.main(["--compare", f"sqlite:///{source}", f"sqlite:///{tmp_path / 'copy.sqlite3'}"]) == 0
    assert "drill_one" not in capsys.readouterr().out
