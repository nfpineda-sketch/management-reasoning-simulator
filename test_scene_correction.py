"""Bounded corrective rendering: only fully screened current-state images publish."""
from concurrent.futures import Future
from copy import deepcopy
import json

import pytest

import clinical_scene
from image_consistency import CHECK_IDS, ImageConsistencyError, _result
from patient_appearance import appearance_signature, appearance_state
import scene_jobs
import scene_pipeline
from scene_errors import SceneImageError


@pytest.fixture
def state():
    return {
        "observable": {
            "mental_status": "Drowsy", "work_of_breathing": "Increased",
            "visual": {"expression": "markedly uncomfortable", "skin_color": "mild pallor",
                       "mottling": False, "diaphoresis": "mild"},
            "hr": 118, "sbp": 88, "spo2": 86,
        },
        "treatments": {}, "sim_time": 0,
        "hidden": {"diagnosis": "PRIVATE_DIAGNOSIS"},
        "learner_submission": "PRIVATE_LEARNER_TEXT",
    }


class DeferredPool:
    def __init__(self):
        self.calls = []

    def submit(self, function, *args):
        future = Future()
        self.calls.append((function, args, future))
        return future

    def complete(self):
        function, args, future = self.calls[-1]
        try:
            future.set_result(function(*args))
        except Exception as error:
            future.set_exception(error)


@pytest.fixture
def pool(monkeypatch):
    pool = DeferredPool()
    monkeypatch.setattr(scene_jobs, "_POOL", pool)
    return pool


def screened_result(*failed):
    # Exercise the real all-domain result gate, while replacing network calls.
    return _result(json.dumps({
        "checks": {name: name not in failed for name in CHECK_IDS},
        "uncertain_checks": [],
    }))


def request(jobs, state):
    signature = appearance_signature(state)
    jobs.request(signature, state, "PRIVATE_KEY", "image-model",
                 scene_pipeline.screened_scene, scene_pipeline.screened_appearance,
                 progress_supported=True)
    return signature


@pytest.mark.parametrize("needs_correction", [False, True])
def test_reported_mild_sweat_uncertainty_renders_current_image_without_extra_generation(
        monkeypatch, state, pool, needs_correction):
    # Replay the reported state through the real reviewer parser, job cache and
    # renderer. Replace only external image generation and the provider response.
    import base64
    from io import BytesIO
    from types import SimpleNamespace
    from PIL import Image
    from image_consistency import inspect_image
    from test_image_consistency import Responses, passing_result
    out = BytesIO()
    Image.new('RGB', (32, 32), (40, 50, 60)).save(out, format='PNG')
    encoded = base64.b64encode(out.getvalue()).decode('ascii')
    uncertain = passing_result()
    uncertain['uncertain_checks'] = ['diaphoresis']
    response = Responses(uncertain)
    calls = {'generate': 0, 'repair': 0, 'screen': 0}
    before = deepcopy(state)

    def generate(*args):
        calls['generate'] += 1
        return encoded

    def repair(*args, **kwargs):
        calls['repair'] += 1
        return encoded

    def screen(candidate, contract, key, **kwargs):
        calls['screen'] += 1
        if needs_correction and calls['screen'] == 1:
            return screened_result('expression')
        return inspect_image(candidate, contract, key, client=SimpleNamespace(responses=response), **kwargs)

    monkeypatch.setattr(clinical_scene, 'generate_scene', generate)
    monkeypatch.setattr(scene_pipeline, 'repair_scene', repair)
    monkeypatch.setattr(scene_pipeline, 'inspect_image', screen)
    jobs = scene_jobs.SceneJobs()
    signature = request(jobs, state)
    pool.complete()
    current = jobs.current(signature)
    assert current == encoded
    assert current.limitations == ('mild_skin_moisture',)
    assert jobs.status(signature)['state'] == 'ready'
    html = clinical_scene.scene_html(current, '<div>HR 118</div>')
    assert 'background-image:url(data:image/png;base64,' + encoded in html
    assert 'Skin moisture is not discernible' in html and 'HR 118' in html
    assert 'unavailable' not in html and 'IMAGE-SCREEN-UNCERTAIN' not in html
    assert 'not discernible' not in clinical_scene.scene_html(current, '', current=False)
    assert encoded not in clinical_scene.scene_html(current, '', current=False)
    for _ in range(4):
        request(jobs, state)
        assert jobs.current(signature) is current
    assert calls == {'generate': 1, 'repair': int(needs_correction), 'screen': 1 + int(needs_correction)}
    assert len(response.calls) == 1 and state == before


