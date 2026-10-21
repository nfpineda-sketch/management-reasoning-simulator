"""Upper gastrointestinal haemorrhage as a shadow module (proposal §8.2, cluster V / Hb / D).

The module owns the bleeding source: its untreated rate (a case parameter), the
slowing a proton-pump inhibitor brings before endoscopy, and the residual rate once
the source is treated. It writes only V- and Hb-. Pressure, rate, refill, lactate and
breathing follow from those channels in the core (``derived``); this module never
writes an observable, which is the main change from the family engine (§8.1 point 3).

It does not decide when the endoscopy happens: that is a logistic process whose
completion arrives as a signal (§10.3). It does not model anticoagulation; a scenario
that needs it is refused by whoever builds the scenario.
"""
from __future__ import annotations

from dataclasses import dataclass

from .. import signals as names
from ..integration import Contribution, Contributor, register
from ..provenance import ChannelDelta, CoreEvent, SourceKind
from ..state import Channel, CoreInvariantError


@register
@dataclass(frozen=True)
class GIHaemorrhage(Contributor):
    kind = SourceKind.DISEASE_MODULE
    type_name = "gi_haemorrhage"
    responds_to = frozenset({names.PPI, names.ENDOSCOPIC_HEMOSTASIS})

    id: str
    volume_loss_ml_per_min: float
    hb_loss_g_dl_per_min: float
    fraction_with_ppi: float
    fraction_after_hemostasis: float

    def __post_init__(self):
        if self.volume_loss_ml_per_min < 0 or self.hb_loss_g_dl_per_min < 0:
            raise CoreInvariantError("a bleeding rate is not negative")
        for name in ("fraction_with_ppi", "fraction_after_hemostasis"):
            if not 0.0 <= getattr(self, name) <= 1.0:
                raise CoreInvariantError(f"{name} is a share of the untreated rate, between 0 and 1")

    def contribute(self, state, minute, signals, anchors, profile):
        own = self.own(state)
        hemostasis = tuple(s for s in self.heard(signals, names.ENDOSCOPIC_HEMOSTASIS) if s.since_minute <= minute)
        ppi = tuple(s for s in self.heard(signals, names.PPI) if s.since_minute < minute)
        if hemostasis:
            fraction, modulators, why = self.fraction_after_hemostasis, hemostasis, "after endoscopic hemostasis"
        elif ppi:
            fraction, modulators, why = self.fraction_with_ppi, ppi, "slowed by a proton-pump inhibitor"
        else:
            fraction, modulators, why = 1.0, (), "untreated"
        by = tuple(signal.source for signal in modulators)
        deltas = (
            ChannelDelta(Channel.V, -self.volume_loss_ml_per_min * fraction, self.source, minute,
                         f"blood lost from the upper GI source ({why})", by),
            ChannelDelta(Channel.HB, -self.hb_loss_g_dl_per_min * fraction, self.source, minute,
                         f"haemoglobin falling with the bleeding ({why})", by),
        )
        controlled_at = own.get("controlled_at")
        events = ()
        if hemostasis and controlled_at is None:
            controlled_at = minute
            events = (CoreEvent("source_controlled", self.source, minute, "significant", "logistic_process",
                                "not applicable", "bleeding source controlled; residual bleeding continues"),)
        return Contribution(deltas=deltas, events=events,
                            internal=own.updated(controlled_at=controlled_at, bleeding_fraction=fraction))
