"""P3-199 and P3-204: the ratification record of ``GI_DEVELOPMENT_SNAPSHOT_V1`` and the binding of a run to that EXACT snapshot.

TEST-SIDE, read-only with respect to the runtime: it registers nothing, enables nothing and writes no patient state. The authority registry
(``runtime_authority.APPROVED_SNAPSHOTS``) is not touched: a ratification for DEVELOPMENT EXPERIMENTS is not an authority approval.

Why a binding exists. The shadow layer builds its Amendment-2 witnesses BY NAME (``systemic_consciousness.WITNESSES[name]``), so "the middle
witness" is whatever that dictionary holds when the run starts. A future authority experiment may not depend on a name: it must run the ten
magnitudes of ONE immutable record, and refuse anything else. ``bind`` is that rule:

* the record is identified by its id, its version, its file hash and its two digests, all pinned here;
* the Amendment-2 profile is built from the record's values and from nothing else (no witness name, no default argument);
* the rest of the core profile is the committed default, verified to be the point the pressure approval ``gi_pressure_committed`` pins;
* the live common core must be the lineage member the record names: it is READ (the layer's lineage and the core's own bytes), and a lineage a
  caller offers can only add a refusal, never replace that reading.

Every refusal has a code, so a tamper control is a named outcome and not an exception text.

What is verified is what was BUILT, not only what was offered (the independent review of P3-208 bound a record whose values read one thing
when verified and another when the profile was built): the record is first reduced to plain JSON data, verified in that form, and the profile
built from it must hash to the pinned values digest and to the pinned profile digest. A ``BoundSnapshot`` made by hand is not a binding:
``bound_is_v1`` re-derives every identity from the object and compares it with the constants below.

The limit, said once: these are checks inside one Python process. They refuse a wrong, modified, partial or forged record or object. They cannot
refuse code that rewrites this module's own constants or functions in the same process; that is the layer's job when a binding ever lives there.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import math
import os
from typing import Any, Mapping

import runtime_authority as authority
import runtime_shadow as rs
import runtime_shadow_evidence as ev
import runtime_shadow_families as fam
import test_gi_snapshot_analysis as an
from clinical_core import systemic_consciousness as sc

ROOT = os.path.dirname(os.path.abspath(__file__))
SNAPSHOT_FILE = an.SNAPSHOT_FILE
RATIFICATION_FILE = "docs/revision/GI_DEVELOPMENT_SNAPSHOT_V1_RATIFICATION.json"

#: The identity of version 1, pinned. A record that does not carry exactly these is not the snapshot.
V1_ID = "GI_DEVELOPMENT_SNAPSHOT_V1"
V1_VERSION = 1
V1_FILE_SHA256 = "d9de4800075e2e5bb7e6e445ec0dc9a5d672f53c54212a56cc2f41b9392d4803"
V1_IDENTITY_DIGEST = "1f292d014255ac968ddc3217400635ca64d22462852056c23bb91850d0d6ec40"
V1_RECORD_DIGEST = "9e258ab5b3790a5abb30053b30dd40fd0755918673bc4024f9da609fd4f8cdc9"
#: The digest of the ten values alone, so that "a parameter was modified" is told apart from any other change of the record.
V1_VALUES_DIGEST = "d998e1de4719ec5ba2459b8fbacae7e265ee0d03e971c3a5a853d201a282314e"
#: The digest of the WHOLE record, its ``immutability`` block included (``superseded_by`` lives there and no content digest covers it).
V1_FULL_DIGEST = "a5ab1283d504f91e90e441b442f2d2d4d3d88194164eea45026aec47ce02683e"
#: The digest of the ONE core profile the ten values build on the committed default: what a run must be carrying, re-derived from the run.
V1_PROFILE_DIGEST = "c167b45ee0ce6ec29643cba47f2dde3b6eb760a4c6e37f11d3fa7e5e0a8acc89"
#: The digest of the ratification record (P3-199). The ratification is as immutable as the snapshot: another text is another ratification.
V1_RATIFICATION_DIGEST = "123135b3e35c7cb8117ed02600e19b8e44e117e4d58feb2cf0a630cb77f58f64"
V1_CORE_VERSION = "PHASE2_AMENDMENT_2"
V1_CORE_DIGEST = "a0af7d08fec3aaf93606b5635cad9f26980428a5ab8d8f66afb1317bb4586ce2"
PRESSURE_POINT = "gi_pressure_committed"

RATIFIED = "RATIFIED_FOR_DEVELOPMENT_EXPERIMENTS"
RATIFIED_ON = "2026-11-11"
IS_NOT = ("clinical calibration", "production profile", "resident profile", "authority-approved snapshot")

WRONG_SNAPSHOT_ID = "WRONG_SNAPSHOT_ID"
WRONG_VERSION = "WRONG_VERSION"
PARTIAL_SNAPSHOT = "PARTIAL_SNAPSHOT"
MODIFIED_PARAMETER = "MODIFIED_PARAMETER"
WRONG_DIGEST = "WRONG_DIGEST"
WRONG_CORE_LINEAGE = "WRONG_CORE_LINEAGE"
WITNESS_SUBSTITUTED = "WITNESS_SUBSTITUTED_FOR_THE_SNAPSHOT"
NOT_A_DEVELOPMENT_SNAPSHOT = "NOT_A_DEVELOPMENT_SNAPSHOT_RECORD"
NOT_RATIFIED = "NOT_RATIFIED_FOR_DEVELOPMENT_EXPERIMENTS"
PRESSURE_POINT_MISMATCH = "PRESSURE_POINT_MISMATCH"
REFUSALS = (WRONG_SNAPSHOT_ID, WRONG_VERSION, PARTIAL_SNAPSHOT, MODIFIED_PARAMETER, WRONG_DIGEST, WRONG_CORE_LINEAGE, WITNESS_SUBSTITUTED,
            NOT_A_DEVELOPMENT_SNAPSHOT, NOT_RATIFIED, PRESSURE_POINT_MISMATCH)


class SnapshotBindingError(ValueError):
    """The record offered is not ``GI_DEVELOPMENT_SNAPSHOT_V1`` as ratified: ``reasons`` lists every refusal code."""

    def __init__(self, reasons):
        self.reasons = tuple(reasons)
        super().__init__(f"snapshot binding refused: {list(self.reasons)}")


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def plain(value: Any) -> Any:
    """The value as plain JSON data (exact ``dict`` / ``list`` / ``str`` / ``int`` / ``float`` / ``bool`` / ``None``), or None when it is not JSON.

    A record is verified and used in THIS form only. A mapping or a number of another class can answer one thing to the verification and another
    to the construction (P3-208, attack 1); after this reduction there is one answer, and it is the one both read."""
    try:
        return json.loads(json.dumps(value, allow_nan=False))
    except Exception:
        return None


def live_lineage() -> dict:
    """The lineage member the live common core IS, read from the layer and from the core's own bytes (never from a record)."""
    from clinical_core import amendment_2 as a2
    member = rs.CORE_LINEAGE[-1]
    return {"version_id": member.version_id, "digest": member.digest, "bytes_digest": a2.amended_core_digest_now(),
            "certified": bool(ev.core_lineage_ok())}


