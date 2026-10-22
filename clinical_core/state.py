"""Typed, immutable state of the common physiologic core (Phase 2, shadow mode only).

Channel definitions follow ``docs/CLINICAL_ENGINE_ARCHITECTURE_PROPOSAL.md`` §7.2. Every
channel is either a multiplier whose arrival value is 1 (T, P) or a deviation from the
patient's authored arrival state, whose arrival value is 0 (V, L, G, W, D, N); the
chemistry values (Hb, glucose, K) are absolute and come from the case. This is the
anchoring rule of §7.4: observables are later derived as authored arrival values plus
mapped deviations, so no channel needs a default the case did not author.

Nothing here formats anything a resident reads. The state is serializable to canonical
JSON and has a stable digest, so a trajectory can be replayed and compared exactly.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field, fields, replace
from enum import Enum
from typing import Any, Iterable, Mapping


class CoreInvariantError(ValueError):
    """A state that cannot exist. The core fails closed instead of carrying it forward."""


class UnresolvedBoundary(CoreInvariantError):
    """The model reached a boundary whose rule is not yet decided (e.g. the arrest threshold).

    No rule is invented: the run stops here, and the message names the boundary (P2D-2).
    """


class Channel(str, Enum):
    """The nine physiological channels and the three chemistry values (proposal §7.2)."""

    V = "V"            # C1 intravascular volume, mL-equivalent deviation from arrival
    T = "T"            # C2 vascular tone, multiplier (arrival = 1)
    P = "P"            # C3 pump performance, multiplier (arrival = 1)
    R = "R"            # C4 rhythm and pulse state: a state machine, changed only by transitions
    L = "L"            # C5 lung water / congestion, index deviation from arrival
    G = "G"            # C6 gas exchange impairment, deviation from arrival
    W = "W"            # C7 ventilation relative to need (drive, mechanics, fatigue), deviation
    D = "D"            # C8 oxygen-delivery debt, deviation from arrival (index-minutes)
    N = "N"            # C9 CNS depression level, deviation from arrival
    HB = "hb"          # C10 haemoglobin, g/dL
    GLUCOSE = "glucose"  # C11 glucose, mg/dL
    K = "k"            # C12 potassium, mmol/L


SCALAR_CHANNELS = tuple(channel for channel in Channel if channel is not Channel.R)

#: What each channel means, in the proposal's own words, and the unit the core keeps it in.
CHANNEL_DEFINITIONS: Mapping[Channel, tuple[str, str, str]] = {
    Channel.V: ("C1", "mL-equivalent deviation from arrival", "Intravascular volume"),
    Channel.T: ("C2", "multiplier, arrival = 1", "Vascular tone"),
    Channel.P: ("C3", "multiplier, arrival = 1", "Pump performance"),
    Channel.R: ("C4", "state machine: code, rate, effective-output factor, pulse", "Rhythm and pulse state"),
    Channel.L: ("C5", "index deviation from arrival", "Lung water / congestion"),
    Channel.G: ("C6", "shunt / V-Q impairment deviation from arrival", "Gas exchange"),
    Channel.W: ("C7", "deviation of alveolar ventilation relative to need", "Ventilation"),
    Channel.D: ("C8", "index-minutes, deviation from arrival", "Oxygen-delivery debt"),
    Channel.N: ("C9", "level deviation from arrival", "CNS depression / neurological state"),
    Channel.HB: ("C10", "g/dL", "Haemoglobin"),
    Channel.GLUCOSE: ("C11", "mg/dL", "Glucose"),
    Channel.K: ("C12", "mmol/L", "Potassium"),
}


class RhythmCode(str, Enum):
    """Rhythm labels the core can hold. Naming them for a resident is the observation layer's job."""

    SINUS = "sinus"
    AF = "af"
    SVT = "svt"
    COMPLETE_AV_BLOCK = "complete_av_block"
    PACED = "paced"
    VT_WITH_PULSE = "vt_with_pulse"
    PULSELESS_VT = "pulseless_vt"
    VF = "vf"
    PEA = "pea"
    ASYSTOLE = "asystole"


