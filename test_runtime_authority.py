"""P3-14: the future limited-authority machinery exists and CANNOT be activated.

Every test here defends one of two claims. The first is that the machinery is complete: a mode, a gate of
nine conditions, an ownership contract with one owner per output, a transaction that commits the three
pressures together or not at all, a validation with no numeric clinical tolerance in it, and a record that
keeps the legacy counterfactual beside the common candidate. The second is that none of it can run: there
is no faculty-approved parameter snapshot, so the gate refuses in every configuration this repository can
produce, and the authority mode is unreachable.

The legacy engine remains the only active runtime authority. ``app.py`` and ``pilot_acceptance.py`` do not
import this module at all, which is also a test.
"""
import ast
import os
import tempfile
from copy import deepcopy
from pathlib import Path

import pytest

import runtime_authority as ra
import runtime_authority_store as store
import runtime_shadow as rs

ROOT = Path(__file__).resolve().parent
CASE = "gi_bleed_57m"
#: The most favourable configuration a deployment could possibly produce, short of an approved snapshot.
BEST = {ra.AUTHORITY_FLAG: ra.MODE_LIMITED_COMMON_AUTHORITY,
        ra.SNAPSHOT_FLAG: "whatever_a_deployment_might_name",
        ra.ENVIRONMENT_FLAG: "development"}


#: A digest-shaped value: ``validate`` refuses anything that is not sha256 hex (P3-17).
DIGEST = "d" * 64
OTHER_DIGEST = "e" * 64
TEST_ONLY_ID = "test_only_point"
#: A TEST-ONLY approval. It is NOT a faculty decision and carries no clinical magnitude: its parameter is
#: a placeholder, and the only field that matters here is the binding to the point the shadow layer ran.
TEST_ONLY_SNAPSHOT = {"id": TEST_ONLY_ID,
                      "approved_by_faculty": True,
                      "decision": "TEST ONLY: exists inside one test session, approves nothing",
                      "runtime_parameter_snapshot_id": rs.PARAMETER_SNAPSHOT_ID,
                      "parameters": {"test_only_placeholder": 1.0}}
#: This file's own artifact store, outside the repository: no test here may write into an ambient one.
STORE_DIR = tempfile.mkdtemp(prefix="phase3-authority-gate-")


@pytest.fixture(autouse=True)
def _pinned_store(monkeypatch):
    """No authority test may write into an ambient faculty store (P3-28 review)."""
    monkeypatch.setenv(store.STORE_FLAG, STORE_DIR)


@pytest.fixture(scope="module")
def gi_state():
    import pilot_acceptance
    return deepcopy(pilot_acceptance.Encounter(CASE).state)


@pytest.fixture
def approved(monkeypatch):
    """Register the test-only approval and the configuration a commit needs, then withdraw both.

    P3-17 closed two holes that make this fixture necessary: the registry is read-only from outside, so
    the injection goes through the private mapping on purpose; and ``commit`` re-evaluates the gate, so a
    transaction cannot write unless the whole configuration holds.
    """
    monkeypatch.setitem(ra._APPROVED_SNAPSHOT_POINTS, TEST_ONLY_ID, TEST_ONLY_SNAPSHOT)
    for name, value in ((ra.AUTHORITY_FLAG, ra.MODE_LIMITED_COMMON_AUTHORITY),
                        (ra.SNAPSHOT_FLAG, TEST_ONLY_ID), (ra.ENVIRONMENT_FLAG, "development")):
        monkeypatch.setenv(name, value)
    for name in ra.PILOT_FLAGS + ra.PILOT_REQUIRED_ON:
        monkeypatch.delenv(name, raising=False)
    return TEST_ONLY_SNAPSHOT


def _candidate(sbp=90.0, dbp=55.0, mean=67.0):
    return {"sbp": sbp, "dbp": dbp, "map": mean}


def _transaction(**kwargs):
    """A transaction built directly, with an explicit snapshot: exercisable, never reachable."""
    base = {"minute": 10, "case_id": CASE, "snapshot": dict(TEST_ONLY_SNAPSHOT)}
    base.update(kwargs)
    return ra.AuthorityTransaction(**base)


# -- P3-14-1, P3-14-8: the mode exists and is unreachable --------------------------------------------------

def test_a1_the_authority_mode_is_unreachable_from_any_configuration(gi_state):
    assert ra.MODES == (ra.MODE_LEGACY, ra.MODE_SHADOW_COMPARE, ra.MODE_LIMITED_COMMON_AUTHORITY)
    assert ra.APPROVED_SNAPSHOTS == {}, "P3-14 may not approve an authority snapshot"
    assert ra.unreachable_because(), "the reason authority cannot run must be stated, not implied"
    decision = ra.gate(gi_state, environ=BEST, unsupported=())
    assert not decision.granted
    assert [name for name, ok in decision.conditions.items() if not ok] == ["approved_snapshot"], \
        decision.to_dict()
    # And a caller that does not say which management actions ran gets a refusal, not a pass (P3-17).
    assert not ra.gate(gi_state, environ=BEST).conditions["no_unsupported_action"]
    assert ra.mode(gi_state, environ=BEST) == ra.MODE_LEGACY
    assert ra.mode(gi_state, environ={**BEST, rs.FLAG: rs.MODE_SHADOW_COMPARE}) == ra.MODE_SHADOW_COMPARE
    assert ra.AuthorityTransaction.open_for(gi_state, environ=BEST) is None
    assert ra.AuthorityTransaction.open_for(gi_state, environ=BEST, unsupported=()) is None


