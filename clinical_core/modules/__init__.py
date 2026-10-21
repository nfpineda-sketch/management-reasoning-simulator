"""Disease-specific modules (proposal §8). Each owns its mechanism and writes only declared channel deltas."""
from .gi_haemorrhage import GIHaemorrhage
from .rhythm_events import ScriptedPumpChange, ScriptedRhythmEvent

__all__ = ["GIHaemorrhage", "ScriptedPumpChange", "ScriptedRhythmEvent"]
