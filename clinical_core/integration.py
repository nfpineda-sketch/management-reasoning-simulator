"""Deterministic minute-by-minute integration with explicit, attributed deltas.

One ``step`` integrates one minute:

1. every contributor publishes the signals it holds for that minute (an order that is
   running, a procedure that has completed); signals depend only on the contributor's
   own specification and the minute;
2. every contributor computes its contribution from the *same* state at the start of
   the minute, plus those signals -- so the order in which contributors are listed can
   never change the result (proposal §14.1, T3);
3. the core adds its own coupling (the oxygen-delivery debt, from flow, haemoglobin and
   saturation; KD-S1), lung water from excess preload on a pump without reserve (KD-S4), and
   updates its own memory: lactate kinetics, from that debt, and the common sympathetic
   drive, from the state the minute ends in (KD-S2);
4. the deltas are summed per channel, the declared bounds are enforced and every clipped
   amount is recorded as a clamp delta, rhythm transitions and setting changes are
   applied, and the new state is checked: the change in every channel must equal the sum
   of the deltas recorded for it.

Nothing reads a clock or a random generator. A contributor is a frozen specification:
whatever it must remember between minutes lives in ``CoreState.internal`` under its own
source key, so a trajectory is a pure function of (anchors, contributors, minutes).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, fields, is_dataclass
from typing import Any, ClassVar, Iterable, Mapping, Sequence

from .derived import (ADOPTED, AUXILIARY_SOURCES, DEFAULT_PROFILE, LUNG_WATER_CLEARANCE, PRELOAD_CONGESTION,
                      PROVISIONAL, CoreProfile, Derived, congestion_rate, derive, lactate_after_minute,
                      lung_water_clearance, sympathetic_after_minute)
from .provenance import (AuxiliaryChange, ChannelDelta, CoreEvent, MinuteRecord, ProvenanceError, RhythmTransition,
                         SettingChange, Source, SourceKind)
from .state import (AUXILIARY_FIELDS, Anchors, AuxiliaryState, Channel, CoreInvariantError, CoreState, FrozenRecord,
                    SCALAR_CHANNELS, digest, initial_state)

#: (lower, upper, status, why). A bound is a safety constraint, not physiology: every time one
#: acts, the clipped amount is recorded as a clamp delta, so it is never silent.
CHANNEL_BOUNDS: Mapping[Channel, tuple[float, float, str, str]] = {
    Channel.V: (-3000.0, 3000.0, PROVISIONAL, "guard only; the family engine's circulation clamp [.25, 1.9] "
                                              "is deliberately not adopted"),
    Channel.T: (0.1, 3.0, PROVISIONAL, "guard only"),
    Channel.P: (0.1, 3.0, PROVISIONAL, "guard only"),
    Channel.L: (-10.0, 10.0, PROVISIONAL, "guard only; only the core's congestion and clearance write L yet"),
    Channel.G: (-10.0, 10.0, PROVISIONAL, "guard only; no module writes G yet"),
    Channel.W: (-10.0, 10.0, PROVISIONAL, "guard only; no module writes W yet"),
    Channel.D: (-10000.0, 10000.0, PROVISIONAL, "guard only"),
    Channel.N: (-10.0, 10.0, PROVISIONAL, "guard only; no module writes N yet"),
    Channel.HB: (3.0, 18.0, ADOPTED, "family_engine._minute clamp"),
    Channel.GLUCOSE: (15.0, 350.0, ADOPTED, "family_engine._minute clamp"),
    Channel.K: (1.5, 9.0, PROVISIONAL, "guard only; no module writes K yet"),
}

OXYGEN_DEBT = Source(SourceKind.CORE_COUPLING, "oxygen_debt")
CONSERVATION_TOLERANCE = 1e-9   # floating-point noise only; not a clinical tolerance


@dataclass(frozen=True, order=True)
class Signal:
    """A fact a contributor holds for a minute that another may respond to (§8.1 point 4)."""

    name: str
    source: Source
    since_minute: int

    def to_dict(self) -> dict:
        return {"name": self.name, "source": self.source.to_dict(), "since_minute": self.since_minute}


@dataclass(frozen=True)
class Contribution:
    deltas: tuple[ChannelDelta, ...] = ()
    transitions: tuple[RhythmTransition, ...] = ()
    settings: tuple[SettingChange, ...] = ()
    events: tuple[CoreEvent, ...] = ()
    internal: FrozenRecord | None = None     # the contributor's own internal state after this minute


NOTHING = Contribution()
_REGISTRY: dict[str, type] = {}


def register(cls):
    """Make a contributor type reconstructible from its specification (replay).

    Registering the same class again (a module reload) replaces it; a *different* class
    under a name already taken is refused.
    """
    known = _REGISTRY.get(cls.type_name)
    if known is not None and (known.__module__, known.__qualname__) != (cls.__module__, cls.__qualname__):
        raise ValueError(f"contributor type {cls.type_name!r} registered twice")
    _REGISTRY[cls.type_name] = cls
    return cls


class Contributor:
    """Base of every disease module, intervention, logistic process and scripted event.

    Subclasses are frozen dataclasses with an ``id`` field. They must not keep state of
    their own: ``contribute`` receives the state and returns what changed.
    """

    kind: ClassVar[SourceKind]
    type_name: ClassVar[str]
    #: Signal names this contributor reads (its declared action capabilities).
    responds_to: ClassVar[frozenset[str]] = frozenset()

    @property
    def source(self) -> Source:
        return Source(self.kind, self.id)

    def signals(self, minute: int) -> tuple[Signal, ...]:
        return ()

    def contribute(self, state: CoreState, minute: int, signals: tuple[Signal, ...], anchors: Anchors,
                   profile: CoreProfile) -> Contribution:
        return NOTHING

    def own(self, state: CoreState) -> FrozenRecord:
        return state.internal_for(self.source.key)

    def heard(self, signals: Iterable[Signal], name: str) -> tuple[Signal, ...]:
        if name not in self.responds_to:
            raise ProvenanceError(f"{self.source.key} reads signal {name!r} it does not declare")
        return tuple(signal for signal in signals if signal.name == name)

    def to_spec(self) -> dict:
        data = {item.name: _plain(getattr(self, item.name)) for item in fields(self)}
        data["type"] = self.type_name
        return data


def _plain(value):
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    return value


def from_spec(spec: Mapping[str, Any]) -> Contributor:
    # Every contributor type the package defines is registered here, whatever was imported before.
    from . import interventions, logistics, modules  # noqa: F401
    data = dict(spec)
    name = data.pop("type")
    if name not in _REGISTRY:
        raise ProvenanceError(f"no contributor type {name!r}")
    cls = _REGISTRY[name]
    builder = getattr(cls, "from_spec_data", None)
    return builder(data) if builder else cls(**data)


def _oxygen_debt(state: CoreState, anchors: Anchors, profile: CoreProfile, minute: int) -> ChannelDelta:
    """D accumulates the shortfall of oxygen delivery against arrival and repays it slowly.

    dD = (1 - delivery_rel) - D / tau. At arrival delivery_rel is 1 and D is 0, so nothing
    moves; at a steady delivery the debt settles at tau * (1 - delivery_rel), which the
    lactate derivation reads (proposal C8).
    """
    before = derive(state, anchors, profile)
    amount = (1.0 - before.delivery_rel) - state.D / profile.debt_clearance_tau_min
    return ChannelDelta(Channel.D, amount, OXYGEN_DEBT, minute,
                        "oxygen-delivery shortfall against arrival, less first-order repayment")


def _check_owned(contributor: Contributor, contribution: Contribution, minute: int) -> None:
    if not isinstance(contribution, Contribution):
        raise ProvenanceError(f"{contributor.source.key} must return a Contribution")
    for item in contribution.deltas + contribution.transitions + contribution.settings + contribution.events:
        if item.source != contributor.source:
            raise ProvenanceError(f"{contributor.source.key} wrote a change attributed to {item.source.key}")
        if item.minute != minute:
            raise ProvenanceError(f"{contributor.source.key} wrote a change for minute {item.minute} in minute {minute}")
    if contribution.internal is not None and not isinstance(contribution.internal, FrozenRecord):
        raise ProvenanceError("internal state is returned as a FrozenRecord")


#: Source kinds only the integrator writes. A contributor claiming one is refused.
RESERVED_KINDS = frozenset({SourceKind.CLAMP, SourceKind.CORE_COUPLING})


def _ordered(contributors: Sequence[Contributor]) -> tuple[Contributor, ...]:
    for item in contributors:
        if not isinstance(item, Contributor) or not is_dataclass(item) or not item.__dataclass_params__.frozen:
            raise ProvenanceError(f"{type(item).__name__} must be a frozen dataclass Contributor")
        if item.source.kind in RESERVED_KINDS:
            raise ProvenanceError(f"{item.source.key}: only the integrator writes {item.source.kind.value} changes")
    ordered = tuple(sorted(contributors, key=lambda item: (item.source.kind.value, item.source.id)))
    keys = [item.source.key for item in ordered]
    if len(set(keys)) != len(keys):
        raise ProvenanceError(f"two contributors share a source: {keys}")
    if any(item.source == OXYGEN_DEBT for item in ordered):
        raise ProvenanceError("the core's own coupling is not a contributor")
    return ordered


def step(state: CoreState, contributors: Sequence[Contributor], anchors: Anchors,
         profile: CoreProfile = DEFAULT_PROFILE) -> tuple[CoreState, MinuteRecord]:
    """Integrate minute ``state.minute + 1``. Returns the new state and what was applied."""
    minute = state.minute + 1
    ordered = _ordered(contributors)
    signals = []
    for contributor in ordered:
        for signal in contributor.signals(minute):
            if signal.source != contributor.source:
                raise ProvenanceError(f"{contributor.source.key} published a signal for {signal.source.key}")
            signals.append(signal)
    signals = tuple(sorted(signals))
    deltas = [_oxygen_debt(state, anchors, profile, minute)]
    congestion = congestion_rate(state, anchors, profile)
    if congestion:
        deltas.append(ChannelDelta(Channel.L, congestion, PRELOAD_CONGESTION, minute,
                                   "excess preload on a pump without reserve"))
    clearance = lung_water_clearance(state, profile)
    if clearance:
        deltas.append(ChannelDelta(Channel.L, -clearance, LUNG_WATER_CLEARANCE, minute,
                                   "lung water above arrival clearing slowly"))
    transitions, settings, events = [], [], []
    internal = {}
    for contributor in ordered:
        # A contributor sees only the signals it declares it responds to.
        heard = tuple(signal for signal in signals if signal.name in contributor.responds_to)
        contribution = contributor.contribute(state, minute, heard, anchors, profile)
        _check_owned(contributor, contribution, minute)
        deltas.extend(contribution.deltas)
        transitions.extend(contribution.transitions)
        settings.extend(contribution.settings)
        events.extend(contribution.events)
        if contribution.internal is not None:
            internal[contributor.source.key] = contribution.internal
    values = {}
    for channel in SCALAR_CHANNELS:
        before = state.value(channel)
        proposed = before + math.fsum(delta.amount for delta in deltas if delta.channel is channel)
        lower, upper, _, why = CHANNEL_BOUNDS[channel]
        bounded = min(upper, max(lower, proposed))
        if bounded != proposed:
            deltas.append(ChannelDelta(channel, bounded - proposed, Source(SourceKind.CLAMP, f"bounds:{channel.value}"),
                                       minute, f"held within [{lower:g}, {upper:g}] ({why})"))
        values[channel.value] = bounded
    rhythm = _rhythm_after(state, transitions)
    fio2 = _setting_after(state.fio2, "fio2", settings)
    terminal = state.terminal_since if state.terminal_since is not None else (None if rhythm.pulse_present else minute)
    new_internal = state.internal.updated(**internal) if internal else state.internal
    new_state = state.evolve(minute=minute, R=rhythm, fio2=fio2, terminal_since=terminal, internal=new_internal,
                             **values)
    # The core's auxiliary state (P2D-1). Lactate follows the debt of the minute before; the
    # drive answers to the state the minute ends in, so a fall in pressure raises the rate in
    # the same minute and only its decay is lagged.
    aux = AuxiliaryState(lactate_excess_mmol_l=lactate_after_minute(state, profile),
                         sympathetic_drive=sympathetic_after_minute(state, new_state, anchors, profile))
    new_state = new_state.evolve(aux=aux)
    changes = tuple(AuxiliaryChange(name, getattr(state.aux, name), getattr(aux, name), AUXILIARY_SOURCES[name],
                                    minute, AUXILIARY_FIELDS[name])
                    for name in AUXILIARY_FIELDS if getattr(aux, name) != getattr(state.aux, name))
    record = MinuteRecord(minute=minute, deltas=tuple(deltas), transitions=tuple(transitions),
                          settings=tuple(settings), events=tuple(events), internal_updates=tuple(sorted(internal)),
                          auxiliary=changes)
    _check_conservation(state, new_state, record)
    derive(new_state, anchors, profile)   # the observation invariants hold, or this minute fails
    return new_state, record


def _rhythm_after(state: CoreState, transitions: list[RhythmTransition]):
    if not transitions:
        return state.R
    targets = {transition.after for transition in transitions}
    if len(targets) > 1:
        raise CoreInvariantError("two sources moved the rhythm to different states in the same minute")
    for transition in transitions:
        if transition.before != state.R:
            raise CoreInvariantError(f"{transition.source.key} moved a rhythm the patient is not in")
    target = transitions[0].after
    if state.terminal_since is not None and target.pulse_present:
        raise CoreInvariantError("return of a pulse after arrest is not modelled (resuscitation is out of scope)")
    return target


def _setting_after(current: float, setting: str, settings: list[SettingChange]) -> float:
    values = {change.value for change in settings if change.setting == setting}
    if len(values) > 1:
        raise CoreInvariantError(f"two sources set {setting} to different values in the same minute")
    return values.pop() if values else current


def _check_conservation(before: CoreState, after: CoreState, record: MinuteRecord) -> None:
    changed = {change.quantity: change for change in record.auxiliary}
    for name in AUXILIARY_FIELDS:
        change = changed.get(name)
        expected = (getattr(before.aux, name), getattr(before.aux, name)) if change is None else (change.before,
                                                                                                  change.after)
        if (getattr(before.aux, name), getattr(after.aux, name)) != expected:
            raise ProvenanceError(f"auxiliary {name} changed without a record of the change")
    for channel in SCALAR_CHANNELS:
        change = after.value(channel) - before.value(channel)
        total = record.total(channel)
        scale = max(1.0, abs(before.value(channel)), abs(after.value(channel)))
        if abs(change - total) > CONSERVATION_TOLERANCE * scale:
            raise ProvenanceError(f"{channel.value} changed by {change!r} but its recorded deltas sum to {total!r}")


@dataclass(frozen=True)
class Trajectory:
    anchors: Anchors
    profile: CoreProfile
    contributors: tuple[Contributor, ...]
    states: tuple[CoreState, ...]
    records: tuple[MinuteRecord, ...]

    def derived(self) -> tuple[Derived, ...]:
        return tuple(derive(state, self.anchors, self.profile) for state in self.states)

    def to_dict(self) -> dict:
        return {"anchors": self.anchors.to_dict(), "profile": self.profile.to_dict(),
                "contributors": [item.to_spec() for item in self.contributors],
                "states": [state.to_dict() for state in self.states],
                "records": [record.to_dict() for record in self.records]}

    def digest(self) -> str:
        return digest(self.to_dict())


def run(anchors: Anchors, contributors: Sequence[Contributor], minutes: int,
        profile: CoreProfile = DEFAULT_PROFILE, initial: CoreState | None = None) -> Trajectory:
    """Integrate ``minutes`` minutes from arrival (or from ``initial``)."""
    if isinstance(minutes, bool) or not isinstance(minutes, int) or minutes < 0:
        raise ValueError("minutes is a non-negative integer")
    state = initial_state(anchors) if initial is None else initial
    derive(state, anchors, profile)
    ordered = _ordered(tuple(contributors))
    states, records = [state], []
    for _ in range(minutes):
        state, record = step(state, ordered, anchors, profile)
        states.append(state)
        records.append(record)
    return Trajectory(anchors, profile, ordered, tuple(states), tuple(records))


def scenario_to_dict(anchors: Anchors, contributors: Sequence[Contributor], minutes: int,
                     profile: CoreProfile = DEFAULT_PROFILE) -> dict:
    return {"anchors": anchors.to_dict(), "profile": profile.to_dict(), "minutes": minutes,
            "contributors": [item.to_spec() for item in _ordered(tuple(contributors))]}


def scenario_from_dict(data: Mapping) -> tuple[Anchors, tuple[Contributor, ...], int, CoreProfile]:
    profile_data = dict(data["profile"])
    for name in ("pressure_levels", "oxygen_levels"):
        profile_data[name] = tuple(tuple(pair) for pair in profile_data[name])
    return (Anchors.from_dict(data["anchors"]), tuple(from_spec(item) for item in data["contributors"]),
            int(data["minutes"]), CoreProfile(**profile_data))
