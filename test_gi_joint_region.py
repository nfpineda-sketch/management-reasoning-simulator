"""P3-338 to P3-347: the joint GI rate / pressure region as an explicit object, its margins, three test witnesses and their blinded candidate trajectories.

Read-only and test-side (``MODEL_ANALYSIS``). Every number comes from the certified common core run on COUNTERFACTUAL copies of scenarios the real legacy
encounter captured (``dataclasses.replace`` of the bleed rate, the preload scale and the crystalloid kernel), and from the frozen faculty evaluators. Nothing
here edits ``clinical_core``, the family engine, a snapshot, a grant or a stored review; nothing is approved, and no point is chosen as a calibration.

What the faculty decided (FD-RATE-14 to FD-RATE-20) and what this module does with it:

* the one-unit window is read on the COMPLETE unit, at minute 30 (FD-RATE-14): the reading the feasibility analysis already used;
* the windows are regions and their centres are not targets (FD-RATE-15): nothing here optimises toward +13 mmHg or 25 %. ``CENTER_REFERENCE`` is the point
  FARTHEST FROM EVERY BOUNDARY (largest smallest margin), not the middle of a window;
* the rate is never a free scalar (FD-RATE-17): a point is ``(c = rate / scale, scale, kernel)`` and the rate is always ``c x scale``;
* the old CANDIDATE scale band is audited before a region outside it is formalised (FD-RATE-18);
* the candidate trajectories are for a NEW blinded human review; no earlier judgment is transferred (FD-RATE-20).

Regenerate the stored records and the review kit with ``MRS_WRITE_JOINT_REGION=1 python3 test_gi_joint_region.py``.
"""
from __future__ import annotations

import dataclasses
import functools
import hashlib
import json
import math
import os
import re
from pathlib import Path

import blood_volume_region as bvr
import test_gi_frg_crystalloid_analysis as fa
import test_gi_bleed_rate_analysis as ga
import test_gi_joint_feasibility_analysis as gj
import volume_behaviour_record as vbr

ROOT = Path(__file__).resolve().parent
RECORD_PATH = ROOT / "docs" / "revision" / "PHASE3_GI_JOINT_REGION_V1.json"
REVIEW_SET_PATH = ROOT / "docs" / "revision" / "PHASE3_JOINT_REGION_V1_CANDIDATE_REVIEW_SET.json"
BLIND_KEY_PATH = ROOT / "docs" / "revision" / "PHASE3_JOINT_REGION_V1_BLIND_KEY.json"
KIT_DIR = ROOT / "faculty_review_kit" / "region_conjunta_v1"
V1_SNAPSHOT_PATH = ROOT / "docs" / "revision" / "GI_DEVELOPMENT_SNAPSHOT_V1.json"
WRITE_FLAG = "MRS_WRITE_JOINT_REGION"
VERSION = "P3-339"
EVIDENCE_CLASS = "MODEL_ANALYSIS"
REGION_ID = "GI_JOINT_RATE_PRESSURE_DEVELOPMENT_REGION_V1"
REGION_STATUS = "JOINT_DEVELOPMENT_REGION__NOT_A_CALIBRATED_POINT__NOT_CLINICALLY_VALIDATED"
CANDIDATE_VERSION = "JOINT_REGION_V1_CANDIDATE"

CASES = gj.CASES
FRACTION = gj.COMMITTED_FRACTION
SCENARIOS = ("FR-B", "FR-C", "FR-E", "FR-G")
WITNESSES = ("LOW", "CENTER_REFERENCE", "HIGH")
RISE_FLOOR_CASE, RISE_CEILING_CASE = "gi_bleed_57m", "gi_bleed_72f"        # the lower arrival pressure meets the floor first, the higher one the ceiling
RISE_WINDOW = gj.PRBC_SBP_RISE_MMHG
SHARE_WINDOW = gj.SLOW_CRYSTALLOID_SHARE
ENVELOPES = {key: tuple(value) for key, value in vbr.EFFECTIVE_REGION.items()}
EXISTING_CONSTRAINTS = ("U-OUT", "U-HB", "FD-BLD-01", "FD-BLD-02", "SECOND-UNIT", "FD-BLD-03", "FD-BLD-04", "FD-BLD-05", "FD-BLD-06", "FD-BLD-07", "FD-BLD-08", "FD-BLD-09")

#: A witness counts as off the boundary when every margin is at least this share of its own window: 5 % of the one-unit window is 0.5 mmHg (half of the unit
#: the page displays) and 5 % of the slow-crystalloid window is one percentage point. An operational convention of this analysis, not a faculty decision.
ROBUST_FLOOR = 0.05
#: LOW and HIGH keep this share of the centre's smallest margin: the two ends, along the scale, of the part of the region that is still half as far from
#: every boundary as the centre is. Not the feasible endpoints (those have no margin at all).
LOW_HIGH_SHARE_OF_THE_CENTRE = 0.5
PERTURBATIONS = (0.005, 0.01)
PLACES = 9                        # c is of order 0.003: six places would not reproduce a witness from its stored binding
SEARCH_TOLERANCE = 1e-4


# -- P3-338: the old scale band ----------------------------------------------------------------------------------------------------------------------------

BAND_INTRODUCED = {"commit": "b4040ba", "date": "2026-10-23", "subject": "P2F-2..11: GI truth, candidate bands, registry, frozen rules, A9, dry run",
                   "what_the_commit_says": "the Level-2 registry (CANDIDATE 47, DEFAULT_UNMAPPED 4, SYNTHETIC_ONLY 2, FACULTY_APPROVED 0)"}
BAND_DECISION_ROWS = ("FD-P3-39", "FD-P3-42", "FD-P3-58", "FD-P3-59", "FD-P3-61")          # every Decision File row that named the scale before this audit
BAND_VERDICTS = {"A": "PURE_CANDIDATE_ANALYSIS_BAND", "B": "FACULTY_DEVELOPMENT_REGION", "C": "CERTIFIED_CONSTRAINT", "D": "UNCLEAR"}
SUPERSEDED = "SUPERSEDED_BY_JOINT_FEASIBILITY_ANALYSIS"


def section_old_band() -> dict:
    """What the band [600, 1500] mL-eq is, read from the certified core's own registry and from what consumes it. The registry is never edited."""
    from clinical_core import blood_constraints as bc
    from clinical_core import calibration
    from clinical_core import haemorrhage_probes as probes
    entry = calibration.REGISTRY["preload_curve_scale_ml"]
    counts = {status: sum(1 for item in calibration.REGISTRY.values() if item.status == status) for status in calibration.STATUSES}
    stronger = {"registry_status_is_faculty_approved": entry.status == calibration.FACULTY_APPROVED,
                "any_registry_entry_is_faculty_approved": counts[calibration.FACULTY_APPROVED] > 0,
                "a_faculty_decision_defines_the_band": False,
                "a_frozen_faculty_constraint_is_the_band": False,
                "a_runtime_validator_enforces_the_band": False}
    verdict = "A" if entry.status == calibration.CANDIDATE and not any(stronger.values()) else "D"
    return {"parameter": entry.name, "band_ml_eq": [entry.lower, entry.upper], "canonical_ml_eq": entry.canonical, "units": entry.units,
            "registry_status": entry.status, "registry_statuses_available": list(calibration.STATUSES), "registry_entries_by_status": counts,
            "registry_rationale": entry.rationale, "introduced": dict(BAND_INTRODUCED),
            "what_the_faculty_did_approve": "one POINT (833.33 mL-eq, with the six other values of gi_pressure_committed) for the development pressure experiment only (FD-P3-42): 'approving the point is not approving the clinical truth of each magnitude'; never the band",
            "canonical_provenance": "the registry's own reason is that the default 'keeps the legacy slope at position 0.5' (FD-P3-61): a legacy reconstruction, not clinical evidence",
            "decision_file_rows_that_named_the_scale_before_this_audit": list(BAND_DECISION_ROWS),
            "stronger_status_search": stronger,
            "stronger_status_search_basis": {"read_from_the_registry_now": ["registry_status_is_faculty_approved", "any_registry_entry_is_faculty_approved"],
                                             "recorded_from_a_manual_audit_not_recomputed": ["a_faculty_decision_defines_the_band", "a_frozen_faculty_constraint_is_the_band", "a_runtime_validator_enforces_the_band"],
                                             "what_the_manual_audit_read": "the Decision File rows that name the scale, clinical_core.blood_constraints and the runtime layer's validators"},
            "who_reads_the_band": {
                "the calibration sweep and the decision pack": "exploration grids inside the band; they select nothing",
                "the shadow region witnesses of Phase 3 (FD-P3-13)": "the corners of the declared region, used as development shadow witnesses; unchanged",
                "the certified core's own haemorrhage probes": {"scales_explored_ml_eq": list(probes.SCALES), "largest": max(probes.SCALES),
                                                               "note": "explored, never approved: the certified core already ran scales up to twice the band's top"},
                "the frozen blood evaluator": {"reading_state": dict(bc.BLOOD_READING), "note": "it READS its haemoglobin constraints at one fixed state whose scale is the band's top; a reading convention, not a constraint on the scale, and not changed by this audit"}},
            "verdict": verdict, "name": BAND_VERDICTS[verdict],
            "supersession": {"mark": SUPERSEDED if verdict == "A" else None, "authorised_by": "FD-RATE-18",
                             "scope": "the current joint analysis only: the band stops being read as the domain of the joint region",
                             "recorded_in": ["this record", "the Decision File (FD-RATE-18)", "the debt register"],
                             "registry_edited": False, "registry_still_says": f"{entry.status} [{entry.lower:g}, {entry.upper:g}]",
                             "why_the_registry_is_not_edited": "it lives in clinical_core, whose certified digest covers every source; carrying the mark there needs a certified successor of the core",
                             "rewrites_historical_evidence": False}}


