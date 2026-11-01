"""Phase 2 shadow core, P2L-2: the common systemic-encephalopathy architecture of observable consciousness (candidate).

Shadow only, a candidate off unless called: nothing in the core's step, derive or arrival state reads this module, and it
writes no state, so every default run, the golden, the closed records and derive's legacy consciousness ladder stay as they
were (that ladder, and the authored arrival floor it keeps, are LEGACY_REFERENCE_ONLY: this candidate never reads them).
The faculty's composition (2026-11-01):

    primary_neurologic_impairment         = N, on the common impairment scale [0, 1]   (N: primary neurologic state only)
    acute systemic brain-stress signals   s_k in [0, 1], one per mechanism, each from one certified core reading
    systemic_acute_brain_stress           S = max_k s_k                                 (never a sum; no synergy term)
    systemic_encephalopathy_burden        F >= 0, relaxes toward S: tau_rise while S > F, tau_clear (> tau_rise) after
    observable_consciousness_impairment   I = max(N, S, F)                              (never a sum)

The scale is structural: 0 is no contribution, 1 the maximal impairment a structural probe uses; 1 is not an approved coma
threshold, and no impairment is mapped to an observed mental-status category here. The six acute signals read MAP (the
cerebral-perfusion-pressure proxy; no SBP), the effective oxygen-delivery deficit, SpO2, pH, PaCO2 (apart from pH) and
glucose; never lactate, D, the heart rate or the authored arrival level. Each maps its reading through a monotone
saturating ramp between a 'normal' bound (no contribution) and a 'severe' bound (maximal); no bound and no time constant
has a committed value: every physiological signal is UNMAPPED and the memory UNSET until the faculty declares them, so
the architecture is exercised with synthetic normalized inputs (P2L-2-2, option A).

F is an auxiliary physiological state of this candidate layer, not a canonical channel: reversible accumulated cerebral
dysfunction caused by systemic insults, distinct from N, from D (the oxygen-delivery debt), from lactate and from any
observed category. It is driven by S alone, never by N, and never feeds back into the core.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from .derived import CoreProfile, acute_deficit_signal, derive
from .state import Anchors, CoreInvariantError, CoreState

REVISION = "P2L-2"
LOW, HIGH = "low", "high"
#: The acute systemic brain-stress signals: the certified core reading each maps, the side on which it impairs, and what
#: it means. No lactate, D, heart rate, SBP or authored arrival level.
SIGNALS = {
    "cerebral_hypoperfusion": ("map", LOW, "mean arterial pressure as the cerebral-perfusion-pressure proxy (no ICP is "
                                           "modelled; autoregulation enters through the bounds); without a pulse it is "
                                           "maximal by definition (circulatory arrest)"),
    "oxygen_deficit": ("deficit_fraction", HIGH, "derived.acute_deficit_signal: the current effective oxygen-delivery "
                                                 "deficit over the current demand (0 to 1); no D, no lactate"),
    "hypoxaemia": ("spo2", LOW, "arterial oxygenation (derive's SpO2), its own input beside the deficit: the systemic "
                                "deficit with its extraction reserve misses cerebral hypoxaemia (P2L-1)"),
    "acidemia": ("ph", LOW, "the current arterial pH of the respiratory closure; any acidemia lowers it, so an acute "
                            "hypercapnia also carries some; the maximum keeps the two from adding"),
    "hypercapnia": ("paco2", HIGH, "the current PaCO2 of the respiratory closure, read apart from pH"),
    "hypoglycaemia": ("glucose", LOW, "CoreState.glucose (absolute, mg/dL)"),
}
#: A modifier the faculty classified for later (P2L-2-12), never implemented here.
FUTURE_MODIFIERS = {
    "pharmacologic_cns_depression": (
        "FUTURE_COMMON_SYSTEMIC_OR_PHARMACOLOGIC_MODIFIER: a sedative or opioid family may need its own signal, entering "
        "the observable maximum like the systemic signals and never written into N; whether it also loads the systemic "
        "memory, or carries its own drug kinetics, is that family's decision")}
#: Status of every part, recorded with the physiology.
STATUS = {"N": "PRIMARY_NEUROLOGIC_STATE (faculty, 2026-11-01): static during the encounter, no recovery kinetics; no "
               "systemic cause and no pharmacologic depression is written into it; state.py's closed wording ('CNS "
               "depression / neurological state') is kept for the closed records and superseded for this candidate",
          "signals": "STRUCTURALLY_DEFINED_BUT_CLINICALLY_UNIDENTIFIED: no bound has a committed value (UNMAPPED)",
          "ramp_shape": "STRUCTURAL_SHAPE_PROVISIONAL: linear between the two bounds, saturating at 0 and 1; any "
                        "monotone saturating shape is admissible, none is approved",
          "aggregation": "MAXIMUM (faculty): no sum and no interaction term",
          "memory": "STRUCTURALLY_DEFINED_BUT_CLINICALLY_UNIDENTIFIED: tau_rise and tau_clear UNSET; never derived from "
                    "tau_D, never fitted to the GI cases; 'sufficiently severe' stress is the signals' own normal bound "
                    "(below it a signal reads 0 and loads nothing), no second threshold",
          "availability": "S is the maximum of the available signals: with a signal UNAVAILABLE (no respiratory closure) "
                          "or UNMAPPED it is a lower bound, and the reasons say which",
          "arrival": "no arrival floor: an arrival impairment comes from N, S, a declared pre-arrival burden F0 or another "
                     "declared cause; an authored mental-status label is never read",
          "legacy": "derive's consciousness_level (SBP 80 / 65, SpO2 87 / 80, authored arrival floor): "
                    "LEGACY_REFERENCE_ONLY",
          "category": "no mapping from the impairment to an observed mental-status category (pending faculty)"}


@dataclass(frozen=True)
class SignalMapping:
    """One signal's ramp: 0 on the normal side of ``normal``, 1 at or past ``severe``, linear between."""

    normal: float
    severe: float


