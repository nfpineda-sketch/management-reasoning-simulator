from copy import deepcopy
import pytest
from family_parser import parse_family_actions
from generated_engine import execute_generated_bundle, validate_declarative_case
from pending_family_orders import hold_incomplete_bundle, complete_bundle
from test_generated_engine import make_state, rule


def run(state,text):
    result=execute_generated_bundle(state,parse_family_actions(text))
    assert result['executed'],result
    return result


def test_contextual_fluid_repetition_retains_type_and_independent_actual_dose():
    state=make_state()
    run(state,'Give 500 mL NS; reassess in 10 minutes')
    run(state,'Repeat the same bolus; reassess in 10 minutes')
    run(state,'Give another 250 mL; reassess in 5 minutes')
    assert state['treatments']['total_crystalloid_ml']==1250
    assert len(state['treatments']['order_history'])==3


def test_explicit_repeated_medication_preserves_identity_and_route():
    state=make_state()
    state['encounter_spec']['clinical_case']['engine']['response_rules'].append(rule('beta','beta_blocker',{'hr':-10},agent='metoprolol',route='IV',dose_field='dose_mg',reference_dose=5,max_exposure=2))
    run(state,'Give metoprolol 5 mg IV; reassess in 10 minutes')
    run(state,'Repeat metoprolol; reassess in 10 minutes')
    assert [m['dose_mg'] for m in state['treatments']['administered_medications']]==[5,5]
    assert state['observable']['hr']==94


@pytest.mark.parametrize('text',['Repeat the same bolus','If worse, repeat the same bolus','Do not repeat the bolus'])
def test_repeat_never_invents_a_previous_administration(text):
    state=make_state();before=deepcopy(state)
    result=execute_generated_bundle(state,parse_family_actions(text))
    assert not result['executed'] and state==before


@pytest.mark.parametrize('initial,replies,expected',[
    ('Start oxygen 4 L/min',['NC'],{'device':'nasal cannula','flow_lpm':4}),
    ('Start oxygen NC',['4 L/min'],{'device':'nasal cannula','flow_lpm':4}),
    ('Start norepinephrine .1',['mcg/kg/min'],{'rate':.1,'units':'mcg/kg/min'}),
    ('Start nitroglycerin',['10 mcg/min'],{'rate_mcg_min':10}),
    ('Start BiPAP',['IPAP 12 EPAP 6','FiO2 40%'],{'mode':'BiPAP','ipap_cmh2o':12,'epap_cmh2o':6,'fio2_percent':40}),
])
def test_missing_support_parameters_can_be_completed_without_repeating_bundle(initial,replies,expected):
    parsed=parse_family_actions(initial+'; give 500 mL NS; reassess in 5 minutes')
    for reply in replies:
        pending=hold_incomplete_bundle(parsed)
        assert pending is not None,(initial,parsed)
        completed=complete_bundle(pending,reply)
        assert completed and 'parsed' in completed,(initial,reply,completed)
        parsed=completed['parsed']
    assert all(parsed['actions'][0].get(k)==v for k,v in expected.items()),parsed
    assert parsed['actions'][1]['volume_ml']==500
    assert parsed['actions'][2]['delay_min']==5


def test_labs_do_not_delay_reassessment_and_keep_original_specimen():
    state=make_state()
    run(state,'Get basic labs; give dextrose 25 g IV; reassess in 1 minute')
    assert state['sim_time']==1 and 'basic_labs' not in state['diagnostics']
    assert state['pending_investigations'][0]['available_at_min']==10
    assert 'result' not in state['pending_investigations'][0]
    run(state,'reassess in 9 minutes')
    assert state['diagnostics']['basic_labs']['glucose_mg_dl']==74
    assert state['observable']['glucose_mg_dl']==174
    assert state['diagnostics']['basic_labs']['collected_at_min']==0
    assert not state['pending_investigations']


def test_timed_fluid_delivery_changes_actual_volume_not_only_label():
    state=make_state()
    run(state,'Give 500 mL NS over 20 minutes; reassess in 5 minutes')
    assert state['treatments']['total_crystalloid_ml']==125
    assert state['family_state']['pending_fluid_ml']==375
    run(state,'reassess in 15 minutes')
    assert state['treatments']['total_crystalloid_ml']==500


