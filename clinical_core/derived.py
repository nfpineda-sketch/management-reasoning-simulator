"""Quantities computed from the core state every minute and never stored (proposal §7.3).

These are numbers, booleans and rhythm codes for a later observation layer. Nothing here
writes text for a resident, rounds to a display precision or applies a display range:
those are observation-layer decisions (Phase 1, Observation v2).

Every gain is declared in ``PARAMETERS`` with where it comes from. ``adopted`` gains are
the family engine's own faculty-reviewed magnitudes, converted to the core's units and
not fitted to any trajectory; ``provisional`` ones have no faculty value yet and are
listed for calibration (Appendix A9 of the proposal).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, fields
from typing import Mapping

from .state import Anchors, CoreInvariantError, CoreState, RhythmCode

ADOPTED = "adopted"
PROVISIONAL = "provisional"

#: One unit of packed red cells is about 300 mL (family_engine TRANSFUSION note) and moves
#: the family engine's circulation variable by 0.36 (family_engine._minute): one unit of
#: that variable is therefore 300 / 0.36 mL-equivalent of intravascular volume.
LEGACY_ML_PER_CIRCULATION_UNIT = 300.0 / 0.36


@dataclass(frozen=True)
class CoreProfile:
    """The derivation gains. Defaults are the declared values in ``PARAMETERS``."""

    volume_per_output_unit_ml: float = LEGACY_ML_PER_CIRCULATION_UNIT
    sbp_per_pressure_deficit: float = 45.0
    dbp_per_pressure_deficit: float = 25.0
    hr_per_pressure_deficit: float = 25.0
    crt_per_output_deficit_s: float = 4.0
    spo2_per_fio2: float = 30.0
    room_air_fio2: float = 0.21
    lactate_per_output_deficit: float = 2.0
    lactate_floor: float = 0.8
    debt_clearance_tau_min: float = 60.0
    rr_per_lactate: float = 7.5
    pressure_levels: tuple[tuple[float, int], ...] = ((80.0, 1), (65.0, 2))
    oxygen_levels: tuple[tuple[float, int], ...] = ((87.0, 1), (80.0, 2))

    def __post_init__(self):
        for item in fields(self):
            value = getattr(self, item.name)
            if isinstance(value, tuple):
                continue
            if not math.isfinite(value) or value < 0:
                raise CoreInvariantError(f"profile gain {item.name} must be finite and non-negative")
        if self.volume_per_output_unit_ml <= 0 or self.debt_clearance_tau_min <= 0:
            raise CoreInvariantError("volume scale and debt clearance time are positive")

    def to_dict(self) -> dict:
        return {item.name: (list(map(list, getattr(self, item.name))) if isinstance(getattr(self, item.name), tuple)
                            else getattr(self, item.name)) for item in fields(self)}


DEFAULT_PROFILE = CoreProfile()

#: name -> (status, where the value comes from). Read by the comparison report and the docs.
PARAMETERS: Mapping[str, tuple[str, str]] = {
    "volume_per_output_unit_ml": (ADOPTED, "300 mL per red-cell unit / 0.36 circulation per unit "
                                           "(family_engine.TRANSFUSION note; family_engine._minute)"),
    "sbp_per_pressure_deficit": (ADOPTED, "family_engine._surface: sbp - (circulation - 1) * 45"),
    "dbp_per_pressure_deficit": (ADOPTED, "family_engine._surface: dbp - (circulation - 1) * 25"),
    "hr_per_pressure_deficit": (ADOPTED, "family_engine._surface: hr + (circulation - 1) * 25"),
    "crt_per_output_deficit_s": (ADOPTED, "family_engine._surface: crt + (circulation - 1) * 4"),
    "spo2_per_fio2": (ADOPTED, "family_engine._surface: oxygen_gain = (FiO2 - 0.21) * 30"),
    "room_air_fio2": (ADOPTED, "family_engine._initialize: oxygen_fio2 = .21"),
    "lactate_per_output_deficit": (ADOPTED, "family_engine._diagnostic: lactate + (circulation - 1) * 2, "
                                            "reached here as the steady state of the debt D"),
    "lactate_floor": (ADOPTED, "family_engine._diagnostic: max(.8, ...)"),
    "debt_clearance_tau_min": (PROVISIONAL, "no faculty value; the family engine's lactate has no kinetics"),
    "rr_per_lactate": (PROVISIONAL, "legacy GI RR gain 15 per circulation unit / lactate 2 per unit; the "
                                    "structure (RR from lactate) is proposal §7.3, the value is not reviewed"),
    "pressure_levels": (ADOPTED, "family_engine._PRESSURE_LEVELS, without the DC1 anchoring or the recovery "
                                 "margin, which belong to the observation layer"),
    "oxygen_levels": (ADOPTED, "family_engine._OXYGEN_LEVELS, same reservation"),
}


@dataclass(frozen=True)
class Derived:
    """State values ready for an observation layer. ``None`` means not measurable."""

    minute: int
    pulse_present: bool
    rhythm: RhythmCode
    monitor_rate_bpm: float | None
    pulse_rate_bpm: float | None
    output_rel: float
    pressure_rel: float
    delivery_rel: float
    sbp: float | None
    dbp: float | None
    map: float | None
    spo2: float | None
    respiratory_rate: float
    crt_s: float | None
    lactate: float
    consciousness_level: int

    def to_dict(self) -> dict:
        data = {item.name: getattr(self, item.name) for item in fields(self)}
        data["rhythm"] = self.rhythm.value
        return data


def _level(value: float, levels) -> int:
    return max((level for threshold, level in levels if value < threshold), default=0)


def derive(state: CoreState, anchors: Anchors, profile: CoreProfile = DEFAULT_PROFILE) -> Derived:
    rhythm = state.R
    lactate = max(profile.lactate_floor,
                  anchors.lactate + profile.lactate_per_output_deficit / profile.debt_clearance_tau_min * state.D)
    if not rhythm.pulse_present:
        derived = Derived(minute=state.minute, pulse_present=False, rhythm=rhythm.code,
                          monitor_rate_bpm=rhythm.rate_bpm, pulse_rate_bpm=None, output_rel=0.0,
                          pressure_rel=0.0, delivery_rel=0.0, sbp=None, dbp=None, map=None, spo2=None,
                          respiratory_rate=0.0, crt_s=None, lactate=lactate, consciousness_level=3)
        check(derived)
        return derived
    preload_rel = max(0.0, 1.0 + state.V / profile.volume_per_output_unit_ml)
    output_rel = state.P * (rhythm.output_factor / anchors.rhythm.output_factor) * preload_rel
    pressure_rel = output_rel * state.T
    deficit = 1.0 - pressure_rel
    sbp = max(0.0, anchors.sbp - profile.sbp_per_pressure_deficit * deficit)
    dbp = max(0.0, anchors.dbp - profile.dbp_per_pressure_deficit * deficit)
    if rhythm.code is RhythmCode.SINUS:
        # Sinus rate answers to the pressure deficit (sympathetic compensation); a block,
        # an escape or a paced rhythm keeps the rate the rhythm state holds.
        pulse_rate = rhythm.rate_bpm + profile.hr_per_pressure_deficit * deficit
    else:
        pulse_rate = rhythm.rate_bpm
    oxygen = (max(0.0, state.fio2 - profile.room_air_fio2) - max(0.0, anchors.fio2 - profile.room_air_fio2))
    spo2 = min(100.0, max(0.0, anchors.spo2 + profile.spo2_per_fio2 * oxygen))
    crt = max(0.0, anchors.crt_s + profile.crt_per_output_deficit_s * (1.0 - output_rel))
    delivery_rel = output_rel * (state.hb / anchors.hb) * (spo2 / anchors.spo2)
    rr = max(0.0, anchors.respiratory_rate + profile.rr_per_lactate * (lactate - anchors.lactate))
    level = max(anchors.consciousness_level, _level(sbp, profile.pressure_levels), _level(spo2, profile.oxygen_levels))
    derived = Derived(minute=state.minute, pulse_present=True, rhythm=rhythm.code,
                      monitor_rate_bpm=pulse_rate, pulse_rate_bpm=pulse_rate, output_rel=output_rel,
                      pressure_rel=pressure_rel, delivery_rel=delivery_rel, sbp=sbp, dbp=dbp,
                      map=(sbp + 2 * dbp) / 3, spo2=spo2, respiratory_rate=rr, crt_s=crt, lactate=lactate,
                      consciousness_level=level)
    check(derived)
    return derived


def check(derived: Derived) -> None:
    """The observation invariants of proposal §11.4 that the core itself can guarantee."""
    measured = (derived.sbp, derived.dbp, derived.map, derived.spo2, derived.crt_s, derived.pulse_rate_bpm)
    if not derived.pulse_present:
        if any(value is not None for value in measured):
            raise CoreInvariantError("without a pulse, BP, SpO2, CRT and pulse rate are not measurable")
        if derived.consciousness_level != 3:
            raise CoreInvariantError("without a pulse the patient is unresponsive")
        if derived.respiratory_rate != 0.0 or derived.output_rel != 0.0:
            raise CoreInvariantError("without a pulse there is no output and no breathing")
    else:
        if any(value is None or not math.isfinite(value) for value in measured):
            raise CoreInvariantError("with a pulse, every vital sign has a finite value")
        if derived.pulse_rate_bpm <= 0:
            raise CoreInvariantError("a perfusing rhythm has a positive rate")
        if derived.sbp < derived.dbp:
            raise CoreInvariantError(f"systolic {derived.sbp:.1f} below diastolic {derived.dbp:.1f}")
    if derived.monitor_rate_bpm == 0 and derived.rhythm is not RhythmCode.ASYSTOLE:
        raise CoreInvariantError("a monitor rate of 0 is asystole")
    if derived.rhythm is RhythmCode.ASYSTOLE and derived.monitor_rate_bpm != 0:
        raise CoreInvariantError("asystole has a monitor rate of 0")
    for value in (derived.output_rel, derived.pressure_rel, derived.delivery_rel, derived.lactate,
                  derived.respiratory_rate):
        if not math.isfinite(value) or value < 0:
            raise CoreInvariantError("derived flows, lactate and rate are finite and non-negative")