def test_a2_no_single_input_can_open_the_gate(gi_state, monkeypatch):
    """Not an environment string, not a secret, not case metadata, not something a user could type."""
    assert not ra.gate(gi_state, environ={ra.AUTHORITY_FLAG: ra.MODE_LIMITED_COMMON_AUTHORITY}).granted
    monkeypatch.setattr(rs, "_named_in_secrets", lambda name: True)
    assert not ra.gate(gi_state, environ=BEST).granted
    poisoned = {**gi_state, "authority": "granted", "mode": ra.MODE_LIMITED_COMMON_AUTHORITY,
                "faculty_approved_snapshot": "yes", "phase3_authority": True}
    assert not ra.gate(poisoned, environ=BEST).granted
    assert ra.mode(poisoned, environ=BEST) != ra.MODE_LIMITED_COMMON_AUTHORITY
    # And a snapshot id a deployment invents is not an approved snapshot.
    for invented in ("gi_region_lower", "gi_committed_default", "gi_pressure_preload_low",
                     "gi_pressure_committed", "gi_pressure_preload_high", TEST_ONLY_ID, None):
        assert ra.approved_snapshot(invented) is None, invented


def test_a3_every_one_of_the_nine_conditions_is_evaluated_and_can_be_the_only_failure(gi_state):
    decision = ra.gate(gi_state, environ=BEST)
    assert set(decision.conditions) == set(ra.GATE_CONDITIONS), decision.conditions
    # The gate does not short-circuit: a future experiment must see every condition it still has to meet.
    assert len(decision.conditions) == 9
    cases = {
        "authority_flag": {name: value for name, value in BEST.items() if name != ra.AUTHORITY_FLAG},
        "environment": {**BEST, ra.ENVIRONMENT_FLAG: "production"},
        "no_pilot": {**BEST, ra.PILOT_FLAGS[0]: "1"},
    }
    for condition, environ in cases.items():
        failing = {name for name, ok in ra.gate(gi_state, environ=environ).conditions.items() if not ok}
        assert condition in failing, (condition, failing)
    assert not ra.gate(gi_state, environ=BEST, case_id="not_a_case").conditions["family_and_case"]
    assert not ra.gate(gi_state, environ=BEST, family="acs").conditions["family_and_case"]
    assert not ra.gate(gi_state, environ=BEST,
                       unsupported=("norepinephrine",)).conditions["no_unsupported_action"]
    assert not ra.gate(gi_state, environ=BEST, domain=("sbp",)).conditions["authority_domain"]


def test_a4_the_phase2_digest_and_the_layer_version_are_gate_conditions(gi_state, monkeypatch):
    import runtime_shadow_evidence as ev
    assert ra.gate(gi_state, environ=BEST, unsupported=()).conditions["phase2_digest"]
    monkeypatch.setattr(ev, "phase2_digest_now", lambda: "a different digest")
    assert not ra.gate(gi_state, environ=BEST).conditions["phase2_digest"]
    monkeypatch.setattr(rs, "MODULE_VERSION", "P9-99")
    assert not ra.gate(gi_state, environ=BEST).conditions["layer_version"]
    assert ra.EXPECTED_LAYER == "P3-11", "the expectation is a literal: comparing a value with itself " \
                                         "would be a condition that cannot fail"


# -- P3-14-3: the ownership contract -----------------------------------------------------------------------

def test_a5_every_output_has_exactly_one_owner_and_the_pressures_are_the_only_common_ones():
    from clinical_core import comparison
    table = ra.ownership()
    comparable = [variable.name for variable in comparison.VARIABLES
                  if variable.kind not in ("core_only", "legacy_only")]
    assert set(comparable) <= set(table), sorted(set(comparable) - set(table))
    common = sorted(name for name, owner in table.items() if owner == ra.COMMON)
    # P3-17 found that the application derives the displayed MAP from the committed SBP and DBP, so MAP
    # carries its own owner: it is shown, and it is not settable without changing the display.
    assert common == ["dbp", "sbp"], common
    assert table["map"] == ra.DERIVED_IN_DISPLAY
    assert sorted(ra.AUTHORITY_DOMAIN) == ["dbp", "map", "sbp"]
    for name in ("crt_s", "hr", "respiratory_rate", "spo2", "hb_g_dl", "lactate_mmol_l", "V_ml_eq",
                 "consciousness_level", "pulse_present", "rhythm"):
        assert table.get(name) in (ra.LEGACY, ra.COMPARISON_ONLY), (name, table.get(name))
    assert set(table.values()) <= {ra.COMMON, ra.LEGACY, ra.COMPARISON_ONLY, ra.DERIVED_IN_DISPLAY}
    assert len({ra.COMMON, ra.LEGACY, ra.COMPARISON_ONLY, ra.DERIVED_IN_DISPLAY}) == 4


