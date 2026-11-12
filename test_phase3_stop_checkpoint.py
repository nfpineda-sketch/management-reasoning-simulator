"""P3-264: the checkpoint record of the EFFECTIVE STOP of the GI development pressure authority experiment, rebuilt from the code and the other records.

TEST-SIDE. ``docs/revision/PHASE3_EFFECTIVE_STOP_CHECKPOINT.json`` states what the repository can and cannot do at this checkpoint. Everything the code can say is READ FROM THE CODE (the
lifecycle graph, the stopped states, the operation classes and their members, the stop classes, the operator resolutions, the notice and its forbidden words, the session fields the record
travels in, the pinned grant, the flag that stays False, the pinned records); the eight statuses, the ONE verdict, the confirmations and the blockers are the checkpoint's own decision,
pinned here as literals. The review figures are REPORTED (a mutation run and a reviewer's tally cannot be recomputed by a test) and are kept apart from what the code says.

This record SUPERSEDES, for the stop only, two statements of the P3-249 checkpoint (``PHASE3_PRESSURE_CHECKPOINT.json``): that ``INVALID_FOR_CONTINUATION`` was *advisory to the encounter* and that
a resumed encounter was *marked, not prevented*. It does not rewrite that record (a record is what was decided then); a test here pins that it still says so. Nothing in this record is a
clinical validation, an approval of version 1, a consciousness authority, a resident deployment or a production authority, and a test refuses a record that says otherwise.
``MRS_WRITE_STOP_CHECKPOINT=1`` regenerates it, once, by the person who changes the checkpoint.
"""
import json
import os
from collections import Counter
from pathlib import Path

import runtime_authority as ra
import runtime_authority_session as se
import runtime_pressure_grant as grants
import runtime_shadow as rs
from curriculum_runtime import SESSION_FIELDS

ROOT = Path(__file__).resolve().parent
RECORD_PATH = ROOT / "docs" / "revision" / "PHASE3_EFFECTIVE_STOP_CHECKPOINT.json"
PREVIOUS_PATH = ROOT / "docs" / "revision" / "PHASE3_PRESSURE_CHECKPOINT.json"
SERIES_PATH = ROOT / "docs" / "revision" / "PHASE3_PRESSURE_AUTHORITY_SERIES.json"
VERSION = "P3-264"

