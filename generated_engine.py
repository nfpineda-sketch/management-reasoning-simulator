"""Execute AI-authored *data*, never AI-authored code, as a bounded simulation.

Case declarations are validated before any order. Numeric trajectories use only
elapsed simulation time and explicitly administered exposure. Learner reasoning,
bias labels, grades and post-hoc reflections cannot affect physiology. This is a
teaching model requiring clinical review, not a clinical prediction engine.
"""
from clinical_core_defaults import CORE_VERSION
from copy import deepcopy
import math
import generated_physiology as physiology
from clinical_physiology import exposure_effect
from generated_response import response_progress, select_responses, diagnostic_overrides
from generated_dynamics import INFUSIONS, event_progress, gain_at, retire_active_events
from generated_rhythm import rhythm_key, select_cardioversion, advance_recurrence

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
_ACTIVE = frozenset({"oxygen", "niv", "bag_mask", "intubation", "ventilator_adjustment", "norepinephrine", "dobutamine", "nitroglycerin"})
_RESPIRATORY = frozenset({"oxygen", "niv", "bag_mask", "intubation", "ventilator_adjustment"})
_ADMIN = frozenset({"consult", "reperfusion_referral", "disposition", "airway_preparation"})
_DOSE_FIELDS = {
    "beta_blocker": "dose_mg", "diltiazem": "dose_mg", "amiodarone": "dose_mg", "procedural_sedation": "dose_mg", "fluid": "volume_ml", "blood": "units", "dextrose": "dose_g", "naloxone": "dose_mg",
    "antibiotics": "dose_mg", "bronchodilator": "dose_mg", "steroid": "dose_mg",
    "ppi": "dose_mg", "aspirin": "dose_mg", "diuretic": "dose_mg", "anticoagulation": "dose",
    "nitroglycerin": "rate_mcg_min", "norepinephrine": "rate", "dobutamine": "rate", "oxygen": "flow_lpm",
}
_DRUGS = frozenset({"beta_blocker", "diltiazem", "amiodarone", "procedural_sedation", "dextrose", "naloxone", "antibiotics", "bronchodilator", "steroid", "ppi", "aspirin", "diuretic", "anticoagulation", "nitroglycerin", "norepinephrine", "dobutamine"})
_ACTIONS = frozenset(_DOSE_FIELDS) | _ACTIVE | {"cardioversion"}
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
    if engine.get("core_profile") is not None:
        from coupled_encounter import validate_profile
        validate_profile(engine["core_profile"])
    if engine.get("model") not in {MODEL, CORE_VERSION} or (engine.get("model") == CORE_VERSION and not engine.get("core_profile")):
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
    physiology.validate(engine, initialized)
    driver_fields = initialized | (physiology.VOLUME_FIELDS if engine.get("volume_model") else set())
    drift = engine.get("untreated_drift_per_min", {})
    _number_map(drift, "untreated_drift_per_min")
    if any(value and key not in initialized for key, value in drift.items()):
        raise ValueError("A drifting laboratory field needs an initial value.")
    horizon = engine.get("horizon_min", 180)
    if not _finite(horizon) or not 1 <= horizon <= 240 or int(horizon) != horizon:
        raise ValueError("The generated trajectory needs a finite supported time horizon.")
    rules = engine.get("response_rules")
    if not isinstance(rules, list) or not (0 if engine.get("core_profile") else 1) <= len(rules) <= 64:
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
        if kind in {"norepinephrine", "dobutamine", "anticoagulation"} and not rule.get("units"):
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
        if rule.get("recovery_min") is not None:
            if kind not in _DRUGS - INFUSIONS or not _finite(rule["recovery_min"]) or not 1 <= rule["recovery_min"] <= 180:
                raise ValueError("Only fixed-dose medications may define a finite recovery interval.")
        if rule.get("mental_status_during") is not None:
            if kind != "procedural_sedation" or rule["mental_status_during"] != "Sedated" or rule.get("recovery_min") is None or not _finite(rule.get("mental_status_threshold")) or not 0 < rule["mental_status_threshold"] <= rule["max_exposure"]:
                raise ValueError("Sedation requires an explicit recovery interval and exposure threshold.")
        if rule.get("interpolate_settings") not in (None, False, True) or (rule.get("interpolate_settings") and kind != "ventilator_adjustment"):
            raise ValueError("Interpolation is restricted to authored ventilator grids.")
        if rule.get("washout_min") is not None and (kind not in INFUSIONS or not _finite(rule["washout_min"]) or not 1 <= rule["washout_min"] <= 180):
            raise ValueError("Infusion washout must be between 1 and 180 minutes.")
        curve = rule.get("state_gain")
        if curve is not None:
            if not isinstance(curve, dict) or curve.get("field") not in driver_fields | {"elapsed_min", "fluid_delivered_ml"}:
                raise ValueError("State coupling must read a declared measurement, elapsed time or delivered fluid.")
            points = curve.get("points")
            if not isinstance(points, list) or not 2 <= len(points) <= 8 or any(not isinstance(p,dict) or not _finite(p.get("value")) or not _finite(p.get("factor")) or not 0 <= p["factor"] <= 1 for p in points):
                raise ValueError("State coupling needs 2–8 finite points with factors between zero and one.")
            if any(a["value"] >= b["value"] for a,b in zip(points,points[1:])):
                raise ValueError("State coupling points must be strictly increasing.")
        _validate_procedure_rule(rule)
        recurrence = rule.get("recurrence")
        if recurrence:
            _number_map(recurrence.get("delta"), "recurrence delta")
            if any(value and key not in initialized for key,value in recurrence["delta"].items()):
                raise ValueError("Recurrence effects require initialized numeric fields.")
            for condition in recurrence["when"]:
                if not isinstance(condition,dict) or condition.get("field") not in driver_fields | {"elapsed_min","fluid_delivered_ml"} or condition.get("operator") not in _COMPARATORS or not _finite(condition.get("value")):
                    raise ValueError("Recurrence must depend on declared numerical conditions.")
        _validate_response_capability(case, rule)
        _number_map(rule.get("delta"), "response delta")
        if any(value and key not in initialized for key, value in rule["delta"].items()):
            raise ValueError("A treatment-responsive laboratory field needs an initial value.")
    initial_values = {key: observed[key] for key in OBSERVED_FIELDS}
    initial_values.update(initial_labs)
    physiology.validate_extremes(engine, initial_values, BOUNDS)
    # The data contract must remain executable through its authored horizon.
    # Check the untreated path and each isolated maximum-exposure response at
    # all breakpoints; combinations are checked atomically when ordered.
    recurrence_responses = [{**r, "delta": r["recurrence"]["delta"], "state_gain": None} for r in rules if r.get("recurrence")]
    for response in [None] + rules + recurrence_responses:
        times = {0, horizon}
        if response is not None:
            times.update({min(horizon, response["onset_min"]), min(horizon, response["onset_min"] + response["duration_min"])})
        if response is not None and response.get("recovery_min") is not None:
            times.add(min(horizon, response["onset_min"] + response["duration_min"] + response["recovery_min"]))
        for at in times:
            values = {key: number + at * drift.get(key, 0) for key, number in initial_values.items()}
            if response is not None:
                progress = response_progress(at, response["onset_min"], response["duration_min"], response.get("recovery_min"), response["action_type"] == "cardioversion")
                for key, delta in response["delta"].items():
                    if key in values:
                        values[key] += delta * exposure_effect(response["max_exposure"], response.get("exposure_curve")) * progress
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
            if not isinstance(condition, dict) or condition.get("field") not in driver_fields | {"elapsed_min", "fluid_delivered_ml"} or condition.get("operator") not in _COMPARATORS or not _finite(condition.get("value")):
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
    for rule in state_rules:
        updates = rule.get("diagnostic_updates") or {}
        if not isinstance(updates, dict) or set(updates) - set(case.get("investigations",{})):
            raise ValueError("Diagnostic updates must refer to available investigations.")
        for study, fields in updates.items():
            if not isinstance(fields, dict) or set(fields) - {"lv","rv","lungs","ivc","pericardium","report"} or any(not isinstance(v,str) or not v.strip() for v in fields.values()):
                raise ValueError("Diagnostic updates may change only explicit narrative findings, not numeric measurements.")
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


