"""P3-491: the binding of the live GI development authority's COMMON TONE SUPPORT to the ratified ``COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1``.

Part of the Phase-3 layer (it is named in ``runtime_shadow.LAYER_SOURCES``, so the layer digest covers it). It is NOT physiology and it is NOT a new mechanism: the faculty ratified the development
snapshot on 2026-11-18 (FD-TONE-RATIFY-01 to FD-TONE-RATIFY-09) and ratified the manual norepinephrine rate control on 2026-11-20 (FD-NR-01). The four values of the snapshot already have an
unambiguous executable home in fields that exist in ``PHASE2_AMENDMENT_3`` (``clinical_core`` is not edited):

* ``tone_gain``                -> ``CoreProfile.vasoconstrictor_support_to_tone_gain`` (the ONE profile field of the common support),
* ``half_effect_rate_mcg_min`` -> ``Norepinephrine.half_effect_rate_mcg_min`` (a constant of the writer the order builds),
* ``onset_tau_min``            -> ``Norepinephrine.onset_tau_min``,
* ``offset_tau_min``           -> ``Norepinephrine.offset_tau_min``.

Binding therefore changes NO source of ``clinical_core``. What this module adds is the part that makes it safe, the same discipline ``runtime_pressure_snapshot`` applies to the pressure point:

* the exact record is READ, never recomputed: its file hash, its whole-record digest, the ratification, the human record it cites and the core digest it names are pinned here;
* the binding in the record must equal, field by field, a second typed copy in this file, and the core's own ``CENTER_REFERENCE`` witness (the one setting the record names; no other
  setting is read: ``LOW`` and ``HIGH`` are test witnesses, are recognised only as the strings the record gives them, and are refused if offered as the snapshot);
* the object that results is frozen against ordinary assignment, and nobody trusts it: every consumer re-derives it with ``configuration_is_pinned``;
* a flag that names this snapshot and a record that does not verify is a REFUSAL (``ToneBindingError``), never a fallback to a witness name, to the shadow's development copy or to no tone.

Nothing here enables an authority, registers an approval or writes into an encounter. ``configuration_for`` returns None when the environment does not name this snapshot.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import math
import os
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

MODULE_VERSION = "P3-491"
ROOT = str(Path(__file__).resolve().parent)

SNAPSHOT_ID = "COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1"
#: What a run REPORTS for the tone configuration it ran.
RUNTIME_SNAPSHOT_ID = "common_tone_development_snapshot_v1"
#: The environment variable that names the ratified tone snapshot a run asks for (the exact id, trimmed; never honoured from a Secret).
TONE_SNAPSHOT_FLAG = "MRS_PHASE3_AUTHORITY_TONE_SNAPSHOT"

RECORD_FILE = "docs/revision/COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1.json"
RATIFICATION_FILE = "docs/revision/COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1_RATIFICATION.json"

# -- what is pinned: the committed records of 2026-11-18 (P3-418, FD-TONE-RATIFY) -------------------------------------------------------------------------------------------------
RECORD_FILE_SHA256 = "1f2ebb46190e72ec150897037a397f788164fb7f29b46337dbb94328d0be8e2c"
RECORD_DIGEST = "ee1740ca77173ce0797268f8327f21fc29304c5c54ff2c642c1f2bdfb3270356"
RATIFICATION_FILE_SHA256 = "d23df1c7a0a27803cf0c318eb0417163eecd65e70ad014c369e06659c842f1b4"
RATIFICATION_DIGEST = "a5a8f4370e240a07406111e0fedf40884e7e382dbd08643949bc82201452bab2"
HUMAN_RECORD_DIGEST = "50807dfc418226aed48826864abf6ac14c8d5d785f9e1f2ed68207091afe0804"
#: The digest of the four binding values alone, so "a parameter was modified" is told apart from any other change of the record.
VALUES_DIGEST = "6d5a4654c9f0167e450ec7abeb02291ac7d4cde4e4ffed27ab85b1163fc5bd8c"
CORE_VERSION = "PHASE2_AMENDMENT_3"
CORE_DIGEST = "867bac09e09bb5c04629e73fbbdec0f7e1f100da17ef8966f580ba91067a7c9c"
PROFILE_FIELD = "vasoconstrictor_support_to_tone_gain"
WITNESS = "CENTER_REFERENCE"

#: The binding, typed a SECOND time on purpose: the record is read and must equal this, field by field (a slip in either copy is a refusal, never a silent value).
BINDING = MappingProxyType({"half_effect_rate_mcg_min": 10.0, "offset_tau_min": 2.5, "onset_tau_min": 1.5, "tone_gain": 0.6})
STATUS = "RATIFIED_FOR_DEVELOPMENT_EXPERIMENTS"
IS_NOT = ("a clinical calibration", "a clinical dose-response", "an mmHg target", "production validation", "resident approval", "authority")
RATIFICATION_IS_NOT = ("a clinical calibration", "production validation", "resident approval", "a clinical-validation claim")
LIMITATIONS = ("COMMON_TONE_PUMP_DEPENDENCE_NOT_YET_VALIDATED", "CONSCIOUSNESS_UNDER_TONE_UNRESOLVED")

# -- the refusals ----------------------------------------------------------------------------------------------------------------------------------------------------------------
NOT_A_RECORD = "NOT_A_TONE_SNAPSHOT_RECORD"
WRONG_SNAPSHOT_ID = "WRONG_TONE_SNAPSHOT_ID"
WRONG_STATUS = "TONE_SNAPSHOT_IS_NOT_RATIFIED_FOR_DEVELOPMENT"
WRONG_DIGEST = "TONE_SNAPSHOT_WRONG_DIGEST"
MODIFIED_PARAMETER = "TONE_SNAPSHOT_MODIFIED_PARAMETER"
WITNESS_SUBSTITUTED = "TONE_SNAPSHOT_IS_A_TEST_WITNESS"
NOT_THE_CORE_WITNESS = "TONE_SNAPSHOT_IS_NOT_THE_CORES_CENTER_REFERENCE"
NOT_RATIFIED = "TONE_SNAPSHOT_RATIFICATION_DOES_NOT_MATCH"
HUMAN_RECORD_MISMATCH = "TONE_SNAPSHOT_HUMAN_RECORD_DOES_NOT_MATCH"
CORE_MISMATCH = "TONE_SNAPSHOT_NAMES_ANOTHER_CORE"
UNREADABLE = "TONE_SNAPSHOT_RECORD_UNREADABLE"
UNKNOWN_TONE_SNAPSHOT = "THE_ENVIRONMENT_NAMES_ANOTHER_TONE_SNAPSHOT"
REFUSALS = (NOT_A_RECORD, WRONG_SNAPSHOT_ID, WRONG_STATUS, WRONG_DIGEST, MODIFIED_PARAMETER, WITNESS_SUBSTITUTED, NOT_THE_CORE_WITNESS, NOT_RATIFIED, HUMAN_RECORD_MISMATCH, CORE_MISMATCH,
            UNREADABLE, UNKNOWN_TONE_SNAPSHOT)

#: The four executable magnitudes a run must carry, in order, and where each one lives (the P3-396 mapping, as data).
EXECUTABLE_HOME = MappingProxyType({
    "tone_gain": "clinical_core.derived.CoreProfile.vasoconstrictor_support_to_tone_gain",
    "half_effect_rate_mcg_min": "clinical_core.vascular_support.Norepinephrine.half_effect_rate_mcg_min",
    "onset_tau_min": "clinical_core.vascular_support.Norepinephrine.onset_tau_min",
    "offset_tau_min": "clinical_core.vascular_support.Norepinephrine.offset_tau_min",
})


class ToneBindingError(ValueError):
    """The record offered is not ``COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1`` as ratified: ``reasons`` lists every refusal code."""

    def __init__(self, reasons):
        self.reasons = tuple(reasons)
        super().__init__(f"tone snapshot binding refused: {list(self.reasons)}")


def canonical(value: Any) -> str:
    """The canonical text the pinned digests were taken over (sorted keys, no spaces, ASCII)."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("ascii")).hexdigest()


