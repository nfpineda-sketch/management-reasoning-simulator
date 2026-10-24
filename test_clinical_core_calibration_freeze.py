"""Phase 2 shadow core, P2G-1: the calibration freeze covers every input of the harness.

The digest is split by component so a change says where it is. These tests prove that the
family-engine path is listed exactly (traced in a fresh interpreter) and that a change to a
scenario, to a file of the path, to the order adapter, to the harness itself (a check binding, a
design default, a band), to the migration gate or its trusted registries (their source, and
since P2H-1 the policies, mappings and approvals as loaded), or to a materialized input changes
the digest.
"""
import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from clinical_core import calibration, legacy_adapter, shadow

ROOT = Path(__file__).resolve().parent

#: Run in a fresh interpreter: every repository file executed (imported or called) or opened
#: while the harness builds the GI arrivals and materializes every scenario input.
TRACE = r"""
import json, os, sys
ROOT = os.getcwd()
executed, opened = set(), set()
def tracer(frame, event, arg):
    if event == "call" and frame.f_code.co_filename.startswith(ROOT + os.sep):
        executed.add(os.path.relpath(frame.f_code.co_filename, ROOT))
def audit(event, args):
    if event == "open" and args and isinstance(args[0], (str, bytes, os.PathLike)):
        path = os.path.abspath(os.fsdecode(args[0]))
        if path.startswith(ROOT + os.sep) and "__pycache__" not in path:
            opened.add(os.path.relpath(path, ROOT))
sys.addaudithook(audit)
sys.settrace(tracer)
from clinical_core import calibration
calibration.scenario_inputs()
sys.settrace(None)
print(json.dumps({"executed": sorted(executed), "opened": sorted(opened - executed)}))
"""


@pytest.fixture(scope="module")
def traced():
    result = subprocess.run([sys.executable, "-c", TRACE], cwd=ROOT, capture_output=True, text=True, timeout=600,
                            env={**os.environ, "PYTHONPATH": str(ROOT)})
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout.strip().splitlines()[-1])


def test_the_input_path_manifest_is_exactly_what_runs(traced):
    outside = {path for path in traced["executed"] if not path.startswith("clinical_core" + os.sep)}
    assert outside == set(calibration.INPUT_PATH_SOURCES), (
        "the family-engine path changed: update INPUT_PATH_SOURCES and record why")
    assert set(calibration.INPUT_ADAPTER_SOURCES) <= set(traced["executed"])
    # The path reads no data file besides Python sources (the bank is clinical_cases.py).
    assert not [path for path in traced["opened"] if not path.endswith(".py")]
    assert "clinical_cases.py" in calibration.INPUT_PATH_SOURCES


@pytest.mark.parametrize("path, component", [
    ("family_engine.py", "input_path_sources"), ("family_parser.py", "input_path_sources"),
    ("clinical_cases.py", "input_path_sources"), ("clinical_core/legacy_adapter.py", "input_adapter_sources"),
    ("clinical_core/gi_reference.py", "gi_reference"), ("clinical_core/calibration.py", "harness_sources"),
    ("clinical_core/bands.py", "harness_sources"), ("clinical_core/migration.py", "migration_sources"),
    ("clinical_core/migration_authority.py", "migration_sources")])
def test_a_changed_input_source_changes_the_digest(monkeypatch, path, component):
    before = calibration.digest_components()
    original = calibration._source_bytes
    monkeypatch.setattr(calibration, "_source_bytes",
                        lambda name: original(name) + (b"\n# changed\n" if name == path else b""))
    after = calibration.digest_components()
    assert {name for name in before if before[name] != after[name]} == {component}


