"""The challenge the offline server opens on (2026-09-21).

Playing one family repeatedly means restarting the server for it; the picker
opened on R1-05 every time and the challenge had to be chosen again by hand.
"""
import ast
from pathlib import Path

import pytest


def default_challenge(monkeypatch, value=None):
    source = Path(__file__).with_name("app.py").read_text()
    node = next(n for n in ast.parse(source).body
                if isinstance(n, ast.FunctionDef) and n.name == "_default_challenge")
    from curriculum import CHALLENGES
    namespace = {"os": __import__("os"), "CHALLENGES": CHALLENGES}
    if value is None:
        monkeypatch.delenv("MRS_DEFAULT_CHALLENGE", raising=False)
    else:
        monkeypatch.setenv("MRS_DEFAULT_CHALLENGE", value)
    exec(compile(ast.Module(body=[node], type_ignores=[]), "app.py", "exec"), namespace)
    return namespace["_default_challenge"]()


def test_unset_is_the_problem_the_app_always_opened_on(monkeypatch):
    assert default_challenge(monkeypatch) == "R1-05"


@pytest.mark.parametrize("value, challenge", [
    ("R2-02", "R2-02"), ("R3-01", "R3-01"), ("R1-06", "R1-06"),
    # A stray space in a shell is not a typo worth punishing.
    ("R2-02 ", "R2-02"), (" R3-01", "R3-01"),
])
def test_a_named_challenge_is_the_one_that_opens(monkeypatch, value, challenge):
    assert default_challenge(monkeypatch, value) == challenge


@pytest.mark.parametrize("value", ["", "   ", "R9-99", "acs", "r2-02"])
def test_anything_that_is_not_a_challenge_falls_back(monkeypatch, value):
    # A typo in a shell must not leave the faculty without a launch screen.
    assert default_challenge(monkeypatch, value) == "R1-05"
