"""P3-402 to P3-405 and P3-413 (records and sources): the multifamily tone review set is a VERSIONED, indexed, sealed historical record, and every trajectory in it IS what the already-certified records and the
certified harness produce -- nothing recomputed with another parameter, nothing tuned, nothing substituted.

What it proves:

* the set record is sealed, carries provenance, is indexed (class VERSIONED, bytes pinned) and its digest is the one the loader pins in code;
* its content, REGENERATED with the certified calls, equals the stored content (so the stored trajectories are not hand-made and not stale), whatever code generated its provenance;
* each scenario's trajectory is tied to the stored certified source record DIRECTLY (FR-F: the stored per-minute CENTER_REFERENCE rows; the families and the synthetic probe: the stored observed values) without the builder;
* the sources are untouched (their pinned bytes are the index's), the common core is the certified Amendment-3 one, and no authority, grant or parameter changed;
* the audit names what was included, what was excluded (opioid, asthma) and why, and what is not stored with the items.
"""
import json
from pathlib import Path

import pytest

import faculty_tone_review as ftm
import historical_records as hr
import test_tone_pathway_analysis as ta
import test_tone_review_analysis as build

ROOT = Path(__file__).resolve().parent
RECORD = json.loads(ftm.SET_PATH.read_text(encoding="utf-8"))
PROBES = ta.load(ta.PROBES_PATH)
FRF = ta.load(ta.CANDIDATE_PATH)
ITEMS = {item["scenario_id"]: item for item in RECORD["items"]}
SENSITIVITY = {entry["scenario_id"]: entry for entry in RECORD["sensitivity"]["scenarios"]}
CORE_DIGEST = "867bac09e09bb5c04629e73fbbdec0f7e1f100da17ef8966f580ba91067a7c9c"
FAMILY_CASE = {"ACS": "acs", "PULM-EDEMA": "pulmonary_edema", "PE": "pulmonary_embolism"}
ORDER_MINUTE, HORIZON = 5, 30


def _mmhg(points: dict, minute: int) -> int:
    return points[minute]["map"]


# -- the record ---------------------------------------------------------------------------------------------------------------------------------------------------------------------
def test_c1_the_set_is_a_sealed_versioned_indexed_record_whose_digest_is_the_one_the_loader_pins():
    assert hr.record_problems(RECORD) == [] and RECORD["record_digest"] == ftm.PINNED_SET_DIGEST == ftm.load_set()["digest"]
    block = RECORD["provenance"]
    assert block["contract"] == hr.CONTRACT and block["record_id"] == ftm.SET_ID and block["generated_on"] == "2026-11-18" and block["supersedes"] is None
    index = hr.load_index(ROOT)
    entry = index["records"]["PHASE3_COMMON_TONE_V1_MULTIFAMILY_REVIEW_SET.json"]
    assert entry["class"] == hr.VERSIONED and entry["record_id"] == ftm.SET_ID and entry["record_digest"] == RECORD["record_digest"] and entry["file_sha256"] == hr.file_sha256(ftm.SET_PATH)
    assert hr.index_problems(ROOT) == []


def test_c2_the_generating_code_names_the_certified_core_and_leaves_out_only_the_two_review_modules():
    parts = RECORD["provenance"]["generating_code"]
    assert parts["clinical_core"] == CORE_DIGEST and parts["excluded_review_modules"] == list(build.REVIEW_MODULES) == ["faculty_tone_review.py", "faculty_tone_review_ui.py"]
    assert set(parts) == {"clinical_core", "application_modules", "application_module_count", "excluded_review_modules", "test_tone_pathway_analysis.py", "test_tone_review_analysis.py"}
    newer = ("faculty_titration_review.py", "faculty_titration_review_ui.py")           # (declared adaptation, P3-440: the two modules of the later titration review did not exist when this set was generated)
    modules = {name for name in ta.application_modules() if name not in build.REVIEW_MODULES and name not in newer}
    assert parts["application_module_count"] == len(modules)
    from clinical_core import amendment_3 as a3
    assert a3.amended_core_digest_now() == CORE_DIGEST, "the core that generated the set is the certified Amendment-3 core, unchanged"


def test_c3_the_content_regenerated_with_the_certified_calls_equals_the_stored_content_whatever_code_generated_its_provenance():
    stored = {key: value for key, value in RECORD.items() if key not in ("provenance", "record_digest")}
    assert build.reproduce() == stored
    if hr.same_generating_code(RECORD, build.generating_code()):                    # and when the code is also the same, the whole sealed record is reproduced byte for byte
        assert build.build() == RECORD


