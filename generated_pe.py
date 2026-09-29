"""The obstructed right ventricle inside a generated case (faculty, 2026-09-20).

Third mechanism, same shape as the coronary and airway ones: the case declares
``engine.pulmonary_obstruction``, a gate refuses a declaration the resident cannot
discover, and the shared pe_obstruction module does the work. The adapter reads
the result as observable deltas.

What the declaration buys: the clock of sustained hypotension that makes systemic
thrombolysis the treatment, the price of volume given faster than an obstructed
ventricle accepts, the dissolution that follows an indicated thrombolytic, its
bleeding, and what positive pressure costs a circulation that is already
obstructed.
"""
import pe_obstruction

# The shared core amplifies what it is given, so the deltas are gentler than the
# bank's internal mapping, exactly as for the AV block and auto-PEEP.
SBP_PER_BURDEN = 45.0
DBP_PER_BURDEN = 25.0
HR_PER_BURDEN = 20.0
SPO2_PER_BURDEN = 8.0
RR_PER_BURDEN = 10.0
SBP_FLOOR = -30.0

MECHANISM_ACTIONS = frozenset({"thrombolysis"})


def spec(state):
    case = state.get("encounter_spec", {}).get("clinical_case", {})
    return case.get("engine", {}).get("pulmonary_obstruction")


def bleeding_risk(state):
    declaration = spec(state) or {}
    return declaration.get("bleeding_risk")


def _vasopressor_running(state):
    treatments = state.get("coupled_state", {}).get("treatments", {}) or {}
    return bool(treatments.get("norepinephrine")) or float(state["family_state"].get("norepinephrine") or 0) > 0


def remember_arrival(state):
    """The pressure the case arrived with, before anything supported it."""
    f = state["family_state"]
    f.setdefault("pe_unsupported_sbp", float(state.get("observable", {}).get("sbp") or 0))


def _track_support(state):
    """Whether a running vasopressor was needed: it counts only if started on a low pressure."""
    f = state["family_state"]
    sbp = float(state.get("observable", {}).get("sbp") or 0)
    if not _vasopressor_running(state):
        f["pe_unsupported_sbp"] = sbp
        f.pop("pe_vasopressor_needed", None)
    elif "pe_vasopressor_needed" not in f:
        f["pe_vasopressor_needed"] = float(f.get("pe_unsupported_sbp", sbp)) < pe_obstruction.HYPOTENSION_SBP


def assessment(state):
    """This minute's embolism state in a generated case (2026-09-29).

    The generated pressure comes from a shared core that cannot separate a
    vasopressor's lift or a drug-induced drop from what the obstruction does. So a
    vasopressor counts only when it was started on a systolic below the threshold
    (starting one never creates the indication), sedation never counts as altered
    consciousness, and other drug effects inside the core are not separated: a
    documented approximation, where the bank engine computes the embolism's share
    exactly.
    """
    f = state["family_state"]
    observable = state.get("observable", {})
    running = _vasopressor_running(state)
    needed = None
    if running:
        needed = f.get("pe_vasopressor_needed")
        if needed is None:
            needed = float(f.get("pe_unsupported_sbp", observable.get("sbp") or 0)) < pe_obstruction.HYPOTENSION_SBP
    values = state.get("generated_state", {}).get("values", {}) or {}
    lactate = values.get("lactate_mmol_l")
    lactate = float(lactate if lactate is not None else f.get("lactate") or 0)
    hidden = state.get("coupled_state", {}).get("hidden", {}) or {}
    sedated = float(hidden.get("procedural_sedation_effect") or 0) > 0
    altered = str(observable.get("mental_status") or "Alert") != "Alert" and not sedated
    return pe_obstruction.assessment(float(observable.get("sbp") or 0), float(observable.get("crt") or 2), lactate,
                                     altered, vasopressor_running=running, vasopressor_needed=needed)


def step(state, fluid_ml_this_minute):
    """One minute of the obstructed ventricle. Returns an event text or None."""
    if spec(state) is None:
        return None
    # pe_obstruction reads the declared bleeding risk from the case engine, so the
    # generated declaration carries it under its own key.
    case = state["encounter_spec"]["clinical_case"]
    case["engine"].setdefault("lysis_bleeding_risk", bleeding_risk(state))
    _track_support(state)
    state["family_state"]["pe_attributable"] = assessment(state)
    return pe_obstruction.step(state, fluid_ml_this_minute)


def relief(f):
    """How much of the obstruction the thrombolytic has dissolved, 0 to 1."""
    share = pe_obstruction.lysis_effect(f)
    return share * (1 - pe_obstruction.LYSIS_CIRCULATION_TARGET)


def generated_effects(state, peep_cmh2o=0):
    """(sbp, dbp, hr, spo2, respiratory_rate, hemoglobin) for the adapter."""
    if spec(state) is None:
        return (0.0,) * 6
    f = state["family_state"]
    strain_circulation, strain_lung = pe_obstruction.surface_penalty(f, peep_cmh2o)
    gain = relief(f)
    burden = strain_circulation - gain
    sbp = max(SBP_FLOOR, -SBP_PER_BURDEN * burden)
    dbp = max(SBP_FLOOR * .6, -DBP_PER_BURDEN * burden)
    hr = HR_PER_BURDEN * burden
    spo2 = -SPO2_PER_BURDEN * (strain_lung - gain)
    rr = RR_PER_BURDEN * (strain_lung - gain)
    hemoglobin = float(f.get("hemoglobin", 0)) - float(f.get("hemoglobin_reference", f.get("hemoglobin", 0)))
    return sbp, dbp, hr, spo2, rr, hemoglobin


def remember_hemoglobin(f):
    """The haemoglobin the case authored, so bleeding can be read as a change."""
    f.setdefault("hemoglobin_reference", float(f.get("hemoglobin", 0)))
