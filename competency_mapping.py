"""Source-traceable local links from simulation challenges to competencies.

Links identify educational alignment, not an accredited assessment or evidence
that an entire EPA or Milestone level has been achieved. All display summaries
are local paraphrases. Faculty assess the observed behaviour and its context.
"""
# 1.1.0 (2026-09-27): R1-03, R1-04 and R2-01 join the observational pipeline
# with the scope of each contribution stated (DF-2, faculty decision for cycle
# 3). The links of the eight Decision Challenges are unchanged.
MAPPING_VERSION = "1.1.0"
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
        # The same guide circulates in more than one edition and the page
        # numbers move between them. Re-checked on 2026-09-23 against the
        # 51-page 2018 VERSION 1.0: every EPA, milestone number, CanMEDS code
        # and milestone text below matched exactly, and only the pagination
        # differed. Page 57 does not exist in that edition, so a reader holding
        # it needs its own numbers rather than a reference that cannot resolve.
        "other_editions": {
            "2018 VERSION 1.0 (51-page edition)": {
                "verified_on": "2026-09-23",
                "pages": {"C5": 22, "TP6": 49},
                "matched": "EPA titles, milestone numbers, CanMEDS codes and milestone text",
                "differs": "pagination only",
            },
        },
    },
    # The document that describes each stage milestone by CanMEDS competency,
    # used where it is the one describing the behaviour observed (faculty
    # decision, 2026-09-27). Verified against the copy the faculty supplied;
    # its public address was not verified, so none is given. Milestones are
    # paraphrased: the licence does not allow sharing the material.
    "rc_em_pathway_2018": {
        "organization": "Royal College of Physicians and Surgeons of Canada",
        "document": "Pathway to Competence: Emergency Medicine",
        "version": "2018 version 1.0; effective for residents entering on or after July 1, 2018",
        "url": None,
        "verified_on": "2026-09-27",
        "page_convention": "1-based PDF page (61-page edition)",
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
    "MK1": (15, "Scientific knowledge", "9"),
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

# R1-03, R1-04 and R2-01: the three foundation challenges, each link with the
# scope of what one observation contributes (faculty decision on DF-2,
# 2026-09-27; verification in docs/VERIFICACION_MAPPINGS_FUNDACIONALES.md).
#
# * "direct": the observation represents the element it is linked to.
# * "partial": it gives valid evidence on an identifiable part of the element
#   and says what stays outside. Partial is not a defect, and neither kind is a
#   score, a weight or a level: nothing here counts one as half of the other.
#
# The ACGME element is quoted; "level" is where the behaviour is described, not
# a level assigned to anyone. The Royal College milestone comes from Pathway to
# Competence, paraphrased; "epa_context" names the EPA the EPA Guide lists it
# under, as context and never as a contribution to that whole EPA. A relation
# the verification found but whose contribution could not be stated clearly is
# documented there and is not activated here.
_FOUNDATION_CONTRIBUTIONS = {
    "R1-03": {
        "observable_behaviors": (
            "Explains the proposed contribution of the tachycardia with the patient's findings.",
            "Links the management priority to that explanation.",
            "Compares the observed response, in rhythm and perfusion, with the explanation.",
        ),
        "opportunity": "A tachycardia whose contribution to the patient's condition can be explained and "
                       "tested against the response to treatment.",
        "contributions": (
            {"framework": "ACGME", "code": "PC4", "level": 3, "contribution": "direct",
             "element": "Demonstrates the ability to modify a diagnosis based on a patient's clinical course "
                        "and additional data.",
             "component_observed": "Holding the explanation of the tachycardia against the patient's course and "
                                   "the observed response, and revising it when they disagree.",
             "limitation": None,
             "evidence_condition": "The learner compares the observed response with the stated explanation "
                                   "and keeps or revises it."},
            {"framework": "ACGME", "code": "MK2", "level": 4, "contribution": "partial",
             "element": "Continually re-appraises one's clinical reasoning to prospectively minimize cognitive "
                        "errors and manage uncertainty.",
             "component_observed": "Re-appraising the explanation of the tachycardia against the response, "
                                   "within one encounter.",
             "limitation": "One encounter's re-appraisal. The continual habit, and the explicit management of "
                           "cognitive error, are outside what this challenge observes.",
             "evidence_condition": "The learner revisits the explanation after the response is known."},
            {"framework": "Royal College", "code": "ME 2.2", "stage": "Foundations of Discipline",
             "pdf_page": 11, "contribution": "partial",
             "element": "Develop a working and a differential diagnosis while managing the patient's symptoms "
                        "at the same time (paraphrase).",
             "component_observed": "A working, causal explanation of the tachycardia formed and used while the "
                                   "initial treatment proceeds.",
             "limitation": "A differential diagnosis is not required by this challenge, and symptom management "
                           "is observed only through the simulated orders.",
             "evidence_condition": "A recorded decision states the explanation and acts on it.",
             "epa_context": {"epa_id": "F1", "milestone_item": 3, "source_id": "rc_em_epa_2018", "pdf_page": 10}},
        ),
    },
    "R1-04": {
        "observable_behaviors": (
            "States a testable expectation of an intervention.",
            "Chooses the variables and the time of the reassessment.",
            "Compares what is observed with what was expected, and uses it for the next decision.",
        ),
        "opportunity": "An intervention whose effect can be anticipated and checked at the bedside within the "
                       "encounter.",
        "contributions": (
            {"framework": "ACGME", "code": "PC1", "level": 3, "contribution": "direct",
             "element": "Reassesses the patient's status after implementing a stabilizing intervention.",
             "component_observed": "Reassessing the patient, on chosen variables and at a chosen time, after a "
                                   "stabilizing intervention.",
             "limitation": None,
             "evidence_condition": "A recorded reassessment follows the intervention it checks."},
            {"framework": "ACGME", "code": "PC6", "level": 3, "contribution": "partial",
             "element": "Identifies which patients will require ongoing emergency department evaluation and "
                        "evaluates the effectiveness of diagnostic and therapeutic interventions.",
             "component_observed": "Evaluating the effectiveness of a therapeutic intervention against the "
                                   "expectation stated before it.",
             "limitation": "Deciding which patients need ongoing emergency department evaluation, and the "
                           "effectiveness of diagnostic interventions, are not required by this challenge.",
             "evidence_condition": "The learner compares the observed response with the stated expectation."},
            {"framework": "Royal College", "code": "ME 4.1", "stage": "Foundations of Discipline",
             "pdf_page": 22, "contribution": "partial",
             "element": "Reassess the patient and follow up on the results of ongoing investigations and the "
                        "response to treatment (paraphrase; pp. 22-23).",
             "component_observed": "Reassessing the patient and the response to treatment against a stated "
                                   "expectation.",
             "limitation": "Following up the results of ongoing investigations is not required by this "
                           "challenge. The EPA Guide lists this milestone under F2, an EPA for uncomplicated "
                           "presentations; these encounters are not, so no EPA is attributed.",
             "evidence_condition": "A recorded reassessment is compared with the expectation stated before it.",
             "epa_context": None},
        ),
    },
    "R2-01": {
        "observable_behaviors": (
            "Integrates several circulatory observations rather than the pressure alone.",
            "Proposes a mechanism and an action directed at it.",
            "Revisits the mechanism and the priority after the response to treatment.",
        ),
        "opportunity": "Circulatory compromise that the pressure alone does not explain, observable in several "
                       "variables before and after treatment.",
        "contributions": (
            {"framework": "ACGME", "code": "PC1", "level": 3, "contribution": "direct",
             "element": "Identifies a patient with occult presentation that is at risk for instability or "
                        "deterioration.",
             "component_observed": "Recognizing circulatory compromise that the blood pressure alone does not "
                                   "show, from several bedside observations.",
             "limitation": None,
             "evidence_condition": "A recorded decision names the compromise and the observations behind it."},
            {"framework": "ACGME", "code": "PC4", "level": 3, "contribution": "direct",
             "element": "Demonstrates the ability to modify a diagnosis based on a patient's clinical course "
                        "and additional data.",
             "component_observed": "Revising the proposed circulatory mechanism after the response to treatment.",
             "limitation": None,
             "evidence_condition": "The learner keeps or revises the mechanism once the response is known."},
            {"framework": "ACGME", "code": "MK1", "level": 2, "contribution": "partial",
             "element": "Demonstrates scientific knowledge of complex presentations and conditions.",
             "component_observed": "Applying physiological knowledge of pressure, flow and perfusion to explain "
                                   "the patient's compromise.",
             "limitation": "MK1 describes scientific knowledge itself. The simulator observes only its "
                           "application in the mechanism the resident states, not the breadth or depth of "
                           "that knowledge.",
             "evidence_condition": "The stated mechanism uses the physiology of pressure, flow and perfusion."},
            {"framework": "ACGME", "code": "MK2", "level": 4, "contribution": "partial",
             "element": "Continually re-appraises one's clinical reasoning to prospectively minimize cognitive "
                        "errors and manage uncertainty.",
             "component_observed": "Re-appraising the proposed mechanism and priority against the response, "
                                   "within one encounter.",
             "limitation": "One encounter's re-appraisal. The continual habit, and the explicit management of "
                           "cognitive error, are outside what this challenge observes.",
             "evidence_condition": "The learner revisits the mechanism after the response is known."},
            {"framework": "Royal College", "code": "ME 1.6", "stage": "Core of Discipline",
             "pdf_page": 9, "contribution": "direct",
             "element": "Use sound clinical reasoning and judgement to guide diagnosis and management and reach "
                        "appropriate decisions, even when complete clinical or diagnostic information is not "
                        "immediately available (paraphrase).",
             "component_observed": "Reasoning from several bedside observations to a circulatory mechanism and "
                                   "a targeted action before complete information is available.",
             "limitation": None,
             "evidence_condition": "A recorded decision acts on a stated mechanism before the picture is "
                                   "complete.",
             "epa_context": {"epa_id": "C1", "milestone_item": 1, "source_id": "rc_em_epa_2018", "pdf_page": 18}},
            {"framework": "Royal College", "code": "ME 1.6", "stage": "Core of Discipline",
             "pdf_page": 9, "contribution": "direct",
             "element": "Adapt care as the complexity, uncertainty and ambiguity of the patient's clinical "
                        "situation evolve (paraphrase).",
             "component_observed": "Revising the mechanism and the management priority as the response to "
                                   "treatment unfolds.",
             "limitation": None,
             "evidence_condition": "A later decision changes, or deliberately keeps, the priority in light of "
                                   "the response.",
             "epa_context": None},
        ),
    },
}
CHALLENGE_MAPPINGS.update(_FOUNDATION_CONTRIBUTIONS)

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


CONTRIBUTION_TYPES = ("direct", "partial")
# How a document or a screen names each kind. Labels, never scores.
CONTRIBUTION_LABELS = {"direct": "Direct contribution:", "partial": "Partial contribution:"}


def _contribution_link(item):
    """One link that says what an observation contributes and what stays outside it."""
    scope = {key: item[key] for key in ("contribution", "element", "component_observed", "limitation",
                                        "evidence_condition")}
    if item["framework"] == "ACGME":
        page, label, printed = _ACGME[item["code"]]
        source = SOURCES["acgme_em_2021"]
        return {
            "framework": "ACGME", "code": item["code"], "label": label,
            "source_id": "acgme_em_2021", "pdf_page": page,
            "source_locator": f"{item['code']} level {item['level']}; printed worksheet page {printed}",
            "source_url": source["url"] + f"#page={page}", "source_version": source["version"],
            "level_described": item["level"],
            "scope": "One element of the milestone, where its level describes it; no level is assigned",
            **scope,
        }
    source = SOURCES["rc_em_pathway_2018"]
    context = item.get("epa_context")
    return {
        "framework": "Royal College", "code": item["code"], "label": item["stage"] + " milestone",
        "stage": item["stage"], "source_id": "rc_em_pathway_2018", "pdf_page": item["pdf_page"],
        "source_locator": f"{item['code']}, {item['stage']}; Pathway to Competence p. {item['pdf_page']}",
        "source_url": (source["url"] + f"#page={item['pdf_page']}") if source["url"] else None,
        "source_version": source["version"],
        "scope": "One stage milestone of the enabling competency; not the complete EPA",
        "epa_context": ({**context, "source_version": SOURCES[context["source_id"]]["version"],
                         "note": "The EPA this milestone is listed under; context, not a contribution to "
                                 "the whole EPA."} if context else None),
        **scope,
    }


def mapping_for_challenge(challenge_id):
    """Return independent, serializable links usable in reports and assessment."""
    definition = CHALLENGE_MAPPINGS.get(challenge_id)
    if definition is None:
        return {}
    if "contributions" in definition:
        return {
            "mapping_version": MAPPING_VERSION,
            "challenge_id": challenge_id,
            "competency_mapping": [_contribution_link(item) for item in definition["contributions"]],
            "observable_behaviors": list(definition["observable_behaviors"]),
            "evidence_requirements": [
                definition["opportunity"],
                "Cite a recorded decision and explain its connection to the selected behavior.",
                "Distinguish contemporaneous reasoning from later reflection; missing documentation is not proof of absent reasoning.",
                "Mark insufficient evidence when the opportunity or behavior was not observed; case completion and outcome alone confer no credit.",
                "Each link states whether the observation is a direct or a partial contribution, the component "
                "observed and what stays outside it; none is a milestone level or the complete EPA.",
            ],
            "assessment_limitation": ASSESSMENT_LIMITATION,
        }
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
    """Scope gate, never a quality/pass decision: did this encounter offer the objective?

    Decided by ``observation_opportunities`` from the declaration frozen with
    the encounter (DF-1, 2026-09-27). Until a case is reviewed, the rule that
    applied before is kept and labelled: TD1, F1, C1, C3, C4 and C14 in every
    encounter, a Decision Challenge in the encounter generated for it.
    """
    from observation_opportunities import resolve
    return resolve(objective_id, record)["eligible"]


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
