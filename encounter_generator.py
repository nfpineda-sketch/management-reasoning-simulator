"""Bounded, reproducible encounter composition for the PS001 curriculum pilot.

The optional model selects from reviewed *software* profiles and English scene
options. It cannot supply physiology, diagnoses, treatments, or free-form patient
facts. These are computationally tested teaching variants, not validated clinical
models. The existing state engine remains responsible for every intervention.

Save ``spec`` with the attempt; replay must use it rather than call the model
again. ``spec`` and ``state`` are server-side objects and contain the undisclosed
curriculum objective. Only ``presentation`` is intended for the learner at entry.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
import random
import secrets
from typing import Any


GENERATOR_VERSION = "0.10.0"
SPEC_VERSION = "mrs.ps001.encounter.v1"
DEFAULT_MODEL = "gpt-5-mini"
SUPPORTED_CHALLENGES = ("R1-03", "R1-04", "R2-01")

# Only persistent causal inputs are authored here. In particular, the engine
# recalculates fluid_responsiveness and fluid_tolerance from volume/congestion.
# Retaining normal age/history/source across profiles prevents contradictions in
# the existing PS001 diagnostic history and source-specific investigations.
PROFILES = {
    "volume_limited": {
        "label": "Reduced preload with an inflammatory contribution",
        "hidden": {
            "effective_volume": 0.28,
            "vasomotor_tone": 0.36,
            "inflammatory_drive": 0.85,
            "cardiac_function": 0.80,
            "contractile_reserve": 1.0,
            "af_causal_weight": 0.20,
            "pulmonary_congestion": 0.05,
            "low_flow_burden": 0.0,
            "tissue_perfusion": 0.33,
        },
        "observable": {"sbp": 88, "dbp": 52, "hr": 162, "crt": 5},
    },
    "rhythm_contributor": {
        "label": "Greater rhythm contribution with residual systemic illness",
        "hidden": {
            "effective_volume": 0.45,
            "vasomotor_tone": 0.42,
            "inflammatory_drive": 0.65,
            "cardiac_function": 0.84,
            "contractile_reserve": 1.0,
            "af_causal_weight": 0.60,
            "pulmonary_congestion": 0.05,
            "low_flow_burden": 0.0,
            "tissue_perfusion": 0.36,
        },
        "observable": {"sbp": 94, "dbp": 56, "hr": 174, "crt": 4},
    },
    "mixed_low_flow": {
        "label": "Reduced contractile reserve and limited preload response",
        "hidden": {
            "effective_volume": 0.58,
            "vasomotor_tone": 0.35,
            "inflammatory_drive": 0.85,
            "cardiac_function": 0.70,
            "contractile_reserve": 0.80,
            "af_causal_weight": 0.20,
            "pulmonary_congestion": 0.14,
            "low_flow_burden": 0.10,
            "tissue_perfusion": 0.30,
        },
        "observable": {"sbp": 90, "dbp": 56, "hr": 158, "crt": 5},
    },
}

_CONTEXTS = {
    "at_home": "He noticed the symptoms while walking around his home this morning.",
    "usual_walk": "He stopped his usual morning walk because he felt unwell.",
    "morning_tasks": "He could not finish his usual morning activities because of the symptoms.",
}
_SYMPTOMS = {
    "dizziness": "presents with dizziness, fatigue, and breathlessness on exertion",
    "fatigue": "presents with fatigue, reduced exercise tolerance, and lightheadedness",
    "dyspnea": "presents with exertional breathlessness, generalized weakness, and dizziness",
}
_HISTORY = (
    "He reports two days of dysuria and urinary frequency, followed by chills, poor oral intake, "
    "and progressive weakness today. He denies chest pain, gastrointestinal bleeding, vomiting, "
    "diarrhea, cough, or focal neurologic symptoms."
)
_OBJECTIVES = {
    "R1-03": "Interpret how much the tachyarrhythmia contributes to the current deterioration.",
    "R1-04": "State an expected intervention effect and compare it with serial observations.",
    "R2-01": "Distinguish arterial pressure, forward flow, and tissue perfusion during mixed deterioration.",
}
_CHOICE_SCHEMA = {
    "type": "object",
    "properties": {
        "profile_id": {"type": "string", "enum": list(PROFILES)},
        "arrival_context": {"type": "string", "enum": list(_CONTEXTS)},
        "symptom_focus": {"type": "string", "enum": list(_SYMPTOMS)},
    },
    "required": ["profile_id", "arrival_context", "symptom_focus"],
    "additionalProperties": False,
}
_INSTRUCTIONS = """
Compose one fictional emergency medicine teaching encounter using only the
provided option identifiers. Select a physiologic profile and neutral scene
options appropriate to the internal objective. All profiles retain atrial
fibrillation and a urinary infection source. Do not make the presenting complaint
an answer to the hidden objective. Do not add any patient fact, diagnosis, dose,
intervention, numeric physiology value, or free-form narration. The supplied
objective is internal and must never be included in your output. Return only the
schema-constrained option identifiers. The local engine authors all English
sentences and applies the chosen bounded physiology profile.
""".strip()


def _seed_value(seed: int | None) -> int:
    if seed is None:
        return secrets.randbelow(2**31)
    if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed < 2**31:
        raise ValueError("Encounter seed must be an integer between 0 and 2147483647.")
    return seed


def _choice_valid(choice: Any, fixed_profile: str | None = None) -> bool:
    return (
        isinstance(choice, dict)
        and set(choice) == {"profile_id", "arrival_context", "symptom_focus"}
        and isinstance(choice["profile_id"], str)
        and choice["profile_id"] in PROFILES
        and isinstance(choice["arrival_context"], str)
        and choice["arrival_context"] in _CONTEXTS
        and isinstance(choice["symptom_focus"], str)
        and choice["symptom_focus"] in _SYMPTOMS
        and (fixed_profile is None or choice["profile_id"] == fixed_profile)
    )


def _fallback_choice(seed: int, profile_id: str | None) -> dict:
    local_rng = random.Random(seed)
    return {
        "profile_id": profile_id or local_rng.choice(tuple(PROFILES)),
        "arrival_context": local_rng.choice(tuple(_CONTEXTS)),
        "symptom_focus": local_rng.choice(tuple(_SYMPTOMS)),
    }


def _safe_usage(response: Any) -> dict:
    """Record counts only, never provider errors, request text, or credentials."""
    result = {}
    usage = getattr(response, "usage", None)
    for key in ("input_tokens", "output_tokens", "total_tokens"):
        value = getattr(usage, key, None)
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            result[key] = value
    return result


def _response_choice(response: Any, fixed_profile: str | None) -> dict:
    if getattr(response, "status", None) != "completed":
        raise ValueError("incomplete_response")
    # A refusal may coexist with other content; never accept a partial success.
    for item in getattr(response, "output", ()) or ():
        for block in getattr(item, "content", ()) or ():
            if getattr(block, "type", None) == "refusal":
                raise ValueError("refused_response")
    output = getattr(response, "output_text", "")
    if not isinstance(output, str) or len(output) > 2000:
        raise ValueError("invalid_response")
    choice = json.loads(output)
    if not _choice_valid(choice, fixed_profile):
        raise ValueError("invalid_response")
    return choice


def _presentation(choice: dict, observable: dict) -> str:
    return (
        f"A 70-year-old man with hypertension and type 2 diabetes {_SYMPTOMS[choice['symptom_focus']]}. "
        f"{_CONTEXTS[choice['arrival_context']]} He cannot identify the exact onset. "
        "He was able to perform his usual activities yesterday. He is alert and conversant but appears uncomfortable. "
        f"BP is {observable['sbp']}/{observable['dbp']} mmHg, heart rate is {observable['hr']}/min, "
        f"and SpO₂ is {observable['spo2']}% on room air. "
        f"Capillary refill is approximately {observable['crt']} seconds and his distal extremities are cool. "
        "The initial ECG shows atrial fibrillation with rapid ventricular response without pre-excitation."
    )


def _spec_digest(spec: dict) -> str:
    material = {key: value for key, value in spec.items() if key != "content_sha256"}
    raw = json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def generate_encounter(
    challenge_id: str,
    base_state: dict,
    api_key: str = "",
    model: str = "",
    seed: int | None = None,
    profile_id: str | None = None,
    client: Any = None,
) -> dict:
    """Build one frozen PS001 variant; provider failure returns a local variant.

    A fixed ``profile_id`` is intended for an authorized faculty sandbox. Access
    control belongs to the calling service, not to this pure composition module.
    ``seed`` reproduces local choices and engine randomness; an AI call itself is
    not guaranteed deterministic. Store the returned specification to replay it.
    """
    if challenge_id not in SUPPORTED_CHALLENGES:
        raise ValueError("This challenge does not yet have an executable encounter family.")
    if profile_id is not None and profile_id not in PROFILES:
        raise ValueError("Unknown PS001 profile.")
    if not isinstance(base_state, dict) or base_state.get("case_id") != "PS001":
        raise ValueError("The PS001 initial state is required.")
    if base_state.get("sim_time") != 0 or any(
        base_state.get("treatments", {}).get(key, 0)
        for key in ("cardioversions", "procedural_sedations", "cumulative_crystalloid_ml")
    ):
        raise ValueError("Encounter generation requires a fresh initial state.")
    encounter_seed = _seed_value(seed)
    choice = _fallback_choice(encounter_seed, profile_id)
    source = "faculty" if profile_id else "fallback"
    fallback_reason = "not_requested" if profile_id else "not_configured"
    used_model = str(model or DEFAULT_MODEL).strip() or DEFAULT_MODEL
    usage = {}

    if api_key or client is not None:
        try:
            if client is None:
                from openai import OpenAI
                # One bounded request per new encounter; no hidden retry spending.
                client = OpenAI(api_key=api_key, timeout=15.0, max_retries=0)
            schema = deepcopy(_CHOICE_SCHEMA)
            if profile_id:
                schema["properties"]["profile_id"]["enum"] = [profile_id]
            response = client.responses.create(
                model=used_model,
                instructions=_INSTRUCTIONS,
                input=json.dumps({
                    "internal_objective": _OBJECTIVES[challenge_id],
                    "variation_seed": encounter_seed,
                    "fixed_profile": profile_id,
                    "profiles": {key: value["label"] for key, value in PROFILES.items()},
                    "arrival_contexts": _CONTEXTS,
                    "symptom_options": _SYMPTOMS,
                }),
                text={"format": {
                    "type": "json_schema", "name": "ps001_encounter_composition",
                    "schema": schema, "strict": True,
                }},
                max_output_tokens=1200,
                store=False,
            )
            usage = _safe_usage(response)
            try:
                ai_choice = _response_choice(response, profile_id)
            except (ValueError, TypeError, KeyError):
                fallback_reason = "invalid_or_incomplete_response"
            else:
                choice = ai_choice
                source = "ai"
                fallback_reason = None
        except Exception:
            # Never return raw exception strings: a provider can echo credentials
            # or request content. The local choice was already prepared safely.
            fallback_reason = "provider_unavailable"

    state = deepcopy(base_state)
    state["seed"] = encounter_seed
    profile = deepcopy(PROFILES[choice["profile_id"]])
    state["hidden"].update(profile["hidden"])
    state["observable"].update(profile["observable"])
    observable = state["observable"]
    state["hidden"]["effective_map"] = (observable["sbp"] + 2 * observable["dbp"]) / 3
    # Synchronize derived entry descriptors without advancing the clinical clock.
    h = state["hidden"]
    h["preload_state"] = h["effective_volume"]
    response = max(0.06, min(0.98, 1 / (1 + math.exp(8 * (h["effective_volume"] - 0.62)))))
    response *= max(0.35, min(1.0, 1 - 0.55 * h["pulmonary_congestion"]))
    h["preload_responsiveness"] = h["fluid_responsiveness"] = max(0.04, min(0.98, response))
    h["fluid_tolerance"] = max(0.18, min(0.72, 0.66 - 0.28 * max(0, h["effective_volume"] - 0.60) - 0.22 * h["pulmonary_congestion"]))

    presentation = _presentation(choice, observable)
    facts = {
        "age_years": 70, "sex": "male", "pronouns": "he/him",
        "comorbidities": ["hypertension", "type 2 diabetes"],
        "source": "urinary", "focused_history": _HISTORY,
    }
    spec = {
        "schema_version": SPEC_VERSION,
        "generator_version": GENERATOR_VERSION,
        "case_family": "PS001",
        "challenge_id": challenge_id,
        "seed": encounter_seed,
        "profile_id": choice["profile_id"],
        "choices": deepcopy(choice),
        "patient_facts": facts,
        "hidden_overrides": deepcopy(profile["hidden"]),
        "initial_observable": deepcopy(observable),
        "presentation": presentation,
        "provenance": {
            "source": source,
            "model": used_model if source == "ai" else None,
            "fallback_reason": fallback_reason,
            "usage": usage,
            "validation": "bounded-options-v1",
            "clinical_validation": "pilot_requires_faculty_review",
        },
    }
    spec["content_sha256"] = _spec_digest(spec)
    state["encounter_spec"] = deepcopy(spec)
    state["encounter_facts"] = deepcopy(facts)
    return {
        "spec": spec,
        "state": state,
        "presentation": presentation,
        "source": source,
        "warning": (
            "AI generation was unavailable; this encounter uses a predefined teaching variant."
            if fallback_reason in {"provider_unavailable", "invalid_or_incomplete_response"}
            else None
        ),
    }
