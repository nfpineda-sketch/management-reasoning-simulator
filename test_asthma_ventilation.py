"""Ventilating the intubated asthmatic (faculty decision 2026-09-19).

Faculty statement: give a long expiratory time, lower tidal volumes and
permissive hypercapnia; the pressure alarm always sounds, and what matters is
the plateau, not the peak. Trapped gas drops the blood pressure, and the rescue
is to disconnect the circuit and ventilate more slowly.
"""
import pytest

import asthma_ventilation as vent
from family_engine import clinical_update, execute_family_bundle
from family_parser import parse_family_actions
from test_cognitive_encounters import encounter
from test_curriculum_trajectories import load_engine

AGGRESSIVE = "Give ketamine 100 mg IV and intubate VC/AC FiO2 100% PEEP 5 Vt 700 mL rate 28. Reassess in 5 minutes."
PROTECTIVE = ("Give ketamine 100 mg IV and intubate VC/AC FiO2 100% PEEP 0 Vt 450 mL rate 12 flow 80 L/min. "
              "Reassess in 5 minutes.")


@pytest.fixture(scope="module")
def engine():
    return load_engine()


def course(engine, orders):
    state = encounter(engine, "asthma", "asthma_24f")["state"]
    for order in orders:
        result = execute_family_bundle(state, parse_family_actions(order))
        assert result["executed"], result["clarification"]
    return state, result


def mechanics(state):
    return state["family_state"]["ventilator_mechanics"]


@pytest.mark.parametrize("text, expected", [
    ("Intubate VC/AC FiO2 100% PEEP 5 Vt 420 mL rate 10 flow 80 L/min.",
     {"tidal_volume_ml": 420.0, "rate_per_min": 10.0, "flow_l_per_min": 80.0}),
    ("Intubate with VC/AC at FiO2 100%, PEEP 0, tidal volume 6 mL/kg, rate 10 and flow 80 L/min.",
     {"tidal_ml_per_kg": 6.0, "rate_per_min": 10.0, "flow_l_per_min": 80.0}),
    ("Ajusta el ventilador a VC/AC, FiO2 60%, PEEP 0, volumen corriente 400 ml y frecuencia 8.",
     {"tidal_volume_ml": 400.0, "rate_per_min": 8.0}),
])
def test_settings_are_read_from_the_order(text, expected):
    action = parse_family_actions(text)["actions"][0]
    for field, value in expected.items():
        assert action[field] == value


@pytest.mark.parametrize("text", ["Disconnect the ventilator circuit.", "Desconecta el circuito del ventilador."])
def test_the_disconnection_is_its_own_manoeuvre(text):
    assert parse_family_actions(text)["actions"] == [{"type": "ventilator_disconnect"}]


def test_a_disconnection_needs_a_ventilator(engine):
    state = encounter(engine, "asthma", "asthma_24f")["state"]
    result = execute_family_bundle(state, parse_family_actions("Disconnect the ventilator circuit."))
    assert not result["executed"] and "not on a ventilator" in result["clarification"]


def test_a_short_expiratory_time_traps_air_and_drops_the_pressure(engine):
    aggressive, _ = course(engine, [AGGRESSIVE])
    protective, _ = course(engine, [PROTECTIVE])
    assert mechanics(aggressive)["auto_peep_cmh2o"] > mechanics(protective)["auto_peep_cmh2o"] + 5
    assert aggressive["observable"]["sbp"] < protective["observable"]["sbp"] - 10


def test_the_peak_stays_high_while_the_plateau_follows_the_settings(engine):
    aggressive, _ = course(engine, [AGGRESSIVE])
    protective, _ = course(engine, [PROTECTIVE])
    # Resistance keeps the peak up whatever the settings: the alarm always sounds.
    assert mechanics(aggressive)["high_pressure_alarm"] and mechanics(protective)["high_pressure_alarm"]
    assert mechanics(protective)["plateau_cmh2o"] < vent.PLATEAU_LIMIT_CMH2O
    assert mechanics(aggressive)["plateau_cmh2o"] > mechanics(protective)["plateau_cmh2o"] + 10
    assert "plateau" in clinical_update(protective)


