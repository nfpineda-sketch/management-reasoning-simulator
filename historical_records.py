"""P3-388 (faculty decision of 2026-11-17): the versioning contract of code-derived historical records.

A record under ``docs/revision/`` that a program GENERATED (a checkpoint, a series, an analysis, a candidate set) is evidence of what
one exact version of the code produced on one date. Twice in this project a later change of the code made a test "regenerate and
compare" such a record, and the only ways out were to rewrite the record (which destroys the evidence) or to carve an ad hoc exception.
This module is the rule that replaces both:

  1. A historical record is IMMUTABLE. Its bytes are pinned in the index (``docs/revision/HISTORICAL_RECORD_INDEX.json``); a record whose
     bytes changed is refused by name. It is never regenerated under new code, silently or otherwise.
  2. A generated record says WHAT generated it: a ``provenance`` block with the record's schema version, the fingerprint of the generating
     code (and the parts it was computed from), the snapshot and the grant it stands on where there is one, the digest of its source data,
     and the date it was generated. The whole record is sealed by a digest of its content.
  3. A regeneration is compared with a stored record ONLY under the same generating code (``same_generating_code``). Under other code the
     stored record is checked for what it is -- sealed, pinned, well formed -- and the new code's output is a NEW record.
  4. When a newer representation is needed, a SUCCESSOR record is created: it names the record it supersedes and that record's digest, and
     the older one stays where it is, byte for byte. Nothing is edited in place.

The module is pure (``hashlib`` and ``json`` only): it reads no clock, imports nothing of the repository and decides nothing about any
record's content. The date is given by the generator as a constant, because the repository's records are reproducible functions of their
inputs and carry dates, not wall-clock timestamps. Records that predate this contract stay as they are: the index lists them as
``LEGACY_UNVERSIONED`` and pins their bytes, which is the part of the contract they can keep.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

SCHEMA_VERSION = 1
CONTRACT = "P3-388_HISTORICAL_RECORD_VERSIONING"
DECIDED = "2026-11-17"
ROOT = Path(__file__).resolve().parent
RECORD_DIR = "docs/revision"
INDEX_PATH = f"{RECORD_DIR}/HISTORICAL_RECORD_INDEX.json"

#: The classes of record the index holds.
LEGACY_UNVERSIONED = "LEGACY_UNVERSIONED"            # generated before this contract: bytes pinned, no provenance block
VERSIONED = "VERSIONED"                              # generated under this contract: bytes pinned, provenance block, sealed
LINEAGE_RECORD_OPEN = "LINEAGE_RECORD_OPEN_UNTIL_CERTIFIED"   # a core successor's own record while its certification is still to be written
LINEAGE_RECORD = "LINEAGE_RECORD"                    # that record once certified: bytes pinned (its format is the lineage gate's, not this contract's)
CLASSES = (LEGACY_UNVERSIONED, VERSIONED, LINEAGE_RECORD_OPEN, LINEAGE_RECORD)

#: The fields every provenance block names. ``grant_id`` and ``source_snapshot_id`` may be None (a record that stands on neither says so).
PROVENANCE_FIELDS = ("contract", "record_schema_version", "record_id", "generating_code_fingerprint", "generating_code", "source_snapshot_id",
                     "grant_id", "source_data_digest", "generated_on", "supersedes")

# -- problem codes (every refusal has a name) ----------------------------------------------------------------------------------------------
NOT_A_RECORD = "NOT_A_RECORD"
NO_PROVENANCE = "RECORD_HAS_NO_PROVENANCE_BLOCK"
MISSING_FIELD = "PROVENANCE_FIELD_MISSING"
WRONG_CONTRACT = "PROVENANCE_NAMES_ANOTHER_CONTRACT"
WRONG_SCHEMA = "RECORD_SCHEMA_VERSION_IS_NOT_A_POSITIVE_INTEGER"
FINGERPRINT_MISMATCH = "GENERATING_CODE_FINGERPRINT_DOES_NOT_MATCH_ITS_PARTS"
NOT_SEALED = "RECORD_IS_NOT_SEALED"
SEAL_MISMATCH = "RECORD_SEAL_DOES_NOT_MATCH_ITS_CONTENT"
BAD_DATE = "GENERATED_ON_IS_NOT_AN_ISO_DATE"
BAD_SUCCESSION = "SUPERSEDES_DOES_NOT_NAME_A_RECORD_AND_ITS_DIGEST"
NOT_INDEXED = "RECORD_IS_NOT_IN_THE_INDEX"
BYTES_CHANGED = "RECORD_BYTES_ARE_NOT_THE_PINNED_ONES"
RECORD_MISSING = "INDEXED_RECORD_IS_MISSING"
UNKNOWN_CLASS = "INDEX_ENTRY_HAS_NO_KNOWN_CLASS"
SUCCESSOR_BROKEN = "INDEX_SUCCESSION_NAMES_A_RECORD_THAT_IS_NOT_INDEXED_OR_NOT_PINNED_AS_STATED"
LEGACY_REWRITTEN = "A_LEGACY_ENTRY_OF_THE_INDEX_WAS_CHANGED_OR_REMOVED"
LINEAGE_CLASS_MISUSED = "A_LINEAGE_CLASS_IS_ONLY_FOR_THE_OWN_RECORD_OF_A_CORE_SUCCESSOR"
OPEN_RECORD_IS_CERTIFIED = "A_LINEAGE_RECORD_THAT_SAYS_CERTIFIED_IS_STILL_INDEXED_AS_OPEN"
ENTRY_NAMES_ANOTHER_RECORD = "INDEX_ENTRY_DOES_NOT_NAME_THE_RECORDS_OWN_ID_AND_SEAL"
#: The own records of the core's successors (``docs/revision/PHASE2_AMENDMENT_<n>.json``): the only files a lineage class may index.
LINEAGE_RECORD_PREFIX, LINEAGE_RECORD_SUFFIX = "PHASE2_AMENDMENT_", ".json"


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def digest_of(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("ascii")).hexdigest()


def file_sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def code_fingerprint(parts: Mapping[str, Any]) -> str:
    """The fingerprint of the generating code: the digest of its named parts (the core digest, the Phase-3 layer digest, the generator's own
    file hashes -- whatever the generator declares). The parts travel with the record, so the fingerprint can be recomputed from them."""
    if not isinstance(parts, Mapping) or not parts:
        raise ValueError("the generating code is named by at least one part")
    return digest_of({str(key): value for key, value in parts.items()})


def provenance(*, record_id: str, generating_code: Mapping[str, Any], source_data: Any, generated_on: str, source_snapshot_id: str | None = None,
               grant_id: str | None = None, supersedes: Mapping[str, str] | None = None, schema_version: int = SCHEMA_VERSION) -> dict:
    """The provenance block of a record being generated NOW. ``source_data`` is whatever the record was computed from (it is digested, not
    stored); ``supersedes`` names the record this one succeeds and that record's file digest, or is None for a first representation."""
    block = {"contract": CONTRACT, "record_schema_version": schema_version, "record_id": str(record_id),
             "generating_code_fingerprint": code_fingerprint(generating_code), "generating_code": dict(generating_code),
             "source_snapshot_id": source_snapshot_id, "grant_id": grant_id, "source_data_digest": digest_of(source_data),
             "generated_on": str(generated_on), "supersedes": None if supersedes is None else dict(supersedes)}
    found = provenance_problems(block)
    if found:
        raise ValueError(f"not a provenance block: {found}")
    return block


