"""Dobutamine, the blocked ventricle, and morphine.

Faculty decisions 5, 6 and 10 of 2026-09-21. The bank produced a complete
atrioventricular block with nothing to treat it, refused the classic inotrope
of cardiogenic shock with a message about "a generated encounter", and did not
know the word morphine. Each of the three now exists with its own price.
"""
import pytest

import analgesia
import bradycardia_support as brady
import inotrope_support
from family_parser import parse_family_actions


def actions(text):
    return parse_family_actions(text)["actions"]


def one(text, kind):
    return next((a for a in actions(text) if a.get("type") == kind), None)


# 6 · Dobutamine

@pytest.mark.parametrize("text, rate", [
    ("Inicia dobutamina a 5 mcg/kg/min.", 5.0),
    ("Start dobutamine at 5 mcg/kg/min.", 5.0),
])
def test_dobutamine_is_an_order_in_any_family(text, rate):
    order = one(text, "dobutamine")
    assert order["rate"] == rate and order["operation"] == "start"


def test_the_inotrope_relieves_a_contractile_burden_and_not_an_obstructed_one():
    assert inotrope_support.CONTRACTILE_SHARE["acs"] > inotrope_support.CONTRACTILE_SHARE["pulmonary_embolism"]
    assert inotrope_support.CONTRACTILE_SHARE["acs"] > inotrope_support.CONTRACTILE_SHARE["gi_bleed"]


def test_the_output_gain_saturates_and_the_afterload_fall_does_not():
    five, twenty = inotrope_support._saturating(5), inotrope_support._saturating(20)
    assert five < twenty < inotrope_support.MAX_BURDEN_RELIEF
    assert twenty - five < five  # each further mcg buys less contraction
    state = {"family_state": {"dobutamine": 70 * 5}, "encounter_spec": {}}
    sbp_low, hr_low = inotrope_support.surface(state)
    state["family_state"]["dobutamine"] = 70 * 15
    sbp_high, hr_high = inotrope_support.surface(state)
    assert sbp_high < sbp_low < 0 and hr_high > hr_low > 0  # and costs more rate


# 5 · The blocked ventricle

def test_atropine_and_pacing_are_orders():
    assert one("Administra atropina 1 mg IV.", "atropine")["dose_mg"] == 1.0
    pacing = one("Instala un marcapasos transcutaneo a 70 por minuto con 80 mA.", "transcutaneous_pacing")
    assert (pacing["rate_per_min"], pacing["output_ma"], pacing["operation"]) == (70.0, 80.0, "start")


def test_the_output_written_as_its_own_clause_still_belongs_to_the_pacer():
    pacing = one("Inicia marcapaso transcutaneo a 70 lpm y 90 miliamperios.", "transcutaneous_pacing")
    assert pacing["output_ma"] == 90.0


def test_a_nodal_block_answers_atropine_and_an_infranodal_one_does_not():
    nodal = {"territory": "inferior"}
    infranodal = {"territory": "anterior"}
    f = {"elapsed": 50, "atropine_doses": [{"index": 0, "at": 50, "dose_mg": 1.0}]}
    assert brady.atropine_gain(f, nodal) == pytest.approx(brady.NODAL_FIRST_DOSE_BEATS)
    assert brady.atropine_gain(f, infranodal) == 0.0


def test_what_atropine_buys_fades_and_the_second_dose_buys_less():
    nodal = {"territory": "inferior"}
    first = brady.atropine_gain({"elapsed": 50, "atropine_doses": [{"index": 0, "at": 50, "dose_mg": 1}]}, nodal)
    later = brady.atropine_gain({"elapsed": 74, "atropine_doses": [{"index": 0, "at": 50, "dose_mg": 1}]}, nodal)
    second = brady.atropine_gain({"elapsed": 50, "atropine_doses": [{"index": 1, "at": 50, "dose_mg": 1}]}, nodal)
    assert later < first / 2 and second < first


def test_choosing_a_rate_is_not_pacing_until_the_current_captures():
    below = {"pacing_rate": 70, "pacing_ma": brady.PACING_DEFAULT_THRESHOLD_MA - 10, "elapsed": 1}
    above = {"pacing_rate": 70, "pacing_ma": brady.PACING_DEFAULT_THRESHOLD_MA + 10, "elapsed": 1}
    assert not brady.capturing(below) and brady.capturing(above)
    assert brady.effective_rate(below, {"territory": "inferior"}, 42) == 42
    assert brady.effective_rate(above, {"territory": "inferior"}, 42) == 70
    assert "without capture" in brady.rhythm(below)
    assert "capture confirmed" in brady.rhythm(above)


def test_capture_gives_back_the_pressure_the_lost_rate_was_costing():
    spec = {"territory": "inferior"}
    blocked = brady.pressure_penalty({"elapsed": 1}, spec, 42, 70)
    paced = brady.pressure_penalty({"pacing_rate": 70, "pacing_ma": 90, "elapsed": 1}, spec, 42, 70)
    # A paced beat is not the ventricle's own: most of the pressure comes back,
    # not all of it.
    assert blocked > paced > 0
    assert paced < blocked * .2


# 10 · Morphine

def test_morphine_is_read_in_both_languages():
    assert one("Indica morfina 3 mg IV.", "opioid_analgesia")["dose_mg"] == 3.0
    assert one("Give morphine 3 mg IV.", "opioid_analgesia")["agent"] == "morphine"


def test_the_preload_it_takes_costs_a_vulnerable_patient_most():
    rv = {"engine_family": "acs", "encounter_spec": {"clinical_case": {"engine": {
        "coronary": {"territory": "inferior", "rv_involvement": True}}}}}
    stable = {"engine_family": "acs", "encounter_spec": {"clinical_case": {"engine": {
        "coronary": {"territory": "anterior"}}}}}
    assert analgesia._vulnerability(rv, 100) > analgesia._vulnerability(stable, 100)
    assert analgesia._vulnerability(stable, 145) < analgesia._vulnerability(stable, 100)


def test_a_falling_respiratory_rate_after_morphine_is_not_an_improvement():
    state = {"family_state": {"morphine_mg": analgesia.SEDATION_MG + 4}}
    steps, rr_cost = analgesia.sedation(state)
    assert steps == 1 and rr_cost > 0
    deep = {"family_state": {"morphine_mg": analgesia.SEDATION_MG + analgesia.DEEP_SEDATION_MG + 1}}
    assert analgesia.sedation(deep)[0] == 2


def test_naloxone_takes_back_the_analgesia_with_the_sedation():
    state = {"family_state": {"morphine_mg": 10.0, "morphine_reversed_mg": 10.0}}
    assert analgesia.sedation(state) == (0, 0.0)


def test_vomiting_is_frequent_and_not_obligatory():
    assert analgesia.NAUSEA_SUSCEPTIBLE_IN >= 2
