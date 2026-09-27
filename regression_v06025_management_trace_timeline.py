from pathlib import Path
s=Path('app.py').read_text()
assert 'def render_management_trace(trace):' in s
assert 'Not explicitly stated' in s
# The label goes through the catalog since 2026-09-27 (Idioma 4b); the same response time.
assert 'w("Observed response · {time}", time=t1)' in s
assert '_trace_observable_delta' in s
print('PASS: v0.6.0.25 learner Management Trace timeline')
