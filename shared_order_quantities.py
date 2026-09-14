"""Fluid quantity interpretation reused from ai-integration-v0.9.0.

Source: d783593, app.py. Kept separate from Streamlit and patient physiology.
Call only on a single, explicit fluid order after intent/ambiguity checks.
"""
import re


def _quantity_is_respiratory_support(text, start, end):
    """Return True when a liter quantity belongs to an oxygen-support clause."""
    t = text.lower()
    suffix = t[end:end + 55]

    # These continuations make the unit respiratory even when the learner omits
    # "/min", as in "O2 3lt nassal canula" or "oxygen 4 L nasal cannula".
    if re.match(
        r"\s*(?:/?\s*(?:min|minute|minutes)\b|(?:by|via|on|with|at)?\s*"
        r"(?:nas+al\s+can+ula|nc\b|non-?rebreather|nrb\b|simple\s+mask|face\s+mask))",
        suffix,
    ):
        return True

    prefix = t[:start]

    def last_match(pattern):
        matches = list(re.finditer(pattern, prefix, re.I))
        return matches[-1].start() if matches else -1

    last_oxygen = last_match(
        r"\b(?:o2|oxygen|nas+al\s+can+ula|nc|non-?rebreather|nrb|simple\s+mask|face\s+mask)\b"
    )
    last_fluid = last_match(
        r"\b(?:ns|normal\s+saline|saline|lr|lactated\s+ringers?|ringer'?s?|crystalloid|fluids?|iv|bolus)\b"
    )
    last_admin = last_match(r"\b(?:give|administer|infuse|bolus)\b")

    # The closest semantic anchor owns the quantity. A new administration verb
    # after an oxygen clause permits compact orders such as "O2 3 L, give 1 L".
    return last_oxygen > max(last_fluid, last_admin)


def parse_volume_ml(text):
    t = text.lower().replace(",", "")
    fluid = r"(?:ns|normal\s+saline|saline|lr|lactated\s+ringers?|ringer'?s?|crystalloid|fluids?)"
    liters = r"(?:l|lt|lts|liter|liters|litre|litres|litter|litters)"
    milliliters = r"(?:ml|milliliter|milliliters|millilitre|millilitres|cc)"

    # A quantity attached to a named fluid has priority over every other number
    # in a compound order. This is the critical distinction in
    # "1000 NS ... O2 3lt": 1000 is the fluid volume and 3 is the oxygen flow.
    named_patterns = (
        (rf"\b(\d+(?:\.\d+)?)\s*{milliliters}\s*(?:of\s+)?{fluid}\b", "ml"),
        (rf"\b{fluid}\s+(\d+(?:\.\d+)?)\s*{milliliters}\b", "ml"),
        (rf"\b(\d+(?:\.\d+)?)\s*{liters}\s*(?:of\s+)?{fluid}\b", "l"),
        (rf"\b{fluid}\s+(\d+(?:\.\d+)?)\s*{liters}\b", "l"),
        (rf"\b(\d+(?:\.\d+)?)\s*{fluid}\b", "shorthand"),
        (rf"\b{fluid}\s+(\d+(?:\.\d+)?)\b", "shorthand"),
    )
    for pattern, scale in named_patterns:
        m = re.search(pattern, t, re.I)
        if m:
            value = float(m.group(1))
            if scale == "l":
                value *= 1000
            elif scale == "shorthand" and value < 100:
                value *= 1000
            return int(round(value))

    word_liters = {
        "half": 500,
        "one": 1000,
        "two": 2000,
        "three": 3000,
        "four": 4000,
        "five": 5000,
    }
    for word, ml in word_liters.items():
        article = r"(?:a\s+)?" if word == "half" else ""
        if re.search(rf"\b{word}\s+{article}{liters}\s*(?:of\s+)?{fluid}\b", t, re.I):
            return ml
        if re.search(rf"\b{fluid}\s+{word}\s+{article}{liters}\b", t, re.I):
            return ml

    # Explicit mL / cc is unambiguously a fluid volume in this simulator.
    m = re.search(rf"(\d+(?:\.\d+)?)\s*{milliliters}\b", t, re.I)
    if m:
        return int(round(float(m.group(1))))

    # For unnamed liter orders, consider every candidate and exclude oxygen flow
    # by its local semantic scope, with or without an explicit "/min" suffix.
    for m in re.finditer(rf"(\d+(?:\.\d+)?)\s*{liters}\b", t, re.I):
        if not _quantity_is_respiratory_support(t, m.start(), m.end()):
            return int(round(float(m.group(1)) * 1000))

    for word, ml in word_liters.items():
        article = r"(?:a\s+)?" if word == "half" else ""
        m = re.search(rf"\b{word}\s+{article}{liters}\b", t, re.I)
        if m and not _quantity_is_respiratory_support(t, m.start(), m.end()):
            return ml

    return None