def test_c3b_a_regeneration_is_refused_in_place_a_new_representation_is_a_successor(tmp_path):
    other = tmp_path / "set.json"
    other.write_text(json.dumps({"x": 1}), encoding="utf-8")
    sealed = build.build()
    with pytest.raises(FileExistsError):
        hr.write(other, sealed)
    assert hr.write(tmp_path / "fresh.json", sealed) == hr.file_sha256(tmp_path / "fresh.json")


# -- the sources --------------------------------------------------------------------------------------------------------------------------------------------------------------------
def test_c4_the_certified_source_records_are_untouched_and_the_set_names_them_by_digest():
    index = hr.load_index(ROOT)["records"]
    for name, path, record in (("PHASE3_FRF_TONE_V1_CANDIDATE.json", ta.CANDIDATE_PATH, FRF), ("PHASE3_COMMON_TONE_PROBES.json", ta.PROBES_PATH, PROBES)):
        assert hr.file_sha256(path) == index[name]["file_sha256"] and hr.record_problems(record) == []
    sources = RECORD["audit"]["sources"]
    assert {sid: (entry["source_record_id"], entry["source_record_digest"], entry["source_file_sha256"]) for sid, entry in sources.items()} == {
        "FR-F": ("FR-F_TONE_V1_CANDIDATE", FRF["record_digest"], hr.file_sha256(ta.CANDIDATE_PATH)),
        "SYNTH": ("COMMON_TONE_PROBES_V1", PROBES["record_digest"], hr.file_sha256(ta.PROBES_PATH)),
        "ACS": ("COMMON_TONE_PROBES_V1", PROBES["record_digest"], hr.file_sha256(ta.PROBES_PATH)),
        "PULM-EDEMA": ("COMMON_TONE_PROBES_V1", PROBES["record_digest"], hr.file_sha256(ta.PROBES_PATH)),
        "PE": ("COMMON_TONE_PROBES_V1", PROBES["record_digest"], hr.file_sha256(ta.PROBES_PATH))}


def test_c5_every_scenario_is_equal_to_its_certified_source_by_the_audit():
    for scenario_id, audit in RECORD["audit"]["sources"].items():
        flags = {key: value for key, value in audit.items() if isinstance(value, bool) and key != "recomputed"}
        assert flags and all(flags.values()), (scenario_id, [key for key, value in flags.items() if not value])
    assert RECORD["audit"]["sources"]["FR-F"]["recomputed"] is False, "FR-F is taken from the stored record, never recomputed"
    for scenario_id in ("SYNTH", "ACS", "PULM-EDEMA", "PE"):
        assert RECORD["audit"]["sources"][scenario_id]["recomputed_with_the_certified_call_and_equal_to_the_stored_record"] is True
    assert RECORD["audit"]["witness"] == "CENTER_REFERENCE" and RECORD["audit"]["no_physiology_change"] is True and RECORD["audit"]["no_parameter_selected"] is True and RECORD["audit"]["no_witness_substituted"] is True


def test_c6_fr_f_is_the_stored_per_minute_center_reference_rows_and_the_stored_low_and_high_ones():
    source = FRF["witnesses"]
    assert ITEMS["FR-F"]["common"] == [ta.displayed(row) for row in source["CENTER_REFERENCE"]["per_minute"]]
    assert SENSITIVITY["FR-F"]["points"]["LOW"] == [ta.displayed(row) for row in source["LOW"]["per_minute"]] and SENSITIVITY["FR-F"]["points"]["HIGH"] == [ta.displayed(row) for row in source["HIGH"]["per_minute"]]
    reassessments = {row["minute"]: row for row in source["CENTER_REFERENCE"]["displayed_pressure"]}
    by_minute = {point["minute"]: point for point in ITEMS["FR-F"]["common"]}
    assert all(by_minute[minute] == row for minute, row in reassessments.items()) and sorted(reassessments) == [2, 7, 17, 32]
    assert FRF["scenario"]["order_minute"] == 2 and FRF["scenario"]["order_as_mirrored"]["rate"] == 10.0 and FRF["scenario"]["order_as_mirrored"]["units"] == "mcg/min"
    assert [row["minute"] for row in ITEMS["FR-F"]["timeline"]] == [2]


