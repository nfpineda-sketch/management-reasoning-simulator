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

    def __bool__(self):
        return bool(self.slots)


def _schema(fields):
    return {
        "type": "object",
        "properties": {
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
        },
        "required": list(fields),
        "additionalProperties": False,
    }


def _instructions(fields):
    wanted = "\n".join(f"- {name}: {_DESCRIPTIONS[name]}" for name in fields)
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
    api_key: str = "",
    model: str = "gpt-5.6-luna",
    client: Any = None,
) -> Recognition:
    """Ask the second reader about ``fields`` only, and validate every answer."""
    asked = tuple(name for name in CATEGORIES if name in set(fields or ()))
    if not asked:
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
            instructions=_instructions(asked),
            input=json.dumps({"resident_message": str(learner_text)}, ensure_ascii=False),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "reasoning_category_recognition",
                    "schema": _schema(asked),
                    "strict": True,
                }
            },
        )
        data = json.loads(response.output_text)
    except Exception as exc:
        raise ReasoningRecognitionError("The recognition request failed.") from exc
    return validate(data, learner_text, asked, model)


def validate(data: Mapping[str, Any], learner_text: str, asked, model="") -> Recognition:
    """Keep only the categories whose quote is genuinely the learner's."""
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
    return Recognition(slots, tuple(absent), tuple(rejected), str(model or ""))
