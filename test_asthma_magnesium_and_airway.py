"""Magnesium in severe asthma, and ventilator settings written naturally.

Faculty (2026-09-19): every severe asthmatic should receive intravenous
magnesium before intubation, and "Intubate with VC/AC at FiO2 100% and PEEP 5"
must be one order. It used to split on the comma or the "and" into two
incomplete intubations, and magnesium was not a recognized treatment at all.
"""
import pytest

from family_engine import MAGNESIUM, execute_family_bundle
from family_parser import parse_family_actions
from test_cognitive_encounters import encounter
from test_curriculum_trajectories import load_engine

TUBE = {"type": "intubation", "ventilator_mode": "VC/AC", "fio2_percent": 100, "peep_cmh2o": 5}


@pytest.fixture(scope="module")
def engine():
    return load_engine()


@pytest.mark.parametrize("text", [
    "Intubate VC/AC FiO2 100% PEEP 5.",
    "Intubate with VC/AC ventilation at FiO2 100% and PEEP 5.",
    "Intubate: VC/AC, FiO2 100%, PEEP 5.",
    "Intuba con VC/AC, FiO2 100% y PEEP 5.",
])
def test_ventilator_settings_stay_with_the_airway_order(text):
    assert parse_family_actions(text)["actions"] == [TUBE]


def test_a_separate_order_is_still_separate():
    actions = parse_family_actions("Start BiPAP 12/5 at FiO2 50% and give albuterol 5 mg nebulized.")["actions"]
    assert [a["type"] for a in actions] == ["niv", "bronchodilator"]


@pytest.mark.parametrize("text", [
    "Give magnesium sulfate 2 g IV over 20 minutes.",
    "Administra sulfato de magnesio 2 g IV en 20 minutos.",
])
def test_magnesium_is_a_recognized_treatment(text):
    action = parse_family_actions(text)["actions"][0]
    assert action["type"] == "magnesium" and action["dose_mg"] == 2000 and action["route"] == "IV"


def airflow(engine, orders):
    state = encounter(engine, "asthma", "asthma_24f")["state"]
    for order in orders:
        result = execute_family_bundle(state, parse_family_actions(order))
    f = state["family_state"]
    return f["obstruction"] - f["bronchodilation"], result


def test_magnesium_adds_bronchodilation_to_the_beta_agonist(engine):
    first = "Give albuterol 5 mg nebulized and methylprednisolone 125 mg IV. Reassess in 20 minutes."
    without, _ = airflow(engine, [first, "Give albuterol 5 mg nebulized. Reassess in 20 minutes."])
    with_magnesium, result = airflow(engine, [
        first, "Give albuterol 5 mg nebulized and magnesium sulfate 2 g IV over 20 minutes. Reassess in 20 minutes."])
    assert with_magnesium < without
    assert "Magnesium sulfate 2 g IV" in " ".join(s.get("label", "") for s in result["action_summaries"])


def test_the_magnesium_effect_is_capped(engine):
    state = encounter(engine, "asthma", "asthma_24f")["state"]
    execute_family_bundle(state, parse_family_actions("Give magnesium sulfate 4 g IV. Reassess in 60 minutes."))
    execute_family_bundle(state, parse_family_actions("Give magnesium sulfate 4 g IV. Reassess in 60 minutes."))
    assert state["family_state"]["magnesium_effect"] <= MAGNESIUM["max_bronchodilation"] + 1e-9
