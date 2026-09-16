"""Offline contract regression tests; no network or third-party test runner."""
import ast
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from clinical_core_defaults import PHENOTYPE_FIELDS, INITIAL_HIDDEN, CORE_VERSION
from generated_case_schema import SCHEMA_VERSION, STATE_TEXT, CASE_SCHEMA, REVIEW_SCHEMA, compile_case, validate_schema
from case_authoring import AUTHOR_SCHEMA, DERIVED, UNUSABLE_RULE_FIELDS, expand_author_case
from generated_case import generate_ai_encounter


def fixture():
    # Reuse the exact existing regression fixture without importing pytest.
    source = ast.parse(Path(__file__).with_name('test_generated_case.py').read_text())
    fn = next(n for n in source.body if isinstance(n, ast.FunctionDef) and n.name == 'novel_payload')
    ns = dict(globals())
    exec(compile(ast.Module(body=[fn], type_ignores=[]), 'fixture', 'exec'), ns)
    return ns['novel_payload']()


def compact(case):
    case = deepcopy(case)
    # The historical fixture includes legacy fluid/volume compatibility rules.
    # New authors rely on native fluids, retaining the steroid extension only.
    case['engine']['response_rules'] = [r for r in case['engine']['response_rules'] if r['action_type'] != 'fluid']
    for rule in case['engine']['response_rules']:
        rule.pop('volume_basis')
        rule.pop('diuresis_ml_min')
        # Fields no author-selectable action can use are not offered any more.
        for field in UNUSABLE_RULE_FIELDS:
            rule.pop(field)
    case.pop('schema_version')
    for field in ('model', 'volume_model', 'terminal_rule', 'untreated_drift_per_min'):
        case['engine'].pop(field)
    case['engine']['core_profile'].pop('version')
    for study in case['investigations']:
        study.pop('result_bindings')
        for item in study['result']:
            if item['field'] in DERIVED:
                item.pop('value')
    return case


class CompactTests(unittest.TestCase):
    def test_expansion_preserves_patient_and_validates(self):
        raw = compact(fixture()); before = deepcopy(raw)
        expanded = expand_author_case(raw)
        compiled = compile_case(expanded)
        self.assertEqual(raw, before)
        for key in ('patient','history','examination','faculty','observable'):
            self.assertEqual(expanded[key], raw[key])
        self.assertEqual(compiled['engine']['core_profile']['version'], CORE_VERSION)
        self.assertLess(len(json.dumps(AUTHOR_SCHEMA)), len(json.dumps(CASE_SCHEMA)))
        self.assertLess(len(json.dumps(raw)), len(json.dumps(expanded)))

    def test_omitted_binding_conflict_is_classified_and_rejected(self):
        raw = fixture()
        study = next(x for x in raw['investigations'] if x['id'] == 'poc_glucose')
        study['result_bindings'] = []
        next(x for x in study['result'] if x['field']=='glucose_mg_dl')['value'] += 40
        with self.assertRaises(ValueError) as caught:
            compile_case(raw)
        codes = {x['code'] for x in caught.exception.issues}
        self.assertIn('DIAGNOSTIC_BINDING', codes)
        self.assertNotIn('CONTRACT_UNCLASSIFIED', codes)

    def test_rejects_injected_value_and_retains_duplicate_gate(self):
        raw = compact(fixture())
        study = next(x for x in raw['investigations'] if x['id']=='poc_glucose')
        study['result'][0]['value'] = 999
        with self.assertRaises(ValueError):
            expand_author_case(raw)
        raw = compact(fixture())
        raw['investigations'].append(deepcopy(raw['investigations'][0]))
        with self.assertRaises(ValueError):
            compile_case(expand_author_case(raw))

    def test_full_generation_reviews_expanded_case_before_launch(self):
        calls=[]
        class Client:
            @property
            def responses(self): return self
            def create(self, **kwargs):
                calls.append(kwargs)
                if len(calls)==1:
                    self_case=compact(fixture())
                    validate_schema(self_case, kwargs['text']['format']['schema'])
                    data=self_case
                else:
                    sent=json.loads(kwargs['input'])
                    assert sent['case']['engine']['model']==CORE_VERSION
                    data={'coherent':True,'issues':[], 'checks':{k:True for k in REVIEW_SCHEMA['properties']['checks']['properties']}}
                return SimpleNamespace(status='completed', output_text=json.dumps(data),output=[])
        result=generate_ai_encounter('R1-05', {'sim_time':0}, client=Client(), seed=11)
        self.assertEqual(len(calls),2)
        self.assertEqual(result['state']['engine_family'],'generated')
        self.assertEqual(result['spec']['challenge_id'],'R1-05')

if __name__=='__main__': unittest.main()
