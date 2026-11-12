"""P3-249: the checkpoint record of the first real GI development pressure authority experiment, rebuilt from the code and the other records.

TEST-SIDE. ``docs/revision/PHASE3_PRESSURE_CHECKPOINT.json`` states what the repository can and cannot do at this checkpoint. Everything the code can say is READ FROM THE CODE (the
gate's ten conditions, the registered grant and its pinned fingerprint, the approved snapshots, the flag, the excluded domains, the window, the authority label, the pinned records);
the eight statuses, the ONE verdict, the confirmations and the blockers are the checkpoint's own decision, pinned here as literals. The review figures are REPORTED (a mutation run and
a reviewer's tally cannot be recomputed by a test) and are kept apart from what the code says. Nothing in it is a clinical validation, an approval of version 1, a consciousness
authority, a resident deployment or a production authority, and a test refuses a record that says otherwise. ``MRS_WRITE_PRESSURE_CHECKPOINT=1`` regenerates it, once, by the person who
changes the checkpoint.
"""
import json
import os
from pathlib import Path

import runtime_authority as ra
import runtime_authority_pair as pair
import runtime_pressure_grant as grants
import runtime_shadow as rs

ROOT = Path(__file__).resolve().parent
RECORD_PATH = ROOT / "docs" / "revision" / "PHASE3_PRESSURE_CHECKPOINT.json"
SERIES_PATH = ROOT / "docs" / "revision" / "PHASE3_PRESSURE_AUTHORITY_SERIES.json"
DECISIONS_PATH = ROOT / "docs" / "revision" / "PHASE3_PRESSURE_AUTHORITY_DECISIONS.json"
VERSION = "P3-249"

#: The checkpoint's decision. Eight statuses, ONE verdict, and what the verdict does NOT do.
STATUSES = {
    "PRESSURE_REAL_DEVELOPMENT_AUTHORITY": "ACTIVE_FOR_TWO_GI_CASES_PRESSURE_ONLY_DEVELOPMENT_ONLY_BEHIND_AN_EXPLICIT_GRANT_THE_TENTH_GATE_CONDITION",
    "PRESSURE_PAGE_RUNTIME": "REAL_PAGE_26_RUNS_BOTH_CLOCK_ROUTES_COMMON_PRESSURE_COMMITTED_AND_NOTHING_ELSE_CHANGED_FOR_THE_RESIDENT",
    "PRESSURE_REPLAY": "REAL_ARTIFACTS_VERIFY_AND_REPLAY_FROM_THE_ARTIFACT_ALONE_WITH_THE_OVERLAY_THE_BOUNDARY_AND_THE_HALT_REASON",
    "POST_COMMIT_HARD_FAIL": "INVALID_FOR_CONTINUATION_DECLARED_NOT_SILENT_BUT_ADVISORY_TO_THE_ENCOUNTER_AND_A_RESUME_IS_MARKED_NOT_PREVENTED",
    "COLLAPSE_BOUNDARY": "PRECOMMIT_EVERY_MINUTE_FAIL_CLOSED_ESTABLISHED_NOT_IMPENDING_WINDOW_240_NOT_A_TERMINAL_STATE",
    "CONSCIOUSNESS_OVERLAY": "V1_CANDIDATE_OVERLAY_BESIDE_THE_AUTHORITY_RECORDED_NEVER_WRITTEN_NEVER_RESIDENT_VISIBLE",
    "CONSCIOUSNESS_LIVE_AUTHORITY": "NOT_GRANTED_BLOCKED_BY_THE_NAMED_READERS_AND_BY_THE_FACULTY_DECISION_THAT_THE_COMMON_WORD_IS_NOT_RESIDENT_VISIBLE",
    "RESIDENT_PILOT_READINESS": "NOT_READY_DEVELOPMENT_ONLY_THE_HALT_IS_ADVISORY_AND_THE_CHECKS_RUN_IN_ONE_PROCESS",
}
VERDICT = "A_GI_PRESSURE_DEVELOPMENT_AUTHORITY_EXPERIMENT_VALIDATED"
VERDICT_ENABLES = ("NOTHING BEYOND the GI pressure development authority the faculty already granted (SBP, DBP, MAP derived; gi_bleed_57m and gi_bleed_72f; the development environment): "
                   "no consciousness authority, no write into mental_status, no resident deployment, no production use, no first-pilot change, no approval of version 1 for authority")
