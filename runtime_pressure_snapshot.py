"""P3-378 to P3-380: the binding of the live GI development PRESSURE authority to the ratified ``GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1``.

Part of the Phase-3 layer (it is named in ``runtime_shadow.LAYER_SOURCES``, so the layer digest covers it). It is NOT physiology and it is NOT a new mechanism: the faculty
ratified a development snapshot on 2026-11-16 (FD-RATIFY-03) and promoted it to the live development authority (FD-PROMOTE-01). The five coordinates that differ from the point the
authority ran until then already have an unambiguous executable home in fields that exist:

* ``bleed_rate_ml_eq_per_min``  -> ``GIHaemorrhage.blood_loss_ml_per_min`` (the family's writer),
* ``preload_scale_ml_eq``       -> ``CoreProfile.preload_curve_scale_ml``,
* ``arrival_position``          -> ``CoreProfile.arrival_preload_fraction`` (0.5 in both points: it does not move),
* the crystalloid kernel ``e / s / tau_min`` -> ``Crystalloid.effective_ml_per_ml / transient_share / leak_tau_min``,

and ``c = rate / scale`` is not a coordinate but a consistency check. Binding therefore changes NO source of ``clinical_core``: the lineage stays ``PHASE2_AMENDMENT_2`` and the
promotion is configuration only (``CONFIG_ONLY_PROMOTION_SUFFICIENT``, P3-377). What this module adds is the part that makes that safe:

* the exact record is READ, never recomputed: its file hash, its whole-record digest, the ratification, the region record it names and the human record it cites are pinned here;
* the binding in the record must equal, field by field, a second typed copy in this file, and ``rate == c x scale``: a rate with another scale is a different point (FD-RATE-17);
* ``LOW`` and ``HIGH`` (test witnesses only) are recognised and refused if offered as the snapshot;
* the object that results is frozen against ordinary assignment, and nobody trusts it: every consumer re-derives it with ``configuration_is_pinned``;
* a flag that names this snapshot and a record that does not verify is a REFUSAL (``PressureBindingError``), never a fallback to the older point.

Nothing here enables an authority, registers an approval or writes into an encounter. ``configuration_for`` returns None when the environment does not name this snapshot, so the
older committed point (``gi_pressure_committed``) behaves exactly as it did.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import math
import os
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Sequence

MODULE_VERSION = "P3-378/380"
ROOT = str(Path(__file__).resolve().parent)

SNAPSHOT_ID = "GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1"
#: What the shadow layer REPORTS for the profile and contributors it ran (the older point reports ``phase2_committed_default_profile``).
RUNTIME_SNAPSHOT_ID = "gi_joint_pressure_development_snapshot_v1"
#: The environment variable that names the approved snapshot a run asks for (``runtime_authority.SNAPSHOT_FLAG``; written here as a literal so this module imports nothing of the gate).
SNAPSHOT_FLAG = "MRS_PHASE3_AUTHORITY_SNAPSHOT"

RECORD_FILE = "docs/revision/GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1.json"
RATIFICATION_FILE = "docs/revision/GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1_RATIFICATION.json"
REGION_FILE = "docs/revision/PHASE3_GI_JOINT_REGION_V1.json"

# -- what is pinned: the committed records of 2026-11-16 (P3-367 to P3-370) -------------------------------------------------------------------------------------------------------
RECORD_FILE_SHA256 = "dc5da76ea764759552d6107fd05584257903e16bb04cefe139486a0b343c922e"
RECORD_DIGEST = "925973f050bc5f9cdc85f7ff83af6fd9349b4499acfbc4987b3b59ab3a60f6b3"
RATIFICATION_FILE_SHA256 = "d9cdd2779b9f81f2abf6b321b8e3bec38d08a0755c11ec898ddc2a3d8f94b60c"
RATIFICATION_DIGEST = "6a471a3a1b729214da7e2f57e647d1b3944620cf08642ad5abdbf426692d7747"
REGION_FILE_SHA256 = "eb614a69dcd89271c18242f8b58e5ae0f3e4ea6362d9b2270e3c7b82ce3f8d6e"
REGION_DIGEST = "bf7361a1d96fe7fed9aeca697bba4809ef70e87843d71ba5b64a77f832c41539"
HUMAN_RECORD_DIGEST = "4af2b53118245b8667d58d3280205ac64101e5c61fb1ecb83ca8bd9f05f05bd8"
#: The digest of the six binding values alone, so "a parameter was modified" is told apart from any other change of the record.
VALUES_DIGEST = "9afd91f5106980410cc1a24591dea4c66e25a2b2d5ba866b3a0fb3b9c11da14f"

#: The binding, typed a SECOND time on purpose: the record is read and must equal this, field by field (a slip in either copy is a refusal, never a silent value).
BINDING = MappingProxyType({
    "arrival_position": 0.5,
    "bleed_rate_ml_eq_per_min": 8.970853509,
    "c_rate_over_scale_per_min": 0.003326066,
    "crystalloid_kernel": MappingProxyType({"e": 0.213115961, "s": 0.835, "tau_min": 60.624}),
    "preload_scale_ml_eq": 2697.136369656,
})
STATUS = "RATIFIED_FOR_DEVELOPMENT_EXPERIMENTS"
IS_NOT = ("a clinical calibration", "production authority", "resident validation")
RATIFICATION_IS_NOT = ("a clinical calibration", "authority-approved production physiology", "resident validation", "a clinical-validation claim")

# -- the refusals ----------------------------------------------------------------------------------------------------------------------------------------------------------------------
NOT_A_RECORD = "NOT_A_PRESSURE_SNAPSHOT_RECORD"
WRONG_SNAPSHOT_ID = "WRONG_PRESSURE_SNAPSHOT_ID"
WRONG_STATUS = "PRESSURE_SNAPSHOT_IS_NOT_RATIFIED_FOR_DEVELOPMENT"
WRONG_DIGEST = "PRESSURE_SNAPSHOT_WRONG_DIGEST"
MODIFIED_PARAMETER = "PRESSURE_SNAPSHOT_MODIFIED_PARAMETER"
RATE_WITHOUT_SCALE = "PRESSURE_SNAPSHOT_RATE_IS_NOT_C_TIMES_SCALE"
WITNESS_SUBSTITUTED = "PRESSURE_SNAPSHOT_IS_A_TEST_WITNESS"
NOT_RATIFIED = "PRESSURE_SNAPSHOT_RATIFICATION_DOES_NOT_MATCH"
REGION_MISMATCH = "PRESSURE_SNAPSHOT_REGION_RECORD_DOES_NOT_MATCH"
HUMAN_RECORD_MISMATCH = "PRESSURE_SNAPSHOT_HUMAN_RECORD_DOES_NOT_MATCH"
UNREADABLE = "PRESSURE_SNAPSHOT_RECORD_UNREADABLE"
REFUSALS = (NOT_A_RECORD, WRONG_SNAPSHOT_ID, WRONG_STATUS, WRONG_DIGEST, MODIFIED_PARAMETER, RATE_WITHOUT_SCALE, WITNESS_SUBSTITUTED, NOT_RATIFIED, REGION_MISMATCH,
            HUMAN_RECORD_MISMATCH, UNREADABLE)

#: The six executable magnitudes a run must carry, in order, and where each one lives (the P3-376 mapping, as data).
EXECUTABLE_HOME = MappingProxyType({
    "bleed_rate_ml_eq_per_min": "clinical_core.modules.gi_haemorrhage.GIHaemorrhage.blood_loss_ml_per_min",
    "preload_scale_ml_eq": "clinical_core.derived.CoreProfile.preload_curve_scale_ml",
    "arrival_position": "clinical_core.derived.CoreProfile.arrival_preload_fraction",
    "kernel_e": "clinical_core.interventions.fluids.Crystalloid.effective_ml_per_ml",
    "kernel_s": "clinical_core.interventions.fluids.Crystalloid.transient_share",
    "kernel_tau_min": "clinical_core.interventions.fluids.Crystalloid.leak_tau_min",
})


class PressureBindingError(ValueError):
    """The record offered is not ``GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1`` as ratified: ``reasons`` lists every refusal code."""

    def __init__(self, reasons):
        self.reasons = tuple(reasons)
        super().__init__(f"pressure snapshot binding refused: {list(self.reasons)}")


def canonical(value: Any) -> str:
    """The canonical text the pinned digests were taken over (sorted keys, no spaces, ASCII)."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("ascii")).hexdigest()


