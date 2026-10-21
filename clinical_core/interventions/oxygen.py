"""Supplemental oxygen sets FiO2, a support setting the core reads (proposal §7.3: SpO2 = f(G, L, W, FiO2)).

FiO2 is one setting: the latest oxygen order to start holds it. Stopping an order returns
the patient to the arrival FiO2 only when no other oxygen order is running; a stop that
would leave another order's FiO2 undefined fails closed rather than guessing.
"""
from __future__ import annotations

from dataclasses import dataclass

from .. import signals as names
from ..integration import Contribution, Contributor, Signal, register
from ..provenance import SettingChange, SourceKind
from ..state import CoreInvariantError
from .timing import check_window

ROOM_AIR = 0.21


@register
@dataclass(frozen=True)
class Oxygen(Contributor):
    kind = SourceKind.INTERVENTION
    type_name = "oxygen"
    responds_to = frozenset({names.OXYGEN})

    id: str
    start_minute: int
    fio2: float
    stop_minute: int | None = None

    def __post_init__(self):
        check_window(self.start_minute, self.stop_minute, whole_start=True)
        if self.stop_minute is not None and self.stop_minute <= self.start_minute:
            raise CoreInvariantError("an oxygen order stops after it starts")
        if isinstance(self.fio2, bool) or not isinstance(self.fio2, (int, float)) or not ROOM_AIR <= self.fio2 <= 1.0:
            raise CoreInvariantError("FiO2 is between 0.21 and 1.0")

    def _running(self, minute) -> bool:
        return self.start_minute < minute and (self.stop_minute is None or minute <= self.stop_minute)

    def signals(self, minute):
        return (Signal(names.OXYGEN, self.source, self.start_minute),) if self._running(minute) else ()

    def contribute(self, state, minute, signals, anchors, profile):
        if minute == self.start_minute + 1:
            return Contribution(settings=(SettingChange("fio2", float(self.fio2), self.source, minute,
                                                        "supplemental oxygen started"),))
        if self.stop_minute is not None and minute == self.stop_minute + 1:
            others = [signal for signal in self.heard(signals, names.OXYGEN) if signal.source != self.source]
            if others:
                raise CoreInvariantError("an oxygen order stopped while another runs: the FiO2 left is not defined")
            return Contribution(settings=(SettingChange("fio2", anchors.fio2, self.source, minute,
                                                        "supplemental oxygen stopped; arrival FiO2"),))
        return Contribution()
