"""A second reader for the four categories, asked only when an order is held.

The deterministic parser reads the four categories a management order has to
carry — the working model, what the learner expects, what they will reassess,
and the order itself. It reads them well when they are written the way its
patterns expect, and it misses them when they are not, and a miss stops the
encounter to ask for something the resident already wrote. That is the cost
this module exists to remove.

Two properties make it safe to put a language model in this position:

* **It never writes.** The model reports whether a category is present and
  quotes the learner's own span. Every quote is checked here against the
  learner's message and discarded unless it appears in it verbatim. Nothing the
  model composes can reach the record that the Management Trace, the Faculty
  Brief and the rubric are built from.
* **It never costs a request for an order that already passed.** It is asked
  only about the categories the deterministic pass reported missing, and only
  when a held order is the alternative. A resident who writes completely is
  never a paid request.

It cannot execute, cannot change physiology, and cannot add a category the
learner did not express: a model that answers "present" without a quote that is
in the text is treated as having answered "absent".
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import re
from typing import Any, Dict, Mapping


class ReasoningRecognitionError(RuntimeError):
    """Raised when the second reader cannot return a usable answer."""


#: The categories this module may be asked about. The action is the fourth of
#: the four and is never in question here: it is what put the order in front of
#: the gate in the first place.
CATEGORIES = ("working_model", "expected_effect", "reassessment_target",
              "management_priority", "reassessment_timing")

#: Where a recognised span is written on the parsed turn.
SLOT_FIELDS = {
    "working_model": "problem_representation",
    "expected_effect": "expected_effect",
    "reassessment_target": "reassessment_target",
    "management_priority": "management_priority",
}

_DESCRIPTIONS = {
    "working_model": "what the learner thinks is happening in this patient and why it matters now",
    "expected_effect": "what clinical or physiologic change the learner expects from what they ordered",
    "reassessment_target": "which variables, findings or measurements the learner says they will check",
    "management_priority": "which problem the learner says they are addressing first",
    "reassessment_timing": "when the learner says they will check, as an interval or a moment",
}


@dataclass(frozen=True)
class Recognition:
    """What the second reader found, after local validation."""

    slots: Dict[str, str] = field(default_factory=dict)
    absent: tuple[str, ...] = ()
    rejected: tuple[str, ...] = ()
    model: str = ""
    cues: tuple = ()
    cues_rejected: int = 0

    def __bool__(self):
        return bool(self.slots or self.cues)


#: The four states a finding can be held in, matching ``reasoning_cues``.
POLARITIES = ("present", "absent", "trend", "uncertain")


def _cue_schema():
    return {
        "type": "array",
        "maxItems": 12,
        "items": {
            "type": "object",
            "properties": {
                "finding": {"type": "string", "maxLength": 160},
                "polarity": {"type": "string", "enum": list(POLARITIES)},
                "linked": {"type": "boolean"},
                "link_marker": {"type": "string", "maxLength": 60},
            },
            "required": ["finding", "polarity", "linked", "link_marker"],
            "additionalProperties": False,
        },
    }


def _schema(fields, with_cues=False):
    properties = {
        name: {
            "type": "object",
            "properties": {
                "present": {"type": "boolean"},
                "quote": {"type": "string", "maxLength": 600},
            },
            "required": ["present", "quote"],
            "additionalProperties": False,
        }
        for name in fields
    }
    if with_cues:
        properties["cues"] = _cue_schema()
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }


_CUE_INSTRUCTIONS = """

Also list, in "cues", the clinical findings the resident named in this message:
what they observed about this patient. For each one:
- finding: the exact words they used, copied from the message. Not your
  paraphrase and not the name of a condition they concluded.
- polarity: "present" when they say it is there; "absent" when they say it is
  not ("sin crepitantes", "no wheeze"); "trend" when they describe it changing
  or persisting ("la presion mejoro", "still confused"); "uncertain" when they
  hedge it ("podria estar hipotenso").
- linked: true only when the resident said in that same sentence that this
  finding supported or questioned their interpretation.
- link_marker: the exact connector they used ("porque", "me preocupa que",
  "which suggests"), copied from the message, or the empty string.

What is not a cue:
- The order. "Dar suero" names no finding, and you may not conclude
  hypovolaemia, dehydration or blood loss from it. This is the rule that
  matters most: never work backwards from the treatment to a finding.
- The interpretation. "Creo que esta en shock" is a conclusion; "edema
  pulmonar cardiogenico" is the name of a condition. Neither is an observation.
- An expectation or a plan. "Espero que suba la presion" and "reevaluo la
  presion en 10 minutos" describe what they want and what they will do.
- Anything from the chart or the monitor that the resident did not write.

Return an empty list when the resident named no finding. A finding whose words
are not in the message is discarded, so copy accurately or leave it out.
"""


def _instructions(fields, with_cues=False):
    wanted = "\n".join(f"- {name}: {_DESCRIPTIONS[name]}" for name in fields)
    return (_base_instructions(wanted)
            + (_CUE_INSTRUCTIONS if with_cues else "")).strip()


def _base_instructions(wanted):
    return f"""
You read one message written by a resident physician during an emergency
medicine simulation and report which of the following categories the resident
expressed in it:

{wanted}

You are not a clinician here and not a teacher. You judge presence, never
quality, never correctness, never safety. A working model that is clinically
wrong is still present. An expectation that will not happen is still present.

