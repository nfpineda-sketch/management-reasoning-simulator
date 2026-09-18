from copy import deepcopy
import pytest
from family_parser import parse_family_actions
from pending_family_orders import hold_incomplete_bundle, complete_bundle
from pending_cancellation import clear_pending_orders, is_cancellation
from generated_engine import execute_generated_bundle, _surface, validate_declarative_case
from test_generated_engine import make_state, rule


def run(state, text):
    result = execute_generated_bundle(state, parse_family_actions(text))
    assert result['executed'], result
    return result


def patient():
    state = make_state()
    state['encounter_spec']['clinical_case']['engine']['untreated_drift_per_min'] = {}
    return state


@pytest.mark.parametrize('text', ['cancel', 'Cancel pending orders', 'Cancelar la orden pendiente'])
def test_cancellation_only_clears_unexecuted_work(text):
    state = patient()
    session = {'state':state,'events':['prior'], 'pending_action':{'type':'family_bundle'},'pending_reasoning':{'parsed':{}}, 'pending_bundle':{'actions':[]}}
    before = deepcopy(state)
    assert is_cancellation(text) and clear_pending_orders(session)
    assert session['state'] == before and session['events'] == ['prior']
    assert all(session[k] is None for k in ['pending_action','pending_reasoning','pending_bundle'])
    assert not clear_pending_orders(session)


@pytest.mark.parametrize('text',['Do not cancel the order','Cancel norepinephrine','Cancel pending orders and give 500 mL NS'])
def test_cancellation_requires_unambiguous_standalone_request(text):
    assert not is_cancellation(text)


def test_prepare_airway_does_not_intubate_or_sedate():
    state=patient()
    run(state,'Prepare for intubation')
    assert state['treatments']['airway_prepared'] and state['sim_time']==2
    assert not state['treatments'].get('invasive_ventilation')
    assert state['observable']['mental_status']=='Alert'


@pytest.mark.parametrize('text',['Do not prepare for intubation','If worse, prepare for intubation'])
def test_prepare_respects_negation_and_condition(text):
    state=patient(); before=deepcopy(state)
    assert not execute_generated_bundle(state,parse_family_actions(text))['executed']
    assert state==before


@pytest.mark.parametrize('initial,reply,field,value',[
    ('Give heparin 5000 units','IV','route','IV'),
    ('Give heparin IV','5000 units','dose',5000),
    ('Transfuse blood','2 units','units',2),
])
def test_complete_anticoagulant_and_transfusion_preserves_remaining_bundle(initial,reply,field,value):
    p=hold_incomplete_bundle(parse_family_actions(initial+'; reassess in 5 minutes'))
    assert p
    result=complete_bundle(p,reply)['parsed']['actions']
    assert result[0][field]==value and result[1]['delay_min']==5


def infusion_state():
    state=patient()
    state['encounter_spec']['clinical_case']['engine']['response_rules'].append(rule('dob','dobutamine',{'sbp':10},agent='dobutamine',route='IV',units='mcg/kg/min',dose_field='rate',reference_dose=5,duration_min=4,washout_min=4))
    return state


def test_infusion_reduction_and_stop_are_continuous_and_continue_does_not_restart():
    state=infusion_state()
    run(state,'Start dobutamine 10 mcg/kg/min; reassess in 4 minutes')
    assert state['observable']['sbp']==110
    run(state,'Decrease dobutamine to 5 mcg/kg/min; reassess in 0 minutes')
    assert state['observable']['sbp']==110
    run(state,'Continue dobutamine; reassess in 2 minutes')
    assert state['observable']['sbp']==105
    run(state,'reassess in 2 minutes')
    assert state['observable']['sbp']==100
    run(state,'Stop dobutamine; reassess in 0 minutes')
    assert state['observable']['sbp']==100 and not state['treatments']['dobutamine']
    run(state,'reassess in 2 minutes')
    assert state['observable']['sbp']==95
    run(state,'Stop dobutamine; reassess in 2 minutes')
    assert state['observable']['sbp']==90


def test_fixed_drug_recovers_and_can_be_given_again():
    state=patient()
    state['encounter_spec']['clinical_case']['engine']['response_rules'].append(rule('beta','beta_blocker',{'hr':-10},agent='metoprolol',route='IV',dose_field='dose_mg',reference_dose=5,duration_min=1,recovery_min=4,max_exposure=1))
    run(state,'Give metoprolol 5 mg IV; reassess in 1 minute')
    assert state['observable']['hr']==104
    run(state,'reassess in 4 minutes')
    assert state['observable']['hr']==114
    run(state,'Repeat metoprolol; reassess in 1 minute')
    assert state['observable']['hr']==104


