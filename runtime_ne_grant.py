"""P3-489: the explicit development grant of the LIVE manual NOREPINEPHRINE control (``GI_NOREPINEPHRINE_DEVELOPMENT_AUTHORITY_GRANT_V1``).

Faculty decisions FD-AUTHNE-01 to FD-AUTHNE-12 (2026-11-21) promote the ratified manual norepinephrine rate control (FD-NR-01) to a LIVE DEVELOPMENT authority for the GI haemorrhage family, and nothing else. This
module is DATA ONLY, like ``runtime_pressure_grant`` (it imports nothing of the repository on purpose, so that nothing can reach the registry through it): one immutable, fingerprinted record that binds the whole
scope in one place -- the ratified GI pressure snapshot, the ratified common tone snapshot, the core lineage that carries the support, the order-safety successor of the reader, the writer version, the cases, the
domain, the operations and units, and what an artifact must say to be replayed.

A grant is never edited. ``GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V3`` is neither modified nor superseded by this one: it stays the grant of every run that does not name a tone snapshot (FD-AUTHNE-08), with
norepinephrine still NOT granted. This grant opens a run ONLY when the environment names the tone snapshot AND the ratified pressure snapshot (the selector is ``MRS_PHASE3_AUTHORITY_TONE_SNAPSHOT``): neither
selector alone, nor the grant alone, suffices, and nothing falls back to the other grant.

What it grants: the pressure domain (``sbp``, ``dbp``, ``map``), the same domain as version 3, with the norepinephrine order classes the order contract below reads, and nothing else. The tone support is an INTERNAL
state of the common run: it is not a domain, it is never visible to the resident and it is not used for scoring. What it never grants is listed in ``not_granted``.
"""
from __future__ import annotations

import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping, Sequence

MODULE_VERSION = "P3-489"
GRANT_KIND = "FACULTY_GI_NOREPINEPHRINE_DEVELOPMENT_AUTHORITY_GRANT"
GRANT_ID = "GI_NOREPINEPHRINE_DEVELOPMENT_AUTHORITY_GRANT_V1"
GRANT_VERSION = 1
AUTHORITY_MODE = "PRESSURE_ONLY"
STATUS_ACTIVE = "ACTIVE_FOR_DEVELOPMENT_EXPERIMENT"
PURPOSE = "DEVELOPMENT_AUTHORITY_EXPERIMENT_ONLY"
ARTIFACT_LABEL = "REAL_DEVELOPMENT_PRESSURE_AUTHORITY"       # the authority is still the PRESSURE authority; the grant id and the norepinephrine_authority block tell the two runs apart
OVERLAY_LABEL = "FACULTY_ACCEPTED_FOR_DEVELOPMENT_COMPARISON"
DOMAIN = ("sbp", "dbp", "map")
EXCLUDED_DOMAINS = ("consciousness", "mental_status", "collapse", "terminal", "pulse", "oxygenation", "lactate", "hb")
FAMILY = "gi_bleed"
CASES = ("gi_bleed_57m", "gi_bleed_72f")
ENVIRONMENTS = ("development",)
WINDOW_MINUTES = 240
OVERLAY_SNAPSHOT_ID = "GI_DEVELOPMENT_SNAPSHOT_V1"