def lineage_is_v1(lineage: Any) -> bool:
    """This lineage reading IS the member the snapshot names: its id, its declared digest, the digest of the core's bytes, and certified."""
    try:
        return ((lineage.get("version_id"), lineage.get("digest")) == (V1_CORE_VERSION, V1_CORE_DIGEST)
                and lineage.get("bytes_digest") == V1_CORE_DIGEST and lineage.get("certified") is True)
    except Exception:
        return False


def identity_of(record: Mapping) -> dict:
    lineage = record.get("common_core_lineage") or {}
    return {"snapshot_id": record.get("snapshot_id"), "version": record.get("version"), "values": record.get("values"),
            "common_core_lineage": {"version_id": lineage.get("version_id"), "digest": lineage.get("digest")},
            "region_bounds": record.get("region_bounds")}


def verify_record(record: Any, *, raw: bytes | None = None, lineage: Mapping | None = None) -> list:
    """Every reason this record is NOT the pinned snapshot (an empty list: it is). Never raises.

    ``lineage`` is an ADDITIONAL claim a caller may offer (a tamper control offers a wrong one). The live lineage is always read here, and both
    must be the pinned member: an offered lineage cannot stand in for the reading."""
    reasons: list = []
    record = plain(record)
    if not isinstance(record, dict):
        return [PARTIAL_SNAPSHOT]
    if record.get("snapshot_id") != V1_ID:
        reasons.append(WRONG_SNAPSHOT_ID)
    if record.get("version") != V1_VERSION or isinstance(record.get("version"), bool):
        reasons.append(WRONG_VERSION)
    values = record.get("values")
    complete = (isinstance(values, Mapping) and set(values) == set(sc.FIELDS)
                and all(_is_number(values[name]) for name in sc.FIELDS))
    if not complete:
        reasons.append(PARTIAL_SNAPSHOT)
    else:
        offered = {name: float(values[name]) for name in sc.FIELDS}
        if any(offered == {name: float(value) for name, value in witness.to_dict().items()} for witness in sc.WITNESSES.values()):
            reasons.append(WITNESS_SUBSTITUTED)
    stored = record.get("immutability") if isinstance(record.get("immutability"), Mapping) else {}
    if stored.get("identity_digest") != V1_IDENTITY_DIGEST or stored.get("record_digest") != V1_RECORD_DIGEST \
            or (raw is not None and hashlib.sha256(raw).hexdigest() != V1_FILE_SHA256):
        reasons.append(WRONG_DIGEST)
    if raw is not None:
        try:
            same_as_the_bytes = json.loads(raw.decode("utf-8")) == record
        except Exception:
            same_as_the_bytes = False
        if not same_as_the_bytes and WRONG_DIGEST not in reasons:
            reasons.append(WRONG_DIGEST)              # the bytes offered are not the bytes of the record offered
    try:
        content_identity = an.digest(identity_of(record))
        content_record = an.digest({key: value for key, value in record.items() if key != "immutability"})
    except Exception:
        content_identity = content_record = None
    if complete and an.digest({name: values[name] for name in sc.FIELDS}) != V1_VALUES_DIGEST:
        reasons.append(MODIFIED_PARAMETER)            # one of the ten values is not the ratified one
    try:
        content_full = an.digest(record)
    except Exception:
        content_full = None
    if (content_identity != V1_IDENTITY_DIGEST or content_record != V1_RECORD_DIGEST or content_full != V1_FULL_DIGEST) \
            and WRONG_DIGEST not in reasons:
        reasons.append(WRONG_DIGEST)                  # the content (the immutability block included) is not what this file pins
    declared = record.get("common_core_lineage") if isinstance(record.get("common_core_lineage"), Mapping) else {}
    if (declared.get("version_id"), declared.get("digest")) != (V1_CORE_VERSION, V1_CORE_DIGEST) \
            or not lineage_is_v1(live_lineage()) or (lineage is not None and not lineage_is_v1(lineage)):
        reasons.append(WRONG_CORE_LINEAGE)
    registered = (record.get("authority") or {}).get("registered_as_an_authority_artifact") if isinstance(record.get("authority"), Mapping) else None
    if record.get("status") != an.SNAPSHOT_STATUS or registered is not False:
        reasons.append(NOT_A_DEVELOPMENT_SNAPSHOT)
    return list(dict.fromkeys(reasons))


