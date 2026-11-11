"""P3-189 to P3-192: the GI development snapshot, its selection criteria, its sensitivity audit and its immutable record.

What is proved here, apart from what is only described in ``docs/PHASE3_GI_DEVELOPMENT_SNAPSHOT.md``:

* the snapshot is the rule's output (the unique maximiser of the minimum margin to the faculty regions), not a name and not a legacy fit;
* the record is immutable: its file hash and its two digests are pinned, so any edit fails;
* the region still exists: LOW and HIGH are the core's own witnesses, unchanged, and nothing registers the snapshot as an authority artifact;
* the sensitivity record re-derives from the physical courses it embeds, and the independent evaluator equals the live channels bit for bit;
* two live encounters reproduce the recorded physical courses exactly with the snapshot as the middle witness.
No ``clinical_core/`` byte, no layer byte and no authority state is touched.
"""
import hashlib
import inspect
import json
import os
import random
import re
from pathlib import Path

import pytest

import runtime_authority as authority
import runtime_shadow as rs
import runtime_shadow_families as fam
import test_gi_snapshot_analysis as an
from clinical_core import amendment_2 as a2
from clinical_core import systemic_consciousness as sc

ROOT = Path(__file__).resolve().parent
SNAPSHOT = json.loads((ROOT / an.SNAPSHOT_FILE).read_text(encoding="utf-8"))
SENSITIVITY = json.loads((ROOT / an.SENSITIVITY_FILE).read_text(encoding="utf-8"))
#: Pinned on 2026-11-11 when version 1 was written. A change to the file, to any value in it, or to its digests fails these.
V1_FILE_SHA256 = "d9de4800075e2e5bb7e6e445ec0dc9a5d672f53c54212a56cc2f41b9392d4803"
V1_IDENTITY_DIGEST = "1f292d014255ac968ddc3217400635ca64d22462852056c23bb91850d0d6ec40"
V1_RECORD_DIGEST = "9e258ab5b3790a5abb30053b30dd40fd0755918673bc4024f9da609fd4f8cdc9"
MIDPOINT = {"delivery_normal": 0.75, "delivery_severe": 0.5, "burden_rise_tau": 1.964, "burden_clear_tau": 8.51, "perfusion_normal": 0.55,
            "perfusion_severe": 0.35, "collapse_rise_tau": 1.85, "collapse_clear_tau": 7.0, "impending_burden": 0.37, "established_burden": 0.625}


def _normal(value):
    return json.loads(json.dumps(value))


# -- P3-192: the immutable record ---------------------------------------------------------------------------------------------------------------

def test_version_1_is_pinned_by_its_file_hash_and_its_two_digests():
    raw = (ROOT / an.SNAPSHOT_FILE).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == V1_FILE_SHA256
    assert SNAPSHOT["immutability"]["identity_digest"] == V1_IDENTITY_DIGEST
    assert SNAPSHOT["immutability"]["record_digest"] == V1_RECORD_DIGEST
    identity = {"snapshot_id": SNAPSHOT["snapshot_id"], "version": SNAPSHOT["version"], "values": SNAPSHOT["values"],
                "common_core_lineage": {"version_id": SNAPSHOT["common_core_lineage"]["version_id"], "digest": SNAPSHOT["common_core_lineage"]["digest"]},
                "region_bounds": SNAPSHOT["region_bounds"]}
    assert an.digest(identity) == V1_IDENTITY_DIGEST
    assert an.digest({key: value for key, value in SNAPSHOT.items() if key != "immutability"}) == V1_RECORD_DIGEST


def test_the_record_names_what_a_later_change_must_do_and_carries_every_field_the_assignment_asks_for():
    for key in ("snapshot_id", "common_core_lineage", "amendment", "values", "faculty_references", "region_bounds", "selection", "uncertainty",
                "falsifiers", "selected_on", "version", "supporting_tests", "immutability", "witnesses_preserved_for_ongoing_sensitivity_checks"):
        assert SNAPSHOT.get(key) not in (None, "", [], {}), key
    assert (SNAPSHOT["snapshot_id"], SNAPSHOT["version"], SNAPSHOT["selected_on"]) == ("GI_DEVELOPMENT_SNAPSHOT_V1", 1, "2026-11-11")
    rule = SNAPSHOT["immutability"]
    assert rule["supersedes"] is None and rule["superseded_by"] is None
    assert "NEW file" in rule["rule"] and "GI_DEVELOPMENT_SNAPSHOT_V2" in rule["rule"]
    assert len(SNAPSHOT["falsifiers"]) >= 5
    # every supporting test the record names exists in the repository
    for name in SNAPSHOT["supporting_tests"]:
        assert (ROOT / name.split(" ")[0]).exists(), name


