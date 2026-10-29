"""P2I-2AD: final D / lactate semantic closure for the GI lactate (shadow only).

Faculty decisions (2026-10-29, P2I-2AD), recorded here and applied to the P2I-2AB current source space:

1. L3 adequacy persists through 120 min. L3 is successful definitive haemostasis and adequate resuscitation: once
   sustained adequate oxygen availability begins after haemostasis (T*, FD-LAC-04's own restoration trigger) the
   effective deficit stays 0 through minute 120. No T*: L3_RESUSCITATION_INADEQUATE. A deficit again before 120:
   L3_RESUSCITATION_LOST. Both are rejections of their own, never FD-LAC-04 or FD-LAC-05 failures, and NOT_EVALUABLE
   is never a passing final L3 state.
2. D repayment needs an adequate interval: a minute repays D only when it has no deficit at its start and none at its
   end; crossing from no deficit into one it neither repays nor accrues (``integration._no_repayment_across``).
3. tau_D does not define D -> lactate production. D accrues by the deficit-to-D gain, repays with tau_D, produces
   lactate by its own D-to-lactate gain (``debt_to_lactate_gain``) and lactate clears with tau_L. The historical gain
   G (``lactate_per_output_deficit``) was a steady-state gain of the pre-P2I-2AC D, k = G / (tau_D tau_L): it cannot
   be translated into an independent gain (OLD_G_RANGE_SEMANTICALLY_INVALID), so the new range is built only from
   dimensional consistency, the faculty envelopes and synthetic probes (K_LD_RULE), before any count.
4. HR / RR: the corrected D raises them in untreated runs; the causal propagation is accepted, the magnitudes are not
   (MAGNITUDE_PENDING_HR_RR_CALIBRATION). Nothing here reads, targets or calibrates HR or RR.
5. Demand 0.9 / 1.0 / 1.1 stays explicit uncertainty; rho 2.0-3.0 (2.5 representative), 1 only a synthetic
   reference, never counted; FD-LAC-01..06 unchanged.

The haemodynamic trajectories of P2I-2AC (delivery, demand, haemostasis, actual flow, stop) do not read D or the
lactate gain: they are simulated once and D and lactate are post-processed with the corrected recurrences, validated
against full core runs (else the run stops). Nothing is fitted, selected or approved; no SBP, MAP, HR or RR is
calibrated; collapse stays off.
"""
from __future__ import annotations

import argparse
import hashlib
import inspect
import itertools
import json
import math
from dataclasses import replace
from pathlib import Path

from . import blood_anchors, calibration, derived, gi_reference
from .bands import Drift
from . import blood_constraints as bc
from . import blood_extension as be
from . import blood_fluid_calibration as bf
from . import faculty_constraints as fd
from . import lactate_adequacy as la
from . import lactate_rebuild as lr
from .derived import DEFAULT_PROFILE, derive, effective_delivery, effective_oxygen_deficit, oxygen_balance
from .integration import CHANNEL_BOUNDS, run as core_run
from .state import Channel

DECIDED = "2026-10-29"
REVISION = "P2I-2AD"
ROOT = lr.ROOT
CASES = lr.CASES
L1, L2, L3 = lr.L1, lr.L2, lr.L3
SCENARIOS = lr.SCENARIOS
MINUTES, TIMES = lr.MINUTES, lr.TIMES
RESERVE = lr.RESERVE
LEVELS = lr.LEVELS
SETTINGS = lr.SETTINGS
PASS, FAIL = fd.PASS, fd.FAIL
RECOVERING, PERSISTENT = lr.RECOVERING, lr.PERSISTENT
STOPPED = lr.STOPPED
ANALYTIC_REJECTION, SIMULATION_REJECTION = lr.ANALYTIC_REJECTION, lr.SIMULATION_REJECTION
P2I2AC_RECORD = ROOT / "docs" / "revision" / "P2I2AC_lactate_adequacy.json"
P2I2AC_DIGEST = "fc49efae455d8a5c259df703a5bcd43bf4c87d3b0ba35dfefdbf1a1567387df5"
P2I2AC_REGION_DIGEST = "99456c31a934b4553960ce56412ffc4980ddc75797655c6aa07b1fe4201f5994"

CAUSAL_PROPAGATION_ACCEPTED = "CAUSAL_PROPAGATION_ACCEPTED"
MAGNITUDE_PENDING = "MAGNITUDE_PENDING_HR_RR_CALIBRATION"
FACULTY = {
    "decided": DECIDED,
    "l3_adequacy": "L3 adequacy persists through 120: once sustained adequate or compensated oxygen availability "
                   "begins after haemostasis, effective_deficit stays 0 through minute 120; otherwise "
                   "L3_RESUSCITATION_LOST, rejected from the final L3 region, never an FD-LAC-05 failure; NOT_EVALUABLE "
                   "is never a passing final L3 state",
    "debt_repayment": "D repays only during an interval that stays oxygen-adequate: effective deficit 0 at the start "
                      "and at the end of the step; crossing 0 -> critical, no repayment and no debt added beyond what "
                      "the deficit signal adds",
    "lactate_coupling": "tau_D is debt-repayment kinetics only and must not define D -> lactate production; an "
                        "independent D_to_lactate_gain, not derived from tau_D or tau_L, not tuned to the legacy, no "
                        "value chosen",
    "hr_rr": f"{CAUSAL_PROPAGATION_ACCEPTED}; {MAGNITUDE_PENDING}: the corrected D raises HR and RR in untreated runs; "
             "D is not reverted; the historical P2F HR1 rejection is not a target; HR and RR are not calibrated here",
    "demand": "0.9 / 1.0 / 1.1 explicit uncertainty: ROBUST_ACROSS_DEMAND, DEMAND_SENSITIVE, DEMAND_INCOMPATIBLE; no "
              "value approved; robustness never a hard filter",
    "rho": "physiological 2.0-3.0, 2.5 representative; 1 only synthetic reference; not in the physiological "
           "multiplicity; invariance under re-anchoring reported once",
    "fd_lac": "FD-LAC-01..06 unchanged (envelopes 57m 4.4-7.0 / 72f 3.4-5.5 at 60 untreated; FD-LAC-04 L(T*+30) < "
              "L(T*), no fixed 10 %; FD-LAC-05 57m 1.5-4.0 / 72f 1.2-3.5 with L120 < L(T*); FD-LAC-06 by actual flow "
              "and recovering-vs-persistent critical semantics)",
}


# 1. The D -> lactate gain: why the old range does not translate, and the new range -------------------------------

OLD_G_RANGE_STATUS = "OLD_G_RANGE_SEMANTICALLY_INVALID"
OLD_G_RANGE_REASON = (
    "G (lactate_per_output_deficit, 2 / 6 / 12) was read as the steady-state lactate excess per unit of g x sustained "
    "deficit of the pre-P2I-2AC D (D* = g s tau_D, X* = k D* tau_L = G g s), with k = G / (tau_D tau_L). Since P2I-2AC "
    "D has no steady state under a deficit, and one G maps to nine production constants across the tau_D x tau_L grid: "
    "the G range carries tau_D in its units and cannot be translated into a gain independent of tau_D. The production "
    "constants the old grid induced are reported for comparison only.")
#: The resolution at which every faculty lactate envelope is stated (one decimal, mmol/L).
ENVELOPE_RESOLUTION = 0.1
K_LD_POINT_COUNT = 5


def k_ld_design() -> dict:
    """The exploration range of debt_to_lactate_gain, from dimensional consistency, the faculty envelopes and synthetic
    probes only (frozen before any count). Units: mmol/L of lactate per minute per unit of D (index-minutes). Synthetic
    probe: a constant debt held for the FD-LAC-02/03 horizon (60 min), no accrual, no clearance (production alone).
    - lowest gain: the largest declared arrival debt (the band's upper level, 60) moves lactate by only the
      resolution the envelopes are stated in (0.1 mmol/L);
    - highest gain: the smallest nonzero declared arrival debt (the band's midpoint, 20) spans the widest untreated
      60-min envelope above arrival (57m: 7.0 - 4.4 = 2.6 mmol/L).
    Five points, log-spaced (equal ratios) between the two, both included."""
    band = gi_reference.arrival_debt_band(CASES[0])
    if any((b.lower, b.midpoint, b.upper) != (band.lower, band.midpoint, band.upper)
           for b in (gi_reference.arrival_debt_band(case) for case in CASES)):
        raise AssertionError("the arrival-debt band is the same for both cases")
    horizon = fd.ENVELOPES[CASES[0]]["minute"]
    span = max(fd.ENVELOPES[case]["high"] - fd.ENVELOPES[case]["arrival"] for case in CASES)
    low = ENVELOPE_RESOLUTION / (horizon * band.upper)
    high = span / (horizon * band.midpoint)
    ratio = (high / low) ** (1.0 / (K_LD_POINT_COUNT - 1))
    points = tuple(low * ratio ** i for i in range(K_LD_POINT_COUNT - 1)) + (high,)
    old = sorted({g / (tau_d * tau_l) for g in calibration.REGISTRY["lactate_per_output_deficit"].points()
                  for tau_d in calibration.REGISTRY["debt_clearance_tau_min"].points()
                  for tau_l in calibration.REGISTRY["lactate_clearance_tau_min"].points()})
    return {"units": "mmol/L per minute per unit of D (index-minutes)", "horizon_min": horizon,
            "envelope_resolution": ENVELOPE_RESOLUTION, "widest_untreated_span": span,
            "debt_levels": {"midpoint": band.midpoint, "upper": band.upper}, "low": low, "high": high,
            "points": points, "ratio": ratio, "default": DEFAULT_PROFILE.debt_to_lactate_gain,
            "old_status": OLD_G_RANGE_STATUS, "old_reason": OLD_G_RANGE_REASON,
            "old_induced_constants_for_comparison_only": old}