#: Proposal §11.4: a missing pulse means exactly one of these rhythms, and these rhythms
#: never have a pulse.
NON_PERFUSING = frozenset({RhythmCode.PULSELESS_VT, RhythmCode.VF, RhythmCode.PEA, RhythmCode.ASYSTOLE})
#: Fibrillation has no organized rate to count; every other rhythm has one.
RATELESS = frozenset({RhythmCode.VF})


def _finite(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise CoreInvariantError(f"{name} must be a finite number, not {value!r}")
    return float(value)


@dataclass(frozen=True)
class RhythmState:
    """C4: the rhythm the heart is in, its rate, its effective-output factor and the pulse.

    The combinations the proposal forbids (§11.4) cannot be constructed: a pulseless
    "sinus" rhythm, a rate of 0 that is not asystole, a VF with a counted rate, or a
    non-perfusing rhythm that still produces output all raise ``CoreInvariantError``.
    """

    code: RhythmCode
    rate_bpm: float | None
    output_factor: float
    pulse_present: bool

    def __post_init__(self):
        if not isinstance(self.code, RhythmCode):
            object.__setattr__(self, "code", RhythmCode(self.code))
        if not isinstance(self.pulse_present, bool):
            raise CoreInvariantError("pulse_present must be a bool")
        output = _finite(self.output_factor, "output_factor")
        if not 0.0 <= output <= 1.5:
            raise CoreInvariantError(f"output_factor {output} outside [0, 1.5]")
        if self.code in RATELESS:
            if self.rate_bpm is not None:
                raise CoreInvariantError(f"{self.code.value} has no countable rate")
        else:
            rate = _finite(self.rate_bpm, "rate_bpm")
            if not 0.0 <= rate <= 300.0:
                raise CoreInvariantError(f"rate {rate} outside [0, 300]")
            if (rate == 0.0) != (self.code is RhythmCode.ASYSTOLE):
                raise CoreInvariantError("a rate of 0 is asystole, and asystole has a rate of 0")
        non_perfusing = self.code in NON_PERFUSING
        if non_perfusing == self.pulse_present:
            raise CoreInvariantError(
                f"{self.code.value} with pulse_present={self.pulse_present}: a pulse is present "
                "exactly when the rhythm perfuses")
        if non_perfusing and output != 0.0:
            raise CoreInvariantError(f"{self.code.value} produces no output")
        if not non_perfusing and output <= 0.0:
            raise CoreInvariantError(f"a perfusing {self.code.value} must produce output")

    @property
    def perfusing(self) -> bool:
        return self.pulse_present

    def to_dict(self) -> dict:
        return {"code": self.code.value, "rate_bpm": self.rate_bpm, "output_factor": self.output_factor,
                "pulse_present": self.pulse_present}

    @classmethod
    def from_dict(cls, data: Mapping) -> "RhythmState":
        return cls(RhythmCode(data["code"]), data["rate_bpm"], data["output_factor"], data["pulse_present"])

    @classmethod
    def sinus(cls, rate_bpm: float) -> "RhythmState":
        return cls(RhythmCode.SINUS, rate_bpm, 1.0, True)

    @classmethod
    def asystole(cls) -> "RhythmState":
        return cls(RhythmCode.ASYSTOLE, 0.0, 0.0, False)

    @classmethod
    def vf(cls) -> "RhythmState":
        return cls(RhythmCode.VF, None, 0.0, False)

    @classmethod
    def pea(cls, rate_bpm: float) -> "RhythmState":
        return cls(RhythmCode.PEA, rate_bpm, 0.0, False)


_PRIMITIVE = (str, int, float, bool, type(None))


class FrozenRecord(Mapping):
    """An immutable, ordered, JSON-serializable mapping for a contributor's internal state."""

    __slots__ = ("_items",)

    def __init__(self, data: Mapping | Iterable[tuple[str, Any]] = ()):
        items = data.items() if isinstance(data, Mapping) else data
        frozen = []
        for key, value in items:
            if not isinstance(key, str):
                raise CoreInvariantError(f"internal-state keys are strings, not {key!r}")
            frozen.append((key, _freeze(value)))
        object.__setattr__(self, "_items", tuple(sorted(frozen)))

    def __setattr__(self, name, value):
        raise AttributeError("FrozenRecord is immutable")

    def __reduce__(self):
        # Copies and pickles rebuild the record from its frozen items: never by setting attributes.
        return (FrozenRecord, (self._items,))

    def __getitem__(self, key):
        for item_key, value in self._items:
            if item_key == key:
                return value
        raise KeyError(key)

    def __iter__(self):
        return (key for key, _ in self._items)

    def __len__(self):
        return len(self._items)

    def __eq__(self, other):
        return isinstance(other, FrozenRecord) and self._items == other._items

    def __hash__(self):
        return hash(self._items)

    def __repr__(self):
        return f"FrozenRecord({dict(self._items)!r})"

    def updated(self, **changes) -> "FrozenRecord":
        data = dict(self._items)
        data.update(changes)
        return FrozenRecord(data)

    def to_dict(self) -> dict:
        return {key: _thaw(value) for key, value in self._items}


def _thaw(value):
    if isinstance(value, FrozenRecord):
        return value.to_dict()
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


def _freeze(value):
    if isinstance(value, FrozenRecord):
        return value
    if isinstance(value, Mapping):
        return FrozenRecord(value)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, float) and not math.isfinite(value):
        raise CoreInvariantError("internal state holds only finite numbers")
    if isinstance(value, _PRIMITIVE):
        return value
    raise CoreInvariantError(f"internal state holds primitives, records and tuples, not {type(value).__name__}")


