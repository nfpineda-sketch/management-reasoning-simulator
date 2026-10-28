"""Phase 2 shadow core, P2I-2AC: oxygen-debt semantics and L3 resuscitation adequacy.

These tests pin the faculty decisions as frozen before evaluation: the P2I-2AB record and source space are the
committed ones; D and lactate are post-processed exactly as the corrected core computes them (off-grid points only,
never a candidate), also at demand 0.9 / 1.1 and over the rho band; L3 adequacy is its own rejection and never passes
as NOT_EVALUABLE; the bleeding windows follow the actual flow, not the haemostasis label; demand is reported
uncertainty, never a filter; rho is never counted; the P2F region is never read and the legacy lactate only after the
filter; and the filter order, the reporting rules and the verdict rule were frozen before any count was seen.
"""
import ast
import hashlib
import inspect

import pytest

from clinical_core import blood_constraints as bc
from clinical_core import blood_fluid_calibration as bf
from clinical_core import decision_pack, lactate_slice
from clinical_core import faculty_constraints as fd
from clinical_core import lactate_adequacy as la
from clinical_core import lactate_rebuild as lr
from test_clinical_core_lactate_rebuild import OFF_GRID, OFF_GRID_POINTS, OFF_GRID_UNIT

ROOT = la.ROOT
SOURCE = ROOT / "clinical_core" / "lactate_adequacy.py"
#: The P2I-2AC freeze: faculty decisions, the P2I-2AB record, the corrected-debt factorization, actual-flow windows,
#: L3 adequacy, demand layer, rho handling, filter order, validation sample, audit, reporting rules, verdict rule,
#: policy and every clinical_core source but the downstream reports, committed before any candidate was evaluated.
FROZEN_DIGEST = "fc49efae455d8a5c259df703a5bcd43bf4c87d3b0ba35dfefdbf1a1567387df5"
P2I2AB_MODULE_SHA = "d969a8c89b678204b4b258c35731f64b0e87ef3cf97b80ef5b92b073ccc9733f"
FACULTY_CONSTRAINTS_SHA = "092c32cf5a20cbf62e3e9df32a47896ccdef701f97170634740a8f8399d7982a"
CASES = la.CASES