def test_timed_medication_preserves_delivery_duration_and_administered_amount():
    state=make_state()
    state['encounter_spec']['clinical_case']['engine']['response_rules'].append(rule('amio','amiodarone',{'hr':-20},agent='amiodarone',route='IV',dose_field='dose_mg',reference_dose=150,duration_min=1,max_exposure=1))
    result=run(state,'Give amiodarone 150 mg IV over 10 minutes; reassess in 5 minutes')
    med=state['treatments']['administered_medications'][0]
    assert med['dose_mg']==75 and med['ordered_dose_mg']==150
    assert med['administration_status']=='in_progress'
    assert result['action_summaries'][0]['administration_duration_min']==10
    assert state['observable']['hr']==104
    run(state,'reassess in 5 minutes')
    assert state['treatments']['administered_medications'][0]['dose_mg']==150
    assert state['treatments']['administered_medications'][0]['administration_status']=='completed'


def test_dobutamine_starts_adjusts_continues_and_stops_separately_from_other_support():
    state=make_state()
    state['encounter_spec']['clinical_case']['engine']['response_rules'].append(rule('dob','dobutamine',{'sbp':10},agent='dobutamine',route='IV',units='mcg/kg/min',dose_field='rate',reference_dose=5,max_exposure=2,duration_min=1))
    run(state,'Start dobutamine 5 mcg/kg/min; reassess in 1 minute')
    run(state,'Increase dobutamine to 10 mcg/kg/min; reassess in 1 minute')
    run(state,'Continue dobutamine; reassess in 1 minute')
    assert state['treatments']['dobutamine_rate']==10
    run(state,'Stop dobutamine; reassess in 1 minute')
    assert not state['treatments']['dobutamine']


def test_sedation_effect_recedes_and_baseline_mental_status_returns():
    state=make_state()
    state['encounter_spec']['clinical_case']['engine']['response_rules'].append(rule('sed','procedural_sedation',{'sbp':-6},agent='midazolam',route='IV',dose_field='dose_mg',reference_dose=2,duration_min=1,recovery_min=4,mental_status_during='Sedated',mental_status_threshold=.25,max_exposure=2))
    run(state,'Give midazolam 2 mg IV; reassess in 1 minute')
    assert state['observable']['mental_status']=='Sedated'
    run(state,'reassess in 4 minutes')
    assert state['observable']['mental_status']=='Alert'
    assert state['observable']['sbp']==89  # Untreated drift remains; drug effect has worn off.
    run(state,'Give midazolam 2 mg IV; reassess in 1 minute')
    assert state['observable']['mental_status']=='Sedated'


def test_pocus_follows_delivered_fluid_and_does_not_rewrite_prior_exam():
    state=make_state();case=state['encounter_spec']['clinical_case']
    case['investigations']['pocus']={'duration_min':0,'result':{'ivc':'Small','lungs':'No diffuse B-lines'}}
    case['engine']['state_rules'].append({'when':[{'field':'fluid_delivered_ml','operator':'gte','value':500}], 'set':{},'diagnostic_updates':{'pocus':{'ivc':'Larger','lungs':'Diffuse B-lines'}}})
    run(state,'Get POCUS')
    prior=deepcopy(state['diagnostic_history'][0])
    run(state,'Give 500 mL NS; reassess in 10 minutes')
    run(state,'Get POCUS')
    assert state['diagnostics']['pocus']['lungs']=='Diffuse B-lines'
    assert state['diagnostic_history'][0]==prior


def test_ventilator_interpolates_patient_authored_grid_without_extrapolation():
    state=make_state();rules=state['encounter_spec']['clinical_case']['engine']['response_rules']
    rules.append(rule('intubation','intubation',{},dose_field=None,reference_dose=None))
    for fi in (30,70):
        for peep in (5,15):
            rules.append(rule(f'vent_{fi}_{peep}','ventilator_adjustment',{'spo2':(fi-30)/20+(peep-5)/10},dose_field=None,reference_dose=None,settings={'fio2_percent':fi,'peep_cmh2o':peep},interpolate_settings=True,duration_min=1,max_exposure=1))
    run(state,'Intubate VC/AC FiO2 50% PEEP 5; reassess in 1 minute')
    run(state,'Set FiO2 50% PEEP 10; reassess in 1 minute')
    assert state['treatments']['ventilator_peep_cmh2o']==10
    assert state['generated_state']['values']['spo2']==94.5
    assert state['observable']['spo2']==94
    before=deepcopy(state)
    result=execute_generated_bundle(state,parse_family_actions('Set FiO2 90%'))
    assert not result['executed'] and state==before


