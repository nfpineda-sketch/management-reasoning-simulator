"""A stopped norepinephrine infusion must be labelled as stopped, not re-dosed.

This checked app.py's source text and broke when the label block was re-indented,
so it failed on the published branch while the behaviour was intact. Assert the
rendered label instead.
"""
import ast
from pathlib import Path

source = Path("app.py").read_text()
tree = ast.parse(source)
node = next(n for n in tree.body
            if isinstance(n, ast.FunctionDef) and n.name == "_norepinephrine_summary_label")
namespace = {}
exec(compile(ast.Module(body=[node], type_ignores=[]), "app.py", "exec"), namespace)
label = namespace["_norepinephrine_summary_label"]

assert label({"support_type": "norepinephrine", "operation": "stop"}) == "norepinephrine stopped"
assert "stopped" not in label({"support_type": "norepinephrine", "operation": "start",
                               "rate": 0.1, "units": "mcg/kg/min"})
# The submit path must reach that label for a stop summary rather than a dose.
assert 'labels.append("norepinephrine stopped")' in source
print("v0.6.0.18 stop-label regression: PASS")
