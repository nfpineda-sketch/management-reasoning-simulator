"""P3-14: the transactional machinery of a future limited authority, built DORMANT.

Nothing in this module can run today, and that is its first property. The legacy engine
(``family_engine.py``) is the only active runtime authority; ``runtime_shadow`` observes beside it without
authority; and this module holds what a FUTURE faculty-approved experiment would need -- a mode, a gate, an
ownership contract, a transaction, a validation and a counterfactual record -- so that the decision to
activate it is a separate, explicit, human one.

Why it cannot activate. ``LIMITED_COMMON_AUTHORITY`` is reachable only when NINE conditions hold at the same
time, and one of them is a faculty-approved parameter snapshot. ``APPROVED_SNAPSHOTS`` is empty on purpose:
P3-14 is not authorized to create one, so the gate refuses in every repository configuration, and a test
proves it. No environment string, no Streamlit secret, no query parameter, no case metadata and no user
input can satisfy the gate on its own.

What it does not do. It adds no call site to the encounter: ``app.py`` and ``pilot_acceptance.py`` do not
import it, so the runtime is byte-identical with this module present or absent. It computes no physiology --
a candidate comes from the shadow runner, which is the one place that advances the common core -- it approves
no clinical magnitude, it introduces no numeric clinical tolerance, and it writes nothing anywhere.

What a future commit would mean, if a faculty decision ever granted it: the three pressure fields of the
authority domain -- ``sbp`` and ``dbp``, with ``map`` as the display derives it from them -- would be
written together from one common pressure state, in a single step, after validation; everything else --
heart rate, rate, saturation, haemoglobin, lactate, consciousness, collapse, arrest, order fates, scoring
and the authoritative persistence -- would stay the legacy engine's. There is no partial pressure write
and no mid-encounter switch between engines.
"""
from __future__ import annotations

import hashlib
import json
import os
from copy import deepcopy
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Sequence

import runtime_shadow as rs

MODULE_VERSION = "P3-14"

#: The three modes of the Phase-3 integration. The third one is dormant: see the module docstring.
MODE_LEGACY = "legacy"
MODE_SHADOW_COMPARE = rs.MODE_SHADOW_COMPARE
MODE_LIMITED_COMMON_AUTHORITY = "limited_common_authority"
MODES = (MODE_LEGACY, MODE_SHADOW_COMPARE, MODE_LIMITED_COMMON_AUTHORITY)

#: The process flag a future experiment would set. Absent by default, and never sufficient by itself.
AUTHORITY_FLAG = "MRS_PHASE3_AUTHORITY"
#: Where a future experiment would name the approved snapshot it runs with.
SNAPSHOT_FLAG = "MRS_PHASE3_AUTHORITY_SNAPSHOT"
#: The environment a first experiment must run in (faculty decision of 2026-11-07).
ENVIRONMENT_FLAG = "MRS_PHASE3_AUTHORITY_ENVIRONMENT"
ALLOWED_ENVIRONMENTS = ("development", "faculty")
#: Names a future deployment could use to say "this is a pilot". Kept because they are explicit, but the
#: P3-17 review was right that they are not anchored to anything: no surface of the first pilot sets them.
PILOT_FLAGS = ("MRS_PILOT", "MRS_PILOT_RESIDENTS")
#: What the frozen pilot deployment REALLY requires, read from the pilot's own freeze
#: (``pilot_freeze.RUNTIME_FLAGS``) instead of from names invented here. A deployment that has these on is
#: the first pilot, whatever it calls itself.
PILOT_REQUIRED_ON = ("MRS_OFFLINE_CASES", "MRS_IMAGE_REQUIRE_REVIEW")


def pilot_deployment_markers() -> tuple:
    """The pilot's own runtime flags, from its freeze. Empty means the freeze could not be read."""
    try:
        import pilot_freeze
        declared = tuple(str(name) for name in (getattr(pilot_freeze, "RUNTIME_FLAGS", {}) or {}))
    except Exception:
        return ()
    return tuple(name for name in PILOT_REQUIRED_ON if name in declared)


def looks_like_the_pilot(environ: Mapping[str, str]) -> tuple:
    """(is_pilot, why): fails CLOSED when the pilot freeze cannot be read at all.

    ``not any(MRS_PILOT...)`` was the whole test before P3-17, and those two names exist nowhere else in
    the repository, so a real pilot deployment satisfied it. The anchor is now the pilot's own freeze.
    """
    named = [name for name in PILOT_FLAGS if str(environ.get(name, "") or "").strip()]
    if named:
        return True, f"a pilot flag is set: {named}"
    markers = pilot_deployment_markers()
    if not markers:
        return True, ("the pilot freeze could not be read, so a pilot deployment cannot be ruled out "
                      "(fails closed)")
    on = [name for name in markers if str(environ.get(name, "") or "").strip()]
    if len(on) == len(markers):
        return True, f"the deployment has the pilot's required runtime flags on: {on}"
    return False, ""

#: The first future authority family and its allowlisted certified cases (faculty decision).
AUTHORITY_FAMILY = "gi_bleed"
AUTHORITY_CASES = ("gi_bleed_57m", "gi_bleed_72f")
#: The ONLY outputs a first experiment could own. CRT is deferred: its divergence is only partially
#: explained, so the faculty kept it out of the first domain.
AUTHORITY_DOMAIN = ("sbp", "dbp", "map")

#: Owners in the ownership contract. There is no third value and no shared ownership.
COMMON = "common_authority"
LEGACY = "legacy_authority"
#: Read by nobody as authority: computed, compared and recorded only.
COMPARISON_ONLY = "comparison_only"
#: Shown to the resident, but computed by the application from fields the common core would own. P3-17
#: found this for the mean pressure: ``app.learner_vitals_snapshot`` derives MAP as
#: ``round((sbp + 2*dbp) / 3)`` from whatever SBP and DBP the authoritative state carries, so a common MAP
#: is NOT displayable without changing the display -- which this authorization forbids. The upside is that
#: the coherence P3-14-3 demands is guaranteed by the renderer: the MAP a resident sees is always a
#: function of the same two pressures beside it.
DERIVED_IN_DISPLAY = "derived_in_display_from_common"

#: The Phase-3 layer version a future experiment must find, written as a literal ON PURPOSE: comparing
#: ``rs.MODULE_VERSION`` with itself would be a condition that cannot fail. When the layer moves, the gate
#: refuses until someone updates this expectation deliberately.
EXPECTED_LAYER = "P3-11"

#: Why the gate refused. Every name here is a condition that must hold for authority to be possible.
GATE_CONDITIONS = ("authority_flag", "approved_snapshot", "family_and_case", "environment",
                   "authority_domain", "no_pilot", "no_unsupported_action", "phase2_digest",
                   "layer_version", "explicit_development_grant")

# -- P3-40: the one registered approval, and what it is NOT --------------------------------------------

#: The only purpose a registered approval may serve. The faculty decision of 2026-11-08 grants a FIRST
#: DEVELOPMENT-ONLY experiment and nothing else, so this is the only value the gate accepts.
PURPOSE_DEVELOPMENT_EXPERIMENT = "DEVELOPMENT_AUTHORITY_EXPERIMENT_ONLY"
APPROVED_PURPOSES = (PURPOSE_DEVELOPMENT_EXPERIMENT,)
#: The only faculty status a registered approval may carry.
STATUS_APPROVED_FOR_DEVELOPMENT = "APPROVED_FOR_DEVELOPMENT_EXPERIMENT"
APPROVED_STATUSES = (STATUS_APPROVED_FOR_DEVELOPMENT,)
#: Claims no faculty decision has ever granted. A registered approval carrying any of them -- anywhere in
#: its record -- is refused, so "approved for a development experiment" can never drift into "validated".
FORBIDDEN_CLAIMS = ("CLINICALLY_VALIDATED", "CLINICALLY_CALIBRATED", "PRODUCTION_APPROVED",
                    "RESIDENT_APPROVED", "CLINICALLY_APPROVED")

#: The seven pressure magnitudes a point must name, in the order the registry declares them.
SNAPSHOT_PARAMETERS = ("preload_curve_scale_ml", "arrival_preload_fraction", "pump_preload_coupling",
                       "afterload_sensitivity", "low_output_pressure_knee", "sbp_per_pressure_deficit",
                       "dbp_per_pressure_deficit")
#: The per-parameter evidence vocabulary P3-31 measured. Approving a POINT is not approving seven
#: physiological magnitudes, and the record has to say so magnitude by magnitude.
EVIDENCE_GI_IDENTIFIABLE = "GI_IDENTIFIABLE"
EVIDENCE_EXTERNALLY_CONSTRAINED = "NOT_GI_IDENTIFIABLE_EXTERNALLY_CONSTRAINED"
EVIDENCE_STRUCTURALLY_WEAK = "NOT_GI_IDENTIFIABLE_STRUCTURALLY_WEAK"
EVIDENCE_NOT_READ = "NOT_GI_IDENTIFIABLE_NOT_READ_BY_THE_CORE"
EVIDENCE_STATUSES = (EVIDENCE_GI_IDENTIFIABLE, EVIDENCE_EXTERNALLY_CONSTRAINED,
                     EVIDENCE_STRUCTURALLY_WEAK, EVIDENCE_NOT_READ)

#: The approval the faculty decision of 2026-11-08 registered: the committed Phase-2 point, for ONE
#: development experiment. Every value is the frozen registry's canonical value, so the physiology this
#: point runs is the physiology every certified Phase-2 artifact was produced with.
DEVELOPMENT_EXPERIMENT_SNAPSHOT: Mapping[str, Any] = MappingProxyType({
    "id": "gi_pressure_committed",
    "approved_by_faculty": True,
    "purpose": PURPOSE_DEVELOPMENT_EXPERIMENT,
    "faculty_status": STATUS_APPROVED_FOR_DEVELOPMENT,
    "decision": ("Faculty decisions A and G of 2026-11-08: this POINT is approved for the first "
                 "development-only GI pressure authority experiment. It is NOT clinically validated, NOT "
                 "clinically calibrated, NOT approved for production and NOT approved for residents. The "
                 "rationale is structural and experimental: it is the only surviving candidate the live "
                 "pipeline can run without adding point-selection code, it preserves deterioration in the "
                 "certified long-horizon scenario, it reaches no unresolved boundary in the accepted "
                 "battery, it is locally stable enough for the experiment, and no competing candidate has "
                 "stronger clinical evidence. Approving the point is not approving the clinical truth of "
                 "each magnitude."),
    "decision_reference": "docs/COLA_DECISIONES_AI_ADVISOR.md FD-P3-42 (faculty decisions A and G)",
    "runtime_parameter_snapshot_id": rs.PARAMETER_SNAPSHOT_ID,
    "parameters": MappingProxyType({
        "preload_curve_scale_ml": 833.3333333333334,
        "arrival_preload_fraction": 0.5,
        "pump_preload_coupling": 1.0,
        "afterload_sensitivity": 0.3,
        "low_output_pressure_knee": 0.5,
        "sbp_per_pressure_deficit": 45.0,
        "dbp_per_pressure_deficit": 25.0,
    }),
    "parameter_evidence": MappingProxyType({
        "preload_curve_scale_ml": MappingProxyType({
            "status": EVIDENCE_GI_IDENTIFIABLE,
            "why": "moving it alone across its declared region changes the GI systolic trajectory by up "
                   "to 33.673 mmHg in 34 of 34 certified scenarios (P3-31)"}),
        "arrival_preload_fraction": MappingProxyType({
            "status": EVIDENCE_GI_IDENTIFIABLE,
            "why": "the same sweep changes it by up to 62.802 mmHg in 34 of 34 scenarios (P3-31)"}),
        "afterload_sensitivity": MappingProxyType({
            "status": EVIDENCE_EXTERNALLY_CONSTRAINED,
            "why": "it enters only as 1/(1 + a(T - 1)) and GI holds T == 1 in all 1638 measured minutes, "
                   "so GI cannot see it; ACS and pulmonary embolism do constrain it, with a footprint of "
                   "at most 0.4 mmHg (P3-31, P3-35)"}),
        "pump_preload_coupling": MappingProxyType({
            "status": EVIDENCE_STRUCTURALLY_WEAK,
            "why": "it enters only as scale * P**c and needs a depressed pump AND a volume change at "
                   "once; GI holds P == 1 and every other certified family holds V == 0, so no certified "
                   "family identifies it (P3-31)"}),
        "low_output_pressure_knee": MappingProxyType({
            "status": EVIDENCE_NOT_READ,
            "why": "the knee left the pressure equation at P2J-1; it survives only as an admissibility "
                   "guard (0 < knee < 1) in clinical_core.derived"}),
        "sbp_per_pressure_deficit": MappingProxyType({
            "status": EVIDENCE_NOT_READ,
            "why": "not read by the core since P2J-1; read in one diagnostic that reconstructs the legacy "
                   "engine's raw systolic pressure to attribute a consciousness mismatch"}),
        "dbp_per_pressure_deficit": MappingProxyType({
            "status": EVIDENCE_NOT_READ,
            "why": "not read anywhere outside the calibration registry since P2J-1"}),
    }),
    "phase2_provenance": MappingProxyType({
        "closure_head": rs.PHASE2_CLOSURE_HEAD if hasattr(rs, "PHASE2_CLOSURE_HEAD") else "d2cca46",
        "digest": rs.PHASE2_DIGEST,
        "source": "clinical_core.derived.DEFAULT_PROFILE, read as a point; clinical_core.calibration "
                  "REGISTRY canonical values; status CANDIDATE, 0 of 58 entries FACULTY_APPROVED",
        "runtime_point": rs.PARAMETER_SNAPSHOT_ID,
    }),
    "scope": MappingProxyType({
        "family": AUTHORITY_FAMILY,
        "cases": AUTHORITY_CASES,
        "domain": AUTHORITY_DOMAIN,
        "environments": ALLOWED_ENVIRONMENTS,
        "pilot": "EXCLUDED",
        "production": "EXCLUDED",
        "resident_visible": "EXCLUDED",
        "scoring": "UNCHANGED_LEGACY",
        "nonpressure_physiology": "LEGACY_AUTHORITY",
        "artifact_store": "REQUIRED",
    }),
    "not_established": ("no parameter point is clinically valid", "no numeric acceptance tolerance exists",
                        "five of the seven magnitudes are not identifiable from GI evidence",
                        "technical success establishes no clinical calibration"),
})

#: Faculty-approved authority snapshots, by id. It holds exactly what an explicit faculty decision put
#: there, and today that is one DEVELOPMENT-ONLY point (P3-40). It was empty until 2026-11-08, and
#: ``test_runtime_authority.py`` fails if an entry appears whose decision is not recorded in the Decision
#: File, or which claims more than a development experiment.
#:
#: It is exposed READ-ONLY. P3-17 found the registry was a plain module dict, so any importer could fill
#: it; ``APPROVED_SNAPSHOTS["x"] = ...`` now raises. The writable mapping below is private and a test
#: injects into it deliberately, which is a name the production scan watches.
_APPROVED_SNAPSHOT_POINTS: dict = {
    DEVELOPMENT_EXPERIMENT_SNAPSHOT["id"]: DEVELOPMENT_EXPERIMENT_SNAPSHOT,
}
APPROVED_SNAPSHOTS: Mapping[str, Mapping[str, Any]] = MappingProxyType(_APPROVED_SNAPSHOT_POINTS)

#: The digest of the VALUES each registered approval was granted for, pinned here and not inside the
#: entry. The P3-40 adversarial review replaced the registered entry with one carrying the same id, the
#: same shape and other numbers, and the gate granted: nothing tied the approved values to the decision.
#: Now ``approved_snapshot`` recomputes this digest, and the import-time guard refuses a registry whose
#: values have moved. An in-process caller can still rebind both, which no check inside one process can
#: prevent; what this does prevent is the case that matters -- a future edit changing an approved value
#: without the faculty decision that would have to accompany it.
APPROVED_POINT_DIGESTS: Mapping[str, str] = MappingProxyType({
    "gi_pressure_committed": "c4fb416f30ad7afbcdc8b0c16d9464d98e87ba64054bebfb257f27848f4c1961",
})

#: What a faculty approval must carry. An id alone is not provenance: P3-17 showed that a lookup by id
#: accepted ``{}`` and even a string, and that nothing tied the approved point to the point the shadow
#: runner actually ran.
SNAPSHOT_REQUIRED_FIELDS = ("id", "parameters", "approved_by_faculty", "decision",
                            "runtime_parameter_snapshot_id")
#: What a REGISTERED approval must carry on top of that shape (P3-40). The test-only mechanism the
#: certified tests use carries a placeholder parameter on purpose and is not a registered approval, so
#: these are checked by ``registered_snapshot_is_complete`` and not by the shape check.
REGISTERED_SNAPSHOT_FIELDS = ("purpose", "faculty_status", "decision_reference", "parameter_evidence",
                              "phase2_provenance", "scope", "not_established")


def snapshot_is_wellformed(snapshot: Any) -> tuple:
    """(ok, reasons): the shape of a faculty approval, and its binding to the point that ran.

    The last check is the one that matters most: ``runtime_parameter_snapshot_id`` must be the id the
    shadow layer reports for the profile it ran (``runtime_shadow.PARAMETER_SNAPSHOT_ID``). Without it, a
    record could claim one approved point while the physiology ran another.
    """
    reasons = []
    if not isinstance(snapshot, Mapping):
        return False, (f"an approved snapshot must be a mapping, not {type(snapshot).__name__}",)
    for name in SNAPSHOT_REQUIRED_FIELDS:
        if name not in snapshot:
            reasons.append(f"the approval has no {name!r}")
    if snapshot.get("approved_by_faculty") is not True:
        reasons.append("approved_by_faculty is not True")
    parameters = snapshot.get("parameters")
    if not isinstance(parameters, Mapping) or not parameters:
        reasons.append("parameters must be a non-empty mapping of named magnitudes")
    ran = str(snapshot.get("runtime_parameter_snapshot_id") or "")
    if ran != rs.PARAMETER_SNAPSHOT_ID:
        reasons.append(f"the approved point {ran!r} is not the point the shadow runner ran "
                       f"({rs.PARAMETER_SNAPSHOT_ID!r})")
    registered = _APPROVED_SNAPSHOT_POINTS.get(str(snapshot.get("id") or ""))
    if registered is None:
        reasons.append("the snapshot is not in the faculty-approved registry")
    elif registered is not snapshot and dict(registered) != dict(snapshot):
        reasons.append("the snapshot differs from the registered approval of the same id")
    return (not reasons), tuple(reasons)


def registered_snapshot_is_complete(snapshot: Any) -> tuple:
    """(ok, reasons): what a REGISTERED faculty approval must carry beyond its shape (P3-40).

    The point is approved for an experiment, not declared true. So the record has to name its purpose,
    its faculty status, the decision that created it, the seven magnitudes, the evidence status of each
    one, the Phase-2 provenance, the scope it may be used in, and what it does not establish. And it may
    never carry a claim no faculty decision has granted -- checked over the whole record, not just the
    status field, so the claim cannot hide in a free-text line.
    """
    reasons = []
    if not isinstance(snapshot, Mapping):
        return False, (f"a registered approval must be a mapping, not {type(snapshot).__name__}",)
    for name in REGISTERED_SNAPSHOT_FIELDS:
        if name not in snapshot:
            reasons.append(f"the registered approval has no {name!r}")
    if snapshot.get("purpose") not in APPROVED_PURPOSES:
        reasons.append(f"purpose must be one of {list(APPROVED_PURPOSES)}, not "
                       f"{snapshot.get('purpose')!r}")
    if snapshot.get("faculty_status") not in APPROVED_STATUSES:
        reasons.append(f"faculty_status must be one of {list(APPROVED_STATUSES)}, not "
                       f"{snapshot.get('faculty_status')!r}")
    # A record may SAY it is not clinically validated; it may not CLAIM to be. The difference is the
    # negation in front, so the phrase is only a finding where the record does not deny it. Both the
    # record and the claims are normalised to single-spaced words first, so "CLINICALLY_VALIDATED",
    # "clinically validated" and "Clinically-Validated" are the same phrase to this check.
    def _words(value: str) -> str:
        return " " + " ".join("".join(
            character if character.isalnum() else " " for character in str(value)).upper().split()) + " "

    text = _words(json.dumps(snapshot, default=str, sort_keys=True))
    claimed = [claim for claim in FORBIDDEN_CLAIMS
               if _words(claim).strip() in text
               and f"NOT {_words(claim).strip()}" not in text
               and f"NEITHER {_words(claim).strip()}" not in text]
    if claimed:
        reasons.append(f"a registered approval may not claim {sorted(claimed)}: no faculty decision has "
                       f"granted any of them")
    parameters = snapshot.get("parameters")
    if not isinstance(parameters, Mapping) or tuple(sorted(parameters)) != tuple(sorted(SNAPSHOT_PARAMETERS)):
        reasons.append(f"parameters must name exactly {list(SNAPSHOT_PARAMETERS)}")
    evidence = snapshot.get("parameter_evidence")
    if not isinstance(evidence, Mapping) or tuple(sorted(evidence)) != tuple(sorted(SNAPSHOT_PARAMETERS)):
        reasons.append("parameter_evidence must carry one entry per named magnitude: approving a point is "
                       "not approving seven validated magnitudes")
    else:
        for name, entry in evidence.items():
            if not isinstance(entry, Mapping) or entry.get("status") not in EVIDENCE_STATUSES:
                reasons.append(f"the evidence status of {name!r} must be one of "
                               f"{list(EVIDENCE_STATUSES)}")
            elif not str(entry.get("why") or "").strip():
                reasons.append(f"the evidence status of {name!r} carries no reason")
    scope = snapshot.get("scope")
    if not isinstance(scope, Mapping):
        reasons.append("scope must be a mapping: an approval with no declared scope is a general switch")
    else:
        for name, expected in (("pilot", "EXCLUDED"), ("production", "EXCLUDED"),
                               ("resident_visible", "EXCLUDED")):
            if str(scope.get(name) or "").upper() != expected:
                reasons.append(f"scope[{name!r}] must be {expected!r}")
    return (not reasons), tuple(reasons)


def approved_values_match(snapshot_id: str, snapshot: Any) -> bool:
    """Whether the values offered under this id are the values that id was granted for.

    An id with no pinned digest is not a registered approval -- the test-only mechanism is the case --
    and this check does not apply to it. An id WITH a pinned digest must match it exactly.
    """
    expected = APPROVED_POINT_DIGESTS.get(str(snapshot_id))
    if not expected:
        return True
    if not isinstance(snapshot, Mapping):
        return False
    parameters = snapshot.get("parameters")
    if not isinstance(parameters, Mapping):
        return False
    return digest_of({str(name): value for name, value in parameters.items()}) == expected


def snapshot_permits(snapshot: Any, *, environment: str, family: str, case_id: str | None,
                     domain: Sequence[str]) -> tuple:
    """(ok, reasons): a registered approval may be NARROWER than the gate's own constants.

    The gate's constants say what this repository would ever allow; the approval says what THIS faculty
    decision allowed. Both have to hold, so widening a constant later cannot widen an approval already
    granted for a development experiment.
    """
    if not isinstance(snapshot, Mapping):
        return False, ("no approval to read a scope from",)
    scope = snapshot.get("scope")
    if not isinstance(scope, Mapping):
        # The test-only mechanism carries no scope on purpose: it is not a registered approval, and the
        # gate's own constants are the whole restriction for it.
        return True, ()
    reasons = []
    allowed_environments = tuple(str(name).strip().lower() for name in scope.get("environments") or ())
    if allowed_environments and str(environment or "").strip().lower() not in allowed_environments:
        reasons.append(f"the approval allows only {list(allowed_environments)}, not "
                       f"{str(environment)!r}")
    if scope.get("family") and str(scope["family"]) != str(family or ""):
        reasons.append(f"the approval is for family {scope['family']!r}, not {str(family)!r}")
    cases = tuple(str(name) for name in scope.get("cases") or ())
    if cases and str(case_id or "") not in cases:
        reasons.append(f"the approval allowlists {list(cases)}, and {str(case_id)!r} is not one of them")
    scoped_domain = tuple(str(name) for name in scope.get("domain") or ())
    if scoped_domain and tuple(str(name) for name in domain) != scoped_domain:
        reasons.append(f"the approval is for the domain {list(scoped_domain)}, not {list(domain)}")
    return (not reasons), tuple(reasons)


def approved_snapshot(snapshot_id: str | None, *, environment: str | None = None,
                      family: str | None = None, case_id: str | None = None,
                      domain: Sequence[str] | None = None) -> Mapping[str, Any] | None:
    """The faculty-approved snapshot of that id, or None.

    Today the registry holds exactly one entry, approved by the faculty decision of 2026-11-08 for a
    FIRST DEVELOPMENT-ONLY experiment (P3-40). A registered entry that is not well formed is NOT
    returned, and neither is one whose own declared scope does not cover the context asked about: a
    malformed or out-of-scope approval cannot open the gate.
    """
    if not snapshot_id:
        return None
    # The PRIVATE mapping is the registry: reading the public proxy would let
    # ``ra.APPROVED_SNAPSHOTS = {...}`` -- a rebinding no proxy can stop -- create an approval.
    found = _APPROVED_SNAPSHOT_POINTS.get(str(snapshot_id))
    if found is None or not snapshot_is_wellformed(found)[0]:
        return None
    if not approved_values_match(str(snapshot_id), found):
        return None
    if environment is not None or family is not None or case_id is not None or domain is not None:
        ok, _why = snapshot_permits(found, environment=str(environment or ""), family=str(family or ""),
                                    case_id=case_id, domain=tuple(domain or AUTHORITY_DOMAIN))
        if not ok:
            return None
    return found


# -- the ownership contract ----------------------------------------------------------------------------

def ownership(domain: Sequence[str] = AUTHORITY_DOMAIN) -> dict:
    """Who owns each comparable output in a future experiment: one owner each, named explicitly.

    The three pressures of the domain would be common; every other variable of the certified comparison
    table stays with the legacy engine. Nothing is left unassigned, which is what makes "no ambiguous
    ownership" a testable claim rather than an intention.
    """
    from clinical_core import comparison
    out: dict = {}
    for variable in comparison.VARIABLES:
        if variable.kind in ("core_only", "legacy_only"):
            out[variable.name] = COMPARISON_ONLY
            continue
        out[variable.name] = COMMON if variable.name in tuple(domain) else LEGACY
    for name in tuple(domain):
        out.setdefault(name, COMMON)
    if "map" in out and {"sbp", "dbp"} <= set(domain):
        out["map"] = DERIVED_IN_DISPLAY
    return out


