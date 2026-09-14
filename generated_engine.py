"""Execute AI-authored *data*, never AI-authored code, as a bounded simulation.

Case declarations are validated before any order. Numeric trajectories use only
elapsed simulation time and explicitly administered exposure. Learner reasoning,
bias labels, grades and post-hoc reflections cannot affect physiology. This is a
teaching model requiring clinical review, not a clinical prediction engine.
"""
from copy import deepcopy
import math

from family_engine import (
    _failure, _initialize as _initialize_orders, _order, _validate as _validate_orders,
    _release_diagnostic,
)

MODEL = "declarative_v1"
OBSERVED_FIELDS = frozenset({"sbp", "dbp", "hr", "spo2", "respiratory_rate", "crt", "temperature_c", "glucose_mg_dl"})
LAB_FIELDS = frozenset({"hemoglobin_g_dl", "lactate_mmol_l", "pco2_mm_hg", "bicarbonate_mmol_l", "pao2_mm_hg"})
NUMERIC_FIELDS = OBSERVED_FIELDS | LAB_FIELDS
BOUNDS = {
    "sbp": (20, 300), "dbp": (10, 180), "hr": (20, 300), "spo2": (30, 100),
    "respiratory_rate": (4, 60), "crt": (.1, 12), "temperature_c": (25, 43),
    "glucose_mg_dl": (10, 1000), "hemoglobin_g_dl": (1, 25), "lactate_mmol_l": (.1, 30),
    "pco2_mm_hg": (10, 150), "bicarbonate_mmol_l": (2, 60), "pao2_mm_hg": (10, 600),
}
_ACTIVE = frozenset({"oxygen", "niv", "bag_mask", "intubation", "norepinephrine", "nitroglycerin"})
_RESPIRATORY = frozenset({"oxygen", "niv", "bag_mask", "intubation"})
_ADMIN = frozenset({"consult", "reperfusion_referral", "disposition"})
_DOSE_FIELDS = {
    "fluid": "volume_ml", "blood": "units", "dextrose": "dose_g", "naloxone": "dose_mg",
    "antibiotics": "dose_mg", "bronchodilator": "dose_mg", "steroid": "dose_mg",
    "ppi": "dose_mg", "aspirin": "dose_mg", "diuretic": "dose_mg", "anticoagulation": "dose",
    "nitroglycerin": "rate_mcg_min", "norepinephrine": "rate", "oxygen": "flow_lpm",
}
_DRUGS = frozenset({"dextrose", "naloxone", "antibiotics", "bronchodilator", "steroid", "ppi", "aspirin", "diuretic", "anticoagulation", "nitroglycerin", "norepinephrine"})
_ACTIONS = frozenset(_DOSE_FIELDS) | _ACTIVE
_COMPARATORS = {"lt": lambda a, b: a < b, "lte": lambda a, b: a <= b, "gt": lambda a, b: a > b, "gte": lambda a, b: a >= b, "eq": lambda a, b: a == b}
_SET_FIELDS = frozenset({"mental_status", "work_of_breathing", "extremities", "peripheral_perfusion", "pulse_present", "rhythm", "ecg_profile", "visual"})


def _finite(value):
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)


def _case(state):
    return state.get("encounter_spec", {}).get("clinical_case", {})


def _number_map(value, name, *, initial=False):
    if not isinstance(value, dict) or set(value) - NUMERIC_FIELDS:
        raise ValueError(f"{name} has unsupported physiological fields.")
    for key, number in value.items():
        if not _finite(number):
            raise ValueError(f"{name}.{key} must be a finite number.")
        lower, upper = BOUNDS[key]
        if initial and not lower <= number <= upper:
            raise ValueError(f"{name}.{key} is outside the supported physiological range.")
        if not initial and abs(number) > upper - lower:
            raise ValueError(f"{name}.{key} exceeds the supported physiological range.")


