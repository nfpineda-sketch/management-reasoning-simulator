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
from dataclasses import replace

from .state import (CASE_PARAMETERS, UNMAPPED, Anchors, AuxiliaryState, BloodState, CoreInvariantError, CoreState,
                    RhythmCode, RhythmState, UnresolvedBoundary, anchored_state)

ADOPTED = "adopted"
PROVISIONAL = "provisional"

#: Numerical zero for effective output (P2D-2). Not a clinical arrest threshold: that threshold,
#: and how long output must stay low before arrest, are TBD.
OUTPUT_EPSILON = 1e-9

#: One unit of packed red cells is about 300 mL (family_engine TRANSFUSION note) and moves
#: the family engine's circulation variable by 0.36 (family_engine._minute): one unit of
#: that variable is therefore 300 / 0.36 mL-equivalent of the preload coordinate V (with kappa 1,
#: of circulating volume; P2I-2T).
LEGACY_ML_PER_CIRCULATION_UNIT = 300.0 / 0.36

#: The sources of the changes to the core's auxiliary dynamic state (``CoreState.aux``, P2D-1):
#: lactate kinetics (KD-S1) and the common sympathetic drive (KD-S2). Only the integrator
#: writes them; each change is an ``AuxiliaryChange`` in the minute's record.
LACTATE_KINETICS = Source(SourceKind.CORE_COUPLING, "lactate_kinetics")
SYMPATHETIC_DRIVE = Source(SourceKind.CORE_COUPLING, "sympathetic_drive")
#: The core's product of the case's demand baseline and the declared demand modifiers (P2E-2).
OXYGEN_DEMAND = Source(SourceKind.CORE_COUPLING, "oxygen_demand")
AUXILIARY_SOURCES = {"lactate_excess_mmol_l": LACTATE_KINETICS, "sympathetic_drive": SYMPATHETIC_DRIVE,
                     "oxygen_demand": OXYGEN_DEMAND}
