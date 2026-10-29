"""Phase 2 shadow core, P2I-2AG: the pressure feedback deferred and the primary HR calibration surface frozen.

These tests pin the faculty decisions as frozen before evaluation: the relative-pressure contribution is DEFERRED for
the primary HR calibration (its gain is 0 in the analysis profile only, the common default keeps it, its value is a
diagnostic column); every calibration candidate declares its intrinsic rate (CALIBRATION_REQUIRES_EXPLICIT_INTRINSIC_HR,
also in check_hr); HR1 / HR2 are structural tests of the current predicted-arrival model; the arrival tolerance is +-5
bpm per case; gains and intrinsic are common (a case-specific intrinsic only as sensitivity); the saturation form and
candidates are P2I-2AF's; nothing is approved; the legacy HR is never read.
"""
import ast
import inspect
import json
from dataclasses import replace

import pytest

from clinical_core import blood_fluid_calibration as bf
from clinical_core import calibration, derived, gi_reference, lactate_slice
from clinical_core import hr_primary as hp
from clinical_core import hr_shock as hk
from clinical_core import hr_structure as hs
from clinical_core.derived import DEFAULT_PROFILE, CoreProfile
from clinical_core.state import CoreInvariantError
from test_clinical_core_lactate_rebuild import OFF_GRID, OFF_GRID_UNIT

ROOT = hp.ROOT
SOURCE = ROOT / "clinical_core" / "hr_primary.py"
#: The P2I-2AG freeze: faculty decisions, the P2I-2AD / P2I-2AE / P2I-2AF records, the primary mode, the guard, the
#: tolerance, the surface, the analytic, constraint and verdict rules, the policy and every clinical_core source but the
#: downstream reports, committed before any arrival count was evaluated.
FROZEN_DIGEST = "94c94584009449c43b15bd3bb8673bccbead3db86fcf71fa10f508b674ccf763"
CASES = hp.CASES
OFF_GRID_INPUTS = {"entry": {**OFF_GRID, **OFF_GRID_UNIT}, "bag": bf.bag(0.22, 0.07, 75.0),
                   "point": (45.0, 1.5, 4e-4, 90.0, "upper", "midpoint", "lower")}


# The frozen inputs ------------------------------------------------------------------------------------------------

def test_the_package_is_frozen():
    sources = bf.freeze_sources()
    assert {"clinical_core/hr_primary.py", "clinical_core/calibration.py", "clinical_core/derived.py"} <= set(sources)
    assert "clinical_core/hr_primary_report.py" in lactate_slice.DOWNSTREAM_REPORTS
    assert not set(lactate_slice.DOWNSTREAM_REPORTS) & set(sources)
    assert hp.p2i2af_record()["freeze_digest"] == hp.P2I2AF_DIGEST
    assert hp.freeze_digest() == FROZEN_DIGEST, "a source, the design, a rule or the policy changed after the freeze"


def test_the_faculty_decisions_are_recorded():
    assert set(hp.FACULTY) == {"decided", "pressure", "intrinsic", "hr1_hr2", "arrival", "common_gains", "saturation",
                               "d_scale", "rhythm", "scope"}
    assert "DEFERRED" in hp.FACULTY["pressure"] and "not rejected" in hp.FACULTY["pressure"]
    assert "no absolute pressure reference" in hp.FACULTY["pressure"]
    assert hp.CALIBRATION_REQUIRES_EXPLICIT_INTRINSIC_HR in hp.FACULTY["intrinsic"]
    assert "never approved" in hp.FACULTY["common_gains"] and "never tuned after counts" in hp.FACULTY["arrival"]


# P2I-2AG-1: the pressure contribution deferred, not removed -----------------------------------------------------------

def test_the_primary_mode_zeroes_only_the_pressure_gain_and_the_common_default_keeps_it():
    assert hp.PRIMARY_HR_CALIBRATION == {"sympathetic_per_pressure_deficit": 0.0}
    assert DEFAULT_PROFILE.sympathetic_per_pressure_deficit == CoreProfile().sympathetic_per_pressure_deficit == 1.0
    primary, common = hp.primary_profile(), hk.analysis_profile()
    assert replace(primary, sympathetic_per_pressure_deficit=common.sympathetic_per_pressure_deficit) == common
    assert "sympathetic_per_pressure_deficit" in inspect.getsource(derived.sympathetic_target)


