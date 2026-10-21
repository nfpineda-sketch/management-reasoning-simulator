"""Crystalloid and packed red cells: volume (C1) and haemoglobin (C10).

The magnitudes are parameters of each order, supplied by whoever builds the scenario.
The shadow comparison supplies the family engine's own (GI_BLEED and _minute), converted
to mL-equivalents; nothing here is fitted to a trajectory.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from ..integration import Contribution, Contributor, register
from ..provenance import ChannelDelta, SourceKind
from ..state import Channel, CoreInvariantError
from .timing import check_window, given_in


def _positive(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise CoreInvariantError(f"{name} must be a positive number")


def _duration(value):
    if value is not None:
        _positive(value, "duration_min")


@register
@dataclass(frozen=True)
class Crystalloid(Contributor):
    """Expands volume on delivery; part of the expansion then leaves the vessels.

    Per mL delivered: V rises by ``effective_ml_per_ml``; ``transient_share`` of that
    rise enters a pool that redistributes out of the circulation with time constant
    ``leak_tau_min``; Hb falls by ``hb_dilution_g_dl_per_ml``.
    """

    kind = SourceKind.INTERVENTION
    type_name = "crystalloid"

    id: str
    start_minute: int
    volume_ml: float
    duration_min: float | None
    untimed_rate_ml_per_min: float
    effective_ml_per_ml: float
    transient_share: float
    leak_tau_min: float
    hb_dilution_g_dl_per_ml: float
    stop_minute: int | None = None

    def __post_init__(self):
        check_window(self.start_minute, self.stop_minute)
        for name in ("volume_ml", "untimed_rate_ml_per_min", "effective_ml_per_ml", "leak_tau_min"):
            _positive(getattr(self, name), name)
        _duration(self.duration_min)
        if not 0.0 <= self.transient_share <= 1.0 or self.hb_dilution_g_dl_per_ml < 0:
            raise CoreInvariantError("the transient share is between 0 and 1 and dilution is not negative")

    def _given(self, minute):
        return given_in(minute, amount=self.volume_ml, start_minute=self.start_minute, duration_min=self.duration_min,
                        untimed_rate_per_min=self.untimed_rate_ml_per_min, stop_minute=self.stop_minute)

    def contribute(self, state, minute, signals, anchors, profile):
        own = self.own(state)
        pool = float(own.get("pool_ml", 0.0))
        given = self._given(minute)
        if given == 0.0 and pool == 0.0:
            return Contribution()
        gain = given * self.effective_ml_per_ml
        pool += gain * self.transient_share
        leak = pool * (1 - math.exp(-1 / self.leak_tau_min))
        pool -= leak
        deltas = []
        if given:
            deltas += [ChannelDelta(Channel.V, gain, self.source, minute, "crystalloid delivered into the circulation"),
                       ChannelDelta(Channel.HB, -given * self.hb_dilution_g_dl_per_ml, self.source, minute,
                                    "haemoglobin diluted by crystalloid")]
        if leak:
            deltas.append(ChannelDelta(Channel.V, -leak, self.source, minute,
                                       "crystalloid redistributing out of the circulation"))
        delivered = float(own.get("delivered_ml", 0.0)) + given
        return Contribution(deltas=tuple(deltas), internal=own.updated(pool_ml=pool, delivered_ml=delivered))


@register
@dataclass(frozen=True)
class PackedRedCells(Contributor):
    """Each unit delivered adds volume that stays in the vessels and oxygen-carrying capacity.

    Transfusion overload (the family engine's TRANSFUSION rule) acts on lung water (C5),
    which no module writes yet: it is not modelled here, and the comparison says so.
    """

    kind = SourceKind.INTERVENTION
    type_name = "packed_red_cells"

    id: str
    start_minute: int
    units: float
    duration_min: float | None
    untimed_units_per_min: float
    volume_ml_per_unit: float
    hb_g_dl_per_unit: float
    stop_minute: int | None = None

    def __post_init__(self):
        check_window(self.start_minute, self.stop_minute)
        for name in ("units", "untimed_units_per_min", "volume_ml_per_unit", "hb_g_dl_per_unit"):
            _positive(getattr(self, name), name)
        _duration(self.duration_min)

    def contribute(self, state, minute, signals, anchors, profile):
        given = given_in(minute, amount=self.units, start_minute=self.start_minute, duration_min=self.duration_min,
                         untimed_rate_per_min=self.untimed_units_per_min, stop_minute=self.stop_minute)
        if not given:
            return Contribution()
        own = self.own(state)
        return Contribution(
            deltas=(ChannelDelta(Channel.V, given * self.volume_ml_per_unit, self.source, minute,
                                 "packed red cells delivered into the circulation"),
                    ChannelDelta(Channel.HB, given * self.hb_g_dl_per_unit, self.source, minute,
                                 "haemoglobin raised by transfusion")),
            internal=own.updated(delivered_units=float(own.get("delivered_units", 0.0)) + given))