#: The core's coupling from excess preload on a pump without reserve to lung water L (KD-S4).
PRELOAD_CONGESTION = Source(SourceKind.CORE_COUPLING, "preload_congestion")
#: The core's slow clearance of lung water above arrival (P2D-6).
LUNG_WATER_CLEARANCE = Source(SourceKind.CORE_COUPLING, "lung_water_clearance")
#: The core's terminal collapse from sustained critically low output (P2E-3): it accumulates the
#: burden and, when the rule is on and the criterion is met, moves R to a pulseless rhythm.
COLLAPSE = Source(SourceKind.CORE_COUPLING, "collapse")
AUXILIARY_SOURCES["collapse_burden"] = COLLAPSE
#: The rhythms the collapse rule may end in (P2E-3). Which one, and when, is TBD.
TERMINAL_RHYTHMS = ("pea", "asystole")
#: The shared blood state's two core couplings (P2I-2T): plasma refill into the circulation, and
#: haemoglobin as the concentration of red-cell content in the circulating volume.
PLASMA_REFILL = Source(SourceKind.CORE_COUPLING, "plasma_refill")
BLOOD_COMPOSITION = Source(SourceKind.CORE_COUPLING, "blood_composition")
#: Mean haemoglobin concentration inside red cells (g/dL of red cells), used only to report the
#: plasma part of the circulating-volume deviation (``plasma_volume_deviation``); no mechanism reads it.
RED_CELL_HB_G_DL = 33.0


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
    low_output_pressure_knee: float = 0.5
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
    debt_per_delivery_deficit: float = 1.0
    # P2I-2P: maximal over normal oxygen extraction. 1 is the pre-P2I-2P model (no reserve); the
    # physiological value is above 1 and TBD.
    oxygen_extraction_reserve: float = 1.0
    lactate_clearance_tau_min: float = 60.0
    rr_per_lactate: float = 7.5
    lactate_drive_threshold_mmol_l: float = 2.0
    rr_metabolic_max: float = 25.0
    rr_ventilatory_floor: float = 12.0
    rr_max: float = 60.0
    pressure_levels: tuple[tuple[float, int], ...] = ((80.0, 1), (65.0, 2))
    oxygen_levels: tuple[tuple[float, int], ...] = ((87.0, 1), (80.0, 2))
    # P2E-3: the collapse rule is off (None) unless a profile declares it. No clinical threshold,
    # dwell or repayment is chosen: only tests and probes set synthetic values.
    collapse_output_threshold: float | None = None
    collapse_burden_limit: float | None = None
    collapse_repayment_tau_min: float | None = None
    collapse_terminal_rhythm: str = "pea"
    collapse_burden_per_minute: float = 1.0
    # P2I-2T: the shared blood state. Every value is PROVISIONAL (SYNTHETIC/CANDIDATE) and TBD.
    arrival_circulating_volume_ml: float = 4000.0
    volume_preload_kappa: float = 1.0
    plasma_refill_target_share: float = 0.5
    plasma_refill_tau_min: float = 120.0
    plasma_refill_capacity_ml: float = 1000.0

    def __post_init__(self):
        for item in fields(self):
            value = getattr(self, item.name)
            if isinstance(value, (tuple, str)) or value is None:
                continue
            if not math.isfinite(value) or value < 0:
                raise CoreInvariantError(f"profile gain {item.name} must be finite and non-negative")
        if min(self.preload_curve_scale_ml, self.debt_clearance_tau_min, self.lactate_clearance_tau_min,
               self.rr_metabolic_max, self.rr_max, self.sympathetic_decay_tau_min,
               self.lung_water_clearance_tau_min) <= 0:
            raise CoreInvariantError("volume scale, time constants and RR bounds are positive")
        if not 0.0 < self.arrival_preload_fraction < 1.0 or not 0.0 < self.congestion_preload_knee < 1.0:
            raise CoreInvariantError("positions on the preload curve are strictly between 0 and 1")
        if not 0.0 <= self.pump_preload_coupling <= 1.0:
            # P2D-5: lower P gives less output and never more per mL only for c in [0, 1].
            raise CoreInvariantError("the pump/preload coupling c is between 0 and 1")
        if self.afterload_sensitivity >= 1.0:
            raise CoreInvariantError("afterload sensitivity is below 1, so output stays positive at any tone")
        if min(self.debt_per_delivery_deficit, self.collapse_burden_per_minute) <= 0.0:
            raise CoreInvariantError("the deficit-to-debt and collapse-burden gains are positive")
        if self.oxygen_extraction_reserve < 1.0:
            # Maximal extraction is never below normal extraction.
            raise CoreInvariantError("the oxygen extraction reserve is at least 1")
        if min(self.debt_clearance_tau_min, self.lactate_clearance_tau_min) < 1.0:
            # D and lactate are integrated one minute at a time; a shorter time constant would
            # overshoot and take them negative.
            raise CoreInvariantError("the debt and lactate time constants are at least one minute (the step)")
        if not 0.0 < self.low_output_pressure_knee < 1.0:
            raise CoreInvariantError("the low-output pressure knee is strictly between 0 and 1")
        if (self.collapse_output_threshold is None) != (self.collapse_burden_limit is None):
            raise CoreInvariantError("the collapse rule declares both its output threshold and its burden limit, "
                                     "or neither")
        for name in ("collapse_output_threshold", "collapse_burden_limit", "collapse_repayment_tau_min"):
            if getattr(self, name) is not None and not getattr(self, name) > 0:
                raise CoreInvariantError(f"{name} is positive when declared")
        if self.collapse_output_threshold is not None and self.collapse_output_threshold >= 1.0:
            # At or above arrival output, arrival itself would accrue burden: no longer a fixed point.
            raise CoreInvariantError("the collapse output threshold is below arrival output (under 1)")
        if self.collapse_repayment_tau_min is not None and self.collapse_output_threshold is None:
            raise CoreInvariantError("a collapse repayment needs a collapse rule")
        if self.collapse_terminal_rhythm not in TERMINAL_RHYTHMS:
            raise CoreInvariantError(f"the collapse rule ends in one of {TERMINAL_RHYTHMS}")
        if min(self.arrival_circulating_volume_ml, self.volume_preload_kappa) <= 0:
            raise CoreInvariantError("the arrival circulating volume and the volume-to-preload conversion are positive")
        if not 0.0 <= self.plasma_refill_target_share <= 1.0:
            # Refill restores part of the shed volume, never more than all of it.
            raise CoreInvariantError("the plasma refill target is a share of the shed volume, between 0 and 1")
        if self.plasma_refill_tau_min < 1.0:
            # Integrated one minute at a time: a shorter time constant would pass the target.
            raise CoreInvariantError("the plasma refill time constant is at least one minute (the step)")

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
    "low_output_pressure_knee": (PROVISIONAL, "pressure_rel below which SBP and DBP leave the adopted linear "
                                              "relation and fall continuously to 0 with output (P2E-4): TBD"),
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
    "debt_per_delivery_deficit": (PROVISIONAL, "D accrued per unit of delivery deficit per minute (P2F-7): 1 by "
                                               "construction so far; only its product with the D -> lactate gain "
                                               "shows in lactate: TBD"),
    "oxygen_extraction_reserve": (PROVISIONAL, "maximal over normal oxygen extraction, E_max / E_normal (P2I-2P): "
                                               "consumption stays supply-independent down to the critical "
                                               "delivery demand / reserve, and only the demand left unmet below "
                                               "it is a deficit D integrates. 1 is the pre-P2I-2P model kept as "
                                               "the neutral default (no reserve: any delivery below demand is a "
                                               "deficit), not a physiological value; the value above 1 is TBD. "
                                               "Only reserve x arrival_delivery_ratio reaches D: a reserve r keeps "
                                               "today's GI dynamics only with the arrival band read as ratio / r, "
                                               "a joint faculty decision"),
    "collapse_burden_per_minute": (PROVISIONAL, "collapse burden accrued per minute at full severity (P2F-7): 1 by "
                                                "construction so far: TBD"),
    "debt_clearance_tau_min": (PROVISIONAL, "tau_D_recovery: TBD (KD-S1); 60 min is not approved. D repays "
                                            "only what it accrued: the deficit against demand is never a credit "
                                            "(P2E-2)"),
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
    "collapse_output_threshold": (PROVISIONAL, "output_rel below which the collapse burden accrues (P2E-3): TBD; off "
                                               "(None) by default, synthetic values in tests only"),
    "collapse_burden_limit": (PROVISIONAL, "burden (fraction below the threshold x minutes) at which R moves to a "
                                           "pulseless rhythm (P2E-3): TBD; off by default"),
    "collapse_repayment_tau_min": (PROVISIONAL, "repayment of the burden once output recovers (P2E-3): TBD; None "
                                                "holds the burden"),
    "collapse_terminal_rhythm": (PROVISIONAL, "the pulseless rhythm the collapse rule ends in (P2E-3): the selection "
                                              "rule is TBD"),
    "arrival_circulating_volume_ml": (PROVISIONAL, "SYNTHETIC/CANDIDATE normalization of the shared blood state "
                                                   "(P2I-2T): the circulating volume at arrival, in mL-equivalent, "
                                                   "against which red-cell content and haemoglobin are read. Not a "
                                                   "measured litre and not inferred from the arrival Hb: TBD"),
    "volume_preload_kappa": (PROVISIONAL, "SYNTHETIC/CANDIDATE conversion V = kappa x circulating-volume deviation "
                                          "(P2I-2T). Output reads V only as V / preload_curve_scale_ml, so only "
                                          "kappa / scale is identifiable from the haemodynamics: neither is "
                                          "approved alone. 1 keeps V in mL-equivalent of circulating volume: TBD"),
    "plasma_refill_target_share": (PROVISIONAL, "SYNTHETIC/CANDIDATE share of the shed volume plasma refill restores "
                                                "at most (P2I-2T), and only while the circulation is below arrival; "
                                                "refill carries no red cells: TBD"),
    "plasma_refill_tau_min": (PROVISIONAL, "SYNTHETIC/CANDIDATE time constant of plasma refill toward its target "
                                           "(P2I-2T): TBD"),
    "plasma_refill_capacity_ml": (PROVISIONAL, "SYNTHETIC/CANDIDATE finite interstitial reserve: the most plasma "
                                               "refill can add in an encounter (P2I-2T): TBD"),
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
    """The lactate the core holds above its clearance baseline (mmol/L): auxiliary state, not a function of D."""
    return state.aux.lactate_excess_mmol_l


