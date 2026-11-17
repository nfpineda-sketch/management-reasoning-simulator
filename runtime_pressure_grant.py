"""P3-239/240: the explicit GI development PRESSURE authority grant (``GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V1``).

The faculty decision of 2026-11-12 authorizes the FIRST real development authority experiment for the GI PRESSURE domain only
(``sbp``, ``dbp`` and the ``map`` the display derives from them), on the two GI cases, with the already-approved pressure snapshot
``gi_pressure_committed`` and the certified common-core lineage. This module is that authorization, written as DATA that is bound, immutable
and fingerprinted, and as the ONE function the authority gate asks (``permits``). It is not a switch: the environment flags still have to
select an experiment, the nine older gate conditions still hold, and ``COMMON_CORE_RUNTIME_AUTHORITY`` stays ``False`` (a global flag alone,
or this grant alone, never starts anything).

What it binds: the authority mode (``PRESSURE_ONLY``), the exact allowed cases, the pressure snapshot by id and by the pinned digest of its
values, the certified core lineage by version and digest, the development-only status and environment, the experiment window, the collapse
boundary policy, the failure policy, the consciousness OVERLAY (``GI_DEVELOPMENT_SNAPSHOT_V1``, comparison only) and a version and fingerprint.

What it excludes, explicitly and not by omission: consciousness, ``mental_status``, collapse, terminal state, pulse, oxygenation, lactate and
haemoglobin. A grant that lists any of them in its domain, or fails to list one of them as excluded, is refused. Adding a domain is a NEW grant
version, never an edit of this one: the body is frozen, its fingerprint is pinned in this file, and the module does not import if they differ.

P3-379 (the faculty decision of 2026-11-16, FD-PROMOTE-05): ``GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V2`` is that NEW version. It binds the ratified
``GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1`` (by id, by the pinned digest of the approved values and by the pinned digest of the whole configuration), the certified lineage
(``PHASE2_AMENDMENT_2``: the promotion is configuration only, no core successor was needed) and the same scope, window, boundary, failure policy and overlay as version 1. Version 1 is
neither edited nor removed: it stays registered, readable, and the artifacts it authorized still verify and replay under it. Which grant a run needs is decided by the snapshot it names.
"""
from __future__ import annotations

import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping, Sequence

MODULE_VERSION = "P3-239/379"

GRANT_KIND = "FACULTY_GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT"
GRANT_ID = "GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V1"
GRANT_VERSION = 1
TEST_ONLY_FIXTURE_KIND = "TEST_ONLY_PRESSURE_GRANT_FIXTURE"
AUTHORITY_MODE = "PRESSURE_ONLY"
STATUS_ACTIVE = "ACTIVE_FOR_DEVELOPMENT_EXPERIMENT"
PURPOSE = "DEVELOPMENT_AUTHORITY_EXPERIMENT_ONLY"
#: The label every artifact of an experiment run under this grant carries, so it cannot be mistaken for a dormant evaluation or a historical run.
ARTIFACT_LABEL = "REAL_DEVELOPMENT_PRESSURE_AUTHORITY"
OVERLAY_LABEL = "FACULTY_ACCEPTED_FOR_DEVELOPMENT_COMPARISON"

DOMAIN = ("sbp", "dbp", "map")
EXCLUDED_DOMAINS = ("consciousness", "mental_status", "collapse", "terminal", "pulse", "oxygenation", "lactate", "hb")
FAMILY = "gi_bleed"
CASES = ("gi_bleed_57m", "gi_bleed_72f")
ENVIRONMENTS = ("development",)
WINDOW_MINUTES = 240
PRESSURE_SNAPSHOT_ID = "gi_pressure_committed"
#: Written as literals ON PURPOSE (a value read from the registry at import would be a comparison of a thing with itself): the pins below must agree with
#: ``runtime_authority.APPROVED_POINT_DIGESTS`` and with the lineage the layer declares, and a test and the check both compare them.
PRESSURE_VALUE_DIGEST = "c4fb416f30ad7afbcdc8b0c16d9464d98e87ba64054bebfb257f27848f4c1961"
CORE_VERSION = "PHASE2_AMENDMENT_2"
CORE_DIGEST = "a0af7d08fec3aaf93606b5635cad9f26980428a5ab8d8f66afb1317bb4586ce2"
OVERLAY_SNAPSHOT_ID = "GI_DEVELOPMENT_SNAPSHOT_V1"

