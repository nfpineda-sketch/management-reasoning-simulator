from pathlib import Path
s = Path('app.py').read_text()
assert 'MVP v0.6.0.31' in s
assert 'POCUS available' not in s
assert 'Basic labs available' not in s
assert 'POCUS: ' in s
assert 'Labs: ' in s
assert 'WBC ' in s and 'HCO₃ ' in s and 'Cr ' in s
assert 'v0.6.0.31: low/moderate norepinephrine can recruit tissue perfusion' in s
assert '0.11 * (norepi / (0.50 + norepi))' in s
assert 'v0.6.0.31: at a starting dose' in s
print('v0.6.0.31 decision-state + norepinephrine regression passed')
