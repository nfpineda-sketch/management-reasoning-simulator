"""P3-372 to P3-374 (records): the decisions, the debt, the document, CLAUDE.md and the sealed closure checkpoint of the GI joint-region ratification say the same thing.

These tests read the documents and the checkpoint, which are the second commit of the publication; the tests of the records themselves (test_phase3_joint_region_ratification.py) do not depend on them.
"""
import hashlib
import json
from pathlib import Path

import faculty_trajectory_review as ftr
import faculty_trajectory_rereview as rr

ROOT = Path(__file__).resolve().parent
REV = ROOT / "docs" / "revision"
FIRST_REVIEW_RECORD_DIGEST = "9ba80fa70d3b38e178caa3aca9432f9227ce6d9591a48c9908c3f5ac4cc6c8d3"
CENTER_BINDING = {"arrival_position": 0.5, "bleed_rate_ml_eq_per_min": 8.970853509, "c_rate_over_scale_per_min": 0.003326066,
                  "crystalloid_kernel": {"e": 0.213115961, "s": 0.835, "tau_min": 60.624}, "preload_scale_ml_eq": 2697.136369656}


def _load(name: str) -> dict:
    return json.loads((REV / name).read_text(encoding="utf-8"))


def _sha(name: str) -> str:
    return hashlib.sha256((REV / name).read_bytes()).hexdigest()


def _sealed(record: dict) -> bool:
    return record["record_digest"] == ftr._digest({key: value for key, value in record.items() if key != "record_digest"})


HUMAN = _load("PHASE3_HUMAN_FACULTY_REREVIEW.json")
LIMITATION = _load("GI_BLOOD_RESUSCITATION_LOW_END_RESPONSE.json")
SNAPSHOT = _load("GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1.json")
RATIFICATION = _load("GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1_RATIFICATION.json")
REGION = _load("PHASE3_GI_JOINT_REGION_V1.json")


