"""Displayed image failures and reviewed prefetches across actual API boundaries."""
import base64
from concurrent.futures import Future
from copy import deepcopy
from io import BytesIO
import json
from types import SimpleNamespace

import httpx
from openai import OpenAI
from PIL import Image
import pytest

import clinical_scene
from patient_appearance import appearance_signature, generate_appearance
from scene_errors import SceneImageError
from scene_preparation import ScenePreparation
from test_scene_preparation import pool, generate


@pytest.fixture
def png():
    output = BytesIO()
    Image.new("RGB", (1536, 1024)).save(output, format="PNG")
    return base64.b64encode(output.getvalue()).decode()


# The session-only path runs only with an account database (faculty decision 10,
# 2026-09-26): these tests drive it as a deployment with the image bank switched off.
WITH_ACCOUNTS = {"store": object()}


@pytest.mark.parametrize("stage", ["CREATE", "EDIT"])
def test_image_sdk_errors_retain_stage_without_provider_body(stage, png):
    calls = []
    def respond(request):
        calls.append(request.url.path)
        return httpx.Response(403, json={"error": {"message": "PRIVATE_KEY_AND_PROMPT"}}, request=request)
    state = {"case_id": "PS001", "observable": {}, "treatments": {}}
    with OpenAI(api_key="test-key", max_retries=0,
                http_client=httpx.Client(transport=httpx.MockTransport(respond))) as client:
        with pytest.raises(SceneImageError) as failure:
            if stage == "CREATE":
                clinical_scene.generate_scene(state, "", client=client)
            else:
                generate_appearance(png, state, "", client=client)
    assert failure.value.reference == f"IMAGE-{stage}-ACCESS"
    assert "PRIVATE" not in str(failure.value) + json.dumps(failure.value.__dict__)
    assert len(calls) == 1


@pytest.mark.parametrize("stage", ["CREATE", "EDIT"])
def test_invalid_provider_image_does_not_pass_as_success(stage, png):
    invalid = SimpleNamespace(data=[SimpleNamespace(b64_json="INVALID_PROVIDER_IMAGE")])
    images = SimpleNamespace(generate=lambda **kw: invalid, edit=lambda **kw: invalid)
    state = {"case_id": "PS001", "observable": {}, "treatments": {}}
    with pytest.raises(SceneImageError) as failure:
        if stage == "CREATE":
            clinical_scene.generate_scene(state, "", client=SimpleNamespace(images=images))
        else:
            generate_appearance(png, state, "", client=SimpleNamespace(images=images))
    assert failure.value.reference == f"IMAGE-{stage}-INVALID_IMAGE"
    assert "INVALID_PROVIDER_IMAGE" not in str(failure.value)


@pytest.mark.parametrize("code", ["MISMATCH", "UNCERTAIN"])
def test_scene_keeps_monitor_and_safe_failure_while_rejected_image_is_hidden(code):
    html = clinical_scene.scene_html(
        "UNAPPROVED_IMAGE", "<div>HR 118</div>", current=False,
        image_status={"state": "failed", "stage": "SCREEN", "code": code,
                      "message": "PRIVATE_RAW_PROVIDER_RESPONSE", "failed_checks": ["expression"]})
    assert "HR 118" in html and f"IMAGE-SCREEN-{code}" in html
    assert "expression" in html.lower()
    assert "UNAPPROVED_IMAGE" not in html and "PRIVATE" not in html
    assert 'role="status"' in html
    assert "background-image:url" not in html


def test_pending_status_distinguishes_queue_generation_and_screening():
    status = {"state": "pending", "stage": "CREATE", "queued": True, "elapsed_seconds": 12.5}
    assert clinical_scene.scene_status_text(status) == "Waiting to prepare patient image · 12s elapsed"
    status.update(queued=False)
    assert clinical_scene.scene_status_text(status) == "Creating patient image · 12s elapsed"
    status.update(stage="SCREEN")
    assert clinical_scene.scene_status_text(status) == "Checking patient appearance · 12s elapsed"
    status.update(stage={"unsafe": "PRIVATE"}, elapsed_seconds="PRIVATE")
    assert clinical_scene.scene_status_text(status) == "Preparing patient image"


def test_room_consumes_reviewed_preparation_once_and_keeps_it_after_event_restore(monkeypatch, pool):
    session = {"_attempt_id": "attempt-one", "_account_user_id": "owner-one"}
    with ScenePreparation("test-key") as preparation:
        result = generate(preparation)
        preparation.adopt(session, result["state"], "attempt-one")
    monkeypatch.setattr(clinical_scene, "st", SimpleNamespace(session_state=session))
    monkeypatch.setattr(clinical_scene, "setting", lambda key, default="": "test-key" if key == "OPENAI_API_KEY" else default)
    arrival = {"kind": "presentation", "text": result["presentation"]}
    state = result["state"]
    before = deepcopy(state)
    assert clinical_scene.scene_image(state, [arrival]) is None
    jobs = session["_scene_jobs"]
    assert len(pool.calls) == 1 and "_prepared_scene" not in session
    pool.calls[0][2].set_result("screened-current-image")
    assert clinical_scene.scene_image(deepcopy(state), [deepcopy(arrival)]) == "screened-current-image"
    assert session["_scene_jobs"] is jobs and len(pool.calls) == 1
    assert state == before


def test_image_retry_keeps_case_and_only_schedules_current_appearance(monkeypatch, pool):
    session = {"_attempt_id": "attempt-one"}
    with ScenePreparation("test-key") as preparation:
        result = generate(preparation)
        preparation.adopt(session, result["state"], "attempt-one")
    monkeypatch.setattr(clinical_scene, "st", SimpleNamespace(session_state=session))
    monkeypatch.setattr(clinical_scene, "setting", lambda key, default="": "test-key" if key == "OPENAI_API_KEY" else default)
    state, events = result["state"], [{"kind": "presentation", "text": result["presentation"]}]
    before = deepcopy((state, events))
    pool.calls[0][2].set_exception(SceneImageError("TIMEOUT", "SCREEN"))
    assert clinical_scene._session_scene_image(state, events, WITH_ACCOUNTS) is None
    jobs = session["_scene_jobs"]
    assert session["_scene_status"]["reference"] == "IMAGE-SCREEN-TIMEOUT"
    assert jobs.retry(appearance_signature(state))
    assert clinical_scene._session_scene_image(state, events, WITH_ACCOUNTS) is None
    assert len(pool.calls) == 2 and session["_scene_status"]["state"] == "pending"
    assert (state, events) == before
    assert jobs.pending[1] is pool.calls[1][2]


def test_open_v0172_session_can_replace_legacy_job_without_discard_method(monkeypatch, pool):
    pending = Future()
    old = SimpleNamespace(base="old-image", images={}, pending=("old", pending))
    session = {"_attempt_id": "attempt-one", "_scene_identity": "v0.17.2", "_scene_jobs": old}
    monkeypatch.setattr(clinical_scene, "st", SimpleNamespace(session_state=session))
    monkeypatch.setattr(clinical_scene, "setting", lambda key, default="": "test-key" if key == "OPENAI_API_KEY" else default)
    state = {"case_id": "PS001", "observable": {}, "treatments": {}}
    assert clinical_scene._session_scene_image(state, [{"kind": "presentation"}], WITH_ACCOUNTS) is None
    assert session["_scene_jobs"] is not old and pending.cancelled()
    assert not session["_scene_current"] and len(pool.calls) == 1