def test_fluid_benefit_and_harm_change_with_delivered_volume():
    state=patient();rules=state['encounter_spec']['clinical_case']['engine']['response_rules']
    rules[0]['state_gain']={'field':'fluid_delivered_ml','points':[{'value':0,'factor':1},{'value':500,'factor':1},{'value':1000,'factor':.25}]}
    rules.append(rule('congestion','fluid',{'spo2':-6},state_gain={'field':'fluid_delivered_ml','points':[{'value':500,'factor':0},{'value':1000,'factor':1}]}))
    run(state,'Give 500 mL NS; reassess in 10 minutes')
    assert state['observable']['sbp']==100 and state['observable']['spo2']==93
    run(state,'Repeat the same bolus; reassess in 10 minutes')
    assert state['observable']['sbp']==95 and state['observable']['spo2']==81
    before=deepcopy(state)
    _surface(state);_surface(state)
    assert state==before


def test_response_can_depend_on_rate_from_another_treatment():
    state=patient();rules=state['encounter_spec']['clinical_case']['engine']['response_rules']
    rules[0]['state_gain']={'field':'hr','points':[{'value':100,'factor':1},{'value':114,'factor':0}]}
    run(state,'Give 500 mL NS; reassess in 10 minutes')
    assert state['observable']['sbp']==90
    rules=state['encounter_spec']['clinical_case']['engine']['response_rules']
    rules.append(rule('beta','beta_blocker',{'hr':-14},agent='metoprolol',route='IV',dose_field='dose_mg',reference_dose=5,duration_min=1))
    run(state,'Give metoprolol 5 mg IV; reassess in 1 minute')
    assert state['observable']['sbp']==100


@pytest.mark.parametrize('points',[[{'value':10,'factor':1},{'value':5,'factor':0}], [{'value':0,'factor':2},{'value':1,'factor':0}]])
def test_invalid_coupling_is_rejected(points):
    state=patient();case=state['encounter_spec']['clinical_case']
    case['engine']['response_rules'][0]['state_gain']={'field':'hr','points':points}
    with pytest.raises(ValueError): validate_declarative_case(case)


def test_completed_heparin_and_blood_orders_execute_once():
    for initial,reply,response,field,value in [
        ('Give heparin 5000 units','IV',rule('heparin','anticoagulation',{},agent='heparin',route='IV',units='units',dose_field='dose',reference_dose=5000),'dose',5000),
        ('Transfuse blood','2 units',rule('blood','blood',{},dose_field='units',reference_dose=1),'packed_red_cells_units',2),
    ]:
        state=patient()
        state['encounter_spec']['clinical_case']['engine']['response_rules'].append(response)
        pending=hold_incomplete_bundle(parse_family_actions(initial))
        completed=complete_bundle(pending,reply)['parsed']
        assert execute_generated_bundle(state,completed)['executed']
        if field=='dose':
            assert len(state['treatments']['administered_medications'])==1
            assert state['treatments']['administered_medications'][0][field]==value
        else:
            assert state['treatments'][field]==value


def test_app_cancellation_records_event_and_preserves_patient():
    import ast
    from pathlib import Path
    from types import SimpleNamespace
    source=ast.parse(Path('app.py').read_text())
    fn=next(n for n in source.body if isinstance(n,ast.FunctionDef) and n.name=='cancel_pending_order')
    state=patient(); session={'state':state,'pending_action':{'type':'fluid'}}; events=[]
    namespace={'st':SimpleNamespace(session_state=session), 'clear_reasoning_gate_clarification':lambda:None, 'next_reasoning_gate_id':lambda:None, 'add_event':lambda *args:events.append(args)}
    exec(compile(ast.Module(body=[fn],type_ignores=[]),'app.py','exec'),namespace)
    before=deepcopy(state)
    assert namespace['cancel_pending_order']()
    assert session['state']==before and events[0][0]=='order_cancelled'


def test_infusion_increase_with_onset_does_not_drop_pressure():
    state=infusion_state()
    state['encounter_spec']['clinical_case']['engine']['response_rules'][-1]['onset_min']=2
    run(state,'Start dobutamine 5 mcg/kg/min; reassess in 6 minutes')
    values=[state['observable']['sbp']]
    run(state,'Increase dobutamine to 10 mcg/kg/min; reassess in 0 minutes')
    for _ in range(6):
        run(state,'reassess in 1 minute')
        values.append(state['observable']['sbp'])
    assert values==sorted(values) and values[-1]==110
