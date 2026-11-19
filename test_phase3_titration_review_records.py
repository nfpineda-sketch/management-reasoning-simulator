"""P3-438 to P3-440 and P3-447 (records and sources): the norepinephrine titration review set is a VERSIONED, indexed, sealed historical record, and every trajectory in it IS what the already-certified titration
probes hold -- nothing recomputed with another parameter, nothing tuned, nothing substituted.

What it proves:

* the set record is sealed, carries provenance, is indexed (class VERSIONED, bytes pinned) and its digest is the one the loader pins in code;
* its content, REGENERATED with the certified calls, equals the stored content (so the stored trajectories are not hand-made and not stale), whatever code generated its provenance;
* each scenario's trajectory is tied to the stored certified probe DIRECTLY (the stored per-minute series, the stored orders, the rate history the harness writes by hand) without the builder, and equal to the series
  the certified harness call produces TODAY;
* the sources are untouched (their pinned bytes are the index's), the common core is the certified Amendment-3 one, the tone constants are the certified ones, and no authority, grant or parameter changed;
* the audit names what was included, what is not (the start-only case, which already had its human review) and what is not stored with the items.
"""
import json
from pathlib import Path

import pytest

import faculty_titration_review as ftt
import historical_records as hr
import test_phase3_titration_review as module_tests
import test_titration_review_analysis as build
import test_tone_titration_analysis as tta

ROOT = Path(__file__).resolve().parent
RECORD = json.loads(ftt.SET_PATH.read_text(encoding="utf-8"))
PROBES = json.loads(tta.PROBES_PATH.read_text(encoding="utf-8"))
STORED = PROBES["gi_probes"]["probes"]
ITEMS = {item["scenario_id"]: item for item in RECORD["items"]}
CORE_DIGEST = "867bac09e09bb5c04629e73fbbdec0f7e1f100da17ef8966f580ba91067a7c9c"
#: Written by hand HERE (not read from the builder): the certified probe each scenario is.
PROBE_OF = {"TIT-1": "B_START_INCREASE", "TIT-2": "C_START_DECREASE", "TIT-3": "D_START_STOP", "TIT-4": "E_START_INCREASE_DECREASE_STOP", "TIT-5": "F_START_STOP_RESTART"}
OUTCOMES = {"TIT-1": ["STARTED", "INCREASED"], "TIT-2": ["STARTED", "DECREASED"], "TIT-3": ["STARTED", "STOPPED"], "TIT-4": ["STARTED", "INCREASED", "DECREASED", "STOPPED"], "TIT-5": ["STARTED", "STOPPED", "RESTARTED"]}


@pytest.fixture(scope="module")
def regenerated():
    """Each scenario's probe regenerated ONCE with the certified harness call (the real interpreter, engine, mirror, shadow mapping and reader)."""
    return {scenario_id: tta.gi_probe(name) for scenario_id, name in PROBE_OF.items()}


# -- the record ---------------------------------------------------------------------------------------------------------------------------------------------------------------------
def test_c1_the_set_is_a_sealed_versioned_record_whose_digest_is_the_one_the_loader_pins():
    assert hr.record_problems(RECORD) == [] and RECORD["record_digest"] == ftt.PINNED_SET_DIGEST == ftt.load_set()["digest"]
    block = RECORD["provenance"]
    assert block["contract"] == hr.CONTRACT and block["record_id"] == ftt.SET_ID and block["generated_on"] == "2026-11-19" and block["supersedes"] is None
    assert RECORD["record_type"] == ftt.SET_TYPE and RECORD["version"] == ftt.VERSION and RECORD["order"] == list(ftt.SCENARIOS)


def test_c2_the_generating_code_names_the_certified_core_and_the_certified_harnesses():
    parts = RECORD["provenance"]["generating_code"]
    assert parts["clinical_core"] == CORE_DIGEST and parts["excluded_review_modules"] == list(build.REVIEW_MODULES) == ["faculty_titration_review.py", "faculty_titration_review_ui.py"]
    assert set(parts) == {"clinical_core", "test_tone_titration_analysis.py", "test_titration_review_analysis.py", "test_tone_review_analysis.py", "excluded_review_modules"}
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
    sealed = build.build(regenerate=False)
    with pytest.raises(FileExistsError):
        hr.write(other, sealed)
    assert hr.write(tmp_path / "fresh.json", sealed) == hr.file_sha256(tmp_path / "fresh.json")


