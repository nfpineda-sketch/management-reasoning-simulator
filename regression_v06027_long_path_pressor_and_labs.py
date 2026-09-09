from pathlib import Path

s = Path('app.py').read_text()
assert 'v0.6.0.27' in s
assert '"basic laboratory tests" not in future' in s
assert 'future.append("basic laboratory tests")' in s
assert '"type": "laboratory"' not in s

def bonus(n):
    return 21.0 * n / (0.25 + n)
vals = [bonus(x) for x in [0, 0.5, 1, 2, 3, 4, 5]]
assert all(b > a for a, b in zip(vals, vals[1:])), vals
assert bonus(1.0) >= 16.5
assert 'norepi_pressure_bonus = 21.0 * norepi / (0.25 + norepi)' in s
assert '+ norepi_pressure_bonus' in s
print('v0.6.0.27 regression passed')
