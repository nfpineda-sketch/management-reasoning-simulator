"""Screening, cache and display integration without a paid model request."""
from concurrent.futures import Future
from copy import deepcopy
from functools import partial
import json
from types import SimpleNamespace

import pytest

import clinical_scene
from image_consistency import ImageConsistencyError
from patient_appearance import appearance_signature, appearance_state
import scene_jobs
import scene_pipeline


@pytest.fixture
def state():
    return {
        "observable": {
            "mental_status": "Alert", "work_of_breathing": "Mildly increased",
            "visual": {"expression": "uncomfortable", "skin_color": "mild pallor",
                       "diaphoresis": "absent", "mottling": False},
            "sbp": 90, "hr": 174,
        },
        "treatments": {"oxygen": True, "oxygen_device": "nasal cannula"},
        "hidden": {"diagnosis": "PRIVATE_DIAGNOSIS", "target": "PRIVATE_TARGET"},
        "learner_submission": "PRIVATE_ACTION", "sim_time": 0,
    }


class DeferredPool:
    """Schedule real pipeline functions; explicitly advance the test's worker."""

    def __init__(self):
        self.calls = []

    def submit(self, function, *args):
        future = Future()
        self.calls.append((function, args, future))
        return future

    def complete(self, index=-1):
        function, args, future = self.calls[index]
        try:
            future.set_result(function(*args))
        except Exception as error:
            future.set_exception(error)


@pytest.fixture
def pool(monkeypatch):
    pool = DeferredPool()
    monkeypatch.setattr(scene_jobs, "_POOL", pool)
    return pool


def test_scene_and_edit_are_screened_with_the_visible_contract(monkeypatch, state):
    calls = []
    before = deepcopy(state)

    def generate(snapshot, key, model):
        calls.append(("generate", deepcopy(snapshot), key, model))
        return "candidate-initial"

    def edit(reference, snapshot, key, model):
        calls.append(("edit", reference, deepcopy(snapshot), key, model))
        return "candidate-edited"

    def inspect(candidate, contract, key, **kwargs):
        calls.append(("inspect", candidate, deepcopy(contract), key, kwargs))
        assert contract == appearance_state(state)
        assert not any(token in json.dumps(contract) for token in ("PRIVATE", "diagnosis", "sbp", "hr", "sim_time"))
        return {"accepted": True}

    monkeypatch.setattr(clinical_scene, "generate_scene", generate)
    monkeypatch.setattr(scene_pipeline, "generate_appearance", edit)
    monkeypatch.setattr(scene_pipeline, "inspect_image", inspect)
    assert scene_pipeline.screened_scene(state, "test-key", "image-model", review_model="review-model") == "candidate-initial"
    assert [entry[0] for entry in calls] == ["generate", "inspect"]
    assert calls[-1][-1] == {"model": "review-model", "reference_b64": None}
    assert scene_pipeline.screened_appearance("original-reference", state, "test-key", "image-model", review_model="review-model") == "candidate-edited"
    assert [entry[0] for entry in calls] == ["generate", "inspect", "edit", "inspect"]
    assert calls[-1][-1] == {"model": "review-model", "reference_b64": "original-reference"}
    assert state == before


@pytest.mark.parametrize("failure_mode", ["mismatch", "uncertain", "false_result"])
def test_rejected_initial_candidate_never_enters_cache_or_retries(monkeypatch, state, pool, failure_mode, caplog):
    generated, inspected = [], []

    def generate(*args):
        generated.append(args)
        return "PRIVATE_REJECTED_IMAGE"

    def inspect(*args, **kwargs):
        inspected.append((args, kwargs))
        if failure_mode == "false_result":
            return {"accepted": False}
        raise ImageConsistencyError(failure_mode, ("expression",))

    monkeypatch.setattr(clinical_scene, "generate_scene", generate)
    monkeypatch.setattr(scene_pipeline, "inspect_image", inspect)
    jobs = scene_jobs.SceneJobs()
    signature = appearance_signature(state)
    request = lambda: jobs.request(signature, state, "PRIVATE_KEY", "image-model",
                                   scene_pipeline.screened_scene, scene_pipeline.screened_appearance)
    request()
    assert jobs.base is None and not jobs.images and len(pool.calls) == 1
    pool.complete()
    assert jobs.current(signature) is None
    assert jobs.base is None and not jobs.images and signature in jobs.failed
    request()
    request()
    assert len(pool.calls) == len(generated) == len(inspected) == 1
    assert "PRIVATE" not in caplog.text


