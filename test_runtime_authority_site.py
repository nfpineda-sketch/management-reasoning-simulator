"""P3-19: the production call site of a future authority exists, and it is DORMANT.

Two claims, and every test defends one of them.

The first is inertness. ``runtime_authority.site_for`` is the only thing ``app.py`` calls, it returns None
in every configuration this repository can produce, the refusal is remembered per encounter so the gate is
not re-evaluated turn after turn, and the application gains no authority state at all. The call site exists
and the encounter runs exactly as it did.

The second is completeness. With a TEST-ONLY approval injected for one process, the same call site runs a
real minute of a real GI encounter: it takes the candidate from the shadow runner (the one place that
advances the common core), computes every digest itself over a canonical serialization, validates, commits
the two common pressures together, records a provenance row that a reader could reproduce the minute from,
and reproduces it from the serialized artifact alone. A failure halts the encounter's authority visibly and
commits nothing: there is no minute-by-minute fallback to the legacy engine.
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
DIGEST = "a" * 64
TEST_ONLY_SNAPSHOT = {"id": "test_only_site_point",
                      "approved_by_faculty": True,
                      "decision": "TEST ONLY: exists inside one test session, approves nothing",
                      "runtime_parameter_snapshot_id": rs.PARAMETER_SNAPSHOT_ID,
                      "parameters": {"test_only_placeholder": 1.0}}
#: Every flag a faculty experiment would set. The shadow flag is one of them since the P3-19 review:
#: authority has no candidate of its own, so the common core must be running beside the engine.
#: This file's own artifact store, outside the repository. Since P3-26 an experiment does not start
#: without one: a hard failure that nothing can record is not a visible hard failure.
STORE_DIR = tempfile.mkdtemp(prefix="phase3-authority-site-")
BEST = {ra.AUTHORITY_FLAG: ra.MODE_LIMITED_COMMON_AUTHORITY,
        ra.SNAPSHOT_FLAG: TEST_ONLY_SNAPSHOT["id"],
        ra.ENVIRONMENT_FLAG: "development",
        rs.FLAG: rs.MODE_SHADOW_COMPARE,
        store.STORE_FLAG: STORE_DIR}

@pytest.fixture(autouse=True)
def _pinned_store(monkeypatch):
    """No authority test may write into an ambient faculty store (P3-28 review).

    The store flag is pinned to this file's own temporary directory for every test here, so a machine
    that exports ``MRS_PHASE3_AUTHORITY_STORE`` cannot receive a record from the repository's own suite.
    """
    monkeypatch.setenv(store.STORE_FLAG, STORE_DIR)



@pytest.fixture
def approved(monkeypatch):
    """The test-only approval and the process flags, withdrawn when the test ends."""
    monkeypatch.setitem(ra._APPROVED_SNAPSHOT_POINTS, TEST_ONLY_SNAPSHOT["id"], TEST_ONLY_SNAPSHOT)
    for name, value in BEST.items():
        monkeypatch.setenv(name, value)
    for name in ra.PILOT_FLAGS + ra.PILOT_REQUIRED_ON:
        monkeypatch.delenv(name, raising=False)
    return TEST_ONLY_SNAPSHOT


@pytest.fixture(scope="module")
def gi_turn():
    """A real GI encounter with one settled turn and its live shadow session: the runtime's own objects."""
    import pilot_acceptance
    import runtime_shadow_evidence as ev
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = pilot_acceptance.Encounter(CASE)
        arrival = deepcopy(encounter.state)
        encounter.order("Give 1 litre of normal saline over 15 minutes. Reassess in 10 minutes.")
    return {"arrival": arrival, "state": deepcopy(encounter.state), "session": encounter.shadow,
            "ran": [dict(order) for order in encounter.entries[-1]["orders"]]}


def _site(gi_turn, **kwargs):
    return ra.open_site(gi_turn["arrival"], environ=BEST, **kwargs)


def _one_minute(site, gi_turn, ran=None):
    return site.minute(gi_turn["arrival"], deepcopy(gi_turn["state"]), gi_turn["session"],
                       gi_turn["ran"] if ran is None else ran, "t0")


# -- P3-19A, P3-19B: inertness -------------------------------------------------------------------------

