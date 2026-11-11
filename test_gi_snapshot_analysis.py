"""P3-189 a P3-192 and P3-197: the GI development snapshot, its sensitivity audit and the counterfactual harness.

TEST-SIDE ANALYSIS, not a layer module. It only READS: the common core, the shadow layer and the legacy engine are exactly what
they were. Nothing here writes a patient state, enables authority, or changes ``COMMON_CORE_RUNTIME_AUTHORITY``.

Three things live here, apart on purpose:

* **The selection rule** (P3-189, P3-191): criteria fixed BEFORE a point is chosen, computed from the faculty's approved behavioural
  regions alone. No legacy value, no legacy minute and no clinical value enters it (``select`` takes only region geometry and
  mechanistic checks), which is what makes "not fitted to the legacy curves" a checkable property and not an intention.
* **An independent evaluator** (P3-190): the Amendment-2 laws written a second time, from their equations, over a recorded physical
  course (relative delivery, relative perfusion, pulse). The core's non-interference (F and the collapse burden feed nothing back)
  makes the course independent of the ten magnitudes, so a profile can be read offline EXACTLY. ``test_phase3_gi_development_snapshot``
  proves that equality against the live rows, bit for bit, instead of assuming it.
* **A counterfactual harness** (P3-197): a legacy-authoritative encounter run beside what a common-core snapshot WOULD have authored,
  minute by minute, committing nothing.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import math
import random
from contextlib import contextmanager
from typing import Any, Mapping, Sequence

import runtime_shadow as rs
import test_gi_amendment_2_series as series
from clinical_core import legacy_adapter
from clinical_core import systemic_consciousness as sc

ANALYSIS_VERSION = "P3-189"
SNAPSHOT_ID = "GI_DEVELOPMENT_SNAPSHOT_V1"
FIELDS = tuple(sc.FIELDS)
#: The faculty's approved behavioural region of every magnitude (the core's own table): the only geometry the rule reads.
REGION = {name: (float(sc.REGIONS[name][0]), float(sc.REGIONS[name][1])) for name in FIELDS}
CUTS = tuple(sc.CATEGORY_CUTS)
CASES = tuple(series.CASES)
SCENARIOS = tuple(series.SCENARIOS)
#: Two scenarios beyond the seven of the series, for the boundary audit (P3-196) and the collapse clearance (P3-190).
EXTRA_SCENARIOS = ("untreated_long", "late_rescue")
#: The classification thresholds of P3-190A, DECLARED BEFORE the sweep ran (minutes of swing of an event time over the region).
HIGH_SWING_MIN, MODERATE_SWING_MIN = 10.0, 3.0
HIGH, MODERATE, LOW_SENS, IRRELEVANT = ("HIGH_SENSITIVITY", "MODERATE_SENSITIVITY", "LOW_SENSITIVITY",
                                        "STRUCTURALLY_IRRELEVANT_FOR_CURRENT_GI")
#: What the classification reads. ``rec_below_0_80`` is reported but NOT classified: on one fixed physical recovery it depends on
#: whether the order falls before or after the profile's own UNRESPONSIVE minute (an artefact of the fixed order, not of the law).
#: ``rescue_*`` come from ``late_rescue`` (an order AFTER established collapse): the only scenario that exercises the collapse clearance. They were
#: added after a first pass showed that ``collapse_clear_tau`` moves nothing in the seven required scenarios -- which, without this scenario,
#: would have been misread as "irrelevant" when it was only "not exercised".
CLASSIFIED = ("first_somnolent", "first_obtunded", "first_unresponsive", "impending", "established", "rec_below_0_50", "rec_normal",
              "rescue_collapse_below_established", "rescue_collapse_none", "rescue_normal")
REPORTED_ONLY = ("rec_below_0_80",)
LEVELS = (0.0, 0.25, 0.5, 0.75, 1.0)
LHS_POINTS, LHS_SEED = 48, 20261111

#: The criteria of P3-189, as data: ``HARD`` ones must all hold; ``RANKED`` ones order the feasible candidates, in this order.
HARD_CRITERIA = (
    ("H1", "lies strictly inside every approved region (no magnitude on a region bound)"),
    ("H2", "keeps every faculty behavioural invariant (FD-P3-176 recovery invariant, ordering of the onset and collapse events)"),
    ("H3", "keeps the causal order, the recovery behaviour and the collapse semantics on every scenario"),
    ("H4", "generalises across both GI cases (event times differ by at most one minute)"),
    ("H5", "is deterministic (re-evaluation equals the record exactly)"),
    ("H6", "has explicit provenance (a complete, digest-pinned record)"),
    ("H7", "is not selected to mimic a legacy timing (the rule reads no legacy value)"),
)
RANKED_CRITERIA = (
    ("R1", "the largest minimum normalised margin to the region bounds"),
    ("R2", "the fewest magnitudes outside the LOW..HIGH witness bracket"),
    ("R3", "the most interpretable provenance (a parameter-free rule over the faculty regions, not an arbitrary draw)"),
)
NEAR_BOUNDARY = 0.05
BROAD_MARGIN = 0.20


# -- geometry and the selection rule (P3-189, P3-191) -----------------------------------------------------------------------------------

def margins(values: Mapping[str, float]) -> dict:
    """The distance of each magnitude to the NEAREST bound of its region, as a share of the region's width (0 on a bound, 0.5 at the midpoint)."""
    return {name: min(values[name] - REGION[name][0], REGION[name][1] - values[name]) / (REGION[name][1] - REGION[name][0])
            for name in FIELDS}


def min_margin(values: Mapping[str, float]) -> float:
    return min(margins(values).values())


