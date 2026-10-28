"""Phase 2 shadow core, P2I-2X: case-truth and domain bounds, and the densified common bleed rate.

These tests pin that the faculty constraints and the closed P2I-2V-R / P2I-2W records are unchanged, that the
arrival position is bounded by the committed POCUS-grounded case band (never tightened, never an exact number),
that only the predeclared rates 6-9 are new and nothing else moves, that the exact pre-filter reads only
constraints whose readings do not depend on the rate, that the boundary taxonomy keeps domain and case-truth bounds
apart from identifiability, that HR1 is structural and never clinical case evidence, and that the render-only
reports are strictly downstream of every artifact whose digest leaves them out.
"""
import ast
import hashlib
import json
from pathlib import Path

import pytest

from clinical_core import blood_constraints as bc
from clinical_core import blood_extension as be
from clinical_core import blood_rate_boundary as rb
from clinical_core import calibration, decision_pack, gi_reference, lactate_slice

ROOT = Path(__file__).resolve().parent
#: The P2I-2X freeze: the rate points, the design, the case-truth rule, the taxonomy, the policy and every
#: clinical_core source but the downstream reports, committed before any new rate was evaluated.
FROZEN_DIGEST = "668bad9903da9a4ee1d49a5e2be06f7be7795140091b98d898a169b8682c67a5"
P2I2VR_CONSTRAINTS_SHA = "2d139733ed529a03f9c58cd4aa5eb70c8812bb25ba0737f90172546b4e2a65a8"
P2I2W_EXTENSION_SHA = "87429c2ed0b453bb33b2107fdfa453ffe6d78e5ffbb26364eab7e8228556ce47"
#: clinical_core/blood_rate_boundary.py as committed with that freeze (7f61e2e). P2I-2X is closed (2026-10-28): its
#: record is not regenerated, and the live digest moved when P2I-2Y added clinical_core sources (it has its own).
P2I2X_SCAN_SHA = "435db3cf1d1fdba4e9ff059b889a2e8180ca80db1d2fdbeff433663692ee9f83"


