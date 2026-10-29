"""Phase 2 shadow core, P2I-2AB: the GI lactate rebuild on current physiology.

These tests pin that the faculty constraints, the closed records and the crystalloid support are unchanged; that the
source space is built from current certified physiology only and never consumes the historical P2F region; that D
and lactate are post-processed exactly as the core computes them (checked on off-grid points, never a candidate);
that FD-LAC reads the faculty's current semantics (adequate is deficit == 0; a recovering critical deficit may let
lactate fall, a persistent or worsening one may not); that the filter order, the reporting rules and the verdict
rule were frozen before evaluation; and that the legacy lactate is read only after the filter.
"""
import ast
import hashlib
import inspect
import json
import subprocess
import sys
from pathlib import Path

import pytest

from clinical_core import blood_constraints as bc
from clinical_core import blood_fluid_calibration as bf
from clinical_core import blood_fluid_tau_closure as tc
from clinical_core import calibration, decision_pack, gi_reference, lactate_slice
from clinical_core import faculty_constraints as fd
from clinical_core import lactate_rebuild as lr

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "clinical_core" / "lactate_rebuild.py"
#: The P2I-2AB freeze: faculty decisions, readiness, source-space design, lactate side, current FD-LAC rules,
#: factorization method, filter order, validation sample, reporting rules, verdict rule, policy and every clinical_core
#: source but the downstream reports, committed before any candidate was evaluated.
FROZEN_DIGEST = "15d05c321b38d2e2512642bf2e3be64bc4382ad639ad05ea445c9050091d7cc4"
P2I2VR_CONSTRAINTS_SHA = "2d139733ed529a03f9c58cd4aa5eb70c8812bb25ba0737f90172546b4e2a65a8"
P2I2AA_MODULE_SHA = "c16a56a77c3957ae1186f4e2b016ddbadd8fee7bae0d405414fb031af735621b"
FACULTY_CONSTRAINTS_SHA = "092c32cf5a20cbf62e3e9df32a47896ccdef701f97170634740a8f8399d7982a"
#: Closed by P2I-2AC, whose debt correction changes the core sources the freeze digest reads: the module and the
#: record are pinned instead, and the live checks below read only what the correction left unchanged.
P2I2AB_MODULE_SHA = "d969a8c89b678204b4b258c35731f64b0e87ef3cf97b80ef5b92b073ccc9733f"
CASES = lr.CASES


