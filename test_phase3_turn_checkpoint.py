"""P3-278: the checkpoint record of the AUTHORITY-CONTROLLED TURN and the DURABLE PROVENANCE ANCHOR of the GI development pressure authority experiment, rebuilt from the code and the other records.

TEST-SIDE. ``docs/revision/PHASE3_TURN_CHECKPOINT.json`` states what the repository can and cannot do at this checkpoint. Everything the code can say is READ FROM THE CODE (the turn's ownership
table and its verdict vocabulary, the anchor's type and states, the stop classes, the routes that run inside a turn, the flags that stay off, the pinned grant, the pinned records); the eight
statuses, the ONE verdict, the confirmations and the blockers are the checkpoint's own decision, pinned here as literals. The review and mutation figures are REPORTED (a mutation run and a
reviewer's tally cannot be recomputed by a test) and are kept apart from what the code says. The certification figures (the tree fingerprint, the suite counts) are NOT in this record: a record cannot
contain the fingerprint of the tree that includes it, so the final report states them.

This record SUPERSEDES, for the failed turn and for the lost-state edge only, two blockers of the P3-264 checkpoint (``PHASE3_EFFECTIVE_STOP_CHECKPOINT.json``): that the turn that fails has
already run on the legacy engine, and that a saved encounter that lost both its record and its site while the legacy engine advanced is not recognised. It does not rewrite that record (a record
is what was decided then); a test here pins that it still says so. Nothing in this record is a clinical validation, an approval of version 1, a consciousness authority, a resident deployment, a
production authority or a faculty-pilot start, and a test refuses a record that says otherwise. ``MRS_WRITE_TURN_CHECKPOINT=1`` regenerates it, once, by the person who changes the checkpoint.
"""
import json
import os
from collections import Counter
from pathlib import Path

import runtime_authority as ra
import runtime_authority_session as se
import runtime_authority_turn as tu
import runtime_pressure_grant as grants
import runtime_shadow as rs
from curriculum_runtime import SESSION_FIELDS

ROOT = Path(__file__).resolve().parent
RECORD_PATH = ROOT / "docs" / "revision" / "PHASE3_TURN_CHECKPOINT.json"
PREVIOUS_PATH = ROOT / "docs" / "revision" / "PHASE3_EFFECTIVE_STOP_CHECKPOINT.json"
SERIES_PATH = ROOT / "docs" / "revision" / "PHASE3_PRESSURE_AUTHORITY_SERIES.json"
VERSION = "P3-278"

