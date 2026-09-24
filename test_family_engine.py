"""Behavioural regression checks for independent clinical family trajectories."""
from copy import deepcopy
import math
import pytest
from family_engine import execute_family_bundle, clinical_update, current_findings, FAMILIES


def make_state(family):
    values = {
        "pneumonia": (88, 54, 118, 89, 28, 5, "Alert", 112),
        "pulmonary_edema": (192, 106, 116, 84, 34, 3, "Alert", 112),
        "acs": (104, 66, 58, 95, 22, 3, "Alert", 112),
        "pulmonary_embolism": (94, 60, 125, 88, 28, 4, "Alert", 112),
        "asthma": (126, 76, 124, 90, 32, 2, "Drowsy", 112),
        "gi_bleed": (86, 52, 118, 97, 24, 5, "Alert", 112),
        "hypoglycemia": (126, 76, 102, 97, 18, 2, "Obtunded", 34),
        "opioid": (104, 66, 74, 82, 6, 2, "Obtunded", 105),
        # Warm, fast and empty: a distributive shock reads differently from the
        # cold ones above, which is the point of the family.
        "anaphylaxis": (84, 46, 126, 91, 28, 3, "Alert", 108),
        # Flank pain with a sepsis behind it: the fever and the lactate move,
        # the lungs do not.
        "renal_colic": (94, 54, 118, 95, 24, 4, "Alert", 138),
        # Slow and underperfused, with the glucose that names the poison.
        "bradycardia": (74, 44, 38, 96, 18, 4, "Alert", 214),
        # Bleeding: fast, cold and falling, with nothing wrong with the lungs.
        "trauma": (88, 52, 128, 97, 26, 4, "Alert", 128),
    }[family]
    o = dict(zip(("sbp", "dbp", "hr", "spo2", "respiratory_rate", "crt", "mental_status", "glucose_mg_dl"), values))
    o.update(rhythm="Sinus bradycardia" if family == "acs" else "Sinus rhythm", work_of_breathing="Reduced" if family == "opioid" else "Markedly increased", extremities="Cool", temperature_c=38.5 if family == "pneumonia" else 36.7, pulse_present=True, peripheral_perfusion="impaired")
    investigations = {
        "poc_glucose": {"duration_min": 0, "result": {"glucose_mg_dl": values[-1]}},
        "hemoglobin": {"duration_min": 10, "result": {"hemoglobin_g_dl": 6.8 if family == "gi_bleed" else 12}},
        "basic_labs": {"duration_min": 10, "result": {"hemoglobin_g_dl": 6.8 if family == "gi_bleed" else 12, "glucose_mg_dl": values[-1], "sodium_mmol_l": 139}},
        "pocus": {"duration_min": 2, "result": {"lv": "Preserved systolic function", "lungs": "Diffuse B-lines" if family == "pulmonary_edema" else "No diffuse B-lines", "rv": "RV dilated" if family == "pulmonary_embolism" else "Not dilated", "ivc": "Small"}},
        "troponin": {"duration_min": 20, "result": {"value_ng_l": 320 if family == "acs" else 9, "report": "Troponin 320 ng/L" if family == "acs" else "Troponin 9 ng/L"}},
        "vbg": {"duration_min": 5, "result": {"pco2_mm_hg": 64, "ph": 7.22}},
        "abg": {"duration_min": 5, "result": {"paco2_mm_hg": 64, "pao2_mm_hg": 50, "ph": 7.22, "sao2_percent": 84}},
    }
    case = {"observable": deepcopy(o), "engine": {
        **({"anaphylaxis": {"severity": 1.0}} if family == "anaphylaxis" else {}),
        **({"renal": {"infected": True, "side": "left"}} if family == "renal_colic" else {}),
        **({"bradycardia": {"cause": "ccb", "block": False, "av_block_location": "infranodal",
                            "escape_rate": 38, "target_rate": 75}} if family == "bradycardia" else {}),
        **({"trauma": {"sources": {"external": 1.0}, "arrival_deficit": .12}} if family == "trauma" else {}),
        "family": family, "baseline_glucose": values[-1], "recurrence_risk": family in {"hypoglycemia", "opioid"}, "baseline_hemoglobin": 6.8 if family == "gi_bleed" else 12, "baseline_lactate": 3.2}, "investigations": investigations, "examination": {"Respiratory": "Case-authored breathing", "Neurological": "Case-authored pupils"}, "visual_profile": {"baseline": {"expression": "uncomfortable", "diaphoresis": "mild"}}}
    return {"engine_family": family, "encounter_spec": {"clinical_case": case, "ecg_profile": "inferior_stemi" if family == "acs" else "baseline"}, "observable": o, "hidden": {}, "sim_time": 0, "treatments": {}, "diagnostics": {}}


