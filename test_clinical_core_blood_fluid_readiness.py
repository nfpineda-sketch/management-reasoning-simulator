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
#: The module as frozen at a927301 (P2I-2Z closed: later packages add modules, so the digest is the record's).
P2I2Z_MODULE_SHA = "40b93a69c8b70190e7d92a056f0987b81a30ee32331629d18132f0aa534a15cf"


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
    # P2I-2Z is closed: its module is the frozen one, byte for byte; its record keeps the digest it ran with.
    assert _sha("clinical_core/blood_fluid_readiness.py") == P2I2Z_MODULE_SHA, "the P2I-2Z module changed"
    record = json.loads((ROOT / "docs" / "revision" / "P2I2Z_blood_fluid_readiness.json").read_text(encoding="utf-8"))
    assert record["freeze_digest"] == FROZEN_DIGEST


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


# After the freeze commit: the analysis's record --------------------------------------------------------------------

RESULT = ROOT / "docs" / "revision" / "P2I2Z_blood_fluid_readiness.json"
DOCUMENT = ROOT / "docs" / "revision" / "P2I2Z_TAU_Y_PREPARACION_LACTATO.md"


def _plain(value):
    return json.loads(json.dumps(value, sort_keys=True, default=str))


@pytest.fixture(scope="module")
def result():
    return json.loads(RESULT.read_text(encoding="utf-8"))


def test_the_record_carries_the_frozen_digest_and_design(result):
    assert result["freeze_digest"] == FROZEN_DIGEST and result["revision"] == "P2I-2Z"
    assert result["record"] == {"P2I-2Y": fr.P2I2Y_DIGEST}
    assert result["design"] == _plain(fr.design()) and result["rule"] == fr.RULE and result["policy"] == fr.POLICY
    assert result["contradictions"] == [] and result["keys"]["distinct"] == 48


def test_the_classification_region_edges_and_tau_follow_the_frozen_rules(result):
    p2i2y = fr.record_p2i2y()
    keys = fr.blood_keys(p2i2y)
    assert fr.reproduces_p2i2y(result["evaluated"], p2i2y) == []
    assert result["classified"] == _plain(fr.classify(result["evaluated"], keys))
    assert result["region"] == fr.robust_region(result["classified"])
    assert result["edges"] == _plain(fr.region_edges(result["region"]))
    assert result["tau"] == _plain(fr.tau_result(result["classified"], result["edges"]))
    for item in result["edges"].values():
        assert item["identified"] is (item["class"] == bc.WELL and item["edge"] == "INTERIOR")
    assert all(fr.calibration_status(*(float(v) for v in k.split("|")[:2])) == fr.ACTIVE for k in result["region"])


def test_fd_bld_04_and_05_are_recomputed_live_on_the_bag_alone(result):
    for key, entry in result["evaluated"].items():
        f0, finf, tau = (float(v) for v in key.split("|"))
        for case in bc.CASES:
            row = bc.retained(case, fc.bag(f0, finf, tau))
            assert {n: bc.passes(n, case, row) for n in ("FD-BLD-04", "FD-BLD-05")} == entry["verdicts"][case], key


def test_fd_bld_06_is_recomputed_live_at_the_smallest_margins(result):
    """For each new tau point, the key with the lowest 1 L peak and the key with the highest 2 L peak (the readings
    closest to the envelope), in both cases."""
    from clinical_core import blood_rate_boundary as rb
    rows = rb.Rows()
    for point in fr.design():
        if not point["new"]:
            continue
        key = f"{point['F0']:g}|{point['Finf']:g}|{point['tau']:g}"
        fd06 = result["evaluated"][key]["fd06"]
        low = min(fd06, key=lambda b: min(fd06[b][c]["reading"]["1000"]["peak"] for c in bc.CASES))
        high = max(fd06, key=lambda b: max(fd06[b][c]["reading"]["2000"]["peak"] for c in bc.CASES))
        for label in {low, high}:
            values = fc._crystalloid_values(point, tuple(float(v) for v in label.split("|")))
            for case in bc.CASES:
                assert rows.verdict(case, "FD-BLD-06", values) is fd06[label][case]["pass"] is True, (key, label, case)


def test_tau_stays_open_at_120_and_readiness_names_that_blocker(result):
    assert result["tau"]["tau_90_survives"] and result["tau"]["tau_120_survives"]
    assert result["tau"]["upper_status"] == "OPEN_UPPER_GRID_EDGE" and result["tau"]["stop"] == fr.OPEN_EDGE_STOP
    assert result["readiness"]["verdict"] == fr.NOT_READY
    assert result["readiness"]["blockers"] == ["crystalloid candidate region characterized"]
    assert result["lactate_input_space"]["status"].startswith("DRAFT")


def test_readiness_and_the_input_space_are_recomputed_from_the_record(result):
    p2i2y = fr.record_p2i2y()
    summary = result["structural"]["summary"]
    ready = fr.readiness(p2i2y, result["region"], result["edges"], result["tau"], summary,
                         result["structural"]["checks"])
    assert _plain(ready) == result["readiness"]
    assert _plain(fr.lactate_input_space(p2i2y, result["region"], summary, False)) == result["lactate_input_space"]
    assert result["lactate_input_space"]["factorization_valid"] is True


def test_nothing_is_approved_selected_or_lactate_filtered(result):
    from clinical_core import calibration, migration_authority
    assert sum(entry.status == calibration.FACULTY_APPROVED for entry in calibration.REGISTRY.values()) == 0
    assert migration_authority.APPROVED_FAMILY_DEFAULTS == () and migration_authority.TRUSTED_CASE_MAPPINGS == ()
    text = json.dumps(result)
    assert "selected" not in text and "best" not in text and "FD-LAC" not in text


def test_the_document_blocks_are_generated(result):
    from clinical_core import blood_fluid_readiness_report as report
    document = DOCUMENT.read_text(encoding="utf-8")
    for name, render in report.RENDERERS.items():
        assert report.apply(document, name, render(result)) == document, name
    assert "1054" in document and "fisiología actual" in document and "OPEN_UPPER_GRID_EDGE" in document