REMAINING_BLOCKERS = (
    "INVALID_FOR_CONTINUATION is advisory to the encounter: the legacy engine keeps running it. An EFFECTIVE stop needs an interface design this cycle does not build and must not invent as a terminal rule (TD-142 item 4, TD-143 item 1); it blocks any use with residents",
    "mapping the common word into the live mental_status stays blocked: seven consequential readers, three of them engine readers that the Phase-2 closure freezes, and the faculty decision that the common UNRESPONSIVE is not resident-visible (C5)",
    "GI_DEVELOPMENT_SNAPSHOT_V1 stays ratified for development experiments only: it is not in the authority registry and it is not a pressure calibration",
    "the grant, the gate and the checks run in one Python process: no defense against in-process code that reassigns a constant; the defense is the pinned fingerprint, the read-only body, the AST tests and code review (TD-143 item 2)",
    "a resumed encounter has no site (the saved session does not keep it): it is MARKED in the durable store, not prevented, and the legacy engine runs it from there (TD-143 item 5)",
    "two GI cases and an arrival-relative semantics, accepted for development only: no generalization to a population or to another family (FD-AUTH-24)",
    "the artifact store grows with the length of the encounter (one file per turn, the overlay and its replay input in each) and the event provenance reads the committed pressure at the start of a turn: the equality of text and events with the legacy run is proven on the series, not by construction (TD-143 items 3 and 7)",
)
CONFIRMATIONS = {
    "common_core_runtime_authority_remains_false": True, "no_consciousness_authority": True, "legacy_mental_status_unchanged": True, "no_common_consciousness_visible_to_residents": True,
    "no_resident_deployment": True, "no_production_authority": True, "first_pilot_unchanged": True, "v1_not_promoted_to_authority": True, "no_terminal_rule_invented": True,
    "no_physiology_retuned": True, "no_opioid_consciousness_added": True, "no_clinical_validation_claim": True,
}
#: REPORTED by the cycle (not recomputable by a test): the independent review and its mutation proof.
REVIEW = {"reviewer": "independent, read-only, 24 attacks", "high": 0, "medium": 5, "low": 8, "medium_reproduced_with_an_own_probe_and_repaired": 5, "low_repaired": ["L1", "L2", "L3", "L4", "L5", "L6"],
          "low_declared_not_repaired": ["L7", "L8"], "mutants_of_the_repairs": 19, "mutants_killed": 19}


def build_record() -> dict:
    series = json.loads(SERIES_PATH.read_text(encoding="utf-8"))
    decisions = json.loads(DECISIONS_PATH.read_text(encoding="utf-8"))
    body = {
        "record_type": "PHASE3_PRESSURE_CHECKPOINT", "version": VERSION, "decided_on": "2026-11-12",
        "from_the_code": {
            "gate_conditions": list(ra.GATE_CONDITIONS), "tenth_condition": ra.GATE_CONDITIONS[-1],
            "grant": grants.summary(), "grant_fingerprint_is_pinned": grants.GRANT_FINGERPRINT == grants.GRANT["fingerprint"], "grant_window_minutes": grants.WINDOW_MINUTES,
            "grant_excluded_domains": list(grants.EXCLUDED_DOMAINS), "authority_domain": list(ra.AUTHORITY_DOMAIN), "authority_cases": sorted(ra.AUTHORITY_CASES),
            "authority_label": grants.ARTIFACT_LABEL, "overlay_label": grants.OVERLAY_LABEL, "authority_mode": grants.AUTHORITY_MODE,
            "common_core_runtime_authority": rs.COMMON_CORE_RUNTIME_AUTHORITY, "approved_authority_snapshots": sorted(ra.APPROVED_SNAPSHOTS),
            "v1_in_the_authority_registry": pair.V1_ID in ra.APPROVED_SNAPSHOTS, "v1_status": pair.RATIFIED,
            "artifact_classes": [ra.REAL_PRESSURE_LABEL, ra.HISTORICAL_PRESSURE_LABEL, ra.DORMANT_LABEL, ra.INCONSISTENT_ARTIFACT],
            "halt_reasons": [ra.COLLAPSE_BOUNDARY_REACHED, ra.COLLAPSE_BOUNDARY_NOT_VERIFIABLE, ra.WINDOW_CLOSED, ra.UNSUPPORTED_AUTHORITY_ACTION, ra.PROVENANCE_CONTRADICTION, ra.RESUMED_WITHOUT_SITE],
        },
        "decisions": {"record": "docs/revision/PHASE3_PRESSURE_AUTHORITY_DECISIONS.json", "record_digest": decisions["record_digest"]},
        "real_series": {"record": "docs/revision/PHASE3_PRESSURE_AUTHORITY_SERIES.json", "record_digest": series["record_digest"], "runs": series["summary"]["runs"],
                        "committed_minutes": series["summary"]["committed_minutes"], "states": series["summary"]["states"], "halt_kinds": series["summary"]["halt_kinds"],
                        "all_verified": series["summary"]["all_verified"], "all_replay": series["summary"]["all_replay"]},
        "reported": {"review": dict(REVIEW)},
        "statuses": dict(STATUSES), "verdict": VERDICT, "verdict_enables": VERDICT_ENABLES, "remaining_blockers": list(REMAINING_BLOCKERS), "confirmations": dict(CONFIRMATIONS),
        "statement": "A technical checkpoint of a development experiment. It is not a clinical validation, an approval of version 1, a consciousness authority, a resident deployment or a production authority.",
    }
    return {**body, "record_digest": ra.digest_of(body)}