def _validate_procedure_rule(rule):
    from ecg12 import RHYTHMS
    kind = rule["action_type"]
    settings = rule.get("settings") or {}
    allowed = {"energy_j"} if kind == "cardioversion" else {"fio2_percent", "peep_cmh2o"} if kind == "ventilator_adjustment" else set()
    if not isinstance(settings, dict) or set(settings) - allowed or any(not _finite(v) for v in settings.values()):
        raise ValueError("Unsupported intervention-specific response settings.")
    if kind == "cardioversion" and (set(settings) != {"energy_j"} or not 1 <= settings["energy_j"] <= 360 or rule.get("onset_min") != 0):
        raise ValueError("Cardioversion responses require explicit energy_j and immediate onset.")
    if kind == "ventilator_adjustment" and set(settings) != {"fio2_percent", "peep_cmh2o"}:
        raise ValueError("Ventilator responses require explicit FiO2 and PEEP settings.")
    before = rule.get("rhythm_before")
    if before is not None and (kind != "cardioversion" or before not in RHYTHMS or RHYTHMS[before] in {"vf", "asystole"}):
        raise ValueError("Pre-shock rhythm must be a supported pulse-present rhythm.")
    recurrence = rule.get("recurrence")
    if recurrence is not None:
        if kind != "cardioversion" or not isinstance(recurrence,dict) or not _finite(recurrence.get("after_min")) or not 1 <= recurrence["after_min"] <= 180 or not isinstance(recurrence.get("when"),list) or len(recurrence["when"]) > 6:
            raise ValueError("Recurrence needs a cardioversion, a finite delay and at most six conditions.")
        if recurrence.get("rhythm_after") not in RHYTHMS or RHYTHMS[recurrence["rhythm_after"]] in {"vf", "asystole"} or not rule.get("rhythm_after") or rhythm_key(recurrence["rhythm_after"]) == rhythm_key(rule["rhythm_after"]):
            raise ValueError("Recurrence must specify a different supported rhythm.")
        if before is not None and rhythm_key(before) == rhythm_key(rule.get("rhythm_after")):
            raise ValueError("An unsuccessful shock cannot schedule post-conversion recurrence.")
    rhythm = rule.get("rhythm_after")
    if rhythm is not None and (kind != "cardioversion" or rhythm not in RHYTHMS or RHYTHMS[rhythm] in {"vf", "asystole"}):
        raise ValueError("Only pulse-present cardioversion may declare a post-procedure rhythm.")


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
    action = {"type": kind, **(rule.get("settings") or {})}
    field = rule.get("dose_field")
    if field:
        action[field] = rule["reference_dose"]
    if kind in _DRUGS - {"norepinephrine", "dobutamine", "nitroglycerin"}:
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
    elif kind in {"intubation", "ventilator_adjustment"}:
        action.update(ventilator_mode="VC/AC", fio2_percent=50, peep_cmh2o=5)
    elif kind in {"nitroglycerin", "norepinephrine", "dobutamine"}:
        action["operation"] = "start"
        if kind in {"norepinephrine", "dobutamine"}:
            action["units"] = rule.get("units")
    action.update(rule.get("settings") or {})
    if kind == "cardioversion":
        action.update(synchronized=True)
    check_state = {"engine_family": "generated", "encounter_spec": {"clinical_case": case}, "observable": {"pulse_present": True, **deepcopy(case["observable"])},
                   "treatments": {"invasive_ventilation": kind == "ventilator_adjustment"}}
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
    physiology.initialize(state)
    _surface(state)


