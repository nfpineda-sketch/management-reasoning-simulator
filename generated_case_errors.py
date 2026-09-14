"""Allowlisted generation diagnostics, without provider bodies or case content."""
import logging

from generated_case_schema import GeneratedCaseError


_MESSAGES = {
    "AUTH": "The case service could not authenticate. Ask the administrator to check OPENAI_API_KEY.",
    "ACCESS": "The case service denied access. Ask the administrator to check the API project's model permissions.",
    "MODEL": "The configured case model is unavailable. Ask the administrator to check MRS_GENERATOR_MODEL and API access.",
    "QUOTA": "The case service has no available API quota. Ask the administrator to check the API project's billing and usage limits.",
    "RATE": "The case service is temporarily busy. Wait a moment and select Begin Encounter to try again.",
    "TIMEOUT": "The case service did not respond in time. Select Begin Encounter to try again.",
    "CONNECTION": "The app could not connect to the case service. Select Begin Encounter to try again.",
    "FORMAT": "The case service rejected the structured request format. Ask the administrator to check the generator's API compatibility.",
    "REQUEST": "The case service rejected the request settings. Ask the administrator to check the case model configuration.",
    "PROVIDER": "The case service is temporarily unavailable. Select Begin Encounter to try again.",
    "INCOMPLETE": "The case service returned an unfinished response. Select Begin Encounter to try again.",
    "REFUSED": "The case service could not complete this request. Select Begin Encounter to try again.",
    "JSON": "The case service returned an unreadable response. Select Begin Encounter to try again.",
    "STRUCTURE": "The proposed case response did not contain the required information. Select Begin Encounter to try again.",
    "CONTRACT": "The proposed case could not satisfy the simulator's consistency checks after a correction attempt. Select Begin Encounter to try again.",
    "REVIEW": "The new case did not pass the clinical consistency screen after one targeted repair. Report the reference and checks below to the administrator before restarting.",
    "INTERNAL": "The app could not prepare this case. Select Begin Encounter to try again; if this persists, share the reference below with the administrator.",
}
_STAGES = {"SETUP", "AUTHOR", "CORRECTION", "REVIEW"}


def generation_error(code, stage, *, validation_codes=(), review_checks=()):
    """Use only fixed public labels, even if callers pass untrusted strings."""
    code = code if code in _MESSAGES else "INTERNAL"
    stage = stage if stage in _STAGES else "SETUP"
    reference = f"CASE-{stage}-{code}"
    # Independently filter even internal callers: exception text, paths, numeric
    # patient values and provider payloads never become public troubleshooting IDs.
    from generated_case_validation import safe_validation_codes
    from types import SimpleNamespace
    checks = (safe_validation_codes(SimpleNamespace(issues=[{"code": value} for value in validation_codes]))
              if code == "CONTRACT" and validation_codes else [])
    from generated_case_schema import REVIEW_SCHEMA
    allowed_review = REVIEW_SCHEMA['properties']['checks']['properties']
    failed_review = [key for key in allowed_review if key in review_checks] if code == 'REVIEW' else []
    suffix = " Checks: " + ", ".join(checks) + "." if checks else ""
    if failed_review:
        suffix += " Review checks: " + ", ".join(failed_review) + "."
    error = GeneratedCaseError(f"{_MESSAGES[code]} No encounter has been started. Reference: {reference}.{suffix}")
    error.code, error.stage, error.reference = code, stage, reference
    error.validation_codes = checks
    error.review_checks = failed_review
    logging.getLogger(__name__).warning("Case generation stopped: %s%s", reference, suffix)
    return error


def provider_error(exc, stage):
    """Classify SDK exceptions without ever copying their messages or request data."""
    from openai import APIConnectionError, APITimeoutError

    status = getattr(exc, "status_code", None)
    body = getattr(exc, "body", None)
    details = body.get("error", body) if isinstance(body, dict) else {}
    details = details if isinstance(details, dict) else {}
    code = details.get("code")
    param = details.get("param")
    if isinstance(exc, (APITimeoutError, TimeoutError)):
        category = "TIMEOUT"
    elif isinstance(exc, APIConnectionError):
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
        category = "FORMAT" if code == "invalid_json_schema" or param in ("text.format.schema", "response_format") else "REQUEST"
    elif type(status) is int and status >= 500:
        category = "PROVIDER"
    else:
        category = "INTERNAL"
    return generation_error(category, stage)