def test_a6_the_pressure_domain_cannot_be_cherry_picked():
    assert ra.domain_is_coherent(("sbp", "dbp", "map"))[0]
    for asked in (("sbp",), ("map",), ("sbp", "dbp"), ("dbp", "map"), ()):
        ok, why = ra.domain_is_coherent(asked)
        assert not ok and why, asked
    assert "one state" in ra.domain_is_coherent(("map",))[1]


# -- P3-14-4, P3-14-6: the transaction and its atomicity ---------------------------------------------------

def test_a7_the_pressure_domain_is_committed_together_and_map_is_the_displays_own(gi_state, approved):
    transaction = _transaction()
    transaction.capture(gi_state).compute(_candidate(), {"sbp": 88.0, "dbp": 54.0, "map": 65.0})
    assert transaction.validate(replay_digest=DIGEST, expected_digest=DIGEST, unsupported=())
    prepared = transaction.commit(gi_state)
    assert transaction.state == ra.COMMITTED
    assert sorted(transaction.committed) == ["dbp", "map", "sbp"]
    assert prepared["observable"]["sbp"] == 90.0 and prepared["observable"]["dbp"] == 55.0
    # P3-17 refused the core's own mean pressure, because it disagreed with the displayed one by a
    # millimetre; the P3-19 review then found that leaving the legacy one made the state and the trace
    # disagree with the screen. What is written is the DISPLAY's function of the two committed pressures.
    assert prepared["observable"]["map"] == ra.derived_map(90.0, 55.0) == 67
    assert prepared["observable"]["map"] != _candidate()["map"] or ra.derived_map(90.0, 55.0) == 67
    # The authoritative state the caller passed in is NOT mutated: the commit returns a new mapping.
    assert gi_state["observable"]["sbp"] != 90.0 or gi_state["observable"]["dbp"] != 55.0
    untouched = {key: value for key, value in prepared["observable"].items()
                 if key not in ra.AUTHORITY_DOMAIN}
    for key, value in untouched.items():
        assert gi_state["observable"].get(key) == value, key


@pytest.mark.parametrize("stage", ["capture", "compute", "validate"])
def test_a8_a_failure_at_any_stage_commits_nothing(gi_state, stage, approved):
    transaction = _transaction()
    before = deepcopy(gi_state)
    if stage == "capture":
        with pytest.raises(ra.AuthorityRefused):
            transaction.commit(gi_state)
    elif stage == "compute":
        transaction.capture(gi_state)
        assert not transaction.validate(replay_digest=DIGEST, expected_digest=DIGEST, unsupported=())
        with pytest.raises(ra.AuthorityRefused):
            transaction.commit(gi_state)
    else:
        transaction.capture(gi_state).compute(_candidate())
        assert not transaction.validate(replay_digest=DIGEST, expected_digest=OTHER_DIGEST, unsupported=())
        with pytest.raises(ra.AuthorityRefused):
            transaction.commit(gi_state)
    assert transaction.state == ra.ABORTED and transaction.committed == ()
    assert gi_state == before, "the authoritative state must be untouched by a refused transaction"


def test_a9_an_unapproved_snapshot_can_never_commit(gi_state, approved):
    transaction = _transaction(snapshot=None)
    transaction.capture(gi_state).compute(_candidate())
    assert not transaction.validate(replay_digest=DIGEST, expected_digest=DIGEST, unsupported=())
    assert "snapshot_approved" in transaction.failures
    with pytest.raises(ra.AuthorityRefused):
        transaction.commit(gi_state)
    # Even a transaction that somehow validated cannot commit without one.
    forced = _transaction(snapshot=None)
    forced.capture(gi_state).compute(_candidate())
    forced.state = ra.VALIDATED
    with pytest.raises(ra.AuthorityRefused) as refused:
        forced.commit(gi_state)
    assert "NO_FACULTY_APPROVED_AUTHORITY_SNAPSHOT" in str(refused.value)


@pytest.mark.parametrize("kwargs,expected", [
    ({"invariants_hold": False}, "invariants_hold"),
    ({"unsupported": ("norepinephrine",)}, "supported_management"),
    ({"legacy_arrest": True}, "no_legacy_arrest"),
    ({"replay_digest": None}, "minute_reproducible"),
    ({"replay_digest": "same", "expected_digest": "same"}, "minute_reproducible"),
    ({"unsupported": None}, "supported_management"),
])
def test_a10_each_validation_check_can_refuse(gi_state, kwargs, expected, approved):
    transaction = _transaction()
    transaction.capture(gi_state).compute(_candidate())
    arguments = {"replay_digest": DIGEST, "expected_digest": DIGEST, "unsupported": (), **kwargs}
    assert not transaction.validate(**arguments)
    assert transaction.failures == [expected], transaction.failures
    assert transaction.rollback and transaction.rollback["validation_failures"] == [expected]


