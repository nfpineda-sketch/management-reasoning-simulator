"""Private initial-image overlap must never publish an unreviewed case."""
from concurrent.futures import Future
from copy import deepcopy
import json

import pytest

from generated_case import generate_ai_encounter, GeneratedCaseError
from patient_appearance import appearance_signature, appearance_state
from scene_preparation import ScenePreparation, consume_prepared_scene
from test_generated_case import AuthorClient, approval, clean_base, novel_payload


class DeferredPool:
    def __init__(self):
        self.calls = []

    def submit(self, function, *args):
        future = Future()
        self.calls.append((function, args, future))
        return future


@pytest.fixture
def pool(monkeypatch):
    value = DeferredPool()
    monkeypatch.setattr("scene_jobs._POOL", value)
    return value


def generate(preparation, client=None):
    return generate_ai_encounter("R1-05", clean_base(), client=client or AuthorClient(), seed=31,
                                 on_case_compiled=preparation.on_case_compiled)


def test_initial_job_starts_only_after_clinical_approval_without_student_data(pool):
    session = {"_account_user_id": "owner-one"}
    before = deepcopy(session)

    class ReviewingClient(AuthorClient):
        def create(self, **kwargs):
            if kwargs["text"]["format"]["name"] == "clinical_consistency_review":
                assert len(pool.calls) == 0
                assert session == before
            return super().create(**kwargs)

    with ScenePreparation("test-key") as preparation:
        result = generate(preparation, ReviewingClient())
        snapshot = pool.calls[0][1][0]
        assert set(snapshot) == {"observable", "treatments", "encounter_spec"}
        assert snapshot["treatments"] == {}
        assert snapshot["encounter_spec"]["clinical_case"] == {
            "patient": {"age_years": 42, "sex": "female"}}
        assert set(snapshot["observable"]) == {"mental_status", "work_of_breathing", "visual"}
        assert appearance_state(snapshot) == appearance_state(result["state"])
        assert not any(field in json.dumps(snapshot) for field in (
            "adrenal", "history", "diagnosis", "challenge", "sbp", "learner", "faculty"))
        assert session == before  # Review success alone does not adopt automatically.
        assert preparation.adopt(session, result["state"], "attempt-one")
    jobs = consume_prepared_scene(session, result["state"], "attempt-one")
    assert jobs is not None
    assert consume_prepared_scene(session, result["state"], "attempt-one") is None
    pool.calls[0][2].set_result("screened-initial-image")
    assert jobs.current(appearance_signature(result["state"])) == "screened-initial-image"
    assert "_prepared_scene" not in session
    assert "screened-initial-image" not in json.dumps(result)


def test_rejected_clinical_review_never_spends_on_an_image(pool):
    review = approval(); review['coherent'] = False
    with pytest.raises(GeneratedCaseError):
        with ScenePreparation('test-key') as preparation:
            generate(preparation, AuthorClient(review=review))
    assert pool.calls == []
    assert preparation._jobs is None


def test_invalid_case_never_starts_image_job(pool):
    raw = novel_payload()
    raw["patient"]["pronouns"] = "he/him"
    with pytest.raises(GeneratedCaseError):
        with ScenePreparation("test-key") as preparation:
            generate(preparation, AuthorClient(raw))
    assert pool.calls == []


def test_store_failure_after_review_keeps_image_out_of_session(pool):
    session = {}
    with pytest.raises(RuntimeError, match="storage failure"):
        with ScenePreparation("test-key") as preparation:
            result = generate(preparation)
            pool.calls[0][2].set_result("screened-but-unadopted-image")
            raise RuntimeError("storage failure")
    assert preparation._jobs is None
    assert not session
    assert "image" not in result


def test_account_launch_storage_failure_cancels_preparation(pool, monkeypatch):
    from types import SimpleNamespace
    import curriculum_runtime
    from account_store import AccountError
    from encounter_generator import generate_encounter as real_generate
    from test_generation_progress import RecordingStatus

    session = {"_account_user_id": "admin-one"}
    class FailingStore:
        def list_attempts(self, token):
            return []

        def create_attempt(self, token, challenge, encounter, sandbox):
            assert len(pool.calls) == 1
            assert "_prepared_scene" not in session
            assert "SceneJobs" not in json.dumps(encounter)
            assert encounter["spec"]["provenance"]["review"]["coherent"]
            raise AccountError("storage failure")

    def author(*args, **kwargs):
        return real_generate(*args, **kwargs, client=AuthorClient())
    monkeypatch.setattr(curriculum_runtime, "generate_encounter", author)
    monkeypatch.setattr(curriculum_runtime, "_secret", lambda key, default="": "test-key" if key == "OPENAI_API_KEY" else default)
    monkeypatch.setattr(curriculum_runtime, "st", SimpleNamespace(
        session_state=session, status=lambda *args, **kwargs: RecordingStatus()))
    context = {"store": FailingStore(), "token": "test-session",
               "user": {"id": "admin-one", "role": "admin"}}
    with pytest.raises(AccountError, match="storage failure"):
        curriculum_runtime.start_encounter(context, clean_base(), lambda: None, "R1-05")
    assert pool.calls[0][2].cancelled()
    assert session == {"_account_user_id": "admin-one"}


@pytest.mark.parametrize("mismatch", ["owner", "attempt", "case", "source", "appearance"])
def test_prepared_job_is_never_adopted_for_a_different_context(pool, mismatch):
    session = {"_account_user_id": "owner-one"}
    with ScenePreparation("test-key") as preparation:
        result = generate(preparation)
        assert preparation.adopt(session, result["state"], "attempt-one")
    state = deepcopy(result["state"])
    attempt = "attempt-one"
    if mismatch == "owner":
        session["_account_user_id"] = "owner-two"
    elif mismatch == "attempt":
        attempt = "attempt-two"
    elif mismatch == "case":
        state["case_id"] = "other-case"
    elif mismatch == "source":
        state["encounter_spec"]["provenance"]["raw_case_sha256"] = "different-draft"
    else:
        state["observable"]["mental_status"] = "Drowsy"
    assert consume_prepared_scene(session, state, attempt) is None
    assert pool.calls[0][2].cancelled()
    assert "_prepared_scene" not in session


def test_sessions_with_identical_visible_patients_do_not_share_jobs(pool):
    first, second = {"_account_user_id": "one"}, {"_account_user_id": "two"}
    results = []
    for session, attempt in ((first, "a"), (second, "b")):
        with ScenePreparation("test-key") as preparation:
            result = generate(preparation)
            results.append(result)
            preparation.adopt(session, result["state"], attempt)
    one = consume_prepared_scene(first, results[0]["state"], "a")
    two = consume_prepared_scene(second, results[1]["state"], "b")
    assert one is not two
    pool.calls[0][2].set_result("first-image")
    assert one.current(appearance_signature(results[0]["state"])) == "first-image"
    assert two.current(appearance_signature(results[1]["state"])) is None
    two.discard()


def test_absent_image_key_keeps_normal_case_review_and_launch(pool):
    with ScenePreparation("") as preparation:
        result = generate(preparation)
        assert not preparation.adopt({}, result["state"])
    assert pool.calls == []
    assert result["source"] == "ai"
