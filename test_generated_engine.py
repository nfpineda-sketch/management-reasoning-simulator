"""Contract tests for runtime execution of newly generated, declarative cases."""
from copy import deepcopy
import math
import pytest

from generated_engine import (
    validate_declarative_case, execute_generated_bundle, current_findings, clinical_update,
)


def rule(identifier="fluid", action_type="fluid", delta=None, **kwargs):
    result = {"id": identifier, "action_type": action_type, "dose_field": "volume_ml",
              "reference_dose": 500, "onset_min": 0, "duration_min": 10,
              "max_exposure": 2, "delta": {"sbp": 10, "dbp": 5, "crt": -1} if delta is None else delta}
    result.update(kwargs)
    return result


def make_state():
    observable = {"sbp": 90, "dbp": 55, "hr": 114, "spo2": 93, "respiratory_rate": 24,
                  "crt": 4.5, "temperature_c": 37.7, "glucose_mg_dl": 74,
                  "mental_status": "Alert", "work_of_breathing": "Mildly increased",
                  "rhythm": "Sinus tachycardia", "pulse_present": True, "extremities": "Cool",
                  "peripheral_perfusion": "impaired", "visual": {"expression": "uncomfortable", "skin_color": "pallor", "mottling": False}}
    case = {"observable": deepcopy(observable), "ecg_profile": "baseline",
            "engine": {"model": "declarative_v1", "horizon_min": 180,
                       "initial_labs": {"hemoglobin_g_dl": 11, "lactate_mmol_l": 3.1, "pco2_mm_hg": 32, "bicarbonate_mmol_l": 18, "pao2_mm_hg": 70},
                       "untreated_drift_per_min": {"sbp": -.2, "dbp": -.1, "crt": .01},
                       "response_rules": [rule(), rule("glucose", "dextrose", {"glucose_mg_dl": 100}, agent="dextrose", route="IV", dose_field="dose_g", reference_dose=25, duration_min=3)],
                       "state_rules": [{"when": [{"field": "sbp", "operator": "lt", "value": 85}],
                                        "set": {"mental_status": "Drowsy", "visual": {"expression": "passive", "mottling": True}},
                                        "examination": {"Neurological": "Opens eyes to voice; replies briefly."}}]},
            "examination": {"Respiratory": "Bilateral breath sounds.", "Neurological": "Alert, responds to questions."},
            "investigations": {"poc_glucose": {"duration_min": 0, "result": {"glucose_mg_dl": 74, "report": "Glucose 74 mg/dL"}, "result_bindings": {"glucose_mg_dl": "glucose_mg_dl"}},
                               "basic_labs": {"duration_min": 10, "result": {"glucose_mg_dl": 74, "hemoglobin_g_dl": 11}, "result_bindings": {"glucose_mg_dl": "glucose_mg_dl", "hemoglobin_g_dl": "hemoglobin_g_dl"}},
                               "vbg": {"duration_min": 5, "result": {"ph": 7.37, "pco2_mm_hg": 32, "bicarbonate_mmol_l": 18}, "result_bindings": {"pco2_mm_hg": "pco2_mm_hg", "bicarbonate_mmol_l": "bicarbonate_mmol_l"}}}}
    return {"engine_family": "generated", "encounter_spec": {"clinical_case": case, "ecg_profile": "baseline"}, "observable": observable, "sim_time": 0, "hidden": {}, "treatments": {}, "diagnostics": {}}


def run(state, *actions):
    result = execute_generated_bundle(state, {"actions": list(actions)})
    assert result["executed"], result.get("clarification")
    return result


def wait(minutes):
    return {"type": "reassessment", "delay_min": minutes}


def test_generated_numeric_state_uses_only_declared_effects_and_elapsed_time():
    state = make_state()
    frozen = deepcopy(state["encounter_spec"])
    run(state, wait(10))
    assert state["observable"]["sbp"] == 88
    assert state["observable"]["hr"] == 114
    assert state["encounter_spec"] == frozen
    assert "hemoglobin_g_dl" not in state["observable"]
    assert state["generated_state"]["values"]["hemoglobin_g_dl"] == 11


def test_actual_dose_scales_effect_instead_of_boolean_full_response():
    small, full = make_state(), make_state()
    run(small, {"type": "fluid", "fluid_type": "normal saline", "volume_ml": 50}, wait(10))
    run(full, {"type": "fluid", "fluid_type": "normal saline", "volume_ml": 500}, wait(10))
    assert small["observable"]["sbp"] == 89
    assert full["observable"]["sbp"] == 98
    assert small["treatments"]["total_crystalloid_ml"] == 50
    assert full["treatments"]["total_crystalloid_ml"] == 500


