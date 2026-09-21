from copy import deepcopy
import pytest
from family_parser import parse_family_actions
from generated_engine import execute_generated_bundle, validate_declarative_case
from test_generated_engine import make_state, rule
from generated_case_coverage import coverage_issues


def execute(state, text):
    result = execute_generated_bundle(state, parse_family_actions(text))
    assert result['executed'], result
    return result


def setup_support():
    state = make_state()
    rules = state['encounter_spec']['clinical_case']['engine']['response_rules']
    rules.extend([
        rule('oxygen', 'oxygen', {'spo2': 3}, device='Nasal cannula', dose_field='flow_lpm', reference_dose=4, max_exposure=1),
        rule('pressor', 'norepinephrine', {'sbp': 10}, agent='norepinephrine', route='IV', units='mcg/kg/min', dose_field='rate', reference_dose=.1, max_exposure=2),
        rule('vent', 'intubation', {}, dose_field=None, reference_dose=None),
        rule('vent_adjust', 'ventilator_adjustment', {'spo2': 2}, dose_field=None, reference_dose=None, settings={'fio2_percent': 40, 'peep_cmh2o': 5}),
    ])
    return state


def test_continue_preserves_support_response_clock_and_does_not_repeat_bolus():
    state = setup_support()
    execute(state, 'Give 500 mL NS; start oxygen NC 4 L/min; start norepinephrine .1 mcg/kg/min; reassess in 5 minutes')
    before = {e['rule_id']: e['started_at'] for e in state['generated_state']['events']}
    execute(state, 'Continue oxygen and continue norepinephrine; reassess in 5 minutes')
    assert state['observable']['spo2'] == 96
    assert state['treatments']['total_crystalloid_ml'] == 500
    assert state['family_state']['pending_fluid_ml'] == 0
    assert {e['rule_id']:e['started_at'] for e in state['generated_state']['events']} == before


def test_partial_oxygen_and_pressor_adjustments_keep_explicit_active_context():
    state = setup_support()
    execute(state, 'Start oxygen NC 4 L/min; start norepinephrine .05 mcg/kg/min; reassess in 1 minute')
    result = execute(state, 'Decrease O2 to 2 L/min; increase norepinephrine .1 mcg/kg/min; reassess in 1 minute')
    assert state['treatments']['oxygen_device'] == 'Nasal cannula'
    assert state['treatments']['oxygen_flow_lpm'] == 2
    assert state['treatments']['norepinephrine_rate'] == .1
    assert result['action_summaries'][0]['device'] == 'Nasal cannula'


def test_ventilator_adjustment_does_not_reintubate_or_stop_pressor():
    state = setup_support()
    execute(state, 'Start norepinephrine .05 mcg/kg/min; intubate VC/AC FiO2 50% PEEP 5; reassess in 1 minute')
    result = execute(state, 'Decrease FiO2 to 40%; reassess in 1 minute')
    assert state['treatments']['ventilator_fio2_percent'] == 40
    assert state['treatments']['ventilator_peep_cmh2o'] == 5
    assert state['treatments']['norepinephrine_rate'] == .05
    assert result['action_summaries'][0]['type'] == 'ventilator_adjustment'
    assert 'intubation' not in [a['type'] for a in result['action_summaries']]


@pytest.mark.parametrize('text', ['Continue oxygen', 'Increase norepinephrine .1 mcg/kg/min', 'Decrease FiO2 to 40%'])
def test_missing_active_context_never_invents_starting_treatment(text):
    state = setup_support()
    before = deepcopy(state)
    result = execute_generated_bundle(state, parse_family_actions(text))
    assert not result['executed'] and state == before


