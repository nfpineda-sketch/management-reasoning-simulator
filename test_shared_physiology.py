"""Behavioral equivalence and coupled clinical encounter trajectories."""
from copy import deepcopy
import math
import pytest
from clinical_physiology import advance_volume, active_drug_fraction, exposure_effect
from generated_engine import execute_generated_bundle, _surface, validate_declarative_case, current_findings, clinical_update
from generated_physiology import VOLUME_FIELDS
from test_generated_engine import make_state, rule, run, wait

PARAMS={'initial_extravascular_ml':0,'redistribution_half_life_min':28,'clearance_half_life_min':120,'extravascular_fraction':.8,'diuresis_extravascular_fraction':.7}
CURVE={'saturating_weight':1,'progressive_weight':0,'rate':.95,'power':1.45,'onset_half_life_min':3.5,'elimination_half_life_min':60}

def patient(extra=0):
    s=make_state(); e=s['encounter_spec']['clinical_case']['engine'];e['untreated_drift_per_min']={}
    e['volume_model']={**PARAMS,'initial_extravascular_ml':extra}
    e['response_rules']=[rule('volume',delta={'sbp':10,'dbp':4},volume_basis='circulating',max_exposure=5),
        rule('congestion',delta={'spo2':-3},volume_basis='extravascular',max_exposure=2),
        rule('diuresis','diuretic',{},agent='furosemide',route='IV',dose_field='dose_mg',reference_dose=40,recovery_min=90,duration_min=5,diuresis_ml_min=8)]
    return s

def bolus(s):
    run(s,{'type':'fluid','volume_ml':500,'fluid_type':'normal saline'},wait(10))

@pytest.mark.parametrize('extra',[0,1000])
def test_volume_mass_conserved_during_bolus_redistribution_and_diuresis(extra):
    s=patient(extra);bolus(s)
    run(s,{'type':'diuretic','agent':'furosemide','route':'IV','dose_mg':40},wait(40))
    c=s['generated_state']['compartments']
    assert all(x>=0 for x in c.values())
    assert c['fluid_retained_ml']+c['fluid_extravascular_ml']+c['fluid_output_ml']-c['fluid_deficit_ml']==pytest.approx(500+extra)
    assert s['treatments']['total_crystalloid_ml']==500

def test_volume_benefit_wanes_as_congestion_persists():
    s=patient();bolus(s);early=deepcopy(s['observable'])
    run(s,wait(35))
    assert s['observable']['sbp']<early['sbp']
    assert s['observable']['spo2']<early['spo2']
    before=deepcopy(s);_surface(s);assert s==before

def test_diuresis_reduces_congestion_but_can_deplete_circulating_volume():
    wet=patient(1500); dry=patient()
    for s in [wet,dry]:
        run(s,{'type':'diuretic','agent':'furosemide','route':'IV','dose_mg':40},wait(35))
    assert wet['generated_state']['compartments']['fluid_extravascular_ml']<1500
    assert dry['generated_state']['compartments']['fluid_deficit_ml']>0
    assert dry['observable']['sbp']<90

def test_timed_delivery_conserves_actual_not_ordered_volume():
    s=patient();run(s,{'type':'fluid','volume_ml':1000,'fluid_type':'normal saline','administration_duration_min':100},wait(5))
    c=s['generated_state']['compartments']
    assert s['treatments']['total_crystalloid_ml']==50
    assert sum(c[k] for k in ['fluid_retained_ml','fluid_extravascular_ml','fluid_output_ml'])==pytest.approx(50)

@pytest.mark.parametrize('a,b',[(3.5,60),(3,90),(9,240),(3,3)])
def test_shared_kinetics_match_original_depot_recurrence(a,b):
    depot=1.;active=0.
    for n in range(1,181):
        transfer=depot*(1-math.exp(-math.log(2)/a));depot-=transfer
        active=active*math.exp(-math.log(2)/b)+transfer
        assert active_drug_fraction(n,a,b)==pytest.approx(active)

def drug_patient():
    s=make_state();e=s['encounter_spec']['clinical_case']['engine'];e['untreated_drift_per_min']={}
    e['response_rules']=[rule('nodal','beta_blocker',{'hr':-10},agent='metoprolol',route='IV',dose_field='dose_mg',reference_dose=5,onset_min=0,duration_min=1,max_exposure=5,recovery_min=60,exposure_curve=CURVE),
      rule('myocardial','beta_blocker',{'sbp':-1,'dbp':-.3},agent='metoprolol',route='IV',dose_field='dose_mg',reference_dose=5,onset_min=0,duration_min=1,max_exposure=5,recovery_min=60,exposure_curve={**CURVE,'saturating_weight':.48,'progressive_weight':.035,'rate':.58})]
    return s

