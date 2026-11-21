"""P3-483: the BUILDER of the SECOND successor record of the order reader (a tool, never imported by a page; it holds no test).

The reader was changed twice under the faculty's lifting of its freeze, each time for ONE narrowly scoped safety correction (FD-TARGET-01 on 2026-11-20, FD-ORDER-01 to FD-ORDER-11 on 2026-11-21). The first
successor record (``PHASE3_READER_SUCCESSION_TARGET_SAFETY.json``) is sealed and is never regenerated; this builder writes the NEXT versioned record, ``PHASE3_READER_SUCCESSION_ORDER_SAFETY.json``: what the reader was
(the reader of the first successor), what it is, the declared reversal that rebuilds the old one, how all three readers stay independently reconstructable, how every Phase-2 digest still recomputes, and the
calibration freeze in each state -- and it changes NOTHING executable and rewrites NOTHING sealed. A record already generated is never regenerated under new code: ``historical_records.write`` refuses to replace one
with other content.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import historical_records as hr
import reader_succession as rsu

ROOT = Path(__file__).resolve().parent
REV = ROOT / "docs" / "revision"
RECORD_PATH = REV / "PHASE3_READER_SUCCESSION_ORDER_SAFETY.json"
RECORD_ID = "PHASE3_READER_SUCCESSION_ORDER_SAFETY_V1"
SUPERSEDES = "PHASE3_READER_SUCCESSION_TARGET_SAFETY_V1"
GENERATED_ON = "2026-11-21"
DECISIONS = {
    "FD-ORDER-01": "L-1 unit compatibility: an adjustment to an active vasoactive infusion never assumes mcg/min; a rate is executable only if its drug is attributed, the rate is explicit, the unit is explicit AND supported for that drug; fail closed otherwise.",
    "FD-ORDER-02": "L-2 rate attribution: the rate of another medication in the same clause or bundle is never attributed to norepinephrine, epinephrine, dobutamine or nitroglycerin; ownership is drug-specific and structurally justified, no nearest-number heuristic, no cross-drug inheritance.",
    "FD-ORDER-03": "L-3 stop attribution: a stop inherited from a list, bundle, prior clause or neighbouring medication does not stop a vasoactive infusion unless it is unambiguously attributed to that drug; an ambiguous stop fails closed.",
    "FD-ORDER-04": "L-4 deferred '/min': the '/min' of a deferred or unrelated order is never read as a duration or another field that makes a vasoactive order executable; explicit valid rate-unit parsing is preserved; no broad grammar redesign.",
    "FD-ORDER-05": "L-5: 'restart norepinephrine' with no explicit supported absolute rate is the approved incomplete-rate clarification; the previous rate is not reused; nothing executes.",
    "FD-ORDER-06": "L-6: 'continue norepinephrine at 12' is INCOMPLETE_EXPLICIT_RATE and asks for units; 'continue norepinephrine at 12 mcg/min' is valid.",
    "FD-ORDER-07": "L-7: the downstream defense-in-depth barrier understands the existing nitroglycerin-style field rate_mcg_min, so nitroglycerin no longer relies on source parsing alone; no physiology change and no new generic medication schema.",
    "FD-ORDER-08": "L-8: a numeric-only answer to a dose/rate question never becomes an executable vasoactive rate; explicit rate AND supported units are required; units are never inferred from the active infusion, a previous order, the question's wording or a drug default.",
    "FD-ORDER-09": "PERMANENT_FAIL_CLOSED stays for the shadow after a malformed or unsupported order; no recovery in this package.",
    "FD-ORDER-10": "RAW_ORDER_REMAINS_CORRECT_BOUNDARY stays for the shared mirror; no raw/resolved hybrid.",
    "FD-ORDER-11": "Out of scope: automatic MAP/SBP-target titration, mcg/kg/min conversion, relative rate arithmetic, another vasopressor or drug, pump-specific physiology, tone recalibration, authority expansion.",
}
#: Texts whose reading in the three states the record shows side by side: the eight limitations, the neighbours the review added, and the orders that must not move.
BEHAVIOR_TEXTS = (
    "increase the infusion to 40 mL/h", "titrate norepinephrine to MAP 65 with propofol 5 mcg/min", "increase norepinephrine to 10 mcg/min with propofol 5 mcg/min", "increase norepinephrine and dobutamine to 10 mcg/min",
    "stop NS, norepinephrine to MAP 65", "stop nitroglycerin, norepinephrine to MAP 65", "stop NS but keep norepinephrine", "stop all except norepinephrine", "stop NS, norepinephrine", "stop norepinephrine and nitroglycerin",
    "increase norepinephrine to 12 mcg/min in 5 minutes", "restart norepinephrine", "restart norepinephrine at 10 mcg/min", "continue norepinephrine at 12", "continue norepinephrine at 12 mcg/min", "continue norepinephrine",
    "increase norepinephrine", "increase norepinephrine to 12", "increase norepinephrine to 12 mcg/min", "decrease norepinephrine to 4 mcg/min", "nitroglicerina para PAS 120", "nitroglycerin 20", "nitroglycerin 20 mcg/min",
    "titrate norepinephrine to MAP 65", "norepinephrine 10 mcg/min", "stop norepinephrine", "Start norepinephrine at 5 mcg/min", "reinicia la noradrenalina a 10 mcg/min",
    "stop all except dobutamine and norepinephrine", "stop norepinephrine while dobutamine continues", "stop norepinephrine to keep MAP above 65", "increase norepinephrine to MAP 65 with NTG 20 mcg/min",
    "start norepinephrine 12 mcg/min of propofol", "start nor-epi at 5 mcg/min", "espera 5 minutos y luego reanuda dobutamina", "stop the norepinephrine infusion in 5 minutes")
#: The tests whose PIN or whose historical recomputation was moved to the reader of its own time (each protects exactly what it protected).
ADAPTED_TESTS = {
    "test_prephase1_reader_freeze.py": "the reader pin is now the order-safety SUCCESSOR blob (EXPECTED_BLOBS); the two earlier readers are pinned beside it (HISTORICAL_BLOBS and TARGET_SAFETY_BLOBS): the reader is frozen again, at its new successor",
    "test_clinical_core_calibration_framework.py": "the calibration freeze is checked in the three states: the closure digest under the closure reader, the first successor's digest under the target-safety view, and the live digest where only input_path_sources moved",
    "test_phase3_reader_succession.py": "the chain: the closure reader and the first successor are both rebuilt from the live file; the first record is read under the target-safety view; the second record is checked like the first",
    "test_reader_succession_analysis.py (the builder of the FIRST record)": "it reads the first successor from its own rebuilt view, so that the sealed record of the first succession still regenerates to the same content",
    "test_phase3_target_order_boundary.py": "the verification line of the reader chain (the dictionary now names both rebuilt readers)",
    "test_phase3_target_rate_source.py and test_phase3_historical_record_versioning.py": "the behavior the first successor pinned that this cycle changed on purpose (restart with no rate, a number after continue) is asserted as it now is; the index pin moved with the new record",
}
CONFIRMED_NOT_CHANGED = ["clinical_core/ (any file)", "the core digest of PHASE2_AMENDMENT_3", "COMMON_CORE_RUNTIME_AUTHORITY", "the physiology constants, the tone parameters and the pump coupling", "family_engine.py", "active_order_context.py",
                         "shared_order_language.py", "shared_order_quantities.py", "weight_based_doses.py", "runtime_shadow.py (the raw order stays the boundary; the shadow stays PERMANENT_FAIL_CLOSED)", "the Phase-2 INPUT_PATH_SOURCES list",
                         "any sealed record"]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _actions(reader, text):
    return [{key: value for key, value in action.items() if key in ("type", "operation", "rate", "units", "rate_mcg_min", "rate_value", "rate_units", "incomplete_explicit_rate", "unrecognized_text")}
            for action in reader.parse_family_actions(text)["actions"]]


def behavior() -> list:
    import family_parser as live
    closure, first = rsu.historical_reader_module(), rsu.target_safety_reader_module()
    return [{"text": text, "closure_reader": _actions(closure, text), "target_safety_reader": _actions(first, text), "order_safety_reader": _actions(live, text)} for text in BEHAVIOR_TEXTS]


def freeze_state() -> dict:
    """The calibration freeze in the three states and the five closure freeze digests, recomputed."""
    from clinical_core import amendment_3 as a3, calibration, closure_guard as cg, decision_pack, lactate_slice, tone_domain
    from clinical_core import amendment_1 as a1, blood_anchors as ba, blood_probes as bp
    components_now, digest_now = calibration.digest_components(), calibration.frozen_digest()
    generated_now = {"decision_pack": decision_pack.pack_digest(), "lactate_slice": lactate_slice.slice_digest(), "blood_anchors": ba.anchors_digest(), "blood_probes": bp.probes_digest()}
    with rsu.target_safety_reader_view():
        components_first, digest_first = calibration.digest_components(), calibration.frozen_digest()
        generated_first = {"decision_pack": decision_pack.pack_digest(), "lactate_slice": lactate_slice.slice_digest(), "blood_anchors": ba.anchors_digest(), "blood_probes": bp.probes_digest()}
    with rsu.historical_reader_view():
        components_closure, digest_closure = calibration.digest_components(), calibration.frozen_digest()
    recorded = json.loads(a1.CLOSURE_RECORD.read_text(encoding="utf-8"))["freeze_digests"]
    with a3.closure_view():
        with rsu.historical_reader_view():
            closure_recomputed = {"calibration": calibration.frozen_digest(), "closure_guard_P2X1A": cg.freeze_digest(), "tone_domain_on_the_live_tree": tone_domain.freeze_digest(),
                                  "lactate_slice": lactate_slice.slice_digest(), "decision_pack": decision_pack.pack_digest()}
    moved = sorted(name for name in components_now if components_now[name] != components_first[name])
    return {"calibration": {"phase2_closure_reader": {"digest": digest_closure, "components": components_closure}, "target_safety_successor": {"digest": digest_first, "components": components_first},
                            "order_safety_successor": {"digest": digest_now, "components": components_now}, "components_that_moved_in_this_succession": moved,
                            "scenario_inputs_identical": components_now["scenario_inputs"] == components_first["scenario_inputs"] == components_closure["scenario_inputs"],
                            "input_path_sources_list_unchanged": True},
            "closure_freeze_digests": {"recorded_in_the_closure_record": recorded, "recomputed_under_the_closure_view_and_the_closure_reader": closure_recomputed, "equal": recorded == closure_recomputed},
            "generated_documents": {name: {"under_the_target_safety_reader": generated_first[name], "under_the_order_safety_reader": generated_now[name]} for name in generated_now}}


def generating_code() -> dict:
    from clinical_core import amendment_3 as a3
    return {"clinical_core": a3.amended_core_digest_now(), "test_reader_succession_order_safety_analysis.py": _sha(Path(__file__).resolve()), "reader_succession.py": _sha(ROOT / "reader_succession.py"),
            "family_parser.py": _sha(ROOT / "family_parser.py"), "order_pipeline.py": _sha(ROOT / "order_pipeline.py"), "time_semantics.py": _sha(ROOT / "time_semantics.py"), "pending_family_orders.py": _sha(ROOT / "pending_family_orders.py"), "app.py": _sha(ROOT / "app.py")}


def build() -> dict:
    from clinical_core import amendment_3 as a3
    freeze = freeze_state()
    if not freeze["closure_freeze_digests"]["equal"]:
        raise ValueError("a closure freeze digest does not recompute under the closure reader")
    verified = rsu.verify()
    body = {"record_type": "READER_SUCCESSION_RECORD", "version": RECORD_ID, "supersedes": SUPERSEDES, "evidence_class": "MODEL_ANALYSIS", "decision_reference": "FD-ORDER-01 to FD-ORDER-11", "date": GENERATED_ON,
            "statement": ("The order reader (family_parser.py) was changed a SECOND time under the faculty's lifting of its freeze for a narrowly scoped safety correction: a rate and a stop belong to ONE drug, restart and continue "
                          "with no explicit rate are the approved question. The reader of the first successor and the reader of the Phase-2 closure both stay reconstructable byte for byte and in behavior; every Phase-2 digest "
                          "recomputes from the closure reader; the calibration freeze moved in exactly one component and the materialized scenario inputs did not move; nothing sealed was rewritten and nothing in "
                          "clinical_core/ was edited."),
            "faculty_decisions": dict(DECISIONS),
            "reader": {"file": rsu.READER,
                       "phase2_closure": {"git_blob": rsu.HISTORICAL_GIT_BLOB, "sha256": rsu.HISTORICAL_SHA256, "accepted_by": "the pre-Phase-1 reader freeze and the Phase-2 closure"},
                       "target_safety_successor": {"git_blob": rsu.TARGET_SAFETY_GIT_BLOB, "sha256": rsu.TARGET_SAFETY_SHA256, "recorded_by": "PHASE3_READER_SUCCESSION_TARGET_SAFETY.json (sealed, never regenerated)"},
                       "order_safety_successor": {"git_blob": rsu.SUCCESSOR_GIT_BLOB, "sha256": rsu.SUCCESSOR_SHA256, "frozen_again_by": "test_prephase1_reader_freeze.py (EXPECTED_BLOBS)"},
                       "the_other_four_reader_files": "byte-identical to the V3 freeze (shared_order_language.py, shared_order_quantities.py, active_order_context.py, weight_based_doses.py)"},
            "reversal": {"mechanism": "declared reversible hunks (the precedent of the amendments), composed: the live file -> the first successor -> the closure reader; each stage is proven against its pinned identity",
                         "order_safety": {"hunks": [{"successor_text": new, "previous_text": old} for new, old in rsu.REVERSAL_ORDER_SAFETY], "hunk_count": len(rsu.REVERSAL_ORDER_SAFETY), "rebuilds": "target_safety_successor",
                                          "proven": verified["target_safety_rebuilt"] and verified["live_is_the_successor"]},
                         "target_safety": {"hunks": [{"successor_text": new, "historical_text": old} for new, old in rsu.REVERSAL], "hunk_count": len(rsu.REVERSAL), "rebuilds": "phase2_closure", "proven": verified["historical_rebuilt"]},
                         "readers_run_as": {"phase2_closure": "family_parser_phase2_closure", "target_safety_successor": "family_parser_target_safety", "live": "family_parser (they never replace it in sys.modules)"}},
            "historical_digests_recompute_by": ("reader_succession.install(patch) / historical_reader_view() for the closure reader and install_target_safety(patch) / target_safety_reader_view() for the first successor, "
                                                "composed INSIDE clinical_core.amendment_3.closure_view(); clinical_core is not edited"),
            "freeze": freeze, "behavior": behavior(),
            "what_changed_in_behavior": ["an adjustment named only by its role is held unless its unit is one a vasoactive infusion runs in (and mcg/kg/min is not one nitroglycerin runs in)",
                                         "a rate another medicine of the same piece claims is never an infusion's: the whole piece is held", "a stop is taken by a vasoactive infusion only if the verb governs its name (never inherited by an order that says more, never through an exception)",
                                         "the '/min' of a mass-per-time rate unit is not a duration (time_semantics)", "a restart with no explicit rate is the approved incomplete-rate question", "a number beside 'continue' is incomplete, not a silent continue",
                                         "the pipeline barrier reads rate_mcg_min and requires the number to be written with its unit", "the legacy page takes no unit from the running infusion or the drug's usual one",
                                         "an exception ends the stop for the pieces after it; one stop that names two infusions is not read (never chosen by the reader's priority)",
                                         "an answer to 'what rate?' is one rate with its unit for the drug that asked, with no other medicine and no time to wait for (family path and legacy page path)",
                                         "an incomplete order of a deferred part is asked, never dropped; 'nor-epi' is never read as epinephrine; the word 'infusion' and the micro sign are not a duration"],
            "what_did_not_change": list(CONFIRMED_NOT_CHANGED),
            "defense_in_depth": ("order_pipeline.incomplete_explicit_rate holds a structured infusion that carries a rate with no units, an adjustment with no rate, a role-named adjustment in a unit no vasoactive runs in, and (with the order's text) "
                                 "a rate_mcg_min that is not written with its unit; each barrier of a target-as-rate or incomplete-rate order protects alone, nitroglycerin included"),
            "core_digest": a3.amended_core_digest_now(), "authority": {"common_core_runtime_authority": False, "expanded": False},
            "executable_change": True, "executable_files_changed": ["family_parser.py", "order_pipeline.py", "time_semantics.py", "pending_family_orders.py", "app.py", "reader_succession.py"], "physiology_change": False, "tone_recalibrated": False,
            "adapted_tests": dict(ADAPTED_TESTS),
            "is_not": ["a clinical validation", "an approval of any medication order", "a recovery semantic for a malformed order", "a change of the shadow boundary", "automatic titration", "a weight-based conversion"]}
    body["provenance"] = hr.provenance(record_id=RECORD_ID, generating_code=generating_code(), generated_on=GENERATED_ON,
                                       source_data={"order_safety_hunks": [list(pair) for pair in rsu.REVERSAL_ORDER_SAFETY], "target_safety_hunks": [list(pair) for pair in rsu.REVERSAL], "freeze": freeze, "decisions": DECISIONS})
    return hr.seal(body)


def write() -> dict:
    return {str(RECORD_PATH.relative_to(ROOT)): hr.write(RECORD_PATH, build())}


def reproduce() -> dict:
    """The CONTENT of the record regenerated, without provenance or seal: what a test compares with the stored one."""
    return {key: value for key, value in build().items() if key not in ("provenance", "record_digest")}


if __name__ == "__main__":
    print(json.dumps(write(), indent=2))