EMPTY = FrozenRecord()


#: The case parameters (P2C) and their neutral values: what the core assumes when a case does
#: not declare one (``None``: the profile's provisional default).
CASE_PARAMETERS: Mapping[str, Any] = {"beta_blockade": 0.0, "preload_fraction": None, "pump_reserve": 1.0}
#: Where a declared case parameter comes from (P2D-8). One that is not declared is "default".
DECLARED_SOURCES = frozenset({"explicit_case", "synthetic_probe"})


@dataclass(frozen=True)
class Anchors:
    """The authored arrival state a case gives the core (§7.4).

    The authored arrival values have no default. ``consciousness_level`` uses the engine's
    existing ladder: 0 alert, 1 drowsy, 2 obtunded, 3 unresponsive.

    The case declarations after them default to neutral, meaning "not declared":
    - ``beta_blockade`` (0 none, 1 complete) blunts the chronotropic response to sympathetic
      drive (proposal §7.3: "modulated by beta-blockade, a case parameter");
    - ``preload_fraction`` is where arrival sits on the preload curve, as a share of the
      output preload alone could reach (0 empty, 1 the plateau); ``None`` takes the profile's
      provisional default (KD-S4). A low value is a preload-dependent patient;
    - ``pump_reserve`` (0 none, 1 normal) is how much excess preload the pump can take before
      it congests the lungs (KD-S4).

    ``declared`` names the source of every case parameter that is declared (P2D-8):
    ``explicit_case`` (the case states it) or ``synthetic_probe`` (a test or a Level-2 probe).
    A value other than the neutral one must be declared: none is ever inferred silently.
    """

    case_id: str
    sbp: float
    dbp: float
    hr: float
    spo2: float
    respiratory_rate: float
    crt_s: float
    lactate: float
    hb: float
    glucose: float
    k: float
    fio2: float
    rhythm: RhythmState
    consciousness_level: int
    beta_blockade: float = 0.0
    preload_fraction: float | None = None
    pump_reserve: float = 1.0
    declared: FrozenRecord = field(default=EMPTY)

    def __post_init__(self):
        if not self.case_id:
            raise CoreInvariantError("anchors name their case")
        if not isinstance(self.declared, FrozenRecord):
            object.__setattr__(self, "declared", FrozenRecord(self.declared))
        for item in fields(self):
            if item.name not in {"case_id", "rhythm", "consciousness_level", "declared"} \
                    and not (item.name == "preload_fraction" and self.preload_fraction is None):
                _finite(getattr(self, item.name), item.name)
        for name, source in self.declared.items():
            if name not in CASE_PARAMETERS or source not in DECLARED_SOURCES:
                raise CoreInvariantError(f"case parameter {name!r} declared from {source!r}: expected one of "
                                         f"{sorted(CASE_PARAMETERS)} from one of {sorted(DECLARED_SOURCES)}")
        for name, neutral in CASE_PARAMETERS.items():
            if getattr(self, name) != neutral and name not in self.declared:
                raise CoreInvariantError(f"case parameter {name} = {getattr(self, name)!r} is not the neutral value "
                                         "and names no source (explicit_case or synthetic_probe)")
        if not 0.0 <= self.beta_blockade <= 1.0:
            raise CoreInvariantError("beta-blockade is between 0 (none) and 1 (complete)")
        if self.preload_fraction is not None and not 0.0 < self.preload_fraction < 1.0:
            raise CoreInvariantError("the arrival preload fraction is strictly between 0 and 1")
        if not 0.0 <= self.pump_reserve <= 1.0:
            raise CoreInvariantError("pump reserve is between 0 (none) and 1 (normal)")
        if not isinstance(self.rhythm, RhythmState):
            raise CoreInvariantError("the arrival rhythm is a RhythmState")
        if not self.rhythm.pulse_present:
            # Every deviation is read against arrival; an arrival in arrest has no output to read
            # against, and resuscitation is not modelled (proposal Appendix A5).
            raise CoreInvariantError("the core does not start an encounter in arrest")
        if not (self.hb > 0 and self.spo2 > 0 and self.sbp > self.dbp >= 0 and self.hr > 0):
            raise CoreInvariantError("arrival Hb, SpO2 and HR are positive and systolic exceeds diastolic")
        if self.consciousness_level not in (0, 1, 2, 3):
            raise CoreInvariantError("consciousness level is 0-3")
        if not 0.21 <= self.fio2 <= 1.0:
            raise CoreInvariantError("FiO2 is between 0.21 and 1.0")

    def to_dict(self) -> dict:
        data = {item.name: getattr(self, item.name) for item in fields(self)}
        data["rhythm"] = self.rhythm.to_dict()
        data["declared"] = self.declared.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: Mapping) -> "Anchors":
        values = dict(data)
        values["rhythm"] = RhythmState.from_dict(values["rhythm"])
        values["declared"] = FrozenRecord(values.get("declared") or {})
        return cls(**values)


