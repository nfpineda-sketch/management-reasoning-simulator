"""Order integrity regressions for the independent-family interpreter."""
import pytest

from family_parser import NEW_TREATMENT_ACTIONS, parse_family_actions


def actions(text):
    return parse_family_actions(text)["actions"]


def test_source_order_does_not_cross_bind_medication_and_fluid_quantities():
    result = actions("Give 25 g IV dextrose and 500 mL normal saline; reassess in 5 minutes")
    assert result == [
        {"type": "dextrose", "dose_g": 25, "route": "IV"},
        {"type": "fluid", "volume_ml": 500, "fluid_type": "normal saline"},
        {"type": "reassessment", "delay_min": 5},
    ]


def test_spanish_decimal_comma_and_diagnostic_order():
    result = actions("Administro naloxona 0,4 mg EV y solicito glicemia; reevalúo en 2 minutos")
    assert result[0] == {"type": "naloxone", "agent": "naloxone", "dose_mg": .4, "route": "IV"}
    assert result[1] == {"type": "diagnostic", "diagnostic": "poc_glucose"}
    assert result[2] == {"type": "reassessment", "delay_min": 2}


def test_multiple_antibiotics_retain_independent_doses_and_routes():
    result = actions("Give ceftriaxone 2 g IV + azithromycin 500 mg PO")
    assert [(a["agent"], a["dose_mg"], a["route"]) for a in result] == [
        ("ceftriaxone", 2000, "IV"), ("azithromycin", 500, "PO")
    ]


@pytest.mark.parametrize("phrase", [
    "I think pneumonia and I expect ceftriaxone to improve perfusion",
    "I suspect opioid toxicity; naloxone could improve breathing",
    "Espero que la glicemia suba con dextrosa",
    "Patient needs NIV because he has respiratory failure",
    "The patient received aspirin 324 mg PO",
    "Aspirin 324 mg PO was already given",
    "Blood pressure improved after 500 mL normal saline",
    "Do not give fluids or aspirin",
    "No administrar ceftriaxona y azitromicina",
    "Give no aspirin 324 mg PO",
    "If glucose is low, give 25 g IV dextrose",
    "Si empeora, administrar naloxona 0.4 mg IV",
    "Consider intubation VC/AC FiO2 100% PEEP 5",
    "I would give aspirin 324 mg PO",
])
def test_hypotheses_prior_actions_negation_and_conditionals_are_not_orders(phrase):
    assert actions(phrase) == []


def test_future_plan_is_preserved_without_becoming_an_intervention():
    result = parse_family_actions("If he worsens, start BiPAP 12/6 FiO2 40%")
    assert not result["actions"]
    assert result["recognized_future_actions"]


def test_new_sentence_is_not_swallowed_by_previous_negation_or_expectation():
    result = actions("Do not give fluids; I expect oxygenation to improve. Give aspirin 324 mg PO; check ECG")
    assert [a["type"] for a in result] == ["aspirin", "diagnostic"]
    assert result[1]["diagnostic"] == "ecg"


def test_reasoning_after_order_cannot_add_another_medication():
    result = actions("Give aspirin 324 mg PO because I suspect ACS and I expect nitroglycerin to reduce pain")
    assert [a["type"] for a in result] == ["aspirin"]


@pytest.mark.parametrize("phrase, diagnostic", [
    ("ECG", "ecg"), ("Obtain a 12-lead ECG", "ecg"),
    ("Solicito electrocardiograma", "ecg"), ("Check glucose", "poc_glucose"),
    ("Pedir hemoglobina", "hemoglobin"), ("Obtain CTPA", "ctpa"),
    ("Solicitar angio-TC pulmonar", "ctpa"), ("Measure temperature", "temperature"),
    ("Order blood cultures", "blood_cultures"), ("Solicito gases arteriales", "abg"),
    ("Solicito gases venosos", "vbg"), ("Order troponin", "troponin"),
    ("Order urinalysis", "urinalysis"), ("Get a chest X-ray", "chest_xray"),
])
def test_supported_diagnostic_orders(phrase, diagnostic):
    assert actions(phrase) == [{"type": "diagnostic", "diagnostic": diagnostic}]


