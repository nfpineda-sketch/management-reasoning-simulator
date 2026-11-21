"""P3-470 and P3-483: the SUCCESSION of the order reader (faculty decisions FD-TARGET-01, 2026-11-20, and FD-ORDER-01 to FD-ORDER-11, 2026-11-21).

The faculty lifted the reader freeze twice, each time ONLY for one narrowly scoped safety correction. The reader therefore has THREE states and the Phase-2 evidence did not move: these tests prove that the reader of the
closure AND the reader of the first successor are each reconstructable byte for byte and in behavior from the live file, that every Phase-2 digest still recomputes from the closure reader WITHOUT editing ``clinical_core/``,
that the calibration freeze moved in exactly one component at each succession, that the sealed record of the first succession still regenerates to the same content, and that nothing sealed was rewritten. They also guard
the successor pin: the reader is frozen again at its current successor state.
"""
import hashlib
import json
import subprocess
from pathlib import Path

import pytest

import family_parser as fp
import historical_records as hr
import reader_succession as succession
import test_prephase1_reader_freeze as freeze
import test_reader_succession_analysis as analysis
import test_reader_succession_order_safety_analysis as analysis2
from clinical_core import amendment_1 as a1
from clinical_core import amendment_3 as a3
from clinical_core import calibration

ROOT = Path(__file__).resolve().parent
RECORD_NAME = "PHASE3_READER_SUCCESSION_TARGET_SAFETY.json"
RECORD = json.loads((ROOT / "docs" / "revision" / RECORD_NAME).read_text(encoding="utf-8")) if (ROOT / "docs" / "revision" / RECORD_NAME).exists() else None
needs_the_record = pytest.mark.skipif(RECORD is None, reason="the successor record is written once the reader is final")
RECORD2_NAME = "PHASE3_READER_SUCCESSION_ORDER_SAFETY.json"
RECORD2 = json.loads((ROOT / "docs" / "revision" / RECORD2_NAME).read_text(encoding="utf-8")) if (ROOT / "docs" / "revision" / RECORD2_NAME).exists() else None
needs_the_second_record = pytest.mark.skipif(RECORD2 is None, reason="the second successor record is written once the reader is final")


def _git_blob(path) -> str:
    return succession.git_blob(Path(path).read_bytes())


def test_v1_the_reader_of_the_closure_is_rebuilt_from_the_live_file_byte_for_byte():
    data = succession.historical_reader_bytes()
    assert succession.git_blob(data) == succession.HISTORICAL_GIT_BLOB == freeze.HISTORICAL_BLOBS["family_parser.py"] == "1d17bf8b3dce66da5f1c8291237e2e7a7afde1c0"
    assert hashlib.sha256(data).hexdigest() == succession.HISTORICAL_SHA256 and data != (ROOT / "family_parser.py").read_bytes()
    assert succession.verify() == {"live_is_the_successor": True, "target_safety_rebuilt": True, "historical_rebuilt": True, "hunks": len(succession.REVERSAL), "order_safety_hunks": len(succession.REVERSAL_ORDER_SAFETY)}
    assert hashlib.sha256((ROOT / "family_parser.py").read_bytes()).hexdigest() == succession.SUCCESSOR_SHA256 and _git_blob(ROOT / "family_parser.py") == succession.SUCCESSOR_GIT_BLOB == freeze.EXPECTED_BLOBS["family_parser.py"]


def test_v1b_the_reader_of_the_first_successor_is_rebuilt_from_the_live_file_byte_for_byte_and_is_a_reader_of_its_own():
    """P3-483: the three readers are independently reconstructable. The first successor (state 2) is rebuilt by the order-safety hunks; the closure reader (state 1) is rebuilt through it."""
    data = succession.target_safety_reader_bytes()
    assert succession.git_blob(data) == succession.TARGET_SAFETY_GIT_BLOB == freeze.TARGET_SAFETY_BLOBS["family_parser.py"] == "7a85714eb2b6fccb47507384a71fe91451e71ecb"
    assert hashlib.sha256(data).hexdigest() == succession.TARGET_SAFETY_SHA256 and data not in ((ROOT / "family_parser.py").read_bytes(), succession.historical_reader_bytes())
    assert len({succession.git_blob((ROOT / "family_parser.py").read_bytes()), succession.TARGET_SAFETY_GIT_BLOB, succession.HISTORICAL_GIT_BLOB}) == 3, "three different readers"
    first = succession.target_safety_reader_module()
    assert first.__name__ == "family_parser_target_safety" and first is not fp and first is not succession.historical_reader_module()
    assert first.parse_family_actions("titrate norepinephrine to MAP 65")["actions"][0]["type"] == "clarification", "the first successor already held the target"
    assert first.parse_family_actions("restart norepinephrine")["actions"] == [{"type": "norepinephrine", "rate": None, "units": None, "operation": "start"}], "and read a restart with no rate as the engine's own question"
    assert first.parse_family_actions("continue norepinephrine at 12")["actions"] == [{"type": "norepinephrine", "rate": None, "units": None, "operation": "continue"}], "and a number after continue as a silent continue (L-6, closed by the second succession)"
    assert fp.parse_family_actions("continue norepinephrine at 12")["actions"][0]["incomplete_explicit_rate"]["operation"] == "continue"


