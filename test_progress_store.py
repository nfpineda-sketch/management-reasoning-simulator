"""Behavioral tests for capped faculty-reviewed simulation evidence."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import time
import uuid

import pytest

from account_store import AccountError, AccountStore
from progress_store import ProgressStore


@pytest.fixture
def cohort(tmp_path):
    accounts = AccountStore(f"sqlite:///{tmp_path / 'accounts.sqlite3'}", allow_sqlite=True)
    users = {}
    # Session authentication itself is covered by test_account_store. Seed
    # users through a trusted fixture so these tests focus on authorization,
    # concurrent assessment transactions, and durable records.
    with accounts._transaction(write=True) as connection:
        for username, role, year in (("admin", "admin", None), ("faculty", "faculty", None),
                                      ("resident", "resident", 1), ("other", "resident", 2)):
            user_id = uuid.uuid4().hex
            accounts._execute(connection, "INSERT INTO mrs_users VALUES (?, ?, ?, ?, ?, 1, ?)",
                              (user_id, username, "unused-fixture-password-hash", role, year, int(time.time())))
            users[username] = {"id": user_id, "token": accounts._new_session(connection, user_id)}
    return accounts, ProgressStore(accounts), users


def completed_attempt(accounts, token, text="Administer sedation and reassess", status="completed"):
    attempt_id = accounts.create_attempt(token, "R1-03", {"presentation": "Synthetic encounter"})
    payload = {
        "schema_version": "mrs_attempt_v1",
        "session": {"review_completed": status == "completed", "management_trace": [
            {"execution_status": "executed", "learner_input": text,
             "reasoning": {"problem_representation": "An explicit simulation working model"},
             "state_before": {"observable": {"mental_status": "alert"}},
             "state_after": {"observable": {"mental_status": "sedated"}}}
        ]},
    }
    accounts.save_attempt(token, attempt_id, payload, status=status)
    return attempt_id, payload


def assessment(**changes):
    return {"satisfactory": True, "depth": "integrated", "autonomy": "independent",
            "context": "Simulated sedation with hemodynamic reassessment",
            "evidence_refs": ["trace:0"], "notes": "The recorded reasoning supports the selected component.",
            **changes}


def objective(progress, token, objective_id="C4", user_id=None):
    return next(item for item in progress.get_progress(token, user_id)["objectives"]
                if item["objective_id"] == objective_id)


def test_twenty_observations_reach_cap_across_depths_and_extra_encounter_is_unchanged(cohort):
    accounts, progress, users = cohort
    resident, faculty = users["resident"]["token"], users["faculty"]["token"]
    for index in range(20):
        attempt_id, _ = completed_attempt(accounts, resident)
        result = progress.assess(faculty, attempt_id, "C4",
                                 assessment(depth=("foundational", "integrated", "complex")[index % 3]))
        assert result["status"] == "credited"
        assert result["count"] == index + 1
    value = objective(progress, resident)
    assert (value["count"], value["target"], value["status"], value["confirmed"]) == (20, 20, "target_reached", False)
    attempt_id, _ = completed_attempt(accounts, resident, text="Another independent sedation encounter")
    original = accounts.get_attempt(resident, attempt_id)
    for satisfactory in (True, False):
        assert progress.assess(faculty, attempt_id, "C4", assessment(satisfactory=satisfactory))["status"] == "capped"
    assert objective(progress, resident)["count"] == 20
    assert len(objective(progress, resident)["observations"]) == 20
    assert accounts.get_attempt(resident, attempt_id) == original


def test_one_encounter_records_separate_objectives_without_double_counting(cohort):
    accounts, progress, users = cohort
    attempt_id, _ = completed_attempt(accounts, users["resident"]["token"])
    faculty = users["faculty"]["token"]
    first = progress.assess(faculty, attempt_id, "TD1", assessment())
    other = progress.assess(faculty, attempt_id, "C4", assessment())
    duplicate = progress.assess(faculty, attempt_id, "C4", assessment(notes="Another assessor opinion"))
    assert first["status"] == other["status"] == "credited"
    assert duplicate["status"] == "duplicate"
    assert duplicate["observation_id"] == other["observation_id"]
    assert objective(progress, users["resident"]["token"], "TD1")["count"] == 1
    assert objective(progress, users["resident"]["token"], "C4")["count"] == 1


def test_unsatisfactory_is_retained_but_never_credited(cohort):
    accounts, progress, users = cohort
    attempt_id, _ = completed_attempt(accounts, users["resident"]["token"])
    result = progress.assess(users["faculty"]["token"], attempt_id, "C4", assessment(satisfactory=False))
    value = objective(progress, users["resident"]["token"])
    assert result["status"] == "recorded"
    assert value["count"] == 0 and value["assessed_count"] == 1
    assert value["observations"][0]["satisfactory"] is False


def test_restart_preserves_targets_assessment_metadata_and_frozen_evidence(cohort):
    accounts, progress, users = cohort
    resident, faculty = users["resident"]["token"], users["faculty"]["token"]
    attempt_id, payload = completed_attempt(accounts, resident)
    progress.set_target(users["admin"]["token"], "C4", 3, "Program pilot target")
    progress.assess(faculty, attempt_id, "C4", assessment())
    expected_sha = hashlib.sha256(json.dumps(payload, ensure_ascii=False, allow_nan=False,
                                             sort_keys=True).encode()).hexdigest()
    # A UI changing its own deserialized value must not change saved evidence.
    payload["session"]["management_trace"][0]["learner_input"] = "Altered outside the database"
    restarted = ProgressStore(AccountStore(accounts._url, allow_sqlite=True))
    value = objective(restarted, resident)
    record = value["observations"][0]
    assert (value["target"], value["count"]) == (3, 1)
    assert record["evidence"][0]["details"]["learner_input"] == "Administer sedation and reassess"
    assert record["source_revision"] == 1 and record["payload_sha"] == expected_sha
    assert record["depth"] == "integrated" and record["autonomy"] == "independent"
    assert record["assessor"] == "faculty" and record["created_at"] > 0


@pytest.mark.parametrize("kind", ["active", "abandoned", "sandbox", "missing"])
def test_unfinished_abandoned_sandbox_and_missing_attempts_cannot_be_reviewed(cohort, kind):
    accounts, progress, users = cohort
    if kind == "missing":
        attempt_id = "missing"
    else:
        token = users["faculty" if kind == "sandbox" else "resident"]["token"]
        attempt_id, _ = completed_attempt(accounts, token, status="completed" if kind == "sandbox" else kind)
    with pytest.raises(AccountError, match="completed, non-sandbox"):
        progress.assess(users["admin"]["token"], attempt_id, "C4", assessment())


@pytest.mark.parametrize("objective_id", ["C2", "C15", "R1-03", "invalid"])
def test_unsupported_or_local_challenge_ids_cannot_gain_epa_component_credit(cohort, objective_id):
    accounts, progress, users = cohort
    attempt_id, _ = completed_attempt(accounts, users["resident"]["token"])
    with pytest.raises(AccountError):
        progress.assess(users["faculty"]["token"], attempt_id, objective_id, assessment())


@pytest.mark.parametrize("changes", [
    {"satisfactory": "yes"}, {"depth": 4}, {"autonomy": "expert"}, {"context": ""},
    {"notes": " "}, {"evidence_refs": []}, {"evidence_refs": ["trace:999"]},
    {"evidence_refs": ["trace:0", "trace:0"]}, {"evidence_refs": [0]},
])
def test_invalid_assessments_cannot_create_observations(cohort, changes):
    accounts, progress, users = cohort
    attempt_id, _ = completed_attempt(accounts, users["resident"]["token"])
    with pytest.raises(AccountError):
        progress.assess(users["faculty"]["token"], attempt_id, "C4", assessment(**changes))
    assert objective(progress, users["resident"]["token"])["observations"] == []


def test_no_saved_executed_evidence_means_no_assessment(cohort):
    accounts, progress, users = cohort
    resident = users["resident"]["token"]
    attempt_id = accounts.create_attempt(resident, "R1-03", {})
    accounts.save_attempt(resident, attempt_id,
                          {"session": {"review_completed": True,
                                       "management_trace": [{"execution_status": "deferred"}]}}, "completed")
    with pytest.raises(AccountError, match="not present"):
        progress.assess(users["faculty"]["token"], attempt_id, "C4", assessment())


def test_completed_status_without_completed_reflection_cannot_be_assessed(cohort):
    accounts, progress, users = cohort
    resident = users["resident"]["token"]
    attempt_id = accounts.create_attempt(resident, "R1-03", {})
    accounts.save_attempt(resident, attempt_id,
                          {"session": {"review_completed": False, "management_trace": [
                              {"execution_status": "executed", "learner_input": "A decision"}]}}, "completed")
    with pytest.raises(AccountError, match="completed encounter reflection"):
        progress.assess(users["faculty"]["token"], attempt_id, "C4", assessment())


def test_resident_scope_and_staff_write_permissions_are_rechecked(cohort):
    accounts, progress, users = cohort
    resident, faculty, admin = (users[name]["token"] for name in ("resident", "faculty", "admin"))
    resident_id = users["resident"]["id"]
    attempt_id, _ = completed_attempt(accounts, resident)
    assert progress.get_progress(resident)["user"]["id"] == resident_id
    assert progress.get_progress(faculty, resident_id)["user"]["id"] == resident_id
    assert len(progress.list_residents(faculty)) == 2
    for action in (
        lambda: progress.get_progress(resident, users["other"]["id"]),
        lambda: progress.list_residents(resident),
        lambda: progress.list_audit(resident),
        lambda: progress.list_targets(resident),
        lambda: progress.assess(resident, attempt_id, "C4", assessment()),
        lambda: progress.set_target(faculty, "C4", 2, "Unauthorized change"),
        lambda: progress.confirm(resident, resident_id, "C4", "Self confirmation"),
        lambda: progress.reopen(resident, resident_id, "C4", "Self reopening"),
        lambda: progress.void_observation(resident, "missing", "Self correction"),
    ):
        with pytest.raises(AccountError):
            action()
    accounts.update_user(admin, users["faculty"]["id"], active=False)
    with pytest.raises(AccountError, match="sign in"):
        progress.assess(faculty, attempt_id, "C4", assessment())
    with pytest.raises(AccountError, match="sign in"):
        progress.get_progress(faculty, resident_id)
    assert objective(progress, resident)["count"] == 0


def test_role_change_invalidates_old_staff_token(cohort):
    accounts, progress, users = cohort
    faculty = users["faculty"]["token"]
    accounts.update_user(users["admin"]["token"], users["faculty"]["id"], role="resident", training_year=1)
    with pytest.raises(AccountError, match="sign in"):
        progress.list_residents(faculty)


def test_numeric_target_and_faculty_confirmation_are_distinct_and_reopen_retains_count(cohort):
    accounts, progress, users = cohort
    admin, faculty, resident = (users[name]["token"] for name in ("admin", "faculty", "resident"))
    user_id = users["resident"]["id"]
    progress.set_target(admin, "C4", 1, "Local pilot target")
    with pytest.raises(AccountError, match="target must be reached"):
        progress.confirm(faculty, user_id, "C4", "Premature confirmation")
    attempt_id, _ = completed_attempt(accounts, resident)
    progress.assess(faculty, attempt_id, "C4", assessment())
    assert objective(progress, resident)["status"] == "target_reached"
    with pytest.raises(AccountError):
        progress.confirm(faculty, user_id, "C4", "")
    assert progress.confirm(faculty, user_id, "C4", "Quality and case context reviewed")["changed"]
    assert objective(progress, resident)["status"] == "confirmed"
    assert not progress.confirm(faculty, user_id, "C4", "Duplicate form submission")["changed"]
    progress.set_target(admin, "C4", 2, "Retention practice across the program")
    confirmation = objective(progress, resident)["confirmation"]
    assert confirmation["target_at_confirmation"] == confirmation["count_at_confirmation"] == 1
    # Existing confirmation intentionally stays frozen until faculty reopens.
    second, _ = completed_attempt(accounts, resident)
    assert progress.assess(faculty, second, "C4", assessment())["status"] == "capped"
    assert progress.reopen(faculty, user_id, "C4", "Assess maintenance at complex depth")["changed"]
    value = objective(progress, resident)
    assert value["count"] == 1 and value["status"] == "developing"
    assert progress.assess(faculty, second, "C4", assessment(depth="complex"))["count"] == 2
    actions = [item["action"] for item in progress.list_audit(faculty, user_id)]
    assert actions.count("confirmed") == 1 and "reopened" in actions and actions.count("target_changed") == 2


def test_reopen_alone_does_not_silently_reset_or_expand_numeric_target(cohort):
    accounts, progress, users = cohort
    admin, faculty, resident = (users[name]["token"] for name in ("admin", "faculty", "resident"))
    progress.set_target(admin, "C4", 1, "Local pilot")
    attempt_id, _ = completed_attempt(accounts, resident)
    progress.assess(faculty, attempt_id, "C4", assessment())
    progress.confirm(faculty, users["resident"]["id"], "C4", "Evidence reviewed")
    progress.reopen(faculty, users["resident"]["id"], "C4", "Plan future retention practice")
    second, _ = completed_attempt(accounts, resident)
    assert progress.assess(faculty, second, "C4", assessment())["status"] == "capped"
    value = objective(progress, resident)
    assert value["count"] == value["target"] == 1 and value["status"] == "target_reached"


def test_void_preserves_history_allows_corrected_review_and_invalidates_confirmation(cohort):
    accounts, progress, users = cohort
    admin, faculty, resident = (users[name]["token"] for name in ("admin", "faculty", "resident"))
    progress.set_target(admin, "C4", 1, "Local pilot")
    attempt_id, _ = completed_attempt(accounts, resident)
    first = progress.assess(faculty, attempt_id, "C4", assessment())
    progress.confirm(faculty, users["resident"]["id"], "C4", "Initial review")
    with pytest.raises(AccountError):
        progress.void_observation(faculty, first["observation_id"], "")
    assert progress.void_observation(faculty, first["observation_id"], "Reassessment evidence misinterpreted")["changed"]
    assert not progress.void_observation(faculty, first["observation_id"], "Repeated button submission")["changed"]
    value = objective(progress, resident)
    assert value["count"] == 0 and not value["confirmed"]
    assert value["observations"][0]["voided"] and value["observations"][0]["notes"]
    second = progress.assess(faculty, attempt_id, "C4", assessment(satisfactory=False))
    value = objective(progress, resident)
    assert second["status"] == "recorded" and len(value["observations"]) == 2
    assert value["count"] == 0 and value["assessed_count"] == 1
    actions = [item["action"] for item in progress.list_audit(faculty)]
    assert "voided" in actions and "reopened_after_void" in actions


def test_targets_cannot_truncate_existing_credit_and_changes_are_audited(cohort):
    accounts, progress, users = cohort
    admin, faculty, resident = (users[name]["token"] for name in ("admin", "faculty", "resident"))
    for _ in range(2):
        attempt_id, _ = completed_attempt(accounts, resident)
        progress.assess(faculty, attempt_id, "C4", assessment())
    for target in (0, -1, 1001, True, 1.2, "2", 1):
        with pytest.raises(AccountError):
            progress.set_target(admin, "C4", target, "Invalid target")
    change = progress.set_target(admin, "C4", 2, "Program accepts two observations for this pilot")
    assert change == {"target": 2, "revision": 1, "changed": True}
    assert objective(progress, resident)["status"] == "target_reached"
    assert not progress.set_target(admin, "C4", 2, "Repeated save")["changed"]
    changes = [row for row in progress.list_audit(faculty) if row["action"] == "target_changed"]
    assert len(changes) == 1 and changes[0]["details"]["before"] == 20 and changes[0]["details"]["after"] == 2


def test_concurrent_graders_cannot_overrun_last_slot(cohort):
    accounts, progress, users = cohort
    admin, faculty, resident = (users[name]["token"] for name in ("admin", "faculty", "resident"))
    progress.set_target(admin, "C4", 2, "Concurrent grading test")
    first, _ = completed_attempt(accounts, resident)
    progress.assess(faculty, first, "C4", assessment())
    attempts = [completed_attempt(accounts, resident)[0] for _ in range(4)]
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda attempt: progress.assess(faculty, attempt, "C4", assessment()), attempts))
    assert sorted(item["status"] for item in results) == ["capped", "capped", "capped", "credited"]
    value = objective(progress, resident)
    assert value["count"] == 2 and len(value["observations"]) == 2


def test_concurrent_duplicate_submissions_create_one_observation(cohort):
    accounts, progress, users = cohort
    attempt_id, _ = completed_attempt(accounts, users["resident"]["token"])
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: progress.assess(users["faculty"]["token"], attempt_id, "C4", assessment()), range(4)))
    assert sorted(item["status"] for item in results) == ["credited", "duplicate", "duplicate", "duplicate"]
    assert objective(progress, users["resident"]["token"])["count"] == 1


def test_targets_match_program_supplied_catalog_without_multiplying_by_depth(cohort):
    _, progress, users = cohort
    values = progress.get_progress(users["resident"]["token"])["objectives"]
    assert {item["objective_id"]: item["target"] for item in values} == {
        "TD1": 10, "F1": 15, "C1": 40, "C2": 25, "C3": 20, "C4": 20, "C14": 50, "C15": 5}
    assert all(item["count"] == 0 and not item["confirmed"] for item in values)
    assert all("not independently verified" in item["target_source"] for item in values)
    assert {item["status"] for item in values} == {"not_observed", "not_available"}
    targets = progress.list_targets(users["faculty"]["token"])
    assert {item["objective_id"]: item["target"] for item in targets} == {
        item["objective_id"]: item["target"] for item in values}


def test_former_resident_promoted_to_faculty_cannot_void_own_old_observation(cohort):
    accounts, progress, users = cohort
    attempt_id, _ = completed_attempt(accounts, users["resident"]["token"])
    result = progress.assess(users["faculty"]["token"], attempt_id, "C4", assessment())
    accounts.update_user(users["admin"]["token"], users["resident"]["id"], role="faculty")
    with accounts._transaction(write=True) as connection:
        promoted_token = accounts._new_session(connection, users["resident"]["id"])
    with pytest.raises(AccountError, match="own encounters"):
        progress.void_observation(promoted_token, result["observation_id"], "Self correction")
