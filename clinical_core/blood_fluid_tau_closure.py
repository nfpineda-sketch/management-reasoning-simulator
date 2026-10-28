"""P2I-2AA: the crystalloid tau edge and the lactate-readiness semantics (shadow only).

    python -m clinical_core.blood_fluid_tau_closure --digest
    python -m clinical_core.blood_fluid_tau_closure --design
    python -m clinical_core.blood_fluid_tau_closure --run --out <directory outside the repository>

Shadow, offline and read-only. FD-BLD-04, 05 and 06 are P2I-2V-R's, byte for byte, and the robust-across-blood-region
criterion is P2I-2Z's (``blood_fluid_readiness.classify``: the 14 P2I-2Y probes and the 45 certified keys of rates 5
and 6). Nothing is fitted, interpolated, selected or approved; no lactate filter runs; no legacy trajectory, SBP or
MAP is read.

1. Tau edge (P2I-2AA-1..4). One final one-dimensional extension: F0 0.20, Finf 0.05 and 0.10, tau 120, 150, 180,
   210 and 240 min (120 reproduces P2I-2Z). Nothing above 240 is added: tau 240 surviving is TAU_REMAINS_OPEN_AT_240,
   reported with its margins, its practical identifiability and the tau -> infinity limit (no transient, Finf == F0,
   REFERENCE_ONLY: never a candidate).
2. Faculty semantics (2026-10-28), recorded for the lactate rebuild, never applied to a lactate filter here:
   - oxygen adequacy for lactate production is effective_oxygen_deficit == 0 (ADEQUATE and COMPENSATED);
   - the future lactate space keeps bleed rates 2.5, 5 and 6;
   - the L3 bleeding modifiers stay fixed provisional values (no range is invented).
3. Readiness (P2I-2AA-5) and the next lactate source space (P2I-2AA-6, 7), specified and counted, never run. The
   source space is a certified input only when the readiness verdict is READY (``certified_input``).

The design, the semantics, the criteria, the checks and the counting rules were frozen and committed before any new
outcome was evaluated (``freeze_digest``).
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path

from . import blood_anchors
from . import blood_constraints as bc
from . import blood_extension as be
from . import blood_fluid_calibration as fc
from . import blood_fluid_readiness as fr
from . import blood_rate_boundary as rb
from . import calibration, gi_reference
from .derived import (OXYGEN_ADEQUATE, OXYGEN_COMPENSATED, OXYGEN_CRITICAL, derive, effective_delivery,
                      effective_oxygen_deficit, oxygen_balance)

DECIDED = "2026-10-28"
REVISION = "P2I-2AA"
ROOT = bc.ROOT
CASES = bc.CASES
P2I2Z_RECORD = ROOT / "docs" / "revision" / "P2I2Z_blood_fluid_readiness.json"
P2I2Z_DIGEST = "e89a248ef406acda8c17d95931da98eac9e92d8ab2c1c1fb5bd2e9bf0f20ecf4"

# 1. The tau edge ----------------------------------------------------------------------------------------------------------

F0 = fr.F0
FINF = fr.FINF
TAU = (120.0, 150.0, 180.0, 210.0, 240.0)
NEW_TAU = (150.0, 180.0, 210.0, 240.0)
TAU_CAP = 240.0
GRIDS = {"F0": fc.F0_GRID, "Finf": fc.FINF_GRID, "tau": fr.GRIDS["tau"] + NEW_TAU}
CLOSED, OPEN_AT_CAP = "TAU_BOUNDARY_CLOSED_WITHIN_TESTED_DOMAIN", "TAU_REMAINS_OPEN_AT_240"
STOP = "tau 240 survives: TAU_REMAINS_OPEN_AT_240; nothing above 240 is added without a faculty decision"
#: The tau -> infinity limit: no transient leaves, every reading equals the Finf == F0 state (REFERENCE_ONLY).
LIMIT = {"F0": F0, "Finf": F0, "tau": TAU_CAP}


def _key(point: dict) -> str:
    return f"{point['F0']:g}|{point['Finf']:g}|{point['tau']:g}"


def design() -> list[dict]:
    return [{"F0": F0, "Finf": finf, "tau": tau, "status": fr.calibration_status(F0, finf), "new": tau in NEW_TAU}
            for finf, tau in itertools.product(FINF, TAU)]


def record_p2i2z() -> dict:
    return json.loads(P2I2Z_RECORD.read_text(encoding="utf-8"))


def reproduces_p2i2z(evaluated: dict, p2i2z: dict) -> list[str]:
    """Tau 120 is P2I-2Z's: the same FD-BLD-04 / 05 verdicts and the same FD-BLD-06 verdict at every one of its keys."""
    out = []
    for key, entry in evaluated.items():
        old = p2i2z["evaluated"].get(key)
        if old is None:
            continue
        if old["verdicts"] != entry["verdicts"]:
            out.append(f"{key}: FD-BLD-04 / 05")
        for label, item in old["fd06"].items():
            if {c: item[c]["pass"] for c in CASES} != {c: entry["fd06"][label][c]["pass"] for c in CASES}:
                out.append(f"{key}: FD-BLD-06 at {label}")
    return out


