"""Safe image failures across real SDK parsing, workers and manual retries."""
import base64
from concurrent.futures import Future
from io import BytesIO
import json
from types import SimpleNamespace

import httpx
from openai import APIConnectionError, APITimeoutError, OpenAI
from PIL import Image
import pytest

from image_consistency import CHECK_IDS, ImageConsistencyError, inspect_image
from scene_errors import SceneImageError, provider_image_error
import scene_jobs
import scene_pipeline


PRIVATE = "PRIVATE_PROVIDER_KEY_CASE_IMAGE"


@pytest.fixture
def image_and_contract():
    output = BytesIO()
    Image.new("RGB", (32, 32), (100, 100, 100)).save(output, format="PNG")
    image = base64.b64encode(output.getvalue()).decode("ascii")
    contract = {"mental_status": "alert", "work_of_breathing": "mildly increased",
                "expression": "uncomfortable", "skin_color": "mild pallor",
                "mottling": False, "diaphoresis": "mild", "respiratory_support": "none"}
    return image, contract


@pytest.mark.parametrize("status,body,code", [
    (401, {}, "AUTH"), (403, {}, "ACCESS"), (404, {}, "MODEL"),
    (429, {"code": "insufficient_quota"}, "QUOTA"),
    (429, {"code": "rate_limit_exceeded"}, "RATE"),
    (400, {"code": "invalid_json_schema"}, "FORMAT"),
    (400, {"param": "model"}, "REQUEST"),
    (400, {"code": "content_policy_violation"}, "REFUSED"),
    (503, {}, "PROVIDER"),
])
def test_screen_retains_safe_sdk_failure_category_once(image_and_contract, status, body, code):
    image, contract = image_and_contract
    calls = []

    def respond(request):
        calls.append(request.method)
        return httpx.Response(status, json={"error": {**body, "message": PRIVATE}}, request=request)

    with OpenAI(api_key="test-key", max_retries=0,
                http_client=httpx.Client(transport=httpx.MockTransport(respond))) as client:
        with pytest.raises(ImageConsistencyError) as failure:
            inspect_image(image, contract, "test-key", client=client)
    error = failure.value
    assert error.reason_code == "provider_unavailable"
    assert error.code == code and error.stage == "SCREEN"
    assert error.reference == f"IMAGE-SCREEN-{code}"
    assert PRIVATE not in str(error) and PRIVATE not in json.dumps(error.__dict__)
    assert calls == ["POST"] and error.__suppress_context__


@pytest.mark.parametrize("stage", ["CREATE", "EDIT", "SCREEN"])
@pytest.mark.parametrize("kind,code", [("timeout", "TIMEOUT"), ("connection", "CONNECTION"), ("unknown", "INTERNAL")])
def test_transport_categories_are_safe_for_every_stage(stage, kind, code):
    request = httpx.Request("POST", "https://example.invalid/" + PRIVATE)
    error = {"timeout": APITimeoutError(request=request),
             "connection": APIConnectionError(message=PRIVATE, request=request),
             "unknown": RuntimeError(PRIVATE)}[kind]
    diagnostic = provider_image_error(error, stage)
    assert diagnostic.code == code and diagnostic.stage == stage
    assert PRIVATE not in str(diagnostic) and PRIVATE not in json.dumps(diagnostic.__dict__)


def test_screen_refusal_is_not_malformed_json(image_and_contract):
    image, contract = image_and_contract
    client = SimpleNamespace(responses=SimpleNamespace(create=lambda **kwargs: SimpleNamespace(
        status="completed", output_text=PRIVATE,
        output=[SimpleNamespace(content=[SimpleNamespace(type="refusal", refusal=PRIVATE)])])))
    with pytest.raises(SceneImageError) as failure:
        inspect_image(image, contract, "test-key", client=client)
    assert failure.value.reference == "IMAGE-SCREEN-REFUSED"
    assert PRIVATE not in str(failure.value)


class DeferredPool:
    def __init__(self):
        self.calls = []

    def submit(self, function, *args):
        future = Future()
        self.calls.append((function, args, future))
        return future

    def run(self, index=-1):
        function, args, future = self.calls[index]
        try:
            future.set_result(function(*args))
        except Exception as error:
            future.set_exception(error)


def test_job_reports_screen_stage_and_failure_without_state_or_provider_payload(monkeypatch, caplog):
    clock = {"now": 100.0}
    pool = DeferredPool()
    monkeypatch.setattr(scene_jobs, "_POOL", pool)
    monkeypatch.setattr(scene_jobs, "monotonic", lambda: clock["now"])
    jobs = scene_jobs.SceneJobs()
    observed = []

    def initial(snapshot, key, model, *, progress):
        assert snapshot == {"hidden": PRIVATE} and key == PRIVATE
        progress("CREATE")
        observed.append(jobs.status("current"))
        clock["now"] = 112
        progress("SCREEN")
        observed.append(jobs.status("current"))
        raise ImageConsistencyError("mismatch", ("expression", PRIVATE))

    jobs.request("current", {"hidden": PRIVATE}, PRIVATE, "image-model", initial, None,
                 progress_supported=True)
    assert jobs.status("current")["queued"]
    pool.run()
    assert [(status["stage"], status["queued"]) for status in observed] == [("CREATE", False), ("SCREEN", False)]
    status = jobs.status("current")
    assert status == {
        "state": "failed", "stage": "SCREEN", "elapsed_seconds": 12.0, "queued": False,
        "code": "MISMATCH", "reference": "IMAGE-SCREEN-MISMATCH",
        "message": "The patient image did not match the current appearance.",
        "failed_checks": ("expression",),
    }
    assert jobs.current("current") is None and jobs.base is None
    assert PRIVATE not in json.dumps(status) and PRIVATE not in caplog.text
    status["code"] = PRIVATE
    assert jobs.failure("current")["code"] == "MISMATCH"
    clock["now"] = 300
    assert jobs.failure("current")["elapsed_seconds"] == 12
    # Re-rendering never retries a failed image silently.
    jobs.request("current", {}, PRIVATE, "image-model", initial, None)
    assert len(pool.calls) == 1


