from copy import deepcopy
import pytest
from test_generated_engine import make_state,rule,wait
from clinical_core_defaults import INITIAL_HIDDEN,PHENOTYPE_FIELDS,CORE_VERSION
import coupled_encounter as adapter
from generated_engine import execute_generated_bundle


def patient(**hidden):
    s=make_state();s['seed']=17;e=s['encounter_spec']['clinical_case']['engine']
    e['model']=CORE_VERSION
    e['core_profile']={'version':CORE_VERSION,'infection_active':True,'initial_hidden':{k:INITIAL_HIDDEN[k] for k in PHENOTYPE_FIELDS}}
    e['core_profile']['initial_hidden'].update(hidden)
    e['untreated_drift_per_min']={}
    s['observable']['rhythm']='AF';s['encounter_spec']['clinical_case']['observable']['rhythm']='AF'
    adapter.initialize(s)
    return s


def run(s,*actions):
    r=execute_generated_bundle(s,{'actions':list(actions)});assert r['executed'],r
    return r


@pytest.mark.parametrize('action',[
 {'type':'beta_blocker','agent':'metoprolol','dose_mg':5,'route':'IV'},
 {'type':'beta_blocker','agent':'propranolol','dose_mg':1,'route':'IV'},
 {'type':'diltiazem','agent':'diltiazem','dose_mg':15,'route':'IV'},
 {'type':'amiodarone','agent':'amiodarone','dose_mg':150,'route':'IV'},
 {'type':'diuretic','agent':'furosemide','dose_mg':40,'route':'IV'},
 {'type':'norepinephrine','operation':'start','rate':.1,'units':'mcg/kg/min'},
 {'type':'dobutamine','operation':'start','rate':5,'units':'mcg/kg/min'},
 {'type':'nitroglycerin','operation':'start','rate_mcg_min':20},
 {'type':'oxygen','device':'Nasal cannula','flow_lpm':4},
 {'type':'cardioversion','energy_j':200,'synchronized':True},
 {'type':'procedural_sedation','agent':'etomidate','dose_mg':10,'route':'IV'},
 {'type':'niv','operation':'start','mode':'BiPAP','ipap_cmh2o':10,'epap_cmh2o':5,'fio2_percent':50},
 {'type':'intubation','ventilator_mode':'VC/AC','fio2_percent':60,'peep_cmh2o':8},
])
def test_native_actions_use_same_engine_and_do_not_require_case_response_rules(action):
    s=patient();reference=deepcopy(s['coupled_state'])
    # Independent native calls: this does not reuse the adapter's action dispatcher.
    k=action['type']
    if k=='beta_blocker':adapter.call(reference,'beta_blocker_transition',action['agent'],action['dose_mg'],action['route'])
    elif k in {'diltiazem','amiodarone'}:adapter.call(reference,k+'_transition',action['dose_mg'],action['route'])
    elif k=='diuretic':adapter.call(reference,'furosemide_transition',40,'IV')
    elif k=='norepinephrine':adapter.call(reference,'norepinephrine_transition',.1,'mcg/kg/min','start')
    elif k=='dobutamine':adapter.call(reference,'dobutamine_transition',5,'mcg/kg/min','start')
    elif k=='nitroglycerin':adapter.call(reference,'nitroglycerin_transition',20,'start')
    elif k=='oxygen':adapter.call(reference,'oxygen_transition','Nasal cannula',4)
    elif k=='cardioversion':adapter.call(reference,'cardioversion_transition',200)
    elif k=='procedural_sedation':adapter.call(reference,'procedural_sedation_transition',[{'agent':'etomidate','dose':10,'units':'mg','route':'IV'}])
    elif k=='niv':adapter.call(reference,'niv_transition','BiPAP',5,'start',10,5,50)
    elif k=='intubation':adapter.call(reference,'intubation_transition','VC/AC',60,8)
    else:raise AssertionError('Missing independent native reference')
    for i in range(5):
        adapter.call(reference,'apply_natural_disease',1);reference['sim_time']+=1
    run(s,action,wait(5))
    assert s['coupled_state']['hidden']==reference['hidden']
    assert s['coupled_state']['observable']==reference['observable']