#: The checkpoint's decision. Eight statuses, ONE verdict, and what the verdict does NOT do.
STATUSES = {
    "FAILED_TURN_MUTATION_PREVENTION": "AFTER_THE_FIRST_REAL_COMMIT_A_TURN_THE_AUTHORITY_REFUSES_NEVER_HAPPENS_TO_THE_REAL_ENCOUNTER_COPY_EXECUTE_JUDGE_APPLY_OR_DISCARD_A_TURN_NOBODY_JUDGED_IS_NOT_APPLIED_BEFORE_THE_FIRST_COMMIT_THE_LEGACY_TURN_STANDS_BY_DESIGN",
    "AUTHORITY_PROVENANCE_DURABILITY": "EVERY_REAL_COMMIT_WRITES_A_MONOTONIC_DIGEST_SEALED_ANCHOR_INTO_THE_PATIENT_STATE_THE_ENCOUNTER_CARRIES_ITS_OWN_PROVENANCE_AN_UNSIGNED_MARK_IS_A_DECLARED_LIMIT",
    "RESTART_FAIL_CLOSED": "REFRESH_REOPEN_A_NEW_SESSION_AND_THE_FLAGS_REMOVED_ARE_STOPS_EVERY_COMBINATION_OF_A_LOST_RECORD_A_LOST_SITE_A_LOST_ARTIFACT_AND_A_LEGACY_CLOCK_THAT_RAN_ON_IS_A_STOP_A_DELETED_ANCHOR_WITH_A_LIVE_CLAIM_IS_A_STOP",
    "POST_COMMIT_STOP": "UNCHANGED_AND_NOW_THE_FAILING_TURN_ITSELF_NEVER_REACHES_THE_REAL_ENCOUNTER_INVALID_FOR_CONTINUATION_BLOCKS_CLINICAL_TIME_AND_MANAGEMENT_ACTIONS_NO_SILENT_LEGACY_FALLBACK",
    "PRESSURE_AUTHORITY": "GI_PRESSURE_DEVELOPMENT_AUTHORITY_UNCHANGED_SBP_DBP_MAP_TWO_CASES_BEHIND_THE_EXPLICIT_GRANT_THE_TENTH_GATE_CONDITION_THE_SERIES_ROWS_OF_REFUSED_TURNS_NOW_SHOW_THE_LAST_AUTHORITATIVE_PRESSURE",
    "PAGE_RUNTIME": "EVERY_ROUTE_THAT_CAN_MOVE_THE_CLOCK_RUNS_INSIDE_AN_AUTHORITY_TURN_A_TRIPWIRE_FAILS_ON_A_NEW_ONE_A_STALE_TURN_IS_CLOSED_AT_THE_START_OF_THE_NEXT_RUN_ECG_CANCEL_AND_EXPLANATION_ARE_BLOCKED_AFTER_A_STOP_NOT_JUDGED",
    "RESIDENT_ISOLATION": "FLAGS_OFF_BEHAVIOUR_IDENTICAL_NO_TURN_NO_ANCHOR_NO_AUTHORITY_KEY_WITH_THE_FLAGS_OFF_NO_RESIDENT_FACING_CLINICAL_TEXT_NO_COMMON_CONSCIOUSNESS_VISIBLE_THE_FIRST_PILOT_AND_OTHER_FAMILIES_UNTOUCHED_NOT_READY_FOR_RESIDENTS",
    "SINGLE_PROCESS_DEVELOPMENT_SAFETY": "SINGLE_PROCESS_SESSION_SAFETY_SUFFICIENT_FOR_DEVELOPMENT_NO_MUTABLE_MODULE_STATE_IN_THE_NEW_LAYER_SEVERAL_PROCESSES_SHARE_ONLY_THE_DURABLE_STORE",
}
VERDICT = "A_GI_PRESSURE_AUTHORITY_READY_FOR_CONTROLLED_FACULTY_ENVIRONMENT_REVIEW"
VERDICT_ENABLES = ("NOTHING BEYOND the GI pressure development authority the faculty already granted, now with an authority-controlled turn and a durable provenance anchor (SBP, DBP, MAP derived; "
                   "gi_bleed_57m and gi_bleed_72f; the development environment): it makes the experiment ELIGIBLE FOR A FACULTY REVIEW of a controlled faculty-only environment. It does NOT start a faculty pilot, "
                   "does not make the experiment ready for residents, and grants no consciousness authority, no write into mental_status, no production use, no first-pilot change and no approval of version 1 "
                   "for authority. That review is not taken here")