def test_several_diagnostics_follow_the_source_order():
    assert [a["diagnostic"] for a in actions("Check glucose and lactate; obtain POCUS, troponin and basic labs")] == [
        "poc_glucose", "lactate", "pocus", "troponin", "basic_labs"
    ]


def test_bronchodilator_steroid_and_gastrointestinal_bleeding_orders():
    result = actions("Nebulize albuterol 2.5 mg; give prednisone 40 mg PO; transfuse 1 unit pRBC; give pantoprazole 80 mg IV")
    assert [a["type"] for a in result] == ["bronchodilator", "steroid", "blood", "ppi"]
    assert result[0]["dose_mg"] == 2.5
    assert result[0]["route"] == "nebulized"
    assert result[1]["route"] == "PO"
    assert result[2]["units"] == 1


def test_naloxone_micrograms_and_dextrose_milligrams_are_normalized():
    assert actions("Give naloxone 400 mcg IV")[0]["dose_mg"] == .4
    assert actions("Give dextrose 25000 mg IV")[0]["dose_g"] == 25


def test_anticoagulant_units_are_not_mistaken_for_mass():
    assert actions("Give heparin 5000 units IV")[0] == {
        "type": "anticoagulation", "agent": "heparin", "dose": 5000, "units": "units", "route": "IV"
    }
    assert actions("Give enoxaparin 80 mg SC")[0]["route"] == "SC"


def test_missing_dose_or_route_is_not_invented():
    result = actions("Give naloxone; give ceftriaxone 2 g; give aspirin 324 mg PO")
    assert result[0]["dose_mg"] is None and result[0]["route"] is None
    assert result[1]["dose_mg"] == 2000 and result[1]["route"] is None
    assert result[2]["dose_mg"] == 324


@pytest.mark.parametrize("phrase", [
    "Give atropine 1 mg IV", "Order brain MRI", "Start dopamine 5 mcg/kg/min",
    "Give ceftriaxone 2 g IV azithromycin 500 mg IV",
    "Give 25 g dextrose 500 mL saline IV", "Give prednisone 1 mg/kg PO",
    "Give naloxone 2 units IV", "Start nitroglycerin 1 mcg/kg/min",
    "Increase norepinephrine by 0.05 mcg/kg/min",
    "Increase norepinephrine from 0.05 mcg/kg/min to 0.1 mcg/kg/min",
])
def test_unsupported_or_ambiguous_orders_require_clarification(phrase):
    assert actions(phrase)[0]["type"] == "clarification"


def test_unsupported_extra_order_is_not_silently_discarded():
    result = actions("Give aspirin 324 mg PO and clopidogrel 300 mg PO")
    assert [a["type"] for a in result] == ["aspirin", "clarification"]


def test_oxygen_niv_and_invasive_ventilation_settings():
    oxygen, niv, tube = actions("Start oxygen via nasal cannula 4 L/min; start BiPAP 12/6 FiO2 40%; intubate VC/AC FiO2 1 PEEP 5")
    assert oxygen == {"type": "oxygen", "device": "nasal cannula", "flow_lpm": 4}
    assert niv == {"type": "niv", "mode": "BiPAP", "ipap_cmh2o": 12, "epap_cmh2o": 6, "fio2_percent": 40, "operation": "start"}
    assert tube == {"type": "intubation", "ventilator_mode": "VC/AC", "fio2_percent": 100, "peep_cmh2o": 5}
    assert actions("Stop oxygen")[0] == {"type": "oxygen", "device": "room air", "flow_lpm": 0}