@pytest.mark.parametrize("scenario", [hk.L1, hk.L3])
def test_the_primary_reconstruction_is_the_core_with_the_pressure_gain_zero(scenario):
    for case in CASES:
        base = hk.full_run(OFF_GRID_INPUTS, case, scenario)
        for level, acute, gain, ceiling in (("lower", 3.3, 2e-3, 165.0), ("upper", 19.0, 0.12, 199.0)):
            changes = {"acute_deficit_to_sympathetic_gain": acute, "debt_to_sympathetic_gain": gain,
                       "sinus_rate_ceiling_bpm": ceiling, **hp.PRIMARY_HR_CALIBRATION}
            full = hk.full_run(OFF_GRID_INPUTS, case, scenario, level, changes)
            series = hp.primary_series(base, hs.intrinsic_levels(case)[level], acute, gain, ceiling)
            assert [p["drive"] for p in series] == [r["drive"] for r in full["rows"]], (case, level)
            assert [p["hr"] for p in series] == [r["hr"] for r in full["rows"]]
            assert all(p["parts"] is None or p["parts"]["pressure"] == 0.0 for p in series)
            diagnostic = [p[hp.PRESSURE_TERM_DIAGNOSTIC_ONLY] for p in series]
            assert diagnostic == [25.0 * (1.0 - r["pressure_rel"]) for r in base["rows"]]
            # The pressure term really acted in the common physiology: the two HR series differ somewhere.
            common = hk.hr_series(base, hs.intrinsic_levels(case)[level], acute, gain, ceiling)
            assert any(a["hr"] != b["hr"] for a, b in zip(common, series))


def test_the_pressure_neutralization_moves_only_the_drive_and_hr():
    changes = {"acute_deficit_to_sympathetic_gain": 1.5, "debt_to_sympathetic_gain": 0.01,
               "sinus_rate_ceiling_bpm": 175.0}
    for case in CASES:
        _, _, on = hp._states(OFF_GRID_INPUTS, case, hk.L3, changes)
        _, _, off = hp._states(OFF_GRID_INPUTS, case, hk.L3, {**changes, **hp.PRIMARY_HR_CALIBRATION})
        assert len(on) == len(off)
        assert all(replace(x, aux=replace(x.aux, sympathetic_drive=0.0)) == replace(y, aux=replace(
            y.aux, sympathetic_drive=0.0)) for x, y in zip(on, off))
        assert any(x.aux.sympathetic_drive != y.aux.sympathetic_drive for x, y in zip(on, off))


def test_acceptance_reads_the_predicted_hr_only():
    body = inspect.getsource(hp.compatible)
    assert "pressure" not in body and "hr - AUTHORED[case]" in body
    surface = inspect.getsource(hp.arrival_surface)
    assert "primary_profile(acute, gain, ceiling)" in surface and '"compatible": compatible(case, hr)' in surface


# P2I-2AG explicit intrinsic, HR1 / HR2 --------------------------------------------------------------------------------

def test_calibration_requires_an_explicit_intrinsic_rate():
    canonical = gi_reference.candidate_anchors(CASES[0], {})
    assert canonical.intrinsic_sinus_rate is None and derived.intrinsic_sinus_rate(canonical) == canonical.hr
    with pytest.raises(CoreInvariantError, match=hp.CALIBRATION_REQUIRES_EXPLICIT_INTRINSIC_HR):
        hp.require_explicit_intrinsic(canonical)
    with pytest.raises(calibration.Failed, match=hp.CALIBRATION_REQUIRES_EXPLICIT_INTRINSIC_HR):
        calibration.check_hr(DEFAULT_PROFILE, {CASES[0]: canonical})
    declared = gi_reference.candidate_anchors(CASES[0], {"intrinsic_sinus_rate": 80.0})
    assert hp.require_explicit_intrinsic(declared) == 80.0


def test_hr1_hr2_carry_the_current_structural_semantics():
    semantics = hp.hr_semantics()
    assert semantics["structural_only"] and semantics["check_hr_requires_explicit_intrinsic"]
    assert semantics["hr2_arrival_reduction_encoded"] and semantics["no_authored_or_legacy_target"]
    assert semantics["fallback_outside_calibration"]
    assert "rhythm-consistent intrinsic rate" in calibration.FROZEN_RULES["HR2"].probe
    assert "but for HR" in calibration.FROZEN_RULES["AC1"].rule
    # HR2 (a) on an arrival with no sympathetic contribution (no debt, no deficit at the default acute gain 0).
    from clinical_core import decision_pack as dp
    candidate = replace(dp.MIDDLE, debt="lower", delivery="upper")
    for case in CASES:
        anchors = gi_reference.candidate_anchors(case, calibration.case_values(case, candidate))
        state = derived.arrival_state(anchors, DEFAULT_PROFILE)
        assert state.aux.sympathetic_drive == 0.0
        assert derived.derive(state, anchors, DEFAULT_PROFILE).pulse_rate_bpm == anchors.intrinsic_sinus_rate
    calibration.check_hr(DEFAULT_PROFILE)