def lactate_baseline(anchors: Anchors) -> float:
    """The lactate clearance tends to (P2E-2): the arrival lactate less the share the case declares can clear.

    Undeclared, it is the arrival lactate itself: D is never negative, so without a declared
    arrival excess nothing takes lactate below arrival.
    """
    return anchors.lactate - anchors.arrival_lactate_excess


def lactate_after_minute(state: CoreState, profile: CoreProfile) -> float:
    """One minute of lactate kinetics (KD-S1): production from the debt D, first-order clearance.

    dX = k * D - X / tau_lactate, with k = gain / (tau_D * tau_lactate). D accrues while a
    shortfall lasts and repays only without one (P2I-2AC), so under a steady shortfall D and X
    keep rising; lactate lags D, and after perfusion is restored it clears more slowly than D.
    X starts at the arrival excess the case declares (0 undeclared) and is read above the
    clearance baseline (``lactate_baseline``).
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


def case_parameter_provenance(anchors: Anchors, profile: CoreProfile = DEFAULT_PROFILE) -> dict:
    """Each case parameter's value, where it comes from and whether it is calibrated (P2D-8).

    ``source`` is the declared one (``explicit_case``, ``approved_family_default`` or
    ``synthetic_probe``), else ``default_unmapped``. No case parameter is calibrated yet: none
    is mapped from the bank cases, and the defaults are neutral (or, for the preload position,
    provisional).
    """
    notes = {UNMAPPED: "not declared: neutral value", "explicit_case": "declared by the case; not calibrated",
             "approved_family_default": "the family's approved default; not calibrated",
             "synthetic_probe": "synthetic probe value; not a case"}
    unmapped_values = {"preload_fraction": (profile.arrival_preload_fraction,
                                            "not declared: provisional profile default (TBD)"),
                       "intrinsic_sinus_rate": (anchors.hr, "not declared: the arrival HR is read as intrinsic, with "
                                                            "no sympathetic share at arrival")}
    unmapped_notes = {"metabolic_demand_baseline": "not declared: the reference demand, met by the reference delivery",
                      "arrival_oxygen_debt": "not declared: no debt accrued before arrival",
                      "arrival_delivery_ratio": "not declared: arrival delivery read as adequate",
                      "reference_preload_fraction": "not declared: no euvolemic reference, so no explicit volume "
                                                    "deficit",
                      "arrival_lactate_excess": "not declared: the arrival lactate is the clearance baseline, so "
                                                "lactate does not fall below arrival"}
    provenance = {}
    for name in CASE_PARAMETERS:
        source = anchors.declared.get(name, UNMAPPED)
        value, note = getattr(anchors, name), notes[source]
        if value is None and name in unmapped_values:
            value, note = unmapped_values[name]
        elif source == UNMAPPED and name in unmapped_notes:
            note = unmapped_notes[name]
        provenance[name] = {"value": value, "source": source, "calibrated": False, "note": note}
    return provenance


def intrinsic_sinus_rate(anchors: Anchors) -> float:
    """The arrival sinus rate without sympathetic drive (P2E-1): declared, or the observed arrival HR."""
    return anchors.intrinsic_sinus_rate if anchors.intrinsic_sinus_rate is not None else anchors.hr


def arrival_sympathetic_drive(anchors: Anchors, profile: CoreProfile) -> float:
    """The sympathetic drive that, on top of the intrinsic rate, gives the observed arrival HR (P2E-1)."""
    share = anchors.hr - intrinsic_sinus_rate(anchors)
    if share <= 0.0:
        return 0.0
    response = profile.hr_per_sympathetic_drive * (1.0 - anchors.beta_blockade)
    if response <= 0.0:
        raise CoreInvariantError("an arrival sympathetic share needs a positive chronotropic response")
    return share / response


def heart_rate_decomposition(anchors: Anchors, profile: CoreProfile = DEFAULT_PROFILE) -> dict:
    """The observed arrival HR split into intrinsic rate and sympathetic contribution, with its source."""
    return {"observed_arrival_hr": anchors.hr, "intrinsic_sinus_rate": intrinsic_sinus_rate(anchors),
            "arrival_sympathetic_bpm": anchors.hr - intrinsic_sinus_rate(anchors),
            "arrival_sympathetic_drive": arrival_sympathetic_drive(anchors, profile),
            "source": anchors.declared.get("intrinsic_sinus_rate", UNMAPPED)}


def relative_delivery(output_rel: float, hb: float, spo2: float, anchors: Anchors) -> float:
    """Oxygen delivery relative to the arrival delivery: (Q / Q_a) x (Hb / Hb_a) x (SpO2 / SpO2_a) (P2F-6).

    Dimensionless and relative, never an indexed physical DO2 (mL/min/m2): flow, oxygen-carrying
    capacity and saturation each scale it in proportion, and dissolved oxygen is ignored.
    """
    return output_rel * (hb / anchors.hb) * (spo2 / anchors.spo2)


def effective_delivery(delivery_rel: float, anchors: Anchors) -> float:
    """The oxygen delivery index: DO2 relative to the patient's normal resting delivery (P2F-6, P2I-2P).

    The arrival-relative delivery times the case's ``arrival_delivery_ratio`` (arrival DO2 over
    normal resting DO2; 1, the neutral value, reads arrival delivery as normal). At normal
    extraction a delivery index of 1 meets a demand index of 1 (``oxygen_demand``, VO2 demand
    over normal resting consumption): before P2I-2P this unit was described as "the delivery
    that meets the reference demand", which conflated normal delivery with the minimum adequate
    (critical) one. Which deficit is a debt is ``effective_oxygen_deficit``'s to say.
    """
    return anchors.arrival_delivery_ratio * delivery_rel


@dataclass(frozen=True)
class AuthoredArrival:
    """Layer A (P2F-1): what the resident sees at t = 0, as the case authors it."""

    sbp: float
    dbp: float
    map: float
    hr: float
    spo2: float
    respiratory_rate: float
    crt_s: float
    lactate: float
    hb: float
    glucose: float
    k: float
    fio2: float
    rhythm: str
    consciousness_level: int


@dataclass(frozen=True)
class PhysiologicalReference:
    """Layer B (P2F-1): the patient's non-acute reference the core normalizes against.

    ``sources`` names where each declared value comes from (``default_unmapped`` when not).
    """

    intrinsic_sinus_rate: float
    lactate_clearance_baseline: float
    metabolic_demand_baseline: float
    reference_preload_fraction: float | None
    beta_blockade: float
    pump_reserve: float
    sources: Mapping[str, str]


@dataclass(frozen=True)
class ArrivalDynamicState:
    """Layer C (P2F-1): the acute physiology already present when the simulation begins."""

    preload_fraction: float
    volume_deficit_ml: float | None
    oxygen_debt: float
    lactate_excess: float
    sympathetic_drive: float
    sympathetic_bpm: float
    delivery_ratio: float
    oxygen_demand: float
    delivery_deficit: float
    sources: Mapping[str, str]


@dataclass(frozen=True)
class ArrivalLayers:
    authored: AuthoredArrival
    reference: PhysiologicalReference
    dynamic: ArrivalDynamicState

    def to_dict(self) -> dict:
        def plain(record):
            return {item.name: (dict(getattr(record, item.name)) if item.name == "sources"
                                else getattr(record, item.name)) for item in fields(record)}
        return {"authored_observation": plain(self.authored), "physiological_reference": plain(self.reference),
                "arrival_dynamic_state": plain(self.dynamic)}


def arrival_volume_deficit(anchors: Anchors, profile: CoreProfile = DEFAULT_PROFILE) -> float | None:
    """mL-equivalent between the euvolemic reference and the arrival position on the arrival curve (P2F-1).

    Positive when the patient arrives below euvolemia. ``None`` without a declared reference.
    """
    if anchors.reference_preload_fraction is None:
        return None
    return profile.preload_curve_scale_ml * (math.log1p(-arrival_preload(anchors, profile))
                                             - math.log1p(-anchors.reference_preload_fraction))


def arrival_layers(anchors: Anchors, profile: CoreProfile = DEFAULT_PROFILE) -> ArrivalLayers:
    """The three arrival layers of a case (P2F-1): authored observation, reference, dynamic state."""
    def source(name):
        return anchors.declared.get(name, UNMAPPED)

    authored = AuthoredArrival(anchors.sbp, anchors.dbp, (anchors.sbp + 2 * anchors.dbp) / 3, anchors.hr,
                               anchors.spo2, anchors.respiratory_rate, anchors.crt_s, anchors.lactate, anchors.hb,
                               anchors.glucose, anchors.k, anchors.fio2, anchors.rhythm.code.value,
                               anchors.consciousness_level)
    reference = PhysiologicalReference(
        intrinsic_sinus_rate(anchors), lactate_baseline(anchors), anchors.metabolic_demand_baseline,
        anchors.reference_preload_fraction, anchors.beta_blockade, anchors.pump_reserve,
        {name: source(name) for name in ("intrinsic_sinus_rate", "arrival_lactate_excess", "metabolic_demand_baseline",
                                         "reference_preload_fraction", "beta_blockade", "pump_reserve")})
    drive = arrival_sympathetic_drive(anchors, profile)
    dynamic = ArrivalDynamicState(
        arrival_preload(anchors, profile), arrival_volume_deficit(anchors, profile), anchors.arrival_oxygen_debt,
        anchors.arrival_lactate_excess, drive, anchors.hr - intrinsic_sinus_rate(anchors),
        anchors.arrival_delivery_ratio, anchors.metabolic_demand_baseline,
        effective_oxygen_deficit(anchors.metabolic_demand_baseline, anchors.arrival_delivery_ratio,
                                 profile.oxygen_extraction_reserve),
        {name: source(name) for name in ("preload_fraction", "reference_preload_fraction", "arrival_oxygen_debt",
                                         "arrival_lactate_excess", "intrinsic_sinus_rate", "arrival_delivery_ratio",
                                         "metabolic_demand_baseline")})
    return ArrivalLayers(authored, reference, dynamic)


def check_arrival_reconstruction(anchors: Anchors, profile: CoreProfile = DEFAULT_PROFILE) -> Derived:
    """The arrival state, derived, reproduces the authored observation exactly (P2F-1), or this raises.

    Reference and dynamic state change what happens next, never what the resident sees at t = 0.
    """
    derived = derive(arrival_state(anchors, profile), anchors, profile)
    expected = {"sbp": anchors.sbp, "dbp": anchors.dbp, "pulse_rate_bpm": anchors.hr, "spo2": anchors.spo2,
                "respiratory_rate": anchors.respiratory_rate, "crt_s": anchors.crt_s, "lactate": anchors.lactate,
                "consciousness_level": anchors.consciousness_level}
    for name, value in expected.items():
        if not math.isclose(getattr(derived, name), value, rel_tol=0.0, abs_tol=1e-9):
            raise CoreInvariantError(f"{anchors.case_id}: the arrival state reads {name} = {getattr(derived, name)!r}, "
                                     f"not the authored {value!r}")
    return derived


def oxygen_demand(anchors: Anchors, modifiers) -> float:
    """Metabolic oxygen demand for a minute: VO2 demand over normal resting consumption (P2E-2, P2I-2P).

    The case's baseline times every factor declared for the minute (disease or module, and
    transient). No factor declared: the baseline. At normal extraction a delivery index of 1
    meets a demand index of 1; how far extraction can rise is ``oxygen_extraction_reserve``
    (before P2I-2P this unit was "the delivery that meets the reference demand"). The factors
    are TBD; nothing here is a calibrated multiplier.
    """
    return anchors.metabolic_demand_baseline * math.prod(item.factor for item in modifiers)


def delivery_deficit(demand: float, delivery_rel: float) -> float:
    """The delivery index below the demand index (P2E-2): max(0, demand - delivery), never a credit.

    With no extraction reserve this is also the unmet demand; with one it is not (P2I-2P):
    D integrates ``effective_oxygen_deficit``.
    """
    return max(0.0, demand - delivery_rel)


def effective_oxygen_deficit(demand: float, delivery: float, reserve: float) -> float:
    """The oxygen demand left unmet once extraction is exhausted (P2I-2P): max(0, demand - reserve x delivery).

    ``delivery`` is the delivery index (DO2 over normal resting DO2) and ``demand`` the demand
    index (VO2 demand over normal resting VO2); at normal extraction delivery 1 meets demand 1.
    Extraction can rise to ``reserve`` times normal (E_max / E_normal), so consumption is met down
    to the critical delivery ``demand / reserve``; below it the unmet demand, in units of normal
    resting consumption, is the deficit D integrates. ``reserve`` = 1 is the pre-P2I-2P model.
    """
    return max(0.0, demand - reserve * delivery)


#: Oxygen-availability states (P2I-2P), from the supply-to-demand ratio delivery / demand.
OXYGEN_ADEQUATE, OXYGEN_COMPENSATED, OXYGEN_CRITICAL = "ADEQUATE", "COMPENSATED", "CRITICAL"


@dataclass(frozen=True)
class OxygenBalance:
    """One minute's oxygen availability (P2I-2P): read-only, it changes no state."""

    delivery: float
    demand: float
    supply_ratio: float
    required_extraction: float
    critical_delivery: float
    effective_deficit: float
    state: str


