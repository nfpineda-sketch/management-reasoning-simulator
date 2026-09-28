"""The C14 review: eight faculty decisions (A-H) and the rows they derive.

Cycle 4 of the AI Advisor (faculty, 2026-09-28, DF-13). C14 is NOT activated.
The cycle 3 draft classified the 31 bank cases as 6 YES, 6 NO and 19 UNCERTAIN
(docs/BORRADOR_C14_OBSERVATION_OPPORTUNITIES.md); the uncertain ones were
grouped into eight clinical decisions so that the faculty answers eight
questions instead of reviewing 31 rows from scratch
(docs/C14_DECISIONES_A_H.md).

This module holds that draft and derives, from the faculty's answers, the state
each case's C14 row would take. It writes nothing: no case has an
``objectives`` block until the faculty approves the rows, and the transition
rule keeps C14 observable meanwhile (observation_opportunities, DF-12).

    derive({})                      # the draft, unchanged
    derive({"A": "approve", ...})   # the rows those answers imply

An answer is "approve" or "reject". A "modify" answer is the faculty's own
wording: the decision below is edited to say it, then derived.

What a decision yields for a case: "yes", "no", "uncertain", or None when that
decision alone does not settle the case (F approved leaves the pneumonias to C).
A case listed by several decisions is YES if any answered decision makes it
YES; it keeps its draft state for every decision not yet answered, so an
unanswered question never turns into a NO. Opportunity is never observed
behaviour (§68): nothing here reads an encounter.
"""
from __future__ import annotations

STATES = ("yes", "no", "uncertain")

# The cycle 3 draft, row by row (docs/BORRADOR_C14_OBSERVATION_OPPORTUNITIES.md).
DRAFT = {
    "acs_54m_inferior": "uncertain",
    "acs_66f_nonst": "uncertain",
    "acs_61m_posterior": "uncertain",
    "acs_52m_de_winter": "uncertain",
    "acs_48m_wellens": "uncertain",
    "acs_70f_left_main": "yes",
    "anaphylaxis_29f": "uncertain",
    "anaphylaxis_63m_betablocked": "uncertain",
    "asthma_24f": "uncertain",
    "asthma_49m": "uncertain",
    "bradycardia_ccb_68m": "uncertain",
    "bradycardia_avb3_78f": "uncertain",
    "bradycardia_bb_54f": "uncertain",
    "bradycardia_hyperk_63m": "no",
    "gi_bleed_57m": "uncertain",
    "gi_bleed_72f": "uncertain",
    "hypoglycemia_28m": "no",
    "hypoglycemia_76f": "no",
    "hypoglycemia_54m_thiamine": "no",
    "opioid_35m": "no",
    "opioid_67f": "no",
    "pneumonia_46f": "uncertain",
    "pneumonia_83m": "uncertain",
    "pulmonary_edema_58m": "yes",
    "pulmonary_edema_75f": "yes",
    "pulmonary_embolism_33f": "uncertain",
    "pulmonary_embolism_61m": "yes",
    "renal_colic_34m": "uncertain",
    "obstructive_pyelonephritis_58f": "uncertain",
    "trauma_limb_hemorrhage_27m": "yes",
    "trauma_hemothorax_41m": "yes",
}

# What each answer yields for the cases a decision covers.
DECISIONS = {
    "A": {"question": "Regional wall motion and the right ventricle in an acute coronary syndrome",
          "approve": {"acs_61m_posterior": "yes", "acs_52m_de_winter": "yes", "acs_66f_nonst": "no",
                      # Its authored POCUS contradicts the right ventricular
                      # involvement the case declares: a data decision first.
                      "acs_54m_inferior": "uncertain"},
          "reject": {"acs_61m_posterior": "no", "acs_52m_de_winter": "no", "acs_66f_nonst": "no",
                     "acs_54m_inferior": "no"}},
    "B": {"question": "A normal resting POCUS that must not reassure (Wellens)",
          "approve": {"acs_48m_wellens": "no"},
          "reject": {"acs_48m_wellens": "yes"}},
    "C": {"question": "Volume assessment to guide fluids",
          "approve": {"pneumonia_46f": "yes", "pneumonia_83m": "yes", "gi_bleed_57m": "yes",
                      "gi_bleed_72f": "yes", "obstructive_pyelonephritis_58f": "yes",
                      "anaphylaxis_29f": "no", "anaphylaxis_63m_betablocked": "no"},
          "reject": {"pneumonia_46f": "no", "pneumonia_83m": "no", "gi_bleed_57m": "no",
                     "gi_bleed_72f": "no", "obstructive_pyelonephritis_58f": "no",
                     "anaphylaxis_29f": "no", "anaphylaxis_63m_betablocked": "no"}},
    "D": {"question": "Asthma: a pneumothorax only if the course brings it",
          "approve": {"asthma_24f": "no", "asthma_49m": "no"},
          "reject": {"asthma_24f": "yes", "asthma_49m": "yes"}},
    "E": {"question": "Bradycardia: contractility to choose the support, and pacing capture",
          "approve": {"bradycardia_ccb_68m": "no", "bradycardia_bb_54f": "no", "bradycardia_avb3_78f": "no"},
          # The complete block stays NO until its POCUS reflects the capture.
          "reject": {"bradycardia_ccb_68m": "yes", "bradycardia_bb_54f": "yes", "bradycardia_avb3_78f": "no"}},
    "F": {"question": "Consolidation seen on POCUS",
          "approve": {"pneumonia_46f": None, "pneumonia_83m": None},
          "reject": {"pneumonia_46f": "yes", "pneumonia_83m": "yes"}},
    "G": {"question": "Pulmonary embolism: right ventricular strain and proximal DVT by compression",
          "approve": {"pulmonary_embolism_33f": "yes", "pulmonary_embolism_61m": "yes"},
          "reject": {"pulmonary_embolism_33f": "no", "pulmonary_embolism_61m": "no"}},
    "H": {"question": "The renal ultrasound of the renal cases",
          "approve": {"renal_colic_34m": "no", "obstructive_pyelonephritis_58f": None},
          "reject": {"renal_colic_34m": "yes", "obstructive_pyelonephritis_58f": "yes"}},
}

# The AI Advisor's recommendation for each decision (docs/C14_DECISIONES_A_H.md).
RECOMMENDED = {letter: "approve" for letter in DECISIONS}


def decisions_for(case_id):
    """The letters whose answer bears on this case, in order."""
    return [letter for letter, decision in DECISIONS.items() if case_id in decision["approve"]]


def derive(answers):
    """The C14 state of every bank case under these answers; the draft where unanswered."""
    unknown = set(answers) - set(DECISIONS)
    if unknown:
        raise ValueError(f"no such decision: {sorted(unknown)}")
    wrong = {letter: answer for letter, answer in answers.items() if answer not in {"approve", "reject", None}}
    if wrong:
        raise ValueError(f"an answer is approve or reject; edit the decision for a modification: {wrong}")
    rows = {}
    for case_id, drafted in DRAFT.items():
        letters = decisions_for(case_id)
        if not letters:
            rows[case_id] = drafted
            continue
        outcomes = []
        for letter in letters:
            answer = answers.get(letter)
            if answer is None:
                outcomes.append(drafted)
            elif DECISIONS[letter][answer][case_id] is not None:
                outcomes.append(DECISIONS[letter][answer][case_id])
        rows[case_id] = ("yes" if "yes" in outcomes else "uncertain" if "uncertain" in outcomes or not outcomes
                         else "no")
    return rows


def counts(rows):
    return {state: sum(1 for value in rows.values() if value == state) for state in STATES}