# -- the source ---------------------------------------------------------------------------------------------------------------------------------------------------------------------
def test_c4_the_certified_source_record_is_untouched_and_the_set_names_it_by_digest():
    index = hr.load_index(ROOT)["records"]
    name = tta.PROBES_PATH.name
    assert hr.file_sha256(tta.PROBES_PATH) == index[name]["file_sha256"] == hr.file_sha256(tta.PROBES_PATH) and hr.record_problems(PROBES) == []
    sources = RECORD["audit"]["sources"]
    assert {scenario_id: (entry["source_record_id"], entry["source_record_digest"], entry["source_file_sha256"], entry["probe"]) for scenario_id, entry in sources.items()} == {
        scenario_id: ("NOREPINEPHRINE_TITRATION_PROBES_V1", PROBES["record_digest"], hr.file_sha256(tta.PROBES_PATH), PROBE_OF[scenario_id]) for scenario_id in PROBE_OF}
    assert hr.index_problems(ROOT) == []


def test_c5_every_scenario_is_equal_to_its_certified_source_by_the_audit():
    for scenario_id, audit in RECORD["audit"]["sources"].items():
        flags = {key: value for key, value in audit.items() if isinstance(value, bool) and key != "recomputed_to_check"}
        assert flags and all(flags.values()), (scenario_id, [key for key, value in flags.items() if not value])
        assert audit["recomputed_to_check"] is True and audit["witness"] == "CENTER_REFERENCE" and audit["case_id"] == "gi_bleed_57m"
        assert audit["regenerated_series_equals_the_stored_one"] is True and audit["regenerated_orders_equal_the_stored_ones"] is True and audit["rate_history_equals_the_faculty_plan"] is True
    assert RECORD["audit"]["witness"] == "CENTER_REFERENCE" and RECORD["audit"]["no_physiology_change"] is True and RECORD["audit"]["no_parameter_selected"] is True and RECORD["audit"]["no_witness_substituted"] is True


@pytest.mark.parametrize("scenario_id", sorted(PROBE_OF))
def test_c6_each_trajectory_is_the_stored_per_minute_series_of_its_certified_probe_unchanged(scenario_id):
    stored = STORED[PROBE_OF[scenario_id]]
    assert ITEMS[scenario_id]["common"] == [{"minute": row["minute"], "sbp": row["sbp"], "dbp": row["dbp"], "map": row["map"]} for row in stored["per_minute"]], "taken without recomputing"
    assert [row["minute"] for row in ITEMS[scenario_id]["common"]] == list(range(33))
    reads = {row["minute"]: row["displayed"] for row in stored["at_the_reads"]}
    by_minute = {point["minute"]: point for point in ITEMS[scenario_id]["common"]}
    assert sorted(reads) == [2, 10, 18, 25, 32] and all(by_minute[minute] == shown for minute, shown in reads.items()), "the displayed pressure at the certified reads is the series"
    assert (by_minute[0]["sbp"], by_minute[0]["dbp"], by_minute[0]["map"]) == (88, 54, 65)
    assert stored["gaps"] == [] and stored["failures"] == [] and stored["dispositions"] == ["BUILT"] * len(OUTCOMES[scenario_id]) and stored["replays_exactly"] is True


@pytest.mark.parametrize("scenario_id", sorted(PROBE_OF))
def test_c7_the_rate_changes_shown_are_the_orders_the_certified_probe_handed_over_and_the_faculty_plan(scenario_id):
    stored = STORED[PROBE_OF[scenario_id]]
    assert [order["outcome"] for order in stored["orders"]] == OUTCOMES[scenario_id]
    expected = [(order["minute"], {"STARTED": "START", "INCREASED": "INCREASE", "DECREASED": "DECREASE", "STOPPED": "STOP", "RESTARTED": "RESTART"}[order["outcome"]],
                 0.0 if order["outcome"] == "STOPPED" else float(order["rate"])) for order in stored["orders"]]
    assert [(change["minute"], change["operation"], change["rate_mcg_min"]) for change in ITEMS[scenario_id]["rate_changes"]] == expected
    assert [(change["minute"], change["rate_mcg_min"]) for change in ITEMS[scenario_id]["rate_changes"]] == module_tests.FACULTY_PLAN[scenario_id]
    assert [[minute, rate] for minute, rate in stored["rate_history_as_written"]] == [[minute, rate] for minute, rate in module_tests.FACULTY_PLAN[scenario_id]]
    assert all(order["units"] == "mcg/min" for order in stored["orders"] if order["units"])