def test_fluids_do_not_have_full_response_before_delivery():
    state = make_state()
    state["encounter_spec"]["clinical_case"]["engine"]["response_rules"][0]["duration_min"] = 1
    run(state, {"type": "fluid", "fluid_type": "normal saline", "volume_ml": 500}, wait(1))
    assert state["treatments"]["total_crystalloid_ml"] == 50
    assert state["observable"]["sbp"] == 91


def test_repeated_exposure_is_capped_without_changing_recorded_dose():
    state = make_state()
    for _ in range(3):
        run(state, {"type": "fluid", "fluid_type": "normal saline", "volume_ml": 500}, wait(10))
    assert state["treatments"]["total_crystalloid_ml"] == 1500
    assert state["observable"]["sbp"] == 104
    assert state["generated_state"]["exposure"]["fluid"] == 2


def test_pending_studies_freeze_at_collection_and_serial_results_follow_new_state():
    state = make_state()
    run(state, {"type": "diagnostic", "diagnostic": "poc_glucose"}, {"type": "dextrose", "dose_g": 25, "route": "IV"}, {"type": "diagnostic", "diagnostic": "basic_labs"})
    first = deepcopy(state["diagnostic_history"])
    assert state["observable"]["glucose_mg_dl"] == 174
    assert state["diagnostics"]["basic_labs"]["glucose_mg_dl"] == 74
    assert state["diagnostics"]["basic_labs"]["collected_at_min"] == 0
    assert state["diagnostics"]["basic_labs"]["time_min"] == 10
    run(state, {"type": "diagnostic", "diagnostic": "poc_glucose"})
    assert state["diagnostics"]["poc_glucose"]["glucose_mg_dl"] == 174
    assert "report" not in state["diagnostics"]["poc_glucose"]
    assert state["diagnostic_history"][:len(first)] == first
    assert state["treatments"]["administered_medications"][0] == {"agent": "dextrose", "dose_g": 25, "route": "IV", "time_min": 0}


def test_examination_and_appearance_follow_same_numeric_state_and_reset_after_recovery():
    state = make_state()
    run(state, wait(30))
    assert state["observable"]["mental_status"] == "Drowsy"
    assert state["observable"]["visual"]["mottling"] is True
    assert "voice" in current_findings(state)["Neurological"]
    run(state, {"type": "fluid", "fluid_type": "normal saline", "volume_ml": 500})
    assert state["observable"]["mental_status"] == "Alert"
    assert state["observable"]["visual"]["mottling"] is False
    assert "Alert" in current_findings(state)["Neurological"]


def test_explicit_zero_effect_is_executed_but_unmodeled_action_is_not():
    state = make_state()
    before = deepcopy(state)
    result = execute_generated_bundle(state, {"actions": [{"type": "aspirin", "dose_mg": 324, "route": "PO"}]})
    assert not result["executed"] and state == before
    state["encounter_spec"]["clinical_case"]["engine"]["response_rules"].append(rule("aspirin", "aspirin", {}, agent="aspirin", route="PO", dose_field="dose_mg", reference_dose=324))
    result = run(state, {"type": "aspirin", "dose_mg": 324, "route": "PO"})
    assert result["action_summaries"][0]["dose_mg"] == 324
    assert state["observable"]["hr"] == 114


def test_wrong_route_or_agent_rejects_whole_bundle():
    state = make_state()
    before = deepcopy(state)
    result = execute_generated_bundle(state, {"actions": [{"type": "fluid", "fluid_type": "normal saline", "volume_ml": 500}, {"type": "dextrose", "dose_g": 25, "route": "PO"}]})
    assert not result["executed"]
    assert state == before


def test_active_infusion_replacement_uses_current_rate_and_stop_removes_effect():
    state = make_state()
    state["encounter_spec"]["clinical_case"]["engine"]["response_rules"].append(rule("pressor", "norepinephrine", {"sbp": 20}, agent="norepinephrine", route="IV", units="mcg/min", dose_field="rate", reference_dose=10, duration_min=1))
    run(state, {"type": "norepinephrine", "rate": 10, "units": "mcg/min"})
    assert state["observable"]["sbp"] == 110
    run(state, {"type": "norepinephrine", "operation": "adjust", "rate": 5, "units": "mcg/min"})
    assert state["observable"]["sbp"] == 100
    assert state["treatments"]["norepinephrine_rate"] == 5
    run(state, {"type": "norepinephrine", "operation": "stop"})
    assert state["observable"]["sbp"] == 89
    assert not state["treatments"]["norepinephrine"]


def test_weight_based_units_cannot_borrow_absolute_rate_effect():
    state = make_state()
    state["encounter_spec"]["clinical_case"]["engine"]["response_rules"].append(rule("pressor", "norepinephrine", {"sbp": 20}, agent="norepinephrine", route="IV", units="mcg/min", dose_field="rate", reference_dose=10))
    before = deepcopy(state)
    result = execute_generated_bundle(state, {"actions": [{"type": "norepinephrine", "rate": .1, "units": "mcg/kg/min"}]})
    assert not result["executed"] and state == before


