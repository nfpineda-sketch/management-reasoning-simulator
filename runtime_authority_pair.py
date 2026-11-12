"""P3-213, P3-214 and P3-216: the DORMANT pressure + consciousness PAIR authority. Nothing here is reachable as an authority.

Part of the Phase-3 layer (it is named in ``runtime_shadow.LAYER_SOURCES``, so the layer digest covers it). It builds, dormant and certified like the
pressure path was, what the P3-208 review found missing:

* the exact binding to ``GI_DEVELOPMENT_SNAPSHOT_V1`` (P3-214): id, version, file hash, record hash, whole-record hash, values hash, the hash of
  the PROFILE BUILT from them, the common-core lineage and the ratification, with the hardened refusals the review forced. The profile is built from the
  immutable record and from nothing else: no witness name and no default argument;
* the pair transaction (P3-213): ``sbp``, ``dbp``, the display's ``map`` and the consciousness CATEGORY as ONE candidate payload, validated all or
  nothing and committed from ONE prepared mapping into a copy the caller owns. The consciousness half is carried by the explicit overlay of
  ``observable_view`` and NEVER written into ``observable["mental_status"]`` (FD-P3-NEW-02): that field has consumers that are not yet all guarded;
* the interval contract (P3-216): a turn that advances several simulated minutes is validated at EVERY minute of it with the same checks, and its
  ONE commit is the engine's end state. A failure at any minute commits nothing and halts: no later minute of the interval becomes authoritative;
* the dry evaluator the page and the harness call on every route the clock moves (P3-215, P3-217): it never writes, never persists into the encounter
  and never raises into the legacy turn.

What this module does not do: enable an authority, register a snapshot as approved, write into an encounter, expose consciousness to a resident, touch
scoring or terminate anything. ``AuthorityTransaction.commit`` is re-used and re-evaluates the nine-condition gate, so the pair cannot commit where the
pressure transaction cannot: with the flag off and no approved snapshot (today, always) it raises ``AuthorityRefused``.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import math
import os
from copy import deepcopy
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Sequence

import observable_view as view
import runtime_authority as ra
import runtime_shadow as rs
import runtime_shadow_evidence as ev
import runtime_shadow_families as fam
from clinical_core import legacy_adapter
from clinical_core import systemic_consciousness as sc

MODULE_VERSION = "P3-213/214/215/216"
ROOT = str(Path(__file__).resolve().parent)

# ============================================================================================================================================
# P3-214: the binding to the exact ratified snapshot
# ============================================================================================================================================

SNAPSHOT_FILE = "docs/revision/GI_DEVELOPMENT_SNAPSHOT_V1.json"
RATIFICATION_FILE = "docs/revision/GI_DEVELOPMENT_SNAPSHOT_V1_RATIFICATION.json"
SNAPSHOT_STATUS = "GI_DEVELOPMENT_SNAPSHOT"
#: The identity of version 1, pinned. A record that does not carry exactly these is not the snapshot.
V1_ID = "GI_DEVELOPMENT_SNAPSHOT_V1"
V1_VERSION = 1
V1_FILE_SHA256 = "d9de4800075e2e5bb7e6e445ec0dc9a5d672f53c54212a56cc2f41b9392d4803"
V1_IDENTITY_DIGEST = "1f292d014255ac968ddc3217400635ca64d22462852056c23bb91850d0d6ec40"
V1_RECORD_DIGEST = "9e258ab5b3790a5abb30053b30dd40fd0755918673bc4024f9da609fd4f8cdc9"
#: The digest of the WHOLE record, its ``immutability`` block included (``superseded_by`` lives there and no content digest covers it).
V1_FULL_DIGEST = "a5ab1283d504f91e90e441b442f2d2d4d3d88194164eea45026aec47ce02683e"
#: The digest of the ten values alone, so that "a parameter was modified" is told apart from any other change of the record.
V1_VALUES_DIGEST = "d998e1de4719ec5ba2459b8fbacae7e265ee0d03e971c3a5a853d201a282314e"
#: The digest of the ONE core profile the ten values build on the committed default: what a run must be carrying, re-derived from the run.
V1_PROFILE_DIGEST = "c167b45ee0ce6ec29643cba47f2dde3b6eb760a4c6e37f11d3fa7e5e0a8acc89"
#: The digest of the ratification record (P3-199). The ratification is as immutable as the snapshot: another text is another ratification.
V1_RATIFICATION_DIGEST = "123135b3e35c7cb8117ed02600e19b8e44e117e4d58feb2cf0a630cb77f58f64"
V1_CORE_VERSION = "PHASE2_AMENDMENT_2"
V1_CORE_DIGEST = "a0af7d08fec3aaf93606b5635cad9f26980428a5ab8d8f66afb1317bb4586ce2"
PRESSURE_POINT = "gi_pressure_committed"

RATIFIED = "RATIFIED_FOR_DEVELOPMENT_EXPERIMENTS"
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


def canonical(value: Any) -> str:
    """The canonical text the pinned digests of the snapshot were taken over (sorted keys, no spaces, ASCII)."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("ascii")).hexdigest()


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
    return {"version_id": member.version_id, "digest": member.digest, "bytes_digest": a2.amended_core_digest_now(), "certified": bool(ev.core_lineage_ok())}


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
            "common_core_lineage": {"version_id": lineage.get("version_id"), "digest": lineage.get("digest")}, "region_bounds": record.get("region_bounds")}


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
    complete = isinstance(values, Mapping) and set(values) == set(sc.FIELDS) and all(_is_number(values[name]) for name in sc.FIELDS)
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
        content_identity = digest(identity_of(record))
        content_record = digest({key: value for key, value in record.items() if key != "immutability"})
    except Exception:
        content_identity = content_record = None
    if complete and digest({name: values[name] for name in sc.FIELDS}) != V1_VALUES_DIGEST:
        reasons.append(MODIFIED_PARAMETER)            # one of the ten values is not the ratified one
    try:
        content_full = digest(record)
    except Exception:
        content_full = None
    if (content_identity != V1_IDENTITY_DIGEST or content_record != V1_RECORD_DIGEST or content_full != V1_FULL_DIGEST) and WRONG_DIGEST not in reasons:
        reasons.append(WRONG_DIGEST)                  # the content (the immutability block included) is not what this layer pins
    declared = record.get("common_core_lineage") if isinstance(record.get("common_core_lineage"), Mapping) else {}
    if (declared.get("version_id"), declared.get("digest")) != (V1_CORE_VERSION, V1_CORE_DIGEST) \
            or not lineage_is_v1(live_lineage()) or (lineage is not None and not lineage_is_v1(lineage)):
        reasons.append(WRONG_CORE_LINEAGE)
    registered = (record.get("authority") or {}).get("registered_as_an_authority_artifact") if isinstance(record.get("authority"), Mapping) else None
    if record.get("status") != SNAPSHOT_STATUS or registered is not False:
        reasons.append(NOT_A_DEVELOPMENT_SNAPSHOT)
    return list(dict.fromkeys(reasons))