# -- version 2 (P3-379): the ratified joint pressure snapshot ------------------------------------------------------------------------------------------------
GRANT_ID_V2 = "GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V2"
GRANT_VERSION_V2 = 2
PRESSURE_SNAPSHOT_ID_V2 = "GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1"
#: The digest of the values ``runtime_authority`` approved for version 2 (the seven profile magnitudes and the four scenario magnitudes), written as a literal on purpose.
PRESSURE_VALUE_DIGEST_V2 = "7270cf8599de0095088601acfe1df4d88b2aa9e38483fbdaf6844a1c2cce65c5"
#: The digest of the whole configuration identity (the six executable values and the records they come from): ``runtime_pressure_snapshot.CONFIGURATION_DIGEST``, as a literal.
CONFIGURATION_DIGEST_V2 = "70e6826cb2844bace6e3249058638340d00d80f84f8fdd2a5a2e752028db0641"
#: The snapshot ids that name a REAL registered pressure point: a run that names one of them never opens without the grant it is bound to.
REAL_SNAPSHOT_IDS = (PRESSURE_SNAPSHOT_ID, PRESSURE_SNAPSHOT_ID_V2)

#: What a grant of this kind may never claim, anywhere in its record.
FORBIDDEN_CLAIMS = ("CLINICALLY_VALIDATED", "CLINICALLY_CALIBRATED", "PRODUCTION_APPROVED", "RESIDENT_APPROVED", "CLINICALLY_APPROVED",
                    "CONSCIOUSNESS_AUTHORITY_GRANTED", "MENTAL_STATUS_AUTHORITY_GRANTED")

# -- problem codes (every refusal has a name) ------------------------------------------------------------------------------------------------
NOT_A_GRANT = "NOT_A_GRANT"
TEST_ONLY_GRANT_NOT_LOADABLE = "TEST_ONLY_GRANT_IS_NOT_LOADABLE"
WRONG_KIND = "WRONG_GRANT_KIND"
WRONG_MODE = "GRANT_MODE_IS_NOT_PRESSURE_ONLY"
NOT_ACTIVE = "GRANT_IS_NOT_ACTIVE_FOR_DEVELOPMENT"
WRONG_PURPOSE = "GRANT_PURPOSE_IS_NOT_DEVELOPMENT_ONLY"
DOMAIN_NOT_PRESSURE = "GRANT_DOMAIN_IS_NOT_EXACTLY_SBP_DBP_MAP"
EXCLUSION_MISSING = "GRANT_DOES_NOT_EXCLUDE_EVERY_NON_PRESSURE_DOMAIN"
EXCLUSION_OVERLAPS = "GRANT_EXCLUDES_A_DOMAIN_IT_ALSO_GRANTS"
SNAPSHOT_MISMATCH = "GRANT_NAMES_ANOTHER_PRESSURE_SNAPSHOT"
SNAPSHOT_DIGEST_MISMATCH = "GRANT_PINS_ANOTHER_SET_OF_PRESSURE_VALUES"
CORE_MISMATCH = "GRANT_NAMES_ANOTHER_CORE_LINEAGE"
CASE_NOT_NAMED = "GRANT_DOES_NOT_NAME_THIS_CASE"
FAMILY_MISMATCH = "GRANT_IS_FOR_ANOTHER_FAMILY"
ENVIRONMENT_NOT_NAMED = "GRANT_DOES_NOT_NAME_THIS_ENVIRONMENT"
WINDOW_WRONG = "GRANT_WINDOW_IS_NOT_THE_PREDEFINED_LIMIT"
BOUNDARY_POLICY_WRONG = "GRANT_COLLAPSE_BOUNDARY_POLICY_IS_NOT_ESTABLISHED_PRECOMMIT_FAIL_CLOSED"
FAILURE_POLICY_WRONG = "GRANT_FAILURE_POLICY_ALLOWS_A_SILENT_FALLBACK"
OVERLAY_WRONG = "GRANT_OVERLAY_IS_NOT_V1_COMPARISON_ONLY"
OVERLAY_AUTHORITATIVE = "GRANT_OVERLAY_CLAIMS_AUTHORITY_OR_RESIDENT_VISIBILITY"
FINGERPRINT_MISMATCH = "GRANT_FINGERPRINT_DOES_NOT_MATCH_ITS_BODY"
FINGERPRINT_NOT_PINNED = "GRANT_FINGERPRINT_IS_NOT_THE_PINNED_ONE"
FORBIDDEN_CLAIM = "GRANT_CARRIES_A_CLAIM_NO_FACULTY_DECISION_GRANTED"
CONFIGURATION_MISMATCH = "GRANT_PINS_ANOTHER_PRESSURE_CONFIGURATION"
PROMOTION_POLICY_WRONG = "GRANT_PROMOTION_POLICY_IS_NOT_CONFIG_ONLY_ON_THE_CERTIFIED_LINEAGE"
RUN_DIMENSION_NOT_NAMED = "THE_RUN_DOES_NOT_NAME_EVERY_DIMENSION_THE_GRANT_BINDS"
UNKNOWN_GRANT = "GRANT_IS_NOT_IN_THE_REGISTRY"
NO_DECISION = "GRANT_HAS_NO_DECISION_REFERENCE"
NOT_IN_REGISTRY_ID = "GRANT_ID_OR_VERSION_IS_NOT_THE_REGISTERED_ONE"


