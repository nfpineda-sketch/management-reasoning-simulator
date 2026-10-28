"""P2I-2Z: the crystalloid tau boundary and the readiness for a current-physiology lactate rebuild.

    python -m clinical_core.blood_fluid_readiness --digest
    python -m clinical_core.blood_fluid_readiness --design
    python -m clinical_core.blood_fluid_readiness --run --out <directory outside the repository>

Shadow, offline and read-only. The faculty constraints are P2I-2V-R's, byte for byte (FD-BLD-04, 05 and 06 through
the frozen ``blood_constraints`` rows and ``passes``). Nothing is fitted, interpolated, selected or approved; no
lactate filter runs; no legacy trajectory, SBP or MAP is read.

1. Faculty records (2026-10-28). The bleed rate is closed for this stage as ROBUST_BOUNDARY:
   TESTED_VIABLE_RATE_REGION {5, 6}, FIRST_TESTED_NONVIABLE_RATE 7 (candidate information, not approved). The
   P2I-2Y ROBUST crystalloid region is the preferred faculty-constrained candidate basis.
2. Calibration rule. For standard isotonic crystalloid in these modelled adults an active calibration candidate needs
   Finf < F0 (a transient component that redistributes). Finf == F0 stays mathematically valid as a reference or
   historical state, outside the preferred region; Finf > F0 is outside the domain (ANALYTIC_REJECTION).
3. Tau boundary (P2I-2Z-1..3). A one-dimensional extension in tau only: F0 0.20, Finf 0.05 and 0.10, tau 60, 90 and
   120 min (60 reproduces P2I-2Y). Each point reads FD-BLD-04 and 05 on the bag alone and FD-BLD-06 in both cases at
   every P2I-2Y probe and at every certified blood key (the distinct FD-BLD-06 keys of P2I-2Y's joint survivors at
   rates 5 and 6), never a blood x crystalloid product. Tau 120 surviving leaves tau OPEN_UPPER_GRID_EDGE: no
   further value is added here.
4. Readiness (P2I-2Z-7) and the next lactate input space (P2I-2Z-8), specified and counted, never run. The
   structural checks behind the factorized design read the haemodynamic and debt trajectories of fixed blood
   states while one lactate-side parameter moves.

The design, the rule, the robustness criterion, the structural checks, the readiness criteria and the input-space
rules were frozen and committed before any new point was evaluated (``freeze_digest``).
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from dataclasses import fields, replace
from pathlib import Path

from . import bands, blood_anchors
from . import blood_constraints as bc
from . import blood_extension as be
from . import blood_fluid_calibration as fc
from . import blood_rate_boundary as rb
from . import calibration, gi_reference, migration_authority
from .derived import derive, effective_delivery
from .state import CoreState

DECIDED = "2026-10-28"
REVISION = "P2I-2Z"
ROOT = bc.ROOT
CASES = bc.CASES
P2I2Y_RECORD = ROOT / "docs" / "revision" / "P2I2Y_blood_fluid_calibration.json"
P2I2Y_DIGEST = "67e5b80a5a96f526fc2f9e5b2c721026f3ac71ba612fe9cb3e06f23106f4a8d4"

# 1. Faculty records ---------------------------------------------------------------------------------------------------

TESTED_VIABLE_RATE_REGION = (5.0, 6.0)
FIRST_TESTED_NONVIABLE_RATE = 7.0
RATE_CLASSIFICATION = fc.ROBUST
RATE_STATUS = "FACULTY-CONSTRAINED CANDIDATE INFORMATION (not FACULTY_APPROVED)"
#: The P2I-2Y ROBUST crystalloid points (F0|Finf|tau), the faculty's candidate basis (not approved values).
P2I2Y_ROBUST = ("0.2|0.05|60", "0.2|0.1|30", "0.2|0.1|60")

# 2. The calibration rule ------------------------------------------------------------------------------------------------

ACTIVE, REFERENCE_ONLY = "ACTIVE_CALIBRATION_CANDIDATE", "REFERENCE_ONLY_NO_TRANSIENT"
RULE = ("standard isotonic crystalloid in these modelled adults: an active calibration candidate needs Finf < F0, "
        "a transient component that redistributes; Finf == F0 stays mathematically valid as a reference or "
        "historical state, outside the preferred region; Finf > F0 is outside the domain. Not a law for other fluids")


def calibration_status(f0: float, finf: float) -> str:
    if finf > f0 + 1e-12:
        return fc.ANALYTIC_REJECTION
    return REFERENCE_ONLY if math.isclose(finf, f0, abs_tol=1e-12) else ACTIVE


# 3. The tau boundary -----------------------------------------------------------------------------------------------------

F0 = 0.20
FINF = (0.05, 0.10)
TAU = (60.0, 90.0, 120.0)
NEW_TAU = (90.0, 120.0)
#: The tau values explored at F0 0.20 over P2I-2Y and this package; F0 and Finf keep P2I-2Y's grids (explored at
#: tau <= 60 only: the faculty fixed F0 and Finf for the extension).
GRIDS = {"F0": fc.F0_GRID, "Finf": fc.FINF_GRID, "tau": fc.TAU_GRID + NEW_TAU}
ROBUST_CRITERION = ("FD-BLD-04 and 05 on the bag alone, and FD-BLD-06 in both cases (the same key) at every P2I-2Y "
                    "probe and at every certified blood key: the distinct (B0, rate, target, tau, capacity) keys of "
                    "P2I-2Y's joint survivors at rates 5 and 6. UNREADABLE is never a pass.")
OPEN_EDGE_STOP = ("tau 120 survives: OPEN_UPPER_GRID_EDGE; no further tau is added without faculty authorization")


def _key(f0: float, finf: float, tau: float) -> str:
    return f"{f0:g}|{finf:g}|{tau:g}"


def design() -> list[dict]:
    return [{"F0": F0, "Finf": finf, "tau": tau, "status": calibration_status(F0, finf), "new": tau in NEW_TAU}
            for finf, tau in itertools.product(FINF, TAU)]


def record_p2i2y() -> dict:
    return json.loads(P2I2Y_RECORD.read_text(encoding="utf-8"))


def blood_keys(p2i2y: dict) -> dict:
    """The FD-BLD-06 keys: P2I-2Y's probes (by name) and the certified keys (rates 5 and 6), each once."""
    probes = {name: tuple(float(v) for v in key) for name, key in p2i2y["probes"].items()}
    certified = sorted({tuple(float(v) for v in key.split("|")) for rate in ("5.0", "6.0")
                        for key in p2i2y["robustness"]["rates"][rate]["survivor_keys"]})
    return {"probes": probes, "certified": certified, "all": sorted(set(probes.values()) | set(certified))}


