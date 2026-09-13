"""Render documented appearance changes using the encounter's original photograph.

No physiology, diagnosis, or learner order is inferred here. The simulation owns
the findings; this module supplies a bounded visual brief and an image edit.
Callers own encounter-scoped caching and must not label a previous signature's
photograph as the current patient while an edit is pending or has failed.
"""
import base64
import hashlib
import json
from io import BytesIO

from PIL import Image


APPEARANCE_VERSION = 1
MAX_IMAGE_BYTES = 20_000_000

_MENTAL = {
    "alert": "Awake, eyes open with an attentive gaze toward the clinician.",
    "drowsy": "Drowsy, with heavy eyelids, an intermittently unfocused gaze and reduced engagement.",
    "obtunded": "Eyes mostly closed, markedly reduced engagement, head resting passively on the pillow.",
    "unresponsive": "Eyes closed, no purposeful gaze or visible engagement; passive resting posture.",
    "sedated": "Sedated, eyes closed and face relaxed. This describes sedation, not a cause of deterioration.",
}
_BREATHING = {
    "normal": "No visible increased breathing effort.",
    "mildly increased": "Subtle increased respiratory effort visible around the neck and shoulders.",
    "increased": "Visible increased breathing effort around the neck and shoulders.",
    "moderately increased": "Moderate respiratory effort, with visible accessory muscle use.",
    "markedly increased": "Marked respiratory effort, with pronounced accessory muscle use.",
    "severe": "Severe visible respiratory effort in the neck and shoulders.",
    "ventilator-supported": "The patient is receiving supported ventilation; do not add unsupported signs of respiratory distress.",
}
_SUPPORT = {
    "none": "No oxygen delivery interface, noninvasive mask or endotracheal tube attached.",
    "nasal cannula": "A nasal cannula with prongs at the nostrils and correctly routed oxygen tubing.",
    "non-rebreather mask": "A fitted oxygen mask with its attached reservoir bag and oxygen tubing.",
    "niv": "A fitted noninvasive ventilation face mask with straps and breathing circuit.",
    "invasive ventilation": "A secured oral endotracheal tube connected to a breathing circuit, with no noninvasive mask or cannula.",
}


def _known(value, choices):
    normalized = str(value or "").strip().lower()
    return normalized if normalized in choices else "not recorded"


def appearance_state(state):
    """Return only established facts with a visible photographic representation.

    Extremity temperature is assessed by touch. Only the explicit Mottled/Cold
    finding permits mottling; Cool/Cold and numeric perfusion values do not.
    Support selection uses executed treatment state, with airway precedence.
    Device settings and drug rates do not change the appearance of the device.
    """
    o, tr = state.get("observable", {}), state.get("treatments", {})
    if tr.get("invasive_ventilation"):
        support = "invasive ventilation"
    elif tr.get("niv"):
        support = "niv"
    elif tr.get("oxygen"):
        support = _known(tr.get("oxygen_device"), ("nasal cannula", "non-rebreather mask"))
        if support == "not recorded":
            support = "unspecified oxygen device"
    else:
        support = "none"
    return {
        "mental_status": _known(o.get("mental_status"), _MENTAL),
        "work_of_breathing": _known(o.get("work_of_breathing"), _BREATHING),
        "mottling": str(o.get("extremities", "")).strip().lower() in {"mottled/cold", "mottled"},
        "respiratory_support": support,
    }


