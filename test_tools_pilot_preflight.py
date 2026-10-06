"""The pilot's preflight says whether a deployment is configured as the pilot, and never a secret (C10-06).

Pre-deployment readiness (2026-10-06, B-3): the preflight reads the configuration as the application does
(Streamlit's own parser for the Secrets and its own copy into the environment, then the application's own
readers) and fails closed on every requirement of the pilot freeze (``pilot_freeze.RUNTIME_FLAGS``). Before,
``MRS_OFFLINE_CASES = true`` (a TOML boolean, which never reaches the environment) passed while the
application stayed online, and ``MRS_DEFAULT_VARIANT=trauma_hemothorax_41m`` passed with a warning while it
opened the excluded case. Every test here goes through ``preflight.evaluate`` or ``preflight.checks``, the
decision the command prints.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import pilot_freeze
import tools_pilot_preflight as preflight

ROOT = Path(__file__).resolve().parent
COMMIT = "0123456789abcdef0123456789abcdef01234567"
URL = "postgresql://pilot_user:s3cret-pass@db.example.org/pilot?sslmode=require"
KEY = "sk-not-a-real-key"
SECRET_WORDS = ("s3cret-pass", "pilot_user", "db.example.org", KEY)
PILOT = {
    "MRS_AUTH_MODE": '"accounts"',
    "MRS_DATABASE_URL": f'"{URL}"',
    "MRS_OFFLINE_CASES": '"1"',
    "MRS_IMAGE_REQUIRE_REVIEW": '"on"',
    "MRS_PAID_GENERATION": '"off"',
    "MRS_CODE_VERSION": f'"{COMMIT[:12]}"',
    "OPENAI_API_KEY": f'"{KEY}"',
}
ENVIRON = {"PATH": os.environ.get("PATH", "/usr/bin:/bin")}
#: The commit above is made up, so the tests read the repository's config.toml; the preflight itself reads the
#: one of the commit to deploy (test_fast_reruns_is_read_from_the_commit_to_deploy).
CONFIG = ROOT / ".streamlit" / "config.toml"


def _toml(values):
    """A secrets.toml from {name: TOML literal}; None leaves the name out."""
    return "".join(f"{name} = {literal}\n" for name, literal in values.items() if literal is not None)


def _write(tmp_path, values, name="secrets.toml"):
    path = tmp_path / name
    path.write_text(_toml(values), encoding="utf-8")
    return path


def _run(tmp_path, change=None, environ=None, commit=COMMIT, config_path=CONFIG):
    path = _write(tmp_path, {**PILOT, **(change or {})})
    return preflight.evaluate([path], {**ENVIRON, **(environ or {})}, commit=commit, config_path=config_path)


def _rules(tmp_path, change=None, environ=None, commit=COMMIT, config_path=CONFIG):
    path = _write(tmp_path, {**PILOT, **(change or {})})
    view = preflight.load_view([path], {**ENVIRON, **(environ or {})}, config_path)
    return {identifier: (level, holds, message) for identifier, level, holds, message
            in preflight.checks(view, commit=commit)}


def _failed(tmp_path, change=None, environ=None, commit=COMMIT):
    return {identifier for identifier, (level, holds, _) in _rules(tmp_path, change, environ, commit).items()
            if level == preflight.REQUIRED and not holds}


# A. The frozen configuration passes, and nothing secret is printed.

def test_a_the_frozen_configuration_passes_and_no_secret_is_printed(tmp_path):
    text, ready = _run(tmp_path)
    assert ready and text.endswith("Configuración del piloto: LISTA.")
    assert "FALLA" not in text and "AVISO" not in text
    for secret in SECRET_WORDS:
        assert secret not in text


def test_every_freeze_requirement_is_a_required_rule(tmp_path):
    assert set(preflight.FREEZE_RULES) == set(pilot_freeze.RUNTIME_FLAGS)
    rules = _rules(tmp_path)
    for flag, identifier in preflight.FREEZE_RULES.items():
        level, holds, _ = rules[identifier]
        assert level == preflight.REQUIRED and holds, flag


# B and C. MRS_OFFLINE_CASES counts only as the application reads it.

@pytest.mark.parametrize("literal", ['"1"', "1", '"true"', '"on"', '"yes"', '" 1 "'])
def test_offline_values_the_application_activates_pass(tmp_path, literal):
    assert _failed(tmp_path, {"MRS_OFFLINE_CASES": literal}) == set()


def test_b_offline_as_a_toml_boolean_fails(tmp_path):
    # Streamlit copies only text and numbers into the environment, where offline_cases reads it.
    assert _failed(tmp_path, {"MRS_OFFLINE_CASES": "true", "OPENAI_API_KEY": None}) == {"offline_cases"}
    # With the provider key present, the key would also be reachable.
    text, ready = _run(tmp_path, {"MRS_OFFLINE_CASES": "true"})
    assert not ready and "[FALLA] offline_cases" in text and "[FALLA] provider_key_withheld" in text
    assert text.endswith("Configuración del piloto: NO LISTA (2 regla(s) obligatoria(s) sin cumplir).")


@pytest.mark.parametrize("literal", ["false", '"0"', '"off"', '""', '"maybe"', "1.0"])
def test_offline_values_the_application_ignores_fail(tmp_path, literal):
    assert "offline_cases" in _failed(tmp_path, {"MRS_OFFLINE_CASES": literal})


def test_c_offline_missing_fails(tmp_path):
    assert _failed(tmp_path, {"MRS_OFFLINE_CASES": None}) == {"offline_cases", "provider_key_withheld"}
    assert _failed(tmp_path, {"MRS_OFFLINE_CASES": None, "OPENAI_API_KEY": None}) == {"offline_cases"}


def test_offline_from_the_environment_counts_as_the_application_reads_it(tmp_path):
    # A boolean in the Secrets is not copied, so an environment value of the same name stays in force.
    assert _failed(tmp_path, {"MRS_OFFLINE_CASES": "true"}, environ={"MRS_OFFLINE_CASES": "1"}) == set()
    assert _failed(tmp_path, {"MRS_OFFLINE_CASES": None}, environ={"MRS_OFFLINE_CASES": "1"}) == set()


def test_the_preflight_and_the_application_agree_on_offline_and_paid_generation(tmp_path):
    """PREFLIGHT = READY with the application online cannot happen: checked against Streamlit's real loader."""
    offline = {"text_1": '"1"', "int_1": "1", "text_true": '"true"', "toml_true": "true", "toml_false": "false",
               "text_0": '"0"', "empty": '""', "float_1": "1.0", "missing": None}
    paid = {"text_off": '"off"', "toml_false": "false", "text_admin": '"admin"', "missing": None}
    files = {}
    for label, literal in offline.items():
        files[f"offline:{label}"] = str(_write(tmp_path, {**PILOT, "MRS_OFFLINE_CASES": literal}, f"o_{label}.toml"))
    for label, literal in paid.items():
        files[f"paid:{label}"] = str(_write(tmp_path, {**PILOT, "MRS_PAID_GENERATION": literal}, f"p_{label}.toml"))
    child = (
        "import json, os, sys\n"
        f"sys.path.insert(0, {str(ROOT)!r})\n"
        "from streamlit import config\n"
        "from streamlit.runtime.secrets import secrets_singleton\n"
        "import offline_cases\n"
        "found = {}\n"
        "for label, path in json.loads(sys.argv[1]).items():\n"
        "    for name in ('MRS_OFFLINE_CASES', 'MRS_PAID_GENERATION', 'OPENAI_API_KEY'):\n"
        "        os.environ.pop(name, None)\n"
        "    config.set_option('secrets.files', [path])\n"
        "    secrets_singleton._reset()\n"
        "    secrets_singleton.load_if_toml_exists()\n"
        "    offline = offline_cases.offline_cases_enabled()\n"
        "    os.environ.pop('MRS_OFFLINE_CASES', None)\n"
        "    paid_open = any(offline_cases.paid_generation_allowed(r) for r in ('resident', 'faculty', 'admin'))\n"
        "    found[label] = {'offline': offline, 'paid_closed': not paid_open}\n"
        "print(json.dumps(found))\n")
    done = subprocess.run([sys.executable, "-c", child, json.dumps(files)], capture_output=True, text=True,
                          env={**ENVIRON, "HOME": str(tmp_path)}, cwd=tmp_path, timeout=120)
    application = json.loads(done.stdout.strip().splitlines()[-1])
    for label, path in files.items():
        rules = {identifier: holds for identifier, _, holds, _ in
                 preflight.checks(preflight.load_view([path], ENVIRON, CONFIG), commit=COMMIT)}
        if label.startswith("offline:"):
            assert rules["offline_cases"] == application[label]["offline"], label
        else:
            assert rules["paid_generation_off"] == application[label]["paid_closed"], label
    assert application["offline:toml_true"]["offline"] is False and application["offline:text_1"]["offline"] is True