def test_corrected_initial_image_is_the_only_candidate_accepted_into_cache(monkeypatch, state, pool, caplog):
    jobs = scene_jobs.SceneJobs()
    signature = appearance_signature(state)
    before = deepcopy(state)
    calls = []
    stages = []

    def generate(snapshot, key, model):
        stages.append(jobs.status(signature)["stage"])
        assert snapshot == before and snapshot is not state
        return "PRIVATE_REJECTED_INITIAL"

    def inspect(candidate, contract, key, **kwargs):
        stages.append(jobs.status(signature)["stage"])
        calls.append(("screen", candidate, deepcopy(contract), kwargs))
        assert jobs.base is None and not jobs.images
        assert contract == appearance_state(before)
        assert "PRIVATE" not in json.dumps(contract)
        assert kwargs == {"model": "gpt-5-mini", "reference_b64": None}
        if candidate == "PRIVATE_REJECTED_INITIAL":
            return screened_result("expression", "gaze_and_eyelids")
        return screened_result()

    def repair(candidate, snapshot, key, model, **kwargs):
        stages.append(jobs.status(signature)["stage"])
        calls.append(("repair", candidate, deepcopy(snapshot), kwargs))
        assert jobs.base is None and not jobs.images
        assert snapshot == before
        assert kwargs == {"failed_checks": ("expression", "gaze_and_eyelids"),
                          "reference_b64": None}
        return "APPROVED_CORRECTED_INITIAL"

    monkeypatch.setattr(clinical_scene, "generate_scene", generate)
    monkeypatch.setattr(scene_pipeline, "inspect_image", inspect)
    monkeypatch.setattr(scene_pipeline, "repair_scene", repair)
    request(jobs, state)
    pool.complete()
    assert jobs.current(signature) == "APPROVED_CORRECTED_INITIAL"
    assert jobs.base == "APPROVED_CORRECTED_INITIAL"
    assert jobs.images == {signature: "APPROVED_CORRECTED_INITIAL"}
    assert stages == ["CREATE", "SCREEN", "REPAIR", "SCREEN"]
    assert [call[0] for call in calls] == ["screen", "repair", "screen"]
    assert state == before and "PRIVATE" not in caplog.text


def test_evolved_correction_keeps_original_reference_and_frozen_state(monkeypatch, state, pool):
    jobs = scene_jobs.SceneJobs()
    jobs.base = "APPROVED_ORIGINAL"
    jobs.images["old-signature"] = jobs.base
    before = deepcopy(state)
    calls = []

    def edit(reference, snapshot, key, model):
        calls.append(("edit", reference, deepcopy(snapshot)))
        return "REJECTED_EVOLVED"

    def repair(candidate, snapshot, key, model, **kwargs):
        calls.append(("repair", candidate, deepcopy(snapshot), kwargs))
        assert kwargs["reference_b64"] == "APPROVED_ORIGINAL"
        assert kwargs["failed_checks"] == ("identity_and_framing",)
        return "CORRECTED_FROZEN_STATE"

    def inspect(candidate, contract, key, **kwargs):
        calls.append(("screen", candidate, deepcopy(contract), kwargs))
        assert contract == appearance_state(before)
        assert kwargs["reference_b64"] == "APPROVED_ORIGINAL"
        if candidate == "REJECTED_EVOLVED":
            return screened_result("identity_and_framing")
        return screened_result()

    monkeypatch.setattr(scene_pipeline, "generate_appearance", edit)
    monkeypatch.setattr(scene_pipeline, "repair_scene", repair)
    monkeypatch.setattr(scene_pipeline, "inspect_image", inspect)
    frozen_signature = request(jobs, state)
    state["observable"]["mental_status"] = "Unresponsive"
    state["sim_time"] = 4
    latest = deepcopy(state)
    latest_signature = appearance_signature(state)
    assert latest_signature != frozen_signature
    pool.complete()
    assert jobs.current(latest_signature) is None
    assert jobs.current(frozen_signature) == "CORRECTED_FROZEN_STATE"
    assert jobs.base == jobs.images["old-signature"] == "APPROVED_ORIGINAL"
    assert "REJECTED_EVOLVED" not in jobs.images.values()
    assert calls[0][2] == before and calls[2][2] == before
    assert [call[0] for call in calls] == ["edit", "screen", "repair", "screen"]
    assert state == latest


@pytest.mark.parametrize("second_failed_domain", CHECK_IDS)
def test_every_domain_is_rechecked_and_second_rejection_stops(monkeypatch, state, pool, second_failed_domain):
    jobs = scene_jobs.SceneJobs()
    screens, repairs = [], []
    monkeypatch.setattr(clinical_scene, "generate_scene", lambda *args: "REJECTED_INITIAL")

    def inspect(candidate, *args, **kwargs):
        screens.append(candidate)
        return screened_result("expression" if len(screens) == 1 else second_failed_domain)

    def repair(*args, **kwargs):
        repairs.append((args, kwargs))
        return "REJECTED_CORRECTION"

    monkeypatch.setattr(scene_pipeline, "inspect_image", inspect)
    monkeypatch.setattr(scene_pipeline, "repair_scene", repair)
    signature = request(jobs, state)
    pool.complete()
    assert jobs.current(signature) is None
    assert jobs.base is None and not jobs.images
    assert jobs.failure(signature)["failed_checks"] == (second_failed_domain,)
    assert jobs.failure(signature)["reference"] == "IMAGE-SCREEN-MISMATCH"
    request(jobs, state)
    request(jobs, state)
    assert len(pool.calls) == len(repairs) == 1
    assert screens == ["REJECTED_INITIAL", "REJECTED_CORRECTION"]


