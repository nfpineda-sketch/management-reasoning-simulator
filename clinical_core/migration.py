"""Case-parameter migration gate (P2E-6, P2H-0): a real family moves onto the core only with verified provenance.

Three things are kept apart (P2H-0, FD-49):
1. the parameter value, read from the anchors or given for a family parameter;
2. the provenance claim: the declared source (``Anchors.declared`` or the family parameter's
   source) and, optionally, a ``ProvenanceClaim`` with references (case, family, mapping,
   approval). A claim is untrusted input;
3. the authorization authority: ``migration_authority``, which never sees the claim and
   recomputes authorization from repository case truth through a registered mapping or from
   the approved-family-default registry.

A parameter lets the family migrate only when the authority confirms its value AND the claim
is consistent with that confirmation. Which trusted source decides is the parameter's authority
policy in ``migration_authority.AUTHORITY_POLICIES`` (P2H-1), never the candidate's. A claim can
only restrict: no source label, reference, case id or family named by the candidate can
authorize a value the authority does not confirm or change which authority is selected.
The sources:
- ``explicit_case``: claims the value is case truth; it needs a confirmation from a registered
  case mapping (``migration_authority.TRUSTED_CASE_MAPPINGS``);
- ``approved_family_default``: claims an approved default; it needs a confirmation from
  ``migration_authority.APPROVED_FAMILY_DEFAULTS``;
- ``default_unmapped``, ``synthetic_probe`` (and any CANDIDATE value) never authorize.

Both registries are empty, so no parameter of any case can migrate yet. The gate maps nothing
and infers nothing. The GI-bleed golden is a shadow baseline, not a migration: it runs every
case parameter ``default_unmapped``, and the gate reports it as blocked.
"""
from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Mapping

from . import migration_authority
from .derived import DEFAULT_PROFILE, CoreProfile, case_parameter_provenance
from .state import CASE_PARAMETERS, DECLARED_SOURCES, UNMAPPED, Anchors, CoreInvariantError

#: The claims that can be authorized, and the trusted authority each one needs.
REQUIRED_AUTHORITY: Mapping[str, str] = {"explicit_case": migration_authority.CASE_MAPPING,
                                         "approved_family_default": migration_authority.FAMILY_DEFAULT_REGISTRY}
MIGRATABLE_SOURCES = frozenset(REQUIRED_AUTHORITY)


class MigrationBlocked(CoreInvariantError):
    """A family cannot migrate: a required parameter is unmapped, synthetic or unapproved."""


@dataclass(frozen=True)
class FamilyGate:
    """What a family must declare before it migrates.

    ``case_parameters`` are the core's case parameters on the family's causal paths (every one a
    mechanism reads, for every family so far; ``DIAGNOSTIC_ONLY`` ones are not required);
    ``family_parameters``
    are the family's own source and control parameters (its disease module and modulators).
    """

    family: str
    case_parameters: tuple[str, ...]
    family_parameters: tuple[str, ...]
    note: str

    def __post_init__(self):
        unknown = set(self.case_parameters) - set(CASE_PARAMETERS)
        if unknown:
            raise CoreInvariantError(f"{self.family}: unknown case parameters {sorted(unknown)}")


#: Case parameters no mechanism reads yet (P2F-1): declarable references, reported, never required.
DIAGNOSTIC_ONLY = frozenset({"reference_preload_fraction"})

FAMILY_GATES: Mapping[str, FamilyGate] = {
    "gi_bleed": FamilyGate(
        "gi_bleed", tuple(name for name in CASE_PARAMETERS if name not in DIAGNOSTIC_ONLY),
        ("volume_loss_ml_per_min", "hb_loss_g_dl_per_min", "fraction_with_ppi", "fraction_after_hemostasis"),
        "shadow baseline only: the golden runs every case parameter default_unmapped, and the haemorrhage module "
        "takes the family engine's literals (adopted for the comparison, not approved for migration)"),
}

