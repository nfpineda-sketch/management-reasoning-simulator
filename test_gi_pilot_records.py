"""P3-518, P3-519, P3-520 and P3-527: the BUILDER of the records of the GI management-trace ratification and of the controlled development pilot's scope (a tool, never
imported by a page; it holds no test).

WHAT IT DOES. It turns the human faculty review of ``GI_MANAGEMENT_TRACE_V1_FACULTY_REVIEW`` and the faculty decisions FD-PILOT-01 to FD-PILOT-08 into durable, sealed,
indexed records, and changes NOTHING executable:

* ``PHASE3_HUMAN_GI_MANAGEMENT_TRACE_REVIEW.json`` -- the HUMAN evidence exactly as the faculty reported it (provenance ``HUMAN_FACULTY_REVIEW_REPORTED_NOT_STORE_VERIFIED``:
  the persisted review store is not in this container). Only the ten overall judgments and the seven review findings were reported: the answers Q1 to Q6, per-path comments,
  lock events, timestamps and the reviewer's identity were NOT, and none is invented;
* ``GI_MANAGEMENT_TRACE_V1_RATIFICATION.json`` -- ``GI_MANAGEMENT_TRACE_V1`` ``RATIFIED_FOR_CONTROLLED_DEVELOPMENT_PILOT_PREPARATION`` (not clinical validation, not production
  approval, not resident deployment), with the decisions, what is not reopened, the management meanings as FACULTY INTERPRETATIONS and H1/H2 open;
* ``GI_MANAGEMENT_TRACE_PILOT_SCOPE_V1.json`` -- the pilot's scope (INCLUDED / EXCLUDED / DEFERRED), the visible-field classification, the fail-safe rules and the case selection,
  read from ``gi_pilot`` (the module the pilot executes), so the record and the code cannot say two things.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import faculty_management_review as fmr
import faculty_trajectory_review as ftr
import gi_pilot as gp
import historical_records as hr

ROOT = Path(__file__).resolve().parent
REV = ROOT / "docs" / "revision"
GENERATED_ON = "2026-11-22"
HUMAN_PATH = REV / "PHASE3_HUMAN_GI_MANAGEMENT_TRACE_REVIEW.json"
RATIFICATION_PATH = REV / "GI_MANAGEMENT_TRACE_V1_RATIFICATION.json"
SCOPE_PATH = REV / "GI_MANAGEMENT_TRACE_PILOT_SCOPE_V1.json"
HUMAN_ID = "HUMAN_GI_MANAGEMENT_TRACE_REVIEW_V1"
RATIFICATION_ID = "GI_MANAGEMENT_TRACE_V1_RATIFICATION"
SCOPE_ID = "GI_MANAGEMENT_TRACE_PILOT_SCOPE_V1"
REPORTED_IN = ("the assignment of 2026-11-22 that opened P3-518 ('PHASE 3 — RATIFY END-TO-END GI MANAGEMENT TRACE AND PREPARE CONTROLLED RESIDENT PILOT READINESS')")
PROVENANCE_CLASS = "HUMAN_FACULTY_REVIEW_REPORTED_NOT_STORE_VERIFIED"

#: The ten overall judgments, as reported ("10 paths reviewed: ACCEPT_WITH_LIMITATION = 10"). Nothing per path was reported beyond the judgment.
REPORTED = {scenario_id: "ACCEPT_WITH_LIMITATION" for scenario_id in fmr.SCENARIOS}
REPORTED_COUNTS = {"ACCEPT": 0, "ACCEPT_WITH_LIMITATION": 10, "RECALIBRATE": 0, "REJECT": 0}
#: The review's findings, in the words they were reported in (one list for the whole review; none is attributed to a path).
REPORTED_FINDINGS = ["causal coherence across all ten paths", "no path requiring recalibration", "negative/incomplete paths are educationally useful when clearly framed",
                     "ongoing hemorrhage remains visible", "norepinephrine is shown as temporary pressure support, not definitive treatment",
                     "blood/crystalloid do not imply hemorrhage control", "no resident reasoning is inferred"]

DECISIONS = {
    "FD-PILOT-01": "Ratify GI_MANAGEMENT_TRACE_V1 as RATIFIED_FOR_CONTROLLED_DEVELOPMENT_PILOT_PREPARATION; NOT clinical validation, production approval or resident deployment yet.",
    "FD-PILOT-02": ("The ten reviewed management paths establish sufficient development evidence that the end-to-end Management Trace construct is causally and educationally coherent. "
                    "Do NOT reopen GI pressure calibration, common-tone calibration, norepinephrine manual-rate calibration, parser/order safety or management-path calibration unless a material "
                    "contradiction appears during pilot preparation or actual use."),
    "FD-PILOT-03": ("Preserve the reviewed management meanings as FACULTY INTERPRETATIONS: reasonable, temporizing, incomplete, clearly nonbeneficial. Do NOT automatically convert them into "
                    "resident scores. Do NOT hard-code them as correctness labels."),
    "FD-PILOT-04": ("H1 remains open: the live engine can perform hemostasis after GI consultation. For the pilot-preparation package: BLOCK or BOUND the encounter before unreviewed "
                    "definitive hemostasis. Do NOT silently allow an unreviewed source-control trajectory."),
    "FD-PILOT-05": ("H2 remains open: mental status under norepinephrine is nonauthoritative. Do NOT expose tone-driven or pressure-derived consciousness as validated feedback. "
                    "Resident-visible mental status must be clearly classified as legacy / nonauthoritative or omitted where necessary to avoid misleading feedback."),
    "FD-PILOT-06": ("Current pilot scope: GI hemorrhagic shock only. Do NOT include pump-limited vasopressor cases, pulmonary edema vasopressor use, ACS vasopressor use, other vasopressors, "
                    "target-based norepinephrine titration, weight-based norepinephrine dosing."),
    "FD-PILOT-07": ("Primary pilot question: can a resident manage a synthetic hemorrhagic-shock encounter, make sequential decisions, observe coherent consequences, and receive a Management "
                    "Trace that is useful for reflection without exposing internal model variables or unsafe interpretations?"),
    "FD-PILOT-08": "The pilot must remain faculty-supervised, development-only, small, reversible and isolated from scoring / summative assessment. No performance consequences.",
}
NOT_REOPENED = ["GI pressure calibration", "common-tone calibration", "norepinephrine manual-rate calibration", "parser/order safety", "management-path calibration"]
MEANINGS = ["reasonable", "temporizing", "incomplete", "clearly nonbeneficial"]
IS_NOT = ["clinical validation", "production approval", "resident deployment", "a resident score or a correctness label", "an approval of any management in a real patient"]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generating_code() -> dict:
    from clinical_core import amendment_3 as a3
    return {"clinical_core": a3.amended_core_digest_now(), "test_gi_pilot_records.py": _sha(Path(__file__).resolve()), "faculty_management_review.py": _sha(ROOT / "faculty_management_review.py"),
            "gi_pilot.py": _sha(ROOT / "gi_pilot.py")}


def _file(path: Path) -> dict:
    record = json.loads(path.read_text(encoding="utf-8"))
    return {"file": str(path.relative_to(ROOT)), "record_digest": record.get("record_digest"), "file_sha256": _sha(path)}


def preserved() -> dict:
    """The earlier records this one rests on, by digest and file hash: preserved, not rewritten."""
    return {"management_review_set": _file(fmr.SET_PATH), "management_trace_checkpoint": _file(REV / "PHASE3_GI_MANAGEMENT_TRACE_CHECKPOINT.json"),
            "management_review_set_digest_pinned_in_code": fmr.PINNED_SET_DIGEST}


def counts(judgments: dict) -> dict:
    out = {choice: 0 for choice in ftr.OVERALL}
    for value in judgments.values():
        out[value] += 1
    return out


def build_human() -> dict:
    loaded = fmr.load_set()
    if not loaded["ok"]:
        raise ValueError(f"the reviewed set does not verify: {loaded['problems']}")
    if counts(REPORTED) != REPORTED_COUNTS:
        raise ValueError("the reported totals are not the tabulation of the reported judgments")
    scenarios = []
    for scenario_id in fmr.SCENARIOS:
        item = loaded["items"][scenario_id]
        scenarios.append({"scenario_id": scenario_id, "title_in_the_set": item["title"], "overall": REPORTED[scenario_id], "first_pass_answers_Q1_to_Q5": "NOT_REPORTED",
                          "management_meaning_Q6": "NOT_REPORTED", "free_text_comments": "NONE_REPORTED", "recalibration_requested": False, "reviewed_item_digest": ftr.item_digest(item)})
    body = {"record_type": "HUMAN_FACULTY_GI_MANAGEMENT_TRACE_REVIEW_RECORD", "version": "P3-518", "evidence_class": "HUMAN_FACULTY_REVIEW",
            "evidence_classes": {"HUMAN_FACULTY_REVIEW": "what the faculty reviewer judged in the review of the ten GI management paths, as reported; only this record and the Decision File rows FD-PILOT-01 to FD-PILOT-08 carry it",
                                 "MODEL_ANALYSIS": "what the development assistant computed or read from the executable model and the certified records; it explains and bounds, it does not judge",
                                 "TEST_RESULT": "what an automated test asserted; it protects a record, it is not a faculty decision"},
            "what_it_is": ("The human faculty review of the ten development management paths of one GI haemorrhage case (the Management Trace construct GI_MANAGEMENT_TRACE_V1), recorded as HUMAN "
                           "evidence as the reviewer reported it. It is not converted into an automated truth, it is not a clinical validation, and nothing in it was written by a model. No answer, "
                           "comment, event or timestamp that was not reported was added."),
            "review": {"review_set_id": fmr.SET_ID, "review_set_digest": loaded["digest"], "paths_reviewed": len(scenarios), "scenario_order_in_the_set": list(fmr.SCENARIOS),
                       "completion_as_reported": "COMPLETE (10 of 10 judgments reported)", "completion_screen_string": "NOT_REPORTED",
                       "item_digests_note": "computed here from the pinned set (what the review logs carry); the faculty did not report them"},
            "scenarios": scenarios, "overall_counts": dict(REPORTED_COUNTS), "overall_counts_recomputed_from_the_scenarios": counts(REPORTED),
            "reported_findings": list(REPORTED_FINDINGS), "reported_findings_scope": "the whole review; none is attributed to a single path",
            "provenance_of_the_evidence": {"date_of_record": GENERATED_ON, "verification": PROVENANCE_CLASS, "reported_in": REPORTED_IN, "persisted_store_available_to_the_assistant": False,
                                          "reviewer_identity_recorded": False, "reviewer_name": None, "reviewer_role": "faculty",
                                          "transcribed_by": "the development assistant; the ten judgments and the seven findings are typed once from the report and nothing was added",
                                          "why": ("no persisted management-review log exists in this container (a search found only the assistant's own transcripts, which are not human evidence); the "
                                                  "assignment asked to read the store if available and, if not, to use the reported results and mark the provenance, without inventing Q1 to Q6, comments, "
                                                  "timestamps or reviewer identity")},
            "not_verified": ["the answers Q1 to Q5 (not reported)", "the management meaning Q6 per path (not reported)", "the overall judgments against the persisted logs", "the completion screen",
                             "the lock and submit events, their order and their timestamps", "free-text comments (none were reported per path)", "the reviewer's identity"],
            "not_in_this_record": ["the reviewer's name", "any model-written judgment", "any clinical-validation claim", "the per-event logs (they live in the reviewer's own store)"],
            "preserved_original_evidence": preserved()}
    body["provenance"] = hr.provenance(record_id=HUMAN_ID, generating_code=generating_code(), generated_on=GENERATED_ON,
                                       source_data={"reported": REPORTED, "counts": REPORTED_COUNTS, "findings": REPORTED_FINDINGS, "set_digest": loaded["digest"]})
    return hr.seal(body)


def build_ratification(human: dict) -> dict:
    body = {"record_type": "GI_MANAGEMENT_TRACE_RATIFICATION", "version": "P3-519", "ratification_id": RATIFICATION_ID, "date": GENERATED_ON, "construct": gp.RATIFIED_CONSTRUCT,
            "status": gp.RATIFIED_STATUS, "status_meaning": "accepted to PREPARE a small, faculty-supervised, development-only pilot; nothing more", "is_not": list(IS_NOT),
            "faculty_decisions": dict(DECISIONS), "human_record": {"file": str(HUMAN_PATH.relative_to(ROOT)), "record_digest": human["record_digest"], "verification": PROVENANCE_CLASS,
                                                                    "overall_counts": human["overall_counts"]},
            "not_reopened": list(NOT_REOPENED), "reopen_only_if": "a material contradiction appears during pilot preparation or actual use",
            "management_meanings": {"values": list(MEANINGS), "status": "FACULTY_INTERPRETATIONS", "converted_into_scores": False, "hard_coded_as_correctness_labels": False,
                                    "shown_to_participants": False},
            "open_findings": {"H1": {"status": "OPEN", "statement": "the live engine can perform haemostasis after a gastroenterology consultation; never reviewed",
                                     "pilot_handling": "BOUNDED: a request for definitive control is recorded and not carried out, and the encounter ends at the development boundary (gi_pilot)"},
                              "H2": {"status": "OPEN", "statement": "mental status under norepinephrine is nonauthoritative (the earlier model's), decoupled from the development pressure",
                                     "pilot_handling": "classified as the earlier model's on every pilot surface and withheld once norepinephrine has been given (gi_pilot)"}},
            "bound_to": {"review_set_id": fmr.SET_ID, "review_set_digest": fmr.PINNED_SET_DIGEST, "management_trace_checkpoint": _file(REV / "PHASE3_GI_MANAGEMENT_TRACE_CHECKPOINT.json")},
            "authority": {"common_core_runtime_authority": False, "expanded": False, "grant_changed": False, "snapshot_changed": False},
            "physiology_change": False, "calibration_change": False, "scoring_change": False, "preserved_original_evidence": preserved()}
    body["provenance"] = hr.provenance(record_id=RATIFICATION_ID, generating_code=generating_code(), generated_on=GENERATED_ON,
                                       source_data={"human": human["record_digest"], "decisions": DECISIONS, "not_reopened": NOT_REOPENED, "meanings": MEANINGS})
    return hr.seal(body)


def build_scope(ratification: dict) -> dict:
    body = {"record_type": "GI_MANAGEMENT_TRACE_PILOT_SCOPE", "version": "P3-520", "scope_id": SCOPE_ID, "pilot_id": gp.PILOT_ID, "date": GENERATED_ON, "decision_reference": gp.DECISIONS,
            "ratification": {"file": str(RATIFICATION_PATH.relative_to(ROOT)), "record_digest": ratification["record_digest"], "status": gp.RATIFIED_STATUS},
            "scope": gp.plain(gp.SCOPE), "visible_field_classes": [{"field": field, "class": cls, "how": how} for field, cls, how in gp.FIELD_CLASSES],
            "fail_safe": [{"situation": situation, "behaviour": behaviour, "exit": exit_kind} for situation, behaviour, exit_kind in gp.FAIL_SAFE],
            "case_selection": {"pilot_cases": list(gp.PILOT_CASES), "challenge_id": gp.CHALLENGE_ID,
                               "why": ("the smallest set that uses only reviewed behaviour: the ten faculty-reviewed paths are all of gi_bleed_57m, and in that one case the course itself gives both "
                                       "pilot situations -- volume and blood with reassessment, and a pressure that falls again so that norepinephrine at an explicit rate becomes a decision; "
                                       "gi_bleed_72f runs under the same authority but was not part of the human management-trace review, so it is DEFERRED"),
                               "not_maximized": True},
            "configuration": {"flag": gp.FLAG, "flag_value": gp.MODE_ON, "store_flag": gp.STORE_FLAG, "default": "OFF", "fails_closed": True,
                              "requires": ["individual accounts", "not a hosted public deployment", "not the first resident pilot's deployment", "not the faculty development review environment",
                                           "the published development configuration (pressure authority, ratified pressure snapshot, tone snapshot, development environment, shadow)",
                                           "a pilot record directory outside the repository", "no AI key", "the image bank off"]},
            "isolation_from_scoring": {"account_attempt_created": False, "reaches_progress_portfolio_rubric_or_evaluation": False, "legacy_post_encounter_review_layer": "EXCLUDED",
                                       "faculty_categories_shown_to_participants": False},
            "identifiers": {"participant": "pseudonymous reference P-<12 hex> (a hash of the account id with the pilot id; the account id is never stored)",
                            "faculty": "pseudonymous reference F-<12 hex>", "encounter": "synthetic PE-<16 hex>",
                            "free_text": "the participant's orders and stated reasoning are kept (they are the encounter); the pilot notice asks for no personal information"},
            "starting_the_real_pilot": "NOT authorized by this record: a separate faculty decision, and the hard stop of P3-533 holds"}
    body["provenance"] = hr.provenance(record_id=SCOPE_ID, generating_code=generating_code(), generated_on=GENERATED_ON,
                                       source_data={"ratification": ratification["record_digest"], "scope": gp.plain(gp.SCOPE), "fields": gp.plain(gp.FIELD_CLASSES),
                                                    "fail_safe": gp.plain(gp.FAIL_SAFE), "cases": list(gp.PILOT_CASES)})
    return hr.seal(body)


def build() -> dict:
    human = build_human()
    ratification = build_ratification(human)
    return {"human": human, "ratification": ratification, "scope": build_scope(ratification)}


PATHS = {"human": HUMAN_PATH, "ratification": RATIFICATION_PATH, "scope": SCOPE_PATH}


def write_all() -> dict:
    """Write the three records; ``historical_records.write`` refuses to replace a record with other content."""
    made = build()
    return {str(path.relative_to(ROOT)): hr.write(path, made[key]) for key, path in PATHS.items()}


def reproduce() -> dict:
    """The CONTENT of the three records, regenerated, without provenance or seal: what a test compares with the stored records."""
    return {key: {name: value for name, value in record.items() if name not in ("provenance", "record_digest")} for key, record in build().items()}


if __name__ == "__main__":
    print(json.dumps(write_all(), indent=2))
