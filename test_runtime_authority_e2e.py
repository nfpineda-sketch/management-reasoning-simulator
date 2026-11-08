"""P3-17: the pre-activation gate. The application path, the atomicity and the failures, with no authority.

The authority machinery of P3-14/P3-15 is dormant, and P3-17 is what must pass BEFORE a faculty decision
could ever activate it. Three things are proven here:

1. the application layer that would show the common pressures runs, and the pressures a resident sees come
   from exactly one mapping -- so there is no way to show a common systolic beside a legacy diastolic;
2. the test-only approval used to exercise the transaction end to end cannot exist in production: nothing
   in the repository writes to ``runtime_authority.APPROVED_SNAPSHOTS``, no artifact is created and the
   Decision File records no approval;
3. every failure a future experiment could hit stops it visibly, with nothing committed.

What P3-17 does NOT do: wire authority into ``app.py``. A real "the app displays the common pressures" path
would need that call site, and this authorization forbids it. The test therefore drives the application's
own render path with the exact mapping a commit produces, which is the strongest claim available without
crossing the boundary -- and it is also how P3-17 found that the displayed MAP is derived by the app from
the committed SBP and DBP rather than taken from the common core.
"""
import ast
import json
import tempfile
from copy import deepcopy
from pathlib import Path

import pytest

import runtime_authority as ra
import runtime_authority_store as store
import runtime_shadow as rs

ROOT = Path(__file__).resolve().parent
CASE = "gi_bleed_57m"
#: A digest-shaped value. P3-17 found that passing the same placeholder twice satisfied the
#: reproducibility check, so ``validate`` now requires two sha256-shaped digests.
DIGEST = "a" * 64
OTHER_DIGEST = "b" * 64
#: The TEST-ONLY approval. It approves no clinical magnitude: its parameter is a placeholder, and the
#: field that matters is the binding to the parameter point the shadow layer actually ran.
TEST_ONLY_SNAPSHOT = {"id": "test_only_pressure_point",
                      "approved_by_faculty": True,
                      "decision": "NOBODY: test-only injection, approves nothing",
                      "runtime_parameter_snapshot_id": rs.PARAMETER_SNAPSHOT_ID,
                      "parameters": {"test_only_placeholder": 1.0}}
STORE_DIR = tempfile.mkdtemp(prefix="phase3-authority-e2e-")
BEST = {ra.AUTHORITY_FLAG: ra.MODE_LIMITED_COMMON_AUTHORITY,
        ra.SNAPSHOT_FLAG: TEST_ONLY_SNAPSHOT["id"],
        ra.ENVIRONMENT_FLAG: "development"}

@pytest.fixture(autouse=True)
def _pinned_store(monkeypatch):
    """No authority test may write into an ambient faculty store (P3-28 review).

    The store flag is pinned to this file's own temporary directory for every test here, so a machine
    that exports ``MRS_PHASE3_AUTHORITY_STORE`` cannot receive a record from the repository's own suite.
    """
    monkeypatch.setenv(store.STORE_FLAG, STORE_DIR)



@pytest.fixture
def injected(monkeypatch):
    """The test-only approval: a snapshot that exists for this process and nowhere else.

    It goes into the PRIVATE mapping on purpose: P3-17 made the registry read-only from outside, so the
    only way to inject one is a name the production scan of ``test_e3`` watches. The process flags are
    set too, because a commit now re-evaluates the gate instead of trusting its own state field.
    """
    monkeypatch.setitem(ra._APPROVED_SNAPSHOT_POINTS, TEST_ONLY_SNAPSHOT["id"], TEST_ONLY_SNAPSHOT)
    for name, value in BEST.items():
        monkeypatch.setenv(name, value)
    for name in ra.PILOT_FLAGS + ra.PILOT_REQUIRED_ON:
        monkeypatch.delenv(name, raising=False)
    return TEST_ONLY_SNAPSHOT


