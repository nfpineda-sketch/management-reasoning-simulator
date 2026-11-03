"""Acute cardiogenic pulmonary edema as a shadow family writer (P2P-1, family pulmonary_edema). Shadow only, off unless
built into a run.

The family owns its disease process, never an observable (proposal §8.1 point 3):
- ``EdemaCongestion`` is the family's single coordinator of lung water on the common L channel, and its owner
  (``lung_water_authority``): while it is present the core's common overload coupling (``derived.congestion_rate``)
  adds nothing (decision B, P2O-3). Untreated, it adds a declared amount of lung water per minute (the authored rapid
  worsening). Once a decongestive treatment's signal is heard, the progression stops and it removes a declared amount
  per minute, never below the case's reversible lung water L_rev (``Anchors.reversible_lung_water``, 0 by default:
  never below the arrival congestion), counting what the common clearance removes in the same minute. Several congestion mechanisms of one case compose here, in one writer; a second
  owner of L is refused by the core. It writes L only: gas exchange, SpO2, delivery, the respiratory rate and lactate
  follow in the common core (``derived``: L -> G -> SpO2 -> delivery), never from here.
- ``DecongestiveTreatment`` is an authored decongestive therapy (a diuretic, a nitrate) reduced to the moment it
  begins: it publishes the signal and writes nothing. Its magnitude is the family's decongestion rate. Its other
  effects (venodilation, afterload, diuresis of volume) need common mechanisms that do not exist yet and are not
  represented here.

No value here is approved: every rate is a FAMILY_CANDIDATE or SYNTHETIC_ONLY value a run declares.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from ..derived import lung_water_clearance
from ..integration import Contribution, Contributor, Signal, register
from ..provenance import ChannelDelta, CoreEvent, SourceKind
from ..state import Channel, CoreInvariantError

EDEMA_DECONGESTION = "edema_decongestion"     # a decongestive treatment has begun (a family signal)


def _rate(value, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0.0:
        raise CoreInvariantError(f"the {name} is finite and not negative")


@register
@dataclass(frozen=True)
class EdemaCongestion(Contributor):
    kind = SourceKind.DISEASE_MODULE
    type_name = "pulmonary_edema_congestion"
    responds_to = frozenset({EDEMA_DECONGESTION})
    #: P2O-3: the family owns lung water; the core's common overload coupling adds nothing while this writer is present.
    lung_water_authority = True

    id: str
    progression_per_min: float
    decongestion_per_min: float = 0.0

    def __post_init__(self):
        _rate(self.progression_per_min, "progression rate")
        _rate(self.decongestion_per_min, "decongestion rate")

    def contribute(self, state, minute, signals, anchors, profile):
        if not state.R.pulse_present:
            return Contribution()
        if not tuple(s for s in self.heard(signals, EDEMA_DECONGESTION) if s.since_minute <= minute):
            if self.progression_per_min <= 0.0:
                return Contribution()
            return Contribution(deltas=(ChannelDelta(Channel.L, self.progression_per_min, self.source, minute,
                                                     "cardiogenic pulmonary edema progressing (untreated)"),))
        # Decongestion removes reversible congestion only: never below the case's L_rev (0: the arrival congestion),
        # counting what the common clearance removes in the same minute (both act on this minute's L).
        room = state.L - lung_water_clearance(state, profile) - anchors.reversible_lung_water
        amount = min(self.decongestion_per_min, max(0.0, room))
        if amount <= 0.0:
            return Contribution()
        return Contribution(deltas=(ChannelDelta(Channel.L, -amount, self.source, minute,
                                                 "cardiogenic pulmonary edema decongesting under treatment"),))


@register
@dataclass(frozen=True)
class DecongestiveTreatment(Contributor):
    kind = SourceKind.INTERVENTION
    type_name = "edema_decongestive_treatment"

    id: str
    begins_at_minute: int

    def __post_init__(self):
        if isinstance(self.begins_at_minute, bool) or not isinstance(self.begins_at_minute, int) \
                or self.begins_at_minute < 1:
            raise CoreInvariantError("a decongestive treatment begins at a minute >= 1")

    def signals(self, minute):
        if minute < self.begins_at_minute:
            return ()
        return (Signal(EDEMA_DECONGESTION, self.source, self.begins_at_minute),)

    def contribute(self, state, minute, signals, anchors, profile):
        if minute != self.begins_at_minute:
            return Contribution()
        return Contribution(events=(CoreEvent("treatment_started", self.source, minute, "info", "intervention",
                                              "not applicable", "decongestive treatment begun"),))