def oxygen_balance(delivery: float, demand: float, reserve: float) -> OxygenBalance:
    """Delivery index, demand index and what extraction makes of them (P2I-2P).

    - ADEQUATE: supply ratio >= 1, normal extraction meets demand;
    - COMPENSATED: 1 / reserve <= ratio < 1, raised extraction meets it, no deficit;
    - CRITICAL: ratio < 1 / reserve, extraction exhausted, the unmet demand is the deficit.
    ``required_extraction`` is the extraction demand needs, relative to normal (capped at none).
    With reserve 1 there is no COMPENSATED state (the pre-P2I-2P model).
    """
    ratio = delivery / demand
    deficit = effective_oxygen_deficit(demand, delivery, reserve)
    state = OXYGEN_ADEQUATE if ratio >= 1.0 else OXYGEN_CRITICAL if deficit > 0.0 else OXYGEN_COMPENSATED
    return OxygenBalance(delivery, demand, ratio, math.inf if delivery <= 0.0 else 1.0 / ratio, demand / reserve,
                         deficit, state)


def arrival_state(anchors: Anchors, profile: CoreProfile = DEFAULT_PROFILE) -> CoreState:
    """Arrival, with the reference states the case declares (P2E).

    - R holds the intrinsic sinus rate and the auxiliary state the arrival sympathetic drive,
      so the derived arrival HR is the observed one (P2E-1);
    - the auxiliary state holds the arrival oxygen demand (the case's baseline) and the
      clearable arrival lactate, so the derived arrival lactate is the authored one (P2E-2);
    - D holds the debt accrued before arrival (P2F-3).
    Undeclared, they are the anchored defaults: intrinsic = observed HR and no drive; demand
    met by arrival delivery; no clearable lactate; no arrival debt.
    """
    state = anchored_state(anchors).evolve(D=anchors.arrival_oxygen_debt)
    if state.R.code is RhythmCode.SINUS:
        state = state.evolve(R=replace(state.R, rate_bpm=intrinsic_sinus_rate(anchors)))
    return state.evolve(aux=AuxiliaryState(lactate_excess_mmol_l=anchors.arrival_lactate_excess,
                                           sympathetic_drive=arrival_sympathetic_drive(anchors, profile),
                                           oxygen_demand=anchors.metabolic_demand_baseline))


