"""Clinical Encounter adapter to the complete main/IA clinical state engine.

Core treatments never use authored vital-sign deltas. One native state advances
through the same transitions, natural disease, pressure/flow, brain and rhythm
functions as the original cases. Extra-domain responses enter the shared engine
as explicit inputs; they do not overwrite its output after a tick.
"""
EXECUTION_VERSION = "0.24.2"

from copy import deepcopy
import math
import random
from clinical_core_defaults import CORE_VERSION, PHENOTYPE_FIELDS, INITIAL_HIDDEN, INITIAL_TREATMENTS
import clinical_physiology as core
import clinical_diagnostics as diagnostic_core

CORE_KINDS=frozenset({'fluid','oxygen','niv','bag_mask','intubation','ventilator_adjustment','norepinephrine','dobutamine','nitroglycerin','beta_blocker','diltiazem','amiodarone','diuretic','cardioversion','airway_preparation','antibiotics'})
CORE_NUMERIC=frozenset({'sbp','dbp','hr','spo2','crt','respiratory_rate'})


def enabled(case):
    return case.get('engine',{}).get('core_profile') is not None


def native(action):
    kind=action['type'];agent=str(action.get('agent','')).lower()
    if kind=='beta_blocker':return agent in {'metoprolol','propranolol'}
    if kind=='diuretic':return agent=='furosemide'
    if kind in {'diltiazem','amiodarone'}:return agent==kind
    return kind in CORE_KINDS or (kind=='procedural_sedation' and agent in {'etomidate','midazolam'} and action.get('route')=='IV')


def validate_profile(profile):
    if not isinstance(profile,dict) or set(profile)!={'version','infection_active','initial_hidden'} or profile['version']!=CORE_VERSION or type(profile['infection_active']) is not bool:
        raise ValueError('The generated case requires a main/IA core profile.')
    h=profile['initial_hidden']
    if not isinstance(h,dict) or set(h)!=set(PHENOTYPE_FIELDS) or any(type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=1 for v in h.values()):
        raise ValueError('Every initial core physiology driver must be explicitly authored between zero and one.')


def call(s,name,*args,**kwargs):
    def rng():
        counter=s.get('rng_counter',0);s['rng_counter']=counter+1
        return random.Random(s.get('seed',17)+counter*997)
    return core.invoke(name,(s,*args),kwargs,rng,lambda t:f'{int(t)//60:02d}:{int(t)%60:02d}')


def core_spo2_target(s):
    """The core's SpO2 target for this state, mirrored from clinical_physiology."""
    h=s['hidden']
    burden=core.clamp(max(0.62*core.pulmonary_clinical_signal(s)+0.38*h['pulmonary_congestion']+0.48*h['respiratory_failure_severity'],
                          0.82*h.get('primary_respiratory_burden',0.0),0.0))
    return max(72.0,min(100.0,94.0-16.0*burden+7.0*core.oxygen_support_fraction(s)))


