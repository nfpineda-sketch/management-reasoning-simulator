"""P3-518, P3-519, P3-520 and P3-527: the stored records of the GI management-trace ratification and of the controlled development pilot's scope.

The records are built by ``test_gi_pilot_records.py`` (a tool) and written once; these tests protect them: the stored content is what the code in the tree regenerates,
by the code it names, and the human evidence carries only what the faculty reported.
"""
from __future__ import annotations

import json

import pytest

import gi_pilot as gp
import historical_records as hr
import test_gi_pilot_records as records

pytestmark = pytest.mark.ordinary_configuration


def _stored(key: str) -> dict:
    return json.loads(records.PATHS[key].read_text(encoding="utf-8"))


#: The sha256 of gi_pilot.py when the three records were generated (published at cc1d3af, unchanged at e2f05c2).
GI_PILOT_AT_GENERATION = "d8fc5ec976e3e08d1817143bcc07e18bd55cef18658f4d6668a2fca919a4e0fe"


@pytest.fixture(scope="module")
def regenerated():
    # DECLARED ADAPTATION (P3-534 to P3-555): the records are chained (each names the digest of the one before), and a digest covers its provenance, so they reproduce
    # byte for byte only with the generating code they were made with: today's tree with gi_pilot.py as it was at their generation.
    today = records.generating_code
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(records, "generating_code", lambda: {**today(), "gi_pilot.py": GI_PILOT_AT_GENERATION})
        return records.reproduce()


@pytest.mark.parametrize("key", sorted(records.PATHS))
def test_r1_each_record_is_sealed_indexed_and_regenerated_by_the_code_it_names(key, regenerated):
    stored = _stored(key)
    assert hr.record_problems(stored) == []
    # DECLARED ADAPTATION (P3-534 to P3-555, FD-FINALPILOT-01 to 10): the three records were generated with gi_pilot.py as published at cc1d3af (sha256 pinned below). The final
    # pre-pilot cycle changed gi_pilot.py (clarification no-op wording, the structural boundary); the records are NOT regenerated (FD-RECORD: a generated record is immutable),
    # their content still reproduces from today's SCOPE (asserted next), and the rest of their generating code is the code in the tree.
    assert hr.same_generating_code(stored, {**records.generating_code(), "gi_pilot.py": GI_PILOT_AT_GENERATION}), f"{key}: the stored record names the generating code it was made with"
    assert {name: value for name, value in stored.items() if name not in ("provenance", "record_digest")} == json.loads(json.dumps(regenerated[key]))
    entry = hr.load_index()["records"][records.PATHS[key].name]
    assert entry == hr.index_entry(records.PATHS[key], hr.VERSIONED)


def test_r2_the_human_evidence_carries_only_what_was_reported():
    human = _stored("human")
    assert human["evidence_class"] == "HUMAN_FACULTY_REVIEW"
    assert human["provenance_of_the_evidence"]["verification"] == "HUMAN_FACULTY_REVIEW_REPORTED_NOT_STORE_VERIFIED"
    assert human["provenance_of_the_evidence"]["reviewer_name"] is None and human["provenance_of_the_evidence"]["reviewer_identity_recorded"] is False
    assert human["overall_counts"] == {"ACCEPT": 0, "ACCEPT_WITH_LIMITATION": 10, "RECALIBRATE": 0, "REJECT": 0} == human["overall_counts_recomputed_from_the_scenarios"]
    assert [item["scenario_id"] for item in human["scenarios"]] == [f"MT-{path}" for path in "ABCDEFGHIJ"]
    for item in human["scenarios"]:
        assert item["first_pass_answers_Q1_to_Q5"] == "NOT_REPORTED" and item["management_meaning_Q6"] == "NOT_REPORTED", "no answer was invented"
        assert item["overall"] == "ACCEPT_WITH_LIMITATION" and item["recalibration_requested"] is False
    assert len(human["reported_findings"]) == 7
    text = json.dumps(human)
    for invented in ("timestamp\":", "submitted_at", "locked_at"):
        assert invented not in text, "no event or time that was not reported"


def test_r3_the_ratification_is_for_pilot_preparation_only_and_the_meanings_are_faculty_interpretations():
    ratification = _stored("ratification")
    assert ratification["status"] == gp.RATIFIED_STATUS == "RATIFIED_FOR_CONTROLLED_DEVELOPMENT_PILOT_PREPARATION"
    assert {"clinical validation", "production approval", "resident deployment"} <= set(ratification["is_not"])
    assert sorted(ratification["faculty_decisions"]) == [f"FD-PILOT-0{n}" for n in range(1, 9)]
    meanings = ratification["management_meanings"]
    assert meanings["status"] == "FACULTY_INTERPRETATIONS" and meanings["converted_into_scores"] is False and meanings["hard_coded_as_correctness_labels"] is False
    assert meanings["shown_to_participants"] is False
    assert ratification["open_findings"]["H1"]["status"] == ratification["open_findings"]["H2"]["status"] == "OPEN"
    assert ratification["authority"] == {"common_core_runtime_authority": False, "expanded": False, "grant_changed": False, "snapshot_changed": False}
    assert ratification["physiology_change"] is ratification["calibration_change"] is ratification["scoring_change"] is False
    assert ratification["human_record"]["record_digest"] == _stored("human")["record_digest"]


def test_r4_the_scope_record_is_the_code_the_pilot_executes_and_does_not_start_it():
    scope = _stored("scope")
    assert scope["scope"] == json.loads(json.dumps(gp.plain(gp.SCOPE)))
    assert [row["field"] for row in scope["visible_field_classes"]] == [field for field, _cls, _how in gp.FIELD_CLASSES]
    assert [row["situation"] for row in scope["fail_safe"]] == [situation for situation, _b, _e in gp.FAIL_SAFE]
    assert scope["case_selection"]["pilot_cases"] == list(gp.PILOT_CASES) == ["gi_bleed_57m"]
    assert scope["configuration"]["default"] == "OFF" and scope["configuration"]["fails_closed"] is True
    assert scope["isolation_from_scoring"]["account_attempt_created"] is False
    assert scope["starting_the_real_pilot"].startswith("NOT authorized")
    assert scope["ratification"]["record_digest"] == _stored("ratification")["record_digest"]


def test_r5_the_decisions_the_debt_the_document_and_claude_md_say_the_same_thing():
    root = records.ROOT
    cola = (root / "docs" / "COLA_DECISIONES_AI_ADVISOR.md").read_text(encoding="utf-8")
    debt = (root / "docs" / "REGISTRO_DEUDA_TECNICA.md").read_text(encoding="utf-8")
    claude = (root / "CLAUDE.md").read_text(encoding="utf-8")
    document = (root / "docs" / "PHASE3_GI_PILOT_READINESS.md").read_text(encoding="utf-8")
    for n in range(1, 9):
        assert f"| FD-PILOT-0{n} |" in cola
    for n in (302, 303, 304):
        assert f"| FD-P3-{n} |" in cola
    assert "## TD-165 · " in debt and "MINUTE_ALREADY_COMMITTED" in debt
    assert "`docs/PHASE3_GI_PILOT_READINESS.md`, FD-PILOT-01 a FD-PILOT-08" in claude and "`TD-165`" in claude and "**el piloto real no se inició**" in claude
    assert "MINUTE_ALREADY_COMMITTED" in document and gp.RATIFIED_STATUS in document