def validate_declarative_case(case):
    """Raise ValueError for non-executable declarations, independently of the LLM schema."""
    if not isinstance(case, dict) or not isinstance(case.get("engine"), dict):
        raise ValueError("A declarative clinical engine is required.")
    engine = case["engine"]
    if engine.get("model") != MODEL:
        raise ValueError("Unsupported generated trajectory model.")
    observed = case.get("observable", {})
    if not isinstance(observed, dict) or not OBSERVED_FIELDS <= set(observed):
        raise ValueError("The generated case must include all baseline observations.")
    _number_map({k: observed[k] for k in OBSERVED_FIELDS}, "observable", initial=True)
    if observed["dbp"] >= observed["sbp"]:
        raise ValueError("Baseline systolic pressure must exceed diastolic pressure.")
    if observed.get("pulse_present") is not True:
        raise ValueError("Generated arrest trajectories are not supported by this action engine.")
    initial_labs = engine.get("initial_labs", {})
    if not isinstance(initial_labs, dict) or set(initial_labs) - LAB_FIELDS:
        raise ValueError("Initial laboratory physiology has unsupported fields.")
    _number_map(initial_labs, "initial_labs", initial=True)
    initialized = OBSERVED_FIELDS | set(initial_labs)
    drift = engine.get("untreated_drift_per_min", {})
    _number_map(drift, "untreated_drift_per_min")
    if any(value and key not in initialized for key, value in drift.items()):
        raise ValueError("A drifting laboratory field needs an initial value.")
    horizon = engine.get("horizon_min", 180)
    if not _finite(horizon) or not 1 <= horizon <= 240 or int(horizon) != horizon:
        raise ValueError("The generated trajectory needs a finite supported time horizon.")
    rules = engine.get("response_rules")
    if not isinstance(rules, list) or not 1 <= len(rules) <= 64:
        raise ValueError("The generated trajectory needs explicit treatment response rules.")
    identifiers = set()
    for rule in rules:
        if not isinstance(rule, dict) or not isinstance(rule.get("id"), str) or not rule["id"] or rule["id"] in identifiers:
            raise ValueError("Response rules need unique identifiers.")
        identifiers.add(rule["id"])
        kind = rule.get("action_type")
        if kind not in _ACTIONS:
            raise ValueError("A response rule has an unsupported action type.")
        for field in ("agent", "route", "units", "device"):
            if rule.get(field) is not None and (not isinstance(rule[field], str) or not rule[field].strip()):
                raise ValueError(f"A response rule has an invalid {field} matcher.")
        if kind in _DRUGS and (not rule.get("agent") or not rule.get("route")):
            raise ValueError("Medication effects need an exact agent and route.")
        if kind in {"norepinephrine", "anticoagulation"} and not rule.get("units"):
            raise ValueError("A variable-unit medication effect needs explicit dose units.")
        expected = _DOSE_FIELDS.get(kind)
        if expected:
            if rule.get("dose_field") != expected or not _finite(rule.get("reference_dose")) or rule["reference_dose"] <= 0:
                raise ValueError("Response exposure must use the actual action dose and a positive reference dose.")
        elif rule.get("dose_field") is not None:
            raise ValueError("An unmeasured action cannot invent a dose exposure.")
        if kind == "oxygen" and not rule.get("device"):
            raise ValueError("Oxygen effects must identify the oxygen device.")
        if not _finite(rule.get("onset_min")) or not 0 <= rule["onset_min"] <= 240:
            raise ValueError("Response onset must be a nonnegative supported interval.")
        if not _finite(rule.get("duration_min")) or not 1 <= rule["duration_min"] <= 240:
            raise ValueError("Response duration must be positive and supported.")
        if not _finite(rule.get("max_exposure")) or not 0 < rule["max_exposure"] <= 20:
            raise ValueError("Response exposure must have a finite positive cap.")
        _validate_response_capability(case, rule)
        _number_map(rule.get("delta"), "response delta")
        if any(value and key not in initialized for key, value in rule["delta"].items()):
            raise ValueError("A treatment-responsive laboratory field needs an initial value.")
    initial_values = {key: observed[key] for key in OBSERVED_FIELDS}
    initial_values.update(initial_labs)
    # The data contract must remain executable through its authored horizon.
    # Check the untreated path and each isolated maximum-exposure response at
    # all breakpoints; combinations are checked atomically when ordered.
    for response in [None] + rules:
        times = {0, horizon}
        if response is not None:
            times.update({min(horizon, response["onset_min"]), min(horizon, response["onset_min"] + response["duration_min"])})
        for at in times:
            values = {key: number + at * drift.get(key, 0) for key, number in initial_values.items()}
            if response is not None:
                progress = min(1, max(0, (at - response["onset_min"]) / response["duration_min"]))
                for key, delta in response["delta"].items():
                    if key in values:
                        values[key] += delta * response["max_exposure"] * progress
            if any(not BOUNDS[key][0] <= number <= BOUNDS[key][1] for key, number in values.items()):
                raise ValueError("A generated trajectory exceeds supported physiology within its stated horizon.")
            if values["dbp"] >= values["sbp"]:
                raise ValueError("A generated trajectory produces inconsistent blood pressure.")
    state_rules = engine.get("state_rules", [])
    if not isinstance(state_rules, list) or len(state_rules) > 64:
        raise ValueError("Invalid physiological observation rules.")
    from ecg12 import PROFILES
    for rule in state_rules:
        if not isinstance(rule, dict) or not isinstance(rule.get("when"), list) or not rule["when"]:
            raise ValueError("Observation changes must have physiological conditions.")
        for condition in rule["when"]:
            if not isinstance(condition, dict) or condition.get("field") not in initialized or condition.get("operator") not in _COMPARATORS or not _finite(condition.get("value")):
                raise ValueError("Observation rules may read only declared numeric physiology.")
        values = rule.get("set", {})
        if not isinstance(values, dict) or set(values) - _SET_FIELDS:
            raise ValueError("An observation rule has unsupported output fields.")
        for key, value in values.items():
            if key == "pulse_present":
                if value is not True:
                    raise ValueError("Generated arrest trajectories are not supported by this action engine.")
            elif key == "visual":
                if not isinstance(value, dict) or any(not isinstance(v, str) and not (k == "mottling" and isinstance(v, bool)) for k, v in value.items()):
                    raise ValueError("Visual findings must be descriptions with an optional mottling flag.")
            elif not isinstance(value, str) or not value.strip():
                raise ValueError("Observation findings must be nonempty descriptions.")
        if values.get("ecg_profile") is not None and values["ecg_profile"] not in PROFILES:
            raise ValueError("An observation rule selected an unsupported ECG morphology.")
        if not isinstance(rule.get("examination", {}), dict) or any(not isinstance(v, str) for v in rule.get("examination", {}).values()):
            raise ValueError("Examination updates must be authored descriptions.")
    studies = case.get("investigations", {})
    if not isinstance(studies, dict):
        raise ValueError("Investigations must be a dictionary.")
    for study in studies.values():
        if not isinstance(study, dict) or not isinstance(study.get("result"), dict):
            raise ValueError("Every supported investigation needs an explicit result.")
        delay = study.get("duration_min", 0)
        if not _finite(delay) or not 0 <= delay <= 120 or int(delay) != delay:
            raise ValueError("Investigation processing times must be supported whole minutes.")
        diagnostic_bindings(case, study)


