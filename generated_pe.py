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


def step(state, fluid_ml_this_minute):
    """One minute of the obstructed ventricle. Returns an event text or None."""
    if spec(state) is None:
        return None
    # pe_obstruction reads the declared bleeding risk from the case engine, so the
    # generated declaration carries it under its own key.
    case = state["encounter_spec"]["clinical_case"]
    case["engine"].setdefault("lysis_bleeding_risk", bleeding_risk(state))
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