def near_boundary(values: Mapping[str, float], threshold: float = NEAR_BOUNDARY) -> list:
    return [name for name, share in margins(values).items() if share < threshold]


def region_midpoint() -> dict:
    """The point of the box region that maximises the minimum normalised margin: each magnitude at the middle of its own region.
    It is UNIQUE (any other point has some magnitude closer to a bound), which is why it follows from criterion R1 and not from a name."""
    return {name: round((REGION[name][0] + REGION[name][1]) / 2.0, 6) for name in FIELDS}


def witness_values(name: str) -> dict:
    return sc.WITNESSES[name].to_dict()


def outside_bracket(values: Mapping[str, float], low: str = "LOW", high: str = "HIGH") -> list:
    """The magnitudes that do not lie between the LOW and the HIGH witness (the witnesses do not bound them)."""
    lo, hi = witness_values(low), witness_values(high)
    return [name for name in FIELDS
            if not (min(lo[name], hi[name]) - 1e-12 <= values[name] <= max(lo[name], hi[name]) + 1e-12)]


def candidate_row(label: str, values: Mapping[str, float]) -> dict:
    share = margins(values)
    return {"label": label, "min_margin": round(min(share.values()), 6), "near_boundary": near_boundary(values),
            "on_a_bound": [name for name, value in share.items() if value <= 1e-9], "outside_bracket": outside_bracket(values),
            "margins": {name: round(value, 4) for name, value in share.items()}, "values": dict(values)}


def feasible(candidate: Mapping) -> bool:
    """The part of the hard criteria that is a property of the point alone (H1): strictly inside every region."""
    return not candidate["on_a_bound"] and candidate["min_margin"] > 0.0


def select(candidates: Sequence[Mapping]) -> dict:
    """Among the candidates that satisfy H1, the one that ranks first by R1, then R2. Reads region geometry and the witness bracket ONLY."""
    pool = [item for item in candidates if feasible(item)]
    if not pool:
        raise ValueError("no candidate is strictly inside every region")
    return max(pool, key=lambda item: (item["min_margin"], -len(item["outside_bracket"])))


# -- the independent evaluator (P3-190) --------------------------------------------------------------------------------------------------

def _ramp(value: float, normal: float, severe: float) -> float:
    if value >= normal:
        return 0.0
    if value <= severe:
        return 1.0
    return (normal - value) / (normal - severe)


def _relax(level: float, signal: float, rise: float, clear: float) -> float:
    tau = rise if signal > level else clear
    return signal + (level - signal) * math.exp(-1.0 / tau)


def category_of(impairment: float) -> int:
    return sum(1 for cut in CUTS if impairment >= cut)


def evaluate(values: Mapping[str, float], physical: Mapping[str, Sequence], primary: float = 0.0) -> list:
    """Read a profile over a recorded physical course: F, the collapse burden, the observable category and the collapse state per minute.

    The two laws are the amendment's, written again from their equations (a first-order relaxation toward a bounded signal, with a
    rise constant while the signal is above the level and a clearance constant below it); no core function is called, so a defect
    in one implementation cannot hide in the other. ``physical`` carries ``relative_delivery``, ``relative_perfusion`` and ``pulse``."""
    burden, collapse = 0.0, 0.0
    out = []
    for delivery, perfusion, pulse, minute in zip(physical["relative_delivery"], physical["relative_perfusion"],
                                                  physical["pulse"], physical["minute"]):
        if not pulse or collapse >= values["established_burden"]:
            state = 2
        elif collapse >= values["impending_burden"]:
            state = 1
        else:
            state = 0
        out.append({"minute": minute, "F": burden, "collapse_burden": collapse,
                    "category": category_of(max(primary, burden, 1.0 if state == 2 else 0.0)), "collapse_state": state})
        delivery_signal = _ramp(delivery, values["delivery_normal"], values["delivery_severe"])
        burden = _relax(burden, delivery_signal if pulse else 1.0, values["burden_rise_tau"], values["burden_clear_tau"])
        if pulse:
            collapse = _relax(collapse, min(_ramp(perfusion, values["perfusion_normal"], values["perfusion_severe"]), delivery_signal),
                              values["collapse_rise_tau"], values["collapse_clear_tau"])
    return out


def first_minute(rows: Sequence[Mapping], predicate) -> int | None:
    for row in rows:
        if predicate(row):
            return row["minute"]
    return None


# -- the sweep (P3-190) ------------------------------------------------------------------------------------------------------------------

def point_at(base: Mapping[str, float], name: str, share: float) -> dict:
    low, high = REGION[name]
    return {**base, name: round(low + share * (high - low), 6)}


def lhs_points(n: int = LHS_POINTS, seed: int = LHS_SEED) -> list:
    """A Latin hypercube of the ten regions (every magnitude's range cut into ``n`` strata, each used once): sparse interior witnesses,
    never a Cartesian grid."""
    rng = random.Random(seed)
    columns = {}
    for name in FIELDS:
        order = list(range(n))
        rng.shuffle(order)
        columns[name] = [(order[i] + rng.random()) / n for i in range(n)]
    return [{name: round(REGION[name][0] + columns[name][i] * (REGION[name][1] - REGION[name][0]), 6) for name in FIELDS}
            for i in range(n)]


def corner_points(base: Mapping[str, float]) -> list:
    """The 16 corners of the four magnitudes that dominate (the two delivery and the two perfusion bounds), the rest at ``base``."""
    names = ("delivery_normal", "delivery_severe", "perfusion_normal", "perfusion_severe")
    return [{**base, **{name: REGION[name][bit] for name, bit in zip(names, bits)}} for bits in itertools.product((0, 1), repeat=4)]


