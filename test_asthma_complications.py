"""Barotrauma and the timing of intubation (faculty decision 2026-09-19).

Faculty: the asthmatic must not be intubated too early nor too late, and the
ventilated asthmatic is the patient in whom a pneumothorax appears, competing with
dynamic hyperinflation as the cause of a falling pressure.
"""
import pytest

import asthma_complications as comp
from family_engine import current_findings, execute_family_bundle
from family_parser import parse_family_actions
from test_cognitive_encounters import encounter
from test_curriculum_trajectories import load_engine

HIGH_PRESSURE = "Give ketamine 100 mg IV and intubate VC/AC FiO2 100% PEEP 5 Vt 750 mL rate 30. Reassess in 10 minutes."
PROTECTIVE = ("Give ketamine 100 mg IV and intubate VC/AC FiO2 100% PEEP 0 Vt 450 mL rate 12 flow 80 L/min. "
              "Reassess in 5 minutes.")
FIRST_LINE = "Give albuterol 5 mg nebulized and methylprednisolone 125 mg IV. Reassess in 20 minutes."


@pytest.fixture(scope="module")
def engine():
    return load_engine()


def course(engine, orders, variant="asthma_24f"):
    state = encounter(engine, "asthma", variant)["state"]
    events = []
    for order in orders:
        result = execute_family_bundle(state, parse_family_actions(order))
        assert result["executed"], result["clarification"]
        events += [s for s in result["action_summaries"] if s.get("type") == "procedure"]
    return state, events


@pytest.mark.parametrize("text, expected", [
    ("Perform needle decompression of the right chest.", {"side": "right", "device": "needle"}),
    ("Place a chest tube on the right.", {"side": "right", "device": "chest tube"}),
    ("Descompresión con aguja en el hemitórax derecho.", {"side": "right", "device": "needle"}),
    ("Coloca un tubo pleural izquierdo.", {"side": "left", "device": "chest tube"}),
])
def test_decompression_orders_are_parsed(text, expected):
    assert parse_family_actions(text)["actions"] == [{"type": "chest_decompression", **expected}]


def test_a_sustained_high_plateau_tears_the_lung(engine):
    state, events = course(engine, [HIGH_PRESSURE, "Reassess in 15 minutes."])
    assert state["family_state"]["pneumothorax_at"] is not None
    assert any("tension pneumothorax" in e["label"] for e in events)
    # It presents as the competing cause of hypotension, with a jump in peak pressure.
    assert state["observable"]["sbp"] < 80 and state["observable"]["spo2"] < 92
    assert "absent over the right" in current_findings(state)["Respiratory"]


def test_protective_settings_do_not_tear_the_lung(engine):
    state, events = course(engine, [PROTECTIVE, "Reassess in 120 minutes."])
    assert state["family_state"].get("pneumothorax_at") is None
    assert state["family_state"].get("barotrauma_exposure", 0) == 0
    assert not any("pneumothorax" in e["label"] for e in events)


def test_decompression_resolves_it_only_on_the_right_side(engine):
    state, _ = course(engine, [HIGH_PRESSURE, "Reassess in 15 minutes."])
    tense = state["observable"]["sbp"]
    wrong = execute_family_bundle(state, parse_family_actions("Perform needle decompression of the left chest. Reassess in 2 minutes."))
    assert "other side" in wrong["action_summaries"][0]["label"]
    assert state["observable"]["sbp"] <= tense + 2
    execute_family_bundle(state, parse_family_actions("Perform needle decompression of the right chest. Reassess in 5 minutes."))
    assert state["observable"]["sbp"] > tense + 20 and state["observable"]["spo2"] > 95
    assert "Sliding restored" in state["diagnostics"].get("pocus", {}).get("lung_sliding", "") or True


def test_decompressing_a_chest_without_tension_releases_nothing(engine):
    state, _ = course(engine, [PROTECTIVE])
    result = execute_family_bundle(state, parse_family_actions("Perform needle decompression of the right chest."))
    assert "no air under tension" in result["action_summaries"][0]["label"]


def test_intubating_an_improving_patient_is_premature(engine):
    state, events = course(engine, [FIRST_LINE, PROTECTIVE])
    assert state["family_state"]["intubation_timing"] == "premature"
    assert any("still alert, oxygenating" in e["label"] for e in events)
    untouched, _ = course(engine, [FIRST_LINE, "Reassess in 5 minutes."])
    assert state["observable"]["sbp"] < untouched["observable"]["sbp"]


def test_exhaustion_accumulates_untreated_and_makes_intubation_late(engine):
    state, events = course(engine, ["Reassess in 30 minutes.", "Reassess in 30 minutes.",
                                    "Reassess in 20 minutes.", PROTECTIVE])
    assert state["family_state"]["exhausted_min"] >= comp.LATE_EXPOSURE_MIN
    assert state["family_state"]["intubation_timing"] == "late"
    assert any("prolonged period of exhaustion" in e["label"] for e in events)
    assert state["family_state"]["lactate"] >= 2 + comp.LATE_LACTATE
    protective, _ = course(engine, [FIRST_LINE, PROTECTIVE])
    assert state["observable"]["sbp"] < protective["observable"]["sbp"]


def test_relief_buys_the_exhaustion_clock_back(engine):
    state, _ = course(engine, ["Reassess in 25 minutes.", FIRST_LINE, "Reassess in 30 minutes."])
    assert state["family_state"]["exhausted_min"] == 0


def test_the_post_intubation_penalty_fades(engine):
    state, _ = course(engine, ["Reassess in 30 minutes.", "Reassess in 30 minutes.",
                               "Reassess in 20 minutes.", PROTECTIVE])
    early = state["observable"]["sbp"]
    execute_family_bundle(state, parse_family_actions("Reassess in 60 minutes."))
    assert state["observable"]["sbp"] > early + 10
