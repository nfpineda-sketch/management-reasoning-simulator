"""Phase 2 shadow core, P2J-3: the faculty pressure / tone observable-envelope filter.

    python -m clinical_core.pressure_tone_filter --digest
    python -m clinical_core.pressure_tone_filter --design
    python -m clinical_core.pressure_tone_filter --run --out <directory outside the repository>

Shadow only and offline (faculty brief of 2026-10-30, recorded in FACULTY). The first numeric pressure / tone filter:
the faculty's decisions on the P2J-2 surface (the arrival-normalized channel and the instantaneous response accepted;
primary gains 0.25 / 0.5 / 1 at the provisional afterload a = 0.3; g = 0 a diagnostic reference; g = 1.5 / 2 and
a = 0.1 / 0.5 sensitivity only) and envelopes A-I, frozen with the comparison times and the filter order before any
survivor count. A candidate is a pressure / tone point (gain, afterload) at one demand times one retained physiology
candidate of P2I-2AK (P3 set x crystalloid point x lactate base); it survives when every scenario it projects to passes
every rule in ORDER. The trajectories are P2J-2's exact reconstruction from cached blood trajectories (no new core
physiology), the crystalloid and red-cell comparators the matched counterfactuals (L1 for L2; L3 without unit 1 or
unit 2), FD-LAC P2I-2AD's rules unchanged. HR is read as a diagnostic, never a filter; pressure never feeds HR; no gain,
afterload or envelope is approved.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from . import blood_anchors
from . import blood_fluid_calibration as bf
from . import hr_envelope_filter as hf
from . import hr_observables as ho
from . import hr_primary as hp
from . import hr_structure as hs
from . import lactate_adequacy as la
from . import lactate_closure as lc
from . import lactate_rebuild as lr
from . import pressure_tone as pt
from . import vascular_tone as vt

DECIDED = "2026-10-30"
REVISION = "P2J-3"
ROOT = vt.ROOT
CASES = vt.CASES
C57, C72 = CASES
L1, L2, L3 = vt.L1, vt.L2, vt.L3
CF1, CF2 = hf.CF1, hf.CF2
MINUTES = vt.MINUTES
TIMES = vt.TIMES
LAMBDAS = vt.LAMBDAS
DEMANDS = vt.DEMANDS
UNITS = vt.UNITS
OWN = ("clinical_core/pressure_tone_filter.py",)
P2J2_RECORD = ROOT / "docs" / "revision" / "P2J2_vascular_tone.json"
P2J2_DIGEST = "baa2ee124decc7c84a48b0b8fe5031a9dab774e3587176c79e1907df94904545"

FACULTY = {
    "decided": DECIDED,
    "normalization": "ACCEPTED: T_abs = 1 + g s, T = (1 + g s) / (1 + g s0), s0 the patient's modelled arrival acute "
                     "signal; T = 1 means tone relative to that patient's arrival state; T_abs is an internal modelled "
                     "vasoconstrictor coordinate, not a measured absolute SVR; no universal normal s0 or premorbid SVR",
    "timing": "ACCEPTED: the instantaneous target with the explicit one-step lag; no tone memory, no D-driven vascular "
              "memory, no tone time constant (reconsidered only if later cross-domain behaviour requires it)",
    "gain": "g = 0 DIAGNOSTIC_NO_RESPONSE_REFERENCE; PRIMARY g = 0.25, 0.5, 1.0; SENSITIVITY_ONLY g = 1.5, 2.0, never "
            "rescuing a primary region; no g FACULTY_APPROVED (g > 1 is not declared impossible)",
    "afterload": "PRIMARY a = 0.3, the provisional reference, not approved; a = 0.1 and 0.5 SENSITIVITY_ONLY, reported "
                 "after the primary filter for the qualitative stability of its conclusions",
    "output": "post-resuscitation Q about 1.4-1.8 x arrival is not rejected for being above 1: Q = 1 is the shocked "
              "arrival, not a normal resting output; BloodState and pump calibration are not reopened for it",
    "envelopes": "A-I as frozen in ENVELOPES: case / scenario educational calibration envelopes, not universal "
                 "thresholds; no DBP envelope; pressures above arrival are not pathological by themselves",
    "demand": "1.0 and 1.1 carried separately; robustness across them is not a hard criterion; neither is approved",
    "hr": "HR is a diagnostic in P2J-3 (P2I-2AK A-F under the changed DO2 / D); never a pressure filter unless a "
          "structural contradiction appears; pressure -> HR stays deferred",
    "scope": "shadow only; no final tone or afterload approval, pressure -> HR reconnection, RR calibration, "
             "consciousness recalibration, collapse activation, GI or second-family migration, runtime integration or "
             "legacy fitting; BloodState, D, lactate constraints, RR, the P2J-1 mapping and the HR latent ranges "
             "unchanged",
}

# 1. Support (P2J-3-1) ---------------------------------------------------------------------------------------------------

GAIN_STATUS = {0.0: "DIAGNOSTIC_NO_RESPONSE_REFERENCE", 0.25: "PRIMARY", 0.5: "PRIMARY", 1.0: "PRIMARY",
               1.5: "SENSITIVITY_ONLY", 2.0: "SENSITIVITY_ONLY"}
AFTERLOAD_STATUS = {0.3: "PRIMARY_PROVISIONAL_REFERENCE", 0.1: "SENSITIVITY_ONLY", 0.5: "SENSITIVITY_ONLY"}
PRIMARY_GAINS = tuple(g for g, s in GAIN_STATUS.items() if s == "PRIMARY")
PRIMARY_A = 0.3
REFERENCE_GAIN = 0.0
PRIMARY_PAIRS = tuple((g, PRIMARY_A) for g in PRIMARY_GAINS)
#: Sensitivity: the primary gains at the two other afterload points, and the high gains at the primary one. Pairs P2J-2
#: rejected analytically (g 2 at a 0.5) are not built.
SENSITIVITY_PAIRS = tuple([(g, a) for a in (0.1, 0.5) for g in PRIMARY_GAINS] + [(1.5, PRIMARY_A), (2.0, PRIMARY_A)])

# 2. Envelopes A-I, comparison times, classes (P2J-3, faculty) --------------------------------------------------------------

ENVELOPES = {
    "A": {"scenario": "P1", "case": C57, "minute": 120, "sbp": (40.0, 70.0), "map": (30.0, 50.0),
          "text": "untreated 57m at 120: 40 <= SBP <= 70 and 30 <= MAP <= 50 mmHg"},
    "B": {"scenario": "P1", "case": C72, "minute": 120, "sbp": (60.0, 95.0), "map": (45.0, 70.0),
          "text": "untreated 72f at 120: 60 <= SBP <= 95 and 45 <= MAP <= 70 mmHg"},
    "C": {"scenario": "P2", "comparator": "P1 (L1: L2 without the crystalloid, same blood set, same elapsed time)",
          "text": "crystalloid against its matched same-time untreated counterfactual: no PRESSURE_AND_PERFUSION_WORSEN "
                  "at the comparison times; a zero or negative pressure change with improving perfusion is kept"},
    "D": {"scenario": "P4", "comparator": "L3 without PRBC unit 1 (hr_envelope_filter.counterfactual_items, omit 1)",
          "text": "first PRBC unit against L3 without it: no PRBC_CAUSES_PRESSURE_AND_PERFUSION_WORSENING at the "
                  "comparison times"},
    "E": {"scenario": "P4", "comparator": "L3 without PRBC unit 2 (omit 2)",
          "text": "second PRBC unit against L3 without it: the same rule; no size relation to unit 1 is required"},
    "F": {"scenario": "P4", "minute": 120, "sbp": (90.0, 140.0), "map": (65.0, 105.0),
          "text": "definitive management (haemostasis, sustained adequacy), both cases, at 120: 90 <= SBP <= 140 and "
                  "65 <= MAP <= 105 mmHg; no DBP envelope"},
    "G": {"t_abs": (1.0, 2.0), "scenarios": ("P1", "P2", "P3", "P4"),
          "text": "T_abs within [1.0, 2.0] at every minute of the clinical haemorrhage scenarios (a broad "
                  "physiological exploration envelope, not an SVR range); synthetic probes reported separately"},
    "H": {"scenarios": ("P1", "P2", "P3", "P4"),
          "text": "when the effective deficit is zero the acute tone resolves: with the accepted one-step lag, every "
                  "minute m with deficit(m) = 0 gives T_abs(m + 1) = 1 to numerical precision; no time constant or "
                  "memory tolerance"},
    "I": {"text": "the candidate keeps FD-LAC and L3 adequacy (P2I-2AD's rules, unchanged) under its own tone; a "
                  "pressure / tone point with zero FD-LAC-compatible candidates at a compatible demand is "
                  "CROSS_DOMAIN_INCOMPATIBLE there; no minimum retained share"},
}
PRECISION = 1e-12            # T_abs: deterministic numerical precision only
#: The comparison minutes, frozen: each intervention where it completes, and minute 120.
COMPARISON_TIMES = {"C": ("crystalloid volume complete", 120), "D": ("unit 1 complete", 120),
                    "E": ("unit 2 complete", 120)}
COMPARISON_RULE = (
    "At each comparison minute: delta = intervention - matched counterfactual for MAP, SBP, output Q, delivery and the "
    "effective deficit. Pressure improves when delta MAP > 0, worsens when < 0; perfusion improves when delta delivery "
    "> 0, worsens when < 0 (at equal demand the effective deficit then moves the other way or stays 0); a delta within "
    "1e-9 of its scale is no change. Classes: PRESSURE_AND_PERFUSION_IMPROVE; "
    "PRESSURE_NONIMPROVING_WITH_PERFUSION_IMPROVEMENT; PRESSURE_IMPROVING_WITH_PERFUSION_WORSENING; "
    "PRESSURE_UNCHANGED_WITH_PERFUSION_WORSENING; NO_PERFUSION_CHANGE; PRESSURE_AND_PERFUSION_WORSEN. Only the last "
    "rejects (for the red cells named "
    "PRBC_CAUSES_PRESSURE_AND_PERFUSION_WORSENING); a pressure fall alone never does.")
WORSEN = "PRESSURE_AND_PERFUSION_WORSEN"
ORDER = ("SUPPORT", "SIMULATION", "G", "H", "A", "B", "F", "C", "D", "E", "I")
REJECTION_CLASS = {"SUPPORT": "PRIMARY_RANGE_REJECTION", "SIMULATION": "SIMULATION_REJECTION",
                   "G": "DOMAIN_REJECTION", "H": "DOMAIN_REJECTION", "A": "PRESSURE_ENVELOPE_REJECTION",
                   "B": "PRESSURE_ENVELOPE_REJECTION", "F": "PRESSURE_ENVELOPE_REJECTION",
                   "C": "PRESSURE_ENVELOPE_REJECTION", "D": "PRESSURE_ENVELOPE_REJECTION",
                   "E": "PRESSURE_ENVELOPE_REJECTION", "I": "FD_LAC_REJECTION"}
ORDER_RULE = (
    "Fixed before any count, cheapest first: the support (a table lookup), a structural guard (a run that stops or "
    "meets T's guard), G and H (read on every minute already rebuilt; G holds analytically for g <= 1 since "
    "T_abs = 1 + g s <= 1 + g), A and B (one P1 trajectory per case), F (P4), C (a P2 / P1 pair per crystalloid "
    "point, the most trajectories), D and E (P4 against its counterfactuals), I last (FD-LAC re-read: the most "
    "expensive). Every rule is evaluated for every candidate; the first failure in ORDER is the counted one, every "
    "failure and every pair of failures is reported too.")
DEMAND_CLASSES = ("ROBUST_ACROSS_DEMAND", "DEMAND_1_0_ONLY", "DEMAND_1_1_ONLY", "DEMAND_INCOMPATIBLE")
DEMAND_RULE = ("Demand 1.0 and 1.1 are filtered separately, each on its own retained units; a pressure / tone point "
               "is ROBUST_ACROSS_DEMAND with survivors at both, DEMAND_1_0_ONLY / DEMAND_1_1_ONLY at one, "
               "DEMAND_INCOMPATIBLE at neither. Diagnostic only: robustness is not required.")

IDENTIFIABILITY_RULE = (
    "Computed on the primary filter, never from the faculty's support decisions: a quantity is WELL_CONSTRAINED only "
    "with an authored observation fixing it (none exists after arrival); PARTIALLY_CONSTRAINED when the faculty "
    "pressure envelopes alone (A-F, before I) leave one primary gain without survivors at a demand while another "
    "keeps some; POORLY_IDENTIFIED when the envelopes remove candidates differently across gains without emptying "
    "one; NON_IDENTIFIABLE when they remove the same candidates at every gain. The afterload point reads the same "
    "rule across a = 0.1 / 0.3 / 0.5 at the primary gains (sensitivity). The T_abs trajectory follows the gain; the "
    "pressure / output composite is bounded at 120 by A, B and F while output is never observed.")
BAROREFLEX_NEXT = (
    "Pressure -> HR stays deferred. Proceeding to the baroreflex needs a pressure / tone region the envelopes have "
    "bounded at both demands or a faculty statement that one demand suffices, then a MAP set point and a gain range "
    "authorized before any value, and the P2I-2AK A-F rules repeated (HR recertification).")
READY = "PRESSURE_TONE_OBSERVABLE_FILTER_SATISFIED"
NOT_READY = "PRESSURE_TONE_OBSERVABLE_FILTER_NOT_READY"
EMPTY = "PRESSURE_TONE_FILTER_EMPTY"
VERDICT_RULE = (
    "EMPTY when no primary candidate survives at either demand (then nothing else runs: no sensitivity, no HR). "
    "READY when: some primary candidate survives; A, B, F hold and C, D, E show no pressure and perfusion "
    "contradiction for the survivors (by the filter); G and H hold on every primary trajectory of the survivors; a "
    "non-empty FD-LAC region remains for some primary gain; no SIMULATION rejection among the primary trajectories; "
    "the comparators change only their intervention; the reconstruction equals the core on the validation runs; the "
    "retained units and P2J-2's trajectory tables are reproduced; pressure -> HR stays 0 in the primary HR profile; "
    "nothing is approved. Otherwise NOT_READY with the first failing check.")
POLICY = ("Shadow only. P2J-2's committed record and machinery; legacy pressure never read (no shadow, legacy adapter "
          "or family-engine import), the P2F region never consumed (P2FGuard), no envelope changed after a count, "
          "sensitivity points never rescue a primary candidate, HR never a filter, pressure -> HR not reconnected, "
          "nothing approved.")


def interval(value, bounds) -> bool:
    return value is not None and bounds[0] <= value <= bounds[1]


def _sign(delta: float, scale: float) -> int:
    if abs(delta) <= 1e-9 * max(1.0, abs(scale)):
        return 0
    return 1 if delta > 0.0 else -1


def classify(delta_map: float, delta_delivery: float, map_scale: float, delivery_scale: float) -> str:
    pressure, perfusion = _sign(delta_map, map_scale), _sign(delta_delivery, delivery_scale)
    if pressure < 0 and perfusion < 0:
        return WORSEN
    if perfusion > 0:
        return "PRESSURE_AND_PERFUSION_IMPROVE" if pressure > 0 else "PRESSURE_NONIMPROVING_WITH_PERFUSION_IMPROVEMENT"
    if perfusion < 0:
        return ("PRESSURE_IMPROVING_WITH_PERFUSION_WORSENING" if pressure > 0
                else "PRESSURE_UNCHANGED_WITH_PERFUSION_WORSENING")
    return "NO_PERFUSION_CHANGE"


# 3. What P2J-3 changed outside its module (closing P2J-2) ----------------------------------------------------------------

#: The tuple-only files at P2J-2 (51bc0ca): P2J-3 adds its modules to the two tuples, nothing else; the rest of each
#: syntax tree is P2J-1's (vascular_tone.TUPLE_CHANGES), so the P2J-2 hash stands in for it while that holds.
TUPLE_AT_P2J2 = {"clinical_core/lactate_slice.py": "a7f49f3bceed18cfc0e584f3321c486ba02b5b59b9b976a9d9b26ee75503e96a",
                 "clinical_core/decision_pack.py": "a9398a62cc0856dfa6d6133d85e68049344ddaf6003fb44b51f57bf68b2d4b2d"}


def p2j2_sources(sources: dict) -> dict:
    out = dict(sources)
    for relative, sha in TUPLE_AT_P2J2.items():
        item = vt.TUPLE_CHANGES[relative]
        if relative in out and vt.outside_digest(vt._live(relative), item["changed"]) == item["outside_p2j1"]:
            out[relative] = sha
    return out


def p2j2_record() -> dict:
    record = json.loads(P2J2_RECORD.read_text(encoding="utf-8"))
    if record["freeze_digest"] != P2J2_DIGEST or record["verdict"]["verdict"] != vt.READY:
        raise AssertionError("the P2J-2 record is not the committed one")
    return record


# 4. Trajectories: blood, counterfactuals, groups ------------------------------------------------------------------------

def _cf_blood_task(task: tuple) -> tuple:
    """L3 without one PRBC unit (hr_envelope_filter.counterfactual_items), cached as vascular_tone._blood_task does."""
    key, entry, case, omit = task
    values = lr.blood_values(entry, case, None)
    anchors, profile, full = blood_anchors.setup(case, **values)
    states, stop = blood_anchors.trajectory(anchors, hf.counterfactual_items(case, full, omit), MINUTES, profile)
    unit = full.get("red_cell_unit_volume_ml")
    shed = [state.blood.shed_ml for state in states]
    flow = [after - before for before, after in zip(shed, shed[1:])]
    views = [vt.derive(state, anchors, profile) for state in states]
    if {state.aux.oxygen_demand for state in states} != {anchors.metabolic_demand_baseline}:
        raise AssertionError("a GI blood run carries a demand modifier: the reconstruction does not cover it")
    return key, {"output1": [v.output_rel for v in views], "hb": [s.hb for s in states],
                 "spo2": [v.spo2 for v in views], "pulse": [v.pulse_present for v in views],
                 "bleed": (flow[:1] or [0.0]) + flow, "crystalloid": [s.blood.crystalloid_in_ml for s in states],
                 "prbc": [s.blood.transfused_ml / unit for s in states], "controlled_at": lr.controlled_at(states[-1]),
                 "stop": stop, "demand": [s.aux.oxygen_demand for s in states]}


def completion(series: list, total: float) -> int | None:
    return next((m for m, v in enumerate(series) if v >= total - 1e-9), None)


def comparison_minutes(name: str, blood: dict) -> tuple:
    if name == "C":
        return completion(blood["crystalloid"], blood["crystalloid"][-1]), 120
    return completion(blood["prbc"], 1.0 if name == "D" else 2.0), 120


def _domain(rows: list, gain: float, s0: float) -> dict:
    """G and H on one rebuilt trajectory; the same-minute view of H reported beside it."""
    t_abs = [row["T_abs"] for row in rows]
    g_ok = all(1.0 - PRECISION <= t <= 2.0 + PRECISION for t in t_abs)
    zero = [m for m, row in enumerate(rows[:-1]) if row["sbp"] is not None and row["deficit"] == 0.0]
    h_ok = all(abs(rows[m + 1]["T_abs"] - 1.0) <= PRECISION for m in zero)
    lagged = sum(abs(rows[m]["T_abs"] - 1.0) > PRECISION for m in zero)
    return {"G": g_ok, "H": h_ok, "t_abs_max": max(t_abs), "t_abs_min": min(t_abs), "zero_minutes": len(zero),
            "same_minute_lag": lagged}


def _below(rows: list, level: float) -> int:
    return sum(1 for row in rows if row["sbp"] is not None and row["sbp"] < level)


def _compare(rows: list, other: list, minute: int) -> dict:
    a, b = rows[minute], other[minute]
    klass = classify(a["map"] - b["map"], a["delivery_rel"] - b["delivery_rel"], b["map"], b["delivery_rel"])
    return {"minute": minute, "class": klass, "map": a["map"] - b["map"], "sbp": a["sbp"] - b["sbp"],
            "output": a["output"] - b["output"], "delivery": a["delivery_rel"] - b["delivery_rel"],
            "deficit": a["deficit"] - b["deficit"]}


def _rebuild(blood: dict, anchors, gain: float, a: float) -> dict:
    return vt.rebuild(blood, anchors, gain, a)


def _sim(rebuilt: dict, blood: dict) -> bool:
    """A structural failure: the run stops where its blood trajectory did not, or T meets its guard."""
    return rebuilt["clamps"] > 0 or (rebuilt["stop"] is not None and blood["stop"] is None)


def _group_task(task: tuple) -> tuple:
    """Every rule one group of trajectories decides, at every gain of one afterload point.

    P1 (blood set i): A or B, G, H. P2 ((i, d)): C against the same blood set's P1, G, H. P4 (P3 set q): F, D against L3
    without unit 1, E against L3 without unit 2, G and H on P3 and P4."""
    key, kind, case, level, factor, bloods, a, gains = task
    anchors = vt.tone_anchors(case, level, factor)
    out = {}
    for gain in gains:
        rb = {name: _rebuild(blood, anchors, gain, a) for name, blood in bloods.items()}
        s0 = next(iter(rb.values()))["s0"]
        item = {"simulation": any(_sim(rb[name], bloods[name]) for name in rb)}
        clinical = [name for name in rb if name in ("P1", "P2", "P3", "P4")]
        domains = {name: _domain(rb[name]["rows"], gain, s0) for name in clinical}
        item["G"] = all(d["G"] for d in domains.values())
        item["H"] = all(d["H"] for d in domains.values())
        item["t_abs_max"] = max(d["t_abs_max"] for d in domains.values())
        item["same_minute_lag"] = sum(d["same_minute_lag"] for d in domains.values())
        item["below"] = {name: {str(level_): _below(rb[name]["rows"], level_) for level_ in (80.0, 65.0)}
                         for name in clinical}
        if kind == "P1":
            row = rb["P1"]["rows"][120]
            envelope = ENVELOPES["A" if case == C57 else "B"]
            item["sbp120"], item["map120"] = row["sbp"], row["map"]
            item["A" if case == C57 else "B"] = interval(row["sbp"], envelope["sbp"]) and interval(row["map"],
                                                                                                  envelope["map"])
            item["output120"], item["delivery120"], item["deficit120"] = row["output"], row["delivery_rel"], \
                row["deficit"]
        elif kind == "P2":
            minutes = comparison_minutes("C", bloods["P2"])
            item["C_readings"] = [_compare(rb["P2"]["rows"], rb["P1"]["rows"], m) for m in minutes]
            item["C"] = all(r["class"] != WORSEN for r in item["C_readings"])
        else:
            row = rb["P4"]["rows"][120]
            item["sbp120"], item["map120"], item["t_abs120"] = row["sbp"], row["map"], row["T_abs"]
            item["deficit120"] = row["deficit"]
            item["F"] = interval(row["sbp"], ENVELOPES["F"]["sbp"]) and interval(row["map"], ENVELOPES["F"]["map"])
            for name, cf in (("D", "CF1"), ("E", "CF2")):
                minutes = comparison_minutes(name, bloods["P4"])
                item[f"{name}_readings"] = [_compare(rb["P4"]["rows"], rb[cf]["rows"], m) for m in minutes]
                item[name] = all(r["class"] != WORSEN for r in item[f"{name}_readings"])
        out[f"{gain:g}"] = item
    return key, out


def groups(units_by_demand: dict, pairs=None) -> dict:
    """(kind, set, case, level, demand) -> the blood keys it rebuilds, from the retained units."""
    out = {}
    for factor, units in units_by_demand.items():
        for i, a, b, r, ds in units:
            for case, index in ((C57, a), (C72, b)):
                level = vt.level_of(index)
                out[("P1", i, case, level, factor)] = {"P1": ("P1", case, i)}
                for d in ds:
                    out[("P2", (i, d), case, level, factor)] = {"P2": ("P2", case, (i, d)), "P1": ("P1", case, i)}
                for q in r:
                    out[("P4", q, case, level, factor)] = {"P3": ("P3", case, q), "P4": ("P4", case, q),
                                                          "CF1": ("CF1", case, q), "CF2": ("CF2", case, q)}
    return out


def group_tasks(group_map: dict, bloods: dict, a: float, gains) -> list:
    return [(key, key[0], key[2], key[3], key[4], {name: bloods[blood] for name, blood in members.items()}, a,
             tuple(gains)) for key, members in sorted(group_map.items(), key=str)]


def blood_task_list(group_map: dict, source: dict, support: list) -> tuple[list, list]:
    plain, counterfactual = {}, {}
    for members in group_map.values():
        for name, case, k in members.values():
            if name in ("CF1", "CF2"):
                counterfactual[(name, case, k)] = ((name, case, k), source["p3"][k], case, 1 if name == "CF1" else 2)
            elif name == "P2":
                i, d = k
                plain[(name, case, k)] = ((name, case, k), source["p1"][i], case, vt.SCENARIOS[name],
                                          support[d]["bag"])
            elif name == "P1":
                plain[(name, case, k)] = ((name, case, k), source["p1"][k], case, vt.SCENARIOS[name], None)
            else:
                plain[(name, case, k)] = ((name, case, k), source["p3"][k], case, vt.SCENARIOS[name], None)
    return ([plain[k] for k in sorted(plain, key=str)], [counterfactual[k] for k in sorted(counterfactual, key=str)])


# 5. FD-LAC under each tone (I) --------------------------------------------------------------------------------------------

def _fd_task(task: tuple) -> tuple:
    """vascular_tone._fd_task, keeping which P3 sets and crystalloid points pass (not only how many)."""
    key, unit, factor, a, gains, bloods, arrivals = task
    i, la_, lb, r, ds = unit
    levels = {C57: vt.level_of(la_), C72: vt.level_of(lb)}
    anchors = {(case, lv): vt.tone_anchors(case, lv, factor) for case in CASES for lv in set(levels.values())}
    out = {}
    for gain in gains:
        def hd(name, case, k, level):
            blood = bloods[(name, case, k)]
            return vt.haemodynamic(blood, vt.rebuild(blood, anchors[(case, level)], gain, a))

        def mask(function, scenario, name, k):
            return vt._masks(function, scenario, k, hd(name, C57, k, levels[C57]), hd(name, C72, k, levels[C72]), la_,
                             lb, arrivals, factor, hd57_b=hd(name, C57, k, levels[C72]),
                             hd72_a=hd(name, C72, k, levels[C57]))
        out[f"{gain:g}"] = {"l1": mask(lc._l1_unit, L1, "P1", i) == 0,
                            "q_ok": [q for q in r if mask(lc._l3_unit, L3, "P4", q) == 0],
                            "d_ok": [d for d in ds if mask(lc._l2_unit, L2, "P2", (i, d)) == 0]}
    return key, out


def fd_tasks(units_by_demand: dict, bloods: dict, a: float, gains, arrivals: dict) -> list:
    return vt.fd_tasks(units_by_demand, bloods, a, gains, arrivals)


# 6. The filter: candidates, first failures, overlaps ------------------------------------------------------------------------

RULES = ORDER[1:]


def candidate_rules(unit: tuple, q: int, d: int, factor: float, gain: float, results: dict, fd: dict) -> dict:
    i, a, b, r, ds = unit
    g = f"{gain:g}"
    levels = {C57: vt.level_of(a), C72: vt.level_of(b)}
    p1 = {case: results[("P1", i, case, levels[case], factor)][g] for case in CASES}
    p2 = {case: results[("P2", (i, d), case, levels[case], factor)][g] for case in CASES}
    p4 = {case: results[("P4", q, case, levels[case], factor)][g] for case in CASES}
    every = [*p1.values(), *p2.values(), *p4.values()]
    lactate = fd[(factor, i, a, b)][g]
    return {"SIMULATION": not any(x["simulation"] for x in every), "G": all(x["G"] for x in every),
            "H": all(x["H"] for x in every), "A": p1[C57]["A"], "B": p1[C72]["B"],
            "F": all(p4[c]["F"] for c in CASES), "C": all(p2[c]["C"] for c in CASES),
            "D": all(p4[c]["D"] for c in CASES), "E": all(p4[c]["E"] for c in CASES),
            "I": lactate["l1"] and q in lactate["q_ok"] and d in lactate["d_ok"]}


def filter_point(units: list, factor: float, gain: float, results: dict, fd: dict) -> dict:
    first = {name: 0 for name in RULES}
    anyf = {name: 0 for name in RULES}
    only = {name: 0 for name in RULES}
    overlap = {}
    survivors, entering, fd_alone, envelope_alone = [], 0, 0, 0
    for unit in units:
        i, a, b, r, ds = unit
        for q in r:
            for d in ds:
                entering += 1
                passed = candidate_rules(unit, q, d, factor, gain, results, fd)
                failed = [name for name in RULES if not passed[name]]
                fd_alone += passed["I"]
                envelope_alone += all(passed[n] for n in RULES if n != "I")
                for name in failed:
                    anyf[name] += 1
                if failed:
                    first[failed[0]] += 1
                    if len(failed) == 1:
                        only[failed[0]] += 1
                    for x in failed:
                        for y in failed:
                            if x < y:
                                overlap[f"{x}+{y}"] = overlap.get(f"{x}+{y}", 0) + 1
                else:
                    survivors.append((i, a, b, q, d))
    return {"entering": entering, "survivors": len(survivors), "first_failure": first, "any_failure": anyf,
            "only_failure": only, "overlap": dict(sorted(overlap.items())), "fd_lac_survivors_alone": fd_alone,
            "envelope_survivors_alone": envelope_alone, "cross_domain_incompatible": fd_alone == 0,
            "survivor_units": sorted({(i, a, b) for i, a, b, _, _ in survivors}), "_survivors": survivors,
            "rejection_classes": _classes(first)}


def _classes(first: dict) -> dict:
    out = {}
    for name, count in first.items():
        out[REJECTION_CLASS[name]] = out.get(REJECTION_CLASS[name], 0) + count
    return out


def demand_class(by_demand: dict) -> str:
    alive = {f for f, item in by_demand.items() if item["survivors"]}
    if alive == {"1", "1.1"}:
        return "ROBUST_ACROSS_DEMAND"
    if alive == {"1"}:
        return "DEMAND_1_0_ONLY"
    if alive == {"1.1"}:
        return "DEMAND_1_1_ONLY"
    return "DEMAND_INCOMPATIBLE"


# 7. Survivor support, trade-off, consciousness ---------------------------------------------------------------------------

def _spread(values):
    return pt._spread(list(values))


def support(units_by_demand: dict, filtered: dict, results: dict, factor: float, gain: float) -> dict:
    """LOW / median / HIGH over the survivors' unique trajectories, per case (P2J-3-6), with the T = 1 reference on the
    same keys, the output / delivery trade-off and the time below the consciousness thresholds."""
    g, out = f"{gain:g}", {}
    survivors = filtered["_survivors"]
    for case in CASES:
        pick = 1 if case == C57 else 2
        p1 = sorted({("P1", i, case, vt.level_of(x[pick]), factor) for x in survivors for i in [x[0]]}, key=str)
        p2 = sorted({("P2", (x[0], x[4]), case, vt.level_of(x[pick]), factor) for x in survivors}, key=str)
        p4 = sorted({("P4", x[3], case, vt.level_of(x[pick]), factor) for x in survivors}, key=str)
        item = {"keys": {"P1": len(p1), "P2": len(p2), "P4": len(p4)}}
        item["untreated"] = {f: _spread(results[k][g][f] for k in p1) for f in ("sbp120", "map120")}
        item["untreated_reference"] = {f: _spread(results[k]["0"][f] for k in p1) for f in ("sbp120", "map120")}
        item["tradeoff"] = {f: _spread(results[k][g][src] / results[k]["0"][src] - 1.0 for k in p1)
                            for f, src in (("output_change", "output120"), ("delivery_change", "delivery120"))}
        item["definitive"] = {f: _spread(results[k][g][f] for k in p4) for f in ("sbp120", "map120")}
        item["definitive_reference"] = {f: _spread(results[k]["0"][f] for k in p4) for f in ("sbp120", "map120")}
        item["t_abs120_after_adequacy"] = _spread(results[k][g]["t_abs120"] for k in p4)
        item["t_abs_max"] = _spread(max(results[k][g]["t_abs_max"] for k in ks) for ks in ([*p1, *p2, *p4],))
        item["t_abs_max_by_scenario"] = {"P1": _spread(results[k][g]["t_abs_max"] for k in p1),
                                         "P2": _spread(results[k][g]["t_abs_max"] for k in p2),
                                         "P3/P4": _spread(results[k][g]["t_abs_max"] for k in p4)}
        for name, keys, field in (("C", p2, "C_readings"), ("D", p4, "D_readings"), ("E", p4, "E_readings")):
            readings = [r for k in keys for r in results[k][g][field]]
            item[name] = {"classes": {c: sum(r["class"] == c for r in readings) for c in sorted({r["class"]
                                                                                                for r in readings})},
                          **{f"at {m}": {f: _spread(r[f] for r in readings if r["minute"] == m)
                                         for f in ("map", "sbp", "output", "delivery", "deficit")}
                             for m in sorted({r["minute"] for r in readings})}}
        item["below"] = {scenario: {level: _spread(results[k][g]["below"][scenario][level] for k in keys)
                                    for level in ("80.0", "65.0")}
                         for scenario, keys in (("P1", p1), ("P2", p2), ("P3", p4), ("P4", p4))}
        out[case] = item
    return out


# 8. Validation, reuse and the HR diagnostic ------------------------------------------------------------------------------

def comparator_checks(source: dict, support_: list) -> dict:
    """C, D, E comparators change only their intervention (inputs and minute-by-minute runs, blood-only, T = 1)."""
    entry, bag, kid = source["p1"][0], support_[0]["bag"], source["p3"][source["children"][0][0]]
    out = {}
    for case in CASES:
        values = lr.blood_values(entry, case, bag)
        _, _, full = blood_anchors.setup(case, **values)
        l1, l2 = lr.scenario_items(case, L1, full), lr.scenario_items(case, L2, full)
        crystalloid_only = [type(i).__name__ for i in l2 if all(i != j for j in l1)] == ["Crystalloid"] and \
            all(any(i == j for j in l2) for i in l1)
        plain = vt._blood_task(("x", entry, case, L1, None))[1]
        bagged = vt._blood_task(("x", entry, case, L1, bag))[1]
        values3 = lr.blood_values(kid, case, None)
        _, _, full3 = blood_anchors.setup(case, **values3)
        l3 = lr.scenario_items(case, L3, full3)
        prbc_only = all([type(x).__name__ for x in hf.counterfactual_items(case, full3, omit)] ==
                        [type(x).__name__ for x in l3] and
                        all(x == y for x, y in zip(hf.counterfactual_items(case, full3, omit), l3)
                            if type(x).__name__ != "PackedRedCells") for omit in (1, 2))
        base = vt._blood_task(("x", kid, case, L3, None))[1]
        cf1 = _cf_blood_task(("x", kid, case, 1))[1]
        cf2 = _cf_blood_task(("x", kid, case, 2))[1]
        one, two = completion(base["prbc"], 1.0), completion(base["prbc"], 2.0)
        out[case] = {
            "C_items_differ_by_crystalloid_only": crystalloid_only,
            "C_bag_does_not_reach_L1": plain == bagged,
            "D_E_items_differ_in_the_red_cells_only": prbc_only,
            "D_unit_minutes": [completion(cf1["prbc"], 1.0) == two, cf1["prbc"][one] == 0.0],
            "E_prefix_equal_until_unit_2": all(cf2[f][:one + 1] == base[f][:one + 1] for f in ("output1", "hb")),
            "E_unit_2_never": completion(cf2["prbc"], 2.0) is None,
            "haemostasis_same": base["controlled_at"] == cf1["controlled_at"] == cf2["controlled_at"],
            "elapsed_same": len(base["output1"]) == len(cf1["output1"]) == len(cf2["output1"]) == MINUTES + 1,
            "unit_minutes": [one, two]}
    flat = [v if isinstance(v, bool) else all(v) for item in out.values() for k, v in item.items()
            if k != "unit_minutes"]
    return {"cases": out, "valid": all(flat)}


def _hr_task(task: tuple) -> tuple:
    """L1, L3 and the two counterfactuals of one survivor (case, P3 set, lambda) at one gain, full core: HR readings
    under each primary latent HR combination, and the core's own output / pressure / deficit for the validation."""
    key, entry, point, case, factor, candidates, position, gain, a = task
    changes = {"deficit_to_tone_gain": gain, "afterload_sensitivity": a}
    runs = {sc: hf.full_run({"entry": entry, "point": point, "bag": None}, case, sc, factor, "midpoint", changes)
            for sc in (L1, L3, CF1, CF2)}
    readings = [hf.readings(runs, hs.intrinsic_levels(case)[c["intrinsic"][position]], c) for c in candidates]
    core = {sc: [[r["output"], r["pressure_rel"], r["deficit"]] for r in runs[sc]["rows"]] for sc in (L3, CF1, CF2)}
    return key, {"readings": readings, "core": core}


