"""P2I-2W: a limited extension of the open grid edges of the P2I-2V-R shared-blood region (shadow only).

    python -m clinical_core.blood_extension --digest
    python -m clinical_core.blood_extension --design
    python -m clinical_core.blood_extension --run --out <directory outside the repository>

Shadow, offline and read-only. The faculty constraints are exactly P2I-2V-R's: this module imports the frozen
``blood_constraints`` and calls its row functions and ``passes`` unchanged; it adds no constraint, changes no
reading, fits nothing and approves nothing. The faculty authorized (2026-10-27) a LIMITED boundary extension to
learn whether the parameters at the upper grid edge are bounded by the constraints or only truncated by the grid.

- Which dimensions: exactly those the committed P2I-2V-R report flagged as open at a grid edge (``OPEN_EDGES``,
  checked against the record by a test). Dimensions whose surviving values are interior are not extended, and
  neither are those the report did not flag.
- Which values: one and two steps beyond the open edge, continuing the dimension's own spacing (constant
  difference or constant ratio over its three explored values, ``continuation``). A point outside the
  parameter's domain is dropped, never moved. A spacing that is neither, or both, is AMBIGUOUS: that dimension
  is not extended and the ambiguity is reported for a faculty decision.
- Which combinations: a sparse design around the surviving region (``design``), never a full Cartesian sweep:
  the surviving box (the frozen filter's survivors must be reproduced), every extension point one at a time,
  every pair of extended dimensions that can interact, and the corner of all first steps. Every other dimension
  keeps the values that survive in P2I-2V-R. The common bleed rate is the primary reading; each case alone is
  the case-specific sensitivity.

The extension points, the design and the evaluation policy were frozen and committed before any extended
candidate was evaluated (``freeze_digest``). Grid truncation is reported as an edge status
(``edge_status``), orthogonal to the frozen identifiability classes: a single surviving value at the edge of
the explored grid is not identified.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path

from . import blood_constraints as bc
from . import gi_reference

DECIDED = "2026-10-27"
REVISION = "P2I-2W"
ROOT = bc.ROOT
#: The committed P2I-2V-R record (freeze a9ab10d8...): the region, its survivors and its identifiability.
P2I2VR_RECORD = ROOT / "docs" / "revision" / "P2I2VR_blood_filter.json"
P2I2VR_DIGEST = "a9ab10d8d809070e5e76bcb4557525924dcb918fbd86d9b2a62393687d53c893"
CASES = bc.CASES
COMMON = f"{bc.BLEED}|common"
POSITION = {case: f"{bc.POS}|{case}" for case in CASES}
#: The candidate's coordinates: one common bleed rate (the primary reading), each case's arrival position, and
#: the shared hidden parameters.
COORDS = (COMMON, *POSITION.values(), *bc.SHARED)

# Edge status (P2I-2W-3): orthogonal to the identifiability classes --------------------------------------------

INTERIOR, OPEN_LOWER, OPEN_UPPER, OPEN_BOTH = ("INTERIOR", "OPEN_LOWER_GRID_EDGE", "OPEN_UPPER_GRID_EDGE",
                                               "OPEN_BOTH_GRID_EDGES")
EDGE_STATUSES = (INTERIOR, OPEN_LOWER, OPEN_UPPER, OPEN_BOTH)


def edge_status(explored, left) -> str | None:
    """Whether the surviving values reach the lowest or highest explored value. INTERIOR: both explored edges
    are rejected, so the constraints bound it on both sides within the design; OPEN_*: the design has not shown
    a bound on that side. None: nothing survives."""
    if not left:
        return None
    ordered = sorted(explored)
    low, high = ordered[0] in left, ordered[-1] in left
    return OPEN_BOTH if low and high else OPEN_LOWER if low else OPEN_UPPER if high else INTERIOR


def identifiability(parameter: str, explored, left) -> str | None:
    """The frozen P2I-2V-R class rule (``blood_constraints.classify``), without its grid-edge flag: grid
    truncation is the edge status, not a class."""
    if parameter in bc.STRUCTURAL:
        return bc.SEPARATELY
    if not left:
        return None
    return bc.WELL if len(left) == 1 else bc.PARTIAL if len(left) < len(explored) else bc.POOR


# What the committed P2I-2V-R record says ---------------------------------------------------------------------

def record() -> dict:
    return json.loads(P2I2VR_RECORD.read_text(encoding="utf-8"))


def positions(case: str) -> dict:
    band = gi_reference.case_bands(case)["preload_fraction"]
    return {"lower": band.lower, "midpoint": band.midpoint, "upper": band.upper}


def _parameter(label: str) -> tuple[str, str | None]:
    parameter, _, case = label.partition("|")
    return parameter, (case if case in CASES else None)


def _numeric(label: str, value):
    parameter, case = _parameter(label)
    if parameter == bc.POS:
        return positions(case)[value] if isinstance(value, str) else value
    return float(value)


def explored(data: dict, label: str) -> list:
    parameter, _ = _parameter(label)
    return [_numeric(label, value) for value in data["region"][parameter]]


def surviving(data: dict, label: str) -> list:
    """The explored values with at least one joint survivor in the P2I-2V-R primary (common bleed rate)."""
    parameter, _ = _parameter(label)
    marginal = data["primary"]["marginal"][label]
    return [value for value, raw in zip(explored(data, label), data["region"][parameter]) if marginal[str(raw)] > 0]


def reported_open_edges(data: dict) -> dict:
    """The dimensions the committed report flagged as open at a grid edge, by its own rule (P2I-2V-R §5.5): a
    PARTIALLY_CONSTRAINED class whose surviving values reach an explored edge, or a single surviving value at an
    explored edge (``grid_edge``). Structural classes are not dimensions of the grid."""
    out = {}
    for label, item in data["identifiability"]["classes"].items():
        if item["class"] == bc.SEPARATELY or not item.get("left"):
            continue
        parameter, _ = _parameter(label)
        raw = [str(value) for value in data["region"][parameter]]
        low, high = item["left"][0] == raw[0], item["left"][-1] == raw[-1]
        if item.get("grid_edge") or (item["class"] == bc.PARTIAL and (low or high)):
            out[label] = "both" if low and high else "lower" if low else "upper"
    return out


#: Declared from the committed report (a test re-derives it from the record): every flagged dimension is open on
#: its upper side only. The POORLY_IDENTIFIED dimensions keep every explored value, so they reach both edges, but
#: the report did not flag them and the faculty did not authorize them: they are not extended (reported).
OPEN_EDGES = {COMMON: "upper", "crystalloid_effective_ml_per_ml": "upper", "plasma_refill_target_share": "upper",
              "plasma_refill_tau_min": "upper", POSITION["gi_bleed_57m"]: "upper", POSITION["gi_bleed_72f"]: "upper"}

# The extension rule (P2I-2W-1) --------------------------------------------------------------------------------

#: The domain of each parameter that can be extended: a continuation point outside it is dropped, never moved.
DOMAIN = {bc.BLEED: (0.0, math.inf, "a bleed rate (mL-eq/min)"),
          "plasma_refill_target_share": (0.0, 1.0, "a share of what was lost"),
          "plasma_refill_tau_min": (0.0, math.inf, "a time constant (min)"),
          bc.POS: (0.0, 1.0, "a position on the preload curve (0-1)"),
          "crystalloid_effective_ml_per_ml": (0.0, 1.0, "a share of the volume infused")}
#: One and two steps beyond the open edge, both evaluated whatever the first one shows.
STEPS = (1, 2)
ARITHMETIC, GEOMETRIC, AMBIGUOUS = "ARITHMETIC", "GEOMETRIC", "AMBIGUOUS"
RULE = ("For each open dimension, take its three explored values. If they have a constant difference and not a "
        "constant ratio, continue by that difference; if a constant ratio and not a constant difference, by that "
        "ratio; otherwise the continuation is AMBIGUOUS and the dimension is not extended. Continue one and two "
        "steps beyond the open edge only. A point outside the parameter's domain is dropped, not moved. The rule "
        "reads only the explored values, never a count.")


def spacing(values) -> tuple[str, float | None]:
    a, b, c = sorted(values)
    arithmetic = math.isclose(b - a, c - b, rel_tol=1e-9, abs_tol=1e-12)
    geometric = a > 0 and math.isclose(b / a, c / b, rel_tol=1e-9)
    if arithmetic and not geometric:
        return ARITHMETIC, (c - a) / 2
    if geometric and not arithmetic:
        return GEOMETRIC, math.sqrt(c / a)
    return AMBIGUOUS, None


def continuation(values, side: str, parameter: str) -> dict:
    kind, step = spacing(values)
    ordered = sorted(values)
    low, high, domain = DOMAIN[parameter]
    if kind == AMBIGUOUS:
        a, b, c = ordered
        edge, last_difference, last_ratio = (c, c - b, c / b) if side == "upper" else (a, b - a, b / a)
        sign = 1 if side == "upper" else -1
        return {"spacing": AMBIGUOUS, "step": None, "points": [], "dropped": [],
                "why": "the explored values have neither a constant difference nor a constant ratio "
                       f"(differences {b - a:g} and {c - b:g}; ratios {b / a:g} and {c / b:g})",
                "not_evaluated": {"by the last difference": [round(edge + sign * k * last_difference, 10)
                                                             for k in STEPS],
                                  "by the last ratio": [round(edge * last_ratio ** (sign * k), 10) for k in STEPS]}}
    edge = ordered[-1] if side == "upper" else ordered[0]
    sign = 1 if side == "upper" else -1
    points = [round(edge + sign * k * step, 10) if kind == ARITHMETIC else round(edge * step ** (sign * k), 10)
              for k in STEPS]
    inside = [p for p in points if low < p <= high]
    return {"spacing": kind, "step": round(step, 10), "points": inside, "dropped": [p for p in points if p not in inside],
            "domain": domain}


def extension(data: dict | None = None) -> dict:
    """The predeclared extension of every open dimension (no candidate is read)."""
    data = data or record()
    out = {}
    for label, side in OPEN_EDGES.items():
        parameter, case = _parameter(label)
        values = explored(data, label)
        out[label] = {"parameter": parameter, "case": case, "side": side, "explored": values,
                      "surviving": surviving(data, label), **continuation(values, side, parameter)}
    return out


# The sparse design (P2I-2W-2) ---------------------------------------------------------------------------------

def _reads(parameter: str) -> set:
    return {name for name in bc.CONSTRAINTS if parameter in bc._depends(name)}


def pair_reason(a: str, b: str) -> str:
    """Why two extended dimensions are combined: the constraints that read both (so they can interact), or, for
    the two arrival positions (each case is read alone), the joint question of both cases arriving higher."""
    (pa, ca), (pb, cb) = _parameter(a), _parameter(b)
    if ca and cb and ca != cb:
        return "no constraint reads both (each case is read alone); the joint survivor needs both cases at once"
    shared = sorted(_reads(pa) & _reads(pb))
    return "both read by " + ", ".join(shared) if shared else ""


def extended(ext: dict | None = None) -> dict:
    ext = ext or extension()
    return {label: item["points"] for label, item in ext.items() if item["points"]}


def base_box(data: dict | None = None) -> dict:
    data = data or record()
    return {label: tuple(surviving(data, label)) for label in COORDS}


def design(data: dict | None = None) -> list[dict]:
    """The boxes, in order: the surviving box (it must reproduce the frozen survivors), each extension point
    alone, each pair of extended dimensions that can interact (every combination of their points), and the corner
    of all first steps. The boxes are disjoint: the set of extended dimensions names the box."""
    data = data or record()
    points = extended(extension(data))
    base = base_box(data)
    boxes = [{"name": "base", "kind": "base", "fixed": {}}]
    for label, values in points.items():
        boxes += [{"name": f"{label}={value:g}", "kind": "one", "fixed": {label: value}} for value in values]
    for a, b in itertools.combinations(points, 2):
        reason = pair_reason(a, b)
        if not reason:
            continue
        for x, y in itertools.product(points[a], points[b]):
            boxes.append({"name": f"{a}={x:g} & {b}={y:g}", "kind": "pair", "fixed": {a: x, b: y}, "why": reason})
    corner = {label: values[0] for label, values in points.items()}
    boxes.append({"name": "corner: every first step", "kind": "corner", "fixed": corner})
    for box in boxes:
        box["size"] = math.prod(1 if label in box["fixed"] else len(base[label]) for label in COORDS)
    return boxes


def _box_values(box: dict, base: dict) -> dict:
    return {label: (box["fixed"][label],) if label in box["fixed"] else base[label] for label in COORDS}


# The evaluation policy, frozen with the design -------------------------------------------------------------------

UNREADABLE = "UNREADABLE"
POLICY = ("Every reading is a frozen blood_constraints row function and every verdict its frozen passes(), primary "
          "reading only. A row whose frozen function raises (for instance because the blood reading's own "
          "haemodynamics stop) is UNREADABLE, with its message. A candidate is REJECTED when a readable constraint "
          "fails in either case, SURVIVES when every constraint is readable and met in both cases, and is "
          "UNREADABLE otherwise; UNREADABLE is reported apart and is never counted as a faculty bound. The "
          "cross-checks of blood_constraints.tables (Hb independent of the haemodynamics; the retained "
          "crystalloid independent of the bleeding, B0 and refill) are run on every extended row and any failure is "
          "reported as a contradiction. FD-BLD-03 is counted as a diagnostic only.")
SOURCES = ("untreated", "untreated_blood", "red_cells", "retained", "crystalloid", f"acute_{int(bc.ACUTE_LOSS_ML)}",
           f"acute_off_{int(bc.ACUTE_LOSS_ML)}", "stopped")


def _keys(source: str) -> tuple:
    return bc.TABLE_KEYS["acute_off" if source.startswith("acute_off") else
                         "acute" if source.startswith("acute") else source]


def _case_values(case: str, combination: dict) -> dict:
    values = {name: combination[name] for name in bc.SHARED}
    values[bc.BLEED] = combination[COMMON]
    values[bc.POS] = combination[POSITION[case]]
    return values


def rows_needed(boxes: list[dict], base: dict) -> dict:
    """Every (case, source) row key the design reads (no row is computed)."""
    out = {(case, source): set() for case in CASES for source in SOURCES}
    for box in boxes:
        values = _box_values(box, base)
        for case in CASES:
            per_case = {name: values[name] for name in bc.SHARED}
            per_case[bc.BLEED], per_case[bc.POS] = values[COMMON], values[POSITION[case]]
            for source in SOURCES:
                keys = _keys(source)
                out[(case, source)].update(itertools.product(*(per_case[name] for name in keys)))
    return out


_BASELINES: dict = {}


def _baseline(case: str, values: dict) -> list:
    """The untreated blood reading the crystalloid rows compare with (it depends only on the untreated_blood
    keys), kept while the rows that share it are built: the same states blood_constraints.tables passes."""
    key = (case, *(values[n] for n in bc.TABLE_KEYS["untreated_blood"]))
    if key not in _BASELINES:
        _BASELINES.clear()
        _BASELINES[key] = bc._run(case, values, "untreated", bc.CRYSTALLOID_MINUTES, blood=True)[3]
    return _BASELINES[key]


def _compute(task: tuple) -> tuple:
    case, source, key = task
    values = dict(zip(_keys(source), key))
    try:
        if source == "untreated":
            row = bc.untreated(case, values)
        elif source == "untreated_blood":
            row = bc.untreated_blood(case, values)
        elif source == "red_cells":
            row = bc.red_cells(case, values)
        elif source == "retained":
            row = bc.retained(case, values)
        elif source == "crystalloid":
            baseline = _baseline(case, values)
            row = {volume: bc.crystalloid(case, values, volume, baseline) for volume in bc.CRYSTALLOID_VOLUMES}
        elif source.startswith("acute_off_"):
            row = bc.acute(case, values, float(source.rsplit("_", 1)[1]), refill=False)
        elif source.startswith("acute_"):
            row = bc.acute(case, values, float(source.rsplit("_", 1)[1]))
        elif source == "stopped":
            row = bc.stopped(case, values)
        else:
            raise KeyError(source)
    except Exception as error:  # the policy: recorded as UNREADABLE, never swallowed silently
        row = {UNREADABLE: f"{type(error).__name__}: {error}"}
    return task, row


def build(needed: dict, progress=None) -> dict:
    # Sorted so that the crystalloid rows sharing a baseline are neighbours (the baseline is kept between them).
    tasks = [(case, source, key) for (case, source), keys in needed.items()
             for key in sorted(keys, key=lambda k: (repr(k[3:]), repr(k)) if source == "crystalloid" else repr(k))]
    table = {case: {source: {} for source in SOURCES} for case in CASES}
    for index, task in enumerate(tasks, 1):
        case, source, key = task
        table[case][source][key] = _compute(task)[1]
        if progress and index % 2000 == 0:
            progress(index, len(tasks))
    return table


def contradictions(table: dict) -> list:
    """blood_constraints.tables' cross-checks, on every row the design read."""
    out = []
    for case in CASES:
        blood = table[case]["untreated_blood"]
        for key, row in table[case]["untreated"].items():
            values = dict(zip(bc.TABLE_KEYS["untreated"], key))
            other = blood.get(tuple(values[n] for n in bc.TABLE_KEYS["untreated_blood"]))
            if UNREADABLE in row or other is None or UNREADABLE in other:
                continue
            for m in bc.MINUTES_HB:
                if row["hb"][m] is not None and abs(row["hb"][m] - other["hb"][m]) > 1e-9:
                    out.append({"case": case, "check": "Hb depends on the haemodynamics", "values": values})
        retained = table[case]["retained"]
        for key, row in table[case]["crystalloid"].items():
            values = dict(zip(bc.TABLE_KEYS["crystalloid"], key))
            reference = retained.get(tuple(values[n] for n in bc.BAG))
            if UNREADABLE in row or reference is None or UNREADABLE in reference:
                continue
            if (abs(row[1000.0]["retained_early"] - reference["early"]) > 1e-12
                    or any(abs(row[1000.0]["retained"][m] - reference["share"][m]) > 1e-12 for m in reference["share"])):
                out.append({"case": case, "check": "the retained crystalloid depends on more than its kinetics",
                            "values": values})
    return out


