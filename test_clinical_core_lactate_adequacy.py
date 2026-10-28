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
import json

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


# After the freeze: the analysis's record ----------------------------------------------------------------------------


RESULT = ROOT / "docs" / "revision" / "P2I2AC_lactate_adequacy.json"
DOCUMENT = ROOT / "docs" / "revision" / "P2I2AC_DEUDA_Y_ADECUACION_L3.md"


@pytest.fixture(scope="module")
def result():
    return json.loads(RESULT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def setting():
    record = la.record_p2i2ab()
    source, support = la.source_space(record), record["crystalloid_support"]
    return {"record": record, "source": source, "support": support, "arrivals": lr.arrival_table(),
            "tasks": la.haemodynamic_tasks(source, support), "store": {}}


def _store(setting, *keys):
    """The haemodynamic trajectories of the given (scenario, unit, case) keys, simulated live once per test module."""
    tasks, store = setting["tasks"], setting["store"]
    for key in keys:
        if tasks[key] not in store:
            store[tasks[key]] = la._haemodynamic(tasks[key])[1]
    return store


def test_the_record_carries_the_frozen_digest_and_the_validation(result):
    assert result["freeze_digest"] == FROZEN_DIGEST and result["revision"] == "P2I-2AC"
    assert result["records"]["P2I-2AB"] == la.P2I2AB_DIGEST and result["faculty"] == la.FACULTY
    validation = result["validation"]
    assert validation["agree"] and validation["exact_at_reserve_2_5"] and validation["no_debt_fall_in_deficit"]
    assert validation["runs"] == len(result["validation_sample"]) == 936 and not validation["disagreements"]
    assert validation["reserves"] == [1.0, 2.0, 2.5, 3.0] and validation["demands"] == [0.9, 1.0, 1.1]
    assert validation["max_gap_other_reserves"] <= la.TOLERANCE
    assert result["source"]["reserves_on_the_blood_grid"] == [1.0, 2.5, 3.0]


def test_the_factorization_agrees_again_live(result, setting):
    sample = result["validation_sample"]
    picked = [sample[0], sample[-1]] + [next(r for r in sample if r["reserve"] == 2.0),
                                        next(r for r in sample if r["demand"] == 1.1 and r["scenario"] == la.L3)]
    source, support = setting["source"], setting["support"]
    for item in picked:
        entry = source["p3"][item["q"]]
        unit = (item["q"] if item["scenario"] == la.L3 else entry["p1"] if item["scenario"] == la.L1
                else (entry["p1"], item["support"]))
        key = (item["scenario"], unit, item["case"])
        haemodynamic = _store(setting, key)[setting["tasks"][key]]
        bag = support[item["support"]]["bag"] if item["scenario"] == la.L2 else None
        live = la._validate_one((item, entry, bag, haemodynamic, setting["arrivals"][item["case"]]))
        assert live["agrees"] and live["exact"] == item["exact"] and live["gaps"] == item["gaps"]


def test_the_stages_chain_for_every_demand_and_the_region_is_its_inline_units(result):
    for factor, filtered in result["filter"].items():
        stages = filtered["stages"]
        assert [s["scenario"] for s in stages] == [la.L1, la.L3, la.L2]
        assert stages[0]["entering"] == filtered["candidates"] == 458 * 12 * 1215
        for before, after in zip(stages, stages[1:]):
            assert after["entering"] == before["survivors"]
        assert stages[-1]["survivors"] == filtered["survivors"] == result["demand"]["survivors"][factor]
        assert all(s[la.ANALYTIC_REJECTION] == 0 and s[la.SIMULATION_REJECTION] == s["rejected"] for s in stages)
        assert not any(la.STOPPED in name for s in stages for name in s["any_failure"])
    region = result["region"]
    units = region["inline"]
    assert region["demand"] == 1.0 and region["candidates"] == result["filter"]["1"]["survivors"] == 345_490
    assert len(units) == region["units"] == 7091 and region["status"] == la.REGION_STATUS
    assert sum(len(r) * len(d) for _, _, r, d in units) == region["candidates"]
    assert hashlib.sha256(json.dumps(units, separators=(",", ":")).encode("utf-8")).hexdigest() == region["digest"]
    against = result["against_p2i2ab"]
    assert against["kept"] + against["lost"] == against["p2i2ab"] == 439_291
    assert against["kept"] + against["new"] == against["p2i2ac"] == region["candidates"]


def _chain(result, setting, i, index):
    """The three stages recomputed live at demand 1.0 for one P1 set and lactate-side point."""
    source, support, arrivals = setting["source"], setting["support"], setting["arrivals"]
    children = source["children"][i]

    def trajectories(scenario, unit):
        keys = [(scenario, unit, case) for case in CASES]
        store = _store(setting, *keys)
        return {key[2]: store[setting["tasks"][key]] for key in keys}

    mask = la._l1_unit((i, trajectories(la.L1, i), arrivals, [index], 1.0))[1][index]
    if mask:
        return mask, [], []
    passing = [q for q in children if not la._l3_unit((q, trajectories(la.L3, q), arrivals, [index], 1.0))[1][index]]
    if not passing:
        return 0, [], []
    points = [d for d in range(len(support)) if not la._l2_unit(
        ((i, d), trajectories(la.L2, (i, d)), arrivals, [index], 1.0))[1][index]]
    return 0, passing, points


def test_survivors_and_their_neighbours_are_recomputed_live(result, setting):
    units = result["region"]["inline"]
    region = {(i, index): (r, d) for i, index, r, d in units}
    for i, index, r, d in (units[0], units[-1]):
        mask, passing, points = _chain(result, setting, i, index)
        assert mask == 0 and passing == list(r) and points == list(d)
        for other in (index - 1, index + 1):
            if 0 <= other < len(la.LAMBDAS) and (i, other) not in region:
                mask, passing, points = _chain(result, setting, i, other)
                assert mask or not passing or not points, (i, other)


def test_l3_inadequacy_is_rejected_apart_and_never_passes_as_not_evaluable(result):
    l3 = result["filter"]["1"]["stages"][1]
    assert l3["only_failure"][la.L3_INADEQUATE] == 375_720
    # Read before FD-LAC-04; an inadequate run's FD-LAC-04 is NOT_EVALUABLE, so these FD-LAC-04 failures are adequate ones.
    assert l3["only_failure"]["FD-LAC-04"] == 10_176 and la.BITS[la.L3].index((la.L3_INADEQUATE, CASES[1])) < (
        la.BITS[la.L3].index(("FD-LAC-04", CASES[0])))
    statistics = result["statistics"]
    for case in CASES:
        assert statistics["adequacy_onset"][case] == {"60": 345_490}
        assert statistics["fd04_status"][case] == {fd.PASS: 345_490} and not statistics["fd04_not_evaluable"][case]
    # The one blocker: 72f survivors whose adequacy, restored at 60, lapses before 120 under residual bleeding.
    assert statistics["fd05_status"]["gi_bleed_72f"] == {fd.NOT_EVALUABLE: 1512, fd.PASS: 343_978}
    assert statistics["fd05_not_evaluable"]["gi_bleed_72f"] == {
        "delivery not adequate throughout from T* to 120 min": 1512}
    assert statistics["fd04_and_05_evaluated_in_both_cases"] == 343_978
    assert statistics["fd05_not_evaluable_72f_above_envelope"] == 1008


def test_the_demand_layer_classifies_every_candidate(result):
    demand = result["demand"]
    total = result["filter"]["1"]["candidates"]
    assert sum(demand["classes"].values()) == total
    assert demand["classes"] == {la.ROBUST: 71_079, la.SENSITIVE: 678_007, la.INCOMPATIBLE: 5_928_554}
    assert sum(demand["patterns"].values()) == total - demand["classes"][la.INCOMPATIBLE]
    assert demand["patterns"]["0.9+1+1.1"] == demand["classes"][la.ROBUST]
    assert sum(demand["final_region"].values()) == result["region"]["candidates"]
    for factor, n in demand["survivors"].items():
        assert n == sum(count for key, count in demand["patterns"].items() if factor in key.split("+"))


def test_the_audit_reproduces_the_p2i2ab_flag_and_reads_the_actual_flow(result, setting):
    audit = result["audit"]
    assert audit["reproduced"] and audit["flagged"] == la.P2I2AB_POST_HAEMOSTASIS_DECLINES == 71_661
    assert sum(audit["classes"].values()) == audit["flagged"] == audit["would_violate_fd06"]
    assert audit["violating_residual_old_d"] == 71_661 and audit["violating_residual_old_d_not_flagged"] == 0
    assert audit["violating_residual_corrected_d"] == audit["flagged_violating_residual_corrected_d"] == 120
    units = setting["record"]["region"]["inline"]
    q = units[0][2][0]
    indices = sorted({index for _, index, r, _ in units if q in r})
    keys = [(la.L3, q, case) for case in CASES]
    store = _store(setting, *keys)
    _, readings = la._audit_unit((q, {key[2]: store[setting["tasks"][key]] for key in keys}, setting["arrivals"],
                                  indices))
    for item in readings.values():
        assert item["class"] in la.AUDIT_CLASSES
        assert not item["flagged"] or item["class"] == la.AUDIT_CLASSES[0]


def test_identifiability_follows_the_frozen_rule_and_sits_beside_p2i2ab(result):
    dimensions = result["identifiability"]["dimensions"]
    for name, item in dimensions.items():
        explored, left = item["explored"], item["surviving"]
        expected = (bc.SEPARATELY if name in la.STRUCTURAL else "NOT_VARIED" if len(explored) == 1 else
                    bc.WELL if len(left) == 1 else bc.PARTIAL if len(left) < len(explored) else bc.POOR)
        assert item["status"] == expected, name
        if item["p2i2ab"] is not None:
            before = len(item["p2i2ab"]["surviving"])
            assert item["change"] == ("NARROWER" if len(left) < before else "WIDER" if len(left) > before else "SAME")
    assert "reserve" not in dimensions and "never counted" in result["identifiability"]["rho"]["status"]
    assert dimensions["G x g"]["change"] == "WIDER" and dimensions["demand_factor"]["surviving"] == ["0.9", "1", "1.1"]
    assert not any(item["status"] == bc.WELL for item in dimensions.values())


def test_the_representatives_rerun_live_and_d_never_falls_under_a_read_deficit(result, setting):
    representatives, survivors = result["representatives"], result["region"]["candidates"]
    assert [representatives[t]["pick"]["rank"] for t in ("LOW", "MID", "HIGH")] == [0, survivors // 2, survivors - 1]
    for item in representatives.values():
        for key, run_ in item["runs"].items():
            assert not run_["debt"]["core_read_deficit_with_falling_d"] and run_["debt"]["onset_minutes_only"]
            assert run_["rerun_equals_factorized"] and run_["stop"] is None
            assert not any(run_["flags"][name] for name in ("WORSENING_CRITICAL_WITH_LARGE_LACTATE_FALL",
                                                            "INSTANT_NORMALIZATION", "INCOMPATIBLE_WITH_SURVIVAL"))
            if key.endswith(la.L3):
                assert all(row["bleed_ml_per_min"] > 0.0 for row in run_["rows"])
    pick = representatives["HIGH"]["pick"]
    full = la.full_run(setting["source"]["p3"][pick["p3"]], "gi_bleed_57m", la.L3, la.LAMBDAS[pick["lambda"]])
    rows = representatives["HIGH"]["runs"]["gi_bleed_57m|L3"]["rows"]
    assert [(full["lactate"][m], full["D"][m], full["bleed"][m]) for m in la.TIMES] == [
        (row["lactate"], row["D"], row["bleed_ml_per_min"]) for row in rows]


def test_the_legacy_is_a_reference_and_the_verdict_is_recomputed(result):
    legacy = result["legacy_reference"]
    assert legacy["rule"] == lr.LEGACY_RULE and set(legacy["beside_representatives"]) == {"LOW", "MID", "HIGH"}
    statistics = dict(result["statistics"])
    verdict = la.verdict(True, result["validation"], {"survivors": result["region"]["candidates"],
                                                       "candidates": result["filter"]["1"]["candidates"]},
                         statistics, result["demand"], result["representatives"])
    assert json.loads(json.dumps(verdict)) == result["verdict"]
    assert verdict["verdict"] == f"{la.NOT_READY} — FD-LAC-04 / 05 are met only as NOT_EVALUABLE by some survivors"
    assert verdict["blockers"] == ["FD-LAC-04 / 05 are met only as NOT_EVALUABLE by some survivors"]
    assert verdict["next_domain"] is None
    efficiency = result["efficiency"]
    assert efficiency["haemodynamic_trajectories"] == 3178 and efficiency["analytic_rejections"] == 0
    assert efficiency["naive_core_runs"] == result["filter"]["1"]["candidates"] * 6 * 3


def test_the_document_blocks_are_generated(result):
    from clinical_core import lactate_adequacy_report as report
    text = DOCUMENT.read_text(encoding="utf-8")
    for name, render in report.RENDERERS.items():
        assert report.apply(text, name, render(result)) == text, name
    assert "LACTATE_PHYSIOLOGY_NOT_READY" in text and "345 490" in text and "2a9129e" in text
