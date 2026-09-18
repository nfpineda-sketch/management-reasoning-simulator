"""Explicit additive native-lab upgrade; no patient reset or authored overrides."""
from copy import deepcopy

def missing_native_studies(case):
    if not case.get('engine',{}).get('core_profile'): return {}
    labs=case['engine'].get('initial_labs',{})
    result={}
    for name,fields in [('vbg',('pco2_mm_hg','bicarbonate_mmol_l','lactate_mmol_l')),
                        ('abg',('pco2_mm_hg','bicarbonate_mmol_l','pao2_mm_hg')),
                        ('lactate',('lactate_mmol_l',))]:
        if name not in case.get('investigations',{}) and all(k in labs for k in fields):
            result[name]={'duration_min':3,'result':{k:labs[k] for k in fields},'result_bindings':{k:k for k in fields}}
    return result

def upgrade_studies(state):
    spec=state['encounter_spec'];case=deepcopy(spec['clinical_case'])
    additions=missing_native_studies(case)
    if not additions:return []
    case['investigations'].update(additions)
    from generated_engine import validate_declarative_case
    validate_declarative_case(case)
    spec['clinical_case']=case
    state.setdefault('case_compatibility_updates',[]).append({'version':'native_labs_v1','time_min':state['sim_time'],'added_studies':sorted(additions)})
    return sorted(additions)
