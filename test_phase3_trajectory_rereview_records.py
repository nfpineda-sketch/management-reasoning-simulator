"""P3-361 (records): the decisions, the debt entry, the document, the reviewer's instructions and the checkpoint of the interactive re-review say the same thing, and the instructions name no configuration.

These tests read the documents and the sealed records, which are the third commit of the publication; the tests of the code (``test_phase3_trajectory_rereview*.py``) do not depend on them.
"""
import json
from pathlib import Path

import faculty_trajectory_review as ftr
import faculty_trajectory_rereview as rr

ROOT = Path(__file__).resolve().parent
CANDIDATES = json.loads(rr.CANDIDATE_SET_PATH.read_text(encoding="utf-8"))
LOADED = rr.load_set()


def test_r15_the_decisions_the_debt_the_document_the_kit_and_the_checkpoint_say_the_same_thing():
    cola = (ROOT / "docs" / "COLA_DECISIONES_AI_ADVISOR.md").read_text(encoding="utf-8")
    for index in range(1, 11):
        assert f"| FD-REREVIEW-{index:02d} |" in cola
    for index in range(240, 246):
        assert f"| FD-P3-{index} |" in cola
    assert "c30ab7f1" in cola and "PENDIENTE DE CONFIRMACIÓN DOCENTE" in cola and "A single order **that** spans" in cola
    debt = (ROOT / "docs" / "REGISTRO_DEUDA_TECNICA.md").read_text(encoding="utf-8")
    assert "## TD-151" in debt and "superado en parte por `TD-151`" in debt and "El ciego es de procedimiento" in debt
    claude = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    assert "docs/PHASE3_FACULTY_REREVIEW_INTERACTIVE.md" in claude and "FD-REREVIEW-01 a FD-REREVIEW-10" in claude and "FD-P3-240 a FD-P3-245" in claude and "`TD-151`" in claude
    doc = (ROOT / "docs" / "PHASE3_FACULTY_REREVIEW_INTERACTIVE.md").read_text(encoding="utf-8")
    assert rr.PINNED_SET_DIGEST in doc and "RE-REVIEW COMPLETE · 4 / 4" in doc and "La **persona revisora no ha hecho** la re-revisión" in doc
    checkpoint = json.loads((ROOT / "docs" / "revision" / "PHASE3_FACULTY_REREVIEW_CHECKPOINT.json").read_text(encoding="utf-8"))
    rest = {key: value for key, value in checkpoint.items() if key != "record_digest"}
    assert checkpoint["record_digest"] == ftr._digest(rest)
    assert checkpoint["overall"] == {"verdict": "A", "name": "INTERACTIVE_JOINT_REREVIEW_READY_FOR_HUMAN_USE"} and checkpoint["blocker"] is None
    pins = checkpoint["pinned_records"]
    assert pins["rereview_set_digest"] == rr.PINNED_SET_DIGEST == LOADED["digest"]
    assert pins["candidate_review_set_digest"] == CANDIDATES["record_digest"] == LOADED["audit"]["candidate_review_set_digest"]
    assert pins["blind_key_digest"] == json.loads(rr.BLIND_KEY_PATH.read_text(encoding="utf-8"))["record_digest"] == LOADED["audit"]["blind_key_digest"]
    assert pins["first_review_set_digest"] == ftr.PINNED_SET_DIGEST and pins["human_review_record_digest"] == "9ba80fa70d3b38e178caa3aca9432f9227ce6d9591a48c9908c3f5ac4cc6c8d3"
    assert pins["active_core_digest"] == "a0af7d08fec3aaf93606b5635cad9f26980428a5ab8d8f66afb1317bb4586ce2"
    assert pins["joint_region_checkpoint_digest"] == json.loads((ROOT / "docs" / "revision" / "PHASE3_JOINT_REGION_CHECKPOINT.json").read_text(encoding="utf-8"))["record_digest"]
    assert all(checkpoint["confirmations"].values()) and checkpoint["statuses"]["HUMAN_RE_REVIEW"] == "NOT_DONE" and checkpoint["review_interface"]["stores"]["first_review_directories_touched"] is False
    assert checkpoint["publication"]["force_push"] is False and checkpoint["publication"]["pull_request"] is False
    # the reviewer's page for the screen and the kit's new file name the same buttons the page draws
    reviewer = (ROOT / "faculty_review_kit" / "12_rerevision_interactiva.md").read_text(encoding="utf-8")
    for label in ("LOCK FIRST IMPRESSION", "SUBMIT & NEXT", "SUBMIT & FINISH", "RE-REVIEW COMPLETE · 4 / 4", "What you are judging"):
        assert label in reviewer, label
    assert "12_rerevision_interactiva.md" in (ROOT / "faculty_review_kit" / "README.md").read_text(encoding="utf-8")


