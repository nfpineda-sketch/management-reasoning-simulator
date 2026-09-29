"""Back up a pilot database and restore it, and prove nothing was lost (cycle 10, C10-05).

The drill never touches real data. It fills a throwaway database with what the pilot writes --
the smoke test's accounts, encounters, Trace, faculty rubric, a faculty directive and an account
change -- then:

1. takes a fingerprint of every ``mrs_*`` table: its row count and a hash of its rows;
2. backs the database up the way docs/RUNBOOK_PILOTO.md says: SQLite's online backup, or
   ``pg_dump --format=custom`` for PostgreSQL;
3. restores the backup into a second, empty database (a new SQLite file, or ``pg_restore`` into
   a new PostgreSQL database);
4. compares the fingerprints, table by table;
5. opens the restored database with the application's own stores and reads every encounter
   back, comparing it with the original; then checks that opening it changed no row.

    python3 tools_backup_drill.py --sqlite [--out report.json]
    python3 tools_backup_drill.py --postgres postgresql://user@host:port/empty_db [--out report.json]
    python3 tools_backup_drill.py --compare SOURCE_URL RESTORED_URL

``--compare`` checks a real restore: it only reads both databases and prints, per table, the row
counts and whether the rows are identical -- never their content.

The PostgreSQL URL must name an empty, throwaway database on a server where this user may
create databases: the restore goes into ``<name>_restored``, created and left for inspection.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def _tables(store, connection):
    # Filtered here, not with LIKE 'mrs_%': the PostgreSQL driver reads a bare % as a placeholder.
    if store._sqlite:
        names = [row["name"] for row in store._execute(
            connection, "SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()]
    else:
        names = [row["table_name"] for row in store._execute(
            connection, "SELECT table_name FROM information_schema.tables WHERE table_schema = current_schema()"
        ).fetchall()]
    return sorted(name for name in names if name.startswith("mrs_"))


def _cell(value):
    if isinstance(value, memoryview):
        value = value.tobytes()
    if isinstance(value, (bytes, bytearray)):
        return {"bytes": hashlib.sha256(bytes(value)).hexdigest()}
    if isinstance(value, bool):
        return int(value)
    return value


def fingerprint(url, skip=("mrs_sessions",)):
    """{table: {"rows": n, "sha256": hash of the rows in a fixed order}} for every mrs_* table."""
    from account_store import AccountStore
    store = AccountStore(url, allow_sqlite=url.startswith("sqlite:"))
    result = {}
    with store._transaction() as connection:
        for table in _tables(store, connection):
            if table in skip:
                continue
            rows = [json.dumps({key: _cell(row[key]) for key in row.keys()}, sort_keys=True, default=str)
                    for row in store._execute(connection, f"SELECT * FROM {table}").fetchall()]
            rows.sort()
            result[table] = {"rows": len(rows), "sha256": hashlib.sha256("\n".join(rows).encode()).hexdigest()}
    return result


def _populate(url):
    """What the pilot writes, through the application: the smoke run plus a directive and an account change."""
    import tools_pilot_smoke
    report = tools_pilot_smoke.run("pilot", url=url)
    from account_store import AccountStore
    from encounter_directives import DirectiveStore
    store = AccountStore(url, allow_sqlite=url.startswith("sqlite:"))
    with store._transaction(write=True) as connection:
        rows = {row["username"]: row["id"] for row in store._execute(
            connection, "SELECT id, username FROM mrs_users").fetchall()}
        admin = store._new_session(connection, rows["smoke_admin"])
        faculty = store._new_session(connection, rows["smoke_faculty"])
    directives = DirectiveStore(store)
    directives.grant(admin, rows["smoke_faculty"], rows["smoke_resident_es"], "Backup drill")
    directives.direct(faculty, rows["smoke_resident_es"], "R2-05", "gi_bleed_72f", "Backup drill")
    store.update_user(admin, rows["smoke_resident_es"], active=False)
    return {"encounters": sorted(report.get("encounters", {})), "provider_attempts": report.get("provider_attempts")}


def _encounters(url):
    """Every encounter as the application reads it, through a fresh administrator session."""
    from account_store import AccountStore
    AccountStore.forget_schemas()
    store = AccountStore(url, allow_sqlite=url.startswith("sqlite:"))
    with store._transaction(write=True) as connection:
        admin = store._execute(connection, "SELECT id FROM mrs_users WHERE username = 'smoke_admin'").fetchone()
        token = store._new_session(connection, admin["id"])
    import image_bank
    import progress_store
    import rubric_store
    rubric_store.RubricStore(store)
    progress_store.ProgressStore(store)
    image_bank.ImageBank(store)
    attempts = {}
    for attempt in store.list_attempts(token):
        record = store.get_attempt(token, attempt["id"])
        attempts[attempt["id"]] = hashlib.sha256(json.dumps(record, sort_keys=True, default=str).encode()).hexdigest()
    return attempts, store.account_changes(token)


def _sqlite_drill(directory):
    source = directory / "pilot.sqlite3"
    backup = directory / "pilot.backup.sqlite3"
    restored = directory / "pilot.restored.sqlite3"
    url = f"sqlite:///{source}"
    populated = _populate(url)
    before = fingerprint(url)
    with sqlite3.connect(source) as live, sqlite3.connect(backup) as copy:
        live.backup(copy)                                     # the online backup, safe while in use
    shutil.copyfile(backup, restored)                         # restoring is putting the file back
    return url, f"sqlite:///{restored}", populated, before, {"backup": backup.name, "bytes": backup.stat().st_size}


def _with_database(url, name):
    split = urlsplit(url)
    return urlunsplit(split._replace(path="/" + name))


def _postgres_drill(url, directory):
    import psycopg
    split = urlsplit(url)
    name = split.path.lstrip("/")
    restored_name = name + "_restored"
    restored = _with_database(url, restored_name)
    admin = _with_database(url, "postgres")
    populated = _populate(url)
    before = fingerprint(url)
    dump = directory / f"{name}.dump"
    started = time.time()
    subprocess.run(["pg_dump", "--format=custom", "--no-owner", "--no-privileges", f"--file={dump}", url],
                   check=True, capture_output=True)
    with psycopg.connect(admin, autocommit=True) as connection:
        connection.execute(f'DROP DATABASE IF EXISTS "{restored_name}"')
        connection.execute(f'CREATE DATABASE "{restored_name}"')
    subprocess.run(["pg_restore", "--no-owner", "--no-privileges", "--exit-on-error", f"--dbname={restored}", str(dump)],
                   check=True, capture_output=True)
    return url, restored, populated, before, {"backup": dump.name, "bytes": dump.stat().st_size,
                                              "seconds": round(time.time() - started, 1)}


def drill(postgres_url=None):
    with tempfile.TemporaryDirectory(prefix="mrs-backup-drill-") as name:
        directory = Path(name)
        if postgres_url:
            source, restored, populated, before, backup = _postgres_drill(postgres_url, directory)
        else:
            source, restored, populated, before, backup = _sqlite_drill(directory)
        after_restore = fingerprint(restored)
        original_encounters, original_changes = _encounters(source)
        restored_encounters, restored_changes = _encounters(restored)
        after_opening = fingerprint(restored)
        tables_differing = sorted(table for table in set(before) | set(after_restore)
                                  if before.get(table) != after_restore.get(table))
        changed_by_opening = sorted(table for table in set(after_restore) | set(after_opening)
                                    if after_restore.get(table) != after_opening.get(table))
        return {
            "engine": "postgresql" if postgres_url else "sqlite",
            "populated": populated,
            "backup": backup,
            "tables": len(before),
            "rows": sum(item["rows"] for item in before.values()),
            "rows_by_table": {table: item["rows"] for table, item in before.items() if item["rows"]},
            "tables_differing_after_restore": tables_differing,
            "encounters_read_back": len(restored_encounters),
            "encounters_identical": original_encounters == restored_encounters and bool(original_encounters),
            "account_changes_identical": original_changes == restored_changes and bool(original_changes),
            "tables_changed_by_opening_the_restored_database": changed_by_opening,
            "passed": (not tables_differing and not changed_by_opening and original_encounters == restored_encounters
                       and bool(original_encounters) and original_changes == restored_changes),
        }


def compare(source, restored):
    """Table by table: row counts and whether the rows are identical. Reads only; prints no content."""
    before, after = fingerprint(source), fingerprint(restored)
    tables = {table: {"source_rows": (before.get(table) or {}).get("rows"),
                      "restored_rows": (after.get(table) or {}).get("rows"),
                      "identical": before.get(table) == after.get(table)}
              for table in sorted(set(before) | set(after))}
    return {"tables": tables, "passed": all(item["identical"] for item in tables.values())}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    engine = parser.add_mutually_exclusive_group(required=True)
    engine.add_argument("--sqlite", action="store_true", help="drill a temporary SQLite database")
    engine.add_argument("--postgres", metavar="URL", help="an EMPTY, throwaway PostgreSQL database")
    engine.add_argument("--compare", nargs=2, metavar=("SOURCE_URL", "RESTORED_URL"),
                        help="compare a database with its restored copy, reading only")
    parser.add_argument("--out", help="write the JSON report here as well")
    args = parser.parse_args(argv)
    report = compare(*args.compare) if args.compare else drill(args.postgres)
    text = json.dumps(report, indent=1, ensure_ascii=False)
    print(text)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
