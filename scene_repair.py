"""One bounded repair of a rejected fictional patient illustration.

The caller owns screening, attempt limits and caching. A returned PNG has passed
technical validation only and must not be shown until it passes a fresh screen.
Neither a rejected candidate nor reviewer prose defines the patient's state.
"""
import base64
from contextlib import ExitStack
from io import BytesIO
import json

from patient_appearance import appearance_brief, appearance_state, _validated_image
from scene_errors import CHECK_IDS, SceneImageError, provider_image_error
from visual_observations import VISUAL_CHOICES


_SUPPORT = {
    "none", "nasal cannula", "simple mask", "non-rebreather mask", "niv",
    "bag-mask ventilation", "invasive ventilation",
}
_REPAIR_DOMAINS = {
    "expression": "facial expression",
    "gaze_and_eyelids": "eye opening, gaze and visible engagement",
    "skin_color": "skin coloration relative to baseline pigmentation",
    "mottling": "mottling of visible extremities",
    "diaphoresis": "visible sweat",
    "respiratory_posture": "neck and shoulder respiratory posture",
    "respiratory_support": "the exact active respiratory interface",
    "identity_and_framing": "patient identity and required scene framing",
    "no_unrequested_signs": "removal of unrequested clinical signs, text and equipment",
}


def _failed_domains(failed_checks):
    if not isinstance(failed_checks, (tuple, list, set, frozenset)):
        raise ValueError("A bounded failed-domain checklist is required.")
    if not failed_checks or any(type(item) is not str or item not in CHECK_IDS
                                for item in failed_checks):
        raise ValueError("A known nonempty failed-domain checklist is required.")
    return tuple(name for name in CHECK_IDS if name in failed_checks)


def _expected_appearance(state):
    expected = appearance_state(state)
    if set(expected) != {*VISUAL_CHOICES, "mottling", "respiratory_support"}:
        raise ValueError("Unsupported visible appearance contract.")
    for name, choices in VISUAL_CHOICES.items():
        if type(expected[name]) is not str or expected[name] not in choices:
            raise ValueError("Unsupported visible appearance contract.")
    if type(expected["mottling"]) is not bool or expected["respiratory_support"] not in _SUPPORT:
        raise ValueError("Unsupported visible appearance contract.")
    return expected


def repair_prompt(state, failed_checks, *, has_reference=False):
    """Use only validated demographics, bounded appearance and fixed domains."""
    # Local import avoids adding a clinical_scene/scene_pipeline import cycle.
    from clinical_scene import _patient_description

    domains = _failed_domains(failed_checks)
    person = _patient_description(state)
    expected = _expected_appearance(state)
    brief = appearance_brief(state)
    if has_reference:
        identity = (
            "Image 1 is the rejected candidate that needs correction. Image 2 is the APPROVED "
            "ORIGINAL patient photograph and is authoritative for the SAME fictional patient's "
            "identity, face structure, age, sex, hair, baseline pigmentation, room and camera position, "
            "even when Image 1 differs. The input order does not make Image 1 authoritative. "
            "Do not copy obsolete clinical expression, eye opening, sweat, coloration or respiratory "
            "interfaces from Image 2: the current appearance contract below overrides both images. "
        )
    else:
        identity = (
            "Image 1 is the rejected candidate. Keep its fictional identity, natural baseline "
            "pigmentation, room and camera continuity where compatible with the validated "
            "demographics and required framing. Do not preserve an incorrect apparent age or sex. "
            "Its expression, clinical signs and equipment are not authoritative. "
        )
    personnel = (
        "Only the necessary gloved clinician hands maintaining the mask seal and compressing the "
        "manual ventilation bag may enter the scene; no additional personnel or bodies. "
        if expected["respiratory_support"] == "bag-mask ventilation" else
        "No extra personnel or clinician hands. "
    )
    return (
        "Correct a rejected photograph of a fictional emergency department patient at the SAME "
        "instant and clinical state. This is a visual correction, not a later time, new intervention, "
        "deterioration or recovery. The validated patient is a " + person + ". " + identity +
        "A complete visual screen found conflicts in these domains: " +
        "; ".join(_REPAIR_DOMAINS[name] for name in domains) + ". "
        "Prioritize those corrections while keeping every domain compatible with the full current "
        "appearance contract: " + json.dumps(expected, sort_keys=True) + ". " + brief + " "
        "Maintain exactly the documented degree of each sign. Mild remains mild; do not amplify "
        "pallor, sweating, discomfort or breathing effort to make them easier to detect. Never add "
        "theatrical suffering or make the patient healthier, happier or sicker than specified. "
        "Unknown or not recorded findings are not permission to invent a sign. A still photograph "
        "cannot establish actual responsiveness, perfusion, respiratory motion or respiratory rate. "
        "Change only visible conflicts and any layout needed for correct framing: head and hands "
        "clearly visible, patient centered at about 40% of the image width, the entire rightmost 34% "
        "reserved as empty dark hospital wall for the software monitor. Retain natural skin texture, "
        "a hospital gown and white blanket, ECG electrodes, blood pressure cuff and finger oximeter. "
        "Use only the current respiratory interface; remove conflicting or obsolete interfaces. " + personnel +
        "Do not infer a diagnosis, symptom, injury, cyanosis, bleeding, pain location, infusion or "
        "procedure. Do not preserve such unrequested signs just because they are in an input image. "
        "Remove monitor screens, numeric readings, ECG traces, text, labels, logos, icons and UI from "
        "the photograph. Photorealistic documentary medical photography with soft clinical lighting. "
        "Return the entire landscape photograph."
    )


def repair_scene(candidate_b64, state, api_key, model="gpt-image-1.5", *,
                 failed_checks, reference_b64=None, client=None):
    """Request exactly one targeted edit; never screen, retry or cache its result."""
    if not api_key and client is None:
        raise SceneImageError("CONFIG", "REPAIR")
    try:
        prompt = repair_prompt(state, failed_checks, has_reference=reference_b64 is not None)
    except (ValueError, TypeError, KeyError, AttributeError):
        raise SceneImageError("CONTRACT", "REPAIR") from None
    try:
        inputs = [("rejected-candidate", *_validated_image(candidate_b64))]
        if reference_b64 is not None:
            inputs.append(("approved-original", *_validated_image(reference_b64)))
    except ValueError:
        raise SceneImageError("INVALID_IMAGE", "REPAIR") from None

    with ExitStack() as stack:
        images = []
        for name, raw, image_format in inputs:
            stream = stack.enter_context(BytesIO(raw))
            stream.name = name + "." + {"PNG": "png", "JPEG": "jpg", "WEBP": "webp"}[image_format]
            images.append(stream)
        request = dict(model=model, image=images, prompt=prompt, size="1536x1024",
                       quality="medium", output_format="png", n=1)
        if model in {"gpt-image-1.5", "gpt-image-1"}:
            request["input_fidelity"] = "high"
        try:
            if client is None:
                from openai import OpenAI
                client = OpenAI(api_key=api_key, timeout=120, max_retries=0)
            result = client.images.edit(**request)
        except Exception as error:
            raise provider_image_error(error, "REPAIR") from None

    try:
        raw, _ = _validated_image(result.data[0].b64_json, output=True)
    except (ValueError, AttributeError, IndexError, TypeError):
        raise SceneImageError("INVALID_IMAGE", "REPAIR") from None
    return base64.b64encode(raw).decode("ascii")
