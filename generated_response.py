"""Data-driven response envelopes and bounded ventilator interpolation.

Interpolation uses only explicitly authored grid corners and never extrapolates.
Frozen older rules keep their original response envelope.
"""
from copy import deepcopy
from itertools import product


def response_progress(elapsed, onset, duration, recovery=None, immediate=False):
    if immediate:
        return 1.0
    age = elapsed - onset
    if age <= 0:
        return 0.0
    if age <= duration:
        return min(1.0, age / duration)
    if recovery is not None:
        return max(0.0, 1 - (age - duration) / recovery)
    return 1.0


def select_responses(rules, action, matches):
    exact = [r for r in rules if matches(r, action)]
    if exact or action['type'] != 'ventilator_adjustment':
        return exact
    anchors = [r for r in rules if r.get('interpolate_settings') is True and matches({**r, 'settings': {}}, action)]
    fields = ('fio2_percent', 'peep_cmh2o')
    ranges = []
    for field in fields:
        points = sorted({r['settings'][field] for r in anchors})
        target = action.get(field)
        if not points or target is None or target < points[0] or target > points[-1]:
            return []
        low, high = max(v for v in points if v <= target), min(v for v in points if v >= target)
        ranges.append([(low,1.0)] if low == high else [(low,(high-target)/(high-low)),(high,(target-low)/(high-low))])
    selected = []
    for (fi,fw),(peep,pw) in product(*ranges):
        corner = [r for r in anchors if r['settings'] == dict(zip(fields,(fi,peep)))]
        if len(corner) != 1:
            return []
        selected.append({**deepcopy(corner[0]), '_interpolation_weight': fw*pw})
    # A grid is a single surface, not a mixture of different response latencies.
    if len({(r['onset_min'], r['duration_min'], r['max_exposure']) for r in selected}) != 1:
        return []
    return selected


def diagnostic_overrides(state, diagnostic):
    from generated_engine import _COMPARATORS
    g = state.get('generated_state', {})
    from generated_physiology import drivers
    values = {**g.get('values', {}), **drivers(state)}
    values.update(elapsed_min=g.get('elapsed',0), fluid_delivered_ml=state.get('family_state',{}).get('fluid_delivered_ml',0))
    overrides = {}
    for rule in state.get('encounter_spec',{}).get('clinical_case',{}).get('engine',{}).get('state_rules',[]):
        if rule.get('when') and all(c['field'] in values and _COMPARATORS[c['operator']](values[c['field']],c['value']) for c in rule['when']):
            overrides.update(deepcopy((rule.get('diagnostic_updates') or {}).get(diagnostic,{})))
    return overrides
