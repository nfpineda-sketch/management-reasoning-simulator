"""Coupled volume / active drug exposure for immutable generated encounters.

All model parameters come from the case, not the patient's diagnostic label.
Old saved declarations without these fields keep their previous trajectory.
"""
from copy import deepcopy
import math
from clinical_physiology import advance_volume, exposure_effect, mark_terminal_collapse, active_drug_fraction
from generated_dynamics import event_progress, gain_at

VOLUME_FIELDS = frozenset({'fluid_retained_ml', 'fluid_extravascular_ml', 'fluid_output_ml', 'fluid_deficit_ml'})

def finite(x):
    return type(x) in (float, int) and math.isfinite(x)

def validate(engine, initialized):
    p = engine.get('volume_model')
    if p is not None:
        ranges = {'initial_extravascular_ml':(0,10000), 'redistribution_half_life_min':(1,240),
                  'clearance_half_life_min':(1,1440), 'extravascular_fraction':(0,1),
                  'diuresis_extravascular_fraction':(0,1)}
        if not isinstance(p,dict) or set(p) != set(ranges) or any(not finite(p[k]) or not lo <= p[k] <= hi for k,(lo,hi) in ranges.items()):
            raise ValueError('Volume compartments require finite case-specific parameters.')
    rules=engine.get('response_rules',[])
    if not isinstance(rules,list) or any(not isinstance(r,dict) for r in rules):
        raise ValueError('Response rules must be a list of declarations.')
    for r in rules:
        if r.get('volume_basis') is not None:
            if p is None or r.get('action_type') != 'fluid' or r['volume_basis'] not in {'circulating','extravascular'}:
                raise ValueError('Fluid compartment responses need a declared volume model and supported basis.')
        renal = r.get('diuresis_ml_min')
        if renal is not None and (p is None or r.get('action_type') != 'diuretic' or not finite(renal) or not 0 <= renal <= 50 or not r.get('recovery_min')):
            raise ValueError('Diuresis requires a volume model, finite urine response and recovery.')
        curve = r.get('exposure_curve')
        if curve is not None:
            if r.get('action_type') not in {'beta_blocker','diltiazem','amiodarone','diuretic','procedural_sedation'} or not r.get('recovery_min'):
                raise ValueError('Active-load curves require a recovering fixed-dose drug.')
            limits={'saturating_weight':(0,1),'progressive_weight':(0,1),'rate':(.01,10),'power':(1,3),'onset_half_life_min':(.1,120),'elimination_half_life_min':(1,1440)}
            if not isinstance(curve,dict) or set(curve)!=set(limits) or any(not finite(curve[k]) or not lo<=curve[k]<=hi for k,(lo,hi) in limits.items()) or curve['saturating_weight']+curve['progressive_weight'] <= 0:
                raise ValueError('Drug exposure curve has invalid parameters.')
    pools={}
    pool_members=set()
    renal_members=set()
    for r in rules:
        matcher=(r.get("action_type"),r.get("agent"),r.get("route"),r.get("units"))
        if r.get("diuresis_ml_min") is not None:
            if matcher in renal_members:
                raise ValueError("Only one renal output response may match each drug and route.")
            renal_members.add(matcher)
        pool=r.get('exposure_pool')
        if pool is None:
            continue
        if not isinstance(pool,str) or not pool.strip() or len(pool)>160 or not r.get('exposure_curve'):
            raise ValueError('Exposure pools require a named active-load curve.')
        member=(pool,matcher)
        if member in pool_members:
            raise ValueError('An administration may contribute only once to a shared drug pool.')
        pool_members.add(member)
        signature=(r.get('delta'),r.get('max_exposure'),r.get('state_gain'),r.get('diuresis_ml_min'),
                   {k:v for k,v in r['exposure_curve'].items() if k not in {'onset_half_life_min','elimination_half_life_min'}})
        if pool in pools and pools[pool]!=signature:
            raise ValueError('A shared drug pool needs one consistent effect curve, delta and cap.')
        pools[pool]=signature
    terminal=engine.get('terminal_rule')
    if terminal is not None:
        if not isinstance(terminal,dict) or set(terminal)!={'when','sustained_min'} or type(terminal['sustained_min']) is not int or not 1<=terminal['sustained_min']<=60 or not isinstance(terminal['when'],list) or not 1<=len(terminal['when'])<=6:
            raise ValueError('Terminal collapse needs explicit sustained physiological conditions.')
        for c in terminal['when']:
            if not isinstance(c,dict) or set(c)!={'field','operator','value'} or c['field'] not in initialized or c['operator'] not in {'lt','lte','gt','gte'} or not finite(c['value']):
                raise ValueError('Terminal collapse may depend only on current declared physiology.')

def drivers(state):
    return dict(state.get('generated_state',{}).get('compartments',{}))

def initialize(state):
    g=state['generated_state']; p=state['encounter_spec']['clinical_case']['engine'].get('volume_model')
    if p and 'compartments' not in g:
        g['compartments']={k:0.0 for k in VOLUME_FIELDS}
        g['compartments']['fluid_extravascular_ml']=p['initial_extravascular_ml']
        g['compartment_initial']=deepcopy(g['compartments'])
        g['accounted_fluid_ml']=state['family_state']['fluid_delivered_ml']

