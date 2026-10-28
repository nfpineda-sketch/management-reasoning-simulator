"""Phase 2 shadow core, P2I-2Z: the crystalloid tau boundary and the readiness for a current-physiology lactate rebuild.

These tests pin that the faculty constraints and the closed records are unchanged, that the tau extension is the
faculty's one-dimensional design (F0 0.20, Finf 0.05 and 0.10, tau 60, 90 and 120) frozen before evaluation, that
the calibration rule keeps Finf == F0 out of the preferred region, that FD-BLD-06 is read only at P2I-2Y's probes and
the certified blood keys (never a blood x crystalloid product), that the structural checks behind the factorized
lactate design hold, that no lactate filter, legacy trajectory, SBP or MAP enters, and that the new module loads no
family engine.
"""
import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from clinical_core import blood_constraints as bc
from clinical_core import blood_fluid_calibration as fc
from clinical_core import blood_fluid_readiness as fr
from clinical_core import decision_pack, lactate_slice

ROOT = Path(__file__).resolve().parent
#: The P2I-2Z freeze: design, rule, robust criterion, stop rule, structural checks, readiness criteria, input-space
#: rules, policy and every clinical_core source but the downstream reports, committed before any new point ran.
FROZEN_DIGEST = "e89a248ef406acda8c17d95931da98eac9e92d8ab2c1c1fb5bd2e9bf0f20ecf4"
P2I2VR_CONSTRAINTS_SHA = "2d139733ed529a03f9c58cd4aa5eb70c8812bb25ba0737f90172546b4e2a65a8"
P2I2Y_MODULE_SHA = "46e73e3314190dd6fc18695346a16e9c6c55059606ac80a16081695f1d9fdd19"


