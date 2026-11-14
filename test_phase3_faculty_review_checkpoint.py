"""P3-289: the checkpoint record of the CONTROLLED FACULTY DEVELOPMENT REVIEW environment of the GI pressure development authority experiment, rebuilt from the code and the other records.

TEST-SIDE. ``docs/revision/PHASE3_FACULTY_REVIEW_CHECKPOINT.json`` states what the repository can and cannot do at this checkpoint. Everything the code can say is READ FROM THE CODE (the review flag and
its fourteen conditions, the allowlist, the single-process lock and the filesystem lists, the seven scripted encounters, the bundle and feedback schemas, what is excluded after a halt and the only
resolution, the layer and isolation facts, the flags that stay off, the pinned grant, the pinned records); the eight statuses, the ONE verdict, the confirmations and the blockers are the checkpoint's own
decision, pinned here as literals. The review and mutation figures are REPORTED (a mutation run and a reviewer's tally cannot be recomputed by a test) and are kept apart from what the code says. The
certification figures (the tree fingerprint, the suite counts) are NOT in this record: a record cannot contain the fingerprint of the tree that includes it, so the final report states them.

This record SUPERSEDES nothing: the P3-278 checkpoint (``PHASE3_TURN_CHECKPOINT.json``) stays what it was, and a test here pins that it is still there and still says what it said. Nothing in this record is
a clinical validation, an approval of version 1, a consciousness authority, a resident deployment, a production authority, a resident pilot or the START of the faculty review, and a test refuses a record
that says otherwise. ``MRS_WRITE_FACULTY_REVIEW_CHECKPOINT=1`` regenerates it, once, by the person who changes the checkpoint.
"""
import ast
import json
import os
from pathlib import Path

import faculty_review_ui as ui
import runtime_authority as ra
import runtime_authority_session as se
import runtime_faculty_bundle as bundles
import runtime_faculty_review as fr
import runtime_pressure_grant as grants
import runtime_shadow as rs

ROOT = Path(__file__).resolve().parent
RECORD_PATH = ROOT / "docs" / "revision" / "PHASE3_FACULTY_REVIEW_CHECKPOINT.json"
PREVIOUS_PATH = ROOT / "docs" / "revision" / "PHASE3_TURN_CHECKPOINT.json"
SERIES_PATH = ROOT / "docs" / "revision" / "PHASE3_PRESSURE_AUTHORITY_SERIES.json"
VERSION = "P3-289"