def test_multiple_supports_and_titration_keep_one_native_state():
    s=patient();run(s,{'type':'oxygen','device':'Nasal cannula','flow_lpm':4},wait(2))
    run(s,{'type':'norepinephrine','operation':'start','rate':.1,'units':'mcg/kg/min'},wait(5))
    before=deepcopy(s['coupled_state']['hidden'])
    run(s,{'type':'norepinephrine','operation':'stop'},wait(2))
    assert s['coupled_state']['treatments']['oxygen']
    assert not s['coupled_state']['treatments']['norepinephrine']
    assert s['coupled_state']['hidden']!=before


def test_fluid_delivery_uses_original_transition_at_actual_delivery():
    s=patient();run(s,{'type':'fluid','fluid_type':'normal saline','volume_ml':1000},wait(1))
    assert s['treatments']['total_crystalloid_ml']==50
    assert s['coupled_state']['treatments']['cumulative_crystalloid_ml']==50
    assert s['hidden']['effective_intravascular_fluid']>0
    assert 'compartments' not in s['generated_state']


def test_core_ignores_authored_fake_oxygen_response():
    a=patient();b=deepcopy(a)
    b['encounter_spec']['clinical_case']['engine']['response_rules'].append(rule('o2','oxygen',{'spo2':-10},device='Nasal cannula',dose_field='flow_lpm',reference_dose=4,max_exposure=1))
    action={'type':'oxygen','device':'Nasal cannula','flow_lpm':4}
    run(a,action,wait(5));run(b,action,wait(5));assert a['observable']==b['observable']


def test_retry_and_rng_are_replayable_and_atomic():
    a=patient();b=deepcopy(a)
    rejected=execute_generated_bundle(a,{'actions':[{'type':'cardioversion','energy_j':200,'synchronized':True},{'type':'unsupported'}]})
    assert not rejected['executed'] and a==b
    for s in (a,b):run(s,{'type':'cardioversion','energy_j':200,'synchronized':True},wait(5))
    assert a==b


def test_noninfectious_patient_does_not_acquire_infectious_drift():
    s=patient(inflammatory_drive=0);s['coupled_state']['physiology_parameters']['infection_active']=False
    run(s,wait(10));assert s['hidden']['inflammatory_drive']==0


def test_lab_and_pocus_samples_follow_shared_state_but_keep_history():
    s=patient();s['encounter_spec']['clinical_case']['investigations']['pocus']={'duration_min':2,'result':{'lv':'preserved','rv':'RV dilated','lungs':'clear'}}
    run(s,{'type':'diagnostic','diagnostic':'pocus'});old=deepcopy(s['diagnostic_history'])
    run(s,{'type':'beta_blocker','agent':'metoprolol','route':'IV','dose_mg':5},wait(20))
    run(s,{'type':'diagnostic','diagnostic':'pocus'})
    assert s['diagnostic_history'][:len(old)]==old
    assert s['diagnostics']['pocus']['rv']=='RV dilated'


def test_weight_based_units_are_equivalent_in_the_shared_core():
    a=patient();b=deepcopy(a)
    for s,rate,units in [(a,.1,'mcg/kg/min'),(b,7,'mcg/min')]:
        run(s,{'type':'norepinephrine','operation':'start','rate':rate,'units':units},wait(10))
    assert a['observable']==b['observable']
    a=patient();b=deepcopy(a)
    for s,rate,units in [(a,5,'mcg/kg/min'),(b,350,'mcg/min')]:
        run(s,{'type':'dobutamine','operation':'start','rate':rate,'units':units},wait(10))
    assert a['observable']==b['observable']


def test_timed_drug_delivery_only_administers_actual_dose():
    s=patient();run(s,{'type':'amiodarone','agent':'amiodarone','dose_mg':150,'route':'IV','administration_duration_min':30},wait(5))
    assert s['coupled_state']['treatments']['amiodarone_total_mg']==25
    assert s['treatments']['administered_medications'][-1]['dose_mg']==25