#: The checkpoint's decision. Eight statuses, ONE verdict, and what the verdict does NOT do.
STATUSES = {
    "PRESSURE_AUTHORITY_VALIDATION": "GI_PRESSURE_DEVELOPMENT_AUTHORITY_UNCHANGED_AND_STILL_VALID_BEHIND_THE_EXPLICIT_GRANT_THE_TENTH_GATE_CONDITION",
    "POST_COMMIT_STOP": "EFFECTIVE_AFTER_THE_FIRST_REAL_COMMIT_INVALID_FOR_CONTINUATION_BLOCKS_CLINICAL_TIME_AND_MANAGEMENT_ACTIONS_NO_SILENT_LEGACY_FALLBACK_THE_FAILING_TURN_ITSELF_ALREADY_RAN",
    "RESTART_PERSISTENCE": "THE_SESSION_RECORD_TRAVELS_WITH_THE_SAVED_ENCOUNTER_A_REOPENED_STOPPED_ENCOUNTER_STAYS_STOPPED_FLAGS_ON_OR_OFF_AND_AN_ACTIVE_ONE_WITHOUT_ITS_SITE_IS_STOPPED_AN_UNSIGNED_RECORD_IS_A_DECLARED_LIMIT",
    "PAGE_CONTINUATION_GUARD": "EVERY_ENGINE_ENTRY_AND_EVERY_RESIDENT_CONTROL_IS_BEHIND_THE_GUARD_OR_NOT_DRAWN_INVENTORY_TRIPWIRES_FAIL_ON_ANY_NEW_ROUTE_OR_BUTTON",
    "COLLAPSE_BOUNDARY_STOP": "PRECOMMIT_EVERY_MINUTE_THE_BOUNDARY_CROSSING_STATE_IS_NEVER_COMMITTED_THEN_THE_SESSION_IS_NOT_CONTINUABLE_AN_EXPERIMENT_STOP_NOT_A_PATIENT_OUTCOME",
    "ARTIFACT_SESSION_CONSISTENCY": "RECORD_SITE_AND_ARTIFACT_AGREE_THE_RECORD_REPLAYS_FROM_THE_ARTIFACT_ALONE_DISAGREEMENT_DENIES_A_COMMIT_WHOSE_RECORD_CANNOT_BE_WRITTEN_STOPS",
    "SINGLE_PROCESS_CONCURRENCY": "SINGLE_PROCESS_SESSION_SAFETY_SUFFICIENT_FOR_DEVELOPMENT_NO_MUTABLE_MODULE_STATE_IN_THE_LAYER_SEVERAL_PROCESSES_SHARE_ONLY_THE_DURABLE_STORE",
    "RESIDENT_ISOLATION": "FLAGS_OFF_BEHAVIOUR_IDENTICAL_NO_RESIDENT_FACING_CLINICAL_TEXT_NO_COMMON_CONSCIOUSNESS_VISIBLE_THE_FIRST_PILOT_AND_OTHER_FAMILIES_UNTOUCHED_NOT_READY_FOR_RESIDENTS",
}
VERDICT = "A_GI_PRESSURE_DEVELOPMENT_AUTHORITY_WITH_EFFECTIVE_STOP_VALIDATED"
VERDICT_ENABLES = ("NOTHING BEYOND the GI pressure development authority the faculty already granted, now with an effective operational stop (SBP, DBP, MAP derived; gi_bleed_57m and "
                   "gi_bleed_72f; the development environment): no consciousness authority, no write into mental_status, no resident deployment, no production use, no first-pilot change, "
                   "no approval of version 1 for authority. The next decision is whether the experiment is ready for a CONTROLLED FACULTY-ONLY PILOT ENVIRONMENT; it is not taken here")
REMAINING_BLOCKERS = (
    "the turn that fails has already run on the legacy engine when the site judges it, so the stop applies from the NEXT action (the page and the record name the last authoritative minute and pressure)",
    "the session record is unsigned: a forged, less-restrictive record with a recomputed digest is not refutable from the record alone (the live site and the artifact still win when they exist); a signature needs a key, a faculty decision",
    "a saved encounter that lost BOTH its record and its site and whose legacy engine then advanced past the last committed minute is not recognised by the durable match (case, minute, committed pressures): a fail-open edge",
    "one Python process: several processes share only the durable store, whose files are written in one call; two encounters with an identical arrival that diverge at the same minute collide in the create-only store and the later one STOPS",
    "the only operator resolution implemented is to leave the session (reset, return, abandon): resuming from the preauthority snapshot and starting a new encounter from it are named, not built",
    "mapping the common consciousness word into the live mental_status stays blocked (seven consequential readers; the faculty decision that the common UNRESPONSIVE is not resident-visible); V1 stays ratified for development experiments only",
    "the stop notice is development-only English text: it is not a resident-facing or first-pilot text, and a controlled faculty-only environment would need its wording and language decided",
    "two GI cases and an arrival-relative semantics, accepted for development only: no generalization to a population or to another family (FD-AUTH-24)",
)
CONFIRMATIONS = {
    "gi_pressure_authority_only": True, "no_consciousness_authority": True, "common_core_runtime_authority_remains_false": True, "legacy_mental_status_unchanged": True,
    "no_common_consciousness_visible_to_residents": True, "no_resident_deployment": True, "no_production_authority": True, "first_pilot_unchanged": True,
    "scoring_unchanged": True, "no_clinical_terminal_rule_invented": True, "no_physiology_retuned": True, "no_clinical_validation_claim": True, "v1_not_promoted_to_authority": True,
    "no_authority_domain_added": True, "flags_off_behaviour_identical": True,
}
#: REPORTED by the cycle (not recomputable by a test): the independent review and its mutation proof.
REVIEW = {"reviewer": "independent, read-only, adversarial (19 probes of its own)", "high": 1, "medium": 2, "low": 5,
          "high_and_medium_reproduced_with_an_own_probe_and_repaired": ["HIGH-1 an artifact that cannot be built after the first commit read as a continuable precommit abort",
                                                                       "MEDIUM-1 a trigger coalesced with the failing submission was handled by the session that had just stopped",
                                                                       "MEDIUM-2 removing the authority configuration mid-encounter let the clock route continue on the legacy engine"],
          "low_repaired": ["LOW-3 the durable match parsed every stored file", "LOW-4 the failing run drew no stop notice", "LOW-7 (part) the window and the artifact error have their own stop classes; the notice names how to leave"],
          "low_declared_not_repaired": ["LOW-5 the pressure shown after the stop is the legacy value of the failing turn", "LOW-6 a healthy turn recovered by Phase 0 stops with RESUMED_WITHOUT_SITE (availability only)",
                                        "LOW-7 (rest) two classification choices; an older build that re-saves the payload drops the new key"],
          "mutants_of_the_mechanisms": 34, "mutants_killed": 33, "mutants_equivalent_declared": 1,
          "equivalent_mutant": "the minute-zero belongs-check of a record is unreachable for a verified record (an authority record always has a last authoritative minute, and the minute test catches minute zero)"}