def _blood_label(key: tuple) -> str:
    return "|".join(f"{v:g}" for v in key)


def evaluate(rows: rb.Rows, points: list[dict], keys: dict) -> dict:
    out = {}
    for point in points:
        key = _key(point["F0"], point["Finf"], point["tau"])
        if point["status"] != ACTIVE:
            out[key] = {"status": point["status"]}
            continue
        entry = {"status": ACTIVE, "bag": fc.bag(point["F0"], point["Finf"], point["tau"]), "verdicts": {},
                 "readings": {}, "fd06": {}}
        reference = fc._crystalloid_values(point, keys["probes"]["REFERENCE"])
        for case in CASES:
            entry["verdicts"][case] = {n: rows.verdict(case, n, reference) for n in ("FD-BLD-04", "FD-BLD-05")}
            retained, _ = bc._row(rows.table, case, "FD-BLD-04", reference, None)
            entry["readings"][case] = {"early": retained["early"], "share": retained["share"]}
        for blood in keys["all"]:
            values = fc._crystalloid_values(point, blood)
            item = {}
            for case in CASES:
                verdict = rows.verdict(case, "FD-BLD-06", values)
                reading, _ = bc._row(rows.table, case, "FD-BLD-06", values, None)
                item[case] = {"pass": verdict,
                              "reading": {str(int(v)): {"peak": reading[v]["peak"], "at_120": reading[v]["at_120"]}
                                          for v in blood_anchors.CRYSTALLOID_VOLUMES}}
            entry["fd06"][_blood_label(blood)] = item
        out[key] = entry
    return out


def _all(entry: dict, labels) -> bool | None:
    verdicts = [entry["fd06"][label][case]["pass"] for label in labels for case in CASES]
    return False if False in verdicts else None if None in verdicts else True


