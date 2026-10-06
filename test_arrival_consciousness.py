"""DC1 (faculty, 2026-09-29): the consciousness written at arrival is the reference.

Recomputing without a physiological change must not alter it. A real fall in pressure,
saturation or glucose, a seizure, sedation and recovery still move it, and a better
glucose never shows a worse patient.
"""
import pytest

import family_engine
from family_engine import execute_family_bundle
from family_parser import parse_family_actions
from test_cognitive_encounters import VARIANTS, encounter
from test_phase0_time_and_events import keep_waiting
from test_curriculum_trajectories import load_engine

# The five arrivals the engine used to rewrite at minute 1, and their family.
ANCHORED = {"bradycardia_ccb_68m": "bradycardia", "pulmonary_edema_58m": "pulmonary_edema",
            "pulmonary_edema_75f": "pulmonary_edema", "hypoglycemia_28m": "hypoglycemia",
            "hypoglycemia_54m_thiamine": "hypoglycemia"}
RANK = {"Alert": 0, "Drowsy": 1, "Obtunded": 2, "Unresponsive": 3}


@pytest.fixture(scope="module")
def engine():
    return load_engine()


def course(engine, family, variant, orders):
    state = encounter(engine, family, variant)["state"]
    seen = []
    for order in orders:
        result = execute_family_bundle(state, parse_family_actions(order))
        assert result["executed"], result["clarification"]
        # Phase 0 (0F, 2026-10-06): a wait stops at a critical event; this course is about what
        # the whole interval brings, so the resident keeps waiting after each stop.
        keep_waiting(state, result)
        seen.append(state["observable"]["mental_status"])
    return state, seen


@pytest.mark.parametrize("variant", sorted(ANCHORED))
def test_the_first_minutes_show_the_consciousness_written_at_arrival(engine, variant):
    arrival = encounter(engine, ANCHORED[variant], variant)["state"]["observable"]["mental_status"]
    _, seen = course(engine, ANCHORED[variant], variant, ["Reassess in 1 minute."] * 3)
    assert seen == [arrival] * 3


def test_only_the_arrivals_that_needed_it_carry_an_anchor(engine):
    for family, variant in VARIANTS:
        state, _ = course(engine, family, variant, ["Reassess in 1 minute."])
        f = state["family_state"]
        assert bool(f.get("consciousness_anchor") or f.get("glucose_anchor")) == (variant in ANCHORED), variant


def test_only_the_thresholds_the_arrival_already_crossed_move():
    pressure, glucose = ((80.0, 1), (65.0, 2)), ((70.0, 1), (45.0, 2), (25.0, 3))
    # Alert at 74 mmHg: drowsy moves below the arrival, obtunded keeps its place.
    assert family_engine._anchored_levels(pressure, 74, 0) == ((69.5, 1), (65.0, 2))
    # Drowsy at 80 mmHg already agrees with the engine: nothing moves.
    assert family_engine._anchored_levels(pressure, 80, 1) == pressure
    # Drowsy at 32 mg/dL: obtunded moves below 32, unresponsive stays at 25.
    assert family_engine._anchored_levels(glucose, 32, 1) == ((70.0, 1), (28.5, 2), (25.0, 3))
    # With no threshold left below the arrival, the moved ones still sit under it.
    assert all(threshold < 60 for threshold, _ in family_engine._anchored_levels(pressure, 60, 0))


def test_a_value_hovering_at_a_threshold_does_not_flicker():
    levels, previous, seen = ((69.5, 1), (65.0, 2)), 0, []
    for sbp in (70.2, 69.4, 69.6, 69.4, 70.9, 71.6):
        previous = family_engine._level_with_margin(sbp, levels, previous, 2.0)
        seen.append(previous)
    assert seen == [0, 1, 1, 1, 1, 0]


