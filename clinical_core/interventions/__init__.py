"""Interventions (proposal §7.6): each declares its channel effects, keeps its order's identity
as its source id, and starts and stops at the minutes its specification states.

The specification is deliberately plain (order id, start, stop, amounts). An adapter
from Phase 1's ``OrderAction`` v2 will build these; until that contract is final, the
only adapter is the one that reads the family engine's parsed actions.
"""
from .fluids import Crystalloid, PackedRedCells
from .modifiers import ProtonPumpInhibitor
from .oxygen import Oxygen

__all__ = ["Crystalloid", "Oxygen", "PackedRedCells", "ProtonPumpInhibitor"]