def test_k1_the_checkpoint_record_is_what_the_code_and_the_other_records_say_now():
    if os.environ.get("MRS_WRITE_PRESSURE_CHECKPOINT") == "1":
        RECORD_PATH.write_text(json.dumps(build_record(), indent=1, sort_keys=True), encoding="utf-8")
    assert RECORD_PATH.exists(), "the record is produced once and committed"
    stored, live = json.loads(RECORD_PATH.read_text(encoding="utf-8")), build_record()
    assert stored == json.loads(json.dumps(live)), "the committed checkpoint no longer matches the code: regenerate it deliberately"


def test_k2_the_record_says_what_it_must_and_claims_nothing_it_may_not():
    record = json.loads(RECORD_PATH.read_text(encoding="utf-8"))
    code = record["from_the_code"]
    assert len(code["gate_conditions"]) == 10 and code["tenth_condition"] == "explicit_development_grant"
    assert code["common_core_runtime_authority"] is False and code["v1_in_the_authority_registry"] is False and code["approved_authority_snapshots"] == ["gi_pressure_committed"]
    assert code["authority_domain"] == ["sbp", "dbp", "map"] and code["authority_cases"] == ["gi_bleed_57m", "gi_bleed_72f"] and code["authority_mode"] == "PRESSURE_ONLY"
    assert {"consciousness", "mental_status", "collapse", "terminal", "pulse", "oxygenation", "lactate", "hb"} == set(code["grant_excluded_domains"])
    assert code["grant_fingerprint_is_pinned"] is True and code["grant"]["fingerprint"] == grants.GRANT_FINGERPRINT and code["grant_window_minutes"] == 240
    assert record["real_series"]["runs"] == 26 and record["real_series"]["all_verified"] is True and record["real_series"]["all_replay"] is True
    assert set(record["statuses"]) == {"PRESSURE_REAL_DEVELOPMENT_AUTHORITY", "PRESSURE_PAGE_RUNTIME", "PRESSURE_REPLAY", "POST_COMMIT_HARD_FAIL", "COLLAPSE_BOUNDARY",
                                       "CONSCIOUSNESS_OVERLAY", "CONSCIOUSNESS_LIVE_AUTHORITY", "RESIDENT_PILOT_READINESS"}
    assert record["statuses"]["CONSCIOUSNESS_LIVE_AUTHORITY"].startswith("NOT_GRANTED") and record["statuses"]["RESIDENT_PILOT_READINESS"].startswith("NOT_READY")
    assert record["verdict"].startswith("A_") and record["verdict_enables"].startswith("NOTHING BEYOND") and all(record["confirmations"].values()) and len(record["confirmations"]) == 12
    text = json.dumps(record).lower()
    for forbidden in ("clinically validated", "consciousness authority granted", "approved for authority", "resident approved", "production approved", "deployed to residents"):
        assert forbidden not in text, forbidden
    assert len(record["remaining_blockers"]) == 7 and record["remaining_blockers"][0].startswith("INVALID_FOR_CONTINUATION")
    review = record["reported"]["review"]
    assert (review["high"], review["medium"], review["low"]) == (0, 5, 8) and review["mutants_killed"] == review["mutants_of_the_repairs"] == 19
