"""P3-449 to P3-461 (records): the decisions, the debt, the document, CLAUDE.md and the sealed checkpoint of the manual norepinephrine ratification and the target-order repair say the same thing.

These tests read the documents and the checkpoint, which belong to the third commit of the publication; the tests of the records themselves (test_phase3_nr_ratification.py) and of the repair
(test_phase3_target_order_boundary.py) do not depend on them. The tests that need the checkpoint are skipped until the checkpoint is written (once, after the certification).
"""
import json
import re
from pathlib import Path

import pytest

import historical_records as hr

ROOT = Path(__file__).resolve().parent
REV = ROOT / "docs" / "revision"
HUMAN_NAME = "PHASE3_HUMAN_NOREPINEPHRINE_TITRATION_REVIEW.json"
CLOSURE_NAME = "NOREPINEPHRINE_MANUAL_RATE_CONTROL_DEVELOPMENT_SEMANTICS_V1.json"
CHECKPOINT_NAME = "PHASE3_NOREPINEPHRINE_TARGET_ORDER_CHECKPOINT.json"
needs_the_checkpoint = pytest.mark.skipif(not (REV / CHECKPOINT_NAME).exists(), reason="the checkpoint is written once, after the certification")


def _load(name: str) -> dict:
    return json.loads((REV / name).read_text(encoding="utf-8"))


def _read(*parts: str) -> str:
    return ROOT.joinpath(*parts).read_text(encoding="utf-8")


def _row(table: str, row_id: str) -> str:
    rows = [line for line in table.split("\n") if line.startswith(f"| {row_id} |")]
    assert len(rows) == 1, row_id
    return rows[0]


HUMAN, CLOSURE = _load(HUMAN_NAME), _load(CLOSURE_NAME)
DOC = _read("docs", "PHASE3_NOREPINEPHRINE_TARGET_ORDER_BOUNDARY.md")
COLA = _read("docs", "COLA_DECISIONES_AI_ADVISOR.md")
DEBT = _read("docs", "REGISTRO_DEUDA_TECNICA.md")
CLAUDE = _read("CLAUDE.md")


def test_r1_the_decisions_the_debt_the_document_and_claude_md_say_the_same_thing():
    for index in range(1, 8):
        assert f"| FD-NR-0{index} |" in COLA
    for index in (281, 282, 283):
        assert f"| FD-P3-{index} |" in COLA
    assert "`ACCEPT` 5" in _row(COLA, "FD-NR-01") and "HUMAN_FACULTY_REVIEW_REPORTED_NOT_STORE_VERIFIED" in _row(COLA, "FD-NR-01") and "no se inventó" in _row(COLA, "FD-NR-01")
    for row_id, text in {"FD-NR-02": "No** se reabren LOW, HIGH", "FD-NR-03": "NOREPINEPHRINE_MANUAL_RATE_CONTROL_DEVELOPMENT_SEMANTICS_CLOSED", "FD-NR-04": "mcg/kg/min", "FD-NR-05": "Resuelto por FD-P3-282",
                         "FD-NR-06": "Sin ampliación de la autoridad", "FD-NR-07": "fallando cerrado"}.items():
        assert text in _row(COLA, row_id), row_id
    second = _row(COLA, "FD-P3-282")
    for text in ("MULTIPLE_LAYERS", "order_pipeline.split_bundle", "23", "16 de los 23", "121 630", "91 508", "nitroglicerina", "congelad", "86 pruebas nuevas", "13 mutantes"):
        assert text in second, text
    third = _row(COLA, "FD-P3-283")
    for text in ("RAW_ORDER_REMAINS_CORRECT_BOUNDARY", "PERMANENT_FAIL_CLOSED", "que no se inventó", "una** prueba adaptada"):
        assert text in third, text
    assert "## TD-160" in DEBT
    section = DEBT[DEBT.index("## TD-160"):]
    for text in ("reportada, no verificada contra el almacén persistido", "nitroglicerina", "levantar el congelamiento del lector", "«restart»", "«Increase norepinephrine» sin ningún número", "`TD-46`", "veredicto A",
                 "`PERMANENT_FAIL_CLOSED`", "Sin firma", "Pruebas adaptadas, declaradas"):
        assert text in section, text
    for text in ("docs/PHASE3_NOREPINEPHRINE_TARGET_ORDER_BOUNDARY.md", "FD-NR-01 a FD-NR-07", "FD-P3-281 a FD-P3-284", "`TD-160`", "NOREPINEPHRINE_MANUAL_RATE_CONTROL_DEVELOPMENT_SEMANTICS_CLOSED", "reportada, no verificada contra el almacén persistido",
                 "único cambio ejecutable", "decisiones docentes no tomadas", "`order_pipeline.py`", "el lector, `active_order_context.py` y el motor están congelados y no se tocaron"):
        assert text in CLAUDE, text
    assert CLAUDE.count("FD-TITREV-01 a FD-TITREV-13, FD-P3-277 a FD-P3-280 y `TD-159`;") == 1, "the new clause continues the titration-review clause: it does not replace it"


