"""P3-301 to P3-313: the first human faculty review, recorded; and the analysis of why FR-G protects as much as it does.

Three things are protected here, and they are kept apart on purpose:

* HUMAN_FACULTY_REVIEW: the record of what the reviewer judged. It has no model-written judgment, no name, no invented blind answers, and the human-reviewed
  items it points at are exactly the pinned ones (nothing was overwritten);
* MODEL_ANALYSIS / TEST_RESULT: ``test_gi_frg_crystalloid_analysis`` is recomputed from the executable model and compared with the stored record, and each claim of the
  verdict (A refuted, B supported, C refuted, bleeding active, mass balance exact, the harness equal to what the faculty saw) is asserted on its own;
* what was NOT done: no executable change (the runtime crystalloid point is still the historical one), no FR-G-specific branch, no multiplier, no source
  control, no norepinephrine physiology.

``MRS_WRITE_FRG_ANALYSIS=1 python3 test_gi_frg_crystalloid_analysis.py`` regenerates the stored analysis record; the human record is written by hand and only changes
when the reviewer changes it.
"""
import hashlib
import json
import re
from pathlib import Path

import pytest

import faculty_trajectory_review as ftr
import test_gi_frg_crystalloid_analysis as fa

ROOT = Path(__file__).resolve().parent
HUMAN_PATH = ROOT / "docs" / "revision" / "PHASE3_FIRST_HUMAN_FACULTY_REVIEW.json"
CHECKPOINT_P3_300 = ROOT / "docs" / "revision" / "PHASE3_FACULTY_REVIEW_CHECKPOINT.json"
P3_300_DIGEST = "45b62670af0983f3513e5ec5b290ff866da073b3100177dfa5f4d1a5729c89b2"
FR_G_COMMENT = ("The common-core direction is correct, but the magnitude of deterioration is too small. I would expect the trajectory to remain closer to the untreated "
                "course, with only modest transient attenuation from the crystalloid.")