def initialize(state):
    if state.get('coupled_state'):
        return
    from family_engine import _initialize
    _initialize(state)
    case=state['encounter_spec']['clinical_case'];p=case['engine']['core_profile'];validate_profile(p)
    o=deepcopy(state['observable'])
    from generated_rhythm import rhythm_key
    key=rhythm_key(o.get('rhythm'))
    if key=='af':o['rhythm']='AF'
    elif key=='sinus':o['rhythm']='Sinus rhythm'
    h=deepcopy(INITIAL_HIDDEN);h.update(p['initial_hidden'])
    # Stores are initialized from explicit patient drivers, never PS001 observations.
    h.update(effective_map=(o['sbp']+2*o['dbp'])/3,preload_state=h['effective_volume'],
             peripheral_flow=h['tissue_perfusion'],preload_responsiveness=core.fluid_responsiveness(h['effective_volume']))
    s={'case_id':state.get('case_id','generated'),'engine_profile':CORE_VERSION,'seed':state.get('seed',17),
       'patient_weight_kg':case.get('patient',{}).get('weight_kg',70), 'sim_time':state.get('sim_time',0),'rng_counter':0,'hidden':h,'observable':o,
       'treatments':deepcopy(INITIAL_TREATMENTS),'diagnostics':{},'treatment_timeline':{},
       'physiology_parameters':{'infection_active':p['infection_active']},'baseline_respiratory_rate':o['respiratory_rate']}
    state['coupled_state']=s
    values={k:float(v) for k,v in case['observable'].items() if type(v) in (int,float)}
    values.update(case['engine'].get('initial_labs',{}))
    state['generated_state']={'version':2,'elapsed':state.get('sim_time',0),'baseline_values':deepcopy(values),
       'values':values,'events':[],'exposure':{},'examination':deepcopy(case.get('examination',{})),
       'pending_diagnostics':[],'native_deliveries':[],'engine_version':CORE_VERSION}
    # Reference values preserve authored baseline laboratory etiologies. Subsequent
    # changes come from the same perfusion/respiratory calculations as main/IA.
    # The core has its own room-air SpO2 equilibrium (at most 94%); an authored 96%
    # fell to it within minutes, as if fluid had worsened oxygenation. Anchor it to
    # the authored arrival value, as the gases are; changes still come from the core.
    state['generated_state']['spo2_anchor']=float(case['observable']['spo2'])-core_spo2_target(s)
    state['generated_state']['arrival_tissue_perfusion']=float(h['tissue_perfusion'])
    if 'lactate_mmol_l' in values:
        # Lactate starts from the authored arrival value, not the core's first-minute reading.
        state['generated_state']['lactate_shown']=values['lactate_mmol_l']
        state['generated_state']['lactate_shown_at']=state['generated_state']['elapsed']
    state['generated_state']['lab_reference']=diagnostic_core.vbg_transition(deepcopy(s),0)['result']
    state['generated_state']['abg_reference']=diagnostic_core.abg_transition(deepcopy(s),0)['result']
    state['hidden']=deepcopy(h)
    state['observable']=deepcopy(o)


def transition(s,a):
    k=a['type'];op=a.get('operation','start')
    if k=='fluid':return call(s,'fluid_transition',a['volume_ml'],a.get('fluid_type','Crystalloid'))
    if k=='beta_blocker':return call(s,'beta_blocker_transition',a['agent'].lower(),a['dose_mg'],a['route'])
    if k in {'diltiazem','amiodarone'}:return call(s,k+'_transition',a['dose_mg'],a['route'])
    if k=='diuretic':return call(s,'furosemide_transition',a['dose_mg'],a['route'])
    if k=='procedural_sedation':return call(s,'procedural_sedation_transition',[{'agent':a['agent'],'dose':a['dose_mg'],'units':'mg','route':a['route']}])
    if k=='cardioversion':return call(s,'cardioversion_transition',a['energy_j'])
    if k=='norepinephrine':return call(s,'norepinephrine_transition',a.get('rate',0),a.get('units','mcg/kg/min'),op)
    if k=='dobutamine':return call(s,'dobutamine_transition',a.get('rate',0),a.get('units','mcg/kg/min'),op)
    if k=='nitroglycerin':return call(s,'nitroglycerin_transition',a.get('rate_mcg_min',0),op)
    if k=='oxygen':
        if s['treatments'].get('niv'):
            call(s,'niv_transition',s['treatments'].get('niv_mode') or 'BiPAP',0,'stop')
        if a['device']=='Room air':
            s['treatments'].update(oxygen=False,oxygen_device=None,oxygen_flow_lpm=0)
            call(s,'_record_treatment_timing','oxygen','stop')
            return {'duration_min':1}
        return call(s,'oxygen_transition','Simple face mask' if a['device']=='Simple mask' else a['device'],a['flow_lpm'])
    if k=='niv':return call(s,'niv_transition',a.get('mode','BiPAP'),a.get('epap_cmh2o',0),op,a.get('ipap_cmh2o'),a.get('epap_cmh2o'),a.get('fio2_percent'))
    if k=='intubation':return call(s,'intubation_transition',a['ventilator_mode'],a['fio2_percent'],a['peep_cmh2o'])
    if k=='ventilator_adjustment':
        if a.get('operation')=='continue':return call(s,'ventilator_continuation_transition')
        return call(s,'ventilator_adjustment_transition',a.get('ventilator_mode'),a.get('fio2_percent'),a.get('peep_cmh2o'))
    if k=='airway_preparation':return call(s,'airway_preparation_transition')
    if k=='antibiotics':
        s['treatments']['antibiotics']=True
        return {'duration_min':5}
    if k=='bag_mask':
        s['treatments'].update(bag_mask=True,niv=False,oxygen=False)
        return {'duration_min':1}
    raise ValueError('Unsupported native intervention.')