@dataclass(frozen=True)
class ProvenanceClaim:
    """What a candidate says about one parameter's provenance. Untrusted: references only.

    Every field but ``source`` is optional. A reference given must match what the trusted
    authority confirms; one left out is not checked. Nothing here is executed or trusted.
    """

    source: str
    family: str | None = None
    case_id: str | None = None
    mapping_id: str | None = None
    mapping_version: str | None = None
    source_path: str | None = None
    approval_id: str | None = None
    approval_version: str | None = None

    def __post_init__(self):
        for item in fields(self):
            value = getattr(self, item.name)
            # Exact strings only: a subclass could compare equal to anything.
            if not (type(value) is str and value) and not (value is None and item.name != "source"):
                raise MigrationBlocked(f"a provenance claim's {item.name} is a non-empty plain string, not "
                                       f"{migration_authority.shown(value)}")


def migration_gate(family: str, anchors: Anchors, family_parameters: Mapping[str, tuple] | None = None,
                   profile: CoreProfile = DEFAULT_PROFILE,
                   claims: Mapping[str, ProvenanceClaim] | None = None) -> dict:
    """Each required parameter: value, claimed source, whether it lets the family migrate and why.

    Never raises for a known family with well-formed input. ``family_parameters`` maps a family
    parameter to (value, source) or (value, ``ProvenanceClaim``); one not given is
    ``default_unmapped``. ``claims`` adds references for case parameters; a claim's source must
    be the one the anchors declare.
    """
    gate = FAMILY_GATES.get(family)
    if gate is None:
        raise MigrationBlocked(f"family {family!r} has no migration gate: its required parameters are not declared")
    case = case_parameter_provenance(anchors, profile)
    given = dict(family_parameters or {})
    unknown = set(given) - set(gate.family_parameters)
    if unknown:
        raise MigrationBlocked(f"{family}: {sorted(unknown)} are not parameters of this family")
    claims = dict(claims or {})
    unknown = set(claims) - set(gate.case_parameters)
    if unknown:
        raise MigrationBlocked(f"{family}: claims for {sorted(unknown)}, which are not case parameters of this family")
    for name, claim in claims.items():
        if not isinstance(claim, ProvenanceClaim):
            raise MigrationBlocked(f"{family}: the claim for {name} is a ProvenanceClaim, not {migration_authority.shown(claim)}")
    authority = migration_authority.AuthoritySession(family, anchors)
    rows = {}
    # A diagnostic-only parameter is not required, but one that is declared is checked like the rest.
    checked = [*gate.case_parameters, *(name for name in DIAGNOSTIC_ONLY if name in anchors.declared)]
    for name in checked:
        declared = case[name]["source"]
        if type(declared) is not str:
            rows[name] = _refused(case[name]["value"], migration_authority.shown(declared), "the declared source is not a plain string")
            continue
        claim = claims.get(name, ProvenanceClaim(declared))
        if claim.source != declared:
            rows[name] = _refused(case[name]["value"], declared,
                                  f"the claim names {claim.source!r} but the anchors declare {declared!r}")
            continue
        rows[name] = _row(family, anchors, name, case[name]["value"], claim, authority)
    for name in gate.family_parameters:
        entry = given.get(name, (None, UNMAPPED))
        if not isinstance(entry, tuple) or len(entry) != 2:
            raise MigrationBlocked(f"{family}: {name} is declared as (value, source), not {migration_authority.shown(entry)}")
        value, claim = entry
        claim = claim if isinstance(claim, ProvenanceClaim) else ProvenanceClaim(claim) if isinstance(claim, str) \
            else None
        if claim is None:
            raise MigrationBlocked(f"{family}: {name} names its source as a string or a ProvenanceClaim")
        if claim.source != UNMAPPED and claim.source not in DECLARED_SOURCES:
            raise MigrationBlocked(f"{family}: {name} from unknown source {claim.source!r}")
        if claim.source != UNMAPPED and migration_authority.exact_number(value) is None:
            raise MigrationBlocked(f"{family}: {name} declared from {claim.source} needs an exact finite number, "
                                   f"not {migration_authority.shown(value)}")
        rows[name] = _row(family, anchors, name, value, claim, authority)
    return rows


def _refused(value, source: str, reason: str, verdict: migration_authority.Authority | None = None) -> dict:
    """``authority`` is ``None`` when the authority was not consulted, else its provenance report."""
    return {"value": value, "source": source, "migratable": False, "reason": reason,
            "authority": None if verdict is None else verdict.report()}