def test_d1_the_site_refuses_in_every_configuration_but_the_authorized_development_one(gi_turn):
    """P3-40 registered one development-only approval, so "every configuration" is now too strong.

    What the site still refuses is everything these tests can produce WITHOUT naming that approval, and
    everything that names it outside its declared scope. The authorized development configuration is
    exercised by the P3-41 experiment and by ``test_d26``.
    """
    assert sorted(ra.APPROVED_SNAPSHOTS) == ["gi_pressure_committed"]
    for environ in ({}, {ra.AUTHORITY_FLAG: ra.MODE_LIMITED_COMMON_AUTHORITY}, BEST,
                    {**BEST, ra.ENVIRONMENT_FLAG: "production"},
                    {**BEST, ra.PILOT_FLAGS[0]: "1"},
                    {**BEST, ra.SNAPSHOT_FLAG: "a name nobody approved"},
                    {**BEST, ra.SNAPSHOT_FLAG: "gi_pressure_committed",
                     ra.ENVIRONMENT_FLAG: "production"},
                    {**BEST, ra.SNAPSHOT_FLAG: "gi_pressure_committed", ra.PILOT_FLAGS[0]: "1"},
                    {**BEST, ra.SNAPSHOT_FLAG: "gi_pressure_committed",
                     store.STORE_FLAG: ""}):
        assert ra.open_site(gi_turn["arrival"], environ=environ) is None, environ
        assert ra.site_for(gi_turn["arrival"], {}, environ=environ) is None, environ
    assert ra.unreachable_because()


def test_d2_a_refused_encounter_does_not_re_evaluate_the_gate_every_turn(gi_turn, monkeypatch):
    """The production path pays one dictionary lookup, not a 141-file digest, on every turn."""
    calls = []
    monkeypatch.setattr(ra, "gate", lambda *a, **k: calls.append(1) or ra.AuthorityGate({}, ()))
    store = {}
    for _ in range(5):
        assert ra.site_for(gi_turn["arrival"], store, environ={}) is None
    assert calls == [], "the flag is read first, so a refusal costs no digest at all"
    assert store.get(ra.SITE_REFUSED_KEY) is None or store[ra.SITE_KEY] is None
    # With the flag set but nothing else, the gate is consulted ONCE for the encounter.
    calls.clear()
    store = {}
    for _ in range(5):
        assert ra.site_for(gi_turn["arrival"], store,
                           environ={ra.AUTHORITY_FLAG: ra.MODE_LIMITED_COMMON_AUTHORITY}) is None
    assert len(calls) <= 1, calls


def test_d3_the_application_orchestrates_and_decides_nothing():
    """``app.py`` holds the call, not the logic: the block is three statements and no condition of its own."""
    tree = ast.parse((ROOT / "app.py").read_text(encoding="utf-8"))
    helper = next(node for node in ast.walk(tree)
                  if isinstance(node, ast.FunctionDef) and node.name == "_runtime_authority_site")
    body = [node for node in helper.body if not isinstance(node, ast.Expr)
            or not isinstance(node.value, ast.Constant)]
    assert len(body) == 2 and isinstance(body[-1], ast.Return), ast.unparse(helper)
    assert ast.unparse(body[-1]) == "return runtime_authority.site_for(st.session_state.state, st.session_state)"
    # The variable the block tests is bound by exactly one call, and it is the helper above.
    bindings = [ast.unparse(node) for node in ast.walk(tree) if isinstance(node, ast.Assign)
                and [target for target in node.targets
                     if isinstance(target, ast.Name) and target.id == "_authority"]]
    assert bindings == ["_authority = _runtime_authority_site()"], bindings
    blocks = [node for node in ast.walk(tree) if isinstance(node, ast.If)
              and ast.unparse(node.test) == "_authority is not None"]
    # P3-46 split the provenance from the commit: TWO blocks, and the second one runs after the order
    # pipeline settles each order's fate. The commit itself did not move.
    assert len(blocks) == 2, [ast.unparse(node.test) for node in blocks]
    # P3-271 (declared adaptation): the commit now receives the SETTLED ledger and is followed, in this order, by the artifact, the turn's verdict and only then the installation of the prepared state;
    # the provenance block ends with the verdict too. The two blocks and everything they decide are unchanged.
    assert [ast.unparse(node) for node in blocks[0].body] == [
        "_prepared = _authority.minute(_shadow_before, st.session_state.state, _shadow, run_actions, submission_id, settled=_ledger.snapshot(turn.get('orders') or []))",
        "st.session_state.phase3_authority_artifact = _authority.artifact()",
        "_authority_turn_check()",
        "if _prepared is not None:\n    st.session_state.state = _prepared",
    ], [ast.unparse(node) for node in blocks[0].body]
    assert [ast.unparse(node) for node in blocks[1].body] == [
        "_authority.settle_provenance(submission_id, _ledger.snapshot(turn.get('orders') or []))",
        "st.session_state.phase3_authority_artifact = _authority.artifact()",
        "_authority_turn_check()",
    ], [ast.unparse(node) for node in blocks[1].body]
    # And the order is the one the repair depends on (P3-271): the pipeline's settlement, THEN the commit, then the provenance. The authority judges the settled lineage and classes BEFORE it commits, so
    # a contradiction the settlement reveals is a refusal and never a commit that has to be taken back (a committed minute is never rewritten). A reader can check it here instead of trusting a comment.
    executes = [node.lineno for node in ast.walk(tree) if isinstance(node, ast.Call) and ast.unparse(node.func) == "execute_bundle" and node.lineno < blocks[0].lineno]
    settles = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
               and ast.unparse(node.func) == "_order_pipeline.settle"
               and max(executes) < node.lineno < blocks[0].lineno]
    assert len(executes) == 1 and len(settles) == 1, "exactly one settlement stands between the engine's turn and the commit"
    assert not [node for node in ast.walk(tree) if isinstance(node, ast.Call) and ast.unparse(node.func) == "_order_pipeline.settle" and node.lineno > blocks[0].lineno], "and none after it"
    # And the site is dropped with the encounter, like the shadow session, by the layer's own names
    # rather than by literals the app could get wrong.
    reset = next(node for node in ast.walk(tree)
                 if isinstance(node, ast.FunctionDef) and node.name == "reset_session")
    dropped = ast.unparse(reset)
    for name in ("SITE_KEY", "SITE_REFUSED_KEY", "ARTIFACT_KEY"):
        assert name in dropped, name
    assert (ra.SITE_KEY, ra.SITE_REFUSED_KEY, ra.ARTIFACT_KEY) == (
        "phase3_authority_site", "phase3_authority_refused_for", "phase3_authority_artifact")