def test_the_record_is_not_an_authority_artifact_and_nothing_reads_it_at_runtime():
    assert SNAPSHOT["status"] == "GI_DEVELOPMENT_SNAPSHOT"
    assert set(SNAPSHOT["is_not"]) == {"clinical calibration", "production profile", "authority-approved profile"}
    assert SNAPSHOT["authority"] == {"registered_as_an_authority_artifact": False, "common_core_runtime_authority": False,
                                     "stored_in": "docs/revision (documentation); no authority store, no registry, no import by the layer or the app"}
    assert rs.COMMON_CORE_RUNTIME_AUTHORITY is False
    assert sorted(authority.APPROVED_SNAPSHOTS) == ["gi_pressure_committed"]
    needles = ("GI_DEVELOPMENT_SNAPSHOT", "GI_DEVELOPMENT_SNAPSHOT_V1")
    for path in ROOT.glob("*.py"):
        if path.name.startswith(("test_", "regression_")):
            continue
        assert not any(needle in path.read_text(encoding="utf-8") for needle in needles), path.name
    # and no record of any authority store mentions it
    for path in (ROOT / "docs" / "revision").glob("PHASE3_*AUTHORITY*.json"):
        # the three REVIEW records that name the snapshot on purpose (readiness, counterfactual, pre-authority review): none is an authority artifact
        if path.name not in ("PHASE3_GI_AUTHORITY_READINESS.json", "PHASE3_GI_AUTHORITY_COUNTERFACTUAL.json", "PHASE3_GI_PREAUTHORITY_REVIEW.json"):
            assert "GI_DEVELOPMENT_SNAPSHOT" not in path.read_text(encoding="utf-8"), path.name


def test_the_record_binds_the_active_common_core_lineage_and_nothing_in_the_core_moved():
    lineage = rs.CORE_LINEAGE[-1]
    assert SNAPSHOT["common_core_lineage"]["version_id"] == lineage.version_id == "PHASE2_AMENDMENT_2"
    assert SNAPSHOT["common_core_lineage"]["digest"] == lineage.digest == "a0af7d08fec3aaf93606b5635cad9f26980428a5ab8d8f66afb1317bb4586ce2"
    assert a2.amended_core_digest_now() == lineage.digest


# -- P3-189 and P3-191: the criteria and the selection ----------------------------------------------------------------------------------------------

def test_the_snapshot_is_the_rules_output_and_equals_the_region_midpoint_of_every_magnitude():
    assert SNAPSHOT["values"] == an.region_midpoint() == MIDPOINT
    for name in sc.FIELDS:
        low, high = sc.REGIONS[name][:2]
        assert SNAPSHOT["values"][name] == pytest.approx((low + high) / 2.0, abs=5e-7), name
    assert set(SNAPSHOT["values"]) == set(sc.FIELDS)
    assert SNAPSHOT["min_margin"] == 0.5
    assert an.near_boundary(SNAPSHOT["values"]) == [] and an.min_margin(SNAPSHOT["values"]) == pytest.approx(0.5)
    # a valid profile of the core
    sc.Amendment2Profile(**SNAPSHOT["values"])


def test_centre_reference_is_not_the_midpoint_and_fails_the_first_hard_criterion():
    centre = an.candidate_row("CENTER_REFERENCE", an.witness_values("CENTER_REFERENCE"))
    assert not an.feasible(centre)
    assert sorted(centre["on_a_bound"]) == ["collapse_clear_tau", "impending_burden"]
    assert centre["min_margin"] == 0.0
    assert "impending_burden" in centre["outside_bracket"]
    assert SNAPSHOT["reference_witness_not_selected"]["magnitudes_on_a_region_bound"] == centre["on_a_bound"]


def test_the_midpoint_is_the_unique_maximiser_of_the_minimum_margin_not_a_name():
    rng = random.Random(7)
    best = an.min_margin(an.region_midpoint())
    for _ in range(4000):
        point = {name: sc.REGIONS[name][0] + rng.random() * (sc.REGIONS[name][1] - sc.REGIONS[name][0]) for name in sc.FIELDS}
        assert an.min_margin(point) <= best + 1e-12
    # moving ANY one magnitude off its midpoint lowers the minimum margin
    for name in sc.FIELDS:
        moved = dict(an.region_midpoint())
        moved[name] += 0.01 * (sc.REGIONS[name][1] - sc.REGIONS[name][0])
        assert an.min_margin(moved) < best