def _row(family: str, anchors: Anchors, name: str, value, claim: ProvenanceClaim,
         authority: migration_authority.AuthoritySession) -> dict:
    """The claim restricts; only the trusted authority's confirmation authorizes."""
    if claim.source == UNMAPPED:
        return _refused(value, claim.source, "not declared")
    if claim.source not in MIGRATABLE_SOURCES:
        return _refused(value, claim.source, f"a {claim.source} value never authorizes a migration")
    verdict = authority.authorize(name, value)
    if not verdict.authorized:
        return _refused(value, claim.source, f"no trusted source confirms {migration_authority.shown(value)}: {verdict.reason}",
                        verdict)
    if claim.family is not None and claim.family != family:
        return _refused(value, claim.source, f"the claim names family {claim.family!r}, not {family!r}", verdict)
    if claim.case_id is not None and claim.case_id != anchors.case_id:
        return _refused(value, claim.source, f"the claim names case {claim.case_id!r}, not {anchors.case_id!r}",
                        verdict)
    kind = REQUIRED_AUTHORITY[claim.source]
    matching = [item for item in verdict.confirmations if item.kind == kind]
    if claim.source == "explicit_case":
        matching = [item for item in matching
                    if claim.mapping_id in (None, item.reference) and claim.mapping_version in (None, item.version)
                    and claim.source_path in (None, *item.source_fields)]
        if claim.approval_id is not None or claim.approval_version is not None:
            matching = []
    else:
        matching = [item for item in matching
                    if claim.approval_id in (None, item.reference) and claim.approval_version in (None, item.version)]
        if claim.mapping_id is not None or claim.mapping_version is not None or claim.source_path is not None:
            matching = []
    if not matching:
        return _refused(value, claim.source, f"the claim does not match the authority the policy selects: "
                                             f"{[(item.kind, item.reference, item.version) for item in verdict.confirmations]}",
                        verdict)
    confirmed = matching[0]
    return {"value": value, "source": claim.source, "migratable": True,
            "reason": f"verified: {confirmed.kind} {confirmed.reference} v{confirmed.version} ({verdict.policy})",
            "authority": verdict.report()}


def check_migration_gate(family: str, anchors: Anchors, family_parameters: Mapping[str, tuple] | None = None,
                         profile: CoreProfile = DEFAULT_PROFILE,
                         claims: Mapping[str, ProvenanceClaim] | None = None) -> dict:
    """The gate's report when every required parameter lets the family migrate; ``MigrationBlocked`` otherwise.

    The error names every blocking parameter, not only the first.
    """
    rows = migration_gate(family, anchors, family_parameters, profile, claims)
    blocked = {name: row for name, row in rows.items() if not row["migratable"]}
    if blocked:
        detail = "; ".join(f"{name} ({row['source']}: {row['reason']})" for name, row in sorted(blocked.items()))
        raise MigrationBlocked(f"{family} cannot migrate case {migration_authority.shown(anchors.case_id)}: {detail}")
    return rows


def gate_summary(family: str, anchors: Anchors, family_parameters=None, profile: CoreProfile = DEFAULT_PROFILE,
                 claims: Mapping[str, ProvenanceClaim] | None = None) -> dict:
    """For reports: whether the case could migrate and which parameters block it."""
    rows = migration_gate(family, anchors, family_parameters, profile, claims)
    return {"migratable": all(row["migratable"] for row in rows.values()),
            "blocked": sorted(name for name, row in rows.items() if not row["migratable"])}


# P2F-11 -- GI dry run --------------------------------------------------------------------------

MAPPABLE = "A. MAPPABLE FROM EXISTING CASE TRUTH"
FAMILY_DEFAULT = "B. REQUIRES APPROVED FAMILY DEFAULT"
FACULTY = "C. REQUIRES FACULTY DECISION"
NOT_REQUIRED = "D. NOT REQUIRED FOR GI"
#: P2H-1: the authoring of the case itself is undecided, not only a value.
FACULTY_AUTHORING_DECISION_REQUIRED = "E. FACULTY AUTHORING DECISION REQUIRED"
DRY_RUN_CATEGORIES = (MAPPABLE, FAMILY_DEFAULT, FACULTY, NOT_REQUIRED, FACULTY_AUTHORING_DECISION_REQUIRED)

