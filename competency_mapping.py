"""Source-traceable local links from simulation challenges to competencies.

Links identify educational alignment, not an accredited assessment or evidence
that an entire EPA or Milestone level has been achieved. All display summaries
are local paraphrases. Faculty assess the observed behaviour and its context.
"""
MAPPING_VERSION = "1.0.0"
SOURCES = {
    "acgme_em_2021": {
        "organization": "ACGME",
        "document": "Emergency Medicine Milestones",
        "version": "Worksheet 2.1; second revision February 2021; effective July 1, 2021",
        "url": "https://www.acgme.org/globalassets/pdfs/milestones/emergencymedicinemilestones.pdf",
        "verified_on": "2026-09-13",
        "page_convention": "1-based PDF page, including cover and introduction",
    },
    "rc_em_epa_2018": {
        "organization": "Royal College of Physicians and Surgeons of Canada",
        "document": "Emergency Medicine EPA Guide",
        "version": "2018 version 1.1; editorial revision November 1, 2018",
        "url": "https://www.royalcollege.ca/content/dam/documents/ibd/emergency-medicine/epa-guide-emergency-med-e.pdf",
        "verified_on": "2026-09-13",
        "page_convention": "1-based PDF page (59-page edition)",
    },
}

# Exact source identifiers; titles below are intentionally short local labels.
_ACGME = {
    "PC1": (7, "Urgent stabilization", "1"),
    "PC2": (8, "Focused clinical assessment", "2"),
    "PC3": (9, "Test selection and interpretation", "3"),
    "PC4": (10, "Diagnostic revision", "4"),
    "PC5": (11, "Medication selection and response", "5"),
    "PC6": (12, "Re-evaluation and continuing care", "6"),
    "MK2": (16, "Treatment reasoning and error awareness", "10"),
}
_RC = {
    "C5.ME1.6": ("C5", "ME 1.6", 25, (1,), "Reasoning with incomplete information"),
    "C5.ME2.2.assessment": ("C5", "ME 2.2", 25, (2, 3), "Selective clinical assessment"),
    "C5.ME2.2.differential": ("C5", "ME 2.2", 25, (4,), "Considering alternative explanations"),
    "C5.ME2.2.tests": ("C5", "ME 2.2", 25, (5,), "Using investigations in management"),
    "C5.ME2.4": ("C5", "ME 2.4", 25, (6,), "Management across concurrent problems"),
    "C5.COM2.3": ("C5", "COM 2.3", 25, (8,), "Verifying information with additional sources"),
    "TP6.ME2.1": ("TP6", "ME 2.1", 57, (2,), "Priorities under uncertainty"),
    "TP6.ME3.3": ("TP6", "ME 3.3", 57, (3,), "Timely intervention when deterioration threatens"),
    "TP6.ME4.1": ("TP6", "ME 4.1", 57, (4,), "Follow-up and reassessment under uncertainty"),
}