def _action_agent(action):
    return str(action.get("agent") or action.get("type") or "").strip().lower()


def _matches(rule, action):
    if any(action.get(key) != value for key, value in (rule.get("settings") or {}).items()):
        return False
    if rule["action_type"] != action["type"]:
        return False
    if rule.get("agent") and rule["agent"].strip().lower() != _action_agent(action):
        return False
    if rule.get("route"):
        route = action.get("route") or ("IV" if action["type"] in {"norepinephrine", "dobutamine", "nitroglycerin"} else None)
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
    signature = {k:v for k,v in action.items() if k != "operation"}
    signatures = g.setdefault("active_signatures", {})
    if kind in INFUSIONS and _stopping(action) and kind in signatures and signatures[kind] is None:
        return
    if kind in INFUSIONS and not _stopping(action) and signatures.get(kind) == signature:
        return
    if kind in INFUSIONS:
        signatures[kind] = None if _stopping(action) else signature
    converting = kind == "cardioversion" and any(r.get("rhythm_after") and rhythm_key(r["rhythm_after"]) != rhythm_key(state["observable"].get("rhythm")) for r in matching)
    if converting:
        # A new conversion replaces its previous rhythm-related benefit, while
        # retaining separately authored adverse effects and other therapies.
        g["events"] = [e for e in g["events"] if not e.get("conversion_effect", e.get("action_type") == "cardioversion" and bool(e.get("rhythm_after")))]
    previous = {e["rule_id"]: e for e in g["events"] if e["action_type"] == kind}
    if kind in _ACTIVE:
        replace = _RESPIRATORY if kind in _RESPIRATORY else {kind}
        retiring = [event for event in g["events"] if event["action_type"] in replace]
        g["events"] = [event for event in g["events"] if event["action_type"] not in replace]
        if kind in INFUSIONS:
            transition = None if _stopping(action) else max((r["onset_min"] + r["duration_min"] for r in matching if r.get("washout_min")), default=None)
            g["events"].extend(retire_active_events(retiring, g["elapsed"], transition))
    if _stopping(action):
        return
    for rule in matching:
        exposure = float(action[rule["dose_field"]]) / rule["reference_dose"] if rule.get("dose_field") else 1.0
        exposure *= rule.get("_interpolation_weight", 1.0)
        consumed = 0 if kind in _ACTIVE or converting or rule.get("recovery_min") is not None else g["exposure"].get(rule["id"], 0)
        exposure = min(exposure, max(0, rule["max_exposure"] - consumed))
        if exposure <= 0:
            continue
        if kind not in _ACTIVE:
            g["exposure"][rule["id"]] = consumed + exposure
        duration = rule["duration_min"]
        if kind in {"fluid", "blood", "dextrose"} or action.get("administration_duration_min") is not None:
            duration = max(duration, summary["duration_min"])
        delivery_queue = 0
        if kind == "fluid":
            delivery_queue = max(0, state["family_state"]["pending_fluid_ml"] - action["volume_ml"]) / 50
        elif kind == "blood":
            delivery_queue = max(0, state["family_state"]["pending_blood_units"] - action["units"]) * 30
        if summary.get("delivery_starts_at_min") is not None:
            delivery_queue = summary["delivery_starts_at_min"] - g["elapsed"]
        g["events"].append({
            "rule_id": rule["id"], "action_type": kind, "started_at": g["elapsed"] + delivery_queue,
            "onset_min": rule["onset_min"], "duration_min": duration,
            "immediate": kind == "cardioversion", "rhythm_after": rule.get("rhythm_after") if converting else None,
            "recovery_min": rule.get("recovery_min"), "mental_status_during": rule.get("mental_status_during"), "mental_status_threshold": rule.get("mental_status_threshold"),
            "exposure": exposure, "delta": deepcopy(rule["delta"]),
            "conversion_effect": converting, "recurrence": deepcopy(rule.get("recurrence")),
            "washout_min": rule.get("washout_min"), "state_gain": deepcopy(rule.get("state_gain")),
        })
        if kind in INFUSIONS and previous and rule.get("washout_min"):
            # Blend the previous effect into the new target over one interval.
            # A delayed target must not create an artificial dip while increasing.
            g["events"][-1]["duration_min"] += rule["onset_min"]
            g["events"][-1]["onset_min"] = 0
        if kind in _ACTIVE and rule["id"] in previous and not rule.get("washout_min"):
            g["events"][-1]["started_at"] = previous[rule["id"]]["started_at"]


