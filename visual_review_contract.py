"""Interpret observed devices separately from treatment and photographic limits."""
MONITORS = ('blood_pressure_cuff', 'pulse_oximeter', 'ecg_electrodes')
RESPIRATORY = {'nasal cannula': 'nasal_cannula', 'simple mask': 'simple_mask',
               'non-rebreather mask': 'non_rebreather_mask', 'niv': 'niv_mask',
               'bag-mask ventilation': 'bag_mask', 'invasive ventilation': 'endotracheal_tube'}
DEVICES = (*MONITORS, *RESPIRATORY.values(), 'other_active_treatment', 'unconnected_equipment')
FINDINGS = ('injury', 'bleeding', 'cyanosis', 'unrequested_active_treatment',
            'conflicting_monitor_value', 'diagnostic_label', 'other_clinical_conflict')
SKIN = ('natural_or_subtle_pallor', 'clear_pallor', 'marked_flushing', 'cyanosis', 'not_assessable')
OBSERVATIONS_SCHEMA = {
    'type':'object', 'additionalProperties':False,
    'properties':{
        'devices':{'type':'array','items':{'type':'string','enum':list(DEVICES)}},
        'unexpected_findings':{'type':'array','items':{'type':'string','enum':list(FINDINGS)}},
        'skin':{'type':'string','enum':list(SKIN)},
    }, 'required':['devices','unexpected_findings','skin']}


def interpret(observed, expected, checks, uncertain, evidence):
    if type(observed) is not dict or set(observed)!= {'devices','unexpected_findings','skin'}:
        raise ValueError('Invalid visual observations')
    for field, allowed in [('devices',DEVICES),('unexpected_findings',FINDINGS)]:
        values=observed[field]
        if type(values) is not list or any(type(v) is not str or v not in allowed for v in values) or len(set(values))!=len(values):
            raise ValueError('Invalid observed devices or findings')
    if observed['skin'] not in SKIN:
        raise ValueError('Invalid observed skin category')
    devices=set(observed['devices'])
    interfaces=devices & set(RESPIRATORY.values())
    wanted=set() if expected['respiratory_support']=='none' else {RESPIRATORY[expected['respiratory_support']]}
    # Monitoring is permitted even when it is attached and in use.
    checks['respiratory_support']=interfaces==wanted
    checks['no_unrequested_signs']=not (observed['unexpected_findings'] or interfaces-wanted or 'other_active_treatment' in devices)
    replaced={'respiratory_support','no_unrequested_signs'}
    if expected['skin_color']=='mild pallor':
        replaced.add('skin_color')
        checks['skin_color']=observed['skin'] not in {'marked_flushing','cyanosis'}
        if observed['skin'] in {'natural_or_subtle_pallor','not_assessable'} and 'skin_color' not in uncertain:
            uncertain.append('skin_color')
        if not checks['skin_color']:
            uncertain[:]=[v for v in uncertain if v!='skin_color']
    # Retain genuine uncertainty about an obscured interface, but not uncertainty
    # contradicted by an explicitly observed wrong interface.
    uncertain[:]=[v for v in uncertain if checks[v]]
    evidence[:]=[e for e in evidence if e['check'] not in replaced]
    descriptions={
        'respiratory_support': 'Observed respiratory interfaces: '+(', '.join(sorted(interfaces)) or 'none')+'. Required: '+expected['respiratory_support']+'.',
        'no_unrequested_signs': 'Observed incompatible findings/devices: '+', '.join(observed['unexpected_findings']+sorted(interfaces-wanted)+(['other_active_treatment'] if 'other_active_treatment' in devices else []))+'.',
        'skin_color':'Observed skin: '+observed['skin']+'. Required: mild pallor.'}
    for field in replaced:
        if not checks[field]:evidence.append({'check':field,'finding':descriptions[field][:240]})