def domain_is_coherent(domain: Sequence[str] = AUTHORITY_DOMAIN) -> tuple:
    """(ok, why): the pressure domain may not be cherry-picked field by field.

    ``map`` is a function of the same pressure state as ``sbp`` and ``dbp``: owning one without the others
    would show a resident a mean pressure that does not belong to the systolic and diastolic beside it.
    """
    asked = tuple(domain)
    pressures = {"sbp", "dbp", "map"}
    chosen = pressures & set(asked)
    if chosen and chosen != pressures:
        return False, (f"the pressure fields are one state: {sorted(pressures)} must be owned together, "
                       f"and {sorted(chosen)} was asked for")
    if not asked:
        return False, "an authority domain cannot be empty"
    unknown = [name for name in asked if name not in ownership(asked)]
    return (not unknown), ("" if not unknown else f"outputs with no ownership row: {unknown}")


# -- the gate ------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class AuthorityGate:
    """The ten conditions (nine until P3-240, plus the explicit development grant), evaluated together. ``granted`` is False unless every one of them holds."""

    conditions: Mapping[str, bool]
    reasons: tuple
    snapshot_id: str | None = None

    @property
    def granted(self) -> bool:
        return bool(self.conditions) and all(self.conditions.values())

    def to_dict(self) -> dict:
        return {"granted": self.granted, "conditions": dict(self.conditions),
                "reasons": list(self.reasons), "snapshot_id": self.snapshot_id}


def gate(state: Mapping | None = None, *, environ: Mapping[str, str] | None = None,
         domain: Sequence[str] = AUTHORITY_DOMAIN, case_id: str | None = None,
         family: str | None = None, unsupported: Sequence[str] | None = None) -> AuthorityGate:
    """Evaluate the ten conditions of a limited development authority. Never raises; refuses by default.

    The tenth (P3-240) is the explicit development grant ``runtime_pressure_grant.GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V1``: a registered, immutable,
    fingerprinted record that must name this exact case, environment, pressure snapshot, domain and core lineage. A flag alone, or the grant alone, never
    suffices: the other nine still hold, and the flags still select the experiment.

    The second condition -- a faculty-approved snapshot -- cannot hold in this repository, so the result
    is always refused today. The other eight are still evaluated, because a gate that short-circuits on
    the first failure would hide which of them a future experiment still has to satisfy.

    Two P3-17 findings shaped the signature. ``unsupported`` has no default any more: a caller that does
    not say which management actions ran gets a REFUSAL, because "nobody told me" used to read as "no
    unsupported action". And a non-empty ``state`` decides its own identity: ``case_id`` and ``family``
    are derived from it, and a caller that declares something else is refused instead of believed.
    """
    import runtime_shadow_evidence as ev
    environ = os.environ if environ is None else environ
    state = {} if state is None else dict(state)
    snapshot_id = str(environ.get(SNAPSHOT_FLAG, "") or "").strip() or None
    declared_family, declared_case = family, case_id
    if state:
        family = str(state.get("engine_family") or "")
        try:
            from clinical_core import legacy_adapter
            case_id = legacy_adapter.engine_case_id(state)
        except Exception:
            case_id = None
    else:
        family = str(family or "")
    identity_declared_against_state = bool(state) and (
        (declared_family is not None and str(declared_family) != str(family))
        or (declared_case is not None and str(declared_case) != str(case_id or "")))
    coherent, why_domain = domain_is_coherent(domain)
    # P3-240: the grant is read from its own registry (never from the environment, a file or the caller) and must name THIS run.
    import runtime_pressure_grant as grants
    member = rs.CORE_LINEAGE[-1]
    grant_ok, grant_why = grants.permits(case_id=case_id, environment=str(environ.get(ENVIRONMENT_FLAG, "") or "").strip().lower() or None, snapshot_id=snapshot_id,
                                         family=family, domain=tuple(domain), lineage={"version_id": member.version_id, "digest": member.digest})
    in_secrets = [name for name in (AUTHORITY_FLAG, SNAPSHOT_FLAG, ENVIRONMENT_FLAG)
                  if rs._named_in_secrets(name)]
    is_pilot, why_pilot = looks_like_the_pilot(environ)
    conditions = {
        "authority_flag": (str(environ.get(AUTHORITY_FLAG, "") or "").strip().lower()
                           == MODE_LIMITED_COMMON_AUTHORITY) and not in_secrets,
        "approved_snapshot": approved_snapshot(
            snapshot_id, environment=str(environ.get(ENVIRONMENT_FLAG, "") or ""), family=family,
            case_id=case_id, domain=tuple(domain)) is not None,
        "family_and_case": (family == AUTHORITY_FAMILY and str(case_id or "") in AUTHORITY_CASES
                            and not identity_declared_against_state),
        "environment": str(environ.get(ENVIRONMENT_FLAG, "") or "").strip().lower()
                       in ALLOWED_ENVIRONMENTS,
        "authority_domain": coherent and tuple(domain) == AUTHORITY_DOMAIN,
        "no_pilot": not is_pilot,
        "no_unsupported_action": unsupported is not None and not tuple(unsupported),
        "phase2_digest": ev.core_lineage_ok(),
        "layer_version": rs.MODULE_VERSION == EXPECTED_LAYER,
        "explicit_development_grant": grant_ok,
    }
    reasons = []
    if in_secrets:
        reasons.append(f"an authority flag is named in Streamlit secrets and is not honoured: {in_secrets}")
    if identity_declared_against_state:
        reasons.append(f"the caller declared family/case {declared_family!r}/{declared_case!r} against a "
                       f"state that is {family!r}/{case_id!r}")
    if unsupported is None:
        reasons.append("the caller did not declare which management actions ran: the condition fails "
                       "closed, because an undeclared action is not a supported action")
    if not conditions["approved_snapshot"]:
        registered = _APPROVED_SNAPSHOT_POINTS.get(str(snapshot_id)) if snapshot_id else None
        if registered is None:
            reasons.append(f"NO_FACULTY_APPROVED_AUTHORITY_SNAPSHOT_FOR_THIS_ID: {snapshot_id!r} is not "
                           f"in the approved registry {sorted(_APPROVED_SNAPSHOT_POINTS)}")
        else:
            reasons.extend(snapshot_is_wellformed(registered)[1])
            reasons.extend(snapshot_permits(
                registered, environment=str(environ.get(ENVIRONMENT_FLAG, "") or ""), family=family,
                case_id=case_id, domain=tuple(domain))[1])
    if not conditions["authority_flag"]:
        reasons.append(f"the authority process flag {AUTHORITY_FLAG} is not set to the authority mode")
    if not conditions["family_and_case"]:
        reasons.append(f"the case is not an allowlisted {AUTHORITY_FAMILY} case: {case_id!r}")
    if not conditions["environment"]:
        reasons.append(f"{ENVIRONMENT_FLAG} is not one of {list(ALLOWED_ENVIRONMENTS)}")
    if not conditions["authority_domain"]:
        reasons.append(why_domain or f"the domain must be exactly {list(AUTHORITY_DOMAIN)}")
    if not conditions["no_pilot"]:
        reasons.append(f"authority is impossible in the first pilot: {why_pilot}")
    if unsupported is not None and not conditions["no_unsupported_action"]:
        reasons.append(f"UNSUPPORTED_AUTHORITY_ACTION: {sorted(set(unsupported))}")
    if not conditions["phase2_digest"]:
        reasons.append(ev.core_lineage_reason() or "the common core lineage could not be evaluated")
    if not conditions["layer_version"]:
        reasons.append(f"the Phase-3 layer is {rs.MODULE_VERSION}, not {EXPECTED_LAYER}")
    if not conditions["explicit_development_grant"]:
        reasons.append(f"NO_EXPLICIT_DEVELOPMENT_GRANT_FOR_THIS_RUN: {list(grant_why)}")
    return AuthorityGate(conditions, tuple(reasons), snapshot_id)


def mode_decision(state: Mapping | None = None, *, environ: Mapping[str, str] | None = None,
                  **kwargs) -> tuple:
    """(mode, gate): the mode AND why it is that mode. P3-17: a bare string hides a refusal.

    ``mode()`` keeps returning a string for convenience, but a future call site must use this one, so
    that "legacy because nine conditions were evaluated and one failed" is never indistinguishable from
    "legacy because nobody asked for anything else".
    """
    decision = gate(state, environ=environ, **kwargs)
    if decision.granted:
        return MODE_LIMITED_COMMON_AUTHORITY, decision
    chosen = MODE_SHADOW_COMPARE if rs.mode(environ) == rs.MODE_SHADOW_COMPARE else MODE_LEGACY
    return chosen, decision


def mode(state: Mapping | None = None, *, environ: Mapping[str, str] | None = None, **kwargs) -> str:
    """The mode this process would run an encounter in. ``LIMITED_COMMON_AUTHORITY`` is unreachable.

    The shadow mode is the one ``runtime_shadow`` already decides; the authority mode needs the gate, and
    the gate needs a faculty-approved snapshot that does not exist. The reasons are discarded here on
    purpose: use ``mode_decision`` where they matter.
    """
    return mode_decision(state, environ=environ, **kwargs)[0]


def unreachable_because() -> tuple:
    """Why no PRODUCTION or resident-facing configuration can activate authority. Never empty.

    Until P3-40 this answered a stronger question -- why NO configuration could -- and the answer was
    that the registry was empty. The faculty decision of 2026-11-08 registered one point for one
    development experiment, so that stronger claim is no longer true and this function does not pretend
    it is. What it reports now is what still holds and still matters: a resident or a production
    deployment cannot enter authority. ``development_authority()`` says what a development configuration
    can do, in as many words.
    """
    reasons = []
    if not _APPROVED_SNAPSHOT_POINTS:
        reasons.append("APPROVED_SNAPSHOTS is empty: no faculty-approved authority snapshot exists")
    else:
        for name in sorted(_APPROVED_SNAPSHOT_POINTS):
            entry = _APPROVED_SNAPSHOT_POINTS[name]
            purpose = dict(entry).get("purpose") if isinstance(entry, Mapping) else None
            if purpose != PURPOSE_DEVELOPMENT_EXPERIMENT:
                reasons.append(f"the registered approval {name!r} has no development-experiment purpose, "
                               f"so nothing may use it")
            else:
                reasons.append(f"the registered approval {name!r} is {PURPOSE_DEVELOPMENT_EXPERIMENT}: "
                               f"its own scope excludes production, the first pilot and any "
                               f"resident-visible deployment")
    reasons.append(f"{ENVIRONMENT_FLAG} must be one of {list(ALLOWED_ENVIRONMENTS)}, and a production "
                   f"deployment is not one of them")
    reasons.append("a deployment carrying the first pilot's own runtime flags is refused by the gate, "
                   "and an unreadable pilot freeze fails closed")
    reasons.append(f"an authority flag named in Streamlit secrets is not honoured")
    return tuple(reasons)


def development_authority() -> dict:
    """What the faculty decision of 2026-11-08 granted, and what it did not. Plain, for people.

    Kept beside ``unreachable_because`` on purpose: the two together are the whole truth, and reading
    only one of them is how "approved for one experiment" turns into "approved".
    """
    registered = {name: dict(_APPROVED_SNAPSHOT_POINTS[name])
                  for name in sorted(_APPROVED_SNAPSHOT_POINTS)}
    complete = {name: registered_snapshot_is_complete(entry)[0] for name, entry in registered.items()}
    return {
        "granted": PURPOSE_DEVELOPMENT_EXPERIMENT,
        "registered": sorted(registered),
        "every_entry_is_development_only": all(
            entry.get("purpose") == PURPOSE_DEVELOPMENT_EXPERIMENT for entry in registered.values()),
        "every_entry_is_complete": all(complete.values()) if complete else True,
        "incomplete": sorted(name for name, ok in complete.items() if not ok),
        "family": AUTHORITY_FAMILY, "cases": list(AUTHORITY_CASES), "domain": list(AUTHORITY_DOMAIN),
        "environments": list(ALLOWED_ENVIRONMENTS),
        "excluded": ["production", "the first resident pilot", "any resident-visible deployment",
                     "scoring, which stays legacy and unchanged",
                     "every non-pressure variable, which stays legacy authority"],
        "not_established": ["clinical validity of any parameter point",
                            "any numeric acceptance tolerance",
                            "clinical calibration, which technical success does not establish"],
        "still_unreachable_for_production_because": list(unreachable_because()),
    }


def _guard_the_registry() -> None:
    """Refuse to import a registry that has drifted. A drifted approval is worse than none.

    Every entry must be a well-formed approval AND a complete registered approval: if a future edit adds
    an entry that claims clinical validation, omits its evidence annotations or declares no scope, this
    module does not load and the application does not start.
    """
    for name in sorted(_APPROVED_SNAPSHOT_POINTS):
        entry = _APPROVED_SNAPSHOT_POINTS[name]
        ok, why = snapshot_is_wellformed(entry)
        if not ok:
            raise RuntimeError(f"the approved snapshot {name!r} is not well formed: {list(why)}")
        ok, why = registered_snapshot_is_complete(entry)
        if not ok:
            raise RuntimeError(f"the registered approval {name!r} is incomplete: {list(why)}")
        if not approved_values_match(name, entry):
            raise RuntimeError(
                f"the values registered under {name!r} do not match APPROVED_POINT_DIGESTS: an approved "
                f"value may not move without the faculty decision that approves the new one")
    for name in sorted(APPROVED_POINT_DIGESTS):
        if name not in _APPROVED_SNAPSHOT_POINTS:
            raise RuntimeError(f"{name!r} has a pinned value digest but is not registered: the pin and "
                               f"the registry must say the same thing")



# -- the transaction -----------------------------------------------------------------------------------

#: A transaction's outcome. ``COMMITTED`` is only ever reachable with an approved snapshot.
PREPARED = "PREPARED"
VALIDATED = "VALIDATED"
COMMITTED = "COMMITTED"
ABORTED = "ABORTED"


class AuthorityRefused(Exception):
    """Raised when something asks a dormant transaction to do what only authority could do."""


#: The shape of a reproducibility digest. These two numbers describe sha256 hex, not a clinical
#: magnitude, and they live out here so that ``validate`` keeps no number of its own.
DIGEST_CHARACTERS = "0123456789abcdef"
DIGEST_LENGTH = 64


def is_digest(value: Any) -> bool:
    """Whether a value is a sha256 hex digest. P3-17: ``"same" == "same"`` used to satisfy a check."""
    return (isinstance(value, str) and len(value) == DIGEST_LENGTH
            and all(char in DIGEST_CHARACTERS for char in value.lower()))


@dataclass
class AuthorityTransaction:
    """One minute of a future authority experiment: capture, compute, validate, commit or abort.

    The transaction is the unit of atomicity. ``commit`` writes the three pressure fields of the domain
    together, into a copy the caller owns, and only after ``validate`` passed; any failure, at any stage,
    leaves the authoritative state exactly as it was. There is no partial pressure write, by construction:
    the write happens once, from one prepared mapping, at the end.

    It is exercisable in tests without being reachable in a runtime: a test constructs it with an explicit
    snapshot object, while ``open_for`` -- the only way a runtime could get one -- goes through the gate.
    """

    minute: int
    case_id: str
    family: str = AUTHORITY_FAMILY
    domain: tuple = AUTHORITY_DOMAIN
    snapshot: Mapping[str, Any] | None = None
    before: Mapping[str, Any] | None = None
    candidate: Mapping[str, Any] | None = None
    legacy_counterfactual: Mapping[str, Any] | None = None
    divergence: tuple = ()
    #: P3-17: ``state`` used to be a constructor field, so ``AuthorityTransaction(state=VALIDATED)``
    #: skipped validation entirely and committed anything. The stages are the only writers now.
    state: str = field(default=PREPARED, init=False)
    failures: list = field(default_factory=list, init=False)
    committed: tuple = field(default=(), init=False)
    reason: str = field(default="", init=False)
    #: Materialized by ``validate`` when it refuses, so a failure cannot be silent even if the caller
    #: ignores the returned ``False``.
    rollback: dict | None = field(default=None, init=False)

    @classmethod
    def open_for(cls, state: Mapping, *, environ: Mapping[str, str] | None = None,
                 minute: int = 0,
                 unsupported: Sequence[str] | None = None) -> "AuthorityTransaction | None":
        """The ONLY way a runtime could obtain a transaction: through the gate. Today always None."""
        decision = gate(state, environ=environ, unsupported=unsupported)
        if not decision.granted:
            return None
        from clinical_core import legacy_adapter
        return cls(minute=minute, case_id=str(legacy_adapter.engine_case_id(dict(state))),
                   snapshot=approved_snapshot(decision.snapshot_id))

    # -- stages ----------------------------------------------------------------------------------------
    def capture(self, authoritative: Mapping) -> "AuthorityTransaction":
        """Copy the authoritative state as it is before this minute. Nothing is written."""
        self.before = deepcopy(dict(authoritative))
        return self

    def compute(self, candidate: Mapping, legacy: Mapping | None = None) -> "AuthorityTransaction":
        """Take the common candidate for this minute, and the legacy counterfactual beside it.

        The candidate is computed elsewhere: ``runtime_shadow_families.ShadowPhysiologyRunner.advance`` is
        the one place that advances the common core, and this module never calls the physics itself.
        """
        self.candidate = deepcopy(dict(candidate))
        self.legacy_counterfactual = None if legacy is None else deepcopy(dict(legacy))
        return self

    def validate(self, *, invariants_hold: bool = True, replay_digest: str | None = None,
                 expected_digest: str | None = None, unsupported: Sequence[str] | None = None,
                 legacy_arrest: bool = False, failures: Sequence = ()) -> bool:
        """Every condition a future commit would need, and no numeric clinical tolerance among them.

        P3-17 hardened three of them. ``snapshot_approved`` checks the approval's shape, its membership in
        the registry and its binding to the parameter point the shadow layer actually ran, instead of
        ``is not None`` -- a string used to pass. ``supported_management`` fails closed when the caller
        says nothing. And ``minute_reproducible`` requires two real digests, so passing the same
        placeholder twice no longer satisfies it.
        """
        wellformed, why_snapshot = snapshot_is_wellformed(self.snapshot)
        digests_are_digests = all(is_digest(value) for value in (replay_digest, expected_digest))
        checks = {
            "snapshot_approved": wellformed,
            "domain_coherent": domain_is_coherent(self.domain)[0]
                               and tuple(self.domain) == AUTHORITY_DOMAIN,
            "case_eligible": self.case_id in AUTHORITY_CASES and self.family == AUTHORITY_FAMILY,
            "candidate_complete": bool(self.candidate) and all(
                self.candidate.get(name) is not None for name in self.domain),
            "invariants_hold": bool(invariants_hold),
            "no_core_failure": not [item for item in failures
                                    if getattr(item, "classification", "") == rs.UNEXPECTED],
            "no_unresolved_boundary": not [item for item in failures
                                           if getattr(item, "classification", "") == rs.BOUNDARY],
            "supported_management": unsupported is not None and not tuple(unsupported),
            "minute_reproducible": digests_are_digests and replay_digest == expected_digest,
            "no_legacy_arrest": not legacy_arrest,
        }
        self.failures = [name for name, ok in checks.items() if not ok]
        if self.failures:
            self.state = ABORTED
            self.reason = f"validation refused: {self.failures}"
            if not wellformed:
                self.reason += f" | snapshot: {list(why_snapshot)}"
            self.rollback = rollback_artifact(self, reason=self.reason, replay_digest=replay_digest)
            return False
        self.state = VALIDATED
        return True

    def refuse(self, failures: Sequence[str], *, reason: str = "", replay_digest: str | None = None) -> bool:
        """P3-223 (R2): abort a transaction whose OWN minute validated but whose interval did not.

        A turn that moves the clock by N minutes is one commit of the end state, and an intermediate minute that failed makes that commit ineligible.
        The transaction cannot see the intermediate minutes, so the site tells it: the transaction becomes ABORTED with its rollback artifact, exactly as
        a refused ``validate`` leaves it, and it can never be committed afterwards. Only a VALIDATED transaction can be refused this way."""
        if self.state != VALIDATED:
            return False
        self.failures = [str(name) for name in failures]
        self.state = ABORTED
        self.reason = reason or f"validation refused: {self.failures}"
        self.committed = ()
        self.rollback = rollback_artifact(self, reason=self.reason, replay_digest=replay_digest)
        return True

    def commit(self, target: Mapping, *, environ: Mapping[str, str] | None = None) -> dict:
        """Write the common fields of the authority domain at once, or raise without touching anything.

        Returns a NEW mapping: the caller decides what to do with it, so a refused transaction cannot
        leave a half-updated state behind even by accident.

        Four P3-17 findings are closed here. The gate is re-evaluated AT COMMIT, so a transaction built
        by hand cannot write while the nine conditions refuse. The target must be the state this
        transaction captured, so yesterday's pressures cannot be written onto an advanced minute. Only
        the fields the ownership contract calls ``common_authority`` are written -- ``map`` is derived by
        the display and is NOT written, which is what keeps the recorded and the shown mean pressure from
        disagreeing by a millimetre. And any failure inside the write leaves the transaction ABORTED and
        raises ``AuthorityRefused``, instead of leaving it committable again.
        """
        try:
            if self.state != VALIDATED:
                raise AuthorityRefused(self.reason
                                       or "a transaction commits only after validation passed")
            wellformed, why_snapshot = snapshot_is_wellformed(self.snapshot)
            if not wellformed:
                raise AuthorityRefused(f"NO_FACULTY_APPROVED_AUTHORITY_SNAPSHOT: {list(why_snapshot)}")
            if self.before is None:
                raise AuthorityRefused("nothing was captured: a commit must know the state it replaces")
            decision = gate(self.before, environ=environ, domain=self.domain, unsupported=())
            if not decision.granted:
                raise AuthorityRefused(f"the authority gate refuses at commit: {list(decision.reasons)}")
            if dict(self.before).get("sim_time") != dict(target).get("sim_time"):
                raise AuthorityRefused("the commit target is not the state this transaction captured "
                                       f"(captured minute {dict(self.before).get('sim_time')!r}, target "
                                       f"{dict(target).get('sim_time')!r})")
            owners = ownership(self.domain)
            writable = tuple(name for name in self.domain if owners.get(name) == COMMON)
            values = {name: (self.candidate or {}).get(name) for name in writable}
            bad = sorted(name for name, value in values.items()
                         if isinstance(value, bool) or not isinstance(value, (int, float)))
            # The display's own mean pressure, written with the two it derives from, so the state, the
            # screen and the management trace carry the same number (P3-19 review). It is NOT the core's
            # mean, which P3-17 refused: it is the function the renderer already applies.
            mean = derived_map(values.get("sbp"), values.get("dbp"))
            if "map" in self.domain and owners.get("map") == DERIVED_IN_DISPLAY and mean is not None:
                values["map"] = mean
            if not writable or bad:
                raise AuthorityRefused(f"the candidate has no usable value for {bad or list(writable)}")
            prepared = dict(deepcopy(dict(target)))
            observable = dict(prepared.get("observable") or {})
            observable.update(values)
            prepared["observable"] = observable
        except Exception as error:
            self.state = ABORTED
            self.reason = self.reason or str(error)
            self.committed = ()
            self.rollback = rollback_artifact(self, reason=f"commit refused: {error}")
            if isinstance(error, AuthorityRefused):
                raise
            raise AuthorityRefused(f"commit failed and nothing was written: {error!r}") from error
        self.committed = tuple(sorted(values))
        self.state = COMMITTED
        return prepared

    def abort(self, reason: str) -> dict:
        """Stop visibly, with nothing committed. The first experiment's failure policy is a hard stop."""
        self.state = ABORTED
        self.reason = reason
        self.committed = ()
        return self.record()

    # -- the record ------------------------------------------------------------------------------------
    def record(self) -> dict:
        """What a future experiment would persist: the candidate, the counterfactual and the decision."""
        return {
            "runtime_authority": "legacy" if self.state != COMMITTED else "common_pressure_domain",
            "common_core_runtime_authority": rs.COMMON_CORE_RUNTIME_AUTHORITY,
            "mode": MODE_LIMITED_COMMON_AUTHORITY,
            "module": MODULE_VERSION,
            "state": self.state,
            "minute": self.minute,
            "case_id": self.case_id,
            "family": self.family,
            "domain": list(self.domain),
            "ownership": ownership(self.domain),
            # A malformed snapshot must still be recordable: ``dict("a string")`` raised, so a refusal
            # could not even write its own rollback artifact (P3-17).
            "snapshot": (dict(self.snapshot) if isinstance(self.snapshot, Mapping) else self.snapshot),
            "candidate": (None if self.candidate is None else dict(self.candidate)),
            "legacy_counterfactual": (None if self.legacy_counterfactual is None
                                      else dict(self.legacy_counterfactual)),
            "divergence": [dict(item) if isinstance(item, Mapping) else vars(item)
                           for item in self.divergence],
            "validation_failures": list(self.failures),
            "committed": list(self.committed),
            "reason": self.reason,
            "versions": rs.family_versions(self.family),
        }


def counterfactual(candidate: Mapping, legacy: Mapping, minute: int, family: str = AUTHORITY_FAMILY,
                   domain: Sequence[str] = AUTHORITY_DOMAIN) -> dict:
    """The comparison a future experiment must keep: common candidate against legacy, classified.

    The legacy engine keeps computing as a comparator even where the common core would hold authority --
    it is what makes a rollback and a later research reading possible -- and it is never the resident's
    authority in that experiment, nor clinical ground truth in the comparison.
    """
    rows = {}
    for name in tuple(domain):
        left, right = legacy.get(name), candidate.get(name)
        if left is None or right is None:
            rows[name] = {"status": rs.NOT_COMPARABLE, "legacy": left, "common": right}
            continue
        rows[name] = {"status": ("MATCH" if left == right else "DIFFERS"),
                      "legacy": left, "common": right, "difference": right - left
                      if isinstance(left, (int, float)) and isinstance(right, (int, float)) else None}
    return {"minute": minute, "family": family, "domain": list(domain), "rows": rows,
            "reading": "the legacy engine is the comparator, not clinical ground truth; a difference here "
                       "is two architectures differing and no numeric tolerance is defined"}


# -- P3-15: eligibility, and the mechanics of a visible failure ----------------------------------------