@dataclass(frozen=True)
class EncephalopathyProfile:
    """The candidate's declared numbers. Committed default: nothing declared (every signal UNMAPPED, the memory UNSET)."""

    mappings: tuple[tuple[str, SignalMapping], ...] = ()
    burden_rise_tau: float | None = None
    burden_clear_tau: float | None = None

    def __post_init__(self):
        names = [name for name, _ in self.mappings]
        if len(set(names)) != len(names) or not set(names) <= set(SIGNALS):
            raise CoreInvariantError("each mapping names one acute signal, once")
        for name, mapping in self.mappings:
            if not all(math.isfinite(v) for v in (mapping.normal, mapping.severe)):
                raise CoreInvariantError(f"the {name} bounds are finite")
            low = SIGNALS[name][1] == LOW
            if (mapping.severe >= mapping.normal) if low else (mapping.severe <= mapping.normal):
                raise CoreInvariantError(f"the {name} severe bound lies past its normal bound, on its impaired side")
        if (self.burden_rise_tau is None) != (self.burden_clear_tau is None):
            raise CoreInvariantError("the memory declares its rise and clearance time constants together, or neither")
        if self.burden_rise_tau is not None:
            if not (math.isfinite(self.burden_rise_tau) and math.isfinite(self.burden_clear_tau)
                    and 0.0 < self.burden_rise_tau < self.burden_clear_tau):
                raise CoreInvariantError("the memory rises faster than it clears: 0 < tau_rise < tau_clear")

    def mapping(self, name: str) -> SignalMapping | None:
        return dict(self.mappings).get(name)

    @property
    def memory_declared(self) -> bool:
        return self.burden_rise_tau is not None


DEFAULT_ENCEPHALOPATHY = EncephalopathyProfile()


def readings(state: CoreState, anchors: Anchors, profile: CoreProfile, gas=None) -> dict:
    """What the signals read at one core state, through the certified core, never writing it. ``gas`` is the respiratory
    closure's reading at that state (ventilation.ventilated_respiration, at a gain its caller carries as uncertainty):
    without it pH and PaCO2 are unavailable, never assumed normal."""
    d = derive(state, anchors, profile)
    pulse = d.pulse_present
    return {"pulse": pulse, "map": d.map, "spo2": d.spo2, "glucose": state.glucose,
            "deficit_fraction": acute_deficit_signal(state, anchors, profile) if pulse else None,
            "ph": None if gas is None else gas.ph, "paco2": None if gas is None else gas.paco2}


def ramp(value: float, mapping: SignalMapping, side: str) -> float:
    """The monotone saturating map from a reading to the impairment scale."""
    span = mapping.normal - mapping.severe if side == LOW else mapping.severe - mapping.normal
    excess = mapping.normal - value if side == LOW else value - mapping.normal
    return min(1.0, max(0.0, excess / span))