#: The checkpoint's decision. Eight statuses, ONE verdict, and what the verdict does NOT do.
STATUSES = {
    "FACULTY_ENVIRONMENT_ISOLATION": "DEVELOPMENT_ONLY_FACULTY_ONLY_ACCOUNTS_ONLY_ONE_NAMED_FLAG_FOURTEEN_CONDITIONS_EVERY_ONE_REQUIRED_MISSING_OR_PARTIAL_MEANS_THE_AUTHORITY_IS_UNAVAILABLE_NEVER_PARTIALLY_ENABLED_FLAGS_FROM_THE_PROCESS_NOT_FROM_SECRETS_REREAD_WHENEVER_THE_AUTHORITY_ASKS_A_REVIEW_WHOSE_FLAG_DISAPPEARS_HALTS_ONE_PLACE_STARTS_ENCOUNTERS_AND_REFUSES_ANY_BUT_THE_LAUNCHER_A_REFUSED_CONFIGURATION_WRITES_NOTHING",
    "SINGLE_PROCESS_ENFORCEMENT": "EXCLUSIVE_FLOCK_ON_A_FILE_INSIDE_THE_STORE_HELD_FOR_THE_LIFE_OF_THE_PROCESS_BOUND_TO_THE_FILES_DEVICE_AND_INODE_A_SECOND_PROCESS_A_FORKED_CHILD_A_DELETED_OR_MOVED_LOCK_AND_A_NETWORK_OR_UNVETTED_FILESYSTEM_ARE_REFUSED_ONE_REVIEW_PROCESS_PER_STORE_ON_A_LOCAL_FILESYSTEM_NOT_ACROSS_MACHINES_NOT_MULTIPROCESS_SOLVED",
    "PRESSURE_AUTHORITY": "GI_PRESSURE_DEVELOPMENT_AUTHORITY_UNCHANGED_SBP_DBP_MAP_TWO_CASES_BEHIND_THE_EXPLICIT_GRANT_THE_REVIEW_MODE_ENABLES_NOTHING_THE_GRANT_DID_NOT_ALREADY_ALLOW_SEVEN_SCRIPTED_ENCOUNTERS_REPRODUCE_THE_CERTIFIED_SERIES_ON_THE_REAL_PAGE",
    "ARTIFACT_REVIEW_BUNDLE": "ONE_DETERMINISTIC_CREATE_ONLY_ATOMIC_BUNDLE_PER_ENCOUNTER_THE_AUTHORITY_VIEW_APART_FROM_THE_NONAUTHORITATIVE_COMPARATOR_NO_GRADE_OF_ANY_KIND_AGAINST_THE_LEGACY_ENGINE_EVIDENCE_THAT_FAILS_ITS_OWN_CHECKS_IS_SHOWN_AND_NOT_JUDGED_THE_BUNDLE_NAMES_ITS_STORED_ARTIFACT_AND_BELONGS_TO_THE_ENCOUNTER_ON_SCREEN",
    "FACULTY_FEEDBACK": "TEN_EDUCATIONAL_QUESTIONS_BOUND_TO_ONE_STORED_BUNDLE_BLINDED_ANSWERS_FIXED_AT_THE_REVEAL_ONLY_THE_TEN_QUESTIONS_STORED_CASE_SCENARIO_BUNDLE_AND_ROLE_REQUIRED_IDENTIFIER_TRIPWIRE_NOT_A_GUARANTEE_SYNTHETIC_CASES_ONLY",
    "EFFECTIVE_STOP_EXPERIENCE": "AFTER_A_HALT_NOTHING_THAT_MUTATES_THE_ENCOUNTER_RUNS_READING_AND_THE_BUNDLE_STAY_ECG_CANCEL_PENDING_AND_RETROSPECTIVE_EXPLANATION_ARE_BLOCKED_AND_EXCLUDED_THE_ONLY_RESOLUTION_IS_TO_EXIT_THE_NOTICE_IS_OPERATIONAL_AND_SAYS_NOTHING_OF_THE_PATIENT",
    "RESIDENT_ISOLATION": "A_RESIDENT_ACCOUNT_GETS_A_GENERIC_REFUSAL_NO_LAUNCHER_NO_PANEL_NO_STATUS_NO_BUNDLE_NO_FEEDBACK_THE_RESIDENT_FACING_VIEWS_CARRY_NO_AUTHORITY_VOCABULARY_THE_COMMON_CONSCIOUSNESS_IS_NEVER_RESIDENT_VISIBLE_STAFF_ATTEMPTS_ARE_SANDBOX_AND_NEVER_SCORED_NOT_READY_FOR_RESIDENTS",
    "PILOT_ISOLATION": "THE_FIRST_PILOT_CONFIGURATION_REFUSES_THE_REVIEW_MODE_THE_FROZEN_PILOT_BRANCH_AND_BASELINES_ARE_UNTOUCHED_FLAGS_OFF_BEHAVIOUR_IS_IDENTICAL_AND_COSTS_ONE_LOOKUP",
}
VERDICT = "A_GI_PRESSURE_AUTHORITY_READY_FOR_CONTROLLED_FACULTY_REVIEW"
VERDICT_ENABLES = ("NOTHING BEYOND the GI pressure development authority the faculty already granted (SBP, DBP, MAP derived; gi_bleed_57m and gi_bleed_72f; the development environment): it makes the "
                   "experiment ELIGIBLE FOR A CONTROLLED, FACULTY-ONLY, SINGLE-PROCESS DEVELOPMENT REVIEW. It does NOT start that review (the actual faculty review needs a separate instruction), is not a "
                   "resident pilot, is not production, is not a clinical validation, grants no consciousness authority, no write into mental_status, no first-pilot change and no approval of version 1 for "
                   "authority. The next step is the ACTUAL FACULTY REVIEW, which is not taken here")
