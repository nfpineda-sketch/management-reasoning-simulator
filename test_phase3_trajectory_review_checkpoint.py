"""UX-013 · the checkpoint of the FACULTY TRAJECTORY REVIEW: a record that is what the code and the stored records say NOW, and that cites only tests that exist.

It claims nothing the tests do not carry: every status names the tests that prove it (they are looked up in the test files), the pins are the stored review set and the certified series, and the limits are written
out. It is a technical checkpoint, not a clinical validation, an approval, a resident pilot or the start of any further phase. The tree fingerprint and the suite counts are NOT in this record (a record cannot contain
the fingerprint of the tree that includes it): the final report states them.
"""
import json
import os
import re
from pathlib import Path

import faculty_trajectory_review as ftr
import runtime_faculty_bundle as bundles
import runtime_faculty_review as fr

ROOT = Path(__file__).resolve().parent
RECORD_PATH = ROOT / "docs" / "revision" / "PHASE3_FACULTY_TRAJECTORY_REVIEW_CHECKPOINT.json"
TEST_FILES = ("test_phase3_trajectory_review.py", "test_phase3_trajectory_review_page.py")

STATUSES = {
    "BLINDED_REVIEW_FLOW": ("one page per scenario: context, timeline, chart, Q1-Q5 (+Q5H where the experiment stopped), one lock; no comparator, legacy number or identifier reaches the browser before the lock", ("test_m3_", "test_u1_", "test_u2_", "test_u3_")),
    "COMPARATOR_REVEAL": ("the legacy comparator exists only for a LOCKED state, is overlaid on the same axes, is labelled nonauthoritative and is never called truth", ("test_m4_", "test_m16_", "test_u2_")),
    "FIRST_PASS_IMMUTABILITY": ("the writer refuses and the reader ignores any change after the lock, a forged chained lock cannot reveal anything, a stale second tab changes nothing", ("test_m6_", "test_m7_", "test_m20_", "test_u2_", "test_u10_")),
    "AUTOSAVE": ("each answer is saved as it is given by a callback of the widget the reviewer changed; a refresh restores; a refused comment is said to be unsaved; a disk error is a refusal, never a traceback", ("test_m5_", "test_m22_", "test_u2_", "test_u10_", "test_u11_", "test_u13_", "test_u14_")),
    "ARTIFACT_LINKAGE": ("one create-only record links reviewer (opaque), scenario, package, artifact, grant, snapshot, review set, item, comparator, blind answers, reveal and post-reveal answers; submit is one critical section", ("test_m8_", "test_m9_", "test_m10_", "test_m11_", "test_m17_", "test_m18_", "test_u2_")),
    "SCENARIO_NAVIGATION": ("submit moves to the next scenario by itself; a scenario out of turn cannot be entered; a failed submit does not advance; submitted scenarios are read-only; each optional scenario opens by itself", ("test_u2_", "test_u3_", "test_u4_", "test_u12_")),
    "SESSION_SUMMARY": ("N/N, the four judgment counts and the comments, from records that VERIFY against the log that closed them; an altered, foreign or missing record is not counted and is reported; the technical summary is written by itself", ("test_m12_", "test_m13_", "test_m19_", "test_u3_")),
    "FACULTY_ISOLATION": ("only inside the faculty review launcher of a process that named the review mode and passed its gate; the review modules import nothing of the engine, the authority, the shadow, the grant or the core", ("test_m15_", "test_u6_", "test_u7_")),
    "RESIDENT_ISOLATION": ("a resident account or an ordinary deployment sees nothing of the review and nothing is created for them", ("test_u5_", "test_u7_")),
}


def _test_names() -> list:
    names = []
    for name in TEST_FILES:
        names += re.findall(r"^def (test_\w+)", (ROOT / name).read_text(encoding="utf-8"), re.M)
    return names