def region(classified: dict, p2i2z: dict) -> list[str]:
    """P2I-2Z's region below tau 120 (carried) and this package's robust points."""
    carried = [key for key in p2i2z["region"] if float(key.split("|")[2]) < min(TAU)]
    return sorted(set(carried) | {key for key, item in classified.items() if item.get("robust")},
                  key=lambda k: tuple(float(v) for v in k.split("|")))


def region_edges(survivors: list[str]) -> dict:
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


def tau_boundary(classified: dict) -> dict:
    """Per Finf and overall: the tested taus with a robust survivor, the highest, the first tested tau with none."""
    robust = {key for key, item in classified.items() if item.get("robust")}
    per = {}
    for finf in FINF:
        alive = [tau for tau in TAU if _key({"F0": F0, "Finf": finf, "tau": tau}) in robust]
        dead = [tau for tau in TAU if tau not in alive]
        per[f"{finf:g}"] = {"surviving": alive, "highest": max(alive) if alive else None,
                            "first_failing": min(dead) if dead else None,
                            "monotone": all(t in alive for t in TAU if alive and t <= max(alive))}
    alive = sorted({tau for item in per.values() for tau in item["surviving"]})
    highest = max(alive) if alive else None
    first = min((tau for tau in TAU if tau not in alive), default=None)
    status = OPEN_AT_CAP if highest == TAU_CAP else CLOSED if highest is not None else None
    return {"per_finf": per, "highest_surviving": highest, "first_without_survivor": first, "status": status,
            "interior_boundary": status == CLOSED, "stop": STOP if status == OPEN_AT_CAP else None}


# 2. Practical identifiability of tau within the 120-minute horizon ------------------------------------------------------

ENVELOPES = {"FD-BLD-04": bc.DECISIONS["FD-BLD-04"]["envelope"], "FD-BLD-05": bc.DECISIONS["FD-BLD-05"]["envelopes"],
             "FD-BLD-06": bc.DECISIONS["FD-BLD-06"]["envelopes"]}
INDISTINGUISHABLE = "CONSTRAINT_INDISTINGUISHABLE_BEYOND_240"
BOUNDED_BEYOND = "CONSTRAINT_BOUNDED_BEYOND_TESTED_DOMAIN"
BOUNDED_WITHIN = "CONSTRAINT_BOUNDED_WITHIN_TESTED_DOMAIN"
NON_MONOTONE = "NON_MONOTONE_UNRESOLVED"
PRACTICAL_RULE = (
    "Structural: for an active point (Finf < F0) tau sets how fast the transient leaves, so it reaches every retained "
    "reading (STRUCTURALLY_IDENTIFIABLE); with Finf == F0 it is inert (reference only). Practical, within the 120-min "
    "horizon and against the faculty constraints: if tau is closed inside the tested domain, "
    "CONSTRAINT_BOUNDED_WITHIN_TESTED_DOMAIN. If tau 240 survives, every reading must be monotone in tau over the "
    "tested values (else NON_MONOTONE_UNRESOLVED); then the tau -> infinity limit (no transient) decides: if it passes "
    "FD-BLD-04, 05 and 06 at every key in both cases, no constraint can tell tau >= 240 apart "
    "(CONSTRAINT_INDISTINGUISHABLE_BEYOND_240) and the surviving range propagates as uncertainty bracketed by tau 240 "
    "and the limit; if the limit fails one, a finite constraint bound lies beyond 240, untested "
    "(CONSTRAINT_BOUNDED_BEYOND_TESTED_DOMAIN). Nothing is called identified because a point fails.")


def _readings(entry: dict) -> dict:
    """Every scalar a constraint reads, by name: retained early / at 30, 60, 120 (per case) and FD-BLD-06 peak and
    120-min dilution per key, case and volume."""
    out = {}
    for case in CASES:
        out[f"early|{case}"] = entry["readings"][case]["early"]
        for minute in (30, 60, 120):
            out[f"share{minute}|{case}"] = entry["readings"][case]["share"][str(minute)] if str(minute) in entry[
                "readings"][case]["share"] else entry["readings"][case]["share"][minute]
    for label, item in entry["fd06"].items():
        for case in CASES:
            for volume, reading in item[case]["reading"].items():
                out[f"peak|{label}|{case}|{volume}"] = reading["peak"]
                out[f"at120|{label}|{case}|{volume}"] = reading["at_120"]
    return out