READINGS = bc.CONSTRAINTS + bc.DIAGNOSTIC_ONLY


def verdict(table: dict, case: str, name: str, values: dict):
    """True, False, or None (UNREADABLE) for one frozen constraint in one case."""
    row, off = bc._row(table, case, name, values, None)
    if UNREADABLE in row or (off is not None and UNREADABLE in off):
        return None
    return bc.passes(name, case, row, None, off)


def _detail(name: str, case: str, row: dict) -> list:
    """Where a failing U-OUT, U-HB or FD-BLD-07 reading leaves its envelope (minute and side)."""
    if name == "U-OUT":
        pairs = [(m, row["output"][m], bc.DECISIONS["untreated_output"][case][m]) for m in bc.MINUTES_OUTPUT]
    elif name == "U-HB":
        pairs = [(m, row["fall"][m], bc.DECISIONS["untreated_hb_fall"][case][m]) for m in bc.MINUTES_HB]
        if row["max_rise"] > bc.HB_RISE_TOLERANCE:
            return ["rise"]
    elif name == "FD-BLD-07":
        pairs = [(m, row["share"][m], bounds) for m, bounds in bc.DECISIONS["FD-BLD-07"]["envelopes"].items()]
    else:
        return []
    return [f"{m}:{'below' if value is None or value < low else 'above'}" for m, value, (low, high) in pairs
            if value is None or not low <= value <= high]