#: How one encounter (or one scenario of the acceptance battery) reads against the future authority gate.
ELIGIBLE_BUT_NO_SNAPSHOT = "ELIGIBLE_EXCEPT_MISSING_APPROVED_SNAPSHOT"
#: P3-40: what a structurally eligible scenario is once an approval covering it exists. Keeping the name
#: above for this state would have the reading say "missing approved snapshot" while one is registered.
ELIGIBLE_FOR_DEVELOPMENT = "ELIGIBLE_FOR_DEVELOPMENT_AUTHORITY_EXPERIMENT"
#: Both readings mean "nothing structural stands in the way". They differ only in whether the faculty
#: decision has happened, which is exactly the distinction a reader needs.
ELIGIBLE_CLASSES = (ELIGIBLE_BUT_NO_SNAPSHOT, ELIGIBLE_FOR_DEVELOPMENT)
INELIGIBLE_UNSUPPORTED = "INELIGIBLE_UNSUPPORTED_ACTION"
INELIGIBLE_OTHER = "INELIGIBLE_OTHER_REASON"

#: The GI management actions a pressure authority must be able to mirror and replay exactly. Anything else
#: the engine executes makes the encounter ineligible: it is not ignored and it is not approximated.
SUPPORTED_ACTIONS = ("fluid", "blood", "ppi", "procedure", "endoscopy", "oxygen", "reassessment",
                     "consult")
#: What the engine may report that carries no physiology and therefore never blocks eligibility.
STRUCTURAL_ACTIONS = ("reassessment", "consult", "diagnostic")

# -- P3-212 (FD-P3-NEW-03): the disposition of an order the engine EXECUTED and the common core does not model ----------------------------------
SUPPORTED_MODELED = "SUPPORTED_MODELED"
STRUCTURAL_ONLY = "STRUCTURAL_ONLY"
EXECUTED_NO_COMMON_PHYSIOLOGY = "EXECUTED_NO_COMMON_PHYSIOLOGY"
HELD_NOT_EXECUTED = "HELD_NOT_EXECUTED"
TERMINAL_NOT_EXECUTABLE = "TERMINAL_NOT_EXECUTABLE"
UNSUPPORTED_ACTION = "UNSUPPORTED_ACTION"
ACTION_DISPOSITIONS = (SUPPORTED_MODELED, STRUCTURAL_ONLY, EXECUTED_NO_COMMON_PHYSIOLOGY, HELD_NOT_EXECUTED, TERMINAL_NOT_EXECUTABLE,
                       UNSUPPORTED_ACTION)
#: The EXPLICIT allowlist of classes whose execution is acknowledged and traced but creates NO common-core contributor and changes NO physiology.
#: It is never inferred and never widened by a rule: a class enters this map by a faculty decision, with the reason written here. Vascular access
#: is the first (FD-P3-NEW-03): no physiologic effect is invented for it, and an authority transaction may continue through it.
NO_COMMON_PHYSIOLOGY_ACTIONS = MappingProxyType({
    "vascular_access": "peripheral or intraosseous access is placed, or already in place: the engine records the fact and the common core models "
                       "no effect of it (fluids and blood execute without it and carry their own volume)",
})
#: The ledger's fates that mean the order did NOT act (read lazily from the repository's own vocabulary, never copied).
_HELD_FATES = frozenset({"HELD_CLARIFICATION", "HELD_REASONING"})

# -- P3-215: every route by which the engine's clock moves ---------------------------------------------------------------------------------------
#: An order turn (``execute_bundle``) and clinical time spent OUTSIDE an order turn (``app.spend_clinical_time``: a history question, an examination).
#: The P3-208 review found the second never reached the site. Both are routes now, an unknown one is refused, and the page reaches both through ONE hook.
ORDER_TURN = "order_turn"
CLINICAL_TIME = "clinical_time_outside_an_order_turn"
KNOWN_ROUTES = (ORDER_TURN, CLINICAL_TIME)
UNKNOWN_ROUTE = "UNKNOWN_CLOCK_ROUTE"
#: A turn that did NOT advance the clock and whose actions are only structural or acknowledged-no-physiology (an IV line, a consult) has no new
#: physiological minute: nothing to commit, nothing to validate beyond the management class, and it does not halt (FD-P3-NEW-03). It is recorded.
NO_ADVANCE_TURN = "NO_ADVANCE_TURN_NOTHING_TO_COMMIT"
NO_ADVANCE_OK = tuple(sorted((set(STRUCTURAL_ACTIONS) | set(NO_COMMON_PHYSIOLOGY_ACTIONS)) - {"diagnostic"}))


def disposition_of(kind: Any, fate: Any = None) -> str:
    """The disposition of ONE order class, given the fate the ledger settled for it (None before settlement).

    A fate that says the order did not act wins over the class: a held order is HELD_NOT_EXECUTED and a terminal one TERMINAL_NOT_EXECUTABLE
    whatever it is; a recorded-not-modelled or unrecognized order is UNSUPPORTED_ACTION. Only then does the class decide."""
    name = str(kind or "").strip().lower() or "untyped_action"
    settled = str(fate or "").strip().upper()
    if settled in _HELD_FATES:
        return HELD_NOT_EXECUTED
    if settled == TERMINAL_NOT_EXECUTABLE:
        return TERMINAL_NOT_EXECUTABLE
    if settled and settled in {str(item) for item in fates_that_did_not_act()}:
        return UNSUPPORTED_ACTION
    if name in NO_COMMON_PHYSIOLOGY_ACTIONS:
        return EXECUTED_NO_COMMON_PHYSIOLOGY
    if name in STRUCTURAL_ACTIONS and name not in SUPPORTED_ACTIONS:
        return STRUCTURAL_ONLY
    if name in SUPPORTED_ACTIONS:
        return STRUCTURAL_ONLY if name in STRUCTURAL_ACTIONS else SUPPORTED_MODELED
    return UNSUPPORTED_ACTION


def executed_no_common_physiology(rows: Sequence | None) -> tuple:
    """The order rows of a turn that are EXECUTED_NO_COMMON_PHYSIOLOGY, each recognised EXACTLY ONCE (by canonical order id; a repeated receipt of
    the same order is one event). A row is ``{"order_id", "type" | "class", "fate"}``: what ``action_fates`` and the settled ledger carry."""
    out, seen = [], set()
    for row in list(rows or []):
        item = dict(row) if isinstance(row, Mapping) else {}
        kind = item.get("type") or item.get("class") or item.get("kind")
        if str(kind or "").strip().lower() not in NO_COMMON_PHYSIOLOGY_ACTIONS:
            continue
        order = str(item.get("order_id") or "").strip()
        if disposition_of(kind, item.get("fate")) != EXECUTED_NO_COMMON_PHYSIOLOGY:
            continue
        if order and order in seen:
            continue
        seen.add(order)
        out.append({"order_id": order, "class": str(kind).strip().lower(), "fate": str(item.get("fate") or ""),
                    "disposition": EXECUTED_NO_COMMON_PHYSIOLOGY, "contributor": None, "physiological_mutation": False})
    return tuple(out)


@dataclass(frozen=True)
class AuthorityEligibility:
    """Whether one encounter COULD have run with pressure authority, from structural facts only."""

    classification: str
    case_id: str
    scenario: str | None
    reasons: tuple
    unsupported: tuple
    facts: Mapping[str, Any]

    @property
    def eligible_but_for_the_snapshot(self) -> bool:
        return self.classification == ELIGIBLE_BUT_NO_SNAPSHOT

    @property
    def structurally_eligible(self) -> bool:
        """Nothing structural stands in the way, whether or not an approval exists yet."""
        return self.classification in ELIGIBLE_CLASSES

    def to_dict(self) -> dict:
        return {"classification": self.classification, "case_id": self.case_id,
                "scenario": self.scenario, "reasons": list(self.reasons),
                "unsupported": list(self.unsupported), "facts": dict(self.facts)}


def eligibility(scenario: Mapping, *, environ: Mapping[str, str] | None = None) -> AuthorityEligibility:
    """Read one acceptance scenario against the future authority gate. Structural facts, no tolerance.

    The facts come from the P3-11 evidence of that scenario -- its case, its action coverage, its declared
    gaps, whether its replay reproduced the live run digest by digest, and whether the shadow recorded a
    failure or a boundary -- so eligibility is computed from what was observed, never from an opinion
    about whether a difference is small.

    Until P3-40 every eligible scenario returned ``ELIGIBLE_EXCEPT_MISSING_APPROVED_SNAPSHOT``, because
    the one condition nothing here could satisfy was the faculty-approved snapshot. The faculty decision
    of 2026-11-08 registered one development-only approval, so a scenario this approval covers now reads
    ``ELIGIBLE_FOR_DEVELOPMENT_AUTHORITY_EXPERIMENT`` instead: the reading may not say a snapshot is
    missing while one is registered. Neither class promises anything clinical.
    """
    environ = os.environ if environ is None else environ
    coverage = dict(scenario.get("coverage") or {})
    # A class the coverage calls fully mirrored but that is NOT in the list of actions a pressure
    # authority must be able to mirror exactly is a contradiction, not a pass: P3-17 found that
    # SUPPORTED_ACTIONS was read by nobody, so it decided nothing.
    contradictory = tuple(sorted(kind for kind, how in coverage.items()
                                 if str(how.get("status")) == "FULLY_MIRRORED"
                                 and str(kind).strip().lower() not in SUPPORTED_ACTIONS
                                 and str(kind).strip().lower() not in NO_COMMON_PHYSIOLOGY_ACTIONS))
    # P3-22: the settled order classes of the whole scenario go through the same filter as the call
    # site's. The coverage is built from the engine's action summaries, and an order the engine does not
    # model (``not_modelled``) produces none, so it used to pass unseen: eligibility and the transaction
    # gave two different answers for the same scenario. They now give one.
    settled = tuple(str(pair[0]) for pair in (scenario.get("fates") or ()) if pair and pair[0])
    unsupported = tuple(sorted(set(
        [kind for kind, how in coverage.items() if str(how.get("status")) == "UNSUPPORTED"
         and str(kind).strip().lower() not in NO_COMMON_PHYSIOLOGY_ACTIONS]
        + list(contradictory) + list(unsupported_among(settled)))))
    declared = tuple(sorted({str(gap.get("kind")) for gap in (scenario.get("gaps") or [])
                             if gap.get("kind") and str(gap.get("kind")).strip().lower() not in NO_COMMON_PHYSIOLOGY_ACTIONS}))
    acknowledged = tuple(sorted({str(gap.get("kind")) for gap in (scenario.get("gaps") or [])
                                 if str(gap.get("kind") or "").strip().lower() in NO_COMMON_PHYSIOLOGY_ACTIONS}))
    case_id = str(scenario.get("case") or scenario.get("shadow_case_id") or "")
    facts = {
        "case_allowlisted": case_id in AUTHORITY_CASES,
        "family": AUTHORITY_FAMILY,
        "domain_coherent": domain_is_coherent()[0],
        "live_equals_replay": bool(scenario.get("live_equals_replay")),
        "no_shadow_failure": not (scenario.get("failures") or []),
        "no_boundary": not (scenario.get("boundaries") or []),
        "no_unexpected_divergence": not (scenario.get("unexpected") or []),
        "no_pilot": not any(str(environ.get(name, "") or "").strip() for name in PILOT_FLAGS),
        # P3-17: the gaps were computed and then skipped, so an order the common core never received did
        # not stand in the way of "eligible". A declared mirror gap now blocks.
        "no_mirror_gap": not declared,
        "unsupported_actions": list(unsupported),
        "settled_classes": sorted(set(settled)),
        "declared_gaps": list(declared),
        "acknowledged_no_common_physiology": list(acknowledged),
        "contradictory_coverage": list(contradictory),
        "approved_snapshot": bool(_APPROVED_SNAPSHOT_POINTS),
    }
    reasons = []
    if unsupported:
        # The faculty decision of 2026-11-07: a management-relevant action the common mapping cannot
        # represent makes the encounter ineligible until its semantics are modelled or shown irrelevant
        # to the pressure horizon. It is never silently ignored.
        reasons.append(f"{INELIGIBLE_UNSUPPORTED}: {list(unsupported)}")
        return AuthorityEligibility(INELIGIBLE_UNSUPPORTED, case_id, scenario.get("scenario"),
                                    tuple(reasons), unsupported, facts)
    for name, ok in facts.items():
        if name in ("unsupported_actions", "settled_classes", "declared_gaps", "acknowledged_no_common_physiology",
                    "contradictory_coverage", "family", "approved_snapshot"):
            continue
        if not ok:
            reasons.append(f"{name} is false")
    if reasons:
        return AuthorityEligibility(INELIGIBLE_OTHER, case_id, scenario.get("scenario"),
                                    tuple(reasons), unsupported, facts)
    covering = approved_snapshot(
        str(environ.get(SNAPSHOT_FLAG, "") or "").strip() or None,
        environment=str(environ.get(ENVIRONMENT_FLAG, "") or ""), family=AUTHORITY_FAMILY,
        case_id=case_id, domain=AUTHORITY_DOMAIN)
    if covering is None:
        # No approval was NAMED for this reading, so report the registry's own state: an approval that
        # exists but was not asked for does not make a scenario eligible for it.
        named = [name for name in sorted(_APPROVED_SNAPSHOT_POINTS)
                 if approved_snapshot(name, environment=str(environ.get(ENVIRONMENT_FLAG, "")
                                                            or "development"),
                                      family=AUTHORITY_FAMILY, case_id=case_id,
                                      domain=AUTHORITY_DOMAIN) is not None]
        covering = _APPROVED_SNAPSHOT_POINTS.get(named[0]) if named else None
    if covering is None:
        reasons.append("NO_FACULTY_APPROVED_AUTHORITY_SNAPSHOT_EXISTS: everything structural holds, and "
                       "the one remaining condition is a faculty decision")
        return AuthorityEligibility(ELIGIBLE_BUT_NO_SNAPSHOT, case_id, scenario.get("scenario"),
                                    tuple(reasons), unsupported, facts)
    facts = {**facts, "approving_snapshot": str(dict(covering).get("id") or ""),
             "approval_purpose": str(dict(covering).get("purpose") or "")}
    reasons.append(f"{dict(covering).get('purpose')}: everything structural holds and the faculty "
                   f"decision registered {dict(covering).get('id')!r} for a development experiment. This "
                   f"is not a clinical validation of any magnitude")
    return AuthorityEligibility(ELIGIBLE_FOR_DEVELOPMENT, case_id, scenario.get("scenario"),
                                tuple(reasons), unsupported, facts)


def eligibility_battery(evidence: Mapping | None = None, *,
                        environ: Mapping[str, str] | None = None) -> dict:
    """Every GI acceptance scenario read against the dormant eligibility logic (P3-15-7).

    No scenario is excluded to improve a percentage: the ones with an unsupported action are reported as
    ineligible, by name, which is the finding and not a blemish on it.
    """
    import runtime_shadow_evidence as ev
    data = evidence if evidence is not None else ev.gi_evidence()
    rows = [eligibility(scenario, environ=environ).to_dict()
            for case in data["cases"] for scenario in case["scenarios"]]
    counts: dict = {}
    for row in rows:
        counts[row["classification"]] = counts.get(row["classification"], 0) + 1
    return {
        "rows": rows, "counts": counts, "scenarios": len(rows),
        "eligible_but_for_the_snapshot": sorted(row["scenario"] for row in rows
                                                if row["classification"] == ELIGIBLE_BUT_NO_SNAPSHOT),
        "eligible_for_development": sorted(row["scenario"] for row in rows
                                           if row["classification"] == ELIGIBLE_FOR_DEVELOPMENT),
        "structurally_eligible": sorted(row["scenario"] for row in rows
                                        if row["classification"] in ELIGIBLE_CLASSES),
        "ineligible_unsupported": sorted({kind for row in rows for kind in row["unsupported"]}),
        "approved_snapshot_exists": bool(_APPROVED_SNAPSHOT_POINTS),
        "reading": "a structurally eligible scenario is eligible for the DEVELOPMENT experiment the "
                   "faculty decision of 2026-11-08 authorized, and for nothing else: not for production, "
                   "not for the first pilot, and not as a claim about any clinical magnitude",
    }


# -- P3-15-4, P3-15-5, P3-15-6: the failure policy -----------------------------------------------------

#: The faculty-selected failure policy for a first experiment: stop visibly, commit nothing, and never
#: switch engines inside an encounter.
FAILURE_POLICY = "HARD_FAIL_VISIBLE_TO_FACULTY"
#: When the mode of an encounter may be decided: once, before its first minute.
MODE_DECIDED_AT = "encounter_start"


def encounter_mode(state: Mapping, *, environ: Mapping[str, str] | None = None, **kwargs) -> str:
    """The mode for this encounter, decided ONCE at its start. Refuses to decide after the first minute.

    A mode chosen mid-encounter is the thing the faculty decision forbids in both directions: no silent
    promotion from legacy to common, and no invisible fallback from common to legacy. A state already past
    its arrival therefore reads LEGACY, whatever the environment says.
    """
    try:
        minute = int(dict(state).get("sim_time", 0) or 0)
    except Exception:
        return MODE_LEGACY
    if minute != 0:
        return MODE_LEGACY
    return mode(state, environ=environ, **kwargs)


def rollback_artifact(transaction: "AuthorityTransaction", *, reason: str,
                      history: Sequence = (), replay_digest: str | None = None) -> dict:
    """What a failed future experiment must preserve, so the encounter can be read and replayed later."""
    record = transaction.record()
    return {
        "failure_policy": FAILURE_POLICY,
        "mode_decided_at": MODE_DECIDED_AT,
        "reason": reason or transaction.reason,
        "minute": transaction.minute,
        "precommit_authoritative_state": (None if transaction.before is None
                                          else dict(transaction.before)),
        "common_candidate": record["candidate"],
        "legacy_counterfactual": record["legacy_counterfactual"],
        "validation_failures": record["validation_failures"],
        "action_history": [dict(item) if isinstance(item, Mapping) else item for item in history],
        "parameter_snapshot": record["snapshot"],
        "phase2_digest": rs.PHASE2_DIGEST,
        "phase3_layer": rs.MODULE_VERSION,
        "phase3_layer_digest": rs.layer_digest(),
        "replay_digest": replay_digest,
        "committed": record["committed"],
        "rescue": "replay the encounter from its immutable artifact with the legacy counterfactual as the "
                  "authority; never continue the same encounter with the other engine",
    }


# -- P3-19: the production call site, dormant -----------------------------------------------------------

SITE_VERSION = "P3-19"
#: What the artifact says about where it may be kept (faculty decision of 2026-11-07). The store itself is
#: ``runtime_authority_store``, and it is off unless a faculty environment names a directory.
STORE_CONTRACT = ("phase3_faculty_research_surface_only: never the Phase-2 trace schema, the resident "
                  "trace, the resident-visible output, the scoring data or the critical-event data")
#: The keys the site keeps in the caller's own store (Streamlit's session state in production). The
#: caller orchestrates; every decision lives here.
SITE_KEY = "phase3_authority_site"
SITE_REFUSED_KEY = "phase3_authority_refused_for"

#: Why a site did not open, or why a minute did not commit. Structural reasons, never a clinical reading.
NO_AUTHORITY_FLAG = "NO_AUTHORITY_FLAG"
GATE_REFUSED = "AUTHORITY_GATE_REFUSED"
COMMIT_REFUSED = "AUTHORITY_COMMIT_REFUSED"
NO_COMMON_CANDIDATE = "NO_COMMON_CANDIDATE_FOR_THIS_MINUTE"
MINUTE_NOT_COMPARED = "MINUTE_NOT_COMPARED_AGAINST_LEGACY"
UNSUPPORTED_AUTHORITY_ACTION = "UNSUPPORTED_AUTHORITY_ACTION"
OUT_OF_DOMAIN_WRITE = "OUT_OF_DOMAIN_WRITE_REFUSED"
VALIDATION_REFUSED = "VALIDATION_REFUSED"
SITE_HALTED = "AUTHORITY_HALTED_AFTER_A_HARD_FAILURE"
#: P3-248 (review M1): the saved session does not carry the authority site, so an encounter resumed after a commit has none. It is MARKED, durably, instead of left ACTIVE.
RESUMED_WITHOUT_SITE = "ENCOUNTER_RESUMED_WITHOUT_ITS_AUTHORITY_SITE"
RESUME_CHECKED_KEY = "phase3_authority_resume_checked_for"
#: P3-251: where the page's session store keeps the authority-SESSION record (lifecycle, last authoritative minute, halt, continuation). It is in ``curriculum_runtime.SESSION_FIELDS``.
SESSION_KEY = "phase3_authority_session"
#: P3-273: the provenance ANCHOR. A REAL commit writes one monotonic mark, ``authority_occurred``, into the patient state itself (a top-level key, outside ``observable`` and outside the authority
#: domain, which it does not widen): it travels with the encounter wherever the encounter goes, so an encounter that lost its session record AND its site is still known to have been authoritative.
PROVENANCE_ANCHOR_KEY = "phase3_authority_anchor"
PROVENANCE_ANCHOR_INVALID = "PROVENANCE_ANCHOR_INVALID"
PROVENANCE_LOST = "AUTHORITY_OCCURRED_BUT_ITS_PROVENANCE_IS_LOST"
#: P3-276 (review H1): a turn of a committed REAL session moved the clock and the site never saw it (a route the site was never asked to judge), so nothing authoritative covers it: the turn is not applied
#: and the session stops. It is the fail-closed answer to "unjudged", never a silent legacy minute.
TURN_NOT_JUDGED = "AUTHORITY_TURN_NOT_JUDGED"
#: P3-257: after the first REAL commit the durable record is what makes a reopened encounter recognisable, so a record that cannot be written is a hard failure, not a note.
ARTIFACT_PERSISTENCE_FAILED = "ARTIFACT_PERSISTENCE_FAILED"
#: The authority configuration of a running experiment changed, which it may not (faculty decision F).
CONFIGURATION_CHANGED = "AUTHORITY_CONFIGURATION_CHANGED_INSIDE_THE_ENCOUNTER"
MINUTE_ALREADY_COMMITTED = "MINUTE_ALREADY_COMMITTED"
#: P3-245: the collapse boundary of the experiment (FD-AUTH-06/17) and the experiment window (FD-AUTH-07). Experiment events, never terminal states.
COLLAPSE_BOUNDARY_REACHED = "COLLAPSE_BOUNDARY_REACHED"
COLLAPSE_BOUNDARY_NOT_VERIFIABLE = "COLLAPSE_BOUNDARY_NOT_VERIFIABLE"
WINDOW_CLOSED = "EXPERIMENT_WINDOW_CLOSED"
#: The key the caller keeps the experiment artifact under, dropped with the encounter like the site.
ARTIFACT_KEY = "phase3_authority_artifact"
#: The encounter whose experiment halted. The P3-28 review found that a site halted at minute 0 -- a plan,
#: a held order, a clarification: turns that do not move the clock -- failed ``is_for`` and was REBUILT as a
#: fresh ACTIVE site for the same encounter. This marker is what makes "no second authority attempt in the
#: same encounter" true instead of intended.
HALTED_KEY = "phase3_authority_halted_for"

#: P3-27: the experiment state of one encounter. There is no transition out of HALTED, by construction:
#: no code assigns ACTIVE anywhere except when a site is built, and a halted site is never rebuilt for the
#: same encounter. A halted experiment is for replay and analysis, never for continuation.
EXPERIMENT_NOT_STARTED = "NOT_STARTED"
EXPERIMENT_ACTIVE = "ACTIVE"
EXPERIMENT_HALTED = "HALTED"
#: What a halted experiment is, said in the artifact and on the faculty surface (faculty decision F).
INVALID_FOR_CONTINUATION = "HALTED/INVALID_FOR_CONTINUATION"
#: The surface's reading when the gate refused and no experiment exists at all.
EXPERIMENT_REFUSED = "REFUSED"


def _normalized(payload: Any) -> Any:
    """The payload in a form that serializes identically in any process (P3-19 review).

    Four things the review found and this closes: a mapping with keys of mixed types made ``sort_keys``
    raise, so every key becomes a string; a ``set`` serialized by ``repr`` and changed order between
    processes, so it becomes a sorted list; a non-finite float produced JSON no other reader accepts, so
    it becomes its own name; and anything else becomes its ``str``, as before.
    """
    if isinstance(payload, Mapping):
        return {str(key): _normalized(value) for key, value in payload.items()}
    if isinstance(payload, (set, frozenset)):
        return sorted(str(item) for item in payload)
    if isinstance(payload, (list, tuple)):
        return [_normalized(item) for item in payload]
    if isinstance(payload, bool) or payload is None or isinstance(payload, (int, str)):
        return payload
    if isinstance(payload, float):
        finite = payload == payload and payload not in (float("inf"), float("-inf"))
        return payload if finite else repr(payload)
    return str(payload)


def canonical(payload: Any) -> str:
    """The ONE serialization every digest in this module is taken over: sorted keys, no spaces."""
    return json.dumps(_normalized(payload), sort_keys=True, separators=(",", ":"), default=str)


def digest_of(payload: Any) -> str:
    """P3-19D: the site computes its own digests. A digest-shaped string from a caller is never trusted."""
    return hashlib.sha256(canonical(payload).encode("utf-8")).hexdigest()


def pressure_point(mapping: Mapping | None) -> dict:
    """The pressure domain of a mapping as plain floats: the shape a candidate digest is taken over."""
    source = dict(mapping or {})
    point = {}
    for name in AUTHORITY_DOMAIN:
        value = source.get(name)
        point[name] = (None if isinstance(value, bool) or not isinstance(value, (int, float))
                       else round(float(value), 9))
    return point


#: The keys the runtime uses for an order's class: ``type`` in the engine's action summaries, ``class`` in
#: the order ledger's settled snapshot. Both are read, because the call site receives whichever the caller
#: has, and guessing wrong would silently read every order as untyped -- which fails closed, but for the
#: wrong reason.
ACTION_CLASS_KEYS = ("type", "kind", "class")


def action_kinds(ran: Sequence | None) -> tuple:
    """The order classes of a settled turn, read from the engine's own summaries or from the ledger."""
    kinds = []
    for action in list(ran or []):
        kind = ""
        for key in ACTION_CLASS_KEYS:
            value = (action.get(key) if isinstance(action, Mapping) else getattr(action, key, None))
            kind = str(value or "").strip().lower()
            if kind:
                break
        kinds.append(kind or "untyped_action")
    return tuple(kinds)


def derived_map(sbp: Any, dbp: Any) -> int | None:
    """The mean pressure the DISPLAY computes from the two pressures beside it.

    The application derives it (``app.learner_vitals_snapshot``) and a test pins this function against
    that one over a range of values. It lives here because a commit has to write the same number the
    screen shows: the P3-19 review found that leaving the legacy ``map`` in the state made the state, the
    screen and the management trace disagree by a millimetre.
    """
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in (sbp, dbp)):
        return None
    return int(round((float(sbp) + 2.0 * float(dbp)) / 3.0))


