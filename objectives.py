"""Local simulated-management objectives and recorded evidence for faculty review.

The identifiers link to Royal College EPAs, but these records assess only the
components that this simulator can demonstrate. They do not attest completion
of a whole workplace EPA. Targets were supplied by the program owner and have
not been independently verified as official EPA observation requirements.

These objectives are distinct from the R1-03/R1-04/R2-01 local encounter
challenges. Neither the counts nor the depth/autonomy tags establish a PGY,
ACGME milestone level, competence decision, or automatic passing result.
"""

from copy import deepcopy


OBJECTIVE_CATALOG_VERSION = "0.1.0"
TARGET_SOURCE = (
    "Program target supplied by the user; official EPA count not independently verified."
)
DEPTH_LEVELS = ("foundational", "integrated", "complex")
AUTONOMY_LEVELS = ("guided", "prompted", "independent")
DEPTH_DESCRIPTIONS = {
    "foundational": "A focused management decision with explicit supporting evidence.",
    "integrated": "Related decisions integrating response, reassessment, and competing priorities.",
    "complex": "Management reasoning under uncertainty or evolving, competing clinical problems.",
}
AUTONOMY_DESCRIPTIONS = {
    "guided": "Faculty or structured guidance directed the management reasoning.",
    "prompted": "Prompts were needed before the resident completed the reasoning.",
    "independent": "The observed reasoning was completed without additional guidance or prompts.",
}


OBJECTIVES = {
    "TD1": {
        "title": "Recognize instability and initiate support",
        "target": 10,
        "scope": "Recognize instability from supplied findings and justify initial simulated support and reassessment.",
        "supported": True,
        "limitation": "Does not assess real help activation, teamwork, or hands-on basic life support.",
    },
    "F1": {
        "title": "Initiate critical patient resuscitation",
        "target": 15,
        "scope": "Prioritize and initiate available simulated resuscitation interventions and assess their response.",
        "supported": True,
        "limitation": "Does not assess assisting an actual resuscitation team or procedural performance.",
    },
    "C1": {
        "title": "Manage critical patient resuscitation",
        "target": 40,
        "scope": "Integrate simulated resuscitation decisions, reassessment, and revision of the working model.",
        "supported": True,
        "limitation": "Does not assess actual team leadership or the full breadth of critical illness.",
    },
    "C2": {
        "title": "Manage critical trauma resuscitation",
        "target": 25,
        "scope": "Reserved for future trauma-specific simulated management encounters.",
        "supported": False,
        "limitation": "Critical trauma encounters are not implemented in the current curriculum pilot.",
    },
    "C3": {
        "title": "Manage airway and ventilation",
        "target": 20,
        "scope": "Reason about available simulated oxygen, airway preparation, and ventilation support and reassess the response.",
        "supported": True,
        "limitation": "Does not assess laryngoscopy, tube placement, manual ventilation, or other hands-on airway skills.",
    },
    "C4": {
        "title": "Manage procedural sedation and analgesia",
        "target": 20,
        "scope": "Justify available simulated procedural sedation, anticipate its consequences, and reassess the patient.",
        "supported": True,
        "limitation": "The current case supports a limited sedation context; it does not assess the full range of analgesia or bedside procedural skills.",
    },
    "C14": {
        "title": "Use POCUS to guide management",
        "target": 50,
        "scope": "Request supplied POCUS findings, interpret their management implications, and relate them to subsequent decisions.",
        "supported": True,
        "limitation": "Does not assess probe handling, image acquisition, or independent interpretation of a complete ultrasound study.",
    },
    "C15": {
        "title": "Provide end-of-life care",
        "target": 5,
        "scope": "Reserved for future end-of-life care and communication encounters.",
        "supported": False,
        "limitation": "End-of-life care and communication encounters are not implemented in the current curriculum pilot.",
    },
}
for _objective in OBJECTIVES.values():
    _objective["target_source"] = TARGET_SOURCE
    _objective["assessment_scope"] = "simulated_management_component"
del _objective


_REVIEW_FIELDS = (
    "working_model_update", "priority_trigger", "alternative_action",
    "expected_response_reassessment",
)
_DECISION_FIELDS = (
    "trace_schema", "decision_time_min", "response_time_min", "elapsed_minutes",
    "learner_input", "interpreted_action", "reasoning", "reasoning_observations",
    "reasoning_gate", "execution_status", "action_summaries",
)
_STATE_FIELDS = (
    "case_id", "sim_time_min", "observable", "diagnostics", "treatments",
    "treatment_timeline",
)


def evidence_items(payload):
    """Return explicit recorded decisions and completed reflection entries.

    This function selects evidence; it does not grade quality or decide which
    objective was demonstrated. Faculty must read the evidence and make that
    decision. A favorable patient outcome, an action keyword, or a filled field
    never creates a pass.

    Trace references use the zero-based raw array index, not the filtered
    display ordinal. Appending another event therefore cannot change a saved
    reference. Labels follow the existing Management Trace display, which
    includes terminal-locked entries; those nonexecuted entries are not returned
    as executed evidence here. The store binds these references to the frozen
    payload revision and snapshot when an assessment is recorded.
    """
    if not isinstance(payload, dict):
        return []
    session = payload.get("session")
    if not isinstance(session, dict):
        return []
    trace = session.get("management_trace")
    if not isinstance(trace, list):
        trace = []

    items = []
    displayed_ordinal = 0
    for raw_index, event in enumerate(trace):
        if not isinstance(event, dict):
            continue
        status = event.get("execution_status")
        if status not in ("executed", "terminal_locked"):
            continue
        displayed_ordinal += 1
        if status != "executed":
            continue
        details = {key: deepcopy(event[key]) for key in _DECISION_FIELDS if key in event}
        for state_key in ("state_before", "state_after"):
            state = event.get(state_key)
            if isinstance(state, dict):
                details[state_key] = {
                    key: deepcopy(state[key]) for key in _STATE_FIELDS if key in state
                }
        items.append({
            "ref": f"trace:{raw_index}",
            "label": f"Decision {displayed_ordinal}",
            "kind": "decision",
            "details": details,
        })

    # Preserve the resident's pre-comparison reflection where that snapshot is
    # present. Responses written after viewing the expert comparison are not
    # substituted for the original reflection.
    reviews = session.get("precomparison_decision_review")
    if not isinstance(reviews, dict) or not reviews:
        reviews = session.get("decision_review")
    if not isinstance(reviews, dict):
        reviews = {}
    for review_key, answers in reviews.items():
        if not isinstance(review_key, str) or not review_key or not isinstance(answers, dict):
            continue
        if not all(isinstance(answers.get(key), str) and answers[key].strip() for key in _REVIEW_FIELDS):
            continue
        items.append({
            "ref": f"reflection:{review_key}",
            "label": f"Reflection {review_key}",
            "kind": "reflection",
            "details": {key: answers[key] for key in _REVIEW_FIELDS},
        })
    return items