# -- what the grant binds, written as literals ON PURPOSE (a value read from another module at import would be a comparison of a thing with itself) ---------------------------------------------------
PRESSURE_SNAPSHOT_ID = "GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1"
PRESSURE_VALUE_DIGEST = "7270cf8599de0095088601acfe1df4d88b2aa9e38483fbdaf6844a1c2cce65c5"
PRESSURE_CONFIGURATION_DIGEST = "70e6826cb2844bace6e3249058638340d00d80f84f8fdd2a5a2e752028db0641"
TONE_SNAPSHOT_ID = "COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1"
TONE_CONFIGURATION_DIGEST = "bdc90a1719472be39d5d5f8a95d08799189dd1e1507a39b238441fdabe93e5d4"
TONE_VALUES_DIGEST = "6d5a4654c9f0167e450ec7abeb02291ac7d4cde4e4ffed27ab85b1163fc5bd8c"
TONE_RECORD_DIGEST = "ee1740ca77173ce0797268f8327f21fc29304c5c54ff2c642c1f2bdfb3270356"
TONE_RECORD_FILE_SHA256 = "1f2ebb46190e72ec150897037a397f788164fb7f29b46337dbb94328d0be8e2c"
TONE_RATIFICATION_DIGEST = "a5a8f4370e240a07406111e0fedf40884e7e382dbd08643949bc82201452bab2"
TONE_HUMAN_RECORD_DIGEST = "50807dfc418226aed48826864abf6ac14c8d5d785f9e1f2ed68207091afe0804"
TONE_SNAPSHOT_FLAG = "MRS_PHASE3_AUTHORITY_TONE_SNAPSHOT"
PROFILE_FIELD = "vasoconstrictor_support_to_tone_gain"
CORE_VERSION = "PHASE2_AMENDMENT_3"
CORE_DIGEST = "867bac09e09bb5c04629e73fbbdec0f7e1f100da17ef8966f580ba91067a7c9c"
WRITER_VERSION = "norepinephrine_rate_history/P3-431"
WRITER_TYPES = ("norepinephrine", "norepinephrine_rate_history")
#: The order-safety successor of the reader (the SECOND successor, FD-ORDER-01): the live reader must be exactly this one, or the grant opens nothing (a changed reader is a new succession and a new decision).
READER_GIT_BLOB = "a71a3888bc687a17a9eea24a6b06096ad58ae448"
READER_SHA256 = "39308bfd456f3b8443d9050bf9917ed3d7c47cd2a0086484dae113417b50d1c5"
READER_SUCCESSION_RECORD_DIGEST = "286053a6ac8063a46ccc83db78357f861f87193f92892a561a91ede4b2b00b5a"
ORDER_SAFETY_CHECKPOINT_DIGEST = "e5ccba3ca2c1dd5051ce0287cf4c1f1c963b2a2aa3e72cff6da8c2bc1b5bd908"
EARLIER_GRANT_ID = "GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V3"
EARLIER_GRANT_FINGERPRINT = "see runtime_pressure_grant.GRANT_FINGERPRINT_V3 (the earlier grant is neither read nor modified here)"

#: What a grant of this kind may never claim, anywhere in its record.
FORBIDDEN_CLAIMS = ("CLINICALLY_VALIDATED", "CLINICALLY_CALIBRATED", "PRODUCTION_APPROVED", "RESIDENT_APPROVED", "CLINICALLY_APPROVED", "CONSCIOUSNESS_AUTHORITY_GRANTED", "MENTAL_STATUS_AUTHORITY_GRANTED",
                    "TERMINAL_AUTHORITY_GRANTED", "VASOPRESSOR_DOSE_RESPONSE_VALIDATED")

#: The operations the order contract reads and the units it requires. An operation the engine names ``adjust`` or ``continue`` is read by what it SAYS (an explicit absolute rate in mcg/min): the faculty's INCREASE,
#: DECREASE and RESTART are an explicit rate that is higher than, lower than, or follows a stop of, the rate before it.
SUPPORTED_SEMANTICS = ("START", "INCREASE", "DECREASE", "STOP", "RESTART")
ENGINE_OPERATIONS = ("start", "adjust", "continue", "stop")
UNITS = "mcg/min"
UNSUPPORTED_SEMANTICS = ("mcg/kg/min", "target-based titration", "MAP or SBP target orders", "relative dose arithmetic", "a rate without a unit", "a restart without an explicit rate",
                         "automatic control", "another vasopressor", "an order that names no drug while the norepinephrine runs", "a bare continuation without a rate")

