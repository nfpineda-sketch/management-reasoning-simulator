"""Phase 2 shadow core: the core can never change what a resident sees.

- No module the application runs imports ``clinical_core``.
- ``clinical_core`` imports nothing that touches the session, the Trace, receipts,
  persistence or the page; only its legacy adapter reads the family engine, and only
  through copies.
- A legacy run is identical with and without the shadow run after it, and nothing the
  shadow is given is changed.
"""
import ast
from copy import deepcopy
from pathlib import Path

import pytest

import family_engine
from clinical_core import AUTHORITATIVE_ENGINE, SHADOW_ONLY
from clinical_core.legacy_adapter import (anchors_from_legacy, bank_case, contributors_from_legacy, run_legacy,
                                          snapshot)
from clinical_core.shadow import SCENARIOS, main, run_shadow
from clinical_core.state import digest

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / "clinical_core"
#: What each core file may import besides the standard library and the package itself.
LEGACY_READERS = {"legacy_adapter.py": {"family_engine", "family_parser", "cognitive_catalog", "cognitive_generator"},
                  "shadow.py": {"family_engine"}}
STDLIB = {"__future__", "argparse", "copy", "dataclasses", "enum", "hashlib", "json", "math", "pathlib", "typing"}


def _imports(path):
    names = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            names.add((node.module or "").split(".")[0])
    return names


def test_no_runtime_module_imports_the_core():
    for path in ROOT.rglob("*.py"):
        relative = path.relative_to(ROOT)
        if relative.parts[0] in {"clinical_core", ".venv", ".claude"} or path.name.startswith("test_"):
            continue
        assert "clinical_core" not in _imports(path), relative


def test_the_core_imports_only_what_a_shadow_needs():
    for path in PACKAGE.rglob("*.py"):
        imported = _imports(path) - STDLIB - {""}
        allowed = LEGACY_READERS.get(path.name, set())
        assert imported <= allowed, (path.relative_to(ROOT), imported - allowed)
    assert SHADOW_ONLY is True and AUTHORITATIVE_ENGINE == "family_engine"


def test_the_legacy_run_is_the_same_with_and_without_the_shadow():
    orders, minutes = SCENARIOS["definitive_management"]["orders"], SCENARIOS["definitive_management"]["minutes"]
    alone = run_legacy("gi_bleed_57m", orders, minutes)
    shadowed = run_shadow("gi_bleed_57m", "definitive_management")
    assert digest(list(alone.snapshots)) == digest(list(shadowed.legacy.snapshots))
    assert digest(_plain(alone.final_state)) == digest(_plain(shadowed.legacy.final_state))


def test_nothing_the_shadow_is_given_is_changed():
    state = bank_case("gi_bleed_72f")
    before = deepcopy(state)
    legacy = run_legacy("gi_bleed_72f", SCENARIOS["saline_then_blood"]["orders"], 40, state=state)
    assert state == before, "run_legacy works on its own copy of the encounter state"
    frozen = deepcopy(legacy)
    anchors_from_legacy(legacy.arrival)
    contributors_from_legacy(legacy)
    snapshot(legacy.final_state)
    assert legacy == frozen


def test_the_family_engine_s_tables_are_untouched_by_a_shadow_run():
    tables = {name: deepcopy(getattr(family_engine, name)) for name in ("GI_BLEED", "TRANSFUSION", "EDEMA")}
    run_shadow("gi_bleed_57m", "aggressive_volume")
    assert all(getattr(family_engine, name) == table for name, table in tables.items())


def test_the_comparison_writes_nothing_it_is_not_asked_to(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    golden = PACKAGE / "golden" / "gi_bleed_shadow.json"
    stamp = golden.stat().st_mtime_ns
    assert main([]) == 0
    assert list(tmp_path.iterdir()) == [] and golden.stat().st_mtime_ns == stamp
    assert "mismatching" in capsys.readouterr().out


def _plain(value):
    """The encounter state as JSON-serializable data, for a digest."""
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return sorted(_plain(item) for item in value)
    if isinstance(value, float) and value != value:
        pytest.fail("NaN in the encounter state")
    return value
