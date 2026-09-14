"""Only screened current-state images may enter the encounter's image cache.

Generation and screening run in one background job using its frozen snapshot.
One targeted correction may follow a complete screen's known visual mismatch.
No clinical clock advances or learner evaluation occur in this layer.
An automated screen can miss errors; it does not constitute clinical validation.
"""
import logging

from image_consistency import ImageConsistencyError, inspect_image
from patient_appearance import appearance_state, generate_appearance
from scene_errors import safe_image_error
from scene_repair import repair_scene

SCENE_PIPELINE_VERSION = 9
_LOG = logging.getLogger(__name__)


class ScreenedImage(str):
    """Image bytes plus a fixed, non-diagnostic limitation retained by the cache."""

    def __new__(cls, encoded, limitations=()):
        value = super().__new__(cls, encoded)
        value.limitations = tuple(x for x in limitations if x in ('mild_skin_moisture', 'breathing_effort'))
        return value


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
            # Private troubleshooting artifact, never an accepted/current image.
            # SceneJobs owns access and clears it with its encounter.
            failure._diagnostic_candidate = candidate
            raise
        raise error from None
    return ScreenedImage(candidate, result.get('limitations', ()))


def _screen_with_correction(candidate, state, api_key, model, review_model, reference=None, progress=None):
    """Correct a known visual conflict once; every acceptance check still applies.

    Missing, refused, incomplete or uncertain review results do not authorize an
    edit. Both rejected candidates stay local to this frozen job, never in the
    session's approved-image cache. A second rejection propagates without loops.
    """
    try:
        return _screen(candidate, state, api_key, review_model, reference, progress)
    except ImageConsistencyError as failure:
        if failure.reason_code != 'mismatch' or not failure.failed_checks:
            raise
        checks = failure.failed_checks
    _progress(progress, 'REPAIR')
    try:
        corrected = repair_scene(candidate, state, api_key, model,
                                 failed_checks=checks, reference_b64=reference)
    except Exception as failure:
        raise safe_image_error(failure, 'REPAIR') from None
    # For an evolving patient the approved original, never a rejected candidate,
    # remains the identity reference. Inspect ALL domains, not only the failures.
    return _screen(corrected, state, api_key, review_model, reference, progress)


def screened_scene(state, api_key, model, *, review_model="gpt-5-mini", progress=None):
    from clinical_scene import generate_scene
    _progress(progress, "CREATE")
    try:
        candidate = generate_scene(state, api_key, model)
    except Exception as error:
        raise safe_image_error(error, "CREATE") from None
    return _screen_with_correction(candidate, state, api_key, model, review_model, progress=progress)


def screened_appearance(reference, state, api_key, model, *, review_model="gpt-5-mini", progress=None):
    _progress(progress, "EDIT")
    try:
        candidate = generate_appearance(reference, state, api_key, model)
    except Exception as error:
        raise safe_image_error(error, "EDIT") from None
    return _screen_with_correction(candidate, state, api_key, model, review_model, reference, progress)