def _surface(state):
    if state.get("hidden", {}).get("terminal_collapse"):
        return
    physiology.initialize(state)
    case = _case(state)
    engine, g, f = case["engine"], state["generated_state"], state["family_state"]
    values = {key: number + g["elapsed"] * engine.get("untreated_drift_per_min", {}).get(key, 0) for key, number in g["baseline_values"].items()}
    # One unmodified snapshot for all response curves prevents circular feedback
    # and makes repeated rendering at the same minute idempotent.
    drivers = {**values, **physiology.drivers(state)}
    coupled_ids = {r["id"] for r in engine["response_rules"] if r.get("volume_basis") or r.get("exposure_curve")}
    for event in g["events"]:
        if event["rule_id"] in coupled_ids:
            continue
        progress = event_progress(event, g["elapsed"])
        for key, delta in event["delta"].items():
            if key in drivers:
                drivers[key] += delta * event["exposure"] * progress
    for key, delta in physiology.contributions(state, engine["response_rules"], drivers, apply_gain=False).items():
        drivers[key] += delta
    drivers.update(elapsed_min=g["elapsed"], fluid_delivered_ml=f["fluid_delivered_ml"])
    for event in g["events"]:
        if event["rule_id"] in coupled_ids:
            continue
        progress = event_progress(event, g["elapsed"]) * gain_at(event.get("state_gain"), drivers)
        for key, delta in event["delta"].items():
            if key in values:
                values[key] += delta * event["exposure"] * progress
    for key, delta in physiology.contributions(state, engine["response_rules"], drivers).items():
        if key in values:
            values[key] += delta
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
    for event in g["events"]:
        if event.get("rhythm_after") and event.get("immediate"):
            observed["rhythm"] = event["rhythm_after"]
    condition_values = {**values, **physiology.drivers(state), "elapsed_min": g["elapsed"], "fluid_delivered_ml": f["fluid_delivered_ml"]}
    for rule in engine.get("state_rules", []):
        if all(_COMPARATORS[c["operator"]](condition_values[c["field"]], c["value"]) for c in rule["when"]):
            for key, value in rule.get("set", {}).items():
                if key == "ecg_profile":
                    state["ecg_profile"] = value
                elif key == "visual":
                    observed.setdefault("visual", {}).update(deepcopy(value))
                else:
                    observed[key] = deepcopy(value)
            g["examination"].update(deepcopy(rule.get("examination", {})))
    sedating = [r for r in engine["response_rules"] if r.get("mental_status_during") and r.get("exposure_curve") and physiology.active_load(state,r) * gain_at(r.get("state_gain"),drivers) >= r["mental_status_threshold"]]
    sedating += [e for e in g["events"] if e["rule_id"] not in coupled_ids and e.get("mental_status_during") and e["exposure"] * gain_at(e.get("state_gain"), drivers) * event_progress(e, g["elapsed"]) >= e["mental_status_threshold"]]
    if sedating:
        # Do not describe an unresponsive patient as more awake due to sedation.
        if observed.get("mental_status") not in {"Unresponsive", "Obtunded"}:
            observed["mental_status"] = sedating[-1]["mental_status_during"]
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
    from generated_delivery import advance_deliveries
    if not advance_deliveries(state):
        fluid, blood = min(50, f["pending_fluid_ml"]), min(1 / 30, f["pending_blood_units"])
        f["pending_fluid_ml"] = max(0, f["pending_fluid_ml"] - fluid)
        f["pending_blood_units"] = max(0, f["pending_blood_units"] - blood)
        f["fluid_delivered_ml"] += fluid
        f["blood_delivered_units"] += blood
    tr["total_crystalloid_ml"] = tr["cumulative_crystalloid_ml"] = round(f["fluid_delivered_ml"], 1)
    tr["packed_red_cells_units"] = round(f["blood_delivered_units"], 3)
    state["sim_time"] = int(state.get("sim_time", 0)) + 1
    physiology.advance(state)
    _surface(state)
    if physiology.terminal_tick(state):
        return
    if advance_recurrence(state):
        _surface(state)