def _sha(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def _record():
    return lr.record_p2i2aa()


# The frozen inputs ------------------------------------------------------------------------------------------------

def test_the_faculty_constraints_and_the_closed_records_are_unchanged():
    assert _sha("clinical_core/blood_constraints.py") == P2I2VR_CONSTRAINTS_SHA
    assert _sha("clinical_core/blood_fluid_tau_closure.py") == P2I2AA_MODULE_SHA
    assert _sha("clinical_core/faculty_constraints.py") == FACULTY_CONSTRAINTS_SHA
    assert _record()["freeze_digest"] == lr.P2I2AA_DIGEST
    assert fd.VERSION == "FD-LAC v2" and fd.PRIMARY["adequacy_tolerance"] == 0.0
    assert fd.PRIMARY["meaningful_change"] == 0.10 and fd.PRIMARY["sustained_min"] == 30
    assert fd.PRIMARY["reassessment_interval_min"] == 15 and fd.PRIMARY["fd01_until_min"] == 60
    assert fd.PRIMARY["fd04_sustained_restoration_min"] == 30 and fd.PRIMARY["fd04_window_min"] == 30
    assert fd.PRIMARY["fd04_required_fall"] == 0.0 and fd.PRIMARY["already_normalized_mmol_l"] == 2.0
    assert {c: (e["low"], e["high"]) for c, e in fd.ENVELOPES.items()} == {"gi_bleed_57m": (4.4, 7.0),
                                                                          "gi_bleed_72f": (3.4, 5.5)}
    assert {c: (e["low"], e["high"]) for c, e in fd.ENVELOPES_120.items()} == {"gi_bleed_57m": (1.5, 4.0),
                                                                              "gi_bleed_72f": (1.2, 3.5)}
    assert lr.SETTINGS == fd.PRIMARY


def test_the_rebuild_is_frozen():
    sources = bf.freeze_sources()
    assert {"clinical_core/lactate_rebuild.py", "clinical_core/faculty_constraints.py",
            "clinical_core/integration.py", "clinical_core/derived.py"} <= set(sources)
    assert not set(lactate_slice.DOWNSTREAM_REPORTS) & set(sources)
    # P2I-2AC corrected the core's debt (no repayment while a deficit lasts): the P2I-2AB module stays byte for byte
    # the frozen one and its record keeps the digest it ran with.
    assert _sha("clinical_core/lactate_rebuild.py") == P2I2AB_MODULE_SHA, "the P2I-2AB module changed"
    assert json.loads(RESULT.read_text(encoding="utf-8"))["freeze_digest"] == FROZEN_DIGEST


def test_readiness_is_the_faculty_s_and_lifts_only_the_tau_blocker():
    record = _record()
    ready = lr.readiness(record)
    assert ready["verdict"] == lr.READINESS == (
        "READY_FOR_CURRENT_PHYSIOLOGY_LACTATE_REBUILD_WITH_PROPAGATED_FLUID_UNCERTAINTY")
    assert ready["previous"] == tc.NOT_READY and ready["previous_blockers"] == [tc.CRYSTALLOID_CRITERION]
    assert ready["tau"]["status"] == lr.TAU_STATUS
    other = json.loads(json.dumps(record))
    other["readiness"]["blockers"].append("shared BloodState active")
    other["readiness"]["criteria"]["shared BloodState active"]["passed"] = False
    assert lr.readiness(other)["verdict"] == tc.NOT_READY


def test_the_whole_certified_crystalloid_support_propagates_without_a_preferred_tau():
    record = _record()
    support = lr.crystalloid_support(record)
    assert [p["key"] for p in support] == record["region"] and len(support) == 12
    assert {p["F0"] for p in support} == {0.2} and {p["Finf"] for p in support} == {0.05, 0.1}
    assert max(p["tau"] for p in support) == 240.0 and all(p["tau"] <= tc.TAU_CAP for p in support)
    assert all(p["bag"] == bf.bag(p["F0"], p["Finf"], p["tau"]) for p in support)
    assert "no preferred tau" in lr.FACULTY["tau"] and lr.TAU_STATUS in lr.FACULTY["tau"]


def test_the_rates_positions_and_l3_modifiers_are_the_faculty_s():
    assert lr.LACTATE_RATES == (2.5, 5.0, 6.0)
    design = lr.blood_design()
    assert design["positions"] == {"gi_bleed_57m": (0.2, 0.35, 0.5), "gi_bleed_72f": (0.3, 0.45, 0.6)}
    assert lr.NON_BAG == ("U-OUT", "U-HB", "FD-BLD-01", "FD-BLD-02", "SECOND-UNIT", "FD-BLD-07", "FD-BLD-08",
                          "FD-BLD-09")
    assert lr.RATE_BOUND == ("U-OUT", "U-HB", "FD-BLD-08") and "FD-BLD-03" not in lr.NON_BAG
    assert set(design["shared"]) == set(lr.BLOOD_DIMS) and not set(bc.BAG) & set(lr.BLOOD_DIMS)
    assert design["shared"][bf.TARGET] == (0.5, 0.75, 1.0) and design["shared"][bf.TAU] == (120.0, 240.0, 480.0)
    audit = tc.l3_audit()
    assert {n: a["value"] for n, a in audit.items()} == {"gi_fraction_with_ppi": 0.8,
                                                         "gi_fraction_after_hemostasis": 0.1}
    assert all(not a["committed_range"] and a["sensitivity_design"] is None for a in audit.values())
    for case in CASES:
        bleed = [i for i in lactate_slice.scenario_inputs(case, lr.L3) if type(i).__name__ == "GIHaemorrhage"][0]
        assert (bleed.fraction_with_ppi, bleed.fraction_after_hemostasis) == (0.8, 0.1)
        assert lactate_slice.endoscopy_minute(case) == 60


def test_the_certified_counts_the_source_must_reproduce():
    counts = lr.certified_counts()
    assert {rate: item["total"] for rate, item in counts.items()} == {"2.5": 3648, "5.0": 3423, "6.0": 2268}
    parts = {name: part["count"] for name, part in counts["2.5"]["parts"].items()}
    assert parts["P2I-2V-R"] == 2628 and sum(parts.values()) == 3648
    assert parts["P2I-2W plasma_refill_target_share=1"] == 264
    assert parts["P2I-2W plasma_refill_target_share=1 & plasma_refill_tau_min=480"] == 756
    # Each count is compared only where its run explored: P2I-2W's boxes fixed the upper positions.
    upper = {"gi_bleed_57m": [0.5], "gi_bleed_72f": [0.6]}
    every = {"gi_bleed_57m": [0.2, 0.35, 0.5], "gi_bleed_72f": [0.3, 0.45, 0.6]}
    for rate, item in counts.items():
        for name, part in item["parts"].items():
            assert part["positions"] == (upper if name.startswith("P2I-2W") else every), (rate, name)
    assert "beyond the certified exploration" in lr.REPRODUCTION_RULE


def test_the_lactate_side_is_the_registry_s_and_the_demand_is_not_variable():
    points = lr.kinetic_points()
    assert points == {"debt_clearance_tau_min": (30.0, 60.0, 120.0), "debt_per_delivery_deficit": (0.5, 1.0, 2.0),
                      "lactate_per_output_deficit": (2.0, 6.0, 12.0), "lactate_clearance_tau_min": (45.0, 120.0, 240.0)}
    assert len(lr.LAMBDAS) == 81 * 3 * 5 == 1215 and len(set(lr.LAMBDAS)) == 1215
    assert lr.ARRIVAL_PAIRS == (("lower", "upper"), ("midpoint", "midpoint"), ("upper", "lower"),
                                ("lower", "lower"), ("upper", "upper"))
    assert calibration.REGISTRY["metabolic_demand_baseline"].points() == ()
    assert "not variable" in lr.DEMAND_RULE and lr.CANONICAL in lr.LAMBDAS
    table = lr.arrival_table()
    for case in CASES:
        bands = gi_reference.case_bands(case)
        assert table[case]["demand_baseline"] == 1.0
        for level in lr.LEVELS:
            band = {"lower": "lower", "midpoint": "midpoint", "upper": "upper"}[level]
            assert table[case]["ratio"][level] == getattr(bands["arrival_delivery_ratio"], band) / lr.RESERVE
            assert table[case]["debt"][level] == getattr(bands["arrival_oxygen_debt"], band)
            assert table[case]["excess"][level] == getattr(bands["arrival_lactate_excess"], band)
    assert table["gi_bleed_57m"]["lactate"] == 4.4 and table["gi_bleed_72f"]["lactate"] == 3.4


# The historical P2F region is never an input ----------------------------------------------------------------------

def _tree():
    return ast.parse(SOURCE.read_text(encoding="utf-8"))


def test_the_source_space_builder_neither_imports_nor_names_the_p2f_region():
    tree = _tree()
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            imported |= {alias.name for alias in node.names} | {(node.module or "").split(".")[-1]}
        elif isinstance(node, ast.Import):
            imported |= {alias.name.split(".")[-1] for alias in node.names}
    assert not imported & {"decision_pack", "lactate_constraints", "gi_candidates", "admissible", "region_runs",
                           "legacy_adapter", "family_engine", "contracts_shadow"}
    attributes = [node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)]
    assert not {"admissible", "gi_candidates", "region_runs", "region_members", "evaluate_region"} & set(attributes)
    assert attributes.count("decision_pack") == 1          # only P2F_ENTRY_POINTS, to guard it
    strings = [node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)]
    for text in strings:
        assert not any(name in text for name in ("P2G_decision_pack", "P2I2_lactate_constraints", "P2I_lactate_slice",
                                                 "1054"))