NOT_GRANTED = ("production", "resident deployment", "the first pilot", "consciousness authority", "mental_status writes", "terminal semantics", "collapse authority", "clinical validation", "a new calibration",
               "a recalibration of the tone, the pump coupling or the afterload coupling", "a weight-based dose", "target-based or automatic titration", "any other vasopressor", "pump-limited families",
               "pulmonary edema authority", "source control", "any non-pressure domain", "a resident-visible tone variable", "scoring")

# -- problem codes (every refusal has a name) ------------------------------------------------------------------------------------------------------------------------------------------------
NOT_A_GRANT = "NOT_A_NOREPINEPHRINE_GRANT"
UNKNOWN_GRANT = "NOREPINEPHRINE_GRANT_IS_NOT_IN_THE_REGISTRY"
WRONG_KIND = "WRONG_NOREPINEPHRINE_GRANT_KIND"
NOT_ACTIVE = "NOREPINEPHRINE_GRANT_IS_NOT_ACTIVE_FOR_DEVELOPMENT"
WRONG_MODE = "NOREPINEPHRINE_GRANT_MODE_IS_NOT_PRESSURE_ONLY"
DOMAIN_NOT_PRESSURE = "NOREPINEPHRINE_GRANT_DOMAIN_IS_NOT_EXACTLY_SBP_DBP_MAP"
EXCLUSION_WRONG = "NOREPINEPHRINE_GRANT_DOES_NOT_EXCLUDE_EVERY_NON_PRESSURE_DOMAIN"
PRESSURE_SNAPSHOT_MISMATCH = "NOREPINEPHRINE_GRANT_NAMES_ANOTHER_PRESSURE_SNAPSHOT"
TONE_SNAPSHOT_MISMATCH = "NOREPINEPHRINE_GRANT_NAMES_ANOTHER_TONE_SNAPSHOT"
CORE_MISMATCH = "NOREPINEPHRINE_GRANT_NAMES_ANOTHER_CORE_LINEAGE"
CASE_NOT_NAMED = "NOREPINEPHRINE_GRANT_DOES_NOT_NAME_THIS_CASE"
FAMILY_MISMATCH = "NOREPINEPHRINE_GRANT_IS_FOR_ANOTHER_FAMILY"
ENVIRONMENT_NOT_NAMED = "NOREPINEPHRINE_GRANT_DOES_NOT_NAME_THIS_ENVIRONMENT"
WINDOW_WRONG = "NOREPINEPHRINE_GRANT_WINDOW_IS_NOT_THE_PREDEFINED_LIMIT"
BOUNDARY_POLICY_WRONG = "NOREPINEPHRINE_GRANT_COLLAPSE_BOUNDARY_POLICY_IS_NOT_ESTABLISHED_PRECOMMIT_FAIL_CLOSED"
FAILURE_POLICY_WRONG = "NOREPINEPHRINE_GRANT_FAILURE_POLICY_IS_NOT_PERMANENT_FAIL_CLOSED"
OVERLAY_WRONG = "NOREPINEPHRINE_GRANT_OVERLAY_IS_NOT_COMPARISON_ONLY_UNDER_TONE"
ORDER_CONTRACT_WRONG = "NOREPINEPHRINE_GRANT_ORDER_CONTRACT_IS_NOT_THE_EXPLICIT_ABSOLUTE_RATE_CONTRACT"
WRITER_WRONG = "NOREPINEPHRINE_GRANT_WRITER_IS_NOT_THE_PINNED_ONE"
READER_WRONG = "NOREPINEPHRINE_GRANT_NAMES_ANOTHER_READER_SUCCESSOR"
NOT_GRANTED_INCOMPLETE = "NOREPINEPHRINE_GRANT_DOES_NOT_LIST_EVERY_THING_IT_DOES_NOT_GRANT"
FINGERPRINT_MISMATCH = "NOREPINEPHRINE_GRANT_FINGERPRINT_DOES_NOT_MATCH_ITS_BODY"
FINGERPRINT_NOT_PINNED = "NOREPINEPHRINE_GRANT_FINGERPRINT_IS_NOT_THE_PINNED_ONE"
FORBIDDEN_CLAIM = "NOREPINEPHRINE_GRANT_CARRIES_A_CLAIM_NO_FACULTY_DECISION_GRANTED"
EARLIER_GRANT_MUTATED = "NOREPINEPHRINE_GRANT_CLAIMS_TO_REPLACE_AN_EARLIER_GRANT"
RUN_DIMENSION_NOT_NAMED = "THE_RUN_DOES_NOT_NAME_EVERY_DIMENSION_THE_NOREPINEPHRINE_GRANT_BINDS"
NO_DECISION = "NOREPINEPHRINE_GRANT_HAS_NO_DECISION_REFERENCE"


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=list)


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    return value


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


