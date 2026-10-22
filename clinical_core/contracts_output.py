"""Offline output adapter: the shadow core's results in Contracts v2 shapes (P2B-3).

Every payload is shadow, never authoritative:
- it carries ``namespace: clinical_core_shadow`` and ``authoritative: False``;
- it is built from the core's own records, so its provenance is the core's;
- it holds numbers, codes and provenance only, never text for a resident: no ``visible``,
  ``label``, ``receipt`` or narrative field (``check_shadow_payload`` fails closed).

What it never does:
- build a ``FateReceipt``: fates belong to the Phase-0 ledger, and the shadow trace only
  cites the fate the input adapter read (``cited_fate`` in each ``OrderBinding``);
- write to the Phase-0/Phase-1 Trace, the session, receipts or persistence;
- interrupt a turn: the core has no turns, so ``interrupted`` is always ``None`` and the
  trace says so in ``limitations``.

Out of the shadow trace, a shadow record travels in ``envelope``, which carries the namespace
even where the contract has no field for it.
"""
from __future__ import annotations

import json
from typing import Iterable, Mapping

from contracts_v2 import events as event_contracts
from contracts_v2 import fates as fate_contracts
from contracts_v2 import observations as observation_contracts
from contracts_v2 import orders as order_contracts
from contracts_v2 import submissions as submission_contracts
from contracts_v2 import timing as time_contracts
from contracts_v2 import trace as trace_contracts
from contracts_v2.events import EventInterruption, EventRecord
from contracts_v2.observations import ObservationSnapshot
from contracts_v2.trace import TraceProvenance

from . import AUTHORITATIVE_ENGINE, CORE_VERSION
from .derived import derive
from .integration import Trajectory
from .state import SCALAR_CHANNELS, digest

SHADOW_NAMESPACE = "clinical_core_shadow"
#: Keys that carry what a resident sees in the Phase-0/Phase-1 records. None may appear here.
RESIDENT_VISIBLE_KEYS = frozenset({"visible", "label", "receipt", "receipt_shown_elsewhere", "receipt_lines",
                                   "text", "raw_text", "narrative", "message", "current_findings"})
#: The Contracts v2 this output and the input adapter speak, by schema and version.
CONTRACTS = {module.SCHEMA: module.VERSION for module in (
    order_contracts, fate_contracts, time_contracts, event_contracts, observation_contracts, trace_contracts,
    submission_contracts)}


class ShadowOutputError(ValueError):
    """A shadow payload would look authoritative or carry resident-visible content."""


def header() -> dict:
    return {"namespace": SHADOW_NAMESPACE, "authoritative": False, "authoritative_engine": AUTHORITATIVE_ENGINE,
            "core_version": CORE_VERSION}


def shadow_events(trajectory: Trajectory, minutes: Iterable[int] | None = None) -> EventInterruption:
    """The core's events (all, or those of ``minutes``) as an EventInterruption v2 record."""
    wanted = None if minutes is None else set(minutes)
    payloads = []
    for record in trajectory.records:
        for event in record.events:
            if wanted is not None and event.minute not in wanted:
                continue
            payloads.append({**header(), "kind": event.kind, "minute": event.minute,
                             "source": event.source.to_dict(), "source_key": event.source.key,
                             "severity": event.severity, "cause_class": event.cause_class,
                             "preventability": event.preventability, "provenance_note": event.description})
    for payload in payloads:
        check_shadow_payload(payload)
    return EventInterruption(events=tuple(EventRecord(payload) for payload in payloads), interrupted=None)