def circulating_volume(blood: BloodState, profile: CoreProfile) -> float:
    """The circulating volume (mL-equivalent): the arrival normalization plus the blood state's deviation.

    It must stay positive; a state that empties the circulation cannot exist (fail closed).
    """
    volume = profile.arrival_circulating_volume_ml + blood.volume_ml
    if not volume > 0:
        raise CoreInvariantError(f"the circulating volume reached {volume!r} mL-equivalent: it stays positive")
    return volume


def blood_haemoglobin(blood: BloodState, anchors: Anchors, profile: CoreProfile) -> float:
    """Haemoglobin as a concentration (P2I-2T): red-cell content over circulating volume.

    At arrival it is the authored Hb (content 1 in the arrival volume). Losing whole blood takes
    content and volume in the same proportion, so it leaves the concentration where it was;
    volume without red cells (refill, crystalloid) dilutes it; red cells raise it.
    """
    return anchors.hb * blood.red_cells * profile.arrival_circulating_volume_ml / circulating_volume(blood, profile)


def red_cell_content(volume_ml: float, hb_g_dl: float, anchors: Anchors, profile: CoreProfile) -> float:
    """Red-cell content, in units of the arrival content, of ``volume_ml`` of fluid at ``hb_g_dl``."""
    return volume_ml * hb_g_dl / (anchors.hb * profile.arrival_circulating_volume_ml)


