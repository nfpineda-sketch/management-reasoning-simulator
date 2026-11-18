"""P3-419 to P3-423 (records): the decisions, the debt, the document, CLAUDE.md and the sealed checkpoint of the common-tone ratification say the same thing.

These tests read the documents and the checkpoint, which are the second commit of the publication; the tests of the records themselves (test_phase3_tone_ratification.py) do not depend on them.
"""
import json
import re
from pathlib import Path

import historical_records as hr

ROOT = Path(__file__).resolve().parent
REV = ROOT / "docs" / "revision"
HUMAN_NAME = "PHASE3_HUMAN_COMMON_TONE_MULTIFAMILY_REVIEW.json"
SNAPSHOT_NAME = "COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1.json"
RATIFICATION_NAME = "COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1_RATIFICATION.json"
CHECKPOINT_NAME = "PHASE3_COMMON_TONE_RATIFICATION_CHECKPOINT.json"


def _load(name: str) -> dict:
    return json.loads((REV / name).read_text(encoding="utf-8"))


def _read(*parts: str) -> str:
    return (ROOT.joinpath(*parts)).read_text(encoding="utf-8")


HUMAN, SNAPSHOT, RATIFICATION, CHECKPOINT = (_load(name) for name in (HUMAN_NAME, SNAPSHOT_NAME, RATIFICATION_NAME, CHECKPOINT_NAME))
DOC = _read("docs", "PHASE3_COMMON_TONE_RATIFICATION.md")
COLA = _read("docs", "COLA_DECISIONES_AI_ADVISOR.md")
DEBT = _read("docs", "REGISTRO_DEUDA_TECNICA.md")
CLAUDE = _read("CLAUDE.md")


def _row(table: str, row_id: str) -> str:
    rows = [line for line in table.split("\n") if line.startswith(f"| {row_id} |")]
    assert len(rows) == 1, row_id
    return rows[0]


def test_r1_the_decisions_the_debt_the_document_and_claude_md_say_the_same_thing():
    for index in range(1, 10):
        assert f"| FD-TONE-RATIFY-0{index} |" in COLA
    for index in range(269, 273):
        assert f"| FD-P3-{index} |" in COLA
    first = _row(COLA, "FD-TONE-RATIFY-01")
    for text in ("`ACCEPT` 1", "`ACCEPT_WITH_LIMITATION` 3", "`RECALIBRATE` 0", "`REJECT` 1", "HUMAN_FACULTY_REVIEW_REPORTED_NOT_STORE_VERIFIED", "no** reajustar `T`", "**no** es fallo del mecanismo común de tono"):
        assert text in first, text
    third = _row(COLA, "FD-TONE-RATIFY-03")
    for text in ("COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1", "0,6", "10,0", "1,5", "2,5", "copiado y no recalculado", "**No** es calibración clínica"):
        assert text in third, text
    for row_id, text in {"FD-TONE-RATIFY-04": "TEST_WITNESS_ONLY", "FD-TONE-RATIFY-05": "COMMON_TONE_PUMP_DEPENDENCE_NOT_YET_VALIDATED", "FD-TONE-RATIFY-06": "INAPPROPRIATE_INTERVENTION_CONTEXT",
                         "FD-TONE-RATIFY-07": "CONSCIOUSNESS_UNDER_TONE_UNRESOLVED", "FD-TONE-RATIFY-08": "NOREPINEPHRINE_TITRATION_AND_STOP_SEMANTICS", "FD-TONE-RATIFY-09": "Alto duro"}.items():
        assert text in _row(COLA, row_id), row_id
    assert "**No se implementa**" in _row(COLA, "FD-TONE-RATIFY-08") and "ni se autoriza su inicio" in _row(COLA, "FD-TONE-RATIFY-08")
    for row_id in ("FD-P3-269", "FD-P3-270", "FD-P3-271", "FD-P3-272"):
        assert len(_row(COLA, row_id)) > 200, row_id
    assert "COMMON_TONE_DEVELOPMENT_SNAPSHOT_RATIFIED" in _row(COLA, "FD-P3-272") and "docs/revision/PHASE3_COMMON_TONE_RATIFICATION_CHECKPOINT.json" in _row(COLA, "FD-P3-272")
    assert "## TD-157" in DEBT
    section = DEBT[DEBT.index("## TD-157"):]
    for text in ("reportado, no verificado contra el almacén persistido", "nada ejecutable lee", "chosen_witness: null", "COMMON_TONE_PUMP_DEPENDENCE_NOT_YET_VALIDATED", "CONSCIOUSNESS_UNDER_TONE_UNRESOLVED",
                 "NOREPINEPHRINE_TITRATION_AND_STOP_SEMANTICS", "**No autorizado.**", "INAPPROPRIATE_INTERVENTION_CONTEXT", "Sin firma", "No es validación clínica"):
        assert text in section, text
    for text in ("docs/PHASE3_COMMON_TONE_RATIFICATION.md", "FD-TONE-RATIFY-01 a FD-TONE-RATIFY-09", "FD-P3-269 a FD-P3-272", "`TD-157`", "COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1", "reportada, no verificada contra el almacén persistido",
                 "NOREPINEPHRINE_TITRATION_AND_STOP_SEMANTICS", "contexto de intervención inapropiado"):
        assert text in CLAUDE, text
    assert CLAUDE.count("FD-P3-265 a FD-P3-268 y `TD-156`;") == 1, "the new clause continues the tone-review clause: it does not replace it"