def shape_of(legacy_observable: Mapping | None) -> dict:
    """Which domain fields the legacy engine writes as whole millimetres. Recorded in the artifact, so a
    replay reproduces the written values from the artifact alone instead of guessing the shape."""
    source = dict(legacy_observable or {})
    shape = {}
    for name in AUTHORITY_DOMAIN:
        value = source.get(name)
        shape[name] = ("int" if isinstance(value, int) and not isinstance(value, bool)
                       else "float" if isinstance(value, float) else "none")
    return shape


def apply_shape(candidate: Mapping, shape: Mapping | None) -> dict:
    """The common pressures in the recorded shape. A presentation shape, never a tolerance.

    The mean is DERIVED from the shaped pair and never shaped on its own, because that is what the
    commit writes and what the screen shows. The first development authority encounter (P3-41) found the
    two definitions disagreeing by one millimetre at minute 30 -- the core's mean was 59.538, shaping it
    alone gave 60, the commit wrote 59 -- and the forensic replay had its own second copy of the rule,
    so the artifact's account of what it wrote was wrong in exactly the minutes where the rounding of
    the pair crosses a boundary. One definition lives here, and both paths read it.
    """
    marks = dict(shape or {})
    out = {}
    for name, value in dict(candidate).items():
        numeric = isinstance(value, (int, float)) and not isinstance(value, bool)
        out[name] = int(round(float(value))) if numeric and marks.get(name) == "int" else value
    if "map" in out:
        mean = derived_map(out.get("sbp"), out.get("dbp"))
        if mean is not None:
            out["map"] = mean
    return out


def shaped_like_legacy(candidate: Mapping, legacy_observable: Mapping | None) -> dict:
    """The common pressures in the SHAPE the legacy engine writes them, so the display does not change.

    The legacy engine writes integer millimetres and the display prints them as they are, so committing
    ``117.428...`` would change what a resident reads without any physiology changing. This is a
    presentation shape and not a tolerance: the digests are taken over the raw candidate the core
    produced, and both the raw and the written values go into the provenance record.

    The mean is DERIVED from the shaped pair, never shaped on its own. The first development authority
    encounter (P3-41) found the difference: at minute 30 the core's mean was 59.538, shaping it alone
    gave 60, and the commit -- which derives the mean from the two integers it writes -- wrote 59. The
    state and the screen agreed; the artifact's own account of what it wrote did not. One definition of
    the mean, used by the commit and by the record, is what makes the record true.
    """
    return apply_shape(candidate, shape_of(legacy_observable))


def action_fates(ran: Sequence | None) -> tuple:
    """The identity and the fate the order pipeline already settled, as the authority minute saw them.

    The site never decides a fate: it records the one the ledger settled, which is what makes an authority
    minute auditable against the order book.
    """
    out = []
    for action, kind in zip(list(ran or []), action_kinds(ran)):
        item = dict(action) if isinstance(action, Mapping) else {}
        out.append({"order_id": canonical_order_id(item),
                    "type": kind,
                    "source_submission": str(item.get("_submission_id") or ""),
                    "action_written_at_min": item.get("_written_at_min"),
                    "fate": str(item.get("fate") or item.get("status") or "")})
    return tuple(out)


#: The reader's own key for an order's identity, stamped by ``order_ledger.tag`` and the ONE key
#: ``order_pipeline._order_by_action`` resolves an order by. P3-52 measured it on the two GI batteries:
#: 170 of 170 consumed actions carry it, so the direct link is total and the site never guesses.
#: ``order_id``/``id`` stay as fallbacks for a shape that is not a reader action.
CANONICAL_ID_KEYS = ("_order_id", "order_id", "id")


def canonical_order_id(action: Any) -> str:
    """The canonical identity of the order this action belongs to, as the repository stamps it."""
    item = dict(action) if isinstance(action, Mapping) else {}
    for key in CANONICAL_ID_KEYS:
        value = str(item.get(key) or "").strip()
        if value:
            return value
    return ""


#: The canonical fields of a SETTLED order, exactly as ``order_ledger.snapshot`` keeps them. The site
#: copies them: it never invents an identity and never decides a fate (P3-46-3, P3-46-4).
SETTLED_ORDER_FIELDS = ("order_id", "submission_id", "class", "fate", "reason", "executed_at_min")
#: Why a settled fate can contradict an authority minute that already happened.
PROVENANCE_CONTRADICTION = "PROVENANCE_CONTRADICTS_THE_AUTHORITY_MINUTE"


def fates_that_did_not_act() -> frozenset:
    """``order_ledger.NOT_ACTED``, read and never copied: the repository owns that vocabulary.

    Read lazily and defensively. A site that cannot reach the ledger reports no contradiction rather
    than inventing one, and the artifact says the provenance was not settled.
    """
    try:
        import order_ledger
        return frozenset(str(name) for name in order_ledger.NOT_ACTED)
    except Exception:
        return frozenset()


#: The canonical lineage of one physiologically consumed action, in the repository's own terms.
LINEAGE_FIELDS = ("order_id", "class", "fate", "source_submission", "activation_submission",
                  "order_written_at_min", "action_written_at_min", "activated_at_min", "origin", "link")
#: Where the source order was opened. P3-52 measured 0 of 170 consumed actions reaching back to an
#: earlier submission in the two GI batteries, so ``ACTIVE_PREVIOUS_ORDER`` is a shape the repository
#: allows (``open_turn`` reuses a held order by its id) that this evidence never exercises.
ORIGIN_THIS_TURN = "SOURCE_ORDER_OPENED_THIS_SUBMISSION"
ORIGIN_EARLIER = "ACTIVE_PREVIOUS_ORDER"
LINK_VALID = "VALID_LINKED_LINEAGE"
#: Named and falsifiable, each one a thing the record can be WRONG about -- not a note.
NO_CANONICAL_SOURCE_ORDER = "NO_CANONICAL_SOURCE_ORDER"
LINEAGE_ABSENT = "LINEAGE_SOURCE_ORDER_ABSENT_FROM_THE_SETTLED_LEDGER"
LINEAGE_CLASS_DISAGREES = "LINEAGE_CLASS_DISAGREES_WITH_THE_SOURCE_ORDER"
LINEAGE_WRITTEN_AFTER_ACTIVATION = "LINEAGE_SOURCE_ORDER_WRITTEN_AFTER_ITS_ACTIVATION"
LINEAGE_NOT_THE_ORDER_THIS_ACTION_OPENED = "LINEAGE_SOURCE_ORDER_IS_NOT_THE_ONE_THIS_ACTION_OPENED"
LINEAGE_FATE_DID_NOT_ACT = "LINEAGE_SOURCE_FATE_SAYS_THE_ORDER_DID_NOT_ACT"
LINEAGE_VIOLATIONS = (NO_CANONICAL_SOURCE_ORDER, LINEAGE_ABSENT, LINEAGE_CLASS_DISAGREES,
                      LINEAGE_WRITTEN_AFTER_ACTIVATION, LINEAGE_NOT_THE_ORDER_THIS_ACTION_OPENED,
                      LINEAGE_FATE_DID_NOT_ACT)


def action_lineage(fates: Sequence | None, settled: Sequence | None, submission_id: Any = None) -> tuple:
    """Link each consumed action to its authoritative source order, by the repository's own identity.

    No class matching and no submission filter: the link is the id ``order_ledger.tag`` stamped on the
    action and ``order_pipeline.settle`` resolves orders by. Every row says which order authorized the
    action, where that order was opened, when it was activated, and whether the link holds. A row whose
    ``link`` is one of ``LINEAGE_VIOLATIONS`` is a thing the record got wrong, not a gap to shrug at.
    """
    by_id = {}
    for order in list(settled or []):
        item = dict(order) if isinstance(order, Mapping) else {}
        key = str(item.get("order_id") or "").strip()
        if key:
            by_id.setdefault(key, item)
    turn = "" if submission_id is None else str(submission_id)
    did_not_act = fates_that_did_not_act()
    rows = []
    for entry in list(fates or []):
        item = dict(entry) if isinstance(entry, Mapping) else {}
        order_id = str(item.get("order_id") or "").strip()
        order = by_id.get(order_id) or {}
        source = str(order.get("submission_id") or "")
        activated = order.get("executed_at_min")
        written = order.get("written_at_min")
        row = {
            "order_id": order_id,
            "class": str(order.get("class") or ""),
            "fate": str(order.get("fate") or ""),
            "source_submission": source,
            "activation_submission": turn,
            "order_written_at_min": written,
            "action_written_at_min": item.get("action_written_at_min"),
            "activated_at_min": activated,
            "origin": ORIGIN_THIS_TURN if (source and source == turn) else (
                ORIGIN_EARLIER if order_id else ""),
            "link": LINK_VALID,
        }
        if not order_id:
            # P3-52 found the runtime always stamps an identity (170 of 170), so an action without one
            # is not a legitimate shape here: it is recorded as a violation, not excused as a gap.
            row["link"] = NO_CANONICAL_SOURCE_ORDER
        elif not order:
            row["link"] = LINEAGE_ABSENT
        elif str(item.get("type") or "") != str(order.get("class") or ""):
            # The collision P3-52 reproduced: a resumed encounter whose turn counter restarts over an
            # inherited ledger makes ``t0:0`` resolve to the ORIGINAL encounter's order. ``order_id`` is
            # unique within one encounter's ledger, not across encounters, so the link is checked and
            # never trusted blind.
            row["link"] = LINEAGE_CLASS_DISAGREES
        elif (_as_int(written) is not None and _as_int(activated) is not None
              and _as_int(written) > _as_int(activated)):
            row["link"] = LINEAGE_WRITTEN_AFTER_ACTIVATION
        elif (row["origin"] == ORIGIN_THIS_TURN and item.get("action_written_at_min") is not None
              and written is not None
              and _as_int(item.get("action_written_at_min")) != _as_int(written)):
            row["link"] = LINEAGE_NOT_THE_ORDER_THIS_ACTION_OPENED
        elif did_not_act and str(order.get("fate") or "") in did_not_act:
            row["link"] = LINEAGE_FATE_DID_NOT_ACT
        rows.append({name: row.get(name) for name in LINEAGE_FIELDS})
    return tuple(rows)


def lineage_violations(rows: Sequence | None) -> tuple:
    """The rows whose canonical link does not hold, each with the reason it does not."""
    out = []
    for row in list(rows or []):
        item = dict(row) if isinstance(row, Mapping) else {}
        if str(item.get("link") or "") != LINK_VALID:
            out.append({"order_id": item.get("order_id"), "class": item.get("class"),
                        "fate": item.get("fate"), "link": item.get("link")})
    return tuple(out)


def settled_provenance(orders: Sequence | None, submission_id: Any = None) -> tuple:
    """The canonical identity and fate of each settled order of this submission.

    ``order_id`` carries the submission as its prefix (``t3:0``), so a ledger snapshot that dropped the
    ``submission_id`` field is still attributable to its turn.
    """
    wanted = None if submission_id is None else str(submission_id)
    out = []
    for order in list(orders or []):
        item = dict(order) if isinstance(order, Mapping) else {}
        if wanted is not None:
            owned = (str(item.get("submission_id") or "") == wanted
                     or str(item.get("order_id") or "").startswith(f"{wanted}:"))
            if not owned:
                continue
        out.append({name: item.get(name) for name in SETTLED_ORDER_FIELDS if name in item})
    return tuple(out)


def unsupported_among(kinds: Sequence[str]) -> tuple:
    """The classes a pressure authority cannot mirror exactly. An unknown class is unsupported.

    P3-212: a class on the EXPLICIT ``NO_COMMON_PHYSIOLOGY_ACTIONS`` allowlist is not unsupported: it was executed and has nothing to mirror.
    It is not silently ignored either: every minute records it as ``no_common_physiology``, and a settled fate that says it did not act is
    still a contradiction (``settle_provenance``) and still a different disposition (``disposition_of``)."""
    allowed = set(SUPPORTED_ACTIONS) | set(STRUCTURAL_ACTIONS) | set(NO_COMMON_PHYSIOLOGY_ACTIONS)
    return tuple(sorted({str(kind).strip().lower() or "untyped_action" for kind in kinds
                         if str(kind).strip().lower() not in allowed}))


UNTYPED_GAP = "untyped_gap"


def unsupported_in_settlement(rows: Sequence | None) -> tuple:
    """The classes of a SETTLED ledger the common mapping cannot represent: the unsupported classes (``unsupported_among``, which normalises the class name)
    and an allowlisted class (the IV line) whose settled fate says it did NOT act (held, terminal, recorded-not-modelled, unrecognized). The one rule the site
    and the dry evaluator share, so that neither can accept what the other refuses (P3-219 review, F1 and F7)."""
    items = [dict(row) if isinstance(row, Mapping) else {} for row in list(rows or [])]
    found = set(unsupported_among(tuple(str(item.get("class") or "") for item in items)))
    for item in items:
        name = str(item.get("class") or "").strip().lower()
        if name in NO_COMMON_PHYSIOLOGY_ACTIONS and disposition_of(item.get("class"), item.get("fate")) in (HELD_NOT_EXECUTED, TERMINAL_NOT_EXECUTABLE, UNSUPPORTED_ACTION):
            found.add(name)
    return tuple(sorted(found))


def settlement_contradictions(identities: Sequence | None, orders: Sequence | None, submission_id: Any, *, quiet: bool = False) -> list:
    """The contradictions the SETTLED ledger of a turn reveals against the actions the authority was told ran (P3-271): a consumed action whose canonical lineage does not hold, and a settled
    class the common mapping cannot represent. The same judgement ``AuthoritySite.settle_provenance`` makes after the commit, made here BEFORE it, so a real session never has to take a commit back.
    ``quiet`` is a turn that did not move the clock: it has no lineage to hold, only classes."""
    found = []
    settled = settled_provenance(orders, submission_id)
    if not quiet:
        lineage = action_lineage([dict(row) for row in (identities or [])], settled_provenance(orders, None), submission_id)
        for row in lineage_violations(lineage):
            found.append({"order_id": dict(row).get("order_id"), "class": dict(row).get("class"), "fate": dict(row).get("fate"), "link": dict(row).get("link"),
                          "why": "the canonical lineage of a consumed action does not hold"})
    unsupported = unsupported_in_settlement(settled)
    if unsupported:
        found.append({"class": list(unsupported),
                      "why": (f"{UNSUPPORTED_AUTHORITY_ACTION}: the settled ledger of a turn that did not move the clock carries a management class the common mapping cannot represent"
                              if quiet else
                              f"{UNSUPPORTED_AUTHORITY_ACTION}: the settled ledger of this turn carries a management class the common mapping cannot represent, and faculty decision "
                              f"C makes the encounter ineligible for common authority")})
    return found


def gap_kinds_of(session: Any) -> tuple:
    """The kinds of the shadow's declared gaps. A gap that names NO kind is a coverage the shadow lost (the state before a turn could not be copied, so nothing
    was mirrored): it is ``untyped_gap``, which is unsupported -- never silently dropped (P3-219 review, F2)."""
    return tuple(str(gap.get("kind")) if gap.get("kind") else UNTYPED_GAP for gap in list(getattr(session, "gaps", []) or []))


