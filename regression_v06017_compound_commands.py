import ast
from pathlib import Path

src = Path(__file__).with_name('app.py').read_text()
tree = ast.parse(src)
fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'local_command_operation')
ns = {'re': __import__('re')}
exec(compile(ast.Module(body=[fn], type_ignores=[]), '<local_command_operation>', 'exec'), ns)
f = ns['local_command_operation']

assert f('stop norepinephrine, continue dobutamine 5 mcg/kg/min, and reassess in 15 min', ['norepinephrine','norepi','levophed']) == 'stop'
assert f('stop norepinephrine, continue dobutamine 5 mcg/kg/min, and reassess in 15 min', ['dobutamine']) == 'continue'
assert f('continue norepinephrine 0.2 mcg/kg/min and stop dobutamine', ['norepinephrine','norepi']) == 'continue'
assert f('continue norepinephrine 0.2 mcg/kg/min and stop dobutamine', ['dobutamine']) == 'stop'
assert f('increase norepinephrine to 0.3 mcg/kg/min, continue dobutamine 5 mcg/kg/min', ['norepinephrine']) == 'titrate'
assert f('increase norepinephrine to 0.3 mcg/kg/min, continue dobutamine 5 mcg/kg/min', ['dobutamine']) == 'continue'
print('PASS: compound infusion verbs are scoped to the named drug clause')
