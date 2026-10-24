"""Phase 2 shadow core, P2E-6 and P2H-0: the migration gate fails closed and no claim authorizes itself.

A parameter's value, its provenance claim and the authority that authorizes it are separate
(P2H-0, FD-49). The tests that pass a case install test-only trusted registries: synthetic
mappings and approvals for the mechanism, never a clinical value. The production registries
are empty, and the GI-bleed golden, a shadow baseline with every case parameter
default_unmapped, is reported as blocked.
"""
import ast
import inspect
import itertools
import json
import random
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

import clinical_cases
from clinical_core import Anchors, calibration, gi_reference
from clinical_core import migration_authority as authority
from clinical_core.bands import ARRIVAL
from clinical_core.decision_pack import MIDDLE
from clinical_core.migration import (FAMILY_GATES, MigrationBlocked, ProvenanceClaim, check_migration_gate,
                                     gate_dry_run, gate_summary, migration_gate)
from clinical_core.migration_authority import ApprovedDefault, CaseMapping
from clinical_core.state import CASE_PARAMETERS, CoreInvariantError

GI = FAMILY_GATES["gi_bleed"]
CASE = "gi_bleed_57m"
#: Synthetic case values for every case parameter (not a bank case's truth, not calibrated).
VALUES = {"beta_blockade": 0.2, "preload_fraction": 0.4, "pump_reserve": 0.8, "intrinsic_sinus_rate": 70.0,
          "metabolic_demand_baseline": 1.1, "arrival_lactate_excess": 0.5, "arrival_oxygen_debt": 10.0,
          "arrival_delivery_ratio": 0.9}
FAMILY = {name: (1.0, "explicit_case") for name in GI.family_parameters}
FAMILY_APPROVED = {name: (1.0, "approved_family_default") for name in GI.family_parameters}


def declared(source="explicit_case", **overrides):
    """The synthetic probe arrival (case ``band_probe``, not a repository case) with every value declared."""
    sources = {name: source for name in VALUES}
    sources.update(overrides)
    return Anchors(**{**ARRIVAL, **VALUES, "declared": sources})


def real(case=CASE, source="explicit_case", values=None, **overrides):
    """A repository case's own arrival with values declared from ``source``."""
    values = VALUES if values is None else values
    sources = {name: source for name in values}
    sources.update(overrides)
    return replace(gi_reference.canonical_anchors(case), **values, declared=sources)


def mapping(name, value, *, version="1", field="engine.family", cases=None, family="gi_bleed"):
    """A test-only registered mapping: the precondition reads a real field; the rule is a constant."""
    return CaseMapping(f"test-map:{name}", version, family, name, (field,),
                       precondition=lambda fields, field=field: fields[field] == "gi_bleed",
                       rule=lambda fields, value=value: value, requirements="test only: the case is a GI bleed",
                       cases=cases)


def approval(name, value=None, *, low=None, high=None, status="approved", family="gi_bleed", version="1"):
    return ApprovedDefault(family, name, f"test-approval:{name}", version, status, value=value, low=low, high=high)


#: Test-only trust that confirms VALUES by case mapping and the family parameters at 1.0 by approval.
FULL_TRUST = {"mappings": tuple(mapping(name, value) for name, value in VALUES.items()),
              "defaults": tuple(approval(name, 1.0) for name in GI.family_parameters)}


#: Every GI parameter the gate can check (case, family and diagnostic-only).
GI_PARAMETERS = (*GI.case_parameters, *GI.family_parameters, "reference_preload_fraction")


def policies(policy=authority.CASE_OVERRIDES_FAMILY_DEFAULT, family="gi_bleed", **overrides):
    """A test-only policy table: ``policy`` for every GI parameter unless overridden by name."""
    return tuple(authority.AuthorityPolicy(family, name, overrides.get(name, policy), "test",
                                           "test only: not a methodological decision")
                 for name in GI_PARAMETERS)


@pytest.fixture
def trust(monkeypatch):
    def install(mappings=(), defaults=(), policy_table=None):
        monkeypatch.setattr(authority, "TRUSTED_CASE_MAPPINGS", tuple(mappings))
        monkeypatch.setattr(authority, "APPROVED_FAMILY_DEFAULTS", tuple(defaults))
        monkeypatch.setattr(authority, "AUTHORITY_POLICIES", policies() if policy_table is None else tuple(policy_table))
    return install


def blocked(anchors, family_parameters=None, claims=None):
    return gate_summary("gi_bleed", anchors, family_parameters, claims=claims)["blocked"]


# The gate and its parameters ------------------------------------------------------------------

def test_every_case_parameter_a_mechanism_reads_is_required_for_the_gi_family():
    from clinical_core.migration import DIAGNOSTIC_ONLY
    assert GI.case_parameters == tuple(name for name in CASE_PARAMETERS if name not in DIAGNOSTIC_ONLY)
    assert len(GI.case_parameters) == 8 and DIAGNOSTIC_ONLY == {"reference_preload_fraction"}
    assert set(GI.family_parameters) == {"volume_loss_ml_per_min", "hb_loss_g_dl_per_min", "fraction_with_ppi",
                                         "fraction_after_hemostasis"}


def test_a_case_passes_only_when_trusted_sources_confirm_every_value(trust):
    trust(**FULL_TRUST)
    rows = check_migration_gate("gi_bleed", real(), FAMILY_APPROVED)
    assert all(row["migratable"] for row in rows.values()) and set(rows) == set(VALUES) | set(FAMILY_APPROVED)
    assert rows["beta_blockade"]["authority"] == {
        "kind": authority.CASE_MAPPING, "reference": "test-map:beta_blockade", "version": "1", "confirmed": True,
        "policy": authority.CASE_OVERRIDES_FAMILY_DEFAULT, "resolved": 0.2, "not_used": [], "conflicts": []}
    assert rows["fraction_with_ppi"]["authority"]["kind"] == authority.FAMILY_DEFAULT_REGISTRY


def test_labels_alone_never_pass_the_gate():
    """FD-49: before P2H-0 the fully declared synthetic case passed on its labels alone."""
    with pytest.raises(MigrationBlocked):
        check_migration_gate("gi_bleed", declared(), FAMILY)
    assert set(blocked(declared(), FAMILY)) == set(VALUES) | set(FAMILY)
    assert set(blocked(real(), FAMILY)) == set(VALUES) | set(FAMILY)
    assert set(blocked(real(source="approved_family_default"), FAMILY_APPROVED)) == set(VALUES) | set(FAMILY)


def test_the_gi_shadow_baseline_is_blocked_on_every_parameter():
    from clinical_core.legacy_adapter import anchors_from_legacy, run_legacy
    anchors = anchors_from_legacy(run_legacy("gi_bleed_57m", {}, 1).arrival)
    rows = migration_gate("gi_bleed", anchors)
    assert all(row["source"] == "default_unmapped" and not row["migratable"] for row in rows.values())
    with pytest.raises(MigrationBlocked) as refused:
        check_migration_gate("gi_bleed", anchors)
    for name in list(VALUES) + list(GI.family_parameters):
        assert name in str(refused.value), "every blocking parameter is named, not only the first"


