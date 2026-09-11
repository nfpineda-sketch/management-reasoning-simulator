"""Accounts and encounter persistence for the optional curriculum deployment.

PostgreSQL is required for hosted use. SQLite is an explicit local development
option; never place a Cloud database on Streamlit's ephemeral filesystem.
All authorization is checked against the database on every operation. The
store represents one teaching cohort; faculty may read that cohort's attempts.
"""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import hmac
import json
from pathlib import Path
import re
import secrets
import sqlite3
import time
from typing import Any
import uuid


class AccountError(Exception):
    """An intentionally non-sensitive message safe to display to the user."""


PASSWORD_ROUNDS = 600_000
ROLES = frozenset({"resident", "faculty", "admin"})
ATTEMPT_STATUSES = frozenset({"active", "completed", "abandoned"})
_SCHEMA_LOCK = 731093218


def _password_valid(password: str) -> bool:
    return isinstance(password, str) and 12 <= len(password) <= 1024


def hash_password(password: str) -> str:
    """Produce a salted hash for local setup or an administrator secret."""
    if not _password_valid(password):
        raise AccountError("Use a password between 12 and 1,024 characters.")
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), PASSWORD_ROUNDS
    ).hex()
    return f"pbkdf2_sha256${PASSWORD_ROUNDS}${salt}${digest}"


def _valid_password_hash(value: str) -> bool:
    try:
        algorithm, rounds, salt, digest = value.split("$")
        return (
            algorithm == "pbkdf2_sha256"
            and PASSWORD_ROUNDS <= int(rounds) <= 2_000_000
            and len(bytes.fromhex(salt)) == 16
            and len(bytes.fromhex(digest)) == 32
        )
    except (AttributeError, TypeError, ValueError):
        return False


def _verify_password(password: str, encoded: str | None) -> bool:
    # Unknown accounts take the same KDF path; no password/token is logged.
    if not isinstance(password, str) or len(password) > 1024:
        password = ""
    valid = _valid_password_hash(encoded)
    if valid:
        _, rounds, salt, expected = encoded.split("$")
    else:
        rounds, salt, expected = PASSWORD_ROUNDS, "00" * 16, "00" * 32
    actual = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), int(rounds)
    ).hex()
    return valid and hmac.compare_digest(actual, expected)


def _username(value: str) -> str:
    if not isinstance(value, str):
        raise AccountError("Use 3–80 letters, numbers, or . _ @ + - for the username.")
    result = value.strip().lower()
    if not re.fullmatch(r"[a-z0-9][a-z0-9._@+\-]{2,79}", result):
        raise AccountError("Use 3–80 letters, numbers, or . _ @ + - for the username.")
    return result


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _json(value: Any, max_bytes: int = 5_000_000) -> str:
    if not isinstance(value, dict):
        raise AccountError("An encounter record must be an object.")
    try:
        encoded = json.dumps(value, ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError, OverflowError):
        raise AccountError("The encounter record contains unsupported values.") from None
    if len(encoded.encode("utf-8")) > max_bytes:
        raise AccountError("The encounter record is too large to save.")
    return encoded


def _enrollment(role: str, training_year: int | None) -> tuple[str, int | None]:
    if role not in ROLES:
        raise AccountError("Choose a valid account role.")
    if training_year is not None and (
        isinstance(training_year, bool)
        or not isinstance(training_year, int)
        or training_year not in (1, 2, 3)
    ):
        raise AccountError("The training year must be 1, 2, or 3.")
    if role == "resident" and training_year is None:
        raise AccountError("A resident needs a training year.")
    return role, training_year if role == "resident" else None