def _collect_diagnostic(state, diagnostic, duration):
    if diagnostic == "ecg":
        from ecg12 import acquire_ecg
        result = acquire_ecg(deepcopy(state))
    else:
        study = _case(state)["investigations"][diagnostic]
        result = deepcopy(study["result"])
        result.update(diagnostic_overrides(state, diagnostic))
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
        if diagnostic in {"abg", "vbg"}:
            # Snapshot support at sampling, never when the delayed result returns.
            fio2 = state["family_state"]["oxygen_fio2"]
            result["fio2_percent"] = round(fio2 * 100, 1)
            result.pop("pf_ratio", None)
            result.pop("report", None)
            if diagnostic == "abg" and _finite(result.get("pao2_mm_hg")):
                result["pf_ratio"] = round(result["pao2_mm_hg"] / fio2)
        result["time_min"] = int(state.get("sim_time", 0))
    return {"type": "diagnostic", "diagnostic_type": diagnostic, "result": result, "duration_min": duration}


def execute_generated_bundle(state, parsed):
    """Atomically execute validated supported orders against an immutable case spec."""
    from coupled_encounter import enabled, execute
    if enabled(_case(state)):
        return execute(state, parsed)
    if state.get("engine_family") != "generated":
        return _failure("This encounter does not have a generated clinical trajectory.")
    try:
        validate_declarative_case(_case(state))
    except (ValueError, TypeError, KeyError) as error:
        return _failure("The generated trajectory could not be validated: " + str(error))
    if state.get("hidden", {}).get("terminal_collapse"):
        return _failure("The patient has no pulse. This encounter has reached its terminal state; resuscitation actions are not executable in this build.")
    actions, error = _validate_orders(state, parsed)
    if error:
        return _failure(error)
    rules = _case(state)["engine"]["response_rules"]
    matching = []
    for action in actions:
        selected = select_responses(rules, action, _matches)
        if action["type"] not in _ADMIN | {"diagnostic", "reassessment"} and not selected and not _stopping(action):
            details = [str(action.get("agent") or action["type"]).replace("_", " ")]
            field = _DOSE_FIELDS.get(action["type"])
            if field and action.get(field) is not None:
                units = action.get("units") or {"volume_ml": "mL", "flow_lpm": "L/min", "dose_mg": "mg", "dose_g": "g", "rate_mcg_min": "mcg/min"}.get(field, field)
                details.append(f"{action[field]:g} {units}")
            details.extend(str(action[key]) for key in ("route", "device") if action.get(key))
            for key, label in (("energy_j", "J"), ("fio2_percent", "% FiO2"), ("peep_cmh2o", "cmH2O PEEP")):
                if action.get(key) is not None:
                    details.append(f"{action[key]:g} {label}")
            return _failure("Order understood: " + ", ".join(details) + ". This generated case has no modeled response for this intervention. Rewording the order will not resolve this case limitation. No orders in this submission were executed.")
        matching.append(selected)
    candidate = deepcopy(state)
    _initialize(candidate)
    summaries = []
    pending = candidate["generated_state"].setdefault("pending_diagnostics", [])
    reassess = None
    for action, selected in zip(actions, matching):
        if action["type"] == "reassessment":
            reassess = action["delay_min"]
        elif action["type"] == "diagnostic":
            delay = 1 if action["diagnostic"] == "ecg" else _case(candidate)["investigations"][action["diagnostic"]].get("duration_min", 0)
            pending.append({"available_at": candidate["sim_time"] + delay, "summary": _collect_diagnostic(candidate, action["diagnostic"], delay)})
        else:
            if action["type"] == "cardioversion":
                selected = select_cardioversion(candidate, selected)
                if not selected:
                    return _failure("Cardioversion understood, but this case has no unambiguous response for the current rhythm and requested energy. No orders in this submission were executed.")
                rhythm_before = candidate["observable"].get("rhythm")
            summary = _order(candidate, action)
            from generated_delivery import schedule_delivery
            schedule_delivery(candidate, action, summary)
            _record_effect(candidate, action, selected, summary)
            summaries.append(summary)
            try:
                _surface(candidate)
                if action["type"] == "cardioversion":
                    summary.update(rhythm_before=rhythm_before, rhythm_after=candidate["observable"].get("rhythm"))
                    candidate.setdefault("rhythm_history", []).append({"time_min":candidate["sim_time"], "kind":"cardioversion", "energy_j":action["energy_j"], "rhythm_before":rhythm_before, "rhythm_after":candidate["observable"].get("rhythm")})
            except ValueError as error:
                return _failure(str(error) + " No orders in this submission were executed.")
    elapsed = reassess if reassess is not None else max(max((item["available_at"] - candidate["sim_time"] for item in pending), default=0), max((s["duration_min"] for s in summaries), default=0))
    if candidate["generated_state"]["elapsed"] + elapsed > _case(candidate)["engine"].get("horizon_min", 180):
        return _failure("This order extends beyond the generated scenario's supported time horizon. Please choose a shorter reassessment interval or finish the encounter.")
    def release_ready():
        ready = [item for item in pending if item["available_at"] <= candidate["sim_time"]]
        for item in ready:
            summaries.append(_release_diagnostic(candidate, item["summary"], item["available_at"]))
            pending.remove(item)
    release_ready()
    try:
        for minute in range(1, elapsed + 1):
            _minute(candidate)
            release_ready()
            if candidate.get("hidden", {}).get("terminal_collapse"):
                elapsed = minute
                break
        _surface(candidate)
    except ValueError as error:
        return _failure(str(error) + " No orders in this submission were executed.")
    # Public waiting status contains no result, private case data or diagnosis.
    candidate["pending_investigations"] = [{"diagnostic_type": item["summary"]["diagnostic_type"], "available_at_min": item["available_at"], "collected_at_min": item["summary"]["result"].get("time_min", item["summary"]["result"].get("acquired_at_minutes", candidate["sim_time"]))} for item in pending]
    state.clear()
    state.update(candidate)
    return {"executed": True, "clarification": None, "action_summaries": summaries, "reassess_delay": reassess, "elapsed_min": elapsed}


