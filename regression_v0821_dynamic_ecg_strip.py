"""The learner-visible rhythm strip renders the trace and does not read it.

This pinned app.py's SIMULATOR_VERSION and exact source lines, so it failed on
every release after 0.8.21 while the strip worked. Assert the rendered SVG.
"""
import ast
import math
from html import escape
from pathlib import Path

source = Path("app.py").read_text(encoding="utf-8")
tree = ast.parse(source)
nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_ecg_strip_svg"]
namespace = {"math": math, "escape": escape}
exec(compile(ast.Module(body=nodes, type_ignores=[]), "v0821_ecg_subset", "exec"), namespace)
render = namespace["_ecg_strip_svg"]


def label_of(svg):
    return svg.split('aria-label="', 1)[1].split('"', 1)[0]


af = render({"hr": 162, "rhythm": "AF", "pulse_present": True})
assert 'data-rhythm="af"' in af and 'data-rate="162"' in af
assert "25 mm/s · 10 mm/mV · 5 s" in af

sinus = render({"hr": 97, "rhythm": "Sinus rhythm", "pulse_present": True})
assert 'data-rhythm="sinus"' in sinus and 'data-rate="97"' in sinus
# Different rhythms must draw differently; that is what the resident reads.
assert sinus != af

pea = render({"hr": 40, "rhythm": "PEA", "pulse_present": False})
assert 'data-rhythm="pea"' in pea
assert "No palpable pulse" in label_of(pea)

# The strip describes itself; naming the rhythm is the resident's work.
for svg in (af, sinus, pea):
    assert "Synthetic lead II rhythm strip" in label_of(svg)
    for name in ("Sinus rhythm", "Atrial fibrillation", "atrial fibrillation",
                 "narrow QRS", "ventricular response", "(PEA)"):
        assert name not in label_of(svg), name

print("PASS: the rhythm strip renders AF, sinus and PEA without interpreting them")
