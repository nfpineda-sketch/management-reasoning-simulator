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

from .state import AUXILIARY_FIELDS, BLOOD_FIELDS, Channel, CoreInvariantError, RhythmState, SCALAR_CHANNELS


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


#: What a demand modifier stands for (P2E-2): a disease or module that raises or lowers demand
#: while it acts (sepsis, fever), or a transient state (a seizure, agitation, pain).
DEMAND_KINDS = ("disease", "transient")


@dataclass(frozen=True)
class DemandModifier:
    """A factor on metabolic oxygen demand that one source declares for one minute (P2E-2).

    Demand is the case's baseline times every factor declared for the minute; a source that
    stops declaring its factor stops modifying demand. A modifier does not write D: the core
    integrates the delivery deficit against demand, and names the modifying sources on its
    debt delta. The factors themselves (sepsis, fever, seizure) are TBD.
    """

    factor: float
    kind: str
    source: Source
    minute: int
    description: str

    def __post_init__(self):
        if isinstance(self.factor, bool) or not isinstance(self.factor, (int, float)) \
                or not math.isfinite(self.factor) or self.factor <= 0:
            raise ProvenanceError(f"a demand factor is a finite positive number, not {self.factor!r}")
        object.__setattr__(self, "factor", float(self.factor))
        if self.kind not in DEMAND_KINDS:
            raise ProvenanceError(f"a demand modifier is one of {DEMAND_KINDS}")
        if not isinstance(self.source, Source):
            raise ProvenanceError("every demand modifier names its Source")
        _minute(self.minute)
        _description(self.description)

    def to_dict(self) -> dict:
        return {"type": "demand", "factor": self.factor, "kind": self.kind, "source": self.source.to_dict(),
                "minute": self.minute, "description": self.description}