def _is_date(value: Any) -> bool:
    text = str(value or "")
    return (len(text) == 10 and text[4] == "-" and text[7] == "-" and text.replace("-", "").isdigit()
            and 1 <= int(text[5:7]) <= 12 and 1 <= int(text[8:10]) <= 31)


def provenance_problems(block: Any) -> list:
    """Why ``block`` is not a provenance block of this contract, by name. Empty means it is one. Never raises."""
    try:
        if not isinstance(block, Mapping):
            return [NO_PROVENANCE]
        problems = [f"{MISSING_FIELD}: {name}" for name in PROVENANCE_FIELDS if name not in block]
        if block.get("contract") != CONTRACT:
            problems.append(WRONG_CONTRACT)
        version = block.get("record_schema_version")
        if isinstance(version, bool) or not isinstance(version, int) or version < 1:
            problems.append(WRONG_SCHEMA)
        parts = block.get("generating_code")
        if not isinstance(parts, Mapping) or not parts or block.get("generating_code_fingerprint") != code_fingerprint(parts):
            problems.append(FINGERPRINT_MISMATCH)
        if not _is_date(block.get("generated_on")):
            problems.append(BAD_DATE)
        if not str(block.get("record_id") or "").strip():
            problems.append(f"{MISSING_FIELD}: record_id")
        source = str(block.get("source_data_digest") or "")
        if len(source) != 64 or any(char not in "0123456789abcdef" for char in source):
            problems.append(f"{MISSING_FIELD}: source_data_digest")
        succeeded = block.get("supersedes")
        if succeeded is not None:
            sha = str(succeeded.get("file_sha256") or "") if isinstance(succeeded, Mapping) else ""
            if not isinstance(succeeded, Mapping) or not str(succeeded.get("record") or "").strip() or len(sha) != 64:
                problems.append(BAD_SUCCESSION)
        return problems
    except Exception as error:
        return [f"{NO_PROVENANCE}: {type(error).__name__}"]


