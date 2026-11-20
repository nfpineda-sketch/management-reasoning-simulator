"""P3-461: the CHECKPOINT of the manual norepinephrine rate-control ratification and the target-order repair (a tool, never imported by a page; it holds no test).

The checkpoint is written ONCE, after the certification, as a sealed, versioned, indexed historical record with exactly ONE verdict of the six the faculty named. It is a different file from the builder of the
ratification records (``test_nr_manual_ratification_analysis``) so that writing it never changes the generating code those records name.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import historical_records as hr
import test_nr_manual_ratification_analysis as build

ROOT = Path(__file__).resolve().parent
CHECKPOINT_PATH = ROOT / "docs" / "revision" / "PHASE3_NOREPINEPHRINE_TARGET_ORDER_CHECKPOINT.json"
CHECKPOINT_ID = "NOREPINEPHRINE_TARGET_ORDER_CHECKPOINT_V1"
VERDICTS = {"A": "MANUAL_NOREPINEPHRINE_SEMANTICS_RATIFIED_AND_TARGET_ORDER_BUG_FIXED", "B": "MANUAL_SEMANTICS_RATIFIED_TARGET_FIX_SAFE_BOUNDARY_UNRESOLVED",
            "C": "GENERIC_ORDER_PARSER_CHANGE_REQUIRES_BROADER_REVIEW", "D": "RAW_VS_RESOLVED_ORDER_REQUIRES_FACULTY_DECISION", "E": "MALFORMED_ORDER_POLICY_BLOCKS_SAFE_PROGRESS",
            "F": "ORDER_MODEL_REQUIRES_BROADER_REDESIGN"}
GENERATED_ON = "2026-11-20"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_checkpoint(certification: dict, adversarial_review: dict, *, sequence: list, facts: dict | None = None, verdict: str = "A") -> dict:
    """The checkpoint record of the cycle. Exactly one verdict. With A: the manual semantics are ratified for development, the target-as-rate defect is reproduced, traced and fixed at the earliest layer that is NOT
    frozen (the order pipeline, before the engine) with no change to the frozen reader, the engine, the mirror, the shadow, the core or the authority, the raw-order boundary stays correct (no new shared mirror contract was
    invented), and no recovery-policy change was needed. The residuals (nitroglycerin, and the reader's own fallback) are declared, not hidden."""
    assert verdict in VERDICTS
    human = json.loads(build.HUMAN_PATH.read_text(encoding="utf-8"))
    closure = json.loads(build.CLOSURE_PATH.read_text(encoding="utf-8"))
    body = {"record_type": "NOREPINEPHRINE_TARGET_ORDER_CHECKPOINT", "version": CHECKPOINT_ID, "decision_reference": "FD-NR-01 to FD-NR-07", "evidence_class": "MODEL_ANALYSIS",
            "statement": ("The manual norepinephrine rate-control semantics -- start, increase, decrease, stop and restart by an explicit absolute rate in mcg/min -- are ratified for DEVELOPMENT (status "
                          "NOREPINEPHRINE_MANUAL_RATE_CONTROL_DEVELOPMENT_SEMANTICS_CLOSED; the human review is reported, not verified against the persisted store). The inherited defect by which 'titrate norepinephrine to MAP 65' "
                          "was executed as 65 mcg/min was reproduced end to end, traced to two layers (the frozen reader fabricated the rate from the only number of the clause; the frozen engine completion made it executable by "
                          "inheriting the running infusion's units) and repaired before the engine, in the order pipeline, which is not frozen: an infusion order that carries a rate WITHOUT units is held as a question, nothing "
                          "is executed and the held copy keeps no number. The rule is structural -- no list of words -- so a MAP, a PA, a heart rate or a typo are the same thing. The reader, the completion and the engine were NOT "
                          "touched (a first design that did was defeated by the independent review and broke two freezes; it was reverted). The only executable changes are the pipeline rule and the Spanish text of its message. "
                          "The shadow keeps consuming the order as written (verdict A of the boundary audit); malformed-order recovery was analysed and not changed. Nitroglycerin, which carries its unit in the field name, is "
                          "NOT covered (a residual that predates the cycle)."),
            "verdict": verdict, "verdict_name": VERDICTS[verdict], "verdicts": VERDICTS,
            "why_not_the_others": {"A": "this is the verdict" if verdict == "A" else "not all conditions of A hold",
                                   "B": "the boundary audit returned A (raw order remains the correct boundary): nothing about the safe boundary is unresolved",
                                   "C": "the repair is one structural rule in the order pipeline, after the reader and before the engine, for the infusion orders that complete a missing unit (norepinephrine, dobutamine, epinephrine and the "
                                        "role-named order); the generic parser was NOT changed (it is frozen), no other family of orders changed, and the other interpreter findings (the verb 'restart', a relative command without a rate, "
                                        "nitroglycerin) were NOT changed; a source-level repair would need the reader freeze lifted, which is a faculty decision, not a blocker of this fix",
                                   "D": "the raw-versus-resolved choice is not genuinely open for this stage: the raw boundary is the safest, the only one compatible with everything certified, and every divergence measured is a declared fidelity "
                                        "gap, not a safety defect; moving toward resolved orders WOULD be a faculty decision and none was made",
                                   "E": "no malformed-order behavior creates a demonstrated safety defect: the shadow has no authority over norepinephrine, is invisible to the resident and declares every divergence; recovery was analysed and is a "
                                        "separate faculty decision (FD-NR-07)",
                                   "F": "the order model needed no redesign: one structural rule in the pipeline repaired the defect and every other layer behaved as designed"},
            "facts": {"human_record_digest": human["record_digest"], "closure_record_digest": closure["record_digest"], "closure_status": closure["status"], "overall_counts": human["overall_counts"],
                      "review_set_digest": human["review"]["review_set_digest"], "provenance_of_the_human_evidence": human["provenance_of_the_evidence"]["verification"],
                      "failure_classification": {"verdict": "F", "name": "MULTIPLE_LAYERS", "layers": {"text_interpreter": "origin (necessary)", "engine_completion": "enabling (necessary)",
                                                                                                    "mirror": "not confused", "shadow_mapping": "not confused", "writer": "never reached"}},
                      "raw_vs_resolved_verdict": {"verdict": "A", "name": "RAW_ORDER_REMAINS_CORRECT_BOUNDARY"},
                      "malformed_order_recovery": {"recommendation": "KEEP_PERMANENT_FAIL_CLOSED", "implemented": False, "faculty_decision_if_recovery_is_wanted": True},
                      "executable_files_changed": ["order_pipeline.py", "language.py"],
                      "executable_files_not_changed": ["family_parser.py", "family_engine.py", "active_order_context.py", "runtime_shadow.py", "runtime_tone_support.py", "clinical_core/"],
                      "reader_freeze": {"reader_changed": False, "calibration_freeze_digest_changed": False, "governance_decision_pending": "lift the reader freeze to repair at the source (it would also cover nitroglycerin)"},
                      "first_design_discarded": {"design": "pressure-word vocabulary guard in the reader", "reason": "independent review: 121630 of 1.65 million phrasings still leaked; false positives; broke the reader freeze and the calibration freeze"},
                      "residual": {"nitroglycerin": "its unit is in the field name (rate_mcg_min): a bare number is still read as 120 mcg/min; predates the cycle; the reader is frozen"},
                      **(facts or {})},
            "confirmations": {"no_tone_recalibration": True, "no_pump_coupling_change": True, "no_physiology_change": True, "no_parameter_selected": True, "no_witness_substituted": True,
                              "no_norepinephrine_authority_expansion": True, "no_consciousness_authority": True, "no_terminal_authority": True, "no_resident_deployment": True, "no_clinical_validation_claim": True,
                              "no_weight_based_dosing": True, "no_map_target_titration": True, "no_new_vasopressor": True, "no_malformed_order_recovery_change": True, "no_new_shared_mirror_contract": True,
                              "persisted_store_verified": False, "common_core_runtime_authority": False},
            "limitations": ["the human review is reported, not verified against the persisted store (only the five overall judgments were reported)",
                            "the repair is after the reader, not at the source: the frozen reader still emits a bare number as a rate with no units (rate 65, units None); repairing it there needs the reader freeze lifted",
                            "nitroglycerin is NOT covered: its only unit is in the field name, so 'titrate nitroglycerin to SBP 120' still reads as 120 mcg/min (predates the cycle; test t18 records it)",
                            "an order of norepinephrine, dobutamine or epinephrine with a number and no units now asks for the units, including the shorthand 'increase norepinephrine to 12' (a declared effect)",
                            "the interpreter does not read the verb 'restart' (it is held as an unrecognized order, with no dose); the supported restart is the explicit start after a stop",
                            "a relative command without a number ('increase norepinephrine') is completed by the engine with the running rate (no real change, no warning); the shadow refuses it and says so",
                            "the shadow does not follow orders the engine resolves (an order that names no drug, mcg/kg/min): declared fidelity gaps; following them would need a new shared mirror contract",
                            "the new Spanish message is a development wording that the faculty has not approved (TD-46)",
                            "the new records have no signature (the same limit as TD-153 item 7)"],
            "certification": certification, "adversarial_review": adversarial_review, "sequence": sequence,
            "next_human_action": ("A faculty member decides, in this order of value: (0) whether to lift the reader freeze to repair the defect at the source (it would also cover nitroglycerin, the residual that is still unsafe), (1) whether the "
                                  "shadow should follow the orders the engine resolves (an architectural choice for the shared mirror: a hybrid that keeps the raw order and adds the engine's resolution with its provenance), (2) whether a later "
                                  "explicit valid order should recover the shadow after a malformed order, and with what tolerance, and (3) whether the interpreter should be taught the verb 'restart', should ask for the rate of 'increase "
                                  "norepinephrine' and should accept the shorthand 'increase to 12'. Nothing else is to be done until then."),
            "open_faculty_decisions": ["whether to lift the reader freeze to repair the target-as-rate defect at the source (also covers nitroglycerin)",
                                       "whether the shadow follows orders the engine resolves (hybrid with provenance) -- architectural", "whether a later explicit valid order recovers the shadow after a malformed order, and the continuity tolerance",
                                       "whether the interpreter reads the verb 'restart', asks for the rate of a relative command and accepts a rate without units", "the approval of the Spanish wording of the new message",
                                       "whether the verified store of the human review should be supplied so that the record can be verified"]}
    parts = {"clinical_core": build.generating_code()["clinical_core"], "human_record_digest": human["record_digest"], "closure_record_digest": closure["record_digest"], "order_pipeline.py": _sha(ROOT / "order_pipeline.py"), "family_parser.py": _sha(ROOT / "family_parser.py"),
             "language.py": _sha(ROOT / "language.py"), "test_phase3_target_order_boundary.py": _sha(ROOT / "test_phase3_target_order_boundary.py"), "test_nr_target_fix_checkpoint.py": _sha(Path(__file__).resolve())}
    body["provenance"] = hr.provenance(record_id=CHECKPOINT_ID, generating_code=parts, generated_on=GENERATED_ON, grant_id="GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V3",
                                       source_data={"verdict": verdict, "certification": certification, "adversarial_review": adversarial_review, "sequence": sequence})
    return hr.seal(body)


def write_checkpoint(certification: dict, adversarial_review: dict, *, sequence: list, facts: dict | None = None, verdict: str = "A") -> dict:
    return {str(CHECKPOINT_PATH.relative_to(ROOT)): hr.write(CHECKPOINT_PATH, build_checkpoint(certification, adversarial_review, sequence=sequence, facts=facts, verdict=verdict))}