# -- the kernel family: the least-retaining kernel at a given depth inside the closed crystalloid region ---------------------------------------------------

@functools.lru_cache(maxsize=None)
def _kernel_cells() -> tuple:
    cells = []
    for index in range(fa.REGION_S_STEPS):
        s = round(0.005 + 0.01 * index, 3)
        for step in range(fa.REGION_TAU_STEPS + 1):
            tau = round(math.exp(math.log(600.0) * step / fa.REGION_TAU_STEPS), 3)
            unit = {key: (bvr.peak_share(1.0, s, tau) if key == "peak" else bvr.retained_share(1.0, s, tau, float(key))) for key in ENVELOPES}
            cells.append((s, tau, unit, fa.retained_ml(1000.0, 60, 1.0, s, tau, 60)))
    return tuple(cells)


@functools.lru_cache(maxsize=None)
def _kernel_at(depth_key: int):
    depth = depth_key / 1e6
    shrunk = {key: (low + depth * (high - low), high - depth * (high - low)) for key, (low, high) in ENVELOPES.items()}
    best = None
    for s, tau, unit, retained_per_e in _kernel_cells():
        low = max(shrunk[key][0] / unit[key] for key in shrunk)
        high = min(min(shrunk[key][1] / unit[key] for key in shrunk), fa.REGION_DOMAIN_E_MAX)
        if low > high:
            continue
        if best is None or low * retained_per_e < best[0]:
            best = (low * retained_per_e, low, s, tau)
    return None if best is None else (best[1], best[2], best[3])


def kernel_at_depth(depth: float):
    """The LEAST-retaining kernel (smallest retention at minute 60 of 1 L over 60 min) whose four closed-region behaviours are each at least ``depth`` of their
    own window away from both bounds. ``depth = 0`` is the least protective kernel of the closed region; ``None`` when no kernel is that deep.
    The same (s, tau) scan P3-304 used, with the envelopes shrunk."""
    return _kernel_at(int(round(depth * 1e6)))


def retained_60(kernel) -> float:
    return fa.retained_ml(1000.0, 60, kernel[0], kernel[1], kernel[2], 60)


def kernel_margin(kernel) -> dict:
    behaviour = bvr.behaviour(kernel[0], kernel[1], kernel[2], times=(30.0, 60.0, 120.0))
    per = {}
    for key, (low, high) in ENVELOPES.items():
        value = behaviour["peak" if key == "peak" else float(key)]
        per[str(key)] = {"value": value, "window": [low, high], "to_lower": value - low, "to_upper": high - value,
                         "normalized": min(value - low, high - value) / (high - low), "nearest": "lower" if value - low <= high - value else "upper"}
    nearest = min(per, key=lambda key: per[key]["normalized"])
    return {"behaviour_on_a_1L_20min_bag": {key: item["value"] for key, item in per.items()}, "per_envelope": per, "normalized": per[nearest]["normalized"],
            "nearest": f"{nearest}:{per[nearest]['nearest']}", "retained_at_60_of_1L_over_60min_ml": retained_60(kernel)}


# -- P3-339: the region as an object -------------------------------------------------------------------------------------------------------------------------

@dataclasses.dataclass(frozen=True)
class Point:
    """One point of the joint region. The bleed rate is NOT a field: it is ``c x scale`` and cannot be set apart from the scale."""

    c: float                # bleed rate over preload scale, per minute: the one thing the untreated course reads
    scale: float            # preload scale, mL-eq: the one thing the one-unit response reads
    kernel: tuple           # (e, s, tau) of the crystalloid retention kernel, inside the closed crystalloid region
    fraction: float = FRACTION

    @property
    def rate(self) -> float:
        return self.c * self.scale

    def binding(self) -> dict:
        return {"bleed_rate_ml_eq_per_min": self.rate, "preload_scale_ml_eq": self.scale, "c_rate_over_scale_per_min": self.c, "arrival_position": self.fraction,
                "crystalloid_kernel": {"e": self.kernel[0], "s": self.kernel[1], "tau_min": self.kernel[2]}}


def _last_true(predicate, low: float, high: float, tolerance: float = SEARCH_TOLERANCE) -> float:
    """The largest value in [low, high] where ``predicate`` still holds (it holds at ``low``; returned from the holding side)."""
    if predicate(high):
        return high
    while high - low > tolerance:
        middle = (low + high) / 2.0
        if predicate(middle):
            low = middle
        else:
            high = middle
    return low


class JointRegion:
    """The joint region in its minimum independent coordinates ``(c, scale, kernel)`` at the committed arrival position.

    A: c inside the window the frozen untreated envelopes (U-OUT) admit for BOTH cases;
    B: the complete unit raises SBP by +8 .. +18 mmHg at minute 30 in BOTH cases (reads the scale only);
    C: 1 L over 60 min prevents 15 .. 35 % of the untreated deterioration at minute 60 (reads c x scale and the kernel);
    K: the kernel's four behaviours are inside the closed crystalloid region;
    R: every existing frozen constraint can be read and is met (a ceiling on the rate c x scale).
    """

    def __init__(self, ctx: dict):
        self.ctx = ctx
        self.a, self.b = gj.constraint_a(FRACTION), gj.constraint_b(ctx, FRACTION)
        self.c_low, self.c_high = self.a["common_c"]
        self.scale_low, self.scale_high = self.b["common_scale_ml_eq"]
        published = gj.load_record()["feasibility"]["with_every_existing_constraint_readable_and_met"]
        self.rate_floor, self.rate_limit_published = published["bleed_rate_ml_min"]
        self._limits: dict = {}

    # the three faculty readings
    def rises(self, scale: float) -> dict:
        return {case: gj.prbc_rise(self.ctx, case, scale) for case in CASES}

    def share(self, point: Point, case: str = ga.FRG_CASE) -> float:
        return gj.slow_share(self.ctx, case, point.rate, point.scale, point.kernel)

    def readable_limit(self, kernel) -> float:
        """The fastest bleed rate at which the frozen evaluator still reads every existing constraint with this kernel."""
        key = tuple(round(value, 6) for value in kernel)
        if key not in self._limits:
            middle = (self.c_low + self.c_high) / 2.0
            found = gj.readable_rate_limit(middle, self.rate_floor, 12.0, kernel)
            self._limits[key] = 12.0 if found is None else found
        return self._limits[key]

    def scale_at_floor_margin(self, margin: float) -> float:
        """The largest scale at which the one-unit rise is still ``margin`` of its window above the floor (in the case that meets the floor first)."""
        target = RISE_WINDOW[0] + margin * (RISE_WINDOW[1] - RISE_WINDOW[0])
        return _last_true(lambda scale: gj.prbc_rise(self.ctx, RISE_FLOOR_CASE, scale) >= target, self.scale_low, self.scale_high, 1e-3)

    def margins(self, point: Point, *, limit: float | None = None) -> dict:
        width_a = self.c_high - self.c_low
        rises = self.rises(point.scale)
        to_floor, to_ceiling = min(rises.values()) - RISE_WINDOW[0], RISE_WINDOW[1] - max(rises.values())
        share = self.share(point)
        kernel = kernel_margin(point.kernel)
        limit = self.readable_limit(point.kernel) if limit is None else limit
        out = {
            "A_untreated": {"c": point.c, "window": [self.c_low, self.c_high], "to_lower": point.c - self.c_low, "to_upper": self.c_high - point.c,
                            "to_upper_as_a_share_of_c": (self.c_high - point.c) / point.c, "to_lower_as_a_share_of_c": (point.c - self.c_low) / point.c,
                            "normalized": min(point.c - self.c_low, self.c_high - point.c) / width_a, "nearest": "upper" if self.c_high - point.c <= point.c - self.c_low else "lower"},
            "B_one_unit": {"sbp_rise_at_30_mmHg": rises, "window_mmHg": list(RISE_WINDOW), "to_floor_mmHg": to_floor, "to_ceiling_mmHg": to_ceiling,
                           "normalized": min(to_floor, to_ceiling) / (RISE_WINDOW[1] - RISE_WINDOW[0]), "nearest": "floor" if to_floor <= to_ceiling else "ceiling"},
            "C_slow_crystalloid": {"share_prevented_at_60": share, "window": list(SHARE_WINDOW), "to_floor": share - SHARE_WINDOW[0], "to_ceiling": SHARE_WINDOW[1] - share,
                                   "normalized": min(share - SHARE_WINDOW[0], SHARE_WINDOW[1] - share) / (SHARE_WINDOW[1] - SHARE_WINDOW[0]),
                                   "nearest": "ceiling" if SHARE_WINDOW[1] - share <= share - SHARE_WINDOW[0] else "floor"},
            "K_closed_crystalloid_region": kernel,
            "R_existing_constraints_readable": {"bleed_rate_ml_eq_per_min": point.rate, "fastest_readable_rate_ml_eq_per_min": limit, "to_limit_ml_eq_per_min": limit - point.rate,
                                                "normalized": (limit - point.rate) / (limit - self.rate_floor), "nearest": "the readability limit of the frozen evaluator",
                                                "note": "a limit of READING, not a faculty constraint; normalised by the rate span of the verified region"}}
        smallest = min(out, key=lambda name: out[name]["normalized"])
        out["smallest"] = {"constraint": smallest, "normalized": out[smallest]["normalized"], "nearest": out[smallest]["nearest"]}
        return out

    def contains(self, point: Point, *, limit: float | None = None) -> bool:
        return self.margins(point, limit=limit)["smallest"]["normalized"] >= 0.0

    def existing(self, point: Point) -> dict:
        """Every EXISTING frozen constraint at this point, per case, from the frozen evaluator itself."""
        return {case: gj.frozen_verdicts(case, point.rate, point.scale, point.fraction, point.kernel) for case in CASES}

    # the balanced family: every faculty margin equal to ``v``
    def balanced(self, margin: float):
        kernel = kernel_at_depth(margin)
        if kernel is None:
            return None
        return Point(self.c_high - margin * (self.c_high - self.c_low), self.scale_at_floor_margin(margin), kernel)

    def share_margin(self, point: Point) -> float:
        share = self.share(point)
        return min(share - SHARE_WINDOW[0], SHARE_WINDOW[1] - share) / (SHARE_WINDOW[1] - SHARE_WINDOW[0])