# The frozen tolerance and surface -------------------------------------------------------------------------------------

def test_the_arrival_tolerance_is_five_bpm_per_case_and_inclusive():
    assert hp.AUTHORED == {"gi_bleed_57m": 124.0, "gi_bleed_72f": 112.0} and hp.TOLERANCE_BPM == 5.0
    assert hp.WINDOWS == {"gi_bleed_57m": (119.0, 129.0), "gi_bleed_72f": (107.0, 117.0)}
    assert hp.compatible("gi_bleed_57m", 119.0) and hp.compatible("gi_bleed_57m", 129.0)
    assert not hp.compatible("gi_bleed_57m", 118.99) and not hp.compatible("gi_bleed_72f", 117.01)


def test_the_surface_is_p2i2af_s_frozen_points_with_common_gains():
    assert hp.ACUTE == hk.ACUTE and hp.DEBT == hk.DEBT and hp.CEILINGS == hk.CEILINGS == (150.0, 175.0, 200.0)
    assert len(hp.ACUTE) == len(hp.DEBT) == 5 and 0.0 not in hp.ACUTE + hp.DEBT
    assert all(hs.intrinsic_levels(case) == {"lower": 60.0, "midpoint": 80.0, "upper": 100.0} for case in CASES)
    assert len(hp.candidates()) == 225 and all(len(c) == 4 for c in hp.candidates())


def test_the_rules_are_declared_before_any_count():
    assert set(hp.ANALYTIC_RULES) == {"IMPLICIT_RECORDED_HR_FALLBACK", "INVALID_RESERVE_BASE",
                                      "NEGATIVE_SYMPATHETIC_COMPONENT", "IDENTICAL_PREDICTION_DISJOINT_WINDOWS"}
    assert "never loosened" in hp.ARRIVAL_RULE and "EMPTY" in hp.CONSTRAINT_RULE
    assert hp.BLOCKED_BY_ARRIVAL in hp.VERDICT_RULE and "no trajectory decision pack" in hp.VERDICT_RULE
    assert [hp._constraint(c) for c in ({"a": 0, "b": 0}, {"a": 3, "b": 0}, {"a": 3, "b": 1, "c": 0},
                                        {"a": 4, "b": 1}, {"a": 4, "b": 2})] == [
        "EMPTY", "WELL_CONSTRAINED", "PARTIALLY_CONSTRAINED", "POORLY_IDENTIFIED", "NON_IDENTIFIABLE"]


# D-scale, rhythm -----------------------------------------------------------------------------------------------------

def test_d_scale_and_debt_gain_are_one_observable_in_the_primary_mode():
    probe = hp.d_scale_probe()
    assert probe["holds"] and all(row["without_gain_division_gap_bpm"] > 1.0 for row in probe["rows"])


def test_non_sinus_edges_stay_a_generalization_blocker_only():
    probe = hp.rhythm_probe()
    assert probe["holds"] and probe["classification"] == "GENERALIZATION_BLOCKER_ONLY" and not probe["affects_gi"]


# Policy ------------------------------------------------------------------------------------------------------------

def test_no_legacy_no_p2f_region_no_p2g_acceptance_and_nothing_approved():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    called = {ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)}
    for name in ("_legacy_run", "legacy_reference", "gi_candidates", "admissible", "region_runs", "p2f_rejection",
                 "runnable", "assess", "gi_physiology"):
        assert not any(name in call for call in called), name
    assert "with lr.P2FGuard(), lr.LegacyLock():" in inspect.getsource(hp.run)
    text = json.dumps(hp.design(), default=str).lower()
    for word in ("faculty_approved", "\"best", "\"selected", "\"recommended", "\"preferred", "\"rank"):
        assert word not in text
    source = SOURCE.read_text(encoding="utf-8")
    for word in ("rr_per_lactate=", "sbp_per_pressure_deficit=", "rr_metabolic_max=", "TOLERANCE_BPM = 6",
                 "TOLERANCE_BPM *"):
        assert word not in source