def hold_mental_while_perfusion_falls(state,before):
    """Keep the previous mental status if the core raised it while perfusion is falling."""
    g=state['generated_state'];s=state['coupled_state']
    if 'arrival_tissue_perfusion' not in g:
        return  # a state saved before this adjustment behaves as before
    history=g.setdefault('recent_tissue_perfusion',[])
    history.append(s['hidden'].get('tissue_perfusion',0.0))
    del history[:-(MENTAL_TREND_WINDOW_MIN+1)]
    now=s['observable'].get('mental_status')
    if before in MENTAL_LEVELS and now in MENTAL_LEVELS and MENTAL_LEVELS.index(now)<MENTAL_LEVELS.index(before):
        if len(history)>MENTAL_TREND_WINDOW_MIN and history[-1]<history[0]-MENTAL_TREND_FALL:
            s['observable']['mental_status']=before


def hr_relief(state):
    """Lower the heart rate as tissue perfusion recovers beyond its arrival value."""
    g=state['generated_state']
    if 'arrival_tissue_perfusion' not in g:
        return 0.0  # a state saved before this adjustment behaves as before
    gained=state['coupled_state']['hidden'].get('tissue_perfusion',0.0)-g['arrival_tissue_perfusion']
    return -min(HR_RELIEF_MAX,HR_RELIEF_PER_PERFUSION*max(0.0,gained))


def prepare_inputs(state):
    """Non-core disease responses enter the core before its pressure/flow update."""
    from generated_dynamics import event_progress,gain_at
    case=state['encounter_spec']['clinical_case'];g=state['generated_state'];s=state['coupled_state']
    delta={k:g['elapsed']*v for k,v in case['engine'].get('untreated_drift_per_min',{}).items()}
    # Untreated cardiorespiratory evolution belongs exclusively to the shared core.
    for k in CORE_NUMERIC:delta.pop(k,None)
    for event in g['events']:
        progress=event['exposure']*event_progress(event,g['elapsed'])*gain_at(event.get('state_gain'),{**g['values'],'elapsed_min':g['elapsed'],'fluid_delivered_ml':state['family_state']['fluid_delivered_ml']})
        for k,v in event['delta'].items():delta[k]=delta.get(k,0)+progress*v
    if g.get('nitrate_drop'):
        from nitrate_hazard import DBP_FRACTION
        delta['sbp']=delta.get('sbp',0)-g['nitrate_drop'];delta['dbp']=delta.get('dbp',0)-DBP_FRACTION*g['nitrate_drop']
    s['physiology_inputs']={'map':(delta.get('sbp',0)+2*delta.get('dbp',0))/3,
       'pulse_pressure':delta.get('sbp',0)-delta.get('dbp',0),'hr':delta.get('hr',0)+hr_relief(state),
       'spo2':delta.get('spo2',0)+g.get('spo2_anchor',0),'crt':delta.get('crt',0),'respiratory_rate':delta.get('respiratory_rate',0)}
    sedating=[e for e in g['events'] if e.get('mental_status_during') and e['exposure']*event_progress(e,g['elapsed'])>=e.get('mental_status_threshold',1)]
    s['physiology_inputs']['sedation_effect']=.5 if sedating else 0
    return delta