def formal_description(region: JointRegion) -> dict:
    middle_c = (region.c_low + region.c_high) / 2.0
    lattice = []
    for c in (region.c_low, middle_c, region.c_high):
        for scale in (2300.0, 2600.0, 2900.0, region.scale_high):
            deepest = _last_true(lambda depth: kernel_at_depth(depth) is not None and gj.slow_share(region.ctx, ga.FRG_CASE, c * scale, scale, kernel_at_depth(depth)) <= SHARE_WINDOW[1],
                                 0.0, 0.5) if gj.slow_share(region.ctx, ga.FRG_CASE, c * scale, scale, kernel_at_depth(0.0)) <= SHARE_WINDOW[1] else None
            lattice.append({"c": c, "scale_ml_eq": scale, "bleed_rate_ml_eq_per_min": c * scale,
                            "inside_for_some_kernel": deepest is not None,
                            "deepest_compatible_kernel_depth": deepest,
                            "largest_compatible_retention_at_60_ml": None if deepest is None else retained_60(kernel_at_depth(deepest)),
                            "readable": c * scale <= region.rate_limit_published})
    return {"id": REGION_ID, "status": REGION_STATUS, "is_not": ["a calibrated point", "an approved parameter set", "a clinically measured blood-loss rate", "independent scalar ranges"],
            "coordinates": {"c": "bleed rate / preload scale, per minute", "scale": "preload scale, mL-eq", "kernel": "(e, s, tau) of the crystalloid retention kernel",
                            "held": {"arrival_position": FRACTION, "kappa": 1.0}, "bleed_rate": "never a coordinate: always c x scale (FD-RATE-17)"},
            "membership": {
                "A_untreated": {"rule": "c_low <= c <= c_high", "c_window": [region.c_low, region.c_high], "per_case_c": region.a["per_case_c"], "source": "the frozen U-OUT faculty envelopes, both cases"},
                "B_one_unit": {"rule": "scale_low <= scale <= scale_high", "scale_window_ml_eq": [region.scale_low, region.scale_high], "per_case_scale_ml_eq": region.b["per_case_scale_ml_eq"],
                               "source": "FD-RATE-09 as clarified by FD-RATE-14: the complete unit, +8 .. +18 mmHg at minute 30, both cases",
                               "closed_form": "SBP rise = SBP_arrival x (1 - f)(1 - exp(-kappa x 300 / scale)) / f"},
                "C_slow_crystalloid": {"rule": "0.15 <= share(c x scale, scale, kernel) <= 0.35", "source": "FD-RATE-10",
                                       "closed_form": "share = 1 - (exp(d_t) - 1) / (exp(d_u) - 1), with d_u the untreated effective-volume deficit at minute 60 over the scale and d_t = d_u - retained_60(kernel) / scale; to first order share = retained_60 / (volume lost in 60 min)",
                                       "couples": "all three coordinates: it is why the ranges cannot be read apart"},
                "K_closed_crystalloid_region": {"rule": "the kernel's Rpeak, R30, R60 and R120 on a 1 L / 20 min bag inside the closed region", "envelopes": {str(key): list(value) for key, value in ENVELOPES.items()},
                                                "source": "volume_behaviour_record.EFFECTIVE_REGION (FACULTY_DEFINED_BEHAVIORAL_REGION), not modified (FD-RATE-12)"},
                "R_existing_constraints": {"rule": "every existing frozen constraint readable and met: in practice c x scale <= the readability limit", "limit_ml_eq_per_min_published": region.rate_limit_published,
                                           "source": "clinical_core.blood_constraints, unchanged"}},
            "kernel_family_used": {"what": "for each depth d in the closed region, the least-retaining kernel whose four behaviours are at least d of their window from both bounds",
                                   "depth_0": {"kernel": list(kernel_at_depth(0.0)), "retained_at_60_ml": retained_60(kernel_at_depth(0.0))},
                                   "limit": "the family is one curve through the closed region (the one most favourable to C at each depth); other kernels of the same depth retain more and are compatible on a smaller part of (c, scale)"},
            "compatible_retention_on_a_lattice": lattice,
            "projections_are_not_ranges": {"bleed_rate_ml_eq_per_min": [region.rate_floor, region.rate_limit_published],
                                           "scale_ml_eq": [gj.load_record()["feasibility"]["with_every_existing_constraint_readable_and_met"]["scale_ml_eq"][0],
                                                           gj.load_record()["feasibility"]["with_every_existing_constraint_readable_and_met"]["scale_ml_eq"][1]],
                                           "warning": "a rate from one end with a scale from the other is OUTSIDE the region: only c x scale pairs inside A are points"}}


# -- P3-340 and P3-341: geometry, margins and the three witnesses --------------------------------------------------------------------------------------------

def solve_witnesses(region: JointRegion) -> dict:
    """CENTER_REFERENCE: the largest margin every constraint can keep at once. LOW / HIGH: the two ends, along the scale, of the part of the region that still
    keeps half of that margin."""
    def holds(margin: float) -> bool:
        point = region.balanced(margin)
        return point is not None and region.share_margin(point) >= margin

    centre_margin = _last_true(holds, 0.0, 0.5)
    centre = region.balanced(centre_margin)
    half = centre_margin * LOW_HIGH_SHARE_OF_THE_CENTRE
    width_a = region.c_high - region.c_low
    # LOW: the smallest scale at which every margin is still ``half`` (c at its upper allowance, the least-retaining kernel of that depth)
    low_c, low_kernel = region.c_high - half * width_a, kernel_at_depth(half)
    low_scale_high = centre.scale
    low_reaches = lambda scale: region.share_margin(Point(low_c, scale, low_kernel)) >= half          # noqa: E731
    span = low_scale_high - region.scale_low
    low_scale = low_scale_high - _last_true(lambda back: low_reaches(low_scale_high - back), 0.0, span, 1e-2)
    low = Point(low_c, low_scale, low_kernel)
    # HIGH: the largest scale at which the one-unit margin is still ``half``; c and the kernel depth then keep the remaining margins as large as they can be
    high_scale = region.scale_at_floor_margin(half)
    limit = region.readable_limit(kernel_at_depth(half))

    def rest(c: float):
        a_margin = min(c - region.c_low, region.c_high - c) / width_a
        r_margin = (limit - c * high_scale) / (limit - region.rate_floor)
        depth = _last_true(lambda d: kernel_at_depth(d) is not None and region.share_margin(Point(c, high_scale, kernel_at_depth(d))) >= d, 0.0, 0.5)
        return a_margin, r_margin, depth

    def rising_side_wins(c: float) -> bool:          # while the margins that GROW with c are still below the readability margin, a larger c is better
        a_margin, r_margin, depth = rest(c)
        return min(a_margin, depth) <= r_margin

    middle_c = (region.c_low + region.c_high) / 2.0
    high_c = _last_true(rising_side_wins, region.c_low + half * width_a, middle_c, 1e-7)
    high = Point(high_c, high_scale, kernel_at_depth(rest(high_c)[2]))
    return {"centre_margin": centre_margin, "half_margin": half, "LOW": low, "CENTER_REFERENCE": centre, "HIGH": high}


WITNESS_REASONS = {
    "LOW": "the SMALLEST scale at which every margin is still half of the centre's: the strongest one-unit response and the largest slow-crystalloid share the region allows without touching a boundary",
    "CENTER_REFERENCE": "the point FARTHEST FROM EVERY BOUNDARY: the untreated, one-unit, slow-crystalloid and closed-region margins are all equal and as large as they can be together; it is not the middle of any window",
    "HIGH": "the LARGEST scale at which the one-unit margin is still half of the centre's, with c and the kernel placed to keep the remaining margins as large as possible: the weakest one-unit response and the smallest slow-crystalloid share of the three"}


def perturbation(region: JointRegion, point: Point, limit: float) -> dict:
    """Does the witness stay inside when ONE bound parameter is moved alone by a small relative amount? (The rate alone moves c; the scale alone moves c the other way.)"""
    out = {}
    for size in PERTURBATIONS:
        moves = {}
        for sign in (-1.0, 1.0):
            factor = 1.0 + sign * size
            label = f"{'+' if sign > 0 else '-'}{size:g}"
            moves[f"bleed_rate {label}"] = region.contains(Point(point.c * factor, point.scale, point.kernel), limit=limit)
            moves[f"scale {label}"] = region.contains(Point(point.c / factor, point.scale * factor, point.kernel), limit=limit)
            moves[f"kernel_e {label}"] = region.contains(Point(point.c, point.scale, (point.kernel[0] * factor, point.kernel[1], point.kernel[2])), limit=limit)
        out[f"{size:g}"] = {"moves": moves, "stays_inside_under_every_move": all(moves.values())}
    return out


