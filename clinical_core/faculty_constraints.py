"""P2I-2R: the faculty-approved GI lactate behaviour constraints and their frozen operational tests.

Two different things live here, kept apart on purpose.

1. ``FACULTY_CLINICAL_CONSTRAINTS``: the faculty's decisions FD-LAC-01..06, status
   FACULTY_APPROVED, with the decision text and the faculty's later clarification verbatim. They
   constrain clinical BEHAVIOUR (what an observable lactate trajectory may do); they approve no
   hidden parameter value. They are not migration authority, not parameter provenance and not a
   calibration-registry status: the migration gate, its authority, the calibration registry and
   the bands never read this module (a test checks), and every hidden lactate/D parameter stays
   CANDIDATE. FD-LAC-05's 120-min envelopes are clinical calibration envelopes for the current GI
   cases, not universal human physiological limits.

2. The operationalization: how each statement becomes a deterministic test on a core trajectory.
   Where the faculty fixed it (``FACULTY_CONFIRMED_DEFINITIONS`` and the clarifications) it follows
   the faculty; the rest is PROPOSED by the shadow core. Its settings (``PRIMARY``), its
   one-at-a-time sensitivity design (``SENSITIVITY``) and the reporting rules are frozen before any
   candidate is filtered: the whole module is pinned by ``definitions_digest`` and the filter
   refuses to run on another digest.

P2I-2R (2026-10-26) replaces P2I-2's operationalization of FD-LAC-01, FD-LAC-04 and FD-LAC-05 by the
faculty's clarification of the statements it had already approved. It is not a rule chosen from
P2I-2's result (66 survivors): the faculty's text decides each change, quoted below.

Everything is read from the shadow core's own trajectory: lactate, effective oxygen delivery,
oxygen demand, D and the minute its GI module records haemostasis. The family engine's lactate
is never an input. D and lactate stay distinct: D is never used as a stand-in for delivery, and
lactate is never read as a deterministic surrogate of delivery: it keeps its own production and
clearance dynamics.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

#: The status of a faculty clinical constraint. It approves behaviour, not a parameter value.
FACULTY_APPROVED = "FACULTY_APPROVED"
DECIDED = "2026-10-25"
CLARIFIED = "2026-10-26"
VERSION = "FD-LAC v2"
CASE_57M, CASE_72F = "gi_bleed_57m", "gi_bleed_72f"
CASES = (CASE_57M, CASE_72F)
#: Only engine-produced trajectories enter the constraints (P2I-1); L4, a manual counterfactual
#: composition, never does.
UNTREATED, PARTIAL, DEFINITIVE = "L1", "L2", "L3"
#: The hidden parameters these constraints bear on. None of them is approved by them.
HIDDEN_PARAMETERS = ("arrival_oxygen_debt", "arrival_lactate_excess", "debt_clearance_tau_min",
                     "debt_per_delivery_deficit", "lactate_per_output_deficit", "lactate_clearance_tau_min",
                     "arrival_delivery_ratio", "metabolic_demand_baseline")
NOT_A_PARAMETER_APPROVAL = ("Approves a clinical behaviour of the lactate observable. Approves no hidden parameter "
                            "value: arrival_oxygen_debt, arrival_lactate_excess, tau_D, tau_lactate, the D-to-lactate "
                            "gain and the deficit-to-D gain stay CANDIDATE.")
#: The outcome of one constraint for one run.
PASS, FAIL, NOT_APPLICABLE, NOT_EVALUABLE, ALREADY_NORMALIZED = (
    "PASS", "FAIL", "NOT_APPLICABLE", "NOT_EVALUABLE", "ALREADY_NORMALIZED")


@dataclass(frozen=True)
class ClinicalConstraint:
    """One faculty decision on clinical behaviour, as decided and as clarified (both verbatim)."""

    id: str
    title: str
    decision: str
    rationale: str
    observable: str
    scenarios: tuple
    cases: tuple
    clarification: str = ""
    status: str = FACULTY_APPROVED
    decided: str = DECIDED
    clarified: str = ""
    version: str = VERSION
    approves_parameter_values: tuple = ()
    scope_note: str = NOT_A_PARAMETER_APPROVAL


FACULTY_CLINICAL_CONSTRAINTS = (
    ClinicalConstraint(
        "FD-LAC-01", "Untreated active bleeding",
        "With ongoing active haemorrhage and persistently inadequate/worsening oxygen delivery, lactate should "
        "GENERALLY RISE. A brief period of stability is acceptable. A sustained fall should NOT be the typical "
        "trajectory when oxygen delivery remains inadequate. Do NOT interpret this as: \"lactate must rise every "
        "minute.\" The clinically important requirement is the trajectory over meaningful reassessment intervals.",
        "The clinically important requirement is the trajectory over meaningful reassessment intervals.",
        "lactate trajectory before 60 min while bleeding is active and oxygen delivery is inadequate",
        (UNTREATED,), CASES,
        clarification=(
            "Do NOT encode: L60 >= L0 as a universal physiological law. Faculty intent is: With active haemorrhage "
            "AND persistent/significant inadequate oxygen delivery, a substantial sustained fall in lactate should "
            "not be the dominant/acceptable trajectory. Lactate should generally remain elevated or rise. The "
            "case-specific 60-min clinical envelopes remain: 57m: 4.4-7.0 mmol/L 72f: 3.4-5.5 mmol/L These envelopes "
            "are the hard 60-min clinical constraints. For the trajectory before 60 min: retain the approved rule "
            "against a sustained substantial decline during persistent inadequate delivery. Do not require monotonic "
            "rise. Do not require a fixed percentage increase. Do not treat a small transient decrease as "
            "automatically physiologically invalid. Operationalize \"substantial sustained decline\" using the "
            "previously frozen clinically meaningful reassessment-window concept and expose sensitivity to the "
            "chosen percentage threshold."),
        clarified=CLARIFIED),
    ClinicalConstraint(
        "FD-LAC-02", "GI 57M, 60 min untreated",
        "APPROVED clinical band: arrival lactate: 4.4 mmol/L. 60-min untreated acceptable band: 4.4-7.0 mmol/L. "
        "Preferred direction: stable-to-rising, usually rising. Do NOT convert the midpoint of this band into a "
        "target. Values are a clinical acceptance envelope.",
        "Values are a clinical acceptance envelope.",
        "lactate (mmol/L) at 60 min untreated", (UNTREATED,), (CASE_57M,)),
    ClinicalConstraint(
        "FD-LAC-03", "GI 72F, 60 min untreated",
        "APPROVED clinical band: arrival lactate: 3.4 mmol/L. 60-min untreated acceptable band: 3.4-5.5 mmol/L. "
        "Preferred direction: stable-to-rising, usually rising. Again, this is a clinical envelope, not a point "
        "target.",
        "Again, this is a clinical envelope, not a point target.",
        "lactate (mmol/L) at 60 min untreated", (UNTREATED,), (CASE_72F,)),
    ClinicalConstraint(
        "FD-LAC-04", "Response after definitive management",
        "After successful haemostasis AND adequate sustained restoration of oxygen delivery, a CLEAR downward "
        "lactate trend should begin within: 15-30 minutes. This means onset of a meaningful downward trend. It "
        "does NOT mean: normalization by 30 minutes; arbitrary fixed mmol/L decline; clearance independent of "
        "accumulated debt.",
        "This means onset of a meaningful downward trend.",
        "lactate at T* + 30 min against T*, after haemostasis and sustained adequate delivery",
        (DEFINITIVE,), CASES,
        clarification=(
            "T* = the later of: A. haemostasis B. onset of adequate oxygen delivery that remains adequate for the "
            "required sustained period. Lactate may already be falling before T*; do not require a new peak after "
            "T*; do not reset physiology at haemostasis; use L(T*) as the reference; if the run does not provide "
            "30 min of follow-up, mark NOT_EVALUABLE; if oxygen delivery ceases to be adequate during the 30-min "
            "interval, mark NOT_EVALUABLE rather than FAIL. Do NOT require: L(T* + 30) <= 0.90 * L(T*) as a "
            "faculty-approved physiological constant. Faculty intent is: After haemostasis AND sustained adequate "
            "restoration of oxygen delivery, a clearly downward lactate trajectory should be evident within 30 "
            "minutes. Therefore: by T* + 30 min: L(T* + 30) < L(T*) with a trajectory consistent with ongoing "
            "clearance. A fixed 10% reduction at 30 min is NOT yet faculty-approved. Report the actual percentage "
            "reduction at 30 min for each surviving candidate. Then separately evaluate candidate thresholds such "
            "as: any decrease, >=5%, >=10%, >=15% as SENSITIVITY ANALYSIS ONLY. If L(T*) <= 2.0 mmol/L: classify "
            "ALREADY_NORMALIZED and satisfy/not-applicable."),
        clarified=CLARIFIED),
    ClinicalConstraint(
        "FD-LAC-05", "120 min after successful management",
        "Residual lactate at 120 min should depend materially on accumulated oxygen debt. Typical severe-shock "
        "trajectories may remain MILDLY ELEVATED. Do NOT require full normalization within 120 minutes. Do NOT "
        "encode one fixed 120-min lactate target. The model should preserve memory of prior debt.",
        "The model should preserve memory of prior debt.",
        "lactate (mmol/L) at 120 min after definitive management with sustained adequate delivery",
        (DEFINITIVE,), CASES,
        clarification=(
            "Faculty now approves case-specific 120-min clinical envelopes after successful definitive management "
            "with sustained adequate oxygen delivery. 57m: 1.5 <= L120 <= 4.0 mmol/L 72f: 1.2 <= L120 <= 3.5 mmol/L "
            "Additionally: L120 < L(T*) must hold when adequate oxygen delivery remained sustained after T*. These "
            "are clinical acceptance envelopes, NOT target values. Do not tune toward the midpoint. A value below 2 "
            "mmol/L is allowed. Normalization by 120 min is NOT required. Treat these as faculty clinical "
            "calibration envelopes for the current GI cases, not universal human physiological limits."),
        clarified=CLARIFIED),
    ClinicalConstraint(
        "FD-LAC-06", "Active bleeding with falling lactate",
        "ONLY IF OXYGEN DELIVERY IS ADEQUATE. Active haemorrhage by itself does not require lactate to rise. If "
        "resuscitation maintains/restores adequate oxygen delivery despite ongoing bleeding, lactate may fall. "
        "However: active bleeding + persistent/worsening inadequate oxygen delivery must NOT produce a sustained "
        "declining lactate trajectory. This rule takes precedence over diagnosis labels.",
        "This rule takes precedence over diagnosis labels.",
        "lactate trajectory while bleeding is active, by oxygen-delivery adequacy",
        (UNTREATED, PARTIAL, DEFINITIVE), CASES),
)
CONSTRAINT_IDS = tuple(item.id for item in FACULTY_CLINICAL_CONSTRAINTS)
#: The operational definitions the faculty confirmed (2026-10-26), verbatim.
FACULTY_CONFIRMED_DEFINITIONS = (
    "inadequate delivery = oxygen delivery < oxygen demand",
    "evaluation should use clinically meaningful reassessment intervals rather than minute-to-minute noise",
    "sustained decline during inadequate delivery may be operationalized as a >=10% decline over a >=30-min interval",
    "FD-LAC-06 applies according to physiology, not diagnosis label",
    "active bleeding may coexist with falling lactate ONLY when delivery is adequate",
    "D and lactate remain distinct state/observable concepts",
    "arrival need not be steady state",
)
#: FD-LAC-02/03: the approved envelopes, inclusive, at 60 min untreated; and the arrival lactate
#: each decision states (checked against repository truth).
ENVELOPES = {CASE_57M: {"constraint": "FD-LAC-02", "arrival": 4.4, "minute": 60, "low": 4.4, "high": 7.0},
             CASE_72F: {"constraint": "FD-LAC-03", "arrival": 3.4, "minute": 60, "low": 3.4, "high": 5.5}}
#: FD-LAC-05: the approved 120-min envelopes, inclusive, after definitive management with sustained
#: adequate delivery (clinical calibration envelopes for these cases, not targets).
ENVELOPES_120 = {CASE_57M: {"minute": 120, "low": 1.5, "high": 4.0},
                 CASE_72F: {"minute": 120, "low": 1.2, "high": 3.5}}


# The operationalization (frozen before filtering) ---------------------------------------------

#: Primary settings. Their rationale is in docs/revision/P2I2_RESTRICCIONES_LACTATO_GI.md §2.
PRIMARY = {
    # Delivery is adequate when it meets demand (faculty-confirmed: inadequate = delivery < demand).
    # A tolerance of e counts delivery >= (1 - e) x demand as adequate (sensitivity only).
    "adequacy_tolerance": 0.0,
    # The reassessment grid (min): a window is judged at its two ends and at every multiple of this.
    "reassessment_interval_min": 15,
    # A substantial sustained decline (faculty-confirmed): two reassessment points at least
    # ``sustained_min`` apart, the later lactate at least ``meaningful_change`` below the earlier.
    "meaningful_change": 0.10,
    "sustained_min": 30,
    # FD-LAC-01 judges the untreated trajectory up to this minute (the faculty's "before 60 min").
    "fd01_until_min": 60,
    # FD-LAC-01: a run with no window to judge is NOT_APPLICABLE; True counts it as not contradicting it.
    "fd01_unapplicable_passes": True,
    # FD-LAC-02/03 and FD-LAC-05 sensitivity only: compare the value as displayed (None: exact).
    "fd0203_display_decimals": None,
    "fd05_display_decimals": None,
    # FD-LAC-04: delivery that stays adequate this long is "sustained" (B of T*).
    "fd04_sustained_restoration_min": 30,
    # FD-LAC-04: the follow-up after T* (the faculty's 30 min).
    "fd04_window_min": 30,
    # FD-LAC-04: the fall required by T* + 30. 0: any decrease, L(T* + 30) < L(T*) (the faculty's rule);
    # 0.05, 0.10, 0.15 are sensitivity only and never select candidates.
    "fd04_required_fall": 0.0,
    # FD-LAC-04: "consistent with ongoing clearance": still falling over the last reassessment interval,
    # L(T* + 30) <= L(T* + 30 - interval). False drops it (sensitivity only).
    "fd04_ongoing_clearance": True,
    # FD-LAC-04: at or below this (mmol/L) at T* the lactate is ALREADY_NORMALIZED (faculty: 2.0).
    "already_normalized_mmol_l": 2.0,
    # FD-LAC-04: NOT_EVALUABLE counts as not contradicting the constraint (faculty: NOT_EVALUABLE, not FAIL).
    "fd04_unevaluable_passes": True,
    # FD-LAC-05 reads minute 120 of the definitive-management run (management starts at minute 0).
    "fd05_minute": 120,
    # FD-LAC-05: L120 < L(T*) is required as the faculty wrote it; True exempts an ALREADY_NORMALIZED
    # L(T*) from it (sensitivity only).
    "fd05_normalized_exception": False,
    # FD-LAC-05: without sustained adequate delivery from T* to 120 min its premise does not hold:
    # NOT_EVALUABLE, counted as not contradicting it.
    "fd05_unevaluable_passes": True,
    # FD-LAC-05 verification only (never filters): the debt memory a severe arrival debt leaves at
    # 120 min, the upper end of P2F's arrival-debt band (60, both cases).
    "fd05_reference_debt": 60.0,
}
#: One-at-a-time sensitivity around PRIMARY, frozen with it. Each variant changes one setting and
#: none of them selects candidates.
SENSITIVITY = {
    "decline threshold 5 %": {"meaningful_change": 0.05},
    "decline threshold 15 %": {"meaningful_change": 0.15},
    "decline threshold 20 %": {"meaningful_change": 0.20},
    "adequacy tolerance 5 %": {"adequacy_tolerance": 0.05},
    "adequacy tolerance 10 %": {"adequacy_tolerance": 0.10},
    "reassessment every 10 min": {"reassessment_interval_min": 10},
    "reassessment every 30 min": {"reassessment_interval_min": 30},
    "sustained over 15 min": {"sustained_min": 15},
    "sustained over 45 min": {"sustained_min": 45},
    "sustained over 60 min": {"sustained_min": 60},
    "FD-LAC-01 not applicable counts as failing": {"fd01_unapplicable_passes": False},
    "FD-LAC-02/03 as displayed (1 decimal)": {"fd0203_display_decimals": 1},
    "FD-LAC-04 fall >= 5 % by T*+30": {"fd04_required_fall": 0.05},
    "FD-LAC-04 fall >= 10 % by T*+30": {"fd04_required_fall": 0.10},
    "FD-LAC-04 fall >= 15 % by T*+30": {"fd04_required_fall": 0.15},
    "FD-LAC-04 without the ongoing-clearance check": {"fd04_ongoing_clearance": False},
    "FD-LAC-04 delivery sustained 15 min": {"fd04_sustained_restoration_min": 15},
    "FD-LAC-04 delivery sustained 60 min": {"fd04_sustained_restoration_min": 60},
    "FD-LAC-04 not evaluable counts as failing": {"fd04_unevaluable_passes": False},
    "FD-LAC-05 as displayed (1 decimal)": {"fd05_display_decimals": 1},
    "FD-LAC-05 decline not required when already normalized": {"fd05_normalized_exception": True},
    "FD-LAC-05 not evaluable counts as failing": {"fd05_unevaluable_passes": False},
}
#: FD-LAC-04's reductions at 30 min are reported against these thresholds, for information only.
REPORTED_FALL_THRESHOLDS = (0.0, 0.05, 0.10, 0.15)
#: Frozen: how a factor's identifiability is classified from the surviving region. A factor not
#: varied by the region, or whose surviving level shares all stay within this many points of the
#: region's, is NOT IDENTIFIED; all levels surviving with a larger shift is POORLY IDENTIFIED; some
#: level eliminated is PARTIALLY CONSTRAINED; one level left is WELL CONSTRAINED (within the explored
#: grid). The most common surviving level is never singled out.
IDENTIFIABILITY_SHIFT = 0.05
#: Frozen representatives: among the candidates that satisfy all six, per case, the lowest, median
#: and highest of the untreated lactate at 60 min, and of the definitive-management lactate at
#: 120 min (ties broken by candidate key).
REPRESENTATIVE_POSITIONS = ("lowest", "median", "highest")


def params(**overrides) -> dict:
    unknown = set(overrides) - set(PRIMARY)
    if unknown:
        raise KeyError(f"not an operational setting: {sorted(unknown)}")
    return {**PRIMARY, **overrides}


@dataclass(frozen=True)
class Trajectory:
    """One shadow-core run as the constraints read it, minute by minute from arrival (0).

    ``delivery`` is the effective oxygen delivery of each minute's end state and ``demand`` that
    minute's oxygen demand, both in the core's units; ``controlled_at`` is the minute the core's
    GI module records haemostasis (None: bleeding never controlled). Bleeding is active before it.
    """

    lactate: tuple
    D: tuple
    delivery: tuple
    demand: tuple
    controlled_at: int | None = None

    def __post_init__(self):
        lengths = {len(self.lactate), len(self.D), len(self.delivery), len(self.demand)}
        if len(lengths) != 1 or not self.lactate:
            raise ValueError("a trajectory has one value per minute in every series")

    @property
    def end(self) -> int:
        return len(self.lactate) - 1

    def bleeding(self, minute: int) -> bool:
        return self.controlled_at is None or minute < self.controlled_at


def adequate(trajectory: Trajectory, minute: int, settings: dict) -> bool:
    """Oxygen delivery meets demand (within the adequacy tolerance) at the end of ``minute``."""
    return trajectory.delivery[minute] >= (1.0 - settings["adequacy_tolerance"]) * trajectory.demand[minute]


def spans(trajectory: Trajectory, predicate) -> list:
    """The maximal runs of consecutive minutes where ``predicate(minute)`` holds, as (first, last)."""
    found, start = [], None
    for minute in range(trajectory.end + 1):
        if predicate(minute):
            start = minute if start is None else start
        elif start is not None:
            found.append((start, minute - 1))
            start = None
    if start is not None:
        found.append((start, trajectory.end))
    return found


def inadequate_bleeding_windows(trajectory: Trajectory, settings: dict) -> list:
    """Persistent inadequate delivery with active bleeding: every maximal span of minutes in which
    bleeding is active and delivery is inadequate at every minute."""
    return spans(trajectory, lambda minute: trajectory.bleeding(minute) and not adequate(trajectory, minute, settings))


def reassessments(first: int, last: int, settings: dict) -> list:
    """The reassessment points of a window: its two ends and every multiple of the interval inside."""
    interval = settings["reassessment_interval_min"]
    return sorted({first, last} | {minute for minute in range(first, last + 1) if minute % interval == 0})


def sustained_declines(trajectory: Trajectory, first: int, last: int, settings: dict) -> list:
    """A substantial sustained decline inside a window: two reassessment points at least
    ``sustained_min`` apart with the later lactate at least ``meaningful_change`` below the earlier.
    A smaller or shorter decrease is not one."""
    points, change, span = reassessments(first, last, settings), settings["meaningful_change"], settings["sustained_min"]
    lactate = trajectory.lactate
    return [(early, late) for index, early in enumerate(points) for late in points[index + 1:]
            if late - early >= span and lactate[late] <= (1.0 - change) * lactate[early]]


def fd_lac_01(untreated: Trajectory, settings: dict) -> dict:
    """FD-LAC-01 on the untreated run, before ``fd01_until_min``: in every part of a window of active
    bleeding with inadequate delivery that lies before that minute and lasts at least
    ``sustained_min``, no substantial sustained decline. No rise, no fixed percentage increase and no
    L60 >= L0 is required (the 60-min value is FD-LAC-02/03's envelope). No such part: NOT_APPLICABLE."""
    until, windows = settings["fd01_until_min"], []
    for first, last in inadequate_bleeding_windows(untreated, settings):
        if first > until:
            continue
        last = min(last, until)
        if last - first < settings["sustained_min"]:
            continue
        declines = sustained_declines(untreated, first, last, settings)
        windows.append({"window": [first, last], "sustained_declines": len(declines),
                        "first_decline": list(declines[0]) if declines else None, "passes": not declines})
    if not windows:
        return {"status": NOT_APPLICABLE, "applicable": False, "passes": settings["fd01_unapplicable_passes"],
                "windows": []}
    passes = all(item["passes"] for item in windows)
    return {"status": PASS if passes else FAIL, "applicable": True, "passes": passes, "windows": windows}


def _shown(value: float, decimals) -> float:
    return value if decimals is None else round(value, decimals)


def fd_lac_envelope(untreated: Trajectory, case: str, settings: dict) -> dict:
    """FD-LAC-02/03: the hard envelope at 60 min untreated, inclusive. A run that ends before the
    minute has no value and fails. Never a distance to the band's midpoint."""
    envelope = ENVELOPES[case]
    minute = envelope["minute"]
    if untreated.end < minute:
        return {"status": FAIL, "value": None, "passes": False}
    value = untreated.lactate[minute]
    shown = _shown(value, settings["fd0203_display_decimals"])
    passes = envelope["low"] <= shown <= envelope["high"]
    return {"status": PASS if passes else FAIL, "value": value, "compared": shown, "passes": passes}


def restoration_trigger(definitive: Trajectory, settings: dict) -> int | None:
    """T* = the later of (A) haemostasis and (B) the onset of adequate delivery that remains adequate
    for ``fd04_sustained_restoration_min``: the first such span still in progress at or after
    haemostasis. None without haemostasis or without such a span."""
    haemostasis, hold = definitive.controlled_at, settings["fd04_sustained_restoration_min"]
    if haemostasis is None:
        return None
    for first, last in spans(definitive, lambda minute: adequate(definitive, minute, settings)):
        if last - first >= hold and last >= haemostasis:
            return max(haemostasis, first)
    return None


def fd_lac_04(definitive: Trajectory, settings: dict) -> dict:
    """FD-LAC-04 on the definitive-management run, timed from T* with L(T*) as the reference.

    - No T*: NOT_EVALUABLE.
    - L(T*) <= ``already_normalized_mmol_l``: ALREADY_NORMALIZED (satisfied; no further fall required).
    - Less than ``fd04_window_min`` of follow-up after T*, or delivery not adequate at every minute
      of it: NOT_EVALUABLE (never FAIL).
    - Otherwise PASS when L(T* + 30) < L(T*) (by at least ``fd04_required_fall``, 0 by default) and
      the trajectory is consistent with ongoing clearance: still falling over the last reassessment
      interval. The lactate may already be falling before T*; no new peak is required."""
    trigger = restoration_trigger(definitive, settings)
    base = {"haemostasis": definitive.controlled_at, "trigger": trigger}
    unevaluable = settings["fd04_unevaluable_passes"]
    if trigger is None:
        return {**base, "status": NOT_EVALUABLE, "reason": "no haemostasis with sustained adequate delivery",
                "passes": unevaluable}
    lactate, window = definitive.lactate, settings["fd04_window_min"]
    at = lactate[trigger]
    if at <= settings["already_normalized_mmol_l"]:
        return {**base, "status": ALREADY_NORMALIZED, "at_trigger": at, "passes": True}
    if trigger + window > definitive.end:
        return {**base, "status": NOT_EVALUABLE, "reason": "less than 30 min of follow-up after T*",
                "at_trigger": at, "passes": unevaluable}
    if not all(adequate(definitive, minute, settings) for minute in range(trigger, trigger + window + 1)):
        return {**base, "status": NOT_EVALUABLE, "reason": "delivery ceased to be adequate within 30 min of T*",
                "at_trigger": at, "passes": unevaluable}
    later = lactate[trigger + window]
    before_end = lactate[trigger + window - settings["reassessment_interval_min"]]
    reduction = (at - later) / at
    falls = later < at and reduction >= settings["fd04_required_fall"]
    ongoing = later <= before_end if settings["fd04_ongoing_clearance"] else True
    passes = falls and ongoing
    return {**base, "status": PASS if passes else FAIL, "at_trigger": at, "at_trigger_plus_window": later,
            "reduction_at_window": reduction, "falls": falls, "ongoing_clearance": ongoing, "passes": passes}


def debt_memory_coefficient(tau_debt: float, tau_lactate: float, gain: float, minutes: int) -> float:
    """The lactate (mmol/L) still attributable, ``minutes`` after arrival, to one unit of arrival D:
    the exact arrival-debt term of the core's recurrences (D repaid with tau_D, X produced with
    k = G / (tau_D tau_L) from the minute before's D and cleared with tau_L). It does not depend on
    delivery: restored flow does not erase it."""
    production, keep_debt, keep_excess = gain / (tau_debt * tau_lactate), 1.0 - 1.0 / tau_debt, 1.0 - 1.0 / tau_lactate
    debt, excess = 1.0, 0.0
    for _ in range(minutes):
        debt, excess = debt * keep_debt, excess * keep_excess + production * debt
    return excess


def fd_lac_05(definitive: Trajectory, trigger: int | None, kinetics: dict, arrival_lactate: float,
              settings: dict, case: str) -> dict:
    """FD-LAC-05 after definitive management with sustained adequate delivery: from T* through
    ``fd05_minute`` delivery adequate at every minute (otherwise NOT_EVALUABLE). Then the lactate at
    ``fd05_minute`` lies in the case's envelope (inclusive) and is below L(T*). Normalization is never
    required and the envelope is never a target. The debt memory (the lactate a severe arrival debt
    still leaves at 120 min) is reported, never filtered on."""
    coefficient = debt_memory_coefficient(kinetics["debt_clearance_tau_min"], kinetics["lactate_clearance_tau_min"],
                                          kinetics["lactate_per_output_deficit"], settings["fd05_minute"])
    memory = {"debt_memory_at_reference_debt": settings["fd05_reference_debt"] * coefficient,
              "memory_per_unit_debt": coefficient, "arrival_lactate": arrival_lactate}
    minute, envelope = settings["fd05_minute"], ENVELOPES_120[case]
    unevaluable = settings["fd05_unevaluable_passes"]
    if trigger is None or definitive.end < minute:
        return {**memory, "status": NOT_EVALUABLE, "reason": "no T* within the run", "passes": unevaluable}
    if not all(adequate(definitive, later, settings) for later in range(trigger, minute + 1)):
        return {**memory, "status": NOT_EVALUABLE, "reason": "delivery not adequate throughout from T* to 120 min",
                "passes": unevaluable}
    value, at = definitive.lactate[minute], definitive.lactate[trigger]
    shown = _shown(value, settings["fd05_display_decimals"])
    inside = envelope["low"] <= shown <= envelope["high"]
    exempt = settings["fd05_normalized_exception"] and at <= settings["already_normalized_mmol_l"]
    below = value < at or exempt
    passes = inside and below
    return {**memory, "status": PASS if passes else FAIL, "residual": value, "compared": shown, "at_trigger": at,
            "inside_envelope": inside, "below_trigger": below, "passes": passes}


def fd_lac_06(runs: dict, settings: dict) -> dict:
    """FD-LAC-06 on every engine-produced run of a case (untreated, partial, definitive): no
    substantial sustained decline inside any window of active bleeding with inadequate delivery at
    least ``sustained_min`` long. A fall while delivery is adequate is allowed, bleeding or not."""
    violations = []
    for scenario, trajectory in sorted(runs.items()):
        for first, last in inadequate_bleeding_windows(trajectory, settings):
            if last - first < settings["sustained_min"]:
                continue
            declines = sustained_declines(trajectory, first, last, settings)
            if declines:
                violations.append({"scenario": scenario, "window": [first, last], "first_decline": list(declines[0]),
                                   "sustained_declines": len(declines)})
    return {"status": FAIL if violations else PASS, "violations": violations, "passes": not violations}


def evaluate(runs: dict, kinetics: dict, arrival_lactate: dict, settings: dict) -> dict:
    """All six for one candidate: ``runs[case][scenario]`` are its trajectories. A constraint that
    applies to both cases must hold in both."""
    detail = {case: {} for case in runs}
    for case, by_scenario in runs.items():
        detail[case]["FD-LAC-01"] = fd_lac_01(by_scenario[UNTREATED], settings)
        detail[case][ENVELOPES[case]["constraint"]] = fd_lac_envelope(by_scenario[UNTREATED], case, settings)
        response = fd_lac_04(by_scenario[DEFINITIVE], settings)
        detail[case]["FD-LAC-04"] = response
        detail[case]["FD-LAC-05"] = fd_lac_05(by_scenario[DEFINITIVE], response["trigger"], kinetics,
                                              arrival_lactate[case], settings, case)
        detail[case]["FD-LAC-06"] = fd_lac_06(by_scenario, settings)
    verdict = {}
    for item in FACULTY_CLINICAL_CONSTRAINTS:
        verdict[item.id] = all(detail[case][item.id]["passes"] for case in item.cases if case in detail)
    return {"passes": verdict, "all": all(verdict.values()), "detail": detail}


def identifiability(region_shares: dict, surviving_shares: dict, varied: bool) -> str:
    """The frozen rule (see IDENTIFIABILITY_SHIFT), from a factor's level shares."""
    if not varied:
        return "NOT IDENTIFIED"
    if not surviving_shares:
        return "NOT ASSESSABLE (no survivors)"
    left = [level for level, share in surviving_shares.items() if share > 0]
    if len(left) == 1:
        return "WELL CONSTRAINED"
    if len(left) < len([level for level, share in region_shares.items() if share > 0]):
        return "PARTIALLY CONSTRAINED"
    if all(abs(surviving_shares.get(level, 0.0) - share) <= IDENTIFIABILITY_SHIFT
           for level, share in region_shares.items()):
        return "NOT IDENTIFIED"
    return "POORLY IDENTIFIED"


def definitions_digest() -> str:
    """This whole module, by hash: the decisions and clarifications, the operational tests, their
    settings, the sensitivity design and the reporting rules. Frozen before any candidate is filtered."""
    return hashlib.sha256(Path(__file__).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