def test_r2_the_older_statements_that_the_ratification_supersedes_are_marked_and_not_edited():
    for text in ("La revisión humana no se hizo", "ningún testigo está elegido", "FR-F es un candidato sin veredicto"):
        assert text in DEBT, text
    assert DEBT.count("[2026-11-18, ratificación") == 3 and "`TD-157`" in DEBT
    for name in ("PHASE3_COMMON_TONE_FACULTY_REVIEW.md", "PHASE3_COMMON_VASCULAR_TONE.md"):
        text = _read("docs", name)
        assert "Nota 2026-11-18 (ratificación)" in text and "PHASE3_COMMON_TONE_RATIFICATION.md" in text and "no se editan" in text, name
    assert "FR-F recibió el veredicto humano `ACCEPT_WITH_LIMITATION`" in CLAUDE and "sin veredicto" in CLAUDE, "the older statement is marked, not removed"


def test_r3_the_document_states_the_binding_the_digests_the_provenance_and_what_is_not_done():
    for text in ("COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1", "HUMAN_FACULTY_REVIEW_REPORTED_NOT_STORE_VERIFIED", "NONE_REPORTED", "TEST_WITNESS_ONLY", "INAPPROPRIATE_INTERVENTION_CONTEXT", "NEGATIVE_CONTROL_CANDIDATE",
                 "MONITORED_DEVELOPMENT_LIMITATION", "OPEN_DEVELOPMENT_LIMITATION", "NEXT_HIGH_PRIORITY_MANAGEMENT_GAP", "NOREPINEPHRINE_TITRATION_AND_STOP_SEMANTICS", "COMMON_TONE_DEVELOPMENT_SNAPSHOT_RATIFIED",
                 "registro que nada ejecutable lee", "sin implementar", "1,192661", "28,9 mmHg", "`chosen_witness: null`"):
        assert text.lower() in DOC.lower(), text
    assert re.search(r"`tone_gain` \| 0,6 \|", DOC) and re.search(r"`half_effect_rate_mcg_min` \| 10,0 \|", DOC) and re.search(r"`onset_tau_min` \| 1,5 \|", DOC) and re.search(r"`offset_tau_min` \| 2,5 \|", DOC)
    for record in (HUMAN, SNAPSHOT, RATIFICATION):
        assert record["record_digest"] in DOC, record["provenance"]["record_id"]
    for letter, name in CHECKPOINT["verdicts"].items():
        assert name in DOC, letter
    assert DOC.count("**A · `COMMON_TONE_DEVELOPMENT_SNAPSHOT_RATIFIED`**") == 1
    for text in ("Sin recalibración del tono", "sin modificación del acoplamiento con la poscarga", "`LOW`/`HIGH` sin promover", "sin ampliación de autoridad", "sin despliegue a residentes", "sin afirmación de validación clínica"):
        assert text.lower() in DOC.lower(), text


