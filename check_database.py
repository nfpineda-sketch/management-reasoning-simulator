#!/usr/bin/env python3
"""Say why the account database will not open, without printing the URL.

The application hides its database errors on purpose: a connection failure can
carry the host, the user and sometimes the password, and none of that belongs
in a browser. This runs the same checks locally and reports the cause in words.

    MRS_DATABASE_URL='postgresql://...' python check_database.py

It never prints the URL, the password or the provider's raw error. It creates
nothing unless --create is passed, which opens the store exactly as the
application does, tables included.
"""
import argparse
import os
import sys
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


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--create", action="store_true",
                        help="open the store as the application does, creating its tables")
    arguments = parser.parse_args()
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
