"""P3-238: the faculty decisions of 2026-11-12 (C1-A, C1-B, C1-C, C5) and the authorization of the first real GI development PRESSURE authority experiment, recorded.

TEST-SIDE. ``docs/revision/PHASE3_PRESSURE_AUTHORITY_DECISIONS.json`` states what the faculty answered and what it authorized. The answers are the faculty's own words
(pinned here as literals; the assistant selected none). Two things are PRESERVED UNCHANGED and a test pins them: the original evidence packet the faculty read
(copied byte for byte) and the P3-200 review record, whose ``faculty_answers`` stay ``null``: the answers are appended as decisions, never written into the earlier
evidence. ``MRS_WRITE_PRESSURE_DECISIONS=1`` regenerates the record, once, by the person who changes it.
"""
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RECORD_PATH = ROOT / "docs" / "revision" / "PHASE3_PRESSURE_AUTHORITY_DECISIONS.json"
PACKET_PATH = ROOT / "docs" / "revision" / "PHASE3_FACULTY_CONSCIOUSNESS_DIVERGENCE_PACKET.md"
REVIEW_PATH = ROOT / "docs" / "revision" / "PHASE3_GI_PREAUTHORITY_REVIEW.json"
DECISION_FILE = ROOT / "docs" / "COLA_DECISIONES_AI_ADVISOR.md"
VERSION = "P3-238"

#: The evidence the faculty read, and the earlier review record: pinned so that neither can change under the decisions that cite them.
PACKET_SHA256 = "3afe6e8a2b1338de704b43c4d2b08d1cc77853eb16e5d1219a3ccbf6669f23d5"
REVIEW_SHA256 = "3cfec3b16e83e8bcd8a67b32b1d5fcdbc2337fa703a2a37f03e88c66f44279bd"

ANSWERS = {
    "C1-A": {"answer": "ACCEPT_WITH_LIMITATION", "decision": "FD-AUTH-23",
             "meaning": "the PRE-COLLAPSE common-core GI consciousness trajectories are educationally defensible for DEVELOPMENT experimentation",
             "limitations": ["F and the consciousness thresholds are NOT recalibrated from the differences with the legacy engine",
                             "post-collapse divergence is EXCLUDED from this approval"]},
    "C1-B": {"answer": "YES_WITH_LIMITATION", "decision": "FD-AUTH-24",
             "meaning": "arrival-relative consciousness semantics remain accepted for GI development",
             "limitations": ["the legacy absolute SBP thresholds and the relative-delivery physiology answer different questions",
                             "the two GI cases suffice for development experimentation, not for population generalization",
                             "the normalization is NOT generalized to unrelated families"]},
    "C1-C": {"answer": "YES_WITH_LIMITATION", "decision": "FD-AUTH-25",
             "meaning": "the development categories NO_MATERIAL_OBSERVABLE_IMPAIRMENT, SOMNOLENT, OBTUNDED, UNRESPONSIVE are accepted for DEVELOPMENT testing only",
             "limitations": ["not clinical validation", "not GCS equivalents", "not production thresholds"]},
    "C5": {"answer": "YES_BUT_NOT_RESIDENT_VISIBLE", "decision": "FD-AUTH-26",
           "meaning": "UNRESPONSIVE_WITH_PULSE is accepted as a valid common-core physiological state",
           "limitations": ["common UNRESPONSIVE is NOT written into the legacy live mental_status field",
                           "the resident-visible mental-status field remains legacy-owned in this cycle"]},
}
FACULTY_STATUS = "READY_FOR_DEVELOPMENT_AUTHORITY_EXPERIMENT_WITH_LIVE_MENTAL_STATUS_STILL_BLOCKED"
AUTHORIZATION = {
    "decision": "FD-AUTH-28", "experiment": "THE_FIRST_REAL_GI_DEVELOPMENT_AUTHORITY_EXPERIMENT", "authority_domain": ["sbp", "dbp", "map"],
    "map": "derived from sbp and dbp, as the display derives it", "cases": ["gi_bleed_57m", "gi_bleed_72f"], "pressure_snapshot": "gi_pressure_committed",
    "overlay_snapshot": "GI_DEVELOPMENT_SNAPSHOT_V1", "overlay_status": "RATIFIED_FOR_DEVELOPMENT_EXPERIMENTS", "overlay_label": "FACULTY_ACCEPTED_FOR_DEVELOPMENT_COMPARISON",
    "scope": "DEVELOPMENT_AUTHORITY_ONLY",
    "not_authority": ["consciousness", "mental_status", "collapse", "terminal state", "pulse", "SpO2", "lactate", "other outputs"],
    "v1_used_as_pressure_calibration": False, "v1_promoted_to_general_authority": False,
}
FORBIDDEN = ("consciousness authority", "writing common consciousness into mental_status", "exposing common consciousness to residents", "approving V1 for consciousness authority",
             "deploying to residents", "modifying the frozen first pilot", "authorizing production use", "inventing terminal semantics", "retuning physiology",
             "adding opioid consciousness", "claiming clinical validation")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_record() -> dict:
    body = {
        "record_type": "PHASE3_PRESSURE_AUTHORITY_DECISIONS", "version": VERSION, "decided_on": "2026-11-12", "decision_file_row": "FD-P3-203",
        "faculty_answers": {key: dict(value) for key, value in ANSWERS.items()}, "conceptual_faculty_status": FACULTY_STATUS,
        "physiology_is_no_longer_the_blocker": True, "live_mental_status_mapping": "STILL_BLOCKED_BY_THE_NAMED_DOWNSTREAM_READERS",
        "authorization": dict(AUTHORIZATION), "forbidden_in_this_cycle": list(FORBIDDEN),
        "evidence_preserved_unchanged": {"packet": "docs/revision/PHASE3_FACULTY_CONSCIOUSNESS_DIVERGENCE_PACKET.md", "packet_sha256": PACKET_SHA256,
                                         "review_record": "docs/revision/PHASE3_GI_PREAUTHORITY_REVIEW.json", "review_record_sha256": REVIEW_SHA256,
                                         "review_faculty_answers_still_null": True},
        "assistant_selected_no_answer": True,
        "statement": "A record of the faculty's decisions. It grants no consciousness authority, does not approve V1 for authority and claims no clinical validation.",
    }
    return {**body, "record_digest": hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()}