def build_record() -> dict:
    series = json.loads(ftr.SERIES_PATH.read_text(encoding="utf-8"))
    loaded = ftr.load_set(bundles=bundles, scenario_of=fr.scenario)
    body = {
        "record_type": "PHASE3_FACULTY_TRAJECTORY_REVIEW_CHECKPOINT", "version": ftr.VERSION, "decided_on": "2026-11-14",
        "statuses": {key: {"status": "VERIFIED_BY_THE_CITED_TESTS", "what": what, "tests": list(prefixes)} for key, (what, prefixes) in STATUSES.items()},
        "pins": {"review_set": "docs/revision/PHASE3_FACULTY_TRAJECTORY_REVIEW_SET.json", "review_set_digest_pinned_in_code": ftr.PINNED_SET_DIGEST, "review_set_loads_pinned": loaded["ok"] and loaded["problems"] == [],
                 "scenarios": [entry["scenario_id"] for entry in ftr.sequence(loaded["items"])], "required": [entry["scenario_id"] for entry in ftr.sequence(loaded["items"]) if entry["required"]],
                 "certified_series": "docs/revision/PHASE3_PRESSURE_AUTHORITY_SERIES.json", "certified_series_record_digest": series["record_digest"]},
        "reviewer_actions": {"old_flow_FR_B_by_inspection_of_the_kit": "about 42 actions and at least 3 file switches, 2 codes copied by hand, a special menu exit",
                             "new_flow_measured_in_test_u3": {"per_scenario_without_stop": {"answers": 7, "clicks": 2}, "per_scenario_with_stop": {"answers": 8, "clicks": 2}, "five_required": {"answers": 37, "clicks": 10},
                                                              "files_opened": 0, "codes_copied": 0, "menu_exit": False},
                             "time": "about 4 minutes per scenario is the AUTHOR'S ESTIMATE, never measured with a person"},
        "adversarial_review": {"reviewer": "one independent read-only reviewer, own probes", "blockers": 0, "comparator_leak_before_lock": "NOT_REPRODUCED", "first_pass_editable_after_lock": "NOT_REPRODUCED",
                               "major": {"F1": "record and log could disagree (submit not one critical section): FIXED", "F2": "permanent lock-out after a crash between record and closing event: FIXED",
                                         "F3": "summary counted records that fail verification and said complete: FIXED"},
                               "minor": {"F4": "stale radio overwrote a newer answer: FIXED (callbacks)", "F5": "edits in the same run as a navigation click lost: FIXED (callbacks)", "F6": "wrong optional scenario opened: FIXED",
                                         "F7": "review set self-attested, display fields unchecked: FIXED (pinned in code, cross-checked, item digest in the log identity)", "F8": "disk error showed a traceback with the path: FIXED",
                                         "F9": "forged lock revealed the comparator, malformed event raised: FIXED"},
                               "nits": "FR-E purpose line, summary labelled optional counts, generic 'not offered' text, private summary file, directory fsync and short-write check: FIXED; tripwire false positives on number triples: mitigated by an unsaved-comment warning, not changed (the certified filter is reused)"},
        "unchanged": {"physiology": True, "trajectories": True, "authority": True, "grant": True, "snapshot": True, "cases": True, "scoring": True, "resident_ui": True, "first_pilot": True,
                      "p3_300_checkpoint_record": "byte-identical (the launcher module gains no import: the page is handed in by app.py)"},
        "limits": [
            "Not measured with a human reviewer: the new flow's usability and its time per scenario are untested with a person.",
            "Q5H (stopping point) is added and the common-consciousness questions (Q8, Q9) are left to the live mode: an architect's decision pending faculty confirmation (FD-UX-05).",
            "Heart rate and capillary refill are shown BEFORE the lock as they were shown in the encounter (legacy engine output; no legacy pressure and nothing labelled comparator): a design note.",
            "Unsigned session record and single process (FD-FAC-05, FD-FAC-06): a log or record changed by someone with write access is DETECTED and not counted, not prevented.",
            "One unreadable saved log blocks its scenario until the person who runs the environment moves the file aside (the file is kept).",
            "The identifier tripwire is the certified bundle layer's: it can refuse clinical number triples; the page says so and the text stays in its box.",
        ],
        "verdict": "A_FACULTY_TRAJECTORY_REVIEW_READY_FOR_HUMAN_USE",
        "verdict_enables": "a first human faculty use of the trajectory review in the controlled development environment, and nothing else; not a clinical validation, not a resident pilot, not an authority expansion",
        "statement": "A technical checkpoint of the faculty trajectory review. It is not a clinical validation, an approval of version 1, a consciousness authority, a resident deployment, a production authority or the start of any further phase.",
    }
    return {**body, "record_digest": ftr._digest(body)}


def test_t1_the_checkpoint_record_is_what_the_code_and_the_stored_records_say_now():
    if os.environ.get("MRS_WRITE_TRAJECTORY_REVIEW_CHECKPOINT") == "1":
        RECORD_PATH.write_text(json.dumps(build_record(), indent=1, sort_keys=True), encoding="utf-8")
    assert RECORD_PATH.exists(), "the record is produced once and committed"
    assert json.loads(RECORD_PATH.read_text(encoding="utf-8")) == json.loads(json.dumps(build_record())), "the committed checkpoint no longer matches the code: regenerate it deliberately"


def test_t2_every_status_cites_only_tests_that_exist_and_the_record_claims_nothing_it_may_not():
    record = json.loads(RECORD_PATH.read_text(encoding="utf-8"))
    names = _test_names()
    assert sorted(record["statuses"]) == sorted(["BLINDED_REVIEW_FLOW", "COMPARATOR_REVEAL", "FIRST_PASS_IMMUTABILITY", "AUTOSAVE", "ARTIFACT_LINKAGE", "SCENARIO_NAVIGATION", "SESSION_SUMMARY", "FACULTY_ISOLATION", "RESIDENT_ISOLATION"])
    for key, status in record["statuses"].items():
        assert status["status"] == "VERIFIED_BY_THE_CITED_TESTS" and status["tests"], key
        for prefix in status["tests"]:
            assert any(name.startswith(prefix) for name in names), (key, prefix)
    assert record["pins"]["review_set_loads_pinned"] is True and record["pins"]["required"] == ["FR-B", "FR-A", "FR-E", "FR-G", "FR-F"] and len(record["pins"]["scenarios"]) == 7
    assert record["adversarial_review"]["blockers"] == 0 and all(value.endswith("FIXED") or "FIXED" in value for value in {**record["adversarial_review"]["major"], **record["adversarial_review"]["minor"]}.values())
    assert all(record["unchanged"][key] is True for key in ("physiology", "trajectories", "authority", "grant", "snapshot", "cases", "scoring", "resident_ui", "first_pilot"))
    assert record["verdict"].startswith("A_") and "not a clinical validation" in record["verdict_enables"] and "not a clinical validation" in record["statement"]
    assert any("Not measured with a human" in limit for limit in record["limits"]), "the missing human test is a declared limit"
    text = json.dumps(record).lower()
    assert not any(phrase in text for phrase in ("clinically validated", "validated clinically", "approved for residents", "proves the physiology"))
    p300 = json.loads((ROOT / "docs" / "revision" / "PHASE3_FACULTY_REVIEW_CHECKPOINT.json").read_text(encoding="utf-8"))
    assert p300["record_digest"] == "45b62670af0983f3513e5ec5b290ff866da073b3100177dfa5f4d1a5729c89b2", "the P3-300 checkpoint is untouched"
