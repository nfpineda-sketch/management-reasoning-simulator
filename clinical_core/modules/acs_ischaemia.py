"""Acute coronary occlusion as shadow family writers (P2N-2, family acs). Shadow only, off unless built into a run.

The family owns its disease process, never an observable (proposal §8.1 point 3):
- ``IschaemicPump`` owns the ischaemic pump process on the common P channel. While the artery stays occluded it
  lowers P by a declared amount per minute, never below a declared floor; once the reperfusion signal is heard it
  stops the loss and lets P recover first order toward a declared share of what the occlusion took during the
  encounter (never above the arrival pump, P = 1). It writes P only.
- ``IschaemicCongestion`` owns the cardiogenic filling-state congestion of the family on the common L channel: lung
  water added per minute in proportion to the pump's shortfall below arrival (1 - P). It writes L only; the common
  clearance (``derived.lung_water_clearance``) and the common preload congestion (``derived.congestion_rate``) stay
  the core's. Whether a common P -> L coupling should exist is a pending common decision; this is the family's.
- ``CoronaryReperfusion`` is the logistic process (a PCI completed at a declared minute): it publishes the signal and
  writes nothing.

Output, pressure, delivery, the deficit, D, lactate, the heart rate, tone, the gases and the consciousness all follow
in the common core (``integration``, ``derived``). No value here is approved: every rate, floor, share and time
constant is a FAMILY_CANDIDATE or SYNTHETIC_ONLY value a run declares.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from ..integration import Contribution, Contributor, Signal, register
from ..provenance import ChannelDelta, CoreEvent, SourceKind
from ..state import Channel, CoreInvariantError

CORONARY_REPERFUSION = "coronary_reperfusion"     # the occluded artery was opened (a family signal)


def _reperfused(contributor, signals, minute) -> tuple:
    return tuple(s for s in contributor.heard(signals, CORONARY_REPERFUSION) if s.since_minute <= minute)


@register
@dataclass(frozen=True)
class IschaemicPump(Contributor):
    kind = SourceKind.DISEASE_MODULE
    type_name = "acs_ischaemic_pump"
    responds_to = frozenset({CORONARY_REPERFUSION})

    id: str
    loss_per_min: float
    floor: float
    recovery_share: float
    recovery_tau_min: float

    def __post_init__(self):
        if not (math.isfinite(self.loss_per_min) and self.loss_per_min >= 0.0):
            raise CoreInvariantError("the ischaemic pump loss per minute is finite and not negative")
        if not 0.0 < self.floor <= 1.0:
            raise CoreInvariantError("the ischaemic pump floor is in (0, 1]: the occlusion never stops the pump")
        if not 0.0 <= self.recovery_share <= 1.0:
            raise CoreInvariantError("the recovery share is a share of what the occlusion took, between 0 and 1")
        if not (math.isfinite(self.recovery_tau_min) and self.recovery_tau_min > 0.0):
            raise CoreInvariantError("the recovery time constant is finite and positive")

    def contribute(self, state, minute, signals, anchors, profile):
        if not state.R.pulse_present:
            return Contribution()
        own = self.own(state)
        reperfused = _reperfused(self, signals, minute)
        if not reperfused:
            amount = -min(self.loss_per_min, max(0.0, state.P - self.floor))
            events = (CoreEvent("ischaemic_pump_loss", self.source, minute, "significant", "disease_process",
                                "preventable", "ongoing myocardial ischaemia lowers pump performance"),) \
                if own.get("started") is None else ()
            deltas = (ChannelDelta(Channel.P, amount, self.source, minute,
                                   "ongoing ischaemia: pump performance falls"),) if amount < 0.0 else ()
            return Contribution(deltas=deltas, events=events, internal=own.updated(started=own.get("started") or minute))
        opened = own.get("reperfused_at")
        events = ()
        if opened is None:
            opened = minute
            # What the occlusion took during the encounter: arrival (1) less the pump at the reperfusion minute.
            own = own.updated(reperfused_at=opened, pump_at_reperfusion=state.P,
                              target=state.P + self.recovery_share * max(0.0, 1.0 - state.P))
            events = (CoreEvent("reperfusion_reached_pump", self.source, minute, "significant", "intervention",
                                "not applicable", "the artery is open: the ischaemic pump loss stops"),)
        gap = own["target"] - state.P
        amount = gap * -math.expm1(-1.0 / self.recovery_tau_min) if gap > 0.0 else 0.0
        deltas = (ChannelDelta(Channel.P, amount, self.source, minute,
                               "after reperfusion: declared recovery of pump performance"),) if amount > 0.0 else ()
        return Contribution(deltas=deltas, events=events, internal=own.updated(reperfused_at=opened))


@register
@dataclass(frozen=True)
class IschaemicCongestion(Contributor):
    kind = SourceKind.DISEASE_MODULE
    type_name = "acs_ischaemic_congestion"

    id: str
    lung_water_per_shortfall_per_min: float

    def __post_init__(self):
        if not (math.isfinite(self.lung_water_per_shortfall_per_min) and self.lung_water_per_shortfall_per_min >= 0.0):
            raise CoreInvariantError("the congestion gain is finite and not negative")

    def contribute(self, state, minute, signals, anchors, profile):
        if not state.R.pulse_present:
            return Contribution()
        amount = self.lung_water_per_shortfall_per_min * max(0.0, 1.0 - state.P)
        if amount <= 0.0:
            return Contribution()
        return Contribution(deltas=(ChannelDelta(Channel.L, amount, self.source, minute,
                                                 "cardiogenic filling-state congestion (pump below arrival)"),))


@register
@dataclass(frozen=True)
class CoronaryReperfusion(Contributor):
    kind = SourceKind.LOGISTIC_PROCESS
    type_name = "coronary_reperfusion"

    id: str
    completes_at_minute: int

    def __post_init__(self):
        if isinstance(self.completes_at_minute, bool) or not isinstance(self.completes_at_minute, int) \
                or self.completes_at_minute < 1:
            raise CoreInvariantError("a reperfusion completes at a minute >= 1")

    def signals(self, minute):
        if minute < self.completes_at_minute:
            return ()
        return (Signal(CORONARY_REPERFUSION, self.source, self.completes_at_minute),)

    def contribute(self, state, minute, signals, anchors, profile):
        if minute != self.completes_at_minute:
            return Contribution()
        return Contribution(events=(CoreEvent("procedure_completed", self.source, minute, "info", "logistic_process",
                                              "not applicable", "coronary reperfusion completed"),))