def _sha(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def test_the_faculty_constraints_and_the_closed_records_are_unchanged():
    assert _sha("clinical_core/blood_constraints.py") == P2I2VR_CONSTRAINTS_SHA
    assert _sha("clinical_core/blood_fluid_calibration.py") == P2I2Y_MODULE_SHA
    assert fr.record_p2i2y()["freeze_digest"] == fr.P2I2Y_DIGEST
    assert bc.DECISIONS["FD-BLD-04"]["envelope"] == (0.15, 0.30)
    assert bc.DECISIONS["FD-BLD-05"]["envelopes"] == {30: (0.15, 0.25), 60: (0.10, 0.20), 120: (0.05, 0.15)}
    assert bc.DECISIONS["FD-BLD-06"]["envelopes"] == {1000: (0.2, 0.5), 2000: (0.4, 0.8)}


def test_the_readiness_analysis_is_frozen():
    sources = fc.freeze_sources()
    assert {"clinical_core/blood_fluid_readiness.py", "clinical_core/blood_constraints.py",
            "clinical_core/interventions/fluids.py", "clinical_core/integration.py"} <= set(sources)
    assert not set(lactate_slice.DOWNSTREAM_REPORTS) & set(sources)
    assert fr.freeze_digest() == FROZEN_DIGEST, "a source, the design, a rule or the policy changed after the freeze"


def test_the_rate_is_the_faculty_record_and_is_not_rescanned():
    assert fr.TESTED_VIABLE_RATE_REGION == fc.TESTED_VIABLE_RATE_REGION == (5.0, 6.0)
    assert fr.FIRST_TESTED_NONVIABLE_RATE == 7.0 and fr.RATE_CLASSIFICATION == "ROBUST_BOUNDARY"
    assert "not FACULTY_APPROVED" in fr.RATE_STATUS
    # U-OUT reads the untreated run, which carries no bag: no crystalloid value can move the rate boundary.
    assert not set(bc.TABLE_KEYS["untreated"]) & set(bc.BAG)
    source = (ROOT / "clinical_core" / "blood_fluid_readiness.py").read_text(encoding="utf-8")
    assert "robustness(" not in source and "ROBUSTNESS_RATES" not in source


def test_the_tau_design_is_one_dimensional_and_the_faculty_s():
    points = fr.design()
    assert len(points) == 6
    assert {p["F0"] for p in points} == {0.20}
    assert {p["Finf"] for p in points} == {0.05, 0.10}
    assert {p["tau"] for p in points} == {60.0, 90.0, 120.0} and fr.NEW_TAU == (90.0, 120.0)
    assert all(p["status"] == fr.ACTIVE for p in points)
    assert fr.GRIDS["tau"] == (15.0, 30.0, 60.0, 90.0, 120.0)
    assert fr.GRIDS["F0"] == fc.F0_GRID and fr.GRIDS["Finf"] == fc.FINF_GRID
    assert set(fr.P2I2Y_ROBUST) == set(fr.record_p2i2y()["counts"]["survivors"]["robust"])


def test_the_calibration_rule_keeps_finf_equal_f0_out_of_the_preferred_region():
    assert fr.calibration_status(0.2, 0.1) == fr.ACTIVE
    assert fr.calibration_status(0.15, 0.15) == fr.REFERENCE_ONLY
    assert fr.calibration_status(0.15, 0.2) == fc.ANALYTIC_REJECTION
    primary = fr.record_p2i2y()["counts"]["survivors"]["primary"]
    reference_only = sorted(k for k in primary if fr.calibration_status(*(float(v) for v in k.split("|")[:2]))
                            == fr.REFERENCE_ONLY)
    assert reference_only == ["0.15|0.15|15", "0.15|0.15|30", "0.15|0.15|60"]
    assert not set(reference_only) & set(fr.P2I2Y_ROBUST)
    assert fr.robust_region({}) == ["0.2|0.1|30"]       # only tau < 60 is carried; 60 and above are re-evaluated


def test_fd_bld_06_reads_only_the_probes_and_the_certified_keys():
    keys = fr.blood_keys(fr.record_p2i2y())
    assert len(keys["probes"]) == 14 and len(set(keys["probes"].values())) == 10
    assert len(keys["certified"]) == 45 and len(keys["all"]) == 48
    assert {k[1] for k in keys["certified"]} == {5.0, 6.0}


def test_the_region_edges_never_identify_at_a_grid_edge():
    open_top = fr.region_edges(["0.2|0.05|60", "0.2|0.1|30", "0.2|0.1|120"])
    assert open_top["tau"]["upper_side"] == "OPEN" and open_top["tau"]["identified"] is False
    assert fr.tau_result({"0.2|0.1|120": {"robust": True}}, open_top)["upper_status"] == "OPEN_UPPER_GRID_EDGE"
    closed = fr.region_edges(["0.2|0.05|60", "0.2|0.1|30", "0.2|0.1|90"])
    assert closed["tau"]["upper_side"] == "CONSTRAINED" and closed["tau"]["lower_side"] == "CONSTRAINED"
    assert fr.tau_result({}, closed)["upper_status"] == "INTERIOR_UPPER_BOUND"


def test_the_structural_checks_hold_on_the_representative_states():
    summary = fr.structural_summary(fr.structural_checks())
    assert summary["lactate_kinetics_post_process_only"]
    assert summary["debt_side_never_reaches_haemodynamics"]
    assert summary["intrinsic_rate_reaches_nothing_read"]
    assert summary["rho_cancels_in_D_and_lactate"] and summary["rho_moves_the_delivery_index"]


def test_no_lactate_filter_legacy_pressure_or_probe_enters():
    tree = ast.parse((ROOT / "clinical_core" / "blood_fluid_readiness.py").read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            imported |= {alias.name for alias in node.names} | {(node.module or "").split(".")[-1]}
        elif isinstance(node, ast.Import):
            imported |= {alias.name.split(".")[-1] for alias in node.names}
    assert not imported & {"lactate_constraints", "faculty_constraints", "legacy_adapter", "family_engine",
                           "lactate_slice", "haemorrhage_probes", "hemodynamic_probes", "oxygen_probes"}
    source = (ROOT / "clinical_core" / "blood_fluid_readiness.py").read_text(encoding="utf-8")
    assert '"sbp"' not in source and '"map"' not in source and "FD-LAC" not in source


def test_the_module_loads_no_family_engine():
    code = ("import sys; import clinical_core.blood_fluid_readiness; "
            "print('family_engine' in sys.modules, 'clinical_core.faculty_constraints' in sys.modules, "
            "'clinical_core.lactate_constraints' in sys.modules)")
    out = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, check=True)
    assert out.stdout.split() == ["False", "False", "False"]


def test_no_active_module_imports_the_historical_probe_modules():
    """P2I-2P, P2I-2Q and P2I-2S are historical records (P2I-2T); the P2I-2Q direct-V haemorrhage probe lives there."""
    historical = {"oxygen_probes", "hemodynamic_probes", "haemorrhage_probes"}     # P2I-2P, 2Q, 2S: records
    for path in sorted((ROOT / "clinical_core").rglob("*.py")):
        if path.stem in historical:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                names = {alias.name for alias in node.names} | {(node.module or "").split(".")[-1]}
            elif isinstance(node, ast.Import):
                names = {alias.name.split(".")[-1] for alias in node.names}
            else:
                continue
            assert not names & historical, path


def test_the_report_stays_downstream():
    assert "clinical_core/blood_fluid_readiness_report.py" in lactate_slice.DOWNSTREAM_REPORTS
    assert {"clinical_core/blood_fluid_readiness.py", "clinical_core/blood_fluid_readiness_report.py"} <= set(
        decision_pack.PACK_DIGEST_EXCLUDED)
    assert "clinical_core/blood_fluid_readiness.py" in lactate_slice.slice_sources()
