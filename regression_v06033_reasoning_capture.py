import ast
import re
from pathlib import Path

source = Path('app.py').read_text()
tree = ast.parse(source)
wanted = {
    '_clean_reasoning_phrase',
    '_resolve_reasoning_coreference',
    'extract_explicit_reasoning',
}
module = ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in wanted], type_ignores=[])
ns = {'re': re}
exec(compile(module, 'reasoning_extract', 'exec'), ns)
extract = ns['extract_explicit_reasoning']

# Commands alone still cannot manufacture reasoning.
assert extract('start norepinephrine 0.1 mcg/kg/min and reassess in 10 min') == {}

r = extract("My working diagnosis is distributive shock. My management goal is to restore perfusion. Start norepinephrine 0.1 mcg/kg/min to support arterial pressure and reassess perfusion in 10 min.")
assert r.get('problem_representation','').lower() == 'distributive shock', r
assert r.get('management_priority','').lower() == 'restore perfusion', r
assert r.get('expected_effect','').lower() == 'support arterial pressure', r
assert r.get('reassessment_target','').lower() == 'perfusion', r

r = extract("I am concerned that persistent vasodilation is driving the hypotension, so start norepinephrine. I expect this to increase arterial pressure and reassess perfusion in 5 min.")
assert 'hypotension' in r.get('problem_representation','').lower(), r
assert 'persistent vasodilation' in r.get('problem_representation','').lower(), r
assert 'driving the hypotension' in r.get('rationale','').lower(), r
assert r.get('expected_effect','').lower() == 'increase arterial pressure', r
assert r.get('reassessment_target','').lower() == 'perfusion', r

r = extract("My working model is persistent low flow despite adequate pressure. My priority is to improve forward flow. Start dobutamine 5 mcg/kg/min to improve cardiac output and reassess perfusion in 10 min.")
assert 'persistent low flow despite adequate pressure' in r.get('problem_representation','').lower(), r
assert r.get('management_priority','').lower() == 'improve forward flow', r
assert r.get('expected_effect','').lower() == 'improve cardiac output', r
assert r.get('reassessment_target','').lower() == 'perfusion', r

print('PASS: v0.6.0.33 expanded conservative explicit Reasoning Capture')