def margins(entry: dict) -> dict:
    """Distance to the nearest envelope edge (positive inside), the smallest over cases and keys."""
    out = {"FD-BLD-04": min(min(entry["readings"][c]["early"] - ENVELOPES["FD-BLD-04"][0],
                                ENVELOPES["FD-BLD-04"][1] - entry["readings"][c]["early"]) for c in CASES)}
    for minute, (low, high) in ENVELOPES["FD-BLD-05"].items():
        values = [entry["readings"][c]["share"].get(str(minute), entry["readings"][c]["share"].get(minute))
                  for c in CASES]
        out[f"FD-BLD-05 {minute}"] = min(min(v - low, high - v) for v in values)
    for volume, (low, high) in ENVELOPES["FD-BLD-06"].items():
        peaks = [item[c]["reading"][str(int(volume))]["peak"] for item in entry["fd06"].values() for c in CASES]
        out[f"FD-BLD-06 {int(volume)}"] = min(min(p - low, high - p) for p in peaks)
        reversal = [min(item[c]["reading"][str(int(volume))]["at_120"],
                        item[c]["reading"][str(int(volume))]["peak"] - item[c]["reading"][str(int(volume))]["at_120"])
                    for item in entry["fd06"].values() for c in CASES]
        out[f"FD-BLD-06 {int(volume)} partial reversal"] = min(reversal)
    return out


def evaluate_limit(rows: rb.Rows, keys: dict) -> dict:
    """The tau -> infinity limit (Finf == F0): REFERENCE_ONLY, read with the same rows, never a candidate."""
    point = {**LIMIT, "status": fr.ACTIVE}         # fr.evaluate reads only ACTIVE points; the label is set below
    entry = fr.evaluate(rows, [point], keys)[_key(LIMIT)]
    entry["status"] = fr.REFERENCE_ONLY
    return entry


def practical(evaluated: dict, limit: dict, keys: dict, p2i2z: dict, boundary: dict) -> dict:
    labels = [fr._blood_label(k) for k in keys["all"]]
    per = {}
    for finf in FINF:
        series = [evaluated[_key({"F0": F0, "Finf": finf, "tau": tau})] for tau in TAU]
        readings = [_readings(entry) for entry in series]
        names = sorted(readings[0])
        monotone = all(readings[i][n] <= readings[i + 1][n] + 1e-12 for n in names if not n.startswith("at120")
                       for i in range(len(readings) - 1))
        last, previous, top = readings[-1], readings[-2], _readings(limit)
        per[f"{finf:g}"] = {
            "monotone_in_tau": monotone,
            "margins_at_240": margins(series[-1]),
            "step_210_240": max(abs(last[n] - previous[n]) for n in names),
            "step_210_240_retained": max(abs(last[n] - previous[n]) for n in names if n.startswith(("early", "share"))),
            "distance_240_to_limit_retained": max(abs(top[n] - last[n]) for n in names
                                                  if n.startswith(("early", "share"))),
            "distance_240_to_limit": max(abs(top[n] - last[n]) for n in names),
        }
    limit_verdicts = {"FD-BLD-04": all(limit["verdicts"][c]["FD-BLD-04"] for c in CASES),
                      "FD-BLD-05": all(limit["verdicts"][c]["FD-BLD-05"] for c in CASES),
                      "FD-BLD-06": all(limit["fd06"][label][c]["pass"] for label in labels for c in CASES)}
    if boundary["status"] == CLOSED:
        cls = BOUNDED_WITHIN
    elif boundary["status"] == OPEN_AT_CAP:
        open_finf = [f for f, item in boundary["per_finf"].items() if item["highest"] == TAU_CAP]
        if not all(per[f]["monotone_in_tau"] for f in open_finf):
            cls = NON_MONOTONE
        else:
            cls = INDISTINGUISHABLE if all(limit_verdicts.values()) else BOUNDED_BEYOND
    else:
        cls = None
    return {"structural": "STRUCTURALLY_IDENTIFIABLE (Finf < F0); STRUCTURALLY_NON_IDENTIFIABLE when Finf == F0",
            "per_finf": per, "limit": {"point": _key(LIMIT), "status": fr.REFERENCE_ONLY, "verdicts": limit_verdicts,
                                        "margins": margins(limit)},
            "classification": cls, "rule": PRACTICAL_RULE}


def horizon_trajectories() -> dict:
    """1 L and 2 L at the middle P2I-2V-R blood representative for every design point and the limit (context)."""
    blood = be.record()["representatives"]["middle"]["values"]
    out = {}
    for point in design() + [LIMIT]:
        key = _key(point)
        out[key] = {}
        for case in CASES:
            values = {**blood[case], **fc.bag(point["F0"], point["Finf"], point["tau"])}
            if isinstance(values[bc.POS], str):
                values[bc.POS] = be.positions(case)[values[bc.POS]]
            out[key][case] = {str(int(v)): fc.fluid_trajectory(case, values, v) for v in bc.CRYSTALLOID_VOLUMES}
    return out