def verify_ratification(ratification: Any, record: Mapping) -> list:
    """Every reason the ratification offered does not ratify THIS record for development experiments.

    The ratification is the committed record of P3-199, whole: its own digest must be the pinned one and must be the digest of its content. A
    dictionary that merely carries the right fields is not a ratification (P3-208, attack 1)."""
    ratification = plain(ratification)
    if not isinstance(ratification, dict):
        return [NOT_RATIFIED]
    try:
        whole = an.digest({key: value for key, value in ratification.items() if key != "ratification_digest"})
    except Exception:
        whole = None
    ok = (ratification.get("ratification_digest") == V1_RATIFICATION_DIGEST and whole == V1_RATIFICATION_DIGEST
          and ratification.get("status") == RATIFIED and ratification.get("snapshot_id") == V1_ID and ratification.get("version") == V1_VERSION
          and ratification.get("identity_digest") == V1_IDENTITY_DIGEST and ratification.get("record_digest") == V1_RECORD_DIGEST
          and ratification.get("snapshot_file_sha256") == V1_FILE_SHA256 and ratification.get("values") == record.get("values")
          and set(IS_NOT) <= set(ratification.get("is_not") or ())
          and (ratification.get("authority") or {}).get("added_to_an_approved_authority_snapshot_registry") is False)
    return [] if ok else [NOT_RATIFIED]


