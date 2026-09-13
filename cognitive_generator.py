"""Compose reproducible cognitive challenges from distinct authored ED families.

The model chooses a compatible family and patient variant. Clinical facts and
the executable mechanism come from that variant; the model cannot invent tests,
drug effects or diagnoses. Save the returned state/spec to replay an encounter.
"""
from copy import deepcopy
import hashlib
import json
import random
import secrets

from cognitive_catalog import BIAS_CHALLENGES, BIAS_CONTEXTS, CATALOG_VERSION

GENERATOR_VERSION = "0.16.0"
SPEC_VERSION = "mrs.cognitive.encounter.v1"


def generate_cognitive_encounter(challenge_id, base_state, api_key="", model="",
                                 seed=None, family_id=None, variant_id=None, client=None):
    from clinical_cases import FAMILIES
    if challenge_id not in BIAS_CHALLENGES:
        raise ValueError("Choose an implemented cognitive challenge.")
    if not isinstance(base_state, dict) or base_state.get("sim_time") != 0:
        raise ValueError("A fresh encounter state is required.")
    if seed is None:
        seed = secrets.randbelow(2**31)
    if type(seed) is not int or not 0 <= seed < 2**31:
        raise ValueError("Invalid encounter seed.")
    challenge = BIAS_CHALLENGES[challenge_id]
    allowed = tuple(challenge["families"])
    if family_id is not None and family_id not in allowed:
        raise ValueError("This family is not available for the selected challenge.")
    candidates = [(family, variant) for family in allowed for variant in FAMILIES[family]["variants"]
                  if (family_id is None or family == family_id)
                  and (variant_id is None or variant["id"] == variant_id)]
    if not candidates:
        raise ValueError("This patient variant is not available for the selected challenge.")
    rng = random.Random(seed)
    chosen_family, chosen_case = rng.choice(candidates)
    source, fallback = "fallback", "not_configured"
    used_model = str(model or "gpt-5-mini").strip() or "gpt-5-mini"
    usage = {}
    if api_key or client is not None:
        try:
            if client is None:
                from openai import OpenAI
                client = OpenAI(api_key=api_key, timeout=30, max_retries=0)
            schema = {
                "type": "object", "additionalProperties": False,
                "properties": {
                    "family_id": {"type": "string", "enum": sorted({f for f, _ in candidates})},
                    "variant_id": {"type": "string", "enum": [v["id"] for _, v in candidates]},
                }, "required": ["family_id", "variant_id"],
            }
            response = client.responses.create(
                model=used_model, store=False, max_output_tokens=4096,
                instructions=("Compose a fictional emergency encounter for this internal teaching objective. "
                              "Choose one compatible family and its patient variant from the supplied pairs. "
                              "Use the variation seed to vary selections. Return only identifiers. Do not add "
                              "clinical facts, physiology, doses, diagnoses, text or learner evaluations. "
                              "The objective describes a learning opportunity, not a bias detected in the learner."),
                input=json.dumps({"objective": challenge["objective"], "variation_seed": seed,
                                  "choices": [{"family_id": f, "variant_id": v["id"],
                                               "presentation": v["presentation"]} for f, v in candidates]}),
                text={"format": {"type": "json_schema", "name": "cognitive_case_selection",
                                  "strict": True, "schema": schema}})
            if getattr(response, "status", None) != "completed":
                raise ValueError("Incomplete selection")
            for item in getattr(response, "output", ()) or ():
                if any(getattr(block, "type", None) == "refusal" for block in getattr(item, "content", ()) or ()):
                    raise ValueError("Refused selection")
            raw = getattr(response, "output_text", None)
            if not isinstance(raw, str) or len(raw) > 2000:
                raise ValueError("Invalid selection")
            selection = json.loads(raw)
            if not isinstance(selection, dict) or set(selection) != {"family_id", "variant_id"}:
                raise ValueError("Invalid selection")
            match = next(((f, v) for f, v in candidates
                          if f == selection["family_id"] and v["id"] == selection["variant_id"]), None)
            if match is None:
                raise ValueError("Incompatible selection")
            chosen_family, chosen_case = match
            source, fallback = "ai", None
            for key in ("input_tokens", "output_tokens", "total_tokens"):
                count = getattr(getattr(response, "usage", None), key, None)
                if type(count) is int and count >= 0:
                    usage[key] = count
        except Exception:
            # Keep the locally prepared coherent case; never log provider text.
            fallback = "provider_or_selection_unavailable"
    case = deepcopy(chosen_case)
    context = deepcopy(BIAS_CONTEXTS.get(challenge["bias_id"], {}))
    presentation = case["presentation"]
    if context.get("prime_text"):
        presentation = context["prime_text"] + "\n\n" + presentation
    state = deepcopy(base_state)
    state.update(case_id="CE-" + hashlib.sha256(f"{seed}:{case['id']}".encode()).hexdigest()[:10],
                 engine_family=chosen_family, sim_time=0, seed=seed,
                 family_state={}, observable=deepcopy(case["observable"]),
                 diagnostics={}, diagnostic_history=[], treatment_timeline={},
                 ecg_profile=case["ecg_profile"])
    # Retain structural compatibility for existing saved trace/export readers,
    # while eliminating legacy AF, drug and inflammatory state from new cases.
    state["hidden"] = {k: (False if isinstance(v, bool) else 0.0 if isinstance(v, (int, float)) else None)
                       for k, v in base_state.get("hidden", {}).items()}
    state["treatments"] = {k: (False if isinstance(v, bool) else 0 if isinstance(v, (int, float))
                               else [] if isinstance(v, list) else None)
                           for k, v in base_state.get("treatments", {}).items()}
    o, h = state["observable"], state["hidden"]
    h.update(effective_map=(o["sbp"] + 2 * o["dbp"]) / 3,
             tissue_perfusion=.8 if o.get("crt", 2) <= 2 else .3,
             oxygen_delivery=.8 if o.get("spo2", 95) >= 94 else .4,
             pulmonary_congestion=.65 if chosen_family == "pulmonary_edema" else 0,
             cardiac_output_index=.7 if o.get("crt", 2) <= 2 else .35,
             effective_volume=.7, fluid_tolerance=.5, contractile_reserve=1.0)
    spec = {
        "schema_version": SPEC_VERSION, "generator_version": GENERATOR_VERSION,
        "catalog_version": CATALOG_VERSION, "challenge_id": challenge_id,
        "case_family": chosen_family, "variant_id": case["id"], "seed": seed,
        "patient_facts": deepcopy(case["patient"]), "clinical_case": case,
        "visual_profile": deepcopy(case["visual_profile"]), "ecg_profile": case["ecg_profile"],
        "initial_observable": deepcopy(o), "presentation": presentation,
        "teaching_context": context,
        "provenance": {"source": source, "model": used_model if source == "ai" else None,
                       "fallback_reason": fallback, "usage": usage,
                       "clinical_validation": "authored_educational_model_requires_faculty_review"},
    }
    spec["content_sha256"] = hashlib.sha256(json.dumps(spec, sort_keys=True, separators=(",", ":"),
                                                       allow_nan=False).encode()).hexdigest()
    state["encounter_spec"] = deepcopy(spec)
    state["encounter_facts"] = deepcopy(case["patient"])
    return {"state": state, "spec": spec, "presentation": presentation, "source": source,
            "warning": "AI selection unavailable; a coherent authored variant was selected locally."
                       if fallback == "provider_or_selection_unavailable" else None}
