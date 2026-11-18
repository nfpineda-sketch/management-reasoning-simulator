"""P3-388: the versioning contract of code-derived historical records (faculty decision of 2026-11-17).

The contract in one line: a historical record is immutable and says what generated it; a regeneration is compared with it only under the
same generating code; a newer representation is a successor record. Each rule has its negative control here.
"""
import ast
import json
import shutil
from pathlib import Path

import pytest

import historical_records as hr

ROOT = Path(__file__).resolve().parent
#: Written as a literal ON PURPOSE: the digest of the 101 legacy entries the contract found. Moving a legacy pin to make a rewritten record
#: pass would have to change this line too, which is a visible act and not a silent regeneration.
LEGACY_ENTRIES_DIGEST = "1afe6c43ab5e4accb33e4b6924d5f63e8c36e23c21c81760eec7251605b38789"
#: The digest of EVERY entry of the repository's index (legacy, versioned and lineage). It is typed here on purpose: adding a record, or certifying the open lineage
#: record, moves this constant in the same change, and nothing else can move a pin without moving it (adversarial review, finding 3).
ALL_ENTRIES_DIGEST = "4f2a12d3b4750bd2e9b40a08578ea1fa3e4a4542789367b8c95f3981236e4a53"
CODE = {"core_digest": "c" * 64, "phase3_layer_digest": "d" * 64, "generator": {"some_generator.py": "e" * 64}}


def _record(**changes) -> dict:
    block = hr.provenance(record_id="EXAMPLE_RECORD_V1", generating_code=CODE, source_data={"rows": [1, 2, 3]}, generated_on="2026-11-17",
                          source_snapshot_id="SOME_SNAPSHOT", grant_id="SOME_GRANT")
    return hr.seal({"record_type": "EXAMPLE", "result": {"value": 42}, "provenance": block, **changes})


# -- the module ---------------------------------------------------------------------------------------------------------------------------------