# D and E. A pinned case fails, whichever it is; the excluded haemothorax can never pass.

@pytest.mark.parametrize("variant", ["acs_54m_inferior", "hypoglycemia_28m", "not_a_case_of_the_bank"])
def test_d_any_pinned_case_fails(tmp_path, variant):
    assert _failed(tmp_path, {"MRS_DEFAULT_VARIANT": f'"{variant}"'}) == {"no_pinned_case"}
    assert _failed(tmp_path, environ={"MRS_DEFAULT_VARIANT": variant}) == {"no_pinned_case"}


def test_e_the_excluded_haemothorax_can_never_pass_the_preflight(tmp_path, capsys):
    assert pilot_freeze.excluded("trauma_hemothorax_41m")
    for change, environ in (({"MRS_DEFAULT_VARIANT": '"trauma_hemothorax_41m"'}, None),
                            ({"MRS_DEFAULT_VARIANT": "true"}, None),
                            (None, {"MRS_DEFAULT_VARIANT": "trauma_hemothorax_41m"})):
        text, ready = _run(tmp_path, change, environ)
        assert not ready and "[FALLA] no_pinned_case" in text
        assert "trauma_hemothorax_41m" not in text
    head = _head()
    path = _write(tmp_path, {**PILOT, "MRS_CODE_VERSION": f'"{head[:12]}"',
                             "MRS_DEFAULT_VARIANT": '"trauma_hemothorax_41m"'})
    assert preflight.main(["--secrets", str(path)]) == 1
    out = capsys.readouterr().out
    assert out.count("[FALLA]") == 1 and "[FALLA] no_pinned_case" in out and "NO LISTA" in out


