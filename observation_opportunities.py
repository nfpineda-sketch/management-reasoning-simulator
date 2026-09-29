"""What an encounter gave a real opportunity to observe, objective by objective.

Faculty decisions on DF-1 (D-1 to D-6), approved 2026-09-27 for cycle 3 of the
AI Advisor. The encounter does not decide which competencies were
demonstrated: it decides which objectives had a real opportunity to be
observed. The resident's performance produces the evidence, and the faculty
confirms the observation. This module answers only the first question.

Where the declaration lives. Next to its domains and critical events
(``case_assessment_bank``), a case may declare an ``objectives`` block:

    "objectives": {
        "C14": {"opportunity": "yes",
                "rationale": "why this case really offers it",
                "observable_component": "what part of the objective can be seen",
                "expected_evidence": ("what in the Management Trace would show it", ...),
                "reviewed": {"by": "who reviewed it clinically", "on": "YYYY-MM-DD"}},
        "C3": {"opportunity": "no", "reason": "why it does not",
               "reviewed": {"by": "...", "on": "YYYY-MM-DD"}},
    }

The block is part of the declaration ``evaluation_basis.freeze`` copies into
the encounter when it starts. That copy is versioned by its fingerprint and is
the only thing read afterwards: a later change to the case never changes what
an earlier encounter offered.

Three states, never merged:

* ``yes``: the case declares a real opportunity, and why;
* ``no``: the case declares there is none, and why;
* ``not_reviewed``: nobody has declared it either way. It is never read as
  ``no``, because missing metadata is not a clinical decision.

The expected evidence guides; it is not a whitelist. The faculty may still
recognise valid evidence nobody anticipated, reject what the AI proposes, or
judge that a declared opportunity did not really occur.

The transition (faculty, 2026-09-27, §56; DF-12 in the decision file). Until a
case is reviewed, an objective keeps the rule it had before opportunities
existed, and the result says so (rule ``transition_fallback``):

* TD1, F1, C1, C3, C4 and C14 are observable in every encounter;
* a Decision Challenge is observable in the encounter generated for it.

That rule takes nothing from an unreviewed case and adds nothing to it, and it
is withdrawn one case at a time as declarations are reviewed. It is the most
conservative and reversible of the transitions considered.

It is TRANSITIONAL, not the architecture (faculty, 2026-09-28): the target is
that only opportunities explicitly reviewed for a case are evaluable. C14 is
withdrawn first, then TD/F/C objective by objective, each only after its
clinical review; when every case of an objective is reviewed, the objective
leaves ``TRANSITION_OBJECTIVES``. Since cycle 9 every bank case declares TD1,
F1, C1 and C3 (tdfc_declarations; acs_54m_inferior once DF-20 was closed).
Generated cases, encounters with no authored case and encounters frozen before
keep the transition, so the four stay listed.

The observation environment (faculty, 2026-09-28, cycle 7). Some limits are
not a case's but the simulator's: C4 has no real opportunity in any encounter
this engine runs, because the engine does not model the procedural components
the EPA observes. ``ENVIRONMENT`` declares those objectives once, with who
decided it and why, and ``evaluation_basis.freeze`` copies it into every new
encounter -- a bank case, a generated case or an encounter with no authored
case. A case's own declaration wins over it. An encounter frozen before the
environment declared anything keeps the transition it started with: the
declaration is prospective, and historical encounters keep their context.

An opportunity is never a demonstration. ``yes`` only makes an objective
assessable: an observation exists when a faculty member assesses the
recorded performance (``progress_store.assess``), and never before.

The encounter's target is one source of opportunity, not the only one. An
encounter generated for one challenge can offer others that its case
declares (incidental observations, D-6). Nothing here assumes one objective
per encounter.
"""
from __future__ import annotations