def examination_updates(rule, observed):
    """Do not present a rule's proposed recovery as an observed native recovery."""
    updates=deepcopy(rule.get('examination',{}))
    dependencies={'mental_status':('Neurological','General appearance'),
                  'work_of_breathing':('Respiratory','General appearance'),
                  'rhythm':('Cardiac',), 'pulse_present':('Cardiac','Peripheral perfusion'),
                  'extremities':('Peripheral perfusion',), 'peripheral_perfusion':('Peripheral perfusion',)}
    for field,areas in dependencies.items():
        proposed=rule.get('set',{}).get(field)
        if proposed is not None and str(proposed).lower()!=str(observed.get(field)).lower():
            for area in areas:updates.pop(area,None)
    return updates


def sync_mottling(observable):
    """The mottling flag must agree with the extremities the core reports.

    ``visual.mottling`` drives the patient illustration, so a patient the engine
    describes as "Mottled/Cold" was being drawn without mottling. The flag is
    derived here rather than in the shared core, which stays identical to main.
    Mottling already recorded by a narrative rule is never erased.
    """
    extremities = str(observable.get('extremities') or '')
    if 'mottled' in extremities.lower():
        observable.setdefault('visual', {})['mottling'] = True
    return observable


def project(state,delta=None):
    from generated_engine import OBSERVED_FIELDS,BOUNDS,_COMPARATORS
    g=state['generated_state'];s=state['coupled_state'];case=state['encounter_spec']['clinical_case']
    previous_visual=deepcopy(state['observable'].get('visual',{}))
    state['hidden']=deepcopy(s['hidden']);state['observable']=deepcopy(s['observable'])
    state['treatment_timeline']=deepcopy(s['treatment_timeline'])
    o=state['observable'];o['map']=round((o['sbp']+2*o['dbp'])/3)
    if s['hidden'].get('terminal_collapse'):
        # Preserve the last displayed findings when terminal physiology bypasses
        # narrative rules; copying the native baseline must not imply recovery.
        o.setdefault('visual',{}).update(previous_visual)
        o.setdefault('electrical_rhythm',s.get('pre_arrest_rhythm','sinus'))
        sync_mottling(o)
        return
    delta=delta or {}
    for k in OBSERVED_FIELDS:
        if k not in CORE_NUMERIC:
            o[k]=g['baseline_values'][k]+delta.get(k,0)
        g['values'][k]=o[k]
    labs=diagnostic_core.vbg_transition(deepcopy(s),0)['result'];ref=g['lab_reference']
    for k,baseline in case['engine'].get('initial_labs',{}).items():
        change=labs[k]-ref[k] if k in {'lactate_mmol_l','bicarbonate_mmol_l','pco2_mm_hg'} else diagnostic_core.abg_transition(deepcopy(s),0)['result']['pao2_mm_hg']-g['abg_reference']['pao2_mm_hg'] if k=='pao2_mm_hg' else 0
        g['values'][k]=baseline+change+delta.get(k,0)
    # A falling lactate clears over tens of minutes, not in one reassessment.
    lactate=g['values'].get('lactate_mmol_l')
    if lactate is not None and 'arrival_tissue_perfusion' in g:
        shown,at=g.get('lactate_shown'),g.get('lactate_shown_at',g['elapsed'])
        elapsed=max(0,g['elapsed']-at)
        perfusion=s['hidden'].get('tissue_perfusion',1.0)
        if shown is not None and perfusion<LACTATE_PRODUCTION_THRESHOLD:
            # Hypoperfused tissue keeps producing lactate, whatever the core's value.
            lactate=max(lactate,shown+LACTATE_PRODUCTION_RATE*(LACTATE_PRODUCTION_THRESHOLD-perfusion)*elapsed)
        elif shown is not None and lactate<shown:
            lactate=shown+(lactate-shown)*(1-math.exp(-elapsed/LACTATE_CLEARANCE_TAU_MIN))
        g['values']['lactate_mmol_l']=lactate
        g['lactate_shown'],g['lactate_shown_at']=lactate,g['elapsed']
    # Gas changes use the inherited physiology, anchored to the authored initial sample.
    for k,v in g['values'].items():
        if k in BOUNDS and (not math.isfinite(v) or not BOUNDS[k][0]<=v<=BOUNDS[k][1]):
            raise ValueError('The physiological evolution exceeds this case\'s validated laboratory/observation range.')
    g['examination']=deepcopy(case.get('examination',{}))
    drivers={**g['values'],'elapsed_min':g['elapsed'],'fluid_delivered_ml':state['family_state']['fluid_delivered_ml']}
    # Narrative state rules may describe current physiology, never reset its pulse,
    # rhythm, perfusion or the brain's delayed recovery to an earlier category.
    for r in case['engine'].get('state_rules',[]):
        if all(c['field'] in drivers and _COMPARATORS[c['operator']](drivers[c['field']],c['value']) for c in r['when']):
            changes=r.get('set',{})
            if changes.get('visual'):o.setdefault('visual',{}).update(changes['visual'])
            g['examination'].update(examination_updates(r,o))
    if state['family_state']['invasive']:o['respiratory_support']='Invasive ventilation'
    elif state['family_state']['niv']:o['respiratory_support']='NIV'
    elif state['family_state']['bag_mask']:o['respiratory_support']='Bag-mask ventilation'
    else:o['respiratory_support']=state['family_state']['oxygen_device']
    sync_mottling(o)