def plain(value: Any) -> Any:
    """The value as plain JSON data, or None when it is not JSON. A record is verified and used in THIS form only: after the reduction there is one answer for the check and the build."""
    try:
        return json.loads(json.dumps(value, allow_nan=False))
    except Exception:
        return None


def _number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _whole_record_digest(record: Mapping) -> str:
    return digest({key: value for key, value in record.items() if key != "record_digest"})


@dataclasses.dataclass(frozen=True)
class PressureConfiguration:
    """The verified binding and the identities that tie it to the committed records. Frozen against ordinary assignment only: Python can still build one by hand or force an
    attribute, so no consumer trusts the object -- each re-checks it with ``configuration_is_pinned``."""

    snapshot_id: str
    runtime_snapshot_id: str
    bleed_rate_ml_eq_per_min: float
    c_rate_over_scale_per_min: float
    preload_scale_ml_eq: float
    arrival_position: float
    kernel_e: float
    kernel_s: float
    kernel_tau_min: float
    values_digest: str
    record_digest: str
    record_file_sha256: str
    ratification_digest: str
    region_record_digest: str
    human_record_digest: str
    configuration_digest: str

    def values(self) -> dict:
        """The six magnitudes a run carries (the order of ``EXECUTABLE_HOME``)."""
        return {"bleed_rate_ml_eq_per_min": self.bleed_rate_ml_eq_per_min, "preload_scale_ml_eq": self.preload_scale_ml_eq, "arrival_position": self.arrival_position,
                "kernel_e": self.kernel_e, "kernel_s": self.kernel_s, "kernel_tau_min": self.kernel_tau_min}

    def summary(self) -> dict:
        """What an artifact says about the configuration it ran: identity and bindings (the values themselves are the pinned ones)."""
        return {"snapshot_id": self.snapshot_id, "runtime_snapshot_id": self.runtime_snapshot_id, "values": self.values(), "c_rate_over_scale_per_min": self.c_rate_over_scale_per_min,
                "values_digest": self.values_digest, "record_digest": self.record_digest, "record_file_sha256": self.record_file_sha256,
                "ratification_digest": self.ratification_digest, "region_record_digest": self.region_record_digest, "human_record_digest": self.human_record_digest,
                "configuration_digest": self.configuration_digest}


