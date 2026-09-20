"""Mechanical ventilation of the severe asthmatic (faculty decision 2026-09-19).

Faculty statement: once intubated, the settings are what matter. Give a long
expiratory time, lower tidal volumes and permissive hypercapnia. The pressure
alarm will always sound, because airway pressure is high; what matters is not
the peak pressure but the plateau, the pressure that reaches the alveolus.

Air that cannot leave before the next breath accumulates. The trapped volume
raises intrathoracic pressure (auto-PEEP), which obstructs venous return and
drops the blood pressure. The rescue is to disconnect the circuit and let the
chest empty, then ventilate more slowly; vasopressors do not fix it.

    time constant   tau = resistance x compliance
    trapped volume  Vt x e^(-Te/tau) / (1 - e^(-Te/tau))   (steady state)
    auto-PEEP       trapped volume / compliance
    plateau         set PEEP + auto-PEEP + Vt / compliance
    peak            plateau + resistance x inspiratory flow

These are teaching magnitudes, not a prediction, and only the bank asthma family
uses them.
"""
import math

COMPLIANCE_L_PER_CMH2O = .05
RESISTANCE_BASE = 10.0            # cmH2O/L/s in a relaxed airway
RESISTANCE_PER_OBSTRUCTION = 30.0  # ...plus this much for the residual obstruction
DEFAULT_TIDAL_ML_PER_KG = 8.0
DEFAULT_RATE_PER_MIN = 14.0
DEFAULT_FLOW_L_PER_MIN = 60.0
DEFAULT_WEIGHT_KG = 70.0

SBP_PER_AUTO_PEEP = 2.0           # mmHg lost per cmH2O of trapped pressure
DISCONNECT_REBUILD_TAU_MIN = 3.0  # after a disconnection, the trap returns this fast
PEAK_ALARM_CMH2O = 40.0
PLATEAU_LIMIT_CMH2O = 30.0

# Faculty 2026-09-20: a pH of 7.20 is the practical target, not a safety boundary,
# and the PaCO2 has no validated absolute ceiling; 90 mmHg is the classic reference.
# A pH below the target calls for reassessing tolerance, trend and other causes of
# acidosis, not automatically for more minute ventilation.
PH_PRACTICAL_TARGET = 7.20
PACO2_CLASSIC_REFERENCE = 90

# Permissive hypercapnia: the CO2 a set minute ventilation cannot clear.
VE_REQUIRED_L_PER_MIN_PER_KG = .10
VE_OBSTRUCTION_PENALTY = .25      # deadspace of the obstructed lung

# An unsedated patient triggers extra breaths, so expiration is cut short and the
# delivered ventilation is less effective than the set one.
DYSSYNCHRONY_RATE_FACTOR = 1.35
SEDATION_DURATION_MIN = 45


def settings(state):
    """Current ventilator settings, with the defaults a ventilator would apply."""
    tr = state.get("treatments", {})
    weight = float(state.get("encounter_spec", {}).get("clinical_case", {})
                   .get("patient", {}).get("weight_kg") or DEFAULT_WEIGHT_KG)
    tidal = tr.get("ventilator_tidal_volume_ml")
    if tidal is None and tr.get("ventilator_tidal_ml_per_kg") is not None:
        tidal = float(tr["ventilator_tidal_ml_per_kg"]) * weight
    return {
        "mode": tr.get("ventilator_mode") or "VC/AC",
        "fio2_percent": float(tr.get("ventilator_fio2_percent") or 100),
        "peep_cmh2o": float(tr.get("ventilator_peep_cmh2o") or 0),
        "tidal_volume_ml": float(tidal if tidal is not None else DEFAULT_TIDAL_ML_PER_KG * weight),
        "rate_per_min": float(tr.get("ventilator_rate_per_min") or DEFAULT_RATE_PER_MIN),
        "flow_l_per_min": float(tr.get("ventilator_flow_l_per_min") or DEFAULT_FLOW_L_PER_MIN),
        "weight_kg": weight,
    }


