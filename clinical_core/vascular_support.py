"""PHASE2_AMENDMENT_3: the common exogenous vasoconstrictor support (shadow only, off by default).

Vascular tone already exists in the common core: the channel T (C2, a multiplier, arrival = 1), written ONLY by the core's
tone response, read by the pressure (pressure = output x tone) and by the afterload (tone above arrival lowers output, and
so delivery). The tone the state calls for was the product of two independent factors: the compensation C(s), which answers
the acute oxygen deficit (P2J-2), and the distributive factor B(b), which a disease process lowers through the common
vasodilatory burden (P2W-1). How a DRUG that constricts would reach T was left undecided on purpose (P2X-1, FACULTY
DECISIONS 2 and 5: "a vasopressor treatment acts through a mechanism of its own, not through negative disease burden").

This stage is that mechanism, and nothing else:

    tone target = C(s) x B(b) x K(u),        K(u) = 1 + k u / (1 + u)

- u is ``aux.vasoconstrictor_support``: a GENERAL common state, at or above 0 (0 none), dimensionless, in half-maximal
  units of its own tone effect (u = 1 is half of the largest effect). It is not norepinephrine: any writer that constricts
  (another vasopressor, an endogenous vasoconstrictive state) adds to the same state through the same change
  (``provenance.VasoconstrictionChange``), and a vasodilator keeps its own input, the burden. None means NOT TRACKED.
- k is ``CoreProfile.vasoconstrictor_support_to_tone_gain``: the largest fractional rise of the tone target the support
  can cause. UNSET (None) by default, and then nothing here runs: every committed trajectory is unchanged bit for bit.
- K is 1 exactly with no support (arrival stays the scale), increases with the support and never reaches 1 + k: bounded
  by construction, with no clamp. The tone domain (``integration.tone_domain``) refuses, before execution, a gain whose
  largest reachable target would reach T's guard.

What follows from the physiology the core already has, and is NOT added here:

- pressure is output x tone, so a rise of tone supports pressure only in proportion to the flow there is: with a depleted
  preload or a depressed pump the same tone buys fewer mmHg, and without a pulse it buys none (``derive`` reports no
  pressure, output or delivery without a pulse, whatever T is);
- tone above arrival lowers output (the afterload, ``afterload_sensitivity``), so delivery does not improve with tone and
  more support is not more perfusion: the oxygen debt accrues faster, not slower;
- T moves one minute behind the state that calls for it (the core's explicit delayed feedback), and the writer brings its
  own onset and offset, so the response has a timing and is never a step in the minute of the order;
- the support never touches V, Hb or P: it adds no volume and creates no pump output.

``Norepinephrine`` is the FIRST writer, and the smallest one: a continuous infusion at a fixed rate from a start minute,
optionally stopped, with a first-order onset and offset of its own. No titration, no weight-based dose, no second drug. Its
magnitudes are not approved values: they are a DEVELOPMENT BEHAVIOURAL REGION with three witnesses, none chosen, and a run
that needs one must declare it. There is no clinical dose-response here and no mmHg target.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping

from .integration import NOTHING, Contribution, Contributor, register
from .interventions.timing import check_window
from .provenance import SourceKind, VasoconstrictionChange
from .state import CoreInvariantError

REVISION = "PHASE2_AMENDMENT_3"
DECIDED = "2026-11-17"
STATUS = "DEVELOPMENT_BEHAVIOURAL_REGION"
NOT_CLAIMED = ("a clinical dose-response", "an mmHg target", "a calibration", "runtime authority", "resident visibility",
               "clinical validation")


#: The resolution at which a writer holds its own contribution: a power of two. Every contribution is a multiple of it, so
#: each per-minute change (a difference of two of them) and the state (their sum) are EXACT in binary64 below the limit:
#: the state is exactly what its writers hold, it returns to exactly 0 when they do, and no rounding accumulates from one
#: minute to the next. Without it a stopped infusion left a residue of either sign, and a negative one, however small,
#: made the core refuse the run tens of minutes after the stop. It is a numerical resolution (about 1e-12 of the
#: half-maximal effect), not a clinical threshold.
SUPPORT_QUANTUM = 2.0 ** -40
#: The steady support one writer may declare, in half-effect units: a rate of 1024 times the half-maximal one is past any
#: order, and below it the sums of up to eight such writers stay exact on the grid.
SUPPORT_LIMIT = 2.0 ** 10


def on_the_grid(value: float) -> float:
    """``value`` at the resolution writers hold their contribution at (nearest multiple, halves up). Exact below the
    limit: the scaling is by a power of two."""
    return math.floor(value / SUPPORT_QUANTUM + 0.5) * SUPPORT_QUANTUM


def saturation(support: float | None) -> float:
    """The share of the largest tone effect a support reaches: u / (1 + u), 0 with none, below 1 at any support."""
    value = 0.0 if support is None else float(support)
    if not math.isfinite(value) or value < 0.0:
        raise CoreInvariantError("the vasoconstrictor support is a finite number at or above 0")
    return value / (1.0 + value)


def tone_factor(support: float | None, gain: float) -> float:
    """K(u) = 1 + k u / (1 + u): the factor the common vasoconstrictor support puts on the tone target.

    1 exactly with no support (None is not tracked and reads as none), increasing in the support, and strictly below 1 + k:
    bounded by its own form, never by a clamp. It reads the support and the declared gain only."""
    if isinstance(gain, bool) or not isinstance(gain, (int, float)) or not math.isfinite(gain) or gain <= 0.0:
        raise CoreInvariantError("the vasoconstrictor reader's gain is a finite positive number")
    return 1.0 + gain * saturation(support)


# -- the development behavioural region (never a calibration) ------------------------------------------------------------

#: What each magnitude is, the broad bounds it may take in a development experiment, and why. ``confidence`` is the
#: confidence that the TRUE clinical value lies inside the bounds, not a confidence in any point of them: all are below
#: 0.80, so no narrow region is adopted and no point is chosen (FD-TONE-06).
REGION: Mapping[str, Mapping[str, object]] = {
    "tone_gain": {
        "bounds": (0.3, 0.9), "unit": "fraction of the arrival tone",
        "what": "k, the largest fractional rise of the tone target (K below 1 + k)",
        "evidence": "a vasopressor raises arterial pressure in a dose-dependent, saturating way; no source in this "
                    "repository gives a magnitude, and the faculty supplied no mmHg target. The upper bound is the "
                    "core's own, not a clinical one: where the committed compensation can reach 1.5 times the "
                    "arrival tone, a gain of 1.0 puts the largest reachable target on T's guard (3.0), which the "
                    "tone domain refuses before execution; 0.9 is inside it in every committed family profile",
        "assumption": "the effect on tone saturates (an Emax form) and composes multiplicatively with the tone the "
                      "state already has",
        "uncertainty": "wide: the true ceiling depends on the patient, the vascular bed and the receptor state",
        "confidence": 0.5,
        "falsifier": "a faculty reviewer finds the pressure response at a saturating support implausibly small or "
                     "large for a patient with preserved flow",
    },
    "half_effect_rate_mcg_min": {
        "bounds": (5.0, 20.0), "unit": "mcg/min",
        "what": "the norepinephrine infusion rate whose steady support is 1 (half of the largest tone effect)",
        "evidence": "the authored order is a fixed rate in mcg/min (FR-F: 10 mcg/min); clinical infusions span roughly "
                    "one order of magnitude around it",
        "assumption": "the steady support is proportional to the rate (the saturation lives in the common factor)",
        "uncertainty": "wide: potency varies with weight, acidosis and receptor desensitisation, none of which is modelled",
        "confidence": 0.5,
        "falsifier": "a faculty reviewer finds that 10 mcg/min produces almost no effect or an almost maximal one",
    },
    "onset_tau_min": {
        "bounds": (0.5, 3.0), "unit": "min",
        "what": "the first-order time constant with which a started infusion approaches its steady support",
        "evidence": "the drug acts within one to two minutes and is at steady effect within several",
        "assumption": "one first-order process stands for mixing, distribution and receptor response",
        "uncertainty": "moderate: the timing CLASS (minutes, not seconds and not tens of minutes) is firmer than any value",
        "confidence": 0.7,
        "falsifier": "a faculty reviewer finds the pressure at the first reassessment arrives too early or too late",
    },
    "offset_tau_min": {
        "bounds": (1.0, 5.0), "unit": "min",
        "what": "the first-order time constant with which the support of a stopped infusion decays",
        "evidence": "a plasma half-life of a few minutes",
        "assumption": "the offset is first order and independent of how long the infusion ran",
        "uncertainty": "moderate; not exercised by the first authored order, which is never stopped",
        "confidence": 0.6,
        "falsifier": "a stopped infusion that keeps supporting pressure for tens of minutes, or loses it within one",
    },
}
WITNESS_NAMES = ("LOW", "CENTER_REFERENCE", "HIGH")
#: Test witnesses of the region: LOW is the weakest and slowest response the bounds allow, HIGH the strongest and fastest,
#: CENTER_REFERENCE a point between them. NONE is chosen, approved or calibrated.
WITNESSES: Mapping[str, Mapping[str, float]] = {
    "LOW": {"tone_gain": 0.3, "half_effect_rate_mcg_min": 20.0, "onset_tau_min": 3.0, "offset_tau_min": 1.0},
    "CENTER_REFERENCE": {"tone_gain": 0.6, "half_effect_rate_mcg_min": 10.0, "onset_tau_min": 1.5, "offset_tau_min": 2.5},
    "HIGH": {"tone_gain": 0.9, "half_effect_rate_mcg_min": 5.0, "onset_tau_min": 0.5, "offset_tau_min": 5.0},
}


def region_problems(point: Mapping[str, float]) -> list:
    """Why ``point`` is not a point of the development region, by name. Empty means it is one."""
    problems = []
    if set(point) != set(REGION):
        return [f"a point names exactly {sorted(REGION)}, not {sorted(point)}"]
    for name, spec in REGION.items():
        value, (low, high) = point[name], spec["bounds"]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) \
                or not low <= value <= high:
            problems.append(f"{name} = {value!r} is outside the development region [{low}, {high}]")
    return problems


def witness(name: str = "CENTER_REFERENCE") -> dict:
    """One of the three test witnesses, as plain data. A witness is a probe of the region, not a calibration."""
    if name not in WITNESSES:
        raise CoreInvariantError(f"the development witnesses are {list(WITNESS_NAMES)}, not {name!r}")
    point = dict(WITNESSES[name])
    if region_problems(point):
        raise CoreInvariantError(f"the witness {name} is not inside the development region")
    return point


# -- the first writer ------------------------------------------------------------------------------------------------------

def _positive(value, what: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0.0:
        raise CoreInvariantError(f"{what} is a finite positive number, declared by the run (no value is approved)")
    return float(value)


@register
@dataclass(frozen=True)
class Norepinephrine(Contributor):
    """A continuous norepinephrine infusion at a fixed rate: the first writer of the common vasoconstrictor support.

    It writes ONE thing, a ``VasoconstrictionChange`` per minute: the change of its own contribution to the support, which
    approaches rate / half_effect_rate with its onset time constant while it runs and decays with its offset time constant
    once stopped. The contribution is a closed form of the order and of time only: it reads no pressure, tone, output,
    delivery, volume, pump or any other state (the writer contract), so nothing here can close a loop or titrate. An order
    given at minute s first acts over (s, s + 1], like every intervention. It writes no channel: no T (the core's response
    is T's only writer), no V or Hb (no volume) and no P (no pump output).

    The three magnitudes are UNSET by default: a run declares them from the development region (``witness``), and a
    contributor without them is refused. With the reader UNSET in the profile the core refuses its first change.
    """

    kind = SourceKind.INTERVENTION
    type_name = "norepinephrine"

    id: str
    start_minute: int
    rate_mcg_min: float
    half_effect_rate_mcg_min: float | None = None
    onset_tau_min: float | None = None
    offset_tau_min: float | None = None
    stop_minute: int | None = None

    def __post_init__(self):
        check_window(self.start_minute, self.stop_minute, whole_start=True)
        if self.stop_minute is not None and self.stop_minute <= self.start_minute:
            raise CoreInvariantError("a norepinephrine infusion stops after it starts")
        _positive(self.rate_mcg_min, "the norepinephrine rate (mcg/min)")
        _positive(self.half_effect_rate_mcg_min, "the norepinephrine half-effect rate (mcg/min)")
        _positive(self.onset_tau_min, "the norepinephrine onset time constant (min)")
        _positive(self.offset_tau_min, "the norepinephrine offset time constant (min)")
        if not self.steady_support() < SUPPORT_LIMIT:
            raise CoreInvariantError(f"a norepinephrine rate of {SUPPORT_LIMIT:g} times its half-effect rate or more is not an "
                                     "order this writer represents")

    def steady_support(self) -> float:
        """What the infusion contributes to the common support once at steady effect: rate over half-effect rate."""
        return self.rate_mcg_min / self.half_effect_rate_mcg_min

    def support_at(self, minute: float) -> float:
        """Its own contribution to the common support at the end of ``minute``: 0 until it starts, a first-order approach
        to the steady support while it runs, a first-order decay from the value it had when it was stopped. Held on the
        writers' grid (``on_the_grid``), so the changes it emits sum back to it exactly, and to exactly 0 once it has
        decayed below the resolution."""
        if minute <= self.start_minute:
            return 0.0
        running_until = minute if self.stop_minute is None else min(minute, self.stop_minute)
        reached = self.steady_support() * -math.expm1(-(running_until - self.start_minute) / self.onset_tau_min)
        if self.stop_minute is None or minute <= self.stop_minute:
            return on_the_grid(reached)
        return on_the_grid(reached * math.exp(-(minute - self.stop_minute) / self.offset_tau_min))

    def contribute(self, state, minute, signals, anchors, profile) -> Contribution:
        amount = self.support_at(minute) - self.support_at(minute - 1)
        if amount == 0.0:
            return NOTHING
        running = self.stop_minute is None or minute <= self.stop_minute
        return Contribution(vasoconstriction=(VasoconstrictionChange(
            amount, self.source, minute,
            f"norepinephrine {self.rate_mcg_min:g} mcg/min approaching its steady support" if running
            else "norepinephrine stopped: its support decaying"),))
