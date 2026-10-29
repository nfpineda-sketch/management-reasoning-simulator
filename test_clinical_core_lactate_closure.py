"""Phase 2 shadow core, P2I-2AD: final D / lactate semantic closure.

These tests pin the faculty decisions as frozen before evaluation: the P2I-2AB and P2I-2AC records are the committed
ones; D repays only across oxygen-adequate minutes and lactate production reads its own gain, and both are
post-processed exactly as the core computes them (off-grid points only, never a candidate), also at demand 0.9 / 1.1
and over the rho band; the D-to-lactate gain range was built from dimensional consistency, the faculty envelopes and
synthetic probes, crossed with every tau_D; L3 adequacy must persist through 120 and its loss is a rejection of its
own; demand is reported uncertainty; rho is never counted; HR and RR are never read; the P2F region is never read and
the legacy lactate only after the filter; and the filter order, the reporting rules and the verdict rule were frozen
before any count was seen.
"""
import ast
import hashlib
import inspect
import json
import math

import pytest

from clinical_core import blood_constraints as bc
from clinical_core import blood_fluid_calibration as bf
from clinical_core import decision_pack, lactate_slice
from clinical_core import faculty_constraints as fd
from clinical_core import lactate_closure as lc
from clinical_core import lactate_rebuild as lr
from test_clinical_core_lactate_rebuild import OFF_GRID, OFF_GRID_UNIT, full_run_or_inconsistent

ROOT = lc.ROOT
SOURCE = ROOT / "clinical_core" / "lactate_closure.py"
#: The P2I-2AD freeze: faculty decisions, the P2I-2AB and P2I-2AC records, the crossing and coupling factorization, the
#: D-to-lactate gain range, L3 adequacy through 120, demand layer, rho handling, filter order, validation sample,
#: crossing audit, reporting rules, verdict rule, policy and every clinical_core source but the downstream reports,
#: committed before any candidate was evaluated.
FROZEN_DIGEST = "5cb48163da4ff081e752b7684f4b036dbcf3e2acb4f94ee1603aaec742fe7fcf"
#: Closed by P2I-2AE, whose independent debt-to-sympathetic gain changes a core source the freeze digest reads
#: (derived.py): the module and the record are pinned instead, and the live checks read only what P2I-2AE left unchanged
#: (D, lactate, haemodynamics; P2I-2AE touches only the sympathetic drive and the arrival decomposition).
P2I2AD_MODULE_SHA = "2ae56c334031da561a9d402795c1a81ec70646ea15ed0e71cc8b6991bc04dbc3"
FACULTY_CONSTRAINTS_SHA = "092c32cf5a20cbf62e3e9df32a47896ccdef701f97170634740a8f8399d7982a"
CASES = lc.CASES
#: Lactate-side points off every grid: (tau_D, g, D-to-lactate gain, tau_L, excess, arrival debt, arrival delivery);
#: arrival delivery "upper" starts exactly at the critical delivery (the crossing).
OFF_GRID_POINTS = ((45.0, 1.5, 4e-4, 90.0, "upper", "upper", "lower"),
                   (20.0, 3.0, 1.1e-3, 60.0, "lower", "lower", "lower"),
                   (100.0, 0.7, 6e-5, 200.0, "midpoint", "midpoint", "upper"),
                   (75.0, 1.2, 3e-4, 150.0, "lower", "upper", "upper"))