def classify(evaluated: dict, keys: dict) -> dict:
    """Per point: FD-BLD-04, FD-BLD-05, FD-BLD-06 (at the reference, at some probe, at every probe, at every certified
    key) and ROBUST_ACROSS_BLOOD_REGION."""
    probes = {name: _blood_label(key) for name, key in keys["probes"].items()}
    certified = [_blood_label(key) for key in keys["certified"]]
    out = {}
    for key, entry in evaluated.items():
        if entry["status"] != ACTIVE:
            out[key] = {"status": entry["status"]}
            continue
        f4 = all(entry["verdicts"][c]["FD-BLD-04"] for c in CASES)
        f5 = all(entry["verdicts"][c]["FD-BLD-05"] for c in CASES)
        at = {name: _all(entry, [label]) for name, label in probes.items()}
        every_probe, every_certified = _all(entry, probes.values()), _all(entry, certified)
        out[key] = {"status": ACTIVE, "FD-BLD-04": f4, "FD-BLD-05": f5, "FD-BLD-06 reference": at["REFERENCE"],
                    "FD-BLD-06 some probe": any(at.values()), "FD-BLD-06 every probe": every_probe,
                    "FD-BLD-06 every certified key": every_certified,
                    "FD-BLD-06 failing keys": sorted(label for label in set(probes.values()) | set(certified)
                                                     if _all(entry, [label]) is False),
                    "robust": bool(f4 and f5 and every_probe and every_certified)}
    return out


def reproduces_p2i2y(evaluated: dict, p2i2y: dict) -> list[str]:
    """Tau 60 was evaluated in P2I-2Y: its FD-BLD-04 / 05 verdicts and its FD-BLD-06 verdicts at every probe must be
    the same here. Returns the disagreements (none expected)."""
    out = []
    for key, entry in evaluated.items():
        old = p2i2y["crystalloid"].get(key)
        if old is None:
            continue
        if old["verdicts"] != entry["verdicts"]:
            out.append(f"{key}: FD-BLD-04 / 05")
        for name, probe in p2i2y["probes"].items():
            new = {c: entry["fd06"][_blood_label(tuple(probe))][c]["pass"] for c in CASES}
            if new != old["fd06"][name]:
                out.append(f"{key}: FD-BLD-06 at {name}")
    return out


def robust_region(classified: dict) -> list[str]:
    """P2I-2Y's robust points below tau 60 (carried: tau 15 fails FD-BLD-04 or 05 on the bag alone, tau 30 is in
    P2I-2Y's robust set and its committed test reads it at every certified key) and this package's robust points."""
    carried = [key for key in P2I2Y_ROBUST if float(key.split("|")[2]) < min(TAU)]
    return sorted(set(carried) | {key for key, item in classified.items() if item.get("robust")},
                  key=lambda k: tuple(float(v) for v in k.split("|")))


def region_edges(survivors: list[str]) -> dict:
    """Identifiability (the frozen count rule) and boundary status per side, on the robust region, against the
    explored grids (GRIDS). Nothing is identified for sitting on a grid edge."""
    points = [dict(zip(fc.SURFACE, (float(v) for v in key.split("|")))) for key in survivors]
    out = {}
    for name in fc.SURFACE:
        left = sorted({p[name] for p in points})
        lower = fc._side(GRIDS[name], left, "lower", name) if left else None
        upper = fc._side(GRIDS[name], left, "upper", name) if left else None
        out[name] = {"explored": list(GRIDS[name]), "left": left, "lower_side": lower, "upper_side": upper,
                     "class": be.identifiability(name, GRIDS[name], left), "edge": rb.edge(lower, upper) if left else None}
        out[name]["identified"] = out[name]["class"] == bc.WELL and out[name]["edge"] == be.INTERIOR
    return out


def tau_result(classified: dict, edges: dict) -> dict:
    survives = {f"{tau:g}": [key for key, item in classified.items() if item.get("robust")
                             and float(key.split("|")[2]) == tau] for tau in TAU}
    upper = edges["tau"]["upper_side"]
    status = ("OPEN_UPPER_GRID_EDGE" if upper == "OPEN" else
              "INTERIOR_UPPER_BOUND" if upper == "CONSTRAINED" else None)
    return {"survives": survives, "tau_90_survives": bool(survives["90"]), "tau_120_survives": bool(survives["120"]),
            "upper_status": status, "stop": OPEN_EDGE_STOP if status == "OPEN_UPPER_GRID_EDGE" else None}


def trajectories(region: list[str]) -> dict:
    """1 L and 2 L for each point of the design at the middle P2I-2V-R blood representative (rate 5, the case band's
    upper position), with ongoing bleeding (P2I-2Y's fluid_trajectory). Context only: no filter."""
    blood = be.record()["representatives"]["middle"]["values"]
    out = {}
    for point in design():
        key = _key(point["F0"], point["Finf"], point["tau"])
        out[key] = {}
        for case in CASES:
            values = {**blood[case], **fc.bag(point["F0"], point["Finf"], point["tau"])}
            if isinstance(values[bc.POS], str):
                values[bc.POS] = be.positions(case)[values[bc.POS]]
            out[key][case] = {str(int(v)): fc.fluid_trajectory(case, values, v) for v in bc.CRYSTALLOID_VOLUMES}
    return {"blood": "P2I-2V-R middle representative", "in_region": [k for k in out if k in region], "sets": out}