def seal(record: Mapping[str, Any]) -> dict:
    """The record with its seal: ``record_digest`` is the digest of everything else in it. A sealed record is what gets written."""
    body = {key: value for key, value in dict(record).items() if key != "record_digest"}
    if provenance_problems(body.get("provenance")):
        raise ValueError(f"a record is sealed with its provenance: {provenance_problems(body.get('provenance'))}")
    return {**body, "record_digest": digest_of(body)}


def record_problems(record: Any) -> list:
    """Why ``record`` is not a sealed, versioned record of this contract, by name. Empty means it is one. Never raises."""
    try:
        if not isinstance(record, Mapping):
            return [NOT_A_RECORD]
        problems = provenance_problems(record.get("provenance"))
        if "record_digest" not in record:
            problems.append(NOT_SEALED)
        elif record.get("record_digest") != digest_of({key: value for key, value in dict(record).items() if key != "record_digest"}):
            problems.append(SEAL_MISMATCH)
        return problems
    except Exception as error:
        return [f"{NOT_A_RECORD}: {type(error).__name__}"]


def same_generating_code(record: Mapping[str, Any], generating_code: Mapping[str, Any]) -> bool:
    """Whether ``record`` was generated by exactly this code. ONLY then may a regeneration be compared with it: under other code the stored
    record is evidence of what the OTHER code produced, and a difference is not a defect of either."""
    try:
        block = record.get("provenance") or {}
        return not provenance_problems(block) and block.get("generating_code_fingerprint") == code_fingerprint(generating_code)
    except Exception:
        return False


def write(path: str | Path, record: Mapping[str, Any]) -> str:
    """Write a sealed record as the repository writes its records (two-space JSON, sorted keys, a final newline) and return its file digest.
    An existing file is never overwritten with other bytes: that would be the silent regeneration this contract forbids."""
    found = record_problems(record)
    if found:
        raise ValueError(f"only a sealed, versioned record is written: {found}")
    target = Path(path)
    text = json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if target.exists() and target.read_text(encoding="utf-8") != text:
        raise FileExistsError(f"{target.name} exists with other content: a historical record is not regenerated in place; create a successor record")
    target.write_text(text, encoding="utf-8")
    return file_sha256(target)


# -- the index ---------------------------------------------------------------------------------------------------------------------------------

def load_index(root: str | Path = ROOT) -> dict:
    return json.loads((Path(root) / INDEX_PATH).read_text(encoding="utf-8"))


def legacy_digest(index: Mapping[str, Any]) -> str:
    """The digest of the index's LEGACY entries (name, class and pinned bytes): what the contract found in the repository when it was adopted.
    It is pinned in the index's own header and in the test that guards it, so a legacy pin cannot be moved to make a rewritten record pass."""
    entries = {name: {"class": entry.get("class"), "file_sha256": entry.get("file_sha256")}
               for name, entry in dict(index.get("records") or {}).items() if entry.get("class") == LEGACY_UNVERSIONED}
    return digest_of(entries)


def entries_digest(index: Mapping[str, Any]) -> str:
    """The digest of EVERY entry of the index, whatever its class. The index's header seals only its legacy part (the index grows by one entry
    per new record); the test that guards the repository pins THIS value, so no pin -- legacy, versioned or lineage -- moves without that
    constant moving in the same change, where a reviewer sees it."""
    return digest_of({name: dict(entry) for name, entry in dict(index.get("records") or {}).items()})


