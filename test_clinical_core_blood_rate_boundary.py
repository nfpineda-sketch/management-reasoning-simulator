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
    assert rb.freeze_digest() == FROZEN_DIGEST, (
        "a clinical_core source, the rates, the design, the case-truth rule or the policy changed after the freeze")


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
    values = {name: kept[0] for name, kept in rb.region().items() if name in bc.SHARED}
    for name in rb.RATE_INDEPENDENT:
        keys = {rate: tuple({**values, bc.BLEED: rate, bc.POS: 0.5}[n] for n in bc._depends(name)) for rate in rb.RATES}
        assert len(set(keys.values())) == 1, "the same reading at every rate"


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