def plasma_refill(blood: BloodState, profile: CoreProfile) -> float:
    """Plasma refilled into the circulation in one minute (mL-eq), from the blood state at its start (P2I-2T).

    Minimal model: refill restores part of the circulating-volume deficit the haemorrhage left.
    Its target is ``plasma_refill_target_share`` x the shed volume, never more than
    ``plasma_refill_capacity_ml`` (the interstitial reserve is finite); it approaches that target
    first order with ``plasma_refill_tau_min``, and only while the circulation is below arrival:
    a minute's refill never exceeds the deficit C < 0 at its start, so it never takes the
    circulation above arrival, and with fluids or red cells already above arrival it stops. So it
    is gradual, never passes its target, never runs backwards, carries no red cells (it dilutes)
    and continues after the bleeding stops while a deficit and a gap to the target remain. How
    far fluids damp it below arrival is not modelled. All three values are provisional and TBD.
    """
    target = min(profile.plasma_refill_capacity_ml, profile.plasma_refill_target_share * blood.shed_ml)
    gap, deficit = target - blood.refill_ml, -blood.volume_ml
    if gap <= 0 or deficit <= 0:
        return 0.0
    return min(gap * -math.expm1(-1.0 / profile.plasma_refill_tau_min), deficit)


def plasma_volume_deviation(blood: BloodState, anchors: Anchors, profile: CoreProfile) -> float:
    """Plasma part of the circulating-volume deviation (mL-eq), for reports only (P2I-2T).

    The circulating-volume deviation less the change of red-cell volume, read through a mean
    red-cell haemoglobin concentration (``RED_CELL_HB_G_DL``). No mechanism reads it.
    """
    arrival_red_cell_ml = anchors.hb * profile.arrival_circulating_volume_ml / RED_CELL_HB_G_DL
    return blood.volume_ml - (blood.red_cells - 1.0) * arrival_red_cell_ml


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
    delivery_rel = relative_delivery(output_rel, state.hb, spo2, anchors)
    return output_rel, pressure_rel, spo2, delivery_rel


