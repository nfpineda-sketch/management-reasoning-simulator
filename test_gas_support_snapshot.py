from copy import deepcopy
from family_parser import parse_family_actions
from generated_engine import execute_generated_bundle
from test_generated_engine import make_state,rule


def run(state,text):
    result=execute_generated_bundle(state,parse_family_actions(text))
    assert result['executed'],result


def test_abg_keeps_support_at_sampling_through_delay_and_subsequent_adjustment():
    state=make_state();case=state['encounter_spec']['clinical_case']
    case['investigations']['abg']={'duration_min':5,'result':{'pao2_mm_hg':70,'fio2_percent':21,'pf_ratio':333,'report':'Baseline room air.'},'result_bindings':{'pao2_mm_hg':'pao2_mm_hg'}}
    case['engine']['response_rules'].extend([
        rule('intubation','intubation',{},dose_field=None,reference_dose=None),
        rule('vent','ventilator_adjustment',{},dose_field=None,reference_dose=None,settings={'fio2_percent':40,'peep_cmh2o':8})])
    run(state,'Intubate VC/AC FiO2 60% PEEP 8; get ABG; reassess in 0 minutes')
    assert 'abg' not in state['diagnostics']
    run(state,'Set FiO2 40%; reassess in 5 minutes')
    result=state['diagnostics']['abg']
    assert result['fio2_percent']==60 and result['pf_ratio']==117
    assert result['collected_at_min']==0 and 'report' not in result
    assert state['treatments']['ventilator_fio2_percent']==40
    previous=deepcopy(state['diagnostic_history'])
    run(state,'Get ABG')
    assert state['diagnostics']['abg']['fio2_percent']==40
    assert state['diagnostics']['abg']['pf_ratio']==175
    assert state['diagnostic_history'][:len(previous)]==previous


def test_vbg_does_not_report_arterial_pf_ratio():
    state=make_state();state['encounter_spec']['clinical_case']['investigations']['vbg']['result']['pf_ratio']=300
    run(state,'Get VBG')
    assert state['diagnostics']['vbg']['fio2_percent']==21
    assert 'pf_ratio' not in state['diagnostics']['vbg']