def verify_ratification(ratification: Any, record: Mapping) -> list:
    """Every reason the ratification offered does not ratify THIS record for development experiments. The ratification is the committed record of
    P3-199, whole: its own digest must be the pinned one and must be the digest of its content (a dictionary that merely carries the right fields is
    not a ratification)."""
    ratification = plain(ratification)
    if not isinstance(ratification, dict):
        return [NOT_RATIFIED]
    try:
        whole = digest({key: value for key, value in ratification.items() if key != "ratification_digest"})
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
    """The base profile is the point the pressure approval pins: same id, same pinned digest, same values."""
    approved = ra.APPROVED_SNAPSHOTS.get(PRESSURE_POINT)
    if approved is None or not ra.approved_values_match(PRESSURE_POINT, approved):
        return False
    return all(getattr(profile, name, None) == value for name, value in dict(approved["parameters"]).items())


def profile_digest(profile: Any) -> str:
    return digest(dataclasses.asdict(profile))


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
    """The core profile of the pair: the committed default (the pressure approval's point) plus ONE field, ``amendment_2``, built from the record's
    ten values. No witness name and no default argument is read: ``sc.development_profile()`` is never called."""
    base = fam._bundle_profile(fam.COMMITTED)
    if base.amendment_2 is not None:
        raise SnapshotBindingError([PRESSURE_POINT_MISMATCH])
    amendment = sc.Amendment2Profile(**{name: float(values[name]) for name in sc.FIELDS})
    return dataclasses.replace(base, amendment_2=amendment)


def bound_is_v1(bound: Any) -> bool:
    """This object IS a binding to version 1: every identity it carries and the profile it holds are re-derived and compared with the pinned
    constants. A ``BoundSnapshot`` built by hand with other values, or edited after the binding, is not one."""
    try:
        amendment = bound.profile.amendment_2
        return (type(bound) is BoundSnapshot and type(amendment) is sc.Amendment2Profile
                and (bound.snapshot_id, bound.version, bound.identity_digest, bound.record_digest, bound.file_sha256, bound.core_version,
                     bound.core_digest, bound.pressure_point) == (V1_ID, V1_VERSION, V1_IDENTITY_DIGEST, V1_RECORD_DIGEST, V1_FILE_SHA256,
                                                                  V1_CORE_VERSION, V1_CORE_DIGEST, PRESSURE_POINT)
                and digest(plain(dict(bound.values))) == V1_VALUES_DIGEST and digest(plain(amendment.to_dict())) == V1_VALUES_DIGEST
                and bound.profile_digest == V1_PROFILE_DIGEST and profile_digest(bound.profile) == V1_PROFILE_DIGEST
                and pressure_point_matches(bound.profile))
    except Exception:
        return False


def bind(root: str = ROOT, *, record: Any = None, raw: bytes | None = None, ratification: Any = None, lineage: Mapping | None = None) -> BoundSnapshot:
    """Bind to the exact ratified snapshot, or raise ``SnapshotBindingError`` with every refusal code.

    With no ``record`` the committed file is read and its raw bytes are hashed. A ``record`` given by the caller is reduced to plain data and verified
    by its whole content (and by ``raw``, which must be the bytes of that same record); the profile built from it is then verified against the pinned
    digests. ``lineage`` can only add a refusal. Nothing is registered, approved or enabled by binding."""
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
    return fam.ShadowPhysiologyRunner.open("gi_bleed", case_id, state=state, adapter=BoundSnapshotAdapter(bound), scenario_id=f"bound::{bound.snapshot_id}")


def runner_is_bound(runner: Any, bound: BoundSnapshot) -> bool:
    """The run in hand IS version 1's: the binding is version 1 (``bound_is_v1``), the run carries that binding, and the profile the run would
    integrate with hashes to the PINNED digests -- not merely to whatever the binding object says."""
    try:
        return (bound_is_v1(bound) and type(runner.adapter) is BoundSnapshotAdapter and runner.adapter.bound is bound
                and runner.profile == bound.profile and profile_digest(runner.profile) == V1_PROFILE_DIGEST
                and type(runner.profile.amendment_2) is sc.Amendment2Profile
                and digest(plain(runner.profile.amendment_2.to_dict())) == V1_VALUES_DIGEST)
    except Exception:
        return False


# ============================================================================================================================================
# P3-213: the pair payload and its transaction
# ============================================================================================================================================

PRESSURE_FIELDS = ("sbp", "dbp", "map")
#: The consciousness half of the payload: the CATEGORY (the common core's own reading), the legacy-ladder WORD of that category, and the pulse.
CONSCIOUSNESS_FIELDS = ("consciousness_category", "mental_status", "pulse_present")
PAIR_FIELDS = PRESSURE_FIELDS + CONSCIOUSNESS_FIELDS
#: Where each field lands. The live ``mental_status`` is deliberately absent: FD-P3-NEW-02 allows the common physiology to represent the state and
#: does NOT authorize writing it into the legacy live field.
OBSERVABLE_WRITES = ("sbp", "dbp", "map")
OVERLAY_WRITES = ("consciousness_category", "mental_status", "pulse_present")
NEVER_WRITTEN = ("hr", "spo2", "respiratory_rate", "crt", "rhythm", "pulse_present_live", "lactate", "hemoglobin", "collapse_state", "mental_status_live")
#: The legacy word of each common category: the inverse of the certified comparison's own table.
WORD_OF = MappingProxyType({level: word for word, level in legacy_adapter.LEVEL_OF.items()})
ESTABLISHED = 2

PAIR_PREPARED, PAIR_VALIDATED, PAIR_COMMITTED, PAIR_ABORTED = ra.PREPARED, ra.VALIDATED, ra.COMMITTED, ra.ABORTED

PAIR_CHECKS = ("pressure_half_validated", "consciousness_candidate_present", "category_on_the_ladder", "word_is_the_category", "pulse_not_contradicted",
               "pair_is_one_course", "interval_minutes_validated", "collapse_boundary_not_reached", "window_open", "snapshot_is_v1",
               "payload_is_the_pair_and_nothing_else", "legacy_mental_status_untouched")


@dataclasses.dataclass(frozen=True)
class PairPayload:
    """ONE candidate: the pressures and the consciousness reading of ONE minute of ONE common-core run. Immutable, and digested as a whole."""

    minute: int
    sbp: float
    dbp: float
    map: int
    consciousness_category: int
    mental_status: str
    pulse_present: bool

    def as_dict(self) -> dict:
        return {name: getattr(self, name) for name in ("minute",) + PAIR_FIELDS}

    def digest(self) -> str:
        return ra.digest_of(self.as_dict())


def payload_problems(payload: Any) -> list:
    """Every reason a payload is not a complete, well-typed pair (an empty list: it is). The pair is complete or it is not a payload."""
    if not isinstance(payload, PairPayload):
        return ["not_a_pair_payload"]
    problems = []
    for name in ("sbp", "dbp"):
        value = getattr(payload, name)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            problems.append(f"{name}_not_a_finite_number")
    if isinstance(payload.map, bool) or not isinstance(payload.map, int):
        problems.append("map_not_an_integer")
    elif not [item for item in problems if item.endswith("_not_a_finite_number")] and ra.derived_map(payload.sbp, payload.dbp) != payload.map:
        problems.append("map_is_not_the_display_mean_of_the_pair")
    if type(payload.consciousness_category) is not int or payload.consciousness_category not in WORD_OF:
        problems.append("category_not_on_the_ladder")                 # an exact int: 3.0 and True are not rungs of the ladder
    elif WORD_OF[payload.consciousness_category] != payload.mental_status:
        problems.append("word_is_not_the_category")
    if not isinstance(payload.pulse_present, bool):
        problems.append("pulse_not_a_boolean")
    return problems