def diagnostic_bindings(case, study):
    """Derive every modeled measurement binding; validate its initial value.

    Binding omission cannot turn a dynamic laboratory value into a constant.
    The function is pure so older frozen generated specs stay immutable during
    replay. Compilation saves the same derived mapping explicitly in new specs.
    Nonmodeled measurements remain case-authored values, never inferred normal.
    """
    results = study.get("result", {})
    declared = study.get("result_bindings", {})
    if not isinstance(results, dict) or not isinstance(declared, dict):
        raise ValueError("Investigation measurements and bindings must be dictionaries.")
    baseline = {key: value for key, value in case.get("observable", {}).items() if key in OBSERVED_FIELDS}
    baseline.update(case.get("engine", {}).get("initial_labs", {}))
    def source(field):
        return "pco2_mm_hg" if field == "paco2_mm_hg" else field
    for field, target in declared.items():
        if field not in results or source(field) not in NUMERIC_FIELDS or target != source(field):
            raise ValueError("A diagnostic binding cannot substitute a different measurement.")
    bindings = {}
    for field, measured in results.items():
        target = source(field)
        if target not in NUMERIC_FIELDS:
            continue
        if target not in baseline or not _finite(measured) or not _finite(baseline[target]):
            raise ValueError("Every modeled diagnostic needs a numerical initial physiological value.")
        if abs(measured - baseline[target]) > .11:
            raise ValueError("Initial results conflict with the initial physiology.")
        bindings[field] = target
    return bindings


def _validate_response_capability(case, rule):
    """Every authored effect must be reachable through an actually executable order."""
    from family_parser import _AGENTS
    kind = rule["action_type"]
    if kind in _DRUGS:
        supported = set(_AGENTS.get(kind, {})) or {kind}
        if str(rule.get("agent", "")).strip().lower() not in supported:
            raise ValueError("A generated treatment names an agent unavailable to the order interpreter.")
    normalized, error = _response_capability_probe(case, rule)
    if error or not normalized or not _matches(rule, normalized[0]):
        raise ValueError("A generated treatment rule cannot be reached by a supported order with those dose units, route or device.")


