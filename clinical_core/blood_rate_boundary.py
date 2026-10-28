"""P2I-2X: close the case-truth and domain bounds of the shared-blood region and densify the common bleed rate.

    python -m clinical_core.blood_rate_boundary --digest
    python -m clinical_core.blood_rate_boundary --design
    python -m clinical_core.blood_rate_boundary --run --out <directory outside the repository>

Shadow, offline and read-only. The faculty constraints are P2I-2V-R's, byte for byte: every reading is a frozen
``blood_constraints`` row function (through P2I-2W's frozen ``_compute``) and every verdict its frozen ``passes``.
Nothing is fitted, interpolated, selected or approved. The faculty decided (2026-10-28):

- Arrival preload position must stay compatible with the authored arrival phenotype (POCUS). A position outside the
  case's committed candidate band, which the POCUS lines ground, is REJECTED_BY_CASE_TRUTH_COMPATIBILITY: no band is
  tightened and no exact position is inferred from POCUS (``case_truth``).
- Only the common bleed rate is densified between 5 and 10, at the predeclared 6, 7, 8 and 9 (``RATES``), over the
  surviving P2I-2V-R region at its case-compatible positions; the case band's other positions are checked for each
  case alone. No other hidden parameter takes a new value.
- The refill target's upper edge at 1.0 is its domain bound (``derived``: 0 <= share <= 1), not a grid edge.
- Boundary status adds DOMAIN_LOWER_BOUND, DOMAIN_UPPER_BOUND and CASE_TRUTH_BOUND, apart from identifiability.

Exact pre-filtering: a constraint whose reading does not depend on the bleed rate (its table keys exclude it) has
the same verdict at every rate, so a candidate that fails one is rejected at every rate without simulating the
rate; this is recorded apart from the rejections simulated per rate. The rate points, the design, the case-truth
rule, the taxonomy and the policy were frozen and committed before any new rate was evaluated (``freeze_digest``).
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
from . import gi_reference, lactate_slice

DECIDED = "2026-10-28"
REVISION = "P2I-2X"
ROOT = bc.ROOT
CASES = bc.CASES
P2I2W_RECORD = ROOT / "docs" / "revision" / "P2I2W_blood_extension.json"
P2I2W_DIGEST = "5257b2336caa76819bdc1f5f3a946dc440dbff88c9e101d9ed25c38287772f6e"

# Case-truth compatibility of the arrival position (faculty decision 1) ------------------------------------------

REJECTED_BY_CASE_TRUTH = "REJECTED_BY_CASE_TRUTH_COMPATIBILITY"
POCUS_ITEMS = ("pocus_ivc", "pocus_lv")


def case_truth_band(case: str) -> tuple[float, float]:
    """The committed candidate band of the arrival position (gi_reference.preload_band), which the case's POCUS lines
    ground. It is candidate inference, not a faculty-approved value, and is applied as committed: not tightened."""
    band = gi_reference.case_bands(case)["preload_fraction"]
    return band.lower, band.upper


def case_truth_compatible(case: str, position: float) -> bool:
    lower, upper = case_truth_band(case)
    return lower - 1e-12 <= position <= upper + 1e-12


def case_truth_evidence(case: str) -> dict:
    """What grounds the bound: A. the repository truth (the POCUS lines, with their source), B. the committed
    candidate band and the euvolaemic reference, each with its rationale and status."""
    truth = [{"item": entry.item, "value": entry.value, "source": entry.source, "snippet": entry.snippet,
              "inference": entry.note} for entry in gi_reference.INVENTORY
             if entry.case == case and entry.item in POCUS_ITEMS]
    bands = gi_reference.case_bands(case)
    band, reference = bands["preload_fraction"], bands["reference_preload_fraction"]
    return {"repository_truth": truth,
            "candidate_band": {"lower": band.lower, "midpoint": band.midpoint, "upper": band.upper,
                               "rationale": band.rationale, "status": "CANDIDATE INFERENCE (gi_reference, B)"},
            "euvolaemic_reference": {"lower": reference.lower, "upper": reference.upper,
                                     "rationale": reference.rationale},
            "faculty_decision_required": "preload_fraction" in gi_reference.FACULTY_DECISIONS}


# The rate points (faculty decision 3) -----------------------------------------------------------------------------

#: Predeclared before evaluation: 5 (survives in P2I-2V-R) and 10 (fails in P2I-2W) are re-read on the same region
#: as anchors of the scan; 6, 7, 8 and 9 are new. Same unit and meaning as the candidate rate (mL-eq/min).
RATES = (5.0, 6.0, 7.0, 8.0, 9.0, 10.0)
NEW_RATES = (6.0, 7.0, 8.0, 9.0)
#: Constraints whose reading does not depend on the bleed rate (exact pre-filter) and those that do, in the order
#: they are evaluated (the cheapest reading first; a case stops at its first readable failure).
RATE_INDEPENDENT = tuple(name for name in bc.CONSTRAINTS if bc.BLEED not in bc._depends(name))
RATE_DEPENDENT = ("U-OUT", "U-HB", "FD-BLD-08", "FD-BLD-06")
#: The case band's other positions, checked for each case alone at every rate (targeted pairs rate x position).
OTHER_POSITIONS = ("lower", "midpoint")
POLICY = ("Every reading is a frozen blood_constraints row function and every verdict its frozen passes(), primary "
          "reading only. A constraint whose table keys exclude the bleed rate is evaluated once and rejects at every "
          "rate (exact pre-filter, reported apart). Then each case is read in the order U-OUT, U-HB, FD-BLD-08, "
          "FD-BLD-06 and stops at its first readable failure; an UNREADABLE reading (its frozen function raises) "
          "never counts as a failure or as a bound. A candidate SURVIVES when both cases meet every constraint, is "
          "REJECTED when either case fails one, and is UNREADABLE otherwise. Positions outside the case band are "
          "REJECTED_BY_CASE_TRUTH_COMPATIBILITY without simulation. FD-BLD-03 is not read.")


def region(data: dict | None = None) -> dict:
    """The surviving P2I-2V-R region: each shared coordinate keeps the values that survive there; the positions
    are the case-compatible ones that survive (one per case)."""
    data = data or be.record()
    base = be.base_box(data)
    return {label: values for label, values in base.items() if label != be.COMMON}


def design(data: dict | None = None) -> dict:
    data = data or be.record()
    values = region(data)
    shared = math.prod(len(values[name]) for name in bc.SHARED)
    positions = {case: values[be.POSITION[case]] for case in CASES}
    others = {case: [be.positions(case)[label] for label in OTHER_POSITIONS] for case in CASES}
    return {"rates": list(RATES), "new_rates": list(NEW_RATES), "rate_independent": list(RATE_INDEPENDENT),
            "rate_dependent": list(RATE_DEPENDENT), "shared_combinations": shared,
            "positions": {case: list(positions[case]) for case in CASES},
            "other_positions": {case: others[case] for case in CASES},
            "joint_candidates_per_rate": shared * math.prod(len(positions[case]) for case in CASES),
            "case_candidates_per_rate_and_other_position": shared}


# Edge taxonomy (faculty decision 5) -------------------------------------------------------------------------------

DOMAIN_LOWER, DOMAIN_UPPER, CASE_TRUTH_BOUND = "DOMAIN_LOWER_BOUND", "DOMAIN_UPPER_BOUND", "CASE_TRUTH_BOUND"
TAXONOMY = (be.INTERIOR, be.OPEN_LOWER, be.OPEN_UPPER, be.OPEN_BOTH, DOMAIN_LOWER, DOMAIN_UPPER, CASE_TRUTH_BOUND)
#: The exact mathematical domain the core enforces (or the definition states) for the parameters that have a
#: finite one; the others are only positive.
DOMAIN = {"plasma_refill_target_share": (0.0, 1.0, "derived.CoreProfile: 0 <= share of the shed volume <= 1"),
          "crystalloid_transient_share": (0.0, 1.0, "fluids.Crystalloid: 0 <= transient share <= 1"),
          bc.POS: (0.0, 1.0, "a position on the preload curve (0-1)")}


def side(explored: list, left: list, which: str, parameter: str, case: str | None) -> str:
    """One side of the surviving range: CONSTRAINED (the next explored value is rejected by a faculty constraint),
    OPEN (the extreme explored value survives), DOMAIN (it survives and is the domain limit) or CASE_TRUTH (the
    values beyond it are excluded by case truth)."""
    ordered = sorted(explored)
    extreme = ordered[-1] if which == "upper" else ordered[0]
    limit = DOMAIN.get(parameter)
    if parameter == bc.POS and case:
        lower, upper = case_truth_band(case)
        beyond = [v for v in ordered if (v > max(left) if which == "upper" else v < min(left))]
        bound = upper if which == "upper" else lower
        if left and math.isclose(max(left) if which == "upper" else min(left), bound) and beyond and all(
                not case_truth_compatible(case, v) for v in beyond):
            return "CASE_TRUTH"
    if extreme in left:
        if limit and math.isclose(extreme, limit[1] if which == "upper" else limit[0]):
            return "DOMAIN"
        return "OPEN"
    return "CONSTRAINED"


def edge(lower: str, upper: str) -> str:
    names = {("lower", "OPEN"): be.OPEN_LOWER, ("upper", "OPEN"): be.OPEN_UPPER, ("lower", "DOMAIN"): DOMAIN_LOWER,
             ("upper", "DOMAIN"): DOMAIN_UPPER, ("lower", "CASE_TRUTH"): CASE_TRUTH_BOUND,
             ("upper", "CASE_TRUTH"): CASE_TRUTH_BOUND}
    if lower == upper == "OPEN":
        return be.OPEN_BOTH
    parts = [names[(which, state)] for which, state in (("lower", lower), ("upper", upper)) if state != "CONSTRAINED"]
    return " + ".join(dict.fromkeys(parts)) or be.INTERIOR


# Evaluation ---------------------------------------------------------------------------------------------------------

class Rows:
    """The frozen readings, computed on demand once each (P2I-2W's frozen _compute: the same row functions and
    cross-checks as blood_constraints.tables)."""

    def __init__(self):
        self.table = {case: {source: {} for source in be.SOURCES} for case in CASES}
        self.computed = 0

    def ensure(self, case: str, name: str, values: dict) -> None:
        sources = [bc._source(name, None)]
        if sources[0] == "acute":
            sources = [f"acute_{int(bc.ACUTE_LOSS_ML)}", f"acute_off_{int(bc.ACUTE_LOSS_ML)}"]
        for source in sources:
            key = tuple(values[n] for n in be._keys(source))
            if key not in self.table[case][source]:
                self.table[case][source][key] = be._compute((case, source, key))[1]
                self.computed += 1

    def verdict(self, case: str, name: str, values: dict):
        self.ensure(case, name, values)
        return be.verdict(self.table, case, name, values)


def _values(combination: dict, case: str, rate: float, position: float) -> dict:
    values = {name: combination[name] for name in bc.SHARED}
    values[bc.BLEED], values[bc.POS] = rate, position
    return values


def _case(rows: Rows, case: str, values: dict, cache: dict) -> tuple[str, str | None]:
    """('pass' | 'fail' | 'unreadable', first readable failure) for one case, rate-dependent constraints only."""
    unreadable = False
    for name in RATE_DEPENDENT:
        key = (name, tuple(values[n] for n in bc._depends(name)))
        if key not in cache:
            cache[key] = rows.verdict(case, name, values)
        if cache[key] is False:
            return "fail", name
        if cache[key] is None:
            unreadable = True
    return ("unreadable" if unreadable else "pass"), None


def _independent(rows: Rows, case: str, values: dict, cache: dict) -> str | None:
    """The first rate-independent constraint the case fails (None: it meets them all). Never UNREADABLE in this
    region (checked)."""
    for name in RATE_INDEPENDENT:
        key = (name, tuple(values[n] for n in bc._depends(name)))
        if key not in cache:
            cache[key] = rows.verdict(case, name, values)
        if cache[key] is None:
            raise AssertionError(f"{case}: a rate-independent reading is unreadable at {values}")
        if cache[key] is False:
            return name
    return None


def _uout_detail(rows: Rows, case: str, values: dict) -> list:
    row, _ = bc._row(rows.table, case, "U-OUT", values, None)
    return be._detail("U-OUT", case, row)


def scan(rows: Rows, data: dict) -> dict:
    """The primary scan: one common rate for both cases, at the case-compatible surviving positions."""
    values = region(data)
    positions = {case: values[be.POSITION[case]][0] for case in CASES}
    caches = {case: {} for case in CASES}
    shared = [dict(zip(bc.SHARED, combination)) for combination in itertools.product(*(values[n] for n in bc.SHARED))]
    prefilter, first = [], {name: 0 for name in RATE_INDEPENDENT}
    for combination in shared:
        failing = [_independent(rows, case, _values(combination, case, RATES[0], positions[case]), caches[case])
                   for case in CASES]
        failing = [name for name in failing if name]
        if failing:
            first[failing[0]] += 1
        else:
            prefilter.append(combination)
    out = {"positions": positions, "candidates": len(shared), "rate_independent_rejected": len(shared) - len(prefilter),
           "rate_independent_first_failure": first, "rates": {}}
    for rate in RATES:
        item = {"candidates": len(shared), "simulated": len(prefilter), "survives": 0, "rejected": 0, "unreadable": 0,
                "u_out_fail": {case: 0 for case in CASES}, "first_failure": {case: {} for case in CASES},
                "alone": {case: 0 for case in CASES}, "alone_unreadable": {case: 0 for case in CASES},
                "u_out_detail": {case: {} for case in CASES}, "survivor_output": {m: [] for m in bc.MINUTES_OUTPUT},
                "survivor_hb_fall": {m: [] for m in bc.MINUTES_HB}, "marginal": {n: {} for n in bc.SHARED}}
        seen_detail = {case: set() for case in CASES}
        for combination in prefilter:
            results = {}
            for case in CASES:
                case_values = _values(combination, case, rate, positions[case])
                state, name = _case(rows, case, case_values, caches[case])
                results[case] = state
                if name:
                    item["first_failure"][case][name] = item["first_failure"][case].get(name, 0) + 1
                if name == "U-OUT":
                    item["u_out_fail"][case] += 1
                    key = tuple(case_values[n] for n in bc._depends("U-OUT"))
                    if key not in seen_detail[case]:
                        seen_detail[case].add(key)
                        for where in _uout_detail(rows, case, case_values):
                            item["u_out_detail"][case][where] = item["u_out_detail"][case].get(where, 0) + 1
                item["alone"][case] += state == "pass"
                item["alone_unreadable"][case] += state == "unreadable"
            if "fail" in results.values():
                item["rejected"] += 1
            elif "unreadable" in results.values():
                item["unreadable"] += 1
            else:
                item["survives"] += 1
                for n in bc.SHARED:
                    item["marginal"][n][str(combination[n])] = item["marginal"][n].get(str(combination[n]), 0) + 1
                for case in CASES:
                    case_values = _values(combination, case, rate, positions[case])
                    out_row, _ = bc._row(rows.table, case, "U-OUT", case_values, None)
                    hb_row, _ = bc._row(rows.table, case, "U-HB", case_values, None)
                    for m in bc.MINUTES_OUTPUT:
                        item["survivor_output"][m].append(out_row["output"][m])
                    for m in bc.MINUTES_HB:
                        item["survivor_hb_fall"][m].append(hb_row["fall"][m])
        item["rejected"] += len(shared) - len(prefilter)
        item["survivor_output"] = {m: bc._envelope(v) for m, v in item["survivor_output"].items()}
        item["survivor_hb_fall"] = {m: bc._envelope(v) for m, v in item["survivor_hb_fall"].items()}
        out["rates"][str(rate)] = item
    return out


def targeted(rows: Rows, data: dict) -> dict:
    """Rate x the case band's other positions, for each case alone (a joint candidate needs both cases)."""
    values = region(data)
    out = {}
    for case in CASES:
        cache = {}
        for label in OTHER_POSITIONS:
            position = be.positions(case)[label]
            entry = {"position": position, "candidates_per_rate": 0, "rate_independent_rejected": 0, "rates": {}}
            passing = []
            for combination in itertools.product(*(values[n] for n in bc.SHARED)):
                combination = dict(zip(bc.SHARED, combination))
                entry["candidates_per_rate"] += 1
                if _independent(rows, case, _values(combination, case, RATES[0], position), cache):
                    entry["rate_independent_rejected"] += 1
                else:
                    passing.append(combination)
            for rate in RATES:
                counts = {"pass": 0, "fail": 0, "unreadable": 0, "u_out_fail": 0}
                for combination in passing:
                    state, name = _case(rows, case, _values(combination, case, rate, position), cache)
                    counts[state] += 1
                    counts["u_out_fail"] += name == "U-OUT"
                entry["rates"][str(rate)] = counts
            out[f"{case}|{label}"] = entry
    return out