def _identity_of(cfg: PressureConfiguration) -> dict:
    body = dataclasses.asdict(cfg)
    body.pop("configuration_digest", None)
    return body


def _expected() -> PressureConfiguration:
    """The configuration the pinned constants describe: the reference every consumer re-derives against."""
    kernel = BINDING["crystalloid_kernel"]
    body = PressureConfiguration(
        SNAPSHOT_ID, RUNTIME_SNAPSHOT_ID, float(BINDING["bleed_rate_ml_eq_per_min"]), float(BINDING["c_rate_over_scale_per_min"]), float(BINDING["preload_scale_ml_eq"]),
        float(BINDING["arrival_position"]), float(kernel["e"]), float(kernel["s"]), float(kernel["tau_min"]), VALUES_DIGEST, RECORD_DIGEST, RECORD_FILE_SHA256, RATIFICATION_DIGEST,
        REGION_DIGEST, HUMAN_RECORD_DIGEST, "")
    return dataclasses.replace(body, configuration_digest=digest(_identity_of(body)))


#: The digest of the whole configuration identity, derived from the pins above. The grant pins it (a grant is never edited: another binding is another grant).
CONFIGURATION_DIGEST = _expected().configuration_digest


def configuration_is_pinned(cfg: Any) -> bool:
    """This object IS the pinned configuration: its type, every field and the digest of its own identity, re-derived and compared with the pins -- not merely with itself."""
    try:
        return (type(cfg) is PressureConfiguration and cfg == _expected() and cfg.configuration_digest == CONFIGURATION_DIGEST
                and digest(_identity_of(cfg)) == CONFIGURATION_DIGEST and digest({"arrival_position": cfg.arrival_position, "bleed_rate_ml_eq_per_min": cfg.bleed_rate_ml_eq_per_min,
                                                                                "c_rate_over_scale_per_min": cfg.c_rate_over_scale_per_min,
                                                                                "crystalloid_kernel": {"e": cfg.kernel_e, "s": cfg.kernel_s, "tau_min": cfg.kernel_tau_min},
                                                                                "preload_scale_ml_eq": cfg.preload_scale_ml_eq}) == VALUES_DIGEST)
    except Exception:
        return False


