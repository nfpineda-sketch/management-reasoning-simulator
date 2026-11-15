"""P3-327 to P3-336: can the current GI physiology satisfy the three faculty anchors at once?

What is protected, and kept apart:

* MODEL_ANALYSIS / TEST_RESULT: ``gi_joint_feasibility_analysis`` is recomputed from the executable model and the frozen faculty evaluators and compared with
  the stored record; each claim is asserted on its own: the mechanism and the timing of one red-cell unit, the three reduced coordinates, the three constraints
  in their own coordinates, the feasible region and its projections, the witnesses, the structural reading and the gate verdict A;
* the faculty anchors FD-RATE-09 and FD-RATE-10 are the numbers the faculty gave, and nothing here narrows them to a point;
* what was NOT done: no executable change, no rate, pressure parameter or kernel approved, no point chosen, no Amendment 3 design or implementation, no change
  of the closed crystalloid region, no FR-G V2 candidate, no norepinephrine, no source control; the human review and every earlier record are byte-identical.

``MRS_WRITE_JOINT_FEASIBILITY=1 python3 gi_joint_feasibility_analysis.py`` regenerates the stored record, only when the analysis itself changes.
"""
import hashlib
import json
from pathlib import Path

import pytest

import faculty_trajectory_review as ftr
import gi_bleed_rate_analysis as ga
import gi_joint_feasibility_analysis as gj

ROOT = Path(__file__).resolve().parent
REVISION = ROOT / "docs" / "revision"
HUMAN_DIGEST = "9ba80fa70d3b38e178caa3aca9432f9227ce6d9591a48c9908c3f5ac4cc6c8d3"
P3_325_DIGEST = "3198f62afd98655768e38e3e2ccceb226fe6cf842655c8b899d90ce4318d94f3"
P3_313_DIGEST = "093262fa98e9a4a476ad6005b1c5c6954858ddafd380ad8538c7c7e9bb644bf5"
P3_300_DIGEST = "45b62670af0983f3513e5ec5b290ff866da073b3100177dfa5f4d1a5729c89b2"
RUNTIME, REGION = "RUNTIME_OUTSIDE_THE_CLOSED_REGION", "CLOSED_REGION_LEAST_PROTECTIVE"


