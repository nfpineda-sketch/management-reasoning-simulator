"""P3-473: the CHECKPOINT of the target-vs-rate repair at the source (a tool, never imported by a page; it holds no test).

The checkpoint is written ONCE, after the certification, as a sealed, versioned, indexed historical record with exactly ONE verdict of the five the faculty named. It is a different file from the builder of the
successor record (``test_reader_succession_analysis``) so that writing it never changes the generating code that record names.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import historical_records as hr
import reader_succession as rsu
import test_reader_succession_analysis as build

ROOT = Path(__file__).resolve().parent
CHECKPOINT_PATH = ROOT / "docs" / "revision" / "PHASE3_TARGET_RATE_SOURCE_CHECKPOINT.json"
CHECKPOINT_ID = "TARGET_RATE_SOURCE_CHECKPOINT_V1"
VERDICTS = {"A": "TARGET_RATE_SEMANTICS_REPAIRED_AT_SOURCE_AND_DEFENSE_IN_DEPTH_CERTIFIED", "B": "NOREPINEPHRINE_FIXED_BUT_NITROGLYCERIN_REQUIRES_SEPARATE_PARSER_SUCCESSOR",
            "C": "PARSER_FREEZE_REQUIRES_FACULTY_GOVERNANCE_DECISION", "D": "RELATIVE_ORDER_SEMANTICS_REQUIRE_BROADER_ORDER_REDESIGN", "E": "SOURCE_FIX_BREAKS_HISTORICAL_RECONSTRUCTION"}
GENERATED_ON = "2026-11-20"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_checkpoint(certification: dict, adversarial_review: dict, *, sequence: list, facts: dict | None = None, verdict: str = "A") -> dict:
    """The checkpoint record of the cycle. Exactly one verdict. With A: a physiologic target is never a drug rate, in the source (the reader) and in the pipeline barrier, for norepinephrine, epinephrine,
    dobutamine and nitroglycerin; the freeze of the reader was lifted ONCE, narrowly, and the reader of the Phase-2 closure stays reconstructable byte for byte with every Phase-2 digest recomputed from it; nothing
    sealed was rewritten and nothing in clinical_core/ was edited. What the independent review found that predates the change and is not a target is declared, not hidden."""
    assert verdict in VERDICTS
    successor = json.loads(build.RECORD_PATH.read_text(encoding="utf-8"))
    body = {"record_type": "TARGET_RATE_SOURCE_CHECKPOINT", "version": CHECKPOINT_ID, "decision_reference": "FD-TARGET-01 to FD-TARGET-11", "evidence_class": "MODEL_ANALYSIS",
            "statement": ("A physiologic target (MAP 65, SBP 90, a pressure goal, with or without '>', in either language) is never executed as a drug rate. The order reader no longer reads a rate of norepinephrine, epinephrine, "
                          "dobutamine or nitroglycerin unless it is written with its unit; a number with no rate unit, and a relative change with no rate, is the approved question and carries no number; an explicit absolute "
                          "rate is read exactly as before; the restart of one of the four infusions is a start that needs an explicit rate and never reuses the previous one. The pipeline barrier of the previous cycle stays "
                          "as defense in depth and each barrier protects alone (proven with the other removed, and by mutants). The reader freeze was lifted ONCE, narrowly (FD-TARGET-01): the reader of the Phase-2 closure "
                          "is rebuilt byte for byte from the successor by declared reversible hunks, every Phase-2 digest recomputes from it, the calibration freeze moved in exactly one component and the materialized "
                          "scenario inputs did not move; nothing sealed was rewritten and nothing in clinical_core/ was edited. The independent review found side effects of the change (reasoning extraction, the record of the "
                          "order, the 'then' sequence, a decimal point, the restart of one-shot doses, a restart alias) and they were reproduced and repaired; it also found behaviors that predate the change and are not a "
                          "target (a non-rate unit on a role-named adjustment, the rate of another drug in the same clause, a stop inherited from a list, '/min' read as a duration): they are declared as limitations and "
                          "decisions, not changed (FD-TARGET-01 forbids an unrelated parsing change)."),
            "verdict": verdict, "verdict_name": VERDICTS[verdict], "verdicts": VERDICTS,
            "why_not_the_others": {"A": "this is the verdict" if verdict == "A" else "not all conditions of A hold",
                                   "B": "nitroglycerin is closed at the source with the same structural rule (its bare number is a question, 'titrate nitroglycerin to SBP 120' is no longer 120 mcg/min); its pipeline barrier is "
                                        "partial by design (the unit is in the field name) and that is declared, not a reason for a separate parser successor",
                                   "C": "the freeze was lifted by the faculty (FD-TARGET-01) and the minimum formally correct mechanism was found and proven: no governance decision is outstanding for this repair",
                                   "D": "the incomplete and relative commands ('increase norepinephrine', 'increase norepinephrine to 12', 'restart norepinephrine') needed no new order language: the existing question mechanism "
                                        "carries them; the semantics that remain open (relative orders with context, targets as an input to titration) were not part of this mandate",
                                   "E": "the historical reconstruction is exact: SHA-256 and git blob of the closure reader are reproduced, every recorded closure digest recomputes with the reader of its time, and no sealed record changed"},
            "facts": {"successor_record_digest": successor["record_digest"], "reader": {"historical_git_blob": rsu.HISTORICAL_GIT_BLOB, "successor_git_blob": rsu.SUCCESSOR_GIT_BLOB, "hunks": len(rsu.REVERSAL)},
                      "calibration_freeze_components_that_moved": successor["freeze"]["calibration"]["components_that_moved"],
                      "scenario_inputs_identical": successor["freeze"]["calibration"]["scenario_inputs_identical"],
                      "closure_freeze_digests_recompute": successor["freeze"]["closure_freeze_digests"]["equal"],
                      "executable_files_changed": ["family_parser.py", "order_pipeline.py", "order_ledger.py", "pending_family_orders.py", "app.py", "language.py", "reader_succession.py"],
                      "executable_files_not_changed": ["family_engine.py", "active_order_context.py", "shared_order_language.py", "shared_order_quantities.py", "weight_based_doses.py", "runtime_shadow.py",
                                                       "runtime_tone_support.py", "clinical_core/"],
                      "core_digest": build.generating_code()["clinical_core"],
                      **(facts or {})},
            "confirmations": {"no_tone_recalibration": True, "no_pump_coupling_change": True, "no_physiology_change": True, "no_parameter_selected": True, "no_norepinephrine_authority_expansion": True,
                              "no_consciousness_authority": True, "no_terminal_authority": True, "no_resident_deployment": True, "no_clinical_validation_claim": True, "no_weight_based_dosing": True,
                              "no_map_target_titration": True, "no_new_drug": True, "no_malformed_order_recovery": True, "no_shadow_boundary_change": True, "no_sealed_record_rewritten": True,
                              "no_clinical_core_edit": True, "common_core_runtime_authority": False},
            "limitations": ["L-1: a role-named adjustment with another unit ('increase the infusion to 40 mL/h') runs as 40 mcg/min when nitroglycerin is running (unit dropped in frozen completion code; predates the change)",
                            "L-2: the rate of another drug in the same clause is attributed to the vasoactive ('... to MAP 65 with propofol 5 mcg/min' -> 5 mcg/min; predates the change)",
                            "L-3: a stop inherited from a list stops the vasopressor ('stop NS, norepinephrine to MAP 65'; a stop is never held; predates the change)",
                            "L-4: a deferred order with an explicit rate runs now ('... to 12 mcg/min in 5 minutes': the duration reads '/min'; predates the change)",
                            "L-5: 'restart norepinephrine' with no rate gets the engine's question, not the approved text (nothing runs, nothing is inferred)",
                            "L-6: 'continue norepinephrine at 12' continues at the running rate with no message (the number is not executed)",
                            "L-7: the pipeline barrier reads rate, rate_value and units only; the engine reads rate_mcg_min for any infusion; the reader does not emit that shape",
                            "L-8: the legacy page path for non-family cases accepts a numeric reply to 'what dose?' as a rate (function level; the interface was not driven)",
                            "L-9: for nitroglycerin the source is the ONLY barrier of the bare number (its unit lives in the field name)",
                            "L-10: an incomplete order is held per turn; there is no recovery of malformed orders (not authorized)",
                            "mcg/kg/min still enters through weight_based_doses (the shadow fails closed); no automatic MAP titration; no relative orders with context",
                            "the new records have no signature (the same limit as TD-153 item 7)"],
            "certification": certification, "adversarial_review": adversarial_review, "sequence": sequence,
            "next_human_action": ("A faculty member decides, in order of value: (1) whether a unit-compatibility guard and a per-drug rate attribution are added to the order pipeline for orders that name no drug (L-1, L-2), "
                                  "(2) how a stop inherited from a list and a deferred order with '/min' should read (L-3, L-4), (3) the text of 'restart' with no rate and what follows 'continue' (L-5, L-6), (4) whether the "
                                  "legacy numeric reply of the page is retired (L-8). Nothing else is to be done until then."),
            "open_faculty_decisions": ["a unit-compatibility guard for role-named adjustments and per-drug rate attribution (L-1, L-2)", "the stop inherited from a list and the deferred order with '/min' (L-3, L-4)",
                                       "unify the text of 'restart' with no rate with the approved one; what a number after 'continue' means (L-5, L-6)", "retire the legacy numeric reply of the page (L-8)"]}
    parts = {"clinical_core": build.generating_code()["clinical_core"], "successor_record_digest": successor["record_digest"], "family_parser.py": _sha(ROOT / "family_parser.py"),
             "order_pipeline.py": _sha(ROOT / "order_pipeline.py"), "order_ledger.py": _sha(ROOT / "order_ledger.py"), "pending_family_orders.py": _sha(ROOT / "pending_family_orders.py"),
             "app.py": _sha(ROOT / "app.py"), "language.py": _sha(ROOT / "language.py"), "reader_succession.py": _sha(ROOT / "reader_succession.py"),
             "test_phase3_target_rate_source.py": _sha(ROOT / "test_phase3_target_rate_source.py"), "test_phase3_target_order_boundary.py": _sha(ROOT / "test_phase3_target_order_boundary.py"),
             "test_target_rate_source_checkpoint.py": _sha(Path(__file__).resolve())}
    body["provenance"] = hr.provenance(record_id=CHECKPOINT_ID, generating_code=parts, generated_on=GENERATED_ON, grant_id="GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V3",
                                       source_data={"verdict": verdict, "certification": certification, "adversarial_review": adversarial_review, "sequence": sequence})
    return hr.seal(body)


def write_checkpoint(certification: dict, adversarial_review: dict, *, sequence: list, facts: dict | None = None, verdict: str = "A") -> dict:
    return {str(CHECKPOINT_PATH.relative_to(ROOT)): hr.write(CHECKPOINT_PATH, build_checkpoint(certification, adversarial_review, sequence=sequence, facts=facts, verdict=verdict))}
