"""Acute pulmonary embolism / obstructive right-ventricular physiology as shadow family writers (P2Q-2, family
pulmonary_embolism). Shadow only, off unless built into a run.

The family owns its disease process, never an observable (proposal §8.1 point 3):
- ``ObstructiveForwardFlow`` owns the obstruction on the common P channel. Canonical P is unsided: the forward-flow
  capacity of the heart and lungs in series at a given filling (arrival = 1). The pulmonary-vascular obstruction and the
  right ventricle it overloads limit that flow, so the family writes it there and never calls it left-ventricular
  contractility (the authored LV contracts vigorously). While the obstruction is not relieved it lowers P by a declared
  amount per minute, never below a declared floor. It writes P only: output, pressure, delivery, the deficit, D, lactate,
  the heart rate, tone and collapse follow in the common core. It never writes V: the LV underfilling the obstruction
  causes is the case's arrival preload position (``embolism_reference``), and V moves only with the shared blood state,
  so the obstruction is never encoded twice.
- ``EmbolicGasExchange`` owns the embolic gas-exchange impairment (dead space, V/Q mismatch) on the common G channel,
  directly, never through L: it adds a declared amount of G per minute while the obstruction is not relieved. The common
  G -> SpO2 -> delivery path and the common FiO2 response follow; no lung-water credit (L_rev) ever reaches it.
- ``EmbolicLungWater`` is the family's owner of lung water (``lung_water_authority``, P2O-3). The core's overload
  coupling (``derived.congestion_rate``) reads an unsided pump and cannot tell left-ventricular from right-ventricular /
  obstructive failure, so it must not infer left pulmonary congestion here: while this owner is present it adds nothing
  (faculty decision PE_L_ZERO_OWNER_AUTHORIZED). The owner's own generation is a declared rate, zero unless the case
  independently authors pulmonary edema. One owner of L per run (P2O-3); the clearance and every reader of L stay common.

No relief (reperfusion) and no treatment effect is modelled: anticoagulation, thrombolysis and their timing are
deferred. No value here is approved: every rate and floor is a FAMILY_CANDIDATE or SYNTHETIC_ONLY value a run declares.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from ..integration import Contribution, Contributor, register
from ..provenance import ChannelDelta, SourceKind
from ..state import Channel, CoreInvariantError


def _rate(value, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0.0:
        raise CoreInvariantError(f"the {name} is finite and not negative")


@register
@dataclass(frozen=True)
class ObstructiveForwardFlow(Contributor):
    kind = SourceKind.DISEASE_MODULE
    type_name = "pe_obstructive_forward_flow"

    id: str
    loss_per_min: float
    floor: float

    def __post_init__(self):
        _rate(self.loss_per_min, "obstruction's loss of forward flow per minute")
        if isinstance(self.floor, bool) or not isinstance(self.floor, (int, float)) or not 0.0 < self.floor <= 1.0:
            raise CoreInvariantError("the obstruction floor is in (0, 1]: the obstruction never stops the circuit")

    def contribute(self, state, minute, signals, anchors, profile):
        if not state.R.pulse_present:
            return Contribution()
        amount = -min(self.loss_per_min, max(0.0, state.P - self.floor))
        if amount >= 0.0:
            return Contribution()
        return Contribution(deltas=(ChannelDelta(Channel.P, amount, self.source, minute,
                                                 "pulmonary-vascular obstruction limits forward flow (unsided P)"),))


@register
@dataclass(frozen=True)
class EmbolicGasExchange(Contributor):
    kind = SourceKind.DISEASE_MODULE
    type_name = "pe_embolic_gas_exchange"

    id: str
    impairment_per_min: float

    def __post_init__(self):
        _rate(self.impairment_per_min, "embolic gas-exchange impairment per minute")

    def contribute(self, state, minute, signals, anchors, profile):
        if not state.R.pulse_present or self.impairment_per_min <= 0.0:
            return Contribution()
        return Contribution(deltas=(ChannelDelta(Channel.G, self.impairment_per_min, self.source, minute,
                                                 "embolic dead space / V/Q mismatch worsening (direct G)"),))


@register
@dataclass(frozen=True)
class EmbolicLungWater(Contributor):
    kind = SourceKind.DISEASE_MODULE
    type_name = "pe_lung_water"
    #: P2O-3 / P2Q-2: the family owns lung water; the core's unsided overload coupling adds nothing while it is present.
    lung_water_authority = True

    id: str
    congestion_per_min: float = 0.0

    def __post_init__(self):
        _rate(self.congestion_per_min, "authored pulmonary-edema generation per minute")

    def contribute(self, state, minute, signals, anchors, profile):
        if not state.R.pulse_present or self.congestion_per_min <= 0.0:
            return Contribution()
        return Contribution(deltas=(ChannelDelta(Channel.L, self.congestion_per_min, self.source, minute,
                                                 "pulmonary edema authored independently of the embolism"),))