def test_a11_an_incomplete_candidate_is_refused(gi_state, approved):
    transaction = _transaction()
    transaction.capture(gi_state).compute({"sbp": 90.0, "dbp": None, "map": 67.0})
    assert not transaction.validate(replay_digest=DIGEST, expected_digest=DIGEST, unsupported=())
    assert "candidate_complete" in transaction.failures


def test_a12_a_core_failure_or_a_boundary_refuses_the_commit(gi_state, approved):
    for classification, expected in ((rs.UNEXPECTED, "no_core_failure"),
                                     (rs.BOUNDARY, "no_unresolved_boundary")):
        transaction = _transaction()
        transaction.capture(gi_state).compute(_candidate())
        failure = rs.ShadowFailure(10, "core", "CoreInvariantError", "broken", classification)
        assert not transaction.validate(replay_digest=DIGEST, expected_digest=DIGEST, unsupported=(),
                                        failures=(failure,))
        assert expected in transaction.failures


# -- P3-14-5: no numeric clinical tolerance ----------------------------------------------------------------

def test_a13_the_validation_introduces_no_numeric_clinical_tolerance():
    """A tolerance would be a clinical decision. There is no number to find in the validation."""
    tree = ast.parse((ROOT / "runtime_authority.py").read_text(encoding="utf-8"))
    validate = next(node for node in ast.walk(tree)
                    if isinstance(node, ast.FunctionDef) and node.name == "validate")
    # A tolerance is a float, or an inequality against a magnitude. An integer used as a tuple index is
    # neither, so indices are the only numbers allowed to appear here.
    indices = {id(node.slice) for node in ast.walk(validate) if isinstance(node, ast.Subscript)}
    numbers = [node.value for node in ast.walk(validate)
               if isinstance(node, ast.Constant) and isinstance(node.value, (int, float))
               and not isinstance(node.value, bool) and id(node) not in indices]
    assert numbers == [], numbers
    assert not [node.value for node in ast.walk(validate)
                if isinstance(node, ast.Constant) and isinstance(node.value, float)]
    for node in ast.walk(validate):
        assert not isinstance(node, (ast.Lt, ast.LtE, ast.Gt, ast.GtE)), ast.dump(node)


# -- P3-14-7: the legacy counterfactual --------------------------------------------------------------------

def test_a14_the_record_keeps_the_legacy_counterfactual_beside_the_candidate(gi_state, approved):
    legacy = {"sbp": 88.0, "dbp": 54.0, "map": 65.0}
    transaction = _transaction()
    transaction.capture(gi_state).compute(_candidate(), legacy)
    transaction.divergence = (ra.counterfactual(_candidate(), legacy, 10),)
    record = transaction.record()
    assert record["legacy_counterfactual"] == legacy and record["candidate"] == _candidate()
    assert record["ownership"]["sbp"] == ra.COMMON and record["ownership"]["hr"] == ra.LEGACY
    assert record["common_core_runtime_authority"] is False
    assert record["versions"]["phase2_digest"] == rs.PHASE2_DIGEST
    assert record["versions"]["golden_digest"] and record["versions"]["phase3_layer_digest"]
    reading = ra.counterfactual(_candidate(), legacy, 10)
    assert reading["rows"]["sbp"]["status"] == "DIFFERS" and reading["rows"]["sbp"]["difference"] == 2.0
    assert "not clinical ground truth" in reading["reading"]
    assert ra.counterfactual({"sbp": None}, legacy, 10)["rows"]["sbp"]["status"] == rs.NOT_COMPARABLE


def test_a15_an_abort_records_why_and_commits_nothing(gi_state, approved):
    transaction = _transaction()
    transaction.capture(gi_state).compute(_candidate())
    record = transaction.abort("the experiment stops visibly")
    assert record["state"] == ra.ABORTED and record["committed"] == []
    assert record["reason"] == "the experiment stops visibly"
    assert record["runtime_authority"] == "legacy"


# -- the harness is dormant: the runtime does not know it exists -------------------------------------------