def test_the_selection_reads_region_geometry_and_the_witness_bracket_only_never_a_legacy_value():
    source = inspect.getsource(an.select) + inspect.getsource(an.feasible) + inspect.getsource(an.margins) + inspect.getsource(an.region_midpoint)
    assert "legacy" not in source.lower()
    assert list(inspect.signature(an.select).parameters) == ["candidates"]
    chosen = SNAPSHOT["selection"]
    assert chosen["legacy_input"] is False and chosen["inputs_of_the_rule"] == ["the region bounds", "the LOW and HIGH witnesses' values"]
    assert chosen["winner"] == "REGION_MIDPOINT"
    assert re.search(r"UNIQUE", chosen["rule"])


def test_a_legacy_fit_would_have_chosen_something_else_and_the_selected_point_is_not_the_legacy_closest():
    legacy = SNAPSHOT["selection"]["legacy_distance_reported_only"]
    assert legacy["closest_candidate"] != SNAPSHOT["selection"]["winner"]
    assert legacy["selected_rank_by_legacy_distance"] > 1 and legacy["of"] == len(SENSITIVITY["candidates"])
    # the legacy-closest candidate hugs a region bound: the opposite of what the criteria choose
    assert legacy["closest_candidate_min_margin"] < an.NEAR_BOUNDARY
    assert legacy["distance_of_closest"] < legacy["distance_of_selected"]


def test_every_candidate_table_row_is_reproduced_and_only_the_midpoint_is_feasible_and_best():
    rows = {row["label"]: row for row in SENSITIVITY["candidates"]}
    assert len(rows) == 4 + an.LHS_POINTS
    assert an.select(SENSITIVITY["candidates"])["label"] == "REGION_MIDPOINT"
    feasible = [label for label, row in rows.items() if an.feasible(row)]
    assert "REGION_MIDPOINT" in feasible and "CENTER_REFERENCE" not in feasible and "LOW" not in feasible and "HIGH" not in feasible
    assert max(rows[label]["min_margin"] for label in feasible if label != "REGION_MIDPOINT") < 0.5
    for label, row in rows.items():
        assert row == _normal(an.candidate_row(label, row["values"])), label


# -- the region still exists (P3-191B) -------------------------------------------------------------------------------------------------------------

def test_low_and_high_stay_the_cores_own_witnesses_and_the_region_is_not_replaced_by_the_point():
    kept = SNAPSHOT["witnesses_preserved_for_ongoing_sensitivity_checks"]
    assert kept["LOW"] == sc.WITNESSES["LOW"].to_dict() and kept["HIGH"] == sc.WITNESSES["HIGH"].to_dict()
    assert kept["SELECTED_SNAPSHOT"] == "GI_DEVELOPMENT_SNAPSHOT_V1"
    assert fam.GI_AMENDMENT_2_WITNESS_NAMES == ("LOW", "CENTER_REFERENCE", "HIGH")
    assert sc.WITNESSES["CENTER_REFERENCE"].to_dict() == SNAPSHOT["reference_witness_not_selected"]["CENTER_REFERENCE"]
    # the two witnesses do NOT bound every event: the record says so, with the minutes
    gap = kept["event_times_not_bounded_by_the_witnesses_minutes"]
    assert gap["established"] == 12 and gap["impending"] == 3 and gap["first_unresponsive"] == 0
    assert "burden_rise_tau" in kept["magnitudes_outside_the_low_high_bracket"]
    assert SENSITIVITY["regions"] == {name: list(sc.REGIONS[name][:2]) for name in sc.FIELDS}


def test_the_middle_witness_block_restores_the_core_dictionary_even_after_an_error():
    before = sc.WITNESSES["CENTER_REFERENCE"]
    with an.snapshot_as_middle_witness(MIDPOINT):
        assert sc.WITNESSES["CENTER_REFERENCE"].to_dict() == MIDPOINT
    assert sc.WITNESSES["CENTER_REFERENCE"] is before
    with pytest.raises(RuntimeError):
        with an.snapshot_as_middle_witness(MIDPOINT):
            raise RuntimeError("boom")
    assert sc.WITNESSES["CENTER_REFERENCE"] is before


# -- P3-190: the sensitivity audit ---------------------------------------------------------------------------------------------------------------------

COURSE = an.course_of_record(SENSITIVITY["physical"])


