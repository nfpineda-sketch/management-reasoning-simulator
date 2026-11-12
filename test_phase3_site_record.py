"""P3-237: the checkpoint record of the dormant GI authority site, rebuilt from the code and the other records.

TEST-SIDE. ``docs/revision/PHASE3_DORMANT_SITE_CHECKPOINT.json`` states what the repository can and cannot do at this checkpoint. Everything the code can say is READ FROM THE CODE
(the gate's conditions, the empty registry, the faculty's approval constant, the reader audit, the arming of a real site, the states, the pinned digests); the eight statuses and the
verdict are the checkpoint's own decision, pinned here as literals. Nothing in it is an approval, a grant, a clinical validation or an answer to a faculty question, and a test
refuses a record that says otherwise. ``MRS_WRITE_SITE_RECORD=1`` regenerates it, once, by the person who changes the checkpoint.
"""
import json
import os
from collections import Counter
from pathlib import Path

import observable_view as view
import runtime_authority as ra
import runtime_authority_pair as pair
import runtime_pair_site as site_module
import runtime_shadow as rs
import test_gi_reader_guards as guards
import test_phase3_minute_validation as validation_tests
from test_phase3_clock_routes import CASE, bound  # noqa: F401 (fixture)

ROOT = Path(__file__).resolve().parent
RECORD_PATH = ROOT / "docs" / "revision" / "PHASE3_DORMANT_SITE_CHECKPOINT.json"
SERIES_PATH = ROOT / "docs" / "revision" / "PHASE3_DORMANT_SITE_SERIES.json"
VERSION = "P3-237"

#: The checkpoint's decision. Eight statuses, ONE verdict, and what the verdict does NOT do.
STATUSES = {
    "PRESSURE_TECHNICAL_READINESS": "READY_FOR_A_DEVELOPMENT_EXPERIMENT_R2_CLOSED",
    "CONSCIOUSNESS_OVERLAY_TECHNICAL_READINESS": "OVERLAY_ISOLATION_PROVEN_AND_PAIR_CANDIDATE_VALIDATED_AT_EVERY_MINUTE",
    "MENTAL_STATUS_LIVE_AUTHORITY_READINESS": "BLOCKED_BY_NAMED_READERS_AND_NOT_REQUESTED",
    "PAIR_TRANSACTION_READINESS": "DORMANT_SITE_ATOMIC_AND_NOT_ARMED_READY_FOR_A_FACULTY_DECISION",
    "PAGE_RUNTIME_READINESS": "DORMANT_PAGE_ALL_CLOCK_ROUTES_HOOKED_AND_INVISIBLE_PROVEN",
    "SNAPSHOT_BINDING_READINESS": "V1_PINNED_RATIFIED_FOR_DEVELOPMENT_ONLY_AND_BINDING_PROVEN",
    "AUTHORITY_GRANT_READINESS": "GRANT_SCHEMA_AND_GATE_BUILT_NO_GRANT_NOT_GRANTED",
    "FACULTY_CONSCIOUSNESS_READINESS": "NOT_READY",
}
VERDICT = "A_TECHNICAL_INFRASTRUCTURE_READY_FOR_FACULTY_AUTHORITY_DECISION"
VERDICT_ENABLES = "NOTHING: no authority, no grant, no approval of version 1, no write into an encounter, no change of what the resident sees"
REMAINING_BLOCKERS = (
    "C1: the nine divergence episodes of consciousness are unanswered by the faculty (FACULTY_CONSCIOUSNESS_READINESS stays NOT_READY)",
    "the faculty's explicit pair-authority grant does not exist (GRANT_REGISTRY is empty) and the faculty's approval of the domain is NOT_GRANTED",
    "GI_DEVELOPMENT_SNAPSHOT_V1 is not in the authority registry: ratification for development experiments is not an approval",
    "no reader reads the common consciousness: COMMON_VIEW_READERS is empty, and routing any of them is a separate, faculty-requested package",
    "mapping the common word into the live mental_status stays blocked by seven consequential readers and, among them, three engine readers that the Phase-2 closure freezes",
    "the checks and the state machine run in one Python process: no defense against in-process code reaching a module constant or a private attribute",
)
CONFIRMATIONS = {
    "common_core_runtime_authority_remains_false": True, "no_active_authority_grant": True, "v1_not_authority_approved": True, "no_common_state_written_into_a_real_encounter": True,
    "legacy_mental_status_unchanged": True, "resident_ui_unchanged": True, "scoring_unchanged": True, "first_pilot_unchanged": True, "no_terminal_rule_invented": True,
    "no_physiology_retuned": True, "no_clinical_validation_claim": True,
}