def test_d4_the_running_application_gains_no_authority_state():
    """The real app, one encounter: no site, no artifact, nothing to clean up."""
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file("app.py", default_timeout=300)
    at.secrets["APP_PASSWORD"] = "test-only-not-a-real-credential"
    at.session_state["_shared_access_granted"] = True
    at.run()
    begin = [button for button in at.button if "Begin" in button.label or "Comenzar" in button.label]
    begin[0].click().run()
    assert not at.exception, [str(item.value)[:300] for item in at.exception]
    assert at.session_state.get("phase3_authority_artifact") is None
    assert at.session_state.get(ra.SITE_KEY) is None
    assert ra.site_for(at.session_state["state"], {}) is None


# -- P3-19A: the mode is decided once ------------------------------------------------------------------

def test_d5_the_mode_is_decided_once_at_the_arrival(gi_turn, approved):
    assert _site(gi_turn) is not None, "with the test-only approval the site opens"
    midway = {**deepcopy(gi_turn["arrival"]), "sim_time": 20}
    assert ra.open_site(midway, environ=BEST) is None, "a site cannot open mid-encounter"
    assert ra.MODE_DECIDED_AT == "encounter_start"


def test_d6_a_site_belongs_to_one_encounter(gi_turn, approved):
    site = _site(gi_turn)
    assert site.is_for(gi_turn["arrival"]) and site.is_for(gi_turn["state"])
    # Another case is another encounter: the certified case id comes from the bank variant being played.
    other = deepcopy(gi_turn["arrival"])
    other["encounter_spec"] = {**dict(other.get("encounter_spec") or {}), "variant_id": "gi_bleed_72f"}
    assert not site.is_for(other)
    # And the clock going backwards, or back to zero after this site advanced, is another encounter too.
    assert not site.is_for({**deepcopy(gi_turn["state"]), "sim_time": 0}) or not site.records
    prepared = _one_minute(site, gi_turn)
    assert prepared is not None and site.minutes_committed
    assert not site.is_for(gi_turn["arrival"]), "a committed site does not accept a fresh arrival"
    store = {ra.SITE_KEY: site}
    assert ra.site_for(gi_turn["arrival"], store, environ=BEST) is not site


# -- P3-19C, P3-19D, P3-19E: one real minute -----------------------------------------------------------