@pytest.mark.parametrize("name", sorted(VALUES))
def test_one_synthetic_probe_value_blocks_the_migration(trust, name):
    trust(**FULL_TRUST)
    anchors = real(**{name: "synthetic_probe"})
    assert blocked(anchors, FAMILY_APPROVED) == [name]
    with pytest.raises(MigrationBlocked, match=name):
        check_migration_gate("gi_bleed", anchors, FAMILY_APPROVED)


def test_one_missing_family_parameter_blocks_the_migration(trust):
    trust(**FULL_TRUST)
    partial = dict(FAMILY_APPROVED)
    partial.pop("fraction_with_ppi")
    assert gate_summary("gi_bleed", real(), partial) == {"migratable": False, "blocked": ["fraction_with_ppi"]}


def test_an_approved_default_counts_only_when_the_registry_holds_it(trust):
    others = tuple(item for item in FULL_TRUST["mappings"] if item.parameter != "pump_reserve")
    claimed = real(pump_reserve="approved_family_default")
    trust(others, FULL_TRUST["defaults"])
    assert blocked(claimed, FAMILY_APPROVED) == ["pump_reserve"], "nothing approves pump_reserve"
    for record, passes in ((approval("pump_reserve", 0.8), True), (approval("pump_reserve", 0.9), False),
                           (approval("pump_reserve", low=0.7, high=0.9), True),
                           (approval("pump_reserve", low=0.85, high=0.9), False),
                           (approval("pump_reserve", 0.8, status="proposed"), False),
                           (approval("pump_reserve", 0.8, family="sepsis"), False)):
        trust(others, FULL_TRUST["defaults"] + (record,))
        assert (blocked(claimed, FAMILY_APPROVED) == []) is passes, record
    trust(others, FULL_TRUST["defaults"] + (approval("pump_reserve", 0.8),))
    claim = {"pump_reserve": ProvenanceClaim("approved_family_default", approval_id="test-approval:pump_reserve",
                                             approval_version="1")}
    assert blocked(claimed, FAMILY_APPROVED, claim) == []
    for wrong in (ProvenanceClaim("approved_family_default", approval_id="forged"),
                  ProvenanceClaim("approved_family_default", approval_version="2"),
                  ProvenanceClaim("approved_family_default", mapping_id="test-map:pump_reserve")):
        assert blocked(claimed, FAMILY_APPROVED, {"pump_reserve": wrong}) == ["pump_reserve"], wrong


def test_unknown_families_parameters_sources_and_claims_are_refused():
    with pytest.raises(MigrationBlocked, match="no migration gate"):
        migration_gate("sepsis", declared(), FAMILY)
    with pytest.raises(MigrationBlocked, match="not parameters"):
        migration_gate("gi_bleed", declared(), {**FAMILY, "lactate_gain": (1.0, "explicit_case")})
    with pytest.raises(MigrationBlocked, match="unknown source"):
        migration_gate("gi_bleed", declared(), {**FAMILY, "fraction_with_ppi": (0.8, "legacy")})
    with pytest.raises(MigrationBlocked, match="unknown source"):
        migration_gate("gi_bleed", declared(), {**FAMILY, "fraction_with_ppi": (0.8, calibration.CANDIDATE)})
    with pytest.raises(MigrationBlocked, match="not case parameters"):
        migration_gate("gi_bleed", declared(), FAMILY, claims={"volume_loss_ml_per_min": ProvenanceClaim("explicit_case")})
    with pytest.raises(MigrationBlocked, match="ProvenanceClaim"):
        migration_gate("gi_bleed", declared(), FAMILY, claims={"beta_blockade": "explicit_case"})
    for bad in ({"source": ""}, {"source": "explicit_case", "mapping_id": ""}, {"source": "explicit_case", "case_id": 7}):
        with pytest.raises(MigrationBlocked):
            ProvenanceClaim(**bad)
    with pytest.raises(CoreInvariantError):
        Anchors(**{**ARRIVAL, "declared": {"beta_blockade": "default_unmapped"}}), "unmapped is never declared"


def test_the_gate_reads_and_never_changes_the_case(trust):
    trust(**FULL_TRUST)
    anchors = real()
    before = anchors.to_dict()
    record = json.dumps(clinical_cases.FAMILIES["gi_bleed"], sort_keys=True, default=str)
    migration_gate("gi_bleed", anchors, FAMILY_APPROVED)
    assert anchors.to_dict() == before
    assert json.dumps(clinical_cases.FAMILIES["gi_bleed"], sort_keys=True, default=str) == record


def test_the_golden_reports_every_gi_run_as_blocked():
    from clinical_core.shadow import GOLDEN
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    for scenario in golden["scenarios"].values():
        assert scenario["migration_gate"]["migratable"] is False
        assert set(scenario["migration_gate"]["blocked"]) == set(VALUES) | set(GI.family_parameters)


@pytest.mark.parametrize("entry", [(None, "explicit_case"), (float("nan"), "explicit_case"), ("lots", "explicit_case"),
                                   (True, "explicit_case"), 2.5, (2.5,), (2.5, "explicit_case", "extra"), (2.5, 3)])
def test_review_f2_a_family_parameter_needs_a_finite_value_and_a_source(entry):
    with pytest.raises(MigrationBlocked):
        migration_gate("gi_bleed", declared(), {**FAMILY, "volume_loss_ml_per_min": entry})


# P2H-0: where authority lives -------------------------------------------------------------------

