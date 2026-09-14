"""Resolve explicitly requested adjustments against active, recorded treatments.

Never supply a new treatment's starting dose or settings. This helper is pure;
only the execution engine may commit the completed order.
"""
from copy import deepcopy


def complete_active_order(state, raw):
    a = deepcopy(raw)
    kind = a.get('type')
    tr = state.get('treatments', {})
    if kind == 'respiratory_adjustment':
        if tr.get('invasive_ventilation'):
            a['type'] = kind = 'ventilator_adjustment'
        elif tr.get('niv'):
            a['type'] = kind = 'niv'
        else:
            return a, 'No active ventilator or NIV settings are recorded. Specify the support to start.'
    if kind == 'ventilator_adjustment':
        if not tr.get('invasive_ventilation'):
            return a, 'The patient is not receiving invasive ventilation.'
        if a.get('operation') == 'stop':
            return a, 'Specify an airway transition; stopping a ventilator is not an extubation order.'
        for field, key in [('ventilator_mode', 'ventilator_mode'), ('fio2_percent', 'ventilator_fio2_percent'), ('peep_cmh2o', 'ventilator_peep_cmh2o')]:
            if a.get(field) is None:
                a[field] = tr.get(key)
        return a, None
    if a.get('operation') not in {'adjust', 'continue'}:
        return a, None
    if kind in {'norepinephrine', 'nitroglycerin'}:
        if not tr.get(kind):
            return a, f'No active {kind} infusion is recorded. Specify a starting rate and units.'
        if kind == 'norepinephrine':
            # A change of units without a rate is not a numerical conversion.
            if a.get('rate') is None and a.get('units') not in (None, tr.get('norepinephrine_units')):
                return a, 'Specify the rate in the new infusion units.'
            for field, key in [('rate', 'norepinephrine_rate'), ('units', 'norepinephrine_units')]:
                if a.get(field) is None:
                    a[field] = tr.get(key)
        elif a.get('rate_mcg_min') is None:
            a['rate_mcg_min'] = tr.get('nitroglycerin_rate_mcg_min')
    elif kind == 'oxygen':
        if not tr.get('oxygen'):
            return a, 'No active conventional oxygen is recorded. Specify the starting device and flow.'
        if a.get('device') and a['device'].lower() != str(tr.get('oxygen_device')).lower() and a.get('flow_lpm') is None:
            return a, 'Specify the flow for the new oxygen device.'
        if a.get('device') is None:
            a['device'] = tr.get('oxygen_device')
        if a.get('flow_lpm') is None:
            a['flow_lpm'] = tr.get('oxygen_flow_lpm')
    elif kind == 'niv':
        if not tr.get('niv'):
            return a, 'No active NIV is recorded. Specify the starting mode, pressures and FiO2.'
        for field, key in [('mode', 'niv_mode'), ('ipap_cmh2o', 'niv_ipap_cmh2o'), ('epap_cmh2o', 'niv_epap_cmh2o'), ('fio2_percent', 'niv_fio2_percent')]:
            if a.get(field) is None:
                a[field] = tr.get(key)
    return a, None


def remember_validated_support(state, a):
    """Advance only validation context within a compound order, not physiology."""
    tr = state.setdefault('treatments', {})
    kind = a['type']
    if kind == 'oxygen':
        tr.update(oxygen=a.get('device') != 'Room air', oxygen_device=a.get('device'), oxygen_flow_lpm=a.get('flow_lpm'))
        tr['niv'] = False
    elif kind == 'niv':
        tr.update(niv=a.get('operation') != 'stop', oxygen=False)
        for field, key in [('mode', 'niv_mode'), ('ipap_cmh2o', 'niv_ipap_cmh2o'), ('epap_cmh2o', 'niv_epap_cmh2o'), ('fio2_percent', 'niv_fio2_percent')]:
            tr[key] = a.get(field)
    elif kind in {'intubation', 'ventilator_adjustment'}:
        tr.update(invasive_ventilation=True, oxygen=False, niv=False)
        state.setdefault('family_state', {})['invasive'] = True
        tr.update(ventilator_mode=a.get('ventilator_mode'), ventilator_fio2_percent=a.get('fio2_percent'), ventilator_peep_cmh2o=a.get('peep_cmh2o'))
    elif kind in {'norepinephrine', 'nitroglycerin'}:
        tr[kind] = a.get('operation') != 'stop'
        if kind == 'norepinephrine':
            tr.update(norepinephrine_rate=a.get('rate'), norepinephrine_units=a.get('units'))
        else:
            tr['nitroglycerin_rate_mcg_min'] = a.get('rate_mcg_min')
