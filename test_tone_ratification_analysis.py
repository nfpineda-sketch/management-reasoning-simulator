"""P3-415 to P3-421: the BUILDER of the common-tone ratification records (a tool, never imported by a page; it holds no test).

WHAT IT DOES. It turns the human faculty review of ``COMMON_TONE_V1_MULTIFAMILY_FACULTY_REVIEW`` into durable, sealed, indexed records and changes NOTHING executable:

* ``PHASE3_HUMAN_COMMON_TONE_MULTIFAMILY_REVIEW.json`` -- the HUMAN evidence, exactly as the faculty reported it (provenance ``HUMAN_FACULTY_REVIEW_REPORTED_NOT_STORE_VERIFIED``: the persisted store is not in this
  container). Nothing is inferred, no comment is invented, and the earlier reviews' records are named by digest and file hash so that their preservation can be tested;
* ``COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1.json`` -- the exact CENTER_REFERENCE binding, COPIED from the certified core and the certified records and never recomputed, optimized or replaced by another witness's value; LOW and
  HIGH are recorded as test witnesses only. It is a RECORD: nothing executable reads it;
* ``COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1_RATIFICATION.json`` -- the faculty decisions FD-TONE-RATIFY-01 to FD-TONE-RATIFY-09, the scenario-level classification (mechanism failure vs inappropriate intervention context vs
  educational limitation), the audit of the pulmonary-edema REJECT, the monitored limitations and the next management priority (titration and stop, NOT implemented).

The classification is NOT derived by this tool from the numbers: every entry quotes the recorded human judgment it rests on, and a test refuses a quotation that is not in the human record. The only model analysis included
(the relative response of the same mechanism in every family, read from the certified probe record) is labelled as such: it explains, it does not judge.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import faculty_tone_review as ftm
import faculty_trajectory_review as ftr
import historical_records as hr
import test_tone_pathway_analysis as ta
import test_tone_review_analysis as tr

ROOT = Path(__file__).resolve().parent
REV = ROOT / "docs" / "revision"
GENERATED_ON = "2026-11-18"
HUMAN_PATH = REV / "PHASE3_HUMAN_COMMON_TONE_MULTIFAMILY_REVIEW.json"
SNAPSHOT_PATH = REV / "COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1.json"
RATIFICATION_PATH = REV / "COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1_RATIFICATION.json"
CHECKPOINT_PATH = REV / "PHASE3_COMMON_TONE_RATIFICATION_CHECKPOINT.json"
HUMAN_ID = "HUMAN_COMMON_TONE_MULTIFAMILY_REVIEW_V1"
SNAPSHOT_ID = "COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1"
RATIFICATION_ID = "COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1_RATIFICATION"
CHECKPOINT_ID = "COMMON_TONE_RATIFICATION_CHECKPOINT_V1"
WITNESS = "CENTER_REFERENCE"
REPORTED_IN = "the assignment of 2026-11-18 that opened P3-415 ('PHASE 3 — RATIFY COMMON VASCULAR TONE DEVELOPMENT SNAPSHOT AFTER MULTIFAMILY HUMAN FACULTY REVIEW')"
PROVENANCE_CLASS = "HUMAN_FACULTY_REVIEW_REPORTED_NOT_STORE_VERIFIED"
QUESTIONS = ("Q1", "Q2", "Q3", "Q4", "Q5")

#: What the faculty reported, typed once from the assignment, in the order of the review. The interpretation is the faculty's own text: no word was changed and none was added.
REPORTED = {
    "FR-F": {"reported_name": "GI HEMORRHAGE", "overall": "ACCEPT_WITH_LIMITATION", "first_pass": ("Expected", "Plausible", "Plausible", "Coherent", "Maybe"),
             "interpretation": ("Norepinephrine produces an appropriate early pressure response.\n\nThe benefit is incomplete and attenuates while hemorrhage remains untreated.\n\n"
                                "The pressure improvement must not be interpreted as correction of underlying volume loss.")},
    "SYNTH": {"reported_name": "LOW-TONE SYNTHETIC PROBE", "overall": "ACCEPT", "first_pass": ("Expected", "Plausible", "Plausible", "Coherent", "No"),
              "interpretation": ("The response is a clean development-positive control.\n\nVascular-tone support restores part of the pressure lost from reduced tone without unrealistically returning "
                                 "the system to its original baseline.")},
    "ACS": {"reported_name": "ACS / PUMP-LIMITED", "overall": "ACCEPT_WITH_LIMITATION", "first_pass": ("Expected", "Plausible", "Plausible", "Uncertain", "Yes"),
            "interpretation": ("The pressure response is directionally and temporally defensible.\n\nHowever:\n\nthe patient is not hypotensive,\nthe state is pump-limited,\nand norepinephrine does not correct pump failure.\n\n"
                               "This remains a pump-dependence limitation.\n\nDo NOT globally recalibrate the tone pathway from this scenario.")},
    "PULM-EDEMA": {"reported_name": "HYPERTENSIVE PULMONARY EDEMA", "overall": "REJECT", "first_pass": ("Expected", "Plausible", "Too large", "Incoherent", "Yes"),
                   "interpretation": ("The pressure rise itself is physiologically understandable.\n\nHowever:\n\nthe patient is already profoundly hypertensive with acute cardiogenic pulmonary edema.\n\n"
                                      "Norepinephrine is clinically inappropriate and drives pressure further into an extreme range.\n\nIMPORTANT:\n\nThis REJECT is primarily a judgment of the MANAGEMENT CONTEXT / "
                                      "EDUCATIONAL USE of this intervention.\n\nIt is NOT, by itself, evidence that the common vascular-tone mechanism requires global recalibration.\n\n"
                                      "Do NOT retune T merely to make norepinephrine look acceptable in a patient who should not receive it.")},
    "PE": {"reported_name": "HIGH-RISK PULMONARY EMBOLISM", "overall": "ACCEPT_WITH_LIMITATION", "first_pass": ("Expected", "Plausible", "Plausible", "Coherent", "Maybe"),
           "interpretation": ("The pressure response is clinically defensible as temporary hemodynamic support in obstructive shock.\n\nIt must not imply correction of the pulmonary vascular obstruction.")},
}
REPORTED_COUNTS = {"ACCEPT": 1, "ACCEPT_WITH_LIMITATION": 3, "RECALIBRATE": 0, "REJECT": 1}

#: The faculty's decisions, as given (FD-TONE-RATIFY-01 to FD-TONE-RATIFY-09).
DECISIONS = {
    "FD-TONE-RATIFY-01": ("Human review totals: ACCEPT 1, ACCEPT_WITH_LIMITATION 3, RECALIBRATE 0, REJECT 1. The single REJECT is a clinically inappropriate vasopressor intervention in an already severely hypertensive "
                          "pulmonary-edema patient: the review is NOT to be interpreted as failure of the common tone mechanism."),
    "FD-TONE-RATIFY-02": "The common vascular-tone pathway is ACCEPTABLE FOR DEVELOPMENT for appropriately selected supportive vasopressor contexts.",
    "FD-TONE-RATIFY-03": ("CENTER_REFERENCE is promoted to COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1. Reason: accepted in the low-tone positive control; acceptable with limitations in hemorrhagic and obstructive shock; no scenario requested "
                          "global tone recalibration; the ACS limitation is pump-context dependent; the pulmonary-edema rejection reflects an inappropriate intervention context. A DEVELOPMENT snapshot, NOT a clinical calibration, "
                          "production validation or resident approval."),
    "FD-TONE-RATIFY-04": "LOW and HIGH remain TEST_WITNESS_ONLY. No further calibration cycle unless future evidence requires it.",
    "FD-TONE-RATIFY-05": ("COMMON_TONE_PUMP_DEPENDENCE_NOT_YET_VALIDATED persists as a MONITORED DEVELOPMENT LIMITATION: it blocks educational promotion of vasopressor behaviour in pump-limited families; it does NOT block "
                          "continued development of the common tone mechanism."),
    "FD-TONE-RATIFY-06": ("The hypertensive pulmonary-edema scenario is classified INAPPROPRIATE_INTERVENTION_CONTEXT and, optionally, NEGATIVE_CONTROL_CANDIDATE for future management-reasoning work. Its physiology is not altered so "
                          "that the intervention appears beneficial."),
    "FD-TONE-RATIFY-07": "CONSCIOUSNESS_UNDER_TONE_UNRESOLVED persists: pressure-derived consciousness interpretation under active tone support stays blocked.",
    "FD-TONE-RATIFY-08": ("TITRATION_AND_STOP_NOT_SUPPORTED persists as the NEXT HIGH-PRIORITY MANAGEMENT GAP; the next implementation target after ratification is norepinephrine rate change / titration / stop semantics. "
                          "NOT implemented in this ratification package unless explicitly authorized later."),
    "FD-TONE-RATIFY-09": "No sensitivity review is required for the current development decision; the LOW/HIGH review remains optional future work and ratification is not delayed for it."}
VOCABULARY = ("MECHANISM_FAILURE", "INAPPROPRIATE_INTERVENTION_CONTEXT", "EDUCATIONAL_LIMITATION")

#: The classification (P3-416). ``human_basis`` quotes the recorded human text it rests on; a test refuses a quotation that is not in the human record. Nothing here is derived from numbers.
CLASSIFICATION = {
    "FR-F": {"classification": "EDUCATIONAL_LIMITATION", "limitation_ids": ["COMMON_TONE_PRESSURE_BENEFIT_MUST_NOT_IMPLY_VOLUME_CORRECTION"],
             "human_basis": ["Norepinephrine produces an appropriate early pressure response.", "must not be interpreted as correction of underlying volume loss"],
             "meaning": "an educational caution about how the pressure improvement is read, not a defect of the mechanism"},
    "SYNTH": {"classification": "DEVELOPMENT_POSITIVE_CONTROL", "limitation_ids": [], "human_basis": ["The response is a clean development-positive control."],
              "meaning": "the mechanism does what it should in the one state built to test it, and does not return the system to its original baseline"},
    "ACS": {"classification": "EDUCATIONAL_LIMITATION", "limitation_ids": ["COMMON_TONE_PUMP_DEPENDENCE_NOT_YET_VALIDATED"],
            "human_basis": ["The pressure response is directionally and temporally defensible.", "This remains a pump-dependence limitation.", "Do NOT globally recalibrate the tone pathway from this scenario."],
            "meaning": "a pump-context limitation of what the pressure response means in a pump-limited patient who is not hypotensive; not a tone-pathway recalibration"},
    "PULM-EDEMA": {"classification": "INAPPROPRIATE_INTERVENTION_CONTEXT", "limitation_ids": [], "negative_control_candidate": True,
                   "human_basis": ["The pressure rise itself is physiologically understandable.", "Norepinephrine is clinically inappropriate",
                                   "This REJECT is primarily a judgment of the MANAGEMENT CONTEXT / EDUCATIONAL USE of this intervention.",
                                   "It is NOT, by itself, evidence that the common vascular-tone mechanism requires global recalibration.",
                                   "Do NOT retune T merely to make norepinephrine look acceptable in a patient who should not receive it."],
                   "meaning": "the faculty rejected giving this vasopressor to this patient, not the way the common mechanism responds to it"},
    "PE": {"classification": "EDUCATIONAL_LIMITATION", "limitation_ids": ["COMMON_TONE_PRESSURE_BENEFIT_MUST_NOT_IMPLY_OBSTRUCTION_CORRECTION"],
           "human_basis": ["The pressure response is clinically defensible as temporary hemodynamic support in obstructive shock.", "It must not imply correction of the pulmonary vascular obstruction."],
           "meaning": "an educational caution: temporary support is not correction of the obstruction"}}
LIMITATIONS = {
    "COMMON_TONE_PUMP_DEPENDENCE_NOT_YET_VALIDATED": {
        "status": "MONITORED_DEVELOPMENT_LIMITATION", "decision": "FD-TONE-RATIFY-05",
        "blocks": ["educational promotion of vasopressor behaviour in pump-limited families"], "does_not_block": ["continued development of the common tone mechanism", "this ratification"],
        "what_it_is": ("the output cost of tone is one sensitivity for every pump and volume (a certified limitation of the pathway); how the pressure response should depend on the state of the pump is not validated, "
                       "and the ACS review (not hypotensive, pump-limited) is where it showed"),
        "reopen_only_if": ["a future faculty review asks for a pump-dependent afterload sensitivity", "another pump-limited family shows the same deficit", "educational use of a vasopressor in a pump-limited family is proposed"],
        "not_to_do_now": ["a pump-specific afterload sensitivity", "a global recalibration of the tone pathway"]},
    "CONSCIOUSNESS_UNDER_TONE_UNRESOLVED": {
        "status": "OPEN_DEVELOPMENT_LIMITATION", "decision": "FD-TONE-RATIFY-07",
        "blocks": ["pressure-derived consciousness interpretation under active tone support", "any consciousness authority or resident-visible interpretation under active tone support"],
        "does_not_block": ["continued development of the common tone mechanism"],
        "what_it_is": ("the consciousness readings are taken from the pressure, so with support they read BETTER while output and delivery are lower (a certified limitation of the pathway); the development mapping refuses "
                       "the support on an Amendment-2 consciousness witness")},
    "TITRATION_AND_STOP_NOT_SUPPORTED": {
        "status": "NEXT_HIGH_PRIORITY_MANAGEMENT_GAP", "decision": "FD-TONE-RATIFY-08",
        "blocks": ["any claim that a norepinephrine rate change or a stop is represented"], "does_not_block": ["this ratification"],
        "what_it_is": "only a single start of norepinephrine at a fixed rate in mcg/min is mapped; an adjustment, a stop, a weight-based dose and any later start are declared gaps (runtime_tone_support)"}}
NEXT_PRIORITY = {
    "id": "NOREPINEPHRINE_TITRATION_AND_STOP_SEMANTICS", "decision": "FD-TONE-RATIFY-08", "implemented": False, "authorized_to_implement": False,
    "desired_future_behaviour": ["start", "increase", "decrease", "stop"],
    "through": "the SAME common writer of the common vasoconstrictor support",
    "without": ["a drug -> mmHg shortcut", "multiple competing tone writers", "case-specific branches"],
    "first_step_when_authorized": ("an audit of what the engine mirrors for a rate change and a stop, of how the writer represents a rate that changes over time, and of what each ordering means for the support the offset "
                                   "constant already decays")}
NEGATIVE_CONTROL = {"id": "HYPERTENSIVE_PULMONARY_EDEMA_NOREPI", "classification": "INAPPROPRIATE_INTERVENTION_CONTEXT", "negative_control_candidate": True, "case_id": "pulmonary_edema_58m",
                    "future_use": "a negative-control management scenario (a vasopressor ordered for a profoundly hypertensive patient with acute cardiogenic pulmonary edema)",
                    "physiology_altered": False, "norepinephrine_made_unavailable": False,
                    "why_not_unavailable": "the action is inappropriate in this context, not in general: the common mechanism must keep representing it so that the inappropriate order has a consequence to be judged"}
NOT_GRANTED = ["runtime authority", "a registered adapter", "resident visibility", "scoring", "the first pilot", "a clinical dose-response", "an mmHg target", "titration", "a weight-based dose", "any other vasopressor",
               "consciousness authority", "terminal authority", "clinical validation"]


# -- the generating code and the sources --------------------------------------------------------------------------------------------------------------------------------
def generating_code() -> dict:
    from clinical_core import amendment_3 as a3
    return {"clinical_core": a3.amended_core_digest_now(), "test_tone_ratification_analysis.py": ta._sha(Path(__file__).resolve()), "test_tone_review_analysis.py": ta._sha(ROOT / "test_tone_review_analysis.py"),
            "test_tone_pathway_analysis.py": ta._sha(ROOT / "test_tone_pathway_analysis.py")}


def _file(path: Path) -> dict:
    record = json.loads(path.read_text(encoding="utf-8"))
    return {"file": str(path.relative_to(ROOT)), "record_digest": record.get("record_digest"), "file_sha256": ta._sha(path)}


def preserved() -> dict:
    """Every earlier faculty review and record this one rests on, by digest and file hash: preserved, not rewritten."""
    return {"first_human_review": _file(REV / "PHASE3_FIRST_HUMAN_FACULTY_REVIEW.json"), "human_rereview": _file(REV / "PHASE3_HUMAN_FACULTY_REREVIEW.json"),
            "tone_review_set": _file(ftm.SET_PATH), "tone_review_checkpoint": _file(tr.CHECKPOINT_PATH), "tone_probes": _file(ta.PROBES_PATH), "frf_candidate": _file(ta.CANDIDATE_PATH),
            "first_review_set_digest_pinned_in_code": ftr.PINNED_SET_DIGEST, "tone_review_set_digest_pinned_in_code": ftm.PINNED_SET_DIGEST}


def counts(scenarios: dict) -> dict:
    out = {choice: 0 for choice in ftr.OVERALL}
    for entry in scenarios.values():
        out[entry["overall"]] += 1
    return out


# -- the records ----------------------------------------------------------------------------------------------------------------------------------------------------------------
def build_human() -> dict:
    loaded = ftm.load_set()
    if not loaded["ok"]:
        raise ValueError(f"the reviewed set does not verify: {loaded['problems']}")
    if counts(REPORTED) != REPORTED_COUNTS:
        raise ValueError("the reported totals are not the tabulation of the reported judgments")
    scenarios = []
    for scenario_id in ftm.SCENARIOS:
        item, reported = loaded["items"][scenario_id], REPORTED[scenario_id]
        scenarios.append({"scenario_id": scenario_id, "reported_name": reported["reported_name"], "title_in_the_set": item["title"], "overall": reported["overall"],
                          "first_pass": dict(zip(QUESTIONS, reported["first_pass"])), "faculty_interpretation_as_reported": reported["interpretation"], "free_text_comments": "NONE_REPORTED",
                          "recalibration_in_isolation_requested": False, "reviewed_item_digest": ftr.item_digest(item),
                          "reviewed_trajectory_digest": hr.digest_of({"scenario_id": scenario_id, "timeline": item["timeline"], "common": item["common"]})})
    body = {"record_type": "HUMAN_FACULTY_COMMON_TONE_MULTIFAMILY_REVIEW_RECORD", "version": "P3-415", "evidence_class": "HUMAN_FACULTY_REVIEW",
            "evidence_classes": {"HUMAN_FACULTY_REVIEW": "what the faculty reviewer judged in the blind multifamily review of the CENTER_REFERENCE tone trajectories, as reported; only this record and the Decision File rows "
                                                         "FD-TONE-RATIFY-01 to FD-TONE-RATIFY-09 carry it",
                                 "MODEL_ANALYSIS": "what the development assistant computed or read from the executable model and the certified records; it explains and bounds, it does not judge",
                                 "TEST_RESULT": "what an automated test asserted; it protects a record, it is not a faculty decision"},
            "what_it_is": ("The human faculty review of the five CENTER_REFERENCE tone trajectories (one norepinephrine order), recorded as HUMAN evidence as the reviewer reported it. It is not converted into an automated "
                           "truth, it is not a clinical validation, and nothing in it was written by a model. No comment, event or sensitivity answer that was not reported was added."),
            "review": {"review_set_id": ftm.SET_ID, "review_set_digest": loaded["digest"], "candidate_reviewed": WITNESS, "candidate_named_by_the_interface": False, "pressure_only_first_pass": True,
                       "scenario_order_as_reported": list(ftm.SCENARIOS), "scenarios_with_reported_judgments": len(scenarios), "completion_as_reported": "NOT_REPORTED_AS_A_STRING",
                       "optional_sensitivity_check": "NOT_REPORTED (FD-TONE-RATIFY-09: not required for this decision)",
                       "item_digests_note": "computed here from the pinned set (what the review logs carry); the faculty did not report them"},
            "scenarios": scenarios, "overall_counts": dict(REPORTED_COUNTS), "overall_counts_recomputed_from_the_scenarios": counts(REPORTED),
            "provenance_of_the_evidence": {"date_of_record": GENERATED_ON, "verification": PROVENANCE_CLASS, "reported_in": REPORTED_IN, "persisted_store_available_to_the_assistant": False,
                                          "reviewer_identity_recorded": False, "reviewer_name": None, "reviewer_role": "faculty",
                                          "transcribed_by": "the development assistant; the judgments and interpretations are typed once from the report and no word of the faculty interpretation was changed",
                                          "why": ("the persisted logs of this review (tone_review/, tone_reviews/ and tone_sensitivity/ of the reviewer's own store) are not in this container: the only review store found here holds no tone "
                                                  "review; the assignment asked to read the store if available and, if not, to use the reported results and mark the provenance, without inventing comments or events")},
            "not_verified": ["the answers Q1 to Q5 and the overall judgments against the persisted logs", "the scenario order as persisted", "the completion state as persisted",
                             "the lock and submit events and their order", "free-text comments (none were reported)", "whether the optional sensitivity check was opened"],
            "not_in_this_record": ["the reviewer's name", "any model-written judgment", "any legacy comparison", "any clinical-validation claim", "the per-event logs (they live in the reviewer's own store)"],
            "preserved_original_evidence": preserved()}
    body["provenance"] = hr.provenance(record_id=HUMAN_ID, generating_code=generating_code(), generated_on=GENERATED_ON, source_data={"reported": REPORTED, "counts": REPORTED_COUNTS, "set_digest": loaded["digest"]})
    return hr.seal(body)


def _binding() -> dict:
    from clinical_core import vascular_support as vs
    return {"half_effect_rate_mcg_min": float(vs.witness(WITNESS)["half_effect_rate_mcg_min"]), "offset_tau_min": float(vs.witness(WITNESS)["offset_tau_min"]),
            "onset_tau_min": float(vs.witness(WITNESS)["onset_tau_min"]), "tone_gain": float(vs.witness(WITNESS)["tone_gain"])}


def build_snapshot(human: dict) -> dict:
    from clinical_core import vascular_support as vs
    probes, frf = ta.load(ta.PROBES_PATH), ta.load(ta.CANDIDATE_PATH)
    binding = _binding()
    equal = {"the_core_witness": binding == {key: float(value) for key, value in vs.witness(WITNESS).items()},
             "the_certified_probe_record": binding == probes["witnesses"][WITNESS], "the_certified_frf_candidate": binding == frf["witnesses"][WITNESS]["witness"]}
    if not all(equal.values()):
        raise ValueError(f"the CENTER_REFERENCE binding is not the same in every certified source: {equal}")
    loaded = ftm.load_set()
    body = {"record_type": "COMMON_TONE_DEVELOPMENT_SNAPSHOT", "version": "P3-418", "snapshot_id": SNAPSHOT_ID, "status": "RATIFIED_FOR_DEVELOPMENT_EXPERIMENTS", "selected_witness": WITNESS,
            "binding": dict(binding), "binding_units": {"half_effect_rate_mcg_min": "mcg/min", "offset_tau_min": "min", "onset_tau_min": "min", "tone_gain": "fraction of the arrival tone"},
            "profile_field": "vasoconstrictor_support_to_tone_gain", "profile_field_takes": "tone_gain (the other three values are the constants of the norepinephrine order the common writer receives)",
            "binding_source": {"copied_not_recomputed": True, "optimized": False, "another_point_considered": False, "equal_in_every_certified_source": equal,
                               "core_function": "clinical_core.vascular_support.witness('CENTER_REFERENCE')", "core_digest": generating_code()["clinical_core"],
                               "probes_record": {**_file(ta.PROBES_PATH), "path_in_record": "witnesses.CENTER_REFERENCE"}, "frf_candidate": {**_file(ta.CANDIDATE_PATH), "path_in_record": "witnesses.CENTER_REFERENCE.witness"}},
            "bound_together": "the four values are ONE point of the development region; none may be replaced by another witness's value, and none is a separate range",
            "region": {"bounds": {name: list(spec["bounds"]) for name, spec in _region().items()}, "confidences": {name: spec["confidence"] for name, spec in _region().items()},
                       "note": "every confidence of the region is below 0.80: no narrow region is adopted and this point is not a calibration (FD-TONE-06)"},
            "reviewed_with": {"review_set_id": ftm.SET_ID, "review_set_digest": loaded["digest"], "witness_the_reviewer_saw": WITNESS, "human_record": {"file": str(HUMAN_PATH.relative_to(ROOT)), "record_digest": human["record_digest"],
                                                                                                                                          "verification": PROVENANCE_CLASS},
                              "reviewed_trajectory_digests": {entry["scenario_id"]: entry["reviewed_trajectory_digest"] for entry in human["scenarios"]},
                              "trajectories_are_the_certified_ones": "the reviewed trajectories were produced from, or proven equal to, the certified records with exactly this binding (docs/PHASE3_COMMON_TONE_FACULTY_REVIEW.md §1)"},
            "witnesses_test_only": {"LOW": "TEST_WITNESS_ONLY", "HIGH": "TEST_WITNESS_ONLY", "decision": "FD-TONE-RATIFY-04", "reopening": "only if future evidence requires another calibration cycle"},
            "live_configuration": {"bound": False, "executable_change": False,
                                   "statement": ("This is a RECORD. Nothing executable reads it: runtime_tone_support still takes a witness NAME for a development shadow copy, no registered adapter declares the reader, the live GI pressure authority "
                                                 "still stops on a norepinephrine order, and binding anything to this snapshot would be a separate EXECUTABLE step with its own authorization and recertification.")},
            "limitations": sorted(LIMITATIONS), "is_not": ["a clinical calibration", "a clinical dose-response", "an mmHg target", "production validation", "resident approval", "authority", "a clinical-validation claim"],
            "reopening_rule": "a different point replaces this snapshot only through a new faculty review and a successor record; this record is never edited"}
    body["provenance"] = hr.provenance(record_id=SNAPSHOT_ID, generating_code=generating_code(), generated_on=GENERATED_ON, source_data={"binding": binding, "human": human["record_digest"], "probes": probes["record_digest"], "frf": frf["record_digest"]})
    return hr.seal(body)


def _region() -> dict:
    from clinical_core import vascular_support as vs
    return {name: {"bounds": spec["bounds"], "confidence": spec["confidence"]} for name, spec in vs.REGION.items()}


def _relative_response() -> dict:
    """MODEL_ANALYSIS: the relative pressure response of the SAME mechanism in every registered family, read from the certified probe record (no run)."""
    probes = ta.load(ta.PROBES_PATH)
    out = {}
    for family, probe in probes["family_probes"].items():
        last = probe["witnesses"][WITNESS]["observed"][-1]
        out[family] = {"case_id": probe["case_id"], "minute": last["minute"], "pressure_ratio": last["pressure_ratio"], "map_gain_mmhg": last["map_gain_mmhg"], "map_without": last["map_without"], "map_with": last["map_with"]}
    return out


def build_ratification(human: dict, snapshot: dict) -> dict:
    scenarios = {}
    for scenario_id in ftm.SCENARIOS:
        reported = REPORTED[scenario_id]
        scenarios[scenario_id] = {"overall": reported["overall"], "first_pass": dict(zip(QUESTIONS, reported["first_pass"])), "mechanism_failure": False, "global_recalibration_requested": False,
                                  **{key: value for key, value in CLASSIFICATION[scenario_id].items()}}
    relative = _relative_response()
    edema = relative["pulmonary_edema"]
    audit = {"scenario_id": "PULM-EDEMA", "case_id": "pulmonary_edema_58m", "recorded_human_judgment": {"overall": "REJECT", "Q1": "Expected", "Q2": "Plausible", "Q3": "Too large", "Q4": "Incoherent", "Q5": "Yes"},
             "reading": {"direction_and_timing": "Q1 Expected and Q2 Plausible: the faculty found the direction and the timing of the response right",
                         "magnitude_management_and_educational_risk": ("Q3 Too large, Q4 Incoherent and Q5 Yes were given with the faculty's own explanation: the patient is already profoundly hypertensive with acute "
                                                                       "cardiogenic pulmonary edema and the intervention drives pressure further into an extreme range")},
             "does_the_recorded_judgment_support_mechanism_failure": False,
             "why_not": ("the faculty stated that the REJECT is primarily a judgment of the management context and educational use, that it is NOT by itself evidence that the common mechanism needs global recalibration, and "
                         "that T is not to be retuned to make the intervention look acceptable in a patient who should not receive it; no scenario was RECALIBRATE"),
             "classification": "INAPPROPRIATE_INTERVENTION_CONTEXT", "negative_control_candidate": True,
             "model_analysis": {"evidence_class": "MODEL_ANALYSIS", "does_not_judge": True,
                                "source": "docs/revision/PHASE3_COMMON_TONE_PROBES.json family_probes.*.witnesses.CENTER_REFERENCE.observed (the last observed minute)", "by_family": relative,
                                "reading": (f"at minute {edema['minute']} the SAME mechanism gives the same relative response in pulmonary edema, gastrointestinal bleed, asthma and opioid (pressure ratio {edema['pressure_ratio']:.6f}) and a slightly "
                                            f"higher one in ACS and pulmonary embolism; the absolute rise is largest in pulmonary edema ({edema['map_gain_mmhg']:.1f} mmHg of mean pressure) because its baseline is the highest "
                                            f"({edema['map_without']:.0f} mmHg), not because the mechanism acts differently there. Changing T to shrink that rise would change every family, to look better in a patient who should not "
                                            f"receive the drug"),
                                "consequence": "no change to T, to the pump coupling or to any parameter follows from it (FD-TONE-RATIFY-06)"}}
    body = {"record_type": "COMMON_TONE_DEVELOPMENT_RATIFICATION", "version": "P3-417", "date": GENERATED_ON, "status": "RATIFIED_FOR_DEVELOPMENT_EXPERIMENTS",
            "ratified": "COMMON VASCULAR TONE PATHWAY (PHASE2_AMENDMENT_3 vasoconstrictor support, norepinephrine start at a fixed rate as its first writer)",
            "ratified_for": "DEVELOPMENT EXPERIMENTS under appropriately selected supportive vasopressor contexts", "faculty_decisions": dict(DECISIONS),
            "human_record": {"file": str(HUMAN_PATH.relative_to(ROOT)), "record_digest": human["record_digest"], "verification": PROVENANCE_CLASS, "overall_counts": human["overall_counts"]},
            "snapshot": {"file": str(SNAPSHOT_PATH.relative_to(ROOT)), "id": SNAPSHOT_ID, "record_digest": snapshot["record_digest"], "file_sha256": None, "selected_witness": WITNESS,
                         "witnesses_test_only": ["LOW", "HIGH"]},
            "classification_vocabulary": list(VOCABULARY), "classification_rule": ("a scenario is a MECHANISM_FAILURE only if the recorded human judgment says so; none does. Each entry quotes the recorded human text it "
                                                                                    "rests on (human_basis) and the quotation is checked against the human record"),
            "scenario_classification": scenarios, "mechanism_failures": [], "pulmonary_edema_audit": audit, "negative_control": dict(NEGATIVE_CONTROL),
            "limitations": {key: dict(value) for key, value in LIMITATIONS.items()}, "next_management_priority": dict(NEXT_PRIORITY),
            "scenario_limitation_labels": {"COMMON_TONE_PRESSURE_BENEFIT_MUST_NOT_IMPLY_VOLUME_CORRECTION": "FR-F: the pressure benefit attenuates while the hemorrhage is untreated and is not correction of the volume loss",
                                          "COMMON_TONE_PRESSURE_BENEFIT_MUST_NOT_IMPLY_OBSTRUCTION_CORRECTION": "PE: temporary hemodynamic support in obstructive shock is not correction of the obstruction"},
            "development_status": {"common_tone": "COMMON_TONE_DEVELOPMENT_RATIFIED", "meaning": "development only; NOT production, NOT clinical validation, NOT resident deployment"},
            "authority": {"common_core_runtime_authority": False, "expanded": False, "norepinephrine_authority_granted": False, "live_configuration_bound_to_the_snapshot": False, "not_granted": list(NOT_GRANTED)},
            "executable_change": False, "physiology_change": False, "tone_recalibrated": False, "pump_coupling_modified": False,
            "is_not": ["a clinical calibration", "production validation", "resident approval", "a clinical-validation claim", "an approval of norepinephrine in any patient", "an educational promotion of vasopressor behaviour"],
            "preserved_original_evidence": preserved()}
    body["provenance"] = hr.provenance(record_id=RATIFICATION_ID, generating_code=generating_code(), generated_on=GENERATED_ON,
                                       source_data={"human": human["record_digest"], "snapshot": snapshot["record_digest"], "decisions": DECISIONS, "classification": CLASSIFICATION, "limitations": LIMITATIONS, "next": NEXT_PRIORITY})
    return hr.seal(body)


def build() -> dict:
    human = build_human()
    snapshot = build_snapshot(human)
    return {"human": human, "snapshot": snapshot, "ratification": build_ratification(human, snapshot)}


def write_all() -> dict:
    """Write the three records, then pin the snapshot's file hash into the ratification (the ratification is sealed after it). ``historical_records.write`` refuses to replace a record with other content."""
    made = build()
    out = {str(HUMAN_PATH.relative_to(ROOT)): hr.write(HUMAN_PATH, made["human"])}
    out[str(SNAPSHOT_PATH.relative_to(ROOT))] = hr.write(SNAPSHOT_PATH, made["snapshot"])
    ratification = json.loads(json.dumps(made["ratification"]))
    ratification.pop("record_digest")
    ratification["snapshot"]["file_sha256"] = ta._sha(SNAPSHOT_PATH)
    out[str(RATIFICATION_PATH.relative_to(ROOT))] = hr.write(RATIFICATION_PATH, hr.seal(ratification))
    return out