def test_sedation_shock_and_immediate_ecg_are_ordered_recorded_and_executed():
    state = make_state()
    case = state['encounter_spec']['clinical_case']
    case['observable']['rhythm'] = 'atrial fibrillation'
    state['observable']['rhythm'] = 'atrial fibrillation'
    case['engine']['response_rules'].extend([
        rule('sedation', 'procedural_sedation', {'sbp': -3}, agent='etomidate', route='IV', dose_field='dose_mg', reference_dose=8, max_exposure=1, duration_min=1),
        rule('shock', 'cardioversion', {'hr': -34}, dose_field=None, reference_dose=None, settings={'energy_j': 200}, rhythm_after='sinus rhythm', max_exposure=1),
    ])
    result = execute(state, 'Give etomidate 8 mg IV; cardiovert 200 J; get ECG; reassess immediately')
    assert [a['type'] for a in result['action_summaries']] == ['procedural_sedation', 'cardioversion']
    assert state['sim_time'] == 0
    assert state['pending_investigations'][0]['diagnostic_type'] == 'ecg'
    execute(state, 'reassess in 1 minute')
    assert state['treatments']['administered_medications'][0]['dose_mg'] == 8
    assert state['treatments']['cardioversions'][0]['energy_j'] == 200
    assert state['observable']['rhythm'] == 'sinus rhythm'
    assert state['observable']['hr'] == 80
    assert state['diagnostics']['ecg'][-1]['rhythm'] == 'sinus'


def test_missing_shock_energy_or_unmodeled_energy_cannot_claim_execution():
    for text in ['Cardiovert', 'Cardiovert 100 J']:
        state = make_state()
        before = deepcopy(state)
        result = execute_generated_bundle(state, parse_family_actions(text))
        assert not result['executed'] and state == before


def test_generation_coverage_identifies_missing_oxygen_interfaces_and_authored_medication():
    state = make_state()
    case = state['encounter_spec']['clinical_case']
    case['observable']['spo2'] = 86
    case['faculty'] = {'anticipated_management_paths': ['Administer etomidate, then perform cardioversion.']}
    missing = coverage_issues(case)[0]['details']['missing']
    assert set(missing) == {'fluid: explicit volume compartments', 'fluid: explicit state-dependent response curve', 'oxygen: nasal cannula', 'oxygen: simple mask', 'oxygen: non-rebreather mask', 'procedural_sedation: etomidate', 'cardioversion'}
    # This is an authoring-only gate: do not mutate stored attempts to fill gaps.
    validate_declarative_case(case)


def test_sequential_support_in_one_bundle_can_use_newly_ordered_settings():
    state = setup_support()
    execute(state, 'Intubate VC/AC FiO2 50% PEEP 5; decrease FiO2 to 40%; reassess in 1 minute')
    assert state['treatments']['ventilator_fio2_percent'] == 40
    assert state['treatments']['ventilator_peep_cmh2o'] == 5


def test_pending_dose_and_route_replies_preserve_other_orders_and_reasoning():
    from pending_family_orders import hold_incomplete_bundle, complete_bundle
    parsed = parse_family_actions('Give etomidate; cardiovert 200 J; reassess in 1 minute')
    parsed['reasoning'] = {'expected_effect': 'Improved perfusion'}
    pending = hold_incomplete_bundle(parsed)
    assert pending is not None
    first = complete_bundle(pending, '8 mg')['parsed']
    assert first['actions'][0]['dose_mg'] == 8 and first['actions'][0]['route'] is None
    second = complete_bundle(hold_incomplete_bundle(first), 'IV')['parsed']
    assert second['actions'][0]['route'] == 'IV'
    assert second['actions'][1:] == parsed['actions'][1:]
    assert second['reasoning'] == parsed['reasoning']
    assert parsed['actions'][0]['dose_mg'] is None
    assert complete_bundle(pending, 'Do not give etomidate') is None