def _response_capability_probe(case, rule):
    """Return order validation only; never execute an order or change the case.

    The same probe supports private authoring diagnostics, so the correction
    request can describe actual normalized matchers rather than guess them.
    """
    kind = rule["action_type"]
    action = {"type": kind}
    field = rule.get("dose_field")
    if field:
        action[field] = rule["reference_dose"]
    if kind in _DRUGS - {"norepinephrine", "nitroglycerin"}:
        action["route"] = rule.get("route")
        if kind != "dextrose":  # The live dextrose parser emits a class and grams.
            action["agent"] = rule.get("agent")
    if kind == "anticoagulation":
        action["units"] = rule.get("units")
    elif kind == "fluid":
        action["fluid_type"] = "normal saline"
    elif kind == "oxygen":
        action["device"] = rule.get("device")
    elif kind == "niv":
        action.update(operation="start", mode="BiPAP", ipap_cmh2o=10, epap_cmh2o=5, fio2_percent=50)
    elif kind == "intubation":
        action.update(ventilator_mode="VC/AC", fio2_percent=50, peep_cmh2o=5)
    elif kind in {"nitroglycerin", "norepinephrine"}:
        action["operation"] = "start"
        if kind == "norepinephrine":
            action["units"] = rule.get("units")
    check_state = {"encounter_spec": {"clinical_case": case}, "observable": deepcopy(case["observable"])}
    return _validate_orders(check_state, {"actions": [action]})


def _initialize(state):
    _initialize_orders(state)
    if state.get("generated_state", {}).get("version") == 1:
        return
    case = _case(state)
    values = {key: float(case["observable"][key]) for key in OBSERVED_FIELDS}
    values.update({key: float(value) for key, value in case["engine"].get("initial_labs", {}).items()})
    state["generated_state"] = {
        "version": 1, "elapsed": 0, "baseline_values": deepcopy(values), "values": values,
        "events": [], "exposure": {}, "examination": deepcopy(case.get("examination", {})),
    }
    _surface(state)


def _action_agent(action):
    return str(action.get("agent") or action.get("type") or "").strip().lower()


def _matches(rule, action):
    if rule["action_type"] != action["type"]:
        return False
    if rule.get("agent") and rule["agent"].strip().lower() != _action_agent(action):
        return False
    if rule.get("route"):
        route = action.get("route") or ("IV" if action["type"] in {"norepinephrine", "nitroglycerin"} else None)
        if str(route).lower() != rule["route"].lower():
            return False
    if rule.get("units"):
        if action["type"] == "blood":
            unit = "units"
        else:
            unit = action.get("units")
        if not unit:
            unit = {"dose_mg": "mg", "dose_g": "g", "volume_ml": "mL", "flow_lpm": "L/min", "rate_mcg_min": "mcg/min"}.get(_DOSE_FIELDS.get(action["type"]))
        if unit != rule["units"]:
            return False
    return not rule.get("device") or str(action.get("device", "")).lower() == rule["device"].lower()


def _stopping(action):
    return action.get("operation") == "stop" or (action["type"] == "oxygen" and action.get("device") == "Room air")


def _record_effect(state, action, matching, summary):
    g = state["generated_state"]
    kind = action["type"]
    if kind in _ACTIVE:
        replace = _RESPIRATORY if kind in _RESPIRATORY else {kind}
        g["events"] = [event for event in g["events"] if event["action_type"] not in replace]
    if _stopping(action):
        return
    for rule in matching:
        exposure = float(action[rule["dose_field"]]) / rule["reference_dose"] if rule.get("dose_field") else 1.0
        consumed = 0 if kind in _ACTIVE else g["exposure"].get(rule["id"], 0)
        exposure = min(exposure, max(0, rule["max_exposure"] - consumed))
        if exposure <= 0:
            continue
        if kind not in _ACTIVE:
            g["exposure"][rule["id"]] = consumed + exposure
        duration = rule["duration_min"]
        if kind in {"fluid", "blood", "dextrose"}:
            duration = max(duration, summary["duration_min"])
        delivery_queue = 0
        if kind == "fluid":
            delivery_queue = max(0, state["family_state"]["pending_fluid_ml"] - action["volume_ml"]) / 50
        elif kind == "blood":
            delivery_queue = max(0, state["family_state"]["pending_blood_units"] - action["units"]) * 30
        g["events"].append({
            "rule_id": rule["id"], "action_type": kind, "started_at": g["elapsed"] + delivery_queue,
            "onset_min": rule["onset_min"], "duration_min": duration,
            "exposure": exposure, "delta": deepcopy(rule["delta"]),
        })