def physical_of(run: Mapping, witness: str = "CENTER_REFERENCE") -> dict:
    """The recorded physical course of a live run: the shared core's relative delivery, relative perfusion and pulse per minute."""
    rows = run["witness_rows"][witness]
    return {"minute": [row["minute"] for row in rows],
            "relative_delivery": [row["channels"]["relative_delivery"] for row in rows],
            "relative_perfusion": [row["channels"]["relative_perfusion"] for row in rows],
            "pulse": [bool(row["channels"]["pulse_present"]) for row in rows]}


def event_times(values: Mapping[str, float], physical: Mapping[str, Sequence]) -> dict:
    rows = evaluate(values, physical)
    return {"first_somnolent": first_minute(rows, lambda r: r["category"] >= 1),
            "first_obtunded": first_minute(rows, lambda r: r["category"] >= 2),
            "first_unresponsive": first_minute(rows, lambda r: r["category"] >= 3),
            "impending": first_minute(rows, lambda r: r["collapse_state"] >= 1),
            "established": first_minute(rows, lambda r: r["collapse_state"] >= 2),
            "f_at_first_minute_ge_0_80": first_minute(rows, lambda r: r["F"] >= 0.80)}


def recovery_times(values: Mapping[str, float], physical: Mapping[str, Sequence], order_minute: int) -> dict:
    """The recovery metrics on ONE physical recovery (an order at ``order_minute``): minutes from the order to F < 0.80, F < 0.50 and category 0."""
    rows = [row for row in evaluate(values, physical) if row["minute"] >= order_minute]

    def after(predicate):
        found = first_minute(rows, predicate)
        return None if found is None else found - order_minute
    at_order = next((row["F"] for row in rows if row["minute"] == order_minute), None)
    return {"rec_below_0_80": after(lambda r: r["F"] < 0.80), "rec_below_0_50": after(lambda r: r["F"] < 0.50),
            "rec_normal": after(lambda r: r["category"] == 0), "rec_f_at_order": None if at_order is None else round(at_order, 4)}


def category_sequence(values: Mapping[str, float], physical: Mapping[str, Sequence]) -> list:
    out, last = [], None
    for row in evaluate(values, physical):
        if row["category"] != last:
            out.append([row["minute"], row["category"]])
            last = row["category"]
    return out


def profile_metrics(values: Mapping[str, float], course: Mapping[str, Mapping]) -> dict:
    """Every event time of a profile over the recorded courses of both cases (``course[case][scenario]`` is a physical course with its order)."""
    out = {}
    for case in CASES:
        events = event_times(values, course[case]["untreated"]["physical"])
        out.update({f"{case}/{key}": value for key, value in events.items()})
        recovery = course[case]["recovery_after_severe"]
        out.update({f"{case}/{key}": value for key, value in
                    recovery_times(values, recovery["physical"], recovery["order_minute"]).items()})
        rescue = course[case]["late_rescue"]
        rescued = [row for row in evaluate(values, rescue["physical"]) if row["minute"] >= rescue["order_minute"]]

        def after(predicate, rows=rescued, start=rescue["order_minute"]):
            found = first_minute(rows, predicate)
            return None if found is None else found - start
        out[f"{case}/rescue_collapse_below_established"] = after(lambda r: r["collapse_state"] < 2)
        out[f"{case}/rescue_collapse_none"] = after(lambda r: r["collapse_state"] == 0)
        out[f"{case}/rescue_normal"] = after(lambda r: r["category"] == 0)
        out[f"{case}/severe_sequence"] = category_sequence(values, course[case]["severe_deterioration"]["physical"])
    return out


def swing(values: Sequence) -> float | None:
    numbers = [value for value in values if isinstance(value, (int, float))]
    return float(max(numbers) - min(numbers)) if numbers and len(numbers) == len(values) else None


def classify(max_swing: float | None) -> str:
    if max_swing is None:
        return "UNDEFINED"
    if max_swing >= HIGH_SWING_MIN:
        return HIGH
    if max_swing >= MODERATE_SWING_MIN:
        return MODERATE
    if max_swing > 0.0:
        return LOW_SENS
    return IRRELEVANT


def invariant_violations(values: Mapping[str, float], course: Mapping[str, Mapping]) -> dict:
    """The safety and ordering checks of P3-190A over every recorded scenario of both cases (counts of violations; all zero is the claim)."""
    found = {"untreated_ordering": 0, "untreated_not_monotone": 0, "collapse_led_unresponsive": 0, "f_falls_before_the_order": 0,
             "category_gives_back_two_bands": 0}
    for case in CASES:
        rows = evaluate(values, course[case]["untreated"]["physical"])
        first = [first_minute(rows, lambda r, k=k: r["category"] >= k) for k in (1, 2, 3)]
        impending = first_minute(rows, lambda r: r["collapse_state"] >= 1)
        established = first_minute(rows, lambda r: r["collapse_state"] >= 2)
        if not (first[0] <= first[1] <= first[2] and impending <= established):
            found["untreated_ordering"] += 1
        if any(b["F"] < a["F"] - 1e-12 or b["collapse_burden"] < a["collapse_burden"] - 1e-12 or b["category"] < a["category"]
               for a, b in zip(rows, rows[1:])):
            found["untreated_not_monotone"] += 1
        unresponsive_by_f = first_minute(rows, lambda r: r["F"] >= 0.80)
        if established is not None and (unresponsive_by_f is None or established < unresponsive_by_f):
            found["collapse_led_unresponsive"] += 1
        for scenario, entry in course[case].items():
            rows = evaluate(values, entry["physical"])
            first_order = entry.get("order_minute")
            for a, b in zip(rows, rows[1:]):
                if first_order is not None and b["F"] < a["F"] - 1e-12 and a["minute"] < first_order:
                    found["f_falls_before_the_order"] += 1
                if a["category"] - b["category"] >= 2:
                    found["category_gives_back_two_bands"] += 1
    return found


