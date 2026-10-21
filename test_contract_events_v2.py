"""Phase 1 WP4: EventInterruption v2 mirrors Phase-0 event state."""
from copy import deepcopy
from dataclasses import replace

import pytest

from contracts_v2 import events as v2


def _turn(**changes):
    turn = {
        "events": [
            {
                "minute": 15,
                "type": "complete_av_block",
                "cause": "natural_history",
                "severity": "critical",
                "preventability": {
                    "class": "not_preventable",
                    "actions": [],
                },
                "interrupted": True,
                "message": "Complete AV block.",
            }
        ],
        "interrupted": {
            "minute": 15,
            "event": "complete_av_block",
            "severity": "critical",
        },
    }
    turn.update(changes)
    return turn


def test_event_contract_has_version_and_exact_legacy_projection():
    turn = _turn()
    original = deepcopy(turn)
    contract = v2.from_legacy_turn(turn)

    assert contract.schema == "event_interruption_v2"
    assert contract.version == 2
    assert contract.legacy_projection() == v2.legacy_projection(turn)
    assert turn == original


def test_event_metadata_is_exposed_without_reinterpretation():
    contract = v2.from_legacy_turn(_turn())
    event = contract.events[0]

    assert event.minute == 15
    assert event.cause == "natural_history"
    assert event.severity == "critical"
    assert event.preventability == {
        "class": "not_preventable",
        "actions": [],
    }
    assert event.interrupted is True


def test_unknown_event_fields_are_preserved_exactly():
    turn = _turn(
        events=[{
            "minute": 7,
            "type": "custom",
            "future_field": {"nested": [1, 2, 3]},
        }]
    )
    contract = v2.from_legacy_turn(turn)
    assert contract.legacy_projection()["events"][0]["future_field"] == {
        "nested": [1, 2, 3]
    }


def test_nested_event_payloads_are_deep_copied():
    turn = _turn()
    contract = v2.from_legacy_turn(turn)

    turn["events"][0]["preventability"]["actions"].append("changed")
    turn["interrupted"]["minute"] = 99

    assert contract.events[0].preventability["actions"] == []
    assert contract.interrupted["minute"] == 15

    projected = contract.legacy_projection()
    projected["events"][0]["preventability"]["actions"].append("also changed")
    assert contract.events[0].preventability["actions"] == []


def test_empty_events_and_no_interruption_are_valid():
    contract = v2.from_legacy_turn({"events": [], "interrupted": None})
    assert contract.events == ()
    assert contract.interrupted is None


def test_non_mapping_event_is_rejected():
    with pytest.raises(v2.EventContractError, match="event 0 is not a mapping"):
        v2.from_legacy_turn({"events": ["not-an-event"]})


def test_shadow_validator_detects_seeded_event_difference():
    turn = _turn()
    contract = v2.from_legacy_turn(turn)
    changed_events = list(contract.events)
    changed_events[0] = v2.EventRecord({
        **changed_events[0].legacy_payload(),
        "severity": "significant",
    })
    changed = replace(contract, events=tuple(changed_events))

    with pytest.raises(v2.EventContractMismatch, match="events"):
        v2.assert_shadow_equivalent(changed, turn)


def test_shadow_validator_detects_seeded_interruption_difference():
    turn = _turn()
    contract = v2.from_legacy_turn(turn)
    changed = replace(
        contract,
        interrupted={**contract.interrupted, "minute": 16},
    )

    with pytest.raises(v2.EventContractMismatch, match="interrupted"):
        v2.assert_shadow_equivalent(changed, turn)

def test_ledger_record_shadows_final_events_before_upsert(monkeypatch):
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
        "events": deepcopy(_turn()["events"]),
        "interrupted": deepcopy(_turn()["interrupted"]),
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

    def shadow_events(current):
        calls.append(("events", deepcopy(current)))
        return v2.from_legacy_turn(current)

    original_upsert = order_pipeline.upsert

    def tracked_upsert(ledger, orders):
        calls.append(("upsert", deepcopy(orders)))
        return original_upsert(ledger, orders)

    monkeypatch.setattr(
        order_pipeline.event_contracts_v2,
        "shadow_from_legacy_turn",
        shadow_events,
    )
    monkeypatch.setattr(order_pipeline, "upsert", tracked_upsert)

    result = order_pipeline.ledger_record(
        session,
        turn,
        lambda kind, text: None,
    )

    assert result is turn
    assert [name for name, _ in calls] == ["fate", "time", "events", "upsert"]
    assert calls[2][1]["events"] == turn["events"]
    assert calls[2][1]["interrupted"] == turn["interrupted"]


def test_ledger_record_preserves_phase0_inconsistency_path_without_event_shadow(monkeypatch):
    import order_pipeline

    turn = {
        "orders": [],
        "events": deepcopy(_turn()["events"]),
        "interrupted": deepcopy(_turn()["interrupted"]),
        "coverage": {},
    }
    session = {}
    event_calls = []

    monkeypatch.setattr(
        order_pipeline,
        "check",
        lambda current: ["legacy invariant failed"],
    )
    monkeypatch.setattr(order_pipeline, "receipt_lines", lambda current: [])
    monkeypatch.setattr(
        order_pipeline.event_contracts_v2,
        "shadow_from_legacy_turn",
        lambda current: event_calls.append(deepcopy(current)),
    )

    order_pipeline.ledger_record(
        session,
        turn,
        lambda kind, text: None,
    )

    assert event_calls == []
    assert turn["limitations"][0]["type"] == "engine_inconsistency"