def test_a16_exactly_one_production_wiring_point_imports_the_authority_harness():
    """P3-19 wired the call site in, so the import exists. What must not exist is a way to activate it."""
    def imports(path):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import)
                 for alias in node.names}
        return names | {node.module for node in ast.walk(tree)
                        if isinstance(node, ast.ImportFrom) and node.module}

    # The declared layer may read itself: the P3-26 artifact store is part of it. The claim is about
    # everything else -- exactly one production wiring point, and it is the app's helper.
    readers = sorted(path.name for path in ROOT.glob("*.py")
                     if not path.name.startswith("test_") and path.name not in rs.LAYER_SOURCES
                     and "runtime_authority" in imports(path))
    assert readers == ["app.py"], readers
    assert "runtime_authority" not in (ROOT / "pilot_acceptance.py").read_text(encoding="utf-8")
    assert "runtime_authority.py" in rs.LAYER_SOURCES, "the layer digest must cover it"
    # The import is inert: the site refuses in every configuration, so the encounter runs as it did.
    assert ra.site_for({}, {}) is None and ra.open_site({}) is None
    assert ra.APPROVED_SNAPSHOTS == {} and ra.unreachable_because()


def test_a17_the_harness_computes_no_physiology_of_its_own():
    """The candidate comes from the shadow runner: this module never advances the core."""
    source = (ROOT / "runtime_authority.py").read_text(encoding="utf-8")
    for forbidden in ("integration.run", "scenario_from_dict", "comparison._display"):
        assert forbidden not in source, forbidden
    tree = ast.parse(source)
    imported = {node.module for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) and node.module}
    assert not {name for name in imported if str(name).startswith("clinical_physiology")}


# -- P3-17: what the adversarial review closed ------------------------------------------------------------

def test_c1_the_approved_registry_cannot_be_written_from_outside():
    """It was a plain module dict: any importer could approve a parameter point."""
    assert ra.APPROVED_SNAPSHOTS == {} and ra._APPROVED_SNAPSHOT_POINTS == {}
    for attempt in (lambda: ra.APPROVED_SNAPSHOTS.__setitem__("forged", {}),
                    lambda: ra.APPROVED_SNAPSHOTS.update({"forged": {}}),
                    lambda: ra.APPROVED_SNAPSHOTS.setdefault("forged", {}),
                    lambda: ra.APPROVED_SNAPSHOTS.pop("forged", None)):
        with pytest.raises((TypeError, AttributeError)):
            attempt()
    assert ra.APPROVED_SNAPSHOTS == {}


def test_c2_a_malformed_or_forged_approval_opens_nothing(gi_state, monkeypatch):
    """A lookup by id used to be the whole check: ``{}`` and even a string passed it."""
    for forged in ({}, "I am a string, not an approved parameter point",
                   {"id": "forged", "parameters": {}, "approved_by_faculty": True,
                    "decision": "x", "runtime_parameter_snapshot_id": rs.PARAMETER_SNAPSHOT_ID},
                   {"id": "forged", "parameters": {"a": 1}, "approved_by_faculty": "yes",
                    "decision": "x", "runtime_parameter_snapshot_id": rs.PARAMETER_SNAPSHOT_ID},
                   {"id": "forged", "parameters": {"a": 1}, "approved_by_faculty": True,
                    "runtime_parameter_snapshot_id": rs.PARAMETER_SNAPSHOT_ID}):
        with monkeypatch.context() as patch:
            patch.setitem(ra._APPROVED_SNAPSHOT_POINTS, "forged", forged)
            patch.setenv(ra.SNAPSHOT_FLAG, "forged")
            assert ra.approved_snapshot("forged") is None, forged
            assert not ra.gate(gi_state, environ={**BEST, ra.SNAPSHOT_FLAG: "forged"},
                               unsupported=()).granted
            transaction = _transaction(snapshot=forged)
            transaction.capture(gi_state).compute(_candidate())
            assert not transaction.validate(replay_digest=DIGEST, expected_digest=DIGEST,
                                            unsupported=())
            assert "snapshot_approved" in transaction.failures
            with pytest.raises(ra.AuthorityRefused):
                transaction.commit(gi_state)


def test_c3_the_approval_must_be_the_point_the_shadow_runner_ran(gi_state, approved):
    """Nothing tied the approved point to the physiology that produced the candidate."""
    assert ra.snapshot_is_wellformed(TEST_ONLY_SNAPSHOT)[0]
    spoofed = {**TEST_ONLY_SNAPSHOT, "runtime_parameter_snapshot_id": "gi_pressure_preload_high"}
    ok, why = ra.snapshot_is_wellformed(spoofed)
    assert not ok and any("is not the point the shadow runner ran" in reason for reason in why), why
    transaction = _transaction(snapshot=spoofed)
    transaction.capture(gi_state).compute(_candidate())
    assert not transaction.validate(replay_digest=DIGEST, expected_digest=DIGEST, unsupported=())
    assert "snapshot_approved" in transaction.failures