def _surface(state):
    case = _case(state)
    engine, g, f = case["engine"], state["generated_state"], state["family_state"]
    values = {key: number + g["elapsed"] * engine.get("untreated_drift_per_min", {}).get(key, 0) for key, number in g["baseline_values"].items()}
    for event in g["events"]:
        progress = min(1.0, max(0.0, (g["elapsed"] - event["started_at"] - event["onset_min"]) / event["duration_min"]))
        for key, delta in event["delta"].items():
            if key in values:
                values[key] += delta * event["exposure"] * progress
    for key, number in values.items():
        if not _finite(number) or not BOUNDS[key][0] <= number <= BOUNDS[key][1]:
            raise ValueError("The combined interventions exceed this generated trajectory's supported physiology.")
    if values["dbp"] >= values["sbp"]:
        raise ValueError("The combined interventions exceed this generated trajectory's blood-pressure model.")
    g["values"] = values
    observed = state.setdefault("observable", {})
    baseline = case["observable"]
    for key in _SET_FIELDS - {"ecg_profile", "visual"}:
        if key in baseline:
            observed[key] = deepcopy(baseline[key])
    observed.pop("visual", None)
    if isinstance(baseline.get("visual"), dict):
        observed["visual"] = deepcopy(baseline["visual"])
    state["ecg_profile"] = case.get("ecg_profile", state.get("encounter_spec", {}).get("ecg_profile", "baseline"))
    for key in OBSERVED_FIELDS:
        observed[key] = round(values[key], 1) if key in {"crt", "temperature_c"} else int(round(values[key]))
    observed["map"] = int(round((observed["sbp"] + 2 * observed["dbp"]) / 3))
    g["examination"] = deepcopy(case.get("examination", {}))
    for rule in engine.get("state_rules", []):
        if all(_COMPARATORS[c["operator"]](values[c["field"]], c["value"]) for c in rule["when"]):
            for key, value in rule.get("set", {}).items():
                if key == "ecg_profile":
                    state["ecg_profile"] = value
                elif key == "visual":
                    observed.setdefault("visual", {}).update(deepcopy(value))
                else:
                    observed[key] = deepcopy(value)
            g["examination"].update(deepcopy(rule.get("examination", {})))
    if f["invasive"]:
        observed["respiratory_support"] = "Invasive ventilation"
        observed["work_of_breathing"] = "Ventilator-supported"
    elif f["niv"]:
        observed["respiratory_support"] = "NIV"
    elif f["bag_mask"]:
        observed["respiratory_support"] = "Bag-mask ventilation"
    else:
        observed["respiratory_support"] = f["oxygen_device"]
    # Do not fabricate a physiological oxygen-delivery, lactate or diagnosis score.
    state.setdefault("hidden", {})["terminal_collapse"] = observed.get("pulse_present") is False


def _minute(state):
    g, f, tr = state["generated_state"], state["family_state"], state["treatments"]
    g["elapsed"] += 1
    f["elapsed"] += 1
    fluid, blood = min(50, f["pending_fluid_ml"]), min(1 / 30, f["pending_blood_units"])
    f["pending_fluid_ml"] = max(0, f["pending_fluid_ml"] - fluid)
    f["pending_blood_units"] = max(0, f["pending_blood_units"] - blood)
    f["fluid_delivered_ml"] += fluid
    f["blood_delivered_units"] += blood
    tr["total_crystalloid_ml"] = tr["cumulative_crystalloid_ml"] = round(f["fluid_delivered_ml"], 1)
    tr["packed_red_cells_units"] = round(f["blood_delivered_units"], 3)
    state["sim_time"] = int(state.get("sim_time", 0)) + 1
    _surface(state)


