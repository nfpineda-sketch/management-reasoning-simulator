"""P3-315 to P3-325: the absolute scale of the GI bleed rate, reopened after the first human faculty review.

What is protected, and kept apart:

* MODEL_ANALYSIS / TEST_RESULT: ``test_gi_bleed_rate_analysis`` is recomputed from the executable model and the frozen faculty evaluators and compared with the stored
  record, and each claim is asserted on its own: where 2.5 mL/min comes from, that no absolute blood loss is authored, that the untreated course reads only
  rate / scale, that a crystalloid infusion's protection reads only the rate, that the rate ALONE does not resolve FR-G under the current map, the joint region
  and its trade-off, and the verdict B;
* HUMAN_FACULTY_REVIEW: the human record, the reviewed set and the earlier checkpoints are byte-identical; nothing here reinterprets a human judgment;
* what was NOT done: no executable change, no rate approved, no pressure parameter moved, no FR-G V2 candidate, no Amendment 3, no norepinephrine, no source
  control.

``MRS_WRITE_BLEED_RATE_ANALYSIS=1 python3 test_gi_bleed_rate_analysis.py`` regenerates the stored record, only when the analysis itself changes.
"""
import hashlib
import json
from pathlib import Path

import pytest

import faculty_trajectory_review as ftr
import test_gi_frg_crystalloid_analysis as fa
import test_gi_bleed_rate_analysis as ga

ROOT = Path(__file__).resolve().parent
REVISION = ROOT / "docs" / "revision"
HUMAN_DIGEST = "9ba80fa70d3b38e178caa3aca9432f9227ce6d9591a48c9908c3f5ac4cc6c8d3"
P3_313_DIGEST = "093262fa98e9a4a476ad6005b1c5c6954858ddafd380ad8538c7c7e9bb644bf5"
P3_300_DIGEST = "45b62670af0983f3513e5ec5b290ff866da073b3100177dfa5f4d1a5729c89b2"
RUNTIME, REGION = "RUNTIME_OUTSIDE_THE_CLOSED_REGION", "CLOSED_REGION_LEAST_PROTECTIVE"


