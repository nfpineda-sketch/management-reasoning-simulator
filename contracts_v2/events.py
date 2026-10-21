"""Event/interruption contract v2 (Phase 1 WP4).

Representational only. It mirrors the Phase-0 event payloads and the turn's
interruption payload without changing event generation, severity policy,
preventability, or clock interruption behavior.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping

SCHEMA = "event_interruption_v2"
VERSION = 2


class EventContractError(RuntimeError):
    """Legacy event/interruption data cannot be represented safely."""


class EventContractMismatch(EventContractError):
    """The v2 event shadow differs from the legacy turn projection."""


@dataclass(frozen=True, slots=True)
class EventRecord:
    payload: dict[str, Any]

    @property
    def minute(self):
        return self.payload.get("minute")

    @property
    def cause(self):
        return self.payload.get("cause")

    @property
    def severity(self):
        return self.payload.get("severity")

    @property
    def preventability(self):
        return self.payload.get("preventability")

    @property
    def interrupted(self):
        return self.payload.get("interrupted")

    def legacy_payload(self) -> dict[str, Any]:
        return deepcopy(self.payload)


@dataclass(frozen=True, slots=True)
class EventInterruption:
    events: tuple[EventRecord, ...]
    interrupted: Any
    schema: str = SCHEMA
    version: int = VERSION

    def legacy_projection(self) -> dict[str, Any]:
        return {
            "events": [event.legacy_payload() for event in self.events],
            "interrupted": deepcopy(self.interrupted),
        }

    def as_record(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "version": self.version,
            **self.legacy_projection(),
        }


def legacy_projection(turn: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(turn, Mapping):
        raise EventContractError(
            f"turn is not a mapping: {type(turn).__name__}"
        )
    events = []
    for index, event in enumerate(turn.get("events") or []):
        if not isinstance(event, Mapping):
            raise EventContractError(
                f"turn event {index} is not a mapping: {type(event).__name__}"
            )
        events.append(deepcopy(dict(event)))
    return {
        "events": events,
        "interrupted": deepcopy(turn.get("interrupted")),
    }


def from_legacy_turn(turn: Mapping[str, Any]) -> EventInterruption:
    projected = legacy_projection(turn)
    return EventInterruption(
        events=tuple(EventRecord(deepcopy(event)) for event in projected["events"]),
        interrupted=deepcopy(projected["interrupted"]),
    )


def assert_shadow_equivalent(
    contract: EventInterruption,
    turn: Mapping[str, Any],
) -> None:
    expected = legacy_projection(turn)
    actual = contract.legacy_projection()
    if actual == expected:
        return
    for field in ("events", "interrupted"):
        if actual.get(field) != expected.get(field):
            raise EventContractMismatch(
                f"event contract differs at field {field!r}: "
                f"v2={actual.get(field)!r} legacy={expected.get(field)!r}"
            )
    raise EventContractMismatch("event contract differs")


def shadow_from_legacy_turn(turn: Mapping[str, Any]) -> EventInterruption:
    contract = from_legacy_turn(turn)
    assert_shadow_equivalent(contract, turn)
    return contract