def test_v2_the_reversal_is_exact_or_it_refuses_a_hunk_that_is_not_unique_and_a_changed_reader():
    live = (ROOT / "family_parser.py").read_bytes()
    first = succession.target_safety_reader_bytes().decode("utf-8")
    for new, old in succession.REVERSAL_ORDER_SAFETY:
        assert new != old and live.decode("utf-8").count(new) == 1, "each order-safety hunk is unique in the LIVE reader"
    for new, old in succession.REVERSAL:
        assert new != old and first.count(new) == 1, "each target-safety hunk is unique in the FIRST successor"
    for rebuild in (succession.historical_reader_bytes, succession.target_safety_reader_bytes):
        with pytest.raises(ValueError):
            rebuild(live + b"\n# a later edit")
        with pytest.raises(ValueError):
            rebuild(live.replace(succession.REVERSAL_ORDER_SAFETY[0][0].encode("utf-8"), b"", 1))


def test_v3_the_historical_reader_still_behaves_as_it_did_and_never_replaces_the_live_one():
    import sys
    old = succession.historical_reader_module()
    assert sys.modules["family_parser"] is fp and old is not fp and old.__name__ == "family_parser_phase2_closure"
    assert old.parse_family_actions("titrate norepinephrine to MAP 65")["actions"] == [{"type": "norepinephrine", "rate": 65.0, "units": None, "operation": "adjust"}]
    assert old.parse_family_actions("titrate nitroglycerin to SBP 120")["actions"] == [{"type": "nitroglycerin", "rate_mcg_min": 120.0, "operation": "adjust"}]
    assert old.parse_family_actions("restart norepinephrine at 10 mcg/min")["actions"][0]["type"] == "clarification"
    assert old.parse_family_actions("increase norepinephrine")["actions"] == [{"type": "norepinephrine", "rate": None, "units": None, "operation": "adjust"}]
    assert fp.parse_family_actions("titrate norepinephrine to MAP 65")["actions"][0]["type"] == "clarification"


def test_v4_the_other_four_reader_files_and_every_root_dependency_of_the_freeze_are_byte_identical_to_the_v3_state():
    assert {name: _git_blob(ROOT / name) for name in freeze.EXPECTED_BLOBS if name != "family_parser.py"} == {
        "shared_order_language.py": "5ed6a8a14aa2f7cf077ffaf2a202ee9cf0bd8047", "shared_order_quantities.py": "65e3606a2fd80bc6fb1f988e48460e6b2f6f100c",
        "active_order_context.py": "3c0432f5711cfbd3a919649e1bbe52cce3afbaeb", "weight_based_doses.py": "cdf79e0e654e11f908a90eb91139c9812a2416e8"}
    assert freeze.test_prephase1_reader_freeze_is_exact() is None


def test_v5_every_phase_two_freeze_digest_recomputes_from_the_historical_reader_and_clinical_core_is_untouched():
    recorded = json.loads(a1.CLOSURE_RECORD.read_text(encoding="utf-8"))["freeze_digests"]
    from clinical_core import closure_guard as cg, decision_pack, lactate_slice, tone_domain
    with a3.closure_view():
        assert calibration.frozen_digest() != recorded["calibration"], "without the historical reader the closure digest cannot recompute: the reader moved"
        with succession.historical_reader_view():
            now = {"calibration": calibration.frozen_digest(), "closure_guard_P2X1A": cg.freeze_digest(), "tone_domain_on_the_live_tree": tone_domain.freeze_digest(),
                   "lactate_slice": lactate_slice.slice_digest(), "decision_pack": decision_pack.pack_digest()}
    assert now == recorded
    assert a3.amended_core_digest_now() == "867bac09e09bb5c04629e73fbbdec0f7e1f100da17ef8966f580ba91067a7c9c", "clinical_core/ is not edited: the lineage digest is the certified one"
    assert (ROOT / "family_parser.py").read_bytes() != succession.historical_reader_bytes() and "family_parser.py" in calibration.INPUT_PATH_SOURCES