REMAINING_BLOCKERS = (
    "the session record and the provenance anchor are unsigned: accepted as a declared limitation for this single-process development review only (FD-FAC-05); a signature needs a key, a faculty decision",
    "one process per store on a local filesystem is enforced; several instances with separate disks cannot be seen by the code and are the operator's responsibility, and a store tampered with by hand is detected at the next page run, not prevented in between (FD-FAC-06)",
    "ECG acquisition, cancelling pending actions and the retrospective explanation are blocked after a halt and excluded from this protocol; there is no resume, rollback or restart from the pre-authority snapshot (FD-FAC-07, FD-FAC-08)",
    "the identifier filter of the feedback form is a tripwire (it cannot recognise a name with no title and no label) and the grading guard of the bundle reads key words, not the free text of values; the internal feedback API accepts a blinded-answer snapshot fabricated by its caller (the page does not fabricate it)",
    "the halt notice is the development English text; two GI cases for development only; the common consciousness stays unmapped, nonauthoritative and visible to faculty only as a labelled comparison (FD-FAC-09, FD-FAC-10); V1 is ratified for development experiments only",
)
CONFIRMATIONS = {
    "gi_pressure_authority_only": True, "no_consciousness_authority": True, "no_resident_deployment": True, "first_pilot_unchanged": True, "scoring_unchanged": True,
    "no_terminal_semantics": True, "no_physiology_retuned": True, "no_clinical_validation_claim": True, "common_core_runtime_authority_remains_false": True,
    "legacy_mental_status_unchanged": True, "no_common_consciousness_visible_to_residents": True, "no_production_authority": True, "v1_not_promoted_to_authority": True,
    "no_authority_domain_added": True, "no_faculty_review_started": True, "flags_off_behaviour_identical": True, "no_second_engine": True, "no_cryptographic_signing_added": True,
    "multiprocess_not_solved_by_assumption": True, "no_case_beyond_the_two_gi_cases": True,
}
#: REPORTED by the cycle (not recomputable by a test): the independent review of the environment and the mutation proof of its repairs. The reviewer's own per-attack table is in the cycle's working record.
REVIEW = {"reviewer": "independent, read-only, adversarial, on its own copy of the candidate; thirteen attack scenarios",
          "held": 8, "broken_high": 1, "broken_medium": 1, "broken_low_medium": 2, "broken_low": 1, "unclear_or_low": 5,
          "reproduced_with_an_own_probe_before_any_repair_and_repaired": [
              "HIGH B1 a bundle and a reveal of an earlier encounter survived into the next one (feedback was written against the wrong case and scenario)",
              "MEDIUM B2 the repeat-attempt button started a non-allowlisted case inside the review environment",
              "LOW-MEDIUM B3 a shadow-family list that left GI out kept the review enabled and the first turn aborted",
              "LOW-MEDIUM B5 feedback and bundle integrity: never-stored bundle, extra answer keys, identifier shapes, forged reveal, grading-key variants, scenario/case mismatch, path traversal, truncated files, evidence that fails its own checks, hard-coded overlay flags"],
          "low_repaired": ["B4 lock file deleted or directory moved under a running review; thread race on the probe file; filesystem denylist replaced by an allowlist"],
          "unclear_repaired_or_declared": ["review flag removed mid-encounter (now a halt)", "a forged enabled decision (the environment is read again)", "non-GI repeat panel (the bundle is shown unusable, no form)",
                                           "launcher abandon on an unreadable store (now a visible refusal)", "the lock binds review processes only (declared)"],
          "mutants_of_the_mechanisms": 72, "mutants_killed": 72, "mutants_equivalent_declared": 0, "equivalent_mutants": [],
          "mutation_note": "71 killed in the first run over the repaired candidate; the one survivor (C1, a misspelled flag with no published decision) was covered by test f26 and killed on rerun; R7 (thread race on the probe file) is probabilistic by nature"}


def _imports(module_path: Path) -> list:
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module.split(".")[0])
    return sorted(found)


