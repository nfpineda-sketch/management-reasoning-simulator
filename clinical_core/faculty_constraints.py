"""P2I-2: the faculty-approved GI lactate behaviour constraints and their frozen operational tests.

Two different things live here, kept apart on purpose.

1. ``FACULTY_CLINICAL_CONSTRAINTS``: the faculty's decisions FD-LAC-01..06, status
   FACULTY_APPROVED, with the decision text verbatim. They constrain clinical BEHAVIOUR (what an
   observable lactate trajectory may do); they approve no hidden parameter value. They are not
   migration authority, not parameter provenance and not a calibration-registry status: the
   migration gate, its authority, the calibration registry and the bands never read this module
   (a test checks), and every hidden lactate/D parameter stays CANDIDATE.

2. The operationalization: how each qualitative phrase becomes a deterministic test on a core
   trajectory. It is PROPOSED by the shadow core, not faculty-approved. Its thresholds
   (``PRIMARY``), its one-at-a-time sensitivity design (``SENSITIVITY``) and the reporting rules
   (identifiability, representatives) are frozen before any candidate is filtered: the whole
   module is pinned by ``definitions_digest`` and the filter refuses to run on another digest.

Everything is read from the shadow core's own trajectory: lactate, effective oxygen delivery,
oxygen demand, D and the minute its GI module records haemostasis. The family engine's lactate
is never an input. D is never used as a stand-in for delivery: "inadequate delivery" means
delivery below demand, whatever D does.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

#: The status of a faculty clinical constraint. It approves behaviour, not a parameter value.
FACULTY_APPROVED = "FACULTY_APPROVED"
DECIDED = "2026-10-25"
VERSION = "FD-LAC v1"
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


@dataclass(frozen=True)
class ClinicalConstraint:
    """One faculty decision on clinical behaviour, as decided (the decision text is verbatim)."""

    id: str
    title: str
    decision: str
    rationale: str
    observable: str
    scenarios: tuple
    cases: tuple
    status: str = FACULTY_APPROVED
    decided: str = DECIDED
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
        "lactate trajectory while bleeding is active and oxygen delivery is inadequate", (UNTREATED,), CASES),
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
        "onset of a clear downward lactate trend after haemostasis and sustained restoration of delivery",
        (DEFINITIVE,), CASES),
    ClinicalConstraint(
        "FD-LAC-05", "120 min after successful management",
        "Residual lactate at 120 min should depend materially on accumulated oxygen debt. Typical severe-shock "
        "trajectories may remain MILDLY ELEVATED. Do NOT require full normalization within 120 minutes. Do NOT "
        "encode one fixed 120-min lactate target. The model should preserve memory of prior debt.",
        "The model should preserve memory of prior debt.",
        "residual lactate at 120 min after definitive management and its dependence on accumulated oxygen debt",
        (DEFINITIVE,), CASES),
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
#: FD-LAC-02/03: the approved envelopes, inclusive, at 60 min untreated; and the arrival lactate
#: each decision states (checked against repository truth).
ENVELOPES = {CASE_57M: {"constraint": "FD-LAC-02", "arrival": 4.4, "minute": 60, "low": 4.4, "high": 7.0},
             CASE_72F: {"constraint": "FD-LAC-03", "arrival": 3.4, "minute": 60, "low": 3.4, "high": 5.5}}


# The operationalization (PROPOSED, not faculty-approved; frozen before filtering) -------------

#: Primary thresholds. Each one's clinical rationale is in docs/revision/P2I2_RESTRICCIONES_LACTATO_GI.md §2.
PRIMARY = {
    # A clinically meaningful change: 10 % of the reference value (the conventional threshold for a
    # meaningful lactate change, as in "lactate clearance >= 10 %"). Relative, never a fixed mmol/L.
    "meaningful_change": 0.10,
    # Delivery is adequate when it meets demand (the model's own boundary: below it, new oxygen debt
    # accrues). A tolerance of e counts delivery >= (1 - e) x demand as adequate.
    "adequacy_tolerance": 0.0,
    # The reassessment grid (min): the trajectory is judged at the window's ends and at every multiple.
    "reassessment_interval_min": 15,
    # A decline is sustained when it persists over at least this span (two reassessment intervals).
    "sustained_min": 30,
    # FD-LAC-01 needs at least this long a window of active bleeding with inadequate delivery.
    "fd01_min_window_min": 60,
    # FD-LAC-01: a run with no such window is NOT APPLICABLE; True counts it as not contradicting it.
    "fd01_unapplicable_passes": True,
    # FD-LAC-01 sensitivity only: the stable phase must end, upward, within this many minutes (None: off).
    "fd01_brief_stability_min": None,
    # FD-LAC-02/03 sensitivity only: compare the value as displayed to this many decimals (None: exact).
    "fd0203_display_decimals": None,
    # FD-LAC-04: the clear downward trend begins no later than this after the trigger ...
    "fd04_onset_limit_min": 30,
    # ... and no earlier than this (0: an earlier onset, or a decline already under way, is accepted).
    "fd04_onset_floor_min": 0,
    # FD-LAC-04: restoration is sustained when delivery stays adequate for this long from the trigger.
    "fd04_sustained_restoration_min": 30,
    # FD-LAC-04: at least this much observation after the trigger, or the run cannot show the response.
    "fd04_observation_after_trigger_min": 60,
    # FD-LAC-04: a lactate at or below this (mmol/L, the upper limit of normal) at the trigger has no
    # elevated lactate left to clear, and the run is NOT EVALUABLE.
    "fd04_elevated_above_mmol_l": 2.0,
    # FD-LAC-04: a run whose premise never occurs (no haemostasis with sustained restoration, too little
    # observation, or no elevated lactate) is NOT EVALUABLE; True counts it as not contradicting it.
    "fd04_unevaluable_passes": True,
    # FD-LAC-05: the debt memory is judged for a severe arrival debt: the upper end of P2F's arrival-debt
    # band, the same (60) for both cases.
    "fd05_reference_debt": 60.0,
    # FD-LAC-05: the upper limit of normal lactate (mmol/L) ...
    "fd05_normal_upper_mmol_l": 2.0,
    # ... which a run must not reach within this long after the trigger when it started clearly above it.
    "fd05_normalization_window_min": 15,
    # FD-LAC-05 reads minute 120 of the definitive-management run (management starts at minute 0).
    "fd05_minute": 120,
}
#: One-at-a-time sensitivity around PRIMARY, frozen with it. Each variant changes one setting.
SENSITIVITY = {
    "meaningful change 5 %": {"meaningful_change": 0.05},
    "meaningful change 20 %": {"meaningful_change": 0.20},
    "adequacy tolerance 5 %": {"adequacy_tolerance": 0.05},
    "adequacy tolerance 10 %": {"adequacy_tolerance": 0.10},
    "reassessment every 10 min": {"reassessment_interval_min": 10},
    "reassessment every 30 min": {"reassessment_interval_min": 30},
    "sustained over 15 min": {"sustained_min": 15},
    "sustained over 45 min": {"sustained_min": 45},
    "sustained over 60 min": {"sustained_min": 60},
    "FD-LAC-01 not applicable counts as failing": {"fd01_unapplicable_passes": False},
    "FD-LAC-01 stability ends within 60 min": {"fd01_brief_stability_min": 60},
    "FD-LAC-01 stability ends within 90 min": {"fd01_brief_stability_min": 90},
    "FD-LAC-02/03 as displayed (1 decimal)": {"fd0203_display_decimals": 1},
    "FD-LAC-04 onset within 15 min": {"fd04_onset_limit_min": 15},
    "FD-LAC-04 onset within 45 min": {"fd04_onset_limit_min": 45},
    "FD-LAC-04 onset only in 15-30 min": {"fd04_onset_floor_min": 15},
    "FD-LAC-04 restoration sustained 15 min": {"fd04_sustained_restoration_min": 15},
    "FD-LAC-04 restoration sustained 60 min": {"fd04_sustained_restoration_min": 60},
    "FD-LAC-04 not evaluable counts as failing": {"fd04_unevaluable_passes": False},
    "FD-LAC-05 reference debt 20": {"fd05_reference_debt": 20.0},
}
#: P2I-2.9, frozen: how a factor's identifiability is classified from the surviving region.
#: A factor not varied by the region, or whose surviving level shares all stay within this many
#: points of the region's, is NOT IDENTIFIED; all levels surviving with a larger shift is POORLY
#: IDENTIFIED; some level eliminated is PARTIALLY CONSTRAINED; one level left is WELL CONSTRAINED
#: (within the explored grid). The most common surviving level is never singled out.
IDENTIFIABILITY_SHIFT = 0.05
#: P2I-2 representatives, frozen: among the candidates that satisfy all six, per case, the lowest,
#: median and highest of the untreated lactate at 60 min, and of the definitive-management lactate
#: at 120 min (ties broken by candidate key).
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
    """'Persistently inadequate/worsening oxygen delivery' with active bleeding: every maximal span
    of minutes in which bleeding is active and delivery is inadequate at every minute."""
    return spans(trajectory, lambda minute: trajectory.bleeding(minute) and not adequate(trajectory, minute, settings))


def reassessments(first: int, last: int, settings: dict) -> list:
    """The reassessment points of a window: its two ends and every multiple of the interval inside."""
    interval = settings["reassessment_interval_min"]
    return sorted({first, last} | {minute for minute in range(first, last + 1) if minute % interval == 0})


def sustained_declines(trajectory: Trajectory, first: int, last: int, settings: dict) -> list:
    """'Sustained decline' inside a window: two reassessment points at least ``sustained_min`` apart
    with the later lactate meaningfully (>= the meaningful change) below the earlier."""
    points, change, span = reassessments(first, last, settings), settings["meaningful_change"], settings["sustained_min"]
    lactate = trajectory.lactate
    return [(early, late) for index, early in enumerate(points) for late in points[index + 1:]
            if late - early >= span and lactate[late] <= (1.0 - change) * lactate[early]]


def fd_lac_01(untreated: Trajectory, settings: dict) -> dict:
    """FD-LAC-01 on the untreated run. In every window of active bleeding with inadequate delivery
    lasting at least ``fd01_min_window_min``: (a) no sustained decline; (b) 'generally rise': the
    lactate at the window's end is meaningfully above its value at the window's start. Stability is
    tolerated (no interval has to rise). Sensitivity only: (c) the stable phase ends, upward,
    within ``fd01_brief_stability_min``. No such window: NOT APPLICABLE (nothing contradicts it)."""
    change, windows = settings["meaningful_change"], []
    for first, last in inadequate_bleeding_windows(untreated, settings):
        if last - first < settings["fd01_min_window_min"]:
            continue
        declines = sustained_declines(untreated, first, last, settings)
        start, finish = untreated.lactate[first], untreated.lactate[last]
        rises = finish >= (1.0 + change) * start
        brief = True
        limit = settings["fd01_brief_stability_min"]
        if limit is not None:
            exit_minute = next((minute for minute in reassessments(first, last, settings)
                                if abs(untreated.lactate[minute] - start) >= change * start), None)
            brief = (exit_minute is not None and exit_minute - first <= limit
                     and untreated.lactate[exit_minute] > start)
        windows.append({"window": [first, last], "sustained_declines": len(declines),
                        "first_decline": list(declines[0]) if declines else None, "start": start, "end": finish,
                        "generally_rises": rises, "brief_stability": brief,
                        "passes": not declines and rises and brief})
    if not windows:
        return {"applicable": False, "passes": settings["fd01_unapplicable_passes"], "windows": []}
    return {"applicable": True, "passes": all(item["passes"] for item in windows), "windows": windows}


def fd_lac_envelope(untreated: Trajectory, case: str, settings: dict) -> dict:
    """FD-LAC-02/03: the hard envelope at 60 min untreated, inclusive. A run that ends before the
    minute has no value and fails. Never a distance to the band's midpoint."""
    envelope = ENVELOPES[case]
    minute = envelope["minute"]
    if untreated.end < minute:
        return {"value": None, "passes": False}
    value = untreated.lactate[minute]
    shown = value if settings["fd0203_display_decimals"] is None else round(value, settings["fd0203_display_decimals"])
    return {"value": value, "compared": shown, "passes": envelope["low"] <= shown <= envelope["high"]}


