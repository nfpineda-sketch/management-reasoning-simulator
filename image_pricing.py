"""What a patient-image request may cost, and the budget it is charged to (2026-09-26).

Two numbers are kept apart on purpose:

* the **reservation**, a conservative ceiling taken before a request is sent,
  so that no request can start unless the budget covers its worst case; and
* the **cost**, computed after the request from the token usage the provider
  reports, at the published price. It is still a calculation, not an invoice:
  the invoice is only in the provider's billing page. Where the provider
  reports no usage -- a failure, a timeout -- the reservation stays charged,
  because a failed request is not assumed to be free.

Prices were checked on 2026-09-26 against OpenAI's published pricing through a
web search restricted to developers.openai.com and openai.com; this
environment's network refuses a direct download of those pages. A model
without a verified price here cannot be used for a paid image request: its
worst case cannot be bounded, so the budget could not be respected.
"""
from __future__ import annotations

PRICING_VERSION = "2026-09-26"
SOURCE = {
    "url": "https://developers.openai.com/api/docs/pricing",
    "checked_on": "2026-09-26",
    "how": ("Web search restricted to developers.openai.com and openai.com. The direct "
            "download of the page is blocked by this environment's network policy."),
}

MICRO = 1_000_000  # micro-dollars per dollar: every amount is kept as an integer


def usd(amount_micro):
    return round((amount_micro or 0) / MICRO, 4)


# Per 1M tokens, in US dollars, as published. ``verified`` marks a price read
# from the provider's own pages on the date above; a bound is marked as such.
MODELS = {
    "gpt-image-1.5": {
        "verified": True,
        "text_input": 5.00, "image_input": 8.00, "image_output": 32.00,
        # Published per-image price for the size and quality this app requests.
        "per_image_low_1536x1024": 0.013,
    },
    # The screening model's price could not be confirmed from the provider's own
    # page (the search summary contradicted itself), so the reviewer is charged
    # at a ceiling above every figure seen: US$2.00 input, US$16.00 output per 1M.
    "gpt-5-mini": {
        "verified": False,
        "text_input": 2.00, "image_input": 2.00, "text_output": 16.00,
        "note": "Ceiling, not the published price: above both figures the search returned.",
    },
}

# The worst case of one request, in micro-dollars, for the parameters this app
# sends (1536x1024, quality low, input_fidelity high, max_output_tokens 4096).
# Each ceiling is several times what the published prices give for a normal
# request; the arithmetic is in docs/IMAGENES_PACIENTE.md.
CEILINGS = {
    ("gpt-image-1.5", "create"): 50_000,   # 2,500 text in + 1,000 image out: 0.045
    ("gpt-image-1.5", "edit"): 150_000,    # + 12,000 image in: 0.141
    ("gpt-image-1.5", "repair"): 250_000,  # two images in: 0.237
    ("gpt-5-mini", "screen"): 100_000,     # 16,000 in + 4,096 out at the ceiling: 0.0976
}

# Requests that count against the budget's request limit. A screen is billed and
# charged in dollars, but it is not a generation or an edit of an image.
IMAGE_REQUESTS = frozenset({"create", "edit", "repair"})


class PriceUnknown(ValueError):
    """No verified price or ceiling for this model and request: it cannot be sent."""


def ceiling(model, kind):
    try:
        return CEILINGS[(model, kind)]
    except KeyError:
        raise PriceUnknown(f"No price ceiling for {model} {kind}.") from None


def _tokens(usage, *path):
    value = usage
    for key in path:
        value = value.get(key) if isinstance(value, dict) else getattr(value, key, None)
        if value is None:
            return None
    return value if type(value) is int and value >= 0 else None


def usage_record(usage):
    """The provider's reported usage as plain integers, or None when it reported none."""
    if usage is None:
        return None
    record = {
        "input_tokens": _tokens(usage, "input_tokens"),
        "output_tokens": _tokens(usage, "output_tokens"),
        "image_input_tokens": _tokens(usage, "input_tokens_details", "image_tokens"),
        "text_input_tokens": _tokens(usage, "input_tokens_details", "text_tokens"),
    }
    if record["input_tokens"] is None and record["output_tokens"] is None:
        return None
    return record


def cost_from_usage(model, kind, usage):
    """Micro-dollars from reported tokens at the listed price, or None when it cannot be computed."""
    prices = MODELS.get(model)
    if prices is None or usage is None:
        return None
    input_tokens = usage.get("input_tokens") or 0
    output_tokens = usage.get("output_tokens") or 0
    image_in = usage.get("image_input_tokens")
    text_in = usage.get("text_input_tokens")
    if image_in is None and text_in is None:
        # No split reported: charge every input token at the dearer input price.
        text_in, image_in = 0, input_tokens
        if kind == "screen":
            image_in, text_in = 0, input_tokens
    if kind == "screen":
        dollars = ((text_in or 0) + (image_in or 0)) * prices["text_input"] + output_tokens * prices["text_output"]
    else:
        dollars = ((text_in or 0) * prices["text_input"] + (image_in or 0) * prices["image_input"]
                   + output_tokens * prices["image_output"])
    return int(round(dollars))  # dollars per 1M tokens x tokens = micro-dollars


# The authorization this work runs under: US$10 and 30 generation or edit
# requests, whichever comes first, retries included (administrator, 2026-09-26).
# A new authorization is a new budget with its own identifier; the ledger of an
# earlier one is never reset or reused.
DEFAULT_BUDGET = {
    "id": "imagenes-2026-09-26",
    "limit_micro": 10 * MICRO,
    "limit_requests": 30,
    "authorization": ("Administrador, 2026-09-26: hasta US$10 y un máximo de 30 solicitudes pagadas "
                      "de generación o edición de imágenes estáticas, lo que se alcance primero; "
                      "los reintentos cuentan."),
}


def configured_budget(settings):
    """The active budget: the default above, or a later authorization set by the administrator.

    ``settings`` reads a named setting (secrets or environment). A partial
    configuration is refused rather than completed with the default's numbers.
    """
    identifier = str(settings("MRS_IMAGE_BUDGET_ID") or "").strip()
    if not identifier:
        return dict(DEFAULT_BUDGET)
    try:
        limit = float(settings("MRS_IMAGE_BUDGET_USD"))
        requests = int(settings("MRS_IMAGE_BUDGET_REQUESTS"))
    except (TypeError, ValueError):
        raise ValueError("MRS_IMAGE_BUDGET_ID needs MRS_IMAGE_BUDGET_USD and MRS_IMAGE_BUDGET_REQUESTS.") from None
    if not (0 < limit <= 1000 and 0 < requests <= 10000 and len(identifier) <= 80):
        raise ValueError("The configured image budget is out of range.")
    return {"id": identifier, "limit_micro": int(round(limit * MICRO)), "limit_requests": requests,
            "authorization": str(settings("MRS_IMAGE_BUDGET_NOTE") or "Configured by the administrator.")[:500]}
