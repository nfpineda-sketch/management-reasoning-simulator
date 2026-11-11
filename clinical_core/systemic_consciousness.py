"""PHASE2_AMENDMENT_2: mechanistic systemic consciousness and soft circulatory collapse (GI first; shadow only).

This module is the physiology of the second amendment to the closed Phase-2 common core, and it is OFF unless a profile
declares it (``CoreProfile.amendment_2``, None by default). With it off nothing in the core moves: every committed
profile, golden and digest is the one the first amendment certified. It adds, for the GI family first and as a common
architecture for the others, three things the faculty decided on 2026-11-10 (A2-FD-011 to A2-FD-022):

    F  the reversible systemic encephalopathy burden, a second accumulated state (``aux.systemic_encephalopathy_burden``),
       distinct from D (the long-horizon oxygen-delivery debt), from N (the primary neurologic state) and from the
       collapse burden. The INSTANTANEOUS signal drives F; the signal itself never enters the observable.
    the consciousness impairment, a bounded coordinate in [0, 1]:  I = max(primary, F, collapse contribution)
       with each contributor kept apart for provenance (PRIMARY_NEUROLOGIC, SYSTEMIC_ENCEPHALOPATHY,
       CIRCULATORY_COLLAPSE). It REPLACES the direct SBP and SpO2 ladders, which are duplicative; they stay only in the
       historical reconstruction. No direct pressure, SpO2 or lactate input reaches consciousness.
    the soft circulatory-collapse state, NONE / IMPENDING / ESTABLISHED, from the existing ``aux.collapse_burden`` slot,
       fed by the CONJUNCTION (the minimum, never the maximum) of a perfusion-failure signal and a delivery-failure
       signal. A pulse-less state is the separate, immediate, structurally sufficient hard path.

The coordinates are ARRIVAL-RELATIVE (A2-FD-012, A2-FD-019): relative delivery is the current effective oxygen delivery over
the arrival's, and relative perfusion is the common pressure coordinate (output x tone) over its arrival value, which is 1.
This does not say the patient is physiologically normal at arrival: the authored encounter begins at a known observed
neurological baseline and the deterioration is modelled from it. No healthy pre-arrival delivery is inferred.

Every number below is a FACULTY_DEFINED_DEVELOPMENT_BEHAVIORAL_REGION (A2-FD-022): a region with LOW, CENTER_REFERENCE and
HIGH witnesses where a point is technically needed, never a clinical calibration, a production threshold or a
resident-facing safety threshold, and never fitted to a case. Nothing here terminates an encounter: the core exposes
structured state and the runtime decides what it means. The opioid-specific mechanisms (a central depressant on
consciousness, a respiratory-arrest state, assisted ventilation) are deferred and not added.

Cycle: this module imports the certified candidates (P2L-2's relaxation memory, ``encephalopathy.burden_after``) and the
core's ``derived`` lazily from the two hooks that call it, so the core's own modules never import it at load.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from . import encephalopathy as en
from .state import Anchors, CoreInvariantError, CoreState

REVISION = "PHASE2_AMENDMENT_2"
DECIDED = "2026-11-10"
STATE_FIELD = "systemic_encephalopathy_burden"

#: The development observable categories (A2-FD-006 / A2-FD-016): educational simulator categories, not a GCS.
CATEGORY_CUTS = (0.25, 0.50, 0.80)
CATEGORIES = ("NO_MATERIAL_OBSERVABLE_IMPAIRMENT", "SOMNOLENT", "OBTUNDED", "UNRESPONSIVE")
#: The lowest impairment of each category: how an authored arrival level reads on the impairment coordinate.
ARRIVAL_FLOOR = (0.0,) + CATEGORY_CUTS

PRIMARY, SYSTEMIC, COLLAPSE = "PRIMARY_NEUROLOGIC", "SYSTEMIC_ENCEPHALOPATHY", "CIRCULATORY_COLLAPSE"
NO_COLLAPSE, IMPENDING, ESTABLISHED = "NONE", "IMPENDING", "ESTABLISHED"
NO_PULSE, SOFT = "NO_PULSE", "SOFT_PATH"
FIELDS = ("delivery_normal", "delivery_severe", "burden_rise_tau", "burden_clear_tau", "perfusion_normal",
          "perfusion_severe", "collapse_rise_tau", "collapse_clear_tau", "impending_burden", "established_burden")

#: The faculty's behavioural regions (A2-FD-013, A2-FD-015, A2-FD-020), derived in docs/revision/PHASE2_AMENDMENT_2.md.
REGIONS = {
    "delivery_normal": (0.70, 0.80, "relative delivery at which the systemic signal begins (0 at or above it)"),
    "delivery_severe": (0.45, 0.55, "relative delivery at which the systemic signal is complete (1 at or below it)"),
    "burden_rise_tau": (1.443, 2.485, "F rise: 1 min of extreme signal leaves F < 0.50 and 4 min reach >= 0.80"),
    "burden_clear_tau": (6.38, 10.64, "F fall: from 0.80 to below 0.50 in about 3 to 5 min once the signal is gone"),
    "perfusion_normal": (0.50, 0.60, "relative perfusion at which the perfusion-failure signal begins"),
    "perfusion_severe": (0.30, 0.40, "relative perfusion at which the perfusion-failure signal is complete"),
    "collapse_rise_tau": (1.5, 2.2, "collapse burden rise toward the combined signal"),
    "collapse_clear_tau": (6.0, 8.0, "collapse burden fall: established to cleared in about 3 to 5 min"),
    "impending_burden": (0.35, 0.39, "burden of impending collapse: a severe combined signal sustained 2 to 4 min"),
    "established_burden": (0.55, 0.70, "burden of established collapse: an extreme combined signal sustained 1 to 3 min"),
}
#: Where each magnitude comes from (A2-012B): the faculty's behaviour, the existing equation, or a structural choice.
IDENTIFIABILITY = {
    "delivery_normal": "FACULTY_DEFINED_FROM_BEHAVIOR", "delivery_severe": "FACULTY_DEFINED_FROM_BEHAVIOR",
    "burden_rise_tau": "DERIVED_FROM_EXISTING_EQUATION", "burden_clear_tau": "DERIVED_FROM_EXISTING_EQUATION",
    "perfusion_normal": "FACULTY_DEFINED_FROM_BEHAVIOR", "perfusion_severe": "FACULTY_DEFINED_FROM_BEHAVIOR",
    "collapse_rise_tau": "WEAKLY_IDENTIFIED", "collapse_clear_tau": "WEAKLY_IDENTIFIED",
    "impending_burden": "WEAKLY_IDENTIFIED", "established_burden": "WEAKLY_IDENTIFIED",
}
STATUS = "FACULTY_DEFINED_DEVELOPMENT_BEHAVIORAL_REGION"


@dataclass(frozen=True)
class Amendment2Profile:
    """The declared magnitudes of the amendment, every one a development behavioural region's point."""

    delivery_normal: float
    delivery_severe: float
    burden_rise_tau: float
    burden_clear_tau: float
    perfusion_normal: float
    perfusion_severe: float
    collapse_rise_tau: float
    collapse_clear_tau: float
    impending_burden: float
    established_burden: float

    def __post_init__(self):
        for name in FIELDS:
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise CoreInvariantError(f"{name} is a finite number")
        if not 0.0 < self.delivery_severe < self.delivery_normal <= 1.0:
            raise CoreInvariantError("the delivery ramp runs from a normal bound at or below arrival (1) down to a "
                                     "severe bound above 0")
        if not 0.0 < self.perfusion_severe < self.perfusion_normal <= 1.0:
            raise CoreInvariantError("the perfusion ramp runs from a normal bound at or below arrival (1) down to a "
                                     "severe bound above 0")
        if not 0.0 < self.burden_rise_tau < self.burden_clear_tau:
            raise CoreInvariantError("F rises faster than it clears: 0 < tau_rise < tau_clear")
        if not 0.0 < self.collapse_rise_tau < self.collapse_clear_tau:
            raise CoreInvariantError("the collapse burden rises faster than it clears: 0 < tau_rise < tau_clear")
        if not 0.0 < self.impending_burden <= self.established_burden < 1.0:
            raise CoreInvariantError("0 < impending <= established < 1: the burden is a share of the combined signal")

    def to_dict(self) -> dict:
        return {name: getattr(self, name) for name in FIELDS}