def test_the_sensitivity_record_re_derives_from_the_physical_courses_it_embeds():
    again = _normal(an.build_sensitivity(COURSE, SENSITIVITY["legacy_first_levels"]))
    for key in ("oat", "ranking", "effects", "additive_residual", "corner_coverage", "invariants", "candidates", "selected", "legacy_distance_reported_only", "base"):
        assert again[key] == SENSITIVITY[key], key


def test_the_independent_evaluator_equals_every_live_channel_of_every_witness_bit_for_bit():
    proof = SENSITIVITY["exactness"]
    assert proof["rows_compared"] == 12012 and proof["max_abs_difference"] == 0.0 and proof["category_or_collapse_mismatches"] == 0


def test_the_thresholds_were_declared_before_the_sweep_and_the_ranking_follows_them():
    assert (an.HIGH_SWING_MIN, an.MODERATE_SWING_MIN) == (10.0, 3.0)
    by_class = {}
    for item in SENSITIVITY["ranking"]:
        by_class.setdefault(item["class"], set()).add(item["parameter"])
        assert an.classify(item["max_classified_swing"]) == item["class"]
    assert by_class[an.HIGH] == {"delivery_normal", "delivery_severe", "perfusion_normal", "perfusion_severe", "established_burden"}
    assert by_class[an.MODERATE] == {"burden_clear_tau", "impending_burden"}
    assert by_class[an.LOW_SENS] == {"burden_rise_tau", "collapse_rise_tau", "collapse_clear_tau"}
    assert an.IRRELEVANT not in by_class
    assert sum(len(items) for items in by_class.values()) == len(sc.FIELDS)
    # the collapse clearance only shows where a scenario exercises it: the late rescue
    assert SENSITIVITY["oat"]["collapse_clear_tau"]["dominant_metric"].endswith("rescue_collapse_none")
    assert SENSITIVITY["oat"]["collapse_clear_tau"]["max_classified_swing"] == 2.0


def test_two_magnitudes_dominate_consciousness_two_dominate_collapse_and_the_rest_do_not():
    effect = SENSITIVITY["effects"]
    onset = effect["gi_bleed_57m/first_unresponsive"]["standardized_effect"]
    assert abs(onset["delivery_severe"]) > 0.9 and abs(onset["delivery_normal"]) > 0.2
    assert abs(effect["gi_bleed_57m/first_somnolent"]["standardized_effect"]["delivery_normal"]) > 0.9
    collapse = effect["gi_bleed_57m/impending"]["standardized_effect"]
    assert abs(collapse["perfusion_normal"]) > 0.9
    assert abs(effect["gi_bleed_57m/established"]["standardized_effect"]["perfusion_severe"]) > 0.8
    for metric in ("first_somnolent", "first_obtunded", "first_unresponsive"):
        assert effect[f"gi_bleed_57m/{metric}"]["r_squared_linear"] > 0.99
        # no perfusion or collapse magnitude moves a consciousness onset
        for name in ("perfusion_normal", "perfusion_severe", "collapse_rise_tau", "collapse_clear_tau", "impending_burden", "established_burden"):
            assert abs(effect[f"gi_bleed_57m/{metric}"]["standardized_effect"][name]) < 0.05, (metric, name)


def test_the_region_is_well_behaved_monotone_additive_and_free_of_ordering_or_safety_violations():
    assert SENSITIVITY["invariants"]["profiles"] == 118
    assert set(SENSITIVITY["invariants"]["violations"].values()) == {0}
    assert all(item["monotone_in_every_defined_metric"] for item in SENSITIVITY["oat"].values())
    assert not [name for name, item in SENSITIVITY["oat"].items() if item["undefined_metrics"]]
    for key, item in SENSITIVITY["additive_residual"].items():
        assert item["max_abs_minutes"] < 4.0, key
        assert item["mean_abs_minutes"] < 1.5, key
    for item in SENSITIVITY["corner_coverage"].values():
        assert item["corners_min"] <= min(item["witnesses_low_high"]) + 3 and item["corners_max"] >= max(item["witnesses_low_high"]) - 1


def test_the_two_cases_read_the_same_for_each_witness_and_for_the_snapshot_within_one_minute():
    for values in (an.witness_values("LOW"), an.witness_values("CENTER_REFERENCE"), an.witness_values("HIGH"), SNAPSHOT["values"]):
        found = an.profile_metrics(values, COURSE)
        for key, value in found.items():
            if key.startswith("gi_bleed_57m/") and isinstance(value, (int, float)):
                other = found[key.replace("57m", "72f")]
                assert abs(value - other) <= 1, key


