"""MRS_OFFLINE_CASES=1 must let a person use the whole encounter for free.

Every launch path called AI case generation, so the encounter could not be
exercised locally without paying. The first version of this switch only covered
launch and still issued patient-image requests: the key is read in seven places
during an encounter. Offline is therefore enforced where the key is resolved.

The suite's own conftest already refuses sockets, so these tests also prove the
switch does not lean on that guard: they assert what each resolver returns.
"""
import ast
import os
from pathlib import Path

import pytest

import offline_cases

ROOT = Path(__file__).resolve().parent


@pytest.fixture
def offline(monkeypatch):
    monkeypatch.setenv("MRS_OFFLINE_CASES", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-must-not-be-used")


def test_the_switch_is_off_unless_it_is_set(monkeypatch):
    monkeypatch.delenv("MRS_OFFLINE_CASES", raising=False)
    assert offline_cases.offline_cases_enabled() is False
    assert offline_cases.withhold("OPENAI_API_KEY", "sk-real") == "sk-real"
    assert offline_cases.launch_options("sk-real", "admin") == ({"api_key": "sk-real"}, "sk-real")


@pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "on"])
def test_the_switch_accepts_the_usual_spellings(monkeypatch, value):
    monkeypatch.setenv("MRS_OFFLINE_CASES", value)
    assert offline_cases.offline_cases_enabled() is True


@pytest.mark.parametrize("value", ["0", "false", "no", "", "off"])
def test_the_switch_stays_off_for_anything_else(monkeypatch, value):
    monkeypatch.setenv("MRS_OFFLINE_CASES", value)
    assert offline_cases.offline_cases_enabled() is False


def test_offline_launch_uses_authored_cases_and_no_key(offline):
    generation, scene_key = offline_cases.launch_options("sk-must-not-be-used")
    assert generation == {"generation_mode": "authored", "api_key": ""}
    assert scene_key == ""


def test_only_provider_keys_are_withheld(offline):
    assert offline_cases.withhold("OPENAI_API_KEY", "sk-x") == ""
    assert offline_cases.withhold("APP_PASSWORD", "local") == "local"
    assert offline_cases.withhold("MRS_IMAGE_MODEL", "gpt-image-1.5") == "gpt-image-1.5"


def test_every_key_resolver_in_the_app_withholds_the_key(offline):
    """The image, history, normalization and faculty paths all read through these."""
    import clinical_scene
    import curriculum_runtime
    import faculty_portal
    assert clinical_scene.setting("OPENAI_API_KEY") == ""
    assert curriculum_runtime._secret("OPENAI_API_KEY") == ""
    assert faculty_portal._secret("OPENAI_API_KEY") == ""
    assert clinical_scene.setting("APP_PASSWORD", "fallback") != ""


def test_app_runtime_secret_withholds_the_key(offline):
    source = (ROOT / "app.py").read_text()
    tree = ast.parse(source)
    node = next(n for n in tree.body
                if isinstance(n, ast.FunctionDef) and n.name == "_runtime_secret")
    namespace = {"st": type("S", (), {"secrets": {}})(), "os": os}
    exec(compile(ast.Module(body=[node], type_ignores=[]), "app.py", "exec"), namespace)
    assert namespace["_runtime_secret"]("OPENAI_API_KEY") == ""


def test_no_key_resolver_bypasses_the_offline_rule():
    """A new resolver that reads the key directly would reopen the leak."""
    readers = {}
    for path in ROOT.glob("*.py"):
        if path.name.startswith(("test_", "regression_")) or path.name in {"conftest.py", "offline_cases.py"}:
            continue
        tree = ast.parse(path.read_text())
        for node in tree.body:
            if not isinstance(node, ast.FunctionDef):
                continue
            body = ast.get_source_segment(path.read_text(), node) or ""
            reads_secrets = "st.secrets.get(name" in body or "os.environ.get(name" in body
            if reads_secrets:
                readers[f"{path.name}:{node.name}"] = "withhold(" in body
    assert readers, "no generic secret resolvers found; the check is stale"
    assert all(readers.values()), {k: v for k, v in readers.items() if not v}


def test_every_menu_challenge_has_an_offline_case(offline):
    from curriculum import CHALLENGES
    from cognitive_catalog import BIAS_CHALLENGES
    from encounter_generator import generate_encounter
    tree = ast.parse((ROOT / "app.py").read_text())
    node = next(n for n in tree.body if isinstance(n, ast.Assign)
                and any(getattr(t, "id", "") == "INITIAL_STATE" for t in n.targets))
    initial = ast.literal_eval(node.value)
    offered = list(BIAS_CHALLENGES) + [k for k in CHALLENGES if k not in BIAS_CHALLENGES]
    for challenge in offered:
        generation, _ = offline_cases.launch_options("sk-must-not-be-used")
        encounter = generate_encounter(challenge, initial, seed=17, **generation)
        assert encounter["state"], challenge
