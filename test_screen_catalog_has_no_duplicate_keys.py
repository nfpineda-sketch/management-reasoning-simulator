"""A key written twice in a screen catalog silently keeps only the last value (TD-43, cycle 10)."""
import ast
from pathlib import Path


def test_no_catalog_dictionary_repeats_a_key():
    for module in ("report_language.py", "language.py", "screen_language.py"):
        tree = ast.parse(Path(__file__).with_name(module).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Dict):
                continue
            keys = [key.value for key in node.keys if isinstance(key, ast.Constant)]
            repeated = sorted({key for key in keys if keys.count(key) > 1}, key=str)
            assert repeated == [], (module, node.lineno, repeated[:5])
