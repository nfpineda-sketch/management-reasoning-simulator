"""Real-engine visual continuity checks, independent of image-provider output.

These verify software state-to-image consistency, not clinical validity of the
underlying physiology or an assertion that a generated photograph is correct.
"""
from copy import deepcopy

import pytest

from encounter_generator import PROFILES, generate_encounter
from patient_appearance import appearance_signature, appearance_state
from test_curriculum_trajectories import load_engine, initialize, execute_turn, PROCEDURE
from visual_observations import visual_observations


@pytest.fixture(scope="module")
def engine():
    return load_engine()


def encounter(engine, profile="volume_limited"):
    return generate_encounter("R1-03", engine["INITIAL_STATE"], seed=17, profile_id=profile)["state"]


def test_every_generated_pilot_starts_with_explicit_uncomfortable_phenotype(engine):
    for profile in PROFILES:
        state = encounter(engine, profile)
        before = deepcopy(state)
        visible = appearance_state(state)
        assert state["encounter_spec"]["visual_profile"]
        assert state["observable"]["peripheral_perfusion"] == "impaired"
        assert visible["mental_status"] == "alert"
        assert visible["expression"] == "uncomfortable"
        assert visible["skin_color"] == "mild pallor"
        assert state == before


def test_engine_warm_distributive_override_preserves_authored_impaired_skin(engine):
    state = encounter(engine)
    # Exercise the engine's existing distributive-warmth branch: peripheral
    # temperature is warm despite an abnormal peripheral-flow surface.
    state["hidden"].update(tissue_perfusion=.5, cardiac_output_index=.3,
                            vasoplegia_severity=.8)
    engine["update_perfusion_surface"](state)
    assert state["observable"]["extremities"] == "Warm"
    assert state["observable"]["peripheral_perfusion"] == "impaired"
    assert appearance_state(state)["skin_color"] == "mild pallor"
    assert appearance_state(state)["expression"] == "uncomfortable"


def test_actual_deterioration_and_partial_recovery_change_visible_contract(engine):
    session = initialize(engine, encounter(engine))
    entry = deepcopy(session.state)
    _, result, _, _ = execute_turn(engine, "Reassess in 20 minutes.")
    assert result["executed"]
    worse = deepcopy(session.state)
    assert worse["observable"]["peripheral_perfusion"] == "severely impaired"
    assert appearance_state(worse)["skin_color"] == "pallor"
    assert appearance_signature(worse) != appearance_signature(entry)

    commands = (
        "Give 500 mL IV crystalloid. I think reduced preload contributes. "
        "My priority is tissue perfusion. I expect improved capillary refill "
        "and blood pressure. Reassess in 5 minutes.",
        "Start norepinephrine at 0.05 mcg/kg/min. I think vasoplegia contributes. "
        "My priority is restoring perfusion. I expect improved blood pressure. "
        "Reassess in 5 minutes.",
        PROCEDURE,
    )
    for command in commands:
        _, result, _, _ = execute_turn(engine, command)
        assert result["executed"]
    recovering = deepcopy(session.state)
    assert recovering["observable"]["peripheral_perfusion"] == "impaired"
    visible = appearance_state(recovering)
    assert visible["skin_color"] == "mild pallor"
    assert visible["mental_status"] == "sedated"
    assert visible["expression"] == "sedated"
    assert appearance_signature(recovering) != appearance_signature(worse)
    # Rendering cannot advance time, change physiology, or rewrite the trace.
    before = deepcopy(session.state)
    visual_observations(session.state)
    appearance_signature(session.state)
    assert session.state == before


def test_executed_sedation_does_not_make_residual_hypoperfusion_look_resolved(engine):
    session = initialize(engine, encounter(engine, "mixed_low_flow"))
    _, result, _, _ = execute_turn(engine, PROCEDURE)
    assert result["executed"]
    assert session.state["treatments"]["procedural_sedations"] == 1
    visible = appearance_state(session.state)
    assert visible["mental_status"] == "sedated"
    assert visible["expression"] == "sedated"
    assert session.state["observable"]["peripheral_perfusion"] == "impaired"
    assert visible["skin_color"] == "mild pallor"


def test_isolated_pressure_rate_and_learner_score_cannot_reward_or_punish_visually(engine):
    state = encounter(engine)
    initial_signature = appearance_signature(state)
    state["observable"].update(sbp=135, dbp=85, hr=75)
    state["assessment"] = {"passed": True, "score": 100}
    assert appearance_signature(state) == initial_signature
    state["observable"].update(sbp=40, dbp=20, hr=220)
    state["assessment"] = {"passed": False, "score": 0}
    assert appearance_signature(state) == initial_signature


def test_actual_arrest_retains_critical_perfusion_despite_temperature_label_change(engine):
    session = initialize(engine, encounter(engine, "mixed_low_flow"))
    for _ in range(6):
        execute_turn(engine, "Reassess in 10 minutes.")
        if session.state["observable"].get("pulse_present") is False:
            break
    o = session.state["observable"]
    assert o["pulse_present"] is False
    assert o["peripheral_perfusion"] == "critical"
    assert o["mental_status"] == "Unresponsive"
    visible = appearance_state(session.state)
    assert visible["skin_color"] == "pallor"
    assert visible["expression"] == "passive"
    assert o["extremities"] == "Mottled/Cold"
    assert visible["mottling"] is True