# 1.1 (2026-09-28, cycle 7): the observation environment's own declarations.
VERSION = "1.1"
STATES = ("yes", "no", "not_reviewed")
# The rule that applied before opportunities were declared, kept for the
# transition: these six were observable in every encounter. C4 stays listed
# because the encounters frozen before the environment declared it keep this
# rule; no new encounter reaches it (ENVIRONMENT).
TRANSITION_OBJECTIVES = ("TD1", "F1", "C1", "C3", "C4", "C14")

C4_ENVIRONMENT_REASON = (
    "This simulator's observation environment offers no real opportunity to observe C4: the engine "
    "does not model the components of procedural sedation and analgesia the EPA observes (the "
    "procedure's pain, the depth of sedation, respiratory depression), and asking for a procedure is "
    "not an opportunity for C4 (TDFC-7). Evidence for C4 comes from procedural simulation or "
    "workplace observation.")

# What the simulator itself does not let anyone observe, whatever the case
# (faculty, 2026-09-28: TDFC-7, and H4 of cycle 7 for its scope). Frozen into
# every new encounter by evaluation_basis.freeze; a case's declaration wins.
ENVIRONMENT = {
    "C4": {"opportunity": "no", "reason": C4_ENVIRONMENT_REASON, "scope": "observation_environment",
           "reviewed": {"by": "Nicolás Pineda", "on": "2026-09-28", "source": "faculty_decision",
                        "decision_group": "TDFC-7", "version": "C4-ENVIRONMENT-1"}},
}

_NEEDS = {"yes": ("rationale", "observable_component", "expected_evidence"), "no": ("reason",)}
# What stays outside the encounter travels with a YES: an opportunity is never the full EPA
# observed (TDFC, cycle 8).
_CARRIED = ("rationale", "reason", "observable_component", "expected_evidence", "outside_the_encounter",
            "reviewed", "scope")
_NOTES = {
    "generation_target": "The encounter was generated to offer this objective.",
    "declared_yes": "The case declares a real opportunity to observe this objective.",
    "declared_no": "The case declares no opportunity to observe this objective.",
    "environment_yes": "The simulator's observation environment declares an opportunity to observe this objective.",
    "environment_no": ("The simulator's observation environment declares no opportunity to observe "
                       "this objective, whatever the case."),
    "transition_open": ("Not reviewed for this case. It stays observable under the rule that applied "
                        "before observation opportunities were declared."),
    "transition_closed": ("Not reviewed for this case. Under the rule that applied before, only the "
                          "encounter generated for this objective offers it."),
    "not_enabled": "This objective is not enabled.",
    "unknown": "This objective does not exist.",
}


def _filled(value):
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple)):
        return bool(value) and all(isinstance(item, str) and item.strip() for item in value)
    return False


def verify_block(case_id, block, known_objectives=None):
    """Every way a case's objectives block is malformed. Empty is good.

    ``case_assessment.verify`` calls it for the shape, without the objective
    catalogue, which the rubric must not know; ``verify_bank`` passes the
    catalogue to check the names too. A malformed declaration is a defect of
    the case, found before any encounter uses it.
    """
    if block is None:
        return []
    if not isinstance(block, dict):
        return [f"{case_id}: the objectives block is not a mapping."]
    problems = []
    for objective_id, entry in block.items():
        where = f"{case_id} {objective_id}"
        if known_objectives is not None and objective_id not in known_objectives:
            problems.append(f"{where}: unknown objective.")
            continue
        if not isinstance(entry, dict):
            problems.append(f"{where}: the declaration is not a mapping.")
            continue
        state = entry.get("opportunity")
        if state not in _NEEDS:
            problems.append(f"{where}: the opportunity must be 'yes' or 'no'. An objective nobody "
                            "has reviewed is left out of the block, not declared.")
            continue
        for field in _NEEDS[state]:
            if not _filled(entry.get(field)):
                problems.append(f"{where}: an opportunity '{state}' needs its {field}.")
        reviewed = entry.get("reviewed")
        if not isinstance(reviewed, dict) or not _filled(reviewed.get("by")) or not _filled(reviewed.get("on")):
            problems.append(f"{where}: a declaration says who reviewed it and when.")
    return problems


