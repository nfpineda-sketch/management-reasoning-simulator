"""Expose the real order/trajectory contract to the case author and reviewer.

These are software capabilities, not recommended clinical treatments or doses.
Examples are parsed and checked by the same validators as the live encounter;
they never execute an intervention or modify patient state.
"""
from copy import deepcopy

from family_engine import _DEVICES, _MEDICINES, _ROUTES, _validate
from family_parser import _AGENTS, parse_family_actions
from generated_engine import (
    BOUNDS, MODEL, OBSERVED_FIELDS, _ACTIVE, _DOSE_FIELDS, _DRUGS, _matches,
    validate_declarative_case,
)
from generated_case_schema import ACTIONS, BOUNDS as INITIAL_BOUNDS


# Syntax examples only. Their parsed representation is checked below rather
# than maintaining a second hand-written representation of live order shapes.
_SYNTAX_EXAMPLES = (
    "Give 500 mL normal saline",
    "Apply nasal cannula at 2 L/min",
    "Start BiPAP IPAP 10 EPAP 5 FiO2 40%",
    "Start nitroglycerin at 10 mcg/min",
    "Give ceftriaxone 1000 mg IV",
    "Give albuterol 2.5 mg nebulized",
    "Give hydrocortisone 100 mg IV",
    "Give dextrose 25 g IV",
    "Give naloxone 0.4 mg IV",
    "Transfuse 1 unit packed red cells",
    "Give pantoprazole 40 mg IV",
    "Give aspirin 325 mg PO",
    "Give heparin 5000 units IV",
    "Start bag-mask ventilation",
    "Intubate VC/AC FiO2 50% PEEP 5",
    "Start norepinephrine 0.05 mcg/kg/min",
    "Start dobutamine 5 mcg/kg/min",
    "Give furosemide 40 mg IV",
    "Give metoprolol 2.5 mg IV",
    "Give diltiazem 5 mg IV",
    "Give amiodarone 150 mg IV",
    "Give etomidate 8 mg IV",
    "Perform synchronized cardioversion 200 J",
    "Set ventilator FiO2 50% PEEP 5",
)
# Candidate spellings are filtered by the existing response matcher/validator.
# Adding a candidate here cannot make a new unit executable.
_UNIT_CANDIDATES = ("mg", "g", "mL", "L/min", "mcg/min", "mcg/kg/min", "units", "U", "IU")


def _validate_response_fields(rule):
    # A zero-effect software probe, never an authored patient or executed order.
    # The full validator also checks mandatory matchers that its lower-level
    # capability helper intentionally leaves to its caller (e.g. oxygen device).
    case = {
        "observable": {"mental_status": "Alert", "pulse_present": True,
                       **{key: sum(BOUNDS[key]) / 2 for key in OBSERVED_FIELDS}},
        "engine": {
            "model": MODEL, "horizon_min": 1, "initial_labs": {},
            "untreated_drift_per_min": {}, "state_rules": [],
            "response_rules": [{"id": "contract_probe", "onset_min": 0,
                                "duration_min": 1, "max_exposure": 1, "delta": {}, **rule}],
        },
    }
    validate_declarative_case(case)


def _accepted_matchers(rule, field, candidates):
    accepted = []
    for candidate in candidates:
        proposed = {**rule, field: candidate}
        try:
            _validate_response_fields(proposed)
        except ValueError:
            continue
        accepted.append(candidate)
    return accepted