def pressure_point_matches(profile: Any) -> bool:
    """The base profile is the point the pressure approval pins: same id, same pinned digest, same seven values."""
    approved = authority.APPROVED_SNAPSHOTS.get(PRESSURE_POINT)
    if approved is None or not authority.approved_values_match(PRESSURE_POINT, approved):
        return False
    return all(getattr(profile, name, None) == value for name, value in dict(approved["parameters"]).items())


def profile_digest(profile: Any) -> str:
    return an.digest(dataclasses.asdict(profile))


@dataclasses.dataclass(frozen=True)
class BoundSnapshot:
    """A verified ``GI_DEVELOPMENT_SNAPSHOT_V1`` and the ONE core profile built from it. Frozen against ordinary assignment only: Python can still
    build one by hand or force an attribute, so no consumer trusts the object -- each re-checks it with ``bound_is_v1``."""

    snapshot_id: str
    version: int
    values: tuple
    identity_digest: str
    record_digest: str
    file_sha256: str
    core_version: str
    core_digest: str
    pressure_point: str
    profile: Any
    profile_digest: str

    def value_map(self) -> dict:
        return dict(self.values)

    def summary(self) -> dict:
        return {"snapshot_id": self.snapshot_id, "version": self.version, "values": self.value_map(), "identity_digest": self.identity_digest,
                "record_digest": self.record_digest, "file_sha256": self.file_sha256, "core_version": self.core_version,
                "core_digest": self.core_digest, "pressure_point": self.pressure_point, "profile_digest": self.profile_digest}


def build_profile(values: Mapping[str, float]):
    """The core profile of the pair: the committed default (the pressure approval's point) plus ONE field, ``amendment_2``, built from the
    record's ten values. No witness name and no default argument is read: ``sc.development_profile()`` is never called."""
    base = fam._bundle_profile(fam.COMMITTED)
    if base.amendment_2 is not None:
        raise SnapshotBindingError([PRESSURE_POINT_MISMATCH])
    amendment = sc.Amendment2Profile(**{name: float(values[name]) for name in sc.FIELDS})
    return dataclasses.replace(base, amendment_2=amendment)


def bind(root: str = ROOT, *, record: Any = None, raw: bytes | None = None, ratification: Any = None,
         lineage: Mapping | None = None) -> BoundSnapshot:
    """Bind to the exact ratified snapshot, or raise ``SnapshotBindingError`` with every refusal code.

    With no ``record`` the committed file is read and its raw bytes are hashed. A ``record`` given by the caller is reduced to plain data and
    verified by its whole content (and by ``raw``, which must be the bytes of that same record); the profile built from it is then verified
    against the pinned digests. ``lineage`` can only add a refusal."""
    if record is None:
        with open(os.path.join(root, SNAPSHOT_FILE), "rb") as handle:
            raw = handle.read()
        record = json.loads(raw.decode("utf-8"))
    if ratification is None:
        try:
            with open(os.path.join(root, RATIFICATION_FILE), encoding="utf-8") as handle:
                ratification = json.load(handle)
        except (OSError, ValueError):
            ratification = None
    record = plain(record)                              # one plain copy: what is verified below is what the profile is built from
    reasons = verify_record(record, raw=raw, lineage=lineage)
    if not reasons:
        reasons += verify_ratification(ratification, record)
    if reasons:
        raise SnapshotBindingError(reasons)
    profile = build_profile(record["values"])
    if not pressure_point_matches(profile):
        raise SnapshotBindingError([PRESSURE_POINT_MISMATCH])
    bound = BoundSnapshot(V1_ID, V1_VERSION, tuple((name, float(record["values"][name])) for name in sc.FIELDS), V1_IDENTITY_DIGEST,
                          V1_RECORD_DIGEST, V1_FILE_SHA256, V1_CORE_VERSION, V1_CORE_DIGEST, PRESSURE_POINT, profile, profile_digest(profile))
    if not bound_is_v1(bound):                          # what was BUILT is checked, not only what was offered
        raise SnapshotBindingError([MODIFIED_PARAMETER])
    return bound


