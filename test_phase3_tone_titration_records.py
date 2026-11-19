"""P3-424 to P3-437 (records): the sealed records, the decisions, the debt, the document, CLAUDE.md and the checkpoint of the norepinephrine titration package say the same thing.

These tests read the documents and the records, which are the third commit of the publication; the tests of the behaviour itself (test_phase3_tone_titration.py) do not depend on them.

The checkpoint record is written ONCE, after the certification, because it carries the certification's own figures: until it exists the tests that read it are skipped, saying so, and
the others run. A candidate that is being certified therefore runs these without the checkpoint, and the final tree runs all of them.
"""
import json
import re
from pathlib import Path

import pytest

import historical_records as hr
import runtime_tone_support as ts
import test_tone_titration_analysis as tt

ROOT = Path(__file__).resolve().parent
REV = ROOT / "docs" / "revision"
CORE_DIGEST = "867bac09e09bb5c04629e73fbbdec0f7e1f100da17ef8966f580ba91067a7c9c"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read(*parts: str) -> str:
    return ROOT.joinpath(*parts).read_text(encoding="utf-8")


PROBES, CONTROL = _load(tt.PROBES_PATH), _load(tt.NEGATIVE_CONTROL_PATH)
CHECKPOINT = _load(tt.CHECKPOINT_PATH) if tt.CHECKPOINT_PATH.exists() else None
needs_the_checkpoint = pytest.mark.skipif(CHECKPOINT is None, reason="the checkpoint record is written once, after the certification: it does not exist yet")
DOC = _read("docs", "PHASE3_NOREPINEPHRINE_TITRATION.md")
COLA = _read("docs", "COLA_DECISIONES_AI_ADVISOR.md")
DEBT = _read("docs", "REGISTRO_DEUDA_TECNICA.md")
CLAUDE = _read("CLAUDE.md")


def _row(row_id: str) -> str:
    rows = [line for line in COLA.split("\n") if line.startswith(f"| {row_id} |")]
    assert len(rows) == 1, row_id
    return rows[0]


def test_r1_the_records_are_sealed_versioned_and_indexed_with_the_bytes_the_index_pins():
    index = hr.load_index(ROOT)["records"]
    records = [(PROBES, tt.PROBES_PATH, tt.PROBES_ID), (CONTROL, tt.NEGATIVE_CONTROL_PATH, tt.NEGATIVE_CONTROL_ID)] + ([(CHECKPOINT, tt.CHECKPOINT_PATH, tt.CHECKPOINT_ID)] if CHECKPOINT else [])
    assert (tt.CHECKPOINT_PATH.name in index) is (CHECKPOINT is not None), "the checkpoint is indexed when, and only when, it exists"
    for record, path, record_id in records:
        assert hr.record_problems(record) == [] and record["provenance"]["record_id"] == record_id and record["provenance"]["generated_on"] == tt.GENERATED_ON == "2026-11-19" and record["provenance"]["supersedes"] is None
        assert index[path.name] == {"class": hr.VERSIONED, "file_sha256": hr.file_sha256(path), "record_id": record_id, "record_digest": record["record_digest"]}
    assert hr.index_problems(ROOT) == []
    parts = PROBES["provenance"]["generating_code"]
    assert parts["clinical_core"] == CORE_DIGEST and "test_tone_titration_analysis.py" in parts and "application_modules" in parts