def test_repeated_doses_pool_active_load_not_lifetime_cap_and_decay():
    s=drug_patient();a={'type':'beta_blocker','agent':'metoprolol','route':'IV','dose_mg':5}
    run(s,a,wait(10));first=deepcopy(s['observable']);run(s,a,wait(10));second=deepcopy(s['observable'])
    assert second['hr']<first['hr'] and second['sbp']<=first['sbp']
    run(s,wait(120));assert s['observable']['hr']>second['hr']
    run(s,a,wait(10));assert len(s['treatments']['administered_medications'])==3
    assert s['observable']['hr']<first['hr']

def test_nodal_saturation_and_progressive_myocardial_load_are_distinct():
    progressive={**CURVE,'saturating_weight':.48,'progressive_weight':.035,'rate':.58}
    assert exposure_effect(5,CURVE)-exposure_effect(4,CURVE)<exposure_effect(2,CURVE)-exposure_effect(1,CURVE)
    assert exposure_effect(5,progressive)-exposure_effect(4,progressive)>exposure_effect(5,CURVE)-exposure_effect(4,CURVE)

def test_sustained_terminal_state_preserves_electrical_activity_stops_clock_and_is_absorbing():
    s=patient();e=s['encounter_spec']['clinical_case']['engine'];e['terminal_rule']={'when':[{'field':'sbp','operator':'lt','value':95}],'sustained_min':3}
    result=run(s,wait(10)); assert result['elapsed_min']==3 and s['sim_time']==3
    assert s['observable']['hr']==114 and s['observable']['rhythm']=='PEA'
    assert s['observable']['pulse_present'] is False and s['observable']['spo2'] is None
    before=deepcopy(s);_surface(s);assert s==before
    assert not execute_generated_bundle(s,{'actions':[wait(10)]})['executed'];assert s==before
    assert 'No palpable pulse' in clinical_update(s)
    assert isinstance(current_findings(s),dict)

def test_correction_resets_sustained_low_flow_clock():
    s=patient();s['encounter_spec']['clinical_case']['engine']['terminal_rule']={'when':[{'field':'sbp','operator':'lt','value':90.5}],'sustained_min':3}
    run(s,wait(2));bolus(s)
    assert not s['hidden'].get('terminal_collapse')
    assert s['generated_state']['low_flow_minutes']==0

def test_compartment_drives_pocus_without_rewriting_previous_study():
    s=patient();c=s['encounter_spec']['clinical_case'];c['investigations']['pocus']={'duration_min':0,'result':{'lungs':'No B lines'}}
    c['engine']['state_rules'].append({'when':[{'field':'fluid_extravascular_ml','operator':'gt','value':100}], 'set':{},'diagnostic_updates':{'pocus':{'lungs':'B lines'}}})
    run(s,{'type':'diagnostic','diagnostic':'pocus'});early=deepcopy(s['diagnostic_history'][0])
    bolus(s);run(s,wait(30));run(s,{'type':'diagnostic','diagnostic':'pocus'})
    assert s['diagnostic_history'][0]==early
    assert s['diagnostics']['pocus']['lungs']=='B lines'

@pytest.mark.parametrize('field,value',[('redistribution_half_life_min',0),('extravascular_fraction',2),('initial_extravascular_ml',float('nan'))])
def test_bad_compartments_reject_atomically(field,value):
    s=patient();s['encounter_spec']['clinical_case']['engine']['volume_model'][field]=value
    before=deepcopy(s)
    assert not execute_generated_bundle(s,{'actions':[wait(5)]})['executed']
    assert s==before

def test_no_hidden_physiology_inferred_for_frozen_old_cases():
    s=make_state();run(s,wait(1));assert not s['generated_state'].get('compartments')


def test_equivalent_agents_share_active_load_without_duplicate_effects():
    same=drug_patient();mixed=drug_patient()
    for s in (same,mixed):
        rules=s['encounter_spec']['clinical_case']['engine']['response_rules']
        for r in list(rules):
            r['exposure_pool']=r['id']
            rules.append({**deepcopy(r),'id':r['id']+'_propranolol','agent':'propranolol'})
    met={'type':'beta_blocker','agent':'metoprolol','route':'IV','dose_mg':5}
    run(same,met,met,wait(10))
    run(mixed,met,{**met,'agent':'propranolol'},wait(10))
    assert same['observable']==mixed['observable']
    assert same['observable']['hr']<114


def test_duplicate_drug_in_pool_is_rejected_before_administration():
    s=drug_patient();rules=s['encounter_spec']['clinical_case']['engine']['response_rules']
    rules[0]['exposure_pool']='nodal'
    rules.append({**deepcopy(rules[0]),'id':'duplicate'})
    before=deepcopy(s)
    assert not execute_generated_bundle(s,{'actions':[wait(1)]})['executed']
    assert s==before
