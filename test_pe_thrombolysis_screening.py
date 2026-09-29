"""The screening reads why the engine judged a thrombolytic as it did (2026-09-29).

Since the revised criterion every thrombolytic order carries a structured record
of its hemodynamic basis: obstructive shock, sustained hypotension or none. The
screening of pe_unindicated_thrombolysis reads that record; an older record
without it keeps the rule of its own time (the engine's narrative), and is never
read as "no indication". The event, its weight and the faculty's confirmation
are unchanged.
"""
import pytest

import rubric_screening
from family_engine import execute_family_bundle
from family_parser import parse_family_actions
from test_cognitive_encounters import encounter
from test_curriculum_trajectories import load_engine

CASE = "pulmonary_embolism_33f"
LYSE = "Give alteplase 100 mg IV."


@pytest.fixture(scope="module")
def engine():
    return load_engine()


def played(engine, orders, variant=CASE):
    """A record whose trace holds what the engine answered to each order."""
    state = encounter(engine, "pulmonary_embolism", variant)["state"]
    trace = []
    for order in orders:
        before = int(state.get("sim_time", 0))
        result = execute_family_bundle(state, parse_family_actions(order))
        assert result["executed"], result["clarification"]
        trace.append({"execution_status": "executed", "decision_time_min": before,
                      "response_time_min": int(state.get("sim_time", 0)), "learner_input": order,
                      "interpreted_action": [], "action_summaries": result["action_summaries"]})
    return {"payload": {"session": {"management_trace": trace}}}


def lysis_row(record):
    [row] = [r for r in rubric_screening.screen_events(record, CASE) if r["event_id"] == "pe_unindicated_thrombolysis"]
    return row


def synthetic(summary_extra, narrative=None):
    summaries = [{"type": "thrombolysis", "label": "alteplase 100 mg IV given", "duration_min": 5,
                  "agent": "alteplase", "dose_mg": 100, "route": "IV", **summary_extra}]
    if narrative:
        summaries.append({"type": "procedure", "label": narrative, "time_min": 0, "duration_min": 0})
    trace = [{"execution_status": "executed", "decision_time_min": 20, "response_time_min": 25,
              "learner_input": LYSE, "interpreted_action": [], "action_summaries": summaries}]
    return {"payload": {"session": {"management_trace": trace}}}


def test_a_normotensive_patient_given_a_thrombolytic_meets_the_event(engine):
    row = lysis_row(played(engine, [LYSE, "Reassess in 30 minutes."]))
    assert row["status"] == "met"
    assert "no hemodynamic indication" in str(row)


def test_a_vasopressor_she_did_not_need_no_longer_hides_the_event(engine):
    """Before 2026-09-29 a normotensive patient on norepinephrine got a false 'sustained hypotension'."""
    record = played(engine, ["Start norepinephrine 0.1 mcg/kg/min. Reassess in 20 minutes.", LYSE,
                             "Reassess in 30 minutes."])
    labels = str(record)
    assert "sustained hypotension" not in labels.replace("nor sustained hypotension", "")
    assert lysis_row(record)["status"] == "met"


@pytest.mark.parametrize("basis, words", [("obstructive_shock", "obstructive shock"),
                                           ("persistent_hypotension", "sustained hypotension (15 consecutive")])
def test_a_recorded_basis_excludes_the_event(basis, words):
    record = synthetic({"thrombolysis_indication": {"version": 2, "minute": 20, "basis": basis, "data": {}},
                        "indication_basis": basis, "indication_version": 2})
    row = lysis_row(record)
    assert row["status"] == "excluded" and words in str(row)


def test_a_recorded_absence_of_basis_meets_the_event():
    record = synthetic({"thrombolysis_indication": {"version": 2, "minute": 20, "basis": None, "data": {}},
                        "indication_basis": "none", "indication_version": 2})
    assert lysis_row(record)["status"] == "met"


def test_an_old_record_keeps_the_rule_of_its_own_time():
    """Without the new field the engine's narrative decides, as it did: never read as 'no indication'."""
    old_with = synthetic({}, narrative="The systolic pressure has stayed below 90 mmHg for 15 minutes: this is "
                                       "sustained hypotension from the obstruction.")
    assert lysis_row(old_with)["status"] == "excluded"
    old_without = synthetic({})
    assert lysis_row(old_without)["status"] == "met"