K_LD_RULE = k_ld_design.__doc__
K_LD = k_ld_design()["points"]
KINETIC = ("debt_clearance_tau_min", "debt_per_delivery_deficit", "debt_to_lactate_gain", "lactate_clearance_tau_min")


def kinetic_points() -> dict:
    return {"debt_clearance_tau_min": tuple(calibration.REGISTRY["debt_clearance_tau_min"].points()),
            "debt_per_delivery_deficit": tuple(calibration.REGISTRY["debt_per_delivery_deficit"].points()),
            "debt_to_lactate_gain": K_LD,
            "lactate_clearance_tau_min": tuple(calibration.REGISTRY["lactate_clearance_tau_min"].points())}


def lambdas() -> list[tuple]:
    """Every lactate-side combination, Cartesian: (tau_D, deficit-to-D gain, D-to-lactate gain, tau_lactate, excess
    level, arrival debt level, arrival delivery level). The D-to-lactate gain is never derived from tau_D."""
    points = kinetic_points()
    return [(*kinetics, excess, debt, delivery)
            for kinetics in itertools.product(*(points[name] for name in KINETIC))
            for excess in LEVELS for debt, delivery in lr.ARRIVAL_PAIRS]


LAMBDAS = lambdas()
CANONICAL = (60.0, 1.0, K_LD[2], 120.0, "midpoint", "midpoint", "midpoint")


def lambda_label(index: int) -> dict:
    tau_d, gain_k, k, tau_l, excess, debt, delivery = LAMBDAS[index]
    return {"debt_clearance_tau_min": tau_d, "debt_per_delivery_deficit": gain_k, "debt_to_lactate_gain": k,
            "lactate_clearance_tau_min": tau_l, "arrival_lactate_excess": excess, "arrival_oxygen_debt": debt,
            "arrival_delivery_ratio": delivery}


PARAMETER_SEMANTICS = {
    "debt_per_delivery_deficit": {"role": "deficit -> D accumulation per minute (g)", "acts": "while the deficit at "
                                  "the start of a minute is > 0", "reaches_lactate": "only as k x g"},
    "debt_clearance_tau_min": {"role": "D repayment kinetics (tau_D)", "acts": "only across minutes with no deficit at "
                               "start and end", "reaches_lactate": "through D's repayment only; never production"},
    "debt_to_lactate_gain": {"role": "D -> lactate production per minute (k)", "acts": "every minute, on the D of the "
                             "minute before", "reaches_lactate": "only as k x g and k x arrival D"},
    "lactate_clearance_tau_min": {"role": "lactate clearance (tau_L)", "acts": "every minute, on the excess",
                                  "reaches_lactate": "directly (clearance)"},
    "arrival_oxygen_debt": {"role": "D at arrival (D0)", "acts": "start value of D; repaid like any D",
                            "reaches_lactate": "only as k x D0"},
    "arrival_lactate_excess": {"role": "clearable lactate at arrival (X0)", "acts": "start value of the excess",
                               "reaches_lactate": "directly (X0 cleared with tau_L)"},
}


# 2. The corrected D and lactate, post-processed -------------------------------------------------------------------

def debt_series(debt_input: list, end_deficit: list, d0: float, tau_d: float, gain_k: float) -> list:
    """The core's D minute by minute since P2I-2AD: g x deficit when the minute starts in a deficit; -D / tau_D only
    when it starts and ends without one; unchanged when it crosses into a deficit (within the channel guard)."""
    lower, upper = CHANNEL_BOUNDS[Channel.D][:2]
    out, debt = [d0], d0
    for start, end in zip(debt_input, end_deficit):
        if start > 0.0:
            debt = min(upper, max(lower, debt + gain_k * start))
        elif end == 0.0:
            debt = min(upper, max(lower, debt - debt / tau_d))
        out.append(debt)
    return out


def lactate_series(debt: list, x0: float, k: float, tau_l: float, baseline: float, floor: float) -> list:
    """The core's lactate (derived.lactate_after_minute since P2I-2AD): X + k x D of the minute before - X / tau_L."""
    excess = x0
    out = [max(floor, baseline + excess)]
    for d in debt[:-1]:
        excess = excess + k * d - excess / tau_l
        out.append(max(floor, baseline + excess))
    return out


def memory_kinetics(point: tuple) -> dict:
    """FD-LAC-05's report-only debt memory (faculty_constraints, frozen) reads production as gain / (tau_D tau_L): it is
    handed k x tau_D x tau_L so that its arithmetic uses k itself. It filters nothing."""
    tau_d, _, k, tau_l = point[:4]
    return {"debt_clearance_tau_min": tau_d, "lactate_per_output_deficit": k * tau_d * tau_l,
            "lactate_clearance_tau_min": tau_l}


FACTORIZATION = (
    "P2I-2AC's haemodynamic trajectories (delivery_rel, demand, the GI module's haemostasis minute, the actual flow and "
    "any stop) do not read D, tau_D, the deficit-to-D gain or the D-to-lactate gain: they are simulated once per "
    "scenario and blood input at reserve 2.5 and shared by the three demand factors. The start deficit of minute m is "
    "demand x f - 2.5 x ratio x delivery_rel of the state before, its end deficit the same against the state it ends "
    "in; D follows the corrected core minute (debt_series) and lactate X + k D - X / tau_L (lactate_series). HR and RR "
    "read D but nothing here reads them. Validated on full core runs (else stop): exact at reserve 2.5 for demand 0.9 / "
    "1.0 / 1.1 and intrinsic lower / midpoint / upper; within 1e-9 with identical verdicts at reserve 2.0, 3.0 and the "
    "synthetic reference 1.")


# 3. Context: windows by actual flow, L3 adequacy through 120 -------------------------------------------------------

L3_ADEQUATE = "L3_RESUSCITATION_ADEQUATE_THROUGH_120"
L3_INADEQUATE, L3_LOST = "L3_RESUSCITATION_INADEQUATE", "L3_RESUSCITATION_LOST"
ADEQUACY_RULE = (
    "T* is FD-LAC-04's own restoration trigger (the later of haemostasis and the onset of a deficit-free span of at "
    "least 30 min still in progress at or after haemostasis; adequacy is effective_deficit == 0, ADEQUATE or "
    "COMPENSATED). No T* (no such span; with haemostasis at 60 and the run ending at 120 a T* is always <= 90): "
    "L3_RESUSCITATION_INADEQUATE. A deficit > 0 at any minute from T* to 120: L3_RESUSCITATION_LOST, with the first "
    "such minute. Otherwise L3_RESUSCITATION_ADEQUATE_THROUGH_120, for which FD-LAC-04 and FD-LAC-05 are both "
    "evaluable. Exact comparison, no tolerance; a stopped run is STOPPED_TRAJECTORY.")


def l3_adequacy(context: "Context", settings: dict = SETTINGS) -> dict:
    zeros = (0.0,) * len(context.deficit)
    trigger = fd.restoration_trigger(fd.Trajectory(zeros, zeros, context.trajectory_delivery,
                                                   context.trajectory_demand, context.controlled_at), settings)
    if trigger is None:
        return {"status": L3_INADEQUATE, "onset": None, "lost_at": None}
    if trigger > MINUTES - settings["fd04_sustained_restoration_min"] or len(context.deficit) <= MINUTES:
        return {"status": L3_INADEQUATE, "onset": trigger, "lost_at": None}
    lost = next((m for m in range(trigger, MINUTES + 1) if context.deficit[m] > 0.0), None)
    return {"status": L3_ADEQUATE if lost is None else L3_LOST, "onset": trigger, "lost_at": lost}


class Context(la.Context):
    """P2I-2AC's context (windows from the actual flow), with this package's L3 adequacy and the end deficit of every
    minute the corrected D reads."""

    __slots__ = ("end_deficit",)

    def __init__(self, delivery, demand, bleed, haemostasis, stop, reserve=RESERVE, settings=SETTINGS):
        super().__init__(delivery, demand, bleed, haemostasis, stop, reserve, settings)
        self.end_deficit = self.deficit[1:]
        self.adequacy = None if haemostasis is None else l3_adequacy(self, settings)


