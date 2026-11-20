"""P3-449 and P3-450 (records): the human review of the norepinephrine rate-control scenarios and the closure of the manual semantics are sealed, indexed, bound to what the faculty reviewed, and change nothing executable.

What it proves (the documents, the decisions and the checkpoint are tested apart, in test_phase3_nr_ratification_records.py, which belongs to the third commit of the publication):

* the HUMAN record is exactly what the faculty reported (five overall judgments of the five scenarios, in the order of the review; the reported totals are the tabulation of the judgments), is marked
  ``HUMAN_FACULTY_REVIEW_REPORTED_NOT_STORE_VERIFIED`` because the persisted store is not in the repository, invents no answer, comment, event, timestamp or identity, and is bound to the pinned review set;
* every earlier record this one rests on is preserved: its file is the one the index pins;
* the closure carries the seven faculty decisions, the supported operations, the unsupported domains and the durable status; it is a DEVELOPMENT status and not a validation, an approval or an authority;
* nothing executable changed by these records: no physiology, no parameter, no authority, no grant.
"""
import hashlib
import json
import re
from pathlib import Path

import pytest

import faculty_titration_review as ftt
import faculty_trajectory_review as ftr
import historical_records as hr
import test_nr_manual_ratification_analysis as build

ROOT = Path(__file__).resolve().parent
REV = ROOT / "docs" / "revision"
FILES = {"human": build.HUMAN_PATH.name, "closure": build.CLOSURE_PATH.name}
HUMAN = json.loads(build.HUMAN_PATH.read_text(encoding="utf-8"))
CLOSURE = json.loads(build.CLOSURE_PATH.read_text(encoding="utf-8"))
SNAPSHOT = json.loads((REV / "COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1.json").read_text(encoding="utf-8"))
REPORTED_ORDER = ["TIT-1", "TIT-2", "TIT-3", "TIT-4", "TIT-5"]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_n1_the_two_records_are_sealed_versioned_and_indexed_with_the_bytes_the_index_pins():
    index = hr.load_index(ROOT)
    for key, name in FILES.items():
        record = {"human": HUMAN, "closure": CLOSURE}[key]
        assert hr.record_problems(record) == [], name
        block = record["provenance"]
        assert block["contract"] == hr.CONTRACT and block["generated_on"] == "2026-11-20" and block["supersedes"] is None
        entry = index["records"][name]
        assert entry["class"] == hr.VERSIONED and entry["record_id"] == block["record_id"] and entry["record_digest"] == record["record_digest"] and entry["file_sha256"] == hr.file_sha256(REV / name)
    assert {HUMAN["provenance"]["record_id"], CLOSURE["provenance"]["record_id"]} == {build.HUMAN_ID, build.CLOSURE_ID}
    assert hr.index_problems(ROOT) == []


def test_n2_the_human_record_is_exactly_what_the_faculty_reported_in_the_order_of_the_review():
    assert [entry["scenario_id"] for entry in HUMAN["scenarios"]] == REPORTED_ORDER == [scenario_id for scenario_id, _ in ftt.SEQUENCE]
    assert [entry["overall"] for entry in HUMAN["scenarios"]] == ["ACCEPT"] * 5
    assert [entry["reported_name"] for entry in HUMAN["scenarios"]] == ["increase 5 -> 10 mcg/min", "decrease 10 -> 4 mcg/min", "stop", "sequence 5 -> 10 -> 4 -> stop", "restart 10 -> stop -> 10"]
    assert HUMAN["overall_counts"] == {"ACCEPT": 5, "ACCEPT_WITH_LIMITATION": 0, "RECALIBRATE": 0, "REJECT": 0} == HUMAN["overall_counts_recomputed_from_the_scenarios"]
    assert all(entry["overall"] in ftr.OVERALL for entry in HUMAN["scenarios"]) and all(entry["recalibration_requested"] is False for entry in HUMAN["scenarios"])
    assert HUMAN["evidence_class"] == "HUMAN_FACULTY_REVIEW" and HUMAN["review"]["review_set_id"] == "NOREPINEPHRINE_TITRATION_V1_FACULTY_REVIEW"
    assert HUMAN["review"]["candidate_reviewed"] == "CENTER_REFERENCE" and HUMAN["review"]["pressure_only_first_pass"] is True


