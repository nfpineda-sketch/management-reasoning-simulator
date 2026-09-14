"""State-aware cardioversion and case-authored post-conversion recurrence."""
from copy import deepcopy
from ecg12 import RHYTHMS


def rhythm_key(value):
    value = str(value).strip().lower()
    return RHYTHMS.get(value, value)


def select_cardioversion(state, candidates):
    current = rhythm_key(state['observable'].get('rhythm'))
    explicit = [r for r in candidates if r.get('rhythm_before') is not None and rhythm_key(r['rhythm_before']) == current]
    if explicit:
        return explicit if len(explicit) == 1 else []
    legacy = [r for r in candidates if r.get('rhythm_before') is None]
    # An old rule had no pre-rhythm matcher. Do not apply its conversion benefit
    # again while a prior successful conversion remains the current rhythm.
    converted = any(e.get('conversion_effect', e.get('action_type') == 'cardioversion') and e.get('rhythm_after')
                    and rhythm_key(e['rhythm_after']) == current
                    for e in state.get('generated_state',{}).get('events',[]))
    return legacy if len(legacy) == 1 and not converted else []


def advance_recurrence(state):
    from generated_engine import _COMPARATORS
    g = state['generated_state']
    values = dict(g['values'])
    values.update(elapsed_min=g['elapsed'], fluid_delivered_ml=state['family_state']['fluid_delivered_ml'])
    changed = False
    for event in g['events']:
        recurrence = event.get('recurrence')
        if not recurrence or event.get('recurrence_applied'):
            continue
        if rhythm_key(state['observable'].get('rhythm')) != rhythm_key(event['rhythm_after']):
            continue
        age = g['elapsed'] - event['started_at']
        if age < recurrence['after_min'] or not all(_COMPARATORS[c['operator']](values[c['field']], c['value']) for c in recurrence['when']):
            continue
        before = state['observable']['rhythm']
        event.update(delta=deepcopy(recurrence['delta']), rhythm_after=recurrence['rhythm_after'],
                     recurrence_applied=True, state_gain=None)
        state.setdefault('rhythm_history', []).append({'time_min':state['sim_time'], 'kind':'recurrence',
            'rhythm_before':before, 'rhythm_after':recurrence['rhythm_after']})
        changed = True
    return changed