@pytest.fixture(scope="module")
def gi_state():
    import pilot_acceptance
    return deepcopy(pilot_acceptance.Encounter(CASE).state)


@pytest.fixture(scope="module")
def candidate():
    """A real common pressure candidate: the committed point over a captured GI artifact."""
    import runtime_shadow_evidence as ev
    import runtime_shadow_families as fam
    from clinical_core import integration
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        import pilot_acceptance
        encounter = pilot_acceptance.Encounter(CASE)
        encounter.order("Give 1 litre of normal saline over 15 minutes. Reassess in 10 minutes.")
    session = encounter.shadow
    captured = session.runner.replay_input()
    replayed = fam.replay_shadow_encounter(captured)
    anchors, contributors, minutes, profile = integration.scenario_from_dict(captured.to_dict()["scenario"])
    derived = integration.run(anchors, contributors, minutes, profile).derived()[minutes]
    return {"minute": minutes, "candidate": {"sbp": derived.sbp, "dbp": derived.dbp, "map": derived.map},
            "artifact": captured.to_dict(), "replay": replayed, "state": deepcopy(encounter.state)}


def _cells(observable):
    import app
    return dict(app._vitals_cells(app.learner_vitals_snapshot({"observable": observable})))


# -- P3-17-1: the application layer --------------------------------------------------------------------

#: A literal for the app's own access gate, not a credential of anything: the gate is fail-closed and
#: refuses to render until a password is configured, so a deterministic app-layer test has to configure
#: one inside its own process. It is never written to a file and it unlocks nothing outside this test.
TEST_ONLY_PASSWORD = "test-only-not-a-real-credential"


def _app():
    """The app, past its access gate, with an encounter started. The repository's own runtime layer.

    Streamlit's ``AppTest`` is the supported way to drive it deterministically: the app renders
    server-side, so a browser would add a rendering engine and no further claim about where the numbers
    come from. That is why ``UI_E2E_DEFERRED_BEFORE_AUTHORITY`` is answered here without automation.
    """
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file("app.py", default_timeout=300)
    at.secrets["APP_PASSWORD"] = TEST_ONLY_PASSWORD
    at.session_state["_shared_access_granted"] = True
    at.run()
    assert not at.exception, [str(item.value)[:300] for item in at.exception]
    begin = [button for button in at.button if "Begin" in button.label or "Comenzar" in button.label]
    assert begin, [button.label for button in at.button]
    begin[0].click().run()
    assert not at.exception, [str(item.value)[:300] for item in at.exception]
    return at


def _shown_pressures(at):
    """The blood pressure the resident can read on the screen, taken from the rendered output."""
    observable = at.session_state["state"]["observable"]
    needle = f'{observable.get("sbp")}/{observable.get("dbp")}'
    return needle, [item.value for item in at.markdown if needle in str(item.value)]


def test_e1_the_application_renders_the_authoritative_pressures_through_its_own_layer():
    at = _app()
    assert at.session_state["state"]["observable"].get("sbp") is not None
    needle, showing = _shown_pressures(at)
    assert showing, f"the screen does not show {needle}"
    assert any("mrs-vitals-grid" in str(item.value) for item in at.markdown), "no vitals grid rendered"


def test_e2_the_resident_sees_the_pressures_of_exactly_one_mapping(gi_state):
    legacy = _cells(gi_state["observable"])
    assert "BP · MAP" in legacy or any("BP" in key for key in legacy), sorted(legacy)
    observable = dict(gi_state["observable"])
    cell = [value for key, value in legacy.items() if "BP" in key][0]
    assert f'{observable["sbp"]}/{observable["dbp"]}' in cell, cell
    # The displayed mean pressure is the application's function of the two it shows beside it.
    import app
    snapshot = app.learner_vitals_snapshot(gi_state)
    assert snapshot["map"] == int(round((float(observable["sbp"]) + 2.0 * float(observable["dbp"])) / 3.0))