def tick(state):
    from generated_delivery import advance_deliveries
    s=state['coupled_state'];g=state['generated_state'];f=state['family_state'];g['elapsed']+=1
    before=[x.get('delivered',0) for x in g.get('deliveries',[])]
    fluid_before=f['fluid_delivered_ml']
    advance_deliveries(state)
    for item,prior in zip(g.get('deliveries',[]),before):
        change=item['delivered']-prior
        if change<=0:continue
        action=item.get('core_action')
        if action:
            part={**action,item['field']:change}
            if action['type']=='fluid':s['_fluid_delivery']={'before_ml':prior,'total_ml':item['amount']}
            try:transition(s,part)
            finally:s.pop('_fluid_delivery',None)
    # A declared preload-dependent condition turns nitroglycerin into an abrupt fall in pressure.
    import nitrate_hazard
    nitrate_hazard.step(state,f['fluid_delivered_ml']-fluid_before)
    delta=prepare_inputs(state)
    before_rhythm=s['observable']['rhythm']
    before_mental=s['observable'].get('mental_status')
    call(s,'apply_natural_disease',1)
    hold_mental_while_perfusion_falls(state,before_mental)
    s['sim_time']+=1;state['sim_time']=s['sim_time'];f['elapsed']=g['elapsed']
    if s['observable'].get('rhythm')!=before_rhythm:
        state.setdefault('rhythm_history',[]).append({'time_min':state['sim_time'],'kind':'physiological_evolution','rhythm_before':before_rhythm,'rhythm_after':s['observable']['rhythm']})
    if s['hidden'].get('terminal_collapse'):s['pre_arrest_rhythm']=before_rhythm
    state['treatments']['total_crystalloid_ml']=state['treatments']['cumulative_crystalloid_ml']=f['fluid_delivered_ml']
    project(state,delta)


DYNAMIC_POCUS=('lv','ivc','lungs')

# Adapter adjustments for generated cases only (faculty review pending). The shared
# core keeps sinus HR near 88 + 25 x sympathetic drive, so a patient whose
# perfusion recovered stayed at ~106/min; and its lactate cleared 3.2 -> 0.5 mmol/L
# in 20 minutes. Bank cases and PS001 do not pass through this adapter.
HR_RELIEF_PER_PERFUSION=30.0   # bpm lower per unit of tissue perfusion gained since arrival
HR_RELIEF_MAX=20.0
LACTATE_CLEARANCE_TAU_MIN=45.0 # a falling lactate approaches the core value with this time constant
# The core's lactate fell even as a patient deteriorated (SBP 72, lactate 3.2 -> 2.6)
# because its low-flow burden clears regardless of perfusion. Below this tissue
# perfusion, lactate is produced: +rate x (threshold - perfusion) mmol/L per minute.
LACTATE_PRODUCTION_THRESHOLD=0.50
LACTATE_PRODUCTION_RATE=0.10
# The core lets mental status climb once 28 minutes of cerebral oxygen delivery have
# accrued, even if perfusion is falling at that moment; a patient woke to "Alert"
# at 86/51 on the way down. No improvement while perfusion fell over this window.
MENTAL_TREND_WINDOW_MIN=5
MENTAL_TREND_FALL=0.01
MENTAL_LEVELS=('Alert','Drowsy','Obtunded','Unresponsive')


