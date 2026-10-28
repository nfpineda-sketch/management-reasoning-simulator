"""P2I-2Y: the crystalloid calibration surface (F0, Finf, tau) and a targeted bleed-rate robustness check.

    python -m clinical_core.blood_fluid_calibration --digest
    python -m clinical_core.blood_fluid_calibration --design
    python -m clinical_core.blood_fluid_calibration --run --out <directory outside the repository>

Shadow, offline and read-only. The faculty constraints are P2I-2V-R's, byte for byte: every reading is a frozen
``blood_constraints`` row function (through P2I-2W's frozen ``_compute``) and every verdict its frozen ``passes``.
Nothing is fitted, interpolated, selected or approved; no lactate, legacy trajectory, SBP or MAP is read.

1. Bleed-rate robustness (P2I-2Y-1). P2I-2X recorded TESTED_VIABLE_RATE_REGION {5, 6} and
   FIRST_TESTED_NONVIABLE_RATE 7, conditional on refill target <= 0.75 and tau <= 240. Only the common rates 5, 6
   and 7 are crossed with the refill extension P2I-2W found (target 1.0, tau 480), over the surviving P2I-2V-R
   values of every other blood dimension and the case-compatible positions (each case band's lower, midpoint and
   upper). The exact pre-filter of P2I-2X (constraints whose readings exclude the rate) runs first.
2. Crystalloid surface (P2I-2Y-2..9). The calibration surface is F0 (initial effective circulating fraction of
   each mL infused), Finf (long-term retained fraction) and tau (redistribution time constant), 0 <= Finf <= F0.
   They map onto the existing contributor exactly: effective_ml_per_ml = F0, transient_share = 1 - Finf / F0,
   leak_tau_min = tau (``bag``). The faculty's exploration grid is frozen here; Finf > F0 is rejected analytically.
   FD-BLD-04 and 05 read the bag alone (blood_constraints cross-checks that they do not depend on the bleeding, B0
   or refill); FD-BLD-06 reads the bag against a blood state, so it is read against predeclared probes drawn from
   the certified surviving blood candidates, never against a full blood x crystalloid product.

The designs, the grid, the probe rule, the representative rules and the policy were frozen and committed before
any new point was evaluated (``freeze_digest``).
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path

from . import blood_constraints as bc
from . import blood_extension as be
from . import blood_rate_boundary as rb
from . import lactate_slice

DECIDED = "2026-10-28"
REVISION = "P2I-2Y"
ROOT = bc.ROOT
CASES = bc.CASES
P2I2X_RECORD = ROOT / "docs" / "revision" / "P2I2X_blood_rate_boundary.json"
P2I2X_DIGEST = "668bad9903da9a4ee1d49a5e2be06f7be7795140091b98d898a169b8682c67a5"
TARGET, TAU, CAP, B0 = "plasma_refill_target_share", "plasma_refill_tau_min", "plasma_refill_capacity_ml", bc.B0
EFFECTIVE, TRANSIENT, LEAK = "crystalloid_effective_ml_per_ml", "crystalloid_transient_share", "crystalloid_leak_tau_min"

# 1. Bleed-rate robustness -----------------------------------------------------------------------------------------

#: The faculty's record of P2I-2X (2026-10-28): a faculty-constrained candidate result, not an approved rate.
TESTED_VIABLE_RATE_REGION = (5.0, 6.0)
FIRST_TESTED_NONVIABLE_RATE = 7.0
ROBUSTNESS_RATES = (5.0, 6.0, 7.0)
EXTRA_TARGET, EXTRA_TAU = 1.0, 480.0
POSITIONS = ("lower", "midpoint", "upper")
ROBUST, DEPENDS = "ROBUST_BOUNDARY", "BOUNDARY_DEPENDS_ON_REFILL_EXTENSION"


def robustness_region(data: dict | None = None) -> dict:
    """The surviving P2I-2V-R value of every shared dimension, with the refill target and tau extended by the values
    P2I-2W found viable (1.0; 480), and each case's case-compatible positions."""
    data = data or be.record()
    values = rb.region(data)
    shared = {name: values[name] for name in bc.SHARED}
    shared[TARGET] = tuple(sorted(set(shared[TARGET]) | {EXTRA_TARGET}))
    shared[TAU] = tuple(sorted(set(shared[TAU]) | {EXTRA_TAU}))
    positions = {case: tuple(be.positions(case)[label] for label in POSITIONS) for case in CASES}
    return {"shared": shared, "positions": positions}