# -- the snapshot's behaviour: the faculty invariants (H2, H3, H4) -----------------------------------------------------------------------------------------

def test_the_snapshot_keeps_the_fd_p3_176_recovery_invariant_in_both_cases():
    for case, item in SNAPSHOT["behaviour"]["recovery_invariant"].items():
        assert 6 <= item["minutes_0_80_to_below_0_50"] <= 8, case
        assert 0 <= item["minutes_remaining_after_entry"] <= 2, case
        assert item["share_of_descent_done_before_entry"] >= 0.79, case
        assert 3.0 <= item["isolated_decay_0_80_to_0_50_min"] <= 5.0, case


def test_the_snapshot_keeps_the_onset_order_the_recovery_order_and_the_collapse_after_unresponsive_in_both_cases():
    for case in an.CASES:
        events = SNAPSHOT["behaviour"]["untreated_events"][case]
        assert events["first_somnolent"] < events["first_obtunded"] < events["first_unresponsive"] < events["impending"] < events["established"]
        sequences = SNAPSHOT["behaviour"]["category_sequences"][case]
        for scenario in ("early_treatment", "blood_focused", "fluid_focused"):
            assert sequences[scenario] == [[1, 0]]
        steps = [category for _, category in sequences["recovery_after_severe"]]
        assert steps[-1] == 0 and max(steps) == 3
        # recovery gives one band back at a time, never two
        assert all(a - b == 1 for a, b in zip(steps[steps.index(3):], steps[steps.index(3) + 1:]))
    # the two cases read the same: H4
    assert SNAPSHOT["behaviour"]["untreated_events"]["gi_bleed_57m"] == SNAPSHOT["behaviour"]["untreated_events"]["gi_bleed_72f"]
    assert SNAPSHOT["selection"]["hard_criteria_evidence"]["H4_case_difference_minutes"] <= 1
    assert set(SNAPSHOT["selection"]["hard_criteria_evidence"]["H2_H3_invariant_violations_over_profiles"]["violations"].values()) == {0}


def test_the_witnesses_around_the_snapshot_keep_their_untreated_events_in_order():
    low, high = (SNAPSHOT["witness_untreated_events_for_comparison"][name] for name in ("LOW", "HIGH"))
    events = SNAPSHOT["behaviour"]["untreated_events"]["gi_bleed_57m"]
    for key in ("first_somnolent", "first_obtunded", "first_unresponsive", "impending", "established"):
        assert high[key] <= events[key] <= low[key], key


def test_the_uncertainty_block_states_the_status_of_every_magnitude_and_the_range_over_the_region():
    block = SNAPSHOT["uncertainty"]
    assert "FACULTY_DEFINED_DEVELOPMENT_BEHAVIORAL_REGION" in block["all_ten_magnitudes"] and "none is validated clinically" in block["all_ten_magnitudes"]
    assert set(block["weakly_identified"]) == {"collapse_rise_tau", "collapse_clear_tau", "impending_burden", "established_burden"}
    assert block["event_time_range_over_the_region_minutes"]["first_unresponsive"] == [140, 175]
    assert block["event_time_range_over_the_region_minutes"]["established"] == [189, 225]
    assert SNAPSHOT["value_status"] == sc.STATUS


# -- live: two encounters reproduce the recorded physical courses with the snapshot as the middle witness -----------------------------------------------------

@pytest.mark.parametrize("scenario", ["early_treatment", "recovery_after_severe"])
def test_a_live_encounter_reproduces_the_recorded_physical_course_exactly_and_the_evaluator_equals_the_live_channels(scenario):
    captured = an.capture("gi_bleed_57m", scenario, SNAPSHOT["values"])
    recorded = SENSITIVITY["physical"]["gi_bleed_57m"][scenario]
    physical = an.physical_from_capture(captured)
    for key in ("minute", "relative_delivery", "relative_perfusion", "pulse"):
        assert physical[key] == recorded[key], key
    assert an.order_minute_of(captured) == recorded["order_minute"]
    values = {"LOW": an.witness_values("LOW"), "CENTER_REFERENCE": SNAPSHOT["values"], "HIGH": an.witness_values("HIGH")}
    proof = an.exactness({("gi_bleed_57m", scenario): captured}, values)
    assert proof["max_abs_difference"] == 0.0 and proof["category_or_collapse_mismatches"] == 0 and proof["rows_compared"] > 300
    assert not captured["failures"]
    assert sc.WITNESSES["CENTER_REFERENCE"].to_dict() == an.witness_values("CENTER_REFERENCE")
