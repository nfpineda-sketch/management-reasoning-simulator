import ast, re, math, random
from copy import deepcopy
from pathlib import Path

src=Path("app.py").read_text()
assert "MVP v0.8.21 — dynamic learner-visible ECG with lower-pressure PS001 entry" in src
tree=ast.parse(src)
funcs=[n for n in tree.body if isinstance(n,ast.FunctionDef)]

class SS(dict):
    __getattr__=dict.get
    __setattr__=dict.__setitem__
class FakeSt:
    def __init__(self):
        self.session_state=SS()

st=FakeSt()
st.session_state.state={"treatments":{
    "norepinephrine":False,"dobutamine":False,"nitroglycerin":False,
    "niv":False,"oxygen":True,"norepinephrine_rate":0,"norepinephrine_units":None
}}
st.session_state.pending_bundle=None
st.session_state.pending_action=None
ns={"re":re,"math":math,"random":random,"deepcopy":deepcopy,"st":st}
exec(compile(ast.Module(body=funcs,type_ignores=[]),"subset","exec"),ns)

assert ns["parse_niv_order"]("initiate BiPAP 16/8 FiO2 100%")==("BiPAP",8.0,16.0,8.0,100.0)
assert ns["parse_niv_order"]("Increase CPAP to 10 cc H2O")[0:2]==("CPAP",10.0)

decision2=(
    "give 1000 ns, initiate NIV with 100% IFO2 send blood cultures, lab exams. "
    "Blood pressure got better, but despite oxygen patient is still hypoxic. "
    "I'll start NIV to increase inspired fraction and give some positive pressure. reassess in 15 min"
)
p=ns["clinical_interpreter"](decision2)
types=[a["type"] for a in p["actions"]]
assert "oxygen" not in types, p["actions"]
assert {"fluid","niv","reassessment","basic_labs","blood_cultures"} <= set(types)
assert p["reasoning"].get("problem_representation")=="still hypoxic"
assert p["reasoning"].get("expected_effect")=="increase inspired fraction and give some positive pressure"

idx=types.index("niv")
ns["hold_pending_bundle"](p,idx)
st.session_state.pending_action=deepcopy(p["actions"][idx])
resolved=ns["try_resolve_pending_action"]("16/8")
assert resolved and resolved.get("parsed")
merged=ns["merge_pending_bundle"](resolved["parsed"])
assert [a["type"] for a in merged["actions"]]==types
assert merged["reasoning"]==p["reasoning"]
niv=next(a for a in merged["actions"] if a["type"]=="niv")
assert niv["mode"]=="BiPAP" and niv["ipap_cmh2o"]==16 and niv["epap_cmh2o"]==8
assert niv["fio2_percent"]==100

q=ns["clinical_interpreter"]("any new symptoms, fever?")
assert {"focused_history","temperature"} <= {a["type"] for a in q["actions"]}

decision5=(
    "give 500 cc ns lab exams including creatinine, cbc, crp, urine patient is doing better, "
    "already preload taken care off, tolerating NIV, but still hypoxic. "
    "I think she doesn't need intubation at this point. Increase CPAP to 10 cc H2O reassess in 15 min"
)
p5=ns["clinical_interpreter"](decision5)
types5={a["type"] for a in p5["actions"]}
assert {"fluid","basic_labs","urinalysis","niv","reassessment"} <= types5
assert next(a for a in p5["actions"] if a["type"]=="niv")["pressure_cmh2o"]==10

ab=ns["clinical_interpreter"]("initiate IV ceftriaxone 2 gr send blood cultures repeat POCUS")
anti=next(a for a in ab["actions"] if a["type"]=="antibiotics")
assert anti["agent"]=="ceftriaxone" and anti["dose_g"]==2 and anti["route"]=="IV"
assert {"pocus","blood_cultures","antibiotics"} <= {a["type"] for a in ab["actions"]}

disp=ns["clinical_interpreter"]("admit to ICU")
assert any(a["type"]=="disposition" and a["destination"]=="ICU" for a in disp["actions"])

print("PASS: v0.7.2 compound bundle integrity")