#: How each GI parameter could become migratable, from the repository-truth inventory
#: (gi_reference.INVENTORY). A CANDIDATE band is never a mapping: it only informs the decision.
GI_DRY_RUN: Mapping[str, tuple[str, str]] = {
    "beta_blockade": (FACULTY_AUTHORING_DECISION_REQUIRED,
                      "neither case lists a beta-blocker (clinical_cases.py:889, :918), but repository truth does not "
                      "establish that either medication/history source is complete, and absence of mention is not "
                      "evidence of 0 (P2H-0). Undecided: should GI case authoring require an explicitly complete "
                      "medication reconciliation capable of proving beta_blockade = 0, or should faculty approve a "
                      "GI-family default?"),
    "preload_fraction": (FACULTY, "POCUS places both arrivals low on the curve (clinical_cases.py:154-156); the "
                                  "position is a candidate band, not case truth"),
    "pump_reserve": (FAMILY_DEFAULT, "the case mentions no cardiac disease; no B-lines, no oedema, troponin below "
                                     "the reference: a family default 'normal reserve without such findings' needs "
                                     "approval"),
    "intrinsic_sinus_rate": (FACULTY, "no baseline HR is authored; candidate resting band 60-100 bpm"),
    "metabolic_demand_baseline": (FACULTY, "afebrile, alert, mild pain, no sepsis or seizure stated; 1 is the "
                                           "candidate (a family default for uncomplicated haemorrhage is one way to "
                                           "decide it), not case truth"),
    "arrival_lactate_excess": (FACULTY, "the authored lactate fixes the sum, not the split into baseline and excess"),
    "arrival_oxygen_debt": (FACULTY, "declared directly by faculty as part of the arrival state; no pre-arrival "
                                     "history is reconstructed, and neither case states the duration of "
                                     "hypoperfusion"),
    "arrival_delivery_ratio": (FACULTY, "declared directly by faculty as part of the arrival state; no pre-arrival "
                                        "history is reconstructed, and the case does not measure delivery"),
    "reference_preload_fraction": (NOT_REQUIRED, "no GI mechanism reads it; it only makes the volume deficit explicit"),
    "volume_loss_ml_per_min": (FAMILY_DEFAULT, "the family engine's literal, adopted for the comparison only"),
    "hb_loss_g_dl_per_min": (FAMILY_DEFAULT, "the family engine's literal, adopted for the comparison only"),
    "fraction_with_ppi": (FAMILY_DEFAULT, "family_engine.GI_BLEED['bleeding_with_ppi']"),
    "fraction_after_hemostasis": (FAMILY_DEFAULT, "family_engine.GI_BLEED['bleeding_after_hemostasis']"),
}

#: The authored arrival observation the core reads (layer A): mappable from case truth as it stands.
GI_ANCHORS_FROM_CASE_TRUTH = ("sbp", "dbp", "hr", "spo2", "respiratory_rate", "crt_s", "lactate", "hb", "glucose",
                              "consciousness_level")
#: Anchors the cases do not author themselves: the bank's default potassium (clinical_cases.py:297),
#: the rhythm the bank derives from HR (clinical_cases.py:211) and the engine's room air at the start
#: (family_engine.py:973).
GI_ANCHORS_FROM_BANK_DEFAULTS = ("k", "rhythm", "fio2")


def gate_dry_run(case: str) -> dict:
    """P2F-11: run the gate on a GI case as the shadow comparison builds it, and classify every parameter.

    It never declares the case migrated and never turns a candidate into a mapping. The
    blockers are every required parameter the gate refuses, with its category.
    """
    from .gi_reference import canonical_anchors
    anchors = canonical_anchors(case)
    rows = migration_gate("gi_bleed", anchors)
    try:
        check_migration_gate("gi_bleed", anchors)
        passes = True
    except MigrationBlocked:
        passes = False
    classified = {name: {**row, "category": GI_DRY_RUN[name][0], "path": GI_DRY_RUN[name][1]}
                  for name, row in rows.items()}
    not_required = {name: {"category": category, "path": path} for name, (category, path) in GI_DRY_RUN.items()
                    if name not in rows}
    return {"case": case, "passes_gate": passes, "parameters": classified, "not_required": not_required,
            "anchors_from_case_truth": list(GI_ANCHORS_FROM_CASE_TRUTH),
            "anchors_from_bank_defaults": list(GI_ANCHORS_FROM_BANK_DEFAULTS),
            "blockers": sorted(name for name, row in rows.items() if not row["migratable"])}