#: LOW, CENTER_REFERENCE and HIGH witnesses: every magnitude at the low, middle and high end of its region. They exist to
#: test with and to bound conclusions; none is a preferred value and none is a calibration.
WITNESSES = {
    "LOW": Amendment2Profile(0.70, 0.45, 1.5, 6.4, 0.50, 0.30, 1.5, 6.0, 0.35, 0.55),
    "CENTER_REFERENCE": Amendment2Profile(0.75, 0.50, 1.65, 8.5, 0.55, 0.35, 2.0, 8.0, 0.39, 0.65),
    "HIGH": Amendment2Profile(0.80, 0.55, 1.85, 10.5, 0.60, 0.40, 2.2, 8.0, 0.38, 0.70),
}


def development_profile(name: str = "CENTER_REFERENCE") -> Amendment2Profile:
    """A witness of the development region. The amendment is off in every committed profile: this is explicit opt-in."""
    return WITNESSES[name]


# -- the arrival-relative coordinates -----------------------------------------------------------------------------------

def relative_delivery(delivery_rel: float, anchors: Anchors) -> float:
    """Current effective oxygen delivery over the arrival's (A2-FD-012): 1 at arrival by definition.

    The core's effective delivery is the arrival-relative delivery times the case's arrival delivery ratio, and the arrival
    state's relative delivery is 1, so the quotient is explicit and the denominator is the case's own arrival value. A
    denominator that is not above 0 has no arrival to be relative to: the run refuses rather than infer a healthy value."""
    arrival = anchors.arrival_delivery_ratio
    if not (isinstance(arrival, (int, float)) and math.isfinite(arrival) and arrival > 0.0):
        raise CoreInvariantError("the arrival effective delivery is above 0: there is no arrival to be relative to")
    return (arrival * delivery_rel) / arrival


