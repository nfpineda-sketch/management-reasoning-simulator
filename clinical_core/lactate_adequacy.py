"""P2I-2AC: oxygen-debt semantics and L3 resuscitation adequacy for the GI lactate (shadow only).

Faculty decisions (2026-10-28, P2I-2AC), recorded here and applied to the P2I-2AB current source space:

1. D is accumulated oxygen-delivery debt. While the effective oxygen deficit is positive D does not fall: production
   goes on and repayment is suspended (dD >= 0). With no deficit it may repay, gradually, with tau_D. The core carries
   it (``integration._oxygen_debt``); the deficit, delivery, extraction, tau_D and the gains are unchanged.
2. L3_RESUSCITATION_ADEQUACY, separate from FD-LAC-04: after two red-cell units and haemostasis at 60, sustained
   effective_deficit == 0 (ADEQUATE or COMPENSATED) must begin no later than minute 90, so that at least 30 min are
   observed by 120. Otherwise the candidate is L3_RESUSCITATION_INADEQUATE: rejected from the final region and
   reported apart, never as an FD-LAC-04 failure.
3. Ongoing bleeding is actual flow (the shared blood state's shed volume rising during the minute), not the
   haemostasis label: after haemostasis a residual bleed keeps FD-LAC-06's protection while the deficit is persistent
   or worsening; a recovering critical deficit, or none, still allows a decline. fraction_after_hemostasis stays the
   provisional 0.1 (FD-25 pending).
4. Metabolic demand 0.9 / 1.0 / 1.1 is explicit uncertainty: every candidate is reported ROBUST (passes at all
   three), DEMAND-SENSITIVE (some) or DEMAND-INCOMPATIBLE (none). 1.0 stays the case truth and the final region;
   no value is approved and robustness is not a filter.
5. rho: physiological band 2.0-3.0 with 2.5 representative; 1 only as SYNTHETIC_REFERENCE. rho is not counted in the
   candidate multiplicity and is reported as non-identifiable (it cancels with the re-anchored arrival ratio).
6. FD-LAC-04 (L(T*+30) < L(T*), no fixed 10 %) and FD-LAC-05 (57m 1.5-4.0, 72f 1.2-3.5, L120 < L(T*)) are unchanged.

The source space is P2I-2AB's (its committed record: 458 P3 sets, 12 crystalloid points, 1215 lactate-side points),
never the historical P2F region. Haemodynamics do not read D, so each scenario's trajectory is simulated once per
blood input and D and lactate are post-processed with the corrected recurrence, validated against full core runs
(else the run stops). Nothing is fitted, selected or approved; no SBP, MAP or HR is calibrated; collapse stays off.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import replace
from pathlib import Path

from . import blood_anchors, calibration, gi_reference
from . import blood_constraints as bc
from . import blood_extension as be
from . import blood_fluid_calibration as bf
from . import faculty_constraints as fd
from . import lactate_rebuild as lr
from .derived import derive, effective_delivery, effective_oxygen_deficit, oxygen_balance
from .integration import CHANNEL_BOUNDS
from .state import Channel

DECIDED = "2026-10-28"
REVISION = "P2I-2AC"
ROOT = lr.ROOT
CASES = lr.CASES
L1, L2, L3 = lr.L1, lr.L2, lr.L3
SCENARIOS = lr.SCENARIOS
MINUTES, TIMES = lr.MINUTES, lr.TIMES
RESERVE = lr.RESERVE
LAMBDAS = lr.LAMBDAS
LEVELS = lr.LEVELS
SETTINGS = lr.SETTINGS
PASS, FAIL = fd.PASS, fd.FAIL
RECOVERING, PERSISTENT = lr.RECOVERING, lr.PERSISTENT
STOPPED = lr.STOPPED
ANALYTIC_REJECTION, SIMULATION_REJECTION = lr.ANALYTIC_REJECTION, lr.SIMULATION_REJECTION

# 1. The records this package reads ----------------------------------------------------------------------------------

P2I2AB_RECORD = ROOT / "docs" / "revision" / "P2I2AB_lactate_rebuild.json"
P2I2AB_DIGEST = "15d05c321b38d2e2512642bf2e3be64bc4382ad639ad05ea445c9050091d7cc4"
P2I2AB_REGION_DIGEST = "ead624104a57948bf66ffd72e163e4847cff83f18698bc9b603f93f288006efe"
#: The P2I-2AB survivors with a sustained substantial lactate fall during a persistent or worsening deficit after
#: haemostasis (its statistics, reported and never filtered there): the P2I-2AC-2 audit re-reads them.
P2I2AB_POST_HAEMOSTASIS_DECLINES = 71_661

FACULTY = {
    "decided": DECIDED,
    "debt": "D is accumulated oxygen-delivery debt: while effective_oxygen_deficit > 0 it does not decrease (production "
            "continues, repayment suspended, dD >= 0); with deficit == 0 it may repay gradually with tau_D. No channel "
            "added; the deficit, DO2, extraction, tau_D, the D gain and the lactate gain unchanged",
    "l3_adequacy": "L3_RESUSCITATION_ADEQUACY: after 2 red-cell units and haemostasis at 60, sustained effective_deficit "
                   "== 0 (ADEQUATE or COMPENSATED) begins no later than minute 90 (>= 30 min observed by 120); "
                   "otherwise L3_RESUSCITATION_INADEQUATE, rejected from the final region and reported apart, never an "
                   "FD-LAC-04 failure",
    "bleeding": "ongoing bleeding is actual flow (current blood loss rate > 0), not the haemostasis event label; after "
                "60 a residual bleed with a PERSISTENT or WORSENING critical deficit keeps FD-LAC-06's protection; "
                "RECOVERING_CRITICAL or deficit == 0 still allows a decline; fraction_after_hemostasis unchanged "
                "(FD-25 pending)",
    "demand": "metabolic demand 0.9 / 1.0 / 1.1 as explicit uncertainty: ROBUST (all three), DEMAND-SENSITIVE (some), "
              "DEMAND-INCOMPATIBLE (none); no value approved, case truth unchanged, robustness never a filter",
    "rho": "physiological band 2.0-3.0, 2.5 representative; 1 only as SYNTHETIC_REFERENCE; rho not counted in the "
           "candidate multiplicity; reported as non-identifiable (invariant)",
    "fd_lac_04": "unchanged: L(T*+30) < L(T*), no fixed 10 %; 5 / 10 / 15 % diagnostic only",
    "fd_lac_05": "unchanged: 57m 1.5-4.0, 72f 1.2-3.5, L120 < L(T*); remaining NOT_EVALUABLE reported with its reason",
}


def record_p2i2ab() -> dict:
    """The committed P2I-2AB record, checked against its freeze and region digests."""
    record = json.loads(P2I2AB_RECORD.read_text(encoding="utf-8"))
    if record["freeze_digest"] != P2I2AB_DIGEST or record["region"]["digest"] != P2I2AB_REGION_DIGEST:
        raise AssertionError("the P2I-2AB record is not the committed one")
    if not record["source"]["reproduced"] or record["region"]["inline"] is None:
        raise AssertionError("the P2I-2AB record does not carry its reproduced source and inline region")
    return record


def source_space(record: dict) -> dict:
    """P2I-2AB's current source space, as its record carries it: P1 and P3 sets and each P1 set's P3 children."""
    p1, p3 = record["source"]["p1"], record["source"]["p3"]
    children = [[] for _ in p1]
    for q, entry in enumerate(p3):
        children[entry["p1"]].append(q)
    return {"p1": p1, "p3": p3, "children": children}


# 2. The corrected debt, post-processed --------------------------------------------------------------------------------

def debt_series(debt_input: list, d0: float, tau_d: float, gain_k: float) -> list:
    """The core's D minute by minute since P2I-2AC (integration._oxygen_debt and the channel guard): g x deficit while
    the deficit the minute reads is positive, -D / tau_D only when it is zero."""
    lower, upper = CHANNEL_BOUNDS[Channel.D][:2]
    out, debt = [d0], d0
    for deficit in debt_input:
        amount = gain_k * deficit if deficit > 0.0 else -debt / tau_d
        debt = min(upper, max(lower, debt + amount))
        out.append(debt)
    return out


FACTORIZATION = (
    "As P2I-2AB: each case's haemodynamic trajectory (delivery_rel, demand, the GI module's haemostasis minute, any stop "
    "and now the actual blood-loss flow of every minute, from the shared blood state's shed volume) is simulated once "
    "per scenario and blood input at reserve 2.5; haemodynamics do not read D, tau_D or the gains. The deficit the D "
    "update reads is demand x f - 2.5 x ratio x delivery_rel of the minute before; D follows the corrected core minute "
    "(D + g x deficit while it is positive, D - D / tau_D otherwise, within the channel guard); the lactate recurrence "
    "is unchanged. Validated on full core runs: exact at reserve 2.5 (any intrinsic rate, demand 0.9 / 1.0 / 1.1), "
    "within 1e-9 with identical verdicts at reserve 2.0 and 3.0 and at the synthetic reference 1.")


# 3. Haemodynamics with the actual flow --------------------------------------------------------------------------------

def _haemodynamic(task: tuple) -> tuple:
    case, scenario, items = task
    anchors, profile, full = blood_anchors.setup(case, **dict(items))
    states, stop = blood_anchors.trajectory(anchors, lr.scenario_items(case, scenario, full), MINUTES, profile)
    shed = [state.blood.shed_ml for state in states]
    flow = [after - before for before, after in zip(shed, shed[1:])]
    return task, {"delivery_rel": [derive(s, anchors, profile).delivery_rel for s in states],
                  "demand": [s.aux.oxygen_demand for s in states], "controlled_at": lr.controlled_at(states[-1]),
                  "stop": stop, "bleed": (flow[:1] or [0.0]) + flow}


def flow_windows(deficit: list, bleed: list) -> list:
    """The maximal spans of minutes with actual blood loss (flow > 0) and deficit > 0, as (first, last)."""
    found, start = [], None
    for minute, value in enumerate(deficit):
        if bleed[minute] > 0.0 and value > 0.0:
            start = minute if start is None else start
        elif start is not None:
            found.append((start, minute - 1))
            start = None
    if start is not None:
        found.append((start, len(deficit) - 1))
    return found


L3_ADEQUATE, L3_INADEQUATE = "L3_RESUSCITATION_ADEQUATE", "L3_RESUSCITATION_INADEQUATE"
L3_LATEST_ONSET = 90
NO_HAEMOSTASIS, NEVER_ADEQUATE, NOT_SUSTAINED = ("no haemostasis", "no minute without deficit after haemostasis",
                                                 "no deficit-free span of 30 min beginning by minute 90")
ADEQUACY_RULE = ("L3_RESUSCITATION_ADEQUATE when some minute t with haemostasis <= t <= 90 starts a span with "
                 "effective_deficit == 0 at every minute t..t+30 (ADEQUATE or COMPENSATED); otherwise "
                 "L3_RESUSCITATION_INADEQUATE, a rejection of its own, read before FD-LAC-04 and never counted as an "
                 "FD-LAC-04 failure. Exact comparison, no tolerance.")


def l3_adequacy(deficit: list, haemostasis: int | None, settings: dict = SETTINGS) -> dict:
    hold = settings["fd04_sustained_restoration_min"]
    if haemostasis is None:
        return {"status": L3_INADEQUATE, "onset": None, "reason": NO_HAEMOSTASIS, "first_zero": None}
    first_zero, start = None, None
    for minute in range(haemostasis, len(deficit) + 1):
        zero = minute < len(deficit) and deficit[minute] == 0.0
        if zero:
            first_zero = minute if first_zero is None else first_zero
            start = minute if start is None else start
            if start <= L3_LATEST_ONSET and minute - start >= hold:
                return {"status": L3_ADEQUATE, "onset": start, "reason": None, "first_zero": first_zero}
        else:
            start = None
    return {"status": L3_INADEQUATE, "onset": None, "reason": NEVER_ADEQUATE if first_zero is None else NOT_SUSTAINED,
            "first_zero": first_zero}


class Context:
    """One run's oxygen side as FD-LAC reads it (see ``lactate_rebuild.Context``), with windows from the actual flow:
    effective delivery, oxygen available (reserve x delivery), demand (x the demand factor), deficit of each minute's end
    state, the deficit the core's D update reads, the actual blood-loss flow, the judged windows and reassessment pairs
    and, for a run with haemostasis, the L3 adequacy reading."""

    __slots__ = ("delivery", "available", "demand", "deficit", "debt_input", "bleed", "controlled_at", "stop", "factor",
                 "fd01_windows", "fd01_pairs", "fd06_windows", "fd06_pairs", "adequacy", "trajectory_delivery",
                 "trajectory_demand")

    def __init__(self, delivery: list, demand: list, bleed: list, haemostasis: int | None, stop: int | None,
                 reserve: float = RESERVE, settings: dict = SETTINGS):
        self.delivery, self.demand, self.bleed, self.controlled_at, self.stop = delivery, demand, bleed, haemostasis, stop
        self.available = [reserve * d for d in delivery]
        self.deficit = [max(0.0, need - have) for need, have in zip(demand, self.available)]
        self.debt_input = [max(0.0, demand[m] - self.available[m - 1]) for m in range(1, len(demand))]
        self.factor = 1.0 - settings["meaningful_change"]
        self.trajectory_delivery, self.trajectory_demand = tuple(self.available), tuple(demand)
        windows = flow_windows(self.deficit, bleed)
        until, span = settings["fd01_until_min"], settings["sustained_min"]
        clipped = [(first, min(last, until)) for first, last in windows if first <= until]
        self.fd01_windows = [w for w in clipped if w[1] - w[0] >= span]
        self.fd06_windows = [w for w in windows if w[1] - w[0] >= span]
        self.fd01_pairs = lr._pairs(self.deficit, self.fd01_windows, settings)
        self.fd06_pairs = lr._pairs(self.deficit, self.fd06_windows, settings)
        self.adequacy = None if haemostasis is None else l3_adequacy(self.deficit, haemostasis, settings)

    def trajectory(self, lactate, debt) -> fd.Trajectory:
        return fd.Trajectory(tuple(lactate), tuple(debt), self.trajectory_delivery, self.trajectory_demand,
                             self.controlled_at)


def context_of(haemodynamic: dict, ratio: float, factor: float = 1.0) -> Context:
    """The factorized reading: effective delivery = ratio x delivery_rel; demand x the demand factor."""
    demand = haemodynamic["demand"] if factor == 1.0 else [factor * x for x in haemodynamic["demand"]]
    return Context([ratio * d for d in haemodynamic["delivery_rel"]], demand, haemodynamic["bleed"],
                   haemodynamic["controlled_at"], haemodynamic["stop"])


# 4. FD-LAC with the actual flow -------------------------------------------------------------------------------------

RESIDUAL = "FD-LAC-06 (residual bleeding)"
RULES = {
    **{name: text for name, text in lr.CURRENT_RULES.items() if name not in ("windows", "FD-LAC-06")},
    "windows": "a critical bleeding window is a maximal span of minutes with actual blood loss (the shared blood "
               "state's shed volume rose during the minute) and deficit > 0; it is judged when it lasts at least "
               "sustained_min (30). Before haemostasis this is the earlier window; after it a residual bleed extends it",
    "FD-LAC-06": "every engine-produced run (L1, L2, L3): no PERSISTENT_OR_WORSENING_CRITICAL decline in any judged "
                 "window. A failing pair whose later point lies before haemostasis is FD-LAC-06 (active bleeding); one "
                 "at or after it is FD-LAC-06 (residual bleeding). RECOVERING_CRITICAL declines and declines while "
                 "adequate are allowed",
    "L3_RESUSCITATION_ADEQUACY": ADEQUACY_RULE,
    "demand": "the deficit reads demand x f (f = 0.9, 1.0, 1.1); 1.0 is the case truth and gives the final region",
}


def fd_lac_06_run(lactate: list, context: Context) -> dict:
    persistent = lr._falls(lactate, context.fd06_pairs[PERSISTENT], context.factor)
    recovering = lr._falls(lactate, context.fd06_pairs[RECOVERING], context.factor)
    haemostasis = context.controlled_at
    residual = [pair for pair in persistent if haemostasis is not None and pair[1] >= haemostasis]
    return {"status": FAIL if persistent else PASS, "passes": not persistent,
            "active": [pair for pair in persistent if pair not in residual], "residual": residual,
            "recovering": recovering,
            "recovering_residual": [p for p in recovering if haemostasis is not None and p[1] >= haemostasis]}


def fd_lac_04_05(lactate: list, debt: list, context: Context, point: tuple, case: str) -> tuple:
    trajectory = context.trajectory(lactate, debt)
    response = fd.fd_lac_04(trajectory, SETTINGS)
    residual = fd.fd_lac_05(trajectory, response["trigger"], lr.kinetics_of(point), lactate[0], SETTINGS, case)
    return response, residual


# 5. The sequential filter at one demand factor -----------------------------------------------------------------------

DEMAND_FACTORS = (1.0, 0.9, 1.1)
PRIMARY_DEMAND = 1.0
FILTER_ORDER = (
    (L1, ("FD-LAC-02/03", "FD-LAC-01", "FD-LAC-06")),
    (L3, (L3_INADEQUATE, "FD-LAC-04", "FD-LAC-05", "FD-LAC-06", RESIDUAL)),
    (L2, ("FD-LAC-06",)),
)
COST_RATIONALE = ("Fixed by cost before any result, as P2I-2AB: L1 (one trajectory per P1 set and case), then L3 (one "
                  "per P3 set), then L2 (one per P1 set and crystalloid point, the most). Inside L3 the first failure "
                  "is read as the faculty listed the layers: L3 adequacy, FD-LAC-04, FD-LAC-05, FD-LAC-06 during active "
                  "bleeding, FD-LAC-06 during residual bleeding (57m before 72f in each); every constraint is evaluated "
                  "for both cases (complete failure counts). The support and the corrected D are applied to every "
                  "candidate. The filter runs once per demand factor on the same haemodynamic trajectories (demand "
                  "reaches only the deficit); 1.0 first, and only 1.0 makes the region.")
BITS = {scenario: tuple((name, case) for name in names for case in CASES) + ((STOPPED, None),)
        for scenario, names in FILTER_ORDER}
REJECTION_RULE = lr.REJECTION_RULE


def _series(haemodynamic: dict, arrival: dict, wanted, factor: float, cache: dict):
    """(lambda index, lactate, D, context) for the wanted lactate-side points; contexts and D series are shared."""
    contexts, debts = cache.setdefault("contexts", {}), cache.setdefault("debts", {})
    for index in wanted:
        tau_d, gain_k, gain, tau_l, excess, debt, delivery = LAMBDAS[index]
        context = contexts.get(delivery)
        if context is None:
            context = contexts[delivery] = context_of(haemodynamic, arrival["ratio"][delivery], factor)
        key = (delivery, debt, tau_d, gain_k)
        series = debts.get(key)
        if series is None:
            series = debts[key] = debt_series(context.debt_input, arrival["debt"][debt], tau_d, gain_k)
        lactate = lr.lactate_series(series, arrival["excess"][excess], tau_d, tau_l, gain, arrival["baseline"][excess],
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
        if haemodynamic[case]["stop"] is not None:
            masks = {index: mask | _bit(L3, STOPPED, None) for index, mask in masks.items()}
            continue
        for index, lactate, debt, context in _series(haemodynamic[case], arrivals[case], wanted, factor, {}):
            response, residual = fd_lac_04_05(lactate, debt, context, LAMBDAS[index], case)
            sixth = fd_lac_06_run(lactate, context)
            masks[index] |= 0 if context.adequacy["status"] == L3_ADEQUATE else _bit(L3, L3_INADEQUATE, case)
            masks[index] |= 0 if response["passes"] else _bit(L3, "FD-LAC-04", case)
            masks[index] |= 0 if residual["passes"] else _bit(L3, "FD-LAC-05", case)
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


class Stage:
    """Candidate-weighted accounting of one stage; ``only`` counts the candidates one constraint alone rejects."""

    def __init__(self, scenario: str):
        self.scenario = scenario
        self.entering = self.rejected = self.units = self.units_rejected = 0
        self.first, self.any, self.only = {}, {}, {}

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


def haemodynamic_tasks(source: dict, support: list) -> dict:
    """Every trajectory a filter at any demand factor can read: L1 per P1 set, L3 per P3 set, L2 per P1 set and
    crystalloid point, each case."""
    p1, p3 = source["p1"], source["p3"]
    tasks = {}
    for i, entry in enumerate(p1):
        for case in CASES:
            tasks[(L1, i, case)] = lr.haemodynamic_task(case, L1, lr.blood_values(entry, case))
            for d, item in enumerate(support):
                tasks[(L2, (i, d), case)] = lr.haemodynamic_task(case, L2, lr.blood_values(entry, case, item["bag"]))
    for q, entry in enumerate(p3):
        for case in CASES:
            tasks[(L3, q, case)] = lr.haemodynamic_task(case, L3, lr.blood_values(entry, case))
    return tasks


def haemodynamics(tasks: dict, map_=map) -> dict:
    store = {}
    for task, result in map_(_haemodynamic, list(dict.fromkeys(tasks.values()))):
        store[task] = result
    return store


def filter_(source: dict, support: list, arrivals: dict, tasks: dict, store: dict, factor: float, map_=map) -> dict:
    """L1, then L3, then L2 at one demand factor. A candidate is (P3 set, crystalloid point, lactate side); it
    survives when every unit it projects to passes in both cases."""
    p1, p3, children = source["p1"], source["p3"], source["children"]
    n_lambda, n_support = len(LAMBDAS), len(support)
    stages = {s: Stage(s) for s in SCENARIOS}
    evaluated = {s: 0 for s in SCENARIOS}

    def trajectories(scenario, unit):
        return {case: store[tasks[(scenario, unit, case)]] for case in CASES}

    passing = {}
    work = [(i, trajectories(L1, i), arrivals, range(n_lambda), factor) for i in range(len(p1))]
    for i, masks in map_(_l1_unit, work):
        evaluated[L1] += len(masks)
        weight = len(children[i]) * n_support
        passing[i] = []
        for index in range(n_lambda):
            stages[L1].add(masks[index], weight)
            if not masks[index]:
                passing[i].append(index)
    alive = [i for i in range(len(p1)) if passing[i]]
    r_ok = {}
    work = [(q, trajectories(L3, q), arrivals, passing[i], factor) for i in alive for q in children[i]]
    for q, masks in map_(_l3_unit, work):
        evaluated[L3] += len(masks)
        i = p3[q]["p1"]
        for index in passing[i]:
            stages[L3].add(masks[index], n_support)
            if not masks[index]:
                r_ok.setdefault((i, index), []).append(q)
    wanted = {i: [index for index in passing[i] if (i, index) in r_ok] for i in alive}
    alive = [i for i in alive if wanted[i]]
    d_ok = {}
    work = [((i, d), trajectories(L2, (i, d)), arrivals, wanted[i], factor) for i in alive for d in range(n_support)]
    for (i, d), masks in map_(_l2_unit, work):
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
    """Each candidate (P3 set q, crystalloid point d, lactate side) as one integer."""
    n_lambda = len(LAMBDAS)
    return {(q * n_support + d) * n_lambda + index for _, index, r, ds in units for q in r for d in ds}


ROBUST, SENSITIVE, INCOMPATIBLE = "ROBUST", "DEMAND-SENSITIVE", "DEMAND-INCOMPATIBLE"
DEMAND_RULE = ("Each candidate is filtered at demand x 0.9, x 1.0 and x 1.1 (the case's metabolic_demand_baseline "
               "scaled; demand reaches only the deficit, checked on full core runs). ROBUST: survives at all three; "
               "DEMAND-SENSITIVE: at one or two; DEMAND-INCOMPATIBLE: at none. Reported, never a filter: the final "
               "region is the one at 1.0, whatever its robustness.")


def demand_layer(filtered: dict, n_support: int, total: int) -> dict:
    ids = {factor: candidate_ids(filtered[factor]["units"], n_support) for factor in DEMAND_FACTORS}
    patterns = {}
    union = set().union(*ids.values())
    for candidate in union:
        key = "+".join(f"{factor:g}" for factor in sorted(DEMAND_FACTORS) if candidate in ids[factor])
        patterns[key] = patterns.get(key, 0) + 1
    robust = patterns.get("+".join(f"{f:g}" for f in sorted(DEMAND_FACTORS)), 0)
    primary = ids[PRIMARY_DEMAND]
    return {"rule": DEMAND_RULE, "survivors": {f"{f:g}": len(ids[f]) for f in DEMAND_FACTORS},
            "classes": {ROBUST: robust, SENSITIVE: len(union) - robust, INCOMPATIBLE: total - len(union)},
            "patterns": dict(sorted(patterns.items())),
            "final_region": {ROBUST: sum(1 for c in primary if all(c in ids[f] for f in DEMAND_FACTORS)),
                             SENSITIVE: sum(1 for c in primary if not all(c in ids[f] for f in DEMAND_FACTORS))},
            "_ids": ids}


# 6. Validation of the factorization ----------------------------------------------------------------------------------

VALIDATION_RULE = ("P2I-2AB's sample (per rate the first, middle and last P3 set; lactate-side indices 0, n/4, n/2, "
                   "3n/4, n-1 and the canonical point; L1, L3 and L2 at the first and last crystalloid point; both "
                   "cases) at reserve 2.5, demand 1.0 and intrinsic midpoint: exact equality of every minute's "
                   "lactate, D, deficit and actual flow, of haemostasis and stop, and of every verdict (FD-LAC, L3 "
                   "adequacy, active and residual FD-LAC-06). On the canonical point also demand 0.9 and 1.1 and "
                   "intrinsic lower / upper (exact), and reserve 2.0, 3.0 and the synthetic reference 1 (within 1e-9, "
                   "identical verdicts). Any disagreement stops the run.")
RHO_BAND = (2.0, 3.0)
RHO_SYNTHETIC_REFERENCE = 1.0
RHO_STATUS = ("NON_IDENTIFIABLE (invariant): rho cancels in deficit, D, lactate and adequacy because the arrival ratio "
              "is re-anchored as ratio / rho; evaluated at 2.5 (representative of the 2.0-3.0 band), checked at 2.0 and "
              "3.0, 1 only as SYNTHETIC_REFERENCE; never counted in the candidate multiplicity")
CANONICAL = lr.CANONICAL
TOLERANCE = lr.TOLERANCE


def validation_sample(source: dict, support: list) -> list[dict]:
    out = []
    canonical = LAMBDAS.index(CANONICAL)
    for item in lr.validation_sample(source, support):
        if item["reserve"] != RESERVE or item["intrinsic"] != "midpoint":
            continue
        out.append({**item, "demand": PRIMARY_DEMAND})
        if item["lambda"] == canonical:
            variants = ([(RESERVE, "midpoint", factor) for factor in DEMAND_FACTORS if factor != PRIMARY_DEMAND]
                        + [(RESERVE, level, PRIMARY_DEMAND) for level in ("lower", "upper")]
                        + [(reserve, "midpoint", PRIMARY_DEMAND) for reserve in (*RHO_BAND, RHO_SYNTHETIC_REFERENCE)])
            out.extend({**item, "reserve": r, "intrinsic": n, "demand": f} for r, n, f in variants)
    return out


def full_run(entry: dict, case: str, scenario: str, point: tuple, bag: dict | None = None, reserve: float = RESERVE,
             intrinsic: str = "midpoint", factor: float = PRIMARY_DEMAND) -> dict:
    """The full core run of one blood entry and lactate-side point (no factorization), with the demand baseline
    scaled by ``factor``."""
    tau_d, gain_k, gain, tau_l, excess, debt, delivery = point
    values = {**lr.blood_values(entry, case, bag), "reserve": reserve}
    _, profile, full = blood_anchors.setup(case, **values)
    case_values = calibration.case_values(case, calibration.GICandidate({}, excess=excess, debt=debt,
                                                                        delivery=delivery, intrinsic=intrinsic))
    case_values["preload_fraction"] = full[bc.POS]
    case_values["arrival_delivery_ratio"] /= reserve
    case_values["metabolic_demand_baseline"] *= factor
    anchors = gi_reference.candidate_anchors(case, case_values)
    profile = replace(profile, debt_clearance_tau_min=tau_d, debt_per_delivery_deficit=gain_k,
                      lactate_per_output_deficit=gain, lactate_clearance_tau_min=tau_l)
    states, stop = blood_anchors.trajectory(anchors, lr.scenario_items(case, scenario, full), MINUTES, profile)
    out = {key: [] for key in ("lactate", "D", "deficit", "available", "demand", "delivery", "output", "views")}
    for state in states:
        view = derive(state, anchors, profile)
        delivery_ = effective_delivery(view.delivery_rel, anchors)
        out["lactate"].append(view.lactate)
        out["D"].append(state.D)
        out["deficit"].append(effective_oxygen_deficit(state.aux.oxygen_demand, delivery_, reserve))
        out["available"].append(reserve * delivery_)
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
                    L3_INADEQUATE: context.adequacy["status"], "onset": context.adequacy["onset"]})
    return out


def factorized(haemodynamic: dict, arrival: dict, point: tuple, factor: float = PRIMARY_DEMAND) -> tuple:
    """(lactate, D, context) of one lactate-side point, on or off the grid, post-processed on a simulated haemodynamic
    trajectory."""
    tau_d, gain_k, gain, tau_l, excess, debt, delivery = point
    context = context_of(haemodynamic, arrival["ratio"][delivery], factor)
    series = debt_series(context.debt_input, arrival["debt"][debt], tau_d, gain_k)
    lactate = lr.lactate_series(series, arrival["excess"][excess], tau_d, tau_l, gain, arrival["baseline"][excess],
                                arrival["floor"])
    return lactate, series, context


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
    no_fall_in_deficit = all(full["D"][m + 1] >= full["D"][m] for m, e in enumerate(own.debt_input) if e > 0.0)
    strict = reserve == RESERVE
    agrees = (events and mine == theirs and no_fall_in_deficit and gaps["bleed"] == 0.0
              and (exact if strict else max(gaps.values()) <= TOLERANCE))
    return {"exact": exact, "gaps": gaps, "events": events, "verdicts": mine, "verdicts_equal": mine == theirs,
            "no_debt_fall_in_deficit": no_fall_in_deficit, "agrees": agrees}


def _validate_one(task: tuple) -> dict:
    item, entry, bag, haemodynamic, arrival = task
    case, scenario, point = item["case"], item["scenario"], LAMBDAS[item["lambda"]]
    full = full_run(entry, case, scenario, point, bag, item["reserve"], item["intrinsic"], item["demand"])
    return {**item, **compare(full, factorized(haemodynamic, arrival, point, item["demand"]), haemodynamic, case,
                              scenario, point, item["reserve"])}


def validate(source: dict, support: list, arrivals: dict, tasks: dict, store: dict, map_=map) -> dict:
    sample = validation_sample(source, support)
    work = []
    for item in sample:
        entry = source["p3"][item["q"]]
        unit = (item["q"] if item["scenario"] == L3 else
                entry["p1"] if item["scenario"] == L1 else (entry["p1"], item["support"]))
        bag = support[item["support"]]["bag"] if item["scenario"] == L2 else None
        work.append((item, entry, bag, store[tasks[(item["scenario"], unit, item["case"])]], arrivals[item["case"]]))
    results = list(map_(_validate_one, work))
    seen = {}
    for result in results:
        for name, value in result.pop("verdicts").items():
            if name != "onset":
                label = f"{result['scenario']} {name} {value}"
                seen[label] = seen.get(label, 0) + 1
    primary = [r for r in results if r["reserve"] == RESERVE]
    return {"rule": VALIDATION_RULE, "runs": len(results), "agree": all(r["agrees"] for r in results),
            "exact_at_reserve_2_5": all(r["exact"] for r in primary),
            "max_gap_other_reserves": max((max(r["gaps"].values()) for r in results if r["reserve"] != RESERVE),
                                          default=0.0),
            "reserves": sorted({r["reserve"] for r in results}), "demands": sorted({r["demand"] for r in results}),
            "no_debt_fall_in_deficit": all(r["no_debt_fall_in_deficit"] for r in results),
            "verdicts_seen": dict(sorted(seen.items())), "disagreements": [r for r in results if not r["agrees"]],
            "sample": results}


# 7. P2I-2AC-2: the P2I-2AB post-haemostasis declines under the actual flow ------------------------------------------

AUDIT_CLASSES = ("PERSISTENT_OR_WORSENING_WITH_RESIDUAL_BLEEDING", "RECOVERING_WITH_RESIDUAL_BLEEDING",
                 "NO_RESIDUAL_BLEEDING", "ADEQUATE_OR_COMPENSATED")
AUDIT_RULE = ("P2I-2AB's survivors re-read with their own (pre-P2I-2AC) D and lactate, never refiltered: on each L3 "
              "run, P2I-2AB's flag (a sustained substantial fall during a persistent or worsening deficit after "
              "haemostasis) and the actual-flow FD-LAC-06. Class per run: PERSISTENT_OR_WORSENING_WITH_RESIDUAL_"
              "BLEEDING when a failing pair lies at or after haemostasis in a window with actual flow (an FD-LAC-06 "
              "violation); else RECOVERING_WITH_RESIDUAL_BLEEDING when a recovering decline does (allowed); else "
              "NO_RESIDUAL_BLEEDING when P2I-2AB's flagged fall lies where the flow had stopped; else "
              "ADEQUATE_OR_COMPENSATED. A candidate takes its worse case, in that order. Also counted: the same "
              "survivors' violations with the corrected D.")


def _audit_unit(task: tuple) -> tuple:
    q, haemodynamic, arrivals, wanted = task
    out = {}
    for case in CASES:
        h, arrival = haemodynamic[case], arrivals[case]
        olds, news, cache = {}, {}, {}
        for index, lactate, _, old_context in lr._series(h, arrival, wanted, cache):
            olds[index] = (lactate, old_context)
        for index, lactate, _, context in _series(h, arrival, wanted, PRIMARY_DEMAND, {}):
            news[index] = (lactate, context)
        after = {}
        for index in wanted:
            lactate, old_context = olds[index]
            context = news[index][1]
            flagged_pairs = after.get(id(old_context))
            if flagged_pairs is None:
                flagged_pairs = after[id(old_context)] = lr._after_haemostasis(old_context)
            flagged = lr._falls(lactate, flagged_pairs, old_context.factor)
            old = fd_lac_06_run(lactate, context)
            new = fd_lac_06_run(news[index][0], context)
            if old["residual"]:
                label = AUDIT_CLASSES[0]
            elif old["recovering_residual"]:
                label = AUDIT_CLASSES[1]
            elif any(context.bleed[m] == 0.0 for early, late in flagged for m in range(early, late + 1)):
                label = AUDIT_CLASSES[2]
            else:
                label = AUDIT_CLASSES[3]
            out[(index, case)] = {"flagged": bool(flagged), "class": label, "violates_old_d": not old["passes"],
                                  "violates_residual_old_d": bool(old["residual"]),
                                  "violates_residual_corrected_d": bool(new["residual"]),
                                  "violates_corrected_d": not new["passes"]}
    return q, out


def audit_p2i2ab(record: dict, source: dict, arrivals: dict, tasks: dict, store: dict, map_=map) -> dict:
    units = record["region"]["inline"]
    by_q = {}
    for _, index, r, _ in units:
        for q in r:
            by_q.setdefault(q, set()).add(index)
    readings = dict(map_(_audit_unit, [(q, {c: store[tasks[(L3, q, c)]] for c in CASES}, arrivals, sorted(idx))
                                       for q, idx in sorted(by_q.items())]))
    flagged = {name: 0 for name in AUDIT_CLASSES}
    counts = {"flagged": 0, "violating_actual_flow_fd06_old_d": 0, "violating_residual_old_d": 0,
              "violating_residual_old_d_not_flagged": 0, "flagged_violating_residual_corrected_d": 0,
              "violating_residual_corrected_d": 0, "survivors": 0}
    for _, index, r, d in units:
        for q in r:
            items = [readings[q][(index, case)] for case in CASES]
            weight = len(d)
            counts["survivors"] += weight
            residual_old = any(item["violates_residual_old_d"] for item in items)
            corrected = any(item["violates_residual_corrected_d"] for item in items)
            counts["violating_actual_flow_fd06_old_d"] += weight * any(item["violates_old_d"] for item in items)
            counts["violating_residual_old_d"] += weight * residual_old
            counts["violating_residual_corrected_d"] += weight * corrected
            if any(item["flagged"] for item in items):
                counts["flagged"] += weight
                worst = min(AUDIT_CLASSES.index(item["class"]) for item in items)
                flagged[AUDIT_CLASSES[worst]] += weight
                counts["flagged_violating_residual_corrected_d"] += weight * corrected
            elif residual_old:
                counts["violating_residual_old_d_not_flagged"] += weight
    return {"rule": AUDIT_RULE, "p2i2ab_flagged": P2I2AB_POST_HAEMOSTASIS_DECLINES,
            "reproduced": counts["flagged"] == P2I2AB_POST_HAEMOSTASIS_DECLINES, "classes": flagged,
            "would_violate_fd06": flagged[AUDIT_CLASSES[0]], **counts}


# 8. The final region: statistics, identifiability, representatives --------------------------------------------------

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
            sixth = fd_lac_06_run(lactate, context)
            trigger = response["trigger"]
            compensated = trigger is not None and any(
                context.deficit[m] == 0.0 and context.delivery[m] < context.demand[m]
                for m in range(trigger, min(trigger + SETTINGS["fd04_window_min"], len(lactate) - 1) + 1))
            out[(index, case)] = {"fd04": response["status"], "fd04_reason": response.get("reason"),
                                  "reduction": response.get("reduction_at_window"), "fd05": residual["status"],
                                  "fd05_reason": residual.get("reason"), "L120": lactate[120], "trigger": trigger,
                                  "at_trigger": response.get("at_trigger"), "onset": context.adequacy["onset"],
                                  "recovering": len(sixth["recovering"]),
                                  "recovering_residual": len(sixth["recovering_residual"]),
                                  "compensated_after_trigger": compensated, "D120": debt[120]}
    return unit, out


def _survivor_l2(task: tuple) -> tuple:
    unit, haemodynamic, arrivals, wanted = task
    out = {}
    for case in CASES:
        for index, lactate, _, context in _series(haemodynamic[case], arrivals[case], wanted, PRIMARY_DEMAND, {}):
            out[(index, case)] = {"recovering": len(fd_lac_06_run(lactate, context)["recovering"])}
    return unit, out


def _count(table: dict, key, weight: int) -> None:
    table[str(key)] = table.get(str(key), 0) + weight


def survivor_statistics(source: dict, support: list, arrivals: dict, tasks: dict, store: dict, filtered: dict,
                        map_=map) -> dict:
    """The final region's readings (never its verdicts): distributions, FD-LAC-04 sensitivity, FD-LAC-04 / 05 status
    with every remaining NOT_EVALUABLE and its reason, adequacy onsets and the recovering declines allowed."""
    units = filtered["units"]
    by_p1, by_p3, by_d = {}, {}, {}
    for i, index, r, d in units:
        by_p1.setdefault(i, []).append(index)
        for q in r:
            by_p3.setdefault(q, []).append(index)
        for k in d:
            by_d.setdefault((i, k), []).append(index)
    l1 = dict(map_(_survivor_l1, [(i, {c: store[tasks[(L1, i, c)]] for c in CASES}, arrivals, idx)
                                  for i, idx in sorted(by_p1.items())]))
    l3 = dict(map_(_survivor_l3, [(q, {c: store[tasks[(L3, q, c)]] for c in CASES}, arrivals, idx)
                                  for q, idx in sorted(by_p3.items())]))
    l2 = dict(map_(_survivor_l2, [((i, k), {c: store[tasks[(L2, (i, k), c)]] for c in CASES}, arrivals, idx)
                                  for (i, k), idx in sorted(by_d.items())]))
    summaries = {name: {case: lr.Summary() for case in CASES} for name in ("L60", "L120", "reduction", "at_trigger",
                                                                          "D120")}
    tables = {name: {case: {} for case in CASES} for name in ("fd01_status", "fd04_status", "fd05_status",
                                                              "fd04_not_evaluable", "fd05_not_evaluable",
                                                              "trigger_minute", "adequacy_onset")}
    sensitivity = {f"{t:g}": 0 for t in lr.FD04_THRESHOLDS}
    recovering = {L1: 0, L3: 0, L2: 0, "L3 residual bleeding": 0}
    compensated = evaluated_both = 0
    high_72f_unevaluated = 0
    for i, index, r, d in units:
        n_r, n_d = len(r), len(d)
        for case in CASES:
            item = l1[i][(index, case)]
            summaries["L60"][case].add(item["L60"], n_r * n_d)
            _count(tables["fd01_status"][case], item["fd01"], n_r * n_d)
        if any(l1[i][(index, case)]["recovering"] for case in CASES):
            recovering[L1] += n_r * n_d
        for q in r:
            items = {case: l3[q][(index, case)] for case in CASES}
            for case, item in items.items():
                _count(tables["fd04_status"][case], item["fd04"], n_d)
                _count(tables["fd05_status"][case], item["fd05"], n_d)
                _count(tables["trigger_minute"][case], item["trigger"], n_d)
                _count(tables["adequacy_onset"][case], item["onset"], n_d)
                if item["fd04"] == fd.NOT_EVALUABLE:
                    _count(tables["fd04_not_evaluable"][case], item["fd04_reason"], n_d)
                if item["fd05"] == fd.NOT_EVALUABLE:
                    _count(tables["fd05_not_evaluable"][case], item["fd05_reason"], n_d)
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
            if items["gi_bleed_72f"]["fd05"] == fd.NOT_EVALUABLE and items["gi_bleed_72f"]["L120"] > \
                    fd.ENVELOPES_120["gi_bleed_72f"]["high"]:
                high_72f_unevaluated += n_d
            if any(item["recovering"] for item in items.values()):
                recovering[L3] += n_d
            if any(item["recovering_residual"] for item in items.values()):
                recovering["L3 residual bleeding"] += n_d
            if any(item["compensated_after_trigger"] for item in items.values()):
                compensated += n_d
        for k in d:
            if any(l2[(i, k)][(index, case)]["recovering"] for case in CASES):
                recovering[L2] += n_r
    return {**{name: {c: summaries[name][c].report() for c in CASES} for name in ("L60", "L120", "D120")},
            "fd04_reduction": {c: summaries["reduction"][c].report() for c in CASES},
            "fd04_at_trigger": {c: summaries["at_trigger"][c].report() for c in CASES},
            **tables, "fd04_and_05_evaluated_in_both_cases": evaluated_both,
            "fd05_not_evaluable_72f_above_envelope": high_72f_unevaluated,
            "fd04_sensitivity": {"thresholds": sensitivity, "survivors": filtered["survivors"],
                                 "note": "diagnostic only: survivors that would also pass FD-LAC-04 with the fall "
                                         "required at the threshold; never filters"},
            "recovering_declines_allowed": {"survivors_with_one": recovering,
                                            "note": "survivors whose run had a sustained substantial decline the "
                                                    "semantics allowed as RECOVERING_CRITICAL"},
            "adequacy_by_compensation_after_trigger": compensated,
            "_l60": {(i, index): {case: l1[i][(index, case)]["L60"] for case in CASES} for i, index, _, _ in units}}


IDENTIFIABILITY_RULE = ("On the final region (demand 1.0), per dimension, against the values present in the source "
                        "space, as P2I-2AB: one value explored = NOT_VARIED; one left = WELL_CONSTRAINED; some excluded "
                        "= PARTIALLY_CONSTRAINED; none excluded = POORLY_IDENTIFIED; structural = "
                        "NON_IDENTIFIABLE_SEPARATELY (G and g reach lactate only as G x g with G x arrival debt). rho is "
                        "not a dimension of the candidates (RHO_STATUS). Demand is read on the union of the three "
                        "filters (the factors at which a candidate survives). Each status is set beside P2I-2AB's: "
                        "NARROWER when fewer values survive, SAME, WIDER when more. No value is chosen by frequency.")
STRUCTURAL = {name: text for name, text in lr.STRUCTURAL.items() if name != "reserve"}


def _dimension_values(source: dict, support: list):
    blood, _, crystalloid, lactate = lr._dimension_values(source, support)
    return blood, crystalloid, lactate


def identifiability(source: dict, support: list, filtered: dict, demand: dict, previous: dict) -> dict:
    blood, crystalloid, lactate = _dimension_values(source, support)
    n_lambda, n_support, n_p3 = len(LAMBDAS), len(support), len(source["p3"])
    explored, surviving = {}, {}

    def add(table, pairs, weight):
        for name, value in pairs:
            key = f"{value:g}" if isinstance(value, float) else str(value)
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
                     "p2i2ab": None if before is None else {"status": before["status"],
                                                            "surviving": before["surviving"]},
                     "change": change}
    return {"rule": IDENTIFIABILITY_RULE, "dimensions": out,
            "rho": {"status": RHO_STATUS, "band": list(RHO_BAND), "representative": RESERVE,
                    "synthetic_reference": RHO_SYNTHETIC_REFERENCE}}


REPRESENTATIVE_RULE = lr.REPRESENTATIVE_RULE
FLAG_RULES = lr.FLAG_RULES
DEBT_CHECK_RULE = ("Per minute of each representative run: (a) the core read a deficit > 0 (delivery at the start of the "
                   "minute against its demand) and D fell: must never happen; (b) the end-state deficit is > 0 and not "
                   "below the minute before's while D fell: reported; with constant demand it can only be the first "
                   "minute of a critical span (the minute began without a deficit: the integrator's start-of-minute "
                   "reading), never later.")


def interval_classes(deficit: list, bleed: list, settings: dict = SETTINGS) -> list:
    """Each reassessment interval: ADEQUATE when the deficit at its end is 0, else RECOVERING_CRITICAL or
    PERSISTENT_OR_WORSENING_CRITICAL, and whether blood was still being lost at its end (reported)."""
    step, end = settings["reassessment_interval_min"], len(deficit) - 1
    out = []
    for start in range(0, end, step):
        stop = min(start + step, end)
        label = lr.ADEQUATE if deficit[stop] == 0.0 else lr.classify_pair(deficit, start, stop)
        out.append([start, stop, label, bleed[stop] > 0.0])
    return out


def debt_checks(full: dict) -> dict:
    debt, deficit = full["D"], full["deficit"]
    own = Context(full["delivery"], full["demand"], full["bleed"], full["controlled_at"], full["stop"],
                  full["profile"].oxygen_extraction_reserve)
    core_read = [m + 1 for m, e in enumerate(own.debt_input) if e > 0.0 and debt[m + 1] < debt[m]]
    end_state = [m for m in range(1, len(debt)) if deficit[m] > 0.0 and deficit[m] >= deficit[m - 1]
                 and debt[m] < debt[m - 1]]
    return {"core_read_deficit_with_falling_d": core_read, "end_state_worsening_with_falling_d": end_state,
            "onset_minutes_only": all(deficit[m - 1] == 0.0 for m in end_state)}


def review(source: dict, support: list, arrivals: dict, tasks: dict, store: dict, picks: dict) -> dict:
    """P2I-2AC-5: the representatives re-run by the full core (demand 1.0, reserve 2.5), read at TIMES."""
    out = {}
    for tag, pick in picks.items():
        entry = source["p3"][pick["p3"]]
        item = {"pick": pick, "lambda": lr.lambda_label(pick["lambda"]), "blood": {
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
                                 "bleed_ml_per_min": full["bleed"][minute], "state": balance.state,
                                 "hb": state.hb, "shed_ml": state.blood.shed_ml,
                                 "transfused_ml": state.blood.transfused_ml})
                series = {"lactate": full["lactate"], "deficit": full["deficit"], "D": full["D"], "stop": full["stop"],
                          "output": full["output"], "hb": [state.hb for state, _ in full["views"]]}
                item["runs"][f"{case}|{scenario}"] = {
                    "rows": rows, "flags": lr._flags(series, scenario), "debt": debt_checks(full),
                    "intervals": interval_classes(full["deficit"], full["bleed"]),
                    "rerun_equals_factorized": lactate == full["lactate"] and debt == full["D"],
                    "controlled_at": full["controlled_at"], "stop": full["stop"]}
        out[tag] = item
    return out


# 9. Verdict, region and freeze -------------------------------------------------------------------------------------

READY, NOT_READY = "LACTATE_PHYSIOLOGY_READY_FOR_NEXT_DOMAIN", "LACTATE_PHYSIOLOGY_NOT_READY"
REGION_STATUS = lr.REGION_STATUS
VERDICT_RULE = ("LACTATE_PHYSIOLOGY_READY_FOR_NEXT_DOMAIN when every check holds: the P2I-2AB record is the committed "
                "one; the factorization agrees with the full core (D never falls under a deficit the core read); D is "
                "coherent in every representative run (never falls under a core-read deficit; any end-state "
                "exception is an onset minute); at least one candidate survives at demand 1.0; every survivor restores "
                "L3 adequacy in both cases; FD-LAC-04 is PASS or ALREADY_NORMALIZED and FD-LAC-05 PASS in both cases "
                "for every survivor (no definitive-management constraint met only as NOT_EVALUABLE); residual bleeding "
                "is read by actual flow (the L3 runs carry the flow after haemostasis and the validation reproduces it "
                "exactly); the demand layer classified every candidate; and no representative carries a patient-like "
                "flag (WORSENING_CRITICAL_WITH_LARGE_LACTATE_FALL, INSTANT_NORMALIZATION, INCOMPATIBLE_WITH_SURVIVAL). "
                "Otherwise LACTATE_PHYSIOLOGY_NOT_READY with the first blocker. No candidate, value or parameter is "
                "selected or approved.")
NEXT_DOMAIN = ("Recommended next domain (not started; needs its own authorization): 1. heart rate and the sympathetic "
               "response (faculty preference), then 2. pressure and vascular tone, on the faculty-constrained blood, "
               "crystalloid and lactate region, before collapse, GI migration or any runtime integration.")
INLINE_UNITS = lr.INLINE_UNITS
POLICY = ("Shadow only. The P2I-2AB current source space (its committed record), never the P2F historical region "
          "(P2FGuard). D is the core's corrected accumulated debt; FD-LAC-02..05 are faculty_constraints' frozen "
          "functions; FD-LAC-01 and 06 read the 2026-10-28 recovery semantics with windows from the actual flow; L3 "
          "adequacy is its own rejection. Demand 0.9 / 1.1 is reported uncertainty, 1.0 the region; rho is not counted. "
          "Haemodynamics are simulated once and D and lactate post-processed exactly (validated, else stop). The "
          "legacy lactate is read after the filter only. Nothing is fitted, selected or approved; no SBP, MAP or HR "
          "is calibrated; collapse stays off.")


def verdict(record_ok: bool, validation: dict, filtered: dict | None, statistics: dict | None, demand: dict | None,
            reviewed: dict | None) -> dict:
    checks = [("p2i2ab_record", record_ok, "the P2I-2AB record is not the committed one"),
              ("factorization", validation["agree"] and validation["no_debt_fall_in_deficit"],
               "the factorization does not agree with the full core")]
    if filtered is not None:
        runs = [run_ for item in (reviewed or {}).values() for run_ in item["runs"].values()]
        checks.append(("debt_coherent", bool(runs) and all(
            not r["debt"]["core_read_deficit_with_falling_d"] and r["debt"]["onset_minutes_only"]
            and r["rerun_equals_factorized"] for r in runs), "D falls under a deficit in a representative run"))
        survivors = filtered["survivors"]
        checks.append(("survivors", survivors > 0, "no candidate meets L3 adequacy and FD-LAC-01..06 jointly"))
        if statistics is not None and survivors:
            adequate = all("None" not in statistics["adequacy_onset"][c] for c in CASES)
            checks.append(("l3_adequacy", adequate, "a survivor does not restore L3 adequacy"))
            checks.append(("definitive_management_evaluable",
                           statistics["fd04_and_05_evaluated_in_both_cases"] == survivors,
                           "FD-LAC-04 / 05 are met only as NOT_EVALUABLE by some survivors"))
        flow = all(item["runs"][f"{case}|{L3}"]["controlled_at"] is not None and all(
            row["bleed_ml_per_min"] > 0.0 for row in item["runs"][f"{case}|{L3}"]["rows"] if row["minute"] > 60)
            for item in (reviewed or {}).values() for case in CASES)
        checks.append(("actual_flow", flow and validation["agree"],
                       "residual bleeding is not read from the actual flow"))
        checks.append(("demand_characterized", demand is not None and sum(demand["classes"].values()) ==
                       filtered["candidates"], "the demand layer did not classify every candidate"))
        flagged = [name for r in runs for name in ("WORSENING_CRITICAL_WITH_LARGE_LACTATE_FALL", "INSTANT_NORMALIZATION",
                                                   "INCOMPATIBLE_WITH_SURVIVAL") if r["flags"][name]]
        checks.append(("patient_like", bool(runs) and not flagged, "a representative carries a patient-like flag"))
    blockers = [why for _, passed, why in checks if not passed]
    return {"verdict": READY if not blockers and filtered is not None else
            f"{NOT_READY} — {blockers[0] if blockers else 'the filter did not run'}",
            "checks": {name: passed for name, passed, _ in checks}, "blockers": blockers, "rule": VERDICT_RULE,
            "next_domain": NEXT_DOMAIN if not blockers and filtered is not None else None}


def region_record(filtered: dict) -> dict:
    units = [[i, index, list(r), list(d)] for i, index, r, d in filtered["units"]]
    digest = hashlib.sha256(json.dumps(units, separators=(",", ":")).encode("utf-8")).hexdigest()
    return {"status": REGION_STATUS, "demand": PRIMARY_DEMAND, "units": len(units), "candidates": filtered["survivors"],
            "digest": digest, "inline": units if len(units) <= INLINE_UNITS else None,
            "format": "[P1 set, lactate-side index, [P3 sets], [crystalloid points]]"}


def compare_regions(record: dict, ids: set, n_support: int) -> dict:
    before = candidate_ids([(i, x, tuple(r), tuple(d)) for i, x, r, d in record["region"]["inline"]], n_support)
    return {"p2i2ab": len(before), "p2i2ac": len(ids), "kept": len(before & ids), "lost": len(before - ids),
            "new": len(ids - before)}


def design() -> dict:
    return {"faculty": FACULTY, "source": "P2I-2AB record (p1, p3, crystalloid support); digests " + P2I2AB_DIGEST,
            "lactate_side": {"points": lr.kinetic_points(), "levels": list(LEVELS),
                             "arrival_pairs": [list(p) for p in lr.ARRIVAL_PAIRS], "size": len(LAMBDAS),
                             "intrinsic": lr.INTRINSIC_RULE},
            "factorization": FACTORIZATION, "rules": RULES, "settings": SETTINGS,
            "l3": {"latest_onset": L3_LATEST_ONSET, "rule": ADEQUACY_RULE},
            "demand": {"factors": list(DEMAND_FACTORS), "primary": PRIMARY_DEMAND, "rule": DEMAND_RULE},
            "rho": {"band": list(RHO_BAND), "representative": RESERVE, "synthetic_reference": RHO_SYNTHETIC_REFERENCE,
                    "status": RHO_STATUS},
            "filter_order": [[s, list(n)] for s, n in FILTER_ORDER], "cost": COST_RATIONALE,
            "rejections": REJECTION_RULE, "validation": VALIDATION_RULE, "audit": AUDIT_RULE,
            "identifiability": IDENTIFIABILITY_RULE, "representatives": REPRESENTATIVE_RULE, "flags": FLAG_RULES,
            "debt_check": DEBT_CHECK_RULE, "legacy": lr.LEGACY_RULE, "verdict": VERDICT_RULE, "region": REGION_STATUS,
            "next_domain": NEXT_DOMAIN, "policy": POLICY}


def freeze_digest() -> str:
    record = hashlib.sha256(P2I2AB_RECORD.read_bytes()).hexdigest()
    text = json.dumps({"revision": REVISION, "records": {"P2I-2AB": record}, "design": design(), "lambdas": LAMBDAS,
                       "bits": {s: [list(b) for b in v] for s, v in BITS.items()}, "fd_lac": fd.definitions_digest(),
                       "thresholds": list(lr.FD04_THRESHOLDS), "histogram": lr.HISTOGRAM_STEP, "inline": INLINE_UNITS,
                       "tolerance": TOLERANCE, "canonical": CANONICAL, "sources": bf.freeze_sources()},
                      sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run(progress=None, map_=map) -> dict:
    say = progress or (lambda *_: None)
    with lr.P2FGuard(), lr.LegacyLock():
        record = record_p2i2ab()
        source, support = source_space(record), record["crystalloid_support"]
        arrivals = lr.arrival_table()
        say("haemodynamics")
        tasks = haemodynamic_tasks(source, support)
        store = haemodynamics(tasks, map_)
        say("factorization")
        validation = validate(source, support, arrivals, tasks, store, map_)
        out = {"freeze_digest": freeze_digest(), "decided": DECIDED, "revision": REVISION, "policy": POLICY,
               "faculty": FACULTY, "records": {"P2I-2AB": record["freeze_digest"]},
               "source": {"p1_sets": len(source["p1"]), "p3_sets": len(source["p3"]), "crystalloid_points": len(support),
                          "lactate_side": len(LAMBDAS), "reserves_on_the_blood_grid": sorted(
                              {r for e in source["p3"] for r in e["reserves"]})},
               "validation": {k: v for k, v in validation.items() if k != "sample"},
               "validation_sample": validation["sample"]}
        if not validation["agree"]:
            out["verdict"] = verdict(True, validation, None, None, None, None)
            return out
        say("audit")
        audit = audit_p2i2ab(record, source, arrivals, tasks, store, map_)
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
        ids = demand.pop("_ids")
        out.update({"audit": audit,
                    "filter": {f"{f:g}": {k: v for k, v in filtered[f].items() if k != "units"} for f in DEMAND_FACTORS},
                    "region": region_record(primary), "demand": demand,
                    "against_p2i2ab": compare_regions(record, ids[PRIMARY_DEMAND], len(support)),
                    "statistics": statistics,
                    "identifiability": identifiability(source, support, primary, demand,
                                                       record["identifiability"]["dimensions"]),
                    "representatives": reviewed,
                    "verdict": verdict(True, validation, primary, statistics, demand, reviewed)})
    out["legacy_reference"] = lr.legacy_reference(reviewed)
    evaluated = {f"{f:g}": filtered[f]["post_processed_units"] for f in DEMAND_FACTORS}
    out["efficiency"] = {
        "haemodynamic_trajectories": len(store), "validation_full_runs": validation["runs"],
        "representative_full_runs": sum(len(item["runs"]) for item in reviewed.values()),
        "naive_core_runs": primary["candidates"] * len(SCENARIOS) * len(CASES) * len(DEMAND_FACTORS),
        "post_processed_units": evaluated, "blood_rows_reused_from_p2i2ab": record["rows_computed"],
        "analytic_rejections": 0, "survivor_units": len(primary["units"])}
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
        (out / "lactate_adequacy.json").write_text(json.dumps(result, indent=1, sort_keys=True, default=str),
                                                   encoding="utf-8")
        print(out / "lactate_adequacy.json")
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