# -- records and digests (P3-192) --------------------------------------------------------------------------------------------------------

def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("ascii")).hexdigest()


# -- live capture (P3-190 data, P3-197) ---------------------------------------------------------------------------------------------------

LEGACY_KEYS = ("map", "respiratory_rate", "crt", "rhythm", "hemoglobin", "lactate_lab")
SESSION_KEYS = ("sbp", "dbp", "map", "monitor_rate_bpm", "spo2", "respiratory_rate", "lactate", "crt_s", "consciousness_level",
                "pulse_present", "hb", "V", "P", "T", "D")
A2_KEYS = ("systemic_encephalopathy_burden", "collapse_burden", "relative_delivery", "relative_perfusion", "category_index",
           "collapse_state_index", "pulse_present")


@contextmanager
def snapshot_as_middle_witness(values: Mapping[str, float]):
    """Run the shadow ensemble with the snapshot in the CENTER_REFERENCE slot (LOW and HIGH untouched), for ONE process and ONE block.

    The layer builds each witness from ``systemic_consciousness.WITNESSES`` when it runs, so this needs no change to the layer or to
    the core: the dictionary entry is replaced for the block and restored after it."""
    original = sc.WITNESSES["CENTER_REFERENCE"]
    sc.WITNESSES["CENTER_REFERENCE"] = sc.Amendment2Profile(**dict(values))
    try:
        yield
    finally:
        sc.WITNESSES["CENTER_REFERENCE"] = original


@contextmanager
def richer_legacy_samples():
    """Take the legacy engine's own snapshot (``legacy_adapter.snapshot``, a pure read) at every sampled minute, besides the series' sample."""
    original = series._legacy_sample

    def sample(encounter) -> dict:
        base = original(encounter)
        snap = legacy_adapter.snapshot(encounter.state)
        base.update({key: snap.get(key) for key in LEGACY_KEYS})
        return base
    series._legacy_sample = sample
    try:
        yield
    finally:
        series._legacy_sample = original


@contextmanager
def extended_plans():
    original = series._plan

    def plan(scenario: str) -> dict:
        if scenario == "untreated_long":
            return {"at": {}, "horizon": 380}
        if scenario == "late_rescue":
            return {"at": {215: (series.ACCESS, series.SALINE, series.BLOOD_MORE)}, "horizon": 300}
        return original(scenario)
    series._plan = plan
    try:
        yield
    finally:
        series._plan = original


def capture(case: str, scenario: str, snapshot_values: Mapping[str, float] | None = None) -> dict:
    """One live encounter with the snapshot as the middle witness: legacy truth per minute, the shadow session's display readings and
    every witness's Amendment-2 channels. Nothing is committed to the encounter; the shadow only observes, as it always does."""
    with extended_plans(), richer_legacy_samples():
        if snapshot_values is None:
            run = series.run_scenario(case, scenario)
        else:
            with snapshot_as_middle_witness(snapshot_values):
                run = series.run_scenario(case, scenario)
    return {
        "case": case, "scenario": scenario, "orders": run["orders"], "triggered_at": run["triggered_at"],
        "minutes_played": run["encounter_minute"], "legacy_arrested": run["legacy_arrested"],
        "failures": run["failures"], "legacy": run["legacy"],
        "session": [{"minute": row["minute"], **{key: row["channels"].get(key) for key in SESSION_KEYS}} for row in run["session_rows"]],
        "witnesses": {name: [{"minute": row["minute"], **{key: row["channels"].get(key) for key in A2_KEYS}} for row in rows]
                      for name, rows in run["witness_rows"].items()},
    }


# -- from captures to physical courses (P3-190) -----------------------------------------------------------------------------------------------

def physical_from_capture(captured: Mapping, witness: str = "CENTER_REFERENCE") -> dict:
    rows = captured["witnesses"][witness]
    return {"minute": [row["minute"] for row in rows],
            "relative_delivery": [row["relative_delivery"] for row in rows],
            "relative_perfusion": [row["relative_perfusion"] for row in rows],
            "pulse": [bool(row["pulse_present"]) for row in rows]}


def order_minute_of(captured: Mapping) -> int | None:
    """The minute of the first order of a capture (the trigger minute of an adaptive scenario), or None for an untreated course."""
    return captured["orders"][0]["minute"] if captured["orders"] else None


def course_from(captures: Mapping) -> dict:
    """``captures[(case, scenario)]`` -> ``course[case][scenario] = {physical, order_minute}``."""
    course: dict = {case: {} for case in CASES}
    for (case, scenario), captured in captures.items():
        course[case][scenario] = {"physical": physical_from_capture(captured), "order_minute": order_minute_of(captured)}
    return course


def exactness(captures: Mapping, witness_values_of: Mapping[str, Mapping[str, float]]) -> dict:
    """Compare the independent evaluator with the live Amendment-2 channels of EVERY witness of EVERY capture, minute by minute."""
    rows_compared, worst, mismatches = 0, 0.0, 0
    for captured in captures.values():
        for name, rows in captured["witnesses"].items():
            evaluated = evaluate(witness_values_of[name], physical_from_capture(captured, name))
            for mine, live in zip(evaluated, rows):
                rows_compared += 1
                worst = max(worst, abs(mine["F"] - live["systemic_encephalopathy_burden"]),
                            abs(mine["collapse_burden"] - live["collapse_burden"]))
                if mine["category"] != live["category_index"] or mine["collapse_state"] != live["collapse_state_index"]:
                    mismatches += 1
    return {"rows_compared": rows_compared, "max_abs_difference": worst, "category_or_collapse_mismatches": mismatches}


