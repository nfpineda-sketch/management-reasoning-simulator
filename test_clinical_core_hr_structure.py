"""Phase 2 shadow core, P2I-2AE: HR / sympathetic-response structure (closed record since P2I-2AF).

P2I-2AF replaced the arrival residual with an acute-deficit drive and added a smooth sinus saturation, so the P2I-2AE
module and its record are pinned and its live checks keep only what P2I-2AF left unchanged: tau_D never reaches the
drive (the debt-driven drive is debt_to_sympathetic_gain x D, 0 at D = 0, never decreasing in D); the rhythm stays
authoritative; HR reaches no output, delivery, D, lactate or RR; the gain range, flags, invariants and verdict rule are
the frozen ones; the intrinsic band is not HR1 evidence; the legacy HR is read only after the verdict.
"""
import ast
import hashlib
import inspect
import json
from dataclasses import replace

import pytest

from clinical_core import blood_fluid_calibration as bf
from clinical_core import derived, lactate_slice
from clinical_core import hr_structure as hs
from clinical_core import lactate_rebuild as lr
from clinical_core.bands import Drift
from clinical_core.derived import DEFAULT_PROFILE, CoreProfile, derive
from clinical_core.integration import run
from clinical_core.modules.rhythm_events import ScriptedRhythmEvent
from clinical_core.state import RhythmCode, RhythmState

ROOT = hs.ROOT
SOURCE = ROOT / "clinical_core" / "hr_structure.py"
RECORD = ROOT / "docs" / "revision" / "P2I2AE_hr_structure.json"
DOCUMENT = ROOT / "docs" / "revision" / "P2I2AE_ESTRUCTURA_FC_SIMPATICA.md"
#: The P2I-2AE freeze: faculty decisions, the P2I-2AD record, the audit, the gain range, the analytic rule, the
#: scenarios, the factorization, the scan, the flags, the invariants, identifiability, the legacy and verdict rules, the
#: policy and every clinical_core source but the downstream reports, committed before any HR outcome was evaluated.
#: Refrozen once after the adversarial review (finding F1): only the historical region modules changed (decision_pack,
#: decision_pack_markdown, lactate_slice); hr_structure.py and the core are byte for byte those of the freeze commit
#: 6052ffb (digest 398ab817...), and the re-run record equals the first one but for this digest.
FROZEN_DIGEST = "1b65d303831011014ca8cf8ce98e5fb880c5ea9cd3244f47773ce9d47b3712c8"
#: Closed by P2I-2AF, whose acute-deficit drive and sinus saturation change the core sources the freeze digest reads:
#: the module and the record are pinned instead.
P2I2AE_MODULE_SHA = "1109ca9dded7b8e67c588932326f510e10e0ad51f6091f0a17fe9ef09f218f16"
CASES = hs.CASES
FALLING = (Drift("pump", "P", 0, 90, -0.005),)


def _anchors(case=CASES[0], intrinsic="midpoint", debt="midpoint"):
    return hs.case_anchors(case, intrinsic, debt)


def _profile(**changes):
    return replace(DEFAULT_PROFILE, **changes)


# The frozen inputs ------------------------------------------------------------------------------------------------

def test_the_p2i2ad_record_is_the_committed_one():
    record = hs.p2i2ad_record()
    assert record["freeze_digest"] == hs.P2I2AD_DIGEST and set(record["representatives"]) == {"LOW", "MID", "HIGH"}


def test_the_package_is_frozen():
    sources = bf.freeze_sources()
    assert {"clinical_core/hr_structure.py", "clinical_core/derived.py", "clinical_core/integration.py",
            "clinical_core/lactate_closure.py"} <= set(sources)
    assert "clinical_core/hr_structure_report.py" in lactate_slice.DOWNSTREAM_REPORTS
    assert not set(lactate_slice.DOWNSTREAM_REPORTS) & set(sources)
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == P2I2AE_MODULE_SHA, "the P2I-2AE module changed"
    assert json.loads(RECORD.read_text(encoding="utf-8"))["freeze_digest"] == FROZEN_DIGEST