def plain(value: Any) -> Any:
    """The value as plain JSON data, or None when it is not JSON. A record is verified and used in THIS form only."""
    try:
        return json.loads(json.dumps(value, allow_nan=False))
    except Exception:
        return None


def _number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _whole_record_digest(record: Mapping) -> str:
    return digest({key: value for key, value in record.items() if key != "record_digest"})


@dataclasses.dataclass(frozen=True)
class ToneConfiguration:
    """The verified tone binding and the identities that tie it to the committed records. Frozen against ordinary assignment only: Python can still build one by hand or force an attribute, so no
    consumer trusts the object -- each re-checks it with ``configuration_is_pinned``."""

    snapshot_id: str
    runtime_snapshot_id: str
    tone_gain: float
    half_effect_rate_mcg_min: float
    onset_tau_min: float
    offset_tau_min: float
    profile_field: str
    values_digest: str
    record_digest: str
    record_file_sha256: str
    ratification_digest: str
    human_record_digest: str
    core_version: str
    core_digest: str
    configuration_digest: str

    def values(self) -> dict:
        """The four magnitudes a run carries (the order of ``EXECUTABLE_HOME``): exactly what the order mapping reads as the witness."""
        return {"tone_gain": self.tone_gain, "half_effect_rate_mcg_min": self.half_effect_rate_mcg_min, "onset_tau_min": self.onset_tau_min, "offset_tau_min": self.offset_tau_min}

    def summary(self) -> dict:
        """What an artifact says about the configuration it ran: identity and bindings."""
        return {"snapshot_id": self.snapshot_id, "runtime_snapshot_id": self.runtime_snapshot_id, "values": self.values(), "profile_field": self.profile_field,
                "values_digest": self.values_digest, "record_digest": self.record_digest, "record_file_sha256": self.record_file_sha256,
                "ratification_digest": self.ratification_digest, "human_record_digest": self.human_record_digest, "core_version": self.core_version,
                "core_digest": self.core_digest, "configuration_digest": self.configuration_digest}