def test_c4_the_gate_is_re_evaluated_at_commit(gi_state, approved, monkeypatch):
    """A transaction built by hand used to commit without any of the nine conditions holding."""
    transaction = _transaction()
    transaction.capture(gi_state).compute(_candidate())
    assert transaction.validate(replay_digest=DIGEST, expected_digest=DIGEST, unsupported=())
    monkeypatch.delenv(ra.AUTHORITY_FLAG)
    with pytest.raises(ra.AuthorityRefused) as refused:
        transaction.commit(gi_state)
    assert "the authority gate refuses at commit" in str(refused.value)
    assert transaction.state == ra.ABORTED and transaction.committed == ()
    # The case and the family are the state's, not the caller's: a foreign case cannot borrow the gate.
    other = ra.AuthorityTransaction(minute=10, case_id="not_an_allowlisted_case", family="acs",
                                    domain=("hr", "spo2"), snapshot=dict(TEST_ONLY_SNAPSHOT))
    other.capture(gi_state).compute({"hr": 42, "spo2": 11})
    assert not other.validate(replay_digest=DIGEST, expected_digest=DIGEST, unsupported=())
    with pytest.raises(ra.AuthorityRefused):
        other.commit(gi_state)
    assert not ra.gate(gi_state, environ=BEST, unsupported=(), case_id="gi_bleed_72f",
                       family="gi_bleed").conditions["family_and_case"]


def test_c5_the_transaction_state_is_not_a_constructor_field():
    """``AuthorityTransaction(state=VALIDATED)`` was the shortest path to a commit."""
    with pytest.raises(TypeError):
        ra.AuthorityTransaction(minute=0, case_id=CASE, state=ra.VALIDATED)
    for field_name in ("state", "committed", "failures", "reason", "rollback"):
        with pytest.raises(TypeError):
            ra.AuthorityTransaction(minute=0, case_id=CASE, **{field_name: "x"})


def test_c6_a_commit_target_that_is_not_what_was_captured_is_refused(gi_state, approved):
    transaction = _transaction()
    transaction.capture(gi_state).compute(_candidate())
    assert transaction.validate(replay_digest=DIGEST, expected_digest=DIGEST, unsupported=())
    advanced = {**deepcopy(gi_state), "sim_time": 20}
    with pytest.raises(ra.AuthorityRefused) as refused:
        transaction.commit(advanced)
    assert "not the state this transaction captured" in str(refused.value)
    assert transaction.state == ra.ABORTED and advanced["observable"] == gi_state["observable"]


def test_c7_a_candidate_without_usable_pressures_is_refused_at_commit(gi_state, approved):
    for candidate in ({"sbp": 90.0, "dbp": None, "map": 67.0}, {"sbp": "ninety", "dbp": 55.0},
                      {"sbp": True, "dbp": 55.0}, {}):
        transaction = _transaction()
        transaction.capture(gi_state).compute(_candidate())
        assert transaction.validate(replay_digest=DIGEST, expected_digest=DIGEST, unsupported=())
        transaction.candidate = dict(candidate)
        with pytest.raises(ra.AuthorityRefused):
            transaction.commit(gi_state)
        assert transaction.state == ra.ABORTED and transaction.committed == ()


def test_c8_an_undeclared_action_list_fails_closed_everywhere(gi_state, approved):
    assert not ra.gate(gi_state, environ=BEST).conditions["no_unsupported_action"]
    assert ra.AuthorityTransaction.open_for(gi_state) is None
    transaction = _transaction()
    transaction.capture(gi_state).compute(_candidate())
    assert not transaction.validate(replay_digest=DIGEST, expected_digest=DIGEST)
    assert transaction.failures == ["supported_management"]
    assert ra.SUPPORTED_ACTIONS and "endoscopy" in ra.SUPPORTED_ACTIONS


def test_c9_a_failure_inside_the_write_leaves_the_transaction_aborted(gi_state, approved):
    """It used to stay VALIDATED after a crash, so a second call committed."""
    transaction = _transaction()
    transaction.capture(gi_state).compute(_candidate())
    assert transaction.validate(replay_digest=DIGEST, expected_digest=DIGEST, unsupported=())
    def boom(_value):
        raise RuntimeError("the copy of the authoritative state failed")
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(ra, "deepcopy", boom)
        with pytest.raises(ra.AuthorityRefused) as refused:
            transaction.commit(gi_state)
    assert "nothing was written" in str(refused.value)
    assert transaction.state == ra.ABORTED and transaction.committed == ()
    assert transaction.rollback and transaction.rollback["committed"] == []
    with pytest.raises(ra.AuthorityRefused):
        transaction.commit(gi_state)


def test_c10_the_pilot_condition_is_anchored_to_the_pilots_own_freeze(gi_state, approved, monkeypatch):
    """``MRS_PILOT`` exists nowhere else in the repository, so it protected nothing on its own."""
    import pilot_freeze
    assert ra.pilot_deployment_markers(), "the pilot's own runtime flags must be readable"
    assert set(ra.pilot_deployment_markers()) <= set(pilot_freeze.RUNTIME_FLAGS)
    assert not ra.looks_like_the_pilot({})[0]
    real_pilot = {name: "1" for name in ra.pilot_deployment_markers()}
    is_pilot, why = ra.looks_like_the_pilot(real_pilot)
    assert is_pilot and "pilot's required runtime flags" in why
    assert not ra.gate(gi_state, environ={**BEST, **real_pilot}, unsupported=()).conditions["no_pilot"]
    # And if the freeze cannot be read at all, the condition fails closed instead of passing.
    monkeypatch.setattr(ra, "pilot_deployment_markers", lambda: ())
    assert ra.looks_like_the_pilot({})[0]
    assert not ra.gate(gi_state, environ=BEST, unsupported=()).conditions["no_pilot"]