def build_record() -> dict:
    series = json.loads(SERIES_PATH.read_text(encoding="utf-8"))
    previous = json.loads(PREVIOUS_PATH.read_text(encoding="utf-8"))
    classes = Counter(se.OPERATIONS.values())
    body = {
        "record_type": "PHASE3_EFFECTIVE_STOP_CHECKPOINT", "version": VERSION, "decided_on": "2026-11-12",
        "from_the_code": {
            "lifecycle": list(se.LIFECYCLE), "transitions": {state: list(targets) for state, targets in se.TRANSITIONS.items()}, "stopped_states": list(se.STOPPED_STATES),
            "operation_classes": list(se.OPERATION_CLASSES), "operations_per_class": {name: classes[name] for name in se.OPERATION_CLASSES},
            "survives_a_stop": sorted(name for name, kind in se.OPERATIONS.items() if kind in (se.READ_ONLY, se.LEAVES_THE_SESSION)),
            "stop_classes": sorted(value for name, value in vars(se).items() if name.startswith("STOP_") and isinstance(value, str)),
            "operator_resolutions": list(se.OPERATOR_RESOLUTIONS), "future_operator_resolutions": list(se.FUTURE_OPERATOR_RESOLUTIONS),
            "notice_headline": se.NOTICE_HEADLINE, "notice_forbidden_words": list(se.FORBIDDEN_NOTICE_WORDS), "notice_is_operational": se.notice_is_operational(se.NOTICE_HEADLINE + " " + se.NOTICE_BODY),
            "session_key": se.SESSION_KEY, "session_key_travels_with_a_saved_encounter": se.SESSION_KEY in SESSION_FIELDS,
            "site_and_artifact_travel_with_a_saved_encounter": [key for key in (ra.SITE_KEY, ra.ARTIFACT_KEY) if key in SESSION_FIELDS],
            "persistence_failure_halt_reason": ra.ARTIFACT_PERSISTENCE_FAILED, "resumed_without_site_halt_reason": ra.RESUMED_WITHOUT_SITE,
            "grant_id": grants.GRANT_ID, "grant_fingerprint_is_pinned": grants.GRANT_FINGERPRINT == grants.GRANT["fingerprint"], "grant_window_minutes": grants.WINDOW_MINUTES,
            "grant_excluded_domains": list(grants.EXCLUDED_DOMAINS), "authority_domain": list(ra.AUTHORITY_DOMAIN), "authority_cases": sorted(ra.AUTHORITY_CASES),
            "common_core_runtime_authority": rs.COMMON_CORE_RUNTIME_AUTHORITY, "approved_authority_snapshots": sorted(ra.APPROVED_SNAPSHOTS),
        },
        "pinned_records": {"pressure_series": {"record": "docs/revision/PHASE3_PRESSURE_AUTHORITY_SERIES.json", "record_digest": series["record_digest"], "runs": series["summary"]["runs"],
                                              "stopped_runs": sorted(f"{row['case']}/{row['scenario']}" for row in series["runs"] if row.get("blocked_steps"))},
                           "previous_checkpoint": {"record": "docs/revision/PHASE3_PRESSURE_CHECKPOINT.json", "record_digest": previous["record_digest"],
                                                   "post_commit_status_then": previous["statuses"]["POST_COMMIT_HARD_FAIL"]}},
        "supersedes_the_previous_checkpoint_on": ["POST_COMMIT_HARD_FAIL: INVALID_FOR_CONTINUATION was advisory to the encounter", "the resumed encounter was marked, not prevented"],
        "reported": {"review": dict(REVIEW)},
        "statuses": dict(STATUSES), "verdict": VERDICT, "verdict_enables": VERDICT_ENABLES, "remaining_blockers": list(REMAINING_BLOCKERS), "confirmations": dict(CONFIRMATIONS),
        "statement": "A technical checkpoint of a development experiment. It is not a clinical validation, an approval of version 1, a consciousness authority, a resident deployment or a production authority.",
    }
    return {**body, "record_digest": ra.digest_of(body)}