def test_the_faculty_decisions_are_recorded():
    assert set(hs.FACULTY) == {"decided", "td_92", "arrival", "lactate", "scope"}
    assert "never derived from tau_D" in hs.FACULTY["td_92"] and "non-negative" in hs.FACULTY["arrival"]
    assert "not calibration evidence" in hs.FACULTY["arrival"]


# The core: the debt-driven drive (P2I-2AE-2) ------------------------------------------------------------------------

def test_the_gain_is_its_own_parameter_and_provisional():
    assert CoreProfile().debt_to_sympathetic_gain == 1.0 / 120.0 == 0.5 / 60.0
    status, text = derived.PARAMETERS["debt_to_sympathetic_gain"]
    assert status == derived.PROVISIONAL and "independent of tau_D" in text and "not a calibrated value" in text
    assert "does not read it" in derived.PARAMETERS["sympathetic_per_debt"][1]
    # Changing tau_D changes no gain: the gain is a field of its own, never computed from tau_D.
    assert replace(DEFAULT_PROFILE, debt_clearance_tau_min=30.0).debt_to_sympathetic_gain == (
        DEFAULT_PROFILE.debt_to_sympathetic_gain)


def test_tau_d_at_fixed_d_changes_no_drive_and_no_hr():
    for case in CASES:
        anchors = _anchors(case)
        arrival = derived.arrival_state(anchors)
        for debt in (0.0, 7.0, anchors.arrival_oxygen_debt, 55.0, 300.0):
            state = arrival.evolve(D=debt)
            readings = set()
            for tau in (1.0, 7.5, 30.0, 60.0, 120.0, 480.0):
                profile = _profile(debt_clearance_tau_min=tau)
                drive = derived.sympathetic_after_minute(arrival, state, anchors, profile)
                readings.add((derived.sympathetic_target(state, anchors, profile), drive,
                              derive(state.evolve(aux=replace(state.aux, sympathetic_drive=drive)), anchors,
                                     profile).pulse_rate_bpm))
            assert len(readings) == 1, (case, debt)


def test_the_retired_coefficient_reaches_nothing():
    # The record's source audit; live, the retired coefficient reaches nothing: a run with it at 0 or 10 is the same.
    live = json.loads(RECORD.read_text(encoding="utf-8"))["audit"]["live"]
    assert live["no_tau_d_in_hr"] and live["reads"]["sinus_rate_reads_drive"]
    body = inspect.getsource(derived.sympathetic_target).split('"""')[-1]
    assert "debt_clearance_tau_min" not in body and "sympathetic_per_debt" not in body
    states = [run(_anchors(), FALLING, 60, _profile(sympathetic_per_debt=value)).states for value in (0.0, 0.5, 10.0)]
    assert states[0] == states[1] == states[2]


def test_the_debt_driven_drive_is_gain_times_d_and_zero_at_zero():
    anchors = _anchors()
    arrival = derived.arrival_state(anchors)
    for gain in (0.0, 1e-3, 1.0 / 120.0, 0.05):
        profile = _profile(debt_to_sympathetic_gain=gain)
        base = derived.sympathetic_target(arrival.evolve(D=0.0), anchors, profile)
        for debt in (0.0, 1.0, 20.0, 64.0, 500.0):
            target = derived.sympathetic_target(arrival.evolve(D=debt), anchors, profile)
            assert target - base == pytest.approx(gain * debt, rel=1e-12, abs=1e-15)
        assert derived.arrival_debt_drive(anchors, profile) == gain * anchors.arrival_oxygen_debt