def _identity_of(cfg: ToneConfiguration) -> dict:
    body = dataclasses.asdict(cfg)
    body.pop("configuration_digest", None)
    return body


def _expected() -> ToneConfiguration:
    """The configuration the pinned constants describe: the reference every consumer re-derives against."""
    body = ToneConfiguration(SNAPSHOT_ID, RUNTIME_SNAPSHOT_ID, float(BINDING["tone_gain"]), float(BINDING["half_effect_rate_mcg_min"]), float(BINDING["onset_tau_min"]),
                             float(BINDING["offset_tau_min"]), PROFILE_FIELD, VALUES_DIGEST, RECORD_DIGEST, RECORD_FILE_SHA256, RATIFICATION_DIGEST, HUMAN_RECORD_DIGEST, CORE_VERSION,
                             CORE_DIGEST, "")
    return dataclasses.replace(body, configuration_digest=digest(_identity_of(body)))


#: The digest of the whole configuration identity, derived from the pins above. The grant pins it (a grant is never edited: another binding is another grant).
CONFIGURATION_DIGEST = _expected().configuration_digest


def configuration_is_pinned(cfg: Any) -> bool:
    """This object IS the pinned configuration: its type, every field and the digest of its own identity, re-derived and compared with the pins -- not merely with itself."""
    try:
        return (type(cfg) is ToneConfiguration and cfg == _expected() and cfg.configuration_digest == CONFIGURATION_DIGEST and digest(_identity_of(cfg)) == CONFIGURATION_DIGEST
                and digest({"half_effect_rate_mcg_min": cfg.half_effect_rate_mcg_min, "offset_tau_min": cfg.offset_tau_min, "onset_tau_min": cfg.onset_tau_min,
                            "tone_gain": cfg.tone_gain}) == VALUES_DIGEST)
    except Exception:
        return False


def verify_record(record: Any, *, raw: bytes | None = None) -> list:
    """Every reason this record is NOT the pinned snapshot (an empty list: it is). Never raises."""
    reasons: list = []
    record = plain(record)
    if not isinstance(record, dict):
        return [NOT_A_RECORD]
    if record.get("snapshot_id") != SNAPSHOT_ID or record.get("selected_witness") != WITNESS:
        reasons.append(WRONG_SNAPSHOT_ID)
    if record.get("status") != STATUS or not set(IS_NOT) <= set(record.get("is_not") or ()):
        reasons.append(WRONG_STATUS)
    binding = record.get("binding")
    complete = isinstance(binding, dict) and set(binding) == set(BINDING) and all(_number(binding[name]) for name in BINDING)
    if not complete:
        reasons.append(NOT_A_RECORD)
    else:
        offered = {name: binding[name] for name in BINDING}
        if offered != dict(BINDING) or digest(offered) != VALUES_DIGEST:
            reasons.append(MODIFIED_PARAMETER)
    if record.get("profile_field") != PROFILE_FIELD:
        reasons.append(MODIFIED_PARAMETER)
    # LOW and HIGH are test witnesses: the record carries them only as the words that say so. A record that carries a NUMBER for either is not this record.
    witnesses = record.get("witnesses_test_only") if isinstance(record.get("witnesses_test_only"), dict) else {}
    if any(witnesses.get(name) != "TEST_WITNESS_ONLY" for name in ("LOW", "HIGH")):
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
    if source.get("copied_not_recomputed") is not True or source.get("optimized") is not False or source.get("another_point_considered") is not False:
        reasons.append(MODIFIED_PARAMETER)
    if source.get("core_digest") != CORE_DIGEST:
        reasons.append(CORE_MISMATCH)
    if dict(dict(record.get("reviewed_with") or {}).get("human_record") or {}).get("record_digest") != HUMAN_RECORD_DIGEST:
        reasons.append(HUMAN_RECORD_MISMATCH)
    return list(dict.fromkeys(reasons))


