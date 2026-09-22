"""The airway drugs, the nursing orders, the urine and the ward's analgesics.

Faculty decisions 11, 12, 13 and 14 of 2026-09-21. A rapid sequence left its
blocker hanging, a sedation infusion was refused for using infusion units, the
nursing orders a resident writes without thinking cost the whole turn, the
furosemide produced nothing visible at all, and paracetamol did not exist.
"""
import pytest

import airway_pharmacology as airway
import antipyretics
import urine_output
from family_parser import parse_family_actions


def actions(text):
    return parse_family_actions(text)["actions"]


def kinds(text):
    return [a.get("type") for a in actions(text)]


# 11 · Induction, paralysis and maintenance

def test_a_rapid_sequence_is_one_order_with_every_component_confirmed():
    parsed = actions("Intuba en secuencia rapida con ketamina 2 mg/kg y rocuronio 1.2 mg/kg, "
                     "en VC/AC con FiO2 100%, PEEP 5, volumen corriente 6 mL/kg y frecuencia 10.")
    assert [a["type"] for a in parsed] == ["intubation", "procedural_sedation", "neuromuscular_blockade"]
    assert parsed[0]["ventilator_mode"] == "VC/AC" and parsed[0]["rate_per_min"] == 10.0
    assert parsed[1]["dose_mg_per_kg"] == 2.0 and parsed[2]["dose_mg_per_kg"] == 1.2


def test_an_infusion_is_an_infusion_and_not_a_refused_fixed_dose():
    started = actions("Inicia propofol a 2 mg/kg/h.")[0]
    assert started == {"type": "sedation_infusion", "agent": "propofol", "rate": 2.0,
                       "units": "mg/kg/h", "route": "IV", "operation": "start"}
    assert actions("Suspende el propofol.")[0]["operation"] == "stop"
    assert actions("Baja el propofol a 1 mg/kg/h.")[0]["rate"] == 1.0


def test_movement_consciousness_and_pain_are_three_different_things():
    paralysed = {"elapsed": 10, "paralysis_until": 60}
    assert airway.mental_and_effort(paralysed)[0] == "Paralysed, sedation not maintained"
    assert airway.mental_and_effort({**paralysed, "sedation_at": 5})[0] == "Sedated"
    # An opioid infusion is analgesia; it is not what keeps a patient asleep.
    assert not airway.infusion_sedating({"sedation_infusion": {"agent": "fentanyl", "rate": 1}})
    assert airway.infusion_sedating({"sedation_infusion": {"agent": "propofol", "rate": 2}})


def test_the_block_outlasting_its_hypnotic_is_reported():
    f = {"elapsed": 50, "paralysis_until": 60, "invasive": True, "sedation_at": 0}
    event = airway.step({"family_state": f})
    assert event == airway.UNSEDATED_TEXT


def test_a_paralysed_patient_nobody_ventilates_arrests():
    f = {"elapsed": 5, "paralysis_until": 60, "invasive": False, "bag_mask": False,
         "sedation_at": 5, "paralysis_apnoea_min": airway.APNOEA_TO_ARREST_MIN - 1}
    event = airway.step({"family_state": f})
    assert "Cardiac arrest" in event and f["arrest_at"] == 5


def test_a_bigger_dose_lasts_longer_but_not_without_limit():
    short = airway.blocker_duration("rocuronium", None, .6, 70)[1]
    usual = airway.blocker_duration("rocuronium", None, 1.2, 70)[1]
    huge = airway.blocker_duration("rocuronium", None, 6.0, 70)[1]
    assert short < usual < huge
    assert huge <= airway.BLOCKERS["rocuronium"]["duration_min"] * airway.MAX_DURATION_FACTOR


# 13 · The nursing orders

@pytest.mark.parametrize("text, kind", [
    ("Instala una via venosa periferica gruesa.", "vascular_access"),
    ("Start a large-bore IV line.", "vascular_access"),
    ("Instala sonda Foley.", "urinary_catheter"),
    ("Pon una sonda nasogastrica.", "gastric_tube"),
    ("Deja regimen cero.", "npo"),
    ("Monitoriza al paciente.", "monitoring"),
])
def test_a_nursing_order_is_an_order(text, kind):
    assert kinds(text) == [kind]


def test_monitoring_a_named_vital_is_still_a_reassessment():
    assert kinds("Monitoriza presion arterial y saturacion.") == ["reassessment"]


def test_one_submission_asks_for_each_support_once():
    assert kinds("Instala monitor y oximetria de pulso.") == ["monitoring"]


# 12 · The urine

def test_a_catheter_measures_and_does_not_produce():
    state = {"family_state": {"elapsed": 1, "circulation": 1.0, "urine_ml": 0.0,
                              "urine_since_report_ml": 0.0, "urine_report_min": 0},
             "encounter_spec": {"clinical_case": {"patient": {"weight_kg": 70}}}, "sim_time": 1}
    with_catheter = dict(state["family_state"], urinary_catheter=True)
    without = dict(state["family_state"], urinary_catheter=False)
    assert urine_output.rate_ml_per_min({**state, "family_state": with_catheter}) == pytest.approx(
        urine_output.rate_ml_per_min({**state, "family_state": without}))


