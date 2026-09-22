"""The breathing of an infarct follows the ventricle that is failing.

Found playing the left main case (2026-09-22): the saturation stayed at 94%,
the rate at 26 and the effort at the word the case was authored with, for 230
minutes, through cardiogenic shock, crackles at the bedside and congestion on
the film, and through the reperfusion that resolved it. The ACS family had a
scale for the work of breathing and never a load to put on it.

What wets this lung is the ischaemic left ventricle. A right ventricular
infarct fails forward instead, and must not produce the same picture.
"""
import pytest

import acs_reperfusion
from family_engine import execute_family_bundle
from family_parser import parse_family_actions
from test_cognitive_encounters import encounter
from test_curriculum_trajectories import load_engine

WAIT = "Reassess in {} minutes."
REPERFUSE = ("ST elevation in aVR with diffuse depression, because the left main is occluded. "
             "My priority is to open the artery. Give aspirin 300 mg PO, give heparin 5000 units IV "
             "and activate the cath lab. I expect the vessel to open. Reassess in 20 minutes.")
NIV = ("Crackles with congestion on the film, because the ischaemic pump is loading the lung. "
       "My priority is to unload the ventricle and recruit the lung. Start BiPAP IPAP 14 EPAP 8 "
       "FiO2 50%. I expect less work of breathing. Reassess in 20 minutes.")


@pytest.fixture(scope="module")
def engine():
    return load_engine()


def run(engine, variant, *orders):
    state = encounter(engine, "acs", variant)["state"]
    track = [dict(state["observable"])]
    for order in orders:
        result = execute_family_bundle(state, parse_family_actions(order))
        assert result["executed"], (order, result.get("clarification"))
        track.append(dict(state["observable"]))
    return state, track


def test_the_arrival_still_reads_as_the_case_was_written(engine):
    _, track = run(engine, "acs_70f_left_main")
    assert (track[0]["spo2"], track[0]["respiratory_rate"]) == (94, 26)
    assert track[0]["work_of_breathing"] == "Mildly increased"


def test_the_untreated_left_main_gets_worse_to_look_at(engine):
    _, track = run(engine, "acs_70f_left_main", *[WAIT.format(20)] * 5)
    assert track[-1]["spo2"] < track[0]["spo2"] - 5
    assert track[-1]["respiratory_rate"] > track[0]["respiratory_rate"] + 5
    efforts = [s["work_of_breathing"] for s in track]
    assert "Moderately increased" in efforts, efforts
    # Carrying that load with no support for long enough is reported as fatigue,
    # never as a lower rung of the same ladder.
    assert efforts[-1] == "Exhausted: shallow and ineffective effort", efforts


def test_the_right_ventricle_does_not_wet_the_lung(engine):
    # The inferior case with right ventricular involvement fails forward: its
    # pressure goes, its breathing barely moves.
    state, track = run(engine, "acs_54m_inferior", *[WAIT.format(20)] * 5)
    assert acs_reperfusion.coronary(state)["rv_involvement"] is True
    assert track[0]["spo2"] - track[-1]["spo2"] <= 2
    assert track[-1]["respiratory_rate"] - track[0]["respiratory_rate"] <= 2
    assert track[-1]["sbp"] < track[0]["sbp"] - 15       # the circulation still fails


def test_opening_the_artery_turns_the_breathing_around(engine):
    _, track = run(engine, "acs_70f_left_main", REPERFUSE, *[WAIT.format(20)] * 9)
    spo2 = [s["spo2"] for s in track]
    worst = spo2.index(min(spo2))
    assert 0 < worst < len(spo2) - 1, spo2            # it turns, rather than only falling
    assert spo2[-1] >= min(spo2) + 4, spo2
    assert track[-1]["respiratory_rate"] < max(s["respiratory_rate"] for s in track)
    assert track[-1]["work_of_breathing"] in {"Mildly increased", "Moderately increased"}


def test_positive_pressure_carries_part_of_the_load(engine):
    _, supported = run(engine, "acs_70f_left_main", NIV, *[WAIT.format(20)] * 4)
    _, alone = run(engine, "acs_70f_left_main", *[WAIT.format(20)] * 5)
    assert "Exhausted: shallow and ineffective effort" in [s["work_of_breathing"] for s in alone]
    assert "Exhausted: shallow and ineffective effort" not in [s["work_of_breathing"] for s in supported]


def test_a_coronary_that_is_not_occluding_does_not_drift(engine):
    state, track = run(engine, "acs_66f_nonst", *[WAIT.format(20)] * 5)
    assert acs_reperfusion.coronary(state).get("omi") is not True
    assert track[-1]["spo2"] == track[0]["spo2"]
    assert track[-1]["respiratory_rate"] == track[0]["respiratory_rate"]
    assert track[-1]["work_of_breathing"] == track[0]["work_of_breathing"]


# --- the model itself -------------------------------------------------------

def test_the_load_is_zero_where_the_case_left_the_wall():
    assert acs_reperfusion.congestion_load({}, {"territory": "left_main"}) == 0


def test_an_akinetic_left_main_carries_the_whole_load():
    load = acs_reperfusion.congestion_load(
        {"lv_function": acs_reperfusion.LV_FLOOR}, {"territory": "left_main"})
    assert load == pytest.approx(1.0)


def test_the_recovered_wall_goes_slightly_below_arrival():
    load = acs_reperfusion.congestion_load(
        {"lv_function": acs_reperfusion.LV_RECOVERY_CEILING}, {"territory": "left_main"})
    assert load < 0


def test_every_territory_the_engine_can_name_has_a_share():
    assert set(acs_reperfusion.CONGESTION_TERRITORY) == set(acs_reperfusion.TERRITORY_WALL)


def test_the_right_ventricle_discounts_the_same_wall():
    wall = {"lv_function": .6}
    inferior = acs_reperfusion.congestion_load(wall, {"territory": "inferior"})
    with_rv = acs_reperfusion.congestion_load(wall, {"territory": "inferior", "rv_involvement": True})
    assert with_rv == pytest.approx(inferior * acs_reperfusion.CONGESTION_RV_SHARE)


def test_support_relieves_the_load_and_never_the_recovery():
    failing = {"lv_function": .6}
    spec = {"territory": "left_main"}
    assert acs_reperfusion.congestion_load(failing, spec, niv=True) == pytest.approx(
        acs_reperfusion.congestion_load(failing, spec) * (1 - acs_reperfusion.CONGESTION_RELIEF["niv"]))
    # A wall that has recovered past arrival is not "relieved" back towards it.
    recovered = {"lv_function": acs_reperfusion.LV_RECOVERY_CEILING}
    assert (acs_reperfusion.congestion_load(recovered, spec, invasive=True)
            == acs_reperfusion.congestion_load(recovered, spec))
