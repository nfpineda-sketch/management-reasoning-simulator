"""Phase 2 shadow core, P2K-3: effective ventilation recruited by the acid burden, never by the respiratory rate.

Shadow only, a candidate off unless called: nothing in the core's step, derive or arrival state reads this module, so
every default run, the golden, the closed records and the P2K-2 candidate stay as they were. P2K-2 made W proportional to
RR / intrinsic RR, so an intrinsic RR of 12 to 16 implied a resting PaCO2 up to about 74 mmHg
(FREQUENCY_TO_VENTILATION_OVERCONSTRAINT). The faculty's mapping (2026-10-31) replaces it for the candidate:

    ventilatory_capacity = ventilation_efficiency x (1 + acid_to_ventilation_gain x metabolic_acid_burden)
    W = ventilatory_capacity / metabolic demand ratio
    PaCO2 = PaCO2_reference / W

RR and W are two outputs of the one acid burden: RR from the drive (P2K-2's rate_from_drive, unchanged), W from the
recruited capacity. The recruitment term is the implicit tidal-volume and dead-space response to the acid load, never a
tidal-volume state. W reads no RR, no intrinsic RR, no drive gain, no lactate, no D and no W channel; with no burden, the
reference efficiency and the baseline demand it is 1 and PaCO2 is the reference (40 mmHg) at any intrinsic RR.

The metabolic demand is the ratio of the minute's oxygen demand to the patient's baseline demand (the case's
metabolic_demand_baseline, which carries the demand class), as in P2K-2: W = 1 is the ventilation that matches the
patient's own baseline CO2 production, so the demand class reaches W only through the deficit and the burden. The
absolute index is the alternative semantics, reported as a sensitivity, never used here.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from .derived import CoreProfile, carbonic_ph, respiration
from .state import Anchors, CoreInvariantError, CoreState

#: What each P2K-3 quantity is, recorded with the physiology.
STATUS = {"acid_to_ventilation_gain": "EXPLORATORY (per mEq/L); no value approved",
          "paco2_reference_mmhg": "COMMON_REFERENCE_PROVISIONAL (the profile's 40 mmHg); not approved. Here it is the "
                                  "PaCO2 at W = 1 (no burden, baseline demand, efficiency 1), not the arrival-PaCO2 "
                                  "fallback derived.arrival_paco2 gives it in P2K-2; the authored arrival PaCO2 only "
                                  "filters the arrival (+/- 3)",
          "ventilation_efficiency": "STRUCTURAL_REFERENCE 1 for the GI cases; below 1 only in synthetic probes; not a "
                                    "universal constant",
          "demand": "the oxygen demand over the patient's baseline demand (BASELINE_RELATIVE)",
          "tidal_volume": "IMPLICIT: no tidal-volume, dead-space, mechanics or fatigue state"}


@dataclass(frozen=True)
class VentilationCandidate:
    """The P2K-3 candidate's one new parameter: the acid burden's recruitment of effective ventilation (per mEq/L)."""

    acid_to_ventilation_gain: float

    def __post_init__(self):
        value = self.acid_to_ventilation_gain
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0.0:
            raise CoreInvariantError("the acid-to-ventilation gain is finite and non-negative")


def ventilation_recruitment(burden: float, gain: float) -> float:
    """1 + acid_to_ventilation_gain x the metabolic acid burden: the recruited share of the baseline ventilation."""
    return 1.0 + gain * burden


def ventilatory_capacity(burden: float, efficiency: float, gain: float) -> float:
    """Effective alveolar ventilation relative to the patient's baseline: efficiency x recruitment. No RR term."""
    return efficiency * ventilation_recruitment(burden, gain)


def effective_ventilation(capacity: float, demand_ratio: float) -> float:
    """W = capacity / (demand / baseline demand): 1 matches the baseline CO2 production, above 1 is relative
    hyperventilation, below 1 relative hypoventilation."""
    return capacity / demand_ratio


def paco2_from_ventilation(ventilation: float, reference: float) -> float:
    """PaCO2 = PaCO2_reference / W (= reference x demand ratio / capacity)."""
    return reference / ventilation


@dataclass(frozen=True)
class VentilatedRespiration:
    """One minute of the P2K-3 candidate: P2K-2's drive and RR, and the recruited effective ventilation beside them.

    ``frequency_drive`` is RR - intrinsic RR (the drive's share of the rate); ``recruitment`` and ``capacity`` are the
    ventilation side; W, PaCO2 and pH never read the rate. PaCO2 and pH are None without breathing (no pulse)."""

    intrinsic_rr: float
    acid_burden: float
    bicarbonate: float
    drive: float
    respiratory_rate: float
    frequency_drive: float
    efficiency: float
    recruitment: float
    capacity: float
    demand_ratio: float
    ventilation: float
    paco2_reference: float
    paco2: float | None
    ph: float | None


def ventilated_respiration(state: CoreState, anchors: Anchors, profile: CoreProfile,
                           candidate: VentilationCandidate) -> VentilatedRespiration:
    """The P2K-3 candidate at one state: the burden, HCO3, drive and RR are P2K-2's (derived.respiration, with its
    acid-base guard and its HCO3 boundary); W is the recruited capacity over the demand ratio; PaCO2 the reference over W;
    pH from HCO3 and PaCO2. Nothing here feeds back into the state."""
    base = respiration(state, anchors, profile)
    demand_ratio = state.aux.oxygen_demand / anchors.metabolic_demand_baseline
    recruitment = ventilation_recruitment(base.acid_burden, candidate.acid_to_ventilation_gain)
    capacity = ventilatory_capacity(base.acid_burden, profile.ventilation_efficiency, candidate.acid_to_ventilation_gain)
    ventilation = effective_ventilation(capacity, demand_ratio) if state.R.pulse_present else 0.0
    paco2 = paco2_from_ventilation(ventilation, profile.paco2_reference_mmhg) if ventilation > 0.0 else None
    return VentilatedRespiration(base.intrinsic_rr, base.acid_burden, base.bicarbonate, base.drive,
                                 base.respiratory_rate, base.respiratory_rate - base.intrinsic_rr if state.R.pulse_present
                                 else 0.0, profile.ventilation_efficiency, recruitment, capacity, demand_ratio,
                                 ventilation, profile.paco2_reference_mmhg, paco2,
                                 None if paco2 is None else carbonic_ph(base.bicarbonate, paco2))


def arrival_paco2(arrival_burden: float, profile: CoreProfile, candidate: VentilationCandidate,
                  demand_ratio: float = 1.0) -> float:
    """The PaCO2 the candidate predicts at arrival (the burden from the authored HCO3): predicted, never anchored."""
    capacity = ventilatory_capacity(arrival_burden, profile.ventilation_efficiency, candidate.acid_to_ventilation_gain)
    return paco2_from_ventilation(effective_ventilation(capacity, demand_ratio), profile.paco2_reference_mmhg)