def test_n3_the_provenance_is_marked_reported_not_verified_and_nothing_is_invented():
    provenance = HUMAN["provenance_of_the_evidence"]
    assert provenance["verification"] == "HUMAN_FACULTY_REVIEW_REPORTED_NOT_STORE_VERIFIED" and provenance["persisted_store_available_to_the_assistant"] is False
    assert provenance["reviewer_identity_recorded"] is False and provenance["reviewer_name"] is None
    assert all(entry["first_pass_answers_Q1_to_Q5"] == "NOT_REPORTED" and entry["free_text_comments"] == "NONE_REPORTED" for entry in HUMAN["scenarios"])
    keys = set()
    for entry in HUMAN["scenarios"]:
        keys |= set(entry)
    assert not keys & {"lock_event", "locked_at", "timestamp", "submitted_at", "reviewer", "comment", "answers"}, "no event, timestamp, comment or identity was invented"
    for text in ("the answers Q1 to Q5 (not reported)", "the lock and submit events, their order and their timestamps", "the reviewer's identity"):
        assert text in HUMAN["not_verified"], text
    assert "assistant's own synthetic test and screenshot sessions" in provenance["why"], "the synthetic sessions found in the container are named as NOT human evidence"


def test_n4_the_record_is_bound_to_the_pinned_set_by_the_digest_of_every_reviewed_item():
    loaded = ftt.load_set()
    assert loaded["ok"] and HUMAN["review"]["review_set_digest"] == loaded["digest"] == ftt.PINNED_SET_DIGEST
    for entry in HUMAN["scenarios"]:
        item = loaded["items"][entry["scenario_id"]]
        assert entry["reviewed_item_digest"] == ftr.item_digest(item) and entry["title_in_the_set"] == item["title"]
        assert entry["reviewed_trajectory_digest"] == hr.digest_of({"scenario_id": entry["scenario_id"], "timeline": item["timeline"], "common": item["common"]})


def test_n5_every_earlier_record_is_preserved_byte_for_byte():
    for source in (HUMAN["preserved_original_evidence"], CLOSURE["preserved_original_evidence"]):
        for name, entry in source.items():
            if not isinstance(entry, dict):
                continue
            path = ROOT / entry["file"]
            assert path.exists() and _sha(path) == entry["file_sha256"], name
            assert json.loads(path.read_text(encoding="utf-8")).get("record_digest") == entry["record_digest"], name
    assert HUMAN["preserved_original_evidence"] == CLOSURE["preserved_original_evidence"]
    assert HUMAN["preserved_original_evidence"]["titration_review_set_digest_pinned_in_code"] == ftt.PINNED_SET_DIGEST


def test_n6_the_closure_carries_the_seven_decisions_the_operations_the_domains_and_the_status():
    assert CLOSURE["status"] == "NOREPINEPHRINE_MANUAL_RATE_CONTROL_DEVELOPMENT_SEMANTICS_CLOSED" and CLOSURE["status_meaning"] == "accepted for DEVELOPMENT semantics only"
    assert list(CLOSURE["faculty_decisions"]) == [f"FD-NR-0{index}" for index in range(1, 8)]
    assert CLOSURE["supported_operations"] == ["START", "INCREASE", "DECREASE", "STOP", "RESTART"] and CLOSURE["supported_unit"] == "mcg/min"
    assert CLOSURE["calibration_closed_for_this_capability"] == ["tone_gain", "half_effect_rate_mcg_min", "onset_tau_min", "offset_tau_min"]
    assert CLOSURE["not_reopened"] == ["LOW", "HIGH", "the CENTER_REFERENCE selection", "the common-tone calibration"]
    assert set(CLOSURE["unsupported_domains"]) == {"MCG_PER_KG_PER_MIN", "AUTOMATIC_MAP_TARGET_TITRATION", "RELATIVE_COMMAND_WITHOUT_A_SUPPORTED_ACTIVE_RATE_CONTEXT", "CONSCIOUSNESS_UNDER_TONE", "PUMP_LIMITED_EDUCATIONAL_PROMOTION"}
    assert CLOSURE["faculty_decisions"]["FD-NR-03"].count("does NOT mean clinical validation") == 1 and "live authority expansion" in CLOSURE["faculty_decisions"]["FD-NR-03"]
    for what in ("clinical validation", "production approval", "resident approval", "live authority expansion"):
        assert what in CLOSURE["is_not"], what