def _canonical(value: Any) -> str:
    return json.dumps(_plain(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


def fingerprint_of(body: Mapping) -> str:
    """The SHA-256 of the grant's canonical body (every field except ``fingerprint`` itself)."""
    return hashlib.sha256(_canonical({key: value for key, value in dict(body).items() if key != "fingerprint"}).encode("utf-8")).hexdigest()


_BODY = {
    "kind": GRANT_KIND, "grant_id": GRANT_ID, "grant_version": GRANT_VERSION, "status": STATUS_ACTIVE, "purpose": PURPOSE,
    "authority_mode": AUTHORITY_MODE, "family": FAMILY, "cases": CASES, "environments": ENVIRONMENTS,
    "domain": DOMAIN, "excluded_domains": EXCLUDED_DOMAINS,
    "pressure_snapshot": {"id": PRESSURE_SNAPSHOT_ID, "value_digest": PRESSURE_VALUE_DIGEST, "faculty_status": "APPROVED_FOR_DEVELOPMENT_EXPERIMENT",
                          "decision_reference": "docs/COLA_DECISIONES_AI_ADVISOR.md FD-P3-42"},
    "core_lineage": {"version_id": CORE_VERSION, "digest": CORE_DIGEST},
    "window": {"max_minute": WINDOW_MINUTES, "basis": "the predefined time limit of the experiment (FD-AUTH-07)"},
    "collapse_boundary": {"boundary": "ESTABLISHED", "impending_is_a_boundary": False, "source": "CONSCIOUSNESS_OVERLAY_V1_RUN",
                          "checked": "PRECOMMIT_EVERY_MINUTE_OF_THE_INTERVAL", "fails_closed": True, "is_a_terminal_state": False,
                          "is_patient_death": False, "resident_text": "none"},
    "failure_policy": {"before_the_first_commit": "EXPERIMENT_HALTED_AND_THE_LEGACY_ENCOUNTER_IS_UNCHANGED",
                       "after_the_first_commit": "INVALID_FOR_CONTINUATION", "silent_fallback_to_the_legacy_engine": False,
                       "is_patient_death": False},
    "consciousness_overlay": {"snapshot_id": OVERLAY_SNAPSHOT_ID, "snapshot_status": "RATIFIED_FOR_DEVELOPMENT_EXPERIMENTS", "label": OVERLAY_LABEL,
                              "role": "CANDIDATE_OVERLAY_NONAUTHORITATIVE", "authority": False, "resident_visible": False, "writes_mental_status": False,
                              "used_as_pressure_calibration": False},
    "decision_reference": "docs/COLA_DECISIONES_AI_ADVISOR.md FD-P3-203 (FD-AUTH-23 a FD-AUTH-31)",
    "issued_by_role": "faculty", "issued_on": "2026-11-12",
    "not_granted": ("production", "resident deployment", "the first pilot", "consciousness authority", "mental_status writes",
                    "terminal semantics", "clinical validation", "any non-pressure domain"),
}
#: The pinned fingerprint of the body above. Changing any byte of the grant changes this value, and the module then does not import: a grant is
#: never edited, a NEW version is issued (and pinned) instead.
GRANT_FINGERPRINT = "3c29c2b9eb070ea1728bea2b17fd4484ff42c5105070c9402b17e73b29c3c136"

GRANT: Mapping[str, Any] = _freeze({**_BODY, "fingerprint": fingerprint_of(_BODY)})

# -- version 2 (P3-379) ------------------------------------------------------------------------------------------------------------------------------------------
_BODY_V2 = {
    **{key: value for key, value in _BODY.items() if key not in ("grant_id", "grant_version", "pressure_snapshot", "decision_reference", "issued_on", "not_granted")},
    "grant_id": GRANT_ID_V2, "grant_version": GRANT_VERSION_V2,
    "pressure_snapshot": {"id": PRESSURE_SNAPSHOT_ID_V2, "value_digest": PRESSURE_VALUE_DIGEST_V2, "configuration_digest": CONFIGURATION_DIGEST_V2,
                          "faculty_status": "RATIFIED_FOR_DEVELOPMENT_EXPERIMENTS",
                          "decision_reference": "docs/COLA_DECISIONES_AI_ADVISOR.md FD-RATIFY-03 and FD-PROMOTE-01",
                          "record": "docs/revision/GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1.json"},
    "promotion": {"lineage_decision": "CONFIG_ONLY_PROMOTION_SUFFICIENT", "successor_core_required": False, "core_sources_changed": False,
                  "supersedes_grant_id": GRANT_ID, "supersedes_pressure_snapshot_id": PRESSURE_SNAPSHOT_ID,
                  "older_grant_remains_readable_and_its_artifacts_replayable": True, "new_calibration": False, "new_physiology": False, "amendment_3": "CLOSED",
                  "monitored_limitation": "GI_BLOOD_RESUSCITATION_LOW_END_RESPONSE (kept, not fixed)"},
    "decision_reference": "docs/COLA_DECISIONES_AI_ADVISOR.md FD-PROMOTE-01 to FD-PROMOTE-07 (on FD-RATIFY-01 to FD-RATIFY-07)",
    "issued_by_role": "faculty", "issued_on": "2026-11-16",
    "not_granted": ("production", "resident deployment", "the first pilot", "consciousness authority", "mental_status writes",
                    "terminal semantics", "clinical validation", "any non-pressure domain", "a new calibration", "Amendment 3 physiology", "norepinephrine", "source control"),
}
#: The pinned fingerprint of the body above (version 2). A grant is never edited: another body is another version.
GRANT_FINGERPRINT_V2 = "8a91145dbfe899dffdc5de1ed28b116c61f4fa5b462a49979727ce8b05b3642f"
GRANT_V2: Mapping[str, Any] = _freeze({**_BODY_V2, "fingerprint": fingerprint_of(_BODY_V2)})

#: What each registered version pins, by id. Read by ``grant_problems``: a grant is judged against ITS OWN version's pins and by no other version's.
_SPECS: Mapping[str, Mapping[str, Any]] = MappingProxyType({
    GRANT_ID: MappingProxyType({"version": GRANT_VERSION, "snapshot_id": PRESSURE_SNAPSHOT_ID, "value_digest": PRESSURE_VALUE_DIGEST, "fingerprint": GRANT_FINGERPRINT,
                                "configuration_digest": None}),
    GRANT_ID_V2: MappingProxyType({"version": GRANT_VERSION_V2, "snapshot_id": PRESSURE_SNAPSHOT_ID_V2, "value_digest": PRESSURE_VALUE_DIGEST_V2, "fingerprint": GRANT_FINGERPRINT_V2,
                                   "configuration_digest": CONFIGURATION_DIGEST_V2}),
})
#: The registry: the registered grants, by faculty decision (version 1 of 2026-11-12, version 2 of 2026-11-16). Read-only (a tuple of frozen mappings).
REGISTERED_GRANTS: tuple = (GRANT, GRANT_V2)


def registered_grant(grant_id: Any, fingerprint: Any = None) -> Mapping[str, Any] | None:
    """The registered grant of that id (and, when asked, that fingerprint), or None: how an artifact's grant block is resolved to the version it ran under."""
    for item in REGISTERED_GRANTS:
        if item.get("grant_id") == grant_id and (fingerprint is None or item.get("fingerprint") == fingerprint):
            return item
    return None


def grant_for_snapshot(snapshot_id: Any) -> Mapping[str, Any] | None:
    """The registered grant that binds this pressure snapshot, or None. A snapshot id is bound to exactly one version."""
    found = [item for item in REGISTERED_GRANTS if dict(item.get("pressure_snapshot") or {}).get("id") == snapshot_id]
    return found[0] if len(found) == 1 else None


def grant_problems(grant: Any, *, case_id: str | None = None, environment: str | None = None, snapshot_id: str | None = None, family: str | None = None,
                   lineage: Mapping | None = None) -> list:
    """Every reason ``grant`` does not authorize this run, by name. Empty means it does. Never raises."""
    problems: list = []
    try:
        if not isinstance(grant, Mapping):
            return [NOT_A_GRANT]
        if grant.get("kind") == TEST_ONLY_FIXTURE_KIND:
            return [TEST_ONLY_GRANT_NOT_LOADABLE]
        text = _canonical(grant)
        for claim in FORBIDDEN_CLAIMS:
            if claim in text:
                problems.append(f"{FORBIDDEN_CLAIM}: {claim}")
        if grant.get("kind") != GRANT_KIND:
            problems.append(WRONG_KIND)
        if grant.get("authority_mode") != AUTHORITY_MODE:
            problems.append(WRONG_MODE)
        if grant.get("status") != STATUS_ACTIVE:
            problems.append(NOT_ACTIVE)
        if grant.get("purpose") != PURPOSE:
            problems.append(WRONG_PURPOSE)
        if not str(grant.get("decision_reference") or "").strip():
            problems.append(NO_DECISION)
        spec = _SPECS.get(grant.get("grant_id"))
        if spec is None or grant.get("grant_version") != spec["version"] or isinstance(grant.get("grant_version"), bool):
            problems.append(NOT_IN_REGISTRY_ID)
            spec = _SPECS[GRANT_ID]                       # the rest is judged against version 1's pins, so an unknown id still gets every other refusal by name
        domain, excluded = tuple(grant.get("domain") or ()), tuple(grant.get("excluded_domains") or ())
        if domain != DOMAIN:
            problems.append(DOMAIN_NOT_PRESSURE)
        if not set(EXCLUDED_DOMAINS) <= set(excluded):
            problems.append(EXCLUSION_MISSING)
        if set(domain) & set(excluded):
            problems.append(EXCLUSION_OVERLAPS)
        snapshot = dict(grant.get("pressure_snapshot") or {})
        if snapshot.get("id") != spec["snapshot_id"] or (snapshot_id is not None and snapshot.get("id") != snapshot_id):
            problems.append(SNAPSHOT_MISMATCH)
        if snapshot.get("value_digest") != spec["value_digest"]:
            problems.append(SNAPSHOT_DIGEST_MISMATCH)
        if spec["configuration_digest"] is not None:
            if snapshot.get("configuration_digest") != spec["configuration_digest"]:
                problems.append(CONFIGURATION_MISMATCH)
            promotion = dict(grant.get("promotion") or {})
            if (promotion.get("lineage_decision") != "CONFIG_ONLY_PROMOTION_SUFFICIENT" or promotion.get("successor_core_required") is not False or promotion.get("core_sources_changed") is not False
                    or promotion.get("supersedes_grant_id") != GRANT_ID or promotion.get("new_calibration") is not False or promotion.get("new_physiology") is not False
                    or promotion.get("amendment_3") != "CLOSED"):
                problems.append(PROMOTION_POLICY_WRONG)
        core = dict(grant.get("core_lineage") or {})
        if core.get("version_id") != CORE_VERSION or core.get("digest") != CORE_DIGEST:
            problems.append(CORE_MISMATCH)
        if lineage is not None and (str(lineage.get("version_id")) != core.get("version_id") or str(lineage.get("digest")) != core.get("digest")):
            problems.append(CORE_MISMATCH)
        if tuple(grant.get("cases") or ()) != CASES:
            problems.append(CASE_NOT_NAMED)
        if case_id is not None and case_id not in tuple(grant.get("cases") or ()):
            problems.append(CASE_NOT_NAMED)
        if family is not None and (family != FAMILY or grant.get("family") != FAMILY):
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
        if (policy.get("silent_fallback_to_the_legacy_engine") is not False or policy.get("after_the_first_commit") != "INVALID_FOR_CONTINUATION"
                or policy.get("is_patient_death") is not False):
            problems.append(FAILURE_POLICY_WRONG)
        overlay = dict(grant.get("consciousness_overlay") or {})
        if overlay.get("snapshot_id") != OVERLAY_SNAPSHOT_ID or overlay.get("label") != OVERLAY_LABEL or overlay.get("used_as_pressure_calibration") is not False:
            problems.append(OVERLAY_WRONG)
        if overlay.get("authority") is not False or overlay.get("resident_visible") is not False or overlay.get("writes_mental_status") is not False:
            problems.append(OVERLAY_AUTHORITATIVE)
        if grant.get("fingerprint") != fingerprint_of(grant):
            problems.append(FINGERPRINT_MISMATCH)
        if grant.get("fingerprint") != spec["fingerprint"]:
            problems.append(FINGERPRINT_NOT_PINNED)
    except Exception as error:
        problems.append(f"{NOT_A_GRANT}: {type(error).__name__}")
    return problems


def permits(*, case_id: str | None, environment: str | None, snapshot_id: str | None, family: str | None, domain: Sequence[str],
            lineage: Mapping | None = None) -> tuple:
    """``(ok, reasons)``: does a REGISTERED grant authorize exactly this run? The ONE question the authority gate asks.

    The grant is read from the registry in this module, never from an environment variable, a file, a query parameter or the caller."""
    reasons: list = []
    if tuple(domain) != DOMAIN:
        return False, [DOMAIN_NOT_PRESSURE]
    # P3-248 (review L4): the ONE question names EVERY dimension of the run. ``grant_problems`` checks only the dimensions it is given (it is also used to judge a
    # grant by itself), so an omitted dimension here would have been a fail-open answer.
    for name, value in (("case_id", case_id), ("environment", environment), ("snapshot_id", snapshot_id), ("family", family), ("lineage", lineage)):
        if value is None or (isinstance(value, str) and not value.strip()):
            return False, [f"{RUN_DIMENSION_NOT_NAMED}: {name}"]
    for grant in REGISTERED_GRANTS:
        found = grant_problems(grant, case_id=case_id, environment=environment, snapshot_id=snapshot_id, family=family, lineage=lineage)
        if not found:
            return True, []
        reasons.extend(found)
    if not REGISTERED_GRANTS:
        reasons.append(UNKNOWN_GRANT)
    return False, reasons


def summary(grant: Mapping | None = None) -> dict:
    """What an artifact says about the grant it ran under: identity and bindings, never the whole body."""
    grant = GRANT if grant is None else grant
    extra = {} if "promotion" not in grant else {"pressure_configuration_digest": dict(grant.get("pressure_snapshot") or {}).get("configuration_digest"),
                                                 "lineage_decision": dict(grant.get("promotion") or {}).get("lineage_decision")}
    return {**extra, "grant_id": grant.get("grant_id"), "grant_version": grant.get("grant_version"), "kind": grant.get("kind"), "authority_mode": grant.get("authority_mode"),
            "fingerprint": grant.get("fingerprint"), "domain": list(grant.get("domain") or ()), "excluded_domains": list(grant.get("excluded_domains") or ()),
            "cases": list(grant.get("cases") or ()), "pressure_snapshot_id": dict(grant.get("pressure_snapshot") or {}).get("id"),
            "core_version": dict(grant.get("core_lineage") or {}).get("version_id"), "window_max_minute": dict(grant.get("window") or {}).get("max_minute"),
            "decision_reference": grant.get("decision_reference")}


def _guard_the_grant() -> None:
    """Refuse to import a grant that has drifted: its body must match the fingerprint pinned in this file, and be a grant ``grant_problems`` accepts."""
    if fingerprint_of(_BODY) != GRANT_FINGERPRINT:
        raise RuntimeError(f"the pressure grant body changed (fingerprint {fingerprint_of(_BODY)}): a grant is never edited; issue a new version and pin it")
    if fingerprint_of(_BODY_V2) != GRANT_FINGERPRINT_V2:
        raise RuntimeError(f"the pressure grant version 2 body changed (fingerprint {fingerprint_of(_BODY_V2)}): a grant is never edited; issue a new version and pin it")
    for registered in REGISTERED_GRANTS:
        found = grant_problems(registered)
        if found:
            raise RuntimeError(f"the registered pressure grant {registered.get('grant_id')} is not a valid grant: {found}")


_guard_the_grant()