def test_k1_the_checkpoint_record_is_what_the_code_and_the_other_records_say_now():
    if os.environ.get("MRS_WRITE_STOP_CHECKPOINT") == "1":
        RECORD_PATH.write_text(json.dumps(build_record(), indent=1, sort_keys=True), encoding="utf-8")
    assert RECORD_PATH.exists(), "the record is produced once and committed"
    stored, live = json.loads(RECORD_PATH.read_text(encoding="utf-8")), build_record()
    assert stored == json.loads(json.dumps(live)), "the committed checkpoint no longer matches the code: regenerate it deliberately"


def test_k2_the_record_says_what_it_must_and_claims_nothing_it_may_not():
    record = json.loads(RECORD_PATH.read_text(encoding="utf-8"))
    code = record["from_the_code"]
    assert code["lifecycle"] == ["NOT_STARTED", "PREAUTHORITY", "ACTIVE_AUTHORITY", "PRECOMMIT_ABORT", "INVALID_FOR_CONTINUATION", "COMPLETED_AUTHORITY"]
    assert code["stopped_states"] == ["INVALID_FOR_CONTINUATION"] and code["transitions"]["INVALID_FOR_CONTINUATION"] == ["INVALID_FOR_CONTINUATION"]
    assert "ACTIVE_AUTHORITY" not in code["transitions"]["INVALID_FOR_CONTINUATION"] and "ACTIVE_AUTHORITY" not in code["transitions"]["PRECOMMIT_ABORT"]
    assert set(code["operation_classes"]) == {"READ_ONLY", "ENCOUNTER_MUTATING", "CLINICAL_TIME_ADVANCING", "LEAVES_THE_SESSION"}
    assert not {"history_question", "order_submission", "examination", "held_order_release", "ecg_acquisition", "complete_encounter"} & set(code["survives_a_stop"])
    assert {"reset_scenario", "abandon_experiment", "return_to_dashboard"} <= set(code["survives_a_stop"])
    assert code["operator_resolutions"] == ["ABANDON_EXPERIMENT"] and code["notice_is_operational"] is True
    assert code["session_key_travels_with_a_saved_encounter"] is True and code["site_and_artifact_travel_with_a_saved_encounter"] == []
    assert code["common_core_runtime_authority"] is False and code["approved_authority_snapshots"] == ["gi_pressure_committed"]
    assert code["authority_domain"] == ["sbp", "dbp", "map"] and code["authority_cases"] == ["gi_bleed_57m", "gi_bleed_72f"]
    assert {"consciousness", "mental_status", "collapse", "terminal", "pulse", "oxygenation", "lactate", "hb"} == set(code["grant_excluded_domains"])
    assert code["grant_fingerprint_is_pinned"] is True and code["grant_window_minutes"] == 240
    assert set(record["statuses"]) == {"PRESSURE_AUTHORITY_VALIDATION", "POST_COMMIT_STOP", "RESTART_PERSISTENCE", "PAGE_CONTINUATION_GUARD", "COLLAPSE_BOUNDARY_STOP",
                                       "ARTIFACT_SESSION_CONSISTENCY", "SINGLE_PROCESS_CONCURRENCY", "RESIDENT_ISOLATION"}
    assert record["verdict"] in ("A_GI_PRESSURE_DEVELOPMENT_AUTHORITY_WITH_EFFECTIVE_STOP_VALIDATED", "B_AUTHORITY_VALID_BUT_CONTINUATION_STOP_INCOMPLETE",
                                 "C_SESSION_PERSISTENCE_OR_CONCURRENCY_BLOCKER", "D_AUTHORITY_RUNTIME_NEEDS_REDESIGN") and record["verdict"] == VERDICT
    assert record["verdict_enables"].startswith("NOTHING BEYOND") and "not taken here" in record["verdict_enables"]
    assert all(record["confirmations"].values()) and len(record["confirmations"]) == 15
    text = json.dumps(record).lower()
    for forbidden in ("clinically validated", "consciousness authority granted", "approved for authority", "resident approved", "production approved", "deployed to residents"):
        assert forbidden not in text, forbidden
    assert "GI_DEVELOPMENT_SNAPSHOT" not in json.dumps(record), "the stop record never names the consciousness snapshot"
    assert len(record["remaining_blockers"]) == 8 and record["remaining_blockers"][0].startswith("the turn that fails has already run")
    review = record["reported"]["review"]
    assert (review["high"], review["medium"], review["low"]) == (1, 2, 5) and len(review["high_and_medium_reproduced_with_an_own_probe_and_repaired"]) == 3
    assert review["mutants_of_the_mechanisms"] == 34 and review["mutants_killed"] == 33 and review["mutants_equivalent_declared"] == 1
    assert review["mutants_killed"] + review["mutants_equivalent_declared"] == review["mutants_of_the_mechanisms"]


