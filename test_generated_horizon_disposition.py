"""The closing decision of a generated case must be reachable at its horizon.

Found preparing the learner report from the first paid case (2026-09-22). A
generated case declares its own supported time horizon — sixty minutes there.
Two rules then contradicted each other at the end of the encounter: the
reasoning gate requires a reassessment time before any order executes, and the
horizon refused every reassessment once the clock reached it. The disposition
could not be written at all, so the encounter could not be closed.

A disposition is the handover: the variables the resident names are checked in
the receiving unit, not here. The clock therefore stops at the horizon instead
of the order being refused.
"""
import pytest

import coupled_encounter as adapter
from family_parser import parse_family_actions
from generated_engine import execute_generated_bundle
from test_generated_metabolic import build

HORIZON = 60
ADMIT = ("Esta estabilizado con soporte, debido al tratamiento. La prioridad ahora es vigilancia "
         "continua. Hospitalizalo en la unidad de paciente critico. Espero monitorizacion. "
         "Reevalua en 30 minutos presion y diuresis.")
WAIT = "Reevalua en {} minutos la presion y el llene capilar."


def fresh():
    state, _ = build(horizon_min=HORIZON)
    adapter.initialize(state)
    return state


def run(state, text):
    return execute_generated_bundle(state, parse_family_actions(text))


def at_the_horizon():
    state = fresh()
    assert run(state, WAIT.format(HORIZON))["executed"]
    assert state["generated_state"]["elapsed"] == HORIZON
    return state


def test_the_horizon_is_where_the_case_put_it():
    state = at_the_horizon()
    assert state["encounter_spec"]["clinical_case"]["engine"]["horizon_min"] == HORIZON


def test_a_plain_reassessment_past_the_horizon_is_still_refused():
    state = at_the_horizon()
    result = run(state, WAIT.format(10))
    assert not result["executed"]
    assert "horizon" in str(result.get("clarification", "")).lower()


def test_the_closing_disposition_executes_at_the_horizon():
    state = at_the_horizon()
    result = run(state, ADMIT)
    assert result["executed"], result.get("clarification")
    assert any(s.get("type") == "disposition" for s in result["action_summaries"])


def test_the_handover_does_not_run_the_clock_past_the_horizon():
    state = at_the_horizon()
    run(state, ADMIT)
    assert state["generated_state"]["elapsed"] == HORIZON


def test_a_disposition_before_the_horizon_keeps_its_own_clock():
    # Nothing changes for the ordinary case: the interval the resident asked for
    # is the interval that passes.
    state = fresh()
    assert run(state, WAIT.format(10))["executed"]
    assert run(state, ADMIT)["executed"]
    assert state["generated_state"]["elapsed"] == 40


def test_the_bank_vocabulary_reaches_the_generated_engine():
    # The same order, written the way it is written here.
    actions = parse_family_actions(ADMIT)["actions"]
    assert {"type": "disposition", "destination": "ICU"} in actions