def test_the_p2f_guard_refuses_every_entry_point_and_the_design_runs_under_it():
    from clinical_core import lactate_constraints
    originals = [getattr(module, name) for module, name in lr.P2F_ENTRY_POINTS]
    assert [name for _, name in lr.P2F_ENTRY_POINTS] == ["admissible", "gi_candidates", "region_runs"]
    with lr.P2FGuard():
        for call in (lambda: decision_pack.admissible(True), lambda: calibration.gi_candidates(True),
                     lambda: lactate_slice.region_runs(True), lambda: lactate_constraints.region(True)):
            with pytest.raises(lr.P2FRegionConsumed):
                call()
        record = _record()
        assert lr.readiness(record)["verdict"] == lr.READINESS
        assert len(lr.crystalloid_support(record)) == 12 and lr.certified_counts()["5.0"]["total"] == 3423
        assert lr.blood_design()["combinations_per_rate"] == 3 ** 8 and lr.arrival_table()
        assert lr.design() and lr.freeze_digest()
    assert [getattr(module, name) for module, name in lr.P2F_ENTRY_POINTS] == originals


def test_the_run_and_its_workers_execute_under_both_guards():
    source = inspect.getsource(lr.run)
    assert "with P2FGuard(), LegacyLock():" in source
    assert source.index("legacy_reference(") > source.index("with P2FGuard(), LegacyLock():")
    body = [node for node in ast.walk(ast.parse(source)) if isinstance(node, ast.With)][0]
    assert not any(isinstance(n, ast.Call) and getattr(n.func, "id", "") == "legacy_reference" for n in ast.walk(body))
    assert "P2FGuard().__enter__()" in inspect.getsource(lr.guard_worker)
    code = ("import sys; import clinical_core.lactate_rebuild; "
            "print('clinical_core.lactate_constraints' in sys.modules)")
    out = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, check=True)
    assert out.stdout.split() == ["False"]


def test_the_legacy_lactate_is_read_only_after_the_filter():
    with lr.LegacyLock():
        with pytest.raises(AssertionError, match="only after the filter"):
            lr.legacy_reference({})
    tree = _tree()
    readers = set()
    for function in (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)):
        for node in ast.walk(function):
            if isinstance(node, ast.Constant) and node.value == "lactate_lab":
                readers.add(function.name)
            if isinstance(node, ast.Attribute) and node.attr in ("_legacy_run", "snapshots", "legacy_reference"):
                readers.add(function.name)
    assert readers == {"legacy_reference"}
    text = SOURCE.read_text(encoding="utf-8")
    assert '"sbp"' not in text and '"map"' not in text and "pulse_rate" not in text


# The factorization (off-grid points only) -------------------------------------------------------------------------

OFF_GRID = {"rate": 3.5, "arrival_circulating_volume_ml": 4200.0, "preload_scale_over_kappa_ml": 1000.0,
            "plasma_refill_target_share": 0.6, "plasma_refill_tau_min": 150.0, "plasma_refill_capacity_ml": 700.0,
            "positions": {"gi_bleed_57m": 0.45, "gi_bleed_72f": 0.5}}
OFF_GRID_UNIT = {"red_cell_unit_hb_g_dl": 19.0, "red_cell_unit_volume_ml": 280.0}
OFF_GRID_POINTS = ((45.0, 1.5, 4.0, 90.0, "upper", "upper", "lower"), (20.0, 3.0, 9.0, 60.0, "lower", "lower", "lower"),
                   (100.0, 0.7, 15.0, 200.0, "midpoint", "midpoint", "upper"))
#: P2I-2AE refused one off-grid arrival: gi_bleed_72f at the intrinsic upper level (100) with the arrival debt at its
#: upper level (60), whose debt alone needed more drive than the arrival HR carried. Since P2I-2AF no arrival residual
#: exists (the arrival HR is predicted, its mismatch reported), so the core refuses none and every variant runs.
INCONSISTENT_ARRIVALS: set = set()


def full_run_or_inconsistent(run_, case: str, intrinsic: str, debt: str):
    """The full run, or None for an arrival P2I-2AE made inconsistent: the core stops there, and only there."""
    from clinical_core.state import CoreInvariantError
    try:
        full = run_()
    except CoreInvariantError as error:
        assert (case, intrinsic, debt) in INCONSISTENT_ARRIVALS, (case, intrinsic, debt, error)
        assert "negative sympathetic contribution" in str(error)
        return None
    assert (case, intrinsic, debt) not in INCONSISTENT_ARRIVALS, (case, intrinsic, debt)
    return full


