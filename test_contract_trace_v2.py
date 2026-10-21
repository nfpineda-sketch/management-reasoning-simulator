"""Phase 1 WP6: TraceProvenance v2 mirrors Phase-0 trace mappings."""
from copy import deepcopy
from dataclasses import replace

import pytest

from contracts_v2 import trace as v2


def _trace(**changes):
    trace = {
        "submission": {
            "id": "s1",
            "entry_point": "free_text",
            "raw_text": "Give aspirin.",
        },
        "orders": [
            {
                "order_id": "s1:0",
                "fate": "EXECUTED",
                "receipt": "Executed.",
            }
        ],
        "time_semantics": {
            "decision_time_min": 0,
            "response_time_min": 2,
        },
        "events": [],
        "interrupted": None,
        "observation_snapshot": {
            "minute": 2,
            "vitals": {"hr": 80},
        },
        "limitations": [],
        "action_summaries": [],
        "ledger_problems": [],
        "inconsistencies": [],
        "versions": {
            "code_version": "abc123",
            "ledger_schema": "order_ledger_v1",
        },
    }
    trace.update(changes)
    return trace


def test_trace_contract_has_version_and_exact_legacy_payload():
    trace = _trace()
    original = deepcopy(trace)
    contract = v2.from_legacy_trace(trace)

    assert contract.schema == "trace_provenance_v2"
    assert contract.version == 2
    assert contract.legacy_payload() == trace
    assert trace == original


def test_trace_core_provenance_fields_are_exposed_without_reinterpretation():
    contract = v2.from_legacy_trace(_trace())

    assert contract.submission["id"] == "s1"
    assert contract.orders[0]["order_id"] == "s1:0"
    assert contract.events == []
    assert contract.observation_snapshot["minute"] == 2
    assert contract.limitations == []
    assert contract.versions["ledger_schema"] == "order_ledger_v1"


def test_unknown_trace_fields_are_preserved_exactly():
    trace = _trace(future_provenance={"source": {"kind": "module", "id": "x"}})
    contract = v2.from_legacy_trace(trace)

    assert contract.legacy_payload()["future_provenance"] == {
        "source": {"kind": "module", "id": "x"}
    }


def test_nested_trace_payload_is_deep_copied():
    trace = _trace()
    contract = v2.from_legacy_trace(trace)

    trace["orders"][0]["fate"] = "CHANGED"
    trace["versions"]["code_version"] = "changed"

    assert contract.payload["orders"][0]["fate"] == "EXECUTED"
    assert contract.payload["versions"]["code_version"] == "abc123"

    projected = contract.legacy_payload()
    projected["observation_snapshot"]["vitals"]["hr"] = 999
    assert contract.payload["observation_snapshot"]["vitals"]["hr"] == 80


def test_empty_trace_mapping_is_valid_and_not_filled_in():
    contract = v2.from_legacy_trace({})
    assert contract.legacy_payload() == {}
    assert contract.submission is None
    assert contract.versions is None


def test_non_mapping_trace_is_rejected():
    with pytest.raises(v2.TraceContractError, match="not a mapping"):
        v2.from_legacy_trace(["bad"])


def test_shadow_validator_detects_seeded_limitations_difference():
    trace = _trace()
    contract = v2.from_legacy_trace(trace)
    changed_payload = contract.legacy_payload()
    changed_payload["limitations"] = [{"type": "changed"}]
    changed = replace(contract, payload=changed_payload)

    with pytest.raises(v2.TraceContractMismatch, match="limitations"):
        v2.assert_shadow_equivalent(changed, trace)


def test_as_record_wraps_trace_without_changing_legacy_payload():
    trace = _trace()
    contract = v2.from_legacy_trace(trace)
    record = contract.as_record()

    assert record["schema"] == "trace_provenance_v2"
    assert record["version"] == 2
    assert record["trace"] == trace

def test_app_shadows_completed_phase0_trace_before_append():
    from pathlib import Path

    source = Path("app.py").read_text(encoding="utf-8")

    versions = 'event["versions"] = trace_phase0.versions(st.session_state.state)'
    shadow = 'trace_contracts_v2.shadow_from_legacy_trace(event)'
    append = 'st.session_state.management_trace.append(event)'

    assert versions in source
    assert shadow in source
    assert append in source

    versions_i = source.index(versions)
    shadow_i = source.index(shadow, versions_i)
    append_i = source.index(append, shadow_i)

    assert versions_i < shadow_i < append_i


def test_app_trace_shadow_is_inside_phase0_turn_extension_block():
    from pathlib import Path

    source = Path("app.py").read_text(encoding="utf-8")

    block_start = source.index("    if turn is not None:")
    append_i = source.index("    st.session_state.management_trace.append(event)", block_start)
    block = source[block_start:append_i]

    assert "from contracts_v2 import trace as trace_contracts_v2" in block
    assert "trace_contracts_v2.shadow_from_legacy_trace(event)" in block