def test_r2_the_older_statements_that_the_repair_supersedes_are_marked_and_not_edited():
    assert "el defecto heredado de «MAP 65» sigue sin resolver (FD-TITREV-12; `TD-158`, ítems 2 y 3)." in DEBT, "the older statement is still there"
    assert "[2026-11-20, objetivo ≠ tasa:" in DEBT and "`TD-160`" in DEBT
    for name in ("PHASE3_NOREPINEPHRINE_TITRATION.md", "PHASE3_NOREPINEPHRINE_TITRATION_REVIEW.md"):
        text = _read("docs", name)
        assert text.count("Nota 2026-11-20 (objetivo ≠ tasa)") == 1 and "PHASE3_NOREPINEPHRINE_TARGET_ORDER_BOUNDARY.md" in text and "no se edita" in text, name
    assert "*[2026-11-20: el defecto de «MAP 65» se reparó antes del motor" in CLAUDE and "sigue sin consumir las órdenes asentadas por el motor" in CLAUDE, "the older statement is marked, not removed"


def test_r3_the_document_states_the_mechanism_the_classification_the_boundary_and_what_is_not_done():
    for text in ("NOREPINEPHRINE_MANUAL_RATE_CONTROL_DEVELOPMENT_SEMANTICS_CLOSED", "HUMAN_FACULTY_REVIEW_REPORTED_NOT_STORE_VERIFIED", "OPEN_AT_RATIFICATION", "MULTIPLE_LAYERS", "order_pipeline.split_bundle",
                 "RAW_ORDER_REMAINS_CORRECT_BOUNDARY", "PERMANENT_FAIL_CLOSED", "RECOVER_ON_LATER_EXPLICIT_VALID_ABSOLUTE_ORDER", "respaldo del número suelto", "complete_active_order", "23/28", "16 de los 19", "0 de los 23", "restart",
                 "contrato nuevo del espejo compartido", "no se inventó", HUMAN_NAME, CLOSURE_NAME):
        assert text.lower() in DOC.lower(), text
    for index in range(1, 8):
        assert f"| FD-NR-0{index} |" in DOC
    for letter in "ABCDEFGHIJ":
        assert re.search(rf"\| {letter} \| ", DOC), letter


def test_r4_the_document_states_what_was_not_changed_in_the_executable_layers():
    for text in ("`family_engine.py`", "`active_order_context.py`", "`clinical_core/`", "COMMON_CORE_RUNTIME_AUTHORITY = False", "único cambio ejecutable", "`family_parser.py`", "`order_pipeline.py`", "`language.py`", "congelad"):
        assert text in DOC, text