def test_hypoperfusion_closes_the_kidney_down():
    def rate(circulation):
        return urine_output.rate_ml_per_min({
            "family_state": {"elapsed": 1, "circulation": circulation},
            "encounter_spec": {"clinical_case": {"patient": {"weight_kg": 70}}}})
    assert rate(1.0) > rate(1.2) > rate(1.5) > 0
    assert rate(1.5) * 60 < 20  # oliguria long before anuria
    assert rate(1.8) == 0.0


def test_the_diuretic_response_arrives_late_fades_and_is_not_a_fixed_volume():
    state = {"family_state": {"elapsed": 0, "circulation": 1.0},
             "encounter_spec": {"clinical_case": {"patient": {"weight_kg": 70},
                                                  "investigations": {}}}}
    urine_output.record_dose(state, 40, "IV")
    f = state["family_state"]
    f["elapsed"] = 10
    early = urine_output.rate_ml_per_min(state)
    f["elapsed"] = 45
    working = urine_output.rate_ml_per_min(state)
    f["elapsed"] = 300
    late = urine_output.rate_ml_per_min(state)
    assert early < working and late < working


def test_without_a_collection_no_volume_is_invented():
    f = {"elapsed": 1, "circulation": 1.0, "urinary_catheter": False,
         "urine_since_report_ml": urine_output.VOID_ML, "urine_report_min": 200, "urine_ml": 0}
    event = urine_output.step({"family_state": f, "sim_time": 200,
                               "encounter_spec": {"clinical_case": {"patient": {"weight_kg": 70}}}})
    assert "not quantified" in event
    assert not any(character.isdigit() for character in event)


# 14 · The ward's analgesics and antipyretics

@pytest.mark.parametrize("text, agent", [
    ("Administra paracetamol 1 g IV.", "paracetamol"),
    ("Indica ibuprofeno 600 mg VO.", "ibuprofen"),
    ("Administra ketorolaco 30 mg IV.", "ketorolac"),
    ("Administra metamizol 1 g EV.", "metamizole"),
])
def test_the_ward_drugs_exist(text, agent):
    order = actions(text)[0]
    assert order["type"] == "antipyretic" and order["agent"] == agent


def test_fever_comes_down_gradually_and_a_normal_temperature_does_not_move():
    f = {"elapsed": 60, "antipyretic_doses": [
        {"agent": "paracetamol", "mg": 1000, "route": "IV", "at": 0, "onset": 20, "share": 1.0}]}
    assert antipyretics.temperature(f, 39.1) < 38.5
    assert antipyretics.temperature(f, 36.8) == 36.8
    assert antipyretics.temperature(f, 39.1) >= antipyretics.NO_FEVER_BELOW_C
    # It wears off while the infection is unresolved.
    assert antipyretics.temperature({**f, "elapsed": 260}, 39.1) > antipyretics.temperature(f, 39.1)


def test_the_oral_route_works_later_than_the_vein():
    state = {"family_state": {"elapsed": 0, "circulation": 1.0}, "engine_family": "pneumonia",
             "encounter_spec": {"clinical_case": {"investigations": {}}}}
    antipyretics.record_dose(state, "paracetamol", 1000, "PO")
    oral = state["family_state"]["antipyretic_doses"][0]["onset"]
    antipyretics.record_dose(state, "paracetamol", 1000, "IV")
    assert state["family_state"]["antipyretic_doses"][1]["onset"] < oral


def test_two_nsaids_are_one_class():
    state = {"family_state": {"elapsed": 0, "circulation": 1.0}, "engine_family": "pneumonia",
             "encounter_spec": {"clinical_case": {"investigations": {}}}}
    assert antipyretics.record_dose(state, "ibuprofen", 600, "IV") is None
    warning = antipyretics.record_dose(state, "ketorolac", 30, "IV")
    assert "two NSAIDs are one class" in warning


def test_an_nsaid_in_a_bleeding_patient_is_questioned():
    state = {"family_state": {"elapsed": 0, "circulation": 1.0}, "engine_family": "gi_bleed",
             "encounter_spec": {"clinical_case": {"investigations": {}}}}
    assert "bleeding from the gut" in antipyretics.record_dose(state, "ibuprofen", 600, "IV")


# Found playing the left main (2026-09-21): "inicia dobutamina a 5 mcg/kg/min e
# instala sonda Foley" executed the catheter and lost the inotrope without a
# word. Two causes: the imperative normalization rewrites the word after "e", so
# the conjunction rule stopped matching, and the support order answered for a
# clause that was not only about the support.

@pytest.mark.parametrize("text, expected", [
    ("Inicia dobutamina a 5 mcg/kg/min e instala sonda Foley.", ["dobutamine", "urinary_catheter"]),
    ("Instala sonda Foley e inicia dobutamina a 5 mcg/kg/min.", ["urinary_catheter", "dobutamine"]),
    ("Administra aspirina 300 mg VO e instala monitor.", ["aspirin", "monitoring"]),
    ("Pide hemograma e instala sonda Foley.", ["diagnostic", "urinary_catheter"]),
])
def test_a_nursing_order_never_swallows_the_treatment_beside_it(text, expected):
    assert kinds(text) == expected


def test_the_conjunction_still_leaves_a_trailing_letter_alone():
    # "Vitamina e" has no order after it: there is nothing to split.
    assert kinds("Administra vitamina e.") == ["clarification"]
