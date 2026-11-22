"""P3-367 to P3-374: the human re-review record, the ratified joint region, the CENTER_REFERENCE development snapshot, the monitored limitation and the closure of GI pressure calibration (for development).

Records only. Nothing here changes an executable, a parameter, a candidate trajectory or an authority: the tests read the sealed records and the certified ones they point to, and they say so when something moves.
The answers of the human re-review are typed a second time below, on purpose, so that a slip in either copy is caught.
"""
import hashlib
import json
import re
from pathlib import Path

import faculty_trajectory_review as ftr
import faculty_trajectory_rereview as rr

ROOT = Path(__file__).resolve().parent
REV = ROOT / "docs" / "revision"
ORDER = ["FR-B", "FR-C", "FR-E", "FR-G"]
FIRST_REVIEW_RECORD_DIGEST = "9ba80fa70d3b38e178caa3aca9432f9227ce6d9591a48c9908c3f5ac4cc6c8d3"
CENTER_BINDING = {"arrival_position": 0.5, "bleed_rate_ml_eq_per_min": 8.970853509, "c_rate_over_scale_per_min": 0.003326066,
                  "crystalloid_kernel": {"e": 0.213115961, "s": 0.835, "tau_min": 60.624}, "preload_scale_ml_eq": 2697.136369656}
# the faculty report of the assignment, typed again: (overall, Q1, Q2, Q3, Q4, Q5)
REPORTED = {"FR-B": ("ACCEPT_WITH_LIMITATION", "Expected", "Plausible", "Too small", "Coherent", "Maybe"),
            "FR-C": ("ACCEPT_WITH_LIMITATION", "Expected", "Plausible", "Too small", "Coherent", "Maybe"),
            "FR-E": ("ACCEPT_WITH_LIMITATION", "Expected", "Plausible", "Too small", "Coherent", "Maybe"),
            "FR-G": ("ACCEPT", "Expected", "Plausible", "Plausible", "Coherent", "No")}


def _load(name: str) -> dict:
    return json.loads((REV / name).read_text(encoding="utf-8"))


def _sha(name: str) -> str:
    return hashlib.sha256((REV / name).read_bytes()).hexdigest()


def _sealed(record: dict) -> bool:
    return record["record_digest"] == ftr._digest({key: value for key, value in record.items() if key != "record_digest"})


HUMAN = _load("PHASE3_HUMAN_FACULTY_REREVIEW.json")
LIMITATION = _load("GI_BLOOD_RESUSCITATION_LOW_END_RESPONSE.json")
SNAPSHOT = _load("GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1.json")
RATIFICATION = _load("GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1_RATIFICATION.json")
REGION = _load("PHASE3_GI_JOINT_REGION_V1.json")
LOADED = rr.load_set()


# ---------------------------------------------------------------------------------------------------------------------------------------- P3-367 · the human record
def test_t1_the_human_record_is_sealed_valid_distinct_and_pinned_to_what_was_reviewed():
    assert _sealed(HUMAN) and HUMAN["record_type"] == "HUMAN_FACULTY_REREVIEW_RECORD" and HUMAN["evidence_class"] == "HUMAN_FACULTY_REREVIEW"
    assert set(HUMAN["evidence_classes"]) == {"HUMAN_FACULTY_REREVIEW", "LEGACY_COMPARATOR", "MODEL_ANALYSIS", "TEST_RESULT"}, "the human evidence stays apart from the model analysis, the test results and the legacy comparator"
    review = HUMAN["review"]
    assert review["review_set_id"] == rr.SET_ID == "GI_JOINT_REGION_V1_FACULTY_REREVIEW" and review["candidate_reviewed"] == "CENTER_REFERENCE" and review["candidate_named_by_the_interface"] is False
    assert review["review_set_digest"] == rr.PINNED_SET_DIGEST == LOADED["digest"], "the human judged exactly the pinned set"
    assert review["scenario_order_as_reported"] == ORDER == [entry["scenario_id"] for entry in rr.sequence(LOADED["items"])]
    assert review["item_digests_full"] == {sid: ftr.item_digest(LOADED["items"][sid]) for sid in ORDER}
    assert [row["reviewed_item_digest"] for row in HUMAN["scenarios"]] == [review["item_digests_full"][sid][:12] for sid in ORDER]
    questions = {question["id"]: question["choices"] for question in ftr.required_questions(LOADED["items"]["FR-B"])[0]}
    for row in HUMAN["scenarios"]:
        assert row["overall"] in ftr.OVERALL
        for key in ("Q1", "Q2", "Q3", "Q4", "Q5"):
            assert row["first_pass"][key] in questions[key], (row["scenario_id"], key)
        assert row["free_text_comments"] == "NONE_REPORTED" and row["recalibration_in_isolation_requested"] is False and row["faculty_interpretation_as_reported"]
    counts = {key: sum(1 for row in HUMAN["scenarios"] if row["overall"] == key) for key in ftr.OVERALL}
    assert HUMAN["overall_counts"] == counts == {"ACCEPT": 1, "ACCEPT_WITH_LIMITATION": 3, "RECALIBRATE": 0, "REJECT": 0}