def test_r2_the_probes_record_says_what_the_design_and_the_runs_say():
    design = PROBES["design"]
    assert design["order_semantics_audit"]["verdict"] == "B" and design["order_semantics_audit"]["verdict_name"] == "SMALL_NOREPINEPHRINE_EVENT_ADAPTER_REQUIRED"
    assert design["governance"]["verdict"] == "A" and design["governance"]["verdict_name"] == "RUNTIME_ADAPTER_ONLY" and design["governance"]["clinical_core_edited"] is False
    assert design["governance"]["core_digest"] == CORE_DIGEST and design["governance"]["grant_changed"] is False and design["dynamics"]["constants_changed"] is False and design["dynamics"]["new_constants"] == []
    assert design["dynamics"]["constants"] == {"half_effect_rate_mcg_min": 10.0, "onset_tau_min": 1.5, "offset_tau_min": 2.5, "tone_gain": 0.6}
    assert design["writer"]["type_name"] == "norepinephrine_rate_history" and design["writer"]["is_a"] == "clinical_core.vascular_support.Norepinephrine" and design["writer"]["version"] == ts.WRITER_VERSION
    assert design["event_stream"]["units_read"] == "mcg/min" and design["event_stream"]["engine_vocabulary_read"] == ["start", "adjust", "continue", "stop"]
    assert design["event_stream"]["what_an_order_not_carried_is"] == list(ts.NOT_CARRIED) and "corrected_after_the_adversarial_review" in design["order_semantics_audit"]["found"]
    assert "not the only" in design["dynamics"]["why_this_rule"] and "no faculty member has reviewed it yet" in design["dynamics"]["why_this_rule"]
    assert design["layer"]["summary"] == json.loads(json.dumps(ts.summary())), "the record carries the mapping's own summary, as it is now"
    gi = PROBES["gi_probes"]
    assert gi["predictions_written_before_the_runs"] == tt.GI_PREDICTIONS and gi["all_as_predicted"] is True and all(gi["checks"].values()) and len(gi["checks"]) == 7
    assert set(gi["probes"]) == set(tt.GI_SCRIPTS) and gi["named_probes"] == tt.NAMED_PROBES and gi["witness"] == "CENTER_REFERENCE"
    edges = PROBES["edge_cases"]
    assert edges["expected_outcomes_were_written_before_the_matrix_was_executed"] is True and edges["all_as_expected"] is True and len(edges["rows"]) == 21
    assert {row["case"]: row["expected_before_executing"] for row in edges["rows"]} == json.loads(json.dumps(tt.EDGE_EXPECTED))
    # what the adversarial review changed in the matrix is IN the record: the revised row keeps the expectation it replaced, and the added ones are marked
    after = edges["after_the_adversarial_review"]
    assert after["revised"] == ["07_TWO_ORDERS_IN_ONE_MINUTE"] and after["added"] == json.loads(json.dumps(tt.EDGE_ADDED_AFTER_THE_REVIEW)) and "17 rows" in after["said_plainly"]
    revised = next(row for row in edges["rows"] if row["case"] == "07_TWO_ORDERS_IN_ONE_MINUTE")["revised_after_the_adversarial_review"]
    assert revised["expected_before_the_review"]["outcomes"] == ["STARTED", "INCREASED"] and revised["expected_before_the_review"] != tt.EDGE_EXPECTED["07_TWO_ORDERS_IN_ONE_MINUTE"]
    assert [row["case"] for row in edges["rows"] if row.get("added_after_the_adversarial_review")] == tt.EDGE_ADDED_AFTER_THE_REVIEW["cases"]
    real = PROBES["real_text_probes"]
    assert real["all_as_expected"] is True and real["no_run_differs_from_the_engine_without_saying_so"] is True and set(real["probes"]) == set(tt.REAL_TEXT_SCRIPTS)
    assert {name: probe["expected_before_it_was_run_through_the_repaired_mapping"] for name, probe in real["probes"].items()} == json.loads(json.dumps(tt.REAL_TEXT_EXPECTED))
    assert [name for name, probe in real["probes"].items() if not probe["the_run_and_the_engine_run_the_same_rate"]] == ["R1_STOP_THE_INFUSION", "R2_INCREASE_THE_INFUSION_RATE",
                                                                                                                      "R3_INCREASE_WITHOUT_UNITS_THEN_STOP", "R5_PRESSURE_TARGET", "R6_WEIGHT_BASED_START"]
    assert any("CLOSE the infusion" in item and "a later explicit stop included" in item for item in PROBES["limitations"]), "the limit the review found is said in the record, not softened"
    families = PROBES["multifamily"]
    assert families["no_regression"] is True and families["the_support_is_the_same_in_every_family"] is True and set(families["families"]) == {"gi_bleed", "pulmonary_embolism", "acs", "pulmonary_edema"}
    assert all(item["the_certified_single_start_is_unchanged"]["equal_to_the_certified_probe_record"] for item in families["families"].values())
    assert "not a clinical validation" in PROBES["statement"] and any("no faculty member has yet reviewed a titration trajectory" in item for item in PROBES["limitations"])


def test_r3_the_records_regenerate_to_the_stored_content_under_the_same_generating_code():
    current = tt.generating_code()
    if not (hr.same_generating_code(PROBES, current) and hr.same_generating_code(CONTROL, current)):
        pytest.skip("generated by other code: the records stand as written (P3-388); a new representation is a successor record, never a regeneration")
    assert tt.content_of(tt.build_probes()) == tt.content_of(PROBES)
    assert tt.content_of(tt.build_negative_control()) == tt.content_of(CONTROL)


