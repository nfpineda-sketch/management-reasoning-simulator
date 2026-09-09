from pathlib import Path
s = Path("app.py").read_text()
assert "MVP v0.6.0.32" in s
assert "base_reserve_loss = 0.003 if pressor_preserving else 0.020" in s
assert "if 0.5 <= norepi <= 1.5 and current_map >= 62 and cardiac_output >= 0.18:" in s
assert "max(h[\"tissue_perfusion\"], 0.24)" in s
assert "prior_extremities == \"Warm\" and o.get(\"extremities\") == \"Warmer\"" in s
print("v0.6.0.32 norepinephrine stabilization regression passed")