def shadow_observation(trajectory: Trajectory, minute: int) -> ObservationSnapshot:
    """The core's state and derived values at ``minute`` as an ObservationSnapshot v2 record.

    Raw numbers and codes, for comparison only: nothing is rounded to a display, put in a
    display range or turned into words.
    """
    if isinstance(minute, bool) or not isinstance(minute, int) or not 0 <= minute < len(trajectory.states):
        raise ShadowOutputError(f"minute {minute!r} is not in the trajectory")
    state = trajectory.states[minute]
    derived = derive(state, trajectory.anchors, trajectory.profile)
    channels = {channel.value: getattr(state, channel.value) for channel in SCALAR_CHANNELS}
    payload = {**header(), "minute": state.minute, "arrested": not state.R.pulse_present,
               "arrest_minute": state.terminal_since, "rhythm_state": state.R.to_dict(), "fio2": state.fio2,
               "channels": channels, "derived": derived.to_dict()}
    check_shadow_payload(payload)
    return ObservationSnapshot(payload=payload)


def shadow_trace(trajectory: Trajectory, adapted) -> TraceProvenance:
    """The shadow run with its inputs' identity and its own provenance, as a TraceProvenance v2 record.

    ``adapted`` is the ``contracts_input.AdaptedInputs`` the run was built from. Its bindings
    are cited, not reinterpreted: each keeps the order's ledger identity and the fate the
    ledger gave it.
    """
    bindings = [binding.to_dict() for binding in adapted.bindings]
    keys = {item.source.key for item in trajectory.contributors}
    for binding in bindings:
        if binding["source_key"] is not None and binding["source_key"] not in keys:
            raise ShadowOutputError(f"order {binding['order_id']} is bound to {binding['source_key']}, which did "
                                    "not run")
    limitations = [{"kind": "shadow_only", "authoritative_engine": AUTHORITATIVE_ENGINE},
                   {"kind": "turn_interruption_not_modelled"}]
    limitations += [{"kind": "legacy_event_not_consumed", "event": event["kind"], "cause_class": event["cause_class"],
                     "minute": event["minute"]} for event in adapted.events_not_consumed]
    payload = {
        **header(),
        "submission": {"submission_ids": sorted({binding["submission_id"] for binding in bindings}),
                       "order_ids": [binding["order_id"] for binding in bindings]},
        "orders": bindings,
        "events": [event.legacy_payload() for event in shadow_events(trajectory).events],
        "observation_snapshot": shadow_observation(trajectory, len(trajectory.states) - 1).legacy_payload(),
        "limitations": limitations,
        "versions": {"core_version": CORE_VERSION, "contracts": dict(CONTRACTS),
                     "profile_digest": digest(trajectory.profile.to_dict())},
        "contributors": [item.to_spec() for item in trajectory.contributors],
        "minutes": [record.to_dict() for record in trajectory.records],
    }
    check_shadow_payload(payload)
    return TraceProvenance(payload=payload)


def envelope(contract) -> dict:
    """A shadow contract record ready to leave the trace, sealed in the shadow namespace.

    ``EventInterruption`` v2 has no field for a namespace at its top level: with no events, its
    record is the same as an authoritative "nothing happened". Out of the shadow trace, every
    shadow record travels inside this envelope.
    """
    sealed = {**header(), "contract": contract.as_record()}
    check_shadow_payload(sealed)
    return sealed


def check_shadow_payload(payload: Mapping) -> None:
    """Fail closed unless the payload is plainly shadow, JSON-safe and free of resident-visible keys."""
    if payload.get("namespace") != SHADOW_NAMESPACE or payload.get("authoritative") is not False:
        raise ShadowOutputError("a shadow payload is namespaced and never authoritative")
    try:
        json.dumps(payload, allow_nan=False)
    except (TypeError, ValueError) as error:
        raise ShadowOutputError(f"a shadow payload is plain JSON data: {error}") from error
    found = _visible_keys(payload)
    if found:
        raise ShadowOutputError(f"a shadow payload carries resident-visible fields: {sorted(found)}")


def _visible_keys(value) -> set:
    found = set()
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key in RESIDENT_VISIBLE_KEYS:
                found.add(key)
            found |= _visible_keys(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            found |= _visible_keys(item)
    return found
