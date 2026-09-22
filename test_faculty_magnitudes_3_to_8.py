"""The four magnitude decisions: the ceiling, the short opioid, volume and thiamine.

Faculty decisions 3, 3b, 4 and 8 of 2026-09-21, answered in full after the bank
review. Together they say: a patient treated in time ends better than they
arrived; concentration is not effect; volume answers to the haemodynamics and
not to a nitrate; and an ordered dose is not a received dose.
"""
import pytest

import acs_reperfusion
import glucose_rescue
import opioid_reversal
import preload_response


# 3 · Better than arrival

def test_the_recovery_runs_past_the_state_the_patient_arrived_in():
    # Arrival is the patient's own baseline plus the acute event, so the wall
    # that comes back takes them past what the case described on arrival.
    assert acs_reperfusion.CIRCULATION_BASELINE < 1.0


# 3b · Concentration is not effect

def test_the_patient_recovers_before_the_drug_is_gone():
    free = opioid_reversal.VENTILATION_THRESHOLD - .01
    assert opioid_reversal.suppression({"opioid": free, "naloxone": 0}) == 0.0
    assert free > 0, "and there is still drug on board"


def test_breathing_comes_back_before_consciousness_does():
    # The antidote is titrated to ventilation, so ventilation is the less
    # sensitive of the two: a patient can breathe well and still be too drowsy.
    assert opioid_reversal.VENTILATION_THRESHOLD > opioid_reversal.CONSCIOUSNESS_THRESHOLD
    free = (opioid_reversal.VENTILATION_THRESHOLD + opioid_reversal.CONSCIOUSNESS_THRESHOLD) / 2
    state = {"opioid": free, "naloxone": 0}
    assert opioid_reversal.suppression(state) == 0.0
    assert opioid_reversal.sedation(state) > 0.0


def test_an_oral_dose_is_still_arriving_when_the_patient_does():
    from clinical_cases import variant_by_id
    case = variant_by_id("opioid_35m")
    assert case["engine"]["opioid_depot"] > 0
    # The depot enters over about twenty minutes, so the concentration climbs
    # before it falls.
    assert 0 < opioid_reversal.ABSORPTION_PER_MIN < .2


# 4 · Volume answers to the haemodynamics

def test_the_right_ventricle_answers_and_the_failing_left_one_much_less():
    rv = {"rv_involvement": True, "territory": "inferior"}
    lv = {"territory": "left_main"}
    assert (preload_response.PRELOAD_SHARE[preload_response.profile(rv)]
            > preload_response.PRELOAD_SHARE[preload_response.profile(lv)])
    assert (preload_response.TOLERANCE_ML[preload_response.profile(rv)]
            > preload_response.TOLERANCE_ML[preload_response.profile(lv)])


def test_the_benefit_does_not_depend_on_having_had_a_nitrate():
    # The old model only rescued a nitrate-induced fall; nothing here asks
    # whether nitroglycerin was ever given.
    state = {"family_state": {"circulation": 1.2, "fluid_delivered_ml": 0.0, "lung": 1.0}}
    before = state["family_state"]["circulation"]
    preload_response.step(state, {"rv_involvement": True, "territory": "inferior"}, 500)
    assert state["family_state"]["circulation"] < before


def test_each_further_bolus_buys_less_and_then_costs_the_lung():
    spec = {"rv_involvement": True, "territory": "inferior"}
    fresh = {"family_state": {"circulation": 1.2, "fluid_delivered_ml": 0.0, "lung": 1.0}}
    loaded = {"family_state": {"circulation": 1.2,
                               "fluid_delivered_ml": preload_response.TOLERANCE_ML["rv"] * .8, "lung": 1.0}}
    preload_response.step(fresh, spec, 250)
    preload_response.step(loaded, spec, 250)
    assert (1.2 - fresh["family_state"]["circulation"]) > (1.2 - loaded["family_state"]["circulation"])
    over = {"family_state": {"circulation": 1.2, "lung": 1.0,
                             "fluid_delivered_ml": preload_response.TOLERANCE_ML["rv"] + 300}}
    event = preload_response.step(over, spec, 250)
    assert over["family_state"]["lung"] > 1.0
    assert "past what this ventricle is carrying" in event


# 8 · An ordered dose is not a received dose

def test_a_line_that_is_not_in_the_vein_delivers_almost_nothing():
    failed = {"iv_access_failed": True}
    assert glucose_rescue.delivered_share(failed, "IV") < .25
    assert glucose_rescue.delivered_share(failed, "PO") == 1.0
    assert glucose_rescue.delivered_share({}, "IV") == 1.0


def test_the_failed_line_is_visible_and_not_hidden():
    assert "forearm swells" in glucose_rescue.FAILED_ACCESS_TEXT
    assert "reaches the circulation" in glucose_rescue.NEW_ACCESS_TEXT


def test_glucagon_depends_on_a_liver_that_has_something_to_mobilise():
    assert 0 < glucose_rescue.DEPLETED_GLYCOGEN_SHARE < 1
    from clinical_cases import variant_by_id
    assert variant_by_id("hypoglycemia_54m_thiamine")["engine"]["glycogen_depleted"] is True


def test_the_encephalopathy_that_was_retired_is_gone():
    # Faculty decision 8: a thiamine deficiency is a reason to give thiamine and
    # never a reason for the patient to stay confused once the glucose arrives.
    assert not hasattr(glucose_rescue, "wernicke_share")
    assert not hasattr(glucose_rescue, "WERNICKE_TEXT")
