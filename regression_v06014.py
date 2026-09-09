#!/usr/bin/env python3
"""Deterministic regression for v0.6.0.14 delayed neurologic recovery."""
import ast
from pathlib import Path
from copy import deepcopy

APP = Path(__file__).with_name("app.py")
source = APP.read_text()
tree = ast.parse(source)
selected=[]
for node in tree.body:
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        # Skip Streamlit import; a fake object is injected below.
        names=[]
        if isinstance(node, ast.Import):
            if any(a.name == "streamlit" for a in node.names):
                continue
        selected.append(node)
    elif isinstance(node, (ast.FunctionDef, ast.Assign)):
        # Avoid top-level Streamlit config; preserve constants + all functions.
        if isinstance(node, ast.Assign):
            targets=[getattr(x,'id',None) for x in node.targets]
            if not any(x in {"INITIAL_STATE","PRESENTATION"} for x in targets):
                continue
        selected.append(node)
mod=ast.Module(body=selected,type_ignores=[])
ns={}
exec(compile(mod,str(APP),"exec"),ns)

class Session(dict):
    def __getattr__(self,k): return self[k]
    def __setattr__(self,k,v): self[k]=v
class FakeSt:
    def __init__(self): self.session_state=Session()
st=FakeSt(); ns['st']=st
st.session_state.state=deepcopy(ns['INITIAL_STATE'])
st.session_state.pending_action=None
st.session_state.pending_bundle=None
st.session_state.last_executed_action=None
st.session_state.rng_counter=0

# Create the target low-output post-cardioversion phenotype directly so this test
# isolates the pressure-vs-flow contract from fluid/rhythm regression tests.
s=st.session_state.state; h=s['hidden']; o=s['observable']; tr=s['treatments']
o.update({'sbp':91,'dbp':61,'hr':93,'rhythm':'Sinus rhythm','crt':8,'extremities':'Mottled/Cold','mental_status':'Obtunded'})
h.update({'cardiac_function':0.62,'contractile_reserve':0.55,'low_flow_burden':0.72,'tissue_perfusion':0.075,
          'pulmonary_congestion':0.28,'respiratory_failure_severity':0.20,'sinus_stability':0.90,
          'minutes_since_cardioversion':5,'cardiac_output_index':0.22,'forward_flow_state':0.22})
tr.update({'norepinephrine':True,'norepinephrine_rate':0.4,'norepinephrine_units':'mcg/kg/min'})

# Norepinephrine alone for 10 minutes must not normalize perfusion.
for _ in range(10):
    ns['apply_natural_disease'](s,1)
assert s['observable']['crt'] >= 7, s['observable']
assert s['observable']['extremities'] in ('Mottled/Cold','Very cold','Cold'), s['observable']

# Add dobutamine 5; improvement must be progressive, not instantaneous.
ns['dobutamine_transition'](s,5.0,'mcg/kg/min','start')
crt0=s['observable']['crt']; mental0=s['observable']['mental_status']
ns['apply_natural_disease'](s,1)
assert s['observable']['crt'] >= 6, s['observable']
assert not (s['observable']['crt'] <= 3 and s['observable']['mental_status']=='Alert'), s['observable']

checkpoints=[]
for mins in (4,5,5,10):
    ns['apply_natural_disease'](s,mins)
    checkpoints.append((s['sim_time'], s['observable']['sbp'], s['observable']['dbp'], s['observable']['crt'],
                        s['observable']['extremities'], s['observable']['mental_status'], h['cardiac_output_index']))

# By 15-25 minutes of active inotropy, direction must be improved from the nadir.
assert s['observable']['crt'] < crt0, checkpoints
# Neurologic recovery should lag peripheral perfusion: at 10 minutes the patient
# must not already be fully Alert merely because CRT has improved.
assert checkpoints[1][5] != 'Alert', checkpoints
# By ~25 minutes, recovery may be underway but should still depend on sustained
# oxygen delivery; severe hypoxemia can legitimately delay a fully Alert state.
# Recovery must remain progressive: no instant normalization in the first 10 min.
assert checkpoints[1][3] >= 5, checkpoints
# Dobutamine should not behave like a second high-amplitude pressor.
assert max(row[1] for row in checkpoints) - checkpoints[0][1] <= 15, checkpoints
assert h['cardiac_output_index'] > 0.22, checkpoints
assert s['observable']['mental_status'] != 'Unresponsive', checkpoints
assert 55 <= s['observable']['dbp'] <= 90, checkpoints
assert 75 <= s['observable']['sbp'] <= 125, checkpoints
print('PASS v0.6.0.14 delayed-neurologic-recovery regression')
for row in checkpoints: print(row)
