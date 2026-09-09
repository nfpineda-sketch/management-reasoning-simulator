from pathlib import Path
s=Path("app.py").read_text()
assert "MVP v0.6.0.37 — target-aware Reflect & Compare" in s
assert "baseline_reassuring" in s
assert "selected.sort(key=lambda x: x[1])" in s
print("PASS: v0.6.0.37 target-aware chronological Reflect & Compare")