def arterial_pressures(pressure_rel: float, anchors: Anchors, profile: CoreProfile) -> tuple[float, float]:
    """SBP and DBP from the pressure the state produces, pressure_rel = output x tone (KD-S4, P2E-4).

    - At and above ``low_output_pressure_knee``: the adopted linear relation, arrival less the
      gain times (1 - pressure_rel), never below 0.
    - Below it: both are the knee's values times pressure_rel / knee, so they fall together,
      continuously and monotonically, to 0 as pressure_rel (and so output, at any tone) goes to
      0: pressure proportional to flow times resistance. Sharing the scale keeps SBP above DBP
      below the knee whenever it is above it at the knee. The slope changes at the knee; the
      value does not.

    An arrival pulse pressure narrower than (sbp gain - dbp gain) x (1 - knee), 10 mmHg at the
    defaults, still reaches SBP < DBP above the knee, as before P2E; ``check`` then fails the
    minute closed (§9.8).

    No legacy floor: without output there is no pressure. Tone still lifts DBP and MAP through
    pressure_rel, so a vasoconstricted patient can hold a pressure that does not mean
    perfusion: output, delivery, D and CRT read output, not pressure. Knee and form are TBD.
    """
    def linear(rel):
        return (max(0.0, anchors.sbp - profile.sbp_per_pressure_deficit * (1.0 - rel)),
                max(0.0, anchors.dbp - profile.dbp_per_pressure_deficit * (1.0 - rel)))

    knee = profile.low_output_pressure_knee
    if pressure_rel >= knee:
        return linear(pressure_rel)
    sbp_knee, dbp_knee = linear(knee)
    scale = max(0.0, pressure_rel) / knee
    return sbp_knee * scale, dbp_knee * scale


