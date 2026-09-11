"""Internal assignment and descriptive evidence for the first curriculum pilot.

Mappings are a local educational design, not certification or official year-level
equivalences. ACGME milestone levels and Royal College stages are not PGY years.
"""
import random

CURRICULUM_VERSION = "0.1.0"
CHALLENGES = {
    "R1-03": {
        "title": "Relate tachycardia to the patient's condition", "year": 1,
        "objective": "Explain the proposed contribution of the rhythm and compare the observed response with that explanation.",
        "evidence_fields": ("working_model", "expected_effect", "reassessment"),
        "acgme": "PC4; PC5; MK2", "royal_college": "ME 2.2; ME 2.4",
    },
    "R1-04": {
        "title": "Anticipate and check an intervention's effect", "year": 1,
        "objective": "State a testable expectation, reassess the patient, and use the observed response to inform the next decision.",
        "evidence_fields": ("expected_effect", "reassessment", "reflection"),
        "acgme": "PC1; PC6", "royal_college": "ME 2.4; ME 4.1",
    },
    "R2-01": {
        "title": "Distinguish pressure, flow, and perfusion", "year": 2,
        "objective": "Use several observations to explain persistent compromise and revisit the working model after treatment.",
        "evidence_fields": ("working_model", "management_priority", "reassessment", "reflection"),
        "acgme": "PC1; PC4; MK1; MK2", "royal_college": "ME 1.6; ME 2.4",
    },
}


def eligible_challenges(training_year):
    # This is an administrator-assigned integer, not a value to coerce from a
    # learner-controlled widget. In particular, bool and fractional years must
    # not silently enroll a resident in a different development stage.
    if isinstance(training_year, bool) or not isinstance(training_year, int) or training_year not in (1, 2, 3):
        raise ValueError("Training year must be assigned by an administrator.")
    return [key for key, value in CHALLENGES.items() if value["year"] <= training_year]


def evidence_summary(payload):
    """Presence of explicit records only; no inference of clinical competence."""
    session = payload.get("session", {}) or {}
    trace = session.get("management_trace", []) or []
    included = [e for e in trace if e.get("execution_status") in {"executed", "terminal_locked"}]
    field_map = {"working_model": "problem_representation", "management_priority": "management_priority", "expected_effect": "expected_effect"}
    out = {key: [] for key in (*field_map, "reassessment", "reflection")}
    for i, event in enumerate(included, 1):
        if event.get("execution_status") != "executed":
            continue
        reasoning = event.get("reasoning", {}) or {}
        for key, field in field_map.items():
            if str(reasoning.get(field) or "").strip():
                out[key].append(i)
        if any(a.get("type") == "reassessment" for a in event.get("interpreted_action", []) or []):
            out["reassessment"].append(i)
    reviews = session.get("precomparison_decision_review") or session.get("decision_review") or {}
    out["reflection"] = [key for key, values in reviews.items() if all(str(values.get(f) or "").strip() for f in ("working_model_update", "priority_trigger", "alternative_action", "expected_response_reassessment"))]
    return {"recorded": out, "interpretation": "Recorded evidence for faculty review; presence does not establish quality or competence."}


def assign_challenge(training_year, attempts, seed):
    """Balance exposure and revisit evidence gaps, without pass/fail automation.

    Initially expose each available challenge. Thereafter choose the largest
    gap in the most recent review, interleaving away from the last challenge
    where possible. Sandbox/abandoned/incomplete attempts never confer credit.
    """
    eligible = eligible_challenges(training_year)
    completed = sorted([a for a in attempts if a.get("status") == "completed" and not a.get("is_sandbox") and a.get("challenge_id") in eligible], key=lambda a: str(a.get("updated_at", "")))
    latest = {a["challenge_id"]: a for a in completed}
    unseen = [key for key in eligible if key not in latest]
    if unseen:
        choices, reason = unseen, "initial_exposure"
    else:
        previous = completed[-1]["challenge_id"]
        candidates = [key for key in eligible if key != previous] or eligible
        gaps = {}
        for key in candidates:
            evidence = evidence_summary(latest[key].get("payload", {}))["recorded"]
            gaps[key] = sum(not evidence[field] for field in CHALLENGES[key]["evidence_fields"])
        choices = [key for key in candidates if gaps[key] == max(gaps.values())]
        reason = "interleaved_evidence_review"
    return {"challenge_id": random.Random(seed).choice(choices), "reason": reason,
            "curriculum_version": CURRICULUM_VERSION, "assignment_seed": seed,
            "competence_decision": "Not assessed automatically"}