For each category, answer with:
- present: true only when the resident actually expressed that category.
- quote: the exact span of the resident's message that expresses it, copied
  character for character from the message. Do not translate it, do not
  correct its spelling, do not tidy its grammar, do not join two separate parts
  of the message into one quote, and do not shorten it to a paraphrase. When
  present is false, quote must be the empty string.

Rules that decide the answer:
- The resident writes in English, in Spanish, or in both in the same message.
  Read either language equally; the quote stays in the language they used.
- A category expressed without its label is still present. "Esto es un edema
  pulmonar cardiogenico" is a working model. "Para subir la PAM" is an expected
  effect. "Controlo el HGT en 15 minutos" is a reassessment target and a
  reassessment timing.
- The order itself is not a working model, an expectation, or a reassessment.
  "Furosemida 40 mg IV" expresses none of these categories.
- A drug indication is not an expectation: "fentanyl for analgesia" names why
  the drug was chosen, not what the resident expects to change.
- Do not infer a category from clinical knowledge. If a resident orders oxygen
  and says nothing about why, the working model is absent even though the
  reason is obvious to you.
- Never report a category as present on the strength of the patient's chart,
  the monitor, or anything other than the resident's own words.

An answer of present with a quote that is not in the message is discarded, so
quote accurately or answer absent.
""".strip()


def _normalise(text):
    """Fold whitespace, case and accents so a quote matches how it was typed."""
    lowered = str(text or "").lower()
    for source, target in (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"),
                           ("ú", "u"), ("ü", "u"), ("ñ", "n")):
        lowered = lowered.replace(source, target)
    return re.sub(r"\s+", " ", lowered).strip(" .,;:")


def verbatim(quote, learner_text):
    """Return the learner's own span, or None when the quote is not in the text.

    The check is deliberately the last word on whether a span may be recorded.
    Case, accents and run-together whitespace are forgiven because they are how
    a quote is transcribed, not what it says; anything else is not the
    learner's language and does not enter the record.
    """
    needle = _normalise(quote)
    if not needle or len(needle) < 3:
        return None
    return str(quote).strip(" .,;:") if needle in _normalise(learner_text) else None


def recognize(
    learner_text: str,
    fields,
    *,
    cues: bool = False,
    api_key: str = "",
    model: str = "gpt-5.6-luna",
    client: Any = None,
) -> Recognition:
    """Ask the second reader about ``fields`` only, and validate every answer.

    The categories and the findings are one question, never two. A separate call
    per field, or a second call for the cues, is the shape this deliberately
    avoids (faculty specification 2026-09-23, section 8).
    """
    asked = tuple(name for name in CATEGORIES if name in set(fields or ()))
    if not asked and not cues:
        raise ReasoningRecognitionError("No category was asked about.")
    if not str(learner_text or "").strip():
        raise ReasoningRecognitionError("The learner message is empty.")
    if not str(api_key or "").strip() and client is None:
        raise ReasoningRecognitionError("OPENAI_API_KEY is not configured.")

    if client is None:
        try:
            from openai import OpenAI
        except Exception as exc:  # pragma: no cover - depends on deployment extras
            raise ReasoningRecognitionError("The OpenAI SDK is unavailable.") from exc
        client = OpenAI(api_key=api_key, timeout=12.0, max_retries=1)

    try:
        response = client.responses.create(
            model=model,
            instructions=_instructions(asked, cues),
            input=json.dumps({"resident_message": str(learner_text)}, ensure_ascii=False),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "reasoning_category_recognition",
                    "schema": _schema(asked, cues),
                    "strict": True,
                }
            },
        )
        data = json.loads(response.output_text)
    except Exception as exc:
        raise ReasoningRecognitionError("The recognition request failed.") from exc
    return validate(data, learner_text, asked, model, cues=cues)


def validate(data: Mapping[str, Any], learner_text: str, asked, model="",
             cues: bool = False) -> Recognition:
    """Keep only the categories and findings whose words are genuinely the learner's."""
    slots, absent, rejected = {}, [], []
    for name in asked:
        answer = (data or {}).get(name) or {}
        if not answer.get("present"):
            absent.append(name)
            continue
        quote = verbatim(answer.get("quote", ""), learner_text)
        if quote is None:
            rejected.append(name)
            continue
        slots[name] = quote

    found, refused = [], 0
    if cues:
        seen = set()
        for row in (data or {}).get("cues") or ():
            if not isinstance(row, dict):
                refused += 1
                continue
            finding = verbatim(row.get("finding", ""), learner_text)
            if finding is None or row.get("polarity") not in POLARITIES:
                refused += 1
                continue
            key = _normalise(finding)
            if key in seen:
                continue
            seen.add(key)
            # A link the resident is said to have expressed has to carry the
            # connector they wrote. A claimed link with no such words is kept as
            # the finding without the claim, never dropped: the observation is
            # still theirs.
            marker = verbatim(row.get("link_marker", ""), learner_text) or ""
            found.append({
                "finding": finding,
                "polarity": row["polarity"],
                "linked": bool(row.get("linked")) and bool(marker),
                "link_marker": marker,
                "contrast": False,
                "statement": "",
                "source": "model",
            })
    return Recognition(slots, tuple(absent), tuple(rejected), str(model or ""),
                       tuple(found), refused)