@dataclass
class AuthoritySite:
    """One encounter's future authority orchestration: the mode decided once, then minute by minute.

    It exists only when the gate granted, which no repository configuration can do today. Its contract:

    * it computes no physiology -- the candidate comes from the shadow runner, the one place that advances
      the common core;
    * it computes its own digests over a canonical serialization, and never trusts one it was handed;
    * it writes nothing anywhere: ``minute`` RETURNS a prepared mapping and the caller decides;
    * a hard failure HALTS the encounter's authority for good, visibly, and never falls back minute by
      minute to the legacy engine, because authority that alternates is not authority.
    """

    case_id: str
    family: str
    snapshot: Mapping[str, Any]
    snapshot_id: str
    encounter_id: str
    environment: str
    environ: Mapping[str, str] | None = None
    domain: tuple = AUTHORITY_DOMAIN
    experiment_id: str = ""
    #: The attempt this encounter is, when the state carries one: part of the artifact's identity.
    attempt: Any = None
    #: P3-240: the explicit development grant this experiment runs under. ``None`` only for a site opened with a TEST-ONLY approved point (the gate asks for the
    #: grant, and a production process can hold only the real registered point), in which case the site behaves exactly as it did before the grant existed.
    grant: Any = None
    records: list = field(default_factory=list, init=False)
    halted: bool = field(default=False, init=False)
    halt_reason: str = field(default="", init=False)
    replay_input: Mapping[str, Any] | None = field(default=None, init=False)
    #: P3-23A: the eligibility reading of this encounter, when the caller computed one. It is data the
    #: artifact must carry to be auditable, and the site never computes it for itself.
    eligibility: Mapping[str, Any] | None = field(default=None, init=False)
    #: P3-27: ACTIVE while the experiment runs, HALTED for good after any hard failure.
    experiment_state: str = field(default=EXPERIMENT_ACTIVE, init=False)
    #: What the store said the last time this artifact was written.
    stored: Mapping[str, Any] | None = field(default=None, init=False)
    #: P3-212/215: turns that did not advance the clock and carried only structural or acknowledged-no-physiology actions. Recorded, never committed.
    no_advance_turns: list = field(default_factory=list, init=False)
    #: How many of the shadow session's failures an earlier turn already judged. A failure the session recorded since is NEW, whatever minute it carries:
    #: the turn that has not yet been judged owns it (P3-219 review, F3).
    failures_judged: int = field(default=0, init=False)
    #: P3-243: the V1 consciousness overlay that runs BESIDE the pressure authority (comparison and trace review only), built lazily from the shadow session.
    overlay: Any = field(default=None, init=False)
    overlay_refusal: str = field(default="", init=False)
    #: The overlay's reading of the turn being judged: consumed by the boundary guard and recorded in the minute.
    current_overlay: Mapping[str, Any] | None = field(default=None, init=False)
    #: The legacy observable of the turn being judged, WITHOUT the pressure domain (what the legacy engine keeps owning): recorded in the minute (P3-246).
    current_legacy: Mapping[str, Any] | None = field(default=None, init=False)

    # -- the encounter's identity ----------------------------------------------------------------------
    def is_for(self, state: Mapping) -> bool:
        """A site belongs to ONE encounter, by the same rule the shadow session uses.

        The rule is the case plus the clock, not ``encounter_id``: that id is the digest of the arrival
        this site opened on, so it travels in the artifact and tells two attempts apart afterwards, but it
        cannot be recomputed from a state that has already advanced.
        """
        try:
            from clinical_core import legacy_adapter
            if str(legacy_adapter.engine_case_id(dict(state))) != self.case_id:
                return False
            minute = _as_int(dict(state).get("sim_time"))
            seen = self.minutes_seen
            if minute < seen:
                return False
            if minute == 0:
                # A second attempt at the same case arrives at minute 0 with a different patient, and the
                # P3-19 review found a fresh site was reused for it because it had no records yet. The
                # arrival's own digest settles it: same arrival, same encounter.
                return (not self.records
                        and rs._encounter_id(dict(state)) == self.encounter_id)
            return True
        except Exception:
            return False

    @property
    def minutes_committed(self) -> tuple:
        return tuple(record["minute"] for record in self.records if record["committed"])

    @property
    def minutes_seen(self) -> int:
        """The last minute the encounter REACHED under this site: its last committed minute. A refused minute is a counterfactual (P3-271): the turn that would have reached it was never applied, so the real
        clock legitimately stays behind it, and counting it would make the halted site of that very encounter 'not its site' (a rewound one) on the next run."""
        return max([_as_int(record.get("minute")) for record in self.records if record.get("committed")] or [0])

    # -- one minute ------------------------------------------------------------------------------------
    def minute(self, before: Mapping | None, after: Mapping, session: Any,
               ran: Sequence | None, submission_id: str | None = None, route: str = ORDER_TURN, settled: Sequence | None = None) -> Mapping | None:
        """One future authority minute: capture, compute, validate, commit atomically, or abort.

        Returns a NEW prepared mapping to install, or None. Never raises into the caller: an unexpected
        error halts the site and is recorded, because a dormant experiment may not break an encounter.

        ``settled`` (P3-271): the order ledger of the turn AFTER the pipeline settled each order's fate, when the caller has it BEFORE the commit. A real session judges the settled lineage and the
        settled classes here, before it commits, so that a contradiction the settlement reveals is a refusal of the turn and never a commit that has to be taken back (a committed minute is never
        rewritten: faculty decision F). The post-commit ``settle_provenance`` stays, and attaches the lineage to the minute as it always did.
        """
        minute = _as_int(dict(after).get("sim_time"))
        if self.halted:
            # P3-248 (review L2): a turn AFTER the halt is a small record, not a copy of the last overlay turn (which was stale and made the artifact grow by the whole turn).
            self.current_overlay = None
            self.current_legacy = None
            self.records.append(self._refusal(minute, SITE_HALTED, ran))
            self._persist()
            return None
        self._settled_ledger = None if settled is None else list(settled)
        try:
            prepared = self._minute(before, dict(after), session, ran, submission_id, route)
        except Exception as error:
            # Through ``_hard_fail``, so an internal error preserves what every other failure preserves:
            # the legacy counterfactual of that minute and a rollback artifact (P3-28 review).
            self.halt_reason = f"{type(error).__name__}: {error}"
            self._hard_fail(minute, f"SITE_ERROR {self.halt_reason}", ran,
                            legacy=dict(dict(after).get("observable") or {}))
            self._persist()
            return None
        # P3-26-4: every outcome of a minute is persisted -- a commit, a refusal, a failure and a halt --
        # so no failure path can be the one that forgot to leave a record. In production the store is not
        # configured, so this writes nothing and says why.
        self._retracted_minute = None
        self._persist()
        if getattr(self, "_retracted_minute", None) is not None:
            # P3-271: the commit of this minute could not be made durable, so it was withdrawn BEFORE anything saw it (see ``_persist``): there is nothing to install.
            return None
        return prepared

    @staticmethod
    def _no_advance(before: Mapping, after: Mapping) -> bool:
        """The clock did not move AND the authority domain is exactly what it was (the turn changed no pressure): only then is it a no-advance turn.

        The display MAP is a function of ``sbp`` and ``dbp`` that the legacy engine derives the first time it refreshes the observable, so a MAP that
        APPEARS (``None`` on one side) is that derivation, not a move: the very first order of an encounter -- an IV line -- would otherwise be read as a
        pressure that moved and refused. A MAP present on both sides that differs, or any change of ``sbp`` or ``dbp``, is a move."""
        try:
            one, two = pressure_point(dict(before).get("observable")), pressure_point(dict(after).get("observable"))
            return (_as_int(dict(before).get("sim_time")) == _as_int(dict(after).get("sim_time"))
                    and one["sbp"] == two["sbp"] and one["dbp"] == two["dbp"]
                    and (one["map"] == two["map"] or one["map"] is None or two["map"] is None))
        except Exception:
            return False

    def _persist(self) -> dict:
        """Hand the artifact to the faculty store. Never raises, and never touches anything else -- except that (P3-257) a REAL site that has already committed treats a record that
        cannot be written as a hard failure (``ARTIFACT_PERSISTENCE_FAILED``, INVALID_FOR_CONTINUATION): a reopened encounter is recognised by that durable record, and an
        authority session nobody can recognise afterwards would be a silent way back to the legacy engine. Then the authority-session record is published (P3-251)."""
        try:
            import runtime_authority_store as store
            self.stored = store.persist(self.artifact(), environ=self.environ)
        except Exception as error:
            self.stored = {"stored": False, "why": f"STORE_ERROR {type(error).__name__}: {error}"}
        if dict(self.stored or {}).get("stored"):
            self._unpersisted_commit = False
            self._unpersisted_quiet = False
        if (self.grant is not None and self.minutes_committed and not self.halted and not dict(self.stored or {}).get("stored")
                and not getattr(self, "_failing_to_persist", False)):
            self._failing_to_persist = True
            try:
                # P3-271: a commit made in THIS call that the store could not write was never durable and never applied (the page installs a commit only when ``minute`` returns it): it is withdrawn
                # and re-recorded as the failed minute, so the record never claims a minute the encounter did not reach. A commit that WAS durable is never touched (faculty decision F).
                withdrawn = self._withdraw_unpersisted_commit()
                if withdrawn is not None:
                    self._hard_fail(_as_int(withdrawn.get("minute")), f"{ARTIFACT_PERSISTENCE_FAILED}: {dict(self.stored or {}).get('why')}; the commit of minute "
                                    f"{_as_int(withdrawn.get('minute'))} was not durable and was not applied", (), provenance=withdrawn)
                else:
                    # P3-276 (review M2): a zero-minute turn that was only in memory when the store failed is withdrawn from the list of quiet turns, so the artifact never lists a turn
                    # the encounter never had (the page discards it); the refusal is recorded as the failed minute of that turn.
                    quiet_minute = self._withdraw_unpersisted_quiet()
                    self._hard_fail(self.minutes_seen if quiet_minute is None else quiet_minute,
                                    f"{ARTIFACT_PERSISTENCE_FAILED}: {dict(self.stored or {}).get('why')}" + ("" if quiet_minute is None else "; the zero-minute turn was not durable and was not applied"), ())
                try:
                    import runtime_authority_store as store
                    self.stored = store.persist(self.artifact(), environ=self.environ)       # the halt itself is recorded if the store lets it
                except Exception as error:
                    self.stored = {"stored": False, "why": f"STORE_ERROR {type(error).__name__}: {error}"}
            except Exception:
                self.halted, self.experiment_state = True, EXPERIMENT_HALTED
                self.halt_reason = self.halt_reason or ARTIFACT_PERSISTENCE_FAILED
            finally:
                self._failing_to_persist = False
        self._publish_session()
        return dict(self.stored or {})

    def _withdraw_unpersisted_commit(self) -> dict | None:
        """The commit made in the call that is being persisted, taken back because the store could not write it, as the record of a failed minute (or None when there is no such commit).

        It existed only in memory for the length of ``minute``: nothing durable, nothing applied and nothing shown ever carried it, so withdrawing it rewrites no history. The artifact then
        says what happened: the minute was refused because it could not be made durable."""
        if not getattr(self, "_unpersisted_commit", False) or not self.records or not dict(self.records[-1]).get("committed"):
            return None
        record = dict(self.records.pop())
        self._unpersisted_commit = False
        self._retracted_minute = _as_int(record.get("minute"))
        for name in ("common_pressures", "moved_fields"):
            record.pop(name, None)
        record["committed"] = []
        return record

    def _withdraw_unpersisted_quiet(self) -> int | None:
        """The zero-minute turn recorded in the call that is being persisted, taken back because the store could not write it (its minute, or None when there is no such turn)."""
        if not getattr(self, "_unpersisted_quiet", False) or not self.no_advance_turns:
            return None
        quiet = dict(self.no_advance_turns.pop())
        self._unpersisted_quiet = False
        return _as_int(quiet.get("minute"))

    def halt_unjudged_turn(self, minute: int, detail: str) -> None:
        """P3-276 (review H1): the turn of a committed REAL session moved the encounter and the site never judged it. Stops the session (INVALID_FOR_CONTINUATION through the ordinary halt) and
        records why. Never raises: a verdict about a turn may not break the page."""
        try:
            if self.halted:
                return
            self._hard_fail(_as_int(minute), f"{TURN_NOT_JUDGED}: {detail}", ())
            self._persist()
        except Exception:
            self.halted, self.experiment_state = True, EXPERIMENT_HALTED
            self.halt_reason = self.halt_reason or TURN_NOT_JUDGED

    # -- P3-251: the authority SESSION record ------------------------------------------------------------------------------------------------------------------------
    def session_record(self, *, encounter_ended: bool = False) -> dict:
        """The authority-session record of this site (lifecycle, last authoritative minute and pressure, halt, continuation), derived from its artifact and cached until the site changes.
        Never raises into a caller: a site that cannot describe itself describes itself as INVALID (fail closed)."""
        try:
            import runtime_authority_session as session
            key = (len(self.records), bool(self.halted), len(self.no_advance_turns), str(self.halt_reason), self.experiment_state, bool(self.grant is not None))
            cached = getattr(self, "_session_cache", None)
            if cached is None or cached[0] != key:
                body = self.artifact()
                record = session.session_record_of(body)
                # P3-262 (review HIGH-1): the record is derived from the artifact, and an artifact that could not be built is a degraded STUB ("halted, no minutes") that would read as a
                # halt BEFORE any commit -- a continuable PRECOMMIT_ABORT after authority began, the silent legacy fallback FD-STOP-03 forbids. The site's own facts win: a REAL site that
                # has committed and whose artifact cannot describe it is HALTED (sticky, so a later healthy artifact says the same) and its record fails closed.
                if self.grant is not None and self.minutes_committed and (str(body.get("halt_reason") or "").startswith("ARTIFACT_ERROR") or bool(record.get("authority_began")) is False):
                    reason = str(body.get("halt_reason") or "") if str(body.get("halt_reason") or "").startswith("ARTIFACT_ERROR") else "ARTIFACT_ERROR the artifact does not describe the commits the site made"
                    if not self.halted:
                        self.halted, self.experiment_state, self.halt_reason = True, EXPERIMENT_HALTED, reason
                    record = self._fail_closed_session_record(reason)
                cached = (key, record)
                self._session_cache = cached
            record = cached[1]
            if encounter_ended and record.get("lifecycle") in (session.PREAUTHORITY, session.ACTIVE_AUTHORITY):
                body = {name: value for name, value in record.items() if name != "record_digest"}
                body["lifecycle"] = session.COMPLETED_AUTHORITY
                return {**body, "record_digest": digest_of(body)}
            return record
        except Exception as error:
            import runtime_authority_session as session
            body = {"record_type": session.RECORD_TYPE, "version": session.VERSION, "lifecycle": session.INVALID_FOR_CONTINUATION, "continuation_allowed": False,
                    "stop_policy": "EFFECTIVE_STOP", "legacy_fallback_allowed": False, "authority_began": True, "last_authoritative_minute": max([_as_int(x) for x in self.minutes_committed] or [0]),
                    "last_authoritative_pressure": None, "halted": True, "halt_reason": f"SESSION_RECORD_ERROR {type(error).__name__}: {error}", "stop_class": session.STOP_INTERNAL,
                    "case_id": self.case_id, "family": self.family, "snapshot_id": self.snapshot_id, "encounter_id": self.encounter_id, "experiment_id": self.experiment_id}
            return {**body, "record_digest": digest_of(body)}

    def _fail_closed_session_record(self, reason: str) -> dict:
        """The session record of a REAL site that has committed and cannot describe itself through its artifact (P3-262, review HIGH-1): INVALID_FOR_CONTINUATION, from the site's OWN
        facts (its committed minutes and the pressure of its last committed record), never from a degraded artifact."""
        import runtime_authority_session as session
        committed = [dict(record) for record in self.records if dict(record).get("committed")]
        last = committed[-1] if committed else {}
        grant = dict(self.grant or {})
        base = {"record_type": session.RECORD_TYPE, "version": session.VERSION, "lifecycle": session.INVALID_FOR_CONTINUATION, "continuation_allowed": False,
                "stop_policy": "EFFECTIVE_STOP", "legacy_fallback_allowed": False, "authority_began": True,
                "last_authoritative_minute": max([_as_int(x) for x in self.minutes_committed] or [0]),
                "last_authoritative_pressure": (dict(last.get("common_pressures") or {}) or None),
                "grant_id": grant.get("grant_id"), "grant_fingerprint": grant.get("fingerprint"), "authority_mode": None,
                "case_id": self.case_id, "family": self.family, "snapshot_id": self.snapshot_id,
                "lineage": {"version_id": grant.get("core_version"), "digest": rs.PHASE2_DIGEST},
                "encounter_id": self.encounter_id, "experiment_id": self.experiment_id, "attempt": self.attempt,
                "halted": True, "halt_reason": reason, "stop_class": session.stop_class_of(reason),
                "failed_minute": None, "failed_operation": None, "last_artifact": {"artifact_digest": "", "minutes_recorded": len(self.records)},
                "authority_label": REAL_PRESSURE_LABEL}
        return {**base, "record_digest": digest_of(base)}

    def _publish_session(self) -> None:
        """Put the session record where the page keeps its session (and therefore where a saved encounter carries it). Never raises."""
        target = getattr(self, "_session_store", None)
        if target is None:
            return
        try:
            target[SESSION_KEY] = self.session_record()
        except Exception:
            pass

    def settle_provenance(self, submission_id: Any, orders: Sequence | None) -> dict:
        """Attach the canonical order identity and fate to the minute already recorded. Never raises.

        The commit does NOT move. The pressure is still written exactly where it was, before the order
        pipeline settles each order's fate, so no action activates a minute earlier or later than before
        and the trajectory, the counterfactual and what a resident would see are unchanged (P3-46-2).
        What moves is the PROVENANCE: it is finalized here, once the authoritative fates exist, which is
        what P3-44 found missing. The site reads those fates and compares them; it decides none, and it
        infers none (P3-46-1, P3-46-4).

        A settled fate that says the order did not act on the patient, under a minute that committed a
        pressure from it, is a contradiction between the record and the run. It is not corrected and the
        committed minute is NOT rewritten -- faculty decision F forbids retrospective mutation. The
        experiment halts, visibly, with the contradiction recorded as its own failure minute.
        """
        report = {"submission_id": str(submission_id or ""), "settled": 0, "contradictions": [],
                  "halted": False, "why": ""}
        try:
            record = next((item for item in reversed(self.records)
                           if str(item.get("submission_id") or "") == str(submission_id or "")), None)
            if record is None:
                quiet = next((item for item in reversed(self.no_advance_turns) if str(item.get("submission_id") or "") == str(submission_id or "")), None)
                if quiet is None:
                    report["why"] = "no authority minute carries this submission"
                    return report
                # P3-219 review, F1: a turn that did not move the clock is RECORDED, and its settled ledger is judged exactly as a committed minute's is. An order
                # the engine does not MODEL produces no action for the turn, so the ledger is the only place its class appears (the P3-48 gap): "Place an IV
                # line. Also give <something the mapping cannot represent>" must not slip through because its first order was acknowledged.
                settled = settled_provenance(orders, submission_id)
                unsupported = unsupported_in_settlement(settled)
                quiet["settled_action_classes"] = sorted({str(item.get("class") or "") for item in settled} - {""})
                quiet["no_common_physiology"] = [dict(row) for row in executed_no_common_physiology(settled)]
                quiet["provenance_settled"] = True
                report["settled"] = len(settled)
                if unsupported:
                    report["unsupported"] = list(unsupported)
                    report["contradictions"].append({"class": list(unsupported), "why": f"{UNSUPPORTED_AUTHORITY_ACTION}: the settled ledger of a turn that did not move "
                                                     f"the clock carries a management class the common mapping cannot represent"})
                    quiet["provenance_contradictions"] = [dict(item) for item in report["contradictions"]]
                    if not self.halted:
                        self._hard_fail(_as_int(quiet.get("minute")), f"{PROVENANCE_CONTRADICTION}: {report['contradictions']}", list(settled))
                        report["halted"] = True
                self._persist()
                return report
            # P3-53: the link is the repository's own identity, resolved against EVERY settled order of
            # the turn -- no class matching and no submission filter, because ``open_turn`` reuses a held
            # order by its id and that order carries the submission that opened it (P3-52-2).
            identities = [dict(row) for row in (record.get("action_fates") or [])]
            everything = settled_provenance(orders, None)
            settled = settled_provenance(orders, submission_id)
            lineage = action_lineage(identities, everything, submission_id)
            record["action_lineage"] = [dict(row) for row in lineage]
            record["action_fates"] = [dict(row) for row in lineage]
            record["no_common_physiology"] = [dict(row) for row in executed_no_common_physiology(lineage)]
            record["action_dispositions"] = [{"order_id": dict(row).get("order_id"), "class": dict(row).get("class"), "fate": dict(row).get("fate"),
                                              "disposition": disposition_of(dict(row).get("class"), dict(row).get("fate"))} for row in lineage]
            record["provenance_settled"] = True
            report["settled"] = len(settled)
            report["lineage"] = [dict(row) for row in lineage]
            if not settled:
                report["why"] = "the submission settled no order"
            for row in lineage_violations(lineage):
                # A named, falsifiable violation -- not a note. P3-52 proved the direct link holds for
                # 170 of 170 consumed actions, so a broken link is a thing the record got wrong.
                report["contradictions"].append(
                    {"order_id": dict(row).get("order_id"), "class": dict(row).get("class"),
                     "fate": dict(row).get("fate"), "link": dict(row).get("link"),
                     "why": "the canonical lineage of a consumed action does not hold"})
            # P3-48 found the gap this closes. An order the engine does not MODEL produces no action for
            # the turn, so ``run_actions`` never carries it and the live site never saw it: the
            # repository's own eligibility reading called those scenarios INELIGIBLE_UNSUPPORTED while
            # the live path committed. The settled ledger is the only place the class appears, and it
            # appears here. The site still decides nothing: it reads the settled classes and applies the
            # same ``unsupported_among`` the eligibility reading applies.
            settled_classes = tuple(str(item.get("class") or "") for item in settled)
            unsupported = unsupported_in_settlement(settled)
            record["settled_action_classes"] = sorted(set(settled_classes) - {""})
            if unsupported:
                report["unsupported"] = list(unsupported)
                report["contradictions"].append(
                    {"class": list(unsupported),
                     "why": f"{UNSUPPORTED_AUTHORITY_ACTION}: the settled ledger of this turn carries a "
                            f"management class the common mapping cannot represent, and faculty decision "
                            f"C makes the encounter ineligible for common authority"})
            record["provenance_contradictions"] = [dict(item) for item in report["contradictions"]]
            if report["contradictions"] and not self.halted:
                reason = (f"{PROVENANCE_CONTRADICTION}: {report['contradictions']}")
                # A FRESH failure record: a committed minute stays exactly as it happened.
                self._hard_fail(_as_int(record.get("minute")), reason, list(settled))
                report["halted"] = True
            self._persist()
        except Exception as error:  # a provenance repair may never break an encounter
            report["why"] = f"{type(error).__name__}: {error}"
        return report

    def _minute(self, before, after: Mapping, session, ran, submission_id, route: str = ORDER_TURN) -> Mapping | None:
        minute = _as_int(after.get("sim_time"))
        settled_rows = getattr(self, "_settled_ledger", None)           # P3-271: the ledger after the pipeline settled the orders, when the caller had it before the commit
        if route not in KNOWN_ROUTES:
            return self._hard_fail(minute, f"{UNKNOWN_ROUTE}: {route!r}", ran)
        if route == CLINICAL_TIME:
            # Clinical time outside an order turn declares no actions: it is the EMPTY turn, not an undeclared one. An action on this route is a
            # contradiction (an order has its own route), and fails closed.
            if ran is not None and list(ran):
                return self._hard_fail(minute, f"{UNSUPPORTED_AUTHORITY_ACTION}: the clinical-time route carries no actions", ran)
            ran = ()
        if ran is None:
            # The P3-19 review: the site always passed a tuple on, so "the caller declared nothing" had
            # become "nothing ran". An undeclared turn fails closed here, as it does in the gate.
            return self._hard_fail(minute, f"{UNSUPPORTED_AUTHORITY_ACTION}: the caller did not declare "
                                           f"which actions ran this turn", ran)
        # P3-243: under a development grant the V1 consciousness overlay is fed EVERY turn that reaches the judgement (a no-advance turn too), before anything is judged,
        # so the collapse boundary of the interval is known BEFORE a commit and every failure record can name the common state at the rejection. It reads; it never
        # writes, and the only thing it decides is the boundary.
        self.current_overlay = self._overlay_turn(after, session) if self.grant is not None else None
        try:
            self.current_legacy = (json.loads(canonical({key: value for key, value in dict(after.get("observable") or {}).items() if key not in AUTHORITY_DOMAIN}))
                                   if self.grant is not None else None)
        except Exception:
            self.current_legacy = None
        # The turn's own classes come FIRST: an unsupported management action is the declared policy and
        # it is about the turn, so a faculty reader must see it named even when the minute would also
        # have failed for another reason (P3-26-3).
        kinds = action_kinds(ran)
        legacy_observable = dict(after.get("observable") or {})
        # The declared gaps of the shadow go through the SAME filter as the turn's own classes: a gap on a
        # structural class is not a management-relevant unsupported action, and the three GI treatments
        # with no common writer are, whichever side names them.
        gap_kinds = gap_kinds_of(session)
        unsupported = tuple(sorted(set(unsupported_among(kinds)) | set(unsupported_among(gap_kinds))))
        # P3-219 review, F3: the failures this turn has not been judged for. Taken ONCE, here, so every path below -- the no-advance turn included -- sees them.
        everything = list(getattr(session, "failures", []) or [])
        new_failures = everything[self.failures_judged:]
        self.failures_judged = len(everything)
        if unsupported:
            return self._hard_fail(minute, f"{UNSUPPORTED_AUTHORITY_ACTION}: {list(unsupported)}",
                                   ran, legacy=legacy_observable, unsupported=unsupported)
        quiet_turn = before is not None and kinds and set(kinds) <= set(NO_ADVANCE_OK)
        # P3-241 (found by the first REAL page run): after a real commit at minute m, a turn that does not move the clock still lets the engine refresh its own observable, which
        # puts the LEGACY pressure of minute m back over the committed one. That is not a move of the patient, and it must not silently hand the pressure back to the legacy
        # engine: the minute's own recorded legacy counterfactual says nothing moved, so the pressure the minute already committed is re-asserted, unchanged (never a second
        # commit, never a new value).
        reasserted = self._reassertion(after, minute) if quiet_turn and _as_int(dict(before).get("sim_time")) == minute else None
        if quiet_turn and (reasserted is not None or self._no_advance(before, after)):
            if new_failures:
                return self._hard_fail(minute, f"{VALIDATION_REFUSED}: the shadow recorded a failure during a turn that did not move the clock: "
                                               f"{[(_as_int(item.minute), str(item.where)) for item in new_failures][:3]}", ran, legacy=legacy_observable)
            if settled_rows is not None:
                # P3-271: a zero-minute turn is judged on its SETTLED classes BEFORE it is recorded (an order the engine does not model produces no action for the turn, so only the settled
                # ledger names it), so a turn that the authority refuses is never applied to the real encounter.
                contradictions = settlement_contradictions(action_fates(ran), settled_rows, submission_id, quiet=True)
                if contradictions:
                    return self._hard_fail(minute, f"{PROVENANCE_CONTRADICTION}: {contradictions}", list(settled_provenance(settled_rows, submission_id)), legacy=legacy_observable)
            # P3-212/215: the clock did not move and nothing physiological was asked: there is no new minute to commit and no certified minute is
            # re-committed. The turn is RECORDED (the artifact lists it), the pressure domain is verified unchanged, and the experiment goes on.
            quiet = {"minute": minute, "submission_id": submission_id, "route": route, "action_kinds": list(kinds),
                     "action_fates": [dict(row) for row in action_fates(ran)],
                     "no_common_physiology": [dict(row) for row in executed_no_common_physiology(action_fates(ran))],
                     "pressure_digest": digest_of(pressure_point(legacy_observable)), "outcome": NO_ADVANCE_TURN}
            if reasserted is not None:
                quiet["pressure_reasserted"] = True
            if self.grant is not None:
                quiet["consciousness_overlay"] = dict(self._real_minute_fields().get("consciousness_overlay") or {}) or None
            self.no_advance_turns.append(quiet)
            self._unpersisted_quiet = True            # P3-276 (review M2): durable only once ``_persist`` has written it (a quiet turn the store could not write is withdrawn, like a commit)
            return reasserted
        if minute in self.minutes_committed:
            # One minute is one transaction: a turn that did not advance the clock -- a plan, a held
            # order, a clarification -- may not commit the same minute a second time. It is checked AFTER
            # the classes, so a turn carrying an unsupported treatment names it (P3-28 review).
            return self._hard_fail(minute, f"{MINUTE_ALREADY_COMMITTED}: {minute}", ran,
                                   legacy=legacy_observable)
        shadow_minute = self._shadow_minute(session, minute)
        if shadow_minute is None:
            return self._hard_fail(minute, NO_COMMON_CANDIDATE, ran, legacy=legacy_observable)
        if not shadow_minute.compared_against_legacy:
            return self._hard_fail(minute, MINUTE_NOT_COMPARED, ran, legacy=legacy_observable)
        candidate = pressure_point(shadow_minute.derived)
        if any(value is None for value in candidate.values()):
            return self._hard_fail(minute, NO_COMMON_CANDIDATE, ran, legacy=legacy_observable)
        if self.grant is not None:
            # P3-245: PRECOMMIT, every minute of the interval: a minute past the window, or one the overlay cannot show, or one at an ESTABLISHED collapse, is never committed.
            stopped = self._boundary_guard(minute)
            if stopped:
                return self._hard_fail(minute, stopped, ran, legacy=legacy_observable)
        # P3-19D: every digest below is computed HERE, from the immutable artifact and the candidate.
        self.replay_input = self._artifact_input(session)
        input_digest = digest_of(self.replay_input)
        minute_input = json.loads(canonical(self.replay_input)) if self.replay_input else None
        candidate_digest = digest_of(candidate)
        replayed = self._replayed_point(self.replay_input, minute)
        replay_digest = digest_of(replayed) if replayed is not None else ""
        transaction_digest = digest_of({"input": input_digest, "candidate": candidate_digest,
                                        "snapshot": self.snapshot_id, "minute": minute,
                                        "domain": list(self.domain), "site": SITE_VERSION})

        legacy_point = pressure_point(legacy_observable)
        written = shaped_like_legacy(candidate, legacy_observable)
        transaction = AuthorityTransaction(minute=minute, case_id=self.case_id, family=self.family,
                                           domain=self.domain, snapshot=self.snapshot)
        transaction.capture(after).compute(written, legacy_point)
        # P3-216 (NEW-06) and the review's F3: EVERY failure the shadow recorded since the last judged turn refuses this one. A turn that advances the clock
        # by N minutes is one commit of the end state; filtering on ``minute == end`` let a failure at minute k < N commit (found by this cycle's probe), and
        # a window on the minute stamp still let a failure stamped at the turn's START (a capture that failed) or recorded during a no-advance turn escape.
        failures = new_failures
        legacy_arrest = bool(dict(after.get("observable") or {}).get("pulse_present") is False)
        valid = transaction.validate(invariants_hold=not failures, replay_digest=replay_digest,
                                     expected_digest=candidate_digest, unsupported=unsupported,
                                     legacy_arrest=legacy_arrest, failures=failures)
        # P3-223 (R2): the commit is the engine's END state, so EVERY minute the turn crossed must have passed the same per-minute validation the pair
        # evaluator applies (``runtime_minute_validation``, one primitive for both). Until now only the end minute (and the failures the shadow recorded)
        # was judged: an intermediate minute with no candidate, or one the artifact does not reproduce, did not stop the commit. The end minute's own
        # refusal keeps its reason; this refuses only what the end minute passed.
        between = self._interval_check(valid, minute, session, unsupported, legacy_arrest)
        if between is not None and not between["ok"]:
            valid = False
            transaction.refuse(["interval_minutes_validated"], replay_digest=replay_digest,
                               reason=f"validation refused: ['interval_minutes_validated'] first failed minute {between['first_failed_minute']}: {between['failed']}")
        provenance = self._provenance(minute, transaction, candidate, after, shadow_minute, kinds,
                                      action_fates(ran), unsupported, submission_id,
                                      {"input": input_digest, "candidate": candidate_digest,
                                       "replay": replay_digest, "transaction": transaction_digest})
        # The P3-19 review: the artifact kept only the LAST immutable input, while every minute's
        # transaction digest was taken with the input of ITS minute, so no encounter of more than one
        # minute could be reproduced. Each minute now carries the input it was computed from.
        provenance["replay_input"] = minute_input
        provenance["precommit_observable_digest"] = digest_of(dict(after.get("observable") or {}))
        if self.grant is not None:
            provenance.update(self._real_minute_fields())
            provenance["interval_check"] = (None if between is None else {"mode": between["mode"], "interval_minutes": between["interval_minutes"], "ok": between["ok"],
                                                                         "rows": len(between["rows"])})
        if route == CLINICAL_TIME:
            # No order was given, so there is no ledger row to settle: the minute is settled by construction. Order turns keep their records
            # byte for byte (no new key) and settle after the pipeline, as they always did.
            provenance.update(route=CLINICAL_TIME, provenance_settled=True, provenance_contradictions=[], action_lineage=[])
        if not valid:
            # P3-26-3: the reason a faculty reader sees names the classes that blocked the minute, not
            # only the validation key that caught them.
            reason = (f"{UNSUPPORTED_AUTHORITY_ACTION}: {list(unsupported)}"
                      if "supported_management" in transaction.failures
                      else f"{VALIDATION_REFUSED}: {transaction.failures}")
            if transaction.reason and "snapshot" in transaction.reason:
                reason = f"{reason} | {transaction.reason}"
            if between is not None and not between["ok"]:
                reason = f"{reason} | interval minute {between['first_failed_minute']}: {between['failed']}"
                provenance["interval_validation"] = {"mode": between["mode"], "interval_minutes": between["interval_minutes"],
                                                     "first_failed_minute": between["first_failed_minute"], "failed": between["failed"],
                                                     "ineligible_after": between["ineligible_after"], "rows": between["rows"]}
            return self._hard_fail(minute, reason, ran, provenance=provenance,
                                   transaction=transaction)
        if settled_rows is not None:
            # P3-271: the lineage of the settled orders and their settled classes are judged BEFORE the commit. A contradiction the settlement reveals refuses the turn; it never leaves a committed
            # minute that has to be taken back (faculty decision F: a committed minute is never rewritten).
            contradictions = settlement_contradictions(action_fates(ran), settled_rows, submission_id)
            if contradictions:
                provenance["provenance_contradictions"] = [dict(item) for item in contradictions]
                return self._hard_fail(minute, f"{PROVENANCE_CONTRADICTION}: {contradictions}", ran, provenance=provenance, transaction=transaction)
        try:
            prepared = transaction.commit(after, environ=self.environ)
        except AuthorityRefused as refused:
            # The gate is named only when the gate refused: ``commit`` turns every failure into this
            # exception, and calling a write failure "the gate refused" misleads a reader.
            label = GATE_REFUSED if "gate refuses" in str(refused) else COMMIT_REFUSED
            return self._hard_fail(minute, f"{label}: {refused}", ran, provenance=provenance,
                                   transaction=transaction)
        moved = self._moved(after, prepared)
        if not moved <= {"sbp", "dbp", "map"}:
            # P3-19C, defence in depth: what reached the state is compared with what may be owned. The
            # test is containment, not equality: a common pressure that happens to equal the legacy one
            # moves nothing, and that is not an out-of-domain write.
            return self._hard_fail(minute, f"{OUT_OF_DOMAIN_WRITE}: {sorted(moved)}", ran,
                                   provenance=provenance, transaction=transaction)
        if self.grant is not None:
            # P3-273: a REAL commit writes the monotonic provenance anchor into the patient state it hands back, AFTER the out-of-domain check (the anchor is metadata that widens no domain): the
            # encounter then carries the fact that authority occurred wherever it goes, even if its session record and its site are both lost.
            try:
                import runtime_authority_session as _session
                prepared = {**dict(prepared), PROVENANCE_ANCHOR_KEY: _session.advance_anchor(dict(after).get(PROVENANCE_ANCHOR_KEY), self, minute, pressure_point(prepared.get("observable")))}
            except Exception as error:
                return self._hard_fail(minute, f"{PROVENANCE_ANCHOR_INVALID}: {type(error).__name__}: {error}", ran, provenance=provenance, transaction=transaction)
        provenance.update({"committed": sorted(transaction.committed), "outcome": COMMITTED,
                           "common_pressures": pressure_point(prepared.get("observable")),
                           "moved_fields": sorted(moved)})
        self.records.append(provenance)
        self._unpersisted_commit = True          # P3-271: durable only once ``minute`` has persisted it (see ``_persist``)
        return prepared

    # -- the pieces ------------------------------------------------------------------------------------
    def _reassertion(self, after: Mapping, minute: int) -> Mapping | None:
        """The state with the pressure this minute already committed written back over the engine's refresh, or ``None`` when this is not that situation.

        Only under a grant, only for a minute that committed, and only when the engine's refresh of the observable IS the legacy counterfactual that minute recorded (so
        nothing moved in the legacy engine): then the committed pressure is the authoritative one still. It writes the recorded written candidate (shaped as the legacy
        engine shows it, MAP derived as the display derives it) and nothing else, and it is checked to touch nothing outside the pressure domain."""
        try:
            if self.grant is None or minute not in self.minutes_committed:
                return None
            held = next(record for record in reversed(self.records) if _as_int(record.get("minute")) == minute and record.get("committed"))
            written, legacy_then = dict(held.get("written_candidate") or {}), held.get("legacy_counterfactual")
            if not written or legacy_then is None or pressure_point(dict(after).get("observable")) != dict(legacy_then):
                return None
            prepared = dict(deepcopy(dict(after)))
            observable = dict(prepared.get("observable") or {})
            observable.update({"sbp": written["sbp"], "dbp": written["dbp"]})
            mean = derived_map(written.get("sbp"), written.get("dbp"))
            if mean is not None:
                observable["map"] = mean
            prepared["observable"] = observable
            return prepared if self._moved(after, prepared) <= {"sbp", "dbp", "map"} else None
        except Exception:
            return None

    def _interval_check(self, end_valid: bool, minute: int, session, unsupported: Sequence[str], legacy_arrest: bool) -> dict | None:
        """The per-minute validation of the minutes BETWEEN the last judged minute and this turn's end minute, in pressure-only mode (P3-223).

        ``None`` when there is nothing to judge: the end minute already refused (its own reason stands) or the turn crossed no intermediate minute.
        It reads the shadow session and one replay of the artifact; it writes nothing and commits nothing."""
        if not end_valid:
            return None
        between = list(range(self.minutes_seen + 1, minute))
        if not between:
            return None
        import runtime_minute_validation as validation
        return validation.validate_interval(between, mode=validation.PRESSURE_ONLY, case_id=self.case_id, snapshot=self.snapshot, session=session,
                                            unsupported=unsupported, legacy_arrest=legacy_arrest, table=validation.replay_table(self.replay_input))

    @staticmethod
    def _shadow_minute(session, minute: int):
        for item in reversed(list(getattr(session, "minutes", []) or [])):
            if _as_int(item.minute) == minute:
                return item
        return None

    @staticmethod
    def _artifact_input(session) -> dict | None:
        runner = getattr(session, "runner", None)
        captured = None if runner is None else runner.replay_input()
        return None if captured is None else captured.to_dict()

    @staticmethod
    def _replayed_point(artifact: Mapping | None, minute: int) -> dict | None:
        """The same minute's pressures, recomputed from the serialized artifact alone (P3-19J)."""
        if not artifact:
            return None
        import runtime_shadow_families as fam
        replayed = fam.replay_shadow_encounter(json.loads(canonical(artifact)))
        for item in replayed["results"]:
            if _as_int(item["minute"]) == minute:
                return pressure_point(item["derived"])
        return None

    @staticmethod
    def _moved(before: Mapping, after: Mapping) -> set:
        """Which observable fields a commit actually changed, and whether it touched anything else."""
        left, right = dict(before), dict(after)
        # Canonical forms, not ``!=``: the review showed that a value comparing by identity, or a NaN,
        # reported itself as moved against its own deep copy, and produced a refusal that was not true.
        def same(one, two):
            return canonical(one) == canonical(two)

        outside = {key for key in set(left) | set(right)
                   if key not in ("observable", PROVENANCE_ANCHOR_KEY) and not same(left.get(key), right.get(key))}
        if outside:
            return outside
        one, two = dict(left.get("observable") or {}), dict(right.get("observable") or {})
        return {key for key in set(one) | set(two) if not same(one.get(key), two.get(key))}

    def _provenance(self, minute, transaction, candidate, after, shadow_minute, kinds, fates,
                    unsupported, submission_id, digests) -> dict:
        """P3-19E: everything a future authority minute must be readable from, outside Phase-2 schemas."""
        divergence = sorted({str(item.status) for item in getattr(shadow_minute, "divergences", ())
                             if str(item.variable) in self.domain})
        return {
            "site": SITE_VERSION,
            "experiment_id": self.experiment_id,
            "encounter_id": self.encounter_id,
            "case_id": self.case_id,
            "family": self.family,
            "minute": minute,
            "mode": MODE_LIMITED_COMMON_AUTHORITY,
            "environment": self.environment,
            "snapshot_id": self.snapshot_id,
            "snapshot": dict(self.snapshot) if isinstance(self.snapshot, Mapping) else self.snapshot,
            "phase2_closure_head": rs.PHASE2_CLOSURE_HEAD,
            "phase2_digest": rs.PHASE2_DIGEST,
            "phase3_versions": rs.family_versions(self.family),
            "authority_module": MODULE_VERSION,
            "submission_id": submission_id,
            "action_kinds": list(kinds),
            "action_fates": list(fates),
            "unsupported_actions": list(unsupported),
            "no_common_physiology": [dict(row) for row in executed_no_common_physiology(fates)],
            "input_digest": digests["input"],
            "candidate_digest": digests["candidate"],
            "replay_digest": digests["replay"],
            "transaction_digest": digests["transaction"],
            "common_candidate": dict(candidate),
            "written_candidate": shaped_like_legacy(candidate, dict(after.get("observable") or {})),
            "written_digest": digest_of(shaped_like_legacy(candidate,
                                                           dict(after.get("observable") or {}))),
            "legacy_shape": shape_of(after.get("observable")),
            "legacy_counterfactual": pressure_point(after.get("observable")),
            "state_digest": getattr(shadow_minute, "state_digest", ""),
            "divergence_classes": divergence,
            "validation_failures": list(transaction.failures),
            "validation_passed": not transaction.failures,
            "committed": [],
            "outcome": transaction.state,
            "failure_reason": transaction.reason,
            "failure_policy": FAILURE_POLICY,
        }

    def _refusal(self, minute: int, reason: str, ran: Sequence | None,
                 legacy: Mapping | None = None, unsupported: Sequence[str] = ()) -> dict:
        """A refused minute, in the SAME shape a committed one has: every field, empty where it has none.

        The P3-26 store verifies completeness over every minute, and a record that carried half the keys
        made a refusal less auditable than a commit for no reason at all.
        """
        empty = {name: None for name in ARTIFACT_MINUTE_FIELDS}
        return {**empty,
                "site": SITE_VERSION, "experiment_id": self.experiment_id,
                "encounter_id": self.encounter_id, "case_id": self.case_id, "family": self.family,
                "minute": minute, "mode": MODE_LIMITED_COMMON_AUTHORITY,
                "snapshot_id": self.snapshot_id, "outcome": ABORTED, "committed": [],
                "failure_reason": reason, "failure_policy": FAILURE_POLICY,
                "action_kinds": list(action_kinds(ran)), "action_fates": list(action_fates(ran)),
                "unsupported_actions": list(unsupported), "divergence_classes": [],
                "no_common_physiology": [dict(row) for row in executed_no_common_physiology(action_fates(ran))],
                "validation_failures": [], "validation_passed": False,
                # Faculty decision F: the legacy counterfactual of the failed minute is preserved even
                # when the refusal came before any transaction was opened.
                "legacy_counterfactual": (None if legacy is None else pressure_point(legacy)),
                "legacy_shape": (None if legacy is None else shape_of(legacy)),
                "precommit_observable_digest": (None if legacy is None
                                                else digest_of(dict(legacy))),
                "phase2_digest": rs.PHASE2_DIGEST,
                **(self._safe_real_minute_fields() if self.grant is not None else {})}

    def _hard_fail(self, minute: int, reason: str, ran: Sequence | None, *, provenance: dict | None = None,
                   transaction: "AuthorityTransaction | None" = None,
                   legacy: Mapping | None = None, unsupported: Sequence[str] = ()) -> None:
        """The failure policy, in one place: stop visibly, commit nothing, never switch engines."""
        self.halted = True
        self.experiment_state = EXPERIMENT_HALTED
        self.halt_reason = reason
        record = provenance or self._refusal(minute, reason, ran, legacy, unsupported)
        record.update({"outcome": ABORTED, "committed": [], "failure_reason": reason,
                       "halted": True})
        if transaction is not None:
            record["rollback"] = (transaction.rollback
                                  or rollback_artifact(transaction, reason=reason,
                                                       replay_digest=record.get("replay_digest")))
        else:
            # A refusal before any transaction opened still leaves a rollback record: the P3-28 review
            # found the internal-error path without one, and decision F asks for the failed minute to be
            # reproducible whatever refused it.
            record["rollback"] = {
                "failure_policy": FAILURE_POLICY, "mode_decided_at": MODE_DECIDED_AT,
                "reason": reason, "minute": minute,
                "precommit_authoritative_state": (None if legacy is None
                                                  else {"observable": dict(legacy)}),
                "common_candidate": None, "legacy_counterfactual": record.get("legacy_counterfactual"),
                "validation_failures": [], "action_history": list(action_fates(ran)),
                "parameter_snapshot": (dict(self.snapshot) if isinstance(self.snapshot, Mapping)
                                       else self.snapshot),
                "phase2_digest": rs.PHASE2_DIGEST, "phase3_layer": rs.MODULE_VERSION,
                "phase3_layer_digest": rs.layer_digest(), "replay_digest": None, "committed": [],
                "rescue": "replay the encounter from its immutable artifact with the legacy "
                          "counterfactual as the authority; never continue the same encounter with the "
                          "other engine",
            }
        self.records.append(record)
        return None

    # -- the artifact ----------------------------------------------------------------------------------
    def artifact(self) -> dict:
        """The immutable record of this (future) experiment, digested over its canonical form.

        It never raises: the P3-19 review found that a malformed approval made the serialization fail and
        the exception would have reached the encounter from the call site, which calls this every turn.
        """
        try:
            return self._artifact()
        except Exception as error:
            return {"artifact": "phase3_authority_experiment", "site": SITE_VERSION,
                    "experiment_id": self.experiment_id, "encounter_id": self.encounter_id,
                    "halted": True, "halt_reason": f"ARTIFACT_ERROR {type(error).__name__}: {error}",
                    "minutes": [], "artifact_digest": ""}

    def _artifact(self) -> dict:
        body = {
            "artifact": "phase3_authority_experiment",
            "site": SITE_VERSION,
            "experiment_id": self.experiment_id,
            "encounter_id": self.encounter_id,
            "case_id": self.case_id,
            "family": self.family,
            "domain": list(self.domain),
            "ownership": ownership(self.domain),
            "environment": self.environment,
            "snapshot_id": self.snapshot_id,
            "snapshot": dict(self.snapshot) if isinstance(self.snapshot, Mapping) else self.snapshot,
            "phase2_closure_head": rs.PHASE2_CLOSURE_HEAD,
            "phase2_digest": rs.PHASE2_DIGEST,
            "phase3_versions": rs.family_versions(self.family),
            "authority_module": MODULE_VERSION,
            "failure_policy": FAILURE_POLICY,
            "mode_decided_at": MODE_DECIDED_AT,
            "attempt": self.attempt,
            "experiment_state": self.experiment_state,
            "invalid_for_continuation": (INVALID_FOR_CONTINUATION if self.halted else ""),
            "store": STORE_CONTRACT,
            "halted": self.halted,
            "halt_reason": self.halt_reason,
            # A halt AFTER a commit leaves the encounter's pressure trajectory mixed: legacy before the
            # authority minutes, common during them, legacy after. The P3-19 review is right that this
            # contradicts "no engine switching mid-encounter", and it cannot be undone retroactively --
            # so it is DECLARED here, and the rescue is to read the encounter from this artifact.
            "mixed_trajectory": bool(self.halted and self.minutes_committed),
            "authority_minutes": list(self.minutes_committed),
            "eligibility": (None if self.eligibility is None else dict(self.eligibility)),
            "action_history": [dict(item) for record in self.records
                               for item in (record.get("action_fates") or [])],
            "minutes": [dict(record) for record in self.records],
            "replay_input": (None if self.replay_input is None
                             else json.loads(canonical(self.replay_input))),
        }
        if self.no_advance_turns:
            body["no_advance_turns"] = [dict(item) for item in self.no_advance_turns]          # only when there are some: the usual artifact is unchanged
        if self.grant is not None:
            body.update(self._real_artifact_fields())                                           # P3-246: only a run under the grant carries these: the historical artifact is unchanged
        return {**body, "artifact_digest": digest_of(body)}

    # -- P3-240/243/245/246: the grant, the overlay and the boundary ----------------------------------------------------------------------
    def _overlay_for(self, session):
        """The overlay beside this experiment, built once from the shadow session's authored arrival. Never raises: an overlay that cannot be built is a refusal named in
        ``overlay_refusal``, and the boundary guard then fails CLOSED (the boundary cannot be verified, so no minute is committed)."""
        if self.overlay is not None or self.overlay_refusal:
            return self.overlay
        try:
            import runtime_authority_pair as pair
            arrival = getattr(session, "arrival", None)
            if arrival is None or getattr(session, "runner", None) is None:
                raise ValueError("the shadow session has no authored arrival or runner to bind the overlay to")
            self.overlay = pair.ConsciousnessOverlay(pair.bind(), self.case_id, arrival)
        except Exception as error:
            self.overlay_refusal = f"{type(error).__name__}: {error}"
        return self.overlay

    def _overlay_turn(self, after: Mapping, session) -> dict:
        overlay = self._overlay_for(session)
        if overlay is None:
            return {"available": False, "why": self.overlay_refusal or "no overlay", "minute": _as_int(dict(after).get("sim_time")), "boundary": None, "clear": False, "rows": []}
        try:
            turn = overlay.turn(after, session)
            turn["available"] = True
            return turn
        except Exception as error:               # ``turn`` does not raise; a second line of defence, because the overlay may never break an encounter
            return {"available": False, "why": f"{type(error).__name__}: {error}", "minute": _as_int(dict(after).get("sim_time")), "boundary": None, "clear": False, "rows": []}

    def _boundary_guard(self, minute: int) -> str:
        """``''`` when this minute may be judged for a commit, else the reason it may not (a hard failure with that reason)."""
        window = dict(dict(self.grant or {}).get("window") or {}).get("max_minute")
        if window is not None and minute > int(window):
            return f"{WINDOW_CLOSED}: minute {minute} is past the experiment window of {window} minutes"
        turn = dict(self.current_overlay or {})
        if not turn.get("available"):
            return f"{COLLAPSE_BOUNDARY_NOT_VERIFIABLE}: the consciousness overlay that carries the boundary is unavailable ({turn.get('why')})"
        boundary = dict(turn.get("boundary") or {})
        if boundary.get("first_established_minute") is not None:
            return (f"{COLLAPSE_BOUNDARY_REACHED}: the common core reads ESTABLISHED collapse at minute {boundary['first_established_minute']} of the interval "
                    f"{turn.get('from_minute')}..{minute}: an experiment boundary, never a patient state")
        if not turn.get("clear"):
            return (f"{COLLAPSE_BOUNDARY_NOT_VERIFIABLE}: minutes not shown {list(boundary.get('minutes_not_shown') or [])}, "
                    f"one course {dict(turn.get('course') or {}).get('one_course')}, failures {list(turn.get('failed') or [])}")
        return ""

    def _safe_real_minute_fields(self) -> dict:
        """The failure handler's own fields: whatever goes wrong while describing a failure is recorded as part of it, and never escapes into the page (review L3)."""
        try:
            return self._real_minute_fields()
        except Exception as error:
            return {"grant_id": dict(self.grant or {}).get("grant_id"), "grant_fingerprint": dict(self.grant or {}).get("fingerprint"), "authority_mode": "PRESSURE_ONLY",
                    "legacy_non_authority": None, "consciousness_overlay": None,
                    "collapse_boundary": {"policy": "ESTABLISHED_PRECOMMIT_FAIL_CLOSED", "first_established_minute": None, "minutes_not_shown": [], "clear": False},
                    "real_fields_error": f"{type(error).__name__}: {error}"}

    def _real_minute_fields(self) -> dict:
        import runtime_pressure_grant as grants
        turn = dict(self.current_overlay or {})
        boundary = dict(turn.get("boundary") or {})
        return {"grant_id": dict(self.grant).get("grant_id"), "grant_fingerprint": dict(self.grant).get("fingerprint"), "authority_mode": grants.AUTHORITY_MODE,
                "legacy_non_authority": (None if self.current_legacy is None else dict(self.current_legacy)),
                "consciousness_overlay": ({key: turn.get(key) for key in ("available", "why", "minute", "from_minute", "legacy_mental_status", "rows", "course", "clear", "digest")}
                                          if turn else None),
                "collapse_boundary": {"policy": "ESTABLISHED_PRECOMMIT_FAIL_CLOSED", "first_established_minute": boundary.get("first_established_minute"),
                                      "minutes_not_shown": list(boundary.get("minutes_not_shown") or []), "clear": bool(boundary.get("clear")) and bool(turn.get("clear"))}}

    def _real_artifact_fields(self) -> dict:
        import runtime_pressure_grant as grants
        grant = dict(self.grant)
        policy = dict(grant.get("failure_policy") or {})
        if self.overlay is not None:
            overlay = self.overlay.overlay_summary()
        else:
            overlay = {"label": grants.OVERLAY_LABEL, "role": "CANDIDATE_OVERLAY_NONAUTHORITATIVE", "available": False, "why": self.overlay_refusal, "authority": False,
                       "resident_visible": False, "writes_mental_status": False, "written_into_the_encounter": False, "turns": [], "violations": [], "replay_input": None,
                       "snapshot": None}
        failed = next((record for record in self.records if record.get("outcome") == ABORTED), None)
        committed = list(self.minutes_committed)
        return {"authority_label": grants.ARTIFACT_LABEL, "authority_mode": grants.AUTHORITY_MODE, "grant": grants.summary(grant),
                "authority_began": bool(committed),
                "experiment_outcome": ("INVALID_FOR_CONTINUATION" if self.halted and committed else "EXPERIMENT_HALTED" if self.halted else "ACTIVE"),
                "excluded_domains": list(grants.EXCLUDED_DOMAINS), "consciousness_overlay": overlay,
                "collapse_boundary": {"policy": dict(grant.get("collapse_boundary") or {}), "window_max_minute": dict(grant.get("window") or {}).get("max_minute"),
                                      "last_authoritative_commit_minute": (max(committed) if committed else None),
                                      "first_rejected_minute": (None if failed is None else failed.get("minute")), "rejection_reason": (self.halt_reason if self.halted else ""),
                                      "common_state_at_rejection": (None if failed is None else dict(failed.get("consciousness_overlay") or {}) or None)},
                "post_commit_policy": {"before_the_first_commit": policy.get("before_the_first_commit"), "after_the_first_commit": policy.get("after_the_first_commit"),
                                       "silent_fallback_to_the_legacy_engine": False, "is_patient_death": False,
                                       "what_the_page_does": ("the legacy engine keeps running the encounter, and the resident sees nothing of the experiment; the experiment is INVALID_FOR_CONTINUATION "
                                                              "after a commit (EXPERIMENT_HALTED before one): no later minute is authoritative, the artifact is the record, and it is read, never continued")}}