def test_respiratory_device_matches_are_exact_and_never_restore_stale_support():
    state = make_state()
    rules = state["encounter_spec"]["clinical_case"]["engine"]["response_rules"]
    rules.extend([rule("oxygen", "oxygen", {"spo2": 4}, device="Nasal cannula", dose_field="flow_lpm", reference_dose=4, duration_min=1, max_exposure=1),
                  rule("niv", "niv", {"spo2": 5}, dose_field=None, reference_dose=None, duration_min=1, max_exposure=1)])
    run(state, {"type": "oxygen", "device": "nasal cannula", "flow_lpm": 4})
    assert state["observable"]["spo2"] == 97
    run(state, {"type": "niv", "mode": "BiPAP", "ipap_cmh2o": 12, "epap_cmh2o": 6, "fio2_percent": 50})
    assert state["observable"]["spo2"] == 98
    run(state, {"type": "niv", "operation": "stop"})
    assert state["observable"]["spo2"] == 93
    assert state["observable"]["respiratory_support"] == "Room air"


def test_bias_grades_and_reasoning_never_drive_physiology():
    left, right = make_state(), make_state()
    left.update(score=100, bias_id="anchoring", working_model="correct")
    right.update(score=0, bias_id="confirmation", working_model="incorrect")
    run(left, wait(40))
    run(right, wait(40))
    assert left["observable"] == right["observable"]
    assert left["generated_state"] == right["generated_state"]


def test_horizon_rejection_is_atomic_including_prior_valid_order():
    state = make_state()
    run(state, wait(120))
    before = deepcopy(state)
    result = execute_generated_bundle(state, {"actions": [{"type": "fluid", "fluid_type": "normal saline", "volume_ml": 500}, wait(61)]})
    assert not result["executed"] and state == before


def test_gas_bindings_recompute_ph_without_changing_old_specimen():
    state = make_state()
    state["encounter_spec"]["clinical_case"]["engine"]["untreated_drift_per_min"]["pco2_mm_hg"] = 1
    state["encounter_spec"]["clinical_case"]["engine"]["horizon_min"] = 60
    run(state, {"type": "diagnostic", "diagnostic": "vbg"})
    first = deepcopy(state["diagnostics"]["vbg"])
    run(state, {"type": "diagnostic", "diagnostic": "vbg"})
    new = state["diagnostics"]["vbg"]
    assert first["pco2_mm_hg"] == 32 and new["pco2_mm_hg"] == 37
    assert new["ph"] == round(6.1 + math.log10(18 / (.03 * 37)), 2)
    assert state["diagnostic_history"][0]["result"] == first


def test_ecg_dynamic_profile_is_snapshot_and_never_mutates_case():
    state = make_state()
    case = state["encounter_spec"]["clinical_case"]
    case["engine"]["state_rules"][0]["set"]["ecg_profile"] = "st_depression"
    frozen = deepcopy(case)
    run(state, {"type": "diagnostic", "diagnostic": "ecg"})
    first = deepcopy(state["diagnostics"]["ecg"])
    run(state, wait(30))
    assert state["ecg_profile"] == "st_depression"
    run(state, {"type": "diagnostic", "diagnostic": "ecg"})
    assert state["diagnostics"]["ecg"][:len(first)] == first
    assert state["encounter_spec"]["clinical_case"] == frozen


@pytest.mark.parametrize("mutation", [
    lambda c: c["engine"]["untreated_drift_per_min"].update(score=4),
    lambda c: c["engine"]["untreated_drift_per_min"].update(sbp=float("nan")),
    lambda c: c["engine"]["response_rules"][0].update(reference_dose=0),
    lambda c: c["engine"]["response_rules"][0].update(dose_field="score"),
    lambda c: c["engine"]["state_rules"][0]["when"][0].update(field="working_model"),
    lambda c: c["engine"]["state_rules"][0]["set"].update(ecg_profile="invented"),
    lambda c: c["investigations"]["poc_glucose"]["result_bindings"].update(glucose_mg_dl="grade"),
    lambda c: c["observable"].update(sbp=50, dbp=90),
])
def test_runtime_revalidates_declarations_instead_of_trusting_llm_or_persisted_data(mutation):
    state = make_state()
    mutation(state["encounter_spec"]["clinical_case"])
    before = deepcopy(state)
    with pytest.raises(ValueError):
        validate_declarative_case(state["encounter_spec"]["clinical_case"])
    result = execute_generated_bundle(state, {"actions": [wait(5)]})
    assert not result["executed"] and state == before