def verify_against_the_core() -> list:
    """The binding equals the core's OWN ``CENTER_REFERENCE`` witness (the one setting the record names). No other witness is read."""
    try:
        from clinical_core import vascular_support as vs
        centre = dict(vs.witness(WITNESS))
        return [] if {name: centre.get(name) for name in BINDING} == dict(BINDING) else [NOT_THE_CORE_WITNESS]
    except Exception:
        return [NOT_THE_CORE_WITNESS]


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
    human = ratification.get("human_record") if isinstance(ratification.get("human_record"), dict) else {}
    ok = (ratification.get("record_digest") == RATIFICATION_DIGEST and whole == RATIFICATION_DIGEST and ratification.get("status") == STATUS
          and snapshot.get("id") == SNAPSHOT_ID and snapshot.get("record_digest") == RECORD_DIGEST and snapshot.get("file_sha256") == RECORD_FILE_SHA256
          and human.get("record_digest") == HUMAN_RECORD_DIGEST and set(RATIFICATION_IS_NOT) <= set(ratification.get("is_not") or ())
          and record.get("record_digest") == snapshot.get("record_digest"))
    return [] if ok else [NOT_RATIFIED]


def bind(root: str = ROOT, *, record: Any = None, raw: bytes | None = None, ratification: Any = None) -> ToneConfiguration:
    """Bind to the exact ratified tone snapshot, or raise ``ToneBindingError`` with every refusal code.

    With no ``record`` the committed files are read and their raw bytes hashed. A ``record`` given by the caller is reduced to plain data and verified by its whole content (and by ``raw``, which must
    be the bytes of that same record); the configuration built from it is then re-derived against the pins. Nothing is registered, approved or enabled by binding."""
    if record is None:
        try:
            with open(os.path.join(root, RECORD_FILE), "rb") as handle:
                raw = handle.read()
            record = json.loads(raw.decode("utf-8"))
        except (OSError, ValueError):
            raise ToneBindingError([UNREADABLE]) from None
    if ratification is None:
        try:
            with open(os.path.join(root, RATIFICATION_FILE), "rb") as handle:
                ratification_raw = handle.read()
            ratification = json.loads(ratification_raw.decode("utf-8"))
            if hashlib.sha256(ratification_raw).hexdigest() != RATIFICATION_FILE_SHA256:
                ratification = None                          # the bytes are not the pinned ones: it is not THE ratification
        except (OSError, ValueError):
            ratification = None
    record = plain(record)
    reasons = verify_record(record, raw=raw)
    reasons += verify_against_the_core()
    if not reasons:
        reasons += verify_ratification(ratification, record)
    if reasons:
        raise ToneBindingError(list(dict.fromkeys(reasons)))
    cfg = _expected()
    if not configuration_is_pinned(cfg):                 # what was BUILT is checked, not only what was offered
        raise ToneBindingError([MODIFIED_PARAMETER])
    return cfg


def flag_value(environ: Mapping[str, str] | None = None) -> str:
    """What the environment says the tone snapshot is: the trimmed text (empty when it says nothing)."""
    live = os.environ if environ is None else environ
    return str(live.get(TONE_SNAPSHOT_FLAG, "") or "").strip()


def requested(environ: Mapping[str, str] | None = None) -> bool:
    """Whether the environment asks for THIS tone snapshot (the exact id, trimmed)."""
    return flag_value(environ) == SNAPSHOT_ID


def named(environ: Mapping[str, str] | None = None) -> bool:
    """Whether the environment says ANYTHING about the tone snapshot (an unknown id is a refusal for the caller, never a silent default)."""
    return bool(flag_value(environ))


def configuration_for(environ: Mapping[str, str] | None = None, *, root: str = ROOT) -> ToneConfiguration | None:
    """None when the environment does not name a tone snapshot; the verified configuration when it names this one; ``ToneBindingError`` when it names another one or this one does not verify.
    There is no third answer and no fallback."""
    if not named(environ):
        return None
    if not requested(environ):
        raise ToneBindingError([UNKNOWN_TONE_SNAPSHOT])
    return bind(root)


def checked(cfg: Any) -> ToneConfiguration:
    if not configuration_is_pinned(cfg):
        raise ToneBindingError([MODIFIED_PARAMETER])
    return cfg


def apply_profile(profile: Any, cfg: Any) -> Any:
    """The profile with the tone gain of the snapshot in the ONE field the common support reads. Nothing else of the profile is touched."""
    cfg = checked(cfg)
    return dataclasses.replace(profile, **{PROFILE_FIELD: float(cfg.tone_gain)})