def _as_int(value: Any) -> int:
    try:
        return int(value or 0)
    except Exception:
        return 0


#: What the immutable eligibility record of a real encounter carries (P3-46-5). It is built from the
#: SAME ``AuthorityGate`` that opened the site, so it cannot disagree with the gate that was used.
ELIGIBILITY_RECORD_FIELDS = ("classification", "family", "case_id", "domain", "snapshot_id", "snapshot",
                             "environment", "pilot", "unsupported_actions", "phase2_digest",
                             "layer_version", "artifact_store_configured", "allowlisted", "granted",
                             "conditions", "reasons", "decided_at")


def eligibility_record(decision: "AuthorityGate", *, family: str, case_id: str, environment: str,
                       snapshot: Mapping | None, domain: Sequence[str] = AUTHORITY_DOMAIN,
                       store_configured: bool = False, environ: Mapping[str, str] | None = None) -> dict:
    """The eligibility decision that allowed authority, as data, at the moment it allowed it.

    P3-44 found a real encounter's artifact carrying no eligibility row at all, so nothing in the record
    said why authority had been allowed. This is not a second reading and not prose: every condition is
    the gate's own, copied from the decision object the site was opened with (P3-46-6).
    """
    live = os.environ if environ is None else environ
    conditions = dict(decision.conditions)
    is_pilot, why_pilot = looks_like_the_pilot(live)
    return {
        "classification": (ELIGIBLE_FOR_DEVELOPMENT if decision.granted else INELIGIBLE_OTHER),
        "family": str(family), "case_id": str(case_id), "domain": list(domain),
        "snapshot_id": str(decision.snapshot_id or ""),
        "snapshot": (dict(snapshot) if isinstance(snapshot, Mapping) else snapshot),
        "environment": str(environment),
        "pilot": {"looks_like_the_pilot": bool(is_pilot), "why": str(why_pilot or ""),
                  "markers": list(pilot_deployment_markers())},
        # The gate refuses an undeclared action, so a granted decision is a decision in which none ran.
        "unsupported_actions": [],
        "phase2_digest": rs.PHASE2_DIGEST,
        "layer_version": rs.MODULE_VERSION,
        "artifact_store_configured": bool(store_configured),
        "allowlisted": bool(str(case_id) in AUTHORITY_CASES and str(family) == AUTHORITY_FAMILY),
        "granted": bool(decision.granted),
        "conditions": conditions,
        "reasons": list(decision.reasons),
        "decided_at": MODE_DECIDED_AT,
    }


def open_site(state: Mapping, *, environ: Mapping[str, str] | None = None,
              experiment_id: str | None = None) -> AuthoritySite | None:
    """The ONE way a runtime obtains an authority site, and today it always returns None.

    The flag is read first on purpose: a production encounter pays one dictionary lookup and never the
    cost of recomputing the Phase-2 digest. Reading it first is not a weakening -- it is one of the nine
    conditions, and the whole gate runs whenever it is set.

    The mode is decided HERE, once, at the encounter's arrival: a site opened mid-encounter is refused.
    """
    live = os.environ if environ is None else environ
    if str(live.get(AUTHORITY_FLAG, "") or "").strip().lower() != MODE_LIMITED_COMMON_AUTHORITY:
        return None
    if rs.mode(live) != rs.MODE_SHADOW_COMPARE:
        # Authority has no candidate of its own: the common core must be running beside the engine. The
        # P3-19 review found a site opened without it and failed only at the first minute.
        return None
    import runtime_authority_store as artifact_store
    if not artifact_store.configured(live):
        # Faculty decision F: a hard failure must be preserved. The P3-28 review found that a whole
        # experiment could run with the store off and leave nothing durable, so an experiment with
        # nowhere to record itself does not start.
        return None
    if encounter_mode(state, environ=live, unsupported=()) != MODE_LIMITED_COMMON_AUTHORITY:
        return None
    decision = gate(state, environ=live, unsupported=())
    snapshot = approved_snapshot(decision.snapshot_id)
    if not decision.granted or snapshot is None:
        return None
    from clinical_core import legacy_adapter
    case_id = str(legacy_adapter.engine_case_id(dict(state)))
    encounter = rs._encounter_id(dict(state))
    spec = dict(dict(state).get("encounter_spec") or {})
    attempt = spec.get("attempt_number", spec.get("attempt", dict(state).get("attempt_number")))
    site = AuthoritySite(case_id=case_id, family=str(dict(state).get("engine_family") or ""),
                         snapshot=snapshot, snapshot_id=str(decision.snapshot_id or ""),
                         encounter_id=encounter, environment=str(live.get(ENVIRONMENT_FLAG, "")),
                         environ=None if environ is None else dict(environ), attempt=attempt,
                         experiment_id=str(experiment_id or digest_of({"encounter": encounter,
                                                                       "snapshot": decision.snapshot_id,
                                                                       "site": SITE_VERSION})[:16]))
    # P3-240: the explicit development grant travels with the site, but only when it is the one that authorizes THIS run (the real registered point, the case, the
    # environment, the family and the live core lineage). A run with a TEST-ONLY point carries none and behaves as before the grant existed.
    import runtime_pressure_grant as grants
    member = rs.CORE_LINEAGE[-1]
    if not grants.grant_problems(grants.GRANT, case_id=case_id, environment=str(live.get(ENVIRONMENT_FLAG, "") or "").strip().lower(), snapshot_id=str(decision.snapshot_id or ""),
                                 family=site.family, lineage={"version_id": member.version_id, "digest": member.digest}):
        site.grant = grants.GRANT
    elif str(decision.snapshot_id or "") == grants.PRESSURE_SNAPSHOT_ID:
        return None                  # the REAL registered point never runs without the grant it is bound to (a registry that disagrees with the grant opens nothing)
    # P3-46-5: the decision that allowed authority travels with the site, so the artifact says why.
    site.eligibility = eligibility_record(
        decision, family=site.family, case_id=case_id, environment=site.environment,
        snapshot=snapshot, domain=site.domain, store_configured=True, environ=live)
    return site


def site_for(state: Mapping, store: Any,
             *, environ: Mapping[str, str] | None = None) -> AuthoritySite | None:
    """This encounter's site, kept in the caller's store. The caller orchestrates and decides nothing.

    Three properties, in this order:

    * the flag is read FIRST, so a production turn costs one dictionary lookup -- no import, no store
      write and above all no Phase-2 digest;
    * a site appears only at the arrival, so no configuration can introduce authority mid-encounter;
    * a refusal is remembered for that case and minute, so repeated reruns of the same turn do not
      re-evaluate the gate.
    """
    live = os.environ if environ is None else environ
    asked = str(live.get(AUTHORITY_FLAG, "") or "").strip().lower() == MODE_LIMITED_COMMON_AUTHORITY
    try:
        existing = store.get(SITE_KEY)
    except Exception:
        # The authority site may never break an encounter: a failure here is a refusal.
        return None
    if existing is None and not asked:
        # The production path: two dictionary lookups, no import, no store write and no digest.
        return None
    try:
        site = existing
        if site is not None and not site.is_for(state):
            if site.halted and _same_encounter(site, state):
                # The halt outlives the site: the artifact stays for the faculty surface, the encounter
                # is remembered as halted, and no new site opens for it (P3-28 review).
                store[HALTED_KEY] = site.encounter_id
                store[SITE_KEY] = None
                return None
            site = None
            for key in (SITE_KEY, SITE_REFUSED_KEY, ARTIFACT_KEY, HALTED_KEY, SESSION_KEY):
                store[key] = None
        if site is not None:
            site._session_store = store          # P3-251: where this site publishes its session record (a non-field attribute: never serialized, never compared)
            if not asked or _configuration_changed(site, live) or _faculty_review_revoked(store, live):
                # The mode is decided at the arrival and may not change inside an encounter. A flag that
                # disappears or changes mid-encounter is a configuration change, and a configuration
                # change is a hard failure the faculty sees -- never a silent return to the legacy engine.
                if not site.halted:
                    site.halted = True
                    site.experiment_state = EXPERIMENT_HALTED
                    site.halt_reason = CONFIGURATION_CHANGED
                    site.records.append(site._refusal(_as_int(dict(state).get("sim_time")),
                                                      CONFIGURATION_CHANGED, (),
                                                      dict(dict(state).get("observable") or {})))
                    site._persist()
            return site
        minute = _as_int(dict(state).get("sim_time"))
        if minute != 0 or not asked:
            if asked and existing is None:
                note_resume_without_site(state, store, live)
            return None
        if store.get(HALTED_KEY) and store.get(HALTED_KEY) == rs._encounter_id(dict(state)):
            return None
        from clinical_core import legacy_adapter
        key = f"{legacy_adapter.engine_case_id(dict(state))}@{minute}"
        if store.get(SITE_REFUSED_KEY) == key:
            return None
        if str(live.get("MRS_FACULTY_DEVELOPMENT_REVIEW", "") or "").strip() or dict(store.get("phase3_faculty_review") or {}).get("requested") is True:
            # P3-281A: a named faculty review mode with a missing or partial configuration makes the authority UNAVAILABLE for this encounter, never partially enabled. A session that WAS a review
            # session and whose flag has since gone is refused too (it does not continue as an ordinary development encounter).
            import runtime_faculty_review as _review
            available, why = _review.authority_available(store, live)
            if not available:
                store[SITE_REFUSED_KEY] = key
                store["phase3_faculty_review_refusal"] = why
                return None
        site = open_site(state, environ=environ)
        store[SITE_KEY] = site
        if site is None:
            store[SITE_REFUSED_KEY] = key
        else:
            site._session_store = store
            site._publish_session()              # PREAUTHORITY: the experiment exists and nothing has committed yet
        return site
    except Exception:
        return None


