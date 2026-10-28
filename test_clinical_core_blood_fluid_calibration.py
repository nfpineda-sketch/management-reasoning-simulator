"""Phase 2 shadow core, P2I-2Y: the crystalloid calibration surface and the targeted bleed-rate robustness check.

These tests pin that the faculty constraints and the closed records are unchanged, that the robustness check
crosses only rates 5-7 with the refill extension over the certified region and the case-compatible positions, that
the crystalloid surface F0 / Finf / tau maps exactly onto the existing contributor with 0 <= Finf <= F0, that the
grid is the faculty's (Finf > F0 rejected analytically), that FD-BLD-06 is read only against predeclared certified
blood probes, and that no lactate, legacy trajectory, SBP, MAP or historical / Level-1 probe enters the inference.
"""
import ast
import hashlib
import json
from pathlib import Path

import pytest

from clinical_core import blood_constraints as bc
from clinical_core import blood_extension as be
from clinical_core import blood_fluid_calibration as fc
from clinical_core import blood_rate_boundary as rb
from clinical_core import decision_pack, lactate_slice

ROOT = Path(__file__).resolve().parent
#: The P2I-2Y freeze: designs, grid, probe and representative rules, policy and every clinical_core source but the
#: downstream reports, committed before any new point was evaluated.
FROZEN_DIGEST = "67e5b80a5a96f526fc2f9e5b2c721026f3ac71ba612fe9cb3e06f23106f4a8d4"
P2I2VR_CONSTRAINTS_SHA = "2d139733ed529a03f9c58cd4aa5eb70c8812bb25ba0737f90172546b4e2a65a8"
P2I2X_SCAN_SHA = "435db3cf1d1fdba4e9ff059b889a2e8180ca80db1d2fdbeff433663692ee9f83"


