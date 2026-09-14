"""Complete missing dose/route fields without losing an unexecuted order bundle."""
from copy import deepcopy
import re
from family_parser import _normalize, _route, _amount, _medication, _COMMAND, _NEGATION, _CONDITIONAL, parse_family_actions

_FIELDS = {'blood': ('units',), 'anticoagulation': ('dose','units','route'), 'fluid': ('volume_ml', 'fluid_type'), 'cardioversion': ('energy_j',),
           'norepinephrine': ('rate', 'units'), 'nitroglycerin': ('rate_mcg_min',),
           'dobutamine': ('rate','units'), 'niv': ('mode','epap_cmh2o','fio2_percent'),
           'intubation': ('ventilator_mode','fio2_percent','peep_cmh2o'), 'oxygen': ('device', 'flow_lpm')}


def missing_fields(a):
    fields = _FIELDS.get(a.get('type'))
    if fields is None and 'dose_mg' in a:
        fields = ('dose_mg', 'route')
    elif fields is None and 'dose_g' in a:
        fields = ('dose_g', 'route')
    if a.get('type') == 'niv' and str(a.get('mode','')).lower() == 'bipap':
        fields = (*fields, 'ipap_cmh2o')
    return [k for k in (fields or ()) if a.get(k) is None]


def hold_incomplete_bundle(parsed):
    parsed = deepcopy(parsed)
    parsed['actions'] = [deepcopy(a.get('pending_action', a)) for a in parsed.get('actions', [])]
    indices = [i for i,a in enumerate(parsed.get('actions', [])) if missing_fields(a)]
    if not indices or any(a.get('type') == 'clarification' for a in parsed.get('actions', [])):
        return None
    return {'type': 'family_bundle', 'parsed': deepcopy(parsed), 'index': indices[0]}


def complete_bundle(pending, text):
    body = _normalize(text).strip()
    if _COMMAND.match(body) or _NEGATION.match(body) or _CONDITIONAL.search(body):
        return None  # A new directive is not a dose clarification.
    parsed = deepcopy(pending['parsed'])
    a = parsed['actions'][pending['index']]
    missing = missing_fields(a)
    supplied = {}
    if a['type'] == 'fluid':
        # Preserve the earlier branch's volume/abbreviation handling, but require
        # an explicit unit when no fluid name is supplied in the reply.
        value, units = _amount(body, r'ml|cc|l|lt|liters?|litros?')
        if value is not None:
            supplied['volume_ml'] = value * (1000 if units not in {'ml','cc'} else 1)
        fluid = parse_family_actions('give ' + body)['actions']
        if len(fluid) == 1 and fluid[0].get('type') == 'fluid':
            supplied.update({k:v for k,v in fluid[0].items() if v is not None})
    elif a['type'] == 'blood':
        value, _ = _amount(body, r'units?|unidades?|u')
        supplied['units'] = value
    elif a['type'] == 'anticoagulation':
        value, unit = _amount(body, r'mg|units?|unidades?|ui|u|iu')
        supplied.update(dose=value, units=('mg' if unit == 'mg' else 'units') if unit else None, route=_route(body))
    elif a['type'] == 'cardioversion':
        value, _ = _amount(body, r'j|joules?|julios?')
        if value is not None:
            supplied['energy_j'] = value
    elif 'dose_mg' in a or 'dose_g' in a:
        supplied = _medication(body, a['type'], a.get('agent', a['type']))
        if supplied.get('type') == 'clarification':
            return {'clarification': supplied['message']}
    else:
        prefix = {'oxygen': 'start oxygen ', 'norepinephrine': 'start norepinephrine ', 'nitroglycerin': 'start nitroglycerin ', 'dobutamine': 'start dobutamine ', 'niv':'start NIV ', 'intubation':'intubate '}.get(a['type'])
        if not prefix:
            return None
        unit_only = re.fullmatch(r'(?:mcg|ug)\s*/\s*(?:kg\s*/\s*)?min', body)
        candidate_text = prefix + ('1 ' if unit_only else '') + body
        candidates = parse_family_actions(candidate_text)['actions']
        if len(candidates) != 1:
            return None
        supplied = candidates[0].get('pending_action', candidates[0])
        if unit_only:
            supplied.pop('rate', None)
            supplied.pop('rate_mcg_min', None)
        if supplied.get('type') == 'clarification':
            return {'clarification': supplied['message']}
    changed = False
    for k in missing:
        if supplied.get(k) is not None:
            a[k] = supplied[k]
            changed = True
    if not changed:
        return None
    parsed.pop('clarification', None)
    parsed['raw_text'] = str(parsed.get('raw_text', '')) + '\nClarification: ' + str(text)
    parsed['resolved_from_clarification'] = True
    return {'parsed': parsed}
