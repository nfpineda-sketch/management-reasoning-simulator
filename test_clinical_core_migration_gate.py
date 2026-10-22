"""Phase 2 shadow core, P2E-6: the case-parameter migration gate fails closed.

The gate maps nothing: these tests use synthetic declarations, and the GI-bleed golden, a
shadow baseline with every case parameter default_unmapped, is reported as blocked.
"""
import json

import pytest

from clinical_core import Anchors
from clinical_core import migration
from clinical_core.bands import ARRIVAL
from clinical_core.migration import (FAMILY_GATES, MigrationBlocked, check_migration_gate, gate_summary,
                                     migration_gate)
from clinical_core.state import CASE_PARAMETERS, CoreInvariantError

GI = FAMILY_GATES["gi_bleed"]
#: Synthetic case values for every case parameter (not a bank case, not calibrated).
VALUES = {"beta_blockade": 0.2, "preload_fraction": 0.4, "pump_reserve": 0.8, "intrinsic_sinus_rate": 70.0,
          "metabolic_demand_baseline": 1.1, "arrival_lactate_excess": 0.5}
FAMILY = {name: (1.0, "explicit_case") for name in GI.family_parameters}


def declared(source="explicit_case", **overrides):
    sources = {name: source for name in VALUES}
    sources.update(overrides)
    return Anchors(**{**ARRIVAL, **VALUES, "declared": sources})


def test_every_case_parameter_is_required_for_the_gi_family():
    assert GI.case_parameters == tuple(CASE_PARAMETERS) and len(GI.case_parameters) == 6
    assert set(GI.family_parameters) == {"volume_loss_ml_per_min", "hb_loss_g_dl_per_min", "fraction_with_ppi",
                                         "fraction_after_hemostasis"}


def test_a_fully_declared_case_passes():
    rows = check_migration_gate("gi_bleed", declared(), FAMILY)
    assert all(row["migratable"] for row in rows.values()) and set(rows) == set(VALUES) | set(FAMILY)


def test_the_gi_shadow_baseline_is_blocked_on_every_parameter():
    from clinical_core.legacy_adapter import anchors_from_legacy, run_legacy
    anchors = anchors_from_legacy(run_legacy("gi_bleed_57m", {}, 1).arrival)
    rows = migration_gate("gi_bleed", anchors)
    assert all(row["source"] == "default_unmapped" and not row["migratable"] for row in rows.values())
    with pytest.raises(MigrationBlocked) as blocked:
        check_migration_gate("gi_bleed", anchors)
    for name in list(VALUES) + list(GI.family_parameters):
        assert name in str(blocked.value), "every blocking parameter is named, not only the first"


@pytest.mark.parametrize("name", sorted(VALUES))
def test_one_synthetic_probe_value_blocks_the_migration(name):
    rows = migration_gate("gi_bleed", declared(**{name: "synthetic_probe"}), FAMILY)
    assert [n for n, row in rows.items() if not row["migratable"]] == [name]
    with pytest.raises(MigrationBlocked, match=name):
        check_migration_gate("gi_bleed", declared(**{name: "synthetic_probe"}), FAMILY)


def test_one_missing_family_parameter_blocks_the_migration():
    partial = dict(FAMILY)
    partial.pop("fraction_with_ppi")
    assert gate_summary("gi_bleed", declared(), partial) == {"migratable": False, "blocked": ["fraction_with_ppi"]}


def test_an_approved_default_counts_only_when_the_registry_holds_it(monkeypatch):
    claimed = declared(pump_reserve="approved_family_default")
    assert gate_summary("gi_bleed", claimed, FAMILY)["blocked"] == ["pump_reserve"], "nothing is approved yet"
    monkeypatch.setattr(migration, "APPROVED_FAMILY_DEFAULTS",
                        {"gi_bleed": {"pump_reserve": (0.8, "synthetic approval for this test")}})
    assert gate_summary("gi_bleed", claimed, FAMILY)["migratable"]
    monkeypatch.setattr(migration, "APPROVED_FAMILY_DEFAULTS",
                        {"gi_bleed": {"pump_reserve": (0.9, "synthetic approval for this test")}})
    assert gate_summary("gi_bleed", claimed, FAMILY)["blocked"] == ["pump_reserve"], "the value must match"


def test_unknown_families_parameters_and_sources_are_refused():
    with pytest.raises(MigrationBlocked, match="no migration gate"):
        migration_gate("sepsis", declared(), FAMILY)
    with pytest.raises(MigrationBlocked, match="not parameters"):
        migration_gate("gi_bleed", declared(), {**FAMILY, "lactate_gain": (1.0, "explicit_case")})
    with pytest.raises(MigrationBlocked, match="unknown source"):
        migration_gate("gi_bleed", declared(), {**FAMILY, "fraction_with_ppi": (0.8, "legacy")})
    with pytest.raises(CoreInvariantError):
        Anchors(**{**ARRIVAL, "declared": {"beta_blockade": "default_unmapped"}}), "unmapped is never declared"


def test_the_gate_reads_and_never_changes_the_case():
    anchors = declared()
    before = anchors.to_dict()
    migration_gate("gi_bleed", anchors, FAMILY)
    assert anchors.to_dict() == before


def test_the_golden_reports_every_gi_run_as_blocked():
    from clinical_core.shadow import GOLDEN
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    for scenario in golden["scenarios"].values():
        assert scenario["migration_gate"]["migratable"] is False
        assert set(scenario["migration_gate"]["blocked"]) == set(VALUES) | set(GI.family_parameters)


@pytest.mark.parametrize("entry", [(None, "explicit_case"), (float("nan"), "explicit_case"), ("lots", "explicit_case"),
                                   (True, "explicit_case"), 2.5, (2.5,), (2.5, "explicit_case", "extra")])
def test_review_f2_a_family_parameter_needs_a_finite_value_and_a_source(entry):
    with pytest.raises(MigrationBlocked):
        migration_gate("gi_bleed", declared(), {**FAMILY, "volume_loss_ml_per_min": entry})
