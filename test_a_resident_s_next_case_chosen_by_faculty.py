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


def authorize(accounts, users, faculty="faculty_test", resident="residente_prueba_r3"):
    """What an administrator does before a faculty member may choose a resident's cases."""
    return DirectiveStore(accounts).grant(users["admin_test"]["token"], users[faculty]["id"],
                                          users[resident]["id"], "Supervises this resident")


def test_a_challenge_offers_only_its_own_cases():
    cases = {variant for variant, _, _ in case_options("R2-05")}
    assert "gi_bleed_72f" in cases and "renal_colic_34m" in cases
    assert "asthma_24f" not in cases
    assert case_options("nonexistent") == []


def test_only_staff_direct_and_always_with_a_reason(cohort):
    accounts, users = cohort
    authorize(accounts, users)
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
    authorize(accounts, users)
    store = DirectiveStore(accounts)
    resident = users["residente_prueba_r3"]["id"]
    first = store.direct(users["faculty_test"]["token"], resident, "R2-05", "gi_bleed_72f", "Batch 15")
    second = store.direct(users["admin_test"]["token"], resident, "R3-01", "asthma_24f", "Batch 1")
    assert store.waiting(users["residente_prueba_r3"]["token"])["id"] == second["id"]
    states = [(row["id"], row["state"]) for row in store.history(users["admin_test"]["token"], resident)]
    assert states == [(first["id"], "cancelled"), (second["id"], "waiting")]
    # A resident sees only their own; nobody else's.
    assert store.waiting(users["other_test"]["token"]) is None


REVEALING_REASON = "Quiet upper GI bleed: does she resuscitate before the endoscopy"


def _page_text(at):
    texts = []
    for kind in ("markdown", "caption", "info", "success", "warning", "error", "text", "title",
                 "header", "subheader"):
        texts += [str(getattr(element, "value", "")) for element in getattr(at, kind)]
    texts += [str(expander.label) for expander in at.expander]
    return " ".join(texts)


def test_the_resident_launch_uses_it_once_and_the_encounter_says_so(cohort):
    accounts, users = cohort
    authorize(accounts, users)
    from resident_profile import ProfileStore
    ProfileStore(accounts).decline(users["residente_prueba_r3"]["token"])
    store = DirectiveStore(accounts)
    store.direct(users["faculty_test"]["token"], users["residente_prueba_r3"]["id"],
                 "R2-05", "gi_bleed_72f", REVEALING_REASON)
    at = AppTest.from_file(APP, default_timeout=120)
    at.session_state["_account_token"] = users["residente_prueba_r3"]["token"]
    at.run()
    before = _page_text(at)
    next(button for button in at.button if button.label == "Begin Encounter").click().run()
    assert not at.exception
    spec = at.session_state["state"]["encounter_spec"]
    assert spec["variant_id"] == "gi_bleed_72f"
    assignment = at.session_state["encounter_assignment"]
    assert assignment["reason"] == "faculty_directed"
    assert assignment["directed_by"] == "faculty_test"
    # Which code produced the encounter travels with it.
    assert assignment["code_version"] and assignment["runtime_version"]
    [row] = store.history(users["admin_test"]["token"], users["residente_prueba_r3"]["id"])
    assert row["state"] == "used" and row["attempt_id"] == at.session_state["_attempt_id"]
    assert row["reason"] == REVEALING_REASON and assignment["directive_id"] == row["id"]
    assert store.waiting(users["residente_prueba_r3"]["token"]) is None
    # Nothing tells the resident that the case was chosen, which one, or why:
    # the reason is not in their record, and the page says none of it.
    record = accounts.get_attempt(users["residente_prueba_r3"]["token"], at.session_state["_attempt_id"])
    assert REVEALING_REASON not in str(record) and "directive_reason" not in str(record)
    during = _page_text(at)
    for revealing in (REVEALING_REASON, "gi_bleed_72f", "directive", "chose", "chosen", "directed"):
        assert revealing not in before and revealing not in during, revealing


