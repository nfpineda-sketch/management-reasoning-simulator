"""Common bilingual quantity and route primitives for both order adapters."""
import re
import unicodedata

def _normalize(text):
    text = unicodedata.normalize("NFKD", str(text or "").replace("µ", "u").replace("μ", "u"))
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    text = text.replace("’", "'")
    # A decimal comma is numeric, whereas a comma separating orders is not.
    return re.sub(r"(?<=\d),(?=\d)", ".", text)

def _route(text):
    found = []
    for route, pattern in (
        ("IV", r"\b(?:iv|ev|intravenous|intravenously|intravenos[ao])\b"),
        ("IO", r"\b(?:io|intraosseous|intraose[ao])\b"),
        ("IM", r"\b(?:im|intramuscular)\b"),
        ("PO", r"\b(?:po|vo|oral|orally|por boca|por via oral)\b"),
        ("IN", r"\bintranasal\b|\bin\s*(?:now|ahora)?\s*$"),
        ("nebulized", r"\b(?:nebulized|nebulised|nebulization|nebulizado|nebulizada|nebulizar|nebulize|neb)\b"),
        ("inhaled", r"\b(?:inhaled|inhalado|inhalada)\b"),
        ("SC", r"\b(?:sc|sq|subcutaneous|subcutane[ao])\b"),
    ):
        if re.search(pattern, text):
            found.append(route)
    return found[0] if len(found) == 1 else None

def _amount(text, units):
    matches = list(re.finditer(r"(?<![\w.])(-?(?:\d+(?:\.\d+)?|\.\d+))\s*(" + units + r")\b", text))
    if len(matches) != 1:
        return None, None
    return float(matches[0][1]), matches[0][2]