def test_v6_the_view_is_restored_after_use_and_composes_in_either_order_with_a_monkeypatch(monkeypatch):
    before = calibration.REPOSITORY
    with succession.historical_reader_view():
        assert calibration.REPOSITORY is not before and (calibration.REPOSITORY / "family_parser.py").read_bytes() == succession.historical_reader_bytes()
        assert (calibration.REPOSITORY / "order_pipeline.py").read_bytes() == (ROOT / "order_pipeline.py").read_bytes(), "only the reader is read as of the closure"
    assert calibration.REPOSITORY is before
    succession.install(monkeypatch)
    assert (calibration.REPOSITORY / "family_parser.py").read_bytes() == succession.historical_reader_bytes()


def test_v7_the_calibration_freeze_moved_in_exactly_one_component_and_the_materialized_inputs_did_not():
    with succession.historical_reader_view():
        before = calibration.digest_components()
    now = calibration.digest_components()
    assert sorted(name for name in now if now[name] != before[name]) == ["input_path_sources"]
    assert now["scenario_inputs"] == before["scenario_inputs"], "the GI scenarios' inputs, as the engine materializes them, are identical"
    assert calibration.frozen_digest() != "c1eeb5538a4ea990cbcb4432b0c28e6cb8c351ffe08c96a6036f82d3b65a9b85", "the live freeze digest moved with the reader; the Phase-2 value is rebuilt, not lost"


def test_v8_the_reader_is_frozen_again_at_its_successor_and_the_pin_names_both_states():
    source = (ROOT / "test_prephase1_reader_freeze.py").read_text(encoding="utf-8")
    assert "HISTORICAL_BLOBS" in source and "TARGET_SAFETY_BLOBS" in source and "reader_succession" in source
    assert succession.SUCCESSOR_GIT_BLOB in source and succession.TARGET_SAFETY_GIT_BLOB in source and succession.HISTORICAL_GIT_BLOB in source


# -- the successor record -------------------------------------------------------------------------------------------------------------------------------------------------------
@needs_the_record
def test_v9_the_record_is_sealed_versioned_indexed_and_regenerates_to_the_same_content():
    assert hr.record_problems(RECORD) == [] and RECORD["provenance"]["record_id"] == analysis.RECORD_ID == "PHASE3_READER_SUCCESSION_TARGET_SAFETY_V1"
    entry = hr.load_index(ROOT)["records"][RECORD_NAME]
    assert entry["class"] == hr.VERSIONED and entry["record_digest"] == RECORD["record_digest"] and entry["file_sha256"] == hr.file_sha256(ROOT / "docs" / "revision" / RECORD_NAME) and hr.index_problems(ROOT) == []
    assert analysis.reproduce() == {key: value for key, value in RECORD.items() if key not in ("provenance", "record_digest")}


@needs_the_record
def test_v10_the_record_states_what_the_tree_recomputes_and_nothing_else():
    reader, freeze_state = RECORD["reader"], RECORD["freeze"]
    assert reader["historical"]["git_blob"] == succession.HISTORICAL_GIT_BLOB and reader["successor"]["git_blob"] == succession.TARGET_SAFETY_GIT_BLOB, "the FIRST record names the first successor, forever"
    assert RECORD["reversal"]["proven"] is True and RECORD["reversal"]["hunk_count"] == len(succession.REVERSAL) == len(RECORD["reversal"]["hunks"])
    assert [(h["successor_text"], h["historical_text"]) for h in RECORD["reversal"]["hunks"]] == [tuple(pair) for pair in succession.REVERSAL]
    assert freeze_state["calibration"]["components_that_moved"] == ["input_path_sources"] and freeze_state["calibration"]["scenario_inputs_identical"] is True
    assert freeze_state["calibration"]["before_the_succession"]["digest"] == "c1eeb5538a4ea990cbcb4432b0c28e6cb8c351ffe08c96a6036f82d3b65a9b85"
    with succession.target_safety_reader_view():
        assert freeze_state["calibration"]["after_the_succession"]["digest"] == calibration.frozen_digest(), "the first record's 'after' is the first successor's freeze, recomputed from its rebuilt reader"
    assert freeze_state["calibration"]["after_the_succession"]["digest"] != calibration.frozen_digest(), "...and it is not the live freeze of the second successor"
    assert freeze_state["closure_freeze_digests"]["equal"] is True
    assert RECORD["core_digest"] == a3.amended_core_digest_now() and RECORD["authority"] == {"common_core_runtime_authority": False, "expanded": False}
    assert RECORD["physiology_change"] is False and RECORD["tone_recalibrated"] is False and set(RECORD["faculty_decisions"]) == {f"FD-TARGET-{index:02d}" for index in range(1, 12)}