# -- P3-17-2: the test-only approval -------------------------------------------------------------------

def test_e3_the_test_only_approval_cannot_exist_in_production(injected, gi_state):
    assert ra.approved_snapshot(TEST_ONLY_SNAPSHOT["id"]) == TEST_ONLY_SNAPSHOT
    assert ra.gate(gi_state, environ=BEST, unsupported=()).granted, "the injection is what makes the gate grant"
    # Nothing in the repository writes the registry, so a deployment has no way to fill it. P3-17 found
    # this scan only saw a BARE name: ``ra.APPROVED_SNAPSHOTS["x"] = ...``, ``.update(...)`` and
    # ``.setdefault(...)`` through the module went unseen, and it never looked below the top directory.
    watched = ("APPROVED_SNAPSHOTS", "_APPROVED_SNAPSHOT_POINTS")

    def watched_name(node):
        """The watched identifier this expression ends in, whatever it is qualified by."""
        if isinstance(node, ast.Name):
            return node.id if node.id in watched else None
        if isinstance(node, ast.Attribute):
            return node.attr if node.attr in watched else None
        return None

    writers = []
    for path in sorted(ROOT.rglob("*.py")):
        relative = path.relative_to(ROOT)
        if path.name.startswith("test_") or relative.parts[0] in {".venv", ".claude", "__pycache__"}:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            targets = list(getattr(node, "targets", ())) + ([node.target] if
                                                            isinstance(node, (ast.AugAssign,
                                                                              ast.AnnAssign)) else [])
            for target in targets:
                if isinstance(target, ast.Subscript) and watched_name(target.value):
                    writers.append(f"{relative.as_posix()}:{node.lineno}")
                if watched_name(target) and relative.as_posix() != "runtime_authority.py":
                    writers.append(f"{relative.as_posix()}:{node.lineno}")
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                    and watched_name(node.func.value) \
                    and node.func.attr in ("update", "setdefault", "__setitem__", "pop", "clear",
                                           "popitem"):
                writers.append(f"{relative.as_posix()}:{node.lineno}")
    assert writers == [], writers
    # The scan has to be able to see those forms: three real writes, three hits.
    probe = ast.parse("import runtime_authority as ra\n"
                      "ra.APPROVED_SNAPSHOTS['x'] = {}\n"
                      "ra.APPROVED_SNAPSHOTS.update({})\n"
                      "runtime_authority._APPROVED_SNAPSHOT_POINTS.setdefault('y', {})\n")
    seen = []
    for node in ast.walk(probe):
        for target in getattr(node, "targets", ()):
            if isinstance(target, ast.Subscript) and watched_name(target.value):
                seen.append(node.lineno)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and watched_name(node.func.value) and node.func.attr in ("update", "setdefault"):
            seen.append(node.lineno)
    assert sorted(seen) == [2, 3, 4], seen
    # No artifact, and no approval recorded anywhere.
    assert not list(ROOT.glob("**/*authority_snapshot*.json"))
    decision_file = (ROOT / "docs" / "COLA_DECISIONES_AI_ADVISOR.md").read_text(encoding="utf-8")
    assert TEST_ONLY_SNAPSHOT["id"] not in decision_file
    assert "FACULTY_APPROVED_AUTHORITY_SNAPSHOT" not in decision_file


def test_e4_without_the_injection_the_gate_refuses_again(gi_state):
    assert ra.APPROVED_SNAPSHOTS == {}, "the injection must not survive its own test"
    assert ra._APPROVED_SNAPSHOT_POINTS == {}, "nor in the private mapping it was injected into"
    assert not ra.gate(gi_state, environ=BEST, unsupported=()).granted


# -- P3-17-3: atomicity at the display boundary --------------------------------------------------------