def test_more_debt_never_lowers_the_drive_or_hr():
    for case in CASES:
        anchors = _anchors(case)
        arrival = derived.arrival_state(anchors)
        for gain in (*hs.GAINS[:3], 0.0):
            profile = _profile(debt_to_sympathetic_gain=gain)
            debts = [0.0, 0.5, 3.0, 20.0, 21.0, 60.0, 240.0, 1000.0]
            drives = [derived.sympathetic_after_minute(arrival, arrival.evolve(D=d), anchors, profile) for d in debts]
            rates = [derive(arrival.evolve(D=d, aux=replace(arrival.aux, sympathetic_drive=r)), anchors,
                            profile).pulse_rate_bpm for d, r in zip(debts, drives)]
            assert drives == sorted(drives) and rates == sorted(rates), (case, gain)


def test_the_drive_is_never_negative_and_the_sinus_rate_never_below_intrinsic():
    anchors = _anchors()
    # A synthetic relief far beyond arrival: the target reaches 0 and the drive decays toward it, never below.
    relieved = run(anchors, (Drift("pump", "P", 0, 40, 0.05),), 120, _profile())
    rates = [item.pulse_rate_bpm for item in relieved.derived()]
    assert min(state.aux.sympathetic_drive for state in relieved.states) >= 0.0
    assert min(rates) >= anchors.intrinsic_sinus_rate and rates[-1] == pytest.approx(anchors.intrinsic_sinus_rate,
                                                                                     abs=1e-3)


def test_the_rhythm_stays_authoritative():
    anchors = _anchors()
    paced = run(anchors, FALLING + (ScriptedRhythmEvent("paced", 10, RhythmState(RhythmCode.PACED, 70.0, 1.0, True),
                                                        "probe"),), 40, _profile())
    assert {item.pulse_rate_bpm for item in paced.derived()[10:]} == {70.0}
    arrest = run(anchors, FALLING + (ScriptedRhythmEvent("pea", 10, RhythmState.pea(40.0), "probe"),), 20, _profile())
    assert all(item.pulse_rate_bpm is None for item in arrest.derived()[10:])
    assert all(state.aux.sympathetic_drive == 0.0 for state in arrest.states[10:])


def test_hr_feeds_back_into_no_output_delivery_debt_lactate_or_rr():
    anchors = _anchors()
    runs = [run(anchors, FALLING, 90, _profile(debt_to_sympathetic_gain=gain)) for gain in (0.0, 1e-3, 0.05)]
    readings = [[(v.output_rel, v.delivery_rel, v.lactate, v.respiratory_rate, s.D)
                 for s, v in zip(r.states, r.derived())] for r in runs]
    assert readings[0] == readings[1] == readings[2]
    assert [v.pulse_rate_bpm for v in runs[0].derived()] != [v.pulse_rate_bpm for v in runs[2].derived()]


# The design (P2I-2AE-1, 3, 4, 6, 7) ---------------------------------------------------------------------------------

def test_the_audit_names_every_tau_d_path_with_its_class():
    classes = {path["class"] for path in hs.TAU_D_PATHS}
    assert classes <= {hs.VALID_CAUSAL_PATH, hs.SEMANTIC_LEAK, hs.LEGACY_ARTIFACT, hs.CASE_SPECIFIC_ARTIFACT}
    assert [p["class"] for p in hs.TAU_D_PATHS].count(hs.SEMANTIC_LEAK) == 1
    assert hs.TAU_D_PATHS[0]["status"] == "removed (P2I-2AE)"
    assert set(hs.CONTRIBUTORS) >= {"intrinsic_rate", "sympathetic", "debt", "direct_deficit", "drugs_interventions",
                                    "rhythm", "caps_floors", "case_specific"}
    assert hs.DEFICIT_AUDIT["A_instantaneous_effective_oxygen_deficit"] is False
    assert hs.DEFICIT_AUDIT["B_accumulated_D"] is True and hs.DEFICIT_AUDIT["new_acute_term_needed"] is False