def _sha(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


# The frozen inputs ------------------------------------------------------------------------------------------------

def test_the_p2i2ab_record_and_the_faculty_constraints_are_the_committed_ones():
    record = la.record_p2i2ab()
    assert record["freeze_digest"] == la.P2I2AB_DIGEST and record["region"]["digest"] == la.P2I2AB_REGION_DIGEST
    assert record["statistics"]["persistent_critical_decline_after_haemostasis"]["survivors"] == (
        la.P2I2AB_POST_HAEMOSTASIS_DECLINES)
    assert _sha("clinical_core/lactate_rebuild.py") == P2I2AB_MODULE_SHA
    assert _sha("clinical_core/faculty_constraints.py") == FACULTY_CONSTRAINTS_SHA
    source = la.source_space(record)
    assert (len(source["p1"]), len(source["p3"]), len(record["crystalloid_support"]), len(la.LAMBDAS)) == (
        87, 458, 12, 1215)
    assert sorted(q for children in source["children"] for q in children) == list(range(458))
    assert all(source["p3"][q]["p1"] == i for i, children in enumerate(source["children"]) for q in children)


def test_the_package_is_frozen():
    sources = bf.freeze_sources()
    assert {"clinical_core/lactate_adequacy.py", "clinical_core/integration.py", "clinical_core/derived.py",
            "clinical_core/faculty_constraints.py", "clinical_core/modules/gi_haemorrhage.py"} <= set(sources)
    assert not set(lactate_slice.DOWNSTREAM_REPORTS) & set(sources)
    assert la.freeze_digest() == FROZEN_DIGEST, "a source, the design, a rule or the policy changed after the freeze"


def test_the_faculty_decisions_are_recorded_and_fd_lac_04_05_are_unchanged():
    assert set(la.FACULTY) == {"decided", "debt", "l3_adequacy", "bleeding", "demand", "rho", "fd_lac_04", "fd_lac_05"}
    assert "dD >= 0" in la.FACULTY["debt"] and "minute 90" in la.FACULTY["l3_adequacy"]
    assert "never an FD-LAC-04 failure" in la.FACULTY["l3_adequacy"] and "actual flow" in la.FACULTY["bleeding"]
    assert fd.VERSION == "FD-LAC v2" and fd.PRIMARY["fd04_required_fall"] == 0.0 and la.SETTINGS == fd.PRIMARY
    assert fd.PRIMARY["fd04_sustained_restoration_min"] == 30 and fd.PRIMARY["fd05_minute"] == 120
    assert {c: (e["low"], e["high"]) for c, e in fd.ENVELOPES_120.items()} == {"gi_bleed_57m": (1.5, 4.0),
                                                                              "gi_bleed_72f": (1.2, 3.5)}
    assert la.L3_LATEST_ONSET == fd.PRIMARY["fd05_minute"] - fd.PRIMARY["fd04_sustained_restoration_min"] == 90
    assert lr.FD04_THRESHOLDS == (0.0, 0.05, 0.10, 0.15)


# The corrected debt, post-processed (off-grid points only) ---------------------------------------------------------

@pytest.mark.parametrize("scenario", [la.L1, la.L2, la.L3])
def test_d_and_lactate_post_process_exactly_as_the_corrected_core_on_off_grid_points(scenario):
    """No candidate: blood, crystalloid and lactate-side points off every grid. Exact at reserve 2.5 for any intrinsic
    rate and demand 0.9 / 1.0 / 1.1 (actual flow included); within 1e-9 with the same verdicts at reserve 2.0, 3.0 and
    the synthetic reference 1. D never falls in a minute the core read a deficit."""
    arrivals = lr.arrival_table()
    entry = {**OFF_GRID, **OFF_GRID_UNIT}
    bag = bf.bag(0.22, 0.07, 75.0) if scenario == la.L2 else None
    variants = [(la.RESERVE, "midpoint", f) for f in la.DEMAND_FACTORS] + [
        (la.RESERVE, level, 1.0) for level in ("lower", "upper")] + [
        (r, "midpoint", 1.0) for r in (*la.RHO_BAND, la.RHO_SYNTHETIC_REFERENCE)]
    for case in CASES:
        _, haemodynamic = la._haemodynamic(lr.haemodynamic_task(
            case, scenario, lr.blood_values(entry if scenario == la.L3 else OFF_GRID, case, bag)))
        assert haemodynamic["stop"] is None
        assert haemodynamic["controlled_at"] == (60 if scenario == la.L3 else None)
        assert all(flow > 0.0 for flow in haemodynamic["bleed"]), "the bleed never stops: residual after haemostasis"
        for point in OFF_GRID_POINTS:
            for reserve, intrinsic, factor in variants:
                full = la.full_run(entry, case, scenario, point, bag, reserve, intrinsic, factor)
                result = la.compare(full, la.factorized(haemodynamic, arrivals[case], point, factor), haemodynamic,
                                    case, scenario, point, reserve)
                assert result["agrees"] and result["no_debt_fall_in_deficit"], (case, point, reserve, factor, result)
                if reserve == la.RESERVE:
                    assert result["exact"]


def test_the_debt_series_is_the_corrected_recurrence():
    deficits = [0.2, 0.2, 0.0, 0.1, 0.0, 0.0, 0.3]
    series = la.debt_series(deficits, 10.0, 50.0, 2.0)
    assert series[0] == 10.0 and len(series) == len(deficits) + 1
    for before, after, deficit in zip(series, series[1:], deficits):
        expected = before + 2.0 * deficit if deficit > 0.0 else before - before / 50.0
        assert after == expected
        assert after >= before or deficit == 0.0
    assert la.debt_series([0.0] * 5, 0.0, 30.0, 1.0) == [0.0] * 6
    assert min(la.debt_series([0.0] * 500, 3.0, 1.0, 1.0)) == 0.0
    # Under a steady deficit D keeps rising; the pre-P2I-2AC recurrence settled at g x deficit x tau.
    steady = la.debt_series([0.1] * 600, 0.0, 30.0, 1.0)
    old = lr.debt_series([0.1] * 600, 0.0, 30.0, 1.0)
    assert steady[-1] == pytest.approx(60.0) and old[-1] == pytest.approx(3.0, rel=1e-3)
    # Only G x g and G x arrival debt still reach lactate.
    a = lr.lactate_series(la.debt_series(deficits * 20, 20.0, 60.0, 2.0), 3.4, 60.0, 120.0, 6.0, 1.0, 0.8)
    b = lr.lactate_series(la.debt_series(deficits * 20, 10.0, 60.0, 1.0), 3.4, 60.0, 120.0, 12.0, 1.0, 0.8)
    assert lr._gap(a, b) <= 1e-12


# L3 adequacy, actual flow, FD-LAC-06 split -----------------------------------------------------------------------

def _deficit(*zero_spans, length=121):
    zero = {m for first, last in zero_spans for m in range(first, last + 1)}
    return [0.0 if m in zero else 0.2 for m in range(length)]


@pytest.mark.parametrize("spans, status, onset, reason", [
    (((60, 120),), la.L3_ADEQUATE, 60, None),
    (((30, 120),), la.L3_ADEQUATE, 60, None),
    (((75, 120),), la.L3_ADEQUATE, 75, None),
    (((90, 120),), la.L3_ADEQUATE, 90, None),
    (((91, 120),), la.L3_INADEQUATE, None, la.NOT_SUSTAINED),
    (((60, 89),), la.L3_INADEQUATE, None, la.NOT_SUSTAINED),
    (((40, 75), (80, 115)), la.L3_ADEQUATE, 80, None),
    (((40, 59),), la.L3_INADEQUATE, None, la.NEVER_ADEQUATE),
    ((), la.L3_INADEQUATE, None, la.NEVER_ADEQUATE),
])
def test_l3_adequacy_needs_sustained_adequacy_beginning_by_90(spans, status, onset, reason):
    reading = la.l3_adequacy(_deficit(*spans), 60)
    assert (reading["status"], reading["onset"], reading["reason"]) == (status, onset, reason)
    assert la.l3_adequacy(_deficit((0, 120)), None)["reason"] == la.NO_HAEMOSTASIS


def test_inadequacy_is_its_own_rejection_never_an_fd_lac_04_failure_or_a_pass():
    assert la.BITS[la.L3][:2] == ((la.L3_INADEQUATE, CASES[0]), (la.L3_INADEQUATE, CASES[1]))
    assert la.FILTER_ORDER[1][0] == la.L3 and la.FILTER_ORDER[1][1][0] == la.L3_INADEQUATE
    source = inspect.getsource(la._l3_unit)
    assert 'context.adequacy["status"] == L3_ADEQUATE else _bit(L3, L3_INADEQUATE, case)' in source
    stage = la.Stage(la.L3)
    stage.add(1 << la.BITS[la.L3].index((la.L3_INADEQUATE, CASES[1])), 5)
    report = stage.report()
    assert report["first_failure"] == {f"{la.L3_INADEQUATE} {CASES[1]}": 5} and report["survivors"] == 0
    assert report["only_failure"] == {la.L3_INADEQUATE: 5} and "FD-LAC-04" not in str(report["any_failure"])


def test_the_windows_follow_the_actual_flow_not_the_label():
    deficit = [0.0] * 10 + [0.3] * 100 + [0.0] * 11
    stopped = [2.0] * 60 + [0.0] * 61
    residual = [2.0] * 60 + [0.25] * 61
    # With no residual flow the window is the label's; with a residual flow it goes on after haemostasis.
    assert la.flow_windows(deficit, stopped) == lr.critical_windows(deficit, 60) == [(10, 59)]
    assert la.flow_windows(deficit, residual) == lr.critical_windows(deficit, None) == [(10, 109)]
    lactate = [5.0] * 75 + [4.0] * 46
    worsening = la.Context([0.1] * 121, [1.0] * 121, residual, 60, None)
    result = la.fd_lac_06_run(lactate, worsening)
    assert result["residual"] and not result["active"] and not result["passes"]
    assert all(late >= 60 for _, late in result["residual"])
    gone = la.Context([0.1] * 121, [1.0] * 121, stopped, 60, None)
    assert la.fd_lac_06_run(lactate, gone)["passes"]
    # A recovering critical deficit, or none, still allows the fall.
    falling = [0.1 + 0.0012 * m for m in range(121)]
    recovering = la.Context(falling, [1.0] * 121, residual, 60, None)
    result = la.fd_lac_06_run(lactate, recovering)
    assert result["passes"] and result["recovering_residual"]
    adequate = la.Context([0.5] * 121, [1.0] * 121, residual, 60, None)
    assert la.fd_lac_06_run(lactate, adequate)["passes"] and not adequate.fd06_windows


def test_the_l3_scenario_keeps_its_provisional_residual_fraction():
    bleed = next(item for item in lactate_slice.scenario_inputs(CASES[0], la.L3) if type(item).__name__ ==
                 "GIHaemorrhage")
    assert bleed.fraction_after_hemostasis == 0.1 and bleed.fraction_with_ppi == 0.8
    assert "FD-25" in la.FACULTY["bleeding"]


# Demand and rho -------------------------------------------------------------------------------------------------

def test_demand_is_reported_uncertainty_never_a_filter():
    assert la.DEMAND_FACTORS[0] == la.PRIMARY_DEMAND == 1.0 and set(la.DEMAND_FACTORS) == {0.9, 1.0, 1.1}
    source = inspect.getsource(la.run)
    assert "region_record(primary)" in source and "primary = filtered[PRIMARY_DEMAND]" in source
    assert "statistics = survivor_statistics(source, support, arrivals, tasks, store, primary" in source
    units = {1.0: [(0, 3, (0,), (0, 1))], 0.9: [(0, 3, (0,), (0,))], 1.1: [(0, 4, (0,), (1,))]}
    layer = la.demand_layer({f: {"units": u} for f, u in units.items()}, 2, 10)
    assert layer["classes"] == {la.ROBUST: 0, la.SENSITIVE: 3, la.INCOMPATIBLE: 7}
    assert layer["final_region"] == {la.ROBUST: 0, la.SENSITIVE: 2}
    assert layer["survivors"] == {"1": 2, "0.9": 1, "1.1": 1}
    assert "never a filter" in la.DEMAND_RULE


def test_rho_is_a_band_never_a_candidate_dimension():
    assert la.RHO_BAND == (2.0, 3.0) and la.RESERVE == 2.5 and la.RHO_SYNTHETIC_REFERENCE == 1.0
    assert "never counted" in la.RHO_STATUS and "reserve" not in la.STRUCTURAL
    tree = ast.parse(inspect.getsource(la.filter_))
    assert not any(isinstance(n, ast.Constant) and n.value == "reserves" for n in ast.walk(tree))
    assert "reserves" not in inspect.getsource(la.identifiability)


# Guards, the legacy lactate, approvals ---------------------------------------------------------------------------

def _tree():
    return ast.parse(SOURCE.read_text(encoding="utf-8"))


def test_the_p2f_region_is_never_read():
    imported = set()
    for node in ast.walk(_tree()):
        if isinstance(node, ast.ImportFrom):
            imported |= {alias.name for alias in node.names} | {(node.module or "").split(".")[-1]}
        elif isinstance(node, ast.Import):
            imported |= {alias.name.split(".")[-1] for alias in node.names}
    assert not imported & {"decision_pack", "lactate_constraints", "gi_candidates", "admissible", "region_runs",
                           "legacy_adapter", "family_engine", "contracts_shadow", "lactate_slice"}
    attributes = {node.attr for node in ast.walk(_tree()) if isinstance(node, ast.Attribute)}
    assert not {"admissible", "gi_candidates", "region_runs", "decision_pack"} & attributes
    source = inspect.getsource(la.run)
    assert "with lr.P2FGuard(), lr.LegacyLock():" in source
    assert source.index("lr.legacy_reference(") > source.index("with lr.P2FGuard(), lr.LegacyLock():")
    body = [node for node in ast.walk(ast.parse(source)) if isinstance(node, ast.With)][0]
    assert not any(isinstance(n, ast.Attribute) and n.attr == "legacy_reference" for n in ast.walk(body))


def test_the_legacy_lactate_is_never_read_by_a_constraint():
    readers = set()
    for function in (n for n in ast.walk(_tree()) if isinstance(n, ast.FunctionDef)):
        for node in ast.walk(function):
            if isinstance(node, ast.Constant) and node.value == "lactate_lab":
                readers.add(function.name)
            if isinstance(node, ast.Attribute) and node.attr in ("_legacy_run", "snapshots", "legacy_reference"):
                readers.add(function.name)
    assert readers == {"run"}
    text = SOURCE.read_text(encoding="utf-8")
    assert '"sbp"' not in text and '"map"' not in text and "pulse_rate" not in text


def test_the_verdict_rule_reads_every_faculty_condition():
    validation = {"agree": True, "no_debt_fall_in_deficit": True}
    run_ = {"debt": {"core_read_deficit_with_falling_d": [], "onset_minutes_only": True}, "rerun_equals_factorized": True,
            "flags": {name: False for name in lr.FLAG_RULES}, "controlled_at": 60,
            "rows": [{"minute": m, "bleed_ml_per_min": 0.25} for m in la.TIMES]}
    reviewed = {"LOW": {"runs": {f"{c}|{s}": run_ for c in CASES for s in (la.L1, la.L3)}}}
    statistics = {"adequacy_onset": {c: {"60": 3} for c in CASES}, "fd04_and_05_evaluated_in_both_cases": 3}
    demand = {"classes": {la.ROBUST: 3, la.SENSITIVE: 1, la.INCOMPATIBLE: 6}}
    filtered = {"survivors": 3, "candidates": 10}
    good = la.verdict(True, validation, filtered, statistics, demand, reviewed)
    assert good["verdict"] == la.READY and not good["blockers"] and good["next_domain"] == la.NEXT_DOMAIN
    vacuous = {**statistics, "fd04_and_05_evaluated_in_both_cases": 2}
    assert la.verdict(True, validation, filtered, vacuous, demand, reviewed)["verdict"].startswith(la.NOT_READY)
    late = {**statistics, "adequacy_onset": {CASES[0]: {"60": 2, "None": 1}, CASES[1]: {"60": 3}}}
    assert "L3 adequacy" in la.verdict(True, validation, filtered, late, demand, reviewed)["verdict"]
    falling = {"LOW": {"runs": {k: {**run_, "debt": {"core_read_deficit_with_falling_d": [61],
                                                     "onset_minutes_only": True}} for k in reviewed["LOW"]["runs"]}}}
    assert "D falls" in la.verdict(True, validation, filtered, statistics, demand, falling)["verdict"]
    flagged = {"LOW": {"runs": {k: {**run_, "flags": {**run_["flags"], "INSTANT_NORMALIZATION": True}}
                                for k in reviewed["LOW"]["runs"]}}}
    assert "patient-like" in la.verdict(True, validation, filtered, statistics, demand, flagged)["verdict"]
    assert la.verdict(True, {"agree": False, "no_debt_fall_in_deficit": True}, None, None, None, None)[
        "verdict"].startswith(la.NOT_READY)
    assert la.verdict(True, validation, {"survivors": 0, "candidates": 10}, None, demand, reviewed)["next_domain"] is None
    assert "not started" in la.NEXT_DOMAIN and la.NEXT_DOMAIN.index("heart rate") < la.NEXT_DOMAIN.index("pressure")


def test_nothing_is_selected_or_approved():
    text = SOURCE.read_text(encoding="utf-8")
    assert "FACULTY_APPROVED" not in text
    assert "no value selected or approved" in la.REGION_STATUS and "No candidate, value or parameter" in la.VERDICT_RULE
    assert "Nothing is fitted, selected or approved" in la.POLICY and "collapse stays off" in la.POLICY


def test_the_report_stays_downstream():
    assert "clinical_core/lactate_adequacy_report.py" in lactate_slice.DOWNSTREAM_REPORTS
    assert {"clinical_core/lactate_adequacy.py", "clinical_core/lactate_adequacy_report.py"} <= set(
        decision_pack.PACK_DIGEST_EXCLUDED)
    assert "clinical_core/lactate_adequacy.py" in lactate_slice.slice_sources()


def test_the_validation_sample_covers_the_demand_factors_and_the_rho_band():
    record = la.record_p2i2ab()
    sample = la.validation_sample(la.source_space(record), record["crystalloid_support"])
    canonical = la.LAMBDAS.index(la.CANONICAL)
    assert {s["scenario"] for s in sample} == {la.L1, la.L2, la.L3}
    assert {s["reserve"] for s in sample} == {1.0, 2.0, 2.5, 3.0} and {s["demand"] for s in sample} == {0.9, 1.0, 1.1}
    assert all(s["lambda"] == canonical for s in sample if (s["reserve"], s["intrinsic"], s["demand"]) != (
        la.RESERVE, "midpoint", 1.0))
    assert len(sample) == 432 + 9 * 2 * 4 * 7
    assert bc.SEPARATELY == "NON_IDENTIFIABLE_SEPARATELY"