@pytest.mark.parametrize("registry", ["AUTHORITY_POLICIES", "TRUSTED_CASE_MAPPINGS", "APPROVED_FAMILY_DEFAULTS"])
def test_a_changed_authority_registry_changes_the_digest(monkeypatch, registry):
    """P2H-1: the policies, mappings and approvals as loaded are part of the trust boundary."""
    from clinical_core import migration_authority as authority
    entries = {
        "AUTHORITY_POLICIES": (authority.AuthorityPolicy("gi_bleed", "pump_reserve", authority.FAMILY_FIXED_VALUE, "1",
                                                         "test only"),),
        "TRUSTED_CASE_MAPPINGS": (authority.CaseMapping("test-map", "1", "gi_bleed", "pump_reserve",
                                                        ("engine.family",), lambda fields: True,
                                                        lambda fields: 0.5, "test only"),),
        "APPROVED_FAMILY_DEFAULTS": (authority.ApprovedDefault("gi_bleed", "pump_reserve", "test-approval", "1",
                                                               "approved", value=0.5),)}
    before = calibration.digest_components()
    monkeypatch.setattr(authority, registry, entries[registry])
    after = calibration.digest_components()
    assert {name for name in before if before[name] != after[name]} == {"authority_registries"}
    if registry == "AUTHORITY_POLICIES":
        monkeypatch.setattr(authority, registry, (replace(entries[registry][0], policy=authority.CASE_REQUIRED),))
        assert calibration.digest_components()["authority_registries"] != after["authority_registries"], \
            "changing only a parameter's policy changes the digest"
    if registry == "TRUSTED_CASE_MAPPINGS":
        monkeypatch.setattr(authority, registry, (replace(entries[registry][0], rule=lambda fields: 0.6),))
        assert calibration.digest_components()["authority_registries"] != after["authority_registries"], \
            "changing only a mapping's rule changes the digest"


@pytest.mark.parametrize("registry, field, value", [
    ("APPROVED_FAMILY_DEFAULTS", "fallback", 0.7), ("APPROVED_FAMILY_DEFAULTS", "low", 0.6),
    ("APPROVED_FAMILY_DEFAULTS", "high", 0.95), ("APPROVED_FAMILY_DEFAULTS", "status", "proposed"),
    ("AUTHORITY_POLICIES", "version", "2"), ("AUTHORITY_POLICIES", "rationale", "another rationale"),
    ("AUTHORITY_POLICIES", "policy", "FAMILY_ALLOWED_RANGE")])
def test_review_p2h2_t3_every_field_of_a_trusted_record_is_pinned(monkeypatch, registry, field, value):
    from clinical_core import migration_authority as authority
    records = {"APPROVED_FAMILY_DEFAULTS": authority.ApprovedDefault("gi_bleed", "pump_reserve", "test-approval", "1",
                                                                     "approved", low=0.5, high=0.9, fallback=0.8),
               "AUTHORITY_POLICIES": authority.AuthorityPolicy("gi_bleed", "pump_reserve", authority.CASE_REQUIRED,
                                                               "1", "test only")}
    monkeypatch.setattr(authority, registry, (records[registry],))
    before = authority.registry_hash()
    monkeypatch.setattr(authority, registry, (replace(records[registry], **{field: value}),))
    assert authority.registry_hash() != before, field


#: A module-level table a registered rule may read; the digest pins its content.
RULE_TABLE = {"pump_reserve": 0.5}


def _registered(rule, precondition=lambda fields: True):
    from clinical_core import migration_authority as authority
    return (authority.CaseMapping("test-map", "1", "gi_bleed", "pump_reserve", ("engine.family",), precondition,
                                  rule, "test only"),)


def _digest_of(monkeypatch, mappings):
    from clinical_core import migration_authority as authority
    monkeypatch.setattr(authority, "TRUSTED_CASE_MAPPINGS", mappings)
    return json.dumps(authority.registry_content(), sort_keys=True)


def test_review_f2_the_digest_pins_what_a_registered_rule_computes(monkeypatch):
    """P2H-1 review F2: keyword defaults and the globals a rule reads."""
    def keyword(value):
        return lambda fields, *, number=value: number
    assert _digest_of(monkeypatch, _registered(keyword(0.5))) != _digest_of(monkeypatch, _registered(keyword(0.7)))
    reads = _registered(lambda fields: RULE_TABLE["pump_reserve"])
    before = _digest_of(monkeypatch, reads)
    monkeypatch.setitem(RULE_TABLE, "pump_reserve", 0.9)
    assert _digest_of(monkeypatch, reads) != before


