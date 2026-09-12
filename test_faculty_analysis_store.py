"""Private draft authorization, source binding and persistence contracts."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import time
import uuid

import pytest

from account_store import AccountError, AccountStore
from faculty_analysis import source_fingerprint
from faculty_analysis_store import FacultyBriefStore
from objectives import OBJECTIVES
from progress_store import ProgressStore


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
    return accounts, FacultyBriefStore(accounts), users


def completed_attempt(accounts, token, *, status="completed", review_completed=True):
    attempt_id = accounts.create_attempt(token, "R1-03", {"presentation": "Synthetic test encounter"})
    payload = {
        "schema_version": "mrs_attempt_v1",
        "session": {"review_completed": review_completed, "management_trace": [
            {"execution_status": "executed", "learner_input": "Reassess the patient in three minutes.",
             "decision_time_min": 0, "response_time_min": 3,
             "reasoning": {"problem_representation": "A synthetic working model"},
             "state_before": {"observable": {"mental_status": "alert"}},
             "state_after": {"observable": {"mental_status": "alert"}}}
        ]},
    }
    accounts.save_attempt(token, attempt_id, payload, status=status)
    return attempt_id


def brief(record, assistance_context="unknown"):
    return {
        "schema_version": "faculty_brief_v1", "prompt_version": "1.0",
        "attempt_id": record["id"], "attempt_revision": record["revision"],
        "source_hash": source_fingerprint(record), "generated_at": "2026-09-12T17:00:00+00:00",
        "model": "fixture-model", "assistance_context": assistance_context,
        "analysis": {
            "summary": "The saved synthetic encounter supports faculty review of a reassessment decision.",
            "strengths": ["A reassessment interval was recorded."],
            "review_points": ["Ask how the reassessment would inform a subsequent priority."],
            "key_decisions": [{"evidence_refs": ["trace:0"],
                               "analysis": "The learner requested reassessment.",
                               "question": "Which change would alter your priority?"}],
            "objectives": [{"objective_id": objective_id, "recommendation": "insufficient_evidence",
                            "rationale": "This short synthetic record cannot establish satisfactory performance.",
                            "depth": None, "autonomy": None, "context": "Synthetic reassessment",
                            "evidence_refs": [], "feedback": "Review a fuller encounter.",
                            "questions": ["What would determine the next action?"]}
                           for objective_id, definition in OBJECTIVES.items() if definition["supported"]],
            "learning_cycle": "Only the recorded reassessment is available; reflection is not inferred.",
            "limits": ["This generated draft does not register an assessment or establish competence."],
        },
    }


def current_brief(cohort, assistance_context="unknown"):
    accounts, store, users = cohort
    attempt_id = completed_attempt(accounts, users["resident"]["token"])
    record = accounts.get_attempt(users["faculty"]["token"], attempt_id)
    return attempt_id, brief(record, assistance_context)


def rows(accounts):
    with accounts._transaction() as connection:
        return [dict(row) for row in accounts._execute(connection,
            "SELECT * FROM mrs_faculty_briefs ORDER BY created_at, id").fetchall()]


def test_draft_is_durable_in_new_process_and_never_changes_progress_or_source(cohort):
    accounts, store, users = cohort
    attempt_id, report = current_brief(cohort)
    original = accounts.get_attempt(users["resident"]["token"], attempt_id)
    progress = ProgressStore(accounts)
    before = progress.get_progress(users["resident"]["token"])
    saved = store.save(users["faculty"]["token"], attempt_id, report)
    assert store.get_latest(users["admin"]["token"], attempt_id) == saved
    assert accounts.get_attempt(users["resident"]["token"], attempt_id) == original
    assert progress.get_progress(users["resident"]["token"]) == before
    # Spawn a separate interpreter rather than merely reusing the store object.
    process = subprocess.run([sys.executable, "-c", """