@pytest.mark.parametrize("scenario_id", sorted(PROBE_OF))
def test_c8_each_trajectory_equals_what_the_certified_harness_call_produces_today(scenario_id, regenerated):
    again, stored = regenerated[scenario_id], STORED[PROBE_OF[scenario_id]]
    assert again["per_minute"] == stored["per_minute"] and again["orders"] == stored["orders"] and again["rate_history_as_written"] == stored["rate_history_as_written"] and again["script"] == stored["script"]
    assert ITEMS[scenario_id]["common"] == [{"minute": row["minute"], "sbp": row["sbp"], "dbp": row["dbp"], "map": row["map"]} for row in again["per_minute"]]


def test_c9_the_five_trajectories_are_five_different_certified_probes_and_the_start_only_case_is_not_among_them():
    assert len(set(PROBE_OF.values())) == 5 and "A_START" not in PROBE_OF.values() and "A10_START" not in PROBE_OF.values()
    assert RECORD["audit"]["selection"]["not_included"] == [{"scenario": "START-only", "reason": "it has already undergone human faculty review (FD-TITREV-05)"}]
    assert RECORD["audit"]["selection"]["required"] == list(ftt.SCENARIOS) and RECORD["audit"]["selection"]["excluded"] == []
    series = {scenario_id: json.dumps(ITEMS[scenario_id]["common"]) for scenario_id in PROBE_OF}
    assert len(set(series.values())) == 5, "no two scenarios draw the same trajectory"
    assert ITEMS["TIT-5"]["common"][:19] == ITEMS["TIT-3"]["common"][:19], "the restart scenario is the stop scenario until the restart: one certified history, two continuations"


# -- the audit and the scope ----------------------------------------------------------------------------------------------------------------------------------------------------
def test_c10_the_audit_records_what_is_not_stored_with_the_items_and_the_limitations_apart():
    stored_text = " ".join(RECORD["audit"]["not_stored_with_the_items"]).lower()
    for needle in ("heart rate and capillary refill", "tone state", "rate history of the writer", "no other setting of the response (low, high)"):
        assert needle in stored_text, needle
    assert [entry["id"] for entry in RECORD["limitations"]] == list(ftt.LIMITATION_IDS) and "sensitivity" not in RECORD
    assert RECORD["audit"]["decision_reference"].startswith("FD-TITREV-01 to FD-TITREV-13")


def test_c11_no_authority_grant_snapshot_tone_constant_or_runtime_switch_changed():
    import runtime_authority
    import runtime_pressure_grant as grants
    import runtime_shadow
    import runtime_tone_support as ts
    assert runtime_shadow.COMMON_CORE_RUNTIME_AUTHORITY is False
    assert grants.GRANT_ID_V3 == "GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V3"
    assert not any("norepinephrine" in action for action in runtime_authority.SUPPORTED_ACTIONS), "norepinephrine stays outside the live authority"
    assert ts.STATUS == "DEVELOPMENT_SHADOW_ONLY" and ts.ORDER_KIND == "norepinephrine"
    constants = PROBES["design"]["dynamics"]["constants"]
    assert constants == {"half_effect_rate_mcg_min": 10.0, "offset_tau_min": 2.5, "onset_tau_min": 1.5, "tone_gain": 0.6} and PROBES["design"]["dynamics"]["constants_changed"] is False
    assert tta._witness() == {"tone_gain": 0.6, "half_effect_rate_mcg_min": 10.0, "onset_tau_min": 1.5, "offset_tau_min": 2.5}, "the live CENTER_REFERENCE constants are the certified ones"
    assert PROBES["witness"] == "CENTER_REFERENCE" and set(PROBES["gi_probes"]["checks"]) >= {"DIRECTION", "TIMING", "PERSISTENCE_AND_DECAY"} and PROBES["gi_probes"]["all_as_predicted"] is True