# The evaluation, on the frozen package (after the freeze commit 8eba7fc) ---------------------------------------------

RECORD = ROOT / "docs" / "revision" / "P2I2AG_hr_primary.json"
DOCUMENT = ROOT / "docs" / "revision" / "P2I2AG_SUPERFICIE_PRIMARIA_FC.md"


@pytest.fixture(scope="module")
def record():
    return json.loads(RECORD.read_text(encoding="utf-8"))


def test_the_record_is_reproduced_live_on_the_frozen_package(record):
    assert record["freeze_digest"] == FROZEN_DIGEST
    assert json.loads(json.dumps(hp.run(), sort_keys=True, default=str)) == record, "rerun and commit the record"


def test_the_verdict_is_blocked_by_the_arrival_reconstruction_and_the_package_stopped(record):
    verdict = record["verdict"]
    assert verdict["verdict"] == f"{hp.NOT_READY} — {hp.BLOCKED_BY_ARRIVAL}" and verdict["stopped"]
    assert verdict["checks"] == {"pressure_excluded": True, "explicit_intrinsic": True, "hr_semantics": True,
                                 "joint_arrival": False, "common_gains": True, "unchanged_physiology": True}
    assert not verdict["approved"] and not record["efficiency"]["trajectory_decision_pack_built"]


def test_the_arrival_counts_the_report_states(record):
    arrival = record["arrival"]
    assert arrival["total_decompositions"] == 1350 and arrival["compatible"] == {"gi_bleed_57m": 30, "gi_bleed_72f": 58}
    assert arrival["joint_common_intrinsic"] == 0 and arrival["simulation_rejections"] == 0
    assert arrival["analytic_rejections"] == {"IMPLICIT_RECORDED_HR_FALLBACK": 0, "INVALID_RESERVE_BASE": 0,
                                              "NEGATIVE_SYMPATHETIC_COMPONENT": 0,
                                              "IDENTICAL_PREDICTION_DISJOINT_WINDOWS": 675}
    assert all(arrival["identical_arrival_physiology"].values()) and arrival["windows_disjoint"]
    assert arrival["pressure_on_equal_at_arrival"] and not arrival["case_specific_gain_required"]
    sens = arrival["case_intrinsic_sensitivity"]
    assert (sens["joint"], sens["of"], sens["approved"]) == (5, 2025, False)
    assert sens["intrinsic_pairs"]["midpoint|lower"] == 5 and sens["ceiling"] == {"150": 5, "175": 0, "200": 0}


def test_the_diagnostics_and_non_regression_the_report_states(record):
    audit = record["pressure_audit"]
    assert (audit["minutes"], audit["both_push_up"], audit["pressure_down_while_deficit"]) == (2160, 948, 457)
    assert audit["ranking_changes"] == {"pairs": 18000, "discordant": 383, "ties_changed": 0}
    assert audit["classification"] == hk.NEEDS_PRESSURE_DOMAIN_REVIEW and not audit["calibrated"]
    assert record["validation"]["agree"] and record["validation"]["full_reruns"] == 54
    assert record["non_regression"]["unchanged"] and record["non_regression"]["states_compared"] == 2178
    assert record["d_scale"]["holds"] and record["rhythm"]["holds"]
    assert record["identifiability"]["sets"]["joint, common intrinsic (primary)"] == {
        "intrinsic": "EMPTY", "acute": "EMPTY", "debt": "EMPTY", "ceiling": "EMPTY"}
    # The only "rank" keys are P2I-2AG-2's diagnostic: whether the descriptive HR order changes with the pressure term.
    assert {key for key in audit if key.startswith("rank")} == {"ranking_changes", "ranking_detail"}
    stripped = {**record, "pressure_audit": {k: v for k, v in audit.items() if not k.startswith("rank")}}
    text = json.dumps(stripped, default=str).lower()
    found = [word for word in ("faculty_approved", "\"best", "\"selected", "\"recommended", "\"preferred", "\"rank")
             if word in text]
    assert not found


def test_the_document_is_generated_from_the_record(tmp_path):
    from clinical_core import hr_primary_report
    copy = tmp_path / "document.md"
    copy.write_text(DOCUMENT.read_text(encoding="utf-8"), encoding="utf-8")
    hr_primary_report.main(["--write", str(copy), "--data", str(RECORD)])
    assert copy.read_text(encoding="utf-8") == DOCUMENT.read_text(encoding="utf-8"), "regenerate the document"
