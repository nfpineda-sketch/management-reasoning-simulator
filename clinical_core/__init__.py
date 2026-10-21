"""Common physiologic core -- Phase 2, SHADOW MODE ONLY.

This package implements the shared channels of
``docs/CLINICAL_ENGINE_ARCHITECTURE_PROPOSAL.md`` §7-§8 so that they can run *beside*
the family engine and be compared with it. The family engine remains the source of
truth for every encounter: no runtime module imports this package, nothing here
reads or writes ``st.session_state``, the Management Trace, receipts, events,
observations or persistence, and no value computed here reaches a resident.

Layout:
- ``state``: typed, immutable, serializable state (channels C1-C12, rhythm state machine).
- ``provenance``: the source of every applied change.
- ``derived``: observation-ready values (numbers and codes only, never narrative).
- ``integration``: the deterministic minute integrator and replayable trajectories.
"""
from .derived import DEFAULT_PROFILE, PARAMETERS, CoreProfile, Derived, derive
from .integration import (CHANNEL_BOUNDS, Contribution, Contributor, Signal, Trajectory, register, run,
                          scenario_from_dict, scenario_to_dict, step)
from .provenance import (ChannelDelta, CoreEvent, MinuteRecord, ProvenanceError, RhythmTransition,
                         SettingChange, Source, SourceKind, attribution)
from .state import (Anchors, Channel, CoreInvariantError, CoreState, FrozenRecord, RhythmCode, RhythmState,
                    initial_state)

CORE_VERSION = "0.1.0-shadow"
#: The engine this core is compared against. It stays authoritative.
AUTHORITATIVE_ENGINE = "family_engine"
SHADOW_ONLY = True

__all__ = [
    "AUTHORITATIVE_ENGINE", "CHANNEL_BOUNDS", "CORE_VERSION", "DEFAULT_PROFILE", "PARAMETERS", "SHADOW_ONLY",
    "Anchors", "Channel", "ChannelDelta", "Contribution", "Contributor", "CoreEvent", "CoreInvariantError",
    "CoreProfile", "CoreState", "Derived", "FrozenRecord", "MinuteRecord", "ProvenanceError", "RhythmCode",
    "RhythmState", "RhythmTransition", "SettingChange", "Signal", "Source", "SourceKind", "Trajectory",
    "attribution", "derive", "initial_state", "register", "run", "scenario_from_dict", "scenario_to_dict", "step",
]