def test_r4_the_negative_control_record_keeps_the_reject_and_the_physiology():
    assert CONTROL["scenario_id"] == "HYPERTENSIVE_PULMONARY_EDEMA_NOREPI" and CONTROL["classification"] == "NEGATIVE_CONTROL_MANAGEMENT_SCENARIO" and CONTROL["mechanism_failure"] is False
    assert CONTROL["decision_reference"].startswith("FD-TITRATE-10") and CONTROL["human_evidence"]["overall"] == "REJECT"
    human, ratification = _load(REV / "PHASE3_HUMAN_COMMON_TONE_MULTIFAMILY_REVIEW.json"), _load(REV / "COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1_RATIFICATION.json")
    assert CONTROL["human_evidence"]["record"]["record_digest"] == human["record_digest"] and CONTROL["earlier_classification"]["record"]["record_digest"] == ratification["record_digest"]
    judged = next(entry for entry in human["scenarios"] if entry["scenario_id"] == "PULM-EDEMA")
    assert CONTROL["human_evidence"]["faculty_interpretation_as_reported"] == judged["faculty_interpretation_as_reported"] and CONTROL["physiology"]["reviewed_trajectory_digest"] == judged["reviewed_trajectory_digest"]
    assert CONTROL["physiology"]["altered"] is False and CONTROL["physiology"]["the_trajectory_recomputed_now_is_the_one_the_faculty_reviewed"] is True
    assert CONTROL["use"]["built_into_the_application"] is False and CONTROL["use"]["resident_visible"] is False and CONTROL["use"]["norepinephrine_made_unavailable"] is False
    assert not [path.name for path in ROOT.glob("*.py") if not path.name.startswith("test_") and "HYPERTENSIVE_PULMONARY_EDEMA_NOREPI" in path.read_text(encoding="utf-8")], "a record nothing executable reads"


def test_r5_the_decisions_the_debt_the_document_and_claude_md_say_the_same_thing():
    for index in range(1, 14):
        assert len(_row(f"FD-TITRATE-{index:02d}")) > 80
    for index in range(273, 276):
        assert len(_row(f"FD-P3-{index}")) > 200
    for row_id, text in {"FD-TITRATE-02": "segundo escritor de `T`", "FD-TITRATE-03": "0,6", "FD-TITRATE-05": "dinámica de cese", "FD-TITRATE-06": "mcg/kg/min", "FD-TITRATE-07": "**una** historia de infusión",
                         "FD-TITRATE-09": "fallan cerrado", "FD-TITRATE-10": "NEGATIVE_CONTROL_MANAGEMENT_SCENARIO", "FD-TITRATE-11": "COMMON_TONE_PUMP_DEPENDENCE_NOT_YET_VALIDATED",
                         "FD-TITRATE-12": "CONSCIOUSNESS_UNDER_TONE_UNRESOLVED", "FD-TITRATE-13": "Alto duro", "FD-P3-273": "veredicto **A**", "FD-P3-274": "NorepinephrineRateHistory",
                         "FD-P3-275": "NEGATIVE_CONTROL_MANAGEMENT_SCENARIO"}.items():
        assert text in _row(row_id), row_id
    assert "tal como se escribió" in _row("FD-P3-273") and "REPLACED_WITHIN_ITS_MINUTE" in _row("FD-P3-274") and "se **revisó** uno" in _row("FD-P3-275"), "the rows say what the review corrected"
    assert "## TD-158" in DEBT
    section = DEBT[DEBT.index("## TD-158"):]
    for text in ("Ninguna persona docente ha revisado una trayectoria de titulación", "NorepinephrineRateHistory", "se rechaza por nombre", "Fallo cerrado", "nunca convertida", "sólo no regresión",
                 "Control negativo: sólo un registro", "adaptaciones declaradas", "No es validación clínica", "El espejo entrega la orden tal como se escribió", "deja de mostrar lo que corre el motor",
                 "65 mcg/min", "tenía una expectativa equivocada", "vistas históricas del linaje"):
        assert text in section, text
    assert DEBT.count("[2026-11-18, titulación") == 2, "the two older items the package supersedes are marked, not edited"
    for text in ("docs/PHASE3_NOREPINEPHRINE_TITRATION.md", "FD-TITRATE-01 a FD-TITRATE-13", "FD-P3-273 a FD-P3-276", "`TD-158`", "NorepinephrineRateHistory", "`clinical_core/` **no se editó**",
                 "NEGATIVE_CONTROL_MANAGEMENT_SCENARIO", "**fuera** de la autoridad viva", "**ninguna persona docente ha revisado todavía una trayectoria de titulación**"):
        assert text in CLAUDE, text
    assert CLAUDE.count("FD-P3-269 a FD-P3-272 y `TD-157`;") == 1, "the new clause continues the ratification clause: it does not replace it"
    for name in ("PHASE3_COMMON_TONE_RATIFICATION.md", "PHASE3_COMMON_VASCULAR_TONE.md"):
        text = _read("docs", name)
        assert "Nota 2026-11-18 (titulación)" in text and "PHASE3_NOREPINEPHRINE_TITRATION.md" in text and "no se editan" in text, name