def restoration_trigger(definitive: Trajectory, settings: dict) -> int | None:
    """FD-LAC-04's clock: the first minute at or after haemostasis from which delivery stays adequate
    for ``fd04_sustained_restoration_min`` (within the run). Never earlier than haemostasis, and never
    while delivery is still inadequate."""
    hold = settings["fd04_sustained_restoration_min"]
    if definitive.controlled_at is None:
        return None
    for minute in range(definitive.controlled_at, definitive.end - hold + 1):
        if all(adequate(definitive, later, settings) for later in range(minute, minute + hold + 1)):
            return minute
    return None


def fd_lac_04(definitive: Trajectory, settings: dict) -> dict:
    """FD-LAC-04 on the definitive-management run, timed from the trigger (not from minute 0).

    The clear downward trend begins at the post-trigger peak: the last minute of the highest
    lactate between the trigger and the end, so from there lactate only stays below it (an
    already falling lactate peaks at the trigger itself; a plateau ends where the fall begins). The trend is clear when the lactate at
    the end is meaningfully below that peak. It passes when the trend is clear and begins between
    ``fd04_onset_floor_min`` and ``fd04_onset_limit_min`` after the trigger. No haemostasis with
    sustained restoration, less than ``fd04_observation_after_trigger_min`` of observation after the
    trigger, or a lactate already at or below ``fd04_elevated_above_mmol_l`` at the trigger (nothing
    elevated to clear): NOT EVALUABLE."""
    trigger = restoration_trigger(definitive, settings)
    base = {"haemostasis": definitive.controlled_at, "trigger": trigger}
    if trigger is None:
        return {**base, "evaluable": False, "reason": "no haemostasis with sustained restoration of delivery",
                "passes": settings["fd04_unevaluable_passes"]}
    if definitive.end - trigger < settings["fd04_observation_after_trigger_min"]:
        return {**base, "evaluable": False, "reason": "too little observation after the trigger",
                "passes": settings["fd04_unevaluable_passes"]}
    lactate = definitive.lactate
    if lactate[trigger] <= settings["fd04_elevated_above_mmol_l"]:
        return {**base, "evaluable": False, "reason": "no elevated lactate left to clear at the trigger",
                "at_trigger": lactate[trigger], "passes": settings["fd04_unevaluable_passes"]}
    peak = max(range(trigger, definitive.end + 1), key=lambda minute: (lactate[minute], minute))
    clear = peak < definitive.end and lactate[definitive.end] <= (1.0 - settings["meaningful_change"]) * lactate[peak]
    delay = peak - trigger
    timely = settings["fd04_onset_floor_min"] <= delay <= settings["fd04_onset_limit_min"]
    return {**base, "evaluable": True, "onset": peak, "onset_after_trigger_min": delay, "at_trigger": lactate[trigger],
            "at_onset": lactate[peak], "at_end": lactate[definitive.end], "clear": clear, "timely": timely,
            "passes": clear and timely}


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
              settings: dict) -> dict:
    """FD-LAC-05, without a numeric 120-min band (none is approved).

    (a) Memory of prior debt is material: the lactate a severe arrival debt (``fd05_reference_debt``)
        still leaves at ``fd05_minute`` is at least the meaningful change of the arrival lactate.
    (b) Not forced to normal immediately: a lactate clearly above the upper limit of normal at the
        trigger does not reach it within ``fd05_normalization_window_min``.
    Full normalization is never required and no 120-min value is targeted."""
    coefficient = debt_memory_coefficient(kinetics["debt_clearance_tau_min"], kinetics["lactate_clearance_tau_min"],
                                          kinetics["lactate_per_output_deficit"], settings["fd05_minute"])
    memory = settings["fd05_reference_debt"] * coefficient
    material = memory >= settings["meaningful_change"] * arrival_lactate
    abrupt = False
    normal, window = settings["fd05_normal_upper_mmol_l"], settings["fd05_normalization_window_min"]
    if trigger is not None and trigger + window <= definitive.end:
        before = definitive.lactate[trigger]
        abrupt = before >= (1.0 + settings["meaningful_change"]) * normal and definitive.lactate[trigger + window] <= normal
    residual = definitive.lactate[settings["fd05_minute"]] if definitive.end >= settings["fd05_minute"] else None
    return {"debt_memory_at_reference_debt": memory, "memory_per_unit_debt": coefficient, "material_memory": material,
            "abrupt_normalization": abrupt, "residual": residual, "passes": material and not abrupt}


