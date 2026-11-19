"""P3-448: the CHECKPOINT of the norepinephrine titration review (a tool, never imported by a page; it holds no test).

The checkpoint is written ONCE, after the certification, as a sealed, versioned, indexed historical record with exactly ONE verdict of the five the faculty named. It is a different file from the builder of the set
(``test_titration_review_analysis``) so that writing it never changes the generating code the set's provenance names.
"""
from __future__ import annotations

import json
from pathlib import Path

import faculty_titration_review as ftt
import historical_records as hr
import test_titration_review_analysis as build

ROOT = Path(__file__).resolve().parent
CHECKPOINT_PATH = ROOT / "docs" / "revision" / "PHASE3_NOREPINEPHRINE_TITRATION_V1_REVIEW_CHECKPOINT.json"
CHECKPOINT_ID = "NOREPINEPHRINE_TITRATION_V1_REVIEW_CHECKPOINT_V1"
VERDICTS = {"A": "NOREPINEPHRINE_TITRATION_REVIEW_READY_FOR_HUMAN_USE", "B": "CORE_TITRATION_SCENARIOS_READY_BUT_RESTART_EXCLUDED", "C": "REVIEW_UI_READY_BUT_PERSISTENCE_NOT_CERTIFIED",
            "D": "BLINDNESS_LEAK_FOUND", "E": "CERTIFIED_TRAJECTORY_SOURCE_MISMATCH"}
GENERATED_ON = "2026-11-19"


def build_checkpoint(certification: dict, adversarial_review: dict, *, sequence: list, facts: dict | None = None, verdict: str = "A") -> dict:
    """The checkpoint record of the cycle. Exactly one verdict. With A, all five scenarios (including the restart) are in the set, persistence is certified, no blindness leak was found and every trajectory equals its
    certified source; each of the other four names the reason it is not the verdict."""
    assert verdict in VERDICTS
    record = json.loads(ftt.SET_PATH.read_text(encoding="utf-8"))
    audit = record["audit"]
    body = {"record_type": "NOREPINEPHRINE_TITRATION_REVIEW_CHECKPOINT", "version": CHECKPOINT_ID, "decision_reference": "FD-TITREV-01 to FD-TITREV-13", "evidence_class": "MODEL_ANALYSIS",
            "statement": ("The faculty review of the explicit norepinephrine rate-change semantics is ready for a human reviewer: five scenarios of ONE gastrointestinal hemorrhage case (an increase, a decrease, a stop, a "
                          "sequence of changes and a restart) with the CENTER_REFERENCE trajectories exactly as the certified titration probes hold them, each change of the rate marked on the graph, the faculty's own question for "
                          "each scenario, Q1 to Q5, the lock, the overall judgment, automatic move to the next scenario, persistence that survives a refresh, and a final summary that states the current limitations. The human review "
                          "has NOT been done; nothing about physiology, parameters, trajectories or authority changed."),
            "verdict": verdict, "verdict_name": VERDICTS[verdict], "verdicts": VERDICTS,
            "why_not_the_others": {"A": "this is the verdict" if verdict == "A" else "not all conditions of A hold",
                                   "B": "the restart (TIT-5) IS in the set: its deterministic trajectory was already certified (the restart probe), so no new code and no new physiology were needed and nothing was excluded",
                                   "C": "persistence is certified: autosave, an irreversible lock, a refresh that restores answers, comment, lock, overall judgment and progress, one record per scenario, a lock from an out-of-date screen locks "
                                        "nothing, a forged or altered log is unreadable, and a record that does not verify is not counted",
                                   "D": "no first-pass screen, element, chart specification, session key, file read, forged route or websocket message carried the configuration, another setting, a parameter, the writer or the rate "
                                        "history, an earlier trajectory or judgment, the comparator, heart rate, capillary refill or a limitation before the summary",
                                   "E": "every scenario equals its certified source: the stored per-minute series of the certified probe, equal to what the certified harness call produces today, with the orders and the rate history of the "
                                        "faculty's plan"},
            "facts": {"set_id": record["set_id"], "set_record_digest": record["record_digest"], "order": record["order"], "witness": audit["witness"], "excluded": audit["selection"]["excluded"],
                      "not_included": audit["selection"]["not_included"], "probes": build.PROBES, "limitations_shown_only_in_the_final_summary": [entry["id"] for entry in record["limitations"]], **(facts or {})},
            "confirmations": {"no_tone_recalibration": True, "no_pump_coupling_change": True, "no_physiology_change": True, "no_parameter_selected": True, "no_witness_substituted": True,
                              "no_norepinephrine_authority_expansion": True, "no_consciousness_authority": True, "no_terminal_authority": True, "no_resident_deployment": True, "no_clinical_validation_claim": True,
                              "no_weight_based_dosing": True, "no_map_target_titration": True, "no_new_vasopressor": True, "human_review_not_performed": True, "common_core_runtime_authority": False},
            "limitations": ["the human review has not been done", "one witness (CENTER_REFERENCE): no LOW/HIGH run of these histories, and the review neither shows nor asks for one",
                            "explicit absolute mcg/min only; an order that closes the modelled infusion is not recovered later in that encounter (TD-158)",
                            "heart rate and capillary refill are not shown (not recomputed for these trajectories); consciousness under tone and pump dependence stay open and do not block this review",
                            "the pressure axis is 0 to 140 mmHg, as in the earlier reviews: responses of 10 to 20 mmHg read as small changes on the graph; the table gives the numbers",
                            "the launcher offers only this review until its five scenarios are submitted and verified (MRS_FACULTY_TITRATION_GATE=off releases it for the operator); the re-review and tone holds keep their precedence",
                            "the set record has no signature (the same limit as TD-153 item 7)"],
            "certification": certification, "adversarial_review": adversarial_review, "sequence": sequence,
            "next_human_action": ("A faculty reviewer performs the five-scenario review (about 20 minutes) and says whether the explicit norepinephrine rate-change semantics -- onset while the rate rises, offset while it falls -- "
                                  "are plausible enough for DEVELOPMENT. Nothing else is to be done until then."),
            "open_faculty_decisions": ["the result of the human review", "whether the shadow should mirror the engine's SETTLED order (so that 'stop the infusion' is followed), with the legacy 'MAP 65' defect settled first (TD-158)",
                                       "whether the first refused order should keep closing the infusion for the rest of the encounter", "whether the negative-control scenario is ever built into the application",
                                       "whether the pump-dependence and consciousness limitations need work before any educational use"]}
    parts = {"clinical_core": build.generating_code()["clinical_core"], "set_record_digest": record["record_digest"], "test_titration_review_checkpoint.py": build._sha(Path(__file__).resolve())}
    body["provenance"] = hr.provenance(record_id=CHECKPOINT_ID, generating_code=parts, generated_on=GENERATED_ON, grant_id="GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V3",
                                       source_data={"set_record_digest": record["record_digest"], "verdict": verdict, "certification": certification, "adversarial_review": adversarial_review, "sequence": sequence})
    return hr.seal(body)


def write_checkpoint(certification: dict, adversarial_review: dict, *, sequence: list, facts: dict | None = None, verdict: str = "A") -> dict:
    return {str(CHECKPOINT_PATH.relative_to(ROOT)): hr.write(CHECKPOINT_PATH, build_checkpoint(certification, adversarial_review, sequence=sequence, facts=facts, verdict=verdict))}
