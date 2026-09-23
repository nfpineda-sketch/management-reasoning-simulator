"""The photograph is asked about at the start, and refusing it costs nothing.

Faculty, 2026-09-23: it should be configured when the account is created
rather than hidden in a page a resident may never open. Asked once, then.

But it is a step, not a toll. The agreement the resident signs says that
withdrawing the photograph does not affect their standing in the programme; a
wall that stopped them training until they agreed would contradict that in the
same breath, and consent obtained that way is not consent. So "Not now" is a
real answer: recorded, never asked again, and costing nothing.
"""
import time
import uuid

import pytest
from streamlit.testing.v1 import AppTest

import resident_portal
import resident_profile
from account_store import AccountStore, hash_password

APP = """
import streamlit as st
from account_store import AccountStore
import resident_portal
store = AccountStore(st.session_state['database_url'], allow_sqlite=True)
token = st.session_state['test_token']
context = {'store': store, 'token': token, 'user': store.get_user(token)}
if resident_portal.needs_setup(context):
    resident_portal.render_setup(context)
    st.session_state['showed'] = 'agreement'
elif resident_portal.needs_photo_step(context):
    resident_portal.render_setup_photo(context)
    st.session_state['showed'] = 'photo'
else:
    st.write('Your next clinical encounter')
    st.session_state['showed'] = 'encounters'
"""


@pytest.fixture
def person(tmp_path):
    store = AccountStore(f"sqlite:///{tmp_path / 'accounts.sqlite3'}", allow_sqlite=True)
    with store._transaction(write=True) as connection:
        user_id = uuid.uuid4().hex
        store._execute(connection, "INSERT INTO mrs_users VALUES (?, ?, ?, ?, ?, 1, ?)",
                       (user_id, "resident_one", hash_password("a-password-for-tests"),
                        "resident", 1, int(time.time())))
        token = store._new_session(connection, user_id)
    return store, token


def page(person):
    store, token = person
    app = AppTest.from_string(APP, default_timeout=20)
    app.session_state["database_url"] = store._url
    app.session_state["test_token"] = token
    app.run()
    assert not app.exception
    return app


def press(app, label):
    return next(button for button in app.button if button.label == label).click().run()


def test_the_agreement_is_the_first_thing_a_new_resident_sees(person):
    app = page(person)
    assert app.session_state["showed"] == "agreement"
    assert "Set up your account" in [item.value for item in app.subheader]
    assert "I have read this and agree" in [button.label for button in app.button]
    assert "Not now" in [button.label for button in app.button]


def test_the_agreement_text_is_on_that_screen(person):
    app = page(person)
    assert any("photograph of your face" in item.value for item in app.markdown)


def test_agreeing_moves_on_to_the_photograph(person):
    app = page(person)
    press(app, "I have read this and agree")
    assert app.session_state["showed"] == "photo"
    assert "Continue to my encounters" in [button.label for button in app.button]


def test_the_photograph_step_can_be_passed_without_one(person):
    app = page(person)
    press(app, "I have read this and agree")
    press(app, "Continue to my encounters")
    assert app.session_state["showed"] == "encounters"


def test_not_now_goes_straight_to_the_encounters(person):
    app = page(person)
    press(app, "Not now")
    assert app.session_state["showed"] == "encounters"


def test_not_now_is_never_asked_again(person):
    store, token = person
    app = page(person)
    press(app, "Not now")
    assert page(person).session_state["showed"] == "encounters"
    assert resident_profile.ProfileStore(store).decision(token) == "declined"


def test_not_now_stores_nothing_and_blocks_nothing(person):
    store, token = person
    app = page(person)
    press(app, "Not now")
    profile = resident_profile.ProfileStore(store).get(token)
    assert profile["photo"] == "" and profile["initials"] == ""
    # The encounter page is what they reach, which is the whole point.
    assert any("Your next clinical encounter" in item.value for item in page(person).markdown)


def test_agreeing_and_storing_one_ends_the_setup(person):
    store, token = person
    profiles = resident_profile.ProfileStore(store)
    profiles.accept(token)
    profiles.save(token, initials="NP")
    assert page(person).session_state["showed"] == "encounters"


def test_a_faculty_member_is_never_asked(person):
    store, _ = person
    with store._transaction(write=True) as connection:
        user_id = uuid.uuid4().hex
        store._execute(connection, "INSERT INTO mrs_users VALUES (?, ?, ?, ?, ?, 1, ?)",
                       (user_id, "faculty_one", hash_password("a-password-for-tests"),
                        "faculty", None, int(time.time())))
        token = store._new_session(connection, user_id)
    app = AppTest.from_string(APP, default_timeout=20)
    app.session_state["database_url"] = store._url
    app.session_state["test_token"] = token
    app.run()
    assert not app.exception
    assert app.session_state["showed"] == "encounters"


def test_the_screen_says_that_declining_costs_nothing(person):
    app = page(person)
    said = " ".join(item.value for item in app.caption)
    assert "changes nothing else" in said
    assert "begin encounters immediately" in said