def is_lineage_record_name(name: str) -> bool:
    middle = str(name)[len(LINEAGE_RECORD_PREFIX):-len(LINEAGE_RECORD_SUFFIX)]
    return str(name).startswith(LINEAGE_RECORD_PREFIX) and str(name).endswith(LINEAGE_RECORD_SUFFIX) and middle.isdigit()


def index_problems(root: str | Path = ROOT, index: Mapping[str, Any] | None = None) -> list:
    """Everything in which the records on disk are not what the index pins, by name. Empty means every record is where, and what, it was.

    Every ``*.json`` under ``docs/revision/`` is indexed; every pinned record exists with the pinned bytes; a versioned record is sealed and
    carries its provenance; a successor names an indexed record by the digest the index pins for it; and the legacy entries are the ones the
    contract found. The index itself is the one file it does not pin (it grows by one entry per new record, and its legacy part is sealed)."""
    base = Path(root)
    problems: list = []
    try:
        index = load_index(base) if index is None else index
        records = dict(index.get("records") or {})
        on_disk = sorted(path.name for path in (base / RECORD_DIR).glob("*.json") if path.name != Path(INDEX_PATH).name)
        for name in on_disk:
            if name not in records:
                problems.append(f"{NOT_INDEXED}: {name}")
        for name, entry in sorted(records.items()):
            kind = entry.get("class")
            if kind not in CLASSES:
                problems.append(f"{UNKNOWN_CLASS}: {name}")
                continue
            path = base / RECORD_DIR / name
            if not path.exists():
                problems.append(f"{RECORD_MISSING}: {name}")
                continue
            if kind in (LINEAGE_RECORD_OPEN, LINEAGE_RECORD) and not is_lineage_record_name(name):
                problems.append(f"{LINEAGE_CLASS_MISUSED}: {name}")       # no other record can be left unpinned, or pinned without its provenance, by a class
                continue
            if kind == LINEAGE_RECORD_OPEN:
                # Its certification block is still to be written, once. The moment it says CERTIFIED it is pinned like the rest: an open entry never covers a certified record.
                status = dict(dict(json.loads(path.read_text(encoding="utf-8"))).get("certification") or {}).get("status")
                if status == "CERTIFIED":
                    problems.append(f"{OPEN_RECORD_IS_CERTIFIED}: {name}")
                continue
            if file_sha256(path) != entry.get("file_sha256"):
                problems.append(f"{BYTES_CHANGED}: {name}")
                continue
            if kind == VERSIONED:
                stored = json.loads(path.read_text(encoding="utf-8"))
                problems += [f"{name}: {item}" for item in record_problems(stored)]
                if (entry.get("record_id"), entry.get("record_digest")) != (dict(stored.get("provenance") or {}).get("record_id"), stored.get("record_digest")):
                    problems.append(f"{ENTRY_NAMES_ANOTHER_RECORD}: {name}")
                succeeded = (json.loads(path.read_text(encoding="utf-8")).get("provenance") or {}).get("supersedes")
                if succeeded is not None:
                    older = records.get(Path(str(succeeded.get("record"))).name)
                    if older is None or older.get("file_sha256") != succeeded.get("file_sha256"):
                        problems.append(f"{SUCCESSOR_BROKEN}: {name} -> {succeeded.get('record')}")
        if legacy_digest(index) != index.get("legacy_entries_digest"):
            problems.append(LEGACY_REWRITTEN)
    except Exception as error:
        problems.append(f"{NOT_A_RECORD}: the index cannot be read ({type(error).__name__})")
    return problems


def index_entry(path: str | Path, kind: str, **more: Any) -> dict:
    """The index entry of a record as it is on disk now: its class and its pinned bytes."""
    if kind not in CLASSES:
        raise ValueError(f"unknown record class {kind!r}")
    entry = {"class": kind, **more}
    if kind != LINEAGE_RECORD_OPEN:
        entry["file_sha256"] = file_sha256(path)
    if kind == VERSIONED:
        stored = json.loads(Path(path).read_text(encoding="utf-8"))
        entry["record_id"], entry["record_digest"] = dict(stored.get("provenance") or {}).get("record_id"), stored.get("record_digest")
    return entry
