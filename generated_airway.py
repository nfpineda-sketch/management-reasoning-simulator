"""The obstructed airway inside a generated case (faculty decision 2026-09-20).

Second mechanism after the coronary one, and the same shape: the case declares
``engine.airway_obstruction``, the gate refuses a declaration the resident cannot
discover, and the shared modules that already serve the bank (asthma_ventilation
and asthma_complications) run against the generated state. The adapter reads
their result as observable deltas, never as bank variables.

What the declaration buys: the obstruction that worsens on its own and answers to
the bronchodilators the resident gives, the exhaustion that follows, the window in
which intubation belongs, the trapped gas of an expiratory time that is too short,
the barotrauma that tears the lung, and the disconnection that empties it.

Teaching magnitudes live in the two shared modules; nothing is duplicated here.
"""
import asthma_complications
import asthma_ventilation

DRIFT_PER_MIN = .002               # the untreated obstruction, as in the bank engine
STEROID_ONSET_MIN = 60
STEROID_PER_MIN = .004
OBSTRUCTION_FLOOR = .2

# The core owns the physiology, so the mechanism nudges it, as the AV block does.
SBP_PER_AUTO_PEEP = 1.2            # bank value is 2.0 mmHg per cmH2O; the core amplifies
SBP_FLOOR = -30.0
TENSION_SBP = -25.0
TENSION_SPO2 = -12.0
RR_PER_OBSTRUCTION = 18.0
SPO2_PER_OBSTRUCTION = 14.0


def spec(state):
    """The case's airway declaration, or None."""
    case = state.get("encounter_spec", {}).get("clinical_case", {})
    return case.get("engine", {}).get("airway_obstruction")


def airflow(state):
    """Residual obstruction: the declared severity, less what treatment has relieved."""
    declaration, f = spec(state), state["family_state"]
    if declaration is None:
        return 0.0
    base = f.get("airway_obstruction", float(declaration.get("severity", 1.0)))
    relieved = float(f.get("bronchodilation") or 0) + asthma_complications.beta_effect(f, 0) * 0
    from family_engine import _airway_relaxation
    return max(OBSTRUCTION_FLOOR, base - relieved - _airway_relaxation(f))


def step(state):
    """One minute of the obstructed airway. Returns an event text or None."""
    declaration, f = spec(state), state["family_state"]
    if declaration is None:
        return None
    base = f.setdefault("airway_obstruction", float(declaration.get("severity", 1.0)))
    steroid_active = f.get("steroid_at") is not None and f["elapsed"] - f["steroid_at"] >= STEROID_ONSET_MIN
    f["airway_obstruction"] = base + DRIFT_PER_MIN - (STEROID_PER_MIN * f.get("steroid_exposure", 0) if steroid_active else 0)
    residual = airflow(state)
    f["airway_obstruction"] += asthma_complications.track_exhaustion(f, state.get("observable", {}))
    if not f.get("invasive"):
        return None
    sedated = f.get("sedation_at") is not None and f["elapsed"] - f["sedation_at"] <= asthma_ventilation.SEDATION_DURATION_MIN
    mechanics = asthma_ventilation.mechanics(state, residual, sedated)
    auto_peep = asthma_ventilation.effective_auto_peep(f, mechanics["auto_peep_cmh2o"])
    tension = asthma_complications.tension_fraction(f)
    f["ventilator_mechanics"] = {
        **mechanics, "auto_peep_cmh2o": round(auto_peep, 1),
        "peak_cmh2o": round(mechanics["peak_cmh2o"] + asthma_complications.TENSION_PEAK_RISE * tension, 1),
        "pneumothorax": tension > .2, "pneumothorax_side": f.get("pneumothorax_side"),
    }
    return asthma_complications.step(f, f["ventilator_mechanics"])


def intubation_note(state):
    """Judge the moment of intubation; called when the tube goes in."""
    if spec(state) is None:
        return None
    f = state["family_state"]
    timing = asthma_complications.intubation_timing(f, state.get("observable", {}), airflow(state))
    asthma_complications.apply_intubation_timing(f, timing)
    return asthma_complications.timing_note(timing)


def generated_effects(state):
    """Observable deltas for the adapter: (sbp, dbp, spo2, respiratory_rate)."""
    declaration, f = spec(state), state["family_state"]
    if declaration is None:
        return 0.0, 0.0, 0.0, 0.0
    residual = airflow(state)
    arrival = float(declaration.get("severity", 1.0))
    # Only the change from the authored arrival state is a delta: the case already
    # describes the patient the resident meets.
    change = residual - arrival
    spo2 = -SPO2_PER_OBSTRUCTION * change
    rr = RR_PER_OBSTRUCTION * change
    sbp = 0.0
    if f.get("invasive"):
        mechanics = f.get("ventilator_mechanics") or {}
        reserve = 1 - asthma_complications.preload_protection(f)
        sbp -= SBP_PER_AUTO_PEEP * float(mechanics.get("auto_peep_cmh2o") or 0) * reserve
        sbp -= asthma_complications.intubation_penalty(f) * reserve
        tension = asthma_complications.tension_fraction(f)
        sbp += TENSION_SBP * tension
        spo2 += TENSION_SPO2 * tension
        rr = 0.0  # the ventilator sets the rate
    return max(SBP_FLOOR, sbp), max(SBP_FLOOR * .6, sbp * .6), spo2, rr


def pressure_report(state):
    """The airway pressures, for the update the resident reads."""
    f = state["family_state"]
    mechanics = f.get("ventilator_mechanics")
    if spec(state) is None or not f.get("invasive") or not mechanics:
        return ""
    return " " + asthma_ventilation.pressure_report(mechanics, mechanics["auto_peep_cmh2o"])