def appearance_signature(state):
    """Stable cache key for drawable state, independent of HR/BP/time/diagnosis."""
    payload = {"version": APPEARANCE_VERSION, **appearance_state(state)}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def edit_prompt(state):
    """A source-bounded edit brief; arbitrary state strings never reach the model."""
    visible = appearance_state(state)
    support = visible["respiratory_support"]
    if support not in _SUPPORT:
        raise ValueError("The active oxygen interface has no supported visual representation.")
    observations = [
        _MENTAL.get(visible["mental_status"], "Mental status is not recorded: preserve the reference expression."),
        _BREATHING.get(visible["work_of_breathing"], "Breathing effort is not recorded: preserve reference posture."),
        "Show mottling only on the visible extremities." if visible["mottling"] else
        "Preserve the person's natural skin color; do not add mottling or a perfusion-related skin-color change.",
        _SUPPORT[support],
    ]
    return (
        "Edit this reference photograph of a fictional patient in an emergency department. "
        "It is the SAME patient later in the SAME encounter. Preserve the exact identity, age, "
        "sex, face structure, hair, skin tone, gown, blanket, room, lighting, camera position, "
        "framing, head location and the empty rightmost wall used by the software monitor. "
        "Change only the following documented observations and active respiratory interface: "
        + " ".join(observations) + " "
        "When the requested appearance differs from the reference, adjust eyelids, gaze, facial "
        "engagement and breathing-related posture conservatively, without changing facial identity. "
        "Use ONLY the respiratory interface listed above; remove other respiratory interfaces if present. "
        "Keep ECG electrodes, cuff and finger oximeter. No extra personnel, procedures, IV infusions "
        "or equipment. Do not infer a diagnosis, unconsciousness cause, pain, pallor, cyanosis, "
        "bleeding, sweating, wounds or any unlisted sign. Cold skin cannot be shown as a color change. "
        "No labels, text, numeric readings, monitors, ECG traces, icons or UI in the photograph. "
        "Photorealistic documentary medical photography. Return the entire landscape photograph."
    )


def _validated_image(encoded, *, output=False):
    if not isinstance(encoded, str) or not encoded or len(encoded) > (MAX_IMAGE_BYTES * 4 // 3 + 4):
        raise ValueError("Patient image is missing or too large.")
    try:
        raw = base64.b64decode(encoded, validate=True)
        if len(raw) > MAX_IMAGE_BYTES:
            raise ValueError("Patient image is too large.")
        with Image.open(BytesIO(raw)) as im:
            image_format, dimensions = im.format, im.size
            if image_format not in {"PNG", "JPEG", "WEBP"} or im.width * im.height > 8_000_000:
                raise ValueError("Unsupported patient image.")
            if output and (image_format != "PNG" or dimensions != (1536, 1024)):
                raise ValueError("Patient image does not match the requested scene dimensions.")
            im.verify()
    except Exception as exc:
        raise ValueError("Patient image validation failed.") from exc
    return raw, image_format


def generate_appearance(base_b64, state, api_key, model="gpt-image-1.5", client=None):
    """Edit the ORIGINAL scene, never the previous edit, returning validated PNG.

    Intended for a background worker using a frozen state snapshot. There are no
    Streamlit calls or global/session caches, so a worker cannot mutate a newer
    clinical state. Format checks are technical validation, not clinical review.
    """
    if not api_key and client is None:
        raise ValueError("Image generation is not configured.")
    prompt = edit_prompt(state)
    raw, image_format = _validated_image(base_b64)
    if client is None:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, timeout=120, max_retries=0)
    reference = BytesIO(raw)
    reference.name = "original-patient." + {"PNG": "png", "JPEG": "jpg", "WEBP": "webp"}[image_format]
    request = dict(model=model, image=reference, prompt=prompt, size="1536x1024",
                   quality="medium", output_format="png", n=1)
    # GPT Image 2 inputs are already high fidelity and reject this parameter.
    if model in {"gpt-image-1.5", "gpt-image-1"}:
        request["input_fidelity"] = "high"
    try:
        result = client.images.edit(**request)
    finally:
        reference.close()
    try:
        encoded = result.data[0].b64_json
    except (AttributeError, IndexError, TypeError) as exc:
        raise ValueError("No edited patient image was returned.") from exc
    output, _ = _validated_image(encoded, output=True)
    return base64.b64encode(output).decode("ascii")
