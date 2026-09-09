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

# Command-only input must not have inferred reasoning.
r = extract('cardiovert 200 J and reassess in 5 min')
assert r == {}, r

# Explicit interpretation + causal rationale + expected effect + targeted reassessment.
r = extract('I think AF with RVR is causing the poor perfusion, so I want to cardiovert 200 J to improve forward flow and reassess perfusion in 5 min.')
assert 'poor perfusion' in r.get('problem_representation', '').lower(), r
assert 'AF with RVR' in r.get('problem_representation', ''), r
assert 'causing the poor perfusion' in r.get('rationale', ''), r
assert r.get('problem_representation') != r.get('rationale'), r
assert r.get('expected_effect', '').lower() == 'improve forward flow', r
assert r.get('reassessment_target', '').lower() == 'perfusion', r

# Explicit priority is captured without inventing other fields.
r = extract('My immediate priority is to improve perfusion, so start norepinephrine 0.1 mcg/kg/min.')
assert r.get('management_priority', '').lower() == 'improve perfusion', r
assert 'rationale' not in r, r

# Because-clause is captured as rationale.
r = extract('Start norepinephrine because the patient remains poorly perfused despite fluids.')
assert r.get('rationale', '').lower() == 'the patient remains poorly perfused despite fluids', r

print('PASS v0.6.0.23 backward Reasoning Capture regression')
