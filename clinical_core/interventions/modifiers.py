"""Orders that act only by modulating a module's mechanism (proposal §7.6).

A proton-pump inhibitor has no short-term channel effect of its own. While it runs it
publishes a signal; the haemorrhage module, which declares that it responds to it, slows
the bleeding and names this order as the modulator of its deltas.
"""
from __future__ import annotations

from dataclasses import dataclass

from .. import signals as names
from ..integration import Contributor, Signal, register
from ..provenance import SourceKind
from ..state import CoreInvariantError
from .timing import check_window


@register
@dataclass(frozen=True)
class ProtonPumpInhibitor(Contributor):
    kind = SourceKind.INTERVENTION
    type_name = "proton_pump_inhibitor"

    id: str
    start_minute: int
    stop_minute: int | None = None

    def __post_init__(self):
        check_window(self.start_minute, self.stop_minute, whole_start=True)
        if self.stop_minute is not None and self.stop_minute <= self.start_minute:
            raise CoreInvariantError("a proton-pump inhibitor stops after it starts")

    def signals(self, minute):
        if minute <= self.start_minute or (self.stop_minute is not None and minute > self.stop_minute):
            return ()
        return (Signal(names.PPI, self.source, self.start_minute),)
