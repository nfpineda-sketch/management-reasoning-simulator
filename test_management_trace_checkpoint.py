"""P3-517: the CHECKPOINT of the end-to-end GI management trace with the live GI pressure and manual norepinephrine development authority (a tool, never imported by a page; it holds no test).

The checkpoint is written ONCE, after the certification, as a sealed, versioned, indexed historical record with exactly ONE verdict of the six the faculty named. It is a different file from the tests of the
trace so that writing it never changes the generating code those files name.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import development_management_trace as mt
import faculty_management_review as fmr
import historical_records as hr

ROOT = Path(__file__).resolve().parent
CHECKPOINT_PATH = ROOT / "docs" / "revision" / "PHASE3_GI_MANAGEMENT_TRACE_CHECKPOINT.json"
CHECKPOINT_ID = "GI_MANAGEMENT_TRACE_CHECKPOINT_V1"
VERDICTS = {"A": "GI_END_TO_END_MANAGEMENT_TRACE_READY_FOR_HUMAN_REVIEW", "B": "GI_MANAGEMENT_TRACE_BLOCKED_BY_SOURCE_CONTROL_BOUNDARY", "C": "ENCOUNTER_TIMING_REQUIRES_FACULTY_DECISION",
            "D": "TRACE_EXTRACTION_NOT_CAUSALLY_RELIABLE", "E": "LIVE_AUTHORITY_INTEGRATION_REVEALS_BROADER_ARCHITECTURE_GAP", "F": "EDUCATIONAL_SAFETY_AUDIT_FOUND_MATERIAL_MISLEADING_BEHAVIOR"}
GENERATED_ON = "2026-11-22"
GRANT_ID = "GI_NOREPINEPHRINE_DEVELOPMENT_AUTHORITY_GRANT_V1"
#: What the cycle found before the certification (each reproduced BEFORE it was repaired) and what became of it: the package's own test findings and the independent review's.
REVIEW_FINDINGS = {
    "T1": ("MATERIAL_TEST_SIDE", "REPAIRED", "the development runner left the live-authority flags in the process environment, so every later test of the same process ran under the live authority; the runner now "
                                             "restores the environment and a test pins it"),
    "T2": ("MATERIAL_TEST_SIDE", "REPAIRED", "the module-scoped page fixture inherited the suite's session-wide historical reconstruction, so the real page opened no authority; it now declares the ordinary configuration"),
    "M1": ("MATERIAL", "REPAIRED", "a priority the page COMPOSED from other words (on the real page, from the gate's answer) was shown as the resident's: the trace now reads the page's own slot provenance, a composed "
                                   "slot is NOT_EXPRESSED with a note, a slot from another moment keeps its label, and the transcript the page appends after its gate is no longer part of the action"),
    "M2": ("MATERIAL", "REPAIRED", "'Consult GI.' and the interventional-radiology request were recorded-not-modelled and the encounter went on for two hours: every request for definitive control is now the boundary, "
                                   "whatever the ledger did with it"),
    "M3": ("MATERIAL", "REPAIRED", "the authored arrival pressure was labelled a live-authority observation after a turn that does not move the clock: the state now carries its provenance and the chain is checked"),
    "M4": ("MATERIAL", "REPAIRED", "the stored review set named a generating code that was not in the tree: regenerated with the final code; a test requires same_generating_code"),
    "N1": ("MINOR", "REPAIRED", "exit order: an authority stop before a request read as the request, and a stop in the same turn was hidden; the earliest exit in time is the boundary and the others of the turn are named"),
    "N2": ("MINOR", "REPAIRED", "the engine-haemostasis and terminal exits reused other messages; each has its own words, and a turn crossing the horizon says so"),
    "N3": ("MINOR", "REPAIRED", "a minute the authority committed and then disowned counted as an observation; it no longer does"),
    "N4": ("MINOR", "REPAIRED", "the turn rule was labelled OBSERVED; it is MODEL_DERIVED"),
    "N5": ("MINOR", "REPAIRED", "every path began with 'Place an IV line.', which the ledger ignored as already done (an action that did not fit the state); removed"),
    "N6": ("MINOR", "REPAIRED", "the purposes of F, H and I stated the conclusion Q6 asks for; rephrased neutrally"),
    "N7": ("MINOR", "REPAIRED", "the set stored traces but not their inputs; each path now carries its turns and the artifact view the extraction reads, and a test re-extracts every trace from the record alone"),
    "N8": ("MINOR", "DECLARED_NOT_REPAIRED", "on a scripted path every block says the resident expressed no reasoning; the screen's note explains it"),
}
LIMITATIONS = [
    "H1: in the LIVE resident page a gastroenterology consultation leads to an engine endoscopy and the common core's EndoscopicHemostasis, never reviewed; this package ends its own encounter at the request and "
    "does not change the live page (a faculty decision)",
    "H2: the resident-visible mental status and heart rate of the live page come from the legacy engine and, under norepinephrine, are decoupled from the authority pressure (CONSCIOUSNESS_UNDER_TONE_UNRESOLVED); "
    "the trace and the review show neither",
    "turn semantics: without a stated interval 2 units of red cells occupy 60 minutes in which the resident cannot act; the pressure is observed only at the end of a turn",
    "the paths are SCRIPTED development paths: their actions are AUTHORED, no resident reasoning is exercised by the review; only one page test exercises the reasoning gate",
    "the categories (reasonable, temporizing, incomplete, clearly nonbeneficial) and the 120-minute horizon are PROPOSALS for the faculty review",
    "in gi_bleed_72f the hypotension does not recur before minute 120, so the state-contingent vasopressor steps are not given; that case is not in the review",
    "a request for definitive control is recognized by the words of the order (gastroenterology, endoscopy, interventional radiology, embolization, surgery); a negated mention also ends the encounter "
    "(the conservative direction); a phrasing outside that list is not recognized",
    "the review set and this record have no signature (the same limit as TD-153 item 7)",
]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


GENERATING_FILES = ("development_management_trace.py", "faculty_management_review.py", "faculty_management_review_ui.py", "faculty_trajectory_review.py", "faculty_review_ui.py", "app.py",
                    "test_gi_management_trace_paths.py", "test_phase3_management_trace.py", "test_phase3_management_review_page.py", "test_phase3_management_trace_page.py")


def build_checkpoint(certification: dict, adversarial_review: dict, *, sequence: list, facts: dict | None = None, verdict: str = "A") -> dict:
    """The checkpoint record of the cycle. Exactly one verdict. With A: one development GI encounter whose management trace is extracted from its events, ten paths through the live development authority
    with every pressure a committed authority minute, a development boundary before definitive haemostasis, resident reasoning only as expressed, the ten misleading lessons attacked without a material
    implication, and an interactive faculty review of the ten paths ready for a human reviewer."""
    assert verdict in VERDICTS
    loaded = fmr.load_set()
    definition = mt.encounter_definition()
    body = {"record_type": "GI_MANAGEMENT_TRACE_CHECKPOINT", "version": CHECKPOINT_ID, "decision_reference": "FD-MTRACE-01 to FD-MTRACE-10", "evidence_class": "MODEL_ANALYSIS",
            "statement": ("One DEVELOPMENT GI haemorrhagic-shock encounter (gi_bleed_57m, gi_bleed_72f) runs the live development pressure authority with the manual norepinephrine control exactly as published, "
                          f"under {GRANT_ID}. Ten scripted management paths from the same arrival, their categories proposed for the faculty review, show that different decisions give causally different "
                          "trajectories and the same decisions the same one. Each encounter is read as a management trace (state, priority, action, expected effect, observed response, reassessment, new state) "
                          "extracted from its own events, every value with one provenance, the resident's reasoning only as expressed, every pressure a committed authority minute, and a development boundary "
                          "before definitive control of the bleeding that never means cure, bleeding stopped, management complete or safe discharge. No physiology, calibration, grant, snapshot, reader or "
                          "clinical_core/ source was changed. The human review has NOT been done."),
            "verdict": verdict, "verdict_name": VERDICTS[verdict], "verdicts": VERDICTS,
            "why_not_the_others": {"A": "this is the verdict" if verdict == "A" else "the conditions of A do not hold",
                                   "B": "the source-control boundary is represented conservatively (the first definitive request ends the development encounter and nothing after it is observed) and no path needs "
                                        "haemostasis; that the live page REACHES an unreviewed engine haemostasis (H1) is a declared faculty decision, not a blocker of this package",
                                   "C": "the timing is the engine's own deterministic rule (a stated interval governs the turn, otherwise the longest administration; at most 120 minutes a step) and every path states its "
                                        "interval; the declared artefacts (the transfusion hour, observation at turn end) do not change any path's reading",
                                   "D": "every trace re-extracts identically from its persisted turns, artifact and arrival; every pressure is a committed authority minute bound by its candidate digest; the causal "
                                        "relations hold by test; a tampered trace, an invented reasoning or a substituted action is refused",
                                   "E": "the runner is the page's own order path plus the certified authority hooks, and a test on the REAL page gives the same pressures for the same orders; nothing parallel was built",
                                   "F": "the ten misleading lessons are attacked by test on the paths, the traces and the review screens without a material implication; mental status, consciousness and heart rate "
                                        "are not shown; the categories appear only in the final summary"},
            "facts": {"encounter": {"id": definition["id"], "definition_digest": definition["definition_digest"], "cases": list(mt.CASES), "horizon_min": mt.HORIZON_MIN,
                                    "horizon_provenance": definition.get("horizon_provenance"), "boundary_provenance": definition.get("boundary_provenance")},
                      "trace": {"schema": mt.SCHEMA, "version": mt.VERSION, "record_type": mt.RECORD_TYPE},
                      "review_set": {"id": fmr.SET_ID, "path": str(fmr.SET_PATH.relative_to(ROOT)), "digest": loaded["digest"], "pinned": fmr.PINNED_SET_DIGEST, "file_sha256": _sha(fmr.SET_PATH),
                                     "scenarios": list(fmr.SCENARIOS), "extra_questions": list(fmr.EXTRA_QUESTIONS), "operator_flag": "MRS_FACULTY_MANAGEMENT_GATE"},
                      "authority": {"grant": GRANT_ID, "pressure_snapshot": "GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1", "tone_snapshot": "COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1",
                                    "common_core_runtime_authority": False},
                      "executable_files_added": ["development_management_trace.py", "faculty_management_review.py", "faculty_management_review_ui.py"],
                      "executable_files_changed": ["faculty_trajectory_review.py (the extra question Q6)", "faculty_review_ui.py (the launcher mode and hold)", "app.py (the wiring)"],
                      "executable_files_not_changed": ["clinical_core/", "family_parser.py", "family_engine.py", "active_order_context.py", "order_pipeline.py", "runtime_authority.py", "runtime_ne_authority.py",
                                                       "runtime_ne_grant.py", "runtime_pressure_grant.py", "runtime_pressure_snapshot.py", "runtime_tone_snapshot.py", "runtime_tone_support.py",
                                                       "runtime_shadow.py", "runtime_shadow_families.py"],
                      **(facts or {})},
            "review_findings": {key: {"class": cls, "outcome": outcome, "note": note} for key, (cls, outcome, note) in REVIEW_FINDINGS.items()},
            "confirmations": {"no_new_physiology": True, "no_source_control_implementation": True, "no_gi_recalibration": True, "no_tone_recalibration": True, "no_parser_work": True,
                              "no_pump_limited_authority_expansion": True, "no_consciousness_authority_expansion": True, "no_terminal_authority_expansion": True, "no_resident_deployment": True,
                              "no_clinical_validation_claim": True, "no_clinical_core_edit": True, "no_reader_edit": True, "no_grant_or_snapshot_change": True, "no_sealed_record_rewritten": True,
                              "human_review_done": False, "common_core_runtime_authority": False},
            "limitations": list(LIMITATIONS),
            "certification": certification, "adversarial_review": adversarial_review, "sequence": sequence,
            "next_human_action": ("A faculty member signs in to the faculty development review (the launcher lands on 'Management trace review (GI paths)' once the earlier reviews are done) and reviews the ten "
                                  "paths, one screen each: Q1 to Q6, the lock, the overall judgment and the submit; the summary after the tenth shows the proposed categories and the limitations. Separately, and "
                                  "only if wanted: decide H1 (the live page reaches an unreviewed engine haemostasis through a gastroenterology consultation) and H2 (the resident-visible mental status under "
                                  "norepinephrine). Nothing else is to be built on this line until then."),
            "open_faculty_decisions": ["the human review of the ten management paths", "H1: block, flag or review the engine haemostasis the live page reaches", "H2: the resident-visible mental status under norepinephrine",
                                       "the 120-minute development horizon and the proposed categories"]}
    parts = {name: _sha(ROOT / name) for name in GENERATING_FILES}
    parts["review_set"] = _sha(fmr.SET_PATH)
    parts["test_management_trace_checkpoint.py"] = _sha(Path(__file__).resolve())
    body["provenance"] = hr.provenance(record_id=CHECKPOINT_ID, generating_code=parts, generated_on=GENERATED_ON, grant_id=GRANT_ID,
                                       source_data={"verdict": verdict, "certification": certification, "adversarial_review": adversarial_review, "sequence": sequence})
    return hr.seal(body)


def write_checkpoint(certification: dict, adversarial_review: dict, *, sequence: list, facts: dict | None = None, verdict: str = "A") -> dict:
    return {str(CHECKPOINT_PATH.relative_to(ROOT)): hr.write(CHECKPOINT_PATH, build_checkpoint(certification, adversarial_review, sequence=sequence, facts=facts, verdict=verdict))}
