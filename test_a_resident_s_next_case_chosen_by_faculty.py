"""A faculty member chooses a resident's next case, and the record says so.

The synthetic batch of 2026-09-24 needs twenty chosen, tested cases played by
a real resident account through the real circuit; until now nothing but the
curriculum could choose a resident's case. A directive is one-shot, explicit,
reasoned and kept: the curriculum's own rule is untouched when there is none.
"""
import time
import uuid
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from account_store import AccountError, AccountStore
from encounter_directives import DirectiveStore, case_options

APP = str(Path(__file__).with_name("app.py"))


@pytest.fixture
def cohort(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'accounts.sqlite3'}"
    accounts = AccountStore(url, allow_sqlite=True)
    users = {}
    with accounts._transaction(write=True) as connection:
        for username, role, year in (("faculty_test", "faculty", None), ("admin_test", "admin", None),
                                     ("residente_prueba_r3", "resident", 3), ("other_test", "resident", 2)):
            user_id = uuid.uuid4().hex
            accounts._execute(connection, "INSERT INTO mrs_users VALUES (?, ?, ?, ?, ?, 1, ?)",
                              (user_id, username, "unused-fixture-hash", role, year, int(time.time())))
            users[username] = {"id": user_id, "token": accounts._new_session(connection, user_id)}
    monkeypatch.setenv("MRS_AUTH_MODE", "accounts")
    monkeypatch.setenv("MRS_DATABASE_URL", url)
    monkeypatch.setenv("MRS_ALLOW_LOCAL_SQLITE", "true")
    monkeypatch.setenv("MRS_OFFLINE_CASES", "1")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("MRS_DEFAULT_VARIANT", raising=False)
    return accounts, users


def test_a_challenge_offers_only_its_own_cases():
    cases = {variant for variant, _, _ in case_options("R2-05")}
    assert "gi_bleed_72f" in cases and "renal_colic_34m" in cases
    assert "asthma_24f" not in cases
    assert case_options("nonexistent") == []


def test_only_staff_direct_and_always_with_a_reason(cohort):
    accounts, users = cohort
    store = DirectiveStore(accounts)
    resident = users["residente_prueba_r3"]["id"]
    with pytest.raises(AccountError):
        store.direct(users["other_test"]["token"], resident, "R2-05", "gi_bleed_72f", "x")
    with pytest.raises(AccountError, match="why"):
        store.direct(users["faculty_test"]["token"], resident, "R2-05", "gi_bleed_72f", "  ")
    with pytest.raises(AccountError, match="not one this challenge offers"):
        store.direct(users["faculty_test"]["token"], resident, "R2-05", "asthma_24f", "Batch")
    with pytest.raises(AccountError, match="resident"):
        store.direct(users["faculty_test"]["token"], users["admin_test"]["id"], "R2-05",
                     "gi_bleed_72f", "Batch")


def test_a_new_directive_replaces_the_waiting_one_and_both_are_kept(cohort):
    accounts, users = cohort
    store = DirectiveStore(accounts)
    resident = users["residente_prueba_r3"]["id"]
    first = store.direct(users["faculty_test"]["token"], resident, "R2-05", "gi_bleed_72f", "Batch 15")
    second = store.direct(users["admin_test"]["token"], resident, "R3-01", "asthma_24f", "Batch 1")
    assert store.waiting(users["residente_prueba_r3"]["token"])["id"] == second["id"]
    states = [(row["id"], row["state"]) for row in store.history(users["admin_test"]["token"], resident)]
    assert states == [(first["id"], "cancelled"), (second["id"], "waiting")]
    # A resident sees only their own; nobody else's.
    assert store.waiting(users["other_test"]["token"]) is None


def test_the_resident_launch_uses_it_once_and_the_encounter_says_so(cohort):
    accounts, users = cohort
    from resident_profile import ProfileStore
    ProfileStore(accounts).decline(users["residente_prueba_r3"]["token"])
    store = DirectiveStore(accounts)
    store.direct(users["faculty_test"]["token"], users["residente_prueba_r3"]["id"],
                 "R2-05", "gi_bleed_72f", "Synthetic batch, scenario 15")
    at = AppTest.from_file(APP, default_timeout=120)
    at.session_state["_account_token"] = users["residente_prueba_r3"]["token"]
    at.run()
    next(button for button in at.button if button.label == "Begin Encounter").click().run()
    assert not at.exception
    spec = at.session_state["state"]["encounter_spec"]
    assert spec["variant_id"] == "gi_bleed_72f"
    assignment = at.session_state["encounter_assignment"]
    assert assignment["reason"] == "faculty_directed"
    assert assignment["directed_by"] == "faculty_test"
    assert assignment["directive_reason"] == "Synthetic batch, scenario 15"
    [row] = store.history(users["admin_test"]["token"], users["residente_prueba_r3"]["id"])
    assert row["state"] == "used" and row["attempt_id"] == at.session_state["_attempt_id"]
    assert store.waiting(users["residente_prueba_r3"]["token"]) is None


def test_without_a_directive_the_curriculum_chooses_as_before(cohort, monkeypatch):
    accounts, users = cohort
    import curriculum_runtime
    chosen = []
    real = curriculum_runtime.assign_challenge

    def spy(*args, **kwargs):
        result = real(*args, **kwargs)
        chosen.append(result)
        return result

    monkeypatch.setattr(curriculum_runtime, "assign_challenge", spy)
    from resident_profile import ProfileStore
    ProfileStore(accounts).decline(users["other_test"]["token"])
    at = AppTest.from_file(APP, default_timeout=120)
    at.session_state["_account_token"] = users["other_test"]["token"]
    at.run()
    next(button for button in at.button if button.label == "Begin Encounter").click().run()
    assert not at.exception
    assert chosen and at.session_state["encounter_assignment"]["reason"] != "faculty_directed"
