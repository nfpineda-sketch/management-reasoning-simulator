from pathlib import Path
import ast

s = Path("app.py").read_text()
assert "v0.6.0.28" in s
assert 'event.get("recognized_future_actions")' in s
assert '(recognized; not yet executable)' in s
assert 'return " + ".join(labels) if labels else "Reassessment"' in s
ast.parse(s)
print("PASS: v0.6.0.28 recognized future actions preserved in learner Management Trace")