# These are the design's observable actions, NOT quotations of official rubrics.
CHALLENGE_MAPPINGS = {
    "R1-05": {
        "acgme_codes": ("PC4", "MK2", "PC6"),
        "rc_links": ("C5.ME1.6", "C5.ME2.4", "TP6.ME4.1"),
        "observable_behaviors": (
            "Names the initial working explanation and the findings supporting it.",
            "Identifies new observations the explanation does not cover.",
            "Explains whether the discrepancy warrants changing priorities or treatment.",
        ),
        "opportunity": "A subsequent observation can challenge the first working explanation.",
    },
    "R1-06": {
        "acgme_codes": ("PC6", "PC4", "MK2"),
        "rc_links": ("C5.ME2.4", "TP6.ME4.1"),
        "observable_behaviors": (
            "Distinguishes an immediate response from resolution of the patient's needs.",
            "Checks remaining abnormalities and states what could recur.",
            "Makes an explicit plan for further observation, treatment, or escalation.",
        ),
        "opportunity": "Initial improvement or an early explanation leaves a reason to reassess.",
    },
    "R2-02": {
        "acgme_codes": ("PC3", "PC4", "MK2"),
        "rc_links": ("C5.ME1.6", "C5.ME2.2.differential", "C5.ME2.2.tests"),
        "observable_behaviors": (
            "States a finding that could weaken the current explanation.",
            "Seeks or interprets information that distinguishes competing explanations.",
            "Relates conflicting evidence to the next management decision.",
        ),
        "opportunity": "Competing explanations can be distinguished with available encounter information.",
    },
    "R2-03": {
        "acgme_codes": ("PC4", "MK2"),
        "rc_links": ("C5.ME1.6", "C5.ME2.2.differential"),
        "observable_behaviors": (
            "Explains how this patient's observations bear on the working model.",
            "Compares the current presentation with the simulated recent-case context.",
            "Justifies priorities using patient-specific evidence.",
        ),
        "opportunity": "The encounter supplies an explicit recent-case context to compare with this patient.",
    },
    "R1-07": {
        "acgme_codes": ("PC2", "PC4", "MK2"),
        "rc_links": ("C5.ME2.2.assessment", "C5.COM2.3"),
        "observable_behaviors": (
            "Separates the handover interpretation from the underlying observations.",
            "Obtains a focused independent assessment or relevant corroboration.",
            "Explains how the assessment changes or supports initial priorities.",
        ),
        "opportunity": "A supplied handover impression can be checked against the patient's findings.",
    },
    "R2-04": {
        "acgme_codes": ("PC1", "PC4", "MK2"),
        "rc_links": ("C5.ME1.6", "C5.ME2.2.differential"),
        "observable_behaviors": (
            "Explains which observations differ from the expected presentation.",
            "Keeps consequential alternatives in consideration using clinical evidence.",
            "Protects immediate patient needs while working through uncertainty.",
        ),
        "opportunity": "The presentation differs from a familiar prototype while retaining actionable findings.",
    },
    "R2-05": {
        "acgme_codes": ("PC4", "PC6", "MK2"),
        "rc_links": ("C5.ME2.4", "TP6.ME4.1"),
        "observable_behaviors": (
            "States what the first positive finding explains and what it leaves unresolved.",
            "Connects persisting abnormalities to additional management needs.",
            "Reassesses the whole patient after addressing the initial finding.",
        ),
        "opportunity": "A positive finding does not by itself resolve every active management problem.",
    },
    "R3-01": {
        "acgme_codes": ("PC5", "PC6", "MK2"),
        "rc_links": ("TP6.ME2.1", "TP6.ME3.3", "TP6.ME4.1"),
        "observable_behaviors": (
            "States the expected incremental benefit and possible harm of another action.",
            "Compares that action with monitored reassessment using the actual response.",
            "Specifies when observation should end and escalation should occur.",
        ),
        "opportunity": "An evolving response supports a choice between additional intervention and reassessment.",
    },
}

ASSESSMENT_LIMITATION = (
    "Faculty-reviewed evidence of a simulated reasoning component only. Does not "
    "establish a cognitive bias, an ACGME level, whole-EPA entrustment, team or "
    "procedural performance. Source-framework stage is not the learner's PGY."
)
LOCAL_TARGET_SOURCE = (
    "Configurable local review milestone: initial default 3 faculty-reviewed "
    "satisfactory observations. Not an ACGME or Royal College requirement, "
    "validated competence threshold, or limit on further observations."
)