def relative_perfusion(pressure_rel: float) -> float:
    """The common perfusion-pressure coordinate (output x tone), already relative to arrival (A2-FD-019): 1 at arrival."""
    return pressure_rel


def _ramp(value: float, normal: float, severe: float) -> float:
    """0 at or above ``normal``, 1 at or below ``severe``, linear between: the low-side monotone saturating signal."""
    return en.ramp(value, en.SignalMapping(normal, severe), en.LOW)


def delivery_failure(relative_delivery_value: float, profile: Amendment2Profile) -> float:
    """The systemic signal that drives F and the delivery side of the collapse conjunction: one scale for both."""
    return _ramp(relative_delivery_value, profile.delivery_normal, profile.delivery_severe)


def perfusion_failure(relative_perfusion_value: float, profile: Amendment2Profile) -> float:
    return _ramp(relative_perfusion_value, profile.perfusion_normal, profile.perfusion_severe)


def collapse_signal(perfusion: float, delivery: float) -> float:
    """Soft collapse needs BOTH failures at once (A2-FD-018): the minimum. Neither alone creates it, and the maximum, which
    would let one failure alone do it, is exactly what the faculty rejected."""
    return min(perfusion, delivery)


def _coordinates(state: CoreState, anchors: Anchors, core_profile):
    from . import derived as dv
    _, pressure_rel, _, delivery_rel = dv._perfusion(state, anchors, core_profile)
    return relative_delivery(delivery_rel, anchors), relative_perfusion(pressure_rel)


# -- F, the systemic encephalopathy burden --------------------------------------------------------------------------------

def systemic_burden(state: CoreState) -> float:
    """F as the state holds it: 0 where the amendment has not yet written it (arrival)."""
    value = state.aux.systemic_encephalopathy_burden
    return 0.0 if value is None else value


def systemic_burden_after(state: CoreState, anchors: Anchors, core_profile) -> float:
    """F after one minute, driven by the signal of the minute's START state (the P2L-2 relaxation, exactly).

    The instantaneous signal is a bounded monotone function of relative delivery alone: no pressure, SpO2 or lactate is read
    here (they act through the delivery and the debt upstream). Without a pulse the signal is complete: arrest is the
    maximal systemic insult. F relaxes toward the signal with tau_rise while the signal is above it and tau_clear after."""
    profile = core_profile.amendment_2
    if state.R.pulse_present:
        signal = delivery_failure(_coordinates(state, anchors, core_profile)[0], profile)
    else:
        signal = 1.0
    memory = en.EncephalopathyProfile(burden_rise_tau=profile.burden_rise_tau, burden_clear_tau=profile.burden_clear_tau)
    return en.burden_after(systemic_burden(state), signal, 1.0, memory)


# -- the collapse burden (the existing aux slot) and the predicate -----------------------------------------------------------