# 4. Structural checks, readiness and the next lactate input space ---------------------------------------------------

#: Fixed blood states the structural checks read: the three P2I-2V-R representatives at the case band's upper
#: position, untreated over 120 min (and, for rho, 2 L of the P2I-2Y robust bag 0.2|0.1|60).
STRUCTURAL_MINUTES = 120
STRUCTURAL_TOLERANCE = 1e-9
LACTATE_SIDE = {"lactate_per_output_deficit": (2.0, 12.0), "lactate_clearance_tau_min": (45.0, 240.0)}
DEBT_SIDE = {"debt_clearance_tau_min": (30.0, 120.0), "debt_per_delivery_deficit": (0.5, 2.0)}
CASE_SIDE = {"debt": ("lower", "upper"), "intrinsic": ("lower", "upper")}
RESERVES = (2.0, 3.0)
STRUCTURAL_BAG = "0.2|0.1|60"


def _run(case: str, values: dict, scenario: str, profile_changes: dict | None = None,
         candidate_changes: dict | None = None):
    anchors, profile, full = bc._setup(case, values)
    if candidate_changes:
        case_values = calibration.case_values(case, calibration.GICandidate({}, **candidate_changes))
        case_values["preload_fraction"] = full[bc.POS]
        case_values["arrival_delivery_ratio"] /= full["reserve"]
        anchors = gi_reference.candidate_anchors(case, case_values)
    profile = replace(profile, **(profile_changes or {}))
    extra = {"volume_ml": 2000.0} if scenario == "crystalloid" else {}
    states, stop = blood_anchors.trajectory(anchors, bc._items(case, scenario, full, **extra), STRUCTURAL_MINUTES,
                                            profile)
    return anchors, profile, states, stop


def _haemodynamics(anchors, profile, states) -> list[tuple]:
    out = []
    for state in states:
        view = derive(state, anchors, profile)
        out.append((state.V, state.hb, state.T, state.P, state.blood.volume_ml, view.output_rel, view.delivery_rel,
                    state.aux.oxygen_demand))
    return out


def _gap(a: list, b: list) -> float:
    if len(a) != len(b):
        return math.inf
    return max((abs(x - y) for row_a, row_b in zip(a, b) for x, y in zip(row_a, row_b)), default=0.0)


def structural_checks() -> dict:
    """What reaches the haemodynamics, the debt D and the lactate excess, on fixed blood states.

    - LACTATE_SIDE moves lactate only: haemodynamics and D unchanged;
    - DEBT_SIDE and the arrival debt move D (and lactate) only: haemodynamics unchanged;
    - the intrinsic sinus rate moves neither the haemodynamics nor D;
    - rho (with the band re-anchored as ratio / rho) moves neither D nor lactate: only rho x ratio reaches them; the
      delivery index (what the lactate constraints' adequacy reads) does move with rho."""
    bag = dict(zip(fc.SURFACE, (float(v) for v in STRUCTURAL_BAG.split("|"))))
    out = {}
    for tag, item in be.record()["representatives"].items():
        for case in CASES:
            values = dict(item["values"][case])
            values[bc.POS] = be.positions(case)["upper"]
            anchors, profile, base, stop = _run(case, values, "untreated")
            ref = _haemodynamics(anchors, profile, base)
            debt = [(s.D,) for s in base]
            lactate = [(s.aux.lactate_excess_mmol_l,) for s in base]
            checks = {}
            for name, levels in {**LACTATE_SIDE, **DEBT_SIDE}.items():
                for level in levels:
                    a, p, st, _ = _run(case, values, "untreated", {name: level})
                    checks[f"{name}={level:g}"] = {"haemodynamics": _gap(_haemodynamics(a, p, st), ref),
                                                   "D": _gap([(s.D,) for s in st], debt),
                                                   "lactate": _gap([(s.aux.lactate_excess_mmol_l,) for s in st], lactate)}
            for name, levels in CASE_SIDE.items():
                for level in levels:
                    a, p, st, _ = _run(case, values, "untreated", candidate_changes={name: level})
                    checks[f"arrival {name}={level}"] = {"haemodynamics": _gap(_haemodynamics(a, p, st), ref),
                                                         "D": _gap([(s.D,) for s in st], debt),
                                                         "lactate": _gap([(s.aux.lactate_excess_mmol_l,) for s in st],
                                                                         lactate)}
            for scenario in ("untreated", "crystalloid"):
                scenario_values = {**values, **fc.bag(bag["F0"], bag["Finf"], bag["tau"])}
                a0, p0, s0, _ = _run(case, scenario_values, scenario)
                for reserve in RESERVES:
                    a, p, st, _ = _run(case, {**scenario_values, "reserve": reserve}, scenario)
                    checks[f"rho={reserve:g} ({scenario})"] = {
                        "D": _gap([(s.D,) for s in st], [(s.D,) for s in s0]),
                        "lactate": _gap([(s.aux.lactate_excess_mmol_l,) for s in st],
                                        [(s.aux.lactate_excess_mmol_l,) for s in s0]),
                        "delivery_index": _gap([(effective_delivery(derive(s, a, p).delivery_rel, a),) for s in st],
                                               [(effective_delivery(derive(s, a0, p0).delivery_rel, a0),) for s in s0])}
            out[f"{tag} {case}"] = {"stop": stop, "checks": checks,
                                    "shed_ml_120": base[-1].blood.shed_ml,
                                    "volume_ml": [base[0].blood.volume_ml, base[-1].blood.volume_ml]}
    return out


