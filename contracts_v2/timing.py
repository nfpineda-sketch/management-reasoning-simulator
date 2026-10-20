"""Time contract v2 (Phase 1 WP3).

Representational only. It mirrors the Phase-0 turn clock result and each
order's existing timing metadata without advancing the simulator clock,
scheduling anything, or changing interruption behavior.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping

SCHEMA = "time_contract_v2"
VERSION = 2


class TimeContractError(RuntimeError):
    """A legacy turn cannot be represented safely as TimeContract v2."""


class TimeContractMismatch(TimeContractError):
    """The v2 time shadow differs from the legacy turn projection."""


@dataclass(frozen=True, slots=True)
class OrderTiming:
    order_id: str
    written_at_min: Any
    executed_at_min: Any
    timing: Any

    def as_record(self) -> dict[str, Any]:
        return {
            "order_id": self.order_id,
            "written_at_min": deepcopy(self.written_at_min),
            "executed_at_min": deepcopy(self.executed_at_min),
            "timing": deepcopy(self.timing),
        }


@dataclass(frozen=True, slots=True)
class TurnTime:
    decision_time_min: Any
    response_time_min: Any
    interrupted: Any
    order_timing: tuple[OrderTiming, ...]
    schema: str = SCHEMA
    version: int = VERSION

    @property
    def elapsed_minutes(self):
        if isinstance(self.decision_time_min, (int, float)) and isinstance(
            self.response_time_min, (int, float)
        ):
            return self.response_time_min - self.decision_time_min
        return None

    def legacy_projection(self) -> dict[str, Any]:
        return {
            "decision_time_min": deepcopy(self.decision_time_min),
            "response_time_min": deepcopy(self.response_time_min),
            "interrupted": deepcopy(self.interrupted),
            "order_timing": [item.as_record() for item in self.order_timing],
        }

    def as_record(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "version": self.version,
            "elapsed_minutes": deepcopy(self.elapsed_minutes),
            **self.legacy_projection(),
        }


def legacy_projection(turn: Mapping[str, Any]) -> dict[str, Any]:
    orders = []
    for order in (turn.get("orders") or []):
        if not isinstance(order, Mapping):
            raise TimeContractError(
                f"turn order is not a mapping: {type(order).__name__}"
            )
        orders.append(
            {
                "order_id": str(order.get("order_id") or ""),
                "written_at_min": deepcopy(order.get("written_at_min")),
                "executed_at_min": deepcopy(order.get("executed_at_min")),
                "timing": deepcopy(order.get("timing")),
            }
        )
    return {
        "decision_time_min": deepcopy(turn.get("decision_time_min")),
        "response_time_min": deepcopy(turn.get("response_time_min")),
        "interrupted": deepcopy(turn.get("interrupted")),
        "order_timing": orders,
    }


def from_legacy_turn(turn: Mapping[str, Any]) -> TurnTime:
    if not isinstance(turn, Mapping):
        raise TimeContractError(
            f"turn is not a mapping: {type(turn).__name__}"
        )

    projected = legacy_projection(turn)
    order_timing = tuple(
        OrderTiming(
            order_id=item["order_id"],
            written_at_min=deepcopy(item["written_at_min"]),
            executed_at_min=deepcopy(item["executed_at_min"]),
            timing=deepcopy(item["timing"]),
        )
        for item in projected["order_timing"]
    )

    return TurnTime(
        decision_time_min=deepcopy(projected["decision_time_min"]),
        response_time_min=deepcopy(projected["response_time_min"]),
        interrupted=deepcopy(projected["interrupted"]),
        order_timing=order_timing,
    )


def assert_shadow_equivalent(contract: TurnTime, turn: Mapping[str, Any]) -> None:
    expected = legacy_projection(turn)
    actual = contract.legacy_projection()
    if actual == expected:
        return

    for field in (
        "decision_time_min",
        "response_time_min",
        "interrupted",
        "order_timing",
    ):
        if actual.get(field) != expected.get(field):
            raise TimeContractMismatch(
                f"time contract differs at field {field!r}: "
                f"v2={actual.get(field)!r} legacy={expected.get(field)!r}"
            )
    raise TimeContractMismatch("time contract differs")


def shadow_from_legacy_turn(turn: Mapping[str, Any]) -> TurnTime:
    contract = from_legacy_turn(turn)
    assert_shadow_equivalent(contract, turn)
    return contract