def test_c12_the_set_record_holds_no_secret_no_real_data_and_no_model_identity():
    text = ftt.SET_PATH.read_text(encoding="utf-8").lower()
    for token in ("password", "secret", "api_key", "token", "@", "claude", "sonnet", "opus", "fable", "anthropic", "reviewer"):
        assert token not in text, token
    for name in ("faculty_titration_review.py", "faculty_titration_review_ui.py", "test_titration_review_analysis.py", "test_phase3_titration_review.py", "test_phase3_titration_review_page.py"):      # (this file names the tokens it scans for)
        source = (ROOT / name).read_text(encoding="utf-8").lower()
        assert not any(token in source for token in ("sonnet", "opus", "fable", "anthropic", "claude")), name


def test_c13_the_earlier_certified_records_the_review_reads_from_are_not_touched_by_this_package():
    index = hr.load_index(ROOT)["records"]
    for name in ("PHASE3_NOREPINEPHRINE_TITRATION_PROBES.json", "PHASE3_NOREPINEPHRINE_TITRATION_CHECKPOINT.json", "NEGATIVE_CONTROL_HYPERTENSIVE_PULMONARY_EDEMA_NOREPI_V1.json",
                 "PHASE3_COMMON_TONE_V1_MULTIFAMILY_REVIEW_SET.json", "PHASE3_COMMON_TONE_PROBES.json", "PHASE3_FRF_TONE_V1_CANDIDATE.json"):
        entry = index[name]
        assert entry["file_sha256"] == hr.file_sha256(ROOT / "docs" / "revision" / name), name


# -- the documents of the cycle ----------------------------------------------------------------------------------------------------------------------------------------------
DOC = (ROOT / "docs" / "PHASE3_NOREPINEPHRINE_TITRATION_REVIEW.md").read_text(encoding="utf-8")
COLA = (ROOT / "docs" / "COLA_DECISIONES_AI_ADVISOR.md").read_text(encoding="utf-8")
DEBT = (ROOT / "docs" / "REGISTRO_DEUDA_TECNICA.md").read_text(encoding="utf-8")
CLAUDE = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")


def test_c14_the_decision_file_holds_the_thirteen_faculty_decisions_and_the_execution_rows_and_the_debt_is_registered():
    for number in range(1, 14):
        assert f"| FD-TITREV-{number:02d} |" in COLA, number
    for identifier in ("FD-P3-277", "FD-P3-278", "FD-P3-279"):
        assert f"| {identifier} |" in COLA, identifier
    row = next(line for line in COLA.splitlines() if line.startswith("| FD-TITREV-07 |"))
    q = module_tests.FACULTY_QUESTION
    assert all(q[key] in row for key in ("TIT-1", "TIT-3", "TIT-4", "TIT-5")) and "decrease smoothly and at an appropriate time after the norepinephrine rate is reduced?" in row, "the five questions, in the faculty's words"
    assert "## TD-159 ·" in DEBT and "La revisión humana no se hizo" in DEBT and "Sólo `CENTER_REFERENCE`" in DEBT
    assert "revisión docente interactiva de la titulación" in CLAUDE and "FD-TITREV-01 a FD-TITREV-13" in CLAUDE and "`TD-159`" in CLAUDE and "MRS_FACULTY_TITRATION_GATE=off" in CLAUDE


def test_c15_the_document_states_the_faculty_questions_in_the_faculty_words_the_five_probes_and_how_to_launch_the_review():
    for question in module_tests.FACULTY_QUESTION.values():
        assert question in DOC, question
    for probe in PROBE_OF.values():
        assert f"`{probe}`" in DOC, probe
    for needle in ("NOREPINEPHRINE_TITRATION_V1_FACULTY_REVIEW", "REVIEW COMPLETE · 5 / 5", "CURRENT LIMITATIONS", "MRS_FACULTY_TITRATION_GATE=off", "streamlit run app.py", "SUBMIT & NEXT", "LOCK FIRST IMPRESSION",
                   "La revisión humana **no se hizo**", "No se excluyó ninguno", "1366 × 768", "1440 × 900", "websocket"):
        assert needle in DOC, needle
    assert "faculty_titration_review.PINNED_SET_DIGEST" in DOC


# -- the checkpoint of the cycle --------------------------------------------------------------------------------------------------------------------------------------------
import test_titration_review_checkpoint as cp  # noqa: E402