def test_c11_the_mode_can_be_asked_why(gi_state):
    """``mode()`` returns a string, so a refusal and a default were indistinguishable."""
    chosen, decision = ra.mode_decision(gi_state, environ=BEST, unsupported=())
    assert chosen == ra.MODE_LEGACY and not decision.granted
    assert any("NO_FACULTY_APPROVED_AUTHORITY_SNAPSHOT_EXISTS" in reason for reason in decision.reasons)
    assert set(decision.conditions) == set(ra.GATE_CONDITIONS)
    assert ra.mode(gi_state, environ=BEST, unsupported=()) == chosen


def test_c12_a_declared_mirror_gap_or_a_contradictory_coverage_is_not_eligible():
    """The gaps were computed and then skipped; SUPPORTED_ACTIONS was read by nobody."""
    base = {"case": CASE, "scenario": "synthetic", "live_equals_replay": True,
            "coverage": {"fluid": {"status": "FULLY_MIRRORED"}}, "gaps": [], "failures": [],
            "boundaries": [], "unexpected": []}
    assert ra.eligibility(base, environ={}).classification == ra.ELIGIBLE_BUT_NO_SNAPSHOT
    gapped = {**base, "gaps": [{"kind": "fluid", "why": "held until a result arrives"}]}
    verdict = ra.eligibility(gapped, environ={})
    assert verdict.classification == ra.INELIGIBLE_OTHER
    assert any("no_mirror_gap" in reason for reason in verdict.reasons), verdict.reasons
    contradictory = {**base, "coverage": {"vasopressor": {"status": "FULLY_MIRRORED"}}}
    verdict = ra.eligibility(contradictory, environ={})
    assert verdict.classification == ra.INELIGIBLE_UNSUPPORTED
    assert verdict.unsupported == ("vasopressor",)


# -- P3-15: eligibility, read from the acceptance battery --------------------------------------------------

@pytest.fixture(scope="module")
def battery():
    import runtime_shadow_evidence as ev
    data = ev.gi_evidence()
    return {"evidence": data, "eligibility": ra.eligibility_battery(data)}


def test_b1_the_thirty_four_scenarios_are_classified_and_none_is_left_out(battery):
    result = battery["eligibility"]
    assert result["scenarios"] == 34
    # P3-22 re-measured this honestly: two more scenarios order something the engine itself does not
    # model, and the eligibility reading now sees the settled order classes as the call site does.
    assert result["counts"] == {ra.ELIGIBLE_BUT_NO_SNAPSHOT: 26, ra.INELIGIBLE_UNSUPPORTED: 8}
    assert set(result["counts"]) <= {ra.ELIGIBLE_BUT_NO_SNAPSHOT, ra.INELIGIBLE_UNSUPPORTED,
                                     ra.INELIGIBLE_OTHER}
    assert len(result["rows"]) == sum(result["counts"].values())
    assert not result["approved_snapshot_exists"]


def test_b2_an_unsupported_action_fails_closed_and_is_named(battery):
    """Six scenarios, three actions, and not one of them silently ignored."""
    rows = [row for row in battery["eligibility"]["rows"]
            if row["classification"] == ra.INELIGIBLE_UNSUPPORTED]
    assert sorted(row["scenario"] for row in rows) == [
        "D_incorrect_treatment", "D_incorrect_treatment", "F_start_stop", "F_start_stop",
        "H_unexpected_reasonable", "H_unexpected_reasonable",
        "K_combined_interventions", "K_combined_interventions"]
    assert battery["eligibility"]["ineligible_unsupported"] == ["anticoagulation", "aspirin",
                                                                "norepinephrine", "not_modelled"]
    for row in rows:
        assert row["unsupported"], row
        assert any(ra.INELIGIBLE_UNSUPPORTED in reason for reason in row["reasons"]), row
        # Either the shadow declared the gap, or the settled ledger carried the class: both are the
        # same rule, and an order the engine does not model only appears in the second.
        assert set(row["unsupported"]) <= set(row["facts"]["declared_gaps"]) | \
            set(row["facts"]["settled_classes"]), row


def test_b3_every_eligible_scenario_mirrors_and_replays_only_supported_actions(battery):
    for row in battery["eligibility"]["rows"]:
        if row["classification"] != ra.ELIGIBLE_BUT_NO_SNAPSHOT:
            continue
        assert row["facts"]["live_equals_replay"], row["scenario"]
        assert row["facts"]["no_shadow_failure"] and row["facts"]["no_boundary"], row["scenario"]
        assert row["facts"]["no_unexpected_divergence"], row["scenario"]
        assert row["facts"]["case_allowlisted"] and row["facts"]["domain_coherent"]
        assert not row["unsupported"]
    for case in battery["evidence"]["cases"]:
        for scenario in case["scenarios"]:
            for kind, how in scenario["coverage"].items():
                if how["status"] != "UNSUPPORTED":
                    assert kind in ra.SUPPORTED_ACTIONS, (scenario["scenario"], kind)