def horizon_gaps(trajectories: dict) -> dict:
    """Largest difference over the reported minutes (0-120) between tau 210 and 240, and between 240 and the limit."""
    fields = ("retained_share", "dilution", "output_rel", "do2", "effective_deficit")
    out = {}
    for finf in FINF:
        k210, k240 = (_key({"F0": F0, "Finf": finf, "tau": t}) for t in (210.0, 240.0))
        item = {}
        for other, name in ((k210, "210_vs_240"), (_key(LIMIT), "240_vs_limit")):
            gaps = {}
            for f in fields:
                gaps[f] = max(abs(a[f] - b[f]) for case in CASES for volume in ("1000", "2000")
                              for a, b in zip(trajectories[k240][case][volume]["rows"],
                                              trajectories[other][case][volume]["rows"]))
            item[name] = gaps
        out[f"{finf:g}"] = item
    return out


# 3. Faculty semantics -------------------------------------------------------------------------------------------------

ADEQUACY_RULE = ("FACULTY 2026-10-28: adequate oxygen availability for lactate production means "
                 "effective_oxygen_deficit == 0, so ADEQUATE and COMPENSATED both count as adequate; CRITICAL means "
                 "effective_oxygen_deficit > 0. Lactate clearance does not require a return to normal resting DO2. "
                 "Recorded for the future FD-LAC interpretation; faculty_constraints.adequate stays frozen until the "
                 "lactate rebuild, which must read this rule. No lactate filter runs here.")
ADEQUATE_STATES = (OXYGEN_ADEQUATE, OXYGEN_COMPENSATED)


def oxygen_adequate(deficit: float) -> bool:
    return deficit <= 0.0


def adequacy_consistency() -> dict:
    """On a deterministic grid of delivery, demand and reserve: state in ADEQUATE_STATES <=> deficit == 0."""
    agree, cases = True, 0
    for delivery, demand, reserve in itertools.product((0.2, 0.4, 0.5, 0.7, 0.9, 1.0, 1.2), (0.9, 1.0, 1.1),
                                                       (1.0, 2.0, 2.5, 3.0)):
        balance = oxygen_balance(delivery, demand, reserve)
        cases += 1
        agree &= (balance.state in ADEQUATE_STATES) == oxygen_adequate(balance.effective_deficit)
        agree &= (balance.state == OXYGEN_CRITICAL) == (balance.effective_deficit > 0.0)
    return {"cases": cases, "agree": agree}


LACTATE_RATES = (2.5, 5.0, 6.0)
RATE_RULE = ("FACULTY 2026-10-28: the future lactate space keeps 2.5 (it survived the blood-state faculty constraints "
             "in P2I-2V-R), 5 and 6 (tested viable, P2I-2X / P2I-2Y); 7 is the first tested jointly non-viable rate. "
             "No rate is approved; the lactate filter may reject one, nothing pre-eliminates it.")
L3_STATUS = ("FIXED_PROVISIONAL_FOR_PRIMARY_LACTATE_ANALYSIS", "FACULTY_DECISION_PENDING")
L3_MODIFIERS = ("gi_fraction_with_ppi", "gi_fraction_after_hemostasis")
L3_DECISIONS = {"gi_fraction_with_ppi": "FD-24", "gi_fraction_after_hemostasis": "FD-25"}


def l3_audit() -> dict:
    """A committed candidate range exists only if the registry entry has distinct lower and upper values."""
    out = {}
    for name in L3_MODIFIERS:
        entry = calibration.REGISTRY[name]
        has_range = entry.lower is not None and entry.upper is not None and entry.lower != entry.upper
        out[name] = {"value": entry.midpoint, "lower": entry.lower, "upper": entry.upper, "registry_status": entry.status,
                     "committed_range": has_range, "status": list(L3_STATUS), "open_decision": L3_DECISIONS[name],
                     "sensitivity_design": ({"one_at_a_time": [entry.lower, entry.upper]} if has_range else None)}
    return out


# 4. Blood-key checks the lactate space needs --------------------------------------------------------------------------

def rate25_keys() -> list[tuple]:
    """Every rate-2.5 FD-BLD-06 key built from P2I-2V-R's surviving values: a superset of its survivors' keys."""
    box = be.base_box(be.record())
    return sorted((b0, 2.5, target, tau, cap) for b0, target, tau, cap in itertools.product(
        box[fc.B0], box[fc.TARGET], box[fc.TAU], box[fc.CAP]))


def compatibility(rows: rb.Rows, region_keys: list[str], blood: list[tuple]) -> dict:
    """FD-BLD-06 for every point of the region at every given key, both cases."""
    out = {}
    for key in region_keys:
        point = dict(zip(fc.SURFACE, (float(v) for v in key.split("|"))))
        failing = []
        for b in blood:
            values = fc._crystalloid_values(point, b)
            verdicts = [rows.verdict(c, "FD-BLD-06", values) for c in CASES]
            if False in verdicts or None in verdicts:
                failing.append({"key": fr._blood_label(b), "verdicts": verdicts})
        out[key] = failing
    return out


