"""Private, data-only feedback for repairing an authored engine declaration.

These diagnostics do not accept a case or adjust its physiology. The existing
engine validator remains the execution gate. Paths, codes and messages are
static software descriptions; details belong only in the authoring request,
never in a learner-facing error or log.
"""
from generated_engine import (
    BOUNDS, MODEL, OBSERVED_FIELDS, LAB_FIELDS, NUMERIC_FIELDS, _ACTIONS,
    _DOSE_FIELDS, _DRUGS, _COMPARATORS, _SET_FIELDS, _finite,
    _validate_response_capability, _response_capability_probe, _action_agent,
)


ENGINE_ISSUE_CODES = frozenset({
    "ENGINE_MODEL", "BASELINE_OBSERVATIONS", "BASELINE_BOUNDS", "BASELINE_PRESSURE",
    "ARREST_UNSUPPORTED", "NUMERIC_FIELDS", "NUMERIC_VALUE", "NUMERIC_DELTA_RANGE",
    "LAB_INITIAL_VALUE", "HORIZON", "RESPONSE_RULES", "RESPONSE_IDENTIFIER",
    "RESPONSE_ACTION", "RESPONSE_MATCHER", "RESPONSE_MEDICATION_MATCHERS",
    "RESPONSE_UNITS", "RESPONSE_EXPOSURE", "RESPONSE_DEVICE", "RESPONSE_TIMING",
    "RESPONSE_CAP", "RESPONSE_ORDER_UNREACHABLE", "TRAJECTORY_BOUNDS",
    "TRAJECTORY_PRESSURE", "STATE_RULES", "STATE_CONDITION", "STATE_OUTPUT",
    "STATE_ECG", "STATE_EXAMINATION", "STUDY_STRUCTURE", "STUDY_TIMING",
})


