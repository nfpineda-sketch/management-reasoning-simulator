"""PHASE2_AMENDMENT_2 (A2-019R): every mutant of the amendment's required behaviour must be CAUGHT.

The control run (no mutant) must be green; each mutant run (``test_amendment_2_mutants_plugin``) must fail at least one of
the focused amendment tests. A surviving mutant would mean a behaviour the faculty required is not protected.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

import test_amendment_2_mutants_plugin as plugin

ROOT = Path(__file__).resolve().parent
FOCUSED = ("test_phase2_amendment_2_physiology.py", "test_phase2_amendment_2_gi_matrix.py")


def _run(mutant: str):
    env = {**os.environ, plugin.FLAG: mutant, "PYTHONPATH": str(ROOT)}
    return subprocess.run([sys.executable, "-m", "pytest", "-x", "--tb=no", "-p", "no:cacheprovider", "-p",
                           "test_amendment_2_mutants_plugin", *FOCUSED], cwd=ROOT, env=env, capture_output=True,
                          text=True, timeout=600)


def test_the_control_run_without_a_mutant_is_green():
    result = _run("")
    assert result.returncode == 0, result.stdout[-1500:]
    assert "INACTIVE" in result.stdout


@pytest.mark.parametrize("mutant", plugin.MUTANTS)
def test_each_mutant_is_caught_by_the_focused_tests(mutant):
    result = _run(mutant)
    assert result.returncode != 0, f"mutant {mutant!r} SURVIVED: a required behaviour is not protected"
    assert f"ACTIVE: {mutant}" in result.stdout


def test_an_unknown_mutant_is_refused_not_ignored():
    result = _run("not_a_mutant")
    assert result.returncode != 0 and "unknown amendment 2 mutant" in (result.stdout + result.stderr)