@pytest.mark.parametrize("reason,code,checks", [
    ("uncertain", None, ("expression",)),
    ("invalid_contract", None, ()),
    ("invalid_image", None, ()),
    ("not_configured", None, ()),
    ("invalid_response", None, ()),
    ("invalid_response", "REFUSED", ()),
    ("invalid_response", "INCOMPLETE", ()),
    ("provider_unavailable", "AUTH", ()),
    ("provider_unavailable", "RATE", ()),
    ("provider_unavailable", "TIMEOUT", ()),
    ("mismatch", None, ()),
])
def test_nonactionable_screen_failure_never_requests_correction(monkeypatch, state, reason, code, checks):
    failure = ImageConsistencyError(reason, checks, diagnostic_code=code)
    screens = []
    monkeypatch.setattr(clinical_scene, "generate_scene", lambda *args: "REJECTED_INITIAL")

    def inspect(*args, **kwargs):
        screens.append(args)
        raise failure

    def forbidden_repair(*args, **kwargs):
        pytest.fail("Only a complete mismatch with known failed checks permits correction")

    monkeypatch.setattr(scene_pipeline, "inspect_image", inspect)
    monkeypatch.setattr(scene_pipeline, "repair_scene", forbidden_repair)
    with pytest.raises(ImageConsistencyError) as caught:
        scene_pipeline.screened_scene(state, "test-key", "image-model")
    assert caught.value is failure and len(screens) == 1


@pytest.mark.parametrize("failure", [
    ImageConsistencyError("uncertain", ("diaphoresis",)),
    ImageConsistencyError("provider_unavailable", diagnostic_code="TIMEOUT"),
    ImageConsistencyError("invalid_response", diagnostic_code="REFUSED"),
    ImageConsistencyError("invalid_response", diagnostic_code="INCOMPLETE"),
])
def test_unsuccessful_second_screen_cannot_publish_or_request_another_edit(monkeypatch, state, pool, failure):
    jobs = scene_jobs.SceneJobs()
    screens, repairs = [], []
    monkeypatch.setattr(clinical_scene, "generate_scene", lambda *args: "INITIAL")

    def inspect(*args, **kwargs):
        screens.append(args)
        if len(screens) == 1:
            return screened_result("expression")
        raise failure

    def repair(*args, **kwargs):
        repairs.append(args)
        return "UNAPPROVED_CORRECTION"

    monkeypatch.setattr(scene_pipeline, "inspect_image", inspect)
    monkeypatch.setattr(scene_pipeline, "repair_scene", repair)
    signature = request(jobs, state)
    pool.complete()
    assert jobs.current(signature) is None and jobs.base is None and not jobs.images
    assert jobs.failure(signature)["reference"] == failure.reference
    assert len(screens) == 2 and len(repairs) == 1


def test_repair_provider_failure_is_terminal_and_has_safe_repair_stage(monkeypatch, state, pool, caplog):
    jobs = scene_jobs.SceneJobs()
    calls = []
    monkeypatch.setattr(clinical_scene, "generate_scene", lambda *args: "PRIVATE_INITIAL")

    def inspect(*args, **kwargs):
        calls.append("screen")
        return screened_result("expression")

    def repair(*args, **kwargs):
        calls.append("repair")
        raise TimeoutError("PRIVATE_PROVIDER_BODY PRIVATE_KEY")

    monkeypatch.setattr(scene_pipeline, "inspect_image", inspect)
    monkeypatch.setattr(scene_pipeline, "repair_scene", repair)
    signature = request(jobs, state)
    pool.complete()
    assert jobs.current(signature) is None and jobs.base is None and not jobs.images
    assert jobs.failure(signature)["reference"] == "IMAGE-REPAIR-TIMEOUT"
    assert calls == ["screen", "repair"] and "PRIVATE" not in caplog.text


def test_generation_failure_does_not_trigger_visual_correction(monkeypatch, state):
    def generate(*args):
        raise SceneImageError("REFUSED", "CREATE")

    def forbidden(*args, **kwargs):
        pytest.fail("No image candidate exists to inspect or correct")

    monkeypatch.setattr(clinical_scene, "generate_scene", generate)
    monkeypatch.setattr(scene_pipeline, "inspect_image", forbidden)
    monkeypatch.setattr(scene_pipeline, "repair_scene", forbidden)
    with pytest.raises(SceneImageError, match="IMAGE-CREATE-REFUSED"):
        scene_pipeline.screened_scene(state, "test-key", "image-model")