def executable_generation_constraints():
    """Return JSON-ready constraints derived from current runtime contracts."""
    contracts = {}
    for text in _SYNTAX_EXAMPLES:
        normalized, error = _validate(
            {"engine_family": "generated", "observable": {"mental_status": "Alert", "pulse_present": True},
             "treatments": {"invasive_ventilation": True, "ventilator_mode": "VC/AC", "ventilator_fio2_percent": 50, "ventilator_peep_cmh2o": 5}}, parse_family_actions(text)
        )
        if error or not normalized or len(normalized) != 1:
            raise ValueError("A generation capability example no longer matches the order interpreter.")
        action = normalized[0]
        kind = action["type"]
        if kind not in ACTIONS or kind in contracts:
            raise ValueError("Generation capability examples do not uniquely cover the supported actions.")
        dose_field = _DOSE_FIELDS.get(kind)
        rule = {
            "action_type": kind,
            "agent": (action.get("agent") or kind) if kind in _DRUGS else None,
            "route": action.get("route") or ("IV" if kind in _DRUGS else None),
            "units": action.get("units") if isinstance(action.get("units"), str) else None,
            "device": action.get("device"),
            "dose_field": dose_field,
            "reference_dose": action.get(dose_field) if dose_field else None,
        }
        if kind == "cardioversion":
            rule["settings"] = {"energy_j": action["energy_j"]}
        elif kind == "ventilator_adjustment":
            rule["settings"] = {"fio2_percent": action["fio2_percent"], "peep_cmh2o": action["peep_cmh2o"]}
        # Fill unit labels only when the live matching logic recognizes them.
        if rule["units"] is None:
            rule["units"] = next(
                (unit for unit in _UNIT_CANDIDATES if _matches({**rule, "units": unit}, action)),
                None,
            )
        _validate_response_fields(rule)
        contract = {
            "dose_field": dose_field,
            "agent_values": sorted(_AGENTS.get(kind, {kind: None})) if kind in _DRUGS else [None],
            "route_values": _accepted_matchers(rule, "route", [None, *sorted(set(_ROUTES.values()))]),
            "unit_values": _accepted_matchers(rule, "units", [None, *_UNIT_CANDIDATES]),
            "device_values": _accepted_matchers(rule, "device", [None, *sorted(set(_DEVICES.values()) - {"Room air"})]),
            "active_support": kind in _ACTIVE,
            "validated_order_example": deepcopy(action),
            "matching_response_fields_example": rule,
        }
        if kind in _MEDICINES:
            _, lower, upper = _MEDICINES[kind]
            contract["reference_dose_software_bounds"] = {"minimum": lower, "maximum": upper}
        contracts[kind] = contract
    if set(contracts) != set(ACTIONS):
        raise ValueError("Generation capability examples must cover all supported actions.")
    return {
        "execution_model": "main_ia_v1",
        "action_contracts": contracts,
        "initial_numeric_bounds": {key: list(value) for key, value in INITIAL_BOUNDS.items()},
        "trajectory_numeric_bounds": {key: list(value) for key, value in BOUNDS.items()},
        "contract_notes": [
            "All newly generated cases use the complete main/IA physiological core. Native actions need no response rules or ventilator interpolation grids; matching-response examples below apply only to declared extensions. Native numeric response deltas are ignored.",
            "All values are software capabilities, not clinical recommendations. Example doses are syntax/exposure examples, not default prescriptions or preferred management paths.",
            "Use matching_response_fields_example for field shape. Select the actual agent, route, reference exposure and physiologic effect appropriate to the newly authored patient; a route accepted by software may still be clinically inappropriate for a particular drug.",
            "Use only listed matcher values. Fluid, blood and respiratory support have null route/agent matchers because the normalized orders do not carry those fields; do not invent an IV route matcher for fluids or blood.",
            "Norepinephrine and nitroglycerin use their action_type as agent and IV as route. Anticoagulation and norepinephrine require explicit units. Dose-based units are case-sensitive canonical strings.",
            "No-dose actions use null dose_field and reference_dose. Every measured action needs a positive reference_dose using exactly its dose_field.",
            "Initial numeric fields must satisfy initial_numeric_bounds. Untreated drift and every isolated maximum-exposure rule must remain within trajectory_numeric_bounds throughout horizon_min, with systolic pressure greater than diastolic pressure.",
            "Generic response rules use their linear onset/duration/recovery envelope. Rules with volume_basis instead read net current compartments; rules with exposure_curve pool active depot/effect-site exposure and transform it with the authored curve. Coupled responses must fit the bounds at both time endpoints and their positive/negative exposure extremes. Concurrent orders undergo an additional atomic runtime bounds check.",
            "A change that reaches a bound at one reference exposure may exceed it at max_exposure. In particular, oxygen saturation cannot exceed 100 and capillary refill cannot become negative. Preserve realistic limits without fabricating clinical recovery.",
        ],
    }
