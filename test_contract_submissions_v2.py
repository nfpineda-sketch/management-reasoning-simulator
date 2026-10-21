"""Phase 1 WP7: SubmissionContract v2 mirrors Phase-0 submission-log entries."""
from copy import deepcopy
from dataclasses import replace

import pytest

from contracts_v2 import submissions as v2


def _entries():
    return [
        {
            "id": "abc123",
            "form_id": "abc123",
            "raw_text": "Give aspirin.",
            "entry_point": "free_text",
            "received_at": "2026-10-20T00:00:00Z",
            "received_at_min": 4,
            "status": "received",
            "duplicates": 0,
            "retries": 0,
        },
        {
            "id": "parent:new",
            "form_id": None,
            "raw_text": "Also give 500 mL LR.",
            "entry_point": "free_text",
            "derived_from": "parent",
            "received_at": "2026-10-20T00:01:00Z",
            "received_at_min": 5,
            "status": "processing",
            "duplicates": 1,
            "retries": 1,
            "saved_before_run": True,
            "started_at": "2026-10-20T00:01:01Z",
            "started_at_min": 5,
        },
    ]


def test_submission_contract_has_version_and_exact_legacy_projection():
    entries = _entries()
    original = deepcopy(entries)

    contract = v2.from_legacy_entries(entries)

    assert contract.schema == "submission_contract_v2"
    assert contract.version == 2
    assert contract.legacy_projection() == entries
    assert entries == original


def test_submission_entry_exposes_phase0_identity_and_state_without_reinterpretation():
    contract = v2.from_legacy_entries(_entries())
    first, second = contract.entries

    assert first.submission_id == "abc123"
    assert first.form_id == "abc123"
    assert first.raw_text == "Give aspirin."
    assert first.entry_point == "free_text"
    assert first.status == "received"
    assert first.duplicates == 0
    assert first.retries == 0
    assert first.saved_before_run is None

    assert second.submission_id == "parent:new"
    assert second.status == "processing"
    assert second.saved_before_run is True


def test_unknown_submission_fields_are_preserved_exactly():
    entries = _entries()
    entries[0]["future_field"] = {"nested": [1, {"x": "y"}]}

    contract = v2.from_legacy_entries(entries)

    assert contract.entries[0].legacy_payload()["future_field"] == {
        "nested": [1, {"x": "y"}]
    }


def test_submission_entries_are_deep_copied():
    entries = _entries()
    contract = v2.from_legacy_entries(entries)

    entries[0]["raw_text"] = "CHANGED"
    entries[1]["future_nested"] = {"x": [1, 2]}

    assert contract.entries[0].raw_text == "Give aspirin."
    assert "future_nested" not in contract.entries[1].payload

    projected = contract.legacy_projection()
    projected[0]["status"] = "changed"
    assert contract.entries[0].status == "received"


def test_empty_submission_log_is_valid_and_not_filled_in():
    contract = v2.from_legacy_entries([])
    assert contract.legacy_projection() == []
    assert contract.entries == ()


def test_non_mapping_submission_entry_is_rejected():
    with pytest.raises(v2.SubmissionContractError, match="entry 1"):
        v2.from_legacy_entries([{"id": "ok"}, "bad"])


def test_shadow_validator_detects_seeded_status_difference():
    entries = _entries()
    contract = v2.from_legacy_entries(entries)
    changed_entry = replace(
        contract.entries[0],
        payload={**contract.entries[0].legacy_payload(), "status": "processed"},
    )
    changed = replace(
        contract,
        entries=(changed_entry,) + contract.entries[1:],
    )

    with pytest.raises(v2.SubmissionContractMismatch, match="differs"):
        v2.assert_shadow_equivalent(changed, entries)


def test_as_record_wraps_exact_submission_log_without_mutating_it():
    entries = _entries()
    contract = v2.from_legacy_entries(entries)
    record = contract.as_record()

    assert record["schema"] == "submission_contract_v2"
    assert record["version"] == 2
    assert record["submission_log"] == entries

def test_app_shadows_submission_log_after_recover_write_ahead_before_processing():
    from pathlib import Path

    source = Path("app.py").read_text(encoding="utf-8")

    recover = "_submission_guard.recover(st.session_state, _SESSION_FIELDS)"
    write_ahead = "_submission_guard.write_ahead(st.session_state, lambda: _write_session(ACCOUNT_CONTEXT))"
    shadow = "submission_contracts_v2.shadow_from_legacy_entries(_submission_guard._entries(st.session_state))"
    fast_path = "_FAST_PENDING_SUBMISSION = _submission_guard.fast_path(st.session_state)"

    recover_i = source.index(recover)
    write_i = source.index(write_ahead, recover_i)
    shadow_i = source.index(shadow, write_i)
    fast_i = source.index(fast_path, shadow_i)

    assert recover_i < write_i < shadow_i < fast_i


def test_rerun_app_shadows_processed_submission_before_save():
    from pathlib import Path

    source = Path("app.py").read_text(encoding="utf-8")
    start = source.index("def rerun_app():")
    stop = source.index("def _capture_submission", start)
    block = source[start:stop]

    finish = "submission_guard.finish(st.session_state)"
    shadow = "submission_contracts_v2.shadow_from_legacy_entries(submission_guard._entries(st.session_state))"
    save = "save_session(context)"

    finish_i = block.index(finish)
    shadow_i = block.index(shadow, finish_i)
    save_i = block.index(save, shadow_i)

    assert finish_i < shadow_i < save_i


def test_phase0_submission_transition_helpers_still_own_all_mutation():
    from pathlib import Path

    source = Path("app.py").read_text(encoding="utf-8")
    assert "submission_contracts_v2" in source

    # WP7 shadow may inspect the log, but it must not write submission state.
    forbidden = (
        "submission_contracts_v2.capture",
        "submission_contracts_v2.write_ahead",
        "submission_contracts_v2.begin",
        "submission_contracts_v2.finish",
        "submission_contracts_v2.recover",
    )
    assert not any(item in source for item in forbidden)