def test_repeated_investigation_never_repeats_previous_drug():
    state = make_state()
    run(state, 'Give 500 mL NS; reassess in 10 minutes')
    run(state, 'Repeat VBG')
    assert len(state['treatments']['order_history']) == 1
    assert 'vbg' in state['diagnostics']


def test_ambiguous_repeat_quantity_does_not_fall_back_to_previous_dose():
    state = make_state()
    run(state, 'Give 500 mL NS; reassess in 10 minutes')
    before = deepcopy(state)
    result = execute_generated_bundle(state, parse_family_actions('Repeat bolus 250 mL or 500 mL'))
    assert not result['executed'] and state == before


def test_sedation_keeps_focal_arrival_examination():
    from generated_engine import current_findings
    state = make_state()
    state['encounter_spec']['clinical_case']['examination']['Neurological'] = 'Right arm weakness.'
    state['encounter_spec']['clinical_case']['engine']['response_rules'].append(rule('sed','procedural_sedation',{},agent='midazolam',route='IV',dose_field='dose_mg',reference_dose=2,duration_min=1,recovery_min=4,mental_status_during='Sedated',mental_status_threshold=.25))
    run(state, 'Give midazolam 2 mg IV; reassess in 1 minute')
    findings = current_findings(state)['Neurological']
    assert 'Right arm weakness' in findings and 'Sedated' in findings


def test_old_session_pending_fluid_survives_delivery_queue_migration():
    state = make_state()
    run(state, 'Give 500 mL NS; reassess in 5 minutes')
    del state['generated_state']['deliveries']
    run(state, 'Give 500 mL NS; reassess in 10 minutes')
    assert state['treatments']['total_crystalloid_ml'] == 750
    assert state['family_state']['pending_fluid_ml'] == 250


def test_respiratory_percentage_alias_and_explicit_mode_adjustment():
    action = parse_family_actions('Start BiPAP 12/6 O2 40%')['actions'][0]
    assert action['fio2_percent'] == 40 and action['ipap_cmh2o'] == 12
    action = parse_family_actions('Set PC/AC FiO2 50% PEEP 10')['actions'][0]
    assert action['type'] == 'respiratory_adjustment' and action['ventilator_mode'] == 'PC/AC'


def test_new_case_requires_explicit_pocus_stability_or_dynamic_findings():
    from generated_case_coverage import coverage_issues
    state = make_state(); case = state['encounter_spec']['clinical_case']
    case['investigations']['pocus'] = {'duration_min':0,'result':{'ivc':'Small'}}
    assert 'POCUS' in str(coverage_issues(case))
    case['engine']['stable_diagnostics'] = ['pocus']
    assert 'POCUS' not in str(coverage_issues(case))


def test_new_case_rejects_incomplete_ventilator_grid_and_permanent_sedation():
    from generated_case_coverage import coverage_issues
    case = make_state()['encounter_spec']['clinical_case']
    rules = case['engine']['response_rules']
    rules.append(rule('intubation','intubation',{},dose_field=None,reference_dose=None))
    rules.append(rule('sed','procedural_sedation',{},agent='midazolam',route='IV',dose_field='dose_mg',reference_dose=2))
    for fi, peep in [(30,5),(40,6),(50,7),(60,8)]:
        rules.append(rule(f'vent_{fi}','ventilator_adjustment',{},dose_field=None,reference_dose=None,settings={'fio2_percent':fi,'peep_cmh2o':peep},interpolate_settings=True))
    issues = str(coverage_issues(case))
    assert 'ventilation' in issues and 'sedation' in issues


@pytest.mark.parametrize('text', ['Repeat dopamine', 'Repeat bolus 250', 'Repeat LR'])
def test_repeat_never_substitutes_unknown_treatment_or_invents_units(text):
    state = make_state()
    run(state, 'Give 500 mL NS; reassess in 10 minutes')
    before = deepcopy(state)
    result = execute_generated_bundle(state, parse_family_actions(text))
    assert not result['executed'] and state == before
