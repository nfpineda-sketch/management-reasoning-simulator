"""P3-449 and P3-450: the BUILDER of the records of the manual norepinephrine rate-control ratification (a tool, never imported by a page; it holds no test).

WHAT IT DOES. It turns the human faculty review of ``NOREPINEPHRINE_TITRATION_V1_FACULTY_REVIEW`` into durable, sealed, indexed records and changes NOTHING executable:

* ``PHASE3_HUMAN_NOREPINEPHRINE_TITRATION_REVIEW.json`` -- the HUMAN evidence, exactly as the faculty reported it (provenance ``HUMAN_FACULTY_REVIEW_REPORTED_NOT_STORE_VERIFIED``: the persisted review store is
  not in this container). Only the five overall judgments were reported: the answers Q1 to Q5, the comments, the lock events, the timestamps and the reviewer's identity were NOT, and none is invented;
* ``NOREPINEPHRINE_MANUAL_RATE_CONTROL_DEVELOPMENT_SEMANTICS_V1.json`` -- the closure: the faculty decisions FD-NR-01 to FD-NR-07, the supported operations, the unsupported domains and the durable status
  ``NOREPINEPHRINE_MANUAL_RATE_CONTROL_DEVELOPMENT_SEMANTICS_CLOSED``. It is accepted for DEVELOPMENT semantics only.

Written BEFORE the repair of the target-as-rate defect, so it states that defect as OPEN at the time of the ratification; the repair is recorded by the checkpoint of the cycle, a different file, and this one is
never edited.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import faculty_titration_review as ftt
import faculty_trajectory_review as ftr
import historical_records as hr

ROOT = Path(__file__).resolve().parent
REV = ROOT / "docs" / "revision"
GENERATED_ON = "2026-11-20"
HUMAN_PATH = REV / "PHASE3_HUMAN_NOREPINEPHRINE_TITRATION_REVIEW.json"
CLOSURE_PATH = REV / "NOREPINEPHRINE_MANUAL_RATE_CONTROL_DEVELOPMENT_SEMANTICS_V1.json"
HUMAN_ID = "HUMAN_NOREPINEPHRINE_TITRATION_REVIEW_V1"
CLOSURE_ID = "NOREPINEPHRINE_MANUAL_RATE_CONTROL_DEVELOPMENT_SEMANTICS_V1"
STATUS = "NOREPINEPHRINE_MANUAL_RATE_CONTROL_DEVELOPMENT_SEMANTICS_CLOSED"
WITNESS = "CENTER_REFERENCE"
REPORTED_IN = "the assignment of 2026-11-20 that opened P3-449 ('PHASE 3 — RATIFY MANUAL NOREPINEPHRINE RATE-CONTROL SEMANTICS AND AUDIT TARGET-BASED ORDER PARSING')"
PROVENANCE_CLASS = "HUMAN_FACULTY_REVIEW_REPORTED_NOT_STORE_VERIFIED"

#: What the faculty reported, typed once from the assignment, in the order of the review: only the name of the scenario and the overall judgment.
REPORTED = {
    "TIT-1": {"reported_name": "increase 5 -> 10 mcg/min", "overall": "ACCEPT"},
    "TIT-2": {"reported_name": "decrease 10 -> 4 mcg/min", "overall": "ACCEPT"},
    "TIT-3": {"reported_name": "stop", "overall": "ACCEPT"},
    "TIT-4": {"reported_name": "sequence 5 -> 10 -> 4 -> stop", "overall": "ACCEPT"},
    "TIT-5": {"reported_name": "restart 10 -> stop -> 10", "overall": "ACCEPT"},
}
REPORTED_COUNTS = {"ACCEPT": 5, "ACCEPT_WITH_LIMITATION": 0, "RECALIBRATE": 0, "REJECT": 0}

#: The faculty's decisions, as given (FD-NR-01 to FD-NR-07).
DECISIONS = {
    "FD-NR-01": ("Manual norepinephrine rate-control semantics are accepted for DEVELOPMENT. Supported explicit operations: START, INCREASE, DECREASE, STOP, RESTART, using absolute rates in mcg/min."),
    "FD-NR-02": ("Close further calibration of tone_gain, half_effect_rate_mcg_min, onset_tau_min and offset_tau_min for this manual-rate-control capability. Do NOT reopen LOW, HIGH, the CENTER_REFERENCE selection "
                 "or the common-tone calibration."),
    "FD-NR-03": ("Create a durable development status NOREPINEPHRINE_MANUAL_RATE_CONTROL_DEVELOPMENT_SEMANTICS_CLOSED: accepted for development semantics. It does NOT mean clinical validation, production approval, "
                 "resident approval or live authority expansion."),
    "FD-NR-04": ("Current unsupported domains remain: mcg/kg/min; automatic MAP-target titration; relative commands without a supported active-rate context; consciousness under tone; pump-limited educational "
                 "promotion. None is implemented in this cycle."),
    "FD-NR-05": ("The next safety-critical issue is the inherited parsing defect: 'titrate norepinephrine to MAP 65' may be interpreted as 65 mcg/min. It must be reproduced, traced and fixed before any attempt to make "
                 "shadow consume engine-resolved orders."),
    "FD-NR-06": "No norepinephrine authority expansion is authorized. Current live authority scope remains unchanged.",
    "FD-NR-07": ("Current malformed-order behavior remains provisionally FAIL CLOSED. Recovery semantics are not changed in this package unless needed to repair a demonstrated safety defect; a later explicit valid order "
                 "recovering from a malformed-order boundary is a separate faculty decision."),
}
SUPPORTED_OPERATIONS = ["START", "INCREASE", "DECREASE", "STOP", "RESTART"]
UNSUPPORTED_DOMAINS = {
    "MCG_PER_KG_PER_MIN": "a weight-based dose is never converted to an absolute rate",
    "AUTOMATIC_MAP_TARGET_TITRATION": "no rate is ever chosen from a pressure; there is no controller and no closed loop",
    "RELATIVE_COMMAND_WITHOUT_A_SUPPORTED_ACTIVE_RATE_CONTEXT": "'increase norepinephrine' with no absolute rate and no running infusion is not guessed",
    "CONSCIOUSNESS_UNDER_TONE": "CONSCIOUSNESS_UNDER_TONE_UNRESOLVED stays open (FD-TONE-RATIFY-07)",
    "PUMP_LIMITED_EDUCATIONAL_PROMOTION": "COMMON_TONE_PUMP_DEPENDENCE_NOT_YET_VALIDATED stays a monitored limitation (FD-TONE-RATIFY-05)",
}
CLOSED_CALIBRATION = ["tone_gain", "half_effect_rate_mcg_min", "onset_tau_min", "offset_tau_min"]
NOT_REOPENED = ["LOW", "HIGH", "the CENTER_REFERENCE selection", "the common-tone calibration"]
NOT_GRANTED = ["runtime authority", "a registered adapter", "resident visibility", "scoring", "the first pilot", "a clinical dose-response", "an mmHg target", "automatic titration", "a weight-based dose",
               "any other vasopressor", "consciousness authority", "terminal authority", "clinical validation", "recovery from a malformed-order boundary"]
IS_NOT = ["clinical validation", "production approval", "resident approval", "live authority expansion", "a clinical dose-response", "an approval of norepinephrine in any patient"]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generating_code() -> dict:
    from clinical_core import amendment_3 as a3
    return {"clinical_core": a3.amended_core_digest_now(), "test_nr_manual_ratification_analysis.py": _sha(Path(__file__).resolve()), "faculty_titration_review.py": _sha(ROOT / "faculty_titration_review.py")}


def _file(path: Path) -> dict:
    record = json.loads(path.read_text(encoding="utf-8"))
    return {"file": str(path.relative_to(ROOT)), "record_digest": record.get("record_digest"), "file_sha256": _sha(path)}


def preserved() -> dict:
    """Every earlier record this one rests on, by digest and file hash: preserved, not rewritten."""
    return {"titration_review_set": _file(ftt.SET_PATH), "titration_review_checkpoint": _file(REV / "PHASE3_NOREPINEPHRINE_TITRATION_V1_REVIEW_CHECKPOINT.json"),
            "titration_checkpoint": _file(REV / "PHASE3_NOREPINEPHRINE_TITRATION_CHECKPOINT.json"), "titration_probes": _file(REV / "PHASE3_NOREPINEPHRINE_TITRATION_PROBES.json"),
            "common_tone_snapshot": _file(REV / "COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1.json"), "common_tone_ratification": _file(REV / "COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1_RATIFICATION.json"),
            "titration_review_set_digest_pinned_in_code": ftt.PINNED_SET_DIGEST}


def counts(scenarios: dict) -> dict:
    out = {choice: 0 for choice in ftr.OVERALL}
    for entry in scenarios.values():
        out[entry["overall"]] += 1
    return out


def build_human() -> dict:
    loaded = ftt.load_set()
    if not loaded["ok"]:
        raise ValueError(f"the reviewed set does not verify: {loaded['problems']}")
    if counts(REPORTED) != REPORTED_COUNTS:
        raise ValueError("the reported totals are not the tabulation of the reported judgments")
    scenarios = []
    for scenario_id, _ in ftt.SEQUENCE:
        item, reported = loaded["items"][scenario_id], REPORTED[scenario_id]
        scenarios.append({"scenario_id": scenario_id, "reported_name": reported["reported_name"], "title_in_the_set": item["title"], "overall": reported["overall"],
                          "first_pass_answers_Q1_to_Q5": "NOT_REPORTED", "free_text_comments": "NONE_REPORTED", "recalibration_requested": False, "reviewed_item_digest": ftr.item_digest(item),
                          "reviewed_trajectory_digest": hr.digest_of({"scenario_id": scenario_id, "timeline": item["timeline"], "common": item["common"]})})
    body = {"record_type": "HUMAN_FACULTY_NOREPINEPHRINE_TITRATION_REVIEW_RECORD", "version": "P3-449", "evidence_class": "HUMAN_FACULTY_REVIEW",
            "evidence_classes": {"HUMAN_FACULTY_REVIEW": "what the faculty reviewer judged in the blind review of the CENTER_REFERENCE norepinephrine rate-change trajectories, as reported; only this record and the Decision "
                                                         "File rows FD-NR-01 to FD-NR-07 carry it",
                                 "MODEL_ANALYSIS": "what the development assistant computed or read from the executable model and the certified records; it explains and bounds, it does not judge",
                                 "TEST_RESULT": "what an automated test asserted; it protects a record, it is not a faculty decision"},
            "what_it_is": ("The human faculty review of the five CENTER_REFERENCE norepinephrine rate-change trajectories of one gastrointestinal-hemorrhage case, recorded as HUMAN evidence as the reviewer reported it. "
                           "It is not converted into an automated truth, it is not a clinical validation, and nothing in it was written by a model. No answer, comment, event or timestamp that was not reported was added."),
            "review": {"review_set_id": ftt.SET_ID, "review_set_digest": loaded["digest"], "candidate_reviewed": WITNESS, "candidate_named_by_the_interface": False, "pressure_only_first_pass": True,
                       "scenario_order_as_reported": [scenario_id for scenario_id, _ in ftt.SEQUENCE], "scenarios_with_reported_judgments": len(scenarios), "completion_as_reported": "COMPLETE (5 of 5 judgments reported)",
                       "completion_screen_string": "NOT_REPORTED", "item_digests_note": "computed here from the pinned set (what the review logs carry); the faculty did not report them"},
            "scenarios": scenarios, "overall_counts": dict(REPORTED_COUNTS), "overall_counts_recomputed_from_the_scenarios": counts(REPORTED),
            "provenance_of_the_evidence": {"date_of_record": GENERATED_ON, "verification": PROVENANCE_CLASS, "reported_in": REPORTED_IN, "persisted_store_available_to_the_assistant": False,
                                          "reviewer_identity_recorded": False, "reviewer_name": None, "reviewer_role": "faculty",
                                          "transcribed_by": "the development assistant; the five judgments are typed once from the report and nothing was added",
                                          "why": ("the persisted logs of this review (titration_review/ and titration_reviews/ of the reviewer's own store) are not in this container: the reviewer's store found here holds no records, and "
                                                  "the other titration-review directories found are the assistant's own synthetic test and screenshot sessions, which are NOT human evidence and were not read as such; the assignment asked to "
                                                  "read the store if available and, if not, to use the reported results and mark the provenance, without inventing comments, lock events, timestamps or reviewer identity")},
            "not_verified": ["the answers Q1 to Q5 (not reported)", "the overall judgments against the persisted logs", "the scenario order as persisted", "the completion screen", "the lock and submit events, their order and their timestamps",
                             "free-text comments (none were reported)", "the reviewer's identity"],
            "not_in_this_record": ["the reviewer's name", "any model-written judgment", "any legacy comparison", "any clinical-validation claim", "the per-event logs (they live in the reviewer's own store)"],
            "preserved_original_evidence": preserved()}
    body["provenance"] = hr.provenance(record_id=HUMAN_ID, generating_code=generating_code(), generated_on=GENERATED_ON, source_data={"reported": REPORTED, "counts": REPORTED_COUNTS, "set_digest": loaded["digest"]})
    return hr.seal(body)


def build_closure(human: dict) -> dict:
    snapshot = json.loads((REV / "COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1.json").read_text(encoding="utf-8"))
    body = {"record_type": "NOREPINEPHRINE_MANUAL_RATE_CONTROL_DEVELOPMENT_SEMANTICS_CLOSURE", "version": "P3-450", "closure_id": CLOSURE_ID, "date": GENERATED_ON, "status": STATUS,
            "status_meaning": "accepted for DEVELOPMENT semantics only", "ratified": "MANUAL NOREPINEPHRINE RATE CONTROL (explicit absolute rates in mcg/min, through the common vasoconstrictor-support writer, in the development shadow)",
            "ratified_for": "DEVELOPMENT semantics", "faculty_decisions": dict(DECISIONS), "supported_operations": list(SUPPORTED_OPERATIONS), "supported_unit": "mcg/min",
            "human_record": {"file": str(HUMAN_PATH.relative_to(ROOT)), "record_digest": human["record_digest"], "verification": PROVENANCE_CLASS, "overall_counts": human["overall_counts"]},
            "calibration_closed_for_this_capability": list(CLOSED_CALIBRATION), "not_reopened": list(NOT_REOPENED),
            "bound_to": {"common_tone_snapshot": "COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1", "snapshot_record_digest": snapshot["record_digest"], "selected_witness": WITNESS, "binding_unchanged": snapshot["binding"],
                         "lineage": "PHASE2_AMENDMENT_3", "core_digest": generating_code()["clinical_core"], "review_set_id": ftt.SET_ID, "review_set_digest": ftt.PINNED_SET_DIGEST},
            "unsupported_domains": dict(UNSUPPORTED_DOMAINS), "malformed_order_behavior": {"status": "PROVISIONALLY_FAIL_CLOSED", "decision": "FD-NR-07", "recovery_policy_changed": False,
                                                                                         "recovery_is_a_separate_faculty_decision": True},
            "next_safety_issue_at_the_time_of_ratification": {"id": "TARGET_ORDER_PARSED_AS_RATE", "decision": "FD-NR-05", "status": "OPEN_AT_RATIFICATION",
                                                              "statement": "'titrate norepinephrine to MAP 65' can be interpreted as 65 mcg/min; to be reproduced, traced and fixed before shadow consumes engine-resolved orders",
                                                              "note": "this record is not edited when it is repaired: the repair is recorded by the checkpoint of the cycle"},
            "authority": {"common_core_runtime_authority": False, "expanded": False, "norepinephrine_authority_granted": False, "live_configuration_bound_to_the_snapshot": False, "not_granted": list(NOT_GRANTED)},
            "executable_change": False, "physiology_change": False, "tone_recalibrated": False, "pump_coupling_modified": False, "is_not": list(IS_NOT), "preserved_original_evidence": preserved()}
    body["provenance"] = hr.provenance(record_id=CLOSURE_ID, generating_code=generating_code(), generated_on=GENERATED_ON,
                                       source_data={"human": human["record_digest"], "decisions": DECISIONS, "unsupported": UNSUPPORTED_DOMAINS, "snapshot": snapshot["record_digest"]})
    return hr.seal(body)


def build() -> dict:
    human = build_human()
    return {"human": human, "closure": build_closure(human)}


def write_all() -> dict:
    """Write the two records; ``historical_records.write`` refuses to replace a record with other content."""
    made = build()
    return {str(HUMAN_PATH.relative_to(ROOT)): hr.write(HUMAN_PATH, made["human"]), str(CLOSURE_PATH.relative_to(ROOT)): hr.write(CLOSURE_PATH, made["closure"])}


def reproduce() -> dict:
    """The CONTENT of the two records, regenerated, without provenance or seal: what a test compares with the stored records."""
    return {key: {name: value for name, value in record.items() if name not in ("provenance", "record_digest")} for key, record in build().items()}


if __name__ == "__main__":
    print(json.dumps(write_all(), indent=2))
