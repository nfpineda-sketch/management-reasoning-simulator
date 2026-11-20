"""P3-470: the SUCCESSION of the order reader (faculty decision FD-TARGET-01, 2026-11-20).

The faculty lifted the reader freeze ONLY for one narrowly scoped safety correction. The reader therefore changed once and the Phase-2 evidence did not move: these tests prove that the reader of the closure is
reconstructable byte for byte and in behavior, that every Phase-2 digest still recomputes from it WITHOUT editing ``clinical_core/``, that the calibration freeze moved in exactly one component, and that nothing sealed was
rewritten. They also guard the successor pin: the reader is frozen again at its successor state.
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
from clinical_core import amendment_1 as a1
from clinical_core import amendment_3 as a3
from clinical_core import calibration

ROOT = Path(__file__).resolve().parent
RECORD_NAME = "PHASE3_READER_SUCCESSION_TARGET_SAFETY.json"
RECORD = json.loads((ROOT / "docs" / "revision" / RECORD_NAME).read_text(encoding="utf-8")) if (ROOT / "docs" / "revision" / RECORD_NAME).exists() else None
needs_the_record = pytest.mark.skipif(RECORD is None, reason="the successor record is written once the reader is final")


def _git_blob(path) -> str:
    return succession.git_blob(Path(path).read_bytes())


def test_v1_the_reader_of_the_closure_is_rebuilt_from_the_live_file_byte_for_byte():
    data = succession.historical_reader_bytes()
    assert succession.git_blob(data) == succession.HISTORICAL_GIT_BLOB == freeze.HISTORICAL_BLOBS["family_parser.py"] == "1d17bf8b3dce66da5f1c8291237e2e7a7afde1c0"
    assert hashlib.sha256(data).hexdigest() == succession.HISTORICAL_SHA256 and data != (ROOT / "family_parser.py").read_bytes()
    assert succession.verify() == {"live_is_the_successor": True, "historical_rebuilt": True, "hunks": len(succession.REVERSAL)}
    assert hashlib.sha256((ROOT / "family_parser.py").read_bytes()).hexdigest() == succession.SUCCESSOR_SHA256 and _git_blob(ROOT / "family_parser.py") == succession.SUCCESSOR_GIT_BLOB == freeze.EXPECTED_BLOBS["family_parser.py"]


def test_v2_the_reversal_is_exact_or_it_refuses_a_hunk_that_is_not_unique_and_a_changed_reader():
    for new, old in succession.REVERSAL:
        assert new != old and (ROOT / "family_parser.py").read_text(encoding="utf-8").count(new) == 1
    live = (ROOT / "family_parser.py").read_bytes()
    with pytest.raises(ValueError):
        succession.historical_reader_bytes(live + b"\n# a later edit")
    with pytest.raises(ValueError):
        succession.historical_reader_bytes(live.replace(succession.REVERSAL[0][0].encode("utf-8"), b"", 1))


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
    assert "HISTORICAL_BLOBS" in source and "reader_succession" in source and succession.SUCCESSOR_GIT_BLOB in source and succession.HISTORICAL_GIT_BLOB in source


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
    assert reader["historical"]["git_blob"] == succession.HISTORICAL_GIT_BLOB and reader["successor"]["git_blob"] == succession.SUCCESSOR_GIT_BLOB
    assert RECORD["reversal"]["proven"] is True and RECORD["reversal"]["hunk_count"] == len(succession.REVERSAL) == len(RECORD["reversal"]["hunks"])
    assert [(h["successor_text"], h["historical_text"]) for h in RECORD["reversal"]["hunks"]] == [tuple(pair) for pair in succession.REVERSAL]
    assert freeze_state["calibration"]["components_that_moved"] == ["input_path_sources"] and freeze_state["calibration"]["scenario_inputs_identical"] is True
    assert freeze_state["calibration"]["before_the_succession"]["digest"] == "c1eeb5538a4ea990cbcb4432b0c28e6cb8c351ffe08c96a6036f82d3b65a9b85"
    assert freeze_state["calibration"]["after_the_succession"]["digest"] == calibration.frozen_digest()
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