def run(state, *actions):
    result = execute_family_bundle(state, {"actions": list(actions)})
    assert result["executed"], result.get("clarification")
    return result


def wait(minutes):
    return {"type": "reassessment", "delay_min": minutes}


@pytest.mark.parametrize("family", sorted(FAMILIES))
def test_family_has_independent_finite_baseline_and_no_af_or_urinary_update(family):
    state = make_state(family)
    run(state, wait(5))
    for key in ("sbp", "dbp", "hr", "spo2", "respiratory_rate", "crt"):
        assert math.isfinite(state["observable"][key])
    assert state["observable"]["rhythm"] != "AF"
    assert "urinary" not in clinical_update(state).lower()
    assert state["encounter_spec"]["clinical_case"] == make_state(family)["encounter_spec"]["clinical_case"]


def test_oxygen_does_not_correct_pneumonia_or_instantly_clear_perfusion_with_antibiotics():
    state = make_state("pneumonia")
    run(state, {"type": "oxygen", "device": "nasal cannula", "flow_lpm": 4}, {"type": "antibiotics", "agent": "ceftriaxone", "dose_mg": 2000, "route": "IV"}, wait(5))
    assert state["observable"]["spo2"] > 89
    assert state["observable"]["crt"] >= 5
    assert state["observable"]["work_of_breathing"] in {"Markedly increased", "Severe"}
    assert state["family_state"]["lung"] >= 1


def test_edema_response_to_niv_nitrate_is_partial_and_fluid_is_not_universal_cure():
    state, fluid = make_state("pulmonary_edema"), make_state("pulmonary_edema")
    run(state, {"type": "niv", "mode": "BiPAP", "ipap_cmh2o": 12, "epap_cmh2o": 6, "fio2_percent": 60}, {"type": "nitroglycerin", "rate_mcg_min": 100}, wait(10))
    run(fluid, {"type": "fluid", "fluid_type": "normal saline", "volume_ml": 500}, wait(10))
    assert state["observable"]["sbp"] < 192
    assert state["observable"]["spo2"] > 84
    assert state["observable"]["respiratory_rate"] < 34
    assert "crackles" in current_findings(state)["Respiratory"]
    assert fluid["family_state"]["lung"] > 1


def test_acs_antiplatelet_and_consult_do_not_invent_reperfusion():
    state = make_state("acs")
    run(state, {"type": "aspirin", "dose_mg": 324, "route": "PO"}, {"type": "consult", "service": "cath lab"}, wait(5))
    assert state["encounter_spec"]["ecg_profile"] == "inferior_stemi"
    assert state["family_state"]["consultations"][0]["service"] == "cath lab"
    assert state["family_state"]["circulation"] >= 1
    assert state["observable"]["rhythm"] == "Sinus bradycardia"


def test_pe_anticoagulation_is_not_instant_clot_lysis():
    state = make_state("pulmonary_embolism")
    run(state, {"type": "anticoagulation", "agent": "heparin", "dose": 5000, "units": "units", "route": "IV"}, {"type": "consult", "service": "PERT"}, wait(10))
    assert state["observable"]["spo2"] <= 88
    assert state["observable"]["crt"] >= 4
    run(state, {"type": "diagnostic", "diagnostic": "pocus"})
    assert state["diagnostics"]["pocus"]["rv"] == "RV dilated"


def test_asthma_airflow_and_mentation_respond_while_steroid_effect_is_delayed():
    state = make_state("asthma")
    # The nebulized dose now arrives over its onset (faculty 2026-09-20), so the
    # answer is read once it has landed rather than at five minutes.
    run(state, {"type": "bronchodilator", "agent": "albuterol", "dose_mg": 5, "route": "nebulized"}, {"type": "steroid", "agent": "prednisone", "dose_mg": 50, "route": "PO"}, wait(15))
    assert state["observable"]["respiratory_rate"] < 32
    assert state["observable"]["mental_status"] == "Alert"
    assert "Improved air entry" in current_findings(state)["Respiratory"]
    assert state["family_state"]["obstruction"] >= 1