def payload_from(minute: int, pressures: Mapping, consciousness: Mapping) -> PairPayload:
    """Build the payload from the pressure point (already shaped like the legacy display) and the consciousness reading of the SAME minute."""
    category = consciousness.get("category")
    return PairPayload(minute=int(minute), sbp=pressures.get("sbp"), dbp=pressures.get("dbp"),
                       map=ra.derived_map(pressures.get("sbp"), pressures.get("dbp")),
                       consciousness_category=category, mental_status=WORD_OF.get(category), pulse_present=consciousness.get("pulse_present"))


class PairAuthorityTransaction:
    """One minute of a future pair experiment: capture, compute, validate, commit or abort -- ALL FIELDS OR NONE.

    It composes the existing ``AuthorityTransaction`` for the pressure half and adds the consciousness and pairing checks. Atomicity, by construction:

    * ``validate`` passes only if the pressure half AND every pair check pass; if anything fails the inner pressure transaction is ABORTED too, so
      there is no pressure-only commit to reach and no consciousness-only one;
    * ``commit`` re-evaluates the nine-condition gate (through the pressure transaction), builds ONE prepared mapping -- the three pressures in
      ``observable`` and the overlay at the state's top level -- and returns it. The caller's state is never touched; any error leaves the pair
      ABORTED with nothing returned;
    * the live ``mental_status`` is never written, and a payload that is not exactly the pair is refused.
    """

    def __init__(self, *, minute: int, case_id: str, snapshot: Mapping | None, bound: BoundSnapshot | None = None):
        self.minute, self.case_id, self.bound = int(minute), str(case_id), bound
        self._pressure = ra.AuthorityTransaction(minute=self.minute, case_id=self.case_id, snapshot=snapshot)
        self.state = PAIR_PREPARED
        self.failures: list = []
        self.reason = ""
        self.payload: PairPayload | None = None
        self.committed: tuple = ()
        self.before: Mapping | None = None

    # -- stages ----------------------------------------------------------------------------------------------------------------------------
    def capture(self, authoritative: Mapping) -> "PairAuthorityTransaction":
        self.before = deepcopy(dict(authoritative))
        self._pressure.capture(authoritative)
        return self

    def compute(self, payload: PairPayload, legacy_pressure: Mapping | None = None) -> "PairAuthorityTransaction":
        self.payload = payload
        written = None if not isinstance(payload, PairPayload) else {"sbp": payload.sbp, "dbp": payload.dbp, "map": payload.map}
        self._pressure.compute(written or {}, legacy_pressure)
        return self

    def validate(self, *, pressure: Mapping, consciousness_ok: Mapping, interval_ok: bool, boundary_clear: bool, window_open: bool,
                 one_course: bool) -> bool:
        """``pressure`` are the keyword arguments of ``AuthorityTransaction.validate``; the other arguments are the pair's own conditions, each a
        boolean the evaluator proved from the run (this method only combines them: it computes no physiology)."""
        if self.state != PAIR_PREPARED:
            # P3-219 review, F5: ABORTED and COMMITTED are terminal. A pair that was refused cannot be re-validated with better arguments and committed.
            raise ra.AuthorityRefused(f"a pair validates once, from {PAIR_PREPARED}: this one is {self.state}")
        checks = {}
        try:
            pressure_ok = bool(self._pressure.validate(**dict(pressure)))
        except Exception:
            pressure_ok = False
        checks["pressure_half_validated"] = pressure_ok
        problems = payload_problems(self.payload)
        checks["consciousness_candidate_present"] = isinstance(self.payload, PairPayload) and self.payload.consciousness_category is not None
        checks["category_on_the_ladder"] = not [item for item in problems if item.startswith("category")]
        checks["word_is_the_category"] = "word_is_not_the_category" not in problems and isinstance(self.payload, PairPayload) \
            and self.payload.mental_status in view.WORDS
        checks["pulse_not_contradicted"] = isinstance(self.payload, PairPayload) and isinstance(self.payload.pulse_present, bool) \
            and self.payload.pulse_present is True                    # the common word may be 'Unresponsive' WITH a pulse; an arrest is not this pair
        checks["pair_is_one_course"] = bool(one_course)
        checks["interval_minutes_validated"] = bool(interval_ok)
        checks["collapse_boundary_not_reached"] = bool(boundary_clear)
        checks["window_open"] = bool(window_open)
        checks["snapshot_is_v1"] = self.bound is not None and bound_is_v1(self.bound)
        checks["payload_is_the_pair_and_nothing_else"] = not [item for item in problems if not item.startswith("category") and item != "word_is_not_the_category"] \
            and isinstance(self.payload, PairPayload)
        checks["legacy_mental_status_untouched"] = "mental_status" not in OBSERVABLE_WRITES
        self.failures = [name for name in PAIR_CHECKS if not checks.get(name, False)]
        if self.failures:
            self._abort(f"pair validation refused: {self.failures}")
            return False
        self.state = PAIR_VALIDATED
        return True

    def commit(self, target: Mapping, *, environ: Mapping[str, str] | None = None, owner: str | None = None) -> dict:
        """Write the pair at once into a COPY of ``target`` and return it, or raise ``AuthorityRefused`` with nothing written."""
        try:
            if self.state != PAIR_VALIDATED:
                raise ra.AuthorityRefused(self.reason or "a pair commits only after every pair check passed")
            if not isinstance(self.payload, PairPayload) or payload_problems(self.payload):
                raise ra.AuthorityRefused(f"the payload is not a complete pair: {payload_problems(self.payload)}")
            if self.bound is None or not bound_is_v1(self.bound):
                raise ra.AuthorityRefused("the pair is not bound to GI_DEVELOPMENT_SNAPSHOT_V1")
            prepared = self._pressure.commit(target, environ=environ)               # gate re-evaluated here; the pressures, in a NEW mapping
            observable = dict(prepared.get("observable") or {})
            if (observable.get("sbp"), observable.get("dbp")) != (self.payload.sbp, self.payload.dbp):
                raise ra.AuthorityRefused("the prepared pressures are not the pair's pressures")
            overlay = {"owner": str(owner or f"pair:{self.case_id}:{self.minute}:{self.payload.digest()[:16]}"), "minute": self.minute,
                       "views": {}, "common": {"consciousness_category": self.payload.consciousness_category,
                                               "mental_status": self.payload.mental_status, "pulse_present": self.payload.pulse_present},
                       "legacy": {}, "mapped_into_live_field": False}
            problems = view.overlay_problems(overlay) + view.mapping_problems(overlay)
            if problems:
                raise ra.AuthorityRefused(f"the overlay is not a view: {problems}")
            if "mental_status" in (self._moved_keys(target, observable)):
                raise ra.AuthorityRefused("the live mental_status would move: FD-P3-NEW-02 forbids it")
            prepared[view.OVERLAY_KEY] = overlay
            if dict(prepared.get("observable") or {}).get("mental_status") != dict(target.get("observable") or {}).get("mental_status"):
                raise ra.AuthorityRefused("the live mental_status moved")
        except Exception as error:
            self._abort(self.reason or str(error))
            if isinstance(error, ra.AuthorityRefused):
                raise
            raise ra.AuthorityRefused(f"pair commit failed and nothing was written: {error!r}") from error
        self.committed = PAIR_FIELDS
        self.state = PAIR_COMMITTED
        return prepared

    @staticmethod
    def _moved_keys(target: Mapping, observable: Mapping) -> set:
        before = dict(target.get("observable") or {})
        return {key for key in set(before) | set(observable) if ra.canonical(before.get(key)) != ra.canonical(observable.get(key))}

    def _abort(self, reason: str) -> None:
        self.state = PAIR_ABORTED
        self.reason = reason
        self.committed = ()
        # the inner transaction can no longer be committed on its own: there is no pressure-only partial commit
        self._pressure.state = ra.ABORTED
        self._pressure.committed = ()
        if not self._pressure.reason:
            self._pressure.reason = reason

    def abort(self, reason: str) -> dict:
        self._abort(reason)
        return self.record()

    def record(self) -> dict:
        return {"module": MODULE_VERSION, "state": self.state, "minute": self.minute, "case_id": self.case_id, "payload": None if self.payload is None else self.payload.as_dict(),
                "payload_digest": None if self.payload is None else self.payload.digest(), "validation_failures": list(self.failures), "reason": self.reason,
                "committed": list(self.committed), "pressure_half": self._pressure.record(),
                "common_core_runtime_authority": rs.COMMON_CORE_RUNTIME_AUTHORITY, "writes_the_live_mental_status": False}