def arrival_core_pocus(case):
    """The core's own LV/IVC/lung findings for this case at arrival.

    The author writes the arrival POCUS in words and the core derives its findings
    from the authored drivers; the two can disagree (a sildenafil case authored
    "normal contractility" with drivers the core reads as a weak LV). Comparing
    later scans with the core's arrival reading reports only real change.
    """
    h=deepcopy(INITIAL_HIDDEN);h.update(case['engine']['core_profile']['initial_hidden'])
    h.update(preload_state=h['effective_volume'])
    s={'case_id':'generated','engine_profile':CORE_VERSION,'hidden':h,'treatments':deepcopy(INITIAL_TREATMENTS)}
    result=diagnostic_core.pocus_transition(s,0)['result']
    return {key:result[key] for key in DYNAMIC_POCUS}


def collect(state,study,duration):
    from generated_engine import _collect_diagnostic
    result=_collect_diagnostic(state,study,duration)
    if study=='pocus':
        case=state['encounter_spec']['clinical_case']
        dynamic=diagnostic_core.pocus_transition(deepcopy(state['coupled_state']),0)['result']
        reference=arrival_core_pocus(case)
        # Preserve authored findings, focal RV/pericardial pathology included, until the
        # physiology itself changes; then report the current finding alone. One scan
        # reports one set of findings: the earlier scans stay in the diagnostic history.
        for key in DYNAMIC_POCUS:
            authored=case['investigations'].get('pocus',{}).get('result',{}).get(key)
            unchanged=dynamic[key]==reference[key] or (key=='lv' and _lv_dip_during_recovery(state,case,dynamic[key],reference[key]))
            result['result'][key]=authored if authored and unchanged else dynamic[key]
    return result


_LV_ORDER=('Preserved to hyperdynamic contraction','Mildly reduced global contraction','Moderately to severely reduced global contraction')


def _lv_dip_during_recovery(state,case,current,arrival):
    """A one-category LV fall while perfusion is better than at arrival is not reported.

    In the sildenafil case the core lowered contractile reserve during the first
    low-flow minutes (0.7 x 1.0 -> 0.7 x 0.8), so the LV crossed from preserved to
    mildly reduced at the moment pressure, capillary refill and lactate recovered.
    A real deterioration -- two categories, or while perfusion is no better -- is shown.
    """
    if current not in _LV_ORDER or arrival not in _LV_ORDER:
        return False
    if _LV_ORDER.index(current)-_LV_ORDER.index(arrival)!=1:
        return False
    arrival_perfusion=case['engine']['core_profile']['initial_hidden'].get('tissue_perfusion',0.0)
    return state['coupled_state']['hidden'].get('tissue_perfusion',0.0)>arrival_perfusion


