import ast,re
from pathlib import Path
s=Path("app.py").read_text()
assert "MVP v0.7.1" in s
assert '"nimv"' in s and '"noninvasive mechanical ventilation"' in s
assert 'filtered_events = [e for e in trace' in s
assert 'What dobutamine dose would you like to use in mcg/kg/min' in s
for token in ['{"type": "temperature"}','{"type": "poc_glucose"}','{"type": "chest_xray"}','{"type": "urinalysis"}','{"type": "blood_cultures"}','{"type": "antibiotics"']:
    assert token in s, token
tree=ast.parse(s)
wanted={"parse_niv_order","parse_agent_mcg_rate"}
nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in wanted]
ns={"re":re}
exec(compile(ast.Module(body=nodes,type_ignores=[]),"subset","exec"),ns)
assert ns["parse_niv_order"]("initiate NIMV")[0]=="CPAP"
assert ns["parse_niv_order"]("initiate noninvasive mechanical ventilation CPAP 8 cm H2O")==("CPAP",8.0)
assert ns["parse_agent_mcg_rate"]("add dobutamine 10 mcg.min",["dobutamine"])==(None,None)
assert ns["parse_agent_mcg_rate"]("add dobutamine 10 mcg/kg/min",["dobutamine"])==(10.0,"mcg/kg/min")
print("PASS: v0.7.1 targeted regression")
