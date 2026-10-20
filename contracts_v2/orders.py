"""Order/action contract v2 (Phase 1 WP1).

The frozen reader still returns its existing dictionaries. The Phase 0 order
pipeline first applies its existing safe defaults and stable ledger tags, then
this module adapts each action into a typed, versioned contract in shadow.

WP1 deliberately does not serve the v2 object to the engine. ``fields`` is an
exact deep-copied image of the payload the v1 path already sends after stripping
ledger-only underscore keys.
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

SCHEMA = "order_action_v2"
VERSION = 2


class OrderContractError(RuntimeError):
    """The reader/pipeline did not provide a shape the v2 contract can represent."""


class OrderContractMismatch(OrderContractError):
    """The shadow v2 payload differs from what the legacy engine would receive."""


@dataclass(frozen=True, slots=True)
class OrderAction:
    """One reader action plus stable identity and exact engine-facing fields."""

    order_id: str
    submission_id: str
    action_class: str
    fields: dict[str, Any]
    schema: str = SCHEMA
    version: int = VERSION

    def engine_payload(self) -> dict[str, Any]:
        return deepcopy(self.fields)

    def as_record(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "version": self.version,
            "order_id": self.order_id,
            "submission_id": self.submission_id,
            "class": self.action_class,
            "fields": deepcopy(self.fields),
        }


def _action_class(action: Mapping[str, Any]) -> str:
    kind = action.get("type")
    if kind == "reassessment":
        return "reassessment"
    if kind == "clarification" and action.get("unrecognized_text"):
        return "unrecognized"
    if kind == "clarification":
        return "clarification"
    return str(kind or "")


def _engine_fields(action: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: deepcopy(value)
        for key, value in action.items()
        if not str(key).startswith("_")
    }


def from_reader_action(action: Mapping[str, Any], *, submission_id: str, index: int) -> OrderAction:
    if not isinstance(action, Mapping):
        raise OrderContractError(f"reader action {index} is not a mapping: {type(action).__name__}")
    order_id = action.get("_order_id")
    tagged_submission = action.get("_submission_id")
    if not order_id or not tagged_submission:
        raise OrderContractError(
            f"reader action {index} has no stable ledger identity; v2 must be built after order_ledger.tag"
        )
    # A parsed bundle may legitimately carry forward an action that was
    # originally written in an earlier submission (for example a held order
    # released by a reasoning follow-up).  The ledger tag is the authoritative
    # stable identity; the current open_turn submission is context, not a
    # requirement that every action be newly authored in this turn.
    return OrderAction(
        order_id=str(order_id),
        submission_id=str(tagged_submission),
        action_class=_action_class(action),
        fields=_engine_fields(action),
    )


def from_parsed(parsed: Mapping[str, Any], *, submission_id: str) -> tuple[OrderAction, ...]:
    actions = (parsed or {}).get("actions") or []
    contracts = []
    for index, action in enumerate(actions):
        if not isinstance(action, Mapping):
            raise OrderContractError(f"reader action {index} is not a mapping: {type(action).__name__}")
        contracts.append(from_reader_action(action, submission_id=submission_id, index=index))
    return tuple(contracts)


def legacy_engine_payloads(parsed: Mapping[str, Any]) -> list[dict[str, Any]]:
    payloads = []
    for index, action in enumerate((parsed or {}).get("actions") or []):
        if not isinstance(action, Mapping):
            raise OrderContractError(f"reader action {index} is not a mapping: {type(action).__name__}")
        payloads.append(_engine_fields(action))
    return payloads


def assert_shadow_equivalent(contracts: tuple[OrderAction, ...], parsed: Mapping[str, Any]) -> None:
    legacy = legacy_engine_payloads(parsed)
    if len(contracts) != len(legacy):
        raise OrderContractMismatch(
            f"action count differs: v2={len(contracts)} legacy={len(legacy)}"
        )
    for index, (contract, expected) in enumerate(zip(contracts, legacy)):
        actual = contract.engine_payload()
        if actual != expected:
            keys = sorted(set(actual) | set(expected))
            field = next((key for key in keys if actual.get(key) != expected.get(key)), "<unknown>")
            raise OrderContractMismatch(
                f"action {index} ({contract.order_id}) differs at field {field!r}: "
                f"v2={actual.get(field)!r} legacy={expected.get(field)!r}"
            )


def shadow_from_reader(parsed: Mapping[str, Any], *, submission_id: str) -> tuple[OrderAction, ...]:
    contracts = from_parsed(parsed, submission_id=submission_id)
    assert_shadow_equivalent(contracts, parsed)
    return contracts