def evaluate_box(table: dict, box: dict, base: dict) -> dict:
    values = _box_values(box, base)
    cache = {case: {} for case in CASES}
    details = {case: {} for case in CASES}

    def case_verdicts(case: str, combination: dict) -> dict:
        per_case = _case_values(case, combination)
        out = {}
        for name in READINGS:
            row_key = tuple(per_case[n] for n in bc._depends(name))
            if row_key not in cache[case].setdefault(name, {}):
                result = verdict(table, case, name, per_case)
                cache[case][name][row_key] = result
                if result is False and name in ("U-OUT", "U-HB", "FD-BLD-07"):
                    row, _ = bc._row(table, case, name, per_case, None)
                    for item in _detail(name, case, row):
                        details[case].setdefault(name, {}).setdefault(item, 0)
                        details[case][name][item] += 1
            out[name] = cache[case][name][row_key]
        return out

    stats = {"size": 0, "survives": 0, "rejected": 0, "unreadable": 0, "with_fd_bld_03": 0,
             "failing": {n: 0 for n in bc.CONSTRAINTS}, "sole": {n: 0 for n in bc.CONSTRAINTS},
             "alone": {case: 0 for case in CASES}, "alone_unreadable": {case: 0 for case in CASES},
             "marginal": {label: {str(v): 0 for v in values[label]} for label in COORDS}}
    for combination in itertools.product(*(values[label] for label in COORDS)):
        combination = dict(zip(COORDS, combination))
        verdicts = {case: case_verdicts(case, combination) for case in CASES}
        stats["size"] += 1
        failing, unreadable = [], False
        for name in bc.CONSTRAINTS:
            results = [verdicts[case][name] for case in CASES]
            if False in results:
                failing.append(name)
            elif None in results:
                unreadable = True
        for case in CASES:
            results = [verdicts[case][name] for name in bc.CONSTRAINTS]
            if False not in results and None not in results:
                stats["alone"][case] += 1
            elif False not in results:
                stats["alone_unreadable"][case] += 1
        for name in failing:
            stats["failing"][name] += 1
        if len(failing) == 1:
            stats["sole"][failing[0]] += 1
        if failing:
            stats["rejected"] += 1
        elif unreadable:
            stats["unreadable"] += 1
        else:
            stats["survives"] += 1
            for label in COORDS:
                stats["marginal"][label][str(combination[label])] += 1
            if all(verdicts[case]["FD-BLD-03"] for case in CASES):
                stats["with_fd_bld_03"] += 1
    # The positions do not vary inside a box (one per case), so each case's own candidates are the box's.
    stats["details"] = details
    return stats