def collect_declarative_issues(case):
    """Collect independent engine contradictions without modifying ``case``.

    Input is the normalized compiler representation. Invalid dependencies stop
    only the checks requiring them: one malformed response cannot conceal
    another response's mismatch or an otherwise calculable untreated path.
    """
    issues = []

    def add(code, path, message, **details):
        assert code in ENGINE_ISSUE_CODES
        issues.append({"code": code, "path": path, "message": message, "details": details})

    def numbers(mapping, path, allowed=NUMERIC_FIELDS, *, initial=False):
        if not isinstance(mapping, dict) or set(mapping) - allowed:
            add("NUMERIC_FIELDS", path, "Use only supported physiological fields.", allowed_fields=sorted(allowed))
            if not isinstance(mapping, dict):
                return False
        valid = isinstance(mapping, dict) and not (set(mapping) - allowed)
        for key, value in mapping.items():
            if key not in allowed:
                continue
            if not _finite(value):
                add("NUMERIC_VALUE", path + "." + key, "The physiological value must be finite.")
                valid = False
                continue
            lower, upper = BOUNDS[key]
            if initial and not lower <= value <= upper:
                add("BASELINE_BOUNDS", path + "." + key, "The baseline must be inside the supported physiological range.", actual=value, lower=lower, upper=upper)
                valid = False
            elif not initial and abs(value) > upper - lower:
                add("NUMERIC_DELTA_RANGE", path + "." + key, "The declared change exceeds the supported physiological range.", actual=value, maximum_absolute_change=upper-lower)
                valid = False
        return valid

    if not isinstance(case, dict) or not isinstance(case.get("engine"), dict):
        add("ENGINE_MODEL", "engine", "A declarative clinical engine is required.")
        return issues
    engine = case["engine"]
    if engine.get("model") != MODEL:
        add("ENGINE_MODEL", "engine.model", "Use the supported declarative engine model.", expected=MODEL)
    observed = case.get("observable", {})
    baseline_ok = isinstance(observed, dict) and OBSERVED_FIELDS <= set(observed)
    if not baseline_ok:
        add("BASELINE_OBSERVATIONS", "observable", "Include every baseline observation.", required_fields=sorted(OBSERVED_FIELDS))
    elif not numbers({key: observed[key] for key in OBSERVED_FIELDS}, "observable", OBSERVED_FIELDS, initial=True):
        baseline_ok = False
    if isinstance(observed, dict):
        if all(_finite(observed.get(key)) for key in ("sbp", "dbp")) and observed["dbp"] >= observed["sbp"]:
            add("BASELINE_PRESSURE", "observable", "Systolic pressure must exceed diastolic pressure.", sbp=observed["sbp"], dbp=observed["dbp"])
        if observed.get("pulse_present") is not True:
            add("ARREST_UNSUPPORTED", "observable.pulse_present", "The available action engine requires a pulse-present encounter.")
    labs = engine.get("initial_labs", {})
    labs_ok = numbers(labs, "engine.initial_labs", LAB_FIELDS, initial=True)
    initialized = OBSERVED_FIELDS | (set(labs) & LAB_FIELDS if isinstance(labs, dict) else set())
    drift = engine.get("untreated_drift_per_min", {})
    drift_ok = numbers(drift, "engine.untreated_drift_per_min")
    if isinstance(drift, dict):
        for key, value in drift.items():
            if key in NUMERIC_FIELDS and value and key not in initialized:
                add("LAB_INITIAL_VALUE", "engine.untreated_drift_per_min." + key, "Initialize every laboratory field that changes over time.", field=key)
                drift_ok = False
    horizon = engine.get("horizon_min", 180)
    horizon_ok = _finite(horizon) and 1 <= horizon <= 240 and int(horizon) == horizon
    if not horizon_ok:
        add("HORIZON", "engine.horizon_min", "Use a whole-number horizon from 1 through 240 minutes.")
    rules = engine.get("response_rules")
    if not isinstance(rules, list) or not 1 <= len(rules) <= 64:
        add("RESPONSE_RULES", "engine.response_rules", "Include 1 through 64 explicit response rules.")
    usable_rules = []
    identifiers = set()
    for index, rule in enumerate(rules if isinstance(rules, list) else []):
        path = f"engine.response_rules[{index}]"
        if not isinstance(rule, dict):
            add("RESPONSE_RULES", path, "A response rule must be an object.")
            continue
        identifier = rule.get("id")
        if not isinstance(identifier, str) or not identifier or identifier in identifiers:
            add("RESPONSE_IDENTIFIER", path + ".id", "Use a unique nonempty response identifier.")
        elif isinstance(identifier, str):
            identifiers.add(identifier)
        kind = rule.get("action_type")
        kind_ok = isinstance(kind, str) and kind in _ACTIONS
        if not kind_ok:
            add("RESPONSE_ACTION", path + ".action_type", "Use an action supported by the order interpreter.", supported_actions=sorted(_ACTIONS))
        matchers_ok = True
        for field in ("agent", "route", "units", "device"):
            if rule.get(field) is not None and (not isinstance(rule[field], str) or not rule[field].strip()):
                add("RESPONSE_MATCHER", path + "." + field, "An optional matcher must be a nonempty string or omitted.")
                matchers_ok = False
        if kind_ok and kind in _DRUGS and (not rule.get("agent") or not rule.get("route")):
            add("RESPONSE_MEDICATION_MATCHERS", path, "Medication effects need an exact supported agent and route.")
            matchers_ok = False
        if kind in ("norepinephrine", "anticoagulation") and not rule.get("units"):
            add("RESPONSE_UNITS", path + ".units", "A variable-unit medication needs explicit dose units.")
            matchers_ok = False
        expected = _DOSE_FIELDS.get(kind) if kind_ok else None
        exposure_ok = True
        if expected and (rule.get("dose_field") != expected or not _finite(rule.get("reference_dose")) or rule["reference_dose"] <= 0):
            add("RESPONSE_EXPOSURE", path, "Use the action's actual dose field and a positive reference dose.", expected_dose_field=expected)
            exposure_ok = False
        elif kind_ok and not expected and rule.get("dose_field") is not None:
            add("RESPONSE_EXPOSURE", path + ".dose_field", "This action has no measured dose field.", expected_dose_field=None)
            exposure_ok = False
        if kind == "oxygen" and not rule.get("device"):
            add("RESPONSE_DEVICE", path + ".device", "Oxygen effects must name the supported oxygen device.")
            matchers_ok = False
        timing_ok = True
        for field, lower, upper in (("onset_min", 0, 240), ("duration_min", 1, 240)):
            value = rule.get(field)
            if not _finite(value) or not lower <= value <= upper:
                add("RESPONSE_TIMING", path + "." + field, "Response timing must be within the supported interval.", lower=lower, upper=upper)
                timing_ok = False
        cap = rule.get("max_exposure")
        cap_ok = _finite(cap) and 0 < cap <= 20
        if not cap_ok:
            add("RESPONSE_CAP", path + ".max_exposure", "Use a positive finite exposure cap no greater than 20.")
        if baseline_ok and kind_ok and matchers_ok and exposure_ok:
            try:
                _validate_response_capability(case, rule)
            except ValueError:
                details = {"action_type": kind, "declared_matchers": {key: rule.get(key) for key in ("agent", "route", "units", "device", "dose_field", "reference_dose")}}
                normalized, error = _response_capability_probe(case, rule)
                if not error and normalized:
                    action = normalized[0]
                    details["normalized_matchers"] = {
                        "agent": _action_agent(action),
                        "route": action.get("route") or ("IV" if kind in ("norepinephrine", "nitroglycerin") else None),
                        "units": "units" if kind == "blood" else action.get("units") or {"dose_mg": "mg", "dose_g": "g", "volume_ml": "mL", "flow_lpm": "L/min", "rate_mcg_min": "mcg/min"}.get(expected),
                        "device": action.get("device"),
                    }
                add("RESPONSE_ORDER_UNREACHABLE", path, "A generated treatment rule cannot be reached by a supported order with those dose units, route or device. Use the supplied action contract's canonical matchers and a valid reference dose.", **details)
        delta = rule.get("delta")
        delta_ok = numbers(delta, path + ".delta")
        if isinstance(delta, dict):
            for key, value in delta.items():
                if key in NUMERIC_FIELDS and value and key not in initialized:
                    add("LAB_INITIAL_VALUE", path + ".delta." + key, "Initialize every laboratory field changed by a response.", field=key)
                    delta_ok = False
        if timing_ok and cap_ok and delta_ok:
            usable_rules.append((index, rule))
    if baseline_ok and labs_ok and drift_ok and horizon_ok:
        initial = {key: observed[key] for key in OBSERVED_FIELDS}
        initial.update(labs)
        for index, response in [(None, None)] + usable_rules:
            extrema = {}
            pressure_issue = None
            times = {0, horizon}
            if response is not None:
                times.update({min(horizon, response["onset_min"]), min(horizon, response["onset_min"] + response["duration_min"])})
            for at in sorted(times):
                values = {key: number + at * drift.get(key, 0) for key, number in initial.items()}
                if response is not None:
                    progress = 1.0 if response["action_type"] == "cardioversion" else min(1, max(0, (at - response["onset_min"]) / response["duration_min"]))
                    for key, delta in response["delta"].items():
                        if key in values:
                            values[key] += delta * response["max_exposure"] * progress
                context = {"time_min": at, "horizon_min": horizon, "response_index": index,
                           "exposure": response["max_exposure"] if response is not None else 0,
                           "response_id": str(response.get("id", ""))[:160] if response is not None else None,
                           "onset_min": response["onset_min"] if response is not None else None,
                           "duration_min": response["duration_min"] if response is not None else None}
                path = f"engine.response_rules[{index}].delta" if response is not None else "engine.untreated_drift_per_min"
                for key in sorted(values):
                    value = values[key]
                    lower, upper = BOUNDS[key]
                    if not lower <= value <= upper:
                        if response is not None and not response["delta"].get(key, 0):
                            # This is exactly the untreated linear path, whose
                            # endpoints have already been checked and reported.
                            continue
                        details = dict(context, field=key, actual=value, lower=lower, upper=upper,
                                       baseline=initial[key], drift_per_min=drift.get(key, 0),
                                       response_delta=response["delta"].get(key, 0) if response is not None else 0)
                        if response is not None and response["max_exposure"] * progress > 0:
                            untreated = initial[key] + at * drift.get(key, 0)
                            factor = response["max_exposure"] * progress
                            details["admissible_delta_at_this_time"] = {"lower": (lower - untreated) / factor, "upper": (upper - untreated) / factor}
                        elif response is None and at > 0:
                            details["admissible_drift_at_this_time"] = {"lower": (lower - initial[key]) / at, "upper": (upper - initial[key]) / at}
                        side = "lower" if value < lower else "upper"
                        previous = extrema.get((key, side))
                        if previous is None or (value < previous["actual"] if side == "lower" else value > previous["actual"]):
                            extrema[(key, side)] = details
                if values["dbp"] >= values["sbp"]:
                    if response is not None and not any(response["delta"].get(key, 0) for key in ("sbp", "dbp")):
                        continue
                    gap = values["dbp"] - values["sbp"]
                    if pressure_issue is None or gap > pressure_issue["dbp"] - pressure_issue["sbp"]:
                        pressure_issue = dict(context, sbp=values["sbp"], dbp=values["dbp"])
            # Report each lower/upper extremum once, rather than repeat the
            # same failing field at every breakpoint. All breakpoints above
            # are still checked with the execution gate's unchanged formula.
            for (key, _), details in sorted(extrema.items()):
                add("TRAJECTORY_BOUNDS", path + "." + key, "At this authored breakpoint the untreated drift plus the isolated maximum-exposure response leaves the supported range. Revise the authored model without clamping its results. Any admissible interval shown applies only at this time; all breakpoints must pass.", **details)
            if pressure_issue is not None:
                add("TRAJECTORY_PRESSURE", path, "At this authored breakpoint systolic pressure must exceed diastolic pressure.", **pressure_issue)
    _collect_state_and_study_issues(case, engine, initialized, add)
    return issues


