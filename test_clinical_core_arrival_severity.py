"""Phase 2 shadow core, P2I-2AI: case-specific arrival severity, the D / lactate recertification and the arrival HR.

These tests pin the faculty decisions as frozen before evaluation: each case may take its own EXISTING arrival (D0,
delivery) pair; the faculty ordering (57m at least as severe as 72f in both, strictly in one) is applied analytically
from the case bands and never reads an HR quantity; the per-case filter is P2I-2AD's machinery with each case kept
apart, and the tied pairs reproduce P2I-2AD's units exactly; the arrival HR uses the patient-specific intrinsic rate per
case, common gains and ceilings, pressure 0 and +-5 bpm; nothing is approved; the legacy HR is never read.
"""
import ast
import inspect
import json

import pytest

from clinical_core import arrival_severity as asv
from clinical_core import blood_fluid_calibration as bf
from clinical_core import derived, gi_reference, lactate_slice
from clinical_core import hr_primary as hp
from clinical_core import lactate_adequacy as la
from clinical_core import lactate_closure as lc
from clinical_core import lactate_rebuild as lr

ROOT = asv.ROOT
SOURCE = ROOT / "clinical_core" / "arrival_severity.py"
#: The P2I-2AI freeze: faculty decisions, the P2I-2AD / P2I-2AF / P2I-2AG records, the existing pairs, the ordering, the
#: equivalence, compatibility, HR, comparison, trajectory and verdict rules, the policy and every clinical_core source
#: but the downstream reports, committed before any new lactate or HR count was evaluated.
FROZEN_DIGEST = "805eff4efb562b19f1d280bdd48bbc1d458d0055f104b66f7bc7dca7ea61a861"
C57, C72 = asv.C57, asv.C72


# The frozen inputs ------------------------------------------------------------------------------------------------

def test_the_package_is_frozen():
    sources = bf.freeze_sources()
    assert {"clinical_core/arrival_severity.py", "clinical_core/lactate_closure.py"} <= set(sources)
    assert "clinical_core/arrival_severity_report.py" in lactate_slice.DOWNSTREAM_REPORTS
    assert not set(lactate_slice.DOWNSTREAM_REPORTS) & set(sources)
    assert asv.p2i2ad_region()["region"]["digest"] == asv.P2I2AD_REGION_DIGEST
    assert asv.freeze_digest() == FROZEN_DIGEST, "a source, the design, a rule or the policy changed after the freeze"


def test_the_faculty_decisions_are_recorded():
    assert set(asv.FACULTY) == {"decided", "severity", "ordering", "no_hr", "recertification", "intrinsic", "common",
                                "scope"}
    assert "no new D0 or delivery value" in asv.FACULTY["severity"] and "never chooses" in asv.FACULTY["no_hr"]
    assert "never identified" in asv.FACULTY["intrinsic"] and "+-5" in asv.FACULTY["common"]


# P2I-2AI-1..3: the existing pairs, the ordering, no HR ----------------------------------------------------------------

def test_the_pairs_are_the_existing_certified_ones_with_their_band_values():
    assert asv.PAIRS == tuple(tuple(p) for p in lr.ARRIVAL_PAIRS) == (
        ("lower", "upper"), ("midpoint", "midpoint"), ("upper", "lower"), ("lower", "lower"), ("upper", "upper"))
    values = {pair: asv.pair_values(C57, pair) for pair in asv.PAIRS}
    assert {pair: (v["D0"], v["delivery"]) for pair, v in values.items()} == {
        ("lower", "upper"): (0.0, 1.0), ("midpoint", "midpoint"): (20.0, 0.85), ("upper", "lower"): (60.0, 0.6),
        ("lower", "lower"): (0.0, 0.6), ("upper", "upper"): (60.0, 1.0)}
    assert all(asv.pair_values(C72, pair) == values[pair] for pair in asv.PAIRS)
    assert values[("upper", "lower")]["x0"] == pytest.approx(0.4) and values[("lower", "upper")]["x0"] == 0.0
    inventory = asv.inventory(asv.p2i2ad_region()["region"]["inline"])
    assert all(item["valid_after_p2i2ad"] and item["same_values_both_cases"] for item in inventory)
    assert sum(item["p2i2ad_tied_survivors"] for item in inventory) == 353302


def test_the_faculty_ordering_is_applied_analytically():
    pairs = asv.case_pairs()
    assert len(pairs) == 25 and sum(1 for p in pairs if "IDENTICAL" in p["reasons"]) == 5
    allowed = asv.admissible()
    assert allowed == [(("midpoint", "midpoint"), ("lower", "upper")), (("upper", "lower"), ("lower", "upper")),
                       (("upper", "lower"), ("midpoint", "midpoint")), (("upper", "lower"), ("lower", "lower")),
                       (("upper", "lower"), ("upper", "upper")), (("lower", "lower"), ("lower", "upper")),
                       (("upper", "upper"), ("lower", "upper"))]
    for first, second in allowed:
        a, b = asv.pair_values(C57, first), asv.pair_values(C72, second)
        assert a["D0"] >= b["D0"] and a["delivery"] <= b["delivery"] and (a["D0"], a["delivery"]) != (
            b["D0"], b["delivery"])