def test_d1_the_decision_record_is_what_the_faculty_decided():
    if os.environ.get("MRS_WRITE_PRESSURE_DECISIONS") == "1":
        RECORD_PATH.write_text(json.dumps(build_record(), indent=1, sort_keys=True), encoding="utf-8")
    assert RECORD_PATH.exists(), "the record is produced once and committed"
    assert json.loads(RECORD_PATH.read_text(encoding="utf-8")) == json.loads(json.dumps(build_record())), "the committed record no longer matches: regenerate it deliberately"


def test_d2_the_answers_are_exactly_the_faculty_s():
    record = json.loads(RECORD_PATH.read_text(encoding="utf-8"))
    assert {key: value["answer"] for key, value in record["faculty_answers"].items()} == {
        "C1-A": "ACCEPT_WITH_LIMITATION", "C1-B": "YES_WITH_LIMITATION", "C1-C": "YES_WITH_LIMITATION", "C5": "YES_BUT_NOT_RESIDENT_VISIBLE"}
    assert record["conceptual_faculty_status"] == "READY_FOR_DEVELOPMENT_AUTHORITY_EXPERIMENT_WITH_LIVE_MENTAL_STATUS_STILL_BLOCKED"
    assert record["assistant_selected_no_answer"] is True and record["authorization"]["authority_domain"] == ["sbp", "dbp", "map"]
    assert record["authorization"]["v1_used_as_pressure_calibration"] is False and record["authorization"]["v1_promoted_to_general_authority"] is False
    assert any("post-collapse" in text for text in record["faculty_answers"]["C1-A"]["limitations"])
    assert any("NOT written into the legacy live mental_status" in text for text in record["faculty_answers"]["C5"]["limitations"])
    text = json.dumps(record).lower()
    for forbidden in ("clinically validated", "consciousness authority granted", "approved for authority", "production approved"):
        assert forbidden not in text, forbidden


def test_d3_the_original_evidence_is_preserved_unchanged():
    """The packet the faculty read is a byte-identical copy, and the earlier review record still has its four questions per episode UNANSWERED: the answers
    are appended as decisions, not written into the evidence."""
    assert _sha(PACKET_PATH) == PACKET_SHA256, "the evidence packet changed: it is preserved as the faculty read it"
    assert _sha(REVIEW_PATH) == REVIEW_SHA256, "the P3-200 review record changed: the faculty's answers are appended as decisions, never written into it"
    review = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))["consciousness_review"]
    assert len(review["faculty_table"]) == 9 and all(value is None for row in review["faculty_table"] for value in row["faculty_answers"].values())


def test_d4_the_decision_file_carries_the_decisions():
    text = DECISION_FILE.read_text(encoding="utf-8")
    row = next(line for line in text.splitlines() if line.startswith("| FD-P3-203 |"))
    for needle in ("ACCEPT_WITH_LIMITATION", "YES_WITH_LIMITATION", "YES_BUT_NOT_RESIDENT_VISIBLE", "READY_FOR_DEVELOPMENT_AUTHORITY_EXPERIMENT_WITH_LIVE_MENTAL_STATUS_STILL_BLOCKED",
                   "sólo para PRESIÓN", "gi_bleed_57m", "gi_bleed_72f", "gi_pressure_committed", "no** se promueve ni se usa como calibración de presión",
                   "FACULTY_ACCEPTED_FOR_DEVELOPMENT_COMPARISON", "no** se escribe en el `mental_status` vivo"):
        assert needle in row, needle
    for number in range(23, 32):
        assert f"({number}" in row or f"{number})" in row, number