#: The common core's auxiliary dynamic state (P2D-1), by field: what it remembers.
#: It is neither a channel (V..K) nor a derived observable: it is memory the core needs to derive
#: observables and responses over time. Only the integrator changes it, each change recorded with
#: its source (``provenance.AuxiliaryChange``). It is never shown to a resident.
AUXILIARY_FIELDS: Mapping[str, str] = {
    "lactate_excess_mmol_l": "lactate above arrival that D has produced and clearance has not yet removed (KD-S1)",
    "sympathetic_drive": "the common sympathetic drive the core holds (KD-S2)",
}


@dataclass(frozen=True)
class AuxiliaryState:
    """Typed, serializable memory owned by the common core (P2D-1); see ``AUXILIARY_FIELDS``."""

    lactate_excess_mmol_l: float = 0.0
    sympathetic_drive: float = 0.0

    def __post_init__(self):
        for name in AUXILIARY_FIELDS:
            _finite(getattr(self, name), name)
        if self.sympathetic_drive < 0:
            # P2D-3: withdrawal of drive lets the rate fall back to the intrinsic rate, never below.
            raise CoreInvariantError("the sympathetic drive is never negative")

    def to_dict(self) -> dict:
        return {name: getattr(self, name) for name in AUXILIARY_FIELDS}

    @classmethod
    def from_dict(cls, data: Mapping) -> "AuxiliaryState":
        unknown = set(data) - set(AUXILIARY_FIELDS)
        if unknown:
            raise CoreInvariantError(f"unknown auxiliary state {sorted(unknown)}")
        return cls(**{name: data[name] for name in AUXILIARY_FIELDS if name in data})


ARRIVAL_AUXILIARY = AuxiliaryState()


