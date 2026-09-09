from pathlib import Path
s=Path('app.py').read_text()
assert 'MVP v0.6.0.33' in s
for label in ['Problem', 'Priority', 'Rationale', 'Expected effect', 'Reassessment target']:
    assert label in s
assert 'Not explicitly stated' in s
print('PASS: v0.6.0.33 reasoning slots remain learner-facing and conservative')