def fingerprint_of(body: Mapping) -> str:
    """The digest of the grant's whole content except its own fingerprint."""
    return hashlib.sha256(_canonical(_plain({key: value for key, value in dict(body).items() if key != "fingerprint"})).encode("ascii")).hexdigest()


_BODY = {
    "kind": GRANT_KIND, "grant_id": GRANT_ID, "grant_version": GRANT_VERSION, "authority_mode": AUTHORITY_MODE, "status": STATUS_ACTIVE, "purpose": PURPOSE,
    "domain": DOMAIN, "excluded_domains": EXCLUDED_DOMAINS, "family": FAMILY, "cases": CASES, "environments": ENVIRONMENTS,
    "window": {"max_minute": WINDOW_MINUTES, "basis": "the predefined time limit of the experiment (FD-AUTH-07)"},
    "pressure_snapshot": {"id": PRESSURE_SNAPSHOT_ID, "value_digest": PRESSURE_VALUE_DIGEST, "configuration_digest": PRESSURE_CONFIGURATION_DIGEST,
                          "faculty_status": "RATIFIED_FOR_DEVELOPMENT_EXPERIMENTS", "unchanged_from_the_earlier_grant": True,
                          "decision_reference": "docs/COLA_DECISIONES_AI_ADVISOR.md FD-RATIFY-03 and FD-PROMOTE-01"},
    "tone_snapshot": {"id": TONE_SNAPSHOT_ID, "configuration_digest": TONE_CONFIGURATION_DIGEST, "values_digest": TONE_VALUES_DIGEST, "record_digest": TONE_RECORD_DIGEST,
                      "record_file_sha256": TONE_RECORD_FILE_SHA256, "ratification_digest": TONE_RATIFICATION_DIGEST, "human_record_digest": TONE_HUMAN_RECORD_DIGEST,
                      "faculty_status": "RATIFIED_FOR_DEVELOPMENT_EXPERIMENTS", "profile_field": PROFILE_FIELD, "selector_flag": TONE_SNAPSHOT_FLAG,
                      "witness": "CENTER_REFERENCE", "copied_not_recomputed": True, "low_and_high_are_test_witnesses_and_are_never_read": True,
                      "decision_reference": "docs/COLA_DECISIONES_AI_ADVISOR.md FD-TONE-RATIFY-01 to FD-TONE-RATIFY-09 and FD-NR-01"},
    "collapse_boundary": {"boundary": "ESTABLISHED", "impending_is_a_boundary": False, "source": "CONSCIOUSNESS_OVERLAY_V1_RUN", "checked": "PRECOMMIT_EVERY_MINUTE_OF_THE_INTERVAL",
                          "fails_closed": True, "is_a_terminal_state": False, "is_patient_death": False, "resident_text": "none"},
    "failure_policy": {"before_the_first_commit": "EXPERIMENT_HALTED_AND_THE_LEGACY_ENCOUNTER_IS_UNCHANGED", "after_the_first_commit": "INVALID_FOR_CONTINUATION",
                       "silent_fallback_to_the_legacy_engine": False, "is_patient_death": False,
                       "a_norepinephrine_order_the_contract_does_not_read": "PERMANENT_FAIL_CLOSED", "recovery_of_a_malformed_order": False,
                       "silent_fallback_to_the_earlier_grant_the_shadow_mapping_or_a_witness_name": False},
    "consciousness_overlay": {"snapshot_id": OVERLAY_SNAPSHOT_ID, "snapshot_status": "RATIFIED_FOR_DEVELOPMENT_EXPERIMENTS", "label": OVERLAY_LABEL, "role": "CANDIDATE_OVERLAY_NONAUTHORITATIVE",
                              "authority": False, "resident_visible": False, "writes_mental_status": False, "used_as_pressure_calibration": False,
                              "carries_the_same_tone_configuration_as_the_pressure": True, "under_tone": "CONSCIOUSNESS_UNDER_TONE_UNRESOLVED",
                              "boundary_is_a_guard_only_under_tone": True},
    "core_lineage": {"version_id": CORE_VERSION, "digest": CORE_DIGEST},
    "order_contract": {"drug": "norepinephrine", "engine_operations": ENGINE_OPERATIONS, "supported_semantics": SUPPORTED_SEMANTICS, "units": UNITS, "rates": "explicit absolute and finite",
                       "a_stop_needs_no_rate": True, "the_authority_verifies_the_contract_independently_of_the_shadow_mapping": True, "raw_order_remains_the_correct_boundary": True,
                       "unsupported_and_failed_closed": UNSUPPORTED_SEMANTICS, "reader_successor": {"git_blob": READER_GIT_BLOB, "sha256": READER_SHA256,
                                                                                                    "succession_record_digest": READER_SUCCESSION_RECORD_DIGEST,
                                                                                                    "checkpoint_digest": ORDER_SAFETY_CHECKPOINT_DIGEST}},
    "writer": {"types": WRITER_TYPES, "version": WRITER_VERSION, "one_infusion_one_ordered_rate": True, "no_drug_to_mmhg_equation": True,
               "path": "order -> rate history -> vasoconstrictor support -> common T -> pressure", "constants_changed": False},
    "replay_identity": {"artifact_label": ARTIFACT_LABEL, "distinguished_by": "the grant id and fingerprint and the norepinephrine_authority block", "an_artifact_names_this_grant_by_id_and_fingerprint": True, "tone_values_are_held_to_the_snapshot_in_every_captured_scenario": True,
                        "a_historical_artifact_replays_under_its_own_grant": True},
    "extends": {"grant_id": EARLIER_GRANT_ID, "pressure_scope_unchanged": True, "mutates_the_earlier_grant": False, "supersedes_the_earlier_grant": False},
    "not_granted": NOT_GRANTED,
    "decision_reference": "docs/COLA_DECISIONES_AI_ADVISOR.md FD-AUTHNE-01 to FD-AUTHNE-12",
    "issued_on": "2026-11-21",
}

