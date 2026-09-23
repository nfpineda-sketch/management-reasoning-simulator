"""Rotating the password you were given.

``change_password`` was in the store from the beginning and reached no screen,
so a resident handed a password at enrolment could never change it. Found on
2026-09-23 while listing what a resident's account still lacked.
"""
import time
import uuid

import pytest
from streamlit.testing.v1 import AppTest

from account_store import AccountError, AccountStore, hash_password

APP = """
import streamlit as st
from account_store import AccountStore
from account_portal import render_account_sidebar
store = AccountStore(st.session_state['database_url'], allow_sqlite=True)
# The app reads the token from session state, which is how a refreshed one
# after a password change keeps the person signed in. The harness must do the
# same or it re-runs holding the revoked token.
from account_portal import _TOKEN_KEY
token = st.session_state.get(_TOKEN_KEY) or st.session_state['test_token']
context = {'store': store, 'token': token, 'user': store.get_user(token)}
render_account_sidebar(context)
"""

PASSWORD = "original-password-12"


@pytest.fixture
def account(tmp_path):
    store = AccountStore(f"sqlite:///{tmp_path / 'accounts.sqlite3'}", allow_sqlite=True)
    with store._transaction(write=True) as connection:
        user_id = uuid.uuid4().hex
        store._execute(connection, "INSERT INTO mrs_users VALUES (?, ?, ?, ?, ?, 1, ?)",
                       (user_id, "resident_one", hash_password(PASSWORD), "resident", 1,
                        int(time.time())))
        token = store._new_session(connection, user_id)
    return store, user_id, token


def page(account):
    store, _, token = account
    app = AppTest.from_string(APP, default_timeout=20)
    app.session_state["database_url"] = store._url
    app.session_state["test_token"] = token
    app.run()
    assert not app.exception
    return app


def fields(app):
    return {item.label: item for item in app.text_input}


def test_a_resident_is_offered_the_form(account):
    app = page(account)
    assert "Change your password" in [item.label for item in app.expander]
    assert {"Current password", "New password", "Repeat the new password"} <= set(fields(app))


def test_changing_it_signs_the_old_password_out(account):
    store, _, token = account
    app = page(account)
    form = fields(app)
    form["Current password"].set_value(PASSWORD)
    form["New password"].set_value("a-brand-new-password")
    form["Repeat the new password"].set_value("a-brand-new-password")
    next(b for b in app.button if b.label == "Change password").click().run()
    assert not app.exception
    # The old password no longer works and the new one does.
    with pytest.raises(AccountError):
        store.authenticate("resident_one", PASSWORD)
    assert store.authenticate("resident_one", "a-brand-new-password")


def test_the_old_session_is_revoked_everywhere(account):
    store, _, token = account
    app = page(account)
    form = fields(app)
    form["Current password"].set_value(PASSWORD)
    form["New password"].set_value("a-brand-new-password")
    form["Repeat the new password"].set_value("a-brand-new-password")
    next(b for b in app.button if b.label == "Change password").click().run()
    # The token this session started with is gone; that is the point of it.
    # get_user answers None rather than raising for an unknown token.
    assert store.get_user(token) is None


def test_the_person_changing_it_stays_signed_in_here(account):
    store, user_id, _ = account
    app = page(account)
    form = fields(app)
    form["Current password"].set_value(PASSWORD)
    form["New password"].set_value("a-brand-new-password")
    form["Repeat the new password"].set_value("a-brand-new-password")
    next(b for b in app.button if b.label == "Change password").click().run()
    from account_portal import _TOKEN_KEY
    fresh = app.session_state[_TOKEN_KEY]
    assert store.get_user(fresh)["id"] == user_id


def test_two_different_new_passwords_change_nothing(account):
    store, _, _ = account
    app = page(account)
    form = fields(app)
    form["Current password"].set_value(PASSWORD)
    form["New password"].set_value("a-brand-new-password")
    form["Repeat the new password"].set_value("a-different-password-1")
    next(b for b in app.button if b.label == "Change password").click().run()
    assert any("do not match" in item.value for item in app.error)
    assert store.authenticate("resident_one", PASSWORD)


def test_the_wrong_current_password_changes_nothing(account):
    store, _, _ = account
    app = page(account)
    form = fields(app)
    form["Current password"].set_value("not-the-password")
    form["New password"].set_value("a-brand-new-password")
    form["Repeat the new password"].set_value("a-brand-new-password")
    next(b for b in app.button if b.label == "Change password").click().run()
    assert app.error
    assert store.authenticate("resident_one", PASSWORD)


def test_a_short_new_password_is_refused(account):
    store, _, _ = account
    app = page(account)
    form = fields(app)
    form["Current password"].set_value(PASSWORD)
    form["New password"].set_value("short")
    form["Repeat the new password"].set_value("short")
    next(b for b in app.button if b.label == "Change password").click().run()
    assert app.error
    assert store.authenticate("resident_one", PASSWORD)