def section_geometry(region: JointRegion, solved: dict) -> dict:
    width_a = region.c_high - region.c_low
    profile = []
    for scale in (2300.0, 2450.0, 2600.0, 2750.0, 2900.0, 3050.0):
        rises = region.rises(scale)
        b_margin = min(min(rises.values()) - RISE_WINDOW[0], RISE_WINDOW[1] - max(rises.values())) / (RISE_WINDOW[1] - RISE_WINDOW[0])

        def others_hold(margin: float, scale=scale) -> bool:
            kernel = kernel_at_depth(margin)
            return kernel is not None and region.share_margin(Point(region.c_high - margin * width_a, scale, kernel)) >= margin

        rest = _last_true(others_hold, 0.0, 0.5) if others_hold(0.0) else None
        rate = None if rest is None else (region.c_high - rest * width_a) * scale
        profile.append({"scale_ml_eq": scale, "one_unit_margin": b_margin, "largest_equal_margin_of_the_untreated_crystalloid_and_kernel_constraints": rest,
                        "smallest_margin_at_this_scale": None if rest is None else min(b_margin, rest),
                        "dominant": None if rest is None else ("B_one_unit (floor, 57m)" if b_margin < rest else "C_slow_crystalloid (ceiling) with A and K"),
                        "bleed_rate_there_ml_eq_per_min": rate, "readable": None if rate is None else rate <= region.rate_limit_published})
    corner_low = Point(region.c_high, gj.load_record()["feasibility"]["projections"]["scale_ml_eq"][0], kernel_at_depth(0.0))
    corner_high = Point(region.c_low, region.scale_high, kernel_at_depth(0.0))
    return {"normalisation": "each margin is the distance to the nearest bound of its own constraint over the width of that constraint's window (A: the c window; B: 10 mmHg; C: 20 percentage points; K: each closed-region envelope; R: the rate span of the verified region)",
            "profile_along_the_scale": profile,
            "dominant_constraints": {"at_small_scales": "C: the 35 % ceiling of the slow-crystalloid share, together with the closed region's floor (K) and the fast edge of the untreated window (A)",
                                     "at_large_scales": "B: the +8 mmHg floor of the complete unit in 57m",
                                     "at_fast_rates": "R: the frozen evaluator can no longer READ FD-BLD-06 in 57m",
                                     "never_binding_inside_the_region": ["the +18 mmHg ceiling of one unit", "the 15 % floor of the slow-crystalloid share", "the upper bounds of the closed crystalloid region"]},
            "fragile_corners": [
                {"where": "smallest scale, fastest admitted untreated course, least-retaining closed-region kernel", "point": corner_low.binding(),
                 "margins_normalized": {name: item["normalized"] for name, item in region.margins(corner_low).items() if name != "smallest"},
                 "why_fragile": "three constraints meet: the share ceiling (C), the closed region's floor (K) and the fast edge of the untreated window (A)"},
                {"where": "largest scale, slowest admitted untreated course", "point": corner_high.binding(),
                 "margins_normalized": {name: item["normalized"] for name, item in region.margins(corner_high).items() if name != "smallest"},
                 "why_fragile": "the complete unit is exactly at its +8 mmHg floor in 57m, at the slow edge of the untreated window"}],
            "interior": {"largest_smallest_margin": solved["centre_margin"], "reached_at": "CENTER_REFERENCE",
                         "in_natural_units": {"one_unit_above_its_floor_mmHg": solved["centre_margin"] * (RISE_WINDOW[1] - RISE_WINDOW[0]),
                                              "share_below_its_ceiling_points": solved["centre_margin"] * (SHARE_WINDOW[1] - SHARE_WINDOW[0]) * 100.0,
                                              "c_below_the_fast_edge_as_a_share_of_c": solved["centre_margin"] * width_a / solved["CENTER_REFERENCE"].c},
                         "half_margin_core_scale_ml_eq": [solved["LOW"].scale, solved["HIGH"].scale],
                         "reading": "the region is NARROW: its most interior point keeps about an eighth of each window; the untreated window is itself under a tenth of c wide"},
            "robust_floor": {"value": ROBUST_FLOOR, "meaning": "5 % of a window: 0.5 mmHg of the one-unit window (half of a displayed mmHg), one percentage point of the slow-crystalloid window",
                             "status": "an operational convention of this analysis, not a faculty decision"}}


def section_witnesses(region: JointRegion, solved: dict) -> dict:
    out = {}
    for label in WITNESSES:
        point = solved[label]
        limit = region.readable_limit(point.kernel)
        margins = region.margins(point, limit=limit)
        existing = region.existing(point)
        every_existing = all(item.get("readable") and all(item.get(name) is True for name in EXISTING_CONSTRAINTS) for item in existing.values())
        faculty = {name: margins[name]["normalized"] for name in ("A_untreated", "B_one_unit", "C_slow_crystalloid")}
        out[label] = {"role": "DEVELOPMENT_TEST_WITNESS", "is_a_calibrated_point": False, "is_clinically_preferred": False, "why": WITNESS_REASONS[label],
                      "binding": point.binding(), "bound_together": "the rate, the scale and the kernel of this witness were found together; none may be replaced by another witness's value",
                      "margins": margins, "satisfies_all_three_faculty_constraints": all(value >= 0.0 for value in faculty.values()),
                      "inside_the_closed_crystalloid_region": margins["K_closed_crystalloid_region"]["normalized"] >= 0.0,
                      "on_a_boundary": margins["smallest"]["normalized"] < ROBUST_FLOOR,
                      "existing_constraints_frozen_evaluator": existing, "every_existing_constraint_readable_and_met": every_existing,
                      "one_unit_sbp_rise_at_30_mmHg": margins["B_one_unit"]["sbp_rise_at_30_mmHg"], "slow_crystalloid_share_at_60": margins["C_slow_crystalloid"]["share_prevented_at_60"],
                      "kernel_retained_at_60_of_1L_over_60min_ml": retained_60(point.kernel),
                      "single_parameter_moves": perturbation(region, point, limit)}
    return out


# -- P3-342 .. P3-345: the candidate trajectories --------------------------------------------------------------------------------------------------------------

_REASONING_TAIL = re.compile(r"\n\s*\n\s*Guided reasoning completion:.*", re.S)


def capture_reviewed(scenario_id: str) -> dict:
    """The reviewed scripted scenario run again through the real legacy encounter with the page's turn timing: the shadow scenario the core replays, and the
    heart rate and capillary refill the encounter showed at each turn (the context the earlier review displayed beside the pressure)."""
    import pilot_acceptance as acceptance
    import runtime_shadow as rs
    import runtime_shadow_evidence as ev
    item = fa.reviewed_item(scenario_id)
    case, orders = fa.reviewed_orders(scenario_id)
    context = {}
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter(case)
        seen = encounter.state["observable"]
        context[0] = {"hr": seen.get("hr"), "crt": seen.get("crt")}
        for text in fa.page_turns(orders):
            encounter.order(text)
            seen = encounter.state["observable"]
            context[int(round(float(encounter.state["sim_time"])))] = {"hr": seen.get("hr"), "crt": seen.get("crt")}
        scenario = encounter.shadow.runner.replay_input().scenario
    return {"item": item, "case": case, "orders": orders, "scenario": scenario, "encounter_context": context}


def overlay_amendment():
    """The Amendment-2 profile of ``GI_DEVELOPMENT_SNAPSHOT_V1`` (the consciousness overlay whose ESTABLISHED collapse is the experiment's stopping boundary)."""
    from clinical_core import systemic_consciousness as sc
    values = json.loads(V1_SNAPSHOT_PATH.read_text(encoding="utf-8"))["values"]
    return sc.Amendment2Profile(**{name: float(values[name]) for name in sc.FIELDS})


def simulate(scenario: dict, minutes: int, point: Point | None = None, *, drop: tuple = (), overlay=None) -> dict:
    """One run of the certified core on COUNTERFACTUAL copies. ``point = None`` keeps the captured (current) configuration; ``drop`` removes a treatment to
    measure what it causes; ``overlay`` adds the consciousness overlay so the experiment's own stopping boundary can be read."""
    from clinical_core import integration
    from clinical_core import systemic_consciousness as sc
    from clinical_core.interventions.fluids import Crystalloid
    anchors, contributors, _captured, profile = integration.scenario_from_dict(scenario)
    made = []
    for item in contributors:
        name = type(item).__name__
        if isinstance(item, Crystalloid):
            if "crystalloid" in drop:
                continue
            if point is not None:
                item = dataclasses.replace(item, effective_ml_per_ml=float(point.kernel[0]), transient_share=float(point.kernel[1]), leak_tau_min=float(point.kernel[2]))
        elif name == "PackedRedCells":
            if "red_cells" in drop:
                continue
        elif name == "GIHaemorrhage" and point is not None:
            item = dataclasses.replace(item, blood_loss_ml_per_min=float(point.rate))
        made.append(item)
    if point is not None:
        profile = dataclasses.replace(profile, preload_curve_scale_ml=float(point.scale), arrival_preload_fraction=float(point.fraction))
    if overlay is not None:
        profile = dataclasses.replace(profile, amendment_2=overlay)
    stopped = None
    try:
        trajectory = integration.run(anchors, made, minutes, profile)
    except Exception as error:                       # the core's own boundary: reported, never worked around
        found = re.search(r"minute (\d+)", str(error))
        if found is None:
            raise
        stopped = int(found.group(1))
        trajectory = integration.run(anchors, made, stopped - 1, profile)
    rows = fa.per_minute(trajectory, anchors, profile)
    established = None
    if overlay is not None:
        readings = trajectory.derived()
        for minute in range(1, len(trajectory.states)):
            try:
                state = sc.readout(trajectory.states[minute], anchors, profile, readings[minute].pressure_rel, readings[minute].delivery_rel)["collapse"]["state"]
            except Exception:                        # an unreadable minute is a boundary too: the authority fails closed
                state = sc.ESTABLISHED
            if state == sc.ESTABLISHED:
                established = minute
                break
    return {"rows": rows, "unresolved_boundary_minute": stopped, "first_established_collapse_minute": established}


