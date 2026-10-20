"""Fate/receipt contract v2 (Phase 1 WP2).

Representational only: adapts the Phase-0 order-ledger record after fate
assignment and projects the exact legacy fate/receipt fields for shadow
comparison. It does not assign fates or create resident-visible receipts.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping

SCHEMA = "fate_receipt_v2"
VERSION = 2

LEGACY_FATE_FIELDS = (
    "order_id",
    "submission_id",
    "class",
    "fate",
    "reason",
    "history",
    "receipt",
    "receipt_shown_elsewhere",
    "executed_at_min",
    "modelled_effect",
    "default_applied",
    "limitation",
)


class FateReceiptContractError(RuntimeError):
    """A legacy ledger record cannot be represented safely as FateReceipt v2."""


class FateReceiptMismatch(FateReceiptContractError):
    """The v2 fate/receipt shadow differs from the legacy ledger projection."""


@dataclass(frozen=True, slots=True)
class FateReceipt:
    order_id: str
    submission_id: str
    action_class: str
    fate: Any
    reason: Any
    history: Any
    receipt: Any
    receipt_shown_elsewhere: Any
    executed_at_min: Any
    modelled_effect: Any
    default_applied: Any
    limitation: Any
    schema: str = SCHEMA
    version: int = VERSION

    def legacy_projection(self) -> dict[str, Any]:
        return {
            "order_id": self.order_id,
            "submission_id": self.submission_id,
            "class": self.action_class,
            "fate": deepcopy(self.fate),
            "reason": deepcopy(self.reason),
            "history": deepcopy(self.history),
            "receipt": deepcopy(self.receipt),
            "receipt_shown_elsewhere": deepcopy(self.receipt_shown_elsewhere),
            "executed_at_min": deepcopy(self.executed_at_min),
            "modelled_effect": deepcopy(self.modelled_effect),
            "default_applied": deepcopy(self.default_applied),
            "limitation": deepcopy(self.limitation),
        }

    def as_record(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "version": self.version,
            **self.legacy_projection(),
        }


def legacy_projection(order: Mapping[str, Any]) -> dict[str, Any]:
    return {field: deepcopy(order.get(field)) for field in LEGACY_FATE_FIELDS}


def from_legacy_order(order: Mapping[str, Any]) -> FateReceipt:
    if not isinstance(order, Mapping):
        raise FateReceiptContractError(
            f"ledger order is not a mapping: {type(order).__name__}"
        )

    order_id = order.get("order_id")
    submission_id = order.get("submission_id")
    if not order_id or not submission_id:
        raise FateReceiptContractError(
            "ledger order has no stable order_id/submission_id"
        )

    if order.get("fate") is None:
        raise FateReceiptContractError(f"ledger order {order_id!r} has no fate")

    return FateReceipt(
        order_id=str(order_id),
        submission_id=str(submission_id),
        action_class=str(order.get("class") or ""),
        fate=deepcopy(order.get("fate")),
        reason=deepcopy(order.get("reason")),
        history=deepcopy(order.get("history")),
        receipt=deepcopy(order.get("receipt")),
        receipt_shown_elsewhere=deepcopy(order.get("receipt_shown_elsewhere")),
        executed_at_min=deepcopy(order.get("executed_at_min")),
        modelled_effect=deepcopy(order.get("modelled_effect")),
        default_applied=deepcopy(order.get("default_applied")),
        limitation=deepcopy(order.get("limitation")),
    )


def from_legacy_orders(orders) -> tuple[FateReceipt, ...]:
    return tuple(from_legacy_order(order) for order in (orders or []))


def assert_shadow_equivalent(contracts: tuple[FateReceipt, ...], orders) -> None:
    legacy = [legacy_projection(order) for order in (orders or [])]
    if len(contracts) != len(legacy):
        raise FateReceiptMismatch(
            f"order count differs: v2={len(contracts)} legacy={len(legacy)}"
        )

    for index, (contract, expected) in enumerate(zip(contracts, legacy)):
        actual = contract.legacy_projection()
        if actual != expected:
            field = next(
                (
                    key
                    for key in LEGACY_FATE_FIELDS
                    if actual.get(key) != expected.get(key)
                ),
                "<unknown>",
            )
            raise FateReceiptMismatch(
                f"order {index} ({contract.order_id}) differs at field {field!r}: "
                f"v2={actual.get(field)!r} legacy={expected.get(field)!r}"
            )


def shadow_from_legacy_orders(orders) -> tuple[FateReceipt, ...]:
    contracts = from_legacy_orders(orders)
    assert_shadow_equivalent(contracts, orders)
    return contracts