def context_of(haemodynamic: dict, ratio: float, factor: float = 1.0) -> Context:
    demand = haemodynamic["demand"] if factor == 1.0 else [factor * x for x in haemodynamic["demand"]]
    return Context([ratio * d for d in haemodynamic["delivery_rel"]], demand, haemodynamic["bleed"],
                   haemodynamic["controlled_at"], haemodynamic["stop"])


RESIDUAL = la.RESIDUAL
RULES = {**la.RULES, "L3_RESUSCITATION_ADEQUACY": ADEQUACY_RULE,
         "debt": "D: + g x deficit when a minute starts in a deficit; - D / tau_D only across a minute without deficit "
                 "at its start and its end; unchanged across a crossing into a deficit",
         "lactate": "X + k x D(minute before) - X / tau_L, k the independent D-to-lactate gain"}
fd_lac_06_run = la.fd_lac_06_run


def fd_lac_04_05(lactate: list, debt: list, context: Context, point: tuple, case: str) -> tuple:
    trajectory = context.trajectory(lactate, debt)
    response = fd.fd_lac_04(trajectory, SETTINGS)
    residual = fd.fd_lac_05(trajectory, response["trigger"], memory_kinetics(point), lactate[0], SETTINGS, case)
    return response, residual


# 4. The sequential filter at one demand factor -----------------------------------------------------------------------

DEMAND_FACTORS = la.DEMAND_FACTORS
PRIMARY_DEMAND = la.PRIMARY_DEMAND
FILTER_ORDER = (
    (L1, ("FD-LAC-02/03", "FD-LAC-01", "FD-LAC-06")),
    (L3, (L3_INADEQUATE, L3_LOST, "FD-LAC-04", "FD-LAC-05", "FD-LAC-06", RESIDUAL)),
    (L2, ("FD-LAC-06",)),
)
COST_RATIONALE = ("Fixed by cost before any count, as P2I-2AB and P2I-2AC: L1 (one trajectory per P1 set and case), "
                  "then L3 (one per P3 set), then L2 (one per P1 set and crystalloid point, the most). Inside L3 the "
                  "first failure is read in the faculty's order: adequacy (INADEQUATE, then LOST), FD-LAC-04, "
                  "FD-LAC-05, FD-LAC-06 with active bleeding, FD-LAC-06 with residual bleeding (57m before 72f in "
                  "each); every constraint is evaluated for both cases. The filter runs once per demand factor on the "
                  "same haemodynamic trajectories; 1.0 first, and only 1.0 makes the region.")
BITS = {scenario: tuple((name, case) for name in names for case in CASES) + ((STOPPED, None),)
        for scenario, names in FILTER_ORDER}
REJECTION_RULE = lr.REJECTION_RULE


def _series(haemodynamic: dict, arrival: dict, wanted, factor: float, cache: dict):
    contexts, debts = cache.setdefault("contexts", {}), cache.setdefault("debts", {})
    for index in wanted:
        tau_d, gain_k, k, tau_l, excess, debt, delivery = LAMBDAS[index]
        context = contexts.get(delivery)
        if context is None:
            context = contexts[delivery] = context_of(haemodynamic, arrival["ratio"][delivery], factor)
        key = (delivery, debt, tau_d, gain_k)
        series = debts.get(key)
        if series is None:
            series = debts[key] = debt_series(context.debt_input, context.end_deficit, arrival["debt"][debt], tau_d,
                                              gain_k)
        lactate = lactate_series(series, arrival["excess"][excess], k, tau_l, arrival["baseline"][excess],
                                 arrival["floor"])
        yield index, lactate, series, context


def _bit(scenario: str, name: str, case: str | None) -> int:
    return 1 << BITS[scenario].index((name, case))


def _l1_unit(task: tuple) -> tuple:
    unit, haemodynamic, arrivals, wanted, factor = task
    masks = dict.fromkeys(wanted, 0)
    for case in CASES:
        if haemodynamic[case]["stop"] is not None:
            masks = {index: mask | _bit(L1, STOPPED, None) for index, mask in masks.items()}
            continue
        for index, lactate, debt, context in _series(haemodynamic[case], arrivals[case], wanted, factor, {}):
            envelope = fd.fd_lac_envelope(context.trajectory(lactate, debt), case, SETTINGS)["passes"]
            masks[index] |= 0 if envelope else _bit(L1, "FD-LAC-02/03", case)
            masks[index] |= 0 if lr.fd_lac_01(lactate, context)["passes"] else _bit(L1, "FD-LAC-01", case)
            masks[index] |= 0 if fd_lac_06_run(lactate, context)["passes"] else _bit(L1, "FD-LAC-06", case)
    return unit, masks


def _l3_unit(task: tuple) -> tuple:
    unit, haemodynamic, arrivals, wanted, factor = task
    masks = dict.fromkeys(wanted, 0)
    for case in CASES:
        if haemodynamic[case]["stop"] is not None or haemodynamic[case]["controlled_at"] is None:
            masks = {index: mask | _bit(L3, STOPPED, None) for index, mask in masks.items()}
            continue
        for index, lactate, debt, context in _series(haemodynamic[case], arrivals[case], wanted, factor, {}):
            status = context.adequacy["status"]
            response, residual = fd_lac_04_05(lactate, debt, context, LAMBDAS[index], case)
            sixth = fd_lac_06_run(lactate, context)
            masks[index] |= _bit(L3, L3_INADEQUATE, case) if status == L3_INADEQUATE else 0
            masks[index] |= _bit(L3, L3_LOST, case) if status == L3_LOST else 0
            masks[index] |= 0 if response["status"] in (fd.PASS, fd.ALREADY_NORMALIZED) else (
                _bit(L3, "FD-LAC-04", case) if response["status"] == fd.FAIL else 0)
            masks[index] |= _bit(L3, "FD-LAC-05", case) if residual["status"] == fd.FAIL else 0
            masks[index] |= _bit(L3, "FD-LAC-06", case) if sixth["active"] else 0
            masks[index] |= _bit(L3, RESIDUAL, case) if sixth["residual"] else 0
    return unit, masks


def _l2_unit(task: tuple) -> tuple:
    unit, haemodynamic, arrivals, wanted, factor = task
    masks = dict.fromkeys(wanted, 0)
    for case in CASES:
        if haemodynamic[case]["stop"] is not None:
            masks = {index: mask | _bit(L2, STOPPED, None) for index, mask in masks.items()}
            continue
        for index, lactate, _, context in _series(haemodynamic[case], arrivals[case], wanted, factor, {}):
            masks[index] |= 0 if fd_lac_06_run(lactate, context)["passes"] else _bit(L2, "FD-LAC-06", case)
    return unit, masks


def _label(scenario: str, bit: int) -> str:
    name, case = BITS[scenario][bit]
    return name if case is None else f"{name} {case}"


class Stage(la.Stage):
    """P2I-2AC's candidate-weighted stage accounting over this package's bits."""

    def add(self, mask: int, weight: int) -> None:
        self.entering += weight
        self.units += 1
        if not mask:
            return
        self.rejected += weight
        self.units_rejected += 1
        bits = [bit for bit in range(len(BITS[self.scenario])) if mask >> bit & 1]
        first = _label(self.scenario, bits[0])
        self.first[first] = self.first.get(first, 0) + weight
        for bit in bits:
            name = _label(self.scenario, bit)
            self.any[name] = self.any.get(name, 0) + weight
        names = {BITS[self.scenario][bit][0] for bit in bits}
        if len(names) == 1:
            name = names.pop()
            self.only[name] = self.only.get(name, 0) + weight

    def report(self) -> dict:
        order = [_label(self.scenario, bit) for bit in range(len(BITS[self.scenario]))]
        names = list(dict.fromkeys(name for name, _ in BITS[self.scenario]))
        return {"scenario": self.scenario, "entering": self.entering, "rejected": self.rejected,
                "survivors": self.entering - self.rejected, SIMULATION_REJECTION: self.rejected, ANALYTIC_REJECTION: 0,
                "units_evaluated": self.units, "units_rejected": self.units_rejected,
                "first_failure": {n: self.first[n] for n in order if n in self.first},
                "any_failure": {n: self.any[n] for n in order if n in self.any},
                "only_failure": {n: self.only[n] for n in names if n in self.only}}


haemodynamic_tasks = la.haemodynamic_tasks
haemodynamics = la.haemodynamics