# ============================================================================================================================================
# P3-215 / P3-216 / P3-217: the dry evaluator on EVERY route the clock moves, at the granularity of the state evolution
# ============================================================================================================================================

DRY_RUN_VERSION = "P3-216/217"
#: FD-AUTH-07: the predefined experimental time limit. The window ends at min(this, the first established-collapse boundary).
TIME_LIMIT_MIN = 240
WOULD_COMMIT, WOULD_ABORT, HALTED = "WOULD_COMMIT", "WOULD_ABORT", "EXPERIMENT_HALTED"
#: A turn that did not advance the clock and carried only structural or acknowledged-no-physiology actions: there is no new minute, so no commit and no abort.
NO_ADVANCE = "NO_ADVANCE_TURN"
NOT_STARTED, ACTIVE = "NOT_STARTED", "ACTIVE"
#: The routes by which the engine's clock moves in the page (P3-215 inventory). Both are covered; an unknown route is refused.
ORDER_TURN, CLINICAL_TIME = ra.ORDER_TURN, ra.CLINICAL_TIME
KNOWN_ROUTES = ra.KNOWN_ROUTES
#: The two granularities P3-216 weighs, and the one chosen (proof in docs/PHASE3_DORMANT_PAIR_AUTHORITY.md §6).
PER_MINUTE_TRANSACTION, VALIDATED_ATOMIC_INTERVAL = "PER_MINUTE_TRANSACTION", "VALIDATED_ATOMIC_INTERVAL"
GRANULARITY = VALIDATED_ATOMIC_INTERVAL
#: The readings of one common state that do NOT depend on the Amendment-2 magnitudes: equal in the pressure run and in the bound run, or the pair is
#: not one course.
SHARED_READINGS = tuple(name for name in fam.TRACE_READINGS if name != "consciousness_level")
DRY_FLAG = "MRS_PHASE3_PAIR_DRY_RUN"
DRY_ON = "on"

CHECKS = ("transaction_completed", "encounter_state_untouched", "turn_has_a_transaction_site", "turn_was_observed", "pair_domain_unchanged", "lineage_certified", "snapshot_bound",
          "case_eligible", "supported_management", "minute_not_already_committed", "pressure_candidate_present", "pressure_validated",
          "consciousness_candidate_present", "consciousness_reproducible", "pair_is_one_course", "interval_minutes_validated",
          "collapse_boundary_not_reached", "window_open", "common_run_did_not_fail", "only_the_pair_would_move")


def dry_run_enabled(environ: Mapping[str, str] | None = None) -> bool:
    """The dry evaluation is off unless a developer turns it on, AND the shadow runs: it needs the common run it evaluates."""
    live = os.environ if environ is None else environ
    return str(live.get(DRY_FLAG, "") or "").strip().lower() == DRY_ON and rs.mode(environ=live) != rs.MODE_OFF


def _as_int(value: Any) -> int:
    try:
        return int(value or 0)
    except Exception:
        return 0


def _digest(value: Any) -> str | None:
    try:
        return ra.digest_of(value)
    except Exception:
        return None


def _plain(value: Any) -> Any:
    try:
        return json.loads(json.dumps(value))
    except Exception:
        return repr(value)


def _anchors_digest(runner: Any) -> str | None:
    try:
        return ra.digest_of(dataclasses.asdict(runner.anchors))
    except Exception:
        return None


def moved_fields(before: Mapping, after: Mapping) -> tuple:
    """``(outside, observable)``: the top-level keys OTHER than ``observable`` that differ, and the observable keys that differ -- BOTH, always.

    ``AuthoritySite._moved`` returns only the outside keys when there are any, which would hide an observable field that moved beside the overlay."""
    left, right = dict(before), dict(after)
    outside = {key for key in set(left) | set(right) if key != "observable" and ra.canonical(left.get(key)) != ra.canonical(right.get(key))}
    one, two = dict(left.get("observable") or {}), dict(right.get("observable") or {})
    return outside, {key for key in set(one) | set(two) if ra.canonical(one.get(key)) != ra.canonical(two.get(key))}


def legacy_point(observable: Mapping) -> dict:
    """What the legacy engine shows for the pair at this minute (the resident's truth; read, never written)."""
    sbp, dbp = observable.get("sbp"), observable.get("dbp")
    return {"sbp": sbp, "dbp": dbp, "map": ra.derived_map(sbp, dbp), "mental_status": observable.get("mental_status"), "pulse_present": observable.get("pulse_present", True)}