def test_manual_retry_replaces_prior_error_but_never_old_image(monkeypatch):
    pool = DeferredPool()
    monkeypatch.setattr(scene_jobs, "_POOL", pool)
    jobs = scene_jobs.SceneJobs()
    jobs.request("a", {}, "key", "model", object(), object())
    pool.calls[0][2].set_exception(SceneImageError("TIMEOUT", "SCREEN"))
    assert jobs.failure("a")["code"] == "TIMEOUT"
    assert jobs.retry("a")
    jobs.request("a", {}, "key", "model", object(), object())
    assert jobs.status("a")["state"] == "pending" and jobs.failure("a") is None
    assert jobs.current("a") is None
    pool.calls[1][2].set_result("approved")
    assert jobs.current("a") == "approved" and jobs.failure("a") is None
    assert "reference" not in jobs.status("a")


def test_retry_cannot_remove_approved_or_pending_work(monkeypatch):
    pool = DeferredPool()
    monkeypatch.setattr(scene_jobs, "_POOL", pool)
    jobs = scene_jobs.SceneJobs()
    assert jobs.retry("unknown") is False
    jobs.images["approved"] = "approved-image"
    jobs.failed.add("approved")  # Even an inconsistent legacy flag cannot evict an approved image.
    assert jobs.retry("approved") is False
    assert jobs.images == {"approved": "approved-image"}
    jobs.request("pending", {}, "key", "model", object(), object())
    original_pending = jobs.pending
    jobs.failed.add("pending")
    assert jobs.retry("pending") is False
    assert jobs.pending == original_pending and not original_pending[1].cancelled()
    jobs.failed.add("old-failed")
    assert jobs.retry("old-failed") is True
    assert jobs.pending == original_pending and jobs.images["approved"] == "approved-image"


def test_retry_cannot_revive_discarded_preparation(monkeypatch):
    pool = DeferredPool()
    monkeypatch.setattr(scene_jobs, "_POOL", pool)
    jobs = scene_jobs.SceneJobs()
    jobs.request("failed", {}, "", "model", object(), object())
    assert jobs.failure("failed") is not None
    jobs.discard()
    jobs.failed.add("failed")
    assert jobs.retry("failed") is False
    jobs.request("failed", {}, "key", "model", object(), object())
    assert not pool.calls and jobs.pending is None


@pytest.mark.parametrize("running", [False, True])
def test_discard_cancels_queue_or_drops_running_job_and_ignores_late_updates(monkeypatch, running):
    pool = DeferredPool()
    monkeypatch.setattr(scene_jobs, "_POOL", pool)
    jobs = scene_jobs.SceneJobs()
    jobs.request("unpublished", {}, "key", "model", object(), object())
    future = pool.calls[0][2]
    if running:
        assert future.set_running_or_notify_cancel()
    jobs.discard()
    assert future.cancelled() is not running
    if running:
        future.set_result(PRIVATE)
    jobs._stage("unpublished", "SCREEN")
    assert jobs.status("unpublished") == {"state": "unavailable", "elapsed_seconds": 0.0}
    assert jobs.current("unpublished") is None and jobs.base is None and not jobs.images
    assert jobs.pending is None
    jobs.request("new", {}, "key", "model", object(), object())
    assert len(pool.calls) == 1


def test_missing_config_is_explicit_and_does_not_create_job(monkeypatch):
    pool = DeferredPool()
    monkeypatch.setattr(scene_jobs, "_POOL", pool)
    jobs = scene_jobs.SceneJobs()
    jobs.request("a", {}, "", "model", object(), object())
    assert jobs.failure("a")["reference"] == "IMAGE-CREATE-CONFIG"
    assert not pool.calls and jobs.current("a") is None


def test_untrusted_diagnostic_values_cannot_become_labels():
    error = SceneImageError({"secret": PRIVATE}, PRIVATE, (PRIVATE, "expression"))
    assert error.reference == "IMAGE-CREATE-INTERNAL" and error.failed_checks == ("expression",)
    assert PRIVATE not in str(error) and PRIVATE not in json.dumps(error.__dict__)


def test_untagged_creation_error_is_sanitized_at_pipeline_boundary(monkeypatch):
    import clinical_scene
    stages = []

    def fail(*args):
        raise RuntimeError(PRIVATE)

    monkeypatch.setattr(clinical_scene, "generate_scene", fail)
    with pytest.raises(SceneImageError) as error:
        scene_pipeline.screened_scene({}, "key", "model", progress=stages.append)
    assert stages == ["CREATE"] and error.value.reference == "IMAGE-CREATE-INTERNAL"
    assert PRIVATE not in str(error.value) and error.value.__suppress_context__