def test_edits_keep_original_reference_and_never_publish_a_rejected_revision(monkeypatch, state, pool):
    references = []
    reject = {"value": False}

    def edit(reference, snapshot, *args):
        references.append(reference)
        return "edited-" + snapshot["observable"]["mental_status"]

    def inspect(*args, **kwargs):
        if reject["value"]:
            raise ImageConsistencyError("mismatch", ("gaze_and_eyelids",))
        return {"accepted": True}

    monkeypatch.setattr(clinical_scene, "generate_scene", lambda *args: "approved-original")
    monkeypatch.setattr(scene_pipeline, "generate_appearance", edit)
    monkeypatch.setattr(scene_pipeline, "inspect_image", inspect)
    jobs = scene_jobs.SceneJobs()

    def request_current():
        signature = appearance_signature(state)
        jobs.request(signature, state, "test-key", "image-model",
                     scene_pipeline.screened_scene, scene_pipeline.screened_appearance)
        pool.complete()
        return signature, jobs.current(signature)

    initial_signature, initial = request_current()
    assert initial == jobs.base == "approved-original"
    state["observable"]["mental_status"] = "Drowsy"
    _, first_edit = request_current()
    assert first_edit == "edited-Drowsy" and jobs.base == "approved-original"
    state["observable"]["mental_status"] = "Obtunded"
    reject["value"] = True
    rejected_signature, rejected = request_current()
    assert rejected is None and rejected_signature in jobs.failed
    assert "edited-Obtunded" not in jobs.images.values()
    assert jobs.images[initial_signature] == "approved-original"
    state["observable"]["mental_status"] = "Unresponsive"
    reject["value"] = False
    _, final_edit = request_current()
    assert final_edit == "edited-Unresponsive"
    assert references == ["approved-original"] * 3 and jobs.base == "approved-original"


def test_worker_screens_frozen_state_and_old_completion_is_not_current(monkeypatch, state, pool):
    seen = []

    def inspect(candidate, contract, *args, **kwargs):
        seen.append(deepcopy(contract))
        return {"accepted": True}

    monkeypatch.setattr(clinical_scene, "generate_scene", lambda *args: "approved-arrival")
    monkeypatch.setattr(scene_pipeline, "generate_appearance", lambda *args: "approved-new-state")
    monkeypatch.setattr(scene_pipeline, "inspect_image", inspect)
    jobs = scene_jobs.SceneJobs()
    original_contract = appearance_state(state)
    initial_signature = appearance_signature(state)
    jobs.request(initial_signature, state, "test-key", "image-model",
                 scene_pipeline.screened_scene, scene_pipeline.screened_appearance)
    state["observable"]["mental_status"] = "Drowsy"
    state["observable"]["visual"]["skin_color"] = "pallor"
    state["sim_time"] = 3
    current_signature = appearance_signature(state)
    current_state = deepcopy(state)
    pool.complete()
    assert jobs.current(current_signature) is None
    assert seen == [original_contract]
    assert jobs.current(initial_signature) == "approved-arrival"
    jobs.request(current_signature, state, "test-key", "image-model",
                 scene_pipeline.screened_scene, scene_pipeline.screened_appearance)
    pool.complete()
    assert jobs.current(current_signature) == "approved-new-state"
    assert seen[-1] == appearance_state(current_state) and state == current_state