def test_getting_better_than_the_arrival_takes_the_plain_threshold():
    # Drowsy on arrival at 34 mg/dL: awake at 70 like every other patient, while a
    # deterioration to obtunded is left only past its margin.
    levels = ((70.0, 1), (29.5, 2), (25.0, 3))
    assert family_engine._level_with_margin(70.2, levels, 1, 1.0, arrival=1) == 0
    assert family_engine._level_with_margin(30.0, levels, 2, 1.0, arrival=1) == 2
    assert family_engine._level_with_margin(30.6, levels, 2, 1.0, arrival=1) == 1


def test_a_real_fall_in_pressure_still_takes_consciousness_down(engine):
    state, seen = course(engine, "bradycardia", "bradycardia_ccb_68m",
                         ["Reassess in 15 minutes.", "Reassess in 10 minutes.", "Reassess in 10 minutes."])
    assert seen == ["Alert", "Drowsy", "Obtunded"]
    assert state["observable"]["sbp"] < 65


def test_a_real_fall_in_saturation_still_takes_consciousness_down(engine):
    state, seen = course(engine, "pulmonary_edema", "pulmonary_edema_58m", ["Reassess in 35 minutes."])
    assert seen == ["Obtunded"] and state["observable"]["spo2"] < 80


def test_treatment_that_restores_the_cause_keeps_or_returns_the_patient_awake(engine):
    _, seen = course(engine, "bradycardia", "bradycardia_ccb_68m",
                     ["Give calcium chloride 1 g IV. Reassess in 5 minutes.", "Reassess in 10 minutes."])
    assert seen == ["Alert", "Alert"]


def test_sedation_still_steps_consciousness_down(engine):
    _, seen = course(engine, "pulmonary_edema", "pulmonary_edema_58m", ["Give morphine 15 mg IV. Reassess in 5 minutes."])
    assert seen == ["Drowsy"]


def test_a_better_glucose_never_shows_a_worse_patient(engine):
    # A tenth of the ampoule takes 34 to 44 mg/dL. The old reading showed 44 as obtunded,
    # worse than the drowsy arrival at 34.
    _, seen = course(engine, "hypoglycemia", "hypoglycemia_28m",
                     ["Give 5 mL D50 IV. Reassess in 1 minute.", "Reassess in 10 minutes."])
    assert seen == ["Drowsy", "Drowsy"]
    state, _ = course(engine, "hypoglycemia", "hypoglycemia_54m_thiamine", ["Reassess in 1 minute."])
    f, last = dict(state["family_state"]), RANK["Drowsy"]
    for glucose in range(32, 90):
        f["glucose"] = float(glucose)
        level = RANK[family_engine._glucose_consciousness(f)]
        assert level <= last, glucose
        last = level
    assert last == RANK["Alert"]


def test_a_seizure_and_its_post_ictal_state_are_untouched(engine):
    state, seen = course(engine, "hypoglycemia", "hypoglycemia_54m_thiamine", ["Reassess in 5 minutes."] * 7)
    assert state["family_state"]["seizure_at"] == 20
    assert seen[:3] == ["Drowsy"] * 3 and seen[3:6] == ["Unresponsive"] * 3 and seen[6] == "Drowsy"


def test_left_untreated_the_glucose_keeps_falling_and_consciousness_with_it(engine):
    state, seen = course(engine, "hypoglycemia", "hypoglycemia_28m", ["Reassess in 30 minutes.", "Reassess in 30 minutes."])
    assert seen[-1] == "Obtunded" and state["family_state"]["glucose"] < 29.5


def test_an_encounter_started_before_the_rule_keeps_the_rule_it_began_with(engine):
    state, seen = course(engine, "bradycardia", "bradycardia_ccb_68m", ["Reassess in 1 minute."])
    assert seen == ["Alert"]
    for key in ("consciousness_anchor", "glucose_anchor", "anchored_level"):
        state["family_state"].pop(key, None)
    execute_family_bundle(state, parse_family_actions("Reassess in 1 minute."))
    assert state["observable"]["mental_status"] == "Drowsy"