# ---------------------------------------------------------------------------------------------------------------------------------------- P3-372 / P3-374 · the documents and the checkpoint say the same thing
def test_r1_the_decisions_the_debt_the_document_claude_md_and_the_checkpoint_say_the_same_thing():
    cola = (ROOT / "docs" / "COLA_DECISIONES_AI_ADVISOR.md").read_text(encoding="utf-8")
    for index in range(1, 8):
        assert f"| FD-RATIFY-0{index} |" in cola
    for index in range(248, 252):
        assert f"| FD-P3-{index} |" in cola
    for text in ("GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1", "GI_BLOOD_RESUSCITATION_LOW_END_RESPONSE", "GI_PRESSURE_DEVELOPMENT_CALIBRATION_CLOSED", "REPORTED_NOT_VERIFIED_AGAINST_PERSISTED_STORE", "vía común de tono vascular / vasopresor", "nada ejecutable la lee"):
        assert text in cola, text
    debt = (ROOT / "docs" / "REGISTRO_DEUDA_TECNICA.md").read_text(encoding="utf-8")
    assert "## TD-152" in debt and "reportado, no verificado contra el almacén persistido" in debt and "no está vinculada a la autoridad viva" in debt and "`TD-152`, ítem 6" in debt
    assert "reportada como completada" in debt, "the notes that mark the older 'not done' statements as superseded"
    claude = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    for text in ("docs/PHASE3_GI_JOINT_REGION_RATIFICATION.md", "FD-RATIFY-01 a FD-RATIFY-07", "FD-P3-248 a FD-P3-251", "`TD-152`", "GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1", "reportado, no verificado contra el almacén persistido"):
        assert text in claude, text
    doc = (ROOT / "docs" / "PHASE3_GI_JOINT_REGION_RATIFICATION.md").read_text(encoding="utf-8")
    for text in ("REPORTED_NOT_VERIFIED_AGAINST_PERSISTED_STORE", "GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1", "8,970853509", "2697,136369656", "0,003326066", "TEST_WITNESS_ONLY", "NOT_REACHABLE", "ALREADY_VALID_ON_EQUIVALENT_CODE",
                 "no está vinculada", "GI_PRESSURE_DEVELOPMENT_CALIBRATION_CLOSED"):
        assert text in doc, text
    assert "vía común de tono vascular / vasopresor" in doc.lower()
    for name in ("PHASE3_GI_JOINT_REGION.md", "PHASE3_FACULTY_REREVIEW_INTERACTIVE.md"):
        assert "2026-11-16" in (ROOT / "docs" / name).read_text(encoding="utf-8") and "PHASE3_GI_JOINT_REGION_RATIFICATION.md" in (ROOT / "docs" / name).read_text(encoding="utf-8")
    checkpoint = _load("PHASE3_GI_PRESSURE_CALIBRATION_CLOSURE_CHECKPOINT.json")
    assert _sealed(checkpoint) and checkpoint["overall"] == {"verdict": "A", "name": "GI_PRESSURE_DEVELOPMENT_REGION_RATIFIED_AND_CLOSED"} and checkpoint["blocker"] is None
    assert checkpoint["gi_pressure_status"] == "GI_PRESSURE_DEVELOPMENT_CALIBRATION_CLOSED" and checkpoint["amendment_3"] == "CLOSED"
    pins = checkpoint["pinned_records"]
    assert pins["human_record_digest"] == HUMAN["record_digest"] and pins["human_record_file_sha256"] == _sha("PHASE3_HUMAN_FACULTY_REREVIEW.json")
    assert pins["snapshot_record_digest"] == SNAPSHOT["record_digest"] and pins["snapshot_file_sha256"] == _sha("GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1.json")
    assert pins["ratification_record_digest"] == RATIFICATION["record_digest"] and pins["limitation_record_digest"] == LIMITATION["record_digest"]
    assert pins["region_record_digest"] == REGION["record_digest"] and pins["region_record_file_sha256"] == _sha("PHASE3_GI_JOINT_REGION_V1.json")
    assert pins["rereview_set_digest"] == rr.PINNED_SET_DIGEST and pins["first_review_record_digest"] == FIRST_REVIEW_RECORD_DIGEST and pins["first_review_record_file_sha256"] == _sha("PHASE3_FIRST_HUMAN_FACULTY_REVIEW.json")
    assert pins["previous_checkpoint_digest"] == _load("PHASE3_FACULTY_REREVIEW_BLINDNESS_PATCH_CHECKPOINT.json")["record_digest"]
    assert pins["active_core_digest"] == "a0af7d08fec3aaf93606b5635cad9f26980428a5ab8d8f66afb1317bb4586ce2"
    assert checkpoint["snapshot"]["binding"] == CENTER_BINDING and checkpoint["snapshot"]["live_configuration_bound"] is False and checkpoint["snapshot"]["copied_not_recomputed"] is True
    assert checkpoint["human_rereview"]["verification"] == "REPORTED_NOT_VERIFIED_AGAINST_PERSISTED_STORE" and checkpoint["human_rereview"]["overall_counts"] == HUMAN["overall_counts"]
    assert checkpoint["witnesses"] == {"LOW": "TEST_WITNESS_ONLY", "HIGH": "TEST_WITNESS_ONLY", "CENTER_REFERENCE": "GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1"}
    assert checkpoint["limitation"]["status"] == LIMITATION["status"] and checkpoint["limitation"]["reopen_only_if"] == LIMITATION["reopen_only_if"]
    assert checkpoint["next_physiology_priority"]["implemented"] is False and checkpoint["next_physiology_priority"]["name"] == "COMMON VASCULAR TONE / VASOPRESSOR PATHWAY"
    assert all(checkpoint["confirmations"].values()) and len(checkpoint["confirmations"]) == 15
    assert checkpoint["publication"]["force_push"] is False and checkpoint["publication"]["pull_request"] is False