CHECKPOINT = json.loads(cp.CHECKPOINT_PATH.read_text(encoding="utf-8")) if cp.CHECKPOINT_PATH.exists() else None
needs_the_checkpoint = pytest.mark.skipif(CHECKPOINT is None, reason="the checkpoint is written after the certification of the frozen candidate")


@needs_the_checkpoint
def test_c16_the_checkpoint_is_a_sealed_indexed_record_with_exactly_one_verdict_and_ties_to_the_set():
    assert hr.record_problems(CHECKPOINT) == []
    entry = hr.load_index(ROOT)["records"][cp.CHECKPOINT_PATH.name]
    assert entry["class"] == hr.VERSIONED and entry["record_id"] == cp.CHECKPOINT_ID and entry["record_digest"] == CHECKPOINT["record_digest"] and entry["file_sha256"] == hr.file_sha256(cp.CHECKPOINT_PATH)
    assert CHECKPOINT["verdict"] in cp.VERDICTS and CHECKPOINT["verdict_name"] == cp.VERDICTS[CHECKPOINT["verdict"]] and set(CHECKPOINT["verdicts"]) == {"A", "B", "C", "D", "E"}
    assert set(CHECKPOINT["why_not_the_others"]) == {"A", "B", "C", "D", "E"} and CHECKPOINT["decision_reference"] == "FD-TITREV-01 to FD-TITREV-13"
    facts = CHECKPOINT["facts"]
    assert facts["set_record_digest"] == RECORD["record_digest"] == ftt.PINNED_SET_DIGEST and facts["order"] == list(ftt.SCENARIOS) and facts["witness"] == "CENTER_REFERENCE" and facts["excluded"] == []
    assert CHECKPOINT["provenance"]["generating_code"]["set_record_digest"] == RECORD["record_digest"] and CHECKPOINT["provenance"]["grant_id"] == "GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V3"


@needs_the_checkpoint
def test_c17_the_checkpoint_confirms_what_did_not_change_says_the_human_review_was_not_done_and_holds_the_certification():
    confirmations = CHECKPOINT["confirmations"]
    assert all(confirmations[key] is True for key in ("no_tone_recalibration", "no_pump_coupling_change", "no_physiology_change", "no_parameter_selected", "no_witness_substituted", "no_norepinephrine_authority_expansion",
                                                       "no_consciousness_authority", "no_terminal_authority", "no_resident_deployment", "no_clinical_validation_claim", "no_weight_based_dosing",
                                                       "no_map_target_titration", "no_new_vasopressor", "human_review_not_performed")) and confirmations["common_core_runtime_authority"] is False
    assert any("human review has not been done" in text for text in CHECKPOINT["limitations"]) and "NOT been done" in CHECKPOINT["statement"] and "Nothing else is to be done" in CHECKPOINT["next_human_action"]
    assert [step["step"] for step in CHECKPOINT["sequence"]] == [f"P3-{number}" for number in range(438, 449)]
    certification = CHECKPOINT["certification"]
    assert certification["scope"] in ("FULL", "FOCUSED") and certification["full_suite"]["failures"] == 0 and certification["full_suite"]["errors"] == 0 and certification["full_suite"]["valid"] is True
    assert certification["full_suite"]["fingerprint_at_start"] == certification["full_suite"]["fingerprint_at_end"] and certification["regressions"]["active_passed"] == certification["regressions"]["active_total"]
    review = CHECKPOINT["adversarial_review"]
    assert review["independent"] is True and review["reviews"] == 1 and [finding["id"] for finding in review["findings"]] == list(range(1, 8)) and review["unresolved_blocking_findings"] == []
    assert not [finding for finding in review["findings"] if finding["severity"] in ("BLOCKER", "MAJOR")]


@needs_the_checkpoint
def test_c18_the_document_and_the_decision_file_state_the_verdict_and_the_fingerprint_of_the_certified_candidate():
    assert "PENDIENTE" not in DOC, "the document has no placeholder left"
    assert "| FD-P3-280 |" in COLA
    row = next(line for line in COLA.splitlines() if line.startswith("| FD-P3-280 |"))
    fingerprint = CHECKPOINT["certification"]["candidate"]["fingerprint"]
    assert CHECKPOINT["verdict_name"] in DOC and CHECKPOINT["verdict_name"] in row and fingerprint[:12] in DOC and fingerprint[:12] in row