def _old_crystalloids(grid: str) -> list[dict]:
    """The crystalloid values explored with each key: the P2I-2V-R grid (27) or P2I-2Y's surviving values (18)."""
    data = be.record()
    values = data["region"] if grid == "P2I-2V-R" else {n: be.base_box(data)[n] for n in (fc.EFFECTIVE, fc.LEAK,
                                                                                         fc.TRANSIENT)}
    return [{fc.EFFECTIVE: e, fc.LEAK: l, fc.TRANSIENT: s}
            for e, l, s in itertools.product(values[fc.EFFECTIVE], values[fc.LEAK], values[fc.TRANSIENT])]


def explored_keys() -> dict:
    """Every explored FD-BLD-06 key of rates 2.5, 5 and 6, with the crystalloid grid explored at it."""
    data = be.record()
    full = data["region"]
    out = {}
    for rate in (2.5, 5.0):
        for b0, target, tau, cap in itertools.product(full[fc.B0], full[fc.TARGET], full[fc.TAU], full[fc.CAP]):
            out[(b0, rate, target, tau, cap)] = "P2I-2V-R"
    shared = fc.robustness_region(data)["shared"]
    for rate in (5.0, 6.0):
        for b0, target, tau, cap in itertools.product(shared[fc.B0], shared[fc.TARGET], shared[fc.TAU], shared[fc.CAP]):
            out.setdefault((b0, rate, target, tau, cap), "P2I-2Y")
    return out


def completeness(rows: rb.Rows) -> dict:
    """The D substitution omits no key: at every explored key some explored old crystalloid that passes FD-BLD-04 and 05
    also passes FD-BLD-06 in both cases, so no key was excluded by the old crystalloid alone (FD-BLD-06 reads no
    position; no other constraint reads the bag)."""
    grids = {name: [c for c in _old_crystalloids(name)
                    if all(bc.passes(n, case, bc.retained(case, c)) for case in CASES
                           for n in ("FD-BLD-04", "FD-BLD-05"))] for name in ("P2I-2V-R", "P2I-2Y")}
    witness = {}
    for key, grid in sorted(explored_keys().items()):
        found = None
        for c in grids[grid]:
            values = {**c, **dict(zip(fc.PROBE_KEYS, key))}
            if all(rows.verdict(case, "FD-BLD-06", values) is True for case in CASES):
                found = [c[fc.EFFECTIVE], c[fc.LEAK], c[fc.TRANSIENT]]
                break
        witness[fr._blood_label(key)] = found
    return {"grids_passing_fd04_05": {k: len(v) for k, v in grids.items()}, "keys": len(witness),
            "without_witness": sorted(k for k, v in witness.items() if v is None), "witness": witness}


# 5. Structural checks for the factorized lactate design ------------------------------------------------------------

DELIVERY_LEVELS = ("lower", "upper")


def _deficits(anchors, profile, states) -> list[tuple]:
    out = []
    for state in states:
        delivery = effective_delivery(derive(state, anchors, profile).delivery_rel, anchors)
        out.append((effective_oxygen_deficit(state.aux.oxygen_demand, delivery, profile.oxygen_extraction_reserve),))
    return out


def structural_checks() -> dict:
    """On the P2I-2Z states: (a) rho moves neither the effective deficit nor the adequacy label (deficit == 0);
    (b) the arrival delivery level moves the deficit but not the haemodynamics."""
    bag = fc.bag(*(float(v) for v in fr.STRUCTURAL_BAG.split("|")))
    out = {}
    for tag, item in be.record()["representatives"].items():
        for case in CASES:
            values = dict(item["values"][case])
            values[bc.POS] = be.positions(case)["upper"]
            checks = {}
            for scenario in ("untreated", "crystalloid"):
                scenario_values = {**values, **bag}
                a0, p0, s0, _ = fr._run(case, scenario_values, scenario)
                d0 = _deficits(a0, p0, s0)
                for reserve in fr.RESERVES:
                    a, p, st, _ = fr._run(case, {**scenario_values, "reserve": reserve}, scenario)
                    d = _deficits(a, p, st)
                    checks[f"rho={reserve:g} ({scenario})"] = {
                        "deficit": fr._gap(d, d0),
                        "adequacy_flips": sum(oxygen_adequate(x[0]) != oxygen_adequate(y[0]) for x, y in zip(d, d0))
                        + abs(len(d) - len(d0))}
            a0, p0, s0, _ = fr._run(case, values, "untreated")
            ref = [row[:6] for row in fr._haemodynamics(a0, p0, s0)]
            d0 = _deficits(a0, p0, s0)
            for level in DELIVERY_LEVELS:
                a, p, st, _ = fr._run(case, values, "untreated", candidate_changes={"delivery": level})
                checks[f"arrival delivery={level}"] = {
                    "haemodynamics": fr._gap([row[:6] for row in fr._haemodynamics(a, p, st)], ref),
                    "deficit": fr._gap(_deficits(a, p, st), d0)}
            out[f"{tag} {case}"] = checks
    return out