# F, G, H. The other settings the freeze fixes.

def test_f_a_replay_case_fails(tmp_path):
    assert _failed(tmp_path, {"MRS_REPLAY_CASE": '"saved_run.json"'}) == {"no_replay_case"}
    assert _failed(tmp_path, environ={"MRS_REPLAY_CASE": "saved_run.json"}) == {"no_replay_case"}


@pytest.mark.parametrize("literal", [None, '"off"', '""', "false", '"0"'])
def test_g_image_review_not_on_fails(tmp_path, literal):
    assert _failed(tmp_path, {"MRS_IMAGE_REQUIRE_REVIEW": literal}) == {"image_review"}


def test_image_review_counts_as_the_application_reads_it(tmp_path):
    # image_scene reads st.secrets itself, where a TOML boolean true does mean "on".
    assert _failed(tmp_path, {"MRS_IMAGE_REQUIRE_REVIEW": "true"}) == set()
    assert _failed(tmp_path, {"MRS_IMAGE_REQUIRE_REVIEW": None}, environ={"MRS_IMAGE_REQUIRE_REVIEW": "on"}) == set()


@pytest.mark.parametrize("change, rule", [
    ({"MRS_PAID_GENERATION": None}, "paid_generation_off"),
    ({"MRS_PAID_GENERATION": '"admin"'}, "paid_generation_off"),
    ({"MRS_PAID_GENERATION": "false"}, "paid_generation_off"),
    ({"MRS_PAID_GENERATION": '"on"'}, "paid_generation_off"),
    ({"MRS_FREE_GENERATION": '"all"'}, "free_generation_closed"),
    ({"MRS_FREE_GENERATION": '"admin"'}, "free_generation_closed"),
    ({"MRS_FREE_GENERATION": "false"}, "free_generation_closed"),
])
def test_h_paid_and_free_generation_outside_the_freeze_fail(tmp_path, change, rule):
    assert _failed(tmp_path, change) == {rule}


@pytest.mark.parametrize("literal", ['"off"', '"none"', '"0"', '"no"'])
def test_paid_generation_closed_as_the_application_reads_it_passes(tmp_path, literal):
    assert _failed(tmp_path, {"MRS_PAID_GENERATION": literal}) == set()


