"""The reload tests change shared modules only in an interpreter of their own (TD-05, cycle 10).

The night audit of cycle 5 (59R) listed test_generation_reload.py as changing versions and
functions of shared modules when pytest imports it. Every test there that does so already runs
its source through ``run_isolated``, in a separate interpreter: running the whole file in one
process leaves the thirteen modules it touches exactly as they were (checked in cycle 10). This
keeps it so: in the file itself, nothing at the top level but imports and definitions, and no
function that assigns to, deletes from or reloads a module; the isolated sources are strings.
"""
import ast
from pathlib import Path

SOURCE = Path(__file__).with_name("test_generation_reload.py")


def _mutations(tree):
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.Delete)):
            targets = node.targets
        elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
            targets = [node.target]
        else:
            targets = []
        if any(isinstance(target, ast.Attribute) for target in targets):
            yield node
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "reload":
            yield node


def test_the_reload_tests_touch_modules_only_in_their_own_interpreter():
    text = SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(text)
    for node in tree.body:
        assert isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef)) or (
            isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)), ast.get_source_segment(text, node)
    assert [ast.get_source_segment(text, node) for node in _mutations(tree)] == []


def test_the_check_would_have_caught_a_mutation_in_the_file_itself():
    tree = ast.parse("import generated_case\n"
                     "def test_x():\n    generated_case.GENERATOR_VERSION = '0.1'\n    importlib.reload(generated_case)\n")
    assert len(list(_mutations(tree))) == 2
