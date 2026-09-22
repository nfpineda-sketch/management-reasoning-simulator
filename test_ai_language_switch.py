"""The paid language normalization is opt-in, and the parser is the default.

Faculty decision B4, 2026-09-23. The normalizer runs before every order, every
clarification and every reasoning completion. With a provider key configured it
therefore cost one paid request per submission, which was measured as six
requests in a five-order encounter while preparing the demonstration. The
deterministic parser reads the Spanish this faculty writes, so the paid path is
now something you switch on, not something a key switches on for you.

The predicate is read straight out of the application, because reaching the
"on" state through the interface would mean starting a paid encounter.
"""
import ast
from pathlib import Path

import pytest

import offline_cases

APP = str(Path(__file__).with_name("app.py"))


def predicate():
    source = Path(APP).read_text(encoding="utf-8")
    wanted = next(node for node in ast.parse(source).body
                  if isinstance(node, ast.FunctionDef)
                  and node.name == "ai_language_interpretation_enabled")
    namespace = {}
    exec(compile(ast.Module([wanted], []), APP, "exec"), namespace)
    return namespace["ai_language_interpretation_enabled"], namespace


def configured(key, switch):
    enabled, namespace = predicate()
    namespace["_runtime_secret"] = lambda name, default="": (
        key if name == "OPENAI_API_KEY" else switch if name == "MRS_AI_LANGUAGE" else default)
    return enabled()


@pytest.mark.parametrize("switch", ["1", "true", "TRUE", "yes", "on"])
def test_the_switch_and_the_key_together_turn_it_on(switch):
    assert configured("a-key", switch) is True


@pytest.mark.parametrize("switch", ["", "0", "false", "off", "no", "maybe"])
def test_a_key_alone_is_not_enough(switch):
    assert configured("a-key", switch) is False


@pytest.mark.parametrize("switch", ["1", ""])
def test_the_switch_alone_is_not_enough(switch):
    assert configured("", switch) is False


def test_offline_mode_still_decides_first(monkeypatch):
    # Every key resolver passes through withhold, so offline mode empties the
    # key before the predicate ever sees it. That is what keeps a replay free.
    monkeypatch.setenv("MRS_OFFLINE_CASES", "1")
    assert offline_cases.withhold("OPENAI_API_KEY", "a-key") == ""
    assert configured(offline_cases.withhold("OPENAI_API_KEY", "a-key"), "1") is False


def test_the_application_asks_the_switch_and_not_only_the_key():
    # A regression guard: the normalizer must consult the new predicate before
    # it reads the key, or a configured deployment starts paying per order again.
    source = Path(APP).read_text(encoding="utf-8")
    body = source[source.index("def normalize_clinical_turn("):]
    body = body[:body.index("\ndef ", 10)]
    assert "ai_language_interpretation_enabled()" in body
    assert body.index("ai_language_interpretation_enabled()") < body.index('_runtime_secret("OPENAI_API_KEY")')