def robustness_design(data: dict | None = None) -> dict:
    region = robustness_region(data)
    shared = region["shared"]
    pairs = list(itertools.product(shared[TARGET], shared[TAU]))
    return {"rates": list(ROBUSTNESS_RATES), "targets": list(shared[TARGET]), "taus": list(shared[TAU]),
            "refill_pairs": [list(pair) for pair in pairs],
            "new_refill_pairs": [list(pair) for pair in pairs if EXTRA_TARGET in pair or EXTRA_TAU in pair],
            "positions": {case: list(region["positions"][case]) for case in CASES},
            "shared_combinations": math.prod(len(v) for v in shared.values())}


def robustness(rows: rb.Rows, data: dict) -> dict:
    """Each case alone at each case-compatible position, then joint: a joint candidate takes one shared value set,
    one common rate and one position per case, so the joint count of a shared set is the product of the cases'
    surviving positions."""
    region = robustness_region(data)
    shared, positions = region["shared"], region["positions"]
    caches = {case: {} for case in CASES}
    combos = [dict(zip(bc.SHARED, c)) for c in itertools.product(*(shared[n] for n in bc.SHARED))]
    passing = {case: {} for case in CASES}          # combo index -> positions passing the exact pre-filter
    analytic = {case: 0 for case in CASES}
    for case in CASES:
        for index, combo in enumerate(combos):
            kept = [p for p in positions[case]
                    if not rb._independent(rows, case, rb._values(combo, case, ROBUSTNESS_RATES[0], p), caches[case])]
            analytic[case] += len(positions[case]) - len(kept)
            if kept:
                passing[case][index] = kept
    out = {"shared_combinations": len(combos), "case_candidates_per_rate": {c: len(combos) * len(positions[c])
                                                                               for c in CASES},
           "analytic_rejection": analytic, "rates": {}}
    for rate in ROBUSTNESS_RATES:
        item = {"joint": 0, "joint_unreadable": 0, "alone": {c: 0 for c in CASES},
                "alone_unreadable": {c: 0 for c in CASES}, "u_out_fail": {c: 0 for c in CASES},
                "simulated": {c: sum(len(v) for v in passing[c].values()) for c in CASES},
                "by_refill": {}, "by_position": {c: {str(p): 0 for p in positions[c]} for c in CASES},
                "survivor_keys": {}}
        for index in sorted(set(passing[CASES[0]]) | set(passing[CASES[1]])):
            combo = combos[index]
            states = {}
            for case in CASES:
                states[case] = {}
                for p in passing[case].get(index, []):
                    state, first = rb._case(rows, case, rb._values(combo, case, rate, p), caches[case])
                    states[case][p] = state
                    item["alone"][case] += state == "pass"
                    item["alone_unreadable"][case] += state == "unreadable"
                    item["u_out_fail"][case] += first == "U-OUT"
            ok = {c: [p for p, s in states[c].items() if s == "pass"] for c in CASES}
            maybe = {c: [p for p, s in states[c].items() if s in ("pass", "unreadable")] for c in CASES}
            joint = len(ok[CASES[0]]) * len(ok[CASES[1]])
            item["joint_unreadable"] += len(maybe[CASES[0]]) * len(maybe[CASES[1]]) - joint
            if joint:
                item["joint"] += joint
                pair = f"{combo[TARGET]:g}|{combo[TAU]:g}"
                item["by_refill"][pair] = item["by_refill"].get(pair, 0) + joint
                for c in CASES:
                    other = len(ok[CASES[1] if c == CASES[0] else CASES[0]])
                    for p in ok[c]:
                        item["by_position"][c][str(p)] += other
                key = "|".join(f"{v:g}" for v in (combo[B0], rate, combo[TARGET], combo[TAU], combo[CAP]))
                item["survivor_keys"][key] = item["survivor_keys"].get(key, 0) + joint
        out["rates"][str(rate)] = item
    joint7 = out["rates"][str(FIRST_TESTED_NONVIABLE_RATE)]
    out["conclusion"] = (ROBUST if joint7["joint"] == 0 and joint7["joint_unreadable"] == 0 else DEPENDS)
    out["rate_6_by_refill"] = out["rates"]["6.0"]["by_refill"]
    return out


