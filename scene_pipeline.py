"""Only screened current-state images may enter the encounter's image cache.

Generation and screening run in one background job using its frozen snapshot.
No clinical clock advances, retries or learner evaluation occur in this layer.
An automated screen can miss errors; it does not constitute clinical validation.
"""
import logging

from image_consistency import ImageConsistencyError, inspect_image
from patient_appearance import appearance_state, generate_appearance

SCENE_PIPELINE_VERSION = 1
_LOG = logging.getLogger(__name__)


def _screen(candidate, state, api_key, review_model, reference=None):
    try:
        result = inspect_image(candidate, appearance_state(state), api_key,
                               model=review_model, reference_b64=reference)
        if result.get("accepted") is not True:
            raise ImageConsistencyError("invalid_response")
    except ImageConsistencyError as error:
        # Fixed codes only: never log provider text, keys, photographs or case data.
        _LOG.warning("patient_image_rejected reason=%s checks=%s",
                     error.reason_code, ",".join(error.failed_checks))
        raise
    return candidate


def screened_scene(state, api_key, model, *, review_model="gpt-5-mini"):
    from clinical_scene import generate_scene
    return _screen(generate_scene(state, api_key, model), state, api_key, review_model)


def screened_appearance(reference, state, api_key, model, *, review_model="gpt-5-mini"):
    return _screen(generate_appearance(reference, state, api_key, model),
                   state, api_key, review_model, reference)
