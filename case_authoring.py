"""Compact author contract; deterministic expansion into the unchanged runtime schema."""
from copy import deepcopy
import math
from generated_case_schema import CASE_SCHEMA, SCHEMA_VERSION, NUMERIC_FIELDS, RESULT_FIELDS, obj, enum, validate_schema
from clinical_core_defaults import CORE_VERSION

DERIVED = set(NUMERIC_FIELDS) & set(RESULT_FIELDS) | {'paco2_mm_hg', 'ph'}
AUTHOR_SCHEMA = deepcopy(CASE_SCHEMA)

def remove(schema, *fields):
    for field in fields:
        schema['properties'].pop(field)
        schema['required'].remove(field)

remove(AUTHOR_SCHEMA, 'schema_version')
engine = AUTHOR_SCHEMA['properties']['engine']
remove(engine, 'model', 'volume_model', 'terminal_rule', 'untreated_drift_per_min')
remove(engine['properties']['core_profile'], 'version')
remove(engine['properties']['response_rules']['items'], 'volume_basis', 'diuresis_ml_min')
# These actions always execute natively; selective agents and non-AF
# cardioversion retain their extension contracts.
NATIVE_ONLY = {'fluid', 'oxygen', 'niv', 'bag_mask', 'intubation',
               'ventilator_adjustment', 'norepinephrine', 'dobutamine',
               'nitroglycerin', 'airway_preparation', 'antibiotics'}
action_schema = engine['properties']['response_rules']['items']['properties']['action_type']
action_schema['enum'] = [kind for kind in action_schema['enum'] if kind not in NATIVE_ONLY]
# Several response-rule fields are legal only for particular action types. Once
# the native-only actions leave the enum, some of them can no longer be used by
# any action the author may write. Structured outputs still require every
# property, so the author has to emit them, and any non-null value is a fatal
# compile error whose message names the field's range rather than the action
# type it does not apply to. v0.24.7 removed volume_basis/diuresis_ml_min for
# the same reason; derive the rest from the executor's own legality sets so a
# later enum change cannot quietly reintroduce an unusable option.
from generated_dynamics import INFUSIONS
_KIND_RESTRICTED_RULE_FIELDS = {
    'washout_min': frozenset(INFUSIONS),
    'interpolate_settings': frozenset({'ventilator_adjustment'}),
    'mental_status_during': frozenset({'procedural_sedation'}),
    'mental_status_threshold': frozenset({'procedural_sedation'}),
    'rhythm_before': frozenset({'cardioversion'}),
    'rhythm_after': frozenset({'cardioversion'}),
    'recurrence': frozenset({'cardioversion'}),
    'settings': frozenset({'cardioversion', 'ventilator_adjustment'}),
}
UNUSABLE_RULE_FIELDS = tuple(sorted(
    field for field, kinds in _KIND_RESTRICTED_RULE_FIELDS.items()
    if not kinds.intersection(action_schema['enum'])))
remove(engine['properties']['response_rules']['items'], *UNUSABLE_RULE_FIELDS)
# Legacy compartment drivers are unavailable when volume_model is null.
from generated_physiology import VOLUME_FIELDS
def restrict_drivers(node):
    if isinstance(node, dict):
        if 'enum' in node and set(node['enum']) & set(VOLUME_FIELDS):
            node['enum'] = [x for x in node['enum'] if x not in VOLUME_FIELDS]
        for value in node.values():
            restrict_drivers(value)
    elif isinstance(node, list):
        for value in node:
            restrict_drivers(value)
restrict_drivers(engine)
study = AUTHOR_SCHEMA['properties']['investigations']['items']
remove(study, 'result_bindings')
original_value = deepcopy(study['properties']['result']['items']['properties']['value'])
study['properties']['result']['items'] = {'anyOf': [obj({'field': enum(sorted(DERIVED))}),
    obj({'field': enum([f for f in RESULT_FIELDS if f not in DERIVED]), 'value': original_value})]}

INSTRUCTIONS = '''Return the compact author schema. The application supplies schema/core version, engine model,
null volume_model/terminal_rule, empty untreated drift, and diagnostic bindings. Do not emit those fields.
Do not author response_rules for native-only actions excluded from that enum; those actions remain executable.
For modeled investigation measurements emit only their field name, without a repeated value. The application
copies the value from observable or initial_labs (paco2 uses pco2), and derives pH from baseline bicarbonate
and pco2. Author those source values carefully once. This finite engine shares the CO2 source across gas
studies; do not promise independently modeled arterial/venous CO2. Nonmodeled results and all clinical
history, findings, diagnoses, management paths and extension effects remain your responsibility.
'''

def collapse_identical_study_fields(raw):
    """Drop exact duplicate rows only; conflicting duplicates reach validation."""
    result = deepcopy(raw)
    for study in result.get('investigations', []):
        for key in ('result', 'result_bindings'):
            if key not in study:
                continue
            unique = []
            for row in study[key]:
                if row not in unique:
                    unique.append(row)
            study[key] = unique
    return result


def expand_author_case(raw):
    validate_schema(raw, AUTHOR_SCHEMA)
    case = collapse_identical_study_fields(raw)
    case['schema_version'] = SCHEMA_VERSION
    engine = case['engine']
    engine.update(model=CORE_VERSION, volume_model=None, terminal_rule=None, untreated_drift_per_min=[])
    engine['core_profile']['version'] = CORE_VERSION
    for rule in engine['response_rules']:
        rule.update(volume_basis=None, diuresis_ml_min=None)
        rule.update(dict.fromkeys(UNUSABLE_RULE_FIELDS))
    baseline = {**case['observable'], **engine['initial_labs']}
    for study in case['investigations']:
        study['result_bindings'] = []
        required = {'poc_glucose': 'glucose_mg_dl', 'temperature': 'temperature_c', 'lactate': 'lactate_mmol_l'}.get(study['id'])
        if required and not any(item['field'] == required for item in study['result']):
            study['result'].append({'field': required})
        for item in study['result']:
            field = item['field']
            if field not in DERIVED:
                continue
            if field == 'ph':
                item['value'] = round(6.1 + math.log10(baseline['bicarbonate_mmol_l'] / (.03 * baseline['pco2_mm_hg'])), 3)
            else:
                source = 'pco2_mm_hg' if field == 'paco2_mm_hg' else field
                item['value'] = baseline[source]
                study['result_bindings'].append({'field': field, 'observable_field': source})
    validate_schema(case, CASE_SCHEMA)
    return case