# 2. The crystalloid calibration surface -------------------------------------------------------------------------------

F0_GRID = (0.15, 0.20, 0.25, 0.30, 0.35)
FINF_GRID = (0.0, 0.05, 0.10, 0.15, 0.20)
TAU_GRID = (15.0, 30.0, 60.0)
ANALYTIC_REJECTION, SIMULATION_REJECTION = "ANALYTIC_REJECTION", "SIMULATION_REJECTION"
CRYSTALLOID_CONSTRAINTS = ("FD-BLD-04", "FD-BLD-05", "FD-BLD-06")
SURFACE = ("F0", "Finf", "tau")
#: The surface's domains: F0 a share of the volume infused, Finf a share no larger than F0, tau positive.
DOMAIN = {"F0": (0.0, 1.0, "share of each mL infused that enters the circulation (0, 1]"),
          "Finf": (0.0, None, "long-term retained share, 0 <= Finf <= F0"),
          "tau": (0.0, None, "redistribution time constant (min), positive")}


def bag(f0: float, finf: float, tau: float) -> dict:
    """F0 / Finf / tau onto the existing Crystalloid contributor, exactly (fluids.Crystalloid: a share F0 of each mL
    enters the circulation; transient_share of that leaves with leak_tau_min; the rest stays)."""
    if not (0.0 < f0 <= 1.0 and 0.0 <= finf <= f0 and tau > 0.0):
        raise ValueError(f"outside the crystalloid surface's domain: F0 {f0}, Finf {finf}, tau {tau}")
    return {EFFECTIVE: f0, TRANSIENT: 1.0 - finf / f0, LEAK: tau}


def surface(values: dict) -> dict:
    """The inverse map, for reports."""
    f0 = values[EFFECTIVE]
    return {"F0": f0, "Finf": f0 * (1.0 - values[TRANSIENT]), "tau": values[LEAK]}


def grid() -> list[dict]:
    out = []
    for f0, finf, tau in itertools.product(F0_GRID, FINF_GRID, TAU_GRID):
        point = {"F0": f0, "Finf": finf, "tau": tau}
        point["status"] = ANALYTIC_REJECTION if finf > f0 + 1e-12 else "EVALUATED"
        out.append(point)
    return out


def _bag_key(point: dict) -> tuple:
    values = bag(point["F0"], point["Finf"], point["tau"])
    return tuple(values[n] for n in bc.BAG)


#: The blood probes FD-BLD-06 is read against (the only crystalloid constraint that reads a blood state): the FD-BLD-06
#: keys (B0, rate, target, tau, capacity) of real certified survivors, never a full product.
#: - REFERENCE: blood_anchors.REFERENCE, whose values are all surviving values (the "isolated" reading);
#: - REPRESENTATIVE: the three P2I-2V-R representatives;
#: - BOUNDARY: for each key dimension, each extreme surviving value among the robustness scan's joint survivors at
#:   rates 5 and 6, taking the survivor key that is first in sorted order.
PROBE_KEYS = (B0, bc.BLEED, TARGET, TAU, CAP)