#: Pinned in this file, like the other grants' fingerprints: the body above may not drift without a new version and a new pin.
GRANT_FINGERPRINT = "d79637c47343b82f0fbb4cb54cc89f5c3027d596d1e4fe086642e50580a45fb7"

GRANT = _freeze({**_BODY, "fingerprint": fingerprint_of(_BODY)})
REGISTERED_NE_GRANTS: tuple = (GRANT,)


def registered_grant(grant_id: Any, fingerprint: Any = None) -> Mapping[str, Any] | None:
    """The registered grant of this id (and, when given, this fingerprint), else None."""
    for grant in REGISTERED_NE_GRANTS:
        if grant.get("grant_id") == grant_id and (fingerprint is None or grant.get("fingerprint") == fingerprint):
            return grant
    return None


def lineage_of(grant: Any) -> dict:
    core = dict(dict(grant or {}).get("core_lineage") or {})
    return {"version_id": core.get("version_id"), "digest": core.get("digest")}


def _claims(value: Any) -> list:
    found: list = []
    if isinstance(value, Mapping):
        for item in list(value.keys()) + list(value.values()):
            found += _claims(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            found += _claims(item)
    elif isinstance(value, str) and value in FORBIDDEN_CLAIMS:
        found.append(value)
    return found


def grant_problems(grant: Any, *, case_id: str | None = None, environment: str | None = None, snapshot_id: str | None = None, tone_snapshot_id: str | None = None, family: str | None = None,
                   lineage: Mapping | None = None) -> list:
    """Every reason this grant does NOT authorize the run it is asked about (an empty list: it does). A dimension that is not passed is not judged here (``permits`` names every one)."""
    problems: list = []
    try:
        grant = _plain(grant)
        if not isinstance(grant, dict) or not grant.get("grant_id"):
            return [NOT_A_GRANT]
        if registered_grant(grant.get("grant_id"), grant.get("fingerprint")) is None:
            problems.append(UNKNOWN_GRANT)
        if grant.get("kind") != GRANT_KIND:
            problems.append(WRONG_KIND)
        if grant.get("status") != STATUS_ACTIVE or grant.get("purpose") != PURPOSE:
            problems.append(NOT_ACTIVE)
        if grant.get("authority_mode") != AUTHORITY_MODE:
            problems.append(WRONG_MODE)
        if tuple(grant.get("domain") or ()) != DOMAIN:
            problems.append(DOMAIN_NOT_PRESSURE)
        if tuple(grant.get("excluded_domains") or ()) != EXCLUDED_DOMAINS or set(grant.get("domain") or ()) & set(grant.get("excluded_domains") or ()):
            problems.append(EXCLUSION_WRONG)
        pressure = dict(grant.get("pressure_snapshot") or {})
        if (pressure.get("id"), pressure.get("value_digest"), pressure.get("configuration_digest")) != (PRESSURE_SNAPSHOT_ID, PRESSURE_VALUE_DIGEST, PRESSURE_CONFIGURATION_DIGEST) or (
                snapshot_id is not None and snapshot_id != pressure.get("id")):
            problems.append(PRESSURE_SNAPSHOT_MISMATCH)
        tone = dict(grant.get("tone_snapshot") or {})
        if (tone.get("id"), tone.get("configuration_digest"), tone.get("values_digest"), tone.get("record_digest"), tone.get("record_file_sha256"), tone.get("ratification_digest"),
                tone.get("human_record_digest"), tone.get("profile_field"), tone.get("selector_flag")) != (
                TONE_SNAPSHOT_ID, TONE_CONFIGURATION_DIGEST, TONE_VALUES_DIGEST, TONE_RECORD_DIGEST, TONE_RECORD_FILE_SHA256, TONE_RATIFICATION_DIGEST, TONE_HUMAN_RECORD_DIGEST, PROFILE_FIELD,
                TONE_SNAPSHOT_FLAG) or tone.get("witness") != "CENTER_REFERENCE" or tone.get("copied_not_recomputed") is not True or (
                tone_snapshot_id is not None and tone_snapshot_id != tone.get("id")):
            problems.append(TONE_SNAPSHOT_MISMATCH)
        core = dict(grant.get("core_lineage") or {})
        if (core.get("version_id"), core.get("digest")) != (CORE_VERSION, CORE_DIGEST) or (
                lineage is not None and (str(lineage.get("version_id")) != core.get("version_id") or str(lineage.get("digest")) != core.get("digest"))):
            problems.append(CORE_MISMATCH)
        if tuple(grant.get("cases") or ()) != CASES or (case_id is not None and case_id not in tuple(grant.get("cases") or ())):
            problems.append(CASE_NOT_NAMED)
        if grant.get("family") != FAMILY or (family is not None and family != FAMILY):
            problems.append(FAMILY_MISMATCH)
        if tuple(grant.get("environments") or ()) != ENVIRONMENTS or (environment is not None and environment not in tuple(grant.get("environments") or ())):
            problems.append(ENVIRONMENT_NOT_NAMED)
        window = dict(grant.get("window") or {})
        if window.get("max_minute") != WINDOW_MINUTES or isinstance(window.get("max_minute"), bool):
            problems.append(WINDOW_WRONG)
        boundary = dict(grant.get("collapse_boundary") or {})
        if (boundary.get("boundary") != "ESTABLISHED" or boundary.get("impending_is_a_boundary") is not False or boundary.get("fails_closed") is not True
                or boundary.get("is_a_terminal_state") is not False or boundary.get("checked") != "PRECOMMIT_EVERY_MINUTE_OF_THE_INTERVAL"):
            problems.append(BOUNDARY_POLICY_WRONG)
        policy = dict(grant.get("failure_policy") or {})
        if (policy.get("silent_fallback_to_the_legacy_engine") is not False or policy.get("after_the_first_commit") != "INVALID_FOR_CONTINUATION" or policy.get("is_patient_death") is not False
                or policy.get("a_norepinephrine_order_the_contract_does_not_read") != "PERMANENT_FAIL_CLOSED" or policy.get("recovery_of_a_malformed_order") is not False
                or policy.get("silent_fallback_to_the_earlier_grant_the_shadow_mapping_or_a_witness_name") is not False):
            problems.append(FAILURE_POLICY_WRONG)
        overlay = dict(grant.get("consciousness_overlay") or {})
        if (overlay.get("snapshot_id") != OVERLAY_SNAPSHOT_ID or overlay.get("label") != OVERLAY_LABEL or overlay.get("authority") is not False or overlay.get("resident_visible") is not False
                or overlay.get("writes_mental_status") is not False or overlay.get("used_as_pressure_calibration") is not False
                or overlay.get("carries_the_same_tone_configuration_as_the_pressure") is not True or overlay.get("under_tone") != "CONSCIOUSNESS_UNDER_TONE_UNRESOLVED"):
            problems.append(OVERLAY_WRONG)
        contract = dict(grant.get("order_contract") or {})
        reader = dict(contract.get("reader_successor") or {})
        if (contract.get("drug") != "norepinephrine" or tuple(contract.get("engine_operations") or ()) != ENGINE_OPERATIONS or tuple(contract.get("supported_semantics") or ()) != SUPPORTED_SEMANTICS
                or contract.get("units") != UNITS or contract.get("a_stop_needs_no_rate") is not True or contract.get("raw_order_remains_the_correct_boundary") is not True
                or contract.get("the_authority_verifies_the_contract_independently_of_the_shadow_mapping") is not True
                or tuple(contract.get("unsupported_and_failed_closed") or ()) != UNSUPPORTED_SEMANTICS):
            problems.append(ORDER_CONTRACT_WRONG)
        if (reader.get("git_blob"), reader.get("sha256"), reader.get("succession_record_digest"), reader.get("checkpoint_digest")) != (
                READER_GIT_BLOB, READER_SHA256, READER_SUCCESSION_RECORD_DIGEST, ORDER_SAFETY_CHECKPOINT_DIGEST):
            problems.append(READER_WRONG)
        writer = dict(grant.get("writer") or {})
        if tuple(writer.get("types") or ()) != WRITER_TYPES or writer.get("version") != WRITER_VERSION or writer.get("constants_changed") is not False or writer.get("no_drug_to_mmhg_equation") is not True:
            problems.append(WRITER_WRONG)
        if not set(NOT_GRANTED) <= set(grant.get("not_granted") or ()):
            problems.append(NOT_GRANTED_INCOMPLETE)
        extends = dict(grant.get("extends") or {})
        if extends.get("mutates_the_earlier_grant") is not False or extends.get("supersedes_the_earlier_grant") is not False or extends.get("grant_id") != EARLIER_GRANT_ID:
            problems.append(EARLIER_GRANT_MUTATED)
        if _claims(grant):
            problems.append(FORBIDDEN_CLAIM)
        if not grant.get("decision_reference"):
            problems.append(NO_DECISION)
        if grant.get("fingerprint") != fingerprint_of(grant):
            problems.append(FINGERPRINT_MISMATCH)
        if grant.get("fingerprint") != GRANT_FINGERPRINT:
            problems.append(FINGERPRINT_NOT_PINNED)
    except Exception as error:
        problems.append(f"{NOT_A_GRANT}: {type(error).__name__}")
    return list(dict.fromkeys(problems))


def permits(*, case_id: str | None, environment: str | None, snapshot_id: str | None, tone_snapshot_id: str | None, family: str | None, domain: Sequence[str],
            lineage: Mapping | None = None) -> tuple:
    """``(ok, reasons)``: does the REGISTERED grant authorize exactly this run? The ONE question the authority gate asks when the environment names the tone snapshot.

    The grant is read from the registry in this module, never from an environment variable, a file, a query parameter or the caller. Every dimension of the run must be named: an omitted one is a refusal,
    never a fail-open answer."""
    if tuple(domain) != DOMAIN:
        return False, [DOMAIN_NOT_PRESSURE]
    for name, value in (("case_id", case_id), ("environment", environment), ("snapshot_id", snapshot_id), ("tone_snapshot_id", tone_snapshot_id), ("family", family), ("lineage", lineage)):
        if value is None or (isinstance(value, str) and not value.strip()):
            return False, [f"{RUN_DIMENSION_NOT_NAMED}: {name}"]
    found = grant_problems(GRANT, case_id=case_id, environment=environment, snapshot_id=snapshot_id, tone_snapshot_id=tone_snapshot_id, family=family, lineage=lineage)
    return (not found), found


def summary(grant: Mapping | None = None) -> dict:
    """What an artifact says about the grant it ran under: identity and bindings, never the whole body."""
    grant = GRANT if grant is None else grant
    return {"grant_id": grant.get("grant_id"), "grant_version": grant.get("grant_version"), "kind": grant.get("kind"), "authority_mode": grant.get("authority_mode"),
            "fingerprint": grant.get("fingerprint"), "domain": list(grant.get("domain") or ()), "excluded_domains": list(grant.get("excluded_domains") or ()), "cases": list(grant.get("cases") or ()),
            "pressure_snapshot_id": dict(grant.get("pressure_snapshot") or {}).get("id"), "pressure_configuration_digest": dict(grant.get("pressure_snapshot") or {}).get("configuration_digest"),
            "tone_snapshot_id": dict(grant.get("tone_snapshot") or {}).get("id"), "tone_configuration_digest": dict(grant.get("tone_snapshot") or {}).get("configuration_digest"),
            "writer_version": dict(grant.get("writer") or {}).get("version"), "core_version": dict(grant.get("core_lineage") or {}).get("version_id"),
            "window_max_minute": dict(grant.get("window") or {}).get("max_minute"), "decision_reference": grant.get("decision_reference"), "extends_grant_id": dict(grant.get("extends") or {}).get("grant_id")}


def _guard_the_grant() -> None:
    """Refuse to import a grant that has drifted: its body must match the fingerprint pinned in this file, and be a grant ``grant_problems`` accepts."""
    if fingerprint_of(_BODY) != GRANT_FINGERPRINT:
        raise RuntimeError(f"the norepinephrine grant body changed (fingerprint {fingerprint_of(_BODY)}): a grant is never edited; issue a new version and pin it")
    found = grant_problems(GRANT)
    if found:
        raise RuntimeError(f"the registered norepinephrine grant is not a valid grant: {found}")


_guard_the_grant()