def test_infusion_rates_and_operations():
    result = actions("Start norepinephrine 0.05 mcg/kg/min; increase nitroglycerin to 30 mcg/min; stop nitroglycerin")
    assert result[0] == {"type": "norepinephrine", "rate": .05, "units": "mcg/kg/min", "operation": "start"}
    assert result[1] == {"type": "nitroglycerin", "rate_mcg_min": 30, "operation": "adjust"}
    assert result[2] == {"type": "nitroglycerin", "rate_mcg_min": None, "operation": "stop"}


def test_spanish_diuretic_and_consults():
    result = actions("Administro furosemida 40 mg EV; activar hemodinamia; consultar cardiología; transfer to ICU")
    assert result[0]["type"] == "diuretic" and result[0]["dose_mg"] == 40
    assert result[1] == {"type": "consult", "service": "cath lab"}
    assert result[2] == {"type": "consult", "service": "cardiology"}
    assert result[3] == {"type": "disposition", "destination": "ICU"}


def test_bag_mask_and_reassessment_preserve_explicit_zero_time():
    assert actions("Ventilate with bag and mask; reassess now") == [
        {"type": "bag_mask"}, {"type": "reassessment", "delay_min": 0}
    ]


def test_plain_question_does_not_create_actions_or_advance_time():
    assert actions("How are you feeling? Do you have any pain?") == []


def test_contracted_explicit_order():
    assert actions("I'll give aspirin 324 mg PO")[0]["dose_mg"] == 324


def test_action_set_excludes_information_requests():
    assert {"fluid", "dextrose", "diuretic", "intubation"} <= NEW_TREATMENT_ACTIONS
    assert not {"diagnostic", "reassessment", "clarification"} & NEW_TREATMENT_ACTIONS


@pytest.mark.parametrize("family, phrase", [
    ("pneumonia", "Start oxygen via nasal cannula 4 L/min; give ceftriaxone 2 g IV and azithromycin 500 mg IV; check lactate"),
    ("pulmonary_edema", "Start BiPAP 12/6 FiO2 60%; start nitroglycerin 20 mcg/min; give furosemide 40 mg IV; reassess in 5 minutes"),
    ("acs", "Give aspirin 324 mg PO; check troponin; consult cardiology"),
    ("pulmonary_embolism", "Order CTPA; give heparin 5000 units IV; consult PERT"),
    ("asthma", "Nebulize albuterol 2.5 mg; give prednisone 40 mg PO; reassess in 5 minutes"),
    ("gi_bleed", "Transfuse 1 unit pRBC; give pantoprazole 80 mg IV; consult gastroenterology"),
    ("hypoglycemia", "Give dextrose 25 g IV; recheck glucose; reassess in 5 minutes"),
    ("opioid", "Ventilate with bag-mask; give naloxone 0.4 mg IV; reassess in 5 minutes"),
])
def test_parsed_orders_are_executable_in_each_independent_engine_family(family, phrase):
    from cognitive_catalog import BIAS_CHALLENGES
    from cognitive_generator import generate_cognitive_encounter
    from family_engine import execute_family_bundle
    challenge = next(key for key, entry in BIAS_CHALLENGES.items() if family in entry["families"])
    state = generate_cognitive_encounter(challenge, {"sim_time": 0, "hidden": {}, "treatments": {}},
                                        family_id=family, seed=1)["state"]
    result = execute_family_bundle(state, parse_family_actions(phrase))
    assert result["executed"], result.get("clarification")
    assert result["action_summaries"]
    assert state["engine_family"] == family


def test_ambiguous_or_unknown_compound_order_does_not_partially_treat_patient():
    from copy import deepcopy
    from cognitive_generator import generate_cognitive_encounter
    from family_engine import execute_family_bundle
    state = generate_cognitive_encounter("R2-02", {"sim_time": 0, "hidden": {}, "treatments": {}},
                                        family_id="acs", seed=1)["state"]
    before = deepcopy(state)
    parsed = parse_family_actions("Give aspirin 324 mg PO and clopidogrel 300 mg PO")
    result = execute_family_bundle(state, parsed)
    assert not result["executed"]
    assert result["clarification"]
    assert state == before