def probes(data: dict, survivor_keys: dict) -> dict:
    from . import blood_anchors
    out = {"REFERENCE": tuple(float(blood_anchors.REFERENCE[n]) for n in PROBE_KEYS)}
    for tag, item in data["representatives"].items():
        values = item["values"][CASES[0]]
        out[f"REPRESENTATIVE {tag}"] = tuple(float(values[n]) for n in PROBE_KEYS)
    keys = sorted(tuple(float(v) for v in key.split("|")) for key in survivor_keys)
    for i, name in enumerate(PROBE_KEYS):
        values = sorted({key[i] for key in keys})
        for label, value in (("min", values[0]), ("max", values[-1])):
            out[f"BOUNDARY {name} {label}"] = next(key for key in keys if key[i] == value)
    return out


def _crystalloid_values(point: dict, probe: tuple) -> dict:
    return {**bag(point["F0"], point["Finf"], point["tau"]), **dict(zip(PROBE_KEYS, probe))}


def crystalloid_filter(rows: rb.Rows, points: list[dict], blood: dict) -> dict:
    """FD-BLD-04 / 05 on the bag alone (both cases) and FD-BLD-06 at every probe (both cases, the same probe)."""
    out = {}
    for point in points:
        key = f"{point['F0']:g}|{point['Finf']:g}|{point['tau']:g}"
        if point["status"] == ANALYTIC_REJECTION:
            out[key] = {"status": ANALYTIC_REJECTION}
            continue
        entry = {"status": "EVALUATED", "bag": bag(point["F0"], point["Finf"], point["tau"]), "verdicts": {},
                 "readings": {}, "fd06": {}}
        for case in CASES:
            values = _crystalloid_values(point, blood["REFERENCE"])
            entry["verdicts"][case] = {n: rows.verdict(case, n, values) for n in ("FD-BLD-04", "FD-BLD-05")}
            retained, _ = bc._row(rows.table, case, "FD-BLD-04", values, None)
            entry["readings"][case] = {"early": retained["early"], "share": retained["share"]}
        for probe, blood_key in blood.items():
            entry["fd06"][probe] = {case: rows.verdict(case, "FD-BLD-06", _crystalloid_values(point, blood_key))
                                    for case in CASES}
        out[key] = entry
    return out


def _passes(entry: dict, names: tuple, probe: str | None = None) -> bool | None:
    verdicts = []
    for case in CASES:
        verdicts += [entry["verdicts"][case][n] for n in names if n != "FD-BLD-06"]
        if "FD-BLD-06" in names:
            verdicts.append(entry["fd06"][probe][case])
    if False in verdicts:
        return False
    return None if None in verdicts else True


def crystalloid_counts(filtered: dict, blood: dict) -> dict:
    """Survivors per constraint and combined. Primary: FD-BLD-04 and 05 (bag alone) and FD-BLD-06 at some certified
    blood probe (the same probe in both cases); ROBUST: at every probe; ISOLATED: at the reference."""
    evaluated = {k: v for k, v in filtered.items() if v["status"] != ANALYTIC_REJECTION}
    per = {"FD-BLD-04": [], "FD-BLD-05": [], "FD-BLD-06 (some probe)": [], "FD-BLD-06 (every probe)": [],
           "FD-BLD-06 (reference)": []}
    combined = {"primary": [], "robust": [], "isolated": []}
    interaction = []
    for key, entry in evaluated.items():
        f4, f5 = _passes(entry, ("FD-BLD-04",)), _passes(entry, ("FD-BLD-05",))
        f6 = {probe: _passes(entry, ("FD-BLD-06",), probe) for probe in blood}
        if f4:
            per["FD-BLD-04"].append(key)
        if f5:
            per["FD-BLD-05"].append(key)
        if any(f6.values()):
            per["FD-BLD-06 (some probe)"].append(key)
        if all(f6.values()):
            per["FD-BLD-06 (every probe)"].append(key)
        if f6["REFERENCE"]:
            per["FD-BLD-06 (reference)"].append(key)
        if f4 and f5:
            if any(f6.values()):
                combined["primary"].append(key)
            if all(f6.values()):
                combined["robust"].append(key)
            if f6["REFERENCE"]:
                combined["isolated"].append(key)
            if len(set(f6.values())) > 1:
                interaction.append({"point": key, "fails_at": sorted(p for p, v in f6.items() if not v),
                                    "isolated": bool(f6["REFERENCE"])})
    return {"evaluated": len(evaluated), "analytic_rejection": len(filtered) - len(evaluated),
            "per_constraint": {k: len(v) for k, v in per.items()}, "combined": {k: len(v) for k, v in combined.items()},
            "survivors": combined, "interaction": interaction}


