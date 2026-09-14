from copy import deepcopy
import pytest
from family_parser import parse_family_actions
from generated_engine import execute_generated_bundle
from test_generated_engine import make_state, rule


@pytest.mark.parametrize('text', [
    'start oxygen 4 L/min nasal cannula',
    'start oxygen 4 L/min nasal canula',
    'O2 4lt NC',
    'iniciar O₂ 4 l/min naricera',
    'aplicar oxígeno 4 lpm cánula nasal',
])
def test_oxygen_free_text(text):
    assert parse_family_actions(text)['actions'] == [dict(type='oxygen', device='nasal cannula', flow_lpm=4)]


@pytest.mark.parametrize('dose', ['.4', '0.4', '0,4'])
def test_small_dose(dose):
    a = parse_family_actions(f'give naloxone {dose} mg IV')['actions'][0]
    assert a['dose_mg'] == .4 and a['route'] == 'IV'


def test_screenshot_bundle_executes_actual_doses_and_studies():
    text = ('patient in shock. start oxygen 4 L/min nasal canula, give 1000 cc NS. '
            'Want POCUS, VBG, lactate and reassess for bp, hr and perfusion in 10 minutes')
    parsed = parse_family_actions(text)
    assert [a['type'] for a in parsed['actions']] == ['oxygen', 'fluid', 'diagnostic', 'diagnostic', 'diagnostic', 'reassessment']
    state = make_state()
    case = state['encounter_spec']['clinical_case']
    case['engine']['response_rules'].append(rule('oxygen', 'oxygen', {'spo2': 3}, device='Nasal cannula', dose_field='flow_lpm', reference_dose=4, max_exposure=1))
    case['investigations']['pocus'] = {'duration_min': 0, 'result': {'report': 'Test fixture'}}
    case['investigations']['lactate'] = {'duration_min': 5, 'result': {'lactate_mmol_l': 3.1}}
    result = execute_generated_bundle(state, parsed)
    assert result['executed'], result
    assert state['observable']['spo2'] == 96
    assert state['family_state']['pending_fluid_ml'] == 500
    assert state['treatments']['total_crystalloid_ml'] == 500
    assert set(state['diagnostics']) >= {'pocus', 'vbg', 'lactate'}
    assert state['sim_time'] == 10


def test_missing_response_identifies_understood_order_without_mutation():
    state = make_state()
    before = deepcopy(state)
    result = execute_generated_bundle(state, parse_family_actions('O2 4lt NC'))
    assert not result['executed'] and state == before
    assert 'Order understood: oxygen, 4 L/min, Nasal cannula' in result['clarification']
    assert 'Rewording' in result['clarification']


@pytest.mark.parametrize('text', ['Do not give naloxone .4 mg IV', 'If worse, start O2 4lt NC', 'I expect O2 4lt NC to improve saturation'])
def test_no_inferred_administration(text):
    assert not parse_family_actions(text)['actions']


def test_spanish_fluid_and_oxygen_keep_separate_quantities():
    a = parse_family_actions('Administro 1 lt SF; iniciar O₂ 4 l/min naricera')['actions']
    assert a[0]['volume_ml'] == 1000 and a[1]['flow_lpm'] == 4


def test_oxygen_hourly_units_are_not_silently_read_as_per_minute():
    assert parse_family_actions('O2 4 l/hr NC')['actions'][0]['type'] == 'clarification'


@pytest.mark.parametrize('text,expected', [
    ('give 1000 NS', 1000), ('give NS 500', 500),
    ('give half a liter of saline', 500), ('give one liter NS', 1000),
    ('give 500 milliliters saline', 500),
])
def test_reused_previous_branch_fluid_quantities(text, expected):
    a = parse_family_actions(text)['actions'][0]
    assert a['type'] == 'fluid' and a['volume_ml'] == expected


def test_reused_parser_does_not_choose_between_conflicting_volumes():
    state = make_state()
    before = deepcopy(state)
    result = execute_generated_bundle(state, parse_family_actions('give 500 ml or 1000 ml NS'))
    assert not result['executed'] and state == before