def collapse_burden_after_minute(state: CoreState, anchors: Anchors, profile: CoreProfile) -> float:
    """One minute of the collapse burden (P2E-3), read on the output at the start of the minute.

    Severity is the share by which output_rel falls below ``collapse_output_threshold`` (0 at
    it, 1 at no output), and the burden adds it every minute: a deeper or a longer fall accrues
    more. With output back at or above the threshold the burden is held, or repaid first order
    with ``collapse_repayment_tau_min`` when declared. The rule is off (None) by default, and
    without a pulse the burden no longer changes. Threshold, limit and repayment are TBD.
    """
    burden = state.aux.collapse_burden
    threshold = profile.collapse_output_threshold
    if threshold is None or not state.R.pulse_present:
        return burden
    severity = max(0.0, threshold - _perfusion(state, anchors, profile)[0]) / threshold
    if severity > 0.0:
        return burden + profile.collapse_burden_per_minute * severity
    if profile.collapse_repayment_tau_min is None:
        return burden
    return burden * math.exp(-1.0 / profile.collapse_repayment_tau_min)


def collapse_reached(state: CoreState, burden: float, profile: CoreProfile) -> bool:
    """Whether the declared collapse criterion is met this minute by a patient who still has a pulse."""
    return (profile.collapse_burden_limit is not None and state.R.pulse_present
            and burden >= profile.collapse_burden_limit)


def terminal_rhythm(state: CoreState, anchors: Anchors, profile: CoreProfile) -> RhythmState:
    """The pulseless rhythm the collapse rule ends in (P2E-3); the selection rule is TBD.

    PEA keeps the organized rhythm: the monitor still counts the rate it had, without a pulse.
    Asystole has none.
    """
    if profile.collapse_terminal_rhythm == "asystole":
        return RhythmState.asystole()
    return RhythmState.pea(min(300.0, derive(state, anchors, profile).monitor_rate_bpm))


def congestion_rate(state: CoreState, anchors: Anchors, profile: CoreProfile) -> float:
    """Lung water added this minute by excess preload on a pump without reserve (KD-S4).

    Only preload added above arrival congests ("additional V", KD-S4), and only above the
    knee of the curve, so arrival stays a fixed point like every other coupling. Both
    positions are read on the current pump's curve (P2D-5): a depressed pump without added
    volume does not congest from this coupling (whether it should is a pending decision). The
    excess is the share of the curve left above max(knee, arrival filling's position) that is
    now used, times how far the pump falls short of normal reserve (the case's reserve times
    the current pump P). A pump with full reserve never congests from preload alone. This
    coupling only adds L; the slow clearance of lung water is ``lung_water_clearance`` (P2D-6).
    """
    if not state.R.pulse_present:
        return 0.0
    start = max(profile.congestion_preload_knee, preload_position(state, anchors, profile, volume=0.0))
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
    - the oxygen-delivery debt D above its arrival value (P2F-3: a debt the patient arrives
      with is already in the arrival drive, and repaying it lowers the drive);
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
    # Absolute drive (P2E-1): the arrival drive plus the stimuli's deviations from arrival.
    target = (arrival_sympathetic_drive(anchors, profile)
              + profile.sympathetic_per_pressure_deficit * (1.0 - pressure_rel)
              + profile.sympathetic_per_debt * (state.D - anchors.arrival_oxygen_debt) / profile.debt_clearance_tau_min
              + profile.sympathetic_per_hypoxaemia_point * hypoxaemia
              + profile.sympathetic_per_hypoglycaemia_mg_dl * hypoglycaemia)
    # P2D-3: the drive is never negative. As its stimuli resolve, the rate falls back to the
    # intrinsic rate of R (below the observed arrival HR when arrival carried a sympathetic
    # share, P2E-1) and no further; a lower rate needs an explicit source that changes R.
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
    # The floor guards against a declared baseline below what any patient reads; it never moves
    # an authored arrival that is already below it.
    lactate = max(min(profile.lactate_floor, anchors.lactate), lactate_baseline(anchors) + lactate_excess(state))
    if not rhythm.pulse_present:
        derived = Derived(minute=state.minute, pulse_present=False, rhythm=rhythm.code,
                          monitor_rate_bpm=rhythm.rate_bpm, pulse_rate_bpm=None, output_rel=0.0,
                          pressure_rel=0.0, delivery_rel=0.0, sbp=None, dbp=None, map=None, spo2=None,
                          respiratory_rate=0.0, crt_s=None, lactate=lactate, consciousness_level=3)
        check(derived)
        return derived
    output_rel, pressure_rel, spo2, delivery_rel = _perfusion(state, anchors, profile)
    if output_rel <= OUTPUT_EPSILON:
        # P2D-2: a pulse and a measurable pressure without output cannot exist. The collapse rule
        # (P2E-3), when declared, moves R to arrest once its burden criterion is met; output that
        # reaches zero before that, or with no rule declared, stops the run.
        raise UnresolvedBoundary(
            f"minute {state.minute}: effective output reached zero while a pulse is present and no declared "
            "terminal transition applied (the collapse rule is off or its criterion is not met; threshold and "
            "dwell are TBD), so the run stops instead of showing a pulse and a blood pressure without output")
    sbp, dbp = arterial_pressures(pressure_rel, anchors, profile)
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