def test_transfusion_delivers_over_time_and_repeat_hemoglobin_is_current():
    state = make_state("gi_bleed")
    run(state, {"type": "blood", "units": 1}, wait(1))
    assert state["treatments"]["packed_red_cells_units"] < .04
    assert state["family_state"]["hemoglobin"] < 6.85
    run(state, wait(29))
    assert state["treatments"]["packed_red_cells_units"] == 1
    run(state, {"type": "diagnostic", "diagnostic": "hemoglobin"})
    assert state["diagnostics"]["hemoglobin"]["hemoglobin_g_dl"] > 6.8
    assert state["family_state"]["circulation"] > .5


def test_dextrose_reverses_neuroglycopenia_and_recurrence_requires_monitoring():
    state = make_state("hypoglycemia")
    run(state, {"type": "diagnostic", "diagnostic": "poc_glucose"})
    first = deepcopy(state["diagnostics"]["poc_glucose"])
    run(state, {"type": "dextrose", "dose_g": 25, "route": "IV"})
    assert state["observable"]["mental_status"] == "Alert"
    run(state, {"type": "diagnostic", "diagnostic": "poc_glucose"})
    assert state["diagnostics"]["poc_glucose"]["glucose_mg_dl"] > 100
    assert state["diagnostic_history"][0]["result"] == first
    run(state, wait(120))
    assert state["observable"]["glucose_mg_dl"] < 70
    assert state["observable"]["mental_status"] != "Alert"
    assert "mg/dL" not in clinical_update(state)


def test_opioid_oxygen_is_not_ventilation_and_naloxone_can_wear_off():
    oxygen, ventilation, antidote = (make_state("opioid") for _ in range(3))
    run(oxygen, {"type": "oxygen", "device": "non-rebreather mask", "flow_lpm": 15}, wait(2))
    assert oxygen["observable"]["spo2"] > 82
    assert oxygen["observable"]["respiratory_rate"] <= 7
    assert oxygen["observable"]["work_of_breathing"] == "Reduced"
    run(ventilation, {"type": "bag_mask"}, wait(2))
    assert ventilation["observable"]["spo2"] >= 95
    assert ventilation["observable"]["mental_status"] != "Alert"
    run(antidote, {"type": "naloxone", "dose_mg": .4, "route": "IV"})
    assert antidote["observable"]["respiratory_rate"] >= 12
    assert antidote["observable"]["mental_status"] == "Alert"
    reversed_rate = antidote["observable"]["respiratory_rate"]
    run(antidote, wait(60))
    # The antidote has gone and the agonist has not: the patient slips back.
    # Faculty decision 3b of 2026-09-21 separated concentration from effect, so
    # a short-acting drug that is already being eliminated comes back milder
    # than it arrived — it comes back, which is the teaching, and not all the
    # way down to the apnoea it started from.
    assert antidote["observable"]["respiratory_rate"] < reversed_rate
    assert antidote["observable"]["mental_status"] != "Alert"


@pytest.mark.parametrize("bad", [
    {"type": "fluid", "volume_ml": float("nan"), "fluid_type": "normal saline"},
    {"type": "fluid", "volume_ml": -1, "fluid_type": "normal saline"},
    {"type": "blood", "units": 1.2},
    {"type": "reassessment", "delay_min": float("inf")},
    {"type": "naloxone", "dose_mg": .4, "route": "unknown"},
    {"type": "diagnostic", "diagnostic": "unavailable_scan"},
    {"type": "unknown_action"},
])
def test_invalid_bundle_is_atomic_even_if_first_order_is_valid(bad):
    state = make_state("hypoglycemia")
    before = deepcopy(state)
    result = execute_family_bundle(state, {"actions": [{"type": "dextrose", "dose_g": 25, "route": "IV"}, bad]})
    assert not result["executed"]
    assert result["clarification"]
    assert state == before


