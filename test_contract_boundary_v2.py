"""Phase 1 WP8: prove Contracts v2 remain shadow-only at the app/engine boundary."""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from contracts_v2 import events, fates, observations, orders, submissions, timing, trace


ROOT = Path(__file__).resolve().parent
RUNTIME_BOUNDARY_FILES = {"app.py", "order_pipeline.py"}


def _source(name):
    return (ROOT / name).read_text(encoding="utf-8")


def _imports_contracts_v2(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name == "contracts_v2" or alias.name.startswith("contracts_v2.")
                   for alias in node.names):
                return True
        elif isinstance(node, ast.ImportFrom):
            if node.module == "contracts_v2" or (
                node.module and node.module.startswith("contracts_v2.")
            ):
                return True
    return False


def _shadow_calls(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    parents = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent

    calls = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr.startswith("shadow_"):
            calls.append((node, parents.get(node)))
    return calls


def test_all_phase1_contract_modules_are_version_2():
    modules = (orders, fates, timing, events, observations, trace, submissions)
    assert all(module.VERSION == 2 for module in modules)
    assert len({module.SCHEMA for module in modules}) == len(modules)


def test_contracts_v2_runtime_imports_are_confined_to_explicit_boundaries():
    offenders = []
    for path in ROOT.glob("*.py"):
        if path.name.startswith("test_"):
            continue
        if path.name in {"tools_contract_baseline.py"}:
            continue
        if _imports_contracts_v2(path) and path.name not in RUNTIME_BOUNDARY_FILES:
            offenders.append(path.name)

    assert offenders == []


@pytest.mark.parametrize(
    "name",
    [
        "family_engine.py",
        "family_parser.py",
        "shared_order_language.py",
    ],
)
def test_engine_and_frozen_readers_do_not_import_contracts_v2(name):
    path = ROOT / name
    assert path.exists(), name
    assert not _imports_contracts_v2(path), name


def test_order_pipeline_contains_only_shadow_contract_calls_for_v2():
    source = _source("order_pipeline.py")

    expected = (
        "order_contracts_v2",
        "fate_contracts_v2",
        "time_contracts_v2",
        "event_contracts_v2",
        "observation_contracts_v2",
    )
    for alias in expected:
        assert alias in source

    calls = _shadow_calls(ROOT / "order_pipeline.py")
    assert calls
    assert all(isinstance(parent, ast.Expr) for _, parent in calls)


def test_app_contains_only_shadow_contract_calls_for_trace_and_submission():
    source = _source("app.py")
    assert "trace_contracts_v2.shadow_from_legacy_trace(event)" in source
    assert "submission_contracts_v2.shadow_from_legacy_entries" in source

    calls = _shadow_calls(ROOT / "app.py")
    assert calls
    assert all(isinstance(parent, ast.Expr) for _, parent in calls)


def test_no_runtime_boundary_uses_v2_serialized_records_as_engine_input():
    forbidden = (
        ".as_record(",
        ".legacy_projection(",
        ".legacy_payload(",
    )
    for name in RUNTIME_BOUNDARY_FILES:
        source = _source(name)
        for token in forbidden:
            assert token not in source, f"{name} unexpectedly consumes v2 projection via {token}"


def test_v2_shadow_results_are_discarded_not_assigned_or_returned():
    for name in RUNTIME_BOUNDARY_FILES:
        calls = _shadow_calls(ROOT / name)
        assert calls, f"no v2 shadow calls found in {name}"
        for call, parent in calls:
            assert isinstance(parent, ast.Expr), (
                f"{name}:{getattr(call, 'lineno', '?')} shadow return value is consumed"
            )
