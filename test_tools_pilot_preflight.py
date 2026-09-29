"""The pilot's preflight says whether a deployment is configured as the pilot, and never a secret (C10-06)."""
import tools_pilot_preflight as preflight

URL = "postgresql://pilot_user:s3cret-pass@db.example.org/pilot?sslmode=require"
PILOT = {"MRS_AUTH_MODE": "accounts", "MRS_DATABASE_URL": URL, "MRS_OFFLINE_CASES": "1",
         "MRS_IMAGE_REQUIRE_REVIEW": "on", "MRS_PAID_GENERATION": "off", "OPENAI_API_KEY": "sk-not-a-real-key",
         "MRS_CODE_VERSION": "abc123"}


def _run(settings):
    text, ready = preflight.report(preflight.checks(settings))
    return text, ready


def test_the_pilot_configuration_is_ready_and_no_secret_is_printed():
    text, ready = _run(PILOT)
    assert ready and "LISTA." in text
    for secret in ("s3cret-pass", "pilot_user", "db.example.org", "sk-not-a-real-key"):
        assert secret not in text


def test_the_default_configuration_with_a_key_is_not_ready():
    settings = {name: value for name, value in PILOT.items() if name != "MRS_OFFLINE_CASES"}
    text, ready = _run(settings)
    assert not ready
    failed = {identifier for identifier, level, holds, _ in preflight.checks(settings)
              if level == preflight.REQUIRED and not holds}
    assert failed == {"offline_cases", "provider_key_withheld"}


def test_each_required_rule_fails_on_its_own():
    cases = {
        "auth_mode": {"MRS_AUTH_MODE": "shared"},
        "database_url": {"MRS_DATABASE_URL": "sqlite:///local.sqlite3"},
        "no_local_sqlite": {"MRS_ALLOW_LOCAL_SQLITE": "true"},
        "image_review": {"MRS_IMAGE_REQUIRE_REVIEW": ""},
        "no_replay_case": {"MRS_REPLAY_CASE": "saved_run.json"},
    }
    for rule, change in cases.items():
        failed = {identifier for identifier, level, holds, _ in preflight.checks({**PILOT, **change})
                  if level == preflight.REQUIRED and not holds}
        assert failed == {rule}, rule


def test_a_recommendation_warns_and_never_fails():
    text, ready = _run({**PILOT, "MRS_PAID_GENERATION": "", "MRS_BATCH_STAFF_PASSWORD": "x"})
    assert ready and "[AVISO] paid_generation_off" in text and "[AVISO] no_batch_settings" in text


def test_secrets_files_are_read_like_the_application_and_win_over_the_environment(tmp_path):
    secrets = tmp_path / "secrets.toml"
    secrets.write_text('MRS_OFFLINE_CASES = "1"\nMRS_AUTH_MODE = "accounts"\n[connections]\nurl = "x"\n')
    settings = preflight.load_settings([secrets], {"MRS_AUTH_MODE": "shared", "MRS_IMAGE_REQUIRE_REVIEW": "on",
                                                   "PATH": "/bin"})
    assert settings["MRS_AUTH_MODE"] == "accounts" and settings["MRS_OFFLINE_CASES"] == "1"
    assert settings["MRS_IMAGE_REQUIRE_REVIEW"] == "on" and "PATH" not in settings and "connections" not in settings


def test_a_malformed_administrator_hash_fails_without_being_printed():
    text, ready = _run({**PILOT, "MRS_ADMIN_USERNAME": "admin", "MRS_ADMIN_PASSWORD_HASH": "plain-password-here"})
    assert not ready and "plain-password-here" not in text


def test_an_unreachable_database_is_said_by_its_error_class_only():
    [found] = preflight._connection_checks("postgresql://someone:hunter22@127.0.0.1:1/pilot?sslmode=disable")
    identifier, level, holds, message = found
    assert (identifier, level, holds) == ("database_reachable", preflight.REQUIRED, False)
    assert "hunter22" not in message and "Error" in message