def active_load(state, rule):
    g=state['generated_state']; curve=rule.get('exposure_curve')
    rules=state['encounter_spec']['clinical_case']['engine']['response_rules']
    members={r['id']:r for r in rules if r['id']==rule['id'] or (rule.get('exposure_pool') and r.get('exposure_pool')==rule['exposure_pool'])}
    def progress(event):
        own=members[event['rule_id']].get('exposure_curve')
        if own:
            return active_drug_fraction(g['elapsed']-event['started_at']-event['onset_min'], own['onset_half_life_min'], own['elimination_half_life_min'])
        return event_progress(event,g['elapsed'])
    load=sum(e['exposure']*progress(e) for e in g['events'] if e['rule_id'] in members)
    return exposure_effect(min(rule['max_exposure'],load),curve)

def advance(state):
    initialize(state)
    g=state['generated_state']; engine=state['encounter_spec']['clinical_case']['engine']; p=engine.get('volume_model')
    if not p:
        return
    # One renal output per authored rule, pooled across repeated administrations.
    diuresis=0.0
    seen=set()
    for rule in engine['response_rules']:
        if rule.get('diuresis_ml_min') is None:
            continue
        pool=rule.get('exposure_pool')
        if pool and pool in seen:
            continue
        seen.add(pool)
        source={**g['values'],**drivers(state),'elapsed_min':g['elapsed'],'fluid_delivered_ml':state['family_state']['fluid_delivered_ml']}
        diuresis += rule['diuresis_ml_min'] * active_load(state,rule) * gain_at(rule.get('state_gain'),source)
    delivered=state['family_state']['fluid_delivered_ml']
    advance_volume(g['compartments'],max(0,delivered-g['accounted_fluid_ml']),p,diuresis)
    g['accounted_fluid_ml']=delivered

def contributions(state, rules, values, apply_gain=True):
    """Apply pooled active loads / compartment changes exactly once per rule."""
    g=state['generated_state']; source={**values,**drivers(state), 'elapsed_min':g['elapsed'],
        'fluid_delivered_ml':state['family_state']['fluid_delivered_ml']}
    changes={key:0.0 for key in values}
    seen=set()
    for r in rules:
        pool=r.get("exposure_pool")
        if pool and pool in seen:
            continue
        seen.add(pool)
        if r.get('volume_basis'):
            c=g['compartments']; initial=g['compartment_initial']
            amount=c['fluid_retained_ml']-c['fluid_deficit_ml'] if r['volume_basis']=='circulating' else c['fluid_extravascular_ml']-initial['fluid_extravascular_ml']
            load=max(-r['max_exposure'], min(r['max_exposure'], amount/r['reference_dose']))
        elif r.get('exposure_curve'):
            load=active_load(state,r)
        else:
            continue
        if apply_gain:
            load *= gain_at(r.get('state_gain'),source)
        for key,delta in r['delta'].items():
            if key in changes:
                changes[key] += delta*load
    return changes

def terminal_tick(state):
    from generated_engine import _COMPARATORS
    g=state['generated_state']; r=state['encounter_spec']['clinical_case']['engine'].get('terminal_rule')
    if not r or state.get('hidden',{}).get('terminal_collapse'):
        return False
    hit=all(_COMPARATORS[c['operator']](g['values'][c['field']],c['value']) for c in r['when'])
    g['low_flow_minutes']=g.get('low_flow_minutes',0)+1 if hit else 0
    if g['low_flow_minutes'] < r['sustained_min']:
        return False
    before=state['observable'].get('rhythm')
    mark_terminal_collapse(state)
    g['terminal_at_min']=state['sim_time']
    state.setdefault('rhythm_history',[]).append({'time_min':state['sim_time'],'kind':'terminal_collapse','rhythm_before':before,'rhythm_after':'PEA'})
    return True


def validate_extremes(engine, initial, bounds):
    """Coupled effects can persist after the old linear response envelope ends."""
    for r in engine.get('response_rules',[]):
        if not (r.get('volume_basis') or r.get('exposure_curve')):
            continue
        peak=exposure_effect(r['max_exposure'],r.get('exposure_curve'))
        low=0
        if r.get('volume_basis')=='circulating' and any(x.get('diuresis_ml_min',0) for x in engine['response_rules']):
            low=-r['max_exposure']
        elif r.get('volume_basis')=='extravascular':
            low=-min(r['max_exposure'],engine['volume_model']['initial_extravascular_ml']/r['reference_dose'])
        for t in (0,engine.get('horizon_min',180)):
            for exposure in (low,peak):
                values={k:v+t*engine.get('untreated_drift_per_min',{}).get(k,0)+r['delta'].get(k,0)*exposure for k,v in initial.items()}
                if any(not bounds[k][0]<=v<=bounds[k][1] for k,v in values.items()) or values['dbp']>=values['sbp']:
                    raise ValueError('A coupled response exceeds supported physiology at its declared exposure limits. Revise its case-specific coefficients or exposure cap.')