def test_unavailable_result_is_not_fabricated_and_admin_order_does_not_invent_treatment():
    state = make_state()
    run(state, {"type": "consult", "service": "endocrinology"})
    assert state["sim_time"] == 0
    assert state["observable"]["sbp"] == 90
    result = execute_generated_bundle(state, {"actions": [{"type": "diagnostic", "diagnostic": "unknown"}]})
    assert not result["executed"]
    assert "glucose" not in clinical_update(state).lower()


def test_concurrent_fluid_orders_cannot_outpace_their_combined_actual_delivery():
    state = make_state()
    run(state, {"type": "fluid", "fluid_type": "normal saline", "volume_ml": 500},
        {"type": "fluid", "fluid_type": "normal saline", "volume_ml": 500}, wait(10))
    assert state["treatments"]["total_crystalloid_ml"] == 500
    assert state["observable"]["sbp"] == 98
    run(state, wait(10))
    assert state["treatments"]["total_crystalloid_ml"] == 1000
    assert state["observable"]["sbp"] == 106


def test_combined_out_of_scope_effects_decline_atomically_without_silent_clamp():
    state = make_state()
    rules = state["encounter_spec"]["clinical_case"]["engine"]["response_rules"]
    rules.extend([rule("oxygen", "oxygen", {"spo2": 5}, device="Nasal cannula", dose_field="flow_lpm", reference_dose=4, duration_min=1, max_exposure=1),
                  rule("antidote", "naloxone", {"spo2": 5}, agent="naloxone", route="IV", dose_field="dose_mg", reference_dose=.4, duration_min=1, max_exposure=1)])
    before = deepcopy(state)
    result = execute_generated_bundle(state, {"actions": [{"type": "oxygen", "device": "nasal cannula", "flow_lpm": 4}, {"type": "naloxone", "dose_mg": .4, "route": "IV"}]})
    assert not result["executed"] and state == before
    assert "No orders" in result["clarification"]


@pytest.mark.parametrize("extra_rule", [
    rule("unknown_bronchodilator", "bronchodilator", {}, agent="invented_drug", route="nebulized", dose_field="dose_mg", reference_dose=5),
    rule("unknown_steroid", "steroid", {}, agent="budesonide", route="PO", dose_field="dose_mg", reference_dose=5),
    rule("invalid_route", "naloxone", {}, agent="naloxone", route="transdermal", dose_field="dose_mg", reference_dose=.4),
    rule("invalid_units", "anticoagulation", {}, agent="heparin", route="IV", units="mL", dose_field="dose", reference_dose=5000),
    rule("invalid_rate", "norepinephrine", {}, agent="norepinephrine", route="IV", units="mcg/kg/min", dose_field="rate", reference_dose=20),
    rule("invalid_mass", "dextrose", {}, agent="dextrose", route="IV", dose_field="dose_g", reference_dose=100),
    rule("invalid_device", "oxygen", {}, device="high flow vapor", dose_field="flow_lpm", reference_dose=4),
    rule("invalid_flow", "oxygen", {}, device="Nasal cannula", dose_field="flow_lpm", reference_dose=100),
    rule("unreachable_route_alias", "naloxone", {}, agent="naloxone", route="intravenous", dose_field="dose_mg", reference_dose=.4),
])
def test_generation_rejects_treatment_rules_the_live_order_contract_cannot_execute(extra_rule):
    state = make_state()
    case = state["encounter_spec"]["clinical_case"]
    case["engine"]["response_rules"].append(extra_rule)
    with pytest.raises(ValueError):
        validate_declarative_case(case)
    before = deepcopy(state)
    result = execute_generated_bundle(state, {"actions": [wait(1)]})
    assert not result["executed"] and state == before


@pytest.mark.parametrize("extra_rule, action", [
    (rule("known_bronchodilator", "bronchodilator", {}, agent="albuterol", route="nebulized", units="mg", dose_field="dose_mg", reference_dose=5), {"type": "bronchodilator", "agent": "albuterol", "route": "nebulized", "dose_mg": 5}),
    (rule("known_steroid", "steroid", {}, agent="hydrocortisone", route="IV", dose_field="dose_mg", reference_dose=100), {"type": "steroid", "agent": "hydrocortisone", "route": "IV", "dose_mg": 100}),
    (rule("ventilation", "intubation", {}, dose_field=None, reference_dose=None), {"type": "intubation", "ventilator_mode": "VC/AC", "fio2_percent": 50, "peep_cmh2o": 5}),
])
def test_generation_accepts_declared_reachable_medication_and_support_rules(extra_rule, action):
    state = make_state()
    state["encounter_spec"]["clinical_case"]["engine"]["response_rules"].append(extra_rule)
    validate_declarative_case(state["encounter_spec"]["clinical_case"])
    run(state, action)
