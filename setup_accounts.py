#!/usr/bin/env python3
"""Create the first administrator without placing a password in shell history.

Local use:
    python setup_accounts.py --local-db /absolute/path/accounts.sqlite3
Hosted setup with MRS_DATABASE_URL already set in the environment:
    python setup_accounts.py
Generate the two bootstrap secret lines for Streamlit's private Secrets panel:
    python setup_accounts.py --print-bootstrap
"""
import argparse
from getpass import getpass
import json
import os
from pathlib import Path
import sys

from account_store import AccountError, AccountStore, hash_password


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--local-db", metavar="PATH", help="Explicit local SQLite database path.")
    group.add_argument("--print-bootstrap", action="store_true", help="Print a salted password hash for private deployment configuration.")
    parser.add_argument("--username", help="Administrator username; prompted when omitted.")
    args = parser.parse_args(argv)
    username = args.username or input("Administrator username: ").strip()
    try:
        password = getpass("New administrator password (at least 12 characters): ")
        confirmation = getpass("Confirm administrator password: ")
        if password != confirmation:
            raise AccountError("The passwords do not match.")
        password_hash = hash_password(password)
        del password, confirmation
        if args.print_bootstrap:
            # Validate the same username rules before emitting configuration.
            from account_store import _username
            username = _username(username)
            print("Paste these lines only into the private deployment Secrets panel:")
            print("MRS_ADMIN_USERNAME = " + json.dumps(username))
            print("MRS_ADMIN_PASSWORD_HASH = " + json.dumps(password_hash))
            print("After the first administrator is created, remove these bootstrap secrets.")
            return 0
        if args.local_db:
            database_url = "sqlite:///" + str(Path(args.local_db).expanduser().resolve())
        else:
            database_url = os.environ.get("MRS_DATABASE_URL", "")
            if not database_url:
                raise AccountError("Set MRS_DATABASE_URL or choose --local-db for development.")
        store = AccountStore(database_url, allow_sqlite=bool(args.local_db))
        created = store.bootstrap_admin(username, password_hash)
        print("Administrator created. Sign in to create resident and faculty invitations." if created
              else "An administrator already exists. No account or password was changed.")
        return 0
    except (EOFError, KeyboardInterrupt):
        print("Setup cancelled.", file=sys.stderr)
        return 1
    except AccountError as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
