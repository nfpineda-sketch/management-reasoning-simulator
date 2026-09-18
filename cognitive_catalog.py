"""Local formative objectives for varied emergency encounters.

Bias names describe an instructional opportunity, not an inferred characteristic
of a learner. The catalog does not diagnose cognitive bias, grade competence, or
change patient physiology. Keep this metadata server-side during an encounter.
"""

CATALOG_VERSION = "0.2.0"

FAMILY_LABELS = {
    "pneumonia": "Pneumonia with systemic illness",
    "pulmonary_edema": "Acute cardiogenic pulmonary edema",
    "acs": "Acute coronary syndrome",
    "pulmonary_embolism": "Pulmonary embolism",
    "asthma": "Acute severe asthma",
    "gi_bleed": "Upper gastrointestinal hemorrhage",
    "hypoglycemia": "Hypoglycemic altered mental status",
    "opioid": "Opioid-associated hypoventilation",
}

EVIDENCE_INTERPRETATION = (
    "Recorded decisions and reflections support formative discussion. "
    "A single action, omission, or patient outcome does not establish cognitive "
    "bias or competence. Review the information available at the time and ask "
    "the learner to explain their reasoning."
)

# Only the explicitly fictional shift context may be shown at entry. It is an
# exposure supplied by this simulation, never an assertion about the learner's
# real experience. Diagnostic labels and objectives remain internal.
BIAS_CONTEXTS = {
    "availability": {
        "prime_text": (
            "Earlier in this simulated shift, you assessed several patients "
            "with respiratory infection."
        ),
    },
}

BIAS_CHALLENGES = {
    "R1-05": {
        "title": "Revisit the first explanation",
        "bias_id": "anchoring",
        "bias_name": "Anchoring",
        "objective": (
            "Compare the initial explanation with subsequent observations and "
            "revise management when important findings remain unexplained."
        ),
        "year": 1,
        "evidence_fields": ("working_model", "management_priority", "reassessment", "reflection"),
        "families": ("pneumonia", "pulmonary_edema"),
        "debrief_questions": (
            "What initially made your explanation plausible?",
            "Which subsequent findings supported or challenged it?",
            "How did that comparison change your next management decision?",
        ),
    },
    "R1-06": {
        "title": "Check whether the problem is fully addressed",
        "bias_id": "premature_closure",
        "bias_name": "Premature closure",
        "objective": (
            "After an initial explanation or treatment response, reassess "
            "whether remaining abnormalities and recurrence risk require "
            "further management."
        ),
        "year": 1,
        "evidence_fields": ("expected_effect", "reassessment", "reflection"),
        "families": ("hypoglycemia", "opioid"),
        "debrief_questions": (
            "What did the initial response explain, and what remained uncertain?",
            "What did you reassess before considering the immediate problem addressed?",
            "What findings would prompt further treatment or observation?",
        ),
    },
    "R2-02": {
        "title": "Seek evidence that challenges the working explanation",
        "bias_id": "confirmation",
        "bias_name": "Confirmation bias",
        "objective": (
            "Seek and interpret discriminating findings, including findings "
            "that could weaken the current hypothesis, and use them to "
            "adjust management."
        ),
        "year": 2,
        "evidence_fields": ("working_model", "expected_effect", "reassessment", "reflection"),
        "families": ("acs", "pulmonary_embolism"),
        "debrief_questions": (
            "Which finding could have changed your leading explanation?",
            "How did you interpret the evidence that fitted it least well?",
            "What did those findings change about your management?",
        ),
    },
    "R2-03": {
        "title": "Distinguish the current patient from recent cases",
        "bias_id": "availability",
        "bias_name": "Availability bias",
        "objective": (
            "Compare this patient's discriminating findings with a supplied "
            "recent-case context and justify management using the current "
            "encounter's evidence."
        ),
        "year": 2,
        "evidence_fields": ("working_model", "management_priority", "reflection"),
        "families": ("pulmonary_embolism", "pneumonia"),
        "debrief_questions": (
            "Did the simulated shift context influence your first impression?",
            "What distinguished this patient from those earlier cases?",
            "Which current findings carried the most weight in your management?",
        ),
    },
    "R1-07": {
        "title": "Assess the patient beyond the handover",
        "bias_id": "framing",
        "bias_name": "Framing effect",
        "objective": (
            "Distinguish a handover impression from observed facts, assess "
            "the patient independently, and explain the resulting priorities."
        ),
        "year": 1,
        "evidence_fields": ("working_model", "management_priority", "reassessment", "reflection"),
        "families": ("acs", "hypoglycemia"),
        "debrief_questions": (
            "Which handover statements were observations and which were interpretations?",
            "What did your own assessment add or change?",
            "How did that affect your immediate priorities?",
        ),
    },
    "R2-04": {
        "title": "Recognize illness outside the usual pattern",
        "bias_id": "representativeness",
        "bias_name": "Representativeness bias",
        "objective": (
            "Evaluate consequential explanations even when the presentation "
            "does not match a familiar prototype, using discriminating "
            "clinical findings to guide management."
        ),
        "year": 2,
        "evidence_fields": ("working_model", "management_priority", "reflection"),
        "families": ("acs", "pulmonary_embolism"),
        "debrief_questions": (
            "Which features differed from the presentation you expected?",
            "What evidence kept a consequential alternative under consideration?",
            "How did you manage that uncertainty while evaluating the patient?",
        ),
    },
    "R2-05": {
        "title": "Explain what remains after the first finding",
        "bias_id": "search_satisficing",
        "bias_name": "Search satisficing",
        "objective": (
            "After finding an abnormality, check whether it explains the "
            "whole clinical state and pursue unresolved management needs."
        ),
        "year": 2,
        "evidence_fields": ("working_model", "management_priority", "reassessment", "reflection"),
        "families": ("gi_bleed", "pneumonia"),
        "debrief_questions": (
            "What did the first positive finding explain?",
            "Which abnormalities or immediate needs remained unresolved?",
            "How did you decide whether to continue evaluation or change treatment?",
        ),
    },
    "R3-01": {
        "title": "Choose the next action from the observed response",
        "bias_id": "action_bias",
        "bias_name": "Action bias",
        "objective": (
            "Compare the expected benefit and harm of another intervention "
            "with reassessment or monitored observation, while continuing "
            "time-critical treatment when indicated."
        ),
        "year": 3,
        "evidence_fields": ("management_priority", "expected_effect", "reassessment", "reflection"),
        "families": ("pulmonary_edema", "asthma"),
        "debrief_questions": (
            "What additional benefit did you expect from the next intervention?",
            "What response or potential harm would make you modify that plan?",
            "When was another intervention needed, and when was reassessment appropriate?",
        ),
    },
}


# Curriculum/report consumers receive the same versioned source links used by
# the faculty assessment catalog. These remain internal during an encounter.
from competency_mapping import mapping_for_challenge

for _challenge_id, _challenge in BIAS_CHALLENGES.items():
    _mapping = mapping_for_challenge(_challenge_id)
    _challenge.update(_mapping)
    _challenge["acgme"] = "; ".join(
        link["code"] for link in _mapping["competency_mapping"]
        if link["framework"] == "ACGME"
    )
    _challenge["royal_college"] = "; ".join(
        dict.fromkeys(link["epa_id"] + " / " + link["code"]
                      for link in _mapping["competency_mapping"]
                      if link["framework"] == "Royal College")
    )
del _challenge_id, _challenge, _mapping
