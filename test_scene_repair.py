"""Targeted repair stays source-bounded and makes one genuine SDK image edit."""
import base64
from copy import deepcopy
from email import message_from_bytes
from email.policy import default
from io import BytesIO
import json
from types import SimpleNamespace

import httpx
from openai import OpenAI
from PIL import Image
import pytest

from scene_errors import SceneImageError
from scene_repair import repair_prompt, repair_scene


PRIVATE = "PRIVATE_PROVIDER_CASE_LEARNER_TEXT"


@pytest.fixture
def current_state():
    return {
        "encounter_spec": {"clinical_case": {
            "patient": {"age_years": 72, "sex": "female", "name": PRIVATE},
            "history": {"chief_complaint": [PRIVATE]}, "diagnosis": PRIVATE,
        }},
        "observable": {"mental_status": "Drowsy", "work_of_breathing": "Increased",
                       "hr": 119, "spo2": 87, "sbp": 83,
                       "visual": {"expression": "markedly uncomfortable", "skin_color": "mild pallor",
                                  "diaphoresis": "mild", "mottling": False}},
        "treatments": {}, "hidden": {"diagnosis": PRIVATE}, "learner_order": PRIVATE,
    }


def encoded_image(size=(1536, 1024), color="white", format="PNG"):
    output = BytesIO()
    Image.new("RGB", size, color).save(output, format=format)
    return base64.b64encode(output.getvalue()).decode("ascii")


@pytest.fixture(scope="module")
def images():
    return encoded_image(color="white"), encoded_image(color="gray")


def multipart(request):
    message = message_from_bytes(
        b"Content-Type: " + request.headers["content-type"].encode() + b"\r\n\r\n" + request.read(),
        policy=default,
    )
    return [(part.get_param("name", header="content-disposition"), part.get_filename(),
             part.get_payload(decode=True)) for part in message.iter_parts()]


@pytest.mark.parametrize("with_reference", [False, True])
@pytest.mark.parametrize("model,high_fidelity", [("gpt-image-1.5", True), ("gpt-image-1", True),
                                               ("gpt-image-2", False)])
def test_real_sdk_sends_correct_images_once_and_preserves_request_contract(
        current_state, images, with_reference, model, high_fidelity):
    candidate, original = images
    calls = []

    def respond(request):
        calls.append((request.method, request.url.path, multipart(request)))
        return httpx.Response(200, json={"created": 1, "data": [{"b64_json": candidate}]})

    before = deepcopy(current_state)
    with OpenAI(api_key="test-key", max_retries=0,
                http_client=httpx.Client(transport=httpx.MockTransport(respond))) as client:
        result = repair_scene(candidate, current_state, "", model, failed_checks=["gaze_and_eyelids"],
                              reference_b64=original if with_reference else None, client=client)
    assert result == candidate and current_state == before
    assert len(calls) == 1 and calls[0][:2] == ("POST", "/v1/images/edits")
    fields = {name: body.decode() for name, filename, body in calls[0][2] if filename is None}
    files = [(name, filename, body) for name, filename, body in calls[0][2] if filename is not None]
    assert fields["model"] == model and fields["size"] == "1536x1024"
    assert fields["quality"] == "low" and fields["output_format"] == "png" and fields["n"] == "1"
    assert fields.get("input_fidelity") == ("high" if high_fidelity else None)
    assert files[0] == ("image[]", "rejected-candidate.png", base64.b64decode(candidate))
    assert len(files) == (2 if with_reference else 1)
    if with_reference:
        assert files[1] == ("image[]", "approved-original.png", base64.b64decode(original))
    assert PRIVATE not in fields["prompt"]
    assert '"mental_status": "drowsy"' in fields["prompt"]
    assert "72-year-old woman" in fields["prompt"]


