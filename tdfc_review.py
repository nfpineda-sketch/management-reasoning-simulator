"""The TDFC review: the faculty's decisions TDFC-1 to TDFC-8 and the rows they derive.

TD1, F1, C1, C3 and C4 follow the path C14 took (``c14_review``): an AI draft,
the faculty's decisions, a declaration per case with its provenance, frozen with
each new encounter (``evaluation_basis.freeze``).

* The cycle 5 draft classified the 31 bank cases objective by objective as
  YES, NO or UNCERTAIN (docs/tdfc/BORRADOR_TDFC.md): 133 clear combinations
  and 22 uncertain ones, grouped into eight decisions
  (docs/tdfc/DECISIONES_TDFC.md, docs/tdfc/TDFC_DECISIONS_FOR_NICOLAS.md).
* TDFC-7 (C4 = NO) was decided in cycle 6 and written in cycle 7, for the whole
  observation environment.
* The faculty approved TDFC-1 to 6 and 8 conceptually "según las
  recomendaciones actuales" (cycle 7 instruction, §28), deferring the
  implementation to cycle 8. The recommendation for TDFC-6 differs from the
  draft: YES in the two pneumonias and pulmonary_embolism_61m, NO in the other
  three.
* acs_54m_inferior kept every TD/F/C row unwritten until DF-20 (its right
  ventricle) was decided, as the recommendation for TDFC-5 said. The faculty
  closed DF-20 on 2026-09-29 with no change to the case (cycle 9), and its rows,
  the ones the approved decisions derive, are declared. No case is pending.

This module holds the draft and derives the state each row takes. It writes
nothing to the bank: ``tdfc_declarations`` holds the rows, and the tests check
them against ``final_states``. An opportunity is never observed behaviour: the
resident's performance, a proposal and the faculty's confirmation still decide.
"""
from __future__ import annotations

OBJECTIVES = ("TD1", "F1", "C1", "C3", "C4")
STATES = ("yes", "no", "uncertain")

_Y, _N, _U = "yes", "no", "uncertain"


def _row(td1, f1, c1, c3, c4):
    return dict(zip(OBJECTIVES, (td1, f1, c1, c3, c4)))


# The cycle 5 draft, row by row (the "Estados por caso" table of docs/tdfc/BORRADOR_TDFC.md).
DRAFT = {
    "acs_54m_inferior": _row(_Y, _Y, _U, _N, _N),
    "acs_66f_nonst": _row(_U, _N, _N, _N, _N),
    "acs_61m_posterior": _row(_U, _N, _N, _N, _N),
    "acs_52m_de_winter": _row(_U, _N, _N, _N, _N),
    "acs_48m_wellens": _row(_N, _N, _N, _N, _N),
    "acs_70f_left_main": _row(_Y, _Y, _Y, _U, _N),
    "anaphylaxis_29f": _row(_Y, _Y, _Y, _Y, _N),
    "anaphylaxis_63m_betablocked": _row(_Y, _Y, _Y, _U, _N),
    "asthma_24f": _row(_Y, _Y, _U, _U, _N),
    "asthma_49m": _row(_Y, _Y, _Y, _Y, _N),
    "bradycardia_ccb_68m": _row(_Y, _Y, _Y, _N, _N),
    "bradycardia_avb3_78f": _row(_Y, _Y, _Y, _N, _U),
    "bradycardia_bb_54f": _row(_Y, _Y, _Y, _N, _N),
    "bradycardia_hyperk_63m": _row(_Y, _Y, _Y, _N, _N),
    "gi_bleed_57m": _row(_Y, _Y, _Y, _N, _N),
    "gi_bleed_72f": _row(_Y, _Y, _Y, _N, _N),
    "hypoglycemia_28m": _row(_Y, _U, _N, _N, _N),
    "hypoglycemia_76f": _row(_Y, _U, _N, _N, _N),
    "hypoglycemia_54m_thiamine": _row(_Y, _U, _N, _N, _N),
    "opioid_35m": _row(_Y, _Y, _Y, _Y, _N),
    "opioid_67f": _row(_Y, _Y, _Y, _Y, _N),
    "pneumonia_46f": _row(_Y, _Y, _Y, _U, _N),
    "pneumonia_83m": _row(_Y, _Y, _Y, _U, _N),
    "pulmonary_edema_58m": _row(_Y, _Y, _Y, _Y, _N),
    "pulmonary_edema_75f": _row(_Y, _Y, _Y, _Y, _N),
    "pulmonary_embolism_33f": _row(_Y, _Y, _U, _U, _N),
    "pulmonary_embolism_61m": _row(_Y, _Y, _Y, _U, _N),
    "renal_colic_34m": _row(_N, _N, _N, _N, _U),
    "obstructive_pyelonephritis_58f": _row(_Y, _Y, _Y, _N, _N),
    "trauma_limb_hemorrhage_27m": _row(_Y, _Y, _U, _N, _U),
    "trauma_hemothorax_41m": _row(_Y, _Y, _U, _N, _U),
}