def _monotone(values: Sequence) -> bool:
    steps = [b - a for a, b in zip(values, values[1:])]
    return all(step >= 0 for step in steps) or all(step <= 0 for step in steps)


def recovery_invariant(values: Mapping[str, float], physical: Mapping[str, Sequence], order_minute: int) -> dict:
    """The FD-P3-176 invariant read on ONE physical recovery: 0.80 to below 0.50 in the complete trajectory, the minutes left after the
    formal entry into the recovery region (relative delivery back at its normal bound), and the share of the descent already done by then."""
    rows = [row for row in evaluate(values, physical) if row["minute"] >= order_minute]
    by_minute = {row["minute"]: row for row in rows}
    entry = next((m for m, d in zip(physical["minute"], physical["relative_delivery"])
                  if m >= order_minute and d >= values["delivery_normal"]), None)
    peak_minute = max(rows, key=lambda row: row["F"])["minute"] if rows else None
    below_80 = first_minute([r for r in rows if r["minute"] >= peak_minute], lambda r: r["F"] < 0.80) if rows else None
    below_50 = first_minute([r for r in rows if r["minute"] >= peak_minute], lambda r: r["F"] < 0.50) if rows else None
    f_entry = by_minute[entry]["F"] if entry in by_minute else None
    share = None if f_entry is None else max(0.0, min(1.0, (0.80 - f_entry) / 0.30))
    return {"order_minute": order_minute, "f_at_order": round(by_minute[order_minute]["F"], 4) if order_minute in by_minute else None,
            "entry_minute": entry, "f_at_entry": None if f_entry is None else round(f_entry, 4),
            "minutes_0_80_to_below_0_50": None if None in (below_80, below_50) else below_50 - below_80,
            "minutes_remaining_after_entry": None if None in (entry, below_50) else max(0, below_50 - entry),
            "share_of_descent_done_before_entry": None if share is None else round(share, 4),
            "isolated_decay_0_80_to_0_50_min": round(values["burden_clear_tau"] * math.log(0.80 / 0.50), 3)}


def legacy_first_levels(captured: Mapping) -> dict:
    """The minute the LEGACY engine first reads level >= 1 and >= 2 on an untreated capture. REPORTED ONLY, never an input of the selection."""
    return {f"level_{level}": next((row["minute"] for row in captured["legacy"]
                                    if row.get("legacy_level") is not None and row["legacy_level"] >= level), None)
            for level in (1, 2)}


def _interpolated(levels: Sequence[float], values: Sequence, share: float):
    for (s0, v0), (s1, v1) in zip(zip(LEVELS, values), zip(LEVELS[1:], values[1:])):
        if s0 <= share <= s1:
            return v0 + (v1 - v0) * (share - s0) / (s1 - s0)
    return None