def hr_diagnostic(units_by_demand: dict, filtered: dict, source: dict, bloods: dict, map_) -> dict:
    """Per primary gain and demand with survivors: P2I-2AK's A-F failures over the survivors' physiology units (a
    diagnostic, never a filter) and the full-core validation of the P4 / counterfactual reconstruction."""
    record = hf.p2i2aj_record()
    pools = {f: hf.arrival_pool(record, f)["primary"] for f in DEMANDS}
    tasks, wanted = [], {}
    for (gain, factor), item in filtered.items():
        phys = sorted({(q, a, b) for i, a, b, q, d in item["_survivors"]})
        wanted[(gain, factor)] = phys
        for q, a, b in phys:
            for case, index, position in ((C57, a, 0), (C72, b, 1)):
                tasks.append(((gain, factor, q, case, index), source["p3"][q], LAMBDAS[index], case, factor,
                              pools[factor], position, gain, PRIMARY_A))
    raw = dict(map_(_hr_task, tasks))
    out, compared, equal = {}, 0, True
    for (gain, factor), phys in wanted.items():
        failures, rows = {}, 0
        for q, a, b in phys:
            r57, r72 = raw[(gain, factor, q, C57, a)]["readings"], raw[(gain, factor, q, C72, b)]["readings"]
            weight = sum(1 for x in filtered[(gain, factor)]["_survivors"] if (x[3], x[1], x[2]) == (q, a, b))
            for x57, x72 in zip(r57, r72):
                rows += weight
                for name in hf.failures(x57, x72):
                    failures[name] = failures.get(name, 0) + weight
            for case, index in ((C57, a), (C72, b)):
                anchors = vt.tone_anchors(case, vt.level_of(index), factor)
                core = raw[(gain, factor, q, case, index)]["core"]
                for sc, name in ((L3, "P4"), (CF1, "CF1"), (CF2, "CF2")):
                    mine = vt.rebuild(bloods[(name, case, q)], anchors, gain, PRIMARY_A)["rows"]
                    compared += 1
                    equal = equal and len(mine) == len(core[sc]) and all(
                        [row["output"], row["p"], row["deficit"]] == theirs for row, theirs in zip(mine, core[sc]))
        out[f"g{gain:g} x{factor:g}"] = {"physiology_units": len(phys), "candidate_rows": rows,
                                         "failures": dict(sorted(failures.items())),
                                         "latent_combinations": len(pools[factor])}
    return {"by_point": out, "validation": {"compared": compared, "equal": equal, "full_runs": 4 * len(tasks)}}