@dataclass(frozen=True)
class AuxiliaryChange:
    """One change of the core's auxiliary dynamic state in one minute (P2D-1).

    Only the integrator writes one, under a core-coupling source. It records the value before
    and after, so the auxiliary state can be replayed and audited like a channel.
    """

    quantity: str
    before: float
    after: float
    source: Source
    minute: int
    description: str

    def __post_init__(self):
        if self.quantity not in AUXILIARY_FIELDS:
            raise ProvenanceError(f"unknown auxiliary quantity {self.quantity!r}")
        for name in ("before", "after"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ProvenanceError("an auxiliary value is a finite number")
        if not isinstance(self.source, Source) or self.source.kind is not SourceKind.CORE_COUPLING:
            raise ProvenanceError("only the core (a core-coupling source) changes its auxiliary state")
        _minute(self.minute)
        if not self.description:
            raise ProvenanceError("an auxiliary change says what it is")

    def to_dict(self) -> dict:
        return {"type": "auxiliary", "quantity": self.quantity, "before": self.before, "after": self.after,
                "source": self.source.to_dict(), "minute": self.minute, "description": self.description}


class BloodProcess(str, Enum):
    """The processes that move volume or red cells into or out of the circulation (P2I-2T)."""

    WHOLE_BLOOD_LOSS = "whole_blood_loss"            # out: volume and red cells, at the current composition
    CRYSTALLOID_IN = "crystalloid_in"                # in: volume, no red cells
    CRYSTALLOID_OUT = "crystalloid_out"              # out: crystalloid redistributing out, no red cells
    RED_CELL_TRANSFUSION = "red_cell_transfusion"    # in: volume and red cells, at the unit's composition
    PLASMA_REFILL = "plasma_refill"                  # in: plasma from the interstitium, no red cells


#: Which way each process moves the circulation, the ``BloodState`` fields it adds to (volume,
#: red cells) and the source kinds that may declare it. Plasma refill is the core's own coupling.
BLOOD_PROCESSES: Mapping[BloodProcess, tuple[int, str, str | None, frozenset]] = {
    BloodProcess.WHOLE_BLOOD_LOSS: (-1, "shed_ml", "shed_red_cells",
                                    frozenset({SourceKind.DISEASE_MODULE, SourceKind.SCRIPTED_EVENT})),
    BloodProcess.CRYSTALLOID_IN: (1, "crystalloid_in_ml", None,
                                  frozenset({SourceKind.INTERVENTION, SourceKind.SCRIPTED_EVENT})),
    BloodProcess.CRYSTALLOID_OUT: (-1, "crystalloid_out_ml", None,
                                   frozenset({SourceKind.INTERVENTION, SourceKind.SCRIPTED_EVENT})),
    BloodProcess.RED_CELL_TRANSFUSION: (1, "transfused_ml", "transfused_red_cells",
                                        frozenset({SourceKind.INTERVENTION, SourceKind.SCRIPTED_EVENT})),
    BloodProcess.PLASMA_REFILL: (1, "refill_ml", None, frozenset({SourceKind.CORE_COUPLING})),
}
if {name for _, volume, cells, _ in BLOOD_PROCESSES.values() for name in (volume, cells) if name} != set(BLOOD_FIELDS):
    raise ProvenanceError("every blood-state field is owned by exactly the processes that change it")


def _positive_volume(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise ProvenanceError(f"a blood flow moves a finite positive volume, not {value!r}")
    return float(value)


@dataclass(frozen=True)
class BloodFlow:
    """What one source declares moves into or out of the circulation in one minute (P2I-2T).

    A source declares only the volume and the process. The red cells it carries are resolved
    by the integrator: whole blood leaves at the composition the blood has at the start of the
    minute; a red-cell transfusion brings the haemoglobin concentration of its unit
    (``hb_g_dl``, the only process that declares one); crystalloid and refill bring none. So
    no source writes haemoglobin, and no bleed has a separate volume rate and Hb rate.
    """

    process: BloodProcess
    volume_ml: float
    source: Source
    minute: int
    description: str
    modulated_by: tuple[Source, ...] = ()
    hb_g_dl: float | None = None

    def __post_init__(self):
        if not isinstance(self.process, BloodProcess):
            object.__setattr__(self, "process", BloodProcess(self.process))
        object.__setattr__(self, "volume_ml", _positive_volume(self.volume_ml))
        if not isinstance(self.source, Source):
            raise ProvenanceError("every blood flow names its Source")
        if self.source.kind not in BLOOD_PROCESSES[self.process][3]:
            raise ProvenanceError(f"a {self.source.kind.value} source does not declare {self.process.value}")
        _minute(self.minute)
        _description(self.description)
        object.__setattr__(self, "modulated_by", tuple(self.modulated_by))
        if any(not isinstance(item, Source) for item in self.modulated_by):
            raise ProvenanceError("modulators are Sources")
        if self.process is BloodProcess.RED_CELL_TRANSFUSION:
            if isinstance(self.hb_g_dl, bool) or not isinstance(self.hb_g_dl, (int, float)) \
                    or not math.isfinite(self.hb_g_dl) or self.hb_g_dl <= 0:
                raise ProvenanceError("a red-cell transfusion declares the haemoglobin concentration of its unit")
            object.__setattr__(self, "hb_g_dl", float(self.hb_g_dl))
        elif self.hb_g_dl is not None:
            raise ProvenanceError(f"{self.process.value} declares no haemoglobin: whole blood leaves at the current "
                                  "composition, and crystalloid and plasma carry none")


@dataclass(frozen=True)
class BloodChange:
    """One flow applied to the shared blood state, with the red cells it carried (P2I-2T).

    The integrator writes one for every ``BloodFlow`` and for the core's plasma refill, so the
    blood state can be replayed and audited: each of its fields changes by exactly the sum of
    the changes of the process that owns it. ``hb_g_dl`` is the haemoglobin concentration the
    flow carried (the current one for whole blood, the unit's for a transfusion, 0 otherwise).
    """

    process: BloodProcess
    volume_ml: float
    red_cells: float
    hb_g_dl: float
    source: Source
    minute: int
    description: str
    modulated_by: tuple[Source, ...] = ()

    def __post_init__(self):
        if not isinstance(self.process, BloodProcess):
            object.__setattr__(self, "process", BloodProcess(self.process))
        object.__setattr__(self, "volume_ml", _positive_volume(self.volume_ml))
        for name in ("red_cells", "hb_g_dl"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ProvenanceError(f"{name} of a blood change is a finite non-negative number")
            object.__setattr__(self, name, float(value))
        if BLOOD_PROCESSES[self.process][2] is None and (self.red_cells or self.hb_g_dl):
            raise ProvenanceError(f"{self.process.value} carries no red cells")
        if not isinstance(self.source, Source) or self.source.kind not in BLOOD_PROCESSES[self.process][3]:
            raise ProvenanceError(f"{self.process.value} is not written by this source")
        _minute(self.minute)
        _description(self.description)
        object.__setattr__(self, "modulated_by", tuple(self.modulated_by))

    @property
    def direction(self) -> int:
        return BLOOD_PROCESSES[self.process][0]

    @property
    def signed_volume_ml(self) -> float:
        """The change of the circulating-volume deviation: + into the circulation, - out of it."""
        return self.direction * self.volume_ml

    @property
    def signed_red_cells(self) -> float:
        return self.direction * self.red_cells

    def to_dict(self) -> dict:
        return {"type": "blood", "process": self.process.value, "volume_ml": self.volume_ml,
                "red_cells": self.red_cells, "hb_g_dl": self.hb_g_dl, "source": self.source.to_dict(),
                "minute": self.minute, "description": self.description,
                "modulated_by": [item.to_dict() for item in self.modulated_by]}


@dataclass(frozen=True)
class MinuteRecord:
    """Everything applied in one minute, in a deterministic order."""

    minute: int
    deltas: tuple[ChannelDelta, ...] = ()
    transitions: tuple[RhythmTransition, ...] = ()
    settings: tuple[SettingChange, ...] = ()
    events: tuple[CoreEvent, ...] = ()
    internal_updates: tuple[str, ...] = field(default=())
    auxiliary: tuple[AuxiliaryChange, ...] = field(default=())
    demand: tuple[DemandModifier, ...] = field(default=())
    blood: tuple[BloodChange, ...] = field(default=())

    def __post_init__(self):
        _minute(self.minute)
        for item in (self.deltas + self.transitions + self.settings + self.events + self.auxiliary + self.demand
                     + self.blood):
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
                "internal_updates": list(self.internal_updates),
                "auxiliary": [item.to_dict() for item in self.auxiliary],
                "demand": [item.to_dict() for item in self.demand],
                "blood": [item.to_dict() for item in self.blood]}


def attribution(records: Iterable[MinuteRecord], channel: Channel) -> dict[str, float]:
    """Sum of the direct contributions to one channel, per source, over a run (§12.2)."""
    totals: dict[str, list[float]] = {}
    for record in records:
        for delta in record.deltas:
            if delta.channel is channel:
                totals.setdefault(delta.source.key, []).append(delta.amount)
    return {key: math.fsum(values) for key, values in sorted(totals.items())}


def blood_attribution(records: Iterable[MinuteRecord]) -> dict[str, dict[str, float]]:
    """Signed volume and red cells moved per (process, source) over a run (P2I-2T)."""
    totals: dict[str, dict[str, list[float]]] = {}
    for record in records:
        for change in record.blood:
            entry = totals.setdefault(f"{change.process.value} {change.source.key}", {"volume_ml": [], "red_cells": []})
            entry["volume_ml"].append(change.signed_volume_ml)
            entry["red_cells"].append(change.signed_red_cells)
    return {key: {name: math.fsum(values) for name, values in entry.items()} for key, entry in sorted(totals.items())}