def _cells(pairs, approve, reject):
    return {"approve": {pair: approve for pair in pairs}, "reject": {pair: reject for pair in pairs}}


# What each answer yields for the combinations a decision covers. "approve" is the
# recommendation of docs/tdfc/TDFC_DECISIONS_FOR_NICOLAS.md; "reject" is its opposite.
DECISIONS = {
    "TDFC-1": {"question": "TD1 in a stable acute coronary syndrome whose ECG needs immediate intervention",
               **_cells([("acs_66f_nonst", "TD1"), ("acs_61m_posterior", "TD1"), ("acs_52m_de_winter", "TD1")],
                        _N, _Y)},
    "TDFC-2": {"question": "F1 in hypoglycaemia with airway, breathing and circulation preserved",
               **_cells([("hypoglycemia_28m", "F1"), ("hypoglycemia_76f", "F1"), ("hypoglycemia_54m_thiamine", "F1")],
                        _Y, _N)},
    "TDFC-3": {"question": "C1 in severe hypoxaemia without shock that first-line treatment stabilises",
               **_cells([("pulmonary_embolism_33f", "C1"), ("asthma_24f", "C1")], _N, _Y)},
    "TDFC-4": {"question": "C1 in trauma while C2 is disabled",
               **_cells([("trauma_limb_hemorrhage_27m", "C1"), ("trauma_hemothorax_41m", "C1")], _N, _Y)},
    "TDFC-5": {"question": "C1 and C3 in a deterioration the engine produces by design while reperfusion is awaited",
               **_cells([("acs_54m_inferior", "C1"), ("acs_70f_left_main", "C3")], _Y, _N)},
    "TDFC-6": {"question": "C3 for oxygen in hypoxaemia without ventilatory failure or an airway threat",
               # The recommendation differs from the draft, which proposed YES in all six.
               "approve": {("pneumonia_46f", "C3"): _Y, ("pneumonia_83m", "C3"): _Y,
                           ("pulmonary_embolism_61m", "C3"): _Y, ("pulmonary_embolism_33f", "C3"): _N,
                           ("asthma_24f", "C3"): _N, ("anaphylaxis_63m_betablocked", "C3"): _N},
               "reject": {pair: _N for pair in (("pneumonia_46f", "C3"), ("pneumonia_83m", "C3"),
                                                 ("pulmonary_embolism_61m", "C3"), ("pulmonary_embolism_33f", "C3"),
                                                 ("asthma_24f", "C3"), ("anaphylaxis_63m_betablocked", "C3"))}},
    "TDFC-7": {"question": "C4 for sedoanalgesia for a procedure the case brings and does not declare",
               **_cells([("bradycardia_avb3_78f", "C4"), ("trauma_hemothorax_41m", "C4"),
                         ("trauma_limb_hemorrhage_27m", "C4")], _N, _Y)},
    "TDFC-8": {"question": "C4 for the condition's own analgesia, with no procedure",
               **_cells([("renal_colic_34m", "C4")], _N, _Y)},
}

# The faculty's answers. TDFC-7 in cycle 6 (written in cycle 7 for the whole observation
# environment); TDFC-1 to 6 and 8 approved conceptually as recommended on 2026-09-28 (cycle 7, §28).
APPROVED = {key: "approve" for key in DECISIONS}

# Cases whose TD/F/C rows are not written yet, and why. They keep the transition rule. None since
# DF-20 was closed (cycle 9, 2026-09-29).
PENDING = {}