def execute(state,parsed):
    from family_engine import _validate,_order,_failure,_release_diagnostic
    from generated_engine import validate_declarative_case,_matches,_record_effect,_ADMIN
    from generated_response import select_responses
    from generated_delivery import schedule_delivery
    try:
        case=state['encounter_spec']['clinical_case'];validate_declarative_case(case)
        if state.get('hidden',{}).get('terminal_collapse'):return _failure('The patient has no pulse. This build does not execute resuscitation actions.')
        actions,error=_validate(state,parsed)
        if error:return _failure(error)
        selected=[]
        for a in actions:
            rules=[] if native(a) else select_responses(case['engine']['response_rules'],a,_matches)
            if not native(a) and a['type'] not in _ADMIN|{'reassessment','diagnostic'} and not rules:
                return _failure('Order understood, but this treatment is outside the main/IA core and has no declared disease-specific response. No orders were executed.')
            selected.append(rules)
        candidate=deepcopy(state);initialize(candidate);g=candidate['generated_state'];s=candidate['coupled_state'];summaries=[];reassess=None
        pending=g['pending_diagnostics']
        for a,rules in zip(actions,selected):
            k=a['type']
            if k=='reassessment':reassess=a['delay_min'];continue
            if k=='diagnostic':
                delay=1 if a['diagnostic']=='ecg' else case['investigations'][a['diagnostic']].get('duration_min',0)
                pending.append({'available_at':candidate['sim_time']+delay,'summary':collect(candidate,a['diagnostic'],delay)});continue
            summary=_order(candidate,a)
            if k=='fluid' and a.get('operation')=='stop':summaries.append(summary);continue
            schedule_delivery(candidate,a,summary)
            queued=k=='fluid' or (native(a) and a.get('administration_duration_min') is not None)
            if queued:
                g['deliveries'][-1]['core_action']=deepcopy(a)
            elif native(a):
                before=s['observable']['rhythm']
                if k=='cardioversion' and before!='AF':
                    from generated_rhythm import select_cardioversion,rhythm_key
                    candidates=select_responses(case['engine']['response_rules'],a,_matches)
                    outcome=select_cardioversion(s,candidates)
                    if outcome:
                        target=outcome[0]['rhythm_after']
                        s['cardioversion_target']='Sinus rhythm' if rhythm_key(target)=='sinus' else 'AF' if rhythm_key(target)=='af' else target
                try:native_result=transition(s,a)
                finally:s.pop('cardioversion_target',None)
                summary.update(native_result)
                if k in {'oxygen','niv','bag_mask','intubation','ventilator_adjustment'}:
                    s['treatments']['bag_mask']=candidate['family_state']['bag_mask']
                    s['treatments']['niv']=candidate['family_state']['niv']
                    s['treatments']['oxygen']=candidate['treatments'].get('oxygen',False)
                if k=='cardioversion':
                    summary.update(rhythm_before=before,rhythm_after=s['observable']['rhythm'])
                    candidate.setdefault('rhythm_history',[]).append({'time_min':candidate['sim_time'],'kind':'cardioversion','energy_j':a['energy_j'],'rhythm_before':before,'rhythm_after':s['observable']['rhythm']})
                # Reflect immediate native actions without calling physiology twice at time zero.
                project(candidate)
            else:_record_effect(candidate,a,rules,summary)
            summaries.append(summary)
        elapsed=reassess if reassess is not None else 0
        if g['elapsed']+elapsed>case['engine'].get('horizon_min',180):return _failure('Choose a reassessment within this case\'s supported time horizon.')
        def release():
            for item in list(pending):
                if item['available_at']<=candidate['sim_time']:
                    summaries.append(_release_diagnostic(candidate,item['summary'],item['available_at']));pending.remove(item)
        release()
        for minute in range(elapsed):
            tick(candidate);release()
            if s['hidden'].get('terminal_collapse'):
                elapsed=minute+1;break
        candidate['pending_investigations']=[{'diagnostic_type':x['summary']['diagnostic_type'],'available_at_min':x['available_at'],'collected_at_min':x['summary']['result'].get('time_min',0)} for x in pending]
        state.clear();state.update(candidate)
        return {'executed':True,'clarification':None,'action_summaries':summaries,'reassess_delay':reassess,'elapsed_min':elapsed}
    except (ValueError,TypeError,KeyError) as error:
        return _failure('The main/IA encounter could not execute this submission: '+str(error)+'. No orders were executed.')


def preview(case, seed=17):
    """Provide real native-engine timepoints to the independent case reviewer."""
    s={'engine_family':'generated','seed':seed,'sim_time':0,'observable':deepcopy(case['observable']),
       'encounter_spec':{'clinical_case':case},'treatments':{},'hidden':{},'diagnostics':{}}
    initialize(s)
    points=[{'time_min':0,'observable':deepcopy(s['observable'])}]
    horizon = case['engine'].get('horizon_min', 15)
    for minute in range(1, horizon + 1):
        tick(s)
        if minute in {1,5,15,30,60,120,horizon} or s['hidden'].get('terminal_collapse'):
            points.append({'time_min':minute,'observable':deepcopy(s['observable']),
                'flow':s['hidden'].get('cardiac_output_index'),'oxygen_delivery':s['hidden'].get('oxygen_delivery')})
        if s['hidden'].get('terminal_collapse'):break
    return points
