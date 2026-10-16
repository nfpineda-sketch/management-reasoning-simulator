from contextlib import contextmanager

import pytest

from account_store import AccountError, AccountStore


_GENERIC = "The account database is temporarily unavailable. Please try again."


def _bare_store():
    store = object.__new__(AccountStore)
    store._sqlite = False
    return store


def test_connection_acquisition_failure_is_sanitized(monkeypatch):
    store = _bare_store()

    @contextmanager
    def broken_borrow():
        raise RuntimeError("postgresql://user:secret@example.invalid/private")
        yield  # pragma: no cover

    monkeypatch.setattr(store, "_borrow_connection", broken_borrow)

    with pytest.raises(AccountError) as caught:
        with store._transaction():
            pass

    assert str(caught.value) == _GENERIC
    assert "secret" not in str(caught.value)


def test_rollback_failure_cannot_replace_the_sanitized_error(monkeypatch):
    store = _bare_store()

    class LostConnection:
        def commit(self):
            pass

        def rollback(self):
            raise RuntimeError("rollback leaked host=private-db password=secret")

    @contextmanager
    def lost_borrow():
        yield LostConnection()

    monkeypatch.setattr(store, "_borrow_connection", lost_borrow)

    with pytest.raises(AccountError) as caught:
        with store._transaction():
            raise RuntimeError("driver leaked host=private-db password=secret")

    assert str(caught.value) == _GENERIC
    assert "private-db" not in str(caught.value)
    assert "secret" not in str(caught.value)