def test_r16_the_reviewers_instructions_name_no_configuration_no_other_set_and_no_comparator():
    reviewer = (ROOT / "faculty_review_kit" / "12_rerevision_interactiva.md").read_text(encoding="utf-8")
    for token in ("CENTER_REFERENCE", "CONJUNTO", "conjunto_", "LOW", "HIGH", "candidato", "testigo", "región conjunta", "tasa de sangrado", "kernel", "legacy", "Legacy", "otros conjuntos", "otro conjunto", "conjuntos de trayectorias"):
        assert token not in reviewer, token
    assert "no** se transfieren" in reviewer and "No ves" in reviewer
    # the blinded first pass shows no heart rate and no capillary refill (FD-REREVIEW-23): the page says so and does not offer them as context
    assert "no muestra la frecuencia cardíaca ni el relleno capilar" in reviewer and "como contexto" not in reviewer


def test_r17_the_blindness_patch_is_recorded_the_same_way_everywhere():
    """FD-REREVIEW-21 to 24: the hold on the other modes, the pressure-only blind page, FR-G's wording kept and the sealed successor checkpoint."""
    cola = (ROOT / "docs" / "COLA_DECISIONES_AI_ADVISOR.md").read_text(encoding="utf-8")
    for index in range(21, 25):
        assert f"| FD-REREVIEW-{index:02d} |" in cola
    assert "| FD-P3-246 |" in cola and "| FD-P3-247 |" in cola and "MRS_FACULTY_REREVIEW_GATE" in cola
    assert "Superada en parte por FD-REREVIEW-23" in cola and "Confirmada por FD-REREVIEW-22" in cola
    debt = (ROOT / "docs" / "REGISTRO_DEUDA_TECNICA.md").read_text(encoding="utf-8")
    assert "Interruptor del operador nuevo" in debt and "resuelto el 2026-11-16 por FD-REREVIEW-21" in debt and "Resuelto el 2026-11-16 por FD-REREVIEW-23" in debt
    claude = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    assert "FD-REREVIEW-21 a FD-REREVIEW-24" in claude and "FD-P3-246" in claude and "no muestra la FC ni el relleno capilar" in claude
    doc = (ROOT / "docs" / "PHASE3_FACULTY_REREVIEW_INTERACTIVE.md").read_text(encoding="utf-8")
    assert "## 14 · Parche de ciego" in doc and "NOT_REACHABLE" in doc and "ALREADY_VALID_ON_EQUIVALENT_CODE" in doc and "MRS_FACULTY_REREVIEW_GATE=off" in doc
    assert "Resuelto por FD-REREVIEW-24" in doc
    operator = (ROOT / "faculty_review_kit" / "02_preparacion_operador.md").read_text(encoding="utf-8")
    assert "MRS_FACULTY_REREVIEW_GATE" in operator and "No pongas" in operator
    first_review = (ROOT / "faculty_review_kit" / "11_revision_de_trayectorias.md").read_text(encoding="utf-8")
    assert "no ofrece esta primera revisión" in first_review
    checkpoint = json.loads((ROOT / "docs" / "revision" / "PHASE3_FACULTY_REREVIEW_BLINDNESS_PATCH_CHECKPOINT.json").read_text(encoding="utf-8"))
    rest = {key: value for key, value in checkpoint.items() if key != "record_digest"}
    assert checkpoint["record_digest"] == ftr._digest(rest)
    assert checkpoint["overall"] == {"verdict": "A", "name": "BLINDED_REREVIEW_READY_FOR_HUMAN_USE"} and checkpoint["blocker"] is None
    previous = json.loads((ROOT / "docs" / "revision" / "PHASE3_FACULTY_REREVIEW_CHECKPOINT.json").read_text(encoding="utf-8"))
    pins = checkpoint["pinned_records"]
    assert pins["previous_checkpoint_digest"] == previous["record_digest"]
    assert pins["rereview_set_digest"] == rr.PINNED_SET_DIGEST == LOADED["digest"], "the stored set did not change"
    assert pins["candidate_review_set_digest"] == CANDIDATES["record_digest"]
    assert pins["active_core_digest"] == "a0af7d08fec3aaf93606b5635cad9f26980428a5ab8d8f66afb1317bb4586ce2"
    assert {key: value for key, value in pins.items() if key != "previous_checkpoint_digest"} == previous["pinned_records"]
    assert all(checkpoint["confirmations"].values()) and checkpoint["statuses"]["HUMAN_RE_REVIEW"] == "NOT_DONE"
    assert checkpoint["blind_first_pass_display"]["not_shown"] == ["heart rate", "capillary refill"] and checkpoint["blind_first_pass_display"]["stored_set_unchanged"] is True
    assert checkpoint["gating"]["operator_switch"]["name"] == "MRS_FACULTY_REREVIEW_GATE" and checkpoint["gating"]["not_a_global_disable"] is True
    assert checkpoint["expensive_checks"]["UNKNOWN"] == [] and checkpoint["review_interface"]["stores"]["first_review_directories_touched"] is False
    assert checkpoint["publication"]["force_push"] is False and checkpoint["publication"]["pull_request"] is False