def test_d7_one_authority_minute_commits_the_pressure_domain_and_nothing_else(gi_turn, approved):
    state = deepcopy(gi_turn["state"])
    site = _site(gi_turn)
    prepared = site.minute(gi_turn["arrival"], state, gi_turn["session"], gi_turn["ran"], "t0")
    assert prepared is not None and not site.halted, site.records
    record = site.records[-1]
    assert record["outcome"] == ra.COMMITTED
    assert sorted(record["committed"]) == ["dbp", "map", "sbp"]
    assert set(record["moved_fields"]) <= {"sbp", "dbp", "map"}
    for key, value in state["observable"].items():
        if key in ("sbp", "dbp", "map"):
            continue
        assert prepared["observable"][key] == value, key
    # The mean pressure written is the one the DISPLAY derives from the two committed pressures, not the
    # core's own mean: that is what keeps the state, the screen and the management trace agreeing.
    assert prepared["observable"]["map"] == ra.derived_map(prepared["observable"]["sbp"],
                                                           prepared["observable"]["dbp"])
    assert prepared["observable"]["map"] != record["common_candidate"]["map"] or \
        float(record["common_candidate"]["map"]).is_integer()
    assert state == deepcopy(gi_turn["state"]), "the state the caller passed in is never mutated"
    # The written pressures carry the legacy engine's own shape, so the display does not change its form.
    for name in ("sbp", "dbp", "map"):
        assert type(prepared["observable"][name]) is type(state["observable"][name]), name


def test_d8_the_provenance_record_carries_everything_a_reader_needs(gi_turn, approved):
    site = _site(gi_turn)
    assert _one_minute(site, gi_turn) is not None
    record = site.records[-1]
    for key in ("encounter_id", "case_id", "family", "minute", "mode", "environment", "snapshot_id",
                "snapshot", "phase2_closure_head", "phase2_digest", "phase3_versions",
                "authority_module", "action_kinds", "action_fates", "unsupported_actions",
                "input_digest", "candidate_digest", "replay_digest", "transaction_digest",
                "written_candidate", "written_digest", "common_candidate", "legacy_counterfactual",
                "state_digest", "divergence_classes", "validation_failures", "validation_passed",
                "committed", "outcome", "failure_reason", "failure_policy"):
        assert key in record, key
    assert record["phase2_digest"] == rs.PHASE2_DIGEST
    assert record["phase2_closure_head"] == rs.PHASE2_CLOSURE_HEAD
    assert record["snapshot_id"] == TEST_ONLY_SNAPSHOT["id"]
    assert record["case_id"] == CASE and record["family"] == "gi_bleed"
    assert record["mode"] == ra.MODE_LIMITED_COMMON_AUTHORITY
    assert record["legacy_counterfactual"]["sbp"] is not None
    assert all(len(record[key]) == 64 for key in ("input_digest", "candidate_digest",
                                                  "transaction_digest", "written_digest"))


def test_d9_the_site_computes_its_own_digests(gi_turn, approved):
    """P3-19D: there is no digest argument to trust, and the replay digest comes from the artifact."""
    import inspect
    parameters = set(inspect.signature(ra.AuthoritySite.minute).parameters)
    assert not {name for name in parameters if "digest" in name}, parameters
    site = _site(gi_turn)
    assert _one_minute(site, gi_turn) is not None
    record = site.records[-1]
    # The recorded digest is checked against the pressures read from the SESSION -- an independent
    # source -- and against a changed value, so the assertion is not the formula compared with itself.
    shadow_minute = [item for item in gi_turn["session"].minutes
                     if item.minute == record["minute"]][-1]
    assert record["candidate_digest"] == ra.digest_of(ra.pressure_point(shadow_minute.derived))
    moved = {**record["common_candidate"], "sbp": float(record["common_candidate"]["sbp"]) + 1.0}
    assert ra.digest_of(moved) != record["candidate_digest"]
    assert record["replay_digest"] == record["candidate_digest"], "live and replay must agree"
    assert record["transaction_digest"] == ra.digest_of(
        {"input": record["input_digest"], "candidate": record["candidate_digest"],
         "snapshot": record["snapshot_id"], "minute": record["minute"],
         "domain": list(ra.AUTHORITY_DOMAIN), "site": ra.SITE_VERSION})
    assert ra.canonical({"b": 1, "a": [2, 3]}) == '{"a":[2,3],"b":1}'
    assert ra.digest_of({"a": 1}) == ra.digest_of({"a": 1})


# -- P3-19F, P3-19G: unsupported actions and the hard fail ---------------------------------------------

@pytest.mark.parametrize("kind", ["norepinephrine", "anticoagulation", "aspirin", "something_new"])
def test_d10_an_unsupported_action_commits_nothing_and_halts(gi_turn, approved, kind):
    state = deepcopy(gi_turn["state"])
    site = _site(gi_turn)
    ran = list(gi_turn["ran"]) + [{"order_id": "t0:9", "type": kind, "fate": "EXECUTED"}]
    assert site.minute(gi_turn["arrival"], state, gi_turn["session"], ran, "t0") is None
    assert site.halted and ra.UNSUPPORTED_AUTHORITY_ACTION in site.halt_reason, site.halt_reason
    assert site.records[-1]["committed"] == [] and kind in site.records[-1]["unsupported_actions"]
    assert state == deepcopy(gi_turn["state"])