class PairDryEvaluator:
    """The dry pair transaction of ONE encounter. ``minute`` is called where an authority site's minute would be: after the engine moved the clock and the
    shadow observed it, on EVERY route (``ORDER_TURN`` and ``CLINICAL_TIME``). It never commits, never writes and never raises into the caller."""

    def __init__(self, bound: BoundSnapshot, case_id: str, arrival_state: Mapping, *, time_limit: int = TIME_LIMIT_MIN, lineage: Mapping | None = None):
        if not bound_is_v1(bound):
            raise SnapshotBindingError([WRONG_SNAPSHOT_ID])
        #: FD-AUTH-07: the predefined limit is the ceiling. A caller may shorten the window, never lengthen it.
        self.bound, self.case_id, self.time_limit = bound, str(case_id), max(0, min(int(time_limit), TIME_LIMIT_MIN))
        self.runner = open_bound_runner(bound, case_id, deepcopy(dict(arrival_state)))
        self.pressure_snapshot = ra.approved_snapshot(PRESSURE_POINT, environment="development", family=ra.AUTHORITY_FAMILY, case_id=self.case_id,
                                                      domain=ra.AUTHORITY_DOMAIN)
        #: A lineage the caller OFFERS (a tamper control offers a wrong one). It can only add a refusal: the live lineage is read every minute.
        self.offered_lineage = None if lineage is None else dict(lineage)
        self.lineage = live_lineage()
        self.records: list = []
        self.would_commit: list = []
        self.violations: list = []
        self.phase = NOT_STARTED
        self.halt: dict | None = None
        self._cleared_through = 0
        self._channels: dict = {}
        self._last_seen = _as_int(dict(arrival_state).get("sim_time"))
        self._failures_seen = 0
        self._anchors = _anchors_digest(self.runner)

    # -- the common candidate under the bound snapshot -------------------------------------------------------------------------------------
    def _advance(self, session, minute: int) -> None:
        if self.runner is None:
            return
        self.runner.mirror(session.mirrored)
        self.runner.advance(minute, state=session._mapping_state())
        if self.runner.failures:
            return
        for row in fam.run_channels(self.runner):
            self._channels[row["minute"]] = row

    def _candidate(self, minute: int) -> dict | None:
        row = self._channels.get(minute)
        if row is None or self.runner is None:
            return None
        result = next((item for item in reversed(self.runner.results) if item.minute == minute), None)
        channels = row["channels"]
        category = channels.get("category_index")
        return {"reproduced": "channels_unavailable" not in row, "derived": None if result is None else dict(result.derived), "category": category,
                "consciousness_level": channels.get("consciousness_level"), "mental_status": WORD_OF.get(category), "F": channels.get("systemic_encephalopathy_burden"),
                "collapse_burden": channels.get("collapse_burden"), "collapse_state": channels.get("collapse_state_index"),
                "relative_delivery": channels.get("relative_delivery"), "relative_perfusion": channels.get("relative_perfusion"),
                "pulse_present": channels.get("pulse_present"), "state_digest": row.get("state_digest")}

    def _boundary(self, minute: int) -> dict:
        """FD-AUTH-06, precommit: EVERY minute since the last cleared one, up to the minute that would be committed. A minute the run cannot show, or
        whose state is not exactly one of the core's three, is not a cleared minute: the guard fails closed. A minute an earlier turn cleared is not
        read again (a rewritten minute is its own failure), and the boundary is ESTABLISHED collapse, not impending."""
        first, unseen = None, []
        for index in range(self._cleared_through + 1, minute + 1):
            row = self._channels.get(index)
            state = None if row is None or "channels_unavailable" in row else row["channels"].get("collapse_state_index")
            if type(state) is not int or state not in (0, 1, ESTABLISHED):
                unseen.append(index)
            elif state >= ESTABLISHED and first is None:
                first = index
        return {"first_established_minute": first, "minutes_not_shown": unseen, "clear": first is None and not unseen}

    # -- one turn --------------------------------------------------------------------------------------------------------------------------
    def minute(self, before: Mapping | None, after: Mapping, session, ran: Sequence | None, submission_id: Any = None, route: str = ORDER_TURN) -> dict:
        """One advance of the clock. NEVER raises and never touches ``after``: the transaction runs on a copy, an exception inside it is a WOULD_ABORT with
        a record, and the state it was handed is hashed before and after."""
        untouched = _digest(after)
        minute = _as_int(after.get("sim_time")) if isinstance(after, Mapping) else 0
        record = {"minute": minute, "route": route, "legacy": None, "common": None, "would_write": None, "would_move": None, "failed_checks": [], "detail": {},
                  "action_kinds": [], "no_common_physiology": [], "interval": [], "phase_before": self.phase}
        try:
            seen = deepcopy(dict(after))
            legacy_observable = dict(seen.get("observable") or {})
            record["legacy"] = legacy_point(legacy_observable)
            self._advance(session, minute)
            candidate = self._candidate(minute)
            record["common"] = self._shown(candidate)
            if self.halt is not None:
                record.update(verdict=HALTED, reason=f"halted at minute {self.halt['minute']}: {self.halt['failed_checks']}")
            else:
                self._evaluate(record, minute, before, seen, legacy_observable, session, ran, candidate, route)
        except Exception as error:                     # a transaction that raised did not complete: it would not commit, and it is not silent
            self._refuse(record, minute, ["transaction_completed"], {"transaction_completed": f"{type(error).__name__}: {error}"}, "exception")
        if _digest(after) != untouched:
            self.violations.append(f"minute {minute}: the encounter state changed while the dry run evaluated it")
            self._refuse(record, minute, ["encounter_state_untouched"], {"encounter_state_untouched": self.violations[-1]}, "state_guard")
        self._last_seen = minute
        self._failures_seen = len(list(getattr(session, "failures", []) or []))
        record["phase_after"] = self.phase
        record["digest"] = ra.digest_of({key: value for key, value in record.items() if key != "digest"})
        self.records.append(record)
        return record

    def _refuse(self, record: dict, minute: int, failed: Sequence[str], detail: Mapping, stage: str) -> None:
        """Mark this turn refused. The FIRST refusal of an encounter is its halt; a refusal after the halt marks its own record and stays HALTED."""
        names = [name for name in CHECKS if name in set(failed) | set(record.get("failed_checks") or [])]
        record["failed_checks"], record["detail"] = names, {**dict(record.get("detail") or {}), **{key: _plain(value) for key, value in dict(detail).items()}}
        record["would_write"] = None
        if record.get("verdict") == WOULD_COMMIT and minute in self.would_commit:
            self.would_commit.remove(minute)
        self.phase = HALTED
        if self.halt is not None:
            record.update(verdict=HALTED, reason=f"halted at minute {self.halt['minute']}: {self.halt['failed_checks']}; this turn also failed {names}")
            return
        began = bool(self.would_commit)
        record.update(verdict=WOULD_ABORT, reason=f"refused: {names}")
        self.halt = {"minute": minute, "failed_checks": list(names), "authority_had_begun": began, "stage": stage,
                     "consequence": ("the experiment hard-stops; the encounter is INVALID_FOR_CONTINUATION and is never continued with the legacy engine"
                                     if began else "authority never began; the legacy engine simply continues and no experiment exists for this encounter"),
                     "detail": dict(record["detail"])}

    @staticmethod
    def _shown(candidate: Mapping | None) -> dict | None:
        if candidate is None:
            return None
        derived = candidate["derived"] or {}
        return {"sbp": derived.get("sbp"), "dbp": derived.get("dbp"), "category": candidate["category"], "mental_status": candidate["mental_status"],
                "F": candidate["F"], "collapse_burden": candidate["collapse_burden"], "collapse_state": candidate["collapse_state"],
                "relative_delivery": candidate["relative_delivery"], "relative_perfusion": candidate["relative_perfusion"], "pulse_present": candidate["pulse_present"]}

    # -- the interval: EVERY minute of the turn, with the same checks (P3-216) -----------------------------------------------------------------
    @staticmethod
    def _replay_table(replay_input: Mapping | None) -> dict | None:
        """The pressures of EVERY minute of the artifact's replay, computed once: ``{minute: pressure_point}``. ``None`` when there is no artifact to replay.
        (Replaying the whole run once per minute of a turn made the dry evaluation quadratic: P3-219 review, F8.)"""
        if not replay_input:
            return None
        replayed = fam.replay_shadow_encounter(json.loads(ra.canonical(replay_input)))
        return {_as_int(item["minute"]): ra.pressure_point(item["derived"]) for item in replayed["results"]}

    def _interval(self, minute: int, session, unsupported: Sequence[str], legacy_arrest: bool, turn_minutes: Sequence[int], table: dict | None = None) -> list:
        """The per-minute validation of ONE turn: for each minute the pressure transaction's own validation (candidate present and finite, reproducible
        from the immutable artifact, no failure recorded at THAT minute, a supported management, no legacy arrest) and the consciousness candidate's
        (on the ladder, the core's own reading, the same course as the pressure run). The legacy comparison is a record, not a safety check, and
        intermediate minutes have none."""
        rows = []
        mine = {_as_int(item.minute): dict(item.derived) for item in (self.runner.results if self.runner is not None else [])}
        theirs = {_as_int(item.minute): item for item in list(getattr(session, "minutes", []) or [])}
        failures_all = list(getattr(session, "failures", []) or [])
        for index in turn_minutes:
            failed, entry = [], theirs.get(index)
            derived = None if entry is None else dict(entry.derived)
            pressure = None if derived is None else ra.pressure_point(derived)
            if pressure is None or any(value is None for value in pressure.values()):
                failed.append("pressure_candidate_present")
            else:
                replayed = None if table is None else table.get(index)
                step = ra.AuthorityTransaction(minute=index, case_id=self.case_id, snapshot=self.pressure_snapshot)
                step.capture({"sim_time": index}).compute(ra.shaped_like_legacy(pressure, {}), None)
                at_this_minute = [item for item in failures_all if _as_int(item.minute) == index]
                ok = step.validate(invariants_hold=not at_this_minute, replay_digest=ra.digest_of(replayed) if replayed is not None else "",
                                   expected_digest=ra.digest_of(pressure), unsupported=tuple(unsupported), legacy_arrest=bool(legacy_arrest),
                                   failures=at_this_minute)
                if not ok:
                    failed.extend(f"pressure:{name}" for name in step.failures)
            row = self._channels.get(index)
            channels = None if row is None or "channels_unavailable" in row else row["channels"]
            if channels is None or channels.get("category_index") not in WORD_OF or channels.get("consciousness_level") != channels.get("category_index"):
                failed.append("consciousness_candidate_present")
            elif channels.get("pulse_present") is not True:
                failed.append("pulse_present")
            if index not in mine or index not in theirs or any(mine[index].get(name) != dict(theirs[index].derived).get(name) for name in SHARED_READINGS):
                failed.append("pair_is_one_course")
            rows.append({"minute": index, "ok": not failed, "failed": failed})
        return rows

    def _evaluate(self, record: dict, minute: int, before: Mapping | None, after: Mapping, legacy_observable: Mapping, session, ran, candidate, route: str) -> None:
        failed, detail = [], {}

        def check(name: str, ok: bool, why: Any = None) -> bool:
            if not ok:
                failed.append(name)
                if why is not None:
                    detail[name] = why
            return bool(ok)

        check("turn_has_a_transaction_site", route in KNOWN_ROUTES, {"route": route})
        started = _as_int(before.get("sim_time")) if isinstance(before, Mapping) else None
        check("turn_was_observed", started is not None and started == self._last_seen,
              {"turn_started_at": started, "last_minute_this_transaction_saw": self._last_seen})
        turn_minutes = sorted(set(range(self._last_seen + 1, minute + 1)) | {minute})
        # P3-212/215: the clock did not move and only structural or acknowledged-no-physiology actions ran. There is NO new minute: nothing to commit
        # and nothing to abort on. The pair domain must be exactly what it was, and every identity check still holds.
        pre = ra.action_kinds(() if (route == CLINICAL_TIME and ran is None) else ran) if (ran is not None or route == CLINICAL_TIME) else ()
        if isinstance(before, Mapping) and started == minute and pre and set(pre) <= set(ra.NO_ADVANCE_OK):
            self._no_advance_turn(record, minute, before, after, legacy_observable, session, ran, pre, route)
            return
        self.lineage = live_lineage()
        check("lineage_certified", bool(ev.core_lineage_ok()) and lineage_is_v1(self.lineage) and (self.offered_lineage is None or lineage_is_v1(self.offered_lineage)),
              {"live": self.lineage.get("version_id"), "bound": self.bound.core_version})
        session_runner = getattr(session, "runner", None)
        check("snapshot_bound", self.runner is not None and runner_is_bound(self.runner, self.bound) and self.pressure_snapshot is not None
              and pressure_point_matches(self.bound.profile) and self._anchors is not None and _anchors_digest(self.runner) == self._anchors
              and session_runner is not None and _anchors_digest(session_runner) == self._anchors)
        check("case_eligible", self.case_id in ra.AUTHORITY_CASES and getattr(session, "case_id", self.case_id) == self.case_id, {"evaluator_case": self.case_id,
              "session_case": getattr(session, "case_id", None)})
        # the clinical-time route declares no actions: it is the empty turn, not an undeclared one
        declared = () if route == CLINICAL_TIME and ran is None else ran
        kinds = ra.action_kinds(declared) if declared is not None else ()
        gap_kinds = ra.gap_kinds_of(session)
        unsupported = tuple(sorted(set(ra.unsupported_among(kinds)) | set(ra.unsupported_among(gap_kinds))))
        record["action_kinds"] = list(kinds)
        record["no_common_physiology"] = [dict(row) for row in ra.executed_no_common_physiology(ra.action_fates(declared))]
        check("supported_management", declared is not None and not unsupported,
              "the caller did not declare which actions ran" if declared is None else {"unsupported": list(unsupported)})
        check("minute_not_already_committed", minute not in self.would_commit)
        shadow_minute = next((item for item in reversed(list(getattr(session, "minutes", []) or [])) if _as_int(item.minute) == minute), None)
        pressure = None if shadow_minute is None else ra.pressure_point(shadow_minute.derived)
        present = shadow_minute is not None and shadow_minute.compared_against_legacy and pressure is not None and all(value is not None for value in pressure.values())
        written = None
        transaction = None
        pair_pressure_kwargs = None
        replay_input = ra.AuthoritySite._artifact_input(session)
        table = self._replay_table(replay_input)                                   # ONE replay of the artifact per turn, read at every minute (not one per minute)
        if check("pressure_candidate_present", present):
            replayed = None if table is None else table.get(minute)
            written = ra.shaped_like_legacy(pressure, legacy_observable)
            failures = list(getattr(session, "failures", []) or [])[self._failures_seen:]
            pair_pressure_kwargs = dict(invariants_hold=not failures, replay_digest=ra.digest_of(replayed) if replayed is not None else "",
                                        expected_digest=ra.digest_of(pressure), unsupported=unsupported if declared is not None else None,
                                        legacy_arrest=legacy_observable.get("pulse_present") is False, failures=failures)
            probe = ra.AuthorityTransaction(minute=minute, case_id=self.case_id, snapshot=self.pressure_snapshot)
            probe.capture(after).compute(written, ra.pressure_point(legacy_observable))
            valid = probe.validate(**pair_pressure_kwargs)
            check("pressure_validated", valid and probe.state == ra.VALIDATED and not probe.committed, {"validation_failures": list(probe.failures)})
        else:
            failed.append("pressure_validated")
        has = (candidate is not None and candidate["derived"] is not None and candidate["category"] in WORD_OF
               and candidate["consciousness_level"] == candidate["category"] and candidate["pulse_present"] is True)
        check("consciousness_candidate_present", has)
        check("consciousness_reproducible", candidate is not None and candidate["reproduced"])
        mine = {_as_int(item.minute): dict(item.derived) for item in (self.runner.results if self.runner is not None else [])}
        theirs = {_as_int(item.minute): dict(item.derived) for item in list(getattr(session, "minutes", []) or [])}
        apart = [index for index in turn_minutes if index not in mine or index not in theirs
                 or any(mine[index].get(name) != theirs[index].get(name) for name in SHARED_READINGS)]
        check("pair_is_one_course", has and shadow_minute is not None and not apart and candidate["state_digest"] is not None, {"minutes_apart_or_missing": apart[:8]})
        rows = self._interval(minute, session, unsupported, legacy_observable.get("pulse_present") is False, turn_minutes, table)
        record["interval"] = rows
        bad = [row for row in rows if not row["ok"]]
        check("interval_minutes_validated", not bad, {"first_failed_minute": bad[0]["minute"] if bad else None, "failed": bad[0]["failed"] if bad else None,
                                                      "interval_minutes": [turn_minutes[0], turn_minutes[-1]]})
        boundary = self._boundary(minute)
        check("collapse_boundary_not_reached", boundary["clear"], boundary)
        check("window_open", minute <= self.time_limit, {"time_limit": self.time_limit})
        check("common_run_did_not_fail", self.runner is not None and not self.runner.failures,
              [f"{item.minute}:{item.where}:{item.exception}" for item in (self.runner.failures if self.runner is not None else [])])
        values = None
        if written is not None and has:
            payload = payload_from(minute, written, {"category": candidate["category"], "pulse_present": candidate["pulse_present"]})
            values = payload.as_dict()
            prepared = deepcopy(dict(after))
            observable = dict(prepared.get("observable") or {})
            observable.update({name: values[name] for name in OBSERVABLE_WRITES})
            prepared["observable"] = observable
            prepared[view.OVERLAY_KEY] = {"owner": "dry", "minute": minute, "views": {}, "common": {name: values[name] for name in view.COMMON_FIELDS},
                                          "legacy": {}, "mapped_into_live_field": False}
            outside, observable_moved = moved_fields(after, prepared)
            record["would_move"] = sorted(outside | observable_moved)
            carried = sorted(set(written) - set(PRESSURE_FIELDS))                       # whatever else the pressure half brought along
            check("only_the_pair_would_move",
                  outside <= {view.OVERLAY_KEY} and observable_moved <= set(OBSERVABLE_WRITES) and "mental_status" not in observable_moved
                  and not carried and not payload_problems(payload) and set(values) == {"minute"} | set(PAIR_FIELDS),
                  {"moved_outside_the_observable": sorted(outside), "moved_in_the_observable": sorted(observable_moved), "carried_by_the_pressure_half": carried,
                   "payload_problems": payload_problems(payload)})
        else:
            failed.append("only_the_pair_would_move")
        record["failed_checks"], record["detail"] = [name for name in CHECKS if name in failed], {key: _plain(value) for key, value in detail.items()}
        if not failed:
            record.update(verdict=WOULD_COMMIT, reason="every check passed", would_write=values)
            self.would_commit.append(minute)
            self.phase = ACTIVE
            self._cleared_through = minute
            return
        self._refuse(record, minute, failed, detail, "validation")

    def _no_advance_turn(self, record, minute, before, after, legacy_observable, session, ran, kinds, route) -> None:
        failed, detail = [], {}

        def check(name: str, ok: bool, why: Any = None) -> None:
            if not ok:
                failed.append(name)
                if why is not None:
                    detail[name] = why
        check("turn_has_a_transaction_site", route in KNOWN_ROUTES, {"route": route})
        check("turn_was_observed", _as_int(before.get("sim_time")) == self._last_seen, {"last_minute_this_transaction_saw": self._last_seen})
        self.lineage = live_lineage()
        check("lineage_certified", bool(ev.core_lineage_ok()) and lineage_is_v1(self.lineage) and (self.offered_lineage is None or lineage_is_v1(self.offered_lineage)))
        session_runner = getattr(session, "runner", None)
        check("snapshot_bound", self.runner is not None and runner_is_bound(self.runner, self.bound) and self._anchors is not None
              and _anchors_digest(self.runner) == self._anchors and session_runner is not None and _anchors_digest(session_runner) == self._anchors)
        check("case_eligible", self.case_id in ra.AUTHORITY_CASES and getattr(session, "case_id", self.case_id) == self.case_id)
        gap_kinds = ra.gap_kinds_of(session)
        unsupported = tuple(sorted(set(ra.unsupported_among(kinds)) | set(ra.unsupported_among(gap_kinds))))
        check("supported_management", not unsupported, {"unsupported": list(unsupported)})
        # P3-219 review, F3: a failure the session recorded during a turn that did not move the clock is not "nothing happened"
        new_failures = list(getattr(session, "failures", []) or [])[self._failures_seen:]
        # the site's own predicate (a MAP that APPEARS on the engine's first refresh is its derivation, not a move), and the overlay untouched
        same = ra.AuthoritySite._no_advance(before, after) and dict(before).get(view.OVERLAY_KEY) == dict(after).get(view.OVERLAY_KEY)
        check("pair_domain_unchanged", same, {"pressure_before": ra.pressure_point(dict(before).get("observable")), "pressure_after": ra.pressure_point(legacy_observable)})
        check("common_run_did_not_fail", self.runner is not None and not self.runner.failures and not new_failures,
              {"session_failures_since_the_last_turn": [f"{item.minute}:{item.where}" for item in new_failures][:4]})
        record["action_kinds"] = list(kinds)
        record["no_common_physiology"] = [dict(row) for row in ra.executed_no_common_physiology(ra.action_fates(ran if ran is not None else ()))]
        record["interval"] = []
        record["failed_checks"], record["detail"] = [name for name in CHECKS if name in failed], {key: _plain(value) for key, value in detail.items()}
        if failed:
            self._refuse(record, minute, failed, detail, "no_advance")
            return
        record.update(verdict=NO_ADVANCE, reason="the clock did not move and nothing physiological ran: no new minute, no commit, no abort")

    # -- after the order pipeline settled the turn ------------------------------------------------------------------------------------------
    def settle(self, orders: Sequence | None) -> None:
        """An order the engine does not MODEL produces no action for the turn, so the minute above never saw it; the settled ledger is the only place its
        class appears. The same ``unsupported_among`` is applied to EVERY settled row (a row without a class is ``untyped_action``), and a ledger that is not
        a list of rows is unreadable: both refuse. An EXECUTED_NO_COMMON_PHYSIOLOGY row is acknowledged and does not. A minute that would already have
        committed is NOT rewritten: the experiment halts after it, as ``AuthoritySite.settle_provenance`` halts."""
        if not self.records:
            return
        record = self.records[-1]
        try:
            readable = isinstance(orders, (list, tuple)) and all(isinstance(item, Mapping) for item in orders)
            rows = [dict(item) for item in ra.settled_provenance(orders, None)] if readable else [{"class": "<unreadable>"}]
        except Exception:
            rows = [{"class": "<unreadable>"}]
        classes = tuple(str(item.get("class") or "") for item in rows)
        # the ONE rule the real site shares (``unsupported_in_settlement``): unsupported classes, and an allowlisted class whose settled fate says it did not act
        dispositions = [ra.disposition_of(item.get("class"), item.get("fate")) for item in rows]
        unsupported = ra.unsupported_in_settlement(rows)
        record["settled_classes"] = sorted(set(classes) - {""})
        record["no_common_physiology"] = [dict(row) for row in ra.executed_no_common_physiology(rows)]
        record["dispositions"] = [{"class": item.get("class"), "fate": item.get("fate"), "disposition": name} for item, name in zip(rows, dispositions)]
        if unsupported and self.halt is None:
            began = bool(self.would_commit)
            record["settlement_refusal"] = list(unsupported)
            self.halt = {"minute": record["minute"], "failed_checks": ["settled_classes_supported"], "authority_had_begun": began, "stage": "settlement",
                         "detail": {"unsupported": list(unsupported)},
                         "consequence": ("the experiment hard-stops; the minute that would already have committed is not rewritten and the encounter is "
                                         "INVALID_FOR_CONTINUATION" if began else "authority never began; the legacy engine simply continues")}
            self.phase = HALTED
        record["digest"] = ra.digest_of({key: value for key, value in record.items() if key != "digest"})

    def summary(self) -> dict:
        commits = list(self.would_commit)
        return {"case": self.case_id, "snapshot": self.bound.summary(), "snapshot_is_the_pinned_version_1": bound_is_v1(self.bound), "granularity": GRANULARITY,
                "time_limit": self.time_limit, "minutes_evaluated": len(self.records), "violations": list(self.violations),
                "would_commit_minutes": len(commits), "first_would_commit": commits[0] if commits else None, "last_would_commit": commits[-1] if commits else None,
                "no_advance_turns": sum(1 for item in self.records if item["verdict"] == NO_ADVANCE),
                "first_would_abort": None if self.halt is None else self.halt["minute"], "abort_checks": None if self.halt is None else self.halt["failed_checks"],
                "abort_stage": None if self.halt is None else self.halt.get("stage"),
                "authority_had_begun_at_abort": None if self.halt is None else self.halt["authority_had_begun"],
                "consequence": None if self.halt is None else self.halt["consequence"],
                "halted_minutes": sum(1 for item in self.records if item["verdict"] == HALTED),
                "routes": sorted({item["route"] for item in self.records}), "record_digest": ra.digest_of([item["digest"] for item in self.records])}


