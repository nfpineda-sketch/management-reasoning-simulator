from pathlib import Path
s=Path('app.py').read_text()
assert 'MVP v0.7.0 — multiple clinical surfaces' in s
assert 'PS001 · Tachyarrhythmia in an Acutely Ill Patient' in s
assert 'PS002 · Acute Dyspnea with Shock' in s
assert 'def build_ps002_state()' in s
assert '"primary_respiratory_burden": 0.66' in s
assert '"rhythm": "Sinus rhythm"' in s
assert '"spo2": 86' in s
assert 'st.selectbox(' in s
assert 'cfg["state_factory"]()' in s
assert 'add_event("presentation", cfg["presentation"], 0)' in s
assert 'primary_resp = clamp(h.get("primary_respiratory_burden", 0.0))' in s
print('PASS: v0.7.0 multiple clinical surfaces scaffold')
