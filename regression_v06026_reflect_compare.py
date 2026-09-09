from pathlib import Path
s=Path('app.py').read_text()
assert 'Reflect & Compare' in s
assert '_reflect_compare_items' in s
assert 'reassessment_target' in s
print('v0.6.0.26 regression passed')