def structural_summary(checks: dict) -> dict:
    tol = fr.STRUCTURAL_TOLERANCE
    rho = [c for item in checks.values() for n, c in item.items() if n.startswith("rho=")]
    delivery = [c for item in checks.values() for n, c in item.items() if n.startswith("arrival delivery")]
    return {"rho_cancels_in_deficit_and_adequacy": all(c["deficit"] <= tol and c["adequacy_flips"] == 0 for c in rho),
            "delivery_level_never_reaches_haemodynamics": all(c["haemodynamics"] <= tol for c in delivery),
            "delivery_level_moves_the_deficit": any(c["deficit"] > tol for c in delivery), "tolerance": tol}


# 6. Readiness and the next lactate source space ----------------------------------------------------------------------

READY, NOT_READY = fr.READY, fr.NOT_READY
CRYSTALLOID_CRITERION = "crystalloid candidate support characterized"
ADEQUACY_CRITERION = "oxygen adequacy semantics locked"
RATE_CRITERION = "bleed-rate support characterized (2.5, 5, 6)"
READINESS_CRITERIA = ("shared BloodState active", "DO2 / extraction model current",
                      "case-compatible preload region defined", RATE_CRITERION, CRYSTALLOID_CRITERION,
                      "no stale active haemorrhage probe bypasses BloodState",
                      "hidden parameters unapproved, candidate support explicit", ADEQUACY_CRITERION)
#: The crystalloid criterion: a non-empty robust region of active points (Finf < F0), no explored key lost to the old
#: crystalloid alone, and tau either closed inside the tested domain or CONSTRAINT_INDISTINGUISHABLE_BEYOND_240. An
#: open edge with a finite constraint bound beyond 240 is a blocker: the faculty decides. A region point failing
#: FD-BLD-06 at a rate-2.5 key (a superset of that rate's survivor keys) is no blocker: the pair is excluded from the
#: source space.
DRAFT_STATUS = "DRAFT — NOT EXECUTABLE UNTIL BLOOD/FLUID READINESS = READY"
CERTIFIED_STATUS = "CERTIFIED_SOURCE_SPACE (not executed)"


def readiness(p2i2z: dict, p2i2y: dict, region_keys: list[str], edges: dict, boundary: dict, practical_item: dict,
              compat: dict, complete: dict, adequacy: dict, summary: dict, checks_z: dict, summary_z: dict) -> dict:
    tau_like = {"upper_status": "INTERIOR_UPPER_BOUND"}         # the P2I-2Z crystalloid criterion is replaced below
    base = fr.readiness(p2i2y, region_keys, edges, tau_like, summary_z, checks_z)
    criteria = {name: base["criteria"][name] for name in base["criteria"] if name != "crystalloid candidate region "
                "characterized" and name != "bleed-rate boundary characterized"}
    marginal = be.record()["primary"]["marginal"]
    labels = {case: sorted(label for label, n in marginal[f"{bc.POS}|{case}"].items() if n) for case in CASES}
    preload = criteria["case-compatible preload region defined"]
    preload["evidence"] = {**preload["evidence"], "p2i2vr_positions (rates 2.5 and 5)": labels}
    preload["passed"] = preload["passed"] and all(
        labels[case] and all(rb.case_truth_compatible(case, be.positions(case)[label]) for label in labels[case])
        for case in CASES)
    rate25 = be.record()["primary"]["marginal"]["bleed_ml_per_min|common"].get("2.5", 0)
    criteria[RATE_CRITERION] = {
        "passed": base["criteria"]["bleed-rate boundary characterized"]["passed"] and rate25 > 0,
        "evidence": {**base["criteria"]["bleed-rate boundary characterized"]["evidence"],
                     "rate_2_5_joint_survivors_p2i2vr": rate25, "rates": list(LACTATE_RATES)}}
    tau_ok = boundary["status"] == CLOSED or practical_item["classification"] == INDISTINGUISHABLE
    criteria[CRYSTALLOID_CRITERION] = {
        "passed": bool(region_keys) and all(fr.calibration_status(*(float(v) for v in k.split("|")[:2])) == fr.ACTIVE
                                            for k in region_keys)
        and not complete["without_witness"] and tau_ok,
        "evidence": {"region": region_keys, "tau": boundary["status"], "practical": practical_item["classification"],
                     "rate_2_5_incompatible": {k: v for k, v in compat.items() if v},
                     "keys_without_witness": complete["without_witness"]}}
    criteria[ADEQUACY_CRITERION] = {
        "passed": adequacy["agree"] and summary["rho_cancels_in_deficit_and_adequacy"],
        "evidence": {"rule": ADEQUACY_RULE, "grid": adequacy, "rho": summary["rho_cancels_in_deficit_and_adequacy"]}}
    blockers = [name for name in READINESS_CRITERIA if not criteria[name]["passed"]]
    return {"criteria": {name: criteria[name] for name in READINESS_CRITERIA},
            "verdict": READY if not blockers else NOT_READY, "blockers": blockers}


ARRIVAL_PAIRS = fr.ARRIVAL_PAIRS


