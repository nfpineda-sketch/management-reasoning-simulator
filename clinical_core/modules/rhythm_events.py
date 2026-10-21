"""Declared scripted events on the rhythm (C4) and the pump (C3) (proposal §8.4).

Some natural history happens whatever the resident does. Such an event is allowed, but
it declares its trigger, its cause class and its preventability, so the Trace and the
analysis can never read it as a consequence of management (§12.3, S3). These are the
primitives a rhythm or pump module will use; no family is migrated onto them yet.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..integration import Contribution, Contributor, register
from ..provenance import ChannelDelta, CoreEvent, RhythmTransition, SourceKind
from ..state import Channel, CoreInvariantError, RhythmState


@register
@dataclass(frozen=True)
class ScriptedRhythmEvent(Contributor):
    kind = SourceKind.SCRIPTED_EVENT
    type_name = "scripted_rhythm_event"

    id: str
    at_minute: int
    target: RhythmState
    preventability: str
    cause_class: str = "natural_history"

    def __post_init__(self):
        if not isinstance(self.target, RhythmState):
            raise CoreInvariantError("a scripted rhythm event names a RhythmState")
        if self.at_minute < 1 or not self.preventability or not self.cause_class:
            raise CoreInvariantError("a scripted event declares its minute, cause class and preventability")

    @classmethod
    def from_spec_data(cls, data):
        values = dict(data)
        values["target"] = RhythmState.from_dict(values["target"])
        return cls(**values)

    def contribute(self, state, minute, signals, anchors, profile):
        if minute != self.at_minute:
            return Contribution()
        if not state.R.pulse_present:
            return Contribution(events=(CoreEvent("rhythm_event_not_applied", self.source, minute, "info",
                                                  self.cause_class, self.preventability,
                                                  "scripted rhythm change not applied: the patient is already in arrest"),))
        if state.R == self.target:
            return Contribution()
        severity = "critical" if not self.target.pulse_present else "significant"
        return Contribution(
            transitions=(RhythmTransition(state.R, self.target, self.source, minute,
                                          f"scripted change to {self.target.code.value}"),),
            events=(CoreEvent("rhythm_change", self.source, minute, severity, self.cause_class, self.preventability,
                              f"rhythm changed to {self.target.code.value}"),))


@register
@dataclass(frozen=True)
class ScriptedPumpChange(Contributor):
    """A declared change of pump performance per minute over an interval (e.g. ischaemic depression)."""

    kind = SourceKind.SCRIPTED_EVENT
    type_name = "scripted_pump_change"

    id: str
    start_minute: int
    stop_minute: int
    per_minute: float
    preventability: str
    cause_class: str = "natural_history"

    def __post_init__(self):
        if not 0 <= self.start_minute < self.stop_minute or not self.preventability:
            raise CoreInvariantError("a scripted pump change declares its interval and preventability")

    def contribute(self, state, minute, signals, anchors, profile):
        if not self.start_minute < minute <= self.stop_minute:
            return Contribution()
        events = ()
        if minute == self.start_minute + 1:
            events = (CoreEvent("pump_change", self.source, minute, "significant", self.cause_class,
                                self.preventability, "scripted change of pump performance begins"),)
        return Contribution(deltas=(ChannelDelta(Channel.P, self.per_minute, self.source, minute,
                                                 "scripted change of pump performance"),), events=events)
