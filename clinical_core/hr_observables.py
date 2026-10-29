"""Phase 2 shadow core, P2I-2AJ: case-truth pruning of the arrival severity and the HR observable decision pack.

    python -m clinical_core.hr_observables --digest
    python -m clinical_core.hr_observables --design
    python -m clinical_core.hr_observables --run --out <directory outside the repository>

Shadow only and offline. Faculty decisions (2026-10-29), recorded in FACULTY:

1. 72f's arrival state with normalized current delivery 1.0 is REJECTED_BY_CASE_TRUTH_COMPATIBILITY: 72f's authored
   arrival is an ongoing underfilled, impaired-perfusion phenotype, and accrued debt does not rescue a normalized
   current delivery. The rule (CASE_TRUTH_RULE) reads 72f's arrival delivery level only: never HR, a survivor count, a
   tolerance or a gain. It removes candidates and adds none.
2. Retained, for these two authored cases only: 57m severe (D0 60, delivery 0.6) with 72f (D0 20, delivery 0.85),
   FACULTY-CONSTRAINED CASE-COMPATIBLE ARRIVAL-SEVERITY SUPPORT. It is not a GI default, an approved D scale or a
   migration parameter. Its D / lactate rows are P2I-2AI's, reused only when reproduced exactly (REUSE_RULE).
3. Demand 0.9 / 1.0 / 1.1 is explicit physiological uncertainty, not three states one patient must satisfy:
   ROBUST_ACROSS_DEMAND is diagnostic, never a filter. Each value is CURRENTLY_COMPATIBLE or CURRENTLY_INCOMPATIBLE
   with the authored cases and the current lactate constraints, never approved. Demand reaches the arrival HR (the acute
   signal is the effective deficit over demand), so 1.0 is not privileged: the HR surface and the trajectories are read
   at every currently compatible demand, each its own condition.
4. HR: intrinsic 60 / 80 / 100 per case (patient-specific latent physiology, never identified or approved, no value
   added or removed); acute and debt gains (P2I-2AF's five points each) and the total sinus ceilings 150 / 175 / 200
   common; pressure DEFERRED (P2I-2AG's primary mode); arrival tolerance +-5 bpm. Trajectories are reported as
   distributions over every surviving candidate; envelope proposals are prepared, never applied.

Nothing is fitted, selected or approved; the legacy HR and lactate are never read.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import inspect
import json
from dataclasses import replace
from pathlib import Path

from . import arrival_severity as asv
from . import blood_anchors, calibration, derived, gi_reference, lactate_slice
from . import blood_constraints as bc
from . import blood_fluid_calibration as bf
from . import hr_primary as hp
from . import hr_shock as hk
from . import hr_structure as hs
from . import lactate_adequacy as la
from . import lactate_closure as lc
from . import lactate_rebuild as lr
from .derived import derive, effective_delivery, effective_oxygen_deficit

DECIDED = "2026-10-29"
REVISION = "P2I-2AJ"
ROOT = lc.ROOT
CASES = lc.CASES
C57, C72 = CASES
L1, L2, L3 = lc.L1, lc.L2, lc.L3
RESERVE = lc.RESERVE
MINUTES = lr.MINUTES
LAMBDAS, INDEX, BASES = asv.LAMBDAS, asv.INDEX, asv.BASES
DEMANDS = tuple(sorted(lc.DEMAND_FACTORS))
P2I2AI_RECORD = ROOT / "docs" / "revision" / "P2I2AI_arrival_severity.json"
P2I2AI_DIGEST = "805eff4efb562b19f1d280bdd48bbc1d458d0055f104b66f7bc7dca7ea61a861"
#: P2I-2AI's units digest of the retained case pair at demand 1.0 (its record, recertification entry).
P2I2AI_RETAINED_UNITS = "06f6d5c82fa3047643c4073bf77614e88499575de51ef9b22aa5514bca18488b"
#: Every clinical_core source at P2I-2AI's certified HEAD (12346cb) but the two files whose only change here is an
#: exclusion tuple naming this package's modules; the executable surface the reused rows were certified on.
DEPENDENCIES_AT_P2I2AI = "a27eddf04f9b075a2093446ea7288dea423874d96823977d1e4b68005ce21e1c"
TUPLE_ONLY = ("clinical_core/decision_pack.py", "clinical_core/lactate_slice.py")
OWN = ("clinical_core/hr_observables.py",)

FACULTY = {
    "decided": DECIDED,
    "case_truth": "72f's arrival state with D0 60 and normalized current delivery 1.0 is REJECTED_BY_CASE_TRUTH_"
                  "COMPATIBILITY: 72f arrives with BP 98/62 (MAP about 74), CRT 4 s, a hyperdynamic LV, IVC 1.1 cm with "
                  "> 50 % inspiratory collapse, active GI bleeding, lactate 3.4 and no known prehospital resuscitation "
                  "restoring delivery; normalized current delivery is not compatible with that ongoing underfilled / "
                  "impaired-perfusion phenotype, and accrued D0 60 does not rescue the contradiction; not rejected "
                  "because of HR or of its survivor count",
    "retained": "57m existing SEVERE pair with 72f D0 20 / delivery 0.85: FACULTY-CONSTRAINED CASE-COMPATIBLE "
                "ARRIVAL-SEVERITY SUPPORT for these authored cases and the current calibration; not a universal GI "
                "default, not a faculty-approved D scale, not a production migration parameter",
    "demand": "simultaneous survival at demand 0.9, 1.0 and 1.1 is not required: the three values are explicit "
              "physiological uncertainty, not three states the same patient must satisfy; ROBUST_ACROSS_DEMAND stays "
              "diagnostic; demand 1.0 is not approved for being the central reference; demand values unchanged",
    "intrinsic": "intrinsic HR is patient-specific latent physiology: 60 / 80 / 100 per patient, explored "
                 "independently, none approved, no value added; no survivor at 80 in P2I-2AI is not evidence that a "
                 "resting HR of 80 is invalid, and 80 stays in the support",
    "hr": "common acute gain (five frozen points), common debt gain (five frozen points), common total sinus ceilings "
          "150 / 175 / 200, pressure DEFERRED (zero in the primary calibration), arrival tolerance 57m 124 +- 5 and "
          "72f 112 +- 5; no dimension changed",
    "scope": "shadow only; no final latent HR selection, no HR-envelope filtering, no pressure / vascular-tone or RR "
             "calibration, no collapse, no GI or second-family migration, no runtime integration",
}

# 1. Exact pair semantics and the case-truth pruning (P2I-2AJ-1, -2) -------------------------------------------------

RETAINED = (("upper", "lower"), ("midpoint", "midpoint"))
RETAINED_KEY = asv._key(*RETAINED)
RETAINED_STATUS = "FACULTY_CONSTRAINED_CASE_COMPATIBLE_ARRIVAL_SEVERITY_SUPPORT"
CASE_TRUTH_REJECTION = "REJECTED_BY_CASE_TRUTH_COMPATIBILITY"
CASE_TRUTH_RULE = (
    "Among P2I-2AI's LACTATE_COMPATIBLE case pairs, a pair is REJECTED_BY_CASE_TRUTH_COMPATIBILITY when 72f's arrival "
    "delivery is the top of its delivery band (1.0, normalized current delivery), whatever its arrival debt; otherwise "
    "RETAINED. The rule reads gi_reference's delivery band for 72f and the pair's level only: no HR, survivor count, "
    "tolerance, gain, ceiling, pressure or legacy value. The retained set must be exactly the faculty's pair (57m "
    "severe, 72f D0 20 / delivery 0.85), else the run stops.")
HR_ITEMS = ("hr",)


def _band(band) -> dict:
    return {"name": band.name, "lower": band.lower, "midpoint": band.midpoint, "upper": band.upper, "units": band.units,
            "rationale": band.rationale}


def band_reads(function) -> dict:
    """What a gi_reference band function reads: the case items it cites (_source) and whether its values are literals
    or read an authored case value. Citations are source lines, which hold several items (the vitals line holds CRT and
    HR), so the cited item names are read from the code, not from the lines."""
    calls = [node for node in ast.walk(ast.parse(inspect.getsource(function))) if isinstance(node, ast.Call)]
    names = [getattr(node.func, "id", getattr(node.func, "attr", None)) for node in calls]
    cited = sorted({node.args[1].value for node, name in zip(calls, names) if name == "_source"
                    and len(node.args) > 1 and isinstance(node.args[1], ast.Constant)})
    band = next(node for node, name in zip(calls, names) if name == "Band")
    return {"cited_items": cited, "reads_authored_value": any(name in ("authored", "INVENTORY") for name in names),
            "literal_values": all(isinstance(arg, ast.Constant) for arg in band.args[1:4])}


def pair_semantics(record: dict) -> dict:
    """P2I-2AJ-1: the retained pairs' exact values and provenance, and the four statements the faculty asked for."""
    inventory = {tuple(item["pair"]) for item in record["inventory"]}
    admissible = {(tuple(a), tuple(b)) for a, b in record["admissible"]}
    compatible = {(tuple(a), tuple(b)) for a, b in record["lactate_compatible"]}
    reads = {"arrival_oxygen_debt": band_reads(gi_reference.arrival_debt_band),
             "arrival_delivery_ratio": band_reads(gi_reference.delivery_ratio_band)}
    out = {"band_reads": reads}
    for case, pair in zip(CASES, RETAINED):
        bands = gi_reference.case_bands(case)
        out[case] = {"pair": list(pair), "label": asv.PAIR_LABELS[pair], **asv.pair_values(case, pair),
                     "debt_band": _band(bands["arrival_oxygen_debt"]),
                     "delivery_band": _band(bands["arrival_delivery_ratio"]),
                     "values_from": "gi_reference.case_bands: arrival_oxygen_debt and arrival_delivery_ratio only "
                                    "(asv.pair_values); delivery re-anchored by the extraction reserve 2.5",
                     "in_p2i2ai_inventory": pair in inventory}
    out["checks"] = {
        "no_hr": all(not set(HR_ITEMS) & set(r["cited_items"]) and not r["reads_authored_value"]
                     and r["literal_values"] for r in reads.values()),
        "no_legacy": all("legacy" not in json.dumps(out[case]).lower() for case in CASES),
        "no_pressure_hr_term": not any(word in name.lower() for name in asv.severity_reads()
                                       for word in ("pressure", "sympathetic")),
        "in_p2i2ai_inventory": all(out[case]["in_p2i2ai_inventory"] for case in CASES),
        "p2i2ai_admissible": RETAINED in admissible,
        "p2i2ai_lactate_compatible": RETAINED in compatible,
    }
    return out