# ============================================================================================================================================
# P3-215A: the page's ONE hook for a clock advance. The decisions live here; ``app.py`` calls and decides nothing.
# ============================================================================================================================================

HOOK_VERSION = "P3-215A"
#: Where the page keeps its dry evaluator, beside the shadow session. Never inside the patient state, never rendered, never scored.
DRY_KEY = "phase3_pair_dry"
DRY_ARTIFACT_KEY = "phase3_pair_dry_artifact"
DRY_REFUSAL_KEY = "phase3_pair_dry_refused_because"
CASE_NOT_ELIGIBLE, ARRIVAL_NOT_ELIGIBLE, BINDING_REFUSED = "CASE_NOT_ELIGIBLE", "ARRIVAL_NOT_ELIGIBLE", "SNAPSHOT_BINDING_REFUSED"


def dry_evaluator_for(store: Any, session: Any, *, environ: Mapping[str, str] | None = None) -> PairDryEvaluator | None:
    """The dry evaluator of the encounter ``session`` follows, or None. A refusal is remembered for this session: it is not retried every turn.

    ``None`` whenever the dry flag is off (today, by default), the shadow does not run, the case is not one of the two GI cases, the arrival was not an
    untouched authored arrival, or the snapshot binding is refused. A new encounter has a new shadow session, hence a new evaluator: two patients are
    never mixed in one."""
    if session is None or not dry_run_enabled(environ):
        return None
    held = store.get(DRY_KEY)
    if isinstance(held, tuple) and len(held) == 2 and held[0] is session:
        return held[1]
    store.pop(DRY_ARTIFACT_KEY, None)                  # a summary of ANOTHER encounter's evaluator must not survive into this one (P3-219 review, F8)
    evaluator, why = None, None
    try:
        eligibility = getattr(session, "eligibility", None) or {}
        if getattr(session, "family", None) != ra.AUTHORITY_FAMILY or getattr(session, "case_id", None) not in ra.AUTHORITY_CASES:
            why = CASE_NOT_ELIGIBLE
        elif getattr(session, "arrival", None) is None or not eligibility.get("eligible") or getattr(session, "runner", None) is None:
            why = ARRIVAL_NOT_ELIGIBLE
        else:
            evaluator = PairDryEvaluator(bind(), session.case_id, session.arrival)
    except Exception as error:                            # a binding refused, a runner that would not open: the legacy encounter does not care why
        evaluator, why = None, f"{BINDING_REFUSED}: {type(error).__name__}"
    store[DRY_KEY] = (session, evaluator)
    store[DRY_REFUSAL_KEY] = why
    return evaluator