def test_the_anchors_are_authored_only():
    table = hs.anchors_table()
    assert table["gi_bleed_57m"]["arrival_hr"]["value"] == 124 and table["gi_bleed_72f"]["arrival_hr"]["value"] == 112
    for case in CASES:
        assert table[case]["arrival_hr"]["label"] == hs.AUTHORED_OBSERVATION
        assert table[case]["later_hr"]["value"] == "not authored"
        assert table[case]["family_engine_hr"]["label"] == hs.LEGACY_REFERENCE
        assert table[case]["core_hr_after_arrival"]["label"] == hs.MODEL_DERIVED


def test_the_intrinsic_band_is_still_valid_and_not_hr1_evidence():
    audit = hs.intrinsic_audit()
    assert audit["status"] == hs.STILL_VALID and not audit["derived_from_hr1"]
    assert audit["band"] == {"gi_bleed_57m": [60.0, 80.0, 100.0], "gi_bleed_72f": [60.0, 80.0, 100.0]}


def test_the_gain_range_follows_its_rule_and_never_reads_tau_d():
    design = hs.gain_design()
    assert design["old_status"] == hs.OLD_RANGE_STATUS == "OLD_SYMPATHETIC_PER_DEBT_RANGE_SEMANTICALLY_INVALID"
    assert design["low"] == 1.0 / (25.0 * 60.0) and design["high"] == (124.0 - 60.0) / (25.0 * 20.0)
    points = design["points"]
    assert len(points) == 5 and points[0] == design["low"] and points[-1] == design["high"] and hs.GAINS == points
    ratios = [b / a for a, b in zip(points, points[1:])]
    assert max(ratios) - min(ratios) < 1e-12
    assert hs.GAIN_ANCHOR == points[2] and hs.GAIN_SCAN == points + (0.0,)
    assert design["every_declared_arrival_consistent_below"] == pytest.approx(0.48 / 60.0)
    body = inspect.getsource(hs.gain_design).split('"""')[-1].split("old = ")[0]
    for word in ("debt_clearance_tau_min", "legacy", "trajectory", "sympathetic_per_debt", "run("):
        assert word not in body


# The factorization (off-grid physiology only) --------------------------------------------------------------------

# Policy ------------------------------------------------------------------------------------------------------------

def test_the_flags_invariants_and_verdict_rule_are_declared_before_any_run():
    assert set(hs.FLAG_RULES) == {"ARRIVAL_NOT_REPRODUCED", "HR_BELOW_INTRINSIC", "NEGATIVE_CONTRIBUTION",
                                  "DRIVE_FALLS_AGAINST_ITS_TARGET", "INSTANT_NORMALIZATION_AT_HAEMOSTASIS",
                                  "NO_DEBT_RECOVERY_AFTER_ADEQUACY"}
    assert sorted(hs.INVARIANTS) == list(range(1, 11))
    assert "No bpm threshold" in hs.FLAG_POLICY and "No numeric HR band is required" in hs.VERDICT_RULE
    assert hs.READY == "HR_STRUCTURE_READY_FOR_NUMERIC_FACULTY_CALIBRATION"


def test_the_legacy_hr_is_read_only_after_the_verdict_and_the_p2f_region_never():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    readers = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
               and "_legacy_run" in ast.unparse(node)}
    assert readers == {"legacy_reference"}
    with lr.LegacyLock():
        with pytest.raises(AssertionError, match="only after the verdict"):
            hs.legacy_reference({})
    run_source = inspect.getsource(hs.run)
    assert run_source.index("legacy_reference(") > run_source.index("verdict(audit")
    assert "with lr.P2FGuard(), lr.LegacyLock():" in run_source
    called = {ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)}
    for name in ("gi_candidates", "admissible", "region_runs", "p2f_rejection"):
        assert not any(name in call for call in called), name


def test_nothing_is_selected_or_approved():
    text = json.dumps(hs.design(), default=str).lower()
    for word in ("faculty_approved", "\"best", "\"selected", "\"recommended", "\"preferred", "\"rank"):
        assert word not in text
    assert DEFAULT_PROFILE == CoreProfile() and DEFAULT_PROFILE.collapse_output_threshold is None
    for word in ("sbp_per_pressure_deficit=", "rr_per_lactate=", "sympathetic_per_pressure_deficit="):
        assert word not in SOURCE.read_text(encoding="utf-8")