def _bounds(counts: dict, per_projection: int) -> tuple[int, int]:
    return (sum(math.ceil(n / per_projection) for n in counts.values()), sum(min(27, n) for n in counts.values()))


def source_space(p2i2y: dict, region_keys: list[str], complete: dict, summary: dict, summary_z: dict,
                 ready: bool, compat: dict | None = None) -> dict:
    compat = compat or {}
    """P2I-2AA-6, 7: the next lactate package's source space from current physiology, counted before any simulation.
    Never the historical P2F candidate region. Not run here."""
    passing = complete["grids_passing_fd04_05"]
    reserves = len(be.base_box(be.record())["reserve"])
    p3, p1 = {}, {}
    for rate in ("5.0", "6.0"):
        keys = p2i2y["robustness"]["rates"][rate]["survivor_keys"]
        p3[rate] = _bounds(keys, passing["P2I-2Y"] * reserves)
        p1[rate] = (len(keys), 3 * len(keys))
    joint25 = be.record()["primary"]["marginal"]["bleed_ml_per_min|common"].get("2.5", 0)
    k25 = len(rate25_keys())
    low25 = math.ceil(joint25 / (passing["P2I-2V-R"] * reserves))
    p3["2.5"] = (low25, min(k25 * 27, joint25))
    p1["2.5"] = (math.ceil(low25 / 9), k25 * 3)
    d = len(region_keys)
    post = math.prod(len(calibration.REGISTRY[n].points()) for n in
                     ("debt_clearance_tau_min", "lactate_per_output_deficit", "lactate_clearance_tau_min")) * 3
    totals = {which: sum(b[i] for b in table.values()) for which, table, i in
              (("P1 min", p1, 0), ("P1 max", p1, 1), ("P3 min", p3, 0), ("P3 max", p3, 1))}
    candidates = [totals[f"P3 {m}"] * d * len(ARRIVAL_PAIRS) * post for m in ("min", "max")]
    haemodynamic = [len(CASES) * (totals[f"P1 {m}"] + totals[f"P1 {m}"] * d + totals[f"P3 {m}"]) for m in ("min", "max")]
    naive = [c * 3 * 3 * 3 * len(CASES) for c in candidates]   # x rho 3, intrinsic 3, scenarios 3, cases 2
    valid = (summary_z["lactate_kinetics_post_process_only"] and summary_z["debt_side_never_reaches_haemodynamics"]
             and summary_z["rho_cancels_in_D_and_lactate"] and summary["rho_cancels_in_deficit_and_adequacy"]
             and summary["delivery_level_never_reaches_haemodynamics"])
    return {
        "status": CERTIFIED_STATUS if ready else DRAFT_STATUS,
        "A_blood": {"rates": {"2.5": "P2I-2V-R joint survivors (refill target <= 0.75, tau <= 240)",
                              "5.0": "P2I-2Y joint survivors (with the refill extension)",
                              "6.0": "P2I-2Y joint survivors (with the refill extension)"},
                    "joint": {"2.5": joint25, **{r: sum(p2i2y["robustness"]["rates"][r]["survivor_keys"].values())
                                                for r in ("5.0", "6.0")}},
                    "P1_bounds": {r: list(v) for r, v in p1.items()}, "P3_bounds": {r: list(v) for r, v in p3.items()},
                    "totals": totals},
        "B_positions": {case: rb.case_truth_band(case)[1] for case in CASES},
        "C_rates": list(LACTATE_RATES),
        "D_crystalloid": region_keys,
        "D_rate_2_5_pairs_excluded": {k: [item["key"] for item in v] for k, v in compat.items() if v},
        "E_oxygen": {"reserve_band": [2.0, 3.0], "simulated_at": blood_anchors.RESERVE,
                     "lactate_and_adequacy_invariant": summary["rho_cancels_in_deficit_and_adequacy"]
                     and summary_z["rho_cancels_in_D_and_lactate"], "adequacy_rule": ADEQUACY_RULE},
        "F_l3_modifiers": l3_audit(),
        "G_lactate_side": {**{n: list(calibration.REGISTRY[n].points()) for n in
                              ("debt_clearance_tau_min", "lactate_per_output_deficit", "lactate_clearance_tau_min")},
                           "arrival_lactate_excess": ["lower", "midpoint", "upper"],
                           "arrival_pairs (debt, delivery)": [list(p) for p in ARRIVAL_PAIRS],
                           "debt_per_delivery_deficit": "canonical 1.0; sensitivity 0.5 and 2 on survivors",
                           "metabolic_demand_baseline": "1.0; sensitivity 0.9 and 1.1 on survivors",
                           "intrinsic_sinus_rate": "midpoint (reaches nothing read)"},
        "counts": {"candidates": candidates, "haemodynamic_trajectories": haemodynamic,
                   "post_process_per_haemodynamic_trajectory": len(ARRIVAL_PAIRS) * post,
                   "naive_core_simulations": naive,
                   "simulations_avoided": [n - h for n, h in zip(naive, haemodynamic)]},
        "factorization_valid": valid,
    }