def test_no_bias_or_action_score_enters_patient_trajectory():
    left, right = make_state("pneumonia"), make_state("pneumonia")
    left["bias_id"], right["bias_id"] = "anchoring", "confirmation"
    left["score"], right["score"] = 0, 100
    run(left, {"type": "fluid", "fluid_type": "normal saline", "volume_ml": 500}, wait(10))
    run(right, {"type": "fluid", "fluid_type": "normal saline", "volume_ml": 500}, wait(10))
    assert left["observable"] == right["observable"]
    assert left["family_state"] == right["family_state"]


def test_studies_freeze_at_collection_and_are_only_returned_after_processing():
    state = make_state("hypoglycemia")
    result = run(state, {"type": "diagnostic", "diagnostic": "poc_glucose"}, {"type": "dextrose", "dose_g": 25, "route": "IV"}, {"type": "diagnostic", "diagnostic": "basic_labs"}, {"type": "diagnostic", "diagnostic": "troponin"})
    assert result["elapsed_min"] == 20
    assert state["diagnostics"]["poc_glucose"]["time_min"] == 0
    assert state["diagnostics"]["poc_glucose"]["glucose_mg_dl"] == 34
    assert state["diagnostics"]["basic_labs"]["time_min"] == 10
    assert state["diagnostics"]["basic_labs"]["glucose_mg_dl"] == 34
    assert state["diagnostics"]["basic_labs"]["collected_at_min"] == 0
    assert state["diagnostics"]["troponin"]["time_min"] == 20


def test_pressure_support_does_not_erase_perfusion_or_pallor():
    state = make_state("gi_bleed")
    run(state, {"type": "norepinephrine", "rate": 10, "units": "mcg/min"}, wait(3))
    assert state["observable"]["sbp"] > 86
    assert state["observable"]["crt"] >= 5
    assert state["observable"]["peripheral_perfusion"] == "impaired"


def test_current_gas_after_reversal_does_not_repeat_old_hypercapnia():
    state = make_state("opioid")
    run(state, {"type": "naloxone", "dose_mg": .4, "route": "IV"}, {"type": "diagnostic", "diagnostic": "vbg"})
    assert state["diagnostics"]["vbg"]["pco2_mm_hg"] == 64
    assert state["diagnostics"]["vbg"]["collected_at_min"] == 0
    assert state["diagnostics"]["vbg"]["time_min"] == 5
    run(state, {"type": "diagnostic", "diagnostic": "vbg"})
    assert state["diagnostics"]["vbg"]["collected_at_min"] == 5
    assert state["diagnostics"]["vbg"]["pco2_mm_hg"] < 50
    assert state["diagnostics"]["vbg"]["ph"] > 7.3


def actual_state(variant):
    return {"engine_family": variant["engine"]["family"], "encounter_spec": {"clinical_case": deepcopy(variant), "ecg_profile": variant["ecg_profile"], "visual_profile": deepcopy(variant["visual_profile"])}, "observable": deepcopy(variant["observable"]), "hidden": {}, "sim_time": 0, "treatments": {}, "diagnostics": {}}


def test_actual_bank_preserves_untreated_ventilatory_pattern_and_coherent_gas():
    from clinical_cases import FAMILIES as BANK
    for family in ("asthma", "opioid"):
        for variant in BANK[family]["variants"]:
            state = actual_state(variant)
            baseline = variant["investigations"]["abg"]["result"]
            run(state, {"type": "diagnostic", "diagnostic": "abg"})
            gas = state["diagnostics"]["abg"]
            assert abs(gas["paco2_mm_hg"] - baseline["paco2_mm_hg"]) <= 2
            expected = 6.1 + math.log10(gas["bicarbonate_mmol_l"] / (.03 * gas["paco2_mm_hg"]))
            assert abs(gas["ph"] - expected) <= .02
            assert "pH" not in gas and "pCO2_mmHg" not in gas


def test_neutral_actions_preserve_authored_extremities_and_effort():
    from clinical_cases import FAMILIES as BANK
    for family in ("pneumonia", "pulmonary_embolism", "pulmonary_edema", "asthma"):
        for variant in BANK[family]["variants"]:
            state = actual_state(variant)
            run(state, {"type": "consult", "service": "ICU"}, wait(1))
            assert state["observable"]["extremities"] == variant["observable"]["extremities"]
            assert state["observable"]["work_of_breathing"] == variant["observable"]["work_of_breathing"]


