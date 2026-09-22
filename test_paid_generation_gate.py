"""Sharing the app's URL must not share the card.

Faculty decision B1, 2026-09-23: for the demonstration, encounters start from
saved validated cases and only an administrator may start one that pays a
provider. Offline mode still overrides everything, so a replay stays free.
"""
import pytest

import offline_cases


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    for name in ("MRS_OFFLINE_CASES", "MRS_PAID_GENERATION", "MRS_REPLAY_CASE"):
        monkeypatch.delenv(name, raising=False)


def test_without_the_switch_nothing_changes(monkeypatch):
    assert offline_cases.paid_generation_allowed("resident") is True
    assert offline_cases.launch_options("a-key", "resident") == ({"api_key": "a-key"}, "a-key")


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