def durable_match(state: Mapping, live: Mapping[str, str]) -> dict | None:
    """P3-255: the authority-session record of the stored experiment (active OR halted) whose last committed minute IS this state -- same case, same minute, same committed pressures --
    or None. It is how a saved encounter that came back without its record is recognised in the durable store. Never raises."""
    try:
        body = _resumed_artifact(state, live, include_halted=True)
        if body is None:
            return None
        import runtime_authority_session as session
        return session.session_record_of(body)
    except Exception:
        return None


def _resumed_artifact(state: Mapping, live: Mapping[str, str], *, include_halted: bool = False) -> dict | None:
    """The stored, still-ACTIVE experiment (or, with ``include_halted``, any stored one) whose last committed minute IS this state: same case, same minute, same committed pressures. Never raises."""
    import runtime_authority_store as artifact_store
    from clinical_core import legacy_adapter
    case_id = str(legacy_adapter.engine_case_id(dict(state)))
    minute = _as_int(dict(state).get("sim_time"))
    observable = dict(dict(state).get("observable") or {})
    now = (observable.get("sbp"), observable.get("dbp"))
    best = None
    for path in artifact_store.paths(environ=live):
        if not path.name.startswith(f"{case_id}__"):
            continue            # P3-262 (review LOW-3): the name of a stored record starts with its case, so another case's files are not even parsed (the guard calls this on every run)
        try:
            body = dict(json.loads(path.read_text(encoding="utf-8")).get("artifact") or {})
        except Exception:
            continue
        if body.get("case_id") != case_id or (body.get("halted") and not include_halted) or not body.get("authority_minutes"):
            continue
        last = [dict(item) for item in (body.get("minutes") or []) if dict(item).get("committed")][-1:]
        if not last or _as_int(last[0].get("minute")) != minute:
            continue
        written = dict(last[0].get("written_candidate") or {})
        if (written.get("sbp"), written.get("dbp")) != now:
            continue
        if best is None or len(body.get("minutes") or []) > len(best.get("minutes") or []):
            best = body
    return best


def note_resume_without_site(state: Mapping, store: Any, live: Mapping[str, str]) -> dict | None:
    """P3-248 (review M1). The saved session keeps the patient state (with the pressures the common authority committed) but NOT the authority site, so an encounter
    resumed after a commit has no site and the legacy engine runs it from there. That is a return to the legacy engine; it is never silent: the stored experiment is
    marked halted (``ENCOUNTER_RESUMED_WITHOUT_ITS_AUTHORITY_SITE``, INVALID_FOR_CONTINUATION, mixed trajectory) and the session carries that artifact so the faculty
    reading says so. Checked once per case and minute of a session; matched by case, minute and committed pressures; a store that is not configured, or no match, marks
    nothing. Never raises."""
    try:
        minute = _as_int(dict(state).get("sim_time"))
        from clinical_core import legacy_adapter
        marked = f"{legacy_adapter.engine_case_id(dict(state))}@{minute}"
        if store.get(RESUME_CHECKED_KEY) == marked:
            return None
        store[RESUME_CHECKED_KEY] = marked
        import runtime_authority_store as artifact_store
        if minute <= 0 or not artifact_store.configured(live):
            return None
        body = _resumed_artifact(state, live)
        if body is None:
            return None
        reason = (f"{RESUMED_WITHOUT_SITE}: the encounter was resumed at minute {minute} without its authority site (the site is not part of the saved session); the pressures "
                  f"of minutes {list(body.get('authority_minutes') or [])} stay in the saved state and the legacy engine runs the encounter from here")
        marker = {key: value for key, value in body.items() if key != "artifact_digest"}
        marker.update({"halted": True, "halt_reason": reason, "experiment_state": EXPERIMENT_HALTED, "invalid_for_continuation": INVALID_FOR_CONTINUATION,
                       "mixed_trajectory": True, "resumed_at_minute": minute})
        if marker.get("authority_label") == REAL_PRESSURE_LABEL:
            marker["experiment_outcome"] = "INVALID_FOR_CONTINUATION"
            marker["collapse_boundary"] = {**dict(marker.get("collapse_boundary") or {}), "rejection_reason": reason}
        marker["artifact_digest"] = digest_of(marker)
        artifact_store.persist(marker, environ=live)          # the digest covers every field, so the storage receipt is not written into the artifact
        store[ARTIFACT_KEY] = marker
        return marker
    except Exception:
        return None


# -- P3-215A: the page's ONE hook for a clock advance reaches the dormant pair layer THROUGH this declared crossing ---------------------------------------
# ``app.py`` imports this module and nothing else of the layer: the pair authority is a layer module, imported here on use, so the page's import graph
# crosses into ``clinical_core`` by the same two declared crossings it always had.

def after_clock_moved(store: Any, session: Any, before: Mapping | None, after: Mapping, ran: Sequence | None, submission_id: Any, route: str,
                      *, environ: Mapping[str, str] | None = None) -> Mapping | None:
    """The page calls this right after the engine moved the clock, on EVERY route. See ``runtime_authority_pair.after_clock_moved``."""
    import runtime_authority_pair
    return runtime_authority_pair.after_clock_moved(store, session, before, after, ran, submission_id, route, environ=environ)


def after_orders_settled(store: Any, session: Any, orders: Sequence | None, *, environ: Mapping[str, str] | None = None) -> None:
    """The second phase of the hook, for an order turn. See ``runtime_authority_pair.after_orders_settled``."""
    import runtime_authority_pair
    runtime_authority_pair.after_orders_settled(store, session, orders, environ=environ)


class AuthoritySessionStopped(RuntimeError):
    """Raised by a page chokepoint that is reached while the experimental authority session is stopped: the loud, fail-closed form of a bypass the page's own gating should have prevented
    (P3-253). Defined here because the page reaches the layer only through this module."""


def continuation_guard(store: Any, state: Mapping | None, *, environ: Mapping[str, str] | None = None, encounter_ended: bool = False) -> dict:
    """The page's ONE question before it moves the experimental encounter: may this authority session continue? See ``runtime_authority_session.continuation_guard``."""
    import runtime_authority_session as session
    return session.continuation_guard(store, state, environ=environ, encounter_ended=encounter_ended)


def operation_allowed(decision: Mapping, operation: str) -> bool:
    """Whether the page may perform ``operation`` under a guard decision: only reading and leaving the session survive a stop."""
    import runtime_authority_session as session
    return session.operation_allowed(decision, operation)


def authority_turn(store: Any, *, route: str = "") -> Any:
    """P3-271: the context under which the page runs ONE turn of the encounter. When a real authority session has already committed and can continue, the turn runs on working copies of the
    encounter and is applied only if the authority holds it valid; otherwise (every flag off, the first pilot, a legacy encounter, a session before its first commit) it is a no-op context and the
    page runs exactly as it always did. See ``runtime_authority_turn``."""
    import runtime_authority_turn as turn
    return turn.begin(store, route=route)


def turn_applies(store: Any) -> bool:
    """P3-271: whether the next turn of this encounter would be transactional (see ``runtime_authority_turn.applies``)."""
    import runtime_authority_turn as turn
    return turn.applies(store)


def turn_check(store: Any) -> None:
    """P3-271: called right after the authority judged the turn; a turn it refused is unwound here (``AuthorityTurnDiscarded``, swallowed by the turn's own context). One lookup when no turn is open."""
    import runtime_authority_turn as turn
    turn.check(store)


def faculty_review_layer() -> Any:
    """The faculty development review layer (P3-281), reached ONLY through this module: the page has one crossing into the Phase-3 layer, so the review environment adds no second path from the
    page to the common core. Returns a namespace with ``review`` (mode, single process, scenarios) and ``bundles`` (status view, bundle, feedback)."""
    from types import SimpleNamespace
    import runtime_faculty_bundle
    import runtime_faculty_review
    return SimpleNamespace(review=runtime_faculty_review, bundles=runtime_faculty_bundle)


def turn_reset(store: Any) -> None:
    """P3-276 (review L2): close a turn an earlier page run left open (see ``runtime_authority_turn.reset_stale``). One lookup when none is open."""
    import runtime_authority_turn as turn
    turn.reset_stale(store)


def forget_dry_evaluator(store: Any) -> None:
    """A new encounter drops the dry evaluator beside the shadow session and the site."""
    import runtime_authority_pair
    runtime_authority_pair.forget(store)


def _same_encounter(site: "AuthoritySite", state: Mapping) -> bool:
    """Whether a state is the arrival this site opened on, by the arrival's own digest."""
    try:
        return rs._encounter_id(dict(state)) == site.encounter_id
    except Exception:
        return False


def _faculty_review_revoked(store: Any, live: Mapping[str, str]) -> bool:
    """Whether a faculty-review SESSION (the process names the review mode, or this session's decision says it was one) no longer holds its review configuration: a flag removed or changed after the
    page decided is a configuration change like any other, so the experiment halts and never goes on as an ordinary development encounter. An ordinary session answers False after two lookups."""
    try:
        named = bool(str(live.get("MRS_FACULTY_DEVELOPMENT_REVIEW", "") or "").strip())
        requested = dict(store.get("phase3_faculty_review") or {}).get("requested") is True
    except Exception:
        return False
    if not (named or requested):
        return False
    try:
        import runtime_faculty_review as _review
        return not _review.authority_available(store, live)[0]
    except Exception:
        return True


def _configuration_changed(site: "AuthoritySite", live: Mapping[str, str]) -> bool:
    """Whether the authority configuration of a running experiment is no longer the one it opened on."""
    try:
        if site.environ is not None:
            return False  # an explicit environment was handed in: it is the experiment's own
        return (str(live.get(SNAPSHOT_FLAG, "") or "").strip() != site.snapshot_id
                or str(live.get(ENVIRONMENT_FLAG, "") or "").strip() != site.environment)
    except Exception:
        return True


def _provenance_is_consistent(minute: Mapping) -> bool:
    """Every class the minute recorded has a canonical order id and a fate under which it acted."""
    item = dict(minute)
    if item.get("route") == CLINICAL_TIME:
        # P3-215: the activity route has no orders, so its lineage is EMPTY by contract; a row on it is a contradiction
        return (bool(item.get("provenance_settled")) and not item.get("provenance_contradictions") and not list(item.get("action_kinds") or [])
                and not list(item.get("action_lineage") or []))
    if not item.get("provenance_settled"):
        return False
    if item.get("provenance_contradictions"):
        return False
    rows = [dict(row) for row in (item.get("action_lineage") or item.get("action_fates") or [])]
    if not rows:
        return False
    # After settlement the two copies ARE the same rows, so a difference between them means the
    # artifact was edited: forging either one is detectable, not only the one the check reads.
    if item.get("action_lineage") is not None and item.get("action_fates") is not None:
        if [dict(row) for row in item["action_lineage"]] != [dict(row) for row in item["action_fates"]]:
            return False
    # P3-53-4: one falsifiable invariant per consumed action, on the canonical lineage. No class
    # matching, so a class whose order belongs to another submission is linked, not shrugged at.
    for row in rows:
        if not str(row.get("order_id") or "").strip():
            return False
        if not str(row.get("fate") or "").strip():
            return False
        if str(row.get("link") or "") != LINK_VALID:
            return False
    return True


def eligibility_is_consistent(artifact: Mapping) -> tuple:
    """(ok, reasons): the stored eligibility row against the artifact it was stored in (P3-46-6)."""
    body = dict(artifact)
    row = body.get("eligibility")
    if not isinstance(row, Mapping):
        return False, ("the artifact carries no eligibility record",)
    row = dict(row)
    reasons = []
    for name in ELIGIBILITY_RECORD_FIELDS:
        if name not in row:
            reasons.append(f"the eligibility record has no {name!r}")
    for name, expected in (("family", body.get("family")), ("case_id", body.get("case_id")),
                           ("snapshot_id", body.get("snapshot_id")),
                           ("environment", body.get("environment")),
                           ("phase2_digest", body.get("phase2_digest"))):
        if name in row and expected is not None and str(row.get(name)) != str(expected):
            reasons.append(f"eligibility {name}={row.get(name)!r} but the artifact says {expected!r}")
    if "domain" in row and body.get("domain") is not None \
            and list(row.get("domain") or []) != list(body.get("domain") or []):
        reasons.append("the eligibility domain is not the artifact's domain")
    if "granted" in row and not row.get("granted"):
        reasons.append("the eligibility record says the gate did not grant, yet a site was opened")
    conditions = dict(row.get("conditions") or {})
    if conditions and sorted(conditions) != sorted(GATE_CONDITIONS):
        reasons.append("the eligibility record does not carry the gate conditions")
    failing = sorted(name for name, ok in conditions.items() if not ok)
    if failing:
        reasons.append(f"the eligibility record carries failing conditions: {failing}")
    return (not reasons), tuple(reasons)


def replay_site_artifact(artifact: Mapping) -> dict:
    """P3-19J: recompute every minute of a (future) experiment from its serialized artifact alone.

    Nothing is read from a live session: the replay input inside the artifact is the only source, so a
    reproduction that disagrees with the recorded digests is a failure of the experiment, not of the read.
    """
    body = dict(artifact)
    recorded = [dict(item) for item in (body.get("minutes") or [])]
    rows = []
    for item in recorded:
        minute = _as_int(item.get("minute"))
        # Each minute's OWN immutable input, as the artifact carries it; the whole-encounter input is
        # the fallback for an artifact written before P3-19's review.
        replay_input = item.get("replay_input") or body.get("replay_input")
        point = AuthoritySite._replayed_point(replay_input, minute)
        candidate_digest = "" if point is None else digest_of(point)
        transaction_digest = digest_of({"input": digest_of(replay_input) if replay_input else "",
                                        "candidate": candidate_digest,
                                        "snapshot": body.get("snapshot_id"), "minute": minute,
                                        "domain": list(body.get("domain") or AUTHORITY_DOMAIN),
                                        "site": str(body.get("site") or SITE_VERSION)})
        # P3-23B: the commit decision is reconstructed too, not read: the written pressures must be the
        # shape of the legacy ones the artifact recorded, and the outcome must match what was committed.
        written = None if point is None else apply_shape(point, item.get("legacy_shape"))
        rows.append({
            "minute": minute,
            "common_pressures": point,
            "candidate_digest": candidate_digest,
            "transaction_digest": transaction_digest,
            "recorded_candidate_digest": item.get("candidate_digest"),
            "recorded_transaction_digest": item.get("transaction_digest"),
            "candidate_matches": bool(point is not None
                                      and candidate_digest == item.get("candidate_digest")),
            "transaction_matches": transaction_digest == item.get("transaction_digest"),
            "pressures_match": (point is not None and item.get("common_candidate") is not None
                                and pressure_point(item.get("common_candidate")) == point),
            "written_matches": (written is not None and item.get("written_candidate") is not None
                                and dict(item["written_candidate"]) == written),
            "outcome": item.get("outcome"),
            "committed": list(item.get("committed") or []),
            "outcome_consistent": bool(item.get("committed")) == (item.get("outcome") == COMMITTED),
            # P3-46-7: the stored identities and fates have to be internally consistent with the minute
            # they belong to. The replay reads them; it does not settle anything itself.
            "provenance_settled": bool(item.get("provenance_settled")),
            "provenance_consistent": _provenance_is_consistent(item),
            # P3-53-5: the lineage is verified from the artifact alone, with no live session.
            "action_lineage": [dict(row) for row in (item.get("action_lineage") or [])],
            "lineage_links": sorted({str(dict(row).get("link") or "")
                                     for row in (item.get("action_lineage") or [])}),
            "lineage_valid": all(str(dict(row).get("link") or "") == LINK_VALID
                                 for row in (item.get("action_lineage") or []))
                             and bool(item.get("action_lineage")),
            "lineage_violations": [dict(row) for row in
                                   lineage_violations(item.get("action_lineage") or [])],
            "provenance_contradictions": [dict(row) for row in
                                          (item.get("provenance_contradictions") or [])],
            "eligibility": (dict(body.get("eligibility")).get("classification")
                            if body.get("eligibility") else None),
        })
    compared = [row for row in rows if row["recorded_candidate_digest"]]
    committed = [row for row in recorded if row.get("committed")]
    digest_matches = body.get("artifact_digest") == digest_of(
        {key: value for key, value in body.items() if key != "artifact_digest"})
    eligibility_ok, eligibility_why = eligibility_is_consistent(body)
    # P3-246A: a run under the grant also replays its overlay and its halt reason FROM THE ARTIFACT ALONE.
    overlay_replay = None
    real_run = body.get("authority_label") == REAL_PRESSURE_LABEL or claims_real_content(body)
    claims = real_artifact_problems(body) if real_run else []
    if real_run:
        try:
            import runtime_authority_pair as pair_module
            overlay_replay = pair_module.replay_overlay_artifact(body)
        except Exception as error:
            overlay_replay = {"checked": True, "reproduces": False, "mismatches": [f"{type(error).__name__}: {error}"], "established_minutes": []}
    halt_replay = halt_reason_replay(body, overlay_replay)
    return {"artifact_class": artifact_class(body), "overlay_replay": overlay_replay, "halt_reason_replay": halt_replay, "real_claims_problems": claims,
            "halt_reason_rederived": bool(halt_replay.get("rederived")),
            "minutes": rows, "compared": len(compared),
            # P3-46-7: the artifact has to carry the decision that allowed authority, and it has to
            # agree with the artifact it travels in.
            "eligibility_present": isinstance(body.get("eligibility"), Mapping),
            "eligibility_consistent": eligibility_ok,
            "eligibility_reasons": list(eligibility_why),
            "provenance_settled_minutes": sum(1 for row in rows if row["provenance_settled"]),
            "provenance_consistent_minutes": sum(1 for row in rows if row["provenance_consistent"]),
            "lineage_valid_minutes": sum(1 for row in rows if row["lineage_valid"]),
            "lineage_links": sorted({link for row in rows for link in row["lineage_links"]}),
            # P3-28 review: "reproduces: True" over 1 of 4 minutes reads as "the experiment reproduces".
            # The counts are part of the verdict now, and the verdict says what it covers.
            "minutes_recorded": len(recorded),
            "minutes_committed": len(committed),
            "minutes_reconstructable": sum(1 for row in rows if row["common_pressures"] is not None),
            "covers_every_committed_minute": bool(committed) and len(compared) == len(committed),
            "verdict": ("every committed minute reproduces"
                        if committed and len(compared) == len(committed)
                        else "no committed minute to reproduce" if not committed
                        else "some committed minute does not reproduce"),
            # P3-248: what the verdict does NOT cover, said apart from it (the verdict text is a certified contract and stays what it was)
            "verdict_notes": [note for note in (("the halt reason is recorded, not re-derived" if body.get("halted") and not halt_replay.get("rederived") else None),
                                                ("the artifact contradicts its own claims: " + "; ".join(claims) if claims else None),
                                                ("the artifact is inconsistent about being a real one" if artifact_class(body) == INCONSISTENT_ARTIFACT else None)) if note],
            # P3-19 review: a verdict that ignored the artifact's own digest called a forged artifact
            # reproducible. The digest is part of the verdict now.
            "reproduces": bool(compared) and len(compared) == len(committed) and digest_matches
                          and all(row["candidate_matches"] and row["transaction_matches"]
                                  and row["pressures_match"] and row["written_matches"]
                                  and row["outcome_consistent"] for row in compared)
                          and all(row["outcome_consistent"] for row in rows)
                          and (overlay_replay is None or bool(overlay_replay.get("reproduces"))) and bool(halt_replay["reproduces"])
                          and not claims and artifact_class(body) != INCONSISTENT_ARTIFACT,
            "artifact_digest": body.get("artifact_digest"),
            "artifact_digest_recomputes": digest_matches,
            "self_certifying": "the digest detects a change, not a determined forger: it has no "
                               "signature, so anyone holding the artifact can recompute it after "
                               "editing. A signed artifact needs a key, which is a faculty decision."}


def halt_reason_replay(body: Mapping, overlay_replay: Mapping | None = None) -> dict:
    """Whether the recorded halt reason is what the artifact's own run says (P3-246A, repaired by the P3-248 review).

    Re-derived from the artifact for the reasons that are DERIVABLE from a run: the collapse boundary (from the replayed overlay), the experiment window (the minute
    against the grant's PINNED window, never the artifact's own copy), an unsupported management class (the recorded classes against the unsupported list, wherever
    the artifact records them: the aborted minute, the committed minute or a turn that did not move the clock), a failed validation or interval and a provenance
    contradiction. A reason that is not derivable from the run (an internal error, a configuration change, a resume) is reported as ``rederived: False``: it is
    recorded, checked only against the aborted minute that carries it, and never called re-derived.

    Two checks apply to EVERY reason: the aborted minute names the SAME reason the artifact names (a relabelled halt reason does not pass), and evidence is searched
    where it lives -- a contradiction found while settling a committed minute is recorded on THAT minute, not on the fresh failure record."""
    import runtime_pressure_grant as grants
    body = dict(body or {})
    if not body.get("halted"):
        return {"applicable": False, "reproduces": True, "kind": "NOT_HALTED", "rederived": True}
    reason = str(body.get("halt_reason") or "")
    kind = reason.split(":", 1)[0].strip()
    records = [dict(record) for record in (body.get("minutes") or [])]
    quiet = [dict(record) for record in (body.get("no_advance_turns") or [])]
    failed = next((record for record in records if record.get("outcome") == ABORTED), None)
    out = {"applicable": True, "kind": kind, "minute": None, "rederived": True, "reproduces": False}
    if kind == RESUMED_WITHOUT_SITE:
        # a resume is an event of the session, not of the run: recorded, never re-derived; it needs committed minutes and no failure record
        return {**out, "rederived": False, "reproduces": bool(failed is None and any(record.get("committed") for record in records) and body.get("resumed_at_minute") is not None),
                "why": "a resume is recorded, not re-derived"}
    if failed is None:
        return {**out, "why": "no aborted minute in the artifact"}
    minute = _as_int(failed.get("minute"))
    out["minute"] = minute
    consistent = str(failed.get("failure_reason") or "") == reason
    out["recorded_reason_consistent"] = consistent
    if not consistent:
        return {**out, "why": "the aborted minute names another reason than the artifact does"}
    everywhere = [failed] + records + quiet
    if kind == COLLAPSE_BOUNDARY_REACHED:
        found = dict(failed.get("collapse_boundary") or {}).get("first_established_minute")
        established = list((overlay_replay or {}).get("established_minutes") or [])
        out["reproduces"] = bool(overlay_replay and overlay_replay.get("reproduces") and found is not None and found in established and found <= minute)
        out["first_established_minute"] = found
    elif kind == WINDOW_CLOSED:
        out["reproduces"] = bool(minute > grants.WINDOW_MINUTES)
    elif kind == UNSUPPORTED_AUTHORITY_ACTION:
        classes = bool(any(unsupported_among(list(item.get("action_kinds") or ())) or unsupported_among(list(item.get("settled_action_classes") or ())) for item in everywhere)
                       or any(item.get("unsupported_actions") for item in everywhere))
        undeclared = ("did not declare which actions ran" in reason or "clinical-time route carries no actions" in reason)
        out["reproduces"] = bool(classes or undeclared)
        if undeclared and not classes:
            out.update(rederived=False, why="an undeclared or misrouted turn is recorded, not re-derived")
    elif kind == PROVENANCE_CONTRADICTION:
        out["reproduces"] = bool(any(item.get("provenance_contradictions") for item in everywhere))
    elif kind == VALIDATION_REFUSED:
        out["reproduces"] = bool(failed.get("validation_failures") or failed.get("interval_validation"))
    elif kind == COLLAPSE_BOUNDARY_NOT_VERIFIABLE:
        boundary = dict(failed.get("collapse_boundary") or {})
        out["reproduces"] = bool(boundary.get("minutes_not_shown") or not boundary.get("clear") or not dict(failed.get("consciousness_overlay") or {}).get("available", True))
    else:
        out.update(rederived=False, reproduces=True, why="this reason is not derivable from the run (it is recorded, not re-derived)")
    return out


# -- P3-22: the GI authority battery, over the dormant logic --------------------------------------------

#: How one acceptance scenario reads when it is driven through the transaction (P3-22C).
TECHNICALLY_VALID = "TECHNICALLY_VALID"
BOUNDARY_FAILURE = "BOUNDARY_FAILURE"
REPLAY_FAILURE = "REPLAY_FAILURE"
STRUCTURAL_DIVERGENCE = "STRUCTURAL_DIVERGENCE"
NOT_ELIGIBLE = "NOT_ELIGIBLE"
OTHER_FAILURE = "OTHER"


def _battery_state(variant: str, minute: int, observable: Mapping) -> dict:
    """The smallest state the gate and the transaction need: the case, the clock and the observable.

    It is a reconstruction for a battery, not a live encounter: the live wiring is exercised by the app
    tests. What it must get right is the identity the gate derives from a state, and it does.
    """
    return {"sim_time": int(minute), "engine_family": AUTHORITY_FAMILY,
            "encounter_spec": {"variant_id": variant}, "observable": dict(observable or {})}