def verify_record(record: Any, *, raw: bytes | None = None, region: Any = None) -> list:
    """Every reason this record is NOT the pinned snapshot (an empty list: it is). Never raises."""
    reasons: list = []
    record = plain(record)
    if not isinstance(record, dict):
        return [NOT_A_RECORD]
    if record.get("snapshot_id") != SNAPSHOT_ID or record.get("selected_witness") != "CENTER_REFERENCE":
        reasons.append(WRONG_SNAPSHOT_ID)
    if record.get("status") != STATUS or not set(IS_NOT) <= set(record.get("is_not") or ()):
        reasons.append(WRONG_STATUS)
    binding = record.get("binding")
    complete = (isinstance(binding, dict) and set(binding) == set(BINDING) and isinstance(binding.get("crystalloid_kernel"), dict)
                and set(binding["crystalloid_kernel"]) == set(BINDING["crystalloid_kernel"])
                and all(_number(binding[name]) for name in BINDING if name != "crystalloid_kernel")
                and all(_number(value) for value in binding["crystalloid_kernel"].values()))
    if not complete:
        reasons.append(NOT_A_RECORD)
    else:
        offered = {name: binding[name] for name in BINDING if name != "crystalloid_kernel"}
        offered["crystalloid_kernel"] = dict(binding["crystalloid_kernel"])
        pinned = {name: BINDING[name] for name in BINDING if name != "crystalloid_kernel"}
        pinned["crystalloid_kernel"] = dict(BINDING["crystalloid_kernel"])
        if offered != pinned or digest(offered) != VALUES_DIGEST:
            reasons.append(MODIFIED_PARAMETER)
        try:
            if abs(float(binding["bleed_rate_ml_eq_per_min"]) - float(binding["c_rate_over_scale_per_min"]) * float(binding["preload_scale_ml_eq"])) > 1e-5 * float(binding["bleed_rate_ml_eq_per_min"]):
                reasons.append(RATE_WITHOUT_SCALE)
        except Exception:
            reasons.append(RATE_WITHOUT_SCALE)
    witnesses = record.get("witnesses_test_only") if isinstance(record.get("witnesses_test_only"), dict) else {}
    if complete and any(isinstance(dict(witnesses.get(name) or {}).get("binding"), dict) and dict(witnesses[name]["binding"]) == binding for name in ("LOW", "HIGH")):
        reasons.append(WITNESS_SUBSTITUTED)
    if record.get("record_digest") != RECORD_DIGEST or _whole_record_digest(record) != RECORD_DIGEST or (raw is not None and hashlib.sha256(raw).hexdigest() != RECORD_FILE_SHA256):
        reasons.append(WRONG_DIGEST)
    if raw is not None:
        try:
            same_as_the_bytes = json.loads(raw.decode("utf-8")) == record
        except Exception:
            same_as_the_bytes = False
        if not same_as_the_bytes and WRONG_DIGEST not in reasons:
            reasons.append(WRONG_DIGEST)                  # the bytes offered are not the bytes of the record offered
    source = record.get("binding_source") if isinstance(record.get("binding_source"), dict) else {}
    if source.get("region_record_digest") != REGION_DIGEST or source.get("region_record_file_sha256") != REGION_FILE_SHA256 or source.get("copied_not_recomputed") is not True:
        reasons.append(REGION_MISMATCH)
    if (record.get("human_record") or {}).get("record_digest") != HUMAN_RECORD_DIGEST:
        reasons.append(HUMAN_RECORD_MISMATCH)
    if region is not None:
        region = plain(region)
        centre = ((region or {}).get("witnesses") or {}).get("CENTER_REFERENCE") if isinstance(region, dict) else None
        if not isinstance(centre, dict) or centre.get("binding") != binding or (region or {}).get("record_digest") != REGION_DIGEST:
            reasons.append(REGION_MISMATCH)
    return list(dict.fromkeys(reasons))


def verify_ratification(ratification: Any, record: Mapping) -> list:
    """Every reason the ratification offered does not ratify THIS record for development experiments."""
    ratification = plain(ratification)
    if not isinstance(ratification, dict):
        return [NOT_RATIFIED]
    try:
        whole = _whole_record_digest(ratification)
    except Exception:
        whole = None
    snapshot = ratification.get("snapshot") if isinstance(ratification.get("snapshot"), dict) else {}
    region = ratification.get("region") if isinstance(ratification.get("region"), dict) else {}
    human = ratification.get("human_record") if isinstance(ratification.get("human_record"), dict) else {}
    ok = (ratification.get("record_digest") == RATIFICATION_DIGEST and whole == RATIFICATION_DIGEST and ratification.get("status") == STATUS
          and snapshot.get("id") == SNAPSHOT_ID and snapshot.get("record_digest") == RECORD_DIGEST and snapshot.get("file_sha256") == RECORD_FILE_SHA256
          and region.get("record_digest") == REGION_DIGEST and region.get("record_file_sha256") == REGION_FILE_SHA256 and human.get("record_digest") == HUMAN_RECORD_DIGEST
          and ratification.get("amendment_3") == "CLOSED" and set(RATIFICATION_IS_NOT) <= set(ratification.get("is_not") or ())
          and dict(ratification.get("authority") or {}).get("expanded") is False and record.get("record_digest") == snapshot.get("record_digest"))
    return [] if ok else [NOT_RATIFIED]


