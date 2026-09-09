"""Optional AI language-normalization layer for the clinical simulator.

The model may normalize only what the learner explicitly wrote. It never updates
patient physiology and never executes an intervention; ``app.py`` reparses the
canonical text with the existing deterministic engine before execution.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict


class AIInterpretationError(RuntimeError):
    """Raised when the optional AI layer cannot return a safe interpretation."""


@dataclass(frozen=True)
class AIInterpretation:
    canonical_text: str
    confidence: str
    ambiguities: tuple[str, ...]
    model: str


_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "canonical_text": {"type": "string", "minLength": 1, "maxLength": 6000},
        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
        "ambiguities": {
            "type": "array",
            "items": {"type": "string", "maxLength": 300},
            "maxItems": 8,
        },
    },
    "required": ["canonical_text", "confidence", "ambiguities"],
    "additionalProperties": False,
}

_INSTRUCTIONS = """
You are a conservative clinical-language normalizer for an educational emergency
medicine simulator. Convert the learner's message into clear canonical English
while preserving only information the learner explicitly supplied.

Rules:
- Always write canonical_text in English, regardless of the learner's input
  language. Accept English, Spanish, or a mixture of both in every turn.
- Never recommend care, judge correctness, or add an action, drug, dose, route,
  diagnostic test, finding, diagnosis, rationale, expected effect, monitoring
  variable, or reassessment time that is absent from the learner message.
- Preserve uncertainty, negation, temporal language, action order, quantities,
  units, routes, and whether an action is proposed, ordered, completed, or avoided.
- Preserve each numeric digit string exactly: do not add thousands separators
  and do not convert a quantity to an equivalent scale (for example, keep
  "1000 cc" rather than changing it to "1 L"). Route abbreviations may be
  translated (for example, Spanish "EV" to English "IV").
- Do not convert a retrospective statement into a new order.
- Do not treat the visible patient state as learner-authored reasoning or an order.
- Resolve spelling, abbreviations, pronouns, and mixed Spanish/English only when
  the meaning is unambiguous. Otherwise preserve the wording and list the issue in
  ambiguities.
- Treat common Spanish clinical shorthand as unambiguous when its local meaning
  is clear: for example, "1rio"/"primario" means "primary", "2rio" means
  "secondary", "post cardioversion" means "after cardioversion", and
  "etomidato" means "etomidate". Do not list a missing optional detail as an
  ambiguity; simply do not invent it.
- When the learner states an expected effect, canonical_text must express that
  clause with the exact starter "I expect..."; never weaken it to "I hope...".
- When present, express priority as "My priority is..." and reassessment as
  "Reassess [variables] in [time] minutes" so the deterministic parser can retain
  the learner-authored semantic slots.
- canonical_text must stand alone and remain semantically equivalent to the
  learner message. The deterministic simulator, not you, decides what executes
  and how physiology changes.
""".strip()


def normalize_with_ai(
    learner_text: str,
    visible_state: Dict[str, Any],
    *,
    api_key: str,
    model: str = "gpt-5.6-luna",
    client: Any = None,
) -> AIInterpretation:
    """Return a schema-constrained normalization or raise ``AIInterpretationError``."""
    if not str(learner_text or "").strip():
        raise AIInterpretationError("Learner text is empty.")
    if not str(api_key or "").strip() and client is None:
        raise AIInterpretationError("OPENAI_API_KEY is not configured.")

    if client is None:
        try:
            from openai import OpenAI
        except Exception as exc:  # pragma: no cover - depends on deployment extras
            raise AIInterpretationError("The OpenAI SDK is unavailable.") from exc
        client = OpenAI(api_key=api_key, timeout=12.0, max_retries=1)

    payload = {
        "learner_message": str(learner_text),
        "visible_patient_state_context_only": visible_state or {},
    }
    try:
        response = client.responses.create(
            model=model,
            instructions=_INSTRUCTIONS,
            input=json.dumps(payload, ensure_ascii=False),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "clinical_language_normalization",
                    "schema": _SCHEMA,
                    "strict": True,
                }
            },
        )
        data = json.loads(response.output_text)
    except Exception as exc:
        raise AIInterpretationError("The AI normalization request failed.") from exc

    canonical = str(data.get("canonical_text") or "").strip()
    confidence = str(data.get("confidence") or "low")
    ambiguities = tuple(str(item).strip() for item in data.get("ambiguities", []) if str(item).strip())
    if not canonical or confidence not in {"high", "medium", "low"}:
        raise AIInterpretationError("The AI response did not pass local validation.")
    return AIInterpretation(canonical, confidence, ambiguities, model)
