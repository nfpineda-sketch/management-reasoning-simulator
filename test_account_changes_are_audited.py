"""Who changed an account, and when (TD-44, §154EI; cycle 10, C10-04, Phase 2 step 1).

Activating or deactivating an account, or changing its role or year, is written with its author
and time in the same transaction as the change; only an administrator reads it, and nothing is
written when nothing changed.
"""
import time
import uuid
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from account_store import AccountError, AccountStore

APP = str(Path(__file__).with_name("app.py"))


@pytest.fixture
def people(tmp_path, monkeypatch):
    AccountStore.forget_schemas()
    url = f"sqlite:///{tmp_path / 'accounts.sqlite3'}"
    accounts = AccountStore(url, allow_sqlite=True)
    users = {}
    with accounts._transaction(write=True) as connection:
        for username, role, year in (("admin_test", "admin", None), ("faculty_test", "faculty", None),
                                     ("resident_test", "resident", 1)):
            user_id = uuid.uuid4().hex
            accounts._execute(connection, "INSERT INTO mrs_users VALUES (?, ?, ?, ?, ?, 1, ?)",
                              (user_id, username, "unused-fixture-hash", role, year, int(time.time())))
            users[username] = {"id": user_id, "token": accounts._new_session(connection, user_id)}
    monkeypatch.setenv("MRS_AUTH_MODE", "accounts")
    monkeypatch.setenv("MRS_DATABASE_URL", url)
    monkeypatch.setenv("MRS_ALLOW_LOCAL_SQLITE", "true")
    monkeypatch.setenv("MRS_OFFLINE_CASES", "1")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    return accounts, users


def test_changes_within_one_second_still_list_newest_first(people, monkeypatch):
    """The full suite of cycle 10 once listed them the other way: the tie was broken by a random id."""
    import account_store
    accounts, users = people
    admin, resident = users["admin_test"]["token"], users["resident_test"]["id"]
    frozen = int(time.time())
    monkeypatch.setattr(account_store.time, "time", lambda: float(frozen))
    for year in (2, 3, 1, 2, 3):
        accounts.update_user(admin, resident, training_year=year)
    changes = [item["changes"]["training_year"] for item in accounts.account_changes(admin)]
    assert changes == [[2, 3], [1, 2], [3, 1], [2, 3], [1, 2]]
    assert {item["at"] for item in accounts.account_changes(admin)} == {frozen}


def test_deactivating_and_reactivating_is_written_with_its_author_and_time(people):
    accounts, users = people
    admin = users["admin_test"]["token"]
    before = int(time.time())
    accounts.update_user(admin, users["resident_test"]["id"], active=False)
    accounts.update_user(admin, users["resident_test"]["id"], active=True)
    changes = accounts.account_changes(admin)
    assert [item["changes"] for item in changes] == [{"active": [False, True]}, {"active": [True, False]}]
    assert {item["account"] for item in changes} == {"resident_test"}
    assert {item["changed_by"] for item in changes} == {"admin_test"}
    assert all(item["at"] >= before for item in changes)


def test_role_and_year_changes_are_written_and_a_save_without_change_is_not(people):
    accounts, users = people
    admin = users["admin_test"]["token"]
    accounts.update_user(admin, users["resident_test"]["id"], role="resident", training_year=2, active=True)
    accounts.update_user(admin, users["resident_test"]["id"], role="resident", training_year=2, active=True)
    [change] = accounts.account_changes(admin)
    assert change["changes"] == {"training_year": [1, 2]}


def test_a_refused_change_writes_nothing(people):
    accounts, users = people
    admin = users["admin_test"]["token"]
    with pytest.raises(AccountError, match="active administrator"):
        accounts.update_user(admin, users["admin_test"]["id"], active=False)
    assert accounts.account_changes(admin) == []


@pytest.mark.parametrize("who", ["faculty_test", "resident_test"])
def test_only_an_administrator_reads_the_history(people, who):
    accounts, users = people
    accounts.update_user(users["admin_test"]["token"], users["resident_test"]["id"], active=False)
    with pytest.raises(AccountError):
        accounts.account_changes(users[who]["token"])
    with pytest.raises(AccountError):
        accounts.update_user(users[who]["token"], users["resident_test"]["id"], active=True)


def test_the_administrator_sees_the_history_and_the_resident_page_never_shows_it(people):
    accounts, users = people
    accounts.update_user(users["admin_test"]["token"], users["faculty_test"]["id"], role="faculty", active=False)
    at = AppTest.from_file(APP, default_timeout=120)
    at.session_state["_account_token"] = users["admin_test"]["token"]
    at.run()
    assert not at.exception
    labels = [expander.label for expander in at.expander]
    assert "Account change history" in labels
    shown = " ".join(str(frame.value) for frame in at.dataframe)
    assert "faculty_test" in shown and "Active → Inactive" in shown
    resident = AppTest.from_file(APP, default_timeout=120)
    resident.session_state["_account_token"] = users["resident_test"]["token"]
    resident.run()
    assert not resident.exception
    assert "Account change history" not in [expander.label for expander in resident.expander]