def filter_(source: dict, support: list, arrivals: dict, tasks: dict, store: dict, factor: float, map_=map) -> dict:
    """L1, then L3, then L2 at one demand factor; a candidate is (P3 set, crystalloid point, lactate side)."""
    p1, p3, children = source["p1"], source["p3"], source["children"]
    n_lambda, n_support = len(LAMBDAS), len(support)
    stages = {s: Stage(s) for s in SCENARIOS}
    evaluated = {s: 0 for s in SCENARIOS}

    def trajectories(scenario, unit):
        return {case: store[tasks[(scenario, unit, case)]] for case in CASES}

    passing = {}
    for i, masks in map_(_l1_unit, [(i, trajectories(L1, i), arrivals, range(n_lambda), factor)
                                    for i in range(len(p1))]):
        evaluated[L1] += len(masks)
        weight = len(children[i]) * n_support
        passing[i] = []
        for index in range(n_lambda):
            stages[L1].add(masks[index], weight)
            if not masks[index]:
                passing[i].append(index)
    alive = [i for i in range(len(p1)) if passing[i]]
    r_ok = {}
    for q, masks in map_(_l3_unit, [(q, trajectories(L3, q), arrivals, passing[i], factor)
                                    for i in alive for q in children[i]]):
        evaluated[L3] += len(masks)
        i = p3[q]["p1"]
        for index in passing[i]:
            stages[L3].add(masks[index], n_support)
            if not masks[index]:
                r_ok.setdefault((i, index), []).append(q)
    wanted = {i: [index for index in passing[i] if (i, index) in r_ok] for i in alive}
    alive = [i for i in alive if wanted[i]]
    d_ok = {}
    for (i, d), masks in map_(_l2_unit, [((i, d), trajectories(L2, (i, d)), arrivals, wanted[i], factor)
                                         for i in alive for d in range(n_support)]):
        evaluated[L2] += len(masks)
        for index in wanted[i]:
            stages[L2].add(masks[index], len(r_ok[(i, index)]))
            if not masks[index]:
                d_ok.setdefault((i, index), []).append(d)
    units = sorted((i, index, tuple(r_ok[(i, index)]), tuple(d_ok[(i, index)])) for i, index in d_ok)
    total = sum(len(children[i]) for i in range(len(p1))) * n_support * n_lambda
    return {"factor": factor, "stages": [stages[s].report() for s, _ in FILTER_ORDER], "candidates": total,
            "survivors": sum(len(r) * len(d) for _, _, r, d in units), "units": units,
            "post_processed_units": evaluated}


def candidate_ids(units: list, n_support: int) -> set:
    n_lambda = len(LAMBDAS)
    return {(q * n_support + d) * n_lambda + index for _, index, r, ds in units for q in r for d in ds}


ROBUST, SENSITIVE, INCOMPATIBLE = "ROBUST_ACROSS_DEMAND", "DEMAND_SENSITIVE", "DEMAND_INCOMPATIBLE"
DEMAND_RULE = la.DEMAND_RULE.replace("ROBUST:", "ROBUST_ACROSS_DEMAND:").replace(
    "DEMAND-SENSITIVE:", "DEMAND_SENSITIVE:").replace("DEMAND-INCOMPATIBLE:", "DEMAND_INCOMPATIBLE:")


def demand_layer(filtered: dict, n_support: int, total: int) -> dict:
    ids = {factor: candidate_ids(filtered[factor]["units"], n_support) for factor in DEMAND_FACTORS}
    patterns = {}
    union = set().union(*ids.values())
    for candidate in union:
        key = "+".join(f"{factor:g}" for factor in sorted(DEMAND_FACTORS) if candidate in ids[factor])
        patterns[key] = patterns.get(key, 0) + 1
    robust = patterns.get("+".join(f"{f:g}" for f in sorted(DEMAND_FACTORS)), 0)
    primary = ids[PRIMARY_DEMAND]
    everywhere = sum(1 for c in primary if all(c in ids[f] for f in DEMAND_FACTORS))
    return {"rule": DEMAND_RULE, "survivors": {f"{f:g}": len(ids[f]) for f in DEMAND_FACTORS},
            "classes": {ROBUST: robust, SENSITIVE: len(union) - robust, INCOMPATIBLE: total - len(union)},
            "patterns": dict(sorted(patterns.items())),
            "final_region": {ROBUST: everywhere, SENSITIVE: len(primary) - everywhere}, "_ids": ids}


# 5. Validation of the factorization ----------------------------------------------------------------------------------

VALIDATION_RULE = la.VALIDATION_RULE
RHO_BAND, RHO_SYNTHETIC_REFERENCE, RHO_STATUS = la.RHO_BAND, la.RHO_SYNTHETIC_REFERENCE, la.RHO_STATUS
TOLERANCE = la.TOLERANCE


