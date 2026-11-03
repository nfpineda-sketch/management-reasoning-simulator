"""Phase 2 shadow core, P2M-2: the minimal common collapse safety layer (candidate).

Shadow only, a candidate off unless called: nothing in the core's step, derive or arrival state reads this module, and
no core step writes through it, so every default run, the golden and the closed records stay as they were. It is the
faculty's composition (2026-11-03), replacing the input of the P2E-3 output rule for this candidate only:

    perfusion_failure_signal        = mapping(MAP)                     MAP is the source; the mapping is UNSET
    oxygen_delivery_failure_signal  = the certified effective deficit  derived.acute_deficit_signal, not recalibrated
    collapse_signal                 = max(perfusion, delivery)         never a sum; nothing else enters
    collapse_burden (aux)           relaxes toward collapse_signal x tau, exactly, one minute at a time
    terminal transition             persistence (burden >= limit) AND current non-viability (signal >= floor)

Q, P and R reach it only through MAP and delivery; direct SpO2 is DEFERRED (oxygenation reaches oxygen content and so
delivery); lactate, D, pH, the consciousness impairment I and the systemic encephalopathy burden F are never read. A
pulseless rhythm is arrest, not collapse: the layer evaluates nothing without a pulse and the burden is reset there.
``RhythmState.pulse_present`` is the effective perfusing-rhythm state, never derived from pressure: a pulse with a MAP
near zero is a representable profound collapse; a pulse with no output stays the core's loud failure.

Every clinical number is a declared slot with no committed value: the MAP mapping (UNSET_CLINICAL_MAPPING), the burden
time constant, the terminal burden, the current non-viability floor (UNSET) and the terminal rhythm
(TERMINAL_RHYTHM_PHENOTYPE_UNSET). The numbers a probe or a test declares are SYNTHETIC_ONLY. ROSC is not modelled.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Sequence

from .derived import CoreProfile, acute_deficit_signal, derive, terminal_rhythm
from .integration import step
from .modules.rhythm_events import ScriptedRhythmEvent
from .state import Anchors, CoreInvariantError, CoreState, UnresolvedBoundary

REVISION = "P2M-2"
UNSET = "UNSET"
UNSET_CLINICAL_MAPPING = "UNSET_CLINICAL_MAPPING"
TERMINAL_RHYTHM_PHENOTYPE_UNSET = "TERMINAL_RHYTHM_PHENOTYPE_UNSET"
ROSC_NOT_CURRENTLY_MODELED = "ROSC_NOT_CURRENTLY_MODELED"
SYNTHETIC_ONLY = "SYNTHETIC_ONLY"
#: The minute statuses: no pulse (arrest, not collapse), a slot UNSET (nothing computed, the burden held), evaluated.
ARREST, NOT_EVALUATED, EVALUATED = "ARREST", "NOT_EVALUATED_UNSET", "EVALUATED"
TERMINAL_RHYTHMS = ("pea", "asystole")
#: The two graded inputs: the certified reading each maps and what it means.
INPUTS = {
    "perfusion_failure": ("map", "derive's MAP, the perfusion-pressure source; mapped through a monotone saturating ramp "
                                 "whose bounds are UNSET_CLINICAL_MAPPING (synthetic tests may inject the normalized "
                                 "value directly)"),
    "oxygen_delivery_failure": ("deficit_fraction", "derived.acute_deficit_signal: the certified effective oxygen-"
                                                    "delivery deficit over the current demand (0 when availability is "
                                                    "adequate or compensated by extraction, 1 at no delivery); read as "
                                                    "it is, not recalibrated, no onset threshold")}
#: What never enters as a graded input, and why.
EXCLUDED = {
    "Q": "NOT_A_GRADED_INPUT: flow reaches MAP (pressure = flow x tone) and delivery (delivery = flow x content)",
    "SpO2": "DEFERRED: oxygenation already reaches oxygen content and so delivery; revisit in generalization if a "
            "respiratory family shows that is insufficient",
    "P": "NOT_A_GRADED_INPUT: the pump reaches Q, hence MAP and delivery",
    "R": "NOT_A_GRADED_INPUT: a perfusing rhythm's output factor reaches Q; a non-perfusing rhythm is arrest; R stays "
         "authoritative for pulse_present",
    "acidemia_pH": "NOT_AN_INPUT: no path to P or R today; the acid burden integrates the deficit",
    "lactate": "NOT_AN_INPUT: a marker and a consequence", "D": "NOT_AN_INPUT: the oxygen debt is not collapse memory",
    "I": "NOT_AN_INPUT: consciousness is downstream", "F": "NOT_AN_INPUT: the encephalopathy memory is not collapse memory"}
STATUS = {
    "approved": "none FACULTY_APPROVED",
    "pulse": "RhythmState.pulse_present is the EFFECTIVE PERFUSING RHYTHM STATE, not a guaranteed palpable peripheral "
             "pulse; never derived from pressure. pulse=true with an extremely low MAP is a transient profound collapse",
    "zero_flow": "pulse=true with Q at the numerical zero stays an inconsistent state that fails loudly (derive's "
                 "UnresolvedBoundary, the RhythmState invariant): a coding invariant, never a clinical arrest rule",
    "map_mapping": UNSET_CLINICAL_MAPPING,
    "delivery_failure": "STRUCTURAL_IDENTITY_ON_THE_CERTIFIED_NORMALIZED_DEFICIT: no clinical onset threshold; whether "
                        "one is needed is UNSET",
    "ramp_shape": "STRUCTURAL_SHAPE_PROVISIONAL: linear between the two MAP bounds, saturating at 0 and 1",
    "aggregation": "MAXIMUM (faculty): no sum and no interaction term",
    "burden_kinetics": "UNSET (tau); the form is structural: exact first-order relaxation toward signal x tau, never "
                       "from tau_D, lactate or the encephalopathy memory",
    "terminal_burden": UNSET, "current_nonviability": UNSET, "terminal_rhythm": TERMINAL_RHYTHM_PHENOTYPE_UNSET,
    "rosc": ROSC_NOT_CURRENTLY_MODELED,
    "terminal_machinery": "STRUCTURAL_TEST_ONLY: the shadow transition is carried by the existing scripted-rhythm "
                          "primitive and derived.terminal_rhythm; its provenance reads scripted, so a runtime "
                          "integration needs the core's own collapse source (not done here)",
    "p2e3": "the P2E-3 output rule and this candidate are never active together (shadow_step refuses it)"}


@dataclass(frozen=True)
class PerfusionMapping:
    """MAP to perfusion failure: 0 at or above ``viable_map_mmhg``, 1 at or below ``failed_map_mmhg``, linear between."""

    viable_map_mmhg: float
    failed_map_mmhg: float

    def __post_init__(self):
        if not all(math.isfinite(v) for v in (self.viable_map_mmhg, self.failed_map_mmhg)):
            raise CoreInvariantError("the MAP bounds are finite")
        if not 0.0 <= self.failed_map_mmhg < self.viable_map_mmhg:
            raise CoreInvariantError("the failed MAP bound lies below the viable one, at or above 0")


def one_minute_ceiling(tau: float) -> float:
    """The most one minute adds to a burden of 0: maximal signal (1) for one minute, tau (1 - exp(-1 / tau)) < 1."""
    return tau * -math.expm1(-1.0 / tau)


@dataclass(frozen=True)
class CollapseProfile:
    """The candidate's declared numbers. Committed default: nothing declared (every slot UNSET)."""

    perfusion_mapping: PerfusionMapping | None = None
    burden_tau_min: float | None = None
    terminal_burden: float | None = None
    current_nonviability: float | None = None
    terminal_rhythm: str | None = None

    def __post_init__(self):
        tau = self.burden_tau_min
        if tau is not None and not (math.isfinite(tau) and tau > 0.0):
            raise CoreInvariantError("the burden time constant is finite and positive when declared")
        if (self.terminal_burden is None) != (self.current_nonviability is None):
            raise CoreInvariantError("the terminal criterion declares its persistence limit and its current "
                                     "non-viability floor together, or neither: historical burden alone never arrests")
        if self.terminal_burden is not None:
            if tau is None:
                raise CoreInvariantError("a terminal criterion needs declared burden kinetics")
            if not (math.isfinite(self.current_nonviability) and 0.0 < self.current_nonviability <= 1.0):
                raise CoreInvariantError("the current non-viability floor lies in (0, 1]: a zero signal never arrests")
            if not (math.isfinite(self.terminal_burden) and one_minute_ceiling(tau) < self.terminal_burden):
                raise CoreInvariantError("persistence floor: the terminal burden lies above one minute's maximal "
                                         "accrual, so no single minute arrests")
            if not self.terminal_burden < tau:
                raise CoreInvariantError("the terminal burden lies below tau, the burden's ceiling at maximal signal, "
                                         "so the criterion is reachable")
        if self.terminal_rhythm is not None and self.terminal_rhythm not in TERMINAL_RHYTHMS:
            raise CoreInvariantError(f"the terminal rhythm is one of {TERMINAL_RHYTHMS} when declared")

    @property
    def kinetics_declared(self) -> bool:
        return self.burden_tau_min is not None

    @property
    def terminal_declared(self) -> bool:
        return self.terminal_burden is not None