def bound_is_v1(bound: Any) -> bool:
    """This object IS a binding to version 1: every identity it carries and the profile it holds are re-derived and compared with the pinned
    constants. A ``BoundSnapshot`` built by hand with other values, or edited after the binding, is not one."""
    try:
        amendment = bound.profile.amendment_2
        return (type(bound) is BoundSnapshot and type(amendment) is sc.Amendment2Profile
                and (bound.snapshot_id, bound.version, bound.identity_digest, bound.record_digest, bound.file_sha256, bound.core_version,
                     bound.core_digest, bound.pressure_point) == (V1_ID, V1_VERSION, V1_IDENTITY_DIGEST, V1_RECORD_DIGEST, V1_FILE_SHA256,
                                                                  V1_CORE_VERSION, V1_CORE_DIGEST, PRESSURE_POINT)
                and an.digest(plain(dict(bound.values))) == V1_VALUES_DIGEST and an.digest(plain(amendment.to_dict())) == V1_VALUES_DIGEST
                and bound.profile_digest == V1_PROFILE_DIGEST and profile_digest(bound.profile) == V1_PROFILE_DIGEST
                and pressure_point_matches(bound.profile))
    except Exception:
        return False


class BoundSnapshotAdapter(fam.GiHaemorrhageAdapter):
    """The GI mapping with the profile of a BOUND snapshot: a development adapter, never registered, that carries no witness name."""

    def __init__(self, bound: BoundSnapshot):
        if not bound_is_v1(bound):
            raise SnapshotBindingError([WRONG_SNAPSHOT_ID])
        self.bound = bound
        self.amendment_2_witness = None
        self.version = f"{fam.GiHaemorrhageAdapter.version}+bound/{bound.snapshot_id}"

    def region_witnesses(self) -> dict:
        return {}

    def profile(self, point: str):
        if point != fam.COMMITTED:
            raise SnapshotBindingError([PRESSURE_POINT_MISMATCH])
        return self.bound.profile

    def snapshot(self, point: str = fam.COMMITTED):
        return fam.ShadowParameterSnapshot(
            f"bound::{self.bound.snapshot_id}", self.family, fam.COMMITTED,
            ("clinical_core.legacy_adapter: the arrival and the haemorrhage module are read from the case",
             f"clinical_core.derived.DEFAULT_PROFILE: the committed default profile (the point {self.bound.pressure_point} pins)",
             f"amendment_2 built ONLY from {SNAPSHOT_FILE}: identity {self.bound.identity_digest}, record {self.bound.record_digest}",
             f"common core {self.bound.core_version} {self.bound.core_digest}",
             "a development snapshot ratified for development experiments: not an authority approval and not clinical truth"))


def open_bound_runner(bound: BoundSnapshot, case_id: str, state: Mapping | None):
    """One shadow run of the encounter under the bound snapshot, through the layer's ONE execution primitive."""
    return fam.ShadowPhysiologyRunner.open("gi_bleed", case_id, state=state, adapter=BoundSnapshotAdapter(bound),
                                           scenario_id=f"bound::{bound.snapshot_id}")


def runner_is_bound(runner: Any, bound: BoundSnapshot) -> bool:
    """The run in hand IS version 1's: the binding is version 1 (``bound_is_v1``), the run carries that binding, and the profile the run would
    integrate with hashes to the PINNED digests -- not merely to whatever the binding object says."""
    try:
        return (bound_is_v1(bound) and type(runner.adapter) is BoundSnapshotAdapter and runner.adapter.bound is bound
                and runner.profile == bound.profile and profile_digest(runner.profile) == V1_PROFILE_DIGEST
                and type(runner.profile.amendment_2) is sc.Amendment2Profile
                and an.digest(plain(runner.profile.amendment_2.to_dict())) == V1_VALUES_DIGEST)
    except Exception:
        return False


# -- P3-199: the ratification record ---------------------------------------------------------------------------------------------------------