def test_the_severity_constructor_reads_no_hr_quantity():
    reads = {name.lower() for name in asv.severity_reads()}
    assert not [name for name in reads for word in asv.HR_NAMES if word in name]
    assert {"case_bands", "arrival_oxygen_debt", "arrival_delivery_ratio"} <= reads
    for function in (asv.pair_values, asv.case_pairs, asv.admissible):
        body = inspect.getsource(function)
        for word in ("hp.", "hk.", "hs.", "AUTHORED", "TOLERANCE", "ceiling", "pulse_rate", "legacy"):
            assert word not in body


# P2I-2AI-4, -5: the per-case filter reproduces P2I-2AD -----------------------------------------------------------------

def _mini(i, support_points):
    record = la.record_p2i2ab()
    source, support = la.source_space(record), record["crystalloid_support"]
    kids = source["children"][i]
    mini = {"p1": [source["p1"][i]], "p3": [{**source["p3"][q], "p1": 0} for q in kids],
            "children": [list(range(len(kids)))]}
    return mini, [support[k] for k in support_points]


def test_the_tied_pairs_reproduce_p2i2ad_s_filter_on_a_source_subset():
    with lr.P2FGuard(), lr.LegacyLock():
        arrivals = lr.arrival_table()
        mini, support = _mini(asv.p2i2ad_region()["region"]["inline"][0][0], (0, 11))
        tasks = lc.haemodynamic_tasks(mini, support)
        store = lc.haemodynamics(tasks)
        for factor in (1.0, 1.1):
            reference = lc.filter_(mini, support, arrivals, tasks, store, factor)
            per = asv.per_case_filter(mini, support, arrivals, tasks, store, factor)
            tied = sorted((i, a, r, d) for p in asv.PAIRS for i, a, b, r, d in asv.combine(per, mini, len(support), p, p))
            assert tied == reference["units"] and reference["units"], factor


def test_a_case_pair_survives_only_when_both_cases_pass_with_their_own_pair():
    a, b = asv.INDEX[(*asv.BASES[0], "upper", "lower")], asv.INDEX[(*asv.BASES[0], "lower", "upper")]
    per = {"l1": {C57: {0: {a}}, C72: {0: {b}}}, "l3": {C57: {0: {a}, 1: set()}, C72: {0: {b}, 1: {b}}},
           "l2": {C57: {(0, 0): {a}, (0, 1): {a}}, C72: {(0, 0): {b}, (0, 1): set()}}}
    source = {"children": [[0, 1]]}
    assert asv.combine(per, source, 2, ("upper", "lower"), ("lower", "upper")) == [(0, a, b, (0,), (0,))]
    assert asv.combine(per, source, 2, ("lower", "upper"), ("upper", "lower")) == []


# P2I-2AI-8..10: the arrival HR -----------------------------------------------------------------------------------------

def test_the_arrival_hr_uses_each_case_pair_explicit_intrinsic_and_the_primary_mode():
    assert hp.PRIMARY_HR_CALIBRATION == {"sympathetic_per_pressure_deficit": 0.0}
    body = inspect.getsource(asv.arrival_hr_table)
    assert "hp.require_explicit_intrinsic(anchors)" in body and "hp.primary_profile(acute, gain, ceiling)" in body
    joint = inspect.getsource(asv._joint)
    assert "hp.compatible(C57, first) and hp.compatible(C72, second)" in joint
    assert hp.TOLERANCE_BPM == 5.0 and hp.CEILINGS == (150.0, 175.0, 200.0)
    assert len(hp.ACUTE) == len(hp.DEBT) == 5


def test_the_rules_are_declared_before_any_count():
    for rule in (asv.ORDERING_RULE, asv.EQUIVALENCE, asv.COMPATIBILITY_RULE, asv.HR_RULE, asv.COMPARISON_RULE,
                 asv.TRAJECTORY_RULE, asv.VERDICT_RULE):
        assert rule
    assert asv.UNRESOLVED in asv.VERDICT_RULE and "No pair is approved" in asv.COMPATIBILITY_RULE
    assert "No envelope filters anything" in asv.TRAJECTORY_RULE