# The evaluation, on the frozen package (after the freeze commit) ---------------------------------------------------



@pytest.fixture(scope="module")
def record():
    return json.loads(RECORD.read_text(encoding="utf-8"))


def test_the_record_ran_on_the_frozen_package(record):
    # P2I-2AE's run was reproduced live on its own core (b8551d2); P2I-2AF changed the HR mapping, so it is not rerun.
    assert record["freeze_digest"] == FROZEN_DIGEST and record["records"] == {"P2I-2AD": hs.P2I2AD_DIGEST}


def test_the_verdict_follows_the_frozen_rule(record):
    verdict = record["verdict"]
    assert verdict["verdict"] == hs.READY and not verdict["blockers"] and not verdict["flags_seen"]
    assert all(verdict["checks"].values()) and set(verdict["checks"]) == {
        "factorization", "no_tau_d_leak", "contributors_explicit", "arrival_coherent", "invariants", "patient_like",
        "support_explicit", "nothing_approved"}
    assert verdict["next_step"] == hs.NEXT_STEP and "Pressure and vascular tone follow HR; not started" in hs.NEXT_STEP


def test_the_factorization_was_exact_and_the_physiology_is_p2i2ad_s(record):
    assert record["validation"]["agree"] and record["validation"]["full_reruns"] == 90
    assert not record["validation"]["disagreements"]
    assert record["unchanged_physiology"] == {"rows_checked": 72, "equal": True}


def test_the_analytic_rejections_and_the_counts(record):
    assert record["analytic"]["analytic_rejections"] == 17 and record["analytic"]["combinations"] == 108
    assert record["refused_by_core"] == {"agree": True, "mismatches": []}
    efficiency = record["efficiency"]
    assert efficiency["representative_runs"] == 18 and efficiency["validation_full_reruns"] == 90
    assert efficiency["post_processed_series"] + efficiency["scan_pairs_rejected_analytically"] == 18 * 3 * 6
    assert efficiency["cartesian_sweep"] is False


def test_the_invariants_hold_and_no_flag_is_raised(record):
    assert record["invariants"]["all_pass"] and record["invariants"]["recovery_runs"] > 0
    assert set(record["flags"].values()) == {0}
    for case in CASES:
        assert record["probes"][case]["tau_d_at_fixed_D"]["holds"]


def test_rr_is_not_changed_or_calibrated_and_the_legacy_is_reference_only(record):
    assert record["rr"]["changes_rr"] is False and record["rr"]["calibrated"] is False
    assert record["legacy_reference"]["rule"] == hs.LEGACY_RULE
    assert "NOT A CALIBRATION TARGET" in hs.LEGACY_RULE


def test_identifiability_is_reported_not_resolved(record):
    identifiable = record["identifiability"]
    assert identifiable["intrinsic_vs_gain"]["status"] == hs.NON_IDENTIFIABLE
    assert identifiable["intrinsic_vs_gain"]["max_hr_gap_bpm"] < 1e-9
    assert identifiable["dimensions"]["saturation_or_cap"]["status"] == "NO_PARAMETER"
    text = json.dumps(record, default=str).lower()
    for word in ("faculty_approved", "\"best", "\"selected", "\"recommended", "\"preferred", "\"rank"):
        assert word not in text


def test_the_document_is_generated_from_the_record(tmp_path):
    from clinical_core import hr_structure_report
    copy = tmp_path / "document.md"
    copy.write_text(DOCUMENT.read_text(encoding="utf-8"), encoding="utf-8")
    hr_structure_report.main(["--write", str(copy), "--data", str(RECORD)])
    assert copy.read_text(encoding="utf-8") == DOCUMENT.read_text(encoding="utf-8"), "regenerate the document"