FACULTY_DECISIONS = {
    "FD-AUTH-01": "Ratify GI_DEVELOPMENT_SNAPSHOT_V1 for DEVELOPMENT EXPERIMENTS. Status RATIFIED_FOR_DEVELOPMENT_EXPERIMENTS. Not a clinical calibration, a "
                  "production profile, a resident profile or an authority-approved snapshot. Preserve LOW, V1 and HIGH as sensitivity witnesses; do not replace "
                  "the underlying development region with V1.",
    "FD-AUTH-02": ["it satisfies the predeclared H1-H7 criteria", "it is interior to every approved parameter region", "it maximizes the minimum boundary margin",
                   "no legacy output was used in the selection rule",
                   "CENTER_REFERENCE was not automatically selected and in fact violates one region-bound criterion",
                   "causal ordering is stable across both GI cases", "recovery semantics satisfy FD-P3-176"],
    "FD-AUTH-03": "No authority yet: COMMON_CORE_RUNTIME_AUTHORITY stays False and no common-core output writes into the real encounter.",
}
REOPENING_RULE = "Snapshot selection is not reopened unless a cycle finds a new structural contradiction (FD-AUTH-02)."


def build_ratification(root: str = ROOT) -> dict:
    """The ratification of version 1, built from the committed record (which stays untouched) and from the registry as it is today."""
    with open(os.path.join(root, SNAPSHOT_FILE), "rb") as handle:
        raw = handle.read()
    record = json.loads(raw.decode("utf-8"))
    reasons = verify_record(record, raw=raw)
    if reasons:
        raise SnapshotBindingError(reasons)
    profile = build_profile(record["values"])
    kept = record["witnesses_preserved_for_ongoing_sensitivity_checks"]
    body = {
        "record_type": "GI_DEVELOPMENT_SNAPSHOT_RATIFICATION", "snapshot_id": V1_ID, "version": V1_VERSION, "status": RATIFIED,
        "ratified_for": "DEVELOPMENT EXPERIMENTS", "ratified_on": RATIFIED_ON, "is_not": list(IS_NOT),
        "faculty_decisions": FACULTY_DECISIONS, "reopening_rule": REOPENING_RULE,
        "snapshot_file": SNAPSHOT_FILE, "snapshot_file_sha256": V1_FILE_SHA256, "identity_digest": V1_IDENTITY_DIGEST, "record_digest": V1_RECORD_DIGEST,
        "values": record["values"], "amendment": record["amendment"],
        "common_core_lineage": {"version_id": V1_CORE_VERSION, "digest": V1_CORE_DIGEST},
        "selection_criteria": record["selection"]["criteria"], "selection_rule": record["selection"]["rule"],
        "boundary_margins": record["margins_to_the_region_bounds"], "min_margin": record["min_margin"], "region_bounds": record["region_bounds"],
        "sensitivity_witnesses": {"LOW": kept["LOW"], "V1": V1_ID, "HIGH": kept["HIGH"],
                                  "region_not_replaced_by_the_point": True,
                                  "note": "LOW and HIGH are the core's own witnesses, unchanged. CENTER_REFERENCE stays a test witness of the layer and "
                                          "is not the snapshot. The sweep of the full region stays the sensitivity check.",
                                  "event_times_not_bounded_by_the_witnesses_minutes": kept["event_times_not_bounded_by_the_witnesses_minutes"]},
        "uncertainty": record["uncertainty"], "falsifiers": record["falsifiers"],
        "binding": {"bound_profile_digest": profile_digest(profile), "pressure_point": PRESSURE_POINT,
                    "pressure_point_digest": authority.APPROVED_POINT_DIGESTS[PRESSURE_POINT],
                    "profile_built_from": "the committed default profile plus amendment_2 built only from the record's ten values"},
        "authority": {"added_to_an_approved_authority_snapshot_registry": False,
                      "approved_authority_snapshots_today": sorted(authority.APPROVED_SNAPSHOTS),
                      "common_core_runtime_authority": rs.COMMON_CORE_RUNTIME_AUTHORITY},
    }
    return {**body, "ratification_digest": an.digest(body)}


def write_ratification(root: str = ROOT) -> dict:
    ratification = build_ratification(root)
    with open(os.path.join(root, RATIFICATION_FILE), "w", encoding="utf-8") as handle:
        json.dump(ratification, handle, indent=1, sort_keys=True)
    return ratification
