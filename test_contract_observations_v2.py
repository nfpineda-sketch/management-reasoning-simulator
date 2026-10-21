"""Phase 1 WP5: ObservationContract v2 mirrors Phase-0 observation_snapshot."""
from copy import deepcopy
from dataclasses import replace

import pytest

from contracts_v2 import observations as v2


def _turn(**changes):
    turn = {
        "observation_snapshot": {
            "minute": 15,
            "vitals": {"hr": 72, "bp": "118/74", "spo2": 98},
            "mental_status": "Alert",
            "rhythm": "sinus rhythm",
            "arrested": False,
            "arrest_minute": None,
            "static_observables": {
                "history": {"reason": "authored past history"},
            },
            "inconsistencies": [],
            "results": [
                {
                    "name": "potassium",
                    "value": 4.2,
                    "collection_min": 10,
                }
            ],
        }
    }
    turn.update(changes)
    return turn


def test_observation_contract_has_version_and_exact_legacy_payload():
    turn = _turn()
    original = deepcopy(turn)
    contract = v2.from_legacy_turn(turn)

    assert contract.schema == "observation_contract_v2"
    assert contract.version == 2
    assert contract.legacy_payload() == turn["observation_snapshot"]
    assert turn == original


def test_unknown_observation_fields_are_preserved_exactly():
    turn = _turn()
    turn["observation_snapshot"]["future_field"] = {
        "nested": [1, 2, {"x": "y"}],
    }
    contract = v2.from_legacy_turn(turn)
    assert contract.legacy_payload()["future_field"] == {
        "nested": [1, 2, {"x": "y"}],
    }


def test_nested_observation_payload_is_deep_copied():
    turn = _turn()
    contract = v2.from_legacy_turn(turn)

    turn["observation_snapshot"]["vitals"]["hr"] = 999
    turn["observation_snapshot"]["results"][0]["value"] = 99

    assert contract.payload["vitals"]["hr"] == 72
    assert contract.payload["results"][0]["value"] == 4.2

    projected = contract.legacy_payload()
    projected["vitals"]["hr"] = 111
    assert contract.payload["vitals"]["hr"] == 72


def test_missing_observation_snapshot_maps_to_empty_snapshot_without_invention():
    contract = v2.from_legacy_turn({})
    assert contract.legacy_payload() == {}
    assert contract.minute is None
    assert contract.arrested is None


def test_non_mapping_observation_snapshot_is_rejected():
    with pytest.raises(v2.ObservationContractError, match="not a mapping"):
        v2.from_legacy_turn({"observation_snapshot": "bad"})


def test_shadow_validator_detects_seeded_observation_difference():
    turn = _turn()
    contract = v2.from_legacy_turn(turn)
    changed_payload = contract.legacy_payload()
    changed_payload["vitals"]["hr"] = 73
    changed = replace(contract, payload=changed_payload)

    with pytest.raises(v2.ObservationContractMismatch, match="differs"):
        v2.assert_shadow_equivalent(changed, turn)


def test_as_record_wraps_exact_legacy_snapshot_without_mutating_it():
    turn = _turn()
    contract = v2.from_legacy_turn(turn)
    record = contract.as_record()

    assert record["schema"] == "observation_contract_v2"
    assert record["version"] == 2
    assert record["observation_snapshot"] == turn["observation_snapshot"]

def test_ledger_record_shadows_final_observation_before_upsert(monkeypatch):
    import order_pipeline

    turn = {
        "orders": [{
            "order_id": "s:0",
            "submission_id": "s",
            "class": "reassessment",
            "fate": "EXECUTED",
            "reason": "executed",
            "history": [],
            "receipt": None,
            "receipt_shown_elsewhere": False,
            "written_at_min": 0,
            "executed_at_min": 0,
            "timing": {"delay_min": 15},
            "modelled_effect": True,
            "default_applied": None,
            "limitation": None,
        }],
        "decision_time_min": 0,
        "response_time_min": 15,
        "events": [],
        "interrupted": None,
        "observation_snapshot": deepcopy(_turn()["observation_snapshot"]),
        "coverage": {},
    }
    session = {}
    calls = []

    monkeypatch.setattr(order_pipeline, "check", lambda current: [])
    monkeypatch.setattr(order_pipeline, "receipt_lines", lambda current: [])
    monkeypatch.setattr(
        order_pipeline.fate_contracts_v2,
        "shadow_from_legacy_orders",
        lambda orders: calls.append(("fate", deepcopy(orders))),
    )
    monkeypatch.setattr(
        order_pipeline.time_contracts_v2,
        "shadow_from_legacy_turn",
        lambda current: calls.append(("time", deepcopy(current))),
    )
    monkeypatch.setattr(
        order_pipeline.event_contracts_v2,
        "shadow_from_legacy_turn",
        lambda current: calls.append(("events", deepcopy(current))),
    )

    def shadow_observation(current):
        calls.append(("observation", deepcopy(current)))
        return v2.from_legacy_turn(current)

    original_upsert = order_pipeline.upsert

    def tracked_upsert(ledger, orders):
        calls.append(("upsert", deepcopy(orders)))
        return original_upsert(ledger, orders)

    monkeypatch.setattr(
        order_pipeline.observation_contracts_v2,
        "shadow_from_legacy_turn",
        shadow_observation,
    )
    monkeypatch.setattr(order_pipeline, "upsert", tracked_upsert)

    result = order_pipeline.ledger_record(
        session,
        turn,
        lambda kind, text: None,
    )

    assert result is turn
    assert [name for name, _ in calls] == [
        "fate", "time", "events", "observation", "upsert"
    ]
    assert calls[3][1]["observation_snapshot"] == turn["observation_snapshot"]


def test_ledger_record_preserves_phase0_inconsistency_path_without_observation_shadow(monkeypatch):
    import order_pipeline

    turn = {
        "orders": [],
        "observation_snapshot": deepcopy(_turn()["observation_snapshot"]),
        "coverage": {},
    }
    session = {}
    observation_calls = []

    monkeypatch.setattr(
        order_pipeline,
        "check",
        lambda current: ["legacy invariant failed"],
    )
    monkeypatch.setattr(order_pipeline, "receipt_lines", lambda current: [])
    monkeypatch.setattr(
        order_pipeline.observation_contracts_v2,
        "shadow_from_legacy_turn",
        lambda current: observation_calls.append(deepcopy(current)),
    )

    order_pipeline.ledger_record(
        session,
        turn,
        lambda kind, text: None,
    )

    assert observation_calls == []
    assert turn["limitations"][0]["type"] == "engine_inconsistency"