def test_completed_fluid_followup_executes_once_with_original_reassessment():
    from pending_family_orders import hold_incomplete_bundle, complete_bundle
    state = make_state()
    parsed = parse_family_actions('Give normal saline; reassess in 5 minutes')
    failed = execute_generated_bundle(state, parsed)
    assert not failed['executed'] and state['sim_time'] == 0
    completed = complete_bundle(hold_incomplete_bundle(parsed), '500 mL')['parsed']
    result = execute_generated_bundle(state, completed)
    assert result['executed'] and state['sim_time'] == 5
    assert state['treatments']['total_crystalloid_ml'] == 250
    assert state['family_state']['pending_fluid_ml'] == 250


def test_unsupported_settings_cannot_be_reported_as_successful_adjustment():
    state = setup_support()
    execute(state, 'Intubate VC/AC FiO2 50% PEEP 5')
    before = deepcopy(state)
    result = execute_generated_bundle(state, parse_family_actions('Set FiO2 80%'))
    assert not result['executed'] and state == before


@pytest.mark.parametrize('text,kind,agent,dose', [
    ('Give metoprolol 2.5 mg IV', 'beta_blocker', 'metoprolol', 2.5),
    ('Give dilt 5 mg IV', 'diltiazem', 'diltiazem', 5),
    ('Administrar amiodarona 150 mg EV', 'amiodarone', 'amiodarone', 150),
])
def test_prior_rhythm_medications_use_patient_authored_effects(text,kind,agent,dose):
    state = make_state()
    state['encounter_spec']['clinical_case']['engine']['response_rules'].append(
        rule('rhythm_drug', kind, {'hr': -10, 'sbp': -3}, agent=agent, route='IV', dose_field='dose_mg', reference_dose=dose, max_exposure=1, duration_min=1))
    execute(state, text + '; reassess in 1 minute')
    assert state['treatments']['administered_medications'][0] == {'agent': agent, 'dose_mg': dose, 'route':'IV', 'time_min':0}
    assert state['observable']['hr'] == 104


def test_new_actions_survive_faculty_evidence_selection_without_private_rules():
    from test_faculty_analysis import sample_record
    from faculty_analysis import build_analysis_source
    record = sample_record()
    event = record['payload']['session']['management_trace'][0]
    event['execution_status'] = 'executed'
    event['action_summaries'] = [
        {'type':'procedural_sedation','agent':'etomidate','dose_mg':8,'route':'IV'},
        {'type':'cardioversion','energy_j':200,'synchronized':True},
        {'type':'ventilator_adjustment','fio2_percent':40,'peep_cmh2o':5},
    ]
    actions = build_analysis_source(record)['decision_events'][0]['executed_action_summaries']
    assert actions == event['action_summaries']


def test_live_app_adapter_holds_and_completes_generated_fluid_bundle():
    import ast
    from pathlib import Path
    from types import SimpleNamespace
    class Session(dict):
        __getattr__ = dict.get
        __setattr__ = dict.__setitem__
    from test_coupled_encounter import patient
    session = Session(state=patient(), pending_action=None)
    namespace = {'st': SimpleNamespace(session_state=session)}
    tree = ast.parse(Path('app.py').read_text())
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)
                 and n.name in {'execute_bundle', 'try_resolve_pending_action',
                                '_held_order_prompt', '_reasoning_gate_action_summary',
                                'procedural_sedation_label'}]
    constants = [n for n in tree.body if isinstance(n, ast.Assign)
                 and any(getattr(t, 'id', '') == 'REASONING_GATE_ACTION_TYPES' for t in n.targets)]
    functions = constants + functions
    exec(compile(ast.Module(body=functions,type_ignores=[]), 'app.py', 'exec'), namespace)
    original = parse_family_actions('Give NS; reassess in 5 minutes')
    assert not namespace['execute_bundle'](original)['executed']
    assert session.pending_action['type'] == 'family_bundle'
    completed = namespace['try_resolve_pending_action']('500 mL')
    assert session.pending_action is None
    assert namespace['execute_bundle'](completed['parsed'])['executed']
    assert session.state['sim_time'] == 5
