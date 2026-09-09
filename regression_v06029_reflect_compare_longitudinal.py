import ast
from pathlib import Path
src=Path('app.py').read_text()
assert 'Across Decisions ' in src
assert 'You made several management decisions without explicitly stating the reasoning guiding them.' in src
assert 'At what points did your working model of the patient change?' in src
# Ensure legacy single-decision prompt remains available.
assert 'No management reasoning was explicitly stated.' in src
ast.parse(src)
print('v0.6.0.29 regression passed')