# Patient-like trajectories of the extension -----------------------------------------------------------------------

def moved_representatives(data: dict, ext: dict) -> dict:
    """The P2I-2V-R representatives (low, middle, high; its frozen rule), each moved to every one-at-a-time
    extension point: the coordinate changes, nothing else. Their verdicts come from the design's table."""
    out = {}
    for label, points in extended(ext).items():
        parameter, case_of = _parameter(label)
        for point in points:
            moved = {}
            for tag, item in data["representatives"].items():
                values = {case: {**item["values"][case]} for case in CASES}
                for case in CASES:
                    values[case][bc.POS] = positions(case)[values[case][bc.POS]] \
                        if isinstance(values[case][bc.POS], str) else values[case][bc.POS]
                    if case_of is None or case_of == case:
                        values[case][parameter] = point
                moved[tag] = values
            out[f"{label}={point:g}"] = moved
    return out


def _trajectories(task):
    case, values = task
    try:
        return bc.trajectories(case, values)
    except Exception as error:
        return {UNREADABLE: f"{type(error).__name__}: {error}"}


# Freeze ---------------------------------------------------------------------------------------------------------

FREEZE_EXCLUDED = ("clinical_core/blood_filter_report.py", "clinical_core/blood_extension_report.py")


def freeze_sources() -> dict[str, str]:
    out = {}
    for path in sorted((ROOT / "clinical_core").rglob("*.py")):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in FREEZE_EXCLUDED:
            out[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def freeze_digest() -> str:
    data = record()
    text = json.dumps({"revision": REVISION, "record": hashlib.sha256(P2I2VR_RECORD.read_bytes()).hexdigest(),
                       "open_edges": OPEN_EDGES, "domain": {k: [str(v) for v in d] for k, d in DOMAIN.items()},
                       "steps": STEPS, "rule": RULE, "extension": extension(data), "design": design(data),
                       "policy": POLICY, "sources": freeze_sources()}, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# The run (P2I-2W, after the freeze commit) -------------------------------------------------------------------------

def edges(data: dict, ext: dict, boxes: dict) -> dict:
    """Explored and surviving values of every coordinate over the P2I-2V-R grid and the design, with the frozen
    identifiability class and the edge status side by side."""
    out = {}
    for label in COORDS:
        parameter, _ = _parameter(label)
        grid = explored(data, label)
        points = ext.get(label, {}).get("points", [])
        values = sorted(set(grid) | set(points))
        left = set(surviving(data, label))
        for stats in boxes.values():
            left |= {float(v) for v, n in stats["marginal"][label].items() if n > 0}
        left = sorted(left)
        out[label] = {"explored": values, "extended": points, "left": left,
                      "class": identifiability(parameter, values, left), "edge": edge_status(values, left),
                      "before": {"explored": grid, "left": surviving(data, label),
                                 "class": identifiability(parameter, grid, surviving(data, label)),
                                 "edge": edge_status(grid, surviving(data, label))},
                      "at_domain_limit": bool(left and parameter in DOMAIN and left[-1] >= DOMAIN[parameter][1])}
    for name, why in bc.STRUCTURAL.items():
        out.setdefault(name, {"class": bc.SEPARATELY, "edge": None, "why": why})
        out[name]["why"] = why
    return out


def run(progress=None) -> dict:
    data = record()
    if data["freeze_digest"] != P2I2VR_DIGEST:
        raise AssertionError("the P2I-2V-R record is not the committed one")
    ext = extension(data)
    base = base_box(data)
    boxes = design(data)
    needed = rows_needed(boxes, base)
    moved = moved_representatives(data, ext)
    for item in moved.values():
        for values in item.values():
            for case in CASES:
                per_case = values[case]
                for source in SOURCES:
                    needed[(case, source)].add(tuple(per_case[n] for n in _keys(source)))
    table = build(needed, progress)
    found = contradictions(table)
    results = {box["name"]: {**evaluate_box(table, box, base), "kind": box["kind"], "fixed": box["fixed"],
                             "why": box.get("why")} for box in boxes}
    if results["base"]["survives"] != data["primary"]["joint"]:
        raise AssertionError(f"the surviving box gives {results['base']['survives']} survivors, not the frozen "
                             f"{data['primary']['joint']}")
    unreadable = {f"{case}|{source}": sum(1 for row in table[case][source].values() if UNREADABLE in row)
                  for case in CASES for source in SOURCES}
    messages = sorted({row[UNREADABLE] for case in CASES for source in SOURCES
                       for row in table[case][source].values() if UNREADABLE in row})[:20]
    representatives = {}
    for point, item in moved.items():
        representatives[point] = {}
        for tag, values in item.items():
            entry = {"values": values, "trajectories": {}, "verdicts": {}}
            for case in CASES:
                entry["trajectories"][case] = _trajectories((case, values[case]))
                entry["verdicts"][case] = {name: verdict(table, case, name, values[case]) for name in READINGS}
            representatives[point][tag] = entry
    metrics = {}
    for label, item in ext.items():
        parameter, case_of = _parameter(label)
        for point in item["points"]:
            metrics[f"{label}={point:g}"] = _point_metrics(table, base, label, point)
    return {"freeze_digest": freeze_digest(), "decided": DECIDED, "revision": REVISION,
            "record_digest": data["freeze_digest"], "open_edges": OPEN_EDGES, "reported_open_edges":
            reported_open_edges(data), "rule": RULE, "extension": ext, "policy": POLICY,
            "base": {label: list(values) for label, values in base.items()},
            "design": boxes, "boxes": results,
            "candidates": {"extended": sum(box["size"] for box in boxes if box["kind"] != "base"),
                           "base": results["base"]["size"]},
            "rows": {f"{case}|{source}": len(table[case][source]) for case in CASES for source in SOURCES},
            "unreadable_rows": unreadable, "unreadable_messages": messages, "contradictions": found,
            "edges": edges(data, ext, results), "representatives": representatives, "metrics": metrics}


def _point_metrics(table: dict, base: dict, label: str, point) -> dict:
    """What the constraints read at one extension point, over the rows of its one-at-a-time box (context)."""
    values = _box_values({"fixed": {label: point}}, base)
    out = {}
    for case in CASES:
        per_case = {name: values[name] for name in bc.SHARED}
        per_case[bc.BLEED], per_case[bc.POS] = values[COMMON], values[POSITION[case]]

        def rows(source):
            keys = _keys(source)
            found = [table[case][source].get(key) for key in itertools.product(*(per_case[n] for n in keys))]
            return [row for row in found if row is not None and UNREADABLE not in row]

        untreated, blood, cells = rows("untreated"), rows("untreated_blood"), rows("red_cells")
        acute, stopped, crystalloid = rows(f"acute_{int(bc.ACUTE_LOSS_ML)}"), rows("stopped"), rows("crystalloid")
        out[case] = {
            "untreated_output": {m: bc._envelope([r["output"][m] for r in untreated]) for m in bc.MINUTES_OUTPUT},
            "untreated_stopped": sum(1 for r in untreated if r["stop"] is not None),
            "untreated_hb_fall": {m: bc._envelope([r["fall"][m] for r in blood]) for m in bc.MINUTES_HB},
            "one_unit_relative_output_gain": bc._envelope([r["output"][1] / r["output"][0] - 1 for r in cells]),
            "second_unit_gain": bc._envelope([r["output"][2] / r["output"][1] - 1 for r in cells]),
            "one_unit_position": bc._envelope([r["position"][1] for r in cells]),
            "crystalloid_peak_dilution": {int(v): bc._envelope([r[v]["peak"] for r in crystalloid])
                                          for v in bc.CRYSTALLOID_VOLUMES},
            "refill_share": {m: bc._envelope([r["share"][m] for r in acute]) for m in bc.REFILL_MINUTES},
            "refill_after_haemostasis_ml": bc._envelope([r["after_ml"] for r in stopped]),
        }
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
        data = record()
        boxes = design(data)
        needed = rows_needed(boxes, base_box(data))
        print(json.dumps({"extension": extension(data), "boxes": [(b["name"], b["kind"], b["size"]) for b in boxes],
                          "extended_candidates": sum(b["size"] for b in boxes if b["kind"] != "base"),
                          "rows": {f"{c}|{s}": len(k) for (c, s), k in needed.items()}}, indent=1, default=str))
        return 0
    if args.run:
        if not args.out:
            parser.error("--run needs --out (a directory outside the repository)")
        out = Path(args.out)
        if out.resolve().is_relative_to(ROOT):
            parser.error("--out must be outside the repository")
        out.mkdir(parents=True, exist_ok=True)
        result = run(lambda done, total: print(f"rows {done}/{total}", flush=True))
        (out / "blood_extension.json").write_text(json.dumps(result, indent=1, sort_keys=True, default=str),
                                                  encoding="utf-8")
        print(out / "blood_extension.json")
        return 0
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