def build_record() -> dict:
    series = json.loads(SERIES_PATH.read_text(encoding="utf-8"))
    previous = json.loads(PREVIOUS_PATH.read_text(encoding="utf-8"))
    after = fr.surface_after_halt()
    body = {
        "record_type": "PHASE3_FACULTY_REVIEW_CHECKPOINT", "version": VERSION, "decided_on": "2026-11-13",
        "from_the_code": {
            "review_layer_version": fr.VERSION, "bundle_layer_version": bundles.VERSION, "review_flag": fr.FLAG, "review_mode": fr.MODE_ON, "offline_flag": fr.OFFLINE_FLAG,
            "conditions": list(fr.CONDITIONS), "configuration_conditions": list(fr.CONFIGURATION_CONDITIONS), "environment_conditions": list(fr.ENVIRONMENT_CONDITIONS),
            "faculty_roles": list(fr.FACULTY_ROLES), "allowlist": list(fr.ALLOWLIST), "authority_mode": fr.AUTHORITY_MODE, "environment": fr.ENVIRONMENT, "family": fr.FAMILY,
            "session_key": fr.SESSION_KEY, "review_directory": fr.REVIEW_DIRNAME,
            "single_process": {"lock_file": "single_process.lock", "filesystem_statuses": [fr.FS_LOCAL, fr.FS_NETWORK, fr.FS_UNKNOWN, fr.FS_UNVERIFIED],
                              "local_filesystems": list(fr.LOCAL_FILESYSTEMS), "network_filesystems": list(fr.NETWORK_FILESYSTEMS)},
            "scenarios": [{"id": item["id"], "case_id": item["case_id"], "series": item["series"], "expected": item["expected"]} for item in fr.SCENARIOS], "scenario_set_problems": fr.scenario_problems(),
            "bundle": {"type": bundles.BUNDLE_TYPE, "comparator_label": bundles.COMPARATOR_LABEL, "forbidden_words": list(bundles.FORBIDDEN_BUNDLE_KEYS), "forbidden_phrases": list(bundles.FORBIDDEN_BUNDLE_PHRASES),
                       "limitations": len(bundles.LIMITATIONS)},
            "feedback": {"type": bundles.FEEDBACK_TYPE, "questions": [{"id": item["id"], "stage": item["stage"], "choices": list(item["choices"])} for item in bundles.QUESTIONS],
                         "overall_choices": list(bundles.OVERALL), "reviewer_roles": list(bundles.REVIEWER_ROLES), "max_comment_characters": bundles.SCHEMA["max_comment_characters"]},
            "after_a_halt": {"allowed": after["allowed"], "blocked": after["blocked"], "excluded_unjudged": after["excluded_unjudged"], "resolution": after["resolution"],
                             "unsupported_resolutions": after["unsupported_resolutions"], "notice": after["notice"]},
            "page": {"challenge_id": ui.CHALLENGE_ID, "banner": ui.BANNER, "generic_refusal": ui.GENERIC_REFUSAL, "ui_imports": _imports(ROOT / "faculty_review_ui.py")},
            "layer_sources_include_the_review_modules": all(name in rs.LAYER_SOURCES for name in ("runtime_faculty_review.py", "runtime_faculty_bundle.py")),
            "one_place_starts_encounters": "MRS_FACULTY_DEVELOPMENT_REVIEW" in (ROOT / "curriculum_runtime.py").read_text(encoding="utf-8"),
            "grant_id": grants.GRANT_ID, "grant_fingerprint_is_pinned": grants.GRANT_FINGERPRINT == grants.GRANT["fingerprint"], "grant_excluded_domains": list(grants.EXCLUDED_DOMAINS),
            "authority_domain": list(ra.AUTHORITY_DOMAIN), "authority_cases": sorted(ra.AUTHORITY_CASES), "common_core_runtime_authority": rs.COMMON_CORE_RUNTIME_AUTHORITY,
            "approved_authority_snapshots": sorted(ra.APPROVED_SNAPSHOTS),
        },
        "pinned_records": {"pressure_series": {"record": "docs/revision/PHASE3_PRESSURE_AUTHORITY_SERIES.json", "record_digest": series["record_digest"], "runs": series["summary"]["runs"]},
                           "previous_checkpoint": {"record": "docs/revision/PHASE3_TURN_CHECKPOINT.json", "record_digest": previous["record_digest"], "verdict_then": previous["verdict"],
                                                   "blockers_then": len(previous["remaining_blockers"])}},
        "reported": {"review": dict(REVIEW)},
        "statuses": dict(STATUSES), "verdict": VERDICT, "verdict_enables": VERDICT_ENABLES, "remaining_blockers": list(REMAINING_BLOCKERS), "confirmations": dict(CONFIRMATIONS),
        "statement": "A technical checkpoint of a controlled development review environment. It is not a clinical validation, an approval of version 1, a consciousness authority, a resident deployment, a production authority, a resident pilot or the start of the faculty review.",
    }
    return {**body, "record_digest": ra.digest_of(body)}


