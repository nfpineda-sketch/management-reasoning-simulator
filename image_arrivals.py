"""The second authorization's plan: the arrival photograph of every case that had none (2026-09-26).

Faculty, 2026-09-26: US$10 more over the remaining balance, spent without
paying for images that end rejected or unusable. So only case arrivals, the
first photograph every encounter shows, and never a state the pilot could not
draw (``image_broker.known_to_fail``). A marked sweat is not drawn for anyone:
on dark skin it failed 4 of 4 times, and drawing it only on lighter skin would
make the bank tie the finding to a skin tone. Those seven cases keep their
neutral view and the written examination.

Each item names a case and a person the case is compatible with; the state is
the case's own arrival as the engine derives it, drawn as the bank draws it.
Batches are made one at a time and reviewed before the next.
"""
from __future__ import annotations

PLAN_ID = "llegadas-2026-09-26"

PLAN = (
    # Batch 1: three people already drawn, one new, to check the method first.
    {"batch": 1, "identity": "V22", "case": "acs_61m_posterior"},
    {"batch": 1, "identity": "V11", "case": "acs_66f_nonst"},
    {"batch": 1, "identity": "V18", "case": "opioid_35m"},
    {"batch": 1, "identity": "V11", "case": "hypoglycemia_76f"},
    {"batch": 1, "identity": "V27", "case": "bradycardia_ccb_68m"},
    # Batch 2
    {"batch": 2, "identity": "V09", "case": "bradycardia_bb_54f"},
    {"batch": 2, "identity": "V05", "case": "pneumonia_46f"},
    {"batch": 2, "identity": "V21", "case": "trauma_hemothorax_41m"},
    {"batch": 2, "identity": "V29", "case": "pneumonia_83m"},
    {"batch": 2, "identity": "V11", "case": "pulmonary_edema_75f"},
    {"batch": 2, "identity": "V03", "case": "asthma_24f"},
    {"batch": 2, "identity": "V24", "case": "pulmonary_embolism_61m"},
    # Batch 3
    {"batch": 3, "identity": "V23", "case": "asthma_49m"},
    {"batch": 3, "identity": "V12", "case": "opioid_67f"},
    {"batch": 3, "identity": "V02", "case": "anaphylaxis_29f"},
    {"batch": 3, "identity": "V26", "case": "anaphylaxis_63m_betablocked"},
    {"batch": 3, "identity": "V17", "case": "renal_colic_34m"},
    {"batch": 3, "identity": "V14", "case": "bradycardia_avb3_78f"},
    # Batch 4: a second person for the commonest arrivals, only people whose reference
    # was already looked at, so each item is one edit (anti-memorization, section 7).
    {"batch": 4, "identity": "V23", "case": "acs_61m_posterior"},
    {"batch": 4, "identity": "V24", "case": "gi_bleed_57m"},
    {"batch": 4, "identity": "V12", "case": "acs_66f_nonst"},
    {"batch": 4, "identity": "V21", "case": "acs_48m_wellens"},
    {"batch": 4, "identity": "V26", "case": "bradycardia_hyperk_63m"},
    {"batch": 4, "identity": "V02", "case": "pulmonary_embolism_33f"},
    {"batch": 4, "identity": "V09", "case": "pneumonia_46f"},
    {"batch": 4, "identity": "V17", "case": "opioid_35m"},
    {"batch": 4, "identity": "V12", "case": "pulmonary_edema_75f"},
)


def items(batch=None):
    return [dict(item, state=item["case"]) for item in PLAN if batch is None or item["batch"] == batch]


def arrival(case_id):
    """The case's arrival appearance, as the room derives it."""
    import catalog_trajectories
    from clinical_cases import FAMILIES
    from patient_appearance import appearance_state
    family = next(name for name, spec in FAMILIES.items() if any(v["id"] == case_id for v in spec["variants"]))
    state = catalog_trajectories.launch(case_id, family, allow_review_candidates=True)
    return state, appearance_state(state)


def contract(item):
    from image_bank import drawn_contract
    return drawn_contract(arrival(item["case"])[1])


def patient(item):
    return arrival(item["case"])[0]["encounter_spec"]["clinical_case"]["patient"]