def test_repair_uses_exact_current_findings_and_not_hidden_or_provider_text(current_state):
    prompt = repair_prompt(current_state, ["gaze_and_eyelids", "expression"])
    assert "SAME instant and clinical state" in prompt
    assert "Mild remains mild" in prompt
    assert '"skin_color": "mild pallor"' in prompt and '"diaphoresis": "mild"' in prompt
    assert '"work_of_breathing": "increased"' in prompt
    assert "heavy eyelids" in prompt and "subtle film of sweat" in prompt
    assert PRIVATE not in prompt
    for key in ("learner_order", "chief_complaint", "diagnosis\":", '"hr"', '"spo2"', '"sbp"'):
        assert key not in prompt
    altered = deepcopy(current_state)
    altered["hidden"] = {"diagnosis": "TOTALLY_DIFFERENT"}
    altered["observable"].update(hr=36, sbp=50, spo2=62)
    assert repair_prompt(altered, ["gaze_and_eyelids", "expression"]) == prompt


def test_original_reference_controls_identity_but_not_obsolete_clinical_state(current_state):
    current_state["treatments"] = {"oxygen": True, "oxygen_device": "nasal cannula"}
    prompt = repair_prompt(current_state, ["identity_and_framing", "respiratory_support"], has_reference=True)
    assert "Image 2 is the APPROVED ORIGINAL" in prompt
    assert "even when Image 1 differs" in prompt
    assert "current appearance contract below overrides both images" in prompt
    assert "remove conflicting or obsolete interfaces" in prompt
    assert '"respiratory_support": "nasal cannula"' in prompt
    assert "any layout needed for correct framing" in prompt
    assert "entire rightmost 34%" in prompt
    assert "head and hands clearly visible" in prompt


@pytest.mark.parametrize("failed", [[], (), None, "expression", [PRIVATE], ["expression", PRIVATE],
                                    ["expression", {}], {"expression": PRIVATE}])
def test_untrusted_or_empty_failed_check_lists_never_reach_provider(current_state, images, failed):
    calls = []
    client = SimpleNamespace(images=SimpleNamespace(edit=lambda **kwargs: calls.append(kwargs)))
    with pytest.raises(SceneImageError) as failure:
        repair_scene(images[0], current_state, "test", failed_checks=failed, client=client)
    assert failure.value.reference == "IMAGE-REPAIR-CONTRACT"
    assert PRIVATE not in str(failure.value) and not calls


@pytest.mark.parametrize("patient", [{"age_years": 14, "sex": "female"},
                                      {"age_years": True, "sex": "male"},
                                      {"age_years": 70, "sex": PRIVATE}, None])
def test_invalid_demographics_cannot_be_copied_from_rejected_candidate(current_state, images, patient):
    current_state["encounter_spec"]["clinical_case"]["patient"] = patient
    with pytest.raises(SceneImageError) as failure:
        repair_scene(images[0], current_state, "test", failed_checks=["identity_and_framing"],
                     client=SimpleNamespace(images=None))
    assert failure.value.reference == "IMAGE-REPAIR-CONTRACT"


def test_unrecognized_oxygen_interface_blocks_repair(current_state, images):
    current_state["treatments"] = {"oxygen": True, "oxygen_device": PRIVATE}
    with pytest.raises(SceneImageError) as failure:
        repair_scene(images[0], current_state, "test", failed_checks=["respiratory_support"],
                     client=SimpleNamespace(images=None))
    assert failure.value.reference == "IMAGE-REPAIR-CONTRACT"
    assert PRIVATE not in str(failure.value)


@pytest.mark.parametrize("bad_candidate,bad_reference", [(True, False), (False, True)])
def test_both_image_inputs_are_validated_before_any_request(current_state, images, bad_candidate, bad_reference):
    calls = []
    client = SimpleNamespace(images=SimpleNamespace(edit=lambda **kwargs: calls.append(kwargs)))
    with pytest.raises(SceneImageError) as failure:
        repair_scene(PRIVATE if bad_candidate else images[0], current_state, "test",
                     failed_checks=["expression"], reference_b64=PRIVATE if bad_reference else images[1], client=client)
    assert failure.value.reference == "IMAGE-REPAIR-INVALID_IMAGE"
    assert PRIVATE not in str(failure.value) and not calls


