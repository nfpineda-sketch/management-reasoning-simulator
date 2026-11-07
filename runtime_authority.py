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
                   "layer_version")

#: Faculty-approved authority snapshots, by id. EMPTY ON PURPOSE: P3-14 may not approve a parameter, so
#: the gate's second condition can never hold and the authority mode is unreachable. A later explicit
#: faculty decision is the only thing that may add one, and ``test_runtime_authority.py`` fails if this
#: mapping stops being empty without that decision being recorded in the Decision File.
#:
#: It is exposed READ-ONLY. P3-17 found the registry was a plain module dict, so any importer could fill
#: it; ``APPROVED_SNAPSHOTS["x"] = ...`` now raises. The writable mapping below is private and a test
#: injects into it deliberately, which is a name the production scan watches.
_APPROVED_SNAPSHOT_POINTS: dict = {}
APPROVED_SNAPSHOTS: Mapping[str, Mapping[str, Any]] = MappingProxyType(_APPROVED_SNAPSHOT_POINTS)

#: What a faculty approval must carry. An id alone is not provenance: P3-17 showed that a lookup by id
#: accepted ``{}`` and even a string, and that nothing tied the approved point to the point the shadow
#: runner actually ran.
SNAPSHOT_REQUIRED_FIELDS = ("id", "parameters", "approved_by_faculty", "decision",
                            "runtime_parameter_snapshot_id")


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
    registered = APPROVED_SNAPSHOTS.get(str(snapshot.get("id") or ""))
    if registered is None:
        reasons.append("the snapshot is not in the faculty-approved registry")
    elif registered is not snapshot and dict(registered) != dict(snapshot):
        reasons.append("the snapshot differs from the registered approval of the same id")
    return (not reasons), tuple(reasons)


def approved_snapshot(snapshot_id: str | None) -> Mapping[str, Any] | None:
    """The faculty-approved snapshot of that id, or None. Today there are none at all.

    A registered entry that is not well formed is NOT returned: a malformed approval cannot open the gate.
    """
    if not snapshot_id:
        return None
    found = APPROVED_SNAPSHOTS.get(str(snapshot_id))
    if found is None or not snapshot_is_wellformed(found)[0]:
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
    """The nine conditions, evaluated together. ``granted`` is False unless every one of them holds."""

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
    """Evaluate the nine conditions of a future limited authority. Never raises; refuses by default.

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
    in_secrets = [name for name in (AUTHORITY_FLAG, SNAPSHOT_FLAG, ENVIRONMENT_FLAG)
                  if rs._named_in_secrets(name)]
    is_pilot, why_pilot = looks_like_the_pilot(environ)
    conditions = {
        "authority_flag": (str(environ.get(AUTHORITY_FLAG, "") or "").strip().lower()
                           == MODE_LIMITED_COMMON_AUTHORITY) and not in_secrets,
        "approved_snapshot": approved_snapshot(snapshot_id) is not None,
        "family_and_case": (family == AUTHORITY_FAMILY and str(case_id or "") in AUTHORITY_CASES
                            and not identity_declared_against_state),
        "environment": str(environ.get(ENVIRONMENT_FLAG, "") or "").strip().lower()
                       in ALLOWED_ENVIRONMENTS,
        "authority_domain": coherent and tuple(domain) == AUTHORITY_DOMAIN,
        "no_pilot": not is_pilot,
        "no_unsupported_action": unsupported is not None and not tuple(unsupported),
        "phase2_digest": ev.phase2_digest_now() == rs.PHASE2_DIGEST,
        "layer_version": rs.MODULE_VERSION == EXPECTED_LAYER,
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
        reasons.append("NO_FACULTY_APPROVED_AUTHORITY_SNAPSHOT_EXISTS: P3-14 may not create one, so the "
                       "authority mode is unreachable until a faculty decision approves a named point")
        if snapshot_id and APPROVED_SNAPSHOTS.get(str(snapshot_id)) is not None:
            reasons.extend(snapshot_is_wellformed(APPROVED_SNAPSHOTS[str(snapshot_id)])[1])
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
        reasons.append("the Phase-2 closure digest does not recompute")
    if not conditions["layer_version"]:
        reasons.append(f"the Phase-3 layer is {rs.MODULE_VERSION}, not {EXPECTED_LAYER}")
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
    """Why no repository configuration can activate authority today. Used by the proof test (P3-14-8)."""
    reasons = []
    if not APPROVED_SNAPSHOTS:
        reasons.append("APPROVED_SNAPSHOTS is empty: no faculty-approved authority snapshot exists")
    return tuple(reasons)


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
        self.committed = writable
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
INELIGIBLE_UNSUPPORTED = "INELIGIBLE_UNSUPPORTED_ACTION"
INELIGIBLE_OTHER = "INELIGIBLE_OTHER_REASON"

#: The GI management actions a pressure authority must be able to mirror and replay exactly. Anything else
#: the engine executes makes the encounter ineligible: it is not ignored and it is not approximated.
SUPPORTED_ACTIONS = ("fluid", "blood", "ppi", "procedure", "endoscopy", "oxygen", "reassessment",
                     "consult")
#: What the engine may report that carries no physiology and therefore never blocks eligibility.
STRUCTURAL_ACTIONS = ("reassessment", "consult", "diagnostic")


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

    Today every eligible scenario returns ``ELIGIBLE_EXCEPT_MISSING_APPROVED_SNAPSHOT``: the one condition
    nothing in this repository can satisfy is the faculty-approved snapshot, and saying so per scenario is
    the point of this reading.
    """
    environ = os.environ if environ is None else environ
    coverage = dict(scenario.get("coverage") or {})
    # A class the coverage calls fully mirrored but that is NOT in the list of actions a pressure
    # authority must be able to mirror exactly is a contradiction, not a pass: P3-17 found that
    # SUPPORTED_ACTIONS was read by nobody, so it decided nothing.
    contradictory = tuple(sorted(kind for kind, how in coverage.items()
                                 if str(how.get("status")) == "FULLY_MIRRORED"
                                 and str(kind).strip().lower() not in SUPPORTED_ACTIONS))
    unsupported = tuple(sorted(set(
        [kind for kind, how in coverage.items() if str(how.get("status")) == "UNSUPPORTED"]
        + list(contradictory))))
    declared = tuple(sorted({str(gap.get("kind")) for gap in (scenario.get("gaps") or [])
                             if gap.get("kind")}))
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
        "declared_gaps": list(declared),
        "contradictory_coverage": list(contradictory),
        "approved_snapshot": bool(APPROVED_SNAPSHOTS),
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
        if name in ("unsupported_actions", "declared_gaps", "contradictory_coverage", "family",
                    "approved_snapshot"):
            continue
        if not ok:
            reasons.append(f"{name} is false")
    if reasons:
        return AuthorityEligibility(INELIGIBLE_OTHER, case_id, scenario.get("scenario"),
                                    tuple(reasons), unsupported, facts)
    reasons.append("NO_FACULTY_APPROVED_AUTHORITY_SNAPSHOT_EXISTS: everything structural holds, and the "
                   "one remaining condition is a faculty decision")
    return AuthorityEligibility(ELIGIBLE_BUT_NO_SNAPSHOT, case_id, scenario.get("scenario"),
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
        "ineligible_unsupported": sorted({kind for row in rows for kind in row["unsupported"]}),
        "approved_snapshot_exists": bool(APPROVED_SNAPSHOTS),
        "reading": "every structurally eligible scenario still needs one thing nothing here can supply: "
                   "a faculty-approved named parameter snapshot",
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