DEFAULT_COLLAPSE = CollapseProfile()


def _on_scale(value: float, what: str) -> float:
    if not (isinstance(value, (int, float)) and math.isfinite(value) and 0.0 <= value <= 1.0):
        raise CoreInvariantError(f"{what} lies on the failure scale [0, 1]")
    return float(value)


def perfusion_failure(map_mmhg: float, profile: CollapseProfile) -> float | None:
    """The perfusion-failure signal of a MAP: None while the mapping is UNSET (never assumed normal)."""
    mapping = profile.perfusion_mapping
    if mapping is None:
        return None
    if not math.isfinite(map_mmhg):
        raise CoreInvariantError("MAP is finite")
    span = mapping.viable_map_mmhg - mapping.failed_map_mmhg
    return min(1.0, max(0.0, (mapping.viable_map_mmhg - map_mmhg) / span))


def delivery_failure(deficit_fraction: float) -> float:
    """The oxygen-delivery failure signal: the certified normalized effective deficit, read as it is."""
    return _on_scale(deficit_fraction, "the effective deficit fraction")


def signal_value(perfusion: float, delivery: float) -> float:
    """collapse_signal = max(perfusion failure, delivery failure). Never a sum: a low output that lowers both is one
    insult read twice, not two."""
    return max(_on_scale(perfusion, "the perfusion failure"), _on_scale(delivery, "the delivery failure"))