def test_d11_a_hard_failure_halts_the_encounter_for_good(gi_turn, approved):
    """No minute-by-minute fallback: authority that alternates with the legacy engine is not authority."""
    site = _site(gi_turn)
    broken = {**deepcopy(gi_turn["state"]), "sim_time": 9999}
    assert site.minute(gi_turn["arrival"], broken, gi_turn["session"], gi_turn["ran"], "t0") is None
    assert site.halted and ra.NO_COMMON_CANDIDATE in site.halt_reason
    # And a perfectly valid minute afterwards is refused, with the halt named.
    assert _one_minute(site, gi_turn) is None
    assert site.records[-1]["failure_reason"] == ra.SITE_HALTED
    assert site.minutes_committed == ()


def test_d12_an_out_of_domain_write_is_refused_by_the_site_itself(gi_turn, approved, monkeypatch):
    """Defence in depth: what reached the state is compared with what the contract allows to be owned."""
    site = _site(gi_turn)
    original = ra.AuthorityTransaction.commit

    def hostile(self, target, *, environ=None):
        prepared = dict(original(self, target, environ=environ))
        observable = dict(prepared["observable"])
        observable["hr"] = 42
        prepared["observable"] = observable
        return prepared

    monkeypatch.setattr(ra.AuthorityTransaction, "commit", hostile)
    state = deepcopy(gi_turn["state"])
    assert site.minute(gi_turn["arrival"], state, gi_turn["session"], gi_turn["ran"], "t0") is None
    assert site.halted and ra.OUT_OF_DOMAIN_WRITE in site.halt_reason
    assert "hr" in site.halt_reason
    assert state == deepcopy(gi_turn["state"])


def test_d13_an_unexpected_error_inside_the_site_never_reaches_the_caller(gi_turn, approved, monkeypatch):
    site = _site(gi_turn)
    monkeypatch.setattr(ra.AuthoritySite, "_artifact_input",
                        staticmethod(lambda session: (_ for _ in ()).throw(RuntimeError("boom"))))
    assert _one_minute(site, gi_turn) is None
    assert site.halted and "RuntimeError" in site.halt_reason
    assert site.records[-1]["outcome"] == ra.ABORTED


# -- P3-19I: the application layer, in its three reachable modes and its unreachable fourth -----------

def _app():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file("app.py", default_timeout=300)
    at.secrets["APP_PASSWORD"] = "test-only-not-a-real-credential"
    at.session_state["_shared_access_granted"] = True
    at.run()
    begin = [button for button in at.button if "Begin" in button.label or "Comenzar" in button.label]
    begin[0].click().run()
    assert not at.exception, [str(item.value)[:300] for item in at.exception]
    return at


def _shown(at):
    observable = at.session_state["state"]["observable"]
    needle = f'{observable.get("sbp")}/{observable.get("dbp")}'
    return needle, [item.value for item in at.markdown if needle in str(item.value)]


def test_d16_the_application_runs_legacy_and_shadow_and_cannot_run_authority(gi_turn, monkeypatch):
    """Three modes at the application layer. The fourth is the one no configuration can reach."""
    # LEGACY: nothing set. No site, no shadow session, and the screen is the engine's.
    at = _app()
    assert ra.site_for(at.session_state["state"], at.session_state) is None
    needle, showing = _shown(at)
    assert showing, needle
    # SHADOW_COMPARE: the shadow flag only. A session exists; the authority site still does not.
    monkeypatch.setenv(rs.FLAG, rs.MODE_SHADOW_COMPARE)
    assert rs.mode() == rs.MODE_SHADOW_COMPARE
    assert ra.site_for(at.session_state["state"], at.session_state) is None
    assert ra.mode(at.session_state["state"]) in (ra.MODE_SHADOW_COMPARE, ra.MODE_LEGACY)
    # LIMITED_COMMON_AUTHORITY: with every flag a deployment could set, and no approved snapshot.
    for name, value in BEST.items():
        monkeypatch.setenv(name, value)
    assert sorted(ra.APPROVED_SNAPSHOTS) == ["gi_pressure_committed"]
    assert ra.site_for(gi_turn["arrival"], {}) is None, \
        "BEST names the test-only id, which is not the registered approval"
    assert at.session_state.get("phase3_authority_artifact") is None