def test_v1_the_module_is_pure_it_reads_no_clock_and_imports_nothing_of_the_repository():
    tree = ast.parse((ROOT / "historical_records.py").read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            imported.add(str(node.module).split(".")[0])
    assert imported == {"__future__", "hashlib", "json", "pathlib", "typing"}
    source = (ROOT / "historical_records.py").read_text(encoding="utf-8")
    for clock in ("datetime", "time.time", "os.environ", "subprocess"):
        assert clock not in source, clock
    assert hr.CONTRACT == "P3-388_HISTORICAL_RECORD_VERSIONING" and hr.SCHEMA_VERSION == 1


# -- the provenance block --------------------------------------------------------------------------------------------------------------------------

def test_v2_a_generated_record_names_its_schema_its_generating_code_its_snapshot_its_grant_its_source_data_and_its_date():
    block = _record()["provenance"]
    assert set(block) == set(hr.PROVENANCE_FIELDS)
    assert block["record_schema_version"] == 1 and block["contract"] == hr.CONTRACT and block["generated_on"] == "2026-11-17"
    assert block["source_snapshot_id"] == "SOME_SNAPSHOT" and block["grant_id"] == "SOME_GRANT" and block["supersedes"] is None
    assert block["generating_code"] == CODE and block["generating_code_fingerprint"] == hr.code_fingerprint(CODE)
    assert block["source_data_digest"] == hr.digest_of({"rows": [1, 2, 3]}) != hr.digest_of({"rows": [1, 2, 4]})
    # a record that stands on no snapshot and no grant says so, explicitly
    free = hr.provenance(record_id="X", generating_code=CODE, source_data=[], generated_on="2026-11-17")
    assert free["source_snapshot_id"] is None and free["grant_id"] is None and hr.provenance_problems(free) == []


@pytest.mark.parametrize("edit, expected", [
    (lambda b: b.pop("grant_id"), hr.MISSING_FIELD),
    (lambda b: b.pop("generated_on"), hr.MISSING_FIELD),
    (lambda b: b.update(contract="ANOTHER_CONTRACT"), hr.WRONG_CONTRACT),
    (lambda b: b.update(record_schema_version=0), hr.WRONG_SCHEMA),
    (lambda b: b.update(record_schema_version=True), hr.WRONG_SCHEMA),
    (lambda b: b.update(record_schema_version="1"), hr.WRONG_SCHEMA),
    (lambda b: b["generating_code"].update(core_digest="f" * 64), hr.FINGERPRINT_MISMATCH),
    (lambda b: b.update(generating_code_fingerprint="0" * 64), hr.FINGERPRINT_MISMATCH),
    (lambda b: b.update(generating_code={}), hr.FINGERPRINT_MISMATCH),
    (lambda b: b.update(generated_on="17/11/2026"), hr.BAD_DATE),
    (lambda b: b.update(generated_on="2026-13-01"), hr.BAD_DATE),
    (lambda b: b.update(record_id="  "), hr.MISSING_FIELD),
    (lambda b: b.update(source_data_digest="abc"), hr.MISSING_FIELD),
    (lambda b: b.update(supersedes={"record": "docs/revision/OLD.json"}), hr.BAD_SUCCESSION),
    (lambda b: b.update(supersedes="docs/revision/OLD.json"), hr.BAD_SUCCESSION),
])
def test_v3_every_defect_of_a_provenance_block_is_refused_by_name(edit, expected):
    block = json.loads(json.dumps(_record()["provenance"]))
    edit(block)
    assert any(item.startswith(expected) for item in hr.provenance_problems(block)), hr.provenance_problems(block)
    with pytest.raises(ValueError):
        hr.seal({"record_type": "EXAMPLE", "provenance": block})


def test_v4_what_is_not_a_record_or_carries_no_provenance_is_named_and_nothing_raises():
    for thing in (None, 7, "record", [], {"record_type": "EXAMPLE"}, {"provenance": "x"}, {"provenance": {}}):
        assert hr.record_problems(thing), thing
    assert hr.NOT_A_RECORD in hr.record_problems(None) and hr.NO_PROVENANCE in hr.record_problems({"a": 1})
    with pytest.raises(ValueError):
        hr.code_fingerprint({})


# -- the seal ----------------------------------------------------------------------------------------------------------------------------------------

def test_v5_a_record_is_sealed_by_the_digest_of_its_content_and_any_edit_breaks_the_seal():
    record = _record()
    assert hr.record_problems(record) == [] and len(record["record_digest"]) == 64
    for edit in (lambda r: r["result"].update(value=43), lambda r: r.update(extra=1), lambda r: r["provenance"].update(grant_id="ANOTHER_GRANT"),
                 lambda r: r.pop("record_type")):
        forged = json.loads(json.dumps(record))
        edit(forged)
        assert hr.SEAL_MISMATCH in hr.record_problems(forged)
    unsealed = {key: value for key, value in record.items() if key != "record_digest"}
    assert hr.record_problems(unsealed) == [hr.NOT_SEALED]
    assert hr.seal(record) == record                                   # sealing a sealed record changes nothing


# -- a regeneration is compared only under the same generating code ------------------------------------------------------------------------------------

def test_v6_a_stored_record_is_compared_with_a_regeneration_only_when_the_same_code_generated_it():
    record = _record()
    assert hr.same_generating_code(record, CODE) is True
    for other in ({**CODE, "phase3_layer_digest": "a" * 64}, {**CODE, "core_digest": "b" * 64}, {**CODE, "generator": {"some_generator.py": "0" * 64}},
                  {key: value for key, value in CODE.items() if key != "generator"}):
        assert hr.same_generating_code(record, other) is False
    assert hr.same_generating_code({"record_type": "LEGACY, NO PROVENANCE"}, CODE) is False
    assert hr.same_generating_code(None, CODE) is False


def test_v7_a_record_is_never_overwritten_with_other_content_and_only_a_sealed_one_is_written(tmp_path):
    record, target = _record(), tmp_path / "EXAMPLE.json"
    first = hr.write(target, record)
    assert first == hr.file_sha256(target) and json.loads(target.read_text(encoding="utf-8")) == record
    assert hr.write(target, record) == first                            # the same content again is the same file
    regenerated = _record(result={"value": 43})
    with pytest.raises(FileExistsError, match="successor"):
        hr.write(target, regenerated)                                   # new code's output is a NEW record, never this one rewritten
    assert hr.file_sha256(target) == first
    with pytest.raises(ValueError):
        hr.write(tmp_path / "UNSEALED.json", {"record_type": "EXAMPLE"})
    assert not (tmp_path / "UNSEALED.json").exists()


# -- the index: immutability on disk ---------------------------------------------------------------------------------------------------------------------

def test_v8_every_record_of_the_repository_is_indexed_and_is_byte_for_byte_what_the_index_pins():
    """THE no-silent-regeneration check of the whole repository: a historical record whose bytes moved fails here, by name."""
    assert hr.index_problems(ROOT) == []
    index = hr.load_index(ROOT)
    on_disk = {path.name for path in (ROOT / hr.RECORD_DIR).glob("*.json")} - {Path(hr.INDEX_PATH).name}
    assert set(index["records"]) == on_disk
    assert all(entry["class"] in hr.CLASSES for entry in index["records"].values())
    assert index["contract"] == hr.CONTRACT and index["adopted_on"] == "2026-11-17"


def test_v9_the_legacy_entries_are_the_ones_the_contract_found_and_their_pins_cannot_be_moved_silently():
    index = hr.load_index(ROOT)
    legacy = {name for name, entry in index["records"].items() if entry["class"] == hr.LEGACY_UNVERSIONED}
    assert len(legacy) == 101 and index["legacy_entries_digest"] == hr.legacy_digest(index) == LEGACY_ENTRIES_DIGEST
    assert {"P2X3_phase2_closure.json", "PHASE2_AMENDMENT_1.json", "PHASE2_AMENDMENT_2.json", "PHASE3_FACULTY_REVIEW_CHECKPOINT.json",
            "PHASE3_GI_PRESSURE_PROMOTION_CHECKPOINT.json", "GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1.json", "GI_DEVELOPMENT_SNAPSHOT_V1.json"} <= legacy
    assert "HISTORICAL_RECORD_INDEX.json" not in index["records"]
    assert not any(entry.get("class") == hr.LEGACY_UNVERSIONED and "provenance" in entry for entry in index["records"].values())
    assert hr.entries_digest(index) == ALL_ENTRIES_DIGEST, "an entry of the index moved: a new record, a certified lineage record, or a pin that must not move"
    versioned = {name: entry for name, entry in index["records"].items() if entry["class"] == hr.VERSIONED}
    assert versioned and all(set(entry) == {"class", "file_sha256", "record_id", "record_digest"} for entry in versioned.values())
    lineage = {name for name, entry in index["records"].items() if entry["class"] in (hr.LINEAGE_RECORD_OPEN, hr.LINEAGE_RECORD)}
    assert lineage == {"PHASE2_AMENDMENT_3.json"}


@pytest.fixture
def small_repository(tmp_path):
    """A repository with three records and their index: a legacy one, a versioned one and its successor."""
    directory = tmp_path / hr.RECORD_DIR
    directory.mkdir(parents=True)
    (directory / "LEGACY.json").write_text(json.dumps({"old": True}) + "\n", encoding="utf-8")
    first = _record()
    first_sha = hr.write(directory / "EXAMPLE_V1.json", first)
    block = hr.provenance(record_id="EXAMPLE_RECORD_V2", generating_code={**CODE, "phase3_layer_digest": "a" * 64}, source_data={"rows": [1, 2, 3]},
                          generated_on="2026-12-01", supersedes={"record": f"{hr.RECORD_DIR}/EXAMPLE_V1.json", "file_sha256": first_sha})
    hr.write(directory / "EXAMPLE_V2.json", hr.seal({"record_type": "EXAMPLE", "result": {"value": 43}, "provenance": block}))
    index = {"contract": hr.CONTRACT, "records": {
        "LEGACY.json": hr.index_entry(directory / "LEGACY.json", hr.LEGACY_UNVERSIONED),
        "EXAMPLE_V1.json": hr.index_entry(directory / "EXAMPLE_V1.json", hr.VERSIONED),
        "EXAMPLE_V2.json": hr.index_entry(directory / "EXAMPLE_V2.json", hr.VERSIONED)}}
    index["legacy_entries_digest"] = hr.legacy_digest(index)
    (tmp_path / hr.INDEX_PATH).write_text(json.dumps(index), encoding="utf-8")
    return tmp_path


def _rewrite_index(root, edit):
    index = json.loads((root / hr.INDEX_PATH).read_text(encoding="utf-8"))
    edit(index)
    (root / hr.INDEX_PATH).write_text(json.dumps(index), encoding="utf-8")


def test_v10_a_successor_record_leaves_the_record_it_supersedes_where_it_was(small_repository):
    assert hr.index_problems(small_repository) == []
    directory = small_repository / hr.RECORD_DIR
    newer = json.loads((directory / "EXAMPLE_V2.json").read_text(encoding="utf-8"))
    assert newer["provenance"]["supersedes"]["file_sha256"] == hr.file_sha256(directory / "EXAMPLE_V1.json")
    assert json.loads((directory / "EXAMPLE_V1.json").read_text(encoding="utf-8"))["result"] == {"value": 42}     # the older evidence, untouched


def test_v11_every_way_of_regenerating_or_losing_a_record_is_refused_by_name(small_repository):
    directory = small_repository / hr.RECORD_DIR
    saved = {name: (directory / name).read_bytes() for name in ("LEGACY.json", "EXAMPLE_V1.json", "EXAMPLE_V2.json")}

    def restore():
        for name, content in saved.items():
            (directory / name).write_bytes(content)

    # the bytes of a legacy record changed (a "regeneration under new code")
    (directory / "LEGACY.json").write_text(json.dumps({"old": True, "regenerated": True}) + "\n", encoding="utf-8")
    assert hr.index_problems(small_repository) == [f"{hr.BYTES_CHANGED}: LEGACY.json"]
    # ... and moving its pin to the new bytes does not make it pass: the legacy part of the index is sealed
    index_before = (small_repository / hr.INDEX_PATH).read_bytes()
    _rewrite_index(small_repository, lambda index: index["records"]["LEGACY.json"].update(file_sha256=hr.file_sha256(directory / "LEGACY.json")))
    assert hr.index_problems(small_repository) == [hr.LEGACY_REWRITTEN]
    (small_repository / hr.INDEX_PATH).write_bytes(index_before)
    restore()
    # a versioned record edited in place, with its seal recomputed: the index still pins the bytes it had
    forged = json.loads(saved["EXAMPLE_V1.json"])
    forged["result"] = {"value": 99}
    (directory / "EXAMPLE_V1.json").write_text(json.dumps(hr.seal(forged), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    assert f"{hr.BYTES_CHANGED}: EXAMPLE_V1.json" in hr.index_problems(small_repository)
    restore()
    # a record deleted, a record nobody indexed, an entry of no known class
    (directory / "EXAMPLE_V2.json").unlink()
    assert hr.index_problems(small_repository) == [f"{hr.RECORD_MISSING}: EXAMPLE_V2.json"]
    restore()
    (directory / "UNINDEXED.json").write_text("{}", encoding="utf-8")
    assert hr.index_problems(small_repository) == [f"{hr.NOT_INDEXED}: UNINDEXED.json"]
    (directory / "UNINDEXED.json").unlink()
    _rewrite_index(small_repository, lambda index: index["records"]["EXAMPLE_V1.json"].update({"class": "REGENERABLE"}))
    assert f"{hr.UNKNOWN_CLASS}: EXAMPLE_V1.json" in hr.index_problems(small_repository)
    (small_repository / hr.INDEX_PATH).write_bytes(index_before)
    # a successor whose predecessor is not the pinned one
    _rewrite_index(small_repository, lambda index: index["records"].pop("EXAMPLE_V1.json"))
    (directory / "EXAMPLE_V1.json").unlink()
    assert any(item.startswith(hr.SUCCESSOR_BROKEN) for item in hr.index_problems(small_repository))
    # an index that cannot be read is a refusal, never a pass
    (small_repository / hr.INDEX_PATH).write_text("{not json", encoding="utf-8")
    assert hr.index_problems(small_repository) and hr.index_problems(small_repository)[0].startswith(hr.NOT_A_RECORD)


def test_v12_a_lineage_record_is_open_only_until_it_is_certified_and_then_it_is_pinned(tmp_path):
    directory = tmp_path / hr.RECORD_DIR
    directory.mkdir(parents=True)
    path = directory / "PHASE2_AMENDMENT_9.json"
    path.write_text(json.dumps({"certification": {"status": "CANDIDATE"}}), encoding="utf-8")
    index = {"contract": hr.CONTRACT, "records": {path.name: hr.index_entry(path, hr.LINEAGE_RECORD_OPEN)}}
    index["legacy_entries_digest"] = hr.legacy_digest(index)
    (tmp_path / hr.INDEX_PATH).write_text(json.dumps(index), encoding="utf-8")
    assert "file_sha256" not in index["records"][path.name] and hr.index_problems(tmp_path) == []
    path.write_text(json.dumps({"certification": {"status": "CANDIDATE", "note": "still being written"}}), encoding="utf-8")
    assert hr.index_problems(tmp_path) == []                            # open: its bytes may still move
    path.write_text(json.dumps({"certification": {"status": "CERTIFIED"}}), encoding="utf-8")
    assert hr.index_problems(tmp_path) == [f"{hr.OPEN_RECORD_IS_CERTIFIED}: {path.name}"]      # the moment it says CERTIFIED it must be pinned
    _rewrite_index(tmp_path, lambda data: data["records"].update({path.name: hr.index_entry(path, hr.LINEAGE_RECORD)}))
    assert hr.index_problems(tmp_path) == []
    path.write_text(json.dumps({"certification": {"status": "CERTIFIED", "edited": True}}), encoding="utf-8")
    assert hr.index_problems(tmp_path) == [f"{hr.BYTES_CHANGED}: {path.name}"]


def test_v12b_no_class_of_the_index_can_be_used_to_unpin_another_record(small_repository):
    """Adversarial review, finding 3: a lineage class is only for the own record of a core successor, and a versioned entry names the record's own id and seal."""
    directory = small_repository / hr.RECORD_DIR
    assert hr.is_lineage_record_name("PHASE2_AMENDMENT_3.json") and hr.is_lineage_record_name("PHASE2_AMENDMENT_12.json")
    for name in ("PHASE2_AMENDMENT_X.json", "PHASE2_AMENDMENT_3.md", "PHASE3_FRF_TONE_V1_CANDIDATE.json", "XPHASE2_AMENDMENT_3.json", "PHASE2_AMENDMENT_.json"):
        assert not hr.is_lineage_record_name(name), name
    # a versioned record reclassified as an OPEN lineage record would be free to change: refused by name, whatever its bytes
    for kind in (hr.LINEAGE_RECORD_OPEN, hr.LINEAGE_RECORD):
        _rewrite_index(small_repository, lambda data, kind=kind: data["records"].update({"EXAMPLE_V1.json": hr.index_entry(directory / "EXAMPLE_V1.json", kind)}))
        assert f"{hr.LINEAGE_CLASS_MISUSED}: EXAMPLE_V1.json" in hr.index_problems(small_repository)
    _rewrite_index(small_repository, lambda data: data["records"].update({"EXAMPLE_V1.json": hr.index_entry(directory / "EXAMPLE_V1.json", hr.VERSIONED)}))
    assert hr.index_problems(small_repository) == []
    before = hr.entries_digest(hr.load_index(small_repository))
    # a re-sealed rewrite with its pin moved: the entry is consistent again, and the digest of the entries is what moved
    stored = json.loads((directory / "EXAMPLE_V1.json").read_text(encoding="utf-8"))
    rewritten = hr.seal({**{key: value for key, value in stored.items() if key != "record_digest"}, "result": {"value": 99}})
    (directory / "EXAMPLE_V1.json").write_text(json.dumps(rewritten, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    assert f"{hr.BYTES_CHANGED}: EXAMPLE_V1.json" in hr.index_problems(small_repository)
    _rewrite_index(small_repository, lambda data: data["records"]["EXAMPLE_V1.json"].update({"file_sha256": hr.file_sha256(directory / "EXAMPLE_V1.json")}))
    assert f"{hr.ENTRY_NAMES_ANOTHER_RECORD}: EXAMPLE_V1.json" in hr.index_problems(small_repository)      # the pinned seal is still the old record's
    _rewrite_index(small_repository, lambda data: data["records"].update({"EXAMPLE_V1.json": hr.index_entry(directory / "EXAMPLE_V1.json", hr.VERSIONED)}))
    assert hr.entries_digest(hr.load_index(small_repository)) != before, "what no check of the index alone can see is seen by the pinned digest of its entries"


def test_v13_the_real_index_on_a_copy_refuses_a_regenerated_historical_checkpoint(tmp_path):
    """The same control on the repository's own records: regenerate one certified checkpoint in a copy and the index names it."""
    shutil.copytree(ROOT / hr.RECORD_DIR, tmp_path / hr.RECORD_DIR)
    assert hr.index_problems(tmp_path) == []
    target = tmp_path / hr.RECORD_DIR / "PHASE3_GI_PRESSURE_PROMOTION_CHECKPOINT.json"
    record = json.loads(target.read_text(encoding="utf-8"))
    record["regenerated_under_new_code"] = True
    target.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    assert hr.index_problems(tmp_path) == [f"{hr.BYTES_CHANGED}: PHASE3_GI_PRESSURE_PROMOTION_CHECKPOINT.json"]
