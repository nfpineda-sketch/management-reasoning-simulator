"""Logistic processes as the core sees them (proposal §10.3).

The staged process -- request, acceptance, preparation, procedure -- and the decision of
when a procedure can happen belong to the scheduler (Phase 1). The core receives only the
completion: from that minute on the process publishes a signal, and the module that owns
the mechanism (here, the haemorrhage module) acts on it. A process never writes a
channel itself.
"""
from __future__ import annotations

from dataclasses import dataclass

from . import signals as names
from .integration import Contribution, Contributor, Signal, register
from .provenance import CoreEvent, SourceKind
from .state import CoreInvariantError


@register
@dataclass(frozen=True)
class EndoscopicHemostasis(Contributor):
    kind = SourceKind.LOGISTIC_PROCESS
    type_name = "endoscopic_hemostasis"

    id: str
    completes_at_minute: int

    def __post_init__(self):
        if isinstance(self.completes_at_minute, bool) or not isinstance(self.completes_at_minute, int) \
                or self.completes_at_minute < 1:
            raise CoreInvariantError("a procedure completes at a minute >= 1")

    def signals(self, minute):
        if minute < self.completes_at_minute:
            return ()
        return (Signal(names.ENDOSCOPIC_HEMOSTASIS, self.source, self.completes_at_minute),)

    def contribute(self, state, minute, signals, anchors, profile):
        if minute != self.completes_at_minute:
            return Contribution()
        return Contribution(events=(CoreEvent("procedure_completed", self.source, minute, "info", "logistic_process",
                                              "not applicable", "upper endoscopy completed with hemostasis"),))