def build_sensitivity(course: Mapping, legacy: Mapping, *, base: Mapping[str, float] | None = None) -> dict:
    """The whole P3-190 record from the recorded physical courses (``course[case][scenario]``) and the legacy first levels (REPORTED ONLY): one-at-a-time
    sweep, Latin hypercube, the corners of the four dominant magnitudes, the ordering and safety invariants over every profile evaluated, the
    candidate table and the selection."""
    midpoint = region_midpoint()
    base = dict(midpoint if base is None else base)
    named = {name: witness_values(name) for name in ("LOW", "CENTER_REFERENCE", "HIGH")}
    named["REGION_MIDPOINT"] = midpoint
    metric_keys = [f"{case}/{metric}" for case in CASES for metric in CLASSIFIED + REPORTED_ONLY]
    # -- one at a time
    oat, evaluated = {}, [(f"witness:{n}", v) for n, v in named.items()]
    for name in FIELDS:
        points = [point_at(base, name, share) for share in LEVELS]
        evaluated += [(f"oat:{name}@{share}", point) for share, point in zip(LEVELS, points)]
        results = [profile_metrics(point, course) for point in points]
        series_of = {key: [item[key] for item in results] for key in metric_keys}
        swings = {key: swing(values) for key, values in series_of.items()}
        classified = [value for key, value in swings.items() if key.split("/")[1] in CLASSIFIED and value is not None]
        top = max(classified) if classified else None
        sequences = {canonical(item[f"{case}/severe_sequence"]) for item in results for case in CASES}
        label = classify(top)
        if label == IRRELEVANT and len(sequences) > 1:
            label = LOW_SENS
        oat[name] = {"levels": [point[name] for point in points], "series": series_of, "swing": swings,
                     "max_classified_swing": top, "class": label,
                     "dominant_metric": max((k for k in swings if k.split("/")[1] in CLASSIFIED and swings[k] is not None),
                                            key=lambda k: swings[k], default=None),
                     "monotone_in_every_defined_metric": all(_monotone(v) for v in series_of.values() if all(isinstance(x, (int, float)) for x in v)),
                     "changes_the_crystalloid_only_sequence": len(sequences) > 1,
                     "undefined_metrics": sorted(k for k, v in swings.items() if v is None)}
    ranking = sorted(({"parameter": name, "class": item["class"], "max_classified_swing": item["max_classified_swing"],
                       "dominant_metric": item["dominant_metric"]} for name, item in oat.items()),
                     key=lambda item: -(item["max_classified_swing"] or 0.0))
    # -- sparse interior (Latin hypercube) and its additive prediction from the one-at-a-time sweep
    points = lhs_points()
    evaluated += [(f"lhs:{i}", point) for i, point in enumerate(points)]
    sampled = [profile_metrics(point, course) for point in points]
    base_metrics = profile_metrics(base, course)
    effects, residuals = {}, {}
    for key in (k for k in metric_keys if k.startswith(CASES[0] + "/")):
        pairs = [(point, item[key]) for point, item in zip(points, sampled) if isinstance(item[key], (int, float))]
        if len(pairs) < 10:
            continue
        xs = [[(point[n] - REGION[n][0]) / (REGION[n][1] - REGION[n][0]) for n in FIELDS] for point, _ in pairs]
        ys = [float(y) for _, y in pairs]
        beta = _least_squares(xs, ys)
        fitted = [beta[0] + sum(b * x for b, x in zip(beta[1:], row)) for row in xs]
        mean_y = sum(ys) / len(ys)
        total = sum((y - mean_y) ** 2 for y in ys)
        spread_y = math.sqrt(total / len(ys)) or 1.0
        standardized = {}
        for index, n in enumerate(FIELDS):
            column = [row[index] for row in xs]
            mean_x = sum(column) / len(column)
            spread_x = math.sqrt(sum((v - mean_x) ** 2 for v in column) / len(column))
            standardized[n] = round(beta[index + 1] * spread_x / spread_y, 3)
        effects[key] = {"n": len(pairs), "range": [min(ys), max(ys)],
                        "r_squared_linear": None if total == 0 else round(1.0 - sum((y - f) ** 2 for y, f in zip(ys, fitted)) / total, 4),
                        "standardized_effect": standardized}
        errors = []
        for point, item in zip(points, sampled):
            actual, centre = item[key], base_metrics[key]
            if not isinstance(actual, (int, float)) or not isinstance(centre, (int, float)):
                continue
            predicted, usable = centre, True
            for n in FIELDS:
                share = (point[n] - REGION[n][0]) / (REGION[n][1] - REGION[n][0])
                value = _interpolated(LEVELS, oat[n]["series"][key], share)
                if value is None:
                    usable = False
                    break
                predicted += value - centre
            if usable:
                errors.append(abs(actual - predicted))
        residuals[key] = {"n": len(errors), "mean_abs_minutes": round(sum(errors) / len(errors), 3), "max_abs_minutes": round(max(errors), 3)} if errors else None
    # -- the corners of the four dominant magnitudes
    corners = corner_points(base)
    evaluated += [(f"corner:{i}", point) for i, point in enumerate(corners)]
    corner_metrics = [profile_metrics(point, course) for point in corners]
    coverage = {}
    for metric in ("first_somnolent", "first_obtunded", "first_unresponsive", "impending", "established"):
        key = f"{CASES[0]}/{metric}"
        values = [item[key] for item in corner_metrics]
        low_value, high_value = (profile_metrics(named[n], course)[key] for n in ("LOW", "HIGH"))
        coverage[metric] = {"corners_min": min(values), "corners_max": max(values), "witnesses_low_high": sorted([low_value, high_value]),
                            "minutes_not_bounded_by_the_witnesses": max(0, min(low_value, high_value) - min(values)) + max(0, max(values) - max(low_value, high_value))}
    # -- invariants over EVERY profile evaluated
    totals = {"profiles": len(evaluated), "violations": {}}
    for label, point in evaluated:
        for kind, count in invariant_violations(point, course).items():
            totals["violations"][kind] = totals["violations"].get(kind, 0) + count
    # -- the selection
    candidates = [candidate_row(name, values) for name, values in named.items()]
    candidates += [candidate_row(f"LHS_{i}", point) for i, point in enumerate(points)]
    chosen = select(candidates)
    distance = {}
    for item in candidates:
        events = profile_metrics(item["values"], course)
        key = lambda metric: events[f"{CASES[0]}/{metric}"]
        distance[item["label"]] = abs(key("first_somnolent") - legacy["level_1"]) + abs(key("first_obtunded") - legacy["level_2"])
    closest = min(distance, key=lambda label: distance[label])
    ordered = sorted(distance, key=lambda label: distance[label])
    return {"base": base, "oat": oat, "ranking": ranking, "effects": effects, "additive_residual": residuals, "corner_coverage": coverage,
            "invariants": totals, "candidates": candidates, "selected": chosen["label"],
            "legacy_distance_reported_only": {"legacy_first_levels": legacy, "closest_candidate": closest,
                                              "closest_candidate_min_margin": next(c["min_margin"] for c in candidates if c["label"] == closest),
                                              "selected_rank_by_legacy_distance": ordered.index(chosen["label"]) + 1,
                                              "of": len(ordered), "distance_of_selected": distance[chosen["label"]],
                                              "distance_of_closest": distance[closest]}}


def _least_squares(xs: Sequence[Sequence[float]], ys: Sequence[float]) -> list:
    """Ordinary least squares with an intercept by the normal equations (Gauss-Jordan, partial pivoting): no numerical library is needed."""
    rows = [[1.0, *row] for row in xs]
    size = len(rows[0])
    a = [[sum(r[i] * r[j] for r in rows) for j in range(size)] + [sum(r[i] * y for r, y in zip(rows, ys))] for i in range(size)]
    for col in range(size):
        pivot = max(range(col, size), key=lambda r: abs(a[r][col]))
        a[col], a[pivot] = a[pivot], a[col]
        if abs(a[col][col]) < 1e-12:
            continue
        a[col] = [v / a[col][col] for v in a[col]]
        for r in range(size):
            if r != col:
                factor = a[r][col]
                a[r] = [v - factor * w for v, w in zip(a[r], a[col])]
    return [a[i][size] for i in range(size)]


# -- the records (P3-190, P3-192) --------------------------------------------------------------------------------------------------------------