@pytest.mark.parametrize("scenario", [lr.L1, lr.L2, lr.L3])
def test_the_haemodynamics_still_agree_with_the_core_and_only_the_debt_semantics_changed(scenario):
    """No candidate: blood, crystalloid and lactate-side points off every grid. P2I-2AB's post-process was exact
    against the core it ran on (its record); since P2I-2AC the core's D is not repaid while a deficit lasts, so the
    P2I-2AB D and lactate no longer describe it. What P2I-2AB read from the core stays exact: deficit, haemostasis
    and stop (exact at reserve 2.5, within 1e-9 at 1 and 3), and the old D differs only through repayment during a
    deficit (P2I-2AC's own test checks the corrected post-process)."""
    arrivals = lr.arrival_table()
    entry = {**OFF_GRID, **OFF_GRID_UNIT}
    bag = bf.bag(0.22, 0.07, 75.0) if scenario == lr.L2 else None
    for case in CASES:
        _, haemodynamic = lr._haemodynamic(lr.haemodynamic_task(
            case, scenario, lr.blood_values(entry if scenario == lr.L3 else OFF_GRID, case, bag)))
        assert haemodynamic["stop"] is None
        assert haemodynamic["controlled_at"] == (60 if scenario == lr.L3 else None)
        for point in OFF_GRID_POINTS:
            for reserve, intrinsic in ((lr.RESERVE, "midpoint"), (1.0, "midpoint"), (3.0, "midpoint"),
                                       (lr.RESERVE, "lower"), (lr.RESERVE, "upper")):
                full = full_run_or_inconsistent(lambda: lr.full_run(entry, case, scenario, point, bag, reserve,
                                                                    intrinsic), case, intrinsic, point[5])
                if full is None:
                    continue
                _, old, context = lr.factorized(haemodynamic, arrivals[case], point)
                assert full["controlled_at"] == haemodynamic["controlled_at"] and full["stop"] is None
                gap = lr._gap(context.deficit, full["deficit"])
                assert gap == 0.0 if reserve == lr.RESERVE else gap <= lr.TOLERANCE, (case, point, reserve)
                repaid_in_deficit = any(e > 0.0 and old[m] > 0.0 for m, e in enumerate(context.debt_input))
                assert (old != full["D"]) == repaid_in_deficit or reserve != lr.RESERVE, (case, point)


def test_only_g_times_gain_and_g_times_arrival_debt_reach_lactate():
    assert lr.structural_products()["same_products_gap"] <= 1e-12


# FD-LAC with the current semantics (synthetic runs) ---------------------------------------------------------------

def _context(deficit, haemostasis=None, demand=1.0):
    """A run whose deficit is the given series (reserve 2.5, demand 1): delivery = (demand - deficit) / 2.5."""
    delivery = [(demand - d) / lr.RESERVE for d in deficit]
    context = lr.Context(delivery, [demand] * len(deficit), haemostasis, None)
    assert all(abs(a - b) <= 1e-12 for a, b in zip(context.deficit, deficit))
    return context


def _falling(start=4.0, fall=0.25, until=60, n=121):
    return [start * (1 - fall * min(m, until) / until) for m in range(n)]


def test_adequacy_is_no_deficit_and_compensation_counts_as_adequate():
    delivery = [0.5] * 121                      # below demand, but 2.5 x 0.5 >= 1: COMPENSATED
    context = lr.Context(delivery, [1.0] * 121, None, None)
    assert set(context.deficit) == {0.0} and not context.fd06_windows
    trajectory = context.trajectory([4.0] * 121, [0.0] * 121)
    assert all(fd.adequate(trajectory, m, lr.SETTINGS) for m in range(121))
    assert lr.fd_lac_06_run(_falling(), context)["passes"]


def test_a_recovering_critical_deficit_may_let_lactate_fall_a_persistent_one_may_not():
    recovering = _context([0.3 - 0.2 * min(m, 60) / 60 for m in range(121)])
    persistent = _context([0.3] * 121)
    worsening = _context([0.3 + 0.002 * m for m in range(121)])
    lactate = _falling()
    result = lr.fd_lac_06_run(lactate, recovering)
    assert result["passes"] and result["recovering"] and not result["persistent"]
    assert not lr.fd_lac_06_run(lactate, persistent)["passes"]
    assert not lr.fd_lac_06_run(lactate, worsening)["passes"]
    assert not lr.fd_lac_01(lactate, persistent)["passes"] and lr.fd_lac_01(lactate, recovering)["passes"]
    rising = [4.0 + 0.01 * m for m in range(121)]
    assert lr.fd_lac_06_run(rising, persistent)["passes"]
    assert [c[2] for c in lr.interval_classes(recovering.deficit, None)][:4] == [lr.RECOVERING] * 4
    assert {c[2] for c in lr.interval_classes(persistent.deficit, 60)} == {lr.PERSISTENT}
    assert len(lr.interval_classes(persistent.deficit, 60)) == 4
    assert {c[2] for c in lr.interval_classes([0.0] * 121, None)} == {lr.ADEQUATE}


def test_the_net_deficit_at_reassessment_points_decides_with_no_tolerance():
    deficit = [0.3] * 121
    deficit[15], deficit[30] = 0.35, 0.3 - 1e-12      # worse in between, net better by 1e-12 at 30
    assert lr.classify_pair(deficit, 0, 30) == lr.RECOVERING
    assert lr.classify_pair(deficit, 30, 60) == lr.PERSISTENT        # 0.3 after 0.3 - 1e-12: worse
    assert lr.classify_pair([0.3] * 61, 0, 60) == lr.PERSISTENT      # stable is persistent
    nine = [4.0 * (1 - 0.09 * min(m, 30) / 30) for m in range(121)]  # a 9 % fall is not substantial
    assert lr.fd_lac_06_run(nine, _context([0.3] * 121))["passes"]


def test_fd_lac_01_reads_before_60_and_windows_end_at_haemostasis():
    late_fall = [4.0 if m <= 60 else 4.0 * (1 - 0.25 * (m - 60) / 60) for m in range(121)]
    persistent = _context([0.3] * 121)
    assert lr.fd_lac_01(late_fall, persistent)["passes"]
    assert not lr.fd_lac_06_run(late_fall, persistent)["passes"]
    controlled = _context([0.3] * 121, haemostasis=60)
    assert controlled.fd06_windows == [(0, 59)] and lr.fd_lac_06_run(late_fall, controlled)["passes"]
    # Reported only: the same fall after haemostasis, with a persistent deficit.
    assert lr._falls(late_fall, lr._after_haemostasis(controlled), controlled.factor)
    assert not lr._after_haemostasis(persistent)
    short = _context([0.3 if m < 20 else 0.0 for m in range(121)])
    assert lr.fd_lac_01(_falling(), short)["status"] == fd.NOT_APPLICABLE
    assert lr.fd_lac_01(_falling(), short)["passes"] is fd.PRIMARY["fd01_unapplicable_passes"]


