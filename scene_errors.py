"""Bounded patient-image diagnostics without provider text or patient content."""

CHECK_IDS = (
    "expression", "gaze_and_eyelids", "skin_color", "mottling", "diaphoresis",
    "respiratory_posture", "respiratory_support", "identity_and_framing",
    "no_unrequested_signs",
)
STAGES = frozenset({"CREATE", "EDIT", "SCREEN"})
_MESSAGES = {
    "CONFIG": "Patient image generation is not configured.",
    "AUTH": "The patient image service could not authenticate.",
    "ACCESS": "Access to the patient image service was denied.",
    "MODEL": "The configured patient image or screening model is unavailable.",
    "QUOTA": "The patient image service has no available API quota.",
    "RATE": "The patient image service is temporarily busy.",
    "TIMEOUT": "The patient image service did not respond in time.",
    "CONNECTION": "The app could not connect to the patient image service.",
    "FORMAT": "The patient image service rejected the request format.",
    "REQUEST": "The patient image service rejected the request settings.",
    "PROVIDER": "The patient image service is temporarily unavailable.",
    "INCOMPLETE": "The patient image screen returned an unfinished response.",
    "REFUSED": "The patient image service could not complete this request.",
    "INVALID_IMAGE": "The patient image could not be read in the required format.",
    "INVALID_RESPONSE": "The patient image screen returned an invalid result.",
    "CONTRACT": "The current patient appearance could not be prepared for screening.",
    "UNCERTAIN": "The requested patient appearance could not be assessed confidently.",
    "MISMATCH": "The patient image did not match the current appearance.",
    "INTERNAL": "The app could not prepare the current patient image.",
}


class SceneImageError(ValueError):
    """Only fixed codes, fixed prose and known visual domains may cross jobs."""

    def __init__(self, code, stage, failed_checks=()):
        self.code = code if isinstance(code, str) and code in _MESSAGES else "INTERNAL"
        self.stage = stage if isinstance(stage, str) and stage in STAGES else "CREATE"
        candidates = failed_checks if isinstance(failed_checks, (tuple, list, set, frozenset)) else ()
        self.failed_checks = tuple(check for check in CHECK_IDS if check in candidates)
        self.reference = f"IMAGE-{self.stage}-{self.code}"
        self.message = _MESSAGES[self.code]
        super().__init__(f"{self.message} Reference: {self.reference}.")


def provider_image_error(error, stage):
    """Classify SDK errors by status and allowlisted codes, never their message."""
    from openai import APIConnectionError, APITimeoutError

    status = getattr(error, "status_code", None)
    body = getattr(error, "body", None)
    details = body.get("error", body) if isinstance(body, dict) else {}
    details = details if isinstance(details, dict) else {}
    code, param = details.get("code"), details.get("param")
    if isinstance(error, (APITimeoutError, TimeoutError)):
        category = "TIMEOUT"
    elif isinstance(error, APIConnectionError):
        category = "CONNECTION"
    elif status == 401:
        category = "AUTH"
    elif status == 403:
        category = "ACCESS"
    elif status == 404:
        category = "MODEL"
    elif status == 429:
        category = "QUOTA" if code in ("insufficient_quota", "billing_hard_limit_reached") else "RATE"
    elif status == 400:
        if code in ("content_policy_violation", "moderation_blocked"):
            category = "REFUSED"
        elif code == "invalid_json_schema" or param in ("text.format.schema", "response_format"):
            category = "FORMAT"
        else:
            category = "REQUEST"
    elif type(status) is int and status >= 500:
        category = "PROVIDER"
    else:
        category = "INTERNAL"
    return SceneImageError(category, stage)


def safe_image_error(error, stage):
    """Rebuild even typed errors rather than retaining exception/traceback data."""
    if isinstance(error, SceneImageError):
        return SceneImageError(error.code, error.stage, error.failed_checks)
    return provider_image_error(error, stage)