def bind(root: str = ROOT, *, record: Any = None, raw: bytes | None = None, ratification: Any = None, region: Any = None) -> PressureConfiguration:
    """Bind to the exact ratified snapshot, or raise ``PressureBindingError`` with every refusal code.

    With no ``record`` the committed files are read and their raw bytes hashed. A ``record`` given by the caller is reduced to plain data and verified by its whole content (and by
    ``raw``, which must be the bytes of that same record); the configuration built from it is then re-derived against the pins. Nothing is registered, approved or enabled by binding.
    """
    if record is None:
        try:
            with open(os.path.join(root, RECORD_FILE), "rb") as handle:
                raw = handle.read()
            record = json.loads(raw.decode("utf-8"))
        except (OSError, ValueError):
            raise PressureBindingError([UNREADABLE]) from None
    if ratification is None:
        try:
            with open(os.path.join(root, RATIFICATION_FILE), "rb") as handle:
                ratification_raw = handle.read()
            ratification = json.loads(ratification_raw.decode("utf-8"))
            if hashlib.sha256(ratification_raw).hexdigest() != RATIFICATION_FILE_SHA256:
                ratification = None                          # the bytes are not the pinned ones: it is not THE ratification
        except (OSError, ValueError):
            ratification = None
    if region is None:
        try:
            with open(os.path.join(root, REGION_FILE), "rb") as handle:
                region_raw = handle.read()
            region = json.loads(region_raw.decode("utf-8"))
            if hashlib.sha256(region_raw).hexdigest() != REGION_FILE_SHA256:
                region = None                                # the bytes are not the pinned ones: it is not THE region record
        except (OSError, ValueError):
            region = None
    record = plain(record)
    reasons = verify_record(record, raw=raw, region=region)
    if not reasons:
        reasons += verify_ratification(ratification, record)
    if region is None and REGION_MISMATCH not in reasons:
        reasons.append(REGION_MISMATCH)
    if reasons:
        raise PressureBindingError(list(dict.fromkeys(reasons)))
    cfg = _expected()
    if not configuration_is_pinned(cfg):                 # what was BUILT is checked, not only what was offered
        raise PressureBindingError([MODIFIED_PARAMETER])
    return cfg


def requested(environ: Mapping[str, str] | None = None) -> bool:
    """Whether the environment asks for THIS snapshot (the exact id, trimmed): the one question the session and the gate share."""
    live = os.environ if environ is None else environ
    return str(live.get(SNAPSHOT_FLAG, "") or "").strip() == SNAPSHOT_ID


def configuration_for(environ: Mapping[str, str] | None = None, *, root: str = ROOT) -> PressureConfiguration | None:
    """None when the environment does not name this snapshot (the older point runs, unchanged); the verified configuration when it does; ``PressureBindingError`` when it names it and
    the record does not verify. There is no third answer and no fallback to the older point."""
    if not requested(environ):
        return None
    return bind(root)


# -- applying the configuration to the three places that carry it ---------------------------------------------------------------------------------------------------------------------

def _checked(cfg: Any) -> PressureConfiguration:
    if not configuration_is_pinned(cfg):
        raise PressureBindingError([MODIFIED_PARAMETER])
    return cfg


def apply_profile(profile: Any, cfg: Any) -> Any:
    """The profile with the scale and the arrival position of the snapshot (the other magnitudes of the profile are untouched)."""
    cfg = _checked(cfg)
    return dataclasses.replace(profile, preload_curve_scale_ml=float(cfg.preload_scale_ml_eq), arrival_preload_fraction=float(cfg.arrival_position))


def apply_writers(writers: Sequence, cfg: Any) -> tuple:
    """The family's writers with the haemorrhage at the snapshot's rate. Every other writer, and every other field of the haemorrhage, is untouched."""
    from clinical_core.modules.gi_haemorrhage import GIHaemorrhage
    cfg = _checked(cfg)
    return tuple(dataclasses.replace(item, blood_loss_ml_per_min=float(cfg.bleed_rate_ml_eq_per_min)) if isinstance(item, GIHaemorrhage) else item for item in writers)


def apply_interventions(contributors: Sequence, cfg: Any) -> tuple:
    """The interventions with every crystalloid at the snapshot's kernel. Red cells, oxygen, the PPI and endoscopy are untouched."""
    from clinical_core.interventions.fluids import Crystalloid
    cfg = _checked(cfg)
    return tuple(dataclasses.replace(item, effective_ml_per_ml=float(cfg.kernel_e), transient_share=float(cfg.kernel_s), leak_tau_min=float(cfg.kernel_tau_min))
                 if isinstance(item, Crystalloid) else item for item in contributors)