@needs_the_record
def test_v11_the_record_does_not_rewrite_any_sealed_record_and_names_the_old_and_new_behavior():
    by_text = {row["text"]: row for row in RECORD["behavior"]}
    assert by_text["titrate norepinephrine to MAP 65"]["historical_reader"][0]["rate"] == 65.0 and by_text["titrate norepinephrine to MAP 65"]["successor_reader"][0]["type"] == "clarification"
    assert by_text["norepinephrine 10 mcg/min"]["historical_reader"] == by_text["norepinephrine 10 mcg/min"]["successor_reader"]
    legacy = hr.load_index(ROOT)
    assert legacy["legacy_adopted_at"] and hr.index_problems(ROOT) == [], "the index still pins every legacy record at its adopted bytes"
    out = subprocess.run(["git", "diff", "--name-only", "HEAD", "--", "docs/revision"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    assert all(path in {"docs/revision/HISTORICAL_RECORD_INDEX.json"} or path.endswith(("PHASE3_READER_SUCCESSION_TARGET_SAFETY.json", "PHASE3_TARGET_RATE_SOURCE_CHECKPOINT.json")) for path in out), out


# -- the SECOND successor record (FD-ORDER-01 to FD-ORDER-11) -------------------------------------------------------------------------------------------------------------------
@needs_the_second_record
def test_v12_the_second_record_is_sealed_versioned_indexed_and_regenerates_to_the_same_content():
    assert hr.record_problems(RECORD2) == [] and RECORD2["provenance"]["record_id"] == analysis2.RECORD_ID == "PHASE3_READER_SUCCESSION_ORDER_SAFETY_V1" and RECORD2["supersedes"] == analysis2.SUPERSEDES
    entry = hr.load_index(ROOT)["records"][RECORD2_NAME]
    assert entry["class"] == hr.VERSIONED and entry["record_digest"] == RECORD2["record_digest"] and entry["file_sha256"] == hr.file_sha256(ROOT / "docs" / "revision" / RECORD2_NAME) and hr.index_problems(ROOT) == []
    assert analysis2.reproduce() == {key: value for key, value in RECORD2.items() if key not in ("provenance", "record_digest")}


@needs_the_second_record
def test_v13_the_second_record_names_the_three_readers_and_the_two_reversals_the_tree_recomputes():
    reader = RECORD2["reader"]
    assert (reader["phase2_closure"]["git_blob"], reader["target_safety_successor"]["git_blob"], reader["order_safety_successor"]["git_blob"]) == (
        succession.HISTORICAL_GIT_BLOB, succession.TARGET_SAFETY_GIT_BLOB, succession.SUCCESSOR_GIT_BLOB)
    assert RECORD2["reversal"]["order_safety"]["proven"] is True and RECORD2["reversal"]["target_safety"]["proven"] is True
    assert [(h["successor_text"], h["previous_text"]) for h in RECORD2["reversal"]["order_safety"]["hunks"]] == [tuple(pair) for pair in succession.REVERSAL_ORDER_SAFETY]
    assert [(h["successor_text"], h["historical_text"]) for h in RECORD2["reversal"]["target_safety"]["hunks"]] == [tuple(pair) for pair in succession.REVERSAL]


@needs_the_second_record
def test_v14_the_second_record_states_the_freeze_in_the_three_states_and_changes_nothing_else():
    state = RECORD2["freeze"]["calibration"]
    assert state["components_that_moved_in_this_succession"] == ["input_path_sources"] and state["scenario_inputs_identical"] is True
    assert state["order_safety_successor"]["digest"] == calibration.frozen_digest()
    with succession.target_safety_reader_view():
        assert state["target_safety_successor"]["digest"] == calibration.frozen_digest()
    with a3.closure_view():
        with succession.historical_reader_view():
            assert state["phase2_closure_reader"]["digest"] == calibration.frozen_digest()
    assert len({state["phase2_closure_reader"]["digest"], state["target_safety_successor"]["digest"], state["order_safety_successor"]["digest"]}) == 3
    assert RECORD2["freeze"]["closure_freeze_digests"]["equal"] is True
    assert RECORD2["core_digest"] == a3.amended_core_digest_now() and RECORD2["authority"] == {"common_core_runtime_authority": False, "expanded": False}
    assert RECORD2["physiology_change"] is False and RECORD2["tone_recalibrated"] is False and set(RECORD2["faculty_decisions"]) == {f"FD-ORDER-{index:02d}" for index in range(1, 12)}


@needs_the_second_record
def test_v15_the_second_record_shows_each_reader_side_by_side_and_rewrites_nothing_sealed():
    by_text = {row["text"]: row for row in RECORD2["behavior"]}
    row = by_text["stop NS, norepinephrine to MAP 65"]
    assert [a["type"] for a in row["target_safety_reader"] if a.get("operation") == "stop"] == ["fluid", "norepinephrine"], "the first successor stopped the infusion"
    assert [a["type"] for a in row["order_safety_reader"] if a.get("operation") == "stop"] == ["fluid"], "the second one does not"
    assert by_text["norepinephrine 10 mcg/min"]["target_safety_reader"] == by_text["norepinephrine 10 mcg/min"]["order_safety_reader"] == by_text["norepinephrine 10 mcg/min"]["closure_reader"]
    assert by_text["stop all except dobutamine and norepinephrine"]["order_safety_reader"][-1]["operation"] != "stop"
    assert all(a["type"] != "epinephrine" for a in by_text["start nor-epi at 5 mcg/min"]["order_safety_reader"])
    out = subprocess.run(["git", "diff", "--name-only", "HEAD", "--", "docs/revision"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    assert all(path == "docs/revision/HISTORICAL_RECORD_INDEX.json" for path in out), out


# -- the CHECKPOINT of the order-safety hardening (written after the certification) ----------------------------------------------------------------------------------------------
CHECKPOINT_NAME = "PHASE3_ORDER_SAFETY_CHECKPOINT.json"
CHECKPOINT = json.loads((ROOT / "docs" / "revision" / CHECKPOINT_NAME).read_text(encoding="utf-8")) if (ROOT / "docs" / "revision" / CHECKPOINT_NAME).exists() else None


@pytest.mark.skipif(CHECKPOINT is None, reason="the checkpoint is written once, after the certification")
def test_v16_the_checkpoint_is_sealed_indexed_has_exactly_one_verdict_and_audits_every_limitation():
    assert hr.record_problems(CHECKPOINT) == [] and CHECKPOINT["provenance"]["record_id"] == "ORDER_SAFETY_CHECKPOINT_V1"
    entry = hr.load_index(ROOT)["records"][CHECKPOINT_NAME]
    assert entry["class"] == hr.VERSIONED and entry["record_digest"] == CHECKPOINT["record_digest"] and hr.index_problems(ROOT) == []
    assert CHECKPOINT["verdict"] in CHECKPOINT["verdicts"] and CHECKPOINT["verdict_name"] == CHECKPOINT["verdicts"][CHECKPOINT["verdict"]] and sorted(CHECKPOINT["verdicts"]) == list("ABCDE")
    audit = CHECKPOINT["closure_audit"]
    assert [f"L-{n}" for n in range(1, 16)] == sorted(audit, key=lambda key: int(key[2:])) and {row["status"] for row in audit.values()} <= {"CLOSED", "MITIGATED_BY_DEFENSE_IN_DEPTH", "INTENTIONALLY_DEFERRED"}
    assert audit["L-9"]["status"] != "INTENTIONALLY_DEFERRED" and audit["L-10"]["status"] == "INTENTIONALLY_DEFERRED", "L-9 no longer means 'the source alone'; L-10 stays deferred"
    assert all(value is True for key, value in CHECKPOINT["confirmations"].items() if key != "common_core_runtime_authority") and CHECKPOINT["confirmations"]["common_core_runtime_authority"] is False
    assert CHECKPOINT["facts"]["reader"]["successor_git_blob"] == succession.SUCCESSOR_GIT_BLOB and CHECKPOINT["facts"]["core_digest"] == a3.amended_core_digest_now()
    assert CHECKPOINT["certification"]["full_suite"]["failures"] == 0 and CHECKPOINT["certification"]["full_suite"]["errors"] == 0 and CHECKPOINT["certification"]["regressions"]["active_passed"] == CHECKPOINT["certification"]["regressions"]["active_total"]