class AccountStore:
    """A transactional store with opaque sessions and one-use invitations.

    Args:
        url: PostgreSQL DSN, or ``sqlite:////absolute/path/accounts.sqlite3``.
        allow_sqlite: Must be explicitly true for local SQLite development.
        session_hours: Absolute login lifetime (1–168 hours), not sliding.
    """

    def __init__(self, url: str, allow_sqlite: bool = False, session_hours: int = 12):
        if not isinstance(url, str) or not url:
            raise AccountError("The account database has not been configured.")
        if not isinstance(session_hours, int) or not 1 <= session_hours <= 168:
            raise AccountError("The account session lifetime is invalid.")
        self._url = url
        self._session_seconds = session_hours * 3600
        self._sqlite = url.startswith("sqlite:///")
        if self._sqlite:
            if not allow_sqlite:
                raise AccountError("SQLite is available only in explicit local development mode.")
            self._path = Path(url[len("sqlite:///"):])
            if not self._path.is_absolute():
                raise AccountError("The local database needs an absolute filesystem path.")
            try:
                self._path.parent.mkdir(parents=True, exist_ok=True)
                # Create privately before SQLite opens it. Existing files are
                # not truncated, and credentials never appear in this file name.
                self._path.touch(mode=0o600, exist_ok=True)
                self._path.chmod(0o600)
            except OSError:
                raise AccountError("The local account database could not be opened.") from None
        elif not url.startswith(("postgres://", "postgresql://")):
            raise AccountError("Hosted accounts require a PostgreSQL database URL.")
        self._initialize()

    def _connect(self):
        if self._sqlite:
            connection = sqlite3.connect(str(self._path), timeout=15)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA busy_timeout = 15000")
            return connection
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError:
            raise AccountError("The PostgreSQL account driver is not installed.") from None
        return psycopg.connect(self._url, row_factory=dict_row, connect_timeout=10)

    def _execute(self, connection, sql: str, parameters: tuple = ()):
        return connection.execute(sql if self._sqlite else sql.replace("?", "%s"), parameters)

    @contextmanager
    def _transaction(self, write: bool = False):
        connection = None
        try:
            connection = self._connect()
            if self._sqlite:
                connection.execute("BEGIN IMMEDIATE" if write else "BEGIN")
            elif write:
                # Serializes bootstrap, invite consumption and attempt creation
                # across workers. The lock is released at transaction end.
                self._execute(connection, "SELECT pg_advisory_xact_lock(?)", (_SCHEMA_LOCK,))
            yield connection
            connection.commit()
        except AccountError:
            if connection is not None:
                connection.rollback()
            raise
        except Exception:
            if connection is not None:
                connection.rollback()
            # Driver exceptions can contain hostnames, usernames or SQL data.
            raise AccountError("The account database is temporarily unavailable. Please try again.") from None
        finally:
            if connection is not None:
                connection.close()

    def _initialize(self):
        statements = [
            """CREATE TABLE IF NOT EXISTS mrs_users (
                id TEXT PRIMARY KEY, username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL, role TEXT NOT NULL
                    CHECK (role IN ('resident','faculty','admin')),
                training_year INTEGER, active INTEGER NOT NULL DEFAULT 1,
                created_at BIGINT NOT NULL,
                CHECK (active IN (0,1)),
                CHECK ((role = 'resident' AND training_year IN (1,2,3))
                    OR (role != 'resident' AND training_year IS NULL))
            )""",
            """CREATE TABLE IF NOT EXISTS mrs_sessions (
                token_hash TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES mrs_users(id) ON DELETE CASCADE,
                created_at BIGINT NOT NULL, expires_at BIGINT NOT NULL
            )""",
            """CREATE TABLE IF NOT EXISTS mrs_login_attempts (
                bucket TEXT PRIMARY KEY, failures INTEGER NOT NULL,
                started_at BIGINT NOT NULL
            )""",
            """CREATE TABLE IF NOT EXISTS mrs_invites (
                code_hash TEXT PRIMARY KEY, role TEXT NOT NULL,
                training_year INTEGER,
                created_by TEXT NOT NULL REFERENCES mrs_users(id),
                created_at BIGINT NOT NULL, expires_at BIGINT NOT NULL,
                used_by TEXT REFERENCES mrs_users(id)
            )""",
            """CREATE TABLE IF NOT EXISTS mrs_attempts (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES mrs_users(id),
                challenge_id TEXT NOT NULL, encounter_json TEXT NOT NULL,
                payload_json TEXT NOT NULL, status TEXT NOT NULL,
                is_sandbox INTEGER NOT NULL,
                created_at BIGINT NOT NULL, updated_at BIGINT NOT NULL,
                revision INTEGER NOT NULL DEFAULT 0,
                CHECK (status IN ('active','completed','abandoned')),
                CHECK (is_sandbox IN (0,1))
            )""",
            "CREATE INDEX IF NOT EXISTS mrs_sessions_user ON mrs_sessions(user_id)",
            "CREATE INDEX IF NOT EXISTS mrs_attempts_user ON mrs_attempts(user_id, updated_at)",
            """CREATE UNIQUE INDEX IF NOT EXISTS mrs_active_resident_attempt
                ON mrs_attempts(user_id) WHERE status = 'active' AND is_sandbox = 0""",
        ]
        with self._transaction(write=True) as connection:
            for statement in statements:
                self._execute(connection, statement)
            if self._sqlite:
                columns = {row["name"] for row in self._execute(connection, "PRAGMA table_info(mrs_attempts)").fetchall()}
            else:
                columns = {row["column_name"] for row in self._execute(connection,
                    "SELECT column_name FROM information_schema.columns WHERE table_schema = current_schema() AND table_name = 'mrs_attempts'").fetchall()}
            if "revision" not in columns:
                self._execute(connection, "ALTER TABLE mrs_attempts ADD COLUMN revision INTEGER NOT NULL DEFAULT 0")

    @staticmethod
    def _public_user(row) -> dict:
        return {
            "id": row["id"], "username": row["username"], "role": row["role"],
            "training_year": row["training_year"], "active": bool(row["active"]),
            "created_at": row["created_at"],
        }

    def _actor(self, connection, token: str, roles=None) -> dict:
        if not isinstance(token, str) or len(token) > 200:
            raise AccountError("Please sign in again.")
        row = self._execute(connection, """SELECT u.* FROM mrs_sessions s
            JOIN mrs_users u ON u.id = s.user_id
            WHERE s.token_hash = ? AND s.expires_at > ? AND u.active = 1""",
            (_digest(token), int(time.time()))).fetchone()
        if row is None:
            raise AccountError("Please sign in again.")
        actor = self._public_user(row)
        if roles is not None and actor["role"] not in roles:
            raise AccountError("Your account does not have permission for this action.")
        return actor

    def _new_session(self, connection, user_id: str) -> str:
        now = int(time.time())
        token = secrets.token_urlsafe(32)
        self._execute(connection, "DELETE FROM mrs_sessions WHERE expires_at <= ?", (now,))
        self._execute(connection, "INSERT INTO mrs_sessions VALUES (?, ?, ?, ?)",
            (_digest(token), user_id, now, now + self._session_seconds))
        return token

    def bootstrap_admin(self, username: str, password_hash: str) -> bool:
        """Create the first administrator; never reset or replace an account.

        Return false when any administrator already exists (even disabled).
        This method belongs to trusted deployment setup, never the signup UI.
        """
        username = _username(username)
        if not _valid_password_hash(password_hash):
            raise AccountError("The administrator password hash is invalid.")
        with self._transaction(write=True) as connection:
            if self._execute(connection, "SELECT id FROM mrs_users WHERE role = 'admin' LIMIT 1").fetchone():
                return False
            if self._execute(connection, "SELECT id FROM mrs_users WHERE username = ?", (username,)).fetchone():
                raise AccountError("That username is already registered.")
            self._execute(connection, "INSERT INTO mrs_users VALUES (?, ?, ?, 'admin', NULL, 1, ?)",
                (uuid.uuid4().hex, username, password_hash, int(time.time())))
            return True

    def authenticate(self, username: str, password: str) -> str:
        try:
            username = _username(username)
        except AccountError:
            username = "__invalid_username__"
        now = int(time.time())
        bucket = _digest(username)
        error = None
        token = None
        with self._transaction(write=True) as connection:
            row = self._execute(connection, "SELECT * FROM mrs_login_attempts WHERE bucket = ?", (bucket,)).fetchone()
            if row and now - row["started_at"] < 900 and row["failures"] >= 5:
                raise AccountError("Too many sign-in attempts. Try again in 15 minutes.")
            started_at = row["started_at"] if row and now - row["started_at"] < 900 else now
            failures = row["failures"] if row and now - row["started_at"] < 900 else 0
            user = self._execute(connection, "SELECT * FROM mrs_users WHERE username = ?", (username,)).fetchone()
            valid = _verify_password(password, user["password_hash"] if user else None)
            if user is None or not valid or not user["active"]:
                self._execute(connection, """INSERT INTO mrs_login_attempts VALUES (?, ?, ?)
                    ON CONFLICT(bucket) DO UPDATE SET failures = excluded.failures,
                    started_at = excluded.started_at""", (bucket, failures + 1, started_at))
                # Commit the throttle before raising. Raising inside this block
                # would roll back the failed-login evidence.
                error = "The username or password is incorrect, or the account is unavailable."
            else:
                self._execute(connection, "DELETE FROM mrs_login_attempts WHERE bucket = ?", (bucket,))
                token = self._new_session(connection, user["id"])
        if error:
            raise AccountError(error)
        return token

    def get_user(self, token: str) -> dict | None:
        with self._transaction() as connection:
            try:
                return self._actor(connection, token)
            except AccountError:
                return None

    def logout(self, token: str):
        if not isinstance(token, str):
            return
        with self._transaction(write=True) as connection:
            self._execute(connection, "DELETE FROM mrs_sessions WHERE token_hash = ?", (_digest(token),))

    def revoke_session(self, token: str):
        """Alias used by the Streamlit sign-out portal."""
        self.logout(token)

    def create_invite(self, token: str, role: str, training_year: int | None = None) -> str:
        role, training_year = _enrollment(role, training_year)
        code = secrets.token_urlsafe(24)
        now = int(time.time())
        with self._transaction(write=True) as connection:
            actor = self._actor(connection, token, {"admin"})
            self._execute(connection, "INSERT INTO mrs_invites VALUES (?, ?, ?, ?, ?, ?, NULL)",
                (_digest(code), role, training_year, actor["id"], now, now + 7 * 86400))
        return code

    def register(self, username: str, password: str, invite_code: str) -> str:
        username = _username(username)
        if not isinstance(invite_code, str) or len(invite_code) > 200:
            raise AccountError("The invitation is invalid, expired, or already used.")
        if not _password_valid(password):
            raise AccountError("Use a password between 12 and 1,024 characters.")
        with self._transaction(write=True) as connection:
            invite = self._execute(connection, """SELECT * FROM mrs_invites
                WHERE code_hash = ? AND used_by IS NULL AND expires_at > ?""",
                (_digest(invite_code.strip()), int(time.time()))).fetchone()
            if invite is None:
                raise AccountError("The invitation is invalid, expired, or already used.")
            if self._execute(connection, "SELECT id FROM mrs_users WHERE username = ?", (username,)).fetchone():
                raise AccountError("That username is already registered.")
            user_id = uuid.uuid4().hex
            self._execute(connection, "INSERT INTO mrs_users VALUES (?, ?, ?, ?, ?, 1, ?)",
                (user_id, username, hash_password(password), invite["role"], invite["training_year"], int(time.time())))
            self._execute(connection, "UPDATE mrs_invites SET used_by = ? WHERE code_hash = ? AND used_by IS NULL",
                (user_id, _digest(invite_code.strip())))
            return self._new_session(connection, user_id)

    def list_users(self, token: str) -> list[dict]:
        with self._transaction() as connection:
            self._actor(connection, token, {"admin"})
            return [self._public_user(row) for row in self._execute(connection,
                "SELECT * FROM mrs_users ORDER BY username").fetchall()]

    def update_user(self, token: str, user_id: str, role: str | None = None,
                    training_year: int | None = None, active: bool | None = None):
        with self._transaction(write=True) as connection:
            self._actor(connection, token, {"admin"})
            row = self._execute(connection, "SELECT * FROM mrs_users WHERE id = ?", (user_id,)).fetchone()
            if row is None:
                raise AccountError("The account was not found.")
            new_role = row["role"] if role is None else role
            new_year = row["training_year"] if training_year is None else training_year
            new_role, new_year = _enrollment(new_role, new_year)
            if active is not None and not isinstance(active, bool):
                raise AccountError("The account status is invalid.")
            new_active = bool(row["active"]) if active is None else active
            if row["role"] == "admin" and row["active"] and (new_role != "admin" or not new_active):
                remaining = self._execute(connection,
                    "SELECT COUNT(*) AS n FROM mrs_users WHERE role = 'admin' AND active = 1 AND id != ?",
                    (user_id,)).fetchone()["n"]
                if not remaining:
                    raise AccountError("Keep at least one active administrator.")
            self._execute(connection, "UPDATE mrs_users SET role = ?, training_year = ?, active = ? WHERE id = ?",
                (new_role, new_year, int(new_active), user_id))
            if (new_role, new_year, new_active) != (row["role"], row["training_year"], bool(row["active"])):
                self._execute(connection, "DELETE FROM mrs_sessions WHERE user_id = ?", (user_id,))

    def change_password(self, token: str, current_password: str, new_password: str) -> str:
        """Change one's own password, revoke every session, and issue a fresh one."""
        if not _password_valid(new_password):
            raise AccountError("Use a password between 12 and 1,024 characters.")
        with self._transaction(write=True) as connection:
            actor = self._actor(connection, token)
            row = self._execute(connection, "SELECT password_hash FROM mrs_users WHERE id = ?", (actor["id"],)).fetchone()
            if not _verify_password(current_password, row["password_hash"]):
                raise AccountError("The current password is incorrect.")
            self._execute(connection, "UPDATE mrs_users SET password_hash = ? WHERE id = ?",
                (hash_password(new_password), actor["id"]))
            self._execute(connection, "DELETE FROM mrs_sessions WHERE user_id = ?", (actor["id"],))
            return self._new_session(connection, actor["id"])

    def create_attempt(self, token: str, challenge_id: str, encounter: dict, is_sandbox: bool = False) -> str:
        if not isinstance(challenge_id, str) or not re.fullmatch(r"R[123]-\d{2}", challenge_id):
            raise AccountError("The assigned challenge is invalid.")
        encoded = _json(encounter, max_bytes=1_000_000)
        with self._transaction(write=True) as connection:
            actor = self._actor(connection, token)
            if actor["role"] == "resident":
                if is_sandbox:
                    raise AccountError("Faculty sandbox access requires a faculty account.")
                if int(challenge_id[1]) > actor["training_year"]:
                    raise AccountError("This challenge has not been assigned to your training stage.")
                existing = self._execute(connection, """SELECT id FROM mrs_attempts
                    WHERE user_id = ? AND status = 'active' AND is_sandbox = 0""", (actor["id"],)).fetchone()
                if existing:
                    return existing["id"]
            else:
                is_sandbox = True
            attempt_id, now = uuid.uuid4().hex, int(time.time())
            self._execute(connection, """INSERT INTO mrs_attempts
                (id, user_id, challenge_id, encounter_json, payload_json, status, is_sandbox, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 'active', ?, ?, ?)""",
                (attempt_id, actor["id"], challenge_id, encoded, "{}", int(is_sandbox), now, now))
            return attempt_id

    @staticmethod
    def _attempt(row) -> dict:
        return {
            "id": row["id"], "user_id": row["user_id"], "username": row["username"],
            "challenge_id": row["challenge_id"], "encounter": json.loads(row["encounter_json"]),
            "payload": json.loads(row["payload_json"]), "status": row["status"],
            "is_sandbox": bool(row["is_sandbox"]), "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "revision": row["revision"],
        }

    def save_attempt(self, token: str, attempt_id: str, payload: dict, status: str = "active",
                     expected_revision: int | None = None) -> int:
        if status not in ATTEMPT_STATUSES:
            raise AccountError("The encounter status is invalid.")
        if expected_revision is not None and (
            isinstance(expected_revision, bool) or not isinstance(expected_revision, int) or expected_revision < 0
        ):
            raise AccountError("The encounter revision is invalid.")
        encoded = _json(payload)
        with self._transaction(write=True) as connection:
            actor = self._actor(connection, token)
            row = self._execute(connection, "SELECT * FROM mrs_attempts WHERE id = ? AND user_id = ?",
                (attempt_id, actor["id"])).fetchone()
            if row is None:
                raise AccountError("The encounter was not found or is not available to your account.")
            if row["status"] != "active":
                raise AccountError("A closed encounter is read-only and cannot be reopened or changed.")
            revision = row["revision"] if expected_revision is None else expected_revision
            result = self._execute(connection, """UPDATE mrs_attempts
                SET payload_json = ?, status = ?, updated_at = ?, revision = revision + 1
                WHERE id = ? AND user_id = ? AND revision = ?""",
                (encoded, status, int(time.time()), attempt_id, actor["id"], revision))
            if result.rowcount != 1:
                raise AccountError("This encounter changed in another session. Reload it before continuing.")
            return revision + 1

    def list_attempts(self, token: str) -> list[dict]:
        with self._transaction() as connection:
            actor = self._actor(connection, token)
            query = "SELECT a.*, u.username FROM mrs_attempts a JOIN mrs_users u ON u.id = a.user_id"
            parameters = ()
            if actor["role"] == "resident":
                query += " WHERE a.user_id = ?"
                parameters = (actor["id"],)
            rows = self._execute(connection, query + " ORDER BY a.updated_at DESC, a.id", parameters).fetchall()
            return [self._attempt(row) for row in rows]

    def get_attempt(self, token: str, attempt_id: str) -> dict | None:
        with self._transaction() as connection:
            actor = self._actor(connection, token)
            query = "SELECT a.*, u.username FROM mrs_attempts a JOIN mrs_users u ON u.id = a.user_id WHERE a.id = ?"
            parameters = (attempt_id,)
            if actor["role"] == "resident":
                query += " AND a.user_id = ?"
                parameters += (actor["id"],)
            row = self._execute(connection, query, parameters).fetchone()
            return self._attempt(row) if row is not None else None
