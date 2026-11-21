"""P3-487: the CHECKPOINT of the final vasoactive order-safety hardening (a tool, never imported by a page; it holds no test).

The checkpoint is written ONCE, after the certification, as a sealed, versioned, indexed historical record with exactly ONE verdict of the five the faculty named. It is a different file from the builder of the
successor record (``test_reader_succession_order_safety_analysis``) so that writing it never changes the generating code that record names.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import historical_records as hr
import reader_succession as rsu
import test_reader_succession_order_safety_analysis as build

ROOT = Path(__file__).resolve().parent
CHECKPOINT_PATH = ROOT / "docs" / "revision" / "PHASE3_ORDER_SAFETY_CHECKPOINT.json"
CHECKPOINT_ID = "ORDER_SAFETY_CHECKPOINT_V1"
VERDICTS = {"A": "VASOACTIVE_ORDER_EXECUTION_SAFETY_BOUNDARY_CLOSED", "B": "HIGH_RISK_ORDER_GAPS_FIXED_WITH_LOW_RISK_SEMANTICS_DEFERRED", "C": "DRUG_RATE_ATTRIBUTION_REQUIRES_GENERIC_ORDER_REDESIGN",
            "D": "HISTORICAL_RECONSTRUCTION_BLOCKS_SOURCE_FIX", "E": "NEW_MATERIAL_ORDER_EXECUTION_SAFETY_DEFECT_FOUND"}
GENERATED_ON = "2026-11-21"
#: The closure audit of the limitations of the previous cycle (TD-161) and of what the independent review added. Exactly one status each.
CLOSED, MITIGATED, DEFERRED = "CLOSED", "MITIGATED_BY_DEFENSE_IN_DEPTH", "INTENTIONALLY_DEFERRED"
CLOSURE_AUDIT = {
    "L-1": (CLOSED, "an adjustment named by its role runs only in a unit a vasoactive infusion runs in (reader drops the number; pipeline rule on structured forms); mL/h on nitroglycerin no longer runs as mcg/min"),
    "L-2": (CLOSED, "a rate belongs to at most one drug, structurally (the drug named just before it through dose connectors, or 'of <drug>' after it); a foreign or unclaimed rate holds the whole piece; the "
                    "recognition of other medicines is a closed list (L-11)"),
    "L-3": (CLOSED, "a stop governs a vasoactive only if the verb governs its name; never inherited by a piece that says more, never through an exception (which also ends the stop for the pieces after it), "
                    "never chosen by priority between two infusions named in one piece"),
    "L-4": (CLOSED, "the '/min' of a vasoactive rate unit (and the word 'infusion' naming it) is not a duration; the generic time phrases of the common time system are not part of this (L-12)"),
    "L-5": (CLOSED, "'restart <drug>' with no explicit rate is the approved incomplete-rate question; the previous rate is never reused"),
    "L-6": (CLOSED, "'continue <drug> at 12' is the approved incomplete-rate question; '... at 12 mcg/min' is valid"),
    "L-7": (MITIGATED, "the pipeline barrier reads rate_mcg_min; each barrier of a target-as-rate or incomplete-rate order protects alone (proven with the other removed, and by mutants)"),
    "L-8": (CLOSED, "an answer is ONE rate with its unit, for the drug that asked, with no time to wait for, on the family path and on the legacy page path; units are taken from nothing but what was written"),
    "L-9": (MITIGATED, "nitroglycerin is no longer protected by the source alone: the pipeline barrier reads rate_mcg_min and requires the number to be written with its unit in the drug's clauses"),
    "L-10": (DEFERRED, "an isolated held order is held per turn and there is no recovery of malformed orders (FD-ORDER-09: PERMANENT_FAIL_CLOSED stays)"),
    "L-11": (DEFERRED, "the recognition of other medicines (and of the other names of the four infusions) is a CLOSED list; an unlisted medicine beside an infusion's only rate literal is not seen"),
    "L-12": (DEFERRED, "time phrases the common time system does not recognise ('despues de', 'luego de', 'in 5 minutes,' with a comma, 'wait 5 minutes then', 'in five minutes', 'later') run a vasoactive order at once, "
                       "like every other order"),
    "L-13": (DEFERRED, "a ceiling, step or baseline ('to MAP 65 max 20 mcg/min') is executed as the rate: a clinical-semantics decision"),
    "L-14": (DEFERRED, "'... to 12 mcg/min to reach MAP 65 in 10 minutes' is a plan (nothing runs); a valid single-rate order with a non-dose word and another medicine in the piece is asked"),
    "L-15": (DEFERRED, "a non-stop piece that names two infusions reads the first by the reader's priority ('start norepinephrine while dobutamine runs' asks for dobutamine's rate); 'stop X then Y' stops Y; 'restart X in 5 "
                       "minutes' is asked; 'levophed 12' and 'epi 12' are not read; 'nor-epi' is asked; '2 mcg/min more' is read as absolute"),
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_checkpoint(certification: dict, adversarial_review: dict, *, sequence: list, facts: dict | None = None, verdict: str = "B") -> dict:
    """The checkpoint record of the cycle. Exactly one verdict. With B: every demonstrated high-risk order semantic is closed and certified (the eight limitations of the previous cycle and the material findings of
    the independent review), the freeze of the reader was lifted a second time and narrowly, the three readers stay reconstructable byte for byte and nothing sealed was rewritten; what remains is declared, with
    its exact shape, as low-risk semantics that need a faculty decision."""
    assert verdict in VERDICTS
    successor = json.loads(build.RECORD_PATH.read_text(encoding="utf-8"))
    body = {"record_type": "ORDER_SAFETY_CHECKPOINT", "version": CHECKPOINT_ID, "decision_reference": "FD-ORDER-01 to FD-ORDER-11", "evidence_class": "MODEL_ANALYSIS",
            "statement": ("The demonstrated order semantics that could execute the wrong vasoactive rate, attribute another drug's rate, stop the wrong infusion, make an incomplete order executable or bypass the defense in "
                          "depth are closed: a rate and a stop belong to one drug (structurally, with no nearest-number heuristic), the unit is required and compatible with the drug, the '/min' of a rate unit is not a "
                          "duration, a restart or a continue with no rate with its unit is the approved incomplete-rate question, the pipeline barrier reads rate_mcg_min so each barrier of nitroglycerin protects "
                          "alone, and an answer is one rate with its unit for the drug that asked. The reader freeze was lifted a second time, narrowly: the reader of the first successor and the reader of the Phase-2 "
                          "closure are rebuilt byte for byte from the live one, every Phase-2 digest recomputes from the closure reader, the calibration freeze moved in exactly one component and nothing sealed was "
                          "rewritten. One independent adversarial review found 17 behaviors; the material ones (two of them regressions of this very change) were reproduced and repaired and the rest are declared. "
                          "What remains is low-risk semantics that needs a faculty decision, listed with its exact shape."),
            "verdict": verdict, "verdict_name": VERDICTS[verdict], "verdicts": VERDICTS,
            "why_not_the_others": {"A": "not every limitation is closed: the closed-list recognition of other medicines, the generic time phrases, the ceiling/step/baseline number and the two-infusion non-stop piece remain, "
                                       "each declared with its shape" if verdict != "A" else "this is the verdict",
                                   "B": "this is the verdict" if verdict == "B" else "the conditions of B do not hold",
                                   "C": "the demonstrated gaps were closed with structural rules inside the existing order language; a generic medication-recognition redesign is the only thing that would close L-11 and it is "
                                        "not needed to close what was demonstrated",
                                   "D": "the historical reconstruction is exact for both successions: the git blob and SHA-256 of the closure reader and of the first successor are reproduced, every recorded closure digest recomputes "
                                        "with the reader of its time and no sealed record changed",
                                   "E": "every material defect the review found was reproduced and repaired inside this package; no unrepaired material order-execution defect remains: what remains needs a faculty decision on clinical "
                                        "semantics and is declared"},
            "closure_audit": {key: {"status": status, "note": note} for key, (status, note) in CLOSURE_AUDIT.items()},
            "facts": {"successor_record_digest": successor["record_digest"], "reader": {"historical_git_blob": rsu.HISTORICAL_GIT_BLOB, "target_safety_git_blob": rsu.TARGET_SAFETY_GIT_BLOB,
                                                                                         "successor_git_blob": rsu.SUCCESSOR_GIT_BLOB, "hunks_first_succession": len(rsu.REVERSAL),
                                                                                         "hunks_second_succession": len(rsu.REVERSAL_ORDER_SAFETY)},
                      "calibration_freeze_components_that_moved": successor["freeze"]["calibration"]["components_that_moved_in_this_succession"],
                      "scenario_inputs_identical": successor["freeze"]["calibration"]["scenario_inputs_identical"],
                      "closure_freeze_digests_recompute": successor["freeze"]["closure_freeze_digests"]["equal"],
                      "executable_files_changed": ["family_parser.py", "order_pipeline.py", "time_semantics.py", "pending_family_orders.py", "app.py", "reader_succession.py"],
                      "executable_files_not_changed": ["family_engine.py", "active_order_context.py", "shared_order_language.py", "shared_order_quantities.py", "weight_based_doses.py", "runtime_shadow.py",
                                                       "runtime_tone_support.py", "clinical_core/"],
                      "core_digest": build.generating_code()["clinical_core"],
                      **(facts or {})},
            "confirmations": {"no_tone_recalibration": True, "no_pump_coupling_change": True, "no_physiology_change": True, "no_parameter_selected": True, "no_norepinephrine_authority_expansion": True,
                              "no_consciousness_authority": True, "no_terminal_authority": True, "no_resident_deployment": True, "no_clinical_validation_claim": True, "no_weight_based_dosing": True,
                              "no_map_target_titration": True, "no_new_drug": True, "no_malformed_order_recovery": True, "no_shadow_boundary_change": True, "no_sealed_record_rewritten": True,
                              "no_clinical_core_edit": True, "common_core_runtime_authority": False},
            "limitations": [f"{key}: {note}" for key, (status, note) in CLOSURE_AUDIT.items() if status == DEFERRED] + ["the new records have no signature (the same limit as TD-153 item 7)"],
            "certification": certification, "adversarial_review": adversarial_review, "sequence": sequence,
            "next_human_action": ("Return to the authority and simulator-development line. A faculty member decides, only if and when it is wanted, in order of value: (1) whether a ceiling, step or baseline written beside a "
                                  "target is a rate (L-13); (2) whether generic medication recognition replaces the closed list (L-11); (3) how the common time system reads the remaining time phrases (L-12). Nothing else is "
                                  "to be done on order parsing until then."),
            "open_faculty_decisions": ["ceiling/step/baseline numbers beside a target (L-13)", "generic medication recognition instead of a closed list (L-11)", "the remaining time phrases of the common time system (L-12)",
                                       "retire the legacy numeric reply of the page, if it is not conducted (kept closed by this package)"]}
    parts = {"clinical_core": build.generating_code()["clinical_core"], "successor_record_digest": successor["record_digest"], "family_parser.py": _sha(ROOT / "family_parser.py"),
             "order_pipeline.py": _sha(ROOT / "order_pipeline.py"), "time_semantics.py": _sha(ROOT / "time_semantics.py"), "pending_family_orders.py": _sha(ROOT / "pending_family_orders.py"),
             "app.py": _sha(ROOT / "app.py"), "reader_succession.py": _sha(ROOT / "reader_succession.py"),
             "test_phase3_order_safety_hardening.py": _sha(ROOT / "test_phase3_order_safety_hardening.py"), "test_order_safety_hardening_checkpoint.py": _sha(Path(__file__).resolve())}
    body["provenance"] = hr.provenance(record_id=CHECKPOINT_ID, generating_code=parts, generated_on=GENERATED_ON, grant_id="GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V3",
                                       source_data={"verdict": verdict, "certification": certification, "adversarial_review": adversarial_review, "sequence": sequence})
    return hr.seal(body)


def write_checkpoint(certification: dict, adversarial_review: dict, *, sequence: list, facts: dict | None = None, verdict: str = "B") -> dict:
    return {str(CHECKPOINT_PATH.relative_to(ROOT)): hr.write(CHECKPOINT_PATH, build_checkpoint(certification, adversarial_review, sequence=sequence, facts=facts, verdict=verdict))}