def case_truth(compatible: list) -> list[dict]:
    """P2I-2AJ-2: the faculty's case-truth rule on P2I-2AI's LACTATE_COMPATIBLE case pairs."""
    top = gi_reference.delivery_ratio_band(C72).upper
    out = []
    for pair_57, pair_72 in compatible:
        values = asv.pair_values(C72, pair_72)
        rejected = values["delivery"] == top
        out.append({"pair_57m": list(pair_57), "pair_72f": list(pair_72), "72f_D0": values["D0"],
                    "72f_delivery": values["delivery"],
                    "status": CASE_TRUTH_REJECTION if rejected else "RETAINED",
                    "reason": ("72f normalized current delivery 1.0 at arrival contradicts its underfilled / "
                               "impaired-perfusion phenotype" if rejected else None)})
    return out


# 2. The retained pair's D / lactate rows, per demand, with P2I-2AD's own checks (P2I-2AJ-2, -3) -------------------------

REUSE_RULE = (
    "P2I-2AI's record keeps the retained pair's units digest, survivors by demand and statistics, not the rows. The "
    "rows are rebuilt for the retained pair only (its 405 lactate-side bases per case, not P2I-2AI's 25 combinations) "
    "with P2I-2AD's own unit checks (lactate_closure._l1_unit, _l3_unit, _l2_unit and its Stage accounting, each case "
    "read at its own pair) and reused only when: the pair is the record's; the record is the committed one (its freeze "
    "digest); every clinical_core source the rows depend on equals P2I-2AI's certified HEAD (DEPENDENCIES_AT_P2I2AI); "
    "the units digest at demand 1.0 equals the record's and the survivors at 0.9 / 1.0 / 1.1 equal the record's. "
    "Otherwise the run stops.")
DEMAND_COMPATIBLE, DEMAND_INCOMPATIBLE = "CURRENTLY_COMPATIBLE", "CURRENTLY_INCOMPATIBLE"
DEMAND_RULE = (
    "Each demand factor is its own uncertainty condition. A value is CURRENTLY_COMPATIBLE when the retained pair has at "
    "least one lactate survivor there (P2I-2AD's constraints, both cases at their own pair), else "
    "CURRENTLY_INCOMPATIBLE; neither is approval. The dominant failure is the (stage, constraint, case) first failure "
    "with the largest candidate weight, read in P2I-2AD's order. ROBUST_ACROSS_DEMAND (survival at all three) is "
    "reported, never a filter. The HR surface and the trajectories are read at every CURRENTLY_COMPATIBLE value.")


def dependency_digest() -> str:
    sources = {k: v for k, v in bf.freeze_sources().items() if k not in TUPLE_ONLY + OWN}
    return hashlib.sha256(json.dumps(sources, sort_keys=True).encode("utf-8")).hexdigest()


def _case_bits(scenario: str, case: str) -> int:
    return sum(1 << n for n, (_, owner) in enumerate(lc.BITS[scenario]) if owner in (case, None))


def _pair_mask(scenario: str, masks: dict, a: int, b: int) -> int:
    return (masks[a] & _case_bits(scenario, C57)) | (masks[b] & _case_bits(scenario, C72))


def units_digest(units: list) -> str:
    """P2I-2AI's units digest (its run(), recertification entry)."""
    rows = [[i, a, b, list(r), list(d)] for i, a, b, r, d in units]
    return hashlib.sha256(json.dumps(rows, separators=(",", ":")).encode()).hexdigest()


