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


@pytest.fixture
def trust(monkeypatch):
    def install(mappings=(), defaults=()):
        monkeypatch.setattr(authority, "TRUSTED_CASE_MAPPINGS", tuple(mappings))
        monkeypatch.setattr(authority, "APPROVED_FAMILY_DEFAULTS", tuple(defaults))
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
    assert rows["beta_blockade"]["authority"] == {"kind": authority.CASE_MAPPING,
                                                  "reference": "test-map:beta_blockade", "version": "1"}
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
        assert not row["migratable"] and phrase in row["reason"], (phrase, row["reason"])


def test_review_f5_every_applicable_trusted_source_must_agree(trust):
    claimed = real(beta_blockade="approved_family_default")
    # Case truth maps to 0.2 and an approved default says 0.0: the default does not override case truth.
    trust((*_without("beta_blockade"), mapping("beta_blockade", 0.5)),
          FULL_TRUST["defaults"] + (approval("beta_blockade", 0.2),))
    assert blocked(claimed, FAMILY_APPROVED) == ["beta_blockade"]
    assert "do not all agree" in migration_gate("gi_bleed", claimed, FAMILY_APPROVED)["beta_blockade"]["reason"]
    # Two mappings that disagree: neither value passes.
    trust((*_without("beta_blockade"), mapping("beta_blockade", 0.2),
           replace(mapping("beta_blockade", 0.7), mapping_id="test-map:beta_blockade/2")), FULL_TRUST["defaults"])
    assert blocked(real(), FAMILY_APPROVED) == ["beta_blockade"]
    # A mapping whose precondition the case does not meet does not apply, so the approved default can authorize.
    unmet = CaseMapping("test-map:beta_complete", "1", "gi_bleed", "beta_blockade", ("engine.family",),
                        lambda f: False, lambda f: 0.0, "test only: a complete medication source")
    trust((*_without("beta_blockade"), unmet), FULL_TRUST["defaults"] + (approval("beta_blockade", 0.2),))
    assert blocked(claimed, FAMILY_APPROVED) == []


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
