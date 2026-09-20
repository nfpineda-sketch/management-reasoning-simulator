"""The obstructed right ventricle (faculty decisions 2026-09-20).

Faculty: systemic thrombolysis if there is sustained hypotension, and punish volume
given fast. Teaching magnitudes pending review.
"""
import pytest

import pe_obstruction as pe
from family_engine import execute_family_bundle
from family_parser import parse_family_actions
from test_cognitive_encounters import encounter
from test_curriculum_trajectories import load_engine

OXYGEN = "Start oxygen 15 L/min non-rebreather. Reassess in 20 minutes."
LYSE = "Give alteplase 100 mg IV. Reassess in 40 minutes."
FAST = "Give 1000 mL normal saline IV over 10 minutes. Reassess in 12 minutes."
SLOW = "Give 250 mL normal saline IV over 30 minutes. Reassess in 32 minutes."


@pytest.fixture(scope="module")
def engine():
    return load_engine()


def course(engine, orders, variant="pulmonary_embolism_61m"):
    state = encounter(engine, "pulmonary_embolism", variant)["state"]
    events = []
    for order in orders:
        result = execute_family_bundle(state, parse_family_actions(order))
        assert result["executed"], result["clarification"]
        events += result["action_summaries"]
    return state, " | ".join(str(e.get("label", "")) for e in events)


def test_fast_volume_distends_the_ventricle_and_drops_the_output(engine):
    fast, labels = course(engine, [FAST])
    assert fast["family_state"]["rv_strain"] > .3
    assert fast["observable"]["sbp"] < 80 and fast["observable"]["spo2"] < 88
    assert "faster than the obstructed right ventricle can accept" in labels


def test_slow_volume_is_neither_treatment_nor_insult(engine):
    slow, labels = course(engine, [SLOW])
    assert slow["family_state"].get("rv_strain", 0) == 0
    assert "faster than" not in labels
    untouched, _ = course(engine, ["Reassess in 32 minutes."])
    assert slow["observable"]["sbp"] == untouched["observable"]["sbp"]


def test_the_insult_recovers_slowly(engine):
    state, _ = course(engine, [FAST])
    worst = state["observable"]["sbp"]
    execute_family_bundle(state, parse_family_actions("Reassess in 45 minutes."))
    assert state["observable"]["sbp"] > worst
    assert state["family_state"]["rv_strain"] < .2


def test_sustained_hypotension_is_announced_and_is_the_indication(engine):
    state, labels = course(engine, [OXYGEN])
    assert state["family_state"]["sustained_hypotension_min"] >= pe.SUSTAINED_HYPOTENSION_MIN
    assert pe.indicated(state["family_state"])
    assert f"below {pe.HYPOTENSION_SBP} mmHg for {pe.SUSTAINED_HYPOTENSION_MIN} minutes" in labels


def test_thrombolysis_after_sustained_hypotension_dissolves_the_obstruction(engine):
    state, labels = course(engine, [OXYGEN, LYSE, "Reassess in 40 minutes."])
    assert "given for sustained hypotension" in labels
    assert state["family_state"]["circulation"] < .8
    # From 86/54 at arrival, without a vasopressor.
    assert state["observable"]["sbp"] > 98 and state["observable"]["hr"] < 130


def test_thrombolysis_before_the_hypotension_is_sustained_does_nothing(engine):
    state, labels = course(engine, [LYSE, "Reassess in 40 minutes."])
    assert "before the hypotension was sustained" in labels
    assert state["family_state"]["lysis_indicated"] is False
    assert state["family_state"]["circulation"] > 1.0 and state["observable"]["sbp"] < 90


def test_a_normotensive_submassive_embolism_has_no_indication(engine):
    state, labels = course(engine, [LYSE], "pulmonary_embolism_33f")
    assert "before the hypotension was sustained" in labels
    assert not pe.indicated(state["family_state"])
    assert state["family_state"]["circulation"] > 1.0


def test_a_pressure_held_up_by_a_vasopressor_still_counts(engine):
    state, labels = course(engine, [
        "Start oxygen 15 L/min non-rebreather. Start norepinephrine 0.1 mcg/kg/min. Reassess in 20 minutes.",
        LYSE, "Reassess in 40 minutes."])
    assert state["observable"]["sbp"] > 105
    assert "given for sustained hypotension" in labels
    assert state["family_state"]["circulation"] < .8


def test_anticoagulation_alone_does_not_relieve_the_obstruction(engine):
    state, _ = course(engine, ["Start oxygen 15 L/min non-rebreather. Give heparin 5000 units IV. Reassess in 40 minutes.",
                               "Reassess in 60 minutes."])
    assert state["family_state"]["circulation"] > 1.0
    assert state["observable"]["sbp"] < 90


def test_the_indication_does_not_expire_once_met(engine):
    state, _ = course(engine, [OXYGEN, "Start norepinephrine 0.2 mcg/kg/min. Reassess in 30 minutes."])
    assert state["observable"]["sbp"] > pe.HYPOTENSION_SBP
    assert pe.indicated(state["family_state"])
