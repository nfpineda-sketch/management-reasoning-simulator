"""Learner analysis persistence is owner-scoped and never changes frozen evidence."""

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import time
import uuid

import pytest

from account_store import AccountError, AccountStore
from faculty_analysis_store import FacultyBriefStore
from management_trace_store import ManagementTraceStore, analysis_payload_from_session
from test_management_trace_analysis import sample_payload, sample_report


@pytest.fixture
def cohort(tmp_path):
    accounts = AccountStore(f"sqlite:///{tmp_path / 'accounts.sqlite3'}", allow_sqlite=True)
    users = {}
    with accounts._transaction(write=True) as connection:
        for username, role, year in (("admin", "admin", None), ("faculty", "faculty", None),
                                     ("resident", "resident", 1), ("other", "resident", 2)):
            user_id = uuid.uuid4().hex
            accounts._execute(connection, "INSERT INTO mrs_users VALUES (?, ?, ?, ?, ?, 1, ?)",
                              (user_id, username, "unused-fixture-password-hash", role, year, int(time.time())))
            users[username] = {"id": user_id, "token": accounts._new_session(connection, user_id)}
    return accounts, ManagementTraceStore(accounts), users


def session_payload(source=None):
    source = source or sample_payload()
    return {"schema_version": "mrs_attempt_v1", "session": {
        "encounter_ended": source["encounter_ended"],
        "expert_comparison_unlocked": source["reflection_locked"],
        "encounter_closed_trace": deepcopy(source["trace"]),
        "management_trace": deepcopy(source["trace"]),
        "precomparison_decision_review": deepcopy(source["reflections"]),
        "review_prompts": deepcopy(source["reflection_prompts"]),
        "review_completed": True,
    }}


def current_report(cohort, *, completed=True):
    accounts, store, users = cohort
    token = users["resident"]["token"]
    attempt_id = accounts.create_attempt(token, "R1-05", {"presentation": "Synthetic test encounter"})
    payload = session_payload()
    accounts.save_attempt(token, attempt_id, payload, status="completed" if completed else "active")
    return attempt_id, sample_report(), payload


def stored_rows(accounts):
    with accounts._transaction() as connection:
        return [dict(row) for row in accounts._execute(connection,
            "SELECT * FROM mrs_learner_trace_analyses ORDER BY created_at, id").fetchall()]


def test_session_adapter_selects_only_frozen_evidence_and_locked_original_reflection():
    payload = session_payload()
    session = payload["session"]
    session.update(management_trace=[{"live_trace": "DO_NOT_USE"}],
                   decision_review={"later_reflection": "DO_NOT_USE"},
                   expert_comparison_responses={"private_comparison": "DO_NOT_USE"},
                   faculty_assessment={"notes": "DO_NOT_USE"})
    original = deepcopy(session)
    adapted = analysis_payload_from_session(session)
    assert adapted == {**sample_payload(), "encounter_events": []}
    adapted["trace"][0]["learner_input"] = "Changed copy"
    assert session == original


def test_owner_can_save_and_read_analysis_without_changing_completed_encounter(cohort):
    accounts, store, users = cohort
    attempt_id, report, _ = current_report(cohort)
    token = users["resident"]["token"]
    before = accounts.get_attempt(token, attempt_id)
    assert store.get_latest(token, attempt_id) is None
    assert store.save(token, attempt_id, report) == report
    assert store.get_latest(token, attempt_id) == report
    assert store.get_latest(users["faculty"]["token"], attempt_id) == report
    assert store.get_latest(users["admin"]["token"], attempt_id) == report
    assert accounts.get_attempt(token, attempt_id) == before
    row = stored_rows(accounts)[0]
    assert row["attempt_id"] == attempt_id
    assert row["creator_user_id"] == users["resident"]["id"]
    assert row["source_hash"] == report["source_hash"]


def test_other_resident_cannot_read_or_write_someone_elses_analysis(cohort):
    accounts, store, users = cohort
    attempt_id, report, _ = current_report(cohort)
    store.save(users["resident"]["token"], attempt_id, report)
    for operation in (lambda: store.get_latest(users["other"]["token"], attempt_id),
                      lambda: store.save(users["other"]["token"], attempt_id, report)):
        with pytest.raises(AccountError, match="not available"):
            operation()
    assert len(stored_rows(accounts)) == 1


@pytest.mark.parametrize("revocation", ["logout", "disabled", "expired"])
def test_cached_report_operations_recheck_current_owner_session(cohort, revocation):
    accounts, store, users = cohort
    attempt_id, report, _ = current_report(cohort)
    owner = users["resident"]
    store.save(owner["token"], attempt_id, report)
    if revocation == "logout":
        accounts.logout(owner["token"])
    elif revocation == "disabled":
        accounts.update_user(users["admin"]["token"], owner["id"], active=False)
    else:
        with accounts._transaction(write=True) as connection:
            accounts._execute(connection, "UPDATE mrs_sessions SET expires_at = 0 WHERE user_id = ?", (owner["id"],))
    for operation in (lambda: store.get_latest(owner["token"], attempt_id),
                      lambda: store.save(owner["token"], attempt_id, report)):
        with pytest.raises(AccountError, match="sign in"):
            operation()
    assert len(stored_rows(accounts)) == 1


