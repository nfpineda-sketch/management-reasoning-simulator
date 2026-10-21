"""Supplemental oxygen sets FiO2, a support setting the core reads (proposal §7.3: SpO2 = f(G, L, W, FiO2))."""
from __future__ import annotations

from dataclasses import dataclass

from ..integration import Contribution, Contributor, register
from ..provenance import SettingChange, SourceKind
from ..state import CoreInvariantError
from .timing import check_window

ROOM_AIR = 0.21


@register
@dataclass(frozen=True)
class Oxygen(Contributor):
    kind = SourceKind.INTERVENTION
    type_name = "oxygen"

    id: str
    start_minute: int
    fio2: float
    stop_minute: int | None = None

    def __post_init__(self):
        check_window(self.start_minute, self.stop_minute)
        if isinstance(self.fio2, bool) or not isinstance(self.fio2, (int, float)) or not ROOM_AIR <= self.fio2 <= 1.0:
            raise CoreInvariantError("FiO2 is between 0.21 and 1.0")

    def contribute(self, state, minute, signals, anchors, profile):
        if minute == self.start_minute + 1:
            return Contribution(settings=(SettingChange("fio2", float(self.fio2), self.source, minute,
                                                        "supplemental oxygen started"),))
        if self.stop_minute is not None and minute == self.stop_minute + 1:
            return Contribution(settings=(SettingChange("fio2", ROOM_AIR, self.source, minute,
                                                        "supplemental oxygen stopped; room air"),))
        return Contribution()