def test_r6_the_document_states_the_contract_the_numbers_and_what_is_not_done():
    for text in ("SMALL NOREPINEPHRINE EVENT ADAPTER_REQUIRED", "RUNTIME/ADAPTER ONLY", "norepinephrine_rate_history/P3-431", "NEGATIVE_CONTROL_MANAGEMENT_SCENARIO",
                 "bit a bit", "(s, s + 1]", "IDEMPOTENT_NO_CHANGE", "REPLACED_WITHIN_ITS_MINUTE", "HistoryRewritten", "nunca convertida", "1,339", "1,112", "96/59 (71)", "99/61 (74)", "91/56 (68)", "80/49 (59)",
                 "ninguna persona docente ha revisado todavía una trayectoria de titulación", "No se pide a la docencia una calibración en mmHg",
                 # the adversarial review, said plainly: the blocker, what was only partly repaired, and the matrix that was revised
                 "**Bloqueante**", "infusion_adjustment", "**Parcial, y así se declara.**", "El cierre persistente sigue", "ya no muestra lo que corre el motor", "**no la única concebible**",
                 "una de esas 17 expectativas describía una regla equivocada", "Nada se ajustó para que pasara", "14 mutantes"):
        assert text in DOC, text
    # the real-text table of the document is the record's
    real = PROBES["real_text_probes"]["probes"]
    for name, shown in {"R1_STOP_THE_INFUSION": "0 / 10", "R2_INCREASE_THE_INFUSION_RATE": "20 / 10", "R5_PRESSURE_TARGET": "**65** / 10", "R6_WEIGHT_BASED_START": "11,1 / 0"}.items():
        engine, run = real[name]["observed"]["engine_rate_at_the_end"], real[name]["observed"]["run_rate_at_the_end"]
        assert shown in DOC and shown.replace("*", "").replace(",", ".").split(" / ") == [f"{engine:g}", f"{run:g}"], name
    reads = {row["minute"]: row["displayed"] for row in PROBES["gi_probes"]["probes"]["E_START_INCREASE_DECREASE_STOP"]["at_the_reads"]}
    for minute in (10, 18, 25, 32):
        shown = reads[minute]
        assert f"{shown['sbp']}/{shown['dbp']} ({shown['map']})" in DOC, (minute, "the table of the document is the record's")
    for text in ("objetivos automáticos de PAM", "dosificación por peso", "otro vasopresor", "recalibración del tono", "ampliación de la autoridad de norepinefrina", "piloto con residentes"):
        assert text in DOC, text


@needs_the_checkpoint
def test_r6b_once_the_checkpoint_exists_the_document_and_the_decision_file_carry_its_verdict_and_nothing_is_left_pending():
    assert "PENDIENTE" not in DOC, "every section of the document is written"
    assert CHECKPOINT["verdict_name"] in DOC and CHECKPOINT["verdict_name"] in _row("FD-P3-276") and len(_row("FD-P3-276")) > 200
    for letter, name in CHECKPOINT["verdicts"].items():
        assert name in DOC, letter
    fingerprint = CHECKPOINT["certification"]["candidate"]["fingerprint"]
    assert fingerprint in DOC and fingerprint[:12] in _row("FD-P3-276"), "the document and the decision row name the candidate that was certified"


