"""Opioid toxicity as a shadow family writer (P2U-1, family opioid). Shadow only, off unless built into a run.

The family owns its disease process and its antagonist signal, never an observable (proposal §8.1 point 3):
- ``OpioidCentralDepression`` is the family's central respiratory depression: it writes the common central drive
  availability only (``provenance.AvailabilityChange``, the P2U-1 target), a declared fraction of it lost per minute
  while the depression deepens untreated.
- ``NaloxoneReversal`` is the family's antagonist signal: from a declared minute it returns a declared fraction of the
  missing availability per minute, toward 1 (no central depression) and never past it.
The expressed RR, W, PaCO2, pH, SpO2 (through P2T-5's link when a profile declares it), delivery, D, lactate, HR and
consciousness follow in the common core, never from here; neither writer writes a channel, G, L, the mechanics, the
distress, the demand or the blood. The core refuses their changes unless the P2K-2 acid-base physiology is on.

No value here is approved: the depression and the reversal rates are SYNTHETIC_ONLY spans a run declares; no
post-treatment course is authored (NALOXONE_KINETICS_UNSET), and the recurrence after a long-acting opioid is only the
depression resuming once the reversal stops (RECURRENCE_KINETICS_UNSET).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from ..integration import Contribution, Contributor, register
from ..provenance import AvailabilityChange, SourceKind
from ..state import CoreInvariantError


def _fraction(value, what: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) \
            or not 0.0 <= value < 1.0:
        raise CoreInvariantError(f"the {what} is a finite fraction per minute in [0, 1)")


def _minutes(start, stop) -> None:
    if isinstance(start, bool) or not isinstance(start, int) or start < 0:
        raise CoreInvariantError("a writer's start minute is a whole minute at or after 0")
    if stop is not None and (isinstance(stop, bool) or not isinstance(stop, int) or stop <= start):
        raise CoreInvariantError("a writer's stop minute is a whole minute after its start, or None (open)")


def _active(minute: int, start: int, stop) -> bool:
    return minute >= start and (stop is None or minute < stop)


@register
@dataclass(frozen=True)
class OpioidCentralDepression(Contributor):
    kind = SourceKind.DISEASE_MODULE
    type_name = "opioid_central_depression"

    id: str
    deepening_per_min: float
    start_minute: int = 0
    stop_minute: int | None = None

    def __post_init__(self):
        _fraction(self.deepening_per_min, "central depression's deepening")
        _minutes(self.start_minute, self.stop_minute)

    def contribute(self, state, minute, signals, anchors, profile):
        if not state.R.pulse_present or self.deepening_per_min <= 0.0 \
                or not _active(minute, self.start_minute, self.stop_minute):
            return Contribution()
        loss = self.deepening_per_min * state.aux.central_availability
        if loss <= 0.0:
            return Contribution()
        return Contribution(availability=(AvailabilityChange(-loss, self.source, minute,
                                                             "opioid central respiratory depression deepening"),))


@register
@dataclass(frozen=True)
class NaloxoneReversal(Contributor):
    kind = SourceKind.INTERVENTION
    type_name = "naloxone_reversal"

    id: str
    recovery_per_min: float
    start_minute: int = 0
    stop_minute: int | None = None

    def __post_init__(self):
        _fraction(self.recovery_per_min, "antagonist's recovery")
        _minutes(self.start_minute, self.stop_minute)

    def contribute(self, state, minute, signals, anchors, profile):
        if not state.R.pulse_present or self.recovery_per_min <= 0.0 \
                or not _active(minute, self.start_minute, self.stop_minute):
            return Contribution()
        gain = self.recovery_per_min * (1.0 - state.aux.central_availability)
        if gain <= 0.0:
            return Contribution()
        return Contribution(availability=(AvailabilityChange(gain, self.source, minute,
                                                             "opioid antagonist restoring the central drive"),))