def reuse_tables(units_by_demand: dict, source: dict, support_: list, bloods: dict, arrivals: dict, map_) -> bool:
    """P2J-2's trajectory tables at a = 0.3, reproduced from the same cached trajectories for the gains P2J-3 reads."""
    record = p2j2_record()
    keys = vt.retained_keys(units_by_demand, source, support_)
    gains = [REFERENCE_GAIN, *PRIMARY_GAINS]
    results = dict(map_(vt._key_task, vt.key_tasks(keys, bloods, PRIMARY_A, gains, arrivals)))
    tables = json.loads(json.dumps(vt.trajectory_tables(results, gains), sort_keys=True, default=str))
    theirs = record["trajectories"]
    return all({g: tables[k]["gains"][g] for g in tables[k]["gains"]} ==
               {g: theirs[k]["gains"][g] for g in tables[k]["gains"]} for k in tables) and set(tables) == set(theirs)


# 9. Identifiability, verdict ------------------------------------------------------------------------------------------------

def identifiability(primary: dict, sensitivity: dict) -> dict:
    def classify_points(points: dict) -> str:
        sets = {name: item for name, item in points.items()}
        if not sets:
            return "NON_IDENTIFIABLE"
        alive = [v["envelope_survivors_alone"] > 0 for v in sets.values()]
        counts = [v["envelope_survivors_alone"] for v in sets.values()]
        if any(alive) and not all(alive):
            return "PARTIALLY_CONSTRAINED"
        return "POORLY_IDENTIFIED" if len(set(counts)) > 1 else "NON_IDENTIFIABLE"
    gain = {}
    for factor in ("1", "1.1"):
        gain[factor] = classify_points({g: primary[g][factor] for g in primary})
    afterload = {}
    for factor in ("1", "1.1"):
        for g in (f"{x:g}" for x in PRIMARY_GAINS):
            points = {"0.3": primary[g][factor]}
            for a in ("0.1", "0.5"):
                if f"g{g} a{a}" in sensitivity:
                    points[a] = sensitivity[f"g{g} a{a}"][factor]
            afterload[f"x{factor} g{g}"] = classify_points(points)
    order = ("WELL_CONSTRAINED", "PARTIALLY_CONSTRAINED", "POORLY_IDENTIFIED", "NON_IDENTIFIABLE")
    best = min(gain.values(), key=order.index)
    best_a = min(afterload.values(), key=order.index)
    return {"rule": IDENTIFIABILITY_RULE, "tone gain": {"class": best, "by_demand": gain},
            "afterload a": {"class": best_a, "by_point": afterload},
            "T_abs trajectory": {"class": best, "why": "T_abs = 1 + g s with s the certified signal: it is "
                                                       "constrained exactly as far as g is"},
            "pressure / output composite": {"class": "POORLY_IDENTIFIED",
                                            "why": "A, B and F bound MAP and SBP at 120 (faculty envelopes, not "
                                                   "observations); output is never observed and enters only through "
                                                   "MAP = arrival MAP x Q x T"}}