def retained_region(source: dict, support: list, arrivals: dict, tasks: dict, store: dict, factor: float,
                    map_=map) -> dict:
    """L1, then L3, then L2 for the retained pair at one demand; a candidate is (P3 set, crystalloid point, base)."""
    p1, p3, children = source["p1"], source["p3"], source["children"]
    n_support = len(support)
    pairs = [(INDEX[(*base, *RETAINED[0])], INDEX[(*base, *RETAINED[1])]) for base in BASES]
    stages = {s: lc.Stage(s) for s in lr.SCENARIOS}

    def trajectories(scenario, unit):
        return {case: store[tasks[(scenario, unit, case)]] for case in CASES}

    def indices(chosen):
        return sorted({index for pair in chosen for index in pair})

    passing = {}
    for i, masks in map_(lc._l1_unit, [(i, trajectories(L1, i), arrivals, indices(pairs), factor)
                                       for i in range(len(p1))]):
        passing[i] = []
        for a, b in pairs:
            mask = _pair_mask(L1, masks, a, b)
            stages[L1].add(mask, len(children[i]) * n_support)
            if not mask:
                passing[i].append((a, b))
    r_ok = {}
    work = [(q, trajectories(L3, q), arrivals, indices(passing[i]), factor) for i in range(len(p1)) if passing[i]
            for q in children[i]]
    for q, masks in map_(lc._l3_unit, work):
        i = p3[q]["p1"]
        for a, b in passing[i]:
            mask = _pair_mask(L3, masks, a, b)
            stages[L3].add(mask, n_support)
            if not mask:
                r_ok.setdefault((i, a, b), []).append(q)
    wanted = {i: [(a, b) for a, b in passing[i] if (i, a, b) in r_ok] for i in passing}
    d_ok = {}
    work = [((i, d), trajectories(L2, (i, d)), arrivals, indices(wanted[i]), factor) for i in sorted(wanted)
            if wanted[i] for d in range(n_support)]
    for (i, d), masks in map_(lc._l2_unit, work):
        for a, b in wanted[i]:
            mask = _pair_mask(L2, masks, a, b)
            stages[L2].add(mask, len(r_ok[(i, a, b)]))
            if not mask:
                d_ok.setdefault((i, a, b), []).append(d)
    units = sorted((i, a, b, tuple(r_ok[(i, a, b)]), tuple(d_ok[(i, a, b)])) for i, a, b in d_ok)
    reports = [stages[scenario].report() for scenario, _ in lc.FILTER_ORDER]
    first = {f"{report['scenario']}: {name}": weight for report in reports
             for name, weight in report["first_failure"].items()}
    return {"factor": factor, "candidates": sum(len(c) for c in children) * n_support * len(BASES),
            "survivors": asv._survivors(units), "units": units, "digest": units_digest(units), "stages": reports,
            "dominant_failure": max(first, key=first.get) if first else None, "first_failures": first}


def demand_support(regions: dict) -> dict:
    ids = {f: asv._ids(regions[f]["units"]) for f in DEMANDS}
    out = {}
    for f in DEMANDS:
        region = regions[f]
        out[f"{f:g}"] = {"survivors": region["survivors"], "candidates": region["candidates"],
                         "status": DEMAND_COMPATIBLE if region["survivors"] else DEMAND_INCOMPATIBLE,
                         "dominant_failure": region["dominant_failure"],
                         "dominant_failure_weight": region["first_failures"].get(region["dominant_failure"], 0),
                         "stages": region["stages"], "approved": False}
    out["robust_across_demand"] = len(set.intersection(*ids.values()))
    out["robust_is_filter"] = False
    out["rule"] = DEMAND_RULE
    return out


# 3. The arrival HR surface per currently compatible demand (P2I-2AJ-4, -5, -6) ------------------------------------------

HR_RULE = (
    "The retained pair only, at each CURRENTLY_COMPATIBLE demand: arrival HR analytic (derived.heart_rate_decomposition, "
    "P2I-2AG's primary profile, pressure 0), 57m intrinsic 60 / 80 / 100 x 72f intrinsic 60 / 80 / 100 x the five "
    "common acute gains x the five common debt gains x the common ceilings 150 / 175 / 200. JOINT when |HR57 - 124| <= "
    "5 and |HR72 - 112| <= 5. At demand 1.0 the joint set must equal P2I-2AI's retained-pair survivors (else stop). "
    "No dimension changed, no best candidate.")
LATENTS = ("intrinsic_57m", "intrinsic_72f", "acute", "debt", "ceiling")
WELL, PARTIAL, POOR, NON = "WELL_CONSTRAINED", "PARTIALLY_CONSTRAINED", "POORLY_IDENTIFIED", "NON_IDENTIFIABLE"
NOT_EVALUABLE = "NOT_EVALUABLE"
STRUCTURAL = {"debt": "only debt_to_sympathetic_gain x D reaches HR and the D scale is not approved (P2I-2AG: the D "
                      "scale and the debt gain are one observable)"}
OBSERVATIONS = ("57m authored arrival HR", "72f authored arrival HR")
IDENTIFIABILITY_RULE = (
    "Per latent, over the joint survivors: NON_IDENTIFIABLE when the observable reaches it only through a product with "
    "an unapproved latent (STRUCTURAL); POORLY_IDENTIFIED when two or more grid values survive or the one surviving "
    "value is an edge of the explored support (unbounded on that side); PARTIALLY_CONSTRAINED when one interior value "
    "survives, bracketed by rejected neighbours, but the observations (two arrival HRs) are fewer than the latents "
    "(five), so the bracket is a grid artefact on a continuum of solutions; WELL_CONSTRAINED only when one interior "
    "value survives and the observations are at least as many as the latents. NOT_EVALUABLE without survivors. A "
    "narrow grid survivor set is never called identification; the arrival observables (acute, debt and total "
    "sympathetic increments, reserve utilization, predicted HR) are reported apart.")


def anchors_at(case: str, intrinsic: str, pair: tuple, factor: float):
    """hr_shock.analysis_anchors at a demand factor (applied as lactate_closure.full_run applies it)."""
    debt, delivery = pair
    values = calibration.case_values(case, calibration.GICandidate({}, intrinsic=intrinsic, debt=debt,
                                                                   delivery=delivery))
    values["arrival_delivery_ratio"] /= RESERVE
    values["metabolic_demand_baseline"] *= factor
    return gi_reference.candidate_anchors(case, values)


def arrival_table(factor: float) -> dict:
    table = {}
    for case, pair in zip(CASES, RETAINED):
        for level in hp.INTRINSIC:
            anchors = anchors_at(case, level, pair, factor)
            hp.require_explicit_intrinsic(anchors)
            for acute in hp.ACUTE:
                for gain in hp.DEBT:
                    for ceiling in hp.CEILINGS:
                        split = derived.heart_rate_decomposition(anchors, hp.primary_profile(acute, gain, ceiling))
                        rate = split["intrinsic_sinus_rate"]
                        table[(case, level, acute, gain, ceiling)] = {
                            "predicted": split["predicted_arrival_hr"], "intrinsic": rate,
                            "x0": split["acute_deficit_signal"], "D0": anchors.arrival_oxygen_debt,
                            "acute_bpm": split["acute_bpm"], "debt_bpm": split["debt_bpm"],
                            "sympathetic_bpm": split["saturated_bpm"],
                            "reserve_utilization": split["saturated_bpm"] / (ceiling - rate)}
    return table


