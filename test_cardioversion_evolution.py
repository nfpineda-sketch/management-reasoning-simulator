from copy import deepcopy
import pytest
from family_parser import parse_family_actions
from generated_engine import execute_generated_bundle, validate_declarative_case
from test_generated_engine import make_state, rule


def patient(legacy=False, recurrence=None):
    state=make_state();case=state['encounter_spec']['clinical_case']
    case['observable']['rhythm']='AF';state['observable']['rhythm']='AF'
    case['engine']['untreated_drift_per_min']={}
    response=rule('shock','cardioversion',{'hr':-34},dose_field=None,reference_dose=None,
                  settings={'energy_j':200},rhythm_after='sinus rhythm',max_exposure=2)
    if not legacy: response['rhythm_before']='af'
    if recurrence: response['recurrence']=recurrence
    case['engine']['response_rules'].append(response)
    return state


def run(state,text):
    result=execute_generated_bundle(state,parse_family_actions(text))
    assert result['executed'],result
    return result


SHOCK='Perform synchronized cardioversion 200 J; reassess in 0 minutes'
RECURRENCE={'after_min':5,'when':[], 'rhythm_after':'af','delta':{}}


@pytest.mark.parametrize('legacy',[False,True])
def test_second_shock_does_not_repeat_conversion_benefit(legacy):
    state=patient(legacy)
    run(state,SHOCK)
    assert state['observable']['hr']==80
    before=deepcopy(state)
    result=execute_generated_bundle(state,parse_family_actions(SHOCK))
    assert not result['executed'] and state==before


def test_explicit_same_rhythm_adverse_response_preserves_prior_conversion():
    state=patient(recurrence=RECURRENCE)
    state['encounter_spec']['clinical_case']['engine']['response_rules'].append(rule('adverse','cardioversion',{'sbp':-5},dose_field=None,reference_dose=None,settings={'energy_j':200},rhythm_before='sinus',rhythm_after='sinus rhythm'))
    run(state,SHOCK); result=run(state,SHOCK)
    assert state['observable']['hr']==80 and state['observable']['sbp']==85
    assert result['action_summaries'][0]['rhythm_before']=='sinus rhythm'
    run(state,'reassess in 5 minutes')
    assert state['observable']['rhythm']=='af' and state['observable']['hr']==114
    assert state['observable']['sbp']==85


def test_recurrence_is_relative_to_conversion_and_reconversion_does_not_stack():
    state=patient(recurrence=RECURRENCE)
    run(state,'reassess in 10 minutes');run(state,SHOCK)
    run(state,'reassess in 4 minutes')
    assert state['observable']['rhythm']=='sinus rhythm'
    run(state,'Get ECG; reassess in 0 minutes')
    run(state,'reassess in 1 minute')
    assert state['observable']['rhythm']=='af' and state['observable']['hr']==114
    assert state['diagnostics']['ecg'][-1]['rhythm']=='sinus'
    assert state['rhythm_history'][-1]['time_min']==15
    run(state,SHOCK)
    assert state['observable']['hr']==80
    run(state,'reassess in 4 minutes')
    assert state['observable']['rhythm']=='sinus rhythm'
    run(state,'reassess in 1 minute')
    assert state['observable']['rhythm']=='af'
    assert [e['time_min'] for e in state['rhythm_history'] if e['kind']=='recurrence']==[15,20]


def test_treating_trigger_can_prevent_recurrence():
    recurrence={**RECURRENCE,'when':[{'field':'glucose_mg_dl','operator':'lt','value':100}]}
    untreated=patient(recurrence=recurrence);treated=patient(recurrence=recurrence)
    run(untreated,SHOCK);run(treated,SHOCK)
    run(treated,'Give dextrose 25 g IV; reassess in 5 minutes')
    run(untreated,'reassess in 5 minutes')
    assert untreated['observable']['rhythm']=='af'
    assert treated['observable']['rhythm']=='sinus rhythm'


def test_stable_conversion_does_not_recur_automatically():
    state=patient();run(state,SHOCK);run(state,'reassess in 60 minutes')
    assert state['observable']['rhythm']=='sinus rhythm' and state['observable']['hr']==80


def test_compound_shocks_are_matched_sequentially_and_failure_is_atomic():
    state=patient();before=deepcopy(state)
    text='Cardiovert 200 J; Cardiovert 200 J'
    assert not execute_generated_bundle(state,parse_family_actions(text))['executed']
    assert state==before


def test_unsuccessful_shock_does_not_schedule_recurrence_or_block_retry():
    state=patient()
    state['encounter_spec']['clinical_case']['engine']['response_rules'].append(rule('failed','cardioversion',{},dose_field=None,reference_dose=None,settings={'energy_j':100},rhythm_before='af',rhythm_after='af'))
    run(state,'Cardiovert 100 J');run(state,'Cardiovert 100 J')
    assert state['observable']['hr']==114 and state['observable']['rhythm']=='AF'
    run(state,SHOCK)
    assert state['observable']['hr']==80


@pytest.mark.parametrize('recurrence',[
    {**RECURRENCE,'after_min':0},
    {**RECURRENCE,'rhythm_after':'vf'},
    {**RECURRENCE,'delta':{'hr':1000}},
    {**RECURRENCE,'when':[{'field':'learner_score','operator':'gt','value':0}]},
])
def test_invalid_recurrence_rejected(recurrence):
    with pytest.raises(ValueError): validate_declarative_case(patient(recurrence=recurrence)['encounter_spec']['clinical_case'])


def test_explicit_shorthand_shock_is_not_silently_dropped():
    state=patient()
    run(state,'Synchronized cardioversion 200 J; reassess in 0 minutes')
    assert state['observable']['hr']==80 and len(state['treatments']['cardioversions'])==1


def test_generation_rejects_missing_rhythm_or_ambiguous_shock_responses():
    from generated_case_coverage import coverage_issues
    case=patient(legacy=True)['encounter_spec']['clinical_case']
    assert 'pre- and post-shock rhythms' in str(coverage_issues(case))
    case=patient()['encounter_spec']['clinical_case']
    duplicate=deepcopy(case['engine']['response_rules'][-1]);duplicate['id']='other';duplicate['rhythm_before']='atrial fibrillation'
    case['engine']['response_rules'].append(duplicate)
    assert 'unambiguous response' in str(coverage_issues(case))


def test_generated_schema_compiles_recurrence_for_execution():
    from test_generated_case import novel_payload
    from generated_case_schema import compile_case
    raw=novel_payload();raw['observable']['rhythm']='af'
    shock=deepcopy(raw['engine']['response_rules'][0])
    shock.update(id='shock',action_type='cardioversion',dose_field=None,reference_dose=None,onset_min=0,duration_min=1,max_exposure=1,
                 state_gain=None,settings=[{'field':'energy_j','value':200}],rhythm_before='af',rhythm_after='sinus rhythm',
                 delta=[{'field':'hr','value':-34}],recurrence={'after_min':5,'when':[], 'rhythm_after':'af','delta':[]})
    raw['engine']['response_rules'].append(shock)
    case=compile_case(raw)
    compiled=case['engine']['response_rules'][-1]
    assert compiled['recurrence']['delta']=={} and compiled['rhythm_before']=='af'