def collapse_burden_after(state: CoreState, anchors: Anchors, core_profile) -> float:
    """The soft-collapse burden after one minute, in the existing ``aux.collapse_burden`` slot, as a share of the combined
    signal: it relaxes toward min(perfusion failure, delivery failure) with its own rise and a slower clearance, so it needs
    persistence to build, and recovery needs both channels restored for sustained time. Without a pulse it no longer
    changes: that is arrest, the hard path, not collapse."""
    profile = core_profile.amendment_2
    if not state.R.pulse_present:
        return state.aux.collapse_burden
    delivery, perfusion = _coordinates(state, anchors, core_profile)
    signal = collapse_signal(perfusion_failure(perfusion, profile), delivery_failure(delivery, profile))
    memory = en.EncephalopathyProfile(burden_rise_tau=profile.collapse_rise_tau, burden_clear_tau=profile.collapse_clear_tau)
    return en.burden_after(state.aux.collapse_burden, signal, 1.0, memory)


def collapse_state(burden: float, pulse_present: bool, profile: Amendment2Profile) -> dict:
    """The circulatory-collapse predicate. NO PULSE is immediate and structurally sufficient; the soft path reads the burden
    in two bands, so recovery passes through IMPENDING on its way down and the state cannot flip at a single boundary
    unless the burden itself does."""
    if not pulse_present:
        return {"state": ESTABLISHED, "basis": NO_PULSE}
    if burden >= profile.established_burden:
        return {"state": ESTABLISHED, "basis": SOFT}
    if burden >= profile.impending_burden:
        return {"state": IMPENDING, "basis": SOFT}
    return {"state": NO_COLLAPSE, "basis": None}


# -- consciousness --------------------------------------------------------------------------------------------------------

def primary_neurologic(state: CoreState, anchors: Anchors) -> float:
    """The primary neurologic contribution: N, read as itself and never written by a systemic cause, and the authored arrival
    level as the known observed neurological baseline (its category's lower edge). Static in the encounter."""
    return max(en.primary_neurologic_impairment(state.N), ARRIVAL_FLOOR[anchors.consciousness_level])


def category_index(impairment: float) -> int:
    return sum(1 for cut in CATEGORY_CUTS if impairment >= cut)


def readout(state: CoreState, anchors: Anchors, core_profile, pressure_rel: float | None = None,
            delivery_rel: float | None = None) -> dict:
    """Everything the amendment says of consciousness and collapse at one state, never writing it: the impairment, who
    set it, its observable category, and the structured collapse predicate. Reads F and the collapse burden the state holds
    (and the arrival-relative coordinates only for the instantaneous signal that is reported, never used for the level)."""
    profile = core_profile.amendment_2
    pulse = state.R.pulse_present
    primary = primary_neurologic(state, anchors)
    systemic = systemic_burden(state)
    collapse = collapse_state(state.aux.collapse_burden, pulse, profile)
    collapse_part = 1.0 if collapse["state"] == ESTABLISHED else 0.0
    parts = {PRIMARY: primary, SYSTEMIC: systemic, COLLAPSE: collapse_part}
    impairment = max(parts.values())
    index = category_index(impairment)
    reading = {"pulse": pulse}
    if pulse and pressure_rel is not None and delivery_rel is not None:
        delivery, perfusion = relative_delivery(delivery_rel, anchors), relative_perfusion(pressure_rel)
        reading.update(relative_delivery=delivery, relative_perfusion=perfusion,
                       delivery_failure=delivery_failure(delivery, profile),
                       perfusion_failure=perfusion_failure(perfusion, profile))
    return {"impairment": impairment, "contributors": parts,
            "dominant": [name for name, value in parts.items() if value == impairment and impairment > 0.0],
            "category": CATEGORIES[index], "category_index": index, "collapse": collapse, "instantaneous": reading,
            "predicates": {"circulatory_collapse": collapse["state"],
                           "severe_consciousness_impairment": impairment >= CATEGORY_CUTS[-1]}}


def consciousness_level(state: CoreState, anchors: Anchors, core_profile) -> int:
    """The observable level, 0 to 3, of the impairment: what ``derive`` reports where the amendment is declared. It replaces
    the direct pressure and SpO2 ladders, which no longer reach consciousness."""
    return readout(state, anchors, core_profile)["category_index"]