# I and J. The commit every encounter records.

@pytest.mark.parametrize("literal", [f'"{COMMIT[:12]}"', f'"{COMMIT}"', f'"{COMMIT[:7]}"', f'"{COMMIT[:12].upper()}"'])
def test_i_the_commit_to_deploy_passes(tmp_path, literal):
    rules = _rules(tmp_path, {"MRS_CODE_VERSION": literal})
    assert rules["code_version"][1], literal


@pytest.mark.parametrize("literal", [None, '""', '"fedcba987654"', '"latest"', '"v0.24.13"', '"0123"'])
def test_j_a_missing_or_different_commit_fails(tmp_path, literal):
    assert _failed(tmp_path, {"MRS_CODE_VERSION": literal}) == {"code_version"}


def test_j_without_the_commit_to_deploy_the_version_cannot_pass(tmp_path):
    assert _failed(tmp_path, commit="not-a-commit") == {"code_version"}


def _head():
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def test_the_default_commit_is_this_checkouts_head(tmp_path):
    rules = _rules(tmp_path, {"MRS_CODE_VERSION": f'"{_head()[:12]}"'}, commit=None, config_path=None)
    assert rules["code_version"][1] and rules["fast_reruns"][1]


def test_the_command_passes_the_frozen_configuration_for_this_checkout(tmp_path, capsys, monkeypatch):
    # The local deployment settings of this machine (the development batch, a pinned case) never reach it.
    monkeypatch.setenv("MRS_DEFAULT_VARIANT", "trauma_hemothorax_41m")
    path = _write(tmp_path, {**PILOT, "MRS_CODE_VERSION": f'"{_head()[:12]}"'})
    assert preflight.main(["--secrets", str(path)]) == 0
    out = capsys.readouterr().out
    assert out.endswith("Configuración del piloto: LISTA.\n") and "FALLA" not in out
    assert "[AVISO] local_environment" in out and "MRS_DEFAULT_VARIANT" in out
    for secret in SECRET_WORDS:
        assert secret not in out


def test_with_secrets_the_local_environment_cannot_hide_the_deployments_offline_setting(tmp_path, capsys,
                                                                                     monkeypatch):
    # Locally MRS_OFFLINE_CASES=1 would win over a TOML boolean; the hosted deployment never receives it.
    monkeypatch.setenv("MRS_OFFLINE_CASES", "1")
    path = _write(tmp_path, {**PILOT, "MRS_CODE_VERSION": f'"{_head()[:12]}"', "MRS_OFFLINE_CASES": "true"})
    assert preflight.main(["--secrets", str(path)]) == 1
    out = capsys.readouterr().out
    assert "[FALLA] offline_cases" in out and "[FALLA] provider_key_withheld" in out


# fastReruns comes from the repository's config.toml and nothing overrides it.

def test_the_repository_config_keeps_fast_reruns_off(tmp_path):
    assert _rules(tmp_path)["fast_reruns"][:2] == (preflight.REQUIRED, True)


def test_fast_reruns_is_read_from_the_commit_to_deploy(tmp_path):
    # 13592e4, where Phase 0 started, had no .streamlit/config.toml: deploying it fails the preflight.
    if preflight.resolve_commit("13592e4") is None:
        pytest.skip("the commit where Phase 0 started is not in this clone")
    rules = _rules(tmp_path, {"MRS_CODE_VERSION": '"13592e4"'}, commit="13592e4", config_path=None)
    assert rules["code_version"][1] and not rules["fast_reruns"][1]


@pytest.mark.parametrize("config", ['[runner]\nfastReruns = true\n', '[runner]\nfastReruns = "false"\n',
                                    '[server]\nheadless = true\n', None])
def test_fast_reruns_not_off_fails(tmp_path, config):
    path = tmp_path / "config.toml"
    if config is not None:
        path.write_text(config, encoding="utf-8")
    text, ready = _run(tmp_path, config_path=path)
    assert not ready and "[FALLA] fast_reruns" in text


def test_an_environment_override_of_fast_reruns_fails(tmp_path):
    assert _failed(tmp_path, environ={"STREAMLIT_RUNNER_FAST_RERUNS": "false"}) == {"fast_reruns"}


# Fail closed, and leave nothing behind.

