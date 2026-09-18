"""Gaps found while preparing a hypertensive pulmonary oedema test run.

- An ordered ECG was reported only as "ECG: Performed at minute 0", with no
  pointer to the tracing.
- "Adjust BiPAP IPAP 10 EPAP 5 FiO2 40%" was dropped without a clarification.
- "Stop the normal saline" was read as a new bolus with no volume.
- "Suspende el suero" was not recognized and held the whole turn.
"""
import pytest

from family_parser import parse_family_actions
from family_reports import format_result
from test_coupled_encounter import patient, run
from test_curriculum_trajectories import load_engine
from test_generated_engine import wait
from test_timed_administration import bank, bank_case, ps001


def test_an_ordered_ecg_points_to_the_tracing_without_naming_the_rhythm():
    text = format_result("ecg", {"status": "available", "collected_at_min": 0, "rhythm": "sinus", "heart_rate": 126})
    assert text == "ECG: Performed at minute 0 · 12-lead tracing available in ECG recordings at the bedside."
    assert "sinus" not in text.lower()


def test_an_ecg_that_cannot_be_acquired_says_why():
    text = format_result("ecg", {"status": "unavailable", "reason": "No organized electrical activity.", "collected_at_min": 3})
    assert text == "ECG: Performed at minute 3 · No organized electrical activity."


@pytest.mark.parametrize("text, expected", [
    ("Adjust BiPAP IPAP 10 EPAP 5 FiO2 40%.",
     {"type": "niv", "mode": "BiPAP", "ipap_cmh2o": 10.0, "epap_cmh2o": 5.0, "fio2_percent": 40.0, "operation": "adjust"}),
    ("Reduce nitroglycerin to 100 mcg/min.", {"type": "nitroglycerin", "rate_mcg_min": 100.0, "operation": "adjust"}),
    ("Wean BiPAP to IPAP 10 EPAP 5 FiO2 40%.",
     {"type": "niv", "mode": "BiPAP", "ipap_cmh2o": 10.0, "epap_cmh2o": 5.0, "fio2_percent": 40.0, "operation": "adjust"}),
])
def test_adjust_reduce_and_wean_are_adjustments(text, expected):
    assert parse_family_actions(text)["actions"] == [expected]


def test_a_goal_after_a_priority_is_still_not_an_adjustment():
    assert parse_family_actions("My priority is oxygenation and reduce preload.")["actions"] == []


@pytest.mark.parametrize("text, fluid_type", [
    ("Stop the normal saline.", "normal saline"),
    ("Discontinue the Ringer lactate.", "lactated Ringer's"),
    ("Stop fluids.", None),
    ("Suspende el suero.", None),
    ("Detener el suero fisiológico.", "normal saline"),
])
def test_stopping_a_fluid_is_not_a_new_bolus(text, fluid_type):
    assert parse_family_actions(text)["actions"] == [{"type": "fluid", "operation": "stop", "fluid_type": fluid_type}]


def test_suero_with_a_volume_is_still_a_bolus():
    assert parse_family_actions("Administra 500 mL de suero fisiológico IV.")["actions"] == [
        {"type": "fluid", "volume_ml": 500.0, "fluid_type": "normal saline", "route": "IV"}]


def test_a_bank_case_stops_a_running_timed_bolus_at_what_it_delivered():
    state = bank_case("pneumonia")
    bank(state, "Give 1000 mL normal saline IV over 60 minutes. Reassess in 20 minutes.")
    result = bank(state, "Suspende el suero. Reevalúa en 20 minutos.")
    assert result["executed"], result["clarification"]
    assert [s["label"] for s in result["action_summaries"]] == ["stopping crystalloid (667 mL not given)"]
    assert state["treatments"]["cumulative_crystalloid_ml"] == pytest.approx(333.3, abs=.1)
    assert state["family_state"]["pending_fluid_ml"] == 0 and state["family_state"]["deliveries"] == []


def test_a_bank_case_stops_an_untimed_bolus():
    state = bank_case("pneumonia")
    bank(state, "Give 1000 mL normal saline IV. Reassess in 5 minutes.")
    result = bank(state, "Stop the normal saline. Reassess in 10 minutes.")
    assert [s["label"] for s in result["action_summaries"]] == ["stopping crystalloid (750 mL not given)"]
    assert state["treatments"]["cumulative_crystalloid_ml"] == 250


def test_stopping_further_fluid_when_nothing_runs_is_recorded_without_holding_the_turn():
    # "Stop further fluids" usually means withhold more fluid; the other orders must still run.
    state = bank_case("pneumonia")
    result = bank(state, "Stop further fluids. Give ceftriaxone 2 g IV. Reassess in 5 minutes.")
    assert result["executed"], result["clarification"]
    assert [s["label"] for s in result["action_summaries"]][0] == "withholding further fluid (none was running)"
    assert state["treatments"]["administered_medications"][0]["agent"] == "ceftriaxone"


def test_a_generated_case_closes_the_bag_at_what_it_delivered():
    state = patient()
    run(state, {"type": "fluid", "fluid_type": "normal saline", "volume_ml": 1000, "administration_duration_min": 40}, wait(10))
    result = run(state, {"type": "fluid", "operation": "stop", "fluid_type": "normal saline"}, wait(10))
    assert [s["label"] for s in result["action_summaries"] if s.get("type") == "fluid"] == ["stopping crystalloid (750 mL not given)"]
    assert state["treatments"]["total_crystalloid_ml"] == 250
    assert state["coupled_state"]["treatments"]["cumulative_crystalloid_ml"] == 250
    assert state["family_state"]["pending_fluid_ml"] == 0


@pytest.fixture(scope="module")
def engine():
    return load_engine()


def test_ps001_stops_a_timed_bolus(engine):
    state, results = ps001(engine, "Give 1000 mL normal saline IV over 30 minutes. Reassess in 10 minutes.",
                           "Stop the normal saline. Reassess in 10 minutes.")
    _, stopped = results[1]
    assert [s.get("label") for s in stopped["action_summaries"]] == ["stopping crystalloid (667 mL not given)"]
    assert state["treatments"]["cumulative_crystalloid_ml"] == pytest.approx(333.3, abs=.1)
    assert state["timed_fluids"] == [] and state["sim_time"] == 20


def test_ps001_records_a_stop_when_nothing_runs(engine):
    _, [(_, result)] = ps001(engine, "Stop fluids. Reassess in 5 minutes.")
    assert result["clarification"] is None
    assert [s.get("label") for s in result["action_summaries"]] == ["withholding further fluid (none was running)"]
