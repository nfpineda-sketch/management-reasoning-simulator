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

from .provenance import Source, SourceKind
from .state import Anchors, CoreInvariantError, CoreState, RhythmCode, UnresolvedBoundary

ADOPTED = "adopted"
PROVISIONAL = "provisional"

#: Numerical zero for effective output (P2D-2). Not a clinical arrest threshold: that threshold,
#: and how long output must stay low before arrest, are TBD.
OUTPUT_EPSILON = 1e-9

#: One unit of packed red cells is about 300 mL (family_engine TRANSFUSION note) and moves
#: the family engine's circulation variable by 0.36 (family_engine._minute): one unit of
#: that variable is therefore 300 / 0.36 mL-equivalent of intravascular volume.
LEGACY_ML_PER_CIRCULATION_UNIT = 300.0 / 0.36

#: The sources of the changes to the core's auxiliary dynamic state (``CoreState.aux``, P2D-1):
#: lactate kinetics (KD-S1) and the common sympathetic drive (KD-S2). Only the integrator
#: writes them; each change is an ``AuxiliaryChange`` in the minute's record.
LACTATE_KINETICS = Source(SourceKind.CORE_COUPLING, "lactate_kinetics")
SYMPATHETIC_DRIVE = Source(SourceKind.CORE_COUPLING, "sympathetic_drive")
AUXILIARY_SOURCES = {"lactate_excess_mmol_l": LACTATE_KINETICS, "sympathetic_drive": SYMPATHETIC_DRIVE}
#: The core's coupling from excess preload on a pump without reserve to lung water L (KD-S4).
PRELOAD_CONGESTION = Source(SourceKind.CORE_COUPLING, "preload_congestion")
#: The core's slow clearance of lung water above arrival (P2D-6).
LUNG_WATER_CLEARANCE = Source(SourceKind.CORE_COUPLING, "lung_water_clearance")


@dataclass(frozen=True)
class CoreProfile:
    """The derivation gains. Defaults are the declared values in ``PARAMETERS``."""

    preload_curve_scale_ml: float = LEGACY_ML_PER_CIRCULATION_UNIT
    arrival_preload_fraction: float = 0.5
    pump_preload_coupling: float = 1.0
    lung_water_clearance_tau_min: float = 240.0
    afterload_sensitivity: float = 0.3
    congestion_preload_knee: float = 0.85
    congestion_per_excess_preload: float = 0.05
    sbp_per_pressure_deficit: float = 45.0
    dbp_per_pressure_deficit: float = 25.0
    hr_per_sympathetic_drive: float = 25.0
    sympathetic_per_pressure_deficit: float = 1.0
    sympathetic_per_debt: float = 0.5
    sympathetic_per_hypoxaemia_point: float = 0.02
    hypoxaemia_threshold_spo2: float = 94.0
    sympathetic_per_hypoglycaemia_mg_dl: float = 0.01
    hypoglycaemia_threshold_mg_dl: float = 70.0
    sympathetic_decay_tau_min: float = 5.0
    crt_per_output_deficit_s: float = 4.0
    spo2_per_fio2: float = 30.0
    room_air_fio2: float = 0.21
    lactate_per_output_deficit: float = 2.0
    lactate_floor: float = 0.8
    debt_clearance_tau_min: float = 60.0
    lactate_clearance_tau_min: float = 60.0
    rr_per_lactate: float = 7.5
    lactate_drive_threshold_mmol_l: float = 2.0
    rr_metabolic_max: float = 25.0
    rr_ventilatory_floor: float = 12.0
    rr_max: float = 60.0
    pressure_levels: tuple[tuple[float, int], ...] = ((80.0, 1), (65.0, 2))
    oxygen_levels: tuple[tuple[float, int], ...] = ((87.0, 1), (80.0, 2))

    def __post_init__(self):
        for item in fields(self):
            value = getattr(self, item.name)
            if isinstance(value, tuple):
                continue
            if not math.isfinite(value) or value < 0:
                raise CoreInvariantError(f"profile gain {item.name} must be finite and non-negative")
        if min(self.preload_curve_scale_ml, self.debt_clearance_tau_min, self.lactate_clearance_tau_min,
               self.rr_metabolic_max, self.rr_max, self.sympathetic_decay_tau_min,
               self.lung_water_clearance_tau_min) <= 0:
            raise CoreInvariantError("volume scale, time constants and RR bounds are positive")
        if not 0.0 < self.arrival_preload_fraction < 1.0 or not 0.0 < self.congestion_preload_knee < 1.0:
            raise CoreInvariantError("positions on the preload curve are strictly between 0 and 1")
        if self.afterload_sensitivity >= 1.0:
            raise CoreInvariantError("afterload sensitivity is below 1, so output stays positive at any tone")

    def to_dict(self) -> dict:
        return {item.name: (list(map(list, getattr(self, item.name))) if isinstance(getattr(self, item.name), tuple)
                            else getattr(self, item.name)) for item in fields(self)}