def _support(joint: list) -> dict:
    return {"intrinsic_pairs": {f"{a}|{b}": sum(1 for s in joint if s["intrinsic"] == [a, b])
                                for a in hp.INTRINSIC for b in hp.INTRINSIC},
            "acute": {f"{v!r}": sum(1 for s in joint if s["acute"] == v) for v in hp.ACUTE},
            "debt": {f"{v!r}": sum(1 for s in joint if s["debt"] == v) for v in hp.DEBT},
            "ceiling": {f"{v:g}": sum(1 for s in joint if s["ceiling"] == v) for v in hp.CEILINGS}}


def surface(table: dict) -> dict:
    joint, candidates = [], 0
    for a in hp.INTRINSIC:
        for b in hp.INTRINSIC:
            for acute in hp.ACUTE:
                for gain in hp.DEBT:
                    for ceiling in hp.CEILINGS:
                        candidates += 1
                        first = table[(C57, a, acute, gain, ceiling)]
                        second = table[(C72, b, acute, gain, ceiling)]
                        if hp.compatible(C57, first["predicted"]) and hp.compatible(C72, second["predicted"]):
                            joint.append({"intrinsic": [a, b], "acute": acute, "debt": gain, "ceiling": ceiling,
                                          "predicted": [first["predicted"], second["predicted"]],
                                          "mismatch": [first["predicted"] - hp.AUTHORED[C57],
                                                       second["predicted"] - hp.AUTHORED[C72]],
                                          "observables": {C57: {k: first[k] for k in OBSERVABLES},
                                                          C72: {k: second[k] for k in OBSERVABLES}}})
    rows = {case: [key for key in table if key[0] == case] for case in CASES}
    return {"rule": HR_RULE, "decompositions": len(table), "joint_candidates": candidates,
            "compatible_decompositions": {case: sum(1 for key in rows[case] if hp.compatible(case,
                                                                                            table[key]["predicted"]))
                                          for case in CASES},
            "compatible_57m": sum(1 for a in hp.INTRINSIC for b in hp.INTRINSIC for key in rows[C57]
                                  if key[1] == a and hp.compatible(C57, table[key]["predicted"])),
            "compatible_72f": sum(1 for a in hp.INTRINSIC for b in hp.INTRINSIC for key in rows[C72]
                                  if key[1] == b and hp.compatible(C72, table[key]["predicted"])),
            "joint": len(joint), "distinct_predictions": len({(round(s["predicted"][0], 9),
                                                               round(s["predicted"][1], 9)) for s in joint}),
            "support": _support(joint), "survivors": joint}


OBSERVABLES = ("intrinsic", "x0", "D0", "acute_bpm", "debt_bpm", "sympathetic_bpm", "reserve_utilization", "predicted")


def _latent(s: dict, name: str):
    return {"intrinsic_57m": s["intrinsic"][0], "intrinsic_72f": s["intrinsic"][1], "acute": s["acute"],
            "debt": s["debt"], "ceiling": s["ceiling"]}[name]


def identifiability(joint: list) -> dict:
    grids = {"intrinsic_57m": list(hp.INTRINSIC), "intrinsic_72f": list(hp.INTRINSIC), "acute": list(hp.ACUTE),
             "debt": list(hp.DEBT), "ceiling": list(hp.CEILINGS)}
    out = {}
    for name in LATENTS:
        grid = grids[name]
        values = sorted({_latent(s, name) for s in joint}, key=grid.index)
        bracket = None
        if name in STRUCTURAL:
            status = NON
        elif not values:
            status = NOT_EVALUABLE
        elif len(values) > 1 or values[0] in (grid[0], grid[-1]):
            status = POOR
        else:
            position = grid.index(values[0])
            bracket = [grid[position - 1], grid[position + 1]]
            status = PARTIAL if len(OBSERVATIONS) < len(LATENTS) else WELL
        out[name] = {"status": status, "surviving": values, "of": grid, "bracket_rejected_neighbours": bracket,
                     "structural": STRUCTURAL.get(name)}
    out["observations"] = list(OBSERVATIONS)
    out["rule"] = IDENTIFIABILITY_RULE
    return out


def observable_table(joint: list) -> dict:
    """The arrival observables per case over the joint survivors (min / max)."""
    out = {}
    for case in CASES:
        out[case] = {}
        for name in OBSERVABLES:
            values = [s["observables"][case][name] for s in joint]
            out[case][name] = {"min": min(values), "max": max(values)} if values else None
    return out


# 4. Trajectories, the 72f crystalloid / PRBC diagnostic and the envelope proposals (P2I-2AJ-7, -8, -9) ------------------

TRAJECTORY_RULE = (
    "At each CURRENTLY_COMPATIBLE demand with joint arrival survivors: every lactate survivor of the retained pair "
    "(P3 set, crystalloid point, its 57m and 72f lactate-side points) is run by the full core at that demand, each case "
    "with its own pair (L1 and L3 once per P3 set and point, L2 once per crystalloid point), and the primary HR "
    "(pressure 0) is post-processed for every joint survivor (hr_primary.primary_series, the core's arithmetic). "
    "Readings H1-H4 and H6 per (lactate survivor, joint survivor, case); distributions LOW / median / HIGH, also by the "
    "case's intrinsic level. Validated before any reading: on the first, middle and last lactate survivor, every joint "
    "survivor, case and scenario is re-run by the full core with its HR profile (exact HR, minute 0 equal to the "
    "analytic arrival), and the demand-aware run equals lactate_closure.full_run (lactate, D) and, at demand 1.0, "
    "hr_shock.full_run (every row); else the run stops. No trajectory filter, no envelope applied, no candidate "
    "selected.")
READINGS = {
    "H1": ("hr_30", "hr_60", "hr_120", "delta_30", "delta_60", "delta_120", "max"),
    "H2": ("early_change", "nadir", "nadir_minute", "hr_60", "hr_120", "rebound"),
    "H3": ("before_unit_1", "after_unit_1", "delta_unit_1", "after_unit_2", "delta_unit_2", "unit_1_minute",
           "unit_2_minute"),
    "H4": ("hr_60", "hr_90", "hr_120", "adequacy_onset", "change_after_adequacy", "residual_above_intrinsic_120"),
    "H6": ("max_hr", "ceiling", "distance_to_ceiling", "reserve_utilization"),
}
FLUID_PRBC_RULE = (
    "72f only, diagnostic (no requirement that HR distinguish the treatments): for every 72f lactate survivor and joint "
    "survivor, L2 (2 L crystalloid over 20 min, bleeding continues) against L3 (2 PRBC units over 60 min with PPI from "
    "minute 0 and endoscopic haemostasis at 60) on the same P3 set and lactate-side point: the first minute the HRs "
    "differ at all and by more than 1 bpm, the largest difference and its minute, and which HR input diverges first "
    "(the acute signal, deficit over demand, or D). The scenarios differ in more than the fluid (PPI, haemostasis).")


