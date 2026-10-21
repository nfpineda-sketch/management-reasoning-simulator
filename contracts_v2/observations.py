"""Observation contract v2 (Phase 1 WP5).

Representational only. It mirrors the Phase-0 observation_snapshot exactly.
It does not compute findings, alter physiology, reinterpret static content,
or change observation-consistency rules.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping

SCHEMA = "observation_contract_v2"
VERSION = 2


class ObservationContractError(RuntimeError):
    """Legacy observation data cannot be represented safely."""


class ObservationContractMismatch(ObservationContractError):
    """The v2 observation shadow differs from the legacy snapshot."""


@dataclass(frozen=True, slots=True)
class ObservationSnapshot:
    payload: dict[str, Any]
    schema: str = SCHEMA
    version: int = VERSION

    @property
    def minute(self):
        return self.payload.get("minute")

    @property
    def arrested(self):
        return self.payload.get("arrested")

    @property
    def arrest_minute(self):
        return self.payload.get("arrest_minute")

    def legacy_payload(self) -> dict[str, Any]:
        return deepcopy(self.payload)

    def as_record(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "version": self.version,
            "observation_snapshot": self.legacy_payload(),
        }


def legacy_projection(turn: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(turn, Mapping):
        raise ObservationContractError(
            f"turn is not a mapping: {type(turn).__name__}"
        )
    snapshot = turn.get("observation_snapshot")
    if snapshot is None:
        snapshot = {}
    if not isinstance(snapshot, Mapping):
        raise ObservationContractError(
            "observation_snapshot is not a mapping: "
            f"{type(snapshot).__name__}"
        )
    return deepcopy(dict(snapshot))


def from_legacy_turn(turn: Mapping[str, Any]) -> ObservationSnapshot:
    return ObservationSnapshot(payload=legacy_projection(turn))


def assert_shadow_equivalent(
    contract: ObservationSnapshot,
    turn: Mapping[str, Any],
) -> None:
    expected = legacy_projection(turn)
    actual = contract.legacy_payload()
    if actual != expected:
        raise ObservationContractMismatch(
            f"observation snapshot differs: v2={actual!r} legacy={expected!r}"
        )


def shadow_from_legacy_turn(turn: Mapping[str, Any]) -> ObservationSnapshot:
    contract = from_legacy_turn(turn)
    assert_shadow_equivalent(contract, turn)
    return contract