import json, sys
from account_store import AccountStore
from faculty_analysis_store import FacultyBriefStore
args = json.loads(sys.stdin.read())
store = FacultyBriefStore(AccountStore(args['url'], allow_sqlite=True))
print(json.dumps(store.get_latest(args['token'], args['attempt_id'])))
"""], input=json.dumps({"url": accounts._url, "token": users["faculty"]["token"],
                        "attempt_id": attempt_id}), text=True, capture_output=True, check=True,
                            cwd=Path(__file__).resolve().parent)
    assert json.loads(process.stdout) == saved
    stored = rows(accounts)[0]
    assert stored["generator_user_id"] == users["faculty"]["id"]
    assert stored["attempt_revision"] == original["revision"]
    assert stored["prompt_version"] == report["prompt_version"]
    assert stored["model"] == report["model"]
    assert stored["generated_at"] == report["generated_at"]
    assert "brief_id" not in json.loads(stored["report_json"])


@pytest.mark.parametrize("actor", ["resident", "other"])
def test_learner_cannot_read_or_write_even_own_report(cohort, actor):
    accounts, store, users = cohort
    attempt_id, report = current_brief(cohort)
    store.save(users["faculty"]["token"], attempt_id, report)
    for action in (lambda: store.get_latest(users[actor]["token"], attempt_id),
                   lambda: store.save(users[actor]["token"], attempt_id, report)):
        with pytest.raises(AccountError, match="permission"):
            action()
    assert len(rows(accounts)) == 1


@pytest.mark.parametrize("revocation", ["logout", "disabled", "role_changed", "expired"])
def test_revocation_between_generation_and_save_blocks_read_and_save(cohort, revocation):
    accounts, store, users = cohort
    attempt_id, report = current_brief(cohort)
    faculty = users["faculty"]
    store.save(faculty["token"], attempt_id, report)
    if revocation == "logout":
        accounts.logout(faculty["token"])
    elif revocation == "disabled":
        accounts.update_user(users["admin"]["token"], faculty["id"], active=False)
    elif revocation == "role_changed":
        accounts.update_user(users["admin"]["token"], faculty["id"], role="resident", training_year=1)
    else:
        with accounts._transaction(write=True) as connection:
            accounts._execute(connection, "UPDATE mrs_sessions SET expires_at = 0 WHERE user_id = ?",
                              (faculty["id"],))
    for action in (lambda: store.get_latest(faculty["token"], attempt_id),
                   lambda: store.save(faculty["token"], attempt_id, report)):
        with pytest.raises(AccountError, match="sign in"):
            action()
    assert len(rows(accounts)) == 1


@pytest.mark.parametrize("kind", ["active", "abandoned", "sandbox", "unreflected", "missing"])
def test_only_finalized_resident_records_support_private_analysis(cohort, kind):
    accounts, store, users = cohort
    if kind == "missing":
        attempt_id = "missing"
    else:
        owner = "faculty" if kind == "sandbox" else "resident"
        attempt_id = completed_attempt(accounts, users[owner]["token"],
                                       status=kind if kind in {"active", "abandoned"} else "completed",
                                       review_completed=kind != "unreflected")
    for action in (lambda: store.get_latest(users["admin"]["token"], attempt_id),
                   lambda: store.save(users["admin"]["token"], attempt_id, {})):
        with pytest.raises(AccountError, match="completed"):
            action()
    assert rows(accounts) == []


def test_new_drafts_append_and_assistance_context_has_separate_cache(cohort):
    accounts, store, users = cohort
    attempt_id, report = current_brief(cohort)
    token = users["faculty"]["token"]
    assert store.get_latest(token, attempt_id) is None
    unknown = store.save(token, attempt_id, report)
    original_row = rows(accounts)[0]
    report["assistance_context"] = "guided"
    guided = store.save(token, attempt_id, report)
    assert store.get_latest(token, attempt_id, "unknown") == unknown
    assert store.get_latest(token, attempt_id, "guided") == guided
    assert store.get_latest(token, attempt_id, "independent") is None
    assert store.get_latest(token, attempt_id) == guided
    report["analysis"]["summary"] = "Revised draft, retained separately from the original."
    latest = store.save(token, attempt_id, report)
    assert latest["brief_id"] != guided["brief_id"]
    assert store.get_latest(token, attempt_id, "guided") == latest
    assert rows(accounts)[0] == original_row
    assert len(rows(accounts)) == 3


@pytest.mark.parametrize("change", ["revision", "payload", "encounter"])
def test_stale_source_never_loads_or_saves_and_prior_draft_is_retained(cohort, change):
    accounts, store, users = cohort
    attempt_id, report = current_brief(cohort)
    token = users["faculty"]["token"]
    store.save(token, attempt_id, report)
    original_row = rows(accounts)[0]
    # Trusted fixture emulates an out-of-band correction while generation was
    # in flight. Public AccountStore correctly disallows edits to closed cases.
    with accounts._transaction(write=True) as connection:
        if change == "revision":
            accounts._execute(connection, "UPDATE mrs_attempts SET revision = revision + 1 WHERE id = ?",
                              (attempt_id,))
        elif change == "payload":
            record = accounts._execute(connection, "SELECT payload_json FROM mrs_attempts WHERE id = ?",
                                       (attempt_id,)).fetchone()
            payload = json.loads(record["payload_json"])
            payload["session"]["management_trace"][0]["learner_input"] = "A changed decision."
            accounts._execute(connection, "UPDATE mrs_attempts SET payload_json = ? WHERE id = ?",
                              (json.dumps(payload), attempt_id))
        else:
            accounts._execute(connection, "UPDATE mrs_attempts SET encounter_json = ? WHERE id = ?",
                              (json.dumps({"presentation": "Changed source"}), attempt_id))
    assert store.get_latest(token, attempt_id) is None
    with pytest.raises(AccountError, match="changed after analysis"):
        store.save(token, attempt_id, report)
    assert rows(accounts) == [original_row]


def test_changed_owner_role_removes_access_to_previously_generated_brief(cohort):
    accounts, store, users = cohort
    attempt_id, report = current_brief(cohort)
    token = users["faculty"]["token"]
    store.save(token, attempt_id, report)
    accounts.update_user(users["admin"]["token"], users["resident"]["id"], role="faculty")
    with pytest.raises(AccountError, match="resident encounter"):
        store.get_latest(token, attempt_id)
    with pytest.raises(AccountError, match="resident encounter"):
        store.save(token, attempt_id, report)


def test_invalid_ai_output_rolls_back_and_existing_private_draft_remains(cohort):
    accounts, store, users = cohort
    attempt_id, report = current_brief(cohort)
    token = users["faculty"]["token"]
    saved = store.save(token, attempt_id, report)
    invalid = deepcopy(report)
    invalid["analysis"]["key_decisions"][0]["evidence_refs"] = ["trace:999"]
    with pytest.raises(AccountError):
        store.save(token, attempt_id, invalid)
    assert store.get_latest(token, attempt_id) == saved
    assert len(rows(accounts)) == 1


def test_deserialized_mutation_and_client_brief_id_cannot_overwrite_saved_draft(cohort):
    accounts, store, users = cohort
    attempt_id, report = current_brief(cohort)
    token = users["faculty"]["token"]
    first = store.save(token, attempt_id, report)
    mutated = deepcopy(first)
    mutated["analysis"]["summary"] = "This is a new draft without changing the previous draft."
    second = store.save(token, attempt_id, mutated)
    assert second["brief_id"] != first["brief_id"]
    assert json.loads(rows(accounts)[0]["report_json"])["analysis"]["summary"] == report["analysis"]["summary"]