def displayed(rows, minute: int) -> dict:
    """The pressure the page shows at a committed minute: whole mmHg, MAP by the screen's convention on the displayed values."""
    sbp, dbp = round(rows[minute]["sbp"]), round(rows[minute]["dbp"])
    return {"minute": minute, "sbp": float(sbp), "dbp": float(dbp), "map": float(int(round((sbp + 2 * dbp) / 3)))}


def reviewer_view(item: dict, pressures=None, context=None) -> dict:
    """What the earlier faculty trajectory review showed for a scenario before its first pass was locked -- title, context, purpose, arrival, what was done,
    the pressure points, heart rate and capillary refill -- with the pressure points replaced when ``pressures`` is given. No comparator, no identifier, no
    parameter. The test compares it, key by key, with the review page's own blind view of the stored item."""
    view = dict(item["bundle"]["authority_view"])
    arrival = dict(item["arrival"])
    timeline, number = [], 0
    for entry in view.get("management_timeline") or ():
        entry = dict(entry)
        number += 1
        actions = [str(action) for action in entry.get("actions") or () if action]
        executed = entry.get("status") in ("executed", "information", "examined")
        timeline.append({"n": number, "minute": entry.get("decision_time_min"), "advance": entry.get("elapsed_minutes"),
                         "action": _REASONING_TAIL.sub("", str(entry.get("input") or "")).strip(),
                         "result": "; ".join(actions) if actions else (f"{entry.get('elapsed_minutes')} min passed" if executed and entry.get("elapsed_minutes") else "—")})
    points = pressures if pressures is not None else [dict(row) for row in view.get("authoritative_pressure_timeline") or ()]
    common = [{"minute": 0, "sbp": float(arrival["sbp"]), "dbp": float(arrival["dbp"]), "map": float(arrival["map"])}]
    common += [{"minute": int(row["minute"]), "sbp": float(row["sbp"]), "dbp": float(row["dbp"]), "map": float(row["map"])} for row in points]
    shown = context if context is not None else [dict(row) for row in item.get("context_vitals") or ()]
    return {"scenario_id": item["scenario_id"], "title": item["title"], "context": item["clinical_context"], "purpose": PURPOSE_SHOWN.get(item["scenario_id"], item["reason"]),
            "arrival": arrival, "timeline": timeline, "common": common,
            "heart_rate_and_capillary_refill": [{"minute": row["minute"], "hr": row.get("hr"), "crt": row.get("crt")} for row in shown]}


#: The page shows only the part of FR-E's purpose it asks about (faculty_trajectory_review.PURPOSE_OVERRIDES); the test holds the two texts equal.
PURPOSE_SHOWN = {"FR-E": "Is the recovery after delayed treatment coherent in direction, timing and magnitude?"}