def verdict(primary: dict, checks_in: dict) -> dict:
    alive = any(item[f]["survivors"] for item in primary.values() for f in item)
    if not alive:
        return {"verdict": EMPTY, "checks": {"primary_survivors": False}, "blockers": ["primary_survivors"],
                "approved": [], "rule": VERDICT_RULE}
    checks = {"primary_survivors": alive, **checks_in, "nothing_approved": True}
    blockers = [name for name, ok in checks.items() if not ok]
    return {"verdict": READY if not blockers else f"{NOT_READY} — {blockers[0]}", "checks": checks,
            "blockers": blockers, "approved": [], "rule": VERDICT_RULE}


# 10. Design, freeze, run -----------------------------------------------------------------------------------------------------

def design() -> dict:
    return {"revision": REVISION, "decided": DECIDED, "faculty": FACULTY, "gain_status": {f"{k:g}": v for k, v in
                                                                                          GAIN_STATUS.items()},
            "afterload_status": {f"{k:g}": v for k, v in AFTERLOAD_STATUS.items()},
            "primary_pairs": [list(p) for p in PRIMARY_PAIRS], "sensitivity_pairs": [list(p) for p in SENSITIVITY_PAIRS],
            "envelopes": ENVELOPES, "precision": PRECISION, "comparison_times": COMPARISON_TIMES,
            "comparison_rule": COMPARISON_RULE, "order": list(ORDER), "rejection_class": REJECTION_CLASS,
            "order_rule": ORDER_RULE, "demand_classes": list(DEMAND_CLASSES), "demand_rule": DEMAND_RULE,
            "identifiability_rule": IDENTIFIABILITY_RULE, "baroreflex_next": BAROREFLEX_NEXT,
            "verdict_rule": VERDICT_RULE, "policy": POLICY, "tuple_at_p2j2": TUPLE_AT_P2J2}