SENSITIVITY_FILE = "docs/revision/PHASE3_GI_SNAPSHOT_SENSITIVITY.json"
SNAPSHOT_FILE = "docs/revision/GI_DEVELOPMENT_SNAPSHOT_V1.json"
SELECTED_ON = "2026-11-11"
SNAPSHOT_STATUS = "GI_DEVELOPMENT_SNAPSHOT"
NOT_A = ("clinical calibration", "production profile", "authority-approved profile")
FACULTY_REFERENCES = ("A2-FD-013, A2-FD-015, A2-FD-020 (the behavioural regions; docs/revision/PHASE2_AMENDMENT_2.md)",
                      "FD-GI-01 (relative-to-arrival delivery, FD-P3-173)", "FD-GI-02 / FD-P3-176 (graded recovery, FD-P3-177)",
                      "FD-GI-03 (no recalibration to the legacy timings, FD-P3-173)", "FD-GI-04 (collapse architecture unchanged, FD-P3-173)")
SUPPORTING_TESTS = ("test_phase3_gi_development_snapshot.py", "test_phase3_gi_authority_readiness.py", "test_gi_snapshot_analysis.py (the harness)",
                    "test_phase3_gi_recovery_review.py (the FD-P3-176 invariant on the witnesses)")


def physical_record(course: Mapping) -> dict:
    """The recorded physical courses (what the shared core did, independent of the ten magnitudes) in a JSON-able form."""
    return {case: {scenario: {"order_minute": entry["order_minute"], **{key: list(values) for key, values in entry["physical"].items()}}
                   for scenario, entry in sorted(scenarios.items())} for case, scenarios in course.items()}


def course_of_record(record: Mapping) -> dict:
    return {case: {scenario: {"order_minute": entry["order_minute"],
                              "physical": {key: entry[key] for key in ("minute", "relative_delivery", "relative_perfusion", "pulse")}}
                   for scenario, entry in scenarios.items()} for case, scenarios in record.items()}


def snapshot_behaviour(values: Mapping[str, float], course: Mapping) -> dict:
    """What a profile does over the recorded courses, in the terms of the faculty's invariants (a record, not a judgement)."""
    out = {"untreated_events": {}, "category_sequences": {}, "recovery_invariant": {}, "rescue": {}}
    for case in CASES:
        out["untreated_events"][case] = event_times(values, course[case]["untreated"]["physical"])
        out["category_sequences"][case] = {scenario: category_sequence(values, entry["physical"]) for scenario, entry in sorted(course[case].items())}
        recovery = course[case]["recovery_after_severe"]
        out["recovery_invariant"][case] = recovery_invariant(values, recovery["physical"], recovery["order_minute"])
        out["rescue"][case] = {key: value for key, value in profile_metrics(values, course).items() if key.startswith(f"{case}/rescue_")}
    return out