def structural_summary(checks: dict) -> dict:
    def worst(prefixes, field):
        return max(item["checks"][name][field] for item in checks.values() for name in item["checks"]
                   if name.startswith(prefixes))
    tol = STRUCTURAL_TOLERANCE
    lactate_only = worst(tuple(LACTATE_SIDE), "haemodynamics") <= tol and worst(tuple(LACTATE_SIDE), "D") <= tol
    debt_no_haemo = (worst(tuple(DEBT_SIDE), "haemodynamics") <= tol
                     and worst(("arrival debt",), "haemodynamics") <= tol)
    intrinsic_none = (worst(("arrival intrinsic",), "haemodynamics") <= tol
                      and worst(("arrival intrinsic",), "D") <= tol and worst(("arrival intrinsic",), "lactate") <= tol)
    rho_cancels = worst(("rho=",), "D") <= tol and worst(("rho=",), "lactate") <= tol
    rho_moves_delivery = worst(("rho=",), "delivery_index") > tol
    return {"lactate_kinetics_post_process_only": lactate_only, "debt_side_never_reaches_haemodynamics": debt_no_haemo,
            "intrinsic_rate_reaches_nothing_read": intrinsic_none, "rho_cancels_in_D_and_lactate": rho_cancels,
            "rho_moves_the_delivery_index": rho_moves_delivery, "tolerance": tol}


READY, NOT_READY = "READY_FOR_CURRENT_PHYSIOLOGY_LACTATE_REBUILD", "NOT_READY"
READINESS_CRITERIA = (
    "shared BloodState active",
    "DO2 / extraction model current",
    "case-compatible preload region defined",
    "bleed-rate boundary characterized",
    "crystalloid candidate region characterized",
    "no stale active haemorrhage probe bypasses BloodState",
    "hidden parameters unapproved, candidate support explicit",
)
#: A criterion passes only on the evidence named for it; "crystalloid candidate region characterized" needs a non-empty
#: robust region of active points (Finf < F0) whose tau upper side is bounded by a constraint (not OPEN at the grid edge).


