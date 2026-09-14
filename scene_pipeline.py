"""Only screened current-state images may enter the encounter's image cache.

Generation and screening run in one background job using its frozen snapshot.
No clinical clock advances, retries or learner evaluation occur in this layer.
An automated screen can miss errors; it does not constitute clinical validation.
"""
import logging

from image_consistency import ImageConsistencyError, inspect_image
from patient_appearance import appearance_state, generate_appearance
from scene_errors import safe_image_error

SCENE_PIPELINE_VERSION = 2
_LOG = logging.getLogger(__name__)


def _progress(callback, stage):
    if callback is not None:
        try:
            callback(stage)
        except Exception:
            # Status reporting must not change the success or failure of a screen.
            pass


def _screen(candidate, state, api_key, review_model, reference=None, progress=None):
    _progress(progress, "SCREEN")
    try:
        result = inspect_image(candidate, appearance_state(state), api_key,
                               model=review_model, reference_b64=reference)
        if result.get("accepted") is not True:
            raise ImageConsistencyError("invalid_response")
    except Exception as failure:
        error = safe_image_error(failure, "SCREEN")
        # Fixed codes only: never log provider text, keys, photographs or case data.
        _LOG.warning("patient_image_rejected reference=%s checks=%s",
                     error.reference, ",".join(error.failed_checks))
        if isinstance(failure, ImageConsistencyError):
            raise
        raise error from None
    return candidate


def screened_scene(state, api_key, model, *, review_model="gpt-5-mini", progress=None):
    from clinical_scene import generate_scene
    _progress(progress, "CREATE")
    try:
        candidate = generate_scene(state, api_key, model)
    except Exception as error:
        raise safe_image_error(error, "CREATE") from None
    return _screen(candidate, state, api_key, review_model, progress=progress)


def screened_appearance(reference, state, api_key, model, *, review_model="gpt-5-mini", progress=None):
    _progress(progress, "EDIT")
    try:
        candidate = generate_appearance(reference, state, api_key, model)
    except Exception as error:
        raise safe_image_error(error, "EDIT") from None
    return _screen(candidate, state, api_key, review_model, reference, progress)