def mechanics(state, airflow, sedated=True):
    """Airway pressures and trapped gas for the current settings and obstruction.

    ``airflow`` is the residual obstruction (1.0 at arrival, .2 fully relieved).
    An unsedated patient triggers breaths of their own, which shortens expiration.
    """
    s = settings(state)
    if not sedated:
        s = {**s, "rate_per_min": s["rate_per_min"] * DYSSYNCHRONY_RATE_FACTOR}
    tidal_l = s["tidal_volume_ml"] / 1000
    resistance = RESISTANCE_BASE + RESISTANCE_PER_OBSTRUCTION * max(0.0, airflow)
    tau = resistance * COMPLIANCE_L_PER_CMH2O
    cycle_s = 60 / max(4.0, s["rate_per_min"])
    inspiratory_s = tidal_l / (s["flow_l_per_min"] / 60)
    expiratory_s = max(.2, cycle_s - inspiratory_s)
    emptied = math.exp(-expiratory_s / tau)
    trapped_l = tidal_l * emptied / max(1e-6, 1 - emptied)
    auto_peep = trapped_l / COMPLIANCE_L_PER_CMH2O
    plateau = s["peep_cmh2o"] + auto_peep + tidal_l / COMPLIANCE_L_PER_CMH2O
    peak = plateau + resistance * (s["flow_l_per_min"] / 60)
    return {
        **s,
        "resistance_cmh2o_l_s": round(resistance, 1),
        "time_constant_s": round(tau, 2),
        "expiratory_time_s": round(expiratory_s, 2),
        "trapped_volume_ml": round(trapped_l * 1000),
        "auto_peep_cmh2o": round(auto_peep, 1),
        "plateau_cmh2o": round(plateau, 1),
        "peak_cmh2o": round(peak, 1),
        "minute_ventilation_l_min": round(tidal_l * s["rate_per_min"], 1),
        "high_pressure_alarm": peak >= PEAK_ALARM_CMH2O,
        "plateau_above_limit": plateau > PLATEAU_LIMIT_CMH2O,
        "dyssynchrony": not sedated,
    }


def effective_auto_peep(f, computed):
    """The trap that is actually present, which a disconnection has just emptied."""
    released = f.get("circuit_disconnected_at")
    if released is None:
        return computed
    since = max(0.0, f["elapsed"] - released)
    return computed * (1 - math.exp(-since / DISCONNECT_REBUILD_TAU_MIN))


def hypercapnia_note(ph, paco2):
    """What a pH under the practical target means, and what it does not mean."""
    if ph is None or ph >= PH_PRACTICAL_TARGET:
        return ""
    text = (f" The last pH is {ph:g}, below the practical target of {PH_PRACTICAL_TARGET:g}: reassess tolerance, the "
            "trend and other causes of acidosis. It does not by itself mean raising the minute ventilation, which "
            "would cost expiratory time.")
    if paco2 is not None and paco2 > PACO2_CLASSIC_REFERENCE:
        text += (f" The PaCO2 of {paco2:g} mmHg is above the classic reference of {PACO2_CLASSIC_REFERENCE} mmHg, which "
                 "is a reference and not a rigid limit: the pH and the cardiovascular repercussion weigh more.")
    return text


def pressure_report(mech, auto_peep):
    text = (f"Airway pressures: peak {mech['peak_cmh2o']:g}, plateau {mech['plateau_cmh2o']:g}, "
            f"auto-PEEP {auto_peep:.1f} cmH2O (set PEEP {mech['peep_cmh2o']:g}); "
            f"Vt {mech['tidal_volume_ml']:g} mL, rate {mech['rate_per_min']:g}/min, "
            f"expiratory time {mech['expiratory_time_s']:g} s.")
    if mech["high_pressure_alarm"]:
        text += (" The high airway pressure alarm is sounding; peak pressure reflects the resistance of the "
                 "airways, while the pressure reaching the alveolus is the plateau.")
    if mech["plateau_above_limit"]:
        text += " Plateau pressure is above 30 cmH2O."
    if mech.get("pneumothorax"):
        side = mech.get("pneumothorax_side") or "right"
        text += (f" Breath sounds are absent on the {side} and the peak pressure has jumped: air is under tension in "
                 f"the {side} pleural space.")
    if mech.get("dyssynchrony"):
        text += (" The patient is triggering breaths of their own: the delivered rate is higher than the set rate "
                 "and expiration is shorter.")
    return text


def blood_gas(state, airflow, sedated=True):
    """Permissive hypercapnia: what the minute ventilation leaves behind.

    Breaths the patient triggers do clear CO2, so dyssynchrony shows up as trapped
    gas and a falling pressure, not as a worse gas.
    """
    mech = mechanics(state, airflow, sedated)
    required = (VE_REQUIRED_L_PER_MIN_PER_KG * mech["weight_kg"]
                * (1 + VE_OBSTRUCTION_PENALTY * max(0.0, airflow)))
    return 40 * required / max(.5, mech["minute_ventilation_l_min"]), mech