def _collect_diagnostic(state, diagnostic, duration):
    if diagnostic == "ecg":
        from ecg12 import acquire_ecg
        result = acquire_ecg(deepcopy(state))
    else:
        study = _case(state)["investigations"][diagnostic]
        result = deepcopy(study["result"])
        bindings = diagnostic_bindings(_case(state), study)
        for field, source in bindings.items():
            result[field] = round(state["generated_state"]["values"][source], 2)
        if bindings:
            # A baseline sentence containing laboratory numbers cannot remain
            # alongside freshly sampled values after treatment.
            result.pop("report", None)
        if "bicarbonate_mmol_l" in result and ("pco2_mm_hg" in result or "paco2_mm_hg" in result):
            co2 = result.get("pco2_mm_hg", result.get("paco2_mm_hg"))
            if _finite(co2) and co2 > 0 and _finite(result["bicarbonate_mmol_l"]) and result["bicarbonate_mmol_l"] > 0:
                result["ph"] = round(6.1 + math.log10(result["bicarbonate_mmol_l"] / (.03 * co2)), 2)
        result["time_min"] = int(state.get("sim_time", 0))
    return {"type": "diagnostic", "diagnostic_type": diagnostic, "result": result, "duration_min": duration}


def execute_generated_bundle(state, parsed):
    """Atomically execute validated supported orders against an immutable case spec."""
    if state.get("engine_family") != "generated":
        return _failure("This encounter does not have a generated clinical trajectory.")
    try:
        validate_declarative_case(_case(state))
    except (ValueError, TypeError, KeyError) as error:
        return _failure("The generated trajectory could not be validated: " + str(error))
    actions, error = _validate_orders(state, parsed)
    if error:
        return _failure(error)
    rules = _case(state)["engine"]["response_rules"]
    matching = []
    for action in actions:
        selected = [rule for rule in rules if _matches(rule, action)]
        if action["type"] not in _ADMIN | {"diagnostic", "reassessment"} and not selected and not _stopping(action):
            details = [str(action.get("agent") or action["type"]).replace("_", " ")]
            field = _DOSE_FIELDS.get(action["type"])
            if field and action.get(field) is not None:
                units = action.get("units") or {"volume_ml": "mL", "flow_lpm": "L/min", "dose_mg": "mg", "dose_g": "g", "rate_mcg_min": "mcg/min"}.get(field, field)
                details.append(f"{action[field]:g} {units}")
            details.extend(str(action[key]) for key in ("route", "device") if action.get(key))
            return _failure("Order understood: " + ", ".join(details) + ". This generated case has no modeled response for this intervention. Rewording the order will not resolve this case limitation. No orders in this submission were executed.")
        matching.append(selected)
    candidate = deepcopy(state)
    _initialize(candidate)
    summaries, pending = [], []
    collection_state = deepcopy(candidate)
    reassess = None
    for action, selected in zip(actions, matching):
        if action["type"] == "reassessment":
            reassess = action["delay_min"]
        elif action["type"] == "diagnostic":
            delay = 1 if action["diagnostic"] == "ecg" else _case(candidate)["investigations"][action["diagnostic"]].get("duration_min", 0)
            pending.append((delay, _collect_diagnostic(collection_state, action["diagnostic"], delay)))
        else:
            summary = _order(candidate, action)
            _record_effect(candidate, action, selected, summary)
            summaries.append(summary)
    elapsed = max(max((delay for delay, _ in pending), default=0), reassess if reassess is not None else max((s["duration_min"] for s in summaries), default=0))
    if candidate["generated_state"]["elapsed"] + elapsed > _case(candidate)["engine"].get("horizon_min", 180):
        return _failure("This order extends beyond the generated scenario's supported time horizon. Please choose a shorter reassessment interval or finish the encounter.")
    due = {}
    for delay, summary in pending:
        due.setdefault(delay, []).append(summary)
    for summary in due.get(0, []):
        summaries.append(_release_diagnostic(candidate, summary, candidate.get("sim_time", 0)))
    try:
        for minute in range(1, elapsed + 1):
            _minute(candidate)
            for summary in due.get(minute, []):
                summaries.append(_release_diagnostic(candidate, summary, candidate["sim_time"]))
        _surface(candidate)
    except ValueError as error:
        return _failure(str(error) + " No orders in this submission were executed.")
    state.clear()
    state.update(candidate)
    return {"executed": True, "clarification": None, "action_summaries": summaries, "reassess_delay": reassess, "elapsed_min": elapsed}