def test_e5_a_valid_candidate_shows_three_common_pressures_and_nothing_else_moves(injected, candidate):
    state = deepcopy(candidate["state"])
    transaction = ra.AuthorityTransaction.open_for(state, environ=BEST, minute=candidate["minute"], unsupported=())
    assert transaction is not None, "with the test-only approval the transaction opens"
    transaction.capture(state).compute({name: round(value) for name, value in
                                        candidate["candidate"].items()},
                                       dict(state["observable"]))
    assert transaction.validate(replay_digest=DIGEST, expected_digest=DIGEST,
                                unsupported=()), transaction.failures
    prepared = transaction.commit(state)
    before, after = _cells(state["observable"]), _cells(prepared["observable"])
    bp_before = [value for key, value in before.items() if "BP" in key][0]
    bp_after = [value for key, value in after.items() if "BP" in key][0]
    assert bp_after != bp_before
    assert f'{round(candidate["candidate"]["sbp"])}/{round(candidate["candidate"]["dbp"])}' in bp_after
    # Every other cell the resident sees is the legacy one: the commit touched the pressure domain only.
    for key in before:
        if "BP" in key:
            continue
        assert before[key] == after[key], key
    # ``map`` is written as the DISPLAY derives it from the two committed pressures (P3-19 review).
    assert sorted(transaction.committed) == ["dbp", "map", "sbp"]
    assert prepared["observable"]["map"] == ra.derived_map(prepared["observable"]["sbp"],
                                                           prepared["observable"]["dbp"])


def test_e6_a_refused_candidate_shows_the_legacy_pressures(injected, candidate):
    state = deepcopy(candidate["state"])
    transaction = ra.AuthorityTransaction.open_for(state, environ=BEST, minute=candidate["minute"], unsupported=())
    transaction.capture(state).compute({name: round(value) for name, value in
                                        candidate["candidate"].items()}, dict(state["observable"]))
    assert not transaction.validate(replay_digest=DIGEST, expected_digest=OTHER_DIGEST,
                                    unsupported=())
    with pytest.raises(ra.AuthorityRefused):
        transaction.commit(state)
    assert _cells(state["observable"]) == _cells(candidate["state"]["observable"])
    assert transaction.committed == ()


@pytest.mark.parametrize("failure,expected", [
    ({"invariants_hold": False}, "invariants_hold"),
    ({"failures": (rs.ShadowFailure(1, "core", "CoreInvariantError", "x", rs.UNEXPECTED),)},
     "no_core_failure"),
    ({"failures": (rs.ShadowFailure(1, "core", "UnresolvedBoundary", "x", rs.BOUNDARY),)},
     "no_unresolved_boundary"),
    ({"unsupported": ("norepinephrine",)}, "supported_management"),
    ({"legacy_arrest": True}, "no_legacy_arrest"),
    ({"replay_digest": DIGEST, "expected_digest": OTHER_DIGEST}, "minute_reproducible"),
    ({"replay_digest": "same", "expected_digest": "same"}, "minute_reproducible"),
    ({"unsupported": None}, "supported_management"),
])
def test_e7_every_injected_failure_stops_the_experiment_visibly(injected, candidate, failure, expected):
    state = deepcopy(candidate["state"])
    transaction = ra.AuthorityTransaction.open_for(state, environ=BEST, minute=candidate["minute"], unsupported=())
    transaction.capture(state).compute({name: round(value) for name, value in
                                        candidate["candidate"].items()}, dict(state["observable"]))
    arguments = {"replay_digest": DIGEST, "expected_digest": DIGEST, "unsupported": (),
                 **failure}
    assert not transaction.validate(**arguments)
    assert expected in transaction.failures, transaction.failures
    artifact = ra.rollback_artifact(transaction, reason=f"injected {expected}")
    assert artifact["committed"] == [] and artifact["failure_policy"] == ra.FAILURE_POLICY
    assert artifact["precommit_authoritative_state"]["observable"] == state["observable"]
    assert _cells(state["observable"]) == _cells(candidate["state"]["observable"])