def test_c1_the_checkpoint_record_is_what_the_code_and_the_other_records_say_now():
    if os.environ.get("MRS_WRITE_FACULTY_REVIEW_CHECKPOINT") == "1":
        RECORD_PATH.write_text(json.dumps(build_record(), indent=1, sort_keys=True), encoding="utf-8")
    assert RECORD_PATH.exists(), "the record is produced once and committed"
    stored, live = json.loads(RECORD_PATH.read_text(encoding="utf-8")), build_record()
    assert stored == json.loads(json.dumps(live)), "the committed checkpoint no longer matches the code: regenerate it deliberately"


def test_c2_the_record_says_what_it_must_and_claims_nothing_it_may_not():
    record = json.loads(RECORD_PATH.read_text(encoding="utf-8"))
    code = record["from_the_code"]
    assert code["review_flag"] == "MRS_FACULTY_DEVELOPMENT_REVIEW" and code["review_mode"] == "faculty_development_review" and len(code["conditions"]) == 14
    assert set(code["conditions"]) - set(code["configuration_conditions"]) == {"faculty_role"}, "the account is the only condition the deployment does not decide"
    assert {"shadow_family", "single_process", "accounts", "no_pilot", "not_streamlit_cloud", "offline_cases", "registered_grant"} <= set(code["conditions"])
    assert code["faculty_roles"] == ["faculty", "admin"] and code["allowlist"] == ["gi_bleed_57m", "gi_bleed_72f"] and code["authority_mode"] == "PRESSURE_ONLY" and code["environment"] == "development"
    assert code["single_process"]["filesystem_statuses"] == ["LOCAL", "NETWORK_REFUSED", "UNKNOWN_NOT_VERIFIABLE", "NOT_ON_THE_LOCAL_LIST_REFUSED"]
    assert "ext4" in code["single_process"]["local_filesystems"] and "nfs4" in code["single_process"]["network_filesystems"] and "virtiofs" not in code["single_process"]["local_filesystems"]
    assert len(code["scenarios"]) == 7 and code["scenario_set_problems"] == [] and {item["case_id"] for item in code["scenarios"]} == {"gi_bleed_57m", "gi_bleed_72f"}
    assert [item["expected"] for item in code["scenarios"]].count("HALTED_AT_COLLAPSE_BOUNDARY") == 2 and [item["expected"] for item in code["scenarios"]].count("HALTED_BY_UNSUPPORTED_ACTION") == 1
    assert code["bundle"]["comparator_label"] == "NONAUTHORITATIVE DEVELOPMENT COMPARISON" and {"score", "closeness", "error", "agreement"} <= set(code["bundle"]["forbidden_words"])
    assert "digest" not in code["bundle"]["forbidden_words"] and "match" not in code["bundle"]["forbidden_words"], "the evidence block's own words are not grades"
    feedback = code["feedback"]
    assert [item["id"] for item in feedback["questions"]] == [f"Q{i}" for i in range(1, 11)] and feedback["overall_choices"] == ["ACCEPT", "ACCEPT_WITH_LIMITATION", "RECALIBRATE", "REJECT"]
    assert [item["stage"] for item in feedback["questions"]].count("BLINDED_AUTHORITY_ONLY") == 5 and feedback["reviewer_roles"] == ["faculty", "admin", "faculty_guest_reviewer"]
    halt = code["after_a_halt"]
    assert halt["excluded_unjudged"] == ["ecg_acquisition", "cancel_pending_orders", "retrospective_explanation"] and halt["resolution"] == "ABANDON_EXPERIMENT"
    assert halt["unsupported_resolutions"] == ["RESUME", "ROLLBACK", "RESTART_FROM_PREAUTHORITY_SNAPSHOT"] and halt["notice"].startswith("DEVELOPMENT AUTHORITY EXPERIMENT HALTED")
    assert not set(halt["allowed"]) & set(halt["blocked"]) and halt["blocked"], "the guard blocks what mutates and allows only reading and leaving"
    assert code["page"]["ui_imports"] == ["__future__", "account_portal", "typing"], "the page module imports nothing of the Phase-3 layer"
    assert code["layer_sources_include_the_review_modules"] is True and code["one_place_starts_encounters"] is True
    assert code["common_core_runtime_authority"] is False and code["approved_authority_snapshots"] == ["gi_pressure_committed"] and code["grant_fingerprint_is_pinned"] is True
    assert code["authority_domain"] == ["sbp", "dbp", "map"] and code["authority_cases"] == ["gi_bleed_57m", "gi_bleed_72f"]
    assert {"consciousness", "mental_status", "collapse", "terminal", "pulse", "oxygenation", "lactate", "hb"} == set(code["grant_excluded_domains"])
    assert set(record["statuses"]) == {"FACULTY_ENVIRONMENT_ISOLATION", "SINGLE_PROCESS_ENFORCEMENT", "PRESSURE_AUTHORITY", "ARTIFACT_REVIEW_BUNDLE", "FACULTY_FEEDBACK", "EFFECTIVE_STOP_EXPERIENCE",
                                       "RESIDENT_ISOLATION", "PILOT_ISOLATION"} and len(record["statuses"]) == 8
    assert record["verdict"] == VERDICT and record["verdict"][:2] in ("A_", "B_", "C_", "D_") and sum(record["verdict"].startswith(letter + "_") for letter in "ABCD") == 1
    assert record["verdict_enables"].startswith("NOTHING BEYOND") and "does NOT start that review" in record["verdict_enables"] and "not taken here" in record["verdict_enables"]
    assert "is not a resident pilot" in record["verdict_enables"] and "is not production" in record["verdict_enables"] and "is not a clinical validation" in record["verdict_enables"]
    assert all(record["confirmations"].values()) and len(record["confirmations"]) == 20
    text = json.dumps(record).lower()
    for forbidden in ("clinically validated", "consciousness authority granted", "approved for authority", "resident approved", "production approved", "deployed to residents", "faculty review started", "pilot started"):
        assert forbidden not in text, forbidden
    assert "GI_DEVELOPMENT_SNAPSHOT" not in json.dumps(record), "the review record never names the consciousness snapshot"
    assert len(record["remaining_blockers"]) == 5 and record["remaining_blockers"][0].startswith("the session record and the provenance anchor are unsigned")
    review = record["reported"]["review"]
    assert (review["broken_high"], review["broken_medium"], review["broken_low_medium"], review["broken_low"], review["unclear_or_low"]) == (1, 1, 2, 1, 5)
    assert len(review["reproduced_with_an_own_probe_before_any_repair_and_repaired"]) == 4
    assert review["mutants_killed"] + review["mutants_equivalent_declared"] == review["mutants_of_the_mechanisms"] and len(review["equivalent_mutants"]) <= review["mutants_equivalent_declared"]


