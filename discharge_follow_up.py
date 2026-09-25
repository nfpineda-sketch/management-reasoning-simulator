"""What a discharge is reassessed by: the follow-up the resident arranged.

Faculty decision 1 of 2026-09-25 ("Alta y seguimiento: opción B"). A discharge
is one of the orders that ask for the four categories, and the fourth -- what
will be checked, and when -- was read only as a check inside the encounter:
"Lo envio a su casa con control en policlinico en 48 horas" was held asking
what the resident would check. After a discharge the reassessment *is* the
follow-up: its appointment, its interval and its return instructions.

This settles the form, and nothing else. Passing it says the resident stated a
follow-up; it does not say the discharge was safe, and a vague plan is still
there for the faculty and the rubric to read. The phrase recorded is always the
resident's own words: nothing here composes a follow-up nobody wrote, and
nothing here advances the clinical clock by 48 hours.
"""
from __future__ import annotations

import re

# An appointment or a follow-up visit, with whatever follows it in the clause.
_APPOINTMENT = (r"\b(?:con\s+)?(?:re-?)?(?:control(?:es)?|seguimiento|citaci[oó]n|cita)\b(?!\s+(?:de\s+)?(?:la\s+)?"
                r"(?:alergia|crisis|dolor\s+ahora))[^.;,]*")
# Return instructions: what should bring the patient back.
_RETURN = (r"\b(?:(?:que|debe|deber[aá]|puede)\s+)?(?:le\s+(?:digo|explico|indico|pido)\s+que\s+)?"
           r"(?:regres(?:ar|e|a)|volver|vuelva|reconsult(?:ar|e|a)|acud(?:ir|a)|"
           r"consult(?:ar|e)\s+(?:de\s+nuevo|nuevamente))\b[^.;]*?\bsi\b[^.;]*")
_ALARM = r"\b(?:signos?|s[ií]ntomas?|indicaciones)\s+de\s+alarma\b[^.;,]*"
_ENGLISH = (r"\bfollow[- ]?up\b[^.;,]*|\breturn\s+precautions?\b[^.;,]*|\breturn\s+if\b[^.;]*"
            r"|\bsafety[- ]net(?:ting)?\b[^.;,]*|\b(?:see|review)\s+(?:by|with)\s+(?:the\s+)?"
            r"(?:gp|primary\s+care|clinic|family\s+doctor)\b[^.;,]*")
FOLLOW_UP = re.compile("(?:" + "|".join((_APPOINTMENT, _RETURN, _ALARM, _ENGLISH)) + ")", re.I)

# An interval or a moment: "en 48 horas", "en una semana", "manana", "in 2 days".
DATED = re.compile(
    r"\b(?:en|dentro\s+de|a\s+las|a\s+los|tras)\s+(?:\d+(?:[.,]\d+)?|una?|dos|tres|cuatro|cinco|siete|diez)\s*"
    r"(?:h|hrs?|horas?|d[ií]as?|semanas?|meses?)\b|\bma[nñ]ana\b|\bpasado\s+ma[nñ]ana\b"
    r"|\b(?:in|within)\s+(?:\d+|one|two|three|a)\s*(?:hours?|days?|weeks?)\b|\btomorrow\b", re.I)


def is_home_discharge(parsed):
    return any(action.get("type") == "disposition" and action.get("destination") == "home"
               for action in (parsed or {}).get("actions", []) or [])


def phrase(text):
    """The follow-up the resident wrote, in their words, or ''."""
    found = []
    for match in FOLLOW_UP.finditer(str(text or "")):
        clause = re.sub(r"^(?:con|y|e|and|with)\s+", "", match.group(0).strip(" ,;."), flags=re.I).strip()
        if clause and clause.lower() not in (f.lower() for f in found):
            found.append(clause)
    return "; ".join(found)


def adopt(parsed):
    """Fill a discharge's missing reassessment with the follow-up it states.

    Returns the phrase adopted, or ''. Only a discharge home, only when the
    reassessment is missing, and only the resident's own words, recorded as
    stated by them.
    """
    if not is_home_discharge(parsed):
        return ""
    reasoning = parsed.setdefault("reasoning", {})
    if reasoning.get("reassessment_target"):
        return ""
    found = phrase(parsed.get("raw_text", ""))
    if not found:
        return ""
    reasoning["reassessment_target"] = found
    reasoning.setdefault("slot_provenance", {})["reassessment_target"] = "stated"
    return found


def dated(parsed):
    """Whether a discharge's follow-up already says when: then the timing was stated."""
    if not is_home_discharge(parsed):
        return False
    target = str(((parsed or {}).get("reasoning") or {}).get("reassessment_target") or "")
    return bool(FOLLOW_UP.search(target) and DATED.search(target))
