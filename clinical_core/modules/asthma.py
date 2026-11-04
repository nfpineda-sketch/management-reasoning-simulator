"""Acute asthma as a shadow family writer (P2S-3, family asthma). Shadow only, off unless built into a run.

The family owns its disease process, never an observable (proposal §8.1 point 3):
- ``AirwayObstruction`` is the family's airflow obstruction: it writes the common respiratory mechanics efficiency only
  (``provenance.MechanicsChange``, the P2S-2 target), a declared fraction of it lost per minute while the obstruction
  worsens untreated. The expressed RR, W, PaCO2, pH, SpO2, delivery, D, lactate, HR and consciousness follow in the
  common core, never from here; it writes no channel, no demand and no blood flow. The core refuses its changes unless
  the respiratory mechanics candidate is on.

No bronchodilator, steroid or fatigue writer exists: the shadow core has no bronchodilator action and no post-treatment
course is authored (BRONCHODILATOR_WRITER_DEFERRED, STEROID_ACUTE_PHYSIOLOGY_DEFERRED); fatigue memory is not authorized.
No value here is approved: the worsening rate is a SYNTHETIC_ONLY span a run declares.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from ..integration import Contribution, Contributor, register
from ..provenance import MechanicsChange, SourceKind
from ..state import CoreInvariantError


@register
@dataclass(frozen=True)
class AirwayObstruction(Contributor):
    kind = SourceKind.DISEASE_MODULE
    type_name = "asthma_airway_obstruction"

    id: str
    worsening_per_min: float

    def __post_init__(self):
        value = self.worsening_per_min
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) \
                or not 0.0 <= value < 1.0:
            raise CoreInvariantError("the airway obstruction's worsening is a finite fraction per minute in [0, 1)")

    def contribute(self, state, minute, signals, anchors, profile):
        if not state.R.pulse_present or self.worsening_per_min <= 0.0:
            return Contribution()
        return Contribution(mechanics=(MechanicsChange(1.0 - self.worsening_per_min, self.source, minute,
                                                       "airflow obstruction worsening (untreated)"),))
