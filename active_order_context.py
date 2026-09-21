"""Resolve explicitly requested adjustments against active, recorded treatments.

Never supply a new treatment's starting dose or settings. This helper is pure;
only the execution engine may commit the completed order.
"""
from copy import deepcopy


def complete_active_order(state, raw):
    a = deepcopy(raw)
    kind = a.get('type')
    tr = state.get('treatments', {})
    if kind == 'repeat_order':
        history = tr.get('order_history', [])
        eligible = [item for item in history if item.get('type') in {'fluid', 'blood', 'beta_blocker', 'diltiazem', 'amiodarone', 'diuretic', 'antibiotics', 'procedural_sedation', 'steroid', 'dextrose', 'naloxone', 'aspirin', 'ppi', 'anticoagulation'}]
        if a.get('target'):
            eligible = [item for item in eligible if item['type'] == a['target']]
        if a.get('fluid_type'):
            eligible = [item for item in eligible if item.get('fluid_type') == a['fluid_type']]
        if a.get('agent'):
            eligible = [item for item in eligible if item.get('agent') == a['agent']]
        if not eligible:
            return a, 'No matching administered treatment is recorded. Specify the treatment, dose and route.'
        if not a.get('target') and not a.get('agent') and len({(item['type'], item.get('agent')) for item in eligible}) > 1:
            return a, 'Which previous treatment should be repeated? Specify the drug or fluid.'
        resolved = deepcopy(eligible[-1])
        if a.get('amount') is not None:
            unit, value = a.get('amount_unit'), a['amount']
            if resolved['type'] == 'fluid' and unit in {'ml','cc','l','lt'}:
                resolved['volume_ml'] = value * (1000 if unit in {'l','lt'} else 1)
            elif 'dose_mg' in resolved and unit in {'mg','g','mcg','ug'}:
                resolved['dose_mg'] = value * (1000 if unit == 'g' else .001 if unit in {'mcg','ug'} else 1)
            else:
                return a, 'Specify compatible units for the treatment being repeated.'
        if a.get('route') is not None:
            resolved['route'] = a['route']
        if a.get('administration_duration_min') is not None:
            resolved['administration_duration_min'] = a['administration_duration_min']
        return resolved, None
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
        for field, key in [('ventilator_mode', 'ventilator_mode'), ('fio2_percent', 'ventilator_fio2_percent'),
                           ('peep_cmh2o', 'ventilator_peep_cmh2o'), ('tidal_volume_ml', 'ventilator_tidal_volume_ml'),
                           ('tidal_ml_per_kg', 'ventilator_tidal_ml_per_kg'), ('rate_per_min', 'ventilator_rate_per_min'),
                           ('flow_l_per_min', 'ventilator_flow_l_per_min')]:
            if a.get(field) is None:
                a[field] = tr.get(key)
        return a, None
    if kind == 'infusion_adjustment':
        # The resident named the treatment by its role. Resolve it the way a
        # ventilator adjustment is resolved: against what is actually running,
        # and never by guessing when the answer is ambiguous.
        running = [name for name in ('norepinephrine', 'nitroglycerin', 'dobutamine') if tr.get(name)]
        if not running:
            return a, 'No infusion is running. Name the drug and its starting rate.'
        if len(running) > 1:
            return a, ('More than one infusion is running (' + ', '.join(sorted(running))
                       + '). Name the one to change.')
        a['type'] = kind = running[0]
        rate, units = a.pop('rate_value', None), a.pop('rate_units', None)
        if kind == 'nitroglycerin':
            if units is not None and 'kg' in str(units):
                return a, 'Nitroglycerin is ordered in mcg/min in this encounter.'
            a['rate_mcg_min'] = rate
        else:
            a['rate'] = rate
            a['units'] = str(units).replace(' ', '') if units else tr.get(kind + '_units')
        if a.get('operation') == 'stop':
            return a, None
        if rate is None and a.get('operation') == 'adjust':
            return a, f'Specify the new {kind} rate.'
    if a.get('operation') not in {'adjust', 'continue'}:
        return a, None
    if kind in {'norepinephrine', 'nitroglycerin', 'dobutamine'}:
        if not tr.get(kind):
            return a, f'No active {kind} infusion is recorded. Specify a starting rate and units.'
        if kind in {'norepinephrine', 'dobutamine'}:
            # A change of units without a rate is not a numerical conversion.
            if a.get('rate') is None and a.get('units') not in (None, tr.get(kind + '_units')):
                return a, 'Specify the rate in the new infusion units.'
            for field, key in [('rate', kind + '_rate'), ('units', kind + '_units')]:
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
    tr.setdefault('order_history', []).append(deepcopy(a))
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
    elif kind in {'norepinephrine', 'nitroglycerin', 'dobutamine'}:
        tr[kind] = a.get('operation') != 'stop'
        if kind in {'norepinephrine', 'dobutamine'}:
            tr.update({kind + '_rate': a.get('rate'), kind + '_units': a.get('units')})
        else:
            tr['nitroglycerin_rate_mcg_min'] = a.get('rate_mcg_min')