@pytest.mark.parametrize("scenario_id", sorted(FAMILY_CASE))
def test_c7_each_family_trajectory_agrees_with_the_stored_probe_at_the_stored_minutes_and_starts_from_the_authored_arrival(scenario_id):
    stored = PROBES["family_probes"][FAMILY_CASE[scenario_id]]
    points = {point["minute"]: point for point in ITEMS[scenario_id]["common"]}
    assert stored["order_minute"] == ORDER_MINUTE and [row["minute"] for row in ITEMS[scenario_id]["timeline"]] == [ORDER_MINUTE] and max(points) == HORIZON
    for name, entries in (("CENTER_REFERENCE", ITEMS[scenario_id]["common"]), ("LOW", SENSITIVITY[scenario_id]["points"]["LOW"]), ("HIGH", SENSITIVITY[scenario_id]["points"]["HIGH"])):
        by_minute = {point["minute"]: point for point in entries}
        for observed in stored["witnesses"][name]["observed"]:
            assert abs(by_minute[observed["minute"]]["map"] - observed["map_with"]) < 1.5, (scenario_id, name, observed["minute"])      # a displayed MAP is whole mmHg of rounded SBP and DBP
    reference = stored["without_the_mapping"]
    assert points[ORDER_MINUTE]["map"] == points[0]["map"] or abs(points[ORDER_MINUTE]["map"] - reference["at_the_order"]["map"]) < 1.5, "until the order the trajectory is the untreated one"
    assert abs(points[0]["map"] - reference["at_the_order"]["map"]) < 3.0
    assert (stored["case_id"], stored["family"]) == (build.FAMILIES[scenario_id][1], build.FAMILIES[scenario_id][0])


def test_c8_the_synthetic_probe_agrees_with_the_stored_distributive_probe():
    stored = PROBES["core_probes"]["distributive"]
    points = {point["minute"]: point for point in ITEMS["SYNTH"]["common"]}
    assert points[0]["map"] == round(stored["arrival"]["map"]) and abs(points[10]["map"] - stored["low_tone_before_the_order"]["map"]) < 1.5 and abs(points[40]["map"] - stored["low_tone_with_support"]["map"]) < 1.5
    assert max(points) == 40 and [row["minute"] for row in ITEMS["SYNTH"]["timeline"]] == [10] and stored["witness"] == "CENTER_REFERENCE" and "SYNTHETIC_ONLY" in stored["probe"]
    without = [point for point in points.values() if point["minute"] == 10]
    assert without and abs(without[0]["map"] - stored["low_tone_without_support"]["map"]) < 1.5, "the pressure reaches the stored untreated plateau before the order"
    assert RECORD["audit"]["sources"]["SYNTH"]["synthetic_only"] == stored["probe"]


def test_c9_the_order_in_every_scenario_is_the_one_certified_norepinephrine_start():
    order = PROBES["order"]
    assert (order["kind"], order["operation"], order["rate"], order["units"], order["minute"], order["read_until"]) == ("norepinephrine", "start", 10.0, "mcg/min", 5, 30)
    assert set(PROBES["witnesses"]) == {"LOW", "CENTER_REFERENCE", "HIGH"} and PROBES["chosen_witness"] is None and FRF["chosen_witness"] is None, "no witness was chosen by anyone"
    for item in ITEMS.values():
        assert item["timeline"][0]["action"] == "Start norepinephrine 10 mcg/min" and "10 mcg/min" in item["intervention"]


# -- the selection and the audit -----------------------------------------------------------------------------------------------------------------------------------------
def test_c10_the_audit_records_what_was_included_what_was_excluded_and_why():
    selection = RECORD["audit"]["selection"]
    assert selection["required"] == list(ftm.SCENARIOS) and selection["optional_included"] == []
    assert [(entry["scenario"], entry["case_id"], entry["status"]) for entry in selection["excluded"]] == [("opioid", "opioid_35m", "EXCLUDED"), ("asthma", "asthma_49m", "EXCLUDED")]
    for entry in selection["excluded"]:
        assert entry["reproduced_exactly_from_the_certified_call"] is True and "not clinically meaningful" in entry["reason"] and "no indication" in entry["reason"]
    assert [entry["arrival_pressure"] for entry in selection["excluded"]] == ["106/64 mmHg", "142/86 mmHg"]
    assert set(RECORD["audit"]["not_stored_with_the_items"]) and all("not stored" in text or "not recomputed" in text for text in RECORD["audit"]["not_stored_with_the_items"])