@dataclass(frozen=True)
class CoreState:
    """The whole physiological state at the end of ``minute`` (0 = arrival).

    ``internal`` holds each contributor's own state under its source key ("kind:id");
    only that contributor's contribution can replace it. ``aux`` is the core's own memory
    (``AuxiliaryState``), which only the integrator changes. ``fio2`` is a support setting,
    not a channel: proposal §7.3 makes SpO2 a function of G, L, W and FiO2.
    ``terminal_since`` is the minute the rhythm stopped perfusing; resuscitation is not
    modelled (proposal Appendix A5), so it is never cleared.
    """

    minute: int
    V: float
    T: float
    P: float
    R: RhythmState
    L: float
    G: float
    W: float
    D: float
    N: float
    hb: float
    glucose: float
    k: float
    fio2: float
    terminal_since: int | None = None
    internal: FrozenRecord = field(default=EMPTY)
    aux: AuxiliaryState = field(default=ARRIVAL_AUXILIARY)

    def __post_init__(self):
        if isinstance(self.minute, bool) or not isinstance(self.minute, int) or self.minute < 0:
            raise CoreInvariantError("minute is a non-negative integer")
        for channel in SCALAR_CHANNELS:
            _finite(getattr(self, _attribute(channel)), channel.value)
        if not isinstance(self.R, RhythmState):
            raise CoreInvariantError("R is a RhythmState")
        if not 0.21 <= _finite(self.fio2, "fio2") <= 1.0:
            raise CoreInvariantError("FiO2 is between 0.21 and 1.0")
        if self.T <= 0 or self.P <= 0:
            raise CoreInvariantError("tone and pump multipliers stay positive")
        if (self.terminal_since is None) != self.R.pulse_present:
            raise CoreInvariantError("terminal_since is set exactly when there is no pulse")
        if self.terminal_since is not None and not 0 <= self.terminal_since <= self.minute:
            raise CoreInvariantError("terminal_since lies within the encounter")
        if not isinstance(self.internal, FrozenRecord):
            raise CoreInvariantError("internal state is a FrozenRecord")
        if not isinstance(self.aux, AuxiliaryState):
            raise CoreInvariantError("the core's auxiliary state is an AuxiliaryState")

    def value(self, channel: Channel) -> float:
        if channel is Channel.R:
            raise CoreInvariantError("R is a state machine; read state.R")
        return getattr(self, _attribute(channel))

    def internal_for(self, key: str) -> FrozenRecord:
        value = self.internal.get(key, EMPTY)
        return value if isinstance(value, FrozenRecord) else EMPTY

    def evolve(self, **changes) -> "CoreState":
        return replace(self, **changes)

    def to_dict(self) -> dict:
        data = {"minute": self.minute, "R": self.R.to_dict(), "fio2": self.fio2,
                "terminal_since": self.terminal_since, "internal": self.internal.to_dict(),
                "aux": self.aux.to_dict()}
        for channel in SCALAR_CHANNELS:
            data[_attribute(channel)] = getattr(self, _attribute(channel))
        return data

    @classmethod
    def from_dict(cls, data: Mapping) -> "CoreState":
        values = dict(data)
        values["R"] = RhythmState.from_dict(values["R"])
        values["internal"] = FrozenRecord(values.get("internal") or {})
        values["aux"] = AuxiliaryState.from_dict(values.get("aux") or {})
        return cls(**values)

    def digest(self) -> str:
        return digest(self.to_dict())


def _attribute(channel: Channel) -> str:
    return channel.value


def initial_state(anchors: Anchors) -> CoreState:
    """Arrival: every deviation channel at 0, both multipliers at 1, chemistry as authored."""
    return CoreState(minute=0, V=0.0, T=1.0, P=1.0, R=anchors.rhythm, L=0.0, G=0.0, W=0.0, D=0.0,
                     N=0.0, hb=anchors.hb, glucose=anchors.glucose, k=anchors.k, fio2=anchors.fio2)


def canonical_json(data: Any) -> str:
    """One text for one value: sorted keys, no whitespace, floats as Python repr."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(data: Any) -> str:
    return hashlib.sha256(canonical_json(data).encode("utf-8")).hexdigest()