REMAINING_BLOCKERS = (
    "the session record and the provenance anchor are unsigned: whoever recomputes the digest is not refuted from the record alone (the live site and the artifact still win when they exist); a signature needs a key, a faculty decision",
    "an encounter reconstructed with NO anchor, NO record, NO site and NO reachable artifact is not recognisable (flags off); with the flags on and the durable store the case/minute/pressure match only works while the legacy engine has not advanced",
    "ECG acquisition, cancelling pending actions and the retrospective explanation neither move the clock nor the pressure, so the authority does not judge them and they are not transactional; after a stop they are blocked",
    "the shadow session keeps in memory the observation of the refused turn (never persisted, never shown): it is the evidence of the refusal, and it is not rolled back",
    "one Python process; the only operator resolution is to leave the session; the stop notice is development-only English text; two GI cases for development only; the common consciousness stays unmapped; V1 is ratified for development experiments only",
)
CONFIRMATIONS = {
    "gi_pressure_authority_only": True, "no_consciousness_authority": True, "no_resident_deployment": True, "first_pilot_unchanged": True, "scoring_unchanged": True,
    "no_terminal_semantics": True, "no_physiology_retuned": True, "no_clinical_validation_claim": True, "common_core_runtime_authority_remains_false": True,
    "legacy_mental_status_unchanged": True, "no_common_consciousness_visible_to_residents": True, "no_production_authority": True, "v1_not_promoted_to_authority": True,
    "no_authority_domain_added": True, "no_faculty_pilot_started": True, "flags_off_behaviour_identical": True, "no_second_engine": True, "no_rollback_after_mutation": True,
}
#: REPORTED by the cycle (not recomputable by a test): the independent review of the turn and the mutation proof of its repairs. The reviewer's own per-attack table is in the cycle's working record.
REVIEW = {"reviewer": "independent, read-only, adversarial, on its own copy of the candidate", "high": 1, "medium": 2, "low": 3,
          "high_and_medium_reproduced_with_an_own_probe_before_any_repair_and_repaired": [
              "HIGH H1 a clock turn the authority never judged was applied (the shadow flag removed from the process: the real clock went 7 to 9, nothing committed, nothing recorded, the session went on)",
              "MEDIUM M1 an encounter whose provenance anchor was deleted while its site, record and artifact were alive was allowed to continue",
              "MEDIUM M2 a zero-minute turn that the store could not write stayed listed in the artifact as a turn the encounter never had"],
          "low_repaired": ["L1 the layer's docstring claimed no durable write happens inside the scope", "L2 a turn left open by an earlier page run made every later turn run untransacted",
                           "L3 two page assertions were vacuous (an or-clause that was always true)"],
          "routes_found_without_a_page_test_of_their_own_and_now_covered": ["the history topic", "the clock turn the site never saw", "an anchor deleted with a live site", "a refused zero-minute turn under a persistence failure",
                                                                         "a durable zero-minute turn when a later write fails", "a turn left open by an earlier run"],
          "mutants_of_the_mechanisms": 65, "mutants_killed": 61, "mutants_equivalent_declared": 4,
          "equivalent_mutants": ["P1, P1b, P2 (three redundant unwinding points: the context's own exit applies the same verdict and the same stop)",
                                 "L2b (a non-turn object left in the turn slot reaches _apply, which does not exist, and the exception branch discards it anyway)"]}


def _routes_in_a_turn() -> list:
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    import re
    return sorted(set(re.findall(r"_authority_turn\(\"([a-z_]+)\"\)", source)))


def build_record() -> dict:
    series = json.loads(SERIES_PATH.read_text(encoding="utf-8"))
    previous = json.loads(PREVIOUS_PATH.read_text(encoding="utf-8"))
    classes = Counter(name for name, fields in tu.OWNERSHIP.items() for _ in fields)
    body = {
        "record_type": "PHASE3_TURN_CHECKPOINT", "version": VERSION, "decided_on": "2026-11-13",
        "from_the_code": {
            "turn_layer_version": tu.VERSION, "turn_key": tu.TURN_KEY, "turn_verdicts": [tu.COMMIT, tu.DISCARD],
            "ownership_classes": {name: list(fields) for name, fields in tu.OWNERSHIP.items()}, "ownership_class_sizes": {name: classes[name] for name in tu.OWNERSHIP},
            "ownership_partitions_the_saved_session_fields": tu.ownership_problems(SESSION_FIELDS) == [],
            "routes_that_run_inside_an_authority_turn": _routes_in_a_turn(),
            "unjudged_turn_halt_reason": ra.TURN_NOT_JUDGED, "persistence_failure_halt_reason": ra.ARTIFACT_PERSISTENCE_FAILED,
            "anchor_key": ra.PROVENANCE_ANCHOR_KEY, "anchor_type": se.ANCHOR_TYPE, "anchor_version": se.ANCHOR_VERSION, "anchor_state": se.STATE_AUTHORITY_OCCURRED,
            "anchor_halt_reasons": [ra.PROVENANCE_ANCHOR_INVALID, ra.PROVENANCE_LOST],
            "lifecycle": list(se.LIFECYCLE), "stopped_states": list(se.STOPPED_STATES),
            "stop_classes": sorted(value for name, value in vars(se).items() if name.startswith("STOP_") and isinstance(value, str)),
            "session_key": se.SESSION_KEY, "session_key_travels_with_a_saved_encounter": se.SESSION_KEY in SESSION_FIELDS,
            "grant_id": grants.GRANT_ID, "grant_fingerprint_is_pinned": grants.GRANT_FINGERPRINT == grants.GRANT["fingerprint"], "grant_window_minutes": grants.WINDOW_MINUTES,
            "grant_excluded_domains": list(grants.EXCLUDED_DOMAINS), "authority_domain": list(ra.AUTHORITY_DOMAIN), "authority_cases": sorted(ra.AUTHORITY_CASES),
            "common_core_runtime_authority": rs.COMMON_CORE_RUNTIME_AUTHORITY, "approved_authority_snapshots": sorted(ra.APPROVED_SNAPSHOTS),
        },
        "pinned_records": {"pressure_series": {"record": "docs/revision/PHASE3_PRESSURE_AUTHORITY_SERIES.json", "record_digest": series["record_digest"], "runs": series["summary"]["runs"]},
                           "previous_checkpoint": {"record": "docs/revision/PHASE3_EFFECTIVE_STOP_CHECKPOINT.json", "record_digest": previous["record_digest"],
                                                   "verdict_then": previous["verdict"], "blockers_then": len(previous["remaining_blockers"])}},
        "supersedes_the_previous_checkpoint_on": ["blocker 1: the turn that fails has already run on the legacy engine when the site judges it",
                                                  "blocker 3: a saved encounter that lost both its record and its site while the legacy engine advanced is not recognised"],
        "reported": {"review": dict(REVIEW)},
        "statuses": dict(STATUSES), "verdict": VERDICT, "verdict_enables": VERDICT_ENABLES, "remaining_blockers": list(REMAINING_BLOCKERS), "confirmations": dict(CONFIRMATIONS),
        "statement": "A technical checkpoint of a development experiment. It is not a clinical validation, an approval of version 1, a consciousness authority, a resident deployment, a production authority or the start of a faculty pilot.",
    }
    return {**body, "record_digest": ra.digest_of(body)}