def test_e8_an_invalid_snapshot_id_opens_nothing(injected, gi_state):
    environ = {**BEST, ra.SNAPSHOT_FLAG: "a name nobody approved"}
    assert not ra.gate(gi_state, environ=environ, unsupported=()).granted
    assert ra.AuthorityTransaction.open_for(gi_state, environ=environ, unsupported=()) is None


# -- P3-17-5: the pilot ---------------------------------------------------------------------------------

def test_e9_the_pilot_cannot_run_authority_even_with_the_test_only_approval(injected, gi_state):
    import pilot_acceptance
    import pilot_freeze
    for flag in ra.PILOT_FLAGS:
        decision = ra.gate(gi_state, environ={**BEST, flag: "1"}, unsupported=())
        assert not decision.granted and not decision.conditions["no_pilot"], flag
        assert ra.AuthorityTransaction.open_for(gi_state, environ={**BEST, flag: "1"}, unsupported=()) is None
    # P3-17: those two flag names exist nowhere else in the repository, so on their own they protected
    # nothing -- a real pilot deployment satisfied the condition. The anchor is the pilot's own freeze.
    real_pilot = {name: "1" for name in ra.pilot_deployment_markers()}
    assert real_pilot, "the pilot's required runtime flags must be readable from its freeze"
    assert set(real_pilot) <= set(pilot_freeze.RUNTIME_FLAGS)
    decision = ra.gate(gi_state, environ={**BEST, **real_pilot}, unsupported=())
    assert not decision.granted and not decision.conditions["no_pilot"], decision.to_dict()
    assert ra.AuthorityTransaction.open_for(gi_state, environ={**BEST, **real_pilot},
                                            unsupported=()) is None
    # The flags not naming the authority is hygiene, not the protection: the condition above is.
    for name in ("pilot_freeze.py", "tools_pilot_preflight.py", "pilot_acceptance.py",
                 "docs/RUNBOOK_PILOTO.md"):
        path = ROOT / name
        if path.exists():
            text = path.read_text(encoding="utf-8")
            for flag in (ra.AUTHORITY_FLAG, ra.SNAPSHOT_FLAG, ra.ENVIRONMENT_FLAG):
                assert flag not in text, (name, flag)
    assert rs.FLAG not in pilot_freeze.RUNTIME_FLAGS
    with __import__("runtime_shadow_evidence").shadow(None):
        assert pilot_acceptance.Encounter(CASE).shadow is None


# -- P3-17-6: persistence -------------------------------------------------------------------------------

def test_e10_the_authority_record_is_separate_from_the_production_persistence(injected, candidate):
    import management_trace_store
    state = deepcopy(candidate["state"])
    transaction = ra.AuthorityTransaction.open_for(state, environ=BEST, minute=candidate["minute"], unsupported=())
    transaction.capture(state).compute({name: round(value) for name, value in
                                        candidate["candidate"].items()}, dict(state["observable"]))
    record = transaction.record()
    for key in ("snapshot", "candidate", "legacy_counterfactual", "ownership", "versions", "state"):
        assert key in record, key
    assert record["versions"]["phase2_digest"] == rs.PHASE2_DIGEST
    assert record["versions"]["phase3_layer_digest"] and record["versions"]["golden_digest"]
    # The production payload is built from a declared list of keys; an authority record cannot ride along.
    payload = management_trace_store.analysis_payload_from_session(
        {"state": state, "history": [], "events": [], "management_trace": [],
         "phase3_authority": record, "phase3_shadow": "not a payload key"})
    serialized = json.dumps(payload, default=str)
    assert "phase3_authority" not in serialized and "limited_common_authority" not in serialized
    assert "test_only_pressure_point" not in serialized
    # And the narrow truth, stated so nobody reads more into it than it proves: the payload is an
    # allowlist of top-level keys, and two of those keys are copied VERBATIM. A record nested inside the
    # closed trace or the closed events WOULD travel, so the future call site must never put one there.
    nested = management_trace_store.analysis_payload_from_session(
        {"state": state, "history": [], "events": [], "management_trace": [],
         "encounter_closed_trace": [{"authority_record": record}]})
    assert "limited_common_authority" in json.dumps(nested, default=str), \
        "the closed trace is copied verbatim: this is a constraint on the call site, not a guarantee"
    # What the harness does guarantee today: it writes nothing anywhere.
    source = (ROOT / "runtime_authority.py").read_text(encoding="utf-8")
    # ``json.dumps`` serializes a payload for a digest; the writers are what must be absent.
    for forbidden in ("open(", "write_text", "write_bytes", "json.dump(", "management_trace_store",
                      "st.session_state", "mkdir", "shutil"):
        assert forbidden not in source, forbidden