def reproduce() -> dict:
    """The CONTENT of the three records, regenerated, without provenance or seal (and with the snapshot's file hash taken from disk): what a test compares with the stored records."""
    made = build()
    out = {}
    for key, record in made.items():
        out[key] = {name: value for name, value in record.items() if name not in ("provenance", "record_digest")}
    out["ratification"]["snapshot"]["file_sha256"] = ta._sha(SNAPSHOT_PATH) if SNAPSHOT_PATH.exists() else None
    return out


def build_checkpoint(certification: dict, *, sequence: list, facts: dict | None = None) -> dict:
    """The checkpoint record, written ONCE after the focused validation. Verdict A: every condition of the ratification holds and nothing executable changed."""
    human = json.loads(HUMAN_PATH.read_text(encoding="utf-8"))
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    ratification = json.loads(RATIFICATION_PATH.read_text(encoding="utf-8"))
    verdicts = {"A": "COMMON_TONE_DEVELOPMENT_SNAPSHOT_RATIFIED", "B": "HUMAN_REVIEW_RECORD_MISMATCH", "C": "PULMONARY_EDEMA_REJECT_IMPLIES_MECHANISM_FAILURE", "D": "SNAPSHOT_BINDING_MISMATCH",
                "E": "RATIFICATION_REQUIRES_PHYSIOLOGY_CHANGE"}
    body = {"record_type": "COMMON_TONE_RATIFICATION_CHECKPOINT", "version": CHECKPOINT_ID, "decision_reference": "FD-TONE-RATIFY-01 to FD-TONE-RATIFY-09", "evidence_class": "MODEL_ANALYSIS",
            "statement": ("The common vascular-tone pathway is ratified for development experiments under appropriately selected supportive vasopressor contexts. CENTER_REFERENCE, the exact binding the faculty reviewed, is "
                          "recorded as COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1 (copied, not recomputed); LOW and HIGH remain test witnesses. The hypertensive pulmonary-edema REJECT is an inappropriate intervention context and a "
                          "negative-control candidate, not a mechanism failure. The pump-dependence and consciousness limitations stay open and titration/stop is the next management priority, not implemented. Nothing executable changed."),
            "verdict": "A", "verdict_name": verdicts["A"], "verdicts": verdicts,
            "why_not_the_others": {"B": "the reported totals are the tabulation of the reported judgments, the answers are valid choices of the real questions, and the record is bound to the pinned review set; the persisted store is not here, so the record is marked REPORTED_NOT_STORE_VERIFIED rather than verified",
                                   "C": "the recorded human judgment states that the REJECT is a management-context judgment and not evidence for recalibration; no scenario was RECALIBRATE",
                                   "D": "the binding is equal in the core, in the certified probe record and in the certified FR-F candidate, and the reviewed trajectories are bound by digest",
                                   "E": "no step of the ratification touches the physiology, the parameters, the pump coupling or any executable file"},
            "facts": {"human_record_digest": human["record_digest"], "snapshot_record_digest": snapshot["record_digest"], "ratification_record_digest": ratification["record_digest"], "snapshot_id": SNAPSHOT_ID,
                      "overall_counts": human["overall_counts"], "binding": snapshot["binding"], "review_set_digest": ftm.PINNED_SET_DIGEST,
                      "witnesses": {"CENTER_REFERENCE": SNAPSHOT_ID, "LOW": "TEST_WITNESS_ONLY", "HIGH": "TEST_WITNESS_ONLY"}, "mechanism_failures": [],
                      "classification": {key: value["classification"] for key, value in ratification["scenario_classification"].items()},
                      "limitations": {key: value["status"] for key, value in ratification["limitations"].items()}, "next_management_priority": NEXT_PRIORITY["id"], **(facts or {})},
            "confirmations": {"no_tone_recalibration": True, "no_pump_coupling_modification": True, "no_authority_expansion": True, "no_gi_recalibration": True, "no_source_control_change": True,
                              "no_consciousness_authority": True, "no_terminal_authority": True, "no_resident_deployment": True, "no_clinical_validation_claim": True, "snapshot_is_a_record_nothing_executable_reads": True,
                              "titration_and_stop_not_implemented": True, "low_and_high_not_promoted": True, "center_reference_not_altered": True, "common_core_runtime_authority": False,
                              "persisted_store_verified": False},
            "limitations": ["the human record is reported, not verified against the persisted store", "one reviewer, five scenarios, one order (a start at a fixed rate), pressure only (no heart rate, no capillary refill)",
                            "no optional sensitivity answers were reported", "the snapshot is a development record: it is not a clinical calibration and nothing executable is bound to it",
                            "the common mechanism is proportional by construction: the absolute rise grows with the baseline pressure (documented, not changed)"],
            "certification": certification, "sequence": sequence,
            "next_human_action": ("A faculty member authorizes (or not) the next management implementation, NOREPINEPHRINE_TITRATION_AND_STOP_SEMANTICS, whose first step is an audit of what the engine mirrors for a rate change "
                                  "and a stop and of how the common writer would represent a rate that changes over time. Nothing else is to be done until then."),
            "open_faculty_decisions": ["whether and when to authorize titration/stop semantics (FD-TONE-RATIFY-08)", "whether the pump-dependence limitation needs work before any educational use of a vasopressor in a pump-limited family",
                                       "whether the hypertensive pulmonary-edema scenario becomes a negative-control management scenario", "whether the persisted human review store should be supplied so that the record can be verified",
                                       "whether the optional LOW/HIGH sensitivity review is ever wanted (FD-TONE-RATIFY-09)"]}
    parts = {"clinical_core": generating_code()["clinical_core"], "human_record_digest": human["record_digest"], "snapshot_record_digest": snapshot["record_digest"], "ratification_record_digest": ratification["record_digest"],
             "test_tone_ratification_analysis.py": ta._sha(Path(__file__).resolve())}
    body["provenance"] = hr.provenance(record_id=CHECKPOINT_ID, generating_code=parts, generated_on=GENERATED_ON, grant_id="GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V3",
                                       source_data={"verdict": "A", "certification": certification, "sequence": sequence})
    return hr.seal(body)


def write_checkpoint(certification: dict, *, sequence: list, facts: dict | None = None) -> dict:
    return {str(CHECKPOINT_PATH.relative_to(ROOT)): hr.write(CHECKPOINT_PATH, build_checkpoint(certification, sequence=sequence, facts=facts))}


if __name__ == "__main__":
    print(json.dumps(write_all(), indent=2))