def _canonical_digest(record: dict) -> str:
    body = {key: value for key, value in record.items() if key != "record_digest"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()


@pytest.fixture(scope="module")
def human() -> dict:
    return json.loads(HUMAN_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def built() -> dict:
    return fa.build()


# -- HUMAN_FACULTY_REVIEW: the record ---------------------------------------------------------------------------------------------------------------

def test_h1_the_human_record_is_human_evidence_with_its_own_sealed_digest_and_the_other_classes_kept_apart(human):
    assert human["evidence_class"] == "HUMAN_FACULTY_REVIEW" and human["record_type"] == "HUMAN_FACULTY_REVIEW_RECORD"
    assert set(human["evidence_classes"]) == {"HUMAN_FACULTY_REVIEW", "MODEL_ANALYSIS", "TEST_RESULT", "LEGACY_COMPARATOR"}
    assert human["record_digest"] == _canonical_digest(human), "the record is sealed by its own digest: an edit is visible"


def test_h2_the_counts_and_the_seven_overall_judgments_are_the_ones_the_reviewer_reported(human):
    overall = {row["scenario_id"]: row["overall"] for row in human["scenarios"]}
    assert overall == {"FR-B": "ACCEPT_WITH_LIMITATION", "FR-A": "ACCEPT_WITH_LIMITATION", "FR-E": "ACCEPT", "FR-G": "RECALIBRATE", "FR-F": "ACCEPT_WITH_LIMITATION",
                       "FR-D": "ACCEPT_WITH_LIMITATION", "FR-C": "ACCEPT_WITH_LIMITATION"}
    counts = {"ACCEPT": 0, "ACCEPT_WITH_LIMITATION": 0, "RECALIBRATE": 0, "REJECT": 0}
    for value in overall.values():
        counts[value] += 1
    assert human["overall_counts"] == counts == {"ACCEPT": 1, "ACCEPT_WITH_LIMITATION": 5, "RECALIBRATE": 1, "REJECT": 0}
    assert human["scope"]["scenarios_reviewed"] == 7
    assert [sid for sid, required in ftr.SEQUENCE if required] == human["scope"]["required"]
    assert [sid for sid, required in ftr.SEQUENCE if not required] == human["scope"]["optional"]
    assert human["comparator_changed_judgment"] == {"answer": "NO", "scenarios": 7}
    assert all(row["comparator_changed_judgment"] is False and row["post_reveal_judgment"]["overall"] == row["overall"] for row in human["scenarios"])


def test_h3_the_fr_g_comment_is_verbatim_and_nothing_the_reviewer_did_not_give_is_invented(human):
    frg = next(row for row in human["scenarios"] if row["scenario_id"] == "FR-G")
    assert frg["faculty_comment_verbatim"] == FR_G_COMMENT and frg["primary_actionable_finding"] is True
    assert all(row["blind_judgment"]["recorded_here"] is False and row["blind_judgment"]["status"] == "NOT_TRANSCRIBED" for row in human["scenarios"]), "the blind answers were not provided"
    assert human["provenance"]["reviewer_name"] is None and human["provenance"]["reviewer_identity_recorded"] is False and human["provenance"]["reviewer_role"] == "faculty"
    text = json.dumps(human)
    assert "@" not in text and not re.search(r"\b(?:Dr|Prof|Dra)\.?\s", text), "no person's name, title or handle"
    for key in ("email", "reviewer_id", "account", "username"):
        assert key not in human["provenance"]


def test_h4_the_human_reviewed_items_are_the_pinned_ones_nothing_was_overwritten(human):
    preserved = human["preserved_original_evidence"]
    stored = json.loads((ROOT / "docs" / "revision" / "PHASE3_FACULTY_TRAJECTORY_REVIEW_SET.json").read_text(encoding="utf-8"))
    assert preserved["review_set_digest"] == stored["record_digest"] == ftr.PINNED_SET_DIGEST == preserved["pinned_in_code"]
    assert preserved["item_digests"] == {item["scenario_id"]: ftr.item_digest(item) for item in stored["items"]}
    assert preserved["p3_300_checkpoint_digest"] == json.loads(CHECKPOINT_P3_300.read_text(encoding="utf-8"))["record_digest"] == P3_300_DIGEST, "the P3-300 checkpoint is byte-identical"


def test_h5_the_six_faculty_decisions_are_recorded_and_norepinephrine_is_a_roadmap_item_not_an_implementation(human):
    assert [row["id"] for row in human["faculty_decisions"]] == [f"FD-REVIEW-0{i}" for i in range(1, 7)]
    assert human["faculty_decisions"][5]["implemented"] is False
    cola = (ROOT / "docs" / "COLA_DECISIONES_AI_ADVISOR.md").read_text(encoding="utf-8")
    debt = (ROOT / "docs" / "REGISTRO_DEUDA_TECNICA.md").read_text(encoding="utf-8")
    for index in range(1, 7):
        assert f"| FD-REVIEW-0{index} |" in cola
    assert "TD-147" in debt and "norepinefrina" in debt.lower() and "tono vascular" in debt.lower()
    for path in sorted((ROOT / "clinical_core").rglob("*.py")):
        assert "norepinephrine" not in path.read_text(encoding="utf-8").lower(), f"{path.name}: no norepinephrine physiology exists, and none was added"


# -- MODEL_ANALYSIS: the stored record is the recomputed one -----------------------------------------------------------------------------------------

def test_m1_the_stored_analysis_is_exactly_what_the_executable_model_gives_now(built):
    stored = fa.load_record()
    assert built["record_digest"] == stored["record_digest"] == fa.digest(stored), "regenerate with MRS_WRITE_FRG_ANALYSIS=1 only when the analysis itself changes"
    assert stored["evidence_class"] == "MODEL_ANALYSIS" and stored["executable_change"] is False


def test_m2_the_harness_reproduces_what_the_faculty_saw_in_every_reviewed_trajectory(built):
    reproduction = built["harness_reproduces_the_reviewed_trajectories"]
    assert reproduction["all_match"] and set(reproduction["scenarios"]) == {"FR-A", "FR-B", "FR-C", "FR-D", "FR-E", "FR-G"}
    assert all(item["minutes_compared"] >= 2 for item in reproduction["scenarios"].values())
    assert built["reconstruction"]["cross_check_matches"], "FR-G at minutes 60 and 70 is the committed 92/58 and 88/56"


def test_m3_the_bleeding_is_active_at_every_minute_of_every_run_read_and_no_source_control_exists_in_any(built):
    bleeding = built["bleeding"]
    assert bleeding["bleeding_active_at_every_minute"] and not bleeding["source_control_in_any_run"]
    for name, run in bleeding["runs"].items():
        assert run["distinct_loss_values_ml_min"] == [2.5] and not run["stops_or_changes"], name
    trace = built["reconstruction"]["trace"]
    assert all(trace[str(minute)]["bleed_ml_min"] == 2.5 for minute in (5, 10, 15, 30, 45, 60, 70))
    assert trace["60"]["bleed_cum_ml"] == 150.0


def test_m4_the_continuous_infusion_is_integrated_minute_by_minute_with_simultaneous_redistribution_not_as_a_bolus(built):
    mass = built["mass_balance"]
    assert mass["behaves_as_per_minute_input_with_simultaneous_redistribution"] and mass["max_abs_gap_ml"] < 1e-6, "core net crystalloid equals the analytic convolution"
    assert mass["total_effective_gain_is_volume_times_e_for_every_rate"]
    assert mass["kernel"] == {"e": 0.125, "s": 0.6, "tau": 30.0}, "the runtime kernel is still the historical one: nothing executable changed"
    analytic = mass["analytic_retained_ml"]
    assert analytic["instantaneous_1min"]["1"] > analytic["15min"]["15"] > analytic["60min"]["60"], "a longer infusion never reaches the expansion of a shorter one"
    assert analytic["60min"]["120"] > analytic["15min"]["120"] > analytic["instantaneous_1min"]["120"] > mass["permanent_floor_ml"], "all of it converges on the permanent floor from above"
    ordering = built["infusion_ordering"]
    assert ordering["peak_falls_as_the_infusion_lengthens"] and ordering["early_expansion_larger_for_the_shorter_bag_at_10_min"] and ordering["same_floor_at_240"]
    assert 40 <= ordering["slow_exceeds_the_15min_bag_from_minute"] <= 60, "the slow bag catches up only late in its own infusion, because its later portions had less time to redistribute"


def test_m5_the_closed_volume_region_is_not_the_runtime_point_and_it_predicts_a_STRONGER_slow_infusion_effect_not_a_weaker_one(built):
    region = built["volume_region"]
    runtime = region["runtime_point"]
    assert runtime["classification"] == "HISTORICAL_PROVISIONAL_NON_SURVIVING_REFERENCE" and runtime["inside_closed_region"] is False
    status = {key: value["status"] for key, value in runtime["bag_20min"].items()}
    assert status == {"peak": "BELOW", "30": "BELOW", "60": "BELOW", "120": "IN"}, "documented in docs/PHASE3_VOLUME_BEHAVIOUR_CALIBRATION.md section 2.4"
    assert abs(runtime["bag_20min"]["peak"]["value"] - 0.103833) < 1e-6 and abs(runtime["module_agreement_max_abs"]) < 1e-12
    slow = region["slow_infusion_60min"]
    assert slow["region_least_retained_at_60_ml"] > 1.5 * slow["runtime_retained_at_60_ml"] and slow["region_least_retained_at_60_ml"] >= 125.0
    general = slow["any_nonincreasing_kernel_inside_the_closed_bands"]
    assert general["retained_at_60_ml_at_least"] == 125.0 and general["over_runtime_ratio"] > 1.5, "true for ANY kernel that never rises with age, not only the three-parameter family"
    runs = region["core_runs"]
    assert runs["runtime"]["protection_pct_at_60"] < runs["region_least_protective"]["protection_pct_at_60"], "moving into the closed region makes FR-G MORE protected"


def test_m6_the_pressure_coupling_does_not_amplify_and_the_bleeding_rate_only_sets_the_scale(built):
    coupling = built["pressure_coupling"]
    assert coupling["amplifies_a_small_volume"] is False and abs(coupling["difference_points"]) < 5.0
    slopes = list(coupling["untreated_slope_sbp_per_ml_by_deficit_band"].values())
    assert all(0.10 < value < 0.16 for value in slopes) and 0.10 < coupling["slope_sbp_per_ml_when_volume_is_added_5min_bag"] < 0.13
    sensitivity = built["bleeding_rate_sensitivity"]
    assert sensitivity["protection_falls_as_bleeding_rises"], "a sensitivity, not a target and not a correction"
    rows = sensitivity["rows"]
    assert rows["5.0"]["region_least_protective_kernel"]["protection_pct_at_60"] > rows["5.0"]["runtime_kernel"]["protection_pct_at_60"]


def test_m7_the_verdict_is_exactly_B_and_each_other_class_is_refuted_or_a_scale_factor(built):
    verdict = built["verdict"]
    assert verdict["classified_as"] == "B"
    assert verdict["B_CLOSED_VOLUME_REGION_TOO_PROTECTIVE_FOR_SLOW_INFUSION"]["supported"] is True
    assert verdict["A_CONTINUOUS_INFUSION_IMPLEMENTATION_BUG"]["supported"] is False
    assert verdict["C_PRESSURE_COUPLING_AMPLIFIES_SMALL_VOLUME_EFFECT"]["supported"] is False
    assert verdict["D_BLEEDING_RATE_OR_TIMING_CAUSES_APPARENT_PROTECTION"]["supported"] is False and verdict["D_BLEEDING_RATE_OR_TIMING_CAUSES_APPARENT_PROTECTION"]["cofactor"] is True
    assert verdict["E_MULTIPLE_MECHANISMS"]["supported"] is False


def test_m8_early_improvement_reverses_slowly_under_continued_bleeding_without_source_control(built):
    early = built["early_treatment_without_source_control"]
    for case, row in early.items():
        assert row["bleed_ml_min_distinct"] == [2.5], case
        assert row["improvement_reverses_after_peak"] is True and row["slope_after_peak_mmHg_per_min"] < -0.1, case
        assert 55 <= row["peak"]["minute"] <= 80, case
        assert row["sbp"]["120"] < row["sbp"]["90"] < row["peak"]["sbp"], case
        assert row["sbp"]["240"] < row["sbp"]["120"], case
        assert row["stays_above_arrival_at_240"] is True and 240 < row["crosses_below_arrival_at_minute"] < 400, "the improvement outlasts four hours and then falls below the arrival value"
        assert row["sbp"]["60"] > row["untreated_sbp"]["60"] + 30


# -- what was NOT done --------------------------------------------------------------------------------------------------------------------------------

def _runtime_sources():
    skip = {"test_phase3_first_review_analysis.py", "test_gi_frg_crystalloid_analysis.py"}          # the analysis harness is test-side (renamed in P3-348)
    for path in sorted(ROOT.glob("*.py")):
        if not path.name.startswith("test_") and path.name not in skip:
            yield path
    yield from sorted((ROOT / "clinical_core").rglob("*.py"))


def test_n1_no_case_specific_branch_no_slow_infusion_multiplier_no_legacy_fit_in_any_runtime_source():
    forbidden = (re.compile(r"slow_infusion\w*"), re.compile(r"legacy_fit\w*"), re.compile(r"\b(?:if|elif)\b[^\n]*[\"']FR-G[\"']"),
                 re.compile(r"\b(?:if|elif)\b[^\n]*FR_G\b"), re.compile(r"\b(?:if|elif)\b[^\n]*case(?:_id)?\s*==\s*[\"']gi_bleed_72f[\"'][^\n]*(?:crystalloid|infusion)"))
    for path in _runtime_sources():
        text = path.read_text(encoding="utf-8")
        for pattern in forbidden:
            assert not pattern.search(text), f"{path.name}: {pattern.pattern}"


def test_n2_the_crystalloid_kernel_and_the_legacy_constants_are_untouched():
    import family_engine as legacy
    assert (legacy.GI_BLEED["crystalloid_per_ml"], legacy.GI_BLEED["crystalloid_transient"], legacy.GI_BLEED["crystalloid_leak_tau_min"]) == (0.00015, 0.6, 30.0)
    from clinical_core import legacy_adapter
    assert legacy_adapter.LEGACY_ML_PER_CIRCULATION_UNIT == 300.0 / 0.36
    import runtime_authority_pair as pair
    import runtime_pressure_grant as grants
    assert pair.V1_CORE_DIGEST == grants.CORE_DIGEST == "a0af7d08fec3aaf93606b5635cad9f26980428a5ab8d8f66afb1317bb4586ce2"
    assert fa.EVIDENCE_CLASS == "MODEL_ANALYSIS"


def test_n3_no_fr_g_v2_candidate_was_generated_because_no_correction_was_authorised_to_exist():
    stored = json.loads((ROOT / "docs" / "revision" / "PHASE3_FACULTY_TRAJECTORY_REVIEW_SET.json").read_text(encoding="utf-8"))
    assert [item["scenario_id"] for item in stored["items"]] == ["FR-A", "FR-B", "FR-C", "FR-D", "FR-E", "FR-F", "FR-G"]
    assert not any("V2" in json.dumps(item["scenario_id"]) for item in stored["items"])
    assert not list((ROOT / "docs" / "revision").glob("*FR-G_V2*")) and not list((ROOT / "docs" / "revision").glob("*FR_G_V2*"))


# -- P3-313: the checkpoint ------------------------------------------------------------------------------------------------------------------------------

def test_c1_the_checkpoint_points_at_the_current_records_and_says_what_was_not_done(human):
    checkpoint = json.loads((ROOT / "docs" / "revision" / "PHASE3_FIRST_FACULTY_REVIEW_CHECKPOINT.json").read_text(encoding="utf-8"))
    assert checkpoint["record_digest"] == _canonical_digest(checkpoint)
    pinned = checkpoint["pinned_records"]
    assert pinned["human_review_record_digest"] == human["record_digest"]
    assert pinned["analysis_record_digest"] == fa.load_record()["record_digest"]
    assert pinned["review_set_digest"] == ftr.PINNED_SET_DIGEST and pinned["p3_300_checkpoint_digest"] == P3_300_DIGEST
    assert checkpoint["overall"] == {"verdict": "B", "name": "FR_G_REQUIRES_NEW_FACULTY_VOLUME_DECISION"}
    statuses = checkpoint["statuses"]
    assert statuses["FIRST_HUMAN_FACULTY_REVIEW_RECORDED"] == "YES" and statuses["FR_G_ROOT_CAUSE"].startswith("B ")
    assert statuses["FR_G_V2_READY_FOR_HUMAN_REVIEW"].startswith("NO")
    assert all(checkpoint["confirmations"].values()), "every confirmation of the assignment is true"
    assert fa.load_record()["verdict"]["classified_as"] == "B"


def test_c2_the_documents_say_the_same_verdict_and_the_same_stop():
    doc = (ROOT / "docs" / "PHASE3_FIRST_FACULTY_REVIEW_ANALYSIS.md").read_text(encoding="utf-8")
    assert "B · CLOSED_VOLUME_REGION_TOO_PROTECTIVE_FOR_SLOW_INFUSION" in doc and "B · FR_G_REQUIRES_NEW_FACULTY_VOLUME_DECISION" in doc and "se DETIENE" in doc
    claude = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    assert "docs/PHASE3_FIRST_FACULTY_REVIEW_ANALYSIS.md" in claude and "FD-REVIEW-01 a FD-REVIEW-06" in claude
    cola = (ROOT / "docs" / "COLA_DECISIONES_AI_ADVISOR.md").read_text(encoding="utf-8")
    assert "PENDIENTE DE DECISIÓN DOCENTE" in cola and "| FD-P3-223 |" in cola