def certified_input(record: dict) -> dict:
    """The only way to read the source space as an analysis input: refused while readiness is not READY."""
    if record["readiness"]["verdict"] != READY or record["source_space"]["status"] != CERTIFIED_STATUS:
        raise ValueError(f"the lactate source space is {DRAFT_STATUS}")
    return record["source_space"]


# Freeze -------------------------------------------------------------------------------------------------------------------

POLICY = ("Frozen blood_constraints readings and passes(); FD-BLD-04, 05 and 06 and P2I-2Z's robust criterion "
          "unchanged. Design F0 0.20 x Finf {0.05, 0.10} x tau {120, 150, 180, 210, 240}; nothing above 240. The tau "
          "-> infinity limit is REFERENCE_ONLY. Adequacy (deficit == 0), the lactate rates and the L3 status are "
          "recorded, not applied. Trajectories and structural checks are context and filter nothing. No lactate "
          "filter runs; no lactate value, legacy trajectory, SBP or MAP is a target.")


def freeze_digest() -> str:
    text = json.dumps({
        "revision": REVISION, "record": hashlib.sha256(P2I2Z_RECORD.read_bytes()).hexdigest(), "design": design(),
        "grids": GRIDS, "limit": LIMIT, "stop": STOP, "practical": PRACTICAL_RULE, "adequacy": ADEQUACY_RULE,
        "rates": [LACTATE_RATES, RATE_RULE], "l3": [L3_STATUS, L3_MODIFIERS, L3_DECISIONS],
        "readiness": READINESS_CRITERIA, "draft": DRAFT_STATUS, "policy": POLICY, "sources": fc.freeze_sources()},
        sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run(progress=None) -> dict:
    p2i2z = record_p2i2z()
    if p2i2z["freeze_digest"] != P2I2Z_DIGEST:
        raise AssertionError("the P2I-2Z record is not the committed one")
    p2i2y = fr.record_p2i2y()
    say = progress or (lambda *_: None)
    keys = fr.blood_keys(p2i2y)
    rows = rb.Rows()
    say("tau")
    points = design()
    evaluated = fr.evaluate(rows, points, keys)
    disagreements = reproduces_p2i2z(evaluated, p2i2z)
    if disagreements:
        raise AssertionError(f"tau 120 does not reproduce P2I-2Z: {disagreements}")
    classified = fr.classify(evaluated, keys)
    region_keys = region(classified, p2i2z)
    edges = region_edges(region_keys)
    boundary = tau_boundary(classified)
    say("limit")
    limit = evaluate_limit(rows, keys)
    practical_item = practical(evaluated, limit, keys, p2i2z, boundary)
    say("trajectories")
    moved = horizon_trajectories()
    say("rate 2.5 and completeness")
    compat = compatibility(rows, region_keys, rate25_keys())
    complete = completeness(rows)
    say("structural")
    checks = structural_checks()
    summary = structural_summary(checks)
    checks_z = fr.structural_checks()
    summary_z = fr.structural_summary(checks_z)
    adequacy = adequacy_consistency()
    ready = readiness(p2i2z, p2i2y, region_keys, edges, boundary, practical_item, compat, complete, adequacy,
                      summary, checks_z, summary_z)
    return {"freeze_digest": freeze_digest(), "decided": DECIDED, "revision": REVISION,
            "record": {"P2I-2Z": p2i2z["freeze_digest"], "P2I-2Y": p2i2y["freeze_digest"]}, "policy": POLICY,
            "design": points, "evaluated": evaluated, "classified": classified, "region": region_keys, "edges": edges,
            "boundary": boundary, "limit": limit, "practical": practical_item, "trajectories": moved,
            "horizon": horizon_gaps(moved), "adequacy": {"rule": ADEQUACY_RULE, "grid": adequacy},
            "rates": {"lactate": list(LACTATE_RATES), "rule": RATE_RULE}, "l3": l3_audit(),
            "rate25_compatibility": compat, "completeness": complete,
            "structural": {"checks": checks, "summary": summary, "p2i2z_summary": summary_z},
            "readiness": ready,
            "source_space": source_space(p2i2y, region_keys, complete, summary, summary_z, ready["verdict"] == READY,
                                         compat),
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
        print(json.dumps({"design": design(), "grids": GRIDS, "limit": LIMIT}, indent=1, default=str))
        return 0
    if args.run:
        if not args.out:
            parser.error("--run needs --out (a directory outside the repository)")
        out = Path(args.out)
        if out.resolve().is_relative_to(ROOT):
            parser.error("--out must be outside the repository")
        out.mkdir(parents=True, exist_ok=True)
        result = run(lambda step: print(step, flush=True))
        (out / "blood_fluid_tau_closure.json").write_text(json.dumps(result, indent=1, sort_keys=True, default=str),
                                                          encoding="utf-8")
        print(out / "blood_fluid_tau_closure.json")
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