def test_c11_no_authority_grant_snapshot_or_runtime_switch_changed():
    import runtime_pressure_grant as grants
    import runtime_shadow
    import runtime_tone_support as ts
    assert runtime_shadow.COMMON_CORE_RUNTIME_AUTHORITY is False
    assert grants.GRANT_ID_V3 == "GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V3"
    mapping = FRF["mapping"]
    assert mapping["registered_adapters_declaring_it"] == [] and mapping["status"] == "DEVELOPMENT_SHADOW_ONLY" and ts.STATUS == "DEVELOPMENT_SHADOW_ONLY"
    assert {"runtime authority", "a registered adapter", "resident visibility", "scoring", "the first pilot", "titration", "any other vasopressor", "clinical validation"} <= set(mapping["not_granted"])
    assert ts.ORDER_KIND == "norepinephrine" and ts.MAPPED_OPERATION == "start" and ts.MAPPED_UNITS == "mcg/min"


def test_c12_the_set_record_holds_no_secret_no_real_data_and_no_model_identity():
    text = ftm.SET_PATH.read_text(encoding="utf-8").lower()
    for token in ("password", "secret", "api_key", "token", "@", "claude", "sonnet", "opus", "fable", "anthropic"):
        assert token not in text, token
    for name in ("faculty_tone_review.py", "faculty_tone_review_ui.py", "test_tone_review_analysis.py", "test_phase3_tone_review.py", "test_phase3_tone_review_page.py"):      # (this file names the tokens it scans for)
        source = (ROOT / name).read_text(encoding="utf-8").lower()
        assert not any(token in source for token in ("sonnet", "opus", "fable", "anthropic", "claude")), name


# -- the checkpoint of the cycle --------------------------------------------------------------------------------------------------------------------------------------------
CHECKPOINT = json.loads(build.CHECKPOINT_PATH.read_text(encoding="utf-8")) if build.CHECKPOINT_PATH.exists() else None


def test_c13_the_checkpoint_is_a_sealed_indexed_record_with_exactly_one_verdict_b_and_ties_to_the_set():
    assert CHECKPOINT is not None and hr.record_problems(CHECKPOINT) == []
    entry = hr.load_index(ROOT)["records"][build.CHECKPOINT_PATH.name]
    assert entry["class"] == hr.VERSIONED and entry["record_id"] == build.CHECKPOINT_ID and entry["record_digest"] == CHECKPOINT["record_digest"] and entry["file_sha256"] == hr.file_sha256(build.CHECKPOINT_PATH)
    assert CHECKPOINT["verdict"] == "B" and CHECKPOINT["verdict_name"] == "CORE_SCENARIOS_READY_BUT_OPTIONAL_SCENARIOS_EXCLUDED" and set(CHECKPOINT["verdicts"]) == {"A", "B", "C", "D", "E"}
    assert set(CHECKPOINT["why_not_the_others"]) == {"A", "C", "D", "E"} and CHECKPOINT["decision_reference"] == "FD-TONEREV-01 to FD-TONEREV-07"
    facts = CHECKPOINT["facts"]
    assert facts["set_record_digest"] == RECORD["record_digest"] == ftm.PINNED_SET_DIGEST and facts["order"] == list(ftm.SCENARIOS) and facts["witness"] == "CENTER_REFERENCE" and facts["optional_included"] == []
    assert [entry["scenario"] for entry in facts["excluded"]] == ["opioid", "asthma"] and facts["sensitivity_offered"] == list(ftm.SCENARIOS)
    assert facts["limitations_shown_only_in_the_final_summary"] == [entry["id"] for entry in RECORD["limitations"]]
    assert CHECKPOINT["provenance"]["generating_code"]["set_record_digest"] == RECORD["record_digest"] and CHECKPOINT["provenance"]["grant_id"] == "GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V3"


def test_c14_the_checkpoint_confirms_what_did_not_change_and_says_the_human_review_was_not_done():
    confirmations = CHECKPOINT["confirmations"]
    assert all(confirmations[key] is True for key in ("no_physiology_change", "no_parameter_selected", "no_witness_substituted", "no_norepinephrine_authority_expansion", "no_gi_recalibration", "no_source_control",
                                                       "no_consciousness_authority", "no_terminal_authority", "no_resident_deployment", "no_clinical_validation_claim", "human_review_not_performed"))
    assert confirmations["common_core_runtime_authority"] is False
    assert any("human review has not been done" in text for text in CHECKPOINT["limitations"]) and "NOT been done" in CHECKPOINT["statement"] and "Nothing else is to be done" in CHECKPOINT["next_human_action"]
    assert [step["id"] for step in CHECKPOINT["sequence"]] == [f"P3-{number}" for number in range(402, 415)]
    assert CHECKPOINT["certification"]["failures"] == 0 and CHECKPOINT["certification"]["errors"] == 0 and CHECKPOINT["certification"]["fingerprint"]
    assert [finding["id"] for finding in CHECKPOINT["adversarial_review"]["findings"]] == [str(number) for number in range(1, 10)]