def readiness(p2i2y: dict, region: list[str], edges: dict, tau: dict, summary: dict, checks: dict) -> dict:
    registry_approved = [name for name, item in calibration.REGISTRY.items()
                         if getattr(item, "status", None) == calibration.FACULTY_APPROVED]
    level1 = {name: item["semantics"] for name, item in calibration.LEVEL1_DIRECT_WRITES.items()}
    haemorrhage_probe = bands.PROBES["haemorrhage"][3]
    evidence = {
        "shared BloodState active": {
            "core_state_has_blood": "blood" in {f.name for f in fields(CoreState)},
            "untreated_runs_shed_through_blood": all(item["shed_ml_120"] > 0.0
                                                     and item["volume_ml"][1] < item["volume_ml"][0]
                                                     for item in checks.values())},
        "DO2 / extraction model current": {
            "profile_has_extraction_reserve": hasattr(blood_anchors.DEFAULT_PROFILE, "oxygen_extraction_reserve"),
            "reserve_reaches_D_only_as_product": summary["rho_cancels_in_D_and_lactate"],
            "candidate_reserve": blood_anchors.RESERVE},
        "case-compatible preload region defined": {
            "bands": {case: list(rb.case_truth_band(case)) for case in CASES},
            "joint_survivor_positions": {rate: {case: [p for p, n in p2i2y["robustness"]["rates"][rate]["by_position"][case].items()
                                                       if n] for case in CASES} for rate in ("5.0", "6.0")}},
        "bleed-rate boundary characterized": {
            "conclusion": p2i2y["robustness"]["conclusion"], "record": p2i2y["rate_record"],
            "faculty": [list(TESTED_VIABLE_RATE_REGION), FIRST_TESTED_NONVIABLE_RATE, RATE_CLASSIFICATION],
            "untreated_reads_no_bag": not set(bc.TABLE_KEYS["untreated"]) & set(bc.BAG)},
        "crystalloid candidate region characterized": {
            "region": region, "all_active": all(calibration_status(*(float(v) for v in k.split("|")[:2])) == ACTIVE
                                                for k in region),
            "tau_upper": tau["upper_status"], "edges": {n: e["edge"] for n, e in edges.items()}},
        "no stale active haemorrhage probe bypasses BloodState": {
            "level1_direct_writes": level1,
            "no_physiological_haemorrhage_probe": all(s == calibration.SYNTHETIC_STATE_PERTURBATION
                                                      for s in level1.values()),
            "band_haemorrhage_probe": [type(item).__name__ for item in haemorrhage_probe],
            "historical_outside_active": not set(bands.HISTORICAL_PROBES) & set(bands.PROBES)},
        "hidden parameters unapproved, candidate support explicit": {
            "registry_faculty_approved": registry_approved,
            "family_defaults_recorded": len(migration_authority.APPROVED_FAMILY_DEFAULTS),
            "trusted_case_mappings": len(migration_authority.TRUSTED_CASE_MAPPINGS)},
    }
    passed = {
        "shared BloodState active": all(evidence["shared BloodState active"].values()),
        "DO2 / extraction model current": (evidence["DO2 / extraction model current"]["profile_has_extraction_reserve"]
                                           and summary["rho_cancels_in_D_and_lactate"]),
        "case-compatible preload region defined": all(
            all(rb.case_truth_compatible(case, float(p)) for p in positions)
            for rate in evidence["case-compatible preload region defined"]["joint_survivor_positions"].values()
            for case, positions in rate.items()),
        "bleed-rate boundary characterized": (p2i2y["robustness"]["conclusion"] == fc.ROBUST
                                              and evidence["bleed-rate boundary characterized"]["untreated_reads_no_bag"]),
        "crystalloid candidate region characterized": bool(region) and evidence[
            "crystalloid candidate region characterized"]["all_active"] and tau["upper_status"] == "INTERIOR_UPPER_BOUND",
        "no stale active haemorrhage probe bypasses BloodState": (
            evidence["no stale active haemorrhage probe bypasses BloodState"]["no_physiological_haemorrhage_probe"]
            and "BloodLoss" in evidence["no stale active haemorrhage probe bypasses BloodState"]["band_haemorrhage_probe"]
            and evidence["no stale active haemorrhage probe bypasses BloodState"]["historical_outside_active"]),
        "hidden parameters unapproved, candidate support explicit": (
            not registry_approved and not migration_authority.APPROVED_FAMILY_DEFAULTS
            and not migration_authority.TRUSTED_CASE_MAPPINGS and bool(region)),
    }
    blockers = [name for name in READINESS_CRITERIA if not passed[name]]
    return {"criteria": {name: {"passed": passed[name], "evidence": evidence[name]} for name in READINESS_CRITERIA},
            "verdict": READY if not blockers else NOT_READY, "blockers": blockers}


#: The P2F arrival (debt, delivery) pairs, unchanged (calibration.gi_candidates): none, middle, severe, mixed.
ARRIVAL_PAIRS = (("lower", "upper"), ("midpoint", "midpoint"), ("upper", "lower"), ("lower", "lower"),
                 ("upper", "upper"))
LACTATE_LEVELS = ("lower", "midpoint", "upper")
SCENARIOS = {"L1": "untreated active bleeding: blood P1 (rate, B0, lambda / kappa, refill target, tau, capacity)",
             "L2": "2 L saline over 20 min, bleeding continues: P1 x crystalloid D",
             "L3": "definitive management (2 units over 60 min, PPI, endoscopy): P3 = P1 x red-cell unit Hb and volume"}


