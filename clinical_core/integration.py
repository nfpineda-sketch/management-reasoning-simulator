"""Deterministic minute-by-minute integration with explicit, attributed deltas.

One ``step`` integrates one minute:

1. every contributor publishes the signals it holds for that minute (an order that is
   running, a procedure that has completed); signals depend only on the contributor's
   own specification and the minute;
2. every contributor computes its contribution from the *same* state at the start of
   the minute, plus those signals -- so the order in which contributors are listed can
   never change the result (proposal §14.1, T3);
3. the shared blood state (P2I-2T) applies every declared blood flow and the core's plasma
   refill, from the blood state at the start of the minute: whole blood leaves at its current
   composition, a red-cell unit brings its own, crystalloid and refill bring none. V moves by
   kappa x each flow's volume, attributed to the flow's source, and Hb by the change of the
   red-cell concentration (a core coupling); no contributor writes V or Hb itself;
4. the core adds its own coupling: the oxygen-delivery debt, from the deficit of delivery
   (flow, haemoglobin and saturation) below the metabolic demand that the case's baseline and
   the minute's declared modifiers give (KD-S1, P2E-2); lung water from excess preload on a
   pump without reserve (KD-S4); vascular tone from the acute shock signal at the start of the
   minute, when its gain is on (P2J-2); and it updates its own memory: lactate kinetics, from that
   debt, the common sympathetic drive, from the state the minute ends in (KD-S2), the
   demand of the minute and the collapse burden; when a declared collapse criterion is met,
   it moves the rhythm to a pulseless one (P2E-3);
5. the deltas are summed per channel, the declared bounds are enforced and every clipped
   amount is recorded as a clamp delta, rhythm transitions and setting changes are
   applied, and the new state is checked: the change in every channel must equal the sum
   of the deltas recorded for it, and the blood state, V and Hb must match the blood
   changes recorded for the minute.

Nothing reads a clock or a random generator. A contributor is a frozen specification:
whatever it must remember between minutes lives in ``CoreState.internal`` under its own
source key, so a trajectory is a pure function of (anchors, contributors, minutes).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, fields, is_dataclass, replace
from typing import Any, ClassVar, Iterable, Mapping, Sequence

from .derived import (ADOPTED, AUXILIARY_SOURCES, BLOOD_COMPOSITION, COLLAPSE, DEFAULT_PROFILE, LUNG_WATER_CLEARANCE,
                      PLASMA_REFILL, PRELOAD_CONGESTION, PROVISIONAL, CoreProfile, Derived, arrival_state,
                      blood_haemoglobin, collapse_burden_after_minute, collapse_reached, congestion_rate,
                      delivery_rel_of, derive, effective_delivery, effective_oxygen_deficit, lactate_after_minute, lung_water_clearance,
                      acid_base_active, acid_burden_after_minute,
                      oxygen_demand, plasma_refill, red_cell_content, sympathetic_after_minute, terminal_rhythm,
                      tone_target)
from .provenance import (BLOOD_PROCESSES, AuxiliaryChange, BloodChange, BloodFlow, BloodProcess, ChannelDelta,
                         CoreEvent, DemandModifier, MinuteRecord, ProvenanceError, RhythmTransition, SettingChange,
                         Source, SourceKind)
from .state import (AUXILIARY_FIELDS, BLOOD_FIELDS, Anchors, AuxiliaryState, BloodState, Channel, CoreInvariantError,
                    CoreState, FrozenRecord, SCALAR_CHANNELS, UnresolvedBoundary, digest, initial_state)

#: (lower, upper, status, why). A bound is a safety constraint, not physiology: every time one
#: acts, the clipped amount is recorded as a clamp delta, so it is never silent.
CHANNEL_BOUNDS: Mapping[Channel, tuple[float, float, str, str]] = {
    Channel.V: (-3000.0, 3000.0, PROVISIONAL, "guard only, in mL-eq of circulating volume (applied to V scaled by "
                                              "kappa, so it never separates kappa from the curve scale); the family "
                                              "engine's circulation clamp [.25, 1.9] is deliberately not adopted"),
    Channel.T: (0.1, 3.0, PROVISIONAL, "guard only"),
    Channel.P: (0.1, 3.0, PROVISIONAL, "guard only"),
    Channel.L: (-10.0, 10.0, PROVISIONAL, "guard only; only the core's congestion and clearance write L yet"),
    Channel.G: (-10.0, 10.0, PROVISIONAL, "guard only; no module writes G yet"),
    Channel.W: (-10.0, 10.0, PROVISIONAL, "guard only; no module writes W yet"),
    Channel.D: (0.0, 10000.0, PROVISIONAL, "guard only; a debt is never negative (P2E-2)"),
    Channel.N: (-10.0, 10.0, PROVISIONAL, "guard only; no module writes N yet"),
    Channel.HB: (3.0, 18.0, ADOPTED, "family_engine._minute clamp"),
    Channel.GLUCOSE: (15.0, 350.0, ADOPTED, "family_engine._minute clamp"),
    Channel.K: (1.5, 9.0, PROVISIONAL, "guard only; no module writes K yet"),
}

OXYGEN_DEBT = Source(SourceKind.CORE_COUPLING, "oxygen_debt")
#: The core's vascular-tone response to the acute shock signal (P2J-2); off at deficit_to_tone_gain 0.
VASCULAR_TONE = Source(SourceKind.CORE_COUPLING, "vascular_tone")
CONSERVATION_TOLERANCE = 1e-9   # floating-point noise only; not a clinical tolerance
#: Channels only the shared blood state moves (P2I-2T): V by kappa x the circulating-volume
#: change, Hb by the change of the red-cell concentration. A disease module, order or logistic
#: process declares a ``BloodFlow`` instead; only a scripted probe still moves them directly.
BLOOD_CHANNELS = frozenset({Channel.V, Channel.HB})
#: Sources whose V and Hb deltas are not the blood state's: scripted probes and the bounds. What
#: they move is accounted in ``BloodState.outside_v`` / ``outside_hb``.
_OUTSIDE_BLOOD = frozenset({SourceKind.SCRIPTED_EVENT, SourceKind.CLAMP})


def check_blood_identity(state: CoreState, anchors: Anchors, profile: CoreProfile) -> None:
    """V = kappa x C + outside_v and Hb = composition + outside_hb (P2I-2T), or the state cannot exist.

    Every state the core produces satisfies both; a state assembled or edited by hand, or resumed
    under another kappa or arrival circulating volume, is refused here instead of carried forward.
    """
    blood = state.blood
    volume = profile.volume_preload_kappa * blood.volume_ml + blood.outside_v
    hb = blood_haemoglobin(blood, anchors, profile) + blood.outside_hb
    if abs(state.V - volume) > CONSERVATION_TOLERANCE * max(1.0, abs(state.V), abs(volume)) \
            or abs(state.hb - hb) > CONSERVATION_TOLERANCE * max(1.0, abs(state.hb), abs(hb)):
        raise CoreInvariantError(f"minute {state.minute}: V {state.V!r} and Hb {state.hb!r} do not match the blood "
                                 f"state ({volume!r}, {hb!r}): the state's V or Hb is not explained by its blood "
                                 "state under this profile")


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
    demand: tuple[DemandModifier, ...] = ()  # factors on metabolic oxygen demand for this minute (P2E-2)
    blood: tuple[BloodFlow, ...] = ()        # what enters or leaves the circulation this minute (P2I-2T)


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


def _oxygen_debt(state: CoreState, anchors: Anchors, profile: CoreProfile, minute: int, demand: float,
                 modulators: tuple[Source, ...]) -> ChannelDelta:
    """D is the accumulated oxygen-delivery debt (P2E-2; semantics corrected by the faculty in P2I-2AC and P2I-2AD).

    With deficit = max(0, demand - reserve x delivery), delivery the delivery index
    (arrival-relative delivery times the case's arrival delivery ratio, P2F-6) read at the
    start of the minute, demand the one declared for it, reserve the oxygen extraction reserve
    (P2I-2P: only the demand left unmet once extraction is exhausted is a deficit; 1, the neutral
    default, is the earlier no-reserve model) and g the deficit-to-debt gain:
    - while deficit > 0 the debt accrues, dD = g x deficit, and is not repaid (dD >= 0);
    - with deficit == 0 nothing accrues and the debt repays first-order, dD = -D / tau, but only
      across a minute that stays without deficit: ``step`` withdraws the repayment when the minute
      ends in a deficit (``_no_repayment_across``, P2I-2AD), and adds no debt for that minute.
    Delivery above demand is no credit: D only repays what it accrued, and never falls below 0.
    Under a steady deficit D keeps rising at g x deficit per minute; it no longer settles. The
    sources that modified demand are named as modulators of the debt only when they changed it:
    when the deficit against the modified demand differs from the deficit against the case's
    baseline.
    """
    before = derive(state, anchors, profile)
    delivery = effective_delivery(before.delivery_rel, anchors)
    reserve = profile.oxygen_extraction_reserve
    deficit = effective_oxygen_deficit(demand, delivery, reserve)
    changed = deficit != effective_oxygen_deficit(anchors.metabolic_demand_baseline, delivery, reserve)
    if deficit > 0.0:
        amount, why = (profile.debt_per_delivery_deficit * deficit,
                       "oxygen demand left unmet once extraction is exhausted: accrued, not repaid")
    else:
        amount, why = -state.D / profile.debt_clearance_tau_min, "no unmet demand: first-order repayment"
    return ChannelDelta(Channel.D, amount, OXYGEN_DEBT, minute, why, modulated_by=modulators if changed else ())


def _acid_burden(state: CoreState, anchors: Anchors, profile: CoreProfile, demand: float) -> float:
    """P2K-2: the metabolic acid burden after the minute, produced by the minute's effective oxygen deficit (the one D
    integrates: the start-of-minute delivery against the minute's demand) and cleared first-order. Held while the acid-base
    physiology is off."""
    if not acid_base_active(profile):
        return state.aux.metabolic_acid_burden
    delivery = effective_delivery(derive(state, anchors, profile).delivery_rel, anchors)
    deficit = effective_oxygen_deficit(demand, delivery, profile.oxygen_extraction_reserve)
    return acid_burden_after_minute(state.aux.metabolic_acid_burden, deficit, profile)


def _no_repayment_across(debt: ChannelDelta, after: CoreState, anchors: Anchors, profile: CoreProfile,
                         demand: float) -> ChannelDelta | None:
    """P2I-2AD: the repayment withdrawn when the minute ends in a deficit, else None.

    Repayment needs an interval that stays oxygen-adequate: no deficit at the start (``_oxygen_debt``)
    and none at the end, read on the end state's delivery against the minute's demand. Delivery reads
    no D, so the end state's delivery is final before D is. A minute that crosses from no deficit
    into one neither repays nor accrues: the deficit signal of its start was 0.
    """
    if debt.amount >= 0.0:
        return None
    delivery = effective_delivery(delivery_rel_of(after, anchors, profile), anchors)
    if effective_oxygen_deficit(demand, delivery, profile.oxygen_extraction_reserve) <= 0.0:
        return None
    return ChannelDelta(Channel.D, 0.0, OXYGEN_DEBT, debt.minute,
                        "no unmet demand at the start, but the minute ends in one: no repayment across the crossing",
                        modulated_by=debt.modulated_by)


def _vascular_tone(state: CoreState, deltas: Sequence[ChannelDelta], anchors: Anchors, profile: CoreProfile,
                   minute: int) -> ChannelDelta:
    """P2J-2: T moves to the tone the state at the start of the minute calls for (``tone_target``).

    Explicit feedback, one minute behind the signal it answers: tone lowers output, so a same-minute reading would be an
    algebraic loop, and no solver is used. The minute after arrival keeps T at 1 (arrival is the target's fixed point).
    Fails closed where nothing is decided: another source writing T in the same minute (how a drug or a disease module
    would compose with the response is not decided), or a gain whose largest target, 1 + g at no delivery, is outside
    T's guard (so the guard never shapes the response).
    """
    upper = CHANNEL_BOUNDS[Channel.T][1]
    if 1.0 + profile.deficit_to_tone_gain > upper:
        raise CoreInvariantError(f"the tone response's largest target 1 + {profile.deficit_to_tone_gain!r} is above "
                                 f"T's guard {upper!r}")
    writers = sorted({delta.source.key for delta in deltas if delta.channel is Channel.T})
    if writers:
        raise CoreInvariantError(f"minute {minute}: {writers} write T while the vascular-tone response is on; how they "
                                 "compose is not decided (P2J-2)")
    return ChannelDelta(Channel.T, tone_target(state, anchors, profile) - state.T, VASCULAR_TONE, minute,
                        "the tone the acute shock signal at the start of the minute calls for")


def _blood_minute(state: CoreState, flows: Sequence[BloodFlow], anchors: Anchors, profile: CoreProfile,
                  minute: int) -> tuple[BloodState, tuple[BloodChange, ...], list[ChannelDelta]]:
    """The shared blood state over one minute (P2I-2T): the flows declared, then the core's refill.

    Everything is read from the blood state at the start of the minute: the composition whole
    blood leaves with, and the refill's distance from its target. Each change moves the
    circulating volume; V moves by kappa x that volume, attributed to the change's source, and
    Hb by the change of red-cell content over circulating volume, under the core's composition
    coupling, modulated by the sources that changed it.
    """
    before = state.blood
    current_hb = blood_haemoglobin(before, anchors, profile)
    changes = []
    for flow in flows:
        carries_cells = BLOOD_PROCESSES[flow.process][2] is not None
        hb = (current_hb if flow.process is BloodProcess.WHOLE_BLOOD_LOSS else flow.hb_g_dl) if carries_cells else 0.0
        changes.append(BloodChange(flow.process, flow.volume_ml,
                                   red_cell_content(flow.volume_ml, hb, anchors, profile) if carries_cells else 0.0,
                                   hb, flow.source, minute, flow.description, flow.modulated_by))
    refill = plasma_refill(before, profile)
    if refill > 0:
        changes.append(BloodChange(BloodProcess.PLASMA_REFILL, refill, 0.0, 0.0, PLASMA_REFILL, minute,
                                   "plasma refilling part of the shed volume from the interstitium"))
    after = _blood_after(before, changes)
    deltas = [ChannelDelta(Channel.V, profile.volume_preload_kappa * change.signed_volume_ml, change.source, minute,
                           change.description, change.modulated_by) for change in changes]
    if changes:
        hb_change = blood_haemoglobin(after, anchors, profile) - current_hb
        if hb_change:
            deltas.append(ChannelDelta(Channel.HB, hb_change, BLOOD_COMPOSITION, minute,
                                       "haemoglobin concentration: red-cell content over circulating volume",
                                       modulated_by=tuple(sorted({change.source for change in changes}))))
    return after, tuple(changes), deltas


def _blood_after(before: BloodState, changes: Sequence[BloodChange]) -> BloodState:
    """Each blood-state field plus the changes of the process that owns it."""
    added = {name: [getattr(before, name)] for name in BLOOD_FIELDS}
    for change in changes:
        _, volume, cells, _ = BLOOD_PROCESSES[change.process]
        added[volume].append(change.volume_ml)
        if cells is not None:
            added[cells].append(change.red_cells)
    return replace(before, **{name: math.fsum(values) for name, values in added.items()})


def _check_owned(contributor: Contributor, contribution: Contribution, minute: int) -> None:
    if not isinstance(contribution, Contribution):
        raise ProvenanceError(f"{contributor.source.key} must return a Contribution")
    if not isinstance(contribution.demand, tuple) or any(not isinstance(item, DemandModifier)
                                                         for item in contribution.demand):
        raise ProvenanceError(f"{contributor.source.key}: demand is modified only by a tuple of DemandModifier records")
    if not isinstance(contribution.blood, tuple) or any(not isinstance(item, BloodFlow) for item in contribution.blood):
        raise ProvenanceError(f"{contributor.source.key}: the circulation changes only by a tuple of BloodFlow records")
    if contributor.source.kind is not SourceKind.SCRIPTED_EVENT and any(delta.channel in BLOOD_CHANNELS
                                                                         for delta in contribution.deltas):
        raise ProvenanceError(f"{contributor.source.key} wrote V or Hb directly: volume and red cells move only "
                              "through the shared blood state (a BloodFlow, P2I-2T)")
    for item in (contribution.deltas + contribution.transitions + contribution.settings + contribution.events
                 + contribution.demand + contribution.blood):
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
    check_blood_identity(state, anchors, profile)
    minute = state.minute + 1
    ordered = _ordered(contributors)
    signals = []
    for contributor in ordered:
        for signal in contributor.signals(minute):
            if signal.source != contributor.source:
                raise ProvenanceError(f"{contributor.source.key} published a signal for {signal.source.key}")
            signals.append(signal)
    signals = tuple(sorted(signals))
    deltas = []
    congestion = congestion_rate(state, anchors, profile)
    if congestion:
        deltas.append(ChannelDelta(Channel.L, congestion, PRELOAD_CONGESTION, minute,
                                   "excess preload on a pump without reserve"))
    clearance = lung_water_clearance(state, profile)
    if clearance:
        deltas.append(ChannelDelta(Channel.L, -clearance, LUNG_WATER_CLEARANCE, minute,
                                   "lung water above arrival clearing slowly"))
    transitions, settings, events, modifiers, flows = [], [], [], [], []
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
        modifiers.extend(contribution.demand)
        flows.extend(contribution.blood)
        if contribution.internal is not None:
            internal[contributor.source.key] = contribution.internal
    # V and Hb written directly this minute: only a scripted probe may (``_check_owned``).
    direct = {channel: [delta.amount for delta in deltas if delta.channel is channel] for channel in BLOOD_CHANNELS}
    blood, blood_changes, blood_deltas = _blood_minute(state, flows, anchors, profile, minute)
    deltas.extend(blood_deltas)
    # The minute's demand: the case's baseline times every declared factor (P2E-2). The debt
    # stays the first delta of the minute, as it was before demand had a state.
    demand = oxygen_demand(anchors, modifiers)
    modulators = tuple(sorted({item.source for item in modifiers}))
    debt = _oxygen_debt(state, anchors, profile, minute, demand, modulators)
    deltas.insert(0, debt)
    # Terminal collapse (P2E-3): when the declared criterion is met, the core moves R to a
    # pulseless rhythm, unless a contributor already moves the rhythm this minute (then the
    # criterion, still met, applies to the rhythm it leaves, the next minute).
    burden = collapse_burden_after_minute(state, anchors, profile)
    if not transitions and collapse_reached(state, burden, profile):
        target = terminal_rhythm(state, anchors, profile)
        transitions.append(RhythmTransition(state.R, target, COLLAPSE, minute,
                                            f"sustained critically low output met the declared collapse criterion: "
                                            f"{target.code.value}"))
        events.append(CoreEvent("terminal_collapse", COLLAPSE, minute, "critical", "physiological_collapse",
                                "not assessed", f"terminal collapse from sustained critically low output: "
                                                f"{target.code.value}"))
    if profile.deficit_to_tone_gain > 0.0:
        deltas.append(_vascular_tone(state, deltas, anchors, profile, minute))
    values = {}
    for channel in SCALAR_CHANNELS:
        before = state.value(channel)
        proposed = before + math.fsum(delta.amount for delta in deltas if delta.channel is channel)
        lower, upper, _, why = CHANNEL_BOUNDS[channel]
        if channel is Channel.V:
            lower, upper = lower * profile.volume_preload_kappa, upper * profile.volume_preload_kappa
        bounded = min(upper, max(lower, proposed))
        if bounded != proposed:
            if channel in BLOOD_CHANNELS and any(delta.channel is channel and delta.source.kind not in _OUTSIDE_BLOOD
                                                 for delta in deltas):
                # A bound on V or Hb is a guard, not physiology: cutting what the blood state moved
                # would part the channel from it, so the run stops (P2I-2T, as P2D-2).
                raise UnresolvedBoundary(f"minute {minute}: the shared blood state takes {channel.value} to "
                                         f"{proposed!r}, outside its guard [{lower:g}, {upper:g}] ({why}); no rule "
                                         "for that boundary is decided")
            deltas.append(ChannelDelta(channel, bounded - proposed, Source(SourceKind.CLAMP, f"bounds:{channel.value}"),
                                       minute, f"held within [{lower:g}, {upper:g}] ({why})"))
        values[channel.value] = bounded
    outside = {channel: math.fsum(direct[channel] + [delta.amount for delta in deltas if delta.channel is channel
                                                     and delta.source.kind is SourceKind.CLAMP])
               for channel in BLOOD_CHANNELS}
    if any(outside.values()):
        blood = replace(blood, outside_v=math.fsum((blood.outside_v, outside[Channel.V])),
                        outside_hb=math.fsum((blood.outside_hb, outside[Channel.HB])))
    rhythm = _rhythm_after(state, transitions)
    fio2 = _setting_after(state.fio2, "fio2", settings)
    terminal = state.terminal_since if state.terminal_since is not None else (None if rhythm.pulse_present else minute)
    new_internal = state.internal.updated(**internal) if internal else state.internal
    new_state = state.evolve(minute=minute, R=rhythm, fio2=fio2, terminal_since=terminal, internal=new_internal,
                             blood=blood, **values)
    withdrawn = _no_repayment_across(debt, new_state, anchors, profile, demand)
    if withdrawn is not None:
        deltas[0] = withdrawn
        new_state = new_state.evolve(D=state.D)
    # The core's auxiliary state (P2D-1). Lactate follows the debt of the minute before; the
    # drive answers to the state the minute ends in, so a fall in pressure raises the rate in
    # the same minute and only its decay is lagged. P2I-2AF: the drive reads the minute's own
    # demand (its acute deficit signal), so the demand is set before the drive is.
    aux = AuxiliaryState(lactate_excess_mmol_l=lactate_after_minute(state, profile),
                         sympathetic_drive=state.aux.sympathetic_drive, oxygen_demand=demand, collapse_burden=burden,
                         metabolic_acid_burden=_acid_burden(state, anchors, profile, demand))
    aux = replace(aux, sympathetic_drive=sympathetic_after_minute(state, new_state.evolve(aux=aux), anchors, profile))
    new_state = new_state.evolve(aux=aux)
    changes = tuple(AuxiliaryChange(name, getattr(state.aux, name), getattr(aux, name), AUXILIARY_SOURCES[name],
                                    minute, AUXILIARY_FIELDS[name])
                    for name in AUXILIARY_FIELDS if getattr(aux, name) != getattr(state.aux, name))
    record = MinuteRecord(minute=minute, deltas=tuple(deltas), transitions=tuple(transitions),
                          settings=tuple(settings), events=tuple(events), internal_updates=tuple(sorted(internal)),
                          auxiliary=changes, demand=tuple(modifiers), blood=blood_changes)
    _check_conservation(state, new_state, record)
    _check_blood(state, new_state, record, anchors, profile)
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


def _check_blood(before: CoreState, after: CoreState, record: MinuteRecord, anchors: Anchors,
                 profile: CoreProfile) -> None:
    """The shared blood state, V and Hb are accounted for by the minute's blood changes (P2I-2T).

    - every blood-state field changed by exactly the changes of the process that owns it, and no
      field ever fell (they are cumulative);
    - the V deltas of every source but scripted probes and bounds sum to kappa x the circulating
      volume those sources moved: no bleed, fluid or refill moves V outside the blood state, and
      none twice;
    - the Hb deltas of every source but scripted probes and bounds are the composition coupling's,
      and sum to the change of red-cell content over circulating volume: Hb never moves without a
      red-cell or volume change to explain it;
    - every change carries the red cells the composition gives, and refill is what the blood
      state at the start of the minute gives;
    - what probes and bounds moved is accounted in ``outside_v`` / ``outside_hb``, so V = kappa x C
      + outside_v and Hb = composition + outside_hb hold after every minute.
    """
    current = blood_haemoglobin(before.blood, anchors, profile)
    for change in record.blood:
        # Each record carries the composition the core resolved: the current Hb for whole blood, the
        # unit's for a transfusion, none for crystalloid and refill.
        hb = (current if change.process is BloodProcess.WHOLE_BLOOD_LOSS else change.hb_g_dl) \
            if BLOOD_PROCESSES[change.process][2] is not None else 0.0
        cells = red_cell_content(change.volume_ml, hb, anchors, profile) if hb else 0.0
        if abs(change.hb_g_dl - hb) > CONSERVATION_TOLERANCE * max(1.0, hb) \
                or abs(change.red_cells - cells) > CONSERVATION_TOLERANCE * max(1.0, cells):
            raise ProvenanceError(f"{change.process.value} from {change.source.key} carries red cells the "
                                  "composition does not give")
    refill = math.fsum(c.volume_ml for c in record.blood if c.process is BloodProcess.PLASMA_REFILL)
    if abs(refill - plasma_refill(before.blood, profile)) > CONSERVATION_TOLERANCE * max(1.0, refill):
        raise ProvenanceError("plasma refill differs from what the blood state at the start of the minute gives")
    expected = _blood_after(before.blood, record.blood)
    for name in BLOOD_FIELDS:
        old, new, want = getattr(before.blood, name), getattr(after.blood, name), getattr(expected, name)
        if new < old or abs(new - want) > CONSERVATION_TOLERANCE * max(1.0, abs(want)):
            raise ProvenanceError(f"blood {name} changed from {old!r} to {new!r} but its recorded changes give {want!r}")
    volume = profile.volume_preload_kappa * math.fsum(change.signed_volume_ml for change in record.blood
                                                      if change.source.kind not in _OUTSIDE_BLOOD)
    moved = math.fsum(delta.amount for delta in record.deltas
                      if delta.channel is Channel.V and delta.source.kind not in _OUTSIDE_BLOOD)
    if abs(moved - volume) > CONSERVATION_TOLERANCE * max(1.0, abs(before.V), abs(after.V)):
        raise ProvenanceError(f"V moved by {moved!r} outside probes and bounds, but kappa x the circulating-volume "
                              f"change is {volume!r}")
    hb_deltas = [delta for delta in record.deltas
                 if delta.channel is Channel.HB and delta.source.kind not in _OUTSIDE_BLOOD]
    if any(delta.source != BLOOD_COMPOSITION for delta in hb_deltas):
        raise ProvenanceError("only the blood composition moves Hb outside probes and bounds")
    concentration = blood_haemoglobin(after.blood, anchors, profile) - blood_haemoglobin(before.blood, anchors, profile)
    if abs(math.fsum(delta.amount for delta in hb_deltas) - concentration) > CONSERVATION_TOLERANCE * max(
            1.0, before.hb, after.hb):
        raise ProvenanceError("Hb moved without the red-cell or volume change that explains it")
    # The V delta of every blood change, as _blood_minute writes it; the rest of the probes' and the
    # bounds' V and Hb deltas moved those channels outside the blood state.
    mapped = [(c.source, c.description, profile.volume_preload_kappa * c.signed_volume_ml) for c in record.blood]
    outside = {Channel.V: [], Channel.HB: []}
    for delta in record.deltas:
        if delta.channel not in BLOOD_CHANNELS or delta.source.kind not in _OUTSIDE_BLOOD:
            continue
        key = (delta.source, delta.description, delta.amount)
        if delta.channel is Channel.V and key in mapped:
            mapped.remove(key)
        else:
            outside[delta.channel].append(delta.amount)
    for channel, name in ((Channel.V, "outside_v"), (Channel.HB, "outside_hb")):
        moved = math.fsum([getattr(before.blood, name)] + outside[channel])
        if abs(getattr(after.blood, name) - moved) > CONSERVATION_TOLERANCE * max(1.0, abs(moved)):
            raise ProvenanceError(f"blood {name} is not what probes and bounds moved")
    check_blood_identity(after, anchors, profile)


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
    arrival = arrival_state(anchors, profile)
    if initial is not None and initial.minute == 0 and initial != arrival:
        raise CoreInvariantError("a minute-0 initial state is the case's arrival (derived.arrival_state); this one "
                                 "is not, so the run would start from a different patient")
    state = arrival if initial is None else initial
    check_blood_identity(state, anchors, profile)
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
