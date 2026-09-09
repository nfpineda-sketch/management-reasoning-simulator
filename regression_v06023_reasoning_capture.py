import ast
from pathlib import Path
import re

source = Path("app.py").read_text()
tree = ast.parse(source)
wanted = {
    "_clean_reasoning_phrase",
    "_resolve_reasoning_coreference",
    "extract_explicit_reasoning",
}
nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in wanted]
ns = {"re": re}
exec(compile(ast.Module(body=nodes, type_ignores=[]), "reasoning_subset", "exec"), ns)
extract = ns["extract_explicit_reasoning"]

# Pure command must not manufacture reasoning.
r = extract("perform synchronized cardioversion 200 J and reassess in 5 min")
assert r == {}, r

# Explicit causal reasoning: distinct semantic slots.
r = extract("I think AF with RVR is causing the poor perfusion, so I want to start norepinephrine 0.2 mcg/kg/min to support arterial pressure and reassess perfusion in 10 min")
assert r.get("rationale") == "AF with RVR is causing the poor perfusion", r
assert r.get("problem_representation") != r.get("rationale"), r
assert "poor perfusion" in r.get("problem_representation", "").lower(), r
assert "AF with RVR" in r.get("problem_representation", ""), r
assert r.get("expected_effect") == "support arterial pressure", r
assert r.get("reassessment_target") == "perfusion", r

# Partial reasoning: only explicit priority is captured.
r = extract("My priority is to restore perfusion. Start norepinephrine 0.1 mcg/kg/min.")
assert r.get("management_priority") == "restore perfusion", r
assert "rationale" not in r and "expected_effect" not in r, r

# Explicit problem without causal theory.
r = extract("He remains poorly perfused despite an acceptable blood pressure, so reassess perfusion in 5 min")
assert "poorly perfused" in r.get("problem_representation", "").lower(), r
assert "rationale" not in r, r
assert r.get("reassessment_target") == "perfusion", r

# Multiple explicit slots.
r = extract("The patient remains cold and poorly perfused. My priority is to improve forward flow. I want to start dobutamine 5 mcg/kg/min to improve cardiac output and reassess perfusion in 10 min.")
assert "cold and poorly perfused" in r.get("problem_representation", "").lower(), r
assert r.get("management_priority") == "improve forward flow", r
assert r.get("expected_effect") == "improve cardiac output", r
assert r.get("reassessment_target") == "perfusion", r

print("PASS: v0.6.0.23 conservative reasoning capture + slot separation")
