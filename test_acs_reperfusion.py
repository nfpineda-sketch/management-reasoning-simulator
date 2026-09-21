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
    """Every text the resident is shown: the order labels and the pathway entries."""
    return " | ".join(str(e.get("label", "")) + " " + str(e.get("pathway_note") or "") for e in events)


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


WELLENS = "acs_48m_wellens"
POSTERIOR = "acs_61m_posterior"
DE_WINTER = "acs_52m_de_winter"
LEFT_MAIN = "acs_70f_left_main"


@pytest.mark.parametrize("variant, profile", [
    (POSTERIOR, "posterior_infarct"), (DE_WINTER, "de_winter"),
    (WELLENS, "wellens"), (LEFT_MAIN, "diffuse_st_depression_avr"),
])
def test_each_equivalent_case_carries_its_morphology(engine, variant, profile):
    state = encounter(engine, "acs", variant)["state"]
    case = state["encounter_spec"]["clinical_case"]
    assert case["ecg_profile"] == profile
    assert case["engine"]["coronary"]["omi"] is True
    # The handover never names the pattern: the resident reads the tracing.
    assert profile.split("_")[0] not in case["presentation"].lower()


@pytest.mark.parametrize("variant", [POSTERIOR, DE_WINTER, LEFT_MAIN])
def test_an_untreated_equivalent_infarcts_like_any_occlusion(engine, variant):
    state, events = course(engine, [ASPIRIN, "Reassess in 60 minutes."], variant)
    assert state["family_state"]["ischemic_min"] == 80
    assert state["family_state"]["lv_function"] < acs.ARRIVAL_LV
    opened, _ = course(engine, ["Activate the cath lab. Reassess in 95 minutes."], variant)
    assert acs.is_open(opened["family_state"])
    assert opened["ecg_profile"] == acs.RESOLVED_PROFILE


def test_wellens_does_not_infarct_while_the_resident_watches(engine):
    state, _ = course(engine, [ASPIRIN, "Reassess in 60 minutes.", "Reassess in 60 minutes."], WELLENS)
    f = state["family_state"]
    assert f.get("ischemic_min") is None and f.get("vf_at") is None
    assert state["observable"]["sbp"] > 120 and state["observable"]["pulse_present"] is True


def test_wellens_still_demands_angiography_and_forbids_provocation(engine):
    scheduled, events = course(engine, ["Activate the cath lab. Reassess in 95 minutes."], WELLENS)
    assert "angiography is scheduled" in labels(events)
    assert "rules out provocation testing" in labels(events)
    assert "stented before it occluded" in labels(events)
    assert scheduled["ecg_profile"] == acs.RESOLVED_PROFILE
    tested, test_events = course(engine, ["Order a stress test. Reassess in 12 minutes."], WELLENS)
    assert tested["family_state"]["vf_at"] is not None
    assert tested["observable"]["pulse_present"] is False


def test_the_left_main_pattern_is_treated_as_an_occlusion(engine):
    state, _ = course(engine, [ASPIRIN, "Reassess in 60 minutes.", "Reassess in 60 minutes."], LEFT_MAIN)
    assert state["family_state"]["vf_at"] is not None


def test_only_the_inferior_territory_blocks_the_av_node(engine):
    state, _ = course(engine, [ASPIRIN, "Reassess in 60 minutes."], DE_WINTER)
    assert state["family_state"].get("av_block_at") is None
    assert state["observable"]["rhythm"] != "Complete AV block"


# Faculty decision 2026-09-21: where the left ventricle is the problem, its
# contractility is paired to the pressure and the perfusion. Opening the artery
# recovered the wall on POCUS while the circulation kept sliding, so a textbook
# door-to-balloon left the patient drifting towards shock for hours and the only
# reward was an isolated ultrasound finding.

def trajectory(engine, case_id, first, waits=5, step=40):
    from family_engine import execute_family_bundle
    from family_parser import parse_family_actions
    state = encounter(engine, "acs", case_id)["state"]
    rows = []
    for order in [first] + [f"Reassess in {step} minutes."] * waits:
        result = execute_family_bundle(state, parse_family_actions(order))
        if not result["executed"]:
            break
        rows.append((state["sim_time"], dict(state["observable"]), dict(state["family_state"])))
    return state, rows


ACTIVATE = "Activate the cath lab. Give aspirin 300 mg PO. Reassess in 20 minutes."


def test_the_pressure_follows_the_ventricle_back(engine):
    state, rows = trajectory(engine, "acs_54m_inferior", ACTIVATE)
    opened = [row for row in rows if row[2].get("artery_open_at") is not None]
    assert opened, [row[0] for row in rows]
    first, last = opened[0], opened[-1]
    # The wall recovers...
    assert last[2]["lv_function"] > first[2]["lv_function"]
    # ...and so do the pressure and the capillary refill, which used to slide.
    assert last[1]["sbp"] > first[1]["sbp"]
    assert last[1]["crt"] < first[1]["crt"]
    assert last[2]["circulation"] < first[2]["circulation"]