@pytest.mark.parametrize("status,body,code", [
    (401, {}, "AUTH"), (403, {}, "ACCESS"),
    (429, {"code": "insufficient_quota"}, "QUOTA"),
    (429, {"code": "rate_limit_exceeded"}, "RATE"),
    (400, {"code": "content_policy_violation"}, "REFUSED"),
    (503, {}, "PROVIDER"),
])
def test_provider_failure_remains_safe_and_does_not_retry(current_state, images, status, body, code):
    calls = []
    def respond(request):
        calls.append(request.url.path)
        return httpx.Response(status, json={"error": {**body, "message": PRIVATE}}, request=request)

    with OpenAI(api_key="test", max_retries=0,
                http_client=httpx.Client(transport=httpx.MockTransport(respond))) as client:
        with pytest.raises(SceneImageError) as failure:
            repair_scene(images[0], current_state, "", failed_checks=["expression"], client=client)
    assert calls == ["/v1/images/edits"]
    assert failure.value.reference == "IMAGE-REPAIR-" + code
    assert PRIVATE not in str(failure.value) and PRIVATE not in json.dumps(failure.value.__dict__)
    assert failure.value.__suppress_context__


def test_sdk_transport_timeout_is_bounded_and_sanitized(current_state, images):
    calls = []
    def respond(request):
        calls.append(request.method)
        raise httpx.ReadTimeout(PRIVATE, request=request)

    with OpenAI(api_key="test", max_retries=0,
                http_client=httpx.Client(transport=httpx.MockTransport(respond))) as client:
        with pytest.raises(SceneImageError) as failure:
            repair_scene(images[0], current_state, "", failed_checks=["expression"], client=client)
    assert calls == ["POST"] and failure.value.reference == "IMAGE-REPAIR-TIMEOUT"
    assert PRIVATE not in str(failure.value)


@pytest.mark.parametrize("provider_fails", [False, True])
def test_all_input_streams_close_on_success_and_exception(current_state, images, provider_fails):
    captured = []
    def edit(**request):
        captured.extend(request["image"])
        assert all(not stream.closed for stream in captured)
        if provider_fails:
            raise RuntimeError(PRIVATE)
        return SimpleNamespace(data=[SimpleNamespace(b64_json=images[0])])

    client = SimpleNamespace(images=SimpleNamespace(edit=edit))
    if provider_fails:
        with pytest.raises(SceneImageError) as failure:
            repair_scene(images[0], current_state, "", failed_checks=["expression"],
                         reference_b64=images[1], client=client)
        assert failure.value.reference == "IMAGE-REPAIR-INTERNAL"
    else:
        repair_scene(images[0], current_state, "", failed_checks=["expression"],
                     reference_b64=images[1], client=client)
    assert len(captured) == 2 and all(stream.closed for stream in captured)


@pytest.mark.parametrize("bad_output", [None, PRIVATE, "wrong-size", "wrong-format", "missing-data"])
def test_repair_output_requires_complete_png_scene(current_state, images, bad_output):
    output = (encoded_image(size=(16, 16)) if bad_output == "wrong-size" else
              encoded_image(format="JPEG") if bad_output == "wrong-format" else bad_output)
    result = SimpleNamespace(data=[] if bad_output == "missing-data" else [SimpleNamespace(b64_json=output)])
    with pytest.raises(SceneImageError) as failure:
        repair_scene(images[0], current_state, "", failed_checks=["expression"],
                     client=SimpleNamespace(images=SimpleNamespace(edit=lambda **kwargs: result)))
    assert failure.value.reference == "IMAGE-REPAIR-INVALID_IMAGE"
    assert PRIVATE not in str(failure.value)


def test_default_client_disables_retries_and_sets_timeout(current_state, images, monkeypatch):
    settings = []
    def make_client(**kwargs):
        settings.append(kwargs)
        return SimpleNamespace(images=SimpleNamespace(edit=lambda **kwargs:
            SimpleNamespace(data=[SimpleNamespace(b64_json=images[0])])) )
    monkeypatch.setattr("openai.OpenAI", make_client)
    repair_scene(images[0], current_state, "test-key", failed_checks=["expression"])
    assert settings == [{"api_key": "test-key", "timeout": 120, "max_retries": 0}]


def test_missing_key_does_not_call_provider(current_state, images):
    with pytest.raises(SceneImageError) as failure:
        repair_scene(images[0], current_state, "", failed_checks=["expression"])
    assert failure.value.reference == "IMAGE-REPAIR-CONFIG"