def _current_examination_overrides(state):
    """Identify descriptions explicitly authored for the current physiological state."""
    values = state.get("generated_state", {}).get("values", {})
    overrides = {}
    for rule in _case(state).get("engine", {}).get("state_rules", []):
        conditions = rule.get("when", [])
        if conditions and all(c.get("field") in values and c.get("operator") in _COMPARATORS
                              and _COMPARATORS[c["operator"]](values[c["field"]], c["value"])
                              for c in conditions):
            overrides.update(deepcopy(rule.get("examination", {})))
    return overrides


def _examination_source_changed(state, fields):
    """Qualify an unchanged arrival description when related observations evolve."""
    baseline = _case(state).get("observable", {})
    observed = state.get("observable", {})
    for field in fields:
        if field == "visual":
            if baseline.get("visual", {}) != observed.get("visual", {}):
                return True
        elif field in observed and observed[field] != baseline.get(field, "Room air" if field == "respiratory_support" else None):
            return True
    return False


def current_findings(state):
    """Preserve focal examination facts alongside current measured observations.

    Evolved descriptions come from explicit state rules. An unchanged baseline
    description is labeled as an arrival finding if its related observations
    have changed; it is never silently deleted or presented as a new exam.
    """
    observed = state.get("observable", {})
    findings = deepcopy(state.get("generated_state", {}).get("examination", _case(state).get("examination", {})))
    overrides = _current_examination_overrides(state)
    findings.update(overrides)
    visual = observed.get("visual", {})
    visible = []
    for key, label in (("skin_color", "skin"), ("expression", "expression"), ("diaphoresis", "diaphoresis")):
        if visual.get(key):
            visible.append(f"{label}: {visual[key]}")
    if isinstance(visual.get("mottling"), bool):
        visible.append("mottling present" if visual["mottling"] else "no visible mottling")
    supplements = {
        "General appearance": (f"{observed.get('mental_status', 'Not recorded')}. Respiratory effort: {observed.get('work_of_breathing', 'Not recorded')}."
                               + (" Visible findings: " + "; ".join(visible) + "." if visible else "")),
        "Peripheral perfusion": (f"Capillary refill {observed.get('crt', 'not recorded')} s; extremities {str(observed.get('extremities', 'not recorded')).lower()}; "
                                 f"peripheral perfusion {observed.get('peripheral_perfusion', 'not recorded')}."),
        "Neurological": f"Mental status: {observed.get('mental_status', 'not recorded')}.",
        "Respiratory": (f"Respiratory rate {observed.get('respiratory_rate', 'not recorded')}/min; "
                        f"effort {str(observed.get('work_of_breathing', 'not recorded')).lower()}; "
                        f"support {observed.get('respiratory_support', 'not recorded')}."),
        "Cardiac": (f"Heart rate {observed.get('hr', 'not recorded')}/min; rhythm {observed.get('rhythm', 'not recorded')}; "
                    f"BP {observed.get('sbp', 'not recorded')}/{observed.get('dbp', 'not recorded')} mmHg."),
    }
    related_fields = {
        "General appearance": ("mental_status", "work_of_breathing", "visual"),
        "Peripheral perfusion": ("crt", "extremities", "peripheral_perfusion", "visual"),
        "Neurological": ("mental_status",),
        "Respiratory": ("respiratory_rate", "work_of_breathing", "respiratory_support"),
        "Cardiac": ("hr", "rhythm", "sbp", "dbp"),
    }
    for area, supplement in supplements.items():
        authored = findings.get(area, "")
        prefix = ""
        if authored:
            source_label = "At arrival" if area not in overrides and _examination_source_changed(state, related_fields[area]) else "Examination"
            prefix = f"{source_label}: {authored}\n"
        findings[area] = prefix + "Current observations: " + supplement
    return findings


def clinical_update(state):
    """Brief public state update; no unmeasured labs or hidden diagnosis."""
    observed = state.get("observable", {})
    return (f"BP {observed.get('sbp')}/{observed.get('dbp')} mmHg · HR {observed.get('hr')}/min · "
            f"SpO₂ {observed.get('spo2')}% · RR {observed.get('respiratory_rate')}/min. "
            f"{observed.get('mental_status', 'Not recorded')}; respiratory effort "
            f"{str(observed.get('work_of_breathing', 'not recorded')).lower()}; "
            f"capillary refill {observed.get('crt')} s.")