def _collect_state_and_study_issues(case, engine, initialized, add):
    from ecg12 import PROFILES
    rules = engine.get("state_rules", [])
    if not isinstance(rules, list) or len(rules) > 64:
        add("STATE_RULES", "engine.state_rules", "Use at most 64 physiological observation rules.")
    for index, rule in enumerate(rules if isinstance(rules, list) else []):
        path = f"engine.state_rules[{index}]"
        if not isinstance(rule, dict):
            add("STATE_RULES", path, "An observation rule must be an object.")
            continue
        when = rule.get("when")
        if not isinstance(when, list) or not when:
            add("STATE_CONDITION", path + ".when", "Observation changes need explicit physiological conditions.")
        for j, condition in enumerate(when if isinstance(when, list) else []):
            if not isinstance(condition, dict) or not isinstance(condition.get("field"), str) or condition.get("field") not in initialized or not isinstance(condition.get("operator"), str) or condition.get("operator") not in _COMPARATORS or not _finite(condition.get("value")):
                add("STATE_CONDITION", path + f".when[{j}]", "Conditions may read only initialized numeric physiology with a supported comparison.")
        values = rule.get("set", {})
        if not isinstance(values, dict) or set(values) - _SET_FIELDS:
            add("STATE_OUTPUT", path + ".set", "Use supported observation fields.")
        if isinstance(values, dict):
            for key, value in values.items():
                if key not in _SET_FIELDS:
                    continue
                if key == "pulse_present":
                    if value is not True:
                        add("ARREST_UNSUPPORTED", path + ".set.pulse_present", "The available action engine does not support an arrest trajectory.")
                elif key == "visual":
                    if not isinstance(value, dict) or any(not isinstance(v, str) and not (k == "mottling" and isinstance(v, bool)) for k, v in value.items()):
                        add("STATE_OUTPUT", path + ".set.visual", "Visual findings must be descriptions with an optional mottling flag.")
                elif not isinstance(value, str) or not value.strip():
                    add("STATE_OUTPUT", path + ".set." + key, "Observation findings must be nonempty descriptions.")
            if values.get("ecg_profile") is not None and (not isinstance(values["ecg_profile"], str) or values["ecg_profile"] not in PROFILES):
                add("STATE_ECG", path + ".set.ecg_profile", "Use a supported ECG morphology.")
        examination = rule.get("examination", {})
        if not isinstance(examination, dict) or any(not isinstance(v, str) for v in examination.values()):
            add("STATE_EXAMINATION", path + ".examination", "Examination updates must be authored descriptions.")
    studies = case.get("investigations", {})
    if not isinstance(studies, dict):
        add("STUDY_STRUCTURE", "investigations", "Investigations must have normalized keyed results.")
        return
    for index, study in enumerate(studies.values()):
        path = f"investigations[{index}]"
        if not isinstance(study, dict) or not isinstance(study.get("result"), dict):
            add("STUDY_STRUCTURE", path, "Every investigation needs an explicit result.")
            continue
        delay = study.get("duration_min", 0)
        if not _finite(delay) or not 0 <= delay <= 120 or int(delay) != delay:
            add("STUDY_TIMING", path + ".duration_min", "Use a whole-number processing time from 0 through 120 minutes.")