def test_every_decline_is_the_frozen_sustained_decline_split_by_the_deficit():
    deficit = [0.3 - 0.002 * m if m < 50 else 0.2 + 0.003 * (m - 50) for m in range(121)]
    context = _context(deficit)
    lactate = [4.0 + 0.6 * ((m * 37) % 11) / 11 - 0.01 * m for m in range(121)]
    trajectory = context.trajectory(lactate, [0.0] * 121)
    assert fd.inadequate_bleeding_windows(trajectory, lr.SETTINGS) == lr.critical_windows(context.deficit, None)
    for first, last in context.fd06_windows:
        frozen = fd.sustained_declines(trajectory, first, last, lr.SETTINGS)
        mine = sorted(lr._falls(lactate, [p for side in (lr.RECOVERING, lr.PERSISTENT)
                                          for p in context.fd06_pairs[side] if first <= p[0] and p[1] <= last],
                                context.factor))
        assert frozen and frozen == mine
        assert all(lr.classify_pair(deficit, e, l) == (lr.RECOVERING if deficit[l] < deficit[e] else lr.PERSISTENT)
                   for e, l in mine)


def test_fd_lac_04_and_05_are_the_frozen_functions_with_deficit_adequacy():
    deficit = [0.2 if m < 70 else 0.0 for m in range(121)]
    context = _context(deficit, haemostasis=60)
    lactate = [4.0 if m <= 70 else 4.0 - 0.02 * (m - 70) for m in range(121)]
    trajectory = context.trajectory(lactate, [0.0] * 121)
    response = fd.fd_lac_04(trajectory, lr.SETTINGS)
    assert response["trigger"] == 70 and response["status"] == fd.PASS
    residual = fd.fd_lac_05(trajectory, response["trigger"], lr.kinetics_of(lr.CANONICAL), lactate[0], lr.SETTINGS,
                            "gi_bleed_57m")
    assert residual["status"] == fd.PASS and residual["residual"] == lactate[120]
    never = _context([0.2] * 121, haemostasis=60)
    assert fd.fd_lac_04(never.trajectory(lactate, [0.0] * 121), lr.SETTINGS)["status"] == fd.NOT_EVALUABLE


# The filter, the accounting and the reporting rules ---------------------------------------------------------------

def test_the_filter_order_was_fixed_by_cost_and_every_failure_is_counted():
    assert [s for s, _ in lr.FILTER_ORDER] == [lr.L1, lr.L3, lr.L2]
    assert lr.BITS[lr.L1][:2] == (("FD-LAC-02/03", "gi_bleed_57m"), ("FD-LAC-02/03", "gi_bleed_72f"))
    assert lr.BITS[lr.L1][-1] == (lr.STOPPED, None) and lr.BITS[lr.L2][-1] == (lr.STOPPED, None)
    stage = lr.Stage(lr.L3)
    stage.add(0, 12)
    stage.add(lr._bit(lr.L3, "FD-LAC-05", "gi_bleed_72f") | lr._bit(lr.L3, "FD-LAC-06", "gi_bleed_57m"), 12)
    report = stage.report()
    assert report["entering"] == 24 and report["rejected"] == 12 and report["survivors"] == 12
    assert report["first_failure"] == {"FD-LAC-05 gi_bleed_72f": 12}
    assert report["any_failure"] == {"FD-LAC-05 gi_bleed_72f": 12, "FD-LAC-06 gi_bleed_57m": 12}
    assert report[lr.ANALYTIC_REJECTION] == 0 and report[lr.SIMULATION_REJECTION] == 12
    assert "ANALYTIC_REJECTION" in lr.REJECTION_RULE and "simulations avoided" in lr.REJECTION_RULE


def test_the_synthetic_pipeline_runs_end_to_end_without_a_candidate():
    """One off-grid P1 set with two off-grid red-cell units and two off-grid crystalloid points: the whole filter,
    statistics, identifiability, representatives and region record, under both guards."""
    entry = {**OFF_GRID, "key": "synthetic"}
    p3 = [dict(entry, **OFF_GRID_UNIT, reserves=[2.5], p1=0),
          dict(entry, red_cell_unit_hb_g_dl=21.0, red_cell_unit_volume_ml=330.0, reserves=[1.0, 2.5], p1=0)]
    source = {"p1": [entry], "p3": p3, "children": [[0, 1]],
              "by_position": {"3.5": {c: {"0.45": 1 if c == "gi_bleed_57m" else 0, "0.5": 1} for c in CASES}}}
    support = [{"key": f"0.22|{f:g}|{t:g}", "F0": 0.22, "Finf": f, "tau": t, "bag": bf.bag(0.22, f, t)}
               for f, t in ((0.05, 70.0), (0.1, 45.0))]
    arrivals = lr.arrival_table()
    parts = lr.components(source, support)
    assert parts["candidates"] == 2 * 2 * 1215 and parts["candidates_with_reserve_multiplicity"] == 3 * 2 * 1215
    assert parts["B_positions"]["3.5"] == {"gi_bleed_57m": ["0.45", "0.5"], "gi_bleed_72f": ["0.5"]}
    assert parts["G_haemostasis"] == {c: 60 for c in CASES} and parts["F_oxygen"]["reserves"] == [1.0, 2.5]
    with lr.P2FGuard(), lr.LegacyLock():
        filtered = lr.filter_(source, support, arrivals)
        stages = filtered["stages"]
        assert stages[0]["entering"] == 2 * 2 * 1215 == filtered["candidates"]
        for before, after in zip(stages, stages[1:]):
            assert after["entering"] == before["survivors"]
        assert stages[-1]["survivors"] == filtered["survivors"] == sum(len(r) * len(d) for _, _, r, d in
                                                                       filtered["units"])
        assert filtered["simulated"] == {lr.L1: 2, lr.L2: 4, lr.L3: 4}
        statistics = lr.survivor_statistics(source, support, arrivals, filtered)
        picks = lr.representatives(source, support, filtered, statistics.pop("_l60"))
        assert [picks[t]["rank"] for t in ("LOW", "MID", "HIGH")] == [0, filtered["survivors"] // 2,
                                                                      filtered["survivors"] - 1]
        identifiability = lr.identifiability(source, support, filtered)["dimensions"]
        assert identifiability["debt_per_delivery_deficit"]["status"] == bc.SEPARATELY
        assert identifiability["reserve"]["status"] == bc.SEPARATELY
        assert identifiability["bleed_ml_per_min"]["status"] == "NOT_VARIED"
        region = lr.region_record(filtered)
        assert region["status"] == lr.REGION_STATUS and region["candidates"] == filtered["survivors"]
        assert sum(sum(c.values()) for c in statistics["fd04_status"].values()) == 2 * filtered["survivors"]


