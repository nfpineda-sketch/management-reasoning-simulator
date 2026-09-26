"""Which recorded outputs of one encounter stand on engine conventions still awaiting a decision.

Faculty instruction of 2026-09-26, point 5. The rubric never scores mg/kg
directly, but an engine convention can change gases, blood pressure, a
blocker's duration or the urine in the bag -- and through them the decisions
the resident took next and how those decisions read. So the faculty brief and
the rubric suggestion carry, per encounter, the specific observations that
depend on a convention the faculty has not yet decided
(docs/PESOS_CASOS.md, section 4), each named with its pending decision.

The scope is the observation, never the domain: a limitation that touches one
reading does not make the encounter unevaluable, and everything the note does
not name keeps its ordinary evidentiary weight. The rule the note states to
the reviewer: do not ground a deficiency on a named output alone.

Everything here is deterministic, read from the frozen trace and the launch
specification; no model call and no judgement of the resident.
"""
from __future__ import annotations

RULE = ("These outputs follow engine conventions the faculty has not yet decided "
        "(docs/PESOS_CASOS.md, section 4). They bound those specific observations only: "
        "do not ground a deficiency on one of them alone. Everything else in the "
        "encounter is evaluated as usual.")

#: Trace action types that run the ventilator (their gases follow the engine's
#: required-minute-ventilation and default-tidal-volume calibration at 70 kg).
_VENTILATION_TYPES = frozenset({"intubation", "ventilator", "ventilator_adjustment"})
_INFUSION_TYPES = frozenset({"norepinephrine", "epinephrine", "dobutamine", "sedation_infusion"})


def _spec(record_state):
    return (record_state or {}).get("encounter_spec") or {}


def _executed_actions(trace):
    for entry in trace or []:
        if not isinstance(entry, dict) or entry.get("execution_status") != "executed":
            continue
        minute = entry.get("decision_time_min", 0)
        for action in entry.get("interpreted_action") or []:
            if isinstance(action, dict):
                yield minute, action


def _order_words(action):
    agent = action.get("agent") or {"tranexamic_acid": "tranexamic acid",
                                    "epinephrine_im": "intramuscular epinephrine",
                                    "fluid": "crystalloid"}.get(action.get("type"), action.get("type"))
    written = action.get("per_kg_written")
    if not written:
        for field, unit in (("dose_mg_per_kg", "mg"), ("dose_g_per_kg", "g"),
                            ("dose_units_per_kg", "units"), ("volume_ml_per_kg", "mL")):
            if action.get(field) is not None:
                written = f"{action[field]:g} {unit}/kg"
                break
    if not written and action.get("units") and action.get("rate") is not None:
        written = f"{action['rate']:g} {action['units']}"
    return f"{agent} {written}".strip() if written else str(agent)


def notes(trace, state):
    """The convention-dependent observations of this encounter, or [].

    ``trace`` is the frozen management trace; ``state`` the launched (or
    closed) state whose spec says which rules and which case this was.
    """
    import patient_body
    spec = _spec(state)
    case = spec.get("clinical_case") or {}
    patient = case.get("patient") or {}
    rows = []
    weight_orders, infusion_orders, blockers, ventilated = [], [], [], False
    furosemide, urine_measured = False, False
    for minute, action in _executed_actions(trace):
        kind = action.get("type")
        if action.get("weight_convention_pending"):
            entry = f"min {minute} · {_order_words(action)}"
            (infusion_orders if kind in _INFUSION_TYPES else weight_orders).append(entry)
        if kind == "neuromuscular_blockade":
            blockers.append(f"min {minute} · {_order_words(action)}")
        if kind in _VENTILATION_TYPES:
            ventilated = True
        if kind == "diuretic":
            furosemide = True
        if kind == "urinary_catheter":
            urine_measured = True
    ambiguous = patient_body.relevant_ambiguity(patient)
    if weight_orders:
        rows.append({
            "id": "weight_basis",
            "decision": "Weight type per drug and indication (decisions C and E)",
            "observation": ("Converted on the chart's actual weight, the engine's stated "
                            "convention while the weight type for each drug is undecided: "
                            + "; ".join(weight_orders) + "."),
            "depends": "The executed dose, and what followed from it."})
    if infusion_orders:
        rows.append({
            "id": "infusion_effect",
            "decision": "Infusion weight basis and effect reference (decision E)",
            "observation": ("Rates per kilogram converted on the actual weight; the simulated "
                            "effect follows the absolute mcg/min, calibrated at 70 kg: "
                            + "; ".join(infusion_orders) + "."),
            "depends": "The pressure and heart-rate response recorded after these rates."})
    if blockers and patient_body.rules_apply(state) and ambiguous:
        rows.append({
            "id": "blocker_duration",
            "decision": "Neuromuscular blocker dosing weight (decision C)",
            "observation": ("The block's duration was measured on the actual weight, the "
                            "engine's convention, whatever weight the dose was written on: "
                            + "; ".join(blockers) + "."),
            "depends": "How long paralysis lasted, and any decision timed against it."})
    if ventilated and case.get("engine", {}).get("family") == "asthma":
        rows.append({
            "id": "minute_ventilation",
            "decision": "Required minute ventilation and default tidal volume (section 4)",
            "observation": ("The gases follow a required minute ventilation and a default "
                            "tidal volume calibrated at 70 kg, while a tidal volume per "
                            "kilogram uses the predicted body weight (decision B)."),
            "depends": "The PaCO2 and pH trajectory on the ventilator."})
    declared = (case.get("engine", {}) or {}).get("renal") or {}
    if declared.get("baseline_urine") and (furosemide or urine_measured):
        rows.append({
            "id": "residual_diuresis",
            "decision": "Baseline urine output and residual renal function (decision D)",
            "observation": ("This case declares minimal residual renal function; the exact "
                            "residual baseline the model ran on is a simulator convention "
                            "pending that decision."),
            "depends": "The measured urine output, and the response to the diuretic."})
    elif furosemide and urine_measured:
        rows.append({
            "id": "baseline_diuresis",
            "decision": "Baseline urine output weight basis (decision D)",
            "observation": ("The baseline urine output is calibrated at 70 kg whatever the "
                            "chart weighs, pending the faculty's basis for it."),
            "depends": "The measured urine output before and after the diuretic."})
    return rows


def for_record(record):
    """Notes for a stored attempt record (the faculty side)."""
    session = ((record or {}).get("payload") or {}).get("session") or {}
    trace = session.get("encounter_closed_trace") or session.get("management_trace") or []
    state = session.get("encounter_closed_state") or session.get("state") or {}
    return notes(trace, state)