def _side(explored, left, which, name):
    ordered = sorted(explored)
    extreme = ordered[-1] if which == "upper" else ordered[0]
    if extreme not in left:
        return "CONSTRAINED"
    low = DOMAIN[name][0]
    if which == "lower" and low is not None and math.isclose(extreme, low):
        return "DOMAIN"
    return "OPEN"


def surface_edges(survivors: list[str]) -> dict:
    """Identifiability (the frozen count rule) and boundary status per side, for F0, Finf and tau, on a survivor
    set. A side is DOMAIN only where the explored edge is the surface's own domain limit (Finf = 0)."""
    points = [dict(zip(SURFACE, (float(v) for v in key.split("|")))) for key in survivors]
    grids = {"F0": F0_GRID, "Finf": FINF_GRID, "tau": TAU_GRID}
    out = {}
    for name in SURFACE:
        left = sorted({p[name] for p in points})
        lower = _side(grids[name], left, "lower", name) if left else None
        upper = _side(grids[name], left, "upper", name) if left else None
        out[name] = {"explored": list(grids[name]), "left": left, "lower_side": lower, "upper_side": upper,
                     "class": be.identifiability(name, grids[name], left), "edge": rb.edge(lower, upper) if left else None}
        out[name]["identified"] = out[name]["class"] == bc.WELL and out[name]["edge"] == be.INTERIOR
    return out


