"""What the resident says about time, where the reader leaves it out (Phase 0, 0E).

Pre-pilot measurement safety, 2026-10-06. The clinical engine audit (§5.2, §3.3) found:

* "Wait 20 minutes", "Observe for 2 hours" and "Repeat the vital signs" were not understood:
  the resident could not let time pass or simply look again;
* "Observar por 20 minutos y reevaluar" reassessed after 0 minutes;
* "reassess" without a number took 0 minutes, and "Give 1 L LR and reassess" printed the
  vital signs from before the fluid under "After 1000 mL ...";
* an order for later ("Repeat the ECG in 30 minutes", "Give aspirin in 30 minutes") ran at
  once, its time silently dropped.

The reader (``family_parser``) is frozen after V3, so this layer works on what it returns,
in the family engine's branch of the interpreter, and records every change it makes in
``parsed["time_semantics"]`` for the Management Trace:

* **Wait.** "wait / observe / watch N minutes|hours" (EN/ES) is a reassessment after N
  minutes. A wait longer than the engine's step (120 minutes) is not shortened: the
  engine holds it and says why (``family_engine``).
* **An immediate look.** "reassess", "reassess now", "repeat (the) vital signs" without a
  number is a reassessment at the bedside after the smallest bedside interval the engine
  already uses (one examined region, ``clinical_time``), flagged ``immediate``, so the page
  says when the values were taken and never calls them "after" a treatment still running.
* **Later.** An order written for a later time ("in 30 minutes", "after 10 minutes",
  "en 30 minutos") is not run now. The pilot has no safe scheduler for timed orders (the
  engine's own deferral waits only for a result), so the order is recorded as a plan with
  the fate RECORDED_NOT_MODELLED and the limitation ``unsupported_future_execution``, and
  the resident is told that nothing was scheduled. A volume given "in 20 minutes" is a rate,
  not a later order, and is left to the reader.
"""
from __future__ import annotations

import re

import clinical_time
import order_ledger

BEDSIDE_LOOK_MIN = int(clinical_time.ACTIVE_MINUTES["examination_region"])
MAX_STEP_MIN = 120

_NUMBER = r"(?P<n>\d+(?:[.,]\d+)?)"
_WORDS = r"(?P<w>half\s+an?|an?|one|media|una|un)"
_UNIT = r"(?P<unit>minutes?|mins?|min|hours?|hrs?|hr|h|minutos?|horas?|hs?)\b"
_AMOUNT = rf"(?:{_NUMBER}|{_WORDS})\s*{_UNIT}"

_WAIT = re.compile(
    r"\b(?:wait(?:ing)?|observe|observing|watch|esper(?:ar|o|amos|emos|en|e)|observ(?:ar|o|amos|emos|en|e)|"
    r"vigil(?:ar|o|amos|emos|en))\b"
    r"(?:\s+(?:and\s+see|y\s+ver|the\s+patient|al\s+paciente|a\s+la\s+paciente|him|her|them))?"
    r"(?:\s+(?:for|during|por|durante|about|around|another|otros?|otras?|unos?|unas?|alrededor\s+de))*\s+"
    + _AMOUNT, re.I)

_VITALS = re.compile(
    r"\b(?:repeat|recheck|re-check|check|take|get|repetir|repito|repetimos|repita|tomar|tomo|tomamos|"
    r"controlar|controlo|controlamos|control\s+de)\s+"
    r"(?:the\s+|a\s+(?:new\s+)?set\s+of\s+|los\s+|las\s+|la\s+|el\s+|unos\s+|nuevos?\s+|nuevas?\s+)?"
    r"(?:(?:full\s+|complete\s+)?vital\s+signs|vitals|signos\s+vitales|constantes(?:\s+vitales)?|"
    r"blood\s+pressure|bp|presion(?:\s+arterial)?)\b", re.I)

_LATER = (
    re.compile(r"\b(?:in|within|after|en|dentro\s+de|despues\s+de|tras|luego\s+de|a\s+los)\s+"
               r"(?:about\s+|around\s+|another\s+|unos\s+|unas\s+|otros\s+)?" + _AMOUNT, re.I),
    re.compile(r"\b" + _AMOUNT + r"\s+(?:later|from\s+now|despues|mas\s+tarde)\b", re.I),
)


def _later(text, start=0, end=None):
    """The first "in 30 minutes" / "30 minutes later" in text[start:end], or None."""
    end = len(text) if end is None else min(end, len(text))
    found = [match for pattern in _LATER for match in [pattern.search(text, start, end)] if match]
    return min(found, key=lambda match: match.start()) if found else None

# A look again is timed by its own words: "reassess in 30 minutes" is not an order for later.
_LOOK = re.compile(
    r"\b(?:re-?assess\w*|re-?evaluat\w*|reevalu\w*|recontrol\w*|re-?examin\w*|monitor\w*|"
    r"vigil\w*|observ\w*|wait\w*|esper\w*|vital\s+signs|vitals|signos\s+vitales|constantes|"
    r"blood\s+pressure|presion)\b", re.I)

