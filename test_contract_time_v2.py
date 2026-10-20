"""Phase 1 WP3: TimeContract v2 mirrors Phase-0 turn timing."""
from copy import deepcopy
from dataclasses import replace

import pytest

from contracts_v2 import timing as v2


def _turn(**changes):
    turn = {
        "decision_time_min": 10,
        "response_time_min": 25,
        "interrupted": None,
        "orders": [
            {
                "order_id": "submission-1:0",
                "written_at_min": 10,
                "executed_at_min": 10,
                "timing": None,
                "fate": "EXECUTED",
            },
            {
                "order_id": "submission-1:1",
                "written_at_min": 10,
                "executed_at_min": 25,
                "timing": {"delay_min": 15},
                "fate": "EXECUTED",
            },
        ],
    }
    turn.update(changes)
    return turn


def test_time_contract_has_version_exact_projection_and_elapsed_minutes():
    turn = _turn()
    original = deepcopy(turn)
    contract = v2.from_legacy_turn(turn)

    assert contract.schema == "time_contract_v2"
    assert contract.version == 2
    assert contract.decision_time_min == 10
    assert contract.response_time_min == 25
    assert contract.elapsed_minutes == 15
    assert contract.legacy_projection() == v2.legacy_projection(turn)
    assert turn == original


@pytest.mark.parametrize("timing", [
    {"delay_min": 15},
    {"wait": True, "delay_min": 20},
    {"immediate": True},
    {"after_result": "troponin"},
    None,
])
def test_order_timing_is_preserved_without_reinterpretation(timing):
    turn = _turn(
        orders=[{
            "order_id": "s:0",
            "written_at_min": 4,
            "executed_at_min": 9,
            "timing": timing,
        }]
    )
    contract = v2.from_legacy_turn(turn)
    assert contract.order_timing[0].timing == timing


def test_interruption_payload_is_preserved_exactly_and_deep_copied():
    turn = _turn(
        response_time_min=18,
        interrupted={
            "minute": 18,
            "event": "complete AV block",
            "severity": "critical",
            "details": {"bp": "83/54"},
        },
    )
    contract = v2.from_legacy_turn(turn)

    turn["interrupted"]["details"]["bp"] = "changed"
    assert contract.interrupted["details"]["bp"] == "83/54"

    projected = contract.legacy_projection()
    projected["interrupted"]["details"]["bp"] = "also changed"
    assert contract.interrupted["details"]["bp"] == "83/54"


def test_elapsed_minutes_is_derived_not_served_back_to_legacy():
    turn = _turn(decision_time_min=7, response_time_min=9)
    contract = v2.from_legacy_turn(turn)

    assert contract.elapsed_minutes == 2
    assert "elapsed_minutes" not in contract.legacy_projection()
    assert contract.as_record()["elapsed_minutes"] == 2


def test_none_clock_values_are_mirrored_not_invented():
    turn = _turn(decision_time_min=None, response_time_min=None)
    contract = v2.from_legacy_turn(turn)
    assert contract.elapsed_minutes is None
    assert contract.decision_time_min is None
    assert contract.response_time_min is None


def test_non_mapping_order_is_rejected():
    turn = _turn(orders=["not-an-order"])
    with pytest.raises(v2.TimeContractError, match="not a mapping"):
        v2.from_legacy_turn(turn)


def test_shadow_validator_detects_seeded_clock_difference():
    turn = _turn()
    contract = v2.from_legacy_turn(turn)
    changed = replace(contract, response_time_min=26)

    with pytest.raises(v2.TimeContractMismatch, match="response_time_min"):
        v2.assert_shadow_equivalent(changed, turn)


def test_shadow_validator_detects_seeded_interruption_difference():
    turn = _turn(interrupted={"minute": 18, "event": "critical"})
    contract = v2.from_legacy_turn(turn)
    changed = replace(contract, interrupted={"minute": 19, "event": "critical"})

    with pytest.raises(v2.TimeContractMismatch, match="interrupted"):
        v2.assert_shadow_equivalent(changed, turn)

def test_ledger_record_shadows_final_time_before_upsert(monkeypatch):
    import order_pipeline

    turn = _turn()
    session = {}
    calls = []

    monkeypatch.setattr(order_pipeline, "check", lambda current: [])
    monkeypatch.setattr(order_pipeline, "receipt_lines", lambda current: [])
    monkeypatch.setattr(
        order_pipeline.fate_contracts_v2,
        "shadow_from_legacy_orders",
        lambda orders: calls.append(("fate", deepcopy(orders))),
    )

    def shadow_time(current):
        calls.append(("time", deepcopy(current)))
        return v2.from_legacy_turn(current)

    original_upsert = order_pipeline.upsert

    def tracked_upsert(ledger, orders):
        calls.append(("upsert", deepcopy(orders)))
        return original_upsert(ledger, orders)

    monkeypatch.setattr(
        order_pipeline.time_contracts_v2,
        "shadow_from_legacy_turn",
        shadow_time,
    )
    monkeypatch.setattr(order_pipeline, "upsert", tracked_upsert)

    result = order_pipeline.ledger_record(
        session,
        turn,
        lambda kind, text: None,
    )

    assert result is turn
    assert [name for name, _ in calls] == ["fate", "time", "upsert"]
    assert calls[1][1]["decision_time_min"] == 10
    assert calls[1][1]["response_time_min"] == 25
    assert calls[1][1]["interrupted"] is None
    assert session["order_ledger"][1]["timing"] == {"delay_min": 15}


def test_ledger_record_preserves_phase0_inconsistency_path_without_time_shadow(monkeypatch):
    import order_pipeline

    turn = _turn()
    session = {}
    time_calls = []

    monkeypatch.setattr(
        order_pipeline,
        "check",
        lambda current: ["legacy invariant failed"],
    )
    monkeypatch.setattr(order_pipeline, "receipt_lines", lambda current: [])
    monkeypatch.setattr(
        order_pipeline.time_contracts_v2,
        "shadow_from_legacy_turn",
        lambda current: time_calls.append(deepcopy(current)),
    )

    order_pipeline.ledger_record(
        session,
        turn,
        lambda kind, text: None,
    )

    assert time_calls == []
    assert turn["limitations"][0]["type"] == "engine_inconsistency"