def test_d17_the_application_store_hands_the_site_its_own_minute(gi_turn, approved):
    """The app's own path, with the test-only approval: store handoff, commit, render, artifact."""
    at = _app()
    at.session_state["state"] = deepcopy(gi_turn["arrival"])
    at.run()
    assert not at.exception, [str(item.value)[:300] for item in at.exception]
    # The app's helper gets the site from exactly this call, with the session as the store.
    site = ra.site_for(at.session_state["state"], at.session_state)
    assert site is not None and at.session_state[ra.SITE_KEY] is site
    assert ra.site_for(at.session_state["state"], at.session_state) is site, "one site per encounter"
    # One minute, exactly as the call site runs it, and then the app renders the prepared state.
    at.session_state["state"] = deepcopy(gi_turn["state"])
    at.run()
    legacy_needle, legacy_showing = _shown(at)
    assert legacy_showing
    prepared = site.minute(gi_turn["arrival"], at.session_state["state"], gi_turn["session"],
                           gi_turn["ran"], "t0")
    assert prepared is not None, site.records
    at.session_state["state"] = prepared
    at.session_state["phase3_authority_artifact"] = site.artifact()
    at.run()
    assert not at.exception, [str(item.value)[:300] for item in at.exception]
    common_needle, common_showing = _shown(at)
    assert common_showing and common_needle != legacy_needle, (common_needle, legacy_needle)
    screen = "\n".join(str(item.value) for item in at.markdown)
    assert legacy_needle not in screen
    # The mean pressure the resident reads is the application's function of the two committed pressures.
    import app
    observable = prepared["observable"]
    assert app.learner_vitals_snapshot(prepared)["map"] == int(round(
        (float(observable["sbp"]) + 2.0 * float(observable["dbp"])) / 3.0))
    assert at.session_state["phase3_authority_artifact"]["minutes"][-1]["outcome"] == ra.COMMITTED


def test_d18_a_failed_minute_leaves_the_application_on_the_legacy_pressures(gi_turn, approved):
    at = _app()
    at.session_state["state"] = deepcopy(gi_turn["state"])
    at.run()
    legacy_needle, _ = _shown(at)
    site = ra.open_site(gi_turn["arrival"], environ=BEST)
    ran = list(gi_turn["ran"]) + [{"order_id": "t0:9", "class": "norepinephrine", "fate": "EXECUTED"}]
    assert site.minute(gi_turn["arrival"], at.session_state["state"], gi_turn["session"], ran, "t0") is None
    at.session_state["phase3_authority_artifact"] = site.artifact()
    at.run()
    still, showing = _shown(at)
    assert still == legacy_needle and showing
    artifact = at.session_state["phase3_authority_artifact"]
    assert artifact["halted"] and artifact["minutes"][-1]["committed"] == []
    assert ra.UNSUPPORTED_AUTHORITY_ACTION in artifact["halt_reason"]


# -- P3-19J: replay from the artifact alone ------------------------------------------------------------

def test_d14_the_artifact_replays_to_the_same_pressures_and_digests(gi_turn, approved):
    site = _site(gi_turn)
    assert _one_minute(site, gi_turn) is not None
    artifact = site.artifact()
    serialized = json.loads(json.dumps(artifact, default=str))
    replayed = ra.replay_site_artifact(serialized)
    assert replayed["compared"] == 1 and replayed["reproduces"], replayed
    row = replayed["minutes"][0]
    assert row["candidate_matches"] and row["transaction_matches"] and row["pressures_match"]
    assert row["common_pressures"] == ra.pressure_point(site.records[-1]["common_candidate"])
    assert replayed["artifact_digest_recomputes"]
    # The artifact is self-contained: nothing is read from the live session.
    assert artifact["replay_input"] and artifact["minutes"] and artifact["artifact_digest"]
    assert artifact["phase2_digest"] == rs.PHASE2_DIGEST
    assert ra.replay_site_artifact({**serialized, "snapshot_id": "tampered"})["reproduces"] is False


def test_d15_the_harness_is_imported_by_exactly_one_production_wiring_point():
    """The import exists now, by authorization. What must not exist is a path that can activate it."""
    def imports(path):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import)
                 for alias in node.names}
        return names | {node.module for node in ast.walk(tree)
                        if isinstance(node, ast.ImportFrom) and node.module}

    # The declared layer may read itself -- the artifact store is part of it (P3-26) -- and the claim is
    # about everything else: exactly one production wiring point, and it is the app's helper.
    readers = sorted(path.name for path in ROOT.glob("*.py")
                     if not path.name.startswith("test_") and path.name not in rs.LAYER_SOURCES
                     and "runtime_authority" in imports(path))
    assert readers == ["app.py"], readers
    assert "runtime_authority.py" in rs.LAYER_SOURCES
    assert "runtime_authority_store.py" in rs.LAYER_SOURCES
    assert rs.COMMON_CORE_RUNTIME_AUTHORITY is False