@dataclass(frozen=True)
class CollapseSignal:
    """The two graded inputs at one state and their maximum. With the MAP mapping UNSET the value is a lower bound and
    ``complete`` is False: nothing accrues or decides on a lower bound."""

    perfusion: float | None
    delivery: float

    @property
    def complete(self) -> bool:
        return self.perfusion is not None

    @property
    def value(self) -> float:
        if self.perfusion is None:
            return _on_scale(self.delivery, "the delivery failure")
        return signal_value(self.perfusion, self.delivery)

    @property
    def dominant(self) -> tuple:
        parts = {"perfusion_failure": self.perfusion, "oxygen_delivery_failure": self.delivery}
        level = self.value
        return tuple(k for k, v in parts.items() if v is not None and level > 0.0 and v == level)


def readings(state: CoreState, anchors: Anchors, core_profile: CoreProfile) -> dict:
    """What the layer reads at one state, through the certified core, never writing it: the pulse, MAP and the effective
    deficit. Without a pulse nothing is read (arrest). A pulse with no output raises, as the core does."""
    derived = derive(state, anchors, core_profile)
    if not derived.pulse_present:
        return {"pulse": False, "map": None, "deficit_fraction": None}
    return {"pulse": True, "map": derived.map,
            "deficit_fraction": acute_deficit_signal(state, anchors, core_profile)}


def signal_at(reading: dict, profile: CollapseProfile) -> CollapseSignal:
    if not reading["pulse"]:
        raise CoreInvariantError("without a pulse there is no collapse signal: the state is arrest")
    return CollapseSignal(perfusion_failure(reading["map"], profile), delivery_failure(reading["deficit_fraction"]))


def burden_after(burden: float, signal: float, profile: CollapseProfile) -> float:
    """One minute of the collapse burden with the signal held over it: the exact first-order relaxation toward
    signal x tau, burden e^(-1/tau) + signal tau (1 - e^(-1/tau)). It never goes negative, rises while the burden is
    below signal x tau, falls once it is above (repayment as the signal improves), falls monotonically to 0 at zero
    signal and never exceeds max(burden, tau): intermittent insults cannot accumulate it without bound."""
    if not profile.kinetics_declared:
        raise CoreInvariantError("the collapse burden has no declared time constant (UNSET)")
    if not (math.isfinite(burden) and burden >= 0.0):
        raise CoreInvariantError("the collapse burden is finite and never negative")
    tau = profile.burden_tau_min
    kept = math.exp(-1.0 / tau)
    return burden * kept + _on_scale(signal, "the collapse signal") * tau * -math.expm1(-1.0 / tau)


def terminal_due(burden: float, signal: CollapseSignal, profile: CollapseProfile) -> bool:
    """The terminal criterion: persistence (the burden after the minute at or above the limit) AND current
    non-viability (this minute's signal at or above the floor). Historical burden alone never satisfies it."""
    return bool(profile.terminal_declared and signal.complete and burden >= profile.terminal_burden
                and signal.value >= profile.current_nonviability)


@dataclass(frozen=True)
class CollapseMinute:
    """One minute of the layer, read on the minute's start state: the signal, the burden it leaves and the decision."""

    minute: int
    status: str
    perfusion: float | None
    delivery: float | None
    signal: float | None
    complete: bool
    dominant: tuple
    burden_before: float
    burden_after: float
    terminal_due: bool

    def to_dict(self) -> dict:
        return {name: getattr(self, name) for name in self.__dataclass_fields__}


