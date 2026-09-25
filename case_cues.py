"""Whether a case's own text states a finding: the one reading every gate uses.

A declaration the resident cannot discover is refused, and "discoverable" means
the history or the examination affirms it. A negated mention -- "denies
alcohol", "no melena" -- affirms nothing. The reading is sentence by sentence:
a sentence with a negation in it never counts, which errs on the side of
asking the author for a clearer statement rather than accepting a doubtful one.

The gate of generated cases and the hypoglycaemia catalogue read cues through
here, so a bank case and a generated one are held to the same rule.
"""
import re

NEGATION = re.compile(r"\b(?:no|not|without|absent|denies|never)\b")


def history_text(case):
    """The history and the examination of a case, as one text."""
    parts = []
    for values in case.get("history", {}).values():
        parts += values if isinstance(values, list) else [values]
    parts += list(case.get("examination", {}).values())
    return " ".join(str(part) for part in parts if part)


def affirmed(text, cues):
    """True when a sentence without a negation matches one of the cue patterns."""
    for sentence in re.split(r"(?<=[.;!?])\s+|;\s*", str(text or "")):
        if NEGATION.search(sentence.lower()):
            continue
        if any(re.search(cue, sentence, re.I) for cue in cues):
            return True
    return False