def test_no_legacy_no_p2f_region_and_nothing_approved():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    called = {ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)}
    for name in ("_legacy_run", "legacy_reference", "gi_candidates", "admissible_p2f", "region_runs", "p2f_rejection",
                 "gi_physiology"):
        assert not any(name in call for call in called), name
    assert "with lr.P2FGuard(), lr.LegacyLock():" in inspect.getsource(asv.run)
    text = json.dumps(asv.design(), default=str).lower()
    for word in ("faculty_approved", "\"best", "\"selected", "\"recommended", "\"preferred", "\"rank"):
        assert word not in text


# The evaluation's code paths on known or synthetic inputs (no new count) ---------------------------------------------

def test_statistics_representatives_review_and_classification_on_a_tied_subset():
    with lr.P2FGuard(), lr.LegacyLock():
        arrivals = lr.arrival_table()
        mini, support = _mini(asv.p2i2ad_region()["region"]["inline"][0][0], (0, 11))
        tasks = lc.haemodynamic_tasks(mini, support)
        store = lc.haemodynamics(tasks)
        per = asv.per_case_filter(mini, support, arrivals, tasks, store, 1.0)
        units = next(u for u in (asv.combine(per, mini, len(support), p, p) for p in asv.PAIRS) if u)
        stats = asv.statistics(per, units)
        picks = asv.representatives(per, mini, units)
        reviewed = asv.review(mini, support, arrivals, tasks, store, picks)
    assert set(picks) == {"LOW", "MID", "HIGH"} and set(stats) == {"evaluated_both", "trigger_is_onset",
                                                                   "debt_coherent", "adequate_through_120"}
    assert all(run_["rerun_equals_factorized"] for item in reviewed.values() for run_ in item["runs"].values())
    status, checks, _ = asv.classify(asv._survivors(units), stats, reviewed)
    assert status in (asv.LACTATE_COMPATIBLE, asv.LACTATE_INCOMPATIBLE) and set(checks) == {
        "survivors", "adequate_through_120", "fd04_05_evaluated", "trigger_is_onset", "debt_coherent", "patient_like",
        "reruns_exact"}


def test_the_trajectory_machinery_reproduces_the_core_on_a_synthetic_survivor():
    record = asv.p2i2ad_region()
    pick = record["representatives"]["MID"]["pick"]
    source = la.source_space(la.record_p2i2ab())
    support = la.record_p2i2ab()["crystalloid_support"]
    pair = tuple(lc.LAMBDAS[pick["lambda"]][5:])
    key = asv._key(pair, pair)
    regions = {key: {"picks": {"MID": {"p3": pick["p3"], "support": pick["support"], "lambda_57m": pick["lambda"],
                                       "lambda_72f": pick["lambda"]}}}}
    synthetic = [{"pair_57m": list(pair), "pair_72f": list(pair), "intrinsic": ["upper", "lower"],
                  "acute": hp.ACUTE[1], "debt": hp.DEBT[3], "ceiling": 150.0, "predicted": [0.0, 0.0]}]
    with lr.P2FGuard(), lr.LegacyLock():
        result = asv.trajectories(source, support, regions, synthetic)
    assert result["exact"] and result["validation_reruns"] == 2
    readings = result["by_case_pair"][key]["readings"]
    assert {"H1_untreated@120", "H3_prbc@30", "H4_definitive@120", "max_saturated_hr"} <= set(readings[C57])
    assert readings[C57]["max_saturated_hr"]["max"] < 150.0


def test_the_surface_and_comparison_count_joint_compatibility_with_common_gains():
    table = {}
    for case, value in ((C57, 124.0), (C72, 112.0)):
        for pair in asv.PAIRS:
            for level in hp.INTRINSIC:
                for acute in hp.ACUTE:
                    for gain in hp.DEBT:
                        for ceiling in hp.CEILINGS:
                            # Synthetic: compatible only at the severe pair for 57m and the 'none' pair for 72f.
                            hit = (case == C57 and pair == ("upper", "lower")) or (case == C72 and pair == ("lower",
                                                                                                           "upper"))
                            table[(case, pair, level, acute, gain, ceiling)] = {"predicted": value if hit else 0.0}
    compatible = [(("upper", "lower"), ("lower", "upper")), (("midpoint", "midpoint"), ("lower", "upper"))]
    surface = asv.hr_surface(table, compatible)
    assert surface["joint"] == 9 * 75 and surface["distinct_case_pairs"] == 1
    # Per-case counts over the joint candidates; decompositions counted once even when two case pairs share the
    # 72f pair.
    assert (surface["joint_candidates"], surface["compatible_57m"], surface["compatible_72f"]) == (2 * 675, 675, 1350)
    assert surface["decompositions"] == 2 * 225 + 225
    assert surface["compatible_decompositions"] == {C57: 225, C72: 225}
    comparison = asv.comparison(table, compatible)
    assert (comparison["A"]["joint"], comparison["B"]["joint"], comparison["C"]["joint"]) == (0, 3 * 75, 0)
    assert comparison["case_severity_restores"] and not comparison["case_intrinsic_restores"]