def _sha(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def test_the_faculty_constraints_and_the_closed_records_are_unchanged():
    assert _sha("clinical_core/blood_constraints.py") == P2I2VR_CONSTRAINTS_SHA
    assert _sha("clinical_core/blood_rate_boundary.py") == P2I2X_SCAN_SHA
    assert json.loads(fc.P2I2X_RECORD.read_text(encoding="utf-8"))["freeze_digest"] == fc.P2I2X_DIGEST
    assert bc.DECISIONS["FD-BLD-04"]["envelope"] == (0.15, 0.30)
    assert bc.DECISIONS["FD-BLD-05"]["envelopes"] == {30: (0.15, 0.25), 60: (0.10, 0.20), 120: (0.05, 0.15)}
    assert bc.DECISIONS["FD-BLD-06"]["envelopes"] == {1000: (0.2, 0.5), 2000: (0.4, 0.8)}


def test_the_fluid_calibration_is_frozen():
    sources = fc.freeze_sources()
    assert {"clinical_core/blood_fluid_calibration.py", "clinical_core/blood_constraints.py",
            "clinical_core/interventions/fluids.py"} <= set(sources)
    assert not set(lactate_slice.DOWNSTREAM_REPORTS) & set(sources)
    assert fc.freeze_digest() == FROZEN_DIGEST, "a source, a design, the grid, a rule or the policy changed after the freeze"


def test_the_rate_record_and_the_robustness_design_stay_targeted():
    assert fc.TESTED_VIABLE_RATE_REGION == (5.0, 6.0) and fc.FIRST_TESTED_NONVIABLE_RATE == 7.0
    design = fc.robustness_design()
    assert design["rates"] == [5.0, 6.0, 7.0]
    assert design["targets"] == [0.5, 0.75, 1.0] and design["taus"] == [120.0, 240.0, 480.0]
    assert len(design["refill_pairs"]) == 9 and len(design["new_refill_pairs"]) == 5
    assert design["positions"] == {"gi_bleed_57m": [0.2, 0.35, 0.5], "gi_bleed_72f": [0.3, 0.45, 0.6]}
    assert all(rb.case_truth_compatible(c, p) for c, ps in design["positions"].items() for p in ps)
    region = fc.robustness_region()["shared"]
    surviving = rb.region()
    for name in bc.SHARED:
        if name not in (fc.TARGET, fc.TAU):
            assert region[name] == surviving[name], name
    assert design["shared_combinations"] == 118_098


def test_the_crystalloid_surface_maps_exactly_and_keeps_finf_within_f0():
    for f0, finf, tau in ((0.3, 0.1, 30.0), (0.15, 0.15, 15.0), (0.2, 0.0, 60.0), (0.35, 0.2, 60.0)):
        values = fc.bag(f0, finf, tau)
        assert values[fc.EFFECTIVE] == f0 and values[fc.LEAK] == tau and 0.0 <= values[fc.TRANSIENT] <= 1.0
        back = fc.surface(values)
        assert back["F0"] == f0 and back["tau"] == tau and back["Finf"] == pytest.approx(finf, abs=1e-12)
    for f0, finf in ((0.15, 0.2), (0.0, 0.0), (1.1, 0.1), (0.2, -0.01)):
        with pytest.raises(ValueError):
            fc.bag(f0, finf, 30.0)
    assert set(fc.bag(0.3, 0.1, 30.0)) == set(bc.BAG)


def test_the_grid_is_the_faculty_s_and_finf_above_f0_is_rejected_analytically():
    assert fc.F0_GRID == (0.15, 0.20, 0.25, 0.30, 0.35)
    assert fc.FINF_GRID == (0.0, 0.05, 0.10, 0.15, 0.20) and fc.TAU_GRID == (15.0, 30.0, 60.0)
    points = fc.grid()
    assert len(points) == 75
    rejected = [p for p in points if p["status"] == fc.ANALYTIC_REJECTION]
    assert [(p["F0"], p["Finf"]) for p in rejected] == [(0.15, 0.2)] * 3
    assert all(p["Finf"] <= p["F0"] + 1e-12 for p in points if p["status"] != fc.ANALYTIC_REJECTION)


def test_only_fd_bld_06_reads_a_blood_state_and_it_reads_only_probes():
    assert bc.READS["FD-BLD-04"] == bc.READS["FD-BLD-05"] == "retained" and bc.READS["FD-BLD-06"] == "crystalloid"
    assert set(bc.TABLE_KEYS["retained"]) == set(bc.BAG)
    assert set(fc.PROBE_KEYS) == set(bc.TABLE_KEYS["crystalloid"]) - set(bc.BAG)
    assert fc.CRYSTALLOID_CONSTRAINTS == ("FD-BLD-04", "FD-BLD-05", "FD-BLD-06")


def test_the_surface_edges_keep_domain_and_grid_apart_from_identifiability():
    edges = fc.surface_edges(["0.2|0|30", "0.25|0.05|30", "0.25|0.05|60"])
    assert edges["Finf"]["lower_side"] == "DOMAIN" and edges["Finf"]["edge"] == rb.DOMAIN_LOWER
    assert edges["F0"]["edge"] == be.INTERIOR and edges["F0"]["class"] == bc.PARTIAL
    assert edges["tau"]["upper_side"] == "OPEN" and edges["tau"]["identified"] is False
    single = fc.surface_edges(["0.35|0.2|60"])
    assert single["F0"]["class"] == bc.WELL and single["F0"]["identified"] is False


def test_no_lactate_legacy_pressure_or_probe_enters_the_inference():
    tree = ast.parse((ROOT / "clinical_core" / "blood_fluid_calibration.py").read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            imported |= {alias.name for alias in node.names} | {(node.module or "").split(".")[-1]}
        elif isinstance(node, ast.Import):
            imported |= {alias.name.split(".")[-1] for alias in node.names}
    assert not imported & {"lactate_constraints", "faculty_constraints", "legacy_adapter", "family_engine", "bands",
                           "calibration", "haemorrhage_probes", "hemodynamic_probes", "oxygen_probes"}
    source = (ROOT / "clinical_core" / "blood_fluid_calibration.py").read_text(encoding="utf-8")
    assert '"sbp"' not in source and '"map"' not in source and '"lactate"' not in source


def test_the_reports_stay_downstream():
    assert "clinical_core/blood_fluid_report.py" in lactate_slice.DOWNSTREAM_REPORTS
    assert {"clinical_core/blood_fluid_calibration.py", "clinical_core/blood_fluid_report.py"} <= set(
        decision_pack.PACK_DIGEST_EXCLUDED)
    assert "clinical_core/blood_fluid_calibration.py" in lactate_slice.slice_sources()
