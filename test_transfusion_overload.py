"""Transfusing a patient who is not anaemic (faculty question 2026-09-20).

A unit is about 300 mL that arrives quickly and stays in the vessels, so in a patient
with no oxygen-carrying deficit the volume goes to the lungs. The consequence modelled
is circulatory overload: the common, teachable one. A febrile reaction is frequent but
random, and this engine is deterministic.
"""
import pytest

from family_engine import TRANSFUSION, current_findings, execute_family_bundle, transfusion_overload
from family_parser import parse_family_actions
from test_cognitive_encounters import encounter
from test_curriculum_trajectories import load_engine

TWO_UNITS = "Transfuse 2 units packed red blood cells over 30 minutes. Reassess in 40 minutes."


@pytest.fixture(scope="module")
def engine():
    return load_engine()


def course(engine, family, variant, orders):
    state = encounter(engine, family, variant)["state"]
    events = []
    for order in orders:
        result = execute_family_bundle(state, parse_family_actions(order))
        assert result["executed"], result["clarification"]
        events += result["action_summaries"]
    return state, " | ".join(str(e.get("label", "")) for e in events)


def test_transfusing_a_patient_who_is_not_anaemic_overloads_them(engine):
    state, labels = course(engine, "acs", "acs_54m_inferior", [TWO_UNITS])
    assert transfusion_overload(state) > 1.5
    assert "circulatory overload" in labels
    assert state["observable"]["spo2"] <= 90 and state["observable"]["respiratory_rate"] >= 28
    assert "crackles since the transfusion" in current_findings(state)["Respiratory"]


def test_an_indicated_transfusion_carries_no_penalty(engine):
    state, labels = course(engine, "gi_bleed", "gi_bleed_57m",
                           ["Transfuse 2 units packed red blood cells over 60 minutes. Reassess in 60 minutes."])
    assert transfusion_overload(state) == 0
    assert "circulatory overload" not in labels
    assert state["observable"]["spo2"] >= 96


def test_the_threshold_is_the_haemoglobin_not_the_diagnosis(engine):
    """Half-corrected anaemia is still anaemia; a normal haemoglobin is not."""
    corrected, _ = course(engine, "gi_bleed", "gi_bleed_57m", [
        "Transfuse 4 units packed red blood cells over 60 minutes. Reassess in 70 minutes.",
        "Transfuse 2 units packed red blood cells over 30 minutes. Reassess in 40 minutes."])
    assert corrected["family_state"]["hemoglobin"] >= TRANSFUSION["unnecessary_above_g_dl"]
    assert transfusion_overload(corrected) > 0


def test_it_builds_over_half_an_hour(engine):
    state, _ = course(engine, "acs", "acs_54m_inferior",
                      ["Transfuse 2 units packed red blood cells over 10 minutes. Reassess in 12 minutes."])
    early = transfusion_overload(state)
    execute_family_bundle(state, parse_family_actions("Reassess in 25 minutes."))
    assert transfusion_overload(state) > early
    assert TRANSFUSION["onset_min"] == 30


def test_a_diuretic_treats_it(engine):
    state, _ = course(engine, "acs", "acs_54m_inferior", [TWO_UNITS])
    loaded = state["observable"]["spo2"]
    execute_family_bundle(state, parse_family_actions("Give furosemide 40 mg IV. Reassess in 30 minutes."))
    assert transfusion_overload(state) < 1.6
    assert state["observable"]["spo2"] > loaded


def test_a_wet_lung_tolerates_it_worse(engine):
    congested, _ = course(engine, "pulmonary_edema", "pulmonary_edema_75f",
                          ["Transfuse 1 unit packed red blood cells over 30 minutes. Reassess in 35 minutes."])
    dry, _ = course(engine, "acs", "acs_54m_inferior",
                    ["Transfuse 1 unit packed red blood cells over 30 minutes. Reassess in 35 minutes."])
    assert transfusion_overload(congested) > transfusion_overload(dry)