def test_c1_the_checkpoint_record_is_what_the_code_and_the_other_records_say_now():
    if os.environ.get("MRS_WRITE_TURN_CHECKPOINT") == "1":
        RECORD_PATH.write_text(json.dumps(build_record(), indent=1, sort_keys=True), encoding="utf-8")
    assert RECORD_PATH.exists(), "the record is produced once and committed"
    stored, live = json.loads(RECORD_PATH.read_text(encoding="utf-8")), build_record()
    assert stored == json.loads(json.dumps(live)), "the committed checkpoint no longer matches the code: regenerate it deliberately"


def test_c2_the_record_says_what_it_must_and_claims_nothing_it_may_not():
    record = json.loads(RECORD_PATH.read_text(encoding="utf-8"))
    code = record["from_the_code"]
    assert code["turn_verdicts"] == ["COMMIT", "DISCARD"] and code["ownership_partitions_the_saved_session_fields"] is True
    assert set(code["ownership_classes"]) == {"TURN_OWNED", "OPERATIONAL", "EXTERNAL_ACCOUNTING", "AUTHORITY_RECORD", "CLOSED_OR_REVIEW"}
    assert "ai_call_ledger" in code["ownership_classes"]["EXTERNAL_ACCOUNTING"] and "ai_call_ledger" not in code["ownership_classes"]["TURN_OWNED"], "paid calls that happened are never restored"
    assert {"state", "events", "management_trace", "order_ledger"} <= set(code["ownership_classes"]["TURN_OWNED"])
    assert code["routes_that_run_inside_an_authority_turn"] == ["examination", "history_question", "history_topic", "order_turn"]
    assert code["anchor_state"] == "AUTHORITY_OCCURRED" and code["anchor_key"] == "phase3_authority_anchor" and "AUTHORITY_PROVENANCE" in code["stop_classes"]
    assert code["unjudged_turn_halt_reason"] == "AUTHORITY_TURN_NOT_JUDGED"
    assert code["lifecycle"] == ["NOT_STARTED", "PREAUTHORITY", "ACTIVE_AUTHORITY", "PRECOMMIT_ABORT", "INVALID_FOR_CONTINUATION", "COMPLETED_AUTHORITY"] and code["stopped_states"] == ["INVALID_FOR_CONTINUATION"]
    assert code["session_key_travels_with_a_saved_encounter"] is True
    assert code["common_core_runtime_authority"] is False and code["approved_authority_snapshots"] == ["gi_pressure_committed"]
    assert code["authority_domain"] == ["sbp", "dbp", "map"] and code["authority_cases"] == ["gi_bleed_57m", "gi_bleed_72f"]
    assert {"consciousness", "mental_status", "collapse", "terminal", "pulse", "oxygenation", "lactate", "hb"} == set(code["grant_excluded_domains"])
    assert code["grant_fingerprint_is_pinned"] is True and code["grant_window_minutes"] == 240
    assert set(record["statuses"]) == {"FAILED_TURN_MUTATION_PREVENTION", "AUTHORITY_PROVENANCE_DURABILITY", "RESTART_FAIL_CLOSED", "POST_COMMIT_STOP", "PRESSURE_AUTHORITY", "PAGE_RUNTIME",
                                       "RESIDENT_ISOLATION", "SINGLE_PROCESS_DEVELOPMENT_SAFETY"} and len(record["statuses"]) == 8
    assert record["verdict"] == VERDICT and record["verdict"][:2] in ("A_", "B_", "C_", "D_")
    assert record["verdict_enables"].startswith("NOTHING BEYOND") and "does NOT start a faculty pilot" in record["verdict_enables"] and "not taken here" in record["verdict_enables"]
    assert all(record["confirmations"].values()) and len(record["confirmations"]) == 18
    text = json.dumps(record).lower()
    for forbidden in ("clinically validated", "consciousness authority granted", "approved for authority", "resident approved", "production approved", "deployed to residents", "pilot started"):
        assert forbidden not in text, forbidden
    assert "GI_DEVELOPMENT_SNAPSHOT" not in json.dumps(record), "the turn record never names the consciousness snapshot"
    assert len(record["remaining_blockers"]) == 5 and record["remaining_blockers"][0].startswith("the session record and the provenance anchor are unsigned")
    review = record["reported"]["review"]
    assert (review["high"], review["medium"], review["low"]) == (1, 2, 3) and len(review["high_and_medium_reproduced_with_an_own_probe_before_any_repair_and_repaired"]) == 3
    assert review["mutants_of_the_mechanisms"] == 65 and review["mutants_killed"] == 61 and review["mutants_equivalent_declared"] == 4
    assert review["mutants_killed"] + review["mutants_equivalent_declared"] == review["mutants_of_the_mechanisms"]