def mapping_for_challenge(challenge_id):
    """Return independent, serializable links usable in reports and assessment."""
    definition = CHALLENGE_MAPPINGS.get(challenge_id)
    if definition is None:
        return {}
    links = []
    for code in definition["acgme_codes"]:
        page, label, printed = _ACGME[code]
        links.append({
            "framework": "ACGME", "code": code, "label": label,
            "source_id": "acgme_em_2021", "pdf_page": page,
            "source_locator": f"{code}; printed worksheet page {printed}",
            "source_url": SOURCES["acgme_em_2021"]["url"] + f"#page={page}",
            "source_version": SOURCES["acgme_em_2021"]["version"],
            "scope": "Selected reasoning evidence; no level assigned",
            "evidence_condition": {
                "PC1": "A decision recognizes or addresses instability or deterioration risk.",
                "PC2": "A recorded focused history or examination informs a management decision.",
                "PC3": "The learner explains why a study was selected or what its result changes.",
                "PC4": "The learner documents competing explanations or revises the working model.",
                "PC5": "A medication decision includes rationale, intended effect, or adverse-effect review.",
                "PC6": "A recorded reassessment informs continuing management or disposition.",
                "MK2": "The learner explains or reflects on reasoning in relation to recorded patient information.",
            }[code],
        })
    for link in definition["rc_links"]:
        epa, code, page, items, label = _RC[link]
        links.append({
            "framework": "Royal College", "code": code, "epa_id": epa,
            "label": label, "source_id": "rc_em_epa_2018", "pdf_page": page,
            "milestone_items": list(items),
            "source_locator": f"{epa}; relevant milestones " + ", ".join(map(str, items)),
            "source_url": SOURCES["rc_em_epa_2018"]["url"] + f"#page={page}",
            "source_version": SOURCES["rc_em_epa_2018"]["version"],
            "scope": "Selected reasoning component within the cited EPA",
            "evidence_condition": (
                "Faculty must identify an actual encounter opportunity and cite the relevant "
                "reasoning behavior; this link does not confer the complete EPA."
            ),
        })
    return {
        "mapping_version": MAPPING_VERSION,
        "challenge_id": challenge_id,
        "competency_mapping": links,
        "observable_behaviors": list(definition["observable_behaviors"]),
        "evidence_requirements": [
            definition["opportunity"],
            "Cite a recorded decision and explain its connection to the selected behavior.",
            "Distinguish contemporaneous reasoning from later reflection; missing documentation is not proof of absent reasoning.",
            "Mark insufficient evidence when the opportunity or behavior was not observed; case completion and outcome alone confer no credit.",
        ],
        "assessment_limitation": ASSESSMENT_LIMITATION,
    }


def objective_definitions(challenges):
    """Build local objective IDs, preserving the challenge IDs for traceability."""
    return {
        key: {
            "title": value["title"], "scope": value["objective"],
            "target": 3, "supported": True,
            "limitation": ASSESSMENT_LIMITATION,
            "target_source": LOCAL_TARGET_SOURCE,
            "assessment_scope": "simulated_reasoning_component",
            **mapping_for_challenge(key),
        }
        for key, value in challenges.items() if key in CHALLENGE_MAPPINGS
    }


def _mapping(value):
    return value if isinstance(value, dict) else {}


def record_challenge_id(record):
    """Resolve only structured source metadata, never free text or AI inference.

    Conflicting source metadata fails closed. Accept both a persisted record and
    an encounter payload for the staff analysis boundary.
    """
    record = _mapping(record)
    payload = _mapping(record.get("payload")) or record
    session = _mapping(payload.get("session"))
    encounter = _mapping(record.get("encounter"))
    candidates = [record.get("challenge_id"), encounter.get("challenge_id"),
                  _mapping(session.get("encounter_assignment")).get("challenge_id")]
    for owner in (encounter, session, _mapping(session.get("state")),
                  _mapping(session.get("encounter_closed_state"))):
        for key in ("spec", "case_spec", "encounter_spec"):
            candidates.append(_mapping(owner.get(key)).get("challenge_id"))
    values = {value for value in candidates if isinstance(value, str) and value}
    return values.pop() if len(values) == 1 else None


def objective_is_eligible(objective_id, record):
    """Scope gate, never a quality/pass decision. Original scopes are preserved."""
    if objective_id in CHALLENGE_MAPPINGS:
        return record_challenge_id(record) == objective_id
    # Defer supported/original scope checks to OBJECTIVES, avoiding an import
    # cycle and preventing arbitrary IDs from being treated as eligible.
    return objective_id in {"TD1", "F1", "C1", "C3", "C4", "C14"}


def objective_evidence_is_eligible(objective_id, selected_evidence):
    """New reasoning observations must cite a real decision, not reflection alone.

    This does not require a favorable response, a particular action or filled
    reasoning fields, so unsatisfactory observations can also be retained.
    """
    if objective_id not in CHALLENGE_MAPPINGS:
        return True
    return isinstance(selected_evidence, (list, tuple)) and any(
        isinstance(item, dict) and item.get("kind") == "decision"
        for item in selected_evidence
    )