def test_actual_opioid_pupils_survive_neurological_update_without_stale_mentation():
    from clinical_cases import FAMILIES as BANK
    state = actual_state(BANK["opioid"]["variants"][0])
    run(state, {"type": "naloxone", "dose_mg": .4, "route": "IV"})
    neuro = current_findings(state)["Neurological"]
    assert "Alert" in neuro
    assert "pupils" in neuro.lower()
    assert "obtunded" not in neuro.lower()


def test_ecg_acquires_current_electrical_state_and_preserves_serial_record():
    from clinical_cases import FAMILIES as BANK
    state = actual_state(BANK["acs"]["variants"][0])
    run(state, {"type": "diagnostic", "diagnostic": "ecg"})
    first = deepcopy(state["diagnostics"]["ecg"][0])
    assert first["status"] == "available"
    assert first["acquired_at_minutes"] == 0
    assert first["time_min"] == 1
    run(state, wait(5), {"type": "diagnostic", "diagnostic": "ecg"})
    assert state["diagnostics"]["ecg"][0] == first
    assert len(state["diagnostics"]["ecg"]) == 2


def test_upstream_partial_parse_clarification_blocks_every_action():
    state = make_state("acs")
    before = deepcopy(state)
    result = execute_family_bundle(state, {"actions": [{"type": "aspirin", "dose_mg": 324, "route": "PO"}], "clarification": "Please clarify an additional order."})
    assert not result["executed"]
    assert state == before


def test_assisted_ventilation_does_not_hide_suppressed_spontaneous_drive():
    state = make_state("opioid")
    run(state, {"type": "bag_mask"}, wait(2))
    assert state["observable"]["work_of_breathing"] == "Reduced"
    run(state, {"type": "oxygen", "device": "nasal cannula", "flow_lpm": 3})
    assert state["treatments"]["bag_mask"] is False
    assert state["family_state"]["bag_mask"] is False
    assert state["observable"]["respiratory_rate"] < 10


@pytest.mark.parametrize("family,kind,agent,normal_dose,field", [
    ("pneumonia", "antibiotics", "ceftriaxone", 1000, "lung"),
    ("asthma", "steroid", "methylprednisolone", 32, "obstruction"),
])
def test_small_recorded_doses_do_not_trigger_full_size_class_response(family, kind, agent, normal_dose, field):
    low, normal, untreated = make_state(family), make_state(family), make_state(family)
    run(low, {"type": kind, "agent": agent, "dose_mg": .01, "route": "IV"}, wait(90))
    run(normal, {"type": kind, "agent": agent, "dose_mg": normal_dose, "route": "IV"}, wait(90))
    run(untreated, wait(90))
    assert low["treatments"]["administered_medications"][0]["dose_mg"] == .01
    assert abs(low["family_state"][field] - untreated["family_state"][field]) < .001
    assert normal["family_state"][field] < low["family_state"][field] - .05


def test_treatment_record_agrees_with_executed_interface_and_recorded_units():
    state = make_state("pulmonary_edema")
    run(state, {"type": "oxygen", "device": "nasal cannula", "flow_lpm": 3})
    assert state["treatments"]["oxygen"] is True
    run(state, {"type": "niv", "mode": "CPAP", "epap_cmh2o": 10, "fio2_percent": 60})
    assert state["treatments"]["niv_pressure_cmh2o"] == 10
    assert state["treatments"]["oxygen"] is False
    run(state, {"type": "niv", "operation": "stop"})
    assert state["treatments"]["oxygen_device"] == "Room air"
    run(state, {"type": "nitroglycerin", "rate_mcg_min": 20})
    assert state["treatments"]["nitroglycerin"] is True
    assert state["treatments"]["nitroglycerin_rate_mcg_min"] == 20
    state = make_state("pneumonia")
    run(state, {"type": "norepinephrine", "rate": .05, "units": "mcg/kg/min"})
    assert state["treatments"]["norepinephrine_rate"] == .05
    assert state["treatments"]["norepinephrine_units"] == "mcg/kg/min"
    run(state, {"type": "fluid", "fluid_type": "normal saline", "volume_ml": 500})
    assert state["treatments"]["cumulative_crystalloid_ml"] == state["treatments"]["total_crystalloid_ml"] == 500