def test_the_recovery_stops_at_the_state_the_case_described(engine):
    _, rows = trajectory(engine, "acs_61m_posterior", ACTIVATE, waits=20, step=60)
    assert min(row[2]["circulation"] for row in rows) >= acs.CIRCULATION_ARRIVAL


def test_an_artery_that_stays_closed_still_deteriorates(engine):
    _, rows = trajectory(engine, "acs_54m_inferior", "Give aspirin 300 mg PO. Reassess in 20 minutes.")
    assert rows[-1][2]["circulation"] > rows[0][2]["circulation"]
    assert rows[-1][1]["sbp"] < rows[0][1]["sbp"] or rows[-1][2].get("vf_at")


def test_a_lesion_that_never_occluded_keeps_its_normal_ventricle(engine):
    # Wellens: stented before it closed, so there is no wall to recover and
    # nothing for the circulation to repay.
    _, rows = trajectory(engine, "acs_48m_wellens", ACTIVATE, waits=5, step=40)
    assert all(row[2].get("lv_function") is None for row in rows)
    assert rows[-1][2]["circulation"] == pytest.approx(acs.CIRCULATION_ARRIVAL)
    assert rows[-1][1]["sbp"] == rows[0][1]["sbp"]


def test_the_ratio_is_the_one_the_occlusion_used(engine):
    # What the artery took per minute is what the recovery gives back per unit
    # of ventricle, so a wall returning to its arrival value returns the patient
    # to the circulation they arrived with.
    rv = acs.circulation_per_lv({"rv_involvement": True})
    plain = acs.circulation_per_lv({})
    assert rv == (acs.RV_CIRCULATION_PER_MIN + acs.FAMILY_DRIFT_PER_MIN) / acs.LV_LOSS_PER_MIN
    assert plain == (acs.CIRCULATION_PER_MIN + acs.FAMILY_DRIFT_PER_MIN) / acs.LV_LOSS_PER_MIN
    assert rv > plain


# Faculty decision 2026-09-21: the authored troponin sets the clock, not a floor.
# Found playing the left main case: serial samples read 260, 260, 260 for a
# hundred minutes with the artery shut, because the curve had not yet caught up
# with the value the case was written with. The sickest of the six gave the
# most silent curve.

@pytest.mark.parametrize("case_id", ["acs_54m_inferior", "acs_61m_posterior",
                                     "acs_52m_de_winter", "acs_70f_left_main"])
def test_the_authored_value_is_the_arrival_sample_and_it_moves(engine, case_id):
    from clinical_cases import FAMILIES
    variant = next(v for v in FAMILIES["acs"]["variants"] if v["id"] == case_id)
    spec = variant["engine"]["coronary"]
    authored = variant["investigations"]["troponin"]["result"]["value_ng_l"]
    onset = spec.get("symptom_onset_min", 0)
    arrival = acs.troponin({"elapsed": 0, "ischemic_min": 0}, authored, onset, spec)
    assert arrival == authored
    previous = arrival
    for minute in (15, 30, 60, 90):
        value = acs.troponin({"elapsed": minute, "ischemic_min": minute}, authored, onset, spec)
        assert value > previous, (case_id, minute, value, previous)
        previous = value


def test_the_clock_is_where_the_value_sits_on_the_curve():
    for minutes, value in acs.TROPONIN_CURVE:
        assert acs.curve_minute(value) == pytest.approx(minutes)
    # Between points it interpolates the same way the curve does.
    assert acs._curve(acs.curve_minute(260)) == pytest.approx(260, rel=.01)


@pytest.mark.parametrize("case_id", ["acs_66f_nonst", "acs_48m_wellens"])
def test_nothing_moves_without_an_artery_that_is_shut(engine, case_id):
    from clinical_cases import FAMILIES
    variant = next(v for v in FAMILIES["acs"]["variants"] if v["id"] == case_id)
    spec = variant["engine"].get("coronary") or {}
    authored = variant["investigations"]["troponin"]["result"]["value_ng_l"]
    for minute in (0, 60, 180):
        assert acs.troponin({"elapsed": minute, "ischemic_min": minute}, authored,
                            spec.get("symptom_onset_min", 0), spec) == authored


def test_the_washout_still_multiplies_after_reperfusion(engine):
    from clinical_cases import FAMILIES
    variant = next(v for v in FAMILIES["acs"]["variants"] if v["id"] == "acs_61m_posterior")
    spec = variant["engine"]["coronary"]
    authored = variant["investigations"]["troponin"]["result"]["value_ng_l"]
    closed = acs.troponin({"elapsed": 90, "ischemic_min": 90}, authored, 0, spec)
    opened = acs.troponin({"elapsed": 90, "ischemic_min": 90, "artery_open_at": 90}, authored, 0, spec)
    assert opened == pytest.approx(closed * acs.TROPONIN_WASHOUT_FACTOR, rel=.01)