def verify_bank():
    """Every problem in the bank's declared opportunities, objective names included."""
    from case_assessment_bank import CANDIDATES, CASES
    from objectives import OBJECTIVES
    problems = verify_block("observation environment", ENVIRONMENT, OBJECTIVES)
    for case_id, declaration in {**CANDIDATES, **CASES}.items():
        problems.extend(verify_block(case_id, declaration.get("objectives"), OBJECTIVES))
    return problems


def environment_block():
    """The observation environment's declarations, as a plain copy to freeze."""
    from copy import deepcopy
    return deepcopy(ENVIRONMENT)


def basis_of(record):
    """The declared objectives the record carries, and where they come from.

    Only a frozen copy is read. A record saved before copies existed, or one
    whose copy cannot be read, has no declared opportunities: the current
    declarations of its case are never applied to it retroactively. The
    observation environment's declarations are read only from a copy frozen
    with the encounter, and a case's own declaration wins over them.
    """
    import evaluation_basis
    basis = evaluation_basis.resolve(record)
    status = basis["status"]
    found = {"basis_status": status, "case_id": basis.get("case_id") or None,
             "basis_fingerprint": basis.get("fingerprint")}
    environment = basis.get("environment") if isinstance(basis.get("environment"), dict) else None
    if status != "frozen":
        if environment and status in ("generated", "no_authored_case"):
            return dict(environment), {**found, "declaration_source": "observation_environment"}
        return None, {**found, "declaration_source": "record_without_frozen_declaration"}
    declared = (basis.get("declaration") or {}).get("objectives")
    if declared is None:
        # The case declares nothing; what the environment declares still applies.
        read_opportunities = "opportunities" in (basis.get("versions") or {})
        return (dict(environment) if environment else None), {
            **found, "declaration_source": ("case_without_objectives" if read_opportunities
                                            else "frozen_before_opportunities")}
    return {**(environment or {}), **declared}, {**found, "declaration_source": "frozen_declaration"}


def resolve(objective_id, record, *, basis=None):
    """This objective's opportunity in this encounter: state, rule and eligibility.

    ``basis`` is ``basis_of(record)`` when the caller already has it.
    """
    from competency_mapping import CHALLENGE_MAPPINGS, record_challenge_id
    from objectives import OBJECTIVES
    result = {"objective_id": objective_id, "version": VERSION}
    definition = OBJECTIVES.get(objective_id)
    if definition is None:
        return {**result, "state": "not_reviewed", "eligible": False, "rule": "unknown_objective",
                "note": _NOTES["unknown"]}
    declared, where = basis if basis is not None else basis_of(record)
    entry = (declared or {}).get(objective_id) if isinstance(declared, dict) else None
    result.update(where)
    if entry is not None:
        result.update({key: entry[key] for key in _CARRIED if key in entry})
    if not definition["supported"]:
        return {**result, "state": entry["opportunity"] if entry else "not_reviewed", "eligible": False,
                "rule": "objective_not_enabled", "note": _NOTES["not_enabled"]}
    if objective_id in CHALLENGE_MAPPINGS and record_challenge_id(record) == objective_id:
        return {**result, "state": "yes", "eligible": True, "rule": "generation_target",
                "note": _NOTES["generation_target"]}
    if entry is not None:
        state = entry["opportunity"]
        environment = entry.get("scope") == "observation_environment"
        return {**result, "state": state, "eligible": state == "yes", "rule": "declared",
                "note": _NOTES["environment_" + state if environment else "declared_" + state]}
    open_ = objective_id in TRANSITION_OBJECTIVES
    return {**result, "state": "not_reviewed", "eligible": open_, "rule": "transition_fallback",
            "note": _NOTES["transition_open" if open_ else "transition_closed"]}


def summary(record):
    """Every objective's opportunity in this encounter, reading its basis once."""
    from objectives import OBJECTIVES
    basis = basis_of(record)
    return {objective_id: resolve(objective_id, record, basis=basis) for objective_id in OBJECTIVES}
