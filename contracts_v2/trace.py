"""Trace/provenance contract v2 (Phase 1 WP6).

Representational only. It mirrors an existing Phase-0 trace/provenance mapping
exactly. It does not add causal claims, alter analysis guards, or manufacture
missing provenance.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping

SCHEMA = "trace_provenance_v2"
VERSION = 2


class TraceContractError(RuntimeError):
    """Legacy trace/provenance data cannot be represented safely."""


class TraceContractMismatch(TraceContractError):
    """The v2 trace shadow differs from the legacy trace mapping."""


@dataclass(frozen=True, slots=True)
class TraceProvenance:
    payload: dict[str, Any]
    schema: str = SCHEMA
    version: int = VERSION

    @property
    def submission(self):
        return deepcopy(self.payload.get("submission"))

    @property
    def orders(self):
        return deepcopy(self.payload.get("orders"))

    @property
    def events(self):
        return deepcopy(self.payload.get("events"))

    @property
    def observation_snapshot(self):
        return deepcopy(self.payload.get("observation_snapshot"))

    @property
    def limitations(self):
        return deepcopy(self.payload.get("limitations"))

    @property
    def versions(self):
        return deepcopy(self.payload.get("versions"))

    def legacy_payload(self) -> dict[str, Any]:
        return deepcopy(self.payload)

    def as_record(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "version": self.version,
            "trace": self.legacy_payload(),
        }


def from_legacy_trace(trace: Mapping[str, Any]) -> TraceProvenance:
    if not isinstance(trace, Mapping):
        raise TraceContractError(
            f"trace is not a mapping: {type(trace).__name__}"
        )
    return TraceProvenance(payload=deepcopy(dict(trace)))


def assert_shadow_equivalent(
    contract: TraceProvenance,
    trace: Mapping[str, Any],
) -> None:
    if not isinstance(trace, Mapping):
        raise TraceContractError(
            f"trace is not a mapping: {type(trace).__name__}"
        )
    expected = deepcopy(dict(trace))
    actual = contract.legacy_payload()
    if actual != expected:
        keys = sorted(set(actual) | set(expected))
        field = next(
            (key for key in keys if actual.get(key) != expected.get(key)),
            "<unknown>",
        )
        raise TraceContractMismatch(
            f"trace differs at field {field!r}: "
            f"v2={actual.get(field)!r} legacy={expected.get(field)!r}"
        )


def shadow_from_legacy_trace(trace: Mapping[str, Any]) -> TraceProvenance:
    contract = from_legacy_trace(trace)
    assert_shadow_equivalent(contract, trace)
    return contract
