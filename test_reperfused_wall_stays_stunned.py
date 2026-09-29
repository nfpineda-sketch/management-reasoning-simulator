"""DF-23 row 6 (faculty, 2026-09-29, B): a reperfused wall stays stunned through the encounter.

The circulation recovers as the model has it, but the wall that was ischaemic is never
described as contracting normally again within the encounter: at best mildly reduced.
Only the words change: lv_function, the circulation, the pressures and the timing are the
same with and without the rule. An encounter started before keeps the reading of its time.
"""
import pytest

import acs_reperfusion as acs
import language
from family_engine import execute_family_bundle
from family_parser import parse_family_actions
from test_cognitive_encounters import encounter
from test_curriculum_trajectories import load_engine

LONG_COURSE = (["Give aspirin 300 mg PO. Activate the cath lab. Reassess in 60 minutes."]
               + ["Reassess in 60 minutes."] * 4 + ["Order POCUS. Reassess in 15 minutes."])


@pytest.fixture(scope="module")
def engine():
    return load_engine()


def played(engine, variant, orders=LONG_COURSE, before_the_rule=False):
    state = encounter(engine, "acs", variant)["state"]
    for number, order in enumerate(orders):
        assert execute_family_bundle(state, parse_family_actions(order))["executed"], order
        if number == 0 and before_the_rule:
            state["family_state"].pop(acs.STUNNED_WALL)   # as an encounter started before the rule
    return state


@pytest.mark.parametrize("variant, now, then", [
    ("acs_54m_inferior", "The inferior wall shows mildly reduced contraction; the other walls contract normally",
     "The inferior wall contracts normally; the other walls contract normally"),
    ("acs_70f_left_main", "Contraction is globally mildly reduced, without a single focal defect",
     "Contraction is globally normal, without a single focal defect"),
])
def test_the_reperfused_wall_is_at_best_mildly_reduced_and_nothing_else_moves(engine, variant, now, then):
    new, old = played(engine, variant), played(engine, variant, before_the_rule=True)
    assert acs.is_open(new["family_state"]) and new["family_state"]["lv_function"] == acs.LV_RECOVERY_CEILING
    assert new["diagnostics"]["pocus"]["lv"] == now
    assert old["diagnostics"]["pocus"]["lv"] == then
    for key in ("lv_function", "circulation", "artery_open_at", "reperfusion_at"):
        assert new["family_state"][key] == old["family_state"][key], key
    assert {k: new["observable"][k] for k in ("sbp", "dbp", "hr", "spo2")} == \
        {k: old["observable"][k] for k in ("sbp", "dbp", "hr", "spo2")}


def test_a_worse_wall_is_described_as_it_is_and_a_closed_artery_is_untouched():
    reperfused = {"lv_function": .62, acs.STUNNED_WALL: True, "artery_open_at": 90}
    assert "moderately reduced" in acs.wall_motion(reperfused, {"territory": "inferior"})
    closed = {"lv_function": .9, acs.STUNNED_WALL: True}
    assert acs.wall_motion(closed, {"territory": "inferior"}).startswith("The inferior wall contracts normally")


def test_the_stunned_wall_is_said_in_spanish():
    stunned = acs.wall_motion({"lv_function": .85, acs.STUNNED_WALL: True, "artery_open_at": 90},
                              {"territory": "inferior"})
    assert language.say(stunned, "es") == ("La pared inferior muestra una contracción levemente disminuida; "
                                           "las demás paredes se contraen normalmente")
