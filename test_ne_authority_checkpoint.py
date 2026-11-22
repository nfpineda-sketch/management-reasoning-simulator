"""P3-502: the CHECKPOINT of the promotion of the ratified manual norepinephrine rate control to LIVE DEVELOPMENT AUTHORITY (a tool, never imported by a page; it holds no test).

The checkpoint is written ONCE, after the certification, as a sealed, versioned, indexed historical record with exactly ONE verdict of the six the faculty named. It is a different file from the test of the
authority so that writing it never changes the generating code that file names.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import historical_records as hr
import runtime_ne_authority as ne
import runtime_ne_grant as grant
import runtime_tone_snapshot as tone

ROOT = Path(__file__).resolve().parent
CHECKPOINT_PATH = ROOT / "docs" / "revision" / "PHASE3_NOREPINEPHRINE_AUTHORITY_CHECKPOINT.json"
CHECKPOINT_ID = "NOREPINEPHRINE_AUTHORITY_CHECKPOINT_V1"
VERDICTS = {"A": "GI_NOREPINEPHRINE_MANUAL_CONTROL_PROMOTED_TO_LIVE_DEVELOPMENT_AUTHORITY", "B": "NOREPINEPHRINE_AUTHORITY_READY_BUT_ARTIFACT_REPLAY_NOT_CERTIFIED",
            "C": "ORDER_SAFETY_CONTRACT_NOT_STRONG_ENOUGH_FOR_AUTHORITY", "D": "TONE_SNAPSHOT_BINDING_MISMATCH", "E": "AUTHORITY_PROMOTION_REQUIRES_NEW_PHYSIOLOGY",
            "F": "ISOLATION_BOUNDARY_NOT_CERTIFIABLE"}
GENERATED_ON = "2026-11-21"
#: What the independent review found (each reproduced BEFORE it was repaired) and what became of it.
REVIEW_FINDINGS = {
    "A1": ("MATERIAL", "REPAIRED", "a norepinephrine run relabelled as the earlier grant, with an honest overlay spliced in, passed verification: the grant the artifact names now decides and the content must agree"),
    "A2": ("MINOR", "REPAIRED", "the contract rows are the writer's orders and their semantics are recomputed from the artifact alone"),
    "A3": ("MINOR", "REPAIRED", "the carried class is modelled, not 'unsupported', in the artifact's dispositions"),
    "A4": ("MINOR", "REPAIRED", "the contract reads the class as the site does and never passes what it cannot see"),
    "A5": ("MINOR", "REPAIRED", "verifying an earlier artifact registers nothing new in the core (checked in a fresh process)"),
    "A6": ("MINOR", "REPAIRED", "the artifact carries the label the grant names (a surviving mutant of that check was closed with a direct test)"),
    "A7": ("LOW_RISK_SEMANTICS", "DECLARED_NOT_REPAIRED", "a compound norepinephrine order with titration clauses ('q5 min increase by 2', '(max 20)', 'at 5 to 10 mcg/min') is read by the frozen reader without those clauses "
                                                       "and runs as the explicit rate it does contain; repairing the reader needs a third succession and a faculty decision"),
}
LIMITATIONS = [
    "CONSCIOUSNESS_UNDER_TONE_UNRESOLVED stays open: the overlay now runs the same haemodynamics as the pressure (with norepinephrine); it is only the collapse-boundary guard it already was, writes no mental_status "
    "and is not resident-visible; that combination has not been reviewed by the faculty",
    "COMMON_TONE_PUMP_DEPENDENCE_NOT_YET_VALIDATED stays monitored: nothing was promoted in pump-limited families or in pulmonary edema",
    "'continue norepinephrine' with no rate is a permanent fail-closed (not in the ratified list): a faculty decision whether to accept it as a no-op",
    "A7: compound orders with titration clauses are read by the frozen reader without those clauses; no reader repair was made (third succession and a faculty decision)",
    "a norepinephrine order HELD by the pending-order queue was not tested end to end",
    "the live equality with the ratified trajectories is MEASURED (minute by minute), not a new human judgment: what the faculty reviewed was the shadow",
    "the checkpoint record has no signature (the same limit as TD-153 item 7)",
]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_checkpoint(certification: dict, adversarial_review: dict, *, sequence: list, facts: dict | None = None, verdict: str = "A") -> dict:
    """The checkpoint record of the cycle. Exactly one verdict. With A: the ratified manual norepinephrine rate control runs under the live development authority of the GI pressure, in the two GI cases, only on
    sbp/dbp/map, under a NEW versioned grant that does not mutate the previous one, bound to the two ratified snapshots exactly, with an order contract the authority verifies by itself, a permanent fail-closed for
    everything unsupported, an artifact and a replay that fail when relabelled or altered (the historical artifacts replay as before), and an exact minute-by-minute equality with the ratified trajectories."""
    assert verdict in VERDICTS
    cfg = tone.bind()
    body = {"record_type": "NOREPINEPHRINE_AUTHORITY_CHECKPOINT", "version": CHECKPOINT_ID, "decision_reference": "FD-AUTHNE-01 to FD-AUTHNE-12", "evidence_class": "MODEL_ANALYSIS",
            "statement": ("The ratified manual norepinephrine rate control (start, increase, decrease, stop and restart with explicit absolute mcg/min rates) runs under the live DEVELOPMENT authority of the GI pressure, only "
                          "in gi_bleed_57m and gi_bleed_72f and only on sbp/dbp/map (the tone support is an internal state, never resident-visible and never scored). It is a NEW versioned grant "
                          f"({grant.GRANT_ID}) that extends and does not mutate the previous one, and it is opened only by the exact tone snapshot id together with the ratified pressure snapshot. The authority verifies the order "
                          "contract by itself (the raw order stays the correct boundary; the certified reader stays the barrier), anything unsupported is a permanent fail-closed with no recovery, and the artifact and its replay "
                          "carry the grant, the tone configuration, the writer and a clean contract per minute: an artifact renamed, relabelled or altered fails even with its digest recomputed, and the earlier artifacts replay "
                          "as before. No tone value, coupling, snapshot, bleed rate or crystalloid kernel was changed, nothing in clinical_core/ or in the frozen reader was edited, and the consciousness under tone stays open."),
            "verdict": verdict, "verdict_name": VERDICTS[verdict], "verdicts": VERDICTS,
            "why_not_the_others": {"A": "this is the verdict" if verdict == "A" else "the conditions of A do not hold",
                                   "B": "artifact and replay are certified: the renamed, relabelled, block-removed and altered-configuration artifacts fail with the digest recomputed, the earlier artifacts replay, and a fresh process reproduces",
                                   "C": "the contract is the authority's own (type, operation, exact unit, one finite positive rate, coherent receipt, a stop without a rate, first move a start, intact chronology, a rate the writer represents) "
                                        "and is held to the shadow's history; the fail-closed matrix and a fuzz of orders produce no executed unsupported order",
                                   "D": "the tone binding reads the ratified record by file hash and record digest, is typed twice and equals the core's CENTER_REFERENCE; LOW and HIGH are never read; per-code mutants are refused",
                                   "E": "the live series equal the ratified trajectories exactly (FR-F and TIT-1 to TIT-5, both cases): no physiology, parameter or coupling was needed",
                                   "F": "only sbp/dbp/map move, no new key reaches the resident, mental_status is the legacy engine's, the page names neither the selector nor the module, and the independent review's isolation probes passed"},
            "facts": {"grant": {"id": grant.GRANT_ID, "fingerprint": grant.GRANT_FINGERPRINT, "extends": "GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V3", "previous_grants_mutated": False,
                                "domains": list(grant.DOMAIN), "cases": ["gi_bleed_57m", "gi_bleed_72f"]},
                      "pressure_snapshot": "GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1",
                      "tone_snapshot": {"id": "COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1", "configuration": cfg.summary(), "binding": dict(tone.BINDING)},
                      "overlay_profile_digest": ne.TONE_OVERLAY_PROFILE_DIGEST, "artifact_label": grant.ARTIFACT_LABEL,
                      "reader": {"git_blob": grant.READER_GIT_BLOB, "sha256": grant.READER_SHA256},
                      "executable_files_added": ["runtime_ne_grant.py", "runtime_tone_snapshot.py", "runtime_ne_authority.py"],
                      "executable_files_changed": ["runtime_authority.py", "runtime_shadow.py", "runtime_authority_pair.py", "runtime_authority_session.py", "runtime_faculty_review.py"],
                      "executable_files_not_changed": ["clinical_core/", "family_parser.py", "family_engine.py", "active_order_context.py", "order_pipeline.py", "app.py", "runtime_pressure_grant.py",
                                                       "runtime_pressure_snapshot.py", "runtime_tone_support.py", "runtime_shadow_families.py"],
                      "equality": {"FR-F": "exact", "TIT-1_to_TIT-5": "exact", "cases": ["gi_bleed_57m", "gi_bleed_72f"], "minutes_compared_each": 32, "differences": 0},
                      "without_norepinephrine": "FR-A, FR-B, FR-C, FR-D, FR-E and FR-G identical to the previous grant to the last digit",
                      **(facts or {})},
            "review_findings": {key: {"class": cls, "outcome": outcome, "note": note} for key, (cls, outcome, note) in REVIEW_FINDINGS.items()},
            "confirmations": {"no_tone_recalibration": True, "no_pump_coupling_change": True, "no_new_physiology": True, "no_parameter_selected": True, "no_consciousness_authority": True,
                              "no_terminal_authority": True, "no_resident_deployment": True, "no_clinical_validation_claim": True, "no_weight_based_dosing": True, "no_map_target_titration": True,
                              "no_other_vasopressor": True, "no_malformed_order_recovery": True, "no_previous_grant_mutated": True, "no_clinical_core_edit": True, "no_reader_edit": True,
                              "no_sealed_record_rewritten": True, "low_and_high_never_read": True, "center_reference_never_recomputed": True, "common_core_runtime_authority": False},
            "limitations": list(LIMITATIONS),
            "certification": certification, "adversarial_review": adversarial_review, "sequence": sequence,
            "next_human_action": ("A faculty member decides, in order of value and only if and when it is wanted: (1) whether the consciousness under tone (CONSCIOUSNESS_UNDER_TONE_UNRESOLVED) may be reviewed with the "
                                  "live norepinephrine path; (2) whether 'continue norepinephrine' with no rate is a no-op; (3) whether the compound-order clauses of A7 need a third reader succession. Nothing else is to be "
                                  "built on this line until then; the authority stays development-only."),
            "open_faculty_decisions": ["review of the consciousness under tone with the live norepinephrine path", "'continue norepinephrine' with no rate: no-op or fail-closed", "compound orders with titration clauses (A7)",
                                       "pump-limited families (COMMON_TONE_PUMP_DEPENDENCE_NOT_YET_VALIDATED)"]}
    parts = {"clinical_core": cfg.summary().get("core_digest") or tone.CORE_DIGEST, "runtime_ne_grant.py": _sha(ROOT / "runtime_ne_grant.py"), "runtime_tone_snapshot.py": _sha(ROOT / "runtime_tone_snapshot.py"),
             "runtime_ne_authority.py": _sha(ROOT / "runtime_ne_authority.py"), "runtime_authority.py": _sha(ROOT / "runtime_authority.py"), "runtime_shadow.py": _sha(ROOT / "runtime_shadow.py"),
             "runtime_authority_pair.py": _sha(ROOT / "runtime_authority_pair.py"), "runtime_authority_session.py": _sha(ROOT / "runtime_authority_session.py"),
             "runtime_faculty_review.py": _sha(ROOT / "runtime_faculty_review.py"), "test_phase3_ne_authority.py": _sha(ROOT / "test_phase3_ne_authority.py"),
             "test_ne_authority_checkpoint.py": _sha(Path(__file__).resolve())}
    body["provenance"] = hr.provenance(record_id=CHECKPOINT_ID, generating_code=parts, generated_on=GENERATED_ON, grant_id=grant.GRANT_ID,
                                       source_data={"verdict": verdict, "certification": certification, "adversarial_review": adversarial_review, "sequence": sequence})
    return hr.seal(body)


def write_checkpoint(certification: dict, adversarial_review: dict, *, sequence: list, facts: dict | None = None, verdict: str = "A") -> dict:
    return {str(CHECKPOINT_PATH.relative_to(ROOT)): hr.write(CHECKPOINT_PATH, build_checkpoint(certification, adversarial_review, sequence=sequence, facts=facts, verdict=verdict))}
