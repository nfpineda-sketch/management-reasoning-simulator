"""Account for ordered versus delivered quantities on the simulation clock."""


def schedule_delivery(state, action, summary):
    g, f, tr = state['generated_state'], state['family_state'], state['treatments']
    kind = action['type']
    field = 'volume_ml' if kind == 'fluid' else 'units' if kind == 'blood' else next((k for k in ('dose_mg','dose_g','dose') if k in action), None)
    duration = action.get('administration_duration_min')
    if kind == 'fluid':
        duration = duration if duration is not None else action['volume_ml'] / 50
    elif kind == 'blood':
        duration = duration if duration is not None else action['units'] * 30
    if duration is None or field is None:
        return
    if 'deliveries' not in g:
        # Migrate unfinished deliveries from sessions started before this release.
        g['deliveries'] = []
        for prior_kind, pending_field, amount_field, rate in (
            ('fluid', 'pending_fluid_ml', 'volume_ml', 50),
            ('blood', 'pending_blood_units', 'units', 1/30),
        ):
            remaining = f[pending_field] - (action[field] if kind == prior_kind else 0)
            if remaining > 0:
                g['deliveries'].append({'key': [prior_kind, None], 'field': amount_field,
                    'amount': remaining, 'delivered': 0.0, 'start': g['elapsed'],
                    'duration': remaining / rate, 'record_index': None})
    queue = g['deliveries']
    key = (kind, action.get('agent'))
    start = max([g['elapsed']] + [item['start'] + item['duration'] for item in queue if tuple(item['key']) == key])
    record_index = None
    if kind not in {'fluid','blood'}:
        record_index = len(tr['administered_medications']) - 1
        record = tr['administered_medications'][record_index]
        record['ordered_' + field] = action[field]
        record[field] = 0
        record['administration_status'] = 'in_progress'
        summary['label'] = f"{action.get('agent', kind)} {action[field]:g} {action.get('units', 'g' if field == 'dose_g' else 'mg')} {action.get('route', '')} started over {duration:g} min"
    queue.append({'key': list(key), 'field': field, 'amount': action[field], 'delivered': 0.0,
                  'start': start, 'duration': duration, 'record_index': record_index})
    summary['administration_duration_min'] = duration
    summary['delivery_starts_at_min'] = start
    summary['delivery_due_at_min'] = start + duration


def advance_deliveries(state):
    g, f, tr = state['generated_state'], state['family_state'], state['treatments']
    items = g.get('deliveries')
    if items is None:
        return False  # Old frozen runtime states retain their former accounting.
    for item in items:
        delivered = item['amount'] * min(1, max(0, (g['elapsed'] - item['start']) / item['duration']))
        change = delivered - item['delivered']
        item['delivered'] = delivered
        kind = item['key'][0]
        if kind == 'fluid':
            f['fluid_delivered_ml'] += change
            f['pending_fluid_ml'] = max(0, f['pending_fluid_ml'] - change)
        elif kind == 'blood':
            f['blood_delivered_units'] += change
            f['pending_blood_units'] = max(0, f['pending_blood_units'] - change)
        else:
            record = tr['administered_medications'][item['record_index']]
            record[item['field']] = round(delivered, 6)
            record['administration_status'] = 'completed' if delivered >= item['amount'] else 'in_progress'
            if delivered >= item['amount']:
                record['completed_at_min'] = item['start'] + item['duration']
    return True
