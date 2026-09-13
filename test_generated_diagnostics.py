"""A missing model binding cannot freeze a changing or inconsistent test."""
from copy import deepcopy
import pytest

from generated_case import GeneratedCaseError, generate_ai_encounter
from generated_case_schema import compile_case
from generated_engine import execute_generated_bundle, validate_declarative_case
from test_generated_case import AuthorClient, clean_base, novel_payload
from test_generated_engine import make_state, run, wait


def test_omitted_binding_does_not_accept_glucose_inconsistent_with_patient():
    raw = novel_payload()
    raw['investigations'][0]['result_bindings'] = []
    raw['investigations'][0]['result'][0]['value'] = 20
    client = AuthorClient(raw)
    with pytest.raises(GeneratedCaseError):
        generate_ai_encounter('R1-05', clean_base(), client=client)
    assert len(client.calls) == 1  # Block before an approving reviewer can mask it.


@pytest.mark.parametrize('measurement,value', [('glucose_mg_dl', 20), ('hemoglobin_g_dl', 3)])
def test_runtime_rejects_inconsistent_unbound_numeric_results_before_any_order(measurement, value):
    state = make_state()
    study = state['encounter_spec']['clinical_case']['investigations']['basic_labs']
    study['result_bindings'] = {}
    study['result'][measurement] = value
    original = deepcopy(state)
    with pytest.raises(ValueError, match='Initial results conflict'):
        validate_declarative_case(state['encounter_spec']['clinical_case'])
    result = execute_generated_bundle(state, {'actions': [wait(2)]})
    assert not result['executed']
    assert state == original


def test_compilation_explicitly_freezes_derived_bindings_for_all_modeled_measurements():
    raw = novel_payload()
    for study in raw['investigations']:
        study['result_bindings'] = []
    compiled = compile_case(raw)
    assert compiled['investigations']['poc_glucose']['result_bindings'] == {'glucose_mg_dl': 'glucose_mg_dl'}
    assert compiled['investigations']['temperature']['result_bindings'] == {'temperature_c': 'temperature_c'}
    assert compiled['investigations']['basic_labs']['result_bindings'] == {
        'hemoglobin_g_dl': 'hemoglobin_g_dl', 'glucose_mg_dl': 'glucose_mg_dl'}
    assert compiled['investigations']['cortisol']['result_bindings'] == {}
    assert raw['investigations'][0]['result_bindings'] == []


def test_unbound_glucose_tracks_physiology_and_past_sample_remains_frozen():
    state = make_state()
    case = state['encounter_spec']['clinical_case']
    case['engine']['untreated_drift_per_min']['glucose_mg_dl'] = 1
    case['investigations']['poc_glucose']['result_bindings'] = {}
    case['investigations']['poc_glucose']['duration_min'] = 2
    frozen_spec = deepcopy(state['encounter_spec'])
    run(state, {'type': 'diagnostic', 'diagnostic': 'poc_glucose'})
    first = deepcopy(state['diagnostics']['poc_glucose'])
    run(state, wait(5))
    assert state['observable']['glucose_mg_dl'] == 81
    run(state, {'type': 'diagnostic', 'diagnostic': 'poc_glucose'})
    latest = state['diagnostics']['poc_glucose']
    assert first['glucose_mg_dl'] == 74
    assert latest['glucose_mg_dl'] == 81  # Collection, not availability at minute9.
    assert latest['collected_at_min'] == 7 and latest['time_min'] == 9
    assert state['diagnostic_history'][0]['result'] == first
    assert state['encounter_spec'] == frozen_spec
    assert 'report' not in latest  # The old "Glucose74" prose cannot contradict81.


def test_omitting_gas_bindings_does_not_freeze_co2_or_ph_after_state_changes():
    state = make_state()
    case = state['encounter_spec']['clinical_case']
    case['investigations']['vbg']['result_bindings'] = {}
    case['engine']['untreated_drift_per_min']['pco2_mm_hg'] = 1
    case['engine']['horizon_min'] = 60
    run(state, {'type': 'diagnostic', 'diagnostic': 'vbg'})
    first = deepcopy(state['diagnostics']['vbg'])
    run(state, {'type': 'diagnostic', 'diagnostic': 'vbg'})
    second = state['diagnostics']['vbg']
    assert first['pco2_mm_hg'] == 32 and second['pco2_mm_hg'] == 37
    assert second['ph'] < first['ph']
    assert state['diagnostic_history'][0]['result'] == first


def test_nonnumeric_glucose_cannot_bypass_binding_and_measurement_checks():
    raw = novel_payload()
    raw['investigations'][0]['result_bindings'] = []
    raw['investigations'][0]['result'][0]['value'] = 'severely low'
    with pytest.raises(ValueError, match='numerical initial'):
        compile_case(raw)
