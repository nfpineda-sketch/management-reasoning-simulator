"""P3-415 to P3-422 (records): the human review of the multifamily tone trajectories, the development snapshot and the ratification are sealed, indexed, bound to what the faculty reviewed, and change nothing executable.

What it proves (the documents, the decisions and the checkpoint are tested apart, in test_phase3_tone_ratification_records.py, which is the second commit of the publication):

* the HUMAN record is exactly what the faculty reported (the typed judgments equal the reported ones, every answer is a valid choice of the real question, the reported totals are the tabulation of the judgments), is marked
  ``HUMAN_FACULTY_REVIEW_REPORTED_NOT_STORE_VERIFIED`` because the persisted store is not in the repository, invents no comment and names no reviewer, and is bound to the pinned review set by the digest of every reviewed item;
* every earlier faculty review and record this one rests on is preserved: its file is the one the index pins;
* the classification is the faculty's: no scenario is a MECHANISM_FAILURE, the pulmonary-edema REJECT is an INAPPROPRIATE_INTERVENTION_CONTEXT and a negative-control candidate, every classification quotes the recorded human text
  it rests on and the quotation is in the human record; a mutation that makes the REJECT a mechanism failure, or a RECALIBRATE, or removes a quotation, is caught;
* the snapshot copies the CENTER_REFERENCE binding that the faculty reviewed (equal in the core, in the certified probes and in the certified FR-F candidate, never recomputed), LOW and HIGH stay test witnesses, and nothing
  executable reads the snapshot;
* the limitations are persisted with the statuses the faculty gave, and titration and stop are the next priority and are NOT implemented;
* nothing executable changed: no physiology, no parameter, no pump coupling, no authority, no grant.
"""
import copy
import hashlib
import json
import re
from pathlib import Path

import pytest

import faculty_tone_review as ftm
import faculty_trajectory_review as ftr
import historical_records as hr
import test_tone_pathway_analysis as ta
import test_tone_ratification_analysis as build

ROOT = Path(__file__).resolve().parent
REV = ROOT / "docs" / "revision"
CORE_DIGEST = "867bac09e09bb5c04629e73fbbdec0f7e1f100da17ef8966f580ba91067a7c9c"
CENTER = {"half_effect_rate_mcg_min": 10.0, "offset_tau_min": 2.5, "onset_tau_min": 1.5, "tone_gain": 0.6}
LOW = {"half_effect_rate_mcg_min": 20.0, "offset_tau_min": 1.0, "onset_tau_min": 3.0, "tone_gain": 0.3}
HIGH = {"half_effect_rate_mcg_min": 5.0, "offset_tau_min": 5.0, "onset_tau_min": 0.5, "tone_gain": 0.9}
#: Typed a SECOND time, here, independently of the builder: what the faculty reported (the order of the review; the five answers Q1 to Q5).
REPORT = {"FR-F": ("ACCEPT_WITH_LIMITATION", ("Expected", "Plausible", "Plausible", "Coherent", "Maybe")),
          "SYNTH": ("ACCEPT", ("Expected", "Plausible", "Plausible", "Coherent", "No")),
          "ACS": ("ACCEPT_WITH_LIMITATION", ("Expected", "Plausible", "Plausible", "Uncertain", "Yes")),
          "PULM-EDEMA": ("REJECT", ("Expected", "Plausible", "Too large", "Incoherent", "Yes")),
          "PE": ("ACCEPT_WITH_LIMITATION", ("Expected", "Plausible", "Plausible", "Coherent", "Maybe"))}
FILES = {"human": "PHASE3_HUMAN_COMMON_TONE_MULTIFAMILY_REVIEW.json", "snapshot": "COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1.json", "ratification": "COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1_RATIFICATION.json"}