def validation_sample(source: dict, support: list) -> list[dict]:
    """P2I-2AC's rule on this lactate side: per rate the first, middle and last P3 set; indices 0, n/4, n/2, 3n/4, n-1
    and the canonical point; L1, L3 and L2 at the first and last crystalloid point; both cases; on the canonical
    point demand 0.9 / 1.1, intrinsic lower / upper, reserve 2.0, 3.0 and the synthetic reference 1."""
    p3 = source["p3"]
    sets = []
    for rate in lr.LACTATE_RATES:
        members = [q for q, entry in enumerate(p3) if entry["rate"] == rate]
        if members:
            sets.extend(dict.fromkeys((members[0], members[len(members) // 2], members[-1])))
    n, canonical = len(LAMBDAS), LAMBDAS.index(CANONICAL)
    points = list(dict.fromkeys((0, n // 4, n // 2, 3 * n // 4, n - 1, canonical)))
    bags = sorted({0, len(support) - 1})
    out = []
    for q in sets:
        for case in CASES:
            for index in points:
                for scenario, d in [(L1, None), (L3, None)] + [(L2, d) for d in bags]:
                    variants = [(RESERVE, "midpoint", PRIMARY_DEMAND)]
                    if index == canonical:
                        variants += ([(RESERVE, "midpoint", f) for f in DEMAND_FACTORS if f != PRIMARY_DEMAND]
                                     + [(RESERVE, level, PRIMARY_DEMAND) for level in ("lower", "upper")]
                                     + [(r, "midpoint", PRIMARY_DEMAND) for r in (*RHO_BAND, RHO_SYNTHETIC_REFERENCE)])
                    out.extend({"q": q, "case": case, "lambda": index, "scenario": scenario, "support": d,
                                "reserve": r, "intrinsic": n_, "demand": f} for r, n_, f in variants)
    return out


def full_run(entry: dict, case: str, scenario: str, point: tuple, bag: dict | None = None, reserve: float = RESERVE,
             intrinsic: str = "midpoint", factor: float = PRIMARY_DEMAND) -> dict:
    """The full core run of one blood entry and lactate-side point (no factorization)."""
    tau_d, gain_k, k, tau_l, excess, debt, delivery = point
    values = {**lr.blood_values(entry, case, bag), "reserve": reserve}
    _, profile, full = blood_anchors.setup(case, **values)
    case_values = calibration.case_values(case, calibration.GICandidate({}, excess=excess, debt=debt,
                                                                        delivery=delivery, intrinsic=intrinsic))
    case_values["preload_fraction"] = full[bc.POS]
    case_values["arrival_delivery_ratio"] /= reserve
    case_values["metabolic_demand_baseline"] *= factor
    anchors = gi_reference.candidate_anchors(case, case_values)
    profile = replace(profile, debt_clearance_tau_min=tau_d, debt_per_delivery_deficit=gain_k,
                      debt_to_lactate_gain=k, lactate_clearance_tau_min=tau_l)
    states, stop = blood_anchors.trajectory(anchors, lr.scenario_items(case, scenario, full), MINUTES, profile)
    out = {key: [] for key in ("lactate", "D", "deficit", "demand", "delivery", "output", "views")}
    for state in states:
        view = derive(state, anchors, profile)
        delivery_ = effective_delivery(view.delivery_rel, anchors)
        out["lactate"].append(view.lactate)
        out["D"].append(state.D)
        out["deficit"].append(effective_oxygen_deficit(state.aux.oxygen_demand, delivery_, reserve))
        out["demand"].append(state.aux.oxygen_demand)
        out["delivery"].append(delivery_)
        out["output"].append(view.output_rel)
        out["views"].append((state, view))
    shed = [state.blood.shed_ml for state in states]
    flow = [after - before for before, after in zip(shed, shed[1:])]
    out.update({"bleed": (flow[:1] or [0.0]) + flow, "controlled_at": lr.controlled_at(states[-1]), "stop": stop,
                "anchors": anchors, "profile": profile})
    return out


def verdicts(case: str, scenario: str, lactate: list, debt: list, context: Context, point: tuple) -> dict:
    sixth = fd_lac_06_run(lactate, context)
    out = {"FD-LAC-06": not sixth["active"], RESIDUAL: not sixth["residual"]}
    if scenario == L1:
        out["FD-LAC-02/03"] = fd.fd_lac_envelope(context.trajectory(lactate, debt), case, SETTINGS)["passes"]
        out["FD-LAC-01"] = lr.fd_lac_01(lactate, context)["status"]
    if scenario == L3:
        response, residual = fd_lac_04_05(lactate, debt, context, point, case)
        out.update({"FD-LAC-04": response["status"], "FD-LAC-05": residual["status"],
                    "L3 adequacy": context.adequacy["status"], "onset": context.adequacy["onset"],
                    "lost_at": context.adequacy["lost_at"]})
    return out


def factorized(haemodynamic: dict, arrival: dict, point: tuple, factor: float = PRIMARY_DEMAND) -> tuple:
    tau_d, gain_k, k, tau_l, excess, debt, delivery = point
    context = context_of(haemodynamic, arrival["ratio"][delivery], factor)
    series = debt_series(context.debt_input, context.end_deficit, arrival["debt"][debt], tau_d, gain_k)
    lactate = lactate_series(series, arrival["excess"][excess], k, tau_l, arrival["baseline"][excess],
                             arrival["floor"])
    return lactate, series, context


def debt_falls_outside_adequate_minutes(debt: list, context: Context) -> list:
    """Minutes in which D fell without a deficit-free start and end: must be none."""
    return [m + 1 for m, (start, end) in enumerate(zip(context.debt_input, context.end_deficit))
            if debt[m + 1] < debt[m] and not (start == 0.0 and end == 0.0)]


def compare(full: dict, factorized_: tuple, haemodynamic: dict, case: str, scenario: str, point: tuple,
            reserve: float) -> dict:
    lactate, series, context = factorized_
    own = Context(full["delivery"], full["demand"], full["bleed"], full["controlled_at"], full["stop"], reserve)
    gaps = {"lactate": lr._gap(lactate, full["lactate"]), "D": lr._gap(series, full["D"]),
            "deficit": lr._gap(context.deficit, full["deficit"]), "bleed": lr._gap(context.bleed, full["bleed"])}
    exact = (lactate == full["lactate"] and series == full["D"] and context.deficit == full["deficit"]
             and context.bleed == full["bleed"])
    events = full["controlled_at"] == haemodynamic["controlled_at"] and full["stop"] == haemodynamic["stop"]
    mine = verdicts(case, scenario, lactate, series, context, point)
    theirs = verdicts(case, scenario, full["lactate"], full["D"], own, point)
    coherent = not debt_falls_outside_adequate_minutes(full["D"], own)
    strict = reserve == RESERVE
    agrees = (events and mine == theirs and coherent and gaps["bleed"] == 0.0
              and (exact if strict else max(gaps.values()) <= TOLERANCE))
    return {"exact": exact, "gaps": gaps, "events": events, "verdicts": mine, "verdicts_equal": mine == theirs,
            "debt_coherent": coherent, "agrees": agrees}


def _validate_one(task: tuple) -> dict:
    item, entry, bag, haemodynamic, arrival = task
    case, scenario, point = item["case"], item["scenario"], LAMBDAS[item["lambda"]]
    full = full_run(entry, case, scenario, point, bag, item["reserve"], item["intrinsic"], item["demand"])
    return {**item, **compare(full, factorized(haemodynamic, arrival, point, item["demand"]), haemodynamic, case,
                              scenario, point, item["reserve"])}


def validate(source: dict, support: list, arrivals: dict, tasks: dict, store: dict, map_=map) -> dict:
    work = []
    for item in validation_sample(source, support):
        entry = source["p3"][item["q"]]
        unit = (item["q"] if item["scenario"] == L3 else
                entry["p1"] if item["scenario"] == L1 else (entry["p1"], item["support"]))
        bag = support[item["support"]]["bag"] if item["scenario"] == L2 else None
        work.append((item, entry, bag, store[tasks[(item["scenario"], unit, item["case"])]], arrivals[item["case"]]))
    results = list(map_(_validate_one, work))
    seen = {}
    for result in results:
        for name, value in result.pop("verdicts").items():
            if name not in ("onset", "lost_at"):
                label = f"{result['scenario']} {name} {value}"
                seen[label] = seen.get(label, 0) + 1
    primary = [r for r in results if r["reserve"] == RESERVE]
    return {"rule": VALIDATION_RULE.replace("P2I-2AB's sample", "P2I-2AC's sample rule on this lactate side"),
            "runs": len(results), "agree": all(r["agrees"] for r in results),
            "exact_at_reserve_2_5": all(r["exact"] for r in primary),
            "max_gap_other_reserves": max((max(r["gaps"].values()) for r in results if r["reserve"] != RESERVE),
                                          default=0.0),
            "reserves": sorted({r["reserve"] for r in results}), "demands": sorted({r["demand"] for r in results}),
            "debt_coherent": all(r["debt_coherent"] for r in results),
            "verdicts_seen": dict(sorted(seen.items())), "disagreements": [r for r in results if not r["agrees"]],
            "sample": results}


# 6. Coupling and crossing checks ------------------------------------------------------------------------------------

def coupling_check() -> dict:
    """D -> lactate production no longer reads tau_D: (a) the core's lactate step names only its own gain; (b) on a
    synthetic run whose D only accrues (an arrival at the critical delivery, the pump falling), tau_D 30 / 60 / 120 give
    the same D and the same lactate; (c) the lactate side crosses every tau_D with every D-to-lactate gain."""
    body = inspect.getsource(derived.lactate_after_minute).split('"""')[-1]
    reads = {name: name in body for name in ("debt_to_lactate_gain", "debt_clearance_tau_min",
                                             "lactate_per_output_deficit")}
    neutral = calibration.NEUTRAL
    arrival = replace(neutral, arrival_oxygen_debt=20.0,
                      declared={**dict(neutral.declared), "arrival_oxygen_debt": "synthetic_probe"})
    runs = [core_run(arrival, (Drift("pump", "P", 0, 90, -0.005),), 90,
                     replace(DEFAULT_PROFILE, debt_clearance_tau_min=tau)).states for tau in (30.0, 60.0, 120.0)]
    same = all([s.aux.lactate_excess_mmol_l for s in other] == [s.aux.lactate_excess_mmol_l for s in runs[0]]
               and [s.D for s in other] == [s.D for s in runs[0]] for other in runs[1:])
    pairs = {(point[0], point[2]) for point in LAMBDAS}
    crossed = len(pairs) == len(kinetic_points()["debt_clearance_tau_min"]) * len(K_LD)
    return {"reads": reads, "tau_d_invariant_probe": same, "cartesian_tau_d_by_gain": crossed,
            "independent": reads["debt_to_lactate_gain"] and not reads["debt_clearance_tau_min"]
            and not reads["lactate_per_output_deficit"] and same and crossed}


CROSSING_RULE = ("P2I-2AC's region re-read (never refiltered): for each surviving unit, the L1 runs of both cases at its "
                 "arrival delivery and debt level, tau_D and g; a critical minute below the arrival D is a minute whose "
                 "end deficit is > 0 with D below its arrival value and no minute before it that started and ended "
                 "without deficit. Counted with P2I-2AC's D (repayment from the start deficit alone) and with "
                 "P2I-2AD's D; a candidate is affected when either case has two or more such minutes.")


def _below_arrival(debt: list, context: Context) -> int:
    count = 0
    for m in range(1, len(debt)):
        start, end = context.debt_input[m - 1], context.end_deficit[m - 1]
        if start == 0.0 and end == 0.0:
            break
        if end > 0.0 and debt[m] < debt[0]:
            count += 1
    return count


def _crossing_unit(task: tuple) -> tuple:
    i, haemodynamic, arrivals, wanted = task
    out = {}
    for case in CASES:
        cache = {}
        for index in wanted:
            tau_d, gain_k, _, _, _, debt_level, delivery = lr.LAMBDAS[index]
            key = (delivery, debt_level, tau_d, gain_k)
            if key not in cache:
                context = context_of(haemodynamic[case], arrivals[case]["ratio"][delivery])
                d0 = arrivals[case]["debt"][debt_level]
                old = la.debt_series(context.debt_input, d0, tau_d, gain_k)
                new = debt_series(context.debt_input, context.end_deficit, d0, tau_d, gain_k)
                cache[key] = (_below_arrival(old, context), _below_arrival(new, context))
            out[(index, case)] = cache[key]
    return i, out


def crossing_audit(source: dict, arrivals: dict, tasks: dict, store: dict, map_=map) -> dict:
    record = json.loads(P2I2AC_RECORD.read_text(encoding="utf-8"))
    if record["freeze_digest"] != P2I2AC_DIGEST or record["region"]["digest"] != P2I2AC_REGION_DIGEST:
        raise AssertionError("the P2I-2AC record is not the committed one")
    units = record["region"]["inline"]
    by_p1 = {}
    for i, index, _, _ in units:
        by_p1.setdefault(i, set()).add(index)
    readings = dict(map_(_crossing_unit, [(i, {c: store[tasks[(L1, i, c)]] for c in CASES}, arrivals, sorted(idx))
                                          for i, idx in sorted(by_p1.items())]))
    counts = {"region": 0, "upper_delivery": 0, "affected_old": 0, "affected_new": 0, "upper_affected_old": 0,
              "upper_affected_new": 0, "max_minutes_old": 0, "max_minutes_new": 0}
    for i, index, r, d in units:
        weight = len(r) * len(d)
        upper = lr.LAMBDAS[index][6] == "upper"
        old = [readings[i][(index, case)][0] for case in CASES]
        new = [readings[i][(index, case)][1] for case in CASES]
        counts["region"] += weight
        counts["upper_delivery"] += weight * upper
        counts["affected_old"] += weight * (max(old) >= 2)
        counts["affected_new"] += weight * (max(new) >= 2)
        counts["upper_affected_old"] += weight * (upper and max(old) >= 2)
        counts["upper_affected_new"] += weight * (upper and max(new) >= 2)
        counts["max_minutes_old"] = max(counts["max_minutes_old"], max(old))
        counts["max_minutes_new"] = max(counts["max_minutes_new"], max(new))
    return {"rule": CROSSING_RULE, "p2i2ac_region_digest": P2I2AC_REGION_DIGEST, **counts}


# 7. The final region: statistics, identifiability, representatives ------------------------------------------------

def _survivor_l1(task: tuple) -> tuple:
    unit, haemodynamic, arrivals, wanted = task
    out = {}
    for case in CASES:
        for index, lactate, _, context in _series(haemodynamic[case], arrivals[case], wanted, PRIMARY_DEMAND, {}):
            out[(index, case)] = {"L60": lactate[60], "fd01": lr.fd_lac_01(lactate, context)["status"],
                                  "recovering": len(fd_lac_06_run(lactate, context)["recovering"])}
    return unit, out


def _survivor_l3(task: tuple) -> tuple:
    unit, haemodynamic, arrivals, wanted = task
    out = {}
    for case in CASES:
        for index, lactate, debt, context in _series(haemodynamic[case], arrivals[case], wanted, PRIMARY_DEMAND, {}):
            response, residual = fd_lac_04_05(lactate, debt, context, LAMBDAS[index], case)
            trigger = response["trigger"]
            out[(index, case)] = {"fd04": response["status"], "reduction": response.get("reduction_at_window"),
                                  "fd05": residual["status"], "L120": lactate[120], "trigger": trigger,
                                  "at_trigger": response.get("at_trigger"), "adequacy": context.adequacy["status"],
                                  "onset": context.adequacy["onset"], "D120": debt[120],
                                  "trigger_is_onset": trigger == context.adequacy["onset"],
                                  "recovering": len(fd_lac_06_run(lactate, context)["recovering"]),
                                  "debt_incoherent": bool(debt_falls_outside_adequate_minutes(debt, context))}
    return unit, out


def _count(table: dict, key, weight: int) -> None:
    table[str(key)] = table.get(str(key), 0) + weight


def survivor_statistics(source: dict, support: list, arrivals: dict, tasks: dict, store: dict, filtered: dict,
                        map_=map) -> dict:
    units = filtered["units"]
    by_p1, by_p3 = {}, {}
    for i, index, r, _ in units:
        by_p1.setdefault(i, []).append(index)
        for q in r:
            by_p3.setdefault(q, []).append(index)
    l1 = dict(map_(_survivor_l1, [(i, {c: store[tasks[(L1, i, c)]] for c in CASES}, arrivals, idx)
                                  for i, idx in sorted(by_p1.items())]))
    l3 = dict(map_(_survivor_l3, [(q, {c: store[tasks[(L3, q, c)]] for c in CASES}, arrivals, idx)
                                  for q, idx in sorted(by_p3.items())]))
    summaries = {name: {case: lr.Summary() for case in CASES} for name in ("L60", "L120", "D120", "reduction",
                                                                          "at_trigger")}
    tables = {name: {case: {} for case in CASES} for name in ("fd01_status", "fd04_status", "fd05_status",
                                                              "adequacy", "trigger_minute")}
    sensitivity = {f"{t:g}": 0 for t in lr.FD04_THRESHOLDS}
    evaluated_both = trigger_is_onset = incoherent = 0
    for i, index, r, d in units:
        n_r, n_d = len(r), len(d)
        for case in CASES:
            item = l1[i][(index, case)]
            summaries["L60"][case].add(item["L60"], n_r * n_d)
            _count(tables["fd01_status"][case], item["fd01"], n_r * n_d)
        for q in r:
            items = {case: l3[q][(index, case)] for case in CASES}
            for case, item in items.items():
                _count(tables["fd04_status"][case], item["fd04"], n_d)
                _count(tables["fd05_status"][case], item["fd05"], n_d)
                _count(tables["adequacy"][case], item["adequacy"], n_d)
                _count(tables["trigger_minute"][case], item["trigger"], n_d)
                summaries["L120"][case].add(item["L120"], n_d)
                summaries["D120"][case].add(item["D120"], n_d)
                if item["reduction"] is not None:
                    summaries["reduction"][case].add(item["reduction"], n_d)
                if item["at_trigger"] is not None:
                    summaries["at_trigger"][case].add(item["at_trigger"], n_d)
            for threshold in lr.FD04_THRESHOLDS:
                if all(item["fd04"] != fd.PASS or item["reduction"] >= threshold for item in items.values()):
                    sensitivity[f"{threshold:g}"] += n_d
            if all(item["fd04"] in (fd.PASS, fd.ALREADY_NORMALIZED) and item["fd05"] == fd.PASS
                   for item in items.values()):
                evaluated_both += n_d
            trigger_is_onset += n_d * all(item["trigger_is_onset"] for item in items.values())
            incoherent += n_d * any(item["debt_incoherent"] for item in items.values())
    return {**{name: {c: summaries[name][c].report() for c in CASES} for name in ("L60", "L120", "D120")},
            "fd04_reduction": {c: summaries["reduction"][c].report() for c in CASES},
            "fd04_at_trigger": {c: summaries["at_trigger"][c].report() for c in CASES},
            **tables, "fd04_and_05_evaluated_in_both_cases": evaluated_both,
            "trigger_is_adequacy_onset": trigger_is_onset, "debt_incoherent_l3": incoherent,
            "fd04_sensitivity": {"thresholds": sensitivity, "survivors": filtered["survivors"],
                                 "note": "diagnostic only: survivors that would also pass FD-LAC-04 with the fall "
                                         "required at the threshold; never filters"},
            "_l60": {(i, index): {case: l1[i][(index, case)]["L60"] for case in CASES} for i, index, _, _ in units}}


IDENTIFIABILITY_RULE = la.IDENTIFIABILITY_RULE + (
    " P2I-2AD: lactate reads (g, k, D0) only as k x g and k x D0 (D is linear in D0 and g given the deficit path and "
    "tau_D), so g, k and the arrival debt level are NON_IDENTIFIABLE_SEPARATELY; the products are reported as their "
    "own dimensions. Set beside P2I-2AC on the dimensions both have.")
STRUCTURAL = {"debt_per_delivery_deficit": "only k x g and k x D0 reach lactate",
              "debt_to_lactate_gain": "only k x g and k x D0 reach lactate",
              "arrival_oxygen_debt": "only k x D0 reaches lactate"}


def _dimension_values(source: dict, support: list, arrivals: dict):
    blood, crystalloid, _ = la._dimension_values(source, support)

    def lactate(index):
        tau_d, gain_k, k, tau_l, excess, debt, delivery = LAMBDAS[index]
        return [("debt_clearance_tau_min", tau_d), ("debt_per_delivery_deficit", gain_k),
                ("debt_to_lactate_gain", k), ("lactate_clearance_tau_min", tau_l),
                ("arrival_lactate_excess", excess), ("arrival_pair", f"{debt}|{delivery}"),
                ("arrival_oxygen_debt", debt), ("arrival_delivery_ratio", delivery), ("k x g", k * gain_k),
                ("k x D0", k * arrivals[CASES[0]]["debt"][debt])]
    return blood, crystalloid, lactate


def _key(value) -> str:
    return f"{value:.6g}" if isinstance(value, float) else str(value)


def identifiability(source: dict, support: list, arrivals: dict, filtered: dict, demand: dict, previous: dict) -> dict:
    blood, crystalloid, lactate = _dimension_values(source, support, arrivals)
    n_lambda, n_support, n_p3 = len(LAMBDAS), len(support), len(source["p3"])
    explored, surviving = {}, {}

    def add(table, pairs, weight):
        for name, value in pairs:
            key = _key(value)
            table.setdefault(name, {})
            table[name][key] = table[name].get(key, 0) + weight

    for q in range(n_p3):
        add(explored, blood(q), n_support * n_lambda)
    for k in range(n_support):
        add(explored, crystalloid(k), n_p3 * n_lambda)
    for index in range(n_lambda):
        add(explored, lactate(index), n_p3 * n_support)
    for _, index, r, d in filtered["units"]:
        for q in r:
            add(surviving, blood(q), len(d))
        for k in d:
            add(surviving, crystalloid(k), len(r))
        add(surviving, lactate(index), len(r) * len(d))
    total = n_p3 * n_support * n_lambda
    explored["demand_factor"] = {f"{f:g}": total for f in sorted(DEMAND_FACTORS)}
    surviving["demand_factor"] = {key: value for key, value in demand["survivors"].items() if value}
    out = {}
    for name in explored:
        values = sorted(explored[name], key=lr._order)
        left = sorted((v for v, n in surviving.get(name, {}).items() if n), key=lr._order)
        if name in STRUCTURAL:
            status = bc.SEPARATELY
        elif len(values) == 1:
            status = "NOT_VARIED"
        elif not left:
            status = "NOT_ASSESSABLE (no survivors)"
        elif len(left) == 1:
            status = bc.WELL
        elif len(left) < len(values):
            status = bc.PARTIAL
        else:
            status = bc.POOR
        edge = None
        if len(values) > 1 and left and all(lr._is_number(v) or v in LEVELS for v in values):
            edge = be.edge_status([lr._order(v) for v in values], [lr._order(v) for v in left])
        before = previous.get(name)
        change = None
        if before is not None:
            change = ("NARROWER" if len(left) < len(before["surviving"]) else
                      "WIDER" if len(left) > len(before["surviving"]) else "SAME")
        out[name] = {"explored": values, "surviving": left, "status": status, "edge": edge,
                     "structural": STRUCTURAL.get(name), "surviving_weight": surviving.get(name, {}),
                     "p2i2ac": None if before is None else {"status": before["status"],
                                                            "surviving": before["surviving"]},
                     "change": change}
    return {"rule": IDENTIFIABILITY_RULE, "dimensions": out, "parameter_semantics": PARAMETER_SEMANTICS,
            "rho": {"status": RHO_STATUS, "band": list(RHO_BAND), "representative": RESERVE,
                    "synthetic_reference": RHO_SYNTHETIC_REFERENCE}}


REPRESENTATIVE_RULE = lr.REPRESENTATIVE_RULE
FLAG_RULES = lr.FLAG_RULES
DEBT_CHECK_RULE = ("Per minute of each representative run: D falls only across a minute with no deficit at its start "
                   "and its end (none otherwise); no critical minute below the arrival D before the first such "
                   "minute; L3 keeps the deficit at 0 from T* to 120.")


def debt_checks(full: dict) -> dict:
    own = Context(full["delivery"], full["demand"], full["bleed"], full["controlled_at"], full["stop"],
                  full["profile"].oxygen_extraction_reserve)
    out = {"falls_outside_adequate_minutes": debt_falls_outside_adequate_minutes(full["D"], own),
           "critical_minutes_below_arrival": _below_arrival(full["D"], own)}
    if own.adequacy is not None:
        out["l3_adequacy"] = own.adequacy
    return out


def review(source: dict, support: list, arrivals: dict, tasks: dict, store: dict, picks: dict) -> dict:
    out = {}
    for tag, pick in picks.items():
        entry = source["p3"][pick["p3"]]
        item = {"pick": pick, "lambda": lambda_label(pick["lambda"]), "blood": {
            "rate": entry["rate"], **{n: entry[n] for n in lr.P3_DIMS}, "positions": entry["positions"]},
            "crystalloid": support[pick["support"]]["key"], "runs": {}}
        for case in CASES:
            for scenario in (L1, L3):
                full = full_run(entry, case, scenario, LAMBDAS[pick["lambda"]])
                unit = entry["p1"] if scenario == L1 else pick["p3"]
                lactate, debt, _ = factorized(store[tasks[(scenario, unit, case)]], arrivals[case],
                                              LAMBDAS[pick["lambda"]])
                rows = []
                for minute in TIMES:
                    if minute >= len(full["views"]):
                        continue
                    state, view = full["views"][minute]
                    balance = oxygen_balance(full["delivery"][minute], full["demand"][minute],
                                             full["profile"].oxygen_extraction_reserve)
                    rows.append({"minute": minute, "output_rel": view.output_rel, "do2": full["delivery"][minute],
                                 "demand": full["demand"][minute], "effective_deficit": full["deficit"][minute],
                                 "D": full["D"][minute], "lactate": full["lactate"][minute],
                                 "bleed_ml_per_min": full["bleed"][minute], "state": balance.state, "hb": state.hb})
                series = {"lactate": full["lactate"], "deficit": full["deficit"], "D": full["D"], "stop": full["stop"],
                          "output": full["output"], "hb": [state.hb for state, _ in full["views"]]}
                item["runs"][f"{case}|{scenario}"] = {
                    "rows": rows, "flags": lr._flags(series, scenario), "debt": debt_checks(full),
                    "intervals": la.interval_classes(full["deficit"], full["bleed"]),
                    "rerun_equals_factorized": lactate == full["lactate"] and debt == full["D"],
                    "controlled_at": full["controlled_at"], "stop": full["stop"]}
        out[tag] = item
    return out


# 8. Readiness, region and freeze -----------------------------------------------------------------------------------

READY, NOT_READY = "LACTATE_PHYSIOLOGY_READY_FOR_HR_DOMAIN", "LACTATE_PHYSIOLOGY_NOT_READY"
REGION_STATUS = lr.REGION_STATUS
VERDICT_RULE = (
    "LACTATE_PHYSIOLOGY_READY_FOR_HR_DOMAIN when every check holds: (1) D temporal semantics coherent: the factorization "
    "validation finds D falling only across deficit-free minutes, no representative run has a D fall outside them or a "
    "critical minute below its arrival D, and in P2I-2AC's region no candidate keeps two or more critical minutes below "
    "its arrival D; (2) D -> lactate production no longer tied to tau_D (coupling_check); (3) the factorization agrees "
    "with the full core; (4) at least one candidate survives at demand 1.0 and every survivor is "
    "L3_RESUSCITATION_ADEQUATE_THROUGH_120 in both cases; (5) FD-LAC-04 is PASS or ALREADY_NORMALIZED and FD-LAC-05 PASS "
    "in both cases for every survivor (no NOT_EVALUABLE); (6) the demand layer classified every candidate; (7) the "
    "representatives are patient-like: no WORSENING_CRITICAL_WITH_LARGE_LACTATE_FALL, INSTANT_NORMALIZATION or "
    "INCOMPATIBLE_WITH_SURVIVAL flag and every rerun equals its factorized reading; (8) no unresolved lactate semantic "
    "contradiction: every survivor's FD-LAC-04 T* is its L3 adequacy onset in both cases. Otherwise "
    "LACTATE_PHYSIOLOGY_NOT_READY with the first blocker. Unique identification of hidden parameters is not required. "
    "No candidate, value or parameter is selected or approved.")
NEXT_DOMAIN = ("Recommended next domain (not started; needs its own authorization): heart rate and the sympathetic "
               "response, whose magnitudes the corrected D already moves (MAGNITUDE_PENDING_HR_RR_CALIBRATION); then "
               "pressure and vascular tone, unless that analysis finds a more fundamental blocker. Before collapse, GI "
               "migration or any runtime integration.")
INLINE_UNITS = lr.INLINE_UNITS
POLICY = ("Shadow only. The P2I-2AB current source space (its committed record), never the P2F historical region "
          "(P2FGuard). D repays only across oxygen-adequate minutes; lactate production is the independent "
          "D-to-lactate gain, explored on a range built before any count from dimensional consistency, the faculty "
          "envelopes and synthetic probes; FD-LAC-01..06 unchanged; L3 adequacy must persist through 120. Demand 0.9 / "
          "1.1 is reported uncertainty, 1.0 the region; rho is not counted. Haemodynamics simulated once, D and lactate "
          "post-processed exactly (validated, else stop). HR and RR changes are a causal propagation, their magnitudes "
          "unapproved and uncalibrated here. The legacy lactate is read after the filter only. Nothing is fitted, "
          "selected or approved; collapse stays off.")


def verdict(validation: dict, coupling: dict, crossing: dict | None, filtered: dict | None, statistics: dict | None,
            demand: dict | None, reviewed: dict | None) -> dict:
    runs = [run_ for item in (reviewed or {}).values() for run_ in item["runs"].values()]
    survivors = filtered["survivors"] if filtered else 0
    checks = [("factorization", validation["agree"], "the factorization does not agree with the full core"),
              ("lactate_coupling", coupling["independent"], "D -> lactate production still reads tau_D")]
    if filtered is not None:
        coherent = (validation["debt_coherent"] and crossing is not None and crossing["affected_new"] == 0
                    and bool(runs) and all(not r["debt"]["falls_outside_adequate_minutes"]
                                           and r["debt"]["critical_minutes_below_arrival"] == 0 for r in runs)
                    and statistics is not None and statistics["debt_incoherent_l3"] == 0)
        checks.insert(0, ("debt_semantics", coherent, "D still repays during a critical interval"))
        checks.append(("survivors", survivors > 0, "no candidate meets L3 adequacy and FD-LAC-01..06 jointly"))
        if statistics is not None and survivors:
            checks.append(("l3_adequate_through_120", all(statistics["adequacy"][c] == {L3_ADEQUATE: survivors}
                                                          for c in CASES), "a survivor loses L3 adequacy before 120"))
            checks.append(("definitive_management_evaluable", statistics["fd04_and_05_evaluated_in_both_cases"]
                           == survivors, "FD-LAC-04 / 05 are not evaluated for every survivor"))
        checks.append(("demand_characterized", demand is not None and sum(demand["classes"].values()) ==
                       filtered["candidates"], "the demand layer did not classify every candidate"))
        flagged = [name for r in runs for name in ("WORSENING_CRITICAL_WITH_LARGE_LACTATE_FALL",
                                                   "INSTANT_NORMALIZATION", "INCOMPATIBLE_WITH_SURVIVAL")
                   if r["flags"][name]]
        checks.append(("patient_like", bool(runs) and not flagged and all(r["rerun_equals_factorized"] for r in runs),
                       "a representative is not patient-like"))
        if statistics is not None and survivors:
            checks.append(("semantic_consistency", statistics["trigger_is_adequacy_onset"] == survivors,
                           "a survivor's FD-LAC-04 T* differs from its L3 adequacy onset"))
    blockers = [why for _, passed, why in checks if not passed]
    ready = not blockers and filtered is not None
    return {"verdict": READY if ready else f"{NOT_READY} — {blockers[0] if blockers else 'the filter did not run'}",
            "checks": {name: passed for name, passed, _ in checks}, "blockers": blockers, "rule": VERDICT_RULE,
            "next_domain": NEXT_DOMAIN if ready else None}


def region_record(filtered: dict) -> dict:
    units = [[i, index, list(r), list(d)] for i, index, r, d in filtered["units"]]
    digest = hashlib.sha256(json.dumps(units, separators=(",", ":")).encode("utf-8")).hexdigest()
    return {"status": REGION_STATUS, "demand": PRIMARY_DEMAND, "units": len(units), "candidates": filtered["survivors"],
            "digest": digest, "inline": units if len(units) <= INLINE_UNITS else None,
            "format": "[P1 set, lactate-side index, [P3 sets], [crystalloid points]]"}


def design() -> dict:
    return {"faculty": FACULTY, "source": "P2I-2AB record (p1, p3, crystalloid support) via lactate_adequacy",
            "k_ld": {**k_ld_design(), "rule": K_LD_RULE},
            "lactate_side": {"points": kinetic_points(), "levels": list(LEVELS),
                             "arrival_pairs": [list(p) for p in lr.ARRIVAL_PAIRS], "size": len(LAMBDAS),
                             "canonical": list(CANONICAL), "intrinsic": lr.INTRINSIC_RULE},
            "parameter_semantics": PARAMETER_SEMANTICS, "factorization": FACTORIZATION, "rules": RULES,
            "settings": SETTINGS, "l3": ADEQUACY_RULE,
            "demand": {"factors": list(DEMAND_FACTORS), "primary": PRIMARY_DEMAND, "rule": DEMAND_RULE},
            "rho": {"band": list(RHO_BAND), "representative": RESERVE, "synthetic_reference": RHO_SYNTHETIC_REFERENCE,
                    "status": RHO_STATUS},
            "filter_order": [[s, list(n)] for s, n in FILTER_ORDER], "cost": COST_RATIONALE,
            "rejections": REJECTION_RULE, "validation": validation_sample.__doc__, "crossing": CROSSING_RULE,
            "identifiability": IDENTIFIABILITY_RULE, "representatives": REPRESENTATIVE_RULE, "flags": FLAG_RULES,
            "debt_check": DEBT_CHECK_RULE, "legacy": lr.LEGACY_RULE, "verdict": VERDICT_RULE, "region": REGION_STATUS,
            "next_domain": NEXT_DOMAIN, "policy": POLICY}


def freeze_digest() -> str:
    records = {name: hashlib.sha256(path.read_bytes()).hexdigest()
               for name, path in (("P2I-2AB", la.P2I2AB_RECORD), ("P2I-2AC", P2I2AC_RECORD))}
    text = json.dumps({"revision": REVISION, "records": records, "design": design(), "lambdas": LAMBDAS,
                       "bits": {s: [list(b) for b in v] for s, v in BITS.items()}, "fd_lac": fd.definitions_digest(),
                       "thresholds": list(lr.FD04_THRESHOLDS), "histogram": lr.HISTOGRAM_STEP, "inline": INLINE_UNITS,
                       "tolerance": TOLERANCE, "sources": bf.freeze_sources()}, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run(progress=None, map_=map) -> dict:
    say = progress or (lambda *_: None)
    with lr.P2FGuard(), lr.LegacyLock():
        record = la.record_p2i2ab()
        source, support = la.source_space(record), record["crystalloid_support"]
        arrivals = lr.arrival_table()
        coupling = coupling_check()
        say("haemodynamics")
        tasks = haemodynamic_tasks(source, support)
        store = haemodynamics(tasks, map_)
        say("factorization")
        validation = validate(source, support, arrivals, tasks, store, map_)
        out = {"freeze_digest": freeze_digest(), "decided": DECIDED, "revision": REVISION, "policy": POLICY,
               "faculty": FACULTY, "records": {"P2I-2AB": record["freeze_digest"], "P2I-2AC": P2I2AC_DIGEST},
               "k_ld": k_ld_design(), "parameter_semantics": PARAMETER_SEMANTICS, "coupling": coupling,
               "hr_rr": {"status": [CAUSAL_PROPAGATION_ACCEPTED, MAGNITUDE_PENDING], "calibrated": False,
                         "historical_hr1_target": False},
               "source": {"p1_sets": len(source["p1"]), "p3_sets": len(source["p3"]),
                          "crystalloid_points": len(support), "lactate_side": len(LAMBDAS)},
               "validation": {k: v for k, v in validation.items() if k != "sample"},
               "validation_sample": validation["sample"]}
        if not (validation["agree"] and coupling["independent"]):
            out["verdict"] = verdict(validation, coupling, None, None, None, None, None)
            return out
        say("crossing")
        crossing = crossing_audit(source, arrivals, tasks, store, map_)
        filtered = {}
        for factor in DEMAND_FACTORS:
            say(f"filter x{factor:g}")
            filtered[factor] = filter_(source, support, arrivals, tasks, store, factor, map_)
        primary = filtered[PRIMARY_DEMAND]
        demand = demand_layer(filtered, len(support), primary["candidates"])
        statistics, picks, reviewed = None, {}, {}
        if primary["units"]:
            say("survivors")
            statistics = survivor_statistics(source, support, arrivals, tasks, store, primary, map_)
            picks = lr.representatives(source, support, primary, statistics.pop("_l60"))
            say("review")
            reviewed = review(source, support, arrivals, tasks, store, picks)
        demand.pop("_ids")
        previous = json.loads(P2I2AC_RECORD.read_text(encoding="utf-8"))["identifiability"]["dimensions"]
        out.update({"crossing": crossing,
                    "filter": {f"{f:g}": {k: v for k, v in filtered[f].items() if k != "units"} for f in DEMAND_FACTORS},
                    "region": region_record(primary), "demand": demand, "statistics": statistics,
                    "identifiability": identifiability(source, support, arrivals, primary, demand, previous),
                    "representatives": reviewed,
                    "verdict": verdict(validation, coupling, crossing, primary, statistics, demand, reviewed)})
    out["legacy_reference"] = lr.legacy_reference(reviewed)
    out["efficiency"] = {
        "haemodynamic_trajectories": len(store), "validation_full_runs": validation["runs"],
        "representative_full_runs": sum(len(item["runs"]) for item in reviewed.values()),
        "naive_core_runs": primary["candidates"] * len(SCENARIOS) * len(CASES) * len(DEMAND_FACTORS),
        "post_processed_units": {f"{f:g}": filtered[f]["post_processed_units"] for f in DEMAND_FACTORS},
        "analytic_rejections": 0, "survivor_units": len(primary["units"]),
        "blood_rows_reused_from_p2i2ab": record["rows_computed"],
        "analytic_rule": "no exact impossibility is known before simulation: every constraint reads the candidate's "
                         "own simulated deficit path, so ANALYTIC_REJECTION stays 0"}
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--digest", action="store_true")
    parser.add_argument("--design", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--out")
    args = parser.parse_args(argv)
    if args.digest:
        print(freeze_digest())
        return 0
    if args.design:
        print(json.dumps(design(), indent=1, default=str))
        return 0
    if args.run:
        if not args.out:
            parser.error("--run needs --out (a directory outside the repository)")
        out = Path(args.out)
        if out.resolve().is_relative_to(ROOT):
            parser.error("--out must be outside the repository")
        out.mkdir(parents=True, exist_ok=True)
        result = run(lambda step: print(step, flush=True))
        (out / "lactate_closure.json").write_text(json.dumps(result, indent=1, sort_keys=True, default=str),
                                                  encoding="utf-8")
        print(out / "lactate_closure.json")
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