@pytest.mark.parametrize("phrase, device, flow", [
    ("Switch from non-rebreather mask 15 L/min to nasal cannula 3 L/min", "nasal cannula", 3),
    ("Increase nasal cannula oxygen from 3 L/min to 4 L/min", "nasal cannula", 4),
    ("Decrease nasal cannula from 4 L/min to 2 L/min", "nasal cannula", 2),
    ("Cambiar de mascarilla con reservorio 15 L/min a canula nasal 3 L/min", "nasal cannula", 3),
    ("Aumentar canula nasal de 3 L/min a 4 L/min", "nasal cannula", 4),
    ("Switch from nasal cannula 4 L/min to room air", "room air", 0),
    ("Apply oxygen through nasal cannula at 3 L/min", "nasal cannula", 3),
    ("Colocar oxigeno por canula nasal a 3 L/min", "nasal cannula", 3),
    ("Start oxygen NC 3 L/min", "nasal cannula", 3),
])
def test_oxygen_target_settings_never_inherit_previous_device_flow(phrase, device, flow):
    assert actions(phrase) == [{"type": "oxygen", "device": device, "flow_lpm": flow}]


@pytest.mark.parametrize("phrase", [
    "Start oxygen", "Apply oxygen 4 L/min", "Colocar oxigeno por canula nasal",
    "Start nasal cannula 2 L/min 4 L/min", "Increase nasal cannula by 2 L/min",
    "Switch from non-rebreather mask 15 L/min to 3 L/min",
    "Start high-flow nasal cannula 15 L/min",
])
def test_incomplete_or_ambiguous_oxygen_order_blocks_whole_bundle(phrase):
    from copy import deepcopy
    from cognitive_generator import generate_cognitive_encounter
    from family_engine import execute_family_bundle
    state = generate_cognitive_encounter("R1-05", {"sim_time": 0, "hidden": {}, "treatments": {}},
                                        family_id="pneumonia", seed=1)["state"]
    before = deepcopy(state)
    parsed = parse_family_actions(phrase + "; reassess in 5 minutes")
    assert parsed["actions"][0]["type"] == "clarification"
    result = execute_family_bundle(state, parsed)
    assert not result["executed"] and result["clarification"]
    assert state == before


@pytest.mark.parametrize("phrase", [
    "Start oxygen NC 3 L/min, and if BP falls give fluids",
    "Start oxygen NC 3 L/min and if BP falls give fluids",
    "Iniciar oxigeno por canula nasal 3 L/min y si cae la presion dar 500 mL de saline",
])
def test_later_conditional_plan_does_not_erase_unconditional_order(phrase):
    parsed = parse_family_actions(phrase)
    assert parsed["actions"] == [{"type": "oxygen", "device": "nasal cannula", "flow_lpm": 3}]
    assert len(parsed["recognized_future_actions"]) == 1


@pytest.mark.parametrize("phrase", [
    "Start oxygen NC 3 L/min if saturation falls",
    "Start oxygen NC 3 L/min, if saturation falls",
    "If saturation falls, start oxygen NC 3 L/min",
])
def test_condition_that_qualifies_oxygen_order_never_executes_now(phrase):
    assert actions(phrase) == []


def test_full_reasoning_does_not_create_fake_or_duplicate_reassessments():
    phrase = ("My working model is that reduced glucose availability may be contributing to altered consciousness. "
              "My priority is to restore glucose availability and reassess the patient. "
              "Give dextrose 25 g IV. I expect improved mental status. "
              "Reassess mental status, glucose, blood pressure and breathing in 5 minutes.")
    assert actions(phrase) == [
        {"type": "dextrose", "dose_g": 25, "route": "IV"},
        {"type": "reassessment", "delay_min": 5},
    ]