def test_review_f2_content_the_digest_cannot_pin_is_refused(monkeypatch):
    class Opaque:
        pass
    opaque = Opaque()
    with pytest.raises(TypeError, match="cannot pin"):
        _digest_of(monkeypatch, _registered(lambda fields, thing=opaque: 0.5))
    outside = eval("lambda fields: 0.5", {"__name__": "not_in_the_repository"})
    with pytest.raises(TypeError, match="defined in a source file of the repository"):
        _digest_of(monkeypatch, _registered(outside))
    # P2H-2: code built at run time has no source in the repository, so the digest cannot pin it.
    with pytest.raises(TypeError, match="source file of the repository"):
        _digest_of(monkeypatch, _registered(eval("lambda fields: 0.5")))


def set_bound_mapping():
    """A registered mapping whose precondition carries a set: its order depends on the hash seed."""
    keys = frozenset({"b", "a", "c", "engine.family", "gi_bleed"})
    return _registered(lambda fields: 0.5, precondition=lambda fields, keys=keys: "gi_bleed" in keys)


def test_review_f2_equal_sets_have_one_digest_form_whatever_their_iteration_order():
    from clinical_core import migration_authority as authority
    first, second = frozenset([1, 9]), frozenset([9, 1])  # 1 and 9 collide: insertion order decides iteration
    assert first == second and list(first) != list(second)
    assert authority._digest_form(first) == authority._digest_form(second)
    assert authority._digest_form({"b": 1, "a": 2}) == authority._digest_form({"a": 2, "b": 1})


def test_review_f2_the_registry_digest_is_the_same_in_every_interpreter():
    script = ("import json\n"
              "from clinical_core import migration_authority as a\n"
              "from test_clinical_core_calibration_freeze import set_bound_mapping\n"
              "a.TRUSTED_CASE_MAPPINGS = set_bound_mapping()\n"
              "print(json.dumps(a.registry_content(), sort_keys=True))\n")
    outputs = set()
    for seed in ("1", "2", "3"):
        result = subprocess.run([sys.executable, "-c", script], cwd=ROOT, capture_output=True, text=True, timeout=120,
                                env={**os.environ, "PYTHONPATH": str(ROOT), "PYTHONHASHSEED": seed})
        assert result.returncode == 0, result.stderr
        outputs.add(result.stdout)
    assert len(outputs) == 1


def test_a_changed_scenario_changes_the_digest_and_is_never_served_stale(monkeypatch):
    before = calibration.digest_components()
    changed = {**shadow.SCENARIOS, "untreated_60": {"minutes": 60, "orders": {0: "Give pantoprazole 80 mg IV."}}}
    monkeypatch.setattr(shadow, "SCENARIOS", changed)
    after = calibration.digest_components()
    assert {name for name in before if before[name] != after[name]} == {"scenarios", "scenario_inputs"}
    _, contributors, _ = calibration._legacy("gi_bleed_57m", "untreated_60")
    assert any(type(item).__name__ == "ProtonPumpInhibitor" for item in contributors)


def test_a_changed_materialized_input_changes_the_digest(monkeypatch):
    before = calibration.digest_components()
    literals = dict(legacy_adapter.LEGACY_LITERALS)
    literals["gi_bleeding_circulation_per_min"] = (0.004, literals["gi_bleeding_circulation_per_min"][1])
    monkeypatch.setattr(legacy_adapter, "LEGACY_LITERALS", literals)
    after = calibration.digest_components()
    assert {name for name in before if before[name] != after[name]} == {"scenario_inputs"}


def test_the_digest_is_reproducible_in_a_fresh_interpreter():
    script = "from clinical_core import calibration; print(calibration.frozen_digest())"
    result = subprocess.run([sys.executable, "-c", script], cwd=ROOT, capture_output=True, text=True, timeout=600,
                            env={**os.environ, "PYTHONPATH": str(ROOT)})
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == calibration.frozen_digest()