def test_disconnecting_the_circuit_empties_the_trap_and_it_rebuilds(engine):
    state, _ = course(engine, [AGGRESSIVE])
    trapped = state["observable"]["sbp"]
    execute_family_bundle(state, parse_family_actions("Disconnect the ventilator circuit. Reassess in 1 minute."))
    assert state["observable"]["sbp"] > trapped + 5
    execute_family_bundle(state, parse_family_actions("Reassess in 15 minutes."))
    assert state["observable"]["sbp"] <= trapped + 1


def test_slower_ventilation_fixes_what_the_disconnection_only_relieves(engine):
    state, _ = course(engine, [AGGRESSIVE, "Disconnect the ventilator circuit. Reassess in 1 minute.",
                               "Adjust the ventilator to VC/AC FiO2 100%, PEEP 0, Vt 450 mL, rate 10 and flow 80 L/min. "
                               "Reassess in 15 minutes."])
    assert mechanics(state)["auto_peep_cmh2o"] < 2
    assert state["observable"]["sbp"] >= 135


def test_permissive_hypercapnia_follows_the_minute_ventilation(engine):
    aggressive, first = course(engine, [AGGRESSIVE, "Order arterial blood gas. Reassess in 5 minutes."])
    protective, second = course(engine, [PROTECTIVE, "Order arterial blood gas. Reassess in 5 minutes."])
    high = next(s["result"] for s in first["action_summaries"] if s.get("diagnostic_type") == "abg")
    low = next(s["result"] for s in second["action_summaries"] if s.get("diagnostic_type") == "abg")
    assert low["paco2_mm_hg"] > high["paco2_mm_hg"] + 20
    assert low["ph"] < high["ph"]


def test_sedation_wears_off_and_the_patient_fights_the_ventilator(engine):
    state, _ = course(engine, [AGGRESSIVE, "Reassess in 60 minutes."])
    assert state["observable"]["mental_status"] == "Awake and fighting the ventilator"
    trapped = state["family_state"]["ventilator_mechanics"]["auto_peep_cmh2o"]
    execute_family_bundle(state, parse_family_actions("Give ketamine 50 mg IV. Reassess in 5 minutes."))
    assert state["observable"]["mental_status"] == "Sedated"
    assert state["family_state"]["ventilator_mechanics"]["auto_peep_cmh2o"] < trapped


def test_dyssynchrony_traps_air_until_sedation_is_restored(engine):
    state, _ = course(engine, [PROTECTIVE, "Reassess in 60 minutes."])
    assert state["observable"]["mental_status"] == "Awake and fighting the ventilator"
    fighting = mechanics(state)
    # Triggered breaths raise the delivered rate and shorten expiration.
    assert fighting["dyssynchrony"] and fighting["rate_per_min"] > 12
    pressure = state["observable"]["sbp"]
    execute_family_bundle(state, parse_family_actions("Give ketamine 50 mg IV. Reassess in 5 minutes."))
    assert mechanics(state)["auto_peep_cmh2o"] < fighting["auto_peep_cmh2o"]
    assert state["observable"]["sbp"] >= pressure


def test_oxygen_raises_the_arterial_tension_not_only_the_saturation(engine):
    """A saturation of 99% on FiO2 100% used to report PaO2 77 and a P/F ratio of 77."""
    state, result = course(engine, [PROTECTIVE, "Order arterial blood gas. Reassess in 5 minutes."])
    gas = next(s["result"] for s in result["action_summaries"] if s.get("diagnostic_type") == "abg")
    assert gas["fio2_percent"] == 100
    assert gas["pao2_mm_hg"] > 200 and gas["pf_ratio"] > 200


# Ordering the ventilator, in the words residents use (faculty, 2026-09-21).
# Found playing the silent-chest asthmatic: the engine reported a pH of 7.16
# below the practical target and the order that answers it — lowering the rate
# to lengthen expiration — could not be written. "Baja el volumen corriente a
# 380 mL" was read as a 380 mL fluid bolus.

INTUBATE = ("Give ketamine 100 mg IV and intubate VC/AC FiO2 100% PEEP 5 Vt 420 mL rate 14. "
            "Reassess in 10 minutes.")