def test_staff_cannot_keep_access_after_role_becomes_another_resident(cohort):
    accounts, store, users = cohort
    attempt_id, report, _ = current_report(cohort)
    store.save(users["faculty"]["token"], attempt_id, report)
    accounts.update_user(users["admin"]["token"], users["faculty"]["id"], role="resident", training_year=1)
    with pytest.raises(AccountError):
        store.get_latest(users["faculty"]["token"], attempt_id)


def test_source_change_invalidates_persisted_cache_and_rejects_old_generated_report(cohort):
    accounts, store, users = cohort
    attempt_id, report, payload = current_report(cohort, completed=False)
    token = users["resident"]["token"]
    store.save(token, attempt_id, report)
    payload["session"]["precomparison_decision_review"]["decision-1"]["working_model_update"] = "Changed before finalization."
    accounts.save_attempt(token, attempt_id, payload)
    assert store.get_latest(token, attempt_id) is None
    with pytest.raises(AccountError, match="no longer matches"):
        store.save(token, attempt_id, report)
    assert len(stored_rows(accounts)) == 1


def test_new_analysis_after_later_plan_does_not_invalidate_original_frozen_source(cohort):
    accounts, store, users = cohort
    attempt_id, report, payload = current_report(cohort, completed=False)
    token = users["resident"]["token"]
    store.save(token, attempt_id, report)
    payload["session"]["adaptation_plan"] = {"next_priority": "A later prospective plan."}
    payload["session"]["expert_comparison_responses"] = {"alignment": "A later comparison."}
    accounts.save_attempt(token, attempt_id, payload, status="completed")
    before = accounts.get_attempt(token, attempt_id)
    assert store.get_latest(token, attempt_id) == report
    store.save(token, attempt_id, report)
    assert accounts.get_attempt(token, attempt_id) == before


@pytest.mark.parametrize("field", ["encounter_ended", "expert_comparison_unlocked"])
def test_unclosed_or_unlocked_encounter_cannot_use_analysis_store(cohort, field):
    accounts, store, users = cohort
    attempt_id, report, payload = current_report(cohort, completed=False)
    payload["session"][field] = False
    token = users["resident"]["token"]
    accounts.save_attempt(token, attempt_id, payload)
    for operation in (lambda: store.get_latest(token, attempt_id),
                      lambda: store.save(token, attempt_id, report)):
        with pytest.raises(AccountError, match="lock"):
            operation()
    assert stored_rows(accounts) == []


def test_report_from_different_source_cannot_be_substituted(cohort):
    accounts, store, users = cohort
    attempt_id, report, _ = current_report(cohort)
    changed = sample_payload()
    changed["trace"][0]["state_after"]["observable"]["hr"] = 98
    with pytest.raises(AccountError, match="no longer matches"):
        store.save(users["resident"]["token"], attempt_id, sample_report(changed))
    assert stored_rows(accounts) == []


def test_learner_analysis_never_grants_access_to_private_faculty_documents(cohort):
    accounts, store, users = cohort
    attempt_id, report, _ = current_report(cohort)
    store.save(users["resident"]["token"], attempt_id, report)
    faculty_store = FacultyBriefStore(accounts)
    for actor in ("resident", "other"):
        with pytest.raises(AccountError, match="permission"):
            faculty_store.get_latest(users[actor]["token"], attempt_id)


def test_persisted_analysis_survives_new_process_without_source_mutation(cohort):
    accounts, store, users = cohort
    attempt_id, report, _ = current_report(cohort)
    token = users["resident"]["token"]
    before = accounts.get_attempt(token, attempt_id)
    store.save(token, attempt_id, report)
    process = subprocess.run([sys.executable, "-c", """
import json, sys
from account_store import AccountStore
from management_trace_store import ManagementTraceStore
args = json.loads(sys.stdin.read())
store = ManagementTraceStore(AccountStore(args['url'], allow_sqlite=True))
print(json.dumps(store.get_latest(args['token'], args['attempt_id'])))
"""], input=json.dumps({"url": accounts._url, "token": token, "attempt_id": attempt_id}),
        text=True, capture_output=True, check=True, cwd=Path(__file__).resolve().parent)
    assert json.loads(process.stdout) == report
    assert accounts.get_attempt(token, attempt_id) == before


def test_corrupt_stored_analysis_is_not_returned_as_valid(cohort):
    accounts, store, users = cohort
    attempt_id, report, _ = current_report(cohort)
    token = users["resident"]["token"]
    store.save(token, attempt_id, report)
    with accounts._transaction(write=True) as connection:
        accounts._execute(connection, "UPDATE mrs_learner_trace_analyses SET report_json = ?", ("{}",))
    with pytest.raises(AccountError, match="generated again"):
        store.get_latest(token, attempt_id)
