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
from test_clinical_core_lactate_rebuild import OFF_GRID, OFF_GRID_UNIT

ROOT = lc.ROOT
SOURCE = ROOT / "clinical_core" / "lactate_closure.py"
#: The P2I-2AD freeze: faculty decisions, the P2I-2AB and P2I-2AC records, the crossing and coupling factorization, the
#: D-to-lactate gain range, L3 adequacy through 120, demand layer, rho handling, filter order, validation sample,
#: crossing audit, reporting rules, verdict rule, policy and every clinical_core source but the downstream reports,
#: committed before any candidate was evaluated.
FROZEN_DIGEST = "5cb48163da4ff081e752b7684f4b036dbcf3e2acb4f94ee1603aaec742fe7fcf"
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
    assert lc.freeze_digest() == FROZEN_DIGEST, "a source, the design, a rule or the policy changed after the freeze"


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
    check = lc.coupling_check()
    assert check["independent"] and check["tau_d_invariant_probe"] and check["cartesian_tau_d_by_gain"]
    assert check["reads"] == {"debt_to_lactate_gain": True, "debt_clearance_tau_min": False,
                              "lactate_per_output_deficit": False}
    assert "tau_d" not in inspect.signature(lc.lactate_series).parameters


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
                full = lc.full_run(entry, case, scenario, point, bag, reserve, intrinsic, factor)
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