# A time that measures how long something runs, not when it starts.
_DURATION = re.compile(
    r"\b(?:over|run(?:ning)?\s+(?:in|over)|infus\w*|durante|a\s+pasar|pasar\s+en|en\s+bolo|en\s+infusion|"
    r"per\s+(?:minute|hour)|por\s+(?:minuto|hora)|/\s*(?:min|h|hr|hora))\b", re.I)

_VOLUME_TYPES = {"fluid", "blood", "oxygen"}
# A destination's time belongs to its plan (a follow-up "in 48 hours", a discharge "in 2 hours"):
# the reader already records it as a plan or a follow-up, and this layer leaves it there.
_PLAN_TYPES = {"disposition"}
_FOLLOW_UP = re.compile(r"\b(?:control|follow[- ]?up|seguimiento|cita|appointment|alta|discharge|"
                        r"policlinic\w*|clinic)\b", re.I)

_REPEAT_QUESTION = re.compile(r"\bto repeat\b", re.I)


def _minutes(match):
    groups = match.groupdict()
    unit = (groups.get("unit") or "").lower()
    if groups.get("n"):
        amount = float(groups["n"].replace(",", "."))
    else:
        word = " ".join((groups.get("w") or "").lower().split())
        amount = 0.5 if word.startswith(("half", "media")) else 1.0
    hours = unit.startswith(("h", "hora"))
    return int(round(amount * (60 if hours else 1)))


def _parse(text):
    from family_parser import parse_family_actions
    return parse_family_actions(text)


def _same(action, other):
    if action.get("type") != other.get("type"):
        return False
    for key in ("diagnostic", "requested_diagnostic", "agent", "agent_name"):
        if action.get(key) or other.get(key):
            if action.get(key) != other.get(key):
                return False
    return True


def _note(parsed, rule, **detail):
    parsed.setdefault("time_semantics", []).append({"rule": rule, **detail})


def _later_orders(text, parsed):
    """Orders written for a later time: taken out of this turn and recorded as plans."""
    folded, pieces = order_ledger._clauses(text)
    _, index = order_ledger._fold_map(text)
    actions = parsed.setdefault("actions", [])
    for _sentence, _terminator, clause, start in pieces:
        when = _later(clause)
        if not when or _LOOK.search(clause) or _DURATION.search(clause) or _FOLLOW_UP.search(clause):
            continue
        words = order_ledger._raw(text, index, start, start + len(clause))
        heard = [a for a in _parse(words).get("actions") or [] if a.get("type") != "clarification"]
        if not heard:
            stripped = (clause[:when.start()] + " " + clause[when.end():]).strip()
            heard = [a for a in _parse(stripped).get("actions") or [] if a.get("type") != "clarification"]
        if not heard or any(a.get("type") == "reassessment" or a.get("type") in _PLAN_TYPES for a in heard):
            continue
        if all(a.get("type") in _VOLUME_TYPES for a in heard):
            continue  # a volume "in 20 minutes" is a rate, not an order for later
        removed = []
        for wanted in heard:
            match = next((a for a in actions if isinstance(a, dict) and _same(a, wanted)), None)
            if match is not None:
                actions.remove(match)
                removed.append(match.get("type"))
        minutes = _minutes(when)
        # The reader may have kept the same words as a repeat plan of its own: one record.
        said = " ".join(clause.split())
        parsed["future_details"] = [detail for detail in parsed.get("future_details") or [] if not (
            isinstance(detail, dict)
            and " ".join(order_ledger.fold(detail.get("text") or "").split()) in said)]
        parsed["recognized_future_actions"] = [
            item for item in parsed.get("recognized_future_actions") or []
            if " ".join(order_ledger.fold(item).split()) not in said]
        parsed.setdefault("ledger_plans", []).append({
            "kind": "future_timed", "text": words, "in_min": minutes,
            "types": sorted({str(a.get("type")) for a in heard if a.get("type")}),
            "receipt": (f'Not done now: "{words}". An order for a later time is not carried out in this '
                        "pilot: nothing was given and nothing was scheduled. Write it again when you want it "
                        "done."),
        })
        _note(parsed, "future_timed", text=words, in_min=minutes, removed=removed)


def _wait(text, parsed):
    folded = order_ledger.fold(text)
    found = [_minutes(match) for match in _WAIT.finditer(folded)]
    if not found:
        return
    minutes = max(found)
    actions = parsed.setdefault("actions", [])
    looks = [a for a in actions if isinstance(a, dict) and a.get("type") == "reassessment"]
    if not looks:
        actions.append({"type": "reassessment", "delay_min": minutes, "wait": True})
        _note(parsed, "wait", minutes=minutes, added=True)
    elif all(not float(a.get("delay_min") or 0) for a in looks):
        for look in looks:
            look["delay_min"] = minutes
            look["wait"] = True
        _note(parsed, "wait", minutes=minutes, added=False)
    else:
        _note(parsed, "wait", minutes=minutes, added=False, kept_stated_interval=True)