def lactate_input_space(p2i2y: dict, region: list[str], summary: dict, ready: bool) -> dict:
    """P2I-2Z-8: the next lactate package's source space, from current physiology, with the counts before any
    simulation. Never the P2F region of 1054 historical candidates. Not run here."""
    keys = {rate: p2i2y["robustness"]["rates"][rate]["survivor_keys"] for rate in ("5.0", "6.0")}
    k5 = sum(len(v) for v in keys.values())
    p1 = (k5, 3 * k5)                                   # lambda / kappa: 1-3 values per certified 5-key
    p3 = (sum(math.ceil(n / 54) for v in keys.values() for n in v.values()),
          sum(min(27, n) for v in keys.values() for n in v.values()))   # /54: old crystalloid 18 x reserve 3
    d = len(region)
    delivery_levels = len({delivery for _, delivery in ARRIVAL_PAIRS})
    kinetics = {name: list(calibration.REGISTRY[name].points()) for name in
                ("debt_clearance_tau_min", "lactate_per_output_deficit", "lactate_clearance_tau_min")}
    post = len(kinetics["debt_clearance_tau_min"]) * len(kinetics["lactate_per_output_deficit"]) * len(
        kinetics["lactate_clearance_tau_min"]) * len(LACTATE_LEVELS)
    reserves = len(RESERVES + (blood_anchors.RESERVE,))
    # A candidate: one P3 blood set (which fixes its P1 projection), one crystalloid point, one arrival pair, the
    # lactate-side kinetics and excess, and one reserve. The naive design simulates every candidate, with the
    # intrinsic rate's three levels, in every scenario and case; the factorized one simulates each case's distinct
    # haemodynamic inputs once per arrival delivery level and post-processes the rest.
    candidates = tuple(n * d * len(ARRIVAL_PAIRS) * post * reserves for n in p3)
    simulations = tuple(len(CASES) * delivery_levels * (a + a * d + b) for a, b in zip(p1, p3))
    naive = tuple(c * len(LACTATE_LEVELS) * len(SCENARIOS) * len(CASES) for c in candidates)
    return {
        "status": "PREPARED" if ready else "DRAFT (readiness not met)",
        "A_blood": {"source": "P2I-2Y joint survivors at rates 5 and 6 (P2I-2V-R surviving values with the refill "
                              "extension), old crystalloid coordinates replaced by D and the reserve by E",
                    "joint_candidates": {rate: sum(v.values()) for rate, v in keys.items()},
                    "certified_5_keys": k5, "P1_bounds": list(p1), "P3_bounds": list(p3),
                    "exact": "enumerated once by the next package with the frozen P2I-2Y robustness logic"},
        "B_positions": {case: max(float(p) for p, n in p2i2y["robustness"]["rates"]["5.0"]["by_position"][case].items()
                                  if n) for case in CASES},
        "C_rates": list(TESTED_VIABLE_RATE_REGION),
        "D_crystalloid": region,
        "E_oxygen": {"trajectories_at_reserve": blood_anchors.RESERVE,
                     "adequacy_read_at": sorted(RESERVES + (blood_anchors.RESERVE,)),
                     "band": "re-anchored (ratio / rho)",
                     "rho_cancels_in_D_and_lactate": summary["rho_cancels_in_D_and_lactate"]},
        "F_lactate_side": {**kinetics, "arrival_lactate_excess": list(LACTATE_LEVELS),
                           "arrival_pairs (debt, delivery)": [list(p) for p in ARRIVAL_PAIRS],
                           "debt_per_delivery_deficit": "canonical 1.0; sensitivity 0.5 and 2",
                           "metabolic_demand_baseline": "1.0; sensitivity 0.9 and 1.1",
                           "intrinsic_sinus_rate": "midpoint (reaches nothing read)" if summary[
                               "intrinsic_rate_reaches_nothing_read"] else "explore",
                           "fixed single-point candidates": {name: list(calibration.REGISTRY[name].points()) for name in
                                                             ("gi_fraction_with_ppi", "gi_fraction_after_hemostasis")},
                           "engine-produced timing": "the L3 endoscopy minute (the family engine's own rule)"},
        "counts": {"candidates": list(candidates), "core_simulations_factorized": list(simulations),
                   "post_processing_per_trajectory": post, "naive_core_simulations": list(naive)},
        "factorization_valid": all(summary[k] for k in ("lactate_kinetics_post_process_only",
                                                          "debt_side_never_reaches_haemodynamics",
                                                          "rho_cancels_in_D_and_lactate")),
    }