def after_clock_moved(store: Any, session: Any, before: Mapping | None, after: Mapping, ran: Sequence | None, submission_id: Any, route: str, *,
                      environ: Mapping[str, str] | None = None) -> Mapping | None:
    """The ONE hook the page calls right after the engine moved the clock, on EVERY route (P3-215A). Returns a prepared state, or None.

    * ``CLINICAL_TIME`` (a question, an examination): the authority site's minute is opened here, by the layer. With the authority off -- always, today --
      ``site_for`` returns None and nothing is prepared.
    * ``ORDER_TURN``: the page's own certified block already holds the site's minute (its shape is pinned), so this hook only feeds the dry evaluator.
    * The dry evaluator (flag ``MRS_PHASE3_PAIR_DRY_RUN``) is fed only while NO real site is open: it evaluates what a transaction would do, and a real
      one has already done it.

    Never raises into the page; never writes ``after``; never reads a clinical value to decide anything."""
    prepared = None
    try:
        if route == ra.CLINICAL_TIME:
            site = ra.site_for(after, store, environ=environ)
            if site is not None:
                prepared = site.minute(before, after, session, ran, submission_id, route)
                store[ra.ARTIFACT_KEY] = site.artifact()
        if store.get(ra.SITE_KEY) is None:
            evaluator = dry_evaluator_for(store, session, environ=environ)
            if evaluator is not None:
                evaluator.minute(before, after, session, ran, submission_id, route)
                store[DRY_ARTIFACT_KEY] = evaluator.summary()
    except Exception as error:                            # the hook is observation: a failure here is recorded, never raised into the turn
        store[DRY_REFUSAL_KEY] = f"HOOK_FAILED: {type(error).__name__}"
    return prepared


def after_orders_settled(store: Any, session: Any, orders: Sequence | None, *, environ: Mapping[str, str] | None = None) -> None:
    """The second phase of the hook, for an order turn: the pipeline settled each order's fate, so the evaluator may read them (P3-215A)."""
    try:
        held = store.get(DRY_KEY)
        if isinstance(held, tuple) and len(held) == 2 and held[0] is session and held[1] is not None and dry_run_enabled(environ):
            held[1].settle(orders)
            store[DRY_ARTIFACT_KEY] = held[1].summary()
    except Exception as error:
        store[DRY_REFUSAL_KEY] = f"SETTLE_FAILED: {type(error).__name__}"


def forget(store: Any) -> None:
    """A new encounter drops the evaluator, as it drops the shadow session and the site."""
    for key in (DRY_KEY, DRY_ARTIFACT_KEY, DRY_REFUSAL_KEY):
        try:
            store.pop(key, None)
        except Exception:
            pass
