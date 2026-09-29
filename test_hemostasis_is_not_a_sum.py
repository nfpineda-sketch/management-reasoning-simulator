"""TD-31 (faculty, 2026-09-29): measures on one external source are not added up.

Repeating, maintaining or rewording direct pressure adds no control, and packing with
pressure is one intervention: neither reaches what a tourniquet does. The magnitudes
stay as they were (pressure and packing .75, tourniquet 1.0) and only a more effective
technique raises the control. The record says whether the bleeding was reduced or
stopped, and nothing in the scoring reads the level.
"""
import pytest

import language
import rubric_screening
import trauma_hemorrhage as th
from family_engine import execute_family_bundle
from family_parser import parse_family_actions
from test_cognitive_encounters import encounter
from test_curriculum_trajectories import load_engine

PRESSURE = "Apply direct pressure to the left thigh wound."
TOURNIQUET = "Apply a tourniquet to the left thigh."
REDUCED = "the external bleeding is reduced, not stopped"
NO_GAIN = "the external bleeding stays reduced, not stopped; this adds no control to what is already applied"


@pytest.fixture(scope="module")
def engine():
    return load_engine()


def course(engine, orders):
    state = encounter(engine, "trauma", "trauma_limb_hemorrhage_27m")["state"]
    said = []
    for order in orders:
        result = execute_family_bundle(state, parse_family_actions(order))
        assert result["executed"], result["clarification"]
        said += [s["label"] for s in result["action_summaries"] if s.get("type") == "hemorrhage_control"]
    return state, said


def control(state):
    return th.controlled(state["family_state"], "external")


def bleeding(state):
    return th.bleeding_ml_per_min(state["family_state"], state)


@pytest.mark.parametrize("again", ["Maintain direct pressure on the wound.", "Hold firm pressure on the thigh wound.",
                                   PRESSURE])
def test_pressure_held_again_adds_no_control(engine, again):
    state, said = course(engine, [PRESSURE, again])
    assert control(state) == th.MEASURE_CONTROL["direct pressure"] and bleeding(state) > 0
    assert said[0].endswith(REDUCED) and said[1].endswith(NO_GAIN)


@pytest.mark.parametrize("orders", [["Pack the wound and hold pressure"], ["Pack the wound.", "Apply direct pressure to the wound."]])
def test_packing_with_pressure_is_one_intervention_written_together_or_apart(engine, orders):
    state, said = course(engine, orders)
    assert control(state) == .75 and bleeding(state) > 0
    assert [label.split(": ", 1)[1] for label in said] == [REDUCED, NO_GAIN]


def test_a_more_effective_technique_still_raises_the_control(engine):
    state, said = course(engine, [PRESSURE, TOURNIQUET])
    assert control(state) == 1.0 and bleeding(state) == 0
    assert said[1].endswith("the external bleeding is stopped; until now it was only reduced")


def test_a_tourniquet_alone_stops_it_and_pressure_after_it_changes_nothing(engine):
    state, said = course(engine, [TOURNIQUET, PRESSURE])
    assert control(state) == 1.0 and bleeding(state) == 0
    assert said == ["Tourniquet applied to the limb: the external bleeding is stopped",
                    "Direct pressure applied to the limb: the external bleeding was already stopped"]


def test_the_record_says_reduced_or_stopped_in_both_languages(engine):
    _, said = course(engine, [PRESSURE, "Maintain direct pressure on the wound.", TOURNIQUET, PRESSURE])
    spanish = [language.say(label, "es") for label in said]
    assert spanish == [
        "Compresión directa aplicada en la extremidad: el sangrado externo disminuye, pero no se detiene",
        "Compresión directa aplicada en la herida: el sangrado externo sigue disminuido, sin detenerse; esto no "
        "agrega control a lo ya aplicado",
        "Torniquete aplicado en la extremidad: el sangrado externo se detiene; hasta ahora sólo disminuía",
        "Compresión directa aplicada en la extremidad: el sangrado externo ya estaba detenido"]
    # A record written before keeps its own words.
    assert language.say("Tourniquet applied to the left thigh: the external bleeding is controlled", "es") == (
        "Torniquete aplicado en el muslo izquierdo: el sangrado externo está controlado")


def played(engine, orders):
    """A record whose trace holds what the engine answered to each order."""
    state = encounter(engine, "trauma", "trauma_limb_hemorrhage_27m")["state"]
    trace = []
    for order in orders:
        before = int(state.get("sim_time", 0))
        result = execute_family_bundle(state, parse_family_actions(order))
        trace.append({"execution_status": "executed", "decision_time_min": before,
                      "response_time_min": int(state.get("sim_time", 0)), "learner_input": order,
                      "interpreted_action": [], "action_summaries": result["action_summaries"]})
    return {"payload": {"session": {"management_trace": trace}}}


def test_the_scoring_reads_the_action_never_the_level(engine):
    """Pressure that only reduces the bleeding counts as the control measure it is, as before."""
    def omission(orders):
        rows = rubric_screening.screen_events(played(engine, orders), "trauma_limb_hemorrhage_27m")
        [row] = [r for r in rows if r["event_id"] == "trauma_no_hemorrhage_control"]
        return row["status"]
    assert omission(["Pack the wound and hold pressure"]) == omission([TOURNIQUET]) == "contradicted"
    assert omission([PRESSURE, "Maintain direct pressure on the wound."]) == "contradicted"
    assert omission(["Reassess in 12 minutes."]) == "met"