def test_t2_the_answers_are_exactly_the_reported_ones_and_the_provenance_does_not_pretend_a_verification():
    got = {row["scenario_id"]: (row["overall"], *(row["first_pass"][key] for key in ("Q1", "Q2", "Q3", "Q4", "Q5"))) for row in HUMAN["scenarios"]}
    assert got == REPORTED
    provenance = HUMAN["provenance"]
    assert provenance["verification"] == "REPORTED_NOT_VERIFIED_AGAINST_PERSISTED_STORE" and provenance["persisted_store_available_to_the_assistant"] is False
    assert provenance["reviewer_identity_recorded"] is False and provenance["reviewer_name"] is None and provenance["reviewer_role"] == "faculty"
    for item in ("the answers Q1 to Q5 and the overall judgments against the persisted logs", "the scenario order as persisted", "the completion state as persisted"):
        assert item in HUMAN["not_verified"]
    assert "any model-written judgment" in HUMAN["not_in_this_record"] and "any legacy comparison" in HUMAN["not_in_this_record"]
    text = json.dumps(HUMAN, ensure_ascii=False)
    assert not re.search(r"\b(Dr|Dra)\.", text), "no physician name in the repository"


def test_t3_the_first_faculty_review_is_preserved_unchanged():
    first = _load("PHASE3_FIRST_HUMAN_FACULTY_REVIEW.json")
    assert first["record_digest"] == FIRST_REVIEW_RECORD_DIGEST and _sealed(first)
    assert first["overall_counts"] == {"ACCEPT": 1, "ACCEPT_WITH_LIMITATION": 5, "RECALIBRATE": 1, "REJECT": 0}
    kept = HUMAN["preserved_original_evidence"]
    assert kept["first_review_record_digest"] == FIRST_REVIEW_RECORD_DIGEST and kept["first_review_record_file_sha256"] == _sha("PHASE3_FIRST_HUMAN_FACULTY_REVIEW.json"), "the first review file is byte-identical to the one preserved here"
    assert kept["first_review_set_digest"] == ftr.PINNED_SET_DIGEST and kept["transfer_of_first_review_judgments"] is False
    assert HUMAN["review"]["review_set_digest"] != ftr.PINNED_SET_DIGEST, "the re-review is another versioned set, not an overwrite of the first one"


# ---------------------------------------------------------------------------------------------------------------------------------------- P3-369 · the snapshot
def test_t4_the_snapshot_is_the_certified_center_reference_binding_copied_not_recomputed():
    assert _sealed(SNAPSHOT) and SNAPSHOT["snapshot_id"] == "GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1" and SNAPSHOT["selected_witness"] == "CENTER_REFERENCE"
    assert SNAPSHOT["binding"] == CENTER_BINDING == REGION["witnesses"]["CENTER_REFERENCE"]["binding"], "the exact already-certified binding, field by field"
    source = SNAPSHOT["binding_source"]
    assert source["region_record_digest"] == REGION["record_digest"] and source["region_record_file_sha256"] == _sha("PHASE3_GI_JOINT_REGION_V1.json")
    assert source["copied_not_recomputed"] is True and source["optimized"] is False and source["another_point_considered"] is False
    binding = SNAPSHOT["binding"]
    assert abs(binding["bleed_rate_ml_eq_per_min"] - binding["c_rate_over_scale_per_min"] * binding["preload_scale_ml_eq"]) <= 1e-5 * binding["bleed_rate_ml_eq_per_min"], "rate, scale and c stay bound together"
    assert SNAPSHOT["margins_from_the_region_record"] == REGION["witnesses"]["CENTER_REFERENCE"]["margins"]
    assert SNAPSHOT["smallest_margin"] == REGION["decision"]["smallest_margin_of_each_witness"]["CENTER_REFERENCE"]
    assert SNAPSHOT["status"] == "RATIFIED_FOR_DEVELOPMENT_EXPERIMENTS"
    for text in ("a clinical calibration", "production authority", "resident validation"):
        assert text in SNAPSHOT["is_not"]
    assert SNAPSHOT["human_record"]["record_digest"] == HUMAN["record_digest"]


