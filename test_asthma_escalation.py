"""Diluted epinephrine, continuous nebulization and ketamine in severe asthma.

Faculty (2026-09-19): before intubation a severe asthmatic should receive
continuous inhaled beta-agonists, IV steroids, magnesium and diluted epinephrine
(1 mg in 1000 mL as a drip, or 50-150 mcg IV boluses); if intubation is needed,
ketamine is the preferred induction and maintenance agent. Magnitudes are
teaching parameters pending review.
"""
import pytest

from family_engine import CONTINUOUS_NEBULIZER, EPINEPHRINE, KETAMINE, execute_family_bundle
from family_parser import parse_family_actions
from test_cognitive_encounters import encounter
from test_curriculum_trajectories import load_engine

FIRST = "Give albuterol 5 mg nebulized and methylprednisolone 125 mg IV. Reassess in 15 minutes."


@pytest.fixture(scope="module")
def engine():
    return load_engine()


def course(engine, orders, variant="asthma_24f"):
    state = encounter(engine, "asthma", variant)["state"]
    for order in orders:
        result = execute_family_bundle(state, parse_family_actions(order))
        assert result["executed"], result["clarification"]
    return state, result


@pytest.mark.parametrize("text, expected", [
    ("Start an epinephrine drip at 5 mcg/min.", {"type": "epinephrine", "rate": 5.0, "units": "mcg/min", "operation": "start"}),
    ("Inicia goteo de adrenalina a 10 mcg/min.", {"type": "epinephrine", "rate": 10.0, "units": "mcg/min", "operation": "start"}),
    ("Give epinephrine 100 mcg IV bolus.", {"type": "epinephrine_bolus", "dose_mcg": 100.0, "route": "IV"}),
    ("Administra un bolo de adrenalina 100 mcg IV.", {"type": "epinephrine_bolus", "dose_mcg": 100.0, "route": "IV"}),
])
def test_epinephrine_is_parsed_as_a_drip_or_a_bolus(text, expected):
    assert parse_family_actions(text)["actions"] == [expected]


def test_an_epinephrine_bolus_relieves_the_obstruction_and_then_fades(engine):
    state, _ = course(engine, [FIRST, "Give epinephrine 100 mcg IV bolus. Reassess in 3 minutes."])
    relieved = state["observable"]["respiratory_rate"]
    assert state["family_state"]["epi_bolus_pool"] > 0
    execute_family_bundle(state, parse_family_actions("Reassess in 20 minutes."))
    assert state["family_state"]["epi_bolus_pool"] == 0
    assert state["observable"]["respiratory_rate"] > relieved


def test_the_drip_costs_tachycardia_while_it_supports_pressure(engine):
    without, _ = course(engine, [FIRST, "Reassess in 15 minutes."])
    with_drip, _ = course(engine, [FIRST, "Start an epinephrine drip at 10 mcg/min. Reassess in 15 minutes."])
    assert with_drip["observable"]["hr"] > without["observable"]["hr"]
    assert with_drip["observable"]["sbp"] > without["observable"]["sbp"]
    assert with_drip["observable"]["respiratory_rate"] <= without["observable"]["respiratory_rate"]


def test_stopping_the_drip_removes_its_effect(engine):
    state, _ = course(engine, [FIRST, "Start an epinephrine drip at 10 mcg/min. Reassess in 10 minutes.",
                               "Stop the epinephrine. Reassess in 10 minutes."])
    assert state["family_state"]["epinephrine"] == 0


@pytest.mark.parametrize("text", [
    "Start continuous albuterol nebulization.",
    "Inicia salbutamol nebulizado continuo.",
    "Give albuterol 10 mg/hour nebulized.",
])
def test_continuous_nebulization_is_its_own_order(text):
    action = parse_family_actions(text)["actions"][0]
    assert action["type"] == "continuous_bronchodilator" and action["rate_mg_h"] == 10


def test_continuous_nebulization_holds_what_single_doses_lose(engine):
    intermittent, _ = course(engine, [FIRST, "Reassess in 60 minutes."])
    continuous, _ = course(engine, ["Start continuous albuterol nebulization. Give methylprednisolone 125 mg IV. "
                                    "Reassess in 15 minutes.", "Reassess in 60 minutes."])
    assert continuous["observable"]["respiratory_rate"] < intermittent["observable"]["respiratory_rate"]
    assert continuous["family_state"]["bronchodilation"] > intermittent["family_state"]["bronchodilation"]


def test_stopping_the_nebulization_lets_the_effect_fade(engine):
    state, _ = course(engine, ["Start continuous albuterol nebulization. Reassess in 30 minutes.",
                               "Stop the continuous albuterol. Reassess in 45 minutes."])
    assert state["family_state"]["continuous_bronchodilator_mg_h"] == 0
    assert state["family_state"]["bronchodilation"] < CONTINUOUS_NEBULIZER["max_bronchodilation"] * .6


def test_ketamine_is_executable_in_a_bank_case_and_bronchodilates(engine):
    with_ketamine, _ = course(engine, ["Give ketamine 100 mg IV. Reassess in 10 minutes."])
    plain, _ = course(engine, ["Reassess in 10 minutes."])
    assert with_ketamine["family_state"]["ketamine_mg"] > 0
    assert with_ketamine["observable"]["respiratory_rate"] < plain["observable"]["respiratory_rate"]
    assert with_ketamine["family_state"]["sedation_bp_drop"] == 0


def test_propofol_drops_the_pressure_and_ketamine_does_not(engine):
    tube = "Intubate VC/AC FiO2 100% PEEP 5. Reassess in 5 minutes."
    ketamine, _ = course(engine, ["Give ketamine 100 mg IV. " + tube])
    propofol, _ = course(engine, ["Give propofol 150 mg IV. " + tube])
    assert propofol["observable"]["sbp"] < ketamine["observable"]["sbp"] - 5