@needs_the_checkpoint
def test_r5_the_checkpoint_is_a_sealed_versioned_indexed_record_with_one_verdict_and_the_facts_of_the_records():
    checkpoint = _load(CHECKPOINT_NAME)
    assert hr.record_problems(checkpoint) == [] and checkpoint["provenance"]["record_id"] == "NOREPINEPHRINE_TARGET_ORDER_CHECKPOINT_V1" and checkpoint["provenance"]["generated_on"] == "2026-11-20"
    entry = hr.load_index(ROOT)["records"][CHECKPOINT_NAME]
    assert entry["class"] == hr.VERSIONED and entry["record_digest"] == checkpoint["record_digest"] and entry["file_sha256"] == hr.file_sha256(REV / CHECKPOINT_NAME) and hr.index_problems(ROOT) == []
    assert list(checkpoint["verdicts"]) == ["A", "B", "C", "D", "E", "F"] and set(checkpoint["why_not_the_others"]) == set("ABCDEF") and checkpoint["verdict"] in checkpoint["verdicts"]
    assert checkpoint["verdict_name"] == checkpoint["verdicts"][checkpoint["verdict"]]
    facts = checkpoint["facts"]
    assert (facts["human_record_digest"], facts["closure_record_digest"]) == (HUMAN["record_digest"], CLOSURE["record_digest"]) and facts["closure_status"] == CLOSURE["status"]
    assert facts["overall_counts"] == {"ACCEPT": 5, "ACCEPT_WITH_LIMITATION": 0, "RECALIBRATE": 0, "REJECT": 0} and facts["failure_classification"]["name"] == "MULTIPLE_LAYERS"
    assert facts["raw_vs_resolved_verdict"]["verdict"] == "A" and facts["malformed_order_recovery"]["implemented"] is False
    assert facts["executable_files_changed"] == ["order_pipeline.py", "language.py"] and "clinical_core/" in facts["executable_files_not_changed"] and "family_parser.py" in facts["executable_files_not_changed"]
    assert facts["reader_freeze"]["reader_changed"] is False and "nitroglycerin" in facts["residual"]
    assert DOC.count(f"**{checkpoint['verdict']} · `{checkpoint['verdict_name']}`**") == 1 and "PENDIENTE" not in DOC
    for text in ("Sin recalibración del tono", "sin cambio del acoplamiento con la bomba", "sin fisiología nueva", "sin ampliación de la autoridad de norepinefrina", "sin autoridad de consciencia ni terminal",
                 "sin despliegue a residentes", "sin afirmación de validación clínica"):
        assert text.lower() in DOC.lower(), text


@needs_the_checkpoint
def test_r6_the_checkpoint_confirmations_and_the_certification_are_the_ones_the_assignment_asks_for():
    checkpoint = _load(CHECKPOINT_NAME)
    confirmations = checkpoint["confirmations"]
    for key in ("no_tone_recalibration", "no_pump_coupling_change", "no_physiology_change", "no_norepinephrine_authority_expansion", "no_consciousness_authority", "no_terminal_authority", "no_resident_deployment",
                "no_clinical_validation_claim", "no_weight_based_dosing", "no_map_target_titration", "no_new_vasopressor", "no_malformed_order_recovery_change", "no_new_shared_mirror_contract"):
        assert confirmations[key] is True, key
    assert confirmations["common_core_runtime_authority"] is False and confirmations["persisted_store_verified"] is False
    certification = checkpoint["certification"]
    assert certification["scope"] == "FULL" and certification["full_suite"]["failures"] == 0 and certification["full_suite"]["errors"] == 0 and certification["full_suite"]["valid"] is True
    assert certification["regressions"]["active_passed"] == certification["regressions"]["active_total"] and certification["regressions"]["exit_code"] == 0
    assert checkpoint["adversarial_review"]["unresolved_blocking_findings"] == [] and "| FD-P3-284 |" in COLA and "FD-P3-284" in CLAUDE


def test_r7_no_model_name_no_reviewer_name_in_the_new_documents_and_rows():
    text = "\n".join([DOC, _row(COLA, "FD-NR-01"), _row(COLA, "FD-P3-281"), DEBT[DEBT.index("## TD-160"):]]).lower()
    for forbidden in ("sonnet", "opus", "haiku", "fable", "claude-", "gpt", "gemini"):
        assert forbidden not in text, forbidden
    assert not re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text)