def _vital_signs(text, parsed):
    folded = order_ledger.fold(text)
    asked = list(_VITALS.finditer(folded))
    if not asked:
        return
    actions = parsed.setdefault("actions", [])
    # What the reader made of "repeat the vital signs": a repeat plan, or a question about
    # which drug to repeat. Neither is what was asked.
    repeats = len(re.findall(r"\b(?:repeat|repetir|repito|repetimos|repita)\b", folded))
    vital_repeats = sum(1 for match in asked
                        if re.match(r"(?:repeat|repetir|repito|repetimos|repita)\b", match.group(0)))
    resolved = sum(1 for a in actions if isinstance(a, dict) and a.get("type") == "repeat_order")
    if repeats and repeats - vital_repeats <= resolved:
        # Every "repeat" in the text is a look: the reader's questions about what to repeat
        # ("which drug or fluid", "which units") are about nothing that was asked.
        parsed["actions"] = actions = [a for a in actions if not (
            isinstance(a, dict) and a.get("type") == "clarification" and _REPEAT_QUESTION.search(
                str(a.get("message") or "")))]
        if _REPEAT_QUESTION.search(str(parsed.get("clarification") or "")):
            parsed["clarification"] = None
    parsed["future_details"] = [detail for detail in parsed.get("future_details") or [] if not (
        isinstance(detail, dict) and detail.get("kind") == "repeat"
        and _VITALS.search(order_ledger.fold(detail.get("text") or "")))]
    parsed["recognized_future_actions"] = [
        item for item in parsed.get("recognized_future_actions") or []
        if not _VITALS.search(order_ledger.fold(item))]
    if not any(isinstance(a, dict) and a.get("type") == "reassessment" for a in actions):
        later = None
        for match in asked:
            when = _later(folded, match.end(), match.end() + 40)
            if when:
                later = _minutes(when)
        actions.append({"type": "reassessment", "delay_min": later or 0, "target": "vital signs"})
        _note(parsed, "vital_signs", minutes=later or 0)


def _immediate(parsed):
    for action in parsed.get("actions") or []:
        if isinstance(action, dict) and action.get("type") == "reassessment" \
                and not float(action.get("delay_min") or 0):
            action["delay_min"] = BEDSIDE_LOOK_MIN
            action["immediate"] = True
            _note(parsed, "immediate_reassessment", minutes=BEDSIDE_LOOK_MIN)


def apply(text, parsed):
    """The resident's time words, applied to what the reader returned (mutates and returns it)."""
    if not isinstance(parsed, dict):
        return parsed
    _later_orders(text, parsed)
    _wait(text, parsed)
    _vital_signs(text, parsed)
    _immediate(parsed)
    if parsed.get("clarification") and not any(
            isinstance(a, dict) and a.get("type") == "clarification" for a in parsed.get("actions") or []):
        parsed["clarification"] = None
    return parsed


def immediate_look(parsed):
    """True when this turn's reassessment is an immediate look at the bedside."""
    return any(isinstance(a, dict) and a.get("type") == "reassessment" and a.get("immediate")
               for a in (parsed or {}).get("actions") or [])


def interrupted_lead(interruption):
    """How the page opens the update of a wait an event cut short (0F)."""
    minutes = int(interruption.get("after_min") or 0)
    asked = int(interruption.get("requested_until_min") or 0) - (int(interruption.get("minute") or 0) - minutes)
    what = str(interruption.get("label") or "a critical change")
    return (f"The wait was interrupted after {minutes} minute{'s' if minutes != 1 else ''}"
            + (f" of the {asked} you asked for" if asked > minutes else "")
            + f", at minute {int(interruption.get('minute') or 0)}: {what}. Now, ")


def update_lead(result, parsed, treatment_labels):
    """The opening of the patient update after a turn, or None when the page writes its own.

    It says what was given and when the values were taken. A treatment still running is
    never called "after" when the look was immediate (0E), and a wait an event stopped is
    said to have stopped, at the event's minute (0F).
    """
    interrupted = (result or {}).get("interrupted")
    given = " + ".join(label for label in treatment_labels or [] if label)
    delay = (result or {}).get("reassess_delay")
    elapsed = int((result or {}).get("elapsed_min", 0) or 0)
    if interrupted:
        return (f"Given: {given}. " if given else "") + interrupted_lead(interrupted)
    if given:
        if immediate_look(parsed):
            return immediate_lead(treatment_labels, elapsed)
        return "After " + given + ", "
    if delay is not None:
        if immediate_look(parsed):
            return f"On reassessment at the bedside, {elapsed} minute{'s' if elapsed != 1 else ''} later, "
        return "On immediate reassessment, " if delay == 0 else f"After {delay} minutes, "
    return None


def immediate_lead(labels, minutes):
    """An immediate look after an order: what was ordered, and when the values were taken.

    The values are those of the patient a few minutes into the treatment, never presented as
    its result: the order is named, then the minute of the look.
    """
    ordered = " + ".join(label for label in labels if label)
    return (f"{ordered}. On reassessment at the bedside {minutes} minute{'s' if minutes != 1 else ''} after "
            "the order, ")