def _load(name: str) -> dict:
    return json.loads((REV / name).read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


HUMAN, SNAPSHOT, RATIFICATION = (_load(FILES[key]) for key in ("human", "snapshot", "ratification"))
PROBES, FRF = ta.load(ta.PROBES_PATH), ta.load(ta.CANDIDATE_PATH)
SET = ftm.load_set()
ROOT_MODULES = sorted(path for path in ROOT.glob("*.py") if not path.name.startswith("test_") and path.name != "conftest.py")


def _problems(human: dict, ratification: dict) -> list:
    """Everything in which the ratification disagrees with the human record. Empty means every classification is the faculty's and every quotation is in the record."""
    out = []
    questions = {question["id"]: question["choices"] for question in ftr.FIRST_PASS}
    counts = {choice: 0 for choice in ftr.OVERALL}
    by_id = {entry["scenario_id"]: entry for entry in human["scenarios"]}
    for scenario_id, entry in by_id.items():
        if entry["overall"] not in ftr.OVERALL:
            out.append(f"{scenario_id}: not an overall judgment")
            continue
        counts[entry["overall"]] += 1
        for question, answer in entry["first_pass"].items():
            if answer not in questions.get(question, ()):
                out.append(f"{scenario_id} {question}: not a choice of the real question")
    if counts != human["overall_counts"]:
        out.append("the reported totals are not the tabulation of the judgments")
    for scenario_id, entry in ratification["scenario_classification"].items():
        text = by_id[scenario_id]["faculty_interpretation_as_reported"]
        if entry["classification"] not in (*build.VOCABULARY, "DEVELOPMENT_POSITIVE_CONTROL"):
            out.append(f"{scenario_id}: unknown classification")
        if entry["classification"] == "MECHANISM_FAILURE" or entry["mechanism_failure"]:
            out.append(f"{scenario_id}: a mechanism failure is not in the recorded human judgment")
        if by_id[scenario_id]["overall"] == "RECALIBRATE" or entry["global_recalibration_requested"]:
            out.append(f"{scenario_id}: a recalibration is not in the recorded human judgment")
        for quotation in entry["human_basis"]:
            if quotation not in text:
                out.append(f"{scenario_id}: a quotation that is not in the human record: {quotation[:40]}")
        if by_id[scenario_id]["overall"] == "REJECT" and entry["classification"] != "INAPPROPRIATE_INTERVENTION_CONTEXT":
            out.append(f"{scenario_id}: a REJECT whose recorded reason is the management context must be classified by that reason")
    return out


# ------------------------------------------------------------------------------------------------------------------------------------ P3-415 · the human review, as reported
def test_t1_the_three_records_are_sealed_versioned_and_indexed_with_the_bytes_the_index_pins():
    index = hr.load_index(ROOT)
    for key, name in FILES.items():
        record = {"human": HUMAN, "snapshot": SNAPSHOT, "ratification": RATIFICATION}[key]
        assert hr.record_problems(record) == [], name
        block = record["provenance"]
        assert block["contract"] == hr.CONTRACT and block["generated_on"] == "2026-11-18" and block["supersedes"] is None and block["record_id"] == record["provenance"]["record_id"]
        entry = index["records"][name]
        assert entry["class"] == hr.VERSIONED and entry["record_id"] == block["record_id"] and entry["record_digest"] == record["record_digest"] and entry["file_sha256"] == hr.file_sha256(REV / name)
    assert {HUMAN["provenance"]["record_id"], SNAPSHOT["provenance"]["record_id"], RATIFICATION["provenance"]["record_id"]} == {build.HUMAN_ID, build.SNAPSHOT_ID, build.RATIFICATION_ID}
    assert hr.index_problems(ROOT) == []


def test_t2_the_human_record_is_exactly_what_the_faculty_reported_in_the_order_of_the_review():
    assert [entry["scenario_id"] for entry in HUMAN["scenarios"]] == list(ftm.SCENARIOS) == list(REPORT)
    for entry in HUMAN["scenarios"]:
        overall, answers = REPORT[entry["scenario_id"]]
        assert entry["overall"] == overall and tuple(entry["first_pass"][question] for question in ("Q1", "Q2", "Q3", "Q4", "Q5")) == answers, entry["scenario_id"]
        assert list(entry["first_pass"]) == ["Q1", "Q2", "Q3", "Q4", "Q5"]
    assert HUMAN["overall_counts"] == {"ACCEPT": 1, "ACCEPT_WITH_LIMITATION": 3, "RECALIBRATE": 0, "REJECT": 1} == HUMAN["overall_counts_recomputed_from_the_scenarios"]
    assert HUMAN["review"]["scenarios_with_reported_judgments"] == 5 and HUMAN["review"]["candidate_reviewed"] == "CENTER_REFERENCE" and HUMAN["review"]["pressure_only_first_pass"] is True
    assert HUMAN["review"]["candidate_named_by_the_interface"] is False


def test_t3_every_answer_is_a_valid_choice_of_the_real_question_and_the_record_is_consistent_with_the_ratification():
    assert _problems(HUMAN, RATIFICATION) == []


def test_t4_the_faculty_interpretation_is_transcribed_with_the_words_of_the_report_and_its_key_statements_are_present():
    by_id = {entry["scenario_id"]: entry["faculty_interpretation_as_reported"] for entry in HUMAN["scenarios"]}
    assert "attenuates while hemorrhage remains untreated" in by_id["FR-F"] and "must not be interpreted as correction of underlying volume loss" in by_id["FR-F"]
    assert "clean development-positive control" in by_id["SYNTH"] and "without unrealistically returning" in by_id["SYNTH"]
    assert "pump-dependence limitation" in by_id["ACS"] and "Do NOT globally recalibrate the tone pathway from this scenario." in by_id["ACS"]
    assert "profoundly hypertensive" in by_id["PULM-EDEMA"] and "clinically inappropriate" in by_id["PULM-EDEMA"]
    assert "primarily a judgment of the MANAGEMENT CONTEXT / EDUCATIONAL USE of this intervention" in by_id["PULM-EDEMA"]
    assert "NOT, by itself, evidence that the common vascular-tone mechanism requires global recalibration" in by_id["PULM-EDEMA"] and "Do NOT retune T merely" in by_id["PULM-EDEMA"]
    assert "obstructive shock" in by_id["PE"] and "must not imply correction of the pulmonary vascular obstruction" in by_id["PE"]
    assert all(entry["free_text_comments"] == "NONE_REPORTED" and entry["recalibration_in_isolation_requested"] is False for entry in HUMAN["scenarios"])


def test_t5_the_provenance_is_marked_reported_not_verified_and_nothing_is_invented():
    provenance = HUMAN["provenance_of_the_evidence"]
    assert provenance["verification"] == "HUMAN_FACULTY_REVIEW_REPORTED_NOT_STORE_VERIFIED" == build.PROVENANCE_CLASS
    assert provenance["persisted_store_available_to_the_assistant"] is False and provenance["reviewer_identity_recorded"] is False and provenance["reviewer_name"] is None
    assert HUMAN["evidence_class"] == "HUMAN_FACULTY_REVIEW" and set(HUMAN["evidence_classes"]) == {"HUMAN_FACULTY_REVIEW", "MODEL_ANALYSIS", "TEST_RESULT"}
    assert HUMAN["review"]["optional_sensitivity_check"].startswith("NOT_REPORTED")
    for text in ("the answers Q1 to Q5 and the overall judgments against the persisted logs", "the lock and submit events and their order", "free-text comments (none were reported)"):
        assert text in HUMAN["not_verified"], text
    assert "the reviewer's name" in HUMAN["not_in_this_record"] and "any model-written judgment" in HUMAN["not_in_this_record"]
    # there is no persisted review store in the repository: the faculty's own logs live in the reviewer's store, never committed
    assert not list(ROOT.glob("tone_review*")) and not list(ROOT.glob("tone_sensitivity*"))


def test_t6_the_record_is_bound_to_the_pinned_set_by_the_digest_of_every_reviewed_item():
    assert HUMAN["review"]["review_set_id"] == ftm.SET_ID and HUMAN["review"]["review_set_digest"] == ftm.PINNED_SET_DIGEST == SET["digest"]
    for entry in HUMAN["scenarios"]:
        item = SET["items"][entry["scenario_id"]]
        assert entry["reviewed_item_digest"] == ftr.item_digest(item), entry["scenario_id"]
        assert entry["reviewed_trajectory_digest"] == hr.digest_of({"scenario_id": entry["scenario_id"], "timeline": item["timeline"], "common": item["common"]})
    assert {entry["scenario_id"]: entry["reviewed_item_digest"] for entry in HUMAN["scenarios"]} == {"FR-F": "d8ca8ea38d43", "SYNTH": "92728a6fa840", "ACS": "c1e87b70f49b", "PULM-EDEMA": "6709f611aa8b", "PE": "eb8970436cfb"}


def test_t7_every_earlier_faculty_review_and_record_is_preserved_byte_for_byte():
    index = hr.load_index(ROOT)["records"]
    preserved = HUMAN["preserved_original_evidence"]
    assert preserved == RATIFICATION["preserved_original_evidence"]
    for key in ("first_human_review", "human_rereview", "tone_review_set", "tone_review_checkpoint", "tone_probes", "frf_candidate"):
        entry = preserved[key]
        assert hr.file_sha256(ROOT / entry["file"]) == entry["file_sha256"] == index[Path(entry["file"]).name]["file_sha256"], key
        assert json.loads((ROOT / entry["file"]).read_text(encoding="utf-8")).get("record_digest") == entry["record_digest"], key
    assert preserved["first_review_set_digest_pinned_in_code"] == ftr.PINNED_SET_DIGEST and preserved["tone_review_set_digest_pinned_in_code"] == ftm.PINNED_SET_DIGEST


# ------------------------------------------------------------------------------------------------------------------------------------ P3-416 · the classification
def test_t8_no_scenario_is_a_mechanism_failure_and_the_edema_reject_is_an_inappropriate_intervention_context():
    scenarios = RATIFICATION["scenario_classification"]
    assert RATIFICATION["mechanism_failures"] == [] and all(entry["mechanism_failure"] is False and entry["global_recalibration_requested"] is False for entry in scenarios.values())
    assert {key: entry["classification"] for key, entry in scenarios.items()} == {"FR-F": "EDUCATIONAL_LIMITATION", "SYNTH": "DEVELOPMENT_POSITIVE_CONTROL", "ACS": "EDUCATIONAL_LIMITATION",
                                                                                 "PULM-EDEMA": "INAPPROPRIATE_INTERVENTION_CONTEXT", "PE": "EDUCATIONAL_LIMITATION"}
    assert scenarios["PULM-EDEMA"]["overall"] == "REJECT" and scenarios["PULM-EDEMA"]["negative_control_candidate"] is True
    assert RATIFICATION["classification_vocabulary"] == ["MECHANISM_FAILURE", "INAPPROPRIATE_INTERVENTION_CONTEXT", "EDUCATIONAL_LIMITATION"]
    assert RATIFICATION["scenario_classification"]["SYNTH"]["limitation_ids"] == [] and RATIFICATION["scenario_classification"]["ACS"]["limitation_ids"] == ["COMMON_TONE_PUMP_DEPENDENCE_NOT_YET_VALIDATED"]


def test_t9_the_audit_of_the_pulmonary_edema_reject_reads_the_recorded_judgment_and_changes_nothing():
    audit = RATIFICATION["pulmonary_edema_audit"]
    assert audit["does_the_recorded_judgment_support_mechanism_failure"] is False and audit["classification"] == "INAPPROPRIATE_INTERVENTION_CONTEXT" and audit["negative_control_candidate"] is True
    assert audit["recorded_human_judgment"] == {"overall": "REJECT", "Q1": "Expected", "Q2": "Plausible", "Q3": "Too large", "Q4": "Incoherent", "Q5": "Yes"}
    assert audit["recorded_human_judgment"] == {"overall": "REJECT", **HUMAN["scenarios"][3]["first_pass"]} and HUMAN["scenarios"][3]["scenario_id"] == "PULM-EDEMA"
    assert "no scenario was RECALIBRATE" in audit["why_not"] and "NOT by itself evidence" in audit["why_not"]
    model = audit["model_analysis"]
    assert model["evidence_class"] == "MODEL_ANALYSIS" and model["does_not_judge"] is True
    for family, entry in model["by_family"].items():
        observed = PROBES["family_probes"][family]["witnesses"]["CENTER_REFERENCE"]["observed"][-1]
        assert (entry["pressure_ratio"], entry["map_gain_mmhg"], entry["map_without"], entry["map_with"], entry["minute"]) == (observed["pressure_ratio"], observed["map_gain_mmhg"], observed["map_without"],
                                                                                                                              observed["map_with"], observed["minute"]), family
    ratios = {family: entry["pressure_ratio"] for family, entry in model["by_family"].items()}
    assert ratios["pulmonary_edema"] == ratios["gi_bleed"] == ratios["asthma"] == ratios["opioid"] < ratios["acs"], "the relative response of the SAME mechanism is the same where the model says it is"
    gains = {family: entry["map_gain_mmhg"] for family, entry in model["by_family"].items()}
    assert max(gains, key=gains.get) == "pulmonary_edema" and model["by_family"]["pulmonary_edema"]["map_without"] == max(entry["map_without"] for entry in model["by_family"].values())
    assert "no change to T, to the pump coupling or to any parameter follows from it" in model["consequence"]
    assert RATIFICATION["negative_control"]["physiology_altered"] is False and RATIFICATION["negative_control"]["norepinephrine_made_unavailable"] is False
    assert RATIFICATION["negative_control"]["id"] == "HYPERTENSIVE_PULMONARY_EDEMA_NOREPI" and RATIFICATION["negative_control"]["classification"] == "INAPPROPRIATE_INTERVENTION_CONTEXT"


def test_t10_mutants_the_validator_catches_a_classification_the_human_record_does_not_support():
    assert _problems(HUMAN, RATIFICATION) == []
    mutants = []
    for label, mutate in {
        "the edema reject as a mechanism failure": lambda h, r: r["scenario_classification"]["PULM-EDEMA"].update(classification="MECHANISM_FAILURE", mechanism_failure=True),
        "the edema reject without its reason": lambda h, r: r["scenario_classification"]["PULM-EDEMA"].update(classification="EDUCATIONAL_LIMITATION"),
        "a global recalibration requested from the acs review": lambda h, r: r["scenario_classification"]["ACS"].update(global_recalibration_requested=True),
        "a quotation the human record does not hold": lambda h, r: r["scenario_classification"]["PE"]["human_basis"].append("the faculty asked to retune the tone gain"),
        "an overall judgment that is not a choice": lambda h, r: h["scenarios"][0].update(overall="ACCEPT_WITH_RESERVATIONS"),
        "an answer that is not a choice of the real question": lambda h, r: h["scenarios"][1]["first_pass"].update(Q3="Huge"),
        "a total that is not the tabulation": lambda h, r: h["overall_counts"].update(REJECT=0, RECALIBRATE=1),
        "an edema review turned into a recalibration": lambda h, r: h["scenarios"][3].update(overall="RECALIBRATE"),
    }.items():
        human, ratification = copy.deepcopy(HUMAN), copy.deepcopy(RATIFICATION)
        mutate(human, ratification)
        mutants.append((label, _problems(human, ratification)))
    for label, found in mutants:
        assert found, f"the validator did not catch: {label}"


# ------------------------------------------------------------------------------------------------------------------------------------ P3-417 / P3-418 · the ratification and the snapshot
def test_t11_the_snapshot_copies_the_exact_binding_the_faculty_reviewed_and_never_recomputes_it():
    from clinical_core import vascular_support as vs
    assert SNAPSHOT["binding"] == CENTER == {key: float(value) for key, value in vs.witness("CENTER_REFERENCE").items()}
    assert SNAPSHOT["binding"] == PROBES["witnesses"]["CENTER_REFERENCE"] == FRF["witnesses"]["CENTER_REFERENCE"]["witness"]
    source = SNAPSHOT["binding_source"]
    assert source["copied_not_recomputed"] is True and source["optimized"] is False and source["another_point_considered"] is False and all(source["equal_in_every_certified_source"].values())
    assert source["core_digest"] == CORE_DIGEST and source["probes_record"]["file_sha256"] == _sha(ta.PROBES_PATH) and source["frf_candidate"]["file_sha256"] == _sha(ta.CANDIDATE_PATH)
    assert SNAPSHOT["snapshot_id"] == "COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1" and SNAPSHOT["selected_witness"] == "CENTER_REFERENCE" and SNAPSHOT["status"] == "RATIFIED_FOR_DEVELOPMENT_EXPERIMENTS"
    assert SNAPSHOT["binding_units"] == {"half_effect_rate_mcg_min": "mcg/min", "offset_tau_min": "min", "onset_tau_min": "min", "tone_gain": "fraction of the arrival tone"}
    assert "none may be replaced by another witness's value" in SNAPSHOT["bound_together"]


def test_t12_the_snapshot_binding_is_one_point_of_the_region_and_low_and_high_stay_test_witnesses():
    from clinical_core import vascular_support as vs
    for name, value in SNAPSHOT["binding"].items():
        low, high = vs.REGION[name]["bounds"]
        assert low <= value <= high and SNAPSHOT["region"]["bounds"][name] == [low, high] and SNAPSHOT["region"]["confidences"][name] == vs.REGION[name]["confidence"], name
    assert all(spec["confidence"] < 0.80 for spec in vs.REGION.values()), "no narrow region is adopted: the point is a development snapshot, not a calibration"
    assert vs.witness("LOW") == LOW and vs.witness("HIGH") == HIGH and vs.witness("CENTER_REFERENCE") == CENTER
    assert SNAPSHOT["witnesses_test_only"] == {"LOW": "TEST_WITNESS_ONLY", "HIGH": "TEST_WITNESS_ONLY", "decision": "FD-TONE-RATIFY-04", "reopening": "only if future evidence requires another calibration cycle"}
    assert PROBES["chosen_witness"] is None and FRF["chosen_witness"] is None, "the certified records that preceded the review still say that no witness was chosen: they are history and are not edited"


def test_t13_the_snapshot_is_bound_to_what_was_reviewed_and_to_the_human_record():
    reviewed = SNAPSHOT["reviewed_with"]
    assert reviewed["review_set_id"] == ftm.SET_ID and reviewed["review_set_digest"] == ftm.PINNED_SET_DIGEST and reviewed["witness_the_reviewer_saw"] == "CENTER_REFERENCE"
    assert reviewed["human_record"] == {"file": f"docs/revision/{FILES['human']}", "record_digest": HUMAN["record_digest"], "verification": "HUMAN_FACULTY_REVIEW_REPORTED_NOT_STORE_VERIFIED"}
    assert reviewed["reviewed_trajectory_digests"] == {entry["scenario_id"]: entry["reviewed_trajectory_digest"] for entry in HUMAN["scenarios"]}
    assert RATIFICATION["snapshot"]["record_digest"] == SNAPSHOT["record_digest"] and RATIFICATION["snapshot"]["file_sha256"] == _sha(REV / FILES["snapshot"])
    assert RATIFICATION["human_record"]["record_digest"] == HUMAN["record_digest"] and RATIFICATION["human_record"]["overall_counts"] == HUMAN["overall_counts"]


def test_t14_the_ratification_carries_the_nine_faculty_decisions_and_the_scope_of_the_ratification():
    assert RATIFICATION["faculty_decisions"] == build.DECISIONS and sorted(RATIFICATION["faculty_decisions"]) == [f"FD-TONE-RATIFY-0{index}" for index in range(1, 10)]
    assert RATIFICATION["status"] == "RATIFIED_FOR_DEVELOPMENT_EXPERIMENTS" and RATIFICATION["development_status"]["common_tone"] == "COMMON_TONE_DEVELOPMENT_RATIFIED"
    assert "appropriately selected supportive vasopressor contexts" in RATIFICATION["ratified_for"] and "NOT production" in RATIFICATION["development_status"]["meaning"]
    for text in ("a clinical calibration", "production validation", "resident approval", "a clinical-validation claim", "an approval of norepinephrine in any patient", "an educational promotion of vasopressor behaviour"):
        assert text in RATIFICATION["is_not"], text
    assert "No sensitivity review is required" in RATIFICATION["faculty_decisions"]["FD-TONE-RATIFY-09"]


# ------------------------------------------------------------------------------------------------------------------------------------ P3-419 / P3-420 / P3-421 · the limitations and the next priority
def test_t15_the_limitations_are_persisted_with_the_status_the_faculty_gave():
    limits = RATIFICATION["limitations"]
    assert {key: value["status"] for key, value in limits.items()} == {"COMMON_TONE_PUMP_DEPENDENCE_NOT_YET_VALIDATED": "MONITORED_DEVELOPMENT_LIMITATION",
                                                                     "CONSCIOUSNESS_UNDER_TONE_UNRESOLVED": "OPEN_DEVELOPMENT_LIMITATION", "TITRATION_AND_STOP_NOT_SUPPORTED": "NEXT_HIGH_PRIORITY_MANAGEMENT_GAP"}
    pump = limits["COMMON_TONE_PUMP_DEPENDENCE_NOT_YET_VALIDATED"]
    assert "educational promotion of vasopressor behaviour in pump-limited families" in pump["blocks"] and "continued development of the common tone mechanism" in pump["does_not_block"]
    assert "a pump-specific afterload sensitivity" in pump["not_to_do_now"] and "a global recalibration of the tone pathway" in pump["not_to_do_now"]
    consciousness = limits["CONSCIOUSNESS_UNDER_TONE_UNRESOLVED"]
    assert any("pressure-derived consciousness interpretation" in text for text in consciousness["blocks"]) and any("consciousness authority" in text for text in consciousness["blocks"])
    assert limits["TITRATION_AND_STOP_NOT_SUPPORTED"]["decision"] == "FD-TONE-RATIFY-08"
    assert SNAPSHOT["limitations"] == sorted(limits)


def test_t16_titration_and_stop_are_the_next_priority_and_are_not_implemented_or_authorized():
    nxt = RATIFICATION["next_management_priority"]
    assert nxt["id"] == "NOREPINEPHRINE_TITRATION_AND_STOP_SEMANTICS" and nxt["implemented"] is False and nxt["authorized_to_implement"] is False
    assert nxt["desired_future_behaviour"] == ["start", "increase", "decrease", "stop"] and "the SAME common writer" in nxt["through"]
    assert nxt["without"] == ["a drug -> mmHg shortcut", "multiple competing tone writers", "case-specific branches"]
    import runtime_tone_support as rts
    # P3-431 (declared adaptation): the RECORD still says what was true when it was written -- titration and stop were the next priority, neither implemented nor authorized -- and it is
    # not edited. The faculty then authorized them (FD-TITRATE-01) and the mapping reads them; the two assertions on the mapping's old gap texts were replaced by what still binds it.
    assert RATIFICATION["limitations"]["TITRATION_AND_STOP_NOT_SUPPORTED"]["status"] == "NEXT_HIGH_PRIORITY_MANAGEMENT_GAP"
    assert rts.STATUS == "DEVELOPMENT_SHADOW_ONLY" and rts.MAPPED_OPERATION == "start" and rts.MAPPED_UNITS == "mcg/min"
    assert any("automatic titration" in item for item in rts.NOT_GRANTED) and "a weight-based dose" in rts.NOT_GRANTED and "runtime authority" in rts.NOT_GRANTED


def test_t17_the_scenario_limitations_do_not_widen_the_blocked_set_and_nothing_is_made_unavailable():
    assert RATIFICATION["scenario_limitation_labels"].keys() == {"COMMON_TONE_PRESSURE_BENEFIT_MUST_NOT_IMPLY_VOLUME_CORRECTION", "COMMON_TONE_PRESSURE_BENEFIT_MUST_NOT_IMPLY_OBSTRUCTION_CORRECTION"}
    assert RATIFICATION["negative_control"]["why_not_unavailable"].startswith("the action is inappropriate in this context, not in general")
    assert RATIFICATION["negative_control"]["case_id"] == "pulmonary_edema_58m"
    import runtime_tone_support as rts
    assert "norepinephrine made unavailable" not in " ".join(rts.NOT_GRANTED) and rts.ORDER_KIND == "norepinephrine", "the order is still mapped for every case the mapping maps: it is not made unavailable"


# ------------------------------------------------------------------------------------------------------------------------------------ P3-422 · nothing executable changed, no authority expanded
def test_t18_the_ratification_changes_nothing_executable_and_expands_no_authority():
    import runtime_tone_support as rts
    from clinical_core import amendment_3 as a3
    assert RATIFICATION["executable_change"] is False and RATIFICATION["physiology_change"] is False and RATIFICATION["tone_recalibrated"] is False and RATIFICATION["pump_coupling_modified"] is False
    authority = RATIFICATION["authority"]
    assert authority["common_core_runtime_authority"] is False and authority["expanded"] is False and authority["norepinephrine_authority_granted"] is False and authority["live_configuration_bound_to_the_snapshot"] is False
    assert a3.amended_core_digest_now() == CORE_DIGEST and rts.STATUS == "DEVELOPMENT_SHADOW_ONLY" and "titration" in authority["not_granted"]
    assert SNAPSHOT["live_configuration"]["bound"] is False and SNAPSHOT["live_configuration"]["executable_change"] is False
    import runtime_shadow
    assert runtime_shadow.COMMON_CORE_RUNTIME_AUTHORITY is False


def test_t19_nothing_executable_reads_the_snapshot_the_human_record_or_the_ratification():
    needles = ("COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1", "PHASE3_HUMAN_COMMON_TONE_MULTIFAMILY_REVIEW", "COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1_RATIFICATION", "COMMON_TONE_RATIFICATION_CHECKPOINT")
    offenders = [path.name for path in ROOT_MODULES for text in [path.read_text(encoding="utf-8")] if any(needle in text for needle in needles)]
    assert offenders == [], f"a record nothing executable reads is read by: {offenders}"
    core = [path.name for path in (ROOT / "clinical_core").glob("*.py") if any(needle in path.read_text(encoding="utf-8") for needle in needles)]
    assert core == []


def test_t20_the_certified_tone_sources_and_the_review_set_are_untouched():
    index = hr.load_index(ROOT)["records"]
    for name in ("PHASE3_COMMON_TONE_PROBES.json", "PHASE3_FRF_TONE_V1_CANDIDATE.json", "PHASE3_COMMON_TONE_V1_MULTIFAMILY_REVIEW_SET.json", "PHASE3_COMMON_TONE_V1_MULTIFAMILY_REVIEW_CHECKPOINT.json",
                 "PHASE3_FIRST_HUMAN_FACULTY_REVIEW.json", "PHASE3_HUMAN_FACULTY_REREVIEW.json", "GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1.json", "GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1_RATIFICATION.json"):
        assert hr.file_sha256(REV / name) == index[name]["file_sha256"], name
    assert ftm.load_set()["ok"] and ftm.load_set()["digest"] == "22ed59069e441aca96939ccf359ceec00a8bd55ddc0b182ff7bbcfcdd6e91487"


def test_t21_the_records_regenerate_to_the_stored_content_under_the_same_generating_code():
    current = build.generating_code()
    for key, name in FILES.items():
        record = {"human": HUMAN, "snapshot": SNAPSHOT, "ratification": RATIFICATION}[key]
        if not hr.same_generating_code(record, current):
            pytest.skip("the generating code moved after the record was written: the record is history, its bytes are pinned by the index, and it is not regenerated")
    made = build.reproduce()
    for key, record in {"human": HUMAN, "snapshot": SNAPSHOT, "ratification": RATIFICATION}.items():
        stored = {name: value for name, value in record.items() if name not in ("provenance", "record_digest")}
        assert stored == made[key], key


def test_t22_no_model_name_no_reviewer_name_no_secret_in_the_records():
    text = " ".join((REV / name).read_text(encoding="utf-8") for name in FILES.values()) + (ROOT / "test_tone_ratification_analysis.py").read_text(encoding="utf-8")
    for forbidden in ("claude-", "sonnet", "opus", "haiku", "fable", "anthropic", "password", "api_key", "secret_key", "BEGIN PRIVATE"):
        assert forbidden not in text.lower().replace("anthropic_model", ""), forbidden
    assert not re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text), "no e-mail address"