DEFAULT_PROFILE = CoreProfile()

#: name -> (status, where the value comes from). Read by the comparison report and the docs.
PARAMETERS: Mapping[str, tuple[str, str]] = {
    "preload_curve_scale_ml": (PROVISIONAL, "scale of the saturating preload curve 1 - exp(-x / scale): TBD "
                                            "(KD-S4). Its value keeps, at the default arrival position 0.5, the "
                                            "family engine's slope at arrival: 300 mL per red-cell unit / 0.36 "
                                            "circulation per unit (family_engine.TRANSFUSION note; _minute)"),
    "arrival_preload_fraction": (PROVISIONAL, "where arrival sits on the preload curve when the case does not "
                                              "declare it (0 empty, 1 plateau): TBD (KD-S4)"),
    "pump_preload_coupling": (PROVISIONAL, "how far a depressed pump shrinks the preload curve: scale x P^c, so "
                                           "it lowers and flattens the usable curve (c = 0: P only scales "
                                           "output): TBD (P2D-5)"),
    "lung_water_clearance_tau_min": (PROVISIONAL, "slow clearance of lung water above arrival: TBD (P2D-6)"),
    "afterload_sensitivity": (PROVISIONAL, "how much tone above arrival lowers output, 1 / (1 + a (T - 1)): TBD "
                                           "(KD-S4)"),
    "congestion_preload_knee": (PROVISIONAL, "position on the preload curve above which excess preload congests "
                                             "a pump without reserve: TBD (KD-S4)"),
    "congestion_per_excess_preload": (PROVISIONAL, "L per minute at full excess and no pump reserve: TBD (KD-S4)"),
    "sbp_per_pressure_deficit": (ADOPTED, "family_engine._surface: sbp - (circulation - 1) * 45"),
    "dbp_per_pressure_deficit": (ADOPTED, "family_engine._surface: dbp - (circulation - 1) * 25"),
    "hr_per_sympathetic_drive": (ADOPTED, "family_engine._surface: hr + (circulation - 1) * 25, read here as bpm "
                                          "per unit of sympathetic drive"),
    "sympathetic_per_pressure_deficit": (PROVISIONAL, "MAP/output deficit -> sympathetic drive gain: TBD (KD-S2)"),
    "sympathetic_per_debt": (PROVISIONAL, "oxygen-delivery debt (D / tau_D) -> sympathetic drive gain: TBD (KD-S2)"),
    "sympathetic_per_hypoxaemia_point": (PROVISIONAL, "drive per SpO2 point below the threshold: TBD (KD-S2)"),
    "hypoxaemia_threshold_spo2": (PROVISIONAL, "SpO2 below which hypoxaemia drives the rate: TBD (KD-S2)"),
    "sympathetic_per_hypoglycaemia_mg_dl": (PROVISIONAL, "drive per mg/dL below the threshold: TBD (KD-S2)"),
    "hypoglycaemia_threshold_mg_dl": (PROVISIONAL, "glucose below which it drives the rate: TBD (KD-S2)"),
    "sympathetic_decay_tau_min": (PROVISIONAL, "sympathetic decay time: TBD (KD-S2); the drive rises at once"),
    "crt_per_output_deficit_s": (ADOPTED, "family_engine._surface: crt + (circulation - 1) * 4"),
    "spo2_per_fio2": (ADOPTED, "family_engine._surface: oxygen_gain = (FiO2 - 0.21) * 30"),
    "room_air_fio2": (ADOPTED, "family_engine._initialize: oxygen_fio2 = .21"),
    "lactate_per_output_deficit": (ADOPTED, "family_engine._diagnostic: lactate + (circulation - 1) * 2, "
                                            "reached here as the steady state of D and of lactate kinetics; the "
                                            "D -> lactate production gain it implies is provisional (KD-S1)"),
    "lactate_floor": (ADOPTED, "family_engine._diagnostic: max(.8, ...)"),
    "debt_clearance_tau_min": (PROVISIONAL, "tau_D_recovery: TBD (KD-S1); 60 min is not approved"),
    "lactate_clearance_tau_min": (PROVISIONAL, "lactate clearance: TBD (KD-S1)"),
    "rr_per_lactate": (PROVISIONAL, "metabolic drive -> RR gain at the threshold: TBD (KD-S1); the value is the "
                                    "legacy GI RR gain 15 per circulation unit / lactate 2 per unit"),
    "lactate_drive_threshold_mmol_l": (PROVISIONAL, "lactate above which acidaemia drives breathing: TBD (KD-S1)"),
    "rr_metabolic_max": (PROVISIONAL, "largest metabolic addition to RR (saturation): TBD (KD-S1)"),
    "rr_ventilatory_floor": (PROVISIONAL, "RR below which the arrival RR is never read as metabolic: TBD (KD-S1)"),
    "rr_max": (PROVISIONAL, "safety bound on RR, not physiology: TBD (KD-S1)"),
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


def lactate_excess(state: CoreState) -> float:
    """The lactate the core holds above arrival (mmol/L): auxiliary state, not a function of D."""
    return state.aux.lactate_excess_mmol_l


def lactate_after_minute(state: CoreState, profile: CoreProfile) -> float:
    """One minute of lactate kinetics (KD-S1): production from the debt D, first-order clearance.

    dX = k * D - X / tau_lactate, with k = gain / (tau_D * tau_lactate). At a steady delivery
    shortfall s, D settles at tau_D * s and X at gain * s, the family engine's lactate; on
    the way, lactate lags D, and after perfusion is restored it clears more slowly than D.
    """
    excess = lactate_excess(state)
    production = profile.lactate_per_output_deficit / (profile.debt_clearance_tau_min
                                                       * profile.lactate_clearance_tau_min) * state.D
    return excess + production - excess / profile.lactate_clearance_tau_min


def _metabolic_drive(lactate: float, profile: CoreProfile) -> float:
    """Breaths/min that acidaemia adds: zero below the threshold, saturating above it."""
    excess = max(0.0, lactate - profile.lactate_drive_threshold_mmol_l)
    cap = profile.rr_metabolic_max
    return cap * (1.0 - math.exp(-profile.rr_per_lactate * excess / cap))


def respiratory_rate(state: CoreState, anchors: Anchors, profile: CoreProfile, lactate: float) -> float:
    """RR = ventilatory RR (from W) + metabolic drive (from lactate), anchored to arrival (KD-S1).

    The arrival RR is split into two parts:
    - a ventilatory part, never below ``rr_ventilatory_floor``;
    - the metabolic part that the arrival lactate explains.

    A rise of lactate above arrival adds its whole metabolic drive. A fall below arrival takes
    away at most the metabolic part, so clearing lactate cannot by itself cause bradypnoea.
    The response is continuous in both the current and the arrival lactate.

    W (proposal C7) is read in two directions, a provisional structure:
    - above 0 (load or drive from respiratory disease), it adds to the ventilatory part, and
      the metabolic drive is added on top, so neither overwrites the other;
    - below 0 (depressed drive: opioid, CNS), it blunts both parts. That explicit mechanism
      is the only route to bradypnoea.
    """
    arrival_metabolic = _metabolic_drive(anchors.lactate, profile)
    share = min(arrival_metabolic, max(0.0, anchors.respiratory_rate - profile.rr_ventilatory_floor))
    ventilatory = (anchors.respiratory_rate - share) * (1.0 + max(0.0, state.W))
    now = _metabolic_drive(lactate, profile)
    if now >= arrival_metabolic:
        metabolic = share + (now - arrival_metabolic)
    else:                                   # arrival_metabolic > now >= 0
        metabolic = share * now / arrival_metabolic
    drive = max(0.0, 1.0 + min(0.0, state.W))
    return min(profile.rr_max, drive * (ventilatory + metabolic))


def arrival_preload(anchors: Anchors, profile: CoreProfile) -> float:
    """Where arrival sits on the preload curve: the case's declaration, or the profile's default."""
    return anchors.preload_fraction if anchors.preload_fraction is not None else profile.arrival_preload_fraction


def arrival_filling(anchors: Anchors, profile: CoreProfile) -> float:
    """Effective preload at arrival (mL-eq): where the arrival position sits on the arrival pump's curve."""
    return -profile.preload_curve_scale_ml * math.log1p(-arrival_preload(anchors, profile))


def preload_position(state: CoreState, anchors: Anchors, profile: CoreProfile, *, volume: float | None = None) -> float:
    """Where the state sits on its pump's preload curve, 0 (empty) to 1 (the plateau) (KD-S4, P2D-5).

    One smooth, saturating curve, 1 - exp(-x / scale), in mL-equivalent of effective preload
    x. Arrival is placed on it by its position, and V moves along it. While the ventricle
    fills (x > 0) every added mL helps less than the one before, and the curve never quite
    reaches its plateau: there is no upper clamp. Below the empty point (x <= 0) the position
    is 0: no curve that never goes negative can be concave for every V.

    The pump shapes the curve (P2D-5): its scale is ``preload_curve_scale_ml x P^c``, so a
    depressed pump sits nearer a lower plateau and gains less from each mL; at arrival (P = 1)
    the curve is the arrival curve. ``volume`` reads the curve at another V (default: the
    state's). Form, scale and c are provisional.
    """
    scale = profile.preload_curve_scale_ml * state.P ** profile.pump_preload_coupling
    filling = arrival_filling(anchors, profile) + (state.V if volume is None else volume)
    return -math.expm1(-max(0.0, filling) / scale)


def _perfusion(state: CoreState, anchors: Anchors, profile: CoreProfile) -> tuple[float, float, float, float]:
    """(output_rel, pressure_rel, spo2, delivery_rel) of a perfusing state.

    V -> effective preload -> stroke volume -> output -> pressure (KD-S4):
    - output is the pump (P) times the rhythm's share times the preload response, lowered by
      tone above arrival (afterload);
    - the preload response is read on the current pump's curve, relative to the arrival
      filling on that curve, so P keeps meaning the output at arrival filling (P2D-5);
    - pressure is output times tone.
    """
    preload_rel = preload_position(state, anchors, profile) / preload_position(state, anchors, profile, volume=0.0)
    afterload = 1.0 / (1.0 + profile.afterload_sensitivity * (state.T - 1.0))
    output_rel = state.P * (state.R.output_factor / anchors.rhythm.output_factor) * preload_rel * afterload
    pressure_rel = output_rel * state.T
    oxygen = (max(0.0, state.fio2 - profile.room_air_fio2) - max(0.0, anchors.fio2 - profile.room_air_fio2))
    spo2 = min(100.0, max(0.0, anchors.spo2 + profile.spo2_per_fio2 * oxygen))
    delivery_rel = output_rel * (state.hb / anchors.hb) * (spo2 / anchors.spo2)
    return output_rel, pressure_rel, spo2, delivery_rel


def congestion_rate(state: CoreState, anchors: Anchors, profile: CoreProfile) -> float:
    """Lung water added this minute by excess preload on a pump without reserve (KD-S4).

    Only preload added above arrival congests ("additional V", KD-S4), and only above the
    knee of the curve, so arrival stays a fixed point like every other coupling. The excess is
    the share of the curve left above max(knee, arrival position) that is now used, times how
    far the pump falls short of normal reserve (the case's reserve times the current pump P).
    A pump with full reserve never congests from preload alone. This coupling only adds L;
    clearing lung water belongs to the mechanisms that act on L, which the shadow core does
    not model yet.
    """
    if not state.R.pulse_present:
        return 0.0
    start = max(profile.congestion_preload_knee, arrival_preload(anchors, profile))
    excess = max(0.0, (preload_position(state, anchors, profile) - start) / (1.0 - start))
    shortfall = max(0.0, 1.0 - anchors.pump_reserve * state.P)
    return profile.congestion_per_excess_preload * excess * shortfall


def lung_water_clearance(state: CoreState, profile: CoreProfile) -> float:
    """Lung water above arrival cleared this minute (P2D-6): slow, first order, never below arrival.

    It runs whatever else acts on L, so without a source L falls back toward arrival, and with
    one that persists it settles above arrival or keeps rising. It never adds L. Specific
    treatments (diuretics, NIV) are not modelled here.
    """
    return max(0.0, state.L) * -math.expm1(-1.0 / profile.lung_water_clearance_tau_min)


def sympathetic_target(state: CoreState, anchors: Anchors, profile: CoreProfile) -> float:
    """The drive the state calls for now, relative to arrival (KD-S2; proposal §7.3).

    It sums the stimuli the core holds state for, each as a deviation from arrival:
    - the pressure deficit;
    - the oxygen-delivery debt D;
    - hypoxaemia;
    - hypoglycaemia.

    Hypercapnia, pain or agitation, fever and withdrawal are declared inputs of the same
    drive, but no core state carries them yet (no CO2, pain, temperature or withdrawal
    module). Hemostasis, or any disease module, never writes it: it moves only through
    these stimuli.
    """
    _, pressure_rel, spo2, _ = _perfusion(state, anchors, profile)
    hypoxaemia = (max(0.0, profile.hypoxaemia_threshold_spo2 - spo2)
                  - max(0.0, profile.hypoxaemia_threshold_spo2 - anchors.spo2))
    hypoglycaemia = (max(0.0, profile.hypoglycaemia_threshold_mg_dl - state.glucose)
                     - max(0.0, profile.hypoglycaemia_threshold_mg_dl - anchors.glucose))
    target = (profile.sympathetic_per_pressure_deficit * (1.0 - pressure_rel)
              + profile.sympathetic_per_debt * state.D / profile.debt_clearance_tau_min
              + profile.sympathetic_per_hypoxaemia_point * hypoxaemia
              + profile.sympathetic_per_hypoglycaemia_mg_dl * hypoglycaemia)
    # P2D-3: the drive is never negative. As its stimuli resolve, the rate falls back to the
    # intrinsic rate of R and no further; a lower rate needs an explicit chronotropic source
    # that changes R.
    return max(0.0, target)


def sympathetic_drive(state: CoreState, anchors: Anchors, profile: CoreProfile) -> float:
    """The drive the core holds: auxiliary state (0 at arrival, where the state calls for none)."""
    return state.aux.sympathetic_drive


def sympathetic_after_minute(before: CoreState, after: CoreState, anchors: Anchors, profile: CoreProfile) -> float:
    """The drive at the end of a minute: it rises at once, and decays with ``sympathetic_decay_tau_min``.

    Without a pulse there is no rate to drive and nothing is kept; when a pulse returns, the
    drive starts from what the state calls for.
    """
    if not after.R.pulse_present:
        return 0.0
    target = sympathetic_target(after, anchors, profile)
    held = sympathetic_drive(before, anchors, profile) if before.R.pulse_present else target
    if target >= held:
        return target
    return target + (held - target) * math.exp(-1.0 / profile.sympathetic_decay_tau_min)


def derive(state: CoreState, anchors: Anchors, profile: CoreProfile = DEFAULT_PROFILE) -> Derived:
    rhythm = state.R
    # The floor guards against a debt repaid below what any patient reads; it never moves an
    # authored arrival that is already below it.
    lactate = max(min(profile.lactate_floor, anchors.lactate), anchors.lactate + lactate_excess(state))
    if not rhythm.pulse_present:
        derived = Derived(minute=state.minute, pulse_present=False, rhythm=rhythm.code,
                          monitor_rate_bpm=rhythm.rate_bpm, pulse_rate_bpm=None, output_rel=0.0,
                          pressure_rel=0.0, delivery_rel=0.0, sbp=None, dbp=None, map=None, spo2=None,
                          respiratory_rate=0.0, crt_s=None, lactate=lactate, consciousness_level=3)
        check(derived)
        return derived
    output_rel, pressure_rel, spo2, delivery_rel = _perfusion(state, anchors, profile)
    if output_rel <= OUTPUT_EPSILON:
        # P2D-2: a pulse and a measurable pressure without output cannot exist. No approved rule
        # moves the rhythm to arrest here (threshold and dwell are TBD), so the run stops.
        raise UnresolvedBoundary(
            f"minute {state.minute}: effective output reached zero while a pulse is present; no approved "
            "terminal transition applies (arrest threshold and dwell TBD), so the run stops instead of showing "
            "a pulse and a blood pressure without output")
    deficit = 1.0 - pressure_rel
    sbp = max(0.0, anchors.sbp - profile.sbp_per_pressure_deficit * deficit)
    dbp = max(0.0, anchors.dbp - profile.dbp_per_pressure_deficit * deficit)
    if rhythm.code is RhythmCode.SINUS:
        # Sinus rate = intrinsic rate + chronotropic response to the common sympathetic drive,
        # blunted by beta-blockade (KD-S2); a block, an escape or a paced rhythm keeps the rate
        # the rhythm state holds.
        response = profile.hr_per_sympathetic_drive * (1.0 - anchors.beta_blockade)
        pulse_rate = rhythm.rate_bpm + response * sympathetic_drive(state, anchors, profile)
    else:
        pulse_rate = rhythm.rate_bpm
    crt = max(0.0, anchors.crt_s + profile.crt_per_output_deficit_s * (1.0 - output_rel))
    rr = respiratory_rate(state, anchors, profile, lactate)
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
        if derived.output_rel <= OUTPUT_EPSILON:
            raise CoreInvariantError("a pulse requires effective output above zero")
        if any(value is None or not math.isfinite(value) for value in measured):
            raise CoreInvariantError("with a pulse, every vital sign has a finite value")
        if derived.pulse_rate_bpm <= 0:
            raise CoreInvariantError("a perfusing rhythm has a positive rate")
        if derived.sbp < derived.dbp:
            raise CoreInvariantError(f"systolic {derived.sbp:.1f} below diastolic {derived.dbp:.1f}")
    if derived.output_rel <= OUTPUT_EPSILON and any(value is not None for value in (derived.sbp, derived.dbp,
                                                                                     derived.map)):
        raise CoreInvariantError("a blood pressure is not measurable without output")
    if derived.monitor_rate_bpm == 0 and derived.rhythm is not RhythmCode.ASYSTOLE:
        raise CoreInvariantError("a monitor rate of 0 is asystole")
    if derived.rhythm is RhythmCode.ASYSTOLE and derived.monitor_rate_bpm != 0:
        raise CoreInvariantError("asystole has a monitor rate of 0")
    for value in (derived.output_rel, derived.pressure_rel, derived.delivery_rel, derived.lactate,
                  derived.respiratory_rate):
        if not math.isfinite(value) or value < 0:
            raise CoreInvariantError("derived flows, lactate and rate are finite and non-negative")
