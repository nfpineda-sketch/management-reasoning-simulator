"""Regression coverage for the learner-visible dynamic ECG strip."""

import ast
import math
from html import escape
from pathlib import Path


source = Path("app.py").read_text(encoding="utf-8")
assert 'SIMULATOR_VERSION = "0.8.21"' in source
assert "st.markdown(_ecg_strip_svg(o), unsafe_allow_html=True)" in source
assert "Synthetic educational rhythm strip · Lead II" in source

tree = ast.parse(source)
function_names = {"_ecg_interpretation", "_ecg_strip_svg"}
nodes = [
    node
    for node in tree.body
    if isinstance(node, ast.FunctionDef) and node.name in function_names
]
namespace = {"math": math, "escape": escape}
exec(compile(ast.Module(body=nodes, type_ignores=[]), "v0821_ecg_subset", "exec"), namespace)

render = namespace["_ecg_strip_svg"]
interpret = namespace["_ecg_interpretation"]

af = {"hr": 162, "rhythm": "AF", "pulse_present": True}
af_svg = render(af)
assert 'data-rhythm="af"' in af_svg
assert 'data-rate="162"' in af_svg
assert "25 mm/s · 10 mm/mV · 5 s" in af_svg
assert "Synthetic lead II ECG" in af_svg
assert "rapid ventricular response" in interpret(af)
assert "no consistent P waves" in interpret(af)

controlled_af = {"hr": 96, "rhythm": "AF", "pulse_present": True}
assert 'data-rhythm="af"' in render(controlled_af)
assert "controlled ventricular response" in interpret(controlled_af)

sinus = {"hr": 97, "rhythm": "Sinus rhythm", "pulse_present": True}
sinus_svg = render(sinus)
assert 'data-rhythm="sinus"' in sinus_svg
assert 'data-rate="97"' in sinus_svg
assert sinus_svg != af_svg
assert "Sinus rhythm at approximately 97/min; narrow QRS." == interpret(sinus)

pea = {"hr": 40, "rhythm": "PEA", "pulse_present": False}
pea_svg = render(pea)
assert 'data-rhythm="pea"' in pea_svg
assert "without a palpable pulse (PEA)" in interpret(pea)

print("PASS: v0.8.21 renders a dynamic educational ECG for AF, sinus rhythm, and PEA")