def test_a_malformed_secrets_file_fails_closed_without_printing_it(tmp_path):
    path = tmp_path / "secrets.toml"
    path.write_text(f'OPENAI_API_KEY = "{KEY}\nMRS_OFFLINE_CASES = "1"\n', encoding="utf-8")
    text, ready = preflight.evaluate([path], ENVIRON, commit=COMMIT)
    assert not ready and "[FALLA] secrets_readable" in text and KEY not in text


def test_a_rule_that_cannot_be_read_fails_closed(tmp_path, monkeypatch):
    import offline_cases

    def broken():
        raise RuntimeError(f"cannot read {KEY}")
    monkeypatch.setattr(offline_cases, "offline_cases_enabled", broken)
    text, ready = _run(tmp_path)
    assert not ready and "[FALLA] offline_cases: no se pudo evaluar (RuntimeError)." in text and KEY not in text


def test_the_evaluation_leaves_the_environment_and_st_secrets_as_they_were(tmp_path):
    import streamlit
    before_environ, before_secrets = dict(os.environ), streamlit.secrets
    _run(tmp_path, {"MRS_OFFLINE_CASES": "true"}, environ={"MRS_DEFAULT_VARIANT": "acs_54m_inferior"})
    assert dict(os.environ) == before_environ and streamlit.secrets is before_secrets


# What the preflight already did (C10-06).

def test_the_default_configuration_with_a_key_is_not_ready(tmp_path):
    text, ready = _run(tmp_path, {"MRS_OFFLINE_CASES": None})
    assert not ready
    assert _failed(tmp_path, {"MRS_OFFLINE_CASES": None}) == {"offline_cases", "provider_key_withheld"}


def test_each_required_rule_fails_on_its_own(tmp_path):
    cases = {
        "auth_mode": {"MRS_AUTH_MODE": '"shared"'},
        "database_url": {"MRS_DATABASE_URL": '"sqlite:///local.sqlite3"'},
        "no_local_sqlite": {"MRS_ALLOW_LOCAL_SQLITE": '"true"'},
        "image_review": {"MRS_IMAGE_REQUIRE_REVIEW": '""'},
        "no_replay_case": {"MRS_REPLAY_CASE": '"saved_run.json"'},
    }
    for rule, change in cases.items():
        assert _failed(tmp_path, change) == {rule}, rule


def test_a_recommendation_warns_and_never_fails(tmp_path):
    text, ready = _run(tmp_path, environ={"MRS_BATCH_STAFF_PASSWORD": "x"})
    assert ready and "[AVISO] no_batch_settings" in text and text.endswith("LISTA.")


def test_secrets_files_are_read_like_the_application_and_win_over_the_environment(tmp_path):
    first = _write(tmp_path, {"MRS_AUTH_MODE": '"shared"', "MRS_OFFLINE_CASES": '"0"'}, "user.toml")
    second = tmp_path / "project.toml"
    second.write_text('MRS_OFFLINE_CASES = "1"\nMRS_AUTH_MODE = "accounts"\n[connections]\nurl = "x"\n',
                      encoding="utf-8")
    view = preflight.load_view([first, second], {"MRS_AUTH_MODE": "shared", "MRS_IMAGE_REQUIRE_REVIEW": "on"})
    assert view.secrets["MRS_AUTH_MODE"] == "accounts" and view.secrets["MRS_OFFLINE_CASES"] == "1"
    rules = {identifier: holds for identifier, _, holds, _ in preflight.checks(view, commit=COMMIT)}
    assert rules["auth_mode"] and rules["offline_cases"] and rules["image_review"]


def test_a_malformed_administrator_hash_fails_without_being_printed(tmp_path):
    text, ready = _run(tmp_path, {"MRS_ADMIN_USERNAME": '"admin"',
                                  "MRS_ADMIN_PASSWORD_HASH": '"plain-password-here"'})
    assert not ready and "plain-password-here" not in text


def test_an_unreachable_database_is_said_by_its_error_class_only():
    [found] = preflight._connection_checks("postgresql://someone:hunter22@127.0.0.1:1/pilot?sslmode=disable")
    identifier, level, holds, message = found
    assert (identifier, level, holds) == ("database_reachable", preflight.REQUIRED, False)
    assert "hunter22" not in message and "Error" in message