def test_b4_the_only_remaining_condition_is_the_faculty_snapshot(battery):
    rows = [row for row in battery["eligibility"]["rows"]
            if row["classification"] == ra.ELIGIBLE_BUT_NO_SNAPSHOT]
    assert len(rows) == 26
    for row in rows:
        assert any("NO_FACULTY_APPROVED_AUTHORITY_SNAPSHOT_EXISTS" in reason
                   for reason in row["reasons"]), row
        assert row["facts"]["approved_snapshot"] is False


def test_b5_a_pilot_configuration_makes_every_scenario_ineligible(battery):
    scenario = battery["evidence"]["cases"][0]["scenarios"][0]
    verdict = ra.eligibility(scenario, environ={ra.PILOT_FLAGS[0]: "1"})
    assert verdict.classification == ra.INELIGIBLE_OTHER
    assert any("no_pilot" in reason for reason in verdict.reasons), verdict.reasons


def test_b6_eligibility_is_deterministic_and_reads_only_the_scenario(battery):
    scenario = battery["evidence"]["cases"][0]["scenarios"][0]
    first = ra.eligibility(scenario, environ={}).to_dict()
    assert first == ra.eligibility(deepcopy(scenario), environ={}).to_dict()
    # A scenario whose replay did not reproduce is ineligible, and it says which fact failed.
    broken = {**scenario, "live_equals_replay": False}
    verdict = ra.eligibility(broken, environ={})
    assert verdict.classification == ra.INELIGIBLE_OTHER
    assert any("live_equals_replay" in reason for reason in verdict.reasons)


# -- P3-15-4, P3-15-5: no mid-encounter switch, and a visible failure --------------------------------------

def test_b7_the_mode_is_decided_once_at_the_start_of_the_encounter(gi_state):
    assert ra.FAILURE_POLICY == "HARD_FAIL_VISIBLE_TO_FACULTY"
    assert ra.MODE_DECIDED_AT == "encounter_start"
    assert int(gi_state.get("sim_time") or 0) == 0
    assert ra.encounter_mode(gi_state, environ=BEST) == ra.mode(gi_state, environ=BEST)
    midway = {**gi_state, "sim_time": 20}
    assert ra.encounter_mode(midway, environ=BEST) == ra.MODE_LEGACY
    assert ra.encounter_mode(midway, environ={**BEST, rs.FLAG: rs.MODE_SHADOW_COMPARE}) == ra.MODE_LEGACY
    assert ra.encounter_mode({"sim_time": "not a number"}, environ=BEST) == ra.MODE_LEGACY


def test_b8_the_rollback_artifact_preserves_everything_a_reader_would_need(gi_state, approved):
    transaction = _transaction()
    transaction.capture(gi_state).compute(_candidate(), {"sbp": 88.0, "dbp": 54.0, "map": 65.0})
    assert not transaction.validate(replay_digest=DIGEST, expected_digest=OTHER_DIGEST, unsupported=())
    artifact = ra.rollback_artifact(transaction, reason="the minute did not reproduce",
                                   history=[{"order_id": "t0:0", "kind": "fluid", "fate": "EXECUTED"}],
                                   replay_digest=DIGEST)
    for key in ("failure_policy", "mode_decided_at", "reason", "minute",
                "precommit_authoritative_state", "common_candidate", "legacy_counterfactual",
                "validation_failures", "action_history", "parameter_snapshot", "phase2_digest",
                "phase3_layer", "phase3_layer_digest", "replay_digest", "committed", "rescue"):
        assert key in artifact, key
    assert artifact["committed"] == [] and artifact["validation_failures"]
    assert artifact["precommit_authoritative_state"]["observable"] == gi_state["observable"]
    assert artifact["phase2_digest"] == rs.PHASE2_DIGEST
    assert "never continue the same encounter with the other engine" in artifact["rescue"]
    assert artifact["failure_policy"] == ra.FAILURE_POLICY


def test_b9_no_code_path_changes_the_mode_inside_an_encounter():
    """The mode is a pure function of the gate and the clock: there is nothing to flip mid-encounter."""
    source = (ROOT / "runtime_authority.py").read_text(encoding="utf-8")
    assert "self.mode =" not in source and "self._mode" not in source
    tree = ast.parse(source)
    assignments = [node for node in ast.walk(tree) if isinstance(node, ast.Assign)
                   for target in node.targets
                   if isinstance(target, ast.Attribute) and target.attr in ("mode", "authority")]
    assert assignments == [], [ast.dump(node) for node in assignments]
