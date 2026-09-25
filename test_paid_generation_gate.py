"""Sharing the app's URL must not share the card.

Faculty decision B1, 2026-09-23: for the demonstration, encounters start from
saved validated cases and only an administrator may start one that pays a
provider. Offline mode still overrides everything, so a replay stays free.
"""
import pytest

import offline_cases


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    for name in ("MRS_OFFLINE_CASES", "MRS_PAID_GENERATION", "MRS_REPLAY_CASE", "MRS_FREE_GENERATION"):
        monkeypatch.delenv(name, raising=False)


def test_without_the_switch_nothing_changes(monkeypatch):
    assert offline_cases.paid_generation_allowed("resident") is True
    assert offline_cases.launch_options("a-key", "admin") == ({"api_key": "a-key"}, "a-key")


def test_free_generation_stays_in_the_administrator_s_sandbox(monkeypatch):
    """Faculty instruction of 2026-09-25, for the stages of the case catalogue:
    everyone else starts a bank case, and keeps the patient's picture."""
    assert offline_cases.free_generation_allowed("admin") is True
    for role in ("resident", "faculty", None, ""):
        assert offline_cases.free_generation_allowed(role) is False
        assert offline_cases.launch_options("a-key", role) == ({"generation_mode": "authored", "api_key": ""},
                                                               "a-key")


def test_a_saved_case_is_what_a_non_administrator_gets_when_one_is_configured(monkeypatch, tmp_path):
    record = tmp_path / "saved.json"
    record.write_text('{"state": {"encounter_spec": {"clinical_case": {}}}}')
    monkeypatch.setenv("MRS_REPLAY_CASE", str(record))
    options, scene_key = offline_cases.launch_options("a-key", "resident")
    assert options["generation_mode"] == "replay" and options["api_key"] == ""
    assert scene_key == "a-key"


@pytest.mark.parametrize("value", ["all", "everyone", "ALL"])
def test_reopening_free_generation_takes_an_explicit_value(monkeypatch, value):
    monkeypatch.setenv("MRS_FREE_GENERATION", value)
    assert offline_cases.free_generation_allowed("resident") is True
    assert offline_cases.launch_options("a-key", "resident") == ({"api_key": "a-key"}, "a-key")


def test_free_generation_never_opens_what_the_paid_rule_closes(monkeypatch):
    monkeypatch.setenv("MRS_FREE_GENERATION", "all")
    monkeypatch.setenv("MRS_PAID_GENERATION", "admin")
    assert offline_cases.free_generation_allowed("resident") is False
    assert offline_cases.launch_options("a-key", "resident") == ({"generation_mode": "authored", "api_key": ""}, "")
    monkeypatch.setenv("MRS_OFFLINE_CASES", "1")
    assert offline_cases.free_generation_allowed("admin") is False


@pytest.mark.parametrize("role, allowed", [("admin", True), ("faculty", False),
                                           ("resident", False), (None, False), ("", False)])
def test_admin_only_lets_the_administrator_through(monkeypatch, role, allowed):
    monkeypatch.setenv("MRS_PAID_GENERATION", "admin")
    assert offline_cases.paid_generation_allowed(role) is allowed


@pytest.mark.parametrize("value", ["none", "off", "0", "false", "no"])
def test_it_can_be_closed_to_everyone(monkeypatch, value):
    monkeypatch.setenv("MRS_PAID_GENERATION", value)
    assert offline_cases.paid_generation_allowed("admin") is False


def test_someone_who_may_not_generate_gets_an_authored_case(monkeypatch):
    monkeypatch.setenv("MRS_PAID_GENERATION", "admin")
    options, scene_key = offline_cases.launch_options("a-key", "resident")
    assert options == {"generation_mode": "authored", "api_key": ""}
    assert scene_key == ""


def test_a_saved_case_is_served_when_one_is_configured(monkeypatch, tmp_path):
    record = tmp_path / "saved.json"
    record.write_text('{"state": {"encounter_spec": {"clinical_case": {}}}}')
    monkeypatch.setenv("MRS_PAID_GENERATION", "admin")
    monkeypatch.setenv("MRS_REPLAY_CASE", str(record))
    options, scene_key = offline_cases.launch_options("a-key", "resident")
    assert options["generation_mode"] == "replay" and options["api_key"] == ""
    assert scene_key == ""


def test_the_administrator_still_generates(monkeypatch, tmp_path):
    monkeypatch.setenv("MRS_PAID_GENERATION", "admin")
    assert offline_cases.launch_options("a-key", "admin") == ({"api_key": "a-key"}, "a-key")


def test_offline_mode_overrides_the_administrator(monkeypatch):
    monkeypatch.setenv("MRS_OFFLINE_CASES", "1")
    monkeypatch.setenv("MRS_PAID_GENERATION", "admin")
    assert offline_cases.paid_generation_allowed("admin") is False
    options, scene_key = offline_cases.launch_options("a-key", "admin")
    assert options["api_key"] == "" and scene_key == ""


def test_the_replay_record_still_needs_offline_by_default(monkeypatch, tmp_path):
    record = tmp_path / "saved.json"
    record.write_text('{"state": {"encounter_spec": {"clinical_case": {}}}}')
    monkeypatch.setenv("MRS_REPLAY_CASE", str(record))
    assert offline_cases.replay_record() is None
    assert offline_cases.replay_record(require_offline=False) is not None


def test_the_pinned_variant_is_the_case_an_authored_launch_opens_on(monkeypatch):
    """MRS_DEFAULT_VARIANT, the companion of MRS_DEFAULT_CHALLENGE.

    Without it each restart drew a new variant, so a defect found in one case
    could not be re-examined after fixing it (2026-09-22).
    """
    import offline_cases
    monkeypatch.setenv("MRS_OFFLINE_CASES", "1")
    monkeypatch.delenv("MRS_REPLAY_CASE", raising=False)

    monkeypatch.delenv("MRS_DEFAULT_VARIANT", raising=False)
    options, scene = offline_cases.launch_options("sk-live-key")
    assert "variant_id" not in options and options["api_key"] == "" and scene == ""

    monkeypatch.setenv("MRS_DEFAULT_VARIANT", "acs_48m_wellens")
    options, _ = offline_cases.launch_options("sk-live-key")
    assert options["variant_id"] == "acs_48m_wellens"
    assert options["api_key"] == ""          # pinning a case is not a way to pay

    # An identifier that is not in the bank is a typo in a local convenience,
    # not a reason to refuse the launch.
    monkeypatch.setenv("MRS_DEFAULT_VARIANT", "acs_48m_wellens_typo")
    assert "variant_id" not in offline_cases.launch_options("")[0]


def test_a_pinned_variant_reaches_the_encounter_it_names(monkeypatch):
    from encounter_generator import generate_encounter
    monkeypatch.setenv("MRS_OFFLINE_CASES", "1")
    monkeypatch.setenv("MRS_DEFAULT_VARIANT", "acs_48m_wellens")
    import offline_cases
    options, _ = offline_cases.launch_options("")
    base = {"sim_time": 0, "hidden": {}, "treatments": {}}
    generated = generate_encounter("R2-02", base, **options)
    assert generated["state"]["encounter_spec"]["clinical_case"]["id"] == "acs_48m_wellens"
