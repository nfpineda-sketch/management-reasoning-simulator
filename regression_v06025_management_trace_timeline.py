from pathlib import Path
s=Path('app.py').read_text()
assert 'def render_management_trace(trace):' in s
assert 'Not explicitly stated' in s
assert 'Observed response · {t1}' in s
assert '_trace_observable_delta' in s
print('PASS: v0.6.0.25 learner Management Trace timeline')
