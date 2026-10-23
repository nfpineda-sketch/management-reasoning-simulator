"""Case-parameter migration gate (P2E-6): a real family moves onto the core only fully declared.

Every parameter a family's mechanisms read is tracked with its source:
- ``explicit_case``: the case states it;
- ``approved_family_default``: the family's default, approved and recorded in
  ``APPROVED_FAMILY_DEFAULTS`` (none is, yet);
- ``default_unmapped``: not declared, so the core runs its neutral or provisional default;
- ``synthetic_probe``: a test or Level-2 probe value, never a case value.

A migration fails closed (``MigrationBlocked``) while any required parameter is
``default_unmapped`` or ``synthetic_probe``, or claims an approved default the registry does
not hold. The gate maps nothing and infers nothing: mapping a family is a separate package.
The GI-bleed golden is a shadow baseline, not a migration: it runs every case parameter
``default_unmapped``, and the gate reports it as blocked.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping

from .derived import DEFAULT_PROFILE, CoreProfile, case_parameter_provenance
from .state import CASE_PARAMETERS, DECLARED_SOURCES, UNMAPPED, Anchors, CoreInvariantError

#: The sources that let a real family migrate.
MIGRATABLE_SOURCES = frozenset({"explicit_case", "approved_family_default"})


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

#: family -> parameter -> (value, where it was approved). Empty: no family default is approved.
APPROVED_FAMILY_DEFAULTS: Mapping[str, Mapping[str, tuple[float, str]]] = {}


def migration_gate(family: str, anchors: Anchors, family_parameters: Mapping[str, tuple[float, str]] | None = None,
                   profile: CoreProfile = DEFAULT_PROFILE) -> dict:
    """Each required parameter: value, source, and whether it lets the family migrate (never raises for a known family).

    ``family_parameters`` maps a family parameter to (value, source); one not given is
    ``default_unmapped``.
    """
    gate = FAMILY_GATES.get(family)
    if gate is None:
        raise MigrationBlocked(f"family {family!r} has no migration gate: its required parameters are not declared")
    approved = APPROVED_FAMILY_DEFAULTS.get(family, {})
    case = case_parameter_provenance(anchors, profile)
    given = dict(family_parameters or {})
    unknown = set(given) - set(gate.family_parameters)
    if unknown:
        raise MigrationBlocked(f"{family}: {sorted(unknown)} are not parameters of this family")
    rows = {}
    for name in gate.case_parameters:
        rows[name] = _row(name, case[name]["value"], case[name]["source"], approved)
    for name in gate.family_parameters:
        entry = given.get(name, (None, UNMAPPED))
        if not isinstance(entry, tuple) or len(entry) != 2:
            raise MigrationBlocked(f"{family}: {name} is declared as (value, source), not {entry!r}")
        value, source = entry
        if source != UNMAPPED and source not in DECLARED_SOURCES:
            raise MigrationBlocked(f"{family}: {name} from unknown source {source!r}")
        if source != UNMAPPED and (isinstance(value, bool) or not isinstance(value, (int, float))
                                   or not math.isfinite(value)):
            raise MigrationBlocked(f"{family}: {name} declared from {source} needs a finite number, not {value!r}")
        rows[name] = _row(name, value, source, approved)
    return rows


def _row(name: str, value, source: str, approved: Mapping[str, tuple[float, str]]) -> dict:
    if source == UNMAPPED:
        return {"value": value, "source": source, "migratable": False, "reason": "not declared"}
    if source == "synthetic_probe":
        return {"value": value, "source": source, "migratable": False,
                "reason": "a synthetic probe value is not a case value"}
    if source == "approved_family_default":
        record = approved.get(name)
        if record is None or record[0] != value:
            return {"value": value, "source": source, "migratable": False,
                    "reason": "no approved family default with this value is recorded"}
        return {"value": value, "source": source, "migratable": True, "reason": f"approved: {record[1]}"}
    return {"value": value, "source": source, "migratable": source in MIGRATABLE_SOURCES, "reason": "declared"}


def check_migration_gate(family: str, anchors: Anchors,
                         family_parameters: Mapping[str, tuple[float, str]] | None = None,
                         profile: CoreProfile = DEFAULT_PROFILE) -> dict:
    """The gate's report when every required parameter lets the family migrate; ``MigrationBlocked`` otherwise.

    The error names every blocking parameter, not only the first.
    """
    rows = migration_gate(family, anchors, family_parameters, profile)
    blocked = {name: row for name, row in rows.items() if not row["migratable"]}
    if blocked:
        detail = "; ".join(f"{name} ({row['source']}: {row['reason']})" for name, row in sorted(blocked.items()))
        raise MigrationBlocked(f"{family} cannot migrate case {anchors.case_id!r}: {detail}")
    return rows


def gate_summary(family: str, anchors: Anchors, family_parameters=None, profile: CoreProfile = DEFAULT_PROFILE) -> dict:
    """For reports: whether the case could migrate and which parameters block it."""
    rows = migration_gate(family, anchors, family_parameters, profile)
    return {"migratable": all(row["migratable"] for row in rows.values()),
            "blocked": sorted(name for name, row in rows.items() if not row["migratable"])}


# P2F-11 -- GI dry run --------------------------------------------------------------------------

MAPPABLE = "A. MAPPABLE FROM EXISTING CASE TRUTH"
FAMILY_DEFAULT = "B. REQUIRES APPROVED FAMILY DEFAULT"
FACULTY = "C. REQUIRES FACULTY DECISION"
NOT_REQUIRED = "D. NOT REQUIRED FOR GI"
DRY_RUN_CATEGORIES = (MAPPABLE, FAMILY_DEFAULT, FACULTY, NOT_REQUIRED)

#: How each GI parameter could become migratable, from the repository-truth inventory
#: (gi_reference.INVENTORY). A CANDIDATE band is never a mapping: it only informs the decision.
GI_DRY_RUN: Mapping[str, tuple[str, str]] = {
    "beta_blockade": (FAMILY_DEFAULT, "neither case lists a beta-blocker (clinical_cases.py:889, :918), but neither "
                                      "states that none is taken: a bank rule 'no listed beta-blocker -> 0' needs "
                                      "approval"),
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
