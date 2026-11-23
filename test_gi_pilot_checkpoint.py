"""P3-533: the CHECKPOINT of the controlled development pilot readiness of the GI management trace (a tool, never imported by a page; it holds no test).

The checkpoint is written ONCE, after the certification, as a sealed, versioned, indexed historical record with exactly ONE verdict of the six the faculty named. It is a different file from the
pilot's tests so that writing it never changes the generating code those files name.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import gi_pilot as gp
import historical_records as hr
import test_gi_pilot_records as records

ROOT = Path(__file__).resolve().parent
CHECKPOINT_PATH = ROOT / "docs" / "revision" / "PHASE3_GI_PILOT_READINESS_CHECKPOINT.json"
CHECKPOINT_ID = "GI_PILOT_READINESS_CHECKPOINT_V1"
VERDICTS = {"A": "GI_MANAGEMENT_TRACE_READY_FOR_SMALL_CONTROLLED_RESIDENT_PILOT", "B": "PILOT_BLOCKED_BY_SOURCE_CONTROL_BOUNDARY", "C": "RESIDENT_VISIBLE_STATE_NOT_SAFE",
            "D": "TRACE_NOT_READY_FOR_RESIDENT_FEEDBACK", "E": "FACULTY_SUPERVISION_NOT_CERTIFIABLE", "F": "PILOT_REQUIRES_BROADER_ARCHITECTURE_WORK"}
GENERATED_ON = "2026-11-23"
GRANT_ID = "GI_NOREPINEPHRINE_DEVELOPMENT_AUTHORITY_GRANT_V1"

#: What the cycle found before the certification (each reproduced BEFORE it was repaired or declared) and what became of it. Filled from the cycle's own tests and the one independent review.
REVIEW_FINDINGS = {
    # the cycle's own dry runs and tests, before the independent review
    "T1": ("MATERIAL_FINDING", "DECLARED_NOT_REPAIRED", "after the first committed minute the certified authority halts the encounter permanently on a zero-minute turn that is not purely "
                                                         "structural (MINUTE_ALREADY_COMMITTED): reproduced on the base 352d5fe without the pilot; it decides the verdict (architecture_finding)"),
    "T2": ("MATERIAL_TEST_SIDE", "REPAIRED", "the stored authority artifact did not verify or replay because a read-only mapping was stringified; the pilot record now keeps plain JSON data"),
    "T3": ("MATERIAL", "REPAIRED", "a faculty stop could arrive after a pending submission had already run; the pilot check now runs before it and a submission to an ended pilot encounter is blocked"),
    "T4": ("MATERIAL", "REPAIRED", "the examination text showed the earlier model's mental status after norepinephrine; it is now classified or withheld like the other surfaces"),
    "T5": ("MINOR", "REPAIRED", "the pilot's secret reader bypassed the offline rule's guard (test_offline_cases); it now uses the project's resolver"),
    "T6": ("MINOR", "DECLARED_NOT_REPAIRED", "the construct's verifier over-rejects the carried reading of a turn without advance; the pilot tolerates exactly that case (TD-165 item 3)"),
    "T7": ("MINOR", "DECLARED_NOT_REPAIRED", "the earlier encounter page's buttons 'Save & return to dashboard' and 'End this attempt without completing review' stay visible after a pilot "
                                             "encounter; without an account attempt they write nothing"),
    # the one independent review (P3-531), each material finding reproduced BEFORE it was repaired and pinned by a test that a mutant fails
    "F1": ("MATERIAL", "REPAIRED", "a participant who chose Spanish read the earlier model's mental status after norepinephrine (the page translated the event before the pilot "
                                   "classified it): the pilot is presented in English and the classification runs on the English words before any translation (test_p17; two mutants)"),
    "F2": ("MATERIAL", "REPAIRED", "a second tab of the same participant recorded the first encounter INTERRUPTED while it kept running orders out of faculty control: an encounter the "
                                   "record no longer shows ACTIVE ends on its next run with ENCOUNTER_CLOSED_IN_RECORD before the pending order (test_p18; mutant)"),
    "F3": ("MATERIAL", "REPAIRED", "races inside the one process: the store's write check shared one name per process, and appends read and wrote without a lock (a forked faculty "
                                   "chain made every later stop unrecordable): the check is unique per call and an append is one serialized, locked step (test_u19; two mutants)"),
    "F4": ("MATERIAL", "REPAIRED", "with the image bank 'on' in the secrets and 'off' in the environment the pilot did not refuse: every source that sets it must say off (test_u2, test_p19)"),
    "F5": ("MINOR", "REPAIRED", "the first-pilot flags and the faculty review flag held only in the secrets did not refuse the pilot; they do now (test_u2)"),
    "F6": ("MINOR", "REPAIRED", "without the authority record directory every encounter opened and closed as AUTHORITY_UNAVAILABLE; the pilot now refuses before it starts (test_u2)"),
    "F7": ("MINOR", "DECLARED_NOT_REPAIRED", "the hash chain has no key and the replay review does not verify the meta or the orders against the artifact (TD-165 item 9)"),
    "F8": ("MINOR", "REPAIRED", "internal ledger tokens ('unread', 'plan:future_timed', 'held_with_question') were shown on the participant trace; the participant's own words are (test_u20)"),
    "F9": ("MINOR", "DECLARED_NOT_REPAIRED", "the pseudonym is recoverable to the account id by enumerating small ids (TD-165 item 8)"),
    "F10": ("MINOR", "DECLARED_NOT_REPAIRED", "the procedure_events check of engine_source_control is dead code; the consultation and endoscopy checks suffice (TD-165 item 16)"),
    "F11": ("MINOR", "DECLARED_NOT_REPAIRED", "an abandoned encounter stays ACTIVE in the record until the same participant starts another; a faculty stop on it has no session to act on (TD-165 item 13)"),
    "S1": ("SUSPECTED_NOT_REPRODUCED", "DECLARED_NOT_REPAIRED", "in Talk mode whether the patient can speak derives from the earlier model's mental status (TD-165 item 14)"),
    # P3-532: what the first full certification run found (it failed; the candidate was repaired and certified again on a new fingerprint)
    "C1": ("MATERIAL", "REPAIRED", "the pilot crossed declared isolation guards: it imported the authority, its store and the shadow (only app.py may), reached the common core by a path "
           "that is not a declared crossing (through runtime_pressure_snapshot) and read the mental-status field to relabel it (a new, uninventoried reader); and a hook in "
           "_vitals_grid_html broke regression_v082_persistent_vitals, which executes that function alone. Now the pilot imports nothing of the layer (app.py, the page's one "
           "crossing, hands it a narrow Layer, as it hands the faculty review pages theirs), its mental-status filters are text transforms that read no field, and "
           "_vitals_grid_html is self-contained (test_u22, test_u23, test_u24)"),
    "C2": ("MINOR", "DECLARED_ADAPTATION", "test_phase3_tone_review_records::test_c2 lists the two pilot modules among the modules that did not exist when the tone review set was generated, "
           "exactly as it already lists the later titration and management-trace modules; test_phase3_gi_preauthority_review::test_review_two_limits counts the pilot's Layer as a "
           "third call of the page's helper _runtime_authority_site (pinned inside the pilot's flag block; the two page routes are unchanged)"),
    "C3": ("PRE_EXISTING_TEST_NONDETERMINISM", "REPAIRED_IN_THE_TEST_HARNESS", "test_phase3_minute_validation::test_r2 saw one scenario more halted (23, 11 instead of 24, 10) in the "
           "first run only; it did not reproduce alone or in its partition's exact order. Cause: the series harness (test_runtime_authority_series) named an experiment by id(self) and "
           "both series of the module share one create-only store; a reused heap address collided with different content, the store refused it and the authority halted "
           "(ARTIFACT_PERSISTENCE_FAILED). A probe that reuses the id reproduces exactly that halt; the harness now names experiments by a per-process counter (nothing pins the names)"),
    "C4": ("ENVIRONMENTAL", "RE_RUN", "two AppTest scripts timed out after 20 s (test_curriculum_app, test_catalog_review_in_the_sandbox) with 24 partitions on 4 cores; the later "
           "certifications re-run them"),
    "C5": ("MATERIAL", "REPAIRED_BY_DECLARED_ADAPTATION", "second run (fingerprint ee8d8f6f...): the C1 repair moved the pilot's configuration to literal constants, and two guards that only an EXACT "
           "declared set of executables may name the ratified snapshots (test_phase3_joint_region_ratification::test_t9, test_phase3_tone_ratification::test_t19) failed. The pilot cannot reach "
           "the bindings (only app.py crosses, and only into the authority and the shadow), so both guards now declare gi_pilot.py, pinned to ONE mention of each snapshot id, no import of a "
           "binding and no record path; test_u23 holds the constants equal to the bindings. Five mutants (a second mention, an import, naming the tone checkpoint or the monitored limitation, "
           "a record path) are caught"),
    "C6": ("ENVIRONMENTAL", "RE_RUN", "second run: fourteen AppTest scripts timed out after 20 s (test_curriculum_app, test_faculty_cohort, test_catalog_review_in_the_sandbox) while an orphan "
           "full-suite pytest left by an earlier probe of this cycle held one of the four cores for 2.5 h; it was stopped, and the fourteen pass alone on the same fingerprint (14 passed in 134 s, "
           "load 0.4); the third certification re-runs them"),
}

#: The material finding that decides the verdict, reproduced on the published base WITHOUT the pilot.
ARCHITECTURE_FINDING = {
    "id": "MINUTE_ALREADY_COMMITTED_ON_A_NON_STRUCTURAL_ZERO_MINUTE_TURN",
    "rule": ("after the first committed minute, a turn that does not move the clock is 'quiet' only if every action of it is structural (reassessment, consultation, venous access); any other "
             "turn re-commits the same minute and the certified authority refuses it with MINUTE_ALREADY_COMMITTED, which halts the development authority permanently (a deliberate rule of P3-28: "
             "'a plan, a held order, a clarification may not commit the same minute a second time')"),
    "reproduced_on": "the published base 352d5fe without the pilot, and with it (test_gi_pilot_page.py::test_p16)",
    "halting_examples": ["Give normal saline.", "Start a pantoprazole infusion.", "Start norepinephrine.", "Titrate norepinephrine to MAP 65.", "What is the hemoglobin?",
                         "Put the patient in the Trendelenburg position."],
    "not_halting_examples": ["Check a hemoglobin.", "Place a second large-bore IV."],
    "why_the_ten_reviewed_paths_did_not_meet_it": "every turn of the ten paths moves the clock, and the development runner of the previous cycle does not call the authority on such a turn",
    "effect_on_the_pilot": ("the first incomplete, held or unrecognized order a resident writes after the first reassessment ends the development encounter (safely, fail-closed, with the "
                            "operational message): the primary question of FD-PILOT-07 (sequential decisions with coherent consequences) cannot be asked of real residents, whose "
                            "incomplete orders are common"),
    "what_the_pilot_does": "it neither bypasses nor changes the authority; it declares the rule in the launcher, ends the encounter with the operational message and pins it by test",
    "what_would_change_it": ("a change of the certified authority's zero-minute-turn semantics (for example, a turn in which nothing is carried out and the clock does not move does not "
                             "re-commit the minute), which is an authority change and needs a faculty decision, a successor of the authority's certification and its own review"),
}

LIMITATIONS = [
    "the human review of the ten paths is REPORTED, not verified against the persisted store; Q1 to Q6, comments, lock events, timestamps and the reviewer's identity were not reported and none is invented",
    "H1 is BOUNDED in the pilot (a request for definitive control is recorded and not carried out, and the encounter ends), not resolved: the ordinary live page is unchanged",
    "H2 is handled in the pilot by labelling the earlier model's mental status and withholding it after norepinephrine; authored case findings are not filtered",
    "the mental-status filters are text transforms over the sentences the earlier model writes; after norepinephrine a sentence they do not know is filtered by a fixed vocabulary (MENTAL_WORDS, which covers the engine's own ladder)",
    "the participant trace tolerates exactly one construct-verifier rejection (the carried reading of a turn without advance); development_management_trace.py was not edited because sealed records pin it",
    "tranexamic acid and other medicines the engine executes halt the authority (AUTHORITY_STOP)",
    "the pilot encounter is presented in English only, whatever language the participant chose; Spanish is deferred (TD-46)",
    "an abandoned encounter stays ACTIVE in the record until the same participant starts another (TD-165 item 13)",
    "the participant reference is pseudonymous, not anonymous: whoever holds the account database can re-link it",
    "the pilot records are hash-chained but not signed (the same limit as TD-153 item 7)",
    "one case only (gi_bleed_57m); gi_bleed_72f is deferred",
    "starting the real pilot needs a separate faculty decision and the grant's scope (resident deployment is NOT granted by GI_NOREPINEPHRINE_DEVELOPMENT_AUTHORITY_GRANT_V1)",
]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


GENERATING_FILES = ("gi_pilot.py", "gi_pilot_ui.py", "curriculum_runtime.py", "resuscitation_room.py", "app.py", "test_gi_pilot.py", "test_gi_pilot_page.py", "test_gi_pilot_records.py",
                    "test_phase3_gi_pilot_records.py")


def _records() -> dict:
    out = {}
    for key, path in records.PATHS.items():
        stored = json.loads(path.read_text(encoding="utf-8"))
        out[key] = {"file": str(path.relative_to(ROOT)), "record_digest": stored["record_digest"], "file_sha256": _sha(path)}
    return out


def build_checkpoint(certification: dict, adversarial_review: dict, *, sequence: list, verdict: str, why_not: dict, facts: dict | None = None) -> dict:
    """The checkpoint record of the cycle. Exactly one verdict, and why not each of the others."""
    assert verdict in VERDICTS and set(why_not) == set(VERDICTS) - {verdict}
    body = {"record_type": "GI_PILOT_READINESS_CHECKPOINT", "version": CHECKPOINT_ID, "decision_reference": gp.DECISIONS, "evidence_class": "MODEL_ANALYSIS",
            "statement": ("GI_MANAGEMENT_TRACE_V1 is ratified for controlled development pilot preparation (reported human review: ACCEPT_WITH_LIMITATION 10). A development pilot of one GI case, "
                          "off by default and fail-closed outside the published development configuration, runs the live development pressure authority with the manual norepinephrine control "
                          f"exactly as published under {GRANT_ID}; it creates no account attempt and reaches no score; it bounds definitive haemostasis before it happens; it labels or withholds "
                          "the earlier model's mental status; it shows a management trace without internals and with the participant's reasoning only as expressed; and it gives faculty "
                          "observe, stop, inspect, flag, mark-unusable and replay-review controls over separate, pseudonymous, hash-chained logs. The real pilot was NOT started."),
            "verdict": verdict, "verdict_name": VERDICTS[verdict], "verdicts": VERDICTS,
            "why_not_the_others": {key: ("this is the verdict" if key == verdict else why_not[key]) for key in VERDICTS},
            "architecture_finding": ARCHITECTURE_FINDING,
            "facts": {"pilot": {"id": gp.PILOT_ID, "flag": gp.FLAG, "store_flag": gp.STORE_FLAG, "cases": list(gp.PILOT_CASES), "challenge_id": gp.CHALLENGE_ID, "horizon_min": gp.HORIZON_MIN,
                                "exits": list(gp.EXITS), "faculty_actions": list(gp.FACULTY_ACTIONS), "participant_kinds": list(gp.RESIDENT_KINDS)},
                      "records": _records(),
                      "authority": {"grant": GRANT_ID, "pressure_snapshot": "GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1", "tone_snapshot": "COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1",
                                    "common_core_runtime_authority": False},
                      "executable_files_added": ["gi_pilot.py", "gi_pilot_ui.py"],
                      "executable_files_changed": ["app.py (the pilot hooks, no-ops without the flag, and the pilot's Layer built at the page's one crossing)", "curriculum_runtime.py (start_pilot_encounter)",
                                                   "resuscitation_room.py (the appearance keyword of render_room)"],
                      "executable_files_not_changed": ["clinical_core/", "family_parser.py", "family_engine.py", "active_order_context.py", "order_pipeline.py", "runtime_authority.py",
                                                       "runtime_ne_authority.py", "runtime_ne_grant.py", "runtime_pressure_grant.py", "runtime_pressure_snapshot.py", "runtime_tone_snapshot.py",
                                                       "runtime_tone_support.py", "runtime_shadow.py", "runtime_shadow_families.py", "development_management_trace.py"],
                      **(facts or {})},
            "review_findings": {key: {"class": cls, "outcome": outcome, "note": note} for key, (cls, outcome, note) in REVIEW_FINDINGS.items()},
            "confirmations": {"real_resident_pilot_started": False, "no_new_physiology": True, "no_source_control_implementation": True, "no_calibration_reopened": True,
                              "no_pump_limited_authority_expansion": True, "no_consciousness_authority_expansion": True, "no_scoring_consequences": True,
                              "no_clinical_validation_claim": True, "no_clinical_core_edit": True, "no_reader_edit": True, "no_authority_change": True, "no_grant_or_snapshot_change": True,
                              "no_sealed_record_rewritten": True, "common_core_runtime_authority": False},
            "limitations": list(LIMITATIONS),
            "certification": certification, "adversarial_review": adversarial_review, "sequence": sequence,
            "next_human_action": ("Decide whether the certified authority's zero-minute-turn rule may change for the pilot (a turn in which nothing is carried out and the clock does not move would "
                                  "not re-commit the minute), or whether the pilot should instead run with that rule declared and its encounters expected to end at the first incomplete order. "
                                  "Separately: decide the real pilot's activation (a faculty decision and the grant's scope), H1 beyond the pilot, and H2. Nothing else is to be built on this line until then."),
            "open_faculty_decisions": ["the zero-minute-turn rule of the certified authority (MINUTE_ALREADY_COMMITTED) for the pilot", "activating the real pilot and the grant's scope",
                                       "H1 on the ordinary live page", "H2 on the ordinary live page", "gi_bleed_72f in the pilot"]}
    parts = {name: _sha(ROOT / name) for name in GENERATING_FILES}
    parts["test_gi_pilot_checkpoint.py"] = _sha(Path(__file__).resolve())
    body["provenance"] = hr.provenance(record_id=CHECKPOINT_ID, generating_code=parts, generated_on=GENERATED_ON, grant_id=GRANT_ID,
                                       source_data={"verdict": verdict, "certification": certification, "adversarial_review": adversarial_review, "sequence": sequence,
                                                    "records": _records()})
    return hr.seal(body)


def write_checkpoint(certification: dict, adversarial_review: dict, *, sequence: list, verdict: str, why_not: dict, facts: dict | None = None) -> dict:
    record = build_checkpoint(certification, adversarial_review, sequence=sequence, verdict=verdict, why_not=why_not, facts=facts)
    return {str(CHECKPOINT_PATH.relative_to(ROOT)): hr.write(CHECKPOINT_PATH, record)}
