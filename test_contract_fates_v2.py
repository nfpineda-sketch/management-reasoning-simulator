"""Phase 1 WP2: FateReceipt v2 mirrors the Phase-0 order ledger."""
from copy import deepcopy
from dataclasses import replace

import pytest

from contracts_v2 import fates as v2


def _order(**changes):
    order = {
        "order_id": "submission-1:0",
        "submission_id": "submission-1",
        "class": "fluid",
        "fate": "EXECUTED",
        "reason": "executed",
        "history": [
            {"fate": "EXECUTED", "reason": "executed", "at_min": 7},
        ],
        "receipt": "Order executed.",
        "receipt_shown_elsewhere": False,
        "executed_at_min": 7,
        "modelled_effect": True,
        "default_applied": None,
        "limitation": None,
        "canonical": "normal saline",
        "dose": None,
        "route": "IV",
        "timing": {"immediate": True},
    }
    order.update(changes)
    return order


def test_fate_receipt_v2_has_identity_version_and_exact_legacy_projection():
    order = _order()
    original = deepcopy(order)
    contract = v2.from_legacy_order(order)

    assert contract.schema == "fate_receipt_v2"
    assert contract.version == 2
    assert contract.order_id == "submission-1:0"
    assert contract.submission_id == "submission-1"
    assert contract.action_class == "fluid"
    assert contract.legacy_projection() == v2.legacy_projection(order)
    assert order == original


@pytest.mark.parametrize("fate", [
    "EXECUTED",
    "HELD_CLARIFICATION",
    "HELD_REASONING",
    "RECORDED_NOT_MODELLED",
    "UNRECOGNIZED",
    "SCHEDULED",
    "CANCELLED",
    "DUPLICATE_IGNORED",
    "DUPLICATE_CONFIRMED",
    "TERMINAL_NOT_EXECUTABLE",
])
def test_fate_receipt_v2_preserves_phase0_fate_vocabulary_without_reinterpreting_it(fate):
    order = _order(fate=fate, reason=f"reason:{fate}")
    contract = v2.from_legacy_order(order)
    assert contract.fate == fate
    assert contract.reason == f"reason:{fate}"


def test_nested_history_and_limitation_are_deep_copied():
    order = _order(
        history=[{"fate": "HELD_REASONING", "meta": {"minute": 3}}],
        limitation={"code": "unsupported_future_execution", "meta": {"delay": 30}},
    )
    contract = v2.from_legacy_order(order)

    order["history"][0]["meta"]["minute"] = 999
    order["limitation"]["meta"]["delay"] = 999

    assert contract.history[0]["meta"]["minute"] == 3
    assert contract.limitation["meta"]["delay"] == 30

    projected = contract.legacy_projection()
    projected["history"][0]["meta"]["minute"] = 111
    assert contract.history[0]["meta"]["minute"] == 3


def test_missing_stable_identity_is_rejected():
    with pytest.raises(v2.FateReceiptContractError, match="stable"):
        v2.from_legacy_order({"fate": "EXECUTED"})


def test_missing_fate_is_rejected_instead_of_invented():
    with pytest.raises(v2.FateReceiptContractError, match="no fate"):
        v2.from_legacy_order(_order(fate=None))


def test_shadow_validator_detects_a_seeded_receipt_difference():
    order = _order()
    contract = v2.from_legacy_order(order)
    changed = replace(contract, receipt="different receipt")

    with pytest.raises(v2.FateReceiptMismatch, match="receipt"):
        v2.assert_shadow_equivalent((changed,), [order])


def test_shadow_validator_preserves_order_sequence():
    orders = [
        _order(order_id="submission-1:0", fate="HELD_REASONING"),
        _order(order_id="submission-1:1", fate="EXECUTED"),
    ]
    contracts = v2.shadow_from_legacy_orders(orders)

    assert [c.order_id for c in contracts] == [
        "submission-1:0",
        "submission-1:1",
    ]


def test_receipt_may_be_none_if_legacy_record_has_none():
    order = _order(receipt=None)
    contract = v2.from_legacy_order(order)
    assert contract.receipt is None
    assert contract.legacy_projection()["receipt"] is None

def test_ledger_record_shadows_final_fates_before_upsert(monkeypatch):
    import order_pipeline

    turn = {"orders": [_order()], "coverage": {}}
    session = {}
    calls = []
    events = []

    monkeypatch.setattr(order_pipeline, "check", lambda current: [])
    monkeypatch.setattr(order_pipeline, "receipt_lines", lambda current: ["legacy receipt"])

    def shadow(orders):
        calls.append(("shadow", deepcopy(orders)))
        return ()

    original_upsert = order_pipeline.upsert

    def tracked_upsert(ledger, orders):
        calls.append(("upsert", deepcopy(orders)))
        return original_upsert(ledger, orders)

    monkeypatch.setattr(
        order_pipeline.fate_contracts_v2,
        "shadow_from_legacy_orders",
        shadow,
    )
    monkeypatch.setattr(order_pipeline, "upsert", tracked_upsert)

    result = order_pipeline.ledger_record(
        session,
        turn,
        lambda kind, text: events.append((kind, text)),
    )

    assert result is turn
    assert [name for name, _ in calls] == ["shadow", "upsert"]
    assert calls[0][1] == turn["orders"]
    assert events == [("prototype", "legacy receipt")]
    assert session["order_ledger"][0]["fate"] == "EXECUTED"


def test_ledger_record_preserves_phase0_inconsistency_path_without_shadow(monkeypatch):
    import order_pipeline

    turn = {"orders": [_order(fate=None)], "coverage": {}}
    session = {}
    shadow_calls = []
    events = []

    monkeypatch.setattr(
        order_pipeline,
        "check",
        lambda current: ["order submission-1:0 has no fate"],
    )
    monkeypatch.setattr(order_pipeline, "receipt_lines", lambda current: [])

    monkeypatch.setattr(
        order_pipeline.fate_contracts_v2,
        "shadow_from_legacy_orders",
        lambda orders: shadow_calls.append(deepcopy(orders)),
    )

    order_pipeline.ledger_record(
        session,
        turn,
        lambda kind, text: events.append((kind, text)),
    )

    assert shadow_calls == []
    assert turn["limitations"][0]["type"] == "engine_inconsistency"
    assert events and events[0][0] == "prototype"
    assert session["order_ledger"][0]["fate"] is None