def _crystalloid_end(case: str) -> int:
    item = next(i for i in lactate_slice.scenario_inputs(case, L2) if type(i).__name__ == "Crystalloid")
    return int(item.start_minute + item.duration_min)


def _prbc_start(case: str) -> int:
    item = next(i for i in lactate_slice.scenario_inputs(case, L3) if type(i).__name__ == "PackedRedCells")
    return int(item.start_minute)


def full_run(inputs: dict, case: str, scenario: str, factor: float, intrinsic: str = "midpoint",
             profile_changes: dict | None = None) -> dict:
    """hr_shock.full_run at a demand factor (applied as lactate_closure.full_run applies it); validated in run()."""
    tau_d, gain_k, k, tau_l, excess, debt, delivery = inputs["point"]
    bag = inputs["bag"] if scenario == L2 else None
    values = {**lr.blood_values(inputs["entry"], case, bag), "reserve": RESERVE}
    _, profile, full = blood_anchors.setup(case, **values)
    case_values = calibration.case_values(case, calibration.GICandidate({}, excess=excess, debt=debt,
                                                                        delivery=delivery, intrinsic=intrinsic))
    case_values["preload_fraction"] = full[bc.POS]
    case_values["arrival_delivery_ratio"] /= RESERVE
    case_values["metabolic_demand_baseline"] *= factor
    anchors = gi_reference.candidate_anchors(case, case_values)
    profile = replace(profile, debt_clearance_tau_min=tau_d, debt_per_delivery_deficit=gain_k, debt_to_lactate_gain=k,
                      lactate_clearance_tau_min=tau_l, **(profile_changes or {}))
    states, stop = blood_anchors.trajectory(anchors, lr.scenario_items(case, scenario, full), MINUTES, profile)
    unit = full["red_cell_unit_volume_ml"]
    shed = [state.blood.shed_ml for state in states]
    flow = [after - before for before, after in zip(shed, shed[1:])]
    bleed = (flow[:1] or [0.0]) + flow
    rows = []
    for minute, state in enumerate(states):
        view = derive(state, anchors, profile)
        delivery_ = effective_delivery(view.delivery_rel, anchors)
        rows.append({"minute": minute, "pulse": state.R.pulse_present, "code": state.R.code.value,
                     "rate_bpm": state.R.rate_bpm, "pressure_rel": view.pressure_rel, "spo2": view.spo2,
                     "glucose": state.glucose, "D": state.D, "drive": state.aux.sympathetic_drive,
                     "hr": view.pulse_rate_bpm, "rr": view.respiratory_rate, "lactate": view.lactate,
                     "output": view.output_rel, "delivery": delivery_, "demand": state.aux.oxygen_demand,
                     "deficit": effective_oxygen_deficit(state.aux.oxygen_demand, delivery_, RESERVE),
                     "bleed_ml_per_min": bleed[minute], "prbc_units": state.blood.transfused_ml / unit,
                     "crystalloid_in_ml": state.blood.crystalloid_in_ml})
    controlled = lr.controlled_at(states[-1])
    context = lc.Context([row["delivery"] for row in rows], [row["demand"] for row in rows], bleed, controlled, stop,
                         RESERVE)
    return {"rows": rows, "stop": stop, "controlled_at": controlled, "adequacy": context.adequacy,
            "anchors": anchors, "profile": profile}


def _first(rows: list, units: float):
    return next((row["minute"] for row in rows if row["prbc_units"] >= units - 1e-9), None)


def readings(runs: dict, rate: float, candidate: dict, case: str) -> dict:
    """H1-H4 and H6 for one (lactate survivor, joint survivor, case)."""
    series = {sc: [p["hr"] for p in hp.primary_series(runs[sc], rate, candidate["acute"], candidate["debt"],
                                                      candidate["ceiling"])] for sc in runs}
    if any(None in values or len(values) != MINUTES + 1 for values in series.values()):
        raise AssertionError("a survivor's trajectory lost its pulse or stopped")
    h1, h2, h3 = series[L1], series[L2], series[L3]
    end, start = _crystalloid_end(case), _prbc_start(case)
    nadir = min(h2)
    unit_1, unit_2 = _first(runs[L3]["rows"], 1.0), _first(runs[L3]["rows"], 2.0)
    adequacy = runs[L3]["adequacy"]
    onset = adequacy["onset"] if adequacy["status"] == lc.L3_ADEQUATE else None
    peak = max(max(values) for values in series.values())
    ceiling = candidate["ceiling"]
    return {
        "H1": {"hr_30": h1[30], "hr_60": h1[60], "hr_120": h1[120], "delta_30": h1[30] - h1[0],
               "delta_60": h1[60] - h1[0], "delta_120": h1[120] - h1[0], "max": max(h1)},
        "H2": {"early_change": h2[end] - h2[0], "nadir": nadir, "nadir_minute": h2.index(nadir), "hr_60": h2[60],
               "hr_120": h2[120], "rebound": h2[120] - nadir},
        "H3": {"before_unit_1": h3[start], "after_unit_1": h3[unit_1], "delta_unit_1": h3[unit_1] - h3[start],
               "after_unit_2": h3[unit_2], "delta_unit_2": h3[unit_2] - h3[unit_1], "unit_1_minute": unit_1,
               "unit_2_minute": unit_2},
        "H4": {"hr_60": h3[60], "hr_90": h3[90], "hr_120": h3[120], "adequacy_onset": onset,
               "change_after_adequacy": h3[120] - h3[onset] if onset is not None else None,
               "residual_above_intrinsic_120": h3[120] - rate},
        "H6": {"max_hr": peak, "ceiling": ceiling, "distance_to_ceiling": ceiling - peak,
               "reserve_utilization": (peak - rate) / (ceiling - rate)},
    }, series


def fluid_vs_prbc(runs: dict, series: dict) -> dict:
    l2, l3 = series[L2], series[L3]
    diff = [b - a for a, b in zip(l2, l3)]
    rows2, rows3 = runs[L2]["rows"], runs[L3]["rows"]
    acute = next((m for m, (a, b) in enumerate(zip(rows2, rows3))
                  if a["deficit"] / a["demand"] != b["deficit"] / b["demand"]), None)
    debt = next((m for m, (a, b) in enumerate(zip(rows2, rows3)) if a["D"] != b["D"]), None)
    largest = max(range(len(diff)), key=lambda m: abs(diff[m]))
    first_input = None if acute is None and debt is None else (
        "acute" if debt is None or (acute is not None and acute <= debt) else "debt")
    return {"diverges_at": next((m for m, d in enumerate(diff) if d != 0.0), None),
            "diverges_by_1_bpm_at": next((m for m, d in enumerate(diff) if abs(d) > 1.0), None),
            "largest_difference": abs(diff[largest]), "largest_at": largest, "prbc_minus_fluid_at_largest": diff[largest],
            "acute_signal_diverges_at": acute, "debt_diverges_at": debt, "first_input": first_input}