#: Representative crystalloid sets: among the primary survivors, ordered by the early retained share (FD-BLD-04's
#: reading, 57m), then F0, Finf and tau; low / middle / high are the first, the floor(n/2)-th and the last.
def crystalloid_representatives(filtered: dict, survivors: list[str]) -> dict:
    ordered = sorted(survivors, key=lambda k: (filtered[k]["readings"][CASES[0]]["early"],
                                               *(float(v) for v in k.split("|"))))
    if not ordered:
        return {}
    return {"low": ordered[0], "middle": ordered[len(ordered) // 2], "high": ordered[-1]}


FLUID_MINUTES = (0, 20, 30, 60, 120)


def fluid_trajectory(case: str, values: dict, volume: float) -> dict:
    """One bag with ongoing bleeding and the candidate's own haemodynamics, against the same bleeding without it:
    the retained share, the Hb dilution and its reversal, output, DO2 and the oxygen state (context only)."""
    anchors, profile, _, states, stop = bc._run(case, values, "crystalloid", bc.CRYSTALLOID_MINUTES,
                                                volume_ml=volume)
    _, _, _, baseline, base_stop = bc._run(case, values, "untreated", bc.CRYSTALLOID_MINUTES)
    reach = min(len(states), len(baseline))
    rows = []
    for m in FLUID_MINUTES:
        if m >= reach:
            continue
        reading = bc._reading(states[m], anchors, profile)
        rows.append({"minute": m, "retained_share": (states[m].blood.crystalloid_in_ml
                                                     - states[m].blood.crystalloid_out_ml) / volume,
                     "dilution": baseline[m].hb - states[m].hb, "output_rel": reading["output_rel"],
                     "do2": reading["do2"], "state": reading["state"], "effective_deficit": reading["effective_deficit"],
                     "circulating_ml": reading["circulating_ml"], "hb": reading["hb"]})
    window = range(min(reach, bc.DILUTION_WINDOW + 1))
    dilution = [baseline[m].hb - states[m].hb for m in window]
    peak = max(dilution) if dilution else None
    end = dilution[-1] if dilution else None
    return {"stop": stop, "baseline_stop": base_stop, "rows": rows, "peak_dilution": peak,
            "reversal_fraction": (peak - end) / peak if peak else None,
            "early_retained": max(r["retained_share"] for r in rows if r["minute"] <= bc.EARLY_WINDOW)}


def trajectories(data: dict, filtered: dict, representatives: dict) -> dict:
    """1 L and 2 L for each representative set, at the middle P2I-2V-R blood representative (P2I-2Y-7), and the
    state dependence: the same sets at each case's lower, midpoint and upper position (P2I-2Y-6)."""
    blood = data["representatives"]["middle"]["values"]
    out = {"sets": {}, "state_dependence": {}}
    for tag, key in representatives.items():
        bag_values = filtered[key]["bag"]
        out["sets"][tag] = {"point": key, "trajectories": {}}
        out["state_dependence"][tag] = {}
        for case in CASES:
            values = {**blood[case], **bag_values}
            values[bc.POS] = be.positions(case)[values[bc.POS]] if isinstance(values[bc.POS], str) else values[bc.POS]
            out["sets"][tag]["trajectories"][case] = {str(int(v)): fluid_trajectory(case, values, v)
                                                     for v in bc.CRYSTALLOID_VOLUMES}
            out["state_dependence"][tag][case] = {}
            for label in POSITIONS:
                position = be.positions(case)[label]
                moved = {**values, bc.POS: position}
                item = {}
                for volume in bc.CRYSTALLOID_VOLUMES:
                    t = fluid_trajectory(case, moved, volume)
                    first = t["rows"][0]["output_rel"] if t["rows"] else None
                    peak = max((r["output_rel"] for r in t["rows"] if r["minute"] <= bc.EARLY_WINDOW), default=None)
                    item[str(int(volume))] = {"position": position, "peak_output_gain": (peak / first - 1.0)
                                              if first else None, "stop": t["stop"]}
                out["state_dependence"][tag][case][label] = item
    return out


# Freeze ----------------------------------------------------------------------------------------------------------------

POLICY = ("Frozen blood_constraints readings and passes(), primary reading only. Robustness: the exact pre-filter of "
          "P2I-2X first; each case at each case-compatible position, read U-OUT, U-HB, FD-BLD-08, FD-BLD-06 until its "
          "first readable failure; joint survivors are the product of the cases' surviving positions per shared set "
          "and common rate; UNREADABLE never counts as a failure. Crystalloid: Finf > F0 is an ANALYTIC_REJECTION; "
          "FD-BLD-04 and 05 read the bag alone in both cases; FD-BLD-06 reads every predeclared certified blood probe "
          "in both cases (the same probe); primary survival needs FD-BLD-06 at some probe, robust at every probe, "
          "isolated at the reference. Secondary consequences (output, Hb, DO2, deficit) are reported, never filtered. "
          "No lactate, legacy trajectory, SBP or MAP is read.")


def freeze_sources() -> dict[str, str]:
    out = {}
    for path in sorted((ROOT / "clinical_core").rglob("*.py")):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in lactate_slice.DOWNSTREAM_REPORTS:
            out[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def freeze_digest() -> str:
    data = be.record()
    text = json.dumps({
        "revision": REVISION,
        "records": {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in
                    (("P2I-2V-R", be.P2I2VR_RECORD), ("P2I-2W", rb.P2I2W_RECORD), ("P2I-2X", P2I2X_RECORD))},
        "rate_record": [TESTED_VIABLE_RATE_REGION, FIRST_TESTED_NONVIABLE_RATE], "robustness": robustness_design(data),
        "grid": grid(), "probe_keys": PROBE_KEYS, "constraints": CRYSTALLOID_CONSTRAINTS, "domain": DOMAIN,
        "fluid_minutes": FLUID_MINUTES, "positions": POSITIONS, "policy": POLICY, "sources": freeze_sources()},
        sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run(progress=None) -> dict:
    data = be.record()
    p2i2x = json.loads(P2I2X_RECORD.read_text(encoding="utf-8"))
    if data["freeze_digest"] != be.P2I2VR_DIGEST or p2i2x["freeze_digest"] != P2I2X_DIGEST:
        raise AssertionError("the P2I-2V-R or P2I-2X record is not the committed one")
    say = progress or (lambda *_: None)
    rows = rb.Rows()
    say("robustness")
    robust = robustness(rows, data)
    old = [f"{t:g}|{u:g}" for t, u in itertools.product(rb.region(data)[TARGET], rb.region(data)[TAU])]
    for rate in ROBUSTNESS_RATES:
        reproduced = sum(n for pair, n in robust["rates"][str(rate)]["by_refill"].items() if pair in old)
        if reproduced != p2i2x["scan"]["rates"][str(rate)]["survives"]:
            raise AssertionError(f"rate {rate}: the certified refill pairs give {reproduced}, not P2I-2X's count")
    say("crystalloid")
    keys = {k: n for rate in ("5.0", "6.0") for k, n in robust["rates"][rate]["survivor_keys"].items()}
    blood = probes(data, keys)
    points = grid()
    filtered = crystalloid_filter(rows, points, blood)
    counts = crystalloid_counts(filtered, blood)
    representatives = crystalloid_representatives(filtered, counts["survivors"]["primary"])
    say("trajectories")
    moved = trajectories(data, filtered, representatives)
    return {"freeze_digest": freeze_digest(), "decided": DECIDED, "revision": REVISION,
            "records": {"P2I-2V-R": data["freeze_digest"], "P2I-2X": p2i2x["freeze_digest"]},
            "policy": POLICY, "rate_record": {"TESTED_VIABLE_RATE_REGION": list(TESTED_VIABLE_RATE_REGION),
                                              "FIRST_TESTED_NONVIABLE_RATE": FIRST_TESTED_NONVIABLE_RATE},
            "robustness_design": robustness_design(data), "robustness": robust,
            "grid": points, "probes": {k: list(v) for k, v in blood.items()}, "crystalloid": filtered,
            "counts": counts, "edges": {"primary": surface_edges(counts["survivors"]["primary"]),
                                        "robust": surface_edges(counts["survivors"]["robust"])},
            "representatives": representatives, "trajectories": moved, "rows_computed": rows.computed,
            "contradictions": be.contradictions(rows.table),
            "unreadable_rows": {f"{c}|{s}": sum(1 for r in rows.table[c][s].values() if be.UNREADABLE in r)
                                for c in CASES for s in be.SOURCES}}


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
        print(json.dumps({"robustness": robustness_design(), "grid": grid()}, indent=1, default=str))
        return 0
    if args.run:
        if not args.out:
            parser.error("--run needs --out (a directory outside the repository)")
        out = Path(args.out)
        if out.resolve().is_relative_to(ROOT):
            parser.error("--out must be outside the repository")
        out.mkdir(parents=True, exist_ok=True)
        result = run(lambda step: print(step, flush=True))
        (out / "blood_fluid_calibration.json").write_text(json.dumps(result, indent=1, sort_keys=True, default=str),
                                                          encoding="utf-8")
        print(out / "blood_fluid_calibration.json")
        return 0
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