def _sha(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def test_the_faculty_constraints_and_the_closed_records_are_unchanged():
    assert _sha("clinical_core/blood_constraints.py") == P2I2VR_CONSTRAINTS_SHA
    assert _sha("clinical_core/blood_extension.py") == P2I2W_EXTENSION_SHA
    assert be.record()["freeze_digest"] == be.P2I2VR_DIGEST
    assert json.loads(rb.P2I2W_RECORD.read_text(encoding="utf-8"))["freeze_digest"] == rb.P2I2W_DIGEST


def test_the_rate_scan_is_frozen():
    sources = rb.freeze_sources()
    assert {"clinical_core/blood_rate_boundary.py", "clinical_core/blood_constraints.py",
            "clinical_core/lactate_slice.py", "clinical_core/decision_pack.py"} <= set(sources)
    assert not set(rb.DOWNSTREAM_REPORTS) & set(sources)
    # P2I-2X is closed: its module is the frozen one, byte for byte; its record keeps the digest it ran with.
    assert _sha("clinical_core/blood_rate_boundary.py") == P2I2X_SCAN_SHA, "the P2I-2X scan changed after its freeze"


def test_only_the_predeclared_rates_are_new_and_nothing_else_moves():
    assert rb.RATES == (5.0, 6.0, 7.0, 8.0, 9.0, 10.0) and rb.NEW_RATES == (6.0, 7.0, 8.0, 9.0)
    assert all(rate.is_integer() for rate in rb.RATES)
    data = be.record()
    values = rb.region(data)
    assert set(values) == set(be.COORDS) - {be.COMMON}
    for label, kept in values.items():
        assert kept == tuple(be.surviving(data, label)), label
    assert {case: values[be.POSITION[case]] for case in bc.CASES} == {"gi_bleed_57m": (0.5,), "gi_bleed_72f": (0.6,)}
    design = rb.design(data)
    assert design["joint_candidates_per_rate"] == design["shared_combinations"] == 52_488
    assert design["other_positions"] == {"gi_bleed_57m": [0.2, 0.35], "gi_bleed_72f": [0.3, 0.45]}


def test_the_exact_prefilter_reads_only_rate_independent_constraints():
    assert set(rb.RATE_INDEPENDENT) | set(rb.RATE_DEPENDENT) == set(bc.CONSTRAINTS)
    assert not set(rb.RATE_INDEPENDENT) & set(rb.RATE_DEPENDENT) and "FD-BLD-03" not in rb.RATE_INDEPENDENT
    for name in rb.RATE_INDEPENDENT:
        assert bc.BLEED not in bc._depends(name), name
    for name in rb.RATE_DEPENDENT:
        assert bc.BLEED in bc._depends(name), name
    # The retained-crystalloid reading runs with the reference bleeding; blood_constraints.tables cross-checks that it
    # does not depend on the bleeding (P2I-2V-R), and the scan repeats that cross-check on every row it computes.
    assert bc.READS["FD-BLD-04"] == bc.READS["FD-BLD-05"] == "retained" and bc.BLEED not in bc.TABLE_KEYS["retained"]


def test_case_truth_is_the_committed_pocus_grounded_band():
    for case in bc.CASES:
        evidence = rb.case_truth_evidence(case)
        truth = {item["item"]: item for item in evidence["repository_truth"]}
        assert set(truth) == {"pocus_ivc", "pocus_lv"}
        assert all(item["source"].startswith("clinical_cases.py:") for item in truth.values())
        band = evidence["candidate_band"]
        assert (band["lower"], band["upper"]) == (gi_reference.PRELOAD_BANDS[case][0], gi_reference.PRELOAD_BANDS[case][2])
        assert band["status"].startswith("CANDIDATE INFERENCE") and evidence["faculty_decision_required"]
        assert band["upper"] <= evidence["euvolaemic_reference"]["lower"] == 0.6
        lower, upper = rb.case_truth_band(case)
        # The whole committed band stays compatible: no exact position is inferred from POCUS, none is tightened.
        assert all(rb.case_truth_compatible(case, p) for p in (lower, (lower + upper) / 2, upper))
    assert gi_reference.verify_inventory() == []
    assert "pocus" in rb.case_truth_evidence("gi_bleed_57m")["candidate_band"]["rationale"].lower()
    assert not rb.case_truth_compatible("gi_bleed_57m", 0.65) and not rb.case_truth_compatible("gi_bleed_72f", 0.75)
    assert not rb.case_truth_compatible("gi_bleed_57m", 0.8) and not rb.case_truth_compatible("gi_bleed_72f", 0.9)


def test_p2i2w_positions_outside_the_bands_are_rejected_by_case_truth():
    record = json.loads(rb.P2I2W_RECORD.read_text(encoding="utf-8"))
    rejected = rb.p2i2w_case_truth(record)
    with_positions = [name for name, stats in record["boxes"].items()
                      if set(stats["fixed"]) & set(be.POSITION.values())]
    assert sorted(rejected) == sorted(with_positions) and len(rejected) == 29  # 4 alone, 24 pairs, the corner
    assert sum(item["survives"] for item in rejected.values()) == 2268


def test_the_boundary_taxonomy_is_extended_and_apart_from_identifiability():
    assert rb.TAXONOMY == ("INTERIOR", "OPEN_LOWER_GRID_EDGE", "OPEN_UPPER_GRID_EDGE", "OPEN_BOTH_GRID_EDGES",
                           "DOMAIN_LOWER_BOUND", "DOMAIN_UPPER_BOUND", "CASE_TRUTH_BOUND")
    target = "plasma_refill_target_share"
    assert rb.DOMAIN[target][:2] == (0.0, 1.0)
    assert rb.edge(rb.side([0.25, 0.5, 0.75, 1.0], [0.5, 0.75, 1.0], "lower", target, None),
                   rb.side([0.25, 0.5, 0.75, 1.0], [0.5, 0.75, 1.0], "upper", target, None)) == rb.DOMAIN_UPPER
    explored = [0.2, 0.35, 0.5, 0.65, 0.8]
    assert rb.side(explored, [0.5], "upper", bc.POS, "gi_bleed_57m") == "CASE_TRUTH"
    assert rb.edge("CONSTRAINED", "CASE_TRUTH") == rb.CASE_TRUTH_BOUND
    assert rb.edge("CONSTRAINED", "CONSTRAINED") == be.INTERIOR and rb.edge("OPEN", "OPEN") == be.OPEN_BOTH
    assert rb.edge("CONSTRAINED", "OPEN") == be.OPEN_UPPER and rb.edge("OPEN", "CONSTRAINED") == be.OPEN_LOWER
    # 1.0 is the exact domain limit the core enforces: a share above it raises.
    from dataclasses import replace
    from clinical_core.derived import DEFAULT_PROFILE
    from clinical_core.state import CoreInvariantError
    with pytest.raises(CoreInvariantError):
        replace(DEFAULT_PROFILE, plasma_refill_target_share=1.0 + 1e-9)
    replace(DEFAULT_PROFILE, plasma_refill_target_share=1.0)


def test_hr1_is_a_structural_outcome_never_clinical_case_evidence():
    lower = next(c for c in calibration.gi_candidates() if c.preload == "lower")
    assert "not clinical case evidence" in decision_pack.p2f_rejection(lower)
    assert decision_pack.p2f_evidence(lower) == decision_pack.STRUCTURAL_HARNESS_OUTCOME
    assert "clinical case calibration" in calibration.NOT_EVIDENCE_FOR
    assert calibration.LEVEL1_DIRECT_WRITES["HR1-HR4"]["semantics"] == calibration.SYNTHETIC_STATE_PERTURBATION
    # Nothing is readmitted: the structurally admissible design still leaves the lower position out.
    assert not any(c.preload == "lower" for c in decision_pack.admissible())
    # The clinical evidence that still excludes 57m's 0.2 is a faculty constraint: in P2I-2V-R, FD-BLD-02 alone
    # leaves no 57m candidate at the lower position, with or without U-OUT.
    record = be.record()
    assert record["single"]["FD-BLD-02"]["alone_marginal"]["gi_bleed_57m"][bc.POS]["lower"] == 0
    assert record["without"]["U-OUT"]["alone_marginal"]["gi_bleed_57m"][bc.POS]["lower"] == 0
    assert record["single"]["U-OUT"]["alone_marginal"]["gi_bleed_57m"][bc.POS]["lower"] > 0


def test_the_render_only_reports_are_strictly_downstream():
    excluded = {Path(path).stem for path in lactate_slice.DOWNSTREAM_REPORTS}
    assert rb.DOWNSTREAM_REPORTS == lactate_slice.DOWNSTREAM_REPORTS
    for path in sorted((ROOT / "clinical_core").rglob("*.py")):
        relative = path.relative_to(ROOT).as_posix()
        if relative in lactate_slice.DOWNSTREAM_REPORTS:
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name.split(".")[-1] for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [(node.module or "").split(".")[-1]] + [alias.name for alias in node.names]
            assert not excluded & set(names), (relative, excluded & set(names))
    sources = lactate_slice.slice_sources()
    assert not set(lactate_slice.DOWNSTREAM_REPORTS) & set(sources)
    assert "clinical_core/blood_rate_boundary.py" in sources and "clinical_core/blood_constraints.py" in sources
    assert set(decision_pack.PACK_DIGEST_EXCLUDED) >= {"clinical_core/blood_rate_boundary.py",
                                                         "clinical_core/blood_rate_report.py"}



# After the freeze commit: the scan's record -------------------------------------------------------------------------

RESULT = ROOT / "docs" / "revision" / "P2I2X_blood_rate_boundary.json"
DOCUMENT = ROOT / "docs" / "revision" / "P2I2X_CIERRE_BORDES_TASA.md"


def _plain(value):
    return json.loads(json.dumps(value, sort_keys=True, default=str))


@pytest.fixture(scope="module")
def result():
    return json.loads(RESULT.read_text(encoding="utf-8"))


def test_the_scan_record_carries_the_frozen_digest_and_design(result):
    assert result["freeze_digest"] == FROZEN_DIGEST and result["revision"] == "P2I-2X"
    assert result["records"] == {"P2I-2V-R": be.P2I2VR_DIGEST, "P2I-2W": rb.P2I2W_DIGEST}
    assert result["design"] == _plain(rb.design()) and result["policy"] == rb.POLICY
    assert sorted(float(rate) for rate in result["scan"]["rates"]) == list(rb.RATES)
    assert result["contradictions"] == []


def test_the_scan_reproduces_the_records_at_rates_5_and_10(result):
    record = be.record()
    assert result["scan"]["rates"]["5.0"]["survives"] == record["primary"]["marginal"][be.COMMON]["5.0"] == 2268
    p2i2w = json.loads(rb.P2I2W_RECORD.read_text(encoding="utf-8"))
    assert result["scan"]["rates"]["10.0"]["survives"] == p2i2w["boxes"]["bleed_ml_per_min|common=10"]["survives"] == 0


def test_the_scan_counts_are_coherent(result):
    scan = result["scan"]
    for rate, item in scan["rates"].items():
        assert item["candidates"] == scan["candidates"] == 52_488, rate
        assert item["simulated"] == scan["candidates"] - scan["rate_independent_rejected"], rate
        assert item["survives"] + item["rejected"] + item["unreadable"] == item["candidates"], rate
        assert item["survives"] <= min(item["alone"].values()), rate
        assert all(item["u_out_fail"][c] <= item["simulated"] - item["alone"][c] for c in bc.CASES), rate
        assert all(item["u_out_fail"][c] == item["first_failure"][c].get("U-OUT", 0) for c in bc.CASES), rate
    assert sum(scan["rate_independent_first_failure"].values()) == scan["rate_independent_rejected"]
    interval = result["interval"]
    assert interval["label"] == "FACULTY-CONSTRAINED BLEED-RATE CANDIDATE INTERVAL"
    assert interval == _plain(rb.interval(scan))


def test_57m_fails_u_out_at_rate_7_wherever_the_scan_simulates(result):
    """The boundary, recomputed live: among the combinations that pass the exact pre-filter in both cases, every
    untreated reading of 57m at rate 7 leaves U-OUT (read with blood_constraints.untreated directly, not through the
    scan's cache), so no joint candidate survives at 7."""
    import itertools
    values = rb.region()
    positions = {case: values[be.POSITION[case]][0] for case in bc.CASES}
    rows, caches = rb.Rows(), {case: {} for case in bc.CASES}
    kept = set()
    for combination in itertools.product(*(values[n] for n in bc.SHARED)):
        combination = dict(zip(bc.SHARED, combination))
        if not any(rb._independent(rows, case, rb._values(combination, case, 7.0, positions[case]), caches[case])
                   for case in bc.CASES):
            v = rb._values(combination, "gi_bleed_57m", 7.0, positions["gi_bleed_57m"])
            kept.add(tuple(v[n] for n in bc.TABLE_KEYS["untreated"]))
    assert kept and len(kept) == 162
    assert not any(bc.passes("U-OUT", "gi_bleed_57m", bc.untreated("gi_bleed_57m", dict(zip(bc.TABLE_KEYS["untreated"], key))))
                   for key in kept)
    assert result["scan"]["rates"]["7.0"]["u_out_fail"]["gi_bleed_57m"] == result["scan"]["rates"]["7.0"]["simulated"]


def test_the_edges_are_recomputed_and_the_bounds_are_not_identification(result):
    p2i2w = json.loads(rb.P2I2W_RECORD.read_text(encoding="utf-8"))
    assert result["edges"] == _plain(rb.edges(be.record(), p2i2w, result["scan"]))
    edges = result["edges"]
    assert edges["plasma_refill_target_share"]["edge"] == rb.DOMAIN_UPPER
    for case in bc.CASES:
        assert edges[be.POSITION[case]]["edge"] == rb.CASE_TRUTH_BOUND
        assert edges[be.POSITION[case]]["identified"] is False
    assert all(item.get("identified") is not True for item in edges.values() if item.get("edge") != be.INTERIOR)


def test_the_moved_representatives_are_the_frozen_evaluation(result):
    record = be.record()
    for rate, item in result["representatives"].items():
        middle = item["middle"]
        for case in bc.CASES:
            values = {**record["representatives"]["middle"]["values"][case], bc.BLEED: float(rate)}
            values[bc.POS] = be.positions(case)[values[bc.POS]]
            if None in middle["verdicts"][case].values():
                continue
            live = bc.evaluate(case, values)["verdicts"]["primary"]
            assert {n: live[n] for n in bc.CONSTRAINTS} == middle["verdicts"][case], (rate, case)


def test_nothing_is_selected_approved_or_lactate_filtered(result):
    from clinical_core import migration_authority
    text = json.dumps(result)
    assert "FACULTY_APPROVED" not in text and "selected" not in text
    assert migration_authority.APPROVED_FAMILY_DEFAULTS == () and migration_authority.TRUSTED_CASE_MAPPINGS == ()
    import inspect
    source = inspect.getsource(rb)
    assert "lactate_constraints" not in source and "FD-LAC" not in source and "faculty_constraints" not in source


def test_the_document_blocks_are_generated(result):
    from clinical_core import blood_rate_report as report
    document = DOCUMENT.read_text(encoding="utf-8")
    for block, render in (("verdad", report.render_truth), ("tasa", report.render_rate),
                          ("representativos", report.render_representatives), ("bordes", report.render_edges)):
        assert report.apply(document, block, render(result)) == document, block
    assert report.apply(document, "auditoria", report.render_audit()) == document
