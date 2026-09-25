"""A fluid's rate is the resident's when written, and the simulator's rule when not.

Faculty decision 5 of 2026-09-25 ("Líquidos sin verbo: mantener A"). "SF 1000
mL EV" is a recognisable order and runs. When no rate is written, running it as
a bolus is the simulator's rule, and the record says so: an unwritten rate is
never presented as one the resident declared. A rate the resident did write
("a 125 ml/h") is read and kept -- it used to hide the volume and hold the
order. Order, hypothesis, condition and negation stay distinct.
"""
import pytest

from family_engine import execute_family_bundle
from family_parser import parse_family_actions
from test_cognitive_encounters import encounter
from test_curriculum_trajectories import load_engine


@pytest.fixture(scope="module")
def engine():
    return load_engine()


@pytest.fixture
def state(engine):
    return encounter(engine, "gi_bleed", "gi_bleed_57m")["state"]


def run(state, order):
    return execute_family_bundle(state, parse_family_actions(order))


def test_no_rate_written_is_a_bolus_by_the_simulator_s_rule(state):
    result = run(state, "SF 1000 ml ev")
    [summary] = [s for s in result["action_summaries"] if s["type"] == "fluid"]
    assert "as a bolus (no rate written; the simulator's standard rate" in summary["label"]
    assert summary["rate_basis"] == "simulator_default"


def test_a_written_duration_is_the_resident_s(state):
    result = run(state, "Paso SF 500 ml ev en 60 minutos")
    [summary] = [s for s in result["action_summaries"] if s["type"] == "fluid"]
    assert "started over 60 min" in summary["label"] and summary["rate_basis"] == "declared"
    assert "no rate written" not in summary["label"]


def test_a_written_rate_is_read_and_kept(state):
    [fluid] = parse_family_actions("SF 500 ml ev a 500 ml/h")["actions"]
    assert (fluid["volume_ml"], fluid["rate_ml_h"], fluid["administration_duration_min"]) == (500.0, 500.0, 60.0)
    result = run(state, "SF 500 ml ev a 500 ml/h")
    [summary] = [s for s in result["action_summaries"] if s["type"] == "fluid"]
    assert summary["rate_basis"] == "declared" and summary["rate_ml_h"] == 500.0


def test_a_rate_the_simulator_cannot_run_is_said_as_such(state):
    result = run(state, "SF 1000 ml ev a 125 ml/h")
    assert not result.get("executed")
    assert result["clarification"].startswith("1000 mL at 125 mL/h would run for 8.0 h")


@pytest.mark.parametrize("text, runs", [
    ("SF 1000 ml ev", True),                        # an order
    ("No doy SF 1000 ml ev", False),                # a negation
    ("Consideraria SF 1000 ml ev si baja la PA", False),   # a hypothesis
    ("Si baja la PA, SF 500 ml ev", False),         # a condition, kept as a plan
])
def test_order_hypothesis_condition_and_negation_stay_distinct(text, runs):
    fluids = [a for a in parse_family_actions(text)["actions"] if a["type"] == "fluid"]
    assert bool(fluids) is runs
