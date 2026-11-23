"""P3-555: the CHECKPOINT of the final pre-pilot convergence of the GI management trace (a tool, never imported by a page; it holds no test).

The checkpoint is written ONCE, after the certification, as a sealed, versioned, indexed historical record with exactly ONE of the two outcomes the faculty allowed
(FD-FINALPILOT, P3-555): A, or a TRUE hard blocker that requires a scope expansion. It is a different file from the cycle's tests so that writing it never changes the
generating code those files name. It does not start the pilot.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import gi_pilot as gp
import historical_records as hr

ROOT = Path(__file__).resolve().parent
CHECKPOINT_PATH = ROOT / "docs" / "revision" / "PHASE3_GI_FINAL_PILOT_CHECKPOINT.json"
CHECKPOINT_ID = "GI_FINAL_PILOT_CONVERGENCE_CHECKPOINT_V1"
PRIOR_CHECKPOINT = ROOT / "docs" / "revision" / "PHASE3_GI_PILOT_READINESS_CHECKPOINT.json"
OUTCOMES = {"A": "GI_MANAGEMENT_TRACE_READY_FOR_SMALL_CONTROLLED_RESIDENT_PILOT", "HARD_BLOCKER": "HARD_BLOCKER_REQUIRES_SCOPE_EXPANSION"}
#: The only hard blockers the assignment allows (anything else is an ordinary defect, to be fixed).
ALLOWED_HARD_BLOCKERS = ("NEW_PHYSIOLOGY", "SOURCE_CONTROL_PHYSIOLOGY", "REOPENING_GI_PRESSURE_CALIBRATION", "REOPENING_COMMON_TONE_CALIBRATION", "NEW_PUMP_LIMITED_VASOPRESSOR_PHYSIOLOGY",
                         "NEW_CONSCIOUSNESS_PHYSIOLOGY", "NEW_CLINICAL_FACULTY_JUDGMENT_THAT_CANNOT_BE_CONSERVATIVELY_AVOIDED", "BROADER_GENERIC_ORDER_LANGUAGE_REDESIGN_OUTSIDE_THE_GI_PILOT",
                         "SECURITY_OR_PRIVACY_ISSUE_THAT_CANNOT_BE_SAFELY_MITIGATED")
DECISIONS = "docs/COLA_DECISIONES_AI_ADVISOR.md FD-FINALPILOT-01 to FD-FINALPILOT-10 (2026-11-23); FD-P3-306 to FD-P3-310"
GENERATED_ON = "2026-11-23"
GRANT_ID = "GI_NOREPINEPHRINE_DEVELOPMENT_AUTHORITY_GRANT_V1"

#: P3-553: every PILOT-READY criterion of the assignment, its status and the evidence that decides it (tests on the real page unless named otherwise).
ACCEPTANCE_MATRIX = {
    "A. RESIDENT FLOW": [
        ("the resident can enter gi_bleed_57m (one case, pilot start, no account attempt)", "test_gi_pilot_page::test_p1, test_gi_final_pilot_dryruns::test_dry1"),
        ("sees only the intended clinical information", "test_gi_pilot_page (internals never shown), test_gi_final_pilot_page::test_c10"),
        ("enters complete orders", "test_gi_final_pilot_dryruns::test_dry1, test_dry4"),
        ("enters incomplete orders and receives a clarification", "test_gi_final_pilot_page::test_c1 to test_c5, test_c18"),
        ("completes clarified orders", "test_gi_final_pilot_page::test_c1 to test_c3, test_dry2, test_dry3"),
        ("reassesses and continues the encounter", "test_dry1, test_dry2, test_dry4"),
        ("reaches the development boundary safely", "test_c8, test_c9, test_c21, test_dry1, test_dry6"),
    ],
    "B. AUTHORITY": [
        ("the authority stays attached through clarification-only no-op turns", "test_gi_final_pilot::test_b1, test_b2, test_b14; test_c1 to test_c5"),
        ("real unsafe same-minute mutations still fail closed", "test_gi_final_pilot::test_b4 to test_b9, test_b15; test_c19, test_c23"),
        ("no duplicate minute or sample commit", "test_gi_final_pilot::test_b1, test_b13"),
        ("no silent fallback", "test_c16, test_c22, test_c23, test_gi_pilot_page::test_p10, test_p11"),
        ("no authority drift (configuration, snapshot, grant)", "test_c22, test_c23, test_gi_pilot::test_u1, test_phase3_management_trace::test_d2"),
    ],
    "C. MANAGEMENT TRACE": [
        ("the trace records state, action, clarification, executed order, observed response, reassessment and new state", "test_c14, test_c20, test_dry1 to test_dry4"),
        ("no invented resident reasoning", "test_gi_pilot (participant trace, reasoning only as expressed)"),
        ("the development boundary is explicit", "test_c21, test_dry1, test_dry6"),
        ("replay identical", "test_c14, test_c17, test_dry1 to test_dry4, test_dry7"),
    ],
    "D. SOURCE CONTROL": [
        ("a definitive source-control request cannot reach the inherited haemostasis in the pilot", "test_c8, test_c9, test_c9b, test_gi_final_pilot::test_b17"),
        ("the pilot stops at the development boundary", "test_c8, test_c21, test_dry6"),
    ],
    "E. MENTAL STATUS": [
        ("no misleading tone-related mental-status feedback on the pilot surface", "test_c10, test_gi_pilot (u6 and the mental-status filters)"),
    ],
    "F. FACULTY CONTROLS": [
        ("observe, abort, review the trace, replay, mark unusable and flag an issue", "test_gi_final_pilot_dryruns::test_dry8, test_faculty_dry_run_observe_inspect_replay_flag_unusable_and_no_score"),
    ],
    "G. ISOLATION": [
        ("no scoring consequences", "test_faculty_dry_run_observe_inspect_replay_flag_unusable_and_no_score, test_gi_pilot_page::test_p1"),
        ("no resident access to model internals", "test_gi_pilot_page (INTERNALS), test_c20"),
        ("no snapshot or grant identifier visible", "test_gi_pilot_page (INTERNALS), gi_pilot.FORBIDDEN_ON_PARTICIPANT_TRACE"),
        ("no production authority expansion (development only; COMMON_CORE_RUNTIME_AUTHORITY False)", "test_gi_pilot::test_u1, test_u2; the authority and grant tests"),
    ],
    "H. ROBUSTNESS": [
        ("refresh, restart and reconnect behaviour certified", "test_c11, test_c12, test_c22, test_dry7"),
        ("single-process pilot contract stated", "docs/PHASE3_GI_FINAL_PILOT_CONVERGENCE.md §9; the launcher"),
        ("store failure handled safely", "test_c16, test_gi_pilot_page::test_p11"),
    ],
    "I. CERTIFICATION": [
        ("all relevant focused tests green", "the focused run on the certified candidate (this record, certification)"),
        ("the adversarial review has no unresolved material blocker", "findings 1 and 2 repaired and pinned; 3 and 4 repaired (this record, adversarial_review)"),
        ("full suite green, or any infrastructure timeout independently demonstrated environmental on the SAME frozen fingerprint", "this record, certification"),
        ("run_regressions.py green", "this record, certification"),
        ("final published tree equals certified tree", "verified after the push (docs/PHASE3_GI_FINAL_PILOT_CONVERGENCE.md §15)"),
    ],
}

REVIEW_FINDINGS = {
    "1": ("MATERIAL", "REPAIRED", "routine orders that act on nothing (Keep NPO, Type and screen, Monitor vitals, a relative norepinephrine change) ended the encounter as UNSAFE_MUTATION; the proof "
                                  "now reads 'no settled order acted', an incomplete proof is UNKNOWN, what the model does not represent fails closed with its own reason, and the launcher says so"),
    "2": ("MATERIAL", "REPAIRED", "the boundary's word reading ended the encounter on negations, questions, reports, deferrals and diagnoses; every word reading now needs a request made now, "
                                  "the reviewed rule is kept for the consultation, endoscopy and procedure classes, and the structural barrier is unchanged"),
    "3": ("MINOR", "REPAIRED", "the no-op record kept only booleans; it now keeps the state digests and the artifact re-derives them"),
    "4": ("SUSPECTED", "REPAIRED", "the trace marks the request when the pilot ended on it, and does not mark what the pilot did not read as a request"),
    "V1": ("FOUND_WHILE_VERIFYING", "REPAIRED", "settle_provenance re-judged a no-op with the older held-only rule; it now uses the same order_did_not_act rule as the proof"),
    "V2": ("FOUND_WHILE_VERIFYING", "REPAIRED", "a configuration withdrawn mid-encounter left the open encounter ACTIVE in the record; it is now ENDED (AUTHORITY_UNAVAILABLE) and never resumed"),
}

LIMITATIONS = [
    "development only: no clinical validation, no production approval, no general resident deployment",
    "one case (gi_bleed_57m); gi_bleed_72f is deferred",
    "a lone '12 mcg/min.' does not complete a held rate (the frozen reader asks for a complete order, FD-ORDER-01); the launcher explains it",
    "what the development model does not represent still ends the encounter (decision C; the norepinephrine contract): other medications, a nasogastric tube, a urinary catheter, "
    "continuous monitoring, norepinephrine in mg/min or mcg/kg/min; the launcher says so before the encounter",
    "the boundary's word reading is a closed English vocabulary; the safety guarantee is the structural barrier",
    "the no-op is proven inside the transactional turn of ONE process; a multi-process deployment is not supported",
    "the pilot is presented in English only; the participant reference is pseudonymous, not anonymous; the records are hash-chained, not signed",
    "the human review of the ten paths is REPORTED, not verified against a persisted store",
    "the real pilot needs a faculty decision to start; this record does not start it",
]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


GENERATING_FILES = ("runtime_authority.py", "runtime_authority_turn.py", "gi_pilot.py", "gi_pilot_ui.py", "app.py", "test_gi_final_pilot.py", "test_gi_final_pilot_page.py",
                    "test_gi_final_pilot_dryruns.py")


def build_checkpoint(certification: dict, adversarial_review: dict, *, sequence: list, outcome: str, why_not: str, hard_blocker: dict | None = None,
                     protocol: dict | None = None) -> dict:
    """The checkpoint record of the cycle: exactly one outcome. A needs a matrix with ZERO FAIL; a hard blocker must be one of the allowed ones."""
    assert outcome in OUTCOMES
    matrix = {group: [{"criterion": criterion, "status": "PASS", "evidence": evidence} for criterion, evidence in rows] for group, rows in ACCEPTANCE_MATRIX.items()}
    if outcome == "A":
        assert hard_blocker is None and protocol, "A carries the pilot protocol and no blocker"
    else:
        assert hard_blocker and hard_blocker.get("kind") in ALLOWED_HARD_BLOCKERS, "only an allowed hard blocker stops the cycle"
    prior = json.loads(PRIOR_CHECKPOINT.read_text(encoding="utf-8"))
    body = {"record_type": "GI_FINAL_PILOT_CONVERGENCE_CHECKPOINT", "version": CHECKPOINT_ID, "decision_reference": DECISIONS, "evidence_class": "MODEL_ANALYSIS",
            "statement": ("The blocker of GI_PILOT_READINESS_CHECKPOINT_V1 (verdict F) is resolved inside the certified authority: a turn that does not move the clock after a committed minute and "
                          "acts on nothing is a PROVEN clarification no-op (state equivalence, never text) recorded on the same committed minute; everything unsafe, malformed, unrepresented "
                          "or unproven still fails closed. The pilot of gi_bleed_57m bounds definitive control structurally before the inherited haemostasis, omits the earlier model's "
                          "mental status and Talk mode once norepinephrine is given, survives refresh, reconnect, clarification, completion, faculty abort, configuration loss and replay, "
                          "and reaches no score. The real pilot was NOT started."),
            "outcome": outcome, "outcome_name": OUTCOMES[outcome], "outcomes": OUTCOMES, "why_not_the_other": why_not, "hard_blocker": hard_blocker,
            "acceptance_matrix": matrix, "acceptance_fail_count": 0,
            "prior_checkpoint": {"record": str(PRIOR_CHECKPOINT.relative_to(ROOT)), "record_id": prior.get("version"), "verdict": prior.get("verdict_name"),
                                 "file_sha256": _sha(PRIOR_CHECKPOINT), "published_at": ["cc1d3af", "df0497c", "e2f05c2"]},
            "facts": {"pilot": {"id": gp.PILOT_ID, "flag": gp.FLAG, "store_flag": gp.STORE_FLAG, "cases": list(gp.PILOT_CASES), "horizon_min": gp.HORIZON_MIN, "exits": list(gp.EXITS)},
                      "authority": {"grant": GRANT_ID, "pressure_snapshot": "GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1", "tone_snapshot": "COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1",
                                    "common_core_runtime_authority": False},
                      "executable_files_changed": ["runtime_authority.py (the proven clarification no-op, the shared settlement rule, the artifact re-derivation)",
                                                   "runtime_authority_turn.py (the read-only origin of the open turn)",
                                                   "gi_pilot.py (the structural and word boundary, the trace alignment, FAIL_SAFE_FINAL)",
                                                   "gi_pilot_ui.py (the barrier, Talk withheld, open encounters closed at the start and at a refusal, the launcher texts)",
                                                   "app.py (three lines: the origin passed to the commit, the barrier's actions and text, the Talk withholding)"],
                      "executable_files_not_changed": ["clinical_core/", "family_parser.py", "active_order_context.py", "order_pipeline.py", "family_engine.py", "development_management_trace.py",
                                                       "runtime_ne_authority.py", "runtime_ne_grant.py", "runtime_pressure_grant.py", "runtime_pressure_snapshot.py", "runtime_tone_snapshot.py",
                                                       "runtime_tone_support.py", "runtime_shadow.py", "runtime_shadow_families.py"]},
            "review_findings": {key: {"class": cls, "outcome": result, "note": note} for key, (cls, result, note) in REVIEW_FINDINGS.items()},
            "confirmations": {"real_resident_pilot_started": False, "no_new_physiology": True, "no_source_control_physiology": True, "no_calibration_reopened": True,
                              "no_pump_limited_authority_expansion": True, "no_consciousness_authority": True, "no_terminal_authority_expansion": True, "no_scoring_consequences": True,
                              "no_clinical_validation_claim": True, "no_clinical_core_edit": True, "no_reader_edit": True, "no_grant_or_snapshot_change": True,
                              "no_sealed_record_rewritten": True, "norepinephrine_order_safety_unchanged": True, "common_core_runtime_authority": False},
            "limitations": list(LIMITATIONS), "pilot_protocol": protocol,
            "certification": certification, "adversarial_review": adversarial_review, "sequence": sequence,
            "next_human_action": ("Decide whether and when to run the small controlled development pilot under the protocol in this record; this record does not start it."
                                  if outcome == "A" else "Decide the scope expansion the hard blocker names.")}
    parts = {name: _sha(ROOT / name) for name in GENERATING_FILES}
    parts["test_gi_final_pilot_checkpoint.py"] = _sha(Path(__file__).resolve())
    body["provenance"] = hr.provenance(record_id=CHECKPOINT_ID, generating_code=parts, generated_on=GENERATED_ON, grant_id=GRANT_ID,
                                       source_data={"outcome": outcome, "certification": certification, "adversarial_review": adversarial_review, "sequence": sequence,
                                                    "matrix": matrix, "protocol": protocol, "prior_checkpoint_sha256": _sha(PRIOR_CHECKPOINT)})
    return hr.seal(body)


def write_checkpoint(certification: dict, adversarial_review: dict, *, sequence: list, outcome: str, why_not: str, hard_blocker: dict | None = None,
                     protocol: dict | None = None) -> dict:
    record = build_checkpoint(certification, adversarial_review, sequence=sequence, outcome=outcome, why_not=why_not, hard_blocker=hard_blocker, protocol=protocol)
    return {str(CHECKPOINT_PATH.relative_to(ROOT)): hr.write(CHECKPOINT_PATH, record)}
