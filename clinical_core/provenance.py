"""Where every change to the core state came from (proposal §12.1 ``effects[]``, §12.2).

Each applied change is a record that names its source, the minute it was applied in and
the channel it touched. The source classes are the ones the Trace v2 contract lists --
disease module, order (intervention), logistic process, scripted event, clamp -- plus the
core's own coupling between channels (the oxygen-delivery debt computed from flow,
haemoglobin and saturation), which is neither a disease nor an order and must not be
attributed to either.

A record's ``minute`` is the end of the interval it acted over: a delta recorded at
minute m acted over (m - 1, m]. These records are direct contributions, not
counterfactual effects (§12.2).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping

from .state import Channel, CoreInvariantError, RhythmState, SCALAR_CHANNELS


class ProvenanceError(CoreInvariantError):
    """A change without a valid source, or a source writing what it does not own."""


class SourceKind(str, Enum):
    DISEASE_MODULE = "disease_module"
    INTERVENTION = "intervention"            # an order; its id is the order's id
    LOGISTIC_PROCESS = "logistic_process"
    SCRIPTED_EVENT = "scripted_event"
    CLAMP = "clamp"                          # a safety bound the integrator enforced
    CORE_COUPLING = "core_coupling"          # one channel computed from others by the core


@dataclass(frozen=True, order=True)
class Source:
    kind: SourceKind
    id: str

    def __post_init__(self):
        if not isinstance(self.kind, SourceKind):
            object.__setattr__(self, "kind", SourceKind(self.kind))
        if not isinstance(self.id, str) or not self.id.strip():
            raise ProvenanceError("every source has a non-empty id")

    @property
    def key(self) -> str:
        return f"{self.kind.value}:{self.id}"

    def to_dict(self) -> dict:
        return {"kind": self.kind.value, "id": self.id}

    @classmethod
    def from_dict(cls, data: Mapping) -> "Source":
        return cls(SourceKind(data["kind"]), data["id"])


def _minute(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ProvenanceError("a change is applied in a minute >= 1")
    return value


def _description(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProvenanceError("every change carries a description of the effect")
    return value


@dataclass(frozen=True)
class ChannelDelta:
    """An additive change to one scalar channel, applied in one minute, by one source.

    ``modulated_by`` names the other sources that changed the size of this effect without
    owning it (a proton-pump inhibitor slowing a bleed the haemorrhage module owns).
    """

    channel: Channel
    amount: float
    source: Source
    minute: int
    description: str
    modulated_by: tuple[Source, ...] = ()

    def __post_init__(self):
        if not isinstance(self.channel, Channel):
            object.__setattr__(self, "channel", Channel(self.channel))
        if self.channel not in SCALAR_CHANNELS:
            raise ProvenanceError("R changes only by a RhythmTransition")
        if isinstance(self.amount, bool) or not isinstance(self.amount, (int, float)) or not math.isfinite(self.amount):
            raise ProvenanceError(f"delta amount must be finite, not {self.amount!r}")
        object.__setattr__(self, "amount", float(self.amount))
        if not isinstance(self.source, Source):
            raise ProvenanceError("every delta names its Source")
        _minute(self.minute)
        _description(self.description)
        object.__setattr__(self, "modulated_by", tuple(self.modulated_by))
        if any(not isinstance(item, Source) for item in self.modulated_by):
            raise ProvenanceError("modulators are Sources")

    def to_dict(self) -> dict:
        return {"type": "delta", "channel": self.channel.value, "amount": self.amount,
                "source": self.source.to_dict(), "minute": self.minute, "description": self.description,
                "modulated_by": [item.to_dict() for item in self.modulated_by]}


@dataclass(frozen=True)
class RhythmTransition:
    """C4 moves only by transitions; each one keeps its before and after state."""

    before: RhythmState
    after: RhythmState
    source: Source
    minute: int
    description: str

    def __post_init__(self):
        if not isinstance(self.before, RhythmState) or not isinstance(self.after, RhythmState):
            raise ProvenanceError("a transition goes from one RhythmState to another")
        if not isinstance(self.source, Source):
            raise ProvenanceError("every transition names its Source")
        _minute(self.minute)
        _description(self.description)

    def to_dict(self) -> dict:
        return {"type": "rhythm_transition", "before": self.before.to_dict(), "after": self.after.to_dict(),
                "source": self.source.to_dict(), "minute": self.minute, "description": self.description}


#: Support settings the core reads but that are not channels (proposal §7.3).
SETTINGS = frozenset({"fio2"})


@dataclass(frozen=True)
class SettingChange:
    setting: str
    value: float
    source: Source
    minute: int
    description: str

    def __post_init__(self):
        if self.setting not in SETTINGS:
            raise ProvenanceError(f"unknown support setting {self.setting!r}")
        if isinstance(self.value, bool) or not isinstance(self.value, (int, float)) or not math.isfinite(self.value):
            raise ProvenanceError("a setting value is a finite number")
        if not isinstance(self.source, Source):
            raise ProvenanceError("every setting change names its Source")
        _minute(self.minute)
        _description(self.description)

    def to_dict(self) -> dict:
        return {"type": "setting", "setting": self.setting, "value": self.value, "source": self.source.to_dict(),
                "minute": self.minute, "description": self.description}


SEVERITIES = ("info", "significant", "critical")


@dataclass(frozen=True)
class CoreEvent:
    """A typed event (proposal §10.2) with the metadata §8.1(6) requires."""

    kind: str
    source: Source
    minute: int
    severity: str
    cause_class: str
    preventability: str
    description: str

    def __post_init__(self):
        if not isinstance(self.kind, str) or not self.kind:
            raise ProvenanceError("an event has a kind")
        if not isinstance(self.source, Source):
            raise ProvenanceError("every event names its Source")
        _minute(self.minute)
        if self.severity not in SEVERITIES:
            raise ProvenanceError(f"severity is one of {SEVERITIES}")
        for name in ("cause_class", "preventability"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise ProvenanceError(f"an event declares its {name}")
        _description(self.description)

    def to_dict(self) -> dict:
        return {"type": "event", "kind": self.kind, "source": self.source.to_dict(), "minute": self.minute,
                "severity": self.severity, "cause_class": self.cause_class,
                "preventability": self.preventability, "description": self.description}


@dataclass(frozen=True)
class MinuteRecord:
    """Everything applied in one minute, in a deterministic order."""

    minute: int
    deltas: tuple[ChannelDelta, ...] = ()
    transitions: tuple[RhythmTransition, ...] = ()
    settings: tuple[SettingChange, ...] = ()
    events: tuple[CoreEvent, ...] = ()
    internal_updates: tuple[str, ...] = field(default=())

    def __post_init__(self):
        _minute(self.minute)
        for item in self.deltas + self.transitions + self.settings + self.events:
            if item.minute != self.minute:
                raise ProvenanceError("a record holds only changes applied in its own minute")

    def total(self, channel: Channel) -> float:
        return math.fsum(delta.amount for delta in self.deltas if delta.channel is channel)

    def by_source(self) -> dict[str, dict[str, float]]:
        totals: dict[str, dict[str, float]] = {}
        for delta in self.deltas:
            per_channel = totals.setdefault(delta.source.key, {})
            per_channel[delta.channel.value] = per_channel.get(delta.channel.value, 0.0) + delta.amount
        return totals

    def to_dict(self) -> dict:
        return {"minute": self.minute, "deltas": [item.to_dict() for item in self.deltas],
                "transitions": [item.to_dict() for item in self.transitions],
                "settings": [item.to_dict() for item in self.settings],
                "events": [item.to_dict() for item in self.events],
                "internal_updates": list(self.internal_updates)}


def attribution(records: Iterable[MinuteRecord], channel: Channel) -> dict[str, float]:
    """Sum of the direct contributions to one channel, per source, over a run (§12.2)."""
    totals: dict[str, list[float]] = {}
    for record in records:
        for delta in record.deltas:
            if delta.channel is channel:
                totals.setdefault(delta.source.key, []).append(delta.amount)
    return {key: math.fsum(values) for key, values in sorted(totals.items())}