# -- P3-17-7: replay ------------------------------------------------------------------------------------

def test_e11_the_pressure_domain_reproduces_from_the_artifact(candidate):
    import runtime_shadow_families as fam
    first = fam.replay_shadow_encounter(candidate["artifact"])
    second = fam.replay_shadow_encounter(json.loads(json.dumps(candidate["artifact"], default=str)))
    minute = candidate["minute"]
    pressures = [{name: round(float(item["derived"][name]), 9) for name in ("sbp", "dbp", "map")}
                 for item in (first["results"][minute], second["results"][minute])]
    assert pressures[0] == pressures[1]
    assert pressures[0]["sbp"] == round(float(candidate["candidate"]["sbp"]), 9)
    digests = [item["state_digest"] for item in first["results"]]
    assert digests == [item["state_digest"] for item in second["results"]]
    assert first["final_digest"] == second["final_digest"]


def test_e12_no_production_configuration_can_reach_authority_after_these_tests(gi_state):
    """The last word: the injection is gone, and the repository is where it was."""
    assert ra.APPROVED_SNAPSHOTS == {}
    assert ra.unreachable_because()
    assert ra.mode(gi_state, environ=BEST) == ra.MODE_LEGACY
    assert rs.COMMON_CORE_RUNTIME_AUTHORITY is False


# -- P3-17-1 and P3-17-3 together: the application path under a test-only authority -----------------------

def _app_on_the_gi_encounter(gi_state):
    """The app's own render path, on the allowlisted GI encounter the authority family names.

    The app's first encounter is not a GI case (``test_e16``), and the authority gate derives the family
    and the case FROM THE STATE since P3-17, so a GI state is what an allowlisted encounter looks like.
    """
    at = _app()
    at.session_state["state"] = deepcopy(gi_state)
    at.run()
    assert not at.exception, [str(item.value)[:300] for item in at.exception]
    return at


def test_e13_a_committed_authority_mapping_changes_the_pressures_on_the_screen(injected, gi_state):
    """The strongest end-to-end claim available without wiring authority into the app.

    The app reads the pressures from the authoritative observable, which is exactly where a future commit
    would write. So the test commits a transaction, puts its prepared mapping where the app reads, and
    re-renders: the screen shows the common pressures, the mean pressure the app derives from them, and
    no other vital moved.
    """
    at = _app_on_the_gi_encounter(gi_state)
    state = deepcopy(at.session_state["state"])
    legacy_needle, legacy_showing = _shown_pressures(at)
    assert legacy_showing
    transaction = ra.AuthorityTransaction(minute=int(state.get("sim_time") or 0),
                                          case_id=ra.AUTHORITY_CASES[0],
                                          snapshot=TEST_ONLY_SNAPSHOT)
    transaction.capture(state).compute({"sbp": 101, "dbp": 61, "map": 74}, dict(state["observable"]))
    assert transaction.validate(replay_digest=DIGEST, expected_digest=DIGEST,
                                unsupported=()), transaction.failures
    prepared = transaction.commit(state)
    at.session_state["state"] = prepared
    at.run()
    assert not at.exception, [str(item.value)[:300] for item in at.exception]
    common_needle, common_showing = _shown_pressures(at)
    assert common_needle == "101/61" and common_showing, common_needle
    screen = "\n".join(str(item.value) for item in at.markdown)
    assert legacy_needle not in screen, "the legacy pressure is still on the screen beside the common one"
    # The mean pressure is written as the DISPLAY derives it from the two committed pressures, so the
    # state, the screen and the management trace carry the same number (P3-19 review).
    import app
    assert app.learner_vitals_snapshot(prepared)["map"] == int(round((101.0 + 2.0 * 61.0) / 3.0))
    assert prepared["observable"]["map"] == app.learner_vitals_snapshot(prepared)["map"]
    assert prepared["observable"]["map"] != state["observable"].get("map")
    # Nothing else the resident reads moved: the commit wrote the two common pressures and nothing more.
    for key, value in state["observable"].items():
        if key in ("sbp", "dbp", "map"):
            continue
        assert prepared["observable"][key] == value, key