def _sealed(record: dict) -> str:
    body = {key: value for key, value in record.items() if key != "record_digest"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()


def doc_text(root: Path) -> str:
    return (root / "docs" / "PHASE3_GI_JOINT_FEASIBILITY.md").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def built() -> dict:
    return gj.build()


def test_a1_the_stored_analysis_is_exactly_what_the_executable_model_gives_now(built):
    stored = gj.load_record()
    assert built["record_digest"] == stored["record_digest"] == gj.digest(stored), "regenerate with MRS_WRITE_JOINT_FEASIBILITY=1 only when the analysis itself changes"
    assert stored["evidence_class"] == "MODEL_ANALYSIS" and stored["executable_change"] is False
    assert stored["depends_on"]["bleed_rate_scale_record_digest"] == ga.load_record()["record_digest"]


def test_a2_the_faculty_anchors_are_the_ones_the_faculty_gave_and_no_point_is_chosen_inside_them(built):
    anchors = built["faculty_anchors"]
    assert anchors["FD-RATE-09"]["one_unit_sbp_rise_mmHg"] == [8.0, 18.0] and anchors["FD-RATE-09"]["window_min"] == [15, 30] and anchors["FD-RATE-09"]["too_large_from_mmHg"] == 25.0
    assert anchors["FD-RATE-10"]["share_of_untreated_deterioration_prevented_at_60"] == [0.15, 0.35]
    assert anchors["FD-RATE-09"]["status"] == anchors["FD-RATE-10"]["status"] == "FACULTY_DEFINED_DEVELOPMENT_BEHAVIORAL_REGION"
    assert "UNRESOLVED_ABSOLUTE_SCALE" in anchors["FD-RATE-11"]
    assert all(item["is_a_chosen_point"] is False for item in built["witnesses"].values())


# -- P3-327 and P3-327A ----------------------------------------------------------------------------------------------------------------------------------

def test_b1_one_unit_is_300_ml_at_20_g_dl_delivered_linearly_over_30_minutes_and_the_response_is_a_closed_form_of_the_scale(built):
    mechanism = built["prbc_mechanism"]
    for case, item in mechanism["cases"].items():
        unit = item["contributor"]
        assert (unit["units"], unit["volume_ml_per_unit"], unit["unit_hb_g_dl"], unit["duration_min"]) == (1.0, 300.0, 20.0, None) and abs(unit["untimed_units_per_min"] - 1 / 30) < 1e-6, case
        assert item["closed_form_agrees"] and item["hb_agrees"] and item["delivery_is_linear"] and item["nothing_after_the_unit_ends"], case
        chain = item["chain_at_the_current_point"]
        assert [chain[m]["effective_volume_change_ml_eq"] for m in ("0", "5", "15", "30", "45")] == [0.0, 50.0, 150.0, 300.0, 300.0]
        assert chain["0"]["sbp"] < chain["5"]["sbp"] < chain["15"]["sbp"] < chain["30"]["sbp"] == chain["45"]["sbp"], "not instantaneous, complete at minute 30"
        assert 0.5 < item["share_of_the_response_at_15_min"] < 0.6
        assert item["current_point_is_too_large_by_FD_RATE_09"] is True, "the current point gives +27 / +30 mmHg: the faculty calls 25 to 30 too large"
    assert abs(mechanism["cases"]["gi_bleed_57m"]["sbp_rise_at_30_mmHg"] - 26.604) < 1e-3 and abs(mechanism["cases"]["gi_bleed_72f"]["sbp_rise_at_30_mmHg"] - 29.628) < 1e-3
    assert abs(mechanism["cases"]["gi_bleed_72f"]["hb_at_30"] - 7.348837) < 1e-5
    timing = mechanism["timing"]
    assert timing["class"] == "FINITE_DURATION_INFUSION" and timing["instantaneous"] is False and timing["response_complete_at_minute"] == 30


# -- P3-328 ----------------------------------------------------------------------------------------------------------------------------------------------

def test_c1_three_constraints_read_three_coordinates_and_blood_and_crystalloid_move_together(built):
    reduction = built["reduction"]
    assert reduction["b_reads_the_scale_only"]["holds"] and reduction["c_reads_the_rate_and_the_kernel_only"]["holds"]
    assert reduction["c_reads_the_rate_and_the_kernel_only"]["max_minus_min"] < 0.03
    coupling = reduction["b_and_c_are_coupled_through_one_volume_channel"]
    for name, low, high in ((RUNTIME, 1.85, 2.05), (REGION, 3.0, 3.3)):
        assert all(low < value < high for value in coupling[name]["share_prevented_over_one_unit_gain_at_three_scales"]) and coupling[name]["spread"] < 0.1, name
    assert abs(coupling[RUNTIME]["retained_over_one_unit_volume"] - 0.273) < 1e-3 and abs(coupling[REGION]["retained_over_one_unit_volume"] - 0.449) < 1e-3
    assert set(reduction["coordinates"]) == {"A_untreated", "B_one_unit", "C_slow_crystalloid"}


# -- P3-329 ----------------------------------------------------------------------------------------------------------------------------------------------

def test_d1_each_constraint_in_its_own_coordinate_at_the_committed_position(built):
    primary = built["feasibility"]["by_shared_arrival_position"]["0.5"]
    assert [round(v, 6) for v in primary["A_untreated"]["common_c"]] == [0.00306, 0.003365] and primary["A_untreated"]["status"] == "NONEMPTY"
    b = primary["B_one_unit"]
    assert [round(v) for v in b["per_case_scale_ml_eq"]["gi_bleed_57m"]] == [1311, 3148] and [round(v) for v in b["per_case_scale_ml_eq"]["gi_bleed_72f"]] == [1478, 3523]
    assert [round(v) for v in b["common_scale_ml_eq"]] == [1478, 3148] and b["status"] == "NONEMPTY"
    assert [round(v, 2) for v in primary["A_x_B_bleed_rate_ml_min"]] == [4.52, 10.59]
    closed = primary["C_slow_crystalloid_by_kernel"][REGION]
    assert closed["status"] == "NONEMPTY" and [round(v) for v in closed["scale_ml_eq"]] == [2258, 3148] and [round(v, 2) for v in closed["bleed_rate_ml_min"]] == [7.6, 10.59]
    assert abs(closed["share_prevented"][0] - 0.2532) < 1e-3 and closed["share_prevented"][1] == 0.35
    assert abs(closed["one_unit_sbp_rise_mmHg"]["gi_bleed_72f"][1] - 12.19) < 0.01 and abs(closed["one_unit_sbp_rise_mmHg"]["gi_bleed_57m"][0] - 8.0) < 1e-3
    assert closed["binding"] == {"smallest_scale": "the 35 % ceiling of the slow-crystalloid share", "largest_scale": "the +8 mmHg floor of one unit"}
    assert closed["share_at_the_most_protected_corner"] > 0.35 > closed["share_at_the_least_protected_corner"] > 0.15, "the box A x B is cut by the ceiling, not swallowed and not missed"


def test_d2_the_region_is_nonempty_with_every_existing_constraint_and_lies_wholly_above_the_declared_scale_band(built):
    feasibility = built["feasibility"]
    assert feasibility["status"] == feasibility["three_anchors_only_status"] == "NONEMPTY"
    verified = feasibility["with_every_existing_constraint_readable_and_met"]
    assert [round(v, 2) for v in verified["bleed_rate_ml_min"]] == [7.6, 9.33] and [round(v) for v in verified["scale_ml_eq"]] == [2258, 3048] and verified["status"] == "NONEMPTY"
    assert "FD-BLD-06 in 57m" in verified["limited_by"] and "UNREADABLE, not failed" in verified["limited_by"]
    band = feasibility["relative_to_the_declared_scale_band"]
    assert band["feasible_region_is_entirely_above_the_band"] is True and 1.5 < band["smallest_feasible_scale_over_the_band_top"] < 1.52
    reference = feasibility["relative_to_the_historical_reference"]
    assert 3.0 < reference["smallest_feasible_rate_over_it"] < 3.1
    primary = feasibility["by_shared_arrival_position"]["0.5"]
    inside = primary["inside_the_declared_scale_band"]["by_kernel"]
    assert inside[REGION]["status"] == "EMPTY" and inside[REGION]["smallest_share_reachable"] > 0.5 and inside[RUNTIME]["status"] == "NONEMPTY"
    fibre = primary["closed_region_fibre"]
    assert fibre["status"] == "NONEMPTY" and fibre["the_most_retaining_kernel_of_the_region_is_compatible"] is False
    assert 185 < fibre["retained_at_60_ml_feasible"][1] < 190 and 0.5 < fibre["share_of_the_closed_region_span_compatible"] < 0.56
    assert fibre["fibre"]["e_inside_the_closed_region"][0] <= fibre["largest_feasible_e"] <= fibre["fibre"]["e_inside_the_closed_region"][1], "every kernel walked is inside the closed region"
    sensitivity = feasibility["by_shared_arrival_position"]["0.4"]["C_slow_crystalloid_by_kernel"][REGION]
    assert sensitivity["status"] == "NONEMPTY" and 7.0 < sensitivity["bleed_rate_ml_min"][0] < 8.0, "the same answer at another shared arrival position"


def test_d3_the_verdict_is_for_the_declared_window_reading_and_the_stricter_reading_is_reported_not_hidden(built):
    reading = built["feasibility"]["window_reading"]
    assert "minute 30" in reading["declared"]
    stricter = reading["stricter_reading_as_a_sensitivity"]
    assert stricter["is_the_declared_reading"] is False
    assert [round(v) for v in stricter["B_one_unit_under_this_reading"]["common_scale_ml_eq"]] == [1478, 1574] and stricter["B_one_unit_under_this_reading"]["status"] == "NONEMPTY"
    assert stricter["status_with_the_closed_crystalloid_region"] == "EMPTY", "a floor already met at minute 15 leaves no point with a closed-region kernel"
    assert stricter["C_slow_crystalloid_by_kernel"][REGION]["share_at_the_least_protected_corner"] > 0.49
    assert stricter["status_with_the_runtime_kernel_for_information"] == "NONEMPTY"
    assert 15.0 < stricter["full_unit_sbp_rise_at_30_mmHg_it_implies"]["gi_bleed_57m"][0] and stricter["full_unit_sbp_rise_at_30_mmHg_it_implies"]["gi_bleed_72f"][1] == 18.0
    condition = built["decision"]["conditional_on_the_window_reading"]
    assert condition == {**condition, "declared_reading_status": "NONEMPTY", "stricter_reading_status": "EMPTY", "verdict_survives_the_stricter_reading": False, "needs_faculty_confirmation": True}


# -- P3-330 .. P3-332 ------------------------------------------------------------------------------------------------------------------------------------

def test_e1_the_three_witnesses_meet_the_three_anchors_and_every_existing_constraint_in_both_cases(built):
    witnesses = built["witnesses"]
    assert list(witnesses) == ["LOW", "CENTER", "HIGH"]
    rates = [item["bleed_rate_ml_min"] for item in witnesses.values()]
    scales = [item["scale_ml_eq"] for item in witnesses.values()]
    assert rates == sorted(rates) and scales == sorted(scales) and 7.5 < rates[0] and rates[-1] < 9.4
    for label, item in witnesses.items():
        assert item["all_three_anchors_and_every_existing_constraint"] and item["case_ordering_57m_below_72f"] and item["kernel"] == REGION, label
        for case, row in item["cases"].items():
            unit = row["one_unit_bleeding_controlled"]
            assert set(unit) == {"0", "5", "15", "30"} and {"sbp", "dbp", "map", "shadow_hr_non_authoritative", "effective_volume_change_ml_eq", "hb"} <= set(unit["30"])
            assert 8.0 <= row["one_unit_sbp_rise_at_30_mmHg"] <= 18.0 and row["one_unit_sbp_rise_at_30_mmHg"] < 13.0, (label, case, "inside the window, in its lower part")
            assert row["one_unit_not_instantaneous"] and row["one_unit_does_not_normalize_perfusion"] and row["one_unit_below_the_too_large_mark"], (label, case)
            assert 0.45 < row["one_unit_sbp_rise_at_15_mmHg"] / row["one_unit_sbp_rise_at_30_mmHg"] < 0.55
            slow = row["slow_crystalloid"]
            assert 0.15 <= slow["share_prevented"]["60"] <= 0.35 and slow["fades_after_the_infusion"] and slow["share_prevented"]["120"] < 0.12, (label, case)
            assert slow["bleeding_ml_min_distinct"] == [round(item["bleed_rate_ml_min"], 6)], "the bleeding is active at every minute: only the one-unit reading controls it"
            assert slow["treated_deterioration_at_60_mmHg"] < slow["untreated_deterioration_at_60_mmHg"] and slow["net_effective_volume_balance_at_60_ml"] < -250
            assert abs(slow["retained_crystalloid_at_60_ml"] - 134.6016) < 1e-3
            untreated = row["untreated"]
            assert untreated["progressive_deterioration"] and untreated["u_out_faculty_envelopes"] and untreated["core_boundary_minute"] is None, (label, case)
            assert all(abs(untreated["sbp"][m] - untreated["accepted_course_sbp"][m]) < 8.0 for m in ("60", "120", "180")), "the same severity class as the accepted course, not the same numbers"
            verdicts = row["existing_constraints_frozen_evaluator"]
            assert verdicts["readable"] and all(verdicts[name] for name in ("U-OUT", "U-HB", "FD-BLD-01", "FD-BLD-02", "SECOND-UNIT", "FD-BLD-04", "FD-BLD-05", "FD-BLD-06",
                                                                           "FD-BLD-07", "FD-BLD-08", "FD-BLD-09", "FD-BLD-03")), (label, case)


# -- P3-333 .. P3-335 ------------------------------------------------------------------------------------------------------------------------------------

def test_f1_the_region_is_a_corner_and_the_middles_of_the_two_windows_need_a_kernel_below_the_closed_region(built):
    structure = built["structure"]
    middles = structure["the_middles_of_the_two_windows"]
    assert middles["one_unit_rise_mmHg"] == 13.0 and middles["share_wanted"] == 0.25
    assert middles["closed_region_kernel_reaches_the_middle_share"] is False and min(middles["share_given_at_that_scale_c_low_to_c_high"][REGION]) > 0.35
    assert middles["runtime_kernel_reaches_the_middle_share"] is True
    assert [item["empty"] for item in structure["near_conflicts"]] == [True, True, True]
    assert structure["near_conflicts"][0]["measured_share"] > 0.5, "a unit worth +18 mmHg goes with a slow litre that prevents more than half"
    causes = structure["structural_causes"]
    assert causes["A_one_effective_volume_channel"]["present"] and causes["A_one_effective_volume_channel"]["does_it_empty_the_intersection"] is False
    assert causes["B_no_infusion_rate_dependence_of_retention"]["does_it_empty_the_intersection"] is False
    assert causes["C_pressure_map_cannot_hold_untreated_and_transfusion"]["present"] is False and causes["D_another_mechanism"]["present"] is False
    assert structure["runtime_kernel_for_information"]["status"] == "NONEMPTY" and "not counted as feasible" in structure["runtime_kernel_for_information"]["note"]


def test_g1_the_gate_verdict_is_A_amendment_3_is_not_opened_and_nothing_was_designed(built):
    decision = built["decision"]
    assert decision["intersection_status"] == "NONEMPTY" and decision["one_shared_family_region"] is True and decision["case_specific_parameters_introduced"] is False
    assert decision["witnesses_satisfy_everything"] is True and decision["status_at_the_sensitivity_position"] == "NONEMPTY"
    assert decision["identification"]["weakly_identified"] is False and all(1.1 < value < 1.5 for value in decision["identification"]["largest_over_smallest"].values())
    gate = decision["amendment_3_gate"]
    assert gate["verdict"] == "A" and gate["name"] == "CURRENT_PHYSIOLOGY_HAS_FEASIBLE_JOINT_REGION" and gate["amendment_3"] == "NOT_JUSTIFIED__NOT_OPENED" and gate["design_written"] is False
    assert len(gate["what_the_region_costs"]) == 4 and set(gate["why_not"]) == {"B", "C", "D", "E"}


def test_g2_the_gate_is_not_vacuous_an_empty_intersection_would_return_C_and_a_failing_witness_would_not_return_A(built):
    import copy
    empty = copy.deepcopy(built["feasibility"])
    empty["status"] = "EMPTY"
    gate = gj.decide(None, empty, built["witnesses"], built["structure"])["amendment_3_gate"]
    assert (gate["verdict"], gate["name"]) == ("C", "AMENDMENT_3_JUSTIFIED_BY_INCOMPATIBLE_BEHAVIORAL_CONSTRAINTS") and gate["amendment_3"] != "NOT_JUSTIFIED__NOT_OPENED"
    broken = copy.deepcopy(built["witnesses"])
    broken["HIGH"]["all_three_anchors_and_every_existing_constraint"] = False
    assert gj.decide(None, built["feasibility"], broken, built["structure"])["amendment_3_gate"]["verdict"] == "E"
    assert gj._interval_status(2.0, 1.0) == "EMPTY" and gj._interval_status(1.0, 1.005) == "NUMERICALLY_AMBIGUOUS" and gj._interval_status(1.0, 1.2) == "NONEMPTY"


# -- nothing moved --------------------------------------------------------------------------------------------------------------------------------------------

def test_h1_the_core_the_closed_region_the_human_review_and_every_earlier_record_are_untouched():
    import runtime_pressure_grant as grants
    import volume_behaviour_record as vbr
    from clinical_core import amendment_2, legacy_adapter
    assert amendment_2.amended_core_digest_now() == grants.CORE_DIGEST == "a0af7d08fec3aaf93606b5635cad9f26980428a5ab8d8f66afb1317bb4586ce2"
    assert vbr.EFFECTIVE_REGION == {"peak": (0.15, 0.27072), 30: (0.15, 0.25), 60: (0.10, 0.20), 120: (0.05, 0.15)} and vbr.STATUS == "FACULTY_DEFINED_BEHAVIORAL_REGION"
    assert legacy_adapter.LEGACY_LITERALS["gi_bleeding_circulation_per_min"][0] == 0.003 and legacy_adapter.LEGACY_LITERALS["untimed_blood_units_per_min"][0] == 1 / 30
    human = json.loads((REVISION / "PHASE3_FIRST_HUMAN_FACULTY_REVIEW.json").read_text(encoding="utf-8"))
    assert human["record_digest"] == _sealed(human) == HUMAN_DIGEST
    for name, expected in (("PHASE3_BLEED_RATE_SCALE_CHECKPOINT.json", P3_325_DIGEST), ("PHASE3_FIRST_FACULTY_REVIEW_CHECKPOINT.json", P3_313_DIGEST),
                           ("PHASE3_FACULTY_REVIEW_CHECKPOINT.json", P3_300_DIGEST)):
        assert json.loads((REVISION / name).read_text(encoding="utf-8"))["record_digest"] == expected, name
    stored = json.loads((REVISION / "PHASE3_FACULTY_TRAJECTORY_REVIEW_SET.json").read_text(encoding="utf-8"))
    assert stored["record_digest"] == ftr.PINNED_SET_DIGEST and [item["scenario_id"] for item in stored["items"]] == ["FR-A", "FR-B", "FR-C", "FR-D", "FR-E", "FR-F", "FR-G"]
    assert not list(REVISION.glob("*V2*")) and not list(REVISION.glob("*AMENDMENT_3*")) and not list((ROOT / "docs").glob("*AMENDMENT_3*")), "no V2 candidate, no Amendment 3 design"
    for path in sorted((ROOT / "clinical_core").rglob("*.py")):
        assert "norepinephrine" not in path.read_text(encoding="utf-8").lower(), f"{path.name}: norepinephrine was not implemented"


# -- P3-336 ----------------------------------------------------------------------------------------------------------------------------------------------

def test_k1_the_decisions_the_debt_and_the_checkpoint_say_the_same_thing(built):
    cola = (ROOT / "docs" / "COLA_DECISIONES_AI_ADVISOR.md").read_text(encoding="utf-8")
    for index in range(9, 14):
        assert f"| FD-RATE-{index:02d} |" in cola
    for index in range(230, 234):
        assert f"| FD-P3-{index} |" in cola
    assert "FACULTY_DEFINED_DEVELOPMENT_BEHAVIORAL_REGION" in cola and "UNRESOLVED_ABSOLUTE_SCALE" in cola
    debt = (ROOT / "docs" / "REGISTRO_DEUDA_TECNICA.md").read_text(encoding="utf-8")
    assert "## TD-149" in debt
    checkpoint = json.loads((REVISION / "PHASE3_JOINT_FEASIBILITY_CHECKPOINT.json").read_text(encoding="utf-8"))
    assert checkpoint["record_digest"] == _sealed(checkpoint)
    assert checkpoint["pinned_records"]["analysis_record_digest"] == gj.load_record()["record_digest"] == built["record_digest"]
    assert checkpoint["pinned_records"]["human_review_record_digest"] == HUMAN_DIGEST and checkpoint["pinned_records"]["p3_325_checkpoint_digest"] == P3_325_DIGEST
    assert set(checkpoint["statuses"]) == {"PRBC_RESPONSE_REGION", "SLOW_CRYSTALLOID_REGION", "UNTREATED_REGION", "JOINT_IDENTIFIABILITY", "INTERSECTION_STATUS", "STRUCTURAL_CONFLICT", "AMENDMENT3_STATUS"}
    assert checkpoint["overall"] == {"verdict": "A", "name": "CURRENT_PHYSIOLOGY_HAS_FEASIBLE_JOINT_REGION"} and all(checkpoint["confirmations"].values())
    assert checkpoint["verdict_condition"] == {**checkpoint["verdict_condition"], "stricter_reading_status_with_the_closed_crystalloid_region": "EMPTY",
                                               "verdict_survives_the_stricter_reading": False, "needs_faculty_confirmation": True}
    assert "TD-149" in debt and "lectura de la ventana" in debt and "Condición del veredicto" in doc_text(ROOT)
    doc = (ROOT / "docs" / "PHASE3_GI_JOINT_FEASIBILITY.md").read_text(encoding="utf-8")
    assert "A · CURRENT_PHYSIOLOGY_HAS_FEASIBLE_JOINT_REGION" in doc and "NONEMPTY" in doc and "No se abre la Enmienda 3" in doc
    assert "docs/PHASE3_GI_JOINT_FEASIBILITY.md" in (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
