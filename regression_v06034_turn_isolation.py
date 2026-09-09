import ast, re
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

source = Path('app.py').read_text()
tree = ast.parse(source)
module = ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef)], type_ignores=[])
ss = SimpleNamespace(state={'treatments': {'dobutamine': False, 'norepinephrine': False}})
ns = {'re': re, 'deepcopy': deepcopy, 'st': SimpleNamespace(session_state=ss)}
exec(compile(module, 'v06034_extract', 'exec'), ns)
parse = ns['clinical_interpreter']

commands = [
    "My working diagnosis is AF with RVR causing hemodynamic compromise. My priority is to restore effective cardiac output. Perform synchronized cardioversion 200 J. I expect restoration of sinus rhythm to improve perfusion. Reassess perfusion in 5 min.",
    "The patient is now in sinus rhythm but I am concerned that reduced effective circulating volume is contributing to the remaining perfusion abnormality. Give 1000 mL NS IV to improve preload and reassess perfusion in 10 min.",
    "The response to the first fluid bolus was limited. My management priority is to determine whether the patient remains fluid responsive. Give another 1000 mL NS IV. I expect further improvement in perfusion if low preload is still important. Reassess perfusion in 10 min.",
    "The patient is deteriorating despite rhythm control and fluids. My working model is that another cause of shock is driving the ongoing hypoperfusion. Perform POCUS and obtain lactate and basic laboratory tests to better characterize the shock state. Reassess in 10 min.",
]
parsed = [parse(c) for c in commands]

# Decision 3: reasoning must survive alongside the fluid order.
r3 = parsed[2]['reasoning']
assert r3.get('management_priority','').lower() == 'determine whether the patient remains fluid responsive', r3
assert r3.get('expected_effect','').lower() == 'further improvement in perfusion', r3
assert r3.get('reassessment_target','').lower() == 'perfusion', r3
acts3 = parsed[2]['actions']
assert [a['type'] for a in acts3] == ['fluid', 'reassessment'], acts3
assert acts3[0]['volume_ml'] == 1000, acts3
assert acts3[1]['delay_min'] == 10, acts3

# Decision 4: reasoning mention of "fluids" must NEVER create/reuse a fluid action.
r4 = parsed[3]['reasoning']
assert 'ongoing hypoperfusion' in r4.get('problem_representation','').lower(), r4
assert 'another cause of shock' in r4.get('problem_representation','').lower(), r4
acts4 = parsed[3]['actions']
assert [a['type'] for a in acts4] == ['reassessment', 'pocus', 'lactate', 'basic_labs'], acts4
assert not any(a['type'] == 'fluid' for a in acts4), acts4
assert next(a for a in acts4 if a['type']=='reassessment')['delay_min'] == 10, acts4

# Bare discussion of a prior bolus is not a new order.
mention = parse('The response to the first fluid bolus was limited. I want to reconsider the diagnosis.')
assert not any(a['type'] == 'fluid' for a in mention['actions']), mention

print('PASS: v0.6.0.34 exact four-turn reasoning/action isolation regression')