# -- P3-19 review: what the adversarial pass found, each with its own test -----------------------------

def test_d19_a_three_minute_experiment_replays_exactly_from_its_artifact(approved):
    """The review's hardest finding: the artifact kept only the LAST input, so nothing longer than one
    minute could be reproduced. Three real minutes, three transactions, one artifact."""
    import pilot_acceptance
    import runtime_shadow_evidence as ev
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = pilot_acceptance.Encounter(CASE)
        arrival = deepcopy(encounter.state)
        site = ra.open_site(arrival, environ=BEST)
        assert site is not None
        prepared = []
        for text in ("Give 1 litre of normal saline over 15 minutes. Reassess in 10 minutes.",
                     "Transfuse 2 units of packed red cells. Reassess in 10 minutes.",
                     "Start pantoprazole 80 mg IV. Reassess in 10 minutes."):
            encounter.order(text)
            ran = [dict(order) for order in encounter.entries[-1]["orders"]]
            prepared.append(site.minute(None, deepcopy(encounter.state), encounter.shadow, ran,
                                        f"t{len(prepared)}"))
    assert all(item is not None for item in prepared), site.records
    assert len(site.minutes_committed) == 3, site.minutes_committed
    artifact = json.loads(json.dumps(site.artifact(), default=str))
    replayed = ra.replay_site_artifact(artifact)
    assert replayed["compared"] == 3, replayed["compared"]
    assert replayed["reproduces"], [row for row in replayed["minutes"]
                                    if not (row["candidate_matches"] and row["transaction_matches"]
                                            and row["written_matches"])]
    assert len({row["candidate_digest"] for row in replayed["minutes"]}) == 3, "three distinct minutes"
    assert ra.verify_artifact(artifact)["complete"], ra.verify_artifact(artifact)


def test_d20_the_layer_and_the_application_derive_the_same_mean_pressure():
    """``derived_map`` exists here because a commit must write what the screen shows; this pins the two."""
    import app
    for sbp, dbp in ((101, 61), (90, 55), (117, 68), (73, 44), (160, 95), (58, 31)):
        shown = app.learner_vitals_snapshot({"observable": {"sbp": sbp, "dbp": dbp}})["map"]
        assert ra.derived_map(sbp, dbp) == shown, (sbp, dbp, shown)
    assert ra.derived_map(None, 61) is None and ra.derived_map(True, 61) is None


def test_d21_the_registry_cannot_be_bypassed_and_the_serialization_cannot_raise(gi_turn, monkeypatch):
    """Two review findings: rebinding the public name, and a payload that broke the canonical form."""
    monkeypatch.setattr(ra, "APPROVED_SNAPSHOTS", {"forged": {"id": "forged"}})
    assert ra.approved_snapshot("forged") is None, "the private registry is the registry"
    assert not ra.gate(gi_turn["arrival"], environ={**BEST, ra.SNAPSHOT_FLAG: "forged"},
                       unsupported=()).granted
    assert ra.unreachable_because(), "and the module still says it is unreachable"
    # The canonical form: mixed keys, sets, non-finite floats and opaque objects all serialize.
    class Opaque:
        def __repr__(self):
            return "<opaque>"
    assert ra.canonical({1: "a", "b": 2}) == '{"1":"a","b":2}'
    assert ra.canonical({"a": {"c", "b"}}) == '{"a":["b","c"]}'
    assert "nan" in ra.canonical({"a": float("nan")}).lower()
    assert ra.digest_of({"a": Opaque()}) == ra.digest_of({"a": "<opaque>"})
    assert ra.canonical({"b": 1, "a": 2}) == ra.canonical({"a": 2, "b": 1})


def test_d22_a_second_attempt_at_the_same_case_does_not_inherit_the_site(gi_turn, approved):
    """The review found a fresh site with no minutes was reused for another attempt of the same case."""
    import pilot_acceptance
    import runtime_shadow_evidence as ev
    site = _site(gi_turn)
    store = {ra.SITE_KEY: site, ra.ARTIFACT_KEY: {"halted": True}}
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        second = deepcopy(pilot_acceptance.Encounter(CASE, seed=99).state)
    assert not site.is_for(second), "another arrival of the same case is another encounter"
    assert ra.site_for(second, store, environ=BEST) is not site
    assert store[ra.ARTIFACT_KEY] is None or store[ra.ARTIFACT_KEY] != {"halted": True}
    # The same arrival, however, is the same encounter while nothing has been recorded.
    assert site.is_for(gi_turn["arrival"])


