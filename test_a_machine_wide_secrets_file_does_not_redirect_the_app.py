"""A machine-wide ``~/.streamlit/secrets.toml`` never decides where the app under test writes.

Pre-deployment B-1 rehearsal, 2026-10-07: with that file naming another database, the Phase 0 test
on PostgreSQL created seven account tables there, not in ``MRS_TEST_POSTGRES_URL``. Streamlit reads
the file before the project's own, ``account_portal._setting`` prefers ``st.secrets`` to the
environment, and Streamlit copies each value into ``os.environ`` as well, over a test's
``monkeypatch.setenv``. ``conftest.py`` now gives Streamlit an empty per-user folder for the session.

This runs the real page the way that fixture does (settings in the environment, no ``at.secrets``)
under a ``HOME`` whose secrets file names a decoy, and records which database URL the page opened.
SQLite stands in for both databases, so it runs on every machine, with or without PostgreSQL.
"""
import os
import sqlite3
from pathlib import Path

import streamlit as st
from streamlit.testing.v1 import AppTest

import account_portal

APP = str(Path(__file__).with_name("app.py"))
DECOY_KEY = "sk-decoy-not-a-real-key"


def _secret(name):
    try:
        return str(st.secrets.get(name, ""))
    except Exception:  # No secrets file at all is normal locally, as in account_portal._setting.
        return ""


def _tables(path):
    with sqlite3.connect(path) as connection:
        return {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}


def test_a_machine_wide_secrets_file_naming_another_database_does_not_redirect_the_app(tmp_path, monkeypatch):
    home = tmp_path / "home"
    (home / ".streamlit").mkdir(parents=True)
    decoy, target = tmp_path / "decoy.sqlite3", tmp_path / "target.sqlite3"
    (home / ".streamlit" / "secrets.toml").write_text(
        f'MRS_DATABASE_URL = "sqlite:///{decoy}"\nOPENAI_API_KEY = "{DECOY_KEY}"\n', encoding="utf-8")
    monkeypatch.setenv("HOME", str(home))
    assert Path.home() == home  # the decoy is where a machine-wide file would be
    url = f"sqlite:///{target}"
    for name, value in (("MRS_AUTH_MODE", "accounts"), ("MRS_DATABASE_URL", url), ("MRS_ALLOW_LOCAL_SQLITE", "1")):
        monkeypatch.setenv(name, value)
    opened = []
    configured_store = account_portal._configured_store

    def recorded(store_url, *args, **kwargs):
        opened.append(store_url)
        return configured_store(store_url, *args, **kwargs)

    monkeypatch.setattr(account_portal, "_configured_store", recorded)
    st.secrets._reset()  # what Streamlit reads from disk is read again, under this HOME
    try:
        at = AppTest.from_file(APP, default_timeout=60).run()
        seen = {"secret": _secret("OPENAI_API_KEY"), "environ": os.environ.get("OPENAI_API_KEY", ""),
                "environ_url": os.environ.get("MRS_DATABASE_URL")}
    finally:
        st.secrets._reset()  # nothing read under this HOME outlives the test
    assert not at.exception
    assert opened and set(opened) == {url}, f"the app opened {opened}, not the test's {url}"
    assert not decoy.exists()
    assert "mrs_users" in _tables(target)
    assert seen["environ_url"] == url
    assert DECOY_KEY not in (seen["secret"], seen["environ"])