def _trajectory_task(task: tuple) -> tuple:
    """One (P3 set, case, lactate-side point) at one demand: L1 and L3 once, L2 per crystalloid point, every joint
    survivor post-processed."""
    key, entry, bags, point, case, factor, joint, position = task
    base = {"entry": entry, "point": point, "bag": None}
    runs = {L1: full_run(base, case, L1, factor), L3: full_run(base, case, L3, factor)}
    out = []
    for d, bag in bags:
        own = {**runs, L2: full_run({**base, "bag": bag}, case, L2, factor)}
        for n, candidate in enumerate(joint):
            level = candidate["intrinsic"][position]
            values, series = readings(own, hs.intrinsic_levels(case)[level], candidate, case)
            item = {"d": d, "candidate": n, "intrinsic": level, "readings": values}
            if case == C72:
                item["fluid_vs_prbc"] = fluid_vs_prbc(own, series)
            out.append(item)
    return key, out, 2 + len(bags)


def survivors_of(units: list) -> list[tuple]:
    """Every lactate survivor (P3 set, crystalloid point, 57m point, 72f point) of the retained pair."""
    return sorted((q, d, a, b) for _, a, b, r, ds in units for q in r for d in ds)


def validate_trajectories(source: dict, support: list, units: list, joint: list, factor: float) -> dict:
    survivors = survivors_of(units)
    sample = sorted({survivors[0], survivors[len(survivors) // 2], survivors[-1]})
    checks, runs = [], 0
    for q, d, a, b in sample:
        entry, bag = source["p3"][q], support[d]["bag"]
        for case, index, position in ((C57, a, 0), (C72, b, 1)):
            inputs = {"entry": entry, "bag": bag, "point": LAMBDAS[index]}
            for scenario in (L1, L2, L3):
                mine = full_run(inputs, case, scenario, factor)
                theirs = lc.full_run(entry, case, scenario, LAMBDAS[index], bag if scenario == L2 else None,
                                     factor=factor)
                runs += 2
                checks.append(("lactate_closure", [r["lactate"] for r in mine["rows"]] == theirs["lactate"]
                               and [r["D"] for r in mine["rows"]] == theirs["D"]))
                if factor == lc.PRIMARY_DEMAND:
                    reference = hk.full_run(inputs, case, scenario)
                    runs += 1
                    checks.append(("hr_shock", mine["rows"] == reference["rows"]))
                for candidate in joint:
                    level = candidate["intrinsic"][position]
                    changes = {"acute_deficit_to_sympathetic_gain": candidate["acute"],
                               "debt_to_sympathetic_gain": candidate["debt"],
                               "sinus_rate_ceiling_bpm": candidate["ceiling"], **hp.PRIMARY_HR_CALIBRATION}
                    full = full_run(inputs, case, scenario, factor, level, changes)
                    runs += 1
                    post = hp.primary_series(mine, hs.intrinsic_levels(case)[level], candidate["acute"],
                                             candidate["debt"], candidate["ceiling"])
                    checks.append(("hr", [p["hr"] for p in post] == [r["hr"] for r in full["rows"]]))
                    checks.append(("arrival", abs(full["rows"][0]["hr"] - candidate["predicted"][position]) <= 1e-9))
    names = sorted({name for name, _ in checks})
    return {"sample": [list(s) for s in sample], "full_runs": runs,
            "checks": {name: all(ok for n, ok in checks if n == name) for name in names},
            "exact": all(ok for _, ok in checks)}


def _spread(values: list):
    values = sorted(v for v in values if v is not None)
    if not values:
        return None
    n = len(values)
    median = values[n // 2] if n % 2 else (values[n // 2 - 1] + values[n // 2]) / 2.0
    return {"low": values[0], "median": median, "high": values[-1], "n": n}


def trajectories(source: dict, support: list, units: list, joint: list, factor: float, map_=map) -> dict:
    tasks = []
    for q, a, b, ds in sorted({(q, a, b, ds) for _, a, b, r, ds in units for q in r}):
        bags = [(d, support[d]["bag"]) for d in ds]
        for case, index, position in ((C57, a, 0), (C72, b, 1)):
            tasks.append(((q, case, index), source["p3"][q], bags, LAMBDAS[index], case, factor, joint, position))
    values = {case: {} for case in CASES}
    by_level = {case: {} for case in CASES}
    contrast, runs = [], 0
    for (q, case, index), items, n_runs in map_(_trajectory_task, tasks):
        runs += n_runs
        for item in items:
            for block, readings_ in item["readings"].items():
                for name, value in readings_.items():
                    values[case].setdefault(f"{block}.{name}", []).append(value)
                    by_level[case].setdefault(item["intrinsic"], {}).setdefault(f"{block}.{name}", []).append(value)
            if "fluid_vs_prbc" in item:
                contrast.append(item["fluid_vs_prbc"])
    n = len(survivors_of(units))
    return {"lactate_survivors": n, "joint_survivors": len(joint), "readings_per_case": n * len(joint),
            "full_runs": runs,
            "naive_full_runs": n * len(CASES) * 3,
            "distributions": {case: {name: _spread(v) for name, v in values[case].items()} for case in CASES},
            "by_intrinsic": {case: {level: {name: _spread(v) for name, v in names.items()}
                                    for level, names in by_level[case].items()} for case in CASES},
            "fluid_vs_prbc_72f": {
                "rule": FLUID_PRBC_RULE, "pairs": len(contrast),
                "never_diverge": sum(1 for c in contrast if c["diverges_at"] is None),
                **{name: _spread([c[name] for c in contrast])
                   for name in ("diverges_at", "diverges_by_1_bpm_at", "largest_difference", "largest_at",
                                "prbc_minus_fluid_at_largest", "acute_signal_diverges_at", "debt_diverges_at")},
                "first_input": {str(kind).lower(): sum(1 for c in contrast if c["first_input"] == kind)
                                for kind in ("acute", "debt", None)}}}


DATA_DRIVEN, PHYSIOLOGICAL, EXPLORATION = "DATA_DRIVEN", "PHYSIOLOGICAL", "EXPLORATION"
#: Faculty envelope proposals, written before any trajectory distribution was read; prepared, never applied.
ENVELOPES = {
    "A": {"quantity": "untreated 57m HR at 120 min (H1)", "reading": (C57, "H1.hr_120"),
          "proposal": "at or above the arrival HR (untreated ongoing haemorrhage does not relieve tachycardia) and "
                      "below the age-predicted maximum (about 220 - 57 = 163 bpm)",
          "basis": PHYSIOLOGICAL,
          "interpretation": "progressive compensation while bleeding continues untreated"},
    "B": {"quantity": "untreated 72f HR at 120 min (H1)", "reading": (C72, "H1.hr_120"),
          "proposal": "at or above the arrival HR and below the age-predicted maximum (about 220 - 72 = 148 bpm)",
          "basis": PHYSIOLOGICAL,
          "interpretation": "progressive compensation while bleeding continues untreated, in an older patient"},
    "C": {"quantity": "HR change over the first PRBC unit (H3, both cases)", "reading": (None, "H3.delta_unit_1"),
          "proposal": "a fall or no rise (<= 0 bpm) while the unit restores delivery; magnitude open",
          "basis": f"{PHYSIOLOGICAL} (direction) / {EXPLORATION} (magnitude)",
          "interpretation": "delivery restored by red cells lowers the acute signal before haemostasis"},
    "D": {"quantity": "additional HR change over the second PRBC unit (H3, both cases)",
          "reading": (None, "H3.delta_unit_2"),
          "proposal": "a fall or no rise (<= 0 bpm); no requirement on its size relative to the first unit "
                      "(endoscopic haemostasis lands at minute 60, when the second unit completes)",
          "basis": f"{PHYSIOLOGICAL} (direction) / {EXPLORATION} (magnitude)",
          "interpretation": "continued restoration; the second interval also carries PPI and approaching haemostasis"},
    "E": {"quantity": "HR at 120 min after successful definitive management (H4, both cases)",
          "reading": (None, "H4.hr_120"),
          "proposal": "within intrinsic + 15 bpm", "basis": EXPLORATION,
          "interpretation": "tachycardia largely resolved once delivery is adequate and bleeding controlled"},
    "F": {"quantity": "residual tachycardia above intrinsic at 120 min (H4, both cases)",
          "reading": (None, "H4.residual_above_intrinsic_120"),
          "proposal": "0 to 15 bpm (some debt repayment may persist)", "basis": EXPLORATION,
          "interpretation": "the debt drive repays after adequacy; a small residual is plausible, a large one is not"},
    "G": {"quantity": "maximum sinus HR and the ceiling candidates 150 / 175 / 200 (H6)",
          "reading": (None, "H6.max_hr"),
          "proposal": "a common total ceiling far above both age-predicted maxima (about 163 for 57m and 148 for 72f "
                      "by 220 - age) is physiologically implausible: drop 200, keep 150 and 175 for the faculty",
          "basis": f"{PHYSIOLOGICAL} (general physiology, not repository truth)",
          "interpretation": "ceilings bound the saturated sinus response; the arrival does not identify them"},
}
ENVELOPE_RULE = ("Each proposal is shown with the current survivors' LOW / median / HIGH, by the case's intrinsic level "
                 "and by demand; nothing is filtered, no pass count is computed and no proposal is approved by the faculty here.")


def envelope_table(by_demand: dict) -> dict:
    out = {}
    for key, envelope in ENVELOPES.items():
        case, reading = envelope["reading"]
        cases = [case] if case else list(CASES)
        current = {}
        for demand, traj in by_demand.items():
            current[demand] = {c: {"all": traj["distributions"][c].get(reading),
                                   "by_intrinsic": {level: names.get(reading)
                                                    for level, names in traj["by_intrinsic"][c].items()}}
                               for c in cases}
        out[key] = {**{k: v for k, v in envelope.items() if k != "reading"}, "reading": reading, "cases": cases,
                    "current": current, "approved": False}
    out["rule"] = ENVELOPE_RULE
    return out


# 5. Verdict, design, freeze ------------------------------------------------------------------------------------------

READY = "HR_OBSERVABLE_DECISION_PACK_READY"
NOT_READY = "HR_OBSERVABLE_DECISION_PACK_NOT_READY"
BLOCKED = "HR_SURFACE_BLOCKED_AFTER_CASE_TRUTH_PRUNING"
VERDICT_RULE = (
    f"{READY} when: (1) the retained case pair is independently case-truth compatible (the case-truth rule retains "
    "exactly the faculty's pair, and its values come from the case bands with no HR, legacy or pressure term, present "
    "in P2I-2AI's inventory); (2) its D / lactate rows remain certified (REUSE_RULE); (3) at least one joint "
    f"arrival-compatible HR candidate remains at a CURRENTLY_COMPATIBLE demand (else {BLOCKED}); (4) the sympathetic "
    "gains and ceiling are common (one triple per candidate, applied to both cases); (5) the intrinsic rate is "
    "patient-specific candidate uncertainty (all three levels explored per case, none approved); (6) the pressure "
    "contribution is 0 in the primary profile and in every validation rerun; (7) no D / lactate regression (the rows "
    "reproduce P2I-2AI's and the demand-aware runs equal lactate_closure.full_run; RR by the final certification); (8) "
    "trajectory distributions are available and validated. Otherwise "
    f"{NOT_READY} with the first blocker. Nothing is approved.")
POLICY = ("Shadow only. P2I-2AI's record and P2I-2AD's machinery (closed), never the P2F historical region (P2FGuard); "
          "legacy never read (LegacyLock). Case truth before any count; the retained pair's rows rebuilt and reused "
          "only on exact reproduction; arrival HR analytic; trajectories once per P3 set, point and crystalloid "
          "point, HR post-processed and validated; no Cartesian product with blood, fluid or other case pairs; "
          "nothing selected, filtered or approved.")


def verdict(semantics: dict, truth_ok: bool, reuse: dict, demand: dict, surfaces: dict, by_demand: dict,
            validations: dict) -> dict:
    joint = {f: s["joint"] for f, s in surfaces.items()}
    checks = [
        ("case_truth_compatible", truth_ok and all(semantics["checks"].values()),
         "the retained pair is not case-truth compatible"),
        ("lactate_rows_certified", reuse["equal"], "the retained pair's D / lactate rows are not P2I-2AI's"),
        ("joint_arrival", any(joint.values()), BLOCKED),
        ("common_gains", all(isinstance(s["acute"], float) and isinstance(s["debt"], float)
                             and isinstance(s["ceiling"], float) for f in surfaces for s in surfaces[f]["survivors"]),
         "a case-specific gain"),
        ("intrinsic_patient_specific", all(s["decompositions"] == len(CASES) * len(hp.INTRINSIC) * len(hp.ACUTE)
                                           * len(hp.DEBT) * len(hp.CEILINGS) for s in surfaces.values()),
         "the intrinsic support was narrowed"),
        ("pressure_deferred", hp.PRIMARY_HR_CALIBRATION == {"sympathetic_per_pressure_deficit": 0.0},
         "the pressure contribution is active"),
        ("no_regression", reuse["equal"] and all(v.get("checks", {}).get("lactate_closure", True)
                                                 for v in validations.values()), "D / lactate changed"),
        ("trajectories_available", bool(by_demand) and all(v["exact"] for v in validations.values()),
         "no validated trajectory distribution"),
    ]
    blockers = [why for _, passed, why in checks if not passed]
    return {"verdict": READY if not blockers else f"{NOT_READY} — {blockers[0]}",
            "checks": {name: passed for name, passed, _ in checks}, "blockers": blockers, "rule": VERDICT_RULE,
            "approved": False}


def design() -> dict:
    return {"faculty": FACULTY, "retained": [list(p) for p in RETAINED], "retained_status": RETAINED_STATUS,
            "case_truth": CASE_TRUTH_RULE, "reuse": REUSE_RULE, "demand": DEMAND_RULE, "demands": list(DEMANDS),
            "hr": HR_RULE, "identifiability": IDENTIFIABILITY_RULE, "structural": STRUCTURAL,
            "observations": list(OBSERVATIONS), "trajectories": TRAJECTORY_RULE, "readings": READINGS,
            "fluid_prbc": FLUID_PRBC_RULE, "envelopes": ENVELOPES, "envelope_rule": ENVELOPE_RULE,
            "verdict": VERDICT_RULE, "policy": POLICY, "p2i2ai_retained_units": P2I2AI_RETAINED_UNITS,
            "dependencies_at_p2i2ai": DEPENDENCIES_AT_P2I2AI}


def freeze_digest() -> str:
    text = json.dumps({"revision": REVISION, "p2i2ai": hashlib.sha256(P2I2AI_RECORD.read_bytes()).hexdigest(),
                       "design": design(), "sources": bf.freeze_sources()}, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def p2i2ai_record() -> dict:
    record = json.loads(P2I2AI_RECORD.read_text(encoding="utf-8"))
    if (record["freeze_digest"] != P2I2AI_DIGEST
            or record["recertification"][RETAINED_KEY]["digest"] != P2I2AI_RETAINED_UNITS):
        raise AssertionError("the P2I-2AI record is not the committed one")
    return record


def _p2i2ai_joint(record: dict) -> list:
    return [{k: s[k] for k in ("intrinsic", "acute", "debt", "ceiling", "predicted")}
            for s in record["hr_surface"]["survivors"] if (tuple(s["pair_57m"]), tuple(s["pair_72f"])) == RETAINED]


def run(progress=None, map_=map) -> dict:
    say = progress or (lambda *_: None)
    with lr.P2FGuard(), lr.LegacyLock():
        record = p2i2ai_record()
        compatible = [tuple(map(tuple, combo)) for combo in record["lactate_compatible"]]
        truth = case_truth(compatible)
        retained = [(tuple(t["pair_57m"]), tuple(t["pair_72f"])) for t in truth if t["status"] == "RETAINED"]
        semantics = pair_semantics(record)
        truth_ok = retained == [RETAINED]
        out = {"freeze_digest": freeze_digest(), "decided": DECIDED, "revision": REVISION, "policy": POLICY,
               "faculty": FACULTY, "record": P2I2AI_DIGEST, "pair_semantics": semantics, "case_truth": truth,
               "retained": [list(p) for p in RETAINED], "retained_status": RETAINED_STATUS}
        dependency = {"digest": dependency_digest(), "at_p2i2ai": DEPENDENCIES_AT_P2I2AI}
        dependency["equal"] = dependency["digest"] == DEPENDENCIES_AT_P2I2AI
        if not (truth_ok and all(semantics["checks"].values()) and dependency["equal"]):
            out["reuse"] = {"dependency": dependency, "equal": False}
            out["verdict"] = verdict(semantics, truth_ok, {"equal": False}, {}, {}, {}, {})
            return out
        say("haemodynamics")
        source_record = la.record_p2i2ab()
        source, support = la.source_space(source_record), source_record["crystalloid_support"]
        arrivals = lr.arrival_table()
        tasks = lc.haemodynamic_tasks(source, support)
        store = lc.haemodynamics(tasks, map_)
        regions = {}
        for factor in DEMANDS:
            say(f"retained pair x{factor:g}")
            regions[factor] = retained_region(source, support, arrivals, tasks, store, factor, map_)
        item = record["recertification"][RETAINED_KEY]
        mine = {f"{f:g}": regions[f]["survivors"] for f in DEMANDS}
        reuse = {"rule": REUSE_RULE, "pair": RETAINED_KEY, "record_freeze_digest": record["freeze_digest"],
                 "dependency": dependency, "units_digest": regions[lc.PRIMARY_DEMAND]["digest"],
                 "recorded_units_digest": item["digest"], "survivors": mine,
                 "recorded_survivors": item["survivors_by_demand"],
                 "reused_from_record": {"statistics": item["statistics"], "representatives": {
                     tag: rep["pick"] for tag, rep in item["representatives"].items()}}}
        reuse["equal"] = (reuse["units_digest"] == item["digest"] == P2I2AI_RETAINED_UNITS
                          and mine == item["survivors_by_demand"] and dependency["equal"])
        out["reuse"] = reuse
        demand = demand_support(regions)
        out["demand"] = demand
        if not reuse["equal"]:
            out["verdict"] = verdict(semantics, truth_ok, reuse, demand, {}, {}, {})
            return out
        say("arrival HR")
        compatible_demands = [f for f in DEMANDS if regions[f]["survivors"]]
        surfaces = {f: surface(arrival_table(f)) for f in compatible_demands}
        if lc.PRIMARY_DEMAND in surfaces:
            mine_joint = [{k: s[k] for k in ("intrinsic", "acute", "debt", "ceiling", "predicted")}
                          for s in surfaces[lc.PRIMARY_DEMAND]["survivors"]]
            if mine_joint != _p2i2ai_joint(record):
                raise AssertionError("the demand-1.0 arrival surface is not P2I-2AI's")
        out["hr_surfaces"] = {f"{f:g}": s for f, s in surfaces.items()}
        joint_all = [s for f in surfaces for s in surfaces[f]["survivors"]]
        out["identifiability"] = {**{f"{f:g}": identifiability(s["survivors"]) for f, s in surfaces.items()},
                                  "union": identifiability(joint_all)}
        out["observables"] = {f"{f:g}": observable_table(s["survivors"]) for f, s in surfaces.items()}
        by_demand, validations = {}, {}
        for f, s in surfaces.items():
            if not s["joint"]:
                continue
            say(f"validation x{f:g}")
            validations[f"{f:g}"] = validate_trajectories(source, support, regions[f]["units"], s["survivors"], f)
            if not validations[f"{f:g}"]["exact"]:
                break
            say(f"trajectories x{f:g}")
            by_demand[f"{f:g}"] = trajectories(source, support, regions[f]["units"], s["survivors"], f, map_)
        out["validation"] = validations
        out["trajectories"] = {"rule": TRAJECTORY_RULE, "readings": READINGS, "by_demand": by_demand}
        out["envelopes"] = envelope_table(by_demand) if by_demand else None
        out["verdict"] = verdict(semantics, truth_ok, reuse, demand, surfaces, by_demand, validations)
    out["efficiency"] = {
        "case_truth_rejections": sum(1 for t in truth if t["status"] == CASE_TRUTH_REJECTION),
        "case_truth_rejected_lactate_survivors": sum(
            record["recertification"][asv._key(tuple(t["pair_57m"]), tuple(t["pair_72f"]))]["survivors"]
            for t in truth if t["status"] == CASE_TRUTH_REJECTION),
        "haemodynamic_trajectories": len(store), "lactate_side_points_per_case": len(BASES),
        "of_lactate_side_points_per_case_in_p2i2ai": len(LAMBDAS),
        "arrival_decompositions": sum(s["decompositions"] for s in surfaces.values()),
        "validation_full_runs": sum(v["full_runs"] for v in validations.values()),
        "trajectory_full_runs": {f: t["full_runs"] for f, t in by_demand.items()},
        "trajectory_full_runs_without_sharing": {f: t["naive_full_runs"] for f, t in by_demand.items()},
        "hr_post_processed_readings": {f: t["readings_per_case"] * len(CASES) for f, t in by_demand.items()},
        "cartesian_sweep": False, "legacy_read": False}
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
        (out / "hr_observables.json").write_text(json.dumps(result, indent=1, sort_keys=True, default=str),
                                                 encoding="utf-8")
        print(out / "hr_observables.json")
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
