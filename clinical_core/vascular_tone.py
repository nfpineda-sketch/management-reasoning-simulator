"""Phase 2 shadow core, P2J-2: the dynamic vascular-tone response and the pressure decision surface.

    python -m clinical_core.vascular_tone --digest
    python -m clinical_core.vascular_tone --design
    python -m clinical_core.vascular_tone --run --out <directory outside the repository>

Shadow only and offline (faculty brief of 2026-10-30, recorded in FACULTY). P2J-1's pressure mapping is accepted
(STRUCTURE_APPROVED); its trajectories are not, because tone T was fixed at 1. This package:

1. Adds one common tone response to the core (``derived.tone_target``, ``integration._vascular_tone``), driven by the
   acute shock signal s = effective oxygen deficit / demand (``derived.acute_deficit_signal``, P2I-2AF): relative to
   the tone with no deficit, 1 + g s; on the T channel, which is relative to arrival, (1 + g s) / (1 + g s0), s0 the
   arrival signal. Explicit feedback, one minute behind the signal (TIMING); no pressure, D, lactate or HR is read;
   0 by default, so every earlier run is unchanged.
2. Audits it before any clinical trajectory: the loop T -> afterload -> output -> delivery -> s -> T (FEEDBACK, with
   its analytic slope bound g a), the arrival handling (ARRIVAL, and the literal 1 + g s channel rejected
   analytically for its minute-1 step), fixed-state probes 1-8 (``probes``), and the analytic prefilter of the frozen
   candidate surface (GAINS x AFTERLOAD, ANALYTIC_RULES), all frozen before any trajectory.
3. Evaluates the surface on the retained physiology (the P2I-2AJ / P2I-2AK lactate units at demand 1.0 and 1.1,
   reproduced exactly) by an exact reconstruction of the core from the cached blood trajectories (RECONSTRUCTION_RULE,
   validated against full core runs on a sample): decision trajectories P1-P4, the T = 1 reference, the
   pressure / delivery trade-off, FD-LAC compatibility of the retained units, the indirect HR diagnostic (P2I-2AK A-F
   read, never filtered), the consciousness-threshold crossings, identifiability, the faculty decision surface A-I and
   the readiness verdict.

Nothing is fitted, selected or approved, no pressure envelope is applied, pressure never feeds HR, and legacy
pressure is never read.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
from dataclasses import replace
from pathlib import Path

from . import blood_anchors, calibration, gi_reference
from . import blood_fluid_calibration as bf
from . import hr_envelope_filter as hf
from . import hr_observables as ho
from . import hr_primary as hp
from . import hr_structure as hs
from . import lactate_adequacy as la
from . import lactate_closure as lc
from . import lactate_rebuild as lr
from . import pressure_tone as pt
from .bands import ARRIVAL
from .derived import (DEFAULT_PROFILE, OUTPUT_EPSILON, acute_deficit_signal, arrival_state, arrival_tone_signal,
                      arterial_pressures, derive, effective_delivery, effective_oxygen_deficit, relative_delivery,
                      tone_target)
from .integration import CHANNEL_BOUNDS, VASCULAR_TONE, step
from .state import Anchors, Channel, CoreInvariantError, RhythmState, UnresolvedBoundary

DECIDED = "2026-10-30"
REVISION = "P2J-2"
ROOT = pt.ROOT
CASES = pt.CASES
C57, C72 = CASES
L1, L2, L3 = pt.L1, pt.L2, pt.L3
NO_HAEMOSTASIS = pt.NO_HAEMOSTASIS
SCENARIOS = pt.SCENARIOS            # P1 L1, P2 L2, P3 L3 without the endoscopic haemostasis, P4 L3
MINUTES = pt.MINUTES
TIMES = pt.TIMES
RESERVE = pt.RESERVE
LAMBDAS = pt.LAMBDAS
DEMANDS = pt.DEMANDS
UNITS = pt.UNITS
TUPLE_ONLY = pt.TUPLE_ONLY
OWN = ("clinical_core/vascular_tone.py",)
P2J1_RECORD = ROOT / "docs" / "revision" / "P2J1_pressure_tone.json"
P2J1_DIGEST = "92aa42cbf18d6f2e4e3a978babbd8a4b0f8dd8a1058a8d6bde4b2592ac3f4091"

FACULTY = {
    "decided": DECIDED,
    "structure": "P2J-1's mapping is STRUCTURE_APPROVED: p = Q x T, SBP = arrival SBP x max(0, p), DBP = arrival DBP x "
                 "max(0, p), MAP proportional to p; the p = 0.5 knee and the 45 / 25 mmHg gains stay retired. Not "
                 "approved: the numerical BP trajectories, T = 1 as clinical physiology, a tone gain, an afterload "
                 "parameter, any BP envelope",
    "tone": "a COMMON dynamic vascular-tone response; primary acute driver the normalized effective oxygen deficit "
            "(effective_oxygen_deficit / demand, or an exactly equivalent normalized deficit already in the core); "
            "deficit 0 -> acute contribution 0; a larger deficit never lowers the vasoconstrictor contribution; no "
            "GI-specific or case-specific coefficient, no legacy BP fitting",
    "semantics": "T_base = 1 and a non-negative acute vasoconstrictor increment, T_target = 1 + gain x signal within "
                 "the T domain; no case-specific offset; no dependence on lactate, HR or legacy pressure; a smooth "
                 "monotone saturation if one is needed, never a hard clamp as the primary mapping",
    "no_pressure_driver": "T is never driven by 1 - relative pressure or another pressure error in P2J-2 (circular "
                          "before the baroreflex set point and gain exist)",
    "no_memory": "no accumulated D as a tone driver: tone answers the current acute deficit",
    "timing": "test an instantaneous common response first (deterministic, no algebraic instability, smooth minute to "
              "minute); a response time constant is not authorized: if one is structurally required, stop",
    "loop": "the T -> afterload -> Q -> DO2 -> deficit -> T loop is audited; deterministic, no hidden iterative "
            "convergence, no oscillation, no evaluation-order dependence; a same-step algebraic closure without a "
            "guaranteed unique solution stops the package, and no iterative solver is added",
    "range": "a small gain range (about 4-6 values, 0 included as the synthetic reference) from T_base, the T domain "
             "[0.1, 3.0], the normalized deficit range of the certified physiology, broad vasoconstrictor plausibility "
             "and fixed-state probes; never from legacy BP, a desired BP or survivor counts; frozen before outcomes",
    "afterload": "a = 0.3 provisional with 0.1 / 0.3 / 0.5 exploratory; none approved; a sparse tone_gain x a design",
    "arrival": "the authored arrival BP stays exactly 88/54 (57m) and 98/62 (72f) at minute 0; the response begins "
               "from the anchored arrival state; arrival BP never infers the gain",
    "demand": "1.0 and 1.1 carried separately unless the signal is invariant to demand; never one chosen",
    "hr": "pressure -> HR stays DEFERRED; no HR latent selected; P2I-2AK A-F read as a diagnostic, never a filter",
    "lactate": "faculty lactate rules unchanged, never recalibrated; if every tone candidate violates the certified "
               "lactate physiology, stop",
    "scope": "shadow only; no runtime integration, GI or second-family migration, final tone or afterload approval, "
             "hard BP envelope, pressure -> HR reconnection, RR calibration, consciousness recalibration, collapse "
             "activation or legacy fitting",
}

# 1. The tone response, its timing and the loop (P2J-2-1, -2, -3) -----------------------------------------------------

TONE = {
    "signal": "s = effective_oxygen_deficit(demand, delivery, reserve) / demand, read on the state "
              "(derived.acute_deficit_signal, P2I-2AF; the same signal the sympathetic drive reads): 0 when oxygen "
              "availability is adequate or compensated, non-decreasing as the effective deficit grows, at most 1 "
              "(no delivery); it reads delivery and demand only",
    "absolute": "tone relative to the tone with no deficit: T_abs = 1 + g x s (g = deficit_to_tone_gain >= 0); "
                "T_abs = 1 exactly at no deficit, non-decreasing in s, linear: no saturation is needed because "
                "1 + g <= 3 (ANALYTIC_RULES) keeps it inside T's guard",
    "channel": "the T channel is relative to arrival (proposal §7.2, P2J-1's anchoring): T = T_abs / T_abs(arrival) "
               "= (1 + g s) / (1 + g s0), s0 = derived.arrival_tone_signal (the arrival delivery against the case's "
               "baseline demand). T = 1 at arrival exactly, so the authored arrival pressure stays the scale of the "
               "accepted mapping and the arrival state is the response's own fixed point; T > 1 while the deficit "
               "exceeds arrival's; T = 1 / (1 + g s0) once no deficit is left (T_abs = 1). s0 is read from the "
               "arrival state, never fitted: no case offset is chosen",
    "core": "derived.tone_target (the target), integration._vascular_tone (the delta, source core_coupling:"
            "vascular_tone); deficit_to_tone_gain 0 writes no delta, so every run before P2J-2 is unchanged",
}
TIMING = (
    "Option A, instantaneous: each minute T takes the target the state at the start of the minute calls for, "
    "T(m+1) = tone_target(state(m)) (the delta is the target minus T(m)). No time constant: the only lag is the "
    "integration step, which the debt D already uses (its deficit is read at the start of the minute). The minute "
    "after arrival keeps T = 1 exactly, because the arrival state is the target's fixed point: tone starts to move at "
    "minute 2, answering the minute-1 state.")
FEEDBACK = {
    "classification": "EXPLICIT_LAGGED_FEEDBACK",
    "loop": "T -> afterload 1 / (1 + a (T - 1)) -> output Q -> delivery -> s -> T, closed one minute behind",
    "map": "with the blood state, rhythm and FiO2 given (none reads T or anything derived from it), T(m+1) = "
           "F(T(m)) = (1 + g s(T(m))) / (1 + g s0); s rises when T rises (T lowers Q), so F is non-decreasing: the "
           "loop is positive feedback and can never alternate in sign",
    "bound": "in a deficit s = 1 - R, R = reserve x delivery / demand < 1, and dR/dT = -a R / (1 + a (T - 1)), so "
             "dF/dT = g a R / ((1 + g s0)(1 + a (T - 1))) < g a / (1 + g s0 (1 - a)) <= g a (T >= 1 / (1 + g s0)); "
             "outside a deficit dF/dT = 0. g a < 1 makes F a contraction: one fixed point for a steady state, "
             "approached monotonically, no oscillation; the amplification at the fixed point is 1 / (1 - dF/dT)",
    "determinism": "no solver, no iteration inside a minute, no clock or random input; contributors are read from the "
                   "same start-of-minute state in a fixed order (integration.step), and the tone delta reads only that "
                   "state, so the result never depends on evaluation order",
    "same_step": "not used: a same-minute reading would make T an algebraic fixed point T = F(T) of the minute's own "
                 "output (no solver is authorized); the explicit scheme converges to that fixed point while the "
                 "upstream is steady",
}
ARRIVAL_RULE = (
    "Minute 0 is the anchored arrival (T = 1, the authored SBP / DBP exactly); minute 1 keeps T = 1 (the target read "
    "on the arrival state is 1); from minute 2 on T answers the previous minute's state. The arrival BP is never used "
    "to infer the gain: it is exact by construction.")
LITERAL_ALTERNATIVE = (
    "The literal channel T = 1 + g s with T = 1 anchored at arrival (no arrival normalization) is rejected analytically "
    "(ANALYTIC_REJECTION, ARRIVAL_DISCONTINUITY): at any arrival with a deficit (s0 > 0) its first update jumps T from 1 "
    "to 1 + g s0 with no change in the patient, raising pressure by (1 + g s0) / (1 + a g s0) in one minute "
    "(``literal_alternative``); removing the step would need a response time constant, which is not authorized.")


def literal_alternative(signals: dict) -> dict:
    """The minute-1 step the un-normalized channel would make, per arrival signal s0, gain and afterload point."""
    out = {}
    for key, s0 in sorted(signals.items()):
        for gain in GAINS[1:]:
            for a in AFTERLOAD:
                factor = (1.0 + gain * s0) / (1.0 + a * gain * s0)
                out[f"{key} g{gain:g} a{a:g}"] = {"s0": s0, "T_minute_1": 1.0 + gain * s0, "map_factor": factor}
    return out


# 2. The frozen candidate surface and the analytic prefilter (P2J-2-4, -5, -9) ----------------------------------------

GAINS = (0.0, 0.25, 0.5, 1.0, 1.5, 2.0)
REFERENCE_GAIN = 0.0
AFTERLOAD = pt.AFTERLOAD                    # 0.1 / 0.3 / 0.5, calibration.REGISTRY (P2G, provisional)
PRIMARY_AFTERLOAD = DEFAULT_PROFILE.afterload_sensitivity
T_LOWER, T_UPPER = CHANNEL_BOUNDS[Channel.T][:2]
RANGE_RULE = (
    "Built before any trajectory, from: T_base = 1 and T's guard [0.1, 3.0]; the normalized acute signal of the "
    "certified physiology (P2J-1's sample at T = 1: s0 0 to 0.45 at arrival, s up to 0.74 untreated at 120, 0 once "
    "resuscitated), so 1 + g s spans 1 to 1 + 0.74 g; broad vasoconstrictor plausibility (in severe haemorrhagic "
    "shock systemic vascular resistance rises to about 1.5-2.5 times its unstressed value, so g up to 2 at s near 0.7 "
    "spans the range); and the fixed-state probes. 0 is the synthetic no-response reference (P2J-1's T = 1), kept "
    "diagnostic, not a primary candidate; 2 is the largest gain whose largest target 1 + g stays inside the guard. "
    "Neither a legacy BP, a desired BP nor a survivor count is read. Every gain is crossed with the three afterload "
    "points (the pairwise surface), then screened analytically.")
ANALYTIC_RULES = {
    "NEGATIVE_GAIN": "g < 0: a vasodilator response to a deficit (the faculty asks for a non-negative increment)",
    "T_ABOVE_GUARD": "1 + g > 3.0: the largest target (s = 1) would leave T's guard, so the guard would shape it",
    "T_BELOW_GUARD": "1 / (1 + g) < 0.1: the no-deficit channel value 1 / (1 + g s0) could fall below the guard",
    "NO_CONTRACTION": "g a >= 1: the loop's slope bound reaches 1, so a unique, oscillation-free fixed point is not "
                      "guaranteed (the core refuses such a profile)",
}
SIMULATION_RULES = {
    "GUARD_CONTACT": "T reaches its guard in a trajectory",
    "OSCILLATION": "T changes sign three minutes running (+ - + or - + -) where the T = 1 reference signal does not",
    "STOP": "a run stops (output reaches zero with a pulse) that the T = 1 reference does not",
    "NOT_DETERMINISTIC": "two runs of the same inputs differ",
}
DEMAND_RULE = (
    "The signal reads demand (s = deficit / demand, and s0 = 1 - ratio / demand at arrival), so tone, output, pressure, "
    "delivery, D and lactate now depend on the demand factor and on the lactate side's arrival delivery level: demand "
    "1.0 and 1.1 are carried separately, each with its own retained units, and never pooled or chosen.")


def analytic_screen() -> dict:
    """Every (gain, afterload) of the surface, before any simulation: admissible or ANALYTIC_REJECTION with reasons."""
    out = {}
    for gain in GAINS:
        for a in AFTERLOAD:
            reasons = [name for name, failed in (("NEGATIVE_GAIN", gain < 0.0), ("T_ABOVE_GUARD", 1.0 + gain > T_UPPER),
                                                 ("T_BELOW_GUARD", 1.0 / (1.0 + gain) < T_LOWER),
                                                 ("NO_CONTRACTION", gain * a >= 1.0)) if failed]
            out[_pair(gain, a)] = {"gain": gain, "a": a, "slope_bound": gain * a,
                                   "status": "ANALYTIC_REJECTION" if reasons else "ADMISSIBLE", "reasons": reasons}
    return out


def _pair(gain: float, a: float) -> str:
    return f"g{gain:g} a{a:g}"


def admissible() -> list[tuple]:
    return [(item["gain"], item["a"]) for item in analytic_screen().values() if item["status"] == "ADMISSIBLE"]


DESIGN = {
    "primary": "every admissible gain at the primary afterload point a = 0.3 (the profile's provisional value) on "
               "every retained key: (scenario, case, blood set, arrival delivery level, demand) of the P2I-2AJ / "
               "P2I-2AK lactate units at each demand",
    "afterload": "every admissible gain at a = 0.1 and 0.5 on the validation sample's keys only (pressure_tone."
                 "sample_units: first, middle and last unit per demand) and its FD-LAC units: the sparse "
                 "tone_gain x a design",
    "fd_lac": "FD-LAC and L3 adequacy re-read on every retained unit (L1, every P3 set, every crystalloid point) at "
              "a = 0.3 for every gain; on the sample units at a = 0.1 and 0.5",
    "hr": "full core runs (L1, L3 and the two unit counterfactuals) of the sample units at a = 0.3, every gain, under "
          "P2I-2AK's primary latent HR combinations: HR read and A-F evaluated as a diagnostic",
    "validation": "full core runs of the sample units, every scenario, both cases, every admissible pair: the "
                  "reconstruction must equal them",
    "not_built": "no blood x fluid x lactate x HR x tone x pressure product: blood sets come only from retained "
                 "units, lactate sides only as those units pair them, the afterload points only on the sample",
}
RECONSTRUCTION_RULE = (
    "No contributor reads a derived quantity (P2J-1's path proof) and nothing derived feeds the blood state, the "
    "rhythm or FiO2, so tone changes only what is downstream of output: the blood trajectory of each set is simulated "
    "once (T = 1) and cached (output, Hb, SpO2, pulse, bleed, interventions), and each (gain, a, delivery level, "
    "demand) is rebuilt minute by minute with the core's own functions in the core's order: output = cached output x "
    "1 / (1 + a (T - 1)) (bit-identical, the cached afterload is 1), p = output x T, delivery = relative_delivery, s, "
    "and T(m+1) = T(m) + (tone_target - T(m)) as the integrator sums it; D and lactate through the P2I-2AD machinery "
    "(lactate_closure) on the rebuilt delivery. Validated against full core runs (DESIGN['validation']): every "
    "compared value must be equal.")

# 3. Readings, trade-off, envelopes, consciousness (P2J-2-7 .. -16) ---------------------------------------------------

TRADEOFF_RULE = (
    "Per admissible (gain, a), predeclared: UNSTABLE_FEEDBACK when a SIMULATION_RULES rejection occurs on any key; "
    "else PRESSURE_SUPPORTED_AT_DELIVERY_COST when a retained unit that passes FD-LAC and L3 adequacy at T = 1 fails "
    "them with the tone response (a faculty-approved outcome lost to the delivery the tone takes); else "
    "PRESSURE_SUPPORTED_WITH_STABLE_DELIVERY. The continuous costs (output, delivery, deficit and D against the T = 1 "
    "reference) are reported for every pair, with no threshold: the faculty sets the acceptable cost (envelope I). "
    "At a = 0.1 and 0.5 the FD-LAC part reads the sample units only (SAMPLE_ONLY).")
CONSCIOUSNESS_LEVELS = tuple(DEFAULT_PROFILE.pressure_levels)     # SBP 80 -> level 1, 65 -> level 2; not recalibrated
ENVELOPES = {
    "A": {"question": "untreated 57m SBP / MAP at 120", "scenario": "P1", "case": C57, "minute": 120,
          "readings": ("sbp", "map"),
          "rationale": "ongoing haemorrhage with compensatory vasoconstriction: pressure supported against the T = 1 "
                       "reference, never normalized (direction 5)"},
    "B": {"question": "untreated 72f SBP / MAP at 120", "scenario": "P1", "case": C72, "minute": 120,
          "readings": ("sbp", "map"), "rationale": "as A, for the 72f course"},
    "C": {"question": "pressure response to crystalloid", "scenario": "P2", "window": "crystalloid",
          "readings": ("map_change", "sbp_change"),
          "rationale": "MAP at the minute the crystalloid volume reaches its total less MAP the minute before it "
                       "starts (net of the bleeding meanwhile); tone falls as delivery recovers, so the response is "
                       "smaller than at T = 1"},
    "D": {"question": "pressure response to the first PRBC unit", "scenario": "P4", "window": "unit 1",
          "readings": ("map_change", "sbp_change"),
          "rationale": "MAP at the minute the first unit completes less MAP the minute before it starts (net)"},
    "E": {"question": "pressure response to the second PRBC unit", "scenario": "P4", "window": "unit 2",
          "readings": ("map_change", "sbp_change"),
          "rationale": "MAP at the minute the second unit completes less MAP at the first unit's completion (net)"},
    "F": {"question": "pressure at 120 after successful definitive resuscitation", "scenario": "P4", "minute": 120,
          "readings": ("sbp", "dbp", "map"),
          "rationale": "deficit resolved, so the acute tone is withdrawn: what remains above arrival is output"},
    "G": {"question": "acceptable T during shock", "scenario": "P1", "minute": 120, "readings": ("T", "T_abs", "T_max"),
          "rationale": "the vasoconstriction an untreated haemorrhage reaches, on the arrival scale and on the "
                       "no-deficit scale"},
    "H": {"question": "acceptable T at 120 after adequacy", "scenario": "P4", "minute": 120, "readings": ("T", "T_abs"),
          "rationale": "the tone left once delivery is adequate: T_abs = 1 when no deficit remains"},
    "I": {"question": "acceptable output / DO2 penalty from vasoconstriction", "scenario": "P1", "minute": 120,
          "readings": ("output_cost", "delivery_cost", "deficit_change", "D_change"),
          "rationale": "output and delivery against the T = 1 reference on the same key (fractional change), the "
                       "effective deficit and D change: the price of the pressure gained"},
}
ENVELOPE_RULE = (
    "Each proposal shows the model distribution (LOW / median / HIGH over the retained keys, per gain at a = 0.3 and "
    "per demand), the T = 1 reference, the physiological rationale, its sensitivity to the gain (the medians across "
    "gains), to a (the sample at a = 0.1 / 0.3 / 0.5) and to demand (1.0 against 1.1), and the basis of any bound: "
    "PHYSIOLOGICAL for a direction the physiology fixes, EXPLORATORY for a number (none is proposed: no authored "
    "pressure exists beyond arrival, so a number would come from the model itself), EVIDENCE for an authored "
    "observation (none). No envelope is applied or approved.")

# 4. Identifiability, baroreflex, verdict ------------------------------------------------------------------------------

IDENTIFIABILITY_RULE = (
    "WELL_CONSTRAINED: fixed by an authored observation; PARTIALLY_CONSTRAINED: bounded by an approved rule or "
    "structure but not fixed; POORLY_IDENTIFIED: the observations move it only weakly or jointly; NON_IDENTIFIABLE: "
    "nothing observed reaches it. The case data hold one pressure per case (arrival, exact by construction) and no "
    "output, resistance or post-arrival pressure.")
BAROREFLEX_PLAN = {
    "status": "DEFERRED: pressure -> HR stays PRESSURE_TERM_DIAGNOSTIC_ONLY (0 in the primary HR profile); not "
              "reconnected in P2J-2",
    "signal": "the absolute MAP the pressure domain now derives with dynamic tone (mmHg, anchored on the authored "
              "arrival), against a faculty set point: max(0, MAP_set - MAP) / MAP_set, never the arrival-relative "
              "1 - p",
    "tone_interaction": "tone already answers the acute deficit and supports pressure; a baroreflex acting on HR must "
                        "not also act on T through the same deficit (one tone writer only: the core fails closed on a "
                        "second one), and its gain is explored jointly with the acute HR gain and the tone gain",
    "double_counting": "the acute signal drives both tone and the sympathetic drive; a pressure deficit falls with "
                       "output and rises less once tone supports it, so the baroreflex term reads MAP after tone; "
                       "their shared variance on the arrival surface is reported before any value",
    "requires": "faculty pressure envelopes (A, B, F) and a tone decision first; then a MAP set point and a "
                "baroreflex gain range authorized before any value; then the P2I-2AK A-F rules repeated",
}
READY = "DYNAMIC_TONE_DECISION_SURFACE_READY"
NOT_READY = "DYNAMIC_TONE_NOT_READY"
VERDICT_RULE = (
    "READY when: the tone semantics are coherent (probes 1, 2 and 6, T = 1 at minutes 0 and 1 on every key, the gain-0 "
    "reference equals P2J-1's pressure); the feedback is deterministic and stable (probe 5, no SIMULATION_RULES "
    "rejection on any admissible pair, repeat runs identical); no pathological pressure / output loop (no "
    "UNSTABLE_FEEDBACK); the current lactate constraints stay satisfiable (at each demand some admissible gain > 0 at "
    "a = 0.3 keeps at least one retained candidate through FD-LAC and L3 adequacy); the candidate distributions exist "
    "for P1-P4, both cases and demands, every admissible gain; the reconstruction equals the core on the sample; "
    "the retained units are P2I-2AK's and, at gain 0, every one of their candidates keeps FD-LAC and L3 adequacy (the "
    "lactate reference reproduced); pressure -> HR stays 0 in the primary profile; and nothing is approved. Otherwise NOT_READY with the first "
    "failing check as the blocker.")
POLICY = ("Shadow only. P2J-1's committed record and the P2I-2AJ / P2I-2AK machinery; legacy pressure never read (no "
          "shadow, legacy adapter or family-engine import), the P2F region never consumed (P2FGuard), no hard pressure "
          "envelope, nothing approved or selected, pressure -> HR not reconnected, lactate never recalibrated.")

# 5. What P2J-2 changed outside its own module (the AST proof for the closed packages' guards) ------------------------

DERIVED, INTEGRATION, SHADOW = "clinical_core/derived.py", "clinical_core/integration.py", pt.SHADOW
#: Per file: its hash at P2I-2AK (052d816) and at P2J-1 (f6b4cd0); the top-level statements P2J-2 changed (a
#: definition by its name, an assignment by its target, an import by "from <module>", "__doc__" the module
#: docstring); the same for P2J-1 and P2J-2 together; and the AST dump digest of every other statement, at P2J-1 and at
#: P2I-2AK, which the live file must keep.
P2J2_CHANGES = {
    DERIVED: {"sha_at_p2i2ak": pt.P2J1_CHANGES[pt.DERIVED]["sha_at_p2i2ak"],
              "sha_at_p2j1": "ef3fe5ca5e63d4cbe298bad4ddfdf2b206e646533a06fcb5db479af72b65a75c",
              "changed": ("CoreProfile", "PARAMETERS", "arrival_tone_signal", "tone_target"),
              "since_p2i2ak": ("CoreProfile", "PARAMETERS", "arrival_tone_signal", "tone_target", "arterial_pressures"),
              "outside_p2j1": "f64141498dfc79d4e82aad1cd9eab538db29b989c74f3db4d6bc5c3ede65f810",
              "outside_p2i2ak": "95898afcf5c51f2ec2c697c71362fae73dc8990f7dea40ea7b08ded194c9969c"},
    INTEGRATION: {"sha_at_p2i2ak": "dc45406cf437593c61cceddee5f2df0a2d0c872e4979ad694c8d2e0e3567db1c",
                  "sha_at_p2j1": "dc45406cf437593c61cceddee5f2df0a2d0c872e4979ad694c8d2e0e3567db1c",
                  "changed": ("__doc__", "from .derived", "VASCULAR_TONE", "_vascular_tone", "step"),
                  "since_p2i2ak": ("__doc__", "from .derived", "VASCULAR_TONE", "_vascular_tone", "step"),
                  "outside_p2j1": "33e1da242de50d56bfbcaeb36e5ca37ce31611918a731e5185299b533fc2e92c",
                  "outside_p2i2ak": "33e1da242de50d56bfbcaeb36e5ca37ce31611918a731e5185299b533fc2e92c"},
}


#: The two tuple-only files: P2J-2 added its modules to the downstream-report and pack-excluded tuples, nothing else.
TUPLE_CHANGES = {
    "clinical_core/lactate_slice.py": {"sha_at_p2j1": "0b9e77a06fc9ccb1442752463b2725142d3e6be5e221521861b9fc8fa531121a",
                                       "changed": ("DOWNSTREAM_REPORTS",),
                                       "outside_p2j1": "419bc6d5ac84ed415f1d9f1e4a118dbae16a6919dc67a3c72b42c02f55c7889a"},
    "clinical_core/decision_pack.py": {"sha_at_p2j1": "773804b681197f08b33c5e134242fa2d4e9911cce94008c875a0e501af912a5d",
                                       "changed": ("PACK_DIGEST_EXCLUDED",),
                                       "outside_p2j1": "777e51ad111e3a29c75e2fa71bfc057c3096625e3b77c72956fd9de013013353"},
}


def outside_digest(text: str, changed) -> str:
    """The AST dump digest of every top-level statement of ``text`` but the ``changed`` ones."""
    tree = ast.parse(text)
    body = list(tree.body)

    def kept(index, node):
        if index == 0 and isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(
                node.value.value, str):
            return "__doc__" not in changed
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            return node.name not in changed
        if isinstance(node, ast.ImportFrom):
            return f"from {'.' * node.level}{node.module or ''}" not in changed
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            return not any(isinstance(n, ast.Name) and n.id in changed for t in targets for n in ast.walk(t))
        return True
    return hashlib.sha256("\n".join(ast.dump(n) for i, n in enumerate(body) if kept(i, n)).encode("utf-8")).hexdigest()


def _live(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def outside_unchanged() -> dict:
    return {relative: {"since_p2j1": outside_digest(_live(relative), item["changed"]) == item["outside_p2j1"],
                       "since_p2i2ak": outside_digest(_live(relative), item["since_p2i2ak"]) == item["outside_p2i2ak"]}
            for relative, item in P2J2_CHANGES.items()}


def p2j1_sources(sources: dict) -> dict:
    """A P2J-1 dependency map with each P2J-2-changed file at its P2J-1 hash, when P2J-2 changed only the declared
    statements there; a file changed elsewhere keeps its live hash, so that guard fails."""
    out = dict(sources)
    for relative, item in {**P2J2_CHANGES, **TUPLE_CHANGES}.items():
        if relative in out and outside_digest(_live(relative), item["changed"]) == item["outside_p2j1"]:
            out[relative] = item["sha_at_p2j1"]
    return out


def p2i2ak_sources(sources: dict) -> dict:
    """An earlier package's dependency map with every file P2J-1 or P2J-2 changed at its P2I-2AK hash, when only the
    declared statements changed (derived.py and integration.py here, shadow.py through P2J-1's own proof)."""
    out = dict(sources)
    for relative, item in P2J2_CHANGES.items():
        if relative in out and outside_digest(_live(relative), item["since_p2i2ak"]) == item["outside_p2i2ak"]:
            out[relative] = item["sha_at_p2i2ak"]
    shadow = pt.pressure_only_sources({SHADOW: out[SHADOW]}) if SHADOW in out else {}
    out.update(shadow)
    return out


def p2j1_record() -> dict:
    record = json.loads(P2J1_RECORD.read_text(encoding="utf-8"))
    if record["freeze_digest"] != P2J1_DIGEST or record["verdict"]["verdict"] != pt.READY:
        raise AssertionError("the P2J-1 record is not the committed one")
    return record


# 6. Anchors and fixed-state probes (P2J-2-6) -------------------------------------------------------------------------

def tone_profile(gain: float, a: float):
    """The retained physiology's profile fields the tone reads (reserve 2.5), at one surface point."""
    return replace(DEFAULT_PROFILE, oxygen_extraction_reserve=RESERVE, deficit_to_tone_gain=gain,
                   afterload_sensitivity=a)


def tone_anchors(case: str, level: str, factor: float) -> Anchors:
    """The anchors a full run of the case builds at one arrival delivery level and demand (pressure_tone.full_run's
    construction; the lactate side's excess and debt levels and the blood set never reach the tone)."""
    values = calibration.case_values(case, calibration.GICandidate({}, excess="midpoint", debt="midpoint",
                                                                   delivery=level, intrinsic="midpoint"))
    values["arrival_delivery_ratio"] /= RESERVE
    values["metabolic_demand_baseline"] *= factor
    return gi_reference.candidate_anchors(case, values)


LEVELS = ("lower", "midpoint", "upper")
NEUTRAL = Anchors(**ARRIVAL)
PROBE_PUMPS = (2.5, 2.0, 1.5, 1.2, 1.0, 0.8, 0.6, 0.4, 0.3, 0.2, 0.1)
PROBE_TONES = (0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 2.5, 3.0)
STEADY_MINUTES = 60
PROBE_RULE = (
    "Fixed states, before any trajectory: two arrivals, the neutral probe arrival (s0 = 0) and the 57m arrival at the "
    "lower delivery level and demand 1.0 (s0 = 0.4), at reserve 2.5. 1: deficit 0 gives T_abs = 1 exactly. 2: T's "
    "target never falls as s rises (pump lowered step by step at T = 1). 3: at a fixed preload, pump and rhythm, output "
    "falls as T rises, for every afterload point. 4: p = Q x T rises with T over the whole guard. 5: a steady upstream "
    "(pump lowered, nothing else acting, 60 minutes) gives T monotone, its step shrinking at no more than the slope "
    "bound, settling on the analytic fixed point (bisection here, never in the core). 6: when the deficit resolves "
    "(pump raised) T returns to T_abs = 1. 7: no pulse, no pressure, the target in the guard; output 0 with a pulse "
    "still stops the run; a tiny output at the largest tone gives a tiny pressure. 8: no pressure is negative, and "
    "minute 1 equals the arrival.")


def _probe_bases() -> dict:
    gi = tone_anchors(C57, "lower", 1.0)
    return {"neutral (s0 = 0)": NEUTRAL, "57m lower x1 (s0 = 0.4)": gi}


def _state(anchors: Anchors, profile, **changes):
    return arrival_state(anchors, profile).evolve(**changes)


def _fixed_point(anchors: Anchors, profile, pump: float) -> float:
    """T* = F(T*) for the steady state (bisection on F(T) - T; F is a contraction, so the root is unique)."""
    base = _state(anchors, profile, P=pump)

    def gap(t):
        return tone_target(base.evolve(T=t), anchors, profile) - t
    low, high = T_LOWER, T_UPPER
    for _ in range(200):
        middle = 0.5 * (low + high)
        if gap(middle) > 0.0:
            low = middle
        else:
            high = middle
    return 0.5 * (low + high)


def probes() -> dict:
    out = {"rule": PROBE_RULE, "bases": {}}
    pairs = admissible()
    ok = {str(n): True for n in range(1, 9)}
    for name, anchors in _probe_bases().items():
        base = {"s0": arrival_tone_signal(anchors, tone_profile(0.0, PRIMARY_AFTERLOAD)), "signal": {}, "afterload": {},
                "steady": {}, "resolution": {}, "zero_output": {}}
        # 1, 2: the signal and the target along a falling pump, T = 1.
        for gain in GAINS:
            profile = tone_profile(gain, PRIMARY_AFTERLOAD)
            rows = []
            for pump in PROBE_PUMPS:
                state = _state(anchors, profile, P=pump)
                signal = acute_deficit_signal(state, anchors, profile)
                target = tone_target(state, anchors, profile)
                rows.append({"P": pump, "s": signal, "T": target, "T_abs": target * (1.0 + gain * base["s0"])})
            base["signal"][f"g{gain:g}"] = rows
            ok["1"] = ok["1"] and all(abs(r["T_abs"] - 1.0) <= 1e-12 for r in rows if r["s"] == 0.0) and any(
                r["s"] == 0.0 for r in rows)
            ok["2"] = ok["2"] and all(b["s"] >= a["s"] and b["T"] >= a["T"] for a, b in zip(rows, rows[1:]))
        # 3, 4: output and pressure along tone at a fixed state.
        for a in AFTERLOAD:
            profile = tone_profile(0.0, a)
            rows = []
            for tone in PROBE_TONES:
                view = derive(_state(anchors, profile, T=tone), anchors, profile)
                rows.append({"T": tone, "output": view.output_rel, "p": view.pressure_rel, "map": view.map})
            base["afterload"][f"a{a:g}"] = rows
            ok["3"] = ok["3"] and all(b["output"] < a_["output"] for a_, b in zip(rows, rows[1:]))
            ok["4"] = ok["4"] and all(b["p"] > a_["p"] and b["map"] > a_["map"] for a_, b in zip(rows, rows[1:]))
        # 5, 6: a steady deficit, then its resolution, through the integrator.
        deficit_pump, resolved_pump = (0.3, 1.0) if base["s0"] == 0.0 else (0.6, 2.5)
        for gain, a in pairs:
            if gain == 0.0:
                continue
            profile = tone_profile(gain, a)
            state = _state(anchors, profile, P=deficit_pump)
            tones = [state.T]
            for _ in range(STEADY_MINUTES):
                state, _record = step(state, (), anchors, profile)
                tones.append(state.T)
            steps = [b - a_ for a_, b in zip(tones, tones[1:])]
            bound = gain * a / (1.0 + gain * base["s0"] * (1.0 - a))
            ratios = [abs(b) / abs(a_) for a_, b in zip(steps[1:], steps[2:]) if abs(a_) > 1e-12]
            fixed = _fixed_point(anchors, profile, deficit_pump)
            monotone = all(s >= -1e-15 for s in steps)
            item = {"T_1": tones[1], "T_end": tones[-1], "fixed_point": fixed, "largest_ratio": max(ratios, default=0.0),
                    "bound": bound, "monotone": monotone, "settled": abs(tones[-1] - fixed) <= 1e-6}
            base["steady"][_pair(gain, a)] = item
            ok["5"] = ok["5"] and monotone and item["settled"] and item["largest_ratio"] <= bound + 1e-9
            state = state.evolve(P=resolved_pump)
            after = []
            for _ in range(STEADY_MINUTES):
                state, _record = step(state, (), anchors, profile)
                after.append(state.T)
            signal = acute_deficit_signal(state, anchors, profile)
            t_abs = after[-1] * (1.0 + gain * base["s0"])
            base["resolution"][_pair(gain, a)] = {"signal_end": signal, "T_end": after[-1], "T_abs_end": t_abs,
                                                  "never_rises": all(b <= a_ + 1e-15 for a_, b in zip(after,
                                                                                                    after[1:]))}
            ok["6"] = ok["6"] and signal == 0.0 and abs(t_abs - 1.0) <= 1e-12
        # 7: zero output and arrest.
        for gain in GAINS[1:]:
            profile = tone_profile(gain, PRIMARY_AFTERLOAD)
            arrest = _state(anchors, profile, R=RhythmState.asystole(), terminal_since=0)
            view = derive(arrest, anchors, profile)
            target = tone_target(arrest, anchors, profile)
            after, _record = step(arrest, (), anchors, profile)
            try:
                derive(_state(anchors, profile, P=1e-12), anchors, profile)
                boundary = "NO_STOP"
            except UnresolvedBoundary:
                boundary = "UNRESOLVED_BOUNDARY"
            tiny = derive(_state(anchors, profile, P=0.1, T=T_UPPER), anchors, profile)
            item = {"pulseless_pressure": [view.sbp, view.dbp, view.map], "pulseless_target": target,
                    "pulseless_T_after_minute": after.T, "zero_output_with_pulse": boundary,
                    "low_output_at_T_3": {"output": tiny.output_rel, "map": tiny.map, "sbp": tiny.sbp}}
            base["zero_output"][f"g{gain:g}"] = item
            ok["7"] = ok["7"] and view.sbp is None and view.map is None and T_LOWER <= target <= T_UPPER and \
                boundary == "UNRESOLVED_BOUNDARY" and tiny.map >= 0.0 and abs(after.T - target) <= 1e-12
        # 8: no negative pressure on any probe, and a minute from the untouched arrival keeps T and MAP exactly.
        arrival_kept = {}
        for gain, a in pairs:
            profile = tone_profile(gain, a)
            start = arrival_state(anchors, profile)
            after, _record = step(start, (), anchors, profile)
            kept = after.T == 1.0 and derive(after, anchors, profile).map == derive(start, anchors, profile).map
            arrival_kept[_pair(gain, a)] = kept
            ok["8"] = ok["8"] and kept
        base["arrival_minute_1"] = arrival_kept
        ok["8"] = ok["8"] and all(r["map"] >= 0.0 for rows in base["afterload"].values() for r in rows)
        out["bases"][name] = base
    out["checks"] = ok
    return out


# 7. The reconstruction (RECONSTRUCTION_RULE) --------------------------------------------------------------------------

def _blood_task(task: tuple) -> tuple:
    """One blood set's T = 1 trajectory, cached: what tone does not change, plus the T = 1 output."""
    key, entry, case, scenario, bag = task
    values = lr.blood_values(entry, case, bag)
    anchors, profile, full = blood_anchors.setup(case, **values)
    states, stop = blood_anchors.trajectory(anchors, pt.scenario_items(case, scenario, full), MINUTES, profile)
    unit = full.get("red_cell_unit_volume_ml")
    shed = [state.blood.shed_ml for state in states]
    flow = [after - before for before, after in zip(shed, shed[1:])]
    views = [derive(state, anchors, profile) for state in states]
    demand = {state.aux.oxygen_demand for state in states}
    if demand != {anchors.metabolic_demand_baseline}:
        raise AssertionError("a GI blood run carries a demand modifier: the reconstruction does not cover it")
    return key, {"output1": [v.output_rel for v in views], "hb": [s.hb for s in states], "spo2": [v.spo2 for v in views],
                 "pulse": [v.pulse_present for v in views], "bleed": (flow[:1] or [0.0]) + flow,
                 "crystalloid": [s.blood.crystalloid_in_ml for s in states],
                 "prbc": [s.blood.transfused_ml / unit if unit else 0.0 for s in states],
                 "controlled_at": lr.controlled_at(states[-1]), "stop": stop,
                 "demand": [s.aux.oxygen_demand for s in states]}


def rebuild(blood: dict, anchors: Anchors, gain: float, a: float) -> dict:
    """The core's minutes for one cached blood trajectory at one surface point (RECONSTRUCTION_RULE)."""
    profile = tone_profile(gain, a)
    s0 = arrival_tone_signal(anchors, profile)
    demand = anchors.metabolic_demand_baseline
    tone, rows, clamps, stop = 1.0, [], 0, blood["stop"]
    for minute, output1 in enumerate(blood["output1"]):
        if blood["pulse"][minute]:
            afterload = 1.0 / (1.0 + a * (tone - 1.0))
            output = output1 * afterload
            if output <= OUTPUT_EPSILON:
                stop = minute
                break
            p = output * tone
            delivery = relative_delivery(output, blood["hb"][minute], blood["spo2"][minute], anchors)
            sbp, dbp = arterial_pressures(p, anchors, profile)
            mean = (sbp + 2 * dbp) / 3
        else:
            output = p = delivery = 0.0
            sbp = dbp = mean = None
        deficit = effective_oxygen_deficit(demand, effective_delivery(delivery, anchors), RESERVE)
        signal = deficit / demand
        rows.append({"minute": minute, "T": tone, "T_abs": tone * (1.0 + gain * s0), "s": signal, "output": output,
                     "delivery_rel": delivery, "deficit": deficit, "p": p, "sbp": sbp, "dbp": dbp, "map": mean})
        if gain > 0.0:
            target = (1.0 + gain * signal) / (1.0 + gain * s0)
            proposed = tone + math.fsum([target - tone])
            bounded = min(T_UPPER, max(T_LOWER, proposed))
            clamps += bounded != proposed
            tone = bounded
    return {"rows": rows, "s0": s0, "clamps": clamps, "stop": stop}


def haemodynamic(blood: dict, rebuilt: dict) -> dict:
    """The lactate machinery's input (lactate_adequacy._haemodynamic's fields) from a rebuilt trajectory."""
    n = len(rebuilt["rows"])
    return {"delivery_rel": [row["delivery_rel"] for row in rebuilt["rows"]], "demand": blood["demand"][:n],
            "controlled_at": blood["controlled_at"], "stop": rebuilt["stop"], "bleed": blood["bleed"][:n]}


def debt_and_lactate(blood: dict, rebuilt: dict, case: str, index: int, factor: float, arrivals: dict) -> dict:
    hd = haemodynamic(blood, rebuilt)
    for _, lactate, debt, context in lc._series(hd, arrivals[case], [index], factor, {}):
        return {"D": debt, "lactate": lactate, "adequacy": context.adequacy}
    raise AssertionError("no lactate series")


def level_of(index: int) -> str:
    return LAMBDAS[index][-1]


# 8. Keys, metrics and the per-key task ---------------------------------------------------------------------------------

def _units_minute(prbc: list, units: float):
    return next((minute for minute, value in enumerate(prbc) if value >= units - 1e-9), None)


def windows(blood: dict) -> dict:
    """The intervention windows envelopes C-E read (blood-state only, the same at every tone)."""
    crystalloid = blood["crystalloid"]
    out = {}
    if crystalloid[-1] > 0.0:
        start = next(m for m, v in enumerate(crystalloid) if v > 0.0) - 1
        end = next(m for m, v in enumerate(crystalloid) if v >= crystalloid[-1])
        out["crystalloid"] = (max(0, start), end)
    first, second = _units_minute(blood["prbc"], 1.0), _units_minute(blood["prbc"], 2.0)
    if first is not None:
        start = next(m for m, v in enumerate(blood["prbc"]) if v > 0.0) - 1
        out["unit 1"] = (max(0, start), first)
        if second is not None:
            out["unit 2"] = (first, second)
    return out


def _signs(values: list) -> list:
    steps = [b - a for a, b in zip(values, values[1:])]
    return [0 if abs(s) <= 1e-12 else (1 if s > 0 else -1) for s in steps]


def _alternations(signs: list) -> set:
    return {k for k in range(len(signs) - 2) if signs[k] and signs[k] == -signs[k + 1] == signs[k + 2]}


def metrics(rebuilt: dict, reference: dict) -> dict:
    rows, ref = rebuilt["rows"], reference["rows"]
    maps = [r["map"] for r in rows if r["map"] is not None]
    ref_maps = [r["map"] for r in ref if r["map"] is not None]
    tone_alt = _alternations(_signs([r["T"] for r in rows]))
    signal_alt = _alternations(_signs([r["s"] for r in ref]))

    def first(level):
        return next((r["minute"] for r in rows if r["sbp"] is not None and r["sbp"] < level), None)
    return {"T1_is_arrival": len(rows) < 2 or (rows[1]["T"] == 1.0 and rows[0]["T"] == 1.0
                                                 and rows[0]["map"] == ref[0]["map"] and rows[1]["map"] == ref[1]["map"]),
            "clamps": rebuilt["clamps"], "stop": rebuilt["stop"], "reference_stop": reference["stop"],
            "oscillation": sorted(tone_alt - signal_alt),
            "negative_pressure": any(r["sbp"] is not None and min(r["sbp"], r["dbp"]) < 0.0 for r in rows),
            "max_dT": max((abs(b["T"] - a["T"]) for a, b in zip(rows, rows[1:])), default=0.0),
            "max_dmap": max((abs(b - a) for a, b in zip(maps, maps[1:])), default=0.0),
            "reference_max_dmap": max((abs(b - a) for a, b in zip(ref_maps, ref_maps[1:])), default=0.0),
            "T_max": max(r["T"] for r in rows), "T_abs_max": max(r["T_abs"] for r in rows),
            "sbp_below": {str(level): first(level) for level, _ in CONSCIOUSNESS_LEVELS},
            "map_min": min(maps) if maps else None,
            "delivery_ratio_min": min((r["delivery_rel"] / q["delivery_rel"] for r, q in zip(rows, ref)
                                       if q["delivery_rel"] > 0.0), default=None)}


READ = ("T", "T_abs", "s", "output", "delivery_rel", "deficit", "map", "sbp", "dbp")
NOT_ASSESSED = "NOT_ASSESSED"   # L3 adequacy is read only where haemostasis happens (P4)


def _read(rows: list, minute: int) -> dict | None:
    return {name: rows[minute][name] for name in READ} if minute < len(rows) else None


def _key_task(task: tuple) -> tuple:
    """Every gain at one afterload point for one (scenario, case, blood set, delivery level, demand): readings at TIMES,
    the trajectory metrics, the envelope windows, and D / lactate for every lambda pairing the key."""
    key, blood, case, scenario, factor, level, lambdas, a, gains, arrivals = task
    anchors = tone_anchors(case, level, factor)
    reference = rebuild(blood, anchors, REFERENCE_GAIN, a)
    win = windows(blood)
    out = {"windows": win, "interventions": {str(m): {"bleed": blood["bleed"][m], "crystalloid": blood["crystalloid"][m],
                                                      "prbc": blood["prbc"][m],
                                                      "controlled": blood["controlled_at"] is not None
                                                      and blood["controlled_at"] <= m} for m in TIMES},
           "gains": {}}
    for gain in gains:
        rebuilt = reference if gain == REFERENCE_GAIN else rebuild(blood, anchors, gain, a)
        rows = rebuilt["rows"]
        item = {"s0": rebuilt["s0"], "at": {str(m): _read(rows, m) for m in TIMES},
                "metrics": metrics(rebuilt, reference),
                "windows": {name: {"map_change": rows[e]["map"] - rows[s]["map"],
                                   "sbp_change": rows[e]["sbp"] - rows[s]["sbp"], "start": s, "end": e}
                            for name, (s, e) in win.items() if e < len(rows)},
                "lambdas": {}}
        for index in lambdas:
            series = debt_and_lactate(blood, rebuilt, case, index, factor, arrivals)
            item["lambdas"][str(index)] = {"D": {str(m): series["D"][m] for m in TIMES if m < len(series["D"])},
                                           "lactate": {str(m): series["lactate"][m] for m in TIMES
                                                       if m < len(series["lactate"])},
                                           "adequacy": (series["adequacy"] or {}).get("status", NOT_ASSESSED)}
        out["gains"][f"{gain:g}"] = item
    return key, out


def retained_keys(units_by_demand: dict, source: dict, support: list, only=None) -> dict:
    """(scenario, case, set, level, demand) -> (blood task key, lambda indices), from the retained units (or ``only``,
    a list of (demand, unit) for the sample)."""
    out = {}
    pairs = only if only is not None else [(f, u) for f in DEMANDS for u in units_by_demand[f]]
    for factor, (i, a, b, r, ds) in pairs:
        for case, index in ((C57, a), (C72, b)):
            level = level_of(index)
            sets = {"P1": [i], "P2": [(i, d) for d in ds], "P3": list(r), "P4": list(r)}
            if only is not None:
                sets = {"P1": [i], "P2": [(i, ds[0])], "P3": [r[0]], "P4": [r[0]]}
            for name, keys in sets.items():
                for k in keys:
                    entry = out.setdefault((name, case, k, level, factor), set())
                    entry.add(index)
    return {key: sorted(value) for key, value in out.items()}


def blood_tasks(keys: dict, source: dict, support: list) -> list:
    tasks = {}
    for name, case, k, _level, _factor in keys:
        scenario = SCENARIOS[name]
        if name == "P2":
            i, d = k
            tasks[(name, case, k)] = ((name, case, k), source["p1"][i], case, scenario, support[d]["bag"])
        elif name == "P1":
            tasks[(name, case, k)] = ((name, case, k), source["p1"][k], case, scenario, None)
        else:
            tasks[(name, case, k)] = ((name, case, k), source["p3"][k], case, scenario, None)
    return [tasks[key] for key in sorted(tasks, key=str)]


def key_tasks(keys: dict, bloods: dict, a: float, gains, arrivals: dict) -> list:
    return [((name, case, k, level, factor), bloods[(name, case, k)], case, name, factor, level, lambdas, a, tuple(gains),
             arrivals) for (name, case, k, level, factor), lambdas in sorted(keys.items(), key=str)]


# 9. Tables, trade-off, envelopes ---------------------------------------------------------------------------------------

def _spread(values):
    return pt._spread(list(values))


def trajectory_tables(results: dict, gains) -> dict:
    """LOW / median / HIGH over the keys, per (scenario, case, demand, gain), at TIMES; D and lactate over the
    (key, lambda) pairs; the intervention state; the change against the T = 1 reference on the same key."""
    out = {}
    for name in SCENARIOS:
        for case in CASES:
            for factor in DEMANDS:
                mine = {key: value for key, value in results.items()
                        if key[0] == name and key[1] == case and key[4] == factor}
                if not mine:
                    continue
                table = {"keys": len(mine), "gains": {}, "interventions": {}}
                for m in TIMES:
                    table["interventions"][str(m)] = {
                        field: _spread(v["interventions"][str(m)][field] for v in mine.values())
                        for field in ("bleed", "crystalloid", "prbc", "controlled")}
                for gain in gains:
                    g = f"{gain:g}"
                    per = {}
                    for m in TIMES:
                        at = [v["gains"][g]["at"][str(m)] for v in mine.values() if v["gains"][g]["at"][str(m)]]
                        ref = [(v["gains"][g]["at"][str(m)], v["gains"]["0"]["at"][str(m)]) for v in mine.values()
                               if v["gains"][g]["at"][str(m)] and v["gains"]["0"]["at"][str(m)]]
                        lam = [x for v in mine.values() for x in v["gains"][g]["lambdas"].values()]
                        lam0 = [x for v in mine.values() for x in v["gains"]["0"]["lambdas"].values()]
                        per[str(m)] = {
                            **{field: _spread(r[field] for r in at if r[field] is not None) for field in READ},
                            "D": _spread(x["D"][str(m)] for x in lam if str(m) in x["D"]),
                            "lactate": _spread(x["lactate"][str(m)] for x in lam if str(m) in x["lactate"]),
                            "map_change": _spread(r["map"] - q["map"] for r, q in ref),
                            "sbp_change": _spread(r["sbp"] - q["sbp"] for r, q in ref),
                            "output_cost": _spread(r["output"] / q["output"] - 1.0 for r, q in ref),
                            "delivery_cost": _spread(r["delivery_rel"] / q["delivery_rel"] - 1.0 for r, q in ref),
                            "deficit_change": _spread(r["deficit"] - q["deficit"] for r, q in ref),
                            "D_change": _spread(x["D"][str(m)] - y["D"][str(m)] for x, y in zip(lam, lam0)
                                                if str(m) in x["D"] and str(m) in y["D"]),
                            "lactate_change": _spread(x["lactate"][str(m)] - y["lactate"][str(m)]
                                                      for x, y in zip(lam, lam0)
                                                      if str(m) in x["lactate"] and str(m) in y["lactate"]),
                        }
                    metric = [v["gains"][g]["metrics"] for v in mine.values()]
                    table["gains"][g] = {
                        "at": per,
                        "T_max": _spread(x["T_max"] for x in metric), "T_abs_max": _spread(x["T_abs_max"] for x in metric),
                        "max_dT": max(x["max_dT"] for x in metric), "max_dmap": max(x["max_dmap"] for x in metric),
                        "reference_max_dmap": max(x["reference_max_dmap"] for x in metric),
                        "delivery_ratio_min": _spread(x["delivery_ratio_min"] for x in metric
                                                      if x["delivery_ratio_min"] is not None),
                        "consciousness": {level: {"keys_crossing": sum(x["sbp_below"][level] is not None
                                                                       for x in metric),
                                                  "first_minute": _spread(x["sbp_below"][level] for x in metric
                                                                          if x["sbp_below"][level] is not None)}
                                          for level in (str(lv) for lv, _ in CONSCIOUSNESS_LEVELS)},
                        "windows": {w: {field: _spread(v["gains"][g]["windows"][w][field] for v in mine.values()
                                                       if w in v["gains"][g]["windows"])
                                        for field in ("map_change", "sbp_change")}
                                    for w in ("crystalloid", "unit 1", "unit 2")
                                    if any(w in v["gains"][g]["windows"] for v in mine.values())},
                        "adequacy": {status: sum(x["adequacy"] == status for v in mine.values()
                                                 for x in v["gains"][g]["lambdas"].values())
                                     for status in sorted({x["adequacy"] for v in mine.values()
                                                           for x in v["gains"][g]["lambdas"].values()})},
                    }
                out[f"{name} {case} x{factor:g}"] = table
    return out


def simulation_flags(results: dict, gains) -> dict:
    """Per gain: every SIMULATION_RULES rejection on any key, and the structural continuity checks."""
    out = {}
    for gain in gains:
        g = f"{gain:g}"
        metric = [v["gains"][g]["metrics"] for v in results.values()]
        out[g] = {"GUARD_CONTACT": sum(x["clamps"] > 0 for x in metric),
                  "OSCILLATION": sum(bool(x["oscillation"]) for x in metric),
                  "STOP": sum(x["stop"] is not None and x["reference_stop"] is None for x in metric),
                  "negative_pressure": sum(x["negative_pressure"] for x in metric),
                  "arrival_kept": all(x["T1_is_arrival"] for x in metric), "keys": len(metric)}
    return out


# 10. FD-LAC compatibility of the retained units (P2J-2-14) ------------------------------------------------------------

def _masks(function, scenario: str, key, hd57: dict, hd72: dict, a: int, b: int, arrivals: dict, factor: float,
           hd57_b: dict | None = None, hd72_a: dict | None = None) -> int:
    """The pair mask of one unit row: the 57m bits at lambda a on its own level's trajectory, the 72f bits at lambda b
    on its own (lactate_closure's unit functions, unchanged)."""
    first = function((key, {C57: hd57, C72: hd72_a if hd72_a is not None else hd72}, arrivals, [a], factor))[1]
    second = first if a == b else function((key, {C57: hd57_b if hd57_b is not None else hd57, C72: hd72}, arrivals,
                                                  [b], factor))[1]
    return ho._pair_mask(scenario, {a: first[a], b: second[b]}, a, b)


def _fd_task(task: tuple) -> tuple:
    """One retained unit at one demand, every gain at one afterload point: the candidates (P3 set x crystalloid point)
    that keep FD-LAC and L3 adequacy, against the unit's P2I-2AK count."""
    key, unit, factor, a, gains, bloods, arrivals = task
    i, la_, lb, r, ds = unit
    levels = {C57: level_of(la_), C72: level_of(lb)}
    anchors = {(case, lv): tone_anchors(case, lv, factor) for case in CASES for lv in set(levels.values())}
    out = {}
    for gain in gains:
        def hd(name, case, k, level):
            blood = bloods[(name, case, k)]
            return haemodynamic(blood, rebuild(blood, anchors[(case, level)], gain, a))

        def mask(function, scenario, name, k):
            return _masks(function, scenario, k, hd(name, C57, k, levels[C57]), hd(name, C72, k, levels[C72]), la_, lb,
                          arrivals, factor, hd57_b=hd(name, C57, k, levels[C72]), hd72_a=hd(name, C72, k, levels[C57]))
        l1 = mask(lc._l1_unit, L1, "P1", i) == 0
        q_ok = [q for q in r if mask(lc._l3_unit, L3, "P4", q) == 0]
        d_ok = [d for d in ds if mask(lc._l2_unit, L2, "P2", (i, d)) == 0]
        out[f"{gain:g}"] = {"l1": l1, "p3_sets": len(q_ok), "points": len(d_ok),
                            "candidates": (len(q_ok) * len(d_ok)) if l1 else 0}
    return key, {"reference_candidates": len(r) * len(ds), "gains": out}


def fd_tasks(units_by_demand: dict, bloods: dict, a: float, gains, arrivals: dict, only=None) -> list:
    pairs = only if only is not None else [(f, u) for f in DEMANDS for u in units_by_demand[f]]
    tasks = []
    for factor, unit in pairs:
        i, la_, lb, r, ds = unit
        need = [("P1", c, i) for c in CASES] + [("P4", c, q) for c in CASES for q in r] + [
            ("P2", c, (i, d)) for c in CASES for d in ds]
        tasks.append(((factor, i, la_, lb), unit, factor, a, tuple(gains), {k: bloods[k] for k in need}, arrivals))
    return tasks


def fd_summary(results: dict, gains) -> dict:
    out = {}
    for factor in DEMANDS:
        mine = [v for (f, *_), v in results.items() if f == factor]
        if not mine:
            continue
        reference = sum(v["reference_candidates"] for v in mine)
        out[f"{factor:g}"] = {"units": len(mine), "reference_candidates": reference,
                              "gains": {f"{g:g}": {"candidates": sum(v["gains"][f"{g:g}"]["candidates"] for v in mine),
                                                   "units_kept": sum(v["gains"][f"{g:g}"]["candidates"] > 0
                                                                     for v in mine),
                                                   "units_lost": sum(v["gains"][f"{g:g}"]["candidates"] == 0
                                                                     for v in mine),
                                                   "candidates_lost": sum(v["reference_candidates"]
                                                                          - v["gains"][f"{g:g}"]["candidates"]
                                                                          for v in mine)}
                                        for g in gains}}
    return out


# 11. Validation and the HR diagnostic -----------------------------------------------------------------------------------

COMPARED = ("T", "output", "p", "sbp", "dbp", "map", "deficit")


def _validate_task(task: tuple) -> tuple:
    """Full core runs of one sample row at every admissible pair, against the reconstruction (exact)."""
    key, entry, bag, case, name, factor, index, pairs, blood, arrivals = task
    scenario = SCENARIOS[name]
    anchors = tone_anchors(case, level_of(index), factor)
    out = {"compared": 0, "equal": True, "first_difference": None, "max_difference": 0.0}
    for gain, a in pairs:
        run_ = pt.full_run(entry, case, scenario, factor, LAMBDAS[index], bag, "midpoint",
                           {"deficit_to_tone_gain": gain, "afterload_sensitivity": a})
        rebuilt = rebuild(blood, anchors, gain, a)
        series = debt_and_lactate(blood, rebuilt, case, index, factor, arrivals)
        core = run_["rows"]
        mine = rebuilt["rows"]
        same = len(core) == len(mine) and run_["stop"] == rebuilt["stop"]
        for row, ref in zip(core, mine):
            values = {"T": row["T"], "output": row["output"], "p": row["p"], "sbp": row["sbp"], "dbp": row["dbp"],
                      "map": row["map"], "deficit": row["deficit"]}
            for field in COMPARED:
                if values[field] != ref[field]:
                    same = False
                    if values[field] is not None and ref[field] is not None:
                        out["max_difference"] = max(out["max_difference"], abs(values[field] - ref[field]))
                    out["first_difference"] = out["first_difference"] or [_pair(gain, a), row["minute"], field]
            for field in ("D", "lactate"):
                if row[field] != series[field][row["minute"]]:
                    same = False
                    out["max_difference"] = max(out["max_difference"], abs(row[field] - series[field][row["minute"]]))
                    out["first_difference"] = out["first_difference"] or [_pair(gain, a), row["minute"], field]
        out["compared"] += 1
        out["equal"] = out["equal"] and same
    return key, out


def validation_tasks(sample: list, source: dict, support: list, bloods: dict, arrivals: dict) -> list:
    pairs = tuple(admissible())
    tasks = []
    for factor, (i, a, b, r, ds) in sample:
        for case, index in ((C57, a), (C72, b)):
            for name, entry, bag, k in (("P1", source["p1"][i], None, i), ("P2", source["p1"][i], support[ds[0]]["bag"],
                                                                           (i, ds[0])),
                                        ("P3", source["p3"][r[0]], None, r[0]), ("P4", source["p3"][r[0]], None, r[0])):
                tasks.append(((factor, i, case, name), entry, bag, case, name, factor, index, pairs,
                              bloods[(name, case, k)], arrivals))
    return tasks


HR_KEYS = ("arrival", "l1_120", "l3_60", "l3_90", "l3_120", "benefit_1", "benefit_2", "max_hr")


def _hr_task(task: tuple) -> tuple:
    """L1, L3 and the two counterfactuals of one sample (case, P3 set, lambda) at every gain (a = 0.3): HR readings under
    each primary latent combination of P2I-2AK's pool at that demand."""
    key, entry, point, case, factor, candidates, position, gains = task
    out = {}
    for gain in gains:
        changes = {"deficit_to_tone_gain": gain}
        runs = {sc: hf.full_run({"entry": entry, "point": point, "bag": None}, case, sc, factor, "midpoint", changes)
                for sc in (L1, L3, hf.CF1, hf.CF2)}
        readings = []
        for candidate in candidates:
            rate = hs.intrinsic_levels(case)[candidate["intrinsic"][position]]
            readings.append(hf.readings(runs, rate, candidate))
        out[f"{gain:g}"] = readings
    return key, out


def hr_tasks(sample: list, source: dict, pools: dict, gains) -> list:
    tasks = []
    for factor, (i, a, b, r, ds) in sample:
        for case, index, position in ((C57, a, 0), (C72, b, 1)):
            tasks.append(((factor, r[0], case, index), source["p3"][r[0]], LAMBDAS[index], case, factor,
                          pools[factor], position, tuple(gains)))
    return tasks


def hr_summary(results: dict, sample: list, gains) -> dict:
    out = {}
    for factor, (i, a, b, r, ds) in sample:
        r57, r72 = results[(factor, r[0], C57, a)], results[(factor, r[0], C72, b)]
        for g in (f"{x:g}" for x in gains):
            slot = out.setdefault(f"{factor:g}", {}).setdefault(g, {"rows": 0, "failures": {}, "readings": {}})
            for x57, x72 in zip(r57[g], r72[g]):
                slot["rows"] += 1
                for name in hf.failures(x57, x72):
                    slot["failures"][name] = slot["failures"].get(name, 0) + 1
                for case, x in ((C57, x57), (C72, x72)):
                    for field in HR_KEYS:
                        slot["readings"].setdefault(f"{case} {field}", []).append(x[field] if x["complete"] else None)
    for factor, by_gain in out.items():
        reference = by_gain["0"]["readings"]
        for slot in by_gain.values():
            slot["change"] = {name: _spread(v - w for v, w in zip(values, reference[name])
                                            if v is not None and w is not None)
                              for name, values in slot["readings"].items()}
        for slot in by_gain.values():
            slot["readings"] = {name: _spread(v for v in values if v is not None)
                                for name, values in slot["readings"].items()}
    return out


# 12. Envelopes, trade-off, identifiability, verdict -----------------------------------------------------------------------

def _median(item):
    return None if item is None else item["median"]


def envelopes(tables: dict, sample_tables: dict, gains) -> dict:
    """The faculty decision surface A-I: proposals with distributions, reference and sensitivities; nothing applied."""
    out = {}
    for name, spec in ENVELOPES.items():
        cases = [spec["case"]] if "case" in spec else list(CASES)
        item = {"question": spec["question"], "rationale": spec["rationale"], "status": "PROPOSED_NOT_APPROVED",
                "basis": "PHYSIOLOGICAL (direction); EXPLORATORY (no numeric bound proposed); no EVIDENCE beyond "
                         "arrival", "by_case": {}}
        for case in cases:
            per = {}
            for factor in DEMANDS:
                table = tables.get(f"{spec['scenario']} {case} x{factor:g}")
                if table is None:
                    continue
                rows = {}
                for gain in gains:
                    g = f"{gain:g}"
                    if "window" in spec:
                        w = table["gains"][g]["windows"].get(spec["window"], {})
                        rows[g] = {field: w.get(field) for field in spec["readings"]}
                    else:
                        at = table["gains"][g]["at"][str(spec["minute"])]
                        values = {}
                        for field in spec["readings"]:
                            if field == "T_max":
                                values[field] = table["gains"][g]["T_max"]
                            else:
                                values[field] = at.get(field)
                        rows[g] = values
                per[f"{factor:g}"] = rows
            sens_gain = {field: {f: [_median(per[f][f"{g:g}"].get(field)) for g in gains] for f in per}
                         for field in spec["readings"]}
            sens_demand = {field: {f"{g:g}": [_median(per[f][f"{g:g}"].get(field)) for f in per] for g in gains}
                           for field in spec["readings"]}
            sens_a = {}
            for a, sample in sample_tables.items():
                for factor in DEMANDS:
                    table = sample.get(f"{spec['scenario']} {case} x{factor:g}")
                    if table is None:
                        continue
                    for gain in gains:
                        g = f"{gain:g}"
                        if g not in table["gains"]:      # rejected analytically at this afterload point
                            continue
                        if "window" in spec:
                            w = table["gains"][g]["windows"].get(spec["window"], {})
                            value = {field: _median(w.get(field)) for field in spec["readings"]}
                        else:
                            at = table["gains"][g]["at"][str(spec["minute"])]
                            value = {field: (_median(table["gains"][g]["T_max"]) if field == "T_max"
                                             else _median(at.get(field))) for field in spec["readings"]}
                        sens_a.setdefault(f"x{factor:g} g{g}", {})[f"a{a:g}"] = value
            item["by_case"][case] = {"distribution": per, "reference": {f: per[f]["0"] for f in per},
                                     "sensitivity_gain": sens_gain, "sensitivity_demand": sens_demand,
                                     "sensitivity_a_sample": sens_a}
        out[name] = item
    return out


def tradeoff(screen: dict, flags: dict, sample_flags: dict, fd: dict, fd_sample: dict) -> dict:
    out = {}
    for pair, item in screen.items():
        gain, a = item["gain"], item["a"]
        if item["status"] != "ADMISSIBLE":
            out[pair] = {"class": "ANALYTIC_REJECTION", "reasons": item["reasons"]}
            continue
        if gain == REFERENCE_GAIN:
            out[pair] = {"class": "REFERENCE_T_EQUALS_1"}
            continue
        g = f"{gain:g}"
        source_flags = flags.get(a, {}).get(g) or sample_flags.get(a, {}).get(g)
        simulation = [name for name in SIMULATION_RULES if source_flags and source_flags.get(name, 0)]
        fd_source = fd if a == PRIMARY_AFTERLOAD else fd_sample.get(a, {})
        lost = sum(fd_source.get(f, {}).get("gains", {}).get(g, {}).get("candidates_lost", 0) for f in fd_source)
        scope = "ALL_RETAINED_UNITS" if a == PRIMARY_AFTERLOAD else "SAMPLE_ONLY"
        if simulation:
            klass = "UNSTABLE_FEEDBACK"
        elif lost:
            klass = "PRESSURE_SUPPORTED_AT_DELIVERY_COST"
        else:
            klass = "PRESSURE_SUPPORTED_WITH_STABLE_DELIVERY"
        out[pair] = {"class": klass, "simulation_rejections": simulation, "fd_lac_candidates_lost": lost,
                     "scope": scope}
    return out


IDENTIFIABILITY = {
    "tone gain": ("NON_IDENTIFIABLE", "no authored pressure, output or resistance after arrival, and the arrival pressure "
                                      "is exact by construction at every gain (T = 1 there): nothing observed reaches "
                                      "g. Bounded only structurally (g a < 1, 1 + g <= 3); faculty envelopes A, B and F "
                                      "would make it PARTIALLY_CONSTRAINED (their sensitivity to g is reported)"),
    "afterload a": ("NON_IDENTIFIABLE", "reaches pressure and output only through T != 1, and no output or resistance is "
                                         "observed; with dynamic tone a and g act jointly (pressure ~ T / (1 + a (T - 1)) "
                                         "with T set by g), so even pressure envelopes would constrain the pair, not a"),
    "T trajectory": ("NON_IDENTIFIABLE", "T is never observed; given g its shape is fixed by the certified signal "
                                          "(s from delivery and demand), so it is identified only once g is"),
    "pressure / output composite": ("POORLY_IDENTIFIED", "MAP = arrival MAP x Q x T: at arrival WELL_CONSTRAINED by "
                                                          "anchoring (exact by construction), beyond arrival nothing "
                                                          "observed; output is fixed by the certified blood physiology "
                                                          "at T = 1 and moves with tone only through a"),
}


def identifiability(envelope: dict) -> dict:
    """The table, with the computed spread across gains of the envelope medians (what an envelope could constrain)."""
    spread = {}
    for name in ("A", "B", "F"):
        for case, item in envelope[name]["by_case"].items():
            for field, by_demand in item["sensitivity_gain"].items():
                for factor, values in by_demand.items():
                    present = [v for v in values if v is not None]
                    if present:
                        spread[f"{name} {case} {field} x{factor}"] = max(present) - min(present)
    return {"table": {k: list(v) for k, v in IDENTIFIABILITY.items()}, "rule": IDENTIFIABILITY_RULE,
            "envelope_spread_across_gains": spread}


def verdict(probe: dict, flags: dict, sample_flags: dict, fd: dict, tables: dict, validation: dict, reuse: dict,
            reference_equal: bool, deterministic: bool, trade: dict, gains) -> dict:
    checks = {
        "tone_semantics_coherent": all(probe["checks"][k] for k in ("1", "2", "6")) and reference_equal and all(
            flag["arrival_kept"] for by_gain in (flags, *sample_flags.values()) for flag in by_gain.values()),
        "feedback_deterministic_stable": probe["checks"]["5"] and deterministic and not any(
            flag[name] for by_gain in (flags, *sample_flags.values()) for flag in by_gain.values()
            for name in ("GUARD_CONTACT", "OSCILLATION", "STOP")),
        "no_pathological_loop": not any(item.get("class") == "UNSTABLE_FEEDBACK" for item in trade.values()),
        "pressure_continuous_nonnegative": probe["checks"]["4"] and probe["checks"]["8"] and not any(
            flag["negative_pressure"] for by_gain in (flags, *sample_flags.values()) for flag in by_gain.values()),
        "zero_output_consistent": probe["checks"]["7"] and probe["checks"]["3"],
        "lactate_satisfiable": all(any(fd[f]["gains"][f"{g:g}"]["candidates"] > 0 for g in gains if g > 0)
                                   for f in fd) and len(fd) == len(DEMANDS),
        "distributions_available": all(f"{name} {case} x{f:g}" in tables for name in SCENARIOS for case in CASES
                                       for f in DEMANDS),
        "reconstruction_exact": validation["equal"] and validation["compared"] > 0,
        "upstream_reproduced": reuse["units_equal"] and all(
            fd[f]["gains"][f"{REFERENCE_GAIN:g}"]["candidates"] == fd[f]["reference_candidates"] for f in fd),
        "pressure_to_hr_deferred": hp.PRIMARY_HR_CALIBRATION.get("sympathetic_per_pressure_deficit") == 0.0,
        "nothing_approved": True,
    }
    blockers = [name for name, ok in checks.items() if not ok]
    return {"verdict": READY if not blockers else f"{NOT_READY} — {blockers[0]}", "checks": checks,
            "blockers": blockers, "approved": [], "rule": VERDICT_RULE}


# 13. Design, freeze, run --------------------------------------------------------------------------------------------------

def design() -> dict:
    return {"revision": REVISION, "decided": DECIDED, "faculty": FACULTY, "tone": TONE, "timing": TIMING,
            "feedback": FEEDBACK, "arrival": ARRIVAL_RULE, "literal_alternative": LITERAL_ALTERNATIVE,
            "gains": list(GAINS), "reference_gain": REFERENCE_GAIN, "afterload": list(AFTERLOAD),
            "primary_afterload": PRIMARY_AFTERLOAD, "range_rule": RANGE_RULE, "analytic_rules": ANALYTIC_RULES,
            "simulation_rules": SIMULATION_RULES, "screen": analytic_screen(), "demand_rule": DEMAND_RULE,
            "design": DESIGN, "reconstruction_rule": RECONSTRUCTION_RULE, "probe_rule": PROBE_RULE,
            "probe_pumps": list(PROBE_PUMPS), "probe_tones": list(PROBE_TONES), "steady_minutes": STEADY_MINUTES,
            "scenarios": dict(SCENARIOS), "times": list(TIMES), "tradeoff_rule": TRADEOFF_RULE,
            "consciousness_levels": [list(x) for x in CONSCIOUSNESS_LEVELS], "envelopes": ENVELOPES,
            "envelope_rule": ENVELOPE_RULE, "identifiability": {k: list(v) for k, v in IDENTIFIABILITY.items()},
            "identifiability_rule": IDENTIFIABILITY_RULE, "baroreflex_plan": BAROREFLEX_PLAN,
            "verdict_rule": VERDICT_RULE, "policy": POLICY,
            "changes": {k: {f: list(v) if isinstance(v, tuple) else v for f, v in item.items()}
                        for k, item in P2J2_CHANGES.items()}}


def freeze_digest() -> str:
    text = json.dumps({"revision": REVISION, "p2j1": hashlib.sha256(P2J1_RECORD.read_bytes()).hexdigest(),
                       "design": design(), "sources": bf.freeze_sources()}, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _repeat_identical(source: dict) -> bool:
    entry = source["p1"][0]
    first = pt.full_run(entry, C57, L1, 1.0, LAMBDAS[0], None, "midpoint", {"deficit_to_tone_gain": 1.0})
    second = pt.full_run(entry, C57, L1, 1.0, LAMBDAS[0], None, "midpoint", {"deficit_to_tone_gain": 1.0})
    return json.dumps(first["rows"], sort_keys=True) == json.dumps(second["rows"], sort_keys=True)


def _reference_equals_p2j1(results: dict, bloods: dict) -> bool:
    """Gain 0 is P2J-1's T = 1: its MAP is the arrival MAP times the cached output, minute by minute."""
    for (name, case, k, level, factor), value in results.items():
        blood = bloods[(name, case, k)]
        anchors = tone_anchors(case, level, factor)
        arrival_map = (anchors.sbp + 2 * anchors.dbp) / 3
        at = value["gains"]["0"]["at"]
        for m in TIMES:
            if at[str(m)] is None:
                continue
            if at[str(m)]["T"] != 1.0 or abs(at[str(m)]["map"] - arrival_map * blood["output1"][m]) > 1e-9 * arrival_map:
                return False
    return True


def run(progress=None, map_=map) -> dict:
    say = progress or (lambda *_: None)
    with lr.P2FGuard(), lr.LegacyLock():
        p2j1_record()
        out = {"freeze_digest": freeze_digest(), "decided": DECIDED, "revision": REVISION, "policy": POLICY,
               "faculty": FACULTY, "record": P2J1_DIGEST, "tone": TONE, "timing": TIMING, "feedback": FEEDBACK,
               "arrival_rule": ARRIVAL_RULE, "literal_alternative_rule": LITERAL_ALTERNATIVE}
        say("analytic screen and probes")
        screen = analytic_screen()
        probe = probes()
        signals = {f"{case} {level} x{f:g}": arrival_tone_signal(tone_anchors(case, level, f),
                                                                  tone_profile(0.0, PRIMARY_AFTERLOAD))
                   for case in CASES for level in LEVELS for f in DEMANDS}
        out.update({"screen": screen, "probes": probe, "arrival_signals": signals,
                    "literal_alternative": literal_alternative(signals), "range_rule": RANGE_RULE,
                    "gains": list(GAINS), "afterload": list(AFTERLOAD), "demand_rule": DEMAND_RULE})
        structural = [k for k in ("1", "2", "3", "4", "5", "6", "7") if not probe["checks"][k]]
        if structural:
            out["verdict"] = {"verdict": f"{NOT_READY} — probe {structural[0]}", "checks": probe["checks"],
                              "blockers": [f"probe {k}" for k in structural], "approved": [], "rule": VERDICT_RULE,
                              "early_stop": True}
            return out
        say("retained units")
        source_record = la.record_p2i2ab()
        source, support = la.source_space(source_record), source_record["crystalloid_support"]
        arrivals = lr.arrival_table()
        tasks = lc.haemodynamic_tasks(source, support)
        store = lc.haemodynamics(tasks, map_)
        units_by_demand, digests = {}, {}
        for factor in DEMANDS:
            region = ho.retained_region(source, support, arrivals, tasks, store, factor, map_)
            units_by_demand[factor], digests[f"{factor:g}"] = region["units"], region["digest"]
        reuse = {"units_digests": digests, "units_equal": all(digests[f"{f:g}"] == UNITS[f] for f in DEMANDS),
                 "outside_unchanged": outside_unchanged(), "haemodynamic_trajectories": len(set(tasks.values()))}
        if not reuse["units_equal"]:
            raise AssertionError("the retained lactate units are not P2I-2AK's")
        sample = pt.sample_units(units_by_demand)
        keys = retained_keys(units_by_demand, source, support)
        sample_keys = retained_keys(units_by_demand, source, support, only=sample)
        say("blood trajectories")
        bloods = dict(map_(_blood_task, blood_tasks({**keys, **sample_keys}, source, support)))
        say("tone trajectories")
        pairs = admissible()
        primary_gains = [g for g, a in pairs if a == PRIMARY_AFTERLOAD]
        results = dict(map_(_key_task, key_tasks(keys, bloods, PRIMARY_AFTERLOAD, primary_gains, arrivals)))
        tables = trajectory_tables(results, primary_gains)
        flags = simulation_flags(results, primary_gains)
        sample_tables, sample_flags = {}, {}
        for a in AFTERLOAD:
            gains_a = [g for g, x in pairs if x == a]
            sample_results = dict(map_(_key_task, key_tasks(sample_keys, bloods, a, gains_a, arrivals)))
            sample_tables[a] = trajectory_tables(sample_results, gains_a)
            sample_flags[a] = simulation_flags(sample_results, gains_a)
        say("FD-LAC")
        fd_raw = dict(map_(_fd_task, fd_tasks(units_by_demand, bloods, PRIMARY_AFTERLOAD, primary_gains, arrivals)))
        fd = fd_summary(fd_raw, primary_gains)
        fd_sample = {}
        for a in AFTERLOAD:
            if a == PRIMARY_AFTERLOAD:
                continue
            gains_a = [g for g, x in pairs if x == a]
            raw = dict(map_(_fd_task, fd_tasks(units_by_demand, bloods, a, gains_a, arrivals, only=sample)))
            fd_sample[a] = fd_summary(raw, gains_a)
        say("validation")
        checked = dict(map_(_validate_task, validation_tasks(sample, source, support, bloods, arrivals)))
        validation = {"rows": len(checked), "compared": sum(v["compared"] for v in checked.values()),
                      "equal": all(v["equal"] for v in checked.values()),
                      "max_difference": max(v["max_difference"] for v in checked.values()),
                      "first_difference": next((v["first_difference"] for v in checked.values()
                                                if v["first_difference"]), None)}
        say("HR diagnostic")
        record_aj = hf.p2i2aj_record()
        pools = {f: hf.arrival_pool(record_aj, f)["primary"] for f in DEMANDS}
        hr_raw = dict(map_(_hr_task, hr_tasks(sample, source, pools, primary_gains)))
        hr = hr_summary(hr_raw, sample, primary_gains)
        deterministic = _repeat_identical(source)
        reference_equal = _reference_equals_p2j1(results, bloods)
        trade = tradeoff(screen, {PRIMARY_AFTERLOAD: flags}, sample_flags, fd, fd_sample)
        envelope = envelopes(tables, sample_tables, primary_gains)
        out.update({
            "reuse": reuse, "units": {f"{f:g}": len(units_by_demand[f]) for f in DEMANDS},
            "sample": [[f, list(u[:3])] for f, u in sample], "keys": len(keys), "sample_keys": len(sample_keys),
            "trajectories": tables, "flags": flags,
            "sample_trajectories": {f"a{a:g}": t for a, t in sample_tables.items()},
            "sample_flags": {f"a{a:g}": t for a, t in sample_flags.items()},
            "fd_lac": fd, "fd_lac_sample": {f"a{a:g}": v for a, v in fd_sample.items()},
            "validation": validation, "hr": hr, "deterministic": deterministic, "reference_equals_p2j1": reference_equal,
            "tradeoff": trade, "tradeoff_rule": TRADEOFF_RULE, "envelopes": envelope, "envelope_rule": ENVELOPE_RULE,
            "identifiability": identifiability(envelope), "baroreflex_plan": BAROREFLEX_PLAN,
            "efficiency": {"blood_runs": len(bloods), "key_rebuilds_primary": len(results) * len(primary_gains),
                           "key_rebuilds_sample": sum(len([g for g, x in pairs if x == a]) for a in AFTERLOAD)
                           * len(sample_keys),
                           "fd_units": len(fd_raw), "validation_full_runs": validation["compared"],
                           "hr_full_runs": 4 * len(hr_raw) * len(primary_gains),
                           "core_runs_without_reconstruction": len(keys) * len(primary_gains)
                           + len(sample_keys) * (len(pairs) - len(primary_gains)),
                           "analytic_rejections": sum(v["status"] == "ANALYTIC_REJECTION" for v in screen.values()),
                           "cartesian_sweep": False, "legacy_read": False}})
        out["verdict"] = verdict(probe, flags, sample_flags, fd, tables, validation, reuse, reference_equal,
                                 deterministic, trade, primary_gains)
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--digest", action="store_true")
    parser.add_argument("--design", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    if args.digest:
        print(freeze_digest())
    if args.design:
        print(json.dumps(design(), indent=1, sort_keys=True, default=str))
    if args.run:
        if args.out is None:
            parser.error("--run needs --out")
        args.out.mkdir(parents=True, exist_ok=True)
        path = args.out / "vascular_tone.json"
        path.write_text(json.dumps(run(lambda step_: print(step_, flush=True)), indent=1, sort_keys=True,
                                   default=str), encoding="utf-8")
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