def freeze_digest() -> str:
    text = json.dumps({"revision": REVISION, "p2j2": hashlib.sha256(P2J2_RECORD.read_bytes()).hexdigest(),
                       "design": design(), "sources": bf.freeze_sources()}, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _evaluate(pairs, units_by_demand, group_map, bloods, arrivals, map_) -> dict:
    """Every rule at the given (gain, afterload) points: group results and FD-LAC, then the candidates per demand."""
    out = {}
    for a in sorted({a for _, a in pairs}):
        gains = [REFERENCE_GAIN] + [g for g, x in pairs if x == a]
        results = dict(map_(_group_task, group_tasks(group_map, bloods, a, gains)))
        fd = dict(map_(_fd_task, fd_tasks(units_by_demand, bloods, a, gains, arrivals)))
        for g in gains[1:]:
            for factor in DEMANDS:
                out[(g, a, factor)] = filter_point(units_by_demand[factor], factor, g, results, fd)
        out[("results", a)] = results
    return out


def _public(item: dict) -> dict:
    return {k: v for k, v in item.items() if not k.startswith("_")}


def run(progress=None, map_=map) -> dict:
    say = progress or (lambda *_: None)
    with lr.P2FGuard(), lr.LegacyLock():
        p2j2_record()
        out = {"freeze_digest": freeze_digest(), "decided": DECIDED, "revision": REVISION, "policy": POLICY,
               "faculty": FACULTY, "record": P2J2_DIGEST, "design": design()}
        say("retained units")
        source_record = la.record_p2i2ab()
        source, support_ = la.source_space(source_record), source_record["crystalloid_support"]
        arrivals = lr.arrival_table()
        tasks = lc.haemodynamic_tasks(source, support_)
        store = lc.haemodynamics(tasks, map_)
        units_by_demand, digests = {}, {}
        for factor in DEMANDS:
            region = ho.retained_region(source, support_, arrivals, tasks, store, factor, map_)
            units_by_demand[factor], digests[f"{factor:g}"] = region["units"], region["digest"]
        if not all(digests[f"{f:g}"] == UNITS[f] for f in DEMANDS):
            raise AssertionError("the retained lactate units are not P2I-2AK's")
        say("blood and counterfactual trajectories")
        group_map = groups(units_by_demand)
        plain, counterfactual = blood_task_list(group_map, source, support_)
        bloods = {**dict(map_(vt._blood_task, plain)), **dict(map_(_cf_blood_task, counterfactual))}
        say("reuse and comparators")
        reuse = {"units_digests": digests, "units_equal": True,
                 "p2j2_tables_reproduced": reuse_tables(units_by_demand, source, support_, bloods, arrivals, map_),
                 "blood_trajectories": len(plain), "counterfactual_trajectories": len(counterfactual)}
        comparators = comparator_checks(source, support_)
        say("primary filter")
        evaluated = _evaluate(PRIMARY_PAIRS, units_by_demand, group_map, bloods, arrivals, map_)
        primary = {f"{g:g}": {f"{f:g}": evaluated[(g, PRIMARY_A, f)] for f in DEMANDS} for g in PRIMARY_GAINS}
        results = evaluated[("results", PRIMARY_A)]
        support_out = {f"g{g} x{f}": support(units_by_demand, primary[g][f], results, float(f), float(g))
                       for g in primary for f in primary[g] if primary[g][f]["survivors"]}
        out.update({"units": {f"{f:g}": len(units_by_demand[f]) for f in DEMANDS},
                    "entering_per_point": {f"{f:g}": sum(len(r) * len(ds) for _, _, _, r, ds in units_by_demand[f])
                                           for f in DEMANDS},
                    "groups": len(group_map), "reuse": reuse, "comparators": comparators,
                    "support_accounting": {
                        "explored_pairs": len(vt.admissible()), "primary_pairs": len(PRIMARY_PAIRS),
                        "PRIMARY_RANGE_REJECTION": {f"{f:g}": sum(len(r) * len(ds) for _, _, _, r, ds in units_by_demand[f])
                                                    * (len(vt.admissible()) - len(PRIMARY_PAIRS)) for f in DEMANDS}},
                    "primary": {g: {f: _public(v) for f, v in by.items()} for g, by in primary.items()},
                    "demand_class": {g: demand_class(by) for g, by in primary.items()},
                    "support": support_out,
                    "domain": {"same_minute_lag": {g: sum(results[k][g]["same_minute_lag"] for k in results)
                                                   for g in primary},
                               "t_abs_max": {g: max(results[k][g]["t_abs_max"] for k in results) for g in primary}}})
        alive = any(item["survivors"] for by in primary.values() for item in by.values())
        if not alive:
            out["verdict"] = verdict(primary, {})
            out["early_stop"] = "PRIMARY_REGION_EMPTY: no sensitivity, no HR diagnostic"
            return out
        say("sensitivity")
        sensitive = _evaluate(SENSITIVITY_PAIRS, units_by_demand, group_map, bloods, arrivals, map_)
        sensitivity = {f"g{g:g} a{a:g}": {f"{f:g}": _public(sensitive[(g, a, f)]) for f in DEMANDS}
                       for g, a in SENSITIVITY_PAIRS}
        say("HR diagnostic")
        hr = hr_diagnostic(units_by_demand, {(g, f): evaluated[(g, PRIMARY_A, f)] for g in PRIMARY_GAINS
                                             for f in DEMANDS if evaluated[(g, PRIMARY_A, f)]["survivors"]},
                           source, bloods, map_)
        survivors_keys = {(g, f): evaluated[(g, PRIMARY_A, f)] for g in PRIMARY_GAINS for f in DEMANDS}
        stable = not any(results[k][f"{g:g}"]["simulation"] for k in results for g in PRIMARY_GAINS)
        checks = {"g_h_hold": all(primary[g][f]["any_failure"]["G"] == 0 and primary[g][f]["any_failure"]["H"] == 0
                                  for g in primary for f in primary[g]),
                  "fd_lac_region_nonempty": any(not v["cross_domain_incompatible"] for v in survivors_keys.values()),
                  "feedback_stable": stable, "comparators_change_only_their_intervention": comparators["valid"],
                  "reconstruction_exact": hr["validation"]["equal"] and hr["validation"]["compared"] > 0,
                  "upstream_reproduced": reuse["units_equal"] and reuse["p2j2_tables_reproduced"],
                  "pressure_to_hr_deferred": hp.PRIMARY_HR_CALIBRATION.get("sympathetic_per_pressure_deficit") == 0.0}
        out.update({"sensitivity": sensitivity,
                    "sensitivity_demand_class": {k: demand_class(v) for k, v in sensitivity.items()},
                    "hr": hr, "identifiability": identifiability(primary, sensitivity),
                    "baroreflex_next": BAROREFLEX_NEXT,
                    "efficiency": {"blood_runs": len(plain), "counterfactual_runs": len(counterfactual),
                                   "groups": len(group_map), "points_evaluated": len(PRIMARY_PAIRS)
                                   + len(SENSITIVITY_PAIRS), "hr_full_runs": hr["validation"]["full_runs"],
                                   "core_runs_without_reconstruction": len(group_map) * 3
                                   * (len(PRIMARY_PAIRS) + len(SENSITIVITY_PAIRS)),
                                   "cartesian_sweep": False, "legacy_read": False}})
        out["verdict"] = verdict(primary, checks)
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--digest", action="store_true")
    parser.add_argument("--design", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    if args.digest:
        print(freeze_digest())
    if args.design:
        print(json.dumps(design(), indent=1, sort_keys=True, default=str))
    if args.run:
        if args.out is None:
            parser.error("--run needs --out")
        args.out.mkdir(parents=True, exist_ok=True)
        path = args.out / "pressure_tone_filter.json"
        path.write_text(json.dumps(run(lambda step: print(step, flush=True)), sort_keys=True, separators=(",", ":"),
                                   default=str), encoding="utf-8")
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
