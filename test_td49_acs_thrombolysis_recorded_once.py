"""TD-49 (faculty, 2026-10-02): an ACS thrombolytic dose is listed once among the medicines given.

The ACS branch wrote its own row -- agent, dose, route and minute -- beside the
row every medicine gets, so "Current treatments" and the recorded state showed
each dose twice. The engine acted once all along: reperfusion is activated a
single time, and nothing about the patient changes with this correction.
"""
import pytest

from family_engine import execute_family_bundle
from family_parser import parse_family_actions
from test_cognitive_encounters import encounter
from test_curriculum_trajectories import load_engine

DOSE = "Give tenecteplase 40 mg IV."


@pytest.fixture(scope="module")
def engine():
    return load_engine()


def given(state):
    return [row for row in state["treatments"]["administered_medications"] if row.get("agent") == "tenecteplase"]


@pytest.mark.parametrize("case", ["acs_52m_de_winter", "acs_66f_nonst"])
def test_each_dose_is_one_row_with_what_was_given(engine, case):
    state = encounter(engine, "acs", case)["state"]
    result = execute_family_bundle(state, parse_family_actions(DOSE))
    assert result["executed"], result.get("clarification")
    rows = given(state)
    assert len(rows) == 1
    assert {key: rows[0][key] for key in ("agent", "dose_mg", "route", "time_min")} == {
        "agent": "tenecteplase", "dose_mg": 40.0, "route": "IV", "time_min": 0}
    # A second order is a second row: one per order, never two.
    result = execute_family_bundle(state, parse_family_actions(DOSE))
    assert result["executed"], result.get("clarification")
    assert len(given(state)) == 2


def test_the_reperfusion_is_unchanged(engine):
    state = encounter(engine, "acs", "acs_52m_de_winter")["state"]
    result = execute_family_bundle(state, parse_family_actions(DOSE))
    label = next(s["label"] for s in result["action_summaries"] if s.get("type") != "diagnostic")
    assert "reperfusion is expected at minute" in label
    keys = ("reperfusion_method", "reperfusion_activated_at", "reperfusion_at")
    first = {key: state["family_state"].get(key) for key in keys}
    assert first["reperfusion_method"] == "thrombolysis" and first["reperfusion_at"] is not None
    execute_family_bundle(state, parse_family_actions(DOSE))
    assert {key: state["family_state"].get(key) for key in keys} == first