def representatives(data: dict, rows: Rows) -> dict:
    """The three P2I-2V-R representatives moved to each rate (only the rate changes): their untreated rows."""
    out = {}
    for rate in RATES:
        out[str(rate)] = {}
        for tag, item in data["representatives"].items():
            entry = {"rows": {}, "verdicts": {}}
            for case in CASES:
                values = {**item["values"][case], bc.BLEED: rate}
                values[bc.POS] = be.positions(case)[values[bc.POS]] if isinstance(values[bc.POS], str) else values[
                    bc.POS]
                anchors, profile, _, states, stop = bc._run(case, values, "untreated", 120)
                entry["rows"][case] = {"stop": stop, "rows": [bc._reading(states[m], anchors, profile)
                                                              for m in (0, 30, 60, 120) if m < len(states)]}
                entry["verdicts"][case] = {name: rows.verdict(case, name, values) for name in bc.CONSTRAINTS}
            out[str(rate)][tag] = entry
    return out


def interval(scanned: dict) -> dict:
    counts = {float(rate): item["survives"] for rate, item in scanned["rates"].items()}
    surviving = [rate for rate in RATES if counts[rate] > 0]
    empty = [rate for rate in RATES if counts[rate] == 0]
    highest, lowest = (max(surviving) if surviving else None), (min(empty) if empty else None)
    adjacent = (highest is not None and lowest is not None and lowest > highest
                and RATES.index(lowest) == RATES.index(highest) + 1)
    monotone = all(counts[a] >= counts[b] for a, b in zip(RATES, RATES[1:]))
    return {"label": "FACULTY-CONSTRAINED BLEED-RATE CANDIDATE INTERVAL", "counts": {str(k): v for k, v in counts.items()},
            "highest_with_survivor": highest, "lowest_without_survivor": lowest,
            "boundary_between_adjacent_tested_rates": adjacent, "monotone_survivor_counts": monotone}