@dataclass(frozen=True)
class AcuteSignals:
    """The six acute signals at one state: a value in [0, 1], or None with the reason (UNMAPPED / UNAVAILABLE)."""

    values: tuple[tuple[str, float | None], ...]
    reasons: tuple[tuple[str, str], ...]

    def value(self, name: str) -> float | None:
        return dict(self.values)[name]


def acute_signals(reading: dict, profile: EncephalopathyProfile) -> AcuteSignals:
    values, reasons = [], []
    for name, (key, side, _) in SIGNALS.items():
        if name == "cerebral_hypoperfusion" and not reading["pulse"]:
            values.append((name, 1.0))
            reasons.append((name, "ARREST"))
            continue
        mapping, value = profile.mapping(name), reading.get(key)
        if value is None:
            values.append((name, None))
            reasons.append((name, "UNAVAILABLE"))
        elif mapping is None:
            values.append((name, None))
            reasons.append((name, "UNMAPPED"))
        else:
            values.append((name, ramp(value, mapping, side)))
            reasons.append((name, "MAPPED"))
    return AcuteSignals(tuple(values), tuple(reasons))


def _on_scale(value: float, what: str) -> float:
    if not (math.isfinite(value) and 0.0 <= value <= 1.0):
        raise CoreInvariantError(f"{what} lies on the impairment scale [0, 1]")
    return value


def systemic_acute_brain_stress(signals: dict) -> float:
    """S = the maximum of the available acute signals (0 when none is available). Never a sum: correlated insults of one
    shock (hypotension, delivery deficit, acidemia) are not independent additive injuries."""
    return max((_on_scale(v, "an acute signal") for v in signals.values() if v is not None), default=0.0)


def primary_neurologic_impairment(n: float) -> float:
    """N read as the primary neurologic impairment, on the common scale; static in the encounter."""
    return _on_scale(n, "primary N")


def primary_from_state(state: CoreState) -> float:
    """The candidate's one reader of N: the primary neurologic impairment of a state (never a systemic signal)."""
    return primary_neurologic_impairment(state.N)


def burden_after(burden: float, stress: float, dt: float, profile: EncephalopathyProfile) -> float:
    """F after dt with S held over the step: exact first-order relaxation toward S, tau_rise while S > F and tau_clear
    otherwise. It stays between F and S (never negative, never past S), falls monotonically once S is below F, and reads
    no N, D, lactate or authored level."""
    if not profile.memory_declared:
        raise CoreInvariantError("the systemic memory has no declared time constants (UNSET)")
    _on_scale(burden, "the systemic burden")
    _on_scale(stress, "the acute stress")
    if not (math.isfinite(dt) and dt >= 0.0):
        raise CoreInvariantError("the step is non-negative")
    tau = profile.burden_rise_tau if stress > burden else profile.burden_clear_tau
    return stress + (burden - stress) * math.exp(-dt / tau)


def observable_impairment(primary: float, stress: float, burden: float) -> dict:
    """I = max(primary N, S, F), with the components that reach it. Never a sum; nothing is written back."""
    parts = {"primary": primary, "acute": stress, "memory": burden}
    level = max(parts.values())
    return {"impairment": level, "components": parts,
            "dominant": [k for k, v in parts.items() if v == level and level > 0.0]}


def burden_course(stresses, dt: float, profile: EncephalopathyProfile, initial: float = 0.0) -> list:
    """F before each step of a stress sequence and after the last one (len(stresses) + 1 values)."""
    out = [initial]
    for stress in stresses:
        out.append(burden_after(out[-1], stress, dt, profile))
    return out


def admissible_support(reading: dict, reference: dict) -> dict:
    """Threshold-free reading of a state: whether each signal can be positive under some admissible mapping (one that
    reads 0 at the reference state, as N1 requires), or is 0 under every one. A reading on the reference's side reads 0
    under every admissible ramp; one strictly past it reads positive under some."""
    out = {}
    for name, (key, side, _) in SIGNALS.items():
        if name == "cerebral_hypoperfusion" and not reading["pulse"]:
            out[name] = "MAXIMAL_ARREST"
            continue
        value, base = reading.get(key), reference.get(key)
        if value is None or base is None:
            out[name] = "UNAVAILABLE"
        else:
            past = value < base if side == LOW else value > base
            out[name] = "POSITIVE_UNDER_SOME_ADMISSIBLE_MAPPING" if past else "ZERO_UNDER_EVERY_ADMISSIBLE_MAPPING"
    return out