def section_candidates(ctx: dict, witnesses: dict) -> dict:
    overlay = ctx["overlay"]
    out = {}
    for scenario_id in SCENARIOS:
        captured = ctx["reviewed"][scenario_id]
        item, scenario, case = captured["item"], captured["scenario"], captured["case"]
        committed = [int(row["minute"]) for row in item["bundle"]["authority_view"]["authoritative_pressure_timeline"]]
        horizon = committed[-1]
        stored = {int(row["minute"]): (row["sbp"], row["dbp"], row["map"]) for row in item["bundle"]["authority_view"]["authoritative_pressure_timeline"]}
        current = simulate(scenario, horizon)
        current_points = [displayed(current["rows"], minute) for minute in committed]
        context_stored = {int(row["minute"]): (row.get("hr"), row.get("crt")) for row in item["context_vitals"]}
        context_now = {minute: (values["hr"], values["crt"]) for minute, values in captured["encounter_context"].items()}
        reproduction = {"pressures_equal_the_reviewed_trajectory": all((point["sbp"], point["dbp"], point["map"]) == tuple(float(v) for v in stored[point["minute"]]) for point in current_points),
                        "heart_rate_and_capillary_refill_equal_the_reviewed_context": all(context_now.get(minute) == values for minute, values in context_stored.items()),
                        "what_it_shows": "run at the CURRENT configuration, this harness gives exactly what the earlier review displayed: the candidates differ from it only by the witness"}
        by_witness = {}
        for label in WITNESSES:
            point = _point_of(witnesses[label])
            run = simulate(scenario, horizon, point)
            guard = simulate(scenario, horizon, point, overlay=overlay)
            pressures = [displayed(run["rows"], minute) for minute in committed if minute < len(run["rows"])]
            rows = run["rows"]
            by_witness[label] = {
                "version": CANDIDATE_VERSION, "case_id": case, "committed_minutes": committed,
                "pressures": pressures,
                "technical_at_the_committed_minutes": [{"minute": minute, "sbp": rows[minute]["sbp"], "dbp": rows[minute]["dbp"], "map": rows[minute]["map"],
                                                        "effective_volume_change_ml_eq": rows[minute]["V"], "blood_lost_ml": rows[minute]["bleed_cum_ml"],
                                                        "crystalloid_retained_ml": rows[minute]["net_retained_crystalloid_ml"], "hb_g_dl": rows[minute]["hb"]}
                                                       for minute in [0] + committed if minute < len(rows)],
                "complete_to_the_last_committed_minute": len(pressures) == len(committed),
                "unresolved_boundary_minute": run["unresolved_boundary_minute"],
                "experiment_would_stop": guard["first_established_collapse_minute"] is not None and guard["first_established_collapse_minute"] <= horizon,
                "first_established_collapse_minute_of_the_overlay": guard["first_established_collapse_minute"],
                "bleed_rate_distinct_values_ml_min": sorted({round(row["bleed_ml_min"], 6) for row in rows[1:]}),
                "change_from_the_reviewed_trajectory_mmHg": [{"minute": point["minute"], "sbp": point["sbp"] - float(stored[point["minute"]][0])} for point in pressures]}
        spread = max(max(by_witness[label]["pressures"][index]["sbp"] for label in WITNESSES) - min(by_witness[label]["pressures"][index]["sbp"] for label in WITNESSES)
                     for index in range(len(committed)))
        out[scenario_id] = {"title": item["title"], "case_id": case, "series": item["series"], "script": [list(step) for step in item["script"]],
                            "largest_sbp_difference_between_witnesses_mmHg": spread,
                            "reviewed_item_digest": hashlib.sha256(json.dumps(item, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()[:12],
                            "reviewed_trajectory_current_configuration": [{"minute": minute, "sbp": float(values[0]), "dbp": float(values[1]), "map": float(values[2])} for minute, values in sorted(stored.items())],
                            "reproduction_at_the_current_configuration": reproduction, "candidates": by_witness}
    return out


def _point_of(witness: dict) -> Point:
    bound = witness["binding"]
    kernel = bound["crystalloid_kernel"]
    return Point(bound["c_rate_over_scale_per_min"], bound["preload_scale_ml_eq"], (kernel["e"], kernel["s"], kernel["tau_min"]), bound["arrival_position"])


# -- P3-346: the cross-scenario causal audit -------------------------------------------------------------------------------------------------------------------

def section_causal(ctx: dict, witnesses: dict, candidates: dict) -> dict:
    out = {}
    for label in WITNESSES:
        point = _point_of(witnesses[label])
        untreated = {case: gj.run(ctx["untreated"][case], 181, rate=point.rate, scale=point.scale, kernel=point.kernel)[0] for case in CASES}
        untreated_sbp = {case: {str(minute): untreated[case][minute]["sbp"] for minute in (0, 30, 60, 120, 150, 160, 180)} for case in CASES}
        blood, crystalloid = {}, {}
        for scenario_id in SCENARIOS:
            captured = ctx["reviewed"][scenario_id]
            case, horizon = captured["case"], candidates[scenario_id]["candidates"][label]["committed_minutes"][-1]
            full = simulate(captured["scenario"], horizon, point)["rows"]
            names = {type(item).__name__ for item in _contributors(captured["scenario"])}
            if "PackedRedCells" in names:
                without = simulate(captured["scenario"], horizon, point, drop=("red_cells",))["rows"]
                blood[scenario_id] = {"case_id": case, "minute": horizon, "sbp_with_red_cells": full[horizon]["sbp"], "sbp_without_red_cells": without[horizon]["sbp"],
                                      "sbp_caused_by_red_cells_mmHg": full[horizon]["sbp"] - without[horizon]["sbp"],
                                      "effective_volume_caused_by_red_cells_ml_eq": full[horizon]["V"] - without[horizon]["V"],
                                      "hb_with_and_without": [full[horizon]["hb"], without[horizon]["hb"]]}
            without_fluid = simulate(captured["scenario"], horizon, point, drop=("crystalloid",))["rows"]
            crystalloid[scenario_id] = {"case_id": case, "minute": horizon, "sbp_caused_by_crystalloid_mmHg": full[horizon]["sbp"] - without_fluid[horizon]["sbp"],
                                        "crystalloid_retained_ml": full[horizon]["net_retained_crystalloid_ml"]}
        long_case = ctx["reviewed"]["FR-G"]["case"]
        long_rows = simulate(ctx["reviewed"]["FR-G"]["scenario"], 70, point)["rows"]
        slow_effect_60 = long_rows[60]["sbp"] - untreated[long_case][60]["sbp"]
        one_unit = witnesses[label]["one_unit_sbp_rise_at_30_mmHg"]
        same_case_blood = next(item for item in blood.values() if item["case_id"] == long_case)
        early, delayed = candidates["FR-B"]["candidates"][label], candidates["FR-C"]["candidates"][label]
        early_end, delayed_end = early["pressures"][-1], delayed["pressures"][-1]
        early_case = candidates["FR-B"]["case_id"]
        every = [item for scenario in candidates.values() for item in [scenario["candidates"][label]]]
        out[label] = {
            "bleeding_remains_active": {"holds": all(item["bleed_rate_distinct_values_ml_min"] == [round(point.rate, 6)] for item in every),
                                        "distinct_rate_values_per_scenario": {scenario_id: candidates[scenario_id]["candidates"][label]["bleed_rate_distinct_values_ml_min"] for scenario_id in SCENARIOS},
                                        "note": "one value in every minute of every candidate: the bleed is never stopped or slowed (it is controlled only in the one-unit READING of FD-RATE-09)"},
            "blood_improves_volume_and_pressure_causally": {"holds": all(item["sbp_caused_by_red_cells_mmHg"] > 0 and item["effective_volume_caused_by_red_cells_ml_eq"] > 0 and item["hb_with_and_without"][0] > item["hb_with_and_without"][1] for item in blood.values()),
                                                            "by_scenario": blood, "how": "the same scenario run again WITHOUT the red cells: the difference is what they cause"},
            "slow_crystalloid_weaker_than_blood": {"holds": slow_effect_60 < same_case_blood["sbp_caused_by_red_cells_mmHg"] and slow_effect_60 < one_unit[long_case],
                                                   "slow_litre_at_60_mmHg": slow_effect_60, "one_complete_unit_bleeding_controlled_mmHg": one_unit[long_case],
                                                   "two_units_in_the_delayed_scenario_same_case_mmHg": same_case_blood["sbp_caused_by_red_cells_mmHg"],
                                                   "retained_ml": {"slow_litre_at_60": long_rows[60]["net_retained_crystalloid_ml"], "one_unit": 300.0}},
            "crystalloid_by_scenario": crystalloid,
            "untreated_deterioration_progressive": {"holds": all(untreated_sbp[case]["0"] > untreated_sbp[case]["30"] > untreated_sbp[case]["60"] > untreated_sbp[case]["120"] > untreated_sbp[case]["180"] for case in CASES),
                                                    "sbp": untreated_sbp},
            "treatment_ordering_preserved": {
                "holds": (early_end["sbp"] > round(untreated[early_case][early_end["minute"]]["sbp"]) and delayed_end["sbp"] > round(untreated[early_case][delayed_end["minute"]]["sbp"])
                          and early_end["sbp"] > delayed_end["sbp"] and long_rows[60]["sbp"] > untreated[long_case][60]["sbp"] and long_rows[70]["sbp"] > untreated[long_case][70]["sbp"]
                          and untreated[CASES[0]][60]["sbp"] < untreated[CASES[1]][60]["sbp"]),
                "early_treatment_end": early_end, "untreated_at_that_minute": untreated[early_case][early_end["minute"]]["sbp"],
                "delayed_treatment_end": delayed_end, "untreated_at_that_minute_delayed": untreated[early_case][delayed_end["minute"]]["sbp"],
                "slow_crystalloid_at_60_and_70": [long_rows[60]["sbp"], long_rows[70]["sbp"]], "untreated_at_60_and_70": [untreated[long_case][60]["sbp"], untreated[long_case][70]["sbp"]],
                "reading": "treated above untreated at the same minute; early treatment ends above delayed treatment; the 57-year-old stays below the 72-year-old untreated"},
            "no_case_specific_branch": {"holds": True, "basis": "a structural declaration, not a measurement: the tests hold it by scanning this module's source",
                                        "how": "one witness tuple is applied to both cases; the only per-case inputs are the authored arrival states the encounter captured"},
            "no_fitting_to_the_legacy_engine": {"holds": True, "basis": "a structural declaration, not a measurement: the tests hold it by scanning this module's source",
                                                "how": "the witnesses are functions of the faculty windows, the closed-region envelopes and the frozen untreated envelopes only; this module never reads a legacy pressure"},
            "no_candidate_reaches_a_boundary": {"holds": all(item["unresolved_boundary_minute"] is None and not item["experiment_would_stop"] and item["complete_to_the_last_committed_minute"] for item in every),
                                                "note": "no unresolved core boundary and no ESTABLISHED collapse of the overlay inside any script: no candidate would stop the development experiment"}}
        out[label]["all_hold"] = all(item["holds"] for key, item in out[label].items() if isinstance(item, dict) and "holds" in item)
    return out


def _contributors(scenario: dict) -> list:
    from clinical_core import integration
    return list(integration.scenario_from_dict(scenario)[1])


# -- P3-347: the blinded review package ------------------------------------------------------------------------------------------------------------------------

#: The five first-pass questions and the overall judgment of the faculty trajectory review, as the page asks them (the test holds them equal to the page's).
QUESTIONS = (
    {"id": "Q1", "topic": "DIRECTION", "text": "Does the physiologic evolution move in the expected direction?", "choices": ["Expected", "Partly", "Wrong"]},
    {"id": "Q2", "topic": "TIMING", "text": "Does the response occur:", "choices": ["Too early", "Plausible", "Too late"]},
    {"id": "Q3", "topic": "MAGNITUDE", "text": "Is the magnitude:", "choices": ["Too small", "Plausible", "Too large"]},
    {"id": "Q4", "topic": "MANAGEMENT RESPONSE", "text": "Is the response to intervention:", "choices": ["Coherent", "Uncertain", "Incoherent"]},
    {"id": "Q5", "topic": "EDUCATIONAL RISK", "text": "Could this trajectory mislead a resident?", "choices": ["No", "Maybe", "Yes"]},
)
OVERALL = ("ACCEPT", "ACCEPT_WITH_LIMITATION", "RECALIBRATE", "REJECT")
PRIMARY_SET = "CONJUNTO-1"


def blind_labels() -> dict:
    """CENTER_REFERENCE is the set reviewed first; the other two get their numbers from a digest, not from their names."""
    others = sorted((label for label in WITNESSES if label != "CENTER_REFERENCE"), key=lambda label: hashlib.sha256(f"{CANDIDATE_VERSION}:{label}".encode("utf-8")).hexdigest())
    return {"CENTER_REFERENCE": PRIMARY_SET, others[0]: "CONJUNTO-2", others[1]: "CONJUNTO-3"}


def _seal(body: dict) -> dict:
    body = fa._round(body, PLACES)
    body["record_digest"] = hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()
    return body


def build_review_set(ctx: dict, candidates: dict) -> dict:
    """What the reviewer is given: per set and scenario, the same view the earlier review showed, with the candidate pressures. No witness name, no parameter,
    no legacy number, no earlier trajectory."""
    labels = blind_labels()
    items = []
    for label in ("CENTER_REFERENCE",) + tuple(name for name in WITNESSES if name != "CENTER_REFERENCE"):
        for scenario_id in SCENARIOS:
            item = ctx["reviewed"][scenario_id]["item"]
            candidate = candidates[scenario_id]["candidates"][label]
            view = reviewer_view(item, pressures=candidate["pressures"])
            items.append({"set": labels[label], "item_id": f"{labels[label]}/{scenario_id}", "required": labels[label] == PRIMARY_SET, **view,
                          "stopped": candidate["experiment_would_stop"], "questions": [dict(question) for question in QUESTIONS], "overall_choices": list(OVERALL)})
    items.sort(key=lambda entry: (entry["set"], SCENARIOS.index(entry["scenario_id"])))
    return _seal({"record_type": "JOINT_REGION_V1_CANDIDATE_REVIEW_SET", "version": CANDIDATE_VERSION, "evidence_class": "MODEL_ANALYSIS",
                  "statement": "Synthetic development cases. Candidate trajectories for a blinded faculty re-review: not a clinical validation, not a calibrated configuration, not a resident pilot.",
                  "what_it_is": "Per set and scenario, the view the faculty trajectory review showed before its first pass was locked, with the pressure of one candidate configuration of the joint development region. It carries no parameter, no witness name, no legacy PRESSURE, no legacy comparator and no earlier trajectory. Heart rate and capillary refill ARE the legacy engine's own values, shown as context exactly as the earlier review showed them.",
                  "order": {"first": PRIMARY_SET, "then_if_wanted": ["CONJUNTO-2", "CONJUNTO-3"], "scenarios": list(SCENARIOS)},
                  "pressure_source": "the certified common core on a counterfactual copy of the captured scenario; whole mmHg as the page displays them",
                  "heart_rate_and_capillary_refill_source": "the legacy engine (the engine that runs today), as the encounter ran and exactly as the earlier review displayed them: context, not part of the pressure trajectory being judged; they do not depend on the candidate configuration and do not change between sets",
                  "items": items})


def build_blind_key(witnesses: dict, candidates: dict) -> dict:
    labels = blind_labels()
    return _seal({"record_type": "JOINT_REGION_V1_BLIND_KEY", "version": CANDIDATE_VERSION,
                  "open_only_after_the_first_pass_is_written_down": True,
                  "sets": {labels[label]: {"witness": label, "role": witnesses[label]["role"], "why": witnesses[label]["why"], "binding": witnesses[label]["binding"],
                                           "one_unit_sbp_rise_at_30_mmHg": witnesses[label]["one_unit_sbp_rise_at_30_mmHg"],
                                           "slow_crystalloid_share_at_60": witnesses[label]["slow_crystalloid_share_at_60"]} for label in WITNESSES},
                  "no_set_is_preferred": "the three are test witnesses of one development region; none is a calibration and none is expected to be 'best'",
                  "earlier_reviewed_trajectories_current_configuration": {scenario_id: candidates[scenario_id]["reviewed_trajectory_current_configuration"] for scenario_id in SCENARIOS},
                  "earlier_review": {"record": "docs/revision/PHASE3_FIRST_HUMAN_FACULTY_REVIEW.json", "preserved_unchanged": True,
                                     "its_judgments_are_not_transferred": "an ACCEPT of the earlier trajectory says nothing about a candidate (FD-RATE-20)"},
                  "legacy_comparator": {"copied_here": False, "where": "docs/revision/PHASE3_FACULTY_TRAJECTORY_REVIEW_SET.json (unchanged), bundle.comparator of each scenario",
                                        "note": "the legacy engine is context, not a reference standard, and no candidate was fitted to it"}})


def _number(value) -> str:
    if value is None:
        return "—"
    text = f"{float(value):.1f}".rstrip("0").rstrip(".")
    return text.replace(".", ",")


def _places(value, places: int) -> str:
    return f"{float(value):.{places}f}".replace(".", ",")


def _sheet(item: dict) -> str:
    arrival = item["arrival"]
    context = {row["minute"]: row for row in item["heart_rate_and_capillary_refill"]}
    lines = [f"## {item['scenario_id']} · {item['title']}", "", f"*{item['context']}*", "", f"**Qué se juzga:** {item['purpose']}", "",
             f"**Llegada:** PA {_number(arrival['sbp'])}/{_number(arrival['dbp'])} mmHg (PAM {_number(arrival['map'])}) · FC {_number(arrival['hr'])}/min · relleno capilar {_number(arrival['crt'])} s"
             f" · FR {_number(arrival['rr'])}/min · SpO₂ {_number(arrival['spo2'])} %", "",
             "| Minuto | Qué se hizo | Qué hizo el encuentro |", "|---|---|---|"]
    lines += [f"| {row['minute']} | {row['action']} | {row['result']} |" for row in item["timeline"]]
    lines += ["", "| Minuto | PAS | PAD | PAM | FC (contexto) | Relleno capilar, s (contexto) |", "|---|---|---|---|---|---|"]
    for point in item["common"]:
        beside = context.get(point["minute"], {})
        minute = "0 (llegada)" if point["minute"] == 0 else str(point["minute"])
        lines.append(f"| {minute} | **{_number(point['sbp'])}** | {_number(point['dbp'])} | {_number(point['map'])} | {_number(beside.get('hr'))} | {_number(beside.get('crt'))} |")
    lines += ["", "*PAS, PAD y PAM son la trayectoria que juzgas. La frecuencia cardíaca y el relleno capilar son contexto para tu interpretación: los calcula el motor vigente del simulador, no forman parte de la trayectoria de presión y no cambian entre conjuntos.*", ""]
    return "\n".join(lines)


def _form(review_set: dict) -> str:
    lines = ["# Formulario de respuestas · re-revisión ciega de la región conjunta (JOINT_REGION_V1_CANDIDATE)", "",
             "**Código de revisor:** \\_\\_\\_\\_\\_ · **Fecha:** \\_\\_\\_\\_\\_\\_\\_\\_ *(sin nombre; sin datos de pacientes reales)*", "",
             "Las preguntas y las opciones son las de la pantalla *Faculty Trajectory Review*, en su texto original. Marca una opción por pregunta.", "",
             "**Primera pasada (ciega):** contesta Q1–Q5 y el juicio global **antes** de abrir `ABRIR_DESPUES_DE_LA_PRIMERA_PASADA.md`.", "",
             "*Dos diferencias con la pantalla de la primera revisión: aquí el juicio global se da en la primera pasada (allí se pedía después de ver el comparador heredado), y no hay comparador que revelar.*", ""]
    for name in (review_set["order"]["first"],) + tuple(review_set["order"]["then_if_wanted"]):
        lines += [f"## {name}" + (" · es el que se revisa" if name == review_set["order"]["first"] else " · sensibilidad: no abrir salvo que se pida después"), ""]
        for item in (entry for entry in review_set["items"] if entry["set"] == name):
            lines += [f"### {item['item_id']} · {item['title']}", "", "| Pregunta | Opciones |", "|---|---|"]
            lines += [f"| {question['id']} {question['topic']} — {question['text']} | " + "  ".join(f"☐ {choice}" for choice in question["choices"]) + " |" for question in item["questions"]]
            lines += ["| **Overall** | " + "  ".join(f"☐ {choice}" for choice in item["overall_choices"]) + " |", "",
                      "Comentario (opcional):", "", "\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_", ""]
        lines += [f"☐ Confirmo que contesté {name} **sin** abrir la clave ni comparar con la revisión anterior.", ""]
    lines += ["## Después de abrir la clave (opcional)", "",
              "| Conjunto / escenario | ¿Cambia tu juicio global? | Si cambia, nuevo juicio | Comentario |", "|---|---|---|---|"]
    lines += [f"| {item['item_id']} | ☐ No  ☐ Sí | | |" for item in review_set["items"]]
    lines += ["", "*Tu primera pasada no se corrige: lo que cambie se anota aquí, aparte.*", ""]
    return "\n".join(lines)


def build_kit(review_set: dict, key: dict) -> dict:
    """The static review kit, as ``{file name: text}``. Reviewer-facing instructions in Spanish; scenario texts and questions verbatim from the review page."""
    files = {}
    first, others = review_set["order"]["first"], review_set["order"]["then_if_wanted"]
    files["README.md"] = "\n".join([
        "# Re-revisión ciega · región conjunta de GI (JOINT_REGION_V1_CANDIDATE)", "",
        "**Estado: preparado; la re-revisión NO ha empezado.** Nada aquí responde por la persona revisora, ni juzga, ni puntúa.", "",
        "## Qué es",
        "Tras la primera revisión docente se preparó, sólo para desarrollo, otra configuración conjunta del modelo de hemorragia digestiva. "
        "Esa configuración cambia **todas** las trayectorias tratadas, así que se vuelven a juzgar a ciegas **FR-B, FR-C, FR-E y FR-G**. Tus juicios anteriores se conservan aparte y **no** se transfieren.", "",
        "Casos sintéticos. **No** es validación clínica, ni una configuración calibrada, ni un piloto con residentes. Ninguna configuración es «la esperada».", "",
        "## Qué revisas y en qué orden",
        f"1. **Sólo `{first}`**: los cuatro escenarios de `conjunto_1.md`, en este orden: **FR-B, FR-C, FR-E, FR-G**.",
        f"2. **`{others[0]}`** y **`{others[1]}`** (`conjunto_2.md` y `conjunto_3.md`) son vistas de sensibilidad de la misma región. **No los abras** salvo que la docencia los pida después.", "",
        "Los conjuntos no dicen qué configuración llevan. No hay comparador heredado en esta primera pasada.", "",
        "## Qué ves en cada escenario",
        "Lo mismo que en la pantalla *Faculty Trajectory Review*: el contexto, qué se hizo y cuándo, la trayectoria de presión (PAS/PAD/PAM) y, como contexto, la frecuencia cardíaca y el relleno capilar. "
        "No hay parámetros técnicos.", "",
        "## Qué contestas",
        "En `formulario_respuestas.md`, por escenario: **Q1 Direction · Q2 Timing · Q3 Magnitude · Q4 Management response · Q5 Educational risk** y el juicio global "
        "(**ACCEPT / ACCEPT_WITH_LIMITATION / RECALIBRATE / REJECT**), con las mismas opciones de la pantalla.", "",
        "## Ciego",
        "- Contesta la primera pasada **antes** de abrir `ABRIR_DESPUES_DE_LA_PRIMERA_PASADA.md` y sin tener delante la revisión anterior.",
        "- El ciego es **de procedimiento**: la pantalla de revisión actual sólo admite el conjunto certificado y fijado por digesto, así que estos candidatos no pasan por ella y nada bloquea el archivo de la clave.", "",
        "## Límites que conviene saber antes de empezar",
        "- Sólo la presión viene de la configuración candidata. La frecuencia cardíaca y el relleno capilar los calcula el motor vigente del simulador, no la configuración candidata: no cambian con ella y **son iguales en los tres conjuntos**.",
        "- El sangrado sigue activo en todos los minutos de todos los escenarios; no hay control de fuente ni vasopresor.",
        "- La duración de la revisión no se ha medido con una persona.", "",
        "## Qué no hace este paquete",
        "No elige una configuración, no aprueba ningún parámetro, no cambia lo que ve el residente y no sustituye tu juicio. El registro de tus respuestas es evidencia humana y se guarda aparte del análisis del modelo.", ""])
    names = {first: "conjunto_1.md", others[0]: "conjunto_2.md", others[1]: "conjunto_3.md"}
    for name, file_name in names.items():
        sheets = [_sheet(item) for item in review_set["items"] if item["set"] == name]
        head = [f"# {name} · re-revisión ciega de la región conjunta", "",
                "> Lee cada escenario y contesta en `formulario_respuestas.md`. No abras la clave antes de terminar la primera pasada.", ""]
        files[file_name] = "\n".join(head + sheets)
    files["formulario_respuestas.md"] = _form(review_set)
    reveal = ["# ABRIR SÓLO DESPUÉS DE LA PRIMERA PASADA · clave de los conjuntos", "",
              "> Si todavía no escribiste tus respuestas de la primera pasada, **cierra este archivo**.", "",
              "Los tres conjuntos son **testigos de prueba** de una misma región de desarrollo. Ninguno es una calibración y ninguno es «el esperado».", "",
              "| Conjunto | Testigo | Tasa (mL-eq/min) | Escala (mL-eq) | Una unidad completa, ΔPAS a 30 min (57m / 72f) | Cristaloide lento, % evitado a 60 min |", "|---|---|---|---|---|---|"]
    for name in sorted(key["sets"]):
        entry = key["sets"][name]
        rises = entry["one_unit_sbp_rise_at_30_mmHg"]
        reveal.append(f"| {name} | {entry['witness']} | {_places(entry['binding']['bleed_rate_ml_eq_per_min'], 2)} | {_places(entry['binding']['preload_scale_ml_eq'], 0)}"
                      f" | +{_places(rises['gi_bleed_57m'], 1)} / +{_places(rises['gi_bleed_72f'], 1)} | {_places(entry['slow_crystalloid_share_at_60'] * 100, 0)} |")
    reveal += ["", "*Tasa y escala van siempre juntas: son lecturas del modelo en mL-equivalentes, no una pérdida de sangre medida clínicamente.*", "",
               "## Trayectoria que juzgaste en la primera revisión (configuración actual)", "",
               "| Escenario | Minuto: PAS/PAD (PAM) |", "|---|---|"]
    for scenario_id in SCENARIOS:
        points = key["earlier_reviewed_trajectories_current_configuration"][scenario_id]
        reveal.append(f"| {scenario_id} | " + " · ".join(f"{point['minute']}: {_number(point['sbp'])}/{_number(point['dbp'])} ({_number(point['map'])})" for point in points) + " |")
    reveal += ["", "Tus juicios de entonces siguen en `docs/revision/PHASE3_FIRST_HUMAN_FACULTY_REVIEW.json`, sin cambios, y **no** se transfieren a estos candidatos.", "",
               "El comparador heredado no se copia aquí: sigue, sin cambios, en el conjunto de la primera revisión. No es un estándar de referencia y ningún candidato se ajustó a él.", ""]
    files["ABRIR_DESPUES_DE_LA_PRIMERA_PASADA.md"] = "\n".join(reveal)
    return files


# -- the record --------------------------------------------------------------------------------------------------------------------------------------------------

def build_context() -> dict:
    ctx = gj.build_context()
    ctx["reviewed"] = {scenario_id: capture_reviewed(scenario_id) for scenario_id in SCENARIOS}
    ctx["overlay"] = overlay_amendment()
    return ctx


def decide(band: dict, region: JointRegion, witnesses: dict, candidates: dict, causal: dict) -> dict:
    published = gj.load_record()["feasibility"]
    reproducible = (published["status"] == "NONEMPTY"
                    and all(abs(a - b) < 1e-6 for a, b in zip((region.c_low, region.c_high), published["by_shared_arrival_position"][f"{FRACTION}"]["A_untreated"]["common_c"]))
                    and all(abs(a - b) < 1e-3 for a, b in zip((region.scale_low, region.scale_high), published["by_shared_arrival_position"][f"{FRACTION}"]["B_one_unit"]["common_scale_ml_eq"])))
    robust = all(item["satisfies_all_three_faculty_constraints"] and item["inside_the_closed_crystalloid_region"] and not item["on_a_boundary"]
                 and item["every_existing_constraint_readable_and_met"] for item in witnesses.values())
    ready = {scenario_id: all(item["complete_to_the_last_committed_minute"] and item["unresolved_boundary_minute"] is None for item in candidates[scenario_id]["candidates"].values())
             and all(candidates[scenario_id]["reproduction_at_the_current_configuration"][name] for name in ("pressures_equal_the_reviewed_trajectory", "heart_rate_and_capillary_refill_equal_the_reviewed_context"))
             for scenario_id in SCENARIOS}
    causal_ok = all(item["all_hold"] for item in causal.values())
    if band["verdict"] != "A":
        verdict = "C"
    elif not reproducible:
        verdict = "D"
    elif not (robust and all(ready.values()) and causal_ok):
        verdict = "B"
    else:
        verdict = "A"
    names = {"A": "JOINT_REGION_READY_FOR_BLINDED_HUMAN_REREVIEW", "B": "JOINT_REGION_EXISTS_BUT_WITNESSES_NOT_ROBUST",
             "C": "OLD_CONSTRAINT_CONFLICT_REQUIRES_FACULTY_DECISION", "D": "JOINT_FEASIBILITY_NOT_REPRODUCIBLE"}
    return {"verdict": verdict, "name": names[verdict], "old_band_verdict": band["verdict"], "joint_feasibility_reproducible": reproducible,
            "witnesses_off_every_boundary": robust, "scenarios_ready": ready, "causal_audit_holds_for_every_witness": causal_ok,
            "smallest_margin_of_each_witness": {label: item["margins"]["smallest"] for label, item in witnesses.items()},
            "amendment_3": "CLOSED (FD-RATE-19): not designed, not implemented", "a_point_was_chosen_as_a_calibration": False}


def build() -> dict:
    ctx = build_context()
    band = section_old_band()
    region = JointRegion(ctx)
    solved = solve_witnesses(region)
    witnesses = section_witnesses(region, solved)
    candidates = section_candidates(ctx, witnesses)
    causal = section_causal(ctx, witnesses, candidates)
    record = {"record_type": "GI_JOINT_REGION_V1", "version": VERSION, "evidence_class": EVIDENCE_CLASS, "executable_change": False,
              "what_it_is": "The joint GI rate / pressure development region as an explicit object, its margins, three development test witnesses and their candidate trajectories for a blinded human re-review. MODEL_ANALYSIS: nothing is approved, no point is a calibration, and nothing here is clinical validation.",
              "depends_on": {**ctx["depends_on"], "joint_feasibility_record_digest": gj.load_record()["record_digest"]},
              "faculty_decisions_applied": {"FD-RATE-14": "the one-unit window is read on the complete unit at minute 30; a monotonic partial response at minute 15, with no floor there",
                                            "FD-RATE-15": "the windows are regions; their centres are not targets",
                                            "FD-RATE-16": "the feasible joint region is accepted as a structural result, not as a calibration",
                                            "FD-RATE-17": "the rate interval is part of a joint development region only with its compatible scale; never a clinically measured rate, never selected alone",
                                            "FD-RATE-18": "the old CANDIDATE scale band may be marked superseded if it is only a candidate analysis band",
                                            "FD-RATE-19": "Amendment 3 stays closed", "FD-RATE-20": "a new blinded human review of FR-B, FR-C, FR-E and FR-G before any adoption"},
              "old_scale_band": band,
              "region": formal_description(region),
              "geometry": section_geometry(region, solved),
              "witnesses": witnesses,
              "candidate_trajectories": candidates,
              "causal_audit": causal,
              "decision": decide(band, region, witnesses, candidates, causal)}
    record = fa._round(record, PLACES)
    record["record_digest"] = digest(record)
    review_set = build_review_set(ctx, record["candidate_trajectories"])
    key = build_blind_key(record["witnesses"], record["candidate_trajectories"])
    return {"record": record, "review_set": review_set, "blind_key": key, "kit": build_kit(review_set, key),
            "objects": {"ctx": ctx, "region": region, "solved": solved}}          # live objects for the tests; never written


def digest(record: dict) -> str:
    body = {key: value for key, value in record.items() if key != "record_digest"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()


def load_record() -> dict:
    return json.loads(RECORD_PATH.read_text(encoding="utf-8"))


def write_all(built: dict) -> None:
    for path, body in ((RECORD_PATH, built["record"]), (REVIEW_SET_PATH, built["review_set"]), (BLIND_KEY_PATH, built["blind_key"])):
        path.write_text(json.dumps(body, sort_keys=True, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    KIT_DIR.mkdir(parents=True, exist_ok=True)
    for name, text in built["kit"].items():
        (KIT_DIR / name).write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")


if __name__ == "__main__":
    result = build()
    if os.environ.get(WRITE_FLAG) == "1":
        write_all(result)
        print("written", RECORD_PATH.name, result["record"]["record_digest"], result["review_set"]["record_digest"], result["blind_key"]["record_digest"])
    else:
        print(result["record"]["record_digest"], result["record"]["decision"]["verdict"])