def test_d23_one_minute_is_one_transaction_and_an_undeclared_turn_fails_closed(gi_turn, approved):
    site = _site(gi_turn)
    assert _one_minute(site, gi_turn) is not None
    # The same minute again -- a plan, a held order, a clarification that did not move the clock.
    assert _one_minute(site, gi_turn) is None
    assert ra.MINUTE_ALREADY_COMMITTED in site.halt_reason, site.halt_reason
    other = _site(gi_turn)
    assert other.minute(gi_turn["arrival"], deepcopy(gi_turn["state"]), gi_turn["session"], None,
                        "t0") is None
    assert ra.UNSUPPORTED_AUTHORITY_ACTION in other.halt_reason


def test_d24_a_halt_after_a_commit_declares_the_mixed_trajectory(gi_turn, approved):
    """It cannot be undone retroactively, so it is declared -- and a faculty surface can read it."""
    site = _site(gi_turn)
    assert _one_minute(site, gi_turn) is not None
    ran = list(gi_turn["ran"]) + [{"order_id": "t1:0", "class": "norepinephrine", "fate": "EXECUTED"}]
    advanced = {**deepcopy(gi_turn["state"]), "sim_time": int(gi_turn["state"]["sim_time"]) + 5}
    assert site.minute(None, advanced, gi_turn["session"], ran, "t1") is None
    artifact = site.artifact()
    assert artifact["mixed_trajectory"] is True
    assert artifact["authority_minutes"] == list(site.minutes_committed)
    status = ra.authority_status({ra.SITE_KEY: site, ra.ARTIFACT_KEY: artifact})
    assert status["authority"] and status["halted"] and status["mixed_trajectory"]
    assert status["artifact_digest"] == artifact["artifact_digest"]
    assert "never continued" in status["why"]
    # And with no site at all, the status is the legacy one, which is what production reads.
    assert ra.authority_status({})["mode"] == ra.MODE_LEGACY
    assert ra.authority_status({})["authority"] is False


def test_d25_a_forged_artifact_is_detected_and_the_limit_is_stated(gi_turn, approved):
    site = _site(gi_turn)
    assert _one_minute(site, gi_turn) is not None
    artifact = json.loads(json.dumps(site.artifact(), default=str))
    assert ra.replay_site_artifact(artifact)["reproduces"]
    for field, value in (("written_candidate", {"sbp": 999, "dbp": 999, "map": 999}),
                         ("outcome", ra.ABORTED), ("committed", []),
                         ("candidate_digest", "f" * 64)):
        forged = json.loads(json.dumps(artifact, default=str))
        forged["minutes"][0][field] = value
        verdict = ra.replay_site_artifact(forged)
        assert not verdict["reproduces"], field
        assert not verdict["artifact_digest_recomputes"], field
    tampered = json.loads(json.dumps(artifact, default=str))
    tampered["case_id"] = "another_case"
    assert not ra.verify_artifact(tampered)["digest_matches"]
    # And the honest limit: a re-digested forgery passes, because the artifact is self-certifying.
    body = {key: value for key, value in tampered.items() if key != "artifact_digest"}
    resealed = {**body, "artifact_digest": ra.digest_of(body)}
    assert ra.verify_artifact(resealed)["digest_matches"]
    assert "signature" in ra.replay_site_artifact(resealed)["self_certifying"]


def test_d26_the_site_does_not_open_without_the_common_core_running(gi_turn, approved, monkeypatch):
    """Authority has no candidate of its own: without the shadow there is nothing to be authoritative."""
    environ = {name: value for name, value in BEST.items() if name != rs.FLAG}
    assert ra.open_site(gi_turn["arrival"], environ=environ) is None
    assert ra.site_for(gi_turn["arrival"], {}, environ=environ) is None
    assert ra.open_site(gi_turn["arrival"], environ=BEST) is not None


def test_d27_the_retention_of_an_artifact_is_measured_not_guessed(gi_turn, approved):
    site = _site(gi_turn)
    assert _one_minute(site, gi_turn) is not None
    artifact = site.artifact()
    retention = ra.artifact_retention(artifact)
    assert retention["minutes"] == 1
    assert retention["full_bytes"] > retention["minimal_bytes"] > 0
    assert retention["replay_input_bytes"] > 0
    minimal = ra.minimal_artifact(artifact)
    assert ra.verify_artifact(minimal)["digest_matches"], "the minimal form carries its own digest"
    assert ra.replay_site_artifact(minimal)["reproduces"], "and it still replays"
    assert "keep the replay input" in retention["recommendation"]
