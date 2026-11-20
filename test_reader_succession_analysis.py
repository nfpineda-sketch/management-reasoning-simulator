"""P3-470: the BUILDER of the successor record of the order reader (a tool, never imported by a page; it holds no test).

The reader was repaired once, on 2026-11-20, under the faculty's lifting of its freeze for ONE narrowly scoped safety correction (FD-TARGET-01). This builder writes the versioned SUCCESSOR record
``PHASE3_READER_SUCCESSION_TARGET_SAFETY.json``: what the reader was, what it is, the declared reversal that rebuilds the old one, how every Phase-2 digest still recomputes from it, and the calibration freeze
before and after -- and it changes NOTHING executable and rewrites NOTHING sealed. A record already generated is never regenerated under new code: ``historical_records.write`` refuses to replace one with other content.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import historical_records as hr
import reader_succession as rsu

ROOT = Path(__file__).resolve().parent
REV = ROOT / "docs" / "revision"
RECORD_PATH = REV / "PHASE3_READER_SUCCESSION_TARGET_SAFETY.json"
RECORD_ID = "PHASE3_READER_SUCCESSION_TARGET_SAFETY_V1"
GENERATED_ON = "2026-11-20"
DECISIONS = {
    "FD-TARGET-01": "The parser freeze is lifted ONLY for a narrowly scoped safety correction; the invariant is PHYSIOLOGIC_TARGET != DRUG_RATE; no broad parser redesign; no change to unrelated parsing.",
    "FD-TARGET-02": "Repair the earliest correct semantic layer: MAP 65, MAP >65, SBP 90, SBP >100, pressure goal 65 are target (or at minimum non-rate) information and NEVER an executable drug rate.",
    "FD-TARGET-03": "The downstream structural rule in order_pipeline stays as DEFENSE IN DEPTH; the source fix and the downstream boundary must agree.",
    "FD-TARGET-04": "The source rule covers norepinephrine, epinephrine, dobutamine and nitroglycerin where the order model exposes them; no new drug physiology and no new medication.",
    "FD-TARGET-05": "Explicit supported absolute rates remain valid (norepinephrine 10 mcg/min, increase to 12 mcg/min, decrease to 4 mcg/min, nitroglycerin 20 mcg/min).",
    "FD-TARGET-06": "Incomplete rate commands (increase norepinephrine, increase norepinephrine to 12, restart norepinephrine) never execute and are never a silent no-op: INCOMPLETE_EXPLICIT_RATE; ask for an explicit rate with units; infer nothing.",
    "FD-TARGET-07": "'restart norepinephrine at 10 mcg/min' is a valid START/RESTART; 'restart norepinephrine' with no explicit supported rate stays incomplete; no previous-rate reuse.",
    "FD-TARGET-08": "PERMANENT_FAIL_CLOSED stays for the shadow after a malformed or unsupported order; no recovery semantics in this package.",
    "FD-TARGET-09": "RAW_ORDER_REMAINS_CORRECT_BOUNDARY stays for the shared mirror; no raw/resolved hybrid; the shadow does not move to engine-resolved orders.",
    "FD-TARGET-10": "The approved Spanish clarification: 'La orden especifica un objetivo o una tasa incompleta. Indique una tasa explícita con sus unidades para continuar.' (neutral, non-prescriptive, it does not call the detected number a dose).",
    "FD-TARGET-11": "No physiology change, no tone recalibration, no authority expansion.",
}
#: Texts whose old and new reading the record shows side by side (the P3-452 ten of the previous cycle, the nitroglycerin forms, the incomplete commands and the restarts).
BEHAVIOR_TEXTS = (
    "titrate norepinephrine to MAP 65", "titrate norepinephrine to MAP >65", "maintain MAP 65", "target MAP 65 with norepinephrine", "increase norepinephrine to 10 mcg/min", "norepinephrine 10 mcg/min",
    "decrease norepinephrine to 4 mcg/min", "stop norepinephrine", "0.1 mcg/kg/min: norepinephrine 0.1 mcg/kg/min", "increase norepinephrine", "increase norepinephrine to 12", "decrease norepinephrine",
    "wean norepinephrine off", "restart norepinephrine", "restart norepinephrine at 10 mcg/min", "titrate nitroglycerin to SBP 120", "nitroglycerin to keep SBP <140", "nitroglycerin 20 mcg/min", "nitroglycerin 20",
    "titrate epinephrine to MAP 65", "titrate dobutamine to MAP 65", "titula noradrenalina a PAM 65", "reinicia la noradrenalina a 10 mcg/min", "continue norepinephrine", "start norepinephrine")
#: The tests whose PIN or whose historical recomputation was moved to the reader of its own time, and why (each protects exactly what it protected).
ADAPTED_TESTS = {
    "test_prephase1_reader_freeze.py": "the reader pin is now the SUCCESSOR blob (EXPECTED_BLOBS) and the closure blob is pinned beside it (HISTORICAL_BLOBS): the reader is frozen again, at its successor; the other four reader files are unchanged",
    "test_clinical_core_calibration_framework.py": "the calibration freeze is checked in both states: the historical digest and components under the reconstructed historical reader, and the successor digest live, where only the input_path_sources component moved",
    "test_phase2_closure.py, test_phase2_amendment_artifacts.py, test_phase2_amendment_lineage.py": "their fixtures install the reader of the Phase-2 closure (reader_succession.install) on top of the closure tree, so every recorded closure digest recomputes with the reader of its own time",
    "43 closed-package test files (test_clinical_core_*, test_gi_*, test_p2*, ...)": ("mechanical: after each a3.tree/chain/amendment_1_tree/amendment_2_tree(patch) the historical reader is installed (succession.install(patch)); where a test recomputes a closure digest, a3.closure_view() is kept and succession.historical_reader_view() is composed inside it; "
                                                                                      "no assertion, no expected value and no threshold changed (verified line by line: only the import and those calls differ)"),
    "test_single_dose_is_not_an_infusion.py": "a bare '.1' is no longer read as a rate, so a reply of only the units cannot make a dose of it: the order missing its rate is completed by an explicit rate with its units; what the test protects (a support order asked for, never refused as a single dose) still holds",
    "test_functional_equivalence.py": "'Bajar la noradrenalina' (a titration with no new setting) is still an order and never dropped as reasoning; it is now the incomplete-rate question where it used to be completed from the running infusion and do nothing",
    "test_reasoning_is_not_an_unreadable_order.py": "'Start norepinephrine .1' is now the incomplete-rate question (INCOMPLETE_EXPLICIT_RATE, no number, no single-dose wording) where it used to ask for the units of a bare 0.1",
    "test_phase3_target_order_boundary.py": "rewritten for two barriers: the second barrier (order_pipeline) is proven ALONE with the historical reader, the source barrier alone with the pipeline monkeypatched away, and both together; the earlier cases are kept",
}
CONFIRMED_NOT_CHANGED = ["clinical_core/ (any file)", "the core digest of PHASE2_AMENDMENT_3", "COMMON_CORE_RUNTIME_AUTHORITY", "the physiology constants and the tone parameters", "family_engine.py", "active_order_context.py",
                         "shared_order_language.py", "shared_order_quantities.py", "weight_based_doses.py", "the Phase-2 INPUT_PATH_SOURCES list", "any sealed record"]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _actions(reader, text):
    return [{key: value for key, value in action.items() if key in ("type", "operation", "rate", "units", "rate_mcg_min", "incomplete_explicit_rate")}
            for action in reader.parse_family_actions(text)["actions"]]


def behavior() -> list:
    import family_parser as live
    old = rsu.historical_reader_module()
    return [{"text": text, "historical_reader": _actions(old, text), "successor_reader": _actions(live, text)} for text in BEHAVIOR_TEXTS]


def freeze_state() -> dict:
    """The calibration freeze before (the reader of the closure) and after (the successor), and the five closure freeze digests, recomputed."""
    from clinical_core import amendment_3 as a3, calibration, closure_guard as cg, decision_pack, lactate_slice, tone_domain
    from clinical_core import amendment_1 as a1, blood_anchors as ba, blood_probes as bp
    components_now, digest_now = calibration.digest_components(), calibration.frozen_digest()
    with rsu.historical_reader_view():
        components_before, digest_before = calibration.digest_components(), calibration.frozen_digest()
        generated_before = {"decision_pack": decision_pack.pack_digest(), "lactate_slice": lactate_slice.slice_digest(), "blood_anchors": ba.anchors_digest(), "blood_probes": bp.probes_digest()}
    generated_after = {"decision_pack": decision_pack.pack_digest(), "lactate_slice": lactate_slice.slice_digest(), "blood_anchors": ba.anchors_digest(), "blood_probes": bp.probes_digest()}
    recorded = json.loads(a1.CLOSURE_RECORD.read_text(encoding="utf-8"))["freeze_digests"]
    with a3.closure_view():
        with rsu.historical_reader_view():
            closure_recomputed = {"calibration": calibration.frozen_digest(), "closure_guard_P2X1A": cg.freeze_digest(), "tone_domain_on_the_live_tree": tone_domain.freeze_digest(),
                                  "lactate_slice": lactate_slice.slice_digest(), "decision_pack": decision_pack.pack_digest()}
    moved = sorted(name for name in components_now if components_now[name] != components_before[name])
    return {"calibration": {"before_the_succession": {"digest": digest_before, "components": components_before}, "after_the_succession": {"digest": digest_now, "components": components_now},
                            "components_that_moved": moved, "scenario_inputs_identical": components_now["scenario_inputs"] == components_before["scenario_inputs"],
                            "input_path_sources_list_unchanged": True},
            "closure_freeze_digests": {"recorded_in_the_closure_record": recorded, "recomputed_under_the_closure_view_and_the_historical_reader": closure_recomputed, "equal": recorded == closure_recomputed},
            "generated_documents": {name: {"under_the_historical_reader": generated_before[name], "under_the_successor_reader": generated_after[name]} for name in generated_before}}


def generating_code() -> dict:
    from clinical_core import amendment_3 as a3
    return {"clinical_core": a3.amended_core_digest_now(), "test_reader_succession_analysis.py": _sha(Path(__file__).resolve()), "reader_succession.py": _sha(ROOT / "reader_succession.py"),
            "family_parser.py": _sha(ROOT / "family_parser.py")}


def build() -> dict:
    from clinical_core import amendment_3 as a3
    freeze = freeze_state()
    if not freeze["closure_freeze_digests"]["equal"]:
        raise ValueError("a closure freeze digest does not recompute under the historical reader")
    body = {"record_type": "READER_SUCCESSION_RECORD", "version": RECORD_ID, "evidence_class": "MODEL_ANALYSIS", "decision_reference": "FD-TARGET-01 to FD-TARGET-11", "date": GENERATED_ON,
            "statement": ("The order reader (family_parser.py) was repaired ONCE under the faculty's lifting of its freeze for a narrowly scoped safety correction: a physiologic target is never a drug rate. The reader of the Phase-2 "
                          "closure stays reconstructable byte for byte and in behavior; every Phase-2 digest recomputes from it; the calibration freeze moved in exactly one component and the materialized scenario inputs "
                          "did not move; nothing sealed was rewritten and nothing in clinical_core/ was edited."),
            "faculty_decisions": dict(DECISIONS),
            "reader": {"file": rsu.READER, "historical": {"git_blob": rsu.HISTORICAL_GIT_BLOB, "sha256": rsu.HISTORICAL_SHA256, "accepted_by": "the pre-Phase-1 reader freeze and the Phase-2 closure"},
                       "successor": {"git_blob": rsu.SUCCESSOR_GIT_BLOB, "sha256": rsu.SUCCESSOR_SHA256, "frozen_again_by": "test_prephase1_reader_freeze.py (EXPECTED_BLOBS)"},
                       "the_other_four_reader_files": "byte-identical to the V3 freeze (shared_order_language.py, shared_order_quantities.py, active_order_context.py, weight_based_doses.py)"},
            "reversal": {"mechanism": "declared reversible hunks (the precedent of the amendments); reader_succession.historical_reader_bytes() applies them to the live file and proves the result against the pinned identity",
                         "hunks": [{"successor_text": new, "historical_text": old} for new, old in rsu.REVERSAL], "hunk_count": len(rsu.REVERSAL),
                         "proven": rsu.verify()["historical_rebuilt"] and rsu.verify()["live_is_the_successor"], "historical_reader_runs_as": "family_parser_phase2_closure (never replaces family_parser in sys.modules)"},
            "historical_digests_recompute_by": "reader_succession.install(patch) / historical_reader_view(), composed INSIDE clinical_core.amendment_3.closure_view(); clinical_core is not edited",
            "freeze": freeze, "behavior": behavior(),
            "what_changed_in_behavior": ["a target or a number with no rate unit beside an infusion is never a rate (INCOMPLETE_EXPLICIT_RATE)", "an adjustment with no rate is asked, not completed from the running infusion",
                                         "restart/resume of the four infusions is a start", "the neutral approved message, in English and Spanish"],
            "what_did_not_change": list(CONFIRMED_NOT_CHANGED),
            "defense_in_depth": "order_pipeline.incomplete_explicit_rate stays: it holds a structured infusion that carries a rate with no units or an adjustment with no rate, whatever produced it; for nitroglycerin only the adjustment "
                                "with no rate (its unit is in the field name)",
            "core_digest": a3.amended_core_digest_now(), "authority": {"common_core_runtime_authority": False, "expanded": False},
            "executable_change": True, "executable_files_changed": ["family_parser.py", "order_pipeline.py", "order_ledger.py", "pending_family_orders.py", "app.py", "language.py", "reader_succession.py"], "physiology_change": False, "tone_recalibrated": False,
            "is_not": ["a clinical validation", "an approval of any medication order", "a recovery semantic for a malformed order", "a change of the shadow boundary"]}
    body["provenance"] = hr.provenance(record_id=RECORD_ID, generating_code=generating_code(), generated_on=GENERATED_ON, source_data={"hunks": [list(pair) for pair in rsu.REVERSAL], "freeze": freeze,
                                                                                                                                      "decisions": DECISIONS})
    return hr.seal(body)


def write() -> dict:
    return {str(RECORD_PATH.relative_to(ROOT)): hr.write(RECORD_PATH, build())}


def reproduce() -> dict:
    """The CONTENT of the record regenerated, without provenance or seal: what a test compares with the stored one."""
    return {key: value for key, value in build().items() if key not in ("provenance", "record_digest")}


if __name__ == "__main__":
    print(json.dumps(write(), indent=2))