# --- decision 14 of 2026-09-25: scoped permission --------------------------------

def test_a_faculty_member_directs_only_the_residents_an_administrator_authorized(cohort):
    accounts, users = cohort
    store = DirectiveStore(accounts)
    faculty, resident = users["faculty_test"]["token"], users["residente_prueba_r3"]["id"]
    with pytest.raises(AccountError, match="not authorized"):
        store.direct(faculty, resident, "R2-05", "gi_bleed_72f", "Batch")
    assert store.residents_in_scope(faculty) == []
    grant = authorize(accounts, users)
    assert [row["username"] for row in store.residents_in_scope(faculty)] == ["residente_prueba_r3"]
    directive = store.direct(faculty, resident, "R2-05", "gi_bleed_72f", "Batch")
    # Another resident stays out of reach, and out of sight.
    with pytest.raises(AccountError, match="not authorized"):
        store.direct(faculty, users["other_test"]["id"], "R2-05", "gi_bleed_72f", "Batch")
    admin_directive = store.direct(users["admin_test"]["token"], users["other_test"]["id"], "R2-05",
                                   "gi_bleed_72f", "Program choice")
    assert [row["id"] for row in store.waiting(faculty)] == [directive["id"]]
    with pytest.raises(AccountError, match="not authorized"):
        store.history(faculty, users["other_test"]["id"])
    with pytest.raises(AccountError, match="not authorized"):
        store.cancel(faculty, admin_directive["id"])
    # Revoked, the permission ends; the directive and the authorization stay on record.
    store.revoke(users["admin_test"]["token"], grant["id"], "Rotation ended")
    with pytest.raises(AccountError, match="not authorized"):
        store.direct(faculty, resident, "R2-05", "gi_bleed_72f", "Batch")
    [row] = store.grants(users["admin_test"]["token"])
    assert row["active"] is False and row["revoke_reason"] == "Rotation ended"
    assert store.history(users["admin_test"]["token"], resident)[0]["id"] == directive["id"]


def test_only_an_administrator_authorizes_and_always_with_a_reason(cohort):
    accounts, users = cohort
    store = DirectiveStore(accounts)
    faculty, resident = users["faculty_test"]["id"], users["residente_prueba_r3"]["id"]
    with pytest.raises(AccountError):
        store.grant(users["faculty_test"]["token"], faculty, resident, "Myself")
    with pytest.raises(AccountError, match="why"):
        store.grant(users["admin_test"]["token"], faculty, resident, " ")
    with pytest.raises(AccountError, match="faculty member"):
        store.grant(users["admin_test"]["token"], users["other_test"]["id"], resident, "Peer")
    with pytest.raises(AccountError, match="resident"):
        store.grant(users["admin_test"]["token"], faculty, users["admin_test"]["id"], "Admin")
    first = store.grant(users["admin_test"]["token"], faculty, resident, "Supervisor")
    assert first["changed"] and not store.grant(users["admin_test"]["token"], faculty, resident,
                                                "Again")["changed"]


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


def test_the_launch_tells_the_paid_generation_rule_who_is_starting_it(cohort, monkeypatch):
    """With MRS_PAID_GENERATION=admin only an administrator starts a generated case
    (faculty decision B1). The curriculum's launch never said who was starting it,
    so the rule read nobody -- and refused the administrator too."""
    accounts, users = cohort
    import offline_cases
    roles = []
    real = offline_cases.launch_options

    def spy(api_key, role=None):
        roles.append(role)
        return real(api_key, role)

    monkeypatch.setattr(offline_cases, "launch_options", spy)
    from resident_profile import ProfileStore
    ProfileStore(accounts).decline(users["other_test"]["token"])
    at = AppTest.from_file(APP, default_timeout=120)
    at.session_state["_account_token"] = users["other_test"]["token"]
    at.run()
    next(button for button in at.button if button.label == "Begin Encounter").click().run()
    assert not at.exception
    assert roles == ["resident"]
