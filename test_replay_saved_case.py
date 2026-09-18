"""A saved AI-generated encounter can be played again locally without paying.

After an authorized paid generation, the faculty wanted to play the launched case
themselves. MRS_REPLAY_CASE names the saved run; it works only in offline mode,
checks the case against the executable contract, and never calls a provider.
"""
import json

import pytest

from encounter_generator import generate_encounter
from generated_case import GeneratedCaseError, generate_ai_encounter
from offline_cases import launch_options
from test_generated_case import AuthorClient, clean_base


@pytest.fixture
def saved_run(tmp_path):
    result = generate_ai_encounter("R1-05", clean_base(), client=AuthorClient(), seed=7)
    path = tmp_path / "run.json"
    path.write_text(json.dumps({"outcome": "LAUNCHED", "presentation": result["presentation"],
                                "state": result["state"]}, default=str))
    return path, result


def test_offline_mode_replays_the_saved_case_without_a_key(monkeypatch, saved_run):
    path, original = saved_run
    monkeypatch.setenv("MRS_OFFLINE_CASES", "1")
    monkeypatch.setenv("MRS_REPLAY_CASE", str(path))
    options, scene_key = launch_options("sk-should-not-be-used")
    assert scene_key == "" and options["api_key"] == "" and options["generation_mode"] == "replay"
    replayed = generate_encounter("R1-05", clean_base(), **options)
    assert replayed["state"]["case_id"] == original["state"]["case_id"]
    assert replayed["state"]["encounter_spec"] == json.loads(json.dumps(original["state"]["encounter_spec"], default=str))
    assert replayed["presentation"] == original["presentation"] and replayed["source"] == "replay"


def test_replay_is_ignored_outside_offline_mode(monkeypatch, saved_run):
    monkeypatch.delenv("MRS_OFFLINE_CASES", raising=False)
    monkeypatch.setenv("MRS_REPLAY_CASE", str(saved_run[0]))
    assert launch_options("key") == ({"api_key": "key"}, "key")


def test_a_different_challenge_is_refused_with_a_clear_message(monkeypatch, saved_run):
    monkeypatch.setenv("MRS_OFFLINE_CASES", "1")
    monkeypatch.setenv("MRS_REPLAY_CASE", str(saved_run[0]))
    options, _ = launch_options("")
    with pytest.raises(GeneratedCaseError, match="belongs to challenge R1-05"):
        generate_encounter("R3-01", clean_base(), **options)


def test_a_record_without_the_launched_state_is_refused(monkeypatch, tmp_path):
    path = tmp_path / "failed.json"
    path.write_text(json.dumps({"outcome": "FAILED"}))
    monkeypatch.setenv("MRS_OFFLINE_CASES", "1")
    monkeypatch.setenv("MRS_REPLAY_CASE", str(path))
    with pytest.raises(ValueError, match="launched encounter state"):
        launch_options("")


def test_a_tampered_case_no_longer_meeting_the_contract_is_refused(monkeypatch, saved_run, tmp_path):
    record = json.loads(saved_run[0].read_text())
    record["state"]["encounter_spec"]["clinical_case"]["engine"]["core_profile"]["initial_hidden"]["effective_volume"] = 7
    path = tmp_path / "tampered.json"
    path.write_text(json.dumps(record))
    monkeypatch.setenv("MRS_OFFLINE_CASES", "1")
    monkeypatch.setenv("MRS_REPLAY_CASE", str(path))
    options, _ = launch_options("")
    with pytest.raises(GeneratedCaseError, match="executable contract"):
        generate_encounter("R1-05", clean_base(), **options)