def _sealed(record: dict) -> str:
    body = {key: value for key, value in record.items() if key != "record_digest"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()


@pytest.fixture(scope="module")
def built() -> dict:
    return ga.build()


# -- the record is the recomputed one ---------------------------------------------------------------------------------------------------------------

def test_a1_the_stored_analysis_is_exactly_what_the_executable_model_gives_now(built):
    stored = ga.load_record()
    assert built["record_digest"] == stored["record_digest"] == ga.digest(stored), "regenerate with MRS_WRITE_BLEED_RATE_ANALYSIS=1 only when the analysis itself changes"
    assert stored["evidence_class"] == "MODEL_ANALYSIS" and stored["executable_change"] is False
    assert stored["depends_on"]["frg_crystalloid_analysis_record_digest"] == fa.load_record()["record_digest"]


# -- P3-315: provenance ---------------------------------------------------------------------------------------------------------------------------------

def test_b1_the_origin_of_2_5_ml_min_is_a_unit_conversion_of_a_legacy_teaching_magnitude(built):
    provenance = built["provenance"]
    assert provenance["all_checks_hold"] and all(provenance["checks"].values())
    live = provenance["live"]
    assert live["legacy_circulation_per_min"] == 0.003 and live["legacy_circulation_per_unit"] == 0.36 and abs(live["ml_per_circulation_unit"] - 300.0 / 0.36) < 1e-6
    assert abs(live["runtime_rate_ml_min"] - 2.5) < 1e-9 and live["reference_rate_ml_min"] == 2.5
    assert abs(live["runtime_rate_ml_min"] / live["default_preload_scale_ml"] - live["legacy_circulation_per_min"]) < 1e-9, "rate / scale IS the legacy literal"
    assert provenance["status_of_2_5"] == "LEGACY_DERIVED" and "HISTORICAL_DEVELOPMENT_REFERENCE" in provenance["faculty_classification"]
    statuses = [row["status"] for row in provenance["records"]]
    assert set(statuses) <= set(ga.STATUSES) and "AUTHORED_CASE" not in statuses, "no case ever authored a rate"
    faculty = [row for row in provenance["records"] if row["status"] == "FACULTY_DEFINED"]
    assert len(faculty) == 1 and faculty[0]["value"] == "none", "the only faculty-defined record is the POLICY: no numeric rate was ever approved"
    import family_engine
    source = Path(family_engine.__file__).read_text(encoding="utf-8")
    assert 'f["circulation"] += (.003 + .002 * f["anticoagulant_exposure"]) * bleeding' in source, "the legacy line the literal is quoted from"


# -- P3-316: the authored cases -------------------------------------------------------------------------------------------------------------------------

def test_c1_the_cases_author_the_arrival_state_and_no_absolute_blood_loss(built):
    authored = built["authored_cases"]
    assert authored["absolute_blood_loss"] == "ABSOLUTE_BLOOD_LOSS_NOT_DIRECTLY_AUTHORED"
    assert authored["estimable_with_confidence_0_80"] == {"ml_per_min": False, "ml_per_hour": False, "total_blood_lost": False}
    expected = {"gi_bleed_57m": ("88/54 mmHg", "6.7 g/dL", "4.4 mmol/L"), "gi_bleed_72f": ("98/62 mmHg", "6.4 g/dL", "3.4 mmol/L")}
    for case, rows in authored["cases"].items():
        by_item = {row["item"]: row for row in rows}
        assert {row["class"] for row in rows} == {"EXPLICIT_CASE_FACT", "INFERRED_SEVERITY_ONLY", "NOT_SPECIFIED"}
        assert (by_item["arrival blood pressure"]["evidence"], by_item["haemoglobin"]["evidence"], by_item["lactate"]["evidence"]) == expected[case]
        for name in ("reported amount of blood lost", "rate of the ongoing loss (mL/min or mL/h)", "total blood lost", "duration of the hypoperfusion"):
            assert by_item[name]["class"] == "NOT_SPECIFIED", (case, name)
        assert by_item["severity of the haemorrhage"]["class"] == "INFERRED_SEVERITY_ONLY"
        assert "black" in by_item["reported bleeding source"]["evidence"].lower() and by_item["reported bleeding source"]["class"] == "EXPLICIT_CASE_FACT"


# -- P3-317: the current scale -------------------------------------------------------------------------------------------------------------------------

def test_d1_the_three_concepts_stay_apart_and_one_hour_of_bleeding_is_half_a_litre_to_a_litre_of_saline(built):
    scale = built["current_scale"]
    assert scale["rate_ml_min"] == 2.5 and scale["ml_per_hour"] == 150.0
    for case, item in scale["cases"].items():
        rows = item["at"]
        assert [rows[str(m)]["A_literal_blood_shed_ml"] for m in (30, 60, 120, 180)] == [75.0, 150.0, 300.0, 450.0]
        assert rows["120"]["A_as_share_of_the_reference_arrival_volume_pct"] == 7.5
        assert all(rows[str(m)]["B_effective_circulating_deficit_ml_eq"] < rows[str(m)]["A_literal_blood_shed_ml"] for m in (60, 120, 180)), "the deficit is the shed blood LESS the refill"
        assert all(abs(rows[str(m)]["C_dimensionless_V_over_scale"] * 833.333333 + rows[str(m)]["B_effective_circulating_deficit_ml_eq"]) < 1e-3 for m in (60, 120))
        assert rows["60"]["sbp"] > rows["120"]["sbp"] > rows["180"]["sbp"] and 0.0 < rows["120"]["hb_fall_g_dl"] < 0.2, "whole-blood loss barely moves the haemoglobin"
        assert item["core_boundary_minute_untreated"] == 349
    assert abs(scale["zero_output_deficit_ml_eq"] - 577.62265) < 1e-4 and 14.0 < scale["zero_output_deficit_share_of_arrival_volume_pct"] < 15.0
    hour = scale["one_hour_of_bleeding_in_faculty_approved_units"]
    assert hour["red_cell_units"] == 0.5 and hour["litres_of_saline_by_FD_BLD_04_early_contribution"] == [0.5, 1.0]


# -- P3-318: the inversion of the untreated course under the current map ------------------------------------------------------------------------------

def test_e1_under_the_current_map_the_untreated_evidence_pins_the_rate_to_a_narrow_band_near_the_reference(built):
    inversion = built["untreated_inversion"]
    intervals = inversion["u_out_rate_interval_ml_min"]
    assert [round(v, 3) for v in intervals["gi_bleed_57m"]] == [2.55, 3.723] and [round(v, 3) for v in intervals["gi_bleed_72f"]] == [1.689, 2.804], "the bands of P3-89, still current"
    assert [round(v, 3) for v in inversion["u_out_common_interval_ml_min"]] == [2.55, 2.804]
    assert inversion["reference_rate_inside_the_common_u_out_band"] is False and 1.9 < inversion["reference_below_the_common_lower_edge_pct"] < 2.0
    low, high = inversion["broad_common_interval_ml_min"]
    assert 2.0 < low < 2.5 < high < 3.2, "the broad time-window reading contains the reference and is no wider than about a quarter either way"
    witnesses = inversion["witnesses"]
    assert list(witnesses) == ["LOWER_72F_U_OUT_EDGE", "BROAD_WINDOW_LOWER", "REFERENCE", "COMMON_U_OUT_LOWER", "COMMON_U_OUT_UPPER", "BROAD_WINDOW_UPPER", "HIGH_57M_U_OUT_EDGE"]
    assert max(item["rate_ml_min"] for item in witnesses.values()) < 4.0, "no arbitrary enormous rate under the current map"
    for label, item in witnesses.items():
        assert item["why"] and item["ordering_57m_below_72f"], label
        assert all(case["remains_below_arrival"] and case["progressively_worsens"] for case in item["cases"].values()), label
    assert witnesses["COMMON_U_OUT_UPPER"]["cases"]["gi_bleed_72f"]["u_out"] and not witnesses["BROAD_WINDOW_UPPER"]["cases"]["gi_bleed_72f"]["u_out"]
    assert witnesses["HIGH_57M_U_OUT_EDGE"]["cases"]["gi_bleed_72f"]["core_boundary_minute"] is not None, "the fastest witness already ends the untreated run of 72f at the core's boundary"


# -- P3-319: identifiability ----------------------------------------------------------------------------------------------------------------------------

def test_f1_the_untreated_course_reads_rate_over_scale_and_the_infusion_s_protection_reads_the_rate(built):
    ident = built["identifiability"]
    assert ident["untreated_course_on_the_joint_manifold"]["invariant"] and ident["untreated_course_on_the_joint_manifold"]["max_abs_sbp_difference_mmHg"] < 1e-9
    assert ident["u_out_bounds_rate_over_scale"]["holds"] and ident["u_out_bounds_rate_over_scale"]["max_abs_difference_in_c"] < 1e-6
    free = ident["crystalloid_protection_is_map_free"]
    assert free["holds"] and all(item["max_minus_min"] < 0.05 for item in free["by_rate"].values())
    by_rate = {float(rate): item["p60_across_six_pressure_maps"] for rate, item in free["by_rate"].items()}
    assert min(by_rate[2.5]) > max(by_rate[4.5]) + 0.2, "the protection moves with the RATE, not with the map"
    assert ident["effective_dimension"]["from_untreated_evidence"] == 1 and ident["effective_dimension"]["absolute_rate_from_untreated_evidence"] == "NOT IDENTIFIED AT ALL"
    assert ident["verdict"] == "B" and ident["verdict_name"] == "BLEED_RATE_AND_PRESSURE_MAP_REQUIRE_JOINT_REGION"
    assert ident["circular_reuse_found"] is False and len(ident["constraints_and_their_single_use"]) == 5


# -- P3-320: rate x crystalloid -------------------------------------------------------------------------------------------------------------------------

def test_g1_under_the_current_map_no_admitted_rate_brings_fr_g_below_one_half(built):
    crystalloid = built["rate_x_crystalloid"]
    current = crystalloid["current_map_witnesses"]
    admitted = [label for label, item in current.items() if item["admitted_for_72f_by_u_out"]]
    assert admitted == ["LOWER_72F_U_OUT_EDGE", "BROAD_WINDOW_LOWER", "REFERENCE", "COMMON_U_OUT_LOWER", "COMMON_U_OUT_UPPER"]
    for label in admitted:
        assert current[label][RUNTIME]["share_of_untreated_pressure_fall_prevented"]["60"] > 0.55, label
        assert current[label][RUNTIME]["class"] in ("SUBSTANTIAL_PROTECTION", "NEAR_STABILIZATION") and current[label][REGION]["class"] == "NEAR_STABILIZATION"
    reference = current["REFERENCE"][RUNTIME]
    assert reference["blood_lost_by_60_ml"] == 150.0 and abs(reference["crystalloid_retained_at_60_ml"] - 81.887514) < 1e-5 and abs(reference["retained_over_lost"] - 0.545917) < 1e-5
    assert abs(reference["net_effective_volume_change_at_60_ml"] + 52.38) < 0.01 and abs(reference["share_of_untreated_pressure_fall_prevented"]["60"] - 0.6289) < 1e-3
    shares = [current[label][RUNTIME]["share_of_untreated_pressure_fall_prevented"]["60"] for label in current]
    assert shares == sorted(shares, reverse=True), "the protection falls monotonically as the rate rises"
    edges = crystalloid["current_map_edges"]
    assert edges[RUNTIME]["closer_to_untreated_p60_one_half"]["untreated_u_out_72f"] is False and edges[RUNTIME]["modest_p60_one_third"]["untreated_core_boundary_minute"] is not None
    assert edges[RUNTIME]["modest_p60_one_third"]["rate_ml_min"] > 5.0 and edges[REGION]["modest_p60_one_third"]["rate_ml_min"] > 9.0
    assert edges[REGION]["modest_p60_one_third"]["untreated_core_boundary_minute"] < 80, "at that rate the untreated patient of the current map does not last 80 minutes"


def test_g2_on_the_joint_manifold_the_protection_falls_with_the_scale_and_the_edges_are_ordered(built):
    crystalloid = built["rate_x_crystalloid"]
    joint, edges = crystalloid["joint_witnesses_at_the_accepted_untreated_course"], crystalloid["joint_edges"]
    assert 841.0 < crystalloid["fd_bld_02_smallest_scale_72f"] < 841.2, "one unit raises output by exactly 30 % at this scale"
    assert joint["REFERENCE"]["one_unit"]["gi_bleed_72f"]["fd_bld_02"] is False and joint["FD_BLD_02_EDGE_72F"]["one_unit"]["gi_bleed_72f"]["fd_bld_02"] is True
    scales = [edges[RUNTIME]["closer_to_untreated_p60_one_half"]["scale_ml_eq"], 1500.0, edges[RUNTIME]["modest_p60_one_third"]["scale_ml_eq"],
              edges[REGION]["closer_to_untreated_p60_one_half"]["scale_ml_eq"], edges[REGION]["modest_p60_one_third"]["scale_ml_eq"]]
    assert scales == sorted(scales) and 1000 < scales[0] < 1100 and 1600 < scales[2] < 1650 and 1700 < scales[3] < 1800 and 2600 < scales[4] < 2700
    assert edges[RUNTIME]["closer_to_untreated_p60_one_half"]["inside_the_declared_scale_band"] is True
    assert not any(edges[name]["modest_p60_one_third"]["inside_the_declared_scale_band"] for name in (RUNTIME, REGION)), "one third is not reachable inside the declared band at the committed position"
    top = joint["DECLARED_BAND_TOP"]
    assert abs(top[RUNTIME]["share_of_untreated_pressure_fall_prevented"]["60"] - 0.357) < 5e-3 and abs(top[REGION]["share_of_untreated_pressure_fall_prevented"]["60"] - 0.577) < 5e-3
    for label, item in joint.items():
        assert abs(item[RUNTIME]["sbp_untreated"]["60"] - 80.867059) < 1e-5, f"{label}: the untreated course is the accepted one at every joint witness"
        assert item[RUNTIME]["crystalloid_retained_at_60_ml"] < item[REGION]["crystalloid_retained_at_60_ml"]
    modest = joint[f"EDGE_MODEST_P60_ONE_THIRD__{REGION}"]
    assert modest[REGION]["class"] == "MODEST_TRANSIENT_ATTENUATION" and modest["outside_the_declared_scale_band"] and 9.0 < modest["sbp_rise_per_red_cell_unit_at_arrival_mmHg"]["gi_bleed_72f"] < 11.0
    assert 29.0 < joint["REFERENCE"]["sbp_rise_per_red_cell_unit_at_arrival_mmHg"]["gi_bleed_72f"] < 30.0


def test_g3_the_most_favourable_corner_of_every_declared_domain_still_leaves_a_closed_region_kernel_above_one_third(built):
    corner = built["rate_x_crystalloid"]["declared_domain_most_favourable_corner"]
    assert corner["scale_ml_eq"] == 1500.0 and corner["arrival_positions"] == {"gi_bleed_57m": 0.5, "gi_bleed_72f": 0.6}
    assert all(corner["u_out_both_cases"].values()) and all(item["fd_bld_02"] for item in corner["one_unit"].values())
    assert 6.6 < corner["common_rate_ml_min"] < 6.8, "consistent with P2I-2X: rate 6 viable, rate 7 the first tested non-viable"
    assert corner[RUNTIME]["class"] == "MODEST_TRANSIENT_ATTENUATION" and abs(corner[RUNTIME]["share_of_untreated_pressure_fall_prevented"]["60"] - 0.249) < 5e-3
    assert corner[REGION]["class"] == "SUBSTANTIAL_PROTECTION" and corner[REGION]["closer_to_untreated_than_to_stable"] and abs(corner[REGION]["share_of_untreated_pressure_fall_prevented"]["60"] - 0.402) < 5e-3


# -- P3-321 and P3-322: the region and the other scenarios ---------------------------------------------------------------------------------------------

def test_h1_the_region_is_joint_never_a_rate_interval_and_the_current_point_is_just_outside_its_low_corner(built):
    region = built["joint_region"]
    assert region["name"] == "GI_BLEED_RATE_PRESSURE_JOINT_DEVELOPMENT_REGION" and "NOT_APPROVED" in region["status"] and region["a_rate_interval_alone_is_defined"] is False
    coordinates = region["coordinates"]
    assert coordinates["c_rate_over_scale_per_min"]["current_inside"] is False and coordinates["scale_ml_eq"]["current_inside"] is False and region["the_current_point"]["inside_the_joint_region"] is False
    assert [round(v, 6) for v in coordinates["c_rate_over_scale_per_min"]["band_at_position_0_5_common_to_both_cases"]] == [0.00306, 0.003365]
    rates = region["implied_absolute_rate_ml_min"]
    assert 2.5 < rates["lower_corner_at_position_0_5"] < 2.6 and [round(v, 2) for v in rates["top_of_the_declared_band_at_position_0_5"]] == [4.59, 5.05]
    assert region["shared_or_case_specific"]["verdict"] == "ONE_FAMILY_REGION_SERVES_BOTH_CASES"
    assert region["confidence"]["in_any_single_number_for_the_fr_g_edge"] < 0.8 <= region["confidence"]["that_the_rate_is_identified_only_jointly_with_the_scale"]
    assert len(region["falsifiers"]) >= 3 and len(region["uncertainty"]) >= 3


def test_h2_the_qualitative_faculty_conclusions_hold_at_every_joint_witness_but_the_magnitudes_of_the_treated_courses_move(built):
    nonregression = built["nonregression"]
    assert nonregression["reference_reproduces_the_reviewed_pressures"] and nonregression["untreated_courses_identical_at_every_joint_witness"]
    witnesses = nonregression["witnesses"]
    assert list(witnesses) == ["REFERENCE", "DECLARED_BAND_TOP", "DECLARED_BAND_TOP__REGION_KERNEL", "EDGE_MODEST__RUNTIME", "EDGE_MODEST__REGION"]
    for label, item in witnesses.items():
        scenarios = item["scenarios"]
        assert scenarios["FR-A"]["progressive_deterioration"] and scenarios["FR-D"]["progressive_deterioration"], label
        assert scenarios["FR-B"]["early_response_above_arrival"], f"{label}: FR-B's early response is still above arrival"
        assert scenarios["FR-C"]["rises_after_treatment"] and scenarios["FR-E"]["rises_after_treatment"], f"{label}: the delayed rescue still rises"
        for case, long in item["early_treatment_to_240_min_without_source_control"].items():
            assert long["reverses_after_the_peak"] and not long["plateau_in_the_last_hour"], (label, case)
            assert long["bleeding_ml_min_distinct"] == [round(item["rate_ml_min"], 9)], "the bleeding never stops: no source control"
    rises = [witnesses[label]["early_treatment_to_240_min_without_source_control"]["gi_bleed_57m"]["peak"]["rise_over_arrival"] for label in ("REFERENCE", "DECLARED_BAND_TOP", "EDGE_MODEST__RUNTIME", "EDGE_MODEST__REGION")]
    assert rises == sorted(rises, reverse=True) and rises[0] > 35 and rises[-1] < 8, "the same scale that makes slow saline modest makes two units of blood weak"
    below = [witnesses[label]["early_treatment_to_240_min_without_source_control"]["gi_bleed_57m"]["below_arrival_again_at_minute"] for label in ("DECLARED_BAND_TOP", "EDGE_MODEST__RUNTIME", "EDGE_MODEST__REGION")]
    assert witnesses["REFERENCE"]["early_treatment_to_240_min_without_source_control"]["gi_bleed_57m"]["below_arrival_again_at_minute"] is None and below == sorted(below, reverse=True) and below[-1] < 100
    assert witnesses["REFERENCE"]["scenarios"]["FR-E"]["ends_above_arrival"] and not witnesses["DECLARED_BAND_TOP"]["scenarios"]["FR-E"]["ends_above_arrival"]


# -- P3-323 and P3-324: no candidate, verdict B ----------------------------------------------------------------------------------------------------------

def test_i1_the_verdict_is_B_the_rate_alone_does_not_resolve_and_no_v2_candidate_exists(built):
    decision = built["decision"]
    assert decision["rate_alone_under_the_current_map_resolves_fr_g"] is False and decision["smallest_p60_among_admitted_current_map_witnesses"] > 0.5
    assert decision["a_joint_rescale_can_reach_modest_attenuation"] is True
    amendment = decision["amendment_3_decision"]
    assert amendment["verdict"] == "B" and amendment["name"] == "JOINT_RATE_PRESSURE_CALIBRATION_REQUIRED" and amendment["amendment_3"] == "NOT_OPENED__UNRESOLVED"
    assert set(amendment["why_not"]) == {"A", "C", "D", "E"}
    assert decision["fr_g_v2_candidate"]["generated"] is False
    stored = json.loads((REVISION / "PHASE3_FACULTY_TRAJECTORY_REVIEW_SET.json").read_text(encoding="utf-8"))
    assert [item["scenario_id"] for item in stored["items"]] == ["FR-A", "FR-B", "FR-C", "FR-D", "FR-E", "FR-F", "FR-G"] and stored["record_digest"] == ftr.PINNED_SET_DIGEST
    assert not list(REVISION.glob("*V2*")), "no FR-G V2 artifact was fabricated"


# -- nothing human was reinterpreted, nothing executable moved -------------------------------------------------------------------------------------------

def test_j1_the_human_review_and_the_earlier_records_are_byte_identical():
    human = json.loads((REVISION / "PHASE3_FIRST_HUMAN_FACULTY_REVIEW.json").read_text(encoding="utf-8"))
    assert human["record_digest"] == _sealed(human) == HUMAN_DIGEST
    overall = {row["scenario_id"]: row["overall"] for row in human["scenarios"]}
    assert overall == {"FR-B": "ACCEPT_WITH_LIMITATION", "FR-A": "ACCEPT_WITH_LIMITATION", "FR-E": "ACCEPT", "FR-G": "RECALIBRATE", "FR-F": "ACCEPT_WITH_LIMITATION",
                       "FR-D": "ACCEPT_WITH_LIMITATION", "FR-C": "ACCEPT_WITH_LIMITATION"}
    assert json.loads((REVISION / "PHASE3_FIRST_FACULTY_REVIEW_CHECKPOINT.json").read_text(encoding="utf-8"))["record_digest"] == P3_313_DIGEST
    assert json.loads((REVISION / "PHASE3_FACULTY_REVIEW_CHECKPOINT.json").read_text(encoding="utf-8"))["record_digest"] == P3_300_DIGEST


def test_j2_no_rate_no_pressure_parameter_and_no_physiology_moved():
    import family_engine as legacy
    import runtime_authority_pair as pair
    import runtime_pressure_grant as grants
    from clinical_core import blood_anchors, calibration, derived, legacy_adapter
    assert legacy_adapter.LEGACY_LITERALS["gi_bleeding_circulation_per_min"][0] == 0.003 and derived.LEGACY_ML_PER_CIRCULATION_UNIT == 300.0 / 0.36
    assert derived.DEFAULT_PROFILE.preload_curve_scale_ml == 300.0 / 0.36 and derived.DEFAULT_PROFILE.arrival_preload_fraction == 0.5
    band = calibration.REGISTRY["preload_curve_scale_ml"]
    assert (band.lower, band.upper, band.status) == (*ga.DECLARED_SCALE_BAND, "CANDIDATE")
    assert blood_anchors.REFERENCE["bleed_ml_per_min"] == 2.5
    assert (legacy.GI_BLEED["crystalloid_per_ml"], legacy.GI_BLEED["crystalloid_transient"], legacy.GI_BLEED["crystalloid_leak_tau_min"]) == (0.00015, 0.6, 30.0)
    assert pair.V1_CORE_DIGEST == grants.CORE_DIGEST == "a0af7d08fec3aaf93606b5635cad9f26980428a5ab8d8f66afb1317bb4586ce2"
    from clinical_core import amendment_2
    assert amendment_2.amended_core_digest_now() == grants.CORE_DIGEST, "every source of clinical_core/ is the certified one: no physiology was added, source control included"
    for path in sorted((ROOT / "clinical_core").rglob("*.py")):
        assert "norepinephrine" not in path.read_text(encoding="utf-8").lower(), f"{path.name}: norepinephrine was not implemented"


# -- P3-325: the decisions, the debt and the checkpoint -------------------------------------------------------------------------------------------------

def test_k1_the_decisions_are_recorded_under_ids_that_do_not_collide_with_the_frozen_blood_constraints():
    from clinical_core import blood_constraints as bc
    assert set(bc.FD_BLD_STATUS) == {f"FD-BLD-0{index}" for index in range(1, 10)}, "FD-BLD-01 to FD-BLD-09 already name the frozen faculty blood constraints"
    cola = (ROOT / "docs" / "COLA_DECISIONES_AI_ADVISOR.md").read_text(encoding="utf-8")
    for index in range(1, 9):
        assert f"| FD-RATE-0{index} |" in cola
    for index in range(225, 230):
        assert f"| FD-P3-{index} |" in cola
    assert "HISTORICAL_DEVELOPMENT_REFERENCE" in cola and "en el encargo: «FD-BLD-0" in cola
    debt = (ROOT / "docs" / "REGISTRO_DEUDA_TECNICA.md").read_text(encoding="utf-8")
    assert "## TD-148" in debt and "norepinefrina" in debt.split("## TD-148")[1].lower()


def test_k2_the_checkpoint_points_at_the_current_records_and_says_the_same_verdict(built):
    checkpoint = json.loads((REVISION / "PHASE3_BLEED_RATE_SCALE_CHECKPOINT.json").read_text(encoding="utf-8"))
    assert checkpoint["record_digest"] == _sealed(checkpoint)
    pinned = checkpoint["pinned_records"]
    assert pinned["analysis_record_digest"] == ga.load_record()["record_digest"] == built["record_digest"]
    assert pinned["human_review_record_digest"] == HUMAN_DIGEST and pinned["p3_313_checkpoint_digest"] == P3_313_DIGEST and pinned["review_set_digest"] == ftr.PINNED_SET_DIGEST
    assert set(checkpoint["statuses"]) == {"BLEED_RATE_PROVENANCE", "AUTHORED_ABSOLUTE_BLOOD_LOSS_EVIDENCE", "UNTREATED_BEHAVIORAL_COMPATIBILITY", "RATE_IDENTIFIABILITY", "RATE_PRESSURE_COUPLING",
                                           "FR_G_SENSITIVITY", "OTHER_GI_NONREGRESSION", "LONG_HORIZON_SOURCE_CONTROL_RISK", "FR_G_V2_STATUS", "AMENDMENT3_STATUS"}
    assert checkpoint["overall"] == {"verdict": "B", "name": "JOINT_RATE_PRESSURE_CALIBRATION_REQUIRED"} and all(checkpoint["confirmations"].values())
    doc = (ROOT / "docs" / "PHASE3_GI_BLEED_RATE_SCALE.md").read_text(encoding="utf-8")
    assert "B · JOINT_RATE_PRESSURE_CALIBRATION_REQUIRED" in doc and "B · BLEED_RATE_AND_PRESSURE_MAP_REQUIRE_JOINT_REGION" in doc and "ABSOLUTE_BLOOD_LOSS_NOT_DIRECTLY_AUTHORED" in doc
    assert "docs/PHASE3_GI_BLEED_RATE_SCALE.md" in (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