def test_k3_the_previous_checkpoint_is_not_rewritten_it_is_superseded_on_the_stop_only():
    """A record is what was decided then. The P3-249 checkpoint still says the stop was advisory (that was true then); this checkpoint names exactly what it supersedes."""
    previous = json.loads(PREVIOUS_PATH.read_text(encoding="utf-8"))
    assert previous["statuses"]["POST_COMMIT_HARD_FAIL"].startswith("INVALID_FOR_CONTINUATION_DECLARED_NOT_SILENT_BUT_ADVISORY")
    assert previous["remaining_blockers"][0].startswith("INVALID_FOR_CONTINUATION is advisory to the encounter")
    record = json.loads(RECORD_PATH.read_text(encoding="utf-8"))
    assert len(record["supersedes_the_previous_checkpoint_on"]) == 2 and record["pinned_records"]["previous_checkpoint"]["record_digest"] == previous["record_digest"]
    assert previous["verdict"].startswith("A_") and record["verdict"].startswith(("A_", "B_", "C_", "D_"))


def test_k4_the_series_rows_of_the_stopped_sessions_are_the_only_rows_the_stop_changed():
    record = json.loads(RECORD_PATH.read_text(encoding="utf-8"))
    series = json.loads(SERIES_PATH.read_text(encoding="utf-8"))
    stopped = [row for row in series["runs"] if row.get("blocked_steps")]
    assert record["pinned_records"]["pressure_series"]["stopped_runs"] == sorted(f"{row['case']}/{row['scenario']}" for row in stopped)
    assert stopped and all(row["halted"] and row["committed_minutes"] for row in stopped), "only sessions that halted AFTER a real commit are stopped"
    assert not [row for row in series["runs"] if row.get("blocked_steps") and not row["halted"]]