def test_the_verdict_needs_survivors_and_evaluated_definitive_management():
    ready, source, keys = {"verdict": lr.READINESS}, {"reproduced": True}, {"certified": True}
    validation = {"agree": True}
    evaluated = {"fd04_status": {c: {fd.PASS: 3} for c in CASES}, "fd05_status": {c: {fd.PASS: 3} for c in CASES}}
    assert lr.verdict(ready, source, keys, validation, {"survivors": 3}, evaluated)["verdict"] == lr.SATISFIED
    vacuous = {"fd04_status": {c: {fd.NOT_EVALUABLE: 3} for c in CASES},
               "fd05_status": {c: {fd.NOT_EVALUABLE: 3} for c in CASES}}
    assert lr.verdict(ready, source, keys, validation, {"survivors": 3}, vacuous)["verdict"].startswith(lr.NOT_READY)
    assert lr.verdict(ready, source, keys, validation, {"survivors": 0}, None)["verdict"].startswith(lr.NOT_READY)
    assert lr.verdict(ready, source, keys, {"agree": False}, None, None)["verdict"].startswith(lr.NOT_READY)
    assert "not started" in lr.NEXT_DOMAIN


def test_nothing_is_selected_or_approved():
    text = SOURCE.read_text(encoding="utf-8")
    assert "FACULTY_APPROVED" not in text.replace("fd.FACULTY_APPROVED", "")
    assert "no value selected or approved" in lr.REGION_STATUS and "No candidate, value or parameter" in lr.VERDICT_RULE
    assert "PROPOSED review markers, not faculty-approved" in lr.FLAG_RULES["INCOMPATIBLE_WITH_SURVIVAL"]


def test_the_report_stays_downstream():
    assert "clinical_core/lactate_rebuild_report.py" in lactate_slice.DOWNSTREAM_REPORTS
    assert {"clinical_core/lactate_rebuild.py", "clinical_core/lactate_rebuild_report.py"} <= set(
        decision_pack.PACK_DIGEST_EXCLUDED)
    assert "clinical_core/lactate_rebuild.py" in lactate_slice.slice_sources()


# After the freeze: the analysis's record ----------------------------------------------------------------------------

RESULT = ROOT / "docs" / "revision" / "P2I2AB_lactate_rebuild.json"
DOCUMENT = ROOT / "docs" / "revision" / "P2I2AB_RECONSTRUCCION_LACTATO.md"


