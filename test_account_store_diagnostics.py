"""A closed door has to leave a note for the administrator.

The account gate hides database errors from the browser on purpose: a
connection failure can carry the connection string. It used to discard them
entirely, so an administrator had nothing to act on — the app said "contact
the application administrator" and the administrator was the one reading it.
The failure is now written to the application log, redacted, naming the step.
"""
import logging

import pytest

import account_portal

URL = "postgresql://mrs_owner:supersecretvalue@host.neon.tech/mrs?sslmode=require"


def test_the_password_never_reaches_the_log():
    text = account_portal._redacted(
        RuntimeError(f'connection to {URL} failed: authentication failed'), URL)
    assert "supersecretvalue" not in text
    assert "***" in text


def test_the_rest_of_the_message_survives():
    text = account_portal._redacted(RuntimeError("could not translate host name"), URL)
    assert "could not translate host name" in text


def test_an_empty_error_still_says_something():
    assert account_portal._redacted(RuntimeError(""), URL) == "(no message)"


def test_a_short_password_does_not_mangle_the_message():
    short = "postgresql://u:p@host/db"
    text = account_portal._redacted(RuntimeError("connection to port 5432 refused"), short)
    assert "port 5432" in text


def test_the_connection_step_is_named_in_the_log(monkeypatch, caplog):
    def explode(*args, **kwargs):
        raise RuntimeError("connection failed for " + URL)
    monkeypatch.setattr(account_portal, "AccountStore", explode)
    with caplog.at_level(logging.ERROR, logger="mrs.accounts"):
        with pytest.raises(RuntimeError):
            account_portal._configured_store(URL, False, "", "")
    assert "at connection" in caplog.text
    assert "supersecretvalue" not in caplog.text


def test_the_bootstrap_step_is_named_in_the_log(monkeypatch, caplog):
    class Store:
        def bootstrap_admin(self, username, password_hash):
            raise ValueError("bad hash for " + URL)
    monkeypatch.setattr(account_portal, "AccountStore", lambda *a, **k: Store())
    with caplog.at_level(logging.ERROR, logger="mrs.accounts"):
        with pytest.raises(ValueError):
            account_portal._configured_store(URL, False, "someone", "a-hash")
    assert "at administrator bootstrap" in caplog.text
    assert "supersecretvalue" not in caplog.text


def test_a_working_store_logs_nothing(monkeypatch, caplog):
    class Store:
        def bootstrap_admin(self, username, password_hash):
            return True
    monkeypatch.setattr(account_portal, "AccountStore", lambda *a, **k: Store())
    with caplog.at_level(logging.ERROR, logger="mrs.accounts"):
        assert account_portal._configured_store(URL, False, "someone", "a-hash")
    assert caplog.text == ""


def test_the_sign_in_throttle_is_told_apart_from_a_wrong_password(tmp_path):
    import pytest
    from account_store import AccountError, AccountLocked, AccountStore, hash_password
    store = AccountStore("sqlite:///" + str(tmp_path / "a.sqlite3"), allow_sqlite=True)
    store.bootstrap_admin("npineda", hash_password("una-clave-larga-de-prueba"))

    for _ in range(5):
        with pytest.raises(AccountError) as raised:
            store.authenticate("npineda", "la-clave-equivocada")
        assert not isinstance(raised.value, AccountLocked)

    with pytest.raises(AccountLocked) as raised:
        store.authenticate("npineda", "una-clave-larga-de-prueba")
    assert "minute(s)" in str(raised.value)
    # A subclass, so code that only knows AccountError keeps catching it.
    assert isinstance(raised.value, AccountError)


def test_a_bad_bootstrap_secret_does_not_close_a_deployment_that_has_an_administrator(tmp_path):
    import pytest
    from account_store import AccountError, AccountStore, hash_password
    store = AccountStore("sqlite:///" + str(tmp_path / "a.sqlite3"), allow_sqlite=True)

    # Before there is an administrator, a malformed hash is fatal: it is the
    # only thing that could have created one.
    with pytest.raises(AccountError) as raised:
        store.bootstrap_admin("npineda", "EL_HASH_QUE_GENERA_EL_COMANDO")
    assert "four" in str(raised.value)

    assert store.bootstrap_admin("npineda", hash_password("una-clave-larga-de-prueba")) is True

    # Afterwards it is inert, and the store opens as usual.
    assert store.bootstrap_admin("npineda", "EL_HASH_QUE_GENERA_EL_COMANDO") is False
    assert store.bootstrap_admin("otro", "") is False
    assert store.authenticate("npineda", "una-clave-larga-de-prueba")
