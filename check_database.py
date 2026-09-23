#!/usr/bin/env python3
"""Say why the account database will not open, without printing the URL.

The application hides its database errors on purpose: a connection failure can
carry the host, the user and sometimes the password, and none of that belongs
in a browser. This runs the same checks locally and reports the cause in words.

    MRS_DATABASE_URL='postgresql://...' python check_database.py

It never prints the URL, the password or the provider's raw error. It creates
nothing unless --create is passed, which opens the store exactly as the
application does, tables included.

    MRS_ADMIN_PASSWORD_HASH='pbkdf2_sha256$...' python check_database.py --admin-hash

checks the administrator bootstrap hash the same way the application does, and
says which part of it is wrong. It never prints the hash.
"""
import argparse
import os
import sys
import time
from urllib.parse import urlsplit

PLACEHOLDERS = ("USUARIO", "CLAVE", "HOST", "BASE", "USER", "PASSWORD", "DATABASE", "...")


def describe(url):
    """What is wrong with the URL itself, before anything is dialled."""
    if not url:
        return "MRS_DATABASE_URL is empty or unset."
    split = urlsplit(url)
    if split.scheme not in ("postgresql", "postgres"):
        return (f"the scheme is {split.scheme!r}; it has to be postgresql://. "
                "A sqlite: URL is refused on a hosted deployment.")
    for word in PLACEHOLDERS:
        if word in url:
            return (f"the URL still contains the example word {word!r}. This is the template, "
                    "not a database: provision PostgreSQL and paste its own connection URL.")
    if not split.hostname:
        return "the URL has no host."
    if not (split.path or "").strip("/"):
        return "the URL names no database after the host."
    if "sslmode" not in (split.query or ""):
        return ("the URL has no sslmode. Most hosted providers require sslmode=require; "
                "add it and try again.")
    return None


def report_account(url, username):
    """Say whether an account exists, may sign in, and is currently throttled.

    A sign-in screen cannot say any of this without telling a stranger which
    usernames exist. Run against the deployment's own database by whoever holds
    its URL, it separates "no such account" from "locked out for nine minutes",
    which look identical from the browser. No password or hash is read.
    """
    sqlite = str(url).startswith("sqlite:")
    if not sqlite:
        complaint = describe(url)
        if complaint:
            print("The database URL is not usable:", complaint)
            return 1
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from account_store import AccountStore, _digest, _username
    try:
        name = _username(username)
    except Exception as error:
        print("That username cannot be used:", error)
        return 1
    store = AccountStore(url, allow_sqlite=sqlite)
    with store._transaction() as connection:
        user = store._execute(
            connection, "SELECT role, active FROM mrs_users WHERE username = ?", (name,)
        ).fetchone()
        attempt = store._execute(
            connection, "SELECT failures, started_at FROM mrs_login_attempts WHERE bucket = ?",
            (_digest(name),)
        ).fetchone()
        admins = store._execute(
            connection, "SELECT username, active FROM mrs_users WHERE role = 'admin' ORDER BY username"
        ).fetchall()
    if user is None:
        print(f"No account named {name!r} exists.")
        print(f"The database holds {len(admins)} administrator account(s).")
        if not admins:
            print("None at all: the bootstrap secrets never created one. Set "
                  "MRS_ADMIN_USERNAME and MRS_ADMIN_PASSWORD_HASH, then reboot the app.")
        else:
            # Knowing which name to type is the whole question here, and whoever
            # holds the database URL can already read the table.
            print("Sign in as one of these instead:")
            for row in admins:
                print(f"   {row['username']}"
                      + ("" if row["active"] else "   (disabled — it cannot sign in)"))
    else:
        print(f"{name!r} exists, role {user['role']}, "
              f"{'active' if user['active'] else 'DISABLED — it cannot sign in'}.")
    if attempt:
        waited = int(time.time()) - int(attempt["started_at"])
        if waited < 900 and attempt["failures"] >= 5:
            print(f"It is locked by the sign-in throttle for another "
                  f"{max(1, (900 - waited + 59) // 60)} minute(s). The password is not the issue "
                  "until that passes.")
        elif waited < 900:
            print(f"{attempt['failures']} failed attempt(s) in the last "
                  f"{waited // 60} minute(s); five within fifteen minutes lock it.")
    return 0


def describe_admin_hash(value):
    """Why the application will refuse this bootstrap hash, or None.

    The hash is what ``setup_accounts.py --print-bootstrap`` prints. The
    judgement is the store's own, so this tool and the running application
    always agree; the hash itself is never printed.
    """
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from account_store import describe_password_hash
    if not str(value or "").strip():
        return "MRS_ADMIN_PASSWORD_HASH is empty or unset."
    return describe_password_hash(str(value).strip("\r\n"))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--create", action="store_true",
                        help="open the store as the application does, creating its tables")
    parser.add_argument("--admin-hash", action="store_true",
                        help="check MRS_ADMIN_PASSWORD_HASH instead of the database URL")
    parser.add_argument("--account", metavar="USERNAME",
                        help="report whether this account exists, is active, and is throttled")
    arguments = parser.parse_args(argv)
    if arguments.account:
        return report_account(os.environ.get("MRS_DATABASE_URL", ""), arguments.account)
    if arguments.admin_hash:
        complaint = describe_admin_hash(os.environ.get("MRS_ADMIN_PASSWORD_HASH", ""))
        if complaint:
            print("The administrator hash is not usable:", complaint)
            return 1
        print("The administrator hash is well formed. Paste it into Secrets exactly as printed, "
              "on one line, between double quotes.")
        return 0
    url = os.environ.get("MRS_DATABASE_URL", "").strip()
    complaint = describe(url)
    if complaint:
        print("The URL is not usable:", complaint)
        return 1
    split = urlsplit(url)
    print(f"URL looks well formed · host {split.hostname} · database {split.path.lstrip('/')}")
    try:
        import psycopg
    except ImportError:
        print("psycopg is not installed in this environment; install requirements first.")
        return 1
    try:
        with psycopg.connect(url, connect_timeout=10) as connection:
            with connection.cursor() as cursor:
                cursor.execute("select version()")
                cursor.fetchone()
                cursor.execute("select has_database_privilege(current_user, current_database(), 'CREATE')")
                may_create = cursor.fetchone()[0]
    except Exception as error:
        # The provider's message can carry the connection string.
        print("The connection failed:", type(error).__name__)
        reason = str(error).splitlines()[0] if str(error) else ""
        # Only redact something long enough to be a secret: a one-character
        # password would otherwise turn "port" into "***ort".
        for secret in (split.password, url):
            if secret and len(secret) >= 4:
                reason = reason.replace(secret, "***")
        print("  ", reason[:300] or "(no message)")
        return 1
    print("Connected.")
    if not may_create:
        print("But this user may not create tables in this database; the application needs that.")
        return 1
    print("This user may create tables.")
    if not arguments.create:
        print("Run again with --create to let the application build its tables.")
        return 0
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from account_store import AccountStore
    AccountStore(url).bootstrap_admin  # touch the API without creating an account
    print("The application's store opened; its tables are in place.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