def p2i2w_case_truth(record: dict) -> dict:
    """P2I-2W's boxes whose fixed positions are outside a case band: their survivors are re-read as
    REJECTED_BY_CASE_TRUTH_COMPATIBILITY (no simulation)."""
    out = {}
    for name, stats in record["boxes"].items():
        fixed = stats["fixed"]
        outside = [case for case in CASES if be.POSITION[case] in fixed
                   and not case_truth_compatible(case, fixed[be.POSITION[case]])]
        if outside:
            out[name] = {"outside": outside, "survives": stats["survives"],
                         "alone": {case: stats["alone"][case] for case in outside}}
    return out


def edges(p2i2vr: dict, p2i2w: dict, scanned: dict) -> dict:
    """Every coordinate over P2I-2V-R, P2I-2W (boxes inside the case bands only) and this scan: explored and
    surviving values, the frozen identifiability class and the extended boundary status, side by side."""
    excluded = set(p2i2w_case_truth(p2i2w))
    out = {}
    for label in be.COORDS:
        parameter, case = be._parameter(label)
        explored = set(be.explored(p2i2vr, label)) | set(p2i2w["edges"][label]["explored"])
        left = set(be.surviving(p2i2vr, label))
        for name, stats in p2i2w["boxes"].items():
            if name not in excluded:
                left |= {float(v) for v, n in stats["marginal"][label].items() if n > 0}
        if label == be.COMMON:
            explored |= set(RATES)
            left |= {rate for rate in RATES if scanned["rates"][str(rate)]["survives"]}
        elif parameter != bc.POS:
            for item in scanned["rates"].values():
                left |= {float(v) for v, n in item["marginal"][parameter].items() if n > 0}
        explored, left = sorted(explored), sorted(left)
        compatible = [v for v in explored if case is None or parameter != bc.POS or case_truth_compatible(case, v)]
        lower = side(explored, left, "lower", parameter, case) if left else None
        upper = side(explored, left, "upper", parameter, case) if left else None
        cls = be.identifiability(parameter, compatible, left)
        status = edge(lower, upper) if left else None
        out[label] = {"explored": explored, "case_compatible": compatible, "left": left, "lower_side": lower,
                      "upper_side": upper, "class": cls, "edge": status,
                      "identified": cls == bc.WELL and status == be.INTERIOR}
    for name, why in bc.STRUCTURAL.items():
        out.setdefault(name, {"class": bc.SEPARATELY, "edge": None, "why": why})
    return out


