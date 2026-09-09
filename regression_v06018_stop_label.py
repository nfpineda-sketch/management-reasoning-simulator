from pathlib import Path
s=Path("app.py").read_text()
assert 'if s.get("operation") == "stop":\n                        labels.append("norepinephrine stopped")' in s
print("v0.6.0.18 stop-label regression: PASS")
