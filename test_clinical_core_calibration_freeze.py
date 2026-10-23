"""Phase 2 shadow core, P2G-1: the calibration freeze covers every input of the harness.

The digest is split by component so a change says where it is. These tests prove that the
family-engine path is listed exactly (traced in a fresh interpreter) and that a change to a
scenario, to a file of the path, to the order adapter, to the harness itself (a check binding, a
design default, a band) or to a materialized input changes the digest.
"""
import json
import os
import subprocess
import sys
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
    ("clinical_core/bands.py", "harness_sources")])
def test_a_changed_input_source_changes_the_digest(monkeypatch, path, component):
    before = calibration.digest_components()
    original = calibration._source_bytes
    monkeypatch.setattr(calibration, "_source_bytes",
                        lambda name: original(name) + (b"\n# changed\n" if name == path else b""))
    after = calibration.digest_components()
    assert {name for name in before if before[name] != after[name]} == {component}


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