def test_r4_the_checkpoint_is_a_sealed_versioned_indexed_record_with_verdict_a_and_the_facts_of_the_records():
    assert hr.record_problems(CHECKPOINT) == [] and CHECKPOINT["provenance"]["record_id"] == "COMMON_TONE_RATIFICATION_CHECKPOINT_V1" and CHECKPOINT["provenance"]["generated_on"] == "2026-11-18"
    entry = hr.load_index(ROOT)["records"][CHECKPOINT_NAME]
    assert entry["class"] == hr.VERSIONED and entry["record_digest"] == CHECKPOINT["record_digest"] and entry["file_sha256"] == hr.file_sha256(REV / CHECKPOINT_NAME) and hr.index_problems(ROOT) == []
    assert CHECKPOINT["verdict"] == "A" and CHECKPOINT["verdict_name"] == "COMMON_TONE_DEVELOPMENT_SNAPSHOT_RATIFIED"
    assert list(CHECKPOINT["verdicts"]) == ["A", "B", "C", "D", "E"] and set(CHECKPOINT["why_not_the_others"]) == {"B", "C", "D", "E"}
    facts = CHECKPOINT["facts"]
    assert (facts["human_record_digest"], facts["snapshot_record_digest"], facts["ratification_record_digest"]) == (HUMAN["record_digest"], SNAPSHOT["record_digest"], RATIFICATION["record_digest"])
    assert facts["snapshot_id"] == "COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1" and facts["overall_counts"] == {"ACCEPT": 1, "ACCEPT_WITH_LIMITATION": 3, "RECALIBRATE": 0, "REJECT": 1}
    assert facts["binding"] == SNAPSHOT["binding"] and facts["witnesses"] == {"CENTER_REFERENCE": "COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1", "LOW": "TEST_WITNESS_ONLY", "HIGH": "TEST_WITNESS_ONLY"}
    assert facts["mechanism_failures"] == [] and facts["classification"]["PULM-EDEMA"] == "INAPPROPRIATE_INTERVENTION_CONTEXT"
    assert facts["limitations"] == {"COMMON_TONE_PUMP_DEPENDENCE_NOT_YET_VALIDATED": "MONITORED_DEVELOPMENT_LIMITATION", "CONSCIOUSNESS_UNDER_TONE_UNRESOLVED": "OPEN_DEVELOPMENT_LIMITATION",
                                    "TITRATION_AND_STOP_NOT_SUPPORTED": "NEXT_HIGH_PRIORITY_MANAGEMENT_GAP"} and facts["next_management_priority"] == "NOREPINEPHRINE_TITRATION_AND_STOP_SEMANTICS"


def test_r5_the_checkpoint_confirmations_are_the_ones_the_assignment_asks_for_and_the_certification_is_focused_and_honest():
    confirmations = CHECKPOINT["confirmations"]
    for key in ("no_tone_recalibration", "no_pump_coupling_modification", "no_authority_expansion", "no_gi_recalibration", "no_source_control_change", "no_consciousness_authority", "no_terminal_authority",
                "no_resident_deployment", "no_clinical_validation_claim", "snapshot_is_a_record_nothing_executable_reads", "titration_and_stop_not_implemented", "low_and_high_not_promoted", "center_reference_not_altered"):
        assert confirmations[key] is True, key
    assert confirmations["common_core_runtime_authority"] is False and confirmations["persisted_store_verified"] is False
    certification = CHECKPOINT["certification"]
    assert certification["scope"] == "FOCUSED" and certification["failed"] == 0 and certification["errors"] == 0 and certification["passed"] > 0
    assert certification["full_suite"].startswith("NOT_RUN") and "dependency analysis" in certification["dependency_analysis"].lower()
    assert any("not verified against the persisted store" in text for text in CHECKPOINT["limitations"])
    assert CHECKPOINT["next_human_action"].startswith("A faculty member authorizes (or not) the next management implementation")
    assert len(CHECKPOINT["open_faculty_decisions"]) == 5 and CHECKPOINT["sequence"]
    assert CHECKPOINT["provenance"]["grant_id"] == "GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V3"


def test_r6_no_model_name_no_reviewer_name_in_the_new_documents_and_rows():
    text = "\n".join([DOC, _row(COLA, "FD-TONE-RATIFY-01"), _row(COLA, "FD-P3-269"), DEBT[DEBT.index("## TD-157"):], (REV / CHECKPOINT_NAME).read_text(encoding="utf-8")]).lower()
    for forbidden in ("sonnet", "opus", "haiku", "fable", "claude-", "gpt", "gemini"):
        assert forbidden not in text, forbidden
    assert not re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text)