def _last_turn(encounter: Any, minute: int) -> dict:
    entries = [dict(entry) for entry in getattr(encounter, "entries", []) or []]
    for entry in reversed(entries):
        if _as_int(entry.get("response_time_min")) == int(minute):
            return entry
    return entries[-1] if entries else {}


def scenario_authority(variant: str, label: str, encounter: Any, snapshot: Mapping, *,
                       environ: Mapping[str, str] | None = None,
                       eligibility_row: Mapping | None = None) -> dict:
    """One acceptance scenario through the dormant transaction logic, at its last compared minute."""
    session = getattr(encounter, "shadow", None)
    runner = getattr(session, "runner", None)
    compared = sorted(runner.compared) if runner is not None else []
    row = {"case": variant, "scenario": label, "snapshot_id": str(dict(snapshot).get("id") or ""),
           "compared_minutes": list(compared),
           "eligibility": (dict(eligibility_row).get("classification") if eligibility_row else None),
           "unsupported": list(dict(eligibility_row).get("unsupported") or []) if eligibility_row else [],
           "actions": [], "transaction_valid": False, "atomic_commit": False, "replay_exact": False,
           "legacy_counterfactual": None, "failure_artifact_complete": None,
           "classification": OTHER_FAILURE, "why": ""}
    if eligibility_row is not None and str(dict(eligibility_row).get("classification")) \
            not in ELIGIBLE_CLASSES:
        row.update({"classification": NOT_ELIGIBLE,
                    "why": "; ".join(str(reason) for reason in
                                     dict(eligibility_row).get("reasons") or [])})
        return row
    if not compared:
        row.update({"classification": OTHER_FAILURE, "why": "no compared minute"})
        return row
    minute = compared[-1]
    turn = _last_turn(encounter, minute)
    observable = dict((turn.get("observation_snapshot") or {}).get("observable")
                      or getattr(encounter, "state", {}).get("observable") or {})
    ran = [dict(order) for order in (turn.get("orders") or [])]
    row["actions"] = sorted({kind for kind in action_kinds(ran)})
    site = AuthoritySite(case_id=variant, family=AUTHORITY_FAMILY, snapshot=snapshot,
                         snapshot_id=str(dict(snapshot).get("id") or ""),
                         encounter_id=f"battery:{variant}:{label}", environment="development",
                         environ=None if environ is None else dict(environ),
                         experiment_id=f"battery-{label}")
    state = _battery_state(variant, minute, observable)
    prepared = site.minute(None, state, session, ran, f"battery:{label}")
    record = dict(site.records[-1]) if site.records else {}
    row["legacy_counterfactual"] = record.get("legacy_counterfactual")
    row["transaction_valid"] = bool(record.get("validation_passed"))
    if prepared is not None:
        moved = set(record.get("moved_fields") or [])
        row.update({"atomic_commit": moved <= {"sbp", "dbp", "map"} and bool(record.get("committed")),
                    "replay_exact": record.get("replay_digest") == record.get("candidate_digest"),
                    "classification": TECHNICALLY_VALID,
                    "failure_artifact_complete": None})
        if record.get("divergence_classes"):
            row["why"] = f"divergence classes at this minute: {record['divergence_classes']}"
        return row
    reason = str(site.halt_reason or record.get("failure_reason") or "")
    rollback = dict(record.get("rollback") or {})
    row["failure_artifact_complete"] = bool(rollback) and all(
        key in rollback for key in ("failure_policy", "reason", "minute", "common_candidate",
                                    "legacy_counterfactual", "validation_failures", "parameter_snapshot",
                                    "phase2_digest", "phase3_layer_digest", "committed", "rescue"))
    if UNSUPPORTED_AUTHORITY_ACTION in reason:
        row.update({"classification": NOT_ELIGIBLE, "why": reason})
    elif NO_COMMON_CANDIDATE in reason or MINUTE_NOT_COMPARED in reason:
        row.update({"classification": BOUNDARY_FAILURE, "why": reason})
    elif "minute_reproducible" in reason:
        row.update({"classification": REPLAY_FAILURE, "why": reason})
    elif "invariants_hold" in reason or "no_core_failure" in reason or "no_unresolved_boundary" in reason:
        row.update({"classification": STRUCTURAL_DIVERGENCE, "why": reason})
    else:
        row.update({"classification": OTHER_FAILURE, "why": reason})
    return row


def authority_scenario_battery(snapshot: Mapping, *, environ: Mapping[str, str] | None = None,
                               evidence: Mapping | None = None) -> dict:
    """P3-22A/B: all 34 GI acceptance scenarios through eligibility AND the transaction logic.

    The battery is played by the repository's own acceptance harness, with the shadow on, and each
    scenario's LAST compared minute is driven through the dormant transaction with a TEST-ONLY snapshot
    the caller supplies. Nothing is excluded to improve a count.
    """
    import runtime_shadow_evidence as ev
    data = evidence if evidence is not None else ev.gi_evidence()
    rows_by_key = {(str(row["case_id"]), str(row["scenario"])): row
                   for row in eligibility_battery(data, environ=environ)["rows"]}
    rows = []
    for variant in ev.gi_variants():
        _categories, collected, _elapsed = ev._play_battery(variant, rs.MODE_SHADOW_COMPARE)
        for label, encounter, _turns in collected:
            rows.append(scenario_authority(variant, label, encounter, snapshot, environ=environ,
                                           eligibility_row=rows_by_key.get((variant, label))))
    counts: dict = {}
    for row in rows:
        counts[row["classification"]] = counts.get(row["classification"], 0) + 1
    valid = [row for row in rows if row["classification"] == TECHNICALLY_VALID]
    return {
        "rows": rows, "scenarios": len(rows), "counts": counts,
        "snapshot_id": str(dict(snapshot).get("id") or ""),
        "atomic_commits": sum(1 for row in valid if row["atomic_commit"]),
        "replay_exact": sum(1 for row in valid if row["replay_exact"]),
        "counterfactual_captured": sum(1 for row in valid
                                       if (row["legacy_counterfactual"] or {}).get("sbp") is not None),
        "failure_artifacts_complete": sorted({bool(row["failure_artifact_complete"]) for row in rows
                                              if row["failure_artifact_complete"] is not None}),
        "reading": "a scenario that is not eligible is reported as such, by name; nothing here commits "
                   "anything in production and no snapshot is approved",
    }


def candidate_matrix(candidates: Mapping[str, Mapping[str, float]], *,
                     evidence: Mapping | None = None, minutes: str = "last") -> dict:
    """P3-22C: each surviving candidate profile against every scenario's immutable artifact.

    Read-only and candidate-independent of the transaction: the profile changes the physics, so this runs
    the SAME immutable input under each candidate and classifies what the core does with it.
    """
    import runtime_shadow_evidence as ev
    import runtime_shadow_families as fam
    data = evidence if evidence is not None else ev.gi_evidence()
    out: dict = {}
    for name, values in candidates.items():
        rows = []
        for case in data["cases"]:
            for scenario in case["scenarios"]:
                artifact = scenario.get("replay_input")
                row = {"case": scenario.get("case"), "scenario": scenario.get("scenario"),
                       "classification": OTHER_FAILURE, "pressures": None, "why": ""}
                if not artifact:
                    row["why"] = "no immutable artifact for this scenario"
                    rows.append(row)
                    continue
                payload = json.loads(canonical(artifact))
                payload["scenario"] = dict(payload["scenario"])
                payload["scenario"]["profile"] = {**dict(payload["scenario"]["profile"]), **dict(values)}
                try:
                    replayed = fam.replay_shadow_encounter(payload)
                except Exception as error:
                    row.update({"classification": BOUNDARY_FAILURE,
                                "why": f"{type(error).__name__}: {error}"})
                    rows.append(row)
                    continue
                results = [item for item in replayed["results"] if _as_int(item["minute"]) >= 1]
                if not results:
                    row.update({"classification": OTHER_FAILURE, "why": "no replayed minute"})
                    rows.append(row)
                    continue
                point = pressure_point(results[-1]["derived"])
                twice = fam.replay_shadow_encounter(json.loads(canonical(payload)))
                same = [item for item in twice["results"] if _as_int(item["minute"]) >= 1]
                if digest_of(pressure_point(same[-1]["derived"])) != digest_of(point):
                    row.update({"classification": REPLAY_FAILURE, "why": "the same input replayed twice "
                                                                         "gave different pressures"})
                elif any(value is None for value in point.values()):
                    row.update({"classification": STRUCTURAL_DIVERGENCE,
                                "why": "the core produced no pressure for the last replayed minute"})
                else:
                    row.update({"classification": TECHNICALLY_VALID, "pressures": point})
                rows.append(row)
        counts: dict = {}
        for row in rows:
            counts[row["classification"]] = counts.get(row["classification"], 0) + 1
        out[name] = {"values": dict(values), "rows": rows, "counts": counts,
                     "scenarios": len(rows)}
    return out


# -- P3-23: the experiment artifact, its retention and its immutability ---------------------------------

#: What an authority experiment artifact must carry to be auditable and replayable (P3-23A).
ARTIFACT_FIELDS = ("artifact", "site", "experiment_id", "encounter_id", "case_id", "family", "domain",
                   "ownership", "environment", "snapshot_id", "snapshot", "phase2_closure_head",
                   "phase2_digest", "phase3_versions", "authority_module", "failure_policy",
                   "mode_decided_at", "attempt", "experiment_state", "invalid_for_continuation",
                   "store", "halted", "halt_reason", "mixed_trajectory", "authority_minutes",
                   "eligibility", "action_history", "minutes", "replay_input", "artifact_digest")
#: P3-246: what an artifact of a run UNDER THE GRANT also carries (the historical artifact has none of these), and what each of its minutes also carries.
REAL_PRESSURE_LABEL = "REAL_DEVELOPMENT_PRESSURE_AUTHORITY"
HISTORICAL_PRESSURE_LABEL = "HISTORICAL_PRESSURE_EXPERIMENT"
DORMANT_LABEL = "DORMANT_AUTHORITY_EVALUATION"
REAL_ARTIFACT_FIELDS = ("authority_label", "authority_mode", "grant", "excluded_domains", "consciousness_overlay", "collapse_boundary", "post_commit_policy",
                        "authority_began", "experiment_outcome")
REAL_MINUTE_FIELDS = ("grant_id", "grant_fingerprint", "authority_mode", "legacy_non_authority", "consciousness_overlay", "collapse_boundary")
#: What each minute of it must carry.
ARTIFACT_MINUTE_FIELDS = ("minute", "outcome", "committed", "replay_input",
                          "precommit_observable_digest", "input_digest", "candidate_digest",
                          "replay_digest", "transaction_digest", "written_candidate", "written_digest",
                          "legacy_shape", "common_candidate", "legacy_counterfactual", "action_kinds",
                          "action_fates", "unsupported_actions", "divergence_classes",
                          "validation_failures", "failure_reason")


#: What only a run under the development grant carries (P3-248, review M5): the content, not the label, says that an artifact claims to be a REAL one.
REAL_CONTENT_KEYS = ("grant", "consciousness_overlay", "authority_mode", "excluded_domains", "post_commit_policy")
REAL_MINUTE_CONTENT_KEYS = ("grant_id", "grant_fingerprint", "legacy_non_authority", "consciousness_overlay")
INCONSISTENT_ARTIFACT = "INCONSISTENT_ARTIFACT"


def claims_real_content(artifact: Mapping) -> bool:
    """Whether the artifact carries anything only a run under the grant carries, whatever its label says."""
    body = dict(artifact or {})
    return bool(any(key in body for key in REAL_CONTENT_KEYS)
                or any(key in dict(record) for record in (body.get("minutes") or []) for key in REAL_MINUTE_CONTENT_KEYS)
                or any("consciousness_overlay" in dict(record) for record in (body.get("no_advance_turns") or [])))


def real_artifact_problems(artifact: Mapping) -> list:
    """What a REAL artifact claims that its own records contradict, by name (P3-248 review, M4 and L6). Every one of these is re-derivable from the artifact alone:
    the derived fields, the grant it names, the boundary policy and the window against the PINNED constants, and above all that no COMMITTED minute is past the window or
    lacks a clear collapse boundary (the precommit guard is a rule of the site; the artifact has to show the rule was kept)."""
    import runtime_pressure_grant as grants
    body = dict(artifact or {})
    problems: list = []
    minutes = [dict(record) for record in (body.get("minutes") or [])]
    committed = [record for record in minutes if record.get("committed")]
    aborted = [record for record in minutes if record.get("outcome") == ABORTED]
    halted, began = bool(body.get("halted")), bool(committed)
    if list(body.get("authority_minutes") or []) != [record.get("minute") for record in committed]:
        problems.append("authority_minutes does not list the committed minutes")
    if body.get("authority_began") is not began:
        problems.append("authority_began is not what the committed minutes say")
    expected = "INVALID_FOR_CONTINUATION" if halted and began else "EXPERIMENT_HALTED" if halted else "ACTIVE"
    if body.get("experiment_outcome") != expected:
        problems.append(f"experiment_outcome {body.get('experiment_outcome')!r} is not {expected!r}")
    if bool(body.get("mixed_trajectory")) is not bool(halted and began):
        problems.append("mixed_trajectory is not (halted and committed)")
    if str(body.get("invalid_for_continuation") or "") != (INVALID_FOR_CONTINUATION if halted else ""):
        problems.append("invalid_for_continuation does not follow the halt")
    if (body.get("experiment_state") == EXPERIMENT_HALTED) is not halted:
        problems.append("experiment_state does not follow the halt")
    if halted and not (aborted or body.get("resumed_at_minute") is not None):
        problems.append("halted without any recorded failure")
    if aborted and not halted:
        problems.append("a failure is recorded but the experiment is not halted")
    if halted and aborted and str(aborted[0].get("failure_reason") or "") != str(body.get("halt_reason") or ""):
        problems.append("the first recorded failure names another reason than the halt reason")
    policy = dict(body.get("post_commit_policy") or {})
    if policy.get("silent_fallback_to_the_legacy_engine") is not False or policy.get("is_patient_death") is not False:
        problems.append("post_commit_policy claims a silent fallback or a patient death")
    if canonical(dict(body.get("grant") or {})) != canonical(grants.summary()):
        problems.append("the grant the artifact names is not the registered grant's summary")
    boundary = dict(body.get("collapse_boundary") or {})
    if canonical(dict(boundary.get("policy") or {})) != canonical(dict(grants.GRANT["collapse_boundary"])) or boundary.get("window_max_minute") != grants.WINDOW_MINUTES:
        problems.append("the collapse boundary policy or the window is not the grant's")
    for record in committed:
        at = record.get("minute")
        reading, overlay = dict(record.get("collapse_boundary") or {}), dict(record.get("consciousness_overlay") or {})
        if _as_int(at) > grants.WINDOW_MINUTES:
            problems.append(f"minute {at} was committed past the experiment window of {grants.WINDOW_MINUTES} minutes")
        if not (reading.get("clear") is True and reading.get("first_established_minute") is None and not list(reading.get("minutes_not_shown") or [])
                and overlay.get("available") is True and overlay.get("clear") is True):
            problems.append(f"minute {at} was committed without a clear collapse boundary")
    return problems


def verify_artifact(artifact: Mapping) -> dict:
    """P3-23E: whether an artifact is the one that was created, and whether it is complete.

    The digest covers every field except itself, so changing any byte of any field -- a pressure, a
    snapshot id, one minute's outcome -- makes it stop matching. There is nothing to trust here: the
    check recomputes.
    """
    body = {key: value for key, value in dict(artifact).items() if key != "artifact_digest"}
    recomputed = digest_of(body)
    missing = [name for name in ARTIFACT_FIELDS if name not in dict(artifact)]
    minute_gaps = {}
    for record in dict(artifact).get("minutes") or []:
        absent = [name for name in ARTIFACT_MINUTE_FIELDS if name not in dict(record)]
        if absent:
            minute_gaps[str(dict(record).get("minute"))] = absent
    consistent = all(bool(dict(record).get("committed")) == (dict(record).get("outcome") == COMMITTED)
                     for record in dict(artifact).get("minutes") or [])
    # P3-248 (review M5): an artifact is judged REAL by what it CONTAINS as well as by its label. Lowering or removing the label does not switch the real checks off:
    # an artifact that carries the grant, the overlay or the real minute fields and does not wear the real label is inconsistent, and so is a label with no such content.
    label_real = dict(artifact).get("authority_label") == REAL_PRESSURE_LABEL
    content_real = claims_real_content(artifact)
    real = label_real or content_real
    label_matches_content = label_real == content_real
    real_missing = [name for name in REAL_ARTIFACT_FIELDS if real and name not in dict(artifact)]
    for record in dict(artifact).get("minutes") or []:
        absent = [name for name in REAL_MINUTE_FIELDS if real and name not in dict(record)]
        if absent:
            minute_gaps[str(dict(record).get("minute"))] = sorted(set(minute_gaps.get(str(dict(record).get("minute")), [])) | set(absent))
    # a run under the grant must say so honestly: the label, the mode, the excluded domains and a consciousness overlay that claims no authority
    overlay = dict(dict(artifact).get("consciousness_overlay") or {})
    honest = (not real) or (label_real and dict(artifact).get("authority_mode") == "PRESSURE_ONLY" and list(dict(artifact).get("domain") or []) == list(AUTHORITY_DOMAIN)
                            and overlay.get("authority") is False and overlay.get("writes_mental_status") is False and overlay.get("resident_visible") is False
                            and overlay.get("written_into_the_encounter") is False)
    # P3-248 (attack 22): a run under the grant names the grant it ran under, and it must be THE registered one (identity and fingerprint), in the artifact and in every minute.
    import runtime_pressure_grant as grants
    named = dict(dict(artifact).get("grant") or {})
    registered = (not real) or (named.get("grant_id") == grants.GRANT_ID and named.get("fingerprint") == grants.GRANT_FINGERPRINT
                                and list(named.get("excluded_domains") or []) == list(grants.EXCLUDED_DOMAINS) and list(named.get("domain") or []) == list(AUTHORITY_DOMAIN)
                                and list(dict(artifact).get("excluded_domains") or []) == list(grants.EXCLUDED_DOMAINS)
                                and all(dict(record).get("grant_fingerprint") == grants.GRANT_FINGERPRINT and dict(record).get("grant_id") == grants.GRANT_ID
                                        for record in dict(artifact).get("minutes") or []))
    claims = real_artifact_problems(artifact) if real else []
    return {"digest_matches": recomputed == dict(artifact).get("artifact_digest"),
            "recomputed": recomputed, "missing_fields": missing + real_missing, "incomplete_minutes": minute_gaps,
            "outcomes_consistent": consistent, "artifact_class": artifact_class(artifact), "claims_are_honest": bool(honest), "grant_is_the_registered_one": bool(registered),
            "label_matches_content": bool(label_matches_content), "real_claims_problems": claims,
            "complete": not missing and not real_missing and not minute_gaps and consistent and bool(honest) and bool(registered) and bool(label_matches_content) and not claims}


def artifact_class(artifact: Mapping) -> str:
    """Which kind of artifact this is (P3-246B): a REAL development pressure experiment under the grant, a HISTORICAL pressure experiment (before the grant), a DORMANT
    evaluation, or an INCONSISTENT one. The kinds are never mistaken for one another: the dormant one has its own type, a real one carries the label, the grant and the
    overlay, and one that wears the real label without that content (or carries that content without the label) is INCONSISTENT -- it is never classified by its label alone
    (P3-248, review M5)."""
    body = dict(artifact or {})
    kind = str(body.get("artifact") or "")
    if kind == "phase3_authority_experiment":
        label_real = body.get("authority_label") == REAL_PRESSURE_LABEL
        content_real = claims_real_content(body)
        grant_named = isinstance(body.get("grant"), Mapping) and bool(dict(body.get("grant")).get("fingerprint"))
        if label_real and content_real and grant_named:
            return REAL_PRESSURE_LABEL
        if label_real or content_real:
            return INCONSISTENT_ARTIFACT
        return HISTORICAL_PRESSURE_LABEL
    if kind == "phase3_pair_authority_dormant" or body.get("label") == DORMANT_LABEL:
        return DORMANT_LABEL
    return "UNKNOWN_ARTIFACT"


def minimal_artifact(artifact: Mapping) -> dict:
    """P3-23D: the smallest form that still replays, with its own digest over what it keeps.

    What it drops is what repeats: the per-minute snapshot object, the per-minute version block and the
    per-minute state digest of the shadow. What it keeps is every digest a replay compares, the pressures,
    the counterfactual and the immutable replay input -- so ``replay_site_artifact`` still reproduces it.
    """
    body = {key: value for key, value in dict(artifact).items()
            if key not in ("artifact_digest", "minutes")}
    dropped = ("snapshot", "phase3_versions", "state_digest", "phase2_closure_head", "phase2_digest",
               "environment", "failure_policy", "mode_decided_at", "site", "experiment_id",
               "encounter_id", "case_id", "family", "authority_module", "submission_id")
    body["minutes"] = [{key: value for key, value in dict(record).items() if key not in dropped}
                       for record in dict(artifact).get("minutes") or []]
    body["retention"] = "minimal"
    return {**body, "artifact_digest": digest_of(body)}


def artifact_retention(artifact: Mapping) -> dict:
    """P3-23D: what each retention costs in bytes, and what the smaller one gives up."""
    full = canonical(dict(artifact))
    minimal = canonical(minimal_artifact(artifact))
    without_input = canonical({key: value for key, value in dict(artifact).items()
                               if key != "replay_input"})
    return {
        "minutes": len(dict(artifact).get("minutes") or []),
        "full_bytes": len(full.encode("utf-8")),
        "minimal_bytes": len(minimal.encode("utf-8")),
        "without_replay_input_bytes": len(without_input.encode("utf-8")),
        "replay_input_bytes": len(canonical(dict(artifact).get("replay_input") or {}).encode("utf-8")),
        "replays_without_input": False,
        "recommendation": "keep the replay input: without it the artifact describes an experiment nobody "
                          "can reproduce. The minimal form drops only what repeats minute after minute, "
                          "and it still replays.",
    }


def authority_status(store: Any) -> dict:
    """What a faculty surface must be able to read in one call: the mode, the halt and the artifact.

    The P3-19 review is right that a halt recorded in a session nobody reads is not visible. This is the
    one read a faculty page (or a future persistence step) needs; where the artifact is kept, and for how
    long, is the faculty decision P3-24 asks for, and this module does not write it anywhere.
    """
    try:
        site = store.get(SITE_KEY)
        artifact = store.get(ARTIFACT_KEY) or {}
    except Exception:
        # The P3-28 review: this branch had no ``experiment_state``, and its only consumer indexes it, so
        # an unreadable store broke the whole faculty panel instead of reporting itself.
        return {"mode": MODE_LEGACY, "authority": False, "halted": False,
                "experiment_state": EXPERIMENT_NOT_STARTED, "why": "no readable store"}
    body = dict(artifact)
    if site is None:
        # No site: either nothing was ever asked for, or the gate refused. Both are legacy, and the
        # difference matters to a faculty reader, so it is named.
        asked = str((os.environ.get(AUTHORITY_FLAG) or "")).strip().lower() \
            == MODE_LIMITED_COMMON_AUTHORITY
        return {"mode": MODE_LEGACY, "authority": False,
                "experiment_state": (EXPERIMENT_HALTED if body.get("halted")
                                     else EXPERIMENT_REFUSED if asked else EXPERIMENT_NOT_STARTED),
                "halted": bool(body.get("halted")),
                "halt_reason": str(body.get("halt_reason") or ""),
                "invalid_for_continuation": str(body.get("invalid_for_continuation") or ""),
                "case_id": body.get("case_id"), "snapshot_id": body.get("snapshot_id"),
                "domain": list(body.get("domain") or ()),
                "minute": (dict((body.get("minutes") or [{}])[-1]).get("minute")
                           if body.get("minutes") else None),
                "authority_minutes": list(body.get("authority_minutes") or ()),
                # P3-28 review: an encounter whose site is gone -- resumed, or its flag removed -- while
                # the state carries committed common pressures IS a mixed trajectory, whatever the
                # artifact said while the experiment was still running.
                "mixed_trajectory": bool(body.get("mixed_trajectory")
                                         or body.get("authority_minutes")),
                "legacy_counterfactual_available": bool(
                    body.get("minutes") and dict(body["minutes"][-1]).get("legacy_counterfactual")),
                "artifact_digest": str(body.get("artifact_digest") or ""),
                "artifact_id": str(body.get("artifact_id") or ""),
                "stored": dict(body.get("stored") or {}),
                "failure_policy": FAILURE_POLICY,
                "why": "no authority experiment in this encounter" if not body.get("halted")
                       else "a halted experiment must be read from its artifact, never continued"}
    last = dict((site.records or [{}])[-1])
    return {"mode": MODE_LIMITED_COMMON_AUTHORITY, "authority": True,
            "authority_label": (None if site.grant is None else REAL_PRESSURE_LABEL), "grant_id": (None if site.grant is None else dict(site.grant).get("grant_id")),
            "authority_mode": ("PRESSURE_ONLY" if site.grant is not None else None),
            "overlay_available": (site.overlay is not None) if site.grant is not None else None,
            "authority_began": (bool(site.minutes_committed) if site.grant is not None else None),
            "experiment_state": site.experiment_state, "halted": bool(site.halted),
            "halt_reason": site.halt_reason, "failure_policy": FAILURE_POLICY,
            "invalid_for_continuation": INVALID_FOR_CONTINUATION if site.halted else "",
            "case_id": site.case_id, "family": site.family, "attempt": site.attempt,
            "snapshot_id": site.snapshot_id, "domain": list(site.domain),
            "environment": site.environment,
            "minute": last.get("minute"), "outcome": last.get("outcome"),
            "failure_reason": str(last.get("failure_reason") or site.halt_reason or ""),
            "unsupported_actions": list(last.get("unsupported_actions") or ()),
            "authority_minutes": list(site.minutes_committed),
            "mixed_trajectory": bool(site.halted and site.minutes_committed),
            "legacy_counterfactual_available": bool(last.get("legacy_counterfactual")),
            "legacy_counterfactual": dict(last.get("legacy_counterfactual") or {}),
            "artifact_digest": str(body.get("artifact_digest") or ""),
            "artifact_id": str(body.get("artifact_id")
                               or (dict(site.stored or {}).get("artifact_id") or "")),
            "stored": dict(site.stored or {}),
            "why": "a halted experiment must be read from its artifact, never continued"
                   if site.halted else "an authority experiment is running in this encounter"}


# The registry is checked LAST, when every helper it needs exists: an import that reaches this
# line with a drifted approval raises instead of letting the application start.
_guard_the_registry()