@pytest.mark.parametrize("text, field, value", [
    ("Baja la frecuencia del ventilador a 8.", "rate_per_min", 8.0),
    ("Lower the ventilator rate to 8.", "rate_per_min", 8.0),
    ("Set the ventilator rate to 8.", "rate_per_min", 8.0),
    ("Adjust the ventilator to rate 8.", "rate_per_min", 8.0),
    ("Baja el volumen corriente a 380 mL.", "tidal_volume_ml", 380.0),
    ("Lower the tidal volume to 380 mL.", "tidal_volume_ml", 380.0),
    ("Raise the PEEP to 8.", "peep_cmh2o", 8.0),
    ("Sube la FiO2 del ventilador a 80%.", "fio2_percent", 80.0),
])
def test_the_ventilator_is_adjusted_in_the_words_residents_use(text, field, value):
    parsed = parse_family_actions(text)["actions"]
    assert [a["type"] for a in parsed] == ["respiratory_adjustment"], parsed
    assert parsed[0][field] == value


@pytest.mark.parametrize("text", [
    # The faculty asked that the resident say whose rate it is.
    "Baja la frecuencia a 8.",
    "Baja la frecuencia cardíaca a 90.",
])
def test_a_bare_rate_is_not_a_ventilator_order(text):
    parsed = parse_family_actions(text)["actions"]
    assert all(a["type"] != "respiratory_adjustment" for a in parsed), parsed


def test_a_tidal_volume_is_never_a_fluid_bolus():
    parsed = parse_family_actions("Baja el volumen corriente a 380 mL.")["actions"]
    assert all(a["type"] != "fluid" for a in parsed), parsed
    # And a real bolus is still a real bolus.
    fluid = parse_family_actions("Dale 1000 mL de suero fisiológico IV.")["actions"]
    assert [a["type"] for a in fluid] == ["fluid"] and fluid[0]["volume_ml"] == 1000


def test_a_slower_rate_buys_expiratory_time(engine):
    state = encounter(engine, "asthma", "asthma_49m")["state"]
    for order in (INTUBATE, "Baja la frecuencia del ventilador a 8. Reevalúa en 10 minutos."):
        result = execute_family_bundle(state, parse_family_actions(order))
        assert result["executed"], result.get("clarification")
        if order is INTUBATE:
            fast = dict(state["family_state"]["ventilator_mechanics"])
    slow = state["family_state"]["ventilator_mechanics"]
    assert state["treatments"]["ventilator_rate_per_min"] == 8
    assert slow["expiratory_time_s"] > fast["expiratory_time_s"]
    assert slow["auto_peep_cmh2o"] <= fast["auto_peep_cmh2o"]


def test_a_smaller_breath_lowers_the_pressure_that_reaches_the_alveolus(engine):
    state = encounter(engine, "asthma", "asthma_49m")["state"]
    for order in (INTUBATE, "Baja el volumen corriente a 380 mL. Reevalúa en 10 minutos."):
        result = execute_family_bundle(state, parse_family_actions(order))
        assert result["executed"], result.get("clarification")
        if order is INTUBATE:
            before = dict(state["family_state"]["ventilator_mechanics"])
    after = state["family_state"]["ventilator_mechanics"]
    assert state["treatments"]["ventilator_tidal_volume_ml"] == 380
    assert after["plateau_cmh2o"] < before["plateau_cmh2o"]


def test_two_settings_changed_in_one_turn_both_stick(engine):
    # The second adjustment used to refill the rate from the state before the
    # first one, so "rate 8 and Vt 380" ended the turn back at rate 14.
    state = encounter(engine, "asthma", "asthma_49m")["state"]
    execute_family_bundle(state, parse_family_actions(INTUBATE))
    result = execute_family_bundle(state, parse_family_actions(
        "Baja la frecuencia del ventilador a 8 y baja el volumen corriente a 380 mL. Reevalúa en 10 minutos."))
    assert result["executed"], result.get("clarification")
    treatments = state["treatments"]
    assert treatments["ventilator_rate_per_min"] == 8
    assert treatments["ventilator_tidal_volume_ml"] == 380
    # And the settings the resident did not touch are unchanged.
    assert treatments["ventilator_mode"] == "VC/AC"
    assert treatments["ventilator_fio2_percent"] == 100
    assert treatments["ventilator_peep_cmh2o"] == 5