def test_t5_what_the_faculty_reviewed_is_exactly_what_the_region_assigns_to_center_reference():
    assert LOADED["audit"]["candidate"] == "JOINT_REGION_V1_CANDIDATE"
    for sid in ORDER:
        reviewed = [(point["minute"], int(point["sbp"]), int(point["dbp"]), int(point["map"])) for point in LOADED["items"][sid]["common"] if point["minute"] > 0]
        assigned = [(point["minute"], int(point["sbp"]), int(point["dbp"]), int(point["map"])) for point in REGION["candidate_trajectories"][sid]["candidates"]["CENTER_REFERENCE"]["pressures"]]
        assert reviewed == assigned and reviewed, sid
        assert REGION["candidate_trajectories"][sid]["reproduction_at_the_current_configuration"]["pressures_equal_the_reviewed_trajectory"] is True


def test_t6_low_and_high_remain_test_witnesses_only():
    for name in ("LOW", "HIGH"):
        entry = SNAPSHOT["witnesses_test_only"][name]
        assert entry["role"] == "TEST_WITNESS_ONLY" and entry["promoted"] is False
        assert entry["binding"] == REGION["witnesses"][name]["binding"] != SNAPSHOT["binding"]
        assert REGION["witnesses"][name]["role"] == "DEVELOPMENT_TEST_WITNESS" and REGION["witnesses"][name]["is_a_calibrated_point"] is False
    assert SNAPSHOT["witnesses_test_only"]["decision"] == "FD-RATIFY-04"
    for sid in ORDER:  # the human saw CENTER_REFERENCE only: no LOW/HIGH trajectory is in the reviewed set
        assert set(LOADED["items"][sid]) and "LOW" not in json.dumps(LOADED["items"][sid]) and "HIGH" not in json.dumps(LOADED["items"][sid])


# ---------------------------------------------------------------------------------------------------------------------------------------- P3-368 · the region
def test_t7_the_region_is_ratified_with_its_correlated_structure_and_its_record_is_untouched():
    assert _sealed(RATIFICATION) and RATIFICATION["status"] == "RATIFIED_FOR_DEVELOPMENT_EXPERIMENTS" and RATIFICATION["ratified_for"] == "DEVELOPMENT EXPERIMENTS"
    region = RATIFICATION["region"]
    assert region["id"] == REGION["region"]["id"] == "GI_JOINT_RATE_PRESSURE_DEVELOPMENT_REGION_V1"
    assert region["record_digest"] == REGION["record_digest"] and region["record_file_sha256"] == _sha("PHASE3_GI_JOINT_REGION_V1.json"), "the certified region record was not edited"
    assert region["status_before"] == REGION["region"]["status"] and region["status_now"] == "RATIFIED_FOR_DEVELOPMENT_EXPERIMENTS"
    rows = REGION["region"]["compatible_retention_on_a_lattice"]
    assert rows and region["structure_preserved"]["lattice_rows_checked"] == len(rows)
    assert all(abs(row["bleed_rate_ml_eq_per_min"] - row["c"] * row["scale_ml_eq"]) <= 1e-5 * row["bleed_rate_ml_eq_per_min"] for row in rows), "every lattice point has rate = c x scale: the coordinates are correlated"
    assert "never a coordinate" in REGION["region"]["coordinates"]["bleed_rate"] and "OUTSIDE the region" in REGION["region"]["projections_are_not_ranges"]["warning"]
    assert region["structure_preserved"]["every_row_has_rate_equal_to_c_times_scale"] is True and region["structure_preserved"]["region_record_edited"] is False
    assert region["structure_preserved"]["coordinates"] == REGION["region"]["coordinates"] and region["structure_preserved"]["projections_are_not_ranges"] == REGION["region"]["projections_are_not_ranges"]
    assert RATIFICATION["snapshot"]["file_sha256"] == _sha("GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1.json") and RATIFICATION["snapshot"]["record_digest"] == SNAPSHOT["record_digest"]
    assert RATIFICATION["human_record"]["record_digest"] == HUMAN["record_digest"] and RATIFICATION["human_record"]["overall_counts"] == HUMAN["overall_counts"]
    assert RATIFICATION["limitation"]["record_digest"] == LIMITATION["record_digest"]
    assert set(RATIFICATION["faculty_decisions"]) == {f"FD-RATIFY-0{index}" for index in range(1, 8)}
    for text in ("a clinical calibration", "authority-approved production physiology", "resident validation", "a clinical-validation claim"):
        assert text in RATIFICATION["is_not"]