def build_snapshot_record(values: Mapping[str, float], sensitivity: Mapping, course: Mapping) -> dict:
    import runtime_shadow as runtime
    lineage = runtime.CORE_LINEAGE[-1]
    share = margins(values)
    chosen = next(item for item in sensitivity["candidates"] if item["label"] == sensitivity["selected"])
    centre = next(item for item in sensitivity["candidates"] if item["label"] == "CENTER_REFERENCE")
    witness_events = {name: snapshot_behaviour(witness_values(name), course)["untreated_events"][CASES[0]] for name in ("LOW", "HIGH")}
    identity = {"snapshot_id": SNAPSHOT_ID, "version": 1, "values": dict(values),
                "common_core_lineage": {"version_id": lineage.version_id, "digest": lineage.digest},
                "region_bounds": {name: list(REGION[name]) for name in FIELDS}}
    record = {
        "record_type": "GI_DEVELOPMENT_SNAPSHOT", "snapshot_id": SNAPSHOT_ID, "version": 1, "status": SNAPSHOT_STATUS,
        "is_not": list(NOT_A), "family": "gi_bleed", "cases": list(CASES), "selected_on": SELECTED_ON,
        "common_core_lineage": {"version_id": lineage.version_id, "parent": lineage.parent, "digest": lineage.digest,
                                "certified_candidate": "ad7bf815e57e63c892ad2be7a63c5a8302a3e688",
                                "record": lineage.record},
        "amendment": "PHASE2_AMENDMENT_2", "values": dict(values), "value_status": sc.STATUS,
        "identifiability": {name: sc.IDENTIFIABILITY[name] for name in FIELDS},
        "region_bounds": {name: list(REGION[name]) for name in FIELDS},
        "margins_to_the_region_bounds": {name: round(value, 6) for name, value in share.items()}, "min_margin": round(min(share.values()), 6),
        "faculty_references": list(FACULTY_REFERENCES),
        "witnesses_preserved_for_ongoing_sensitivity_checks": {
            "LOW": witness_values("LOW"), "SELECTED_SNAPSHOT": SNAPSHOT_ID, "HIGH": witness_values("HIGH"),
            "note": "The region is NOT replaced by the point. LOW and HIGH stay as the bounding witnesses; the sweep of the full region "
                    "(the record PHASE3_GI_SNAPSHOT_SENSITIVITY) stays the check, because the two witnesses do not bound every event time.",
            "magnitudes_outside_the_low_high_bracket": chosen["outside_bracket"],
            "event_times_not_bounded_by_the_witnesses_minutes": {metric: item["minutes_not_bounded_by_the_witnesses"]
                                                                 for metric, item in sensitivity["corner_coverage"].items()},
        },
        "reference_witness_not_selected": {
            "CENTER_REFERENCE": witness_values("CENTER_REFERENCE"), "min_margin": centre["min_margin"],
            "magnitudes_on_a_region_bound": centre["on_a_bound"], "magnitudes_outside_the_low_high_bracket": centre["outside_bracket"],
            "why_not": "It is a test witness, not the midpoint of the region: two of its magnitudes (collapse_clear_tau, impending_burden) sit ON the "
                       "upper bound of their region and one lies outside the LOW..HIGH bracket. It fails the hard criterion H1 (strictly inside "
                       "every region) and is not chosen by default."},
        "selection": {
            "criteria": {"hard": [list(item) for item in HARD_CRITERIA], "ranked": [list(item) for item in RANKED_CRITERIA],
                         "near_boundary_threshold": NEAR_BOUNDARY, "broad_margin": BROAD_MARGIN},
            "rule": "Among the candidates strictly inside every region, the one with the largest minimum normalised margin to the region bounds (R1); "
                    "ties by fewest magnitudes outside the LOW..HIGH bracket (R2). For a box region the maximiser is UNIQUE: each magnitude at the "
                    "middle of its own faculty-approved region.",
            "candidates_evaluated": len(sensitivity["candidates"]), "winner": sensitivity["selected"],
            "inputs_of_the_rule": ["the region bounds", "the LOW and HIGH witnesses' values"],
            "legacy_input": False,
            "legacy_distance_reported_only": sensitivity["legacy_distance_reported_only"],
            "hard_criteria_evidence": {
                "H2_H3_invariant_violations_over_profiles": sensitivity["invariants"],
                "H4_case_difference_minutes": max(abs((a or 0) - (b or 0)) for a, b in zip(
                    [v for k, v in profile_metrics(values, course).items() if k.startswith(CASES[0] + "/") and isinstance(v, int)],
                    [v for k, v in profile_metrics(values, course).items() if k.startswith(CASES[1] + "/") and isinstance(v, int)]))},
        },
        "behaviour": snapshot_behaviour(values, course),
        "witness_untreated_events_for_comparison": witness_events,
        "uncertainty": {
            "all_ten_magnitudes": "FACULTY_DEFINED_DEVELOPMENT_BEHAVIORAL_REGION: none is validated clinically, none is calibrated.",
            "sensitivity_ranking": sensitivity["ranking"],
            "weakly_identified": [name for name in FIELDS if sc.IDENTIFIABILITY[name] == "WEAKLY_IDENTIFIED"],
            "event_time_range_over_the_region_minutes": {metric: [item["corners_min"], item["corners_max"]]
                                                        for metric, item in sensitivity["corner_coverage"].items()},
        },
        "falsifiers": [
            "an ordering or safety invariant violated at the snapshot on any recorded or new GI course (onset order, monotone untreated course, no collapse-led UNRESPONSIVE, no fall of F before the order, no two-band give-back)",
            "the FD-P3-176 recovery invariant failing on a physical recovery of the snapshot (0.80 to below 0.50 outside 6 to 8 min, more than 2 minutes left after the formal entry, or less than 79 % of the descent done before it)",
            "the independent evaluator and the live Amendment-2 channels disagreeing for the snapshot (the exactness test)",
            "a faculty change to a region bound that leaves the snapshot on, near (< 5 %) or outside a bound",
            "a new GI case, a new supported treatment or a new core lineage member that changes the physical course enough to change which magnitudes are HIGH_SENSITIVITY",
            "the common-core digest moving (a new amendment): the snapshot is then re-derived as a NEW version",
        ],
        "supporting_tests": list(SUPPORTING_TESTS),
        "authority": {"registered_as_an_authority_artifact": False, "common_core_runtime_authority": False,
                      "stored_in": "docs/revision (documentation); no authority store, no registry, no import by the layer or the app"},
        "immutability": {"rule": "This file is version 1 and is never edited. A change to ANY value, bound, lineage or reason is a NEW file "
                                 "(GI_DEVELOPMENT_SNAPSHOT_V2.json) that names this one in `supersedes`; this file keeps `superseded_by` unset and "
                                 "its digest is pinned by a test.",
                         "supersedes": None, "superseded_by": None, "identity_digest": digest(identity)},
    }
    record["immutability"]["record_digest"] = digest({key: value for key, value in record.items() if key != "immutability"})
    return record


def write_records(root: str, captures: Mapping) -> dict:
    """Regenerate both records from live captures (the harness's own use; the committed files are what the tests pin)."""
    import os
    course = course_from(captures)
    legacy = legacy_first_levels(captures[(CASES[0], "untreated")])
    sensitivity = build_sensitivity(course, legacy)
    values = region_midpoint()
    sensitivity = {"analysis_version": ANALYSIS_VERSION, "snapshot_id": SNAPSHOT_ID, "regions": {n: list(REGION[n]) for n in FIELDS},
                   "thresholds": {"high_swing_min": HIGH_SWING_MIN, "moderate_swing_min": MODERATE_SWING_MIN, "levels": list(LEVELS),
                                  "lhs_points": LHS_POINTS, "lhs_seed": LHS_SEED, "classified_metrics": list(CLASSIFIED),
                                  "reported_only_metrics": list(REPORTED_ONLY)},
                   "witness_values": {name: witness_values(name) for name in ("LOW", "CENTER_REFERENCE", "HIGH")},
                   "exactness": exactness(captures, {"LOW": witness_values("LOW"), "HIGH": witness_values("HIGH"), "CENTER_REFERENCE": values}),
                   "legacy_first_levels": legacy, "physical": physical_record(course), **sensitivity}
    snapshot = build_snapshot_record(values, sensitivity, course)
    for name, content in ((SENSITIVITY_FILE, sensitivity), (SNAPSHOT_FILE, snapshot)):
        path = os.path.join(root, name)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(content, handle, indent=1, sort_keys=True)
    return {"sensitivity": sensitivity, "snapshot": snapshot}
