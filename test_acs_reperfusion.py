"""The ACS pathway the ECG dictates (faculty decision 2026-09-19).

Faculty: in ACS with ST elevation the cath lab is activated to open the artery; in
ACS without it management is different and immediate angiography is not required;
and the electrocardiographic equivalents of an occlusion must be studied
aggressively even without ST elevation. Door to balloon under 90 minutes with a
cath lab, 120 with transfer, and thrombolysis when a delay beyond 120 is
anticipated. A stress test on an unstable occlusion fibrillates.
"""
import pytest

import acs_reperfusion as acs
from family_engine import execute_family_bundle
from family_parser import parse_family_actions
from test_cognitive_encounters import encounter
from test_curriculum_trajectories import load_engine

ASPIRIN = "Give aspirin 300 mg PO. Reassess in 20 minutes."
ACTIVATE = "Activate the cath lab. Reassess in 30 minutes."


@pytest.fixture(scope="module")
def engine():
    return load_engine()


def course(engine, orders, variant="acs_54m_inferior"):
    state = encounter(engine, "acs", variant)["state"]
    events = []
    for order in orders:
        result = execute_family_bundle(state, parse_family_actions(order))
        assert result["executed"], result["clarification"]
        events += result["action_summaries"]
    return state, events


def labels(events):
    return " | ".join(str(e.get("label", "")) for e in events)


@pytest.mark.parametrize("text, expected", [
    ("Order a stress test.", {"type": "stress_test"}),
    ("Pide un test de esfuerzo.", {"type": "stress_test"}),
    ("Give tenecteplase 40 mg IV.", {"type": "thrombolysis", "agent": "tenecteplase", "dose_mg": 40.0, "route": "IV"}),
    ("Administra tenecteplasa 40 mg IV.", {"type": "thrombolysis", "agent": "tenecteplase", "dose_mg": 40.0, "route": "IV"}),
])
def test_the_new_orders_are_parsed(text, expected):
    assert parse_family_actions(text)["actions"] == [expected]


def test_activating_the_cath_lab_opens_the_artery_at_the_door_to_balloon_time(engine):
    state, events = course(engine, [ASPIRIN, ACTIVATE, "Reassess in 70 minutes."])
    assert f"door to balloon {acs.DOOR_TO_BALLOON_MIN} minutes" in labels(events)
    f = state["family_state"]
    assert acs.is_open(f)
    assert f["artery_open_at"] == 20 + acs.DOOR_TO_BALLOON_MIN
    # The resident who repeats the ECG sees the injury current resolve.
    assert state["ecg_profile"] == acs.RESOLVED_PROFILE
    assert "artery is open after percutaneous coronary intervention" in labels(events)


def test_delay_costs_troponin_and_wall_motion(engine):
    early, _ = course(engine, [ASPIRIN, ACTIVATE, "Order troponin and POCUS. Reassess in 70 minutes."])
    late, _ = course(engine, [ASPIRIN, "Reassess in 60 minutes.", "Order troponin and POCUS. Reassess in 30 minutes."])
    assert late["diagnostics"]["troponin"]["value_ng_l"] > early["diagnostics"]["troponin"]["value_ng_l"]
    assert late["family_state"]["lv_function"] < early["family_state"]["lv_function"]
    assert "reduced contraction" in late["diagnostics"]["pocus"]["lv"] or "akinetic" in late["diagnostics"]["pocus"]["lv"]


def test_an_inferior_infarct_blocks_the_av_node_before_it_fibrillates(engine):
    state, events = course(engine, [ASPIRIN, "Reassess in 30 minutes."])
    assert state["family_state"]["av_block_at"] == acs.AV_BLOCK_AT_MIN
    assert state["observable"]["rhythm"] == "Complete AV block"
    assert state["observable"]["hr"] == acs.AV_BLOCK_RATE
    assert "atrioventricular block" in labels(events)


def test_two_hours_of_occlusion_end_in_ventricular_fibrillation(engine):
    state, events = course(engine, [ASPIRIN, "Reassess in 60 minutes.", "Reassess in 60 minutes."])
    assert state["family_state"]["vf_at"] is not None
    assert state["observable"]["pulse_present"] is False and state["observable"]["rhythm"] == "VF"
    assert "Ventricular fibrillation" in labels(events)


def test_reperfusion_prevents_the_block_and_the_arrest(engine):
    state, _ = course(engine, ["Activate the cath lab. Reassess in 40 minutes.", "Reassess in 90 minutes."])
    f = state["family_state"]
    assert acs.is_open(f) and f.get("vf_at") is None
    assert state["observable"]["pulse_present"] is True
    assert f["lv_function"] > acs.SHOCK_LV


def test_thrombolysis_opens_the_artery_an_hour_after_it_is_given(engine):
    state, events = course(engine, ["Give tenecteplase 40 mg IV. Reassess in 70 minutes."])
    assert state["family_state"]["reperfusion_method"] == "thrombolysis"
    assert state["family_state"]["artery_open_at"] == acs.THROMBOLYSIS_TO_REPERFUSION_MIN
    assert "artery is open after thrombolysis" in labels(events)


def test_a_stress_test_on_an_unstable_occlusion_fibrillates(engine):
    state, events = course(engine, ["Order a stress test. Reassess in 12 minutes."])
    assert state["family_state"]["vf_at"] is not None
    assert "stress test on an unstable occlusion" in labels(events)


def test_the_non_occlusion_case_is_not_pushed_to_the_cath_lab(engine):
    state, events = course(engine, [ASPIRIN, ACTIVATE, "Order troponin and POCUS. Reassess in 60 minutes."],
                           "acs_66f_nonst")
    assert "immediate angiography is not required" in labels(events)
    f = state["family_state"]
    assert f.get("reperfusion_at") is None and f.get("ischemic_min") is None
    # Its troponin and its authored wall motion do not move, and nothing arrests.
    assert state["diagnostics"]["troponin"]["value_ng_l"] == 180
    assert "inferolateral" in state["diagnostics"]["pocus"]["lv"]
    assert state["observable"]["pulse_present"] is True


def test_a_stress_test_without_an_occlusion_is_merely_uninformative(engine):
    state, events = course(engine, ["Order a stress test. Reassess in 12 minutes."], "acs_66f_nonst")
    assert state["family_state"].get("vf_at") is None
    assert "no ischaemic change" in labels(events)


def test_thrombolysis_without_an_occlusion_is_recorded_as_a_bleeding_risk(engine):
    state, events = course(engine, ["Give tenecteplase 40 mg IV. Reassess in 20 minutes."], "acs_66f_nonst")
    assert "without an artery to open" in labels(events)
    assert state["family_state"].get("reperfusion_at") is None


def test_nitroglycerin_collapses_the_right_ventricular_infarct_and_volume_rescues_it(engine):
    state, _ = course(engine, ["Start nitroglycerin at 20 mcg/min. Reassess in 10 minutes."])
    assert state["observable"]["sbp"] < 75 and state["family_state"]["nitrate_drop"] > 20
    execute_family_bundle(state, parse_family_actions(
        "Stop the nitroglycerin. Give 500 mL normal saline IV over 10 minutes. Reassess in 12 minutes."))
    assert state["family_state"]["nitrate_drop"] == 0
    assert state["observable"]["sbp"] > 90


def test_nitroglycerin_is_ordinary_in_the_case_without_right_ventricular_involvement(engine):
    state, _ = course(engine, ["Start nitroglycerin at 20 mcg/min. Reassess in 10 minutes."], "acs_66f_nonst")
    assert state["family_state"].get("nitrate_drop", 0) == 0
    assert state["observable"]["sbp"] > 130