def test_e14_a_refused_transaction_leaves_the_screen_as_the_legacy_engine_left_it(injected, gi_state):
    at = _app_on_the_gi_encounter(gi_state)
    state = deepcopy(at.session_state["state"])
    legacy_needle, _showing = _shown_pressures(at)
    transaction = ra.AuthorityTransaction(minute=int(state.get("sim_time") or 0),
                                          case_id=ra.AUTHORITY_CASES[0], snapshot=TEST_ONLY_SNAPSHOT)
    transaction.capture(state).compute({"sbp": 101, "dbp": 61, "map": 74}, dict(state["observable"]))
    assert not transaction.validate(replay_digest=DIGEST, expected_digest=OTHER_DIGEST,
                                    unsupported=())
    with pytest.raises(ra.AuthorityRefused):
        transaction.commit(state)
    at.run()
    assert not at.exception
    still, showing = _shown_pressures(at)
    assert still == legacy_needle and showing, (still, legacy_needle)


def test_e16_the_apps_own_encounter_is_not_an_authority_case_and_cannot_be_committed_to(injected):
    """The family restriction holds at the application layer, from the state and not from a caller."""
    at = _app()
    state = deepcopy(at.session_state["state"])
    assert str(state.get("engine_family")) != ra.AUTHORITY_FAMILY, state.get("engine_family")
    decision = ra.gate(state, environ=BEST, unsupported=())
    assert not decision.granted and not decision.conditions["family_and_case"], decision.to_dict()
    assert ra.AuthorityTransaction.open_for(state, environ=BEST, unsupported=()) is None
    # And declaring an allowlisted case over this state does not buy the commit anything.
    transaction = ra.AuthorityTransaction(minute=int(state.get("sim_time") or 0),
                                          case_id=ra.AUTHORITY_CASES[0], snapshot=TEST_ONLY_SNAPSHOT)
    transaction.capture(state).compute({"sbp": 101, "dbp": 61, "map": 74}, dict(state["observable"]))
    assert transaction.validate(replay_digest=DIGEST, expected_digest=DIGEST, unsupported=())
    with pytest.raises(ra.AuthorityRefused) as refused:
        transaction.commit(state)
    assert "refuses at commit" in str(refused.value)
    before = _shown_pressures(at)
    at.run()
    assert _shown_pressures(at) == before


def test_e15_the_test_only_password_unlocks_nothing_outside_this_process():
    """It is a literal in a test, not a credential: the repository holds no password and no secrets file."""
    assert TEST_ONLY_PASSWORD not in (ROOT / "app.py").read_text(encoding="utf-8")
    assert not (ROOT / ".streamlit" / "secrets.toml").exists()
    for path in list(ROOT.glob("*.py")) + list(ROOT.glob("docs/*.md")):
        if path.name.startswith("test_"):
            continue
        assert TEST_ONLY_PASSWORD not in path.read_text(encoding="utf-8"), path.name