def evaluate(state: CoreState, anchors: Anchors, core_profile: CoreProfile, profile: CollapseProfile) -> CollapseMinute:
    """state(t) -> derive(t) -> collapse_signal(t) -> burden(t+1) -> the terminal decision. Reads only state(t)."""
    before = state.aux.collapse_burden
    reading = readings(state, anchors, core_profile)
    if not reading["pulse"]:
        # Arrest, not collapse: nothing is evaluated and the burden is reset, so it can never retrigger.
        return CollapseMinute(state.minute, ARREST, None, None, None, False, (), before, 0.0, False)
    signal = signal_at(reading, profile)
    if not (signal.complete and profile.kinetics_declared):
        return CollapseMinute(state.minute, NOT_EVALUATED, signal.perfusion, signal.delivery, signal.value,
                              signal.complete, signal.dominant, before, before, False)
    after = burden_after(before, signal.value, profile)
    return CollapseMinute(state.minute, EVALUATED, signal.perfusion, signal.delivery, signal.value, True,
                          signal.dominant, before, after, terminal_due(after, signal, profile))


SHADOW_EVENT_ID = "p2m2_shadow_terminal"


@dataclass(frozen=True)
class ShadowMinute:
    collapse: CollapseMinute
    applied: str | None
    deferred: bool

    def to_dict(self) -> dict:
        return {"collapse": self.collapse.to_dict(), "applied": self.applied, "deferred": self.deferred}


def shadow_step(state: CoreState, contributors: Sequence, anchors: Anchors, core_profile: CoreProfile,
                profile: CollapseProfile):
    """One shadow minute, in the declared order (EXPLICIT_LAG_REQUIRED):

        state(t) -> derive(t) -> collapse_signal(t) -> burden(t+1) -> terminal decision (persistence + current
        non-viability) -> the terminal rhythm transition applied by the core's own minute -> state(t+1)

    The decision is taken before the core's minute and never reads state(t+1): no same-step pulse / flow / collapse
    loop. A rhythm a contributor moves this minute wins (the decision is taken again next minute on the new rhythm's
    current physiology); any loss of the pulse resets the burden. The core's P2E-3 rule must be off. Returns the core's
    state and record and this layer's minute; the burden is the only thing the layer writes (aux.collapse_burden).
    STRUCTURAL_TEST_ONLY: the transition rides the scripted-rhythm primitive."""
    if core_profile.collapse_output_threshold is not None or core_profile.collapse_burden_limit is not None:
        raise CoreInvariantError("the P2E-3 output rule and the P2M-2 candidate are never active together")
    minute = evaluate(state, anchors, core_profile, profile)
    contributors = tuple(contributors)
    new_state, record = step(state, contributors, anchors, core_profile)
    applied, deferred = None, False
    if minute.terminal_due:
        if record.transitions:
            deferred = True
        elif profile.terminal_rhythm is None:
            raise UnresolvedBoundary(f"minute {state.minute + 1}: the terminal criterion is met but the terminal rhythm "
                                     f"is {TERMINAL_RHYTHM_PHENOTYPE_UNSET}")
        else:
            target = terminal_rhythm(state, anchors, replace(core_profile, collapse_terminal_rhythm=profile.terminal_rhythm))
            event = ScriptedRhythmEvent(id=SHADOW_EVENT_ID, at_minute=state.minute + 1, target=target,
                                        preventability="not assessed", cause_class="physiological_collapse_shadow")
            new_state, record = step(state, contributors + (event,), anchors, core_profile)
            applied = target.code.value
    if new_state.aux.collapse_burden != state.aux.collapse_burden:
        raise CoreInvariantError("the core moved the collapse burden: its own rule is on")
    burden = minute.burden_after if new_state.R.pulse_present else 0.0
    new_state = new_state.evolve(aux=replace(new_state.aux, collapse_burden=burden))
    derive(new_state, anchors, core_profile)
    return new_state, record, ShadowMinute(minute, applied, deferred)


def burden_course(signals: Sequence[float], profile: CollapseProfile, initial: float = 0.0) -> list:
    """The burden before each minute of a signal sequence and after the last one (len(signals) + 1 values)."""
    out = [initial]
    for value in signals:
        out.append(burden_after(out[-1], value, profile))
    return out


def first_terminal(signals: Sequence[float], profile: CollapseProfile, initial: float = 0.0) -> int | None:
    """The first minute (1-based) whose signal and resulting burden meet the terminal criterion, or None."""
    burden = initial
    for index, value in enumerate(signals, 1):
        burden = burden_after(burden, value, profile)
        if terminal_due(burden, CollapseSignal(value, 0.0), profile):
            return index
    return None