# Freeze -------------------------------------------------------------------------------------------------------------------

POLICY = ("Frozen blood_constraints readings and passes(), primary reading only; FD-BLD-04, 05 and 06 unchanged. The "
          "tau design is F0 0.20 x Finf {0.05, 0.10} x tau {60, 90, 120}; the calibration rule (Finf < F0) classifies "
          "before any evaluation. Robust across the blood region: ROBUST_CRITERION. Tau 120 surviving is "
          "OPEN_UPPER_GRID_EDGE and stops the extension. Trajectories, structural checks and the input space are "
          "context: they filter nothing. No lactate filter runs; no lactate value, legacy trajectory, SBP or MAP is a "
          "target.")


def freeze_digest() -> str:
    text = json.dumps({
        "revision": REVISION, "record": hashlib.sha256(P2I2Y_RECORD.read_bytes()).hexdigest(),
        "rate": [list(TESTED_VIABLE_RATE_REGION), FIRST_TESTED_NONVIABLE_RATE, RATE_CLASSIFICATION],
        "p2i2y_robust": P2I2Y_ROBUST, "rule": RULE, "design": design(), "grids": GRIDS,
        "robust": ROBUST_CRITERION, "stop": OPEN_EDGE_STOP,
        "structural": [STRUCTURAL_MINUTES, STRUCTURAL_TOLERANCE, LACTATE_SIDE, DEBT_SIDE, CASE_SIDE, RESERVES,
                       STRUCTURAL_BAG],
        "readiness": READINESS_CRITERIA, "arrival_pairs": ARRIVAL_PAIRS, "scenarios": SCENARIOS, "policy": POLICY,
        "sources": fc.freeze_sources()}, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run(progress=None) -> dict:
    p2i2y = record_p2i2y()
    if p2i2y["freeze_digest"] != P2I2Y_DIGEST:
        raise AssertionError("the P2I-2Y record is not the committed one")
    say = progress or (lambda *_: None)
    keys = blood_keys(p2i2y)
    rows = rb.Rows()
    say("tau")
    points = design()
    evaluated = evaluate(rows, points, keys)
    disagreements = reproduces_p2i2y(evaluated, p2i2y)
    if disagreements:
        raise AssertionError(f"tau 60 does not reproduce P2I-2Y: {disagreements}")
    classified = classify(evaluated, keys)
    region = robust_region(classified)
    edges = region_edges(region)
    tau = tau_result(classified, edges)
    say("trajectories")
    moved = trajectories(region)
    say("structural")
    checks = structural_checks()
    summary = structural_summary(checks)
    ready = readiness(p2i2y, region, edges, tau, summary, checks)
    return {"freeze_digest": freeze_digest(), "decided": DECIDED, "revision": REVISION,
            "record": {"P2I-2Y": p2i2y["freeze_digest"]}, "policy": POLICY, "rule": RULE,
            "rate": {"TESTED_VIABLE_RATE_REGION": list(TESTED_VIABLE_RATE_REGION),
                     "FIRST_TESTED_NONVIABLE_RATE": FIRST_TESTED_NONVIABLE_RATE,
                     "classification": RATE_CLASSIFICATION, "status": RATE_STATUS},
            "design": points, "keys": {"probes": {k: list(v) for k, v in keys["probes"].items()},
                                       "certified": [list(k) for k in keys["certified"]], "distinct": len(keys["all"])},
            "evaluated": evaluated, "classified": classified, "region": region, "edges": edges, "tau": tau,
            "trajectories": moved, "structural": {"checks": checks, "summary": summary}, "readiness": ready,
            "lactate_input_space": lactate_input_space(p2i2y, region, summary, ready["verdict"] == READY),
            "rows_computed": rows.computed, "contradictions": be.contradictions(rows.table)}


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
        print(json.dumps({"design": design(), "grids": GRIDS, "rule": RULE}, indent=1, default=str))
        return 0
    if args.run:
        if not args.out:
            parser.error("--run needs --out (a directory outside the repository)")
        out = Path(args.out)
        if out.resolve().is_relative_to(ROOT):
            parser.error("--out must be outside the repository")
        out.mkdir(parents=True, exist_ok=True)
        result = run(lambda step: print(step, flush=True))
        (out / "blood_fluid_readiness.json").write_text(json.dumps(result, indent=1, sort_keys=True, default=str),
                                                        encoding="utf-8")
        print(out / "blood_fluid_readiness.json")
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