@pytest.mark.parametrize("pending", [True, False])
def test_scene_html_never_displays_previous_image_and_keeps_monitor(pending):
    html = clinical_scene.scene_html(
        "PRIOR_UNSCREENED_IMAGE_BYTES", '<div id="live-vitals">HR 174</div>',
        current=False, pending=pending, observations="Drowsy <updated>")
    assert "PRIOR_UNSCREENED_IMAGE_BYTES" not in html and "background-image:url(" not in html
    assert '<div id="live-vitals">HR 174</div>' in html
    assert "Drowsy &lt;updated&gt;" in html and "current state" not in html


def test_scene_image_invalidates_legacy_unscreened_cache(monkeypatch, state):
    arrival = {"kind": "presentation", "text": "Arrival"}
    signature = appearance_signature(state)
    legacy = scene_jobs.SceneJobs()
    legacy.base = "UNSCREENED_LEGACY"
    legacy.images[signature] = legacy.base
    session = {"_attempt_id": "same-encounter", "_scene_identity": ("same-encounter", id(arrival)),
               "_scene_jobs": legacy, "_scene_current": True, "_scene_failure_notified": "legacy-notice"}
    monkeypatch.setattr(clinical_scene, "st", SimpleNamespace(session_state=session))
    monkeypatch.setattr(clinical_scene, "setting", lambda name, default="": "" if name == "OPENAI_API_KEY" else default)
    assert clinical_scene.scene_image(state, [arrival]) is None
    assert session["_scene_jobs"] is not legacy and session["_scene_jobs"].base is None
    assert session["_scene_current"] is False and session["_scene_failure_notified"] is None
    assert len(session["_scene_identity"]) == 5


def test_scene_image_returns_only_requested_signature_during_failure_or_pending(monkeypatch, state):
    arrival = {"kind": "presentation", "text": "Arrival"}
    session = {"_attempt_id": "same-encounter"}
    monkeypatch.setattr(clinical_scene, "st", SimpleNamespace(session_state=session))
    monkeypatch.setattr(clinical_scene, "setting", lambda name, default="": "" if name == "OPENAI_API_KEY" else default)
    assert clinical_scene.scene_image(state, [arrival]) is None
    jobs = session["_scene_jobs"]
    signature = appearance_signature(state)
    jobs.base = "old-approved-reference"
    jobs.images["previous-signature"] = "old-approved-image"
    jobs.pending = (signature, Future())
    assert clinical_scene.scene_image(state, [arrival]) is None
    assert session["_scene_pending"] and not session["_scene_current"]
    jobs.pending[1].set_exception(ImageConsistencyError("mismatch", ("expression",)))
    assert clinical_scene.scene_image(state, [arrival]) is None
    assert session["_scene_failed"] and not session["_scene_pending"] and not session["_scene_current"]
    jobs.failed.clear()
    jobs.images[signature] = "approved-current-image"
    assert clinical_scene.scene_image(state, [arrival]) == "approved-current-image"
    assert session["_scene_current"] and not session["_scene_failed"]


def test_scene_image_schedules_screened_functions_and_configurable_review_model(monkeypatch, state, pool):
    session = {"_attempt_id": "new-encounter"}
    monkeypatch.setattr(clinical_scene, "st", SimpleNamespace(session_state=session))
    monkeypatch.setattr(clinical_scene, "setting", lambda name, default="": {
        "OPENAI_API_KEY": "test-key", "MRS_IMAGE_MODEL": "image-model",
        "MRS_IMAGE_REVIEW_MODEL": " review-model ",
    }.get(name, default))
    assert clinical_scene.scene_image(state, [{"kind": "presentation"}]) is None
    callback = pool.calls[0][0]
    assert isinstance(callback, partial) and callback.func is scene_pipeline.screened_scene
    assert callback.keywords["review_model"] == "review-model"
    assert callable(callback.keywords["progress"])
    assert session["_scene_jobs"].status(appearance_signature(state))["queued"]
    assert session["_scene_pending"] and not session["_scene_current"]