def _current_examination_overrides(state):
    """Identify descriptions explicitly authored for the current physiological state."""
    values = dict(state.get("generated_state", {}).get("values", {}))
    values.update(physiology.drivers(state))
    values.update(elapsed_min=state.get("generated_state",{}).get("elapsed",0), fluid_delivered_ml=state.get("family_state",{}).get("fluid_delivered_ml",0))
    overrides = {}
    for rule in _case(state).get("engine", {}).get("state_rules", []):
        conditions = rule.get("when", [])
        if conditions and all(c.get("field") in values and c.get("operator") in _COMPARATORS
                              and _COMPARATORS[c["operator"]](values[c["field"]], c["value"])
                              for c in conditions):
            from coupled_encounter import enabled, examination_updates
            updates = examination_updates(rule, state.get("observable", {})) if enabled(_case(state)) else deepcopy(rule.get("examination", {}))
            overrides.update(updates)
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
    if observed.get("pulse_present") is False:
        supplements["Cardiac"] = f"No palpable pulse; organized electrical activity (PEA), electrical rate {observed.get('hr')}/min. Blood pressure unavailable."
        supplements["Peripheral perfusion"] = "No palpable pulse. Capillary refill cannot be assessed."
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
    if observed.get("pulse_present") is False:
        return "No palpable pulse; organized electrical activity (PEA). Unresponsive. Blood pressure, SpO₂ and capillary refill are unavailable."
    return (f"BP {observed.get('sbp')}/{observed.get('dbp')} mmHg · HR {observed.get('hr')}/min · "
            f"SpO₂ {observed.get('spo2')}% · RR {observed.get('respiratory_rate')}/min. "
            f"{observed.get('mental_status', 'Not recorded')}; respiratory effort "
            f"{str(observed.get('work_of_breathing', 'not recorded')).lower()}; "
            f"capillary refill {observed.get('crt')} s.")
