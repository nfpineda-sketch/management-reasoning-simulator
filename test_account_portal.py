"""Real Streamlit account-gate regressions; all accounts use temporary SQLite."""

import pytest
from streamlit.testing.v1 import AppTest

from account_store import AccountStore, hash_password


APP = """
import streamlit as st
from account_portal import accounts_enabled, require_account_access, render_account_sidebar
if accounts_enabled():
    context = require_account_access()
    render_account_sidebar(context)
    st.success('Authenticated: ' + context['user']['username'])
    st.write('Role: ' + context['user']['role'])
else:
    st.write('Legacy gate selected')
"""
ADMIN_PASSWORD = "portal-test-admin-password"
RESIDENT_PASSWORD = "portal-test-resident-password"


@pytest.fixture(scope="module")
def admin_hash():
    return hash_password(ADMIN_PASSWORD)


@pytest.fixture
def configuration(tmp_path, admin_hash):
    return {
        "MRS_AUTH_MODE": "accounts",
        "MRS_DATABASE_URL": "sqlite:///" + str(tmp_path / "accounts.sqlite3"),
        "MRS_ALLOW_LOCAL_SQLITE": True,
        "MRS_ADMIN_USERNAME": "admin",
        "MRS_ADMIN_PASSWORD_HASH": admin_hash,
    }


def portal(configuration):
    app = AppTest.from_string(APP, default_timeout=15)
    app.secrets.update(configuration)
    app.run()
    assert not app.exception
    return app


def widget(app, kind, label):
    return next(item for item in getattr(app, kind) if item.label == label)


def sign_in(app, username, password):
    widget(app, "text_input", "Username").set_value(username)
    widget(app, "text_input", "Password").set_value(password)
    widget(app, "button", "Sign in").click().run()
    assert not app.exception


def register(app, username, invitation):
    widget(app, "text_input", "Invitation code").set_value(invitation)
    widget(app, "text_input", "Choose a username").set_value(username)
    widget(app, "text_input", "Choose a password").set_value(RESIDENT_PASSWORD)
    widget(app, "text_input", "Confirm password").set_value(RESIDENT_PASSWORD)
    widget(app, "button", "Create account").click().run()
    assert not app.exception


def test_auth_modes_fail_closed():
    shared = AppTest.from_string(APP).run()
    assert "Legacy gate selected" in shared.markdown[0].value
    unknown = AppTest.from_string(APP)
    unknown.secrets["MRS_AUTH_MODE"] = "account"
    unknown.run()
    assert unknown.error
    assert not unknown.markdown
    missing_database = AppTest.from_string(APP)
    missing_database.secrets["MRS_AUTH_MODE"] = "accounts"
    missing_database.run()
    assert missing_database.error
    assert not missing_database.text_input


def test_login_and_logout_remove_previous_clinical_state(configuration):
    app = portal(configuration)
    app.session_state["state"] = {"patient": "previous user's case"}
    app.session_state["_shared_access_granted"] = True
    sign_in(app, "admin", ADMIN_PASSWORD)
    assert any(item.value == "Authenticated: admin" for item in app.success)
    assert "state" not in app.session_state
    assert "_shared_access_granted" not in app.session_state
    session = app.session_state["_account_token"]
    app.session_state["state"] = {"patient": "current user's case"}
    widget(app, "button", "Sign out").click().run()
    assert not app.exception
    assert "_account_token" not in app.session_state
    assert "state" not in app.session_state
    store = AccountStore(configuration["MRS_DATABASE_URL"], allow_sqlite=True)
    assert store.get_user(session) is None
    assert widget(app, "button", "Sign in")


def test_invited_registration_assigns_role_and_revocation_removes_access(configuration):
    admin = portal(configuration)
    sign_in(admin, "admin", ADMIN_PASSWORD)
    widget(admin, "selectbox", "Invite role").set_value("resident")
    widget(admin, "selectbox", "Training year").set_value(2)
    widget(admin, "button", "Create invitation").click().run()
    assert not admin.exception
    invitation = admin.code[0].value

    learner = portal(configuration)
    register(learner, "resident.one", invitation)
    assert any(item.value == "Authenticated: resident.one" for item in learner.success)
    assert not any(item.label == "Account administration" for item in learner.expander)
    store = AccountStore(configuration["MRS_DATABASE_URL"], allow_sqlite=True)
    learner_token = learner.session_state["_account_token"]
    learner_user = store.get_user(learner_token)
    assert learner_user["role"] == "resident"
    assert learner_user["training_year"] == 2

    reused = portal(configuration)
    register(reused, "resident.two", invitation)
    assert reused.error
    assert "_account_token" not in reused.session_state

    # Admin edits use the real controls and revoke an already signed-in learner.
    admin.run()
    widget(admin, "selectbox", "Manage an account").set_value(learner_user["id"]).run()
    widget(admin, "checkbox", "Account active").uncheck()
    widget(admin, "button", "Save account").click().run()
    assert not admin.exception
    learner.session_state["state"] = {"patient": "private clinical data"}
    learner.run()
    assert not learner.exception
    assert "_account_token" not in learner.session_state
    assert "state" not in learner.session_state
    assert widget(learner, "button", "Sign in")


def test_bad_credentials_do_not_start_a_session(configuration):
    app = portal(configuration)
    sign_in(app, "admin", "incorrect-password")
    assert app.error
    assert "_account_token" not in app.session_state
    assert not app.success