def test_c3_the_previous_checkpoint_is_still_there_and_still_says_what_it_said():
    """This checkpoint supersedes nothing: it adds an environment around an authority the P3-278 checkpoint certified."""
    previous = json.loads(PREVIOUS_PATH.read_text(encoding="utf-8"))
    assert previous["verdict"].startswith("A_") and len(previous["remaining_blockers"]) == 5 and previous["remaining_blockers"][0].startswith("the session record and the provenance anchor are unsigned")
    record = json.loads(RECORD_PATH.read_text(encoding="utf-8"))
    assert record["pinned_records"]["previous_checkpoint"]["record_digest"] == previous["record_digest"] and record["verdict"].startswith("A_")


def test_c4_the_series_this_checkpoint_pins_is_the_one_the_earlier_checkpoints_pin():
    """One series, three checkpoints, and seven scripted encounters that reproduce it: regenerating the series without regenerating the checkpoints fails here."""
    record = json.loads(RECORD_PATH.read_text(encoding="utf-8"))
    turn = json.loads(PREVIOUS_PATH.read_text(encoding="utf-8"))
    series = json.loads(SERIES_PATH.read_text(encoding="utf-8"))
    assert record["pinned_records"]["pressure_series"]["record_digest"] == turn["pinned_records"]["pressure_series"]["record_digest"] == series["record_digest"]
    assert record["pinned_records"]["pressure_series"]["runs"] == series["summary"]["runs"] == 26
    covered = {(item["case_id"], item["series"]) for item in record["from_the_code"]["scenarios"]}
    assert covered <= {(row["case"], row["scenario"]) for row in series["runs"]}, "every scripted review encounter is a run the certified series already contains"
