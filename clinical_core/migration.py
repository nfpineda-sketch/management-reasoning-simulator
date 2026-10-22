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

    ``case_parameters`` are the core's case parameters on the family's causal paths (all of
    them for every family so far: the shared mechanisms read each one); ``family_parameters``
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


FAMILY_GATES: Mapping[str, FamilyGate] = {
    "gi_bleed": FamilyGate(
        "gi_bleed", tuple(CASE_PARAMETERS),
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