@pytest.fixture(scope="module")
def result():
    return json.loads(RESULT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def arrivals():
    return lr.arrival_table()


def _plain(value):
    return json.loads(json.dumps(value, sort_keys=True, default=str))


def _h(case, scenario, entry, bag=None):
    return lr._haemodynamic(lr.haemodynamic_task(case, scenario, lr.blood_values(entry, case, bag)))[1]


def test_the_record_carries_the_frozen_digest_and_the_faculty_readiness(result):
    assert result["freeze_digest"] == FROZEN_DIGEST and result["revision"] == "P2I-2AB"
    assert result["readiness"]["verdict"] == lr.READINESS and result["records"]["P2I-2AA"] == lr.P2I2AA_DIGEST
    assert [p["key"] for p in result["crystalloid_support"]] == _record()["region"]
    assert result["lactate_side"]["size"] == 1215 and result["lactate_side"]["arrivals"] == _plain(lr.arrival_table())
    assert result["l3"] == _plain(tc.l3_audit())


def test_the_blood_source_reproduces_every_certified_count_where_it_was_explored(result):
    source, counts = result["source"], lr.certified_counts()
    assert source["reproduced"] and source["reproduction_rule"] == lr.REPRODUCTION_RULE
    for rate, item in source["reproduction"].items():
        assert item["total"]["certified"] == item["total"]["reproduced"] == counts[rate]["total"]
        for name, row in item["parts"].items():
            assert row["certified"] == row["reproduced"] == counts[rate]["parts"][name]["count"], (rate, name)
        assert not item["uncovered_explored_cells"]
    assert source["reproduction"]["2.5"]["beyond_certified_exploration"] == {"1|480 @ 0.35 / 0.45": 756}
    assert not any(source["reproduction"][r]["beyond_certified_exploration"] for r in ("5.0", "6.0"))
    assert sum(source["unreadable"].values()) == 0 and result["contradictions"] == []
    assert result["source_keys"]["certified"] and result["source_keys"]["keys"] == 72
    parts = result["components"]
    assert (parts["A_blood"]["P1_sets"], parts["A_blood"]["P3_sets"]) == (87, 458)
    assert parts["B_positions"] == {"2.5": {"gi_bleed_57m": ["0.35", "0.5"], "gi_bleed_72f": ["0.45", "0.6"]},
                                    "5": {"gi_bleed_57m": ["0.5"], "gi_bleed_72f": ["0.6"]},
                                    "6": {"gi_bleed_57m": ["0.5"], "gi_bleed_72f": ["0.6"]}}
    assert parts["candidates"] == 458 * 12 * 1215 and parts["F_oxygen"]["reserves"] == [1.0, 2.5, 3.0]
    assert all(entry["reserves"] == [1.0, 2.5, 3.0] for entry in source["p3"])


def test_the_factorization_agreed_exactly_and_agrees_again_live(result, arrivals):
    validation, sample = result["validation"], result["validation_sample"]
    assert validation["agree"] and validation["exact_at_reserve_2_5"] and not validation["disagreements"]
    assert validation["runs"] == len(sample) == 720 and validation["max_gap_other_reserves"] <= lr.TOLERANCE
    assert {r["scenario"] for r in sample} == {lr.L1, lr.L2, lr.L3} and {r["reserve"] for r in sample} == {1.0, 2.5,
                                                                                                         3.0}
    seen = validation["verdicts_seen"]
    for label in ("L1 FD-LAC-01 FAIL", "L1 FD-LAC-02/03 False", "L1 FD-LAC-06 False", "L2 FD-LAC-06 False",
                  "L3 FD-LAC-04 PASS", "L3 FD-LAC-04 FAIL", "L3 FD-LAC-04 NOT_EVALUABLE", "L3 FD-LAC-05 FAIL"):
        assert seen.get(label), label
    source, support = result["source"], result["crystalloid_support"]
    picked = [sample[0], sample[-1]] + [next(r for r in sample if r["scenario"] == s and r["reserve"] != lr.RESERVE)
                                        for s in (lr.L2, lr.L3)]
    # Live, only what the P2I-2AC debt correction left unchanged: the deficit and the events (see the off-grid test).
    for item in picked:
        _, haemodynamic = lr._haemodynamic(lr._sample_task(item, source, support))
        bag = support[item["support"]]["bag"] if item["scenario"] == lr.L2 else None
        point = lr.LAMBDAS[item["lambda"]]
        full = lr.full_run(source["p3"][item["q"]], item["case"], item["scenario"], point, bag, item["reserve"],
                           item["intrinsic"])
        live = lr.compare(full, lr.factorized(haemodynamic, arrivals[item["case"]], point), haemodynamic,
                          item["case"], item["scenario"], point, item["reserve"])
        assert live["events"] and live["adequacy_is_no_deficit"] and live["gaps"]["deficit"] == item["gaps"]["deficit"]


def test_the_stages_chain_and_the_region_is_its_inline_units(result):
    filtered, region = result["filter"], result["region"]
    stages = filtered["stages"]
    assert [s["scenario"] for s in stages] == [lr.L1, lr.L3, lr.L2]
    assert stages[0]["entering"] == filtered["candidates"] == result["components"]["candidates"]
    for before, after in zip(stages, stages[1:]):
        assert after["entering"] == before["survivors"]
    assert stages[-1]["survivors"] == filtered["survivors"] == region["candidates"] == 439_291
    assert all(s[lr.ANALYTIC_REJECTION] == 0 and s[lr.SIMULATION_REJECTION] == s["rejected"] for s in stages)
    assert not any(lr.STOPPED in name for s in stages for name in s["any_failure"])
    units = region["inline"]
    assert len(units) == region["units"] == 7811 and region["status"] == lr.REGION_STATUS
    assert sum(len(r) * len(d) for _, _, r, d in units) == filtered["survivors"]
    assert hashlib.sha256(json.dumps(units, separators=(",", ":")).encode("utf-8")).hexdigest() == region["digest"]
    p3 = result["source"]["p3"]
    assert sum(len(p3[q]["reserves"]) * len(d) for _, _, r, d in units for q in r) == (
        filtered["survivors_with_reserve_multiplicity"])
    assert all(p3[q]["p1"] == i for i, _, r, _ in units for q in r)


def _chain(result, arrivals, i, index):
    """The three stages recomputed live for one P1 set and lactate-side point: (L1 mask, P3 sets passing L3, crystalloid
    points passing L2 for those)."""
    source, support = result["source"], result["crystalloid_support"]
    p1, children = source["p1"][i], [q for q, e in enumerate(source["p3"]) if e["p1"] == i]
    mask = lr._l1_unit((i, {c: _h(c, lr.L1, p1) for c in CASES}, arrivals, [index]))[1][index]
    if mask:
        return mask, [], []
    passing = [q for q in children if not lr._l3_unit(
        (q, {c: _h(c, lr.L3, source["p3"][q]) for c in CASES}, arrivals, [index]))[1][index]]
    if not passing:
        return 0, [], []
    points = [k for k in range(len(support)) if not lr._l2_unit(
        ((i, k), {c: _h(c, lr.L2, p1, support[k]["bag"]) for c in CASES}, arrivals, [index]))[1][index]]
    return 0, passing, points


def test_survivors_and_their_neighbours_are_recomputed_live(result, arrivals):
    units = result["region"]["inline"]
    region = {(i, index): (r, d) for i, index, r, d in units}
    for i, index, r, d in (units[0], units[len(units) // 2], units[-1]):
        mask, passing, points = _chain(result, arrivals, i, index)
        assert mask == 0 and passing == list(r) and points == list(d)
        for other in (index - 1, index + 1):
            if 0 <= other < len(lr.LAMBDAS) and (i, other) not in region:
                mask, passing, points = _chain(result, arrivals, i, other)
                assert mask or not passing or not points, (i, other)


def test_identifiability_follows_the_frozen_rule(result):
    dimensions, survivors = result["identifiability"]["dimensions"], result["region"]["candidates"]
    for name, item in dimensions.items():
        explored, left = item["explored"], item["surviving"]
        expected = (bc.SEPARATELY if name in lr.STRUCTURAL else "NOT_VARIED" if len(explored) == 1 else
                    bc.WELL if len(left) == 1 else bc.PARTIAL if len(left) < len(explored) else bc.POOR)
        assert item["status"] == expected, name
    assert not any(item["status"] == bc.WELL for item in dimensions.values())
    assert dimensions["G x g"]["surviving"] == ["3", "4", "6", "12", "24"]
    assert dimensions["arrival_pair"]["surviving_weight"].get("lower|upper", 0) == 0
    assert len(dimensions["crystalloid_point"]["surviving"]) == 12
    for name in ("bleed_ml_per_min", "crystalloid_point", "debt_clearance_tau_min", "arrival_pair"):
        assert sum(dimensions[name]["surviving_weight"].values()) == survivors, name


def test_the_statistics_add_up_and_name_the_survivor_bias(result):
    statistics, survivors = result["statistics"], result["region"]["candidates"]
    for key in ("fd01_status", "fd04_status", "fd05_status"):
        assert all(sum(statistics[key][case].values()) == survivors for case in CASES), key
    assert statistics["fd04_status"]["gi_bleed_57m"] == {"PASS": 158_172, "NOT_EVALUABLE": 281_119}
    thresholds = list(statistics["fd04_sensitivity"]["thresholds"].values())
    assert thresholds[0] == survivors and thresholds == sorted(thresholds, reverse=True)
    assert statistics["persistent_critical_decline_after_haemostasis"]["survivors"] == 71_661
    assert statistics["trigger_minute"]["gi_bleed_57m"] == {"60": 158_172, "None": 281_119}


def test_the_post_hoc_evaluated_subset_is_the_documented_one(result, arrivals):
    """Report only (computed after the results, outside the freeze; filters nothing): survivors whose FD-LAC-04 and 05
    were evaluated in both cases, and the arrival delivery level of those that were not."""
    p3, units = result["source"]["p3"], result["region"]["inline"]
    by_q = {}
    for _, index, r, _ in units:
        for q in r:
            by_q.setdefault(q, set()).add(index)
    readings = {q: lr._survivor_l3((q, {c: _h(c, lr.L3, p3[q]) for c in CASES}, arrivals, sorted(idx)))[1]
                for q, idx in sorted(by_q.items())}
    evaluated = vacuous = 0
    levels = set()
    for _, index, r, d in units:
        for q in r:
            ok = all(readings[q][(index, c)]["fd04"] in (fd.PASS, fd.ALREADY_NORMALIZED)
                     and readings[q][(index, c)]["fd05"] == fd.PASS for c in CASES)
            evaluated, vacuous = evaluated + ok * len(d), vacuous + (not ok) * len(d)
            if not ok:
                levels.add(lr.LAMBDAS[index][6])
    assert (evaluated, vacuous) == (135_115, 304_176) and levels == {"lower"}


def test_the_representatives_follow_the_frozen_rule_and_rerun_live(result):
    representatives, survivors = result["representatives"], result["region"]["candidates"]
    assert [representatives[t]["pick"]["rank"] for t in ("LOW", "MID", "HIGH")] == [0, survivors // 2, survivors - 1]
    l60 = {tag: next(row["lactate"] for row in item["runs"]["gi_bleed_57m|L1"]["rows"] if row["minute"] == 60)
           for tag, item in representatives.items()}
    assert l60["LOW"] == result["statistics"]["L60"]["gi_bleed_57m"]["min"]
    assert l60["HIGH"] == result["statistics"]["L60"]["gi_bleed_57m"]["max"]
    pick = representatives["HIGH"]["pick"]
    full = lr.full_run(result["source"]["p3"][pick["p3"]], "gi_bleed_57m", lr.L3, lr.LAMBDAS[pick["lambda"]])
    rows = representatives["HIGH"]["runs"]["gi_bleed_57m|L3"]["rows"]
    # Since P2I-2AC the core's D (and lactate) differ from this record; its haemodynamics do not.
    assert [full["deficit"][m] for m in lr.TIMES] == [row["effective_deficit"] for row in rows]
    assert [row["lactate"] for row in rows] != [full["lactate"][m] for m in lr.TIMES]
    flags = {(tag, key): run["flags"] for tag, item in representatives.items() for key, run in item["runs"].items()}
    assert [k for k, f in flags.items() if f["WORSENING_CRITICAL_WITH_LARGE_LACTATE_FALL"]] == [("HIGH",
                                                                                               "gi_bleed_57m|L3")]
    assert not any(f["INSTANT_NORMALIZATION"] or f["INCOMPATIBLE_WITH_SURVIVAL"] for f in flags.values())


def test_the_legacy_is_a_reference_and_the_verdict_is_recomputed(result):
    legacy = result["legacy_reference"]
    assert legacy["rule"] == lr.LEGACY_RULE and set(legacy["beside_representatives"]) == {"LOW", "MID", "HIGH"}
    assert set(legacy["legacy"]) == set(CASES)
    assert all(set(v) == {lr.L1, lr.L2, lr.L3} for v in legacy["legacy"].values())
    verdict = lr.verdict(result["readiness"], result["source"], result["source_keys"], result["validation"],
                         result["filter"], result["statistics"])
    assert _plain(verdict) == result["verdict"] and verdict["verdict"] == lr.SATISFIED and not verdict["blockers"]
    efficiency = result["efficiency"]
    assert efficiency["factorized_core_runs"] == sum(efficiency["haemodynamic_trajectories"].values()) == 3178
    assert efficiency["naive_core_runs"] == result["filter"]["candidates"] * 6


def test_the_document_blocks_are_generated(result):
    from clinical_core import lactate_rebuild_report as report
    text = DOCUMENT.read_text(encoding="utf-8")
    for name, render in report.RENDERERS.items():
        assert report.apply(text, name, render(result)) == text, name
    assert "LACTATE_CALIBRATION_CONSTRAINTS_SATISFIED" in text and "135 115" in text and "68b92de" in text