def _sha(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


# The frozen inputs ------------------------------------------------------------------------------------------------

def test_the_records_and_the_faculty_constraints_are_the_committed_ones():
    record = lc.la.record_p2i2ab()
    assert record["freeze_digest"] == lc.la.P2I2AB_DIGEST
    p2i2ac = json.loads(lc.P2I2AC_RECORD.read_text(encoding="utf-8"))
    assert p2i2ac["freeze_digest"] == lc.P2I2AC_DIGEST and p2i2ac["region"]["digest"] == lc.P2I2AC_REGION_DIGEST
    assert _sha("clinical_core/faculty_constraints.py") == FACULTY_CONSTRAINTS_SHA


def test_the_package_is_frozen():
    sources = bf.freeze_sources()
    assert {"clinical_core/lactate_closure.py", "clinical_core/integration.py", "clinical_core/derived.py",
            "clinical_core/lactate_adequacy.py", "clinical_core/faculty_constraints.py"} <= set(sources)
    assert not set(lactate_slice.DOWNSTREAM_REPORTS) & set(sources)
    # P2I-2AE changed the core (the debt-driven drive is debt_to_sympathetic_gain x D): the P2I-2AD module stays byte
    # for byte the frozen one and its record keeps the digest it ran with.
    assert _sha("clinical_core/lactate_closure.py") == P2I2AD_MODULE_SHA, "the P2I-2AD module changed"
    assert json.loads((ROOT / "docs" / "revision" / "P2I2AD_lactate_closure.json").read_text(encoding="utf-8"))[
        "freeze_digest"] == FROZEN_DIGEST


def test_the_faculty_decisions_are_recorded_and_fd_lac_is_unchanged():
    assert set(lc.FACULTY) == {"decided", "l3_adequacy", "debt_repayment", "lactate_coupling", "hr_rr", "demand",
                               "rho", "fd_lac"}
    assert "through minute 120" in lc.FACULTY["l3_adequacy"] and "L3_RESUSCITATION_LOST" in lc.FACULTY["l3_adequacy"]
    assert lc.CAUSAL_PROPAGATION_ACCEPTED in lc.FACULTY["hr_rr"] and lc.MAGNITUDE_PENDING in lc.FACULTY["hr_rr"]
    assert fd.VERSION == "FD-LAC v2" and fd.PRIMARY["fd04_required_fall"] == 0.0 and lc.SETTINGS == fd.PRIMARY
    assert {c: (e["low"], e["high"]) for c, e in fd.ENVELOPES.items()} == {"gi_bleed_57m": (4.4, 7.0),
                                                                          "gi_bleed_72f": (3.4, 5.5)}
    assert {c: (e["low"], e["high"]) for c, e in fd.ENVELOPES_120.items()} == {"gi_bleed_57m": (1.5, 4.0),
                                                                              "gi_bleed_72f": (1.2, 3.5)}


# The D-to-lactate gain ---------------------------------------------------------------------------------------------

def test_the_old_gain_range_is_declared_invalid_and_the_new_range_follows_its_rule():
    design = lc.k_ld_design()
    assert design["old_status"] == lc.OLD_G_RANGE_STATUS == "OLD_G_RANGE_SEMANTICALLY_INVALID"
    assert design["low"] == 0.1 / (60 * 60.0) and design["high"] == 2.6 / (60 * 20.0)
    points = design["points"]
    assert len(points) == 5 and points[0] == design["low"] and points[-1] == design["high"]
    ratios = [b / a for a, b in zip(points, points[1:])]
    assert max(ratios) - min(ratios) < 1e-12 and ratios[0] == pytest.approx((design["high"] / design["low"]) ** 0.25)
    assert lc.K_LD == points and points[0] < design["default"] < points[-1]
    # Never derived from tau_D: the rule reads the envelopes and the arrival-debt band, and the grid crosses every tau_D
    # with every gain.
    body = inspect.getsource(lc.k_ld_design).split('"""')[-1].split("old = ")[0]
    assert "debt_clearance_tau_min" not in body and "lactate_clearance_tau_min" not in body
    assert {(p[0], p[2]) for p in lc.LAMBDAS} == {(t, k) for t in (30.0, 60.0, 120.0) for k in points}
    assert len(lc.LAMBDAS) == 3 * 3 * 5 * 3 * 3 * 5


def test_the_coupling_no_longer_reads_tau_d():
    """The record's coupling check, and what of it still runs live. Its probe arrival (the neutral one with a debt of
    20 and no intrinsic rate declared) carries no sympathetic share, so since P2I-2AE its debt would need a negative
    one and the core stops it; test_clinical_core_lactate_coupling reruns the same probe on a consistent arrival."""
    record = json.loads((ROOT / "docs" / "revision" / "P2I2AD_lactate_closure.json").read_text(encoding="utf-8"))
    check = record["coupling"]
    assert check["independent"] and check["tau_d_invariant_probe"] and check["cartesian_tau_d_by_gain"]
    body = inspect.getsource(lc.derived.lactate_after_minute).split('"""')[-1]
    assert {name: name in body for name in check["reads"]} == check["reads"] == {
        "debt_to_lactate_gain": True, "debt_clearance_tau_min": False, "lactate_per_output_deficit": False}
    assert {(p[0], p[2]) for p in lc.LAMBDAS} == {(t, k) for t in (30.0, 60.0, 120.0) for k in lc.K_LD}
    assert "tau_d" not in inspect.signature(lc.lactate_series).parameters
    with pytest.raises(lc.derived.CoreInvariantError, match="negative sympathetic contribution"):
        lc.coupling_check()


# The corrected D and lactate, post-processed (off-grid points only) -----------------------------------------------

@pytest.mark.parametrize("scenario", [lc.L1, lc.L2, lc.L3])
def test_d_and_lactate_post_process_exactly_as_the_core_on_off_grid_points(scenario):
    """No candidate: blood, crystalloid and lactate-side points off every grid, two of them starting at the critical
    delivery. Exact at reserve 2.5 for any intrinsic rate and demand 0.9 / 1.0 / 1.1; within 1e-9 with identical
    verdicts at reserve 2.0, 3.0 and the synthetic reference 1. D falls only across deficit-free minutes."""
    arrivals = lr.arrival_table()
    entry = {**OFF_GRID, **OFF_GRID_UNIT}
    bag = bf.bag(0.22, 0.07, 75.0) if scenario == lc.L2 else None
    variants = [(lc.RESERVE, "midpoint", f) for f in lc.DEMAND_FACTORS] + [
        (lc.RESERVE, level, 1.0) for level in ("lower", "upper")] + [
        (r, "midpoint", 1.0) for r in (*lc.RHO_BAND, lc.RHO_SYNTHETIC_REFERENCE)]
    crossings = 0
    for case in CASES:
        _, haemodynamic = lc.la._haemodynamic(lr.haemodynamic_task(
            case, scenario, lr.blood_values(entry if scenario == lc.L3 else OFF_GRID, case, bag)))
        for point in OFF_GRID_POINTS:
            context = lc.context_of(haemodynamic, arrivals[case]["ratio"][point[6]])
            crossings += sum(1 for s, e in zip(context.debt_input, context.end_deficit) if s == 0.0 and e > 0.0)
            for reserve, intrinsic, factor in variants:
                full = full_run_or_inconsistent(lambda: lc.full_run(entry, case, scenario, point, bag, reserve,
                                                                    intrinsic, factor), case, intrinsic, point[5])
                if full is None:
                    continue
                result = lc.compare(full, lc.factorized(haemodynamic, arrivals[case], point, factor), haemodynamic,
                                    case, scenario, point, reserve)
                assert result["agrees"] and result["debt_coherent"], (case, point, reserve, factor, result)
                if reserve == lc.RESERVE:
                    assert result["exact"]
    if scenario != lc.L3:
        assert crossings, "the probe exercises the crossing rule"


def test_the_debt_series_repays_only_across_deficit_free_minutes():
    starts = [0.0, 0.2, 0.0, 0.0, 0.1, 0.0]
    ends = [0.0, 0.0, 0.3, 0.0, 0.0, 0.0]
    series = lc.debt_series(starts, ends, 10.0, 50.0, 2.0)
    expected = [10.0]
    for start, end in zip(starts, ends):
        d = expected[-1]
        expected.append(d + 2.0 * start if start > 0.0 else d - d / 50.0 if end == 0.0 else d)
    assert series == expected and series[3] == series[2], "the crossing minute keeps D"
    assert min(lc.debt_series([0.0] * 400, [0.0] * 400, 3.0, 1.0, 1.0)) == 0.0
    # Only k x g and k x D0 reach lactate.
    path = [0.1 + 0.002 * m for m in range(120)]
    a = lc.lactate_series(lc.debt_series(path, path, 20.0, 60.0, 2.0), 0.4, 6e-4, 120.0, 1.0, 0.8)
    b = lc.lactate_series(lc.debt_series(path, path, 10.0, 60.0, 1.0), 0.4, 1.2e-3, 120.0, 1.0, 0.8)
    assert lr._gap(a, b) <= 1e-12


# L3 adequacy through 120 ------------------------------------------------------------------------------------------

def _context(*zero_spans, length=121):
    zero = {m for first, last in zero_spans for m in range(first, last + 1)}
    delivery = [0.5 if m in zero else 0.2 for m in range(length)]
    return lc.Context(delivery, [1.0] * length, [0.25] * length, 60, None)


@pytest.mark.parametrize("spans, status, onset, lost", [
    (((60, 120),), lc.L3_ADEQUATE, 60, None),
    (((30, 120),), lc.L3_ADEQUATE, 60, None),
    (((75, 120),), lc.L3_ADEQUATE, 75, None),
    (((90, 120),), lc.L3_ADEQUATE, 90, None),
    (((60, 100),), lc.L3_LOST, 60, 101),
    (((40, 75), (80, 120)), lc.L3_LOST, 60, 76),
    (((91, 120),), lc.L3_INADEQUATE, None, None),
    (((40, 59),), lc.L3_INADEQUATE, None, None),
    ((), lc.L3_INADEQUATE, None, None),
])
def test_l3_adequacy_must_persist_through_120(spans, status, onset, lost):
    reading = _context(*spans).adequacy
    assert (reading["status"], reading["onset"], reading["lost_at"]) == (status, onset, lost)


def test_l3_inadequacy_and_loss_are_rejections_of_their_own_and_never_pass_as_not_evaluable():
    assert lc.BITS[lc.L3][:4] == ((lc.L3_INADEQUATE, CASES[0]), (lc.L3_INADEQUATE, CASES[1]),
                                  (lc.L3_LOST, CASES[0]), (lc.L3_LOST, CASES[1]))
    source = inspect.getsource(lc._l3_unit)
    assert "_bit(L3, L3_LOST, case) if status == L3_LOST" in source
    assert 'response["status"] == fd.FAIL' in source and 'residual["status"] == fd.FAIL' in source
    # An adequate-through-120 run always has FD-LAC-04 and 05 evaluable.
    context = _context((60, 120))
    lactate = [5.0 - 0.02 * m for m in range(121)]
    response, residual = lc.fd_lac_04_05(lactate, [0.0] * 121, context, lc.CANONICAL, CASES[0])
    assert response["status"] != fd.NOT_EVALUABLE and residual["status"] != fd.NOT_EVALUABLE
    lost = _context((60, 100))
    response, residual = lc.fd_lac_04_05(lactate, [0.0] * 121, lost, lc.CANONICAL, CASES[0])
    assert residual["status"] == fd.NOT_EVALUABLE and lost.adequacy["status"] == lc.L3_LOST
    stage = lc.Stage(lc.L3)
    stage.add(1 << lc.BITS[lc.L3].index((lc.L3_LOST, CASES[1])), 4)
    assert stage.report()["only_failure"] == {lc.L3_LOST: 4} and stage.report()["survivors"] == 0


# Demand, rho, HR / RR -----------------------------------------------------------------------------------------------

def test_demand_is_reported_uncertainty_never_a_filter():
    assert lc.DEMAND_FACTORS[0] == lc.PRIMARY_DEMAND == 1.0 and set(lc.DEMAND_FACTORS) == {0.9, 1.0, 1.1}
    source = inspect.getsource(lc.run)
    assert "region_record(primary)" in source and "primary = filtered[PRIMARY_DEMAND]" in source
    units = {1.0: [(0, 3, (0,), (0, 1))], 0.9: [(0, 3, (0,), (0,))], 1.1: [(0, 4, (0,), (1,))]}
    layer = lc.demand_layer({f: {"units": u} for f, u in units.items()}, 2, 10)
    assert layer["classes"] == {lc.ROBUST: 0, lc.SENSITIVE: 3, lc.INCOMPATIBLE: 7}
    assert set(layer["classes"]) == {"ROBUST_ACROSS_DEMAND", "DEMAND_SENSITIVE", "DEMAND_INCOMPATIBLE"}


def test_rho_is_never_counted_and_hr_rr_are_never_read():
    assert lc.RHO_BAND == (2.0, 3.0) and lc.RESERVE == 2.5 and lc.RHO_SYNTHETIC_REFERENCE == 1.0
    assert "reserve" not in lc.STRUCTURAL and "reserves" not in inspect.getsource(lc.identifiability)
    text = SOURCE.read_text(encoding="utf-8")
    assert "pulse_rate" not in text and "respiratory_rate" not in text and '"sbp"' not in text and '"map"' not in text


# Guards, the legacy lactate, approvals ---------------------------------------------------------------------------

def _tree():
    return ast.parse(SOURCE.read_text(encoding="utf-8"))


def test_the_p2f_region_is_never_read_and_the_legacy_only_after_the_filter():
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
    source = inspect.getsource(lc.run)
    assert "with lr.P2FGuard(), lr.LegacyLock():" in source
    assert source.index("lr.legacy_reference(") > source.index("with lr.P2FGuard(), lr.LegacyLock():")
    readers = set()
    for function in (n for n in ast.walk(_tree()) if isinstance(n, ast.FunctionDef)):
        for node in ast.walk(function):
            if isinstance(node, ast.Attribute) and node.attr in ("_legacy_run", "snapshots", "legacy_reference"):
                readers.add(function.name)
    assert readers == {"run"}


def test_the_verdict_rule_reads_every_faculty_condition():
    validation = {"agree": True, "debt_coherent": True}
    coupling = {"independent": True}
    crossing = {"affected_new": 0}
    run_ = {"debt": {"falls_outside_adequate_minutes": [], "critical_minutes_below_arrival": 0},
            "rerun_equals_factorized": True, "flags": {name: False for name in lr.FLAG_RULES}}
    reviewed = {"LOW": {"runs": {f"{c}|{s}": run_ for c in CASES for s in (lc.L1, lc.L3)}}}
    statistics = {"adequacy": {c: {lc.L3_ADEQUATE: 3} for c in CASES}, "fd04_and_05_evaluated_in_both_cases": 3,
                  "trigger_is_adequacy_onset": 3, "debt_incoherent_l3": 0}
    demand = {"classes": {lc.ROBUST: 3, lc.SENSITIVE: 1, lc.INCOMPATIBLE: 6}}
    filtered = {"survivors": 3, "candidates": 10}
    good = lc.verdict(validation, coupling, crossing, filtered, statistics, demand, reviewed)
    assert good["verdict"] == lc.READY == "LACTATE_PHYSIOLOGY_READY_FOR_HR_DOMAIN" and good["next_domain"]
    for broken, why in (({**statistics, "fd04_and_05_evaluated_in_both_cases": 2}, "FD-LAC-04 / 05"),
                        ({**statistics, "adequacy": {CASES[0]: {lc.L3_ADEQUATE: 2, lc.L3_LOST: 1},
                                                     CASES[1]: {lc.L3_ADEQUATE: 3}}}, "loses L3 adequacy"),
                        ({**statistics, "trigger_is_adequacy_onset": 2}, "T*")):
        assert why in lc.verdict(validation, coupling, crossing, filtered, broken, demand, reviewed)["verdict"]
    assert "repays during a critical" in lc.verdict(validation, coupling, {"affected_new": 1}, filtered, statistics,
                                                    demand, reviewed)["verdict"]
    assert "tau_D" in lc.verdict(validation, {"independent": False}, crossing, filtered, statistics, demand,
                                 reviewed)["verdict"]
    assert lc.verdict(validation, coupling, crossing, {"survivors": 0, "candidates": 10}, None, demand,
                      reviewed)["next_domain"] is None
    assert "not started" in lc.NEXT_DOMAIN and lc.NEXT_DOMAIN.index("heart rate") < lc.NEXT_DOMAIN.index("pressure")
    assert "Unique identification of hidden parameters is not required" in lc.VERDICT_RULE


def test_nothing_is_selected_or_approved_and_the_report_stays_downstream():
    text = SOURCE.read_text(encoding="utf-8")
    assert "FACULTY_APPROVED" not in text
    assert "no value selected or approved" in lc.REGION_STATUS and "No candidate, value or parameter" in lc.VERDICT_RULE
    assert "Nothing is fitted, selected or approved" in lc.POLICY
    assert "clinical_core/lactate_closure_report.py" in lactate_slice.DOWNSTREAM_REPORTS
    assert {"clinical_core/lactate_closure.py", "clinical_core/lactate_closure_report.py"} <= set(
        decision_pack.PACK_DIGEST_EXCLUDED)


def test_the_validation_sample_covers_the_demand_factors_and_the_rho_band():
    record = lc.la.record_p2i2ab()
    sample = lc.validation_sample(lc.la.source_space(record), record["crystalloid_support"])
    canonical = lc.LAMBDAS.index(lc.CANONICAL)
    assert {s["scenario"] for s in sample} == {lc.L1, lc.L2, lc.L3}
    assert {s["reserve"] for s in sample} == {1.0, 2.0, 2.5, 3.0} and {s["demand"] for s in sample} == {0.9, 1.0, 1.1}
    assert all(s["lambda"] == canonical for s in sample if (s["reserve"], s["intrinsic"], s["demand"]) != (
        lc.RESERVE, "midpoint", 1.0))
    assert len(sample) == 936 and bc.SEPARATELY == "NON_IDENTIFIABLE_SEPARATELY" and math.isfinite(lc.K_LD[2])


# After the freeze: the analysis's record ----------------------------------------------------------------------------

RESULT = ROOT / "docs" / "revision" / "P2I2AD_lactate_closure.json"
DOCUMENT = ROOT / "docs" / "revision" / "P2I2AD_CIERRE_DEUDA_LACTATO.md"


@pytest.fixture(scope="module")
def result():
    return json.loads(RESULT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def setting():
    record = lc.la.record_p2i2ab()
    source, support = lc.la.source_space(record), record["crystalloid_support"]
    return {"record": record, "source": source, "support": support, "arrivals": lr.arrival_table(),
            "tasks": lc.haemodynamic_tasks(source, support), "store": {}}


def _store(setting, *keys):
    tasks, store = setting["tasks"], setting["store"]
    for key in keys:
        if tasks[key] not in store:
            store[tasks[key]] = lc.la._haemodynamic(tasks[key])[1]
    return store


def _trajectories(setting, scenario, unit):
    keys = [(scenario, unit, case) for case in CASES]
    store = _store(setting, *keys)
    return {key[2]: store[setting["tasks"][key]] for key in keys}


def test_the_record_carries_the_frozen_digest_the_validation_and_the_coupling(result):
    assert result["freeze_digest"] == FROZEN_DIGEST and result["revision"] == "P2I-2AD"
    assert result["records"] == {"P2I-2AB": lc.la.P2I2AB_DIGEST, "P2I-2AC": lc.P2I2AC_DIGEST}
    assert result["faculty"] == lc.FACULTY and result["coupling"]["independent"]
    validation = result["validation"]
    assert validation["agree"] and validation["exact_at_reserve_2_5"] and validation["debt_coherent"]
    assert validation["runs"] == len(result["validation_sample"]) == 936 and not validation["disagreements"]
    assert validation["reserves"] == [1.0, 2.0, 2.5, 3.0] and validation["demands"] == [0.9, 1.0, 1.1]
    assert validation["max_gap_other_reserves"] <= lc.TOLERANCE
    assert result["k_ld"]["points"] == list(lc.K_LD) and result["k_ld"]["old_status"] == lc.OLD_G_RANGE_STATUS
    assert result["hr_rr"] == {"status": [lc.CAUSAL_PROPAGATION_ACCEPTED, lc.MAGNITUDE_PENDING], "calibrated": False,
                               "historical_hr1_target": False}


def test_the_factorization_agrees_again_live(result, setting):
    sample = result["validation_sample"]
    picked = [sample[0], sample[-1]] + [next(r for r in sample if r["reserve"] == 2.0),
                                        next(r for r in sample if r["demand"] == 1.1 and r["scenario"] == lc.L3)]
    source, support = setting["source"], setting["support"]
    for item in picked:
        entry = source["p3"][item["q"]]
        unit = (item["q"] if item["scenario"] == lc.L3 else entry["p1"] if item["scenario"] == lc.L1
                else (entry["p1"], item["support"]))
        key = (item["scenario"], unit, item["case"])
        haemodynamic = _store(setting, key)[setting["tasks"][key]]
        bag = support[item["support"]]["bag"] if item["scenario"] == lc.L2 else None
        live = lc._validate_one((item, entry, bag, haemodynamic, setting["arrivals"][item["case"]]))
        assert live["agrees"] and live["exact"] == item["exact"] and live["gaps"] == item["gaps"]


def test_the_stages_chain_for_every_demand_and_the_region_is_its_inline_units(result):
    for factor, filtered in result["filter"].items():
        stages = filtered["stages"]
        assert [s["scenario"] for s in stages] == [lc.L1, lc.L3, lc.L2]
        assert stages[0]["entering"] == filtered["candidates"] == 458 * 12 * 2025
        for before, after in zip(stages, stages[1:]):
            assert after["entering"] == before["survivors"]
        assert stages[-1]["survivors"] == filtered["survivors"] == result["demand"]["survivors"][factor]
        assert all(s[lc.ANALYTIC_REJECTION] == 0 and s[lc.SIMULATION_REJECTION] == s["rejected"] for s in stages)
        assert not any(lc.STOPPED in name for s in stages for name in s["any_failure"])
    region = result["region"]
    units = region["inline"]
    assert region["demand"] == 1.0 and region["candidates"] == result["filter"]["1"]["survivors"] == 353_302
    assert len(units) == region["units"] == 7128 and region["status"] == lc.REGION_STATUS
    assert sum(len(r) * len(d) for _, _, r, d in units) == region["candidates"]
    assert hashlib.sha256(json.dumps(units, separators=(",", ":")).encode("utf-8")).hexdigest() == region["digest"]


def _chain(setting, i, index):
    source, support, arrivals = setting["source"], setting["support"], setting["arrivals"]
    mask = lc._l1_unit((i, _trajectories(setting, lc.L1, i), arrivals, [index], 1.0))[1][index]
    if mask:
        return mask, [], []
    passing = [q for q in source["children"][i]
               if not lc._l3_unit((q, _trajectories(setting, lc.L3, q), arrivals, [index], 1.0))[1][index]]
    if not passing:
        return 0, [], []
    points = [d for d in range(len(support)) if not lc._l2_unit(
        ((i, d), _trajectories(setting, lc.L2, (i, d)), arrivals, [index], 1.0))[1][index]]
    return 0, passing, points


def test_survivors_and_their_neighbours_are_recomputed_live(result, setting):
    units = result["region"]["inline"]
    region = {(i, index): (r, d) for i, index, r, d in units}
    for i, index, r, d in (units[0], units[-1]):
        mask, passing, points = _chain(setting, i, index)
        assert mask == 0 and passing == list(r) and points == list(d)
        for other in (index - 1, index + 1):
            if 0 <= other < len(lc.LAMBDAS) and (i, other) not in region:
                mask, passing, points = _chain(setting, i, other)
                assert mask or not passing or not points, (i, other)


def test_every_l3_survivor_stays_adequate_through_120_with_fd_lac_04_05_evaluated(result):
    survivors, statistics = result["region"]["candidates"], result["statistics"]
    for case in CASES:
        assert statistics["adequacy"][case] == {lc.L3_ADEQUATE: survivors}
        assert statistics["fd04_status"][case] == {fd.PASS: survivors}
        assert statistics["fd05_status"][case] == {fd.PASS: survivors}
    assert statistics["fd04_and_05_evaluated_in_both_cases"] == statistics["trigger_is_adequacy_onset"] == survivors
    assert statistics["debt_incoherent_l3"] == 0
    l3 = result["filter"]["1"]["stages"][1]
    assert l3["any_failure"][f"{lc.L3_LOST} gi_bleed_72f"] == 9396 and l3["only_failure"][lc.L3_LOST] == 1476
    assert l3["only_failure"][lc.L3_INADEQUATE] == 377_844


def test_the_demand_layer_classifies_every_candidate(result):
    demand, total = result["demand"], result["filter"]["1"]["candidates"]
    assert sum(demand["classes"].values()) == total
    assert demand["classes"] == {lc.ROBUST: 63_859, lc.SENSITIVE: 673_381, lc.INCOMPATIBLE: 10_392_160}
    assert sum(demand["final_region"].values()) == result["region"]["candidates"]
    for factor, n in demand["survivors"].items():
        assert n == sum(count for key, count in demand["patterns"].items() if factor in key.split("+"))


def test_the_crossing_audit_clears_the_p2i2ac_arrivals_at_the_tie(result, setting):
    crossing = result["crossing"]
    assert crossing["region"] == 345_490 and crossing["upper_delivery"] == crossing["upper_affected_old"] == 95_698
    assert crossing["affected_old"] == 95_698 and crossing["max_minutes_old"] == 63
    assert crossing["affected_new"] == crossing["upper_affected_new"] == crossing["max_minutes_new"] == 0
    units = json.loads(lc.P2I2AC_RECORD.read_text(encoding="utf-8"))["region"]["inline"]
    i = units[0][0]
    indices = sorted({index for p1, index, _, _ in units if p1 == i})
    _, readings = lc._crossing_unit((i, _trajectories(setting, lc.L1, i), setting["arrivals"], indices))
    assert all(new == 0 for _, new in readings.values())
    assert all(old >= 2 for (index, _), (old, _) in readings.items() if lr.LAMBDAS[index][6] == "upper")


def test_identifiability_follows_the_frozen_rule(result):
    dimensions = result["identifiability"]["dimensions"]
    for name, item in dimensions.items():
        explored, left = item["explored"], item["surviving"]
        expected = (bc.SEPARATELY if name in lc.STRUCTURAL else "NOT_VARIED" if len(explored) == 1 else
                    bc.WELL if len(left) == 1 else bc.PARTIAL if len(left) < len(explored) else bc.POOR)
        assert item["status"] == expected, name
    assert "reserve" not in dimensions and not any(item["status"] == bc.WELL for item in dimensions.values())
    assert dimensions["debt_to_lactate_gain"]["edge"] == "OPEN_UPPER_GRID_EDGE"
    assert dimensions["arrival_oxygen_debt"]["status"] == bc.SEPARATELY
    assert set(result["identifiability"]["parameter_semantics"]) == set(lc.PARAMETER_SEMANTICS)


def test_the_representatives_rerun_live_and_never_repay_during_a_critical_interval(result, setting):
    representatives, survivors = result["representatives"], result["region"]["candidates"]
    assert [representatives[t]["pick"]["rank"] for t in ("LOW", "MID", "HIGH")] == [0, survivors // 2, survivors - 1]
    for item in representatives.values():
        for key, run_ in item["runs"].items():
            assert not run_["debt"]["falls_outside_adequate_minutes"]
            assert run_["debt"]["critical_minutes_below_arrival"] == 0
            assert run_["rerun_equals_factorized"] and run_["stop"] is None
            assert not any(run_["flags"][name] for name in ("WORSENING_CRITICAL_WITH_LARGE_LACTATE_FALL",
                                                            "INSTANT_NORMALIZATION", "INCOMPATIBLE_WITH_SURVIVAL"))
            if key.endswith(lc.L3):
                assert run_["debt"]["l3_adequacy"]["status"] == lc.L3_ADEQUATE
    pick = representatives["HIGH"]["pick"]
    full = lc.full_run(setting["source"]["p3"][pick["p3"]], "gi_bleed_57m", lc.L3, lc.LAMBDAS[pick["lambda"]])
    rows = representatives["HIGH"]["runs"]["gi_bleed_57m|L3"]["rows"]
    assert [(full["lactate"][m], full["D"][m], full["bleed"][m]) for m in lc.TIMES] == [
        (row["lactate"], row["D"], row["bleed_ml_per_min"]) for row in rows]


def test_the_legacy_is_a_reference_and_the_verdict_is_recomputed(result):
    legacy = result["legacy_reference"]
    assert legacy["rule"] == lr.LEGACY_RULE and set(legacy["beside_representatives"]) == {"LOW", "MID", "HIGH"}
    verdict = lc.verdict(result["validation"], result["coupling"], result["crossing"],
                         {"survivors": result["region"]["candidates"], "candidates": result["filter"]["1"]["candidates"]},
                         result["statistics"], result["demand"], result["representatives"])
    assert json.loads(json.dumps(verdict)) == result["verdict"]
    assert verdict["verdict"] == lc.READY and not verdict["blockers"] and verdict["next_domain"] == lc.NEXT_DOMAIN
    efficiency = result["efficiency"]
    assert efficiency["haemodynamic_trajectories"] == 3178 and efficiency["analytic_rejections"] == 0
    assert efficiency["naive_core_runs"] == result["filter"]["1"]["candidates"] * 6 * 3


def test_the_document_blocks_are_generated(result):
    from clinical_core import lactate_closure_report as report
    text = DOCUMENT.read_text(encoding="utf-8")
    for name, render in report.RENDERERS.items():
        assert report.apply(text, name, render(result)) == text, name
    assert "LACTATE_PHYSIOLOGY_READY_FOR_HR_DOMAIN" in text and "353 302" in text and "c9647c8" in text


def test_a_lost_l3_unit_also_post_processes_exactly_as_the_core(setting):
    """Review finding: the frozen validation sample saw no L3_RESUSCITATION_LOST run. One from the region's own L3 space
    (P3 set 59, 72f, arrival delivery lower: adequate at 60, a deficit again at 101) agrees with full core runs too."""
    entry, case = setting["source"]["p3"][59], "gi_bleed_72f"
    haemodynamic = _trajectories(setting, lc.L3, 59)[case]
    point = lc.LAMBDAS[767]
    assert point[6] == "lower"
    for reserve, factor in ((lc.RESERVE, 1.0), (lc.RESERVE, 0.9), (lc.RESERVE, 1.1), (2.0, 1.0), (3.0, 1.0)):
        full = lc.full_run(entry, case, lc.L3, point, None, reserve, "midpoint", factor)
        factorized = lc.factorized(haemodynamic, setting["arrivals"][case], point, factor)
        result = lc.compare(full, factorized, haemodynamic, case, lc.L3, point, reserve)
        assert result["agrees"] and (result["exact"] or reserve != lc.RESERVE), (reserve, factor, result)
        if factor == 1.0:
            assert result["verdicts"]["L3 adequacy"] == lc.L3_LOST and result["verdicts"]["lost_at"] == 101