# ---------------------------------------------------------------------------------------------------------------------------------------- P3-370 / P3-371 · the limitation and the status
def test_t8_the_limitation_is_durable_monitored_and_has_its_reopening_rule():
    assert _sealed(LIMITATION) and LIMITATION["limitation_id"] == "GI_BLOOD_RESUSCITATION_LOW_END_RESPONSE"
    assert LIMITATION["status"] == ["ACCEPTED_WITH_LIMITATION", "MONITOR", "NO_CURRENT_RECALIBRATION"]
    assert LIMITATION["reopen_only_if"] == ["another family shows the same deficit", "intervention ordering becomes wrong", "educational risk becomes material", "a new faculty review changes the judgment"]
    assert LIMITATION["evidence"]["scenarios"] == [row["scenario_id"] for row in HUMAN["scenarios"] if row["first_pass"]["Q3"] == "Too small"] == ["FR-B", "FR-C", "FR-E"]
    assert LIMITATION["evidence"]["human_record_digest"] == HUMAN["record_digest"]
    assert "raising these trajectories by a few mmHg" in LIMITATION["not_a_reason_to_recalibrate"]
    assert SNAPSHOT["limitation"]["id"] == LIMITATION["limitation_id"] and SNAPSHOT["limitation"]["status"] == LIMITATION["status"]
    assert RATIFICATION["development_status"]["gi_pressure"] == "GI_PRESSURE_DEVELOPMENT_CALIBRATION_CLOSED"
    for text in ("NOT production", "NOT clinical validation", "NOT resident deployment"):
        assert text in RATIFICATION["development_status"]["meaning"]
    assert SNAPSHOT["reopening_rule"] == ["a cross-family contradiction", "a dangerous educational effect", "a failure under a new intervention", "a failure of generalization"] and SNAPSHOT["minor_numerical_preference_reopens"] is False


# ---------------------------------------------------------------------------------------------------------------------------------------- P3-373 · nothing executable, nothing expanded
def test_t9_nothing_executable_reads_the_new_records_and_no_authority_was_expanded():
    import runtime_shadow
    assert runtime_shadow.COMMON_CORE_RUNTIME_AUTHORITY is False
    assert RATIFICATION["executable_change"] is False and RATIFICATION["amendment_3"] == "CLOSED" and REGION["decision"]["amendment_3"].startswith("CLOSED")
    assert RATIFICATION["authority"] == {"expanded": False, "common_core_runtime_authority": False, "live_configuration_bound_to_the_snapshot": False}
    assert SNAPSHOT["live_configuration"]["bound"] is False and SNAPSHOT["live_configuration"]["executable_change"] is False
    # FD-PROMOTE-01 (declared adaptation). At the ratification nothing executable named these records; the promotion deliberately binds the live authority to the snapshot, so the executable modules that name
    # it are now an EXACT declared set. What this still protects: the monitored limitation is named by exactly two modules and only as declared text (nothing executes it, nothing "fixes" it), and no
    # executable names the closure marker or the human re-review record (the binding pins that record's DIGEST, never its name).
    # FD-AUTHNE-08 (declared adaptation): the norepinephrine grant (data only; it extends the pressure grant and binds the SAME snapshot, by name, as part of its body) is the one module added to the set; it does not
    # name the monitored limitation, the closure marker or the human re-review record, so the rest of what this protects is unchanged.
    declared = {"GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1": ["runtime_authority.py", "runtime_ne_grant.py", "runtime_pressure_grant.py", "runtime_pressure_snapshot.py", "runtime_shadow_families.py"],
                "GI_BLOOD_RESUSCITATION_LOW_END_RESPONSE": ["runtime_authority.py", "runtime_pressure_grant.py"],
                "GI_PRESSURE_DEVELOPMENT_CALIBRATION_CLOSED": [], "PHASE3_HUMAN_FACULTY_REREVIEW": []}
    found = {token: sorted(path.name for path in ROOT.glob("*.py") if not path.name.startswith("test_") and token in path.read_text(encoding="utf-8", errors="replace")) for token in declared}
    assert found == declared, f"the executable modules that name the ratified records are not the declared set: {found}"