def test_c3_the_previous_checkpoint_is_not_rewritten_it_is_superseded_on_two_blockers_only():
    """A record is what was decided then. The P3-264 checkpoint still lists the failed turn and the lost-state edge as blockers (true then); this checkpoint names exactly what it supersedes."""
    previous = json.loads(PREVIOUS_PATH.read_text(encoding="utf-8"))
    assert previous["remaining_blockers"][0].startswith("the turn that fails has already run on the legacy engine")
    assert previous["remaining_blockers"][2].startswith("a saved encounter that lost BOTH its record and its site")
    record = json.loads(RECORD_PATH.read_text(encoding="utf-8"))
    assert len(record["supersedes_the_previous_checkpoint_on"]) == 2 and record["pinned_records"]["previous_checkpoint"]["record_digest"] == previous["record_digest"]
    assert previous["verdict"].startswith("A_") and record["verdict"].startswith("A_")


def test_c4_the_series_this_checkpoint_pins_is_the_one_the_stop_checkpoint_pins():
    """One series, two checkpoints: regenerating the series without regenerating both checkpoints fails here and in the stop checkpoint."""
    record = json.loads(RECORD_PATH.read_text(encoding="utf-8"))
    stop = json.loads(PREVIOUS_PATH.read_text(encoding="utf-8"))
    series = json.loads(SERIES_PATH.read_text(encoding="utf-8"))
    assert record["pinned_records"]["pressure_series"]["record_digest"] == stop["pinned_records"]["pressure_series"]["record_digest"] == series["record_digest"]
    assert record["pinned_records"]["pressure_series"]["runs"] == series["summary"]["runs"] == 26
