from pathlib import Path
src = Path(__file__).with_name('app.py').read_text()
assert 'current_map < 45 or o["sbp"] < 70' in src
assert 'desired_mental = "Obtunded"' in src
assert 'current_map < 32 or o["sbp"] < 55' in src
assert 'desired_mental = "Unresponsive"' in src
assert 'current_map < 55 or o["sbp"] < 85' in src
assert 'desired_mental = "Drowsy"' in src
print('PASS v0.6.0.19 acute-hypotension neurologic deterioration regression')