def test_the_authority_never_sees_a_claim():
    """Authorization is recomputed from trusted sources; the claim is not an input to it."""
    assert list(inspect.signature(authority.AuthoritySession.authorize).parameters) == ["self", "parameter", "value"]
    assert list(inspect.signature(authority.AuthoritySession.__init__).parameters) == ["self", "family", "anchors"]
    source = Path(authority.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
    assert not any(name == "migration" or name.endswith(".migration") for name in imported), imported
    # It never reads a declaration (the claim's labels) or a claim object.
    assert not [node for node in ast.walk(tree) if isinstance(node, ast.Attribute) and node.attr == "declared"]
    code = authority.AuthoritySession.authorize.__code__
    assert "ProvenanceClaim" not in source and not {"claim", "claims", "declared"} & {*code.co_varnames, *code.co_names}
    assert authority.TRUSTED_CASE_MAPPINGS == () and authority.APPROVED_FAMILY_DEFAULTS == ()


def test_provenance_records_are_typed_and_immutable():
    claim = ProvenanceClaim("explicit_case", mapping_id="m")
    record, rule = approval("pump_reserve", 0.8), mapping("pump_reserve", 0.8)
    for item, name in ((claim, "source"), (record, "value"), (rule, "rule")):
        with pytest.raises(FrozenInstanceError):
            setattr(item, name, None)
    with pytest.raises(ValueError):
        ApprovedDefault("gi_bleed", "pump_reserve", "a", "1", "approved", value=0.8, low=0.7, high=0.9)
    with pytest.raises(ValueError):
        CaseMapping("m", "1", "gi_bleed", "pump_reserve", (), lambda f: True, lambda f: 0.8, "none")


# P2H-0: spoofing probes 1-8 (each fails closed) ------------------------------------------------------

def _candidate_values(case=CASE):
    return {name: value for name, value in calibration.case_values(case, MIDDLE).items() if name in VALUES}


def test_probe_1_candidate_relabelled_explicit_case_without_case_evidence(trust):
    anchors = real(values=_candidate_values())
    rows = migration_gate("gi_bleed", anchors)
    assert not any(rows[name]["migratable"] for name in _candidate_values())
    assert all("no trusted source holds this parameter" in rows[name]["reason"] for name in _candidate_values())
    trust(FULL_TRUST["mappings"])  # trusted mappings that give other values
    rows = migration_gate("gi_bleed", anchors)
    assert all("case truth maps to" in rows[name]["reason"] for name in _candidate_values()
               if _candidate_values()[name] != VALUES[name])


def test_probe_2_candidate_relabelled_approved_default_without_registry_entry(trust):
    anchors = real(values=_candidate_values(), source="approved_family_default")
    claimed = {name: (calibration.REGISTRY["gi_" + name].midpoint, "approved_family_default")
               for name in GI.family_parameters}
    assert set(blocked(anchors, claimed)) == set(VALUES) | set(GI.family_parameters)
    trust((), tuple(approval(name, 99.0) for name in [*VALUES, *GI.family_parameters]) +
          tuple(approval(name, value, family="asthma") for name, value in _candidate_values().items()))
    assert set(blocked(anchors, claimed)) == set(VALUES) | set(GI.family_parameters)


def test_probe_3_wrong_case_id(trust):
    trust(**FULL_TRUST)
    other = replace(gi_reference.canonical_anchors("gi_bleed_72f"), case_id=CASE, **VALUES,
                    declared={name: "explicit_case" for name in VALUES})
    rows = migration_gate("gi_bleed", other, FAMILY_APPROVED)
    assert all(not row["migratable"] and "authored arrival differs" in row["reason"] for row in rows.values())
    ghost = replace(real(), case_id="gi_bleed_99x")
    assert all("not a repository case" in row["reason"] for row in migration_gate("gi_bleed", ghost).values()
               if row["source"] != "default_unmapped")
    claims = {name: ProvenanceClaim("explicit_case", case_id="gi_bleed_72f") for name in VALUES}
    assert set(blocked(real(), FAMILY_APPROVED, claims)) == set(VALUES)


def test_probe_4_wrong_family(trust):
    trust(**FULL_TRUST)
    claims = {name: ProvenanceClaim("explicit_case", family="asthma") for name in VALUES}
    assert set(blocked(real(), FAMILY_APPROVED, claims)) == set(VALUES)
    asthma = replace(real(), case_id="asthma_24f")
    assert all("in family 'asthma'" in row["reason"]
               for row in migration_gate("gi_bleed", asthma, FAMILY_APPROVED).values())
    trust(tuple(mapping(name, value, family="asthma") for name, value in VALUES.items()), FULL_TRUST["defaults"])
    assert set(blocked(real(), FAMILY_APPROVED)) == set(VALUES), "another family's mapping never applies"


def test_probe_5_source_field_that_does_not_exist(trust):
    trust((mapping("beta_blockade", 0.2, field="history.beta_blocker_list"),
           *(item for item in FULL_TRUST["mappings"] if item.parameter != "beta_blockade")), FULL_TRUST["defaults"])
    row = migration_gate("gi_bleed", real(), FAMILY_APPROVED)["beta_blockade"]
    assert not row["migratable"] and "'history.beta_blocker_list' does not exist" in row["reason"]


def _age_mapping():
    """Test-only: a rule that really reads its field (age in years as the intrinsic rate; meaningless clinically)."""
    return CaseMapping("test-map:age", "1", "gi_bleed", "intrinsic_sinus_rate", ("patient.age_years",),
                       precondition=lambda fields: isinstance(fields["patient.age_years"], int),
                       rule=lambda fields: float(fields["patient.age_years"]), requirements="test only")


def test_probe_6_registered_mapping_whose_source_value_changed(trust, monkeypatch):
    trust((_age_mapping(), *(item for item in FULL_TRUST["mappings"] if item.parameter != "intrinsic_sinus_rate")),
          FULL_TRUST["defaults"])
    anchors = real(values={**VALUES, "intrinsic_sinus_rate": 57.0})
    assert blocked(anchors, FAMILY_APPROVED) == []
    case = next(item for item in clinical_cases.FAMILIES["gi_bleed"]["variants"] if item["id"] == CASE)
    monkeypatch.setitem(case["patient"], "age_years", 58)
    row = migration_gate("gi_bleed", anchors, FAMILY_APPROVED)["intrinsic_sinus_rate"]
    assert not row["migratable"] and "case truth maps to 58.0, not 57.0" in row["reason"]


def test_probe_7_approved_default_value_differs_from_the_registry(trust):
    trust(**FULL_TRUST)
    assert set(blocked(real(), {**FAMILY_APPROVED, "fraction_with_ppi": (0.8, "approved_family_default")})) == {
        "fraction_with_ppi"}


def test_probe_8_synthetic_probe_presented_as_real_case_provenance(trust):
    trust(**FULL_TRUST)
    candidate = _candidate_values()
    probe = gi_reference.candidate_anchors(CASE, candidate)
    assert set(dict(probe.declared).values()) == {"synthetic_probe"}
    assert set(candidate) <= set(blocked(probe, FAMILY_APPROVED))
    relabelled = replace(probe, declared={name: "explicit_case" for name in candidate})
    assert set(candidate) <= set(blocked(relabelled, FAMILY_APPROVED)), "probe values relabelled are not case truth"
    assert set(blocked(declared(), FAMILY_APPROVED)) == set(VALUES) | set(FAMILY_APPROVED), (
        "the band probe is not a repository case: nothing of it is authorized")


# P2H-0: the required adversarial property ------------------------------------------------------------

SOURCES = ("explicit_case", "approved_family_default", "synthetic_probe")


def _claims(rng, ids, bare=False):
    pick = rng.choice
    if bare:
        return ProvenanceClaim(pick(SOURCES))
    return ProvenanceClaim(pick(SOURCES), family=pick([None, "gi_bleed", "asthma"]),
                           case_id=pick([None, CASE, "gi_bleed_72f", "band_probe"]),
                           mapping_id=pick([None, "forged", *ids["mappings"]]), mapping_version=pick([None, "1", "2"]),
                           source_path=pick([None, "engine.family", "history.medications", "patient.age_years"]),
                           approval_id=pick([None, "forged", *ids["approvals"]]), approval_version=pick([None, "1", "2"]))


def test_no_metadata_mutation_authorizes_an_unauthorized_candidate(trust):
    """Unauthorized: the trusted sources hold other values. Every claim and label mutation still fails.

    Every case parameter is declared (none blocks merely for being undeclared), and half the
    claims carry no reference at all, so a gate that trusted the label would be caught here.
    """
    candidate = {**_candidate_values(), "beta_blockade": 0.0, "pump_reserve": 1.0}
    assert set(candidate) == set(VALUES)
    # Trusted sources that exist (so their ids are real) but confirm other values.
    trust(tuple(mapping(name, value + 0.05) for name, value in candidate.items()),
          tuple(approval(name, value + 0.05) for name, value in candidate.items())
          + tuple(approval(name, 2.0) for name in GI.family_parameters))
    ids = {"mappings": [f"test-map:{name}" for name in candidate], "approvals": [f"test-approval:{name}" for name in
                                                                                 [*candidate, *GI.family_parameters]]}
    rng = random.Random(20261023)
    attempts = 0
    for case_id, label in itertools.product((CASE, "gi_bleed_72f", "band_probe", "asthma_24f"), SOURCES):
        for turn in range(12):
            bare = turn % 2 == 0
            claims = {name: replace(_claims(rng, ids, bare), source=label) for name in candidate}
            anchors = replace(real(values=candidate, source=label), case_id=case_id)
            family = {name: (1.0, _claims(rng, ids, bare)) for name in GI.family_parameters}
            with pytest.raises(MigrationBlocked):
                check_migration_gate("gi_bleed", anchors, family, claims=claims)
            rows = migration_gate("gi_bleed", anchors, family, claims=claims)
            assert not any(row["migratable"] for row in rows.values())
            assert not any(rows[name]["reason"] == "not declared" for name in candidate)
            attempts += 1
    assert attempts == 144


def test_a_migratable_row_always_has_an_independent_confirmation(trust):
    """Whatever the claims, migratable implies the authority (which never sees them) confirms the value."""
    trust(**FULL_TRUST)
    ids = {"mappings": [item.mapping_id for item in FULL_TRUST["mappings"]],
           "approvals": [item.approval_id for item in FULL_TRUST["defaults"]]}
    rng = random.Random(7)
    checked = 0
    for turn in range(60):
        label = rng.choice(SOURCES)
        anchors = real(source=label)
        bare = turn % 2 == 0
        claims = {name: replace(_claims(rng, ids, bare), source=label) for name in VALUES}
        rows = migration_gate("gi_bleed", anchors,
                              {name: (1.0, _claims(rng, ids, bare)) for name in GI.family_parameters}, claims=claims)
        session = authority.AuthoritySession("gi_bleed", anchors)
        for name, row in rows.items():
            if row["migratable"]:
                assert session.authorize(name, row["value"]).authorized
                checked += 1
    assert checked > 0, "the property was exercised on migratable rows"


def test_only_a_trusted_source_changes_authorization(trust, monkeypatch):
    anchors = real(values={**VALUES, "intrinsic_sinus_rate": 57.0})
    assert "intrinsic_sinus_rate" in blocked(anchors, FAMILY_APPROVED)
    trust((_age_mapping(), *(item for item in FULL_TRUST["mappings"] if item.parameter != "intrinsic_sinus_rate")),
          FULL_TRUST["defaults"])
    assert blocked(anchors, FAMILY_APPROVED) == [], "a trusted mapping that confirms the value authorizes it"
    case = next(item for item in clinical_cases.FAMILIES["gi_bleed"]["variants"] if item["id"] == CASE)
    monkeypatch.setitem(case["patient"], "age_years", 60)
    assert blocked(anchors, FAMILY_APPROVED) == ["intrinsic_sinus_rate"], "changed case truth withdraws it"


def test_review_n6_relabelling_every_candidate_explicit_case_no_longer_passes():
    """The P2G review's bypass: every CANDIDATE and family parameter relabelled explicit_case."""
    values = calibration.case_values(CASE, MIDDLE)
    anchors = gi_reference.candidate_anchors(CASE, {**values, "beta_blockade": 0.0, "pump_reserve": 1.0})
    relabelled = replace(anchors, declared={name: "explicit_case" for name in anchors.declared})
    family = {name: (calibration.REGISTRY["gi_" + name].midpoint, "explicit_case") for name in GI.family_parameters}
    with pytest.raises(MigrationBlocked):
        check_migration_gate("gi_bleed", relabelled, family)


@pytest.mark.parametrize("case", gi_reference.GI_CASES)
def test_gi_still_fails_and_nothing_is_approved(case):
    result = gate_dry_run(case)
    assert result["passes_gate"] is False and len(result["blockers"]) == 12
    assert sum(entry.status == calibration.FACULTY_APPROVED for entry in calibration.REGISTRY.values()) == 0
    assert authority.APPROVED_FAMILY_DEFAULTS == () and authority.TRUSTED_CASE_MAPPINGS == ()


# P2H-0: the second-review findings, each closed ------------------------------------------------------

class LyingFloat(float):
    """Reports another number through __float__ and compares equal to anything."""

    def __float__(self):
        return 0.2

    def __eq__(self, other):
        return True

    def __ne__(self, other):
        return False

    __hash__ = float.__hash__


class LookalikeStr(str):
    def __eq__(self, other):
        return True

    def __ne__(self, other):
        return False

    __hash__ = str.__hash__


def _without(name):
    return tuple(item for item in FULL_TRUST["mappings"] if item.parameter != name)


def test_review_f1_only_exact_numbers_are_authorized(trust):
    trust(**FULL_TRUST)
    lying = real(values={**VALUES, "beta_blockade": LyingFloat(0.9)})
    assert "beta_blockade" in blocked(lying, FAMILY_APPROVED)
    assert "not an exact finite int or float" in migration_gate("gi_bleed", lying, FAMILY_APPROVED)[
        "beta_blockade"]["reason"]
    for value in (LyingFloat(1.0), True, 10 ** 400, float("nan"), "1.0"):
        with pytest.raises(MigrationBlocked, match="exact finite number"):
            migration_gate("gi_bleed", real(), {**FAMILY_APPROVED, "fraction_with_ppi": (value, "approved_family_default")})


def test_review_f2_the_arrival_is_compared_in_exact_canonical_form(trust):
    trust(**FULL_TRUST)
    forged = replace(real(), sbp=LyingFloat(200.0), hr=LyingFloat(150.0))
    verification = authority.verify_case("gi_bleed", forged)
    assert not verification.verified and "exact builtin type" in verification.reason
    assert set(blocked(forged, FAMILY_APPROVED)) == set(VALUES) | set(FAMILY_APPROVED)


def test_review_f3_the_case_id_is_the_bank_s_and_exact(trust):
    trust(**FULL_TRUST)
    lookalike = replace(real(), case_id=LookalikeStr("gi_bleed_72f"))
    verification = authority.verify_case("gi_bleed", lookalike)
    assert not verification.verified and "not a repository case id" in verification.reason
    good = authority.verify_case("gi_bleed", real())
    assert good.verified and type(good.case_id) is str and good.case_id == CASE
    trust((*_without("beta_blockade"), mapping("beta_blockade", 0.2, cases=("gi_bleed_72f",))), FULL_TRUST["defaults"])
    assert blocked(real(), FAMILY_APPROVED) == ["beta_blockade"], "a mapping limited to another case never applies"


def test_review_f4_a_precondition_or_rule_that_does_not_hold_fails_closed(trust):
    def with_rule(precondition, rule):
        return CaseMapping("test-map:beta", "1", "gi_bleed", "beta_blockade", ("engine.family",), precondition, rule,
                           "test only")
    for precondition, rule, phrase in (
            (lambda f: False, lambda f: 0.2, "does not meet its precondition"),
            (lambda f: 1, lambda f: 0.2, "does not meet its precondition"),
            (lambda f: "yes", lambda f: 0.2, "does not meet its precondition"),
            (lambda f: f["missing"], lambda f: 0.2, "the precondition failed"),
            (lambda f: True, lambda f: True, "no exact finite number"),
            (lambda f: True, lambda f: float("nan"), "no exact finite number"),
            (lambda f: True, lambda f: f["missing"], "the rule failed")):
        trust((*_without("beta_blockade"), with_rule(precondition, rule)), FULL_TRUST["defaults"])
        row = migration_gate("gi_bleed", real(), FAMILY_APPROVED)["beta_blockade"]
        explained = row["reason"] + " ".join(row["authority"]["not_used"])
        assert not row["migratable"] and phrase in explained, (phrase, row)


def test_review_f5_case_mappings_that_disagree_or_a_doubled_default_fail_closed(trust):
    # Two mappings that disagree on the case truth: neither value passes, whatever the policy.
    trust((*_without("beta_blockade"), mapping("beta_blockade", 0.2),
           replace(mapping("beta_blockade", 0.7), mapping_id="test-map:beta_blockade/2")), FULL_TRUST["defaults"])
    row = migration_gate("gi_bleed", real(), FAMILY_APPROVED)["beta_blockade"]
    assert not row["migratable"] and "disagree" in row["reason"] and row["authority"]["conflicts"]
    # Two approved defaults for one parameter are a registry inconsistency.
    trust(FULL_TRUST["mappings"], FULL_TRUST["defaults"] + (replace(approval("fraction_with_ppi", 1.0),
                                                                    approval_id="test-approval:ppi/2"),))
    assert blocked(real(), FAMILY_APPROVED) == ["fraction_with_ppi"]


def test_review_f6_a_declared_diagnostic_only_parameter_must_be_authorized(trust):
    trust(**FULL_TRUST)
    anchors = replace(real(), reference_preload_fraction=0.37,
                      declared={**dict(real().declared), "reference_preload_fraction": "synthetic_probe"})
    assert blocked(anchors, FAMILY_APPROVED) == ["reference_preload_fraction"]
    trust((*FULL_TRUST["mappings"], mapping("reference_preload_fraction", 0.37)), FULL_TRUST["defaults"])
    confirmed = replace(anchors, declared={**dict(anchors.declared), "reference_preload_fraction": "explicit_case"})
    assert blocked(confirmed, FAMILY_APPROVED) == []
    assert blocked(real(), FAMILY_APPROVED) == [], "an undeclared diagnostic-only parameter is not required"


def test_review_f7_a_changed_case_truth_is_never_served_from_a_stale_arrival(trust, monkeypatch):
    trust(**FULL_TRUST)
    anchors = real()
    assert blocked(anchors, FAMILY_APPROVED) == []
    case = next(item for item in clinical_cases.FAMILIES["gi_bleed"]["variants"] if item["id"] == CASE)
    monkeypatch.setitem(case["observable"], "sbp", 90)
    assert set(blocked(anchors, FAMILY_APPROVED)) == set(VALUES) | set(FAMILY_APPROVED)
    monkeypatch.setitem(case["observable"], "sbp", 88)
    assert blocked(anchors, FAMILY_APPROVED) == []


@pytest.mark.parametrize("numbers", [{"value": True}, {"value": float("nan")}, {"value": "0.8"},
                                     {"low": float("-inf"), "high": float("inf")}, {"low": 0.9, "high": 0.1},
                                     {"value": LyingFloat(0.8)}, {"value": 0.8, "low": 0.1, "high": 0.9}, {}])
def test_review_f8_an_approved_default_holds_exact_finite_numbers(numbers):
    with pytest.raises(ValueError):
        ApprovedDefault("gi_bleed", "pump_reserve", "a", "1", "approved", **numbers)


def test_review_f9_labels_and_claims_are_plain_strings(trust):
    trust(**FULL_TRUST)
    for field in ("source", "mapping_id", "case_id"):
        with pytest.raises(MigrationBlocked, match="plain string"):
            ProvenanceClaim(**{"source": "explicit_case", field: LookalikeStr("explicit_case")})
    odd = real(**{"beta_blockade": LookalikeStr("explicit_case")})
    assert blocked(odd, FAMILY_APPROVED) == ["beta_blockade"]


# P2H-1: authority precedence (verified case truth > approved family default > fail closed) -------------

def _conflicting(policy, *, case=0.2, default=0.6, name="pump_reserve"):
    """Trust in which the case mapping and the approved default disagree on one case parameter."""
    others = tuple(item for item in FULL_TRUST["mappings"] if item.parameter != name)
    return {"mappings": (*others, mapping(name, case)),
            "defaults": (*FULL_TRUST["defaults"], approval(name, default)),
            "policy_table": policies(**{name: policy})}


def _with(name, value, source="explicit_case"):
    return real(values={**VALUES, name: value}, **{name: source})


def test_p2h1_1_verified_case_truth_overrides_a_conflicting_default(trust):
    trust(**_conflicting(authority.CASE_OVERRIDES_FAMILY_DEFAULT))
    rows = check_migration_gate("gi_bleed", _with("pump_reserve", 0.2), FAMILY_APPROVED)
    row = rows["pump_reserve"]
    assert row["migratable"] and row["authority"]["kind"] == authority.CASE_MAPPING
    assert row["authority"]["reference"] == "test-map:pump_reserve" and row["authority"]["resolved"] == 0.2
    assert any("test-approval:pump_reserve" in note and "not used" in note for note in row["authority"]["not_used"])
    assert len(row["authority"]["conflicts"]) == 1 and "resolved by precedence" in row["authority"]["conflicts"][0], \
        "a conflict that precedence resolves is still recorded"


def test_p2h1_2_the_family_default_is_used_when_no_case_mapping_applies(trust):
    others = tuple(item for item in FULL_TRUST["mappings"] if item.parameter != "pump_reserve")
    for missing in ((), (mapping("pump_reserve", 0.2, cases=("gi_bleed_72f",)),)):
        trust((*others, *missing), (*FULL_TRUST["defaults"], approval("pump_reserve", low=0.5, high=0.9)))
        row = check_migration_gate("gi_bleed", _with("pump_reserve", 0.6, "approved_family_default"),
                                   FAMILY_APPROVED)["pump_reserve"]
        assert row["migratable"] and row["authority"]["kind"] == authority.FAMILY_DEFAULT_REGISTRY
        assert row["authority"]["reference"] == "test-approval:pump_reserve"
        assert row["authority"]["resolved"] == [0.5, 0.9] and row["authority"]["conflicts"] == []
        assert bool(missing) == any("does not apply" in note for note in row["authority"]["not_used"])


def test_p2h1_3_family_fixed_rejects_a_conflicting_case_override(trust):
    trust(**_conflicting(authority.FAMILY_FIXED))
    for value, source in ((0.2, "explicit_case"), (0.6, "approved_family_default"), (0.6, "explicit_case")):
        row = migration_gate("gi_bleed", _with("pump_reserve", value, source), FAMILY_APPROVED)["pump_reserve"]
        assert not row["migratable"] and "case override is not permitted" in row["reason"], (value, source)
        assert row["authority"]["policy"] == authority.FAMILY_FIXED and row["authority"]["conflicts"]
    # When the case agrees, the family value is authoritative and the case is recorded as not used.
    trust(**_conflicting(authority.FAMILY_FIXED, case=0.6))
    row = check_migration_gate("gi_bleed", _with("pump_reserve", 0.6, "approved_family_default"),
                               FAMILY_APPROVED)["pump_reserve"]
    assert row["authority"]["kind"] == authority.FAMILY_DEFAULT_REGISTRY
    assert any("family value is authoritative" in note for note in row["authority"]["not_used"])
    assert blocked(_with("pump_reserve", 0.6), FAMILY_APPROVED) == ["pump_reserve"], \
        "a case claim cannot select a FAMILY_FIXED parameter's authority"


def test_p2h1_4_case_required_rejects_the_family_default_fallback(trust):
    others = tuple(item for item in FULL_TRUST["mappings"] if item.parameter != "pump_reserve")
    trust(others, (*FULL_TRUST["defaults"], approval("pump_reserve", 0.6)),
          policies(pump_reserve=authority.CASE_REQUIRED))
    for source in ("approved_family_default", "explicit_case"):
        row = migration_gate("gi_bleed", _with("pump_reserve", 0.6, source), FAMILY_APPROVED)["pump_reserve"]
        assert not row["migratable"] and "CASE_REQUIRED" in row["reason"], source
        assert any("not a permitted fallback" in note for note in row["authority"]["not_used"])
    # With verified case truth the parameter passes, and the default is reported as not used.
    trust(**_conflicting(authority.CASE_REQUIRED))
    row = check_migration_gate("gi_bleed", _with("pump_reserve", 0.2), FAMILY_APPROVED)["pump_reserve"]
    assert row["authority"]["kind"] == authority.CASE_MAPPING and row["authority"]["conflicts"]


@pytest.mark.parametrize("policy", authority.POLICIES)
def test_p2h1_5_candidate_metadata_cannot_change_the_policy(trust, policy):
    # The candidate has no place to carry a policy: not in a claim, its labels or a family entry.
    with pytest.raises(TypeError):
        ProvenanceClaim(source="explicit_case", policy=authority.CASE_OVERRIDES_FAMILY_DEFAULT)
    with pytest.raises(CoreInvariantError):
        replace(real(), declared={**dict(real().declared), "policy": authority.FAMILY_FIXED})
    trust(**_conflicting(policy))
    entry = {**FAMILY_APPROVED, "fraction_with_ppi": (1.0, "approved_family_default", authority.FAMILY_FIXED)}
    with pytest.raises(MigrationBlocked):
        migration_gate("gi_bleed", real(), entry)
    expected = migration_gate("gi_bleed", _with("pump_reserve", 0.2), FAMILY_APPROVED)["pump_reserve"]
    rng = random.Random(1049)
    for _ in range(60):
        claims = {"pump_reserve": _claims(rng, {"mappings": ["test-map:pump_reserve"],
                                                "approvals": ["test-approval:pump_reserve"]})}
        anchors = _with("pump_reserve", rng.choice((0.2, 0.6)), rng.choice(SOURCES))
        row = migration_gate("gi_bleed", anchors, FAMILY_APPROVED, claims=claims)["pump_reserve"]
        if row["authority"] is not None:
            assert row["authority"]["policy"] == policy
            assert row["authority"]["resolved"] == expected["authority"]["resolved"]
            assert row["authority"]["conflicts"] == expected["authority"]["conflicts"]


def test_p2h1_6_claimed_precedence_cannot_change_authorization(trust):
    trust(**_conflicting(authority.CASE_OVERRIDES_FAMILY_DEFAULT))
    # The candidate claims the default should win: the policy still selects the verified case truth.
    for value in (0.6, 0.2):
        anchors = _with("pump_reserve", value, "approved_family_default")
        claims = {"pump_reserve": ProvenanceClaim(source="approved_family_default",
                                                  approval_id="test-approval:pump_reserve", approval_version="1")}
        row = migration_gate("gi_bleed", anchors, FAMILY_APPROVED, claims=claims)["pump_reserve"]
        assert not row["migratable"] and row["authority"]["resolved"] == 0.2, value
    # A claim naming the case mapping cannot authorize a value the selected authority does not hold.
    claims = {"pump_reserve": ProvenanceClaim(source="explicit_case", mapping_id="test-map:pump_reserve")}
    assert blocked(_with("pump_reserve", 0.6), FAMILY_APPROVED, claims) == ["pump_reserve"]
    assert blocked(_with("pump_reserve", 0.2), FAMILY_APPROVED, claims) == []


def test_p2h1_7_an_undeclared_or_doubled_policy_fails_closed(trust):
    table = tuple(item for item in policies() if item.parameter != "pump_reserve")
    trust(FULL_TRUST["mappings"], FULL_TRUST["defaults"], table)
    row = migration_gate("gi_bleed", real(), FAMILY_APPROVED)["pump_reserve"]
    assert not row["migratable"] and "no authority policy is declared for gi_bleed/pump_reserve" in row["reason"]
    assert blocked(real(), FAMILY_APPROVED) == ["pump_reserve"]
    trust(FULL_TRUST["mappings"], FULL_TRUST["defaults"],
          (*policies(), authority.AuthorityPolicy("gi_bleed", "pump_reserve", authority.CASE_REQUIRED, "2", "test")))
    assert blocked(real(), FAMILY_APPROVED) == ["pump_reserve"]
    trust(FULL_TRUST["mappings"], FULL_TRUST["defaults"], policies(family="another_family"))
    assert set(blocked(real(), FAMILY_APPROVED)) == set(VALUES) | set(FAMILY_APPROVED)
    for bad in ("case_overrides_family_default", "", None, "UNANIMOUS"):
        with pytest.raises(ValueError):
            authority.AuthorityPolicy("gi_bleed", "pump_reserve", bad, "1", "test")


def test_p2h1_production_declares_no_policy_so_every_gi_parameter_fails_closed():
    assert authority.AUTHORITY_POLICIES == ()
    for name in GI_PARAMETERS:
        assert authority.policy_for("gi_bleed", name) == (None, f"no authority policy is declared for gi_bleed/{name}")


def test_p2h1_8_provenance_reports_the_authority_that_won(trust):
    trust(**_conflicting(authority.CASE_OVERRIDES_FAMILY_DEFAULT))
    rows = check_migration_gate("gi_bleed", _with("pump_reserve", 0.2), FAMILY_APPROVED)
    case_row, default_row = rows["pump_reserve"], rows["fraction_with_ppi"]
    assert case_row["reason"] == f"verified: {authority.CASE_MAPPING} test-map:pump_reserve v1 " \
                                 f"({authority.CASE_OVERRIDES_FAMILY_DEFAULT})"
    assert set(case_row["authority"]) == {"kind", "reference", "version", "confirmed", "policy", "resolved",
                                          "not_used", "conflicts"}
    assert (case_row["authority"]["kind"], case_row["authority"]["reference"], case_row["authority"]["version"],
            case_row["authority"]["policy"], case_row["authority"]["resolved"]) == (
        authority.CASE_MAPPING, "test-map:pump_reserve", "1", authority.CASE_OVERRIDES_FAMILY_DEFAULT, 0.2)
    assert len(case_row["authority"]["not_used"]) == 1
    assert case_row["authority"]["not_used"][0].startswith("test-approval:pump_reserve v1 holds 0.6: not used")
    assert (default_row["authority"]["kind"], default_row["authority"]["reference"],
            default_row["authority"]["resolved"], default_row["authority"]["not_used"]) == (
        authority.FAMILY_DEFAULT_REGISTRY, "test-approval:fraction_with_ppi", 1.0, [])
    # A refusal still reports which authority the policy selected, what it resolves and that it does not hold.
    refused = migration_gate("gi_bleed", _with("pump_reserve", 0.6), FAMILY_APPROVED)["pump_reserve"]
    assert (refused["authority"]["kind"], refused["authority"]["reference"], refused["authority"]["confirmed"],
            refused["authority"]["resolved"]) == (authority.CASE_MAPPING, "test-map:pump_reserve", False, 0.2)
    assert "case truth maps to 0.2, not 0.6" in refused["reason"]
    # A refusal by the claim, after the selected authority confirmed: confirmed, not migratable.
    claims = {"pump_reserve": ProvenanceClaim(source="explicit_case", family="asthma")}
    row = migration_gate("gi_bleed", _with("pump_reserve", 0.2), FAMILY_APPROVED, claims=claims)["pump_reserve"]
    assert not row["migratable"] and row["authority"]["confirmed"]
    assert row["authority"]["reference"] == "test-map:pump_reserve"


# P2H-1 adversarial review: precedence edges, digest, candidate objects, report --------------------

def _trust_one(policy, *, maps=(), defaults=(), name="pump_reserve"):
    """FULL_TRUST with ``name`` held only by ``maps`` and ``defaults`` under ``policy``."""
    return {"mappings": (*(item for item in FULL_TRUST["mappings"] if item.parameter != name), *maps),
            "defaults": (*FULL_TRUST["defaults"], *defaults), "policy_table": policies(**{name: policy})}


def _pump(trust, value, source="explicit_case", **kwargs):
    trust(**_trust_one(**kwargs))
    return migration_gate("gi_bleed", _with("pump_reserve", value, source), FAMILY_APPROVED)["pump_reserve"]


def test_review_m1_family_fixed_never_falls_back_to_case_truth(trust):
    row = _pump(trust, 0.8, policy=authority.FAMILY_FIXED, maps=(mapping("pump_reserve", 0.8),))
    assert not row["migratable"] and "no approved family default" in row["reason"]
    assert any("cannot decide a FAMILY_FIXED parameter" in note for note in row["authority"]["not_used"])


def test_review_m2_case_required_has_no_fallback_when_the_mapping_does_not_apply(trust):
    elsewhere = mapping("pump_reserve", 0.8, cases=("gi_bleed_72f",))
    unmet = CaseMapping("test-map:pump_reserve", "1", "gi_bleed", "pump_reserve", ("engine.family",),
                        lambda fields: False, lambda fields: 0.8, "test only")
    for maps in ((elsewhere,), (unmet,)):
        for source in ("approved_family_default", "explicit_case"):
            row = _pump(trust, 0.8, source, policy=authority.CASE_REQUIRED, maps=maps,
                        defaults=(approval("pump_reserve", 0.8),))
            assert not row["migratable"] and "CASE_REQUIRED" in row["reason"], (maps, source)


def test_review_m3_duplicate_approved_defaults_block_even_when_case_truth_would_win(trust):
    doubled = (approval("pump_reserve", 0.8), replace(approval("pump_reserve", 0.8), approval_id="dup"))
    for policy in authority.POLICIES:
        row = _pump(trust, 0.8, policy=policy, maps=(mapping("pump_reserve", 0.8),), defaults=doubled)
        assert not row["migratable"] and "2 approved family defaults" in row["reason"], policy


def test_review_m4_m7_a_range_default_differs_when_case_truth_is_outside_it(trust):
    outside = {"maps": (mapping("pump_reserve", 0.95),), "defaults": (approval("pump_reserve", low=0.5, high=0.9),)}
    row = _pump(trust, 0.6, "approved_family_default", policy=authority.FAMILY_FIXED, **outside)
    assert not row["migratable"] and "case override is not permitted" in row["reason"]
    row = _pump(trust, 0.95, policy=authority.CASE_OVERRIDES_FAMILY_DEFAULT, **outside)
    assert row["migratable"] and len(row["authority"]["conflicts"]) == 1
    assert "resolved by precedence" in row["authority"]["conflicts"][0]
    row = _pump(trust, 0.95, policy=authority.CASE_REQUIRED, **outside)
    assert row["migratable"] and len(row["authority"]["conflicts"]) == 1


def test_review_m5_a_mapping_whose_precondition_is_unmet_lets_the_default_decide(trust):
    unmet = CaseMapping("test-map:pump_reserve", "1", "gi_bleed", "pump_reserve", ("engine.family",),
                        lambda fields: False, lambda fields: 0.2, "test only: a complete cardiac history")
    row = _pump(trust, 0.8, "approved_family_default", policy=authority.CASE_OVERRIDES_FAMILY_DEFAULT,
                maps=(unmet,), defaults=(approval("pump_reserve", 0.8),))
    assert row["migratable"] and row["authority"]["kind"] == authority.FAMILY_DEFAULT_REGISTRY
    assert any("does not meet its precondition" in note for note in row["authority"]["not_used"])


def test_review_m6_an_approved_range_is_inclusive(trust):
    for value, passes in ((0.5, True), (0.9, True), (0.7, True), (0.4999, False), (0.9001, False)):
        row = _pump(trust, value, "approved_family_default", policy=authority.CASE_OVERRIDES_FAMILY_DEFAULT,
                    defaults=(approval("pump_reserve", low=0.5, high=0.9),))
        assert row["migratable"] is passes, value


def test_review_f3_family_fixed_records_a_value_that_differs_from_agreeing_case_truth(trust):
    # Decision pending (FD-50): the family range decides, and the difference is never silent.
    inside = {"maps": (mapping("pump_reserve", 0.6),), "defaults": (approval("pump_reserve", low=0.5, high=0.9),)}
    row = _pump(trust, 0.9, "approved_family_default", policy=authority.FAMILY_FIXED, **inside)
    assert row["migratable"] and len(row["authority"]["conflicts"]) == 1
    assert "differs from verified case truth" in row["authority"]["conflicts"][0]
    row = _pump(trust, 0.6, "approved_family_default", policy=authority.FAMILY_FIXED, **inside)
    assert row["migratable"] and row["authority"]["conflicts"] == []


def test_review_f4_an_int_the_float_cannot_hold_exactly_is_refused(trust):
    assert authority.exact_number(2 ** 53 + 1) is None and authority.exact_number(2 ** 53) == 2.0 ** 53
    name = "arrival_oxygen_debt"
    trust(**_trust_one(authority.CASE_OVERRIDES_FAMILY_DEFAULT, maps=(mapping(name, 2.0 ** 53),), name=name))
    assert blocked(real(values={**VALUES, name: 2 ** 53 + 1}), FAMILY_APPROVED) == [name]
    assert blocked(real(values={**VALUES, name: 2 ** 53}), FAMILY_APPROVED) == []
    with pytest.raises(MigrationBlocked, match="exact finite number"):
        migration_gate("gi_bleed", real(), {**FAMILY_APPROVED, "fraction_with_ppi": (2 ** 53 + 1, "explicit_case")})


class RaisingFloat(float):
    def __repr__(self):
        raise RuntimeError("candidate code ran")

    __str__ = __format__ = __repr__


class LyingRepr(float):
    def __repr__(self):
        return "0.8"

    __str__ = __repr__


class LyingLabel(str):
    def __str__(self):
        return "approved_family_default"

    __repr__ = __str__


@pytest.mark.parametrize("installed", [False, True])
def test_review_f5_the_gate_never_runs_the_candidate_s_repr_or_str(trust, installed):
    if installed:
        trust(**FULL_TRUST)
    for value in (RaisingFloat(0.8), LyingRepr(0.3)):
        anchors = replace(real(), declared={**dict(real().declared)})
        object.__setattr__(anchors, "pump_reserve", value)
        rows = migration_gate("gi_bleed", anchors, FAMILY_APPROVED)
        assert not rows["pump_reserve"]["migratable"] and "0.8" not in rows["pump_reserve"]["reason"]
        with pytest.raises(MigrationBlocked):
            check_migration_gate("gi_bleed", anchors, FAMILY_APPROVED)
        with pytest.raises(MigrationBlocked):
            migration_gate("gi_bleed", real(), {**FAMILY_APPROVED, "fraction_with_ppi": (value, "explicit_case")})
    anchors = real()
    object.__setattr__(anchors, "declared", {**dict(anchors.declared), "pump_reserve": LyingLabel("explicit_case")})
    row = migration_gate("gi_bleed", anchors, FAMILY_APPROVED)["pump_reserve"]
    assert not row["migratable"] and type(row["source"]) is str and row["source"] != "approved_family_default"


def test_review_f6_the_report_names_every_agreeing_mapping_and_a_declared_policy(trust):
    trust(**_trust_one(authority.CASE_OVERRIDES_FAMILY_DEFAULT,
                       maps=(mapping("pump_reserve", 0.8),
                             replace(mapping("pump_reserve", 0.8), mapping_id="test-map:pump_reserve/2"))))
    row = migration_gate("gi_bleed", _with("pump_reserve", 0.8), FAMILY_APPROVED)["pump_reserve"]
    assert row["migratable"] and row["authority"]["reference"] == "test-map:pump_reserve"
    assert any(note.startswith("test-map:pump_reserve/2 v1 -> 0.8: agrees") for note in row["authority"]["not_used"])
    # A declared policy is reported even when no trusted source holds the parameter.
    trust(**_trust_one(authority.CASE_REQUIRED))
    row = migration_gate("gi_bleed", _with("pump_reserve", 0.8), FAMILY_APPROVED)["pump_reserve"]
    assert not row["migratable"] and row["authority"]["policy"] == authority.CASE_REQUIRED


@pytest.mark.parametrize("registry", ["AUTHORITY_POLICIES", "TRUSTED_CASE_MAPPINGS", "APPROVED_FAMILY_DEFAULTS"])
def test_review_h1_a_registry_entry_of_the_wrong_type_fails_closed(trust, monkeypatch, registry):
    from types import SimpleNamespace
    trust(**FULL_TRUST)
    good = getattr(authority, registry)[0]
    for impostor in (tuple(vars(good).values()) if hasattr(good, "__dict__") else (),
                     SimpleNamespace(**{name: getattr(good, name) for name in good.__dataclass_fields__})):
        monkeypatch.setattr(authority, registry, (*getattr(authority, registry), impostor))
        rows = migration_gate("gi_bleed", real(), FAMILY_APPROVED)
        assert not any(row["migratable"] for row in rows.values())
        assert all(f"the trusted registry {registry}" in row["reason"] for row in rows.values())
        with pytest.raises(TypeError):
            authority.registry_content()
        trust(**FULL_TRUST)


def test_review_f2_registered_rules_are_plain_functions():
    import functools

    class Rule:
        def __call__(self, fields):
            return 0.5

        def method(self, fields):
            return 0.5
    for rule in (functools.partial(lambda fields, value: value, value=0.5), Rule(), Rule().method, float):
        with pytest.raises(ValueError, match="plain Python functions"):
            CaseMapping("m", "1", "gi_bleed", "pump_reserve", ("engine.family",), lambda fields: True, rule, "t")