@needs_the_checkpoint
def test_r7_the_checkpoint_is_sealed_carries_one_verdict_and_the_facts_of_the_records():
    assert CHECKPOINT["verdict"] in tt.VERDICTS and CHECKPOINT["verdict_name"] == tt.VERDICTS[CHECKPOINT["verdict"]] and CHECKPOINT["verdicts"] == tt.VERDICTS
    assert set(CHECKPOINT["why_not_the_others"]) == set(tt.VERDICTS) - {CHECKPOINT["verdict"]}
    facts = CHECKPOINT["facts"]
    assert (facts["probes_record_digest"], facts["negative_control_record_digest"]) == (PROBES["record_digest"], CONTROL["record_digest"])
    assert facts["order_semantics_audit"] == "SMALL_NOREPINEPHRINE_EVENT_ADAPTER_REQUIRED" and facts["governance"] == "RUNTIME_ADAPTER_ONLY" and facts["core_digest"] == CORE_DIGEST
    assert all(facts["gi_checks"].values()) and all(facts["edge_cases_as_expected"].values()) and len(facts["edge_cases_as_expected"]) == 21 and facts["multifamily_no_regression"] is True
    assert all(facts["real_text_probes_as_expected"].values()) and len(facts["real_text_probes_as_expected"]) == 8 and facts["no_run_differs_from_the_engine_without_saying_so"] is True
    assert facts["norepinephrine_in_supported_actions"] is False and facts["norepinephrine_not_granted_by_the_live_grant"] is True and facts["common_core_runtime_authority"] is False
    for key in ("no_tone_recalibration", "no_pump_coupling_change", "no_new_physiology", "no_authority_expansion", "no_consciousness_authority", "no_terminal_authority", "no_resident_deployment",
                "no_clinical_validation_claim", "clinical_core_not_edited", "no_automatic_titration_or_pressure_target", "no_weight_based_dosing", "no_other_vasopressor"):
        assert CHECKPOINT["confirmations"][key] is True, key
    certification = CHECKPOINT["certification"]
    assert certification["scope"] == "FULL" and certification["full_suite"]["failures"] == 0 and certification["full_suite"]["errors"] == 0 and certification["full_suite"]["tests"] > 13000
    assert certification["regressions"]["active_passed"] == certification["regressions"]["active_total"] and len(certification["candidate"]["fingerprint"]) == 64
    review = CHECKPOINT["adversarial_review"]
    assert review["independent"] is True and review["reviews"] == 1 and isinstance(review["findings"], list) and all(item["disposition"] for item in review["findings"])
    assert [item["severity"] for item in review["findings"]][:4] == ["BLOCKER", "MAJOR", "MAJOR", "MAJOR"] and any(item["disposition"].startswith("PARTLY") for item in review["findings"]), \
        "the checkpoint says what the review found and what was only partly repaired"
    assert any("SETTLED order" in item for item in CHECKPOINT["open_faculty_decisions"])
    assert [item["step"] for item in CHECKPOINT["sequence"]] == [f"P3-{number}" for number in range(424, 438)]
    assert CHECKPOINT["next_human_action"].startswith("A faculty member looks at the titration and stop development trajectories")
    assert CHECKPOINT["provenance"]["grant_id"] == "GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V3"


def test_r8_the_earlier_records_are_untouched_and_nothing_names_a_model_or_a_person():
    index = hr.load_index(ROOT)["records"]
    for name in ("PHASE3_COMMON_TONE_PROBES.json", "PHASE3_FRF_TONE_V1_CANDIDATE.json", "PHASE3_COMMON_TONE_V1_MULTIFAMILY_REVIEW_SET.json", "PHASE3_HUMAN_COMMON_TONE_MULTIFAMILY_REVIEW.json",
                 "COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1.json", "COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1_RATIFICATION.json", "PHASE3_COMMON_TONE_RATIFICATION_CHECKPOINT.json",
                 "GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1.json"):
        assert hr.file_sha256(REV / name) == index[name]["file_sha256"], name
    paths = [path for path in (tt.PROBES_PATH, tt.NEGATIVE_CONTROL_PATH, tt.CHECKPOINT_PATH) if path.exists()]
    rows = [_row(f"FD-P3-{index}") for index in range(273, 277) if f"| FD-P3-{index} |" in COLA]
    text = "\n".join([DOC, DEBT[DEBT.index("## TD-158"):]] + rows + [path.read_text(encoding="utf-8") for path in paths]).lower()
    for forbidden in ("sonnet", "opus", "haiku", "fable", "claude-", "gpt-", "gemini"):
        assert forbidden not in text, forbidden
    assert not re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text)