def build_record() -> dict:
    guard_mechanisms = Counter(row["mechanism"] for row in guards.READER_GUARDS.values())
    series = json.loads(SERIES_PATH.read_text(encoding="utf-8"))
    body = {
        "record_type": "PHASE3_DORMANT_SITE_CHECKPOINT", "version": VERSION, "decided_on": "2026-11-12",
        "from_the_code": {
            "arming_conditions": list(site_module.ARMING_CONDITIONS), "faculty_conditions": list(site_module.FACULTY_CONDITIONS),
            "grant_registry_is_empty": site_module.GRANT_REGISTRY == (), "faculty_approval": dict(site_module.FACULTY_APPROVAL), "grant_fields": list(site_module.GRANT_FIELDS),
            "states": list(site_module.STATES), "terminal_states": list(site_module.TERMINAL_STATES), "artifact_type": site_module.ARTIFACT_TYPE, "artifact_label": site_module.LABEL,
            "granularity": site_module.GRANULARITY, "time_limit_minutes": pair.TIME_LIMIT_MIN, "validation_modes": ["PRESSURE_ONLY", "PAIR_PRESSURE_CONSCIOUSNESS"],
            "common_core_runtime_authority": rs.COMMON_CORE_RUNTIME_AUTHORITY, "approved_authority_snapshots": sorted(ra.APPROVED_SNAPSHOTS), "v1_in_the_authority_registry": pair.V1_ID in ra.APPROVED_SNAPSHOTS,
            "snapshot": {"id": pair.V1_ID, "version": pair.V1_VERSION, "status": pair.RATIFIED, "record_digest": pair.V1_RECORD_DIGEST, "profile_digest": pair.V1_PROFILE_DIGEST,
                         "core": pair.V1_CORE_VERSION, "core_digest": pair.V1_CORE_DIGEST},
            "reader_audit": {"executable_readers": len(guards.READER_GUARDS), "routed": guard_mechanisms[guards.ROUTED], "reading_frozen_traces": guard_mechanisms["READS_THE_FROZEN_TRACE_WHICH_THE_ROUTED_SNAPSHOTS_KEEP_LEGACY"],
                             "reading_the_live_field": guard_mechanisms[guards.LIVE_FIELD], "no_caller": guard_mechanisms["NO_CALLER"],
                             "unrouted_consequential": len(view.UNROUTED_CONSEQUENTIAL), "frozen_by_the_phase2_closure": len(view.FROZEN_BY_THE_PHASE2_CLOSURE),
                             "readers_of_the_common_view": len(view.COMMON_VIEW_READERS)},
            "pressure_series": {"scenarios": 34, "completed": 26, "stopped": 8, "committed_minutes": 66, "minute_records": 78, "fingerprint": validation_tests.SERIES_FINGERPRINT},
        },
        "dormant_site_series": {"record": "docs/revision/PHASE3_DORMANT_SITE_SERIES.json", "record_digest": series["record_digest"], "runs": len(series["runs"]),
                                "states": dict(Counter(run["technical"]["state"] for run in series["runs"]))},
        "statuses": dict(STATUSES), "verdict": VERDICT, "verdict_enables": VERDICT_ENABLES, "remaining_blockers": list(REMAINING_BLOCKERS), "confirmations": dict(CONFIRMATIONS),
        "statement": "A technical checkpoint. It is not an approval, a grant, a clinical validation or an answer to a faculty question; it enables nothing.",
    }
    return {**body, "record_digest": ra.digest_of(body)}


def test_c1_the_checkpoint_record_is_what_the_code_and_the_other_records_say_now():
    if os.environ.get("MRS_WRITE_SITE_RECORD") == "1":
        RECORD_PATH.write_text(json.dumps(build_record(), indent=1, sort_keys=True), encoding="utf-8")
    assert RECORD_PATH.exists(), "the record is produced once and committed"
    stored, live = json.loads(RECORD_PATH.read_text(encoding="utf-8")), build_record()
    assert stored == json.loads(json.dumps(live)), "the committed checkpoint no longer matches the code: regenerate it deliberately"


def test_c2_the_record_says_what_it_must_and_claims_nothing_it_may_not():
    record = json.loads(RECORD_PATH.read_text(encoding="utf-8"))
    code = record["from_the_code"]
    assert code["common_core_runtime_authority"] is False and code["grant_registry_is_empty"] is True and code["v1_in_the_authority_registry"] is False
    assert code["faculty_approval"] == {"GI_PAIR_AUTHORITY": "NOT_GRANTED"} and code["approved_authority_snapshots"] == ["gi_pressure_committed"]
    assert code["reader_audit"] == {"executable_readers": 32, "routed": 5, "reading_frozen_traces": 13, "reading_the_live_field": 13, "no_caller": 1, "unrouted_consequential": 7,
                                    "frozen_by_the_phase2_closure": 3, "readers_of_the_common_view": 0}
    assert set(record["statuses"]) == {"PRESSURE_TECHNICAL_READINESS", "CONSCIOUSNESS_OVERLAY_TECHNICAL_READINESS", "MENTAL_STATUS_LIVE_AUTHORITY_READINESS", "PAIR_TRANSACTION_READINESS",
                                       "PAGE_RUNTIME_READINESS", "SNAPSHOT_BINDING_READINESS", "AUTHORITY_GRANT_READINESS", "FACULTY_CONSCIOUSNESS_READINESS"}
    assert record["statuses"]["FACULTY_CONSCIOUSNESS_READINESS"] == "NOT_READY" and record["statuses"]["AUTHORITY_GRANT_READINESS"].endswith("NOT_GRANTED")
    assert record["verdict"].startswith("A_") and record["verdict_enables"].startswith("NOTHING") and all(record["confirmations"].values()) and len(record["confirmations"]) == 11
    text = json.dumps(record).lower()
    for forbidden in ("clinically validated", "authority granted", "approved for authority", "resident approved", "production approved"):
        assert forbidden not in text, forbidden
    assert len(record["remaining_blockers"]) == 6 and record["remaining_blockers"][0].startswith("C1")


def test_c3_the_decision_a_real_site_would_get_today_is_not_armed(bound):
    """What the record says about arming is what a real site says: built on the real arrival, every condition read, the faculty's two false."""
    import pilot_acceptance as acceptance
    import runtime_shadow_evidence as ev
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        arrival = acceptance.Encounter(CASE).state
    site = site_module.DormantPairSite(bound, CASE, arrival)
    arming = site.arming({})
    assert arming["armed"] is False and arming["faculty_conditions"] == {name: False for name in site_module.FACULTY_CONDITIONS}
    assert site.state == site_module.NOT_STARTED and site.continuation()["legacy_may_continue_silently"] is True