def covering(case_id, objective_id):
    """The decisions that settle this combination (at most one, by construction)."""
    return [key for key, decision in DECISIONS.items() if (case_id, objective_id) in decision["approve"]]


def derive(answers):
    """Each combination's state under these answers; the draft where nothing answers it."""
    rows = {}
    for case_id, draft in DRAFT.items():
        rows[case_id] = {}
        for objective_id, state in draft.items():
            keys = covering(case_id, objective_id)
            if not keys:
                rows[case_id][objective_id] = state
                continue
            results = [DECISIONS[key][answers[key]][(case_id, objective_id)] if answers.get(key) else _U
                       for key in keys]
            rows[case_id][objective_id] = _Y if _Y in results else _U if _U in results else _N
    return rows


def final_states():
    """The rows the bank declares for TD1, F1, C1 and C3: the approved answers, pending cases left out.

    C4 is declared for the whole observation environment (case_assessment_bank.C4_DECLARATIONS).
    """
    rows = derive(APPROVED)
    return {case_id: {objective_id: rows[case_id][objective_id] for objective_id in ("TD1", "F1", "C1", "C3")}
            for case_id in rows if case_id not in PENDING}


def decision_group(case_id, objective_id):
    """The decision that settled a row, or "clear" when the draft had already classified it."""
    keys = covering(case_id, objective_id)
    return keys[0] if keys else "clear"


def counts(rows=None):
    """YES / NO per objective over the rows given (the final ones by default)."""
    rows = final_states() if rows is None else rows
    return {objective_id: (sum(1 for row in rows.values() if row.get(objective_id) == _Y),
                           sum(1 for row in rows.values() if row.get(objective_id) == _N))
            for objective_id in ("TD1", "F1", "C1", "C3")}


# --- the final table: what the bank declares, row by row (cycle 8) ---------------------------

PENDING_NOTE = ("Not written: waits for DF-20, the decision on this case's right ventricle (recommendation of "
                "TDFC-5). Its TD/F/C objectives keep the transition rule until then.")


def final_table():
    """One row per bank case and objective (TD1, F1, C1, C3), in the draft's order, read from the bank."""
    from case_assessment_bank import CASES
    rows = []
    for case_id in DRAFT:
        declared = CASES[case_id].get("objectives") or {}
        for objective_id in ("TD1", "F1", "C1", "C3"):
            entry = declared.get(objective_id)
            if entry is None:
                rows.append({"case_id": case_id, "objective_id": objective_id, "opportunity": "NOT REVIEWED",
                             "rationale": PENDING_NOTE, "observable_component": "", "expected_evidence": (),
                             "outside_the_encounter": "", "review_source": "none yet"})
                continue
            reviewed = entry["reviewed"]
            group = reviewed["decision_group"]
            rows.append({
                "case_id": case_id, "objective_id": objective_id, "opportunity": entry["opportunity"].upper(),
                "rationale": entry.get("rationale") or entry["reason"],
                "observable_component": entry.get("observable_component", ""),
                "expected_evidence": tuple(entry.get("expected_evidence", ())),
                "outside_the_encounter": entry.get("outside_the_encounter", ""),
                "review_source": ("clear row" if group == "clear" else f"decision {group}") + f"; {reviewed['version']}"
                                 + (f"; revised {reviewed['revised']['id']} ({reviewed['revised']['on']})"
                                    if reviewed.get("revised") else "")})
    return rows


def final_table_markdown():
    """The table of docs/tdfc/TDFC_TABLA_FINAL.md, exactly."""
    def cell(value):
        return str(value).replace("|", "\\|").replace("\n", " ")
    lines = ["| CASE ID | OBJ. | OPPORTUNITY | RATIONALE (YES) / REASON (NO) | OBSERVABLE COMPONENT | "
             "EXPECTED TRACE EVIDENCE | OUTSIDE THE ENCOUNTER | SOURCE |",
             "|---|---|---|---|---|---|---|---|"]
    for row in final_table():
        lines.append("| " + " | ".join(cell(value) for value in (
            f"`{row['case_id']}`", row["objective_id"], row["opportunity"], row["rationale"],
            row["observable_component"] or "—", "; ".join(row["expected_evidence"]) or "—",
            row["outside_the_encounter"] or "—", row["review_source"])) + " |")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    print(final_table_markdown(), end="")