# Freeze ---------------------------------------------------------------------------------------------------------------

#: Render-only modules downstream of every numerical artifact (lactate_slice.DOWNSTREAM_REPORTS): outside this
#: freeze, each with its own generated-document test.
DOWNSTREAM_REPORTS = lactate_slice.DOWNSTREAM_REPORTS


def freeze_sources() -> dict[str, str]:
    out = {}
    for path in sorted((ROOT / "clinical_core").rglob("*.py")):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in DOWNSTREAM_REPORTS:
            out[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def freeze_digest() -> str:
    data = be.record()
    text = json.dumps({"revision": REVISION, "records": {
        "P2I-2V-R": hashlib.sha256(be.P2I2VR_RECORD.read_bytes()).hexdigest(),
        "P2I-2W": hashlib.sha256(P2I2W_RECORD.read_bytes()).hexdigest()},
        "rates": RATES, "new_rates": NEW_RATES, "rate_independent": RATE_INDEPENDENT, "rate_dependent": RATE_DEPENDENT,
        "other_positions": OTHER_POSITIONS, "design": design(data), "policy": POLICY, "taxonomy": TAXONOMY,
        "domain": DOMAIN, "case_truth": {case: case_truth_evidence(case) for case in CASES},
        "sources": freeze_sources()}, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run(progress=None) -> dict:
    p2i2vr = be.record()
    p2i2w = json.loads(P2I2W_RECORD.read_text(encoding="utf-8"))
    if p2i2vr["freeze_digest"] != be.P2I2VR_DIGEST or p2i2w["freeze_digest"] != P2I2W_DIGEST:
        raise AssertionError("the P2I-2V-R or P2I-2W record is not the committed one")
    rows = Rows()
    say = progress or (lambda *_: None)
    say("scan")
    scanned = scan(rows, p2i2vr)
    expected = p2i2vr["primary"]["marginal"][be.COMMON]["5.0"]
    if scanned["rates"]["5.0"]["survives"] != expected or scanned["rates"]["10.0"]["survives"] != 0:
        raise AssertionError("the scan does not reproduce P2I-2V-R at rate 5 or P2I-2W at rate 10")
    say("targeted")
    other = targeted(rows, p2i2vr)
    say("representatives")
    moved = representatives(p2i2vr, rows)
    unreadable = {f"{case}|{source}": sum(1 for row in rows.table[case][source].values() if be.UNREADABLE in row)
                  for case in CASES for source in be.SOURCES}
    return {"freeze_digest": freeze_digest(), "decided": DECIDED, "revision": REVISION,
            "records": {"P2I-2V-R": p2i2vr["freeze_digest"], "P2I-2W": p2i2w["freeze_digest"]},
            "policy": POLICY, "design": design(p2i2vr),
            "case_truth": {case: {**case_truth_evidence(case), "band": list(case_truth_band(case))} for case in CASES},
            "p2i2w_case_truth": p2i2w_case_truth(p2i2w), "scan": scanned, "interval": interval(scanned),
            "targeted": other, "representatives": moved, "edges": edges(p2i2vr, p2i2w, scanned),
            "rows_computed": rows.computed, "contradictions": be.contradictions(rows.table),
            "unreadable_rows": unreadable}


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
        print(json.dumps({"design": design(), "case_truth": {case: case_truth_band(case) for case in CASES}},
                         indent=1, default=str))
        return 0
    if args.run:
        if not args.out:
            parser.error("--run needs --out (a directory outside the repository)")
        out = Path(args.out)
        if out.resolve().is_relative_to(ROOT):
            parser.error("--out must be outside the repository")
        out.mkdir(parents=True, exist_ok=True)
        result = run(lambda step: print(step, flush=True))
        (out / "blood_rate_boundary.json").write_text(json.dumps(result, indent=1, sort_keys=True, default=str),
                                                      encoding="utf-8")
        print(out / "blood_rate_boundary.json")
        return 0
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
