"""The corrections registry is complete, and every test it cites exists."""
import ast
from datetime import date
from pathlib import Path

import pytest

import corrections_registry as registry

ROOT = Path(__file__).resolve().parent


def _functions(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


@pytest.mark.parametrize("entry", registry.CORRECTIONS, ids=[e["id"] for e in registry.CORRECTIONS])
def test_every_entry_states_scope_reason_versions_and_tests(entry):
    assert entry["scope"]["level"] in registry.SCOPES
    if entry["scope"]["level"] == "family":
        assert entry["scope"]["family"]
    if entry["scope"]["level"] == "variant":
        assert entry["scope"]["variants"]
    assert entry["kind"] in registry.KINDS
    assert entry["clinical_relevance"] in registry.RELEVANCE
    assert len(entry["reason"]) > 40 and entry["title"] and entry["authorised_by"]
    assert isinstance(entry["affects"]["modules"], list) and entry["affects"]["modules"]
    assert isinstance(entry["affects"]["versions"], dict)
    date.fromisoformat(entry["date"])
    assert entry["tests"]


@pytest.mark.parametrize("entry", registry.CORRECTIONS, ids=[e["id"] for e in registry.CORRECTIONS])
def test_every_cited_test_exists(entry):
    for reference in entry["tests"]:
        filename, _, name = reference.partition("::")
        path = ROOT / filename
        assert path.exists(), reference
        assert name.split("[")[0] in _functions(path), reference


def test_identifiers_are_unique_and_ordered():
    identifiers = [entry["id"] for entry in registry.CORRECTIONS]
    assert len(identifiers) == len(set(identifiers)) == len(registry.CORRECTIONS)
    assert identifiers == sorted(identifiers)


def test_no_entry_records_an_approval_of_a_clinical_criterion():
    """An entry names the instruction it was made under, never someone's clinical approval."""
    for entry in registry.CORRECTIONS:
        assert not {"approved_by", "reviewed_by", "approval", "approved"} & set(entry), entry["id"]
        assert entry["authorised_by"].startswith("Instrucción"), entry["id"]


def test_only_cosmetic_entries_can_waive_a_review():
    for entry in registry.CORRECTIONS:
        if entry.get("fingerprint_changes"):
            assert entry["clinical_relevance"] == "cosmetic", entry["id"]
    assert registry.cosmetic_waivers() == []


def test_the_versions_the_registry_names_are_the_code_s():
    import glucose_rescue
    from case_assessment import COVERAGE_VERSION
    import hypoglycemia_catalog
    current = {"coverage": COVERAGE_VERSION, "glucose_rescue": glucose_rescue.VERSION,
               "catalog": f"hypoglycemia {hypoglycemia_catalog.VERSION}"}
    named = {}
    for entry in registry.CORRECTIONS:
        for key, change in entry["affects"]["versions"].items():
            named.setdefault(key, change["to"])
    assert set(named) <= set(current), set(named) - set(current)
    for key, version in named.items():
        assert version == current[key], key
    assert {"coverage", "catalog"} <= set(named)