def test_n7_the_closure_is_bound_to_the_ratified_snapshot_and_changes_nothing_executable():
    from clinical_core import amendment_3 as a3
    bound = CLOSURE["bound_to"]
    assert bound["common_tone_snapshot"] == "COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1" and bound["snapshot_record_digest"] == SNAPSHOT["record_digest"] and bound["selected_witness"] == "CENTER_REFERENCE"
    assert bound["binding_unchanged"] == SNAPSHOT["binding"] and bound["lineage"] == "PHASE2_AMENDMENT_3" and bound["core_digest"] == a3.amended_core_digest_now()
    assert CLOSURE["executable_change"] is False and CLOSURE["physiology_change"] is False and CLOSURE["tone_recalibrated"] is False and CLOSURE["pump_coupling_modified"] is False
    authority = CLOSURE["authority"]
    assert authority["common_core_runtime_authority"] is False and authority["expanded"] is False and authority["norepinephrine_authority_granted"] is False and authority["live_configuration_bound_to_the_snapshot"] is False
    for what in ("automatic titration", "a weight-based dose", "any other vasopressor", "consciousness authority", "terminal authority", "recovery from a malformed-order boundary"):
        assert what in authority["not_granted"], what


def test_n8_the_malformed_order_behavior_stays_fail_closed_and_the_target_defect_is_open_at_the_time_of_ratification():
    malformed = CLOSURE["malformed_order_behavior"]
    assert malformed == {"status": "PROVISIONALLY_FAIL_CLOSED", "decision": "FD-NR-07", "recovery_policy_changed": False, "recovery_is_a_separate_faculty_decision": True}
    issue = CLOSURE["next_safety_issue_at_the_time_of_ratification"]
    assert issue["id"] == "TARGET_ORDER_PARSED_AS_RATE" and issue["decision"] == "FD-NR-05" and issue["status"] == "OPEN_AT_RATIFICATION"
    assert "not edited when it is repaired" in issue["note"], "a record is immutable: the repair is recorded by the checkpoint, never by editing this record"


def test_n9_the_records_regenerate_to_the_stored_content_under_the_same_generating_code():
    current = build.generating_code()
    for key, name in FILES.items():
        record = {"human": HUMAN, "closure": CLOSURE}[key]
        if not hr.same_generating_code(record, current):
            pytest.skip("the generating code moved after the record was written: the record is history, its bytes are pinned by the index, and it is not regenerated")
    made = build.reproduce()
    for key, record in {"human": HUMAN, "closure": CLOSURE}.items():
        stored = {name: value for name, value in record.items() if name not in ("provenance", "record_digest")}
        assert stored == made[key], key


def test_n10_a_mutation_of_the_reported_judgments_is_caught():
    """A tampered tabulation (a REJECT hidden in the totals, a scenario out of order, a recorded comment) does not verify against the pinned set and the reported counts."""
    for mutate, what in (({"TIT-3": "REJECT"}, "a judgment changed"),):
        changed = {key: dict(value) for key, value in build.REPORTED.items()}
        for scenario_id, overall in mutate.items():
            changed[scenario_id]["overall"] = overall
        assert build.counts(changed) != build.REPORTED_COUNTS, what
    assert build.counts(build.REPORTED) == build.REPORTED_COUNTS


def test_n11_no_model_name_no_reviewer_name_no_secret_in_the_records():
    text = " ".join((REV / name).read_text(encoding="utf-8") for name in FILES.values()) + (ROOT / "test_nr_manual_ratification_analysis.py").read_text(encoding="utf-8")
    for forbidden in ("claude-", "sonnet", "opus", "haiku", "fable", "anthropic", "password", "api_key", "secret_key", "BEGIN PRIVATE"):
        assert forbidden not in text.lower(), forbidden
    assert not re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text), "no e-mail address"