def fd_lac_06(runs: dict, settings: dict) -> dict:
    """FD-LAC-06 on every engine-produced run of a case (untreated, partial, definitive): no
    sustained decline inside any window of active bleeding with inadequate delivery at least
    ``sustained_min`` long. A fall while delivery is adequate is allowed, bleeding or not."""
    violations = []
    for scenario, trajectory in sorted(runs.items()):
        for first, last in inadequate_bleeding_windows(trajectory, settings):
            if last - first < settings["sustained_min"]:
                continue
            declines = sustained_declines(trajectory, first, last, settings)
            if declines:
                violations.append({"scenario": scenario, "window": [first, last], "first_decline": list(declines[0]),
                                   "sustained_declines": len(declines)})
    return {"violations": violations, "passes": not violations}


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
                                              arrival_lactate[case], settings)
        detail[case]["FD-LAC-06"] = fd_lac_06(by_scenario, settings)
    verdict = {}
    for item in FACULTY_CLINICAL_CONSTRAINTS:
        verdict[item.id] = all(detail[case][item.id]["passes"] for case in item.cases if case in detail)
    return {"passes": verdict, "all": all(verdict.values()), "detail": detail}


def identifiability(region_shares: dict, surviving_shares: dict, varied: bool) -> str:
    """P2I-2.9's frozen rule (see IDENTIFIABILITY_SHIFT), from a factor's level shares."""
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
    """This whole module, by hash: the decisions, the operational tests, their thresholds, the
    sensitivity design and the reporting rules. Frozen before any candidate is filtered."""
    return hashlib.sha256(Path(__file__).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