def test_live_dispatch_refuses_old_independent_engine_and_accepts_native_cases():
    from family_engine import execute_family_bundle
    assert not execute_family_bundle(make_state(),{'actions':[wait(1)]})['executed']
    assert execute_family_bundle(patient(),{'actions':[wait(1)]})['executed']


def test_non_af_cardioversion_keeps_declared_rhythm_outcome_but_uses_native_flow():
    s=patient();s['coupled_state']['observable']['rhythm']='svt';s['observable']['rhythm']='svt'
    s['encounter_spec']['clinical_case']['engine']['response_rules'].append(rule('shock','cardioversion',{},dose_field=None,reference_dose=None,onset_min=0,duration_min=1,max_exposure=1,settings={'energy_j':100},rhythm_before='svt',rhythm_after='sinus rhythm'))
    run(s,{'type':'cardioversion','energy_j':100,'synchronized':True},wait(1))
    assert s['observable']['rhythm']=='Sinus rhythm'
    assert s['hidden']['cardiac_output_index']>0


def test_step_down_from_niv_does_not_leave_physiological_niv_active():
    s=patient();run(s,{'type':'niv','operation':'start','mode':'BiPAP','ipap_cmh2o':10,'epap_cmh2o':5,'fio2_percent':50},wait(1))
    run(s,{'type':'oxygen','device':'Nasal cannula','flow_lpm':4},wait(1))
    assert not s['coupled_state']['treatments']['niv']
    assert s['coupled_state']['treatments']['oxygen']
    assert s['treatment_timeline']['niv']['active'] is False


def test_unknown_beta_agent_is_not_substituted_with_propranolol():
    s=patient();before=deepcopy(s)
    result=execute_generated_bundle(s,{'actions':[{'type':'beta_blocker','agent':'atenolol','route':'IV','dose_mg':5}]})
    assert not result['executed'] and s==before


def test_native_no_extra_treatment_has_no_declared_response_requirement():
    s=patient();s['encounter_spec']['clinical_case']['engine']['response_rules']=[]
    run(s,{'type':'oxygen','device':'Nasal cannula','flow_lpm':4},wait(3))
    assert s['coupled_state']['treatments']['oxygen']


def test_small_sedative_dose_does_not_create_full_sedation():
    s=patient();run(s,{'type':'procedural_sedation','agent':'etomidate','dose_mg':.01,'route':'IV'},wait(0))
    assert s['observable']['mental_status']!='Sedated'


def test_terminal_core_state_preserves_electrical_morphology_for_monitor():
    from ecg12 import monitor_wave_svg
    s=patient();native=s['coupled_state'];native['observable'].update(rhythm='PEA',electrical_rhythm='AF',pulse_present=False,sbp=0,dbp=0,spo2=None,crt=None)
    native['hidden'].update(cardiac_arrest=True,terminal_collapse=True)
    adapter.project(s)
    assert '<svg' in monitor_wave_svg(s['observable'])
    before=deepcopy(s);assert not execute_generated_bundle(s,{'actions':[wait(1)]})['executed'];assert s==before


def test_authored_recovery_cannot_contradict_native_neurological_state():
    from generated_engine import current_findings
    s=patient()
    case=s['encounter_spec']['clinical_case']
    case['engine']['state_rules']=[{'when':[{'field':'spo2','operator':'gte','value':30}],
        'set':{'mental_status':'Alert'},'examination':{'Neurological':'Fully recovered and alert.'}}]
    s['coupled_state']['observable']['mental_status']='Drowsy'
    adapter.project(s)
    findings=current_findings(s)
    assert 'Fully recovered and alert.' not in findings['Neurological']
    assert 'Mental status: Drowsy' in findings['Neurological']


def test_native_model_identity_requires_native_profile():
    from generated_engine import validate_declarative_case
    case=deepcopy(patient()['encounter_spec']['clinical_case'])
    case['engine'].pop('core_profile')
    with pytest.raises(ValueError):validate_declarative_case(case)
